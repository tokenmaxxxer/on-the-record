---
issue: 2326
role: adversarial-review-37c43bc9
author: adversarial-review-37c43bc9
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: PR #2866 (branch issue-2326/diagnose-first-71f82584, head 5be0fbfd25196f6e45c34b5a764ac009343d71de, untracked in this branch's own working tree)
type: verification
breaking: false
verdict: no-ship as landed — process-group-kill/temp-file capture and the fail-open matrix hold up under direct adversarial testing, but two of the three claims the ship decision rests on do not survive independent attack — see "What was done" below for the executed evidence.
loop_state: landed
upstream:
  - path: docs/issue-2326/reports/diagnose-first-71f82584.md
    sha: 5be0fbfd25196f6e45c34b5a764ac009343d71de
  - path: on-the-record/hooks/lint-test-on-edit.sh
    sha: 5be0fbfd25196f6e45c34b5a764ac009343d71de
  - path: on-the-record/hooks/otr_lint_test_timeout_plugin.py
    sha: 5be0fbfd25196f6e45c34b5a764ac009343d71de
  - path: tests/test_spawn_gate_wiring.py
    sha: 5be0fbfd25196f6e45c34b5a764ac009343d71de
  - path: scripts/rework_fraction.py
    sha: same-commit
---

# issue-2326 — adversarial-review-37c43bc9 record

skill-verdict: adversarial-review — applied: invoked; this session's own structural position (independently spawned verifier, fresh context, no access to PR #2866's builder session or its intent) already instantiates the two-party protocol — every number and mechanism below was re-derived against the real shipped hook script and real constructed adversarial inputs, not restated from the PR's own record.
skill-verdict: work-in-english — applied: invoked; this record, all derived commands, and commit/PR text are in English; the final chat summary to the user will be in Korean.
other mounted skills: implementation-audit, research-evidence-discipline — not triggered (this is a mechanism/measurement re-derivation against a shipped hook, not a claims-extraction audit or a research-shaped record).

## What was done

canonical: `gh pr view 2866 --repo tokenmaxxxer/on-the-record` body, read directly by this session, plus PR #2866 head checked out into fresh `git clone`s (paths given per-finding below) — every number in this section was re-derived against that checkout this session, none restated from the PR's own pasted output.

### 1. Process-group kill + temp-file capture: holds under direct adversarial attack

Constructed a synthetic impacted test whose test function forks a grandchild that (a) installs
`signal.signal(SIGTERM, SIG_IGN)`, (b) writes roughly 2MB to its inherited stdout, and (c) sleeps 120s
— combining all three attack shapes in one process, matched into the impacted-test selection via a
same-stem module import (a scratch module/test pair created for this attack only, not a repo path).

```
$ printf '%s' "$PAYLOAD" | timeout 30 bash on-the-record/hooks/lint-test-on-edit.sh post
rc=0 dur=3.452040575s outlen=4181
lint-test-on-edit: impacted test failed (...): ... ZeroDivisionError-style pytest failure text, truncated at 4000 chars ...
$ ps -ef | grep -i "pytest\|adv_probe"
no matching procs
```
derived: both commands run this session, in that order, against the fresh checkout of PR #2866 head — the hook returned in 3.45s (bounded by the 3s per-item SIGALRM timeout, well inside the 15s combined budget) and left zero orphaned processes behind.

`os.killpg(pgid, 9)` sends `SIGKILL`, which cannot be ignored — so the SIGTERM-ignoring branch of the
attack does not actually stress this mechanism; what holds it is the temp-file-vs-pipe distinction the
fix's own comment names. That framing is the one that matters and it holds.

### 2. The docs-fast-path fix closes one spelling, not the shape

Five shapes were tried against a fresh checkout of PR #2866 head. Only the symlink shape reproduces a
bypass:

```
$ python3 -c "import os; os.symlink('../spawn.py', 'docs/live_spawn.py')"
$ printf '%s' "$PAYLOAD_SYMLINK" | bash on-the-record/hooks/lint-test-on-edit.sh post
rc=0 dur=.004711390s outlen=0
```
derived: this session, against a real symlink at a docs-shaped path pointing at the traced episode's own `spawn.py` — the hook classifies the edit as docs-only and skips entirely (zero output) even though the bytes actually being edited through that path are `spawn.py`'s.

