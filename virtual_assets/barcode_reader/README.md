# Virtual OPC UA Barcode Reader

This is a **virtual OPC UA device** that simulates a barcode reader. It is designed for testing, development, and demonstrations, and integrates with the **OpenFactory virtual assets framework**.

The device can automatically generate barcode reads, simulate read failures, and expose realistic state and event information through OPC UA.

---

## Device Overview

The virtual barcode reader provides:

* **State monitoring**: Last scanned barcode, timestamp, and read success
* **Simulation control**: Automatic or manual barcode generation
* **Failure simulation**: Configurable probability of read errors
* **Manual triggering**: OPC UA method to force barcode reads
* **Event notifications**: “No read” and simulated device fault events

---

## Features

* **Automatic barcode generation** based on a configurable average arrival time
* **Manual barcode triggering** via OPC UA method calls
* **Failure rate simulation** to mimic real-world scanning issues
* **Device state exposure** (ready status, trigger input, last read result)
* **Event generation** for failed reads and simulated device errors

---

## 📁 OPC UA Server Structure

The OPC UA node structure is as follows:

```text
📁 2:BarcodeReader
│
├─ 2:Model (Property, String, ReadOnly)
├─ 2:SoftwareRevision (Property, String, ReadOnly)
├─ 2:Manufacturer (Property, String, ReadOnly)
├─ 2:License (Property, String, ReadOnly)
│
├─ 📁 2:State
│   ├─ 2:LastCode (Variable, String, ReadOnly)
│   ├─ 2:LastTimestamp (Variable, DateTime, ReadOnly)
│   ├─ 2:ReadSuccess (Variable, Boolean, ReadOnly)
│   ├─ 2:DeviceReady (Variable, Boolean, ReadOnly)
│   └─ 2:TriggerInputActive (Variable, Boolean, ReadOnly)
│
├─ 📁 2:Simulation
│   ├─ 2:Mode (Variable, String, Read/Write, Enum: AUTOMATIC / MANUAL)
│   ├─ 2:MeanArrivalTime (Variable, Double, Read/Write)
│   │     └─ Average seconds between generated barcodes in AUTOMATIC mode
│   ├─ 2:FailureRate (Variable, Double, Read/Write)
│   │     └─ Probability of a failed read (0–1)
│   ├─ 2:SetAutomaticMode()
│   │     └─ OutputArguments: StatusCode (UInt32)
│   ├─ 2:SetManualMode()
│   │     └─ OutputArguments: StatusCode (UInt32)
│   └─ 2:GenerateCode()
│      ├─ InputArguments: Code (String, Optional)
│      └─ OutputArguments: StatusCode (UInt32)
│          └─ If Code is empty, a random 12-digit barcode is generated
|
├─ NoReadEvent (BaseEventType)
│   └─ Message: "No code detected during trigger"
│
└─ ReaderErrorEvent (BaseEventType)
    └─ Message: "Simulated device fault — reader unavailable"
```

---

## ⚙️ Configuration

The barcode reader OPC UA server can be configured using environment variables.

### 🖥️ OPC UA Server

| Variable          | Type      | Default                                   | Description                            |
| ----------------- | --------- | ----------------------------------------- | -------------------------------------- |
| `OPCUA_ENDPOINT`  | string    | `opc.tcp://0.0.0.0:4840`                  | OPC UA server endpoint URL             |
| `OPCUA_NAMESPACE` | string    | `http://examples.openfactory.local/opcua` | Namespace URI registered by the server |
| `DT_SIM`          | float (s) | `0.1`                                     | Simulation loop timestep               |

---

### 🎯 Barcode Simulation

| Variable                | Type      | Default | Description                                     |
| ----------------------- | --------- | ------- | ----------------------------------------------- |
| `SIM_MEAN_ARRIVAL_TIME` | float (s) | `2.0`   | Average time between automatic barcode reads    |
| `SIM_FAILURE_RATE`      | float     | `0.1`   | Probability of a simulated read failure (0–1)   |
| `SIM_DEVICE_ERROR_RATE` | float     | `0.1`   | Probability of a simulated device failure (0–1) |

---

## 🔁 Operating Modes

### AUTOMATIC

The reader generates barcode reads automatically. The time between reads follows an exponential distribution with mean `MeanArrivalTime`.

### MANUAL

No automatic reads are generated. Barcodes are only produced when:

* `GenerateCode()` is called via OPC UA, or
* The simulation is switched back to AUTOMATIC mode.

---

## 🚀 Deploying

The virtual barcode reader can be deployed locally or in the OpenFactory cluster.

### 🖥️ Local machine

Run as a Docker container:

```bash
docker run -d -p 4840:4840 --name virtual-opcua-barcode-reader ghcr.io/openfactoryio/virtual-opcua-barcode-reader
```

Connect it to OpenFactory:

```bash
ofa device up opcua_barcode_reader.yml
```

You can use the example device configuration from this repository:
`virtual_assets/barcode_reader/opcua_barcode_reader.yml`

---

### ☁️ On the OpenFactory cluster

Deploy as a Swarm service:

```bash
docker service create \
  --name virtual-opcua-barcode-reader \
  --publish 4840:4840 \
  ghcr.io/openfactoryio/virtual-opcua-barcode-reader
```

---

### 📝 Logging

The verbosity of the barcode reader server logs can be configured via an environment variable.

| Variable    | Type   | Default | Description                                                                                 |
| ----------- | ------ | ------- | ------------------------------------------------------------------------------------------- |
| `LOG_LEVEL` | string | `INFO`  | Logging level for the application. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

This controls how much runtime information the server prints to the console.

**Examples:**

More detailed logs for debugging:

```bash
docker run -e LOG_LEVEL=DEBUG -p 4840:4840 ghcr.io/openfactoryio/virtual-opcua-barcode-reader
```

Only show warnings and errors:

```bash
docker run -e LOG_LEVEL=WARNING -p 4840:4840 ghcr.io/openfactoryio/virtual-opcua-barcode-reader
```


---

## 🛠 Development

Inside the devcontainer, make sure Kafka is running:

```bash
spinup
```

Deploy the OpenFactory OPC UA connector:

```bash
opcua-connector-up
```

Run the barcode reader locally:

```bash
cd virtual_assets/barcode_reader
python -m src.barcode_reader
```

To build the Docker image run from the projet root:

```bash
docker build -t virtual-opcua-barcode-reader ./virtual_assets/barcode_reader
```
