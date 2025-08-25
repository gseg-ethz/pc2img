import re
from typing import Optional, Callable

import numpy as np
from numpy.typing import NDArray
from scipy.ndimage import sobel

from .core import DerivativeFeatureStrategy
from .registry import FEATURES

@FEATURES.register
class GradientFeature(DerivativeFeatureStrategy):
    """
    Computes the gradient of a base feature image along x or y.
    Dependencies: the base feature (will be treated as grid-level).
    """

    regex_pattern = re.compile(
        r"^gradient_(?P<axis>[xy])_(?P<base_feature>.+)$"
        )

    def __init__(self, base_feature: str, axis: str) -> None:
        self.base_feature = base_feature
        self.axis = axis
        self.dependencies = [base_feature]

    def compute(self,_, fetch: Callable[[str], NDArray]) -> NDArray:
        img = fetch(self.base_feature)
        ax = 1 if self.axis == 'x' else 0
        grad = np.gradient(img, 100, axis=ax)
        return grad
    
@FEATURES.register
class SobelFeature(DerivativeFeatureStrategy):
    """
    Computes the Sobel filter of a base feature image along x or y.
    Dependencies: the base feature (will be treated as grid-level).
    """

    regex_pattern = re.compile(
        r"^sobel_(?P<axis>[xy])_(?P<base_feature>.+)$"
        )

    def __init__(self, base_feature: str, axis: str) -> None:
        self.base_feature = base_feature
        self.axis = axis
        self.dependencies = [base_feature]

    def compute(self,_, fetch: Callable[[str], NDArray]) -> NDArray:

        img = fetch(self.base_feature)
        ax = 1 if self.axis == 'x' else 0
        sobel_img = sobel(img, axis=ax, mode="constant", cval=np.nan)
        return sobel_img

@FEATURES.register
class NormalizedFeature(DerivativeFeatureStrategy):
    regex_pattern = re.compile(
        r"^normalized_(?P<base_feature>.+?)"r"(?:_(?P<low>\d+(?:\.\d+)?)_(?P<high>\d+(?:\.\d+)?))?$"
        )

    def __init__(self, base_feature: str, low: Optional[str] = None, high: Optional[str] = None) -> None:
        if low is None:
            low = "0"
        if high is None:
            high = "100"

        # low = float(low)

        # if not(0 <= float(low) < float(high) <= 100):
        #     raise ValueError(f"low={low} and high={high} must be between 0 and 100 and low must be smalller than high")

        self.base_feature = base_feature
        self.dependencies = [base_feature]
        self.low = float(low)
        self.high = float(high)

    def compute(self,_, fetch: Callable[[str], NDArray]) -> NDArray:
        img = fetch(self.base_feature)
        low_bound, high_bound = np.nanpercentile(img, [self.low, self.high])

        if high_bound - low_bound != 0:
            np.divide(img - low_bound, high_bound - low_bound, out=img)
        np.clip(img, 0, 1.0, out=img)
        return img

@FEATURES.register
class LogFeature(DerivativeFeatureStrategy):
    regex_pattern = re.compile(
        r"^log_(?P<base_feature>.+?)$"
        )

    def __init__(self, base_feature: str) -> None:

        self.base_feature = base_feature
        self.dependencies = [base_feature]


    def compute(self,_, fetch: Callable[[str], NDArray]) -> NDArray:
        img = fetch(self.base_feature)
        return np.log10(img)


