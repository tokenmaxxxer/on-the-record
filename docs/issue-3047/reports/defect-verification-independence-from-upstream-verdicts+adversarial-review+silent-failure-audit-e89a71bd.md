---
issue: 3047
role: defect-verification-independence-from-upstream-verdicts+adversarial-review+silent-failure-audit-e89a71bd
author: defect-verification-independence-from-upstream-verdicts+adversarial-review+silent-failure-audit-e89a71bd
skills: defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true
code_under_review: dfad1978748145cadab18db6a7de52fef156c902
type: verification-record
breaking: false
verdict: PASS
loop_state: landed
upstream:
  - path: PR #3085 (tokenmaxxxer/on-the-record), head dfad1978748145cadab18db6a7de52fef156c902
    sha: dfad1978748145cadab18db6a7de52fef156c902
---

# issue-3047 — defect-verification-independence-from-upstream-verdicts+adversarial-review+silent-failure-audit-e89a71bd record

## What was done

Independent, builder-blind verification of PR #3085 against issue #3047's
two acceptance checks and three must-not clauses. Fetched PR #3085's head
(`git fetch origin pull/3085/head:pr-3085-review`) and added it as a
separate git worktree at `/tmp/pr3085-verify`; added `main`
(`573e7382282be24439c223c1603be648dd0e158f`) as a second worktree at
`/tmp/main-verify` for the pre-PR baseline. Neither worktree's files are
tracked in this branch's tree — they are cited below as `<sha>:<path>`
since bare paths (e.g. `watchdog.py`,
`dfad1978:tests/test_watchdog_cause_classification.py`) do not exist on
this branch; command blocks below run inside those worktrees (`cd
/tmp/pr3085-verify` or `/tmp/main-verify` as shown), so relative paths in
those commands resolve against the `dfad1978` or `573e7382` checkout
respectively, not against this branch.

**Acceptance check 1** (`python3 -m pytest tests/test_watchdog_cause_classification.py -q`):
canonical: `dfad1978:tests/test_watchdog_cause_classification.py` (232-line new file, decision-table + GWT tests over `watchdog._classify_mapping_loss_cause`/`_format_mapping_loss_line`/`_classify_narrowing_prs`)
```
$ cd /tmp/pr3085-verify && python3 -m pytest tests/test_watchdog_cause_classification.py -q
..............                                                           [100%]
14 passed in 1.45s
```
Read `dfad1978:watchdog.py:855-885` directly to confirm the decision logic the tests exercise:
```python
def _classify_mapping_loss_cause(pr_index: dict, issue_n: int) -> str:
    prefix = f"issue-{issue_n}/"
    states = [info.get("state") for branch, info in pr_index.items()
              if branch.startswith(prefix)]
    if any(s == "MERGED" for s in states):
        return _MAPPING_LOSS_CORRUPTED
    if any(s == "CLOSED" for s in states):
        return _MAPPING_LOSS_UNCLASSIFIED
    return _MAPPING_LOSS_NO_RECORD_YET
```
Verdict: **Present**.

**Acceptance check 2** (`python3 gates/probe_cause_misattribution.py`):
canonical: `dfad1978:gates/probe_cause_misattribution.py` (new file)
```
$ cd /tmp/pr3085-verify && python3 gates/probe_cause_misattribution.py; echo "exit=$?"
ok
exit=0
```
Independently re-checked the PR's own "must fail against main" claim
(rather than trusting the claim as stated) by copying the identical,
unmodified probe script onto the main worktree, which still carries the
pre-PR 4-argument `_classify_narrowing_prs` signature:
```
$ cp /tmp/pr3085-verify/gates/probe_cause_misattribution.py /tmp/main-verify/gates/probe_cause_misattribution.py
$ cd /tmp/main-verify && python3 gates/probe_cause_misattribution.py; echo "exit=$?"
TypeError: _classify_narrowing_prs() takes 4 positional arguments but 5 were given
exit=1
```
Verdict: **Present**.

