---
issue: 2393
role: conformance-review
author: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2393/reports/implementation.md
    sha: 512eec2c1179a572e5b8818a484894bbd3ce678e
  - path: docs/issue-2291/reports/conformance-review.md
    sha: 1addbe9eb492ccff43134673f50ae9dfbd1df894
subject: PR #2400 (issue-2393: skip pytest-origin spawn-attempt records, rotate + prune the trace)
test: independent re-execution of all four acceptance-bullet reproductions, this session, against a checked-out worktree of PR #2400
result: passed
assertedBy: conformance-review (builder-blind — no access to the builder session's own reasoning beyond the record and diff text)
---

# issue-2393 — conformance-review record

## What was done

Builder-blind conformance review of PR #2400 against issue #2393's four
acceptance bullets.

canonical: `gh pr view 2400`, `gh pr diff 2400` (this session) — PR body,
commits `f6487073` and `512eec2c`, and the full diff of
`512eec2c:docs/issue-2393/reports/implementation.md`, `spawn.py`,
`roster.py`, `docs/reports/deviation-log.md`, read in this session.

Rather than trusting the builder's own pasted output, this review checked
out the PR branch into an isolated worktree and independently re-ran every
claimed reproduction, capturing this session's own command output below.

canonical: `git fetch origin pull/2400/head:pr-2400 && git worktree add
/tmp/otr-pr2400-review pr-2400` (this session) — worktree at
`512eec2c1179a572e5b8818a484894bbd3ce678e`.

## Why

Builder-blind conformance review means checking the artifact against the
issue's stated acceptance criteria without assuming the builder's claimed
numbers are correct — independent re-execution, not re-paraphrase of the
record, is the check.

The PR body's own numbers (285 issue-cited vs. 341 actually pruned)
already diverge from the issue text for a stated reason (concurrent
sessions on a shared host file continuing to append while the fix was
built) — this was itself independently re-verified rather than taken on
faith (see Finding 4 below), not merely repeated from the record.

## Upstream basis

- `512eec2c:docs/issue-2393/reports/implementation.md` — the builder's own
  record of the fix, read in full this session. canonical: present on
  branch `pr-2400` (this session's `git worktree add`), not on this review
  branch's own `main` base — cited by commit sha, not by a bare path on
  this branch, per the pinned-citation convention.
- `1addbe9eb492ccff43134673f50ae9dfbd1df894:docs/issue-2291/reports/conformance-review.md`
  — source of R8, read this session for backward-trace before checking its
  resolution (see Finding 4).

## Findings

---
requirement: "spawn attempts originating from the test suite are either not
  recorded in `runs/spawn-attempts.jsonl` at all, or are recorded with a
  marker the watchdog uses to exclude them — decided and stated in the
  record which approach and why"
spec_ref: issue #2393 acceptance bullet 1
verdict: Present
evidence: |
  `512eec2c:spawn.py:901-922` (`_record_spawn_attempt()`), guard at
  `spawn.py:920-921`:
  ```
  if os.environ.get("PYTEST_CURRENT_TEST") is not None:
      return None
  ```
  Single caller confirmed this session:

  acceptance: `grep -rn "_record_spawn_attempt(" --include=*.py .` (in
  `/tmp/otr-pr2400-review`, this session) — result:
  ```
  roster.py:441:    `_record_spawn_attempt()`/`_record_spawn_outcome()` now append that
  spawn.py:901:def _record_spawn_attempt(issue: int | None, role: str, pid: int) -> str | None:
  spawn.py:1771:    attempt_id = (_record_spawn_attempt(a.issue, a.role, os.getpid())
  ```
  derived: one production call site (`spawn.py:1771`, inside `main()`),
  matching the record's own claim of a single caller.

  Decision (not-recorded-at-all, not a marker) and two rejected
  alternatives (marker+watchdog-filter, per-test-file isolation via
  `tests/_spawn_test_support.py`'s `isolated_role_model_config()`) are
  stated in `512eec2c:docs/issue-2393/reports/implementation.md`'s `## Why`
  section, read in full this session.
rationale: code implements "not recorded at all" exactly as decided, the
  sole caller null-guards the return, and the decision plus its rejected
  alternatives are stated in the record — satisfying the bullet's explicit
  "decided and stated" clause.
---

---
requirement: "after the fix, running the full test suite adds zero new
  `spawn halted pre-workspace` watchdog reports (measured before/after: run
  the suite, then a watchdog tick, and count)"
spec_ref: issue #2393 acceptance bullet 2
verdict: Present
evidence: |
  Independently reproduced in this session (not copied from the record),
  in `/tmp/otr-pr2400-review`.

  acceptance: BEFORE — `spawn.py`/`roster.py` reverted to commit
  `f6487073~1` = `ce7fadd7` (pre-fix), isolated
  `MUSTER_STATE_ROOT=/tmp/otr-2393-verify/isolated-state`:
  `python3 -m pytest tests/test_default_single_phase_flip.py
  tests/test_checkpoint_mode.py -q` then
  `python3 -c "import time,spawn,roster; print(roster.spawn_attempt_sweep(now=time.time()+400))"`
  — result:
  ```
  25 passed in 2.81s
  [spawn-attempt] issue-31/implementation: spawn halted pre-workspace: ...  (x5)
  [spawn-attempt] issue-7/implementation: spawn halted pre-workspace: ...  (x2)
  BEFORE-FIX simulated tick, reports: 7
  ```

  acceptance: AFTER — `spawn.py`/`roster.py` restored to `512eec2c`, fresh
  isolated state, identical two commands — result:
  ```
  25 passed in 2.46s
  wc: /tmp/otr-2393-verify/isolated-state/spawn-attempts.jsonl: no such file
  ```
  no `spawn-attempts.jsonl` was created at all post-fix, so the tick has
  nothing to report.

  derived: 7 (before) -> 0 (after) for the identical two test files and the
  real `roster.spawn_attempt_sweep()` function the watchdog tick calls.
rationale: this session's own before/after run reproduces the exact 7→0
  drop the bullet requires, against the real function, not a stand-in.
---

---
requirement: "a genuine pre-workspace halt (the case #2291 exists to catch)
  is still reported — demonstrate with a live forced halt, not by reading
  the code"
spec_ref: issue #2393 acceptance bullet 3
verdict: Present
evidence: |
  Independently forced in this session with a fresh issue number (999002,
  distinct from the record's own 999001) to rule out replaying a cached
  fixture.

  acceptance: `MUSTER_STATE_ROOT=/tmp/otr-2393-verify/isolated-state2
  python3 spawn.py implementation "test task" --issue 999002 -C
  /tmp/otr-2393-verify/no-board-repo --unattended` (real git repo with no
  `docs/specs/approvers.md`, `PYTEST_CURRENT_TEST` unset, spawn.py @
  `512eec2c`) — result:
  ```
  대상 레포에 docs/specs/approvers.md 가 없다: /tmp/otr-2393-verify/no-board-repo
    이 파일이 보드 opt-in 이자 승인자 allowlist 다. 만들려면:
      python3 spawn.py init -C /tmp/otr-2393-verify/no-board-repo
    보드를 안 쓸 작업이면 --no-contract 로 건너뛴다.
  ```
  acceptance: `cat` the resulting `spawn-attempts.jsonl` — result:
  ```
  {"event": "spawn_attempt", "attempt_id": "999002:implementation:978567:1787656009168", ...}
  {"event": "spawn_attempt_outcome", "attempt_id": "999002:implementation:978567:1787656009168", "outcome": "halted", ...}
  ```
  acceptance: `SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1 python3 spawn.py
  watchdog -C /tmp/otr-2393-verify/no-board-repo` (real watchdog CLI, same
  state root) — result:
  ```
  [spawn-attempt] issue-999002/implementation: spawn halted pre-workspace: 대상 레포에 docs/specs/approvers.md 가 없다: ...
  ```
  derived: a real, non-test halt run end-to-end (attempt → outcome →
  watchdog report) is still recorded and reported after the fix.
rationale: demonstration (not code-reading, per verification-method-selection
  rule 3 — a live forced halt) confirms the guard does not suppress genuine
  halts alongside test noise.
---

---
requirement: "the 285 existing junk records in `runs/spawn-attempts.jsonl`
  are pruned or the file is rotated, and whatever rotation/pruning policy
  is chosen is stated (this file has no rotation today — separately
  flagged as R8 Surface in #2291's own conformance review)"
spec_ref: issue #2393 acceptance bullet 4; backward-traced to R8.
  canonical: `1addbe9eb492ccff43134673f50ae9dfbd1df894:docs/issue-2291/reports/conformance-review.md:575-583`
  ("R8 `Surface`... `spawn-attempts.jsonl` has no pruning/rotation...
  Resolution path unchanged: prune once an entry's outcome has been swept
  and reported once, or cap/rotate the file"), read this session — R8's
  source line confirmed to exist before checking its resolution here.
verdict: Present
evidence: |
  (a) Historical prune — independently parsed the backup file this
  session:

  acceptance: `wc -l` + a `python3` tally of `event == "spawn_attempt"` by
  `issue` against
  `/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/spawn-attempts.jsonl.bak-issue-2393-20260825T094422Z`
  (this session) — result:
  ```
  341 lines total
  backup attempt counts by issue (top): [(31, 232), (7, 68), (2348, 6), ...]
  total attempt records in backup: 321
  ```
  derived: 232+68 = 300 dropped, matching the record's claimed
  "341 → drop 300 {31:232, 7:68} → kept 41" exactly.

  (b) Ongoing policy — `512eec2c:spawn.py:989-1039` (`_prune_spawn_attempts()`):
  unresolved attempts always kept, `"session-log"` outcomes dropped
  immediately, `"halted"` outcomes kept
  `SPAWN_ATTEMPTS_RETENTION_SEC = 7*24*3600` (matches
  `roster.APPROVAL_WAIT_LEDGER_TTL_SEC` —

  acceptance: `grep -n APPROVAL_WAIT_LEDGER_TTL_SEC roster.py` this session
  — result: `roster.py:509:APPROVAL_WAIT_LEDGER_TTL_SEC = 7 * 24 * 3600`

  ), wired at `512eec2c:roster.py:498` inside `spawn_attempt_sweep()`,
  called every tick — this is exactly R8's own stated resolution path
  ("prune once an entry's outcome has been swept and reported once").

  (c) Independently re-ran the prune-policy unit check with four synthetic
  events this session (not the builder's script, freshly written):

  acceptance: built one event of each case (unresolved/8-days-old,
  resolved-session-log/8-days-old, resolved-halted/1-day-old,
  resolved-halted/8-days-old) and called the real
  `spawn._prune_spawn_attempts(now=now)` — result:
  ```
  dropped: 4
  remaining ids: ['a1', 'a3']
  OK
  ```
  derived: `a1` (unresolved) and `a3` (halted, recent) survive, `a2`
  (session-log) and `a4` (halted, 8 days old) are dropped — matches the
  expected policy exactly.
rationale: both the one-time historical prune and the ongoing rotation
  policy are independently confirmed working as stated, and the policy
  choice is stated in the record with reasoning tied to
  `spawn_attempt_sweep()`'s own reporting rules — satisfying both the
  "pruned or rotated" clause and the "policy stated" clause.
---

## Open findings

- The canonical shared `runs/spawn-attempts.jsonl`
  (`/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/spawn-attempts.jsonl`,
  outside this repo checkout) had grown back up by the time of this
  review.

  acceptance: `python3` tally of `spawn_attempt` events by `issue` against
  the live file (this session) — result:
  ```
  total attempts: 327
  by issue: [(31, 210), (7, 86), (2348, 7), (2383, 6), (2395, 4), ...]
  unresolved by issue: [(31, 210), (7, 86), (2395, 1)]
  ```
  derived: 210 issue-31 + 86 issue-7 = 296 unresolved records
  re-accumulated since the 09:44:22Z historical prune (341 → 41). Confirmed
  this is expected, not a regression in the PR: this review branch does
  not carry the fix.

  acceptance: `grep -c PYTEST_CURRENT_TEST spawn.py` on branch
  `issue-2393/conformance-review` (this checkout, not `pr-2400`) — result:
  `0`.

  derived: PR #2400 is unmerged, so other concurrent sessions on this host
  still run the pre-fix `spawn.py` against the same shared file — not a
  defect in the PR itself. Resolution path: re-run this same tally after
  #2400 merges (command above); not independently re-verifiable
  pre-merge, so left open rather than downgrading any of the four bullets'
  own verdicts, none of which depend on this.
- R7 (`1addbe9eb492ccff43134673f50ae9dfbd1df894:docs/issue-2291/reports/conformance-review.md`
  — ad-hoc, `--issue`-less spawns get no durable trace) remains open,
  correctly out of scope for #2393 per the builder's own record; not
  re-verified here as it is not one of #2393's acceptance bullets.
- None of the four acceptance bullets produced a Surface, Absent,
  Incorrect, or Unverifiable verdict — no disputed findings to resolve.

## Next steps

None — `loop_state: reported` (terminal for conformance-review).

acceptance: four independent re-executions this session (full transcripts
in the Findings section above) — result:
```
bullet 1: grep confirms single caller + guard present -> Present
bullet 2: pytest 25 passed; simulated tick 7 (before) -> 0 (after) -> Present
bullet 3: forced halt issue 999002 recorded + watchdog CLI reported it -> Present
bullet 4: backup tally 300 dropped matches record; unit check dropped=4 remaining=['a1','a3'] -> Present
overall: passed
```

## skill-verdict

skill-verdict: conformance-review-verification-method-selection — applied: invoked;
used Test/Demonstration (independent re-execution, this session's
own commands) for bullets 2-4 per rule 4 (reused the existing reproduction
shape rather than a fresh derivation) and rule 3 (bullet 3 is a
qualitative functional claim, exercised live with a fresh issue number);
did not re-verify the warrant-hunt's stale-env-var-propagation Analysis
independently (condition not reproducible in this review session; treated
as Analysis-appropriate per rule 2, not re-derived).
skill-verdict: conformance-review-verdict-assignment — applied: invoked;
assigned Present to all four bullets only after independent re-derivation
of each (rule 1 — checked the guard fires on the stated condition, not
just that matching code exists); backward-traced R8 to its source record
before checking its resolution (rule 3-adjacent, shared with the
traceability skill).
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked;
every evidence line cites file:line-range plus commit sha
(`512eec2c`/`f6487073`/`1addbe9e`); R8 backward-traced to its source line
(`docs/issue-2291/reports/conformance-review.md:575-583`) before verifying
its resolution, per rule 3.
skill-verdict: conformance-review-finding-record — applied: invoked; wrote
one `---`-delimited block per acceptance bullet with requirement, spec_ref,
verdict, evidence, rationale fields; no Incorrect verdicts, so no
spec_vs_built field was needed.
skill-verdict: conformance-review-requirement-extraction — not-applicable:
issue #2393's four acceptance bullets were already discrete and
individually checkable as written; no bundled-obligation splitting needed.
skill-verdict: conformance-review-sampling-derivation — not-applicable:
scope was four acceptance bullets plus two small changed files
(`spawn.py`, `roster.py`), fully enumerable without sampling.
skill-verdict: conformance-review-severity-classification — not-applicable:
no findings were recorded (all four bullets Present), so there is nothing
to risk-weight.
other mounted skills: not triggered — no LLM/Claude-API surface, no chart
work, no settings/keybinding changes in scope.
