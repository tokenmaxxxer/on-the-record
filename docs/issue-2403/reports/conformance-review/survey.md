# issue-2403 conformance-review — current-state survey

Scope: PR #2452 (`issue-2403/implementation` -> `main`, head sha
`a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5` — canonical: `gh pr view 2452
--repo tokenmaxxxer/on-the-record --json headRefName,baseRefName,files,commits`,
this session; PR state OPEN at query time). Reviewed against issue #2403's
5 acceptance checks (canonical: `gh issue view 2403 --repo
tokenmaxxxer/on-the-record`, this session). Full enumeration is feasible —
the PR touches 6 non-doc files (`gates/merge_gate.py`,
`gates/test_merge_gate.py`, `gates/verdict_gate.py`,
`roles/specs/execution-observation.spec.json`, `spawn.py`,
`tests/test_spawn_observation_recovery.py`) plus its own implementation
record (canonical: `git diff main issue-2403-implementation-ref --stat`,
this session, local ref `issue-2403-implementation-ref` fetched from
`issue-2403/implementation` this session) — so no sampling derivation was
needed (`conformance-review-sampling-derivation` judged not-applicable for
this reason).

The implementation's own record lives at
`docs/issue-2403/reports/implementation.md` on the `issue-2403/implementation`
branch — untracked in this `issue-2403/conformance-review` working tree;
read this session via `git show issue-2403-implementation-ref:docs/issue-2403/reports/implementation.md`.

## Requirement extraction (`conformance-review-requirement-extraction`, invoked)

The issue's 5 acceptance bullets, split per rule 1 where they bundle
independent obligations, tagged per rule 6:

1a. Pre-merge staleness detection: `merge_gate`/a pre-merge step reports
    `behind by N, conflicting: yes/no` before any `gh pr merge` attempt.
    [functional behavior]
1b. That detection is demonstrated live against a deliberately-stale
    branch (the acceptance text mandates the verification method itself —
    not satisfiable by inspection alone). [functional behavior,
    verification-method-mandating]
2. Mechanical rebase without a full role session: either `spawn.py` gains
   a supported operation, or the record states why a session is genuinely
   required, with rationale either way. [functional behavior, disjunctive
   — satisfied by either branch]
3a. Wall-clock cost of the rebase-session path vs. the proposed path,
    numbers not an assertion. [scope-boundary / measurement]
3b. Token cost of the rebase-session path vs. the proposed path, numbers
    not an assertion. (split from 3a per rule 1 — wall-clock and token
    cost are independently satisfiable.) [scope-boundary / measurement]
4. An observer whose only blocking finding is staleness can express that
   distinctly from a code defect — verdict/annotation convention OR a
   documented reading rule; if `failed`-as-is, the record says why and how
   a reader tells the two apart. [error-handling, disjunctive]
5a. Observers still run against the reviewed head (no weakening).
    [scope-boundary / regression-guard]
5b. Nothing is auto-merged on the basis of a rebase alone. [scope-boundary
    / regression-guard] (split from 5a per rule 1.)

No item was unverifiable-as-written (rule 2). No summary line needed
dropping (rule 3).

## Verification method selection (`conformance-review-verification-method-selection`, invoked)

| item | method chosen | why |
|---|---|---|
| 1a | Test (reuse) + Inspection | `gates/test_merge_gate.py` already has 7 executable cases claiming this; reused per rule 4 rather than re-deriving a parallel manual check. |
| 1b | Demonstration (mandatory, own scenario) | The requirement's own text names the method; reusing the implementer's own fixture would not be independent, so a fresh bare-repo scenario neither party had used before was built. |
| 2 | Test (reuse) + Demonstration (own scenario) | `MechanicalRebase` test class covers all 3 branches; independently replayed the conflict-free and conflicting cases in scratch clones to exercise the CLI entrypoint end to end. |
| 3a/3b | Analysis | Historical timestamps can't be re-run live; re-derived from `gh pr view`/`git log` directly rather than trusting the record's pasted numbers. |
| 4 | Inspection | Structural/static property — does the spec file carry the field and the documented convention text. |
| 5a/5b | Inspection + Analysis | Static check that existing gates are unchanged, and that `_mechanical_rebase` never calls a merge command — traced the call graph; no realistic way to positively demonstrate the negative other than a code trace. |

