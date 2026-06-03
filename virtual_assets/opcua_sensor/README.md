# Virtual OPC UA Temperature Sensor

This virtual asset simulates one or more temperature sensors for OpenFactory using OPC UA.
Each sensor exposes temperature, humidity, a calibration method, and alarm conditions.

## 📂 Contents

* `opcua_device.py` – OPC UA server generating simulated temperature and humidity readings.
* `Dockerfile` – Builds a Docker image for this asset.

## ⚙️ Configuration

The asset is configurable via environment variables.

| Variable           | Description                                          | Default                                      |
| ------------------ | ---------------------------------------------------- | -------------------------------------------- |
| `OPCUA_ENDPOINT`   | OPC UA server endpoint                               | `opc.tcp://127.0.0.1:4840/freeopcua/server/` |
| `OPCUA_NAMESPACE`  | OPC UA namespace URI                                 | `http://examples.openfactory.local/opcua`    |
| `NUM_SENSORS`      | Number of sensors to expose                          | 2                                            |
| `TEMP_MIN`         | Minimum temperature value                            | 21.0                                         |
| `TEMP_MAX`         | Maximum temperature value                            | 25.0                                         |
| `HUM_MIN`          | Minimum humidity value                               | 40.0                                         |
| `HUM_MAX`          | Maximum humidity value                               | 60.0                                         |
| `TEMP_SLEEP_AVG`   | Average interval (s) between temperature updates     | 2.0                                          |
| `HUM_SLEEP_AVG`    | Average interval (s) between humidity updates        | 4.0                                          |
| `SENSOR_FAULT_AVG` | Average interval (s) between simulated sensor faults | 20.0                                         |

## 📁 OPC UA Server Structure

If `NUM_SENSORS=2`, the structure looks like this (under `0:Root/0:Objects`):

```
📁 2:Sensors
├─ 📁 2:TemperatureSensor1
│  ├─ 📄 Variables
│  │   ├─ 2:SensorModel (Property, String, ReadOnly)
│  │   ├─ 2:Temperature (Variable, Double, ReadOnly)
│  │   └─ 2:Humidity (Variable, Double, ReadOnly)
│  ├─ ⚙️ Methods
│  │   └─ 2:Calibrate()
│  │       ├─ InputArguments: None
│  │       └─ OutputArguments: StatusCode (Enum/UInt32)
│  └─ 🔔 Events
│      ├─ OverTemperatureAlarm (AlarmConditionType)
│      │   ├─ Severity: 900
│      │   ├─ ActiveState (Boolean)
│      │   └─ InputNode: Temperature
│      └─ SensorFaultCondition (ConditionType)
│          ├─ Severity: 500
│          ├─ ActiveState (Boolean)
│          └─ Message (String)
│
└─ 📁 2:TemperatureSensor2
   └─ (same structure as above)
```

### Node behaviors

* **SensorModel** – Descriptive string identifying the sensor (e.g., `Virtual DHT TemperatureSensor3`).
* **Temperature** – Current temperature reading (°C). Updates around `TEMP_SLEEP_AVG`.
* **Humidity** – Current humidity reading (%). Updates around `HUM_SLEEP_AVG`.
* **Calibrate()** – Simulated calibration method; always returns status code `0` (success).
* **OverTemperatureAlarm** – Triggered when temperature exceeds 90% of the configured range.
* **SensorFaultCondition** – Triggered around `SENSOR_FAULT_AVG` intervals to simulate random sensor errors.

### Timing behavior

Each sensor is assigned a random initial phase when the simulator starts.
This distributes updates across the reporting interval and avoids startup bursts when simulating large numbers of sensors.

Subsequent update intervals vary by ±20% around the configured average values (`TEMP_SLEEP_AVG`, `HUM_SLEEP_AVG`, and `SENSOR_FAULT_AVG`).

### Event distribution diagnostics

When running the simulator, periodic log messages report the average number of events generated per scheduler cycle.

These diagnostics help verify that events are evenly distributed across time and that large bursts are not created when simulating hundreds of sensors. They are particularly useful when evaluating the impact of scheduler settings and validating load-generation behavior before connecting the simulator to Kafka or other downstream services.

## 🚀 Deploying

The virtual sensor can be deployed on a local machine or in the OpenFactory cluster.

### 🖥️ Local machine

Run as a Docker container:

```bash
docker run -d --name virtual-opcua-sensor -p 4840:4840 -e NUM_SENSORS=5 ghcr.io/openfactoryio/virtual-opcua-sensor
```

or with Docker Compose:

```yaml
services:
  virtual-opcua-sensor:
    image: ghcr.io/openfactoryio/virtual-opcua-sensor
    container_name: virtual-opcua-sensor
    ports:
      - "4840:4840"
    environment:
      - NUM_SENSORS=5
```

Start it with:

```bash
docker compose up -d
```

👉 Use `NUM_SENSORS` to control how many virtual sensors are created.

To connect to OpenFactory, create `sensor.yml` (for the first sensor):

```yaml
devices:
  vtempsens1:
    uuid: VIRTUAL-OPCUA-SENS-001

    connector:
      type: opcua

      server:
        uri: opc.tcp://<your-host-ip>:4840/freeopcuas/server/

      variables:
        temp:
          node_id: ns=2;i=4
          tag: Temperature
        hum:
          node_id: ns=2;i=5
          tag: Humidity
        sensor_model: 
          node_id: ns=2;i=3
          tag: SensorModel

      events:
        sensor_events:
          node_id: ns=2;i=2
        
```
where `<your-host-ip>` is the IP address of the host on which you deployed the virtual sensor.
If you are deploying inside the Dev Container of this repository, you can use `${CONTAINER_IP}` for your host IP address.

For multiple sensors, just duplicate the `vtempsens1` section and change the UUID and the node IDs of the variables and events.
For each new sensore the index, in the node ID needs to be incremented by 6.

Alternatively use the `browse_path` to indentify the OPC UA nodes instead of the `node_id`:
```
devices:
  vtempsens1:
    uuid: VIRTUAL-OPCUA-SENS-001

    connector:
      type: opcua

      server:
        uri: opc.tcp://<your-host-ip>:4840/freeopcuas/server/

      variables:
        temp:
          browse_path: 0:Root/0:Objects/2:Sensors/2:TemperatureSensor1/2:Temperature
          tag: Temperature
        hum:
          browse_path: 0:Root/0:Objects/2:Sensors/2:TemperatureSensor1/2:Humidity
          tag: Humidity
        sensor_model: 
          browse_path: 0:Root/0:Objects/2:Sensors/2:TemperatureSensor1/2:SensorModel
          tag: SensorModel

      events:
        sensor_events:
          browse_path: 0:Root/0:Objects/2:Sensors/2:TemperatureSensor1
```

To connect your sensors to OpenFactory:
```bash
ofa device up sensor.yml
```

---

### ☁️ On the OpenFactory cluster

Deploy as a Swarm service:

```bash
docker service create \
  --name virtual-opcua-sensor \
  --publish 4840:4840 \
  --env NUM_SENSORS=3 \
  ghcr.io/openfactoryio/virtual-opcua-sensor
```

## 🛠 Development

Inside the devcontainer, make sure Kafka is running:

```bash
spinup
```

and the OpenFactory OPC UA Connector is deployed:

```bash
opcua-connector-up
```

Run the sensor locally for testing:

```bash
python virtual_assets/opcua_sensor/opcua_device.py
```

Build the Docker image:

```bash
docker build -t virtual-opcua-sensor ./virtual_assets/opcua_sensor
```
