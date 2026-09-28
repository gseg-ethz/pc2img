---
type: migration-spec
spec_version: "1.0"
repo: pc2img
baseline_ref: "91b4ab6"
target_ref: "e9eb3c48354a73e294c0aff8718fac562215d958"
generated_at: "2026-09-28T14:25:10Z"
bc_id_prefix: BC-P2I
milestone: v1.0
---

# pc2img MIGRATION-v0.11

**Baseline:** `dev/v2` tip (`91b4ab6`, 2025-11-06) — the fork point of `develop-gsd`.
**Target:** `develop-gsd` HEAD (`e9eb3c48354a73e294c0aff8718fac562215d958`) at draft time. Re-stamped
to the `v0.11.0` release tag when this record is finalized.

## Summary

<!-- Filled in Task 2. -->

## Public API stability statement

<!-- Filled in Task 2. -->

## Breaking changes & behavior changes

| BC-ID | category | severity | affected_symbols | origin | migration_steps |
|---|---|---|---|---|---|
| BC-P2I-001 | error-behavior | should-review | `pc2img.errors.RegistryLookupError`, `pc2img.strategies.registry.StrategyRegistry`, `pc2img.features.registry.FeatureRegistry` | `eb62a60` — registry miss/duplicate exception unified | Catch `RegistryLookupError`, or keep catching `KeyError`/`RuntimeError` — both still match. |

## Additive changes

| BC-ID | category | severity | affected_symbols | origin | migration_steps |
|---|---|---|---|---|---|

## Internal & sweep changes

<!-- Filled in Task 2. -->

## Verifier (inline)

The block below is the executor-time verifier for this record. It Tier-1 AST-walks the four
public-surface `__init__.py` barrels and asserts every non-dotted top-level symbol named in a
`BC-P2I-NNN` entry's `affected_symbols` resolves on the public surface (or, for a
`surface-removed` entry, does not). It then Tier-2 runtime-checks the mechanical claims a static
walk cannot see (raised exception types, kwarg presence, on-disk behavior). Exits 0 on success.

```python
r"""Inline executor-time verifier for pc2img MIGRATION-v0.11.md.

Extract this block and run it from the repository root:

    awk '/^## Verifier \(inline\)$/,/^```$/' MIGRATION-v0.11.md \
        | sed -n '/^```python$/,/^```$/p' | sed '1d;$d' \
        > /tmp/pc2img-migration-verifier.py
    uv run --frozen python /tmp/pc2img-migration-verifier.py

Tier 1 AST-walks the four public __init__.py barrels' `__all__` list literals and
asserts every non-dotted top-level symbol named in a BC-P2I entry's
affected_symbols resolves (or, for surface-removed entries, does NOT resolve).
Tier 2 runtime-checks the mechanical claims a static AST walk cannot see
(raised exception types, kwarg presence, on-disk behavior). Exits 0 on
success, 1 on any failure — including an empty BC_ENTRIES list, which is
always a verifier bug, never a vacuous pass.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# The four public-surface __init__.py barrels, relative to the repo root.
PUBLIC_SURFACE_FILES = [
    "src/pc2img/__init__.py",
    "src/pc2img/features/__init__.py",
    "src/pc2img/strategies/__init__.py",
    "src/pc2img/image_cache/__init__.py",
]


def _extract_all(py_text: str) -> set[str]:
    """Return the string literals assigned to a module's ``__all__`` list."""
    tree = ast.parse(py_text)
    declared: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "__all__":
                    value = node.value
                    if isinstance(value, ast.List):
                        for elt in value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                declared.add(elt.value)
    return declared


# BC-P2I entries — keep in sync with the markdown tables above. Only entries
# whose affected_symbols list contains a top-level (non-dotted) name are
# checked at Tier 1; dotted names and mechanical claims are Tier 2's job.
BC_ENTRIES: list[dict[str, object]] = [
    {
        "id": "BC-P2I-001",
        "category": "error-behavior",
        "severity": "should-review",
        "affected_symbols": [
            "pc2img.errors.RegistryLookupError",
            "pc2img.strategies.registry.StrategyRegistry",
            "pc2img.features.registry.FeatureRegistry",
        ],
    },
]


