---
issue: 3281
role: silent-failure-audit+test-derivation-e073366a
author: silent-failure-audit+test-derivation-e073366a
skills: silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false
code_under_review: scripts/issue-3041/run_pair.sh, on-the-record/hooks/amendment_channel.py, on-the-record/checks/macos_bash32_compat.py (same-commit)
loop_state: delivered
type: fix
breaking: false
verdict: all three sites the issue named are fixed; both acceptance checks pass (see Acceptance below).
upstream:
  - path: scripts/issue-3041/run_pair.sh
    sha: same-commit
  - path: on-the-record/hooks/amendment_channel.py
    sha: same-commit
  - path: on-the-record/checks/macos_bash32_compat.py
    sha: same-commit
---

# issue-3281 — silent-failure-audit+test-derivation-e073366a record

## What was done

**Site 1 — `scripts/issue-3041/run_pair.sh:96` and `:109`.** Both
`env "${UNSET_ARGS[@]}"` expansions (inside `set -euo pipefail`) are now
`env ${UNSET_ARGS[@]+"${UNSET_ARGS[@]}"}`.

canonical: `git diff -- scripts/issue-3041/run_pair.sh` (this session's own
working-tree diff):
```
-      timeout 600 env "${UNSET_ARGS[@]}" claude -p "$PROMPT" \
+      timeout 600 env ${UNSET_ARGS[@]+"${UNSET_ARGS[@]}"} claude -p "$PROMPT" \
```
(same hunk appears twice, lines 96 and 109).

derived: `bash -n scripts/issue-3041/run_pair.sh` — result: exits 0, no
syntax error.

derived: manual boundary check on this session's own bash (5.x, Linux —
cannot reproduce a bash-3.2 abort, so this only checks the guard does not
change the two argument-shape cases):
```
$ bash -c '
set -euo pipefail
UNSET_ARGS=()
env ${UNSET_ARGS[@]+"${UNSET_ARGS[@]}"} echo "empty-array: no extra args"
UNSET_ARGS=(-u FOO)
env ${UNSET_ARGS[@]+"${UNSET_ARGS[@]}"} echo "non-empty-array: passthrough" -- "${UNSET_ARGS[@]}"
'
empty-array: no extra args
non-empty-array: passthrough -- -u FOO
```
Empty array → no extra `env` args; non-empty array → the array's own args
pass through unchanged. Neither case's output differs from what the
unguarded form produces on this bash version.

**Site 2 — `on-the-record/hooks/amendment_channel.py`.** Added a new
`NoProcOnPlatform` `WriteResult` variant, checked in
`record_amendment_from_response()` before calling
`registered_repo_for_pid()`, with its own `_report_write_result()` branch
and inclusion in `main()`'s fail-closed nonzero-exit tuple.

canonical: `git diff -- on-the-record/hooks/amendment_channel.py` (this
session's own working-tree diff), key hunks:
```
+    if not os.path.isdir("/proc"):
+        return NoProcOnPlatform()
+
     registered_repo = registered_repo_for_pid(
```
```
+    if isinstance(result, NoProcOnPlatform):
+        sys.stderr.write(
+            "amendment-channel: this platform has no /proc (macOS) -- "
+            "ancestry-based repo attribution cannot run here at all, for "
...
+    elif isinstance(result, NoRegisteredRepo):
```
```
-    if isinstance(write_result, (NoRegisteredRepo, NoIssueUrlInResponse,
-                                  RepoMismatch, MarkerWriteFailed)):
+    if isinstance(write_result, (NoProcOnPlatform, NoRegisteredRepo,
+                                  NoIssueUrlInResponse, RepoMismatch,
+                                  MarkerWriteFailed)):
```
The pre-existing `NoRegisteredRepo` stderr message's "(no /proc on this
platform, ...)" clause was removed, since that cause is now reported
through the new variant instead.

**Site 3 — `on-the-record/checks/macos_bash32_compat.py`.** Added
`"amendment_channel.py"` to `KNOWN_PROC_SITES`.