The other four shapes tried (absolute path into docs, a relative path that normalizes into docs via
`sub/../docs/x.py`, a Unicode fullwidth-solidus separator U+FF0F which `posixpath` does not treat as a
separator so the whole string becomes one opaque filename, and an embedded-NUL path) all either
correctly classify as docs or fail open harmlessly — none of them bypass the check the way the symlink
does. `posixpath.normpath` (used by both the bash fast path indirectly and python's authoritative
check) resolves `..` segments; it does not resolve symlinks, and neither check layer calls
`os.path.realpath` or checks `os.path.islink` anywhere.

### 3. The timing claim was measured single-invocation; concurrency breaks it — the third thing

Re-ran PR #2866's own 8-run command 35 more times sequentially against a fresh checkout of PR #2866
head:

```
$ for i in $(seq 1 35); do <same spawn.py-edit payload> | bash lint-test-on-edit.sh post; done
min 8.628s, max 13.302s (run 23), all rc=0, none over budget
```
derived: 35 sequential end-to-end runs, this session — consistent with the PR's own cited 9.15-13.21s range; sequential repetition alone did not find an over-budget case.

This machine's own process table shows multiple concurrent agent sessions already running
`spawn.py`-based workflows at the same time as this session:

```
$ ps -ef | grep spawn.py
jwjung 1119117 ... python3 /home/jwjung/.claude/plugins/.../spawn.py -C .../tokenmaxxxer-core-issue-304-execution-observation watch --issue 304 ...
jwjung 1427749 ... python3 spawn.py --issue 370 -C /home/jwjung/tokenmaxxxer-core ...
```
canonical: `ps -ef` output, read directly by this session — this is the hook's actual deployment shape (fires on every edit, fleet-wide, on a shared multi-session box), which single-invocation timing never modeled.

So this session tested that deployment condition directly: 8 concurrent invocations of the real hook,
same payload, same fresh checkout:

```
$ for j in $(seq 1 8); do ( <same spawn.py-edit payload> | bash lint-test-on-edit.sh post ) & done; wait
concurrent-8: 12.646695799s
concurrent-1: 13.145604013s
concurrent-7: 13.650855526s
concurrent-5: 14.204087294s
concurrent-6: 14.655957191s
concurrent-3: 15.037339284s budget exceeded
concurrent-4: 15.049461335s budget exceeded
concurrent-2: 15.049524959s budget exceeded
```
derived: this exact 8-way concurrent run, this session, against the fresh checkout — 3 of the 8 invocations hit the 15s outer budget and returned `"budget exceeded (15s), skipped remaining lint/test checks for spawn.py"`, meaning zero of the three real target-test failures were reported by those 3 runs. A separate 4-concurrent run (10.29s-11.74s across all 4) stayed clear of budget — the failure only appeared once concurrency reached 8.

SIGALRM and process-group-kill (finding 1) bound one test item's own runaway behavior; neither bounds
wall-clock cost imposed by CPU contention from other concurrent invocations of the same hook, which is
exactly the condition a hook shipped to fire on every edit, fleet-wide, will experience. This is the
third thing the task asked me to assume existed.

### 4. Fail-open matrix: every case lets the edit proceed, none hang

```
python3 missing (PATH stripped to bash-only dir): rc=0, dur=.003649688s, outlen=0 (silent)
malformed JSON payload ('{not valid json'): rc=0, dur=.031912695s, outlen=0 (silent)
zero budget (OTR_LINT_TEST_BUDGET_S=0): rc=0, dur=.030974452s, outlen=169 -- "budget exceeded (0s), skipped remaining lint/test checks for spawn.py"
bash missing for .sh lint (PATH built from every /usr/bin,/bin binary except bash): rc=0, dur=.033142600s, outlen=0 (silent, lint step skipped)
otr_lint_test_timeout_plugin.py moved aside: rc=0, dur=.275961985s, outlen=4191 -- ModuleNotFoundError traceback reported as "impacted test failed", zero of the impacted tests actually ran
read-only workspace (chmod -w . on repo root): rc=0, dur=12.281976187s, outlen=4186 -- ran and reported normally (tempfile.TemporaryFile uses TMPDIR, not the workspace)
```
derived: each scenario run individually this session, against a fresh checkout of PR #2866 head — all six scenarios returned rc=0 and completed without hanging; the edit is never blocked by any of them (PostToolUse runs after the edit already happened, so "let the edit proceed" reduces to "never hang, never crash the turn," which held in all six).

