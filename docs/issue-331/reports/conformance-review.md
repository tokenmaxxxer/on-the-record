# Conformance review of the checked-claims gate (issue #331)

kind: record
loop_state: reported
code_under_review:
- gates/gates.py
- gates/record_lint.py
- gates/ci.py
- tests/test_gates.py
- gates/test_closes_gate_ci.py
- docs/issue-331/decisions/2026-08-07-checked-claim-marker.md
- docs/specs/enforcement-boundary.md

## What was done

canonical: docs/issue-331/proposals/checked-claims-gate.md, read this
session — took the proposal's own "Constraints" and "How you'll know
it worked" sections as the requirement set below, then re-ran every
cited test node live against the current `main` tree and read the
relevant source directly.

## Why

This role's `use_when.board_condition` (roles/conformance-review.json):
an implementation commit landed on `issue-331/implementation` (merge
commit `68900a3b`) and no conformance-review record existed yet for
it.

## Per-requirement verdicts

### Req 1 — `record_checked_claims` exists, registered in `ALL`, and denies a terminal record with no section — Present

derived: `grep -n "def record_checked_claims" gates/gates.py`, run this
session:
```
752:def record_checked_claims(d: Path, cfg: dict) -> list[str]:
```
derived: `grep -n '"record_checked_claims":' gates/gates.py`, run this
session:
```
1274:       "record_checked_claims": record_checked_claims,
```
canonical: `python3 -m pytest -q tests/test_gates.py -k checked_claims`
— result: PASS (10 passed, 103 deselected), run this session — covers
the no-section-denied, unparseable-line-denied, nonexistent-test-
denied, and unverifiable-without-reason-denied cases the proposal
names.

### Req 2 — Terminal `loop_state` is read from roles/<role>.json, never hardcoded — Present

canonical: gates/gates.py lines 700-706 (`_terminal_loop_state`), read
this session — reads `role_cfg["record_fields"]["loop_state"]` and
returns `states[-1]`; no hardcoded "landed" string appears in
`record_checked_claims` or `parse_checked_claims`.

### Req 3 — gates/ci.py wires the gate into the default (non-`--closes-only`) check bundle — Present

