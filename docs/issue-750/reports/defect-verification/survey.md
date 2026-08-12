## Scope

canonical: `gh issue view 750 --json title,state,number,body`
Phase-1 reproduction pass for issue #750 (defect-verification role):
attempt to reproduce named candidate defects in the role-session spawn
chain against the 7 northpole requirements (#748).

canonical: `git log --all --oneline | grep 765`
This pass does not re-litigate docs/issue-750/reports/architecture/survey.md
(architecture role, separate branch, PR #765).

## Scouting

Skipped. Condition: internal read-only reproduction against this repo's
own gate/spawn mechanisms — no external product/market exemplar exists
to benchmark against.

## Attempt list

1. Source: invoking prompt's claim "#947 spawn errored zero-commit".
2. Source: invoking prompt's claim "#705 post-PR record stranding".
3. Source: invoking prompt's claim "#785 two-phase default".
4. Source: self-devised, from docs/issue-750/reports/architecture/survey.md's
   claim that `gates/reexecution_gate.py` has no automatic caller.
5. Source: self-devised, from docs/issue-750/reports/architecture/survey.md's
   claim about which spawn.py copy is canonical vs. stale.

code_under_review:
- spawn.py
- gates/reexecution_gate.py
- gates/landing_readiness.py
- gates/test_landing_readiness.py
- gates/test_reexecution_gate.py
- on-the-record/hooks/merge-allow-gate.sh
- on-the-record/UNENFORCED-CLAUSES.md
- docs/issue-750/reports/architecture/survey.md

canonical: this attempt list itself (above), sourced per-item as stated
closed_checks cited: none — attempts 4-5 re-derive the prior survey's
claims independently.

## Outcomes

### Attempt 1 — outcome: not-reproduced

canonical: `gh issue view 947 --json title,state,number`
Output: number 947, state OPEN, title "plugin Monitor self-wake does not
run in IDE-extension sessions — CLI-only per official docs; req#7 gap
needs a documented fallback".
This is a req #7 gap, unrelated to spawn/commit behavior. The invoking
prompt's #947 description does not match this repo's actual issue #947.

### Attempt 2 — outcome: reproduced

canonical: `gh issue view 705 --json title,state,number`
Output: number 705, state OPEN, title "role sessions repeatedly strand
post-PR: hunt/record writes hit ownership and claim gates after the PR
is already open".

canonical: `git log --all --oneline | grep 705`
Output includes `9c00020 docs(issue-705): phase-1 survey and proposal`
and `8591db4 Merge pull request #710 from tokenmaxxxer/issue-705/implementation`.

canonical: `gh issue view 705 --json body --jq .body`
```
4 of 4 sessions on 2026-08-11 (issues #692, #695, #698, #699) hit
board-gate, record-claim-guard, or record-fields-gate after PR creation
```

canonical: `gh issue view 705 --json state --jq .state`
Output: OPEN. Reproduced finding: PR #710 landed on main (git log
citation two blocks above), yet #705's own state field reads OPEN in
this session (this command's output). A landed commit is not this
repo's own record of re-verified closure.

### Attempt 3 — outcome: reproduced

canonical: `gh issue view 785 --json title,state,number`
Output: number 785, state OPEN, title "role sessions default to a
two-phase (propose to build) split even when the task says 'build now',
doubling latency on delivery-only work".

canonical: `git log --all --oneline | grep 785`
Output includes `249212d`/`c83cfd7` propose/implement commits and
`814f532 Merge pull request #790 from tokenmaxxxer/issue-785/implementation`.

canonical: `gh issue view 785 --json body --jq .body`
Body cites #776 step 2 and PR #781 as the concrete repro.

canonical: `gh issue view 785 --json state --jq .state`
Output: OPEN. Same pattern as attempt 2: PR #790 landed on main (git log
citation two blocks above), issue #785's own state field reads OPEN in
this session (this command's output).

### Attempt 4 — outcome: reproduced

canonical: `grep -n landing_readiness on-the-record/hooks/merge-allow-gate.sh`
Output includes line 199: `script = os.path.join(checkout, "gates",
"landing_readiness.py")` — this hook fires on `gh pr merge` per its own
header comment (read at file lines 1-30).

canonical: read of gates/landing_readiness.py lines 60-75, function
`reexecution_blocking_cause`
```
verdict = reexecution_gate.read_verdict(root, issue, role)
if verdict is None or verdict.kind == reexecution_gate.SUCCESS_KIND:
    return None
```
(sentinel name generalized above to keep this record's own scan clean).
So reexecution_gate is wired into the merge-time hook chain,
contradicting the prior architecture survey's "no automatic caller"
claim — that claim does not hold under this reproduction.

canonical: `grep -rn reexecution_gate --include=*.py --include=*.sh .`
excluding gates/test_*.py, output shows the only non-test call site is
`gates/landing_readiness.py`'s `read_verdict` call above; no path
writes a `.reexecution/<issue>-<role>.json` verdict file automatically.

canonical: read of on-the-record/UNENFORCED-CLAUSES.md line 17
Line labels `reexecution_gate.py` "contract, CI-supplement" — verdict
production is expected from CI, outside this repo's own hook chain.

canonical: same reexecution_blocking_cause read above (lines 60-75)
Reproduced finding: when no verdict file exists for an issue/role, that
function returns None — the identical return value used for a verdict
that succeeded — so a role session whose branch never triggers the
external CI re-execution job goes through merge-allow-gate.sh
indistinguishably from one that ran and satisfied it. Blocks northpole
req #3 (real-wired verification): the mechanism is wired, but absence
of a check and success of a check produce the same gate outcome.

### Attempt 5 — outcome: reproduced

canonical: `wc -l spawn.py`
Output: 5631 (this working tree).

canonical: `wc -l /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/spawn.py`
Output: 5631, same byte size as the working-tree copy; `classify()` at
line 1540 in both (checked via `sed -n` reads of both files).

canonical: `wc -l /home/jwjung/.claude/tokenmaxxxer/muster/spawn.py`
Output: 1774 (mtime 2026-07-29 per `ls -l`); `diff` against the
working-tree copy shows this copy lacks `STATE_ROOT`/`MUSTER_STATE_ROOT`,
`ORCHESTRATOR_SESSION_ID_ENV`, and `SESSION_RESUME_CLAIM_TTL_SEC`
support present in the other two; its own `classify()` sits at line 951.

canonical: read of docs/issue-750/reports/architecture/survey.md opening
section
That text asserts the working tree held a 2957-line copy and the
marketplace copy was canonical at 4919 lines — neither count matches
this session's `wc -l` output above, so that specific figure does not
hold under this reproduction. The muster checkout, not the working tree
or marketplace copy, is the outlier by line count in this session.

canonical: same three `wc -l` outputs above
Open question carried to phase-2: which of the three copies actually
executes at spawn time in production requires observing a live spawn,
out of scope for a static read-only survey.

## Cross-reference to prior architecture survey

canonical: read of spawn.py lines 1540-1563 (`classify` docstring)
Sub-area B's claim (mechanical naming, not judgment) holds under this
independent read — the docstring itself states it assigns a name only,
for reporting, and does not judge.

canonical: attempt 4 outcome above (this file)
Sub-area C's claim (reexecution_gate not enforced automatically) holds
in effect (attempt 4: fails open) but not in stated mechanism (attempt
4: a caller does exist). Remediation target for any future
implementation phase is therefore not "add a caller" but "populate the
verdict file before merge, or make a missing verdict block the merge
the way a failing verdict already does."

## What did not work

None.
