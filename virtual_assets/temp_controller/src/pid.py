"""
Discrete PID controller implementation for temperature and process control.

This module provides the PIDController class, which supports independent
enable/disable flags for proportional, integral, and derivative terms,
integral anti-windup, output saturation, and dynamic gain updates.
"""


class PIDController:
    """
    Discrete PID controller with optional P, I, and D terms.

    This controller maintains its own internal state (integral term,
    previous error) and supports enabling or disabling each contribution
    individually. Output saturation and integral anti-windup limiting
    are also supported.

    The controller is intended to be updated at a fixed timestep `dt`
    inside a control or simulation loop.
    """

    def __init__(
        self,
        setpoint: float = 0.0,
        kp: float = 0.0,
        ki: float = 0.0,
        kd: float = 0.0,
        prop_enabled: bool = True,
        integ_enabled: bool = True,
        deriv_enabled: bool = False,
        windup_limit: float = 100.0,
        output_min: float = 0.0,
        output_max: float = 100.0,
    ) -> None:
        """
        Initialize the PID controller.

        Args:
            setpoint: Desired target value for the controlled variable.
            kp: Proportional gain.
            ki: Integral gain.
            kd: Derivative gain.
            prop_enabled: Whether the proportional term is active.
            integ_enabled: Whether the integral term is active.
            deriv_enabled: Whether the derivative term is active.
            windup_limit: Absolute limit for the internal integral term to prevent integral windup.
            output_min: Minimum allowed controller output.
            output_max: Maximum allowed controller output.
        """
        self._setpoint = setpoint
        self._kp = kp
        self._ki = ki
        self._kd = kd
        self._prop_enabled = prop_enabled
        self._integ_enabled = integ_enabled
        self._deriv_enabled = deriv_enabled
        self._windup_limit = windup_limit
        self._output_min = output_min
        self._output_max = output_max

        self.integral = 0.0
        self.last_error = None

    @property
    def setpoint(self):
        return self._setpoint

    @setpoint.setter
    def setpoint(self, val):
        self._setpoint = val

    @property
    def kp(self):
        return self._kp

    @kp.setter
    def kp(self, val):
        self._kp = val

    @property
    def ki(self):
        return self._ki

    @ki.setter
    def ki(self, val):
        self._ki = val

    @property
    def kd(self):
        return self._kd

    @kd.setter
    def kd(self, val):
        self._kd = val

    @property
    def prop_enabled(self):
        return self._prop_enabled

    @prop_enabled.setter
    def prop_enabled(self, val: bool):
        self._prop_enabled = val

    @property
    def integ_enabled(self):
        return self._integ_enabled

    @integ_enabled.setter
    def integ_enabled(self, val: bool):
        self._integ_enabled = val

    @property
    def deriv_enabled(self):
        return self._deriv_enabled

    @deriv_enabled.setter
    def deriv_enabled(self, val: bool):
        self._deriv_enabled = val

    @property
    def windup_limit(self):
        return self._windup_limit

    @windup_limit.setter
    def windup_limit(self, val: float):
        self._windup_limit = val

    @property
    def output_min(self):
        return self._output_min

    @output_min.setter
    def output_min(self, val: float):
        self._output_min = val

    @property
    def output_max(self):
        return self._output_max

    @output_max.setter
    def output_max(self, val: float):
        self._output_max = val

    def compute(self, measured: float, dt: float) -> float:
        """
        Compute the PID control output.

        Args:
            measured: Current measured value of the process variable.
            dt: Time step since the last controller update, in seconds.

        Returns:
            The saturated control output after applying P, I, and D terms
            and output limits.
        """
        error = self.setpoint - measured

        P = self.kp * error if self.prop_enabled else 0.0

        if self.integ_enabled:
            self.integral += error * dt
            self.integral = max(min(self.integral, self.windup_limit), -self.windup_limit)
        Int = self.ki * self.integral if self.integ_enabled else 0.0

        D = 0.0
        if self.deriv_enabled and self.last_error is not None:
            D = self.kd * (error - self.last_error) / dt

        self.last_error = error
        return max(self.output_min, min(self.output_max, P + Int + D))

    def reset(self) -> None:
        """
        Reset the internal controller state.

        This clears the accumulated integral term and the stored previous
        error. Useful when restarting a control sequence or after large
        setpoint changes.
        """
        self._integral = 0.0
        self._prev_error = 0.0

    def set_output_limits(self, output_min: float, output_max: float) -> None:
        """
        Update the output saturation limits.

        Args:
            output_min: New minimum allowed controller output.
            output_max: New maximum allowed controller output.
        """
        self.output_min = output_min
        self.output_max = output_max

    def set_windup_limit(self, limit: float) -> None:
        """
        Update the integral anti-windup limit.

        Args:
            limit: Maximum absolute value allowed for the internal integral accumulator.
        """
        self.windup_limit = abs(limit)
