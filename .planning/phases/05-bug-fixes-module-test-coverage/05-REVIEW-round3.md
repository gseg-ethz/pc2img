---
phase: 05-bug-fixes-module-test-coverage
reviewed: 2026-07-28T14:20:00Z
depth: deep
review_round: 3
diff_base: 95fe38c
files_reviewed: 4
files_reviewed_list:
  - src/pc2img/features/rrim.py
  - src/pc2img/image_cache/disk_backed_image_store.py
  - tests/test_image_store.py
  - tests/test_rrim_features.py
findings:
  critical: 1
  warning: 5
  info: 5
  total: 11
status: issues_found
---

# Phase 05: Code Review Report (round 3)

**Reviewed:** 2026-07-28T14:20:00Z
**Depth:** deep
**Diff:** `95fe38c..HEAD` (commits `03eb715`, `b9b6a2e`)
**Files Reviewed:** 4
**Status:** issues_found

## Summary

The round-3 gap closure does two things: it adds a path-containment authority to
`DiskBackedImageStore` (WR-02) and it corrects the RRIM `_Z_FACTOR_RE` comment plus the
`RRIMConfig` name-grammar docstring (WR-03), each with new tests. The containment guard
itself is **real and load-bearing** — I removed it in a scratch copy and the four new
proving tests went RED, and I reproduced the escape end-to-end through the public
`generate([...])` API. The RRIM half is prose-only and its claims check out.

Every finding below was **reproduced by running code**, per the project's standing rule.
Baseline suite on HEAD: `175 passed`. Ruff on the four files reports only the known,
deferred `B008` (IN-03 in `05-UAT.md`). No source file was modified by this review.

Three themes:

1. **One blocker introduced by the diff.** The containment refusal fires *after*
   `super().__delitem__(key)` has already removed the key from the in-memory store, so a
   refused delete is a partially-applied delete. This is the exact shape of the G10 defect
   that round 2 classified blocker — re-introduced on the new `ValueError` branch — and the
   new proving test is blind to it because it never asserts store state.
2. **The containment predicate over-resolves.** `path.resolve()` follows symlinks in the
   final component, so an existing cache entry that is a symlink is now refused on the
   *read* path with `ValueError` (not `KeyError`), wedging the key and breaking
   `pickle.loads` of the store — i.e. the joblib/loky tiled path.
3. **The threat-posture documentation is factually wrong, in the direction that invites the
   guard's removal.** "No store key can begin with `..` or `/`" and "not a live exploit path
   from untrusted point-cloud metadata" are both disproven by running the public API. The
   same text is duplicated into `05-BC-NOTES.md` entry 15 and `05-UAT.md`
   `review-r1-a239bdbfc017`, both of which are marked *carry into Phase 6 BC-01*.

Findings already dispositioned in earlier rounds (WR-04, WR-05, WR-06, IN-01, IN-02, IN-03
in `05-UAT.md`, and the deferred RRIM float32 scaling guard) are **not** re-reported.

_No `<structural_findings>` block was supplied for this review, so there is no structural
substrate section; everything below is narrative._

## Narrative Findings (AI reviewer)

### Critical Issues

