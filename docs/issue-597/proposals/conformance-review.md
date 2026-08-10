# Conformance-review proposal — issue-597 sixth firing condition (phase 1)

## Upstream / basis

Issue #597. Merged architecture: `docs/issue-597/proposals/architecture.md`.
Delivered implementation: PR #607, `docs/issue-597/reports/implementation.md`,
`on-the-record/hooks/delegated-judgment-gate.sh`. Survey:
`docs/issue-597/reports/conformance-review/survey.md`.

## Requirement list (extracted, verdict deferred to phase 2)

Requirements below are the review's fixed unit — phase 2 renders one
Present/Surface/Absent/Incorrect/Unverifiable verdict per row, from the
artifact and spec only.

1. **R1 — Writer is the deployed gate, not orchestrator free prose.**
   Source: architecture §1; acceptance bullet 2 ("written by the deployed
   surface, not the orchestrator's free prose"). Check: the framing-snapshot
   body is produced and posted from within `delegated-judgment-gate.sh`
   (`build_framing_snapshot` → `_gh(["issue", "comment", ...])`), not from
   a role's authored text passed through unmodified.

2. **R2 — Three transitions, single detection mechanism, no new hook.**
   Source: architecture §2. Check: `FRAMING_TRANSITIONS` covers
   `gh pr merge`, `gh issue reopen <n>`, `gh issue close <n>`; no new
   `PreToolUse` matcher registration beyond the existing `Bash` hook.

3. **R3 — Four labeled elements per comment: Resolved problem, Prior cost,
   Newly possible, Still broken.** Source: architecture §3; acceptance
   bullet 1 ("four labeled elements"). Check: `build_framing_snapshot`'s
   output always contains exactly these four `**Label:**` lines.

4. **R4 — Each element's citation is mechanically-resolvable, checked
   before posting; fail-closed on an unresolvable citation.** Source:
   architecture §4; acceptance bullet 1 ("each element citing at least
   one record path"); acceptance check line ("mechanically-resolvable
   citations at each covered transition"). Check: `resolve_citation` runs
   over every element before `_gh(...)` fires, and `build_framing_snapshot`
   returns `None` (no post) on any failure.

5. **R5 — Citation-per-element vs. citation-per-comment.** Source:
   contradiction flagged in survey.md between issue body's constraints
   section ("each element carries at least one record citation") and
   acceptance bullet 1's phrasing ("each element citing at least one
   record path" — on inspection these two are not actually in tension;
   both name the element as the citation's unit). Kept as its own
   requirement row so phase 2 states explicitly which wording it is
   verifying against and notes if evidence diverges per-element vs.
   per-comment in the delivered code.

6. **R6 — Content assembled from cited record text, never freely
   composed.** Source: architecture §3 ("never invents a sentence with no
   antecedent text in a record"). Check: every non-baseline sentence in
   `build_framing_snapshot` originates from `_field_and_citation` /
   `_first_heading_prose` reads of an existing record file, not a
   hardcoded or synthesized string.

7. **R7 — Baseline behavior when no prior records exist.** Source:
   architecture §5; acceptance bullet 1's empty-state line ("a transition
   with no prior records ... states baseline framing explicitly —
   absence of prior cost evidence is stated, not fabricated"). Check: the
   `if not records:` branch posts an explicit baseline statement per
   element and a baseline-form citation, never a fabricated cost/resolution
   claim.

8. **R8 — No duplication of section-12 one-line events.** Source: issue
   body constraints ("Do not duplicate section-12 events ... complements
   the one-line events at a coarser cadence"); architecture §3's
   non-duplication paragraph. Check: framing-snapshot comments are
   structurally distinct from (not a restatement of) the pre-existing
   section-12 event postings in the same file — requires reading the
   section-12 event-posting code paths (outside the sixth-firing-condition
   diff) alongside the new arms, flagged in survey.md as not yet read.

9. **R9 — Test-fixture check: driving a fixture transition asserts the
   four labeled sections + citations.** Source: acceptance bullet 1's
   `check:` line verbatim. Check: `test_delegated_judgment_gate.py`'s five
   new tests actually assert on the four-label structure and citation
   presence/resolvability, not merely that a comment was posted.

10. **R10 — Writer-path test exists, same pattern as section 11-12.**
    Source: acceptance bullet 2's `check:` line verbatim. Check: a test
    asserts the comment originates from the gate's own code path (stub-`gh`
    call site), matching the existing section-11/12 writer-path test
    convention.

## Out of scope (phase 2 will not re-litigate)

- Detection-pattern edge cases already named as open by architecture.md's
  Resolution path (e.g. `gh issue close` aliases, non-`gh` merge paths) —
  those are implementation-phase scouting territory per that document, not
  a conformance gap unless the delivered code claims to have closed them.
- Code-quality judgment (naming, structure, efficiency) — this role
  renders per-requirement fidelity verdicts only, never a holistic quality
  read.

## Method (phase 2, once approved)

Artifact-only review: phase 2 works from `delegated-judgment-gate.sh`,
`test_delegated_judgment_gate.py`, and the two spec documents (architecture.md,
issue #597 body) only — the builder's implementation.md prose (`Why`,
`What did not work`) is not read as evidence for verdicts, consistent with
this role's artifact-only rulebook; it may be cited only to locate code,
never to substitute for reading the code directly.

## What did not work

(none yet — phase 1, no verdicts attempted)

## loop_state

kind: proposal
loop_state: scope-proposed

## Open findings

None at phase 1. R5 and R8 are flagged above as requiring closer reading in
phase 2 before a verdict can be rendered; R8 in particular may resolve to
Unverifiable-pending-further-code-read rather than a contradiction, once
the section-12 event-posting arms are read directly.

## Next steps

Await approval (`APPROVE issue-597/conformance-review` per contract v3
s19, single-account mode). On approval: render the phase-2 per-requirement
verdicts (R1-R10 above) in `docs/issue-597/reports/conformance-review.md`,
using `review-traceability:finding-record` to write one verdict row per
requirement, and `review-severity:severity-classification` only if a
finding's risk needs explicit weighting.

## Resolution path

Phase 2 resolves R5/R8 by direct code read (the section-12 event arms in
`delegated-judgment-gate.sh`, and a literal re-check of the two acceptance
wordings side by side) before assigning verdicts.
