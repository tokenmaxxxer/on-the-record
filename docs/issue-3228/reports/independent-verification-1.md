---
issue: 3228
role: independent-verification-1
author: independent-verification-1
verifies_subject: true
code_under_review: PR #3233, sha e92623b5e76dc7cb4f16c6023b9acb0461a649d1 (scripts/lint/silent_failure.py, tests/test_issue_3228_silent_failure_lint.py, scripts/lint/fixtures/silent_failure/**)
loop_state: complete
type: review
breaking: false
verdict: fail
upstream:
  - path: e92623b5e76dc7cb4f16c6023b9acb0461a649d1:docs/issue-3228/reports/silent-failure-audit+implementation-blueprint+test-derivation-ed55a103.md
    sha: e92623b5e76dc7cb4f16c6023b9acb0461a649d1
  - path: e92623b5e76dc7cb4f16c6023b9acb0461a649d1:scripts/lint/silent_failure.py
    sha: e92623b5e76dc7cb4f16c6023b9acb0461a649d1
  - path: 86b9ebbb6ac30caf62f2ffcfcee3a7625e1c5a46:docs/issue-3228/reports/adversarial-review+silent-failure-audit+test-depth-audit-00aea41d.md
    sha: 86b9ebbb6ac30caf62f2ffcfcee3a7625e1c5a46
---

# issue-3228 — independent-verification-1 record

## What was done

Independent, second-observer verification of PR #3233 (issue #3228's
`e92623b5e76dc7cb4f16c6023b9acb0461a649d1:scripts/lint/silent_failure.py`
AST lint), built in a separate worktree checked out at PR #3233's head
commit `e92623b5e76dc7cb4f16c6023b9acb0461a649d1` (`/tmp/pr3233-check`,
from `origin/issue-3228/silent-failure-audit+implementation-blueprint+
test-derivation-ed55a103`). This session did not edit PR #3233, comment
on it, or coordinate with the session that wrote PR #3237 (the first
independent verification) — findings below were reproduced from scratch
before PR #3237's record was read closely enough to compare against.

acceptance: `python3 -m pytest tests/test_issue_3228_silent_failure_lint.py -q` (run in /tmp/pr3233-check, at e92623b5e76dc7cb4f16c6023b9acb0461a649d1) — result:
```
...........                                                              [100%]
11 passed in 0.85s
```

acceptance: `python3 scripts/lint/silent_failure.py --self-check` (run in /tmp/pr3233-check, at e92623b5e76dc7cb4f16c6023b9acb0461a649d1) — result:
```
no subprocess call sites found across the scanned target(s) -- refusing to report a clean pass ...
PASS: history_before/site3_git_failure_conflation.py: pre-repair shape is flagged
PASS: history_before/site4_missing_timeout.py: pre-repair shape is flagged
PASS: history_before/site1_2_consumer_preconditions.py: outside this mechanism's documented scope (not a subprocess-observation defect)
PASS: history_before/site5_delegation_state_wildcard.py: outside this mechanism's documented scope (not a subprocess-observation defect)
PASS: history_before/site6_forgeable_evidence.py: outside this mechanism's documented scope (not a subprocess-observation defect)
PASS: history_before/site7_amendment_channel_fixture.py: outside this mechanism's documented scope (not a subprocess-observation defect)
PASS: history_after/site3_git_failure_conflation.py: repaired shape stays quiet
PASS: history_after/site4_missing_timeout.py: repaired shape stays quiet
PASS: history_after/site1_2_consumer_preconditions.py: repaired shape stays quiet
PASS: history_after/site5_delegation_state_wildcard.py: repaired shape stays quiet
PASS: history_after/site6_forgeable_evidence.py: repaired shape stays quiet
PASS: history_after/site7_amendment_channel_fixture.py: repaired shape stays quiet
PASS: a nonexistent/unreadable file reports an error, not a silent skip
PASS: a permission-denied file reports an error, not a silent skip
PASS: a file with a syntax error reports an error, not a silent skip
PASS: a target with zero subprocess call sites is distinguished from a clean pass
PASS: scanning that same zero-call-site target end-to-end exits nonzero
SELF_CHECK_EXIT=0
```

Both `## Acceptance` check: lines from issue #3228 hold, matching PR
#3233's own record's claim (11 passed; 17/17 self-check assertions PASS,
exit 0) — reproduced independently above, not merely re-read from that
record.

Then independently checked whether the lint is wired into any automated,
repo-run check that scans a *new or changed* source file (as opposed to
its own bundled fixtures), since that is the literal ask of issue #3228
("a mechanism that catches the class at authoring time").

derived: `grep -rl "silent_failure" --include="*.py" .` (run in /tmp/pr3233-check, at e92623b5e76dc7cb4f16c6023b9acb0461a649d1) — result:
```
tests/test_failed_no_commit_reconcile.py
tests/test_issue_3228_silent_failure_lint.py
scripts/lint/silent_failure.py
scripts/lint/fixtures/silent_failure/history_before/site1_2_consumer_preconditions.py
```

