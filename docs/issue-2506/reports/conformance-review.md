---
issue: 2506
role: conformance-review
author: conformance-review
loop_state: reported
type: review-record
code_under_review:
  - consult.py:366-441 (`_CONSULT_TRACE_REF`, rewritten `_commit_consult_trace()`)
  - spawn.py:2566-2632 (`checkout_staleness()`, new)
  - gates/merge_gate.py:283-301 (`evaluate()` checkout-staleness preflight)
  - 85f7b6f6:test/test_consult_trace_commit.py (new)
  - 85f7b6f6:test/test_checkout_staleness.py (new)
breaking: "none — this is a review record, no code changed by this role"
verdict: "pass — canonical: `python3 -m pytest test/test_consult_trace_commit.py test/test_checkout_staleness.py -q` (this session, worktree at bfd8beb4) — 12 passed; `python3 -m pytest test/ -q` (same worktree) — 15 failed, 308 passed, the 15 failures identical to the pre-session baseline"
upstream:
  - path: docs/issue-2506/reports/silent-failure-audit+diagnose-first-96b1bb2d.md
    sha: bfd8beb493f36ef90a404ad81f0c115329a0babc
subject: PR #2612 (branch issue-2506/silent-failure-audit+diagnose-first-96b1bb2d, HEAD bfd8beb493f36ef90a404ad81f0c115329a0babc)
test: issue #2506's own Acceptance section, https://github.com/tokenmaxxxer/on-the-record/issues/2506
result: passed
assertedBy: conformance-review session, issue-2506 (builder-blind; independently re-executed every test in a fresh worktree rather than trusting the implementation record's pasted output)
---

# issue-2506 — conformance-review record

Builder-blind conformance review of PR #2612 (branch
`issue-2506/silent-failure-audit+diagnose-first-96b1bb2d`, HEAD
`bfd8beb4`) against issue #2506's own Acceptance text, not against the
implementation session's self-report.

canonical: `git worktree add /tmp/otr-2506-review origin/issue-2506/silent-failure-audit+diagnose-first-96b1bb2d --detach` (this session), `git -C /tmp/otr-2506-review rev-parse HEAD` —
```
bfd8beb493f36ef90a404ad81f0c115329a0babc
```

skill-verdict: conformance-review-requirement-extraction — applied: invoked; used to split issue #2506's three `check:` bullets into checkable line items (bullet 1's body clause + its `must not` clause; bullet 2's body clause + its two independent `must not` clauses; bullet 3 as a single disclosure item; plus the issue's own empty-state clause) — see ## Requirement list below.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; every extracted requirement below already had an executable test in the PR, so each was routed to Test-method evidence (rule 4) except R3 (disclosure), which is a historical-recoverability claim routed to Analysis and independently re-derived rather than trusted from the record's citations.
skill-verdict: work-in-english — applied: invoked; this record and all commands run this session are in English; the final chat summary to the user is in Korean per the skill's routing rule.

## What was done

Reviewed PR #2612 (issue #2506's implementation) for conformance against
the issue's own Acceptance text: added a `git worktree` pinned to the
PR's actual head (`bfd8beb4`), read the changed code in `consult.py`,
`spawn.py`, and `gates/merge_gate.py` directly, and independently
re-executed every test the PR's test plan cites rather than trusting its
pasted output.

derived: `python3 -m pytest test/test_consult_trace_commit.py test/test_checkout_staleness.py -q` (this session, fresh worktree at `bfd8beb4`) —
```
12 passed
```
derived: `python3 -m pytest test/ -q` (same worktree) —
```
15 failed, 308 passed
```
The 15 failure names matched exactly (`test_convention_equivalence.py`, `test_local_dependency_env.py`, `test_spawn_cross_family_skill_selection.py`, `test_spawn_artifact_skill_pairing.py`, `test_spawn_skill_judge_haiku_timeout_overlap.py` cases) what the PR's own test plan reports as pre-existing/unrelated failures — no regression introduced by this PR's own two new test files or the three changed source files.

