---
issue: 2215
role: conformance-review
loop_state: reported
upstream:
  - path: issue #2215 (GitHub, canonical: gh issue view 2215)
    sha: same-commit
  - path: PR #2223 (branch issue-2215/implementation, GitHub)
    sha: a025f27d2a8be32774695405284cf4bdda21543f
subject: PR #2223 ("issue-2215: harness-decided workspace checkpointing + dirty-tree health signal") graded against issue #2215's frozen `## Acceptance` section
test: gates/requirement_met.py 2215 2223 (deterministic artifact-presence sub-check); independent live re-execution of the kill-mid-edit recovery and before/after HEAD/branch/index demonstrations in a throwaway /tmp fixture using checkpoint.py fetched verbatim from the PR's head commit; pytest tests/test_workspace_checkpoint.py -v re-run from a git worktree checked out at the PR's head commit
result: passed
assertedBy: builder-blind conformance-review session (branch issue-2215/conformance-review) — no access to PR #2223's builder session or its rationale; verdicts below rest on the issue body, the PR diff, and code/tests read from the PR's own head commit
---

# issue-2215 — conformance-review record

## What was done

Builder-blind grading of PR #2223 against issue #2215's frozen `## Acceptance` section, per issue #1651's requirement-met contract.
canonical: gh issue view 2215
canonical: gh pr diff 2223

issue #2215's Acceptance section is five prose bullets plus one trailing gate:/empty state:/provenance: block. gates/check_runner.py's parse_checks() only recognizes lines literally prefixed check:/gate: (its `_CHECK_LINE` regex), so only the trailing gate: line is machine-parseable — the five prose bullets are hand-graded below (conformance-review-requirement-extraction rules 1 and 6: one obligation per line, each dimension-tagged). Full enumeration of all eight checkable items was feasible without sampling.

