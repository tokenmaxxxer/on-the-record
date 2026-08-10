---
code_under_review:
  - on-the-record/hooks/product-capture-stopgate.sh
  - on-the-record/hooks/test_product_capture_stopgate.py
  - on-the-record/hooks/hooks.json
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #566: Stop-time product-capture hook

## What was done

Built exactly what `docs/issue-566/proposals/implementation.md` froze, with no design decisions
reopened from `docs/issue-566/proposals/architecture.md` (merged PR #569):

- `on-the-record/hooks/product-capture-stopgate.sh` — new `Stop` hook. Reads `transcript_path`
  off the raw Stop event JSON, walks the transcript JSONL for `type=="user"` entries with
  plain-string (or text-block) content, sentence-splits on `.`/`!`/`?`/`\n`, and applies the four
  category anchor(+modal) regex pairs from architecture (requirements/priorities/philosophy/goals,
  EN+KO). For each category with >=1 flagged sentence: bootstraps `docs/product/<category>.md`
  (two-line header, create-only) if absent, then checks `git diff --unified=0` (uncommitted) union
  `git log -1 -p` (last commit) for that file for at least one added line. Categories with zero
  added lines produce a `hookSpecificOutput.additionalContext` advisory naming the category and a
  short excerpt; zero flagged categories -> silent (exit 0, no output). Same kill-switch
  (`CLAUDE_ROLE`, `ORCHESTRATE_OFF`) and fail-closed `trap` skeleton as
  `decision-queue-stopgate.sh`.
- `on-the-record/hooks/test_product_capture_stopgate.py` — `t_*` subprocess-invocation tests
  following `test_decision_queue_stopgate.py`'s pattern: no-flag silence, flagged category with no
  doc change -> advisory naming the category, bootstrap creates the missing file on first flag,
  flagged category with a matching committed doc diff -> silent, `CLAUDE_ROLE` set -> no-op,
  `ORCHESTRATE_OFF` set -> no-op, missing transcript path -> fails closed/silent, never crashes.
- `on-the-record/hooks/hooks.json` — appended the fifth `Stop` entry
  (`product-capture-stopgate.sh`) after `report-framing-check.sh`, exact command string
  architecture specified.
- `docs/issue-566/proposals/implementation.md` — added a `## Accumulation` field (required by
  `accumulation-claim-guard.sh` for this change shape: new inline-subprocess test helpers) stating
  the helpers stay local to this one test file, matching `test_decision_queue_stopgate.py`'s own
  local-helper convention; not shared because only two files today would use it.

## Why

`docs/issue-566/proposals/implementation.md` (phase-1, approved) is the upstream basis; it in turn
implements `docs/issue-566/proposals/architecture.md` (merged PR #569) verbatim. Issue #566 asks
for hook-enforced, deployed-plugin-surface capture of requirements/priorities/philosophy/goals
stated in conversation, structured (not raw transcript quotation) — this hook is that mechanism.

## Basis

- `docs/issue-566/proposals/implementation.md` (this phase's approved proposal)
- `docs/issue-566/proposals/architecture.md` (merged PR #569, frozen design)
- `docs/issue-566/reports/implementation/survey.md` (current-state survey)

## How you'll know it worked

- `python3 -m pytest on-the-record/hooks/test_product_capture_stopgate.py` — run once, actual
  output:
  ```
  on-the-record/hooks/test_product_capture_stopgate.py::t_no_flagged_sentence_is_silent PASSED
  on-the-record/hooks/test_product_capture_stopgate.py::t_flagged_requirement_with_no_doc_change_gets_additional_context PASSED
  on-the-record/hooks/test_product_capture_stopgate.py::t_bootstrap_creates_missing_file_on_first_flag PASSED
  on-the-record/hooks/test_product_capture_stopgate.py::t_flagged_requirement_with_matching_doc_diff_is_silent PASSED
  on-the-record/hooks/test_product_capture_stopgate.py::t_claude_role_set_is_noop PASSED
  on-the-record/hooks/test_product_capture_stopgate.py::t_orchestrate_off_is_noop PASSED
  on-the-record/hooks/test_product_capture_stopgate.py::t_missing_transcript_path_fails_closed_silently PASSED
  7 passed in 0.29s
  ```
- `hooks.json` parses as valid JSON via `python3 -c "import json; json.load(open('on-the-record/hooks/hooks.json'))"` —
  confirmed, one new `Stop` entry, four existing entries unchanged.
- Manual dry run covered by the test suite itself (the subprocess-invocation tests feed real Stop
  payloads against real temp git repos and transcripts, which is the same shape the proposal's
  manual-dry-run step describes) — a separate freestanding manual run was not additionally
  performed since the automated tests already exercise that exact path.

## Doc-placement ladder

- No new env var, config key, dependency, or migration introduced — nothing to add to a handbook.
- No library-or-format choice over a named alternative beyond what implementation.md's own
  `## Rationale` already recorded (python3 heredoc over bash-only parsing) — no new decisions-bucket
  entry needed.
- No benchmark/investigation numbers produced beyond this record itself.

## What did not work

None — the build matched the proposal on the first pass; the two test-fixture adjustments (using
"the project" instead of "this project" to match architecture's frozen anchor regex literally, and
committing the doc-diff fixture instead of leaving it untracked so `git diff`/`git log -1 -p`
actually observe it) were made while first authoring the test file, before any test run recorded a
failure against a stable version — not a case of something built, run, and found broken.

## Open findings

None.

## Next steps

Commit this record together with the three code/hooks-json files, then push and open the phase-2
PR against `main` with `Closes #566`.

## Resolution path

Not applicable — no open findings to resolve.

## closed_checks

- pytest suite, derived: the fenced `pytest -v` output under "How you'll know it worked" above —
  code_sha: e02988f
- hooks.json JSON-validity parse — code_sha: e02988f

## Hunt

Per the role directive's hunt cadence, a warrant-hunter dispatch was due before phase-2 completion.
Headless/single-shot contract v3 s22 takes priority here: this session cannot end the turn with a
dispatched-but-unconsumed background agent, and there is no further turn in this session to consume
one. No hunter was dispatched this phase; this is recorded as the reason, not silently omitted.
