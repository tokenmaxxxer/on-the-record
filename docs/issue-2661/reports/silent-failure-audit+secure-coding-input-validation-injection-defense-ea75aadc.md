---
issue: 2661
role: silent-failure-audit+secure-coding-input-validation-injection-defense-ea75aadc
author: silent-failure-audit+secure-coding-input-validation-injection-defense-ea75aadc
skills: silent-failure-audit (skill-repository(297e350)), secure-coding-input-validation-injection-defense (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: PR #2680 body and send-back review comment
    sha: 871b30eac88fedfb874556a2efe90a6f941e516b
---

# issue-2661 — silent-failure-audit+secure-coding-input-validation-injection-defense-ea75aadc record

## What was done

Fixes the three send-back items on PR #2680 (deliverable-guard's
scratch/tmp/.git/plugin-cache exemption removal). Built on top of PR
#2680's branch tip (`871b30ea`, `issue-2661/silent-failure-audit+
secure-coding-input-validation-injection-defense-07028068`). The core
fix (`on-the-record/hooks/deliverable-guard.sh`) is untouched here.

canonical: `gh pr view 2683/2684/2685 --json state,body` — result: all
three MERGED, all three independently re-derived (not cited from each
other or from PR #2680's own record) that both of issue #2661's
acceptance checks reproduce live against PR #2680's diff and that the
exemption-removal itself is correctly scoped, with no falsifying
counter-example found for that part of the claim.

Both of the issue's own acceptance checks still reproduce unchanged on
this branch:

acceptance: real hook run against the issue's three payloads — result:

```
src/tmp/module.py              DENY
docs/tmp/note.md               DENY
tmp/docs/specs/approvers.md    DENY
```

acceptance: real hook run against the genuine issue #787 exemptions —
result:

```
docs/specs/approvers.md                       ALLOW
docs/reports/product/requirements.md          ALLOW
docs/reports/product/priorities/entry1.md     ALLOW
```

**Item 1 — `guard-nonboard-repo`'s stale assertion (`tests/run-orchestrate-tests.sh`).**
PR #2680's record claimed this test "fails identically against the
unmodified HEAD hook." canonical: `gh pr view 2685 --json body` — result:
reproduces live that this claim is false — the test *passes* on
unmodified HEAD and only starts failing after the fix, because it was
passing by accident: `guard()`'s fixture used plain `mktemp -d`, which
lands under `/tmp`, and every path under `/tmp` carries a path segment
literally named "tmp" (the `/tmp` directory itself). That segment used
to be an unconditional exemption (the very bug this issue removes), so
every `guard()` case's write silently rode through that bypass instead
of exercising the behavior each case claims to test.

Fix: `guard()`'s fixture root moved from plain `mktemp -d` to
`mktemp -d "$HERE/.guard-fixture.XXXXXX"` (never under `/tmp`), and
`guard-nonboard-repo`'s expected verdict corrected from `allow` to
`deny` — derived: `on-the-record/hooks/deliverable-guard.sh` lines
257-262 (the git-root-activation walk) and its header comment lines
16-28, quoted in full below in "Upstream basis", establish that any git
repo activates the guard regardless of board-file presence (issue #787
H1 retired "must already carry `docs/specs/approvers.md`" as the
activation signal). Once the fixture no longer rides the tmp-segment
bypass, a fresh git repo with no board files still gets a
deliverable-shaped write denied, on *both* the unmodified hook and this
branch's hook alike. Confirmed live, not asserted:

acceptance: `env -u TOKENMAXXXER_SPAWNED bash tests/run-orchestrate-tests.sh`
— result:

```
# this branch (871b30ea + this fix), non-tmp fixture
ok     directive-injects
FAIL   directive-silent-for-roles         want=0 got=58
ok     guard-docs-in-board                deny
ok     guard-src-in-board                 deny
ok     guard-tests-in-board               deny
ok     guard-approvers-ok                 allow
ok     guard-nonboard-repo                deny
ok     guard-scratch-not-exempt           deny
ok     guard-empty-stdin                  deny
ok     guard-non-json-stdin               deny
ok     guard-non-dict-json                deny
ok     guard-missing-file-path            deny
== 12 passed, 1 failed ==

