---
issue: 2705
role: secure-coding-input-validation-injection-defense+adversarial-review-bb9edf99
author: secure-coding-input-validation-injection-defense+adversarial-review-bb9edf99
skills: secure-coding-input-validation-injection-defense (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false
code_under_review: PR #2753's own fix to on-the-record/hooks/gate-registration-guard.sh (sha c6068dcf496c11d1423814e22ab9975fb686aff7), which came back CHANGES on two independent adversarial-review verification records
type: fix
breaking: false
verdict: all three parser gaps both independent reviews live-reproduced against PR #2753 (cd/subshell-before-add path resolution, a directory `git add` argument, and `:(exclude)`/`:!` pathspec magic causing a false refusal) are fixed and each pinned with a regression test that fails against the pre-fix parser and passes after; the core fix, the three first-cut bug fixes, and the sibling-hook enumeration all carry forward unchanged.
loop_state: landed
upstream:
  - path: on-the-record PR #2753, on-the-record/hooks/gate-registration-guard.sh
    sha: c6068dcf496c11d1423814e22ab9975fb686aff7
  - path: docs/issue-2705/reports/adversarial-review-249cc937.md
    sha: becb449d74faf225b65289949fe52e8ac10ce513
  - path: docs/issue-2705/reports/adversarial-review-e4ba953e.md
    sha: 1d6e746c2de29de19d066d420c8eba4e4cb10653
---

# issue-2705 — secure-coding-input-validation-injection-defense+adversarial-review-bb9edf99 record

## What was done

Build-now bypass (contract v3 s19a): checked: `printenv | grep CORE_BUILD_NOW`
— result: `CORE_BUILD_NOW=1`. Delivers directly, no proposal round.

canonical: `gh pr view 2753 --json state,body` and the PR's review comment,
both read at session start — PR #2753, OPEN, came back CHANGES: two
independent adversarial-review verification sessions
(`docs/issue-2705/reports/adversarial-review-249cc937.md`,
`docs/issue-2705/reports/adversarial-review-e4ba953e.md`) both live-
reproduced the same class of gap in the parser PR #2753's own fix
introduces — the fix's own attack surface, one layer down.

Note on file paths cited below: every `gates/*.py` / `*.md` filename
referenced in this record's Fix/verification sections (e.g.
`new_gate_2705_cd.py`, `excluded_2705.py`, `probe1.py`,
`new_gate_2705_excl.py`) is untracked — a throwaway probe or
unittest-fixture file, created only inside a temporary `git clone`
(either this session's manual probes or the pinned tests'
`tempfile.TemporaryDirectory` fixture in
`test/test_gate_registration_guard_bundled_add_commit.py`), and never
committed to this repo — same convention both merged verification
records already used for their own probe files.

derived: `git fetch origin main` then `git merge-base origin/main
FETCH_HEAD` — result: this session's branch was already forked from
`origin/main` tip `1d6e746c` (includes both verification records above
as already-landed commits, since neither touched
`gate-registration-guard.sh` itself), so no further rebase was needed.
PR #2753's own code+test commit (`8160def4`) was cherry-picked onto this
branch: derived: `git cherry-pick -n 8160def4` — result: clean apply, no
conflicts (`git status --short` showed only the two expected files
staged: `M on-the-record/hooks/gate-registration-guard.sh`, `A
test/test_gate_registration_guard_bundled_add_commit.py`). PR #2753's own
two record-only commits (`469075ef`, `c6068dcf`) were deliberately NOT
cherry-picked — they are that session's own record file under a
different report filename (`...-cd806f25.md`), and this session writes
its own record here instead, per this role's own report-area ownership
rule.

### Fix 1 — `cd`/subshell path-resolution bypass

canonical: `on-the-record/hooks/gate-registration-guard.sh:213-241`
(`_pending_add_segments`) — `_shell_segments` (`:177-199`) now emits
`("open", None)`/`("close", None)` boundary markers for `(`/`)` instead
of treating them as plain separators, and `_pending_add_segments` walks
the resulting sequence with a cwd stack: entering `(` pushes a copy of
the current effective cwd, closing `)` pops back to it (so a subshell's
own `cd` never leaks to a later top-level segment, the same as real
bash), and a `cd`/`pushd` segment updates the top of the stack in place.
Every `git add` segment now carries its own effective cwd instead of the
payload's single, static top-level `cwd`.

