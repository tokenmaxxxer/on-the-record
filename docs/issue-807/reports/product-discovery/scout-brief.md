---
kind: scout-brief
---

# Scout brief — issue #807

Mode: batched-sequential WebSearch (3 queries, one turn) — parallel Agent
fan-out was not needed at this width; angles: (a) adversarial-review
rubric literature for hollow-vs-valid LLM deliverables, (b) rubric-design
structural principles (checklist vs performance-level rubric), (c)
LLM-as-judge anti-anchoring / adversarial-refutation methods. 1 stage,
saturation reached after round 1 (all three angles converged on the same
handful of usable mechanisms).

## Must-bes (what a real methodology-validity check assumes)
- A rubric is not a checklist: it must describe distinct **quality
  levels** per criterion, not just presence/absence of fields (UCD/EJ1458026
  rubric-design guides; Snorkel "science of rubric design").
- Criteria must be MECE — non-overlapping, jointly covering the
  deliverable, each atomic (one aspect per criterion) — this is the
  structural-adequacy axis PReMISE audits rubrics against.
- A judge/reviewer must commit to an independent verdict **before**
  seeing the candidate's own reasoning, or its oversight collapses to
  agreement with whatever the candidate already asserted (anti-anchoring
  finding, arxiv 2607.05904).
- Adversarial robustness must be tested by construction, not assumed: the
  gold pattern is "edit the response so the correct verdict flips, then
  check the verifier's verdict flips with it" (Adversarial Validation
  Loop) — a rubric that never faces a deliberately-broken deliverable has
  no evidence it can catch one.

## Performance axes strong instruments compete on
1. **Reliability** — same deliverable, same verdict across repeated/
   independent runs (PReMISE's reliability axis).
2. **Adversarial robustness** — verdict survives an author trying to game
   it (PReMISE; Adversarial Validation Loop).
3. **Construct validity** — the rubric measures the capacity it claims to
   (domain judgment / deliverable validity / lens-finding), not a proxy
   that correlates with it by accident (arxiv "Measuring What Matters").

## Pattern to adopt
Independent-verdict-first + deliberate-flip test, composed: have a second
agent (same domain, no sight of the producing role's reasoning) render an
independent judgment on the SAME artifact, then separately run a
same-domain adversarial refutation pass against a version of the
deliverable with one substantive defect deliberately reintroduced — the
rubric passes only if the refutation pass's verdict flips when the defect
is reintroduced.
canonical: gh issue view 807 (read in full this session) — Acceptance
section, check clause: "an adversarial review confirms a produced
deliverable is domain-valid not surface, and the #776 harness emits a
methodology-validity signal that fails on a deliberately hollow role and
passes on the grounded one". The literature above converges on the same
mechanism shape independently of that clause.

## Pattern to skip
Generic LLM-as-judge holistic scoring (single judge, single pass, no
independent-commit, no adversarial flip-test) — multiple sources note it
is gameable and its high inter-rater agreement does not imply low
exploitability (PReMISE). Do not recommend it as the harness signal.

## Segment fit
canonical: `python3 -c` dump of `roles/specs/*.spec.json` `source_standard`
field, all 43 files, run this session (see survey.md for the full list).
Every role already carries a named methodology citation with a live URL —
the gap is not "no citation," it's that (a) no rubric grades the DEPTH of
judgment/deliverable/lens-finding methodology use behind that citation,
and (b) no adversarial-flip mechanism exists to tell a domain-valid
deliverable from a hollow one. The proposal targets exactly that gap, not
a from-scratch citation program.

## Gap line
Field must-be "rubric describes quality levels, not just presence" — MET
partially: source_standard's presence is already checked (canonical:
`roles/specs/security-threat-model.spec.json` `reference_resolution.
checked_by` = `on-the-record/hooks/role-spec-reference-guard.sh`, read
this session), but no per-role rubric grades the depth of
judgment/deliverable/lens-finding methodology use. Field must-be
"adversarial flip-test" — MISSING entirely: canonical:
`docs/specs/northpole-harness.md` §3 (read in full this session) — all 7
signals check delegation-event-presence / record-presence / build-exit-
code, none checks verdict-flips-on-injected-defect.

Sources:
- https://arxiv.org/html/2605.30803v1 (PReMISE: Policy Rubrics as Measurement Specifications for LLM Judges)
- https://arxiv.org/html/2604.25224 (Agreement-Gated Stress Testing / Adversarial Validation Loop pattern)
- https://openreview.net/pdf?id=mdA5lVvNcU (Measuring What Matters: Construct Validity in LLM Benchmarks)
- https://arxiv.org/pdf/2607.05904 (Self-Play Reward Hacking of Reference-Free LLM Judges — anti-anchoring finding)
- https://files.eric.ed.gov/fulltext/EJ1458026.pdf (Rubric Design — quality-level vs checklist distinction)
- https://snorkel.ai/blog/the-science-of-rubric-design/ (rubric structural principles, MECE)
