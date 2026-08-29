---
issue: 2705
role: adversarial-review-f4b31b03
author: adversarial-review-f4b31b03
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2763's own deliverable
code_under_review: on-the-record PR #2763 (f943d3fc9fa052e006072eed471db4cc535f6313), on-the-record/hooks/gate-registration-guard.sh
type: review
breaking: false
verdict: changes-recommended — the three parser gaps PR #2763 was built to close (cd/subshell path resolution, directory add, `:(exclude)` pathspec false refusal) ARE closed; re-derived fail-before/pass-after for all three myself via a stash-based revert against this branch's own pre-fix commit and got the identical 7-failed/2-passed → 9-passed split the PR's record claims. But probing the new cwd-stack and directory-argument parsing itself (this PR's own new attack surface, per the standing risk) found three further live, ground-truthed silent bypasses the PR does not cover — `cd -`, `cd`-through-a-symlink, and `pushd`/`popd` — all reproduced with the identical unregistered-gate fixture the PR's own tests use, each confirmed a real bypass by running the actual bash command for real and checking what git committed, not just reading the guard's exit code in isolation.
loop_state: landed
upstream:
  - path: docs/issue-2705/reports/adversarial-review-249cc937.md
    sha: becb449d74faf225b65289949fe52e8ac10ce513
  - path: docs/issue-2705/reports/adversarial-review-e4ba953e.md
    sha: 1d6e746c2de29de19d066d420c8eba4e4cb10653
  - path: f943d3fc:on-the-record/hooks/gate-registration-guard.sh
    sha: f943d3fc9fa052e006072eed471db4cc535f6313
---

# issue-2705 — adversarial-review-f4b31b03 record

## What was done

Build-now bypass (contract v3 s19a): checked: `printenv | grep CORE_BUILD_NOW`
— result: `CORE_BUILD_NOW=1`. Delivers directly, no proposal round.

canonical: `gh issue view 2705` (read at session start) for the original
acceptance criteria and must-not list; `gh pr view 2753 --repo
tokenmaxxxer/on-the-record` plus its CHANGES review comment (read at session
start) — PR #2753 was sent back after both `adversarial-review-249cc937.md`
and `adversarial-review-e4ba953e.md` (merged to main as `becb449d`/
`1d6e746c`) independently live-reproduced the same three parser gaps in its
bundled-`git add`-parser fix; canonical: `gh pr view 2763 --repo
tokenmaxxxer/on-the-record` (state OPEN, head
`f943d3fc9fa052e006072eed471db4cc535f6313`, branch
`issue-2705/secure-coding-input-validation-injection-defense+adversarial-review-bb9edf99`)
— PR #2763 claims to fix all three. This session's task is to verify
#2763's own claims (not re-verify #2753, already closed/superseded), with
explicit brief to hunt the new cwd-stack/directory-argument parsing itself
as its own attack surface, not only confirm the three named gaps are
closed.

