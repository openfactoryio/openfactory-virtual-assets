"""
Main executable for the virtual temperature controller simulation with OPC UA interface.

Features:
- Sets up an asyncua OPC UA server with a hierarchical TemperatureController object.
- Selects a thermal plant model (first-order or two PT1 in series) based on environment variables.
- Autotunes PI or PID controller gains using IMC-based rules.
- Implements a discrete PIDController with optional P, I, D terms, integral anti-windup, and output saturation.
- Updates OPC UA nodes with plant state, PID outputs, and timestamps.
- Subscribes to writable OPC UA PID parameters for dynamic reconfiguration.
- Triggers overtemperature alarms if the plant exceeds setpoint by more than 5°C.

Environment Variables:
- OPCUA_ENDPOINT, OPCUA_NAMESPACE, UPDATE_INTERVAL, DT_SIM
- PLANT_TYPE, PLANT_INITIAL_TEMPERATURE, AMBIENT_TEMPERATURE
- PT1 / Two PT1 plant parameters (tau, K, tau_p, K_p, tau_h, K_h)
"""


import os
import time
import logging
import asyncio
import datetime
from asyncua import Server, Node
from typing import Dict, Any
from src.plant import ThermalPlant, TwoPT1ThermalPlant
from src.pid import PIDController
from src.autotune import autotune_pi_from_plant, autotune_pid_from_two_pt1
from src.temperature_controller_setup import create_temperature_controller


# ----------------------------
# Logger
# ----------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("asyncua").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)


# ----------------------------
# OPC UA subscription handler
# ----------------------------
class PIDSubscriptionHandler:
    """
    Subscription handler for OPC UA PID controller variables.

    This class is used with asyncua subscriptions. When a subscribed PID-related
    OPC UA variable changes, the corresponding attribute of the PIDController
    instance is automatically updated.

    Attributes:
        pid (PIDController): The PID controller instance to update.
        ctrl (Dict[str, Node]): Dictionary of OPC UA nodes corresponding to PID variables.
    """

    def __init__(self, pid: PIDController, ctrl: Dict[str, Node]) -> None:
        """
        Initialize the PID subscription handler.

        Args:
            pid (PIDController): PID controller instance.
            ctrl (Dict[str, Node]): Dictionary mapping names of PID parameters
                ("setpoint", "kp", "ki", "kd", "prop_enabled", "integ_enabled",
                "deriv_enabled", "windup", "output_min", "output_max") to
                their corresponding OPC UA Node objects.
        """
        self.pid = pid
        self.ctrl = ctrl

    def datachange_notification(self, node: Node, val: Any, data: Any) -> None:
        """
        Called by asyncua when a subscribed variable changes.

        Updates the corresponding attribute in the PIDController instance.

        Args:
            node (Node): The OPC UA node that triggered the change.
            val (Any): The new value of the node.
            data (Any): Additional subscription data provided by asyncua.
        """
        try:
            if node == self.ctrl["setpoint"]:
                self.pid.setpoint = val
            elif node == self.ctrl["kp"]:
                self.pid.kp = val
            elif node == self.ctrl["ki"]:
                self.pid.ki = val
            elif node == self.ctrl["kd"]:
                self.pid.kd = val
            elif node == self.ctrl["prop_enabled"]:
                self.pid.prop_enabled = val
            elif node == self.ctrl["integ_enabled"]:
                self.pid.integ_enabled = val
            elif node == self.ctrl["deriv_enabled"]:
                self.pid.deriv_enabled = val
            elif node == self.ctrl["windup"]:
                self.pid.windup_limit = val
            elif node == self.ctrl["output_min"]:
                self.pid.output_min = val
            elif node == self.ctrl["output_max"]:
                self.pid.output_max = val
        except Exception as e:
            logger.warning(f"Failed to update PID for node {node}: {e}")