#### CR-01: A refused delete is a *partially applied* delete — the in-memory entry is dropped while the caller is told the operation failed

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:126-158` (interaction with `:90-96`)
**Severity:** BLOCKER (data loss / inconsistent state, introduced by `03eb715`)

`__delitem__` was deliberately left byte-identical, so its first statement is
`super().__delitem__(key)` — whose entire body is `del self._store[key]`. The containment
guard now rides inside `_get_npy_path`, which is the **second** statement. For a key whose
path escapes, the mutation has already committed when the `ValueError` is raised:

```
tracked before: True len: 1
ValueError raised: Refusing raster key path '/tmp/.../cache/../victim.npy': it resolves to
tracked AFTER failed delete: False len: 0
store keys: []
sentinel intact: b'SENTINEL'
```

(reproduced 2026-07-28 with `store["../victim"] = DiskBackedImageData(arr)` — the same
`__setitem__` route the new proving test uses, and the route the plan's own `key_links`
identifies as the one that makes the unlink reachable.)

If the entry was never offloaded, the store held the only reference and it is gone. A caller
that catches the `ValueError` — the natural response to a refusal — has silently lost the
raster. Round 2 classified exactly this property as blocker-grade for the `KeyError` branch
("Ordering matters here — the reverse order made a `KeyError` delete irreversibly
destructive", `:133-134`); the new `ValueError` branch re-opens it in the in-memory
dimension.

The same partial delete is reachable on two further routes, both measured:

* `add_image_to_store(key, arr)` on an already-tracked escaping key — it routes through
  `del self[img_name]` (`:116-117`), so the overwrite drops the old entry and then never
  inserts the new one.
* An **adopted, symlinked** cache entry (see WR-01), where the key is an ordinary
  feature name: `del store["range"]` raised `ValueError` **and** left `store.keys() == []`.

The new test `test_escaping_key_delete_refuses_and_leaves_outside_file_intact`
(`tests/test_image_store.py:250-276`) asserts the exception and the outside file, but never
asserts that the store still tracks the key — so the suite cannot see this.

**Fix** — build (and therefore validate) both paths *before* the base delete. This keeps the
05-14 ordering property intact (`super()` is still the single membership authority, and the
`KeyError` path is still a disk no-op), and adds the missing property that a refused delete
is a full no-op:

```python
def __delitem__(self, key: str) -> None:
    # Containment is validated BEFORE any mutation: a refused delete must be a
    # no-op in memory as well as on disk (the KeyError path already is).
    npy_path = self._get_npy_path(key)   # may raise ValueError - nothing mutated yet
    meta_path = self._get_meta_path(key)
    super().__delitem__(key)             # may raise KeyError - still no disk effect
    npy_path.unlink(missing_ok=True)
    meta_path.unlink(missing_ok=True)
```

Verified compatible with the existing sensors: `test_failed_delete_preserves_codec_pair_and_both_stores`
(contained path → no raise from the builders → `KeyError` from `super()` → no unlink) and
`test_adopted_key_delete_purges_shared_pair` both still hold.

**Also add the missing assertion** to the proving test so this cannot regress:

```python
    with pytest.raises(ValueError):
        del store[key]

    assert key in store, "a refused delete must not drop the in-memory entry"
    assert sentinel.exists(), "escaping delete removed a file outside the cache directory"
```

> Note on scope: `05-15-PLAN.md` `<scope_boundaries>` forbids editing `__delitem__`. That
> constraint is what produced this defect — it forced the guard into a position where it can
> only fire after the mutation. The constraint should be lifted for this fix.

### Warnings

#### WR-01: The containment predicate resolves symlinks in the final component, so an existing symlinked cache entry is newly refused — the key wedges and store unpickling breaks

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:81-88`
**Severity:** WARNING (behavioral regression on the read path, introduced by `03eb715`)

`_assert_within_cache_dir` compares `path.resolve()` against `self._cache_dir.resolve()`.
`Path.resolve()` follows symlinks including the last component, so a `<key>.npy` that is a
symlink to a file outside the cache directory now resolves outside and is refused — even
though the *key* is an ordinary feature name and the path the store built is genuinely
inside its own directory.

Measured 2026-07-28 (cache dir containing `range.npy` → `../shared/range.npy` symlinks;
`DiskBackedStore.__init__`'s `*.npy` glob uses `f.is_file()`, which follows symlinks, so the
key **is** adopted):

```
  adopted: True
  get:       ValueError: Refusing raster key path '.../cache/range.npy': it resolves to ...
  delete:    ValueError: ...            (and the key is dropped from _store — see CR-01)
  overwrite: ValueError: ...
  still tracked: False   []
  unpickle:  ValueError: Refusing raster key path '.../cache/range.npy' ...
```

Two consequences beyond the refusal itself:

