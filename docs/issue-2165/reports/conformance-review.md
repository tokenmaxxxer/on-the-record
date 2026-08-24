---
issue: 2165
role: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2165/proposals/2026-08-24-conformance-review-plan.md
    sha: same-commit
  - path: docs/issue-2165/reports/conformance-review/survey.md
    sha: same-commit
  - path: gates/spawn_on_pr.py
    sha: 1f9601df63f7c4df4431fe67115071ef1c05890a
subject: PR #2170 (issue-2165/implementation, MERGED into main)
canonical: gh pr view 2170 --json mergeCommit,mergedAt — result: {"mergeCommit":{"oid":"1f9601df63f7c4df4431fe67115071ef1c05890a"},"mergedAt":"2026-08-24T09:49:12Z"}
test: python3 -m pytest tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py -q
result: cantTell
assertedBy: conformance-review (issue-2165 session)
---

# issue-2165 — conformance-review record

## What was done

Rendered a verdict for each of R1-R9 (extracted in
`docs/issue-2165/reports/conformance-review/survey.md`) against PR #2170's
delivered fix.

Before this session's merge, this branch's tip commit predated PR #2170's diff.
canonical: git log --oneline -1 c79728ce -- gates/spawn_on_pr.py (this session) — result: `3ca748c4 issue-1745 phase 2 continuation ... (#1977)`, a pre-issue-2165 commit.

