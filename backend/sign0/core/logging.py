"""
Production Structured Logging Module for Sign0
Formats logs with timestamp, log level, module, and correlation IDs.
"""

import sys
import logging
from backend.sign0.core.config import settings


def setup_logger(name: str = "sign0") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        log_format = (
            "[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] - %(message)s"
            if settings.DEBUG
            else '{"timestamp":"%(asctime)s", "level":"%(levelname)s", "module":"%(name)s", "message":"%(message)s"}'
        )
        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    return logger


logger = setup_logger()
