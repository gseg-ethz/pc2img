"""Feature-name DSL + registry-unification sensors (TEST-04, BUG-05 / D-14 / DSN-05).

These tests are *pure* — no ``PointCloudData`` is built. They exercise the
regex/parse surface of the two registries and the new ``dependencies_for``
classmethod directly, so they run fast and share nothing with the heavier
projection/orchestration fixtures in ``conftest.py``.

Test-first (D-12): the unification assertions below are authored *before* the
source change and marked ``xfail`` so this file is committed RED. Task 2 removes
the ``xfail`` markers once the source is unified. The single default-fallback
characterization test is NOT xfail — it pins behavior that already holds today
and MUST keep holding after unification (unknown feature name → default
pseudo-spec, never a raise).
"""

from __future__ import annotations

import re

import pytest

# Importing the features package populates ``FEATURES`` (registration happens as
# an import side effect via the ``@FEATURES.register`` decorators).
import pc2img.features  # noqa: F401
from pc2img.features.core import DerivativeFeatureStrategy
from pc2img.features.registry import FeatureRegistry


# --------------------------------------------------------------------------- #
# Local dummy features (for duplicate / ambiguity scenarios on a fresh reg)    #
# --------------------------------------------------------------------------- #
class _AmbiWide(DerivativeFeatureStrategy):
    regex_pattern = re.compile(r"^ambi_(?P<base_feature>.+)$")

    def __init__(self, base_feature: str) -> None:
        self.base_feature = base_feature
        self.dependencies = [base_feature]

    def compute(self, _, fetch):  # pragma: no cover - never invoked
        return fetch(self.base_feature)


class _AmbiExact(DerivativeFeatureStrategy):
    regex_pattern = re.compile(r"^ambi_x$")

    def __init__(self) -> None:
        self.dependencies = []

    def compute(self, _, fetch):  # pragma: no cover - never invoked
        return fetch("range")


# --------------------------------------------------------------------------- #
# PASSING characterization: default-fallback is preserved (no raise)           #
# --------------------------------------------------------------------------- #
def test_unknown_feature_name_falls_back_to_default_without_raising() -> None:
    """An unregistered feature name resolves to the default pseudo-spec.

    This is the ``ScalarFieldFeature(default=True)`` fallback. It already holds
    today and unification MUST NOT turn it into a raise (correction to the
    FINDINGS framing captured in the plan objective).
    """
    from pc2img.features.base_features import ScalarFieldFeature
    from pc2img.features.registry import FEATURES

    spec = FEATURES.match("totally_unknown_feature")
    assert spec.cls is ScalarFieldFeature
    assert spec.params == {"feature": "totally_unknown_feature"}
    assert spec.dependencies == []


# --------------------------------------------------------------------------- #
# Unified miss-exception type (dual inheritance)                               #
# --------------------------------------------------------------------------- #
def test_unknown_strategy_key_raises_unified_error_caught_as_keyerror() -> None:
    from pc2img.errors import RegistryLookupError
    from pc2img.strategies.registry import PROJECTIONS

    # Dual inheritance keeps every existing ``except KeyError`` caller working.
    assert issubclass(RegistryLookupError, KeyError)

    with pytest.raises(RegistryLookupError):
        PROJECTIONS.get_strategy("no_such_projection")
    with pytest.raises(KeyError):
        PROJECTIONS.get_strategy("no_such_projection")


def test_ambiguous_feature_match_raises_unified_error_caught_as_runtimeerror() -> None:
    from pc2img.errors import RegistryLookupError

    # Dual inheritance keeps every existing ``except RuntimeError`` caller working.
    assert issubclass(RegistryLookupError, RuntimeError)

    reg = FeatureRegistry()
    reg.register(_AmbiWide)
    reg.register(_AmbiExact)

    with pytest.raises(RegistryLookupError):
        reg.match("ambi_x")
    with pytest.raises(RuntimeError):
        reg.match("ambi_x")


def test_duplicate_pattern_registration_raises_unified_error() -> None:
    from pc2img.errors import RegistryLookupError

    reg = FeatureRegistry()
    reg.register(_AmbiWide)
    with pytest.raises(RegistryLookupError):
        reg.register(_AmbiWide)


# --------------------------------------------------------------------------- #
# dependencies_for classmethod — derives deps WITHOUT constructing the class   #
# --------------------------------------------------------------------------- #
def test_dependencies_for_base_feature_single_dep() -> None:
    from pc2img.features.derivative_features import GradientFeature

    params = GradientFeature.regex_pattern.fullmatch("gradient_x_range").groupdict()
    assert GradientFeature.dependencies_for(params) == ["range"]


def test_dependencies_for_average_splits_its_own_group() -> None:
    from pc2img.features.derivative_features import AverageFeature

    params = AverageFeature.regex_pattern.fullmatch("average_(range,scalar_field_x)").groupdict()
    assert AverageFeature.dependencies_for(params) == ["range", "scalar_field_x"]


