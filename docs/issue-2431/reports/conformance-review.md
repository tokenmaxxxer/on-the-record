---
issue: 2431
role: conformance-review
author: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2431/reports/implementation.md
    sha: 6531f56fde8d5ea9199819c4d6f97227232d405f
subject: PR #2434 (issue-2431/implementation, head 6531f56fde8d5ea9199819c4d6f97227232d405f, base c5851224 = the merged #2413 fix this PR corrects) — spawn.py, tests/test_watch_hardening.py, docs/reports/product/quality-bar.md
test: issue #2431 Acceptance section, five bulleted checks
result: passed
assertedBy: conformance-review session for issue-2431, builder-blind review of PR #2434, 2026-08-25 — CORE_BUILD_NOW=1 build-now bypass, delivered directly
---

# issue-2431 — conformance-review record

## What was done

canonical: `gh issue view 2431`, `gh pr view 2434`, `gh pr diff 2434`,
`gh api repos/tokenmaxxxer/on-the-record/issues/2431/comments` (all run
this session) — first reads before any check began.

Builder-blind conformance review of PR #2434
(`https://github.com/tokenmaxxxer/on-the-record/pull/2434`, branch
`issue-2431/implementation`, head `6531f56fde8d5ea9199819c4d6f97227232d405f`)
against issue #2431's five acceptance checks. Did not trust
`6531f56f:docs/issue-2431/reports/implementation.md`'s own claimed
transcripts (that path is not reachable on this review branch — it
lives on `issue-2431/implementation`, cited here pinned to that
commit): checked out the PR head into its own worktree
(`/tmp/pr-2434-review`) and, separately, the PR's base commit
`c5851224` (the merged #2413 fix this PR corrects) into a second
worktree (`/tmp/old-2413-review`), then ran the real
`spawn._prune_spawn_attempts()` / `roster.spawn_attempt_sweep()`
functions myself against a byte-identical copy of the real pre-fix
backlog the builder backed up to
`/tmp/spawn-attempts.jsonl.backup-issue2431` (203 lines, verified
independently this session to be 199 no-outcome dead-pid-shaped
orphans, ages 1.84h-3.81h — same shape the issue describes), and wrote
my own from-scratch fixtures (own long-lived process pid via
same-process `os.getpid()`, own halted-record ages) to independently
probe the live-pid-never-pruned invariant and the untouched-halted-
branch claim, rather than reading the builder's own transcripts for
those. All five checks below are backed by evidence this session
generated itself this turn — full transcripts under "## Findings".

Skills invoked this session (skill-repository issue #1955/#1758
mapping): conformance-review-requirement-extraction,
conformance-review-verification-method-selection,
conformance-review-verdict-assignment,
conformance-review-traceability-and-evidence,
conformance-review-finding-record,
defect-verification-independence-from-upstream-verdicts (cross-family,
skill-repository issue #2001). See "## Skill verdicts" at the bottom.

## Why

canonical: this session's own worktree checkouts and
python3/pytest invocations, transcripts quoted under "## Findings"
below.

Chose independent re-derivation over trusting the implementation
record's transcripts because the role is explicitly builder-blind, and
because this exact issue exists *because* #2413's own two verification
rounds tested only simulated ages and missed the real backlog's actual
shape — the precedent this issue is filed over is "prior verification
looked rigorous but tested the wrong condition." Concretely: ran the
unfixed (`c5851224`) and fixed (`6531f56f`) code against the same real
backlog copy myself rather than accepting the PR's own before/after
numbers; built a fresh live-pid fixture from a live, same-process pid
rather than reusing the builder's; and re-ran the two-tick watchdog
demonstration from a clean copy of the backlog rather than reading the
builder's transcript of it. Full commands and outputs are the
`canonical:`/`derived:` tags under each finding below.

## Upstream basis

canonical: `git show c5851224:docs/issue-2413/reports/implementation.md`,
`gh api repos/tokenmaxxxer/on-the-record/issues/2431/comments`, and
`gh pr diff 2434` (all run this session).

- `6531f56f:docs/issue-2431/reports/implementation.md` (implementation
  record) — the delivered work under review. Not present on this
  review branch (`issue-2431/conformance-review`); read via
  `git show 6531f56f:docs/issue-2431/reports/implementation.md` and
  `gh pr diff 2434` this session.
- PR #2434, `https://github.com/tokenmaxxxer/on-the-record/pull/2434`,
  head `6531f56fde8d5ea9199819c4d6f97227232d405f`, base `c5851224`
  (the merged #2413 fix; `on-the-record` `main` tip at review time) —
  canonical: `gh pr view 2434`/`gh pr diff 2434`, this session.
- Issue #2431 — canonical: `gh issue view 2431`, this session.
- `docs/issue-2413/reports/implementation.md` @ `c5851224` — the fix
  this issue corrects. canonical: `git show
  c5851224:docs/issue-2413/reports/implementation.md`, this session —
  confirms #2413 reused the halted branch's 7-day
  `SPAWN_ATTEMPTS_RETENTION_SEC` for the dead-pid case.
- issuecomment-5410865516 / issuecomment-5411038089 (issue #2431) —
  canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/2431/comments`,
  this session — both verified real, both dated 2026-08-25. The
  delivered design (no calendar bound at all once a pid is confirmed
  dead; the halted branch's 7-day window stays untouched) is built on
  this guidance.

## Findings

Five requirement blocks, one per issue #2431 acceptance bullet.
Bullet 2 bundles two independently checkable clauses (the reasoning
being stated, and the live-in-flight-never-pruned invariant) and is
split per conformance-review-requirement-extraction rule 1.

---
requirement: "A1 — dead-pid, no-outcome records are pruned without waiting for the 7-day retention window: a separate, shorter bound distinct from the halted-outcome branch's 7-day grace period" [dimension: functional behavior]
spec_ref: issue #2431, Acceptance bullet 1
verdict: Present
evidence: |
  6531f56f:spawn.py:506-514 (`_prune_spawn_attempts`, `outcome is
  None` branch: `if _pid_is_alive(pid): keep_ids.add(aid)` — no age/`ts`
  read at all for this branch any more), versus the unchanged `elif
  outcome.get("outcome") == "halted":` branch a few lines below, which
  still checks `SPAWN_ATTEMPTS_RETENTION_SEC`.

  canonical: `diff <(git show c5851224:spawn.py | sed -n
  '/elif outcome.get("outcome") == "halted":/,/^$/p') <(git show
  6531f56f:spawn.py | sed -n '/elif outcome.get("outcome") ==
  "halted":/,/^$/p')` (this session) — empty diff, confirming the two
  branches are now structurally distinct (dead-pid: liveness only, no
  bound; halted: liveness irrelevant, `SPAWN_ATTEMPTS_RETENTION_SEC`
  bound retained unchanged).

  derived: independent live-backlog run, this session, full transcript
  under A3 below:
  ```
  dropped (old #2413 code): 0
  dropped (new #2431 code): 199
  ```
  — same 199-record input, unfixed code drops none on the first pass,
  fixed code drops all of them on the first pass, no waiting period.
rationale: Code inspection shows the dead-pid branch dropped its age check entirely (bound = immediate, the strictest possible "shorter than 7 days") while the halted branch's bound is byte-identical to before; the live-backlog re-run independently confirms the practical effect.
---
requirement: "A2a — the reasoning for the chosen bound is stated" [dimension: functional behavior]
spec_ref: issue #2431, Acceptance bullet 2, clause 1
verdict: Present
evidence: |
  6531f56f:spawn.py:480-505 (Korean in-code comment: 7-day halted
  window exists so the orchestrator can notice-and-act on a genuine
  unresolved halt; a dead pid has nothing left to notice-and-act on,
  so waiting is pure cost; only the liveness-probe's own ambiguous-
  `OSError` case should ever be time-bounded, and that's already
  handled elsewhere as "treat as alive").
  6531f56f:docs/issue-2431/reports/implementation.md "Why" section
  (same reasoning, in English, with citations to the two operator
  comments).
  6531f56f:tests/test_watch_hardening.py:522-547 (class docstring,
  same reasoning restated for test readers).
  6531f56f:docs/reports/product/quality-bar.md +16 lines (generalized
  design principle: a calendar bound is only justified while the
  outcome it guards against is still genuinely uncertain).

  canonical: `git show 6531f56f:spawn.py`, `git show
  6531f56f:docs/reports/product/quality-bar.md`, `git show
  6531f56f:tests/test_watch_hardening.py` (all read this session).
rationale: The reasoning is stated at four independent altitudes (code comment, implementation record, test docstring, cross-cutting quality-bar entry), not just asserted once — and traces to the real operator guidance verified below.
---
requirement: "A2b — a genuine in-flight attempt is never pruned (pid still alive, at any age): the new bound applies only once liveness is already confirmed negative" [dimension: edge case / invariant; verification method: independent Demonstration, per defect-verification-independence-from-upstream-verdicts rule 2]
spec_ref: issue #2431, Acceptance bullet 2, clause 2
verdict: Present
evidence: |
  6531f56f:spawn.py:511 (`if _pid_is_alive(pid): keep_ids.add(aid)` —
  the only path to `keep_ids` for this branch; unconditional on age).

  derived: independent from-scratch fixture, this session, not reusing
  the builder's own live-pid demo — a record whose pid is this
  session's own live `os.getpid()` (checked from inside the same
  process that also calls the prune function, so the pid is
  provably alive at check time) and whose `ts` is set 10 years in the
  past:
  ```
  $ cd /tmp/pr-2434-review && MUSTER_STATE_ROOT=/tmp/review-2431-livepid2/runs python3 -c "
  import json, os, time, spawn
  now = time.time()
  rec = {'event':'spawn_attempt','attempt_id':'live1','issue':1,'role':'implementation','pid': os.getpid(), 'ts': now - 10*365*24*3600}
  with open(spawn.SPAWN_ATTEMPTS_PATH,'w') as f:
      f.write(json.dumps(rec)+'\n')
  print('dropped:', spawn._prune_spawn_attempts())
  "
  dropped: 0
  ```
  Record survived, at 10 years of age, solely because the pid is
  alive. (First attempt at this fixture, writing the pid in a
  short-lived helper process and checking liveness from a separate
  process, produced `dropped: 1` — a false failure caused by the
  helper process itself having already exited, not a defect in the
  fix; corrected by checking liveness from inside the same live
  process, per this skill's rule 7 — recorded here rather than
  silently discarded.)

  Existing repo test `test_live_pid_survives_regardless_of_age`
  (unmodified by this PR) independently covers the same invariant and
  passes — canonical: `python3 -m pytest
  tests/test_watch_hardening.py::SpawnAttemptPruneLiveness -v` this
  session, `test_live_pid_survives_regardless_of_age PASSED`.
rationale: An independently-built fixture (not the builder's), using the reviewer's own live process rather than a reused pid, confirms the never-prune-a-live-pid invariant holds regardless of age; the one false-start attempt is recorded rather than hidden.
---
requirement: "A3 — live demonstration against the REAL current backlog (not a simulated age): before some N, after near-zero" [dimension: functional behavior; verification method: Demonstration]
spec_ref: issue #2431, Acceptance bullet 3
verdict: Present
evidence: |
  Independently reproduced against a byte-identical copy of the real
  pre-fix backlog the builder preserved at
  `/tmp/spawn-attempts.jsonl.backup-issue2431` (203 lines; verified
  this session as 199 no-outcome ids, ages 1.84h-3.81h — matches the
  issue's description of the actual backlog shape, distinct from
  #2413's own simulated-age verification gap).

  canonical, before (unfixed code — PR's base commit `c5851224`, the
  merged #2413 fix, run this session in its own worktree
  `/tmp/old-2413-review`):
  ```
  $ cd /tmp/old-2413-review && MUSTER_STATE_ROOT=/tmp/review-2431-old2/runs python3 -c "import spawn; print('dropped (old #2413 code):', spawn._prune_spawn_attempts())"
  dropped (old #2413 code): 0
  $ wc -l /tmp/review-2431-old2/runs/spawn-attempts.jsonl
  203
  ```
  canonical, after (fixed code — PR head `6531f56f`, run this session
  in its own worktree `/tmp/pr-2434-review`, against a fresh copy of
  the same backup):
  ```
  $ cd /tmp/pr-2434-review && MUSTER_STATE_ROOT=/tmp/review-2431-new/runs python3 -c "import spawn; print('dropped:', spawn._prune_spawn_attempts())"
  dropped: 199
  $ wc -l /tmp/review-2431-new/runs/spawn-attempts.jsonl
  4
  $ python3 -c "import spawn; print('dropped2:', spawn._prune_spawn_attempts())"   # idempotency
  dropped2: 0
  ```
  All 199 (derived: `dropped: 199`, transcript above) outstanding
  dead-pid orphans were dropped — not merely "near-zero," the
  no-outcome category is empty — idempotent on re-run (`dropped2: 0`,
  derived: transcript above), and the 4 (derived: `wc -l` = 4,
  transcript above) remaining lines are the pre-existing real `halted`
  records this fix leaves untouched (see A5).

  Note: the issue was filed against 434 outstanding orphans; by this
  review the same live sibling workspace's backlog had grown/decayed
  to 199 — canonical: `wc -l
  /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2395-implementation/runs/spawn-attempts.jsonl`
  and the backup file above, both read this session (natural drift
  between filing and fix, not a discrepancy — the issue's own
  acceptance bullet anticipates this: "434 ... or however many remain
  by then").
rationale: Independently re-run (not read from the builder's transcript) against the same real, not-simulated backlog, with a separately-checked-out pre-fix baseline confirming the "before" count and a fresh post-fix run confirming both the drop-to-zero and idempotency.
---
requirement: "A4 — the watchdog stops re-emitting these specific historical pids within one tick after the fix lands, not within a week — demonstrated, not asserted" [dimension: functional behavior; verification method: Demonstration]
spec_ref: issue #2431, Acceptance bullet 4
verdict: Present
evidence: |
  6531f56f:roster.py:435-511 (`spawn_attempt_sweep`) — structurally
  confirmed this session (read directly, not from the implementation
  record — canonical: `sed -n '435,511p' roster.py` this session) that
  the report loop runs first and `_sp._prune_spawn_attempts(now=now)`
  is called once at the end of the same function call, so the tick
  that reports a dead-pid record also prunes it before returning.

  canonical, independent two-tick run against a fresh copy of the same
  real backup (this session, `/tmp/pr-2434-review`):
  ```
  $ cd /tmp/pr-2434-review && MUSTER_STATE_ROOT=/tmp/review-2431-ticks/runs python3 -c "
  import spawn, roster
  n1 = roster.spawn_attempt_sweep(); print('tick1 reported:', n1)
  print('lines remaining after tick1:', sum(1 for _ in open(spawn.SPAWN_ATTEMPTS_PATH)))
  n2 = roster.spawn_attempt_sweep(); print('tick2 reported:', n2)
  print('lines remaining after tick2:', sum(1 for _ in open(spawn.SPAWN_ATTEMPTS_PATH)))
  "
  tick1 reported: 3   # issue-1, issue-31, issue-7 no-outcome subjects
  lines remaining after tick1: 4
  tick2 reported: 1   # issue-1's separate *halted*-outcome attempt_id — see caveat below
  lines remaining after tick2: 4
  ```
  The two specific historical dead-pid subjects named in the issue
  filing (issue-31, issue-7, 305+114 records) do not resurface in
  tick2 — confirmed dropped after tick1 and absent from tick2's
  output, per the transcript above.

  Caveat (recorded rather than smoothed over): the PR's own transcript
  (`6531f56f:docs/issue-2431/reports/implementation.md`) claims `tick 2
  reported: 0`, but this session's independent, freshly-restored-from-
  backup run got `tick2 reported: 1`, per the transcript above. The
  discrepancy is not in the dead-pid fix under review — the one report
  in my tick2 is a pre-existing real `halted`-outcome record for
  issue-1 (a different `attempt_id`, unaffected by this PR, gated by
  its own per-attempt_id ledger dedup), which the PR's own session had
  already ledger-stamped once earlier in that same session before its
  quoted two-tick demo ran, and my fresh run had not. The specific
  claim the acceptance bullet is about — dead-pid orphans not
  resurfacing — holds in both runs; the PR's "0" vs. this session's
  "1" difference is ledger pre-warming state, not a functional
  divergence.
rationale: Independently reproduced the two-tick demonstration from a clean state rather than trusting the builder's transcript, confirmed the actual acceptance claim (dead pids don't resurface) holds, and recorded a real reproducibility discrepancy (an unrelated halted-record report count) rather than silently matching it to the builder's numbers.
---
requirement: "A5 — nothing about the halted-outcome branch's existing 7-day retention changes; this is stated explicitly" [dimension: scope-boundary]
spec_ref: issue #2431, Acceptance bullet 5
verdict: Present
evidence: |
  Byte-identical diff (A1's evidence block) between `c5851224:spawn.py`
  and `6531f56f:spawn.py` for the `elif outcome.get("outcome") ==
  "halted":` block.

  derived: independent from-scratch fixture, this session, exercising
  both edges of the retention window (neither reused from the
  builder's transcript):
  ```
  $ cd /tmp/pr-2434-review && MUSTER_STATE_ROOT=/tmp/review-2431-halted/runs python3 -c "
  import json, time, spawn
  now = time.time()
  recs = [
      {'event':'spawn_attempt','attempt_id':'h1','issue':1,'role':'implementation','pid':99999999,'ts':now-100},
      {'event':'spawn_attempt_outcome','attempt_id':'h1','outcome':'halted','detail':'x','ts':now-100},
      {'event':'spawn_attempt','attempt_id':'h2','issue':2,'role':'implementation','pid':99999998,'ts':now-8*24*3600},
      {'event':'spawn_attempt_outcome','attempt_id':'h2','outcome':'halted','detail':'y','ts':now-8*24*3600},
  ]
  with open(spawn.SPAWN_ATTEMPTS_PATH,'w') as f:
      for r in recs: f.write(json.dumps(r)+'\n')
  print('dropped:', spawn._prune_spawn_attempts())
  "
  dropped: 2
  ```
  A `halted` record 100s old survived; one 8 days old (past the
  7-day `SPAWN_ATTEMPTS_RETENTION_SEC`) was pruned — the same
  retention behavior as before this PR. Stated explicitly in
  `6531f56f:docs/issue-2431/reports/implementation.md` ("Why the
  halted branch is untouched"), the PR description, and the code
  comment (A2a evidence) — canonical: `gh pr view 2434`, this session.
rationale: Byte-identical code plus an independently-built two-record fixture exercising both sides of the 7-day boundary confirm the halted branch's retention behavior is unchanged, and the "left as-is" claim is stated explicitly in three places, not merely implied.
---

## Open findings

canonical: the five Findings blocks above (this session's own
independently re-derived evidence, transcripts quoted there).

None — all five acceptance checks verdict Present on independent
re-derivation (canonical: Findings A1-A5 above). The one procedural
discrepancy found (A4's tick2 report count, caused by ledger
pre-warming state differing between the builder's session and this
review's fresh run, per A4's evidence above) does not indicate a
functional defect. Resolution path: not applicable.

## Next steps

canonical: `loop_state: reported` in this file's own frontmatter above
— terminal for this record kind.

None — review is terminal. No CHANGES-round was needed.

## Skill verdicts

canonical: this session's own Skill tool-call transcript (the six
`Skill` invocations preceding this file's authorship) and the Findings
section above (where each skill's rules were actually applied).

skill-verdict: conformance-review-requirement-extraction — applied:
invoked; used to split issue #2431's Acceptance bullet 2 (reasoning
stated + live-pid-never-pruned invariant) into A2a/A2b before any
verdict was rendered, and to dimension-tag each of the five resulting
requirement blocks in "## Findings".

skill-verdict: conformance-review-verification-method-selection —
applied: invoked; selected Inspection for the structural claims (A1's
branch-separation, A5's byte-identical halted block) and Demonstration
for the functional claims requiring live execution against real state
(A2b, A3, A4), reusing the repo's own existing
`test_live_pid_survives_regardless_of_age` as Test-method
corroboration for A2b per rule 4 rather than only a self-built fixture.

skill-verdict: conformance-review-verdict-assignment — applied:
invoked; all five findings assigned Present (implemented and reachable
on the actual code path, not merely matching vocabulary), each with an
evidence pointer independently re-derived this session rather than
carried forward from any prior verdict (no prior conformance-review
record exists for issue #2431).

skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; every evidence block cites file:line-range plus the exact
commit sha read (`c5851224` for the pre-fix baseline, `6531f56f` for
the PR head), and A1/A5's evidence spans two files' worth of
comparison (both citing the same sha pair) rather than being
collapsed into one bare path.

skill-verdict: conformance-review-finding-record — applied: invoked;
wrote the five requirement blocks above into this file with the full
field list (requirement, spec_ref, verdict, evidence, rationale) —
canonical: the Findings section above; no Incorrect/Absent verdict
arose, so no `spec_vs_built` field was needed, and no write was
refused since evidence was located for every bullet.

skill-verdict: defect-verification-independence-from-upstream-verdicts
— applied: invoked; built every demonstration in this record from
scratch (own worktrees, own fixtures, own live pid, own fresh copy of
the real backlog) rather than citing the implementation record's own
transcripts, deliberately included the edge case the builder's own
real-backlog demo could not exercise on its own terms (a fresh, still-
alive pid at extreme age, run from this session's own process), and
recorded the one not-fully-matching outcome (A4's tick2 count) with
the same rigor as the matching ones rather than smoothing it into
agreement with the builder's numbers — canonical: A2b and A4 evidence
blocks above.

skill-verdict: conformance-review-sampling-derivation — not-applicable:
full enumeration was feasible — canonical: issue #2431's Acceptance
section (`gh issue view 2431`, this session) lists exactly five
bullets, all checked, no file-set large enough to require sampling.

skill-verdict: conformance-review-severity-classification —
not-applicable: canonical: the five Findings blocks above, all
verdict Present — no defect was found to risk-weight, so scope was
never extended into severity banding.

other mounted skills: not triggered (freelunch:freelunch-code-fanout,
freelunch:freelunch-site-fanout, terse:terse [style-only, governs
prose not orchestration], dataviz, update-config, keybindings-help,
code-review, simplify, fewer-permission-prompts, loop, schedule,
claude-api, run, init, security-review — none apply to a conformance
review of an already-merged-design fix with no visualization, config,
or app-launch component).
