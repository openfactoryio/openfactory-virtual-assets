# ------------------------------------------------------------------------------
# 🐳 Dockerfile for OpenFactory Virtual Temperature Sensor MTCAdapter
#
# This Docker image provides a lightweight container to simulate a
# temperature sensor in OpenFactory. It clones and installs the
# MTCAdapters package, sets up a non-root user, and executes the adapter.
#
# Key Features:
#   - Based on Python 3.13-slim for small image footprint
#   - Runs with non-root user for better security
#   - Automatically installs MTCAdapters from GitHub
#
# Build:
#   docker build -t virtual-temp-sensor ./virtual_assets/temp_sensor
#
# ------------------------------------------------------------------------------

FROM python:3.13-slim
LABEL description="Docker image for OpenFactory Virtual Temperature Sensor"
LABEL documentation="https://github.com/openfactoryio/openfactory-virtual-assets"

ARG UNAME=vtemp_sens
ARG UID=1200
ARG GID=1200

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install git and non-root user
RUN apt-get update && apt-get install -y git \
    && groupadd --gid $GID $UNAME \
    && useradd --create-home --uid $UID --gid $GID $UNAME \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# python dependencies
RUN pip install --no-cache-dir git+https://github.com/Demo-Smart-Factory-Concordia-University/MTCAdapters.git

WORKDIR /home/$UNAME
USER $UNAME

COPY adapter.py .

CMD ["python3", "-u", "adapter.py"]
