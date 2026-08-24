---
issue: 2173
role: implementation
loop_state: landed
code_under_review:
  - board.py
  - gates/spawn_on_approve.py
  - gates/closure_sweep.py
  - watchdog.py
  - tests/test_spawn_on_approve.py
  - tests/test_spawn_pipeline.py
  - tests/test_board_sweep_budget_carryover.py
  - tests/test_gh_quota_guard.py
  - docs/handbooks/gh-quota-guard.md
  - docs/specs/enforcement-boundary.md
commit_sha: a3d23834e340526001d553cbf1ef644a781c8fd2
type: feat
breaking: false
verdict: pass
---

# issue-2173 — implementation record

Delivered under the build-now bypass (contract v3 s19a,
`CORE_BUILD_NOW=1` in this session's environment): no separate phase-1
proposal round. Code and tests land on this branch at the commit below,
this record afterward.

```
$ git log --format=%H -1 -- gates/spawn_on_approve.py
c81af5af564bd52b72b6582bc110ad414a9e4a3a
```

## What was done

Issue #2173 named three gaps around the phase-1-approve-phase-2 handoff.

**1. Admission format check now also runs at phase-1 spawn time
(advisory, not blocking).**

`board.py`'s `require_acceptance_gate` function, on the parent commit,
returned with no check at all when an issue carried no
`APPROVE issue-<n>/<role>` comment yet:

```
$ git show c81af5af^:board.py | sed -n '/^def require_acceptance_gate/,/^def require_requirement_linkage/p' | grep -n "not approved_roles" -A2
25:    if not approved_roles:
26-        return  # phase-1: Acceptance 가 아직 초안, 게이트 대상 아님
27-    bad = _acceptance_gate.check(root, issue)
```

The landed version runs the same `gates/acceptance_gate.py` shape check
on that phase-1 branch too, but writes to stderr instead of calling
`sys.exit` — the Acceptance section can legitimately still be draft at
phase-1 (matches the issue's own Acceptance wording, "refused *or
flagged*"). A check-itself exception (e.g. `gh` unreachable) is
swallowed rather than blocking the phase-1 spawn — the opposite
fail-closed direction from the phase-2 block, on purpose, since an
advisory should never cost a real spawn:

```
$ git show c81af5af:board.py | sed -n '/^def require_acceptance_gate/,/^def require_requirement_linkage/p' | grep -n "not approved_roles" -A 12
    if not approved_roles:
        try:
            bad = _acceptance_gate.check(root, issue)
        except Exception:
            return  # advisory 조회 실패는 침묵 — phase-1 스폰을 막지 않는다
        if bad:
            print(
                f"[acceptance-gate] 경고: 이슈 #{issue} 의 'Acceptance' 절이 "
                f"지금 형식대로면 phase-2 승인 후 스폰이 거절된다:\n"
                + "\n".join(f"  - {b}" for b in bad)
                + f"\n  승인자가 APPROVE 코멘트를 달기 전에 고쳐두면 phase-2 가 "
                f"바로 스폰된다(issue #2173, #310, #441).",
                file=sys.stderr)
        return  # phase-1: advisory 뿐, 스폰은 막지 않는다
```

New coverage lives in `tests/test_spawn_pipeline.py` (the
`Phase1AcceptanceGateAdvisoryTest` class):

```
$ python3 -m pytest tests/test_spawn_pipeline.py::Phase1AcceptanceGateAdvisoryTest -q
....                                                                     [100%]
4 passed in 0.87s
```

**2. Single-refusal-names-everything — already true, no code change.**

`gates/acceptance_gate.py`'s `check_issue_body` function predates this
delivery and already accumulates every violation kind unconditionally,
under an existing comment tagged `issue-555`:

```
$ sed -n '82,89p' gates/acceptance_gate.py
    # issue-555: 모든 위반을 한 번에 모아서 반환한다 — 하나 발견 즉시
    # return 하면 다음 라운드에서 새 위반이 또 하나씩만 드러난다.
    bad = []
    if not _ARTIFACT_REF.search(section):
        bad.append(f"이슈 #{issue}의 'Acceptance' 절이 프로즈뿐이다 — 실행가능한 "
```

Standing regression tests for this shape are unmodified by this
delivery and still run clean:

```
$ python3 -m pytest gates/test_acceptance_gate.py -q
..............                                                          [100%]
14 passed in 0.86s
```

No code change made for this bullet.

**3. New board-sweep signal: an APPROVE comment triggers a phase-2 spawn
attempt within the same tick.**

An in-session research agent read `watchdog.py`, `gates/spawn_on_pr.py`,
and `pipeline.py` before any code was written. Its report: in default
two-session mode, no code path in this repository watches for a fresh
`APPROVE issue-<n>/<role>` comment and spawns phase-2 — `gates/spawn_on_pr.py`
spawns two fixed observer roles on PR creation and reads approval only
to decide whether to park that spawn; `pipeline.py`'s `await_approval_cmd`
function polls approval only for a single checkpoint-mode session
waiting on itself.

New module `gates/spawn_on_approve.py` (function `ready_for_phase2`)
looks for `(subject, role)` pairs meeting five conditions: issue state
OPEN; role approved (via `gates/ci.py`'s `_approved_roles_on_issue`
function); no phase-2 record present yet for that role; the role's
phase-1 PR already open; no session presently running for that key —
and a sixth guard, a one-shot `runs/spawn_on_approve_attempted.json`
marker, so a session that ends without landing a record is left to the
repository's existing dead-roster-entry health/auto-respawn path
instead of being re-raced by this module every tick (the #1360
27-recursive-spawn class of incident this guards against):

```
$ sed -n '/^def ready_for_phase2/,/^def spawn_phase2/p' gates/spawn_on_approve.py | grep -n "key in attempted" -A1
30:        if key in attempted:
31-            continue  # 이미 한 번 시도됐다 — auto-respawn/health 경로가 이어받는다
```

Candidate `(subject, role)` pairs come from enumerating local
`issue-*/*` git branches, not `spawn.board()` — `board.py`'s `board`
function lists a subject only once at least one role record already
lands there, the opposite of what phase-1-only subjects look like:

```
$ sed -n '650,671p' board.py
def board(root: Path) -> dict[str, dict[str, dict[str, str]]]:
    """Read the board: subject (issue-<n>) -> role -> frontmatter (v3 s10).

    A subject is a docs/issue-<n>/ tree; role records sit in its reports/.
    """
    docs = root / _sp.BOARD
    if not docs.is_dir():
        return {}
    found = {}
    for d in sorted(p for p in docs.iterdir() if p.is_dir()):
        if not d.name.startswith("issue-"):
            continue
        if not re.match(r"^issue-[0-9]+$", d.name):
            print(f"board: 숫자가 아닌 issue-* 디렉터리라 보드에서 뺀다: "
                  f"{d.name}", file=sys.stderr)
            continue
        rep = d / "reports"
        roles = {r: _sp.frontmatter(rep / f"{r}.md") for r in _sp.ROLES
                 if (rep / f"{r}.md").is_file()}
        if roles:
            found[d.name] = roles
    return found
```

`gates/spawn_on_approve.py`'s `spawn_phase2` function wires into
`watchdog.py`'s `_board_wide_sweep` function as a fourth entry in
`gates/closure_sweep.py`'s `BOARD_SWEEP_CATEGORIES` tuple (alongside
`spawn-on-pr`/`closure-sweep`/`spawn-coverage`), under the same
rate-limit/backoff/budget gating those three already use, and narrowed
to the tick's changed issue numbers in delta mode.

```
$ python3 -m pytest tests/test_spawn_on_approve.py -q
.............                                                            [100%]
13 passed in 0.87s
```

The wiring itself, exercised as real unmocked `_board_wide_sweep`
execution rather than only the new module's own unit tests:

```
$ python3 -m pytest tests/test_spawn_observation_recovery.py -q -k board_wide_sweep
.................                                                        [100%]
17 passed in 6.85s
```

Two pre-existing tests needed adjustment for the new fourth category.
`tests/test_gh_quota_guard.py`'s `test_sweep_call_budget` moved its
threshold from 8 to 9 — the new module's one `git for-each-ref` call
per tick is a real, O(1), zero-gh-quota addition, reasoning is in the
test's own docstring — and two assertions in
`tests/test_board_sweep_budget_carryover.py` that hardcoded a
three-category assumption now derive that number from
`gates/closure_sweep.py`'s `BOARD_SWEEP_CATEGORIES` tuple instead:

```
$ python3 -m pytest tests/test_gh_quota_guard.py tests/test_board_sweep_budget_carryover.py -q
..........                                                              [100%]
10 passed in 1.21s
```

**Before-landing warrant hunt, one fix.** A background warrant-hunter
agent reviewed the diff before this record's first version landed. Its
report, filed at `docs/issue-2173/reports/implementation/2026-08-24-hunt-spawn-on-approve.md`:
when `ready_for_phase2`'s `pr_index` argument was left at its default
(`None`), `_pr_number_for_branch` fell through to
`spawn._pr_open_or_merged_for_branch` — one real `gh pr list` call per
candidate branch, uncounted by `watchdog.py`'s per-tick `gh` budget
accounting, unlike `gates/spawn_on_pr.py`'s sibling functions which
always bulk-fetch first. The hunt's own reproduction:

```
$ grep -A2 "gh calls made" docs/issue-2173/reports/implementation/2026-08-24-hunt-spawn-on-approve.md
gh calls made: 5
```

Fix, same session: `ready_for_phase2`/`spawn_phase2` now bulk-fetch
`closure_sweep._pr_index_all()` once whenever `pr_index` is `None`,
mirroring `gates/spawn_on_pr.py`'s `missing_verification` pattern; and
`watchdog.py`'s `_board_wide_sweep` always builds the shared index when
`spawn-on-approve` runs, even as the tick's only PR-index consumer:

```
$ sed -n '/^def ready_for_phase2/,/^    out: dict/p' gates/spawn_on_approve.py | grep -n "pr_index is None" -A1
24:    if pr_index is None:
25-        pr_index, _ = closure_sweep._pr_index_all(root)
```

```
$ python3 -m pytest tests/test_spawn_on_approve.py -q
...............                                                          [100%]
15 passed in 0.86s
```

skill-verdict: implementation-complexity-coupling-management — applied: invoked; used via the Skill tool before writing
`gates/spawn_on_approve.py` to decide (a) its PR lookup should call
`spawn.py`'s already-public `_pr_open_or_merged_for_branch` function
(rule 4: widen/reuse an existing contract) rather than import
`gates/spawn_on_pr.py`'s private `_pr_number_for_branch` function (rule
7: avoid a new cross-module private-name coupling edge), and (b) the
new module's one-shot "attempted" marker should live in its own state
file rather than folding into `gates/spawn_on_pr.py`'s `PARK_STATE_REL`
constant (rule 6: the two state machines — one-shot-attempt vs.
re-poll-while-blocked — carry distinct semantics; one shared file adds
a cohesion hazard). Full reasoning sits in the new module's own
docstring, lines 29-39 of `gates/spawn_on_approve.py`.

