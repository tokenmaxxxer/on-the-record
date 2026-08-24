---
issue: 2205
role: implementation
loop_state: landed
upstream:
  - path: docs/issue-2166/reports/implementation.md
    sha: b9cd89af0e6626fa98db53d580c95936d6710f6e
  - path: consult.py
    sha: b9cd89af0e6626fa98db53d580c95936d6710f6e
  - path: tests/data/retrieval_gold.jsonl
    sha: b9cd89af0e6626fa98db53d580c95936d6710f6e
code_under_review:
  - consult.py
  - tests/data/retrieval_gold.jsonl
  - tests/test_retrieval_eval.py
type: fix
breaking: false
verdict: pass
---

# issue-2205 — implementation record

## What was done

canonical: `tests/test_retrieval_eval.py:120-126` (pre-change) — the frozen
assertion loop read `for cid, r8, _mrr, _p, r, _o in rows: if r8 is not
None: ...`. Every `expected: []` (negative) gold row has `r8 is None`
(`recall8 = ... if expected else None`, line 82), so that `if` silently
skipped the assertion on every negative row even though `precision` (`p`)
was already computed per-row at line 98 — Recall@8=1.0 could hold while a
negative case's precision was 0.0 and no assertion would ever fail. This is
the exact blindness issue #2205 names.

Fix, in `tests/test_retrieval_eval.py`:
canonical: `git diff tests/test_retrieval_eval.py` (this commit)
1. Added an `else` branch asserting `self.assertEqual(p, 1.0, ...)` on every
   negative row, and renamed the printed macro line from "final-pick
   precision" to "precision@mount" to match the issue's own vocabulary.