Checked out the PR head into an isolated worktree (`git fetch origin
pull/2763/head:pr-2763-review && git worktree add /tmp/pr2763-wt
pr-2763-review`) and re-derived every claim below against that checkout,
not by re-reading the PR's own record. This session's own branch
(`issue-2705/adversarial-review-f4b31b03`, forked from `origin/main` tip
`1d6e746c`) never contains PR #2763's diff at all — canonical: `git log
--oneline -1 -- on-the-record/hooks/gate-registration-guard.sh` in this
session's own working tree — result: `90d1c5a7`, an unrelated commit,
confirming this branch's own copy of the file predates both PR #2753 and
#2763. Every file below that exists only on the PR branch is therefore
cited in `<sha>:<path>` commit-pinned form (per that branch's own tip
`f943d3fc9fa052e006072eed471db4cc535f6313`), matching the convention both
merged prior verification records used. Every filename referenced below in
a probe command (e.g. `cddash_min.py`, `symlinked2.py`, `popd_check.py`,
`nested_space.py`, `arith_form.py`, `acc1.py`-`acc4.py`) is untracked — a
throwaway probe fixture, created only inside a temporary `git clone` this
session's own probe scripts made, never committed to this repo — same
convention `adversarial-review-249cc937.md` and the PR's own record
already used for their own probe files.

### 1. Required acceptance checks (issue #2705's own 4 directional cases) — all hold

derived: `/tmp/acceptance_2763.py` (this session's own script, live-fired
against a real PreToolUse JSON payload on stdin through a throwaway `git
clone` of the PR-head worktree, same harness shape as
`f943d3fc:test/test_gate_registration_guard_bundled_add_commit.py`) —
```
1. bundled unregistered -> RC= 2 (expect 2)
2. bundled registered -> RC= 0 (expect 0)
3. unbundled unregistered -> RC= 2 (expect 2)
4. unbundled registered -> RC= 0 (expect 0)
```
All four match. Acceptance checks 1 and 2 of issue #2705 hold.

### 2. Fail-before/pass-after for all three named gaps — re-derived myself, not trusted from the PR's record

canonical: `git log --oneline` in the PR-head worktree — all of PR #2763's
code diff lands in a single commit, `5a2f1c8c` ("fix cd/subshell,
directory-add, and pathspec-exclude gaps..."); the branch tip `f943d3fc` is
a record-only follow-up commit. derived: `git diff 1d6e746c 5a2f1c8c --stat
-- on-the-record/hooks/gate-registration-guard.sh
test/test_gate_registration_guard_bundled_add_commit.py` and `git show
f943d3fc --stat` — confirms `f943d3fc` touches neither file, so reverting
`gate-registration-guard.sh` to its content at `1d6e746c` (origin/main tip,
the commit both merged verification records landed on and PR #2763 forked
from) is the correct pre-fix baseline, not a partial revert.

derived: `git show 1d6e746c:on-the-record/hooks/gate-registration-guard.sh
> /tmp/prefix_guard.sh`, copied over the shipped (post-fix) file in place
(not `git stash`, to avoid the PR's own record's documented stash-pop
self-conflict), then, this session:
```
$ python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -k "BundledCdBeforeAddTest or BundledDirectoryAddTest or BundledExcludePathspecTest" -q
7 failed, 2 passed in 1.95s
FAILED ...BundledCdBeforeAddTest::test_subshell_cd_before_add_refuses_unregistered_gate
FAILED ...BundledCdBeforeAddTest::test_subshell_cd_does_not_leak_to_a_later_top_level_segment
FAILED ...BundledCdBeforeAddTest::test_plain_cd_before_add_refuses_unregistered_gate
FAILED ...BundledExcludePathspecTest::test_exclude_pathspec_for_unrelated_path_still_refuses_real_gate
FAILED ...BundledDirectoryAddTest::test_trailing_slash_directory_add_refuses_unregistered_gate
FAILED ...BundledCdBeforeAddTest::test_cd_then_dotdot_relative_add_refuses_unregistered_gate
FAILED ...BundledDirectoryAddTest::test_no_trailing_slash_directory_add_refuses_unregistered_gate
```
This 7-failed/2-passed split matches the PR's own per-class breakdown
exactly (3 failed/1 passed cd-class + 2 failed/0 passed directory-class + 2
failed/1 passed exclude-class = 7/2), independently re-derived rather than
taken on the PR record's word.

Restored the post-fix file (`cp /tmp/postfix_guard.sh
on-the-record/hooks/gate-registration-guard.sh`, verified `git status
--short` clean against `f943d3fc` afterward) and reran, this session:
```
$ python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -k "BundledCdBeforeAddTest or BundledDirectoryAddTest or BundledExcludePathspecTest" -q
9 passed in 1.99s
$ python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -q
20 passed in 3.16s
```
Fail-before/pass-after confirmed live, this session, for all three named
gaps — not a test that merely passes both ways.

### 3. Hunting the new parser's own edges — three further live, ground-truthed bypasses found

Per the task's explicit brief, probed the new cwd-stack (`_shell_segments`/
`_pending_add_segments`,
`f943d3fc:on-the-record/hooks/gate-registration-guard.sh:177-265`) and
directory-argument handling
(`f943d3fc:on-the-record/hooks/gate-registration-guard.sh:289-316`)
themselves, not only the three named-gap reproductions. Every candidate
below was checked TWICE: once against the shipped guard (its exit code),
and once by actually running the identical shell command for real in a
second throwaway clone and inspecting what real `git log -1 --name-status`
shows was actually committed — a candidate only counts as a confirmed
bypass if the guard says RC=0 (allow) AND real git/bash actually landed the
unregistered file.

**Checked, not a bypass (guard's RC matches real bash's outcome).**
derived: `/tmp/probe_2763b.py` (this session, sections A/A2/F) and
`/tmp/probe_2763.py` (this session, `escape_dotdot` and
`exclude_excludes_gate_but_second_gate_present` cases) —
- Nested subshells with real bash syntax, `( (cd gates && git add x) )
  && git commit`: guard RC=2 (refuses); real git actually stages the file
  (`A gates/nested_space.py`, an untracked throwaway probe fixture never
  committed to this repo) — guard correctly catches it, no gap.
- The unspaced `((cd gates && git add x)) && git commit -m x` form:
  confirmed via real bash that `((...))` is arithmetic-command syntax, not
  a nested subshell — real bash errors (`((: ... 표현식 문법 오류`) and
  never runs `git add` at all (`git status --porcelain` after shows
  `?? gates/arith_form.py`, an untracked throwaway probe fixture, still
  untracked). The guard's RC=0 here is irrelevant since the command never
  stages anything for real; not a finding.
- `cd does_not_exist_xyz && git add gates/x.py && git commit -m x`: real
  bash's `cd` fails (`그런 파일이나 디렉터리가 없습니다`), and `&&`
  short-circuits — nothing is ever staged for real. Guard RC=0 matches by
  coincidence (its parser doesn't distinguish a successful `cd` from a
  failed one, but the resulting wrong-directory path resolution happens
  to also miss the target, landing on the same aggregate verdict as
  reality). Not a discrepancy in outcome.
- `git add ../outside_gate.py && git commit -m x` (path escaping the repo
  via `..`, `outside_gate.py` an untracked throwaway fixture placed
  outside the repo clone): real git itself refuses (`fatal: ... is
  outside repository`) before anything is staged — this path class is not
  exploitable regardless of the guard's own analysis.
- `git add . ':(exclude)gates/excluded_gate.py' && git commit -m x` with a
  SECOND, non-excluded real unregistered gate (`gates/other_real_gate.py`,
  untracked throwaway fixture) also present: guard RC=2 (still refuses on
  the non-excluded file) — confirms the exclude fix subtracts only the
  excluded match rather than going quiet on the whole segment whenever any
  exclude token appears, exactly as PR #2763's Fix 3 claims.
- Bare `cd` (no argument, real bash meaning "go to $HOME"): treated as a
  no-op by the parser (stays at the previous effective cwd) rather than
  modeling `$HOME`. Probed with a realistic-shaped
  `cd && cd <absolute-repo-path> && git add gates/home_add.py && git
  commit` chain (`gates/home_add.py`, untracked throwaway fixture) — RC=2
  (refuses correctly) since the later absolute `cd` overwrites the no-op's
  staleness. Did not find a live-reproducible bypass built on the
  bare-`cd` gap alone in the time available for this pass; recorded under
  Open findings below as an untested edge, not a confirmed defect.

**Confirmed BYPASS — new findings, live, ground-truthed against real
git/bash, both directions checked.** derived: `/tmp/probe_2763b.py` and
`/tmp/probe_2763c.py` (this session's own scripts and their full output,
reproduced inline below — `/tmp/probe_2763c.py`'s runs are the corrected,
authoritative ones per "What did not work" below):

```
Bypass A — `cd -` (OLDPWD):
$ cd sub && cd - && git add gates/cddash_min.py && git commit -m x
guard: RC=0 (allow)
real bash+git: git log -1 --name-status -> "A\tgates/cddash_min.py" (committed for real)
```
`gates/cddash_min.py` is an untracked throwaway probe fixture, created only
in this session's own temporary clones, never committed to this repo.
Root cause: `f943d3fc:on-the-record/hooks/gate-registration-guard.sh:244`
— `args = [a for a in seg[1:] if not a.startswith("-")]` filters out the
lone `-` argument to `cd -` as if it were a command-line flag (the same
filter that correctly strips `-L`/`-P` from `cd -L <dir>`), so `cd -`
degrades to the "no `cd`/`pushd` argument survived" no-op branch two lines
later instead of being recognized as "go to `$OLDPWD`". After `cd sub`
sets the stack top to `<repo>/sub`, the no-op `cd -` leaves it there
instead of restoring `<repo>`; the later `git add gates/cddash_min.py`
then resolves against `<repo>/sub/gates/cddash_min.py`, which is not the
real untracked path `gates/cddash_min.py`, so no target is found and the
guard allows.

```
Bypass B — `cd` through a symlinked directory:
$ cd gateslink2 && git add symlinked2.py && git commit -m x   # gateslink2 -> gates (symlink)
guard: RC=0 (allow)
real bash+git: git log -1 --name-status -> "A\tgates/symlinked2.py" (committed for real)
```
`gates/symlinked2.py` is an untracked throwaway probe fixture (never
committed to this repo); `gateslink2` is a symlink this session's own
probe script (`os.symlink(repo/"gates", repo/"gateslink2")`) created
inside a temporary clone, also never committed. Root cause: the cwd stack
in `_pending_add_segments`
(`f943d3fc:on-the-record/hooks/gate-registration-guard.sh:213-265`) tracks
the effective directory purely lexically (`os.path.normpath(os.path.join(...))`,
never `os.path.realpath`), and `_match_untracked`'s own path resolution
(`f943d3fc:on-the-record/hooks/gate-registration-guard.sh:289-316`) is
equally lexical (`os.path.relpath(abs_p, repo_root)`, no symlink
resolution). Real bash's `cd` (without `-P`) and real git both resolve a
symlinked directory transparently at the OS level and git reports the
file at its real repo-relative path (`gates/symlinked2.py`, untracked,
same throwaway fixture as above) in `git status`/`git log`. The guard
instead computes the relative path through the symlink's own name
(`gateslink2/symlinked2.py`), which matches nothing in the untracked set,
so no target is found and the guard allows.

```
Bypass C — `pushd`/`popd`:
$ pushd sub && popd && git add gates/popd_check.py && git commit -m x
guard: RC=0 (allow)
real bash+git: git log -1 --name-status -> "A\tgates/popd_check.py" (committed for real)
```
`gates/popd_check.py` is an untracked throwaway probe fixture, never
committed to this repo. Root cause:
`f943d3fc:on-the-record/hooks/gate-registration-guard.sh:243` — `if
seg[0] in ("cd", "pushd"):` recognizes `pushd` as a directory mutator
(mutating the stack top in place, same as `cd` — it does not model
`pushd`'s own directory-stack-push semantics either, though that
mismodeling is inert here) but never recognizes `popd` at all. After
`pushd sub` sets the stack top to `<repo>/sub`, the unrecognized `popd`
segment falls through to the generic "segment has no `git` token, skip"
branch and the stack top is left at `<repo>/sub` instead of being restored
to `<repo>`. The later `git add gates/popd_check.py` then resolves against
`<repo>/sub/gates/popd_check.py`, not the real untracked
`gates/popd_check.py`, so no target is found and the guard allows.

All three commands above are the exact same class of shape the issue and
PR #2763 both name as in scope (a directory-changing construct preceding
`git add` in the same bundled command) and use the identical
unregistered-gate fixture pattern `f943d3fc:test/test_gate_registration_guard_bundled_add_commit.py`
already uses — they are not exotic. `cd -` and `pushd`/`popd` in
particular are common, idiomatic shell shapes, not adversarial
contrivances.

### 4. Sibling-hook enumeration (issue #2705 acceptance check 3) — carried forward, not re-derived a third time

canonical: `docs/issue-2705/reports/adversarial-review-249cc937.md`
("Enumeration re-derivation") and `docs/issue-2705/reports/adversarial-review-e4ba953e.md`
("Enumeration re-derivation"), both already independently re-derived this
same population against six primary grep/wiring commands each and matched
the PR's claimed 3 on-the-record + 2 core (advisory) + 2 dead-code split
exactly. PR #2763 does not change the guard's scope of files it protects,
only its `git add` parsing, so this population is unaffected by #2763's
diff — re-running the same six commands a third time would be pure
repetition, not new verification. No discrepancy carried forward.

## Why

canonical: this record's §1-§4 above (all executed this session against
the PR-head worktree, not cited from the PR's own record) is the basis for
every conclusion.

This task's brief was explicit that the standing risk is structural: "a
parser in front of a guard means anything the parser mis-reads is a silent
bypass" — and that the new cwd-stack/directory-argument code PR #2763
itself adds is new parsing, so it deserves the same adversarial treatment
as the parser PR #2753 introduced (which is exactly what sent #2753 back).
Confirming the three named gaps are closed (§2) is necessary but not
sufficient evidence the new code is safe; §3 is this session's attempt at
the harder half of the brief — probing the NEW code's own edges rather
than re-treading ground two prior sessions already covered. Three of
those probes (`cd -`, symlink, `popd`) produced live, ground-truthed
bypasses using the exact bundled-shape/unregistered-gate fixture pattern
this whole issue is about — not contrived, and not variations on the
three gaps already named (those were: `cd`/plain-subshell, directory
`git add` argument, `:(exclude)` pathspec; these three are: OLDPWD
navigation, symlink-transparent directory traversal, and directory-stack
restoration).

I ground-truthed every candidate against real bash/git execution before
counting it as a bypass (§3's "Checked, not a bypass" list exists because
several plausible-looking RC=0 results turned out to match real bash's own
outcome once I actually ran the command for real — `((...))` arithmetic
syntax and the `..`-escapes-repo case both looked like findings until the
real-execution check disproved them, per §3 above). This discipline is why
the "Checked, not a bypass" section is as long as the "Confirmed BYPASS"
section: a parser-in-front-of-a-guard review that reports every RC=0 as a
finding without checking what real bash would actually do produces false
positives at the same rate PR #2753's own over-refusal bug did in the
other direction.

I did not attempt to fix Bypasses A-C; this role's remit is independent
verification, not remediation, consistent with `verifies_subject: true`
review scope and the same convention both merged verification records for
PR #2753 used.

## Upstream basis

canonical: `gh issue view 2705`, read at session start, for acceptance
criteria and the fail-closed must-not. `gh pr view 2753` and its CHANGES
review comment, read at session start. `gh pr view 2763 --json
headRefName,headRefOid,baseRefName`, read at session start — head
`f943d3fc9fa052e006072eed471db4cc535f6313`, base `main`.
`docs/issue-2705/reports/adversarial-review-249cc937.md` (sha
`becb449d74faf225b65289949fe52e8ac10ce513`) and
`docs/issue-2705/reports/adversarial-review-e4ba953e.md` (sha
`1d6e746c2de29de19d066d420c8eba4e4cb10653`), both read in full this
session — both already merged to `origin/main` and cited above per their
own commit shas, to identify exactly what the two prior verification
rounds already covered so this session's own probing (§3) could target
what neither did.

- `f943d3fc:on-the-record/hooks/gate-registration-guard.sh` and
  `f943d3fc:test/test_gate_registration_guard_bundled_add_commit.py` — PR
  #2763's head, read directly from a `git worktree add /tmp/pr2763-wt
  pr-2763-review` checkout of the PR branch, not from the PR's own diff
  view. This session's own branch tip never carries these files (§ "What
  was done" above, `git log --oneline -1 -- ...` confirms).
- `f943d3fc:docs/issue-2705/reports/secure-coding-input-validation-injection-defense+adversarial-review-bb9edf99.md`
  (PR #2763's own record, present only on the PR branch), read this
  session to identify what the PR's own claims were, then independently
  re-derived rather than cited at face value.

## Open findings

- **Bypass A (`cd -`), Bypass B (symlink-through-`cd`), Bypass C
  (`pushd`/`popd`)**: all three live, ground-truthed, not fixed in this
  review. derived: this record's §3 above ("Confirmed BYPASS" —
  `/tmp/probe_2763b.py`/`/tmp/probe_2763c.py`, this session's own
  transcripts) is the evidence. Resolution paths:
  - A: in `_pending_add_segments`'s `cd`/`pushd` handling
    (`f943d3fc:on-the-record/hooks/gate-registration-guard.sh:243-249`),
    special-case a lone `-` argument as "restore `$OLDPWD`" rather than
    letting the generic `a.startswith("-")` flag filter consume it — this
    requires the cwd stack to also track an OLDPWD-equivalent per frame
    (the directory in force immediately before the most recent
    `cd`/`pushd` in the same segment sequence), not just the current top.
  - B: resolve the effective cwd (and/or every path derived from it in
    `_match_untracked`) through `os.path.realpath` before computing any
    repo-relative path, so a symlinked directory component canonicalizes
    to the same real path git itself reports in `git status`.
  - C: recognize `popd` alongside `cd`/`pushd` in the segment-kind check
    at `f943d3fc:on-the-record/hooks/gate-registration-guard.sh:243`, and
    model an actual directory stack (not just a single mutable top) so
    `pushd`/`popd` push/pop symmetrically the way they do in real bash,
    rather than `pushd` reusing the single-slot `cd` mutation it currently
    does.
  - All three belong to this same fix's own attack surface (not #2757's
    five sibling hooks, which don't yet carry any cwd-tracking at all) —
    recommend a third follow-up round on `gate-registration-guard.sh`
    specifically, using the same stash-based fail-before/pass-after
    discipline this record's §2 and PR #2763's own record both used,
    before treating this parser's cwd-tracking as exhausted.
- **Bare `cd` (no argument, real meaning "go to `$HOME`") treated as a
  no-op**: derived: this record's §3 above ("Checked, not a bypass", bare
  `cd` bullet — `/tmp/probe_2763.py`'s `bare_cd_home` case, this session)
  — probed but did not find a live-reproducible bypass built on this alone
  in this session's time budget. Left as an untested edge rather than a
  confirmed defect — worth a follow-up probe specifically constructing a
  scenario where `$HOME` sits inside or adjacent to the repo tree (this
  session's fresh `/tmp` clones never did), since the no-op fallback's
  safety currently rests on `$HOME` being unrelated to the repo, which
  was true in every environment this session tested but is not something
  the parser itself guarantees.
- Sibling-hook enumeration and the two advisory-only core hooks: canonical:
  this record's §4 above (citing both merged prior verification records'
  own "Enumeration re-derivation" sections, not re-derived a third time
  this session) — no open finding beyond what both records already state.

## Next steps

None for this record; `loop_state: landed`. Recommended next step for the
subject issue: a fourth session (or PR #2763's own author) fix Bypasses
A-C above using the resolution paths named in "Open findings", pin each
with a fail-before/pass-after regression test the same way this PR's own
three fixes were pinned (derived: this record's §2 above,
`python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -q`
this session — `20 passed`, the discipline the follow-up fix should
repeat against the three new shapes in §3, which are not yet in that
suite), and route through an independent verification pass again before
treating issue #2705's "silently unreachable in the bundled shape" defect
class as closed. derived: §3 above ("Confirmed BYPASS", this session's
own `/tmp/probe_2763c.py` transcript) is the executed evidence that
Bypasses A-C remain live against PR #2763's shipped head as of this
session — the pattern of "one review round finds N gaps, the fix for
those N gaps has its own new gaps" has now held twice in a row (PR #2753
-> PR #2763's three fixes -> this record's three more), which is itself
evidence this parser's surface is not yet exhausted, not evidence any one
round was insufficiently thorough.

## What did not work

The `os.symlink` fixture in `/tmp/probe_2763.py`'s first pass
(`case()`/`bare_cd_home_case()` helpers) initially reused a single shared
`BASE` temp directory across many sequential `fresh_clone()` calls without
cleanup, which was fine functionally (each clone is its own subdirectory)
but made the later ground-truth passes slower to write correctly: the
first ground-truth attempt in `/tmp/probe_2763b.py` checked `git diff
--cached --name-status` AFTER already running the full command (including
its own `&& git commit -m x`) for real, which is empty by construction
since the commit already consumed the staged diff — this produced
misleading "real git staged: ''" lines that looked like they contradicted
the guard's own RC=0 verdicts. derived: caught by cross-checking against
the commit log lines bash printed inline during that same run
(`[pr-2763-review ...] x / 1 file changed`), which showed the commits had,
in fact, happened; corrected in `/tmp/probe_2763c.py` by checking `git log
-1 --name-status` instead of `--cached` after a command that itself
commits, which is the version cited throughout this record's §3.

## Standing invariants

1. **No return of the retired role axis in any reshaped form.** derived:
   `git diff 1d6e746c -- on-the-record/hooks/gate-registration-guard.sh test/test_gate_registration_guard_bundled_add_commit.py | grep -ic role`
   (run in the PR-head worktree, this session) — result: `0`.
2. **No new bug — failing-test-name SET vs origin/main, not counts.**
   canonical: `python3 -m pytest test/ gates/ -q`, run in the PR-head
   worktree, this session — result: `15 failed, 450 passed, 3 xfailed`;
   run again in a separate `git worktree add /tmp/wt-main-2763
   origin/main` (tip `1d6e746c`, the same commit both prior verification
   records already landed on), this session — result: `15 failed, 430
   passed, 3 xfailed`. The 20-test gap (450 vs 430) is exactly PR #2763's
   own added tests (11 pre-existing + 9 new = 20 in the target file).
   derived: `diff <(sort main-failing-names) <(sort pr-failing-names)`,
   this session — result: empty (byte-identical SETS, not a count
   comparison) — `/tmp/main_failing.txt` vs `/tmp/pr2763_failing.txt`,
   both 15 lines, diff empty.
3. **No overhead increase.** canonical: `du -sb on-the-record/directive`
   in the PR-head worktree, this session — result: `53162`, matching both
   prior verification records' stated baseline exactly; `git diff
   1d6e746c --stat -- on-the-record/directive`, this session — result:
   empty (untouched). Re-measured the added parse cost myself with
   interleaved timing (10 rounds, alternating
   no-add/plain-bundled-add/worst-case-new-path commands in sequence to
   cancel out warm-up drift, rather than running each command's N repeats
   back-to-back as the PR's own record did): derived:
   `/tmp/perf_probe2.py`, this session —
   ```
   no_add:     avg=0.0569s  min=0.0477  max=0.0682
   plain_add:  avg=0.0821s  min=0.0607  max=0.1592
   worst:      avg=0.0821s  min=0.0604  max=0.1035
   ```
   The pre-existing bundled-add case (`plain_add`, the cost PR #2753
   already introduced) and this PR's own worst-case new path (subshell cd
   + exclude pathspec together, `worst`) average to the identical
   `0.0821s` under interleaved measurement — this session's own numbers
   diverge in absolute value from the PR record's own claimed
   `~0.08s`/`~0.09s` pair (this session measured a larger ~30ms gap over
   the no-add baseline, likely environment/hardware-dependent, not a
   defect), but the substantive claim — the new parsing paths add no
   measurable cost beyond what PR #2753 already paid for any bundled
   `git add` segment — holds under this session's own independent,
   interleaved re-measurement.
4. **Monitor/watch machinery unbroken and not quieter.** derived: `git
   diff 1d6e746c --stat` in the PR-head worktree, this session — result:
   4 files touched (the guard script, the test file, the PR's own record,
   and one deviation-log entry under that record's directory), none in
   any monitor/watch-class path; `git diff 1d6e746c --stat | grep -i
   'monitor\|watch'`, this session — result: empty.

## Skill verdicts

- skill-verdict: adversarial-review — applied: invoked; this session's own
  role structurally IS the two-party protocol's evaluator seat relative to
  PR #2763's builder session (a separate session, given the deliverable —
  PR #2763 and its diff — and re-deriving every claim in this record from
  primary commands run this session against a fresh worktree checkout,
  rather than trusting the PR's own record's claims or the two merged
  prior verification records' conclusions at face value where this
  session could re-check them itself). derived: this record's §1-§4 above
  (executed this session against the PR-head worktree) is the evidence —
  the fail-before/pass-after re-derivation in §2, the ground-truthed new
  bypasses in §3 (specifically checking real bash/git execution before
  counting an RC=0 as a finding, per the skill's "every problem must cite
  a specific, verifiable location/reproduction" requirement), and the
  independent overhead re-measurement in Standing Invariant 3 are all
  primary re-derivations, not citations of the builder's own claims.
- other mounted skills: not triggered — no other skill in this session's
  configured list (only `adversarial-review` was mounted for this task)
  applies beyond what was already invoked.
