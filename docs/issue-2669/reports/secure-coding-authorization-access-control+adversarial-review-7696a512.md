---
issue: 2669
role: secure-coding-authorization-access-control+adversarial-review-7696a512
author: secure-coding-authorization-access-control+adversarial-review-7696a512
skills: secure-coding-authorization-access-control (skill-repository(297e350)), adversarial-review (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
code_under_review: 338cac10d307ed3dfb0a884466735dd548724c6a
type: fix
breaking: false
verdict: narrowed-with-two-named-residual-gaps
upstream:
  - path: on-the-record/hooks/upstream-defect-scope-guard.sh
    sha: 338cac10d307ed3dfb0a884466735dd548724c6a
  - path: test/test_upstream_defect_scope_guard_cross_repo_cwd.py
    sha: 338cac10d307ed3dfb0a884466735dd548724c6a
---

# issue-2669 — secure-coding-authorization-access-control+adversarial-review-7696a512 record

## What was done

Send-back on PR #2700 (issue #2669's first fix attempt).
canonical: `gh pr view 2700 --json state,headRefName` — result: `{"headRefName":"issue-2669/secure-coding-authorization-access-control+silent-failure-audit-604a6e6b","state":"OPEN"}`.
Independent adversarial verification of PR #2700 (PR #2703) confirmed
PR #2700's two disclosed claims and two disclosed narrower-coverage
gaps, but found a critical undisclosed regression.
canonical: `gh pr view 2703 --json state,mergedAt` — result: `{"mergedAt":"2026-08-29T07:39:06Z","state":"MERGED"}`.
PR #2700's `operative_cwd()` made the guard's pre-existing
unresolvable-origin fail-open fallback attacker-steerable —
`cd <dir> && gh pr create --repo <anything>` where `<dir>` is not a
real git checkout (`/tmp`, a nonexistent path) was allowed for *any*
target repo, because `origin_repo()` returning `None` made `in_scope()`
fall open regardless of who chose the unresolvable directory.

Fixed `on-the-record/hooks/upstream-defect-scope-guard.sh` by having
`operative_cwd()` report a second value — whether the returned directory
came from a leading `cd` in the command text (session-chosen) or is the
harness's own payload `cwd` (not session-chosen) — and threading that
through `origin_repo()` to `in_scope()`. `in_scope()` now fails open on
an unresolvable origin ONLY when the unresolvable directory is the
harness's payload cwd (the pre-#2669 posture, preserved); an unresolvable
session-chosen `cd` target is now treated as in-scope (denied, when a
target repo was extracted), closing the bypass. No other guard branch
touched — channel-role signal, extraction regexes, and deny messages are
all unchanged from PR #2700.
canonical: `338cac10:on-the-record/hooks/upstream-defect-scope-guard.sh` diff (`operative_cwd`, `origin_repo`, `in_scope`).

Also fixed the smaller finding from the same send-back: `test/
test_upstream_defect_scope_guard_cross_repo_cwd.py`'s `_init_repo_with_
origin()` had 2 of its 3 new `subprocess.run` call sites missing
`timeout=` (the `git init`/`git remote add` calls; `_run_guard`'s call
already had `timeout=30`). Added `timeout=30` to both.
canonical: `338cac10:test/test_upstream_defect_scope_guard_cross_repo_cwd.py` diff (`_init_repo_with_origin`).

Added two regression tests for the send-back's exact bypass shape
(`test_cd_into_non_checkout_dir_still_denied`,
`test_cd_into_nonexistent_dir_still_denied`) plus a control proving the
harness-cwd fail-open posture is untouched
(`test_harness_cwd_unresolvable_without_cd_still_fails_open`).
derived: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v` — result: `7 passed, 2 xfailed in 0.85s`.

Before finalizing, ran a real blind adversarial-review pass on just this
diff (a fresh subagent, given only the unified diff, no issue context,
no builder framing — the actual two-party protocol the mounted
`adversarial-review` skill describes, not a self-critique). It found six
issues; one was real and actionable: my new docstring claimed the
harness-payload-cwd fail-open case "is not something a session can
choose to trigger," which is false — a session with ordinary write
access to its own harness workspace can `git remote remove origin`
there in an earlier call, then make a later bare (no-`cd`) `gh pr
create` call fail open for any target too. This is NOT a new regression
(it is the guard's pre-#2669 posture, explicitly kept as "fail open, as
today" by this send-back's own instructions, and requires mutating the
harness's own checkout rather than picking an arbitrary directory), but
the comment's absolute claim was wrong and the gap was undisclosed.
Corrected the comment and added
`test_harness_cwd_origin_removed_bypass_should_be_denied`
(`@unittest.expectedFailure`, same posture as the pre-existing
spoofed-origin gap) to disclose it live rather than leave it as an
inaccurate claim in a comment.
canonical: `338cac10:on-the-record/hooks/upstream-defect-scope-guard.sh` `in_scope()` docstring.
derived: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_harness_cwd_origin_removed_bypass_should_be_denied -v` — result: `XFAIL` (confirmed genuinely open, not accidentally closed).

Full suite comparison, `origin/main` vs. this branch's head
(`338cac10`):
derived: `python3 -m pytest test/ -m "not slow" -q` on `origin/main` — result: `15 failed, 380 passed, 4 xfailed in 2.55s`.
derived: `python3 -m pytest test/ -m "not slow" -q` on `338cac10` — result: `15 failed, 387 passed, 6 xfailed in 2.55s`.
Same 15-failed count on both, net +7 passed / +2 xfailed on this
branch, matching this branch's two test-file additions (PR #2700's 4
passed + 1 xfailed, plus this fix's 3 passed + 1 xfailed).

## Why

The send-back's constraint was the hard part: the unresolvable-origin
case had to stop being an allow when the directory is session-chosen,
without simply flipping it to deny outright, because the fallback
exists precisely for the harness's own cwd legitimately failing to
resolve (denying there would break ordinary sessions with no
adversarial intent at all). The two cases needed telling apart, and the
command text already carries the distinguishing signal: whether a
`cd <dir> &&`/`cd <dir>;` prefix is present. `operative_cwd()` already
parsed that prefix for PR #2700's fix; it only needed to also report
*that it did*, rather than silently collapsing "resolved via `cd`
target" and "resolved via payload cwd" into the same return shape that
`in_scope()` couldn't tell apart. This is a small, mechanical change
riding the same signal PR #2700 already introduced — not a new
resolution scheme — which is why it doesn't reopen the #2637-class
question of whether a fully unsteerable signal exists at all (it
doesn't try to be one; it only stops the *specific* new steerability PR
#2700 introduced).
canonical: `338cac10:on-the-record/hooks/upstream-defect-scope-guard.sh` `operative_cwd()` (now returns `(target, bool)`).

Considered, and rejected: flipping the unresolvable-origin fallback to
deny unconditionally regardless of who chose the directory. Rejected
per the send-back's explicit instruction — this would deny ordinary
harness-cwd resolution failures that predate #2669 and have nothing to
do with a session's `cd` choice, trading a fixed bypass for a new false
denial of legitimate sessions whose harness workspace happens not to be
a resolvable git checkout (e.g., very first Bash call before any git
state exists).

Considered, and rejected: chasing the harness-cwd-mutation variant the
blind adversarial review surfaced into a code fix — e.g. snapshotting
the harness cwd's origin at session start and refusing to trust a live
re-read. Rejected for the same reason issue #2637's precedent (cited by
PR #2700, still applicable) gives: no path/git-derived resolution
decided from session-reported or session-mutable local state before the
write can be made fully unsteerable, and this send-back's own
acceptance scope is specifically the `cd`-target steerability PR #2703
flagged, not a general hardening sweep over every fail-open branch the
guard has ever had. Pinning it as a disclosed `expectedFailure` test
(same posture as the already-pinned spoofed-origin gap) resolves the
"undisclosed" problem without an open-ended resolution-scheme redesign
this task didn't ask for.
derived: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_harness_cwd_origin_removed_bypass_should_be_denied -v` — result: `XFAIL`.

## What did not work

None — the fix landed on the first attempt at the narrowing itself. The
one thing that needed correcting was a docstring overclaiming safety
(caught by the blind adversarial-review pass before landing, not by a
failed attempt at the fix); it never shipped in a merged PR, so it is
fixed in this same commit rather than logged as a deviation.
canonical: `338cac10:on-the-record/hooks/upstream-defect-scope-guard.sh` `in_scope()` docstring (corrected wording).

## Upstream basis

- PR #2700: first fix attempt for issue #2669, superseded by this
  commit's changes to the same file.
  canonical: `gh pr view 2700 --json state,headRefName` — result: `{"headRefName":"issue-2669/secure-coding-authorization-access-control+silent-failure-audit-604a6e6b","state":"OPEN"}`.
- PR #2703: independent adversarial verification of PR #2700 that found
  the critical fail-open bypass this record closes, and the `timeout=`
  gap this record also fixes. The send-back text quoted in this
  session's spawn prompt is PR #2703's own findings.
  canonical: `gh pr view 2703 --json state,mergedAt` — result: `{"mergedAt":"2026-08-29T07:39:06Z","state":"MERGED"}`.
- docs/issue-2637/reports/silent-failure-audit+architecture-interface-
  contract-shape-149dabd2.md — precedent this record's "pin as
  expectedFailure rather than chase further" framing follows for the
  harness-cwd-mutation gap, same as PR #2700 followed it for the
  spoofed-origin gap.
- `338cac10:on-the-record/hooks/upstream-defect-scope-guard.sh` — the
  file this fix lives in.
- `338cac10:test/test_upstream_defect_scope_guard_cross_repo_cwd.py` —
  demonstrates the closed bypass, the preserved legitimate-case
  fail-open, and both pinned residual gaps.
  derived: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v` — result: `7 passed, 2 xfailed in 0.85s`.

## Open findings

- Residual gap, not closed by this fix, inherited from PR #2700's own
  disclosed scope (issue #2637's precedent: no path/git-derived
  resolution decided from session-reported strings before the write can
  be made fully unsteerable): a session can fabricate a throwaway
  checkout with a spoofed `origin` remote pointed at the target repo and
  `cd` into it, with zero real relationship to that repo. Pinned live as
  `test_spoofed_origin_remote_bypass_should_be_denied`
  (`@unittest.expectedFailure`), untouched by this commit.
  derived: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_spoofed_origin_remote_bypass_should_be_denied -v` — result: `XFAIL`.
- New residual gap, same class, surfaced by this session's own blind
  adversarial-review pass (not by PR #2703): the harness's own payload
  cwd is a real checkout the session has ordinary write access to. A
  session that runs `git remote remove origin` there in an earlier call
  makes a later bare (no-`cd`) `gh pr create` call fail open for any
  target, via the pre-#2669 harness-cwd fallback this fix deliberately
  keeps failing open (per the send-back's own scoping). Pinned live as
  `test_harness_cwd_origin_removed_bypass_should_be_denied`
  (`@unittest.expectedFailure`) rather than left as an inaccurate "can't
  happen" claim in the code comment.
  derived: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_harness_cwd_origin_removed_bypass_should_be_denied -v` — result: `XFAIL`.
- Coverage limit, inherited unchanged from PR #2700 (confirmed by PR
  #2703 as disclosed and non-blocking): `operative_cwd()` only matches a
  single leading `cd <dir> &&`/`cd <dir>;`. `pushd <dir> && ...`, a
  subshell `(cd <dir> && gh pr create ...)`, or a second chained `cd`
  still resolve against the payload cwd, so those call shapes fall back
  to the pre-#2669 denial even for a genuinely legitimate second-repo
  checkout. Not fixed here — same as PR #2700, the reported case and
  the Acceptance's own check-3 construction are both the
  single-leading-`cd` shape.
- Minor, non-blocking, not fixed (fails closed, not a bypass; found by
  the blind adversarial-review pass): a *relative* `cd <relpath> && ...`
  resolves against the payload cwd, which can be stale if the session
  `cd`'d in an earlier, separate Bash call — this can produce a false
  denial of a legitimate cross-repo PR when a relative path is used
  after a prior `cd`, not an incorrect allow. Left as-is; absolute `cd`
  targets are unaffected and are what both this fix's and PR #2700's
  own tests use.

## Next steps

None — delivered per the build-now bypass (CORE_BUILD_NOW=1, contract
v3 s19a); this record accompanies the delivery PR.

skill-verdict: secure-coding-authorization-access-control — applied: invoked; loaded via the Skill tool this session. Rule 1 (deny by default when no explicit rule matches) is the direct frame for the bug being fixed: the guard's `in_scope()` fell through to `return False` (allow) whenever origin was unresolvable, regardless of why — a permit-by-omission default. This fix narrows that omission to only the case the fallback was originally designed for (harness cwd), converting the session-chosen-directory case from permit-by-omission to deny. Rule 7 (multi-entry-path parity) was re-checked against the inherited pushd/subshell/chained-`cd` gap (see Open findings); left as-is since it's already disclosed and non-blocking per the send-back, not newly discovered here. canonical: `338cac10:on-the-record/hooks/upstream-defect-scope-guard.sh` `in_scope()` (the `target_repo is not None` branch).
skill-verdict: adversarial-review — applied: invoked; ran the actual two-party protocol (not a same-session self-critique) on this fix's own diff before landing — spawned a fresh subagent given only `/tmp/fix.diff` (the unified diff of the two changed files), no issue number, no builder framing, no claim about what the diff was supposed to do, instructed to find everything wrong with it per the skill's Step 2-3 evaluator prompt. It returned six findings; one (the harness-cwd-mutation fail-open) was real, undisclosed, and is now fixed and disclosed above; the other five were either already-known/disclosed gaps (spoofed origin, pushd/subshell coverage) or non-blocking fail-closed/hygiene items not worth expanding this send-back's scope for. canonical: subagent transcript, agentId `a3ef09608713b98a9`, finding titled "the 'safe' fail-open branch is not actually session-unsteerable".
