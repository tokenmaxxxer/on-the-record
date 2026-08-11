# Northpole E2E acceptance harness — design spec

Status: designed (issue #776 step 1), not yet built. Building it is issue
#776 step 2; running it for a baseline is step 3. This spec is the frozen
design contract those later steps build against — see
`docs/issue-776/proposals/2026-08-11-northpole-e2e-harness-design.md` for
the rationale behind each choice.

## 1. Fixture target repo

A new, separate, minimal repo — NOT nested inside on-the-record.
Smallest real-buildable unit: a single-file Python CLI.

```
fixture-target/
  pyproject.toml
  fixture_target/__init__.py   # CLI entrypoint, argument parsing helper
  test_fixture_target.py       # one test file
```

- No `.github/workflows/`, no CI config of any kind.
- No repo-level skill or command invocation — on-the-record is present
  only via Claude Code plugin install (`.claude-plugin` path), nothing
  else in the repo references it.
- Seeded defect at repo creation: `--version` crashes with a stack trace
  (the crash lives in the argument-parsing helper, one layer removed from
  the CLI entrypoint the obvious fix would touch — this is what forces a
  real mid-course "why does this still crash" moment for signal #5).
- Build/run mechanically checkable via:
  ```
  pip install -e . && fixture-target --version
  pytest
  ```

## 2. Representative user requirement

Given verbatim, as the entire first message, to a fresh plain session with
on-the-record installed and no other framing:

> The CLI's `--version` flag currently crashes with a stack trace instead
> of printing the version — fix it, and make sure the fix is tested.

## 3. Per-requirement signals (pre-registered before any backlog fix)

| # | Requirement | Signal | Pass condition | Empty state |
|---|---|---|---|---|
| 1 | Orchestration to completion | Transcript shows >=1 delegation/spawn event between requirement statement and final report | Event present AND final report emitted | UNMEASURED if session produces no transcript to inspect |
| 2 | Full record-ability | A second, fresh session (no chat history, repo files only) can correctly state what changed and why | Fresh-session read-back names the fix and its rationale correctly | UNMEASURED if no record file exists to read |
| 3 | Real-wired verification | Harness itself (not the session) checks out the resulting repo state fresh and runs the build+run commands (§5) | Both commands exit 0, independently run by the harness | UNMEASURED if the run never reaches a checkout-able state |
| 4 | Autonomous completion + human-legible reporting | Final report states 4 named parts: what broke, what changed, what became possible, what limits remain | All 4 parts present | UNMEASURED if no final report is emitted |
| 5 | Problems are not pushed back to the human | Seeded defect's non-obvious root cause forces a mid-course moment; check for any stalled human-input request during the run, and for a recorded resolution trail | Zero human-input stalls AND a resolution trail exists in-repo | UNMEASURED if the run halts before reaching the mid-course moment at all |
| 6 | Condensed requirement management | Exactly one canonical, current record of the original requirement exists in the resulting repo | Single canonical record exists and matches the original ask, no drift across duplicates | UNMEASURED if no requirement record exists anywhere |
| 7 | Inviolable constraint — default-on, plugin-only, no explicit invocation | Signals 1-6 evaluated under the as-installed precondition: no skill was explicitly invoked by the harness operator, no CI configured | All of signals 1-6 pass under that precondition | Independent FAIL (not UNMEASURED) if any of 1-6 only passed because the operator explicitly invoked a skill |

A signal that never got the chance to run (the session halted before that
checkpoint) is recorded `UNMEASURED`, never silently scored as pass or
fail.

## 4. Zero-human-intervention observation method

Operator actions, in order, and nothing else until halt-or-cap:
1. Install the on-the-record plugin into the fixture repo.
2. Paste the representative requirement (§2) verbatim as the first and
   only message to a fresh session.
3. Do not respond to anything else the session emits until it halts on
   its own or a wall-clock cap is reached.

Observation is entirely post-hoc: the full transcript/log is captured and
scanned for delegation events, report content, and any point where the
session emitted an unanswered request for human input (each such point is
itself an intervention-point and fails signal #5 and, transitively, the
run's overall #7 verdict). The harness never steers the run mid-flight.

## 5. Build-and-run assertion

Run by the harness itself, against a clean checkout of the fixture repo's
state after the session halts — never a restatement of what the session
claimed:

```
pip install -e . && fixture-target --version   # must exit 0, print a version string
pytest                                          # must exit 0
```

A session-claimed success whose artifact fails either command is a FAIL
on signal #3, regardless of transcript content.

## 6. Pre-registered decision rule

`requirement-satisfied = its row's signal (§3) passes`, fixed by this
document before any of the 17 `docs/issue-749/reports/conformance-review.md`
backlog rows is fixed. Re-running this harness after a backlog fix lands
should flip exactly the row(s) that fix targeted; a fix that lands without
flipping its targeted row means the fix did not do what the backlog row
claimed. If all 17 rows land and a signal still fails, the backlog was
incomplete — route that as a new finding back into conformance-review.md,
not as a redesign of this harness.
