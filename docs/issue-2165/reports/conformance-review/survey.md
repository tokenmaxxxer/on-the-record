---
issue: 2165
role: conformance-review
---

# issue-2165 — current-state survey

## Scope

Subject under review: PR #2170 (`issue-2165/implementation` branch, open,
HEAD commit `e2fdec458f6d43671458844e1259ec0de91b95ff`), the delivery
issue #2165 asks this review to check.
canonical: `gh pr view 2170 --json state,mergedAt` — result: `{"state":"OPEN","mergedAt":null}`

Issue #2165's body asks for a fix closing a respawn gap plus a regression
test.
canonical: `gh issue view 2165 --json body`

PR #2170's own write set, per its file list:
`gates/spawn_on_pr.py`, `tests/test_spawn_on_pr.py`, plus its phase-1
homes and its own record.
canonical: `gh pr view 2170 --json files`

## Requirement extraction (conformance-review-requirement-extraction)

Split from issue #2165's `## Fix` / `## Acceptance` sections plus its
trailing `empty state:` / `provenance:` notes, one obligation per line,
dimension-tagged. Each line paraphrases the issue's own text.
canonical: `gh issue view 2165 --json body`

- **R1** [functional] Close the merged-subject skip gap that let
  issue-513 evade the merge check for many cycles, using the same skip
  logic other subjects in the same watchdog cycle already use correctly.
- **R2** [edge-case, conditional] Add a regression test reproducing
  #513's shape, conditioned on: the underlying defect being
  issue/subject-specific (e.g. a naming edge case or a merge-detection
  race) rather than a generic flakiness issue.
- **R3** [functional] A subject whose PR merges triggers no further
  observer-role spawns on subsequent poll ticks.
- **R4** [test-coverage] R3 has coverage in `tests/test_spawn_on_pr.py`.
- **R5** [test-coverage] R3 has coverage in
  `tests/test_spawn_on_pr_park.py`, specifically a scenario simulating
  the #513 shape.
- **R6** [scope-boundary] Executed acceptance evidence (command + actual
  output) appears in the record, per #2137's verify-at-landing
  convention.
- **R7** [edge-case] A fresh clone with no prior `spawn_on_pr.py` runs
  (no sticky-cache file yet) is treated as empty/not-yet-confirmed, not
  an error.
- **R8** [provenance] Verification provenance is executed-live:
  `tests/test_spawn_on_pr.py` and `tests/test_spawn_on_pr_park.py` run
  against the real fault-injection harness already used by #1476/#1643's
  precedent.
- **R9** [scope-boundary, unverifiable-as-written] Determine whether the
  respawn pattern is bounded or unbounded and quantify the token/session
  cost of the reported ~50 near-instant respawns. No numeric acceptance
  threshold is stated in the issue, and this workspace has no log access
  to the external target repo #513 ran in — flagged per
  requirement-extraction rule 2 rather than a guessed number.

No summary line met rule 3's drop condition. No requirement needed rule
4's sampling-derivation carve-out — the issue states no sampling scope of
its own.

## Sampling-derivation — not applicable

Full enumeration of R1-R9 is feasible: one source file plus one test
file, both small.
canonical: `gh pr view 2170 --json files,additions,deletions` — result:
`{"additions":543,"deletions":0}` across 7 files, with
`gates/spawn_on_pr.py` at +41/-0 and `tests/test_spawn_on_pr.py` at
+75/-0.

## Verification-method plan (conformance-review-verification-method-selection)

- R1, R3, R4: Test — reuse the two regression tests PR #2170 adds rather
  than re-derive a manual check.
- R2: Inspection (test presence) then Test (its run result).
- R5: Inspection first — see gap noted below.
- R6: Inspection of the implementation record's own verification section.
- R7: Inspection + Analysis of `load_merged_seen()`'s fail-safe branch.
- R8: Analysis — this repo's "executed-live" convention (per #1476/#1643
  precedent) is a real pytest run against a fixture repo with
  `monkeypatch` on the `gh`-backed leaf calls, not literally-unmocked
  `gh`.
