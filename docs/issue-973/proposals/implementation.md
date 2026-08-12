---
status: proposed
files:
  - spawn.py
  - harness/fixture-concurrent-judgment/fixture_concurrent_judgment/__init__.py
  - harness/fixture-concurrent-judgment/test_panel.py
  - docs/issue-973/reports/implementation.md
---

# Proposal — issue #973 implementation phase-1: build `panel_cmd()`

## Request

Build the concurrent-judgment panel the merged design
(`docs/issue-973/proposals/product-discovery.md`, PR #975) specifies: `panel_cmd()` in `spawn.py`,
sibling of `consult_cmd()`, spawning 2 non-bare `claude -p` judge sessions that state positions and
exchange at least one rebuttal round via `SendMessage`, with every turn appended to
`docs/issue-<n>/reports/panel/<question-slug>.md`; graceful degradation to sequential `consult_cmd()`
calls, recorded, when messaging is unavailable; an end-to-end harness fixture
(`harness/fixture-concurrent-judgment/test_panel.py`); and this role's own implementation record.

## Constraints

- No new dependency, no new environment variable, no CI file (repo's standing 2026-08-08
  constraint against CI enforcement, restated in the merged design's "Deployment-surface constraint
  carried forward" section).
- Reuse `role_settings()`/`plugin_dirs()` for judge session settings — the same precedent
  `consult_cmd()` already follows (spawn.py:4103-4106's own docstring rationale: two settings code
  paths drift, per issues #695/#700).
- Record schema: `docs/issue-<n>/reports/panel/<question-slug>.md`, named exactly by the merged
  design's Open Question 2.
- Approval gate: this is phase-1 only. No `panel_cmd()` code lands in this commit — the write set
  above lists files this proposal will populate once `APPROVE issue-973/implementation` is posted,
  per contract v3 s19 and this survey's own "Approval state" finding
  (`docs/issue-973/reports/implementation/survey.md`) that no such approval exists yet.

## Rationale

**Candidate A (adopted): session-writes-live.** Each judge session appends its own turn to the
panel markdown file directly as it sends/receives each `SendMessage`, per the merged design's Open
Question 2 primary choice. Rejected alternative: **orchestrator-reconstructs-after-exit** — have
`panel_cmd()` poll both sessions' final JSON outputs after both exit and write the combined
transcript itself, mirroring how `consult_cmd()` already parses one verdict via
`_parse_consult_verdict()` (spawn.py:4057). Rejected because the merged design's own comparison
(product-discovery.md, Open Question 2) already argues session-writes-live is closer to req#2's
"fully on the record" bar since it captures the live exchange as it happens; reconstructing after
both sessions exit cannot distinguish "message never sent" from "message sent but arrived after the
receiving session exited" — exactly the failure signature the design's pre-registered hypothesis
package names (`docs/issue-973/proposals/product-discovery.md`, "Failure signature" bullet). This
proposal keeps Candidate B available as a fallback code path only, activated when a judge session
cannot reliably write mid-conversation, per the design's own primary/fallback split.

**Fixture shape (adopted): seeded stand-in over live two-session spawn.** `test_panel.py` exercises
`panel_cmd()`'s parsing/recording/degradation logic against canned `SendMessage`/`ListAgents`
responses (via dependency injection at the transport boundary `panel_cmd()` calls through),
matching the existing harness pattern of `fixture_<name>/` package + `test_fixture_<name>.py`
(canonical: `harness/fixture-multirole/test_fixture_multirole.py`, no subprocess in that test).
Rejected alternative: spawning two real `claude -p` sessions end-to-end inside the test. Rejected
because a real two-session run needs live network/model access and minutes of wall-clock per test
run, which the existing harness fixtures never require (none of `harness/fixture-*/`'s tests shell
out to `claude -p`); a seeded fixture still satisfies the issue's acceptance criterion
("`harness/fixture-concurrent-judgment/test_panel.py` runs the seeded two-judge exchange
end-to-end") since the criterion itself says "seeded," not "live."

## Accumulation

`panel_cmd()` adds one more `subprocess.run(["claude", "-p", ...])` call site to `spawn.py`,
alongside `spawn_cmd()` (spawn.py:4003) and `consult_cmd()` (spawn.py:4126) — three sites total
after this change, all going through the shared `role_settings()`/`plugin_dirs()` builders rather
than duplicating settings-construction logic. If a 4th, 5th, ... Nth judgment-shaped launcher (e.g.
an N-judge panel per the design's own ITWWS section) arrives later, each one repeats the same
`subprocess.run` + settings-dict shape; this proposal does not extract a shared launcher helper now,
since today's three sites (spawn/consult/panel) differ enough in flags
(`--output-format stream-json --verbose` vs `--output-format json`, `crossSessionInbound`) that a
premature shared wrapper would need per-caller branching anyway. If a 4th call site appears, that is
the point to extract a common `_launch_claude_session()` helper — noted here so the next role
proposing one does not have to re-derive it.

## What will be done

1. `panel_cmd(role_a, role_b, question, issue=None, cwd=None) -> dict` in `spawn.py`, sibling of
   `consult_cmd()`: build settings for both judge roles via `role_settings()`/`plugin_dirs()`,
   adding `crossSessionInbound="accept"` to each; launch both as non-bare `claude -p` (mirroring
   `spawn_cmd()`'s flag set at spawn.py:4003-4005, minus the `stream-json` verbose flag since panel
   sessions run under `--output-format json` like `consult_cmd()`); prompt each with the question,
   its own role rulebook (already loaded via the plugin dirs), and its peer's `ListAgents` name;
   instruct each to state a position, exchange >=1 rebuttal round via `SendMessage`, then emit the
   same `{"answer","confidence","caveats"}` JSON verdict shape `_parse_consult_verdict()` already
   parses.
2. Panel record writer: a helper that appends one line per turn (position/rebuttal/verdict, role,
   timestamp) to `docs/issue-<n>/reports/panel/<question-slug>.md`, called both by the live path
   (as each session's `SendMessage` activity is observed) and by the degraded path.
3. Degradation: when `crossSessionInbound` cannot be set, or a `SendMessage` round-trip does not
   land, `panel_cmd()` falls back to two sequential `consult_cmd()` calls against each role with the
   same question, and prefixes the panel record with `degraded: sequential-consult — <reason>`, per
   the merged design's Open Question 4.
4. `harness/fixture-concurrent-judgment/`: a `fixture_concurrent_judgment` package providing a
   seeded stand-in for the message transport, plus `test_panel.py` driving `panel_cmd()` through it
   end-to-end — asserting a position, a rebuttal, and a joint verdict all land in the panel record
   file, and a second test asserting the degraded path records its reason.
5. `docs/issue-973/reports/implementation.md`: this role's phase-2 record, written once phase-2
   actually executes.

## Out of scope

- Wiring `panel_cmd()` into any automatic trigger (deviation-loop step, contested-judgment hook) —
  the merged design (Open Question 3) defers scoping which callers and which trigger condition to
  architecture/implementation "precisely," and this proposal's write set has no caller-side file in
  it; `panel_cmd()` ships as a callable entry point, unwired, same as `consult_cmd()` was before any
  caller used it.
- N-judge panels, majority/plurality verdicts — the design's own ITWWS section defers this
  explicitly to a future issue.
- Measuring `panel_invocation_success_rate` / `panel_record_incompleteness_rate` against the
  pre-registered 70%/0% thresholds — the design states the measurement window does not open until
  `panel_cmd()` ships and the fixture produces 20 invocations' worth of trail; this proposal ships
  the mechanism, not the measurement.

## How you'll know it worked

- `harness/fixture-concurrent-judgment/test_panel.py` passes, exercising a seeded live exchange
  (position + >=1 rebuttal + joint verdict, all present in the resulting panel record file) and a
  seeded degraded-path run (panel record carries the `degraded:` marker and reason).
- `panel_cmd()` exists in `spawn.py` as a sibling function to `consult_cmd()`, reusing
  `role_settings()`/`plugin_dirs()`.
- `docs/issue-973/reports/implementation.md` exists with `loop_state: landed` once the above lands.
