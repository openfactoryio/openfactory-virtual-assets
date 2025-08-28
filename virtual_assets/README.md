# Virtual Assets

This directory contains virtual assets for OpenFactory.

Each asset is organized in its own subdirectory and includes the source code plus a `Dockerfile` to build its container image.
Automated workflows in [.github/workflows](../.github/workflows) build these images and publish them to the OpenFactoryIO GitHub Container Registry.

Assets are typically configurable via environment variables, as documented in their respective subdirectories.

## Example: Virtual Temperature Sensor

Below is a minimal example configuration for a virtual temperature sensor:

```yaml
devices:
  vtempsens:
    uuid: VIRTUAL-TEMP-SENS-002     # Unique identifier for this virtual device

    connector:
      type: mtconnect               # Connector type
      agent:
        port: 2102                  # Port the MTConnect agent will listen on
        device_xml: github://openfactoryio:openfactory-virtual-assets@/virtual_assets/temp_sensor/device.xml
                                    # Path to the device XML definition in the repository
        adapter:
          image: ghcr.io/openfactoryio/virtual-temp-sensor:${OPENFACTORY_VERSION}
                                    # Docker image of the virtual adapter
          port: 7878                # Port exposed by the adapter
          environment:
            - SLEEP_INTERVAL=4.0    # Interval between simulated readings
            - MIN_TEMP=200          # Minimum temperature value
            - MAX_TEMP=220          # Maximum temperature value
            - ADAPTER_PORT=7878     # Adapter’s exposed port
```

### Deploying the Virtual Asset

1. Save the YAML configuration above to a file, e.g., `temp_sensor.yml`.
2. Deploy the asset in OpenFactory with a single command:

```bash
ofa device up temp_sensor.yml
```

OpenFactory will automatically build and start the virtual asset based on this configuration.

