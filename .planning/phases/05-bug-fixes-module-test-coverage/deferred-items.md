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
