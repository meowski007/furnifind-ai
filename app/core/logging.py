import logging
import sys


def setup_logging(debug: bool = True) -> logging.Logger:
    logger = logging.getLogger("furnifind")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG if debug else logging.INFO)
    return logger


logger = setup_logging()
