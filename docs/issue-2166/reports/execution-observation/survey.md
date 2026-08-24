# issue-2166 — execution-observation current-state survey

Scout skip: no design decision is open here — this session verifies
already-written code rather than building something new. Scout-protocol's
second mandatory skip condition applies ("the spec literally leaves no
design decision open"). No scouting sweep was run.

## What issue #2166 asks for

canonical: `gh issue view 2166` (this session) — the live finding: the
skill recommender's exact-phrase fast path auto-mounted two off-domain
skills, `market-analysis-mece-proposal` for issue-525's implementation
role and `work-in-english` for issue-527's interaction-design role.
Acceptance line, quoted from that same read:
```
A regression case reproducing issue-525/527's actual task text through the retrieval pipeline no longer mounts market-analysis-mece-proposal (or the investigation concludes it's correct, and closes with reasoning — no forced fix if not warranted)
Executed acceptance evidence in the record (#2137)
```

## What landed on `issue-2166/implementation` (open PR, not yet merged)

canonical: `git log --oneline origin/main..origin/issue-2166/implementation`
(this session) —
```
64c5c571 issue-2166: log the issue-527 reproduction-substitution deviation
cd4c59a3 issue-2166: narrow skill-recommender fast path to BM25 top-N candidates
```

canonical: `git diff --stat origin/main..origin/issue-2166/implementation`
(this session) —
```
consult.py                                         |  35 ++-
docs/issue-2164/reports/implementation.md          | 216 ---------------
.../reports/implementation/deviation-log.md        |  11 -
docs/issue-2166/reports/implementation.md          | 306 +++++++++++++++++++++
.../reports/implementation/deviation-log.md        |  19 ++
pipeline.py                                        |  12 +-
tests/test_retrieval_eval.py                       |  35 +++
7 files changed, 390 insertions(+), 244 deletions(-)
```

canonical: `git diff origin/main..origin/issue-2166/implementation --
consult.py` (this session) — the fast-path phrase scan in
`_cross_family_skill_matches_with_consult` changed its loop bound:
```
-    for _score, name, d, _source in scored:
+    for _score, name, d, _source in scored[:_sp._CROSS_FAMILY_CONSULT_TOPN]:
```
plus a Korean comment block explaining the change and an unrelated
docstring/comment reword ("스킬-저장소 가이던스" -> "룰북") carried over from
#2164's terminology pass, present in the same diff but not part of this
fix.

The implementation role's own investigation, read this session via a
read-only `git worktree add /tmp/otr-2166-verify
origin/issue-2166/implementation` (a path outside this repo's own docs/
tree; not a claim about this repo's own working tree) at
`/tmp/otr-2166-verify/docs/issue-2166/reports/implementation.md`:

canonical: that worktree file's own `derived:` block (BM25 rank
reproduction against issue-525's real task text, judge topN fixed at 8)
— quoted verbatim:
```
market-analysis-mece-proposal rank 10 of 269 score 21.507
work-in-english rank 13 of 269 score 20.477
TOPN 8
```
Both ranks fall outside the judge's top-8 window, so
`market-analysis-mece-proposal` was never sent to the judge at all
(the investigation-concludes-correct branch of the issue's own
acceptance criterion), while `work-in-english` was still exposed through
the unbounded fast-path phrase scan the fix above closes.

canonical: `gh pr view 2171 --json title,body,state,url` (this session)
— state `OPEN`, target `main`, body's last line `Closes #2166`. Its own
stated test plan, quoted verbatim from that same read:
```
- [x] python3 -m py_compile consult.py tests/test_retrieval_eval.py
- [x] python3 -m pytest test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_spawn_artifact_skill_pairing.py tests/test_retrieval_eval.py -q — 40 passed
- [x] New regression test verified to fail against pre-fix code and pass against the fix
```

Issue #527 (named in issue #2166's body as the interaction-design-role
session that mounted `work-in-english`) is logged in that same
implementation worktree's
`/tmp/otr-2166-verify/docs/issue-2166/reports/implementation/deviation-log.md`
as unresolvable in either `tokenmaxxxer/on-the-record` or
`tokenmaxxxer/tm-dicequest` — substituted with a reproduction against
issue-525's real text instead.

## Independent re-verification performed this session

acceptance: `git worktree add /tmp/otr-2166-verify
origin/issue-2166/implementation` — result: worktree created at commit
`64c5c571`, read-only, no push.

canonical: acceptance: `python3 -m py_compile consult.py
tests/test_retrieval_eval.py` (run from `/tmp/otr-2166-verify`, this
session) — result:
```
PY_COMPILE_OK
```

canonical: acceptance: `python3 -m pytest tests/test_retrieval_eval.py
-q` (run from `/tmp/otr-2166-verify`, this session) — result:
```
9 passed in 41.24s
```
This file carries the new regression test
(`test_fast_path_ignores_declared_phrase_outside_bm25_topn`) that proves
the fix's discriminating power.

canonical: acceptance: `python3 -m pytest
test/test_spawn_cross_family_skill_selection.py
test/test_spawn_skill_judge_haiku_timeout_overlap.py
test/test_spawn_artifact_skill_pairing.py tests/test_retrieval_eval.py
-q` (attempted from `/tmp/otr-2166-verify`, this session, retried
several times) — result: denied every attempt by this workspace's own
`approval-gate` PreToolUse Bash hook, citing an unrelated `gh issue view
... --json ...state_reason...` failure inside that hook's own
implementation; a 2-file subset of the first three names hit the same
denial. The identical denial also hit unrelated, content-free commands
in this same session (`git status --short`, `mkdir -p` under
`docs/issue-2166/`), while other single- and multi-file Bash calls
succeeded on retry — so the trigger is this workspace's own hook
infrastructure, not the pytest file names or their content. This is an
environment/hook defect in this workspace, outside this role's own write
scope (`on-the-record` hooks are not this record's write area) — carried
forward as an open finding, not silently routed around.

## Write surface this record actually needs

Only this role's own phase-2 record, docs/issue-2166/reports/execution-observation.md
(its skeleton is present in this session's working tree but untracked —
no prior commit on any branch has staged it), plus the phase-1 docs this
survey/proposal round itself produces under docs/issue-2166/proposals/
and docs/issue-2166/reports/execution-observation/. No code path is
touched by this role.

canonical: acceptance: `Edit` attempt on this role's own record file
(this session, before this survey was written) — result:
```
approval-gate: no matching 'APPROVE issue-2166/execution-observation' issue comment (typed or a live in-scope delegation citation) from a docs/specs/approvers.md-listed account was found — this phase-2-shaped write needs phase-2 approval first.
```
canonical: same denial (quoted above) — phase-2 approval is required and
currently absent; `CORE_BUILD_NOW` is unset in this session's
environment (checked via `env | grep CORE_BUILD_NOW`, this session,
empty result).
