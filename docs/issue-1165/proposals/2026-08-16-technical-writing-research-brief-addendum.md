---
status: proposed
files:
  - docs/issue-1165/proposals/2026-08-16-technical-writing-research-brief-addendum.md
---

# issue-1165 (technical-writing, step 1 continued): research-brief addendum — document side

kind: proposal
subject: issue-1165

Proposal: docs/issue-1165/proposals/2026-08-16-technical-writing-research-brief-addendum.md

## Background

This amends `docs/issue-1165/proposals/2026-08-13-technical-writing-human-comprehensibility.md`
(already merged, PR #1168) against the operator's 2026-08-16 research
brief comment on issue #1165 (canonical: issue #1165 comment,
"Research brief for step 1 (2026-08-16 backlog drive...)", read this
turn). That brief supplies evidence grades the 2026-08-13 proposal did
not yet have: production-adoption evidence for the tier-1 shape,
readability-formula invalidity, LLM-as-judge reliability limits, and
format-only-gate insufficiency. Design/spec only, per this step's scope
— no gate/spec/hook file lands here.

## Target reader

Same as the base proposal: a phase-2 implementing session copying the
(now revised) tier-1/tier-2 shape into `roles/specs/technical-
writing.spec.json`'s `quality_bar` array and into on-the-record's
record-scaffold/report-framing surfaces.

## Proposed structure

Six numbered points follow (§"What the brief changes"), each keyed to
one clause of the 2026-08-16 brief, then a revised tier-1/tier-2/tier-3
summary, the reconciliation restatement, rationale, and the phase-2
plan delta.

## What the brief changes