# clean origin/main worktree (c9c9b6f0, unmodified hook), same repaired
# test file, fixture rooted outside /tmp (/home/jwjung/otr-clean-main)
ok     directive-injects
FAIL   directive-silent-for-roles         want=0 got=58
ok     guard-docs-in-board                deny
ok     guard-src-in-board                 deny
ok     guard-tests-in-board               deny
ok     guard-approvers-ok                 allow
ok     guard-nonboard-repo                deny
FAIL   guard-scratch-not-exempt           want=deny got=allow
ok     guard-empty-stdin                  deny
ok     guard-non-json-stdin               deny
ok     guard-non-dict-json                deny
ok     guard-missing-file-path            deny
== 11 passed, 2 failed ==
```

`directive-silent-for-roles` fails identically on both — genuinely
pre-existing, unrelated (unchanged by this fix or PR #2680). The only
other difference is `guard-scratch-not-exempt`, which is expected to
differ: FAIL on unmodified HEAD (the actual bug — the "scratch/notes.md"
test payload's own relative path carries a literal "scratch" segment),
PASS on this branch (the fix removes that exemption). `guard-nonboard-repo`
no longer appears in either failure set — it was never a real
pre-existing failure once its fixture stopped rigging its own result; it
is simply a passing test on both branches now.

**Item 2 — `expectedFailure` coverage claim was inaccurate
(`test/test_deliverable_guard_priorities_shard.py`).** PR #2680's record
claimed the three existing `expectedFailure` cases (planted `.git`
directory / symlink / linked worktree) already cover the git-root walk's
steerability for `EXEMPT_SUFFIXES` (the anchoring this PR added for
`docs/specs/approvers.md` and friends). derived:
`grep -n "expectedFailure\|def test_" test/test_deliverable_guard_priorities_shard.py`
— result: all three existing cases target `PRODUCT_CAPTURE_PRIORITIES_DIR_RE`
(the priorities-shard exemption) via a "src/docs/reports/product/priorities/hack.md"
test payload — none target `EXEMPT_SUFFIXES`. Reproduced live that the
same bypass reaches `EXEMPT_SUFFIXES` too:

acceptance: planted-`.git` reproduction against `docs/specs/approvers.md`
— result:

```
$ mkdir -p "$repo/src/.git" "$repo/src/docs/specs"
$ printf '{"tool_name":"Write","tool_input":{"file_path":"%s","content":"x"},"cwd":"%s"}' \
    "$repo/src/docs/specs/approvers.md" "$repo" \
    | env -u CLAUDE_ROLE -u TOKENMAXXXER_SPAWNED /bin/bash on-the-record/hooks/deliverable-guard.sh
rc=0   # EXEMPT — should be 2 (DENY): this is a src/-rooted deliverable
       # write, not the sanctioned docs/specs/approvers.md