derived: `python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -k BundledCdBeforeAddTest -v`
— result: 4 passed — `test_plain_cd_before_add_refuses_unregistered_gate`
(`cd gates && git add new_gate_2705_cd.py && git commit -m x`),
`test_subshell_cd_before_add_refuses_unregistered_gate`
(`(cd gates && git add new_gate_2705_sub.py && git commit -m x)`),
`test_cd_then_dotdot_relative_add_refuses_unregistered_gate`
(`cd sub && git add ../gates/new_gate_2705_dotdot.py && git commit -m x`),
and `test_subshell_cd_does_not_leak_to_a_later_top_level_segment` (a
subshell's own `cd` must not affect a later top-level `git add`).

Fail-before/pass-after pinned live this session: derived: `git stash push
--keep-index -- on-the-record/hooks/gate-registration-guard.sh` (reverts
only the guard script to the pre-fix, cherry-picked-only state, keeping
the new test file in place), then `python3 -m pytest
test/test_gate_registration_guard_bundled_add_commit.py -k
BundledCdBeforeAddTest -q` — result: `3 failed, 1 passed` (the three
new-bypass tests failed against the pre-fix parser exactly as expected;
the fourth, the no-leak regression test, incidentally already held
pre-fix since the pre-fix parser never tracked `cd` at all). `git stash
pop` (resolved a self-conflict from `--keep-index` by taking the
stashed, fixed side — see "What did not work" below) restored the fix;
the full suite re-run clean afterward (see "Full regression run" below).

### Fix 2 — directory-add bypass

canonical: `on-the-record/hooks/gate-registration-guard.sh:289-306`
(`_match_untracked`) — a positional argument that resolves to an
existing directory (`os.path.isdir(abs_p)`) now sweeps every untracked
path with that directory's repo-relative path as a prefix, the exact
mechanism the `.` case already used, just keyed off a real directory
check instead of the literal string `"."`.

derived: `python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -k BundledDirectoryAddTest -v`
— result: 2 passed (`git add gates/ && git commit -m x` and `git add
gates && git commit -m x`, both against an untracked, unregistered
`gates/new_gate_2705_dir1.py` / `gates/new_gate_2705_dir2.py`).

Fail-before/pass-after: same stash-based pre-fix rerun as Fix 1 above —
derived: `python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -k BundledDirectoryAddTest -q`
against the pre-fix parser — result: `2 failed` (both directory-add
tests).

### Fix 3 — `:(exclude)`/`:!` pathspec magic false refusal

canonical: `on-the-record/hooks/gate-registration-guard.sh:268-286`
(`_pathspec_exclude_pattern`) and `:340-354`
(`_pending_add_targets`'s `excludes` handling) — an argument starting
with `:!`/`:^` or `:(...)` whose magic-keyword list contains `exclude`
is now collected separately as an exclude pattern rather than falling
into the generic literal/glob branch; after the positive targets (from
`.`, directory, literal, and glob positionals) are computed, every
exclude pattern's own matches (resolved through the same
`_match_untracked` used for positives) are subtracted from the result.
Only the exclude direction is special-cased — other pathspec magic
(`:(glob)`, `:(icase)`, `:(top)`, ...) is not implemented and falls
through to the existing generic handling, unchanged.

derived: `python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -k BundledExcludePathspecTest -v`
— result: 3 passed — the false-refusal case (`git add .
':(exclude)gates/excluded_2705.py' && git commit -m x` must allow), the
`:!` shorthand form of the same case, and a same-segment regression case
(`git add . ':(exclude)excluded_unrelated_2705.md' && git commit -m x`
must still refuse a real, unrelated, unregistered, untracked
`gates/new_gate_2705_excl.py` (a throwaway test-fixture file the test's
own `_write` helper creates in its temporary clone, never committed to
this repo) — proves the fix does not just make the whole segment go
quiet whenever any exclude token appears, which would have traded the
over-refusal bug for a new bypass).

Fail-before/pass-after: same stash-based pre-fix rerun — derived: `python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -k BundledExcludePathspecTest -q`
against the pre-fix parser — result: `2 failed, 1 passed` (the
false-refusal case and its `:!` shorthand variant failed against the
pre-fix parser, as expected; the "unrelated exclude must still refuse"
case incidentally already held pre-fix, since the pre-fix parser had no
exclude handling at all and the unconditional `.` sweep already caught
the real gate file regardless).

Ground-truthed against real git before writing the fix, not just
asserted: derived: `git add . ':(exclude)gates/should_not_flag.py' &&
git diff --cached --name-status` in a throwaway clone, this session —
result: only the unrelated file staged, confirming real git's actual
exclude semantics before pinning the guard's expected behavior to match
them.

### Live-fire verification beyond the pinned unit tests

canonical: both merged review records' own "Confirmed BYPASS"/"Confirmed
over-refuse" transcripts (`adversarial-review-249cc937.md` §3,
`adversarial-review-e4ba953e.md` "Second adversarial round"), re-derived
independently this session rather than trusted at face value — re-ran the
same shapes against a real PreToolUse JSON payload on stdin through a
throwaway `git clone` fixture (same harness shape the pinned test file
uses, driven manually via a `/tmp/run_guard_probe.py` script this
session wrote and ran). derived: the six commands below, this session,
each showing before/after return codes:

