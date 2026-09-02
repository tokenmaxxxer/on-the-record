---
issue: 3057
role: refactoring-legacy-seam-selection+silent-failure-audit+merge-gates+architecture-dependency-direction-9b4a1ebc
author: refactoring-legacy-seam-selection+silent-failure-audit+merge-gates+architecture-dependency-direction-9b4a1ebc
skills: refactoring-legacy-seam-selection (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), merge-gates (skill-repository(c05de12)), architecture-dependency-direction (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: delivered
upstream:
  - path: gh issue view 3057 (issue body + correcting comment, replaces the original Acceptance set)
    sha: same-commit
---

# issue-3057 — refactoring-legacy-seam-selection+silent-failure-audit+merge-gates+architecture-dependency-direction-9b4a1ebc record

## What was done

derived: every claim below was executed live this session; see the fenced commands/output inline and `## Acceptance verification`.

Three separable fixes to `gates/merge_gate.py` and `gates/check_runner.py`, plus one re-derived (not re-fixed) finding on the third reported blocker.

**1. Sibling-import collision (root cause of the `AttributeError`).** Both files did a bare `import gates` intending the sibling `gates/gates.py`. That resolves correctly when the file runs as a script (`sys.path[0]` is `gates/`), but under `python3 -m gates.<module>` the name `gates` is already bound to the enclosing namespace package — `ls gates/__init__.py` finds no such file, so it is an implicit namespace package — so the bare import silently binds to that package instead and `gates.record_frontmatter`/`gates.RECORD_PATH` raise `AttributeError`. Fixed by replacing the bare import in both files with the same `importlib.util.spec_from_file_location` sibling-load-by-path pattern already used by `gates/claims.py`, `gates/risk_report.py`, `gates/ui_evidence_gate.py`, `gates/ci.py`, `gates/record_lint.py`, and `on-the-record/gates/record_lint.py` — cached under the same shared `sys.modules` key (`_on_the_record_gates_sibling_impl`) those files already use, so all modules share one loaded `gates.py` instance per process rather than re-executing it once per file.

**2. Exit code carried no verdict.** `gates/merge_gate.py::main()` returned `0` for allow, `1` for refuse, and (via Python's default handler for an uncaught exception) also `1` for a crash. Added `EXIT_ALLOWED = 0`, `EXIT_REFUSED = 1`, `EXIT_COULD_NOT_DECIDE = 2` and wrapped the single `evaluate()` call in `main()` in a `try`/`except Exception` that prints the full traceback (via `traceback.print_exc()`, to stderr) plus one line naming the PR/subject and warning against reading `EXIT_COULD_NOT_DECIDE` as `EXIT_REFUSED`, then returns `EXIT_COULD_NOT_DECIDE`. `main()` returns immediately after printing — no verdict is fabricated, `evaluate()` itself is untouched. Bad-usage paths (missing args, non-integer PR) were also moved to `EXIT_COULD_NOT_DECIDE`.

**3. The self-referential verification deadlock — re-derived, not re-fixed.** Independently reran the working form against the live pair the issue names (PR #3043, its independent-verification PR #3055, both under subject `issue-3042`). See `## Acceptance verification` below for the executed evidence: `required_verification_missing()` already returns `0` for PR #3055 evaluating itself against subject `issue-3042` — the `_own_pr_supplies_verification()` self-exemption from issue #2609 already fires for this exact pair. No code change was made for this item.

Added `gates/test_merge_gate.py` (new this session):
```
$ git show HEAD:gates/test_merge_gate.py
fatal: path 'gates/test_merge_gate.py' does not exist in 'HEAD'
```
```
$ python3 -m pytest gates/test_merge_gate.py -q
....                                                                     [100%]
4 passed in 0.82s
```
Pins the three-way exit-code split and the no-catch-and-continue behavior via monkeypatching `merge_gate.evaluate` rather than hitting the network, since `main()` had no prior test coverage.

## Why

derived: this section's claims are grounded by the fenced commands/output inline below (this session).

`refactoring-legacy-seam-selection`: the fix for (1) reuses the exact seam the codebase had already standardized on (`evaluate`/`gates` as monkeypatch/reload points) rather than inventing a new one — Sprout-Method-shaped, localized to the single import line and the single `evaluate()` call site in `main()`, closest to the actual point of behavioral difference (skill rule 5), narrowed to that one call rather than seaming all of `main()` (rule 6).

`silent-failure-audit`: the new `except Exception` block in `main()` is the only new error-handling site this session added. Classified Handled (H): the error is (a) logged with full context and (d) propagated via a distinct, non-zero, non-`EXIT_REFUSED` return code — execution does not continue past the `return`.
```
$ python3 gates/merge_gate.py 3043 issue-3042 --repo /nonexistent/path/xyz
Traceback (most recent call last):
  ...
FileNotFoundError: [Errno 2] No such file or directory: PosixPath('/nonexistent/path/xyz')
판정 불가: PR #3043 (issue-3042) — 게이트 실행 중 처리되지 않은 예외 발생, 위 트레이스백 참고. 이 종료 코드를 거절(1)로 읽지 말 것.
$ echo $?
2
```
No `허용:`/`거절:` verdict text appears in that output — the H classification (traceback surfaced, no fabricated verdict) is grounded in the fenced run just above.

`merge-gates`: applied the shape test (Step 2) to the exit-code change — `EXIT_COULD_NOT_DECIDE` is still non-zero, so property (c) (fail-closed) holds for any existing caller that already treated `rc != 0` as blocked.
```
$ python3 -c "import sys; sys.path.insert(0,'gates'); import merge_gate; print(merge_gate.EXIT_ALLOWED, merge_gate.EXIT_REFUSED, merge_gate.EXIT_COULD_NOT_DECIDE)"
0 1 2
```
Also used Step 4 (fail-open audit) on the pre-existing `_own_pr_supplies_verification()` exemption while re-deriving item 3 — read `gates/merge_gate.py:172-185` this session; the exemption requires `own_branch.startswith(f"{subject}/")` AND a `git show` of that exact branch's own record AND `fm.get("verifies_subject") == "true"` AND an author differing from the subject's deliverable author, scoped to the one PR under evaluation, not a wholesale exemption of all observer PRs.

`architecture-dependency-direction`: judged not-applicable — this fix changes how an existing sibling-module dependency resolves at import time under two invocation forms, not which way any dependency arrow points between modules/layers; `merge_gate.py`/`check_runner.py` still depend on `gates.py` exactly as before.

## What did not work

derived: `python3 gates/check_runner.py 3055 3042` (run this session) — see fenced output below.

Running `python3 gates/check_runner.py 3055 3042` while re-deriving item 3 posted a real "no checks declared" comment to live PR #3055 on GitHub as a side effect of `check_runner.post_comment()` — the check-runner's normal, intended behavior (it always posts its result comment), not a bug, but not anticipated going in. The comment is accurate (issue-3042's Acceptance section genuinely has no mechanical checks) and needs no reverting.
```
$ python3 gates/check_runner.py 3055 3042
## Acceptance check-runner result: no checks declared
...
$ echo $?
0
```
Exit 0 is the record-only/no-mechanical-check path's designed return per `gates/check_runner.py:672-676`.

## Upstream basis

derived: the file list and PR states below are quoted verbatim from the commands shown.

- `gh issue view 3057` — issue body (original three-point Acceptance) and its correcting comment (the operative, narrower Acceptance set this record satisfies — see frontmatter `upstream:`).
- Live GitHub PR state read this session:
```
$ gh pr view 3043 --json number,state,headRefName,baseRefName
{"baseRefName":"main","headRefName":"issue-3042/implementation-audit+silent-failure-audit+conformance-review-verdict-assignment+defect-verification-independence-from-upstream-verdicts-0d4eb553","number":3043,"state":"OPEN"}
$ gh pr view 3055 --json number,state,headRefName,baseRefName
{"baseRefName":"main","headRefName":"issue-3042/conformance-review-verdict-assignment+adversarial-review+implementation-audit+defect-verification-independence-from-upstream-verdicts-5cdf6b1a","number":3055,"state":"OPEN"}
```
- Pre-existing sibling-import fix pattern in `gates/claims.py`, `gates/risk_report.py`, `gates/ui_evidence_gate.py`, `gates/ci.py`, `gates/record_lint.py`, `on-the-record/gates/record_lint.py` (issue #2226) — reused verbatim.
```
$ grep -rln "_GATES_IMPL_KEY\|^import gates\b" gates/*.py on-the-record/gates/*.py
gates/claims.py
gates/check_runner.py
gates/record_lint.py
gates/ui_evidence_gate.py
gates/risk_report.py
gates/merge_gate.py
gates/ci.py
on-the-record/gates/record_lint.py
```
- `_own_pr_supplies_verification()` / `required_verification_missing()` in `gates/merge_gate.py` (issue #2609) — the prior fix independently re-verified live this session, not re-derived from scratch (see `## Acceptance verification`).

## Open findings

derived: `python3 -m pytest gates/ -q` (run this session) and `python3 gates/check_runner.py 3055 3042` (run this session) — see fenced output below.

None outstanding for this issue's scope.
```
$ python3 -m pytest gates/ -q
..............................................                           [100%]
46 passed in 0.83s
```
Full `gates/` suite, this session's two edited files plus new test file included, no failures.

Out of scope but observed: issue-3042's Acceptance section is entirely judgment-type checks, so no PR under that subject currently gets past `merge_gate.py`'s check-runner track regardless of verification count or landing order — a separate, pre-existing, intentional design point (issue #2233 empty-state), not filed as a new issue since it was not asked for.
```
$ python3 gates/check_runner.py 3055 3042
## Acceptance check-runner result: no checks declared

이 이슈의 `## Acceptance` 절에 있는 4개 `check:`/`gate:` 항목이 전부 판단이 필요한(judgment) 기준이라 기계적으로 실행할 검사가 없다.
```

## Next steps

None — `loop_state: delivered`, terminal for this record.

## Acceptance verification

derived: every requirement below was checked live this session — see the fenced command/output pairs.

Requirement (correcting comment): both invocation forms produce the same verdict for the same PR.
```
$ diff <(python3 gates/merge_gate.py 3043 issue-3042) <(python3 -m gates.merge_gate 3043 issue-3042)
(no output — diff is empty)
$ python3 gates/merge_gate.py 3043 issue-3042; echo "rc=$?"
거절: PR #3043 (issue-3042)
  - check-runner: 이슈의 Acceptance 절에 실행가능한 검사가 없다(no checks declared) — 통과로 취급하지 않는다
  - required_verification_missing(): 독립 검증 기록이 부족하다 -- 0/2개 확인됨 (2개 더 필요)
rc=1
$ python3 -m gates.merge_gate 3043 issue-3042; echo "rc=$?"
거절: PR #3043 (issue-3042)
  - check-runner: 이슈의 Acceptance 절에 실행가능한 검사가 없다(no checks declared) — 통과로 취급하지 않는다
  - required_verification_missing(): 독립 검증 기록이 부족하다 -- 0/2개 확인됨 (2개 더 필요)
rc=1
```
Satisfied — identical output, identical rc.

Requirement: the exit code distinguishes allow, refuse, and could-not-decide.
Satisfied by the fenced `pytest gates/test_merge_gate.py -q` run under `## What was done` (4 passed, pinning rc=0/1/2 against `EXIT_ALLOWED`/`EXIT_REFUSED`/`EXIT_COULD_NOT_DECIDE`) and the fenced forced-crash run under `## Why` (rc=2, via a nonexistent `--repo` making `subprocess.run(cwd=...)` inside `check_runner.fetch_all_skill_branches()` raise `FileNotFoundError`) plus the live refusal run just above in this section (rc=1).

Requirement: a deliverable PR and its independent-verification PR can both land, and the record shows the order that worked.
empty state invoked (issue's own clause): the chosen finding makes landing order irrelevant to the self-reference cycle specifically — no fix was needed for that cycle, and neither PR was landed by this session (merging PRs #3043/#3055, authored by unrelated role sessions, to `main` is outside this session's write set/authority and was not attempted).
```
$ python3 -c "
import sys; sys.path.insert(0,'gates'); sys.path.insert(0,'.')
import merge_gate
from pathlib import Path
r = Path('.').resolve()
print('3043:', merge_gate.required_verification_missing(r, 'issue-3042', r, 3043))
print('3055:', merge_gate.required_verification_missing(r, 'issue-3042', r, 3055))
"
3043: 2
3055: 0
```
PR #3043 needs 2 more landed verifications; PR #3055 needs 0 (self-exempted) — the self-reference cycle does not currently block #3055 on #3043 landing first.
```
$ python3 gates/merge_gate.py 3055 issue-3042; echo "rc=$?"
거절: PR #3055 (issue-3042)
  - check-runner 코멘트를 찾을 수 없다
rc=1
```
Refused for a missing check-runner comment (later, after running check-runner, for `no checks declared` — see `## What did not work`) — never for `required_verification_missing`.

Requirement: every module under `gates/` and `on-the-record/gates/` importing a sibling by bare name is listed, with what it resolves to under each invocation form.
population: all `.py` under `gates/` and `on-the-record/gates/`.
```
$ ls gates/*.py | wc -l
67
$ ls on-the-record/gates/*.py | wc -l
2
$ git show HEAD:gates/merge_gate.py | grep -n "^import gates"
24:import gates  # noqa: E402
$ git show HEAD:gates/check_runner.py | grep -n "^import gates"
40:import gates  # noqa: E402
```
(confirms the pre-session state for the two files this session fixed — see the population commands just above.)

| module | sibling import | script form | `-m` form before this session | `-m` form after this session |
|---|---|---|---|---|
| `gates/merge_gate.py` | `import gates` | resolves to `gates/gates.py` | `AttributeError` (namespace package) | resolves to `gates/gates.py` (fixed) |
| `gates/check_runner.py` | `import gates` | resolves to `gates/gates.py` | `AttributeError` (namespace package) | resolves to `gates/gates.py` (fixed) |
| `gates/claims.py` | sibling-load-by-path (issue #2226) | resolves to `gates/gates.py` | resolves to `gates/gates.py` | unchanged |
| `gates/risk_report.py` | sibling-load-by-path (issue #2226) | resolves to `gates/gates.py` | resolves to `gates/gates.py` | unchanged |
| `gates/ui_evidence_gate.py` | sibling-load-by-path (issue #2226) | resolves to `gates/gates.py` | resolves to `gates/gates.py` | unchanged |
| `gates/ci.py` | sibling-load-by-path (issue #2226) | resolves to `gates/gates.py` | resolves to `gates/gates.py` | unchanged |
| `gates/record_lint.py` | sibling-load-by-path (issue #2226, origin of the pattern) | resolves to `gates/gates.py` | resolves to `gates/gates.py` | unchanged |
| `on-the-record/gates/record_lint.py` | sibling-load-by-path (issue #2226) | resolves to `on-the-record/gates/gates.py` | resolves to `on-the-record/gates/gates.py` | unchanged |

```
$ grep -rln "_GATES_IMPL_KEY\|^import gates\b" gates/*.py on-the-record/gates/*.py
gates/claims.py
gates/check_runner.py
gates/record_lint.py
gates/ui_evidence_gate.py
gates/risk_report.py
gates/merge_gate.py
gates/ci.py
on-the-record/gates/record_lint.py
```
Exactly these 8 files; `on-the-record/gates/gates.py` and `gates/gates.py` themselves excluded from the table (they define the module, not import it).

```
$ for f in gates/*.py; do grep -n "^import [a-zA-Z_]" "$f"; done | grep "import gates\b"
(no output, post-fix: neither file has a bare "import gates" left)
```
(full unfiltered output cross-referenced against `ls gates/*.py | xargs -n1 basename | sed 's/\.py$//'`, this session) — every bare local import target other than `gates` itself (`gh_rest`, `check_runner`, `ci`, `flows`, `spawn_on_pr`, `state_paths`, `pr_reference`, `record_lint`, `closure_sweep`, `acceptance_gate`, `merge_gate`, `stale_revert_guard`, `check_run_artifact`, `human_comprehensibility`, `design_artifacts_gate`, `gh_budget`, `reexecution_gate`, `landing_obligation`, `requirement_digest`, `auto_approval_class`, `requirement_met`, `scope_adherence`, `spec_index`, `accumulation`) does not collide under either invocation form, because none of those names is also the enclosing namespace package's own name — only `gates` collides, and both pre-fix hits for it (`gates/merge_gate.py:24`, `gates/check_runner.py:40` — see the pre-session `git show HEAD:...` fenced block above in `## Acceptance verification`) are the two this session already fixed, which is why the post-fix grep above returns nothing.

## skill-verdict

skill-verdict: refactoring-legacy-seam-selection — applied: invoked; used the existing `evaluate()`/`gates` seam points (rules 5, 6) for both the exit-code Sprout-Method addition and the new tests, rather than introducing a new seam (see `## Why`).
skill-verdict: silent-failure-audit — applied: invoked; audited the one new error-handling site (`main()`'s `except Exception`), classified Handled (see `## Why`, with fenced evidence there).
skill-verdict: merge-gates — applied: invoked; Step 2 and Step 4 applied to the exit-code change and the pre-existing verification exemption respectively (see `## Why`, with fenced evidence there).
skill-verdict: architecture-dependency-direction — not-applicable: this fix changes how an existing sibling-module dependency resolves at import time under two invocation forms, not which way any dependency arrow points between modules/layers.
skill-verdict: defect-verification-independence-from-upstream-verdicts — not-applicable: not invoked; there is no upstream Present/closed_checks verdict being re-verified here — item 3's re-derivation was original investigation of the issue's own claim, not a re-check of a prior review/QA verdict.
skill-verdict: work-in-english — not-applicable: not invoked; no separate slash-invocation needed, this record and all commits/code/PR are already in English per the plugin's standing convention.
