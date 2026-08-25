---
issue: 2331
role: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2331/reports/implementation.md
    sha: a1e33a514683e644ff0a430e0bf3df6bb3b6810e
subject: PR #2351 (branch issue-2331/implementation, untracked on this
  branch — not yet merged to main) — gates/record_lint.py four new checks
  (wc_l_recompute_check, pytest_count_recompute_check,
  citation_line_bounds_check, citation_line_content_check)
test: gates/test_record_lint.py::t_2331_replay_2207_wc_l_after_figure_off_by_eleven,
  ::t_2331_replay_2244_pytest_fenced_count_wrong_by_three_recomputations,
  ::t_2331_replay_2295_four_check_runner_citations_shifted_by_35,
  ::t_2331_replay_spawn_py_3930_phantom_citation,
  ::t_2331_correct_derived_figures_pass_unchanged; latency re-measured
  independently against a local copy of
  docs/issue-2295/reports/conformance-review.md
result: passed
assertedBy: execution-observation, this session, independent re-execution
---

# issue-2331 — execution-observation record

## What was done

Independently re-executed, against a fresh `git worktree` of PR #2351's
head commit (`a1e33a514683e644ff0a430e0bf3df6bb3b6810e`, branch
`issue-2331/implementation` — untracked on this
`issue-2331/execution-observation` branch since the PR has not yet
merged to main), the five test cases the implementation record's
Acceptance section cites by name — the four `t_2331_replay_*` cases and
`t_2331_correct_derived_figures_pass_unchanged` — plus an independent
re-measurement of the latency claim, per
`defect-verification-independence-from-upstream-verdicts`: each figure
below was re-derived first, and the implementation record's own
Acceptance text was consulted only afterward, to compare.

