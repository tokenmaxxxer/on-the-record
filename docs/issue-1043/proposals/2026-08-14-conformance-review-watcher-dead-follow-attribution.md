---
status: proposed
files:
  - docs/issue-1043/reports/conformance-review/survey.md
  - docs/issue-1043/proposals/2026-08-14-conformance-review-watcher-dead-follow-attribution.md
  - docs/issue-1043/reports/conformance-review.md
---

## Intent

Conformance-review the merged watcher-dead follow-attribution fix
(`origin/main`'s commit 5f5e5ff0, closing issue #1043) against the two
acceptance cases the issue itself states: a per-requirement Present /
Surface / Absent / Incorrect / Unverifiable verdict, checked from the
artifact (`spawn.py`, `tests/test_spawn.py`) and the spec (issue #1043's
own `## Acceptance` block), not from `docs/issue-1043/reports/implementation.md`'s
stated intent.

## Constraints

- Evidence must be re-run live this session, not a restatement of the
  implementation record's own pasted pytest output.
- No fixes performed here; the one open finding the implementation
  record already logged (a TOCTOU race in `_watch()`'s watcher-claim
  read-before-write) is carried into the verdict record as-is, not
  re-litigated or fixed.

## What will be done

Phase 2 renders one verdict per acceptance case in issue #1043's
`## Acceptance` block:
1. stale auto-armed pid + live follow watcher → no `watcher-dead` flag
2. no watcher at all → flag fires

against `tests/test_spawn.py`'s `WatchFollow.test_watcher_dead_stale_pid_cleared_by_live_follow_registration`
and `test_watcher_dead_or_missing_still_fires_with_no_watcher_registered`,
plus a fresh read of the `_watch()` call site (spawn.py:3964-3968) that
implements the read-before-write guard. `docs/issue-1043/reports/conformance-review/survey.md`
(this phase's own current-state survey) already independently reproduced
`python3 -m pytest tests/test_spawn.py -k watcher_dead` and confirmed
both cited test names and the cited code exist at HEAD of `origin/main`.

## Out of scope

- Fixing or filing a new issue for the open TOCTOU-race finding — it is
  already logged with a resolution path in `docs/issue-1043/reports/implementation.md`'s
  own `## Open findings` section; this review's record will restate it,
  not reopen it.
- Reconciling the issue's own inconsistent requirement linkage (its
  body cites "R001" but the parenthetical describes northpole req#7 /
  watch-coverage, which `docs/specs/requirements.md`'s actual R001 text
  does not match) — noted in the survey, not something this review
  resolves.

## How you'll know it worked

`docs/issue-1043/reports/conformance-review.md` exists (phase 2), states
a Present/Surface/Absent/Incorrect/Unverifiable verdict for each of the
two acceptance cases against the merged commit, and the one open finding
already logged upstream is carried forward with its resolution path
intact.