canonical: `grep -n KNOWN_PROC_SITES on-the-record/checks/macos_bash32_compat.py`
— result:
```
65:KNOWN_PROC_SITES = {"roster.py", "watchdog.py", "amendment_channel.py"}
```

**Test added.** `tests/test_amendment_channel.py::
RecordAmendmentFromResponse::
test_no_proc_on_platform_is_fail_closed_with_a_distinct_notice` — mocks
`os.path.isdir` so only `/proc` reports absent, asserts the result is
`NoProcOnPlatform` (and explicitly not `NoRegisteredRepo`), no marker is
written, and the emitted stderr contains both "no /proc" and "macOS".

## Why

**Where the notice lives.** The issue's own constraint decided this: the
notice must fire when /proc is genuinely unavailable, not on every
ancestry miss on Linux (a miss there is already a legitimate fail-closed
report via `NoRegisteredRepo`, unchanged by this fix).
`registered_repo_for_pid()`'s own `if not os.path.isdir("/proc")` check
(pre-existing, untouched) is the exact boundary between "this platform
structurally cannot do this, ever" and "this session's own
ancestry/roster state happens to be unresolvable." Checking that same
condition one level up, in `record_amendment_from_response()`, before the
walk is attempted, gives the platform-gap case its own `WriteResult`
variant without touching `registered_repo_for_pid()` itself — it still
returns bare `None` for both causes.

canonical: `tests/test_amendment_channel.py:736` (`test_no_proc_on_this_platform_resolves_to_none`,
pre-existing, unmodified by this change) still asserts
`registered_repo_for_pid()` returns `None` for the /proc-absent case —
confirms the internal function's contract is unchanged.

