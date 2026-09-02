---
issue: 3081
role: adversarial-review+test-depth-audit+defect-verification-reproduction-evidence-quality-98387fb6
author: adversarial-review+test-depth-audit+defect-verification-reproduction-evidence-quality-98387fb6
skills: adversarial-review (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12)), defect-verification-reproduction-evidence-quality (skill-repository(c05de12))
verifies_subject: true  # second independent, builder-blind verification of PR #3084's own deliverable against issue #3081
loop_state: landed
code_under_review: 4fefe107db388bb2eb8b6439a0274549a8b84f59
type: defect-verification-record
breaking: false
verdict: 4 of 6 checked criteria Present. 1 Absent -- the issue's explicit
  must-not about spawn_on_pr's waiting-for-human list was never
  investigated by the builder, and this session's own reproduction (see
  "must-not 3" section) shows it leaks identically and remains unfixed. 1
  Incorrect as an evidence instrument -- the issue's own literal
  acceptance check 1 passes vacuously on both pre-fix and post-fix code.
upstream:
  - path: watchdog.py
    sha: 4fefe107db388bb2eb8b6439a0274549a8b84f59
  - path: gates/spawn_on_pr.py
    sha: 4fefe107db388bb2eb8b6439a0274549a8b84f59
---

# issue-3081 — adversarial-review+test-depth-audit+defect-verification-reproduction-evidence-quality-98387fb6 record

## What was done

canonical: `gh pr view 3084 --repo tokenmaxxxer/on-the-record` and
`gh issue view 3081 --repo tokenmaxxxer/on-the-record --comments` (7
comments read in full). This is a second independent, builder-blind
verification of PR #3084 (branch head 4fefe107db388bb2eb8b6439a0274549a8b84f59)
against issue #3081 -- a different verification is running in parallel;
this record reaches its own verdict by executing code, not by reading the
other session's output.

