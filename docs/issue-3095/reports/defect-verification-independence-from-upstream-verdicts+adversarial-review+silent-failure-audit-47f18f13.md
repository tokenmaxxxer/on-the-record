---
issue: 3095
role: defect-verification-independence-from-upstream-verdicts+adversarial-review+silent-failure-audit-47f18f13
author: defect-verification-independence-from-upstream-verdicts+adversarial-review+silent-failure-audit-47f18f13
skills: defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true  # independent, builder-blind verification of PR #3106's own deliverable against issue #3095
code_under_review: e06909962b58130aa889b8c15561ade355bf89f3
type: defect-verification-record
breaking: false
verdict: All 3 acceptance checks and both must-nots are Present, independently
  re-derived with a sensitivity control and mutation tests. One new
  adversarial finding beyond the issue's acceptance scope, in "Open
  findings" below.
loop_state: landed
upstream:
  - path: PR #3106 (github.com/tokenmaxxxer/on-the-record/pull/3106), head
      commit e0690996 -- not merged to main, untracked in this repo's own
      checkout; fetched read-only this session as local ref
      pr-3106-review and checked out into two disposable worktrees, since
      removed
    sha: e06909962b58130aa889b8c15561ade355bf89f3
  - path: main (baseline for the sensitivity control and full-suite
      comparison)
    sha: 7ee166122719b8b4f3bcde72d9a5c73885aaceee
---

# issue-3095 — defect-verification-independence-from-upstream-verdicts+adversarial-review+silent-failure-audit-47f18f13 record

## What was done

Independent, builder-blind verification of PR #3106 against issue #3095.

canonical: `gh issue view 3095` output, read this session — title
"spawn-on-pr's parked-subject list leaks across repos the same way
requirement-drift did", targets R007, three `check:` acceptance lines,
two must-nots (no suppression/rate-limit of the waiting-for-human line;
no vacuous CLI-flag check, sensitivity control required).

canonical: `gh pr view 3106` output, read this session — state OPEN,
+699/-6, "Closes #3095".

derived: `git merge-base pr-3106-review origin/main` — result:
`7ee166122719b8b4f3bcde72d9a5c73885aaceee`, equal to `origin/main` HEAD
at the start of this session — PR #3106's base is current main, not
stale.

Fetched PR #3106 read-only (`git fetch origin pull/3106/head:pr-3106-review`)
and worked from two disposable git worktrees, `/tmp/verify-pr3106-branch`
(PR head, commit `e0690996`) and `/tmp/verify-pr3106-main` (`origin/main`,
commit `7ee16612`). Both worktrees were removed (`git worktree remove
--force`) before this record was written — every `gates/probe_parked_report_repo_leak.py`
(untracked) and `tests/test_spawn_on_pr_repo_scope.py` (untracked)
reference below existed only inside those now-removed worktrees. No
merge, no edit to PR #3106's branch.

### 1. Diff shape

canonical: `git diff origin/main...pr-3106-review -- gates/spawn_on_pr.py`
output, full diff read this session. `parked_report()` gained one line —
`repo_slug = spawn._repo_slug(root)` and an `and entry.get("repo") ==
repo_slug` filter clause. `spawn_missing_for_pr()` computes `repo_slug`
once per tick, evicts a `prior` whose `repo` doesn't match
(`if prior is not None and prior.get("repo") != repo_slug: prior = None`),
and tags all four park-state write sites (recheck-skip, should_park,
ceiling-hit, spawned) with `"repo": repo_slug`.

derived: `git diff origin/main...pr-3106-review -- gates/spawn_on_pr.py |
grep -n "_park_state_path"` — result: no match — `_park_state_path` is
untouched by this diff, still routed through
`state_paths.orchestrator_state_path` — must-not "cache stays
orchestrator-scoped" (issue #2240) holds.

### 2. Acceptance check 1 — `python3 -m pytest tests/test_spawn_on_pr_repo_scope.py -q` (untracked)

derived: ran inside `/tmp/verify-pr3106-branch` (commit `e0690996`) —
result:
```
......                                                                   [100%]
6 passed in 1.26s
```
**Present.** 6 tests, decision-table shaped (own-repo retention,
cross-repo eviction, parked_report inclusion/exclusion, non-identical
reports across repos, legacy no-`repo`-key entry excluded).

### 3. Acceptance check 2 — `python3 gates/probe_parked_report_repo_leak.py` (untracked), with sensitivity control

derived: ran inside `/tmp/verify-pr3106-branch` — result:
```
[spawn-on-pr] park=1건 waiting-for-human (승인-대기 상태 변화 없음): ['issue-3059']
ok
```
exit 0.