def _find_repo_root() -> Path:
    root = Path.cwd()
    pyproject = root / "pyproject.toml"
    if pyproject.exists() and 'name = "pc2img"' in pyproject.read_text(encoding="utf-8"):
        return root
    raise RuntimeError(
        f"cannot find a pc2img repository root at {root} "
        "(expected ./pyproject.toml naming pc2img) — run this verifier from the repo root"
    )


def _check_ids(failures: list[str]) -> None:
    if not BC_ENTRIES:
        failures.append("BC_ENTRIES is empty — an empty record is a failure, never a vacuous pass")
        return
    seen: list[int] = []
    for entry in BC_ENTRIES:
        entry_id = str(entry["id"])
        prefix, _, digits = entry_id.rpartition("-")
        if prefix != "BC-P2I" or len(digits) != 3 or not digits.isdigit():
            failures.append(f"{entry_id}: id is not of the form BC-P2I-NNN (zero-padded to 3 digits)")
            continue
        seen.append(int(digits))
        if entry.get("category") == "surface-removed" and not entry.get("affected_symbols"):
            failures.append(f"{entry_id}: surface-removed entry names no symbol")
    if seen != sorted(seen) or len(seen) != len(set(seen)):
        failures.append(f"BC-P2I ids are not unique and strictly increasing: {seen}")


def _tier1(root: Path, failures: list[str]) -> None:
    public_surface: set[str] = set()
    for rel in PUBLIC_SURFACE_FILES:
        path = root / rel
        if not path.exists():
            failures.append(f"missing public-surface file: {path}")
            continue
        public_surface |= _extract_all(path.read_text(encoding="utf-8"))

    for entry in BC_ENTRIES:
        entry_id = str(entry["id"])
        affected = entry.get("affected_symbols") or []
        category = entry.get("category")
        for sym in affected:  # type: ignore[union-attr]
            if not isinstance(sym, str) or "." in sym:
                continue  # dotted / non-string symbols are Tier 2's job
            if category == "surface-removed":
                if sym in public_surface:
                    failures.append(
                        f"{entry_id}: documented as surface-removed but {sym!r} is present "
                        "on the public surface"
                    )
            elif sym not in public_surface:
                failures.append(f"{entry_id}: symbol {sym!r} not found on the public surface (Tier 1)")


def _tier2_bc_p2i_001() -> str | None:
    import pc2img.errors as errors_mod

    exc = errors_mod.RegistryLookupError
    if not (issubclass(exc, KeyError) and issubclass(exc, RuntimeError)):
        return "BC-P2I-001: RegistryLookupError does not dual-inherit KeyError and RuntimeError"
    return None


# Tier-2 dict of runtime checks, keyed by BC-P2I id. Extended in a later task
# for every surface-removed / signature-shape entry.
TIER2_CHECKS: dict[str, "object"] = {
    "BC-P2I-001": _tier2_bc_p2i_001,
}


def _tier2(failures: list[str]) -> None:
    known_ids = {str(e["id"]) for e in BC_ENTRIES}
    for check_id, check in TIER2_CHECKS.items():
        if check_id not in known_ids:
            failures.append(f"{check_id}: Tier-2 check exists for an id not present in BC_ENTRIES")
            continue
        result = check()
        if result:
            failures.append(result)


def main() -> int:
    failures: list[str] = []
    _check_ids(failures)
    if failures:
        print("[fail] " + "\n  ".join(failures), file=sys.stderr)
        return 1

    try:
        root = _find_repo_root()
    except RuntimeError as exc:
        print(f"[fail] {exc}", file=sys.stderr)
        return 1

    _tier1(root, failures)
    _tier2(failures)

    if failures:
        print("[fail] migration-spec verification:\n  " + "\n  ".join(failures), file=sys.stderr)
        return 1
    print(f"[ok] verified {len(BC_ENTRIES)} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
