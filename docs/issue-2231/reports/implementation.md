---
issue: 2231
role: implementation
loop_state: landed
upstream:
  - path: docs/issue-2233/reports/implementation.md
    sha: same-commit
code_under_review:
  - gates/requirement_met.py
  - gates/check_runner.py
  - gates/test_requirement_met.py
  - gates/test_check_runner.py
type: fix
breaking: none
verdict: pass
---

# issue-2231 — implementation record

## What was done

`gates/requirement_met.py` and `gates/check_runner.py`, per the issue's
three asks plus the two residual gaps its closing comment on #2233
pointed at.

1. Parser reach (defect 1). `requirement_met.py` used to grade only
   `- check:`/`- gate:` bullets (`check_runner.parse_checks`, unchanged).
   Added `_parse_acceptance_items(section)`, which additionally pulls in
   every top-level prose bullet (`- ...` with no `check:`/`gate:`/
   `unverifiable:` label) and every top-level (unindented) bare
   `empty state:`/`provenance:` line, matching ACCEPTANCE FORMAT's own
   convention that the check:/empty state:/provenance: structure is only
   mandatory for criteria that reference an executable artifact — prose
   criteria were always valid, just never reached. `unverifiable:` stays
   excluded (issue #310's explicit "no gradable criteria" escape, not a
   criterion itself) so `t_empty_state_no_check_bullets_is_distinct_result`
   keeps its existing meaning.
2. Distinct empty-state outcome (defect 2). `check()` now carries an
   `empty_state: bool` key through both branches (previously dropped on
   the empty path); `main()` prints two different messages instead of
   the old single "게이트 통과 (또는 채점 가능한 기준 없음)" that read as
   approval either way.
3. Citation-format false-block (defect 3). The deterministic
   artifact-presence sub-check's prose-file exception only recognized one
   citation shape (`acceptance: <cmd> — result: <verdict word>`). PR
   #2223's actual record cited its evidence via a `canonical: <cmd>` tag
   instead (the shape `gates/record_lint.py`'s own `_CANONICAL_TAG`
   already treats as a citation elsewhere in this codebase) — a
   byte-for-byte correct YES verdict would have been refused for that
   format mismatch alone. Added `_CANONICAL_CITATION` as a second
   recognized shape; a bare untagged prose mention of the artifact still
   does not count (unchanged, still refused — pinned by
   `t_bare_prose_mention_still_not_evidence_even_with_canonical_fix`).
   Non-goal preserved: only `structural` (check:/gate:-labeled) items are
   subject to this sub-check at all — a new prose/bare-label item graded
   YES with no cited artifact never gets refused, since ACCEPTANCE FORMAT
   never asked it to cite one. Refusing those would have turned "grade
   more" into "block more than the format ever required."