**Silent-failure-audit finding (skill invoked this session — see Skill
verdicts).** Before this fix, the /proc-absent case was not literally
absorbed with zero trace — `NoRegisteredRepo`'s stderr already fired for
it — but the message conflated three unrelated causes ("no /proc on this
platform, the roster is unreadable, or ..."), so an operator could not
tell a permanent platform gap from a one-off registration problem. The
fix routes the platform-gap case through its own variant using the exact
same fail-closed stderr + nonzero-exit machinery the other four variants
already use.

derived: `python3 -m pytest tests/test_amendment_channel.py -q` — result:
```
84 passed in 0.97s
```
(includes both the pre-existing `NoRegisteredRepo`/`AmendmentWritten`/etc.
tests, run unmodified, and the new `NoProcOnPlatform` test — all pass
together, so the split introduced no regression in the existing
classification tests.)

**Must-nots kept.** On Linux, `os.path.isdir("/proc")` is always `True`,
so the new branch never executes there.

derived: `python3 -m pytest tests/test_amendment_channel.py -q` (same run
cited above) — the pre-existing Linux-path tests
(`test_matching_repo_writes_marker_keyed_to_url_issue_number`,
`test_no_registered_repo_is_fail_closed_not_skip_silently`,
`test_unresolvable_repo_does_not_write_a_marker_and_logs_to_stderr`, and
the rest) exercise the real, un-mocked `/proc` on this Linux session and
all pass unchanged — none of them mock `os.path.isdir`, so they drive the
actual Linux code path.

## What did not work

None.

## Upstream basis

This is the first and only record for this issue (docs/issue-3281/ has no
prior report). The three sites, their line numbers, and the two must-nots
are quoted directly from issue #3281's body.

canonical: `gh issue view 3281 --repo tokenmaxxxer/on-the-record` (this
session's own fetch) — body names exactly the three sites fixed above and
the two must-nots addressed in the Why section.

## Open findings

- **A green check is not a macOS-works claim.** This fix makes the static
  check pass, and passing it is necessary but not sufficient for the
  macOS axis — it does not prove `run_pair.sh` or the amendment channel
  actually execute correctly on macOS. No macOS/bash-3.2 install-and-run
  of R007 was performed by this session (or, per the issue text, by
  anyone against today's fourteen deployments).

  canonical: this session's own shell — `bash --version` reports GNU bash
  5.x on Linux (the environment this session ran every command in above);
  no macOS or bash-3.2 environment was reachable from this session, which
  is why the shell-guard boundary check above is a manual bash-5 argument
  comparison rather than a live bash-3.2 abort/no-abort repro.

  acceptance: `python3 -m pytest on-the-record/checks/test_macos_bash32_compat.py -q` — result:
  ```
  4 passed in 0.86s
  ```
  This is a static scan of two known shapes (`check_sh_file`,
  `check_py_file` against `KNOWN_PROC_SITES`); it is the entirety of what
  "PASS" proves here.

  acceptance: `python3 -m pytest -q` — result:
  ```
  1 failed, 1652 passed, 3 xfailed in 46.03s
  ```
  FAILED: `harness/fixture-operator-experience/test_flow.py::
  test_first_contact_fires_once_per_workspace`.

  derived: `git stash && python3 -m pytest harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace -q && git stash pop`
  — result: the same test fails identically on the pre-change working
  tree (`1 failed in 0.79s`, same assertion), confirming it is
  pre-existing and not a new failure introduced by this branch's changes,
  satisfying the issue's acceptance clause "no new failures relative to
  main."

  Resolution path: an actual macOS install-and-run of R007 is follow-up
  work, out of this issue's scope (its own acceptance criteria are the
  two pytest commands above, both static/Linux-only).
- No other open findings.

## Next steps

None — terminal.

## Skill verdicts

skill-verdict: silent-failure-audit — applied: invoked; audited
`registered_repo_for_pid()`/`record_amendment_from_response()`'s
ancestry-walk failure paths in `on-the-record/hooks/amendment_channel.py`
before finalizing the fix's placement (see Why section above for the
finding and its evidence).

skill-verdict: test-derivation — applied: invoked; routed the /proc-site
requirement (issue's must: notice fires only on genuine /proc absence,
not every Linux ancestry miss) to EP/BVA over the partition {/proc
absent, /proc present+ancestry-unregistered, /proc
present+ancestry-matches}.

derived: `python3 -m pytest tests/test_amendment_channel.py -q` — result
(cited above): `84 passed` — partition 1 (/proc absent) is exercised by
the new `test_no_proc_on_platform_is_fail_closed_with_a_distinct_notice`;
partitions 2 and 3 (/proc present, ancestry unregistered / matches) are
exercised by pre-existing tests in the same run
(`test_no_registered_repo_is_fail_closed_not_skip_silently`,
`test_unresolvable_repo_does_not_write_a_marker_and_logs_to_stderr`,
`test_matching_repo_writes_marker_keyed_to_url_issue_number`) that this
change leaves unmodified. Partitions exercised / partitions identified =
3 / 3 = 100% (derived: match the three test names above one-to-one
against the three-partition list stated at the start of this paragraph).

Named gap: the shell guard's empty/non-empty array boundary (Site 1
above) has no automated pytest coverage — only the manual bash-5 boundary
check cited in "What was done" — because this session's bash-5/Linux
environment cannot exercise the bash-3.2-specific abort behavior the
guard defends against (see Open findings' canonical `bash --version`
note), and the issue's own acceptance criteria do not require a shell
unit test; `test_macos_bash32_compat.py`'s static scan
(`check_sh_file`'s `_ARRAY_BARE_RE`/`_ARRAY_GUARD_MARK` check) is the
automated coverage for that site.

other mounted skills: not triggered.

canonical: `docs/issue-3281/reports/consult-log/20260903T065245288680-2569450.md`
— the skill_judge candidates for this task (adversarial-review,
implementation-audit, technical-feasibility-reversibility-tag,
flow-metrics, prose-modes) recorded there ended with `outcome='error:
시간초과(48.78s)'` (a judge timeout, fail-open per issue #3230, not a
completed applicability verdict); none of the five were judged applicable
to this concrete three-site portability fix, so none were loaded.
