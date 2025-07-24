from pc2img.core import PointCloudImageGenerator
from pc2img.strategies.registry import PROJECTIONS, INTERPOLATIONS


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