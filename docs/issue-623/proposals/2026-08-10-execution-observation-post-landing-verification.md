---
status: landed
files:
  - docs/issue-623/reports/execution-observation.md
---

## Request

Verify, by spawning real agent-driven sessions against fixture target
repos, that (a) today's eleven stacked shipped surfaces produce no side
effects/regressions operating together, run under
marketplace-install-path conditions per the operator's addition (no
repo-checkout `gates/`, versioned plugin-cache layout,
`CLAUDE_PLUGIN_ROOT` resolution) — not the repo checkout; and (b) each
pre-registered metric named in the issue body is reported
measured-pass / measured-fail / deferred-with-reason, with no
denominator manipulation. Render both as tables in
`docs/issue-623/reports/execution-observation.md`.

## Constraints

- Install-path parity is load-bearing: any drive step that only
  exercises the dev checkout does not satisfy Scope A, per the
  operator's comment. Every Scope A row must state which environment
  (installed-cache fixture vs. this repo's own flows) it ran under.
- Independence: never edit any observed surface's `src/`, `test/`, or
  another issue's `docs/issue-<n>/` path outside this role's own report
  and proposal paths.
- No denominator manipulation (operator principle 4, issue body): a
  metric with an empty or thin corpus is reported deferred-with-reason,
  never rounded into a pass by shrinking its denominator.
- Coordinate, don't duplicate, with #628: #628's phase-2 hunt (signature
  classes a-h) is not yet written (confirmed this session — only its
  phase-1 survey/proposal exist). Cite its record by commit SHA once it
  exists for any surface both issues name; drive independently until
  then.
- Verdict-shaped claims require adjacent citation (fixture path +
  literal command invoked, or file:line / commit SHA) — never a bare
  "no issues found."

## What will be done

1. Build a fixture target repo, plus a simulated marketplace-cache
   fixture (`$TMPDIR`, layout matching
   `~/.claude/plugins/cache/tokenmaxxxer/on-the-record/<hash>/`: hooks
   present, no repo-root `gates/`, `CLAUDE_PLUGIN_ROOT` pointed at it) —
   per #556's documented cache layout and the operator's install-path
   requirement.
2. Scope A — drive the eleven named surfaces (#566, #476, #573/#597,
   #586, #587, core#189, #577, #576, #608, #600, #619) as constructed
   hook/CLI payloads against both fixtures, observing: gate misfires,
   hook-collision/latency across the now-stacked PreToolUse chain
   (contract-guard, pr-preflight, claim-scan-preflight,
   spec-index-preflight, impact-guard, delegated-judgment-gate), false
   refusals on honest work (#476's false_reject class), Korean-string
   regressions. Any surface unreachable in a fixture gets a row naming
   the concrete blocker, never a silent skip.
3. Scope B — for each registered metric (#476 wiring_coverage_rate,
   #566 unrecorded_requirement_rate/false_flag_rate, #573
   decision_fatigue_reduction_rate/auto_decision_reversal_rate, #587
   five-event e2e, #609/#600/#608/#619 acceptance re-runs), query the
   actual session/PR corpus and report measured-pass/measured-fail/
   deferred-with-reason, citing the registering document and the
   measurement evidence.
4. Any Scope A finding routes to remediation per the shipped machinery
   (dogfood it) — no fix lands in this branch. Any Scope B fail routes
   per each issue's registered rule.
5. Write `docs/issue-623/reports/execution-observation.md`: independence
   statement first, then the Scope A per-surface table and Scope B
   per-metric table, then the outcome/trajectory/step verdict section
   with adjacent citations, `loop_state` at a terminal value.

## Out of scope

Fixing anything found; filing issues; editing any observed surface's
source/tests or another issue's docs tree; re-running #628's
signature-class hunt (a-h) as its own deliverable — #623 drives the
same surfaces for interaction/metric evidence, and folds in #628's
record by citation once it lands, rather than reproducing its method.

## What did not work

- After-proposal warrant-hunt dispatch (stance 0) could not run: the
  first Agent-tool call named a nonexistent agent-type string and
  failed before returning a task ID, but the `hunt-guard.sh` PreToolUse
  hook had already recorded a lock ("a hunter has been running for Ns")
  before that failure surfaced. Every retry (waited up to ~90s between
  attempts) still reported the lock held, with no task ID available to
  call TaskStop against — a stale lock with no recovery path visible
  from this session. Proceeding without the after-proposal hunt dispatch
  rather than polling further; noting this so the before-landing
  dispatch attempt (or a human clearing the lock) is not surprised by
  the same stale state.

## How you'll know it worked

`docs/issue-623/reports/execution-observation.md` exists, committed,
with: a Scope A table row for every named surface (interaction finding
or evidenced absence, with the fixture path + command invoked, and
which environment — installed-cache fixture or this repo's own flows —
it ran under); a Scope B row for every named metric
(measured-pass/measured-fail/deferred-with-reason with cited evidence);
the independence statement preceding all verdict language; every
verdict-bearing sentence with an adjacent citation; `loop_state` at a
terminal value for this record kind.