Also independently re-derived the R3 disclosure claim (see below) via `grep` over `gates/*.py` and a fresh `gh pr view 2493 --json comments,state,createdAt,mergedAt` call, rather than accepting the implementation record's citations as given.

## Requirement list

- R1a (functional-behavior): the consult path no longer commits to the orchestrator checkout's `main` in a way that makes it undivergeable — either traces are written without a commit, or committed somewhere that does not block `main` from fast-forwarding.
- R1b (edge-case, must-not on R1a): must not drop, thin, or make optional any consult trace — every consult, success or failure, still leaves exactly one trace line; traces already accumulated must not be discarded.
- R2a (functional-behavior): a gate invoked from a stale checkout refuses to produce a verdict, naming the staleness, rather than silently evaluating old code.
- R2b (edge-case, must-not on R2a): must not block a gate run in a checkout that is legitimately current.
- R2c (scope-boundary, must-not on R2a): must not auto-mutate the operator's working tree (fetch and compare is fine; reset/checkout is not).
- R3 (disclosure): the record states how many gate verdicts on 2026-08-26 were produced from the stale tree and are therefore suspect, or states plainly that the number could not be recovered and why.
- Empty-state clause (edge-case, applies to R2a): a fresh checkout with zero local commits — the staleness check is a no-op and gates run exactly as today.

## R1a — Present

canonical: `bfd8beb4:consult.py:96-131` (this session, worktree read) — `_commit_consult_trace()` builds each commit against `refs/heads/otr-consult-trace` through an isolated `GIT_INDEX_FILE`, then lands it with `git update-ref <ref> <new> <old>` (CAS). No `git commit` call targets the checked-out branch anywhere in the function.

derived: `python3 -m pytest test/test_consult_trace_commit.py -q` (this session, fresh worktree) —
```
5 passed
```
`test_main_head_never_moves_across_n_consults` is the bullet's literal demonstration: it runs 3 real consult-trace commits against a scratch origin+clone (not mocked), then asserts `git merge-base --is-ancestor origin/main main` returns 0 after all three. Independently re-ran it in a clean worktree rather than trusting the PR's pasted test-plan output — result matched.

## R1b — Present

derived: same `test/test_consult_trace_commit.py -q` run above. `test_trace_ref_accumulates_every_commit` confirms 3 consults produce 3 commits on `_CONSULT_TRACE_REF` (no trace silently dropped). `test_working_tree_files_survive_and_stay_untracked_on_main` confirms the on-disk trace file's byte content is untouched after the commit call.

canonical: `bfd8beb4:consult.py:347-360` (this session) — `_append_consult_trace()` (which writes the trace line to disk) runs unconditionally in every caller's `finally` block, *before* `_commit_consult_trace()` is invoked (e.g. `bfd8beb4:consult.py:581-583`). This ordering means a `_commit_consult_trace()` failure (exhausted CAS retries, a real git error) still leaves the trace line durably on disk — the failure path only prints a warning to stderr, per `_fail()`; it never removes or rewrites the already-written line. Confirms "no traceless consults" holds even on the new function's failure path, not only its success path.

`test_rev_parse_error_is_not_silently_read_as_missing_ref` additionally pins the silent-failure-audit fix: a real git error at the `rev-parse --verify` step is now surfaced (not misread as "ref doesn't exist yet").

## R2a — Present

canonical: `bfd8beb4:gates/merge_gate.py:283-301` (this session) — `evaluate()` calls `spawn.checkout_staleness()` first; on `checked and stale` it returns `{"allowed": False, "reasons": [<named reason>], "checkout_staleness": {...}}` before any of the check-runner/verification-record logic runs. The reason string names the staleness explicitly (`"checkout-stale (...): <behind-count and shas>"`), not a generic refusal.

