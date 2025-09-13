"""
Configurable OPC UA server exposing a TemperatureSensor
with Temperature, Humidity, Calibrate() method,
and AlarmConditionType conditions.

Environment Variables:
    OPCUA_ENDPOINT       (default: opc.tcp://0.0.0:4840/freeopcua/server/)
    OPCUA_NAMESPACE      (default: http://examples.openfactory.local/opcua)
    TEMP_MIN             (default: 21.0)
    TEMP_MAX             (default: 25.0)
    HUM_MIN              (default: 40.0)
    HUM_MAX              (default: 60.0)
    TEMP_SLEEP_AVG       (default: 2.0) Average update interval for temperature
    HUM_SLEEP_AVG        (default: 4.0) Average update interval for humidity
    SENSOR_FAULT_AVG     (default: 20.0 seconds) Average interval between simulated sensor faults

OPC UA Server Structure:

Objects Node
└── Sensors (Folder)
    └── TemperatureSensor (Object)
        ├── 📄 Variables
        │   ├── SensorModel (Property, String, ReadOnly)
        │   ├── Temperature (Variable, Double, ReadOnly)
        │   └── Humidity (Variable, Double, ReadOnly)
        ├── ⚙️ Methods
        │   └── Calibrate()
        │       ├── InputArguments: None
        │       └── OutputArguments: StatusCode (Enum/UInt32)
        └── 🔔 Alarms (Folder)
            ├── OverTemperatureAlarm (AlarmConditionType)
            │   ├── Severity: 900
            │   ├── ActiveState: Boolean
            │   └── InputNode: Temperature
            └── SensorFaultCondition (ConditionType)
                ├── Severity: 500
                ├── ActiveState: Boolean
                └── Message: String

Behavior:
    - SensorModel provides a descriptive identifier for the sensor.
    - Temperature and Humidity values are updated periodically with configurable average intervals.
    - OverTemperatureAlarm triggers if temperature exceeds 90% of defined range.
    - SensorFaultCondition triggers at random intervals based on SENSOR_FAULT_AVG.
"""

import os
import time
import random
import logging
from opcua import ua, Server

# ----------------------------
# Configure logger
# ----------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ----------------------------
# Silence noisy internals
# ----------------------------
logging.getLogger("opcua").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)


def calibrate(parent):
    logger.info("Calibration requested (simulated).")
    return [ua.Variant(0, ua.VariantType.Int32)]  # simple status code