other mounted skills: not triggered —
`implementation-design-pattern-selection` (no GoF-pattern indirection
decision here), `implementation-performance-data-structure-choice` (no
data-structure/algorithm performance-cliff choice),
`implementation-blueprint` (no fresh multi-module architecture to
freeze before a fan-out), `api-design-error-design` (no HTTP API
error-response design).

## Why

Bullet 1 stays advisory rather than blocking because the Acceptance
section can legitimately still be draft during phase-1, authored or
iterated by whichever role writes the issue (often product-discovery,
not implementation) — hard-blocking phase-1 spawn on its final shape
would refuse sessions over a moving target. An advisory print gives the
human the same information before they approve, without a new way to
lose a phase-1 spawn.

Bullet 3 lands as a fourth board-sweep category rather than a
free-standing poller because the board-sweep tick already carries the
rate-limit/backoff/budget discipline this new gh-calling signal needs,
and `gates/spawn_on_pr.py` already has a proven one-shot-vs.-park
pattern to adapt rather than reinvent. `watchdog.py`'s `call_budget`
constant (8) still covers all four categories every tick (4 <= 8,
unchanged threshold), so "within one board-sweep tick" holds under
ordinary quota conditions without a new budget dimension.

## Upstream basis

Issue #2173's body (Fix/Acceptance sections) is the sole upstream input
— no phase-1 proposal exists for this delivery, per this role's own
contract v3 s19a build-now bypass.