The plugin-missing case (line 5 in the fence above) is a minor honesty gap: pytest itself fails to
start because `-p otr_lint_test_timeout_plugin` cannot be imported, so none of the impacted tests
actually ran (see the fence above), but the reported text is shaped identically to a real multi-test
failure — an agent reading the next turn's context cannot currently tell a genuine batch of broken
tests apart from the harness's own plugin file being missing.

### 5. Unprompted finding: git-worktree root misresolution can silently zero out test selection

The hook's git-root walk (checking `os.path.isdir(<probe>/.git)`) only recognizes a real `.git`
directory, never a worktree's `.git` file. In an isolated worktree with no git-tracked ancestor this
degrades harmlessly to the `root = cwd` fallback — verified separately, reports correctly. But nested
under an ancestor that itself contains an unrelated `.git` directory, the walk latches onto that
ancestor instead of the worktree's own root, and impacted-test selection silently finds zero candidates
under the wrong root.

```
$ # outer real repo (.git dir) containing an unrelated inner repo added as a worktree (.git file),
$ # the worktree holding spawn.py + a genuinely failing test (ZeroDivisionError)
$ printf '%s' "$PAYLOAD" | bash lint-test-on-edit.sh post   # cwd = the nested worktree
output: []
$ # control: the same worktree NOT nested under any ancestor .git
$ printf '%s' "$PAYLOAD" | bash lint-test-on-edit.sh post   # cwd = the isolated worktree
output: [{"hookSpecificOutput": ... "impacted test failed (test/test_spawn_thing.py): ... ZeroDivisionError ..."}]
```
derived: both constructed repros run this session in scratch directories outside this repo (`git init`/`git worktree add` against synthetic content, never committed anywhere, no repo-tracked path involved), using the real shipped hook script copied from the fresh PR #2866 head checkout — nesting under an ancestor `.git` reproduces silent zero-report; the isolated control correctly reports the real failure. The accidental first trigger of this same defect, before this controlled repro was built, is noted under "What did not work" below.

This is narrower than findings 2-3 (requires a worktree nested under a repo-shaped ancestor) and this
project's own session working directories are plain clones today, not worktrees, so it does not fire in
the hook's primary deployment population — but this task's own instructions had this session construct
exactly this shape (`git worktree add`) for testing purposes, so it is not a contrived edge case for a
project whose own workflows use worktrees.

### 6. Materiality (4.6%): reproduces now, but swings hard on 2 files

```
$ python3 scripts/rework_fraction.py --batch "$MUSTER_WORKSPACE_ROOT/on-the-record-*.session.*.log"
=== corpus rollup: 17 session(s) ===
total edit calls (Edit/Write/MultiEdit): 212
total rework episodes (cost known): 10
  rework_fraction_of_edit_turns: 4.7%
```
derived: this session, live corpus, ~3.5 hours after PR #2866's own measurement (13 files then, 17 now) — 4.7% vs. the PR's cited 4.6%, same order of magnitude, a 0.1-point drift from 4 new session logs appearing.

The task asked whether two files could move the figure by a point. They can move it by much more:

```
$ # same 17-file corpus, minus the 2 heaviest-rework session logs (5 + 3 of the corpus's 10 episodes)
total rework episodes (cost known): 2
  rework_fraction_of_edit_turns: 1.1%
$ # same 17-file corpus, minus 2 different, zero-rework session logs instead
total rework episodes (cost known): 10
  rework_fraction_of_edit_turns: 6.0%
```
derived: two synthetic 15-file subsets built by copying the live 17-file corpus to scratch directories and deleting 2 files each, this session — removing the corpus's two heaviest-rework sessions drops the figure from 4.7% to 1.1% (a 3.6-point swing from 2 of 17 files); removing two zero-rework sessions instead pushes it to 6.0%.

One session alone contributed half the corpus's rework episodes at 4-8x the median per-episode turn
cost of the rest (see the fence above). A corpus this concentrated is not a stable base for a
materiality argument that two prior rounds already got wrong in opposite directions (round 2's "31s"
was one sleeping test; the original "4.5%" figure's source corpus no longer exists).

## Why

The task named the hook's two hardest-to-verify claims explicitly (the timing bound and the
docs-fast-path fix) and named the exact failure mode that matters for a hook shipping on every edit: a
hook that usually finishes in time and occasionally does not is one that occasionally reports nothing
while costing the full budget. I treated that sentence as the acceptance test rather than as color:
single-invocation repetition (35 more runs) could not find an over-budget case, so this session built
the deployment condition the PR's own methodology never modeled — concurrency — and it produced exactly
that failure mode on the first attempt at 8-way contention. Symmetrically, for the fast-path fix, the
task's framing ("the fix was for one spelling rather than for the shape") pointed at the actual defect
class (string-shape checks that never resolve symlinks) rather than at guessing more `..`-flavored
strings, which is why the symlink attack — and not the Unicode/NUL variants also tried — is the one
that reproduces.

