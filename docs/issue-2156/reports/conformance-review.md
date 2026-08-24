---
issue: 2156
role: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2156/reports/conformance-review/survey.md
    sha: fca59e11daa6e8ce80a5282d917e5122805bd423
  - path: docs/issue-2156/proposals/conformance-review.md
    sha: fca59e11daa6e8ce80a5282d917e5122805bd423
  - path: docs/issue-2156/reports/conformance-review/deviation-log.md
    sha: cddc026a5769890491ee48c6c87899ef123f2772
subject: commit b47a2abf3a4b28e54303b15bd4f660870fbef8da
  (on-the-record/directive/spawn-and-board.md; PR #2157, squash-merged
  to main)
test: issue #2156 body (`## Change`/`## Acceptance`), decomposed into
  R1..R8 (docs/issue-2156/reports/conformance-review/survey.md,
  "Requirement list" section)
result: passed
assertedBy: issue-2156/conformance-review session (role-handoff contract v3)
---

# issue-2156 — conformance-review record

## What was done

Audited `on-the-record/directive/spawn-and-board.md` at
`b47a2abf3a4b28e54303b15bd4f660870fbef8da` against the 8 requirements
the phase-1 survey extracted from issue #2156's own `## Change`/`##
Acceptance` text, re-deriving every verdict directly against the
artifact this session rather than reusing
`docs/issue-2156/reports/implementation.md`'s own self-assessment.

canonical: acceptance: `grep -n "NO REDUNDANT WATCHER" on-the-record/directive/spawn-and-board.md` — result: PASS (1 match; R8 finding below). Combined with R1-R7's own `Present` verdicts (this session's measurement), the worst-case recomputation per `roles/specs/conformance-review.spec.json`'s `recomputation` rule is `passed`.

One Open Finding is recorded outside the R1-R8 set, per the approved
proposal's scope split (below).

## Why

The approved proposal's Rationale rejected trusting
`docs/issue-2156/reports/implementation.md`'s own pasted grep as
sufficient on its own — this role's `conformance-review-verdict-assignment`
skill requires evidence the review session itself re-derived. Every
citation below is this session's own read or command execution against
the artifact, not a copy of the implementer's account.

## Findings

---
requirement: no new file created; guidance added to an existing directive file (R1)
canonical: `git show b47a2abf --stat` — executed this session, output below (executed-unit).
spec_ref: issue #2156 body, `## Change`, sentence 1
verdict: Present
evidence: `b47a2abf:on-the-record/directive/spawn-and-board.md:34-53`
rationale: canonical fence, this session:
```
$ git show b47a2abf --stat
 docs/issue-2156/reports/implementation.md          | 128 +++++++++++++++++++++
 .../2026-08-24-hunt-spawn-watcher-guidance.md      |  33 ++++++
 .../reports/implementation/deviation-log.md        |  17 +++
 on-the-record/directive/spawn-and-board.md         |  20 ++++
 4 files changed, 198 insertions(+)
```
canonical: fence directly above (executed-unit, this session) —
`spawn-and-board.md` is a modification to an existing file (20 lines
added, no new blob), and no second directive file was created.

---
requirement: forbids spawning a separate watcher Agent to poll a spawn to completion (R2)
canonical: `on-the-record/directive/spawn-and-board.md:34-37`, read directly this session.
spec_ref: issue #2156 body, `## Change`, sentence 2, clause 1
verdict: Present
evidence: `b47a2abf:on-the-record/directive/spawn-and-board.md:34-37`
rationale: lines 34-37 read "do not build a separate standing watch
  loop for that spawn by ANY means — not a separate Agent
  (general-purpose or otherwise) whose sole job is to poll it to
  completion". Names "Agent" and "poll it to completion" verbatim.

---
requirement: names the mechanism reason (watcher process + poll cycle already surfaces events) (R3)
canonical: `on-the-record/directive/spawn-and-board.md:48-50`, read directly this session.
spec_ref: issue #2156 body, `## Change`, sentence 2, clause 2
verdict: Present
evidence: `b47a2abf:on-the-record/directive/spawn-and-board.md:48-50`
rationale: lines 48-50 read "the spawn's own watcher process plus the
  `spawn.py watch`/`--follow` poll cycle already surface
  HEALTHY/RUNNING/anomaly/returned-PR events as notifications to this
  session automatically" — names both the mechanism and the event
  vocabulary the requirement specifies.

