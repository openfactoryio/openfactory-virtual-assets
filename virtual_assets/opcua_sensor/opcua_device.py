"""
Configurable OPC UA server exposing multiple TemperatureSensors,
each with Temperature, Humidity, a Calibrate() method,
and AlarmConditionType conditions.

Environment Variables:
    OPCUA_ENDPOINT       (default: opc.tcp://0.0.0:4840/freeopcua/server/)
    OPCUA_NAMESPACE      (default: http://examples.openfactory.local/opcua)
    SENSOR_COUNT         (default: 2) Number of simulated TemperatureSensors
    TEMP_MIN             (default: 21.0)
    TEMP_MAX             (default: 25.0)
    HUM_MIN              (default: 40.0)
    HUM_MAX              (default: 60.0)
    TEMP_SLEEP_AVG       (default: 2.0) Average update interval for temperature
    HUM_SLEEP_AVG        (default: 4.0) Average update interval for humidity
    SENSOR_FAULT_AVG     (default: 20.0 seconds) Average interval between simulated sensor faults

OPC UA Server Structure:

Objects Node
└── Sensors (Object)
    ├── TemperatureSensor1 (Object)
    │   ├── 📄 Variables
    │   │   ├── SensorModel (Property, String, ReadOnly)
    │   │   ├── Temperature (Variable, Double, ReadOnly)
    │   │   └── Humidity (Variable, Double, ReadOnly)
    │   └── ⚙️ Methods
    │       └── Calibrate()
    │           ├── InputArguments: None
    │           └── OutputArguments: StatusCode (Enum/UInt32)
    │
    ├── TemperatureSensor2 (Object)
    │   └── ... (same structure)
    │
    └── TemperatureSensorN (Object)
        └── ... (same structure)

Events (per sensor):
    ├── 🔔 OverTemperatureAlarm (AlarmConditionType)
    │    ├── Severity: 900
    │    ├── Message: "Temperature too high"
    │    └── SourceName: "TemperatureSensorX"
    └── 🔔 SensorFaultCondition (AlarmConditionType)
         ├── Severity: 500
         ├── Message: "Sensor malfunction detected"
         └── SourceName: "TemperatureSensorX"

Behavior:
    - Each TemperatureSensor has its own SensorModel identifier.
    - Temperature and Humidity values are updated periodically with configurable average intervals.
    - OverTemperatureAlarm triggers if temperature exceeds 90% of defined range.
    - SensorFaultCondition triggers at random intervals based on SENSOR_FAULT_AVG.
"""

import os
import time
import random
import logging
import asyncio
from typing import Any
from asyncua import Server, ua, Node
from asyncua.common.methods import uamethod

# ----------------------------
# Logger
# ----------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ----------------------------
# Silence noisy internals
# ----------------------------
logging.getLogger("asyncua").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)


# ----------------------------
# Calibration method
# ----------------------------
@uamethod
async def calibrate(parent: Node) -> list[ua.Variant]:
    """
    Simulated calibration method for a TemperatureSensor node.

    This OPC UA method can be invoked by clients to simulate a calibration
    routine on the sensor. No actual calibration logic is performed; the
    function always returns a success status code.

    Args:
        parent (Node): The OPC UA node (sensor object) on which the method
            is invoked. Typically a TemperatureSensor node.

    Returns:
        list[ua.Variant]: A single-element list containing the result:
            - StatusCode (Int32): `0` indicates success.

    Example:
        >>> # Client calls the Calibrate() method on TemperatureSensor1
        >>> result = await sensor_node.call_method("Calibrate")
        >>> print(result)  # [Variant(0)]
    """
    logger.info(f"Calibration requested for {parent}. (simulated)")
    return [ua.Variant(0, ua.VariantType.Int32)]