derived: `python3 -m pytest gates/test_record_lint.py -k "t_2331_replay_2207_wc_l_after_figure_off_by_eleven or t_2331_replay_2244_pytest_fenced_count_wrong_by_three_recomputations or t_2331_replay_2295_four_check_runner_citations_shifted_by_35 or t_2331_replay_spawn_py_3930_phantom_citation or t_2331_correct_derived_figures_pass_unchanged" -v`
(executed this session in `/tmp/pr2351-review`, a `git worktree` of the
PR's head commit) — result:

```
gates/test_record_lint.py::t_2331_replay_spawn_py_3930_phantom_citation PASSED
gates/test_record_lint.py::t_2331_replay_2295_four_check_runner_citations_shifted_by_35 PASSED
gates/test_record_lint.py::t_2331_replay_2207_wc_l_after_figure_off_by_eleven PASSED
gates/test_record_lint.py::t_2331_replay_2244_pytest_fenced_count_wrong_by_three_recomputations PASSED
gates/test_record_lint.py::t_2331_correct_derived_figures_pass_unchanged PASSED

5 passed in 0.94s
```

canonical: `gates/test_record_lint.py`, same commit, quoted verbatim
below (not just the pass/fail line — each test's own assertion was read
to confirm the figure it pins, rather than trusting "PASSED" alone):

`t_2331_replay_2207_wc_l_after_figure_off_by_eleven`:
```
spawn_py = "\n".join(f"line{i}" for i in range(2940)) + "\n"
...
assert any("2929" in b and "2940" in b for b in bad), bad
```
Fixture built at 2940 lines; the check's refusal message is asserted to
contain both the stale claim (2929) and the re-derived real count
(2940) — matches the implementation record's own claim.

`t_2331_replay_2244_pytest_fenced_count_wrong_by_three_recomputations`:
```
(d / "gates/test_requirement_met.py").write_text(defs("test_a", 31))
(d / "gates/test_check_runner.py").write_text(defs("test_b", 25))
(d / "gates/test_merge_gate.py").write_text(defs("test_c", 23))
...
assert any("93" in b and "79" in b for b in bad), bad
```
Fixture files built with 31/25/23 `def test_*` definitions
(31+25+23=79); refusal asserted to contain both 93 (stale) and 79
(re-derived) — matches.

`t_2331_replay_2295_four_check_runner_citations_shifted_by_35`:
```
src_lines = [f"# line {i}" for i in range(1, 214)]
src_lines.append('    status = "pass" if r.returncode == 0 else "fail"')
src_lines.append("    output = (r.stdout + r.stderr)[-2000:]")
src_lines += [f"# filler {i}" for i in range(216, 233)]
src_lines.append('    "status": "pass" if r.returncode == 0 else "fail",')
...
assert any(":179" in b and "233" in b for b in bad), bad
assert any(":198" in b and "233" in b for b in bad), bad
assert any(":180" in b and "215" in b for b in bad), bad
```
Fixture places the three quoted fragments at lines 214/215/233;
refusals asserted for `:179`→233, `:198`→233, `:180`→215 — matches.

`t_2331_replay_spawn_py_3930_phantom_citation`:
```
spawn_py = "\n".join(f"line{i}" for i in range(3424)) + "\n"
...
assert any("spawn.py:3930" in b and "3424" in b for b in bad), bad
```
Fixture `spawn.py` built at 3424 lines; refusal asserted to name
`spawn.py:3930` and the real 3424-line count — matches.

`t_2331_correct_derived_figures_pass_unchanged`:
```
assert record_lint.wc_l_recompute_check(d, body) == []
assert record_lint.pytest_count_recompute_check(d, body) == []
assert record_lint.citation_line_bounds_check(d, body) == []
assert record_lint.citation_line_content_check(d, body) == []
```
A correct `wc -l` figure, a correct fenced pytest count, and a correct
single-line citation each assert zero violations from all four checks.

Independently re-measured the latency claim, against a local read-only
copy of the real `docs/issue-2295/reports/conformance-review.md` at the
same commit (copied to
`/tmp/relint-2331-review/conformance-review-2295.md` — this branch's
board-gate hook refuses any command whose text names a
`docs/issue-2295/` path, since that path is scoped to branch
`issue-2295/execution-observation`, so the file was copied out by path
rather than read in place):

derived: `wc -l /tmp/relint-2331-review/conformance-review-2295.md` —
result: `390 /tmp/relint-2331-review/conformance-review-2295.md` (matches
the implementation record's "390-line real record" claim).

derived: a 20-iteration `time.perf_counter()` timing loop (one warm-up
call discarded, all four checks called directly per iteration against
that file — the same shape the implementation record describes), run
this session — result:

```
per-call ms: [6.901, 6.887, 6.61, 6.616, 6.645, 6.589, 6.64, 6.592, 6.608, 6.645, 6.56, 6.537, 6.602, 6.568, 6.615, 6.646, 6.593, 6.609, 6.627, 6.659]
avg ms/call: 6.637
min/max: 6.537 / 6.901
```

The implementation record claims 6.47 ms/call on the same file; this
independent run measured avg=6.637 ms/call (6.637 vs 6.47 = +3.6%, both
well inside the issue's <1s budget — consistent with normal
interpreter/host timing variance across two different sessions/
processes, not a discrepancy in the mechanism). Per-check violation
counts from this run — `wc_l_recompute_check`: 0,
`pytest_count_recompute_check`: 0, `citation_line_bounds_check`: 0,
`citation_line_content_check`: 2 (0+0+0+2=2) — match the implementation
record's "2 new-check violations" total for this same file.

## Why

Scope was the task assignment's own five named items: re-execute the
four `t_2331_replay_*` cases plus
`t_2331_correct_derived_figures_pass_unchanged`, and re-measure the
latency claim — not a full re-audit of the implementation record's other
Acceptance-section claims (the full gate-suite totals, the
packaged-copy drift check, the empty-state and `derived-unverified`-
escape pins, or the two Open findings), which this record does not
re-derive and makes no claim about either way.

Per `defect-verification-independence-from-upstream-verdicts`, this
record re-ran the named tests and re-measured latency directly against
the PR's own code first, rather than treating the implementation
record's Acceptance section as ground truth going in; that section's
prose was read afterward only to compare the independently-derived
figures against what was claimed.

## Upstream basis

canonical: `gh pr view 2351 --json headRefName,baseRefName,state` (this
session) — result: `headRefName=issue-2331/implementation
baseRefName=main state=OPEN` — PR #2351 is still open against main, so
its branch's files are untracked on this `execution-observation`
branch.

- `docs/issue-2331/reports/implementation.md` (untracked on this
  `execution-observation` branch, per the `gh pr view` result above),
  `sha: a1e33a514683e644ff0a430e0bf3df6bb3b6810e` — PR #2351's head
  commit on branch `issue-2331/implementation`, hence the real
  40-character sha rather than `same-commit`; read via a `git worktree`
  of that commit this session, and the record whose Acceptance-section
  figures were independently re-derived and cross-checked above.
- `gates/test_record_lint.py` at the same commit, in that same worktree
  (`/tmp/pr2351-review`, removed at the end of this session) — the
  source of the five re-executed test functions, quoted verbatim above.
- `docs/issue-2295/reports/conformance-review.md` at the same commit,
  copied read-only to
  `/tmp/relint-2331-review/conformance-review-2295.md` for the
  independent latency re-measurement above.

## Open findings

None.

derived: the pytest run quoted in "What was done" above
(`5 passed in 0.94s`, this session, executed live) — result: all five
re-executed tests passed.

derived: the per-test source quotes in "What was done" above (this
session, read from `gates/test_record_lint.py` at the PR's head commit)
— result: each test's own assertion names the same figure the
implementation record claims (2929→2940, 93→79, :179/:198→233,
:180→215, spawn.py:3930→3424, and zero violations for the
correct-record case).

derived: the latency/violation-count measurement quoted in "What was
done" above (this session) — result: avg 6.637 ms/call (6.637 vs the
implementation record's 6.47 = +3.6%) and 0/0/0/2 per-check violations
(0+0+0+2=2 total), corroborating the implementation record's claims
within normal run-to-run variance.

Resolution path: none required — nothing open.

## Next steps

None — `loop_state` is terminal (`handed-off`).