* **Wrong exception class on the read path.** `DiskBackedStore.__getitem__` documents
  `KeyError` for "no usable on-disk pair"; the store's own class docstring promises that an
  unusable cache file "degrades to a cache miss". A `ValueError` defeats every
  `except KeyError: recompute` caller and turns a cache problem into a hard failure.
* **The tiled/loky path breaks.** `DiskBackedStore.__setstate__` (`disk_backed_store.py:541-547`)
  catches only `KeyError` around `_load_entry`; the `ValueError` escapes and unpickling the
  whole store fails inside the worker. `pickle.loads(pickle.dumps(store))` raised in the run
  above. (A plain store with no symlinks pickles and round-trips fine — verified.)

Symlinking large rasters into a scratch cache directory is an ordinary scientific-computing
layout, and nothing in the docstring states that symlinks are now refused.

**Fix** — check containment lexically, resolving only as far as the directory, so `..`
segments are still collapsed but a legitimate final-component symlink is not chased:

```python
import os

def _assert_within_cache_dir(self, path: Path) -> Path:
    cache_dir = self._cache_dir.resolve()
    candidate = Path(os.path.normpath(path if path.is_absolute() else cache_dir / path))
    if not candidate.is_relative_to(cache_dir):
        raise ValueError(...)
    return path
```

If refusing symlinked entries is *intended* hardening, then say so in the docstring and in
`05-BC-NOTES.md` entry 15, translate the read-path refusal into a `KeyError` cache miss, and
add a test for it — right now the behaviour is undocumented and untested in either direction.

#### WR-02: The threat-posture docstring asserts a security property that is false — escaping store keys ARE reachable from the public feature-name DSL

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:62-71`
**Severity:** WARNING (documentation asserting a false security property; duplicated into records that carry to Phase 6)

The docstring states:

> the feature-name DSL cannot currently produce an escaping key, because every registered
> `regex_pattern` anchors on a literal prefix (`range`, `scalar_field_`, `rrim`, `sqrt_`, …),
> so no store key can begin with `..` or `/`. […] This is hardening of a public API surface,
> not a live exploit path from untrusted point-cloud metadata.

Both clauses are wrong, and I reproduced both against the real pipeline.

**(a) The registry has an unanchored default fallback.** `FeatureRegistry.match`
(`src/pc2img/features/registry.py:73-81`) returns a pseudo-spec bound to `ScalarFieldFeature`
with `params={"feature": name}` for **any** name that matches no pattern. No prefix is
required. `FeatureManager.submit` then uses that name verbatim as the store key
(`manager.py:72-73`). With a point cloud carrying a scalar field of that name:

```
# guard removed:
generate(["../victim"])  ->  OK, keys: ['../victim']
outside listing: ['cache', 'victim.dat', 'victim.npy']   # written OUTSIDE the cache dir
# guard present:
generate raised: ValueError Refusing raster key path '.../cache/../victim.npy' ...
```

A store key that literally begins with `..`, produced by the documented public API.

**(b) Prefix anchoring does not prevent traversal.** `ScalarFieldFeature.regex_pattern` is
`^scalar_field_(?P<feature>.+)$` — the suffix is unconstrained. Scalar-field names come from
the point-cloud file (PLY/E57 property names), i.e. from untrusted metadata:

```
requested feature: scalar_field_a/../../scalar_field_victim
# guard removed: generate OK, and 'scalar_field_victim.dat' appears one level ABOVE the cache dir
# guard present: ValueError ... resolves to '/tmp/.../scalar_field_victim.npy', outside ...
```

The diff's own test file already encodes this shape as `embedded_traversal: "a/../../victim"`
(`tests/test_image_store.py:246`), which directly contradicts the docstring's reasoning.

This matters because the same paragraph is duplicated verbatim into `05-BC-NOTES.md` entry 15
("Reachability, stated honestly … **NOT reachable through the feature-name DSL**") and into
`05-UAT.md` `review-r1-a239bdbfc017`'s `reason` field, both flagged *carry into Phase 6
BC-01*. The false posture is what a future maintainer will inherit, and it is the exact
argument someone would use to relax the guard for the WR-01 symlink regression.

**Fix** — replace the reachability paragraph with the measured facts, e.g.:

```
Threat posture, measured 2026-07-28: escaping keys ARE reachable from the public
API. FeatureRegistry.match falls back to ScalarFieldFeature for any unmatched
name (registry.py:73-81), so generate(["../victim"]) produces the store key
"../victim" verbatim; and ScalarFieldFeature's own pattern
^scalar_field_(?P<feature>.+)$ accepts an embedded traversal, so a scalar-field
name read out of a PLY/E57 file reaches this builder unsanitized. Without this
guard both routes write outside the cache directory. This guard is load-bearing,
not defence in depth.
```

Apply the same correction to `05-BC-NOTES.md` entry 15 (forward-only: append a correcting
paragraph rather than rewriting the entry) and to the `05-UAT.md` entry's `reason`.

#### WR-03: `test_escaping_key_add_refuses_before_writing_outside_cache_dir` does not test what its name and docstring claim

**File:** `tests/test_image_store.py:279-290`
**Severity:** WARNING (proving test weaker than advertised, on the security-relevant route)

The docstring says "must refuse **before any outside file is created or truncated**", and the
body asserts `sentinel.exists()` and `sentinel.read_bytes() == _SENTINEL_BYTES` after the
`pytest.raises`. But `add_image_to_store` alone never writes — measured against a
guard-removed build, for all three spellings:

```
  '../victim':      after add -> sentinel intact: True   | after offload -> intact: False
  'abs':            after add -> sentinel intact: True   | after offload -> intact: False
  'a/../../victim': after add -> sentinel intact: True   | after offload -> intact: False
