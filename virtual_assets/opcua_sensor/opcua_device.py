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
└── Sensors (Object)
    └── TemperatureSensor (Object)
        ├── 📄 Variables
        │   ├── SensorModel (Property, String, ReadOnly)
        │   ├── Temperature (Variable, Double, ReadOnly)
        │   └── Humidity (Variable, Double, ReadOnly)
        └── ⚙️ Methods
            └── Calibrate()
                ├── InputArguments: None
                └── OutputArguments: StatusCode (Enum/UInt32)

Events:
    ├── 🔔 OverTemperatureAlarm (AlarmConditionType)
    │    ├── Severity: 900
    │    ├── Message: "Temperature too high"
    │    └── SourceName: "TemperatureSensor"
    └── 🔔 SensorFaultCondition (AlarmConditionType)
         ├── Severity: 500
         ├── Message: "Sensor malfunction detected"
         └── SourceName: "TemperatureSensor"

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
import asyncio
from asyncua import Server, ua
from asyncua.common.methods import uamethod

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
logging.getLogger("asyncua").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)


# ----------------------------
# Calibration method
# ----------------------------
@uamethod
async def calibrate(parent):
    logger.info("Calibration requested (simulated).")
    return [ua.Variant(0, ua.VariantType.Int32)]  # simple status code


# ----------------------------
# Main server coroutine
# ----------------------------
async def main():
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
    await server.init()
    server.set_endpoint(endpoint)
    idx = await server.register_namespace(namespace_uri)

    objects = server.nodes.objects

    # Create a folder "Sensors"
    sensors = await objects.add_object(idx, "Sensors")

    # Create TemperatureSensor object
    sensor = await sensors.add_object(idx, "TemperatureSensor")

    # Add SensorModel variable
    sensor_model = await sensor.add_variable(idx, "SensorModel", "Virtual DHT Sensor")
    await sensor_model.set_writable(False)

    # Add Temperature variable
    temp = await sensor.add_variable(idx, "Temperature", TEMP_MIN)
    await temp.set_writable(False)

    # Add Humidity variable
    hum = await sensor.add_variable(idx, "Humidity", HUM_MIN)
    await hum.set_writable(False)

    # Add Calibrate() method
    await sensor.add_method(idx, "Calibrate", calibrate, [], [ua.VariantType.Int32])

    # ----------------------------
    # Add Alarms
    # ----------------------------
    alarm_type_node = server.get_node(ua.ObjectIds.AlarmConditionType)

    overtemp_alarm = await server.get_event_generator(etype=alarm_type_node, emitting_node=sensor)
    overtemp_alarm.event.Severity = 900
    overtemp_alarm.event.Message = ua.LocalizedText("Temperature too high")
    overtemp_alarm.event.SourceName = "TemperatureSensor"

    sensor_fault_alarm = await server.get_event_generator(etype=alarm_type_node, emitting_node=sensor)
    sensor_fault_alarm.event.Severity = 500
    sensor_fault_alarm.event.Message = ua.LocalizedText("Sensor malfunction detected")
    sensor_fault_alarm.event.SourceName = "TemperatureSensor"

    # ----------------------------
    # Set EventNotifier bits
    # ----------------------------
    await sensors.set_event_notifier([ua.EventNotifier.SubscribeToEvents])
    await sensor.set_event_notifier([ua.EventNotifier.SubscribeToEvents])

    # ----------------------------
    # Create HasEventSource reference
    # As of today this is not yet implemented in the opcua-asyncio library
    # https://github.com/FreeOpcUa/opcua-asyncio/issues/105
    # ----------------------------
    await sensors.add_reference(
        target=sensor.nodeid,
        reftype=ua.ObjectIds.HasEventSource,
        forward=True,
        bidirectional=False
    )

    # ----------------------------
    # Start server
    # ----------------------------
    async with server:
        logger.info("---------------------------------------------------")
        logger.info(f"Server started at {endpoint} with namespace {namespace_uri}")
        logger.info(f"Temperature range: {TEMP_MIN} - {TEMP_MAX}")
        logger.info(f"Humidity range: {HUM_MIN} - {HUM_MAX}")
        logger.info("---------------------------------------------------")

        TEMP_SLEEP_AVG = float(os.getenv("TEMP_SLEEP_AVG", 2.0))
        HUM_SLEEP_AVG = float(os.getenv("HUM_SLEEP_AVG", 4.0))
        SENSOR_FAULT_AVG = float(os.getenv("SENSOR_FAULT_AVG", 20.0))

        next_temp_time = time.time()
        next_hum_time = time.time()
        next_fault_time = time.time() + random.uniform(0.8 * SENSOR_FAULT_AVG, 1.2 * SENSOR_FAULT_AVG)

        try:
            while True:
                now = time.time()

                # Update temperature if its time
                if now >= next_temp_time:
                    current_temp = round(random.uniform(TEMP_MIN, TEMP_MAX), 1)
                    await temp.write_value(current_temp)
                    logger.info(f"Temperature: {current_temp}°C")

                    if current_temp > (TEMP_MIN + 0.9 * (TEMP_MAX - TEMP_MIN)):
                        await overtemp_alarm.trigger()
                        logger.info("OverTemperatureAlarm triggered")

                    # Schedule next temperature update with some jitter
                    next_temp_time = now + random.uniform(0.8 * TEMP_SLEEP_AVG, 1.2 * TEMP_SLEEP_AVG)

                # Update humidity if its time
                if now >= next_hum_time:
                    current_hum = round(random.uniform(HUM_MIN, HUM_MAX), 1)
                    await hum.write_value(current_hum)
                    logger.info(f"Humidity: {current_hum}%")

                    # Schedule next humidity update with some jitter
                    next_hum_time = now + random.uniform(0.8 * HUM_SLEEP_AVG, 1.2 * HUM_SLEEP_AVG)

                # Trigger sensor fault if its time
                if now >= next_fault_time:
                    await sensor_fault_alarm.trigger()
                    logger.info("SensorFaultCondition triggered")
                    # Schedule next fault with some jitter
                    next_fault_time = now + random.uniform(0.8 * SENSOR_FAULT_AVG, 1.2 * SENSOR_FAULT_AVG)

                # Sleep a short time to avoid busy-waiting
                await asyncio.sleep(0.1)

        finally:
            logger.info("Server stopped")

# ----------------------------
# Run server
# ----------------------------
if __name__ == "__main__":
    asyncio.run(main())
