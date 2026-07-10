"""Wave 0 hygiene gate for the QUAL-01 sweep (phase 04).

Four checks encode the QUAL-01 *target* state so the downstream FIX work has an
automated target that exists before the work starts (Nyquist Wave 0):

1. ``test_all_submodules_import`` — LIVE now. Import ``pc2img`` plus each submodule
   so the barrel side effects (strategy/feature registration) keep firing. Every
   later hygiene edit (ruff sweep, ``__all__`` sync, metadata cleanup) must keep
   this green.
2. ``test_pyproject_keywords_not_placeholder`` — xfail until 04-02 lands the
   pyproject metadata cleanup (keywords are still the ``["one", "two"]``
   placeholder). Asserts the *shape* (not the placeholder, non-empty), not the
   owner-chosen values, so a legitimate metadata choice does not re-break the test.
3. ``test_pyproject_viz_extra_exists`` — xfail until 04-02 adds the ``viz`` extra.
   Asserts the *key* exists, not its contents.
4. ``test_ruff_check_src_is_clean`` — xfail until 04-04 lands the ruff sweep.
   Shells ``ruff check src/`` and asserts a clean exit.

The xfail markers use ``strict=False`` so Wave 0 collection stays green under
``--strict-markers``; the executor of 04-02/04-04 flips the relevant marker off
once that check xpasses strictly.
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


@pytest.mark.xfail(
    strict=False,
    reason="green after 04-02 pyproject metadata cleanup",
)
def test_pyproject_keywords_not_placeholder() -> None:
    """XFAIL until 04-02: keywords are non-placeholder and non-empty.

    Assert the *shape* (not the ``["one", "two"]`` placeholder, non-empty), not the
    exact owner-chosen values, so a legitimate metadata choice does not fail here.
    """
    keywords = _load_pyproject()["project"].get("keywords", [])
    assert keywords != ["one", "two"], "keywords still the placeholder pair"
    assert keywords, "keywords must be a non-empty list"


@pytest.mark.xfail(
    strict=False,
    reason="green after 04-02 pyproject metadata cleanup",
)
def test_pyproject_viz_extra_exists() -> None:
    """XFAIL until 04-02: a ``project.optional-dependencies.viz`` extra exists.

    Assert the *key*, not its contents, so the owner's extra definition is free.
    """
    optional_deps = _load_pyproject()["project"].get("optional-dependencies", {})
    assert "viz" in optional_deps, "expected a project.optional-dependencies.viz extra"


@pytest.mark.xfail(
    strict=False,
    reason="green after 04-04 ruff sweep",
)
def test_ruff_check_src_is_clean() -> None:
    """XFAIL until 04-04: ``ruff check src/`` exits clean (no lint findings)."""
    ruff = Path(sys.executable).with_name("ruff")
    ruff_cmd = str(ruff) if ruff.exists() else shutil.which("ruff")
    if ruff_cmd is None:
        pytest.skip("ruff not found on PATH or next to the interpreter")

    result = subprocess.run(
        [ruff_cmd, "check", "src/"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"ruff check src/ reported findings:\n{result.stdout}"
    )