```

Both sentinel assertions therefore pass identically with and without the guard; the entire
sensor is the single `pytest.raises(ValueError)` line. (Confirmed independently: removing the
guard in a scratch checkout turns these three parametrisations RED only on `DID NOT RAISE`.)
The test does not demonstrate the "before any write" property the truth statement and
`05-BC-NOTES.md` entry 15 both claim it demonstrates.

**Fix** — put the write inside the guarded region so the sentinel assertions become live:

```python
    with pytest.raises(ValueError):
        store.add_image_to_store(key, _gray((4, 4)))
        store.offload_image_data_to_disk(key)   # the step that actually writes
```

#### WR-04: The documented containment invariant is broader than the implementation — `offload(pickle_container=False)` writes through the entry's own path and never reaches the guard

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:26-33` and `:165-171`
**Severity:** WARNING (over-claimed invariant on a public method declared in this file)

The class docstring (added by this diff) reads:

> **Containment invariant (WR-02):** every on-disk path this store builds must resolve
> *inside* the configured cache directory.

`DiskBackedImageStore.offload(features)` defaults to `pickle_container=False`, which delegates
to `entry.offload()` and writes through the entry's **own** `_cache_path` — a path the store
never builds and the guard never sees. Reproduced 2026-07-28 through public API only:

```python
store["range"] = DiskBackedImageData(np.ones((4, 4), np.float32),
                                     enable_caching=True, cache_path=outside_dat)
store.offload("range")
# outside file now: b'\x00\x00\x80?\x00\x00\x80?...'   <- overwritten with raster bytes
# cache dir listing: []
```

