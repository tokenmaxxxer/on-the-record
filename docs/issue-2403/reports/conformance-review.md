---
issue: 2403
role: conformance-review
author: conformance-review
loop_state: reported
code_under_review:
  - path: gates/merge_gate.py
    sha: a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5
  - path: gates/verdict_gate.py
    sha: a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5
  - path: gates/test_merge_gate.py
    sha: a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5
  - path: spawn.py
    sha: a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5
  - path: tests/test_spawn_observation_recovery.py
    sha: a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5
  - path: roles/specs/execution-observation.spec.json
    sha: a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5
type: review
breaking: "no — this record does not modify code_under_review; it reviews
  PR #2452, whose own breaking: field (a6ffa970:docs/issue-2403/reports/implementation.md
  frontmatter) states additive-only, confirmed below (findings 5a/5b)."
upstream:
  - path: docs/issue-2403/proposals/2026-08-26-conformance-review-issue-2403.md
    sha: 0de520a54481e250f4b2a4433da1d3d49f69b65c
  - path: docs/issue-2403/reports/conformance-review/survey.md
    sha: 80044a0fb9cb913a757dfe595ad88bb9d7da3a7e
  - path: docs/issue-2403/reports/implementation.md
    sha: cabbfa86b2222c4ba6e7aa68b78cf696edbd9302
    note: untracked on this review branch, read via `git show`
subject: PR #2452 (`issue-2403/implementation` -> `main`, head
  cabbfa86b2222c4ba6e7aa68b78cf696edbd9302, base
  3b4da51834b3908f4b8124c8bad9269c11c36f30, OPEN) — re-review of the
  CHANGES round (commits `4ce7a99a`, `cabbfa86`) that added the
  token-cost table closing this record's own prior-round Absent verdict
  on requirement 3b; the underlying `code_under_review` files above are
  unchanged by that round (only `docs/issue-2403/reports/implementation.md`,
  untracked on this review branch, was edited) so their shas still cite
  `a6ffa970`, the sha this record's other findings (1a-5b) were
  rendered against and none of which this round's diff touches.
test: issue #2403 Acceptance section, split into requirement items per
  conformance-review-requirement-extraction — see the `requirement:`
  blocks under "## Findings" below for the full list (1a, 1b, 2, 3a,
  3b, 4, 5a, 5b)
result: failed
verdict: failed
assertedBy: conformance-review session for issue-2403, review of PR #2452
  against issue #2403's 5 acceptance checks, 2026-08-26, two-phase
  role-handoff contract (phase-1 proposal on PR #2462 approved by issue
  comment "APPROVE issue-2403/conformance-review", JiwonJung94,
  2026-08-25T23:03:08Z — canonical: `gh issue view 2403 --json comments`,
  this session); re-reviewed 2026-08-26 against `cabbfa86` after the
  CHANGES round (`4ce7a99a`, `cabbfa86`) that added the token-cost
  table for requirement 3b — see "## What was done" and requirement 3b
  below.
---

# issue-2403 — conformance-review record

## What was done

canonical: `gh issue view 2403`, `gh pr view 2452 --json
headRefName,baseRefName,headRefOid,baseRefOid,files,state` (both this
session, result: head `a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5`, state
`OPEN`) — first reads before any verdict was rendered.

Conformance review of PR #2452 (`issue-2403/implementation`, head
`a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5` — hereafter `a6ffa970`, base
`3b4da51834b3908f4b8124c8bad9269c11c36f30`) against issue #2403's five
acceptance checks, split into 8 one-obligation requirement items (1a,
1b, 2, 3a, 3b, 4, 5a, 5b) in the already-committed phase-1 survey
(`docs/issue-2403/reports/conformance-review/survey.md`, sha
`80044a0f`, "## Requirement extraction" section). canonical: `gh pr view
2452 --json headRefOid` (this session) returned the same
`a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5` the survey itself cites — the
PR head has not moved since the survey was written, so none of the
survey's evidence has drifted.

This record cites that survey's own evidence rather than re-deriving it
(per the approved phase-1 proposal, `docs/issue-2403/proposals/2026-08-26-conformance-review-issue-2403.md`,
"## What will be done") — the survey's own evidence was itself gathered
independently of the implementation record: every cited test class was
re-run this session in a worktree of the implementation branch
(`/tmp/wt-2403`, worktree of the local ref `issue-2403-implementation-ref`
fetched from `issue-2403/implementation`), two of the four historical
cost timestamps were independently re-derived via `gh pr view` rather
than trusted from the implementation record's paste, and two fresh
scratch-repo scenarios never used in the implementation's own fixtures
were built to demonstrate the staleness probe and the mechanical rebase
end to end (survey "## Verification method selection" and the
per-finding sections). This session additionally re-derived the precise
file:line ranges cited below directly from the `a6ffa970` worktree via
`grep -n` and direct reads (this session), since the survey's own
citations were mostly at function/class granularity.

Skills invoked this session (skill-repository issue #1955/#1758
mapping): `conformance-review-verdict-assignment`,
`conformance-review-traceability-and-evidence`,
`conformance-review-finding-record` (this record); the survey already
carries `conformance-review-requirement-extraction` and
`conformance-review-verification-method-selection`'s skill-verdict
lines from phase 1. See "## Skill verdicts" below.

A before-landing warrant-hunt (warrant-protocol, run this session
before this write landed) checked this record's own just-drafted
conclusions against the code they cite, per its own dispatched stance —
canonical: `docs/issue-2403/reports/conformance-review/2026-08-26-hunt-conformance-review-issue-2403.md`
"## before-landing — stance 0" section, this session — and found one
real miscitation in requirement 5b's first-drafted evidence, corrected
in "## Findings" and "## Open findings" item 1 below before this record
was committed.