Sensitivity control (issue's must-not 2 — a probe that only ever runs on
the fixed branch establishes nothing, the same failure shape as issue
#3081's first acceptance check, which called a CLI flag that never
existed). Copied this session's unmodified `gates/probe_parked_report_repo_leak.py`
(untracked, fetched from the PR branch) into `/tmp/verify-pr3106-main`
(`origin/main` at `7ee16612`, unmodified) and ran the identical file
there:

derived: `python3 gates/probe_parked_report_repo_leak.py` (untracked)
inside `/tmp/verify-pr3106-main` — result:
```
FAIL: parked_report(root_a) and parked_report(root_b) are identical (['issue-3059']) -- no per-repo filter is running at all (issue #3095).
```
exit 1. Same unmodified probe file: fails on `main`, passes on the PR
branch. **Present**, with a real sensitivity control, not vacuous.

### 4. Acceptance check 3 — `python3 -m pytest tests/ -q`

derived: ran inside `/tmp/verify-pr3106-branch` — result:
```
222 passed, 2 warnings in 10.54s
```
derived: ran the identical command inside `/tmp/verify-pr3106-main`
(`origin/main` at `7ee16612`, probe file removed first) — result:
```
216 passed, 2 warnings in 9.44s
```
derived: `222 - 216 = 6` — matches the PR's own added test file's
collected-test count exactly (acceptance check 1, step 2 above). 0
regressions, 0 failures on either branch. **Present.**

Note on the PR's own body: PR #3106's "Test plan" claims "195 passed, 5
pre-existing failures unrelated to this change" for this same check.
canonical: `gh pr view 3106 --json body` output, read this session,
"Test plan" section.

derived: `git show pr-3106-review:docs/issue-3095/reports/implementation-blueprint+silent-failure-audit+test-derivation-0cae2f1d.md`
(untracked) — result: that record measured against `origin/main` at
`ed45102b`, an ancestor of `7ee16612` — checked: `git merge-base --is-ancestor ed45102b13a755bc27dc342dd471f578a8e8e083 7ee166122719b8b4f3bcde72d9a5c73885aaceee`
— exit 0 (true, confirmed ancestor).

derived: `git log --oneline ed45102b13a755bc27dc342dd471f578a8e8e083..7ee166122719b8b4f3bcde72d9a5c73885aaceee`
— result includes `7ee16612 issue-3083: fix hooks.json additive guard and
respawn-gate debounce test gap (#3089)` — the commit that landed between
the PR body's measurement point and the PR's actual current base, and
whose title matches the 5 failing test names the PR body lists
(`test_respawn_deliverable_gate.py` x4, `test_spawn_gate_wiring.py` x1).
This is stale PR-description text left over from a rebase, not a
functional defect in the fix — the current, freshly-run result (222
passed, 0 failed, per the derived: run above) is strictly better than
either the PR body or the issue's acceptance line requires. Noted for a
human reviewer's benefit, not scored as a criterion failure.

### 5. Must-not 1 — waiting-for-human line not suppressed or rate-limited

derived: `git diff origin/main...pr-3106-review -- gates/spawn_on_pr.py |
grep -n "parked_now\|print(f\"\[spawn-on-pr\] park="` — result: two
hits, both `parked_now.append(subject)` context lines inside the
existing `if`/`elif` branches, neither a `+`/`-` diff line — the
`print(f"[spawn-on-pr] park={len(parked_now)}건 ...")` block itself is
untouched by this PR's diff. **Present** — the fix changes which
subjects populate `parked_now` (repo-scoped now), not whether or how
often the line prints once populated.

### 6. Must-not 2 — no vacuous check via a nonexistent CLI flag

Covered by step 3's sensitivity control above: the probe calls
`spawn_on_pr.spawn_missing_for_pr`/`parked_report` directly (the real
entrypoints `watchdog.py`'s board-sweep calls every tick — checked:
`grep -n "spawn_missing_for_pr\|parked_report" watchdog.py`, run inside
`/tmp/verify-pr3106-branch` — result: 2 matches, both real call sites),
not a shell-invoked CLI flag. **Present.**

### 7. Mutation tests — confirming the fix has real discriminating power

Both mutations applied to and reverted from `gates/spawn_on_pr.py`
inside `/tmp/verify-pr3106-branch`; restored state confirmed via
`git status --short gates/spawn_on_pr.py` — result: empty output (clean).

**Report-time filter.** Removed the `and entry.get("repo") == repo_slug`
clause from `parked_report()`, restoring the old
return-every-parked-entry shape.

