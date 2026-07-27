# Deferred Items (Phase 05)

Out-of-scope discoveries logged during execution. Not fixed in the owning plan.

## From 05-10 (tiled_generator)

Pre-existing pyright errors in `src/pc2img/tiled_generator.py` (present at HEAD before
this plan's edits; confirmed by pyright on the pre-edit file — same 6 errors):
- `reportInconsistentOverload` at the `__init__` overload vs impl — intentional
  loose-overload / validated-impl pydantic pattern (params `pcd_tiles`/`img_res`/`proj_cls`
  advertise loose types the impl narrows via `@validate_call`). Same trick as `core.py`'s
  `TYPE_CHECKING` union; overload types just don't line up structurally.
- `reportOptionalSubscript` (×3) in `generate()` — joblib `Parallel()(...)` is typed as
  possibly `None`, so `tile_result[...]` subscripts flag. Runtime always returns a list.
Out of scope for 05-10 (untouched by BUG-03/DSN-10/DSN-07 fixes). Candidate for a typing
cleanup pass if the tiled path is revisited.

## From 05-11 (manager)

Pre-existing pyright errors in `src/pc2img/features/manager.py` (present at HEAD before
this plan's edits; confirmed by pyright on the pre-edit file — same 3 errors, only the
line numbers shifted after the DSN-04/DSN-08 edits):
- `reportArgumentType` at `issubclass(spec.cls, BaseFeatureStrategy)` — `FeatureSpec.cls`
  is typed `type[...] | None` (None until `FeatureRegistry.match` resolves it), so pyright
  flags the possibly-`None` `type` argument.
- `reportOptionalCall` (×2) in `_compute()` / `get_base_features()` — `spec.cls(**...)`
  constructs the same possibly-`None` class attribute; runtime always has it set by `match`.
Out of scope for 05-11 (DSN-04/06/07/08 fixes did not introduce or touch `spec.cls` typing).
Candidate for the same typing cleanup pass — narrowing `FeatureSpec.cls` to non-optional
post-`match` (or an assert/cast at the resolve site) clears all three.

## From 05-14 (round-2 gap closure)

Pre-existing findings on the two files this plan touched, all confirmed to sit outside the
plan's diff hunks (05-14 touched `rrim.py` lines 43–104 and `disk_backed_image_store.py`
lines 70–92 only):

- `pyright src/pc2img/features/rrim.py` — 1 error, `reportReturnType` at
  `_parse_rrim_component` (`return component, _validate_config(config)`): `component` is a
  plain `str` after `.lower()`, not narrowed to the `RRIMComponent` Literal. The membership
  check against the four-name set immediately above it is the runtime guarantee pyright
  cannot see. Fix is a `cast(RRIMComponent, component)` at that return; belongs in the same
  typing cleanup pass as the 05-10 / 05-11 entries.
- `pyright src/pc2img/image_cache/disk_backed_image_store.py` — 1 error,
  `reportArgumentType` on `factory=DiskBackedImageData` in `__init__`: the base store's
  `factory` protocol names its first parameter `data`, while `DiskBackedImageData.__init__`
  names it `image_data`, so the class object is not assignable to the callable type. A
  parameter rename on either side (or a `cast`) clears it — but the pc2img-side rename is a
  public-signature change and would itself be a BC event, so it is deliberately not done here.
- `ruff check src/pc2img/image_cache/disk_backed_image_store.py` — 1 `B008` at
  `config: LazyDiskCacheConfig = LazyDiskCacheConfig()` (`__init__`, line 31). This is one of
  the four B008 findings deferred at 04-04 as a visible breadcrumb (D-02); the repo hygiene
  gate runs `--ignore E402,C901,B008`, so the suite is green with it present. Note the
  05-10 / 05-11 mutable-default sweep replaced this pattern at the *generator/manager*
  construction sites with a `None` sentinel — this store `__init__` is the remaining site.

Two behavioral follow-up candidates, both **verified by running code** during 05-14 and both
deliberately outside its locked scope:

- **`<key>.dat` residue after a successful delete.** The `__delitem__` override purges only
  the `.npy` + `.meta.json` codec pair; `offload_image_data_to_disk` (`pickle_container=True`)
  also writes an entry-level `<key>.dat`, which survives. Verified: after `del s["range"]` the
  cache dir holds `['range.dat']`, and a fresh store over that dir registers **zero** keys —
  the base `__init__` re-scans `*.npy`, so a lone `.dat` is never re-adopted. Disk residue,
  **not** a stale-serve path. Candidate for a follow-up that extends the purge to `.dat`.
- **A non-finite `z_factor` still breaks the RRIM round trip.** `_validate_config` accepts
  `float("inf")` (`inf > 0` is True) and the shortest-round-trip formatter emits `zinf`, which
  the widened `_Z_FACTOR_RE` still rejects. Verified: `RRIMConfig(z_factor=float("inf"))`
  yields `rrim_pack_(range,r16,d8,zinf)` → `ValueError: Unknown RRIM option 'zinf'`. The G9
  owner decision covered exponent notation and precision, **not** finiteness validation, so a
  `math.isfinite` check in `_validate_config` was deliberately not added. Candidate for a
  follow-up: reject non-finite `z_factor` at validation time (fail-fast, one line).