derived: `python3 -m pytest test/test_checkout_staleness.py -q` (this session, fresh worktree) —
```
7 passed
```
`test_deliberately_stale_checkout_is_flagged_with_count` is the bullet's literal live demonstration: a checkout deliberately held one commit behind a scratch origin reports `checked: True, stale: True, behind: 1`, detail naming the count. `test_stale_checkout_short_circuits_to_a_named_refusal` confirms `merge_gate.evaluate()` itself refuses and never reaches `latest_check_runner_comment` when staleness is detected (asserted via `mock.assert_not_called()`).

derived: `grep -n "^ROOT" spawn.py` (this session) — `ROOT = Path(__file__).resolve().parent`, confirming `checkout_staleness()`'s default `root=spawn.ROOT` checks the orchestrator's *own* checkout (the code that is executing the gate), which is the distinct axis the issue names — separate from `evaluate()`'s own `root`/`repo` params, which address the target PR's repository. Independently traced this distinction rather than accepting the record's docstring claim at face value.

## R2b — Present

derived: same `test/test_checkout_staleness.py -q` run above. `test_current_checkout_is_not_stale` and `MergeGateRefusesOnStaleCheckoutTest.test_legitimately_current_checkout_is_not_blocked` both pin this must-not: a checkout at parity with origin is never flagged stale, and `merge_gate.evaluate()` proceeds to its normal (unrelated) refusal reason rather than the checkout-staleness one.

canonical: `bfd8beb4:test/test_checkout_staleness.py:396-428` (this session, `test_no_origin_remote_is_a_checked_false_no_op`) — a fresh checkout with no remote returns `checked: False, stale: False`, matching the issue's declared empty-state clause verbatim (a synthetic test repo with no `origin` is not mistaken for stale).

## R2c — Present

canonical: `bfd8beb4:spawn.py:291-358` (this session) — `checkout_staleness()`'s only git subcommands are `fetch`, `rev-parse`, `merge-base --is-ancestor`, and `rev-list --count`. No `reset`, `checkout`, `merge`, `commit`, or `push` call appears anywhere in the function.

derived: `test_staleness_check_never_mutates_the_working_tree` (part of the `test/test_checkout_staleness.py -q` run above) asserts `HEAD` and `git status --porcelain` are byte-identical before and after the check. Confirms the must-not mechanically, not just by reading the function body.

## Empty-state clause — Present

Covered by `test_no_origin_remote_is_a_checked_false_no_op` (cited under R2b above): `checked: False` is returned rather than either "stale" or "not stale," and `merge_gate.evaluate()` falls through to its pre-existing checks unchanged — "gates run exactly as today," per the issue's own wording.

## R3 — Present (disclosure honestly returns "unrecoverable," independently confirmed)

The implementation record's own answer is that the count cannot be recovered. Re-derived each supporting claim independently rather than accepting the record's citations as given:

derived: `grep -n "ledger_write\|ledger\." gates/merge_gate.py gates/verdict_gate.py gates/gates.py` (this session, this worktree) —
```
(no output, exit 1)
```
Neither gate persists a verdict to any ledger.

canonical: `bfd8beb4:watchdog.py:1280-1294` (this session, read directly, unmodified by this PR) — the `코드-신선도` check only compares current `HEAD` against the process's own `startup_head`; it has no origin-staleness branch and no persistence of past verdicts. Matches the record's quoted excerpt verbatim.

derived: `gh pr view 2493 --repo tokenmaxxxer/on-the-record --json comments,state,createdAt,mergedAt` (this session) — result: the PR's two GitHub comments (2026-08-26T02:53:21Z, 2026-08-26T03:12:28Z) record a `no_checks: True` / "no checks declared" refusal as the landing basis, not the `"필요한 검증 기록이 없다: ['execution-observation']"` refusal the issue's own prose quotes. Independently confirmed this discrepancy by reading the raw comment bodies myself — the record's disclosure claim (that the specific stale verdict never became a durable, `gh`-queryable artifact) holds.

Given no code path in this repository persists a merge-gate verdict keyed by date, and the one PR named as a concrete instance does not carry the specific stale verdict as a comment, "the number cannot be recovered" is the accurate answer, not an evasion. R3's own `must not: not applicable — disclosure bullet, adds no mechanism` confirms no code change was expected here.

