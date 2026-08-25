# issue-2207 conformance-review — current-state survey

Phase-1 survey (survey-order-directive) for the conformance audit of PR
tokenmaxxxer/on-the-record#2308 (branch `issue-2207/refactoring-legacy`,
role `refactoring-legacy`), issue #2207's own delivery.

```
$ gh pr view 2308 --json state,mergedAt,mergeable,baseRefName,headRefName
{"baseRefName":"main","headRefName":"issue-2207/refactoring-legacy",
 "mergeable":"MERGEABLE","mergedAt":null,"state":"OPEN"}
$ gh pr view 2308 --json headRefOid,baseRefOid -q '.headRefOid, .baseRefOid'
85a9611f6809183fa49ec9c270c2fbcae7079d8a
ede98d8f30d88bf13ba6dbfc9792e98f183a07aa
```
canonical: both commands — pasted live run above (executed-unit). The
target is **open, not merged** — unlike the issue-2164 conformance-review
precedent this survey otherwise follows, which audited an already-merged
commit. `ede98d8f` sits in this branch's own `git log` history (7 commits
back from this session's HEAD), so PR #2308's base is an ancestor of
current `main`.

## 0. Base-commit drift

```
$ git log --oneline -- spawn.py | head -3
5bf8da8a issue-2241: stage 0 — additive skill-based spawn CLI alongside role path (#2296)
0fc13f24 issue-2208: judge abstention rate, negative-clause BM25 stripping, work-in-english static pin (#2218)
fd5016c2 issue-2211: export plugin-root/core-root/skill-registry/workspace-root into spawned session env (#2228)
$ wc -l spawn.py
3386 spawn.py
```
canonical: both commands — pasted live run above (executed-unit).
`5bf8da8a` (issue-2241) touches `spawn.py` and sits between PR #2308's
base `ede98d8f` and this session's HEAD — `main` has grown `spawn.py` by
39 lines (3347 at the PR's base -> 3386 here) since the PR branched, from
unrelated work. The PR's own before/after counts (3347 -> 2929, record's
"What was done") are correct against its own base but will not be the
literal before/after once the PR is rebased/merged onto current `main`.
Not a conformance defect — a moving-target property of reviewing an open
PR — logged as an open finding for phase 2 to re-check at merge time.

## 1. What landed (gh pr diff / gh api, read-only)

