---
status: proposed
files:
  - docs/issue-566/reports/implementation/survey.md
  - docs/issue-566/proposals/implementation.md
  - on-the-record/hooks/product-capture-stopgate.sh
  - on-the-record/hooks/test_product_capture_stopgate.py
  - on-the-record/hooks/hooks.json
  - docs/issue-566/reports/implementation.md
---

# Proposal — issue #566 implementation: build the Stop-time product-capture hook

Phase 1 only (role-handoff contract v3 s19). Builds exactly what
`docs/issue-566/proposals/architecture.md` (merged PR #569) already designed — hook name,
detection vocabulary, cross-check, bootstrap, wiring — with no design decisions reopened. Scouting
skipped per the survey's skip-condition record: architecture leaves no open design surface for
this proposal to research (see `docs/issue-566/reports/implementation/survey.md`).

## Request

Operator asked (issue #566) for a hook-enforced, deployed-plugin-surface mechanism that records
requirements/priorities/philosophy/goals stated in conversation into target-repo docs, structured
rather than raw-transcript. product-discovery and architecture already resolved intent and design;
this step is the code that ships it.

## Constraints

- No design decisions reopened: hook name, vocabulary, cross-check mechanism, bootstrap behavior,
  and `hooks.json` placement all come from the merged architecture proposal verbatim.
- Deterministic script only (bash + python3 heredoc), no LLM judgment, no GitHub Actions — matches
  the issue's own constraint and every existing `Stop` hook in this directory.
- Same kill-switch/fail-closed skeleton as `decision-queue-stopgate.sh`/`stop-gate.sh`: no-op on
  `CLAUDE_ROLE` set, honor `ORCHESTRATE_OFF`, `trap`-based exit-code remap to 2 on unexpected
  failure.
- Advisory only: `hookSpecificOutput.additionalContext`, never `decision: block` — architecture's
  cross-check section states this explicitly to avoid stranding a session on an over-eager match.

## Rationale

Considered writing the transcript-walk and cross-check logic as an inline bash-only implementation
(grep/sed over the JSONL and diff output) instead of a Python heredoc, to avoid the python3
dependency check. Rejected: every existing `Stop` hook with non-trivial logic here
(`decision-queue-stopgate.sh`, `stop-gate.sh`) already requires python3 and gates on
`command -v python3` before proceeding, so bash-only would be an inconsistent one-off that adds
JSONL-parsing fragility (multi-line assistant messages, embedded quotes) that `json.loads` handles
for free — the dependency is already paid by the rest of the surface, so avoiding it here buys
nothing and costs correctness.

## What will be done

- Write `product-capture-stopgate.sh`: reads the Stop payload for `transcript_path`, walks the
  JSONL for `type == "user"` entries with plain-string content (skipping tool-result entries),
  sentence-splits each on `.`/`!`/`?`/`\n`, and applies the four anchor+modal regex pairs from
  architecture's vocabulary section per category. For each category with >=1 flagged sentence,
  bootstraps `docs/product/<category>.md` if absent (two-line header, create-only), then computes
  the uncommitted-plus-last-commit diff for that file and flags it in `additionalContext` if the
  diff adds no new line. Kill-switches and fail-closed trap match `decision-queue-stopgate.sh`'s
  skeleton exactly. Silent (exit 0, no output) when zero categories are flagged.
- Write `test_product_capture_stopgate.py`: `t_*` subprocess-invocation tests following
  `test_decision_queue_stopgate.py`'s pattern, covering: no-flag silence, single-category flag with
  no doc change -> advisory output naming the category, single-category flag with a matching doc
  diff -> silent, bootstrap creates the missing file on first flag, `CLAUDE_ROLE` set -> no-op,
  `ORCHESTRATE_OFF` set -> no-op, malformed/missing transcript path -> fails closed (exit 2) but
  never crashes the Stop turn silently-wrong.
- Append the fifth `Stop` entry to `hooks.json` after `report-framing-check.sh`, exact command
  string architecture specified.
- Run the new test file once against the built hook before this record is written, per the
  no-mock directive's single confirmation-run requirement; fix whatever the run surfaces.

## Accumulation

The test file's `_run`/`_git`/`_init_repo`/`_write_transcript` helpers are new but stay local to
`test_product_capture_stopgate.py`, mirroring `test_decision_queue_stopgate.py`'s own local
`_fake_checkout`/`_run` helpers rather than a shared cross-file helper module — the existing hooks
directory has no shared test-helper module today, and this proposal does not introduce one. If a
third stopgate test file needing both a temp git repo and a temp transcript fixture appears later,
extracting a shared helper becomes worth it then; two occurrences (this file and
`test_decision_queue_stopgate.py`'s narrower git-repo-only fixture) do not yet justify it.

## Out of scope

- Widening detector recall/vocabulary beyond architecture's starting set — that is the
  product-discovery H1 measurement window's job, not this build.
- Any change to `docs/product/*.md` content beyond the two-line bootstrap header.
- Any change to `gates/`-side mechanical gates or other `Stop` hooks.
- Category-assignment ambiguity (a statement matching >1 category) — architecture already named
  this a known limitation, not resolved here.

## How you'll know it worked

- `python3 -m pytest on-the-record/hooks/test_product_capture_stopgate.py` passes, run once and
  its actual output reported (no-mock directive).
- `hooks.json` remains valid JSON with exactly one new `Stop` entry, verified by parsing it.
- Manual dry run: feed a Stop payload whose transcript contains one KO priorities-shaped user
  turn and confirm `additionalContext` names `priorities.md`; feed the same transcript again after
  committing a matching `docs/product/priorities.md` addition and confirm silence.
