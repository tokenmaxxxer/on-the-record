---
status: proposed
files:
  - docs/issue-776/reports/execution-observation.md
---

# Northpole E2E harness — baseline execution (issue #776 step 3)

## Intent

Run the harness built in step 2 (PR #779, `58b799c`) for real: install
on-the-record as the fixture-target repo's only plugin, drive the one
representative requirement into a fresh plain session with zero human
intervention, and record each of the 7 signals + build-and-run as
PASS/FAIL/UNMEASURED with the concrete evidence observed — the BASELINE,
not a re-inference of the design spec.

## Constraints stated so far

- Provenance must be `executed-live`: every signal verdict cites actual
  command output or session-transcript content from this run, never a
  guess. A signal the live run cannot reach is `UNMEASURED` with the
  reason, never a guessed PASS (issue body's own empty-state rule).
- Never edit `harness/`, `docs/specs/northpole-harness.md`, or
  `docs/handbooks/northpole-harness.md` — those are the implementation
  role's artifacts; this role only runs them and records what happened.
- Write set is `docs/issue-776/**` only (this role's own record), per the
  execution-observation role directive.
- The observed session must be launched with zero framing beyond the
  representative requirement text (`harness.driver.get_representative_requirement()`)
  as its first and only message — no explicit skill invocation by the
  operator (spec §7's inviolable constraint).

## What will be done

1. `harness.driver.instantiate_fixture_target(dest)` into a scratch
   directory to get a clean fixture-target working copy.
2. Install the on-the-record plugin into that copy the same way the
   fixture's `.claude-plugin/marketplace.json` declares it (Claude Code
   plugin install, not a repo-level skill/command reference).
3. Launch one `claude -p` session rooted in that copy, with
   `get_representative_requirement()`'s text as the sole prompt, and let it
   run to completion unattended (session log captured to a file) up to a
   wall-clock cap.
4. Build the `transcript` / `repo_state` dicts `signals.evaluate_all`
   expects from the captured log and the resulting working copy's file
   state — no field invented; a field the log doesn't evidence is left
   absent so its dependent signal reads `UNMEASURED`.
5. Run `driver.run_build` / `driver.run_version_check` / `driver.run_tests`
   against the resulting copy (signal #3 / build-and-run, run by the
   harness itself, never taken from the session's own claim).
6. Call `signals.evaluate_all(...)` and write
   `docs/issue-776/reports/execution-observation.md` with each of the 8
   rows, its verdict, and the concrete evidence (log excerpt, command
   output, or file content) backing that verdict.

## Out of scope

- Fixing any gap the baseline finds — that is a future implementation-role
  step against a new backlog row, not this role's job.
- Re-running the harness after any fix (that is the re-run step the spec's
  §6 decision rule describes for later).
- Editing `harness/` itself, even if the live run reveals the
  transcript-capture placeholder (`driver.capture_transcript`) needs a real
  parser — that finding goes into the record as a finding, not a live edit.

## How this will be known to have worked

`docs/issue-776/reports/execution-observation.md` exists, is committed on
this branch, states `loop_state: handed-off` (or the correct non-terminal
state if the live run could not complete), and every one of its 8 rows
carries either a PASS/FAIL with cited evidence or an UNMEASURED with a
stated reason — never a silently omitted row and never a guessed verdict.

## What did not work

(appended live, during phase 2, if applicable)
