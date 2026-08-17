---
code_under_review:
  - on-the-record/hooks/product-capture-stopgate.sh
  - on-the-record/hooks/test_product_capture_stopgate.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# issue-1726 implementation record

## What was done

canonical: on-the-record/hooks/product-capture-stopgate.sh (direct read this session)

Removed the bootstrap-on-first-flag block from
`on-the-record/hooks/product-capture-stopgate.sh`: the
`if not os.path.isfile(doc_path): os.makedirs(...); open(...).write(...)`
block that created an empty `# <Category>\n\nAppend-only, newest entry
last.\n` template file the moment a category regex flagged any user
sentence, plus the now-unused `doc_path` variable. Added a short
issue-numbered comment (matching the file's existing convention of
documenting each behavior change inline) explaining why the write was
removed: the cross-check that follows only reads `git diff`/`git log`
output for `rel`, which a freshly-created untracked file never
produces, so the write was provably inert to the cross-check's outcome.
The advisory path derivation (`rel` = issue-scoped or fallback
`docs/.../product/<cat>.md`) is untouched, so a missing file's advisory
still names the path the operator would create.

canonical: on-the-record/hooks/test_product_capture_stopgate.py (direct read this session)

Rewrote `t_bootstrap_creates_missing_file_on_first_flag` (renamed to
`t_missing_doc_file_stays_absent_on_flag`) to assert the doc file stays
absent after a flagged run while the advisory's `additionalContext`
still names the category path, and dropped the
`assert doc.exists() / "Requirements" in doc.read_text()` tail of
`t_off_issue_branch_falls_back_to_repo_root_doc_path` in favor of
`assert not doc.exists()`. No other test in the file touched
file-creation.

## Why

canonical: docs/issue-1726/proposals/2026-08-17-stop-bootstrapping-product-capture-doc-files.md

Issue #1726: the hook's category vocabulary is broad enough that
ordinary conversation trips it, so the bootstrap write left untracked
junk template files in the working tree that the operator then had to
notice and delete, with zero effect on the hook's actual advisory
decision.

## Upstream / basis

basis: docs/issue-1726/reports/implementation/survey.md, docs/issue-1726/proposals/2026-08-17-stop-bootstrapping-product-capture-doc-files.md

## Test evidence

canonical: acceptance: `python3 -m pytest on-the-record/hooks/test_product_capture_stopgate.py -v -o addopts=""` — result: pass, this session's own run

```
on-the-record/hooks/test_product_capture_stopgate.py::t_no_flagged_sentence_is_silent PASSED
on-the-record/hooks/test_product_capture_stopgate.py::t_flagged_requirement_with_no_doc_change_gets_additional_context PASSED
on-the-record/hooks/test_product_capture_stopgate.py::t_missing_doc_file_stays_absent_on_flag PASSED
on-the-record/hooks/test_product_capture_stopgate.py::t_flagged_requirement_with_matching_doc_diff_is_silent PASSED
on-the-record/hooks/test_product_capture_stopgate.py::t_claude_role_set_is_noop PASSED
on-the-record/hooks/test_product_capture_stopgate.py::t_orchestrate_off_is_noop PASSED
on-the-record/hooks/test_product_capture_stopgate.py::t_off_issue_branch_falls_back_to_repo_root_doc_path PASSED
on-the-record/hooks/test_product_capture_stopgate.py::t_off_issue_branch_empty_state_is_silent PASSED
on-the-record/hooks/test_product_capture_stopgate.py::t_missing_transcript_path_fails_closed_silently PASSED
9 passed in 1.82s
```

## Test-tier note (issue #1518)

canonical: `cat .on-the-record/test-tiers.json` — result: file present, declares `on-the-record/hooks/*.sh` and `on-the-record/hooks/test_*.py` as `slow`-tier trigger classes, this session's own read

This session's diff matches the `slow` tier's `trigger_change_classes`,
so the fast-tier run above is not the whole tiering contract.

