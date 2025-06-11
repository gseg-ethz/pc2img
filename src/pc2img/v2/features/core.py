from abc import ABC, abstractmethod
import re
from typing import List, Dict, Any, Optional
import numpy as np
from pchandler.geometry import PointCloudData

class BaseFeatureStrategy(ABC):
    """Produces a 1D array of length N (per point)."""
    dependencies: List[str] = []
    regex_pattern: re.Pattern[str]

    @abstractmethod
    def compute(
        self,
        pcd: PointCloudData,
        fetch: "FeatureManager._get"
    ) -> np.ndarray:
        ...

class DerivativeFeatureStrategy(ABC):
    """
    Produces a 2D raster (H×W).
    Depends on one or more *raster* inputs, each already projected & interpolated.
    """
    dependencies: List[str] = []
    regex_pattern: re.Pattern[str]

    @abstractmethod
    def compute(
        self,
            pcd: PointCloudData,
            fetch: "FeatureManager._get"
    ) -> np.ndarray:
        ...


    @staticmethod
    def _split_top_level(s: str, top_level_bound: tuple[str,str] = ("(", ")"), sep: str = ',') -> list[str]:
        """
        Split s on `sep` only when we're *not* inside parentheses.
        """
        parts = []
        buf: list[str] = []
        depth = 0
        left_bound = top_level_bound[0]
        right_bound = top_level_bound[1]

        for ch in s:
            if ch == left_bound:
                depth += 1
                buf.append(ch)
            elif ch == right_bound:
                depth -= 1
                buf.append(ch)
            elif ch == sep and depth == 0:
                parts.append(''.join(buf).strip())
                buf = []
            else:
                buf.append(ch)

        parts.append(''.join(buf).strip())
        return parts


