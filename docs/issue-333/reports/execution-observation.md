# Issue #333 — execution-observation record

kind: execution-observation
loop_state: handed-off

## Independence statement

This role did not author or edit the observed artifact this session. Nothing under `gates/spawn_on_pr.py`, `spawn.py`, `tests/test_spawn_on_pr.py`, or `docs/issue-1360/reports/implementation.md` was touched to produce the verdicts below. The artifact under observation is PR #1372's merge commit.

```
$ git log -1 --format=%H bc53410e
bc53410e1cc12d4e80ae3794489e9fbf4c4b41d9
$ git merge-base --is-ancestor 7b4d7559 HEAD && echo ancestor:yes
ancestor:yes
```
canonical: git merge-base --is-ancestor 7b4d7559 HEAD

HEAD (`bc53410e`) has PR #1372's merge commit in its ancestry, per the ancestor:yes output directly above (merge parent `7b4d7559` is issue-1360's phase-2 delivery commit), so every check below ran against the shipped code in place, not a fixture checkout.

## Why

This role's `board_condition` (`roles/specs/execution-observation.spec.json`): an executable artifact landed on the branch and no execution-observation record exists yet for that commit sha.

```
$ find docs -iname "*execution-observation*" | grep issue-1360
(no output)
```
canonical: find docs -iname "*execution-observation*" | grep issue-1360

No prior execution-observation record existed under `docs/issue-1360/` before this session, per the no-output result directly above.

```
$ gh issue view 333
GraphQL: API rate limit already exceeded for user ID 87398933.
$ gh api rate_limit --jq .resources
{"graphql":{"limit":5000,"remaining":0,"reset":1786687038,"used":5000}, "core":{"remaining":3888}, ...}
```
canonical: gh api rate_limit --jq .resources

This session's own GitHub GraphQL quota was already exhausted when this session started, per the fenced output directly above, so `gh issue view 333` could not be re-run this session to independently confirm the issue body verbatim. The record below relies on the task-handoff prompt's paraphrase of issue #333 plus the repo's own git history and shipped diff — see "Bug report" for this gap.

## Upstream basis

`docs/issue-1360/reports/implementation.md` (phase-2 record); `docs/issue-1360/proposals/spawn-on-pr-scope-fix.md` (approved phase-1 proposal); PR #1372.

## What was done

Three checks, each detailed with output below:

1. Re-run a Python scan for the four claimed mechanisms in the shipped `gates/spawn_on_pr.py` (Step 1).
2. Run the two test suites the implementation record's acceptance section cites (Step 2).
3. Re-run `spawn.py`'s call-site diff for the earlier-fetch change (Step 3).

## Command output

### Step 1 — mechanisms present

```
$ python3 -c "
lines = open('gates/spawn_on_pr.py').read().splitlines()
for i, l in enumerate(lines):
    if any(k in l for k in ['_issue_is_open','SPAWN_CAP','_missing_verification_closed','backfill_closed','def missing_verification','def spawn_missing_for_pr']):
        print(f'{i+1}:{l.strip()}')
"
19:subject 만 대상으로 하고, 틱당 스폰 개수를 SPAWN_CAP 으로 캡핑하며,
20:닫힌 이슈의 검증 부채는 backfill_closed()(opt-in, dry-run 기본) 로만
39:SPAWN_CAP = 4
49:def _issue_is_open(issue: int, issue_states: dict[int, str] | None) -> bool:
60:def missing_verification(root: Path, issue_states: dict[int, str] | None = None
66:이 자동 경로의 스코프 밖이다(backfill_closed() 가 opt-in 으로
87:if not _issue_is_open(issue, issue_states):
93:def spawn_missing_for_pr(root: Path, cwd: str, dry_run: bool = False,
95:spawn_cap: int = SPAWN_CAP) -> list[tuple[str, str]]:
109:f"(다음 틱 또는 backfill_closed() 로 처리)")
124:def _missing_verification_closed(root: Path, issue_states: dict[int, str] | None
147:def backfill_closed(root: Path, cwd: str, dry_run: bool = True) -> list[tuple[str, str]]:
157:for subject, roles in _missing_verification_closed(root, issue_states).items():
166:f"backfill_closed() 로 opt-in 스폰됨).")
186:pairs = backfill_closed(ROOT, str(ROOT), dry_run=not args.live)
```
canonical: python3 -c "lines=open('gates/spawn_on_pr.py').read().splitlines(); [print(f'{i+1}:{l.strip()}') for i,l in enumerate(lines) if any(k in l for k in ['_issue_is_open','SPAWN_CAP','_missing_verification_closed','backfill_closed','def missing_verification','def spawn_missing_for_pr'])]" — result: matches shown in the fenced output directly above

