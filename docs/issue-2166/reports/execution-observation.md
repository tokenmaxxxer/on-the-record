---
issue: 2166
role: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2166/reports/implementation.md
    sha: b9cd89af0e6626fa98db53d580c95936d6710f6e
  - path: consult.py
    sha: b9cd89af0e6626fa98db53d580c95936d6710f6e
  - path: tests/test_retrieval_eval.py
    sha: b9cd89af0e6626fa98db53d580c95936d6710f6e
subject: PR #2171 (issue-2166/implementation), on main as commit b9cd89af0e6626fa98db53d580c95936d6710f6e
test: "python3 -m py_compile consult.py tests/test_retrieval_eval.py; python3 -m pytest test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_spawn_artifact_skill_pairing.py tests/test_retrieval_eval.py -q"
result: passed
assertedBy: issue-2166/execution-observation session, 2026-08-24 (independent re-execution against current main, not a restatement of PR #2171's own reported numbers)
---

# issue-2166 — execution-observation record

## What was done

canonical: gh issue view 2166 (this session)

Investigated the live finding named there — the skill recommender's
exact-phrase fast path auto-mounting `market-analysis-mece-proposal` for
issue-525's implementation role and `work-in-english` for issue-527's
interaction-design role — and independently re-ran PR #2171's own
acceptance evidence against the current state of `main`, rather than
relying on the implementation role's self-reported numbers.

canonical: git log --oneline -3

Phase 1 (commit `d1c27d0d`) surveyed the diff and proposed the plan
below; commit `431bfe22` logged the resulting phase-1-only-landing
deviation.

canonical: gh issue view 2166 --json comments

Phase 2 opened on comment `issuecomment-5392326695`, body exactly
`APPROVE issue-2166/execution-observation`, posted by `JiwonJung94`.

canonical: gh pr view 2174 --json author

`JiwonJung94` (listed in `docs/specs/approvers.md`, read this session)
also authored this branch's own PR #2174 — single-account mode, so the
issue-comment approval path applies here.

canonical: git worktree add /tmp/otr-2166-verify2 origin/main

A read-only worktree at commit `b9cd89af0e6626fa98db53d580c95936d6710f6e`
(PR #2171, now on `main`). The phase-1 survey had exercised the same
diff at the pre-merge branch head `64c5c571` — identical content,
different sha.

canonical: python3 -m py_compile consult.py tests/test_retrieval_eval.py — result: PASS

(run from `/tmp/otr-2166-verify2`, this session)
```
PY_COMPILE_OK
```

canonical: python3 -m pytest test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_spawn_artifact_skill_pairing.py tests/test_retrieval_eval.py -q — result: PASS

(run from `/tmp/otr-2166-verify2`, this session; the full test-plan leg
the phase-1 survey could not independently run — that session was
blocked every attempt by an `approval-gate` PreToolUse Bash-hook flake
there, logged as an open finding; this session's run below hit no such
block):
```
........................................                                 [100%]
40 passed in 2.10s
```

canonical: python3 -m pytest tests/test_retrieval_eval.py -v — result: PASS

(run from `/tmp/otr-2166-verify2`, this session)
```
PASSED tests/test_retrieval_eval.py::HermeticEnrichmentAndFastPathTest::test_fast_path_ignores_declared_phrase_outside_bm25_topn
9 passed in 1.38s
```
`test_fast_path_ignores_declared_phrase_outside_bm25_topn` is the new
regression test targeting this fix, shown above. Worktree removed after
use (`git worktree remove /tmp/otr-2166-verify2 --force`, this session);
no push, no edit to any code path.

## Why

Verify-at-landing (on-the-record #2137): a deliverable is code plus
independently executed acceptance evidence, not a copy of the delivering
role's own claimed numbers. canonical:
`docs/issue-2166/reports/execution-observation/survey.md`, quoting `gh
issue view 2166`'s own acceptance line — it requires either a regression
case proving the off-domain mount no longer force-fires, or a reasoned
investigation-concludes-correct closure, backed by evidence in this
record.

## Upstream basis

canonical: git show origin/main:docs/issue-2166/reports/implementation.md

The implementation role's own delivery record, commit
`b9cd89af0e6626fa98db53d580c95936d6710f6e`. Its own `derived:` block
(quoted verbatim, BM25 rank reproduction against issue-525's real task
text, judge topN fixed at 8):
```
market-analysis-mece-proposal rank 10 of 269 score 21.507
work-in-english rank 13 of 269 score 20.477
```
Both ranks sit outside the judge's top-8 window: `market-analysis-mece-proposal`
never reached the judge (the investigation-concludes-correct branch of
the issue's own acceptance criterion), while `work-in-english` was
exposed through the *unbounded* fast-path phrase scan that this fix
narrows.

canonical: git diff 3ea0ec88..b9cd89af -- consult.py

The fast-path phrase scan in `_cross_family_skill_matches_with_consult`
now iterates `scored[:_sp._CROSS_FAMILY_CONSULT_TOPN]` instead of the
full `scored` list.

canonical: `tests/test_retrieval_eval.py` at commit
`b9cd89af0e6626fa98db53d580c95936d6710f6e`, read this session — carries
`test_fast_path_ignores_declared_phrase_outside_bm25_topn`, exercised in
the pytest -v run above.

canonical: `docs/issue-2166/proposals/execution-observation-record.md`
(this branch, commit `d1c27d0d`) — this role's own phase-1 proposal. The
one contingency it named (the test-plan leg blocked by the
approval-gate hook flake) is addressed by the acceptance runs above:
this session re-ran that leg live in phase 2 against current `main`, no
divergence from the proposal's own plan.

## Open findings

1. `approval-gate.sh` Bash-tool coverage gap — canonical:
   `docs/issue-2166/reports/execution-observation/2026-08-24-hunt-execution-observation-record.md`
   (this branch, commit `d1c27d0d`), which ran
   `on-the-record/hooks/pretooluse_dispatcher.py` directly that session:
   the hook is registered only for the `Write|Edit|MultiEdit` matcher, so
   an identical phase-2-shaped record write issued as a Bash
   heredoc/redirect goes unchecked, unlike the Write-tool path (which
   correctly denies it pre-approval). Out of this role's own write scope
   (`on-the-record/hooks/` infrastructure, not `docs/issue-2166/`) — not
   fixed here. Resolution path: whoever owns `on-the-record/hooks/`
   registers `approval-gate.sh` under the Bash matcher too (or widens
   `heredoc-command-refusal-gate.sh`'s existing heredoc detection to
   phase-2-shaped file-write commands generally, not only
   `git commit`/`gh issue`/`gh pr`).

canonical: the py_compile and pytest runs above (this session) — no open
finding remains against the observed artifact itself: every leg of PR
#2171's own test plan ran clean against current `main`, independently.

## Next steps

None against this record's own subject — `loop_state` is terminal
(`handed-off`). The py_compile and pytest runs above (this session) show
the observed artifact's evidence fully reproduced against current
`main`. The one open finding above is infrastructure outside this
role's write area, carried forward via its own resolution path rather
than left as an unstated gap.
