import logging
import src.config as Config


def setup_logging() -> None:
    """
    Configure application-wide logging.

    This sets the root logger format and level and reduces verbosity of
    noisy third-party libraries.
    """

    logging.basicConfig(
        level=Config.LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    # Reduce noise from libraries
    logging.getLogger("asyncua").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
