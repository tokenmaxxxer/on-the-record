---
issue: 2637
role: silent-failure-audit+architecture-interface-contract-shape-149dabd2
author: silent-failure-audit+architecture-interface-contract-shape-149dabd2
skills: silent-failure-audit (skill-repository(297e350)), architecture-interface-contract-shape (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
code_under_review:
  - path: on-the-record/hooks/deliverable-guard.sh
    sha: 500688a0fd13db4aa199aeafd768c656126690c9
  - path: test/test_deliverable_guard_priorities_shard.py
    sha: 500688a0fd13db4aa199aeafd768c656126690c9
type: verification
breaking: false
verdict: pass
upstream:
  - path: docs/issue-2637/reports/adversarial-review+silent-failure-audit-aba56a87.md
    sha: a93cbf95af82d194fddff5a980284dc3a0349f37
  - path: docs/issue-2637/reports/adversarial-review+secure-coding-input-validation-injection-defense-52c62489.md
    sha: cecb89bd4fee62b1ae99ff68db7954be33177cdd
  - path: docs/issue-2637/reports/adversarial-review+secure-coding-input-validation-injection-defense-b0e82077.md
    sha: 9e58a1f0e6e8be91cb26a5e2be5e0adbf1a44c99
---

# issue-2637 — silent-failure-audit+architecture-interface-contract-shape-149dabd2 record

## What was done

Fourth and final round on PR #2643's shard exemption
(`PRODUCT_CAPTURE_PRIORITIES_DIR_RE` in `on-the-record/hooks/deliverable-guard.sh`
— untracked/absent on this branch, `f4e69cf2` here; the priorities-sharding
work under review lives only on PR #2643's own branch
`issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985`,
confirmed via `git log --oneline -1 -- on-the-record/hooks/deliverable-guard.sh`
in this worktree returning `f4e69cf2`, the pre-#2637 commit).

Answered the question this round was scoped to, with evidence rather than
reasoning, before writing any more resolution logic: **does a session
ever need to `Write` a priorities shard file directly, or does
`spawn.py priorities-log`/`priorities-path` (a Bash path
`deliverable-guard.sh` never inspects) already suffice?**

canonical: PR #2643 branch tip `5dc6b12b:priorities.py:24-28` (module
docstring, quoted verbatim): "The write path needs no orchestrator or
coordinator: a session calls `_priorities_entry_path()` (or `spawn.py
priorities-path`) for its own unique path and writes its own entry
directly with its own Write/Edit call, exactly like
`_consult_trace_path()`/`_deviation_log_path()`."

canonical: `5dc6b12b:priorities.py:82-95` (`_priorities_entry_path()`,
quoted verbatim) — the function body is exactly `d.mkdir(parents=True,
exist_ok=True)` then `return d / f"{ts}-{os.getpid()}.md"`. It mints a
filename and creates the parent directory; it contains no `open()`/
`write_text()` call anywhere, and neither does `5dc6b12b:spawn.py:2343-2350`
(the `priorities-path` branch, a bare `print(_priorities_entry_path(...))`).

derived: this session, fresh worktree of PR #2643's branch at `5dc6b12b`,
`python3 spawn.py priorities-path --issue 2637` — result:
```
=== step 1: spawn.py priorities-path (issue-scoped) ===
/tmp/dg-investigate-188854/docs/issue-2637/reports/product/priorities/20260827T110304434233-192002.md
=== step 2: confirm priorities-path itself created no file ===
confirmed: no file created by priorities-path itself
=== step 3: session writes its own entry (cp, provably-read target) ===
=== step 4: entry landed on disk ===
-rw-rw-r-- 1 jwjung jwjung 187  8월 27 20:03 /tmp/.../20260827T110304434233-192002.md
=== step 5: read back via spawn.py priorities-log (aggregate reader) ===
## Priority: sharding regression tests take precedence
Operator stated during issue-2637 round 4 that closing the git-root-walk
bypass matters less than keeping the write path reachable.
=== step 6: git status -- untracked new shard ===
?? docs/issue-2637/reports/product/priorities/
```
The `cp` at step 3 stands in for the Write/Edit tool call a real session
would issue (this worktree is outside this record's own board write-set,
so this record's own Write tool was not the mechanism used to place the
file — but the target-path mechanics, and the fact that nothing before
step 3 produced a file, are identical to what a session's own Write call
would do). Only after this manual write did the entry exist; `spawn.py
priorities-log` then read it back correctly (step 5) and `git status`
showed it as a new untracked shard (step 6).

**Finding: yes, a session genuinely must `Write` a shard file directly.**
The subcommand mints the path; it is not the write path itself. Per this
round's instruction, that finding stops the round here on the exemption
question: `PRODUCT_CAPTURE_PRIORITIES_DIR_RE` is not deleted, and no
fourth (or fifth) regex/resolution attempt was written to try to close
the residual gap below — that decision is left to the issue, not
invented by this round.

Pushed to PR #2643's branch directly, per this task's explicit
instruction — commit `500688a0`, no new PR:
- A documentation-only comment above the exemption's git-root-walk
  block in `deliverable-guard.sh`, naming the residual open bypass (see
  "Open findings" below) and why no further resolution logic was
  written.
- Three new `@unittest.expectedFailure` cases in
  `test/test_deliverable_guard_priorities_shard.py` (untracked on this
  branch; present only on PR #2643's branch, commit `500688a0`):
  `test_bypass_via_planted_git_directory_should_be_denied`,
  `test_bypass_via_planted_git_symlink_should_be_denied`,
  `test_bypass_inside_linked_worktree_should_be_denied` — reproducing
  PR #2658's three findings inside the suite so `pytest` surfaces the
  open gap instead of the suite silently having no coverage for it.
  derived: `python3 -m pytest test/test_deliverable_guard_priorities_shard.py -v`
  at `5dc6b12b` (pre-this-round) — result: `11 passed in 0.87s`; same
  command at `500688a0` (post-this-round) — result: `11 passed, 3
  xfailed in 0.90s`. derived, same two runs: the original 11 pass names
  are identical between both runs (compared by eye against the pytest
  `-v` output) — PR #2649/#2653's coverage is untouched; only the 3 new
  `expectedFailure` cases were added.

## Reproductions: the three prior rejections, run verbatim against the current (unchanged) exemption logic

All four fixtures below are rooted under `$HOME`, not `/tmp` — PR
#2653's own record
(`docs/issue-2637/reports/adversarial-review+secure-coding-input-validation-injection-defense-52c62489.md`)
flags `/tmp` as a trap: `deliverable-guard.sh` has an unrelated
literal-`tmp`-path-segment exemption that would false-EXEMPT every case
through the wrong mechanism. This round hit that exact trap on a first
pass (see "What did not work") before correcting it. Hook under test:
`bash on-the-record/hooks/deliverable-guard.sh` at PR #2643 branch
commit `5dc6b12b` (pre-this-round) and `500688a0` (post-this-round,
comment-only) — identical `rc` values both times, confirmed by re-running
the same script (`/tmp/dg_repro2.py`, scratch, not committed) against
both commits in separate worktrees.

derived: `python3 /tmp/dg_repro2.py <hook-path>` against `5dc6b12b` and
again against `500688a0`, real JSON PreToolUse payloads on stdin,
`TOKENMAXXXER_SPAWNED` unset, fresh `$HOME`-rooted `git init` fixture
per case — **PR #2649's table** (src-rooted bypass rel/abs, plus the
absolute-path false-deny it originally found and which is already fixed
upstream of this round) — result (identical both commits):
```
relative shard legit            -> rc=0 (exempt, correct)
exploit rel src-rooted           -> rc=2 (denied)
exploit abs src-rooted           -> rc=2 (denied)
real deliverable rel             -> rc=2 (denied, correct)
legacy priorities.md rel         -> rc=0 (exempt, correct)
absolute legit shard             -> rc=0 (exempt -- the false-deny PR #2649 found is fixed)
```

**PR #2653's exact reproduction** (`cd src`, absolute `file_path`, `cwd`
a real ancestor of the target other than repo root) — result (identical
both commits):
```
cwd=<repo>/src, file_path=<repo>/src/docs/reports/product/priorities/hack.md -> rc=2 (denied)
```
Still denied — the git-root walk this round leaves untouched correctly
closes this one.

