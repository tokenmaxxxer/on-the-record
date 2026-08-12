---
kind: hypothesis-testing
loop_state: measuring
---

# issue #476 — phase 2 record: candidate E (refusal-cost-parity) shipped

## What was done

Built and landed candidate E from
`docs/issue-476/proposals/discovery-round3.md` (RICE-primary, "ships
first"): `spawn.py`'s own outcome-classification path
(`classify()`) now recognizes a registered REFUSAL declaration in a
session's final result text and exempts it from `silent-failure` —
which previously read identically to a dead/silent session, with no
board delta and no commit required either way.

code_under_review:
- spawn.py
- tests/test_spawn.py

derived:
```
python3 -m pytest tests/test_spawn.py -q
```
```
463 passed in 24.31s
```

canonical: tests/test_spawn.py:820-829 (new cases
`test_registered_null_result_declaration_is_not_silent_failure`,
`test_unregistered_null_result_state_stays_silent_failure`,
`test_null_result_declaration_does_not_outrank_delta_or_denial`), all
passing per the pasted pytest output above — no SKIPPED lines in that
run.

canonical: spawn.py `REGISTERED_NULL_RESULT_STATES` /
`_null_result_declared` / `classify()`, read directly (this commit's
diff). Mechanism, concretely: a session's final text is scanned for
the exact pattern `REFUSAL: <state> — <reason>`. canonical: same
functions above. `<state>` must be a member of a closed, code-level
vocabulary (`hypothesis-not-falsifiable`, `evidence-log-unreadable`,
`nothing-to-do` — reusing the earlier rounds' H2 `loop_state` refusal
names plus issue #983's role-session generic). `classify()`'s ordering
is unchanged above this check: board delta still wins (`progressed`),
a human gate still wins (`waiting-on-human`), a real permission denial
still wins (`refused`). Only the previously-uncovered case — no delta,
not blocked, no denial, but a well-formed registered refusal
declaration present — moves off `silent-failure` onto a new
`refused-null-result` outcome. `fail_closed_downgrade()` and the
`silent-failure`→`progressed` git-state upgrade are untouched: this
outcome sits outside both, so a genuine null-result report is not
"failed" for lacking a commit, matching H3's stated intent, and is
also not silently promoted to `progressed` by git-state heuristics it
never earned.

## Why

canonical: spawn.py `classify()` and `fail_closed_downgrade()`, read
directly at spawn.py:1542-1666 and the session-end print block around
spawn.py:5760-5777 (this commit's base, pre-change). Upstream half of
issue #476: the operator's named failure mode is that "a session that
reports 'nothing to do' or 'cannot verify' reads as failure, so
sessions manufacture deliverables." Reading `spawn.py`'s own scoring
path directly showed this literally coded in: a role session that
makes no board-file write and hits no gate produced `silent-failure`
regardless of whether it said why, with the identical downstream label
a kill-9'd process gets. Candidate E from the round-3 proposal targets
exactly this reporting-path asymmetry, scored highest RICE (14.0)
because it is population-wide (every spawn, not a sampled fraction)
and lowest-effort (a scoring change, not a new interception point).

## Upstream basis

- docs/issue-476/proposals/discovery-round3.md
- 32ce1040f25d8e3e3c71b5adbc9a8c83423ff54a

canonical: `git log --oneline -1 origin/main` (this session's own
command, output `32ce104 issue-586 ...`, full sha above) — this branch
was cut from that commit, which carries #990's merged round-3 proposal.

## Opportunity-solution-tree disposition

Branch: outcome = "spawned role sessions do genuinely-needed work
instead of gate-satisfying theater" → opportunity = "refusal/
null-result currently costs a role session more than fabricating a
deliverable" (survey-round3.md's upstream-half finding) → candidate
solution **E, refusal-cost-parity** → discriminating-assumption-test =
H3-refusal-parity (registered above). This branch is **promoted**:
canonical: `python3 -m pytest tests/test_spawn.py -q` — result: `463
passed in 24.31s` (same derived block under "What was done" above,
this session's own run against the shipped diff). E is built and its
tests pass, so it moves from "candidate solution" to "shipped, awaiting
its own pre-registered verdict" (go, pending measurement — see
Guardrail status below). Sibling candidate solutions F (task-string
check) and G (sampling audit) remain candidate solutions, deliberately
not promoted this round per the proposal's staging order. Candidate H
(diversity/non-transcription check) stays pruned, per
discovery-round3.md's own "reject for this round" verdict — unchanged
here, not revisited.

## Pre-registered hypothesis (H3-refusal-parity), unchanged from the proposal

- **Metric**: `refusal_parity_rate` — role sessions using
  `refused-null-result` on tasks a sampled review agrees genuinely
  warranted refusal, over all sessions in the window that genuinely
  warranted refusal.
- **Threshold**: ≥80% over the next 30 qualifying spawns after this
  change ships.
- **Guardrail**: `false_reject_rate` (sessions using
  `refused-null-result` where real deliverable work existed) ≤15%.
- **Decision rule**: unchanged from discovery-round3.md — go / pivot /
  kill-and-redesign per the metric and guardrail above.
- **ITWWS follow-up (pre-committed in discovery-round3.md)**: "if this
  works [`refusal_parity_rate` ≥80% and `false_reject_rate` ≤15%] we
  should proceed to stage candidate F (spawn-time task-string check),
  using this round's rollout data to calibrate F's false-positive
  risk." Status here: **deferred, with reason** — the 30-spawn
  measurement window this ITWWS follow-up depends on has not started
  (corpus size 0, see Guardrail status below), so it cannot be actioned
  in this same record; it is carried forward verbatim into Next steps
  item 3 below rather than dropped.

## Guardrail status at this measurement moment

Guardrail metric `false_reject_rate` (threshold ≤15%): status is
**held, not breached** — but only because the qualifying corpus is
currently size 0 (this mechanism lands in this same commit; no
post-rollout spawns exist yet). "Not breached" here means "no
breaching evidence exists," not "verified safe" — the same empty-state
distinction discovery-round3.md's decision rule already draws.
`refusal_parity_rate` is likewise not yet measurable against its ≥80%
threshold for the same reason.

## Open findings

- The registered-state list (`REGISTERED_NULL_RESULT_STATES`) is a
  hand-maintained snapshot of other plugins' `loop_state` refusal
  vocabularies (H2, issue #983). If a plugin registers a new
  refusal/null-result state later and this constant is not updated in
  the same review, that plugin's genuine refusals silently fall back
  to `silent-failure` — the failure signature the proposal itself
  named for candidate E ("locating the ACTUAL current scoring path...
  is this round's first architecture task, not a given" — read here
  directly rather than assumed).
- Candidates F (spawn-time task-string check) and G (sampling audit)
  from discovery-round3.md are staged after E's rollout data per the
  proposal and are explicitly not built in this delivery.

## Next steps

1. Run the next 30 qualifying spawns under this mechanism and collect
   `refusal_parity_rate` / `false_reject_rate` via the sampled-review
   process discovery-round3.md specifies.
2. Apply the decision rule to that measurement and record the verdict
   (go/pivot/kill-and-redesign) in a follow-up phase-2 record.
3. If go: build candidate F (the deferred ITWWS follow-up above),
   calibrated against this round's rollout data per the proposal's
   staging order.

## Resolution path

The corpus-size-0 open finding above resolves once 30 qualifying
spawns have run under this mechanism and a follow-up record applies
the pre-registered decision rule to the measured
`refusal_parity_rate`/`false_reject_rate` pair.

## What did not work

None.