1. **`changed_content_only`, a sixth tier-1 rule (new).** The brief's
   evidence-graded finding: "Vale-style deterministic prose/structure
   linting is the only automatable tier with strong production
   adoption (GitLab, Datadog, Grafana, Meilisearch); convergent
   adoption pattern: FEW rules, changed-lines-only enforcement, inline
   escape hatch — otherwise documented developer revolt." The base
   proposal's five tier-1 rules (lead_paragraph_present,
   enumeration_cap, section_size_bound, no_raw_dump,
   convention_family_named) already satisfy "few" and "structural"; none
   of them yet scope enforcement to changed content only — each runs
   over the whole document/record body. Add: **tier-1 rules 2-5
   (enumeration_cap, section_size_bound, no_raw_dump,
   convention_family_named) apply only to sections that contain
   changed content in the diff being checked** (a record/report
   revision, or a document's edited sections); rule 1
   (lead_paragraph_present) is the one exception and stays whole-
   document, because a lead paragraph is a document-level property with
   no "changed" sub-unit to scope to — a document either opens with one
   or it does not. Rationale for the split, not a blanket exemption:
   the brief's adoption evidence is about avoiding false-positive noise
   on *pre-existing* content a contributor did not touch (the
   documented "developer revolt" failure mode); a document with no lead
   paragraph at all is not pre-existing-content noise, it is a shape
   defect in the artifact as a whole. `verification_method`: same
   automated structural scan as the other rules, with input scoped to
   the diff hunk boundaries (mirrors Vale's own changed-lines-only
   integration mode, and `gates/record_lint.py`'s existing pattern of
   operating on the record being checked, not the whole repo).

2. **Readability formulas: explicitly out, stated not silently
   omitted.** The brief grades Flesch-style readability formulas "C,
   invalid as a hard gate for technical text — use never or as soft
   signal only." The base proposal never proposed one, but did not
   record the rejection, so a later reader could not tell "not
   considered" from "considered and rejected." Recorded here: no tier-1
   or tier-2 rule in this design is or will become a readability-
   formula threshold (e.g. a Flesch-Kincaid grade-level gate);
   `no_raw_dump`/`section_size_bound`/`enumeration_cap` stay structural
   presence/count checks, never a formula score.

3. **Tier-2 stays three items, not four — genre-shape-match moves.**
   The brief: "LLM-as-judge: reliable specifically on coherence/
   relevance-class criteria with explicit rubrics ... reliable only as
   3 binary questions (what changed / why / what next after one pass),
   no style comments." Amendment 2 (2026-08-13, folded into the base
   proposal) added a fourth tier-2 item, `genre-shape-match`
   ("does this document's shape match its named convention family").
   That item is style/shape judgment, not a what/why/what-next
   comprehension question — exactly the class the brief's evidence says
   an LLM judge is *not* reliably calibrated on ("unreliable on
   fluency/consistency"). Resolution: **demote `genre-shape-match` out
   of tier 2**; its automatable half already exists as tier-1's
   `convention_family_named` rule (does the document *name* a
   convention family — a presence check, not a match judgment); its
   non-automatable half (does the shape actually *match* the named
   family) moves to **tier 3** (sampled deep review by the owning
   communication-domain role), where a full human/role read — not a
   single sampled binary LLM question — is the right-weight instrument
   for a judgment this evidence-grade-uncertain. Tier 2 for documents is
   now exactly the three items the base proposal opened with
   (what-changed / why / what-next), matching this task's own
   deliverable framing ("three-binary-question new-reader checklist")
   and the brief's evidence ceiling.

4. **Format-only-gate insufficiency confirms, does not change,
   existing tier-1 design.** The brief: "Format-only gates (PR
   templates, commitlint) are proven insufficient for content quality
   (empirical PR studies) — tier-1 must check structure presence, not
   content quality." This is exactly what the base proposal already
   does (§1 note: "The *semantic* claim ... is not automatable
   ... duplicated in tier 1 at all"); no rule changes, recorded here as
   confirming evidence rather than a new constraint.

5. **LLM-judge cost/reliability discipline folds into tier 2/3
   `verification_method` wording, not new rules.** The brief: "pin
   judge model + rubric; cost means SAMPLED use only." This was already
   tier 3's design (base proposal §3, "Sampling frequency is a
   tunable ... phase 2 should start with a small fixed sample"). New
   here: tier 2's `verification_method: human-review-checklist` note
   should also record that when tier 2 is executed by an LLM judge
   rather than a human reviewer, the judge model and the exact three-
   question rubric text must be pinned and stated in the verdict record
   (not re-derived per invocation) — this is a wording addition to
   `verification_method`, not a new tier or rule.

6. **No end-to-end outcome evidence — effectiveness measurement is a
   phase-2 open item, not assumed.** The brief: "No source demonstrates
   end-to-end comprehension-outcome improvement from any automated
   gate — effectiveness measurement must be built in, not assumed."
   This design does not claim tier-1/tier-2 passing implies readers
   actually comprehend better; phase 2's plan (below) adds an explicit
   item to track pass/fail outcomes against tier-3's sampled human
   verdicts over time, so the gate's own effectiveness becomes
   observable rather than asserted.

## Revised tier summary (document side, supersedes base proposal §1/§2 in the two points above)

- **Tier 1** (six rules, all `verification_method: automated
  structural scan`): lead_paragraph_present (whole-document scope),
  enumeration_cap, section_size_bound, no_raw_dump,
  convention_family_named (all four changed-content-only scoped),
  **changed_content_only** is not itself a seventh rule but the scoping
  discipline rules 2-5 now carry — listed here as a named property of
  the rule set, matching this task's own framing ("few, structural,
  changed-content-only, escape hatch"). Escape hatch: unchanged from
  the base proposal — `section_size_bound`'s named single-indivisible-
  artifact exception and `convention_family_named`'s `none-applicable`
  + stated-reason exception remain the two inline escape points; no new
  escape hatch is added, none is needed (the changed-content-only scope
  itself is the noise-reduction mechanism the brief's adoption evidence
  calls for, not an escape hatch on top of it).
- **Tier 2** (three items, `verification_method: human-review-
  checklist`, sampled-LLM-judge-eligible with pinned model+rubric):
  what-changed, why, what-next. `genre-shape-match` removed (see point
  3).
- **Tier 3** (sampled deep review, owning role, tunable frequency):
  gains one item — does the document's shape actually match its named
  convention family (moved from tier 2, point 3) — alongside the base
  proposal's existing Diátaxis-fit / style-guide-compliance sampled
  review scope.

## Reconciliation with required-field record contracts

Unchanged from the base proposal §4: structured fields
(`doc_id`/`quadrant`/frontmatter) stay outside tiers 1-3; prose-body
fields (`content`, on-the-record's own `## Summary of work` etc.) stay
in scope. The changed-content-only scoping (point 1) narrows *where
inside* a prose field a rule fires, it does not touch which fields are
in scope — no new reconciliation surface opens.

## Rationale

- Every point above traces to a named clause of the 2026-08-16 brief
  (quoted inline per point), per the operator's THOROUGH/web-verified
  standard already carried into the base proposal's amendment 2 — this
  addendum's own source is the brief comment itself (already a
  synthesized, risk-graded research artifact per its own text: "web
  sweep + risk grading done in orchestration session; full sources
  therein"), so citation here is to that comment, not a re-run of the
  underlying web sweep.
- Demoting `genre-shape-match` (point 3) rather than dropping it
  preserves amendment 2's convention-conformance requirement in full —
  it changes *which tier* judges shape-match, not whether the criterion
  exists, keeping issue requirement 4's anti-nitpick bound intact (a
  tier-3 human/role read is the correctly-weighted instrument for a
  judgment call the brief's own evidence says a sampled LLM binary
  question is not calibrated for).

## Plan for phase 2 (unchanged in kind, two additions)

Base proposal's four-step plan stands; add:
- Step 1 gate fixtures also cover the changed-content-only scope (a
  fixture where a pre-existing unchanged section would fail
  enumeration_cap/no_raw_dump/section_size_bound/convention_family_named
  but the check passes because that section carries no diff hunk, plus
  a fixture where the same failure inside a changed section still
  fails).
- Step 3's tier-2 live review also records, going forward, whether the
  reviewed record's tier-1/tier-2 pass correlated with a genuinely
  comprehensible artifact per that same review's own judgment — the
  seed of point 6's effectiveness tracking, not a new mechanism.

## Out of scope

Scope gate: this addendum is document-side design only — it does not
land any spec/hook/gate/template file, and it does not decide anything
for another role's surface.

- Screen-side reconciliation of the same brief — content-design's own
  parallel step-1 deliverable.
- Landing any of the revised tier-1/tier-2/tier-3 shape into
  `roles/specs/technical-writing.spec.json`, `gates/`, or
  `record-scaffold.sh`/`report-framing-check.sh` — phase 2, listed
  above, not this PR.
- Fixing the tier-3 sample size/frequency number — still a tunable, per
  the base proposal.

## Approval

Per role-handoff contract v3 s19: phase 2 opens on an approvers.md
Approve or the exact single-account string `APPROVE issue-1165/
technical-writing`. (Note: that exact string already appears twice on
the issue, both before this addendum existed — an approval of the
2026-08-13 base proposal's content, not of this addendum's post-dated
revisions; phase 2 for the points in this addendum still needs its own
fresh approval covering this file.)

## What did not work

None.