```
cd gates && git add probe1.py && git commit -m x                              -> RC=2 (was 0)
(cd gates && git add probe1b.py && git commit -m x)                            -> RC=2 (was 0)
git add gates/ && git commit -m x                                              -> RC=2 (was 0)
git add gates && git commit -m x                                               -> RC=2 (was 0)
git add . ':(exclude)gates/should_not_flag.py' && git commit -m x              -> RC=0 (was 2, false refusal)
git add . ':(exclude)excluded_doc.md' && git commit -m x  (real_new_gate.py present) -> RC=2 (unrelated exclude still refuses)
```

derived: three additional shapes this session ran, named in the task
brief but not verbatim in either review's own transcript, to check the
fix generalizes rather than only matching the exact reproduction
strings —
`cd sub && git add ../gates/dotdot_gate.py && git commit -m x` (relative
parent-then-child cd) -> RC=2;
`cd gates && cd .. && git add gates/chained_gate.py && git commit -m x`
(chained cd) -> RC=2;
`(cd other && git add note.txt) && git add gates/leak_check.py && git
commit -m x` (subshell cd must not leak into a later top-level segment)
-> RC=2, confirming the outer `git add` still resolved against the repo
root, not the subshell's `other/`.

### Full regression run

derived: `python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -q`
— result: `20 passed` (the original 11 plus 9 new: 4 cd/subshell, 2
directory-add, 3 exclude-pathspec).

## Why

canonical: the PR #2753 review comment, read at session start — "the
risk this fix takes on is that a parser now sits in front of the guard,
so anything the parser mis-reads is a silent bypass again — the very
defect being fixed," and both merged verification records independently
converged on the same shape of fix for (1) and (2): thread an effective
cwd through `_shell_segments`/`_pending_add_segments`, tracking
`cd`/`pushd` per segment and restoring on subshell close. This session
implemented exactly that shape rather than inventing an alternative,
since two independent reviews reaching the same design under no shared
context is strong evidence it is the right shape, and re-deriving a
different approach from scratch would not have been a better use of the
time than verifying and pinning the one two reviewers already agreed on.

