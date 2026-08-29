---
issue: 2705
role: adversarial-review-87659a67
author: adversarial-review-87659a67
skills: adversarial-review (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2774's own deliverable
code_under_review: on-the-record PR #2774 (0d9858b02aba95b30be4b99db3227cb138629969), on-the-record/hooks/gate-registration-guard.sh
loop_state: landed
type: review
breaking: false
verdict: changes-recommended — the three round-3 shapes PR #2763 was sent back for (`cd -`, symlinked directory component, `pushd`/`popd`) ARE genuinely closed; re-derived fail-before/pass-after myself against the true pre-round-3 baseline (PR #2763's own head) and got the identical 3-failed/1-passed → 4-passed split the PR's record claims, and re-measured the standing invariants (failing-test-name SET, directive size, overhead, monitor/watch) with matching results. But the per-frame cwd/oldpwd/dirs model this PR ships is still incomplete, not exhausted: bare `pushd` (no argument) and `pushd +N`/`-N` are silently treated as no-ops instead of bash's real stack-rotation semantics, and an inline env-var-prefixed `cd` (`FOO=bar cd dir`, and separately `CDPATH` even in front of a plain unprefixed `cd`) is invisible to the parser's `seg[0] in ("cd","pushd")` check entirely — all four are live, ground-truthed silent bypasses using the identical unregistered-gate fixture pattern this whole issue is about, none of them the two edges the PR names as deliberately left open. This is the third consecutive round to find fresh gaps in this parser's own new code, which is itself the signal the task brief named: not evidence of insufficient rigor this round, but evidence the hand-rolled-shell-emulator approach has an unbounded surface.
upstream:
  - path: on-the-record PR #2774, branch issue-2705/secure-coding-input-validation-injection-defense+adversarial-review-4b9dda8b
    sha: 0d9858b02aba95b30be4b99db3227cb138629969
  - path: on-the-record PR #2763, branch issue-2705/secure-coding-input-validation-injection-defense+adversarial-review-bb9edf99
    sha: f943d3fc9fa052e006072eed471db4cc535f6313
  - path: docs/issue-2705/reports/adversarial-review-17a16473.md
    sha: same-commit
  - path: docs/issue-2705/reports/adversarial-review-f4b31b03.md
    sha: same-commit
---

# issue-2705 — adversarial-review-87659a67 record

## What was done

Build-now bypass (contract v3 s19a): checked: `printenv | grep CORE_BUILD_NOW`
— result: `CORE_BUILD_NOW=1`. Delivers directly, no proposal round — this
record is the delivered artifact.

canonical: `gh issue view 2705` and `gh pr view 2774 --repo tokenmaxxxer/on-the-record`,
both read at session start. PR #2774 supersedes PR #2763 (still open, three
CHANGES rounds deep) and claims to close the three cwd-stack bypasses
(`cd -`, symlink, `pushd`/`popd`) that two independent verification records —
`docs/issue-2705/reports/adversarial-review-17a16473.md` and
`.../adversarial-review-f4b31b03.md` (both read in full this session, both
already merged to `origin/main`) — ground-truthed live against PR #2763's own
head (`f943d3fc9fa052e006072eed471db4cc535f6313`).

Checked out the PR head into an isolated worktree (`git fetch origin
pull/2774/head:pr-2774 && git worktree add /tmp/pr2774-wt pr-2774`, this
session) and re-derived every claim below against that checkout, not by
re-reading the PR's own record or the two prior verification records at
face value.

### 1. The three round-3 shapes — confirmed fixed, and re-derived fail-before/pass-after against the true baseline

