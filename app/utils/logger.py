import logging
import sys

_LOG_FORMAT = "[%(asctime)s] %(levelname)s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str = "app") -> logging.Logger:
    logger = logging.getLogger(name)

    logger.propagate = False

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)

        logger.addHandler(stream_handler)

    return logger