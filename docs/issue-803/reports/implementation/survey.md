# issue-803 implementation — current-state survey

## Scope of this survey

canonical: docs/issue-803/proposals/2026-08-11-self-driven-deviation-loop.md (read in full this turn)

Issue #803 step 2 (implementation) builds on the design that step 1
(product-discovery) produced in the file cited above: it names the
write set, the paragraph content outline, and the guard behavior. This
survey checks the current state of each surface that design names, so
the implementation write set is grounded in what is on disk now.

## Skip condition (scout directive)

canonical: docs/issue-803/reports/product-discovery/scout-brief.md (read this turn)

Scouting (external product research) is skipped for this proposal: the
spec leaves no design decision open. Step 1 already ran the scout sweep
and resolved the RECOGNIZE/CLASSIFY/RESOLVE approach in the design doc,
naming two rejected alternatives. Implementation's task is to encode
that already-approved design into directive.sh, a new guard hook, and a
handbook — a mechanical port, not a fresh design decision.

## Surfaces touched

### on-the-record/hooks/directive.sh

canonical: on-the-record/hooks/directive.sh:1-184 (read in full this turn)

- 184 lines total. Injected on every UserPromptSubmit, gated by
  `[ -z "${CLAUDE_ROLE:-}" ]` at line 12 — a spawned role session skips
  it.
- Already carries three stacked norms as paragraphs inside one heredoc
  block (lines 39-181): the base issue/PR flow, "DELEGATION IS THE
  DEFAULT" (#699 R2, lines 121-141), "YOUR GOAL LOOP" (#699 R3, lines
  142-155), and "AUTONOMOUS ASYNC COMPLETION" (#878, lines 157-177) —
  each paragraph states it nests inside the prior one. The new #803
  paragraph is a fourth such addition and needs the same framing (nests
  inside #699 R3), matching the design doc's own instruction.
- `poll_rearm_arm_if_due` at line 37 is the existing due-tick arming call
  the design's RESOLVE step's watch/re-arm reference points at — no new
  arming mechanism is needed for that reuse.

### Guard-hook pattern for the planned new Stop-hook script

canonical: on-the-record/hooks/record-claim-guard.sh:1-45 (read this turn)
- record-claim-guard.sh (PreToolUse, Write|Edit|MultiEdit) is the closest
  existing shape for a payload-reading guard: fail-closed
  `trap ... EXIT` at its top, an `ORCHESTRATE_OFF` kill switch, and an
  embedded-Python heredoc reading the tool-call JSON from an env var.

canonical: on-the-record/hooks/stop-gate.sh:1-40 (read this turn)
- stop-gate.sh is the closest existing Stop-hook shape: same fail-closed
  trap, same `ORCHESTRATE_OFF` kill switch, same
  `[ -z "${CLAUDE_ROLE:-}" ]` orchestrator-only gate, reads a
  `STOP_PAYLOAD` env var, inspects `last_assistant_message`. The planned
  guard needs to inspect the transcript for a recognized-deviation
  marker with no matching deviation-log entry — stop-gate.sh's
  payload-reading shape is the template; the check content differs
  (marker-vs-log-entry, not approval-phrase-vs-clause).

### Registration point: on-the-record/hooks/hooks.json

canonical: on-the-record/hooks/hooks.json lines 84-95 (read this turn)

- The Stop array currently lists 6 hooks in order: stop-poll-rearm.sh,
  stop-gate.sh, role-test-claim-guard.sh, decision-queue-stopgate.sh,
  report-framing-check.sh, product-capture-stopgate.sh. A new guard
  entry slots into this array as a 7th line.
- hooks.json is a config file, not one of contract v3 s21's named
  operational-surface types (package manifest, CI workflow, deploy
  script) — no separate handbook-touch obligation attaches to this file
  specifically; the handbook is already in the write set for the
  deviation-loop behavior itself.

### Deviation-log path convention

canonical: docs/reports/consult-log.md (path exists, checked this turn), on-the-record/commands/consult.md (read this turn)

- docs/reports/consult-log.md exists today, together with the
  per-issue docs/issue-<n>/reports/consult-log.md split the consult
  command documents. The design's planned deviation-log split (issue-
  scoped vs. not) mirrors this existing convention exactly — no new path
  scheme is being invented.
- on-the-record/commands/consult.md documents consult-log.md's append
  contract in prose; the planned handbook needs the equivalent contract
  for the new deviation log.

### docs/handbooks/ (existing directory)

canonical: `ls docs/handbooks` (run this turn)

- Confirmed present as a standing bucket. A new file in this directory
  is an addition to an existing directory, not a new directory.

## Write set for this proposal

- on-the-record/hooks/directive.sh (edit: append the 4th paragraph)
- a new Stop-hook guard script under on-the-record/hooks/
- on-the-record/hooks/hooks.json (edit: register the new Stop hook)
- a new file under docs/handbooks/ documenting the deviation loop
- this survey file
- this proposal's own file

hooks.json is an addition beyond the design doc's own files: list — a
new Stop hook is inert unless registered there, and omitting it would
ship a guard script nobody invokes. Naming it here follows the
survey-order directive's requirement that the write set be the one
actually expected to be touched, not a placeholder copied from the prior
phase.

## Open dependency (unchanged from the design doc)

canonical: docs/issue-803/proposals/2026-08-11-self-driven-deviation-loop.md, "Constraints" and "Out of scope" sections (read this turn)

#787 (orchestration entry) and #801 (quiet-gap self-wake) remain the
design's stated operational dependencies. This build makes the loop
writable now (directive text plus guard); whether it is autonomous
end-to-end without those two issues landed is not re-decided here — the
design doc already scopes that question to #787/#801, not to this
build.
