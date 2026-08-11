---
status: proposed
files:
  - docs/issue-870/reports/product-discovery/survey.md
  - docs/issue-870/reports/product-discovery/scout-brief.md
  - docs/issue-870/proposals/2026-08-11-generalized-fake-success-detection.md
---

# Proposal — generalize fake-success detection, default-on (issue #870, phase 1: design)

## Intent

Design, plugin-only and default-on, how any target-repo session catches
a claimed-but-not-real "requirement met / done" — generalizing the
discipline that already caught fake successes on this session
(canonical-source citation, re-measurement instead of trusting a claim,
actual build/run, reading ground truth in full) from this repo's own
harness into any installed session's normal delivery flow.

## Constraints (from the issue + directives)

- Default-on via plugin hooks/directives only — no CI, no explicit
  invocation (req #7).
- Must not false-PASS: an unmeasurable target degrades to an explicit
  `UNMEASURED-with-reason`, never a silent pass.
- Must not add friction to a genuinely backed done-claim.
- Composes with, does not duplicate, #793's existing
  `canonical_source_claim_check` (state/defect-claim citation
  presence).

## Evidence cited

- code observation, 2026-08-11, paraphrase: `gates/record_lint.py`'s
  `canonical_source_claim_check` (landed for #793) requires a
  `canonical:` tag near a state/defect claim but never inspects what
  kind of source that tag names — a citation reading "role's own
  summary" passes identically to one reading "gh pr view --json files"
  (derived: `gates/record_lint.py:148-183`).
- in-repo incident observation, 2026-08-11, paraphrase: four re-run
  records in this session's own history (PRs #845, #855, #867; #787's
  independent rerun) each found the prior attempt's PASS/done claim
  did not survive a fresh, live re-execution — the failure was caught
  only because an operator chose to re-run, not because any default-on
  mechanism forced it (canonical: docs/issue-870/reports/product-discovery/survey.md, "Background / context" section, read this session).
  - unverifiable: whether an UNGATED equivalent claim exists elsewhere
    in the repo's history that was never caught, since by definition an
    uncaught fake success leaves no record distinguishing it from a
    true success — this proposal's own case for default-on gating rests
    on the ones that WERE caught manually, not on a count of ones that
    were not.
- external documentation observation, 2026-08-11, paraphrase: the
  official Claude Code hooks reference confirms `PreToolUse` can block
  a tool call before it runs, `Stop`/`SubagentStop` can block a
  turn/subagent from ending, and `TaskCompleted` can block a task from
  being marked done — no other event type carries block capability over
  an outcome decision (canonical: https://code.claude.com/docs/en/hooks,
  fetched this session; see scout-brief.md).

No stated-preference or hypothetical evidence used (Mom Test rule) —
all three items are direct code/incident/documentation observations.

## Candidates (the issue's own a/b/c) — RICE scoring

Reach (fraction of outcome-claiming writes/turns affected per session),
Impact (1-3: a real fake success prevented vs. cosmetic), Confidence,
Effort (person-weeks equivalent):

| Candidate | Reach | Impact | Confidence | Effort | RICE |
|---|---|---|---|---|---|
| (a) — write-time citation-kind gate for outcome claims | 0.7 (fires on every record write asserting met/done/PASS, the same surface `canonical_source_claim_check` already covers, one layer up) | 2 (catches a claim with no citation, or a citation naming a non-executed source — does not itself verify the citation's truth, same limit #793 already accepts) | 0.7 (mechanical extension of a shipped gate; the new part — classifying a cited source as "executed-live" vs. "read/summary" by surface form — is a bounded regex/keyword problem, not semantic judgment) | 1 | 0.7×2×0.7/1 = 0.98 |
| (b) — per-target acceptance command, run before accept | 0.5 (only fires where a target has an acceptance command set — see degrade-path below; reach is lower than (a) until most targets have one configured) | 3 (the only candidate that runs REAL execution against the REAL current target — directly matches what actually caught #776/#787's fake successes: build+run, not a citation) | 0.5 (feasible per the scout brief's `Stop`/`SubagentStop`/`TaskCompleted` block capability, but needs new plumbing: a stored per-target command, a confirmed-setup flow mirroring #831, and a degrade path — more moving parts than (a)) | 2.5 | 0.5×3×0.5/2.5 = 0.3 |
| (c) — independent adversarial re-verify before accept | 0.3 (only applies where a second role/session is already part of the delivery flow — e.g. role-handoff contract's phase-2 record path — not every single-session turn) | 3 (structurally the hardest to fool: a separate session with no stake in the original claim, the exact pattern this session's orchestrator used manually against #787/#845/#855/#867) | 0.3 (cannot be a hook body itself — a hook can only trigger a dispatch, per the scout brief's finding that a `prompt`/`agent` hook type cannot itself independently judge a same-session claim's truth; real independence needs a second session/role, which is orchestration-layer, not a single hook) | 3 | 0.3×3×0.3/3 = 0.09 |

Reach data above is derived from each candidate's own trigger surface
(existing gate's per-write firing pattern for (a); target-acceptance
configuration state for (b); phase-2 hand-off frequency for (c)), so
RICE applies directly — no ICE fallback needed.

(a) wins on RICE and is cheapest; (b) is the only candidate that
supplies REAL execution evidence, which is what the cited incidents
show actually caught the fake successes — (a) alone would have caught
none of the four re-run incidents, since each one already carried a
plausible-looking citation (a prior transcript, a summary, a grep
hit), just not an executed-live one. This is why the recommendation
below ships (a) and (b) together rather than picking the single
highest-RICE candidate in isolation: they close different halves of
the same gap (citation-kind presence vs. citation-kind truth-by-actual-
execution), and #793's own precedent already established that a cheap,
narrow, write-time gate is deliberately paired with — not a
replacement for — the more expensive check it cannot itself perform
(compare #793's own explicit ruling-out of candidate C "full automated
re-verification" as a hook body, while still recommending #791 compose
alongside it for the row it cannot cover).

## What will be done (design output of this phase)

### Ship default-on: (a) + (b). Do not ship (c) as a default-on hook.

**(a) — extend `canonical_source_claim_check` to outcome claims,
citation KIND not just presence.**

- New marker vocabulary, sibling to `_STATE_CLAIM_MARKER`:
  outcome-claim markers (`\brequirement(s)?\s+met\b`, `\bdone\b`,
  `\bPASS\b`, `\bpasses\b`, `\bcomplete(d)?\b` in a claim-shaped
  sentence) — same deliberately-narrow, known-bypassable-by-synonym
  tradeoff #793 already accepts for its own vocabulary, same
  append-only widening policy.
- When an outcome marker fires, the required `canonical:` tag must
  additionally match an EXECUTED-LIVE shape, not just be non-empty:
  a command string (`gh ...`, `pytest ...`, `python3 gates/...`, a
  `spawn.py` invocation), or an explicit `acceptance: <command> —
  result: PASS|FAIL|UNMEASURED` line (see (b) below) — a bare file-read
  citation (`docs/... (read this session)`) satisfies #793's existing
  state-claim check but does NOT satisfy this new outcome-claim check,
  since a file read is a summary/prior-state signal, not a fresh
  execution.
- Fail-closed: an outcome marker with no qualifying citation is
  refused at `PreToolUse`, same enforcement point and same shell
  script (`on-the-record/hooks/record-claim-guard.sh`) #793 already
  uses — no new hook registration needed, one new check function
  wired into the existing `lint_record()` list.
- Empty state: a write with no outcome-claim marker is untouched,
  identical to #793's own empty-state scoping.

**(b) — per-target `acceptance:` command, confirmed once, run before a
`done` claim is accepted; degrades to `UNMEASURED-with-reason`.**

- Setup, mirroring #831's `ensure_target_remote` shape exactly: the
  first time a session in a target repo is about to write an outcome
  claim and no `acceptance:` command is on record for that target,
  prompt once (attended sessions only, gated the same way #831 gates
  on the `unattended` flag) — "what command proves this target's
  deliverable actually works (build/test/`--version`, etc.)?" — record
  the answer via the same `ledger_write` mechanism #831 uses
  (`{"event": "acceptance_command_confirmed", "command": ..., "ts":
  ...}`), then never re-ask unless the recorded command starts failing
  to even execute (distinct from failing its own check — a syntax
  error / missing binary means the recorded command itself needs
  re-confirmation, not that the deliverable is broken).
- Enforcement point: per the scout brief, `Stop`/`SubagentStop` is the
  event type able to block a turn/subagent from ending — a `Stop` hook
  checks whether this turn's transcript contains an outcome claim
  written this turn; if so, and an `acceptance:` command is on record
  for this target, the hook runs it (bounded timeout, matching the
  `timeout` field the scout brief's hook-options table documents) and
  requires the outcome claim's citation to match that run's actual
  exit status — a claim of "done"/PASS backed by a run that exited
  non-zero, or backed by no run at all when a command IS on record, is
  refused (`decision: "block"`, per the scout brief's Stop/SubagentStop
  decision-control shape), forcing the turn to continue and correct the
  claim instead of silently completing.
- Degrade path (never a false PASS): no `acceptance:` command on record
  for this target (setup was declined, or the target genuinely has none
  yet) → the outcome claim is not blocked, but the `Stop` hook rewrites
  or requires an `additionalContext`/citation stating
  `UNMEASURED-with-reason: no acceptance command on record for this
  target` — matching `acceptance_gate.py`'s existing `unverifiable:`
  escape-hatch shape (issue #310's pattern), reused rather than
  reinvented.
- This generalizes #776's `build_and_run` from "one fixture target,
  operator-driven" to "any target, plugin-driven, one-time-confirmed
  command" — the same generalization #831 already performed for the
  GitHub-remote precondition.

### Do not ship (c) as a default-on hook; note it as a composition point only

Per the scout brief's finding, no hook event type can host a
genuinely-independent judgment of a same-session claim — a `prompt`
hook still evaluates from inside the claiming session's own context in
spirit (it has no separate memory/stake, but more importantly it
cannot itself dispatch a second session, only render a yes/no from a
model call). Adversarial re-verify needs a structurally separate
session or role, which is what role-handoff contract v3 s19's own
phase-1/phase-2 approval split and the (already-existing, non-hook)
`warrant-hunter` background-dispatch pattern already provide at the
orchestration layer. Recommendation: (c) is not a new hook to build;
it is a documentation point — the phase-2 approval gate (a human, or a
second role, must explicitly approve before phase-2/record work lands)
already IS the adversarial-re-verify moment this issue asks about, and
(a)+(b) are what make that human/second-role's job checkable (they see
a `canonical:`/`acceptance:` citation to look at, rather than a bare
assertion) rather than a new mechanism replacing it.

## How (a) and (b) compose

(a) fires first, at write time, cheap, catches the citation-shape gap
(no citation, or a citation that is transparently not an execution).
(b) fires second, at turn-end, catches what (a) structurally cannot:
a citation that LOOKS like an execution reference but the execution
either did not happen this turn or did not actually pass — the exact
shape of the #845/#855/#867/#787 incidents, where a citation existed
(a prior transcript, a summary) but was not itself current, live, or
against the real target. Neither subsumes the other: (a) is citation
presence-and-shape at write granularity; (b) is citation truth at
turn-granularity, the only point a real command can be re-run and
compared.

## Plugin-only / no-forced-CI feasibility (req #7)

Confirmed feasible for both (a) and (b) using only plugin `hooks.json`
entries, per the scout brief's canonical:
https://code.claude.com/docs/en/hooks reading: (a) is a `PreToolUse`
`command` hook (bash + the extended `record_lint.py`), identical
registration shape to #793's shipped hook. (b) is a `Stop`/
`SubagentStop` `command` hook plus a small setup prompt inside an
existing `SessionStart`-adjacent flow (matching #831's exact prior
precedent for the same shape of one-time confirmed fact). No CI
workflow, no explicit skill invocation, no new install step beyond the
plugin itself — the operator installs `on-the-record` and both fire by
default from that point on, exactly req #7's bar.

## Out of scope

- Implementing the two hooks/gate functions (phase 2, pending
  approval).
- Widening the outcome-claim marker vocabulary beyond the initial
  narrow set (append-only follow-up, same as #793's own noted
  limitation).
- Building (c) as a hook (recommended against above; the existing
  phase-2 human/role approval gate already occupies that role).
- Verifying an outcome claim's SEMANTIC correctness beyond citation
  kind and exit-status match — an executed-live command that itself
  passes a wrong or incomplete acceptance test is out of scope, same
  boundary #776's harness and #793's citation check both already draw.

## How you will know it worked

Phase 2's acceptance (per the issue): in a fresh installed target
session, a deliverable claiming the requirement is met with no
executed-live citation is refused/flagged by default (candidate (a));
a deliverable whose recorded `acceptance:` command actually passes is
accepted (candidate (b)); where no `acceptance:` command is on record,
the outcome is `UNMEASURED-with-reason`, never a false PASS (candidate
(b)'s degrade path). Empty state: no done-claim made → no verification
demanded, no error (both candidates' existing empty-state scoping).

## Accumulation

Not accumulation-cost-shaped in the same sense as a per-instance
recurring cost — (a) is one new check function added once to an
existing gate list (the same shape #793 already added). (b) does carry
a small recurring cost worth naming: each target repo pays a one-time
setup prompt (mirroring #831's own accepted one-time cost for the
remote preflight), and each `Stop`/`SubagentStop` firing pays one
bounded-timeout command execution per turn that contains an outcome
claim — bounded by the `timeout` hook option (scout-brief.md), and
scoped to fire only on turns that actually assert an outcome, not
every turn.

## What did not work

None.
