---
issue: 3230
role: diagnose-first+implementation-blueprint+experiment-trust-5df5cff1
author: diagnose-first+implementation-blueprint+experiment-trust-5df5cff1
skills: diagnose-first (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12)), experiment-trust (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-3230/reports/diagnose-first+implementation-blueprint+experiment-trust-a01a3586.md (PR #3234, Round 1)
    sha: same-commit
  - path: docs/issue-3230/reports/adversarial-review+diagnose-first+experiment-trust-f2f4f629.md (PR #3240, merged to main, untracked on this branch)
    sha: 07ffcb7444ae47587e2c74b58187ce009b0abb9a
---

# issue-3230 — diagnose-first+implementation-blueprint+experiment-trust-5df5cff1 record

## What was done

Round 2 on PR #3234's diagnosis. Appended a "Round 2" section to PR
#3234's own record
(`docs/issue-3230/reports/diagnose-first+implementation-blueprint+experiment-trust-a01a3586.md`,
same commit as this file — this session may only append to that
foreign-authored record, never alter its existing lines, per contract v3
s11) that: (1) corrects the record's Question 3 claim ("this codebase
has none today" for a mechanism to deliver a correction into an
already-running session) — that claim is false, this repo already ships
a wired, production `PostToolUse` hook,
`on-the-record/hooks/amendment_channel.py`, built for exactly this
purpose; (2) does the async-dispatch-viability analysis the false
premise skipped, concluding async is technically buildable on that
channel but not safe to ship this round, for three named structural
reasons (reactive delivery, advisory-only content, no undo for work
already done) rather than the absent-mechanism claim; (3) evaluates a
fifth option PR #3240 raised but did not resolve — scoping the judge to
the issue rather than the dispatch — concluding it is also unsafe, for a
reason distinct from "it's a cache": it converts transient judge
disagreement into a durable single point of failure and discards real
within-issue task-text variation; (4) corrects two disclosure defects PR
#3240 found: the truncation fix widened two `consult.py` fields (200→4000
and 300→2000), not the one originally described, and Question 1's cache
numbers (n=56, 25%/43%) are replaced with PR #3240's corrected,
deduplicated, both-field-name-era sample (n=291, 32%/36%), naming the two
methodology gaps (workspace-clone corpus duplication, a `role=`→`skill=`
field-rename undercount). Also updated PR #3234's own GitHub description
via `gh pr edit` to summarize the correction (see "Upstream basis"
below for the exact command). No dispatch-path, timeout, or
selection-mechanism code change ships this round — see the a01a3586.md
Round 2 section's own "Conclusion" paragraphs for the full reasoning.

acceptance: `python3 -m pytest tests/test_issue_3230_skill_judge_cost.py -q`
(this branch, this round) — result:
```
13 passed in 0.88s
```
acceptance: `python3 scripts/issue-3230/measure_skill_judge.py --report`
(this branch, this round) — result: exit code 0, n=31 real events,
median=20.700s (quoted in full in the a01a3586.md Round 2 section,
"Round 2 re-run of the acceptance checks").
acceptance (must-not): `python3 scripts/issue-3186/measure_cross_family.py --report`
(this branch, this round) — result: exit code 0, still finds its data.
acceptance: `python3 -m pytest -q` (full suite, this branch, this round)
— result: `4 failed, 1433 passed, 3 xfailed, 2 warnings in 45.96s` — same
4 pre-existing failures as PR #3234's own Round 1 run and PR #3240's
independent confirmation, none touching any file this round edited.

## Why

The task that spawned this round read PR #3240's independent verification
of PR #3234 (canonical: `gh pr view 3240`, `gh pr diff 3240`, both read in
full this round) and found its Item 3 finding — the async-delivery claim
graded **Incorrect** — changes the shape of the diagnosis: PR #3234
refused to consider asynchronous dispatch on a premise ("no mechanism
exists") that is false, so the refusal needed re-deriving on the correct
premise rather than left standing. `diagnose-first`'s G2 verify-against-
evidence axis is what this round applied to Question 3's own claim
directly — reading `on-the-record/hooks/amendment_channel.py` rather than
trusting either PR #3234's or PR #3240's framing at face value — and to
the fifth option, reasoning from `spawn.py:3950`'s own per-dispatch task
text (read directly this round) rather than accepting PR #3240's brief
argument as sufficient on its own. `implementation-blueprint` does not
apply: this round ships no multi-module code, only a documentation
correction. `experiment-trust` does not apply: no variant-comparison
result is reported as a launch decision this round; the corrected
cache/BM25 counts are diagnostic re-derivations carried forward from PR
#3240, not a fresh A/B result.

## Upstream basis

- `docs/issue-3230/reports/diagnose-first+implementation-blueprint+experiment-trust-a01a3586.md`
  (PR #3234, Round 1) — sha `same-commit` (this session's Round 2 section
  is appended to it in the same commit as this file).
- `docs/issue-3230/reports/adversarial-review+diagnose-first+experiment-trust-f2f4f629.md`
  (PR #3240's own record; untracked on this branch, that content merged
  to `main` via PR #3240 after this branch was cut) — sha
  `07ffcb7444ae47587e2c74b58187ce009b0abb9a`. canonical: `gh pr diff 3240`,
  executed this round, full text read directly.
- `on-the-record/hooks/amendment_channel.py`, `on-the-record/hooks/amendment-channel.sh`,
  `on-the-record/hooks/hooks.json`, `spawn.py`,
  `docs/issue-1960/reports/execution-observation/baseline-measurement.md`
  — this branch's own checkout, read directly this round, unmodified by
  this session (cited, not edited).
- PR #3234 (`gh pr view 3234`) — the PR this round's commits push to,
  updated via `gh pr edit 3234 --body-file` this round to summarize the
  correction.

## Open findings

- **Async design not built.** This round establishes the amendment
  channel is a viable delivery path in principle but explicitly does not
  design or build the callback wiring (`write_amendment()` call from
  `_cross_family_future`'s completion), the "wait for the notice before
  the first substantive action" worker-directive change, or the
  before/after skill-selection measurement R007 requires before shipping
  it. Resolution path: a dedicated follow-up scoped to exactly that
  design-and-measure work, per the a01a3586.md Round 2 "Conclusion"
  paragraph under "Is async dispatch viable?".
- **Issue-scoped judge reasoned about, not empirically tested.** Same gap
  PR #3240 itself left open — this round adds a second, distinct
  argument (durable single-point-of-failure, discarded task-text
  variation) but does not run a live issue-scoped comparison. Resolution
  path: re-run Question 1's methodology grouped by `issue` alone
  (dropping the `question` half of the key) and report the resulting
  disagreement rate directly, if a future session wants to close this
  gap fully.
- **PR #3234's frontmatter `upstream:` list was not updated** to add PR
  #3240 as an upstream input, because doing so would have altered an
  existing frontmatter line in a foreign-authored record, which
  `board-gate.sh` (contract v3 s11) refuses even for a session appending
  new content elsewhere in the same file. The citation lives in this
  file's own `upstream:` list and in the appended Round 2 section's own
  `canonical:` tags instead. No resolution needed — this is the correct
  behavior of the gate, not a gap.

## Next steps

None outstanding for this round — the record correction is written,
committed, and pushed to PR #3234's branch; the PR description is
updated; all four acceptance checks (the two named in this issue's
acceptance criteria, the must-not check, and the full suite) ran this
round and are quoted above. loop_state: landed.

## Skill verdicts

skill-verdict: diagnose-first — applied: invoked; used G2's
verify-against-evidence axis to re-derive Question 3's own claim against
the actual `amendment_channel.py` code rather than accepting either PR's
framing, and to argue the issue-scoped-judge option from `spawn.py`'s own
per-dispatch task-text evidence.
skill-verdict: implementation-blueprint — not-applicable: this round
ships no multi-module code; the async wiring it evaluates is scoped as
future design work, not implemented here.
skill-verdict: experiment-trust — not-applicable: no variant-comparison
result is reported as a launch decision this round; the corrected
cache/BM25 counts carried forward from PR #3240 are diagnostic
re-derivations, not a fresh A/B result this round produced.