derived: `python3 gates/probe_parked_report_repo_leak.py` (untracked)
against that mutation — result:
```
FAIL: parked_report(root_a) and parked_report(root_b) are identical (['issue-3059']) -- no per-repo filter is running at all (issue #3095).
```
exit 1. Restored, re-ran clean — `ok`, exit 0, same as step 3.

**Eviction guard.** Replaced `if prior is not None and prior.get("repo")
!= repo_slug: prior = None` with a no-op (`pass`).

derived: `python3 -m pytest tests/test_spawn_on_pr_repo_scope.py -k
"no_retention_when_entry_is_another_repos" -q` (untracked) against that
mutation — result:
```
FAILED tests/test_spawn_on_pr_repo_scope.py::TestRetentionRepoScoped::test_no_retention_when_entry_is_another_repos
AssertionError: repo A inherited repo B's park/attempts history for the same-named subject 'issue-3059' instead of evicting it as a foreign-repo entry (issue #3095 retention split).
1 failed in 1.35s
```
Restored, re-ran the full acceptance-check-1 suite clean — `6 passed`,
same as step 2. Both mutations demonstrate real discriminating power:
derived by direct observation of pass→fail→pass across the mutate/
restore cycle above, not asserted from reading the diff alone.

### 8. Independent adversarial probes beyond the acceptance checks

Wrote a fresh probe script from scratch (not copied from
`gates/probe_parked_report_repo_leak.py` (untracked) or
`tests/test_spawn_on_pr_repo_scope.py` (untracked)), driving
`spawn_on_pr.spawn_missing_for_pr`/`parked_report` against
`/tmp/verify-pr3106-branch`'s code with three repos (`acme/repo-a`,
`acme/repo-b`, `acme/repo-never-swept`) and gh/git/spawn boundaries
mocked, same idiom the PR's own tests use.

**A repo the orchestrator has never swept.** Seeded park state with only
repo A's entry, called `parked_report()` on a third root whose slug never
appears in the file.

derived: ran the probe script this session — result: `check1
(never-swept repo reports nothing): OK` (`parked_report(root_never) ==
[]`). A repo with zero parked subjects prints nothing, not someone
else's list.

**A pre-existing entry with no `repo` field (legacy polluted park
state).** Seeded `{"issue-77": {"blocked": True, "parked": True,
"attempts": 3}}` — no `repo` key, the pre-fix shape. Checked both
`parked_report()` (report-time) and `spawn_missing_for_pr()`
(retention-time, dry-run) against a resolvable repo.

derived: ran the probe script this session — result: `check2 (legacy
entry excluded + evicted, not inherited): OK` — `"issue-77" not in
parked_report(root_a)`, and the legacy entry was evicted (the subject
re-spawned rather than staying parked on 3 stale attempts). This
independently reproduces, rather than merely cites, what the
implementer's own record describes:

derived: `git show pr-3106-review:docs/issue-3095/reports/implementation-blueprint+silent-failure-audit+test-derivation-0cae2f1d.md`
(untracked), "Why" section — the implementer chose to keep legacy
entries at load time (unlike PR #3084's `_drift_cache_key` re-keying,
for compatibility with `gates/test_spawn_on_pr.py`'s bare-subject-key
fixtures) and rely on `entry.get("repo") == repo_slug` never matching
`None` against a real slug. The probe run above confirms that filter and
the retention-eviction guard both actually produce that effect in
running code, not just in the stated design intent.