@FEATURES.register
class HillshadeFeature(DerivativeFeatureStrategy):

    regex_pattern = re.compile(
        r"^hillshade"
        r"(?:_(?P<base_feature>.+?))?"
        r"(?:_(?P<azimuth>\d+(?:\.\d+)?))?"
        r"(?:_(?P<altitude>\d+(?:\.\d+)?))?"
        r"(?:_(?P<z_factor>\d+(?:\.\d+)?))?"
        r"$")

    def __init__(self, base_feature: Optional[str] = None, azimuth: Optional[str] = None,
                 altitude: Optional[str] = None, z_factor: Optional[str] = None) -> None:
        if base_feature is None:
            base_feature = "range"
        if azimuth is None:
            azimuth: float = 315.0
        if altitude is None:
            altitude: float = 45.0
        if z_factor is None:
            z_factor: float = 1.0

        self.base_feature = base_feature
        self.azimuth = float(azimuth)
        self.altitude = float(altitude)
        self.z_factor = float(z_factor)
        self.dependencies = [base_feature]

    def compute(self, _,fetch) -> NDArray:
        values = fetch(self.base_feature)

        x, y = np.gradient(values * self.z_factor)
        slope = np.pi / 2.0 - np.arctan(np.sqrt(x * x + y * y))
        aspect = np.arctan2(-x, y)
        azimuth_rad = self.azimuth * np.pi / 180.0
        altitude_rad = self.altitude * np.pi / 180.0

        shaded = np.sin(altitude_rad) * np.sin(slope) + np.cos(altitude_rad) * np.cos(slope) * np.cos(
            azimuth_rad - aspect)

        return shaded


@FEATURES.register
class AverageFeature(DerivativeFeatureStrategy):
    regex_pattern = re.compile(r"^average_[(](?P<average_features>[^,]+(?:,[^,]+)+)[)]$")

    def __init__(self, average_features: str) -> None:
        # self.average_features = average_features.split(',')
        self.average_features = type(self)._split_top_level(average_features)
        self.dependencies = self.average_features

    def compute(self,_,fetch: Callable[[str], NDArray]) -> NDArray:
        values: list[NDArray] = [fetch(v) for v in self.average_features]
        need_3dim = any(v.ndim == 3 for v in values)

        if need_3dim:
            new_values = []
            for v in values:
                new_values.append(v if v.ndim == 3 else np.repeat(v[:,:,np.newaxis], 3, axis=-1))
            values = new_values

        stacked = np.stack(values, axis=-1)
        return np.average(stacked, axis=-1)


@FEATURES.register
class SumFeature(DerivativeFeatureStrategy):
    regex_pattern = re.compile(r"^sum_[(](?P<sum_features>[^,]+(?:,[^,]+)+)[)]$")

    def __init__(self, sum_features: str) -> None:
        # self.sum_features = sum_features.split(',')
        self.sum_features = type(self)._split_top_level(sum_features)
        self.dependencies = self.sum_features

    def compute(self,_,fetch: Callable[[str], NDArray]) -> NDArray:
        values: list[NDArray] = [fetch(v) for v in self.sum_features]
        need_3dim = any(v.ndim == 3 for v in values)

        if need_3dim:
            new_values = []
            for v in values:
                new_values.append(v if v.ndim == 3 else np.repeat(v[:,:,np.newaxis], 3, axis=-1))
            values = new_values

        stacked = np.stack(values, axis=-1)
        return np.sum(stacked, axis=-1)

@FEATURES.register
class SquareFeature(DerivativeFeatureStrategy):
    regex_pattern = re.compile(r"^square_(?P<base_feature>.+?)$")

    def __init__(self, base_feature: str) -> None:
        self.base_feature = base_feature
        self.dependencies = [base_feature]

    def compute(self,_,fetch: Callable[[str], NDArray]) -> NDArray:
        img = fetch(self.base_feature)
        return np.square(img)
    
@FEATURES.register
class RootFeature(DerivativeFeatureStrategy):
    regex_pattern = re.compile(r"^sqrt_(?P<base_feature>.+?)$")

    def __init__(self, base_feature: str) -> None:
        self.base_feature = base_feature
        self.dependencies = [base_feature]

    def compute(self,_,fetch: Callable[[str], NDArray]) -> NDArray:
        img = fetch(self.base_feature)
        return np.sqrt(img)
