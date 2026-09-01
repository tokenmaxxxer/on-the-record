---
issue: 2982
role: adversarial-review-bcc60aba
author: adversarial-review-bcc60aba
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
loop_state: landed
verdict: fail
upstream:
  - path: PR #3003 (issue-2982/knowledge-management-taxonomy-tagging+test-derivation-d8949284)
    sha: 084dbe8c4b7da8d885cad36165247e3bfbb9a42d
---

# issue-2982 — adversarial-review-bcc60aba record

## What was done

Independently verified PR #3003 (`issue-2982/knowledge-management-taxonomy-tagging+test-derivation-d8949284`,
head `084dbe8c`) against issue #2982's acceptance criteria and must-not
list.

canonical: `gh pr view 3003` output (state: OPEN, base: main, mergeable:
MERGEABLE, headRefOid: `084dbe8c4b7da8d885cad36165247e3bfbb9a42d`). None
of the paths cited below with an `084dbe8c:` prefix exist on this
session's own branch (`issue-2982/adversarial-review-bcc60aba`) — they
were fetched from the PR into an isolated worktree
(`git fetch origin pull/3003/head:pr-3003-verify && git worktree add
/tmp/verify-pr-3003 pr-3003-verify`), read and executed there, and the
worktree was not merged into this branch.

**Acceptance checks, re-run myself in `/tmp/verify-pr-3003`, not taken
from the PR's claim:**

acceptance: `python3 -m pytest tests/ -k skill_candidates_floor -q` — result:
```
7 passed in 0.88s
```
acceptance: `python3 -m pytest tests/ -k skill_candidates_floor_calibrated -q` — result:
```
2 passed in 0.84s
```
acceptance: `python3 -m pytest tests/ -k skill_candidates_regression_cases -q` — result:
```
2 passed in 0.86s
```
All three match the PR's claimed counts (7/2/2).

**Must-not audit** (`git diff main...pr-3003-verify` in the worktree:
`consult.py` +44 lines, `spawn.py` +1 line), each claim read directly
from the diff/files at `084dbe8c` in that worktree:

canonical: `084dbe8c:consult.py` lines 880-887 (the `if not use_judge:`
branch of `rank_skills()`), read directly in `/tmp/verify-pr-3003`.

- Haiku judge NOT made the default fix — confirmed. The
  `_SKILL_CANDIDATES_RELEVANCE_FLOOR` check sits only inside the
  `if not use_judge:` branch of `rank_skills()`; `084dbe8c:spawn.py`
  line 2256 (`--with-judge`) is `action="store_true"`, default `False`,
  so `--skill-candidates`'s default path stays BM25-only.
- `--skill-candidates` does not select on the operator's behalf —
  confirmed. `084dbe8c:spawn.py` lines 2462-2483 only print the
  `rank_skills()` result as JSON and `return 0`; no session/roster/
  board-gate/merge_gate call in that branch.
- spawn's internal cross-family mount unchanged — confirmed.
  `_cross_family_skill_matches_with_consult()` calls
  `_bm25_cross_family_scores()` directly (per the PR's own docstring
  addition at `084dbe8c:consult.py` lines 838-857) and never passes
  through `rank_skills()`, so the floor cannot affect it.
- Floor derived from measurement, not freehand — **see finding below**:
  procedurally yes (a real script ran against the live corpus, and I
  reproduced its output independently), but the derivation does not
  support the number well enough to satisfy the issue's actual concern.

**Independent reproduction of the derivation.** The subject's own record
(`084dbe8c:docs/issue-2982/reports/knowledge-management-taxonomy-tagging+test-derivation-d8949284.md`,
not present on this branch) quotes two `derived:` scripts. I re-ran both
myself in the isolated worktree, not copy-pasted from that record:

```
$ python3 -c '... positive_tasks ... print("min positive top-1 score:", min(scores))'
min positive top-1 score: 16.963157077618174
$ python3 -c '... negative_tasks ... print("max negative top-1 score:", max(scores))'
max negative top-1 score: 15.134316351480953
```
Both match the record to 6+ significant figures (last-digit float noise
only) — the derivation's 7 positive / 6 negative data points are real,
not fabricated, and `16.0` does sit in that measured gap.

**Finding: the floor silently filters out correct candidates — the
specific failure direction the issue named as the risk.** The derivation's
7 positive examples were all hand-written by the same session that chose
the floor, using rich, multi-clause technical vocabulary matching the
target skill's own trigger language closely. I probed with additional
task-shaped queries — full sentences, not degenerate short queries —
against skills chosen at random from the live corpus, and checked whether
each skill's genuine, unambiguous BM25 top-1 rank survived the floor:

```
$ python3 -c '... "define SLA tiers and escalation priority for support tickets" ...'
raw top1: customer-support-sla-tier-priority, score=14.53 (rank 1, correct)
post-floor: outcome=no-candidates (SUPPRESSED — 14.53 < 16.0)

$ python3 -c '... "consolidate and aggregate risk exposure across business units" ...'
raw top1: risk-management-aggregation-consolidation, score=11.19 (rank 1, correct)
post-floor: outcome=no-candidates (SUPPRESSED — 11.19 < 16.0)

$ python3 -c '... "derive the sampling method for this conformance review" ...'
raw top1: conformance-review-sampling-derivation, score=10.53 (rank 1, correct)
post-floor: outcome=no-candidates (SUPPRESSED — 10.53 < 16.0)
```
Full raw-score dumps run in `/tmp/verify-pr-3003` (worktree discarded at
the end of this session) — reproducible by rerunning the three quoted
task strings through `spawn.rank_skills()` in a checkout of PR #3003
against the same skill-repository, `$MUSTER_SKILL_REGISTRY_ROOT`.

