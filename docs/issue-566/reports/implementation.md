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

None.

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

## Addendum (2026-08-12, re-delivery session)

This session was invoked to extend #566's Stop-hook to a "target-project" scope — reusing the
requirement-digest machinery from #930/#943, plus a harness fixture proving a fresh target repo
captures a stated requirement with no explicit skill call.

canonical: `gh issue view 566` body, read live in this session — that scope does not appear
anywhere in the issue body. The body only specifies the on-the-record repo's own Stop-time capture
hook.

canonical: `docs/issue-566/reports/implementation.md` frontmatter above (`loop_state: landed`) and
`git log --oneline --all | grep 566` (PR #575 shown as `Merge pull request #575`), both read live
in this session — that hook is already delivered and merged.

canonical: `gh issue view 566 --comments`, read live in this session — the reopening comment states
explicitly that only step 4 (execution-observation ‖ conformance-review) remains, which is not a
step the implementation role owns and not a target-project extension. The same comment thread also
carries a prior "Anomaly report (implementation role, 2026-08-12)" comment reaching this identical
conclusion, followed by a "stranded-relay: pr-create-failed" comment (`No commits between main and
issue-566/implementation`) — that prior session's finding was posted only as an issue comment and
never committed to the branch, so it was not a durable repo record and the redelivery task fired
again.

canonical: `find docs/issue-566 -type f` and `git status`, run live in this session — no
target-project proposal file exists under `docs/issue-566/proposals/`, and no uncommitted work from
the prior session was found in this workspace to recover.

No proposal for a target-project extension exists, and none is approved. Per the warrant-directive,
building it now would be unauthorized scope. Not starting that work in this session. If the
target-project extension is wanted, it needs its own issue (or an explicit amendment to #566's
body/plan) so a phase-1 proposal can go through the approval gate normally.

canonical: this record's own frontmatter above (`loop_state: landed`) and PR #575 (merged, per
`git log --oneline --all | grep 566` cited earlier in this addendum) — unchanged by this session.

loop_state remains `landed`: this addendum documents a refusal of adjacent unauthorized scope, not
a reopening of the landed unit.
