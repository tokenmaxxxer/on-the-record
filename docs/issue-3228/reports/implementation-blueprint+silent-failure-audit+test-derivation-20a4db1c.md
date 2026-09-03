---
issue: 3228
role: implementation-blueprint+silent-failure-audit+test-derivation-20a4db1c
author: implementation-blueprint+silent-failure-audit+test-derivation-20a4db1c
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
type: fix
breaking: false
code_under_review: same-commit
verdict: addressed
upstream:
  - path: PR #3237 (independent verification of PR #3233; branch not present in this working tree)
    sha: same-commit
  - path: PR #3233 (issue #3228 round 1, silent-failure AST lint)
    sha: 867f2a4361b5bd28b6ab35f5cf350b9ff097f9c9
---

# issue-3228 — implementation-blueprint+silent-failure-audit+test-derivation-20a4db1c record

## What was done

Round 2 on PR #3233's branch (`issue-3228/silent-failure-audit+implementation-blueprint+test-derivation-ed55a103`), addressing all four findings from PR #3237's independent verification, in the priority order the spawning task specified: wiring, then the two reliability defects, then the fixture correction, catch rate unchanged.

canonical: PR #3237 body (`gh pr view 3237`), read at the start of this session — "central finding: nothing this PR wires into the repo's automated checks ever runs `scripts/lint/silent_failure.py` against a new or changed source file"; "a null byte crashes the scan uncaught"; "a permission-denied directory is silently indistinguishable from a genuinely empty one"; "one of the five reconstructed 'before' fixtures (site 7, amendment_channel.py) implements a different, already-fixed bug".

**1. Wiring.** Two tiers, deliberately unequal in enforcement strength and labeled as such:

- `on-the-record/hooks/silent-failure-lint-guard.sh` (new): a `PreToolUse` `Write|Edit|MultiEdit` gate registered in `on-the-record/hooks/pretooluse_dispatcher.py`'s `GATES` list. Genuinely **blocks** — denies (exit 2) a write that adds a new `subprocess.run`/`Popen`/`check_output`/`check_call` call site with no `timeout=` keyword (SF001 only). Scoped to `.py` writes, matches only the dotted `subprocess.<attr>(...)` call shape, honors the `# silent-failure: allow <reason>` escape hatch, and falls back through raw/dedented/synthetic-function-wrapped parse attempts for a fragment with no enclosing `def` of its own.
- `gates.silent_failure_new_findings` (new, `gates/gates.py`), wired into `gates/ci.py`'s `check()` right after the pre-existing `gates.subprocess_call_shape_divergence` call. Diff-scoped (via `git diff -U0`'s own hunk headers) to lines a PR's diff actually added — covers all three rules (SF001/SF002/SF003) with full post-edit file context. This tier is **advisory only, not a block**.

acceptance: `OTR_DISPATCH_ONLY=silent-failure-lint-guard.sh python3 on-the-record/hooks/pretooluse_dispatcher.py` against 7 crafted payloads — result:
```
with timeout= => rc=0 (allow)
allow-marker escape => rc=0 (allow)
non-.py file => rc=0 (allow)
Edit fragment indented, no timeout => rc=2 (deny)
unrelated function literally named run() => rc=0 (allow)
no subprocess token at all => rc=0 (allow)
MultiEdit with one bad edit => rc=2 (deny)
```

acceptance: `python3 -m pytest on-the-record/hooks/test_silent_failure_lint_guard.py -q -o addopts=""` — result:
```
10 passed
```

acceptance: `python3 -m pytest gates/test_silent_failure_new_findings.py -q -o addopts=""` — result:
```
5 passed
```
Verifies the load-bearing diff-scoping property directly: a finding on a line the diff did not add is never reported; a finding on a newly-added line is.

SF002/SF003 are deliberately not blocked by the `PreToolUse` gate: both need whole-function context a write-time fragment does not carry, and checking them from a fragment alone risks false-denying a legitimate author whose returncode check or distinguishing return sits outside the edited lines.

canonical: `gates/gates.py`'s `ci_reachable_gates` function body (read this session, lines ~1066-1094) — its own docstring states the real merge-blocking `--closes-only` entry point never calls anything registered after the `closes_only` guard in `check()`; `gates.subprocess_call_shape_divergence` and the new `gates.silent_failure_new_findings` both sit in that unreached position, so both are advisory (surfaced via `board.py`'s post-session `gate_report()`), not merge-blocking. Stated here so this tier is never mistaken for a block.

Diff/fragment scoping (never repo-wide) is load-bearing in both tiers.
canonical: PR #3237 body (`gh pr view 3237`) — "Ran the lint over the whole repo: 594 findings, 535 distinct call sites flagged of 617 total (86.7%)". An unscoped check in either position would flag or block nearly all of that 86.7%, not just a newly-written site.

Both new hook-surface files were registered in this repo's own live specs.
acceptance: `git commit` of `on-the-record/hooks/silent-failure-lint-guard.sh` plus its `docs/specs/enforcement-boundary.md`/`docs/specs/generated-paths.md` rows — result:
```
commit 39597535: gate-registration-guard.sh (live PreToolUse Bash gate on git commit) fired for real and did not deny
```

