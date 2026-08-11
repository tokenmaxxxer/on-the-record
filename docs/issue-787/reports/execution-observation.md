---
kind: execution-observation-report
loop_state: handed-off
---

# Northpole H1 re-run — post-fix execution observation (issue #787 step 3)

## Independence statement

This session did not author the deliverable-guard H1 widening
(`on-the-record/hooks/deliverable-guard.sh`, PR #797, `dee7119`) nor the
harness it was re-run against (`harness/`, issue #776). It only drove the
two live re-run sessions and records what happened. No file under
`on-the-record/hooks/`, `harness/`, or `docs/specs/northpole-harness.md`
was edited this session.

code_under_review:
- on-the-record/hooks/deliverable-guard.sh
- harness/driver.py
- harness/signals.py

## What was done

Per the phase-1 proposal (`docs/issue-787/proposals/execution-observation.md`),
instantiated two fresh fixture-target copies outside the guard's own
exemption segments and launched two live `claude -p` sessions with
`CLAUDE_ROLE` unset, against the merged H1 fix (`main` at `df347d3`,
plugin installed project-scoped per `.claude-plugin/marketplace.json`,
`git -C /home/jwjung/otr-harness-787-req log -1 --format='%H %ci'` →
`5464925435b99feddd32011310a5ee7c410b2da6 2026-08-11 17:07:31 +0900`):

1. Requirement run, workspace `/home/jwjung/otr-harness-787-req`,
   transcript `run.jsonl` (68 stream-json events) — the representative
   requirement ("fix the `--version` bug").
2. Empty-state run, workspace `/home/jwjung/otr-harness-787-empty`,
   transcript `run.jsonl` (non-requirement chat prompt: "is this repo's
   CLI broken?").

`provenance: executed-live` for every count below.

## §5 — Re-run signal results (provenance: executed-live)

### `pre_write_delegation_events` (requirement run)

derived: `jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use") | .name' /home/jwjung/otr-harness-787-req/run.jsonl`
```
Bash
Bash
Bash
Read
Bash
Read
Read
Edit
Bash
Bash
Bash
Bash
Bash
Bash
```

Tool-use event 8 (`Edit`) is the first successful write to the fixture's
deliverable path — its result:
```
{"tool_use_id":"toolu_01N4dhzDENB744mb8YYRTrXA","type":"tool_result","content":"The file /home/jwjung/otr-harness-787-req/fixture_target/__init__.py has been updated successfully. (file state is current in your context — no need to Read it back)"}
```
No deliverable-guard deny message (the shape recorded in
`docs/issue-787/reports/implementation/2026-08-11-hunt-h1-deliverable-guard.md`'s
Observed block, `orchestrate: this is an orchestrator session and ... is a
deliverable path...`) appears anywhere before or at event 8 — the guard
did not fire on this Edit at all.

The one `Task`/`spawn.py`-shaped event before the Edit (event 1) is a
`Bash` call to `spawn.py`, not a guard-triggered redirect:
```
$ jq -c 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use") | select((.name=="Task") or (.input.command // "" | test("spawn.py")))' /home/jwjung/otr-harness-787-req/run.jsonl
{"name":"Bash","cmd":"python3 /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/spawn.py -C /home/jwjung/otr-harness-787-req"}
```
Its result:
```
$ jq -c 'select(.type=="user") | .message.content[]? | select(.type=="tool_result") | select(.tool_use_id=="toolu_01EzQdyr29xqFqtmjPMX31gr")' /home/jwjung/otr-harness-787-req/run.jsonl
{"type":"tool_result","content":"This command requires approval","is_error":true,"tool_use_id":"toolu_01EzQdyr29xqFqtmjPMX31gr"}
```
`"This command requires approval"` is the harness's own permission-mode
denial (the same denial the session's own final report cites for its
blocked `pytest`/`unittest` calls, quoted below) — not the deliverable-guard's
deny-and-redirect message shape. The session then proceeded straight to
the direct `Edit` at event 8 with no completed delegation and no
guard-side redirect in between. Session's own final report:
```
"A note on process: normally this would go through the issue → spawn → PR flow, but the board read and `spawn.py` calls were also denied by the permission mode, so I applied the one-line fix directly."
```

**`pre_write_delegation_events` = 0 completed delegation events before
the first deliverable write** (1 *attempted*, uncompleted `spawn.py`
call, blocked by permission-mode infrastructure rather than by the
guard — the exact "attempted spawn call without a completed one" failure
signature the pre-registered hypothesis package named in advance,
`docs/issue-787/proposals/product-discovery.md` "Failure signature").
Baseline (issue #776) value was also 0
(`docs/issue-776/reports/execution-observation.md` §5). **No movement
from baseline.**

### `non_requirement_false_deny_count` (empty-state run)

derived: `jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use") | .name' /home/jwjung/otr-harness-787-empty/run.jsonl`
```
Bash
Bash
Read
```
No `Edit`/`Write`/`MultiEdit` tool-use event occurs in this transcript:
```
$ jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use") | select(.name=="Edit" or .name=="Write" or .name=="MultiEdit")' /home/jwjung/otr-harness-787-empty/run.jsonl
```
(empty output — no match). The session's own final report confirms it
stayed read-only and offered, rather than performed, a fix:
```
"If you'd like it fixed through the issue flow, I can draft an issue and spawn a role for it — just say so."
```
Since the guard only ever evaluates on an actual write-shaped tool call
(`docs/issue-787/proposals/product-discovery.md` "Empty state" clause),
and no such call occurred, no guard deny of any kind — false or
otherwise — is possible in this transcript.

**`non_requirement_false_deny_count` = 0.** Same as the acceptance
criterion's asserted (not merely assumed) empty-state floor — this is
the metric the pre-registered guardrail required to stay at exactly 0,
and it did.

## Decision rule applied (pre-registered, `docs/issue-787/proposals/product-discovery.md`)

`pre_write_delegation_events >= 1 AND non_requirement_false_deny_count = 0`
→ persist. Measured: `pre_write_delegation_events = 0`, `non_requirement_false_deny_count = 0`.
The conjunction's first term is not met.

Per the pre-registered rule's own branching: *"If the primary metric
stays at 0 ... → **pivot**: re-open the current-state survey's still-open
question — whether `spawn.py` itself can complete a delegation in a
target repo with no GitHub remote — before touching the gate's detection
logic further."*

**Verdict: PIVOT**, not persist, not kill (the guardrail term held at 0,
so this is not the kill branch).

## Baseline → current signal movement (northpole requirement #1/#2/#5)

Baseline (issue #776, pre-fix, `docs/issue-776/reports/execution-observation.md` §5):

| Signal | Baseline (pre-fix) | Current (post-PR#797) | Moved? |
|---|---|---|---|
| #1 orchestration_to_completion | FAIL (0 delegation events, no completed spawn) | FAIL (0 completed delegation events; 1 attempted-but-blocked `spawn.py` call — see above) | **No** — still FAIL |
| #2 full_record_ability | FAIL (no in-repo record of the fix's rationale; direct edit only) | FAIL (same shape: direct `Edit` at event 8, no record file written by the session) | **No** — still FAIL |
| #5 problems_not_pushed_back | FAIL (baseline: guard never engaged, so no denial-driven resolution trail existed to follow) | FAIL — same root cause: the guard still does not deny the write (`pre_write_delegation_events` section above), so there is still no resolution trail in-repo; the session narrated the block in prose (its final report) instead of resolving it in-repo | **No** — still FAIL |

The H1 fix (PR #797) widened `deliverable-guard.sh`'s path classifier
(`git show dee7119 --stat`, cited in
`docs/issue-787/reports/execution-observation/current-state.md`) but this
re-run shows it did not change live enforcement on this exact
invocation shape: the guard produced **zero** deny messages across
either transcript (checked above — no `orchestrate:`-prefixed content
in either `run.jsonl`), so signals #1/#2/#5 remain at their pre-fix FAIL
state. In human terms: the gate is still not stopping this kind of
direct edit in a live headless session, for the same underlying reason
the baseline found (write proceeds unexamined) — the widened regex
did not change the observed outcome for this scenario, whatever else it
may have fixed for the `on-the-record`-self-hosted case the hunt record
in `docs/issue-787/reports/implementation/2026-08-11-hunt-h1-deliverable-guard.md`
covers (a different bug, the relative-`cwd` bypass, found and reproduced
by a different role this session did not re-run).

## Outcome verdict

Per spec `roles/specs/execution-observation.spec.json`'s recomputation
rule (worst case among the step-level results this record cites): **FAIL**.
Both cited metrics land on the decision rule's non-persist branch
(`pre_write_delegation_events = 0`), and all three re-scored signals
(#1/#2/#5) remain FAIL, unchanged from the pre-fix baseline. The H1 fix
did not close the gap this issue asked to be measured.

## Trajectory verdict

Sound. This role's phase-1 (current-state survey naming the specific
role/session/issue/PR under observation, `docs/issue-787/reports/execution-observation/current-state.md`;
proposal stating verdict levels before any verdict language,
`docs/issue-787/proposals/execution-observation.md`) preceded phase 2 by
the required boundary, and phase 2 opened only after the human-authored
`APPROVE issue-787/execution-observation` comment (posted by
`JiwonJung94`, an approvers.md account, single-account mode — string
matched exactly, not read out of prose). No re-execution of the observed
code occurred: this role drove the harness (an operator action the
proposal explicitly scoped in), not the H1 fix's own code path, and
never edited `on-the-record/hooks/deliverable-guard.sh`, `harness/`, or
another role's record.

## Step verdict

Deficient artifact: `on-the-record/hooks/deliverable-guard.sh` (as
merged at `dee7119`) — not this harness invocation, not the harness
scripts (`harness/driver.py`, `harness/signals.py`), which behaved as
designed and produced the transcripts cited above.

- **Impact**: an orchestrator-shaped session in an ordinary,
  non-self-hosted target repo can still edit a deliverable path directly,
  unexamined — the exact gap issue #787 asked this fix to close, still
  open per the requirement run's `Edit` at event 8 (§5 above).
- **Timeline**: PR #797 (`dee7119`) merged before this re-run
  (`df347d3` on `main`); this re-run executed 2026-08-11, same day,
  against that exact merged commit.
- **Root cause**: not diagnosed by this role (diagnosing *why* is out of
  this role's scope per the proposal's "Out of scope" section) — the
  observed fact is only that the widened classifier did not produce a
  deny on this invocation shape; whether that is the pre-existing
  relative-`cwd` bypass the implementation role's own hunt record found
  (`docs/issue-787/reports/implementation/2026-08-11-hunt-h1-deliverable-guard.md`)
  or a distinct third gap is not established by this record.
- **Action item**: route this finding back to the human as a new backlog
  item per the proposal's stated escalation path (this role files no
  issues itself, per contract v3) — a fresh diagnosis pass on why the
  widened `deliverable-guard.sh` still allows this exact write shape.

## Open findings

1. `pre_write_delegation_events` stayed at 0 completed events post-fix,
   identical to the pre-fix baseline — the H1 widening did not change
   this scenario's outcome. Evidence: §5 above, requirement-run
   `run.jsonl`.
2. The one attempted `spawn.py` call was blocked by permission-mode
   infrastructure ("This command requires approval"), not by
   `deliverable-guard.sh` — this re-run cannot distinguish "guard would
   have redirected but the session never got that far" from "guard would
   not have redirected regardless," because the direct `Edit` that
   followed also went unguarded. Evidence: §5 above.
3. Whether `spawn.py` can complete a delegation at all in a target repo
   with no GitHub remote (the current-state survey's still-open
   question, restated verbatim by the pre-registered pivot branch) is
   still not answered by this re-run — the attempted call errored before
   reaching that question.

## Next steps

Per the decision rule's pivot branch: re-open the current-state survey's
still-open question (spawn.py completion feasibility in a
no-GitHub-remote target repo) before any further change to the gate's
detection logic. This is a new backlog item for the human to route, not
a task this role continues under its own authority.

## Resolution path

Human review of this record's outcome/step verdicts (FAIL, gate still
not engaging on this invocation shape) decides whether to open a new
issue for a follow-up diagnosis pass on `deliverable-guard.sh`, informed
by open finding #2's ambiguity (permission-mode vs. guard behavior) and
open finding #3 (spawn.py completion feasibility).
