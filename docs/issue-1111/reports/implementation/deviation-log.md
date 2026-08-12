## Deviation log

- 2026-08-13T00:00:00Z, `filed`, retargeting `product-capture-stopgate.sh`'s
  write paths (proposal step 1) breaks `harness/fixture-target/scenario.py`'s
  `scenario_capture_fires_in_target_repo` assertion, which hardcodes the old
  docs/product/requirements.md fallback path (no longer written by the hook)
  and the substring "docs/product/" in the advisory context — not in this
  proposal's frozen write set. Reported, not spawned.