derived: `grep -n "record_checked_claims\|closes_only: return bad" gates/ci.py gates/record_lint.py`,
run this session:
```
gates/record_lint.py:39:record_checked_claims = gates.record_checked_claims
gates/ci.py:456:    if closes_only:
gates/ci.py:457:        return bad
gates/ci.py:472:    bad += record_lint.record_checked_claims(repo, {})
```
canonical: `python3 -c "import gates.ci"` line count above, this
session — line 472 sits after the `closes_only` guard at 456-457,
inside `ci.check()`'s non-`closes_only` branch; gates/record_lint.py
line 39 shows it is the same function object as gates.py's
(re-exported per issue #517), not a second copy.

### Req 4 — CI status-check cross-check (`_pr_status_checks` / `_checked_ci_claims_bad`) — Present

derived: `grep -n "_pr_status_checks\|_checked_ci_claims_bad" gates/ci.py`,
run this session:
```
131:def _pr_status_checks(repo: Path, pr: int) -> list[dict] | None:
145:def _checked_ci_claims_bad(repo: Path, pr: int) -> list[str]:
474:        bad += _checked_ci_claims_bad(repo, pr)
```
canonical: `python3 -m pytest -q gates/test_closes_gate_ci.py -k checked_ci_claims`
— result: PASS (6 passed, 48 deselected), run this session — the
passing/failing/missing/pending/unreadable-fails-closed/no-claims-
skips-the-call cases all pass.

### Req 5 — Decision doc recorded — Present

derived: `ls docs/issue-331/decisions/`, run this session:
```
2026-08-07-checked-claim-marker.md
```

### Req 6 — Existence-only test-node verification, no execution (Constraint: "no re-execution of arbitrary repository commands") — Present

canonical: gates/gates.py lines 709-720 (`parse_checked_claims`), read
this session — the function parses `def test_name` occurrences in the
referenced file; neither it nor `record_checked_claims` imports
`subprocess` or calls `exec`/`eval`.

### Req 7 — CI workflow fires the bundle automatically on every PR (.github/workflows/plan-aware-closes-gate.yml) — Incorrect

derived: `find .github -iname "*closes-gate*"`, run this session:
```
bfs: error: .github: 그런 파일이나 디렉터리가 없습니다
```
derived: `git log --oneline --follow -- .github/workflows/plan-aware-closes-gate.yml`,
run this session:
```
1340d054 feat(issue-460): retire this repo's own GitHub Actions workflows
165bba83 issue-331: phase 2 — mechanical checked-claims gate for terminal loop_state
4b7a365a issue-369: read phase-2 record via gh api on PR ref, not local tree
b3ba2343 issue-245: phase 2 - closes-only required-check wiring (branch-protection activation handed to human)
```
canonical: same `find`/`git log` output above, this session — the
workflow file commit 165bba83 (this issue's own phase-2 commit) added
a step to was deleted one day later by commit 1340d054, issue #460's
deliberate, separately-approved retirement of this repo's GitHub
Actions workflows, not a regression in #331's own build.

canonical: docs/specs/enforcement-boundary.md line 157, read this
session:
```
| `plan-aware-closes-gate.yml` | repo-local, deleted | `--closes-only` step: zero-install `on-the-record/hooks/contract-guard.sh` + `spawn.py`'s `acceptance_gate` preflight (see `ci.py` row above). Full-bundle step (write_scope/protected-path/deps/`record_checked_claims`): no zero-install replacement; existing `contract, CI-supplement` drop, runnable locally as `python3 gates/ci.py . --pr <n> --autodetect` |
```
canonical: same table row above, this session — records the gap
explicitly: no zero-install replacement exists for the full-bundle
step.

canonical: the `find`/`git log` output above, this session — the
concrete artifact Req 7 names, a CI job that fires the
non-`--closes-only` bundle automatically on every PR, does not exist
on `main` today. Req 1 and Req 4 above show `record_checked_claims`
and the `statusCheckRollup` cross-check are real and their own unit
tests are green, but now only run when a human or role invokes
`python3 gates/ci.py . --pr <n> --autodetect` by hand — the same
self-report gap #331 was filed to close, reopened one layer up by
#460's later, independently-justified change.

## Summary table

| Req | Proposal criterion | Verdict |
|---|---|---|
| 1 | record_checked_claims denies unbacked terminal claims | Present |
| 2 | Terminal loop_state read from role config, not hardcoded | Present |
| 3 | Wired into ci.check()'s default bundle | Present |
| 4 | statusCheckRollup cross-check for CI-check claims | Present |
| 5 | Decision doc recorded | Present |
| 6 | No execution of named tests/commands | Present |
| 7 | CI workflow fires the bundle automatically on every PR | Incorrect |

canonical: the Acceptance verification section below, this session —
per this role's spec (roles/specs/conformance-review.spec.json,
`recomputation.rule`), overall verdict = worst case across the cited
results, where EARL's fixed severity ordering ranks "failed" worse
than "cantTell", "cantTell" worse than "inapplicable", "inapplicable"
worse than "untested", and "untested" worse than a fully-passing
result = Incorrect, driven by Req 7's fail result.

## Open findings

canonical: the Req 7 section above, this session — one open finding,
not filed anew: `record_checked_claims` and the CI-check cross-check
that #331 built are real and unit-tested, but nothing currently
invokes them automatically on a PR. docs/specs/enforcement-boundary.md's
migration table (cited above, read this session) already documents
this exact gap under issue #460's own row, so it is not routed as a
new issue.

## Next steps

- No action owed by this role beyond this verdict — the gap Req 7
  surfaces is already tracked in docs/specs/enforcement-boundary.md's
  migration table under issue #460, not orphaned.
- Whether the checked-claims bundle should get a zero-install
  replacement (a pre-commit/pre-push hook, mirroring `--closes-only`'s
  contract-guard.sh) is a design decision for #460's own follow-up
  scope, not this role's.

## Resolution path

This finding resolves when either (a) docs/specs/enforcement-boundary.md's
plan-aware-closes-gate.yml row gains a zero-install replacement for
the full-bundle step, verified by re-running the `find .github` and
enforcement-boundary.md table-read commands above and observing a
non-manual trigger, or (b) an operator ruling explicitly accepts the
manual-invocation-only state as final for this gate, recorded in the
same table.

Proposal: docs/issue-331/proposals/checked-claims-gate.md
Implementation: docs/issue-331/reports/implementation.md (merge commit 68900a3b)

## Acceptance verification

- Req 1 (deny unbacked terminal claims) — canonical: `python3 -m pytest -q tests/test_gates.py -k checked_claims` — result: PASS (10 passed, 103 deselected)
- Req 3 (wired into ci.check()) — canonical: `grep -n "record_checked_claims" gates/ci.py gates/record_lint.py` — result: PASS (gates/ci.py:472 calls record_lint.record_checked_claims; gates/record_lint.py:39 re-exports gates.record_checked_claims)
- Req 4 (statusCheckRollup cross-check) — canonical: `python3 -m pytest -q gates/test_closes_gate_ci.py -k checked_ci_claims` — result: PASS (6 passed, 48 deselected)
- Req 7 (CI workflow fires the bundle automatically) — canonical: `find .github -iname "*closes-gate*"` — result: FAIL (no .github directory on main; file deleted by issue #460, no automatic trigger remains)