canonical: python3 gates/requirement_met.py 2215 2223
```
advisory: [UNKNOWN] tests/test_workspace_checkpoint.py
게이트 통과 (또는 채점 가능한 기준 없음)
```
(this transcription of the CLI's advisory line omits the tool's own decorative backticks around the artifact name — that path lives only on the PR branch, not this grading branch, and this record's own path-reference lint treats a backtick-wrapped tests/... path as a reachability claim; the artifact name and verdict are otherwise reproduced exactly.)

The CLI supplies no per-criterion verdict, so the one parseable criterion defaults to UNKNOWN. Feeding `grade()` a YES verdict for that criterion directly, against the real issue body and PR diff:
canonical: python3 -c "import sys; sys.path.insert(0,'gates'); import requirement_met as rm; ..." (grade() call, this session)
```
{"raw": "tests/test_workspace_checkpoint.py", "verdict": "YES", "artifact_in_diff": false, "blocking_fail": true}
blocking_reasons: ["기준 'tests/test_workspace_checkpoint.py'이 YES 로 채점됐지만 인용된 아티팩트 'tests/test_workspace_checkpoint.py'이 PR diff 에 없다"]
```
This blocking behavior and its cause are explained in Open findings item 2 below.

Per-criterion findings (functional-behavior dimension unless noted; verdict set per conformance-review-verdict-assignment: Present/Surface/Absent/Incorrect/Unverifiable, mapped to the gate's own YES/NO/UNKNOWN vocabulary in parentheses):

---
requirement: "Kill a role session mid-edit with uncommitted changes; the edits are recoverable from the checkpoint ref afterward. Show the recovery commands and their real output."
spec_ref: issue #2215 `## Acceptance`, bullet 1
verdict: Present (YES)
method: Demonstration — independently executed this session, in a throwaway /tmp fixture unrelated to the builder's own record, using checkpoint.py fetched verbatim from the PR head via `gh api repos/tokenmaxxxer/on-the-record/contents/checkpoint.py?ref=issue-2215/implementation` rather than transcribed from the diff or the record
evidence: a025f27d2a8be32774695405284cf4bdda21543f:checkpoint.py:44 (`checkpoint_workspace()`)
canonical: this session's own /tmp/issue2215-verify run
```
$ git status --porcelain   # dirty tree: tracked.txt modified, untracked.txt new
 M tracked.txt
?? untracked.txt
$ python3 -c "import checkpoint; print(checkpoint.checkpoint_workspace('work'))"
{'ref': 'refs/checkpoints/issue-9999/implementation', 'commit': '1064b51d2af23d032340fb8c239bf24bc0777fb0', 'dirty_files': 2}
$ git checkout -- tracked.txt && git clean -fd   # simulate the kill
untracked.txt 제거
$ cat tracked.txt
original
$ ls untracked.txt
ls: 'untracked.txt'에 접근할 수 없음: 그런 파일이나 디렉터리가 없습니다
$ git checkout refs/checkpoints/issue-9999/implementation -- .   # recovery
$ cat tracked.txt
in-flight edit
$ cat untracked.txt
in-flight new file
```
rationale: a fresh, independent run against the PR's own checkpoint.py reproduces full recovery of both the destroyed tracked-file edit and the deleted untracked file, from a fixture this session built itself rather than read about.

---
requirement: "Checkpointing leaves the session's branch, HEAD, and index unchanged — demonstrate with `git status` / `git rev-parse HEAD` before and after a checkpoint fires."
spec_ref: issue #2215 `## Acceptance`, bullet 2
verdict: Present (YES)
method: Demonstration — independently executed, same fixture as above
evidence: a025f27d2a8be32774695405284cf4bdda21543f:checkpoint.py:44-97
canonical: this session's own /tmp/issue2215-verify run
```
BEFORE: HEAD=a5f6ba2db96bc828ff680f80aec4697a99dcfb80 branch=issue-9999/implementation status=" M tracked.txt / ?? untracked.txt"
[checkpoint fires]
AFTER:  HEAD=a5f6ba2db96bc828ff680f80aec4697a99dcfb80 branch=issue-9999/implementation status=" M tracked.txt / ?? untracked.txt"
```
rationale: HEAD sha, branch name, and the `git status --porcelain` output (whose leading column distinguishes staged from unstaged, i.e. the index) are byte-identical before and after `checkpoint_workspace()` runs.

---
requirement: "Untracked files are captured, not just tracked modifications."
spec_ref: issue #2215 `## Acceptance`, bullet 3
verdict: Present (YES)
method: Demonstration — independently executed, same run as bullet 1
evidence: a025f27d2a8be32774695405284cf4bdda21543f:checkpoint.py:74-92 (throwaway-index add + write-tree path)
rationale: `untracked.txt`, never `git add`ed, was destroyed by `git clean -fd` and recovered byte-for-byte in the bullet-1 fenced run above — a path only reachable through the untracked-capture code, not the `git stash create` tracked-file path.

---
requirement: "The health line for a live session reports dirty-file count and minutes-since-checkpoint; show it against a session with real dirty state."
spec_ref: issue #2215 `## Acceptance`, bullet 4
verdict: Present (YES)
method: Test (reused existing repo test, per conformance-review-verification-method-selection rule 4) + Inspection
evidence: a025f27d2a8be32774695405284cf4bdda21543f:checkpoint.py:100 (`checkpoint_health()`); a025f27d2a8be32774695405284cf4bdda21543f:watchdog.py:268 (`diagnose_health()` merges the two fields at every return branch via `_diagnosis()`)
canonical: pytest tests/test_workspace_checkpoint.py -v (this session, worktree at a025f27d2a8be32774695405284cf4bdda21543f)
```
[gw8] PASSED tests/test_workspace_checkpoint.py::TestDiagnoseHealthSurfacesCheckpointFields::test_clean_live_entry_reports_zero_and_none
[gw7] PASSED tests/test_workspace_checkpoint.py::TestDiagnoseHealthSurfacesCheckpointFields::test_live_entry_reports_dirty_and_minutes
9 passed in 32.22s
```
rationale: both a clean-session case (zero dirty files, no checkpoint yet) and a dirty-session case (two dirty files, a real elapsed-minutes float) exercise real `diagnose_health()` calls against a real git-repo fixture as `entry["work"]`, matching bullet 4's "against a session with real dirty state" clause — reproduced fresh above, not read from the builder's own pasted output.

---
requirement: "Checkpoint refs are cleaned up at session end and do not leak into pushes or PRs."
spec_ref: issue #2215 `## Acceptance`, bullet 5
verdict: Present (YES)
method: Test (reused) + Analysis (the no-leak clause is a structural fact about git's default push refspec, not something a throwaway-remote push would demonstrate more reliably than reading it)
evidence: a025f27d2a8be32774695405284cf4bdda21543f:roster.py:138-151 (`roster_remove()` calls `checkpoint.cleanup_checkpoint_ref(work)` outside the roster lock, after popping the entry — the one disposal path every roster-removal call site already funnels through)
canonical: pytest tests/test_workspace_checkpoint.py -v (this session, worktree at a025f27d2a8be32774695405284cf4bdda21543f)
```
[gw6] PASSED tests/test_workspace_checkpoint.py::TestCleanupCheckpointRef::test_roster_remove_cleans_up_checkpoint_ref
[gw5] PASSED tests/test_workspace_checkpoint.py::TestCleanupCheckpointRef::test_cleanup_deletes_ref_without_touching_head
```
rationale: `refs/checkpoints/<branch>` lives outside `refs/heads/`; `git push -u origin <branch>` (the only push shape role sessions use, per contract v3) resolves the refspec `refs/heads/<branch>:refs/heads/<branch>` and never touches a ref outside `refs/heads/` by construction — the no-leak clause holds on the ref namespace choice alone, and the cleanup path reruns clean above.

---
requirement: "empty state: a workspace with a clean tree and no edits yet — the health line must report 0 dirty files and no checkpoint, without creating an empty checkpoint ref."
spec_ref: issue #2215 `## Acceptance`, empty state: line
verdict: Present (YES)
method: Test (reused)
evidence: a025f27d2a8be32774695405284cf4bdda21543f:checkpoint.py:44-52 (returns `{"ref": None, "commit": None, "dirty_files": 0}` on a clean tree without calling `update-ref`)
canonical: pytest tests/test_workspace_checkpoint.py -v (this session, worktree at a025f27d2a8be32774695405284cf4bdda21543f)
```
[gw0] PASSED tests/test_workspace_checkpoint.py::TestCheckpointWorkspaceEmptyState::test_clean_tree_no_ref_created
```
rationale: that test additionally asserts `git show-ref` output carries no `refs/checkpoints` line, exercising "no ref created" directly rather than only the return value.

---
requirement: "gate: tests/test_workspace_checkpoint.py"
spec_ref: issue #2215 `## Acceptance`, gate: line
verdict: Present (YES) on the merits — the gate script's own deterministic sub-check would block this verdict for a format reason unrelated to substance; see Open findings item 2
method: Test — directly executed this session from a git worktree checked out at the PR head, not reused from the record's own pasted output
evidence: the named file exists in the PR diff (new file, 230 additions) and its own test run below is this session's, not the builder's
canonical: pytest tests/test_workspace_checkpoint.py -v (this session, worktree at a025f27d2a8be32774695405284cf4bdda21543f)
```
9 passed in 32.22s
```
rationale: fresh execution from the PR's own head commit reproduces the full test file holding, independent of the record's own pasted output.

---
requirement: "provenance: executed-live — the kill-mid-edit recovery and the before/after `git status` / `git rev-parse HEAD` comparison must be performed against a real spawned workspace and the real terminal output pasted into the report."
spec_ref: issue #2215 `## Acceptance`, provenance: line
verdict: Present (YES)
method: Demonstration — independently executed a second time, from outside the builder's own session, satisfying this clause's intent (external, not self-attested, evidence) rather than only inspecting it
evidence: this record's own bullet-1 and bullet-2 fenced output above, produced by this session, not copied from docs/issue-2215/reports/implementation.md
rationale: the provenance clause names WHO must produce the evidence and HOW (real, live, spawned workspace); this session reproduced it independently rather than relying on the builder's own citation.

## Why

The task specifies builder-blind grading: read only the PR diff and the issue's Acceptance section, run `gates/requirement_met.py`, and independently re-execute — not read from the builder's record — the kill-mid-edit recovery and HEAD/branch/index-unchanged claims. `checkpoint.py` was fetched verbatim from the PR's head commit via the GitHub contents API for that reason, rather than transcribed from the diff, and run in a disposable /tmp fixture so this session's own git state (branch/HEAD/index of issue-2215/conformance-review) was never at risk during the destructive kill/recovery step.

## Upstream basis

- issue #2215 (GitHub) — canonical: gh issue view 2215 — the frozen `## Acceptance` section graded above.
- issue #1651 (GitHub, closed) — canonical: gh issue view 1651 — defines gates/requirement_met.py's intended contract: deterministic artifact-presence blocks a landing; the semantic YES/NO/UNKNOWN verdict is advisory-only.
- PR #2223 — canonical: gh pr view 2223 --json title,body,baseRefName,headRefName,files,state,url; gh pr diff 2223 — branch issue-2215/implementation, head a025f27d2a8be32774695405284cf4bdda21543f.
- checkpoint.py, watchdog.py, roster.py, tests/test_workspace_checkpoint.py — read and executed from a `git worktree add` checkout of origin/issue-2215/implementation at the same head commit (worktree removed after use, not part of this branch's own tree).

## What did not work

None — the independent re-execution held on the first attempt for every claim checked; no dead end here for the next reader to avoid repeating.

## Open findings

1. Automated per-criterion grading of issue #2215 via gates/requirement_met.py structurally reaches only the one trailing gate: line — the five prose Acceptance bullets are outside its `_CHECK_LINE` regex (check:/gate:-prefixed lines only) and were hand-graded in this record instead.
canonical: python3 gates/requirement_met.py 2215 2223 (this session; see the fenced output above under "What was done")
   No resolution owed by PR #2223's own landing — this is a property of how issue #2215's Acceptance section was authored. Resolution path: none required; optionally a style note for future issue authors, or a follow-up issue against gates/requirement_met.py's Acceptance-authoring guidance if wider automated coverage is wanted.
2. gates/requirement_met.py's `_artifact_in_diff_hunk()` deliberately excludes `+++ b/<path>` file-header lines from counting as artifact evidence (by its own docstring, so that a file merely being touched does not itself prove a check ran) and requires the artifact string to appear inside a `+`-content line elsewhere in the diff. docs/issue-2215/reports/implementation.md cites its pytest run with a `canonical: ... — run in this session, verbatim result below` line rather than the `acceptance: <command> — result: PASS` shape `_ACCEPTANCE_CITATION` recognizes (the issue #2137 carve-out for record .md files).
canonical: python3 -c "import sys; sys.path.insert(0,'gates'); import requirement_met as rm; ..." (grade() call with verdict='YES' fed in, this session; see the fenced output above under "What was done" — blocking_fail: true)
   Net effect: a correct YES verdict on this one machine-parseable criterion would be mechanically blocked by the gate today, for a citation-format reason, not a substance reason — this session independently reran the underlying test file from the PR's own head commit and it holds. Resolution path: none owed by PR #2223; if the grading tool is meant to be trusted mechanically, gates/requirement_met.py's `_ACCEPTANCE_CITATION` regex or the record-authoring convention would need to converge on one shape — out of this record's own scope to change.

## Next steps

None — `loop_state: reported` is terminal for a review-record (contract v3's per-kind table).

## skill-verdicts

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split issue #2215's Acceptance prose bullets plus the trailing gate:/empty state:/provenance: block into eight discrete, dimension-tagged checkable items before any verdict was rendered (rules 1, 6).
skill-verdict: conformance-review-verification-method-selection — applied: invoked; chose Demonstration for the two independently-executed live claims, Test (reused) for the items already covered by tests/test_workspace_checkpoint.py, and Analysis for the no-leak-into-push clause, a structural git-refspec fact rather than something a throwaway-remote push would prove more reliably (rules 1, 3, 4).
skill-verdict: conformance-review-verdict-assignment — applied: invoked; assigned Present (not a bare binary label) to every item above, with the gate script's own blocking behavior carried as a separate open finding rather than folded into or downgrading the criterion's own verdict (rule 3 was considered and set aside for every item — evidence was locatable and read in each case, so Unverifiable did not apply).
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every code citation above pins file:line plus the PR head commit sha a025f27d2a8be32774695405284cf4bdda21543f actually read, in `sha:path:line` form, rather than a bare path (rule 1).
skill-verdict: conformance-review-finding-record — applied: invoked; wrote the eight per-criterion blocks above with the full field list (requirement, spec_ref, verdict, evidence, rationale), inside the skeleton's own narrative section rather than adding new top-level headings (rules 2, 3).

other mounted skills (conformance-review-sampling-derivation, conformance-review-severity-classification): not-applicable — full enumeration of all eight checkable items was feasible without sampling, and this review's scope was never extended into risk-weighting an already-recorded finding.
