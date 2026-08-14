# Conformance-review survey — issue-321

## Subject

commit c27af1ab27a54b3a9eacc9fec6b84af366ab1c7c (PR #426, `issue-321:
close requirements-registry delivery (already on main via #352)`,
which merges PR #352's `77c978e0 issue-321: phase 2 — requirements
registry + regression gate`) — the landed implementation this role
audits against #321's Acceptance section (requirement R001).

## Method

Re-ran each of #321's four mechanically-checkable Acceptance criteria
live against current HEAD, independent of the implementation report's
own narrative (docs/issue-321/reports/implementation.md).

## Findings

### 1. R001 registry entry

canonical: docs/specs/requirements.md, read this session:
```
## R001

quote: 기록이 많아짐으로써 사용자가 핵심으로 제시하는 요구사항들이 희석되는 문제 (requirements dilute as the record grows)
source_issue: 321
check: gates/gates.py::requirement_registry
status: enforced
```
Both `quote` and `source_issue` fields are populated.

### 2. Regression gate on stale check path

canonical: gates/gates.py lines 641-664, read this session — walks
registry entries and appends a failure string when the `check` path
does not exist at HEAD (for non-`UNVERIFIABLE:` entries).
derived: `python3 -m pytest tests/test_gates.py -k requirement_registry -q`,
run this session:
```
........
8 passed, 105 deselected in 0.29s
```
canonical: same pytest output above — includes fixtures that
construct a stale `check` path and assert the gate flags it
(`t_requirement_registry_missing_field_blocks`,
`t_requirement_registry_unverifiable_passes`, both in
tests/test_gates.py).

### 3. CI wiring

canonical: gates/ci.py line 470, read this session:
```
    bad += gates.requirement_registry(repo, {})
```
inside `ci.check`.
canonical: `git log --all --oneline -- .github`, run this session,
top entry:
```
1340d054 feat(issue-460): retire this repo's own GitHub Actions workflows
```
so "CI" here resolves to `ci.check` invoked at PR-preflight time, not
a GitHub Actions workflow.
canonical: spawn.py line 1542, read this session:
```
        bad = ci.check(Path(cwd).resolve())
```
confirming the call chain from spawn.py reaches `requirement_registry`
through `ci.check`.

### 4. CI-wiring regression test

canonical: tests/test_gates.py lines 1351-1362, read this session —
builds a fixture repo whose R001 `check` path does not exist and
asserts `ci.check` (not `requirement_registry` called directly)
surfaces the failure.
derived: `python3 -m pytest tests/test_gates.py -k t_ci_check_wires_requirement_registry -q`,
run this session:
```
.
1 passed, 112 deselected in 0.29s
```

### 5. Re-checkability at HEAD (not snapshotted)

canonical: `gh issue view 321` Acceptance section, read this session
— already marks this criterion `unverifiable: ...` and names
criterion 2's fail-on-stale-path behavior as its practical stand-in.
No additional mechanical check exists beyond what the issue itself
declined to require.

## Verdict preview

canonical: findings 1-4 above (each with its own derived/canonical
citation, this session) — all four mechanically-checkable criteria
reproduce live at HEAD; finding 5 is the issue's own declared
Unverifiable escape.

## Gaps / unknowns this survey did not resolve

- Whether any commit landed after c27af1ab has separately regressed
  the registry or its gate is out of this survey's scope — the subject
  is #321's own landed delivery, not the full subsequent commit
  history.

## Next step

canonical: `gh issue view 321 --json comments`, run this session — no
comment reading exactly `APPROVE issue-321/conformance-review` exists
on issue #321 yet. Phase-2 write
(docs/issue-321/reports/conformance-review.md) is gated on that
approval from a docs/specs/approvers.md account. This survey's
findings are ready to carry into that record once approval posts.
