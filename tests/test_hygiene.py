"""Hygiene gate for the project-wide lint/metadata sweep.

Five checks encode the sweep's *target* state so the downstream fix work has an
automated target that exists before the work starts:

1. ``test_all_submodules_import`` — LIVE now. Import ``pc2img`` plus each submodule
   so the barrel side effects (strategy/feature registration) keep firing. Every
   later hygiene edit (ruff sweep, ``__all__`` sync, metadata cleanup) must keep
   this green.
2. ``test_pyproject_keywords_not_placeholder`` — LIVE since the pyproject metadata
   cleanup landed. Asserts the *shape* (not the ``["one", "two"]``
   placeholder, non-empty), not the owner-chosen values.
3. ``test_pyproject_viz_extra_exists`` — LIVE since the ``viz`` extra was added.
   Asserts the *key* exists, not its contents.
4. ``test_ruff_check_src_is_clean`` — LIVE since the ruff sweep landed.
   Shells ``ruff check src/`` over the *hygiene-fixable* rule subset (ignoring the
   E402/C901/B008 findings deferred to the bug-fix phase, which stay visible in a
   bare ``ruff check`` as breadcrumbs) and asserts a clean exit, plus that
   ``ruff format --check`` reports no reformatting.
5. ``test_shipped_file_has_no_planning_vocabulary`` — parametrized over every
   git-tracked path outside the internal planning directories. Publication
   hardening requires the shipped tree to carry no internal decision,
   requirement, review-ledger or phase/plan references — comments and
   docstrings should read as plain technical prose, not project-management
   breadcrumbs. One exemption is held in ``_EXEMPTIONS`` below, each with the
   reason stated at the exemption. ``test_public_identifiers_are_not_flagged``
   is a companion self-check proving the word-boundary rules do not clip
   legitimate public identifiers that merely share a hyphenated shape.

All checks are now normal passing tests, except the parametrized gate, which
is red on any shipped file that still carries the vocabulary it scans for.
"""

from __future__ import annotations

import importlib
import re
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
    """LIVE: every pc2img submodule imports cleanly.

    This is the gate the ruff sweep and the barrel/``__all__`` edits must keep green.
    """
    for module_name in _SUBMODULES:
        module = importlib.import_module(module_name)
        assert module is not None, f"{module_name} imported as None"


def test_pyproject_keywords_not_placeholder() -> None:
    """LIVE: keywords are non-placeholder and non-empty.

    Assert the *shape* (not the ``["one", "two"]`` placeholder, non-empty), not the
    exact owner-chosen values, so a legitimate metadata choice does not fail here.
    """
    keywords = _load_pyproject()["project"].get("keywords", [])
    assert keywords != ["one", "two"], "keywords still the placeholder pair"
    assert keywords, "keywords must be a non-empty list"


def test_pyproject_viz_extra_exists() -> None:
    """LIVE: a ``project.optional-dependencies.viz`` extra exists.

    Assert the *key*, not its contents, so the owner's extra definition is free.
    """
    optional_deps = _load_pyproject()["project"].get("optional-dependencies", {})
    assert "viz" in optional_deps, "expected a project.optional-dependencies.viz extra"


# The E402/C901/B008 findings (rrim import ordering, cyclomatic complexity,
# mutable-default seed) are deferred to the bug-fix phase. They stay
# visible in a bare ``ruff check`` as breadcrumbs, so the gate scopes to
# the hygiene-fixable subset by ignoring exactly those three families.
_DEFERRED_RULES = "E402,C901,B008"


