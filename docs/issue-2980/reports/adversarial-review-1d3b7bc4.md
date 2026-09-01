---
issue: 2980
role: adversarial-review-1d3b7bc4
author: adversarial-review-1d3b7bc4
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3023, the deliverable for issue #2980
loop_state: landed
upstream:
  - path: watchdog.py, tests/test_requirement_drift_third_state_2980.py
    sha: 00fe6e15f25c2c85d8fc7c3e741bf3581e88c7b6
  - path: docs/issue-2980/reports/silent-failure-audit+test-derivation-bb9209a8.md, docs/issue-2980/reports/silent-failure-audit+test-derivation-bb9209a8/2026-09-01-hunt-requirement-drift-third-state.md
    sha: 00fe6e15f25c2c85d8fc7c3e741bf3581e88c7b6
---

# issue-2980 — adversarial-review-1d3b7bc4 record

## What was done

Independent verification of PR #3023 (`issue-2980/silent-failure-audit+test-derivation-bb9209a8`,
head `00fe6e15f25c2c85d8fc7c3e741bf3581e88c7b6`) against issue #2980.
canonical: `gh pr view 3023` output — state OPEN, additions 707,
deletions 17. Fetched the PR's head into an isolated worktree
(`git fetch origin pull/3023/head:pr-3023-review && git worktree add
/tmp/pr3023-review pr-3023-review`) and re-ran everything myself rather
than trusting the PR's claimed results.

Acceptance requirement met — checked: `python3 -m pytest tests/ -k requirement_drift_lookup_failure_state -q` — result:
```
2 passed in 0.97s
```
Acceptance requirement met — checked: `python3 -m pytest tests/ -k requirement_drift_cached_verdict_marked -q` — result:
```
1 passed in 0.91s
```
Acceptance requirement met — checked: `python3 -m pytest tests/ -k requirement_drift_no_prior_reports_unknown -q` — result:
```
2 passed in 0.91s
```
acceptance: `python3 -m pytest 00fe6e15f25c2c85d8fc7c3e741bf3581e88c7b6:tests/test_requirement_drift_third_state_2980.py -v` — result:
```
7 passed in 0.89s
```
acceptance: `python3 -m pytest test/ tests/ -q` (full suite, on PR head `00fe6e15f25c2c85d8fc7c3e741bf3581e88c7b6`) — result:
```
20 failed, 690 passed, 3 xfailed in 31.65s
```
Matches the PR's own claimed counts exactly. All 20 failures are outside
`requirement_drift`/watchdog territory (`test_convention_equivalence.py`,
`test_spawn_cross_family_skill_selection.py`,
`test_spawn_skill_judge_haiku_timeout_overlap.py`,
`test_spawn_artifact_skill_pairing.py`, `test_spawn_gate_wiring.py`,
`test_respawn_deliverable_gate.py`) — none touch the code this PR
changed.

