from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from pc2img.core import PointCloudImageGenerator
from pc2img.features import registry as registry_module
from pc2img.features import rrim as rrim_module
from pc2img.features.registry import FEATURES

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RRIM_SRC = "src/pc2img/features/rrim.py"

# The default RRIMConfig pack name (base_feature=range, r16, d8, z1) — the exact
# string RRIMFeature.__init__ derives, so match() must schedule the same dep.
_DEFAULT_PACK_NAME = "rrim_pack_(range,r16,d8,z1)"


def test_rrim_module_docstring_is_populated() -> None:
    """BUG-04: the module docstring is the first statement, so __doc__ populates."""
    assert isinstance(rrim_module.__doc__, str)
    assert rrim_module.__doc__.strip()


def test_rrim_module_docstring_clears_e402() -> None:
    """BUG-04 proving test: reordering the header so the docstring leads clears the E402 findings."""
    ruff = Path(sys.executable).with_name("ruff")
    ruff_cmd = str(ruff) if ruff.exists() else shutil.which("ruff")
    if ruff_cmd is None:
        pytest.skip("ruff not found on PATH or next to the interpreter")

    check = subprocess.run(
        [ruff_cmd, "check", "--select", "E402", _RRIM_SRC],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert check.returncode == 0, f"ruff E402 reported findings:\n{check.stdout}"


def test_compute_rrim_flat_plane_returns_neutral_gray() -> None:
    raster = np.zeros((9, 9), dtype=np.float32)
    result = rrim_module.compute_rrim(raster, max_distance=4, num_directions=8)

    assert np.nanmax(np.abs(result.slope)) == 0.0
    assert np.nanmax(np.abs(result.structure)) < 1e-6
    assert np.allclose(result.rgb[4, 4], np.array([0.5, 0.5, 0.5], dtype=np.float32))


def test_compute_rrim_distinguishes_ridge_from_valley() -> None:
    ridge_profile = np.array([0.0, 1.0, 2.5, 1.0, 0.0], dtype=np.float32)
    ridge = np.tile(ridge_profile, (5, 1))
    valley = -ridge

    ridge_result = rrim_module.compute_rrim(ridge, max_distance=3, num_directions=8)
    valley_result = rrim_module.compute_rrim(valley, max_distance=3, num_directions=8)

    assert ridge_result.structure[2, 2] > 0.0
    assert valley_result.structure[2, 2] < 0.0
    assert ridge_result.structure[2, 2] > valley_result.structure[2, 2]


def test_compute_rrim_steeper_surface_increases_red_channel() -> None:
    x = np.arange(21, dtype=np.float32)
    profile = np.where(x < 10, x * 0.2, 2.0 + (x - 10) * 1.0)
    raster = np.tile(profile, (11, 1))

    result = rrim_module.compute_rrim(raster, max_distance=4, num_directions=8)

    assert result.rgb[5, 16, 0] > result.rgb[5, 4, 0]
    assert np.allclose(result.rgb[..., 1], result.rgb[..., 2], equal_nan=True)


def test_compute_rrim_nan_and_edge_handling_do_not_wrap() -> None:
    raster = np.zeros((5, 5), dtype=np.float32)
    raster[:, -1] = 10.0
    raster[2, 2] = np.nan

    result = rrim_module.compute_rrim(raster, max_distance=1, num_directions=4)

    assert np.isnan(result.structure[2, 2])
    assert np.nanmax(np.abs(result.structure[:, 0])) < 1e-6


def test_rrim_feature_registry_outputs_rgb_and_components() -> None:
    features = registry_module.FEATURES
    raster = np.tile(np.linspace(0.0, 2.0, 9, dtype=np.float32), (9, 1))

    rrim_spec = features.match("rrim")
    rrim_feature = rrim_spec.cls(**rrim_spec.params)
    pack_name = next(dep for dep in rrim_feature.dependencies if dep.startswith("rrim_pack_("))

    pack_spec = features.match(pack_name)
    pack_feature = pack_spec.cls(**pack_spec.params)
    pack = pack_feature.compute(None, lambda name: raster)

    rrim_rgb = rrim_feature.compute(None, lambda name: raster if name == "range" else pack)
    assert rrim_rgb.shape == raster.shape + (3,)

    component_spec = features.match("rrim_component_(structure,range,r16,d8)")
    component_feature = component_spec.cls(**component_spec.params)
    structure = component_feature.compute(None, lambda name: pack)

    assert structure.shape == raster.shape
    assert np.allclose(structure, pack[..., 2], equal_nan=True)


# --------------------------------------------------------------------------- #
# G1 (BUG-05, blocker): RRIM dependency resolution via dependencies_for        #
#                                                                              #
# FeatureRegistry.match derives deps via cls.dependencies_for(params) WITHOUT  #
# constructing the class (DSN-05). The three RRIM classes use a regex group    #
# named ``args`` (not ``base_feature``), so without a dependencies_for         #
# override the inherited base returns [] and the base raster is never          #
# scheduled — reproducing "Scalar field 'rrim' not found" end-to-end. These    #
# tests derive deps without construction AND drive the full generate() path.   #
# --------------------------------------------------------------------------- #
def test_rrim_dependencies_for_derives_deps_without_construction() -> None:
    """match() derives each RRIM name's deps via dependencies_for, no __init__."""
    assert FEATURES.match("rrim").dependencies == ["range", _DEFAULT_PACK_NAME]
    assert FEATURES.match("rrim_pack_(range)").dependencies == ["range"]
    # slope component depends on the base feature directly ...
    assert FEATURES.match("rrim_component_(slope,range)").dependencies == ["range"]
    # ... while a non-slope component depends on the pack raster.
    assert FEATURES.match("rrim_component_(structure,range)").dependencies == [_DEFAULT_PACK_NAME]


def test_rrim_dependencies_for_does_not_construct_the_class(monkeypatch) -> None:
    """dependencies_for must read params['args'], never run __init__."""

    def _boom(self, *args, **kwargs):
        raise AssertionError("dependencies_for must not construct the RRIM feature")

    monkeypatch.setattr(rrim_module.RRIMFeature, "__init__", _boom)
    assert rrim_module.RRIMFeature.dependencies_for({"args": None}) == ["range", _DEFAULT_PACK_NAME]


def _rrim_generator(synthetic_pcd) -> PointCloudImageGenerator:
    pcd = synthetic_pcd(n=300)
    return PointCloudImageGenerator(pcd, (16, 16), ("orthographic", {"plane": "xy"}), "nearest_neighbor")


def test_generate_rrim_end_to_end_returns_finite_rgb(synthetic_pcd) -> None:
    gen = _rrim_generator(synthetic_pcd)
    images = gen.generate(["rrim"])
    raster = np.asarray(images["rrim"])
    assert raster.shape == (16, 16, 3)
    assert np.isfinite(raster).all()


def test_generate_rrim_pack_end_to_end_returns_finite_pack(synthetic_pcd) -> None:
    gen = _rrim_generator(synthetic_pcd)
    images = gen.generate(["rrim_pack_(range)"])
    raster = np.asarray(images["rrim_pack_(range)"])
    assert raster.shape == (16, 16, 3)
    assert np.isfinite(raster).all()


def test_generate_rrim_component_slope_end_to_end_returns_finite_raster(synthetic_pcd) -> None:
    gen = _rrim_generator(synthetic_pcd)
    images = gen.generate(["rrim_component_(slope,range)"])
    raster = np.asarray(images["rrim_component_(slope,range)"])
    assert raster.shape == (16, 16)
    assert np.isfinite(raster).all()


# --------------------------------------------------------------------------- #
# G9 (BUG-05, blocker, round 2): the derived pack-feature name must round-trip #
#                                                                              #
# RRIMConfig.pack_feature_name() is BOTH a public feature name and the cache   #
# key. It formatted z_factor with a 6-significant-figure general format, which #
# (a) switches to exponent notation below 1e-4 — a token _Z_FACTOR_RE rejects, #
# so the pack dependency the G1 dependencies_for derives raises ValueError at  #
# request time — and (b) truncates above 6 significant figures, making the     #
# cache key NON-INJECTIVE (two distinct configs collide on one raster).        #
# The fix is both halves: widen the grammar AND emit the shortest exactly      #
# round-tripping form. The existing G1 end-to-end tests above all use default  #
# z, which is exactly why they pass and why this class of defect was invisible.#
# --------------------------------------------------------------------------- #
_ROUND_TRIP_Z_VALUES = [
    1e-06,
    1e-05,
    0.0001,
    0.5,
    1.0,
    1.2345678,
    2.5,
    10.0,
    100.0,
    # review-r1-4939108716dd (WR-05): upper exponent boundary, NAME-level only.
    1e16,
    1e17,
    1.2345678e20,
    1e22,
    4503599627370495.5,
]


@pytest.mark.parametrize("z_factor", _ROUND_TRIP_Z_VALUES)
def test_pack_feature_name_round_trips_z_factor(z_factor: float) -> None:
    """parse(pack_feature_name(cfg)) == cfg over the four fields the pack name carries."""
    cfg = rrim_module.RRIMConfig(base_feature="range", z_factor=z_factor)

    spec = FEATURES.match(cfg.pack_feature_name())
    assert spec.cls is rrim_module.RRIMPackFeature

    parsed = rrim_module._parse_rrim_config(spec.params["args"])
    assert parsed.base_feature == cfg.base_feature
    assert parsed.max_distance == cfg.max_distance
    assert parsed.num_directions == cfg.num_directions
    # exact equality, not approx: the cache key must encode the config losslessly
    assert parsed.z_factor == cfg.z_factor


def test_pack_feature_name_is_injective_for_nearby_z() -> None:
    """Two configs differing beyond 6 significant figures must not share one cache key."""
    a = rrim_module.RRIMConfig(z_factor=1.2345678).pack_feature_name()
    b = rrim_module.RRIMConfig(z_factor=1.2345681).pack_feature_name()
    assert a != b, "distinct z_factor configs collide on one pack name (non-injective cache key)"


def test_upper_boundary_exponent_spellings_canonicalise_to_one_pack_name() -> None:
    """review-r1-4939108716dd (WR-05): round-trip coverage extends to the upper exponent boundary.

    ``_format_number``'s integer branch means every float >= 2**53 (all of
    which are integers) emits a long-digit token, never exponent notation — so
    the upper boundary is exercised on INPUT spelling (the widened grammar
    accepts ``z1e16``) and on the canonical emitted key, not on the
    formatter's own output switching form. This is NAME-level only: the
    float32 raster overflow at such ``z`` is the deferred Phase-6 item
    (``2026-07-27-rrim-float32-scaling-invariant-guard.md``) and is
    deliberately not computed here — no raster is generated with z >= 1e16.
    """
    expected_pack_name = "rrim_pack_(range,r16,d8,z10000000000000000)"
    for spelling in ("rrim_(range,z1e16)", "rrim_(range,z1E+16)", "rrim_(range,z1e+16)"):
        assert FEATURES.match(spelling).dependencies == ["range", expected_pack_name]

    reparsed = rrim_module._parse_rrim_config(FEATURES.match(expected_pack_name).params["args"])
    assert reparsed.z_factor == 1e16

    high_precision_pack_name = rrim_module.RRIMConfig(base_feature="range", z_factor=1.2345678e20).pack_feature_name()
    assert high_precision_pack_name == "rrim_pack_(range,r16,d8,z123456780000000000000)"
    reparsed_high = rrim_module._parse_rrim_config(FEATURES.match(high_precision_pack_name).params["args"])
    assert reparsed_high.z_factor == 1.2345678e20


def test_rrim_dependency_chain_resolves_for_sub_1e4_z() -> None:
    """The full request-time loop: rrim name -> pack dep name -> re-match on that name."""
    assert FEATURES.match("rrim_(range,z1e-05)").dependencies == [
        "range",
        "rrim_pack_(range,r16,d8,z1e-05)",
    ]
    assert FEATURES.match("rrim_pack_(range,r16,d8,z1e-05)").dependencies == ["range"]


def test_generate_rrim_small_z_end_to_end(synthetic_pcd) -> None:
    """A sub-1e-4 z_factor (e.g. a um -> m unit conversion) must survive generate()."""
    gen = _rrim_generator(synthetic_pcd)
    images = gen.generate(["rrim_(range,z1e-05)"])
    raster = np.asarray(images["rrim_(range,z1e-05)"])
    assert raster.shape == (16, 16, 3)
    assert np.isfinite(raster).all()


def test_generate_rrim_z_factor_changes_the_output(synthetic_pcd) -> None:
    """review-r1-a8cd7b4707b0 (WR-04): z_factor must be observably load-bearing end-to-end.

    z reaches the final rasters on two distinct paths, and each needs its own
    pair to be provably load-bearing. The rrim composite's slope channel is
    robust-percentile normalised (`_normalize_robust`), so a linear z scale on
    `compute_slope`'s output cancels there — the rrim pair therefore observes
    z only through the pack's openness-derived structure channel, and the pack
    pair observes z on the openness path (`compute_openness`). Neither pair
    can detect a regression that drops z from `compute_slope` specifically:
    the component-slope pair below is the only surface on which
    `compute_slope`'s own z is directly observable, which is why all three
    pairs are asserted together.
    """
    gen = _rrim_generator(synthetic_pcd)
    images = gen.generate(
        [
            "rrim_(range,z1)",
            "rrim_(range,z4)",
            "rrim_pack_(range,r16,d8,z1)",
            "rrim_pack_(range,r16,d8,z4)",
            "rrim_component_(slope,range,z1)",
            "rrim_component_(slope,range,z4)",
        ]
    )
    rrim_z1 = np.asarray(images["rrim_(range,z1)"])
    rrim_z4 = np.asarray(images["rrim_(range,z4)"])
    pack_z1 = np.asarray(images["rrim_pack_(range,r16,d8,z1)"])
    pack_z4 = np.asarray(images["rrim_pack_(range,r16,d8,z4)"])
    slope_z1 = np.asarray(images["rrim_component_(slope,range,z1)"])
    slope_z4 = np.asarray(images["rrim_component_(slope,range,z4)"])

    for raster in (rrim_z1, rrim_z4, pack_z1, pack_z4, slope_z1, slope_z4):
        assert np.isfinite(raster).all()

    assert not np.array_equal(rrim_z1, rrim_z4), "rrim raster is z_factor-insensitive"
    assert not np.array_equal(pack_z1, pack_z4), "rrim_pack raster is z_factor-insensitive"
    assert not np.array_equal(slope_z1, slope_z4, equal_nan=True), "slope path is z_factor-insensitive"


@pytest.mark.parametrize(
    ("z_factor", "expected"),
    [
        (0.5, "0.5"),
        (2.5, "2.5"),
        (0.0001, "0.0001"),
        (0.001, "0.001"),
        (0.01, "0.01"),
        (0.1, "0.1"),
        (0.25, "0.25"),
        (0.75, "0.75"),
        (1.5, "1.5"),
        (1.0, "1"),
        (2.0, "2"),
        (10.0, "10"),
        (100.0, "100"),
        (1234567.0, "1234567"),
    ],
)
def test_z_factor_token_unchanged_for_currently_valid_values(z_factor: float, expected: str) -> None:
    """Characterization guard (passes BEFORE and AFTER the G9 fix): zero cache-key churn.

    Every z_factor that encodes correctly today must emit a BYTE-IDENTICAL token
    after the formatter change, so no currently-valid cache key is invalidated.
    """
    assert rrim_module._format_number(z_factor) == expected
    assert rrim_module.RRIMConfig(base_feature="range", z_factor=z_factor).pack_feature_name() == (
        f"rrim_pack_(range,r16,d8,z{expected})"
    )


# --------------------------------------------------------------------------- #
# WR-03 — the widened z grammar is a NAME-level precedence change (round 3)    #
#                                                                             #
# Widening `_Z_FACTOR_RE` is additive at the TOKEN level, but `_looks_like_    #
# option_token(tokens[0])` turns that into a NAME-level reinterpretation: a    #
# first token matching the widened grammar is now read as an OPTION rather     #
# than as a base-feature name. Same public name, same cache key, different     #
# computation. Owner decision 2026-07-28: the new precedence is ACCEPTED as    #
# correct — these are kept-behavior characterization tests (they pass on their #
# first run, before any source edit), not a fix. Recorded as BC-NOTES 16.      #
# --------------------------------------------------------------------------- #
def test_exponent_token_takes_precedence_over_base_feature_name() -> None:
    """A first token matching the widened z grammar is read as an option, not a base feature.

    Measured 2026-07-28. PRE-05-14 (pattern `^z([+-]?\\d+(?:\\.\\d+)?)$`, which
    does not match `z1e5`) the SAME name yielded ``base_feature='z1e5'`` and
    ``z_factor=1.0``. That is the BC event this test pins.

    Asserted through `_parse_rrim_config` / `_parse_rrim_component`, never on
    `_Z_FACTOR_RE` directly: the regex is only the mechanism — the consequence
    that matters is at the NAME level.
    """
    cfg = rrim_module._parse_rrim_config("z1e5")
    assert cfg.base_feature == "range", "exponent z token was read as a base-feature name"
    assert cfg.z_factor == 100000.0

    # The widened group is case-insensitive in its exponent marker.
    upper = rrim_module._parse_rrim_config("z1E5")
    assert (upper.base_feature, upper.z_factor) == ("range", 100000.0)

    # The precedence RULE predates the widening — only its EXTENT changed.
    plain = rrim_module._parse_rrim_config("z1")
    assert (plain.base_feature, plain.z_factor) == ("range", 1.0)

    # The component form carries the identical precedence.
    component, comp_cfg = rrim_module._parse_rrim_component("slope,z1e5")
    assert component == "slope"
    assert comp_cfg.base_feature == "range"
    assert comp_cfg.z_factor == 100000.0


def test_z_like_token_that_misses_the_grammar_is_still_a_base_feature_name() -> None:
    """The precedence boundary, and the migration path out of it.

    A near-miss token is still a base-feature name, so the reinterpretation is
    narrowly scoped to tokens that fully match the widened grammar. And a scalar
    field whose bare name would be read as an option remains addressable via the
    `scalar_field_<name>` prefix — which is what makes the BC entry's migration
    note a checked claim rather than a suggestion.
    """
    assert rrim_module._parse_rrim_config("z1e5x").base_feature == "z1e5x"
    assert rrim_module._parse_rrim_config("zx1e5").base_feature == "zx1e5"

    migrated = rrim_module._parse_rrim_config("scalar_field_z1e5")
    assert migrated.base_feature == "scalar_field_z1e5"
    assert migrated.z_factor == 1.0

    # ... and the migration path still composes with trailing option tokens.
    with_options = rrim_module._parse_rrim_config("scalar_field_z1e5,z2")
    assert with_options.base_feature == "scalar_field_z1e5"
    assert with_options.z_factor == 2.0


def test_exponent_token_precedence_is_visible_at_the_registry_surface() -> None:
    """review-r2-d1c47843161c: pin WR-03 precedence at the PUBLIC surface.

    BC-NOTES entry 16 describes the break at the surface a caller actually
    touches: "the same public name, resolving to the same cache key, now
    denotes a different computation". The pins above
    (``test_exponent_token_takes_precedence_over_base_feature_name`` et al.) go
    through the private parser (``_parse_rrim_config`` / ``_parse_rrim_component``),
    which is the *mechanism*, not the surface the BC record is written about —
    ``dependencies_for`` is the exact surface G1 rewrote (DSN-05), and it could
    drift independently of the private-parser pins staying green. This test
    asserts through ``FEATURES.match``, which is what schedules the dependency
    graph and derives the store key.
    """
    pack_spec = FEATURES.match("rrim_pack_(z1e5)")
    assert pack_spec.dependencies == ["range"]
    assert pack_spec.cls is rrim_module.RRIMPackFeature

    rrim_spec = FEATURES.match("rrim_(z1e5)")
    assert rrim_spec.dependencies == ["range", "rrim_pack_(range,r16,d8,z100000)"]
    assert rrim_spec.cls is rrim_module.RRIMFeature
    # Ties the asserted dependency string to the actual derived store key.
    assert rrim_spec.dependencies[1] == rrim_module.RRIMConfig(z_factor=1e5).pack_feature_name()

    component_spec = FEATURES.match("rrim_component_(slope,z1e5)")
    assert component_spec.dependencies == ["range"]
    assert component_spec.cls is rrim_module.RRIMComponentFeature


# --------------------------------------------------------------------------- #
# review-r1-8fb6b87813d1 (IN-02): a clip validation error names its clip       #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("field", "expected"),
    [("slope_clip", "slope_clip"), ("structure_clip", "structure_clip")],
)
def test_clip_validation_error_names_the_failing_clip(field: str, expected: str) -> None:
    cfg = rrim_module.RRIMConfig(**{field: (98.0, 2.0)})
    with pytest.raises(ValueError, match=expected):
        rrim_module._validate_config(cfg)


def test_clip_validation_error_reaches_the_registry_surface() -> None:
    with pytest.raises(ValueError, match="slope_clip"):
        FEATURES.match("rrim_(range,sclip98-2)")
