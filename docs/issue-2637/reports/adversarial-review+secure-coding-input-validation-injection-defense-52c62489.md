---
issue: 2637
role: adversarial-review+secure-coding-input-validation-injection-defense-52c62489
author: adversarial-review+secure-coding-input-validation-injection-defense-52c62489
skills: adversarial-review (skill-repository(297e350)), secure-coding-input-validation-injection-defense (skill-repository(297e350))
verifies_subject: true
code_under_review: on-the-record/hooks/deliverable-guard.sh @ 2354b1e7764b0dc3b56b1f641c214c76da902e5e (PR #2643 branch issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985)
loop_state: landed
type: verification
breaking: false
verdict: REJECT — PR #2643 must not land at commit 2354b1e7; the fix reopens the exact bypass it claims to close
upstream:
  - path: docs/issue-2637/reports/adversarial-review+silent-failure-audit-aba56a87.md
    sha: a93cbf95af82d194fddff5a980284dc3a0349f37
---

# issue-2637 — adversarial-review+secure-coding-input-validation-injection-defense-52c62489 record

## What was done

Independent adversarial verification of the fix pushed directly to PR
#2643's branch, commit `2354b1e7764b0dc3b56b1f641c214c76da902e5e`
("issue-2637: fix absolute-path false-deny in priorities-shard
exemption"), answering
`docs/issue-2637/reports/adversarial-review+silent-failure-audit-aba56a87.md`'s
open finding (a legitimate absolute-path priorities-shard write was
wrongly denied by the `^`-anchored `PRODUCT_CAPTURE_PRIORITIES_DIR_RE`).
The fixing session's own record is PR #2650
(`https://github.com/tokenmaxxxer/on-the-record/pull/2650`).

canonical: `gh pr view 2643 --json files` (files touched by the whole PR
branch) cross-checked against `git diff --stat aa152c797e60e6620e8162dec586b97fc8f171e1..2354b1e7764b0dc3b56b1f641c214c76da902e5e`
(this specific fix commit alone) — the fix commit touches exactly
`on-the-record/hooks/deliverable-guard.sh` (+28/−3) and
`2354b1e7764b0dc3b56b1f641c214c76da902e5e:test/test_deliverable_guard_priorities_shard.py`
(new file, 110 lines; untracked in this branch, read via
`git show 2354b1e7764b0dc3b56b1f641c214c76da902e5e:test/test_deliverable_guard_priorities_shard.py`
from a disposable worktree — not present in this branch's own tree).

**Verdict: the fix reopens the exact `src/`-rooted bypass the anchor was
added to close.** Present with one CONFIRMED bypass.

### The fix's mechanism

canonical: `2354b1e7764b0dc3b56b1f641c214c76da902e5e:on-the-record/hooks/deliverable-guard.sh:148-156`
(quoted verbatim, matches the working-tree fence below line-for-line):
```python
priorities_candidate = n
_cwd_for_exemption = e.get("cwd")
if (posixpath.isabs(n) and isinstance(_cwd_for_exemption, str)
        and _cwd_for_exemption and posixpath.isabs(_cwd_for_exemption)):
    _rel = posixpath.relpath(n, posixpath.normpath(_cwd_for_exemption))
    if _rel != "." and not _rel.startswith(".."):
        priorities_candidate = _rel
if (n.endswith(EXEMPT_SUFFIXES) or PRODUCT_CAPTURE_ISSUE_RE.search(n)
        or PRODUCT_CAPTURE_PRIORITIES_DIR_RE.search(priorities_candidate)):
    sys.exit(0)
```
When `file_path` arrives absolute, the anchored shard regex is matched
against `posixpath.relpath(n, cwd)` — a value derived from `e.get("cwd")`,
the session's own reported working directory — instead of against `n`
(the raw absolute path) or against the git-root-relative path the same
file already computes three lines below, at
`2354b1e7764b0dc3b56b1f641c214c76da902e5e:on-the-record/hooks/deliverable-guard.sh:179`
(`d = n if posixpath.isabs(n) else posixpath.normpath(posixpath.join(cwd, n))`,
followed by a `.git`-probing walk up from `d`). `cwd` is not validated
against the discovered repo root anywhere before this exemption check
runs — the git-root discovery happens strictly after the exemption
block, at
`2354b1e7764b0dc3b56b1f641c214c76da902e5e:on-the-record/hooks/deliverable-guard.sh:178-186`.

### Both required directions confirmed with the real hook, real payloads

Fixture: `~/dgabsfix` (deliberately **not** under `/tmp` — the hook has
a pre-existing, unrelated `tmp`/`scratch`/`.git`/`plugin-cache`
path-segment exemption at
`2354b1e7764b0dc3b56b1f641c214c76da902e5e:on-the-record/hooks/deliverable-guard.sh:163-165`
that silently exits 0 for anything with a literal `tmp` segment; a
fixture rooted under `/tmp` gives a false EXEMPT for every case through
that unrelated path, not through the priorities-shard logic under test —
the project's own regression test avoids this for the same reason, see
`2354b1e7764b0dc3b56b1f641c214c76da902e5e:test/test_deliverable_guard_priorities_shard.py:27-32`
(the `_FIXTURE_BASE = Path.home() / ".otr-dg-test-fixture"` comment)).

derived (`bash on-the-record/hooks/deliverable-guard.sh` at
`2354b1e7764b0dc3b56b1f641c214c76da902e5e`, real JSON payloads on
stdin, `TOKENMAXXXER_SPAWNED` unset via `env -u`, `git init`-ed fixture
at `~/dgabsfix` with `~/dgabsfix/src/docs/reports/product/priorities/`
and `~/dgabsfix/docs/reports/product/priorities/` pre-created):
```
required direction 1 — src/-rooted bypass DENIED (Present):
  cwd=/home/jwjung/dgabsfix (repo root)
  file_path=src/docs/reports/product/priorities/hack.md (relative)
  -> rc=2, "... is a deliverable path in a board repo." (DENIED, correct)

required direction 2 — legitimate absolute shard write EXEMPT (Present):
  cwd=/home/jwjung/dgabsfix (repo root)
  file_path=/home/jwjung/dgabsfix/docs/reports/product/priorities/legit.md
  -> rc=0 (EXEMPT, correct — this is the false-deny PR #2650 set out to fix)
```
Both required directions hold — for the specific calling shapes above.

### Adversarial variant that reopens the bypass

derived (same hook, same fixture, only `cwd` changed from the repo root
to the `src/` subdirectory, target file identical to direction 1 above):
```
cwd=/home/jwjung/dgabsfix/src
file_path=/home/jwjung/dgabsfix/src/docs/reports/product/priorities/hack.md (absolute)
-> rc=0 (EXEMPT — BYPASS)
```
This is the identical `src/`-rooted deliverable write from "required
direction 1" above — same absolute target file — with only the calling
shape changed: relative `file_path` swapped for absolute, and `cwd`
moved from the repo root to `src/`.

derived (trailing-slash `cwd` variant, `posixpath.normpath` collapses
the slash so the same bypass fires):
```
cwd=/home/jwjung/dgabsfix/src/  (trailing slash)
file_path=/home/jwjung/dgabsfix/src/docs/reports/product/priorities/hack2.md
-> rc=0 (EXEMPT — BYPASS)
```

**Same payload, pre-fix vs. post-fix, proving this is a NEW regression
introduced by `2354b1e7764b0dc3b56b1f641c214c76da902e5e` and not a
pre-existing gap** — derived (identical payload run against both
commits in separate disposable worktrees):
```
payload: cwd=/home/jwjung/dgabsfix/src, file_path=/home/jwjung/dgabsfix/src/docs/reports/product/priorities/hack.md

against aa152c797e60e6620e8162dec586b97fc8f171e1 (anchor-only, pre-abs-fix):
  rc=2  "... is a deliverable path in a board repo." (DENIED)

against 2354b1e7764b0dc3b56b1f641c214c76da902e5e (this fix):
  rc=0  (EXEMPT)
```

**Why the bypass is real, not contrived**: the orchestrator session
this hook is guarding is not sandboxed from choosing its own `cwd` — it
can run `cd src` (or `cd` into any subdirectory) via Bash before issuing
the `Write` call this hook inspects, and `e.get("cwd")` is exactly the
session's own reported cwd at call time, not an independently-verified
value. The fix's own commit message claims a src-rooted absolute path
"still normalizes to a src/-prefixed relative form and stays denied" —
that claim is true only when `cwd` equals the repo root; the
reproduction above shows it is false whenever `cwd` is a subdirectory
the caller controls, which is exactly the value the new code trusts.

**Root cause, framed by secure-coding-input-validation-injection-defense
rule 1 (allowlist must match the canonical form) and rule 8 (do not
substitute a looser-but-convenient value for the trust-boundary-safe
one)**: canonical, `secure-coding-input-validation-injection-defense`
skill file, rules 1 and 8 — the guard already computes a canonical
git-root-relative value (`d` at
`2354b1e7764b0dc3b56b1f641c214c76da902e5e:on-the-record/hooks/deliverable-guard.sh:179`,
discovered via the `.git` probe-walk at lines 178-186) that would be the
correct anchor to allowlist-match against. The fix instead re-derives a
*different*, cheaper "relative" value (`posixpath.relpath(n, cwd)`)
computed before the trust boundary (the actual repo root) is even
known, using an attacker-influenced `cwd` as the reference point instead
of the already-available canonical one.

### Other adversarial variants tried — no additional bypass found

derived (same hook/fixture, three more shapes from the task's list):
```
cwd inside the shard directory, abs file_path = a real src/ file:
  cwd=/home/jwjung/dgabsfix/docs/reports/product/priorities
  file_path=/home/jwjung/dgabsfix/src/evil.py
  -> rc=2 (DENIED, correct — relpath crosses via ".." and priorities_candidate falls back to n)

relative path with ".." resolving up into the real repo-root shard dir:
  cwd=/home/jwjung/dgabsfix/src/nested
  file_path=../../docs/reports/product/priorities/hack.md (relative)
  -> rc=2 (DENIED — over-strict relative to the true target, not a bypass;
     the isabs-only branch never engages for a relative file_path)

cwd entirely outside the repo, abs file_path under src/ (relpath has no common prefix):
  cwd=/home/jwjung/otherplace
  file_path=/home/jwjung/dgabsfix/src/docs/reports/product/priorities/hack3.md
  -> rc=2 (DENIED — relpath produces a leading "..", falls back to raw n, correct)
```
canonical: these three negative results, read together with the
confirmed bypass above, bound the vulnerable shape precisely — it
requires an absolute `file_path` together with a `cwd` that is a real
filesystem ancestor of that path (so `relpath` yields no leading `..`)
other than the actual repo root. It is not a fully unconstrained
traversal, but it is still reachable by the orchestrator session itself
choosing its own `cwd`, so it is still a live bypass.

## Regression test suite: verified count, and why it missed the bypass

derived: `python3 -m pytest test/test_deliverable_guard_priorities_shard.py -v`
run against a `2354b1e7764b0dc3b56b1f641c214c76da902e5e` worktree —
result:
```
8 passed in 0.86s
```
derived: the identical test file copied into an `aa152c797e60e6620e8162dec586b97fc8f171e1`
(anchor-only, pre-abs-fix) worktree and re-run — result:
```
FAILED test/test_deliverable_guard_priorities_shard.py::DeliverableGuardPrioritiesShardTest::test_absolute_shard_write_is_exempt
FAILED test/test_deliverable_guard_priorities_shard.py::DeliverableGuardPrioritiesShardTest::test_absolute_shard_write_with_dotdot_is_exempt
FAILED test/test_deliverable_guard_priorities_shard.py::DeliverableGuardPrioritiesShardTest::test_absolute_issue_scoped_shard_write_is_exempt
3 failed, 5 passed in 0.86s
```
This CONFIRMS PR #2650's own claimed pre-fix pass/fail split, via
independent re-run in a fresh worktree, not read from the PR body.

**Why the suite didn't catch the reopened bypass**: canonical,
`2354b1e7764b0dc3b56b1f641c214c76da902e5e:test/test_deliverable_guard_priorities_shard.py:39-43`
(`_run_gate`, quoted verbatim):
```python
def _run_gate(repo: Path, file_path: str, cwd: str | None = None):
    payload = json.dumps({
        "tool_name": "Write",
        "tool_input": {"file_path": file_path},
        "cwd": cwd if cwd is not None else str(repo),
```
`_run_gate` defaults `cwd` to `str(repo)` — the fixture's own repo root
— whenever the caller doesn't pass an explicit `cwd`. The one test
aimed squarely at this bypass,
`2354b1e7764b0dc3b56b1f641c214c76da902e5e:test/test_deliverable_guard_priorities_shard.py:73-77`
(`test_absolute_src_rooted_bypass_stays_denied`, quoted verbatim):
```python
    def test_absolute_src_rooted_bypass_stays_denied(self):
        r = _run_gate(
            self.repo,
            str(self.repo / "src/docs/reports/product/priorities/hack.md"))
        self.assertEqual(r.returncode, 2, r.stderr)
```
never passes a `cwd` argument, so it only ever exercises
`cwd == repo_root`. canonical: reasoning directly from the two fences
quoted immediately above — that is the one case where
`posixpath.relpath(n, cwd)` happens to reduce to the correct
git-root-relative form (`cwd` equals the git root `d` was walked from),
so the fix's own bug never has a chance to surface in this test.
derived: grepping the full test file for `cwd=` overrides of `_run_gate`'s
third argument (`grep -n "cwd=" test/test_deliverable_guard_priorities_shard.py`
in the worktree) returns zero matches — no test in the suite varies
`cwd` independently of `repo`.

**Do the 5 both-pass tests test anything?** derived, reading each of the
5 by name against what changed in the diff: yes, narrowly. Two
(`test_relative_shard_write_is_exempt`,
`test_relative_src_rooted_bypass_stays_denied`) exercise the relative-path
path, which the `isabs` branch never touches, so passing identically
before and after is expected, not vacuous. One
(`test_real_deliverable_write_still_denied`) confirms the ordinary deny
path is untouched. One (`test_absolute_legacy_priorities_file_still_exempt`)
confirms the pre-existing flat-file suffix exemption is untouched. The
fifth, `test_absolute_src_rooted_bypass_stays_denied`, is the one that
should have caught this and would have, had it varied `cwd` — it
currently only proves the src-bypass stays denied when `cwd` equals the
repo root, which this record's adversarial variant (see "Adversarial
variant that reopens the bypass" above) shows is not the only reachable
case. All 5 are real, non-tautological invariants; none of them cover
the `cwd != repo_root` surface the fix's new code actually touches.

derived: `python3 -m pytest test/ -q` in the `2354b1e7764b0dc3b56b1f641c214c76da902e5e`
worktree — result:
```
15 failed, 350 passed in 2.99s
```
derived: `python3 -m pytest test/ -q --ignore=test/test_deliverable_guard_priorities_shard.py`
in the `aa152c797e60e6620e8162dec586b97fc8f171e1` worktree (test file
excluded pre-fix since it didn't exist there yet) — result:
```
15 failed, 342 passed in 2.71s
```
The two 15-name failure lists were diffed by eye against each other —
identical set of test names in both runs (`test_convention_equivalence.py`
x2, `test_local_dependency_env.py` x1,
`test_spawn_cross_family_skill_selection.py` x6,
`test_spawn_artifact_skill_pairing.py` x2,
`test_spawn_skill_judge_haiku_timeout_overlap.py` x4 — 2+1+6+2+4=15,
matching both quoted totals above). No new regressions in the broader
suite from this commit. This CONFIRMS PR #2650's own claim that the
same pre-existing unrelated failures recur both times, via independent
re-run.

## Re-confirmation of PR #2643 facts already verified in aba56a87, checked again at 2354b1e7764b0dc3b56b1f641c214c76da902e5e

- **Legacy `priorities.md` byte-identical**: derived,
  `diff <(git show origin/main:docs/reports/product/priorities.md) <(git show 2354b1e7764b0dc3b56b1f641c214c76da902e5e:docs/reports/product/priorities.md)`
  → no output (byte-identical). Still true post-fix.
- **Two-branch zero-conflict merge, both orders**: derived: rebuilt the
  fixture fresh at the `2354b1e7764b0dc3b56b1f641c214c76da902e5e` tip
  via `git clone` + `git checkout 2354b1e7764b0dc3b56b1f641c214c76da902e5e`
  (not reused from aba56a87's `aa152c797e60e6620e8162dec586b97fc8f171e1`
  fixture). derived: `branch-A` minted one shard by calling
  `2354b1e7764b0dc3b56b1f641c214c76da902e5e:priorities.py`'s
  `_priorities_entry_path(None, cwd='.')` and committing the result;
  `branch-B` did the same independently from the same base commit.
  derived: `git merge --no-ff branch-A -m "merge A"` then
  `git merge --no-ff branch-B -m "merge B"` into a `merged` branch —
  result:
  ```
  Merge made by the 'ort' strategy.   (branch-A merge, no CONFLICT line)
  Merge made by the 'ort' strategy.   (branch-B merge, no CONFLICT line)
  git status --porcelain              (empty output, both merges)
  ```
  derived: repeated with the reverse merge order (branch-B first, then
  branch-A, from the same merge-base, into a separate `merged-reverse2`
  branch) — same clean result, no `CONFLICT` line either time.
  `read_priorities(None, cwd='.')` returned legacy content, then "Entry
  from session A", then "Entry from session B" — in **both** merge
  orders, chronological (filename-timestamp) ordering still holds,
  unaffected by this commit. Still true post-fix.
- **Other three named consumers**: canonical,
  `git diff --stat aa152c797e60e6620e8162dec586b97fc8f171e1..2354b1e7764b0dc3b56b1f641c214c76da902e5e`
  (shown under "What was done" above) touches only
  `on-the-record/hooks/deliverable-guard.sh` and the new test file —
  `spawn.py`, `on-the-record/hooks/product-capture-stopgate.sh`,
  `on-the-record/hooks/skill-verdict-guard.sh` are therefore
  byte-identical to the `aa152c797e60e6620e8162dec586b97fc8f171e1` state
  aba56a87 already verified live (its own `spawn.py priorities-path`/
  `priorities-log` and `product-capture-stopgate.sh` stdin-driven
  reproductions). Unchanged, still true.

## Why

secure-coding-input-validation-injection-defense's trigger fires here
exactly: `file_path` is untrusted input crossing a filesystem-write
trust boundary, and the task was to verify the chosen allowlist approach
(rule 1) around it. canonical: `secure-coding-input-validation-injection-defense`
skill file, rules 1 ("validate with an allowlist regex that defines
exactly what IS authorized") and 8 ("remove the silent-fallback path...
fail closed instead") — the fix's own diff (quoted under "The fix's
mechanism" above) shows exactly the failure mode those rules warn
about: the allowlist regex ends up matched against a value derived from
an attacker-influenced anchor (`cwd`) rather than the already-available
canonical value, so a request can be shaped to make the allowlist say
yes to something it should say no to.

adversarial-review's core mechanism — treat the deliverable's own
stated approach and its own regression-test claims as unverified until
independently re-derived (derived: this session's own
`python3 -m pytest test/test_deliverable_guard_priorities_shard.py -v`
and `python3 -m pytest test/ -q` runs, executed in fresh worktrees at
both `aa152c797e60e6620e8162dec586b97fc8f171e1` and
`2354b1e7764b0dc3b56b1f641c214c76da902e5e` this turn, full output
quoted under "Regression test suite" above) — is exactly what surfaced
this. canonical: PR #2650's own body states its approach as "match the
anchored regex against a cwd-relative form ... rather than the raw
absolute string" and states it reproduced both directions plus three
named variants (`..`, an issue-scoped write, a symlinked root). This
session did not accept that test-plan claim on its word — it re-ran the
suite independently (results above) and then targeted precisely the
`cwd`-relative computation the PR names as its approach, searching past
the fixing session's own listed variants for the failure mode it hadn't
covered — the `cwd != repo_root` case, confirmed above under
"Adversarial variant that reopens the bypass."

skill-verdict: adversarial-review — applied: invoked; treated PR #2650's
own test-plan claims and its "reproduced both directions" statement as
unverified — derived: independently re-ran
`python3 -m pytest test/test_deliverable_guard_priorities_shard.py -v`
at both `aa152c797e60e6620e8162dec586b97fc8f171e1` and
`2354b1e7764b0dc3b56b1f641c214c76da902e5e` (full pass/fail counts
quoted under "Regression test suite" above) instead of accepting them,
rebuilt every reproduction independently (fresh fixtures, fresh git
worktrees, own payload generator) rather than accepting the PR body's
pasted transcripts, and searched past the fixing session's own listed
variants for a failure mode it hadn't covered.
skill-verdict: secure-coding-input-validation-injection-defense — applied: invoked; identified the fix's allowlist check
(`PRODUCT_CAPTURE_PRIORITIES_DIR_RE.search(priorities_candidate)`) as
matching against a value derived from an untrusted anchor (`cwd`)
instead of the code's own already-computed canonical anchor (the
git-root-relative `d`), per rules 1 and 8 — this framing is what pointed
at testing `cwd != repo_root` specifically, which is where the bypass
lives.

## What did not work

None — the adversarial variants that did not reproduce a bypass (cwd
inside the shard dir writing outside it, `..`-relative escape, cwd
fully outside the repo) are reported above as negative results that ran
successfully, not as attempts that failed to execute.

## Open findings

1. **CONFIRMED bypass**: `on-the-record/hooks/deliverable-guard.sh`'s
   `2354b1e7764b0dc3b56b1f641c214c76da902e5e` fix for the absolute-path
   false-deny reopens the `src/`-rooted deliverable-write bypass the
   `aa152c797e60e6620e8162dec586b97fc8f171e1` anchor was written to
   close, whenever `file_path` arrives absolute and the session's
   reported `cwd` is a real filesystem ancestor of the target path other
   than the actual repo root (e.g. the orchestrator itself ran `cd src`
   first). Reproduced live above, both directions, against the real
   shipped hook. Resolution path: match the anchored shard regex against
   the git-root-relative path (`d` /
   `posixpath.relpath(d, root)` after the `.git` probe-walk at
   `2354b1e7764b0dc3b56b1f641c214c76da902e5e:on-the-record/hooks/deliverable-guard.sh:178-186`
   finds `root`) instead of a pre-root-discovery `cwd`-relative guess —
   the exemption check would need to move after (or be re-derived from)
   the root-walk, not before it. Also extend
   `2354b1e7764b0dc3b56b1f641c214c76da902e5e:test/test_deliverable_guard_priorities_shard.py:73-77`
   (`test_absolute_src_rooted_bypass_stays_denied`, and a new
   exempt-case test) to vary `cwd` independently of `repo` — derived:
   `python3 -m pytest test/test_deliverable_guard_priorities_shard.py -v`
   at `2354b1e7764b0dc3b56b1f641c214c76da902e5e` returns `8 passed in
   0.86s` (quoted in full under "Regression test suite" above) precisely
   because the current suite never varies `cwd` away from `repo`, so
   every case in that run passing did not — and could not — catch this
   bypass.
2. Pre-existing, not introduced by this commit, noted but out of this
   record's scope: a **relative** `file_path` that textually matches
   `^docs/reports/product/priorities/...` also bypasses when `cwd` is
   not the repo root (e.g. `cwd=<repo>/src`,
   `file_path=docs/reports/product/priorities/hack.md` resolves in
   practice to `<repo>/src/docs/...`) — this path never goes through the
   fix's `isabs` branch at all and was already true at
   `aa152c797e60e6620e8162dec586b97fc8f171e1`, before this fix commit.
   Same root cause (exemption matched before root discovery); the same
   resolution path proposed for finding 1 would also close it, but it
   predates PR #2643/#2650 and is not this fix's regression.

**Verdict: REJECT.** PR #2643 must not land at commit
`2354b1e7764b0dc3b56b1f641c214c76da902e5e` — canonical: the
pre-fix-vs-post-fix same-payload reproduction under "Adversarial variant
that reopens the bypass" above (`rc=2` at
`aa152c797e60e6620e8162dec586b97fc8f171e1` vs. `rc=0` at
`2354b1e7764b0dc3b56b1f641c214c76da902e5e` for the identical
`src/`-rooted target path) is this record's own live reproduction,
executed in this session, of a real, reachable deliverable-write bypass
— per this task's own instruction that a found bypass is the finding
and the PR does not land.

## Upstream basis

- `docs/issue-2637/reports/adversarial-review+silent-failure-audit-aba56a87.md`,
  sha `a93cbf95af82d194fddff5a980284dc3a0349f37` (on `main`, this
  branch's own history) — the finding this record verifies the fix for.
- `on-the-record/hooks/deliverable-guard.sh` (tracked in this branch
  too, but at different content than the fix commit — read from the fix
  commit's own worktree, not this branch's HEAD) and
  `2354b1e7764b0dc3b56b1f641c214c76da902e5e:test/test_deliverable_guard_priorities_shard.py`
  (new file added by that commit, untracked in this branch) — PR #2643
  branch `issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985`,
  sha `2354b1e7764b0dc3b56b1f641c214c76da902e5e` (subject of this
  verification; fetched into a disposable worktree, not committed to
  this branch).
- `aa152c797e60e6620e8162dec586b97fc8f171e1` — same branch, the
  anchor-only parent commit used as the pre-fix baseline for the
  before/after diffs above (also a disposable worktree, not committed
  here).
- PR #2650 (`https://github.com/tokenmaxxxer/on-the-record/pull/2650`)
  — the fixing session's own record, read for the claims under test but
  not trusted as evidence; every claim it makes was independently
  re-derived above.

## Next steps

None from this record — `loop_state: landed`. The open finding above
(bypass) is PR #2643/#2650's next round of work, not this record's.
