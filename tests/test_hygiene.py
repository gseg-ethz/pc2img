"""Wave 0 hygiene gate for the QUAL-01 sweep (phase 04).

Four checks encode the QUAL-01 *target* state so the downstream FIX work has an
automated target that exists before the work starts (Nyquist Wave 0):

1. ``test_all_submodules_import`` — LIVE now. Import ``pc2img`` plus each submodule
   so the barrel side effects (strategy/feature registration) keep firing. Every
   later hygiene edit (ruff sweep, ``__all__`` sync, metadata cleanup) must keep
   this green.
2. ``test_pyproject_keywords_not_placeholder`` — LIVE since 04-02 landed the
   pyproject metadata cleanup. Asserts the *shape* (not the ``["one", "two"]``
   placeholder, non-empty), not the owner-chosen values.
3. ``test_pyproject_viz_extra_exists`` — LIVE since 04-02 added the ``viz`` extra.
   Asserts the *key* exists, not its contents.
4. ``test_ruff_check_src_is_clean`` — LIVE since 04-04 landed the ruff sweep.
   Shells ``ruff check src/`` over the *hygiene-fixable* rule subset (ignoring the
   E402/C901/B008 findings deferred to Phase 5 per D-02, which stay visible in a
   bare ``ruff check`` as breadcrumbs) and asserts a clean exit, plus that
   ``ruff format --check`` reports no reformatting.

All four checks are now normal passing tests.
"""

from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PYPROJECT = _REPO_ROOT / "pyproject.toml"

# The barrels/submodules whose import side effects populate the registries. Importing
# each proves the public surface still resolves after any hygiene edit.
_SUBMODULES = (
    "pc2img",
    "pc2img.registry",
    "pc2img.strategies.projection",
    "pc2img.features",
    "pc2img.util",
    "pc2img.image_cache",
)


def _load_pyproject() -> dict:
    with _PYPROJECT.open("rb") as fh:
        return tomllib.load(fh)


def test_all_submodules_import() -> None:
    """LIVE (Wave 0): every pc2img submodule imports cleanly.

    This is the gate the ruff sweep and the barrel/``__all__`` edits must keep green.
    """
    for module_name in _SUBMODULES:
        module = importlib.import_module(module_name)
        assert module is not None, f"{module_name} imported as None"


def test_pyproject_keywords_not_placeholder() -> None:
    """LIVE (since 04-02): keywords are non-placeholder and non-empty.

    Assert the *shape* (not the ``["one", "two"]`` placeholder, non-empty), not the
    exact owner-chosen values, so a legitimate metadata choice does not fail here.
    """
    keywords = _load_pyproject()["project"].get("keywords", [])
    assert keywords != ["one", "two"], "keywords still the placeholder pair"
    assert keywords, "keywords must be a non-empty list"


def test_pyproject_viz_extra_exists() -> None:
    """LIVE (since 04-02): a ``project.optional-dependencies.viz`` extra exists.

    Assert the *key*, not its contents, so the owner's extra definition is free.
    """
    optional_deps = _load_pyproject()["project"].get("optional-dependencies", {})
    assert "viz" in optional_deps, "expected a project.optional-dependencies.viz extra"


# The E402/C901/B008 findings are deferred to Phase 5 per D-02 (rrim import
# ordering -> BUG-04; cyclomatic complexity; mutable-default seed E). They stay
# visible in a bare ``ruff check`` as Phase-5 breadcrumbs, so the gate scopes to
# the hygiene-fixable subset by ignoring exactly those three families.
_DEFERRED_RULES = "E402,C901,B008"


def test_ruff_check_src_is_clean() -> None:
    """LIVE (since 04-04): the hygiene-fixable ruff subset is clean and the tree is formatted.

    Shells ``ruff check src/ --ignore E402,C901,B008`` (the deferred Phase-5
    families are excluded, not fixed) and ``ruff format --check src/ tests/``.
    """
    ruff = Path(sys.executable).with_name("ruff")
    ruff_cmd = str(ruff) if ruff.exists() else shutil.which("ruff")
    if ruff_cmd is None:
        pytest.skip("ruff not found on PATH or next to the interpreter")

    check = subprocess.run(
        [ruff_cmd, "check", "src/", "--ignore", _DEFERRED_RULES],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert check.returncode == 0, f"ruff check src/ reported findings:\n{check.stdout}"

    fmt = subprocess.run(
        [ruff_cmd, "format", "--check", "src/", "tests/"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert fmt.returncode == 0, f"ruff format --check reported reformatting:\n{fmt.stdout}"
