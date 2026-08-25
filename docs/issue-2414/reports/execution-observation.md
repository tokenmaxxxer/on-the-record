---
issue: 2414
role: execution-observation
author: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2414/reports/implementation.md
    sha: 2019bf3be0f0404e6b05e753eba5f1991bb54c34
  - path: gates/acceptance_gate.py
    sha: 2019bf3be0f0404e6b05e753eba5f1991bb54c34
  - path: gates/requirement_met.py
    sha: 2019bf3be0f0404e6b05e753eba5f1991bb54c34
subject: PR #2422 (issue-2414/implementation, "measure same-shape
  follow-up defect rate, offer scoped negative-criteria/
  convergence-evidence checks (superseded by #2415)"), commit 2019bf3b
  (HEAD), branch issue-2414/implementation, checked out into an
  independent git worktree at /tmp/wt-2414-impl (untracked in this tree,
  removed after this observation)
test: independent re-derivation of issue-2414's Acceptance checks 1
  (A/B distinct-shape confirmation), 2 (measured frequency), and 3/4
  (backlog-impact and live demonstrations of the two shipped checks) --
  fresh `gh issue view`/`gh pr view` fetches of every cited issue/PR,
  fresh measurement scripts against the live GitHub tracker and the real
  current open backlog, and the two shipped regression suites re-run
  from an independent worktree, none of it taken from the PR's own
  pasted transcripts
result: passed
assertedBy: execution-observation session for issue-2414, independent of
  PR #2422's authoring (implementation) session
---

# issue-2414 — execution-observation record

## What was done

canonical: `gh issue view 2291/2383/2393 --json body -q .body` (this
session, live) -- read each original `## Acceptance` section directly
and confirmed PR #2422's Measurement 1 quotes are verbatim-accurate and
its A/B verdict holds: #2291's Acceptance says what the trace must DO
(record, watchdog report) and never what it must NOT do; #2383's says
WHAT to prune (by age) and never what it must NOT prune; #2393's fourth
bullet requires the one-time 285-record cleanup but never requires the
*ongoing* rotation policy to prove it reaches records that predate the
fix -- a completeness property no re-reading of the Acceptance text
would surface. All three match the A/B shapes #2414 and PR #2422
describe.

canonical: `gh issue view 2411` / `gh pr view 2411` (this session) --
both resolve to the same PR (state: MERGED), confirming #2411 is not a
standalone GitHub issue distinct from #2393/#2413 -- see Open findings.

**Frequency (Measurement 2).** canonical: `gh pr list --state merged
--json number,title,mergedAt --limit 300`, filtered
`2026-08-25T00:00:00Z..T11:51:03Z` (this session) -- 116, exact match to
the record's own count. derived: independently re-read all 116
titles/bodies and reclassified "mechanism-adding delivery PR"
(introduces/changes a write/delete/refuse/report surface, excluding
conformance-review/execution-observation/re-review PRs) from scratch,
without seeing the record's own enumerated list -- landed on 27, not 24.
Both counts are judgment calls, exactly as the record itself labels this
step (`provenance: read ... not a mechanical regex`), and both put the
same-shape follow-up rate in an 11-13% band (3/24=12.5%, 3/27=11.1%) --
the record's substantive verdict (non-negligible, justifies a bounded
intervention, likely a floor due to right-censoring) is robust to
exactly where this classification boundary is drawn.

canonical: `gh issue view 2413 --json createdAt -q .createdAt` (this
session) -- result: `2026-08-25T11:52:55Z`. derived: the record's own
stated window (`00:00:00Z` to `11:51:03Z`, chosen to match PR #2411's
merge timestamp exactly) does not actually contain one of the three
events counted inside it -- issue #2413 (the Failure-B follow-up defect)
was opened about 1m52s *after* the window's stated end. See Open
findings.

**Backlog-impact (Measurement 3).** Checked out `gates/acceptance_gate.py`
into an independent worktree and wrote a fresh script (the record's own
`/tmp/measure_backlog.py` no longer exists) isolating the marginal
block effect of the universal vs. narrow-trigger designs against a
baseline with `_MUST_NOT` monkeypatched to always-match, run against the
*current* real open backlog:

