---
proposal: docs/decisions/2026-08-25-retire-role-axis-staging.md
---

# Hunt record — retire-role-axis-staging

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: NO FINDING
Seed: full diff main...HEAD (docs/ only — survey.md, scout-brief.md, ADR, 7 stage proposals, architecture.md record)
cap_seconds: unspecified (not provided by dispatcher in prompt)
tier: default
diff_stat_lines: 1232 insertions across 10 files
started_at: 2026-08-25T00:00:00Z
ended_at: 2026-08-25T00:45:00Z

Checked two specific angles handed in the brief plus a general third:

(a) `files:` list quietly omitting a path the body says is touched, to
dodge accumulation-claim-guard's `.py`/`roles/*.json` shape scan.
Every one of the 7 proposals has a filled `## Accumulation` section
(grepped `^## Accumulation` in all 7 — all present with non-empty
bodies), which short-circuits the guard's `hit and not filled` deny
regardless of whether `_touches_shape_5`'s `^roles/[^/]+\.json$` regex
matches stage-6's `roles/`/`roles/specs/` directory-style `files:`
entries (it does not — confirmed by inspection of
`on-the-record/hooks/accumulation-claim-guard.sh` `_touches_shape_5`).
Cross-checked every `.py` name mentioned in each proposal body against
its `files:` list: the one repeated omission (`merge_gate.py`, named in
stage 0/1/2/3/4 bodies but absent from their `files:` lists) is in every
case explicit "must not touch `merge_gate.py` — stage 5's job" scope
language, not a disguised touch. No omission-to-dodge found.

(b) A path/line-range citation that resolves differently under the
OLDER `on-the-record/gates/record_lint.py` (which `record-claim-guard.sh`
actually imports, confirmed: `script_dir/../gates` = `on-the-record/gates`
exists and is checked before `../../gates`, so the stale copy always
wins) than under the canonical `gates/record_lint.py`. Confirmed by
running both modules' `canonical_source_claim_check`,
`outcome_claim_citation_check`, `bare_count_claim_check`,
`orphaned_path_reference_check`, `defect_claim_grounding_check` against
the actual new content (`docs/issue-2241/reports/architecture.md`,
`docs/issue-2241/reports/architecture/survey.md`,
`docs/issue-2241/reports/architecture/scout-brief.md`) — output was
byte-identical between old and new on every file. Root cause: every
citation in this diff with the `_PATH_REF`-required prefix
(`docs/|gates/|on-the-record/|src/|test/|tests/`) uses a plain
`:N` or `:N-M` suffix (e.g. `` `docs/issue-651/reports/implementation/survey.md:16-31` ``),
which both the old and new `_LINE_SUFFIX` regex strip identically. The
comma-list citations that do exist in this diff
(`` `board.py:667,691,699` ``, `` `board-gate.sh:614,723-762` ``,
`` `consult.py:470-471,484` `` — all in survey.md) are bare filenames
with no `docs/|gates/|on-the-record/|src/|test/|tests/` prefix, so
`_PATH_REF` never captures them in either module version — the
old-vs-new `_LINE_SUFFIX`/`_FUNC_SUFFIX` divergence is real (verified
directly: `_LINE_SUFFIX.sub('', 'docs/x.md:28,34')` leaves the comma tail
in the old module, strips clean in the new one) but this diff's content
never lands a citation in the shape that would trigger the divergence.

(c) No other case found where a gate's real check is narrower than its
own stated intent that this content's actual bytes exploit. The stale
`on-the-record/gates/record_lint.py` vs canonical `gates/record_lint.py`
divergence (confirmed real, confirmed which one wins path resolution,
confirmed record-claim-guard.sh's own header comment "there is exactly
one place each rule's logic lives" is currently false) is a genuine
standing defect, but it is not something this specific diff's content
triggers a wrong outcome from — direct execution shows identical lint
results on every file this diff touches.

### Reproduce
```
cd <repo>
diff -q on-the-record/gates/record_lint.py gates/record_lint.py   # differ
script_dir="$(cd on-the-record/hooks && pwd)"
[ -d "$script_dir/../gates" ] && cd "$script_dir/../gates" && pwd
# -> resolves to on-the-record/gates (the stale copy), confirming
#    record-claim-guard.sh imports the wrong module despite its own
#    "exactly one place" comment
python3 /tmp/run_new.py docs/issue-2241/reports/architecture.md \
    docs/issue-2241/reports/architecture/survey.md \
    docs/issue-2241/reports/architecture/scout-brief.md
python3 /tmp/run_old.py docs/issue-2241/reports/architecture.md \
    docs/issue-2241/reports/architecture/survey.md \
    docs/issue-2241/reports/architecture/scout-brief.md
# (run_new.py imports gates/record_lint.py, run_old.py imports
#  on-the-record/gates/record_lint.py, both call the same five checks)
```

### Observed
`run_new.py` and `run_old.py` output is byte-identical for all three
files — no check fires differently between the canonical and stale
copies on this diff's actual content.

### Expected (if this were a live finding)
A citation in the report files shaped like `` `docs/x.md:28,34` `` or
`` `on-the-record/y.sh::func()` `` would need to produce a false-orphan
denial under the stale copy while passing clean under canonical — no
such citation exists in this diff.