The narrow WR-02 truth ("a store *key* can never cause `unlink()` to touch a file outside the
cache directory") still holds — the escape here comes from the value, not the key. But the
class docstring reads store-wide and will be understood as such.

**Fix** — either narrow the wording to what is enforced ("every on-disk path this store builds
**from a key**…, and note that an entry inserted via `store[key] = value` carries its own
`cache_path`, which this guard does not cover"), or override `__setitem__` to validate the
incoming entry's `cache_path` through `_assert_within_cache_dir`.

#### WR-05: The RRIM precedence tests pin only the private parsers, not the public surface where the BC event actually bites

**File:** `tests/test_rrim_features.py:272-322`
**Severity:** WARNING (pinning test does not cover the contract it is cited for)

`05-BC-NOTES.md` entry 16 states the break as "the same public name, resolving to the same
cache key, now denotes a different computation", and cites these two tests as the pin. Both
tests call `rrim_module._parse_rrim_config` / `_parse_rrim_component` — private functions. The
public path is `FEATURES.match(name)` → `dependencies_for(params)` → the derived pack name,
which is what schedules rasters and what becomes the cache key. Nothing asserts it.

A refactor that moved the `_looks_like_option_token(tokens[0])` decision into
`dependencies_for` (or changed how `params["args"]` is threaded) would keep both tests green
while the public behaviour drifted — and `dependencies_for` is precisely the surface this
phase rewrote for G1.

**Fix** — add one public-surface assertion. Measured on HEAD:

```python
def test_exponent_token_precedence_is_visible_at_the_registry_surface() -> None:
    assert FEATURES.match("rrim_pack_(z1e5)").dependencies == ["range"]
    assert FEATURES.match("rrim_(z1e5)").dependencies == [
        "range",
        "rrim_pack_(range,r16,d8,z100000)",
    ]
    assert FEATURES.match("rrim_component_(slope,z1e5)").dependencies == ["range"]
```

### Info

#### IN-01: `_assert_within_cache_dir` calls `resolve()` up to three times per rejected path

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:81-87`
`path.resolve()` is recomputed at `:82` and again at `:85` inside the f-string. Hoist it into
a local. (The docstring's "~40 µs per path build" cost claim is honest — I measured 50.4 µs
guarded vs 1.3 µs for the base builder, i.e. ~49 µs of overhead, all of it `resolve()`.)

#### IN-02: `_get_meta_path`'s guard can never be the one that fires, and no test exercises it

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:94-96`
Every route builds the npy path first — `add_data_to_store` (`disk_backed_store.py:326`, npy
only), `_store_entry` (`:418` then `:419`), `_load_entry` (`:483` then `:484`), and
`__delitem__` (`:157` then `:158`). The meta-path guard is therefore unreachable *as a guard*.
Fine as defence in depth, but a divergence between the two overrides would be invisible to the
suite. Add a direct assertion, e.g. `with pytest.raises(ValueError): store._get_meta_path("../victim")`.

#### IN-03: The "four routes that touch the disk" enumeration omits the `LazyDiskCache` memmap `<key>.dat`

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:52-61`
In the guard-removed reproductions the file that appeared outside the cache directory *first*
was `victim.dat` — the memmap `LazyDiskCache` creates from the `cache_path` handed to the
factory. It is covered transitively (that `cache_path` is `_get_npy_path(key)`), but the
docstring's list reads as exhaustive and does not mention it. Add it as route 0, or say
"…plus the entry's own `<key>.dat` memmap, whose path is derived from route 1".

#### IN-04: Unused sentinel binding in the false-positive-bound test

**File:** `tests/test_image_store.py:310`
`_sentinel, cfg = _escape_layout(tmp_path)` — the sentinel is never used here; only the
"cache dir is a subdirectory" side effect is needed. Either use it (assert it is untouched
after the round trip, which would make the test bound false positives *and* stray writes) or
split a `_cache_layout` helper out of `_escape_layout`.

#### IN-05: The delete route is pinned for only one of the three escape spellings

**File:** `tests/test_image_store.py:241-247`, `:250-276`
`_escaping_keys` defines three spellings and the add route is parametrised over all three, but
the delete route hardcodes `"../victim"`. The `absolute` spelling in particular exercises a
different `Path.__truediv__` behaviour (absolute right-hand operand replaces the left). Reuse
the same `@pytest.mark.parametrize` on the delete test.

---

_Reviewed: 2026-07-28T14:20:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep — every finding reproduced by running code against `.venv/bin/python`; guard removal verified in a throwaway git worktree with `PYTHONPATH` shadowing the editable install; no source file modified._
