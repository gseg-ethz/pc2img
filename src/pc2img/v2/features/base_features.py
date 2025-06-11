import re

import numpy as np
from numpy.typing import NDArray

from pchandler.geometry import PointCloudData

from .core import BaseFeatureStrategy

from .registry import FEATURES


@FEATURES.register
class RangeFeature(BaseFeatureStrategy):
    regex_pattern = re.compile(r"^range$")

    def compute(self, pcd, _):
        return pcd.spherical_coordinates[:, 0]


@FEATURES.register(default=True)
class ScalarFieldFeature(BaseFeatureStrategy):
    """
    A BaseFeatureStrategy that pulls any named scalar field off the point cloud.
    Usage: feature name should be "scalar_<field_name>"
    """
    regex_pattern = re.compile(r"^scalar_field_(?P<feature>.+)$")

    def __init__(self, feature: str):
        self.feature = feature

    def compute(self, pcd: PointCloudData, _) -> np.ndarray:
        try:
            return pcd.scalar_fields[self.feature].data
        except KeyError as e:
            raise ValueError(f"Scalar field '{self.feature}' not found on PointCloudData.") from e