---
subject: issue-1199
role: devrel
loop_state: scope-proposed
status: proposed
files:
  - docs/handbooks/devrel-plugins.md
  - docs/issue-1199/reports/devrel.md
---

# Proposal: fold devrel's surveyed tool landscape into the rulebook (issue-1199)

All file paths below (except this repo's own record) live in the
separate rulebook repo (tokenmaxxxer/devrel-rulebook, cloned this turn
at /tmp/devrel-rulebook-1199 — see docs/issue-1199/reports/devrel/survey.md),
not in this working tree; phase 2 branches and commits there directly.

## Request

Per issue-1199 (northpole req#1/req#5, consult-log 2026-08-13T06:10:35
entry), add a bounded tool-learnings addition to
docs/handbooks/devrel-plugins.md in tokenmaxxxer/devrel-rulebook: five
surveyed devrel-adjacent tools, each with adoption evidence, problem/
how/learning, and a named upgrade to existing proposal/record content
guidance — never a tool catalog, never a gate-code change.

## Problem/Motivation

devrel-rulebook's 4 methodology gates (`phase-order`,
`rfc-seven-section`, `diataxis-record`, `metric-record`) enforce
structural presence only — a header exists, a field is non-empty, an
enum is one of four values — with no prose guidance on content
quality. The handbook that documents those gates has never learned
from the tool ecosystems devrel practitioners actually rely on (API
docs platforms, SDK generators, OpenAPI reference renderers, developer-
community analytics), so the guidance a devrel author gets for filling
"Adoption-friction evidence," "Adoption-friction list," and
`product_journey_stage:` stays generic where those tools' design moves
would make it concrete.

## Proposed surface decision

Add one "Tool learnings (issue-1199)" section to
docs/handbooks/devrel-plugins.md, five entries, each capped to a short
paragraph, each naming which existing gate-required field/section it
upgrades (never adding a new required field — content guidance only):

1. **Docusaurus** (65,100+ GitHub stars as of mid-2026, Meta-
   maintained — see scout-brief Sources). Problem: a doc set drifts
   from the product surface it describes because nothing ties the
   record to a version. How: content is versioned Markdown/MDX with a
   formal per-release snapshot feature. Upgrades: guidance on filling
   `doc-type:`/`segment:` — name the product version/release the doc
   set targets, not an undated snapshot.

2. **Scalar** (15,500+ GitHub stars, first-class OpenAPI/Swagger
   rendering — see scout-brief Sources). Problem: a hand-described API
   surface silently diverges from its real spec. How: the reference
   renders directly from the spec file at build time. Upgrades:
   guidance on the "Proposed surface decision" proposal section — when
   a machine-readable spec exists, name it as the surface's source of
   truth rather than describing the surface in free prose alone.

3. **ReadMe** (cited across the WebSearch results as the platform for
   mature API-docs teams, 2026 AI-assisted search answering
   integration questions against current docs — see scout-brief
   Sources). Problem: "friction" as a single bucket conflates a wrong/
   incomplete reference with a hard path from reference to first
   successful call. How: pairs the reference with an interactive
   try-it console, keeping the two failure points visibly distinct.
   Upgrades: guidance on the "Adoption-friction list" record header —
   each entry states which of the two failure points it is.

4. **Orbit** (developer-community analytics tracking GitHub/forum/
   social activity to identify advocates — see scout-brief Sources).
   Problem: `product_journey_stage:` values default to `adoption`
   regardless of what the metric measures. How: tracks discrete
   engagement events (first star, first issue, first PR, repeat
   contribution) instead of one lagging aggregate. Upgrades: guidance
   on choosing `product_journey_stage:` — tie the enum value to the
   discrete event the recorded metric corresponds to.

docs/issue-1199/reports/devrel.md is phase-2 output, written only
after approval opens phase 2, per contract v3 s19.

## Adoption-friction evidence

**Stainless** (vendor-stated production use generating the official
SDKs for OpenAI, Anthropic, and Cloudflare — see scout-brief Sources).
Problem: sample code cited as adoption evidence rots silently as the
API changes, because nothing regenerates it. How: SDKs/sample code are
generated mechanically from the same spec driving the reference, with
automated per-release changelog generation, so drift is caught at
build time rather than by a developer hitting a stale example.
Upgrades: guidance on the "Adoption-friction evidence" proposal
section itself — sample code cited as evidence must name the spec/
version it was verified against, not stand as freestanding proof.

## Alternatives

- New required gate fields for each learning (e.g. a `spec_source:`
  line) — rejected: issue-1199 requirement 3 and the brand-design
  fold-in precedent both scope this unit to content/prose, not
  mechanical gate changes; a gate-shape change belongs to a
  cross-cutting follow-up at the issue level, not one role's fold-in.
- A new standalone `docs/handbooks/devrel-tool-guidance.md` file
  instead of extending devrel-plugins.md — rejected: the existing
  handbook is the sole content-bearing doc this rulebook has for
  authoring guidance; splitting it would fragment the one place an
  author already reads before writing a proposal/record.

## User impact

Authors writing a devrel proposal or record get five concrete content
checks tied to tools their own domain already runs at scale, instead
of generic field-presence requirements; no gate becomes stricter, so
no previously-passing proposal/record starts failing.

## Sources

See docs/issue-1199/reports/devrel/scout-brief.md for the full source
list (8 URLs consulted this turn).
