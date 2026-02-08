"""
Main executable for the virtual barcode reader simulation with OPC UA interface.

Features:
- Sets up an asyncua OPC UA server with a hierarchical BarcodeReader object.
- Supports automatic and manual simulation modes.
- Automatically generates barcodes at random intervals in AUTOMATIC mode.
- Allows manual triggering of barcodes via OPC UA method.
- Simulates read failures based on configurable failure probability.
- Updates OPC UA nodes with last code, timestamp, and read success.
- Triggers events for failed reads or simulated device errors.
"""

import time
import asyncio
import random
import logging
from asyncua import Server, Node
from typing import Dict, Any

from src.barcode_reader_setup import create_barcode_reader, generate_barcode_method
from src.logging_config import setup_logging
import src.config as Config

# ----------------------------
# Logger
# ----------------------------
setup_logging()
logger = logging.getLogger(__name__)


# ----------------------------
# Subscription handler
# ----------------------------
class SimulationSubscriptionHandler:
    """ Updates internal simulation state on OPC UA node changes. """

    def __init__(self, sim_state: Dict[str, Any]):
        """
        Initialize the simulation subscription handler.

        Args:
            sim_state (Dict[str, Any]): Dictionary containing internal simulation variables and OPC UA node references:
                - mode_value: "AUTOMATIC" or "MANUAL"
                - mean_arrival_value: average seconds between automatic barcode generation
                - nodes: references to OPC UA nodes for simulation parameters
        """
        self.sim_state = sim_state

    def datachange_notification(self, node: Node, val: Any, data: Any) -> None:
        """
        Called by asyncua when a subscribed node changes.

        Updates the internal simulation state used by the main loop.

        Args:
            node (Node): OPC UA node that changed.
            val (Any): New value of the node.
            data (Any): Additional subscription data.
        """
        try:
            if node == self.sim_state["nodes"]["mode"]:
                self.sim_state["mode_value"] = str(val).upper()
                logger.info(f"Simulation mode updated to {val}")
            elif node == self.sim_state["nodes"]["mean_arrival_time"]:
                self.sim_state["mean_arrival_value"] = float(val)
                logger.info(f"Mean arrival time updated to {val}")
        except Exception as e:
            logger.warning(f"Failed to update simulation state for {node}: {e}")


# ----------------------------
# Main server loop
# ----------------------------
async def main() -> None:
    """
    Main OPC UA server loop running the virtual BarcodeReader simulation.

    This function initializes and runs an asyncua OPC UA server, creates the
    BarcodeReader node hierarchy, subscribes to simulation parameters, and
    continuously drives the barcode reader simulation based on the configured mode.

    Behavior:
        - The BarcodeReader object tree is created under the OPC UA Objects folder.
        - Simulation parameters (Mode and MeanArrivalTime) are monitored via OPC UA
          data change subscriptions and applied dynamically.
        - In AUTOMATIC mode, barcode reads are generated at random intervals drawn
          from an exponential distribution with mean MeanArrivalTime.
        - In MANUAL mode, automatic generation is disabled and barcode generation
          is expected to be triggered via the GenerateCode() OPC UA method.
        - Each simulated read updates the State nodes (LastCode, LastTimestamp,
          ReadSuccess) and may trigger a NoReadEvent depending on FailureRate.

    Subscriptions:
        - Mode: Controls whether the reader runs in AUTOMATIC or MANUAL mode.
        - MeanArrivalTime: Controls the average time between automatic barcode reads.

    Notes:
        - The server runs until interrupted.
        - Automatic barcode generation uses a Poisson process model (exponential
          inter-arrival times) to simulate irregular part arrivals.
    """
    # --- Server setup ---
    server = Server()
    await server.init()
    server.set_endpoint(Config.OPCUA_ENDPOINT)
    idx = await server.register_namespace(Config.OPCUA_NAMESPACE)
    objects = server.nodes.objects

    # --- Create BarcodeReader OPC UA tree ---
    nodes = await create_barcode_reader(server, idx, objects)

    # --- Internal simulation state ---
    sim_state = {
        "mode_value": await nodes["mode"].read_value(),
        "mean_arrival_value": await nodes["mean_arrival_time"].read_value(),
        "nodes": {
            "mode": nodes["mode"],
            "mean_arrival_time": nodes["mean_arrival_time"],
        }
    }

    # --- Subscribe to simulation parameters ---
    handler = SimulationSubscriptionHandler(sim_state)
    subscription = await server.create_subscription(100, handler)
    for node in sim_state["nodes"].values():
        await subscription.subscribe_data_change(node)

    # --- Start server ---
    async with server:
        logger.info(f"Server started at {Config.OPCUA_ENDPOINT} with namespace {Config.OPCUA_NAMESPACE}")
        next_auto_time = time.time() + random.expovariate(1.0 / sim_state["mean_arrival_value"])

        try:
            while True:
                now = time.time()
                if sim_state["mode_value"] == "AUTOMATIC" and now >= next_auto_time:
                    await generate_barcode_method(parent=None, code="", nodes=nodes)
                    next_auto_time = now + random.expovariate(1.0 / sim_state["mean_arrival_value"])
                await asyncio.sleep(Config.DT_SIM)

        finally:
            logger.info("Server stopped")
            await subscription.delete()


if __name__ == "__main__":
    asyncio.run(main())
