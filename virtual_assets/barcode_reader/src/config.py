import os

# ----------------------------
# General
# ----------------------------
VERSION = os.getenv("VERSION", "dev")
OPCUA_ENDPOINT = os.getenv("OPCUA_ENDPOINT", "opc.tcp://0.0.0.0:4840")
OPCUA_NAMESPACE = os.getenv("OPCUA_NAMESPACE", "http://examples.openfactory.local/opcua")
DT_SIM = float(os.getenv("DT_SIM", 0.1))

# ----------------------------
# Logging configuration
# ----------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# ----------------------------
# Simualtion configuration
# ----------------------------
SIM_MEAN_ARRIVAL_TIME = float(os.getenv("SIM_MEAN_ARRIVAL_TIME", 2.0))
SIM_FAILURE_RATE = float(os.getenv("SIM_FAILURE_RATE", 0.05))
SIM_DEVICE_ERROR_RATE = float(os.getenv("SIM_DEVICE_ERROR_RATE", 0.01))