def test_ruff_check_src_is_clean() -> None:
    """LIVE: the hygiene-fixable ruff subset is clean and the tree is formatted.

    Shells ``ruff check src/ --ignore E402,C901,B008`` (the deferred
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


# --------------------------------------------------------------------------- #
# Planning-vocabulary gate (public-tree hygiene, whole shipped tree)          #
#                                                                              #
# Every git-tracked path outside the two internal-planning directories is a   #
# candidate for public promotion, so none of them may carry an internal      #
# decision, requirement, review-ledger or phase/plan reference. The scope is  #
# "every tracked path minus the stripped ones", not a fixed directory list,   #
# so a newly-added file is covered automatically without touching this gate. #
# --------------------------------------------------------------------------- #

# Assembled from parts so this file's own source text never contains the
# contiguous literal the gate scans for below -- this module is itself a
# git-tracked, non-exempted target of its own scan, and the raw regex source
# would otherwise always flag its own definition.
_PLANNING_DIR = "." + "planning" + "/"
_STRIPPED_PREFIXES = (_PLANNING_DIR, ".claude/")

# path -> reason. An exempted file passes without being scanned.
_EXEMPTIONS: dict[str, str] = {
    "docs/ip/rrim-eth-signoff.md": (
        "signed ETH IP-clearance record shipped verbatim; editing it would weaken what it attests"
    ),
    ".pre-commit-config.yaml": (
        "the exclude regex must literally name the internal planning directory to scope hook "
        "exclusion out of it; this is a path definition, not a planning-artifact reference, and "
        "the same trick this module uses to avoid self-matching is not available in a static YAML "
        "regex literal"
    ),
}

# Case-sensitive families: internal identifier codes and artifact filenames.
# Each alternative is word-bounded so a public identifier that merely shares a
# hyphenated shape (an ID family letters immediately followed by more letters,
# not digits) is never clipped -- see test_public_identifiers_are_not_flagged.
_CODE_PATTERN = re.compile(
    "|".join(
        [
            r"\b(?:BUG|DSN|QUAL|TEST|DEP|CICD|BC|PERF|BRANCH)-[0-9]+\b",  # requirement/decision code families
            r"\b[MD]-[0-9]{1,3}\b",  # two-letter finding families (M-NN, D-NN)
            r"\bT-[0-9]{2}-[0-9]{2}\b",  # threat ids
            r"\bSC[0-9]\b",  # success-criterion labels
            r"\breview-r[0-9]-[0-9a-f]{6,}\b",  # review-ledger ids
            re.escape(_PLANNING_DIR),  # the internal planning path, literally
            r"\b(?:RESEARCH|CONTEXT|SUMMARY|VERIFICATION|UAT)\.md\b",  # planning artifact names
        ]
    )
)

# Case-insensitive families: phase and plan references. Deliberately NOT a
# bare two-digit-hyphen-two-digit pattern -- that would match ISO dates.
_PHASE_PLAN_PATTERN = re.compile(
    r"\bphase[- ]?[0-9]+(?:\.[0-9]+)?\b"
    r"|\bplans?\s[0-9]{2}-[0-9]{2}\b",
    re.IGNORECASE,
)


def _repo_tracked_paths() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line and not line.startswith(_STRIPPED_PREFIXES)]


def _gate_params() -> list:
    params = []
    for rel_path in _repo_tracked_paths():
        abs_path = _REPO_ROOT / rel_path
        try:
            raw = abs_path.read_bytes()
        except OSError as exc:
            params.append(
                pytest.param(
                    rel_path,
                    marks=pytest.mark.skip(reason=f"could not read {rel_path}: {exc}"),
                    id=rel_path,
                )
            )
            continue
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            params.append(
                pytest.param(
                    rel_path,
                    marks=pytest.mark.skip(reason="binary file, not UTF-8 decodable"),
                    id=rel_path,
                )
            )
            continue
        params.append(pytest.param(rel_path, id=rel_path))
    return params


def _matches(text: str) -> list[str]:
    """Return one ``line: matched text`` entry per hit, in file order."""
    hits: list[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pattern in (_CODE_PATTERN, _PHASE_PLAN_PATTERN):
            for match in pattern.finditer(line):
                hits.append(f"{lineno}: {match.group(0)!r}")
    return hits


@pytest.mark.parametrize("path", _gate_params())
def test_shipped_file_has_no_planning_vocabulary(path: str) -> None:
    """Every shipped file carries no decision, requirement, review-ledger,
    phase or planning-path reference -- exempted files pass unscanned, and a
    red run lists every ``path:line: matched text`` hit as a to-do list."""
    if path in _EXEMPTIONS:
        return
    text = (_REPO_ROOT / path).read_text(encoding="utf-8")
    hits = _matches(text)
    assert not hits, "\n".join(f"{path}:{hit}" for hit in hits)


def test_public_identifiers_are_not_flagged() -> None:
    """Self-check: a public identifier family sharing the internal families'
    hyphenated shape, but with letters (not digits) after the hyphen, must
    never match -- e.g. a downstream migration-record identifier."""
    for identifier in ("BC-P2I-001", "BC-GSEG-006"):
        assert _CODE_PATTERN.search(identifier) is None, f"{identifier} was incorrectly flagged as planning vocabulary"
