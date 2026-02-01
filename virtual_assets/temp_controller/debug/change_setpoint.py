"""
OPC UA Temperature Controller Setpoint Helper

This script connects to a running OPC UA temperature controller server and updates
the SetPoint value of the virtual PID controller.

Usage:
    python change_setpoint.py <new_setpoint>

Example:
    python change_setpoint.py 30.0

Environment Variables:
    OPCUA_ENDPOINT (str): OPC UA server endpoint.
        Default: "opc.tcp://0.0.0:4840/freeopcua/server/"
    OPCUA_NAMESPACE (str): Namespace URI used in the server.
        Default: "http://examples.openfactory.local/opcua"
"""

import asyncio
import os
from asyncua import Client
import logging

# ----------------------------
# Logger
# ----------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("asyncua").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)


async def change_setpoint(new_setpoint: float) -> None:
    """
    Connect to the OPC UA server and change the temperature controller setpoint.

    Args:
        new_setpoint (float): Desired new setpoint value (°C).

    Environment Variables:
        OPCUA_ENDPOINT (str): OPC UA server endpoint. Default: "opc.tcp://0.0.0:4840/freeopcua/server/"
        OPCUA_NAMESPACE (str): Namespace URI used in the server. Default: "http://examples.openfactory.local/opcua"
    """
    endpoint: str = os.getenv(
        "OPCUA_ENDPOINT", "opc.tcp://0.0.0:4840/freeopcua/server/"
    )
    namespace_uri: str = os.getenv(
        "OPCUA_NAMESPACE", "http://examples.openfactory.local/opcua"
    )

    async with Client(url=endpoint) as client:
        logger.info(f"Connected to OPC UA server at {endpoint}")

        # Find the namespace index
        idx = await client.get_namespace_index(namespace_uri)

        # Browse to the TemperatureController node
        objects = client.nodes.objects
        controller_node = await objects.get_child([f"{idx}:TemperatureController"])

        # Access SetPoint variable
        setpoint_node = await controller_node.get_child([f"{idx}:Configuration", f"{idx}:SetPoint"])

        # Write the new setpoint
        await setpoint_node.write_value(new_setpoint)
        logger.info(f"Setpoint updated to {new_setpoint} °C")


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Change OPC UA temperature controller setpoint")
    parser.add_argument("setpoint", type=float, help="New setpoint value (°C)")
    args = parser.parse_args()

    asyncio.run(change_setpoint(args.setpoint))
