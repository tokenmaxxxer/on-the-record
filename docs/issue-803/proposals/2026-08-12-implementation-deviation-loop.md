---
status: proposed
files:
  - on-the-record/hooks/directive.sh
  - on-the-record/hooks/deviation-log-guard.sh
  - on-the-record/hooks/hooks.json
  - docs/handbooks/deviation-loop.md
  - docs/issue-803/reports/implementation/survey.md
  - docs/issue-803/proposals/2026-08-12-implementation-deviation-loop.md
---

## Request

Issue #803 step 2 (implementation): build the RECOGNIZE → CLASSIFY →
RESOLVE-AND-CONTINUE deviation loop that step 1 (product-discovery)
already fully designed and got approved (docs/issue-803/proposals/2026-08-11-self-driven-deviation-loop.md,
merged). Encode it as a fourth `directive.sh` paragraph, a new
Stop-hook guard enforcing the no-traceless-deviation invariant, and a
human-facing handbook — no new design decisions, a mechanical port of
an already-specified behavior.

## Constraints

- Reuse #699's primitives only (`spawn.py consult`, `spawn.py spawn`) —
  no new spawn/consult mechanism, per the design doc's own constraint,
  unchanged here.
- Default-on via plugin hooks/directives alone (req #7) — the new
  paragraph goes in `directive.sh`'s existing always-injected heredoc;
  no CI, no explicit skill invocation.
- The new paragraph must nest inside the existing #699 R3 goal loop
  paragraph, matching how the three existing additions already nest
  (survey: directive.sh lines 121-177) — not a fifth standalone loop.
- The new guard must follow the existing Stop-hook shape (fail-closed
  trap, `ORCHESTRATE_OFF` kill switch, `CLAUDE_ROLE`-unset gate) that
  `stop-gate.sh` already establishes (survey), so it composes with the
  five other Stop hooks already registered rather than introducing a
  second convention.
- The deviation-log path split (`docs/issue-<n>/reports/deviation-log.md`
  vs. `docs/reports/deviation-log.md`) must mirror `consult-log.md`'s
  existing split exactly (survey) — no new path convention.

## Rationale

**Chosen approach: port the design doc's spec verbatim into the three
named surfaces, adding one surface (`hooks.json` registration) the
design doc's own write set omitted.**

The design phase already resolved every judgment call this build would
otherwise face — RECOGNIZE's test for what counts as a deviation,
CLASSIFY's inline-vs-file mechanical test, and the two rejected
alternatives (always-file, always-inline-and-log-only, and a numeric
noise score) are all settled in
docs/issue-803/proposals/2026-08-11-self-driven-deviation-loop.md. Re-
litigating any of that here would be redundant work, not care — the
approved proposal is the spec to build against, not a starting point to
re-derive from.

**Rejected alternative — treat `hooks.json` registration as out of
scope, deferring it to a follow-up issue.** Rejected: a Stop hook that
exists on disk but is never listed in `hooks.json`'s `Stop` array never
fires — this would ship code with zero observable effect and leave
#803's own acceptance criterion (a plain session self-files/resolves a
seeded deviation, checked by the deviation log's presence) permanently
unmeetable, since the guard that makes "no traceless deviation" a
default-on invariant (design doc's own justification for the guard's
existence) would never run. Registering it in the same commit is the
only version of "ship the guard" that actually ships a working guard.

**Rejected alternative — skip the handbook, fold its content into
`directive.sh`'s injected paragraph instead.** Rejected: the design
doc's own `## Accumulation` section already flags `directive.sh` as an
accumulating per-prompt read cost (now a fourth standing paragraph) and
explicitly scopes the deviation-log format's full explanation to a
separate handbook rather than growing the injected paragraph further —
reversing that here would work directly against the design's own
documented cost-control choice.

## What will be done

- `on-the-record/hooks/directive.sh`: append a fourth paragraph inside
  the existing heredoc, after the `AUTONOMOUS ASYNC COMPLETION`
  paragraph, titled to match the existing house style (e.g. "YOUR
  DEVIATION LOOP (issue #803)"), stating RECOGNIZE (deviation vs. normal
  task friction), CLASSIFY (inline-fix vs. file-as-issue, the four-part
  mechanical test, consult when not obvious), and RESOLVE-AND-CONTINUE
  (deviation-log append shape for both the inline and filed cases,
  reusing the existing `spawn.py consult`/`spawn.py spawn`/
  `spawn.py watch` calls already documented above it in the same file) —
  explicitly framed as nesting inside "YOUR GOAL LOOP" rather than a
  fifth separate loop, per the design doc's own framing instruction.
- `on-the-record/hooks/deviation-log-guard.sh` (new file, Stop hook):
  reuses `stop-gate.sh`'s fail-closed trap, `ORCHESTRATE_OFF` kill
  switch, and `CLAUDE_ROLE`-unset orchestrator-only gate — but for the
  actual check, follows `product-capture-stopgate.sh`'s mechanism, not
  `stop-gate.sh`'s: `stop-gate.sh` only inspects `last_assistant_message`
  text and has no file/git access, which cannot maintain a
  "no-matching-deviation-log-append-this-turn" fact (warrant hunt
  finding, docs/issue-803/reports/implementation/2026-08-12-hunt-implementation-deviation-loop.md,
  dispatched after this proposal's first commit). The guard instead
  reads `transcript_path` off the raw Stop event JSON the way
  `product-capture-stopgate.sh` does (`e.get("transcript_path")`),
  scans it for a recognized-deviation marker, and separately checks —
  via `git diff` against the deviation-log path(s), the same
  `os.path.isfile` / `git diff` pattern `product-capture-stopgate.sh`
  already uses — whether a matching append actually landed. Refuses
  session-end via `hookSpecificOutput.additionalContext` (not a hard
  `decision:"block"`), matching `stop-gate.sh`'s own house-style
  rationale that a heuristic misfire on unusual phrasing should not
  discard the whole turn.
- `on-the-record/hooks/hooks.json`: register `deviation-log-guard.sh` as
  a 7th entry in the `Stop` array (survey: currently 6 entries, lines
  84-95), after the existing `stop-gate.sh` entry since both inspect
  `last_assistant_message` and should run adjacently.
- `docs/handbooks/deviation-loop.md` (new file): human-facing
  explanation of RECOGNIZE/CLASSIFY/RESOLVE, the deviation-log entry
  format (timestamp, `inline`/`filed`/`resolved`, description, and for
  `filed`/`resolved` the issue number/role/PR), and the explicit
  #787/#801 dependency statement carried forward from the design doc's
  own `## What will be done` section.
- This survey and this proposal (phase-1 output).

## Out of scope

- Re-deciding any part of the RECOGNIZE/CLASSIFY/RESOLVE design itself —
  that was step 1's job and is already approved.
- Re-running the #776 harness to measure whether the loop actually moves
  `problems_not_pushed_back` toward PASS — that is #803 step 3
  (execution-observation), gated on this step landing.
- Resolving the open #787 self-file-permission question the design doc
  itself left to #787 — carried forward unchanged, not answered here.
- #801's self-wake mechanism itself.

## How you'll know it worked

- The new `directive.sh` paragraph is present in the file, gated the
  same `CLAUDE_ROLE`-unset way as the three existing paragraphs, and
  explicitly states it nests inside "YOUR GOAL LOOP".
- `deviation-log-guard.sh` exists, is registered in `hooks.json`'s
  `Stop` array, and — run once by hand against a synthetic Stop payload
  (`transcript_path` pointing at a fixture transcript containing a
  deviation marker, working tree with no matching deviation-log append)
  — refuses (non-zero exit / `additionalContext` set), and against a
  fixture where the deviation-log append is present, passes clean
  (exit 0). This is the confirmation run no-mock's "build it, run it,
  once" calls for; it is not step 3's harness re-run.
- `docs/handbooks/deviation-loop.md` documents the entry format and the
  #787/#801 dependency explicitly.
- Step 3's own success check (unchanged from the design doc, not
  re-registered here): a #776 harness re-run showing
  `problems_not_pushed_back` moving from baseline FAIL toward PASS.
