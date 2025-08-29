# OpenFactory Virtual Assets

[![Dev Container Ready](https://img.shields.io/badge/devcontainer-ready-green?logo=visualstudiocode\&labelColor=2c2c2c)](.devcontainer/README.md) <img src="https://img.shields.io/badge/python-3.13-blue?logo=python&logoColor=white" alt="Python Version" />
![License](https://img.shields.io/github/license/openfactoryio/openfactory-virtual-assets?style=flat-square)

A collection of virtual assets for OpenFactory. Each asset simulates a device and can be used for testing, development, or demonstration purposes.

Virtual assets are organized in `virtual_assets/`, and each asset has its own subdirectory with source code, a `Dockerfile`, and a README explaining its configuration and usage.

## 🚀 Quick Start

Deploying a virtual asset involves **two simple steps**:

1. **Create a configuration file**
   Write a YAML file that defines the virtual device and its adapter. You can base it on the example provided in the asset’s README. For example, for the temperature sensor:

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

   Save this file as `temp_sensor.yml` (or any name you prefer).

2. **Deploy the virtual asset in OpenFactory**

   ```bash
   ofa device up temp_sensor.yml
   ```

OpenFactory will automatically build and deploy the virtual asset based on this configuration.

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

* Add new virtual assets in their own subdirectory under `virtual_assets/`.
* Include a README for each asset explaining configuration and deployment.

## 🛠 Development

### 🧪 Install for Development

Install in editable mode with development tools:

```bash
pip install -e .[dev]
```

> 🔧 For a zero-configuration local dev environment using Docker and VS Code, see [Development Container Setup](.devcontainer/README.md)

### 💻 CLI Commands

Use the `ofa` command for deploying and managing virtual assets.

### ✅ Code Quality

Run linting checks with:

```bash
flake8 .
```