# ----------------------------
# Create one TemperatureSensor node
# ----------------------------
async def create_sensor(
    server: Server,
    idx: int,
    parent: Node,
    sensor_name: str,
    temp_range: tuple[float, float],
    hum_range: tuple[float, float],
) -> dict[str, Any]:
    """
    Create a simulated TemperatureSensor node in the OPC UA server.

    The TemperatureSensor node includes:
        - SensorModel (read-only string property)
        - Temperature (read-only double variable)
        - Humidity (read-only double variable)
        - Calibrate() method (returns StatusCode)
        - OverTemperature and SensorFault alarms (AlarmConditionType)

    Args:
        server (Server): The OPC UA server instance.
        idx (int): The namespace index in which to create the node.
        parent (Node): The parent node (e.g., "Sensors" object).
        sensor_name (str): Name for this sensor node (e.g., "TemperatureSensor1").
        temp_range (tuple[float, float]): (min, max) range for temperature values.
        hum_range (tuple[float, float]): (min, max) range for humidity values.

    Returns:
        dict[str, Any]: Dictionary containing references for controlling this sensor:
            - "name": Sensor name (str)
            - "temp": Temperature variable node (ua.Node)
            - "hum": Humidity variable node (ua.Node)
            - "overtemp_alarm": OverTemperature alarm generator
            - "fault_alarm": SensorFault alarm generator
            - "temp_range": Configured temperature range (tuple[float, float])
            - "hum_range": Configured humidity range (tuple[float, float])

    Example:
        >>> sensors_obj = await server.nodes.objects.add_object(idx, "Sensors")
        >>> sensor = await create_sensor(server, idx, sensors_obj,
        ...                              "TemperatureSensor1", (21.0, 25.0), (40.0, 60.0))
        >>> await sensor["temp"].write_value(22.5)  # update temperature
    """
    TEMP_MIN, TEMP_MAX = temp_range
    HUM_MIN, HUM_MAX = hum_range

    sensor = await parent.add_object(idx, sensor_name)

    # Variables
    sensor_model = await sensor.add_variable(idx, "SensorModel", f"Virtual DHT {sensor_name}")
    await sensor_model.set_writable(False)

    temp = await sensor.add_variable(idx, "Temperature", TEMP_MIN)
    await temp.set_writable(False)

    hum = await sensor.add_variable(idx, "Humidity", HUM_MIN)
    await hum.set_writable(False)

    # Method
    await sensor.add_method(idx, "Calibrate", calibrate, [], [ua.VariantType.Int32])

    # Alarms
    alarm_type_node = server.get_node(ua.ObjectIds.AlarmConditionType)

    overtemp_alarm = await server.get_event_generator(etype=alarm_type_node, emitting_node=sensor)
    overtemp_alarm.event.Severity = 900
    overtemp_alarm.event.Message = ua.LocalizedText("Temperature too high")
    overtemp_alarm.event.SourceName = sensor_name

    fault_alarm = await server.get_event_generator(etype=alarm_type_node, emitting_node=sensor)
    fault_alarm.event.Severity = 500
    fault_alarm.event.Message = ua.LocalizedText("Sensor malfunction detected")
    fault_alarm.event.SourceName = sensor_name

    await sensor.set_event_notifier([ua.EventNotifier.SubscribeToEvents])
    await parent.add_reference(sensor.nodeid, ua.ObjectIds.HasEventSource, forward=True)

    return {
        "name": sensor_name,
        "temp": temp,
        "hum": hum,
        "overtemp_alarm": overtemp_alarm,
        "fault_alarm": fault_alarm,
        "temp_range": temp_range,
        "hum_range": hum_range,
    }


