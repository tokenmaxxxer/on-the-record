---
issue: 2326
role: adversarial-review-941d677c
author: adversarial-review-941d677c
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: PR #2855 (branch issue-2326/diagnose-first-4658f30a, head d81146222a90804e39e730c5d08e62c47a171ab1)
type: verification
breaking: false
verdict: partial — measurement instrument and hook mechanics are sound and fail-open as claimed, but the materiality verdict and the hook's practical value are not supported once the corpus is restricted to sessions the hook could actually run in, and the impacted-test heuristic misses the real production files behind the one clean rework episode traced
loop_state: landed
upstream:
  - path: docs/issue-2326/reports/diagnose-first-4658f30a.md
    sha: 399f6afce85f9ec26a4010f4fd365b2b2724379b
  - path: on-the-record/hooks/lint-test-on-edit.sh
    sha: d81146222a90804e39e730c5d08e62c47a171ab1
  - path: scripts/rework_fraction.py
    sha: d81146222a90804e39e730c5d08e62c47a171ab1
  - path: tests/test_spawn_gate_wiring.py
    sha: d81146222a90804e39e730c5d08e62c47a171ab1
---

# issue-2326 — adversarial-review-941d677c record

skill-verdict: adversarial-review — applied: invoked; this session's own structural position (independently spawned verifier, fresh context, no shared session with the builder) already instantiates the skill's two-party protocol — I re-derived every number from raw session logs and re-ran the hook/tests myself rather than trusting PR #2855's or its record's own citations
skill-verdict: work-in-english — applied: invoked; this record, all derived commands, and commit/PR text are in English; final chat summary to the user will be in Korean

## What was done

Independently re-derived, rather than restated, the three claims PR #2855 makes:
canonical: `gh pr view 2855 --repo tokenmaxxxer/on-the-record` body, read directly by this session

**1. Test-selection accuracy (the hardest question) — fails on the one clean episode traced.**
Restricting the measurement corpus to sessions where `lint-test-on-edit.sh` could actually run — it
ships in `on-the-record/hooks/hooks.json`, a different plugin from `tokenmaxxxer-core`'s own
`core/hooks/`, so it is never wired into `tokenmaxxxer-core-*` sessions regardless of what file they
edit —
canonical: `printenv | grep -iE "ON_THE_RECORD|CLAUDE_PLUGIN"` (this session's own environment) and `find "$CLAUDE_PLUGIN_ROOT_CORE" -maxdepth 2`, both read directly by this session; `ON_THE_RECORD=/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer`, `CLAUDE_PLUGIN_ROOT_CORE=/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core` — two separate plugin roots, each with its own `hooks/` directory
, I traced `on-the-record-issue-2795-silent-failure-audit-3da5ceae`'s rework episode (turn-cost 35,
the one genuine code-editing episode in a real on-the-record session — see corpus split in finding 5
below): the edits inside the episode window are `board.py`, `spawn.py`, `watchdog.py` (multiple edits
each), and the failing test-stage calls are whole-suite (`python3 -m pytest test/ -q`) and multi-file
(`test/test_convention_equivalence.py test/test_local_dependency_env.py
test/test_spawn_cross_family_skill_selection.py ...`) runs, never a single 1:1-stem file.
derived: trajectory dump of `tool_use`/`tool_result` events for that session's log, produced by this session's own one-off script against `trajectory_analyzer.parse_session_log`, output pasted below
```
[22] EDIT board.py   [25] EDIT board.py   [29] EDIT spawn.py
[32,33,36,39] EDIT watchdog.py   [59] EDIT spawn.py  [60] EDIT board.py  [61] EDIT watchdog.py
[67] TEST pytest outcome=pass  test/test_unrecovered_commit_count.py
[69] TEST pytest outcome=fail  timeout 580 python3 -m pytest test/ -q
[72] TEST pytest outcome=fail  test/test_convention_equivalence.py test/test_local_dependency_env.py test/test_spawn_cross_family_skill_selection.py test/test_sp...
[88] TEST pytest outcome=fail  full suite AFTER (this branch)
```
Checked whether the hook's 1:1-stem heuristic (`test/test_<stem>.py` / `tests/test_<stem>.py` for the
edited file's basename) would find any test for these three real, frequently-edited production files:
derived: `ls test/test_watchdog.py tests/test_watchdog.py test/test_board.py tests/test_board.py test/test_spawn.py tests/test_spawn.py 2>&1` — all six paths return "그런 파일이나 디렉터리가 없습니다" (no such file, 0 of 6 exist); `git ls-files "test*/test_*.py" | grep -iE "spawn|board|watchdog"` returns only multi-word descriptive names (`test_board_bracket_provenance.py`, `test_spawn_artifact_skill_pairing.py`, `test_spawn_cross_family_skill_selection.py`, etc.), none matching the stem pattern
. Zero of three. This repo's actual test-naming convention is descriptive multi-word filenames, not
1:1 stem matches — so for the one real code-editing rework episode this session could trace end to
end, the hook would have run lint only (`py_compile`, ~50ms) and silently skipped the test step,
producing no signal about the failure that actually happened. The 330-350ms "lint+impacted test" cost
the record advertises never fires for this episode's files at all.

