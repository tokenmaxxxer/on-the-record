---
code_under_review:
  - on-the-record/hooks/credential_example_allowlist.py
  - on-the-record/hooks/credential-record-guard.sh
  - on-the-record/hooks/credential-network-guard.sh
  - on-the-record/hooks/test_credential_record_guard.py
  - on-the-record/hooks/test_credential_network_guard.py
type: feature
breaking: false
# canonical: python3 -m pytest on-the-record/hooks/ -k credential — result: 32 passed, 375 deselected
verdict: pass
loop_state: landed
---

## What was done
Implemented the approved phase-1 proposal (docs/issue-1033/proposals/credential-example-allowlist.md) on current main: added `on-the-record/hooks/credential_example_allowlist.py`, a shared module exposing `EXAMPLE_ALLOWLIST` (a `frozenset[str]`) containing two vendor-sourced canonical documentation example credentials — AWS's `AKIAIOSFODNN7EXAMPLE` IAM example access key and GitHub's `ghp_16C7e42F292c6912E7710c838347Ae178B4a` example classic PAT.

Both `credential-record-guard.sh` and `credential-network-guard.sh` now: set an env var (`CRG_HOOKS_DIR` / `CNG_HOOKS_DIR`) to the guard's own script directory before invoking the python heredoc; the heredoc inserts that directory onto `sys.path` and imports `EXAMPLE_ALLOWLIST` from the shared module; `find_credentials()` in each guard skips a match whose exact matched text (`m.group(0)`) is a member of `EXAMPLE_ALLOWLIST`, before it is counted as a hit. No shape regex was touched.

Added acceptance tests `t_canonical_aws_example_key_is_allowed`, `t_canonical_github_example_pat_is_allowed`, `t_novel_akia_shaped_string_still_denied` in `test_credential_record_guard.py`, and their network-guard analogues in `test_credential_network_guard.py`.

canonical: `python3 -m pytest on-the-record/hooks/ -k credential`, executed this turn against the working tree (full output pasted in the Acceptance verification section below).
All 32 selected tests, including the six new ones, passed this run.

## Why
Requirement R001 (the credential guard is the standing security invariant and must not be weakened) is preserved: the allowlist is an exact-string exception list, never folded into the shape patterns, so a real-shaped novel credential still blocks. This removes the false-positive friction the issue reports — a documentation-teaching example tripping the same guard as a real leaked secret — without loosening detection of anything shape-matching but not vendor-sourced.

## Upstream
canonical: docs/issue-1033/proposals/credential-example-allowlist.md, read this session on the current branch (merged to main as commit d085557 via PR #1036).
Based on: docs/issue-1033/proposals/credential-example-allowlist.md.

## Acceptance verification
checked: `python3 -m pytest on-the-record/hooks/ -k credential` — result:
canonical: `python3 -m pytest on-the-record/hooks/ -k credential`, execution transcript pasted below, run this turn.
```
32 passed, 375 deselected in 1.43s
```

## What did not work
None.

## Open findings
None.
