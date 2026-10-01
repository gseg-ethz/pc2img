"""Spike 001, part A — ORPHANED-OVERRIDE HUNT over every pc2img subclass of GSEGUtils.

For each pc2img class whose MRO contains a GSEGUtils class, classify every name the
pc2img class defines itself against GSEGUtils 0.6.0:

  LIVE      base defines it AND upstream calls it through self./cls./super()
  INERT     base defines it, upstream never calls it (override intercepts nothing)
  ORPHAN    base no longer defines it at all (withdrawn name)
  PC2IMG    pc2img-only name (not an override); reported with its callers

And the reverse direction — DANGLING ``super().X`` calls: pc2img calls ``super().X``
where the base has no ``X``.  Also: signature drift on overridden methods upstream
calls with keywords, and every ``from GSEGUtils... import X`` in src/tests/scripts
resolves on 0.6.0.

Run (scratch venv with GSEGUtils==0.6.0, pchandler==2.1.1; see README):
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/scratch/31_pc2img/src \
      <scratch-venv>/bin/python .planning/spikes/001-orphaned-override-hunt/test_orphan_hunt.py
"""

from __future__ import annotations

import ast
import importlib
import inspect
import pkgutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from provenance import print_provenance  # noqa: E402

print_provenance()

import GSEGUtils  # noqa: E402
import pc2img  # noqa: E402

GSEG_ROOT = Path(GSEGUtils.__file__).parent
REPO = Path("/scratch/31_pc2img")

# ---------------------------------------------------------------- upstream self-call scan
upstream_self_calls: dict[str, list[str]] = {}   # attr -> ["file:line", ...]
upstream_offload_kw: list[str] = []
for py in sorted(GSEG_ROOT.rglob("*.py")):
    tree = ast.parse(py.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            v = node.value
            if isinstance(v, ast.Name) and v.id in ("self", "cls"):
                upstream_self_calls.setdefault(node.attr, []).append(f"{py.name}:{node.lineno}")
            elif (isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "super"):
                upstream_self_calls.setdefault(node.attr, []).append(f"{py.name}:{node.lineno}(super)")
        # Dunder dispatch is invisible to an attribute scan: ``del self[k]`` IS a
        # call to ``self.__delitem__``; ``self[k] = v`` to ``__setitem__``.
        if isinstance(node, ast.Delete):
            for t in node.targets:
                if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and t.value.id == "self":
                    upstream_self_calls.setdefault("__delitem__", []).append(f"{py.name}:{node.lineno}(del self[..])")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            f = node.func
            if f.attr == "offload" and isinstance(f.value, ast.Name) and f.value.id == "self":
                upstream_offload_kw.append(
                    f"{py.name}:{node.lineno} args={len(node.args)} kw={[k.arg for k in node.keywords]}"
                )

# ---------------------------------------------------------------- import all pc2img modules
for m in pkgutil.walk_packages(pc2img.__path__, "pc2img."):
    try:
        importlib.import_module(m.name)
    except Exception as e:  # noqa: BLE001
        print(f"  (import skipped {m.name}: {type(e).__name__}: {e})")

subclasses = []
for modname, mod in sorted(sys.modules.items()):
    if not modname.startswith("pc2img") or mod is None:
        continue
    for _, cls in inspect.getmembers(mod, inspect.isclass):
        if cls.__module__ != modname:
            continue
        gbases = [b for b in cls.__mro__[1:] if b.__module__.startswith("GSEGUtils")]
        if gbases:
            subclasses.append((cls, gbases))

print("=" * 72)
print("pc2img classes with a GSEGUtils base (MRO scan of every pc2img module)")
print("=" * 72)
for cls, gbases in subclasses:
    print(f"  {cls.__module__}.{cls.__qualname__}  <-  {[b.__qualname__ for b in gbases]}")
print()

BOILER = {"__module__", "__qualname__", "__doc__", "__dict__", "__weakref__", "__annotations__",
          "__firstlineno__", "__static_attributes__", "__orig_bases__", "__parameters__",
          "__abstractmethods__", "_abc_impl", "__type_params__", "__slots__"}

# ---------------------------------------------------------------- pc2img-side super() calls
def super_calls_in(cls) -> dict[str, list[tuple[str, int]]]:
    out: dict[str, list[tuple[str, int]]] = {}
    src_file = inspect.getsourcefile(cls)
    tree = ast.parse(Path(src_file).read_text(encoding="utf-8"))
    for cnode in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == cls.__name__]:
        for node in ast.walk(cnode):
            if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name) and node.value.func.id == "super"):
                out.setdefault(node.attr, []).append((Path(src_file).name, node.lineno))
    return out


