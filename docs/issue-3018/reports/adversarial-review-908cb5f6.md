---
issue: 3018
role: adversarial-review-908cb5f6
author: adversarial-review-908cb5f6
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3036's deliverable
code_under_review: b4cba7ddf3b792d14d940bf51fc328cbce6cc96d (PR #3036 head; consult.py, spawn.py, tests/test_skill_candidates_signal.py, tests/test_skill_candidates_false_positive_rate.py)
type: verification
breaking: false
verdict: pass-with-reservation
loop_state: terminal
upstream:
  - path: docs/issue-3018/reports/knowledge-management-taxonomy-tagging+test-derivation-66e9bdc2.md
    sha: 3622388b763123a12a7b83c003ad7d2dd0af3299
---

# issue-3018 — adversarial-review-908cb5f6 record

## What was done

Independent verification of PR #3036 (issue #3018, top1/top2 margin signal
for `--skill-candidates`). Fetched the PR head into an isolated worktree
(`git fetch origin pull/3036/head:pr-3036-review && git worktree add
/tmp/pr3036-review pr-3036-review`, HEAD `b4cba7dd`), re-ran the three
issue-mandated acceptance checks there, audited the diff against all four
of the issue's `must not` items, and independently measured the PR's
central effect claim against a query set I authored myself (not the PR's
13 queries, not any prior record's queries). Note: `/tmp/pr3036-review/...`
paths below are the fetched PR worktree, not this branch — this branch has
no code changes of its own, only this verification record.

**Acceptance checks — all three pass, executed live in the isolated worktree:**

checked: `cd /tmp/pr3036-review && python3 -m pytest tests/ -k skill_candidates_signal -q` — result: 10 passed
checked: `cd /tmp/pr3036-review && python3 -m pytest tests/ -k skill_candidates_false_positive_rate -q` — result: 2 passed
checked: `cd /tmp/pr3036-review && python3 -m pytest tests/ -k skill_candidates_regression_cases -q` — result: 5 passed
checked: `cd /tmp/pr3036-review && python3 -m pytest tests/test_skill_candidates_floor.py -q` (pre-existing file, untouched by this PR's diff) — result: 11 passed

derived: `cd /tmp/pr3036-review && git diff main...HEAD --stat`:
```
 consult.py                                         |  65 ++++++
 .../knowledge-management-.../...-66e9bdc2.md        | 225 +++++++++++++++++++
 .../deviation-log/20260901T...-48357133f0368cd6.md   |   1 +
 spawn.py                                           |   1 +
 tests/test_skill_candidates_false_positive_rate.py | 124 +++++++++++
 tests/test_skill_candidates_signal.py              | 238 +++++++++++++++++++++
 6 files changed, 654 insertions(+)
```
`test_skill_candidates_floor.py` is absent from that list — the regression
suite it hosts is untouched by this PR, confirming the 11 passed above is
against pre-existing, unmodified test code.

**Must-not audit (all four hold), each checked against the diff, not the
PR's own claims:**

- Relevance floor not raised: derived: `cd /tmp/pr3036-review && git diff
  main...HEAD -- consult.py` shows `_SKILL_CANDIDATES_RELEVANCE_FLOOR = 4.0`
  unchanged — the diff only adds a new, separate constant
  (`_SKILL_CANDIDATES_MARGIN_FLOOR = 0.1`) and a new branch in
  `rank_skills()`; the floor's own comparison (`scored[0][0] <
  _SKILL_CANDIDATES_RELEVANCE_FLOOR` → `"no-candidates"`) is untouched.
- Evaluation queries not authored by the delivering session: the 13-query
  fixture in `/tmp/pr3036-review/tests/test_skill_candidates_false_positive_rate.py`
  and `/tmp/pr3036-review/tests/test_skill_candidates_signal.py` claims
  provenance from PRs #3015/#3016's records. Verified directly, not taken
  on the PR's word:
  checked: `grep -n "off-by-one\|exponential backoff\|rename the
  internal\|docker container\|tails a log\|asyncio\|unit test for the
  parser\|changelog for the upcoming\|memory leak\|CSV export"
  docs/issue-2982/reports/adversarial-review-e63d3cd4.md` — result: all 10
  queries found verbatim at lines 95-104 of that record (PR #3015).
  checked: `grep -n "clean this"
  docs/issue-2982/reports/adversarial-review-fc5c800d.md` — result:
```
148:feature"` → `legal-compliance-retention-minimization` (6.43), `"clean this
```
  — `"fix this bug"`, `"add a new feature"`, `"clean this up"` are quoted
  verbatim in that record's own false-positive measurement (PR #3016).
  Provenance claim holds — this is exactly the failure mode issue #2982's
  first derivation had (session-authored queries), and PR #3036 avoided it.
- `--skill-candidates` does not select on the operator's behalf: derived:
  read `/tmp/pr3036-review/spawn.py:2501-2521` (the `a.skill_candidates`
  CLI branch) — it calls `rank_skills()` and prints `{"task": ..., "issue":
  ..., **result}` verbatim; no new branch added by this PR interprets or
  resolves `outcome: "ambiguous"` — the operator sees `ranked` populated
  and `picked: []`, same shape as the pre-existing `"bm25-only"`/
  `"no-candidates"` outcomes, and decides themselves.
- Landed floor not removed: confirmed by the same `consult.py` diff read
  above — `_SKILL_CANDIDATES_RELEVANCE_FLOOR` and its comparison branch
  are present and unmodified.

## Why

The two judgment calls the task asked for needed evidence beyond the PR's
own record, so I gathered my own before forming either verdict.

**(1) Scope — defensible slice or inversion?** The issue's Direction
(consult, 2026-09-01T06:37:25Z, read via `gh issue view 3018` this
session) explicitly orders three interventions by "cost against measured
effect":
```
First — trigger-document expansion. The measured failure is surface
vocabulary mismatch between skill trigger text and implementation-task
phrasing. Adding task-shaped sentences to trigger documents attacks that
directly, needs no new dependency, and raises recall rather than
reordering what was already retrieved.
Second — fix the haiku judge's operational failure. The judge path
already exists but timed out at ~44s repeatedly during this session's own
spawns, falling open to BM25 every time. A reranker that is usually
absent cannot be assessed as a reranker.
```
and separately, unordered, names a fourth item the consult calls
something "none of them substitute for" — "stop forcing a top-1 return."
PR #3036 delivers only that fourth item and explicitly defers all three
ordered ones (its own PR description: "trigger-document expansion and the
haiku judge's timeout fix ... are not attempted here").

In isolation the delivered piece is defensible: it's honestly scoped,
fully tested, doesn't violate any must-not, and the consult itself says no
other item substitutes for it. But the consult ordered 1 and 2 first
specifically because they were assessed to target the measured cause
(vocabulary mismatch) at low cost, and PR #3036 skips both of the
cost-effective, cause-targeting interventions in favor of the fourth,
unordered item — which section (2) below measures (derived:
`/tmp/my_verify_queries.py` run, `19/20 → 18/20`, `95.0% - 90.0% = 5.0%`)
to have only a 5-point effect on the issue's headline number. The design
change was never numbered 1-2-3 by the consult — it sits outside that
cost/effect ordering entirely, which means deferring 1 and 2 to deliver it
is not a choice the ordering itself supports. **Verdict: defensible as an
isolated, honestly-scoped contribution, but an inversion of the consult's
stated cost-against-effect ordering** — the two cheap, cause-targeting
fixes were passed over for the one change section (2) shows moves the
metric least.

**(2) Effect — does this touch the reported 89% failure?** The PR's own
record discloses a modest effect honestly: 13/13 (100%) → 11/13 (84.6%) on
its own fixture, explicitly framed as "not a claim that the residual
failure is solved." I did not take that framing on trust — I built an
independent 20-query set (realistic unrelated coding/ops tasks, none
overlapping the PR's 13, none drawn from any prior record) and ran both
the "before" check (`spawn._bm25_cross_family_scores(...)[0][0] >=
_SKILL_CANDIDATES_RELEVANCE_FLOOR`, reproducing pre-issue behavior
exactly) and the "after" check (`spawn.rank_skills(...)["outcome"] ==
"bm25-only"`, the shipped code) live against the corpus on disk in the
fetched worktree:

derived: `cd /tmp/pr3036-review && python3 /tmp/my_verify_queries.py`
(script written this session; 20 queries: "add unit tests for the login
form validation", "optimize the SQL query that's causing slow page
loads", "set up a GitHub Actions workflow for linting", "write
documentation for the new CLI flag", "refactor the payment processing
module to use dependency injection", "fix the flaky end-to-end test in
checkout flow", "add dark mode support to the settings page", "migrate
the database from MySQL to Postgres", "implement rate limiting on the API
endpoints", "resolve merge conflicts in the release branch", "write a
Dockerfile for the microservice", "add input sanitization to prevent
XSS", "improve error messages returned by the REST API", "cache the
results of the expensive computation", "translate the UI strings to
Spanish", "profile the app to find the memory bottleneck", "add
pagination to the search results endpoint", "write a script to
bulk-update user records", "set up monitoring alerts for high latency",
"review the pull request for the auth refactor"):
```
BEFORE: 19/20 = 95.0%
AFTER:  18/20 = 90.0%
```
Only 1 of 20 queries ("migrate the database from MySQL to Postgres", top1
margin small enough to cross `_SKILL_CANDIDATES_MARGIN_FLOOR`) moved from
confident-wrong-top-1 to `"ambiguous"`. The other 18 — including clear
misses like `"write documentation for the new CLI flag"` →
`implementation-blueprint` (score 7.32) and `"add dark mode support to the
settings page"` → `api-design-payload-design` (score 8.98) — kept a
confident top-1 both before and after, because their top1/top2 margins
were comfortably above `0.1`, not near-ties.

This confirms exactly what the spawning task anticipated: the margin
signal converts only near-ties. On my independently sourced set the
reduction is 5 percentage points (95.0%-90.0%=5.0%), smaller than the
PR's own 15.4-point figure on its 13-query fixture (`(13-11)/13 = 15.4%`)
— both point the same direction. **The issue's reported failure (89%
confident-wrong-top-1) remains almost entirely present after this
change.** The PR does not claim otherwise in its own record, but a reader
who only checks the three `pytest -k` acceptance commands (which pass,
correctly) would not learn how small the reachable slice is without also
reading the record's "Open findings" section or, as done here,
re-measuring independently.

## Upstream basis

- PR #3036, HEAD `b4cba7dd` (fetched via `git fetch origin
  pull/3036/head:pr-3036-review`, reviewed in worktree
  `/tmp/pr3036-review`).
- `/tmp/pr3036-review/docs/issue-3018/reports/knowledge-management-taxonomy-tagging+test-derivation-66e9bdc2.md`
  (PR #3036's own delivery record, in the fetched worktree) — read for its
  claims, but every claim checked here was re-derived independently
  (acceptance checks re-run, query provenance re-grepped against the cited
  source records, effect re-measured against a self-authored query set)
  rather than cited on trust.
- `gh issue view 3018` (issue body + Direction consult, both read live this
  session).

## What did not work

None — read-only verification pass. derived: this session's own commands
above (`git fetch`/`git worktree add`, the four `pytest` runs, the two
`grep` provenance checks, `python3 /tmp/my_verify_queries.py`) — no
repository file was written or reverted this session other than this
record itself.

## Open findings

- The margin signal's practical reach on the issue's core complaint is
  small (5-15% of confidently-wrong unrelated queries, by two independent
  measurements — this session's 5.0 points and the PR's own 15.4 points
  quoted under "Why" (2) above) and the two Direction items ordered first
  specifically because they target the measured cause (trigger-document
  expansion, judge timeout fix) remain undone. Resolution path: already
  named in the PR's own record's "Next steps" section; this finding does
  not disagree with that list, only underscores from independent
  measurement that it is not optional follow-through — it is where the
  actual fix lives.
- No must-not violations found (see "What was done" must-not audit above).
  No regressions found in `test_skill_candidates_floor.py` — derived: `cd
  /tmp/pr3036-review && python3 -m pytest tests/test_skill_candidates_floor.py -q`
  — result: 11 passed, file absent from this PR's diff (quoted under "What
  was done" above).

## Next steps

None from this record — verification is terminal. The issue itself stays
open pending Direction priorities 1 (trigger-document expansion) and 2
(judge timeout fix), which is where subsequent work should land per both
the consult and this verification's effect measurement.

skill-verdict: adversarial-review — applied: invoked; loaded via the Skill
tool after this record's first landing (see deviation log,
`20260901T070414358274-65c92070ff521aa9.md`) — the skill's own "does this
even need the procedure" gate says the blind two-session artifact-only
protocol (Steps 1-3) does not fit a task that requires spec/must-not
knowledge to do its job (this task needed the issue's Direction and
must-not list to check compliance), so the formal blind sub-protocol was
not run. What was applied is the skill's core mechanism at the session
level: this session is structurally independent from PR #3036's building
session (no shared context, artifact received only via `gh`/`git fetch`),
incentivized to find real problems rather than defend the work, and
required every claim to cite a specific, re-derivable location — which is
how the acceptance re-runs, must-not audit, and the independent 20-query
effect measurement above were produced, rather than citing PR #3036's own
record on trust.
other mounted skills: not triggered (work-in-english,
defect-verification-independence-from-upstream-verdicts,
implementation-audit — none invoked via the Skill tool this session).