canonical: acceptance: `python3 -m pytest -q -m slow -o addopts=""` (run in background this session, then killed after 19 wall-clock minutes) — result: 61 passing dots emitted, 0 failures observed, run incomplete when killed

That repo-wide slow-tier run was killed before finishing to stay inside
this headless single-shot turn's time budget (contract v3 s22 forbids
ending the turn with unconsumed background work); no failure was
observed in the portion that ran, but the full run did not reach
completion this session — recorded here as a tiering-gap note, not a
completion claim, per the test-tier directive.

## What did not work

None — no attempt was undone or replaced during this session.

## Rationale for deviations

None. This phase-2 session applied exactly the change set the approved
phase-1 proposal specified, with no scope-exceeded stop and no
proposal-stated alternative swapped mid-build. The Open findings section
below cites an item the phase-1 hunt filed in a prior session, before
this build started, not a divergence from within it.

## Document placement

- [x] No env var, config key, new dependency, or migration was
  introduced — no handbook update required.
- [x] The library/format decision (delete the bootstrap block outright
  vs. redirect it to a scratch path) was already recorded in
  docs/issue-1726/proposals/2026-08-17-stop-bootstrapping-product-capture-doc-files.md's
  `## Rationale` — no separate decisions/ entry needed since no public
  signature or wire format outside this issue's own hook script changed.
- [x] No benchmark/investigation numbers were produced — no reports/
  entry beyond this record and the existing survey.

## Open findings

canonical: docs/issue-1726/reports/implementation/2026-08-17-hunt-stop-bootstrapping-product-capture-doc-files.md lines 9, 49-98 (read this session)
The phase-1 warrant hunt found `gates/test_product_capture_vs_deliverable_guard.py` lines 135-159 (function `t_empty_state_bootstrap_still_works`) is an `xfail(strict=False)` guard whose reason still frames the removed bootstrap behavior as pending bug #1619, not a closed, intentional deletion.

canonical: docs/reports/deviation-log.md, entry timestamped 2026-08-17T00:00:00Z (read this session)
That guard file sits outside this issue's frozen write set
(`on-the-record/hooks/product-capture-stopgate.sh`,
`on-the-record/hooks/test_product_capture_stopgate.py`), so it was
reported rather than fixed here — already filed to the log cited above
during the phase-1 hunt dispatch, before this phase-2 session began.

## Warrant hunt

The warrant-hunter already ran at end of phase 1 (dispatched before this
phase-2 session), producing the hunt record cited under Open findings
above.

canonical: on-the-record/hooks/product-capture-stopgate.sh, on-the-record/hooks/test_product_capture_stopgate.py (both diffed against the pre-phase-2 working tree this session)

No line outside the approved proposal's write set changed between the
hunt's reviewed diff and this phase-2 commit, so re-hunting the same
diff was not run again this session.

closed_checks:
- check: hook never creates the category doc file when missing; advisory still names the path
  code_sha: (see code_under_review above)
  canonical: acceptance: `python3 -m pytest on-the-record/hooks/test_product_capture_stopgate.py -k t_missing_doc_file_stays_absent_on_flag -v -o addopts=""` — result: pass, this session's own run (part of the full 9-pass run pasted above)
- check: off-issue-branch fallback path also never creates the file
  code_sha: (see code_under_review above)
  canonical: acceptance: `python3 -m pytest on-the-record/hooks/test_product_capture_stopgate.py -k t_off_issue_branch_falls_back_to_repo_root_doc_path -v -o addopts=""` — result: pass, this session's own run (part of the full 9-pass run pasted above)
- check: existing-file cross-check path is unchanged (git-diff/git-log still governs silent-vs-flagged)
  code_sha: (see code_under_review above)
  canonical: acceptance: `python3 -m pytest on-the-record/hooks/test_product_capture_stopgate.py -k t_flagged_requirement_with_matching_doc_diff_is_silent -v -o addopts=""` — result: pass, this session's own run (part of the full 9-pass run pasted above)