**2. Two reliability defects.**

- Null byte crash: `ast.parse`/`compile` raise `ValueError`, not `SyntaxError`, for a source string containing an embedded null byte; only `SyntaxError` was caught in `scan_file`, so this crashed the whole scan uncaught, taking every sibling target's already-collected findings down with it. Fixed by also catching `ValueError`, reported as a `FileResult.error`.
- Permission-denied directory indistinguishable from empty: `Path.rglob("*.py")` silently swallows a `PermissionError` on a subdirectory it cannot list. Replaced with `os.walk(root, onerror=...)`; `_expand_targets` now returns `(files, errors)`, merged into `scan_targets`'s existing error list; `_run_scan`'s empty-state check reordered so a permission-denied directory is never reported with the "no .py files found" text a genuinely empty target gets.

acceptance: `python3 scripts/lint/silent_failure.py /tmp/sf_probe/nullbyte.py /tmp/sf_probe/ok_no_timeout.py` (adversarial probe, both files in one invocation) — result:
```
ERROR /tmp/sf_probe/nullbyte.py: cannot parse: ValueError: source code string cannot contain null bytes
/tmp/sf_probe/ok_no_timeout.py:2: [SF001] subprocess call has no explicit timeout= ...
/tmp/sf_probe/ok_no_timeout.py:2: [SF002] subprocess call's result is discarded ...
RC=1
```
The sibling file's own findings survive the null-byte crash.

acceptance: `python3 scripts/lint/silent_failure.py /tmp/sf_probe2` (a `chmod 000` subdirectory containing a real `.py` file) — result:
```
ERROR /tmp/sf_probe2/locked: cannot list directory: PermissionError: [Errno 13] Permission denied: '/tmp/sf_probe2/locked'
RC=1
```

acceptance: `python3 -m pytest tests/test_issue_3228_silent_failure_lint.py -q` — result:
```
17 passed in 0.85s
```
5 of those 17 are the new reliability regression tests: `test_null_byte_is_reported_not_a_crash`, `test_null_byte_sibling_finding_survives_in_a_multi_target_scan`, `test_permission_denied_directory_is_reported_not_treated_as_empty`, `test_permission_denied_directory_cli_exits_nonzero_not_clean_pass`, `test_scan_continues_past_a_permission_denied_subdirectory`.

**3. Fixture correction (site 7, `amendment_channel.py`).** PR #3237 found the round-1 `history_before/site7_amendment_channel_fixture.py` reconstructed round 5's already-fixed `.search()`-vs-`.fullmatch()` bug, not the round-7 defect issue #3228 actually cites.
canonical: `git log --all --oneline --grep="amendment" -i`, run this session — surfaces `f699f5c6 issue-3129: round-7 fix -- real Bash tool_response shape + fixture blind spot`.
canonical: `git show f699f5c6` commit message, read this session — states the real defect: `_issue_url_from_response` already used `.fullmatch()` (from round 5) but read its text through `hook_input.tool_response_text()`, which `json.dumps()`-wraps a real Bash `tool_response` dict whole, so `fullmatch` against the bare URL pattern could never match a real payload's JSON-wrapped text; all pre-round-7 fixtures were hand-built strings, never a dict, so the gap went unnoticed.

Replaced the fixture with the real pre-round-7 code.
canonical: `git show f699f5c6^:on-the-record/hooks/amendment_channel.py` and `git show f699f5c6^:on-the-record/hooks/hook_input.py`, both read this session — source for the replacement fixture's `_old_tool_response_text`/`issue_url_from_response` functions, copied verbatim.

acceptance: `python3 -c "import sys; sys.path.insert(0,'scripts/lint'); import silent_failure as sf; r = sf.scan_file(sf._FIXTURES/'history_before'/'site7_amendment_channel_fixture.py'); print(r.error, r.findings, r.call_sites)"` — result:
```
None [] 0
```
Parses cleanly, no subprocess call site, correctly stays in the lint's documented out-of-scope set.

Added `test_site7_before_fixture_matches_real_pre_round7_history` (`tests/test_issue_3228_silent_failure_lint.py`), which re-derives the real pre-round-7 `hook_input.py` text from git at test time and asserts the fixture's own code (excluding its docstring, which legitimately narrates the round-5 history in prose) reproduces the `json.dumps()` coercion, not a `.search()` call.

**4. Catch rate.** `_CAUGHT_BEFORE`/`_MISSED_BEFORE` in `scripts/lint/silent_failure.py` are unchanged from round 1, per the spawning task's explicit instruction not to widen this round.
acceptance: `python3 scripts/lint/silent_failure.py --self-check` — result:
```
PASS: history_before/site3_git_failure_conflation.py: pre-repair shape is flagged
PASS: history_before/site4_missing_timeout.py: pre-repair shape is flagged
PASS: history_before/site1_2_consumer_preconditions.py: outside this mechanism's documented scope
PASS: history_before/site5_delegation_state_wildcard.py: outside this mechanism's documented scope
PASS: history_before/site6_forgeable_evidence.py: outside this mechanism's documented scope
PASS: history_before/site7_amendment_channel_fixture.py: outside this mechanism's documented scope
(11 more PASS lines for history_after/*, unreadable/permission-denied/syntax-error/empty-state)
RC=0
```
2 of the 7 sites (3 and 4, both subprocess-observation shapes) are caught; the other 5 (sites 1/2 sharing one function, 5, 6, 7) are not subprocess-shaped defects and remain explicitly out of scope, not silently missed.

