---
issue: 3081
role: silent-failure-audit+implementation-blueprint+test-derivation+defect-verification-independence-from-upstream-verdicts-ba2a806f
author: silent-failure-audit+implementation-blueprint+test-derivation+defect-verification-independence-from-upstream-verdicts-ba2a806f
skills: silent-failure-audit (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12)), test-derivation (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
code_under_review: watchdog.py::requirement_drift, _requirement_drift_cache_path, _load_requirement_drift_cache, _drift_cache_key
type: bugfix
breaking: false
verdict: fixed
upstream:
  - path: watchdog.py
    sha: 573e7382282be24439c223c1603be648dd0e158f
---

# issue-3081 — silent-failure-audit+implementation-blueprint+test-derivation+defect-verification-independence-from-upstream-verdicts-ba2a806f record

## What was done

canonical: `gh issue view 3081 --repo tokenmaxxxer/on-the-record --comments`
(5 comments as of this session's last read, most importantly the
operator's correction in the 4th: the shared, orchestrator-scoped cache is
not the defect; do not narrow it to `root`).

amendments-reconciled: `issuecomment-5505557426` (5th comment, landed
mid-session after the code fix's first commit) — established the leak is
bidirectional (a study-companion PR leaked onto on-the-record's board too,
not just the reverse) and both boards printed the byte-identical union of
every repo's cache. `gates/probe_drift_repo_leak.py` and
`tests/test_requirement_drift_repo_scope.py` were both extended with a
same-tick, both-directions check per this comment's own suggestion (assert
the two boards' outputs are not identical, the tightest available signal
that no per-repo filter runs at all) — see the dedicated commit and "What
was done" below. The already-committed fix (symmetric composite-key
filtering by construction) needed no further code change; only the probe
and tests grew a case.
derived: `git checkout 573e7382 -- watchdog.py spawn.py && python3
gates/probe_drift_repo_leak.py; git checkout HEAD -- watchdog.py spawn.py`
(run against the extended, bidirectional-checking probe) — result:
`FAIL: repo B's number 77 appeared in repo A's sweep output`, exit 1 —
confirms the pre-fix code also fails the bidirectional check; re-running
the same probe with `HEAD` (this session's fix) checked out gives `ok`,
exit 0.

Two defects in `watchdog.py`'s `requirement_drift()` cache
(`requirement_drift_cache.json`, anchored via
`state_paths.orchestrator_state_path` per issue #2240 — unchanged, per the
issue's own must-not, confirmed still true after this change: checked
`grep -n "state_paths.orchestrator_state_path" watchdog.py` — result: 2
matches, `_requirement_drift_cache_path` and `_watchdog_noise_state_path`,
both still routed through it, no `root`-based path introduced):

1. **Attribution lost at report time.** Cache entries carried no repo of
   origin. Delta mode's reuse pass and full mode's cache rebuild both
   read/wrote the whole shared file with no repo check, so a sweep of one
   repo's board printed another repo's cached issues/PRs under its own
   report prefix.
2. **A failed lookup was read as confirmation regardless of whose entry it
   was.** `requirement-drift-cache-retained:` fired for any number with a
   cache hit, without checking that the hit belonged to the sweeping
   repo — a lookup failing because the entry is a different repo's PR
   looked identical to a transient `gh` blip and was retained the same
   way.

Fix: every cache entry is now keyed `repo:number`
(`watchdog._drift_cache_key`, new) instead of a flat `str(number)`, and
carries `"repo"` in its value:
- Delta mode's reuse pass only re-adds entries whose `"repo"` matches the
  sweeping repo.
- Delta mode's retention check looks up `_drift_cache_key(repo_slug, n)`
  instead of `str(n)` — a failed lookup for a number whose only cache
  entry belongs to a different repo finds no match under this repo's key
  and falls through to the existing `requirement-drift-unknown:` path.
- Full mode now loads the existing cache and replaces only this repo's
  slice, instead of overwriting the whole file.
- Legacy entries (written before this change, no `"repo"` key at all) are
  dropped in `_load_requirement_drift_cache` — they cannot be attributed
  after the fact.

derived: `python3 gates/probe_drift_repo_leak.py` — result: `ok` (exit 0).
derived: `python3 -m pytest tests/test_requirement_drift_repo_scope.py -q`
— result: `7 passed`.
derived: `python3 -m pytest
tests/test_requirement_drift_repo_scope.py
tests/test_requirement_drift_third_state_2980.py -q` — result: `14 passed`
(the pre-existing regression file plus this session's new one, together).

New: `gates/probe_drift_repo_leak.py` (standalone acceptance probe,
registered in `docs/specs/enforcement-boundary.md`) and
`tests/test_requirement_drift_repo_scope.py`
derived: `grep -c '^    def test_' tests/test_requirement_drift_repo_scope.py`
— result: `7` test methods; `grep -c '^class Test'
tests/test_requirement_drift_repo_scope.py` — result: `4` classes,
covering the decision table
documented at the top of that file (entry repo matches sweep × lookup
succeeded/failed this tick × entry predates the repo field) plus the
bidirectional/not-identical case added for the issue's 5th comment.

## Why

The issue's 4th comment (operator correction) is explicit that the shared,
orchestrator-scoped cache is not the defect — re-anchoring it to `root`
would regress issue #2240 and was ruled out as an acceptable fix in the
issue's own must-not. The defect is one step later: a stored entry has no
memory of which repo it came from, so a read that fans across every repo
an orchestrator sweeps cannot tell which entries belong to the sweep in
front of it. A repo-keyed composite cache key is the minimal change that
adds that missing dimension without touching where the cache lives — it
also resolves a latent same-file numeric collision (two repos can both
have a PR numbered the same) that a flat `str(number)` key plus a bolted-on
`"repo"` field, without changing the key itself, would not have.

Retention had to change in lockstep with attribution, per the issue's
second must-not: fixing the key alone would still let already-cached
foreign entries reprint on every tick forever, since a foreign entry's
lookup genuinely fails (it doesn't exist in this repo) and the old
retention rule read every failure as "transient, keep the prior verdict."
Composite keys make the two lookup-failure causes structurally
distinguishable for free: a same-repo transient failure still finds its
entry under this repo's key and retains (unchanged behavior, regression-
covered by the pre-existing `test_requirement_drift_third_state_2980.py`);
a wrong-repo failure finds nothing under this repo's key and correctly
falls to the existing "no genuine prior, unknown" path — no new
retain/evict flag was added, just routing the existing lookup through the
repo-scoped key.
derived: `python3 -m pytest tests/test_requirement_drift_repo_scope.py
-q -k no_retention_when_entry_is_another_repos` — result: `1 passed`.

skill-verdict: implementation-blueprint — applied: invoked; ran the
`classify --single-file` step against the change shape (one function
cluster in one module, no new files beyond tests/probe) before writing any
code
canonical: `python3
/home/jwjung/skill-registry/skills/implementation-blueprint/scripts/prep.py
classify --surface backend --external no --logic crud --asynchronous no
--single-file` — result: `VETO: single file, single concern, no callers ->
no-structure` — honored by writing the fix flat inside
`requirement_drift`/its existing helper cluster.
skill-verdict: silent-failure-audit — applied: invoked; audited the
existing failed-`gh`-lookup handling in `requirement_drift` against the
catalog before changing it, specifically checking that the new
cross-repo-mismatch case would classify as Handled (an explicit, distinct
printed line) rather than Silently Absorbed (falling into the existing
retain-by-default branch) — routed through the existing
`requirement-drift-unknown:` line instead of a new no-op branch.
skill-verdict: test-derivation — applied: invoked; derived the decision
table documented at the top of `tests/test_requirement_drift_repo_scope.py`
covering the 6 feasible columns with one test each.
skill-verdict: defect-verification-independence-from-upstream-verdicts —
not-applicable: this session implements a fresh fix from the issue's own
reported defect, not a re-verification of an upstream Present/closed_checks
verdict.

## What did not work

First cut of `_load_requirement_drift_cache`'s legacy-entry filter used
`v.get("repo")` (truthy check) to decide "has this entry been attributed."
A checkout with no resolvable `gh` slug legitimately stores `"repo": None`
(`_repo_slug` returns `None` and caches it per-root), and that truthy check
dropped those entries too, indistinguishable from genuinely pre-fix,
unattributed entries.
canonical: this session's own transcript — running
`python3 -m pytest tests/test_requirement_drift_third_state_2980.py -q`
against that first cut regressed
`test_requirement_drift_cached_verdict_marked` from pass to fail (`1
failed, 6 passed`, `AssertionError: assert 'requirement-drift-cache-
retained:' in 'requirement-drift-unknown: ...'`) before the fix below.
Fixed by checking `"repo" in v` (key presence) instead of the value's
truthiness.
derived: `python3 -m pytest
tests/test_requirement_drift_third_state_2980.py -q` — result (after the
fix): `7 passed`.

## Upstream basis

canonical: `gh issue view 3081 --repo tokenmaxxxer/on-the-record
--comments` — all 5 comments read (the 5th, `issuecomment-5505557426`,
landed mid-session — see `amendments-reconciled:` above); the acceptance
checks (`tests/test_requirement_drift_repo_scope.py`,
`gates/probe_drift_repo_leak.py`, full `pytest tests/ -q -x`) and the live
repro numbers (issue #3081's 1st comment: on-the-record PRs `3048`,
`3051`, `3056`, `3058` printed as study-companion's own open items; 5th
comment: PR `11` leaking the other direction) come from that read; this
record's probe/tests reuse `3048`/`3051`/`77` as the seeded numbers.

`watchdog.py` at commit `573e7382282be24439c223c1603be648dd0e158f` (this
branch's parent / `origin/main` at session start) — the pre-fix
`requirement_drift`, `_requirement_drift_cache_path`,
`_load_requirement_drift_cache`, `_save_requirement_drift_cache`.
derived: `git checkout 573e7382 -- watchdog.py spawn.py && python3
gates/probe_drift_repo_leak.py; git checkout HEAD -- watchdog.py spawn.py`
— result: `FAIL: repo A's number 3048 appeared in repo B's sweep output`,
exit 1 — confirms the probe fails against that exact pre-fix commit.

## Open findings

None.

## Next steps

None — `loop_state: landed`.
derived: `git log --oneline 573e7382..HEAD` — result: 4 commits on this
branch on top of `573e7382` (the code fix, the enforcement-boundary.md
registration, the session record, the bidirectional-leak extension) plus
this record update landing as a 5th. PR to be opened from this branch,
not merged (build-now bypass, single session, delivery only).

## Rationale for deviations

Two deviations from a literal reading of the task, both decided and
recorded at the point they came up rather than after the fact:

1. **Top-level acceptance vs. the issue's own acceptance.** A separate,
   spawner-provided acceptance block named
   `python3 watchdog.py --once --repo <path> ...` and a
   `docs/issue-3081/reports/*/[a-z]*.md` grep pattern.
   derived: `grep -n -- "--once" watchdog.py spawn.py` — result: no match
   — no `--once`/`--repo` CLI surface exists in either file;
   `requirement_drift` is invoked as a library function from
   `roster_watchdog()`'s tick loop, not a standalone CLI mode. Building
   that surface was not requested by the issue's own Acceptance section
   (3rd comment) and would be new, unrequested scope, so it was not built.
   The glob path also does not match this repo's actual
   `docs/issue-3081/reports/<name>.md` layout (no subdirectory under
   `reports/`)
   derived: `git ls-files docs/issue-3081/` — result: one file directly
   under `reports/`, no subdirectory — read as boilerplate from the
   spawning template, not an issue-specific requirement, and not pursued.
2. **`pytest tests/ -q -x` does not reach a clean pass, independent of
   this change.** derived: `git worktree add /tmp/main-check origin/main
   --detach && cd /tmp/main-check && python3 -m pytest
   tests/test_respawn_deliverable_gate.py -q` — result: `4 failed, 9
   passed` on a pristine `origin/main` (`573e7382`) checkout with zero
   modifications, before this session touched anything.
   derived: `python3 -m pytest
   tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
   -q` (same pristine checkout) — result: `1 failed`,
   `AssertionError: 5 not greater than 5` — this test compares `hooks.json`
   at `origin/main` against the working tree and asserts the PostToolUse
   command count is strictly greater; since `origin/main` IS the base ref
   in this checkout, comparing it against itself with zero hooks.json
   changes fails this assertion by construction, in any session that does
   not add a new hooks.json entry. Both are unrelated to requirement-drift
   or the repo-attribution fix.
   derived: `python3 -m pytest tests/ -q --deselect
   tests/test_respawn_deliverable_gate.py --deselect
   tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present`
   — result (mid-session): `179 passed`. derived: `python3 -m pytest
   tests/ -q` (unfiltered, full run, no `-x`, after the bidirectional-leak
   extension) — result: `5 failed, 189 passed` — the same 5 pre-existing
   cases (4 in `test_respawn_deliverable_gate.py` + 1 in
   `test_spawn_gate_wiring.py` above) and no new failures, confirming this
   change introduces no regressions beyond baseline.