- R9: no method applies — unverifiable-as-written from this workspace.

## What PR #2170 adds (grounded in its own diff)

The diff adds `MERGED_SEEN_STATE_REL`, `load_merged_seen()`,
`_save_merged_seen()`, and a merged-seen short-circuit inside
`missing_verification()`.
canonical: derived: `gh pr diff 2170` — result (excerpt,
`gates/spawn_on_pr.py` hunk):
```
+MERGED_SEEN_STATE_REL = Path("runs") / "spawn_on_pr_merged_seen.json"
+        if merged_seen is None:
+            merged_seen = load_merged_seen(root)
+        if subject in merged_seen:
+            continue
```

The same diff adds two new test functions to `tests/test_spawn_on_pr.py`:
`test_missing_verification_sticky_merged_cache_survives_flaky_reconfirm`
and `test_spawn_missing_for_pr_sticky_merged_cache_zero_spawns_across_ticks`.
canonical: derived: `gh pr diff 2170` — result (excerpt,
`tests/test_spawn_on_pr.py` hunk):
```
+def test_missing_verification_sticky_merged_cache_survives_flaky_reconfirm(
+        fixture_repo, monkeypatch):
+def test_spawn_missing_for_pr_sticky_merged_cache_zero_spawns_across_ticks(
+        fixture_repo, monkeypatch):
```

The PR's own body reports its test run.
canonical: `gh pr view 2170 --json body` — result (excerpt):
```
python3 -m pytest tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py -q — 28 passed, 0 failed, 0 skipped
python3 -m pytest tests/test_watchdog_local_signals.py tests/test_watchdog_freshness.py -q — 20 passed, 0 failed, 0 skipped
```

This review's own worktree (`issue-2165/conformance-review`, branched
from `main`) predates PR #2170's diff — `git log` on
`gates/spawn_on_pr.py` in this worktree shows no issue-2165 commit yet,
so the counts above are PR #2170's own claim, not yet independently
re-run by this review.
canonical: `git log --oneline -1 -- gates/spawn_on_pr.py` — result:
`3ca748c4 issue-1745 phase 2 continuation ...` (predates issue-2165)

## Existing precedent this design mirrors

`closure_sweep.py` already carries the same "confirmed-once,
remembered-forever" cache shape for a related problem, on this worktree's
current `main`-based state.
canonical: `gates/closure_sweep.py:297-316`
```
def _load_out_of_index_seen(root: Path) -> set[str]:
    p = root / OUT_OF_INDEX_SEEN_STATE_REL
    if not p.is_file():
        return set()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return set()
```

## Gap candidate for phase-2 (R5)

`tests/test_spawn_on_pr_park.py` is absent from PR #2170's file list.
canonical: `gh pr view 2170 --json files` — result: file list contains
`gates/spawn_on_pr.py` and `tests/test_spawn_on_pr.py` only, no
`tests/test_spawn_on_pr_park.py` entry.

A text search of this worktree's current `tests/test_spawn_on_pr_park.py`
for a #513/merged-cache scenario returns no match.
canonical: derived: `grep -n "513\|merged_seen\|MERGED_SEEN" tests/test_spawn_on_pr_park.py`
```
(no output — zero matches)
```

Phase-2 needs a verdict call here: whether Acceptance bullet 1's
parenthetical naming `test_spawn_on_pr_park.py` specifically is satisfied
by the new tests instead living in `test_spawn_on_pr.py`, or whether this
is a genuine Absent/Incorrect against R5 as literally worded.

## Gitignore check

`runs/` (the new cache file's parent) is already covered by a blanket
gitignore entry, matching the existing `spawn_on_pr_parked.json`
convention.
canonical: `.gitignore:1`
```
runs/
```

## Open findings carried into the proposal

1. R5 gap candidate above — resolution path: phase-2 re-reads Acceptance
   bullet 1 literally against what actually landed and states a verdict
   with the specific clause named either way.
2. R9 — resolution path: phase-2 states unverifiable-as-written plainly,
   citing this workspace's lack of access to the external target repo.
