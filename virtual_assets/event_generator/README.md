# Virtual Event Generator

This virtual asset simulates a event generator for OpenFactory.

## 📂 Contents

* `virtual_event_generator.py` – Adapter code generating simulated event readings.
* `device.xml` – MTConnect device definition.
* `Dockerfile` – Builds a Docker image for this asset.

## ⚙️ Configuration

The asset is configurable via environment variables.

| Variable         | Description                         | Default |
| ---------------- | ----------------------------------- | ------- |
| `SLEEP_INTERVAL` | Interval between simulated readings | 3.0     |
| `ADAPTER_PORT`   | Port exposed by the adapter         | 7878    |

Example YAML configuration for OpenFactory:

```yaml
devices:
  vtempsens:
    uuid: VIRTUAL-EVENT-GEN-001
    connector:
      type: mtconnect
      agent:
        port: 2104
        device_xml: github://openfactoryio:openfactory-virtual-assets@/virtual_assets/event_generator/device.xml
        adapter:
          image: ghcr.io/openfactoryio/virtual-event-generator:${OPENFACTORY_VERSION}
          port: 7878
          environment:
            - SLEEP_INTERVAL=3.0
            - ADAPTER_PORT=7878
```

> **Tip:** Save this YAML as `event_generator.yml` (or any preferred name) before deploying.

## 🚀 Deploying

Deploy the virtual event generator:

```bash
ofa device up event_generator.yml
```

OpenFactory will automatically build and deploy the virtual asset based on this configuration.

## 🛠 Development

Make sure you are in the devcontainer and that the Kafka cluster is running:

```bash
spinup
```

Build the Docker image for the virtual temperature sensor:

```bash
docker build -t virtual-event-generator ./virtual_assets/event_generator
```

Deploy the asset:

```bash
ofa device up virtual_assets/event_generator/event_generator.yml 
```

Inspect the deployed asset:

```bash
ofa asset inspect VIRTUAL-EVENT-GEN-001
```

Teardown the asset:

```bash
ofa device down virtual_assets/event_generator/event_generator.yml  
```
