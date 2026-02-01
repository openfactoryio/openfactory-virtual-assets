"""
Models for thermal and generic first-order dynamic systems.

This module provides:

- FirstOrderPlant: Generic first-order linear time-invariant system.
- ThermalPlant: First-order thermal system with absolute temperature and ambient reference.
- TwoPT1ThermalPlant: Thermal system with separate first-order dynamics for heater and plant.

These classes are intended for simulation of temperature control loops and can
be connected to PID controllers or virtual OPC UA assets for testing.
"""


class FirstOrderPlant:
    """
    Generic first-order linear time-invariant (LTI) dynamic system.

    This class models a first-order lag process in deviation-variable form:

        dx/dt = (-x + K * u) / tau

    Transfer function (from input u to output x):

        G(s) = X(s) / U(s) = K / (tau s + 1)

    where:
        x   = system state (output)
        u   = control input
        tau = time constant
        K   = process gain

    The model represents pure dynamics without any operating-point offset
    or bias. Physical offsets (e.g., ambient temperature) should be handled
    in a derived class by transforming between deviation and absolute
    variables.

    The internal state is numerically integrated using forward Euler.
    """

    def __init__(self, K: float = 1.0, tau: float = 10.0, x0: float = 0.0) -> None:
        """
        Initialize the first-order plant.

        Args:
            K: Static gain of the plant.
            tau: Time constant of the plant in seconds.
            x0: Initial state value .
        """
        self.K = K
        self.tau = tau
        self.x = x0

    def update(self, u: float, dt: float) -> float:
        """
        Advance the plant simulation by one time step.

        Args:
            u: Control input.
            dt: Simulation time step in seconds.

        Returns:
            Updated plant output (state).
        """
        dx = dt / self.tau * (-self.x + self.K * u)
        self.x += dx
        return self.x


class ThermalPlant(FirstOrderPlant):
    """
    First-order thermal system with absolute temperature input/output.

    Simulates the temperature of a heated object with heat losses to the environment.
    Internally, it models a first-order lag with heater input.

    The absolute temperature T follows:

        dT/dt = (-(T - T_ambient) + K * u) / tau

    where:
        T         : absolute temperature
        T_ambient : ambient temperature
        u         : heater input (control signal)
        tau       : thermal time constant
        K         : heater gain

    Attributes:
        temp    : current absolute temperature
        ambient : ambient temperature
        tau     : thermal time constant
        K       : heater gain
    """

    def __init__(
        self,
        initial_temp: float = 22.0,
        ambient: float = 20.0,
        tau: float = 10.0,
        heater_gain: float = 1.0,
    ) -> None:
        """
        Initialize the thermal plant.

        Args:
            initial_temp: Initial absolute temperature of the plant
            ambient: Ambient (environment) temperature
            tau: Thermal time constant (s)
            heater_gain: Gain from heater control signal to temperature change
        """
        super().__init__(tau=tau, K=heater_gain, x0=initial_temp - ambient)
        self.ambient = ambient
        self.temp = initial_temp

    def update(self, control_output: float, dt: float) -> float:
        """
        Advance the thermal simulation by one timestep.

        Args:
            control_output: Heater control signal (e.g., power level)
            dt: Simulation time step (s)

        Returns:
            Updated absolute temperature
        """
        self.temp = self.ambient + super().update(control_output, dt)
        return self.temp


class TwoPT1ThermalPlant:
    """
    Thermal system with a first-order heater and first-order plant dynamics.

    This class models a heated object where the heater has its own dynamics
    and the plant (object) responds to the delivered heat. Both are modeled
    as first-order systems in series.

    System equations:

        Heater:  dQ_h/dt = (-Q_h + K_h * u) / tau_h
        Plant:   dT/dt   = (-(T - T_ambient) + K_p * Q_h) / tau_p

    where:
        u         : heater command (control input), unitless [0..1] or normalized
        Q_h       : effective heater output (after first-order lag), Watts [W]
        T         : absolute temperature of the object, degrees Celsius [°C]
        T_ambient : ambient temperature, degrees Celsius [°C]
        tau_h     : heater time constant, seconds [s]
        tau_p     : plant time constant, seconds [s]
        K_h       : heater gain (max heater power per unit command), Watts/unit input [W/unit]
        K_p       : plant gain (temperature rise per Watt of heater power), °C/W

    Transfer function from u to T:

        G(s) = (K_h * K_p) / ((tau_h s + 1) * (tau_p s + 1))

    Attributes:
        temp    : current absolute temperature of the plant [°C]
        heater  : current effective heater output [W]
        ambient : ambient temperature [°C]
        tau_p   : plant thermal time constant [s]
        tau_h   : heater time constant [s]
        K_p     : plant gain [°C/W]
        K_h     : heater gain [W/unit input]
    """

    def __init__(
        self,
        initial_temp: float = 22.0,
        ambient: float = 20.0,
        tau_p: float = 10.0,
        K_p: float = 0.5,
        tau_h: float = 1.0,
        K_h: float = 100.0,
    ) -> None:
        """
        Initialize the two PT1 thermal plant.

        Args:
            initial_temp: Initial absolute temperature of the plant [°C]
            ambient: Ambient temperature [°C]
            tau_p: Plant thermal time constant [s]
            K_p: Plant gain (temperature rise per Watt of heater output) [°C/W]
            tau_h: Heater time constant [s]
            K_h: Heater gain (max heater power per unit command) [W/unit input]
        """
        self.temp = initial_temp
        self.ambient = ambient
        self.tau_p = tau_p
        self.K_p = K_p
        self.tau_h = tau_h
        self.K_h = K_h
        # initial effective heater output
        self.heater = 0.0

    def update(self, u: float, dt: float) -> float:
        """
        Advance the thermal simulation by one timestep.

        Args:
            u: Heater control input (unitless, typically 0..1)
            dt: Simulation time step [s]

        Returns:
            Updated absolute temperature [°C]
        """
        # Heater first-order dynamics
        dQ_h = dt / self.tau_h * (-self.heater + self.K_h * u)
        self.heater += dQ_h

        # Plant first-order dynamics
        dT = dt / self.tau_p * (-(self.temp - self.ambient) + self.K_p * self.heater)
        self.temp += dT

        return self.temp
