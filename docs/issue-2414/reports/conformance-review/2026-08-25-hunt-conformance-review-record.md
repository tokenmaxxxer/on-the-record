---
proposal: docs/issue-2414/reports/conformance-review.md
---

# Hunt record — conformance-review-record

## before-landing — stance 1: check the conformance-review record itself for silent failures or plain errors — NOT the code under review

Verdict: FINDING — the record's own finding-record skill-verdict claims "this file is the only file this review wrote to," but the same review process also wrote a second file (a deviation-log entry), on the same branch, in a separate commit.
Kind: silent-failure
Seed: docs/issue-2414/reports/conformance-review.md (in full), spot-checked against gh/live-repo citations per requirement block 1-7, the Incorrect-verdict block, and frontmatter/result-field consistency
cap_seconds: not stated by dispatcher
tier: not stated by dispatcher
diff_stat_lines: not stated by dispatcher (single-file review record, ~343 lines)
started_at: 2026-08-25T12:56:00Z
ended_at: 2026-08-25T13:10:00Z

All seven requirement-block citations spot-checked reproduced exactly
(PR #2389/#2400 body contents and Closes-trailers; `gh pr diff 2422
--name-only`'s 10-file list; both shipped regression suites, 27/27 and
35/35; the 116-merged-PR window count and 38-item mechanical superset;
and — most load-bearing — the "Incorrect" verdict's own re-derivation:
`grep -n "8 of 45\|18%\|blocks 8" gates/acceptance_gate.py
on-the-record/directive/acceptance-format.md` against the PR #2422
worktree reproduces the cited stale "8 of 45 (18%)" lines verbatim, and
re-running the narrow/universal backlog sweep against a freshly-fetched
44-issue open backlog via the PR's own `acceptance_gate` module
reproduces the record's exact `total=44 baseline_blocked=11
narrow_blocked=24 narrow_marginal_new=13` / `universal_blocked=44
universal_marginal_new=33` figures, issue-list-for-issue-list, matching
the record's re-run byte for byte). None of that yielded a finding.

The finding is in the record's self-report of its own write footprint,
which is checkable independently of the code under review and turned
out to be false.

### Reproduce
```
$ cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2414-conformance-review
$ find docs/issue-2414/ -type f
docs/issue-2414/reports/conformance-review.md
docs/issue-2414/reports/conformance-review/deviation-log/20260825T125345186260-ddf09ecd52f19b23.md

$ git log --oneline -3 -- docs/issue-2414/
6674a0da issue-2414: log Closes-trailer deviation on the conformance-review PR
5ba3ba9c issue-2414: builder-blind conformance review of PR #2422

$ grep -n "only file this review wrote to" docs/issue-2414/reports/conformance-review.md
333:- skill-verdict: conformance-review-finding-record — applied: invoked; this file is the only file this review wrote to, using the five-value verdict set, and evidence was locatable for all seven requirement blocks (no refusal needed).
```

### Observed
`conformance-review.md`'s own `conformance-review-finding-record`
skill-verdict (line 333) asserts, as its compliance evidence, "this
file is the only file this review wrote to." But the same
review — on the identical branch, in a second commit titled "issue-2414:
log Closes-trailer deviation on the conformance-review PR" — also wrote
`docs/issue-2414/reports/conformance-review/deviation-log/20260825T125345186260-ddf09ecd52f19b23.md`,
which records a deviation encountered while opening this review's own
PR (a `Closes #2414` trailer forced by the `pr-preflight` gate under
`CORE_BUILD_NOW=1`). Neither `conformance-review.md`'s frontmatter
`upstream:` list, its "Upstream basis" section, its "What was done"
section, nor its "Open findings" section mentions this second file at
all — it is invisible from reading the record, and the one place that
does make a claim about the review's write footprint states the wrong
thing. (Other conformance-review records in this same repo that also
write a deviation-log entry — e.g. issue-2211, issue-2156, issue-2295 —
openly cite `.../conformance-review/deviation-log.md` in their own
frontmatter `upstream:` and body; issue-2414's record is the only one
using the "only file this review wrote to" phrasing, and the only one
where that phrasing is contradicted by `git log`/`find` on its own
branch.)

### Expected
The finding-record skill-verdict should either not claim a
single-file write footprint (since a second file — the deviation-log
entry — was in fact written by this same review), or the record should
list/cite that second file the way other conformance-review records in
this repo do, so the claim matches what `find docs/issue-2414/ -type f`
and `git log` on the branch actually show.