derived: `grep -n "silent_failure\|lint" gates/ci.py gates/merge_gate.py gates/check_runner.py` (run in /tmp/pr3233-check, at e92623b5e76dc7cb4f16c6023b9acb0461a649d1) — result:
```
gates/ci.py:60:import record_lint
gates/ci.py:619:    bad += record_lint.record_wellformed_in(repo)
gates/ci.py:620:    bad += record_lint.record_no_tool_residue_in(repo)
gates/ci.py:625:    bad += record_lint.record_checked_claims(repo, {})
```

`e92623b5e76dc7cb4f16c6023b9acb0461a649d1:gates/ci.py` wires in
`record_lint` (a pre-existing, unrelated record-shape lint) but never
imports or calls `scripts/lint/silent_failure`; no `.github/*.yml`, no
`pre-commit` config, and no other `gates/*.py` file references it either
(derived from the same greps above — empty result set for those paths).
canonical: `e92623b5e76dc7cb4f16c6023b9acb0461a649d1:tests/test_issue_3228_silent_failure_lint.py` — the only test in that
file that runs automatically without arguments is `test_self_check_passes`
(`_run("--self-check")`), which only scans the lint's own bundled
`scripts/lint/fixtures/silent_failure/` directory — never a git diff,
changed-files list, or the repo at large. `main()` in
`e92623b5e76dc7cb4f16c6023b9acb0461a649d1:scripts/lint/silent_failure.py`
does accept arbitrary path arguments (`_run_scan(argv)`, line 523) and can
scan real files when invoked by hand, but nothing in this repo invokes it
that way automatically.

This independently reproduces PR #3237's central finding
(canonical: `86b9ebbb6ac30caf62f2ffcfcee3a7625e1c5a46:docs/issue-3228/reports/adversarial-review+silent-failure-audit+test-depth-audit-00aea41d.md`,
"Central finding" in its Summary): the mechanism, as landed, does not
make the silent-failure shape unwritable for a new subprocess call site —
only its two hardcoded historical fixtures and its own bundled test
fixtures are ever checked automatically. A brand-new site with exactly
the missing-timeout or git-failure-conflation shape would merge today
without the lint ever seeing it.

