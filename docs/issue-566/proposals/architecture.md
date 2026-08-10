---
status: proposed
files:
  - docs/issue-566/reports/architecture/survey.md
  - docs/issue-566/proposals/architecture.md
  - docs/issue-566/reports/architecture.md
---

# Proposal — issue #566 architecture: Stop-time capture hook design

Phase 1 only (role-handoff contract v3 s19). Designs the mechanism product-discovery's phase-1
proposal (`docs/issue-566/proposals/product-discovery.md`, merged PR #568) left open: hook name,
detection vocabulary, transcript-to-docs cross-check, `hooks.json` wiring, bootstrap behavior.
Deterministic script checks only — no LLM judgment, no GitHub Actions, matching the issue's own
constraint and this repo's existing hook style throughout `on-the-record/hooks/`.

## Hook name and file

`on-the-record/hooks/product-capture-stopgate.sh` — named to match the existing
`decision-queue-stopgate.sh` (a `Stop`-time gate over accumulated session state, not a single
last-message check) rather than `stop-gate.sh`'s narrower "gate the closing reply" shape, since
this hook inspects the whole session's user turns, not the final assistant message.

## Payload: full transcript, not `last_assistant_message`

Every existing `Stop` hook here reads `last_assistant_message`, which cannot see a requirement
stated three user turns before the final one. This hook instead reads `transcript_path` off the
raw Stop event JSON (the field Claude Code's Stop payload always carries) and walks the
transcript JSONL for `type == "user"` entries whose content is a plain string (skips tool-result
entries, which are also `type: "user"` in the transcript format but carry structured
`tool_result` content, not authored text). This is strictly additive to the existing
`*_PAYLOAD`-env convention, not a replacement of it — other Stop hooks are unaffected.

Same no-op/kill-switch shape as the rest of the `Stop` array: no-op when `CLAUDE_ROLE` is set
(this hook is for the target-repo orchestrating session, not a role session — role sessions write
their own records through a different mechanism), honors `ORCHESTRATE_OFF`, fails closed via the
same `trap`-based exit-code remap as `stop-gate.sh`/`report-framing-check.sh`.

## Detection vocabulary (regex, EN+KO), by category

Four independent pattern sets, one per target file, tuned narrow deliberately: the registered
guardrail is `false_flag_rate <= 20%` (product-discovery's H1), and a broad "any imperative
sentence" match would blow through that on ordinary conversational instructions ("read this
file", "run the tests") that are not project-level requirements. Each pattern requires a
project-scoping anchor word co-occurring with the shape word, not the shape word alone.

- **requirements.md** — an actionable, falsifiable ask about what the project/system must do.
  Anchor: (`이 프로젝트|이 시스템|the (project|system|app|service)|we (need|must|should build)`)
  co-occurring within the same sentence as a modal/imperative
  (`must|should|need(s)? to|해야|필요합니다|required|requirement`).
- **priorities.md** — ranking/ordering language between two or more project-level concerns.
  (`더 중요|우선순위|prioriti(z|s)e|more important than|comes first|먼저 처리|takes precedence`).
- **philosophy.md** — non-actionable stance/principle statements, marked by rationale connectives
  rather than an ask. (`철학은|원칙은|the (point|philosophy|principle) is|우리는 .*라고 믿|we
  believe|기본적으로.*지향`).
- **goals.md** — outcome/target statements distinct from a requirement (a goal names a desired
  end state, not a build ask). (`목표는|goal is|aim(ing)? (for|to)|achieve|달성하고자|success
  looks like`).

A statement matching more than one category's anchor is flagged under all matching categories —
category assignment ambiguity is a known limitation, not resolved here (see Open findings in the
delivery record). Matching is case-insensitive, sentence-scoped (split on `.`/`!`/`?`/`\n` before
matching, so an anchor word and a modal word ten sentences apart do not co-fire).

## Cross-check: flagged statements vs. `docs/product/*.md` diff

For each category with at least one flagged sentence, the hook runs (in the target repo's working
tree) `git diff --unified=0 -- docs/product/<category>.md` (uncommitted) union
`git log -1 --format= -p -- docs/product/<category>.md` when the session already committed — the
same "inspect the session's own changes" approach `contract-guard.sh`/`pr-preflight.sh` already
use — and checks whether the diff added at least one new entry. Zero flagged categories -> hook
no-ops entirely (nothing to cross-check, no output). One or more flagged categories with zero
corresponding new lines in that category's file -> `hookSpecificOutput.additionalContext` names
the category and a short excerpt of the unrecorded statement, in the same advisory (not
`"decision":"block"`) shape `stop-gate.sh` uses — a Stop-time nudge to record before ending the
turn, not a hard refusal that could strand an otherwise-fine session on an over-eager match.

## Bootstrap for target repos without `docs/product/`

On the first sentence flagged in any category, before computing the cross-check diff, the hook
checks whether `docs/product/<category>.md` exists for that category; if not, it creates
`docs/product/` and writes a two-line header (title + "append-only, newest entry last") into the
missing file(s) — mirroring `record-scaffold.sh`'s "create the skeleton, never overwrite" rule,
but automatic here (fired by the hook itself) rather than CLI-invoked, since product-discovery's
resolved open-question 3 requires the capture to be automatic, not a separate manual step an
operator could skip running. Creating the skeleton file with zero entries still counts as "no new
entry" for that turn's cross-check — bootstrap does not silently satisfy the requirement to
record; it only removes "the file doesn't exist yet" as a reason a hook-based writer could fail.

## `hooks.json` wiring

Appended as a fifth entry in the existing `Stop` array, after `report-framing-check.sh`:

```json
{ "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/product-capture-stopgate.sh" }
```

Placed last because it is the only `Stop` entry with a real filesystem side effect (bootstrap
writes); running after the three read-only checks avoids interleaving a write between them, though
none of the four depend on each other's output today.

## What this proposal does not decide

Detector recall against paraphrased/indirect requirement statements (product-discovery's named
failure signature) is not solved here — it is a `false_flag_rate`/`unrecorded_requirement_rate`
measurement question for whoever runs the pre-registered H1 window, not an architecture-time
design choice. Implementation may need to widen the vocabulary per product-discovery's own pivot
rule if the measured rate exceeds threshold; this proposal's vocabulary is the starting point, not
frozen forever.
