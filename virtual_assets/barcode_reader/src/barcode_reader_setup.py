"""
Creates a virtual BarcodeReader object hierarchy in an asyncua OPC UA server.

The reader tree includes:
- State: LastCode, LastTimestamp, ReadSuccess, DeviceReady, TriggerInputActive
- Simulation: Mode, MeanArrivalTime, FailureRate, GenerateCode() method
- Events: NoReadEvent, ReaderErrorEvent

This module returns a dictionary of key OPC UA nodes for easy integration
with barcode reader simulations or control loops.
"""

import datetime
import random
import logging
from asyncua import Server, Node, ua
from typing import Dict, Any
import src.config as Config

# ----------------------------
# Logger
# ----------------------------
logger = logging.getLogger(__name__)


# ----------------------------
# OPC UA simulation mode methods
# ----------------------------
async def set_automatic_mode_method(parent: Node, nodes: Dict[str, Node]):
    """
    Switch the barcode reader simulation to AUTOMATIC mode.

    Args:
        parent: OPC UA parent node (required by asyncua method signature)
        nodes (Dict[str, Node]): Must contain the "mode" OPC UA variable node

    Returns:
        List[ua.Variant]: Status code 0 (success)
    """
    await nodes["mode"].write_value("AUTOMATIC")
    return [ua.Variant(0, ua.VariantType.UInt32)]


async def set_manual_mode_method(parent: Node, nodes: Dict[str, Node]):
    """
    Switch the barcode reader simulation to MANUAL mode.

    Args:
        parent: OPC UA parent node (required by asyncua method signature)
        nodes (Dict[str, Node]): Must contain the "mode" OPC UA variable node

    Returns:
        List[ua.Variant]: Status code 0 (success)
    """
    await nodes["mode"].write_value("MANUAL")
    return [ua.Variant(0, ua.VariantType.UInt32)]


# ----------------------------
# OPC UA barcode generation method
# ----------------------------
async def generate_barcode_method(parent: Node, code: str | ua.Variant | None, nodes: Dict[str, Node]):
    """
    Generate a barcode and update OPC UA nodes realistically.

    Behavior:
      - If a device fault occurs, triggers ReaderErrorEvent (Severity 700) and
        ReadSuccess=False. LastCode is not updated.
      - If a simulated read fails, triggers NoReadEvent (Severity 200) and
        ReadSuccess=False. LastCode is not updated.
      - Otherwise, successfully reads a barcode and updates LastCode.

    Args:
        parent: OPC UA parent node (not used)
        code (str | ua.Variant | None): Optional barcode to read (empty = generate random)
        nodes (Dict[str, Node]): Dictionary of OPC UA nodes

    Returns:
        List[ua.Variant]: Status code 0
    """
    if isinstance(code, ua.Variant):
        code = code.Value

    now = datetime.datetime.now()

    # --- Simulate rare device error ---
    if random.random() < Config.SIM_DEVICE_ERROR_RATE:
        await nodes["read_success"].write_value(False)
        await nodes["device_ready"].write_value(False)
        nodes["reader_error_event"].event.Severity = 700
        await nodes["reader_error_event"].trigger(
            message="Simulated device fault — reader unavailable"
        )
        await nodes["last_timestamp"].write_value(now)
        logger.debug("Simulated ReaderErrorEvent (device fault)")
        return [ua.Variant(0, ua.VariantType.UInt32)]

    await nodes["device_ready"].write_value(True)

    # --- Determine if read succeeds ---
    fail_prob = await nodes["failure_rate"].read_value()
    read_success = random.random() > fail_prob
    await nodes["read_success"].write_value(read_success)
    await nodes["last_timestamp"].write_value(now)

    if read_success:
        # Only update LastCode on successful read
        if not code:
            code = "".join(str(random.randint(0, 9)) for _ in range(12))
        await nodes["last_code"].write_value(code)
        logger.debug(f"Generated a new Barcode {code}")
    else:
        # Trigger NoReadEvent if read failed
        nodes["no_read_event"].event.Severity = 200
        await nodes["no_read_event"].trigger(
            message="No code detected during trigger"
        )
        logger.debug("Simulated NoReadEvent (read failed)")

    return [ua.Variant(0, ua.VariantType.UInt32)]


