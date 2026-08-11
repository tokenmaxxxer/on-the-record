---
subject: issue-914
kind: scout-brief
---

# Scout brief — standing real-build-and-use verification (issue #914)

Stage count: 1 sweep stage (reuse of the official hooks reference already
fetched for #870, plus one fresh read of this repo's own live-fire
precedent), 0 deepening stages — saturated after stage 1: the open
question ("which hook events can act at gate-registration time and at
outcome-claim time, and does this repo already have a script that
live-fires another script") is answered completely by these two sources,
and no competitive-product space applies (this is an internal
verification-discipline extension, not an external-facing product).
Mode: single fetch + one in-repo read, not a multi-angle fan-out.

canonical: https://code.claude.com/docs/en/hooks (re-consulted this
session; originally fetched 2026-08-11 for #870, content unchanged)
canonical: gates/test_boundary.py (read this session, `import
importlib.util` + `spec.loader.exec_module` pattern)

## Category must-bes

- `PreToolUse` is the only event type that can refuse a tool call before
  it happens, and can rewrite `tool_input` (write-time gates already use
  this: `record-claim-guard.sh`, `gate-registration-guard.sh`).
- `Stop`/`SubagentStop` are the only event types that can block a
  turn/subagent from ending — `decision: "block"`.
- No hook event type can itself *invoke* another script as a live
  PreToolUse event with a synthetic payload — hooks fire only on real
  tool calls the harness makes. Live-firing a hook under test therefore
  has to happen as an executable check (a script that pipes a crafted
  JSON payload into the target hook script and asserts stdout/exit
  code), the same shape `gates/test_boundary.py` and
  `gates/test_acceptance_gate.py` already use for gate unit tests, not
  as a new hook type.

Sources:
- https://code.claude.com/docs/en/hooks

## Performance axes this deliverable competes on

- Axis 1: whether "the hook has a unit test" is treated the same as
  "the hook was actually invoked as a lifecycle event with a real
  payload and its allow/deny path asserted" — #909's finding shows a gap
  between the two today (`absorbed-branch-recut-guard.sh` has its own
  test file yet was never wired into `hooks.json`, so its test exercises
  code that never fires in an installed session).
- Axis 2: whether "acceptance section exists and looks executable"
  (`acceptance_gate.py`, shipped) is treated the same as "the acceptance
  command was actually run against the current target and exited zero"
  — they differ; `acceptance_gate.py` only checks the section's
  *shape*, per its own docstring ("값의 진실은 검사하지 않는다").
- Axis 3: fail-safe direction on the degrade path — an unmeasurable
  target should read as `UNMEASURED-with-reason`, never a silent/false
  positive (the standing rule already established by #310's
  `unverifiable:` escape and reused by #870/#892's outcome-claim check).

## Adopt / skip

- **Adopt**: `PreToolUse` on `git commit`/`gh pr create` as the
  enforcement point for "a newly-staged gate/hook has no matching
  live-fire test" — same interception shape
  `test-authoring-invariant-guard.sh` (#906) already uses for "no
  covering test", one layer stricter (covering test must itself be a
  live-fire, not any test).
- **Adopt**: `Stop`/`SubagentStop` as the enforcement point for the
  target-deliverable acceptance-command re-run — already scoped as
  candidate-b in #870's own proposal, not yet built; this issue
  generalizes it into the "artifact-type: target-repo deliverable" row
  of the same standing requirement.
- **Adopt**: an executable-check convention ("live-fire harness": pipe a
  crafted PreToolUse-shaped JSON payload into the hook script under
  test via stdin, assert stdout/exit code against the allow/deny/log
  outcome the hook's own header comment declares) as the mechanical
  definition of "live-fired," reusing the stdin-JSON contract every
  `on-the-record/hooks/*.sh` script already implements (`payload="$(cat
  2>/dev/null || true)"`).
- **Skip**: a new hook *event type* for live-firing — none exists or is
  needed; live-firing is a test-authoring convention checked by an
  extension of the existing test-authoring invariant (#906), not a new
  lifecycle hook.
- **Skip**: semantic judgment of whether the acceptance command's
  *content* is a good test of the deliverable — out of scope, same
  boundary #870/#892 and #776 already draw (exit-status match, not
  correctness of the check itself).

## Gap line

The field already has, separately: (1) a standing requirement that a
test must exist for new code (#906, test-authoring-invariant-guard.sh)
(2) a requirement that an outcome claim cite an executed-live source
(#870 candidate-a, #892, `outcome_claim_citation_check`) (3) a
requirement that an issue's Acceptance section reference a runnable
artifact (#310, `acceptance_gate.py`, shape-only) (4) a *designed-but-
unbuilt* per-target acceptance-command re-run (#870 candidate-b). What
is missing across all four: none of them require that a test *existing*
also means that test was *actually run against the real wired
capability*. #909's finding
(`on-the-record/hooks/absorbed-branch-recut-guard.sh`) is the concrete
evidence this gap is real: the script carries its own test file,
satisfying (1), yet the capability it tests has never fired once in any
installed session because it carries no `hooks.json` row. That is the
"real build + use" gap issue #914 asks to close, generalized across
three artifact types (deliverable, gate/hook, general outcome claim).
