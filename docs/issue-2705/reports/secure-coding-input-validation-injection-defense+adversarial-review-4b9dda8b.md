---
issue: 2705
role: secure-coding-input-validation-injection-defense+adversarial-review-4b9dda8b
author: secure-coding-input-validation-injection-defense+adversarial-review-4b9dda8b
skills: secure-coding-input-validation-injection-defense (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false
code_under_review: on-the-record/hooks/gate-registration-guard.sh (round 3, built on PR #2763's own head f943d3fc9fa052e006072eed471db4cc535f6313, cherry-picked as commit 87814f4b onto this branch)
loop_state: landed
type: fix
breaking: false
verdict: fixed — the three cwd-stack bypasses (`cd -`, symlinked directory component, `pushd`/`popd`) both independent round-3 verification records ground-truthed are closed, each pinned with a stash-based fail-before/pass-after regression test proven live against the true pre-round-3 baseline. Round 2's fixes (`cd`/subshell, directory-add, `:(exclude)`) are unchanged and re-verified passing. Failing-test-name SET vs origin/main is unchanged (byte-identical); directive bytes unchanged; added overhead is within the same noise band prior sessions measured (no new subprocess call).
upstream:
  - path: on-the-record PR #2763, branch issue-2705/secure-coding-input-validation-injection-defense+adversarial-review-bb9edf99
    sha: f943d3fc9fa052e006072eed471db4cc535f6313
  - path: docs/issue-2705/reports/adversarial-review-17a16473.md
    sha: same-commit
  - path: docs/issue-2705/reports/adversarial-review-f4b31b03.md
    sha: same-commit
---

# issue-2705 — secure-coding-input-validation-injection-defense+adversarial-review-4b9dda8b record

## What was done

Build-now bypass (contract v3 s19a): checked: `printenv | grep CORE_BUILD_NOW`
— result: `CORE_BUILD_NOW=1`. Delivers directly, no proposal round.

canonical: `gh issue view 2705` and `gh pr view 2763 --repo tokenmaxxxer/on-the-record --comments`,
both read at session start — PR #2763 came back CHANGES a third time; the
review comment names three ground-truthed bypasses in the cwd-stack PR
#2763 itself introduced (`cd -`, a symlinked directory component,
`pushd`/`popd`), citing `docs/issue-2705/reports/adversarial-review-17a16473.md`
and `.../adversarial-review-f4b31b03.md` (both read in full this session)
as the merged, independent ground-truthing.

### 0. This branch did not yet carry PR #2763's own code

derived: `grep -c _pending_add_segments on-the-record/hooks/gate-registration-guard.sh`
against both `origin/main` and this session's own starting branch tip
(`1fcf9e2d`) — result: `0` in both. PR #2753's code was never merged
(sent back for CHANGES); PR #2763 (built on top of it) is still open. So
"rebase onto current origin/main first" for this round means: bring PR
#2763's own code onto this branch's current `origin/main` base, then fix
the three named gaps on top of it, not append a diff against code this
branch doesn't have.

derived: `git fetch origin pull/2763/head:pr-2763-ref` then `git merge-base
origin/main pr-2763-ref` — result: `1d6e746c`, which is exactly this
branch's own `origin/main` base (two docs-only commits behind this
session's starting tip `1fcf9e2d`) — so PR #2763's single code commit
cherry-picks cleanly with no rebase conflict. `git cherry-pick -n
5a2f1c8c` (PR #2763's one code+test commit; its second commit, `f943d3fc`,
touches only that PR's own record file, confirmed via `git show f943d3fc
--stat`, and was not picked). Re-ran the inherited suite immediately after
the cherry-pick, before touching anything: `python3 -m pytest
test/test_gate_registration_guard_bundled_add_commit.py -q` — result: `20
passed in 3.26s`, confirming PR #2763's own round-2 fixes are intact on
this branch before any round-3 change.

### 1. The fix — a real per-frame cwd model in `_pending_add_segments`

canonical: `on-the-record/hooks/gate-registration-guard.sh` (this commit,
`87814f4b`), `_new_frame`/`_pending_add_segments` (lines ~213-303) and
`_match_untracked` (lines ~337-361). Both merged verification records
named the same resolution path at file:line; followed it:

- **`cd -`**: each stack entry is now a frame `{cwd, oldpwd, dirs}`
  instead of a bare cwd string. A `cd` (non-`pushd`) segment sets
  `frame["oldpwd"] = frame["cwd"]` before moving. A segment whose args
  contain the literal token `-` is recognized as `cd -` (checked before
  the generic `-`-prefix flag filter would otherwise swallow it) and
  swaps `frame["cwd"]`/`frame["oldpwd"]`, mirroring bash's own OLDPWD
  swap.
- **`pushd`/`popd`**: `frame["dirs"]` is a real stack (`dirs[0]` always
  kept equal to `frame["cwd"]`). `pushd DIR` inserts the resolved target
  at `dirs[0]`, which pushes the old cwd (already sitting at `dirs[0]`)
  back to `dirs[1]`. `popd` (previously unrecognized anywhere in this
  parser — an unrecognized segment fell through to the generic
  "no `git` token, skip" branch, so `pushd`'s own directory change was
  never undone) is now a first-class segment kind: pops `dirs[0]` and
  promotes `dirs[1]` if the stack has more than one entry, a no-op
  (matching bash's own "directory stack empty" error) otherwise.
- **symlinked directory component**: every cwd committed to a frame
  (the initial payload cwd, and the target of every `cd`/`pushd`/`cd -`)
  is now `os.path.realpath`'d, not `os.path.normpath`'d, before being
  stored. `_match_untracked`'s own final `abs_p` computation is also
  `os.path.realpath`'d (not just its `seg_cwd` input) as defense in
  depth for a segment that passes a symlinked path straight to `git add`
  without ever `cd`-ing through it — both records' root-cause spans
  named this same function as the second half of the fix ("resolve the
  effective cwd (and/or every path derived from it in
  `_match_untracked`)").

A `(...)` subshell still pushes/pops a full copy of the current frame
(cwd, OLDPWD, and dir stack together), intended so a `cd`/`pushd`/`popd`/
`cd -` done inside a subshell does not leak to the parent, the same
containment round 2 already established. derived:
`test_subshell_cd_does_not_leak_to_a_later_top_level_segment`, part of
the `24 passed` run in §2 below (this session), is the live evidence this
containment still holds with the richer per-frame state in place.

### 2. Regression tests — `BundledCwdStackFrameTest`, pinned per shape

canonical: `test/test_gate_registration_guard_bundled_add_commit.py`
(this commit), `BundledCwdStackFrameTest` — four new tests: `cd -`,
`pushd`/`popd`, `cd` through a symlinked directory, and a defensive
`popd` on an empty stack (must not raise, must not move cwd).

derived: `python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -v`
— result: `24 passed in 5.95s` (the pre-existing 20 plus these 4).

### 3. Stash-based fail-before/pass-after, per shape, against the true baseline

Same discipline both merged verification records used: the true
pre-round-3 baseline is PR #2763's own head (`f943d3fc`, cherry-picked
as `5a2f1c8c` onto this branch before any round-3 edit), not
`origin/main` (which has no bundled-add parsing at all and would test
"parsing absent," a different and coarser condition).

derived: swapped only `on-the-record/hooks/gate-registration-guard.sh`
to the pre-round-3 (post-cherry-pick, pre-edit) content — captured from
the git index right after the cherry-pick via `git show
:on-the-record/hooks/gate-registration-guard.sh` — keeping this
session's own new test file in place, then:
```
$ python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -k "BundledCwdStackFrameTest" -v
FAILED ...BundledCwdStackFrameTest::test_cd_dash_restores_oldpwd_and_refuses_unregistered_gate
FAILED ...BundledCwdStackFrameTest::test_pushd_popd_restores_directory_and_refuses_unregistered_gate
FAILED ...BundledCwdStackFrameTest::test_cd_through_symlinked_directory_refuses_unregistered_gate
3 failed, 1 passed in 1.76s
```
The one that passes both ways, `test_popd_with_empty_stack_is_a_noop_not_a_crash`,
does not depend on the round-3 fix at all (an empty-stack `popd` is a
no-op under both the pre- and post-fix code — the pre-fix code simply
never recognized `popd` as a keyword, and the post-fix code's own
no-op-on-empty-stack branch produces the identical observable result),
so its pass-both-ways is expected, matching the same "defensive,
not shape-pinning" convention `adversarial-review-17a16473.md` §2 already
established for its own two pass-both-ways tests.

Restored the round-3-fixed file (`cp` from a pre-edit copy saved before
the swap, verified via `git diff --stat` showing no residual diff against
the committed version), reran:
```
$ python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -v
24 passed in 3.96s
```
derived: the two pytest transcripts quoted immediately above (this
session) are the fail-before/pass-after evidence for all three named
shapes.

### 4. Live-fire against the real working-tree hook + real bash/git ground truth

A first live-fire attempt against a fresh `git clone` of this repo used
the CLONE's own copy of the guard script as the harness target — which,
since `git clone` only ever checks out committed refs, was still running
the pre-round-3 (in fact pre-any-cherry-pick, since nothing on this
branch is committed until this session's own checkpoint) code regardless
of the working tree's edits, producing three misleading `EXIT: 0` results
that looked like the fix was not taking effect. Documented under "What
did not work" below; corrected by pointing the harness at the real
on-disk file (`$REPO/on-the-record/hooks/gate-registration-guard.sh`),
the same convention `test/test_gate_registration_guard_bundled_add_commit.py`'s
own `HOOK_PATH` already uses (only the git-status/staged side of the
harness needs a disposable clone; the hook binary itself must be the real
file to reflect an uncommitted edit).

derived: `python3 /tmp/grg_r3_run_guard.py "<cmd>" "$HOOK" "$PWD"` (this
session's own harness script, POSTing a real PreToolUse JSON payload on
stdin to `bash on-the-record/hooks/gate-registration-guard.sh`), against
untracked `gates/probe_*.py` fixtures in a throwaway `/tmp/grg_r3_probe2`
clone (never committed to this repo):
```
=== cd - ===
$ cd sub && cd - && git add gates/probe_cddash.py && git commit -m x
EXIT: 2
gate-registration-guard: newly-added gate/hook module(s) missing a spec registration row (issue #441/#684):
gates/probe_cddash.py: no row in docs/specs/enforcement-boundary.md

=== pushd/popd ===
$ pushd sub && popd && git add gates/probe_pushd.py && git commit -m x
EXIT: 2
gates/probe_pushd.py: no row in docs/specs/enforcement-boundary.md

=== symlink cd ===
$ cd gates_link && git add probe_symlink.py && git commit -m x   # gates_link -> gates
EXIT: 2
gates/probe_symlink.py: no row in docs/specs/enforcement-boundary.md
```
derived: the three transcripts immediately above (this session) confirm
all three now correctly refuse (rc=2) against the shipped fix.

Real-git/bash ground truth for the same three commands, established this
session in the same throwaway clone (`git diff --cached --name-status`
after running just the `cd`/`pushd`+`git add` portion, `git reset -q`
between rows):
```
cd sub && cd - && git add gates/probe_cddash.py         -> A  gates/probe_cddash.py
pushd sub && popd && git add gates/probe_pushd.py        -> A  gates/probe_pushd.py
cd gates_link && git add probe_symlink.py                -> A  gates/probe_symlink.py
```
derived: the transcript immediately above (this session) — real git
stages all three under their real repo-relative path in every case,
matching the guard's own refusal target exactly, not a coincidental rc.

## Why

canonical: this record's §0-§4 above (all executed this session against
this branch's own working tree, not cited from either verification
record at face value) is the basis for every conclusion.

Both merged verification records independently converged on the same
diagnosis and the same resolution path: the round-2 cwd stack modeled a
single mutable "current cwd" string, which cannot represent bash's own
OLDPWD (`cd -`) or its directory stack (`pushd`/`popd`), and never
canonicalized a symlinked path component before deriving a repo-relative
comparison against `git status`'s own (always-canonical) output. The
CHANGES review framed this as one defect, not three, and asked for the
model to be finished rather than patched a third time with another
single-slot special case. canonical:
`docs/issue-2705/reports/adversarial-review-17a16473.md` and
`.../adversarial-review-f4b31b03.md`, both re-read this session — "Open
findings" in each names the same resolution path this fix implements
(per-frame OLDPWD, `realpath` before deriving a repo-relative path, a
real push/pop stack). This fix replaces the single mutable string with a
per-frame object (`cwd`/`oldpwd`/`dirs`) so `cd -` and `pushd`/`popd` are
each a direct, non-special-cased read of state the model already tracks,
and canonicalizes every cwd the moment it is computed (at the frame
level) plus again at the point a repo-relative path is actually derived
(`_match_untracked`) rather than patching the three named symptoms
individually.

derived: the `Skill(secure-coding-input-validation-injection-defense)`
tool call made this session (its returned rule text, quoted in full in
this session's own tool-result turn) is the source for the following
citation. Rule 10 of that skill reads: scope a review/fix pass to the
changed lines and the trust boundaries they cross, triaging out
low-signal or non-reachable matches. This fix stays scoped to the trust
boundary the cwd stack itself crosses (the `cd`/`pushd`/`popd`/`git add`
resolution path both verification records named), not a broader rescan
of the guard's other branches. That same skill's rule 8 (fail closed
instead of a silent fallback, for security-relevant fields) does not
apply in its literal form here — canonical: `gh issue view 2705`'s own
must-not list (re-read this session) explicitly forbids widening this
guard to fail-closed on unanalyzable input, and
`docs/issue-2705/reports/adversarial-review-249cc937.md`'s §3 (re-read
this session) already established that the round-2 `:(exclude)` fix
exists specifically to avoid an accidental fail-closed regression — this
guard's fail-open posture on genuinely unparseable shapes is therefore a
deliberate, previously-confirmed design invariant, not an oversight rule
8 would flag for removal.

I did not widen scope beyond the three named shapes. Two adjacent edges
one of the two records flagged as untested (a `cd` to a nonexistent
target joined by `;` instead of `&&`, and bare `cd` meaning `$HOME`) are
outside the CHANGES review's own named list (`cd -`, symlink,
`pushd`/`popd` only) — canonical: `gh pr view 2763 --comments` (re-read
this session), the review comment's own bullet list names exactly those
three — and are carried forward under "Open findings" below rather than
folded in here, consistent with the review's own stated bound (a fourth
round finding a fresh gap is a signal to reconsider the approach, not
license to pre-empt it with an unscoped patch this round).

## Upstream basis

canonical: `gh issue view 2705`, read at session start, for acceptance
criteria and the must-not-fail-closed constraint. `gh pr view 2763
--repo tokenmaxxxer/on-the-record --comments`, read at session start, for
the third CHANGES review and its exact three named bypasses.
`docs/issue-2705/reports/adversarial-review-17a16473.md` and
`.../adversarial-review-f4b31b03.md`, both read in full this session, for
the ground-truthed root causes and the resolution paths this fix follows
at file:line. `on-the-record/hooks/gate-registration-guard.sh` at PR
#2763's head (`f943d3fc9fa052e006072eed471db4cc535f6313`), cherry-picked
onto this branch (commit `5a2f1c8c`) as this round's starting point —
derived: `git cherry-pick -n 5a2f1c8c` and `git merge-base origin/main
pr-2763-ref` (both this session), confirming a clean, conflict-free
cherry-pick onto this branch's actual `origin/main` base.

## Open findings

- **Bare `cd` (no argument, real meaning "go to `$HOME`") treated as a
  no-op**: not fixed this round. canonical:
  `docs/issue-2705/reports/adversarial-review-f4b31b03.md`, "Checked, not
  a bypass" (re-read this session) — that record itself did not find a
  live-reproducible bypass built on this alone within its own session,
  and it is not one of the three shapes this round's CHANGES review
  named. Left open per the review's own explicit bound; a follow-up round
  should construct a scenario where `$HOME` sits inside or adjacent to
  the repo tree before treating this as a confirmed defect.
- **`cd` to a nonexistent target, joined by `;` not `&&`**: not fixed
  this round. canonical: `docs/issue-2705/reports/adversarial-review-17a16473.md`,
  §3 ("Nonexistent-`cd`-target bypass under `;`", re-read this session) —
  reproduced there, but also not one of the three shapes this round's
  CHANGES review named. Resolution path, per that record: check
  `os.path.isdir(target)` (relative to the repo checkout the guard
  already has on disk) before committing a `cd` target to a frame,
  leaving the frame unchanged on a nonexistent target, mirroring bash's
  own failed-`cd` behavior.
- Per the CHANGES review's own explicit bound: if a fourth round finds a
  fresh cwd-tracking bypass beyond the two named above, that is the
  review's own stated signal to reconsider the approach (a different
  seam, or an explicit statement of what this parser does not cover)
  rather than a fourth single-shape patch — not a next step for this
  record to pre-empt.

## Next steps

None for this record; `loop_state: landed`. Recommend the two open
findings above be evaluated together as a single follow-up scope
decision (fix vs. state-as-uncovered), consistent with the review's own
bound, rather than as a fourth incremental patch.

## What did not work

A probe-harness mistake, not a finding about the code under review: the
first live-fire attempt in §4 above pointed the harness's `HOOK` path at
a freshly `git clone`d copy of this repo instead of the real working-tree
file. Since `git clone` only ever checks out committed refs, and nothing
on this branch was committed yet at that point, the cloned guard script
was still the pre-cherry-pick (in fact pre-round-2) code regardless of
what the working tree already contained — all three probes returned
`EXIT: 0`, which briefly looked like the round-3 fix was not taking
effect. derived: `python3 -m pytest ...` had already shown `24 passed`
moments earlier using the SAME test file (`_run_guard`'s own `HOOK_PATH`
resolves to `Path(__file__).resolve().parent.parent`, the real repo, not
a clone) — the contradiction between that green run and the manual
probe's `EXIT: 0` results is what surfaced the harness bug rather than a
regression. Corrected by pointing the manual harness at
`$REPO/on-the-record/hooks/gate-registration-guard.sh` directly (the same
convention the test file already used), re-ran, and got the `EXIT: 2`
results quoted in §4 above.

A sequencing gap: the `secure-coding-input-validation-injection-defense`
`Skill` tool call happened after the fix's implementation was already
written (§1-§2 above), not before it, since this task's own build-now
bypass framing led straight into cherry-picking and patching without
pausing for the skill-obligations check first. Corrected in this same
commit by calling the skill and citing its applicable rule (rule 10) in
"Why" above; the fix's own scoping already matched that rule in substance
(strictly the three named shapes, no broader rescan) before the tool call
caught up to it in form — the same shape of correction
`adversarial-review-249cc937.md` logged for its own skill-call ordering.

## Standing invariants

1. **No return of the retired role axis in any reshaped form.**
   derived: `git diff HEAD -- on-the-record/hooks/gate-registration-guard.sh test/test_gate_registration_guard_bundled_add_commit.py | grep -ic role`
   — result: `0`.

2. **No new bug — failing-test-name SET vs `origin/main`, not counts.**
   canonical: `python3 -m pytest test/ gates/ -q`, run in a fresh
   `git worktree` of this commit (`87814f4b`) — result:
   ```
   15 failed, 454 passed, 3 xfailed
   ```
   run again in a separate worktree of `origin/main` — result:
   ```
   15 failed, 430 passed, 3 xfailed
   ```
   derived: `grep "^FAILED" <output> | awk '{print $2}' | sort` on both,
   then `diff`/`comm -13`/`comm -23` of the two 15-line sorted name
   lists — result: empty both directions (`diff` reports no difference).
   Byte-identical failing-test-name SETS; this round introduces zero new
   failing test names. The 24-test gap (454 vs 430) is exactly this
   file's own added tests (20 from PR #2763's round-2 fixes + 4 new from
   this round's `BundledCwdStackFrameTest`).

3. **No overhead increase.**
   canonical: `du -sb on-the-record/directive`, run in this branch's
   working tree — result: `53162`, matching the baseline both prior
   verification records already confirmed; `git status --short
   on-the-record/directive` — result: untouched (not in this round's
   diff).
   Re-measured the added parse cost directly (5 runs each, live-fire
   harness against a fresh clone, hook path pointing at the real
   working-tree file per the corrected harness above):
   ```
   no_add (plain "git commit -m x"):                        0.043-0.061s
   plain_add (round-1 bundled-add case):                     0.064-0.067s
   worst_round2 (subshell cd + exclude pathspec together):   0.062-0.077s
   new_round3_path (pushd + popd + add):                     0.074-0.087s
   ```
   derived: the four timing rows above (this session, 5 runs each) — the
   round-3 path (pushd/popd resolution, one extra dict copy per
   subshell-scope frame and O(1) list operations per `cd`/`pushd`/`popd`
   segment) adds roughly 10-20ms over the round-2 worst case under this
   session's own measurement — within the same noise band
   `adversarial-review-17a16473.md`/`adversarial-review-f4b31b03.md`
   already measured for round 2, and no new subprocess call is introduced
   (the `git status --porcelain` call PR #2753 already introduced is
   still the only one gating on `pending_add_segments` being non-empty).

4. **Monitor/watch machinery unbroken and not quieter.**
   derived: `git status --short | grep -i 'monitor\|watch'` — result:
   empty (no monitor/watch-class path touched by this round's diff);
   `git show 87814f4b --stat` — result: 3 files touched (the guard
   script, the test file, and PR #2763's own carried-forward record via
   the cherry-pick), none in any monitor/watch-class path.

## Skill verdicts

- skill-verdict: secure-coding-input-validation-injection-defense — applied: invoked; derived: the `Skill(secure-coding-input-validation-injection-defense)` tool call this session and this record's "Why" section above (rule 10 and rule 8's applicability both reasoned through there, each with its own separate citation) together are the evidence this verdict is grounded in — not a summary of the skill, the actual tool call plus the reasoning it produced.
- skill-verdict: adversarial-review — not-applicable: this round's task
  is to build the fix (build-now bypass), not to serve as a structurally
  independent evaluator of someone else's deliverable — the skill's own
  trigger requires a separate session with no stake in defending the
  work, which this session, as the builder, is not.
- other mounted skills: not triggered — none beyond the two above were
  configured for this session.
</content>
