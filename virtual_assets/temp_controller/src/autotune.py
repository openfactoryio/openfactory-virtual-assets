"""
Functions to automatically compute PID or PI controller gains from thermal
plant models.

This module provides IMC-based tuning rules for first-order (PT1) and two
PT1 systems in series. It is intended for use with virtual temperature
controllers, heaters, ovens, and other thermal systems where a simple
dynamic model has been identified.

Functions:
    - autotune_pi_from_plant(plant, aggressiveness=1.0)
        Computes PI gains for a first-order thermal plant using IMC tuning.
    - autotune_pid_from_two_pt1(plant, aggressiveness=1.0)
        Computes PID gains for a two PT1 system (heater + plant) using IMC-based tuning.

Notes:
    - These functions return gains suitable for virtual or real-time PID
      controllers.
    - The 'aggressiveness' parameter allows tuning the speed of response
      without changing the plant model.
    - Derivative action is only included for two PT1 systems, not first-order
      plants, to avoid amplifying noise.

References:
    Rivera, Morari, Skogestad (1986). "Internal Model Control: PID Controller Design."
"""

from typing import Tuple
from src.plant import FirstOrderPlant
from src.plant import TwoPT1ThermalPlant


def autotune_pi_from_plant(plant: FirstOrderPlant, aggressiveness: float = 1.0) -> Tuple[float, float, float]:
    """
    Compute PI controller gains from a first-order plant model.

    This function derives proportional and integral gains using an
    Internal Model Control (IMC)-based tuning rule for a first-order system.
    It assumes the plant can be approximated as:

        G(s) = K / (tau * s + 1)

    where:
        K   : steady-state gain (temperature change per unit control input)
        tau : time constant of the thermal process

    For this class of slow, well-behaved systems (like heaters, ovens,
    thermal chambers), a PI controller is typically sufficient. Derivative
    action is avoided because it amplifies measurement noise and provides
    little benefit for dominant first-order thermal dynamics.

    The IMC tuning rule introduces a design parameter λ (lambda), which
    directly shapes the closed-loop response speed and robustness. We use:

        Kp = tau / (K * λ)
        Ki = 1 / λ
        Kd = 0

    where λ is chosen proportional to the plant time constant:

        λ = aggressiveness * tau

    Interpretation of `aggressiveness`:
        aggressiveness = 1.0  -> balanced response (λ = tau)
        aggressiveness < 1.0  -> faster, more aggressive control
        aggressiveness > 1.0  -> slower, smoother, more robust control

    With λ ≈ tau, the closed-loop system typically has a time constant
    on the order of the plant's natural dynamics, giving a responsive
    but stable temperature regulation without excessive overshoot.

    Args:
        plant (ThermalPlant):
            Identified thermal plant model containing at least:
            - plant.K    : steady-state gain K
            - plant.tau  : time constant tau
        aggressiveness (float, optional):
            Scaling factor for the IMC tuning parameter λ. Defaults to 1.0.

    Returns:
        tuple[float, float, float]:
            A tuple (kp, ki, kd) containing the proportional, integral,
            and derivative gains. For this thermal IMC tuning, kd is 0.0.

    Raises:
        ValueError:
            If the plant gain or time constant are non-positive, making
            the tuning physically meaningless.

    References:
        Rivera, Morari, Skogestad (1986). "Internal Model Control: PID
        Controller Design." Widely used foundation for IMC-based PID tuning.
    """
    K = plant.K
    tau = plant.tau

    if K <= 0 or tau <= 0:
        raise ValueError("Invalid plant parameters for tuning")

    # IMC tuning parameter
    lam = tau * aggressiveness

    kp = tau / (K * lam)
    ki = 1.0 / lam
    kd = 0.0

    return kp, ki, kd


def autotune_pid_from_two_pt1(plant: TwoPT1ThermalPlant, aggressiveness: float = 1.0) -> Tuple[float, float, float]:
    """
    Autotune a PID controller for a two PT1 thermal system (heater + plant).

    The plant is assumed to have the transfer function:

        G(s) = (K_h * K_p) / ((tau_h s + 1) * (tau_p s + 1))

    We use a simplified IMC-based tuning for two PT1 systems in series
    to compute PID gains including derivative action.

    Args:
        plant: TwoPT1ThermalPlant instance containing:
            - K_h   : heater gain [W/unit input]
            - K_p   : plant gain [°C/W]
            - tau_h : heater time constant [s]
            - tau_p : plant time constant [s]
        aggressiveness: tuning factor (λ scaling). 1.0 is balanced, <1 faster, >1 slower

    Returns:
        Tuple[float, float, float]: (kp, ki, kd)
            Proportional, integral, and derivative gains.
            Units consistent with control input in [0..1] and temperature in °C.
    """
    K = plant.K_h * plant.K_p
    tau1 = plant.tau_h
    tau2 = plant.tau_p

    if K <= 0 or tau1 <= 0 or tau2 <= 0:
        raise ValueError("Invalid plant parameters for tuning")

    # IMC-based closed-loop tuning parameter
    lam = aggressiveness * (tau1 + tau2)  # simple approximation for series PT1

    # PID coefficients using IMC tuning for 2 PT1 systems
    kp = (tau1 + tau2) / (K * lam)
    ki = 1.0 / lam
    kd = (tau1 * tau2) / (tau1 + tau2)  # approximate derivative term

    return kp, ki, kd
