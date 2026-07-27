# Phase 5 — API Coverage Declaration

No external API integration: Phase 5 fixes in-repo correctness defects and adds
unit tests; the only "API" in scope is the in-process GSEGUtils
`DiskBackedStore` base-class member surface, not an external service.

## Why this file exists

The deterministic seal-time detector fires on the phrase **"Store API-Gap
Analysis"** in `05-RESEARCH.md`. That heading refers to the in-process
base-class member surface named above — which members of the GSEGUtils
`DiskBackedStore` / `LazyDiskCache` primitives the reparented `image_cache/`
does and does not use — not to any networked or third-party service endpoint.

This file is the reasoned declaration the `api-coverage.verify-pre` gate
requires. It is deliberately **not** padded with an endpoint/coverage matrix:
Phase 5 integrates no external API, so any such matrix would be fabricated.
