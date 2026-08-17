---
code_under_review:
  - on-the-record/hooks/directive.sh
  - gates/test_scope_option_directive.py
type: observation
loop_state: phase-2-complete
---

Subject: issue-1707

## Independence statement

This session did not author or edit on-the-record/hooks/directive.sh,
gates/test_scope_option_directive.py, or the observed role's own record
on branch issue-1707/implementation — all read-only this session. No
edits were made under the observed role's src/, test/, or
docs/issue-1707/ paths outside this record.

## What was done

Read PR #1711's full diff, its two commits, its body, issue #1707's body
and its approval comment, and docs/specs/approvers.md; independently
reproduced the observed role's asserted test result by copying the
committed directive.sh and test file into a scratch tree and running the
test there; rendered a three-level phase-2 verdict (outcome/trajectory/
step) on PR #1711 without re-executing any of its code in place or
editing any of its files.

## Scope

canonical: `gh pr view 1711 --json number,title,body,commits,files,reviews,state,url` (executed this session)
Observing PR #1711 ("feat(issue-1707): scope-option proposal directive"),
commit 8e35cd609a4a4ef572899e252036f30b7e5d6944 (directive block + unit
test) and commit e0d534ef089ac5281e548a4f6237dcdc48a8828a (implementation
record). canonical: same command, `state` field, read this session — its
value is OPEN (not yet merged) as of this read.

canonical: `gh pr list --head issue-1707/implementation --state all` (executed this session)
PR #1711 is the sole PR from `issue-1707/implementation`; it is the
phase-2 delivery observed here (this repo's build-now/single-PR flow for
this subject carries no separate proposal-round PR).

canonical: `gh issue view 1707` (executed this session)
Issue #1707's body carries the acceptance criteria quoted throughout this
record.

What was read to arrive at this scope: the diff of PR #1711
(`gh pr diff 1711`, full file, executed this session), the PR's commit
list and body (`gh pr view 1711 --json ...`, executed this session), the
issue body/acceptance criteria, and the issue's comment thread
(`gh issue view 1707 --json comments`, executed this session). The
observed role's own record narrative (on branch issue-1707/implementation,
path docs/issue-1707/reports/implementation.md, not present on this
branch's tree) was read via `gh pr diff 1711` after the diff and commits,
per FRESH-EYES ORDERING.

DIFF-SCOPE: on-the-record/hooks/directive.sh hunk read in full — the
entire inserted "SCOPE-OPTION PROPOSAL (issue #1707)" bullet
(on-the-record/hooks/directive.sh:266-284 in the diff, the only hunk this
PR touches in that file); the new test file added by this PR (path
gates/test_scope_option_directive.py, not present on this branch's own
tree, read via `gh pr diff 1711`) read in full as a wholly new file. All
step-level citations below fall inside these read hunks.

## Phase 2 verdict

### Outcome

canonical: `gh pr diff 1711` (executed this session, full diff read)
Recomputed across the step-level results below (worst case), the outcome
is **met**.

