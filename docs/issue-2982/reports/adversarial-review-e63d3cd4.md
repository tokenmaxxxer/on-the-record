---
issue: 2982
role: adversarial-review-e63d3cd4
author: adversarial-review-e63d3cd4
skills: adversarial-review, defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12))
verifies_subject: true  # this record independently re-verifies PR #3011's recalibration of PR #3003's deliverable for issue #2982
loop_state: landed
verdict: fail
upstream:
  - path: PR #3011 (issue-2982/silent-failure-audit-68344f70)
    sha: b0efb53aaa9e594c5002d894b8e74d2f5749caa3
  - path: docs/issue-2982/reports/silent-failure-audit-68344f70.md (recalibration record, floor 16.0 -> 4.0)
    sha: b0efb53aaa9e594c5002d894b8e74d2f5749caa3
  - path: docs/issue-2982/reports/adversarial-review-bcc60aba.md (PR #3007, verdict fail)
    sha: 0de957736e9efd941da3393c6b1725f66775ed13
  - path: docs/issue-2982/reports/adversarial-review-4a0acec2.md (PR #3009, verdict fail)
    sha: 4ff13becad426e49d304d076dc64d07531ffbb75
---

# issue-2982 — adversarial-review-e63d3cd4 record

## What was done

Independently re-verified PR #3011 (`issue-2982/silent-failure-audit-68344f70`)
in an isolated git worktree separate from this session's own checkout.

canonical: `gh pr view 3011 --repo tokenmaxxxer/on-the-record` output, read
this session (state: OPEN, title "issue-2982: re-derive skill-candidates
relevance floor from real operator selections", supersedes PR #3003 and
carries its commits merged in per PR #3011's own description).

derived: `git fetch origin pull/3011/head:pr-3011-verify && git worktree
add /tmp/verify-3011 pr-3011-verify` then `git rev-parse HEAD` inside
`/tmp/verify-3011` — result:
```
b0efb53aaa9e594c5002d894b8e74d2f5749caa3
```
This session's own checkout (`issue-2982/adversarial-review-e63d3cd4`) was
never modified — every command below ran with `cd /tmp/verify-3011`.

**1. The three acceptance checks, reproduced live in the isolated worktree:**

acceptance: `python3 -m pytest tests/ -k skill_candidates_floor -q` — result:
```
11 passed in 0.97s
```
acceptance: `python3 -m pytest tests/ -k skill_candidates_floor_calibrated -q` — result:
```
2 passed in 1.13s
```
acceptance: `python3 -m pytest tests/ -k skill_candidates_regression_cases -q` — result:
```
5 passed in 1.18s
```
All three requirements issue #2982 names are met by this test run.

**2. PR #3007/#3009's false-suppression finding is genuinely fixed —
confirmed live against the corpus, not by re-citing either record.** The
shipped floor:

derived: `grep -n _SKILL_CANDIDATES_RELEVANCE_FLOOR consult.py`, run in
`/tmp/verify-3011` — result:
```
consult.py:106:_SKILL_CANDIDATES_RELEVANCE_FLOOR = 4.0
```
All 5 previously-suppressed genuine matches from PR #3007
(`0de95773:docs/issue-2982/reports/adversarial-review-bcc60aba.md`) and
PR #3009 (`4ff13bec:docs/issue-2982/reports/adversarial-review-4a0acec2.md`)
were replayed live against today's corpus via `spawn.rank_skills(q,
"candidates", repo_root, use_judge=False)`, in `/tmp/verify-3011`:

derived:
```
$ python3 -c "...replay of 5 queries through spawn.rank_skills()..."
14.53(PR3007 SLA-tier task)         -> live top1 score=14.529 name=customer-support-sla-tier-priority        outcome=bm25-only
11.19(PR3007 risk-aggregation task) -> live top1 score=11.186 name=risk-management-aggregation-consolidation outcome=bm25-only
10.53(PR3007 conformance task)      -> live top1 score=10.531 name=conformance-review-sampling-derivation    outcome=bm25-only
11.46(PR3009 test-coverage task)    -> live top1 score=11.459 name=test-depth-audit                          outcome=bm25-only
13.87(PR3009 taxonomy task)         -> live top1 score=13.870 name=knowledge-management-taxonomy-tagging     outcome=bm25-only
```
All 5 (derived count from the code fence above) now correctly survive as
`bm25-only` instead of being suppressed to `no-candidates` — this part
of the recalibration is real and independently reproduced, not merely
re-cited from the record.

**3. The overlap claim is independently reproducible from a fresh query
set this review wrote, not the record's own numbers.** Ten short,
realistic, negative-shaped coding-task descriptions — none copied from
any prior record in this issue's history — were scored against the live
corpus in `/tmp/verify-3011`:

derived:
```
$ python3 -c "...for q in [10 fresh task-shaped queries]: print(top1_score, top1_name, q)"
 10.379  api-design-payload-design                           fix an off-by-one error in the pagination loop...
  7.265  legal-compliance-license-compatibility               add a retry with exponential backoff...
  8.555  finance-unit-economics-sensitivity-scenario          rename the internal variable foo to bar...
  7.081  content-strategy-content-audit-and-inventory         debug why the docker container exits immediately...
 11.119  upstream-defect-report-comprehensibility             write a bash script that tails a log file...
  6.019  devrel-channel-convention                            convert this synchronous function to use asyncio...
  9.866  premortem                                            investigate why the unit test for the parser...
 10.371  release-engineering-changelog-entry-categorization   update the changelog for the upcoming release...
  5.981  conformance-review-finding-record                    fix a memory leak caused by an event listener...
  8.275  upstream-defect-report-convention                    reorder the columns in this CSV export...
```
All 10 (derived count from the code fence above) land in the 5.98-11.12
range — above the 4.0 floor by a margin of `5.981 - 4.0 = 1.981` at the
closest — and every top-1 is a confidently-wrong, unrelated skill for the
stated task (an off-by-one pagination bug does not need
`api-design-payload-design`; a retry/backoff task does not need
`legal-compliance-license-compatibility`). None of the 10 is suppressed.
This range overlaps the record's own claimed "genuine positive" range
(`b0efb53a:tests/test_skill_candidates_floor.py:115-123`,
`REAL_POSITIVE_TOP1_SCORES`, 7.62-13.79 lowest-to-highest) — independent
confirmation that BM25 score alone does not separate on-topic from
off-topic on this corpus, a limitation the record's own
`SkillCandidatesFloorKnownLimitationTest`
(`b0efb53a:tests/test_skill_candidates_floor.py:152-177`) already names.

A stopword-only, near-content-free query was also tried:
derived: `python3 -c "...spawn._bm25_cross_family_scores('the the the and or but', ...)"`, run in `/tmp/verify-3011` — result:
```
(5.974592498508469, 'kubernetes-workload-probe-selection', ...)
```
Even a query with no real content words scores above the 4.0 floor.
Pure gibberish with no dictionary tokens at all (e.g. `"asdf qwer zxcv"`)
returns an empty `scored` list, which already hits the pre-existing
`if not scored` branch that predates this issue — not a check this
issue's floor added.

**4. The floor does almost nothing against the issue's actual complaint,
and this is understated in the record.** Issue #2982's stated complaint
is "the command returns confident-looking unrelated skills." Against
that complaint, floor=4.0 does essentially nothing:

derived: the 10-query replay in finding 3 above (same command, same
section, quoted verbatim there) shows every one of the 10 realistic
queries scoring clear of the floor and each still returning a single
confident wrong top-1 as `bm25-only`. The only inputs the floor actually
catches are (a) the two literal near-zero scores originally reported in
the issue (0.4325, 1.3324 — see the derived CLI output immediately below
for what these two cases now score) and (b) inputs with no scored
candidates at all, which were already `no-candidates` before this issue
existed.

And (a) no longer occurs on today's corpus — the issue's own two
headline example queries, replayed live in this same worktree:

derived:
```
$ python3 spawn.py --skill-candidates "rewrite the workspace preservation predicate in lifecycle.py from git-status-based to what-would-be-lost — unpushed commits, stash, merge/rebase state, untracked classification via git check-ignore"
```
result (top of `ranked`, `outcome` field):
```
{"name": "agent-coordination", "score": 15.134316351480953, ...}
"outcome": "bm25-only"
```
derived:
```
$ python3 spawn.py --skill-candidates "remove the 200-turn session cap, replace with wall-clock/token backstops and an observe-only runaway signal reusing trajectory_analyzer"
```
result (top of `ranked`, `outcome` field):
```
{"name": "secure-coding-session-authentication", "score": 7.911048066340095, ...}
"outcome": "bm25-only"
```
Both score above the 4.0 floor and both remain `bm25-only`, each now
returning a *different* but equally unrelated top-1 (`agent-coordination`,
`secure-coding-session-authentication`) instead of the originally-named
ones (`market-analysis-competitor-mapping` / `tech-feasibility`, etc).
This is the live behavior of the shipped code today, reproduced directly
above via the actual CLI (`spawn.py --skill-candidates`), not via any
mocked test.

This connects to something the record already contains but never names:
`SkillCandidatesFloorKnownLimitationTest.MID_BAND_PLAUSIBLE_BUT_WRONG_SCORES`
(`b0efb53a:tests/test_skill_candidates_floor.py:165-167`) hardcodes
`7.911048066340095` and `15.134316351480955` — identical, to the last
decimal, to the live scores this review just reproduced above (the two
derived CLI blocks in this same finding) for the issue's own two
headline queries — but its comments label them only as generic
"off-topic probe" scores, never connecting them to the fact that they are
the *current* live behavior of the same two cases
`SkillCandidatesRegressionCasesTest`
(`b0efb53a:tests/test_skill_candidates_floor.py:195-221`) claims, via
hardcoded scores of 0.4325 and 1.3324 (quoted directly from that file,
same commit), to be "must-suppress" fixtures. Read side by side, the same
two queries reach opposite conclusions in the same test file: one class
says "suppressed" (via a frozen, mocked score), the other says "not
suppressed, and that's an accepted limitation" (via the current, real
score) — and neither the test file's comments nor PR #3011's description
draws that connection.
`SkillCandidatesRegressionCasesTest`'s own docstring
(`b0efb53a:tests/test_skill_candidates_floor.py:180-186`) does disclose
that "a live rerun drifts as the ... corpus grows," so the drift itself
is not hidden — but the practical consequence demonstrated by the two
derived CLI blocks above, that the issue's own two named examples no
longer reproduce their intended fix against the live system, is not
stated anywhere in
`b0efb53a:docs/issue-2982/reports/silent-failure-audit-68344f70.md`
or in PR #3011's description
(canonical: `gh pr view 3011 --repo tokenmaxxxer/on-the-record`, read
this session, quoted under `## What was done` above).

## Why

canonical: this turn's own acceptance-check transcript (finding 1 under
`## What was done` above, all three checks green, quoted verbatim there)
and this turn's own derived CLI transcripts (findings 2-4 above).

Per `defect-verification-independence-from-upstream-verdicts`, this
review did not take PR #3011's "overlap exists, floor 4.0 is a
conservative bound" framing at face value from its own record, and did
not stop once the three acceptance checks above were confirmed green. It
re-derived the overlap from a query set this session wrote fresh (not
`REAL_POSITIVE_TOP1_SCORES`, not PR #3007/#3009's numbers) specifically
to avoid reproducing the prior derivation's own selection bias, and it
re-ran the issue's original two headline queries against today's live
corpus through the actual CLI rather than trusting the frozen-snapshot
regression fixture. That last step — an edge case beyond the happy-path
acceptance re-run — is what surfaced finding 4 above.

## Upstream basis

canonical: `gh pr view 3011 --repo tokenmaxxxer/on-the-record`, read this
session — head `b0efb53aaa9e594c5002d894b8e74d2f5749caa3`,
`issue-2982/silent-failure-audit-68344f70`, includes PR #3003's original
commits merged in per its own description.

- PR #3011 (`b0efb53a`) — the recalibration under review, including
  `consult.py` (`_SKILL_CANDIDATES_RELEVANCE_FLOOR = 4.0`,
  `b0efb53a:consult.py:106`) and
  `b0efb53a:tests/test_skill_candidates_floor.py`, both read directly in
  the isolated worktree, not cited from any prior record.
- `b0efb53a:docs/issue-2982/reports/silent-failure-audit-68344f70.md` —
  PR #3011's own derivation record, read directly for the claims
  re-derived above.
- PR #3007 (`0de95773:docs/issue-2982/reports/adversarial-review-bcc60aba.md`,
  verdict fail) and PR #3009
  (`4ff13bec:docs/issue-2982/reports/adversarial-review-4a0acec2.md`,
  verdict fail) — the two prior independent verifications whose 5
  reproduction cases were re-confirmed fixed in finding 2 above.

## Open findings

canonical: findings 3 and 4 under `## What was done` above (this
session's own live command output, `/tmp/verify-3011`, quoted verbatim
there) — restated here as open items, not re-derived a second time.

1. **Floor=4.0 does not meaningfully address issue #2982's actual
   complaint.** All 10 of the independently-chosen realistic task
   queries in finding 3 score above the floor and each still returns a
   confidently-wrong single top-1 as `bm25-only` — see finding 3's
   derived code fence for the full command and per-query scores.
   Resolution path: the same one PR #3011's own open findings already
   name and decline to attempt in scope — a relative signal (margin
   between top-1 and top-2, or a different feature entirely) rather than
   an absolute BM25-score cutoff, since finding 3 shows no single cutoff
   separates the classes on this corpus. Not attempted here either —
   this is a verification record, not a fix.
2. **The issue's own two headline example queries no longer reproduce
   their intended suppression against today's live corpus.** Confirmed
   live via the actual CLI in finding 4's two derived code fences above,
   and shown there to be the exact score values (`7.911048066340095`,
   `15.134316351480955`) the record's own
   `SkillCandidatesFloorKnownLimitationTest` already contains under a
   different framing. Resolution path: either re-derive the
   `SkillCandidatesRegressionCasesTest` "must-suppress" fixtures
   periodically against the live corpus, or state plainly in the
   record/PR body that they are frozen historical snapshots that no
   longer reflect current live behavior — canonical: neither is present
   in `b0efb53a:docs/issue-2982/reports/silent-failure-audit-68344f70.md`,
   read in full this session.

## Next steps

canonical: this record's own frontmatter (`loop_state: landed`,
`verdict: fail`), set from the acceptance/derived evidence under `## What
was done` above — this turn's own transcript, not a prior record's claim.

None from this record itself — this is a completed verification pass,
not an in-progress fix. A fix for the two open findings above, if
pursued, is a follow-up session's work.

skill-verdict: adversarial-review — applied: invoked; used to receive PR
#3011's deliverable and re-derive its central calibration claim (the
positive/negative score overlap) from a fresh, self-authored query set
in `/tmp/verify-3011` rather than accepting the record's own "conservative
bound" framing at face value, surfacing findings 3-4 above.
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; re-ran PR #3007/#3009's reproduction queries live in `/tmp/verify-3011` (see finding 2's derived block) rather than citing their reported scores, and separately probed a fresh negative-query set plus the issue's own two original queries against today's corpus (findings 3-4's derived blocks) rather than stopping once the three named acceptance checks in `## What was done` finding 1 above were confirmed green.
skill-verdict: verify-finding-record — not-applicable: this session's designated record location is fixed by the adversarial-review role-handoff contract to `docs/issue-2982/reports/adversarial-review-e63d3cd4.md`, not a fresh `docs/issue-<n>/reports/defect-verification.md` reproduction-attempt file this skill's output shape targets.
skill-verdict: work-in-english — applied: invoked; this record, all commands, and the commit/PR are written in English; only the final user-facing summary is in Korean.