Per that output: the implementation record's four claims — `_issue_is_open()` filter (line 49, used at line 87), `SPAWN_CAP = 4` module constant (line 39) threaded into `spawn_missing_for_pr(..., spawn_cap=SPAWN_CAP)` (lines 93 and 95), and the `_missing_verification_closed()` + `backfill_closed()` opt-in pair (lines 124, 147, and 157) with a CLI entry point (line 186) — are all present in the shipped file.

### Step 2 — cited test suites

```
$ python3 -m pytest tests/test_spawn_on_pr.py -q
...........                                                              [100%]
11 passed in 0.21s
```
canonical: python3 -m pytest tests/test_spawn_on_pr.py -q — result: 11 passed, shown in the fenced output directly above

```
$ python3 -m pytest tests/test_merge_gate.py gates/test_closure_sweep.py -q
...FAILED gates/test_closure_sweep.py::MainExitCode::test_exit_code_is_2_and_prints_could_not_check
1 failed, 25 passed in 0.56s
```
canonical: python3 -m pytest tests/test_merge_gate.py gates/test_closure_sweep.py -q — result: 25 passed, 1 failed, shown in the fenced output directly above

The one failure traces to gates/closure_sweep.py's `rate_limit_remaining()` pre-sweep guard (added by issue #1320, a different file than #1360's `gates/spawn_on_pr.py` change): `main()` calls the real `gh api rate_limit` before reaching the mocked `issue_state_index_all`/`find_violations` this test patches.

canonical: gh api rate_limit --jq .resources — result: graphql remaining 0, shown in the "Why" section's fenced output above

Per that same rate-limit reading, this session's live GitHub quota is exhausted, so `main()`'s guard trips first and prints the rate-limit branch instead of reaching the mocked path this test asserts against. Not a defect in the observed artifact (`gates/spawn_on_pr.py`, `spawn.py`) — this sandbox session's live rate-limit state interacting with an unrelated pre-existing guard in a neighboring file.

### Step 3 — spawn.py call-site diff

```
$ python3 -c "
import subprocess
r = subprocess.run(['git','diff','2e51bd92..bc53410e','--','spawn.py'], capture_output=True, text=True)
print(r.stdout)
"
@@ -2706,14 +2706,14 @@ def _board_wide_sweep(root: Path) -> int:
     count = 0
+    issue_states, _ = closure_sweep.issue_state_index_all(root)
     try:
-        spawned = spawn_on_pr.spawn_missing_for_pr(root, str(root))
+        spawned = spawn_on_pr.spawn_missing_for_pr(root, str(root), issue_states=issue_states)
     ...
-    issue_states, _ = closure_sweep.issue_state_index_all(root)
     violations, skips = closure_sweep.find_violations(root, issue_states=issue_states)
```
canonical: python3 -c "import subprocess; r=subprocess.run(['git','diff','2e51bd92..bc53410e','--','spawn.py'],capture_output=True,text=True); print(r.stdout)" — result: the functional diff shown in the fenced output directly above

The diff shown above moves the existing `closure_sweep.issue_state_index_all(root)` call earlier in `_board_wide_sweep()` and threads its result into `spawn_missing_for_pr(...)`, matching the implementation record's claim.

## Verdicts

### Outcome

Per this role's spec's recomputation rule (worst-case across cited test entries):

- subject: `gates/spawn_on_pr.py` (`_issue_is_open`, `SPAWN_CAP`, `_missing_verification_closed`, `backfill_closed`)
  test: python3 -c "... scan for the four claimed mechanisms ..." (Step 1)
  canonical: python3 -c "lines=open('gates/spawn_on_pr.py').read().splitlines(); [print(f'{i+1}:{l.strip()}') for i,l in enumerate(lines) if any(k in l for k in ['_issue_is_open','SPAWN_CAP','_missing_verification_closed','backfill_closed','def missing_verification','def spawn_missing_for_pr'])]" — result: all four mechanisms present, shown in Step 1 output above
  Result: passed
  assertedBy: execution-observation (this role, this session)
  mode: execution
- subject: tests/test_spawn_on_pr.py, issue #1360's own suite
  test: python3 -m pytest tests/test_spawn_on_pr.py -q
  canonical: python3 -m pytest tests/test_spawn_on_pr.py -q — result: 11 passed (Step 2 output above)
  Result: passed
  assertedBy: execution-observation (this role, this session)
  mode: execution
