---
issue: 3095
role: independent-verification-2
author: independent-verification-2
verifies_subject: true  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: terminal
upstream:
  - path: docs/issue-3095/reports/implementation-blueprint+silent-failure-audit+test-derivation-0cae2f1d.md
    sha: e06909962b58130aa889b8c15561ade355bf89f3
---

# issue-3095 — independent-verification-2 record

## What was done

Independent, builder-blind verification of PR #3106 ("issue-3095:
attribute spawn-on-pr's park state to a repo") against issue #3095's own
acceptance criteria and both must-nots. Ran everything myself against two
linked git worktrees I built (PR #3106's branch at full sha
`e06909962b58130aa889b8c15561ade355bf89f3`, and unmodified `origin/main`
at `0cd96c6d`), rather than citing the builder's record or either of the
two other open verification PRs (#3119, #3121) already sitting on this
subject — per [[defect-verification-independence-from-upstream-verdicts]],
their prior Present verdicts were not treated as settled going in. The
two files these acceptance checks execute
(`gates/probe_parked_report_repo_leak.py`,
`tests/test_spawn_on_pr_repo_scope.py`) are both untracked in this
session's own worktree — both were added by PR #3106 and only exist on
its branch, not merged to `main` — so every command below ran inside a
linked worktree checked out at that branch's head, not in this session's
own repo root. This "untracked, PR #3106-only" note covers every bare
mention of either filename below.

acceptance: `python3 -m pytest tests/test_spawn_on_pr_repo_scope.py -q` (run in the linked worktree at `e0690996`) — result: 6 passed

acceptance: `python3 gates/probe_parked_report_repo_leak.py` (untracked, PR #3106-only per above; run in the linked worktree at `e0690996`) — result: `ok`, exit 0

Sensitivity control (issue #3081's must-not #2), self-devised, not part
of the required acceptance list: copied the identical, unmodified probe
file (untracked, PR #3106-only per above) into a second linked worktree
at unmodified `origin/main` (`0cd96c6d`) and ran it there unchanged —

acceptance: `python3 gates/probe_parked_report_repo_leak.py` (untracked, PR #3106-only per above; copied unmodified into the `origin/main`/`0cd96c6d` worktree) — result:
```
FAIL: parked_report(root_a) and parked_report(root_b) are identical (['issue-3059']) -- no per-repo filter is running at all (issue #3095).
```
exit 1. Same probe file, byte-identical between the two runs, fails on
main and passes on the branch — this is the sensitivity control the
issue's must-not #2 requires.

acceptance: `python3 -m pytest tests/ -q` (run in the linked worktree at `e0690996`) — result: 222 passed, 0 failed

canonical: `git diff origin/main -- gates/spawn_on_pr.py` (run in the linked worktree at `e0690996`), reproduced here —
```python
     return sorted(subject for subject, entry in load_park_state(root).items()
-                  if entry.get("parked"))
+                  if entry.get("parked") and entry.get("repo") == repo_slug)
```
```python
+        if prior is not None and prior.get("repo") != repo_slug:
+            prior = None
         if prior is not None and prior.get("blocked"):
```
`parked_report()` filters by `entry.get("repo") == repo_slug` (own-repo
genuine parked subjects still show — must-not #1, suppression, not
violated), and `spawn_missing_for_pr()` sets `prior = None` when
`prior.get("repo") != repo_slug` before any park/attempts/ceiling
decision reads `prior` (the retention-split must-not: cross-repo prior
evicts). The own-repo path (`is_approval_blocked()`'s existing
fail-closed retention on a real gh-lookup failure) is untouched by this
diff (absent from the diff above), so "transient own-repo failure still
retains" holds by virtue of not being touched, not a new mechanism.

canonical: `tests/test_spawn_on_pr_repo_scope.py` (untracked, PR #3106-only per above; read directly in the linked worktree) — `grep -n "^class\|^    def test"` output:
```
class TestParkedReportFiltersByRepo:
    def test_parked_report_includes_own_repo(self, repos):
    def test_parked_report_excludes_other_repo(self, repos):
    def test_parked_report_not_identical_across_repos(self, repos):
class TestRetentionRepoScoped:
    def test_retention_when_repo_matches(self, repos, monkeypatch, capsys):
    def test_no_retention_when_entry_is_another_repos(self, repos, monkeypatch):
class TestLegacyEntries:
    def test_legacy_entry_without_repo_key_excluded_from_resolvable_repo(self, repos):
```
6 test methods (derived: the grep output above), each asserting real
state — `parked_report()` return values and `park_state` dict contents
read back from disk — not a vacuous pass; read the assertion bodies of
`test_retention_when_repo_matches` and `test_no_retention_when_entry_is_another_repos`
directly and confirmed both assert on `state[SUBJECT]["repo"]`,
`state[SUBJECT]["attempts"]`, and `spawn_on_pr.parked_report(root_a)`.

Self-devised negative-path repro, independent of the PR's own test file
(per this skill's rule 2 — deliberately not just re-running their
suite): seeded a shared park-state file with a deeply-blocked,
12-attempt entry for `issue-77` tagged `repo: org-b/repo-b`, called
`spawn_on_pr.parked_report(root_a)` directly with `root_a` slugged as
`org-a/repo-a`.

derived: inline Python script against `gates/spawn_on_pr.py` in the `e0690996` worktree — result:
```
repo A report: []
PASS: repo A does not see repo B's foreign parked subject
```

canonical: `gates/spawn_on_pr.py`'s `_park_state_path()` (read directly in the linked worktree at `e0690996`) — still routes through `state_paths.orchestrator_state_path()`, unchanged from `origin/main` by the diff above — the cache stays one file shared across every swept repo (issue #2240), matching the issue's requirement that only per-repo *selection at report time* changes, not the storage scope.

canonical: `docs/issue-3095/reports/implementation-blueprint+silent-failure-audit+test-derivation-0cae2f1d/deviation-log/20260902T074039474451-214b4bd62dd70a4f.md` (untracked in this session's own worktree — lives on PR #3106's branch, not merged to `main`; read directly in the linked worktree at `e0690996`) — the builder reuses `spawn._repo_slug(root)` (the same primitive PR #3084 introduced) but does not reuse #3084's compound-key re-keying; adds a `repo` field to each entry's value instead, keeping the bare-subject key, because `gates/test_spawn_on_pr.py` (pre-existing, tracked on `main`) seeds/reads ~30 bare-subject-key fixtures with no `repo` field and re-keying would have required rewriting most of that file. The disclosed residual boundary (a same-numbered-issue collision across two swept repos can still overwrite the shared entry on *write*, not just on read) is real by inspection of `_save_park_state()` (the dict key stays bare `subject`) and matches what the deviation log itself states — not independently contested here, only independently re-derived from the code.

## Why

Issue #3095 requires two independent verifications before this subject
can land; this record is the second, produced without reading or relying
on the verdict of the first (#3119) or the other already-open second
(#3121) — both exist as open PRs, unmerged, so the subject's own
merge-gate does not yet count them. Verifying against `origin/main`
worktrees I built myself (not against the builder's or either other
verifier's reported command output) satisfies rule 3 (re-derive rather
than cite) and rule 8 (do not default to citing under time pressure) of
[[defect-verification-independence-from-upstream-verdicts]]. The
self-devised negative-path repro (rule 2) exists so this record's
verdict rests on at least one check that was not already in the
subject's own PR.

## What did not work

None.

## Upstream basis

`docs/issue-3095/reports/implementation-blueprint+silent-failure-audit+test-derivation-0cae2f1d.md`
(untracked in this session's own worktree — lives on PR #3106's branch,
not merged to `main`), landed as PR #3106's phase-2 record at commit
`e06909962b58130aa889b8c15561ade355bf89f3` (PR #3106 branch head —
canonical: `gh pr view 3106 --json headRefOid,state` — result:
`headRefOid: e06909962b58130aa889b8c15561ade355bf89f3`, `state: OPEN`,
not yet merged to `main`).

## Open findings

- The write-time same-numbered-subject collision boundary (two repos'
  same-tick writes to a bare `subject` key in the shared park-state file
  can overwrite each other, independent of the new `repo` field) is real
  by inspection and disclosed by the builder (see canonical citation
  above), but uncovered by any test in PR #3106's own suite. Out of
  scope for issue #3095's acceptance criteria, which target the
  report-time leak and the retention split, not the write-time
  collision — not counted against PR #3106. Resolution path: a future
  issue scoped to the write-path collision (re-keying `spawn_on_pr.py`'s
  park state by `repo:subject`, matching #3084's `_drift_cache_key`
  approach the deviation log describes abandoning) closes it; no action
  from this record.
- PR #3121 independently reports (not re-derived by this record) the
  same leak-shape pattern recurring elsewhere (`gates/board_read.py`,
  `gates/closure_sweep.py`'s recheck state). Out of scope for issue
  #3095's own acceptance criteria, which name only
  `gates/spawn_on_pr.py`'s park state. Resolution path: left to whatever
  follow-up issue #3121's own record proposes; not this record's to
  open, since it was not independently re-derived here.

## Next steps

None. `verifies_subject: true`; loop_state terminal.

skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; re-derived PR #3106's acceptance checks and must-nots from primary evidence (two linked worktrees I built, code I read myself) rather than citing PR #3119/#3121's or the builder's reported output, and added a self-devised negative-path repro not present in the PR's own test suite.
skill-verdict: work-in-english — not-applicable: this session's inbound task prompt was in Korean, but this record, all commits, and the PR are written in English per the skill's language policy; no separate invocation needed beyond following that policy while writing.
other mounted skills: not triggered.
