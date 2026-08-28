---
issue: 2600
role: silent-failure-audit+test-authoring-isolation-and-fixture-strategy-d44249ff
author: silent-failure-audit+test-authoring-isolation-and-fixture-strategy-d44249ff
skills: silent-failure-audit (skill-repository(297e350)), test-authoring-isolation-and-fixture-strategy (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: PR #2675 body, "Open finding, out of this send-back's scope" paragraph
    sha: 0a34a752fcbb98563be20696c1ecf9703e0091a9
---

# issue-2600 — silent-failure-audit+test-authoring-isolation-and-fixture-strategy-d44249ff record

## What was done

Fixed the fourth send-back item on PR #2675 (branch
`issue-2600/silent-failure-audit+technical-writing-structure-comprehension-5597774d`,
tip `0a34a752`): PR #2673's original commit edited three comment lines in
`on-the-record/hooks/approval-gate.sh` (retiring "role-session" ->
"spawned-session" and "acting role's own" -> "acting session's own"
wording), and `test/test_auto_approval_shadow_wiring.py::
SimulatedApprovalAppendsSampleTest::test_approval_gate_sh_is_byte_identical`
asserts that exact file is byte-identical to `origin/main` via
`git diff --exit-code origin/main HEAD -- on-the-record/hooks/approval-gate.sh`.

acceptance: `python3 -m pytest test/ -q` — result:

```
# clean origin/main (8862a33b) worktree, /tmp/otr-main-check
15 failed, 358 passed, 3 xfailed in 2.99s

# this branch, before the fix (HEAD=0a34a752)
16 failed, 357 passed, 3 xfailed in 2.95s   # + test_approval_gate_sh_is_byte_identical

# this branch, after the fix (HEAD=464cd9bb)
15 failed, 358 passed, 3 xfailed in 2.53s

# diff <(sort main_failed.txt) <(sort branch_failed.txt) -> empty, identical failure sets
```

Checked out PR #2675's branch tip (`0a34a752`) as a new commit on top under
this session's own branch, reverted `on-the-record/hooks/approval-gate.sh`
to `origin/main`'s byte-for-byte content (`git checkout origin/main --
on-the-record/hooks/approval-gate.sh`), and committed that single-file
revert (`464cd9bb`). The three "role" occurrences in that file's comments
are left untouched and deferred to a later, separately-authorized slice
per PR #2675's own body — not part of this fix.

## Why

Two defensible fixes existed: revert the hunk (freeze is absolute, bytes
included), or widen the assertion to ignore comment-only diffs (freeze is
about behavior, not bytes). Read issue #1739 (the auto-approval
shadow-wiring issue that introduced this test) and the test's own
docstrings first:

- Requirement 2 of #1739: "any diff touching `on-the-record/hooks/`,
  `gates/`, `docs/specs/`, or any file defining approval/gate semantics is
  ALWAYS human-required... Auto-approval logic can never approve a change
  to itself (circular-trust ban)." This requirement is about auto-approval
  *classification/routing*, not a literal ban on ever editing those files.
- The test method's own docstring: "diff assertion: this PR's
  approval-gate.sh (working tree) must be byte-identical to origin/main's
  copy" — written for PR #1791 (the shadow-wiring PR itself), to prove
  *that* PR's own diff didn't need to touch the trust-boundary hook. It is
  phrased as a point-in-time self-check, not explicitly as a permanent
  freeze on all future PRs.

Despite the narrower textual scope of #1739's requirement 2, the test as
actually written is a literal `git diff` against `origin/main` with no
allowance for comment-only or non-behavioral change — it makes no
distinction between "auto-approval touched this file" and "any PR touched
this file." Weakening that literal check (e.g. diffing with comments
stripped) means a session inside this same governance system unilaterally
narrowing an assertion that guards the circular-trust boundary the
governance system itself relies on — exactly the shape of self-referential
risk #1739 was written to foreclose. Reverting costs one file's three
comment lines, deferred to a future slice that can widen or retire this
test as its own explicitly-scoped, explicitly-approved change; widening it
here as a side effect of an unrelated wording-retirement task is the
higher-risk option for a reversible, one-file cost. Chose revert.

## What did not work

None.

## Upstream basis

- PR #2675 (branch `issue-2600/silent-failure-audit+technical-writing-structure-comprehension-5597774d`,
  tip `0a34a752fcbb98563be20696c1ecf9703e0091a9`) — carries the Open
  finding this record resolves, in its PR body.
- Issue #1739 (`gh issue view 1739`) — origin of
  `test/test_auto_approval_shadow_wiring.py` and the circular-trust-ban
  requirement.
- `test/test_auto_approval_shadow_wiring.py:154-160` — the
  `test_approval_gate_sh_is_byte_identical` assertion and its docstring.

## Open findings

None from this item. The three retired-word occurrences left in
`on-the-record/hooks/approval-gate.sh`'s comments are a known, logged
deferral, not a new open finding — see the "Why" section above and PR
#2675's own body.

skill-verdict: silent-failure-audit — not-applicable: this item is a
test-assertion-scope judgment call (byte-diff freeze vs. behavioral
freeze) on an existing test, not an audit of unaudited error-handling
paths (try/catch, rejection, error callback) in new production code.
skill-verdict: test-authoring-isolation-and-fixture-strategy —
not-applicable: the decision concerns what a test's assertion should
verify (bytes vs. behavior) and a governance trust boundary, not fixture
scope, shared-state isolation between tests, or test-double kind choice.

## Next steps

None remaining for this item — reverted, verified (see `acceptance:`
block above), committed as `464cd9bb`. Push and PR open the delivery.
