---
issue: 2915
role: technical-writing-structure-comprehension+diagnose-first-676b7bd2
author: technical-writing-structure-comprehension+diagnose-first-676b7bd2
skills: technical-writing-structure-comprehension (skill-repository(c05de12)), diagnose-first (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2915/reports/adversarial-review-fa319c5b.md
    sha: 0209daf7d1a75d8fe7df15fc350fe9bcfe2e967b
  - path: docs/handbooks/monitor-liveness.md
    sha: same-commit
---

# issue-2915 — technical-writing-structure-comprehension+diagnose-first-676b7bd2 record

## What was done

Round 4 on issue #2915, a documentation-only follow-up to the
independent adversarial review of round 3
(`docs/issue-2915/reports/adversarial-review-fa319c5b.md`, landed via
PR #2940). canonical: `gh pr view 2940` — result: `state: MERGED`.

Brought round 3's own content over onto this session's own branch
first, per this round's instruction to base on PR #2934's branch
content as it exists on origin. derived: `git merge-base HEAD
origin/issue-2915/diagnose-first+observability-methodology-selection-1f7123db`
— result: `4677971899e70dd63d51f4d76cf6f52c8ad25470`. derived: `git diff
4677971899e70dd63d51f4d76cf6f52c8ad25470 HEAD --
docs/handbooks/monitor-liveness.md` — result: empty (this branch's
pre-edit copy of the file is byte-identical to the merge-base's, so no
divergent edits to reconcile). Took `git show
origin/issue-2915/diagnose-first+observability-methodology-selection-1f7123db:docs/handbooks/monitor-liveness.md`
directly as this file's starting point, rather than merging the whole
branch, to avoid the unrelated `consult.py`/`spawn.py`/etc. drift a full
merge would pull in from PR #2934's base having since fallen behind
`main`. derived: `git diff --stat HEAD
origin/issue-2915/diagnose-first+observability-methodology-selection-1f7123db`
— result: 29 files changed, most unrelated to this issue (consult.py,
spawn.py, skills.py, other issues' reports).

**The fix.** The review found one stale paragraph: "Staleness threshold
and the re-arm directive" (now lines 47-55) still asserted, ~150 lines
above round 3's rewritten "Issue #2915" section, that
`poll_heartbeat_delta.py`'s 1800s-bound beacon "bounds detection for a
non-empty tracked roster specifically" — the exact dead-Monitor
detection-latency claim round 3 withdrew everywhere else in the file.
Rewrote that paragraph (`docs/handbooks/monitor-liveness.md:47-55`) to
state the corrected position inline — the 360s/180s numbers bound only
how fast the check flags staleness once a turn invokes it, not how
often it gets invoked or how quickly an actually dead Monitor's death
surfaces — and to point forward to "Issue #2915" under "Structural
limit" for the full argument, rather than repeating it there.

Applied `technical-writing-structure-comprehension` while rewriting:
canonical: skill-repository technical-writing-structure-comprehension
SKILL.md ("target roughly 15-20 words per instructional sentence";
"when a sentence carries more than one independent clause plus a
conditional, split it") — restructured the replacement paragraph from
one long multi-clause sentence into several shorter sentences at clause
boundaries, matching that target range.

**Bounding the "no third instance" check.** The review's own grep for
detection-bound phrasing found 3 hits in the pre-fix file, of which 1
was this stale paragraph and 2 were not — re-ran that exact grep
against the pre-fix content myself: derived: `git show
origin/issue-2915/diagnose-first+observability-methodology-selection-1f7123db:docs/handbooks/monitor-liveness.md
| grep -n "bounds detection\|bound.*detection\|detection.*bound"` —
result:
```
53:bounds detection for a non-empty tracked roster specifically, without
283:where it stops here too: a true bound on actual-death detection needs an
305:dead-Monitor detection-latency bound.
```
Per the round's instruction not to trust that count alone, widened the
search independently before and after the edit: derived: `grep -n -i
"bound\|detect\|beacon\|infer\|absence\|surfac"
docs/handbooks/monitor-liveness.md` (case-insensitive, full file,
superset of the reviewer's pattern) — every hit past line 130 falls
inside the round-3-rewritten "Issue #2915" / "Structural limit"
sections and is consistent with the withdrawal; the only affirmative
claim outside that section, in either grep's output, was the one
paragraph fixed here. Search was bounded to this single file
(`docs/handbooks/monitor-liveness.md`) because round 3's own
`monitor-heartbeat` consumer grep (re-verified by the round-3 review)
already established no code anywhere else in the repo reads or alerts
on the beacon; a documentation-only fix to a stale claim about that
beacon's scope does not require re-running the code-wide grep.

## Why

The review named this precisely: a reader who reads the top of the
document and stops comes away believing dead-Monitor detection is
bounded, which is exactly the misunderstanding round 3 exists to
prevent. Fixing only the deep section and leaving the shallow
restatement uncorrected would leave the document internally
contradictory — the failure mode the whole round exists to close.
Rewriting the paragraph in place, rather than deleting it, preserves
the orientation value it correctly provides (what the 360s/180s numbers
do bound) while removing the one clause that was wrong, and
forward-refers to the deep section instead of duplicating its argument,
keeping the document from growing longer without becoming clearer.

## What did not work

None — the fix was a single, correctly-scoped paragraph rewrite; no
alternative approach was tried and discarded.

## Upstream basis

canonical: `docs/issue-2915/reports/adversarial-review-fa319c5b.md`
(commit `0209daf7`, PR #2940, merged) — named the exact stale paragraph
(`docs/handbooks/monitor-liveness.md` "Staleness threshold" section,
lines ~44-53 in its pre-fix numbering) and the grep that found it.
`docs/handbooks/monitor-liveness.md` (this commit) is the file edited;
its round-3 content was pulled in from
`origin/issue-2915/diagnose-first+observability-methodology-selection-1f7123db`
at commit `422ec2b18f571b5acbf7b812124212801a65656e` before this
round's own edit was made on top.

## Open findings

None open. derived: `grep -n "bounds detection\|bound.*detection\|detection.*bound"
docs/handbooks/monitor-liveness.md` (post-fix) — result:
```
285:where it stops here too: a true bound on actual-death detection needs an
307:dead-Monitor detection-latency bound.
```
Both remaining hits sit inside round 3's rewritten "Issue #2915"
section and restate the corrected (not withdrawn) position — line 285
says a true bound "needs an [OS-level scheduled-execution primitive]"
(none exists today), line 307 says the beacon is explicitly "not a
dead-Monitor detection-latency bound." The review's single finding is
fully resolved and the independent, wider re-check surfaced no further
instance of the withdrawn claim.

## Next steps

None — `loop_state: landed`. No code was touched (documentation-only,
per the round's must-nots); no watch/monitor behavior changed.

## Skill verdicts

skill-verdict: technical-writing-structure-comprehension — applied: invoked; canonical: skill-repository
technical-writing-structure-comprehension SKILL.md — used its
sentence-length and clause-split rules to restructure the fixed
paragraph in `docs/handbooks/monitor-liveness.md:47-55` from one long
compound sentence into several shorter sentences at clause boundaries.
skill-verdict: diagnose-first — not-applicable: the cause (one stale
paragraph) was already diagnosed and named by the prior round's
adversarial review; this round is direct execution on a known cause,
not a diagnose-the-cause task.
other mounted skills: not triggered — work-in-english and prose-modes
were configured for this task's text match but neither Skill tool was
invoked; the change is a targeted factual/structural correction to
existing handbook prose already in English, not new prose drafting or
a language-policy decision.
