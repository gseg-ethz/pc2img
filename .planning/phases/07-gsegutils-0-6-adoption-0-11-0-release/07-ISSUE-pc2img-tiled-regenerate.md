# Known limitation: repeated TiledPointCloudImageGenerator.generate() on one instance fails with n_jobs >= 2 on GSEGUtils 0.6.0

## Symptom

Calling `TiledPointCloudImageGenerator.generate()` more than once on the **same instance**, with `n_jobs >= 2` and at least two tiles, fails on the second or a later call on GSEGUtils 0.6.0. The first call succeeds. The failure takes one of two exception families, depending on timing:

- a loky pool error, `BrokenProcessPool` or `TerminatedWorkerError` (both `RuntimeError` subclasses), raised in the parent when a worker dies or cannot unpickle its task ("A task has failed to un-serialize"); or
- the worker's own `FileNotFoundError` (an `OSError`) on `<tile cache>/<key>.dat.tmp`, re-raised by joblib in the parent.

In the reproduction run for this report (two tiles, `n_jobs=2`, three `generate()` calls on one instance, three rounds, run twice) the first family was observed every time: `joblib.externals.loky.process_executor.BrokenProcessPool`, 6 of 6 rounds. The second family was not seen at the pc2img level, but it is what the upstream reproduction shows, so it is expected to occur as well.

The upstream reproduction of the cause (see below) passes on GSEGUtils 0.5.3.

## Affected configuration

- pc2img with GSEGUtils 0.6.0 (the range `pc2img` 0.11 pins)
- a `TiledPointCloudImageGenerator` that is reused for more than one `generate()` call
- `n_jobs >= 2` (the default `n_jobs=-1` counts) and two or more tiles
- caching enabled with a cache directory, as in the reproduction (the disk-backed tile stores are what is raced; other configurations were not measured)

## Not affected

- a fresh `TiledPointCloudImageGenerator` for every `generate()` call (the pattern used by the downstream application); checked with `n_jobs=2` and a shared cache directory, three calls
- `n_jobs=1`; checked with one reused instance, three calls

## Workaround

Either of:

1. Build a fresh `TiledPointCloudImageGenerator` for each `generate()` call.
2. Pass `n_jobs=1` when you need to reuse one instance.

## Cause

Each loky worker unpickles the whole generator, including every tile's disk-backed store, because the tile function is a bound method. On GSEGUtils 0.6.0 unpickling a store rebuilds every entry's `.dat` memmap through one fixed temporary name, `<key>.dat.tmp`, so concurrent workers race on it. This is an upstream defect, reported at https://github.com/gseg-ethz/GSEGUtils/issues/82, and reproduces with GSEGUtils alone (12 of 12 rounds on 0.6.0, 0 of 12 on 0.5.3).

## Regression test

`tests/test_tiled_generator.py::test_tiled_regenerate_on_one_instance_with_two_workers` runs the failing sequence and is marked `xfail(strict=False)` for exactly the two exception families above. It is expected to report XPASS once the upstream fix is released.

## Close condition

Close when the GSEGUtils pin moves to a release that fixes the race and the `xfail` marker is removed from the test above.