canonical: `/home/jwjung/skill-registry/skills/customer-support-sla-tier-priority/SKILL.md`
lines 1-9 (`description:`), read directly — "Use when a ticket needs an
Impact x Urgency Priority tier ... Trigger on requests like ... 'first-response
SLA for this ticket'" — confirms the query/skill pairing above is
topically genuine, not a coincidental token overlap.

In all three cases the correct skill was the unambiguous BM25 top-1 pick
against the full ~270-skill corpus (verified by dumping the raw,
pre-floor ranking via `spawn._bm25_cross_family_scores()` and checking
the expected skill's rank directly, not just its score) — exactly the
"genuinely on-topic top-1 match" category the derivation's positive set
claims bottoms out at 16.963. These three score 10.53-14.53, well under
both the shipped floor (16.0) and the derivation's own claimed positive
floor (16.963). This directly contradicts the derivation record's framing
that the measured gap (15.13-16.96) cleanly separates "genuine top-1
match" from "no on-topic match in the corpus" — it does not generalize
past the 7 examples it was fit to.

This is not a corner case the PR's own tests would catch:
`SkillCandidatesFloorCalibratedTest` (`084dbe8c:tests/test_skill_candidates_floor.py`)
only replays the same 7+6 data points the floor was fit to (mocked
scores, not a live corpus query), so it can only confirm internal
consistency with its own training set, never generalization. The PR's own
before-landing warrant-hunt
(`084dbe8c:docs/issue-2982/reports/knowledge-management-taxonomy-tagging+test-derivation-d8949284/hunt-skill-candidates-floor.md`,
not present on this branch) explicitly probed only the opposite
direction — trying to get a low-confidence match to slip *past* the floor
as a false positive — and found nothing; it did not probe whether the
floor eats true positives, which is the direction issue #2982 and its
consult explicitly flagged as the risk of an uncalibrated floor ("A floor
set too high silently filters out correct candidates").

Practical consequence: an operator running `--skill-candidates` with a
normal, single-clause task description against a real but lexically
sparse skill match (rather than the rich multi-clause phrasing the
derivation set happened to use) will now see `no-candidates` even when a
correct match exists and previously would have surfaced at rank 1 — the
same "fall back on the last name that worked" failure mode issue #2982
opened with, just reached by suppression instead of noise.

## Why

The task asked me to scrutinize whether the derivation actually supports
the number, with the same discipline issue #2961 held its backstop
thresholds to, and to probe specifically for the "floor too high"
direction. I re-ran the acceptance checks and both derivation scripts
myself in an isolated worktree rather than trusting the PR's or the
subject's own record, then went beyond the subject's own positive/negative
set (which is self-consistent by construction, since the floor was fit to
it) with independently chosen task/skill pairs to test whether the
measured gap actually generalizes. It does not: n=7 positive examples,
all authored in one sitting by the party choosing the threshold, is too
thin a sample to establish a corpus-wide floor, and three independently
chosen realistic queries against skills outside that set fell through it
while still being genuine, unambiguous top-1 matches.

## What did not work

An automated sweep using regex-extracted quoted phrases from `SKILL.md`
`description:` frontmatter (intended to scale the probe past hand-picked
examples) produced mostly noisy, non-representative fragments — the
regex caught prose sentence fragments and non-English quotes rather than
clean trigger examples, so its output was not used as evidence. Reverted
to hand-crafted, manually-verified full-sentence task queries instead
(the three cited under Finding, above), each checked against the target
skill's actual `SKILL.md` description before being counted.

## Upstream basis

canonical: `gh pr view 3003 --json headRefOid` output
(`084dbe8c4b7da8d885cad36165247e3bfbb9a42d`) and the
`git worktree add /tmp/verify-pr-3003 pr-3003-verify` fetch, both run
this session.

- PR #3003, head commit `084dbe8c4b7da8d885cad36165247e3bfbb9a42d`
  (`issue-2982/knowledge-management-taxonomy-tagging+test-derivation-d8949284`),
  fetched into `/tmp/verify-pr-3003` for this verification; not merged
  into this branch.
- The subject's own implementation record at that same sha
  (`084dbe8c:docs/issue-2982/reports/knowledge-management-taxonomy-tagging+test-derivation-d8949284.md`),
  whose derivation scripts I independently re-ran rather than citing at
  face value.

## Open findings

- The calibrated relevance floor (`consult._SKILL_CANDIDATES_RELEVANCE_FLOOR = 16.0`)
  suppresses genuine, unambiguous top-1 skill matches for realistic,
  full-sentence task queries outside the 7-example set it was fit to
  (three reproduced above: 14.53, 11.19, 10.53, all well under both the
  shipped floor and the derivation's own claimed 16.963 positive minimum).
  Resolution path: recalibrate against a larger, more diverse sample of
  positive pairs (ideally not all authored by the same session choosing
  the threshold), or replace the single hard cutoff with a design that
  degrades more gracefully than an all-or-nothing floor — before this PR
  lands. This is not a hypothetical edge case; it reproduces on the first
  three realistic queries tried against skills outside the derivation set.

## Next steps

None from this session — verdict and finding are handed back to the
operator/coding session for issue #2982; loop_state is terminal for this
verification record.

skill-verdict: adversarial-review — applied: invoked; loaded the skill's
procedure and applied its core mechanism (structurally independent
evaluator, incentivized to find real problems with cited locations,
blind to the builder's own framing) to audit PR #3003's derivation claim
rather than taking the subject's own record at face value.
other mounted skills: not triggered
