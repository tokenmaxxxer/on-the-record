---
code_under_review:
  - roles/specs/brand-design.spec.json
  - roles/specs/content-design.spec.json
  - roles/specs/market-analysis.spec.json
type: observation
loop_state: handed-off
---

kind: execution-observation
subject: issue-1160
Proposal: docs/issue-1160/proposals/execution-observation-step3-live-pilot.md

## Independence statement

This role did not author or edit the observed artifact this session.
canonical: gh pr view 1164 --json number,title,body,mergeCommit,commits,files
(read this session). The observed artifact is PR #1164 (branch
issue-1160/implementation), content commit
cd97d6bc1c0609ee0d93eb3efedbff72f65faa1e, merge commit
6baf542805576cd898b9e668fdf5f15a4d90a67e. Nothing under
roles/specs/brand-design.spec.json, roles/specs/content-design.spec.json,
roles/specs/market-analysis.spec.json, or
docs/issue-1160/reports/implementation.md was touched this session;
this record lives solely at docs/issue-1160/reports/execution-observation.md
and docs/issue-1160/reports/execution-observation/**.

## What was done

Read the observed role's actual artifacts (PR #1164, its content commit
cd97d6b, its own record docs/issue-1160/reports/implementation.md — all
via `git show`/`gh pr view`, canonical: docs/issue-1160/reports/execution-observation/current-state-survey.md
"What was read this session"), then attempted to exercise issue #1160
step 3's three-leg live pilot against what PR #1164 actually landed,
without re-executing any observed role's task and without editing any
observed role's src/test/docs path.

Leg 1 (detector fires on WITH-need, silent on WITHOUT-need): PR #1164
landed `need_detector` as a JSON string field only — canonical: git show
cd97d6b:roles/specs/brand-design.spec.json (full file read this
session), field `use_when.need_detector.condition`:
"the target project has UI source files (path_patterns: **/*.tsx,
**/*.jsx, **/*.vue, **/*.svelte) AND no design-tokens/*.json file
exists anywhere in the repo tree". No evaluator in this repository reads
`need_detector` — canonical: `grep -rn "need_detector" gates/ spawn.py
on-the-record/hooks/` run this session, zero hits; and
gates/roles_due.py's module docstring (read this session, lines 1-17)
scopes its board_condition evaluator to `use_when.trigger` only, a
field distinct from `use_when.need_detector` that none of the three
pilot specs carry. Because no evaluator exists to invoke, this session
hand-implemented the stated predicate verbatim as a throwaway shell
check (never committed to this repo, run only against /tmp scratch
fixtures, no repository path touched) and applied it to two fixture
directories built this session: /tmp/tmp.bxofRmMPvi/with-need (one
.tsx file, no design-tokens/) and /tmp/tmp.bxofRmMPvi/without-need (one
.tsx file, plus design-tokens/colors.json).

canonical: this session's own derived shell commands (reproduced
below), run against the /tmp fixtures built this session.
```
$ find with-need -regex '.*\.\(tsx\|jsx\|vue\|svelte\)$' | wc -l   # 1
$ find with-need -path '*design-tokens/*.json' | wc -l              # 0
  -> predicate fires (YES) on with-need
$ find without-need -regex '.*\.\(tsx\|jsx\|vue\|svelte\)$' | wc -l # 1
$ find without-need -path '*design-tokens/*.json' | wc -l           # 1
  -> predicate stays silent (NO) on without-need
```
canonical: same derived commands above. This confirms the prose
predicate as written is internally consistent and produces the
false-positive bound its own text claims on these two fixtures — it
does not confirm "the landed detector fires" in the machinery sense,
because no landed, code-invoked detector exists to fire (see the
step-level finding below).

Leg 2 (a pilot role session wakes and lands its mission deliverable):
not exercisable. canonical: gates/role_spec_shape.py lines 14, 26,
84-86 (read this session) — it only validates that
`use_when.board_condition` is a non-empty string; it does not evaluate
or act on it. No mechanism in this repository wakes a role from
`use_when.need_detector` or `use_when.board_condition` on a target
project (canonical: grep -rn "need_detector" gates/ spawn.py
on-the-record/hooks/, zero hits, run this session). No brand-design/
content-design/market-analysis session was spawned this session, and
none of their `mission_deliverables` artifacts (e.g. brand-design's
`design-tokens/*.json` palette+type scale) exist anywhere in this
repository or on any open branch — canonical: `find . -path
'*/design-tokens/*.json'` run this session, zero hits outside the spec
text itself. This role does not spawn peer roles on its own initiative
(SCOPE-EXCEEDED rule) even to close this gap.

Leg 3 (a different role records the #1156-pattern bar verdict): not
exercisable, downstream of leg 2 — there is no landed deliverable for
any role to grade. `verified_by` (e.g. brand-design's
"ux-engineering") is likewise unconsumed by any code — canonical:
`grep -n "mission_deliverables\|verified_by" gates/quality_bar.py` run
this session, zero hits — and no #1156-pattern bar verdict record
citing any of the three pilot roles' `mission_deliverables` exists
anywhere under docs/ — canonical: `grep -rl "mission_deliverables"
docs/` run this session, hits confined to this issue's own paperwork
(docs/issue-1160/reports/**, docs/issue-1160/proposals/**).

## Why

- upstream: docs/issue-1160/proposals/execution-observation-step3-live-pilot.md
- basis: docs/issue-1160/reports/execution-observation/current-state-survey.md
- reason: issue #1160 step 3 requires this role to record, with
  executed-live provenance, whether the three-leg live pilot actually
  runs against what PR #1164 landed — and to state plainly, per leg,
  when it cannot be run, rather than claim it.

## Verdict — outcome

acceptance: `find with-need -path '*design-tokens/*.json'` /
`find without-need -path '*design-tokens/*.json'` (executed this
session against the /tmp fixtures above) — result: leg 1's predicate is
the only leg of the three with any executable surface at all.
acceptance: `grep -rn "need_detector" gates/ spawn.py
on-the-record/hooks/` (executed this session) — result: zero hits, so
legs 2 and 3 have no wake call, spawn, or verifier invocation anywhere
in the repository to run.

Outcome verdict: FAIL, per the spec's recomputation rule (worst case
across the cited step-level results below, canonical: the three
"Verdict — step" entries below, this session, each with its own
canonical grep/read citation). canonical: git show cd97d6b:docs/issue-1160/reports/implementation.md
("Rationale for deviations" section, read this session) — PR #1164's
own record states the live pilot was never run in its own session:
"no live pilot run ... was performed in this session". Issue #1160's
step-3 acceptance ("live pilot — ... one pilot role wakes on its
detector and lands its actual deliverable, and a different role
records the #1156 bar verdict on it", provenance: executed-live) is
unsatisfied by anything landed in PR #1164 as of commit cd97d6b.

## Verdict — trajectory

Sound for what it covered, not for step 3. canonical:
docs/issue-1160/reports/requirements-engineering/scout-brief.md and
docs/issue-1160/reports/requirements-engineering/current-state-survey.md
(both referenced from implementation's own record's "Why" section, read
this session) — implementation's phase-1→phase-2 path scouted and
surveyed before proposing, and got real human approval via the
exact-match "APPROVE issue-1160/implementation" issue comment
(canonical: gh issue view 1160 --json comments, read this session).
Its own record is also explicit and non-evasive about the gap it left
(its "Rationale for deviations" section, same commit) rather than
silently claiming the live pilot ran.

## Verdict — step

- subject: `roles/specs/brand-design.spec.json` `use_when.need_detector`
  field (canonical: git show cd97d6b:roles/specs/brand-design.spec.json,
  read this session)
  test: is the detector condition invoked by any evaluator on a real
  target project, mechanically, the way `use_when.trigger` is by
  gates/roles_due.py?
  result: absent (the field exists as declarative text; no evaluator
  reads it — canonical: grep -rn "need_detector" gates/ spawn.py
  on-the-record/hooks/, zero hits, this session)
  assertedBy: execution-observation (this record)

- subject: `roles/specs/{brand-design,content-design,market-analysis}.spec.json`
  `mission_deliverables` / `verified_by` fields
  test: does any code path check a landed deliverable against
  `mission_deliverables.fit_criterion` or record a `verified_by`
  bar-verdict?
  result: absent (canonical: grep -n "mission_deliverables\|verified_by"
  gates/quality_bar.py, zero hits, this session)
  assertedBy: execution-observation (this record)

- subject: brand-design `need_detector.condition` prose predicate,
  hand-applied to /tmp scratch fixtures this session (not a repository
  path)
  test: does the stated predicate fire on a WITH-need fixture and stay
  silent on a WITHOUT-need fixture, as its own false_positive_bound
  claims?
  result: present, but only as a manually-reproduced text predicate —
  canonical: this session's own derived commands above (fires YES on
  with-need, NO on without-need)
  assertedBy: execution-observation (this record)

## Blameless finding: step-3 live-pilot machinery gap

- impact: issue #1160's step-3 acceptance (executed-live provenance)
  cannot be satisfied by anything currently in the repository — the
  detector, the wake path, and the bar-verdict path are all
  unimplemented; only spec-text fields exist (canonical: the three
  step-level results above).
- timeline: canonical: git show cd97d6b:docs/issue-1160/reports/implementation.md,
  read this session. Gap present since PR #1164 merged (merge commit
  6baf542805576cd898b9e668fdf5f15a4d90a67e); confirmed unresolved as of
  this session (2026-08-13, this session's own greps above).
- root cause: PR #1164's approved phase-1 proposal froze a write set of
  exactly the three spec files plus docs/specs/reconciled-index.md
  (canonical: git show cd97d6b:docs/issue-1160/reports/implementation.md,
  "Rationale for deviations" — the write set explicitly excluded any
  evaluator/test file), so no executable detector, spawn-wiring, or
  verifier code was ever in scope for that build.
- action item: a follow-up implementation proposal must add (a) a
  `need_detector` evaluator analogous to gates/roles_due.py's
  `use_when.trigger` handling, (b) the wake path that spawns a pilot
  role session when it fires, and (c) a `mission_deliverables`/
  `verified_by` check in gates/quality_bar.py (or equivalent) before
  step 3's acceptance can be re-attempted with executed-live
  provenance. Owner: implementation role, next issue-1160-linked
  session; no deadline stated in the issue (canonical: gh issue view
  1160, this session).

## Open findings

1. (see Blameless finding above) — step-3 live-pilot machinery does not
   exist; outcome verdict is FAIL until it is built.

## Next steps

Per this role's own directive (a role session never files an issue or
spawns a peer role on its own initiative): report this finding plainly
in the session reply for the human to decide whether to open a
follow-up issue for the evaluator/wake/verify machinery.

## Resolution path

Human reviews this record's open finding, and either authorizes a
follow-up implementation proposal scoped to the three machinery pieces
named in the action item, or explicitly accepts the current spec-only
state and closes step 3 as descoped.

## What did not work

- Attempted first to treat the hand-applied /tmp predicate check as
  evidence that "the detector fires" in the machinery sense issue #1160
  step 3 asks for; on reflection this conflates a manually reproduced
  text predicate with landed, invoked code — corrected by scoping the
  leg-1 finding narrowly ("prose predicate is internally consistent,"
  not "the landed detector fired") rather than claiming the full leg.
