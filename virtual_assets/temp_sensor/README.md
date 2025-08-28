# Virtual Temperature Sensor

This virtual asset simulates a temperature sensor for OpenFactory.

## Contents

* `adapter.py` – The adapter code that generates simulated sensor readings.
* `device.xml` – MTConnect device definition for the virtual sensor.
* `Dockerfile` – Builds a Docker image for this virtual asset.

## Configuration

The asset is configurable via environment variables. The most common options:

| Variable         | Description                         | Default |
| ---------------- | ----------------------------------- | ------- |
| `SLEEP_INTERVAL` | Interval between simulated readings | 3.0     |
| `MIN_TEMP`       | Minimum temperature value           | 18      |
| `MAX_TEMP`       | Maximum temperature value           | 22      |
| `ADAPTER_PORT`   | Port exposed by the adapter         | 7878    |

Example YAML configuration to use with OpenFactory:

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

## Deploying

To deploy the virtual temperature sensor:

```bash
ofa device up temp_sensor.yml
```

OpenFactory will automatically build and deploy the virtual asset based on this configuration.
