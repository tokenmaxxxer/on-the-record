---
subject: issue-791
role: product-discovery
kind: survey
---

# Current-state survey (issue #791)

## Background / context

2026-08-11, this orchestration session: a `spawn.py ps` output was piped
through a grep filter; the filtered view read as "all sessions vanished."
Reading the raw `ps` output (no filter) showed all four sessions alive —
the filtered read was mis-parsed, not the process state. The false
"defect" was manufactured entirely by the inspection method, not by any
real fault. This directly violates northpole req #3 (actual
running/real content, not code-analysis/skim) and, per the issue,
corrupts req #1/#4/#5 downstream: a fix built on a false premise is not
completion, and its "resolution" is noise added to the record.

The repo already has a citation-integrity layer for records:
`on-the-record/gates/record_lint.py`'s `lint_record()` (mirrored at
write-time by `on-the-record/hooks/record-claim-guard.sh`) checks bare
count claims (`derived:` requirement, issue #333), unverifiable-reason
lines (#310/#331), and orphaned path references (#330). None of these
checks the *evidentiary basis for a defect/root-cause claim* — a record
can cite a real, existing path (passing #330) while the citation itself
is a bare keyword hit with no surrounding context, exactly the failure
observed 2026-08-11. That gap is this issue's subject.

## Problem, stated without any solution attached (JTBD)

- **Job performer:** a role session (any plugin-installed target
  session, per req #7) about to write a record that names a defect,
  bug, or root cause.
- **Job:** to ground a defect/root-cause claim in content the session
  actually inspected with enough surrounding context to know what the
  content means — not in an isolated keyword match that can carry a
  different meaning once its surrounding lines are seen (a filtered
  `ps` line reading "gone" when the raw output shows "alive").
- **Circumstance:** nothing today distinguishes, in the written record
  itself, a citation backed by a multi-line read of real source/design
  content from a citation backed by a single grep hit — both currently
  produce the same passing shape under `record_lint.py`'s existing
  checks, and per req #7 no CI step or explicit invocation may be relied
  on to catch the difference; only a default-on hook can.
- **Desired outcome:** a defect/root-cause claim reaching a commit
  carries a citation that a mechanical check can distinguish from a
  bare-grep citation, and grep-only claims are refused or flagged before
  they land — while a record with no defect/causation claim (additive
  feature, doc edit, quick lookup) is left untouched.

The issue itself already proposes a solution shape (a directive plus a
composable gate check). That shape is carried into the proposal below,
but the problem above — a record can currently claim causation from a
single decontextualized match, and nothing catches it before the commit
lands — is the reason it's needed, independent of that shape.

## Where this sits on the opportunity-solution tree

- **Outcome:** a record that claims a defect/root-cause is never wrong
  because the session read one line out of context (northpole req #1
  completion — no false-premise "fix" counted as done; req #3 — real
  content, not skim; req #4/#5 — no corrupted downstream fix/noise).
- **Opportunity:** `record_lint.py`'s existing citation checks (#333,
  #310/#331, #330) verify a claim's *shape* (a number has a `derived:`
  tag, a path exists) but never verify a defect claim's *grounding* —
  whether the cited evidence carries context beyond a keyword match.
  This is the exact hole the 2026-08-11 incident fell through: the
  filtered `ps` line was a real, existing piece of output (would pass
  #330), just decontextualized.
- **Candidate solutions:** (a) directive-only instruction ("read before
  you claim a defect") with no mechanical check; (b) a gate that checks
  citation *shape* only — multi-line excerpt present, `file:line`
  format — without verifying the excerpt is real; (c) a gate that
  verifies the cited excerpt's lines exist verbatim at the cited
  `file:line` in the working tree (closing the fabrication/skim-passed-
  off-as-read loophole that shape-only checking leaves open), composed
  with a directive that instructs full-read-before-claim by default.
  Scored in the proposal below.
- **Discriminating assumption test:** can a PreToolUse/write-time hook
  — seeing only the record's final text, never the session's prior tool
  calls — mechanically tell a grounded multi-line read apart from a
  single grep hit dressed up to look like one? The proposal's design
  answers this directly: verbatim content-match against the working
  tree is the strongest signal available without tool-call visibility,
  and its ceiling (it cannot prove comprehension, only non-fabrication
  plus context-presence) is stated as a limit, not hidden.

## Order-constraint note

This current-state survey is written before the proposal (contract v3
s19 / scout directive).

## Scout: skip record

Scouting was attempted at reduced scope, not skipped outright: no
`WebSearch`/`WebFetch` tool was loaded this session (deferred-tool
listing at session start carries neither), so no external sweep ran.
The comparable "best-in-class" system for this deliverable's kind
(citation/evidence-integrity gating over an authored record) is
already in-repo — `on-the-record/gates/record_lint.py` and
`on-the-record/hooks/record-claim-guard.sh`, read directly above — and
is used as the scouted baseline instead of an external exemplar. This
is recorded plainly per the scout directive's "state scouted-and-why"
rule rather than silently folded in.

## Write-surface unknowns this survey identifies

- Whether a defect-claim *trigger* vocabulary (which words in a record
  count as "claiming a defect/root-cause") can be kept conservative
  enough that additive/doc-only records never false-positive, while
  still catching the 2026-08-11 shape of claim.
- Whether verbatim content-match against the working tree is strong
  enough evidence of grounding to gate on, given the hook cannot see
  which tool (Read vs. `grep`) produced the cited text — addressed in
  the proposal's Confidence/limits section.
