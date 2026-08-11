---
subject: issue-776
role: execution-observation
kind: survey
---

# Current-state survey (issue #776, execution-observation)

## Scope

Observed role: execution-observation, session on branch
`issue-776/execution-observation`, subject issue #776, step 3 of #776's
execution plan. Prior steps: product-discovery (PR #777, merged via
`a78b008`, approved by `APPROVE issue-776/product-discovery`) and
implementation (PR #779, merged via `1c40447` after `58b799c`, approved by
`APPROVE issue-776/implementation`) — both read this session via
`git log --oneline -20` and by reading their commit trees directly, not
summarized secondhand.

## What was read this session

- `gh issue view 776` (body + 4 comments) — the requirement, execution
  plan, and the two `APPROVE` comments for the prior two roles.
- `docs/specs/northpole-harness.md` (commit `58b799c`) — the frozen design
  spec: fixture repo shape, the representative requirement text, the 7
  per-requirement signal table (§3), the zero-human-intervention
  observation method (§4), and the build-and-run assertion (§5).
- `harness/README.md`, `harness/driver.py`, `harness/signals.py`,
  `harness/run_smoke.py` (all landed in `58b799c`) — the actual built
  harness: `driver.instantiate_fixture_target`/`get_representative_requirement`/
  `run_build`/`run_version_check`/`run_tests`/`capture_transcript`, and
  `signals.evaluate_all` consuming a `transcript` dict + `repo_state` dict
  + build/run results to emit the 8-row PASS/FAIL/UNMEASURED report.
- `docs/issue-776/reports/product-discovery/survey.md` and
  `docs/issue-776/reports/implementation/survey.md` — prior roles' own
  current-state framing.

## What step 3 actually requires, per the harness as built

`harness/README.md`'s own "Run the real baseline later" section states the
gap plainly: `driver.py` performs operator-only actions (instantiate a
clean fixture-target copy, run build/test commands, hold the requirement
text) but **does not launch a live Claude Code session itself** —
`capture_transcript` is an explicit placeholder that returns its input
unchanged, "callers own the actual parsing once a real session transcript
format is available." There is no code path in `harness/` today that:

1. installs the on-the-record plugin into an instantiated fixture-target
   copy,
2. launches a fresh plain Claude Code session against that copy with the
   representative requirement as its first and only message, or
3. captures that session's transcript into the `delegation_events` /
   `final_report` / `reached_midcourse_moment` / `human_input_stalls` /
   `skill_explicitly_invoked_by_operator` shape `signals.py` consumes.

`signals.py` itself is fully built and was already exercised (only) against
a synthetic fixture by `run_smoke.py` — that run is explicitly labeled "NOT
a live baseline run against a real session."

## Environment constraint this session sits inside

This session is itself a headless Claude Code invocation (subagent-spawned,
no interactive terminal, no ability to launch and babysit a second,
independent, long-running Claude Code session against a separate fixture
repo while remaining unresponsive to it per spec §4's "do not respond to
anything else until it halts or a wall-clock cap is reached"). Launching
that second session is the one action spec §4 requires and this session's
own execution context cannot itself perform as a nested, isolated,
zero-intervention Claude Code launch — that gap is the central fact this
survey surfaces for the proposal to address.