async def create_barcode_reader(server: Server, idx: int, parent: Node) -> Dict[str, Any]:
    """
    Create a hierarchical BarcodeReader node tree in an OPC UA server.

    The tree is organized as follows:
    - GeneralInfo: Static device information (model, version, manufacturer, license)
    - State: Last read barcode, timestamp, read success flag, device readiness, and trigger input state
    - Simulation: Configurable simulation parameters (Mode, MeanArrivalTime, FailureRate)
                  and a GenerateCode() method to simulate barcode reads
    - Events: NoReadEvent (triggered when a read fails) and ReaderErrorEvent (reserved for device errors)

    The GenerateCode() OPC UA method accepts an optional barcode string.
    If the provided code is empty or not set, a random 12-digit barcode is generated.
    The method updates the State variables and may trigger a NoReadEvent depending
    on the configured FailureRate.

    All key variables, methods, and event generators are returned in a dictionary
    for easy integration with simulations, control logic, or higher-level orchestration.

    Args:
        server (Server): The asyncua server instance.
        idx (int): Namespace index used to create nodes in the server address space.
        parent (Node): Parent OPC UA node under which the BarcodeReader object is created.

    Returns:
        Dict[str, Any]: Dictionary containing references to key OPC UA nodes, methods,
        and event generators, including:
            - "barcode_reader": Root BarcodeReader object
            - "last_code": Last read barcode variable
            - "last_timestamp": Last read timestamp variable
            - "read_success": Read success flag variable
            - "device_ready": Device ready status variable
            - "trigger_input_active": Trigger input active flag variable
            - "mode": Simulation mode variable ("AUTOMATIC" / "MANUAL")
            - "mean_arrival_time": Mean time between automatic reads
            - "failure_rate": Probability of a simulated read failure
            - "generate_code_method": GenerateCode() OPC UA method node
            - "no_read_event": Event generator for failed read events
            - "reader_error_event": Event generator for simulated device errors
    """

    # --- Root object ---
    barcode_reader = await parent.add_object(idx, "BarcodeReader")

    # --- General info ---
    model = await barcode_reader.add_variable(idx, "Model", "Virtual Barcode Reader")
    await model.set_writable(False)
    version = await barcode_reader.add_variable(idx, "SoftwareRevision", Config.VERSION)
    await version.set_writable(False)
    manufacturer = await barcode_reader.add_variable(idx, "Manufacturer", "OpenFactoryIO")
    await manufacturer.set_writable(False)
    license = await barcode_reader.add_variable(idx, "License", "Polyform Noncommercial License 1.0.0")
    await license.set_writable(False)

    # --- State ---
    state = await barcode_reader.add_object(idx, "State")
    last_code = await state.add_variable(idx, "LastCode", "")
    await last_code.set_writable(False)
    last_timestamp = await state.add_variable(idx, "LastTimestamp", datetime.datetime.now())
    await last_timestamp.set_writable(False)
    read_success = await state.add_variable(idx, "ReadSuccess", True)
    await read_success.set_writable(False)
    device_ready = await state.add_variable(idx, "DeviceReady", True)
    await device_ready.set_writable(False)
    trigger_input = await state.add_variable(idx, "TriggerInputActive", True)
    await trigger_input.set_writable(False)

    # --- Simulation config ---
    sim = await barcode_reader.add_object(idx, "Simulation")
    mode = await sim.add_variable(idx, "Mode", "AUTOMATIC")
    await mode.set_writable(True)
    mean_arrival_time = await sim.add_variable(idx, "MeanArrivalTime", Config.SIM_MEAN_ARRIVAL_TIME)
    await mean_arrival_time.set_writable(True)
    failure_rate = await sim.add_variable(idx, "FailureRate", Config.SIM_FAILURE_RATE)
    await failure_rate.set_writable(True)

    # --- Define custom event types ---
    base_event_type = server.get_node(ua.ObjectIds.BaseEventType)

    no_read_event_type = await server.create_custom_event_type(
        idx,
        "NoReadEvent",
        base_event_type,
        [
            ("Message", ua.VariantType.LocalizedText),
            ("Severity", ua.VariantType.UInt16),
        ],
    )

    reader_error_event_type = await server.create_custom_event_type(
        idx,
        "ReaderErrorEvent",
        base_event_type,
        [
            ("Message", ua.VariantType.LocalizedText),
            ("Severity", ua.VariantType.UInt16),
        ],
    )

    # --- Event generators ---
    no_read_event = await server.get_event_generator(
        etype=no_read_event_type,
        emitting_node=barcode_reader
    )

    reader_error_event = await server.get_event_generator(
        etype=reader_error_event_type,
        emitting_node=barcode_reader
    )

    # --- Capture nodes in a dict for OPC UA methods ---
    nodes_for_method = {
        "last_code": last_code,
        "last_timestamp": last_timestamp,
        "read_success": read_success,
        "failure_rate": failure_rate,
        "no_read_event": no_read_event,
        "mode": mode,
    }

    # --- OPC UA methods wrappers ---
    async def _generate_code_wrapper(parent, code: str):
        # Wrapper only takes OPC UA input arguments
        return await generate_barcode_method(parent, code, nodes_for_method)

    async def _set_automatic_mode(parent):
        await nodes_for_method["mode"].write_value("AUTOMATIC")
        return [ua.Variant(0, ua.VariantType.UInt32)]

    async def _set_manual_mode(parent):
        await nodes_for_method["mode"].write_value("MANUAL")
        return [ua.Variant(0, ua.VariantType.UInt32)]

    # --- Input / Output Arguments ---
    input_args = [
        ua.Argument(
            Name="Code",
            DataType=ua.NodeId(ua.ObjectIds.String),
            ValueRank=-1,
            Description=ua.LocalizedText("Barcode to generate (empty for random)")
        )
    ]

    output_args = [
        ua.Argument(
            Name="StatusCode",
            DataType=ua.NodeId(ua.ObjectIds.UInt32),
            ValueRank=-1,
            Description=ua.LocalizedText("0=Success")
        )
    ]

    # --- Add methods to OPC UA ---
    generate_code_node = await sim.add_method(
        idx,
        "GenerateCode",
        _generate_code_wrapper,
        input_args,
        output_args
    )

    set_auto_node = await sim.add_method(
        idx,
        "SetAutomaticMode",
        _set_automatic_mode,
        [],         # no input arguments
        output_args
    )

    set_manual_node = await sim.add_method(
        idx,
        "SetManualMode",
        _set_manual_mode,
        [],         # no input arguments
        output_args
    )

    # --- Return all key nodes ---
    return {
        "barcode_reader": barcode_reader,
        "last_code": last_code,
        "last_timestamp": last_timestamp,
        "read_success": read_success,
        "device_ready": device_ready,
        "trigger_input_active": trigger_input,
        "mode": mode,
        "mean_arrival_time": mean_arrival_time,
        "failure_rate": failure_rate,
        "generate_code_method": generate_code_node,
        "set_automatic_mode_method": set_auto_node,
        "set_manual_mode_method": set_manual_node,
        "no_read_event": no_read_event,
        "reader_error_event": reader_error_event
    }