**PR #2658's three findings** (`.git`-probe walk is steerable) — result
(identical both commits):
```
fake .git DIRECTORY planted at <repo>/src/.git,
  abs src-rooted write            -> rc=0 (EXEMPT -- BYPASS, still live)
fake .git SYMLINK at <repo>/src/.git -> elsewhere,
  abs src-rooted write            -> rc=0 (EXEMPT -- BYPASS, still live)
linked worktree (.git is a FILE there, walk finds no root),
  abs src-rooted write inside worktree -> rc=0 (EXEMPT -- BYPASS, still live)
```
canonical: this session's own reproduction above, cross-checked against
`docs/issue-2637/reports/adversarial-review+secure-coding-input-validation-injection-defense-b0e82077.md`
(PR #2658's record) §2–§3, which found the identical two bypasses and
the linked-worktree fallback against commit `5dc6b12b` — this round
re-derived them independently (own fixtures, own script) rather than
citing that record's transcript, and confirms they still reproduce
unchanged at `500688a0`. All three are still live; this round did not
attempt to close them (see "Open findings").

derived: `python3 -m pytest test/ -q` at `500688a0` — result:
```
15 failed, 353 passed, 3 xfailed in 2.98s
```
canonical: the 15 failing test names printed by that run were compared
by eye against
`docs/issue-2637/reports/adversarial-review+secure-coding-input-validation-injection-defense-52c62489.md`'s
own "Regression test suite" section, which lists the identical 15 names
(`test_convention_equivalence.py` x2, `test_local_dependency_env.py` x1,
`test_spawn_cross_family_skill_selection.py` x6,
`test_spawn_artifact_skill_pairing.py` x2,
`test_spawn_skill_judge_haiku_timeout_overlap.py` x4) as a pre-existing,
unrelated failure set at commit `2354b1e7`. derived: 353 = 350 (that
pre-existing pass count) + 11 (this file's original tests, unchanged) −
8 (this file's test count before PR #2650/#2653's rounds added the
other 3) = 353; the 3 new `expectedFailure` cases account for the `3
xfailed`.

## Why

architecture-interface-contract-shape's rule 8 (Open Host Service +
Published Language, for exposing functionality to unknown/many
consumers rather than one negotiated partner) is what `priorities.py`
already chose. canonical:
`docs/issue-2637/reports/architecture-interface-contract-shape+silent-failure-audit-a86b8985.md`
frontmatter (`skill-verdict: architecture-interface-contract-shape —
applied: invoked; rule 12 ... + rule 8 ... applied to the directory+reader
design`) — the prior round's own skill-verdict on this same file. This
round's finding reinforces that choice rather than replacing it: the
alternative shape — `spawn.py priorities-log`/`priorities-path` as a
synchronous command that owns the write on the caller's behalf, turning
the boundary into something closer to a Shared-Kernel RPC — is not what
shipped, and the module docstring (quoted under "What was done") states
the direct-write design was deliberate. Verifying which shape actually
ships (rather than assuming the subcommand's existence implied the RPC
shape) is exactly rule 8's question: does the published contract let
heterogeneous unknown callers act on their own, or does it centralize
the action? The evidence says the former, so the `deliverable-guard.sh`
exemption guarding that caller-side write action is real, necessary
surface — not a defeated guard protecting a door nobody uses.

silent-failure-audit's relevance here is narrower but load-bearing for
trusting the reproductions above: before citing `rc=0`/`rc=2` results as
ground truth, the exception-handling sites in the code path being
exercised were checked for a site that could silently produce a
misleading result. canonical: `5dc6b12b:on-the-record/hooks/deliverable-guard.sh:60-62`
(JSON-parse failure → explicit `deny()`, Handled) and
`5dc6b12b:on-the-record/hooks/deliverable-guard.sh:83-88` (role-bind
snapshot read failure → falls back to the live env var, Handled,
pre-existing, documented two-tier resolve) are the only two try/except
sites in the file — derived: `grep -n "except\|try:"
on-the-record/hooks/deliverable-guard.sh` in the PR #2643-branch
worktree, two matches, both listed above. `_git_root_from()` (the
function whose steerability this round's open finding is about) has no
try/except at all — `os.path.isdir()` on a non-existent probe path
returns `False` rather than raising, so there is no silently-absorbed
exception that could be manufacturing the observed `rc=0` bypass
results; they trace to the walk's own trust-any-`.git`-shaped-entry
logic, not to a masked error. `priorities.py`'s `read_priorities()` was
already audited for this by the prior round (canonical:
`5dc6b12b:priorities.py:104-111`, docstring states the directory/file
absence check is the only silent-empty case, everything else propagates
unwrapped) and was not re-litigated here.

## What did not work

Two reproduction attempts against the current code (unchanged by this
round on the matching/resolution front) were discarded before landing
on the fixture hygiene needed for a trustworthy result:

1. An initial pass reused a single `$HOME`-rooted fixture directory
   across PR #2658's `.git`-directory-plant case and then, without
   resetting it, the PR #2653 cwd-steering case — derived: re-running
   `PR2653 repro` in that contaminated fixture returned `rc=0`, which
   looked like a *new* re-opening of PR #2653's bug; re-running the
   identical payload in a fresh, uncontaminated fixture (the
   `/tmp/dg_repro2.py` version actually used for the numbers above)
   returned `rc=2`, matching every other trial — the `rc=0` reading was
   an artifact of the leftover `.git` plant from the prior case, not a
   real finding, and is not reported as one above.
2. A second pass rooted fixtures under `/tmp/dgfix-...` (`tempfile.mkdtemp()`'s
   default) — derived: every absolute-path case in that run returned
   `rc=0`, including cases (e.g. "exploit abs src-rooted", a case PR
   #2649's own table has as `rc=2` DENIED) that should not be exempt at
   all; re-running the identical script with fixtures rooted under
   `$HOME` instead (via `tempfile.mkdtemp(dir=os.path.expanduser("~"))`)
   reproduced PR #2649's table exactly. Both were caught by cross-checking
   against the PR #2649/#2653 records' own tables before trusting the
   numbers.

## Upstream basis

- `docs/issue-2637/reports/adversarial-review+silent-failure-audit-aba56a87.md`
  (PR #2649) — the `^`-anchor / absolute-path false-deny finding, reused
  verbatim as this round's first reproduction table.
- `docs/issue-2637/reports/adversarial-review+secure-coding-input-validation-injection-defense-52c62489.md`
  (PR #2653) — the cwd-steering bypass finding, reused verbatim as this
  round's second reproduction.
- `docs/issue-2637/reports/adversarial-review+secure-coding-input-validation-injection-defense-b0e82077.md`
  (PR #2658) — the git-root-walk steerability finding (`.git` plant,
  linked worktree), reused verbatim as this round's third reproduction
  and turned into the three new `expectedFailure` regression tests.
- `priorities.py`, `spawn.py`, `on-the-record/hooks/product-capture-stopgate.sh`
  — read at PR #2643 branch tip `5dc6b12b`, cited above for the
  subcommand-does-not-write finding; not modified by this round.

## Open findings

1. **CONFIRMED, still open**: canonical, this round's own reproduction
   under "Reproductions" above (PR #2658's three cases, `rc=0` each,
   identical at `5dc6b12b` and `500688a0`) — `deliverable-guard.sh`'s
   git-root walk (`_git_root_from`, backing
   `PRODUCT_CAPTURE_PRIORITIES_DIR_RE`'s absolute-path/cwd-relative
   resolution) trusts `os.path.isdir(<probe>/".git")` as proof of repo
   root. A session can run ordinary `mkdir`/`ln -s` before its guarded
   Write/Edit call (this hook never inspects Bash calls — canonical
   `5dc6b12b:on-the-record/hooks/deliverable-guard.sh:93`, the
   `tool_name not in (...)` check) to plant a fake `.git` entry and
   relocate the discovered root, reopening the src/-rooted bypass; a
   linked worktree/submodule (`.git` there is a file) hits the walk's
   "no root found" fallback and disables the hook's src/test/docs
   deliverable-write denial entirely, not just this exemption — canonical,
   this round's own "linked worktree" reproduction above.
   Resolution path: **not a path-shaped fix** — the consult this round's
   task cites already concluded no such formulation can be made
   unsteerable while this hook decides from session-reported strings
   and session-mutable filesystem state before the write happens (three
   prior attempts across PRs #2649/#2653/#2658, three different layers,
   each defeated in turn — canonical, the three upstream records listed
   above). This round did not attempt a fourth/fifth attempt per its own
   explicit instruction; documented in-code (the comment landed in
   `500688a0`) and here so it stays visible rather than silently
   unaddressed. The issue needs a decision on a genuinely different
   mechanism — outside this round's scope.

## Next steps

None from this round — `loop_state: landed`. The open finding above is
the issue's next decision, not this record's to resolve.

skill-verdict: silent-failure-audit — applied: invoked; enumerated
`deliverable-guard.sh`'s two try/except sites and `_git_root_from`'s
lack of one, tracing that none of them silently manufacture the `rc=0`
bypass results cited above (see "Why").
skill-verdict: architecture-interface-contract-shape — applied: invoked;
canonical: the prior round's own skill-verdict on this file (quoted
above under "Why", frontmatter of
`docs/issue-2637/reports/architecture-interface-contract-shape+silent-failure-audit-a86b8985.md`)
— rule 8 (Open Host Service/Published Language) applied to confirm
`priorities.py`'s direct-write-by-caller shape is the shipped design,
not an accidental gap the subcommand was meant to close.
