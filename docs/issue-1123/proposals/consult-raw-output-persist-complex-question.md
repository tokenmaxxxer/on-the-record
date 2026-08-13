---
status: proposed
files:
  - spawn.py
  - gates/test_consult_json_parse.py
  - docs/reports/consult-log.md
  - docs/issue-1123/reports/consult-log.md
---

## Request

#1123: the #1119 fix (skip self-hosted-hook injection at consult call
sites) removed one overhead source but a second failure mode still hits
`판단 JSON 을 못 찾음` for a longer, multi-part question. Root-cause it
using the model's actual raw output (persist it on parse failure — it
isn't persisted today), make complex questions return a verdict with
loud degradation instead of a silent same-shape retry, and extend the
regression guard with a complex-question case.

## Constraints

- Two-phase flow applies (no `CORE_BUILD_NOW`) — this PR is phase-1 only:
  survey + proposal, no code changes yet.
- `consult_cmd()` must stay a pure judgment call — no branch/commit/PR,
  per `on-the-record/commands/consult.md`.
- Every consult attempt still traces exactly one line to
  `docs/reports/consult-log.md` (or the issue-scoped variant), success or
  failure — "no traceless consult" is an operator decision, not
  renegotiable here.
- Raw-output persistence must not blow up trace-file size on every
  failure — write full text to a side file, keep the trace line a
  pointer plus a bounded excerpt.

## Rationale

Considered fixing this purely by raising `CONSULT_TIMEOUT` for longer
questions (detect length, scale timeout). Rejected: without the raw
output from the actual 00:35:18 failure, there is no evidence timeout
(vs. truncation, vs. a still-present prompt-budget drain) is the real
cause — guessing at a timeout bump would be exactly the kind of
unfalsifiable fix the issue is warning against repeating (#1119 already
shipped one fix for the same symptom that turned out to be necessary but
not sufficient). The raw-output persistence is the prerequisite the
issue itself names first, so it goes in before any retry/timeout
behavior changes, not alongside a guessed timeout fix.

Considered making `consult_cmd()` return a degraded verdict object
(`{"answer": None, "degraded": true, ...}`) instead of raising, so
programmatic callers (e.g. `panel_cmd`'s `_consult_or_record_error`) get
a value rather than an exception. Rejected for the CLI path: `spawn.py
consult` already surfaces failure loudly via `sys.exit(f"consult
실패(트레이스는 남았다): {e}")` — that's non-silent today. This
proposal's "loud degradation" fix targets the raw-output/diagnosis gap
and the fixed-retry-budget gap (hypothesis C in the survey), not the
CLI's already-loud exit path.

## What will be done

- `spawn.py`: on parse failure (either attempt), write the raw `result`
  text to a side file under
  `docs/issue-<n>/reports/consult-raw-failures/<ts>-<attempt>.txt` (or
  `docs/reports/consult-raw-failures/...` when no `--issue`), via a
  single shared helper (see Accumulation), and record its path plus a
  short excerpt in the trace `outcome` string so a recurrence is
  diagnosable from the trace alone.
- `spawn.py`: after persisting the raw output, root-cause via the
  persisted text at implementation time (phase 2) whether the retry
  exhausted `CONSULT_TIMEOUT`, whether the JSON was truncated, or
  something else — the phase-2 fix (timeout scaling / retry-prompt
  change / other) is scoped by whatever the raw output actually shows,
  not decided here.
- `spawn.py`: `consult_cmd()`'s final `RuntimeError` message, when raised
  after both attempts still lack JSON, includes the raw-output file path
  so the loud failure is also a diagnosable one.
- `gates/test_consult_json_parse.py`: add a case reproducing the
  00:35:18 shape — a fake model response that is long/multi-part and
  either lacks JSON entirely or is truncated mid-object — asserting (a)
  the existing loud-failure behavior still holds, and (b) the raw output
  landed in a side file referenced from the trace line.
- `docs/reports/consult-log.md`: phase-2 live smoke with an actual
  multi-part question, logged `ok:`, once the fix lands.

## Out of scope

- Changing `CONSULT_TIMEOUT`'s value or making it question-length-aware
  — decided in phase 2 once the raw output shows whether timeout is
  actually implicated.
- Changing `panel_cmd`/`_consult_or_record_error`'s degrade-and-continue
  behavior — that path already treats `consult_cmd` failure as
  non-fatal by design (docstring at spawn.py:4579) and is out of this
  issue's scope.
- Any change to `_parse_consult_verdict`'s parsing algorithm itself —
  the survey found it length-insensitive by design; changing it is not
  indicated without raw-output evidence otherwise.

## Accumulation

The change touches `consult_cmd()`'s existing `subprocess.run` call site
(spawn.py:4423-4424) only to add raw-output persistence on the failure
branch already there — it does not add a new inline `subprocess`/`gh`
call site, and does not touch any `roles/*.json`-style repeated-file
list. If this persist-raw-output-on-parse-failure pattern is needed at N
more call sites in the future, it should factor into a shared helper
rather than being copy-pasted per call site — this proposal writes it as
a single private helper in `spawn.py` for exactly that reason, so a
second call site (e.g. `_run_panel_session`) can reuse it instead of
duplicating the side-file-path logic.

## How you'll know it worked

- `python3 gates/test_consult_json_parse.py` passes, including the new
  complex-question case.
- A live smoke with a real multi-part/tradeoff question logs `ok:` in
  `docs/reports/consult-log.md` (phase 2).
- If a future consult attempt still fails to find JSON, the trace line
  points to a raw-output file that actually contains the model's
  output — the unfalsifiability gap the issue names is closed.
