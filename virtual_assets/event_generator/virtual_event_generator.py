import time
import os
import logging
from datetime import datetime
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
    _event_id: int = 0   # counter for unique event IDs

    def read_data(self) -> Dict[str, str]:
        """
        Simulate an event with ID and timestamp.
        Sleeps for a configured interval, then returns an event dictionary.

        Returns:
            dict[str, Any]: Dictionary containing event_id and event_time.
        """
        time.sleep(self.SLEEP_INTERVAL)

        # Increment event counter
        self._event_id += 1

        # Generate timestamp in ISO 8601 UTC format
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Keys must match the DataItem ids in device.xml
        data = {
            "event_id": str(self._event_id),
            "event_time": timestamp
        }

        logger.info(f"Generated event: ID={self._event_id}, Timestamp={timestamp}")
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