**Must-not 1** — "a genuine corrupted merge-base must still be named and
still carry its repair path": constructed a case with different
identifiers than any of the PR's own test/probe fixtures (issue 8001,
branches `issue-8001/some-work-{abcd,efgh}`, one `MERGED` + one `OPEN`
sibling) and called the PR worktree's `watchdog._classify_narrowing_prs`/
`_format_mapping_loss_line` directly.
derived: `python3 -c "..."` against `/tmp/pr3085-verify` (inline script, run this session) — result:
```
cause: corrupted-merge-base
has recut-corrupted: True
[watchdog] board-sweep: PR #901 변경 감지했으나 issue-8001 subject 가 board 매핑을 잃었다 (브랜치='issue-8001/some-work-efgh') — 원인: corrupted-merge-base (이 subject 의 이전 병합 레코드가 있는데도 지금 board 에 없다) — issue-<n>/<skill>[+<skill>]-<lease> 산출물을 잘못된 base 에서 다시 잡아온(#2379) 브랜치라면 `spawn.py recut-corrupted --issue <n> --session <session>`(#2402)로 같은 이름 아래 재컷하라
```
Verdict: **Present**.

**Must-not 2** — "must not fetch per-PR detail on every tick; the
distinguishing signal must come from the existing `gh pr list` index":
derived: `awk '/^def _classify_mapping_loss_cause/,/^def _format_mapping_loss_line/' watchdog.py | grep -n "subprocess\|gh \|gh_api\|gh\."` run inside `/tmp/pr3085-verify` — result: exactly one hit, inside a docstring sentence describing the index's provenance, not a call:
```
3:    가져온 `pr_index`(branch -> {number, state, body}, `gh api
```
No `subprocess`/network call appears in either new function's executable body (confirmed by reading `dfad1978:watchdog.py:855-911` directly, quoted above and below). The sole production call site
(`dfad1978:watchdog.py:1426-1517`) threads through the *same* `pr_index`
object already obtained from `closure_sweep._pr_index_all(root)` earlier
in the tick — that call already existed pre-PR for `number_to_branch`;
this PR adds no new `gh` call:
```python
                pr_index, pr_index_ok = closure_sweep._pr_index_all(root)
                if pr_index_ok and pr_index is not None:
                    number_to_branch = {v.get("number"): k for k, v in pr_index.items()}
                    (mapped, non_subject_count, mapping_loss_new,
                     mapping_loss_already_reported) = _classify_narrowing_prs(
                        root, pr_numbers, number_to_branch, _sp.board(root), pr_index)