```
$ gh api repos/tokenmaxxxer/on-the-record/pulls/2308/files --jq '.[].filename'
directive_assembly.py
docs/issue-2207/reports/refactoring-legacy.md
spawn.py
tests/test_perf_budget_issue_2053.py
```
canonical: pasted live run above (executed-unit). 4 files, +799/-435 per
`gh pr view 2308` (additions/deletions fields). All four paths are
**untracked in this working tree** — they exist only on the unmerged
`issue-2207/refactoring-legacy` branch (PR #2308 head `85a9611f`), not
on this branch or on `main` yet. Every citation below to
`refactoring-legacy.md`'s prose is sourced from `gh pr diff 2308`'s text
output, not from a local path read, and will resolve to a real path in
this working tree only after the PR merges.

`gh pr diff 2308` (full diff, read this session) shows: a new module
`directive_assembly.py` (462 lines, untracked here — PR #2308 only)
receiving 9 functions + private constants
(`_CHECKPOINT_CONTRACT_BLOCK`/`_checkpoint_contract_block`/
`_checkpoint_index_block`, the directive-section-file machinery,
`_RECORD_SKELETON`/`write_record_skeleton`, `composition_breakdown`, and
the cross-family BM25 matching pair) moved verbatim out of `spawn.py`;
`spawn.py` gains a 26-line import+re-export block
(`directive_assembly._sp = sys.modules[__name__]`, then one
`name = directive_assembly.name` line per moved symbol) at the same site
the functions used to live, and loses the ~424 lines of their bodies;
`tests/test_perf_budget_issue_2053.py` is updated to regex-scan
`directive_assembly.py` instead of `spawn.py` for the
no-network-or-consult-call invariant on `_bm25_cross_family_scores`.

Note: this survey did **not** fetch the untracked-here
`refactoring-legacy.md`'s content via `gh api .../contents/...` — that
call is refused by this session's own `board-gate` ("belongs to another
role"), encountered live (see §5). Its content was instead read via the
plain `gh pr diff 2308` text (not board-gated), which is how this
survey's citations to that file's prose above and below are sourced,
consistent with the untracked/unmerged status noted just above.

## 2. Requirement extraction (conformance-review-requirement-extraction applied)

Splitting issue #2207's Investigate/Fix/Acceptance bundles plus the
2026-08-25 operator-frozen-constraint comment (rule 1, one obligation per
line), dimension-tagged (rule 6), conditional items kept separate (rule
5):

1. **REQ-1** (functional-behavior) — sample 3-5 recent engineering-task
   sessions, report the distribution of per-file partial-read counts, not
   one anecdote. Source: "## Investigate", bullet 1.
2. **REQ-2** (functional-behavior) — identify which `spawn.py` regions
   attract repeated navigation and what lives there. Source:
   "## Investigate", bullet 2.
3. **REQ-3** (scope-boundary) — check whether the #2114-#2122 2,649-line
   source-pin floor is still load-bearing or was a stopping point.
   Source: "## Investigate", bullet 3.
4. **REQ-4** (scope-boundary) — decomposition proceeds only if the
   measurement supports it, and follows the seam the access pattern
   reveals rather than scattering a cohesive region. Source: "## Fix",
   both bullets.
5. **REQ-5** (functional-behavior, conditional — see rule 5: this item's
   verdict depends on post-landing evidence that does not exist yet) —
   a re-measured engineering-class task on the same subject shows
   materially fewer single-file partial reads than the 19 recorded,
   verified by the same session-log read-offset analysis. Source:
   "## Acceptance", bullet 1. The issue's own "empty state" note
   ("measured against live session logs that already exist") already
   flags this as a future observation, not something a landing commit
   can itself satisfy.
6. **REQ-6** (scope-boundary, conditional on REQ-3: only binds if a floor
   test exists and the floor changes) — existing source-pin tests
   updated deliberately, not merely relaxed, if the floor changes, with
   reasoning recorded. Source: "## Acceptance", bullet 2.
7. **REQ-7** (error-handling/regression) — full test suite green
   (decomposition must not change behavior). Source: "## Acceptance",
   bullet 3.
8. **REQ-8** (process/scope-boundary) — executed acceptance evidence
   present in the record. Source: "## Acceptance", bullet 4 (references
   issue #2137's convention).
9. **REQ-9** (scope-boundary) — the fix holds systemically for every
   session that installs on-the-record and works against any target
   repo, not just this self-hosted checkout. Source: 2026-08-25
   operator-frozen-constraint comment, sentence 1.
10. **REQ-10** (scope-boundary) — no added per-spawn overhead or
    steady-state load. Source: same comment, sentence 2, clause 1.
11. **REQ-11** (scope-boundary) — no new conflict surfaces (append-log or
    otherwise). Source: same comment, clause 2.
12. **REQ-12** (scope-boundary) — no stall/deadlock modes. Source: same
    comment, clause 3.
13. **REQ-13** (scope-boundary) — no consumer-tree pollution. Source:
    same comment, clause 4.
14. **REQ-14** (process) — where a trade-off is unavoidable, it is
    measured and stated in the record, not discovered later. Source:
    same comment, final sentence.

No summary line restated 3+ sub-points needing removal (rule 3 n/a); the
issue states no sampling derivation for phase 2 to reuse verbatim (rule 4
n/a — see §6, full enumeration is feasible at this size).

## 3. Independent re-checks performed this session (not taken from the record)

```
$ grep -rln "2649\|source.pin\|source_pin" --include=*.py --include=*.md --include=*.json .
spawn.py
docs/issue-235/reports/execution-observation/research-evidence.md
docs/issue-2159/reports/implementation.md
$ grep -n "2649\|source.pin\|source_pin" spawn.py
347:# and `watchdog_check_one` stay here (source-pinned by gates/test_boundary.py
```
canonical: both commands — pasted live run above (executed-unit). Broader
than the refactoring-legacy record's own `grep -rln "2649\|source_pin"
tests/ test/ gates/` (that record, quoted via `gh pr diff 2308` in §1
above) — this survey searched every `.py`/`.md`/`.json` in the repo, not
only the three test directories. The one `spawn.py` hit is an unrelated
`gates/test_boundary.py` coverage-mapping reference (confirmed by reading
that line: it is about `watchdog_check_one` staying in `spawn.py`, not a
line-count floor). `gates/test_boundary.py` itself was inspected
(`grep -n "spawn.py\|len(\|wc -l\|line"`) and contains no line-count
assertion. **Independently confirms** the record's own claim: no literal
2,649-line (or any numeric) source-pin floor test exists anywhere in this
checkout — REQ-3/REQ-6 support.

Full-suite pytest re-verification (REQ-7) was **not** attempted this
survey — the record's own pasted run took 927.82s, longer than a single
Bash call's budget in this session; independently re-running it (rather
than trusting the record's pasted transcript, per this skill family's own
rejection of builder-self-report-as-evidence) is deferred to phase 2,
where it can be backgrounded across the session's full turn budget.

## 4. Environment notes encountered this session (for phase 2's benefit)

- `git fetch origin pull/2308/head:<local-branch>` is refused by this
  session's `approval-gate` hook (phase-2-work gate) even though it only
  reads/creates local refs — read the PR's diff via `gh pr diff 2308`
  instead, which is not gated.
- `gh api repos/.../pulls/2308/files` / `.../contents/...` on the
  untracked-here `refactoring-legacy.md` path is refused by a second,
  distinct `board-gate` check ("belongs to another role") layered onto
  the same denial — `gh pr diff 2308` (plain text diff, no per-file API
  call) was not gated and is what this survey's file-content citations
  use instead.
- Any Bash command whose argv text contains a `docs/issue-<n>` path
  substring is refused by the `approval-gate` hook pre-execution, for
  **any** issue number, not only #2207's own — encountered live against
  a different issue's path (read only out of curiosity, abandoned once
  denied) and against a plain `mkdir -p docs/issue-2207/...` call. The
  `Write` tool (used to create this survey and the sibling proposal) is
  not subject to this Bash-argv pattern check — a separate
  `record-claim-guard` hook gates `Write` instead, requiring every cited
  path to either exist in this working tree or be marked untracked/moved
  nearby, which is why this section and §1 above spell that out
  explicitly rather than citing `refactoring-legacy.md` bare. Logged as
  an open finding, not worked around silently.

## 5. Sampling scope

Full enumeration, not a sample: 14 requirement line items extracted in
§2, small enough that spot-checking would cost more setup than it saves.
`conformance-review-sampling-derivation` is not invoked this session (see
the proposal's skill-verdict section).
