# Draft notes for GSEGUtils#82 and pc2img#24

## Baseline

Taken with read-only `gh issue view` calls before any text below was drafted, at 2026-10-02T12:35:49Z (UTC). Output exactly as printed:

| Issue | Command | Printed (state, comment count) |
|-------|---------|--------------------------------|
| GSEGUtils#82 | `gh issue view 82 --repo gseg-ethz/GSEGUtils --json state,comments --jq '[.state, (.comments\|length)]'` | `["OPEN",1]` |
| pc2img#24 | `gh issue view 24 --repo gseg-ethz/pc2img --json state,comments --jq '[.state, (.comments\|length)]'` | `["OPEN",0]` |

The one existing comment on GSEGUtils#82 is the cross-link to pc2img#24 added when the two issues were filed. "Nothing was posted" means: both counts are still 1 and 0 and both issues are still OPEN.

## Status

Draft, nothing posted. Approval and outcome are recorded in the approval record below.

## Note for gseg-ethz/GSEGUtils#82

```
Follow-up from the pc2img side: pc2img no longer triggers this. Its tiled generator used to hand joblib a bound method, so every task carried the whole generator, every tile's store included, and every worker unpickled every store at the same time; that is how it reached the fixed `<key>.dat.tmp` name described here. Each task now carries only its own tile's generator. In the scenario that reproduced it in pc2img (two tiles, two workers, three `generate()` calls on one generator), 12 of 12 rounds failed before and 0 of 12 after; the change will ship in pc2img 0.11.0. The defect itself stands as reported: any program that unpickles one `DiskBackedStore` in several processes at the same time still races on `<key>.dat.tmp`, and the minimal reproduction above is unaffected.
```

## Comment for gseg-ethz/pc2img#24

Two complete variants. They differ only in the last sentence; the owner picks one.

### Variant A

```
Update: the cause was on the pc2img side as much as upstream, and a fix is written.

Cause: `TiledPointCloudImageGenerator.generate()` handed joblib a bound method, so every loky task carried the whole generator, meaning every tile's store and point cloud. Every worker therefore unpickled every tile's store at once, which is what reached the GSEGUtils 0.6.0 race on the fixed `<key>.dat.tmp` name (GSEGUtils#82).

Fix: `generate()` now dispatches a module-level per-tile function that receives only that tile's generator (or none on the first call) and picklable inputs, so a store is unpickled by one process per call. Measured on the scenario from this report (two tiles, `n_jobs=2`, three `generate()` calls on one instance): 12 of 12 rounds failed before, 0 of 12 after. `tests/test_tiled_generator.py::test_tiled_regenerate_on_one_instance_with_two_workers` is now a plain passing test instead of an expected failure. The fix will ship in 0.11.0, so the workaround in the description is no longer needed from that release on.

What remains: with `n_jobs >= 2` each tile's store is built inside a worker and is owned by that worker's process, so `purge`, and overwriting an existing key, called from the parent raises `StorePurgeRefusedError` after the run. Routes: use `n_jobs=1` for an instance you will purge from or overwrite on, use a fresh generator per call, or remove the tile's cache sub-directory. A fix for that is planned after 0.11.0. GSEGUtils#82 stays open for the upstream side.

This issue will be closed when the fix is merged into the development branch.
```

### Variant B

```
Update: the cause was on the pc2img side as much as upstream, and a fix is written.

Cause: `TiledPointCloudImageGenerator.generate()` handed joblib a bound method, so every loky task carried the whole generator, meaning every tile's store and point cloud. Every worker therefore unpickled every tile's store at once, which is what reached the GSEGUtils 0.6.0 race on the fixed `<key>.dat.tmp` name (GSEGUtils#82).

Fix: `generate()` now dispatches a module-level per-tile function that receives only that tile's generator (or none on the first call) and picklable inputs, so a store is unpickled by one process per call. Measured on the scenario from this report (two tiles, `n_jobs=2`, three `generate()` calls on one instance): 12 of 12 rounds failed before, 0 of 12 after. `tests/test_tiled_generator.py::test_tiled_regenerate_on_one_instance_with_two_workers` is now a plain passing test instead of an expected failure. The fix will ship in 0.11.0, so the workaround in the description is no longer needed from that release on.

What remains: with `n_jobs >= 2` each tile's store is built inside a worker and is owned by that worker's process, so `purge`, and overwriting an existing key, called from the parent raises `StorePurgeRefusedError` after the run. Routes: use `n_jobs=1` for an instance you will purge from or overwrite on, use a fresh generator per call, or remove the tile's cache sub-directory. A fix for that is planned after 0.11.0. GSEGUtils#82 stays open for the upstream side.

This issue will be closed when 0.11.0 is on PyPI.
```

## Posting commands (run only after approval, with the approved block extracted verbatim)

Each block is extracted to a scratch file with `awk` over the fence markers, so nothing is retyped. From the repository root:

```bash
F=$(find . -path '*/phases/*' -name '07-ISSUE-NOTES-DRAFT.md' | head -1)
mkdir -p _scrap
awk '/^## Note for gseg-ethz\/GSEGUtils#82/{s=1;next} s&&/^```/{n++; if(n==2) exit; next} s&&n==1' "$F" > _scrap/note-82.md
awk '/^### Variant A/{s=1;next} s&&/^```/{n++; if(n==2) exit; next} s&&n==1' "$F" > _scrap/note-24-A.md
awk '/^### Variant B/{s=1;next} s&&/^```/{n++; if(n==2) exit; next} s&&n==1' "$F" > _scrap/note-24-B.md
```

Then, with the approved variant (A or B) as the second file:

```bash
gh issue comment 82 --repo gseg-ethz/GSEGUtils --body-file _scrap/note-82.md
gh issue comment 24 --repo gseg-ethz/pc2img --body-file _scrap/note-24-A.md
```

## Close action, NOT part of this round

Run only at the close point the owner chose, by the owner or by whatever reaches that point:

```bash
gh issue close 24 --repo gseg-ethz/pc2img --comment "<the owner's closing line>"
```

## Approval record

| Decision | Date | Variant | Comment URLs |
|----------|------|---------|--------------|
| #82 note DROPPED by owner (upstream issue stays about the upstream defect; pc2img status belongs in #24). #24 comment ON HOLD: gap-round-1 review (07-REVIEW-GAP1.md CR-01) found the second pooled generate() returns unreadable rasters, so the drafted 'fix' text is not yet true; redraft after gap round 2 is reviewed. Nothing posted. | 2026-10-02 | — | — |