# ----------------------------
# Main server loop with OPC UA subscriptions
# ----------------------------
async def main() -> None:
    """
    Main OPC UA server loop with temperature control simulation.

    This function sets up an OPC UA server, creates a temperature controller
    node tree, selects the plant model (PT1 or two PT1s in series), autotunes
    the PID controller, subscribes to OPC UA PID parameters, and continuously
    simulates the plant while updating the OPC UA server state.

    Behavior:
        - Plant type is selected using the environment variable `PLANT_TYPE`
          ("pt1" or "two_pt1").
        - PI or PID gains are autotuned based on the chosen plant model.
        - PID parameters in OPC UA are writable and dynamically update the PID
          controller via subscriptions.
        - Plant simulation runs at `DT_SIM` timestep; OPC UA nodes are updated
          every `UPDATE_INTERVAL`.
        - Overtemperature alarms are triggered if the temperature exceeds the
          setpoint by more than 5°C.

    Environment Variables:
        OPCUA_ENDPOINT (str): OPC UA server endpoint. Default: "opc.tcp://0.0.0:4840/freeopcua/server/"
        OPCUA_NAMESPACE (str): Namespace URI for the server. Default: "http://examples.openfactory.local/opcua"
        UPDATE_INTERVAL (float): Interval in seconds for OPC UA node updates. Default: 1.0
        DT_SIM (float): Simulation timestep in seconds. Default: 0.1

        PLANT_INITIAL_TEMPERATURE (float): Initial absolute temperature of the plant [°C]. Default: 22.0
        AMBIENT_TEMPERATURE (float): Ambient temperature [°C]. Default: 20.0

        PLANT_TYPE (str): "pt1" for single thermal plant, "two_pt1" for plant with first-order heater dynamics. Default: "two_pt1"

        # PT1 plant parameters
        PLANT_TAU (float): Thermal time constant of the PT1 plant [s]. Default: 10.0
        PLANT_K (float): Heater gain of the PT1 plant [°C/unit input]. Default: 1.0

        # Two PT1 plant parameters
        PLANT_TAU_P (float): Thermal time constant of the plant [s]. Default: 10.0
        PLANT_K_P (float): Plant gain (temperature rise per Watt of heater output) [°C/W]. Default: 0.5
        PLANT_TAU_H (float): Heater time constant [s]. Default: 1.0
        PLANT_K_H (float): Heater gain (max heater power per unit command) [W/unit]. Default: 100.0
    """
    # --- Config ---
    endpoint = os.getenv("OPCUA_ENDPOINT", "opc.tcp://0.0.0:4840/freeopcua/server/")
    namespace_uri = os.getenv("OPCUA_NAMESPACE", "http://examples.openfactory.local/opcua")
    UPDATE_INTERVAL = float(os.getenv("UPDATE_INTERVAL", 1.0))
    DT_SIM = 0.1

    # --- Server setup ---
    server = Server()
    await server.init()
    server.set_endpoint(endpoint)
    idx = await server.register_namespace(namespace_uri)
    objects = server.nodes.objects

    # --- Create OPC UA controller tree ---
    ctrl = await create_temperature_controller(server, idx, objects)

    # --- Select plant type from environment and autotune controller ---
    plant_type = os.getenv("PLANT_TYPE", "two_pt1").lower()  # "pt1" or "two_pt1"

    initial_temp = float(os.getenv("PLANT_INITIAL_TEMPERATURE", 22.0))
    ambient = float(os.getenv("AMBIENT_TEMPERATURE", 20.0))

    if plant_type == "two_pt1":
        # Read TwoPT1 plant parameters from environment
        tau_p = float(os.getenv("PLANT_TAU_P", 10.0))
        K_p = float(os.getenv("PLANT_K_P", 0.5))
        tau_h = float(os.getenv("PLANT_TAU_H", 1.0))
        K_h = float(os.getenv("PLANT_K_H", 100.0))

        plant = TwoPT1ThermalPlant(
            initial_temp=initial_temp,
            ambient=ambient,
            tau_p=tau_p,
            K_p=K_p,
            tau_h=tau_h,
            K_h=K_h,
        )

        # Autotune PID for second-order plant
        kp, ki, kd = autotune_pid_from_two_pt1(plant, aggressiveness=1.0)
        await ctrl["deriv_enabled"].write_value(True)

    else:
        # Read PT1 plant parameters from environment
        tau = float(os.getenv("PLANT_TAU", 10.0))
        K = float(os.getenv("PLANT_K", 1.0))

        plant = ThermalPlant(
            initial_temp=initial_temp,
            ambient=ambient,
            tau=tau,
            heater_gain=K,
        )

        # Autotune PI for first-order plant
        kp, ki, kd = autotune_pi_from_plant(plant, aggressiveness=1.0)
        await ctrl["deriv_enabled"].write_value(False)

    await ctrl["prop_enabled"].write_value(True)
    await ctrl["integ_enabled"].write_value(True)
    await ctrl["kp"].write_value(kp)
    await ctrl["ki"].write_value(ki)
    await ctrl["kd"].write_value(kd)

    pid = PIDController(
        setpoint=await ctrl["setpoint"].read_value(),
        kp=await ctrl["kp"].read_value(),
        ki=await ctrl["ki"].read_value(),
        kd=await ctrl["kd"].read_value(),
        prop_enabled=await ctrl["prop_enabled"].read_value(),
        integ_enabled=await ctrl["integ_enabled"].read_value(),
        deriv_enabled=await ctrl["deriv_enabled"].read_value(),
        windup_limit=await ctrl["windup"].read_value(),
        output_min=await ctrl["output_min"].read_value(),
        output_max=await ctrl["output_max"].read_value(),
    )

    control_output = 0.0

    # --- Subscribe to PID parameters ---
    handler = PIDSubscriptionHandler(pid, ctrl)
    subscription = await server.create_subscription(100, handler)

    monitored_nodes = [
        ctrl["setpoint"], ctrl["kp"], ctrl["ki"], ctrl["kd"],
        ctrl["prop_enabled"], ctrl["integ_enabled"], ctrl["deriv_enabled"],
        ctrl["windup"], ctrl["output_min"], ctrl["output_max"]
    ]

    for node in monitored_nodes:
        try:
            await subscription.subscribe_data_change(node)
        except Exception as e:
            logger.warning(f"Cannot subscribe to node {node}: {e}")

    async with server:
        logger.info(f"Server started at {endpoint} with namespace {namespace_uri}")
        next_opcua_update = time.time()

        try:
            while True:
                now = time.time()

                # --- Simulate plant ---
                new_temp = plant.update(control_output, dt=DT_SIM)

                # --- Compute PID  ---
                control_output = pid.compute(measured=new_temp, dt=DT_SIM)

                # --- Update OPC UA every UPDATE_INTERVAL ---
                if now >= next_opcua_update:
                    await ctrl["temp"].write_value(new_temp)
                    await ctrl["output"].write_value(control_output)
                    await ctrl["last_update"].write_value(datetime.datetime.now())

                    if new_temp > pid.setpoint + 5.0:
                        await ctrl["overtemp_alarm"].trigger()
                        logger.info("OverTemperatureAlarm triggered")

                    next_opcua_update = now + UPDATE_INTERVAL

                await asyncio.sleep(DT_SIM)

        finally:
            logger.info("Server stopped")
            await subscription.delete()


if __name__ == "__main__":
    asyncio.run(main())