## What did not work

None to report as a mid-task deviation — every constructed attack and re-derivation ran to completion.
One methodology note, not a deviation: this session's first attempt at the timing re-derivation used a
`git worktree add`-based checkout (`git worktree add /tmp/pr2866-verify FETCH_HEAD`, run against this
session's own repo) rather than a plain clone, and that checkout happened to sit directly under an
unrelated, pre-existing `.git` directory left over from other testing on this shared machine — which is
what surfaced finding 5 above by accident (the hook silently reported nothing against that checkout,
where it should have reported the traced episode's real failures).
derived: `bash -x` trace of that first checkout's hook invocation plus a manual `posixpath`/`os.path.isdir` walk, both run this session, showing the walk terminating at `/tmp/.git` (a directory, empty, unrelated to this repo) instead of the worktree's own root — this diagnosis is what led to building the controlled, non-accidental repro in finding 5 above, using plain `git clone` checkouts for every subsequent timing and invariant re-derivation in this record.

## Upstream basis

- `docs/issue-2326/reports/diagnose-first-71f82584.md` — sha 5be0fbfd25196f6e45c34b5a764ac009343d71de, PR #2866 head, untracked in this branch's own working tree. PR #2866's own record; every load-bearing number and mechanism claim in it was independently re-derived above, this session, rather than restated.
canonical: `git cat-file -e 5be0fbfd:docs/issue-2326/reports/diagnose-first-71f82584.md` — present at that commit, this session
- `on-the-record/hooks/lint-test-on-edit.sh`, `on-the-record/hooks/otr_lint_test_timeout_plugin.py`, `tests/test_spawn_gate_wiring.py` — all sha 5be0fbfd25196f6e45c34b5a764ac009343d71de, PR #2866 head, untracked in this branch's own working tree.
derived: `git cat-file -e 5be0fbfd:on-the-record/hooks/lint-test-on-edit.sh && git cat-file -e 5be0fbfd:on-the-record/hooks/otr_lint_test_timeout_plugin.py && git cat-file -e 5be0fbfd:tests/test_spawn_gate_wiring.py` — all three present at that commit, this session; each was read in full and executed directly from a fresh `git clone` checked out to that commit (findings 1-6 above cite the exact commands run against it).
- `scripts/rework_fraction.py` — same-commit, unmodified by PR #2866, present in this branch's own working tree at this record's own commit. Re-run against the live `$MUSTER_WORKSPACE_ROOT` corpus this session (finding 6), not reused from the PR's pasted output.
- Live session-log corpus at `$MUSTER_WORKSPACE_ROOT/on-the-record-*.session.*.log` — 17 files at this session's measurement time, 2026-08-30, vs. 13 at PR #2866's measurement time the same day. Re-queried live, plus two synthetic scratch-directory subsets constructed by this session for the sensitivity check in finding 6.

## Standing invariants (re-derived independently)

**No role-axis return.**
```
$ grep -n "role" scripts/rework_fraction.py on-the-record/hooks/lint-test-on-edit.sh on-the-record/hooks/otr_lint_test_timeout_plugin.py tests/test_spawn_gate_wiring.py
on-the-record/hooks/lint-test-on-edit.sh:89:# No role-axis: this hook keys nothing on a role/skill identity (only
on-the-record/hooks/lint-test-on-edit.sh:93:# gates, per the retired-role-axis decision
on-the-record/hooks/lint-test-on-edit.sh:94:# (docs/decisions/2026-08-25-retire-role-axis-staging.md).
```
derived: this session, against the fresh checkout of PR #2866 head — 3 matches total, all three inside the hook's own "No role-axis:" disclaimer comment block; `scripts/rework_fraction.py` (unmodified) contributes zero matches. This session agrees with PR #2866's own characterization: no executable branch keys on role/skill identity.

**No new bug — failing-test set as names, not counts.**
```
$ diff <(sort main_FAILED.txt) <(sort branch_FAILED.txt)
(empty)
$ wc -l main_FAILED.txt branch_FAILED.txt
15 main_FAILED.txt
15 branch_FAILED.txt
```
derived: fresh `git clone` of `origin/main` and a fresh `git clone` at PR #2866 head, `python3 -m pytest test/ tests/ -q` in each, `grep "^FAILED " | sort` on each, this session — the sorted FAILED-name lists diff empty: 15 of 15 identical test names on both sides (470 passed on main, 491 passed on the branch — the 21-test delta is exactly the new gate-wiring test file's own new test count, expected and not a regression).

**No overhead increase, measured on real edits.**
```
docs-only edit (symlink and non-symlink docs paths): 4.7ms-63ms, no subprocess
low-fan-in edit (watchdog.py): 1.66s, 1.66s, 1.78s across 3 runs
high-fan-in edit (spawn.py, the traced episode's own edit): 8.63s-15.05s depending on concurrency
```
derived: this session, fresh checkout of PR #2866 head — the docs-only and low-fan-in numbers match the PR's own order of magnitude (PR cited 0.002s and 1.14s respectively; the difference here is shell/subprocess startup overhead on this machine, not a regression). The high-fan-in number is inside budget only in the single-invocation case the PR measured; finding 3 above shows the concurrent-load case that breaks it.

**Monitor/watch unbroken and not quieter.**
```
$ python3 -m pytest test/ tests/ -q -k "monitor or watch"
15 passed
$ python3 -m pytest test/test_watchdog_heartbeat_noise.py -q
6 passed in 0.82s
```
derived: this session, fresh checkout of PR #2866 head, using the exact command PR #2866/#2863/#2860 all cite (`test/ tests/` explicit) — 15 passed, matching all three prior citations exactly; 6 passed, matching PR #2866's own citation. Note: running the same `-k` filter without restricting to `test/ tests/` picks up broader default test discovery and returns 45 passed instead — the exact cited command, not the bare filter, is what reproduces 15.

## Open findings

1. Symlink bypass of the docs-fast-path check (finding 2 above). Resolution path: none attempted here
   (verification only) — a fix would need to resolve the real path (or at minimum check
   `os.path.islink`) before the docs-classification decision, which trades away the "zero subprocess for
   docs-only edits" cost claim the hook's own docstring makes as a design constraint — a real tradeoff
   for the issue owner to weigh, not a one-line patch.
2. Concurrent-load budget failures (finding 3 above). Resolution path: none attempted here — options
   include lowering the budget's safety margin further, detecting contention and reporting "skipped,
   high load" distinctly from "budget exceeded" so the two are not conflated, or accepting the residual
   risk explicitly rather than citing single-invocation timing as bounding the deployed case.
3. Fragile materiality (finding 6 above). Resolution path: none attempted here — a materiality claim
   this corpus-sensitive would need either a much larger corpus or an explicit confidence-interval
   framing instead of a point estimate, which is a call for the issue owner.
4. Plugin-missing traceback masquerades as a real test failure (finding 4 above). Minor: does not block
   the edit or hang. Resolution path: none attempted here — catch the pytest invocation's own startup
   failure distinctly (e.g. detect a nonzero-exit-with-zero-collected shape) and report it as an
   infrastructure fault, not a test failure.
5. Git-worktree root misresolution (finding 5 above). Narrow and not in the hook's primary deployment
   population today. Resolution path: none attempted here — checking `os.path.exists` instead of
   `os.path.isdir` on the candidate `.git` entry would recognize the worktree case explicitly rather than
   relying on the `root = cwd` fallback happening to be correct.

## Next steps

loop_state: landed.
derived: this record's own re-derivations this session — the grandchild/SIGTERM/large-output attack (finding 1), the five fast-path-bypass shape attempts (finding 2), the 35-run sequential plus 8-way concurrent timing attack (finding 3), the six-scenario fail-open matrix (finding 4), the worktree-root-misresolution repro (finding 5), the corpus-sensitivity re-derivation with two synthetic subsets (finding 6), and the four standing-invariant re-derivations above — all executed live by this session against the real shipped hook script and fresh checkouts, none restated from PR #2866's own record.

This record's own scope (independent verification of PR #2866) is complete. The verdict is
no-ship-as-landed: the mechanics under direct, deliberate attack in this round (process-group kill,
temp-file capture, fail-open posture) held up completely, but the two claims the ship decision was
actually staked on — bounded timing and a closed fast-path bypass — do not hold once tested past the
single-invocation, single-spelling cases PR #2866 itself tried. The five open findings above are handed
to the issue owner; no further action is taken by this role.