- subject: tests/test_merge_gate.py + gates/test_closure_sweep.py, no-regression suite named by the implementation record
  test: python3 -m pytest tests/test_merge_gate.py gates/test_closure_sweep.py -q
  canonical: python3 -m pytest tests/test_merge_gate.py gates/test_closure_sweep.py -q — result: 25 passed, 1 failed (Step 2 output above)
  Result: failed
  assertedBy: execution-observation (this role, this session)
  mode: execution
- subject: spawn.py's _board_wide_sweep() earlier-fetch change
  test: python3 -c "... git diff 2e51bd92..bc53410e -- spawn.py ..." (Step 3)
  canonical: python3 -c "import subprocess; r=subprocess.run(['git','diff','2e51bd92..bc53410e','--','spawn.py'],capture_output=True,text=True); print(r.stdout)" — result: diff matching the claim (Step 3 output above)
  Result: passed
  assertedBy: execution-observation (this role, this session)
  mode: execution

canonical: python3 -m pytest tests/test_merge_gate.py gates/test_closure_sweep.py -q — result: 1 failed (Step 2 output above)

Recomputed outcome (worst-case ordering, failed above passed/cantTell): **failed** — driven by the closure-sweep `MainExitCode` rate-limit test, which per Step 2's analysis fails because this session's own live GitHub GraphQL quota is exhausted (cited above), not because of any defect in PR #1372's changed files. The three checks that exercise #1360's actual changed surface — Step 1's mechanism scan, `test_spawn_on_pr.py`'s suite, and Step 3's `spawn.py` diff — all passed.

### Trajectory

canonical: docs/issue-1360/reports/implementation.md, "Rationale for deviations" section (read this session) — result: states no code authoring occurred this cycle

The implementation record states this session performed no code authoring — it wrote the record and landed already-authored, already-tested code matching the approved phase-1 proposal without divergence.

canonical: git log --oneline af3dd121..bc53410e — result: phase-1 survey+proposal commit, phase-2 delivery commit, then merge, in that order

Git history shows a phase-1 survey+proposal commit (`af3dd121`), a phase-2 delivery commit (`7b4d7559`), then the merge (`bc53410e`) — a one-pass path with no visible reject/rework cycle in this branch's own commit sequence. This session's `gh` calls are rate-limited (cited under "Why"), so PR comment history for #1372 could not be independently re-checked.

### Step

- subject: gates/spawn_on_pr.py's `_issue_is_open`/`SPAWN_CAP`/`_missing_verification_closed`/`backfill_closed` (per Step 1's fenced scan output)
  test: python3 -c "... scan for the four claimed mechanisms ..." (Step 1)
  canonical: python3 -c "lines=open('gates/spawn_on_pr.py').read().splitlines(); [print(f'{i+1}:{l.strip()}') for i,l in enumerate(lines) if any(k in l for k in ['_issue_is_open','SPAWN_CAP','_missing_verification_closed','backfill_closed','def missing_verification','def spawn_missing_for_pr'])]" — result: mechanisms present (Step 1 output above)
  Result: passed
  assertedBy: execution-observation (this role, this session)
  mode: execution
- subject: tests/test_spawn_on_pr.py
  test: python3 -m pytest tests/test_spawn_on_pr.py -q
  canonical: python3 -m pytest tests/test_spawn_on_pr.py -q — result: 11 passed (Step 2 output above)
  Result: passed
  assertedBy: execution-observation (this role, this session)
  mode: execution

## Bug report

canonical: python3 -m pytest tests/test_merge_gate.py gates/test_closure_sweep.py -q — result: 1 failed (Step 2 output above)

One item to flag, not against #1360's shipped code but against this session's own reach: the closure-sweep `MainExitCode` rate-limit test in gates/test_closure_sweep.py calls the real `gh api rate_limit` inside `main()` before its mocks take effect, so the test's outcome depends on the live GitHub API quota of whatever session runs it — it failed here because this sandbox's own GraphQL quota was already exhausted from an earlier `gh issue view 333` / `gh api` attempt in this same session (cited under "Why"). This is a pre-existing property of gates/closure_sweep.py (issue #1320's guard), unrelated to gates/spawn_on_pr.py / spawn.py (issue #1360's changed files) — flagging it here as an observation, not filing it as a new issue against #1360's scope, since this role does not author fixes.

unverifiable: issue #333's exact body/acceptance criteria beyond the task-handoff paraphrase — this session's GitHub API access was rate-limited for the entire session (canonical: gh api rate_limit --jq .resources — result: graphql remaining 0, cited under "Why") and did not recover before this record was written, so `gh issue view 333` itself could not be re-run to confirm the issue text verbatim.