def test_dependencies_for_sum_splits_its_own_group() -> None:
    from pc2img.features.derivative_features import SumFeature

    params = SumFeature.regex_pattern.fullmatch("sum_(range,scalar_field_x)").groupdict()
    assert SumFeature.dependencies_for(params) == ["range", "scalar_field_x"]


def test_dependencies_for_norm_splits_its_own_group() -> None:
    from pc2img.features.derivative_features import NormFeature

    params = NormFeature.regex_pattern.fullmatch("norm_(range,scalar_field_x)").groupdict()
    assert NormFeature.dependencies_for(params) == ["range", "scalar_field_x"]


def test_dependencies_for_does_not_construct_the_feature(monkeypatch) -> None:
    """``dependencies_for`` must read the groupdict, never run ``__init__``."""
    from pc2img.features.derivative_features import AverageFeature

    def _boom(self, *args, **kwargs):
        raise AssertionError("dependencies_for must not construct the feature class")

    monkeypatch.setattr(AverageFeature, "__init__", _boom)
    assert AverageFeature.dependencies_for({"average_features": "range,range"}) == ["range", "range"]


def test_match_derives_deps_via_dependencies_for_without_construction(monkeypatch) -> None:
    """``FeatureRegistry.match`` must resolve deps without the double-construction."""
    from pc2img.features.derivative_features import AverageFeature
    from pc2img.features.registry import FEATURES

    def _boom(self, *args, **kwargs):
        raise AssertionError("match must not construct the feature class")

    monkeypatch.setattr(AverageFeature, "__init__", _boom)
    spec = FEATURES.match("average_(range,range)")
    assert spec.cls is AverageFeature
    assert spec.dependencies == ["range", "range"]


# --------------------------------------------------------------------------- #
# G5 — one shared default dependency helper (both ABCs delegate, still override)#
# --------------------------------------------------------------------------- #
def test_dependencies_for_stays_overridable_after_unification() -> None:
    """G5: the shared default must not break subclass / family overrides."""
    from pc2img.features.derivative_features import AverageFeature, GradientFeature

    # single-base_feature grammar → the shared default helper
    assert GradientFeature.dependencies_for(
        GradientFeature.regex_pattern.fullmatch("gradient_x_range").groupdict()
    ) == ["range"]
    # split-list family override still wins over the default
    assert AverageFeature.dependencies_for(
        AverageFeature.regex_pattern.fullmatch("average_(range,scalar_field_x)").groupdict()
    ) == ["range", "scalar_field_x"]


@pytest.mark.xfail(reason="Phase 5 (G5): the shared _default_dependencies_for helper does not exist yet", strict=False)
def test_both_feature_abcs_share_one_default_dependency_helper() -> None:
    """G5: both ABCs derive the single-base_feature default via one helper."""
    from pc2img.features import core
    from pc2img.features.core import BaseFeatureStrategy, DerivativeFeatureStrategy

    params = {"base_feature": "range"}
    assert BaseFeatureStrategy.dependencies_for(params) == core._default_dependencies_for(params)
    assert DerivativeFeatureStrategy.dependencies_for(params) == core._default_dependencies_for(params)
    assert BaseFeatureStrategy.dependencies_for({}) == []


# --------------------------------------------------------------------------- #
# G6 — FeatureSpec no longer self-derives dependencies (match is single writer)#
# --------------------------------------------------------------------------- #
@pytest.mark.xfail(reason="Phase 5 (G6): FeatureSpec.__init__ still derives self.dependencies from base_feature", strict=False)
def test_feature_spec_does_not_self_derive_dependencies() -> None:
    from pc2img.features.derivative_features import GradientFeature
    from pc2img.features.registry import FeatureSpec

    spec = FeatureSpec("gradient_x_range", GradientFeature.regex_pattern)
    assert spec.dependencies == []


def test_match_is_single_writer_of_dependencies() -> None:
    """G6 characterization (green before and after): match derives deps via dependencies_for."""
    from pc2img.features.registry import FEATURES

    assert FEATURES.match("gradient_x_range").dependencies == ["range"]


def test_registry_lookup_error_str_is_not_repr_wrapped() -> None:
    # WR-02 (05-REVIEW): RegistryLookupError subclasses KeyError, whose __str__
    # repr-wraps the message (adds quotes). The FeatureRegistry sites used to
    # raise clean RuntimeError text, so str() must render the plain message —
    # no surrounding quotes — to avoid a diagnostics regression.
    from pc2img.errors import RegistryLookupError

    msg = "Unknown feature 'range'"
    assert str(RegistryLookupError(msg)) == msg
    # And a real registry miss surfaces cleanly (no double-quoting).
    from pc2img.strategies.registry import PROJECTIONS

    with pytest.raises(RegistryLookupError) as ei:
        PROJECTIONS.create("definitely_not_a_projection")
    assert '"' not in str(ei.value) and not str(ei.value).startswith("'")