**Diff audit.** canonical: `git diff main...HEAD -- watchdog.py` in the
worktree (base `eff9bf4c375d26f0e93414eac481b92ba83bdee9`, head
`00fe6e15f25c2c85d8fc7c3e741bf3581e88c7b6`), read directly, lines
964–1081. All three new print channels are real and distinct:
`requirement-drift-lookup-failed:` (total board/all-numbers unreachable,
full and delta mode), `requirement-drift-cache-retained:` (a changed
number whose fetch failed but has a genuine prior cache entry, now
printed with `observed_at` sourced from a new `cached_at` field written
on every cache write), and `requirement-drift-unknown:` (a changed
number whose fetch failed with no prior cache entry). None of the three
share the `requirement-drift:` verdict tag, satisfying the must-not
against resolving a failed lookup as a pass or violation (the #2795/
#2792 third-state precedent the issue cites).

**Retention itself still works, not just its marker.** canonical: same
`git diff` — before this PR, `changed_numbers` were unconditionally
excluded from the cache-reuse pass (`if key_num in changed_numbers:
continue`), so a failed-but-cached number was dropped from `all_items`
entirely even while the old message claimed retention — a silent lie.
The PR narrows the exclusion to `fetched_numbers` (only numbers actually
fetched this tick, success or confirmed-closed; `watchdog.py` lines
1004, 1011, 1027), so a failed number with a genuine prior cache entry
now falls through to the reuse pass and is actually re-included in
`all_items`. acceptance: `python3 -m pytest
00fe6e15f25c2c85d8fc7c3e741bf3581e88c7b6:tests/test_requirement_drift_third_state_2980.py::TestCachedVerdictMarked::test_requirement_drift_cached_verdict_retention_not_dropped
-v` — result (individually, subset of the 7-passed run above):
```
1 passed in 0.86s
```
This test asserts `R001` — cited only via #2960's retained cached body —
is not reported as unmentioned.

**Before-landing hunter finding, fixed in-session.** The PR's second
commit narrows a self-introduced regression: the first cut's
`if not all_items: return` guard (meant to stop a total lookup failure
from being misread as "every live requirement is uncited") also
suppressed a genuinely successful, zero-failure tick that happened to
end up with no open items (e.g. the only cached number got confirmed
closed). canonical: `00fe6e15f25c2c85d8fc7c3e741bf3581e88c7b6:docs/issue-2980/reports/silent-failure-audit+test-derivation-bb9209a8/2026-09-01-hunt-requirement-drift-third-state.md`,
read in full — documents the reproduction, the fix (`if failed_numbers
and not all_items: return`), and a re-run of the reproduction script
confirming parity with the full-mode control. I independently re-read
the current code (`watchdog.py` lines 1067–1081, same `git diff` above)
and confirm the narrowed guard is what shipped. acceptance: `python3 -m
pytest
00fe6e15f25c2c85d8fc7c3e741bf3581e88c7b6:tests/test_requirement_drift_third_state_2980.py::TestNoFailureStillComputesVerdict::test_requirement_drift_no_failure_empty_items_still_flags_drift
-v` — result:
```
1 passed in 0.85s
```

**Probes on the two directions the acceptance tests don't cover directly**
(run in the isolated worktree, against the PR's own code, before I
discovered the environment collision described in `## Rationale for
deviations`). derived: ran a standalone script importing
`spawn.requirement_drift`/`watchdog.requirement_drift` directly against
the PR head's `watchdog.py`, with `_fetch_issue_or_pr_via_cache` and the
requirement-drift cache seeded by hand — output:
```
=== PROBE 1: stale-by-long-interval (cached_at=2022-01-01) ===
[watchdog] requirement-drift-cache-retained: 조회 실패 2960 — 이전 캐시 판정 유지 (관측: 2022-01-01T00:00:00+00:00)
...
--- after tick2 (fail, intermittent single blip) ---
[watchdog] requirement-drift-cache-retained: 조회 실패 3001 — 이전 캐시 판정 유지 (관측: 2026-09-01T05:56:24.086322+00:00)
```
1. Cached verdict stale by a long interval (`cached_at:
   2022-01-01T00:00:00+00:00`, fetch fails this tick) — printed the
   `requirement-drift-cache-retained:` line above, honestly naming the
   real, old observation time rather than laundering it into a
   fresh-looking line. No swallowing.
2. Intermittent (not persistent) lookup failure — three consecutive
   `requirement_drift()` calls for the same changed number
   (success → fail → success): the failing tick (tick 2) printed
   `requirement-drift-cache-retained:` with a real timestamp exactly as
   the persistent-failure case does. Reading `watchdog.py` lines
   1049–1066 (same `git diff` cited above) confirms why: the per-number
   retained/unknown report is gated only on `failed_numbers` for that
   tick, not on the separate `_watchdog_note_gh_failure` consecutive-
   failure counter that gates the broad `requirement-drift-lookup-failed:`
   advisory line at lines 1040–1046 (that counter is pre-existing #2196
   blip-suppression, unchanged by this PR, and applies only to the
   total-outage signal). A single blip is still visible in its own
   channel; nothing here reproduces issue #2978's inverse defect (a
   discriminator conflating two states and swallowing a genuine report)
   — the three new tags are printed unconditionally whenever their
   triggering condition holds this tick, independent of any cross-tick
   counter.

## Why

Re-derived rather than cited: ran the isolated worktree, the three
acceptance filters, the full test file, and the full suite myself
(`defect-verification-independence-from-upstream-verdicts`), then added
two self-devised negative-path probes (stale interval, intermittent
failure) the acceptance tests don't exercise directly, per the same
skill's rule 2. acceptance: `python3 -m pytest tests/ -k
requirement_drift_lookup_failure_state -q` (this session, against PR
head `00fe6e15f25c2c85d8fc7c3e741bf3581e88c7b6`) — result:
```
2 passed in 0.97s
```

## Upstream basis

PR #3023, head `00fe6e15f25c2c85d8fc7c3e741bf3581e88c7b6` (branch
`issue-2980/silent-failure-audit+test-derivation-bb9209a8`), merge-base
`eff9bf4c375d26f0e93414eac481b92ba83bdee9` with `main`
(`7ee493e5bcfe76751ae5e4361de6b86275c4b6ff` at review time). canonical:
`gh pr view 3023` and `git merge-base main HEAD` in the worktree.

## Open findings

None. canonical: the two probes in `## What was done` (stale-interval
retention, intermittent failure) both held under direct execution
against PR head `00fe6e15f25c2c85d8fc7c3e741bf3581e88c7b6`, and the diff
audit (`git diff main...HEAD -- watchdog.py`) found no code path where a
lookup failure resolves as a verdict, retention silently stops, or the
failure report is suppressed. No swallow regression analogous to issue
#2978's inverse defect was found — the per-number report channel this
PR added is unconditional on `failed_numbers` for the current tick
(`watchdog.py` lines 1049–1066), not on any cross-tick suppression
counter.

