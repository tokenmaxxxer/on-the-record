---
issue: 2705
role: adversarial-review-17a16473
author: adversarial-review-17a16473
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2763's own deliverable
code_under_review: on-the-record PR #2763 (f943d3fc9fa052e006072eed471db4cc535f6313)
loop_state: landed
type: review
breaking: false
verdict: changes-recommended — the three parser gaps PR #2753 was sent back for (`cd`/subshell path resolution, directory-add, `:(exclude)` false refusal) are genuinely fixed and each is pinned by a regression test proven live to fail against the true pre-fix baseline (PR #2753's own head, `c6068dcf`) and pass after — but the cwd-stack machinery this PR introduces to fix them has its own gaps: `cd -`, `pushd`/`popd`, a `cd` to a directory that does not exist (semicolon-joined), and `cd` into a symlink all reproduce the identical silent bypass class live, on the same fixture the fixed shapes correctly refuse. This is the same standing risk stated in the task brief (a parser sits in front of a guard) recurring one layer down in the new code, not a different defect class.
upstream:
  - path: on-the-record PR #2763, branch issue-2705/secure-coding-input-validation-injection-defense+adversarial-review-bb9edf99
    sha: f943d3fc9fa052e006072eed471db4cc535f6313
  - path: docs/issue-2705/reports/adversarial-review-249cc937.md
    sha: same-commit
  - path: docs/issue-2705/reports/adversarial-review-e4ba953e.md
    sha: same-commit
---

# issue-2705 — adversarial-review-17a16473 record

## What was done

Build-now bypass (contract v3 s19a): checked: `printenv | grep CORE_BUILD_NOW`
— result: `CORE_BUILD_NOW=1`. Delivers directly, no proposal round.

canonical: `gh pr view 2763 --json title,body,state,headRefName,baseRefName`
— PR #2763, OPEN, base `main`, head
`f943d3fc9fa052e006072eed471db4cc535f6313`, branch
`issue-2705/secure-coding-input-validation-injection-defense+adversarial-review-bb9edf99`.
Read both merged verification records
(`docs/issue-2705/reports/adversarial-review-249cc937.md`,
`.../adversarial-review-e4ba953e.md`) and PR #2753's CHANGES comment
first, to identify what this PR must fix without re-verifying #2753's
own claims. Checked out the PR head into an isolated worktree
(`git fetch origin pull/2763/head:pr-2763-review && git worktree add
/tmp/pr2763-wt pr-2763-review`) and re-derived every claim below against
that checkout.

### 1. The three named gaps — confirmed fixed, live

canonical: `f943d3fc:on-the-record/hooks/gate-registration-guard.sh`
(diff against `1d6e746c`, the last commit on `main` before this PR —
`git diff 1d6e746c f943d3fc -- on-the-record/hooks/gate-registration-guard.sh`)
adds a cwd stack (`_pending_add_segments`, lines ~162-330) threaded
through `_shell_segments`, a `_match_untracked` directory-prefix sweep,
and `_pathspec_exclude_pattern`/exclude-subtraction in
`_pending_add_targets`.

derived: live-fired each shape against a fresh clone of the PR head
(`/tmp/probe2763`), harness: a Python wrapper POSTing a real PreToolUse
JSON payload (`{"tool_name":"Bash","tool_input":{"command":"<cmd>"},
"cwd":"/tmp/probe2763"}`) on stdin to
`bash on-the-record/hooks/gate-registration-guard.sh`, against untracked
`gates/probe_*.py` files (throwaway fixtures created and deleted within
this session's `/tmp/probe2763` scratch clone only, never committed, no
spec row):
```
cd gates && git add probe_cd1.py && git commit -m x                    -> EXIT 2 (refused)
(cd gates && git add probe_sub1.py) && git commit -m x                  -> EXIT 2 (refused)
git add gates/ && git commit -m x                                       -> EXIT 2 (refused)
git add gates && git commit -m x                                        -> EXIT 2 (refused)
git add . ':(exclude)docs_note_probe.md' && git commit -m x  (real gate co-occurs) -> EXIT 2 (refused)
```
The last row is the specific must-not-fail-closed case the task asked me
to test: an exclude pathspec co-occurring with a real new gate file
(`gates/probe_realgate.py`, an untracked throwaway fixture in the same
scratch clone, created and deleted this session, never committed). The
guard still refuses correctly (subtracts only the excluded match, the
untracked real-gate file remains flagged) — not a blanket "any exclude
token makes the segment unparseable" fail-closed response.