amendments-reconciled: `issuecomment-5505985986` (landed mid-session,
after this session's worktree analysis was already underway) -- reports
PR #3084 merged and issue #3081 closed, with a before/after production
heartbeat sample confirming both the cross-repo leak and the retention
misreport are gone in the live system. The same comment also states
"Issue #3095 tracks the sibling leak in `spawn_on_pr.parked_report()`,
which both verifications found unfixed" -- confirming this session's own
independently-reproduced "must-not 3" finding (below) converges with the
parallel verification session's finding, and that a tracking issue for it
already exists.
derived: `gh issue view 3081 --repo tokenmaxxxer/on-the-record --json
state` -- result: `{"state":"CLOSED"}`. `gh issue view 3095 --repo
tokenmaxxxer/on-the-record --json state,title` -- result:
`{"state":"OPEN","title":"spawn-on-pr's parked-subject list leaks across
repos the same way requirement-drift did"}`.

Setup for everything below: `git fetch origin pull/3084/head:pr-3084` then
`git worktree add /tmp/pr3084-wt pr-3084` (PR #3084's branch) and
`git worktree add /tmp/main-wt 573e7382` (the pre-fix parent commit) --
two linked worktrees of this repo, so every command below ran the actual
PR/main code, not a paraphrase.

### Criterion 1 -- a heartbeat tagged with a repo reports only that repo's issues/PRs

PR #3084 adds a probe (gates/probe_drift_repo_leak.py, not present on this
session's own branch -- only on PR #3084's branch) and a test file
(tests/test_requirement_drift_repo_scope.py, same caveat). Both were run
directly from the PR #3084 worktree, then this session wrote and ran its
own adversarial probe covering four cases those do not.

derived: `python3 -m pytest tests/test_requirement_drift_repo_scope.py -q`
(run from /tmp/pr3084-wt) -- result: `7 passed`.
derived: `python3 gates/probe_drift_repo_leak.py` (run from
/tmp/pr3084-wt) -- result: `ok`, exit 0.
derived: `python3 gates/probe_drift_repo_leak.py` (run from /tmp/main-wt,
the pre-fix parent commit 573e7382282be24439c223c1603be648dd0e158f, after
copying the probe file over since it does not exist pre-fix) -- result:
exit 1,
```
FAIL: repo B's number 77 appeared in repo A's sweep output -- a cache entry leaked across repos without attribution (issue #3081). Full output:
[watchdog] requirement-drift: 요구 R001 — 다이제스트: "something" (source: #1) — 열린 이슈/PR 어디에도 인용되지 않는다. 후보(요구 인용이 전혀 없는 열린 이슈/PR): [77, 3048, 3051]
[watchdog] requirement-drift: 요구 ID 를 전혀 인용하지 않는 열린 이슈/PR [77, 3048, 3051]
```
Confirms the PR's own probe genuinely discriminates pre-fix from
post-fix.

This session wrote its own adversarial probe (full script reproduced
below), covering: (A) an entry for a repo the orchestrator never swept in
this process, (B) a legacy cache entry with no "repo" key at all
(pre-existing polluted cache), (C) two repos with an overlapping issue/PR
number, (D) a repo with zero drift entries of its own but a shared cache
full of other repos' entries. It mocks only the external boundary
(spawn._repo_slug, spawn._fetch_issue_or_pr_via_cache) -- the same
network boundary the PR's own probe mocks -- and exercises the real
cache read/write/filter/print code otherwise:

```python
def main():
    tmp = Path(tempfile.mkdtemp(prefix="adversarial-drift-"))
    try:
        root_a, root_b, root_c = tmp/"repo-a", tmp/"repo-b", tmp/"repo-c"
        for r in (root_a, root_b, root_c):
            _write_digest(r)
        slug_map = {root_a: REPO_A, root_b: REPO_B, root_c: REPO_C}
        with mock.patch.object(state_paths, "STATE_ROOT", tmp / "state"), \
             mock.patch.object(spawn, "_repo_slug", side_effect=lambda r: slug_map[r]):
            # A: repo C, never swept before, must not see A's/B's numbers
            _sweep(root_a, {3048}); _sweep(root_b, {77})
            out_c = _reuse_only(root_c)
            assert "3048" not in out_c and "77" not in out_c
            # B: a legacy (no "repo" key) entry written directly to the
            # cache file must not leak into ANY repo's report, and must
            # not survive being loaded+resaved
            cache_path = spawn._requirement_drift_cache_path(root_a)
            cache = json.loads(cache_path.read_text())
            cache["9999"] = {"title": "", "body": "cites nothing",
                              "cached_at": "2020-01-01T00:00:00+00:00"}
            cache_path.write_text(json.dumps(cache))
            assert "9999" not in _reuse_only(root_a)
            assert "9999" not in _reuse_only(root_b)
            assert "9999" not in json.loads(cache_path.read_text())
            # C: two repos both cache a PR numbered #555 -- each must keep
            # its own body, the composite key must not collide
            root_a2, root_d = tmp/"repo-a2", tmp/"repo-d"
            _write_digest(root_a2); _write_digest(root_d)
            slug_map[root_a2] = "octo/overlap-a"; slug_map[root_d] = "octo/overlap-d"
            _sweep(root_a2, {555}, {555: "repo-a2 body for 555"})
            _sweep(root_d, {555}, {555: "repo-d body for 555"})
            assert "555" in _reuse_only(root_a2) and "555" in _reuse_only(root_d)
            cache2 = json.loads(spawn._requirement_drift_cache_path(root_a2).read_text())
            k_a2 = spawn._drift_cache_key("octo/overlap-a", 555)
            k_d = spawn._drift_cache_key("octo/overlap-d", 555)
            assert k_a2 in cache2 and k_d in cache2
            assert cache2[k_a2]["body"] != cache2[k_d]["body"]
            # D: a repo with zero drift entries of its own must not print
            # any *foreign* number, even though the shared cache is full
            root_e = tmp/"repo-e"; _write_digest(root_e)
            slug_map[root_e] = "octo/empty-repo"
            out_e = _reuse_only(root_e)
            for foreign in (3048, 77, 555, 9999):
                assert str(foreign) not in out_e
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

derived: `python3 adversarial_drift_probe.py` (this session's script
above, run from /tmp/pr3084-wt, with the four asserts per case rewritten
as soft checks that print failures instead of raising) -- result:
`ADVERSARIAL PROBE: all cases held (A/B/C/D)`, exit 0.
derived: the same script, adapted to drop the two lines that call
spawn._drift_cache_key (that function does not exist pre-fix), run from
/tmp/main-wt against 573e7382 -- result: `ADVERSARIAL PROBE: FAILURES
FOUND`, exit 1, all four cases (A/B/C/D) failing, e.g.:
```
[A-never-swept-repo] repo C, never swept before, saw other repos' cached numbers on its first sweep: '[watchdog] requirement-drift: ... 후보(...): [77, 3048]\n[watchdog] requirement-drift: 요구 ID 를 전혀 인용하지 않는 열린 이슈/PR [77, 3048]\n'
[C-overlap] flat numeric key '555' collided across repos -- body is 'repo-d body for 555', expected repo-a2's own body (pre-fix has no repo dimension on the key at all)
```
This confirms all four adversarial cases are real discriminators (fail on
main, pass on the PR branch), not vacuous checks that would pass
regardless of the fix. Verdict: Present.

One false lead caught before being reported as a finding: the first cut
of cases A and D asserted total output silence for a repo with no
genuine drift entries, which failed even on the PR's already-fixed code.
derived: `python3 check_empty_state.py` (run from /tmp/main-wt, single-repo
scenario, zero shared cache, `spawn.requirement_drift(root_e,
changed_numbers=set())` where root_e's digest declares R001 "open" and
never cited by anything) -- result: `OUTPUT: '[watchdog] requirement-drift:
요구 R001 — 다이제스트: "something" (source: #1) — 열린 이슈/PR 어디에도
인용되지 않는다.\n'` -- the identical line, with an empty candidate list,
prints on pre-fix main with zero cross-repo state involved at all, so it
is a pre-existing, unrelated signal (watchdog.py's unmentioned_live
branch, which fires whenever a digest requirement is uncited by anything,
independent of the cache) and not part of this issue. The assertion was
narrowed to check only for absence of foreign numbers; re-run, cases A and
D held (see result above).

### Criterion 2 -- "empty state: a repo with no open subjects prints no drift line at all, unchanged"

derived: same check_empty_state.py invocation as directly above (run from
both /tmp/main-wt and, separately, /tmp/pr3084-wt with the identical
single-repo, zero-shared-cache setup) -- result on both worktrees:
byte-identical output, `'[watchdog] requirement-drift: 요구 R001 —
다이제스트: "something" (source: #1) — 열린 이슈/PR 어디에도 인용되지
않는다.\n'`. That pre-existing unmentioned_live-only line is unrelated to
this issue and unchanged pre-fix to post-fix in a no-shared-cache setup --
no regression found or introduced by this fix. Verdict: Present, narrowly
(this criterion's literal "zero open subjects" case was not independently
constructed beyond the above; see the deviation-log analog under "What
did not work" for the case this probe actually distinguishes).

### Criterion 3 -- the leak's mechanism is named

check: `grep -rn 'cross-repo\|foreign repo' docs/issue-3081/reports/[a-z]*.md`
derived: the same grep, run from /tmp/pr3084-wt -- result: 1 match, one
line in the builder's own record about the _load_requirement_drift_cache
legacy-entry filter classifying a cross-repo-mismatch case as Handled.
The mechanism -- attribution lost at report time, not cache location or
sweep resolution -- is stated in that record's "Why" section and matches
the issue's own 4th-comment correction. Present.

### must-not 1 -- cache stays orchestrator-scoped (no root-based re-anchor)

derived: `grep -n "state_paths.orchestrator_state_path" watchdog.py` (run
from /tmp/pr3084-wt) -- result: 2 matches, _requirement_drift_cache_path
and _watchdog_noise_state_path, neither introduces a root-keyed path.
Present.

### must-not 2 -- do not suppress or throttle the requirement-drift signal

derived: `python3 -m pytest tests/test_requirement_drift_repo_scope.py -q
-k includes_own_repo` (run from /tmp/pr3084-wt) -- result: `1 passed` --
this test and this session's own case D above both assert a repo's own
genuine drift entries still print after the fix, so a fix that silenced
everything to close the leak would have failed both. Present.

### must-not 3 -- check whether spawn_on_pr's waiting-for-human list leaks the same way

The issue's 3rd comment states this explicitly as a condition on the fix:
do not scope the fix to requirement-drift alone without checking whether
spawn_on_pr's waiting-for-human list leaks the same way, since both were
observed leaking in the same tick.

derived: `git diff 573e7382 HEAD --stat` (run from /tmp/pr3084-wt) --
result:
```
 docs/issue-3081/reports/.../*.md               | 254 +++++
 docs/issue-3081/reports/.../deviation-log/*.md |   9 +
 docs/specs/enforcement-boundary.md             |   1 +
 gates/probe_drift_repo_leak.py                 | 170 +++++
 spawn.py                                       |   1 +
 tests/test_requirement_drift_repo_scope.py     | 249 +++++
 watchdog.py                                    |  46 ++--
```
gates/spawn_on_pr.py is not in this diff.
derived: `grep -n -i "spawn-on-pr\|waiting-for-human\|park"` against the
builder's own record file (run from /tmp/pr3084-wt) -- result: no match.
The builder's record contains zero mentions of spawn-on-pr,
waiting-for-human, or park state anywhere -- this must-not was not
investigated, not ruled out with evidence, and not acknowledged as
deferred.

This session independently checked whether the leak is real.
parked_report() (backs the `[watchdog] spawn-on-pr: waiting-for-human`
line) is built on load_park_state(root) -> _park_state_path(root), which
-- like the pre-fix requirement_drift_cache.json -- is anchored via
state_paths.orchestrator_state_path and ignores root entirely:

```python
def _park_state_path(root: Path) -> Path:
    """issue #2240: orchestrator cross-tick memory, not target-repo state —
    anchored via state_paths, never `root`. `root` is accepted for
    call-site symmetry with the rest of this module's `root`-scoped
    helpers; it is not used here."""
    return state_paths.orchestrator_state_path(PARK_STATE_FILENAME)


def parked_report(root: Path) -> list[str]:
    return sorted(subject for subject, entry in load_park_state(root).items()
                  if entry.get("parked"))
```
derived: `grep -n "def _park_state_path" -A 6 gates/spawn_on_pr.py` and
`grep -n "def parked_report" -A 3 gates/spawn_on_pr.py` (both run from
/tmp/pr3084-wt, quoted verbatim above, identical to pre-fix main since
this file is untouched by the PR) confirm parked_report applies no repo
filter of any kind.
derived: `grep -n 'f"issue-{issue}/{skill}"' gates/spawn_on_pr.py` (run
from /tmp/pr3084-wt) -- result: 2 matches, lines 1006 and 1088 -- subject
keys carry no repo component, the same shape of gap requirement_drift's
flat str(number) key had before this fix.

derived: ran the following against PR #3084's own branch (from
/tmp/pr3084-wt, `python3 check_spawn_on_pr_leak.py`):
```python
root_a = Path("/tmp/fake-repo-a")
root_b = Path("/tmp/fake-repo-b")
state = spawn_on_pr.load_park_state(root_a)
state["issue-3059"] = {"blocked": True, "pr_number": 1234, "parked": True}
spawn_on_pr._save_park_state(root_a, state)
print("parked_report(root_a):", spawn_on_pr.parked_report(root_a))
print("parked_report(root_b):", spawn_on_pr.parked_report(root_b))
print("_park_state_path(root_a) == _park_state_path(root_b):",
      spawn_on_pr._park_state_path(root_a) == spawn_on_pr._park_state_path(root_b))
```
-- result:
```
parked_report(root_a): ['issue-3059']
parked_report(root_b): ['issue-3059']
_park_state_path(root_a) == _park_state_path(root_b): True
```
A subject parked while sweeping root_a is reported as root_b's own
waiting-for-human item -- the exact shape the issue's live repro
described (issue-3059, an on-the-record issue, printed on
study-companion's board). This reproduces on PR #3084's own delivered
branch, unchanged by the fix.

Verdict on must-not 3: **Absent** -- not merely unfixed but
uninvestigated, contrary to an explicit must-not in the issue.

### Acceptance check 1 as literally specified -- evidence-quality finding

check: `bash -c "python3 watchdog.py --once --repo /home/jwjung/study-companion 2>&1 | grep -c 'issue-30\|30[0-9][0-9]' | grep -qx 0"`

derived: `grep -n -- "--once\|--repo\b" watchdog.py spawn.py` (run from
/tmp/pr3084-wt) -- result: no match. `grep -n "argparse\|def main("
watchdog.py` (same worktree) -- result: no match either -- there is no
main()/argparse entrypoint at all in watchdog.py.
derived: `python3 watchdog.py --once --repo /home/jwjung/study-companion;
echo $?` (run from /tmp/pr3084-wt) -- result: no output, exit 0 -- the
module executes at import time and returns; unrecognized CLI args are
never parsed.
derived: `bash -c "python3 watchdog.py --once --repo
/home/jwjung/study-companion 2>&1 | grep -c 'issue-30\|30[0-9][0-9]' |
grep -qx 0"; echo $?` (run from /tmp/pr3084-wt, PR #3084's fixed code) --
result: exit 0 (passes).
derived: the identical command (run from /tmp/main-wt, the pre-fix parent
573e7382282be24439c223c1603be648dd0e158f, the commit the issue's own
repro was observed on) -- result: exit 0 (also passes).

Acceptance check 1 passes identically on the broken pre-fix commit and
the fixed PR commit, per the two `echo $?` results directly above, because
it never executes a code path that could distinguish them --
`watchdog.py --once --repo ...` runs, produces zero output either way, and
`grep -c ... | grep -qx 0` trivially succeeds on empty input. Verdict:
**Incorrect as an evidence instrument** -- it cannot serve as evidence the
fix works, and, as literally written, could not have caught the original
bug either. The builder's own record documents this as a considered
deviation rather than a silent gap (checked there is no --once CLI
surface, treated the check's glob mismatch as spawning-template
boilerplate) -- this session independently confirms that read of the
codebase is correct, but it does not make the check itself into usable
evidence; the real evidence for criterion 1 is the probe/tests/this
session's adversarial script above, all separately confirmed Present.

### Test depth audit -- the PR's new repo-scope test file

Enumerated via `grep -n "^    def test_"` against
tests/test_requirement_drift_repo_scope.py (run from /tmp/pr3084-wt) --
result: 7 matches:
1. TestFullModeMerges.test_full_mode_merges_other_repos_entries
2. TestDeltaReusePassFiltersByRepo.test_delta_reuse_pass_excludes_other_repo
3. TestDeltaReusePassFiltersByRepo.test_delta_reuse_pass_leak_is_not_one_directional
4. TestDeltaReusePassFiltersByRepo.test_delta_reuse_pass_includes_own_repo
5. TestRetentionRepoScoped.test_retention_when_repo_matches
6. TestRetentionRepoScoped.test_no_retention_when_entry_is_another_repos
7. TestLegacyCacheEntries.test_legacy_entry_without_repo_key_not_retained

Classification below is read directly off each test body quoted earlier
in this record's "Criterion 1"/"must-not 2" sections and off the diff
read under "Upstream basis" (Genuine Assertion / Execution-Only /
Mock-Dominated / Happy-Path-Only / Dead):

- Test 1: GA. Its assertion checks a composite key's presence in the
  cache and the "repo" field on that entry, after a real full-mode sweep
  of a second repo -- a falsifiable, specific check, not merely "ran
  without throwing."
- Test 2: GA. Its assertion checks a foreign number string is absent from
  a second repo's sweep output -- matches the exact assertion shape this
  session's own case A/D checks reproduced failing against main above.
- Test 3: GA, the strongest test in the file -- its assertion checks both
  directions don't leak AND that the two repos' outputs are not
  byte-identical, directly implementing the issue's own 5th-comment
  suggestion that identical output is the tightest available signal that
  no per-repo filter runs at all.
- Test 4: GA -- the deliberate negative-of-the-negative: its assertion
  checks a repo's own entry still surfaces via the reuse pass, guarding
  against a fix that closes tests 2 and 3 above by suppressing all
  output. derived: `python3 -m pytest
  tests/test_requirement_drift_repo_scope.py -q -k includes_own_repo`
  (run from /tmp/pr3084-wt) -- result: `1 passed`.
- Test 5: GA -- regression check that same-repo retention (pre-existing,
  correct behavior) is unchanged.
- Test 6: GA -- the core new behavior: its assertion checks a foreign
  entry's failed lookup is not reported as retained.
- Test 7: GA -- legacy entries dropped, checked both in printed output
  and in the re-saved cache file on disk.

Mocking covers only the external boundary (the gh-backed fetch and
_repo_slug) -- the cache read/write, filtering, and print logic under
test all run for real, so none of the 7 are Mock-Dominated. All 7 carry a
genuine, falsifiable assertion -- 0 Execution-Only, 0 Dead among the 7
enumerated above. Not Happy-Path-Only as a suite: tests 6 and 7 are
explicitly negative/failure-path (foreign lookup failure, legacy
unattributed entry).

derived: 7 GA / 7 total = 100% verification density (see the pytest
result `7 passed` quoted under "Criterion 1" above, matching this
enumeration one-for-one). This is a well-designed regression suite for
the criteria it targets; it does not cover must-not 3 (spawn_on_pr)
because, per the section above, that code path was never touched or
tested by this PR.

### Evidence-quality review of PR #3084's own record

Per defect-verification-reproduction-evidence-quality (rules 5, 7, 11):
most claims in the builder's record carry derived:/canonical: tags with
actual re-runnable commands and quoted output, not paraphrase -- e.g. the
pre-existing-test-failure claim is backed by a pristine-origin/main
re-run, which this session independently re-confirmed rather than
trusting:
derived: `python3 -m pytest tests/test_respawn_deliverable_gate.py
tests/test_spawn_gate_wiring.py -q` (run from /tmp/main-wt) -- result: `5
failed, 35 passed`.
derived: `python3 -m pytest tests/ -q` (run from /tmp/pr3084-wt) --
result: `5 failed, 189 passed` -- matching the failing test names from
the command directly above (test_respawn_deliverable_gate.py's four cases
plus the one hooks.json-wiring case), consistent with the builder's
record and PR description.

The one place evidence quality breaks down is must-not 3: the builder's
record does not merely under-support that claim, it contains no
reference to it at all -- no derived:/canonical: tag, no prose
acknowledging it was considered and deferred. Per rule 11 (judge by
whether the claimed behavior was exercised, not whether code executed),
there is nothing to judge here -- the check was never attempted, so the
builder's own "fixed" verdict rests entirely on the implementer's word for
the one requirement this session independently reproduced as still
broken (see must-not 3 above).

## Why

The task asked specifically for adversarial cases the acceptance checks
do not cover (never-swept repo, pre-existing unattributed entry,
overlapping numbers, zero-entry repo) and for an evidence-quality read of
the PR's own claims. Rather than re-running only the builder's own
probe/tests, this session wrote an independent probe from scratch,
checked it discriminates pre-fix from post-fix on all four cases, and
pursued the issue's own must-not clause about spawn_on_pr -- the one
condition that turned out to be silently unaddressed. Per
defect-verification-independence-from-upstream-verdicts (rule 1: treat a
Present-shaped claim as something to test, not a settled fact; rule 6:
run the reproduction rather than deferring to the record's stated
verdict), the spawn_on_pr finding was pursued to an actual reproduction
rather than left as "the record doesn't mention it."

## Upstream basis

canonical: `gh issue view 3081 --repo tokenmaxxxer/on-the-record
--comments` (7 comments read in full, including the two landed after the
prior verification session: the PR-opened watch notice and the
check-path-glob correction).
canonical: `gh pr view 3084 --repo tokenmaxxxer/on-the-record` and
`gh pr diff 3084` (863-line diff read in full: the builder's new record
file, its deviation-log entry, docs/specs/enforcement-boundary.md,
gates/probe_drift_repo_leak.py, spawn.py,
tests/test_requirement_drift_repo_scope.py, watchdog.py).

watchdog.py, spawn.py, gates/spawn_on_pr.py, plumbing.py at PR #3084's
branch head 4fefe107db388bb2eb8b6439a0274549a8b84f59, and the same files
at the pre-fix parent 573e7382282be24439c223c1603be648dd0e158f -- both
read directly via linked git worktrees (/tmp/pr3084-wt, /tmp/main-wt),
not the PR's rendered diff alone.

## Open findings

1. Unaddressed must-not: gates/spawn_on_pr.py's parked_report() /
   waiting-for-human line leaks across repos via the same
   orchestrator-scoped-with-no-repo-key pattern requirement_drift_cache.json
   had before this fix, reproduced under "must-not 3" above. The issue's
   3rd comment made checking this a condition of the fix; it was not
   checked. Resolution path: a follow-up should apply the same
   repo-attribution pattern (composite key or a repo field per park
   entry, filtered at parked_report()'s read) to park state, then add a
   probe covering spawn_on_pr specifically -- the issue's own acceptance
   section never got a dedicated check for this signal.
2. Acceptance check 1 is not usable evidence: as literally written it
   passes unconditionally (no CLI surface exists to exercise). derived:
   `bash -c "python3 watchdog.py --once --repo /home/jwjung/study-companion
   2>&1 | grep -c 'issue-30\|30[0-9][0-9]' | grep -qx 0"; echo $?` run
   from both /tmp/pr3084-wt and /tmp/main-wt -- result: exit 0 on both
   (repeated from "Acceptance check 1 as literally specified" above). Not
   this PR's defect to fix, but worth flagging to whoever closes the
   issue so criterion 1's real evidence (the probe/tests/this session's
   adversarial script, all Present) is what's cited, not the literal
   check line.

## Next steps

None from this session -- loop_state: landed. Both open findings above are
handoffs, not further work planned by this record.

## What did not work

Two false leads, both caught before being reported as findings:
- First cut of adversarial cases A/D asserted total output silence for a
  repo with no genuine drift entries; this over-fired on a pre-existing,
  unrelated uncited-digest-requirement line that prints regardless of
  cross-repo state, per the check_empty_state.py result quoted under
  "Criterion 1" and re-confirmed under "Criterion 2" above. Narrowed the
  assertion to check only for foreign numbers; re-ran and the cases held.
- Considered whether docs/specs/reconciled-index.md needed regeneration
  since PR #3084 touched docs/specs/enforcement-boundary.md.
  derived: `grep -n "enforcement-boundary.md" docs/specs/reconciled-index.md`
  (run against this session's own working tree) -- result: no match --
  enforcement-boundary.md is not one of the documents that index tracks,
  so no regeneration was owed; not pursued further as a finding.

skill-verdict: adversarial-review — applied: invoked; ran this
verification of PR #3084 blind to the builder's session (never received
the builder's prompt/reasoning, only gh reads of the issue and PR), and
reached an independent verdict by executing code rather than reading the
builder's claims as settled.
skill-verdict: test-depth-audit — applied: invoked; classified every test
in the PR's repo-scope test file per the "Test depth audit" section above
(derived: 7 GA / 7 total = 100%, same section).
skill-verdict: defect-verification-reproduction-evidence-quality —
applied: invoked; every claim above carries a derived:/canonical: tag with
the actual command and quoted output (rule 5), the pre-fix/post-fix
environment for each is stated (rule 7), and the spawn_on_pr finding
attaches evidence to each step of the causal chain (_park_state_path's
root-ignoring anchor, then parked_report's missing filter) rather than
one end-state pointer (rule 12).
skill-verdict: defect-verification-independence-from-upstream-verdicts —
applied: invoked; devised the four adversarial cases independently of
what PR #3084's own probe/tests already covered (rule 2: deliberately
included edge/negative cases -- never-swept repo, legacy entry, numeric
overlap, empty repo), and pursued the issue's own must-not clause to an
actual reproduction rather than accepting the builder record's verdict at
face value (rule 1, rule 6).
skill-verdict: work-in-english — applied: invoked; this record, all
commands, and all code are in English.
other mounted skills (conformance-review-finding-record,
implementation-audit, verify-finding-record): not triggered -- this
record's target file is this session's own role record, not a
conformance-review or defect-verification record file, which those
skills' triggers name specifically.