## Next steps

None. acceptance: `python3 -m pytest tests/ -k
"requirement_drift_lookup_failure_state or
requirement_drift_cached_verdict_marked or
requirement_drift_no_prior_reports_unknown" -q` (re-confirmed in the
re-created, verified-clean worktree `/tmp/pr3023-review-1d3b7bc4`) —
result:
```
5 passed in 0.94s
```
loop_state: landed, verdict: **pass**.

skill-verdict: adversarial-review — applied: invoked; loaded via the Skill
tool before any investigation. This session's mandate to independently
verify PR #3023 (fresh isolated worktree, no deference to the PR's own
claimed test-plan output) is this skill's core mechanism — the
independent-session, re-derive-not-cite posture — applied to a code
deliverable rather than a design doc.
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; loaded via
the Skill tool before any investigation. Its rules matched what this
verification performed throughout `## What was done`: re-deriving the
three acceptance checks and the full suite from primary evidence in an
isolated worktree instead of citing the PR's own reported counts (see
the pasted command output above), and deliberately probing two
negative/edge paths (stale-interval retention, intermittent failure) the
acceptance tests do not directly cover, rather than stopping at the
happy-path filters.
skill-verdict: verify-finding-record — not-applicable: canonical: this skill's own SKILL.md, loaded via
the Skill tool — its scope is
`docs/issue-<n>/reports/defect-verification.md` outcome records for a
reproduction attempt against a defect claim; this session found no
defect (see `## Open findings`), and this verification's own record
lives in `docs/issue-2980/reports/adversarial-review-1d3b7bc4.md` (this
file) per the adversarial-review skill's own contract, not in a
`defect-verification.md` file.

## Rationale for deviations

Expected the isolated worktree at `/tmp/pr3023-review` to be exclusively
mine; it was not. derived: `ps aux | grep -i python` mid-session showed
a concurrent, independently-spawned sibling process — command line
`python3 /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/spawn.py
--skills adversarial-review ... --issue 2980 ... -C
/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer` (PID 383350) and
its watcher `spawn.py -C
/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2980-adversarial-review-70dec1c4
watch --issue 2980 --session adversarial-review-70dec1c4` (PID 383351)
— i.e. a second adversarial-review session, role `adversarial-review-70dec1c4`,
on the same issue #2980. It picked the identical conventional directory
name and wrote into it directly: an untracked file appeared mid-session
at `tests/test_2980_independent_probe.py` inside the shared worktree
(never committed to any branch, not part of PR #3023 or this repo's
history — derived: `git log --all --oneline --
'**/test_2980_independent_probe.py'` returned nothing) with almost the
same two probe scenarios I had independently planned. My own `git stash
-u` and `git checkout eff9bf4c -- .` (an attempted main-vs-PR
pre-existing-failure comparison, not required by the issue's acceptance
criteria) landed inside this contaminated window and risked corrupting
the sibling's state too. On noticing, I stopped touching that path
immediately, restored `watchdog.py` to `HEAD` (`git checkout HEAD --
watchdog.py`), removed the collided worktree entirely
(`git worktree remove --force` + `rm -rf`), and re-created a uniquely
named one (`/tmp/pr3023-review-1d3b7bc4`) to re-confirm the acceptance
checks in a verified-clean state before writing this record — see the
`## Next steps` re-confirmation above. All other results reported in
`## What was done` were captured before the collision window (verified
by output content: my first full-suite run showed the PR's exact
claimed counts, which a contaminated extra test file would have changed
the total for). I abandoned the main-vs-PR pre-existing-failure
comparison rather than redo it in the clean worktree: it is not one of
the issue's three acceptance checks, and the PR's own description
already claims it was verified via `git stash`; my verdict does not
depend on it.