**Two repos with overlapping issue numbers (write-path collision) — new
finding, not covered by the issue's acceptance checks.** Seeded
`{"issue-100": {..., "repo": "acme/repo-a"}}`, confirmed
`parked_report(root_a) == ["issue-100"]`, then ran a real
`spawn_missing_for_pr(root_b, ...)` tick for repo B's own,
entirely-unrelated "issue-100" (blocked, so it should park under repo
B's own attribution).

derived: ran the probe script this session — result:
```
after repo B's tick on same-numbered subject: out_a=[] out_b=[]
FAIL: repo A's own park entry for issue-100 was lost after repo B's unrelated tick: []
```
Repo B's tick, spawning fresh for its own "issue-100" (correctly evicting
repo A's foreign entry as its own `prior`, per step 7's mutation-tested
eviction guard), writes `park_state["issue-100"] = {..., "repo":
"acme/repo-b", "parked": False}` into the one shared JSON file
(`_park_state_path`, confirmed orchestrator-scoped in step 1) using the
bare subject string as the key. Because the fix keeps the pre-existing
bare-subject key and only adds a `repo` field to the *value* (per the
implementer's own "Why" section, cited above), repo B's write silently
overwrites the dict entry at key `"issue-100"` in full, including repo
A's untouched, unrelated, still-genuinely-parked entry —
`parked_report(root_a)` afterward returns `[]`, not `["issue-100"]`, as
shown in the derived run above.

derived: `grep -c "spawn_missing_for_pr" tests/test_spawn_on_pr_repo_scope.py`
(untracked), run inside `/tmp/verify-pr3106-branch` before the worktree
was removed — result: 4 (all 4 within `TestRetentionRepoScoped`, none
constructing a second root's real tick against the same subject string) —
confirms this collision path is not exercised by any test in that file.

See "Open findings" below for this session's assessment of severity and
recommended resolution path.

### 9. Silent-failure audit

derived: `git diff origin/main...pr-3106-review -- gates/spawn_on_pr.py |
grep -n "except\|try:"` — result: no match. The only error-handling path
in the functions this PR touches — `load_park_state()`'s `try:
return json.loads(p.read_text()) except (OSError, ValueError): return
{}` — predates the PR and is not part of its diff.

canonical: `gates/spawn_on_pr.py`, `load_park_state`'s own docstring,
read inside `/tmp/verify-pr3106-branch` — "빈 사전은 park 후보 없음과
같은 뜻이라 이 함수 하나만으로 fail-safe 하다" ("an empty dict means no
park candidates, so this function alone is fail-safe") — states the
silent-absorb-to-empty-dict behavior is pre-existing and intentional, not
new error handling introduced by PR #3106. **Not-applicable in scope**:
this PR adds no new try/except/error-handling path; it adds attribution
tagging and a read-time filter over an already-audited, unchanged
failure path — established by the `grep` above, not cited from the
implementer's own equivalent claim in their record.

## Why

canonical: this record's own "What was done" section above (steps 1-9,
all run this session in `/tmp/verify-pr3106-branch` and
`/tmp/verify-pr3106-main` before this section was written) is the basis
for the rationale below.

Followed the assignment's explicit structure: re-run the PR's own claims
from primary evidence rather than cite them (per this skill's rule on
re-deriving from primary evidence over trusting a prior verdict), build
a sensitivity control rather than trust a single-branch pass (must-not
2, itself born from issue #3081's vacuous-CLI-flag incident — canonical:
`gh issue view 3081` body, read this session, cited in the assignment
prompt), then go beyond the stated acceptance with self-devised
adversarial inputs — the four scenarios the assignment named (never-swept
repo, legacy entry, numeric collision, empty-report repo — step 8 above)
plus mutation tests (step 7 above) to check the fix's guards are
load-bearing, matching the rigor the prior issue-3081/PR-3084
verification session used as precedent — canonical:
`docs/issue-3081/reports/defect-verification-independence-from-upstream-verdicts+adversarial-review+silent-failure-audit-98169d33.md`,
read this session.

`adversarial-review`'s literal Step 1-2 (spawn a separate sub-session
blind to the spec, feed it the artifact only) was not run: grading the
issue's three specific acceptance checks and two must-nots requires
holding the spec throughout, which the strict blind-artifact protocol
excludes by design. Applied in spirit instead — this session is
structurally independent of PR #3106's builder session (fresh context, no
shared reasoning chain to defend), and did not accept the PR's own
probe/test results or its record's claims at face value: every claim
graded in "What was done" above was re-run from primary evidence in a
disposable worktree, and the write-collision finding (step 8, derived:
the three-repo probe script run this session, output quoted there) was
produced by writing and running new adversarial code, not by reading the
PR's own disclosure and agreeing with it.

## What did not work

None — every planned check ran to completion; no reproduce attempt was
abandoned or reverted.

## Upstream basis

PR #3106 (github.com/tokenmaxxxer/on-the-record/pull/3106), head commit
`e06909962b58130aa889b8c15561ade355bf89f3` — `gates/spawn_on_pr.py`
(`_park_state_path`, `load_park_state`, `parked_report`,
`spawn_missing_for_pr`), `gates/probe_parked_report_repo_leak.py`
(untracked), `tests/test_spawn_on_pr_repo_scope.py` (untracked),
`docs/specs/enforcement-boundary.md` (this record's `code_under_review:`).

main (github.com/tokenmaxxxer/on-the-record), commit
`7ee166122719b8b4f3bcde72d9a5c73885aaceee` — sensitivity-control and
full-suite baseline, and PR #3106's own actual merge-base (derived: `git
merge-base pr-3106-review origin/main`, cited in "What was done" above).

PR #3084 / issue #3081 — canonical: `gh pr view 3084 --json
state,mergeCommit,mergedAt` output, read this session — result:
`{"mergeCommit":{"oid":"e5172b24565e990f974292614df951410d729ceb"},
"mergedAt":"2026-09-02T07:17:25Z","state":"MERGED"}`. The mechanism PR
#3106 reuses (`watchdog._drift_cache_key`); this record's step 8
write-collision finding is the same collision class `_drift_cache_key`'s
own re-keying was designed to close, per PR #3106's own record's
disclosure (cited in step 8 above).

## Open findings

1. **Write-path collision across two repos sharing a subject name.**
   derived: the adversarial probe script run this session inside
   `/tmp/verify-pr3106-branch`, output quoted in step 8 above — confirmed
   real: repo A's own genuine, unrelated parked entry for "issue-100" was
   silently lost after repo B's own unrelated tick for its own
   "issue-100". Disclosed by the implementer as an accepted boundary
   outside this issue's three acceptance checks (derived: `git show
   pr-3106-review:docs/issue-3095/reports/implementation-blueprint+silent-failure-audit+test-derivation-0cae2f1d.md`
   (untracked), cited in step 8 above); this session's independent
   reproduction found it more severe than the record's own description
   ("overwrite... not just misread") — the reproduction above is a full
   loss of the victim repo's own entry, not a misattribution. Resolution
   path: a follow-up issue scoped to re-keying park-state entries as
   `f"{repo}:{subject}"` (matching `_drift_cache_key`), which requires
   updating `gates/test_spawn_on_pr.py`'s bare-subject-key fixtures —
   derived: `grep -c "KEY = SUBJECT" gates/test_spawn_on_pr.py`, run
   inside `/tmp/verify-pr3106-branch` — result: 1 (confirms the
   compatibility constraint the implementer's own record names). Not
   attempted by this session — out of this session's own scope
   (verification only, no edits to PR #3106 or its target files, per the
   assignment).

2. **PR #3106's own body ("Test plan" section) carries a stale test
   count.** derived: `python3 -m pytest tests/ -q` inside
   `/tmp/verify-pr3106-main` (`origin/main` at `7ee16612`) — result: 216
   passed, 0 failed (quoted in step 4 above), which does not match the PR
   body's "195 passed, 5 pre-existing failures" claim — canonical: `gh pr
   view 3106 --json body` output, "Test plan" section, read this session
   (cited in step 4 above). Root cause: the PR was rebased onto a newer
   main (which merged PR #3089, fixing those 5 failures) after the PR
   description was written — derived: `git log --oneline
   ed45102b13a755bc27dc342dd471f578a8e8e083..7ee166122719b8b4f3bcde72d9a5c73885aaceee`,
   cited in step 4 above. Not a functional defect — the current result is
   strictly better than claimed. Resolution path: none required for this
   issue's acceptance; noted so a human reviewer isn't confused by the
   mismatch between the PR body and a fresh `pytest tests/ -q` run.

## Next steps

None — `loop_state: landed`. All three of issue #3095's acceptance checks
and both must-nots are independently verified **Present** (steps 2-6
above). Open finding 1 above is recommended as a follow-up issue but does
not block this session's verdict on issue #3095's own stated acceptance
criteria, which PR #3106 satisfies.

skill-verdict: defect-verification-independence-from-upstream-verdicts —
applied: invoked; re-derived all three acceptance checks and both
must-nots from primary evidence in disposable worktrees rather than
citing PR #3106's own claims (steps 2-6), built the required sensitivity
control (step 3), added mutation tests beyond what either issue asked
for (step 7), and devised four independent adversarial probes beyond the
stated acceptance scope (step 8), one of which surfaced a new finding
(Open finding 1).
skill-verdict: adversarial-review — applied: invoked; ran as a
structurally independent session with no shared reasoning chain with PR
#3106's builder, re-running rather than trusting every claim in the PR's
own record (steps 2-4, 8-9) and re-deriving the step 8 finding from
scratch rather than only checking the implementer's own disclosure;
literal Step 1-2 (spawn a separate blind-to-spec sub-session) was not
run because grading the issue's named acceptance checks requires holding
the spec (see "Why" above).
skill-verdict: silent-failure-audit — applied: invoked; step 9 above
(`grep -n "except\|try:"` over this PR's own diff — result: no match)
establishes this PR introduces no new error-handling path, and that the
one pre-existing try/except in the functions it touches is unchanged,
documented-intentional fail-safe behavior.
