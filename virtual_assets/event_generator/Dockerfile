# ------------------------------------------------------------------------------
# 🐳 Dockerfile for OpenFactory Virtual Event Generator MTCAdapter
#
# This Docker image provides a lightweight container to simulate a
# Event Generator in OpenFactory. It clones and installs the
# MTCAdapters package, sets up a non-root user, and executes the adapter.
#
# Key Features:
#   - Based on Python 3.13-slim for small image footprint
#   - Runs with non-root user for better security
#   - Automatically installs MTCAdapters from GitHub
#
# Build:
#   docker build -t virtual-event-generator ./virtual_assets/event_generator
#
# ------------------------------------------------------------------------------

FROM python:3.13-slim
LABEL author="Soha Kabir" 
LABEL organisation="Concordia University"
LABEL description="Docker image for OpenFactory Virtual Event Generator "
LABEL documentation="https://github.com/openfactoryio/openfactory-virtual-assets"

ARG UNAME=vevent_gen
ARG UID=1200
ARG GID=1200

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

RUN groupadd --gid $GID $UNAME
RUN useradd --create-home --uid $UID --gid $GID $UNAME
RUN apt-get update
RUN apt-get -y install git

# python dependencies
RUN pip3 install git+https://github.com/Demo-Smart-Factory-Concordia-University/MTCAdapters.git

WORKDIR /home/$UNAME
USER $UNAME

COPY virtual_event_generator.py .

CMD ["python3", "-u", "virtual_event_generator.py"]