## Why

Ordered per the spawning task's own priority: wiring first ("without it the rest is decoration"), then the two reliability defects, then the fixture correction, with the catch rate held constant.

The two-tier wiring design (blocking-but-narrow vs. advisory-but-complete) follows directly from tracing this repo's actual enforcement architecture rather than assuming a single "the CI gate" exists.
canonical: `gates/gates.py`'s `ci_reachable_gates` function (read this session) — states the real merge-blocking `--closes-only` `gates/ci.py` entry point never reaches anything registered after the `closes_only` guard in `check()`; the pre-existing `gates.subprocess_call_shape_divergence` call already sits in that unreached, advisory-only position.

Rather than dress that position up as enforcement, or skip enforcement entirely, the round adds a second, narrower mechanism (`silent-failure-lint-guard.sh`) at the one point in this repo that genuinely is enforcing for a code write: the `PreToolUse` dispatcher.
canonical: `on-the-record/hooks/record-claim-guard.sh` header comment (read this session) — "a PreToolUse hook only ever sees one write's resulting content, so this is a write-time approximation of the same intent, not a byte-identical port" — the established convention this new gate follows: scan the write's own fragment, not a full-file re-derivation. SF001 is the only one of the three rules safe to check that way without risking a false deny (SF002/SF003 need whole-function context a fragment does not carry).

Diff/fragment scoping in both tiers is a direct, measured response to PR #3237's own coverage measurement (see "What was done" item 1) — an unscoped check anywhere in this position would be indistinguishable from blocking/flagging almost everything already in the repo, not "unwritable for a new site," which is what issue #3228 actually asks for.

## Upstream basis

- PR #3237: independent verification of PR #3233, source of all four findings this round addresses. Its own record file lives on PR #3237's branch, which is not present in this working tree (PR #3233's branch); cited by PR number and `gh pr view 3237` output only, not by path.
- PR #3233 (`867f2a4361b5bd28b6ab35f5cf350b9ff097f9c9`, round 1): the lint (`scripts/lint/silent_failure.py`), its fixtures, and `tests/test_issue_3228_silent_failure_lint.py`, all edited/extended in place on the same branch this round.
- `f699f5c694800d91604fa5ed22b6d004dc4c5ddd` (`on-the-record/hooks/amendment_channel.py`, `on-the-record/hooks/hook_input.py` at the parent commit): real pre-round-7 code, source for the corrected site7 fixture.

## Open findings

none

## What did not work

None. No approach was tried and abandoned this round in the sense of code written then reverted. One design detour, recorded for context: an earlier plan considered reconstructing a full-file view inside the `PreToolUse` gate (applying `old_string`/`new_string` against the on-disk file) so SF002/SF003 could also block. Dropped before implementation once the reachability trace (see "Why") showed the live `PreToolUse` dispatch path has a much larger blast radius for a bug than the diff-scoped `gates/ci.py` advisory path, and `record-claim-guard.sh`'s own established convention already answers "how much context does a write-time gate get" with "the fragment, not the full file."

## Next steps

none — `loop_state: landed`.

acceptance: `python3 -m pytest tests/test_issue_3228_silent_failure_lint.py -q` — result:
```
17 passed in 0.85s
```

acceptance: `python3 scripts/lint/silent_failure.py --self-check` — result:
```
RC=0, 17/17 PASS
```

acceptance: `python3 -m pytest tests/ -q` — result:
```
557 passed, 2 warnings in 26.04s
```

canonical: this session's own transcript — round-1 baseline recheck done via `git stash` (stashing this round's tracked-file changes on this branch), then `python3 -m pytest on-the-record/hooks/test_hook_classification.py -q`, then `git stash pop` — result:
```
2 failed, 4 passed in 0.84s
FAILED test_registration_count_matches_the_issues_own_count
FAILED test_every_hooks_json_registration_has_a_classification_entry
```
Same 2 subtests failed identically with this round's changes removed, confirming they predate this round. The other 2 of the 4 pre-existing failures seen in the full-suite run (`test_macos_bash32_compat.py`, `harness/fixture-operator-experience/test_flow.py`) were already documented as pre-existing and unrelated by PR #3233's own round-1 record and were not independently rechecked again this round.

other mounted skills: not triggered. implementation-blueprint, silent-failure-audit, test-derivation, and work-in-english were weighed against this task at session start. This session's own tool-call history is the ground truth for what ran: no Skill tool call appears in it for any of the four. The reasoning under "Why" above (wiring placement, defect characterization, test partitioning) happened without a Skill tool call, so per issue #2062 none of the four counts as applied.