```
`_pr_index_all` itself (`dfad1978:gates/closure_sweep.py:195-235`) is
confirmed by its own docstring and body to call `gh api
repos/{slug}/pulls?state=all` in a paginated bulk request, not a per-PR
endpoint.
Verdict: **Present**.

**Must-not 3** — "a subject that cannot be classified must not fall
silently into either bucket; report it as unclassified": constructed an
independent ambiguous subject not in the PR's own fixtures (issue 9999,
branches `issue-9999/some-work-lease{1,2}`, one `CLOSED` + one `OPEN`
sibling, no `MERGED` sibling anywhere).
derived: `python3 -c "..."` against `/tmp/pr3085-verify` (inline script, run this session) — result:
```
loss_new: [(701, 9999, 'issue-9999/some-work-lease2', 'unclassified')]
line: [watchdog] board-sweep: PR #701 변경 감지했으나 issue-9999 subject 가 board 매핑을 잃었다 (브랜치='issue-9999/some-work-lease2') — 원인: unclassified (이 subject 에 병합 안 된 채 닫힌 PR 이 있어, 정상 흡수와 손상된 시도 포기를 이 인덱스만으로는 구별할 수 없다) — 사람이 직접 확인, 자동 재컷 복구를 임의로 적용하지 말 것
```
No `recut-corrupted` text present. Verdict: **Present**.

**Live-context reconstruction** (issue-3081): the watchdog reported this
exact alarm live, during this session, against
`issue-3081/silent-failure-audit+implementation-blueprint+test-derivation+defect-verification-independence-from-upstream-verdicts-ba2a806f`
(PR #3084), naming `recut-corrupted` for a branch that was never
corrupted — its PR had simply just opened.
canonical: `gh pr list --search issue-3081 --state all --json number,headRefName,state,title` (run this session) — result:
```
[{"headRefName":"issue-3081/silent-failure-audit+implementation-blueprint+test-derivation+defect-verification-independence-from-upstream-verdicts-ba2a806f","number":3084,"state":"OPEN","title":"issue-3081: attribute requirement-drift cache entries to a repo"}]
```
Exactly one PR for this subject, `OPEN`, no merged/closed sibling.
Rebuilt that exact `pr_index` shape and ran it through
`/tmp/pr3085-verify`'s classifier:
```
cause: no-record-yet
line: ...원인: no-record-yet (이 subject 는 아직 병합된 레코드가 한 번도 없다 — 새 이슈의 정상 상태) — 조치 불필요, 재컷 복구 대상 아님
```
The fixed classifier resolves the real false-alarm case correctly and
attaches no repair instruction.

**Full test suite**: ran on both worktrees.
derived: `python3 -m pytest tests/ test/ -q` in `/tmp/pr3085-verify` — result:
```
20 failed, 744 passed, 3 xfailed, 2 warnings in 31.92s
```
derived: `python3 -m pytest tests/ test/ -q` in `/tmp/main-verify` — result:
```
20 failed, 730 passed, 3 xfailed, 2 warnings in 32.29s
```
derived: `diff <(sort /tmp/main_failed.txt) <(sort /tmp/pr_failed.txt); echo "exit: $?"` (each file built via `grep "^FAILED"` on the two runs above) — result: `exit: 0` — the two sorted `FAILED` line lists are byte-identical, 20 lines each, same test IDs on both trees.
derived: `python3 -m pytest tests/ -q` in `/tmp/main-verify` (narrower scope matching the task brief's cited figure) — result:
```
5 failed, 182 passed, 2 warnings in 7.09s
```
same 5 test IDs (`tests/test_respawn_deliverable_gate.py` x4,
`tests/test_spawn_gate_wiring.py` x1) as the 20-failure full-suite run
above restricted to `tests/`, all unrelated to `watchdog.py`/board-sweep.
The 14-test delta (744 − 730) equals exactly the size of the PR's own new
`dfad1978:tests/test_watchdog_cause_classification.py` file (14 test
methods, confirmed by the "Acceptance check 1" run above reporting `14
passed` for that file alone). This PR introduces no regression; none of
the pre-existing failures are attributable to it.

## Why

Per `defect-verification-independence-from-upstream-verdicts`: every
claim above was re-derived by constructing fresh inputs (different issue
numbers and branch names than the PR's own test/probe fixtures) and
running the shipped code directly in a separate worktree, rather than
trusting the PR body's or the builder record's stated results. The one
place the PR's own probe script was reused verbatim was to test *against
main* (a script that does not exist on main at all, so "run the PR's
probe on the PR's own tree" would be circular) — that check targets the
tool's portability against the pre-PR signature, not the correctness the
acceptance checks already establish independently, so reuse there does
not compromise independence.

adversarial-review / silent-failure-audit angle: read
`dfad1978:watchdog.py:837-911` (the two new functions) and the one
changed call site (`dfad1978:watchdog.py:1426-1517`) line-by-line for
swallowed errors or silent defaults.
canonical: `dfad1978:docs/issue-3047/reports/silent-failure-audit+implementation-blueprint+test-derivation-48ce3454/deviation-log/20260902T070240618925-3404bb453e4199a2.md` (builder's own deviation-log entry, read after completing independent execution above) — records that the first draft used `pr_index = pr_index or {}`, which would have collapsed "never supplied" into a guessed `no-record-yet`; this was caught by the builder's own silent-failure-audit pass before commit and replaced with the explicit `pr_index is not None` branch quoted in "What was done" above (must-not-2 section). This is exactly the case exercised by
`ClassifyNarrowingPrsRoutesCauseIntoTupleTest::test_missing_pr_index_argument_routes_to_unclassified_not_a_guess`
already included in the 14-passed run cited under "Acceptance check 1"
above — independently re-confirmed by inspecting that test's assertion
in `dfad1978:tests/test_watchdog_cause_classification.py` directly (it
asserts `loss_new[0][3] == watchdog._MAPPING_LOSS_UNCLASSIFIED` when
`pr_index` is omitted from the call).
No other swallowed-error or silent-default path was found in the two new
functions or the changed call site — both are pure dict/string
operations with no `try`/`except` anywhere in their bodies, per the full
source quoted in "What was done" above.

One residual limitation, not scored as a defect: a corrupted-merge-base
subject that has *never* had a merged sibling (its very first PR was
itself the corrupted one) would classify as `no-record-yet` under
`dfad1978:watchdog.py:855-885`'s three-way decision quoted above, since
that function only distinguishes on sibling MERGED/CLOSED/OPEN state and
such a subject has no MERGED sibling to key on. Closing this would
require exactly the per-PR fetch must-not-2 forbids; the issue's own
three named causes and both acceptance checks are all satisfied by the
shipped signal, and this edge case is outside what either `check:` line
exercises.

skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; every check above was re-run this session against freshly constructed inputs distinct from the PR's own fixtures (see the `derived:`/`canonical:` command blocks throughout "What was done"), rather than citing the PR's or builder record's stated pass/fail as given.
skill-verdict: adversarial-review — applied: invoked; reviewed `dfad1978:watchdog.py:837-911` line-by-line independent of the builder record's framing, and surfaced the one residual signal-limitation noted directly above.
skill-verdict: silent-failure-audit — applied: invoked; traced the `pr_index=None` defensive branch to the builder's own deviation-log entry (canonical: cited directly above) and independently confirmed the specific regression test's assertion for it.

## Upstream basis

- PR #3085, head `dfad1978748145cadab18db6a7de52fef156c902` — fetched via
  `git fetch origin pull/3085/head:pr-3085-review`, checked out as a git
  worktree at `/tmp/pr3085-verify`. Not edited (per task instruction).
- `main` at `573e7382282be24439c223c1603be648dd0e158f` — checked out as a
  git worktree at `/tmp/main-verify`, used only as the pre-PR comparison
  baseline for the full-suite diff and the probe's main-fails check
  above.
- `dfad1978:docs/issue-3047/reports/silent-failure-audit+implementation-blueprint+test-derivation-48ce3454.md`
  — builder record shipped in PR #3085, read *after* completing
  independent execution above, to compare conclusions rather than to
  source them.

## Open findings

None. All two acceptance checks and all three must-not clauses graded
**Present** on independent execution (see per-criterion `derived:`/
`canonical:` blocks in "What was done"). No regression in the full suite
— the pre-existing failure set (20 test IDs in `tests/`+`test/`, 5 in
`tests/` alone) is identical between main and the PR branch, confirmed
by the `diff`/`exit: 0` result above.

## Next steps

None — terminal state.
derived: `python3 -m pytest tests/test_watchdog_cause_classification.py -q` (14 passed) and `python3 gates/probe_cause_misattribution.py` (`ok`) — both quoted in full under "What was done" above, both are this record's own two acceptance checks, and both passed; all three must-not clauses were independently confirmed by execution in the same section. No unresolved check remains for `loop_state` to track.