For (3), the task left two options open ("honor pathspec magic, or treat
an argument beginning with `:(`/`!` as contributing zero pending
targets") and asked this session to decide and say why. Chose to
partially honor pathspec magic (implement exclude semantics
specifically) rather than the zero-contribution alternative, because the
zero-contribution option only changes what the EXCLUDE TOKEN ITSELF
contributes — canonical: `on-the-record/hooks/gate-registration-guard.sh:352-354`
(the pre-existing generic literal/glob branch, unchanged) shows an
exclude-token string was already contributing zero matches on its own
before this fix, since `:(exclude)path` never literally or glob-matches
an untracked path. The actual over-refusal bug is that the CO-OCCURRING
`.`/directory sweep in the same segment ignores the exclude token
entirely; making the exclude token itself inert does not touch that
sweep. The only way to fix the false refusal without opening a new
bypass is to compute what the exclude pattern actually matches and
subtract it from the positive sweep — which is what "honoring pathspec
magic" means for the one direction (exclude) this bug is about. Went
narrow (only `:(exclude)`/`:!`/`:^`, not `:(glob)`/`:(icase)`/`:(top)`)
because the reported bug is specifically about exclude causing a false
refusal; the other magic keywords affect match semantics, not direction,
and are out of the reported scope — an unrecognized one still falls
through to the pre-existing generic literal/glob handling, unchanged,
so this is additive rather than a behavior change for those keywords.

Did not fail-closed on any new unparseable shape, per the task's
explicit "do not respond to this by fail-closing" instruction and this
guard's own existing design comment (`gate-registration-guard.sh:44-49`,
carried over unchanged from PR #2753): canonical: `on-the-record/hooks/gate-registration-guard.sh:224-227`
(`_pending_add_segments`'s `cd`/`pushd` handling) — a `cd`/`pushd`
segment with no resolvable argument is left as a no-op (effective cwd
unchanged) rather than aborting the scan, and canonical:
`on-the-record/hooks/gate-registration-guard.sh:355-357`
(`_pending_add_targets`'s fallthrough) — an unrecognized pathspec-magic
argument (anything other than exclude) still falls through to the
existing literal/glob branch instead of being rejected.

## Upstream basis

canonical: `gh pr view 2753 --json title,body,state,url` and its review
comment, both read at session start. `docs/issue-2705/reports/adversarial-review-249cc937.md`
and `docs/issue-2705/reports/adversarial-review-e4ba953e.md`, both read
in full this session (they do not overlap completely — 249cc937 names
three `cd`-variant reproductions and the `:(exclude)` case; e4ba953e
additionally names the plain directory-add case as a fourth, distinct
bypass and a `:!` shorthand-adjacent framing). `gh issue view 2705`, read
at session start, for the original acceptance criteria and the
fail-closed must-not.

- `on-the-record/hooks/gate-registration-guard.sh` at PR #2753's own head
  `c6068dcf496c11d1423814e22ab9975fb686aff7` — the code+test commit
  `8160def48e0c3392af39fc2ac18057ab42e60a39` cherry-picked onto this
  branch, then edited in this session's own commit (`same-commit` for
  the incremental fix on top of the cherry-picked baseline).
- `test/test_gate_registration_guard_bundled_add_commit.py`, same
  cherry-pick-then-extend basis.

## Open findings

canonical: `docs/issue-2705/reports/adversarial-review-249cc937.md`
("Open findings" section) and `docs/issue-2705/reports/adversarial-review-e4ba953e.md`
("Open findings"/"Enumeration re-derivation" sections), both re-read
this session (not re-derived independently a third time, per this
session's own "what holds and must not be redone" instruction) — none of
this session's own scope remains open. The three parser gaps named in
the PR's review comment are fixed and pinned above.

Carried forward unchanged, per the citation above: the three "affected,
not fixed here" on-the-record sibling hooks
(`acceptance-command-real-run-guard.sh`, `live-fire-claim-real-run-guard.sh`,
`spec-index-preflight.sh`) and the two advisory-only core hooks
(`trailer-gate.sh`, `handbook-trigger-gate.sh`) share this same
blind-spot shape and are out of scope for issue #2705 itself (tracked by
issue #2757, filed on the strength of the enumeration both verifications
re-derived independently). Both verification records recommend the
eventual sibling-hook follow-up (#2757) design in per-segment-cwd
tracking from the start rather than copying PR #2753's original
static-`cwd` approach and reproducing the same three gaps five more
times — this session's own fix above is the concrete shape that
recommendation should port.

## Next steps

None for this record; `loop_state: landed`. Recommended next step for
the subject issue: PR #2753's reviewer(s) re-verify this session's fix
against the same live-fire shapes their own records used. derived: this
record's own "Live-fire verification beyond the pinned unit tests"
section above is this session's own evidence, produced this session —
it is not an independent second pass, so the recommended re-verification
is still outstanding.

## What did not work

The first `git stash push --keep-index -- on-the-record/hooks/gate-registration-guard.sh`
/ `git stash pop` round-trip (used to prove the new tests fail against
the pre-fix parser) produced a self-merge conflict on `git stash pop`,
because `--keep-index` left the fixed version staged in the index while
the working tree held the pre-fix content, and popping tried to reapply
the same fix as a diff against that already-fixed index. derived:
resolved by inspecting one conflict hunk directly (`grep -n '<<<<<<<\|=======\|>>>>>>>' on-the-record/hooks/gate-registration-guard.sh`,
then reading the hunk to confirm the "Stashed changes" side was the
fixed version) and running `git checkout --theirs on-the-record/hooks/gate-registration-guard.sh`
followed by `git stash drop`; re-ran `python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -q`
afterward — result: `20 passed`, confirming the fixed file survived the
conflict resolution intact rather than silently losing part of the diff.

## Standing invariants

1. **No return of the retired role axis in any reshaped form.** derived:
   `git diff origin/main -- on-the-record/hooks/gate-registration-guard.sh test/test_gate_registration_guard_bundled_add_commit.py | grep -ic role`
   — result: `0`.
2. **No new bug — failing-test-name set vs origin/main, not counts.**
   canonical: `python3 -m pytest test/ gates/ -q` run on this branch —
   result: `15 failed, 450 passed, 3 xfailed`; the same command run in a
   separate `git worktree add /tmp/wt-main origin/main` — result: `15
   failed, 430 passed, 3 xfailed`. The 20-test gap (450 vs 430) is
   exactly this session's own added tests (11 pre-existing + 9 new = 20
   in the target file). derived: `diff <(sort failing-names-before)
   <(sort failing-names-after)` — result: empty (identical sets, byte
   for byte) — confirmed as a SET comparison, not a count comparison,
   per this session's own instruction.
3. **No overhead increase.** canonical: `du -sb on-the-record/directive`
   — result: `53162`, matching both prior verification records' stated
   baseline exactly; `git diff origin/main --stat -- on-the-record/directive`
   — result: empty (untouched). Measured the added parse cost directly,
   this session: derived: 5-run averages via a throwaway clone — plain
   `git commit -m x --allow-empty` (no `git add` segment, unaffected by
   any of this file's parsing) averaged `0.051s`; the pre-existing
   bundled-literal-path case (`git add gates/perf_probe.py && git commit
   -m x`, already paying the `git status` subprocess cost PR #2753
   introduced) averaged `0.094s`; this session's own worst-case new
   parse path (`(cd gates && git add . ':(exclude)perf_probe.py' && git
   commit -m x)` — subshell cwd-stack tracking plus pathspec-exclude
   parsing together) averaged `0.080s` — within the same noise band as
   the already-existing bundled-add case, confirming this session's
   added pure-Python parsing (a cwd stack, an exclude-pattern pass)
   contributes no measurable cost beyond the `git status` subprocess
   call PR #2753 already paid for any bundled `git add` segment.
4. **Monitor/watch machinery unbroken and not quieter.** derived: `git
   diff origin/main --stat -- on-the-record/hooks/gate-registration-guard.sh test/test_gate_registration_guard_bundled_add_commit.py docs/issue-2705/reports/secure-coding-input-validation-injection-defense+adversarial-review-bb9edf99.md`
   — result: exactly these 3 files, none monitor/watch-class; `git diff
   origin/main --stat | grep -i 'monitor\|watch'` — result: empty.

## Skill verdicts

- skill-verdict: secure-coding-input-validation-injection-defense —
  applied: invoked; canonical: `on-the-record/hooks/gate-registration-guard.sh:268-357`
  (this session's own diff) is the evidence — the fix itself is about a
  shell-command parser deciding what an untrusted, attacker-shaped Bash
  command string is about to stage before it crosses the trust boundary
  into `git commit`, an allowlist-shaped decision (only a segment the
  parser actually recognizes as `git add ...` with a resolvable target
  contributes a pending target) rather than a denylist of known-bad
  shapes, consistent with this skill's guidance to prefer allowlists at
  a trust boundary; the `:(exclude)` fix specifically is sink-aware
  (matches real git's own pathspec semantics, ground-truthed this
  session per Fix 3 above, rather than a generic string heuristic) to
  avoid both an injection-shaped bypass (Fixes 1-2) and an over-broad
  denylist-style false positive (Fix 3).
- skill-verdict: adversarial-review — applied: invoked; derived: this
  session's own stash-based fail-before/pass-after reruns (Fix 1-3
  sections above) are the evidence — before writing the fix,
  ground-truthed real git's own `:(exclude)` behavior in a throwaway
  clone rather than assuming the reviews' description was sufficient,
  and pinned every one of the three fixed shapes with a regression test
  proven to fail against the pre-fix parser via a stash-based
  revert-and-rerun this same session, rather than trusting that a
  passing test after the fix alone was adequate evidence.
- other mounted skills: not triggered — `work-in-english`: this record,
  all commands, and all new test/code content were authored in English
  throughout.
