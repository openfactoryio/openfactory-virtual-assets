# Virtual OPC UA Temperature Sensor

This virtual asset simulates a temperature sensor for OpenFactory using OPC UA.

## 📂 Contents

* `opcua_device.py` – OPC UA server generating simulated temperature and humidity readings.
* `Dockerfile` – Builds a Docker image for this asset.

## ⚙️ Configuration

The asset is configurable via environment variables.

| Variable           | Description                                          | Default                                      |
| ----------------- | ----------------------------------------------------- | -------------------------------------------- |
| `OPCUA_ENDPOINT`   | OPC UA server endpoint                               | `opc.tcp://127.0.0.1:4840/freeopcua/server/` |
| `OPCUA_NAMESPACE`  | OPC UA namespace URI                                 | `http://examples.openfactory.local/opcua`    |
| `TEMP_MIN`         | Minimum temperature value                            | 21.0                                         |
| `TEMP_MAX`         | Maximum temperature value                            | 25.0                                         |
| `HUM_MIN`          | Minimum humidity value                               | 40.0                                         |
| `HUM_MAX`          | Maximum humidity value                               | 60.0                                         |
| `TEMP_SLEEP_AVG`   | Average interval (s) between temperature updates     | 2.0                                          |
| `HUM_SLEEP_AVG`    | Average interval (s) between humidity updates        | 4.0                                          |
| `SENSOR_FAULT_AVG` | Average interval (s) between simulated sensor faults | 20.0                                         |

## 📁 OPC UA Server Structure

```
📁 Sensors
└─ 📁 TemperatureSensor
   ├─ 📄 Variables
   │   ├─ SensorModel (Writable)   
   │   ├─ Temperature (Writable)
   │   └─ Humidity (Writable)
   ├─ ⚙️ Methods
   │   └─ Calibrate()
   └─ 🔔 Alarms
       ├─ OverTemperatureAlarm (Severity: 900)
       └─ SensorFaultCondition (Severity: 500)
```

- **SensorModel** – Descriptive string identifying the sensor
- **Temperature** – Current temperature reading (°C). Updates at intervals around `TEMP_SLEEP_AVG`.
- **Humidity** – Current humidity reading (%). Updates at intervals around `HUM_SLEEP_AVG`.
- **Calibrate()** – Simulated calibration method; returns status code `0`.
- **OverTemperatureAlarm** – Triggered when temperature exceeds 90% of configured range.
- **SensorFaultCondition** – Triggered at intervals around `SENSOR_FAULT_AVG` to simulate sensor errors.

## 🚀 Deploying

The virtual sensor can be deployed either on a local machine or on the OpenFactory cluster.

### 🖥️ Local machine
Deploy the virtual sensor from the repository of OpenFactory as a Docker container:
```bash
docker run -d --name virtual-opcua-sensor -p 4840:4840 ghcr.io/openfactoryio/virtual-opcua-sensor
```

or use this Docker Compose file:

```yaml
services:
  virtual-opcua-sensor:
    image: ghcr.io/openfactoryio/virtual-opcua-sensor
    container_name: virtual-opcua-sensor
    ports:
      - "4840:4840"
```

and start it with:

```bash
docker compose up -d
```

> Note: you can select a specific version of the sensor. For example `ghcr.io/openfactoryio/virtual-opcua-sensor:v0.4.1`.
> You should choose the same version as the OpenFactory version you are using (as displayed by `ofa version`)

To connect the virtual sensor to OpenFactory, store the following config in `sensor.yml`:

```yaml
devices:
  vtempsens:
    uuid: VIRTUAL-OPCUA-SENS-001

    connector:
      type: opcua

      server:
        uri: opc.tcp://<ip-address-local-machine>:4840/freeopcua/server/
        namespace_uri: http://examples.openfactory.local/opcua

      device:
        path: Sensors/TemperatureSensor

        variables:
          temp: Temperature
          hum: Humidity
          sensor_model: SensorModel

        methods:
          calibrate: Calibrate
```

where `<ip-address-local-machine>` is the IP address of the machine on which your virtual sensor is running.
If you deployed the virtual sensor in the devcontainer of this repo, then you can use:

```yaml
uri: opc.tcp://${CONTAINER_IP}:4840/freeopcua/server/
```

Connect the virtual sensor to OpenFactory with:

```bash
ofa device up sensor.yml
```

---

### ☁️ On the OpenFactory cluster

To deploy the virtual sensor as a service on the OpenFactory cluster, run from a manager node:

```bash
docker service create \
  --name virtual-opcua-sensor \
  --network factory-net \
  --publish 4840:4840 \
  ghcr.io/openfactoryio/virtual-opcua-sensor
```

To connect the virtual sensor to OpenFactory, store the following config in `sensor.yml`:

```yaml
devices:
  vtempsens:
    uuid: VIRTUAL-OPCUA-SENS-001

    connector:
      type: opcua

      server:
        uri: opc.tcp://virtual-opcua-sensor:4840/freeopcua/server/
        namespace_uri: http://examples.openfactory.local/opcua

      device:
        path: Sensors/TemperatureSensor

        variables:
          temp: Temperature
          hum: Humidity
          sensor_model: SensorModel

        methods:
          calibrate: Calibrate
```
and run:

```bash
ofa device up sensor.yml
```

## 🛠 Development

Make sure you are in the devcontainer and that the Kafka cluster is running:

```bash
spinup
```

You can run the virtual sensor directly for testing it:
```
python virtual_assets/opcua_sensor/opcua_device.py
```

To build the Docker image for the virtual temperature sensor:

```bash
docker build -t virtual-opcua-sensor ./virtual_assets/opcua_sensor
```