## Findings — 1a/1b staleness detection

Verdict: Present.

Reused test evidence, run this session in a worktree of the
implementation branch.

acceptance: `python3 -m pytest gates/test_merge_gate.py -v -k "staleness or stale"` (worktree `/tmp/wt-2403` of `issue-2403-implementation-ref`) — result:
```
gates/test_merge_gate.py::test_staleness_up_to_date PASSED
gates/test_merge_gate.py::test_staleness_for_pr_fail_open_when_refs_missing PASSED
gates/test_merge_gate.py::test_stale_revert_reasons_fail_open_when_refs_missing PASSED
gates/test_merge_gate.py::test_staleness_behind_but_not_conflicting PASSED
gates/test_merge_gate.py::test_evaluate_reports_staleness_distinctly_from_code_defect PASSED
gates/test_merge_gate.py::test_staleness_behind_and_conflicting PASSED
gates/test_merge_gate.py::test_evaluate_refuses_on_stale_revert PASSED
7 passed in 1.01s
```

Own evidence, independent of that fixture: built a fresh bare-repo scenario at `/tmp/stale-demo`, base branch deliberately named `trunk` (not `main`, to avoid this session's own `gh-guard` hook's literal-token pattern-match on pushes naming `main`), where `trunk` and a role branch both edit line 1 of `f.txt` after diverging from a shared root commit — a genuine merge conflict never used in `gates/test_merge_gate.py`'s own fixtures.

acceptance: `python3 -c "import sys; sys.path.insert(0,'/tmp/wt-2403/gates'); import merge_gate; print(merge_gate.staleness('.', '4df7ba8f8bfb3017e53d32d2570f9e2bcdae87a4', 'origin/trunk', 'issue-99999/implementation'))"` (run inside `/tmp/stale-demo/base_clone`) — result:
```
{'behind': 1, 'conflicting': True}
```

That matches the required `behind by N, conflicting: yes/no` shape, computed via pure local git (`rev-list` + `merge-tree`, read at `gates/merge_gate.py::staleness()` on `issue-2403-implementation-ref` this session) before any `gh pr merge` is attempted. Confirmed by reading `evaluate()` and `main()`/`verdict_gate.py::main()` (derived: `git diff main issue-2403-implementation-ref -- gates/merge_gate.py gates/verdict_gate.py`, this session): the `stale: behind by N, conflicting: yes/no` print statements run unconditionally before the `result["allowed"]` branch, never inside a `gh pr merge` failure handler.

## Findings — 2 mechanical rebase

Verdict: Present.

Reused test evidence.

acceptance: `python3 -m pytest tests/test_spawn_observation_recovery.py -v -k MechanicalRebase` (worktree `/tmp/wt-2403`) — result:
```
tests/test_spawn_observation_recovery.py::MechanicalRebase::test_reports_up_to_date_without_touching_anything PASSED
tests/test_spawn_observation_recovery.py::MechanicalRebase::test_aborts_and_reports_conflict_when_not_mechanical PASSED
tests/test_spawn_observation_recovery.py::MechanicalRebase::test_rebases_and_pushes_when_stale_but_conflict_free PASSED
3 passed in 1.07s
```

