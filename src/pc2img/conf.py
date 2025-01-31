from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime


# Define log directory
LOG_DIR = Path.home() / r".log/PC2Image"
LOG_DIR.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

# Define log file with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"main_{timestamp}.log"

LOG_LEVEL = 10  # DEBUG


@dataclass(init=False)
class PathsConf:
    results_folder: Path
    point_cloud_1_file: Path
    point_cloud_2_file: Path

    def __init__(self, results_folder: str, point_cloud_1_file: str, point_cloud_2_file: str):
        object.__setattr__(self, "results_folder", Path(results_folder).absolute())
        object.__setattr__(self, "point_cloud_1_file", Path(point_cloud_1_file).absolute())
        object.__setattr__(self, "point_cloud_2_file", Path(point_cloud_2_file).absolute())


@dataclass
class GenerationParametersConf:
    image_resolution_width: int
    image_resolution_height: int
    angular_resolution_gon: float


@dataclass
class RunParametersConf:
    nb_jobs: int


@dataclass
class PC2IMGConf:
    generation_parameters: GenerationParametersConf
    paths: PathsConf
    run_parameters: RunParametersConf

