# pc2img/__init__.py
__all__ = ["core", "image_processing", "tiled_image_generation", "__version__"]

import logging

from .conf import LOG_FILE, LOG_LEVEL
from . import tiled_image_generation, image_processing
from .version import __version__

__author__ = "Nicholas Meyer"
__email__ = "meyernic@ethz.ch"

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

