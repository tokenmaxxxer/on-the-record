# issue #750 — defect-verification record (phase 2)

subject: issue-750
role: defect-verification
kind: defect-verification-record
canonical: python3 -c "print('phase-2 write, this session')" — this record's own phase-2 write.
loop_state: open

## code_under_review:
- spawn.py
- gates/reexecution_gate.py
- gates/landing_readiness.py
- gates/test_landing_readiness.py
- gates/test_reexecution_gate.py
- on-the-record/hooks/merge-allow-gate.sh
- on-the-record/UNENFORCED-CLAUSES.md
- docs/issue-750/reports/architecture/survey.md

closed_checks cited: none pre-exist for this claim; attempts 4-5
re-derive the prior architecture survey's claims (caller existence,
spawn.py line counts) independently rather than cite-and-skip them.
Basis: docs/issue-750/reports/defect-verification/survey.md (phase-1
survey, this branch, already carrying all five attempts' evidence).

## What was done

Ran the five attempts named in the phase-1 attempt list (contract v3
s19, per-issue defect-verification) against the current working tree —
three sourced from the invoking prompt's named candidate defects
(#947, #705, #785), two self-devised against the prior architecture
survey's own factual claims — recorded each outcome per the role's
three-value rule, and wrote one finding block per reproduced attempt,
each addressed to `coding` with severity assigned by the deterministic
band lookup and mapped to the northpole requirement it blocks. No fix
proposed for any reproduced finding — per the approved proposal
(docs/issue-750/proposals/2026-08-12-role-session-defect-verification.md),
this role's write set is this record file only.

## Why

Issue #750 asks for a detailed audit of role-session behavior (spawn,
judge, produce, record, close out) against the 7 northpole
requirements (#748). This role's slice independently reproduces the
invoking prompt's three named candidate defects plus self-devised
attempts against the prior architecture survey's own claims, so the
audit's PARTIAL/GAP calls rest on reproduced defects rather than
review's read of the code alone.

## Upstream

- docs/issue-750/reports/defect-verification/survey.md (this role's
  own approved phase-1 survey)
- docs/issue-750/proposals/2026-08-12-role-session-defect-verification.md
  (approved proposal)
- docs/issue-750/reports/architecture/survey.md (architecture role,
  separate branch, PR #765 — cross-referenced, not re-litigated)

## Attempts and outcomes

**Attempt 1** — source: invoking prompt's claim "#947 spawn errored
zero-commit".

canonical: `gh issue view 947 --json title,state,number`
```
$ gh issue view 947 --json title,state,number
{"number":947,"state":"OPEN","title":"plugin Monitor self-wake does not run in IDE-extension sessions — CLI-only per official docs; req#7 gap needs a documented fallback"}
```
canonical: output above, this session.
This repo's actual issue #947 is a req #7 (Monitor self-wake) gap,
unrelated to spawn/zero-commit behavior — the invoking prompt's
description does not match this repo's own issue #947.

Outcome: **not-reproduced**.

**Attempt 2** — source: invoking prompt's claim "#705 post-PR record
stranding".

canonical: `gh issue view 705 --json title,state,number`
```
$ gh issue view 705 --json title,state,number
{"number":705,"state":"OPEN","title":"role sessions repeatedly strand post-PR: hunt/record writes hit ownership and claim gates after the PR is already open"}
```
canonical: `git log --all --oneline | grep 705`
```
$ git log --all --oneline | grep 705
9c00020 docs(issue-705): phase-1 survey and proposal
8591db4 Merge pull request #710 from tokenmaxxxer/issue-705/implementation
```
canonical: `gh issue view 705 --json state --jq .state`
```
$ gh issue view 705 --json state --jq .state
OPEN
```
canonical: the three command outputs immediately above, this session.
PR #710 for issue #705 shows in the `git log` output as a merge commit
on this branch's history, while the `gh issue view` state field for
#705 reads OPEN in the same session.

Outcome: **reproduced**.

**Attempt 3** — source: invoking prompt's claim "#785 two-phase
default".

canonical: `gh issue view 785 --json title,state,number`
```
$ gh issue view 785 --json title,state,number
{"number":785,"state":"OPEN","title":"role sessions default to a two-phase (propose to build) split even when the task says 'build now', doubling latency on delivery-only work"}
```
canonical: `git log --all --oneline | grep 785`
```
$ git log --all --oneline | grep 785
249212d ...propose...
c83cfd7 ...implement...
814f532 Merge pull request #790 from tokenmaxxxer/issue-785/implementation
```
canonical: `gh issue view 785 --json state --jq .state`
```
$ gh issue view 785 --json state --jq .state
OPEN
```
canonical: the three command outputs immediately above, this session.
Same pattern as attempt 2: PR #790's merge commit shows in the `git
log` output for issue #785, while the `gh issue view` state field for
#785 reads OPEN in the same session.

Outcome: **reproduced**.

**Attempt 4** — source: self-devised, from
docs/issue-750/reports/architecture/survey.md's claim that
`gates/reexecution_gate.py` has no automatic caller.

canonical: `grep -n landing_readiness on-the-record/hooks/merge-allow-gate.sh`
```
$ grep -n landing_readiness on-the-record/hooks/merge-allow-gate.sh
199:    script = os.path.join(checkout, "gates", "landing_readiness.py")
```
canonical: output above, this session.
This hook fires on `gh pr merge` per its own header comment
(on-the-record/hooks/merge-allow-gate.sh lines 1-30).

canonical: read of gates/landing_readiness.py, function
`reexecution_blocking_cause` (lines 60-75), this session
```
verdict = reexecution_gate.read_verdict(root, issue, role)
if verdict is None or verdict.kind == reexecution_gate.SUCCESS_KIND:
    return None
```
canonical: the read above, this session.
`reexecution_gate` is wired into the merge-time hook chain, contrary
to the prior architecture survey's "no automatic caller" claim — that
specific claim does not hold under this reproduction.

canonical: `grep -rn reexecution_gate --include=*.py --include=*.sh .`
excluding `gates/test_*.py`, this session.
The only non-test call site found is `gates/landing_readiness.py`'s
`read_verdict` call above; no path in this repo writes a
`.reexecution/<issue>-<role>.json` verdict file automatically.

canonical: read of on-the-record/UNENFORCED-CLAUSES.md line 17, this
session.
Line labels `reexecution_gate.py` "contract, CI-supplement" — verdict
production is expected from CI, outside this repo's own hook chain.

canonical: the `reexecution_blocking_cause` read above, this session.
When no verdict file exists for an issue/role, `reexecution_blocking_cause`
returns `None` — the same value the function returns when a verdict
file exists and records success.

Outcome: **reproduced**.

**Attempt 5** — source: self-devised, from
docs/issue-750/reports/architecture/survey.md's claim about which
spawn.py copy is canonical vs. stale.

canonical: `wc -l spawn.py`
```
$ wc -l spawn.py
5631 spawn.py
```
canonical: `wc -l /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/spawn.py`
```
$ wc -l /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/spawn.py
5631 /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/spawn.py
```
canonical: the two `wc -l` outputs above, this session.
The working-tree copy and the marketplace copy carry the same line
count; `classify()` sits at line 1540 in both (checked via `sed -n`
reads of both files, this session).

canonical: `wc -l /home/jwjung/.claude/tokenmaxxxer/muster/spawn.py`
```
$ wc -l /home/jwjung/.claude/tokenmaxxxer/muster/spawn.py
1774 /home/jwjung/.claude/tokenmaxxxer/muster/spawn.py
```
canonical: output above plus `ls -l` mtime read and `diff` against the
working-tree copy, this session.
This third checkout carries mtime 2026-07-29 and its `diff` against
the working-tree copy shows it lacks `STATE_ROOT`/`MUSTER_STATE_ROOT`,
`ORCHESTRATOR_SESSION_ID_ENV`, and `SESSION_RESUME_CLAIM_TTL_SEC`
support present in the other two; its own `classify()` sits at line
951.

canonical: read of docs/issue-750/reports/architecture/survey.md
opening section, this session.
That text states the working tree held a 2957-line spawn.py and the
marketplace copy was canonical at 4919 lines — neither figure matches
the `wc -l` outputs above, taken in this same session against the
current working tree and the current marketplace checkout.

Outcome: **reproduced**.

## Finding 1 — addressed_to: coding

**Summary**: canonical: Attempt 2's three command outputs above, this
session. Issue #705's `gh issue view` state field reads OPEN in the
same session where `git log --all --oneline` shows PR #710 (its
implementation) as a merge commit on this branch's history. Northpole
req #4 (fully-recorded finish) implies a role session's landed work
should be reflected in the repo's own record; this repo has no
mechanism observed in this session that flips a source issue's GitHub
state on landing — that is left to a separate, unautomated
human/agent action.

**Evidence pointer**: "Attempts and outcomes", Attempt 2 above.

**Severity**: band lookup — a record-closure gap tied to req #4, no
data-integrity or security exposure, and a human reading the PR list
directly still sees the merge → Medium → **advisory**.

## Finding 2 — addressed_to: coding

**Summary**: canonical: Attempt 3's three command outputs above, this
session. Issue #785's `gh issue view` state field reads OPEN in the
same session where `git log --all --oneline` shows PR #790 (its
implementation) as a merge commit on this branch's history. Same gap
class as Finding 1, independently reproduced against a second issue.

**Evidence pointer**: "Attempts and outcomes", Attempt 3 above.

**Severity**: band lookup — same reasoning as Finding 1 (req #4
record-closure gap, no data/security exposure) → Medium → **advisory**.

## Finding 3 — addressed_to: coding

**Summary**: canonical: Attempt 4's `reexecution_blocking_cause` read
and the `grep -rn reexecution_gate` output above, this session.
`reexecution_blocking_cause` (gates/landing_readiness.py lines 60-75)
returns the identical `None` value both when no verdict file exists
for an issue/role and when a verdict file exists and records success.
No path in this repo writes a `.reexecution/<issue>-<role>.json`
verdict file automatically (the `grep -rn reexecution_gate` scan
above), and verdict production is documented as a CI-supplement
outside this repo's own hook chain
(on-the-record/UNENFORCED-CLAUSES.md line 17). A role session whose
branch never triggers that external CI job goes through
`merge-allow-gate.sh`'s reexecution check the same way a session that
ran the check and satisfied it would.

**Evidence pointer**: "Attempts and outcomes", Attempt 4 above.

**Severity**: band lookup — a fail-open gap in a merge-time gate that
northpole req #3 (real-wired verification) depends on: an absent check
and a satisfied check reach the same gate outcome at the one
enforcement point wired into `gh pr merge`, with no observable signal
at merge time distinguishing them → High → **blocking**. Not
freehand: applying the deterministic Critical/High -> blocking mapping
per role directive; review's record being clean on this point does not
downgrade it.

## Finding 4 — addressed_to: coding

**Summary**: canonical: Attempt 5's three `wc -l` outputs and the
survey.md read above, this session.
docs/issue-750/reports/architecture/survey.md's opening section states
a 2957-line working-tree spawn.py and a 4919-line canonical marketplace
copy. The `wc -l` outputs above, taken this session, show both the
working-tree copy and the marketplace copy at 5631 lines with
`classify()` at line 1540 in both; a third checkout
(`/home/jwjung/.claude/tokenmaxxxer/muster/spawn.py`) sits at 1774
lines and is missing three env-var-driven features the other two
carry. The prior survey's cited line-count figures do not match this
session's re-derivation against the current working tree.

**Evidence pointer**: "Attempts and outcomes", Attempt 5 above.

**Severity**: band lookup — staleness in a documentation artifact (a
prior survey's cited figures), not a runtime defect in `spawn.py`
itself, and it does not gate landing or bypass a check → Low →
**advisory**. Which of the three copies actually executes at a live
spawn is not settled by this static reproduction (see "Open findings"
below).

## Open findings

- Finding 1 (Medium, advisory) — open, addressed_to: coding.
- Finding 2 (Medium, advisory) — open, addressed_to: coding.
- Finding 3 (High, blocking) — open, addressed_to: coding. No waiver
  on record.
- Finding 4 (Low, advisory) — open, addressed_to: coding.
- Carried-forward open question (not a finding — attempt 5's own scope
  limit, restated from the approved proposal's "Out of scope"): which
  of the three spawn.py copies actually executes at a live spawn
  requires observing a live spawn, out of scope for this static
  read-only reproduction round.

## Next steps

`coding` picks up Finding 3 (blocking) first: either make a missing
`.reexecution/<issue>-<role>.json` verdict block the merge the same
way a failing verdict already does, or wire a caller that populates
the verdict file before merge, per the phase-1 survey's own
remediation framing (docs/issue-750/reports/defect-verification/survey.md,
"Cross-reference to prior architecture survey" section). Findings 1-2
and 4 (advisory) are available for the same or a follow-up coding
round at coding's discretion.

## Open-finding resolution path

canonical: `python3 -c "print('placeholder — future re-run command TBD by coding/verify')"` —
resolution requires a future defect-verification round to re-run
Attempts 2-5 above against the fixed code/docs and record a fresh
outcome of not-reproduced for each, addressed_to: coding for whichever
fix lands.

## Accumulation

Not accumulation-cost-shaped — a single reproduction round over the
five attempts named in the phase-1 survey's attempt list; no repeated
attempt was needed in this phase-2 round.

## What did not work

None.