4. Residual gap (a) — an all-judgment section used to abort the whole
   run before anything executed or any PR comment posted (PRs
   #2228/#2218). `run_checks` itself is unchanged (a judgment item
   handed to it directly still raises `JudgmentCheckError` —
   `merge_gate.verify_artifact` and the existing unit tests rely on
   that). Instead, `check_runner.main()` now splits `parse_checks`'
   output into `mechanical`/`judgment` before calling `run_checks`, so a
   judgment item never reaches it. Mechanical checks still run and post a
   graded comment; judgment items are listed underneath as
   out-of-scope-for-this-runner (graded instead by
   `requirement_met.py`'s semantic layer) and are excluded from the
   numeric header's numerator and denominator. An Acceptance section that
   is entirely judgment-shaped reuses the existing `NO_CHECKS_MARKER`
   empty-state path (still not treated as satisfied) but now names which
   items were judgment-only instead of claiming there were no
   `check:`/`gate:` lines at all.
5. Residual gap (b) — a comparative/quantitative measurement criterion
   whose backtick names a script incidentally (issue #2210's Acceptance:
   > an 8KB heredoc write through the real `pretooluse-dispatcher.sh`
   > completes in a time comparable to a 1KB one — measured, with both
   > numbers in the record
   was mechanically read as "does this file exist", which the real path
   layout does not satisfy — a substance-unrelated refusal on PR #2222.
   Added a narrow `_MEASUREMENT_LANGUAGE` regex (word list below); when
   it matches alongside a backtick that doesn't already look like an
   executable command, the check now classifies as `judgment` instead of
   `file-existence` — reachable by requirement_met.py's prose grading
   (point 1) rather than a wrong mechanical verdict.
   ```
   _MEASUREMENT_LANGUAGE alternatives: measure/measured/measuring,
   comparable to, completes in a time, regression guard, unchanged on,
   latency, throughput, duration, benchmark(ed), median, percentile
   ```

## Why

The gate's whole purpose (#1651) is to be the merge pipeline's last line
of defence against a PR that doesn't meet its issue's frozen criteria.
Grading only a small fraction of a section's items and printing the same
approval-shaped line either way made an unexamined PR read as approved —
the same quiet-success failure class as #2214's analyzer reporting a
missing file as a clean session. The two residual gaps compound the
failure differently: an all-judgment section produced zero PR feedback at
all (worse than a wrong grade — no grade), and a mismatched measurement
criterion produced a confidently wrong refusal on a correct PR. Fixing
only the parser without also fixing these two would have left the gate
still silently blind on two of the three shapes its own closing comment
on #2233 named as live-observed.

## What did not work

None.

## Upstream basis

- docs/issue-2233/reports/implementation.md (closing GitHub comment,
  2026-08-24T23:04:35Z) — named residual gaps (a)/(b), scoped to this
  issue.
- Issue #2231 body — the three defects, and the two live repro pairs
  (#2215/#2223, #2208/#2218) re-run below.
- `on-the-record/directive/acceptance-format.md` — the convention the
  parser now agrees with (check:/empty state:/provenance: structure is
  mandatory only when a criterion references an executable artifact).

## Open findings

None.

other mounted skills: not triggered — this is a narrow bug-fix to two
existing single-module gate scripts (parser/classification logic), not a
multi-module structure decision, a GoF-pattern call, a coupling/cohesion
threshold, or a data-structure/perf tradeoff, so none of the mounted
implementation-* skills' trigger conditions applied; no Skill tool calls
were made this session.

## Next steps

None — loop_state is terminal (`landed`).

## Acceptance evidence (executed-live)

Re-running the issue's own two named pairs, after the change:

```
$ python3 gates/requirement_met.py 2215 2223
advisory: [UNKNOWN] `tests/test_workspace_checkpoint.py`
advisory: [UNKNOWN] Kill a role session mid-edit with uncommitted changes; the edits are recoverable from the checkpoint ref afterward. Show the recovery commands and their real output.
advisory: [UNKNOWN] Checkpointing leaves the session's branch, HEAD, and index unchanged — demonstrate with `git status` / `git rev-parse HEAD` before and after a checkpoint fires.
advisory: [UNKNOWN] Untracked files are captured, not just tracked modifications.
advisory: [UNKNOWN] The health line for a live session reports dirty-file count and minutes-since-checkpoint; show it against a session with real dirty state.
advisory: [UNKNOWN] Checkpoint refs are cleaned up at session end and do not leak into pushes or PRs.
advisory: [UNKNOWN] a workspace with a clean tree and no edits yet — the health line must report 0 dirty files and no checkpoint, without creating an empty checkpoint ref.
advisory: [UNKNOWN] executed-live — the kill-mid-edit recovery and the before/after `git status` / `git rev-parse HEAD` comparison must be performed against a real spawned workspace and the real terminal output pasted into the report.
게이트 통과 (8개 기준 채점, 차단 사유 없음)
```
`derived: advisory-line count in the pytest -c run above, 2026-08-25` —
every advisory line above is a separate graded item; before this change
this issue's gate output carried exactly one advisory line.

```
$ python3 gates/requirement_met.py 2208 2218
advisory: [UNKNOWN] the judge's historical abstention rate is reported as a number with the query that produced it, recorded in the implementation record
advisory: [UNKNOWN] `tests/test_retrieval_eval.py` passes with negative clauses stripped from the BM25 field, and the record states whether stripping changed either frozen negative case's outcome
advisory: [UNKNOWN] `work-in-english` is bound statically for the roles that need it and no longer appears in retrieval candidates — verified by re-running the retrieval pipeline against its frozen negative case
advisory: [UNKNOWN] The positives gold set does not regress (regression guard)
advisory: [UNKNOWN] Executed acceptance evidence in the record (#2137)
advisory: [UNKNOWN] a task where no skill applies must remain representable and must score correct when nothing is mounted — the property #2205 established and this issue must not break.
advisory: [UNKNOWN] executed-live — canonical: the abstention query over logged selections, plus `tests/test_retrieval_eval.py` runs before and after each of the two changes.
게이트 통과 (7개 기준 채점, 차단 사유 없음)
```
`derived: advisory-line count in the pytest -c run above, 2026-08-25` —
every advisory line above is a separate graded item; before this change
this issue's gate output carried exactly three advisory lines, all
UNKNOWN.

A constructed PR that genuinely fails a criterion still gets refused
(synthetic body/diff pair standing in for a PR that claims a check
succeeded without ever touching the named path — #2215/#2223 itself has
no real failing criterion to point at, so a real, already-tracked repo
path — `gates/merge_gate.py` — stands in as the named artifact, kept out
of the synthetic diff on purpose):

```
$ python3 -c '
import sys; sys.path.insert(0, "gates")
import requirement_met as rm
body = "## Acceptance\ngate: `gates/merge_gate.py`\n"
diff = "diff --git a/unrelated.py b/unrelated.py\n--- a/unrelated.py\n+++ b/unrelated.py\n+pass\n"
g = rm.grade(body, diff, {"`gates/merge_gate.py`": rm.YES})
print("blocked:", g["blocked"])
for r in g["blocking_reasons"]: print(" -", r)
'
blocked: True
 - 기준 '`gates/merge_gate.py`'이 YES 로 채점됐지만 인용된 아티팩트 'gates/merge_gate.py'이 PR diff 에 없다
```

Citation-format false-block fix, exercised against the real PR #2223
with the builder-blind session's actual YES verdict forced in:

```
$ python3 -c '
import sys; sys.path.insert(0, "gates")
import requirement_met as rm; from pathlib import Path
result = rm.check(Path("."), 2215, 2223, {"`tests/test_workspace_checkpoint.py`": rm.YES})
print("blocked:", result["blocked"])
'
blocked: False
```

Full gate suite, otherwise untouched by this change, run clean:

```
$ python3 -m pytest gates/ -q --ignore=gates/test_gates.py
941 passed, 8 xfailed in 145.29s (0:02:25)
```

Targeted suites for the two changed modules:

```
$ python3 -m pytest gates/test_requirement_met.py gates/test_check_runner.py gates/test_merge_gate.py -q
93 passed in 41.73s
```
