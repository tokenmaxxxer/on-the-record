---
code_under_review:
  - consult.py
  - tests/test_retrieval_eval.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# issue-2166 — implementation record

## What was done

Investigated the two reported off-domain skill mounts
(`market-analysis-mece-proposal` for issue-525's implementation role,
`work-in-english` for issue-527's interaction-design role) by reproducing
the retrieval pipeline directly against the real `skill-repository`
checkout, rather than guessing ahead of the evidence.

Reproduction, issue-525's actual GitHub issue body (title `Batch-3+:
realize remaining 33 role specs (build/ops-knowledge/commercial-risk
families) — follow-up E of #515`, `role="implementation"`) as
`spawn._bm25_cross_family_scores`'s `task_text` — the same raw text
`_spawn_one` pins to `_cross_family_task_text` before any directive
appends (spawn.py:2212, `_cross_family_task_text = task`):

derived: `gh issue view 525 --json body` piped into a script calling
`spawn._bm25_cross_family_scores(body, "implementation", spawn._skill_repo_root())`
with `spawn._installed_plugin_skill_dirs` patched to `{}` (skill-repo-only
corpus) — result:
```
market-analysis-mece-proposal rank 10 of 269 score 21.507
work-in-english rank 13 of 269 score 20.477
TOPN 8
```

Both skills rank outside the judge's top-8 slate
(`spawn._CROSS_FAMILY_CONSULT_TOPN=8`) for issue-525's real task text.
Because `_cross_family_skill_matches_with_consult`'s judge candidate list
is built from `scored[:_sp._CROSS_FAMILY_CONSULT_TOPN]` (consult.py:367-369,
unchanged by this fix), a rank-13/rank-10 skill is *never sent to the
judge* for this input — that part of the pipeline already produces the
right outcome for `market-analysis-mece-proposal` on this specific
reproduction, with no fix needed (**investigation concludes correct,
per the issue's own "closes with reasoning" branch**).

But `work-in-english` was still exposed through a different channel: the
exact-phrase fast path. Its declared quoted phrases:

derived: `spawn._skill_declared_phrases(spawn._skill_repo_root() / "work-in-english")` — result:
```
['이 버그 고쳐줘', '리팩토링 해줘', 'pr 올려줘', '커밋 메시지 영어로 써야 하나', 'fix this bug and open a pr']
```
canonical: `skill-repository/skills/work-in-english/SKILL.md:10-11` —
```
        Trigger even if the user never mentions language or tokens — e.g.
        "이 버그 고쳐줘", "리팩토링 해줘", "PR 올려줘", "커밋 메시지 영어로 써야 하나", "fix this bug and open a pr".
```
These are generic illustrative request examples from the skill's own
`"Trigger on requests like \"...\""` format, not distinctive jargon —
contrast with the fast path's own worked example, `game-growth-system-design`'s
"per-stage monster damage/HP scaling" (dicequest gold case, rank inside
top-8 by design — `tests/data/retrieval_gold.jsonl`).

Before this fix, `consult.py`'s fast-path scan ran over the *entire*
`scored` list, not just the judge's top-N slate.
canonical: pre-fix `consult.py` at commit `f7d431c` —
```
    task_lower = task_text.lower()
    fast: list[tuple[int, str, Path]] = []
    for _score, name, d, _source in scored:
        for phrase in _sp._skill_declared_phrases(d):
```
So a phrase like "fix this bug and open a pr" — which can appear
verbatim in almost any Korean-language coding request regardless of role
or project — auto-picked `work-in-english` with **zero judgment**,
independent of its measured rank-13-of-269 relevance to the actual task
(rank derived above).

## Why

Fix: `consult.py:366` now reads
`for _score, name, d, _source in scored[:_sp._CROSS_FAMILY_CONSULT_TOPN]:`
— the fast-path phrase scan is narrowed to the same top-N slice the judge
itself uses. A declared phrase can now only auto-pick a skill that is
already among the judge's own top-8 BM25 candidates; a skill ranked
outside that window (`work-in-english` at 13th for issue-525's task,
measured above) is excluded from the candidate set entirely — same as it
would be without any declared phrase, forcing genuinely off-topic skills
through normal BM25 ranking (which already rejects them) instead of an
unranked phrase-match bypass.

Root cause: #2128 (issue #2124 part 2) added the exact-phrase fast path
as an unconditional shortcut over the entire BM25-scored candidate pool.
derived: `git log --format='%ad %H %s' --date=short --all -- pipeline.py spawn.py consult.py | grep -i 2124` — result:
```
2026-08-24 f7d431c253b581adbb44725c81d4a0f74816eae7 issue-2124: skill recommender tuning — enriched BM25 documents, exact-phrase fast path, judge prompt diet, offline retrieval eval (#2128)
```
canonical: `consult.py:344-346` (the mechanism's own framing) —
```
    # 이슈 #2124 part 2 (exact-phrase fast path, OpenHands microagents 키워드
    # tier): description 에 따옴표로 선언된 트리거 문구가 과제 텍스트에
    # 그대로(대소문자 무시) 들어 있으면 그 스킬은 판단 없이 자동 픽 —
```
This frames the mechanism as a "keyword tier" for distinctive technical
phrases, but skill authors used the same `#99` quoting convention
(`"Trigger on requests like \"...\""`) for both distinctive jargon and
illustrative example sentences describing a skill's applicability
condition — #2128 treated every quoted phrase as equally safe to
auto-pick regardless of which kind it is or how relevant the skill
otherwise is to the task. That scope mismatch is what this fix closes,
from the retrieval-pipeline side.

Two alternatives considered and rejected:
- **Corpus-wide IDF/rarity filter on declared-phrase tokens** (disqualify
  a phrase from fast-path if its tokens are too common across the BM25
  corpus): rejected after measuring it against the real corpus — Korean
  phrases (`이 버그 고쳐줘`) tokenize to the empty set under the existing
  ASCII-only `spawn._TOKEN_RE = re.compile(r"[a-z0-9]+")` (spawn.py:2060),
  so an IDF-based filter cannot evaluate them at all; and even for the
  English phrase "fix this bug and open a pr" the per-token IDF spread
  measured against the real 269-skill corpus (`this`=0.431, `fix`=3.073,
  `bug`=3.894, `open`=3.347, `pr`=4.682 —
  derived: per-token IDF replay of `spawn._bm25_cross_family_scores`'s own
  `idf = log((n - df + 0.5) / (df + 0.5) + 1)` formula over the same
  corpus df table) was not cleanly separable from the legitimate
  dicequest phrase's own spread without a corpus-scale tuning exercise
  this issue does not warrant, and would still leave every Korean-only
  phrase completely unfiltered.
- **Reword `work-in-english`'s declared phrases** (the issue's own
  suggested remedy #1, "narrow the description"): correct in principle
  but out of scope for this session — that `SKILL.md` lives in
  `tokenmaxxxer/skill-repository`, a separate repository with its own
  role/branch/PR flow; this session's write scope and PR target is
  `tokenmaxxxer/on-the-record` only, branch `issue-2166/implementation`
  (contract v3). The topN restriction fixes the retrieval-pipeline side
  of the bug without a cross-repo change, and generalizes to any future
  skill whose declared phrases turn out to be similarly generic.

## Upstream basis

Issue #2166 itself (the live finding) is the primary upstream input.
Build-now bypass (contract v3 s19a, `CORE_BUILD_NOW=1` set by the
spawner) skipped the phase-1 proposal round, so there is no
`docs/issue-2166/proposals/*` file to cite.

canonical: files read directly in this session — `consult.py`
(`_cross_family_skill_matches_with_consult`, `_skill_judge_consult`),
`pipeline.py` (`_skill_declared_phrases`, `_skill_bm25_document`,
`_skill_frontmatter_description`), `spawn.py`
(`_bm25_cross_family_scores`, `_CROSS_FAMILY_CONSULT_TOPN`,
`_cross_family_task_text` pinning at spawn.py:2212), the real
`skill-repository` checkout's `market-analysis-mece-proposal/SKILL.md`
and `work-in-english/SKILL.md`, and
`docs/issue-2040/proposals/bm25-first-then-consult-judge.md`.
derived: `git log --format='%ad %H %s' --date=short --all -- pipeline.py spawn.py consult.py | grep -i 2124` — result (repeated from `## Why`):
```
2026-08-24 f7d431c253b581adbb44725c81d4a0f74816eae7 issue-2124: skill recommender tuning — enriched BM25 documents, exact-phrase fast path, judge prompt diet, offline retrieval eval (#2128)
```

derived: `gh issue view 527 --json title,body -R tokenmaxxxer/on-the-record` — result: an unrelated write_scope-split proposal (title `docs(issue-523): phase-1 proposal — technical-writing/devrel write_scope split`), not an interaction-design-role task.
derived: `gh issue view 527 -R tokenmaxxxer/tm-dicequest` — result: `GraphQL: Could not resolve to an issue or pull request with the number of 527.`

Issue #527 could not be located as a real, resolvable GitHub issue in
either repo checked (derived block immediately above). `sha:
same-commit` for both `consult.py` and `tests/test_retrieval_eval.py`
(both land in this commit).

Scout/survey: skipped. This is a live, reported retrieval-pipeline bug
report with a stated, boundable investigate/fix/acceptance shape (not an
open product/design decision needing option comparison) — the
survey-order and scout-protocol directives both name that as the skip
condition, and the issue's own Acceptance criterion explicitly allows an
investigation-only outcome for one of the two named skills.

## Doc placement ladder

- [x] `docs/specs/` — not applicable; no system design changed, and no
  `docs/specs/*` file was touched (no `spec_index.py --update` needed).
- [x] `docs/decisions/` — not applicable; no hard-to-reverse choice — the
  topN restriction is a narrow, reversible one-line scoping fix.
- [x] `docs/reports/` — not applicable; no cross-cutting measurement
  produced beyond what's cited inline above.
- [x] This implementation record — filled (this file).

## What did not work

- First attempts at reproducing the pipeline live called
  `spawn._cross_family_skill_matches_with_consult` without mocking
  `spawn._skill_judge_consult`, which — as designed
  (`consult.py:_skill_judge_consult`, lines 200-213) — spawns a real
  haiku-tier consult session and commits its trace to
  `docs/reports/consult-log.md` on this branch as a side effect. This
  happened across the investigation (unintended commits, e.g. sha
  `e2f085f8`, `a566fa0d`, `67cb5763`, `e1126ee4`, `a414fc7d`).
  derived: `git rev-parse --abbrev-ref --symbolic-full-name @{u}` run
  before each cleanup — result: `origin/main` (this branch had never
  been pushed as `origin/issue-2166/implementation`), so
  `git reset --hard d9a1e826` (the branch's real base, `issue-2163:
  guard patrol-poll against missing checkout mid-reclone (#2167)`) was
  safe each time without discarding pushed history. Every further
  reproduction was then switched to either read-only calls
  (`_bm25_cross_family_scores`, `_skill_declared_phrases` alone) or
  `mock.patch.object(spawn, "_skill_judge_consult", ...)` around the
  full pipeline call.
- One inline diagnostic script constructing a fake corpus with
  `mock.patch.object(spawn, "_skill_judge_consult", judge)` did not
  intercept the real call the way the equivalent pattern does inside the
  actual test module.
  canonical: `tests/test_retrieval_eval.py`'s existing
  `test_fast_path_autopicks_on_verbatim_phrase_judge_never_called` and
  `test_fast_path_filling_cap_skips_judge_entirely` use the identical
  `mock.patch.object(spawn, "_skill_judge_consult", judge)` pattern —
  their own status is reported in `## Acceptance evidence` below, not
  restated here. Root cause of the throwaway-script mismatch not fully
  isolated; worked around by writing the new regression test into the
  real test file instead of an ad-hoc script.

## Open findings

- `market-analysis-mece-proposal`'s own declared phrases (`do these
  sections overlap`, `is the proposal missing a required element`) were
  not separately exercised end-to-end against a live judge run in this
  investigation, to avoid triggering further consult-trace commit side
  effects (see "What did not work" above).
  canonical: `consult.py:366` — the fix is unconditional on which
  skill's phrase matched, so it protects this skill via the same code
  path proven by the new regression test, but a skill-specific
  live-judge confirmation was not performed. Resolution path: covered
  generically by the regression test's mechanism proof; a skill-specific
  live-judge check would need a session that accepts the consult-trace
  commit side effect, or a further mock-based test using this skill's
  actual declared phrases.
- Issue #527 (cited in the issue body as the interaction-design-role
  session that mounted `work-in-english`) could not be located as a
  resolvable GitHub issue.
  canonical: `gh issue view 527 -R tokenmaxxxer/on-the-record` and
  `gh issue view 527 -R tokenmaxxxer/tm-dicequest` (repeated from
  `## Upstream basis`) — the first returns an unrelated proposal, the
  second returns `Could not resolve to an issue or pull request with the
  number of 527`. Resolution path: if the reporting session can supply
  the actual repo/issue pair, a targeted regression case using that
  literal task text could be added to `tests/data/retrieval_gold.jsonl`.
- The declared-phrase authoring ambiguity itself (skill-repository's
  `#99` quoting convention conflates "distinctive jargon" and
  "illustrative example sentence" with no structural marker
  distinguishing them) is not fixed — only worked around from the
  retrieval-pipeline side. Resolution path: a `tokenmaxxxer/skill-repository`
  session, out of this repo's write scope, could reword
  `work-in-english`'s declared phrases to be less generic, or introduce
  an explicit marker distinguishing fast-path-safe phrases from
  illustrative examples; either would be a defense-in-depth addition on
  top of (not a replacement for) this fix.

## Next steps

None — `loop_state: landed` (terminal for a `coding-record`): the fix,
regression test, and this record are committed, pushed, and carried in
the phase-2 delivery PR for issue #2166.

## Skill check

skill-verdict: implementation-blueprint — not-applicable: a one-line
scan-window change in one existing function of one file, not new
multi-module structure or a parallel fan-out needing a frozen contract.
skill-verdict: implementation-complexity-coupling-management —
not-applicable: no coupling/cohesion metric crossed a threshold and no
cross-module import direction was introduced; the change narrows an
existing slice expression in place.
skill-verdict: implementation-design-pattern-selection — not-applicable:
no GoF-style pattern was introduced, removed, or reconsidered.
skill-verdict: implementation-performance-data-structure-choice —
not-applicable: no data structure or algorithm choice was made; the
fast-path scan already iterated a list, and the fix only bounds how much
of it is scanned (an O(topN) vs O(n) difference on an already-small,
sub-300-item list, not a performance-motivated decision).

## Acceptance evidence

Executed in this session, from the repo root.

canonical: acceptance: `python3 -m py_compile consult.py tests/test_retrieval_eval.py && echo "SYNTAX OK"` — result:
```
SYNTAX OK
```

canonical: acceptance: `python3 -m pytest test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_spawn_artifact_skill_pairing.py tests/test_retrieval_eval.py -q` — result:
```
40 passed in 36.17s
```

canonical: acceptance: the new regression test
(`tests/test_retrieval_eval.py`'s
`test_fast_path_ignores_declared_phrase_outside_bm25_topn`) run in
isolation against the pre-fix code (`consult.py` stashed back to the
full-`scored` scan) via
`python3 -m pytest tests/test_retrieval_eval.py::HermeticEnrichmentAndFastPathTest::test_fast_path_ignores_declared_phrase_outside_bm25_topn -v` — result:
```
AssertionError: Lists differ: ['low-rank-skill'] != []
FAILED tests/test_retrieval_eval.py::HermeticEnrichmentAndFastPathTest::test_fast_path_ignores_declared_phrase_outside_bm25_topn
1 failed in 22.71s
```
confirming the test discriminates the actual bug; the fix was then
restored via `git stash pop` and the full suite re-run to the passing
result shown above.
