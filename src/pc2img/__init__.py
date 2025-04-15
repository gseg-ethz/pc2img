# pc2img/__init__.py
__all__ = ["image_generation", "tiled_image_generation", "__version__",
           "PC2IMGRunSettings","PCDImageLink","ImageData","ImageStack", "decorators"]

import logging

from .core import (
    PC2IMGRunSettings,
    PCDImageLink,
    ImageStack,
    ImageData
)

from . import tiled_image_generation, image_generation, decorators
from ._version import __version__

__author__ = "Nicholas Meyer"
__email__ = "meyernic@ethz.ch"



logger = logging.getLogger(__name__.split(".")[0])

# If root logger has no handlers, configure "library minimum" for root: level: warning -> stderr
if not logging.getLogger().hasHandlers():
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "detailed": {
                "format": "[%(levelname)s|%(module)s|L%(lineno)d] %(asctime)s: %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S%z"
            }
        },
        "handlers": {
            "stderr": {
                "class": "logging.StreamHandler",
                "formatter": "detailed",
                "stream": "ext://sys.stderr"
            }
        },
        "loggers": {
            "root": {
                "level": "WARNING",
                "handlers": [
                    "stderr"
                ]
            }
        }
    }
    logging.config.dictConfig(config)