```
$ python3 /tmp/measure_backlog_eo.py
open_issues_total=44
baseline_blocked=11
universal_blocked=44 universal_marginal_new=33 issues=[1633, 1650, 1656, 1672, 1694, 1725, 2092, 2135, 2136, 2138, 2139, 2193, 2196, 2203, 2216, 2238, 2287, 2288, 2289, 2297, 2324, 2325, 2326, 2332, 2334, 2357, 2360, 2402, 2403, 2409, 2412, 2415, 2417]
narrow_blocked=24 narrow_marginal_new=13 issues=[1633, 1656, 2136, 2138, 2139, 2297, 2334, 2357, 2360, 2409, 2412, 2415, 2417]
```
canonical: `python3 /tmp/measure_backlog_eo.py` (this session, real
worktree, pasted output above) -- exit 0, no crash.

derived: 33/44 (75%) universal, 13/44 (30%) narrow -- against the
record's own 34/45 (76%) / 14/45 (31%), off by exactly one issue in
each, and the missing issue is the same one in both: `#2413`. canonical:
`gh issue view 2413 --json state -q .state` (this session) -- result:
`CLOSED` -- #2413 was open at the record's measurement time and has
since closed, so the one-off difference is fully explained by ordinary
backlog drift between the two measurements, not a reproduction failure.
This is a strong independent confirmation of Measurement 3.

canonical: `gates/acceptance_gate.py:75-77` (this session's independent
worktree checkout, commit `2019bf3b`) -- the module's own inline comment
claims the narrow-trigger design "bounds the one-time migration cost to
8 of 45 open issues (18%)" -- this contradicts both the shipped record's
own figure (14/45, 31%, quoted in its `breaking:` frontmatter and
Measurement 3) and this session's independent reproduction immediately
above (13-14/44-45, ~30%). See Open findings.

**Regression suites**, re-run from the independent worktree:

```
$ python3 gates/test_acceptance_gate.py
27/27 passed
$ python3 gates/test_requirement_met.py
35/35 passed
```
canonical: `python3 gates/test_acceptance_gate.py`,
`python3 gates/test_requirement_met.py` (this session, independent
worktree, pasted output above) -- both exit 0.

derived: exact match to the record's own figures.

**Live demonstrations**, reproduced independently:

```
$ python3 /tmp/verify_real_cases_eo.py
#2291: total_violations=1 must_not_violation=True
#2383: total_violations=1 must_not_violation=True
#2393: total_violations=1 must_not_violation=True
```
canonical: `python3 /tmp/verify_real_cases_eo.py` (this session, real
worktree, pasted output above) -- exit 0, no crash.

canonical: appending `must not: record an attempt whose issue number is
a test-suite fixture` to #2291's real fetched body and re-running
`check_issue_body` (this session) -- result: `[]` (zero violations).
Matches the record's Failure-A demonstration.

