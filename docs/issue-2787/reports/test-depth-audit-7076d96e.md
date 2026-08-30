---
issue: 2787
role: test-depth-audit-7076d96e
author: test-depth-audit-7076d96e
skills: test-depth-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: test/test_upstream_defect_scope_guard_cross_repo_cwd.py
    sha: dc48170d6c3c428ee970768207f0367401efda91
  - path: docs/issue-2755/reports/independent-verification-1.md
    sha: same-commit
  - path: docs/issue-2755/reports/independent-verification-2.md
    sha: same-commit
  - path: on-the-record/hooks/deliverable-guard.sh
    sha: fbe218cc1067837cd58e6c941998a89cd34a0163
---

# issue-2787 — test-depth-audit-7076d96e record

## What was done

Added message-content assertions to the `deliverable-guard.sh` denial
tests in `test/test_deliverable_guard_worktree_submodule.py` and
`test/test_deliverable_guard_priorities_shard.py` that previously
asserted `returncode == 2` alone.

**Population, re-derived directly, not inherited from PR #2781's own
record:**
canonical: this session's own command, run directly against this
checkout —
```
derived: grep -n "returncode, 2" test/test_deliverable_guard_worktree_submodule.py test/test_deliverable_guard_priorities_shard.py | wc -l
16
```
Of those 16 raw `returncode, 2` hits, canonical: reading
`test_deliverable_guard_worktree_submodule.py:144-159` directly —
`test_missing_git_binary_refuses_with_explanation` already carries its
own content checks (`assertIn("could not determine", ...)` /
`assertNotIn("deliverable path in a board repo", ...)`) and needed no
change. The other 15 had no content check anywhere in their method body —
canonical: this session read every one of the 15 test method bodies
directly (not grepped) in both files before editing, specifically to rule
out the false-positive the issue warns about
(`assertEqual(rc, 2, r.stderr)` passing `stderr` only as the failure
*message*, never evaluated as content). This reproduces the "1 + 14 = 15"
count from `docs/issue-2755/reports/independent-verification-1.md` and
`docs/issue-2755/reports/independent-verification-2.md` (both
`same-commit` in this checkout's history, see frontmatter) a third time.
Per those two records' own "Open findings" sections, the "delivering
record undercounted one file by one" issue #2787 references is an
undercount in PR #2781's record *prose* (it names only 1 of
`test_deliverable_guard_worktree_submodule.py`'s 2 raw hits), not in its
final 15-unchecked total — this session's own re-derivation above
confirms the total, independent of that prose.

**The fix.** Added a module-level helper to each file (each stays
self-contained — neither previously imported from the other or from
`test_upstream_defect_scope_guard_cross_repo_cwd.py`):
```python
def _assert_denied_as_deliverable_path(test_case, result):
    test_case.assertIn(
        "deliverable path in a board repo", result.stderr, result.stderr)
    test_case.assertNotIn("Traceback", result.stderr, result.stderr)
```
`"deliverable path in a board repo"` is a fragment of
`deliverable-guard.sh`'s own terminal `deny(...)` call. canonical:
reading `on-the-record/hooks/deliverable-guard.sh:357-362` directly —
the fragment is quoted verbatim from the hook's own source, and it is
the same fragment the file already used defensively at
`test_deliverable_guard_worktree_submodule.py:159`
(`assertNotIn("deliverable path in a board repo", r.stderr)`) for a
different scenario. canonical: reading the entire hook
(`on-the-record/hooks/deliverable-guard.sh`, all 368 lines) confirmed all
15 sites reach this one `deny(...)` call, not any of the hook's other
`deny(...)` calls (payload-parsing, missing `cwd`, git-unknown) — so a
single helper suffices; a per-test message helper, which PR #2781's
summary speculated might be needed, is not.

Called `_assert_denied_as_deliverable_path(self, r)` immediately after
each of the 15 existing `self.assertEqual(r.returncode, 2, ...)` lines —
canonical: this session's own post-edit grep —
```
derived: grep -c "_assert_denied_as_deliverable_path(self, r)" test/test_deliverable_guard_worktree_submodule.py test/test_deliverable_guard_priorities_shard.py
test/test_deliverable_guard_worktree_submodule.py:1
test/test_deliverable_guard_priorities_shard.py:14
```
1 + 14 = 15, matching the population above exactly. Sites:
`test/test_deliverable_guard_worktree_submodule.py:112` (inside
`test_deny_shaped_write_denied_in_every_layout`'s `subTest` loop) and
`test/test_deliverable_guard_priorities_shard.py:143,151,162,175,180,189,194,205,215,259,270,287,296,308`
(14 test methods, including
`test_bypass_via_nested_git_init_reaches_exempt_priorities_dir` at line
308 — `@unittest.expectedFailure` left unchanged).

acceptance: `git diff --stat -- test/test_deliverable_guard_worktree_submodule.py test/test_deliverable_guard_priorities_shard.py` — result:
```
 test/test_deliverable_guard_priorities_shard.py   | 24 +++++++++++++++++++++++
 test/test_deliverable_guard_worktree_submodule.py | 11 +++++++++++
 2 files changed, 35 insertions(+)
```
0 deletions — no existing assertion weakened, reordered, or removed; the
return-code check stays, the message check is added on top, per the
issue's "must not" clause.

**Crash-hook proof — replace, show fifteen failing, restore, show them
passing — executed directly in this session, three times over (baseline
/ crash / restore):**

acceptance: `python3 -m pytest test/test_deliverable_guard_worktree_submodule.py test/test_deliverable_guard_priorities_shard.py -v` (baseline, real hook) — result:
```
24 passed, 1 xfailed in 1.16s
```

acceptance: `printf '#!/usr/bin/env bash\nexit 2\n' > on-the-record/hooks/deliverable-guard.sh && python3 -m pytest test/test_deliverable_guard_worktree_submodule.py test/test_deliverable_guard_priorities_shard.py -v` (hook exits the denial code before reaching any policy) — result:
```
23 failed, 1 passed, 1 xfailed in 0.98s
```
The 1 passed is `test_git_file_is_recognized_not_just_git_directory`,
which never invokes the hook — confirmed by canonical: reading
`test_deliverable_guard_worktree_submodule.py:111-116` directly (it only
calls `.is_file()` on fixture paths, no `_run_gate` call). All 14 plain
(non-xfail) sites among the 15 flip to FAILED. The 15th site
(`test_bypass_via_nested_git_init_reaches_exempt_priorities_dir`,
`@expectedFailure`) stays `XFAIL`, not `XPASS`:
acceptance: `python3 -m pytest test/test_deliverable_guard_worktree_submodule.py test/test_deliverable_guard_priorities_shard.py -v 2>&1 | grep -iE "xpass|unexpected success|xfail"` — result:
```
[gw7] [ 32%] XFAIL test/test_deliverable_guard_priorities_shard.py::DeliverableGuardPrioritiesShardTest::test_bypass_via_nested_git_init_reaches_exempt_priorities_dir
```
Zero XPASS / "unexpected success" matches. Before this fix, a crash-hook
would have made this one site XPASS (misreads as "the bug got fixed") —
the same landmine PR #2781 closed for
`test_upstream_defect_scope_guard_cross_repo_cwd.py`'s two
`@expectedFailure` sites; the message check restores the same
discriminating XFAIL-not-XPASS behavior here.

acceptance: `cp <backup> on-the-record/hooks/deliverable-guard.sh && git diff --stat -- on-the-record/hooks/deliverable-guard.sh` — result: empty output (byte-identical restore). Then:
acceptance: `python3 -m pytest test/test_deliverable_guard_worktree_submodule.py test/test_deliverable_guard_priorities_shard.py -v` — result:
```
24 passed, 1 xfailed in 1.24s
```
Identical pass/xfail counts and test names to the pre-crash baseline.

**Sweep — both repos, re-derived directly.**

On-the-record (`test/`):
acceptance: `grep -rn "returncode, 2" test/ | wc -l` — result:
```
34
```
acceptance: `grep -rln "returncode, 2" test/` — result:
```
test/test_deliverable_guard_worktree_submodule.py
test/test_branch_skill_field.py
test/test_upstream_defect_scope_guard_cross_repo_cwd.py
test/test_approval_gate_carriers.py
test/test_deliverable_guard_priorities_shard.py
```
Same 5 files `docs/issue-2755/reports/independent-verification-2.md`
found (that record's `test_branch_role_field.py` was since renamed to
`test_branch_skill_field.py` — canonical: `git log --oneline --all | grep -i "rename 5 test files"` shows commit `6f9b5afa`, "issue-2814: rename 5 test files off the retired role noun", same test count, no content change).
acceptance: `grep -rEln "rc, 2\)|returncode == 2|assertEqual\(2," test/` (broader spelling sweep, to rule out under-counting the narrow literal pattern) — result:
```
test/test_ps_live_reliability.py
```
`test_ps_live_reliability.py` is out of scope — canonical: reading
`test_ps_live_reliability.py:90-134` directly, its `rc == 2` hits call
`board.roster_ps()` in-process, not a hook subprocess (same conclusion
`independent-verification-2.md`'s "Open findings" reached).
acceptance: `grep -rl "hooks/" test/*.py | xargs grep -l "subprocess"` — result:
```
test/test_approval_gate_carriers.py
test/test_auto_approval_shadow_wiring.py
test/test_branch_skill_field.py
test/test_deliverable_guard_priorities_shard.py
test/test_deliverable_guard_worktree_submodule.py
test/test_skill_verdict_guard_zero_invocation_signal.py
test/test_spawn_skills_mount.py
test/test_upstream_defect_scope_guard_cross_repo_cwd.py
```
canonical: reading the returncode/rc usage in the 3 files not already
covered above
(`test_auto_approval_shadow_wiring.py`,
`test_skill_verdict_guard_zero_invocation_signal.py`,
`test_spawn_skills_mount.py`) directly —
```
derived: grep -n "returncode\|\.rc\b\| rc \|rc==" test/test_auto_approval_shadow_wiring.py test/test_skill_verdict_guard_zero_invocation_signal.py test/test_spawn_skills_mount.py
test/test_skill_verdict_guard_zero_invocation_signal.py:108:        self.assertEqual(mounted_unused.returncode, 0, mounted_unused.stderr)
test/test_skill_verdict_guard_zero_invocation_signal.py:109:        self.assertEqual(zero_mounted.returncode, 0, zero_mounted.stderr)
test/test_skill_verdict_guard_zero_invocation_signal.py:126:        self.assertEqual(r.returncode, 0, r.stderr)
test/test_skill_verdict_guard_zero_invocation_signal.py:145:        self.assertEqual(r.returncode, 0, r.stderr)
test/test_skill_verdict_guard_zero_invocation_signal.py:161:        self.assertEqual(r.returncode, 0, r.stderr)
```
All `returncode, 0` (allow checks), not the denial-by-rc-alone shape this
issue is about; the other two files had zero matches. canonical: the two
grep passes above (`returncode, 2` and the broader-spelling sweep) plus
this hooks/subprocess cross-check together are this record's own basis
for "no third hook found in `test/` with the same shape" — no file
outside the 5 named above showed a denial-by-rc-only assertion against a
hook subprocess.

Second repo: a separate local checkout of `tokenmaxxxer/tokenmaxxxer-core`
at `/home/jwjung/tokenmaxxxer-core` — every path cited below from that
checkout is untracked in *this* repository's git history (a different
repo entirely; not reachable from this session's own `git log`/`git
ls-files`).
canonical: `cd /home/jwjung/tokenmaxxxer-core && git rev-parse HEAD` — result:
```
8f9562263f8fe6ae791d3962444d0efcf0aa63de
```
acceptance: `cd /home/jwjung/tokenmaxxxer-core && grep -rln "returncode == 2" tests/ test/` — result (4 files, untracked here):
```
tests/test_ordering_gate_livefire.py
tests/test_silent_failure_repros.py
tests/test_promoted_hooks.py
tests/test_ordering_gates_237.py
```
```
derived: grep -rn "returncode == 2" tests/ | wc -l   (run inside /home/jwjung/tokenmaxxxer-core)
20
```
A dispatched read-only sub-agent pass read every one of these 20 hits'
full test method bodies and traced each to its invoked hook; this
session then independently re-verified (not just trusted) the sub-agent's
key structural claim directly, itself, this turn:
```
canonical: sed -n '38,48p' /home/jwjung/tokenmaxxxer-core/core/hooks/lib/gate-lib.sh   (untracked here, read directly this turn)
gate_trap_fail_closed() {
  trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then
    echo "fail-closed: gate aborted (rc=$rc)" >&2
    exit 2
  fi' EXIT
}
```
```
canonical: sed -n '1,3p' /home/jwjung/tokenmaxxxer-core/core/hooks/trailer-gate.sh   (untracked here, read directly this turn)
#!/usr/bin/env bash
__fc(){ rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then echo "fail-closed: gate aborted (rc=$rc)" >&2; exit 2; fi; }
trap __fc EXIT
```
```
canonical: grep -n "gate_trap_fail_closed" /home/jwjung/tokenmaxxxer-core/warrant/hooks/hunt-guard.sh /home/jwjung/tokenmaxxxer-core/core/hooks/ordering-gate.sh   (untracked here, read directly this turn)
warrant/hooks/hunt-guard.sh:24:gate_trap_fail_closed
core/hooks/ordering-gate.sh:25:gate_trap_fail_closed
```
This confirms `warrant/hooks/hunt-guard.sh` (untracked here),
`core/hooks/ordering-gate.sh` (untracked here, both via the shared
`gate_trap_fail_closed()`), and `core/hooks/trailer-gate.sh` (untracked
here, inlined equivalent, `__fc`/`trap __fc EXIT`) all carry the same
crash-remaps-to-2 trap shape as `deliverable-guard.sh:42` — the same
"hook that crashed on every input keeps the test green" mechanism this
issue is about. See "Open findings" below for which specific test sites,
of the 20, are return-code-only against these hooks.

## Why

The fix reuses the pattern from issue #2755/PR #2781
(`_assert_denied_for_documented_reason`, applied to 7 sites in
`test_upstream_defect_scope_guard_cross_repo_cwd.py` — canonical:
`git show dc48170d --stat` read directly), adapted with a fragment
specific to `deliverable-guard.sh`'s own denial message rather than
reusing the other hook's `"issue #1131 req#4"` string — the two hooks
deny for unrelated reasons and share no message text. Reading the whole
hook (see "What was done" above) confirmed one fragment covers all 15
sites, so a shared cross-file helper or per-call-site parameterization
(more machinery than the situation needs) was not built.

The `@expectedFailure` site
(`test_bypass_via_nested_git_init_reaches_exempt_priorities_dir`) got the
identical treatment as the 2 analogous sites PR #2781 fixed in the other
file, on purpose: that PR's own record already established the reasoning
(a crash-hook flips an `expectedFailure` test from XFAIL to the
misleading XPASS "unexpected success", not to a plain FAILED), and this
session's own crash-hook run above (see "What was done") reproduces the
same XFAIL-not-XPASS outcome, confirming the reused pattern actually
holds for this hook too rather than assuming it by analogy alone.

`assertIn` on a short fragment (not the full stderr, not a regex) keeps
the assertion from over-tightening: a future edit to the hook's
surrounding prose in that `deny()` call would not break these tests,
only a change to the actual verdict class would (verified live: the
crash-hook demonstration above replaced the entire hook body, a far
larger change than a prose edit, and correctly failed all 15; no smaller
prose-only change was tested, since none was made).

## Upstream basis

- `test/test_upstream_defect_scope_guard_cross_repo_cwd.py` @
  `dc48170d6c3c428ee970768207f0367401efda91` — canonical: `git show dc48170d --stat` (PR #2781, merged into this branch's history) — source of the
  `_assert_denied_for_documented_reason` helper pattern this fix adapts.
- `docs/issue-2755/reports/independent-verification-1.md` and `-2.md`
  (`same-commit`, already present in this checkout — canonical: `git
  ls-files docs/issue-2755/reports/` lists both) — both independently
  re-derived the "1 + 14 = 15" population this record's own
  re-derivation above reproduces a third time.
- `on-the-record/hooks/deliverable-guard.sh` @
  `fbe218cc1067837cd58e6c941998a89cd34a0163` — canonical: `git log -1
  --format=%H -- on-the-record/hooks/deliverable-guard.sh` — read in full
  to determine the denial-message fragment; not modified in this
  delivery (only transiently swapped and restored byte-identical for the
  crash-hook demonstration, confirmed by the empty `git diff --stat`
  above).

## Open findings

- `tokenmaxxxer-core`'s `tests/` directory (separate local checkout,
  untracked in this repo — see "What was done" → "Sweep" above, including
  this session's own direct reads of the relevant hook source) has 7
  hook-invoking tests with the same return-code-only-denial shape:
  `tests/test_silent_failure_repros.py:99,106,163,170,177` (untracked
  here; hooks `warrant/hooks/hunt-guard.sh` (untracked here) and
  `core/hooks/trailer-gate.sh` (untracked here), trap shape confirmed
  above under "What was done" → "Sweep") and
  `tests/test_ordering_gates_237.py:99` (untracked here; hook
  `core/hooks/ordering-gate.sh` (untracked here), same trap shape,
  confirmed above). canonical: this session independently read
  `tests/test_ordering_gates_237.py:92-99` (untracked here, the finding)
  against
  `tests/test_ordering_gates_237.py:53-59,124-127,162-165,192-195,230-233,259-262`
  (untracked here, its 6 siblings, all in the same file — `derived: sed -n
  '50,100p;120,135p;160,200p;228,265p' tests/test_ordering_gates_237.py`
  run directly inside `/home/jwjung/tokenmaxxxer-core`, this turn) —
  every sibling test carries a trailing `assert "refused" in proc.stderr`
  immediately after its `assert proc.returncode == 2` line; the one
  finding at line 99 alone lacks it, confirmed by this session's own read,
  not inherited from the sub-agent's report. A structurally-flagged but
  not-currently-exploitable 8th case
  (`tests/test_silent_failure_repros.py:41`'s `has_deny()` helper,
  untracked here) also surfaced from the sub-agent's pass: its
  `returncode == 2` branch is dead code today because the hook it wraps,
  `freelunch/hooks/observe.sh` (untracked here), has no `trap` and always
  exits 0 — deny is signaled via stdout JSON only — so it is noted but
  not counted among the 7 (this specific claim was not independently
  re-verified by this session beyond the sub-agent's report, unlike the
  trap-shape and sibling-test claims above).
  This population is out of this issue's stated Ask (scoped to
  `deliverable-guard.sh`'s own tests in this repo) and lives in a
  different git repository from this session's own write set / branch,
  so it is named, not fixed — the same "flag, don't fix" disposition PR
  #2781 gave these very 15 sites. Resolution path: a follow-up issue
  scoped to `tokenmaxxxer-core`'s `hunt-guard.sh` /
  `trailer-gate.sh` / `ordering-gate.sh` test coverage — left for the
  user to file, per this role's standing instruction not to pick or file
  issues itself.
- None open in `on-the-record`: canonical: the sweep commands and their
  outputs shown above under "What was done" → "Sweep" (the `returncode,
  2` grep, the broader-spelling grep, and the hooks/subprocess
  cross-check) together found no third hook in `test/` with the same
  shape, and the before/after failing-test-name comparison below shows no
  regression from this change.

## Verification / invariants

acceptance: `git diff -- test/test_deliverable_guard_worktree_submodule.py test/test_deliverable_guard_priorities_shard.py | grep -iE "\brole\b"` (no return of the retired role axis) — result: no matches (empty output).

acceptance: no-new-bug check, failing-test set vs a stashed (pre-change) tree, compared as SETS OF NAMES —
```
git stash push -u -- test/test_deliverable_guard_worktree_submodule.py test/test_deliverable_guard_priorities_shard.py
python3 -m pytest test/ -q 2>&1 | grep "^FAILED" | sort > baseline.txt
git stash pop
python3 -m pytest test/ -q 2>&1 | grep "^FAILED" | sort > withfix.txt
diff baseline.txt withfix.txt
```
result:
```
15 failed, 425 passed, 3 xfailed   (both runs, identical count)
(diff: no output — identical 15-name sets before and after this change)
```
canonical: neither `test_deliverable_guard_worktree_submodule.py` nor
`test_deliverable_guard_priorities_shard.py` appears among the 15
`FAILED` lines in either run (both files are listed in full above, under
"What was done" → "Sweep") — all 15 are pre-existing failures unrelated
to `deliverable-guard.sh`.

acceptance: `git diff --shortstat -- test/test_deliverable_guard_worktree_submodule.py test/test_deliverable_guard_priorities_shard.py` (no overhead increase) — result:
```
2 files changed, 35 insertions(+)
```
0 deletions — a fixed, small, additive assertion cost per test (one
`assertIn` + one `assertNotIn` against an already-captured
`result.stderr`), no new subprocess calls, no new fixtures, no loop
added.

acceptance: `python3 -m pytest test/test_watchdog_heartbeat_noise.py on-the-record/monitors/test_poll_heartbeat.py -v` (monitor and watch machinery unbroken and not quieter) — result:
```
36 passed in 2.80s
```
canonical: neither `watchdog.py` nor anything under
`on-the-record/monitors/` appears in the `git diff --stat` shown under
"What was done" above — this change does not touch that machinery, and
the 36-pass count is this session's own direct run, not inherited.

## Next steps

None — `loop_state: landed`. The `tokenmaxxxer-core` finding above is
left as an open finding with a stated resolution path (file a follow-up
issue), not as a next step of this delivery.

## Skill verdicts

- skill-verdict: test-depth-audit — applied: invoked; used the
  skill's execution-vs-verification distinction directly on the 15 named
  sites (a `returncode == 2`-only assertion is exactly the skill's
  Execution-Only pattern applied to a subprocess result: the test runs
  the hook and checks it exited, without checking *what* it decided or
  *why*) to design the fix, and reused the same lens read-only on the
  `tokenmaxxxer-core` sweep population to separate genuinely
  content-checked hits from return-code-only ones.
- skill-verdict: work-in-english — applied: invoked; this record, all
  code comments, commit messages, and the PR are written in English
  despite the spawning task's Korean framing.