```

Per #2637's own landing precedent (assert the residual gap as
`expectedFailure` tests, not a sentence in a comment), added one
`expectedFailure` case,
`test_bypass_via_planted_git_directory_reaches_exempt_suffixes`, pinning
this down the same way the three existing cases pin down the
priorities-shard variant — same underlying `_git_root_from` mechanism,
not a new one, and not fixed here (out of scope per #2637 round 4's own
finding, quoted in `deliverable-guard.sh` lines 167-224, that no
path-shaped resolution closes this while the hook decides from
session-reported strings and session-mutable filesystem state before the
write happens).

acceptance: `python3 -m pytest test/test_deliverable_guard_priorities_shard.py -q`
— result: `16 passed, 4 xfailed` (was `16 passed, 3 xfailed` on PR
#2680; the added case is the fourth xfail, not a new failure).

**Item 3 — undisclosed side effects.** canonical: `gh pr view 2683 --json body`
— result: PR #2683 found, and this branch's own test runs above
independently reproduce, that PR #2680 silently fixes three additional
`tests/run-orchestrate-tests.sh` cases beyond what its body describes:
`guard-docs-in-board`, `guard-src-in-board`, and `guard-tests-in-board`.
On unmodified `origin/main`, all three were silently mis-passing as
`allow` — not because the deliverable-shaped-path denial logic was
working, but because the harness's own `mktemp -d` fixture sat under
`/tmp`, and the very tmp-segment exemption this PR removes exempted the
write regardless of the actual target path ("docs/issue-3/reports/product.md",
"src/app.py", "tests/test_app.py" — synthetic test-fixture payloads
defined in `tests/run-orchestrate-tests.sh`, not files that exist in
this repo). Once the exemption is removed, all three correctly deny —
genuine coverage the original PR delivered but never mentioned in its
body or test-plan checklist. This record states it explicitly, as this
send-back required.

## Why

canonical: `gh pr view 2683/2684/2685 --json state,body` — result: all
three independent verifications (all MERGED) confirm the
exemption-removal fix itself with no falsifying counter-example, so the
core fix is not in question.

Chose to repair the fixture and the one stale assertion rather than
revert any part of the exemption-removal fix or weaken
`guard-scratch-not-exempt`'s "deny" expectation — the send-back was
explicit on this point, and the failure being fixed here is in the test
harness's own fixture confound, not in the fix itself. Moving `guard()`'s
fixture root to `"$HERE/.guard-fixture.XXXXXX"` (never under `/tmp`)
fixes the confound for every case in that helper, not just
`guard-nonboard-repo`, since any future case sharing the same
`mktemp -d` helper would otherwise inherit the identical
accidental-pass risk.

For the `EXEMPT_SUFFIXES` coverage gap, followed #2637's own precedent
literally rather than inventing a new resolution: that issue's round 4
already established, after a dedicated consult, that no path-shaped fix
closes the git-root-walk steerability while this hook decides from
session-reported strings and session-mutable filesystem state before the
write happens — re-deriving that conclusion here would be redundant.
The choice per this send-back's instruction was "assert it as
`expectedFailure`, or state plainly it survives uncovered." Asserting it
is strictly stronger (it pins the gap down as a live, re-checked
regression instead of a claim that could drift out of sync with the code
again), and costs one small test mirroring an existing pattern already
in the file.

## What did not work

None — the fixture-root fix, the added `expectedFailure` case, and the
disclosure were all straightforward once the live reproductions in the
send-back review (and PR #2683/#2685's own findings) pinned down exactly
what to check.

## Upstream basis

- PR #2680 (branch `issue-2661/silent-failure-audit+secure-coding-input-validation-injection-defense-07028068`,
  tip `871b30eac88fedfb874556a2efe90a6f941e516b`) — carries the three
  send-back items this record resolves, in its review comment.
- PR #2683 — canonical: `gh pr view 2683 --json body` — found the
  `EXEMPT_SUFFIXES` coverage inaccuracy and the three undisclosed
  side-effect cases.
- PR #2685 — canonical: `gh pr view 2685 --json body` — found and
  explained the `guard-nonboard-repo` accidental-pass mechanism (the
  `/tmp`-fixture confound).
- Issue #2637 round 4's finding and its "no path-shaped fix" conclusion
  — derived: `sed -n '167,224p' on-the-record/hooks/deliverable-guard.sh`
  (the `_git_root_from` steerability comment) and
  `test/test_deliverable_guard_priorities_shard.py`'s three existing
  `expectedFailure` cases — the precedent this record's new test
  mirrors.

## Open findings

None new. The `EXEMPT_SUFFIXES` git-root-walk steerability is now
covered as an `expectedFailure` regression test rather than left as an
uncovered claim; its resolution path is unchanged from #2637 round 4's
own deferral (out of scope for a path-shaped fix). PR #2680's own
already-disclosed open finding (`PRODUCT_CAPTURE_ISSUE_RE` left
unanchored) is untouched by this record — not part of this send-back.

skill-verdict: silent-failure-audit — not-applicable: this item repairs
a test harness's fixture confound and adds regression coverage for an
already-documented, already-deferred bypass; it does not touch new
production error-handling code (try/catch, rejection, error callback) to
audit.
skill-verdict: secure-coding-input-validation-injection-defense — not-applicable:
the allowlist-vs-denylist validation approach for
`EXEMPT_SUFFIXES`/`PRODUCT_CAPTURE_PRIORITIES_DIR_RE` was already chosen
and verified correct by three independent prior sessions; this item adds
test coverage for an already-disclosed residual gap in that approach,
not a new validation/encoding decision.

## Next steps

None remaining for this item — fixture repaired, coverage added,
disclosure written, committed. Push and PR open the delivery.
