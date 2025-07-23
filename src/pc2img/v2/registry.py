from .core import PointCloudImageGenerator
from .strategies.registry import StrategyRegistry, PROJECTIONS, INTERPOLATIONS
# from .strategies.projection import ProjectionStrategy
# from .strategies.interpolation import InterpolationStrategy
# from .strategies.registry import StrategyRegistry


# Factory for assembling a configured generator

def make_generator(
    pcd,
    proj_name: str,
    proj_cfg: dict,
    interp_name: str,
    interp_cfg: dict
) -> PointCloudImageGenerator:
    proj = PROJECTIONS.create(proj_name, **proj_cfg)
    interp = INTERPOLATIONS.create(interp_name, **interp_cfg)
    return PointCloudImageGenerator(pcd, proj, interp)