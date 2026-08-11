---
subject: issue-858
kind: survey
---

# Current-state survey — issue #858

## Scout skip record

Skip condition applied: "the spec literally leaves no design decision
open." The issue body is fully prescriptive — exact PreToolUse Write/Edit
scope (docs/**), exact credential patterns (gho_, ghp_, ghs_, ghr_,
github_pat_ + "similar high-signal secret shapes"), exact allow-list
([REDACTED] marker, truncated prefix under ~12 chars), exact
existing-file scrub target, and exact test cases (full token denied,
redacted/short-prefix allowed, ordinary prose untouched). No product
category to benchmark against — this is an internal write-time guard, not
a user-facing surface. Scout sweep skipped for this reason.

## Existing hook shape to follow

`on-the-record/hooks/record-claim-guard.sh` is the closest sibling: a
PreToolUse Write/Edit/MultiEdit bash wrapper that pipes a JSON payload
(tool_name, tool_input, cwd) into an inline python3 heredoc, scoped by a
path regex, checking content / new_string / edits[].new_string
fragments, wrapped in an EXIT trap remapping any unexpected exit code to
2 as its deny-by-default posture, with an ORCHESTRATE_OFF kill switch.
Its checks live in `gates/record_lint.py` as functions shared with
`gates/ci.py`'s full-PR-diff scan. Issue #858 asks only for the
write-time PreToolUse gate, no CI-diff-scan counterpart, so keeping the
pattern match inline in the new hook script (the way
`gate-registration-guard.sh` keeps its own classification check inline)
is proportionate — a shared module would serve a second caller that this
issue does not create.

Registration point: `on-the-record/hooks/hooks.json`, PreToolUse block,
matcher `Write|Edit|MultiEdit` (same group as `record-claim-guard.sh` and
`role-spec-reference-guard.sh`).

Test convention: `on-the-record/hooks/test_<name>.py`, pytest with
`python_functions = test_* t_*` (derived: `pytest.ini`), subprocess-invokes
the real bash script with a JSON payload piped to stdin, asserts
returncode and stderr — modeled on
`on-the-record/hooks/test_record_claim_guard.py`.

## Scope: docs/** vs docs/issue-*/reports/**

record-claim-guard.sh scopes to a role's own record tree (docs, an
issue segment, then reports) only. Issue #858 asks for the wider
docs/**. Building to the issue's stated scope, not narrowed to match
the sibling hook.

## Near-miss file to scrub

canonical: read docs/issue-776/reports/execution-observation/run2.md
directly, this session — line 39 carries `gho_A5ji...`, an already-
truncated, ellipsis-suffixed 8-char prefix (under the ~12-char
allowance) — technically inside the acceptance criterion's allowed
shape already, but the issue explicitly asks to scrub it further.
Write set includes this file; the exact scrub text is a build-time
call, not a design decision needing proposal-stage alternatives.

## Alternative considered: reuse gates/record_lint.py

Rejected: record_lint.py's checks are shared between the write-time
hook and the CI diff-scanner because both apply the same claim-shape
rules to two different inputs (one write's fragment vs. a full PR diff).
Issue #858 has no CI-diff-scan counterpart in its requirement, so adding
a shared module now would be speculative reuse for a caller that does
not exist yet. Kept the pattern match inline in the new hook script.