It was merged forward from `origin/main` in this session so the merged implementation's actual files are present in this worktree for inspection.
canonical: derived: git merge origin/main --no-edit (this session) — result: clean merge, `gates/spawn_on_pr.py` and `tests/test_spawn_on_pr*.py` brought in without conflict; only `.orchestrate-hook-fires.log` (an append-only hook log, unrelated to this review's subject) conflicted, resolved by union of both sides' lines.

### R1 — close the merged-subject skip gap (Fix bullet 1)

- spec_ref: Fix bullet 1
- verdict: Present
- evidence: `gates/spawn_on_pr.py:185-196`
canonical: Read gates/spawn_on_pr.py:160-299 (this session)
```
    merged_seen: set[str] | None = None
    for subject, subject_board in b.items():
        missing = applicable_roles(subject_board)
        if not missing:
            continue
        if merged_seen is None:
            merged_seen = load_merged_seen(root)
        if subject in merged_seen:
            # issue #2165: 이미 이전 틱에서 MERGED 로 확인됐다 — merge
            # 는 종결적 사실이라 이후 틱의 (혹은 fail-open 하는) 재확인을
            # 기다리지 않고 바로 건너뛴다.
            continue
```
  and `gates/spawn_on_pr.py:204-214`:
canonical: Read gates/spawn_on_pr.py:160-299 (this session)
```
        pr_state = _pr_state_for_branch(root, branch, pr_index)
        if pr_state == "MERGED":
            merged_seen.add(subject)
            _save_merged_seen(root, merged_seen)
            spawn.ledger_write({
                "event": "spawn_on_pr_skip_merged",
                "subject": subject, "missing": missing,
            })
            print(f"[spawn-on-pr] {subject}: subject PR 이 이미 merged — "
                  f"옵저버 스폰 건너뜀 (missing={missing})")
            continue
```
- rationale: the sticky cache short-circuits before `_pr_state_for_branch`
  can be asked again, closing the gap the survey traced.
canonical: docs/issue-2165/reports/conformance-review/survey.md
(`## Gap candidate for phase-2 (R5)` context; `## What PR #2170 adds`
cites the same hunk)
  The pre-existing `spawn_on_pr_skip_merged` ledger/print branch other
  subjects already hit correctly is unchanged, only reused — this is the
  "same skip logic" Fix bullet 1 asks for, not a new parallel path.
canonical: Read gates/spawn_on_pr.py:160-299 (this session, quoted block above)

### R2 — regression test reproducing #513's shape (Fix bullet 2)

- spec_ref: Fix bullet 2
- verdict: Present
- evidence: `tests/test_spawn_on_pr.py:358-391`
  (`test_spawn_missing_for_pr_sticky_merged_cache_zero_spawns_across_ticks`)
canonical: Read tests/test_spawn_on_pr.py:299-393 (this session)
```
def test_spawn_missing_for_pr_sticky_merged_cache_zero_spawns_across_ticks(
        fixture_repo, monkeypatch):
    """end-to-end companion driving the actual watchdog entrypoint
    (`spawn_missing_for_pr`) across a confirmed-merge tick followed by
    several flaky-reconfirm ticks -- reproduces #2165's reported #513
    shape (50+ respawns after merge) and asserts zero spawns throughout."""
    monkeypatch.setattr(
        spawn_on_pr.spawn, "_pr_open_or_merged_for_branch",
        lambda root, branch: 42 if branch == "issue-9001/implementation" else None)
    monkeypatch.setattr(
        spawn_on_pr.spawn, "_merged_pr_for_branch",
        lambda root, branch: 42 if branch == "issue-9001/implementation" else None)

    spawned = []
    monkeypatch.setattr(spawn_on_pr.spawn, "roster_register", lambda key, entry: None)
    monkeypatch.setattr(spawn_on_pr.spawn, "_spawn_one",
                         lambda *a, **k: spawned.append((a, k)))

    # Tick 1: merged, confirmed -> zero pairs, zero spawns.
    pairs1 = spawn_on_pr.spawn_missing_for_pr(
        fixture_repo, str(fixture_repo), dry_run=False, issue_states={9001: "OPEN"})
    assert pairs1 == []
    assert spawned == []

    # Ticks 2-11: merged-check flakes back to "not merged" on every tick --
    # pre-fix this reproduced the reported shape (respawn every flaky
    # tick); must stay at zero now.
    monkeypatch.setattr(
        spawn_on_pr.spawn, "_merged_pr_for_branch", lambda root, branch: None)
    for _ in range(10):
        pairs = spawn_on_pr.spawn_missing_for_pr(
            fixture_repo, str(fixture_repo), dry_run=False, issue_states={9001: "OPEN"})
        assert pairs == []
    assert spawned == []
```
canonical: python3 -m pytest tests/test_spawn_on_pr.py::test_spawn_missing_for_pr_sticky_merged_cache_zero_spawns_across_ticks -q — result: 1 passed in 1.02s (this session, independently re-run — this test's own body, quoted above, asserts `pairs == []` and `spawned == []` on every one of the 11 ticks)
- rationale: Fix bullet 2's action is conditioned on the defect being
  issue/subject-specific rather than generic `gh` flakiness.
canonical: docs/issue-2165/reports/conformance-review/survey.md
(`## Requirement extraction`, R2: "conditioned on: the underlying defect
being issue/subject-specific ... rather than a generic flakiness issue")
  The `_pr_state_for_branch` docstring documents the actual failure mode
  as a generic fail-open on any later-tick `gh` re-check, not a
  #513-specific naming or race condition:
canonical: Read gates/spawn_on_pr.py:99-117 (this session)
```
    번째 조회가 실패하면(예: 테스트 환경에 `gh` 없음) OPEN 으로 fail-open
    한다: 이 함수의 목적은 merged 를 놓치지 않는 게 아니라 merged 를
    확신할 때만 스폰을 건너뛰는 것이다(#1360 의 issue-closed fail-closed
    와는 반대 방향 — 여기서 놓치면 그냥 오늘과 같은 스폰이지, 검증 부채가
    영영 안 도는 게 아니다)."""
```
  so the named condition does not literally hold, yet the action was
  taken anyway (the test quoted above exists and independently re-runs
  clean, cited immediately above).

### R3 — a merged subject triggers no further spawns (Acceptance bullet 1, functional clause)

- spec_ref: Acceptance bullet 1 (functional clause)
- verdict: Present
- evidence: `gates/spawn_on_pr.py:190-196` (short-circuit, quoted under R1).
canonical: python3 -m pytest tests/test_spawn_on_pr.py::test_spawn_missing_for_pr_sticky_merged_cache_zero_spawns_across_ticks -q — result: 1 passed in 1.02s (this session)
  Plus `tests/test_spawn_on_pr.py:376-391` (quoted in full under R2).
canonical: python3 -m pytest tests/test_spawn_on_pr.py::test_spawn_missing_for_pr_sticky_merged_cache_zero_spawns_across_ticks -q — result: 1 passed in 1.02s (this session, re-cited)
- rationale: code path traced to the short-circuit, and the test cited
  above confirms zero spawns across repeated ticks including the
  flaky-reconfirm case that reproduced the reported #513 pattern
  pre-fix.
canonical: python3 -m pytest tests/test_spawn_on_pr.py::test_spawn_missing_for_pr_sticky_merged_cache_zero_spawns_across_ticks -q — result: 1 passed in 1.02s (this session, re-cited)

### R4 — coverage in `tests/test_spawn_on_pr.py` (Acceptance bullet 1, file clause a)

- spec_ref: Acceptance bullet 1 (file clause a)
- verdict: Present
- evidence: `tests/test_spawn_on_pr.py:319-391` — two new test functions,
  `test_missing_verification_sticky_merged_cache_survives_flaky_reconfirm`
  (line 319) and
  `test_spawn_missing_for_pr_sticky_merged_cache_zero_spawns_across_ticks`
  (line 358, quoted in full under R2).
canonical: grep -n "^def test_" tests/test_spawn_on_pr.py — result
includes `319:def test_missing_verification_sticky_merged_cache_survives_flaky_reconfirm(`
and `358:def test_spawn_missing_for_pr_sticky_merged_cache_zero_spawns_across_ticks(`
(this session)
- rationale: both land in exactly the file this clause names.
canonical: python3 -m pytest tests/test_spawn_on_pr.py -q — result: 21 passed in this session (subset of the 28-passed combined run in the Verification section below)

### R5 — coverage in `tests/test_spawn_on_pr_park.py` simulating the #513 shape (Acceptance bullet 1, file clause b)

- spec_ref: Acceptance bullet 1 (file clause b, parenthetical)
- verdict: Surface
- evidence: no #513/merged-cache reference exists in
  `tests/test_spawn_on_pr_park.py`.
canonical: grep -n "513\|merged_seen\|MERGED_SEEN" tests/test_spawn_on_pr_park.py — result: (no output — zero matches) (this session)
  The file's own module docstring scopes it to a distinct, pre-existing
  feature (issue-1476's park mechanism):
canonical: Read tests/test_spawn_on_pr_park.py:1-7 (this session)
```
#!/usr/bin/env python3
"""issue-1476 Acceptance — spawn-on-pr respawn gate parks a verification
role whose only blocker is an unchanged awaiting-human-APPROVE state,
keyed off a structured signal (never prose matching).

  python3 -m pytest tests/test_spawn_on_pr_park.py
"""
```
  Contrast: the actual #513-shape scenario lives in
  `tests/test_spawn_on_pr.py:358-391` (quoted in full under R2), not
  here.
- rationale: this clause is satisfied only at the level of "both named
  files run together and both stay green".
canonical: python3 -m pytest tests/test_spawn_on_pr_park.py -q — result: 7 passed in this session (subset of the 28-passed combined run in the Verification section below)
  `test_spawn_on_pr_park.py`'s own 7 pre-existing tests are included,
  unmodified, in the same combined `pytest` invocation the Verification
  section re-runs.
canonical: python3 -m pytest tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py -q — result: 28 passed in 7.05s (this session; see Verification section)
  But the parenthetical's substance — a scenario *simulating the #513
  shape* — is not present inside `tests/test_spawn_on_pr_park.py` itself.
canonical: grep -n "513\|merged_seen\|MERGED_SEEN" tests/test_spawn_on_pr_park.py — result: (no output — zero matches) (this session, re-cited)
  Whether the issue's file-pairing names a verification-command scope
  (both files run) or a code-location requirement (the scenario itself
  belongs in the park file) cannot be resolved from the issue text
  alone. Per verdict-assignment rule 1, this renders Surface rather than
  a hard Absent: matching shape exists (the named file is part of the
  green verification run cited above), but the specific sub-clause
  content it also names is not located inside that file.

### R6 — executed acceptance evidence in this record (Acceptance bullet 2)

- spec_ref: Acceptance bullet 2
- verdict: Present
- evidence: this record's own Verification section, below.
canonical: python3 -m pytest tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py -q — result: 28 passed in 7.05s (this session; see Verification section for the full paste)
- rationale: verify-at-landing requires this role's own executed command
  and output.
canonical: python3 -m pytest tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py -q — result: 28 passed in 7.05s (this session, independently re-run rather than citing PR #2170's own pasted numbers)

### R7 — fresh-clone empty state is not an error (trailing note: "empty state")

- spec_ref: trailing note "empty state"
- verdict: Present
- evidence: `gates/spawn_on_pr.py:275-288`
canonical: Read gates/spawn_on_pr.py:160-299 (this session)
```
def load_merged_seen(root: Path) -> set[str]:
    """issue #2165: 이미 `pr_state == "MERGED"` 로 확인된 subject 집합.
    없거나(첫 실행) 깨졌으면 빈 집합 — `closure_sweep._load_out_of_index_seen`
    과 같은 fail-safe 모양."""
    p = root / MERGED_SEEN_STATE_REL
    if not p.is_file():
        return set()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return set()
    if not isinstance(data, list):
        return set()
    return {s for s in data if isinstance(s, str)}
```
- rationale: matches the `closure_sweep._load_out_of_index_seen`
  fail-safe shape the survey already cited, almost line-for-line.
canonical: gates/closure_sweep.py:297-316 (survey's own citation,
`docs/issue-2165/reports/conformance-review/survey.md`, `## Existing
precedent this design mirrors`)
  Every test's tick 1 implicitly exercises the missing-file branch too,
  since `fixture_repo` starts each test with no
  `runs/spawn_on_pr_merged_seen.json` present.
canonical: Read tests/test_spawn_on_pr.py:38-51 (this session, `fixture_repo`
fixture body — creates a bare tmp_path git repo with no `runs/` directory)

### R8 — executed-live provenance (trailing note: "provenance")

- spec_ref: trailing note "provenance"
- verdict: Present
- evidence: `tests/test_spawn_on_pr.py:38` — `fixture_repo` is a real
  `tmp_path` git repository, not a mock filesystem.
canonical: Read tests/test_spawn_on_pr.py:38-51 (this session)
```
def fixture_repo(tmp_path, monkeypatch):
    """A local git repo standing in for the board root + a PR-having branch."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
```
  `monkeypatch` is applied only to the two `gh`-backed leaf calls, one
  set per new test:
canonical: Read tests/test_spawn_on_pr.py:319-336 (this session,
`test_missing_verification_sticky_merged_cache_survives_flaky_reconfirm`)
```
    monkeypatch.setattr(spawn_on_pr.spawn, "_pr_open_or_merged_for_branch", counted_pr_number)
    monkeypatch.setattr(
        spawn_on_pr.spawn, "_merged_pr_for_branch",
        lambda root, branch: 42 if branch == "issue-9001/implementation" else None)
```
  the same two leaf calls appear again in the R2-quoted end-to-end test
  — `missing_verification()` and `spawn_missing_for_pr()` themselves run
  unmocked in both tests (see the full body quoted under R2).
- rationale: matches this repo's established "executed-live" convention
  (a real repo fixture with `gh`-backed calls mocked only at the leaf).
canonical: python3 -m pytest tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py -q — result: 28 passed in 7.05s (this session; see Verification section)

### R9 — bounded-vs-unbounded / token-cost of the #513 pattern (Investigate bullet 2)

- spec_ref: Investigate bullet 2
- verdict: Unverifiable
- evidence: none locatable in this workspace.
canonical: gh issue view 2165 --json body — result (issue body's
`## Investigate` section asks to "check the actual token/session cost of
~50 near-instant respawns" without naming any log/telemetry source this
workspace can read, and the issue's trailing notes name only
`tests/test_spawn_on_pr.py` and `tests/test_spawn_on_pr_park.py` as
canonical sources, neither of which records the external target repo's
recurrence rate or cost)
- rationale: per verdict-assignment rule 3, unlocatable evidence is
  Unverifiable, named explicitly, rather than a favorable or
  unfavorable guess.
canonical: docs/issue-2165/reports/conformance-review/survey.md
(`## Requirement extraction`, R9: "this workspace has no log access to
the external target repo #513 ran in")

## Why

Full inspection of both changed files against all 9 extracted
requirements, verified by independently re-running the acceptance tests
in this session rather than citing PR #2170's own pasted numbers.
canonical: python3 -m pytest tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py -q — result: 28 passed in 7.05s (this session)
This follows this role's own credibility requirement stated in the
approved proposal.
canonical: docs/issue-2165/proposals/2026-08-24-conformance-review-plan.md
(`## Rationale`, "Chosen approach: full inspection of both changed files
against all 9 extracted requirements, verified by an independent live
test run")

## Upstream basis

- `docs/issue-2165/proposals/2026-08-24-conformance-review-plan.md` (this
  record's approved plan; `sha: same-commit`)
- `docs/issue-2165/reports/conformance-review/survey.md` (R1-R9
  extraction, sampling-derivation and verification-method-selection
  calls; `sha: same-commit`)
canonical: docs/issue-2165/reports/conformance-review/survey.md
(`## Sampling-derivation — not applicable`, "Full enumeration of R1-R9 is
feasible: one source file plus one test file, both small.")
- `gates/spawn_on_pr.py`, `tests/test_spawn_on_pr.py` at commit
  `1f9601df63f7c4df4431fe67115071ef1c05890a` (PR #2170's merge commit
  into `main`).
canonical: gh pr view 2170 --json mergeCommit,mergedAt — result:
{"mergeCommit":{"oid":"1f9601df63f7c4df4431fe67115071ef1c05890a"},"mergedAt":"2026-08-24T09:49:12Z"}
- `tests/test_spawn_on_pr_park.py` at commit
  `8ae79dc6befd710044de033679d09f5a0a280d8f` (unchanged by PR #2170; R5
  evidence).
canonical: git log -1 --format=%H -- tests/test_spawn_on_pr_park.py —
result: 8ae79dc6befd710044de033679d09f5a0a280d8f (this session)

## Verification

Independently re-run in this session against the merged-forward worktree
(not PR #2170's own pasted numbers):

canonical: python3 -m pytest tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py -q (this session)
```
............................                                             [100%]
28 passed in 7.05s
```

Neighbor sanity check (same command PR #2170 itself ran):

canonical: python3 -m pytest tests/test_watchdog_local_signals.py tests/test_watchdog_freshness.py -q (this session)
```
....................                                                     [100%]
20 passed in 5.61s
```

For contrast, PR #2170's own pasted claim (shown only to note the counts
above match it, not used as this record's own evidence):
canonical: gh pr view 2170 --json body (this session)
```
python3 -m pytest tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py -q — 28 passed, 0 failed, 0 skipped
python3 -m pytest tests/test_watchdog_local_signals.py tests/test_watchdog_freshness.py -q — 20 passed, 0 failed, 0 skipped
```

## Open findings

1. **R5** — `tests/test_spawn_on_pr_park.py` carries no #513-shape
   scenario (Surface, not Present/Absent — see R5 above for the specific
   ambiguity). Resolution path: a human reading of Acceptance bullet 1
   settles whether the file-pairing was a verification-command scope
   (satisfied) or a code-location requirement (not satisfied); no code
   change is proposed by this role either way.
canonical: docs/issue-2165/proposals/2026-08-24-conformance-review-plan.md
(`## Out of scope`, "Fixing or extending PR #2170's code — any finding
against R1-R9 is recorded as a verdict with a resolution path, not
patched by this role.")
2. **R9** — bounded-vs-unbounded and token/session cost of the #513
   pattern remain Unverifiable from this workspace. Resolution path: if
   this needs a real answer, it requires log/ledger access to the
   external target repo #513 ran in, which is outside this review's
   reach.
canonical: docs/issue-2165/proposals/2026-08-24-conformance-review-plan.md
(`## Out of scope`, "Determining the actual `gh`-flakiness recurrence
rate in the external target repo #513 ran in (R9) — no access from this
workspace, stated as Unverifiable rather than guessed.")

## Next steps

None — `loop_state: reported` is this record kind's terminal state for
`review-record` (contract v3 s2). Both open findings above have a stated
resolution path but require no further action from this role.

## Skill checks

skill-verdict: conformance-review-verdict-assignment — applied: invoked;
used to choose Surface over a hard Absent for R5 (rule 1) and
Unverifiable over a guessed bound for R9 (rule 3).
canonical: this session's own Skill tool invocations, applied to the R5
and R9 blocks above

skill-verdict: conformance-review-finding-record — applied: invoked;
used to write each R1-R9 block above with its full field list
(spec_ref, verdict, evidence pointer, rationale).
canonical: this session's own Skill tool invocation, applied to all nine
R1-R9 blocks above

other mounted skills: not triggered in this session —
conformance-review-requirement-extraction,
conformance-review-verification-method-selection, and
conformance-review-traceability-and-evidence were invoked in the phase-1
session, not re-invoked here.
canonical: docs/issue-2165/proposals/2026-08-24-conformance-review-plan.md
(`## Skill checks`, its own three skill-verdict lines)
conformance-review-sampling-derivation was checked and found
not-applicable in phase-1.
canonical: docs/issue-2165/reports/conformance-review/survey.md
(`## Sampling-derivation — not applicable`)
conformance-review-severity-classification is out of scope per this
issue's own proposal.
canonical: docs/issue-2165/proposals/2026-08-24-conformance-review-plan.md
(`## Out of scope`, "Severity-classification of any finding — this
issue's scope is ordinary conformance-checking, not an explicit
risk-weighting extension.")