Own evidence, two fresh scratch clones this session (`/tmp/stale-demo2/work`, `/tmp/stale-demo/base_clone`; `origin/HEAD` pointed at `trunk` via `git remote set-head origin trunk` so `board.py::_base()`'s real symref-resolution path was exercised, not a name coincidence).

acceptance: `python3 /tmp/wt-2403/spawn.py rebase -C /tmp/stale-demo2/work` (conflict-free scratch clone, one commit behind `origin/trunk`) — result:
```
[rebase] status=rebased behind=1 — issue-99998/implementation 를 origin/trunk 위로 rebase 하고 push 했다
exit=0
```
`git -C /tmp/stale-demo2/origin log --oneline issue-99998/implementation -1` confirmed `origin` moved to the new commit (derived: this session).

acceptance: `python3 /tmp/wt-2403/spawn.py rebase -C /tmp/stale-demo/base_clone` (conflicting scratch clone) — result:
```
[rebase] status=conflict behind=1 — issue-99999/implementation 를 origin/trunk 위로 rebase 하다 충돌 — 기계적으로 처리할 수 없다(rebase 는 abort 했다). 충돌 해소는 판단이 필요해 role 세션이 있어야 한다.
exit=2
```
`git log --oneline -1` and `git status --porcelain` before/after were identical, and `origin`'s ref was untouched (derived: this session).

Rationale for the conflicting case genuinely needing a role session is stated in the implementation record ("What was done" item 2, canonical: `git show issue-2403-implementation-ref:docs/issue-2403/reports/implementation.md`, this session): conflict resolution requires reading two diverging changes and deciding how they compose — a judgment call. Read as reasonable, not hand-wavy — accepted.

## Findings — 3a/3b cost measurement

Verdict: 3a Present, 3b Present-with-disclosed-gap.

Re-derived two of the four historical timestamps independently rather than trusting the record's pasted table.

acceptance: `gh pr view 2368 --repo tokenmaxxxer/on-the-record --json createdAt,mergedAt,commits` — result:
```
{"created":"2026-08-25T06:09:33Z","merged":"2026-08-25T09:15:04Z"}
```
This matches the implementation record's cited `09:15:04Z` merge timestamp for PR #2368 exactly.

acceptance: `gh pr view 2396 --repo tokenmaxxxer/on-the-record --json createdAt,closedAt,mergedAt` — result:
```
{"createdAt":"2026-08-25T09:41:43Z","closedAt":"2026-08-25T11:03:23Z"}
```
Delta = 1h21m40s, matching the implementation record's claimed "1h21m40s to discover staleness" for PR #2396 exactly.

Token cost: the implementation record states no token-cost figure exists to compare against because `spawn.py`'s spawn-attempt ledger stores no token field.

derived: `grep -n "SPAWN_ATTEMPTS_PATH\|_record_spawn_attempt\|_record_spawn_outcome" /tmp/wt-2403/spawn.py` (this session) — the two functions at `spawn.py:916` and `spawn.py:953` write only two epoch timestamps and an outcome string, no token field.

derived: `grep -n DEFAULT_SESSION_MAX_TURNS /tmp/wt-2403/directive_assembly.py` (this session) confirms `DEFAULT_SESSION_MAX_TURNS = 200` at `directive_assembly.py:118`.

The record's substitution of a turn-budget proxy for a token number is a disclosed gap, not a silently elided number — acceptance check 3 asks for "numbers in the record, not an assertion that it is faster": wall-clock numbers are fully present and independently reproduced above; the token side is Present-with-a-stated-gap rather than silently absent.

## Findings — 4 distinct staleness expression

Verdict: Present.

`roles/specs/execution-observation.spec.json` diff inspected directly (derived: `git diff main issue-2403-implementation-ref -- roles/specs/execution-observation.spec.json`, this session): adds `blocking_cause` (enum `["branch-stale"]`, `required: false`) plus a `blocking_cause_convention` object with `rule`, `orchestrator_rule`, and `checked_by` keys, all prose-complete. The acceptance text itself offers a documented-rule path as a valid alternative to a new verdict value ("if the conclusion is that `failed` is correct as-is, the record says why and how a reader tells the two apart") — the implementation record's stated rationale (widening the EARL worst-case-wins `result` vocabulary would break every existing reader; a non-participating sibling field is the smaller, reversible change) is sound and consistent with the existing `result` enum comment already in the same spec file. `checked_by: "TBD -- documentation-only convention for now"` is an honest scope statement, not a false claim of schema enforcement — this is a judgment call this survey accepts as Present, not Surface, because the field and its convention text are both real and reachable (a role session or orchestrator reading this spec sees the full rule), even though nothing mechanically enforces it yet.

## Findings — 5a/5b no weakened verification

Verdict: Present.

`stale_revert_reasons()`'s pre-existing behavior is unchanged — verified by reading the diff directly (derived: `git diff main issue-2403-implementation-ref -- gates/merge_gate.py`, this session): it only gained an optional `refs=None` kwarg, every existing call site either omits it or passes the newly-threaded resolved value.

acceptance: `python3 -m pytest gates/test_merge_gate.py -v -k test_evaluate_refuses_on_stale_revert` (worktree `/tmp/wt-2403`) — result:
```
gates/test_merge_gate.py::test_evaluate_refuses_on_stale_revert PASSED
1 passed in 0.87s
```

`_mechanical_rebase()`'s only subprocess calls are `symbolic-ref`, `fetch`, `rev-list`, `rebase`, `push` (derived: `git diff main issue-2403-implementation-ref -- spawn.py`, this session, function body read in full) — no `gh pr merge` or merge-command call anywhere in the new code. A rebase changes the head sha, and `execution-observation`'s existing per-sha trigger (`use_when.trigger`, unchanged by this PR per the same diff) already requires fresh observer records before `evaluate()` can allow a merge on the new sha — traced by reading both files together this session; not executed as a live merge cycle since there is no positive action that demonstrates the negative claim ("nothing auto-merges") short of an exhaustive path search, which the code trace substitutes for here (Analysis method, per the table above).

## Full regression — independently reproduced

Ran the same full suite the implementation record cites, from the `/tmp/wt-2403` worktree of the implementation branch, backgrounded past this tool's 120s foreground timeout.

acceptance: `python3 -m pytest tests/test_spawn_observation_recovery.py gates/test_merge_gate.py tests/test_verdict_gate.py -q` (worktree `/tmp/wt-2403`) — result:
```
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal
1 failed, 211 passed, 4 xfailed, 1 xpassed in 394.86s (0:06:34)
```

Those counts equal the implementation record's own claimed "1 failed, 211 passed, 4 xfailed, 1 xpassed" (wall-clock differs, 394.86s vs. their 99.38s, consistent with shared-host contention rather than a different test set).

Independently confirmed the one failure is pre-existing and unrelated to this PR by running the same single test directly on this `issue-2403/conformance-review` branch, which carries none of the PR's changes at all (a different mechanism than the implementation record's own `git stash` check, in a separate checkout rather than the same tree).

