# Virtual OPC UA PID Temperature Controller

This is a **virtual OPC UA device** that simulates a PID-controlled temperature controller. It is designed for testing and demonstration purposes and integrates with the **OpenFactory virtual assets framework**.

## Device Overview

The controller provides:

* **State monitoring**: Current temperature and control output
* **Configuration**: Setpoint, mode, and full PID tuning parameters
* **Output constraints**: Minimum and maximum output limits
* **Controller actions**: Reset and mode switching
* **Event notifications**: Overtemperature and fault conditions

## Features

* **Full PID tuning**: Separate Proportional, Integral, and Derivative gains with enable/disable switches
* **Configurable setpoint and mode**: AUTO or MANUAL
* **Limits for output signal**: Prevents actuator saturation
* **Simulation of controller behavior**: Outputs a control signal based on PID calculations
* **Event generation**: Alarms and fault conditions are triggered under configurable conditions

## 📁 OPC UA Server Structure

The OPC UA node structure is as follows:

```text
📁 2:TemperatureController
│
├─ 2:Model (Property, String, ReadOnly)
├─ 2:SoftwareRevision (Property, String, ReadOnly)
├─ 2:Manufacturer (Property, String, ReadOnly)
├─ 2:License (Property, String, ReadOnly)
│
├─ 📁 2:State
│   ├─ 2:CurrentTemperature (Variable, Double, ReadOnly)
│   ├─ 2:ControlOutput (Variable, Double, ReadOnly)
│   └─ 2:LastUpdateTime (Variable, DateTime, ReadOnly)
│
├─ 📁 2:Configuration
│   ├─ 2:ControllerModel (Property, String, ReadOnly)
│   ├─ 2:SetPoint (Variable, Double, Read/Write)
│   ├─ 2:Mode (Variable, String, Read/Write, Enum: AUTO/MANUAL)
│   └─ 📁 2:PID
│       ├─ 📁 2:Proportional
│       │   ├─ 2:Gain (Variable, Double, Read/Write)
│       │   └─ 2:Enabled (Variable, Boolean, Read/Write)
│       ├─ 📁 2:Integral
│       │   ├─ 2:Gain (Variable, Double, Read/Write)
│       │   ├─ 2:Enabled (Variable, Boolean, Read/Write)
│       │   └─ 2:WindupLimit (Variable, Double, Read/Write)
│       └─ 📁 2:Derivative
│           ├─ 2:Gain (Variable, Double, Read/Write)
│           └─ 2:Enabled (Variable, Boolean, Read/Write)
│
├─ 📁 2:OutputConstraints
│   ├─ 2:OutputMin (Variable, Double, Read/Write)
│   └─ 2:OutputMax (Variable, Double, Read/Write)
│
├─ 📁 2:ControllerActions
│   ├─ 2:ResetController()
│   │   ├─ InputArguments: None
│   │   └─ OutputArguments: StatusCode (Enum/UInt32)
│   └─ 2:SwitchMode()
│       ├─ InputArguments: NewMode (String)
│       └─ OutputArguments: StatusCode (Enum/UInt32)
│
└─ 📁 2:Events
    ├─ OverTemperatureAlarm (AlarmConditionType)
    │   ├─ Severity: 900
    │   ├─ ActiveState (Boolean)
    │   └─ InputNode: State/CurrentTemperature
    └─ ControllerFaultCondition (ConditionType)
        ├─ Severity: 500
        ├─ ActiveState (Boolean)
        └─ Message (String)
```

## ⚙️ Configuration

The controller OPC UA server can be configured using environment variables.

### 🖥️ OPC UA Server

| Variable          | Type      | Default                                   | Description                            |
| ----------------- | --------- | ----------------------------------------- | -------------------------------------- |
| `OPCUA_ENDPOINT`  | string    | `opc.tcp://0.0.0:4840/freeopcua/server/`  | OPC UA server endpoint URL             |
| `OPCUA_NAMESPACE` | string    | `http://examples.openfactory.local/opcua` | Namespace URI registered by the server |
| `UPDATE_INTERVAL` | float (s) | `1.0`                                     | How often OPC UA nodes are updated     |
| `DT_SIM`          | float (s) | `0.1` (hardcoded)                         | Simulation timestep                    |

---

### 🏭 Plant Selection

| Variable     | Type   | Default   | Description                              |
| ------------ | ------ | --------- | ---------------------------------------- |
| `PLANT_TYPE` | string | `two_pt1` | Plant model type: `"pt1"` or `"two_pt1"` |

---

### 🌍 Thermal Environment

| Variable                    | Type       | Default | Description               |
| --------------------------- | ---------- | ------- | ------------------------- |
| `PLANT_INITIAL_TEMPERATURE` | float (°C) | `22.0`  | Initial plant temperature |
| `AMBIENT_TEMPERATURE`       | float (°C) | `20.0`  | Ambient temperature       |

---

### 🔥 PT1 Plant Parameters (used when `PLANT_TYPE=pt1`)

| Variable    | Type      | Default | Description                     |
| ----------- | --------- | ------- | ------------------------------- |
| `PLANT_TAU` | float (s) | `10.0`  | Thermal time constant           |
| `PLANT_K`   | float     | `1.0`   | Heater gain (°C per unit input) |

---

### 🔥🔥 Two-PT1 Plant Parameters (used when `PLANT_TYPE=two_pt1`)

| Variable      | Type           | Default | Description                                    |
| ------------- | -------------- | ------- | ---------------------------------------------- |
| `PLANT_TAU_P` | float (s)      | `10.0`  | Plant thermal time constant                    |
| `PLANT_K_P`   | float (°C/W)   | `0.5`   | Plant gain (temperature rise per heater power) |
| `PLANT_TAU_H` | float (s)      | `1.0`   | Heater time constant                           |
| `PLANT_K_H`   | float (W/unit) | `100.0` | Heater gain (max power per control unit)       |

---

## 🚀 Deploying

The virtual temperature controller can be deployed on a local machine or in the OpenFactory cluster.

### 🖥️ Local machine

Run as a Docker container:

```bash
docker run -d -p 4840:4840 --name virtual-opcua-temp-controller ghcr.io/openfactoryio/virtual-opcua-temp-controller
```

To connect your sensors to OpenFactory:
```bash
ofa device up opcua_temp_ctrl.yml
```
where `opcua_temp_ctrl.yml` is the OpenFactory device configuration file of the controller. You can use the one provided in this repo under [virtual_assets/temp_controller/opcua_temp_ctrl.yml](virtual_assets/temp_controller/opcua_temp_ctrl.yml).

---

### ☁️ On the OpenFactory cluster

Deploy as a Swarm service:

```bash
docker service create \
  --name virtual-opcua-temp-controller \
  --publish 4840:4840 \
  --env PLANT_TYPE=pt1 \
  ghcr.io/openfactoryio/virtual-opcua-temp-controller
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

Run the controller locally for testing:

```bash
cd virtual_assets/temp_controller
python -m src.temp_controller
```

Build the Docker image:

```bash
docker build -t virtual-opcua-temp-controller ./virtual_assets/temp_controller
```