# ----------------------------
# Main server coroutine
# ----------------------------
async def main():
    # Config
    endpoint = os.getenv("OPCUA_ENDPOINT", "opc.tcp://0.0.0:4840/freeopcua/server/")
    namespace_uri = os.getenv("OPCUA_NAMESPACE", "http://examples.openfactory.local/opcua")
    NUM_SENSORS = int(os.getenv("NUM_SENSORS", 2))

    TEMP_MIN = float(os.getenv("TEMP_MIN", 21.0))
    TEMP_MAX = float(os.getenv("TEMP_MAX", 25.0))
    HUM_MIN = float(os.getenv("HUM_MIN", 40.0))
    HUM_MAX = float(os.getenv("HUM_MAX", 60.0))

    TEMP_SLEEP_AVG = float(os.getenv("TEMP_SLEEP_AVG", 2.0))
    HUM_SLEEP_AVG = float(os.getenv("HUM_SLEEP_AVG", 4.0))
    SENSOR_FAULT_AVG = float(os.getenv("SENSOR_FAULT_AVG", 20.0))

    # Setup server
    server = Server()
    await server.init()
    server.set_endpoint(endpoint)
    idx = await server.register_namespace(namespace_uri)

    objects = server.nodes.objects
    sensors_folder = await objects.add_object(idx, "Sensors")
    await sensors_folder.set_event_notifier([ua.EventNotifier.SubscribeToEvents])

    # Create N sensors
    sensors = []
    for i in range(1, NUM_SENSORS + 1):
        sensor = await create_sensor(
            server,
            idx,
            sensors_folder,
            f"TemperatureSensor{i}",
            (TEMP_MIN, TEMP_MAX),
            (HUM_MIN, HUM_MAX),
        )
        sensors.append(sensor)

    # Start server
    async with server:
        logger.info("---------------------------------------------------")
        logger.info(f"Server started at {endpoint} with namespace {namespace_uri}")
        logger.info(f"Created {NUM_SENSORS} sensors")
        logger.info("---------------------------------------------------")

        # Timers per sensor
        next_temp_time = {s["name"]: time.time() for s in sensors}
        next_hum_time = {s["name"]: time.time() for s in sensors}
        next_fault_time = {
            s["name"]: time.time() + random.uniform(0.8 * SENSOR_FAULT_AVG, 1.2 * SENSOR_FAULT_AVG)
            for s in sensors
        }

        try:
            while True:
                now = time.time()

                for s in sensors:
                    TEMP_MIN, TEMP_MAX = s["temp_range"]
                    HUM_MIN, HUM_MAX = s["hum_range"]

                    # Temperature
                    if now >= next_temp_time[s["name"]]:
                        current_temp = round(random.uniform(TEMP_MIN, TEMP_MAX), 1)
                        await s["temp"].write_value(current_temp)
                        logger.info(f"{s['name']} Temperature: {current_temp}°C")

                        if current_temp > (TEMP_MIN + 0.9 * (TEMP_MAX - TEMP_MIN)):
                            await s["overtemp_alarm"].trigger()
                            logger.info(f"{s['name']} OverTemperatureAlarm triggered")

                        next_temp_time[s["name"]] = now + random.uniform(0.8 * TEMP_SLEEP_AVG, 1.2 * TEMP_SLEEP_AVG)

                    # Humidity
                    if now >= next_hum_time[s["name"]]:
                        current_hum = round(random.uniform(HUM_MIN, HUM_MAX), 1)
                        await s["hum"].write_value(current_hum)
                        logger.info(f"{s['name']} Humidity: {current_hum}%")

                        next_hum_time[s["name"]] = now + random.uniform(0.8 * HUM_SLEEP_AVG, 1.2 * HUM_SLEEP_AVG)

                    # Fault
                    if now >= next_fault_time[s["name"]]:
                        await s["fault_alarm"].trigger()
                        logger.info(f"{s['name']} SensorFaultCondition triggered")
                        next_fault_time[s["name"]] = now + random.uniform(0.8 * SENSOR_FAULT_AVG, 1.2 * SENSOR_FAULT_AVG)

                # Sleep a short time to avoid busy-waiting
                await asyncio.sleep(0.1)

        finally:
            logger.info("Server stopped")


if __name__ == "__main__":
    asyncio.run(main())
