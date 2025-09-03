import time
import os
import logging
from datetime import datetime, timezone
from typing import Dict
from mtcadapter.mtcdevices import MTCDevice
from mtcadapter.adapters import MTCAdapter

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


class VirtualEventGenerator(MTCDevice):
    """
    A virtual event generator device for development/testing purposes.
    Simulates periodic events with sequential IDs and timestamps.
    """

    SLEEP_INTERVAL: float = float(os.environ.get("SLEEP_INTERVAL", 3.0))

    def read_data(self) -> Dict[str, str]:
        """
        Simulate an event with a timestamp.
        Sleeps for a configured interval, then returns an event dictionary.

        Returns:
            dict[str, Any]: Dictionary containing event_time and timestamp.
        """
        time.sleep(self.SLEEP_INTERVAL)

        # Generate timestamp in ISO 8601 UTC format
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Keys must match the DataItem ids in device.xml
        data = {
            "event_time": timestamp
        }

        logger.info(f"Generated event: Timestamp={timestamp}")
        return data


class VirtualEventGeneratorAdapter(MTCAdapter):
    """ Adapter class for the VirtualEventGenerator. """
    device_class = VirtualEventGenerator
    adapter_port: int = int(os.environ.get("ADAPTER_PORT", 7878))  # default port 7878


def main() -> None:
    """ Entry point to start the virtual event generator adapter. """
    logger.info("Starting VirtualEventGeneratorAdapter...")
    adapter = VirtualEventGeneratorAdapter()
    adapter.run()


if __name__ == "__main__":
    main()
