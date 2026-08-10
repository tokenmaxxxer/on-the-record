---
proposal: docs/proposals/2026-08-10-resolve-gate-naming-reference.md
---

# Hunt record — resolve-gate-naming-reference


## after-proposal — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — the proposal's corrected prose ("external harness, not a packaged hook") is asserted by a one-time manual doc edit with no mechanical check tying it to filesystem/`hooks.json` reality; if `on-the-record/hooks/` ever gains a `.sh` file matching either name, `gates/test_boundary.py` will flag that new file as missing a boundary-spec row, but nothing re-flags the now-stale "external harness" claim in the two implementation-record files, so the drift this proposal fixes can silently recur in the opposite direction.
Kind: design-error
Seed: docs/issue-638/proposals/2026-08-10-resolve-gate-naming-reference.md
cap_seconds: 60
tier: default
diff_stat_lines: 0 (proposal not yet applied; docs-only diff per dispatcher)
started_at: 2026-08-10T00:00:00Z
ended_at: 2026-08-10T00:05:00Z

### Reproduce
grep -rln "issue-600" gates/*.py               # no output: no gate reads that record file
grep -rln "issue-623" gates/*.py               # no output: no gate reads that record file
sed -n '1,80p' gates/test_boundary.py          # _actual_mechanisms() globs on-the-record/hooks/*.sh by filename only, compares against docs/specs/enforcement-boundary.md rows; never touches either report file's text

### Observed
`gates/test_boundary.py`, the only mechanized check the proposal cites as its safety net ("must stay green"), derives its check purely from `on-the-record/hooks/*.sh` filenames vs. `docs/specs/enforcement-boundary.md` rows. It has no rule, assertion, or reference anywhere that reads either of the two report files this proposal edits. The proposal explicitly puts `docs/specs/enforcement-boundary.md` out of scope ("no real file exists to register"), so even the one spec that could plausibly gate this claim is deliberately left untouched.

### Expected
For the "external harness, not a packaged hook" claim to hold as a durable fact rather than a one-time snapshot, something (a gate, a test, or at minimum a spec row/comment) would need to re-derive or re-check that neither gate name exists under `on-the-record/hooks/`, and fail loudly if one ever does — otherwise the correction is the same kind of unguarded prose claim that produced the original stale reference #638 is fixing.