def self_calls_in(cls) -> dict[str, list[tuple[str, int]]]:
    out: dict[str, list[tuple[str, int]]] = {}
    src_file = inspect.getsourcefile(cls)
    tree = ast.parse(Path(src_file).read_text(encoding="utf-8"))
    for cnode in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == cls.__name__]:
        for node in ast.walk(cnode):
            if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                    and node.value.id in ("self", "cls")):
                out.setdefault(node.attr, []).append((Path(src_file).name, node.lineno))
    return out


hits = []
print("=" * 72)
print("Per-name classification")
print("=" * 72)
for cls, gbases in subclasses:
    sup = super_calls_in(cls)
    selfc = self_calls_in(cls)
    print(f"\n{cls.__qualname__}")
    for name, obj in cls.__dict__.items():
        if name in BOILER:
            continue
        base_has = any(name in b.__dict__ for b in gbases)
        up = upstream_self_calls.get(name, [])
        if base_has and up:
            verdict = "LIVE"
        elif base_has:
            verdict = "INERT (base defines, upstream never self-calls)"
        elif name in ("__init__", "__init_subclass__"):
            verdict = "LIVE"
        else:
            verdict = "PC2IMG-ONLY (no base counterpart)"
            if name in upstream_self_calls:
                verdict = f"LIVE-BY-NAME?? upstream self-calls it: {up[:3]}"
        extra = ""
        if verdict.startswith("PC2IMG-ONLY"):
            callers = selfc.get(name, [])
            extra = f"  [pc2img self-callers in this class: {callers}]"
        print(f"  {name:32s} {verdict}{extra}")
        if not base_has and name in sup:   # pragma: no cover
            pass
    # DANGLING: super().X where X is not defined by any GSEGUtils base
    for attr, locs in sorted(sup.items()):
        if attr == "__init__":
            continue
        defined = any(hasattr(b, attr) for b in gbases)
        tag = "ok (base defines it)" if defined else "!! DANGLING — base has no such attribute"
        print(f"  super().{attr:24s} at {locs}  -> {tag}")
        if not defined:
            hits.append((cls.__qualname__, attr, locs))

# ---------------------------------------------------------------- signature drift
print()
print("=" * 72)
print("Signature drift: overridden methods vs how upstream calls them")
print("=" * 72)
from GSEGUtils.lazy_disk_cache import DiskBackedStore  # noqa: E402
from pc2img.image_cache import DiskBackedImageStore  # noqa: E402

for name in ("offload", "__delitem__", "__init__"):
    ours = inspect.signature(DiskBackedImageStore.__dict__[name]) if name in DiskBackedImageStore.__dict__ else None
    theirs = inspect.signature(getattr(DiskBackedStore, name))
    print(f"  {name}: pc2img={ours}  upstream={theirs}")
print("  upstream self.offload( call sites:")
for l in upstream_offload_kw:
    print(f"    {l}")
print("  -> any call passing keys=... would hit pc2img's `features` parameter name (TypeError)")
drift = [l for l in upstream_offload_kw if "'keys'" in l]
print(f"  keyword 'keys' passed by upstream self.offload: {bool(drift)}")

# ---------------------------------------------------------------- every GSEGUtils import resolves
print()
print("=" * 72)
print("Every `from GSEGUtils... import X` in src/ tests/ scripts/ (excluding scripts/v*) resolves?")
print("=" * 72)
bad = []
seen = set()
for base in ("src", "tests", "scripts", ".planning/spikes"):
    for py in sorted((REPO / base).rglob("*.py")):
        rel = py.relative_to(REPO)
        if str(rel).startswith(("scripts/v1.0", "scripts/v2.0", ".planning/spikes/000")):
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("GSEGUtils"):
                mod = importlib.import_module(n.module)
                for a in n.names:
                    key = (n.module, a.name)
                    ok = hasattr(mod, a.name)
                    if key not in seen:
                        seen.add(key)
                        print(f"  {n.module}.{a.name:28s} {'ok' if ok else '!! MISSING'}   ({rel}:{n.lineno})")
                    if not ok:
                        bad.append((str(rel), n.lineno, n.module, a.name))
print()
print("=" * 72)
print(f"DANGLING super() calls : {hits}")
print(f"MISSING imports        : {bad}")
print("=" * 72)
