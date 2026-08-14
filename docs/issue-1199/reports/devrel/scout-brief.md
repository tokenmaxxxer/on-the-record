kind: report
subject: issue-1199
doc-type: reference

# devrel — scout brief (phase-1, issue #1199)

Mode: batched-sequential WebSearch fan-out this turn (3 queries run in
this session, not concurrently dispatched as parallel subagents — noted
as the batched-sequential fallback per the scout directive). 1 sweep
round; saturation reached after judge point 1 — each query returned a
clear adoption-evidenced leader mapping to a distinct devrel tool
category (docs-as-code, OpenAPI reference rendering, SDK generation,
hosted API-docs platform, developer-community analytics), no
conflicting signals to reconcile, so no deepening round was run.

canonical: WebSearch results, this turn's tool transcript (queries:
"most popular developer relations DevRel tools API documentation
platform GitHub stars 2026", "developer experience DX changelog tool
adoption OpenAPI SDK generation Stainless Fern GitHub stars downloads",
"Docusaurus GitHub stars Scalar GitHub stars developer community
analytics tool Orbit Common Room adoption")

## Category must-bes and adopted design moves

1. **Docs-as-code (Docusaurus)** — adoption: 65,100+ GitHub stars as of
   mid-2026 per the WebSearch results, Meta-maintained, cited as the
   standard choice for engineering teams wanting full control over doc
   infrastructure. Design move: doc content is versioned Markdown/MDX
   committed in the same repo pipeline as the product, with a formal
   per-release snapshot feature rather than one floating page tree.
   Gap fit: devrel's `doc-type:`/`segment:` record fields never require
   naming which product version a doc set targets.

2. **OpenAPI reference rendering (Scalar)** — adoption: 15,500+ GitHub
   stars per the WebSearch results, positioned as first-class OpenAPI/
   Swagger support competing directly with Redoc/Swagger UI. Design
   move: the reference page renders directly from the spec file at
   build time, so page and spec cannot disagree. Gap fit: devrel's
   "Proposed surface decision" proposal section has no requirement to
   name a machine-readable spec as source of truth when one exists.

3. **SDK generation (Stainless)** — adoption: vendor-stated production
   use generating the official SDKs for OpenAI, Anthropic, and
   Cloudflare per the WebSearch results. Design move: SDKs and sample
   code are generated mechanically from the same spec driving the
   reference, with automated per-release changelog generation so
   sample code can't silently drift from the shipped API. Gap fit:
   devrel's "Adoption-friction evidence" section can cite sample code
   as evidence without naming what spec/version it was verified
   against.

4. **Hosted API-docs platform (ReadMe)** — adoption: cited across the
   WebSearch results as the platform for "mature API docs teams," with
   2026-added AI-assisted search answering integration questions
   directly against the current docs. Design move: pairs a spec-driven
   reference with an interactive try-it console, separating "the
   reference is wrong/incomplete" friction from "getting from reference
   to a first successful call" friction. Gap fit: devrel's
   "Adoption-friction list" record header has no requirement to
   distinguish these two failure points.

5. **Developer-community analytics (Orbit)** — adoption: per the
   WebSearch results, Orbit tracks GitHub/forum/social activity
   specifically to identify developer advocates, competing with Common
   Room in the "community signal aggregation" category. Design move:
   tracks discrete engagement events per individual (first star, first
   issue, first PR, repeat contribution) instead of one lagging
   adopted/not-adopted aggregate. Gap fit: devrel's
   `product_journey_stage:` metric field has no guidance tying the
   chosen enum value to which discrete event the recorded metric
   actually corresponds to.

## Adopt / skip

Adopt: the design-move-level lesson from each tool (spec-as-source-of-
truth, versioned doc snapshots, friction-point separation, discrete
event-to-stage mapping) as prose guidance in the existing handbook.
Skip: installing, depending on, or recommending any of the 5 tools
themselves — devrel's own output is markdown records/proposals, not a
docs site or SDK, so the tools are a design-pattern reference only, not
a dependency candidate.

Stages used: 1 (sweep) + judge point 1 (no deepening needed).

Sources:
- https://www.mintlify.com/library/7-best-software-documentation-tools-in-2026
- https://www.devtoolreviews.com/reviews/mintlify-vs-gitbook-vs-docusaurus-vs-readme-2026
- https://herothemes.com/blog/docusaurus-alternatives/
- https://github.com/scalar/scalar
- https://www.stainless.com/customers/replicate/
- https://www.speakeasy.com/blog/choosing-an-sdk-vendor/
- https://www.thedevrelcollective.com/blog/choosing-the-right-community-tool-for-developer-relations
- https://www.leadpipe.com/blog/common-room-vs-orbit/

## kind / loop_state

kind: report
loop_state: phase-1-scouted
