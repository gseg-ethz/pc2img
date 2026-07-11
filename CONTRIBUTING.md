# Contributing to pc2img

This document covers the **developer bootstrap workflow**. It is intentionally
dev-facing only — user-facing installation and usage documentation lives in
`README.rst`, not here.

pc2img uses [`uv`](https://docs.astral.sh/uv/) for environment management. The
committed `uv.lock` is a universal, hash-pinned lockfile that reproduces the exact
dependency set across platforms. `setuptools_scm` remains the build backend, so the
package version is derived from git tags at build time (keep `.git` present).

## Prerequisites

- Python 3.12 (the project is pinned to `~=3.12,<3.13`).
- `uv` (0.11+). Install from <https://docs.astral.sh/uv/getting-started/installation/>.

## Bootstrap the environment

```bash
uv sync                 # create .venv, install runtime deps + the `dev` group,
                        # and install pc2img itself (editable) so `uv run` can import it
```

`uv sync` with no flags installs the project, its runtime dependencies, **and the
`dev` group** (uv special-cases `dev` as a default group). It reproduces the exact
versions recorded in `uv.lock`.

```bash
uv sync --group doc     # additionally install the `doc` group (sphinx) for building docs
```

Both `dev` (ruff, pytest, memory_profiler) and `doc` (sphinx) are declared as
[PEP 735](https://peps.python.org/pep-0735/) `[dependency-groups]`, so they never
leak into the published wheel metadata and are never installed by
`pip install pc2img`.

## Everyday commands

```bash
uv run python scripts/smoke_pipeline.py   # SC1 smoke: run the single-cloud pipeline end-to-end
uv run pytest                             # run the test suite (tests land in Phase 3)
```

`uv run <cmd>` executes inside the synced environment without needing to activate
`.venv` manually. Because `uv sync` installs pc2img editable, `uv run` resolves
`import pc2img` directly.

> Note: `scripts/smoke_pipeline.py` is created in a later plan of this phase; until
> then, `uv run pytest` has no tests to collect (the pytest framework is stood up in
> Phase 3).

Run `pytest` (or a scoped subset like `pytest tests/test_rrim_features.py`) — never
`pytest .`, which re-collects the gitignored `third_party/` sibling symlinks. Coverage
flags are intentionally **not** in `addopts`, so a bare or subset `pytest` run stays fast
and never trips the coverage gate; opt into coverage explicitly with `--cov=pc2img` when
you want a measurement.

## Coverage baseline

The test suite is measured with branch coverage scoped to the `pc2img` package:

```bash
uv run pytest --cov=pc2img --cov-branch --cov-report=term-missing
```

**Measured baseline: 57%** (whole-package branch coverage, measured 2026-07-11 on the
green suite of **109 passed / 0 xfailed**). This is the Phase-5 baseline: every Phase-5
proving/characterization test now passes (no residual xfail for a finding fixed this phase),
and the previously-unexercised core modules (`projection.py`, `interpolation.py`,
`derivative_features.py`, `manager.py`, `tiled_generator.py`, `util.py`, `rrim.py`) got
behavioral coverage across TEST-03..06. Some large modules (`derivative_features.py`,
`util.py`, `strategies/utils.py`) are still only partially exercised, leaving further ratchet
headroom for future phases.

_Prior Phase-3 baseline (for the ratchet history): 37% on a 15 passed / 11 xfailed
foundation suite, measured 2026-07-09; enforced floor was 35%. (An even earlier draft
recorded 23% because `tests/test_rrim_features.py` loaded `rrim.py` under a throwaway module
name, so its passing tests didn't attribute to the tracked file; the test now imports the
real `pc2img.features.rrim`.)_

**Enforced floor: `--cov-fail-under=55`.** CI (`.github/workflows/ci.yml`) runs the suite
with `--cov-fail-under=55` on the command line — a couple of points below the measured
baseline, keeping the same headroom margin convention Phase 3 established (baseline − ~2pts).
The margin historically absorbed xfail coverage volatility (xfail'd tests execute up to their
failure line, so their coverage contribution could shift); the suite now carries no xfails,
but the margin is retained as ratchet headroom against incidental drift. The gate lives on
the CI command line, not in `pyproject.toml`, so local subset runs never enforce it.

This floor is a **regression ratchet**: it fails CI if coverage drops, without pretending
the suite is comprehensive. It was ratcheted upward in **Phase 5** (35 → 55) as real coverage
landed — the bug-fix proving tests flipped from xfail to pass and the untested core modules
got behavioral coverage. It can be ratcheted further in later phases as more of
`derivative_features.py` / `util.py` gets exercised.

## After changing dependencies

Any edit to `pyproject.toml` dependencies (or the `[tool.uv]` index/source/conflict
tables) must be followed by regenerating and committing the lock:

```bash
uv lock                 # regenerate uv.lock from pyproject.toml
uv lock --check         # verify the committed lock is up to date with pyproject.toml
git add uv.lock pyproject.toml && git commit   # commit the updated lock alongside the change
```

Locking the GPU (`cuda11`/`cuda12`) extras reaches `pypi.nvidia.com` for the RAPIDS
`25.4.*` packages, so run `uv lock` with network access to that index. The two CUDA
variants are declared as mutually exclusive via `[tool.uv] conflicts` (they pull
conflicting `cuda-python` major versions); uv resolves each in a separate fork, so
both stay hash-pinned in the universal lock. Pick the variant that matches your
NVIDIA driver at install time: `pip install pc2img[cuda12]` or `pc2img[cuda11]`.

## Choosing a CUDA variant (`cuda11` vs `cuda12`)

pc2img exposes two GPU extras, `pc2img[cuda11]` and `pc2img[cuda12]` — both pull
`pchandler[cudaXX]`, which in turn drags in the RAPIDS stack
(`cudf`/`cuspatial`/`cuproj`/`cuml`/`dask-cudf`).

- **The pick is driven by your installed NVIDIA driver, not your CUDA toolkit.**
  Run `nvidia-smi` and read the "CUDA Version" in the top-right — that is the
  *maximum* CUDA runtime your driver supports.
  - Driver supports CUDA ≥ 12.0 → install `pc2img[cuda12]` (preferred; RAPIDS 25.4
    is primarily a cu12 line).
  - Older driver capped at CUDA 11.x → install `pc2img[cuda11]`.
- **The two extras are mutually exclusive** — `cudf-cu12` needs
  `cuda-python>=12.6.2,<13` while `cudf-cu11` needs `>=11.8.5,<12`, so a single
  environment cannot satisfy both. Choose exactly one at install time.
- Both require the nvidia index (`--extra-index-url=https://pypi.nvidia.com`).
- For exact driver/runtime minimums, consult the
  [RAPIDS install selector](https://docs.rapids.ai/install/) rather than a version
  table duplicated here.

## Gotchas

- **`gsegutils` vs `GSEGUtils` casing.** The distribution name installed by
  pip/uv is lowercase `gsegutils`; the importable package is capitalized
  `GSEGUtils` (`import GSEGUtils`). pip/uv normalize case for *resolution*, so the
  `pyproject.toml` requirement keeps the capitalized `GSEGUtils` form while
  `importlib.metadata.version("gsegutils")` uses the lowercase distribution name.

- **`third_party/` symlinks are optional dev aids, not the install mechanism.**
  The `third_party/` directory (symlinks to sibling `pchandler`/`GSEGUtils`
  checkouts) is **gitignored** and exists only for local source investigation.
  pc2img resolves `pchandler` and `GSEGUtils` from public PyPI via the committed
  `uv.lock` — never from local editable paths. Do **not** add
  `[tool.uv.sources]` entries pointing at local `/scratch` or `third_party/` paths.