---
requirement: directs to trust and act on those notifications (R4)
canonical: `on-the-record/directive/spawn-and-board.md:50`, read directly this session.
spec_ref: issue #2156 body, `## Change`, sentence 2, clause 3
verdict: Present
evidence: `b47a2abf:on-the-record/directive/spawn-and-board.md:50`
rationale: line 50 reads "Trust those and act on them when they
  arrive;" — literal imperative matching the requirement's wording.

---
requirement: permits a one-shot fallback via `spawn.py ps` / `spawn.py watch --issue <n> --role <r>` (R5)
canonical: `on-the-record/directive/spawn-and-board.md:50-52`, read directly this session.
spec_ref: issue #2156 body, `## Change`, sentence 3
verdict: Present
evidence: `b47a2abf:on-the-record/directive/spawn-and-board.md:50-52`
rationale: lines 50-52 read "the only sanctioned direct status checks
  are a one-shot `spawn.py ps` or `spawn.py watch --issue <n> --role
  <r>` call" — both commands named verbatim as sanctioned.

---
requirement: states the one-shot check is the only sanctioned direct check — never a standing watcher agent (R6)
canonical: `on-the-record/directive/spawn-and-board.md:34-53`, read directly this session.
spec_ref: issue #2156 body, `## Change`, sentence 3, negative clause
verdict: Present
evidence: `b47a2abf:on-the-record/directive/spawn-and-board.md:34-53`
rationale: line 34 carries the "NO REDUNDANT WATCHER, BY ANY MECHANISM"
  heading; lines 38-43 generalize the prohibition beyond Agent to "a
  substitute with the same shape, such as a backgrounded
  `Bash(run_in_background: true)` sleep-and-poll loop, a cron/schedule
  entry, or any other mechanism"; lines 51-53 state "never a standing
  loop of any kind" — stricter than the bare requirement (any-mechanism,
  not Agent-only), satisfying it a fortiori.

---
requirement: docs-only — no code/gate change (acceptance criterion 2) (R7)
canonical: R1's `git show b47a2abf --stat` fence above (executed this session).
spec_ref: issue #2156 body, `## Acceptance`, bullet 2
verdict: Present
evidence: R1's `git show b47a2abf --stat` fence above
rationale: canonical: R1's fence above, this session — all 4 changed
  paths are under `docs/issue-2156/` or `on-the-record/directive/`;
  none is a `.py`/`.sh`/`gates/*` path.

