# Virtual Temperature Sensor

This virtual asset simulates a temperature sensor for OpenFactory.

## 📂 Contents

* `adapter.py` – Adapter code generating simulated sensor readings.
* `device.xml` – MTConnect device definition.
* `Dockerfile` – Builds a Docker image for this asset.

## ⚙️ Configuration

The asset is configurable via environment variables.

| Variable         | Description                         | Default |
| ---------------- | ----------------------------------- | ------- |
| `SLEEP_INTERVAL` | Interval between simulated readings | 3.0     |
| `MIN_TEMP`       | Minimum temperature value           | 18      |
| `MAX_TEMP`       | Maximum temperature value           | 22      |
| `ADAPTER_PORT`   | Port exposed by the adapter         | 7878    |

Example YAML configuration for OpenFactory:

```yaml
devices:
  vtempsens:
    uuid: VIRTUAL-TEMP-SENS-002
    connector:
      type: mtconnect
      agent:
        port: 2102
        device_xml: github://openfactoryio:openfactory-virtual-assets@/virtual_assets/temp_sensor/device.xml
        adapter:
          image: ghcr.io/openfactoryio/virtual-temp-sensor:${OPENFACTORY_VERSION}
          port: 7878
          environment:
            - SLEEP_INTERVAL=4.0
            - MIN_TEMP=200
            - MAX_TEMP=220
            - ADAPTER_PORT=7878
```

> **Tip:** Save this YAML as `temp_sensor.yml` (or any preferred name) before deploying.

## 🚀 Deploying

### 🖥️ Local machine

Run as a Docker container:

```bash
docker run -d -p 7878:7878 --name virtual-shdr-sensor ghcr.io/openfactoryio/virtual-temp-sensor
```

Connect it to OpenFactory:

```bash
ofa device up temp_sensor.yml
```

### ☁️ On the OpenFactory cluster

Deploy as a Swarm service:

```bash
docker service create \
  --name virtual-shdr-sensor \
  --publish 7878:7878 \
  ghcr.io/openfactoryio/virtual-temp-sensor
```

## 🛠 Development

Make sure you are in the devcontainer and that the Kafka cluster is running:

```bash
spinup
```

Build the Docker image for the virtual temperature sensor:

```bash
docker build -t virtual-temp-sensor ./virtual_assets/temp_sensor
```

Deploy the asset:

```bash
ofa device up virtual_assets/temp_sensor/temp_sensor.yml 
```

Inspect the deployed asset:

```bash
ofa asset inspect VIRTUAL-TEMP-SENS-001
```

Teardown the asset:

```bash
ofa device down virtual_assets/temp_sensor/temp_sensor.yml 
```
