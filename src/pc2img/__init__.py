# pc2img/__init__.py

import logging

from .conf import LOG_FILE, LOG_LEVEL
from . import tiled_image_generation, image_processing

__author__ = "Nicholas Meyer"
__email__ = "meyernic@ethz.ch"
__version__ = "0.10.0"

# Configure logger for IOF3D
logger = logging.getLogger(__name__)

if not logger.hasHandlers():
    handler = logging.FileHandler(LOG_FILE, mode='a')  # Append mode
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.setLevel(LOG_LEVEL)

    # Console handler
    console_handler = logging.StreamHandler() # Adjust level for console output if needed
    console_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(LOG_LEVEL)

    logger.addHandler(handler)
    logger.addHandler(console_handler)

__all__ = ["core", "image_processing", "tiled_image_generation"]