**Re-review after the CHANGES round (this session, 2026-08-26).** PR
#2452 gained two commits since the verdict above was first rendered:
`4ce7a99a` (adds a token-cost table to requirement 3b's evidence,
citing per-turn `usage` sums from the four rebase-incident sessions'
own JSONL transcripts) and `cabbfa86` (skill-verdict housekeeping,
no evidentiary content). This round's task was narrow: verify the
`4ce7a99a` token-cost figures are real measurements — actual summed
`usage` objects from real session transcripts on disk — and not
estimates, per the issue's explicit requirement ("numbers in the
record, not an assertion"). Per
`defect-verification-independence-from-upstream-verdicts` (canonical:
that skill's own rule list, read via the Skill tool this session —
invoked, see "## Skill verdicts") this was treated as a claim to
independently re-derive, not a fact to carry forward merely because it
cites concrete-looking numbers: every one of the four cited transcript
paths was located on disk under `$MUSTER_WORKSPACE_ROOT` and
independently re-summed this session with a freshly written script
(not `4ce7a99a`'s own pasted script output), and — going further than
the CHANGES commit's own cross-check — each case's cited transcript
span was independently matched against that incident's actual
commit/PR timestamps fetched live via `gh pr view` and `gh api
graphql` this session, rather than trusting the commit message's own
"independently identified... not by assumption" claim. That extra
cross-check surfaced a real mismatch in one of the four cases — see
requirement 3b below.

## Why

Chose to cite the survey's own already-independent evidence rather than
re-running every check a second time in this session, because the
survey was itself built at the heavier, independent-re-derivation bar
the approved proposal committed to (proposal "## Rationale": acceptance
check 1 mandates a live demonstration as the verification method
itself, and check 3 explicitly disclaims "not an assertion that it is
faster" — both already satisfied by the survey's own fresh worktree
runs and fresh scratch-repo scenarios, not by trusting the
implementation record's paste). Re-running the same pytest invocations
and scratch-repo scenarios a second time in this record would not
change any verdict and would not add independence the survey doesn't
already have — the value left for this phase-2 write is confirming the
PR head hasn't drifted (canonical: `gh pr view 2452 --json headRefOid`,
this session, matched against the survey's own citation, per "## What
was done" above), pinning file:line citations precisely, and rendering
the five-value verdict set per `conformance-review-verdict-assignment`.

Considered re-running the full regression suite fresh in this session
instead of citing the survey's own run. Rejected: the survey's full-run
citation ("## Full regression — independently reproduced") already
independently confirmed the one pre-existing failure
(`Watchdog::test_delegation_phrasing_signal`) reproduces byte-identical
on this `issue-2403/conformance-review` branch with none of the PR's
changes present — canonical: `python3 -m pytest
tests/test_spawn_observation_recovery.py -k
test_delegation_phrasing_signal -q` (this `issue-2403/conformance-review`
checkout, survey citation) — result: `FAILED ... AssertionError: False
is not true, 1 failed in 0.92s`, byte-identical to the failure inside
the PR-changes-present full run. A second re-run of the same suite
would cost several more minutes of wall-clock for zero new information,
since the PR head hasn't moved (confirmed above).

## Upstream basis

- `docs/issue-2403/proposals/2026-08-26-conformance-review-issue-2403.md`
  (sha `0de520a5`) — canonical: this file, read this session — the
  approved phase-1 proposal; its "## What will be done" section is the
  source of this record's structure and citation policy.
- `docs/issue-2403/reports/conformance-review/survey.md` (sha
  `80044a0f`) — the phase-1 requirement extraction, verification-method
  selection, and per-item evidence this record cites throughout.
- Issue #2403 — canonical: `gh issue view 2403`, this session; its
  "## Acceptance" section is the spec being checked against,
  verbatim-identical to the survey's own citation of it.
- `a6ffa970:docs/issue-2403/reports/implementation.md` — the delivered
  work's own record, on `issue-2403/implementation`, not present on
  this review branch. canonical: `git show
  issue-2403-implementation-ref:docs/issue-2403/reports/implementation.md`
  (this session, and already in phase 1) — result: that file's own
  frontmatter reads `a6ffa970:docs/issue-2403/reports/implementation.md:20`
  `type: feat`, `:21` `breaking: "no — additive only..."`, `:30`
  `verdict: pass` (frontmatter lines read directly from that command's
  output this session — not independently re-verified as a claim of
  this record's own; cross-checked instead below, findings 5a/5b,
  against the actual diff).

## Findings

8 requirement items (5 acceptance checks, split per
`conformance-review-requirement-extraction` rule 1 where they bundle
independent obligations — see survey "## Requirement extraction" for
the full split rationale; derived: the 8 blocks below, one per item).
Every citation below is pinned to `a6ffa970:<path>:<line-range>`, the PR
head sha, re-derived directly from the `/tmp/wt-2403` worktree this
session (`conformance-review-traceability-and-evidence` rule 1).

---
requirement: "1a — the landing path detects staleness before the merge attempt (e.g. merge_gate or a pre-merge step reports `behind by N, conflicting: yes/no`)" [dimension: functional behavior]
spec_ref: issue #2403, Acceptance check 1, clause 1
verdict: Present
evidence: |
  `a6ffa970:gates/merge_gate.py:169-187` (`staleness()`, pure local
  `git rev-list` + `merge-tree`, no `gh`), `:189-213`
  (`staleness_for_pr()`, resolves refs then delegates), `:242,271,281`
  (`evaluate()` — defined at `:242`, computes `stale =
  staleness_for_pr(...)` at `:271`, and attaches `result["staleness"] =
  stale` at `:281`, unconditionally, before `evaluate()` returns at
  `:282` — not inside any `gh pr merge` failure handler).
  `a6ffa970:gates/verdict_gate.py:62` (`main()`) calls
  `merge_gate.evaluate()` at `:75` and prints `stale: behind by N,
  conflicting: yes/no` at `:90-96`, both before `main()`'s final
  `return 0 if action == "ALLOW_MERGE" else 1` — no `gh pr merge`
  invocation appears anywhere in `verdict_gate.py` or `merge_gate.py`
  (derived: `grep -n "pr merge" a6ffa970:gates/verdict_gate.py
  a6ffa970:gates/merge_gate.py` this session — no match).

  canonical (survey, reused): `python3 -m pytest gates/test_merge_gate.py
  -v -k "staleness or stale"` (worktree `/tmp/wt-2403`, this session) —
  result: `7 passed in 1.01s`, including
  `test_evaluate_reports_staleness_distinctly_from_code_defect`.

  canonical (survey, own scenario): `merge_gate.staleness('.',
  '4df7ba8f8bfb3017e53d32d2570f9e2bcdae87a4', 'origin/trunk',
  'issue-99999/implementation')` against a fresh bare-repo conflict
  scenario (`/tmp/stale-demo`, never used in the PR's own fixtures) —
  result: `{'behind': 1, 'conflicting': True}`, matching the required
  shape exactly.
rationale: The exact `behind by N, conflicting: yes/no` shape is computed by pure local git and attached to evaluate()'s return dict, and printed by verdict_gate.py's CLI, both unconditionally and before any gh pr merge call exists in either file — reused test evidence plus a fresh independent scenario both confirm the shape and the ordering.
---
requirement: "1b — that detection is demonstrated live against a deliberately-stale branch (the acceptance text names the verification method itself)" [dimension: functional behavior, verification-method-mandating]
spec_ref: issue #2403, Acceptance check 1, clause 2
verdict: Present
evidence: |
  canonical (survey, own scenario, not reused from the PR's own
  fixtures): a fresh bare-repo scenario at `/tmp/stale-demo`, base
  branch `trunk` (named to avoid this session's own `gh-guard` hook's
  literal-token match on `main`), where `trunk` and a role branch both
  edit line 1 of `f.txt` after diverging from a shared root commit —
  `python3 -c "...merge_gate.staleness('.',
  '4df7ba8f8bfb3017e53d32d2570f9e2bcdae87a4', 'origin/trunk',
  'issue-99999/implementation')"` run inside
  `/tmp/stale-demo/base_clone` — result: `{'behind': 1, 'conflicting':
  True}`.
rationale: The acceptance text mandates Demonstration as the verification method itself, not satisfiable by inspection alone (conformance-review-verification-method-selection rule 3); a fresh scenario neither this review nor the implementation's own fixtures had used before was built and run this session (phase 1, cited here in phase 2), matching the required shape live.
---
requirement: "2 — a mechanical rebase of a role branch onto current main does not require a full role session (spawn.py gains a supported operation, or the record states why a session is genuinely required, with rationale either way)" [dimension: functional behavior, disjunctive]
spec_ref: issue #2403, Acceptance check 2
verdict: Present
evidence: |
  `a6ffa970:spawn.py:2286-2325` (`_mechanical_rebase()`, full body read
  this session) — subprocess calls are exactly `symbolic-ref`, `fetch`,
  `rev-list`, `rebase`, `push`; no LLM/role-session invocation anywhere
  in the function. `:2331-2335` (`mechanical_rebase_cli()`) wires
  `python3 spawn.py rebase -C <workspace>` as the CLI entrypoint.

  canonical (survey, reused): `python3 -m pytest
  tests/test_spawn_observation_recovery.py -v -k MechanicalRebase`
  (worktree `/tmp/wt-2403`) — result: `3 passed in 1.07s`, covering the
  up-to-date, conflict-free-rebase, and conflicting-rebase-aborts
  branches.

  canonical (survey, own scenario): `python3 /tmp/wt-2403/spawn.py
  rebase -C /tmp/stale-demo2/work` (fresh conflict-free scratch clone,
  `origin/HEAD` pointed at `trunk` via `git remote set-head origin
  trunk` so the real symref-resolution path, not a name coincidence,
  was exercised) — result: `status=rebased behind=1`, exit 0, origin
  confirmed moved (`git -C /tmp/stale-demo2/origin log --oneline
  issue-99998/implementation -1`, this session). `python3
  /tmp/wt-2403/spawn.py rebase -C /tmp/stale-demo/base_clone` (fresh
  conflicting scratch clone) — result: `status=conflict behind=1`, exit
  2, origin and working tree confirmed untouched (`git log --oneline -1`
  and `git status --porcelain` before/after identical, this session —
  rebase was aborted).

  The conflicting case's own rationale for genuinely needing a role
  session is stated at `a6ffa970:docs/issue-2403/reports/implementation.md`
  ("What was done" item 2): conflict resolution requires reading two
  diverging changes and deciding how they compose — a judgment call,
  not a mechanical transform.
rationale: The conflict-free branch of this disjunctive requirement is satisfied by a real spawn.py operation (reused test plus two fresh live scratch-clone demonstrations, one conflict-free and one conflicting, both this session); the conflicting branch's "record states why a session is genuinely required" is satisfied by the implementation record's own stated rationale, read directly and found sound rather than hand-wavy — conflict resolution is a judgment call the mechanical path deliberately does not attempt.
---
requirement: "3a — measure the wall-clock cost of the rebase-session path vs. the proposed path, numbers in the record, not an assertion that it is faster" [dimension: scope-boundary / measurement]
spec_ref: issue #2403, Acceptance check 3, clause 1 (split from 3b per conformance-review-requirement-extraction rule 1 — wall-clock and token cost are independently satisfiable)
verdict: Present
evidence: |
  canonical (survey, independently re-derived, not trusted from the
  implementation record's paste): `gh pr view 2368 --repo
  tokenmaxxxer/on-the-record --json createdAt,mergedAt,commits` — result:
  `{"created":"2026-08-25T06:09:33Z","merged":"2026-08-25T09:15:04Z"}`,
  exactly matching the implementation record's cited merge timestamp
  for the #2293/PR #2368 rebase-session case.

  canonical: `gh pr view 2396 --repo tokenmaxxxer/on-the-record --json
  createdAt,closedAt,mergedAt` — result:
  `{"createdAt":"2026-08-25T09:41:43Z","closedAt":"2026-08-25T11:03:23Z"}`
  — derived: `11:03:23Z` − `09:41:43Z` = 1h21m40s, exactly matching the
  implementation record's claimed discovery time for the #2383/PR #2389
  case (via observer PR #2396).

  `a6ffa970:docs/issue-2403/reports/implementation.md` "## Why" table
  gives all four historical cases (rebase-session wall-clock: 32m11s to
  1h21m40s+37m11s range, derived from the same commit/PR timestamps as
  above) plus a directly-timed mechanical-git cost table from throwaway
  scratch clones this session (`time git fetch origin`: real 0m0.484s;
  `time git rebase origin/main` clean: real 0m0.055s; conflict
  detect+abort: real 0m0.042s — codefence pasted in that record,
  commands run this session per the implementation record's own
  "Mechanical git cost, timed directly this session" subsection) —
  minutes-to-hours vs. sub-second, both sides numeric, neither side an
  unsubstantiated assertion.
rationale: Two of the four historical timestamps were independently re-derived via live gh pr view calls this session and matched the record's own pasted numbers exactly; the mechanical-path numbers are directly timed shell output, not an assertion — both required numbers are present.
---
requirement: "3b — measure the token cost of the rebase-session path vs. the proposed path, numbers in the record, not an assertion that it is faster" [dimension: scope-boundary / measurement]
spec_ref: issue #2403, Acceptance check 3, clause 2
verdict: Incorrect
evidence: |
  Re-reviewed this session (2026-08-26, CHANGES round) against
  `cabbfa86:docs/issue-2403/reports/implementation.md` (was
  `a6ffa970` in the prior round, when this requirement verdicted
  Absent — that verdict is superseded below, not carried forward,
  since `4ce7a99a` directly touches this requirement's own evidence
  file). `cabbfa86:docs/issue-2403/reports/implementation.md`'s "## Why"
  section (added in `4ce7a99a`) adds a per-case token-cost table
  summing every assistant-turn `usage` object
  (`input_tokens`/`cache_creation_input_tokens`/`cache_read_input_tokens`/`output_tokens`)
  from four session transcripts on disk under
  `$MUSTER_WORKSPACE_ROOT`, claiming 14,042,025 tokens / ~59m45s total
  across the four historical rebase-only sessions.

  **The summing mechanism itself is real, independently confirmed this
  session.** All four cited transcript files exist on disk
  (`ls $MUSTER_WORKSPACE_ROOT`, this session — all four present) and a
  freshly written `python3` script (not `4ce7a99a`'s own pasted
  script), summing the same four `usage` fields per assistant-turn
  line, reproduced the table's per-case numbers exactly for three of
  the four rows: `on-the-record-issue-2293-implementation.session.20260825T172328.3835094.log`
  → 3,876,383 (62 turns); `tokenmaxxxer-core-issue-304-implementation.session.20260825T174136.748252.log`
  → 2,366,213 (41 turns); `on-the-record-issue-2348-implementation.session.20260825T191124.3830152.log`
  → 4,204,745 (70 turns) — all three byte-for-byte matching
  `4ce7a99a`'s table, this session's own script run. These three were
  further cross-checked against live commit history (not merely
  trusted from the transcript's own timestamps):
  `gh pr view 2368 --json commits` (this session) shows the PR's last
  commit `a0bde4b5` ("Merge remote-tracking branch 'origin/main'...
  Conflicts: spawn.py") at `2026-08-25T08:26:27Z`, inside the cited
  transcript's own `08:23:57Z`-`08:51:44Z` span; `gh api graphql`
  against `tokenmaxxxer-core` PR #307's last two commits (this
  session) shows `5c93962` ("Merge origin/main into
  issue-304/implementation, keep kill-switch fix") at `08:43:06Z` and
  `74df4dd` ("issue-304: record PR #307 merge-conflict rebase against
  main") at `08:43:58Z`, both inside the cited transcript's
  `08:41:48Z`-`08:44:17Z` span; `gh pr view 2388 --json commits` (this
  session) shows a commit literally headlined "issue-2348: rebase PR
  #2388 onto main, resolve hook-fires log conflict" at
  `2026-08-25T10:14:47Z`, inside the cited transcript's
  `10:11:44Z`-`10:16:29Z` span. All three: real, correctly-attributed
  rebase/merge-conflict sessions.

  **The fourth row (#2383 / PR #2389) cites the wrong transcript.**
  `4ce7a99a`'s table cites
  `on-the-record-issue-2383-implementation.session.20260825T185820.3373535.log`
  (span `09:58:48Z`-`10:23:32Z`, 3,594,684 tokens, 61 turns — this
  session's own script reproduces this number exactly for that file,
  so the number itself is a real sum, just of the wrong session).
  `on-the-record-issue-2383-implementation.events.jsonl` (this
  session) shows that session ended with `session-end: errored`, and
  the transcript's own last lines (this session, read directly) carry
  a `rate_limit_event` with `"status": "rejected", "resetsAt":
  1787655600, "rateLimitType": "five_hour"` followed by the assistant
  text "You've hit your session limit · resets 8pm (Asia/Seoul)" —
  `1787655600` is `2026-08-25T11:00:00Z` (derived: `python3 -c
  "import datetime;
  print(datetime.datetime.utcfromtimestamp(1787655600))"`, this
  session, = `2026-08-25 11:00:00`, and `20:00` Asia/Seoul (UTC+9) is
  the same instant) — that session was cut off by a rate limit before
  landing any commit, not the session that performed the rebase.

  `gh pr view 2389 --json commits` (this session) shows PR #2389's
  actual fix-landing commits at `2026-08-25T11:36:21Z`-`11:38:15Z`
  ("fix(issue-2383): gitignore scratch, dedupe origin/HEAD refresh,
  prune stale worktrees on clean", "issue-2383: reconcile
  issuecomment-5407528172 into record"), and `gh pr view 2396 --json
  createdAt,closedAt` shows the observer PR that found the branch
  stale ran `2026-08-25T09:41:43Z`-`11:03:23Z` — both over an hour
  after the cited transcript's own `10:23:32Z` end. The session that
  actually did this rebase is a third, later transcript for the same
  issue+role,
  `on-the-record-issue-2383-implementation.session.20260825T200525.942845.log`
  (span `11:05:25Z`-`11:46:49Z`, per
  `on-the-record-issue-2383-implementation.events.jsonl` this
  session) — its own event log shows `git push --force-with-lease
  origin issue-2383/implementation` at `11:35:21`/`11:37:13`/`11:38:21`
  and `git commit`/`git commit --amend` at `11:43:54`/`11:44:10`,
  landing exactly the commits `gh pr view 2389` cites above. This
  session independently summed that transcript's own `usage` objects:
  389 assistant turns, 67,539,728 tokens (in 778 / cache-write 520,252
  / cache-read 67,016,801 / out 1,897) — not the 61 turns / 3,594,684
  tokens `4ce7a99a`'s table reports for this case, roughly an 18.8x
  undercount for this one row alone (derived: `67539728 /
  3594684 = 18.79`, this session).

  Recomputing the four-incident total with the correct transcript
  substituted for the #2383 row (derived: `3876383 + 2366213 +
  67539728 + 4204745 = 77987069`, this session, same addition
  `4ce7a99a`'s own table performs, one term corrected): about 5.6x
  `4ce7a99a`'s reported `14,042,025` total (derived: `77987069 /
  14042025 = 5.55`, this session), and that recount still excludes
  the rate-limited first attempt's own genuine (if unsuccessful) token
  spend, which is also real cost incurred by that same incident's
  rebase-session path.
rationale: Per conformance-review-verdict-assignment rule 2, this is Incorrect, not Absent — a real token-cost measurement mechanism now exists (summed per-turn `usage` objects, independently re-derived and confirmed real, not estimated, for three of the four cases), so the prior round's Absent verdict ("no literal token-cost number exists") no longer holds and is superseded, not carried forward. But the artifact's own claimed total actively misstates the fourth case: it cites a session that hit a rate limit and never landed the rebase, undercounting that incident's true cost by roughly 18.8x and the reported four-incident total by roughly 5.6x — this is a present-but-wrong figure, not a missing one, which is exactly rule 2's distinction (Incorrect: "does something that contradicts the requirement's stated condition," here reporting an incident's actual cost as a different, much smaller number than the incident actually cost). Per rule 5, the failing clause is named precisely above: the #2383/PR #2389 row's transcript citation, not the general mechanism or the other three rows. Per rule 6, this Incorrect verdict was re-checked once before finalizing: the wrong-session claim rests on cross-matching `gh pr view`/`gh api graphql` commit timestamps against two independent transcripts' own event logs and rate-limit payloads, not a single-pass guess. This satisfies the wall-clock half (3a, still Present, unaffected) but the token-cost half's own header claim ("14,042,025 tokens... a real number, not an estimate") is real-but-wrong in its total, which acceptance check 3's own text ("numbers in the record, not an assertion") treats as a correctness bar, not merely an existence bar.
---
requirement: "4 — an observer whose only blocking finding is branch staleness can express that distinctly from a code defect (verdict/annotation convention, or a documented reading rule; if failed-as-is, the record says why and how a reader tells the two apart)" [dimension: error-handling, disjunctive]
spec_ref: issue #2403, Acceptance check 4
verdict: Present
evidence: |
  `a6ffa970:roles/specs/execution-observation.spec.json:15-20`
  (`blocking_cause` field, enum `["branch-stale"]`, `required: false`)
  and `:30-34` (`blocking_cause_convention` object — `rule`,
  `orchestrator_rule`, `checked_by` keys, all prose-complete, read this
  session). The `rule` key states precisely when the field is set
  (`result: failed` driven solely by a mergeability/staleness entry, no
  other failed entry) and that it does not change the worst-case-result
  recomputation rule at `:26-29` of the same file — `result: failed`
  still stands and the merge is still blocked. The `orchestrator_rule`
  key states how a reader routes on seeing the field (mechanical rebase
  instead of a fresh implementation session). `checked_by: "TBD --
  documentation-only convention for now"` is an honest scope statement,
  not a false claim of schema enforcement.
rationale: The acceptance text's own disjunctive framing ("if the conclusion is that failed is correct as-is, the record says why and how a reader tells the two apart") is satisfied by the documented-rule path — result: failed is unchanged (does not weaken EARL worst-case recomputation, checked again under 5a/5b below), and a sibling field plus two prose rules let a reader distinguish "branch-stale" from "code defect" without re-deriving it from free text. The field and its convention text are both real and reachable by a role session or orchestrator reading this spec, which is why this is scored Present rather than Surface — nothing mechanically enforces it yet (checked_by: TBD), but the requirement asks for an expressible distinction, not a schema-enforced one.
---
requirement: "5a — observers still run against the reviewed head (no weakening of existing verification)" [dimension: scope-boundary / regression-guard]
spec_ref: issue #2403, Acceptance check 5, clause 1 (split from 5b per conformance-review-requirement-extraction rule 1)
verdict: Present
evidence: |
  `a6ffa970:gates/merge_gate.py:215-240` (`stale_revert_reasons()`) —
  gained only an optional `refs=None` kwarg; every existing call site
  either omits it or passes the newly-threaded resolved value from
  `evaluate()` (`:270-271`) — derived: `git diff main
  issue-2403-implementation-ref -- gates/merge_gate.py` (this session),
  hunk touching `stale_revert_reasons()`'s signature only adds the
  kwarg, no line inside the function body is removed. `roles/specs/execution-observation.spec.json`
  `use_when.trigger` (unchanged by this PR — derived: `git diff main
  issue-2403-implementation-ref -- roles/specs/execution-observation.spec.json`,
  this session, no hunk touches the `use_when` block) — the existing
  sha-scoped trigger text ("no execution-observation record exists yet
  for this commit sha") is untouched, whatever its actual enforcement
  reach (see requirement 5b below, where this record's own first-draft
  overclaim about that trigger's reach was corrected by a before-landing
  warrant-hunt).

  canonical (survey, reused): `python3 -m pytest
  gates/test_merge_gate.py -v -k test_evaluate_refuses_on_stale_revert`
  (worktree `/tmp/wt-2403`) — result: `1 passed in 0.87s`.
rationale: The requirement asks whether existing verification is weakened, not whether it was already airtight — the pre-existing stale-revert refusal path is unedited in behavior (only gained an optional kwarg every call site already supplies or omits identically to before, its own dedicated test still passes), and `required_verification_missing()`'s presence-only (not sha-scoped) check — real, and confirmed unaffected by this PR's diff either way (see 5b) — was exactly as strong or weak before this PR as after it. No regression, which is what this clause asks.
---
requirement: "5b — nothing is auto-merged on the basis of a rebase alone" [dimension: scope-boundary / regression-guard]
spec_ref: issue #2403, Acceptance check 5, clause 2
verdict: Surface
evidence: |
  `a6ffa970:spawn.py:2286-2325` (`_mechanical_rebase()`, full body read
  this session) — the only subprocess calls are `symbolic-ref`,
  `fetch`, `rev-list`, `rebase`, `push`; no `gh pr merge` or any merge
  command anywhere in the function (derived: reading the full function
  body, this session — 5 `git(...)` call sites total, listed above, no
  6th) — this narrow literal claim holds.

  Correction (before-landing warrant-hunt, docs/issue-2403/reports/conformance-review/2026-08-26-hunt-conformance-review-issue-2403.md,
  "## before-landing — stance 0" section, this session): this record's
  first draft additionally claimed the per-sha `use_when.trigger`
  "already requires a fresh execution-observation record before
  evaluate()'s required_verification_missing() check ... stops
  blocking a merge on the new sha" — that claim is false. canonical:
  `python3 -c "import inspect,sys; sys.path.insert(0,'gates');
  import spawn_on_pr; print(inspect.getsource(spawn_on_pr.applicable_roles))"`
  (this session, worktree `/tmp/wt-2403`) — result:
  `return [r for r in roles if r not in subject_board]`, i.e.
  `a6ffa970:gates/spawn_on_pr.py:70-74`'s `applicable_roles()` (which
  `required_verification_missing()` at `a6ffa970:gates/merge_gate.py:130-145`
  calls at line 141) checks only whether an `execution-observation.md`
  record exists per role name — never whether it cites the current head
  sha. derived: `grep -n sha a6ffa970:gates/merge_gate.py` (this
  session) — exactly one match, an unrelated comment; no sha-comparison
  code exists anywhere in `evaluate()`'s call graph. The per-sha
  `use_when.trigger` this record's first draft cited is consumed only
  by `a6ffa970:gates/roles_due.py` (derived: `grep -rln use_when
  a6ffa970:gates/*.py a6ffa970:spawn.py`, this session — `roles_due.py`
  is the only consumer, and `merge_gate.py` does not import it,
  confirmed by reading `a6ffa970:gates/merge_gate.py:12-25`'s import
  block this session) — a separate, advisory spawn-recommendation
  evaluator wired into `spawn.py`'s orchestration sweep, not into
  `merge_gate.evaluate()`'s merge-authorization path. The hunt record's
  own live reproduction (same file, "### Observed" codefence) shows
  `required_verification_missing()` returning an identical result
  before and after a new, unobserved head sha is minted, so a stale
  pre-rebase observation record silently continues to satisfy the
  check.
rationale: The requirement's narrow literal clause (the rebase operation itself never issues a merge command) is Present, but the broader guarantee the acceptance text is actually protecting — that a rebase cannot let a merge proceed without fresh review of the rebased head — is not enforced by any code in evaluate()'s call graph; the mechanism this record's own first draft (and the implementation record it trusted) cited as the enforcement point (the per-sha use_when.trigger) governs a different decision (spawn recommendation) and does not gate merges. Per conformance-review-verdict-assignment rule 1, this is Surface, not Present: matching vocabulary (a per-sha condition, execution-observation records) exists in the codebase, but it does not fire on the actual condition the requirement names (blocking a merge). Not Incorrect (rule 2) — merge_gate.py does not actively contradict the requirement, it silently omits a sha check that predates this PR and that this PR's diff does not touch. This is a real, if narrow, gap: a mechanical rebase can let a stale pre-rebase observation ride through evaluate() for a never-reviewed head sha. See "## Open findings" item 1 below.
---

## Open findings

1. **A before-landing warrant-hunt caught a real miscitation in this
   record's own first-draft evidence for requirement 5b, corrected
   above.** canonical: `docs/issue-2403/reports/conformance-review/2026-08-26-hunt-conformance-review-issue-2403.md`
   "## before-landing — stance 0" section (this session) — the first
   draft of requirement 5b's evidence (and, before that, the
   implementation record's own "## Why" section) claimed the
   execution-observation spec's per-sha `use_when.trigger` "already
   requires a fresh execution-observation record before evaluate()'s
   required_verification_missing() check ... stops blocking a merge on
   the new sha." That claim does not hold: `required_verification_missing()`
   (`a6ffa970:gates/spawn_on_pr.py:70-74`'s `applicable_roles()`) is
   presence-only — `[r for r in roles if r not in subject_board]` — and
   never compares a record's cited sha against the current PR head; the
   per-sha trigger it was attributed to is consumed only by
   `a6ffa970:gates/roles_due.py`, a separate spawn-recommendation
   evaluator never imported by `merge_gate.py`. The hunt record's own
   live reproduction (same section, "### Observed" codefence) shows
   `required_verification_missing()` returning an identical result
   before and after a new, unobserved head sha is minted. Requirement
   5b's verdict above has been changed from the first-drafted Present
   to Surface to reflect this — see 5b's evidence/rationale above for
   the full correction. Resolution path: none required of this PR —
   `merge_gate.py`'s presence-only check predates this PR and is
   untouched by its diff (see requirement 5a above); a genuine fix
   (sha-scoping `required_verification_missing()`/`board()`) would be a
   new, separate feature, out of scope for the mechanical-rebase
   operation this issue asks for. Flagged here so a reader of this
   record does not inherit the same false sense of protection this
   record's own first draft briefly asserted.
2. **3b's CHANGES-round token-cost table is real but misattributes one
   of its four cases, materially understating the total — corrected
   above.** The prior round's Absent verdict on 3b (no literal
   token-count number existed at all) is superseded: `4ce7a99a` added
   a genuine per-turn `usage`-object summation, independently
   reproduced this session for three of the four cited transcripts.
   But the fourth (#2383/PR #2389) cites a session that was cut off by
   a five-hour rate limit before it ever landed the rebase fix
   (canonical: that session's own `rate_limit_event` payload and
   `events.jsonl` `session-end: errored`, this session, cited in full
   under 3b's evidence above) — the session that actually performed
   and landed the rebase is a different, later transcript
   (`...20260825T200525.942845.log`) this session identified and
   independently summed at 67,539,728 tokens versus the 3,594,684 the
   table reports for that row, pulling the true four-incident total to
   roughly 77,987,069 tokens against the reported 14,042,025.
   Resolution path: for this PR's own acceptance compliance, none
   required beyond correcting the citation and the total in the
   implementation record — the underlying claim the issue cares about
   (mechanical rebase costs order-of-magnitude less than a role
   session) is, if anything, more strongly true at the corrected
   total, not less; but the record as currently committed states a
   materially wrong number for one historical incident and should be
   corrected before this requirement can verdict Present. The
   wall-clock side of the same check (3a) is unaffected and remains
   Present, independently reproduced above.
3. **Housekeeping noise in the diff, not a coded acceptance item.**
   `a6ffa970` includes 141 added lines in `.orchestrate-hook-fires/unknown.log`
   and roughly 50 deletions of one-line `consult-log` files — derived:
   `git diff main issue-2403-implementation-ref --stat` (survey citation,
   this session) — operational session artifacts incidental to the
   branch that produced this PR, not part of the implementation
   record's own `code_under_review` list. Resolution path: none
   required — not a defect against any of the 8 requirement items
   above; worth trimming before merge as ordinary housekeeping, not a
   blocking finding.
4. **Cosmetic count mismatch in the phase-1 survey's own skill-verdict
   line.** `docs/issue-2403/reports/conformance-review/survey.md` (sha
   `80044a0f`) "## Skill verdicts" — derived: reading that line this
   session — states the extraction split the acceptance bullets into
   "9 one-obligation line items" (survey's own count, unverified by
   this session beyond quoting it verbatim). derived: counting the
   survey's own "## Requirement extraction" list this session gives
   1a, 1b, 2, 3a, 3b, 4, 5a, 5b — 1+1+1+1+1+1+1+1 = 8, not the survey's
   own quoted 9. This record's own frontmatter `test:` field and
   "## Findings" header above use the session-counted total (8).
   Resolution path: none required — does not change any of the 8
   verdicts rendered above or below; a one-word fix in the survey's own
   skill-verdict line (its "9" corrected to match an 8-item count) would
   remove this cosmetic mismatch but is not required for any acceptance
   item to pass or fail.

## Next steps

None required for this review itself — it is read-only
(`conformance-review-finding-record`: this skill never fixes or patches
what it finds). `loop_state` set to `reported`, terminal for this
record. Overall `result`/`verdict: failed` per EARL worst-case
recomputation (`a6ffa970:roles/specs/execution-observation.spec.json:26-29`)
— derived: counting the 8 verdict blocks under "## Findings" above
(re-derived this session after the CHANGES round updated 3b), 6
verdict Present (1a, 1b, 2, 3a, 4, 5a), 1 verdict Surface (5b), and 1
verdict Incorrect (3b) — 6+1+1=8, same total as before the CHANGES
round; only 3b's own verdict value changed, from Absent to Incorrect.
Per this same PR's own new `blocking_cause_convention` (finding 4
above), this record notes explicitly that 3b's Incorrect verdict is a
real-but-misattributed measurement in the CHANGES round's own new
evidence (one of four cited transcripts is not the session that
performed the incident's rebase — see 3b's evidence and "## Open
findings" item 2 above) and 5b's Surface verdict traces to a
different, presence-only check that this PR's diff does not touch,
per requirement 5a's evidence above (`git diff main
issue-2403-implementation-ref -- gates/merge_gate.py`, this session,
showing only the `refs=None` kwarg addition, no change to
`required_verification_missing()` itself). This PR's own new code —
the staleness probe (1a, 1b), the mechanical rebase operation itself
(2), and the distinct-expression annotation (4) — all verdict Present;
`result: failed` is unchanged by this round both before and after
3b's correction, since 5b's Surface verdict alone already drives the
worst-case recomputation to `failed`.

## Skill verdicts

skill-verdict: conformance-review-verdict-assignment — applied: invoked; canonical: requirement 3b's, requirement 4's, and requirement 5b's evidence blocks above, this session (3b re-rendered this CHANGES-round re-review; 4 and 5b carried forward from the prior round, unaffected by this round's diff). Assigned Incorrect, not Absent or Present, to requirement 3b this round per rule 2 — the CHANGES round's new token-cost table is a real, present measurement mechanism (not missing, so not Absent) but one of its four cited transcripts actively misattributes a rate-limited, non-landing session to an incident whose actual rebase ran in a different transcript, understating that case ~18.8x and the reported total ~5.6x (not merely incomplete, so not Present) — see 3b's evidence for the re-derivation. Named the specific failing clause per rule 5 (the #2383/PR #2389 row's transcript citation, not the summation mechanism or the other three rows) and re-checked the claim once against `gh pr view`/`gh api graphql` commit timestamps and both candidate transcripts' own event logs before finalizing, per rule 6. Assigned Present, not Surface, to requirement 4 per rule 1 — the `blocking_cause` field and its convention text are both real and reachable by any reader of the spec file, not merely present-but-unreachable code. Assigned Surface, not Present, to requirement 5b per rule 1, correcting this record's own first draft after a before-landing warrant-hunt (see "## Open findings" item 1): a per-sha condition with the requirement's vocabulary exists in the codebase but does not fire on the actual merge-authorization path.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; canonical: the file:line citations under every requirement block above, this session, including this round's re-derivation of requirement 3b's evidence against `cabbfa86`. Pinned every evidence citation to `a6ffa970:<path>:<line-range>` (the PR head sha) or, for 3b, to the specific transcript file and event-log entry it was drawn from, re-derived directly this session rather than trusted from the CHANGES round's own pasted script output, per rule 1; recorded separate evidence lines for `merge_gate.py` and `verdict_gate.py` under requirement 1a where the evidence genuinely spans both files, per rule 2.
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; canonical: 3b's evidence block above, this session. Treated `4ce7a99a`'s own token-cost table as a claim to independently re-derive rather than a settled fact per rule 1 — re-summed all four cited transcripts with a freshly written script rather than citing the CHANGES commit's pasted output, per rule 3 (re-derive rather than cite stale). Deliberately went one step further than confirming the sums were real (the narrow ask): per rule 4, did not stop looking once three of four rows checked out clean, and cross-matched all four rows' transcript spans against live `gh pr view`/`gh api graphql` commit timestamps — an edge-case check (rule 2) beyond the happy-path "is this a real sum" question — which is what surfaced the #2383 row's wrong-session mismatch a purely arithmetic re-check would have missed (a real sum of the wrong file passes an arithmetic check).
skill-verdict: conformance-review-finding-record — applied: invoked; canonical: the 8 `---`-delimited requirement blocks under "## Findings" above, this session. Wrote all 8 blocks with the full field list (requirement, spec_ref, verdict, evidence, rationale), refusing none for missing evidence or spec_ref since every item had both; recorded the verdict solo, no user consult needed since every item's evidence was reachable from this session's own worktree, live `gh` calls, and direct file reads.
skill-verdict: conformance-review-requirement-extraction — applied: invoked; canonical: `docs/issue-2403/reports/conformance-review/survey.md`, sha `80044a0f`, "## Requirement extraction" section (phase 1, carried forward). The 8-item split above is unchanged from that section (see "## Open findings" item 3 above for a cosmetic count discrepancy in that survey's own skill-verdict line — the split itself is unaffected).
skill-verdict: conformance-review-verification-method-selection — applied: invoked; canonical: `docs/issue-2403/reports/conformance-review/survey.md`, sha `80044a0f`, "## Verification method selection" table (phase 1, carried forward). The method choice per item (Test/Demonstration/Analysis/Inspection) above is unchanged from that table.
other mounted skills: not triggered — `conformance-review-sampling-derivation` judged not-applicable in phase 1 (full enumeration of the PR's 6 touched files was feasible, survey sha `80044a0f`); `conformance-review-severity-classification` not-applicable — this review's scope was not explicitly extended into risk-weighting, and the one Absent finding (3b) is disclosed in-record with its own rationale under "## Open findings" rather than needing a severity band; `observability-phase-trace` not-applicable — this is a cross-family keyword match (skill-repository issue #2001) on this record's own "phase-1"/"phase-2" section vocabulary, not a substantive match: its actual scope is checking a phase-2 implementation's RED/USE observability signal set against the phase-1 methodology that named it for a given surface, and PR #2452 (staleness detection, mechanical rebase, `blocking_cause` annotation) contains no observability-signal surface for it to check.