Also independently reproduced, by direct attack (not by reading PR
#3237's account of them first), the same two reliability defects that
record also reports:

derived: `printf 'import subprocess\nsubprocess.run(["ls"], timeout=5)\x00\n' > /tmp/sf_test/nullbyte.py && python3 scripts/lint/silent_failure.py /tmp/sf_test/nullbyte.py; echo exit=$?` (run in /tmp/pr3233-check, at e92623b5e76dc7cb4f16c6023b9acb0461a649d1) — result:
```
Traceback (most recent call last):
  ...
  File ".../silent_failure.py", line 360, in scan_file
    tree = ast.parse(text, filename=str(path))
ValueError: source code string cannot contain null bytes
exit=1
```
An uncaught exception on a null byte is a crash, not a reported per-file
error — a multi-file scan hitting this file would lose every other
file's findings in the same run, not just this file's.

derived: `chmod 000 /tmp/sf_test/denied_dir && python3 scripts/lint/silent_failure.py /tmp/sf_test/denied_dir; echo exit=$?` then the same command against a genuinely empty directory (run in /tmp/pr3233-check, at e92623b5e76dc7cb4f16c6023b9acb0461a649d1) — result:
```
$ python3 scripts/lint/silent_failure.py /tmp/sf_test/denied_dir; echo exit=$?
no .py files found under the given target(s)
exit=1

$ python3 scripts/lint/silent_failure.py /tmp/sf_test/empty_dir; echo exit=$?
no .py files found under the given target(s)
exit=1
```
A permission-denied directory (a `.py` file exists inside but cannot be
read) prints the identical message and exit code as a directory that
genuinely contains no Python files — "could not observe" and "nothing to
observe" collapse to the same signal. This is the exact defect shape
issue #3228 names, reproduced inside the tool built to catch it.

unverifiable: PR #3237's third finding — that
canonical: `e92623b5e76dc7cb4f16c6023b9acb0461a649d1:scripts/lint/fixtures/silent_failure/history_before/site7_amendment_channel_fixture.py`
implements a different, already-fixed bug than the one issue #3228's
site 7 actually cites — was not independently re-derived by this
session: the fixture's own docstring is self-consistent and explicitly
marked "DOCUMENTED MISS: ... invisible to a subprocess-observation
lint", but re-running PR #3237's wider git-history search to confirm or
refute the mismatch claim itself was out of scope for this pass. Carried
forward unverified, attributed to
`86b9ebbb6ac30caf62f2ffcfcee3a7625e1c5a46:docs/issue-3228/reports/adversarial-review+silent-failure-audit+test-depth-audit-00aea41d.md`.

## Why

Issue #3228 requires two independent verification records
(`docs/handbooks/observer-verification.md`,
`REQUIRED_INDEPENDENT_VERIFICATIONS = 2`) before the subject's own PR can
merge. PR #3237 supplies one
(canonical: `86b9ebbb6ac30caf62f2ffcfcee3a7625e1c5a46:docs/issue-3228/reports/adversarial-review+silent-failure-audit+test-depth-audit-00aea41d.md`
frontmatter — `verifies_subject: true`, author
`adversarial-review+silent-failure-audit+test-depth-audit-00aea41d`,
`verdict: fail`). This session was spawned to supply the second, from an
author distinct from both the subject's deliverable author and PR
#3237's author, per the spawn instructions and `CORE_BUILD_NOW=1`
(build-now bypass: deliver directly on
`issue-3228/independent-verification-1`, no proposal round).

Chose to re-derive the central question from scratch (run the checks
myself against PR #3233's actual head commit, grep the gate files
myself, attack the tool with hostile inputs myself) rather than simply
reading PR #3237's record and affirming it, because a verification
record whose only content is agreement with the prior one adds no
independent evidence toward the count this issue requires. Independently
reproducing the same finding by a different route (path enumeration +
gate-file grep, plus fresh hostile-input attacks, all captured in
`## What was done` above) is what makes this a second *independent*
verification rather than a rubber stamp on the first.

## What did not work

None.

## Upstream basis

- `e92623b5e76dc7cb4f16c6023b9acb0461a649d1:docs/issue-3228/reports/silent-failure-audit+implementation-blueprint+test-derivation-ed55a103.md` —
  PR #3233's own record; the subject deliverable being verified.
- `e92623b5e76dc7cb4f16c6023b9acb0461a649d1:scripts/lint/silent_failure.py`,
  `e92623b5e76dc7cb4f16c6023b9acb0461a649d1:tests/test_issue_3228_silent_failure_lint.py`,
  `e92623b5e76dc7cb4f16c6023b9acb0461a649d1:scripts/lint/fixtures/silent_failure/` —
  the code under review, checked out and run directly in a separate
  worktree (`/tmp/pr3233-check`).
- `86b9ebbb6ac30caf62f2ffcfcee3a7625e1c5a46:docs/issue-3228/reports/adversarial-review+silent-failure-audit+test-depth-audit-00aea41d.md` —
  the first independent verification (PR #3237); read only after the
  reproductions in `## What was done` above were already run, to compare
  results rather than to source them.

## Open findings

1. **Central:** derived: reproduced above (`## What was done`, the two
   `grep`-tagged blocks against `e92623b5e76dc7cb4f16c6023b9acb0461a649d1`) —
   the lint is not wired into any automated, repo-run check that scans a
   new or changed source file; only its own bundled self-check fixtures
   run automatically via
   `e92623b5e76dc7cb4f16c6023b9acb0461a649d1:tests/test_issue_3228_silent_failure_lint.py`.
   Resolution path: wire `scripts/lint/silent_failure.py` into
   `gates/ci.py` (or an equivalent changed-files/pre-merge hook) the same
   way `record_lint` is already wired there, scanning at minimum the
   files touched by a PR's diff. Until that lands, the class issue #3228
   asks to make unwritable remains writable for every site except the
   two hardcoded regression targets.
2. **Reliability:** derived: reproduced above (`## What was done`, the
   null-byte block) — a null byte in a scanned `.py` file crashes the
   scan with an uncaught `ValueError` instead of reporting a per-file
   error, losing sibling findings in the same run. Resolution path: catch
   `ValueError` (and other `ast.parse` failures) per-file in `scan_file`,
   same as the existing syntax-error handling.
3. **Reliability:** derived: reproduced above (`## What was done`, the
   chmod-000 block) — a permission-denied directory produces the
   identical "no .py files found" message and exit code as a genuinely
   empty directory. Resolution path: distinguish "0 files found,
   directory readable" from "could not enumerate directory contents"
   (catch `PermissionError` from the directory walk and report it as a
   scan error, not a zero-file result).
4. **Not independently re-derived** (see `unverifiable:` tag in
   `## What was done` above): PR #3237's claim that the site7 "before"
   reconstruction implements a different, already-fixed bug than issue
   #3228's actual site 7. Resolution path: a future session re-runs PR
   #3237's git-history search and either confirms or refutes it
   explicitly.

## Next steps

derived: this record's own frontmatter (`loop_state: complete`, set in
this same commit) — no further action from this session. Findings 1-3
above are confirmed defects, each backed by its own `derived:`-tagged
reproduction in `## What was done`, for a future repair session — either
a revision of PR #3233 or a follow-up issue — to act on; this record's
own obligation (supply a second independent, evidenced verification
toward `REQUIRED_INDEPENDENT_VERIFICATIONS = 2`) is discharged.

skill-verdict: test-depth-audit — not-applicable: this record verifies a lint tool's own behavior and its repo-wide wiring, not a test suite's assertion quality; no test-suite classification (Genuine Assertion / Execution-Only / Mock-Dominated / Happy-Path-Only / Dead) was performed.
other mounted skills: not triggered