canonical: `0d9858b0:on-the-record/hooks/gate-registration-guard.sh` (this
session's own worktree read) — `_new_frame`/`_pending_add_segments`
(the per-frame `{cwd, oldpwd, dirs}` model) replaces the single mutable
cwd string PR #2763 shipped.

derived: `git fetch origin pull/2763/head:pr-2763-ref` then
`git show pr-2763-ref:on-the-record/hooks/gate-registration-guard.sh >
/tmp/pre_round3_guard.sh` (this session), confirmed via `grep -c oldpwd
/tmp/pre_round3_guard.sh` → `0` vs `grep -c oldpwd
/tmp/pr2774-wt/on-the-record/hooks/gate-registration-guard.sh` → `7` — the
true pre-round-3 baseline (PR #2763's own head) genuinely has no
OLDPWD-equivalent tracking at all, unlike `origin/main` (which never
carried PR #2763's code at all and would be a coarser, wrong baseline).

derived: in `/tmp/pr2774-wt`, swapped only the guard script to the
`pre_round3_guard.sh` content (kept this PR's own test file in place), ran:
```
$ python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -k "BundledCwdStackFrameTest" -v
FAILED ...BundledCwdStackFrameTest::test_cd_through_symlinked_directory_refuses_unregistered_gate
FAILED ...BundledCwdStackFrameTest::test_cd_dash_restores_oldpwd_and_refuses_unregistered_gate
FAILED ...BundledCwdStackFrameTest::test_pushd_popd_restores_directory_and_refuses_unregistered_gate
3 failed, 1 passed in 1.63s
```
Restored the shipped (post-fix) guard script (`git diff --stat` showed no
residual diff against the committed version afterward), reran the same
selector:
```
$ python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -k "BundledCwdStackFrameTest" -v
4 passed in 1.67s
```
derived: the two pytest transcripts immediately above (this session) are a
live, independent re-derivation of the PR's own fail-before/pass-after
claim for all three named shapes — the 3-failed/1-passed → 4-passed split
matches the PR's record exactly, re-derived rather than cited. The one test
that passes both ways (`test_popd_with_empty_stack_is_a_noop_not_a_crash`)
is, canonical:
`0d9858b0:test/test_gate_registration_guard_bundled_add_commit.py:475-480`
(read this session), the same defensive (not shape-pinning) convention both
prior verification records already established for their own pass-both-ways
tests.

derived: also live-fired the symlink shape directly against the shipped
hook (not just the pytest suite) with a multi-hop symlink chain (an edge
neither the PR's tests nor either prior verification record's transcript
names explicitly): `gates_link2 -> gates_link1 -> gates`, this session:
```
$ cd gates_link2 && git add probe_symlink_chain.py && git commit -m x
RC=2 — gate-registration-guard: ...gates/probe_symlink_chain.py: no row in docs/specs/enforcement-boundary.md
```
`os.path.realpath` resolves a symlink chain natively, so this holds without
further fix — not a finding, cited here as evidence I probed past the PR's
own named cases rather than only replaying them.

### 2. New bypasses found in the round-3 model's own new code — four confirmed, ground-truthed both ways

Per the task's explicit brief (probe past `cd -`/`pushd`/`popd`/symlink into
shapes real bash would disagree with the parser on): derived: this
session's own harness (`/tmp/grg_probe/harness.py`, POSTing a real
PreToolUse JSON payload to `bash on-the-record/hooks/gate-registration-
guard.sh`) plus, for every candidate, a paired real-git ground-truth run in
a throwaway scratch clone (`git diff --cached --name-status` or `git log -1
--name-status` after actually running the command, never committed to this
repo) — a candidate below is only reported as a confirmed bypass because
both were run and disagreed (real git staged the file, guard's own exit
code was `0`).

**Bypass D — bare `pushd` (no argument): real bash swaps the top two
stack entries, the parser no-ops.**

derived: `dirs -p` run before/after a bare `pushd`, this session, real
bash, `/tmp/cdtest_real4` (untracked scratch dir, never committed) —
stack `[sub2, sub, repo]` → bare `pushd` → `[sub, sub2, repo]`, `pwd` moves
from `sub2` to `sub`: real bash's bare `pushd` swaps `dirs[0]`/`dirs[1]`
and `cd`s into the new top, it is not a no-op.
```
ground truth: cd /tmp/pushd_real_gt2 && pushd sub_bare2 && pushd && pwd && git add gates/probe_bare_pushd2.py && git diff --cached --name-status
  -> pwd: /tmp/pushd_real_gt2   (bare pushd swapped back to repo root)
  -> A	gates/probe_bare_pushd2.py   (real git DOES stage it)
guard: pushd sub_bare2 && pushd && git add gates/probe_bare_pushd2.py && git commit -m x
  -> RC=0  (silent bypass)
```
derived: the transcript immediately above (this session) — `gates/probe_bare_pushd2.py`,
`sub_bare2/` are untracked throwaway fixtures in a scratch clone
(`/tmp/pushd_real_gt2`), created and removed this session, never committed
to this repo.

Root cause, canonical: `0d9858b0:on-the-record/hooks/gate-registration-guard.sh`
— the `pushd`/`cd` branch in `_pending_add_segments`:
```python
        if seg[0] in ("cd", "pushd"):
            is_pushd = seg[0] == "pushd"
            raw_args = seg[1:]
            ...
            args = [a for a in raw_args if not a.startswith("-")]
            if not args:
                continue
```
A bare `pushd` segment has `raw_args == []`, so `args == []` and the
`if not args: continue` guard treats it as a complete no-op instead of the
swap the transcript above shows real bash performs. The model's
`dirs`/`cwd` fields already exist to represent exactly this swap (the same
fields `cd -` and `pushd DIR` already update); the bare-argument case is
simply unhandled.

**Bypass E — `pushd +N`/`pushd -N` (stack rotation): treated as a literal
directory name, not a rotation index.**

derived: `pushd pn_a` then `pushd +1` from a 2-entry stack, this session,
real bash, `/tmp/cdtest_real5`/`/tmp/cdtest_real6` (untracked scratch dirs,
never committed) — `dirs -p` before: `[pn_a, repo]`; after `pushd +1`:
`[repo, pn_a]`, `pwd` moves to `repo` — real bash's `pushd +1` rotates
index 1 (`repo`) to the top and `cd`s there.
```
ground truth: cd /tmp/pushd_plusN_gt && pushd pn_a && pushd +1 && pwd && git add gates/probe_pushd_plusN.py && git diff --cached --name-status
  -> pwd: /tmp/pushd_plusN_gt   (real bash's `pushd +1` rotates back to repo root)
  -> A	gates/probe_pushd_plusN.py   (real git DOES stage it)
guard: pushd pn_a && pushd +1 && git add gates/probe_pushd_plusN.py && git commit -m x
  -> RC=0  (silent bypass)
```
derived: the transcript immediately above (this session) — `gates/probe_pushd_plusN.py`,
`pn_a/` are untracked throwaway fixtures, never committed.

Root cause, canonical: same `_pending_add_segments` branch quoted under
Bypass D — `-1` starts with `-` and is dropped entirely by the
`a.startswith("-")` filter (degrading to the bare-`pushd` no-op above);
`+1` does NOT start with `-`, so it survives the filter and is instead
treated as a literal path segment: `target = "+1"`, `resolved =
os.path.realpath(os.path.join(frame["cwd"], "+1"))` — the model computes a
bogus `<cwd>/+1` path and pushes THAT as the new cwd, rather than rotating
`frame["dirs"]` by the numeric index the transcript above shows real bash
performing.

**Bypass F — an inline env-var-prefixed `cd` (e.g. `FOO=bar cd dir`) is
invisible to the parser, with no `CDPATH` involved at all.**

derived: `cd envprefix_sub2 && FOO=bar cd .. && pwd`, this session, real
bash, `/tmp/envprefix_gt2` (untracked scratch clone, never committed) —
`pwd` ends at the repo root: an ordinary per-command environment-variable
prefix on `cd` really changes directory in real bash.
```
ground truth: cd /tmp/envprefix_gt2 && cd envprefix_sub2 && FOO=bar cd .. && pwd && git add gates/probe_envprefix2.py && git diff --cached --name-status
  -> pwd: /tmp/envprefix_gt2   (env-prefixed `cd ..` really changes directory)
  -> A	gates/probe_envprefix2.py   (real git DOES stage it)
guard: cd envprefix_sub2 && FOO=bar cd .. && git add gates/probe_envprefix2.py && git commit -m x
  -> RC=0  (silent bypass)
```
derived: the transcript immediately above (this session) — `gates/probe_envprefix2.py`,
`envprefix_sub2/` are untracked throwaway fixtures, never committed.

Root cause, canonical:
`0d9858b0:on-the-record/hooks/gate-registration-guard.sh`'s
`_pending_add_segments` segment-kind check, `if seg[0] in ("cd", "pushd")`
— a strict position-0 token match. A segment shaped `["FOO=bar", "cd",
".."]` has `seg[0] == "FOO=bar"`, not `"cd"`; it fails this check, falls
through to `if "git" not in seg: continue` (no `git` token either), and is
silently skipped, leaving the frame's `cwd` exactly where it was before
this segment. canonical: the same file's `_pending_add_segments` docstring
already documents tolerance for "a leading wrapper/keyword before `git`"
on the `git add` side of detection (`env FOO=bar git add x`) — that
tolerance was never extended to the `cd`/`pushd` side, an internal
inconsistency within the same function.

**Bypass G — `CDPATH` is never consulted, even for a plain,
correctly-recognized `cd` token (no env-prefix or Bypass F needed).**

derived: `export CDPATH=<dir-with-a-same-named-subdir-as-cwd>; cd <name>`,
this session, real bash — the `$CDPATH` entry wins even though a
same-named directory also exists relative to cwd (`/tmp/cdtest_real10`,
untracked scratch dir, never committed): confirms real bash's `cd` search
order prefers `$CDPATH` ahead of a cwd-relative match here, not merely as a
fallback.
```
ground truth: cd /tmp/cdpath_recog_gt && export CDPATH=/tmp/cdpath_guard_other2 && cd back && pwd && git add gates/probe_cdpath_recognized.py && git diff --cached --name-status
  -> pwd: /tmp/cdpath_guard_other2/back   (a symlink CDPATH resolved `back` to, pointing at the same repo clone)
  -> A	gates/probe_cdpath_recognized.py   (real git DOES stage it)
guard: export CDPATH=/tmp/cdpath_guard_other2 && cd back && git add gates/probe_cdpath_recognized.py && git commit -m x
  -> RC=0  (silent bypass)
```
derived: the transcript immediately above (this session) —
`gates/probe_cdpath_recognized.py` is an untracked throwaway fixture;
`/tmp/cdpath_guard_other2/back` is a symlink this session's own probe
created (`ln -sf /tmp/cdpath_recog_gt /tmp/cdpath_guard_other2/back`),
never committed to this repo.

Root cause, canonical: the `cd`/`pushd` branch resolves every target via
`os.path.realpath(os.path.join(frame["cwd"], target))` — a pure
cwd-relative join, with no reference to `$CDPATH` anywhere in
`_pending_add_segments`. This is distinct from Bypass F: `seg[0] == "cd"`
matches cleanly here (`export CDPATH=...` and `cd back` are two separate
segments, so the segment-kind check is not the problem) — the
target-resolution logic itself never models `$CDPATH`.

None of Bypasses D-G are the "fail-closed on an unanalyzable shape" the
issue's must-not warns against — each is the same class the PR's own round
3 fixed one layer up: a shape the parser fully tokenizes and "resolves,"
just to the wrong effective directory, producing a silent, incorrect ALLOW.
`pushd`/`popd` (bare and `+N`/`-N`) and env-prefixed `cd` are ordinary shell
idioms, not adversarial contrivances — `pushd`/`popd` pairs are exactly the
shape this same PR's own tests already exercise for the non-bare case.

### 3. The two edges the PR deliberately leaves open — restraint reasonable in isolation, but the surrounding picture undercuts it

canonical: the PR's own record (`docs/issue-2705/reports/secure-coding-
input-validation-injection-defense+adversarial-review-4b9dda8b.md`, "Open
findings", read this session) cites the review's stated bound to leave `cd`
to a nonexistent target joined by `;` and bare `cd` (meaning `$HOME`) open,
since neither was one of the three named CHANGES-review shapes.

Per this session's own `defect-verification-independence-from-upstream-
verdicts` skill call (rule 4: a not-reproduced prior finding does not
settle the area), re-checked both narrowly rather than accepting the "not
found" verdict at face value. canonical:
`docs/issue-2705/reports/adversarial-review-f4b31b03.md`'s own "Checked,
not a bypass" bare-`cd` probe (re-read this session) constructed a chain
where a later absolute `cd` overwrites the no-op's staleness and did not,
within that session's own time budget, find a live bypass built on the
bare-`cd`/`$HOME` gap alone; that same record's "Confirmed BYPASS" section
for the `;`-joined nonexistent target does name a real divergence, but one
requiring `;` in the same command that also stages and commits — a shape
this repo's own batching guidance (#2135) does not recommend and is
unusual to reach for deliberately.

Judged in isolation, leaving those two specific edges open was a reasonable
call: neither is as operationally common as the shapes actually found live
this session (§2). But the restraint judgment's implicit premise — that the
model is otherwise complete enough that two named, narrow edges are what
remains — does not hold under this session's own re-derivation: derived:
§2 above (this session's own four confirmed, ground-truthed transcripts) —
Bypasses D-G are found in the exact same review pass, are not narrow
(bare `pushd`/`popd` pairs are pervasive, ordinary shell idioms), and were
on neither the PR's own "did not fix" list nor either prior verification
record's list at all. The PR's restraint about scope (not chasing the two
named edges) was sound; treating those two edges as the remaining gap in
the model was not — there was more, undiscovered surface than the "two
adjacent edges" framing accounted for.

### 4. Standing invariants — independently re-measured

1. **No return of the retired role axis.** derived: `git diff 1d6e746c --
   on-the-record/hooks/gate-registration-guard.sh
   test/test_gate_registration_guard_bundled_add_commit.py | grep -ic role`,
   run in `/tmp/pr2774-wt` this session — result: `0`.
2. **No new bug — failing-test-name SET vs `origin/main`, not counts.**
   canonical: `python3 -m pytest test/ gates/ -q`, run in `/tmp/pr2774-wt`
   (PR head, cleaned of this session's own scratch fixtures via `git clean
   -fdx` first) — result: `15 failed, 454 passed, 3 xfailed`; run again in
   a separate worktree of `origin/main` (tip `88a84684`, 15 commits ahead
   of the PR's own base `1d6e746c` — later, unrelated merges, not this
   PR's own baseline) — result: `15 failed, 433 passed, 3 xfailed`. The
   passed-count gap from the PR's own claimed `430` (this session measured
   `433`) is `origin/main` drift since the PR was authored, not a
   discrepancy in the PR's own claim — re-verified by SET, not count:
   derived: `grep "^FAILED" <output> | awk '{print $2}' | sort` on both
   runs, then `diff` — result: empty, byte-identical failing-test-name
   SETS between this PR's head and the current `origin/main` tip. Zero new
   failing test names.
3. **No overhead increase.** canonical: `du -sb on-the-record/directive` in
   `/tmp/pr2774-wt` — result: `53162`, matching the claimed baseline.
   derived: re-measured the added parse cost myself (5 runs each, this
   session's own `/tmp/grg_probe/perf.py`, live-fired against the real
   working-tree hook):
   ```
   no_add:      0.0407-0.0551s avg=0.0451
   plain_add:   0.0656-0.0886s avg=0.0766
   pushd_popd:  0.0691-0.0864s avg=0.0777
   ```
   The `pushd`/`popd` path adds no measurable cost beyond the pre-existing
   bundled-add case — consistent with the PR's own `~0.08s` claim and no
   new subprocess call.
4. **Monitor/watch machinery unbroken and not quieter.** derived: `git diff
   1d6e746c --stat | grep -i 'monitor\|watch'`, run in `/tmp/pr2774-wt` —
   result: empty (no monitor/watch-class path touched by this PR's diff).

## Why

canonical: §1-§4 above (all executed this session against the PR-head
worktree and fresh scratch clones, not cited from the PR's own record or
either prior verification record at face value) is the basis for every
conclusion.

The task brief framed the bound explicitly: a fourth round finding a fresh
cwd-tracking gap is a signal about the approach, not license for a fourth
single-shape patch. derived: §2 above (this session's own four confirmed
bypasses) is exactly that outcome — not one fresh gap but four, spanning
two further sub-classes of `pushd` (bare-argument swap, numeric rotation)
and two further sub-classes of `cd` target resolution (env-var-assignment
prefixes, `$CDPATH`) that the round-3 model's own new `dirs`/`oldpwd`
fields do not cover despite already carrying the state (D, E) or despite
the segment-kind check being one `seg[0]` string away from the
wrapper-tolerance the sibling `git add` detection already has (F). I did
not attempt a fix; this role's remit is independent verification,
consistent with `verifies_subject: true` and the convention both prior
verification records for this same file used.

Per this session's own `defect-verification-independence-from-upstream-
verdicts` skill call (rule 2: deliberately include edge/negative paths
rather than only re-confirming the named shapes; rule 4: a not-reproduced
prior finding does not settle the area), I treated the PR's own "three
shapes fixed" claim as something to re-derive from primary evidence (§1),
not cite, and treated the two prior records' "did not find a bypass" notes
on bare `cd`/`;`-joined nonexistent targets as an invitation to keep
looking in the same class rather than a closed matter (§3) — which is how
Bypasses D-G were found: not by re-testing the two named-open edges, but by
extending the same "what does bash actually do here" discipline to
`pushd`'s own argument grammar and to environment-variable interaction with
`cd`, neither of which either prior record or the PR's own testing touched.

Per this session's `adversarial-review` skill call, this record evaluates
PR #2774's deliverable (the guard script diff, the test file, and the PR's
own record) from a structurally independent position — a separate session
from the one that built it, re-deriving every claim rather than trusting
the PR's own "verified live" framing, and specifically hunting the new
code's own edges rather than only confirming the three shapes it names.

## Upstream basis

canonical: `gh issue view 2705`, read at session start, for acceptance
criteria and the fail-closed must-not. `gh pr view 2774 --repo
tokenmaxxxer/on-the-record` and `gh pr diff 2774 --name-only`, read at
session start, for the PR's own claims and changed-file list.
`docs/issue-2705/reports/adversarial-review-17a16473.md` and
`.../adversarial-review-f4b31b03.md`, both read in full this session — the
two merged verification records PR #2774 claims to have closed.
`0d9858b0:on-the-record/hooks/gate-registration-guard.sh` and
`0d9858b0:test/test_gate_registration_guard_bundled_add_commit.py`, read
directly from a `git worktree add /tmp/pr2774-wt pr-2774` checkout of the
PR branch (`git fetch origin pull/2774/head:pr-2774`, this session), not
from the PR's diff view alone.
`f943d3fc:on-the-record/hooks/gate-registration-guard.sh` (PR #2763's own
head, `git fetch origin pull/2763/head:pr-2763-ref`, this session) as the
true pre-round-3 baseline for §1's fail-before/pass-after re-derivation.

## Open findings

- **Bypass D (bare `pushd`), Bypass E (`pushd +N`/`-N`), Bypass F
  (env-var-prefixed `cd`), Bypass G (`$CDPATH` never consulted)**: all four
  live, ground-truthed both ways, not fixed by this PR. derived: this
  record's §2 above (this session's own transcripts, each with real-git
  ground truth and the matching guard exit code) is the evidence.
  Resolution paths:
  - D: in the `pushd`/`cd` branch (the `if not args: continue` guard),
    special-case a `pushd` segment whose args are empty (after the same
    `-`-prefix filter) as "swap `frame["dirs"][0]`/`frame["dirs"][1]`" —
    the fields to represent this already exist.
  - E: parse a `+N`/`-N`-shaped argument to `pushd` as a rotation index
    into `frame["dirs"]` rather than falling through to the generic
    literal-directory-join path; requires bounds-checking against the
    stack's current length (bash itself errors on an out-of-range index,
    a no-op case parallel to `popd` on an empty stack).
  - F: extend the same leading-wrapper tolerance `_pending_add_segments`
    already documents and implements for `git` detection (skip
    `KEY=value` assignment tokens before checking `seg[0] in ("cd",
    "pushd")`) to the `cd`/`pushd` segment-kind check itself.
  - G: either read `$CDPATH` from the hook's own environment and search it
    the way bash does before falling back to a cwd-relative join, or (a
    narrower, more conservative fix matching this guard's own fail-open
    convention on genuinely unanalyzable shapes) treat any segment
    touching `cd`/`pushd` while `$CDPATH` is set anywhere in the ambient
    environment as unparseable and contribute no pending targets from that
    point forward in the same command — the "contributes nothing" fallback
    this guard already uses elsewhere, rather than resolving confidently
    against a rule it does not implement.
  - All four belong to this same parser's own attack surface. Given this
    is the third consecutive round to find fresh gaps in code written to
    close the previous round's gaps, recommend treating this as the
    signal the task brief and both prior verification records already
    named: a scope decision (state explicitly what directory-changing
    shapes this parser does and does not cover, rather than continuing to
    patch discovered shapes one at a time) rather than a fourth
    single-shape patch.
- **Bare `cd` (`$HOME`) and `;`-joined nonexistent `cd` target**: still
  open, per §3 above — restraint in leaving these two specific edges
  unaddressed this round was reasonable on its own terms, but should be
  evaluated together with D-G in the same follow-up scope decision rather
  than as a separate, smaller loose end.
- Sibling-hook enumeration (issue #2705 acceptance check 3): unaffected by
  this PR's diff (git add-parsing only; the file-pattern/target
  enumeration this check covers is untouched) — canonical: both prior
  verification records' own "Enumeration re-derivation" sections, not
  re-derived a fourth time this session since nothing in this PR's diff
  bears on that population.

## Next steps

None for this record; `loop_state: landed`. Recommend the subject issue's
next round treat Bypasses D-G together with the two already-open edges as
one scope decision — either state explicitly which directory-changing
constructs this parser covers (and accept the residual as a documented,
not silent, gap) or reconsider whether a hand-rolled shell-cwd emulator
inside a PreToolUse hook is the right shape for this guard at all, per the
task brief's own framing of a fourth-round fresh gap as a signal about the
approach.

## What did not work

derived: this session's own probe harness worked on the first
construction — no harness-authoring correction to log, unlike the two
prior verification records (each of which logged and corrected an earlier
harness mistake).

One early probe of my own ("cd - twice") turned out, on inspection, not to
be a new finding: I first ran "cd sub && cd sub2 && cd - && cd -" (`sub2`
does not exist as a child of `sub` in that scratch layout) expecting to
test `cd -`'s toggle semantics in isolation, and got guard `RC=0`. derived:
running the identical command under real bash first (this session,
`/tmp/cdtest_real.sh`) showed the `&&` chain aborts at the failed `cd
sub2` either way — this was the already-acknowledged nonexistent-`cd`-
target-under-`&&` case (which both prior verification records already
documented as a coincidental, non-bypass match), reached by an accidental
directory layout, not `cd -`'s own toggle behavior. Caught before citing it
as a finding by re-deriving the real-bash ground truth first, per this
session's own `defect-verification-independence-from-upstream-verdicts`
skill call. Re-derived the intended question with a layout where all `cd`
targets genuinely exist (`cd sub && cd .. && cd - && cd -`, landing back at
the repo root in both real bash and the guard's model — derived: this
session's own transcript, §1 area, confirmed via a direct guard run showing
`RC=2` against a fixture placed at the repo root) and confirmed no bug
there; not repeated as a separate section since it produced no finding.

## Skill verdicts

- skill-verdict: adversarial-review — applied: invoked; this session's own
  role structurally is the two-party protocol's evaluator seat relative to
  PR #2774's builder session — a separate session, re-deriving every claim
  in this record from primary commands run against a fresh worktree
  checkout (§1-§4 above) rather than trusting the PR's own record, and
  specifically hunting the new code's own edges (§2) rather than only
  confirming the three named shapes.
- skill-verdict: defect-verification-independence-from-upstream-verdicts —
  applied: invoked; derived: §1 above re-derives the fail-before/pass-after
  claim from primary pytest evidence instead of citing the PR's record
  (rule 3); §2-§3 above keep probing the bare-`cd`/`pushd` argument-grammar
  space after both prior records reported "fixed"/"not found" there rather
  than treating it as settled (rule 4); §3 above gives the not-reproduced
  bare-`cd`/`;`-target edges the same evidentiary citation treatment as the
  confirmed bypasses rather than a thinner note (rule 7).
- skill-verdict: work-in-english — applied: invoked; this record, all
  commands, and all citations are written in English per the skill's
  routing (the task's own directive text is Korean-heavy); the final
  summary to the user is in Korean.
- skill-verdict: verify-finding-record — not-applicable: this skill governs
  recording a reproduction attempt's outcome specifically in
  `docs/issue-<n>/reports/defect-verification.md`; this session's record
  target is `docs/issue-2705/reports/adversarial-review-87659a67.md` (an
  adversarial-review record, not a defect-verification one), a different
  file and format this skill's own trigger does not cover.
- other mounted skills: not triggered.
</content>