---
requirement: executed acceptance evidence — grep shows the guidance text present (acceptance criterion 3) (R8)
canonical: acceptance: `grep -n "NO REDUNDANT WATCHER" on-the-record/directive/spawn-and-board.md` — result: PASS (1 match), executed this session (output below).
spec_ref: issue #2156 body, `## Acceptance`, bullet 1 and "Executed acceptance evidence" line
verdict: Present
evidence: `on-the-record/directive/spawn-and-board.md:34` at current `HEAD` (a descendant of `b47a2abf`, unchanged since)
rationale: independent Test-method re-run per
  `conformance-review-verification-method-selection` rule 4 (not reused
  from the implementer's own pasted output):
```
$ grep -n "NO REDUNDANT WATCHER" on-the-record/directive/spawn-and-board.md
34:  NO REDUNDANT WATCHER, BY ANY MECHANISM (issue #2156): after `spawn.py`
```
canonical: fence directly above (executed-unit, this session) — a
match, satisfying the acceptance check verbatim, independently of
`docs/issue-2156/reports/implementation.md`'s own copy of the same
command.

## Upstream basis

- `docs/issue-2156/reports/conformance-review/survey.md`, sha
  `fca59e11daa6e8ce80a5282d917e5122805bd423` — requirement extraction
  (R1-R8) and the PR-trailer/still-open observation this record's
  Findings and Open findings sections build on.
- `docs/issue-2156/proposals/conformance-review.md`, sha
  `fca59e11daa6e8ce80a5282d917e5122805bd423` — the approved phase-1 proposal.
  canonical: this session's own measurement — the Findings section above
  (R1-R8) uses exactly the methods and scope split the proposal planned
  (Inspection R1-R7, Test R8, one Open Finding outside the requirement
  set); no divergence from the plan occurred this session.
  canonical: `gh issue view 2156 --json comments -q '.comments[] | .author.login+": "+.body'` — executed this session, output below (executed-unit):
  ```
  $ gh issue view 2156 --json comments -q '.comments[] | .author.login+": "+.body'
  JiwonJung94: [watch] issue-2156/implementation: ...
  JiwonJung94: [watch] issue-2156/conformance-review: ...
  JiwonJung94: APPROVE issue-2156/conformance-review
  ```
  canonical: fence directly above (executed-unit, this session) — the
  last line matches `APPROVE issue-2156/conformance-review` exactly
  (contract v3 s19 string-equality gate); `JiwonJung94` is listed in
  `docs/specs/approvers.md`, read this session.
- `docs/issue-2156/reports/conformance-review/deviation-log.md`, sha
  `cddc026a5769890491ee48c6c87899ef123f2772` — this role's own
  phase-1-subtree deviation log, carried forward for traceability; no
  new deviation in this phase-2 session.
- canonical: `gh pr view 2157 --json state,mergeCommit -q '.state,.mergeCommit.oid'` — executed this session, output below (executed-unit) — commit `b47a2abf3a4b28e54303b15bd4f660870fbef8da` merged to `main` via PR #2157:
  ```
  $ gh pr view 2157 --json state,mergeCommit -q '.state,.mergeCommit.oid'
  MERGED
  b47a2abf3a4b28e54303b15bd4f660870fbef8da
  ```

## Open findings

1. PR #2157's body ends with a plain `#2156` reference (no
   `Closes`/`Fixes`/`Resolves` keyword), and issue #2156 remains `OPEN`
   despite `b47a2abf` already landing on `main`. Not scored against
   R1-R8 — issue #2156's own `## Acceptance` text names none of this.
   canonical: `gh pr view 2157 --json body -q .body` and `gh issue view 2156 --json state -q .state` — executed this session, output below (executed-unit):
   ```
   $ gh pr view 2157 --json body -q .body
   ...
   #2156
   $ gh issue view 2156 --json state -q .state
   OPEN
   ```
   canonical: fence directly above (executed-unit, this session), plus
   `docs/reports/deviation-log.md` read this session — its tail entries
   dated `2026-08-24T05:05:09Z` (issue-2153) and
   `2026-08-24T14:30:00Z` (issue-2152) both note `pr-preflight.sh`
   forces a plain `#<n>` reference under the `CORE_BUILD_NOW=1` bypass
   because no real human-authored approval comment exists at PR-open
   time to authorize a `Closes` trailer; no matching entry exists yet
   for issue-2156. Resolution path: whichever role/human next writes to
   `docs/reports/deviation-log.md` (outside this role's `write_scope`)
   should add a matching entry.
   canonical: the `gh pr view 2157` fence above this bullet (executed-unit,
   this session) shows `state: MERGED` — separately, whoever closes out
   issue #2156 should close it on GitHub to match that state.

## Next steps

None needed from this role or branch — `loop_state` above is already
this record kind's terminal value, `reported`.
canonical: `roles/specs/conformance-review.spec.json`'s `loop_state.terminal` field, read this session — lists `reported` as the sole terminal value.
The Open Finding above names its own resolution path and owner for
whoever picks it up next.

## What did not work

Nothing — this session's re-derivation matched the approved proposal's
plan; every requirement kept the method and scope the proposal set out.

## Skill verdicts

skill-verdict: conformance-review-verification-method-selection —
applied: invoked; loaded this session before executing R8's independent
grep (rule 4 — Test method, not re-deriving a fresh manual check where
the acceptance criterion already names an executable check) and before
treating R1-R7 as Inspection (rule 1 — structural text-presence).
canonical: R1-R8 finding blocks above, this session.

skill-verdict: conformance-review-verdict-assignment — applied:
invoked; loaded this session to confirm every requirement's evidence
shows the guidance both present and reachable (the directive file's own
header states it is loaded via the always-on index, so `Present` rather
than `Surface` applies per rule 1) before rendering the 8 verdicts.
canonical: R1-R8 finding blocks above, this session.

skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; loaded this session; every evidence citation above pins a
`sha:path:line` pointer against `b47a2abf`, not a bare path, per rule 1.
canonical: R1-R8 finding blocks above, this session.

skill-verdict: conformance-review-finding-record — applied: invoked;
loaded this session before writing the Findings section above; its
field list (`requirement`/`spec_ref`/`verdict`/`evidence`/`rationale`)
shaped every block, one per R1..R8.
canonical: R1-R8 finding blocks above, this session.

other mounted skills: not triggered — conformance-review-requirement-extraction
was the phase-1 session's job
(`docs/issue-2156/reports/conformance-review/deviation-log.md` already
carries its skill-verdict line from that session);
conformance-review-sampling-derivation (full enumeration of R1-R8 was
feasible at this size) and conformance-review-severity-classification
(no severity-weighting was requested) stay `not-applicable` this
session too.
