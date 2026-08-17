---
status: proposed
files:
  - on-the-record/hooks/product-capture-stopgate.sh
  - on-the-record/hooks/test_product_capture_stopgate.py
---

Skip condition: pure bugfix (scout-directive skip condition) — issue #1726 states `validity-consult-skip: trivial` and `design-research-skip: mechanical`, and the fix is fully specified by the issue's own Acceptance section plus the hook's existing cross-check logic (see docs/issue-1726/reports/implementation/survey.md). No design decision is open; scouting/full survey round skipped accordingly (survey.md still written, per survey-order-directive, to record the concrete write set).

## Request
`product-capture-stopgate.sh` bootstraps an empty `# <Category>\n\nAppend-only, newest entry last.\n` template file the moment a category regex matches any user sentence in the transcript (bootstrap-on-first-flag, #566), before the operator has recorded anything. The category vocabulary is broad enough that ordinary conversation trips it, leaving untracked junk files in the working tree that the operator then has to notice and delete. Stop the hook from ever creating the file; when it's missing, the advisory should just name the path the operator would create.

## Constraints
- The hook must never write the category doc file to disk, in any code path.
- When the file is missing, the advisory text must still name the path the operator would create (issue-scoped `docs/issue-<n>/reports/product/<cat>.md` or the off-branch fallback `docs/reports/product/<cat>.md`, per #684/#956/#1111).
- When the file already exists, behavior is unchanged: the existing git-diff/git-log cross-check against `rel` still decides whether the category is silent or flagged.
- Category vocabulary, issue-scoped vs. fallback path resolution, advisory-only output (never `decision:"block"`), and the kill switches (`ORCHESTRATE_OFF`, `CLAUDE_ROLE`) stay untouched.

## Rationale
Two ways to remove the bootstrap side effect were considered:
1. **Chosen**: delete the `if not os.path.isfile(doc_path): os.makedirs(...); open(...).write(...)` block outright. The survey confirmed the bootstrapped file's content was never actually read by the cross-check that follows it (a freshly-created file produces no `git diff`/`git log` output), so removing the write changes nothing about which categories end up in `unrecorded` — it only removes the disk side effect. Minimal diff, no behavior change to the cross-check path.
2. **Rejected**: keep creating the file but write it into a scratch/temp location instead of the real doc path, so the operator never sees it in `git status`. Rejected because it still performs an unnecessary filesystem write on every flagged-and-missing category (wasted I/O, another path to keep in sync with the real one) for zero benefit — the acceptance criterion is "the hook never creates a file," not "creates it somewhere less visible."

## What will be done
- `on-the-record/hooks/product-capture-stopgate.sh`: remove the `if not os.path.isfile(doc_path): ...` bootstrap block and the now-unused `doc_path` variable from the per-category loop; add a short comment noting the #1726 removal for the same reason the file's other issue-numbered comment blocks document each behavior change (#684, #956, #1118).
- `on-the-record/hooks/test_product_capture_stopgate.py`: rewrite `t_bootstrap_creates_missing_file_on_first_flag` to assert the doc file stays absent after a flagged run while the advisory's `additionalContext` still names the category path; rewrite `t_off_issue_branch_falls_back_to_repo_root_doc_path`'s trailing assertions the same way (drop `assert doc.exists()` / `"Requirements" in doc.read_text()`, assert `not doc.exists()` instead). No other test in the file touches file-creation, so no other test changes.

## Accumulation
This is a one-off deletion (one `if` block removed from one loop body in one hook file) — not a repeated per-entry pattern like `roles/*.json`. The hook has exactly one call site that ever wrote a category doc file; there is no second copy of this bootstrap logic anywhere else in the repo to keep in sync, and removing it introduces no new per-category or per-file accumulation (the existing per-category `git diff`/`git log` subprocess calls a few lines below are untouched and already shared across all four categories via the same loop).

## Out of scope
- Any change to the category vocabulary, issue-scoped path derivation, or the git-diff/git-log cross-check logic itself.
- Any change to the dedup/state-file logic (#1118 Fix 3) or the kill switches.

## How you'll know it worked
`python3 on-the-record/hooks/test_product_capture_stopgate.py` passes, including the two rewritten tests, and a manual read of the diff shows the bootstrap write is gone with no other logic touched.