2. Added two new `expected: []` cases to `tests/data/retrieval_gold.jsonl`:
   canonical: `git diff tests/data/retrieval_gold.jsonl` (this commit)
   `issue-525-cross-family-off-domain-fp` (issue-525's real GH body) and
   `work-in-english-declared-phrase-self-inflation-fp` (constructed;
   rationale below).
3. Fixed a second, still-live false-positive mechanism located while
   building case 2 — detail and derivation immediately below.
   canonical: `git diff consult.py` (this commit)

## Why

**Reproducing the two named incidents split into two different outcomes.**

derived: `gh issue view 525 --json body -q .body > /tmp/issue525_body.txt`
then, patched `_installed_plugin_skill_dirs` to `{}` (skill-repo-only
corpus) and called
`spawn._bm25_cross_family_scores(body, "implementation", spawn._skill_repo_root())`
— result:
```
market-analysis-mece-proposal: rank 10 of 269, score 21.506964310806325
work-in-english: rank 13 of 269, score 20.47681772887442
TOPN = 8
```
Both named skills already rank outside `_CROSS_FAMILY_CONSULT_TOPN=8` for
issue-525's real body — matching issue #2166's own investigation result.
canonical: `docs/issue-2166/reports/implementation.md:33-36`
This became gold case `issue-525-cross-family-off-domain-fp`, a permanent
regression guard on the real production text — see `## Acceptance evidence`
for the before/after run showing this row unaffected by the revert both
times.

Checking whether `work-in-english`'s fast path had a residual gap beyond
what #2166 fixed, `_skill_bm25_document` was read next.
canonical: `pipeline.py:1067-1080`
The indexed BM25 document is "name + full frontmatter description + axis",
and the description includes the same quoted phrases
`_skill_declared_phrases` extracts for the fast path.
canonical: `pipeline.py:1087-1101`
So a task containing a skill's own declared phrase verbatim doesn't just
fast-path-match it — it also inflates that skill's BM25 rank, because the
corpus document and the task text now share a long exact n-gram.

derived: constructed a task text about an unrelated database-indexing bug
fix that happens to end with `work-in-english`'s own illustrative trigger
example (`"fix this bug and open a pr"`,
`skill-repository/skills/work-in-english/SKILL.md`), and re-ran
`spawn._bm25_cross_family_scores` against the real corpus — result:
```
market-analysis-mece-proposal rank 168 of 248
work-in-english rank 1 of 248
```
`work-in-english` ranks 1st of 248 for a task with nothing to do with
language policy, comfortably inside `TOPN=8`.
canonical: `consult.py:366`
That line (unchanged by this fix) only rejects a candidate whose rank falls
*outside* topN, so it never fires here; the phrase is *why* the skill is
inside topN in the first place. This became gold case
`work-in-english-declared-phrase-self-inflation-fp`.

**The fix.**
canonical: `consult.py` diff, `_cross_family_skill_matches_with_consult` (this commit)
When a declared-phrase match is found, the matched phrase is stripped out
of the task text and re-scored with `_bm25_cross_family_scores`; the skill
must independently place inside `TOPN` on that phrase-blind text before the
fast-path pick is trusted. Guarded by
`_FAST_PATH_CORROBORATION_MIN_TOKENS=10`
canonical: `consult.py:320`
— this re-score only runs when the phrase-stripped residual still carries
10 or more non-stopword tokens (via `_sp._tokenize`), so a task that is
essentially nothing but the phrase itself is still trusted at full
confidence with no re-score.

derived: measured non-stopword residual-token counts (`pipeline._tokenize`)
after stripping the matched phrase, across the cases that motivate the
threshold — result:
```
synthetic two-phrase fixture (alpha/beta/gamma + delta/epsilon/zeta): 5
dicequest-72-monster-scaling (real gold case, phrase stripped): 26
work-in-english-declared-phrase-self-inflation-fp (phrase stripped): 51
```
Ten sits with headroom below the two real/positive cases and above the
synthetic no-other-content fixture shown just above — the two alternatives
considered and rejected (stripping quoted phrases from the BM25 document
globally; an earlier cut of this check with no residual-length exemption)
are in `## What did not work`.

## What did not work

- First cut of the corroboration check re-scored unconditionally (no
  residual-length exemption) and rejected any skill that fell out of topN
  after stripping.
  canonical: `python3 -m pytest tests/test_retrieval_eval.py test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_spawn_artifact_skill_pairing.py -q`
  against that version — result:
  ```
  FAILED tests/test_retrieval_eval.py::HermeticEnrichmentAndFastPathTest::test_fast_path_filling_cap_skips_judge_entirely
  AssertionError: 'fail-open' != 'fast-path:skill-a,skill-b'
  1 failed, 39 passed in 1.50s
  ```
  Root cause: that fixture's two skills' entire declared content IS their
  trigger phrase, so stripping it left a zero-relevance residual (no shared
  tokens with anything in the tiny 2-skill corpus) and both got rejected,
  falling through to the mocked judge, which the test asserts must never be
  called. Fixed by adding `_FAST_PATH_CORROBORATION_MIN_TOKENS` (thresholds
  measured in `## Why`) so a near-empty residual skips re-scoring — the
  same suite was re-run after the fix (result in `## Acceptance evidence`
  below).
- Rejected alternative: strip quoted phrases from `_skill_bm25_document`
  globally instead of gating the fast path.
  canonical: `tests/data/retrieval_gold.jsonl`'s
  `dicequest-72-monster-scaling` case note
  Its Recall@8 depends on the skill descriptions naming stage/monster/HP
  scaling inside the quoted phrase; stripping quoted text from the indexed
  document globally risks silently regressing recall on real positive
  cases across the full skill corpus. Not re-measured (out of scope per
  issue #2205's own "do not delete or replace the BM25+judge layer"
  instruction) — rejected without executing it.
- Assumed issue-525's real GH body would directly reproduce the
  `work-in-english` fast-path bug end-to-end (not just the BM25-rank
  measurement).
  derived: `gh search issues "fix this bug and open a pr" --repo
  tokenmaxxxer/on-the-record --json number,title,body` and the same with
  `--repo tokenmaxxxer/tm-dicequest` — result both: `[]` (zero hits)
  Reverted `consult.py` to its pre-#2205 state
  (`git diff consult.py > /tmp/consult2205.patch && git checkout --
  consult.py`) and re-ran `spawn._cross_family_skill_matches_with_consult`
  on issue-525's real body with a null judge.
  derived: the same re-run — result: `picked=[]`
  both before and after the revert (`git apply /tmp/consult2205.patch` then
  restored the fix). That specific text is unable to demonstrate a
  fails/succeeds transition, since it never contained a declared phrase;
  the second, constructed gold case supplies that demonstration instead
  (canonical: `## Acceptance evidence` below).

## Upstream basis

Issue #2205 (acceptance criterion) and issue #2166
(`docs/issue-2166/reports/implementation.md`, landed
`b9cd89af0e6626fa98db53d580c95936d6710f6e`) are the primary upstream
inputs.
canonical: `docs/issue-2166/reports/implementation.md:220-234`
#2166 already recorded that a skill-specific live-judge confirmation for
`market-analysis-mece-proposal` was not performed, and that the real
issue-#527/Korean-project session could not be located.
canonical: `docs/issue-2166/reports/implementation.md:235-242`
This session reused #2166's own real-text reproduction (issue-525's body)
as a permanent gold-set case, and located the residual self-inflation gap
while extending that reproduction to `work-in-english` specifically — see
the two `derived:` BM25-rank measurements in `## Why` above.

Build-now bypass (contract v3 s19a, `CORE_BUILD_NOW=1` set by the spawner)
skipped the phase-1 proposal round, so there is no `docs/issue-2205/proposals/*`
file to cite.
derived: `echo "CORE_BUILD_NOW=$CORE_BUILD_NOW"` at session start — result: `CORE_BUILD_NOW=1`

canonical: files read directly in this session — `consult.py`
(`_cross_family_skill_matches_with_consult`, lines 314-420), `pipeline.py`
(`_skill_bm25_document` lines 1067-1080, `_skill_declared_phrases` lines
1087-1101, `_skill_frontmatter_description` lines 1035-1049), `spawn.py`
(`_bm25_cross_family_scores`, `_CROSS_FAMILY_CONSULT_TOPN`, `_tokenize`),
`tests/test_retrieval_eval.py`, `tests/data/retrieval_gold.jsonl`, and the
real `skill-repository` checkout's `work-in-english/SKILL.md` and
`market-analysis-mece-proposal/SKILL.md`.

`sha: same-commit` applies to `consult.py`, `tests/data/retrieval_gold.jsonl`,
and `tests/test_retrieval_eval.py` in `code_under_review` (all land in this
commit); the `upstream:` frontmatter block cites the pre-existing state
each builds on.
derived: `git log --format='%H %ad %s' --date=short -1 -- consult.py` (run
before this session's edits) — result: `b9cd89af0e6626fa98db53d580c95936d6710f6e
2026-08-24 issue-2166: narrow skill-recommender fast path to BM25 top-N
candidates (#2171)`

Scout/survey: skipped — a bounded investigate-then-fix issue with a stated
shape, not an open product/design decision needing option comparison.
canonical: `docs/issue-2166/reports/implementation.md:170-175`
Identical skip reasoning applied there for the same code area.

## Doc placement ladder

- [x] `docs/specs/` — not applicable; no system design changed, no
  `docs/specs/*` file touched (no `spec_index.py --update` needed).
- [x] `docs/decisions/` — not applicable; the fast-path corroboration check
  is a narrow, reversible gating addition, not a hard-to-reverse choice.
- [x] `docs/reports/` — not applicable; no cross-cutting measurement beyond
  what's cited inline above and in the gold-set case notes themselves.
- [x] This implementation record — filled (this file).

## Open findings

- Issue #2205's own plan item 2 ("run skill-creator's should-trigger/
  should-not-trigger tuning") could not be executed.
  derived: checked `~/.claude/plugins/installed_plugins.json` and grepped
  `~/.codex/skills/.system/skill-creator/SKILL.md` and its `scripts/` for
  `trigger|eval|scenario|precision|recall|negative|positive` — result: the
  only plugin installed is `on-the-record@tokenmaxxxer` itself; the one
  `skill-creator` present on disk (Codex-flavored) has zero matches for
  that vocabulary
  No trigger/scenario eval-case machinery exists in this environment.
  Resolution path: install the Anthropic `skill-creator` plugin in a
  session with plugin-install capability, then re-run this step against
  the current skill library.
- Issue #2205's own plan item 3 ("rewrite descriptions from live FP/FN
  cases") is out of this repo's write scope.
  canonical: `docs/issue-2166/reports/implementation.md:131-139`
  Every `SKILL.md` referenced in this record lives in
  `tokenmaxxxer/skill-repository`, a separate repository with its own
  role/branch/PR flow (same boundary recorded there previously).
  Resolution path: a `tokenmaxxxer/skill-repository` session, given this
  record's two live FP/FN cases as its live-case input per arXiv
  2606.30775's method.
- `_FAST_PATH_CORROBORATION_MIN_TOKENS=10` is a measured compromise, not a
  principled boundary.
  derived: residual non-stopword token counts measured in `## Why` above —
  5 (synthetic fixture), 26 (dicequest-72), 51 (the new bug-reproduction
  case)
  A task landing near the threshold with a declared phrase could go either
  way, untested. Resolution path: if a live case surfaces at that
  boundary, add it to `tests/data/retrieval_gold.jsonl` and let the
  regression suite settle the threshold empirically.
- `work-in-english-declared-phrase-self-inflation-fp`'s task text is
  constructed, not a literal historical GH issue.
  canonical: `docs/issue-2166/reports/implementation.md:235-242`
  The real triggering session for the "Korean project" incident (issue
  #527) remains unlocatable; this session's own repeat search (`##
  What did not work` above, zero-hit `gh search issues` result) shows the
  gap is still open. Resolution path: unchanged from #2166's own open
  finding — if the reporting session can supply the actual repo/issue
  pair, replace this case's task text with the literal original.

## Next steps

None — `loop_state: landed` (terminal for a `coding-record`).
canonical: `## Acceptance evidence` below
The fix, the two new gold-set negatives, the precision@mount assertion,
and this record are committed, pushed, and carried in the phase-2 delivery
PR for issue #2205.

## Skill check

skill-verdict: implementation-performance-data-structure-choice — applied: invoked; reviewed the added full-corpus BM25 rescore
(`_bm25_cross_family_scores` over ~269 skills) inside the fast-path's
declared-phrase-match branch against the skill's Rule 3 (measure actual
per-element cost, not asymptotic class alone).
canonical: `test/test_spawn_cross_family_skill_selection.py:492`
That timing-budget test still runs clean with this change (full command in
`## Acceptance evidence` below). A per-skill-only rescore cannot answer
"does this skill still rank inside topN" without comparing against the
rest of the corpus, so a full rescore is the minimum computation that
answers the question, and it only runs on the already-rare phrase-match
path. Kept as scoped.
skill-verdict: implementation-blueprint — not-applicable: a scoped,
mostly-single-function change to one existing retrieval-pipeline function
plus gold data, not new multi-module structure or a parallel fan-out
needing a frozen contract.
skill-verdict: implementation-complexity-coupling-management —
not-applicable: no coupling/cohesion metric crossed a threshold, no
accessor-chain caller was introduced, and no cross-module import direction
changed.
skill-verdict: implementation-design-pattern-selection — not-applicable: no
GoF-style pattern was introduced, removed, or reconsidered — the change adds
one conditional re-scoring branch to an existing procedural function.

## Acceptance evidence

Executed in this session, from the repo root.

canonical: acceptance: `python3 -m py_compile consult.py tests/test_retrieval_eval.py && echo "SYNTAX OK"` — result:
```
SYNTAX OK
```

canonical: acceptance: `python3 -m pytest test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_spawn_artifact_skill_pairing.py tests/test_retrieval_eval.py -q` (fixed/current code) — result:
```
40 passed in 3.28s
```

canonical: acceptance: `python3 -m pytest tests/test_retrieval_eval.py::RetrievalEvalTest::test_bm25_recall_at_8_and_final_pick_metrics -v -s -n0` (fixed/current code) — result:
```
case                                     R@8   MRR     P     R  outcome
dicequest-72-monster-scaling            1.00 1.00  1.00  1.00  fast-path:game-growth-system-design+completed
fixture-version-flag                       - 0.00  1.00  1.00  completed
otr-2068-returned-pr-respawn               - 0.00  1.00  1.00  completed
otr-2100-admission-checklist               - 0.00  1.00  1.00  completed
otr-2101-watch-hardening                   - 0.00  1.00  1.00  completed
otr-2102-directive-diet                    - 0.00  1.00  1.00  completed
otr-2103-board-read-efficiency             - 0.00  1.00  1.00  completed
dicequest-upgrade-cost-curve            1.00 0.50  1.00  1.00  fast-path:game-growth-system-design+completed
dicequest-hp-bar-colorblind             1.00 1.00  1.00  1.00  completed
release-semver-changelog                1.00 1.00  1.00  1.00  completed
issue-525-cross-family-off-domain-fp       - 0.00  1.00  1.00  completed
work-in-english-declared-phrase-self-inflation-fp     - 0.00  1.00  1.00  completed
macro (non-empty n=4): Recall@8=1.000 MRR=0.875 | precision@mount (all n=12)=1.000
1 passed
```
`precision@mount (all n=12)=1.000` and `Recall@8=1.000` (unchanged on the 4
pre-existing non-empty gold cases) are both shown in the table above — the
regression guard.

canonical: acceptance, the acceptance-required current-fails/fixed-passes
demonstration: `git diff consult.py > /tmp/consult2205.patch && git
checkout -- consult.py` (reverts `consult.py` to pre-#2205, i.e. #2166's
landed state) then
`python3 -m pytest tests/test_retrieval_eval.py::RetrievalEvalTest::test_bm25_recall_at_8_and_final_pick_metrics -v -s -n0`
— result, current/pre-#2205 selection:
```
work-in-english-declared-phrase-self-inflation-fp     - 0.00  0.00  1.00  fast-path:work-in-english+completed
macro (non-empty n=4): Recall@8=1.000 MRR=0.875 | precision@mount (all n=12)=0.917
AssertionError: 0.0 != 1.0 : precision@mount < 1.0 for negative case work-in-english-declared-phrase-self-inflation-fp — the real pipeline mounted a skill that should not apply
1 failed in 0.58s
```
The assertion fires and the run exits non-zero — this is the required
"current selection fails" half of the acceptance criterion.

Then `git apply /tmp/consult2205.patch` restored the fix and the identical
command was re-run — result, fixed/current selection:
```
work-in-english-declared-phrase-self-inflation-fp     - 0.00  1.00  1.00  completed
macro (non-empty n=4): Recall@8=1.000 MRR=0.875 | precision@mount (all n=12)=1.000
1 passed in 0.65s
```
The assertion holds and the run exits zero — this is the "fixed selection
succeeds" half of the acceptance criterion.

`issue-525-cross-family-off-domain-fp` (the other named negative) is
present and unaffected (identical row, zero-mount outcome, precision 1.00)
in both tables above. Per `## Why`/`## What did not work` its real text never
contained a declared phrase, so it functions as a stable regression guard
rather than the fails/succeeds transition; that transition, required by
the acceptance criterion, is the
`work-in-english-declared-phrase-self-inflation-fp` result shown
immediately above, which directly implicates the second named skill,
`work-in-english`.
