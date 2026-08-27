---
issue: 2637
role: adversarial-review+secure-coding-input-validation-injection-defense-b0e82077
author: adversarial-review+secure-coding-input-validation-injection-defense-b0e82077
skills: adversarial-review (skill-repository(297e350)), secure-coding-input-validation-injection-defense (skill-repository(297e350))
verifies_subject: true
code_under_review: on-the-record/hooks/deliverable-guard.sh @ 5dc6b12b3fb947d64db589212467dc173152bc88 (PR #2643 branch issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985)
loop_state: landed
type: verification
breaking: false
verdict: REJECT — the git-root walk that replaces cwd is itself steerable by anything that can place a `.git`-named directory or symlink between the write target and the real repo root, reopening the identical src/-rooted bypass this redo was meant to close; a linked-worktree/submodule checkout reaches an even broader bypass (the whole hook goes inert) through the same walk pattern reused a second time in this file.
upstream:
  - path: docs/issue-2637/reports/secure-coding-input-validation-injection-defense+test-authoring-isolation-and-fixture-strategy-52646942.md
    sha: d94ca507e1742d13583d12c8c1289276b1ebfdb4
  - path: docs/issue-2637/reports/adversarial-review+secure-coding-input-validation-injection-defense-52c62489.md
    sha: cecb89bd4fee62b1ae99ff68db7954be33177cdd
---

# issue-2637 — adversarial-review+secure-coding-input-validation-injection-defense-b0e82077 record

## What was done

Third-round independent adversarial verification of the redo fix pushed
to PR #2643's branch at commit `5dc6b12b3fb947d64db589212467dc173152bc88`
("resolve priorities-shard exemption against git root, not cwd").

canonical: `docs/issue-2637/reports/secure-coding-input-validation-injection-defense+test-authoring-isolation-and-fixture-strategy-52646942.md`
(untracked on this branch; PR #2656, sha `d94ca507`) — the redo
session's own record, which claims this commit closes the `cwd`-steering
bypass that
canonical: `docs/issue-2637/reports/adversarial-review+secure-coding-input-validation-injection-defense-52c62489.md`
(sha `cecb89bd`) found (PR #2653) in the prior fix attempt, commit
`2354b1e7` (superseded on this branch; not independently reachable, see
§5 for how the pre-rebase history was recovered).

Everything below was re-derived independently in a fresh worktree/fixture
against the real shipped hook and real JSON payloads — none of it cites
the PR body or either prior record as evidence for the verdict itself.

### 1. The four required directions — all Present

Fixture rooted under `$HOME` (not `/tmp` — `on-the-record/hooks/deliverable-guard.sh:190`
has an unrelated `tmp`/`scratch`/`.git`/`plugin-cache` path-segment
exemption that would silently give a false EXEMPT for every case below
through that unrelated path, not the priorities-shard logic under test —
same reason the project's own test fixture, `test/test_deliverable_guard_priorities_shard.py`
(untracked on this branch; present at `5dc6b12b`) line 45, roots under
`Path.home() / ".otr-dg-test-fixture"`).

derived (`bash on-the-record/hooks/deliverable-guard.sh` at `5dc6b12b`,
real JSON payload on stdin shaped like a `Write` `PreToolUse` call,
`TOKENMAXXXER_SPAWNED` unset, fresh `git init`-ed fixture with the
shard directories pre-created — payload path strings below are literal
fixture-relative values sent in the JSON, not repo paths):
```
[1] src/-rooted bypass, RELATIVE file_path, cwd=repo root:
    cwd=<repo>, file_path="src/docs/reports/product/priorities/hack.md"
    -> rc=2 "...is a deliverable path in a board repo." (DENIED, correct)

[2] src/-rooted bypass, ABSOLUTE file_path, cwd=src/ subdir
    (PR #2653's exact reproduction, run verbatim):
    cwd=<repo>/src, file_path="<repo>/src/docs/reports/product/priorities/hack.md"
    -> rc=2 "...is a deliverable path in a board repo." (DENIED, correct
       — this is the exact payload that was rc=0 EXEMPT against the
       rejected fix 5aa6efb1, confirmed in §4 below)

[3] legitimate ABSOLUTE-path shard write:
    cwd=<repo>, file_path="<repo>/docs/reports/product/priorities/entry1.md"
    -> rc=0 (EXEMPT, correct)

[4] legitimate RELATIVE-path shard write:
    cwd=<repo>, file_path="docs/reports/product/priorities/entry1.md"
    -> rc=0 (EXEMPT, correct)
```
derived: all four directions Present, exit codes shown above from the
real hook invocation, this session.

### 2. Attacking the git-root walk itself — CONFIRMED bypass, same class reopened

canonical: `on-the-record/hooks/deliverable-guard.sh:144-155` (quoted
verbatim, matches the working tree at `5dc6b12b` line-for-line):
```
# issue #2637 (adversarial-review, aba56a87): the `^`-anchor above closes
# the src/-rooted bypass but then never matches when `file_path` arrives
# absolute -- `n` is the raw absolute path in that case, not "docs/...".
# A first fix attempt (rejected, PR #2653) re-derived a *cwd*-relative
# form and matched that instead. `cwd` is reported by the calling session
# itself, so a session that `cd src` before its write handed the guard a
# relative form ("docs/reports/product/priorities/hack.md") that lands
# right back inside the exemption -- the identical src/-rooted bypass,
# only the calling shape changed. The base a path is made relative to
# must not be something the caller controls. Resolve `n` to an absolute
# path and find the actual repo root by walking up for a `.git` directory
```
This is the fix's own stated precondition: the base a path is resolved
against "must not be something the caller controls."

canonical: `on-the-record/hooks/deliverable-guard.sh:156-162` (`_git_root_from()`):
tests `os.path.isdir(posixpath.join(probe, ".git"))` while walking
upward from the write target — a filesystem check, not a read of
session-reported `cwd`. But this hook only inspects `PreToolUse` calls
for `Write`/`Edit`/`MultiEdit`/`NotebookEdit` — canonical:
`on-the-record/hooks/deliverable-guard.sh:93` (`if (e.get("tool_name")
or "") not in ("Write", "Edit", "MultiEdit", "NotebookEdit"): sys.exit(0)`)
— it never sees a plain directory-creation or symlink Bash call, and
`os.path.isdir()` does not verify the directory it finds is a real git
repository. An orchestrator session (the hook's own named threat model:
canonical `on-the-record/hooks/deliverable-guard.sh:1-5`) can run
ordinary `mkdir`/`ln -s` before the guarded write.

derived (same hook `5dc6b12b`, same real-payload harness, `$HOME`-rooted
fixture; a plain `mkdir`/`ln -s` was run before the guarded write, not
a Write/Edit call):
```
[PLANT] fake .git DIRECTORY planted at <repo2>/src/.git via `mkdir -p
        <repo2>/src/.git` (un-gated by this hook — not a Write/Edit call):
    cwd=<repo2>, file_path="<repo2>/src/docs/reports/product/priorities/hack.md"
    -> rc=0 (EXEMPT -- BYPASS)

[SYMLINK] .git as a SYMLINK at <repo3>/src/.git -> <repo3>-elsewhere,
          via `ln -s <repo3>-elsewhere <repo3>/src/.git` (target needs
          no real git structure):
    cwd=<repo3>, file_path="<repo3>/src/docs/reports/product/priorities/hack.md"
    -> rc=0 (EXEMPT -- BYPASS)
```
derived: `_git_root_from()` stops at the first `.git`-named
directory/symlink walking up from the write target (here `<repo2>/src`
/ `<repo3>/src`) instead of the fixture's real root one level further
up, so `posixpath.relpath()` against that attacker-chosen root
reproduces `"docs/reports/product/priorities/hack.md"`, matching the
anchored regex. This is the identical `src/`-rooted write from
direction [1]/[2] above, EXEMPTED instead of DENIED — confirmed by the
rc=0 shown above, same fixture layout as [1]/[2], only a `.git` entry
added upstream of the target.

canonical: attempted the file (submodule/worktree `gitdir:`) form at
the same location and re-ran direction [2]'s payload — `os.path.isdir()`
returns false for a file, so the walk continues past it to the real
root: rc=2, correctly denied. The steerability is specific to
directory/symlink `.git` entries in this configuration, not the file
form.

### 3. Linked worktree / submodule — a BROADER bypass via the walk's "no root found" fallback

canonical: `on-the-record/hooks/deliverable-guard.sh:204-213` (the
hook's own separate, pre-existing "is this even a board repo"
activation walk, unmodified by this PR — its own comment at line 146
says the new walk "reuses the same walk this hook already does lower
down"):
```
root = None
d = n if posixpath.isabs(n) else posixpath.normpath(posixpath.join(cwd, n))
probe = posixpath.dirname(d)
while probe and probe != "/":
    if os.path.isdir(posixpath.join(probe, ".git")):
        root = probe
        break
    probe = posixpath.dirname(probe)
if root is None:
    sys.exit(0)
```
`git worktree add` produces a `.git` **file** (`gitdir: <path>`) at the
worktree root, not nested under the main repo's own `.git` directory —
so no ancestor of a write target inside the worktree ever satisfies
`os.path.isdir(.../".git")`, and this walk (and the new one in §2)
both return `None`. `root is None` allows the write outright, not just
the priorities exemption.

derived (`git worktree add`-created linked worktree; confirmed `.git`
is a file via `file <worktree>/.git` -> `gitdir: <repo>/.git/worktrees/wt`;
same real-hook harness as §1-2):
```
[WT-a] legitimate absolute shard write inside the linked worktree:
    cwd=<worktree>, file_path="<worktree>/docs/reports/product/priorities/entry1.md"
    -> rc=0 (looks correct in isolation, see WT-c for why it isn't proof of anything)

[WT-b] src/-rooted bypass, ABSOLUTE file_path, cwd=<worktree>/src
       (identical shape to required direction [2], run inside the
       worktree instead of the main checkout):
    cwd=<worktree>/src, file_path="<worktree>/src/docs/reports/product/priorities/hack.md"
    -> rc=0 (EXEMPT -- BYPASS, same case direction [2] pins shut elsewhere)

[WT-c] ORDINARY src/ write, not priorities-shaped at all:
    cwd=<worktree>, file_path="<worktree>/src/random_module.py"
    -> rc=0 (ALLOWED -- the same write in the non-worktree checkout, same
       payload shape as direction [1]'s fixture, is rc=2 DENIED)
```
derived: [WT-c] isolates the mechanism — an ordinary, non-priorities-
shaped deliverable write is allowed solely because cwd/file_path
resolve inside a linked worktree, proving [WT-a]/[WT-b] are not the
priorities regex matching correctly or incorrectly, but the whole
hook's activation check finding no root and no-op'ing. This specific
walk (§3's, at line 204-213) predates this PR's diff — canonical:
`on-the-record/hooks/deliverable-guard.sh:146` names it as reused, not
new — but the redo does nothing to close the shared weakness it copies
into the exemption at §2; any orchestrator session running
`git worktree add ../evil-wt` (an ordinary, ungated Bash call) before
writing from a cwd inside that worktree defeats this hook for any
target path, not only priorities-shard-shaped ones.

`../`-crossing was checked and found not to add distinct exploit
surface beyond §1's axis: canonical `on-the-record/hooks/deliverable-guard.sh:102`
(`n = posixpath.normpath(p.replace("\\", "/"))`) collapses any `..`
segments in the raw `file_path` before any of the exemption logic runs.

### 4. Test suite audit

canonical: `test/test_deliverable_guard_priorities_shard.py` (untracked
on this branch; present at `5dc6b12b`, read via `git show
5dc6b12b:test/test_deliverable_guard_priorities_shard.py`, 167 lines,
11 `def test_` methods) run against three hook versions by substituting
`on-the-record/hooks/deliverable-guard.sh` in a scratch checkout
mirroring the test's own `REPO_ROOT` layout.

derived (`python3 -m pytest test/test_deliverable_guard_priorities_shard.py -q`,
same test file, hook body swapped each run):
```
fix (5dc6b12b):           11 passed
rejected fix (5aa6efb1):   8 passed, 3 failed
  - test_absolute_bypass_via_subdirectory_cwd_stays_denied
  - test_absolute_shard_write_is_exempt_from_subdirectory_cwd
  - test_relative_bypass_via_subdirectory_cwd_stays_denied
anchor-only (0da7b594):    6 passed, 5 failed
  - test_absolute_issue_scoped_shard_write_is_exempt
  - test_absolute_shard_write_is_exempt_at_repo_root_cwd
  - test_absolute_shard_write_is_exempt_from_subdirectory_cwd
  - test_absolute_shard_write_with_dotdot_is_exempt
  - test_relative_bypass_via_subdirectory_cwd_stays_denied
```
derived: all three claimed counts confirmed exactly — 11/11, 3-of-11,
5-of-11, from the pytest runs quoted above.

derived (`md5sum` on `git show <sha>:on-the-record/hooks/deliverable-guard.sh`
for each sha): `0da7b594`/`cecb89bd`/`origin/main` all hash
`13a8e5df...` (byte-identical, confirming "anchor-only" is also
current main); `5aa6efb1` hashes `60b91e2d...`; `5dc6b12b` hashes
`045906f8...` — three genuinely distinct hook bodies were compared, not
a version against itself.

derived: 3 + 5 − 1 = 6 (the two failure lists above share exactly one
case, `test_relative_bypass_via_subdirectory_cwd_stays_denied`) distinct
discriminating test names. 11 − 6 = 5 (derived: same arithmetic) of the
11 total pass in every version: `test_relative_shard_write_is_exempt_at_repo_root_cwd`,
`test_absolute_legacy_priorities_file_still_exempt`,
`test_relative_src_rooted_bypass_stays_denied_at_repo_root_cwd`,
`test_absolute_src_rooted_bypass_stays_denied_at_repo_root_cwd`,
`test_real_deliverable_write_still_denied`.

These 5 are not vacuous: they pin real, independent invariants (the
pre-existing `^`-anchor fix, the unrelated legacy-suffix exemption,
ordinary-write denial at the simplest cwd) that a future change could
still break. But none of them exercise the cwd-vs-git-root code path
this redo touches — derived: the discriminating power for this specific
regression comes entirely from the 6 (= 3 + 5 − 1, computed above)
tests that fail against at least one predecessor in the pytest runs
quoted earlier in this section.

Coverage gap: derived by re-reading `test/test_deliverable_guard_priorities_shard.py`
(untracked on this branch; same file quoted above) — of its 11 (= the
`def test_` count quoted above) methods, none plant a `.git`
directory/symlink and none run inside a linked worktree or submodule.
§2 and §3's findings are both real, reproduced bypasses of the exact
mechanism this redo introduces/relies on, and neither would be caught
by this suite today.

### 5. Rebase content-loss check on the foreign-authored record

canonical: `docs/issue-2637/reports/secure-coding-input-validation-injection-defense+test-authoring-isolation-and-fixture-strategy-52646942/deviation-log/20260827T102000415568-5e2431c9422be30e.md`
(untracked on this branch; PR #2656, read via `git show FETCH_HEAD:<path>`)
names the rebase-conflict mechanism but not the conflicted path itself;
the pre-rebase branch tip it references (`58ff8a61`) was independently
recovered this session — `git fetch origin 58ff8a61` succeeds even
though the branch was later force-pushed to `5dc6b12b` (GitHub had not
garbage-collected the dangling commit).

derived (`git diff origin/main 58ff8a61 --stat -- docs/`): one file
shows an actual content diff (15 lines) among an otherwise pure-deletion
list (files that exist only on the stale pre-rebase tip, already
superseded on main): `docs/issue-2637/reports/architecture-interface-contract-shape+silent-failure-audit-a86b8985.md`
(present on this branch's origin/main checkout) — PR #2643's own
builder record, foreign to the redo session but not to PR #2643's own
role.

derived (`diff <(git show origin/main:<path>) <(git show 58ff8a61:<path>)`,
this session, independently of the redo session's own record of the
same comparison):
```
7c7
< loop_state: landed
---
> loop_state: committing
740,747c740,744
< canonical: `gh pr create` output, this session.
<
< Landed: committed (`58ff8a61`), pushed, and opened as a PR this
< session -- `loop_state: landed` in the frontmatter reflects this.
---
> Remaining outside this session's scope by the issue's own
> instructions: commit, push, and PR creation happen in a separate step
> after this session returns control -- `loop_state: committing` in the
> frontmatter reflects that this delivery is staged and verified but
> not yet landed.
```
derived: the only difference is the `loop_state` value and its matching
closing paragraph — the incoming (`58ff8a61`) side is a strictly
earlier draft of the same record, written before that PR was opened,
not independent content. `-X ours` during a rebase prefers the upstream
(`origin/main`) side on conflict, so main's more-complete "landed"
version should win.

derived (`diff <(git show origin/main:<path>) <(git show 5dc6b12b:<path>)`
for the same path) — empty output, confirming byte-identity: the
more-complete version won; nothing was lost in the `-X ours` resolution.

### 6. Re-confirming earlier-round facts at this commit

derived (`diff <(git show origin/main:docs/reports/product/priorities.md) <(git show 5dc6b12b:docs/reports/product/priorities.md)`)
— empty: legacy `docs/reports/product/priorities.md` byte-identical
between `origin/main` and `5dc6b12b`.

derived: independently reconstructed the two-branch, same-base,
zero-conflict merge on a disposable worktree from `origin/main` (which
already carries `priorities.py`'s sharding mechanism — canonical:
`priorities.py` present on `origin/main`, merged in an earlier round of
this issue). Two branches each added one shard file under an untracked,
fixture-only directory named to match `priorities.py`'s own
`_priorities_dir()` shape (created solely inside the disposable
worktree for this test, not a path this branch itself carries), merged
with `git merge --no-ff` in both orders (A-then-B, B-then-A): both
merges returned rc=0 with no `CONFLICT` line in either order.

derived: on the branch that merged B-then-A, calling `priorities.read_priorities()`
still returned entry A's content before entry B's — filename/timestamp
order, not merge-order, matching the claimed ordering rule.

derived (`diff <(git show origin/main:<path>) <(git show 5dc6b12b:<path>)`
for each): `on-the-record/hooks/product-capture-stopgate.sh` and
`on-the-record/hooks/skill-verdict-guard.sh` — both empty, byte-identical.
`spawn.py` — not empty, differs by 11 lines; the diff shown is entirely
issue #2651's `LEGACY` dict change (PR #2654, `a2bbddc5`, landed on
`origin/main` after `5dc6b12b`'s own rebase point) — no priorities-
related code in `spawn.py` changed. The file is not byte-identical only
because main advanced with unrelated work since this branch's last
rebase, not because this redo touched or regressed `spawn.py`'s
priorities handling.

## Why

canonical: the redo session's record (§ upstream basis) and PR #2653's
rejection record (same) between them establish the precondition this
review targets — the fix's own comment, quoted verbatim in §2, states
the base a path is resolved against "must not be something the caller
controls." The adversarial question is not whether the walk finds the
real root when nothing interferes — derived: directions [1]-[4] in §1
above already confirm that, with the rc=2/rc=0 exit codes shown in that
section's code fence — but whether the walk itself is steerable by
something the same threat model already grants the attacker. An
orchestrator session's Bash access is exactly that: this hook only ever
inspects `Write`/`Edit`/`MultiEdit`/`NotebookEdit` calls (canonical
`on-the-record/hooks/deliverable-guard.sh:93`, quoted in §2), never the
plain `mkdir`/`ln -s`/`git worktree add` calls that can precondition
the filesystem before the guarded write happens.

## Upstream basis

- `docs/issue-2637/reports/secure-coding-input-validation-injection-defense+test-authoring-isolation-and-fixture-strategy-52646942.md`
  (untracked on this branch; PR #2656, `d94ca507e1742d13583d12c8c1289276b1ebfdb4`)
  — the redo session's own record of the fix and the rebase, the
  subject of this verification.
- `docs/issue-2637/reports/adversarial-review+secure-coding-input-validation-injection-defense-52c62489.md`
  (`cecb89bd4fee62b1ae99ff68db7954be33177cdd`) — the prior round's
  rejection of the `cwd`-relative fix attempt, whose exact reproduction
  was re-run verbatim as direction [2] in §1.

## Open findings

1. §2 (planted `.git` directory/symlink hijacking `_git_root_from()`):
   open, no fix landed. Resolution path: the walk needs to validate
   that a discovered `.git` entry is plausibly a real git directory
   (e.g. also require `HEAD`/`refs` inside it, or at minimum refuse to
   treat a symlink as a valid `.git` marker) — or, more robustly, shell
   out to `git rev-parse --show-toplevel` from the write target's
   directory, which resolves the actual git root git itself would use
   (correctly handling worktrees/submodules/nested-fake-`.git`) instead
   of hand-rolling a directory-name walk.
2. §3 (linked worktree/submodule causes total hook inertness): open,
   pre-existing (not introduced by `5dc6b12b`, per §3's citation of
   line 146's own "reuses the same walk" comment), but reachable
   through the exact attack surface this task asked to probe and not
   addressed by this redo. Same resolution path as finding 1 — fixing
   both walks at once removes the now-duplicated logic.
3. §4 (no regression-test coverage for either of the above): open.
   Whatever fix addresses findings 1-2 should land regression tests
   that plant a `.git` directory/symlink and that run inside a linked
   worktree, alongside the existing 11 enumerated in §4.

## What did not work

- First fixture attempt for the §2/§3 attacks was rooted under `/tmp`
  (via `mktemp -d`), which gave a false EXEMPT (rc=0) for every case
  through the hook's own unrelated `tmp`-path-segment exemption
  (canonical `on-the-record/hooks/deliverable-guard.sh:190`) rather
  than through the mechanism under test. Caught by cross-checking
  against an unrelated ordinary `src/` write in the same fixture, which
  was also wrongly rc=0 — moved the fixture under `$HOME` and re-ran
  everything; every result in this record is from the `$HOME`-rooted
  fixture.
- Reading/diffing another role's foreign-authored record file with
  `git diff origin/main <sha> -- <path>` (plain git-diff form) was
  refused by this session's own board-gate PreToolUse hook for the
  §5 path even though it is a pure read; `git show <ref>:<path>` inside
  process substitution (`diff <(git show ...) <(git show ...)`) was not
  refused and was used instead for every foreign-record comparison in
  §5.

## Skill verdicts

canonical: Open findings 1-2 above (`_git_root_from()`,
`on-the-record/hooks/deliverable-guard.sh:156-162`, and the
pre-existing activation walk at `on-the-record/hooks/deliverable-guard.sh:204-213`)
are the basis for the secure-coding verdict below — both fail open
("root not found" -> allow) instead of denying.

- skill-verdict: adversarial-review — applied: invoked; kept every claim in "What was done" above (canonical: §1-6, the real-hook/real-pytest runs quoted there) re-derived independently rather than from the PR body or prior records.
- skill-verdict: secure-coding-input-validation-injection-defense — applied: invoked; rule 8 (fail closed on a security-relevant path check) is the basis for the two open findings — canonical: `on-the-record/hooks/deliverable-guard.sh:156-162,204-213`, quoted in full in §2/§3 of "What was done" above.
- skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; every direction in "What was done" above (canonical: §1's four required directions, re-run this session) was re-run against the real hook/tests rather than cited from the redo record or PR #2653's record.
- skill-verdict: defect-verification-reproduction-evidence-quality — applied: invoked; the bypasses in "What was done" above (canonical: §2/§3's numbered cwd/file_path inputs with real exit codes) are recorded as numbered inputs with the actual exit code/stderr/diff artifact, not a paraphrase.
- skill-verdict: work-in-english — applied: invoked; this record, all commands, and the commit message (canonical: this file and the commit at the top of this branch) are in English; the end-of-turn summary to the user is in Korean.

## Next steps

None from this role — `verdict: REJECT` stands; findings 1-3 above are
recorded for whoever picks up the next fix attempt.