- Acceptance check 1 (trigger subclass + non-overlap statement + option
  block form + neutrality rule, asserted by a unit test):
  canonical: `gh pr diff 1711` — on-the-record/hooks/directive.sh:266-284, read
  this session — states the trigger subclass ("BOTH design-bearing ...
  AND scope-ambiguous"), the non-overlap statement ("Every other vague
  ask ... keeps REQUIREMENT ELICITATION's open-question path above
  unchanged"), the option-block form ("exactly 2 or 3 options, ordered
  by ascending scope size ... \`scope:\`, \`cost:\`, \`risk:\`,
  \`non-goals:\`"), and the neutrality rule ("the literal token
  \`recommended\` (case-insensitive, any substring match) MUST NOT
  appear anywhere inside the option block") verbatim (mode: read).
- Acceptance check 2 (per-option consult-trace citation, asserted by the
  same test):
  canonical: `gh pr diff 1711` — on-the-record/hooks/directive.sh:266-284, read
  this session — the option-block form includes a `consult-trace:` field
  whose text is "cites the validity/risk consult ref the option's
  alternatives/tradeoffs were drawn from" (mode: read).
- Execution leg, independently reproduced this session (mode: command):
canonical: command run this session, transcript below — this session's
own live execution against the observed commit's tree, not a read of the
PR's pasted claim.
```
$ git show origin/issue-1707/implementation:gates/test_scope_option_directive.py > /tmp/t.py
$ git show origin/issue-1707/implementation:on-the-record/hooks/directive.sh > /tmp/directive.sh
$ mkdir -p /tmp/otr_check/on-the-record/hooks /tmp/otr_check/gates
$ cp /tmp/directive.sh /tmp/otr_check/on-the-record/hooks/directive.sh
$ cp /tmp/t.py /tmp/otr_check/gates/test_scope_option_directive.py
$ cd /tmp/otr_check && python3 gates/test_scope_option_directive.py
ok - t_states_consult_trace_per_option
ok - t_states_neutrality_rule_forbids_recommended_token
ok - t_states_non_overlap_with_1006_req4
ok - t_states_option_block_count_and_order
ok - t_states_option_fields
ok - t_states_trigger_subclass
6/6 passed
```
  canonical: transcript above, this session's own command run — this
  matches the count in PR #1711's own body (`gh pr view 1711 --json
  body`, read this session), and is independently reproduced by this
  session's own live run, not merely asserted from the PR's pasted
  claim.
- Empty-state check (precise asks and non-design-bearing vague asks
  untouched):
  canonical: `gh pr diff 1711` — on-the-record/hooks/directive.sh:266-284, read
  this session — the inserted block is a new bullet appended after the
  existing REQUIREMENT ELICITATION bullet, which the diff leaves
  unmodified (no `-` lines against that earlier bullet in this PR's
  diff); the new bullet's own text scopes itself to the strict subclass
  and states the non-overlap explicitly (mode: read).

canonical: transcript above, this session's own command run — no result
classifies as a failure. Unlike PR #1705 (issue-1702's precedent), this
PR's sole execution leg was independently reproduced this session rather
than only asserted from the observed role's pasted output.

### Trajectory

canonical: `gh pr view 1711 --json commits` (executed this session)
- scouted-when-required: PR #1711 carries two commits, 8e35cd60 (directive
  block + test) and e0d534ef (record only); there is no separate
  research/survey commit preceding 8e35cd60 on this branch. canonical:
  `gh issue view 1707`, read this session — the issue body itself states
  "## Refinements from validity consult (2026-08-17)" and names
  `validity-consult: spawn.py consult requirements-engineering
  2026-08-17` and `design-research: memory/research-first briefings
  2026-08-16` — the research/consult step is recorded as having happened
  upstream of this branch, in the issue body, not as a commit on this
  branch. canonical: `gh pr diff 1711` — the record file's own "Upstream
  / basis" section, read this session — cites the same issue-body
  refinements section as its basis. Check result: yes, on this evidence.
- surveyed-before-proposing: canonical: `gh pr diff 1711` file list,
  read this session — this subject shipped as a single build-now commit
  (8e35cd60) carrying both the directive text and the test in one
  commit, with no docs/issue-1707/proposals/ path in the diff's file
  list to compare a separate scope statement against. Check result: not
  applicable — this PR's flow (single implementation commit + record
  commit, no proposal-round artifact in the diff cited above) shows no
  separate proposal stage to check ordering against.
- approved-by-human: canonical: `gh issue view 1707 --json comments`
  (executed this session) — a comment whose entire body is exactly
  `APPROVE issue-1707/implementation`, posted by `JiwonJung94`, at
  2026-08-17T04:35:38Z, before the branch's commits (04:38:38 and
  04:39:59) and before the PR was opened (04:40:11). canonical: `cat
  docs/specs/approvers.md`, read this session — `JiwonJung94` is listed.
  canonical: `gh pr view 1711 --json commits`, read this session — PR
  author (JiwonJung94) and approver are the same account, so
  single-account mode applies and the exact-string test is satisfied.
  Check result: yes.

canonical: three checks above, this session's own reads — trajectory
summary: scouted-when-required and approved-by-human both check out as
described above; surveyed-before-proposing is not applicable under this
subject's single-commit build-now flow. No check was skipped silently.

### Step

canonical: `gh pr diff 1711` (executed this session, full diff read)
No step-level deficiency found.

- subject: on-the-record/hooks/directive.sh:266-284 (SCOPE-OPTION
  PROPOSAL block), test: does the inserted text state the trigger
  subclass, non-overlap statement, option-block form, and neutrality
  rule the issue's acceptance criteria name, result: matches, assertedBy:
  execution-observation (this session), mode: read. canonical: `gh pr
  diff 1711`, same hunk cited under Outcome above.
- subject: gates/test_scope_option_directive.py (new file added by this
  PR, path not present on this branch's own tree), test: do the test
  bodies (as written) assert the same obligations the directive text
  states, and does running them against the observed commit's tree
  produce all-ok output, result: matches, assertedBy:
  execution-observation (this session), mode: command. canonical:
  transcript under Outcome above, this session's own command run.
- subject: PR #1711 body's pasted test-count claim, test: does the
  observed role's own pasted output substantiate the execution leg,
  result: matches (independently reproduced, not merely asserted).
  canonical: transcript under Outcome above, this session's own command
  run, assertedBy: execution-observation (this session), mode: command.

## Open findings

None.

## Why

canonical: `gh issue view 1707`, `gh pr view 1711`, `gh pr diff 1711`
(all executed this session)
Per the role directive, this record judges whether PR #1711's
phase-1→phase-2 execution on issue #1707 was sound, by reading its own
diff, commits, and record, and by independently re-running its unit
test against the observed commit's tree, rather than re-executing the
observed role's task in place.

## Upstream

canonical: PR #1711 (commits 8e35cd609a4a4ef572899e252036f30b7e5d6944,
e0d534ef089ac5281e548a4f6237dcdc48a8828a), read this session

## Next steps

None — the phase-2 verdict is rendered and this record is final for this
observation.

## Resolution path

Not applicable: no open finding rose to a deficiency requiring
resolution.
