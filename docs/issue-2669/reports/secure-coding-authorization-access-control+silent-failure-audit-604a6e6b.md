---
issue: 2669
role: secure-coding-authorization-access-control+silent-failure-audit-604a6e6b
author: secure-coding-authorization-access-control+silent-failure-audit-604a6e6b
skills: secure-coding-authorization-access-control (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
code_under_review: 074573f679d3887b365d976b3483524d83d578f4
type: fix
breaking: false
verdict: narrowed-with-named-residual-gap
upstream:
  - path: on-the-record/hooks/upstream-defect-scope-guard.sh
    sha: 074573f679d3887b365d976b3483524d83d578f4
  - path: test/test_upstream_defect_scope_guard_cross_repo_cwd.py
    sha: 074573f679d3887b365d976b3483524d83d578f4
---

# issue-2669 — secure-coding-authorization-access-control+silent-failure-audit-604a6e6b record

## What was done

Changed `on-the-record/hooks/upstream-defect-scope-guard.sh`'s `origin_repo()`
so it resolves "this session's own git origin repo" from the directory a
guarded command actually runs in, not only from the PreToolUse payload's
`cwd` field. A new `operative_cwd()` parses a leading `cd <dir> &&`/`cd
<dir>;` off the command text (resolved against the payload cwd when
relative) and, when present, runs `git remote get-url origin` there
instead of at the payload cwd. No other branch of the guard changed —
the channel-role signal (a), the `--repo`/`GH_REPO`/`repos/…/pulls`
extraction, and the deny messages are untouched.
canonical: `074573f6:on-the-record/hooks/upstream-defect-scope-guard.sh` diff.

Added `test/test_upstream_defect_scope_guard_cross_repo_cwd.py`, which
runs the real shipped hook via a real PreToolUse JSON payload on stdin
against real local git checkouts (same harness shape as
`test/test_deliverable_guard_priorities_shard.py`), covering:
- the legitimate cross-repo case now allowed (`cd <repo-B-checkout> &&
  gh pr create --repo owner/repo-B`, from a payload cwd rooted in repo A)
- the same call *without* the `cd` still denied, proving the cwd
  disagreement is real and the guard is now reading the `cd`-resolved
  directory rather than always the payload cwd
- the case the guard was written for (a repo the session has no real
  checkout of at all) still denied, both from repo A's payload cwd and
  from inside repo B's checkout
- one `expectedFailure`-pinned residual gap (see Open findings)

derived: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v` — result: `4 passed, 1 xfailed in 0.84s` (all four acceptance-facing cases green, the pinned gap correctly xfails).

## Why

The bug (issue #2669, reported live in #2600's env-var slice, PR
`79983f8`/tokenmaxxxer-core#347) is that `origin_repo()` read only
`e.get("cwd")` — the harness's fixed per-session workspace directory —
which does not track a `cd` the guarded command itself performs (Bash
tool cwd persists across separate tool-call invocations, but the
PreToolUse hook payload's own `cwd` field does not follow it). A session
legitimately delivering to a second repo it has a genuine local checkout
of was denied regardless of `cd`-ing there first, because origin was
always resolved against the first (harness) repo.

Before writing a fix, I worked out whether an unsteerable signal for
"this issue legitimately spans repo B" exists at all, per the task's own
framing and issue #2637's precedent (a git-root-walk resolution for
`deliverable-guard.sh` went through three fix attempts before the
consult concluded no path-shaped resolution decided from session-
reported strings before the write can be made unsteerable, and the gap
was pinned as `expectedFailure` tests rather than chased further).
Candidates I checked and rejected:
- **roster/lease `work` field** (`spawn.py`'s `_roster_target_repos`,
  used by the multi-repo board sweep): rejected — a role session can
  itself call `spawn.py watch -C <any-dir>` to register a roster entry,
  so the roster's `work` field is session-writable, not harness-only.
  canonical: `watchdog.py:826-838` (`_roster_target_repos`, dedups the
  `work` field roster entries were registered with).
- **a persisted spawn-time issue-resolution cache** (`issue_data` /
  `resolved_repo` in `spawn.py`, the source of this session's own
  "해석된 레포/이슈" line): rejected.
  derived: `grep -n "issue_data\b" spawn.py directive_assembly.py` and
  `grep -n "해석된" spawn.py` — result: `resolved_line` (spawn.py:3202,
  3636) only ever formats that string into spawn-time stdout/prompt
  text; no write to a file under the workspace that a hook could
  re-read at execution time.
- **a live `gh issue view` fetch of the issue body inside the hook**,
  parsing it for a named second repo: the issue body itself genuinely
  is unsteerable (user-authored, contract-enforced — role sessions
  cannot author or edit issues), but the hook has no reliable unsteerable
  way to learn *which issue number* it is running under.
  derived: `printenv | grep -iE "issue|CLAUDE_"` — result: no
  `CLAUDE_ISSUE`-shaped variable present (only `CLAUDE_ROLE`,
  `CLAUDE_CODE_*`, `CLAUDE_PID`, `CLAUDE_EFFORT`, `CLAUDE_PLUGIN_ROOT_CORE`
  — none carry the issue number). A live network call on every Bash
  invocation is also a cost/latency regression this fix does not need
  to take on for what the issue actually asks.

Given none of those hold up, I chose the narrower fix: resolve origin
from the directory the command actually runs in (verified on disk via a
real `git remote get-url origin`, not a string the session merely
asserts), which fixes the reported false-denial without widening the
guard to allow any `--repo` target. This is real forward progress — it
is not "trust anything the session claims about itself," it is "verify
the real git configuration of a real local checkout" — but it inherits
the same class of residual gap #2637 already named, since a session can
fabricate a throwaway checkout with a spoofed `origin` remote. Rather
than iterate a fourth resolution scheme against that (which #2637's
consult already concluded doesn't converge), I pinned it as one
`expectedFailure` test, per that round's own precedent.

Rejected alternative: rebinding the second checkout's own `origin`
remote to the target repo and omitting `--repo` from the `gh pr create`
call, so `gh` auto-detects the target and the guard's `--repo`/`GH_REPO`
extraction never fires at all (`in_scope(None)` is `False` off the
channel-role path). This is the workaround multiple prior sessions
already used live — rejected as the *fix* here because it is a
session-side workaround that happens to dodge the extraction regex, not
a guard behavior change; it does nothing for a call that legitimately
does carry an explicit `--repo` flag (the shape #2669's Acceptance
actually exercises), and it requires mutating the checkout's git config
rather than the guard correctly reading it as-is.
canonical: `docs/reports/deviation-log.md:81,83,84,86,87` (the prior
live denials on #1884/#1907/#1912/#1917/#1921, and the origin-rebind
workaround #1917/#1921 used).

## What did not work

None.

## Upstream basis

- `074573f6:on-the-record/hooks/upstream-defect-scope-guard.sh` — the
  file this fix and its updated header comments live in.
- `074573f6:test/test_upstream_defect_scope_guard_cross_repo_cwd.py` —
  live demonstration of both acceptance directions plus the pinned
  residual gap.
- docs/issue-2637/reports/silent-failure-audit+architecture-interface-
  contract-shape-149dabd2.md — precedent this record's residual-gap
  framing and `expectedFailure` pinning follow directly.
- docs/reports/deviation-log.md:81,83,84,86,87 — the prior live denials
  (#1884/#1907/#1912/#1917/#1921) and the origin-rebind workaround this
  record's Rationale evaluates and rejects as the fix.

## Open findings

- Residual gap, not closed by this fix and not expected to be closable
  by any path/git-derived resolution decided from session-reported
  strings before the write (per #2637's consult): a session can `git
  init` a throwaway directory, `git remote add origin <target-url>`,
  and `cd` into it before the `gh pr create` call, making `ORIGIN_REPO`
  report the target repo with zero real relationship to it. Pinned live
  as `test_spoofed_origin_remote_bypass_should_be_denied`
  (`@unittest.expectedFailure`) in
  `074573f6:test/test_upstream_defect_scope_guard_cross_repo_cwd.py`
  rather than left silently uncovered.
  derived: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_spoofed_origin_remote_bypass_should_be_denied -v` — result: `XFAIL` (confirmed still open, not accidentally closed by this fix).
  No further resolution path is proposed here; closing it would need a
  signal outside what a PreToolUse Bash hook can observe about
  session-mutable filesystem state (e.g. an orchestrator-attested repo
  allowlist recorded outside the session's own write access — out of
  scope for this issue).
- Coverage limit surfaced by re-reading secure-coding-authorization-
  access-control rule 7 (multi-entry-path parity) after actually
  invoking the skill (see deviation log entry
  `20260829T071518840485-c7642d9bf3bcd4eb.md`): `operative_cwd()` only
  matches a single leading `cd <dir> &&`/`cd <dir>;`. `pushd <dir> &&
  ...`, a subshell `(cd <dir> && gh pr create ...)`, or a second chained
  `cd` all still resolve against the payload cwd, so those call shapes
  do not get the fix even for a genuinely legitimate second-repo
  checkout — they fall back to the pre-#2669 denial. Not fixed here
  (the reported case, and the Acceptance's own check-3 construction, are
  both the single-leading-`cd` shape); left as a known narrower-than-
  ideal coverage boundary rather than claimed as fully general.
  derived: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v` — result: 4 passed, 1 xfailed — none of the passing cases exercise `pushd`/subshell/chained-`cd` shapes, confirming they are genuinely untested, not incidentally covered.

## Next steps

None — delivered per the build-now bypass (CORE_BUILD_NOW=1, contract
v3 s19a); this record accompanies the delivery PR.

skill-verdict: secure-coding-authorization-access-control — applied: invoked; loaded via the Skill tool this session, correcting an invoke-before-apply miss (the lines below this note originally claimed "invoked" before the Skill tool was ever called — see deviation log entry `20260829T071518840485-c7642d9bf3bcd4eb.md`). canonical: `on-the-record/hooks/upstream-defect-scope-guard.sh` `in_scope()` (lines defining the `target_repo is not None and ORIGIN_REPO is not None` gate). Re-checked the delivered fix against rule 7 (an endpoint reachable through more than one entry path must get the same check on every path) — a `--repo` PR-creation call is reachable through a bare command, a `cd &&`-prefixed one, a `pushd`-prefixed one, or a subshell, and `operative_cwd()` gives parity only for the single-leading-`cd` shape; recorded above as a new Open finding rather than left unnoticed. Rule 1 (deny by default when no rule matches) is in tension with the guard's pre-existing fail-open posture on unresolvable origin — not introduced by this fix, out of scope here, noted for completeness.
skill-verdict: silent-failure-audit — applied: invoked; loaded via the Skill tool this session (same correction, deviation-log entry cited above). Re-classified `origin_repo()`/`operative_cwd()`'s failure paths under the skill's own H/S/U taxonomy: `origin_repo()`'s three failure modes (subprocess error, non-zero `git remote` exit, unparseable URL) are Handled — they propagate to `in_scope()`'s documented fail-open branch, not silently absorbed into a wrong allow/deny with no trace; `operative_cwd()`'s no-match path is also Handled — it falls back to the payload cwd rather than raising or defaulting to a silently-wrong directory. No Silently-Absorbed sites found in the changed code. derived: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_same_call_without_cd_still_denied test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_unrelated_upstream_repo_still_denied -v` — result: 2 passed.
