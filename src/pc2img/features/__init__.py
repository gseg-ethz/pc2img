__all__ = [
    "FeatureManager",
    # Base (per-point / 1D) features
    "RangeFeature",
    "ScalarFieldFeature",
    # Derivative (per-raster / 2D) features
    "GradientFeature",
    "SobelFeature",
    "NormalizedFeature",
    "LogFeature",
    "HillshadeFeature",
    "AverageFeature",
    "SumFeature",
    "SquareFeature",
    "RootFeature",
    "NormFeature",
    "ClipPercentileFeature",
    "MultiScaleGradientFeature",
    "OcclusionAwareMultiScaleGradientFeature",
    # NOTE: RRIM features (RRIMPackFeature/RRIMFeature/RRIMComponentFeature) are
    # deliberately NOT re-exported here — they are opt-in by design and only
    # register when `pc2img.features.rrim` is imported explicitly.
]

from .base_features import RangeFeature, ScalarFieldFeature
from .derivative_features import (
    AverageFeature,
    ClipPercentileFeature,
    GradientFeature,
    HillshadeFeature,
    LogFeature,
    MultiScaleGradientFeature,
    NormalizedFeature,
    NormFeature,
    OcclusionAwareMultiScaleGradientFeature,
    RootFeature,
    SobelFeature,
    SquareFeature,
    SumFeature,
)
from .manager import FeatureManager
