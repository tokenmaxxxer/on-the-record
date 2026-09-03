---
issue: 3231
role: implementation-blueprint+silent-failure-audit+test-derivation-b51a2437
author: implementation-blueprint+silent-failure-audit+test-derivation-b51a2437
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: a0e30dcfba8308693754294e9a72541f839364db
loop_state: landed
type: repair-record
breaking: false
verdict: Repaired both defects PR #3238's independent verification found on
  PR #3235's commit a0e30dcf, re-derived with the same or equivalent commands
  the verification used, without touching anything it graded Present. Details
  and citations are in the body below (What was done, sections Fix 1/Fix 2).
upstream:
  - path: PR #3235 (tokenmaxxxer/on-the-record), commit a0e30dcfba8308693754294e9a72541f839364db
    sha: a0e30dcfba8308693754294e9a72541f839364db
  - path: docs/issue-3231/reports/adversarial-review+silent-failure-audit+test-depth-audit-0664d1ed.md (untracked in this checkout -- lives on main, not PR #3235's branch)
    sha: 1b7293da57db04f4f0d39cd9bb2c2a262301f538
---

# issue-3231 — implementation-blueprint+silent-failure-audit+test-derivation-b51a2437 record

## What was done

Round 2 on PR #3235. canonical: PR #3238's verification record
`docs/issue-3231/reports/adversarial-review+silent-failure-audit+test-depth-audit-0664d1ed.md`
(untracked in this checkout -- lives on main, not PR #3235's branch, sha
`1b7293da57db04f4f0d39cd9bb2c2a262301f538`, read this session via
`git show 1b7293da:docs/issue-3231/reports/adversarial-review+silent-failure-audit+test-depth-audit-0664d1ed.md`)
— its "Open findings" section 1 and 2 name the two defects fixed below;
sections 1-4, 6-8 graded Present and are the scope this round must not touch.

derived: `git checkout issue-3231/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-c01699d6` after
`git fetch origin issue-3231/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-c01699d6`
(this session) — landed at commit `a0e30dcf`, matching PR #3235's
`headRefName`/tip per `gh pr view 3235 --json headRefName` (this session,
result: `"headRefName":"issue-3231/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-c01699d6"`).
Per the task's explicit instruction, this round commits onto that same
branch/PR rather than opening a new one.

### Fix 1 — `ensure_skill_corpus_cli()`'s "always returns 0" contract

canonical: `plumbing.py:41-52` (`_run_net`, read this session):

```python
def _run_net(args: list[str], label: str, timeout: float = NETWORK_TIMEOUT,
             **kwargs) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, timeout=timeout, **kwargs)
    except subprocess.TimeoutExpired:
        sys.exit(f"{label}: 시간초과({int(timeout)}s) — 네트워크를 확인하라")
```

This `sys.exit()` on a real network timeout is correct for `_run_net`'s
orchestrator callers (issue #285 P5, cited in `_run_net`'s own docstring,
read this session). canonical: `skills.py:255-256` and `skills.py:278-280`
(`ensure_skill_corpus_cli()`'s docstring and inline comment, read this
session; both quoted verbatim in PR #3238's record section 5, re-read here
directly from the working tree) state the opposite contract for the caller:
"각각 실패해도 나머지를 막지 않는다(best-effort, 항상 0 을 돌려준다)" and
"`_skill_repo_root()` 자체는 sys.exit 하지 않는다". canonical: `skills.py:113`
before this fix (read this session on commit `a0e30dcf`, before any edit) —
`except OSError as exc:` around only the clone call, and the TTL-refresh
pull call (`skills.py:75-77` on that same commit) had no exception handler
at all. `OSError` does not catch `SystemExit` (not a subclass), so a real
timeout on either call escaped uncaught.

Fix, applied this session to `skills.py`'s `_skill_repo_managed_root()`:

```python
            if not _sp._pull_is_fresh(d):
                try:
                    _sp._run_net(["git", "-C", str(d), "pull", "-q", "--ff-only"],
                             "[skill-repo] pull")
                    _sp._mark_pulled(d)
                except SystemExit as exc:
                    print(f"[skill-repo] pull failed: {exc}", file=sys.stderr)
```
and
```python
        except (OSError, SystemExit) as exc:
            ...
            print(f"[skill-repo] fetch failed: {type(exc).__name__}: {exc}",
                  file=sys.stderr)
```
derived: `git diff a0e30dcf -- skills.py` (this session) shows this exact
diff, reproduced in the commit this record lands in.

Return value per failure class after this fix, derived by reading the
function body just edited (this session):

| Failure class | Existing valid corpus? | Return |
|---|---|---|
| Pull real timeout (`SystemExit`) | yes | existing `skills_dir` (refresh skipped, not fatal) |
| Clone real timeout (`SystemExit`) | no | `None` |
| Clone `OSError` (permission, disk-full, missing git) | no | `None` (unchanged) |
| Clone succeeds, content invalid (partial checkout) | no | `None` (unchanged must-not clause) |

`ensure_skill_corpus_cli()` itself was not edited — canonical: PR #3238's
record section 5 (read this session) already grades its `home_skills.mkdir()`
`try/except OSError` and unconditional `return 0` as correct; the violation
lived entirely inside `_skill_repo_managed_root()`, the one place that calls
`_run_net`.

derived: `python3 -m pytest tests/test_issue_3231_install_removals.py -q`
(this session, after the fix, on the current working tree) — result:
```
14 passed in 0.91s
```
(12 pre-existing + 2 new, added this session). The 2 new tests reproduce the
exact failure PR #3238 demonstrated live: a `_run_net` side effect that
raises `SystemExit` (matching `plumbing._run_net`'s real behavior on
`TimeoutExpired`, distinct from the existing `_fake_clone_interrupted`'s
non-zero-exit shape). derived: before applying the Fix 1 diff (`git stash`,
this session, then rerunning the same 2 new tests against the pre-fix
`skills.py`) — both fail with an uncaught `SystemExit` propagating out of
`spawn._skill_repo_root()` (pytest error output showed `E   SystemExit: ...`,
not an assertion failure); `git stash pop` (this session) restored the fix
before continuing.

### Fix 2 — the full-suite claim and the citation-line drift

canonical: `git log --oneline main..a0e30dcf -- skills.py` (this session) —
result: two commits touch `skills.py`, `101a9095` ("fix citation line
numbers shifted by the skills.py/spawn.py edits") followed later by
`b2f089ec` ("silent-failure-audit fix + structure-comprehension pass on
install-sufficiency.md"). derived: `git show b2f089ec --stat -- skills.py`
(this session) — result: `skills.py | 13 ++++++++--` (net +9 lines), landing
after `101a9095` had already synced the citation lines. derived:
`git log --oneline main..a0e30dcf -- scripts/preflight/consumer_preconditions.py`
(this session) — result: only `101a9095` touches that file on this branch;
nothing after it could have re-synced the anchors `b2f089ec` shifted. This
confirms the drift is caused by this PR's own commit ordering, not a
pre-existing or unrelated failure.

derived: `grep -n "def _skill_repo_root" skills.py` (this session, on the
working tree with the Fix 1 edit already applied) — result: `155:def
_skill_repo_root() -> Path | None:`. derived:
`grep -n '_local_skill_dirs(home' skills.py` (this session) — result:
`441:    tier3 = _sp._local_skill_dirs(home / ".claude" / "skills")`.
canonical: `scripts/preflight/consumer_preconditions.py:312-327` before this
fix (read this session) still said
`("skills.py", 122, "def _skill_repo_root")` and
`("skills.py", 408, '_local_skill_dirs(home / ".claude" / "skills")')`
(note: measured against the working tree after Fix 1's own line-adding edit,
so the offset from 122/408 is larger than the 9-line drift PR #3238 measured
against the PR's pre-Fix-1 commit `a0e30dcf` alone — both point at the same
underlying anchor-staleness defect).

Fix, applied this session to `scripts/preflight/consumer_preconditions.py`:
updated both `line_anchors` entries to `155` and `441` respectively, and
their adjacent `"source"` comments to match.

derived: `python3 -m pytest tests/test_issue_3182_citation_line_accuracy.py -q`
(this session, after the fix) — result:
```
10 passed in 0.94s
```

acceptance: `python3 -m pytest test/ tests/ on-the-record/hooks/ -q` (this
session, on the fixed working tree, run twice in a row to rule out a flake)
— result, both runs identical:
```
1253 passed, 3 xfailed, 2 warnings in ~33s
```
0 failed both times. The two warnings are pre-existing pinned-fixture-
divergence `UserWarning`s from `test_skill_candidates_floor.py`
(`SkillCandidatesPinnedFixtureDivergenceTest`, read in the pytest output this
session), unrelated to issue #3231 and not failures. 1253 is 2 more than the
PR's original claim of 1251, matching this round's own 2 added tests exactly
(1251 + 2 = 1253) — the PR's original "0 failed" claim now genuinely
reproduces.

### Acceptance checks (issue #3231's three official checks, this session)

acceptance: `python3 -m pytest tests/test_issue_3231_install_removals.py -q` — result:
```
14 passed in 0.91s
```
acceptance: `python3 -m pytest tests/test_issue_3182_preflight.py -q` — result:
```
12 passed in 13.47s
```
acceptance: `python3 -m pytest tests/test_issue_3182_install_sufficiency_doc.py -q` — result:
```
4 passed in 4.83s
```

### Kept unchanged (verification graded Present)

derived: `git diff --stat` against commit `a0e30dcf` (this session, on the
final working tree) — result:
```
 scripts/preflight/consumer_preconditions.py |  8 +++---
 skills.py                                   | 32 +++++++++++++++++++---
 tests/test_issue_3231_install_removals.py   | 41 +++++++++++++++++++++++++++++
 3 files changed, 73 insertions(+), 8 deletions(-)
```
No other file changed. `plumbing.py`, `spawn.py`,
`on-the-record/hooks/skill-corpus-bootstrap.sh`,
`on-the-record/hooks/install-precondition-notices.sh`,
`docs/handbooks/install-sufficiency.md`, `setup.md`, and `README.md` are all
absent from this diff, so the 5→7 satisfied-count, the atomic
clone-then-`os.replace()`, the kill/disk-full/unwritable-scratch/rename-
failure behavior, the concurrency lock, the no-overwrite-of-user-corpus
behavior, the read-only notices hook, and the doc-vs-code alignment — all
graded Present in PR #3238's record sections 1, 2, 3, 4, 6, 7, 8 (read this
session) — are untouched by this round.

## Why

canonical: PR #3238's record "Open findings" 1-2 (already cited above under
"What was done") named exactly two specific, already-reproduced defects
rather than asking for a fresh audit, so the approach here was targeted: fix
each at the exact location the verification's reproduction pointed to
(`skills.py:113`'s `except OSError`, and `consumer_preconditions.py`'s stale
`line_anchors`), re-derive commands equivalent to the ones the verification
used (quoted in Fix 1/Fix 2 above) to confirm each fix, and leave every other
code path untouched. derived: the "Kept unchanged" `git diff --stat` above
shows only the three files this round intended to touch, confirming nothing
else was edited.

For Fix 1, catching `SystemExit` at the two `_run_net` call sites inside
`_skill_repo_managed_root()` — rather than changing `_run_net` itself to
never `sys.exit()`, or leaning harder on the SessionStart hook's `|| true`
wrapper — is the only change that makes the violated function's own stated
contract true without weakening `_run_net`'s intentional fail-closed
behavior for its other (orchestrator) callers, which the task explicitly
said not to do. For Fix 2, `git log`/`git show` on the PR's own commit
sequence (cited above) gave a direct, checkable causation answer (a later
commit's line-count change re-drifting an earlier commit's already-applied
fix) rather than leaving root cause as an assumption, per the task's
instruction to establish causation before fixing.

## Upstream basis

- PR #3235 (`tokenmaxxxer/on-the-record`), commit `a0e30dcfba8308693754294e9a72541f839364db` — the branch this round committed onto directly. canonical: `gh pr view 3235 --json headRefName,state` (this session) confirmed the branch name and `state: OPEN` before checkout.
- PR #3238 (`tokenmaxxxer/on-the-record`) and its verification record `docs/issue-3231/reports/adversarial-review+silent-failure-audit+test-depth-audit-0664d1ed.md` (untracked in this checkout -- lives on main, not PR #3235's branch), merged to main as commit `1b7293da57db04f4f0d39cd9bb2c2a262301f538`. derived: `git show 1b7293da:docs/issue-3231/reports/adversarial-review+silent-failure-audit+test-depth-audit-0664d1ed.md` (this session) — read in full for both open findings' reproduction commands and root-cause pointers; both addressed in Fix 1/Fix 2 above.
- `docs/issue-3231/reports/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-c01699d6.md` (PR #3235's own builder record; lives on PR #3235's branch, present in this session's working tree, read this session at commit `fe213c47`) — read for the original claims under repair.

## Open findings

1. canonical: PR #3238's record, "Open findings" item 1 (`docs/issue-3231/reports/adversarial-review+silent-failure-audit+test-depth-audit-0664d1ed.md`, untracked in this checkout -- lives on main, read this session) — the `SystemExit` escape from `ensure_skill_corpus_cli()`'s "always returns 0" contract. Status: fixed, see Fix 1 above; derived: the 2 new regression tests plus the pre-fix `git stash` regression check both confirm the fix live (quoted in Fix 1 above).
2. canonical: PR #3238's record, "Open findings" item 2 (same file, read this session) — the full-suite "0 failed" claim not reproducing, caused by stale citation-line anchors. Status: fixed, see Fix 2 above; derived: `python3 -m pytest test/ tests/ on-the-record/hooks/ -q` reproduces 0 failed twice (quoted in Fix 2 above).
3. canonical: PR #3238's record, "Open findings" item 3 (same file, read this session) — `gh auth status`'s own `device-id` file write on a first-run machine, explicitly graded pre-existing and out of #3231/#3235's own diff by that same record (its own `git diff main pr-3235-review -- scripts/preflight/consumer_preconditions.py` showing no lines touching that check, per that record's section 7). Status: left untouched; this round's task named only findings 1 and 2 above.

## What did not work

None. Both defects reproduced exactly as PR #3238's record described once
checked out on the same commit (`a0e30dcf`), and both fixes were verifiable
with the same or equivalent commands the verification record used (plus new
regression tests for Fix 1, quoted above). No planned repair had to be
abandoned or descoped.

## Next steps

acceptance: `python3 -m pytest tests/test_issue_3231_install_removals.py tests/test_issue_3182_preflight.py tests/test_issue_3182_install_sufficiency_doc.py -q` (this session) — result:
```
30 passed
```
acceptance: `python3 -m pytest test/ tests/ on-the-record/hooks/ -q` (this session, run twice) — result:
```
1253 passed, 3 xfailed, 2 warnings
```
derived: `git status` / `git log -1` (this session, on this checkout) — the
working tree at commit time carries only the three files listed in "Kept
unchanged" above plus this record; the fix is committed onto PR #3235's own
branch and pushed. canonical: no `gh pr merge` or `gh pr review --approve`
call was made this session (this session's own tool-call history), so PR
#3235 remains open pending human review.
loop_state: landed for this record; the PR remains open pending human review.

skill-verdict: implementation-blueprint — not-applicable: both fixes are
small, localized edits (an added `except` clause at two call sites; two
corrected integer literals) inside a single existing module each, not new
multi-module structure or a fan-out needing a frozen contract.
skill-verdict: silent-failure-audit — applied: invoked; canonical:
`skills.py:74-77` on commit `a0e30dcf` before this session's edit (read this
session) shows the TTL-refresh pull's `_run_net` call had no exception
handler at all, a second, previously-unnamed instance of the same
`except OSError`-vs-`SystemExit` defect class PR #3238 named only for the
clone call site (`skills.py:113`) — found by re-auditing every `_run_net`
call site inside `_skill_repo_managed_root()`, not just the one already
pointed to, and fixed both.
skill-verdict: test-derivation — applied: invoked; derived the two new test
cases in `tests/test_issue_3231_install_removals.py` from PR #3238's own
reproduction shape (a `_run_net` side effect that raises `SystemExit`,
distinct from the existing `_fake_clone_interrupted`'s non-zero-exit
partition) crossed with the two corpus states the fix must hold across (no
prior corpus vs. an existing valid-but-stale corpus) — an equivalence-
partitioning split on "which corpus state was present when the timeout hit",
not a single generic regression test.
other mounted skills: not triggered.
