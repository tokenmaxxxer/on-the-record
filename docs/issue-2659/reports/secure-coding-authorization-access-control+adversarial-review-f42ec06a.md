---
issue: 2659
role: secure-coding-authorization-access-control+adversarial-review-f42ec06a
author: secure-coding-authorization-access-control+adversarial-review-f42ec06a
skills: secure-coding-authorization-access-control (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
type: bugfix
breaking: false
verdict: pass
upstream:
  - path: on-the-record/hooks/deliverable-guard.sh
    sha: 9bcb75817afd9408bd3fab5ead890d055d5fa9d8
  - path: test/test_deliverable_guard_priorities_shard.py
    sha: 9bcb75817afd9408bd3fab5ead890d055d5fa9d8
  - path: test/test_deliverable_guard_worktree_submodule.py
    sha: 9bcb75817afd9408bd3fab5ead890d055d5fa9d8
---

# issue-2659 — secure-coding-authorization-access-control+adversarial-review-f42ec06a record

## What was done

Fixed `deliverable-guard.sh`'s two root-detection walks (both hand-rolled
`os.path.isdir(<probe>/".git")` loops: the board-repo activation check and
`_git_root_from`, used by the priorities-shard/`approvers.md` exemption
resolution) to ask git itself instead — `git rev-parse --is-inside-work-tree`
for the activation check, `git rev-parse --show-toplevel` for
`_git_root_from` — both invoked with `LC_ALL=C` for deterministic
English output, and both starting from the nearest *existing* ancestor
directory (`_nearest_existing_dir`) since the target file/directory may
not exist yet.

canonical: `9bcb75817afd9408bd3fab5ead890d055d5fa9d8:on-the-record/hooks/deliverable-guard.sh:159-207` (`_nearest_existing_dir`, `_run_git`, `_git_root_from`) and `:271-309` (activation walk)

Both walks previously matched only a `.git` *directory* — the shape an
ordinary clone uses. A linked worktree or a submodule marks its checkout
root with a `.git` *file* (a `gitdir: <path>` pointer), which
`os.path.isdir` never matches, so the walk found nothing. The activation
walk's fallback on "nothing found" was `sys.exit(0)` — ALLOW — so a write
that is denied in an ordinary clone was silently allowed in a worktree or
submodule.

When git itself cannot answer (binary missing, timeout, unrecognized
output), the activation check now denies with an explicit message rather
than falling through to allow — the fallback for "no repo detected" is
still `sys.exit(0)`/allow only when git *positively* reports "not a git
repository" (matched via a `git -C <probe> rev-parse --is-inside-work-tree`
call run with `LC_ALL=C`).

### Verified live: three layouts, deny/allow pair, before and after