**2. Overhead — docs-only and lint-only confirmed; "lint+impacted test" not reproducible at the
claimed number.** Re-ran the shipped hook directly, 5x per path, on the committed PR branch
(materialized untracked into `/tmp/wt-pr2` via `git worktree add /tmp/wt-pr2 pr-2855-review`, PR #2855
head d81146222a90804e39e730c5d08e62c47a171ab1):
derived: `for i in 1 2 3 4 5; do t0=$(date +%s%N); bash on-the-record/hooks/lint-test-on-edit.sh post < <payload>; t1=$(date +%s%N); echo $(( (t1-t0)/1000000 )) ms; done`, run inside `/tmp/wt-pr2` against synthetic PostToolUse JSON payloads written via the Write tool (`/tmp/docs_payload.json`, `/tmp/py_payload.json`, `/tmp/pytest_payload.json`)
```
docs-only:                 1-6 ms      (matches record's ~1.1-1.8ms)
non-docs, py_compile only: 45-66 ms    (matches record's ~49-57ms)
non-docs, impacted test:   1526-1611 ms  (record claims 329-349ms)
```
The third path used tests/test_spawn_gate_wiring.py (untracked in this branch's own working tree,
present in the `/tmp/wt-pr2` worktree at PR #2855 head) itself as the edited file — its own
`is_own_test` branch, so the hook runs `pytest tests/test_spawn_gate_wiring.py -q` directly (17 tests,
several of which shell out to the hook subprocess). Direct
`time python3 -m pytest tests/test_spawn_gate_wiring.py -q` confirms 1.22-1.52s standalone
derived: `time python3 -m pytest tests/test_spawn_gate_wiring.py -q` (inside `/tmp/wt-pr2`) — "17 passed in 1.22s", real 1.520s
, and a second, unrelated real test file (test/test_watchdog_heartbeat_noise.py) confirms its own
6-test suite runs standalone at
derived: `time python3 -m pytest test/test_watchdog_heartbeat_noise.py -q` — "6 passed in 0.86s", real 1.089s
0.84-1.09s. Two different real matched-test examples both land at ~0.9-1.6s, not 330-350ms. The record
does not name which file it timed for that number, so it is not reproducible against anything in this
repo — I could not find a test file in this corpus that runs in 330-350ms via `pytest`.

**2b. Break-even.** Across the on-the-record-only session set (finding 5's corpus), edit calls split
into docs-shaped and non-docs:
derived: one-off script counting `Edit`/`Write`/`MultiEdit` tool_use calls by file-path shape over `/tmp/otr_only/*.session.*.log` — "total edit calls: 134 docs-shaped: 98 non-docs: 36"
So per-session overhead at the measured lint-only rate (finding 2's "45-66 ms" fence) is roughly
3.6 non-docs edits/session × ~55ms ≈ 200ms/session, negligible on its own. The expensive path
(0.86-1.6s, finding 2's "1526-1611 ms" fence) only matters if it actually fires, and finding 1 shows
it does not fire for the real production files behind the one traced episode — so on the evidence
gathered here the realistic catch-rate for the expensive path is close to zero, not "every non-docs
edit." Converting the benefit side (median 14-41 turns saved per prevented episode, per finding 5's
`on-the-record`-only vs. record's full-corpus numbers) into a comparable wall-clock figure requires an
assumed seconds-per-turn constant that nothing in this corpus establishes — a turn can be a sub-second
grep or a multi-minute build — so a literal "N edits per prevented episode" crossover point depends on
a number nobody has, exactly as the task anticipated. What the evidence does support without that
assumption: the overhead is small in the common case (docs-heavy sessions, lint-only on the rest) and
the benefit is smaller than claimed, because the mechanism that would deliver it rarely engages
(finding 1). Neither side of the trade is what the record's own framing implies.

**3. Fail-open — confirmed across the modes I could construct.**
derived: `printf 'not json{{{' | bash on-the-record/hooks/lint-test-on-edit.sh post; echo rc=$?` → rc=0; `printf '' | bash on-the-record/hooks/lint-test-on-edit.sh post; echo rc=$?` → rc=0; `env -i PATH="" $(command -v bash) on-the-record/hooks/lint-test-on-edit.sh post < /tmp/py_payload.json; echo rc=$?` (python3 unresolvable) → rc=0; `env OTR_LINT_TEST_BUDGET_S=0 bash on-the-record/hooks/lint-test-on-edit.sh post < /tmp/py_payload.json; echo rc=$?` → rc=0, emits "budget exceeded (0s)" context instead of hanging
. Malformed JSON, empty stdin, an unresolvable `python3`, and a zero budget all exit 0 — the edit
proceeds in every case I could construct. This claim holds.

**4. The exclusion filter (33→17 sessions) — the filter's own stated reason does not match what is
actually in the data, though the exclusion itself was not what manufactured the "material" verdict.**
Re-ran the corpus rollup myself against the live log set (34 files now, one more than the record's 33
— the corpus is a moving target, not a frozen snapshot; expect drift, not exact reproduction):
derived: `python3 scripts/rework_fraction.py --batch "$MUSTER_WORKSPACE_ROOT/*.session.*.log"` (unfiltered, 34 sessions) → "total test-stage calls: 115 (fail=68, fail_fraction=59.1%) ... rework_fraction_of_edit_turns: 12.2%"; same command with `adversarial-review`-substring files excluded (17 remain) → "total test-stage calls: 77 (fail=36, fail_fraction=46.8%) ... rework_fraction_of_edit_turns: 9.8%"
. Both directionally match the record's 61.0%/42.9%/10.8% (unfiltered) and 49.3%/26.9%/7.9% (filtered)
figures — the filter reduces the signal, it does not inflate it, so it is not "the filter that
produced the material verdict": the unfiltered number is already at least as material.

But the record's stated reason for the exclusion ("adversarial-review-family sessions deliberately
run pytest twice, main vs PR branch, and score every comparison re-run as a rework episode") does not
match what I found on inspection. I traced every excluded session with rework episodes
(`tokenmaxxxer-core-*-adversarial-review-*`) — 13 such sessions
derived: count of `adversarial-review`-family log filenames with `rework_episodes_count > 0`, from this session's own per-session `analyze_session()` dump over all 17 excluded logs — 13 sessions listed, 12 of them show `fail_fraction: 1.0` / `test_stage_pass: 0`
— and 12 of those 13 have `fail_fraction: 1.0` / `test_stage_pass: 0`, i.e. the session never records a
single passing test-stage call, not "one pass, one fail" from a branch diff:
```
tokenmaxxxer-core-issue-233-secure-coding...+adversarial-review-8bab0cf8: fail_fraction=1.0 n_pass=0 rework_costs=[150,149,124,121] total_turns=185
tokenmaxxxer-core-issue-233-adversarial-review-a814c155: fail_fraction=1.0 n_pass=0 rework_costs=[106,84,83]
(11 more, same n_pass=0 shape)
```
`rework_fraction.py`'s episode boundary defaults to session end when no later passing test-stage call
exists, so `turn_cost = boundary - fail_i - 1` becomes "however many turns were left in the session,"
not a measured fix time — this is what produces the 150/149/124/121-turn outliers, not a diff-
comparison double-count. And this is not unique to the excluded family: the same `n_pass=0` /
boundary-defaults-to-end shape survives inside the retained 17-session corpus —
derived: same per-session dump, non-`adversarial-review` logs
```
tokenmaxxxer-core-issue-233-secure-coding-input-validation-injection-defense-bcd7fd6a: n_pass=0 rework_costs=[98,96,79,65]
tokenmaxxxer-core-issue-361-secure-coding-input-validation-injection-defense-a072264b: n_pass=0 rework_costs=[93,92,48,29]
```
— and the `[98,96,79,65]` session is the literal source of the "up to 98 in the worst family" figure
quoted in the diagnose-first-4658f30a.md record (untracked in this branch's working tree, present in
`/tmp/wt-pr2` at PR #2855 head) and repeated in lint-test-on-edit.sh's own header comment (same
worktree)
canonical: both files read directly by this session from `/tmp/wt-pr2`; cross-checked against the per-session dump immediately above showing the 98 originates from `tokenmaxxxer-core-issue-233-secure-coding-input-validation-injection-defense-bcd7fd6a`'s unresolved (`n_pass=0`) episode, not a resolved fix
. That number is an artifact of the same unresolved-session-end default the record used to justify
excluding the other 17 sessions, not a measured worst-case fix time.

**5. Repo-scope mismatch — restricting to the sessions the hook can actually reach cuts the
headline number roughly in half.** Of the 17 sessions in the record's own filtered corpus, 7
(`tokenmaxxxer-core-issue-233-*`, `tokenmaxxxer-core-issue-361-*`) are `tokenmaxxxer-core` sessions —
a different repo/plugin than `on-the-record`, where this hook is not installed (see plugin-root
citation in finding 1). Restricting the batch to only the 10 `on-the-record-*` sessions — the entire
population the shipped hook can ever run against —
derived: `python3 scripts/rework_fraction.py --batch "/tmp/otr_only/*.session.*.log"` (10 files, symlinked by excluding both `adversarial-review`-substring and non-`on-the-record-`-prefixed logs from the live 34-file set)
```
total test-stage calls: 57 (fail=19, fail_fraction=33.3%)
total edit calls: 133   total rework episodes: 6
rework_fraction_of_edit_turns: 4.5%   (record's headline: 7.9%)
rework turn-cost: median=14.0 mean=19.00   (record's headline: median=41 mean=54.6)
```
Of those 6 remaining episodes, one (`on-the-record-issue-2324-independent-verification-1`, cost 13)
resolves via edits to an uncommitted, untracked report draft under docs/issue-2324/reports/ (a live
session artifact, never landed to git history) and other `/tmp` report drafts — the docs-only fast
path the hook explicitly skips before spawning any subprocess, so a perfect hook would not have
engaged for this "rework" instance either.
derived: trajectory dump for that session's log (`on-the-record-issue-2324-independent-verification-1.session.20260830T142219.670326.log`, read directly under `$MUSTER_WORKSPACE_ROOT`) — edits between the failing `pytest test/ tests/ -q` call and session end are three writes to the report path above plus `/tmp/record_draft/draft.md` and `/tmp/pr2324_verification_body.md` — no source-code edit in the window
Three more of the 6 (`on-the-record-issue-2326-diagnose-first-4658f30a`, PR #2855's own build session)
are the builder debugging its own new test file plus `git stash`-based before/after baseline diffs —
the same diff-comparison shape the record used to exclude the `adversarial-review` family, present
unflagged inside its own build session's contribution to the corpus.

**6. Standing invariants.**
- No role-axis return: restricted the diff to the actual shipped/behavioral files —
  derived: `git diff $(git merge-base origin/main HEAD)..HEAD -- on-the-record/hooks/lint-test-on-edit.sh tests/test_spawn_gate_wiring.py docs/specs/enforcement-boundary.md on-the-record/hooks/hooks.json` (run inside `/tmp/wt-pr2`) — added `role` hits are exactly 3: the hook's own comment block ("No role-axis: this hook keys nothing on a role/skill identity..."), and the `enforcement-boundary.md` row's matching prose. No executable branch keys on role/skill identity. I read the task's framing the same way: compliant.
- No new bug: clean-worktree A/B (`git worktree add /tmp/wt-main origin/main`, `/tmp/wt-pr pr-2855-review`) —
  derived: `python3 -m pytest test/ tests/ -q 2>&1 | grep '^FAILED' | sort` in each worktree — both produced the identical 15-line `FAILED` name set (`diff /tmp/before_fail2.txt /tmp/after_fail2.txt` → empty)
  . Confirmed as a set of names, not just a count.
- No overhead increase: docs-only and lint-only confirmed cheap
  derived: see the "docs-only: 1-6 ms" and "py_compile only: 45-66 ms" fence in finding 2 above
  ; "lint+impacted test" is real but measured at 0.86-1.6s where it actually fires (same fence), not
  330-350ms, and per findings 1 and 5 above it fires on close to none of the real production files
  this corpus's genuine rework episodes touch.
- Monitor/watch unbroken and not quieter: same clean-worktree A/B —
  derived: `python3 -m pytest test/test_watchdog_heartbeat_noise.py -q` → "6 passed in 0.84s" (main) vs "6 passed in 0.86s" (PR); `python3 -m pytest test/ tests/ -q -k "monitor or watch"` → "15 passed" both worktrees, identical
  .
- Acceptance gate re-run independently:
  derived: `python3 -m pytest tests/test_spawn_gate_wiring.py -q` inside `/tmp/wt-pr2` → "17 passed in 1.19s"
  .

## Why

The task named three hard questions in priority order and one methodology check. I traced each to
concrete session-log evidence rather than re-deriving abstract percentages, because the record's own
central claim — 7.9% rework, material, build it — turns on whether the built mechanism actually
reaches the failures the measurement found. It largely doesn't: the mechanism can't run in 41% of the
material corpus's sessions (repo mismatch, finding 5), doesn't fire its test step on the real
production files behind the one traceable clean episode in the reachable population (naming-convention
mismatch, finding 1), and part of the corpus's own worst-case citation ("up to 98") turns out to be a
measurement-script artifact rather than a real fix-time outlier (finding 4).
canonical: findings 1, 4, and 5 above, each independently re-derived by this session this turn against live session logs and the PR branch's shipped code — not restated from the PR's own record
None of this makes the underlying diagnose-first process dishonest — the record is unusually
transparent about its own caveats (small n, single-day snapshot, two-family split) — but the gap
between "material by the numbers" and "the shipped mechanism addresses what the numbers found" is
large enough that the acceptance criterion the task set (would the hook, running at the edit that
caused each episode, have selected the test that later failed) fails on the one episode I could fully
trace end to end.

## What did not work

None — every re-derivation attempt succeeded (ran to completion, produced a usable comparison).
The `git checkout <ref> -- .` approach to A/B testing left a corrupted mixed index (partial-path
checkouts don't remove files absent from the target ref while present in the current index), so I
switched to `git worktree add` for all before/after comparisons; noted here since it changed the
method used partway through this session for the "no new bug" and "monitor/watch" invariant checks.

## Upstream basis

- docs/issue-2326/reports/diagnose-first-4658f30a.md (sha `399f6afce85f9ec26a4010f4fd365b2b2724379b`, untracked in this branch's working tree, present in `/tmp/wt-pr2` at PR #2855 head) — PR #2855's own record; every number in it was independently re-derived above rather than restated.
- on-the-record/hooks/lint-test-on-edit.sh, scripts/rework_fraction.py, tests/test_spawn_gate_wiring.py (all sha `d81146222a90804e39e730c5d08e62c47a171ab1`, PR #2855 head, untracked in this branch's own working tree) — read in full and executed directly from `/tmp/wt-pr2` (`git worktree add /tmp/wt-pr2 pr-2855-review`).
- Live session-log corpus at `$MUSTER_WORKSPACE_ROOT/*.session.*.log` (34 files at measurement time) — the same corpus class PR #2855 measured against, re-queried live rather than reusing its pasted output.

## Open findings

1. The impacted-test 1:1-stem heuristic misses this repo's actual test-naming convention
   (test_board_bracket_provenance.py-style descriptive names, not test_board.py) for at least the
   three production files (board.py, spawn.py, watchdog.py) behind the one clean on-the-record
   rework episode this session could trace end to end. Resolution path: none attempted here — this
   record is a verification, not a fix; a follow-up would need either a smarter impacted-test mapping
   (e.g. a committed file→test manifest) or an honest scope narrowing of what the hook claims to catch.
2. scripts/rework_fraction.py's episode-boundary-defaults-to-session-end behavior inflates
   rework_turn_cost for any session that ends without a later passing test-stage call, independent of
   whether the session belongs to the excluded adversarial-review family. This affects the "up to 98"
   citation still standing in diagnose-first-4658f30a.md (untracked in this branch's working tree,
   present in `/tmp/wt-pr2` at PR #2855 head)
   canonical: finding 4 above's per-session dump, produced and read directly by this session this turn, showing the 98 originates from an unresolved (`n_pass=0`) episode rather than a resolved fix
   . Resolution path: none attempted here (verification only) — a fix would cap or flag boundary-at-
   session-end episodes separately from resolved ones, the way the script already does for the "no
   re-entry" case.
3. 41% of the record's "material" 17-session corpus is tokenmaxxxer-core sessions the shipped hook
   cannot run against (different plugin/repo). Resolution path: none attempted here — re-stating the
   materiality claim against only the reachable population (finding 5 above: 4.5%/median 14, not
   7.9%/median 41) would be the honest correction, but that is a call for the issue's owner, not this
   verification.

## Next steps

loop_state: landed.
derived: this record's own re-derivations this turn — `python3 -m pytest tests/test_spawn_gate_wiring.py -q` (inside `/tmp/wt-pr2`) → "17 passed in 1.19s"; `python3 scripts/rework_fraction.py --batch ...` re-runs in findings 4 and 5 above; fail-open probes in finding 3 above — all executed live by this session, not restated from PR #2855's own record
This record's own scope (independent verification of PR #2855) is complete: every claim in the task's
four-part ask (test selection, overhead/break-even, fail-open, filter judgment) plus the four standing
invariants has been re-derived against live evidence and reported above. No further action by this
role; the open findings above are handed to the issue owner, not carried forward in this record.
