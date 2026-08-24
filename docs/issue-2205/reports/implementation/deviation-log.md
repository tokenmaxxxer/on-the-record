# Deviation log — issue #2205

- 2026-08-24T00:00:00Z | inline | while building the second named-FP
  negative gold case (`work-in-english-declared-phrase-self-inflation-fp`),
  a residual bug surfaced that issue #2166's topN-restricted fast-path
  gate does not cover.
  canonical: `docs/issue-2205/reports/implementation.md` — `## Why`
  A skill's own declared phrase is indexed into its own BM25 document,
  so a task containing that phrase verbatim can push the skill inside
  the top-8 window on the phrase alone (full rank measurement in the
  record's `## Why` section, cited above).
  This sat outside the issue's literal scope (add precision@mount plus
  negatives to the eval), but the acceptance criterion's own wording
  needs an actual retrieval-side change for the `work-in-english` case —
  an eval-only change leaves that one gold case with no way to show the
  required before/after contrast.
  canonical: `docs/issue-2205/reports/implementation.md` — `## Acceptance
  evidence`, the before/after `git-stash` run
  Fixed in `consult.py`'s `_cross_family_skill_matches_with_consult`:
  re-score with the matched phrase stripped from the task text, require
  the skill to independently place inside topN, exempting tasks whose
  stripped residual is too short to judge relevance from at all.
  canonical: `docs/issue-2205/reports/implementation.md` — `## What did
  not work`
  Stays inside this session's write set (no phase-1 proposal froze
  one — build-now bypass); weighed one alternative (stripping quoted
  phrases from the BM25 document globally, rejected there for recall
  risk) but did not change what the eval-metric fix itself claims to
  do, and is a one-off scoped to this one retrieval mechanism. Both
  changes landed together in the same commit, carried by PR #2206.