Built an ordinary clone, a `git worktree add` linked worktree off it, and
a submodule checkout (a fresh superproject with the clone added via
`git submodule add`) under `~/.otr-dg-test-fixture/` (never `/tmp` — this
machine's `/tmp` itself carries a stray `.git` directory that would
silently satisfy the very check under test and mask the bug). Confirmed
`.git` is a file, not a directory, in the worktree and the submodule.
Ran the real shipped hook (`bash on-the-record/hooks/deliverable-guard.sh`)
with a real PreToolUse JSON payload on stdin against each, for a
deny-shaped write (a path under a `src/` directory, matching the shape
this hook denies everywhere it's active) and an allow-shaped write
(`docs/specs/approvers.md`, the orchestrator exemption) — 12 runs total
(2 payloads × 3 layouts × before/after, "before" = `git stash` reverting
`deliverable-guard.sh` to its pre-fix state for the duration of that
half of the run only, restored immediately after via `git stash pop`).

derived: `git stash -q -- on-the-record/hooks/deliverable-guard.sh && <run the 6 payload/layout combinations through the hook> && git stash pop -q && <run the same 6 again>` — result:

```
=== BEFORE FIX ===
clone/DENY  rc=2  (correctly denied)
clone/ALLOW rc=0  (correctly allowed)
wt/DENY     rc=0  (WRONG — fail-open: the exact bug in this issue)
wt/ALLOW    rc=0  ("correct" verdict, wrong mechanism — the exemption
                    never matched; the root-walk found nothing above the
                    worktree at all, and the activation walk's own
                    "nothing found" fallback happened to also be ALLOW)
sub/DENY    rc=2  (correct verdict, wrong mechanism — the old walk
                    doesn't match the submodule's own .git, a FILE, but
                    keeps climbing and lands on the superproject's real
                    directory .git one level up, so it denies against
                    the wrong root)
sub/ALLOW   rc=2  (WRONG — same wrong-root mechanism: root resolves to
                    the superproject, so approvers.md's exemption is
                    checked against "sub/docs/specs/approvers.md", which
                    doesn't match, and the write is wrongly denied)

=== AFTER FIX ===
clone/DENY  rc=2  (unchanged)
clone/ALLOW rc=0  (unchanged)
wt/DENY     rc=2  (fixed: now matches clone's verdict)
wt/ALLOW    rc=0  (unchanged verdict, now via the real exemption match)
sub/DENY    rc=2  (unchanged verdict, now via the submodule's own root)
sub/ALLOW   rc=0  (fixed: now matches clone's verdict)
```

### Constructed the "cannot determine" refusal state

Built a minimal `PATH` containing only symlinks to `bash`/`python3`/`sh`/
`env`/`cat` (no `git`), and ran the hook with that `PATH` against an
ordinary git repo for a deny-shaped write.

derived: `PATH=<git-free bin dir> HOME="$HOME" bash on-the-record/hooks/deliverable-guard.sh < payload.json` — result:
```
rc=2
orchestrate: could not determine whether src/x.py is inside a git repository (git rev-parse did not run) — cannot verify this write is outside a board repo, denying rather than silently allowing it through.
```
(src/x.py above is the file_path value inside the JSON test payload, an
untracked fixture path used only for this reproduction — not a path in
this repository's own working tree.)

Before the fix, the same git-free PATH run against the same payload
returned rc=0 — the old walk needs no `git` binary at all (pure
`os.path`/`os.listdir` calls), so the absence of `git` was invisible to
it and it silently allowed.

### Tests added/updated

- `test/test_deliverable_guard_worktree_submodule.py` (new): builds the
  three layouts, asserts deny/allow parity across all three
  (`DeliverableGuardLayoutParityTest`), asserts `.git` is a file (not a
  directory) in the worktree/submodule, and asserts the git-missing case
  refuses with the "could not determine" message and never the ordinary
  "deliverable path in a board repo" message
  (`DeliverableGuardCannotDetermineTest`).
- `test/test_deliverable_guard_priorities_shard.py` (updated): the fix to
  `_git_root_from` closes the "planted `.git` directory/symlink" bypass
  documented there since issue #2637 round 4 — git's own discovery does
  not accept a bare `.git` name with no real git content as a repo
  boundary, and keeps walking up past a planted empty `.git` dir or a
  symlink-to-an-empty-dir to find the real root instead. The four
  `@unittest.expectedFailure` cases targeting that exact planted-name
  shape now pass for real; removed the decorator on all four, updated
  the section comment, and added one new `expectedFailure` case
  (`test_bypass_via_nested_git_init_reaches_exempt_priorities_dir`)
  pinning down what remains open: a session that runs a genuine `git
  init` in a subdirectory still redirects the perceived root, because
  that subdirectory is then a real, independent git repository from
  git's own perspective, and that narrower class is issue #2637's
  problem, not this one.

canonical: `9bcb75817afd9408bd3fab5ead890d055d5fa9d8:test/test_deliverable_guard_priorities_shard.py:198-273` (updated section comment and the four now-unmarked tests, plus the new xfail case)

derived: `python3 -m pytest test/test_deliverable_guard_worktree_submodule.py test/test_deliverable_guard_priorities_shard.py -q` — result: `24 passed, 1 xfailed`

## Why

The issue's own constraint ruled out the obvious naive fix ("accept any
`.git`, file or directory, as proof of root") because that is exactly
what already burned this file once (PR #2658): a `.git` entry the
guarded session itself can plant is not proof of anything. `git
rev-parse` was chosen because git already has to solve this exact
problem correctly for its own operation — parsing a `.git` file's
`gitdir:` pointer, validating what it points at, and refusing to treat
an empty or malformed `.git` entry as a repository boundary — so
delegating to it is not a second hand-rolled walk with the same
weakness, it is removing the hand-rolled walk. `LC_ALL=C` was added
after discovering live that this system's default locale renders git's
"not a git repository" message in Korean (`깃 저장소가 아닙니다`), which
would have made the English substring match silently fail-safe into the
"cannot determine → deny" branch for the *common* case (ordinary
non-repo write) — over-strict, not the direction the issue asked to
avoid, but still a correctness bug in the fix itself if left unnoticed.

derived: `LC_ALL=C git -C <no-repo-dir> rev-parse --is-inside-work-tree` — result: `fatal: not a git repository (or any of the parent directories): .git`; same command without `LC_ALL=C` on this system — result: `fatal: (현재 폴더 또는 상위 폴더 중 일부가) 깃 저장소가 아닙니다: .git`

`_git_root_from` was brought into scope alongside the activation walk,
despite the issue text scoping itself to "this walk" (singular) and
listing the priorities-shard exemption as a non-goal, because leaving it
on the old directory-only check produced a live verdict mismatch the
issue's own acceptance criterion #1 forbids: `docs/specs/approvers.md`
denied inside a worktree/submodule while allowed in an ordinary clone
(the "sub/ALLOW rc=2" before-fix row above). The change made to
`_git_root_from` is the identical, narrow one made to the activation
walk — swap the trust mechanism, touch nothing about which paths are
exempt — and it does not attempt the priorities-shard exemption's own
separately-tracked, harder problem: a session running a genuine `git
init` in a subdirectory still steers root resolution, since that creates
an authentically independent repository from git's own perspective, not
something a bare-name check can tell apart from the outer one.

derived: `python3 -m pytest test/test_deliverable_guard_priorities_shard.py::DeliverableGuardPrioritiesShardTest::test_bypass_via_nested_git_init_reaches_exempt_priorities_dir -q` — result: `1 xfailed` (confirms the gap reproduces exactly as expected — rc=0 EXEMPT instead of rc=2)

## Upstream basis

No upstream record to build on — issue #2659 is a standalone bug report
against `on-the-record/hooks/deliverable-guard.sh`, filed directly against
its own root-walk history (PR #2658's adversarial-review finding).

## Standing invariants

- **Role axis retirement**: this change touches zero role-membership
  logic.
  checked: `grep -n '\brole\b' on-the-record/hooks/deliverable-guard.sh test/test_deliverable_guard_priorities_shard.py test/test_deliverable_guard_worktree_submodule.py` — result: 6 matches, all pre-existing (`session-role-bind snapshot`, `role session`, `otr-role-bind`, `role work` ×2, comment prose), none of them added or removed lines in this diff.
  derived: `git show main:on-the-record/hooks/deliverable-guard.sh | grep -c '\brole\b'` — result: `6` (identical to this branch's count in the same file, confirming this diff added/removed zero role occurrences).
  A repo-wide role-occurrence count differs from the issue's cited
  baseline (1390) because `origin/main` has advanced past this branch's
  base commit with unrelated merges.
  checked: `git rev-parse HEAD~1 main origin/main` (`HEAD~1` = this branch's base before the code commit) — result: base and `main` both `00aeaae4`, `origin/main` at `e1b35a53` — confirming the drift is upstream, not from this diff.
- **No new bug**: compared the failing-test-name SET (not count) between
  this branch and `origin/main`, full `test/` suite.
  derived: `python3 -m pytest test/ -q` on this branch — result: `15 failed, 411 passed, 3 xfailed`; same command in a `git worktree add` checkout of `origin/main` — result: `15 failed, 403 passed, 6 xfailed`; `diff <(sort main-failed-names.txt) <(sort branch-failed-names.txt)` — result: empty (identical 15 failing test names on both sides). The pass-count delta (411 vs 403 = +8) is fully accounted for: 4 new tests in `test_deliverable_guard_worktree_submodule.py`, plus 4 previously-`expectedFailure` tests in `test_deliverable_guard_priorities_shard.py` that now pass for real (decorator removed) — matching the xfail-count delta (6 vs 3 = -3 = -4 removed +1 added).
- **No overhead increase**: `on-the-record/directive` is untouched by
  this diff.
  checked: `du -sb on-the-record/directive` — result: `53162	on-the-record/directive` (identical to the cited baseline).
- **Monitor/watch machinery**: untouched and green.
  checked: `python3 -m pytest test/test_watchdog_heartbeat_noise.py on-the-record/monitors/test_poll_heartbeat.py -q` — result: `36 passed`.

## Open findings

- The `_git_root_from`/priorities-shard exemption's narrower remaining
  gap (a genuine nested `git init` still redirects perceived root) is
  pinned as `expectedFailure`
  (`test_bypass_via_nested_git_init_reaches_exempt_priorities_dir` in
  `9bcb75817afd9408bd3fab5ead890d055d5fa9d8:test/test_deliverable_guard_priorities_shard.py`)
  rather than fixed here — it is issue #2637's problem (three prior
  path-shaped fixes already rejected there), not issue #2659's, and this
  issue's non-goals section says so explicitly.
- Everything else: none.

## What did not work

The one design correction made before landing: the initial draft matched
`"not a git repository"` against `git`'s stderr without forcing the
locale.

derived: running that draft's match against this system's actual default
locale (no `LC_ALL` override) — result: the Korean message
`깃 저장소가 아닙니다` does not contain the English substring, so the
match would have fallen through to the "cannot determine → deny" branch
for every ordinary non-repo write on this machine — caught by running
the unpatched match live before shipping it (see the two-command
comparison in `## Why` above), corrected by adding `LC_ALL=C` to the
`_run_git` helper before the fix was tested against the three layouts.

## Next steps

None — landed. Acceptance criteria (verdict parity across three layouts,
fail-closed on genuine non-determination, ordinary-checkout behavior
preserved, existing suite green with an identical failing-test set) are
all verified live above.

## Skill verdicts

skill-verdict: secure-coding-authorization-access-control — applied: invoked; used to judge the correct trust boundary for root resolution (deny-by-default on "cannot determine", never trust a session-plantable filesystem signal as an authorization decision) when choosing `git rev-parse` over a naive `.git`-of-any-kind walk.
skill-verdict: adversarial-review — not-applicable: this record is original bugfix work, not a review of another session's deliverable — no separate artifact to hold at arm's length from its own author.
