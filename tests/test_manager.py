"""TEST-05 sensors for the ``FeatureManager`` orchestration findings (BUG-05).

Covers the four Phase-5 manager/orchestration findings from ``04-FINDINGS.md``:

* **DSN-04** — ``FeatureManager.request()`` never reset ``_base_features``, so a
  reused generator accumulated stale specs across successive requests.
* **DSN-08** — the recursive ``request().visit`` had no visited-set guard, so a
  cyclic feature dependency graph recursed unbounded into a ``RecursionError``
  instead of failing with a clear, catchable error.
* **DSN-07** — the ``lazy_disk_cache_config`` parameter defaulted to a *constructed*
  ``LazyDiskCacheConfig()`` (a shared mutable-default anti-pattern) rather than the
  ``None``-sentinel pattern used at the ``core.py`` / tiled sites.

DSN-06 (omitted-config coercion) is proven by the pre-existing xfail at
``test_point_cloud_image_generator.py::test_constructor_normalizes_omitted_lazy_disk_cache_config``
— that xfail IS the sensor and is flipped in Task 2, so it is not re-authored here.

Per D-12 the genuine-fix sensors are authored xfail first (Task 1) and flipped when
the fix lands (Task 2).
"""

from __future__ import annotations

import inspect
import re
from collections.abc import Callable, Iterator

import pytest
from numpy.typing import NDArray
from pchandler import PointCloudData

from pc2img.features.core import DerivativeFeatureStrategy
from pc2img.features.manager import FeatureManager
from pc2img.features.registry import FEATURES

# Unique throwaway feature name — must not collide with any registered pattern.
_SELF_CYCLE_NAME = "__selfcycle_test__"


@pytest.fixture
def self_cyclic_feature() -> Iterator[str]:
    """Register a self-referential feature, unregistering it on teardown.

    The feature's ``dependencies_for`` returns its own name, so resolving it in
    ``FeatureManager.request()`` re-enters ``visit`` on the same node forever.
    Registration is scoped to the test and removed in ``finally`` so the global
    ``FEATURES`` registry is never polluted for other tests.
    """

    class _SelfCycleFeature(DerivativeFeatureStrategy):
        regex_pattern = re.compile(rf"^{re.escape(_SELF_CYCLE_NAME)}$")

        @classmethod
        def dependencies_for(cls, params: dict[str, str | None]) -> list[str]:
            return [_SELF_CYCLE_NAME]

        def compute(self, pcd: PointCloudData, fetch) -> NDArray:  # pragma: no cover - never reached
            return fetch(_SELF_CYCLE_NAME)

    FEATURES.register(_SelfCycleFeature)
    try:
        yield _SELF_CYCLE_NAME
    finally:
        FEATURES._map.pop(_SelfCycleFeature.regex_pattern, None)


def test_request_twice_does_not_accumulate_base_features(
    synthetic_pcd: Callable[..., PointCloudData],
) -> None:
    """DSN-04: a second ``request()`` reflects only the latest uncached base specs.

    First request pulls two base features (``range`` + ``scalar_field_intensity``);
    the second requests only ``range``. With the reset in place ``_base_features``
    holds exactly one spec after the second call; without it the specs accumulate.
    """
    pcd = synthetic_pcd(n=8, with_scalar_fields={"intensity": None})
    mgr = FeatureManager(pcd)

    mgr.request(["range", "scalar_field_intensity"])
    mgr.request("range")

    assert len(mgr._base_features) == 1


def test_dependency_cycle_raises_valueerror_not_recursionerror(
    synthetic_pcd: Callable[..., PointCloudData],
    self_cyclic_feature: str,
) -> None:
    """DSN-08: a cyclic dependency graph fails with a clear ``ValueError``.

    Without the visited-set guard this recurses unbounded into a ``RecursionError``
    (a ``RuntimeError`` subclass, NOT a ``ValueError``) — so this ``pytest.raises``
    only matches once the guard raises ``ValueError("dependency cycle: ...")``.
    """
    pcd = synthetic_pcd(n=4)
    mgr = FeatureManager(pcd)

    with pytest.raises(ValueError, match="dependency cycle"):
        mgr.request(self_cyclic_feature)


def test_default_config_uses_none_sentinel() -> None:
    """DSN-07: the ``lazy_disk_cache_config`` default is the ``None`` sentinel.

    A constructed ``LazyDiskCacheConfig()`` default is evaluated once at definition
    time and shared across every default-constructed manager. The ``None``-sentinel
    pattern (matching ``core.py`` and the tiled site) coerces a fresh config per
    call instead, so two default-constructed managers never share one instance.
    """
    default = inspect.signature(FeatureManager.__init__).parameters["lazy_disk_cache_config"].default
    assert default is None