### 2. Stash/revert-based fail-before/pass-after re-derivation

The PR's own claim ("each of the three shapes is pinned with a
regression test verified live to FAIL against the pre-fix parser and
PASS after, via a stash-based revert") needed re-derivation with the
*true* pre-fix baseline, not a shortcut. PR #2753's own code was never
merged to `main` — `main` at `1d6e746c` has zero `_pending_add_segments`
lines at all. derived: `git show 1d6e746c:on-the-record/hooks/gate-registration-guard.sh
| grep -c _pending_add_segments` — result: `0`. Swapping in `1d6e746c`'s
guard script therefore tests "no bundled-add parsing whatsoever," not
"PR #2753's first cut minus this PR's three follow-up fixes" — a
materially different, too-coarse baseline that would misrepresent which
tests actually pin which fix. The real first-cut baseline is PR #2753's
own head commit, still fetchable: `git fetch origin
c6068dcf496c11d1423814e22ab9975fb686aff7`.

derived: swapped only `on-the-record/hooks/gate-registration-guard.sh`
to the `c6068dcf` (PR #2753 first-cut) content, kept this PR's test
file, ran `python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py
-v -k "CdBeforeAdd or DirectoryAdd or ExcludePathspec"` — result:
```
7 failed, 2 passed in 2.09s
```
Restored the fixed guard script (`cp /tmp/guard_fixed.sh
on-the-record/hooks/gate-registration-guard.sh`, verified via `git diff
--stat` showing no residual diff), reran the identical pytest command —
result:
```
9 passed in 2.02s
```
The two that pass unchanged both ways
(`test_subshell_cd_does_not_leak_to_a_later_top_level_segment`,
`test_exclude_pathspec_for_unrelated_path_still_refuses_real_gate`) are,
canonical: `f943d3fc:test/test_gate_registration_guard_bundled_add_commit.py:220-228,304-308`
(read this session) — by their own class docstrings, defensive
no-regression tests guarding against the fix itself over-reaching (a
subshell `cd` leaking past its close; an exclude token swallowing an
unrelated real gate) — not claimed as shape-pinning tests, so their
pass-both-ways is expected and not a discrepancy. The other 7 (spanning
all three named shapes, per the two pytest transcripts immediately
above, this session) genuinely fail against the true first-cut baseline
and pass against the shipped fix — the PR's fail-before/pass-after claim
holds under this independent re-derivation with the corrected baseline.

### 3. New bypasses found in the fix's own cwd-stack machinery

Per the task's brief — assume the new cwd-stack and directory handling
introduced their own edges, don't just confirm the three named ones are
gone — I probed nested subshells, nested-cd chains, nonexistent-cd
targets, `cd -`, `cd` with no argument, symlink-`cd`, and `pushd`/`popd`
against the same live-fire harness and the same untracked-gate fixture
described in §1 above.

**Confirmed correct (no bypass):**
```
cd nonexistent_dir_xyz && git add gates/probe.py && git commit -m x   -> EXIT 0 (correct: real bash aborts the && chain when cd fails, nothing is ever staged)
cd sub && cd .. && git add gates/probe.py && git commit -m x          -> EXIT 2 (chained cd correctly resolved)
( (cd gates && git add probe.py) ) && git commit -m x                 -> EXIT 2 (nested subshell correctly resolved)
cd  && git add gates/probe.py && git commit -m x   (no-arg cd)        -> EXIT 2 (conservatively treated as a no-op; see caveat below)
```

**Confirmed BYPASS (exit 0, should refuse) — new findings, not covered by
the shipped regression suite or the PR's own record.** For each, real
git's staging behavior was established first as ground truth this
session in the same throwaway scratch clone (`/tmp/probe2763`, all
fixture files untracked, created and deleted within this session, never
committed), then the identical command text was fed to the shipped
`f943d3fc` guard:

```
=== cd - (return to previous directory) ===
ground truth: ( cd gates && cd - >/dev/null && git add gates/probe_cddash.py && git diff --cached --name-status )
  -> A       gates/probe_cddash.py   (real git DOES stage it)
guard: cd gates && cd - && git add gates/probe_cddash.py && git commit -m x
  -> EXIT 0  (silent bypass)

=== pushd/popd pair ===
ground truth: ( pushd gates >/dev/null && popd >/dev/null && git add gates/probe_pushd.py && git diff --cached --name-status )
  -> A       gates/probe_pushd.py   (real git DOES stage it)
guard: pushd gates && popd && git add gates/probe_pushd.py && git commit -m x
  -> EXIT 0  (silent bypass)

=== cd to a nonexistent target, joined by `;` not `&&` ===
ground truth: ( cd nonexistent_dir_xyz; git add gates/probe_cdbad2.py; git diff --cached --name-status )
  -> A       gates/probe_cdbad2.py   (real git DOES stage it -- `;` does not abort on the failed cd, so cwd stays put and the add resolves against it)
guard: cd nonexistent_dir_xyz; git add gates/probe_cdbad2.py; git commit -m x
  -> EXIT 0  (silent bypass)

=== cd into a symlinked directory ===
ground truth: ( cd gates_link && git add probe_symlink.py && git diff --cached --name-status )   # gates_link -> gates
  -> A       gates/probe_symlink.py   (real git resolves the symlink and stages the real path)
guard: cd gates_link && git add probe_symlink.py && git commit -m x
  -> EXIT 0  (silent bypass)
```
derived: all eight commands above (four ground-truth, four guard
invocations), run this session against the same `/tmp/probe2763` scratch
clone of the PR head; `git diff --cached --name-status` immediately
followed by `git reset -q` established each ground-truth row, `echo $?`
captured each guard exit code.

Root cause, all four, in `f943d3fc:on-the-record/hooks/gate-registration-guard.sh:243-247`
(read this session):
```python
        if seg[0] in ("cd", "pushd"):
            args = [a for a in seg[1:] if not a.startswith("-")]
            if args:
                target = args[0]
                stack[-1] = target if os.path.isabs(target) else os.path.normpath(
                    os.path.join(stack[-1], target))
            continue
```
Four distinct gaps in this one branch:
- **`cd -`**: the arg-filter `if not a.startswith("-")` drops the literal
  token `-` itself (it starts with `-`), leaving `args` empty, so the
  `if args:` guard is false and the stack is left unchanged — treated as
  a no-op instead of restoring `$OLDPWD`. The effective cwd stays wherever
  it was before the `cd -`, one directory level off from where real bash
  actually ends up, so the following `git add`'s relative path resolves
  against the wrong base and produces a `rel` that matches nothing in
  the untracked set.
- **`pushd`/`popd`**: `popd` is not recognized as a directory-changing
  keyword anywhere in this branch or in `_shell_segments` — only `"cd"`
  and `"pushd"` are checked at line 243. A `popd` segment has no `git`
  token, so it falls into the generic `if "git" not in seg: continue`
  path a few lines down and is silently skipped. `pushd`'s own directory
  change is therefore never undone in the parser's model, even though
  real bash's `popd` restores the prior directory exactly as `cd -`
  would.
- **cd to a nonexistent directory**: `os.path.normpath(os.path.join(...))`
  is a pure string operation — there is no `os.path.isdir(target)` check
  before committing `target` to the stack. Real bash's `cd` to a missing
  directory fails and leaves `$PWD` unchanged; this parser always
  "succeeds." Under `&&` this coincidentally matches ground truth (the
  chain aborts either way, so the wrong resolved path never gets
  compared against anything meaningful) — but under `;` (or any
  separator that does not short-circuit on the failed `cd`), the
  divergence becomes a live bypass, per the transcript above.
- **symlink `cd`**: `os.path.normpath` performs no `os.path.realpath`/
  symlink resolution. `cd`ing into a directory that is a symlink to
  `gates/` leaves the stack holding the symlink's own path
  (`.../gates_link`), so the later `os.path.relpath(..., repo_root)`
  computes `gates_link/probe_symlink.py` — a string that appears nowhere
  in the untracked set (which records the file under its real path,
  `gates/probe_symlink.py`), even though real git transparently follows
  the symlink and stages the file under its real path.

None of these four are the "fail-closed on an unanalyzable shape" the
issue's must-not warns against and the task told me not to accept as an
answer — each is the opposite: a shape the parser fully tokenizes and
resolves, just to the wrong effective directory, producing a wrong
resolved path and a silent, incorrect ALLOW. Same defect class as the
`cd`/subshell gap this PR exists to fix, one branch over.

## Why

canonical: §1-§3 above (this session's own live-fire transcript against
the PR head, plus the real-git ground truth established alongside each
new bypass) is the basis for every conclusion in this record. The task's
premise — a parser in front of a guard is itself new attack surface, and
one review round rarely exhausts it — held again on this round: the
three previously-reported shapes are genuinely closed (§1-§2 above), but
the specific machinery built to close them (the `cd`/`pushd` branch at
`f943d3fc:on-the-record/hooks/gate-registration-guard.sh:243-247`) has
its own untested edges in the same class. I worked the task's explicit
list of unexplored shapes (nested subshells, unclosed subshell, no-arg
`cd`, `cd -`, symlink `cd`, `..`-escape, `pushd`/`popd`, a nonexistent
`cd` target, exclude-pathspec co-occurring with a real gate) rather than
re-confirming only the three named fixes, and established real-git
ground truth for every new bypass before citing it, per this task's
explicit "every negative claim needs a command and its output"
instruction. I did not attempt a fix; this role's remit is independent
verification, not remediation.

## Upstream basis

canonical: `gh pr view 2763 --json title,body,state,headRefName,baseRefName`
and `gh pr diff 2763`, both read at session start — PR #2763
(`tokenmaxxxer/on-the-record`), head `f943d3fc9fa052e006072eed471db4cc535f6313`.
`docs/issue-2705/reports/adversarial-review-249cc937.md` and
`.../adversarial-review-e4ba953e.md`, both read in full at session start,
for what PR #2753's own review round already covered (not re-verified
here, per this task's explicit instruction). `gh issue view 2705`, read
at session start, for the acceptance criteria and the must-not-fail-closed
constraint.

## Open findings

canonical: §1-§3 above (this session's own live-fire transcript,
ground-truth comparisons, and file:line citations) is the evidence for
every item below; no separate re-derivation is needed to restate the
verdicts here.

- **`cd -` path-resolution bypass** (§3 above): silently bypasses the
  fix, same class as the already-fixed `cd`/subshell gap. Resolution
  path: recognize the literal `-` argument to `cd` and pop/restore a
  tracked "previous cwd" per segment scope (mirroring `$OLDPWD`), rather
  than letting the arg-filter silently drop it.
- **`pushd`/`popd` bypass** (§3 above): `popd` is unrecognized anywhere
  in `_pending_add_segments`/`_shell_segments`; `pushd`'s directory
  change is never undone. Resolution path: track a directory stack
  parallel to (not conflated with) the existing subshell-scope stack,
  and pop it on `popd`.
- **Nonexistent-`cd`-target bypass under `;`** (§3 above): the parser
  never checks `os.path.isdir(target)` before adopting a `cd` target.
  Resolution path: check the target directory actually exists (relative
  to the same repo checkout the guard already has on disk) before
  updating the stack; on a nonexistent target, leave the stack
  unchanged (mirroring real bash's own failed-`cd` behavior) instead of
  blindly trusting the string.
- **Symlink-`cd` bypass** (§3 above): `os.path.normpath` never resolves
  symlinks. Resolution path: `os.path.realpath` the target (or resolve
  it relative to the repo root the same way `git status`'s own
  untracked-path output already is) before storing it on the stack.
- Recommend one follow-up issue covering all four, scoped to this same
  `cd`/`pushd` branch — narrower than #2757's sibling-hook scope, and a
  continuation of the same gap class. canonical:
  `docs/issue-2705/reports/adversarial-review-249cc937.md` and
  `.../adversarial-review-e4ba953e.md`, both read at session start —
  each already recommended "track an effective cwd across `cd`/`pushd`
  segments" as the resolution path for the original gap, without
  anticipating these four sub-cases.
- The three previously-reported shapes (`cd`/subshell path resolution,
  directory-add, `:(exclude)` false refusal): canonical: §1-§2 above
  (this session's own live-fire and stash-revert transcripts) —
  confirmed fixed and correctly pinned; no open finding here.
- The sibling-hook enumeration (issue #2757) and the "no new bug"/
  overhead/monitor invariants: re-derived below under "Standing
  invariants", all hold; no discrepancy from the PR's own claims.

## Next steps

None for this record; `loop_state: landed`. canonical: this record's own
verdict (frontmatter above, backed by §1-§3's live-fire transcript and
ground-truth comparisons) — recommend PR #2763 go back for one more
round fixing the four `cd`/`pushd`-branch gaps in "Open findings" above
before issue #2705 is treated as closed, the same "assume more remain"
premise that sent PR #2753 back once already applying here, one layer
down in the new code.

## Standing invariants

1. **No return of the retired role axis in any reshaped form.**
   derived: `git diff 1d6e746c f943d3fc -- on-the-record/hooks/gate-registration-guard.sh test/test_gate_registration_guard_bundled_add_commit.py | grep -ic role`
   — result: `0`.

2. **No new bug — failing-test-NAME set vs `origin/main`, not counts.**
   canonical: `python3 -m pytest test/ gates/ -q`, run in a fresh
   worktree of the PR head (`f943d3fc`) — result:
   ```
   15 failed, 450 passed, 3 xfailed
   ```
   run again in a separate worktree of `origin/main` (`1d6e746c`) —
   result:
   ```
   15 failed, 430 passed, 3 xfailed
   ```
   Both counts match the PR's own claimed numbers exactly. derived:
   `grep "^FAILED" <pytest output> | awk '{print $2}' | sort` on both
   worktrees' output, then `diff` of the two sorted 15-line name lists —
   result: empty diff (byte-identical sets). This PR introduces zero new
   failing test names.

3. **No overhead increase.**
   canonical: `du -sb on-the-record/directive`, run in the PR-head
   worktree — result: `53162`, matching the stated baseline exactly.
   derived: `git diff 1d6e746c f943d3fc --stat -- on-the-record/directive`
   — result: empty (directory untouched by this diff).
   Re-measured the added parse cost directly (5 runs each, live-fire
   harness against `/tmp/probe2763`):
   ```
   existing bundled-add case (no cd, no exclude):
     git add gates/overhead_probe.py && git commit -m x
     -> 0.142, 0.072, 0.078, 0.089, 0.085 s
   worst-case new path (subshell cd + exclude pathspec together):
     (cd gates && git add . ':(exclude)overhead_probe.py') && git add unrelated_overhead.md && git commit -m x
     -> 0.067, 0.101, 0.086, 0.068, 0.075 s
   ```
   Both bands overlap (~0.07-0.09s median either way) — the PR's claim of
   "no measurable overhead beyond the existing bundled-add `git status`
   call" holds under independent re-measurement; the new cwd-stack/
   exclude-subtraction logic itself adds no separate subprocess call.

4. **Monitor/watch machinery unbroken and not quieter.**
   derived: `git diff 1d6e746c f943d3fc --stat` — result: 4 files touched
   (this PR's own record, its deviation-log entry,
   `gate-registration-guard.sh`, and the test file);
   `git diff 1d6e746c f943d3fc --stat | grep -i 'monitor\|watch'` —
   result: empty (grep exit 1, no match).

## What did not work

A baseline-selection correction mid-review, not a finding about the code
under review: my first attempt at re-deriving the "fail-before/pass-after"
claim (§2 above) used `main`'s own tip (`1d6e746c`) as the "pre-fix"
guard script. canonical: `git show 1d6e746c:on-the-record/hooks/gate-registration-guard.sh
| grep -c _pending_add_segments` (this session) — result: `0` — that
baseline has zero `_pending_add_segments` code at all, since PR #2753
itself was never merged, so it tests "no bundled-add parsing
whatsoever," a materially coarser condition than "PR #2753's first cut
minus this PR's three follow-up fixes." Against that wrong baseline, two
of the exclude-pathspec tests appeared to pass pre-fix for the wrong
reason (no parsing at all trivially "allows" everything, matching what
those two tests happen to assert). Caught this before drawing any
conclusion by fetching PR #2753's actual head commit
(`c6068dcf496c11d1423814e22ab9975fb686aff7`, still reachable via `git
fetch origin c6068dcf496c11d1423814e22ab9975fb686aff7`) and re-running
the identical 9-test selection (derived: the two pytest transcripts
quoted in full in §2 above, this session — `7 failed, 2 passed` against
the true first-cut baseline, `9 passed` against the shipped fix) against
that true first-cut baseline instead of the wrong one.

## Skill verdicts

- skill-verdict: adversarial-review — applied: invoked; this session is
  the structurally independent evaluator for PR #2763's own deliverable
  (a separate session from the one that built PR #2763, given only the
  artifact — the PR diff, its test file, and its own record — and
  incentivized to find everything wrong rather than trust the builder's
  claims). Findings above were reached by live-firing the shipped hook
  against real payloads and comparing to real-git ground truth in every
  case, not by reading the diff for plausibility alone (§1-§3 above).
- other mounted skills: not triggered — `work-in-english` matched the
  task-configuration list but this record and every probe script were
  already authored in English throughout; `conformance-review-finding-record`,
  `implementation-audit`, `verify-finding-record`, `premortem`, and
  `technical-feasibility-reversibility-tag` do not apply to an
  adversarial-review-shaped PR verification task (no conformance-review.md
  verdict to record, no builder/evaluator claim-extraction split separate
  from this review itself, no defect-verification.md reproduction outcome
  to record, no pre-commitment plan to pressure-test, no probe-resolution
  reversibility tag to attach).