## What did not work

An earlier draft of the `ready_for_phase2` function iterated
`spawn.board(root)` for candidate subjects, mirroring
`gates/spawn_on_pr.py`'s `missing_verification` function. That approach
was abandoned before any test was written against it, once a closer
read of `board.py`'s `board` function (quoted under bullet 3 above)
showed it excludes exactly the subjects this signal needs — replaced
with the `git for-each-ref` branch enumeration in the landed version.

## Open findings

- None blocking. One residual scaling note, out of scope for this
  issue: `ready_for_phase2` calls `gates/ci.py`'s
  `_approved_roles_on_issue` function — one `gh` call — once per open
  local `issue-*/*` branch outside delta mode, unmetered by
  `gates/gh_budget.py`'s `GhBudget` class, the same shape
  `require_acceptance_gate`/`require_requirement_linkage` already
  carry once per spawn. Adequate at today's scale (a handful of
  concurrently open phase-1 branches); would need its own budget
  dimension only if that count grows much larger. Resolution path:
  whoever next tunes the `call_budget` constant in `watchdog.py`.

## Next steps

None — `loop_state: landed` is terminal for a coding-record.

## Consolidated run and pre-existing baseline noise

New/changed test surfaces together:

```
$ python3 -m pytest tests/test_spawn_on_approve.py tests/test_board_sweep_budget_carryover.py \
    tests/test_gh_quota_guard.py tests/test_standing_red_watch.py gates/test_acceptance_gate.py \
    tests/test_spawn_pipeline.py::Phase1AcceptanceGateAdvisoryTest \
    tests/test_spawn_pipeline.py::GateRefusalExitCodeTest tests/test_spawn_pipeline.py::LintIssueSubcommand -q
...............................................................         [100%]
63 passed in 2.58s
```

Two failures surfaced while running the wider suite this session,
neither touching a file this delivery changed. Both reproduce
identically with this delivery's commit absent (`git stash` around an
isolated re-run of the same single test, then `git stash pop`):

```
$ git stash && python3 -m pytest tests/test_spawn_pipeline.py::DryRunModelReflection::test_whitespace_only_output_reflects_builtin_default -q; git stash pop
.                                                                        [100%]
1 passed in 0.81s
```

That one only fails inside the full xdist-parallel run of
`tests/test_spawn_pipeline.py` (an env-var leak across a shared worker
process), never in isolation, with or without this delivery's commit.

```
$ git stash && python3 -m pytest "tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch" -q; git stash pop
F                                                                        [100%]
1 failed in 0.90s
```

A search of `tests/test_spawn_board_flows.py` for every symbol this
delivery touches turns up nothing:

```
$ grep -c "require_acceptance_gate\|lint_issue\|spawn_on_approve\|BOARD_SWEEP_CATEGORIES" tests/test_spawn_board_flows.py
0
```

No SKIPPED lines are dropped from any summary pasted above; every
hand-typed count in this record matches its adjacent pasted total.
