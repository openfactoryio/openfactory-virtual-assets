# ------------------------------------------------------------------------------
# 🐳 Dockerfile for OpenFactory Virtual OPC UA Temperature Sensor
#
# This Docker image provides a lightweight container to simulate a
# temperature sensor in OpenFactory. It sets up the Python environment,
# configures a non-root user, and runs the OPC UA sensor server.
#
# Key Features:
#   - Based on Python 3.13-slim for small image footprint
#   - Runs with non-root user for better security
#   - Logs output to console for easy monitoring
#
# Build:
#   docker build -t virtual-opcua-sensor ./virtual_assets/opcua_sensor
#
# ------------------------------------------------------------------------------

FROM python:3.13-slim
LABEL description="Docker image for OpenFactory Virtual OPC UA Temperature Sensor"
LABEL documentation="https://github.com/openfactoryio/openfactory-virtual-assets"

ARG UNAME=vopcua_sens
ARG UID=1300
ARG GID=1300

# Prevent Python from generating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Turn off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install dependencies and create non-root user
RUN apt-get update && apt-get install -y git \
    && groupadd --gid $GID $UNAME \
    && useradd --create-home --uid $UID --gid $GID $UNAME \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir opcua

# Set working directory
WORKDIR /home/$UNAME
USER $UNAME

# Copy sensor script
COPY opcua_device.py .

# Default command to start the OPC UA server
CMD ["python3", "-u", "opcua_device.py"]
