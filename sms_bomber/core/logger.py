# sms_bomber/core/logger.py
import logging
from pathlib import Path
from datetime import datetime


def setup_logger(log_dir: Path) -> logging.Logger:
    """Configure application logging."""
    logger = logging.getLogger("sms_bomber")
    logger.setLevel(logging.INFO)

    # File handler
    log_file = log_dir / f"sms_bomber_{datetime.now():%Y%m%d_%H%M%S}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