canonical: `gh pr diff 2400 > /tmp/pr2400_eo.diff` (this session), then
calling `requirement_met._convergence_evidence_missing(
"runs/spawn-attempts.jsonl", "executed-live", diff)` directly against
that real diff -- result: `False` (correctly not blocked, since
`341 -> 41` is present in the diff's added lines); against a constructed
diff with no before/after pair -- result: `True` (correctly blocked).
Matches the record's Failure-B demonstration.

## Why

Scope was independent re-derivation of the two measurements issue-2414's
own Acceptance names as the thing that must justify (or refute) any new
gate -- frequency and backlog-impact -- not re-litigating the A/B design
choice itself, whose reasoning (Measurement 4, "What did not work") this
session spot-checked for internal consistency but did not redo from
scratch. Every issue body, PR diff, and timestamp used above was fetched
live via `gh` this session (canonical tags inline above), never taken
from the record's own pasted transcripts, per this issue's own explicit
instruction that a delivering session must "read... original text"
rather than a summary -- the same standard applied here to observing the
delivering session's own work. canonical: the denominator
reclassification (27 vs. 24, "What was done" -> Frequency above) was
performed by this session reading all 116 `gh pr list`-fetched
titles/bodies directly and judging each independently, before reading
the record's own methodology text a second time to compare -- not a
check of arithmetic against a list already seen.

## Upstream basis

- `docs/issue-2414/reports/implementation.md`, untracked in this tree --
  lives on branch `issue-2414/implementation` at commit
  `2019bf3be0f0404e6b05e753eba5f1991bb54c34`, PR #2422 -- the record
  whose Measurements 1-3 and live demonstrations this session
  independently re-derived above.
- `gates/acceptance_gate.py`, `gates/requirement_met.py` at the same
  commit (independent worktree `/tmp/wt-2414-impl`, removed after this
  observation) -- the two changed modules this session ran tests and
  fresh measurement scripts against directly.
- #2291, #2383, #2393, #2411, #2413 read live via `gh issue view`/`gh pr
  view` this session, independent of both issue #2414's own summary and
  PR #2422's citations.

## Open findings

- canonical: `gates/acceptance_gate.py:75-77` (independent worktree,
  commit `2019bf3b`, this session) -- the module's own inline comment
  states the narrow-trigger design costs "8 of 45 open issues (18%)" --
  contradicts the shipped record's own `breaking:` frontmatter and
  Measurement 3 (14/45, 31%), and this session's independent
  reproduction above (13-14 of 44-45, ~30%, `derived:` from
  `/tmp/measure_backlog_eo.py`'s pasted output above). Likely stale: the
  warrant-hunt fix documented in the record's "What did not work"
  (adding past-tense/passive verb inflections to `_MECHANISM_TRIGGER`)
  would mechanically increase the trigger's match rate, and the comment
  reads as written before that fix and never updated after. Resolution
  path: PR #2422 itself states this code is offered as candidate input
  to #2415's redesign rather than landed as permanent, so no separate
  fix is proposed here -- a #2415 session picking up this code should
  not carry the stale comment forward.
- canonical: `gh issue view 2413 --json createdAt -q .createdAt` (this
  session) -- result `2026-08-25T11:52:55Z`, cited above in "What was
  done" -> Frequency. The record's stated measurement window
  (`2026-08-25T00:00:00Z` to `11:51:03Z`) ends before this event, which
  it counts inside the window. Immaterial to the substantive conclusion
  -- extending the window two minutes later does not add or remove any
  other PR or issue in this dense session (same `gh pr list`/`gh issue
  list` fetch above shows no other event in that gap) -- but the
  record's own stated window is not literally self-consistent with its
  own numerator. Resolution path: none needed; noted for a future reader
  who might try to reproduce the exact boundary.
- canonical: `gh issue view 2411` / `gh pr view 2411` (this session,
  cited in "What was done" above) -- both resolve to the same PR (state:
  MERGED). The record cites "#2411 (Failure A)" as a same-kind artifact
  to #2393/#2413's issue-tracked follow-up defects, but no standalone
  issue number was ever filed for this defect -- it was found by a
  background warrant-hunter during PR #2389's CHANGES round and narrated
  only in PR #2411's own body (racing a concurrent merge of #2389,
  `gh pr view 2411 --json body -q .body`, this session). The underlying
  incident is real and independently confirmed (PR #2411's body and diff
  describe and fix the exact worktree force-remove bug), but its
  citation shape differs from the other two numerator events, which are
  separately filed, triaged issues. Resolution path: none needed against
  PR #2422 itself, which did not originate this citation shape -- worth
  a #2415 session's awareness if it re-derives this same frequency
  measurement.
- derived: this session's own independent classification of
  "mechanism-adding delivery PR" in the stated window (`/tmp` scratch
  work this session, tallied in "What was done" -> Frequency above)
  landed at 27, not the record's 24. Both numbers are judgment calls, as
  the record's own methodology states (`provenance: read ... not a
  mechanical regex`), and both put the same-shape-defect rate in the
  same 11-13% band, so this does not change the record's verdict that
  the rate is non-negligible. No resolution path needed -- recorded so a
  future reader knows the exact denominator was independently checked,
  not merely re-typed.

## Next steps

None -- `loop_state` above is this record kind's terminal value,
`handed-off`.
