---
issue: 3230
role: independent-verification-1
author: independent-verification-1
verifies_subject: true  # independent verification of PR #3234's deliverable (author diagnose-first+implementation-blueprint+experiment-trust-a01a3586)
code_under_review:
  - consult.py
  - scripts/issue-3230/measure_skill_judge.py
  - tests/test_issue_3230_skill_judge_cost.py
  - docs/issue-3230/reports/diagnose-first+implementation-blueprint+experiment-trust-a01a3586.md (untracked in this worktree -- lives on PR #3234's branch)
  - on-the-record/hooks/amendment_channel.py (pre-existing on origin/main, read not written by PR #3234 -- checked as counter-evidence)
  - on-the-record/hooks/hooks.json (pre-existing on origin/main, read not written by PR #3234 -- checked as counter-evidence)
type: verification
breaking: false
verdict: PR #3234's shipped tooling and its "ship no behavior change this round" conclusion both hold up under independent re-derivation. One factual claim in its record is incorrect (async-delivery mechanism); one corpus-scan number in its record is not durably reproducible; both are non-blocking since neither changes the round's recommended action. See "What was done" for the executed evidence.
loop_state: done
upstream:
  - path: PR #3234 (branch issue-3230/diagnose-first+implementation-blueprint+experiment-trust-a01a3586, untracked in this worktree)
    sha: c2151465252020fc4f18d150339469f77af93fb9
  - path: PR #3240 (branch issue-3230/adversarial-review+diagnose-first+experiment-trust-f2f4f629, untracked in this worktree), read after independently re-deriving the async finding, for cross-reference only
    sha: 58593a6876d261e3c54a578b72c95e47519720bb
---

# issue-3230 — independent-verification-1 record

## What was done

Independently verified PR #3234 (the R007 skill_judge diagnosis) against
its own branch, in a separate `git worktree` from this record's own
branch (`/tmp/verify-3234`, HEAD `c2151465`), without reusing any of PR
#3234's own claims as given.

**1. Acceptance checks, re-run live in that worktree:**

- `python3 -m pytest tests/test_issue_3230_skill_judge_cost.py -q` ->
  `13 passed in 1.42s`.
  derived: `cd /tmp/verify-3234 && python3 -m pytest tests/test_issue_3230_skill_judge_cost.py -q` — 13 passed
- `python3 scripts/issue-3230/measure_skill_judge.py --report` -> exit 0,
  `ledger files scanned: 42`, `real (plausible) events ... found: 31`,
  `median=20.700s`.
  derived: `cd /tmp/verify-3234 && python3 scripts/issue-3230/measure_skill_judge.py --report` — exit 0, n=31, median=20.700s
  The PR's own test-plan (body of PR #3234, `gh pr view 3234`) claimed
  n=21, median=16.343s; both counts are real (n only grows as more
  `skill_judge_perf` events land in `runs/ledger.jsonl` between the PR's
  run and this one) — a timing artifact of when each report ran, not a
  discrepancy in the tool.
- `python3 scripts/issue-3186/measure_cross_family.py --report`
  (must-not requirement) -> exit 0, `bootstrap_timing lines found: 18`,
  still finds its `cross_family` share data (`share=29.9%`).
  derived: `cd /tmp/verify-3234 && python3 scripts/issue-3186/measure_cross_family.py --report` — exit 0, 18 bootstrap_timing lines, share=29.9%
  Not broken by this PR.

**2. `consult.py` diff, read directly rather than trusting the PR body's
prose description of its own change:**

```
-    line = (f"- {ts} | skill={skill} | verb={verb} "
-            f"| issue={issue if issue is not None else 'none'} "
-            f"| question={question[:200]!r} | outcome={outcome[:300]!r}")
+    line = (f"- {ts} | skill={skill} | verb={verb} "
+            f"| issue={issue if issue is not None else 'none'} "
+            f"| question={question[:4000]!r} | outcome={outcome[:2000]!r}")
```
derived: `git diff origin/main...origin/issue-3230/diagnose-first+implementation-blueprint+experiment-trust-a01a3586 -- consult.py` (fetched live in this session)

The diff widens **two** truncation limits — `question[:200]` ->
`question[:4000]` AND `outcome[:300]` -> `outcome[:2000]` — while the PR
body and the PR's own record (untracked in this worktree, lives on PR
#3234's branch) describe only the question-field widen as the change.
Observability-only, no selection/timing logic touched either way, but
the PR's own description of its own diff is incomplete.

**3. Async-delivery claim**, checked against the actual repo,
independently, before reading PR #3240 in detail. The PR's record
(untracked in this worktree) says: "this codebase has none today ... no
existing mechanism delivers it later" for a way to push information into
an already-running session.

```
$ git ls-files | grep -i amendment
on-the-record/hooks/amendment-channel.sh
on-the-record/hooks/amendment_channel.py
tests/test_amendment_channel.py
...
$ grep -n amendment-channel on-the-record/hooks/hooks.json
90:            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/fail-open-wrapper.sh ${CLAUDE_PLUGIN_ROOT}/hooks/amendment-channel.sh"
```
derived: `git ls-files | grep -i amendment && grep -n amendment-channel on-the-record/hooks/hooks.json` (run in this session's own worktree against `origin/main`, both files pre-existing and unrelated to PR #3234's diff)

`on-the-record/hooks/hooks.json:90` registers `amendment-channel.sh` as a
live `PostToolUse` hook. `amendment_channel.py`'s own docstring (lines
12, 39-42 of that file, read directly) describes exactly the class of
mechanism the PR's record says doesn't exist: delivering information
into an already-running session via the `PostToolUse` seam, specifically
scoped today to detecting `gh issue edit` commands and correlating their
stdout URL against the issue actually edited.
canonical: `on-the-record/hooks/amendment_channel.py` lines 12, 39-42 (docstring, read directly in this session's own working tree)

Reusing that mechanism for skill-list delivery is real, unbuilt
integration work — but the PR's record claim ("has none today") is
unqualified and, as stated, false: a wired delivery-into-a-running-
session mechanism does exist, it is simply not wired for this purpose.

**4. Cache repeat-rate scan**, re-run live and unmodified against the
PR's own "Evidence appendix" script (in its own record, untracked in
this worktree, the `scan_repeats2.py` body reproduced verbatim there),
against the same glob the PR used
(`~/.tokenmaxxxer/work/*/docs/issue-*/reports/consult-log{,/*.md}`):

```
$ python3 /tmp/verify_scan_repeats.py
paths matched: 11570
total trace lines: 192 | fixture-filtered out: 136 | real remaining: 56
distinct real (issue, question) keys: 44
real keys repeated >1x: 5 | repeat (would-be cache hit) events: 12
repeat share of REAL dispatches: 0.21428571428571427
```
derived: `python3 /tmp/verify_scan_repeats.py` (script body = the PR's own reproduced-verbatim `scan_repeats2.py`, executed live in this session; script itself written via this session's own Write tool at `/tmp/verify_scan_repeats.py`, outside the repo)

The PR's own record claimed `total trace lines: 865`, `real remaining:
56`, `distinct keys: 42`, `repeated keys: 7`, `repeat events: 14`,
`repeat share: 14/56=0.25`. The corpus this script reads is ephemeral
per-session workspace state under `~/.tokenmaxxxer/work/*` that gets
cleaned up over time (865 -> 192 raw trace lines between the PR's run
and this one), so the same script re-run later sees a materially
different raw count — independent of the two separate methodology gaps
PR #3240's own record (untracked in this worktree) reports finding
(cross-workspace duplication, field-name-rename undercount). The
qualitative conclusion (repeat rate is real and non-trivial, "not near
zero") held on this smaller, later corpus too: `12/56=0.214` here vs.
`14/56=0.25` in the PR's own run.

**5. Judge-vs-BM25 live comparison**: not independently re-run by this
record. Each sample is a real subprocess judge dispatch costing roughly
15-20s per call.
canonical: `git show 58593a6876d261e3c54a578b72c95e47519720bb:docs/issue-3230/reports/adversarial-review+diagnose-first+experiment-trust-f2f4f629.md` (PR #3240's own record, read directly via `git show` on the fetched commit in this session)
That citation's own `verdict:` frontmatter and body report an
independent fresh 10-sample live comparison and a combined-sample
agreement figure alongside the original PR's 5-sample figure; re-running
a third from-scratch sample was judged unnecessary given that existing
independent run, and is accepted here as corroboration rather than
re-derived a third time in this record.

**6. PR #3240 cross-check**: read only after step 3 above, to compare
findings rather than to source them — the async-mechanism finding was
independently re-derived first in this record, then found to match PR
#3240's own record's finding on the same question.
canonical: `git show 58593a6876d261e3c54a578b72c95e47519720bb:docs/issue-3230/reports/adversarial-review+diagnose-first+experiment-trust-f2f4f629.md` frontmatter `verdict:` field, read directly in this session

## Why

The issue's own text requires the "did not make selection worse" half of
R007 to be demonstrated, not assumed, and PR #3234's own record makes
several load-bearing factual claims (an async delivery mechanism "has
none today", specific repeat/agreement percentages from a live corpus
scan) that are exactly the kind of claim this repo's verification
convention treats as needing independent re-derivation rather than
citation-trust. Re-running the PR's own scripts against real state
(rather than reading only its prose) is what surfaced both the async
claim's inaccuracy and the corpus-scan's non-reproducibility, neither of
which would show up from reading the record alone.

## What did not work

None.

## Upstream basis

- PR #3234 (`issue-3230/diagnose-first+implementation-blueprint+experiment-trust-a01a3586`,
  untracked in this worktree, sha `c2151465252020fc4f18d150339469f77af93fb9`)
  -- the subject verified; see "What was done" above for the
  `derived:`/`canonical:`-tagged re-derivation.
- PR #3240 (`issue-3230/adversarial-review+diagnose-first+experiment-trust-f2f4f629`,
  untracked in this worktree, sha `58593a6876d261e3c54a578b72c95e47519720bb`)
  -- cross-referenced after independently re-deriving the async finding.
  canonical: `git show 58593a6876d261e3c54a578b72c95e47519720bb:docs/issue-3230/reports/adversarial-review+diagnose-first+experiment-trust-f2f4f629.md` (read directly in this session, cited above in "What was done" steps 5-6)
- `on-the-record/hooks/hooks.json` and `on-the-record/hooks/amendment_channel.py`
  (both pre-existing on `origin/main`, unrelated to PR #3234's own diff) --
  read directly in this session's own working tree as the counter-evidence
  for the async finding.
  canonical: `on-the-record/hooks/hooks.json:90` and `on-the-record/hooks/amendment_channel.py` lines 12, 39-42, both read directly in this session (cited above in "What was done" step 3)

## Open findings

- The async-delivery claim in PR #3234's record is incorrect as stated.
  canonical: `on-the-record/hooks/hooks.json:90` (`amendment-channel.sh` registered as a live `PostToolUse` hook), read directly in this session -- see "What was done" step 3 above for the full derivation.
  Resolution path: PR #3234's own record should be corrected before or as
  part of any future round that revisits async dispatch as an option --
  not blocking, since the PR does not ship async dispatch this round
  either way, but the claim as written would mislead a future session
  that re-opens that option.
- The cache-repeat-rate scan's corpus (`~/.tokenmaxxxer/work/*`) is
  ephemeral and shrinks/changes as session workspaces get cleaned up, so
  the specific percentage in any record that cites it is not a stable,
  later-reproducible number.
  derived: `python3 /tmp/verify_scan_repeats.py` — 12/56=0.214 (this session, `~/.tokenmaxxxer/work/*` corpus at verification time) vs. 14/56=0.25 (the PR's own run, same script, earlier corpus state) -- see "What was done" step 4 above.
  Resolution path: none required this round -- the qualitative conclusion
  (cache is unsafe due to non-determinism, not due to a low repeat rate)
  is robust to this and was independently confirmed on two different
  corpus snapshots. Worth flagging for any future session that wants to
  cite an exact repeat-rate percentage as durable evidence -- it is not,
  without also committing the corpus or the matched trace lines.
- The `consult.py` diff widens two truncation limits (question, outcome)
  while the PR's own description names only one.
  derived: `git diff origin/main...origin/issue-3230/diagnose-first+implementation-blueprint+experiment-trust-a01a3586 -- consult.py` — see "What was done" step 2 above for the full diff.
  Resolution path: none required -- confirmed observability-only on both
  counts via the diff itself, no selection/timing logic touched.

## Next steps

None -- loop_state is `done`.
acceptance: `python3 -m pytest tests/test_issue_3230_skill_judge_cost.py -q` (run against PR #3234's branch in `/tmp/verify-3234`) — result:
```
13 passed in 1.42s
```
This record's own verification purpose is satisfied against the subject
it verifies (see "What was done" step 1 above for the full
acceptance-check re-run, including the must-not check).