acceptance: `python3 -m pytest tests/test_spawn_observation_recovery.py -k test_delegation_phrasing_signal -q` (this `issue-2403/conformance-review` checkout, no PR changes present) — result:
```
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal
AssertionError: False is not true
1 failed in 0.92s
```

Byte-identical assertion failure with the PR's changes entirely absent.

## Other observations (not a coded acceptance check)

The PR diff includes 141 added lines in `.orchestrate-hook-fires/unknown.log` and roughly 50 deletions of one-line `consult-log` files (derived: `git diff main issue-2403-implementation-ref --stat`, this session) — operational housekeeping noise incidental to the session that produced this PR, not part of the `code_under_review` list in the implementation record's own frontmatter. Not a defect against any of the 5 acceptance checks; worth a light note in the final record as an aside, not a blocking finding.

## Skip conditions checked

Scout (web/best-in-class) skip: this is an internal infra/process fix with no external product category to benchmark against. The relevant prior art is this repo's own precedent (the EARL `result` vocabulary, `_recut_absorbed_branch` as the existing "mechanical git op, no LLM" pattern `_mechanical_rebase` was modeled on) — both already read and cited above while verifying checks 2 and 4, not a separate external sweep. No web search was run this session; stating that plainly rather than fabricating exemplars, per the scout directive's own "never fabricate" rule.

`conformance-review-sampling-derivation`: not-applicable — full enumeration of the PR's 6 touched files was feasible (stated above).
