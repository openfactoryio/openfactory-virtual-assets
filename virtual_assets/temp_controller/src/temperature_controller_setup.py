"""
Creates a virtual TemperatureController object hierarchy in an asyncua OPC UA server.

The controller tree includes:
- State: Current temperature, control output, timestamps
- Configuration: Setpoint, mode, PID gains
- OutputConstraints: Min/max control output limits
- ControllerActions: Methods for resetting or switching controller modes
- Events: Overtemperature and fault alarms

This module returns a dictionary of key OPC UA nodes for easy integration
with PID controllers or simulation loops.
"""


import datetime
import os
from asyncua import Server, Node, ua
from typing import Dict, Any


async def create_temperature_controller(server: Server, idx: int, parent: Node) -> Dict[str, Any]:
    """
    Create a hierarchical TemperatureController node tree in an OPC UA server.

    The tree is organized as follows:
    - State: Current process variables and timestamps
    - Configuration: Controller parameters (setpoint, mode, PID gains)
    - OutputConstraints: Min/max control output limits
    - ControllerActions: Methods for resetting or switching modes
    - Events: Overtemperature and fault alarms

    All key variables and events are returned in a dictionary for easy access.

    Args:
        server (Server): The asyncua server instance.
        idx (int): Namespace index for the server.
        parent (Node): Parent node under which to create the controller object.

    Returns:
        Dict[str, Any]: Dictionary containing references to key OPC UA nodes and events, including:
            - "controller": Root controller object
            - "temp": Current temperature variable
            - "output": Control output variable
            - "last_update": Last update timestamp
            - "setpoint": Controller setpoint variable
            - "mode": Controller mode variable
            - "kp", "ki", "kd": PID gain variables
            - "prop_enabled", "integ_enabled", "deriv_enabled": PID enable flags
            - "windup": Integral windup limit
            - "output_min", "output_max": Control output constraints
            - "overtemp_alarm", "fault_alarm": OPC UA event generators
    """
    VERSION = os.getenv("VERSION", "dev")
    # --- Root controller object ---
    ctrl_obj = await parent.add_object(idx, "TemperatureController")

    # --- General information
    model = await ctrl_obj.add_variable(idx, "Model", "Virtual Temperature Controller")
    await model.set_writable(False)
    version = await ctrl_obj.add_variable(idx, "SoftwareRevision", VERSION)
    await version.set_writable(False)
    manufacturer = await ctrl_obj.add_variable(idx, "Manufacturer", "OpenFactoryIO")
    await manufacturer.set_writable(False)
    license = await ctrl_obj.add_variable(idx, "License", "Polyform Noncommercial License 1.0.0")
    await license.set_writable(False)

    # --- State folder ---
    state = await ctrl_obj.add_object(idx, "State")
    temp_node = await state.add_variable(idx, "CurrentTemperature", 20.0)
    await temp_node.set_writable(False)
    output_node = await state.add_variable(idx, "ControlOutput", 0.0)
    await output_node.set_writable(False)
    last_update_node = await state.add_variable(idx, "LastUpdateTime", datetime.datetime.now())
    await last_update_node.set_writable(False)

    # --- Configuration folder ---
    config = await ctrl_obj.add_object(idx, "Configuration")
    await config.add_property(idx, "ControllerModel", "Virtual PID Controller")
    setpoint_node = await config.add_variable(idx, "SetPoint", 25.0)
    await setpoint_node.set_writable(True)
    mode_node = await config.add_variable(idx, "Mode", "AUTO")
    await mode_node.set_writable(True)

    # --- PID subtree ---
    pid = await config.add_object(idx, "PID")

    # Proportional
    prop = await pid.add_object(idx, "Proportional")
    kp_node = await prop.add_variable(idx, "Gain", 1.0)
    await kp_node.set_writable(True)
    prop_enabled = await prop.add_variable(idx, "Enabled", True)
    await prop_enabled.set_writable(True)

    # Integral
    integ = await pid.add_object(idx, "Integral")
    ki_node = await integ.add_variable(idx, "Gain", 0.1)
    await ki_node.set_writable(True)
    integ_enabled = await integ.add_variable(idx, "Enabled", True)
    await integ_enabled.set_writable(True)
    windup_node = await integ.add_variable(idx, "WindupLimit", 50.0)
    await windup_node.set_writable(True)

    # Derivative
    deriv = await pid.add_object(idx, "Derivative")
    kd_node = await deriv.add_variable(idx, "Gain", 0.0)
    await kd_node.set_writable(True)
    deriv_enabled = await deriv.add_variable(idx, "Enabled", True)
    await deriv_enabled.set_writable(True)

    # --- Output constraints ---
    output_constraints = await ctrl_obj.add_object(idx, "OutputConstraints")
    output_min = await output_constraints.add_variable(idx, "OutputMin", 0.0)
    await output_min.set_writable(True)
    output_max = await output_constraints.add_variable(idx, "OutputMax", 100.0)
    await output_max.set_writable(True)

    # --- Controller actions ---
    actions = await ctrl_obj.add_object(idx, "ControllerActions")

    async def reset_controller(parent: Node):
        return [ua.Variant(0, ua.VariantType.Int32)]
    await actions.add_method(idx, "ResetController", reset_controller, [], [ua.VariantType.Int32])

    async def switch_mode(parent: Node, new_mode: str):
        return [ua.Variant(0, ua.VariantType.Int32)]
    await actions.add_method(idx, "SwitchMode", switch_mode, [ua.VariantType.String], [ua.VariantType.Int32])

    # --- Events ---
    alarm_type_node = server.get_node(ua.ObjectIds.AlarmConditionType)
    overtemp_alarm = await server.get_event_generator(etype=alarm_type_node, emitting_node=ctrl_obj)
    overtemp_alarm.event.Severity = 900

    fault_alarm = await server.get_event_generator(etype=alarm_type_node, emitting_node=ctrl_obj)
    fault_alarm.event.Severity = 500

    # Return references to key nodes
    return {
        "controller": ctrl_obj,
        "temp": temp_node,
        "output": output_node,
        "last_update": last_update_node,
        "setpoint": setpoint_node,
        "mode": mode_node,
        "kp": kp_node,
        "ki": ki_node,
        "kd": kd_node,
        "prop_enabled": prop_enabled,
        "integ_enabled": integ_enabled,
        "windup": windup_node,
        "deriv_enabled": deriv_enabled,
        "output_min": output_min,
        "output_max": output_max,
        "overtemp_alarm": overtemp_alarm,
        "fault_alarm": fault_alarm
    }
