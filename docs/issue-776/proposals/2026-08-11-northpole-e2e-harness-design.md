---
status: proposed
files:
  - docs/issue-776/reports/product-discovery/survey.md
  - docs/issue-776/reports/product-discovery/scout-brief.md
  - docs/issue-776/proposals/2026-08-11-northpole-e2e-harness-design.md
  - docs/specs/northpole-harness.md
---

# Northpole E2E acceptance harness — design (issue #776)

## Intent

Design (not build — that is step 2/3 of issue #776's execution plan) a
reproducible harness that judges, by actually running a session, whether
each of the 7 `docs/specs/northpole.md` requirements is met — replacing
`docs/issue-749/reports/conformance-review.md`'s static-reading verdict
with an execution-based one, and giving the 17-row backlog a pre-registered
pass/fail rule instead of a felt impression of progress.

## Constraints stated so far

- Fixture repo: fresh, minimal, real-buildable, NOT the on-the-record repo
  itself; on-the-record installed as a plugin and nothing else — no CI, no
  explicit skill invocation (req #7's own reach test).
- One representative user requirement, given to a plain session.
- Zero human intervention during the run.
- Each of the 7 requirements maps to >=1 observable pass/fail signal.
- A build-and-run assertion on the produced artifact.
- Pre-registered decision rule, fixed before any fix lands (hypothesis-
  testing discipline): requirement-satisfied = its signal passes.
- Empty state: a requirement with no observable signal emits UNMEASURED,
  never silently passed.
- Scope: design only. Building the harness (step 2) and running it for a
  baseline (step 3) are separate, later execution-plan steps.

## What will be done

Full design lives in `docs/specs/northpole-harness.md` (the write set
above). Summary:

### 1. Fixture target repo

A new, separate minimal repo (not nested in on-the-record) — smallest
real-buildable unit possible: a single-file Python CLI
(`fixture-target/`, `pyproject.toml` + one module + one test) so "build
and run" has an unambiguous mechanical check (`pip install -e . && target
--help` exits 0; `pytest` exits 0). No `.github/workflows/`, no CI config,
no repo-level skill/command invocation of any kind. on-the-record is added
as a Claude Code plugin dependency only (`.claude-plugin` install path),
mirroring req #7's own install-only bar. The repo starts with one seeded
defect (see requirement below) so the representative requirement has real
work to do, not a no-op.

### 2. Representative user requirement

Given verbatim to a plain session with no other framing: "The CLI's
`--version` flag currently crashes with a stack trace instead of printing
the version — fix it, and make sure the fix is tested." This is
deliberately small (bounded blast radius, single true root cause,
mechanically checkable) but exercises every requirement's mechanism: it
needs orchestration (#1), produces artifacts needing a record (#2), needs
a real build+run to confirm the fix (#3), must complete with a legible
report (#4), and — the seeded defect is chosen so its root cause is one
layer removed from the obvious fix (the crash is in an argument-parsing
helper the CLI author didn't write), forcing a mid-course "why does this
still crash" moment that only resolves via role composition (#5), not a
one-shot patch.

### 3. Per-requirement signal (pre-registered, checked before any fix)

| # | Requirement | Signal | Pass condition |
|---|---|---|---|
| 1 | Orchestration to completion | Session transcript/log shows a delegation event (spawn/sub-agent call) between requirement-statement and final report | >=1 delegation event exists AND a final report is emitted |
| 2 | Full record-ability | A fresh session (no chat history) can state what changed and why using only repo files, zero chat context | Fresh-session read-back correctly names the fix and its rationale |
| 3 | Real-wired verification | The produced artifact is checked out fresh and (a) `pip install -e . && target --version` exits 0 and prints a version string, (b) `pytest` exits 0, run by the harness itself, not narrated by the session | Both commands exit 0 when the harness runs them independently |
| 4 | Autonomous completion + human-legible reporting | Final report states: what broke, what changed, what became possible, what limits remain — 4 named parts | All 4 parts present in the final report text |
| 5 | Problems are not pushed back to the human | The mid-course "still crashes after obvious fix" moment (built into the seeded defect) is resolved without a `<user-input-needed>`-shaped pause; resolution path is recorded in-repo | Zero human-input requests during the run AND a recorded resolution trail exists |
| 6 | Condensed requirement management | The one requirement given at the start is traceable, in condensed form, in exactly one place in the resulting repo (not scattered across N files with drift) | A single canonical requirement record exists and matches the original ask |
| 7 | Inviolable constraint — default-on, plugin-only, no explicit invocation | All 6 signals above fire with the fixture repo in its as-installed state — no skill was explicitly invoked, no CI was configured, only plugin install | Signals 1-6 each pass under this install-only precondition; if any signal above only fires when a skill was explicitly typed by the harness operator, req #7 fails independently of that signal's own verdict |

Empty-state rule: if a signal cannot be observed at all (e.g. the session
never produces a final report to inspect for #4), the row emits
`UNMEASURED`, distinct from `FAIL` — a signal that never got the chance to
run is not the same claim as a signal that ran and failed.

### 4. Zero-human-intervention observation method

The harness operator's only actions are: (a) install the plugin into the
fixture repo, (b) paste the one representative requirement into a fresh
session, (c) do not respond to anything else until the session halts on
its own or a hard wall-clock cap is hit. Observation is post-hoc only:
the full session transcript/log is captured and scanned (not steered) for
(i) any point where the session emitted a request the operator did not
answer (a stalled human-input request counts as an intervention point and
fails signal #5 and the run overall for that dimension) and (ii) the
delegation/report events signals 1-4 and 6 check for. This mirrors the
scout brief's "human effort upfront-only" pattern (Human-on-the-Bridge):
the human curates the fixture and the requirement once, never mid-run.

### 5. Build-and-run assertion

Independent of anything the session claims: after the session halts, the
harness checks out the fixture repo's resulting state into a clean
environment and runs, itself:
```
pip install -e . && target --version   # must exit 0, print a version
pytest                                  # must exit 0
```
This is the harness's own execution, not a re-statement of the session's
log — directly satisfying req #3's "not mockups / doc-only / code-analysis
tests, but actually building and running." A session claiming success
whose artifact fails this check is a FAIL on signal #3 regardless of what
the transcript says.

### 6. Pre-registered decision rule

`requirement-satisfied = its row's signal passes`, fixed by this document
before any of the 17 backlog fixes lands. Re-running the harness after
each fix flips exactly the rows that fix targeted, or the fix didn't do
what the backlog row claimed. If all 17 rows land and a signal still
fails, the row list was incomplete, per issue #776's own escape clause —
that finding routes back to conformance-review.md as a new gap, not a
harness redesign.

## Candidate comparison (RICE)

Compared during current-state survey (`survey.md`'s OST section):

| Candidate | Reach | Impact | Confidence | Effort | RICE (R*I*C/E) |
|---|---|---|---|---|---|
| (a) This harness (fixture + driven session + signals) | 7/7 requirements | 3 (high — replaces the only evidence source) | 0.7 | 3 (person-weeks-equivalent to build+run) | 4.9 |
| (b) Re-read code after each fix | 7/7 requirements | 1 (low — same method that produced the unproven backlog) | 0.9 (easy, known method) | 0.5 | 12.6 (high score, rejected: does not test the discriminating assumption — see below) |
| (c) Trust each fix's PR self-report | 7/7 requirements | 0.5 (low — req #3/#4 explicitly distrust self-report) | 0.5 | 0.2 | 8.75 (high score, rejected on the same ground) |

(b) and (c) score higher on raw RICE because they're cheap and confident,
but confidence here measures "will this be easy to execute," not "will
this answer the actual question" — RICE's Impact term is where that's
supposed to be captured, and both are scored low-Impact specifically
because they reproduce the method whose output is in question (issue
#776's own framing: "the backlog diagnosed req #3 by violating req #3").
Candidate (a) is selected despite lower raw RICE because it is the only
candidate that tests the discriminating assumption at all.

## Out of scope

- Building the harness (issue #776 step 2, a separate execution-plan
  step / separate role session).
- Running the harness for a baseline (step 3).
- Extending the harness to more than one representative requirement, or
  to a benchmark-scale fixture suite (scout brief: adopt single-fixture,
  skip general eval-platform infra as out of proportion to this issue).
- Modifying `docs/specs/northpole.md` or the 17-row backlog itself.

## How you'll know it worked

`docs/specs/northpole-harness.md` exists, is readable by a session with no
prior context on issue #776, and contains: the fixture repo's shape, the
representative requirement's exact text, the 7-row signal table with
pass/fail conditions and the UNMEASURED empty-state rule, the zero-
intervention observation method, the build-and-run commands, and the
pre-registered decision rule — sufficient for a later implementation
session (step 2) to build the harness without design decisions of its
own.

## Accumulation

Not accumulation-cost-shaped: this proposal is a one-time design
document, not a recurring resource whose per-unit cost compounds (no
growing list, no per-instance-scaling artifact). N/A.