## Open findings

- **Trace-path collision, raised in the issue's own 2026-08-27 comment thread but never formally folded into the Acceptance section, and not addressed by this PR.** derived: `gh issue view 2506 --repo tokenmaxxxer/on-the-record --comments` (this session) — result: a 2026-08-26 comment describes 4 add/add merge conflicts, all consult-log files, each side having independently written a *different* trace line to the *same* timestamp+pid path, and states "Any fix must make the trace path collision-free, not just non-diverging." `bfd8beb4:consult.py` touches only `_commit_consult_trace()` (the git-commit-target problem); it does not change `_consult_trace_path()`/`_CONSULT_SESSION_SHARD_ID` (the file-naming scheme), and the implementation record does not mention this comment at all. Resolution path: since this was never added as a literal `check:` bullet to the issue's Acceptance section (confirmed by `gh issue view 2506 --json body -q .body`, this session — only three `check:` bullets exist, none mentioning path collision), it is not a formal conformance defect against the text this review is scored against — but it is a live, evidenced risk the issue's author explicitly flagged as in-scope-adjacent, and it should be filed as its own follow-up issue rather than left to recur silently.
- **Scope limit, already disclosed by the implementation record, independently confirmed.** derived: `grep -rln "checkout_staleness" gates/` (this session) — result: only `gates/merge_gate.py`. `grep -n "merge_gate" gates/verdict_gate.py` (this session) confirms `verdict_gate.py` inherits the protection by calling `merge_gate.evaluate()`. Every other script under `gates/` (confirmed by `ls gates/*.py`, dozens of files) runs standalone and remains exposed to the same "stale checkout, confident wrong verdict" class. This matches the issue's concrete reproduction (`merge_gate.py` via PR #2493) exactly, so it is not a gap against R2a as written — recorded here only so it isn't mistaken for full coverage across `gates/`.

## What did not work

None — this session performed only review actions (read, `pytest`, `grep`, `gh`) against the existing worktree; no code or test file was modified.

## Why

Re-executed every test the implementation PR cites rather than trusting its pasted output, per builder-blind convention (`docs/issue-2381/reports/conformance-review.md` precedent): a fresh `git worktree` pinned to the PR's actual head, `pytest` run directly in that worktree, and every disclosure claim in R3 independently re-derived (grep, `gh pr view`) instead of accepted from the record's own citations. All three formal Acceptance bullets (R1/R2/R3) and both named must-not clauses under each verified Present. The one substantive gap found — the trace-path collision the issue's own comment thread flagged as "worth folding into the acceptance" — was never actually added to the Acceptance section as a `check:` bullet, so it is recorded as an open finding rather than scored as a failed requirement; scoring it as failed would silently expand the issue's own accepted text.

## Upstream basis

- `bfd8beb4:docs/issue-2506/reports/silent-failure-audit+diagnose-first-96b1bb2d.md` — the implementation record this review checks against.
- `bfd8beb4:consult.py`, `bfd8beb4:spawn.py`, `bfd8beb4:gates/merge_gate.py`, `85f7b6f6:test/test_consult_trace_commit.py`, `85f7b6f6:test/test_checkout_staleness.py` — the code under review, all pinned to the PR's own commits since none of these files/lines exist on this review branch's base tree.
- GitHub issue #2506 (body + 3 comments, read live this session via `gh issue view 2506 --comments`) — the requirement text and its own historical-incident evidence, both used as the review's ground truth.

## Next steps

None remaining — `loop_state: reported`. Verdict is terminal: **pass**. derived: `python3 -m pytest test/test_consult_trace_commit.py test/test_checkout_staleness.py -q` (this session) — result: 12 passed, covering every formal Acceptance bullet's literal demonstration; one open finding (trace-path collision) recorded above for a possible follow-up issue, not blocking this one since it was never added to the issue's own Acceptance section.
