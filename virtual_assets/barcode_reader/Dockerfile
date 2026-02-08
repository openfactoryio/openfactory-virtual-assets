# ------------------------------------------------------------------------------
# 🐳 Dockerfile for OpenFactory Virtual OPC UA Barcode Reader
#
# This Docker image provides a lightweight container to simulate a
# barcode reader in OpenFactory. It sets up the Python environment,
# configures a non-root user, and runs the OPC UA sensor server.
#
# Key Features:
#   - Based on Python 3.13-slim for small image footprint
#   - Runs with non-root user for better security
#   - Logs output to console for easy monitoring
#
# Build:
#   docker build -t virtual-opcua-barcode-reader ./virtual_assets/barcode_reader
#
# Run:
#   docker run -d -p 4840:4840 virtual-opcua-barcode-reader
#
# ------------------------------------------------------------------------------

FROM python:3.13-slim
LABEL description="Docker image for OpenFactory Virtual OPC UA Barcode Reader"
LABEL documentation="https://github.com/openfactoryio/openfactory-virtual-assets"

ARG UNAME=vopcua_temp_ctrl
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
RUN pip install --no-cache-dir asyncua

# Set working directory
WORKDIR /home/$UNAME
USER $UNAME

# Copy code
COPY . .

# Default command to start the OPC UA server
CMD ["python3", "-um", "src.barcode_reader"]
