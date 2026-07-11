import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import numpy as np
from pchandler import PointCloudData

if TYPE_CHECKING:
    from .manager import FeatureManager


def _default_dependencies_for(params: dict[str, str | None]) -> list[str]:
    """Derive raster dependencies from a parsed regex ``groupdict`` (G5).

    The single source of the default single-``base_feature`` dependency grammar,
    shared by both feature ABCs so the rule is defined in exactly one place. It
    returns ``[base_feature]`` when the parsed ``groupdict`` carries a
    ``base_feature`` group, else ``[]``.

    DSN-05: this lets ``FeatureRegistry.match`` resolve dependencies WITHOUT
    constructing the feature class (which previously ran ``__init__`` twice — once
    in ``match`` and again at compute time). Families whose ``__init__`` derives
    dependencies differently (e.g. the split-list ``average``/``sum``/``norm``
    features, ``hillshade``'s defaulted base, or the RRIM family) OVERRIDE
    ``dependencies_for`` to mirror their own derivation so ``match`` and
    construction always agree.
    """
    base_feature = params.get("base_feature")
    return [base_feature] if base_feature is not None else []


class BaseFeatureStrategy(ABC):
    """Produces a 1D array of length N (per point)."""

    dependencies: list[str] = []
    regex_pattern: re.Pattern[str]

    @classmethod
    def dependencies_for(cls, params: dict[str, str | None]) -> list[str]:
        """Default single-``base_feature`` derivation via :func:`_default_dependencies_for`.

        Overridable: subclasses whose grammar differs mirror their own
        ``__init__`` derivation here (see :func:`_default_dependencies_for`).
        """
        return _default_dependencies_for(params)

    @abstractmethod
    def compute(self, pcd: PointCloudData, fetch: "FeatureManager._get") -> np.ndarray: ...


class DerivativeFeatureStrategy(ABC):
    """
    Produces a 2D raster (H×W).
    Depends on one or more *raster* inputs, each already projected & interpolated.
    """

    dependencies: list[str] = []
    regex_pattern: re.Pattern[str]

    @classmethod
    def dependencies_for(cls, params: dict[str, str | None]) -> list[str]:
        """Default single-``base_feature`` derivation via :func:`_default_dependencies_for`.

        See :meth:`BaseFeatureStrategy.dependencies_for`. Split-list and
        defaulted-base families (and the RRIM family) override this.
        """
        return _default_dependencies_for(params)

    @abstractmethod
    def compute(self, pcd: PointCloudData, fetch: "FeatureManager._get") -> np.ndarray: ...

    @staticmethod
    def _split_top_level(s: str, top_level_bound: tuple[str, str] = ("(", ")"), sep: str = ",") -> list[str]:
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
                parts.append("".join(buf).strip())
                buf = []
            else:
                buf.append(ch)

        parts.append("".join(buf).strip())
        return parts