if __name__ == "__main__":
    # ----------------------------
    # Environment-based configuration
    # ----------------------------
    endpoint = os.getenv("OPCUA_ENDPOINT", "opc.tcp://0.0.0:4840/freeopcua/server/")
    namespace_uri = os.getenv("OPCUA_NAMESPACE", "http://examples.openfactory.local/opcua")

    TEMP_MIN = float(os.getenv("TEMP_MIN", 21.0))
    TEMP_MAX = float(os.getenv("TEMP_MAX", 25.0))
    HUM_MIN = float(os.getenv("HUM_MIN", 40.0))
    HUM_MAX = float(os.getenv("HUM_MAX", 60.0))

    # ----------------------------
    # Setup server
    # ----------------------------
    server = Server()
    server.set_endpoint(endpoint)
    idx = server.register_namespace(namespace_uri)

    objects = server.get_objects_node()

    # Create a folder "Sensors"
    sensors = objects.add_object(idx, "Sensors")

    # Create TemperatureSensor object
    sensor = sensors.add_object(idx, "TemperatureSensor")

    # Add SensorModel variable (informational, non-numeric)
    sensor_model = sensor.add_variable(idx, "SensorModel", "Virtual DHT Sensor")
    sensor_model.set_read_only()

    # Add Temperature variable
    temp = sensor.add_variable(idx, "Temperature", TEMP_MIN)
    temp.set_read_only()

    # Add Humidity variable
    hum = sensor.add_variable(idx, "Humidity", HUM_MIN)
    hum.set_read_only()

    # Add Calibrate() method
    sensor.add_method(idx, "Calibrate", calibrate, [], [ua.VariantType.Int32])

    # ----------------------------
    # Add Alarms
    # ----------------------------
    alarms_folder = sensor.add_folder(idx, "Alarms")

    # Create OverTemperatureAlarm node (child of the folder)
    overtemp_node = alarms_folder.add_object(
        idx,
        "OverTemperatureAlarm",
        ua.ObjectIds.AlarmConditionType
    )
    # Add standard properties
    overtemp_node.add_property(idx, "Severity", 900)
    overtemp_node.add_property(idx, "InputNode", temp.nodeid)
    overtemp_node.add_property(idx, "SourceName", "TemperatureSensor")

    # Create SensorFaultCondition node (child of the folder)
    sensor_fault_node = alarms_folder.add_object(
        idx,
        "SensorFaultCondition",
        ua.ObjectIds.ConditionType
    )
    # Add standard properties
    sensor_fault_node.add_property(idx, "Severity", 500)
    sensor_fault_node.add_property(idx, "SourceName", "TemperatureSensor")

    # ----------------------------
    # Start server
    # ----------------------------
    server.start()
    logger.info("---------------------------------------------------")
    logger.info(f"Server started at {endpoint} with namespace {namespace_uri}")
    logger.info(f"Temperature range: {TEMP_MIN} - {TEMP_MAX}")
    logger.info(f"Humidity range: {HUM_MIN} - {HUM_MAX}")
    logger.info("---------------------------------------------------")

    # Average sleep intervals (can be different for temp, hum, and sensor fault)
    TEMP_SLEEP_AVG = float(os.getenv("TEMP_SLEEP_AVG", 2.0))
    HUM_SLEEP_AVG = float(os.getenv("HUM_SLEEP_AVG", 4.0))
    SENSOR_FAULT_AVG = float(os.getenv("SENSOR_FAULT_AVG", 20.0))

    try:
        next_temp_time = time.time()
        next_hum_time = time.time()
        next_fault_time = time.time() + random.uniform(0.8 * SENSOR_FAULT_AVG, 1.2 * SENSOR_FAULT_AVG)

        while True:
            now = time.time()

            # Update temperature if its time
            if now >= next_temp_time:
                current_temp = round(random.uniform(TEMP_MIN, TEMP_MAX), 1)
                temp.set_value(current_temp)
                logger.info(f"Temperature: {current_temp}°C")

                if current_temp > (TEMP_MIN + 0.9 * (TEMP_MAX - TEMP_MIN)):
                    # Create fresh event generator for OverTemperatureAlarm
                    overtemp_alarm = server.get_event_generator(ua.ObjectIds.AlarmConditionType, overtemp_node)
                    overtemp_alarm.event.Severity = 900
                    overtemp_alarm.event.Message = ua.LocalizedText("Temperature too high")
                    overtemp_alarm.event.SourceName = "TemperatureSensor"
                    overtemp_alarm.trigger()
                    logger.info("OverTemperatureAlarm triggered")

                # Schedule next temperature update with jitter
                next_temp_time = now + random.uniform(0.8 * TEMP_SLEEP_AVG, 1.2 * TEMP_SLEEP_AVG)

            # Update humidity if its time
            if now >= next_hum_time:
                current_hum = round(random.uniform(HUM_MIN, HUM_MAX), 1)
                hum.set_value(current_hum)
                logger.info(f"Humidity: {current_hum}%")

                # Schedule next humidity update with jitter
                next_hum_time = now + random.uniform(0.8 * HUM_SLEEP_AVG, 1.2 * HUM_SLEEP_AVG)

            # Trigger sensor fault if its time
            if now >= next_fault_time:
                # Create fresh event generator for SensorFaultCondition
                sensor_fault_alarm = server.get_event_generator(ua.ObjectIds.ConditionType, sensor_fault_node)
                sensor_fault_alarm.event.Severity = 500
                sensor_fault_alarm.event.Message = ua.LocalizedText("Sensor malfunction detected")
                sensor_fault_alarm.event.SourceName = "TemperatureSensor"
                sensor_fault_alarm.trigger()
                logger.info("SensorFaultCondition triggered")

                # Schedule next fault with jitter
                next_fault_time = now + random.uniform(0.8 * SENSOR_FAULT_AVG, 1.2 * SENSOR_FAULT_AVG)

            # Sleep a short time to avoid busy-waiting
            time.sleep(0.1)

    finally:
        server.stop()
        logger.info("Server stopped")
