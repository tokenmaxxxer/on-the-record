---
proposal: docs/issue-2414/reports/conformance-review.md
---

# Hunt record — re-review-conformance-record

## after-proposal — stance 1: does the record's own pasted grep output for the migration-cost-accuracy sweep match what the exact same command actually produces against the exact head it cites?

Verdict: FINDING — the record's pasted "canonical" grep output for the post-fix stale-figure sweep is incomplete: it shows one hit when the same command against the exact cited head (bd9350cd) produces two, and the record's prose then falsely claims "No other file under gates/, on-the-record/, or docs/issue-2414/ carries the stale figure."
Kind: silent-failure
Seed: docs/issue-2414/reports/conformance-review.md (migration-cost-accuracy requirement block), commit b6e4c968
cap_seconds: not specified in dispatch
tier: not specified in dispatch
diff_stat_lines: 162 (109 insertions, 53 deletions) per `git show b6e4c968 --stat`
started_at: 2026-08-25T22:50:00+09:00
ended_at: 2026-08-25T23:15:00+09:00

### Reproduce
```
$ git fetch origin pull/2422/head:tmp-pr2422-check
$ git worktree add /tmp/pr2422-verify tmp-pr2422-check   # HEAD bd9350cdc79c3b57c34c0a207320c460e5aff276, the exact sha the record cites
$ cd /tmp/pr2422-verify
$ grep -rn "8 of 45\|18%\|8/45" gates/ on-the-record/ docs/issue-2414/
```

### Observed
The real command against the record's own cited head produces two hits:
```
docs/issue-2414/reports/implementation/deviation-log/20260825T130144037066-0b23939226b07fc9.md:1:- 2026-08-25T12:57:42Z inline: CHANGES round on PR #2422, triggered by PR #2426 ... both still stated the shipped narrow-trigger design blocks "8 of 45 (18%)" of the backlog ...
docs/issue-2414/reports/implementation.md:129:  "8 of 45 (18%)" as the narrow-trigger design's backlog cost — the
```
But docs/issue-2414/reports/conformance-review.md's migration-cost-accuracy requirement block pastes only the implementation.md:129 line as the sweep's output, then states: "derived: the one remaining hit is historical narration ... No other file under `gates/`, `on-the-record/`, or `docs/issue-2414/` carries the stale figure." That sentence is false as written — a second file (the deviation-log shard) also carries the string, and the record's own pasted "canonical" grep transcript omits it entirely rather than showing and dismissing it.

### Expected
A builder-blind conformance-review record that presents a grep transcript as "canonical" evidence for a completeness claim ("no other file ... carries the stale figure") must paste the actual, complete output of that exact command against the exact head cited. Here the actual output has two lines; the record shows one and then asserts full coverage. (The second hit is very likely also legitimate historical narration once inspected — this finding is not that the sweep's conclusion is wrong, but that the record's own pasted "canonical" reproduction of the sweep does not match reality, which is exactly the invisible-until-checked defect this review exists to catch in a record whose whole claim is "independently re-verified, not carried forward.")
