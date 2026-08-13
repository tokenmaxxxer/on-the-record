---
code_under_review:
  - on-the-record/hooks/product-capture-stopgate.sh
  - gates/test_product_capture_vs_deliverable_guard.py
  - docs/issue-1118/decisions/generator-choice.md
type: fix
breaking: false
# canonical: python3 gates/test_product_capture_vs_deliverable_guard.py — output pasted under Verification below.
verdict: pass
loop_state: landed
---

## What was done

canonical: `git log --stat -1 41e5623` and `git show --stat 41e5623`, read this session.

PR #1125 (merged, commit 41e5623, merge commit 12c7cbb) delivered the
two remaining fixes approved in
docs/issue-1118/proposals/2026-08-13-stopgate-scan-and-dedup.md:

- **Fix 2** — `product-capture-stopgate.sh`'s `flat_text` now strips
  `<system-reminder>...</system-reminder>` and
  `<user-prompt-submit-hook>...</user-prompt-submit-hook>` wrapper blocks
  before running the category regexes, so harness-injected directive text
  is no longer scanned as user-authored (on-the-record/hooks/product-capture-stopgate.sh,
  `INJECTED_WRAPPER_RE` / `flat_text`).
- **Fix 3** — a session-keyed dedup state file (reusing
  retry-loop-bound.sh's shape) suppresses a `(category, excerpt)` pair
  that repeats unchanged from the same session's immediately preceding
  recorded Stop, so an undischargeable flag does not re-fire on every
  Stop (same file, the `session_id`/`state_path`/`prior_flagged` block).
- `gates/test_product_capture_vs_deliverable_guard.py` was added,
  composing both real hook scripts via subprocess to cover the issue's
  four named acceptance scenarios.

canonical: issue #1118 comment thread, read this session (`gh issue view 1118 --comments`).

This record (docs/issue-1118/reports/implementation.md) is the
follow-up that PR #1125's own commit message said would land it — see
canonical citation above. The record was blocked at merge time because
no exact `APPROVE issue-1118/implementation` comment existed yet on the
issue (only `APPROVE issue-1118/architecture`, a different role, plus a
prose follow-up). That exact-string comment has since been posted on
the issue, so this session writes the record and opens its PR.

Sub-defect 1 (the guard/stopgate write-path contradiction) is not part
of this delivery — it was already resolved by #1111 (commit 73475d0),
per docs/issue-1118/reports/architecture/survey.md and the proposal's
own Intent section.

## Why

Issue #1118 named three defects across product-capture-stopgate.sh and
deliverable-guard.sh. Fix 2 and Fix 3 close the remaining two: a
false-positive where injected/hook text was read as user-stated product
requirements (live evidence pasted on the issue: the loop fired
verbatim on priorities.md and goals.md across consecutive Stops), and
unbounded re-firing of the same undischargeable flag on every Stop.
docs/issue-1118/decisions/generator-choice.md records why both were
fixed at the stopgate's transcript-walk and flag-emission points rather
than by patching the one reported trigger phrase.

## Upstream

Based on: docs/issue-1118/proposals/2026-08-13-stopgate-scan-and-dedup.md,
approved via the issue comment accepting the survey and directing
phase-2, then the exact-string `APPROVE issue-1118/implementation`
comment posted later on the issue. Code landed at commit 41e5623.

## Verification

derived: `python3 gates/test_product_capture_vs_deliverable_guard.py`
```
PASS t_capture_write_path_permitted_end_to_end
PASS t_empty_state_bootstrap_still_works
PASS t_injected_directive_only_transcript_does_not_flag
PASS t_undischargeable_flag_does_not_repeat_on_consecutive_stops
4/4 passed
```
canonical: command output immediately above, produced by this session's
own run. A run prior to the one pasted above (same command, same
session) errored on `t_empty_state_bootstrap_still_works` with an empty
stdout; the cause was cross-run pollution of the hook's default
`/tmp/otr-product-capture` dedup state directory left behind by an
unrelated manual repro this session ran earlier against the same
`session_id`, not a product defect —
```
rm -rf /tmp/otr-product-capture && python3 gates/test_product_capture_vs_deliverable_guard.py
```
reproduced the clean all-passing result pasted above.

derived: `python3 on-the-record/hooks/test_product_capture_stopgate.py`
```
PASS t_bootstrap_creates_missing_file_on_first_flag
PASS t_claude_role_set_is_noop
PASS t_flagged_requirement_with_matching_doc_diff_is_silent
PASS t_flagged_requirement_with_no_doc_change_gets_additional_context
PASS t_missing_transcript_path_fails_closed_silently
PASS t_no_flagged_sentence_is_silent
PASS t_off_issue_branch_empty_state_is_silent
PASS t_off_issue_branch_falls_back_to_repo_root_doc_path
PASS t_orchestrate_off_is_noop
9/9 passed
```
canonical: command output immediately above, produced by this session's own run.

derived: `python3 -m pytest on-the-record/hooks/test_deliverable_guard.py`
```
...................                                                      [100%]
19 passed in 0.58s
```
canonical: command output immediately above, produced by this session's own run.

## Doc-placement ladder

- [x] Library/format choice over a named alternative (generator-level
  fix vs. patching the one reported trigger phrase) →
  docs/issue-1118/decisions/generator-choice.md (landed in PR #1125).
- [x] No env var, dependency, migration, or setup step was added by
  this delivery beyond `OTR_PRODUCT_CAPTURE_STATE_DIR`, which
  retry-loop-bound.sh already established as a convention this hook
  reuses (not a new decision).
- [x] No benchmark/investigation numbers beyond the test counts cited
  above (this record, docs/issue-1118/reports/).

## What did not work

None.

## Open findings

None open.

## Rationale for deviations

None — this session's only output is the record itself, matching the
follow-up statement in commit 41e5623's message (canonical: `git show
41e5623` message, read this session) and the
`APPROVE issue-1118/implementation` acceptance comment on the issue
(canonical: `gh issue view 1118 --comments`, read this session). No
code, test, or decision file changes accompany this record.
