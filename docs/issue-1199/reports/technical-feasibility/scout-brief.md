# Scout brief: technical-feasibility Claude Code plugin-ecosystem sweep (issue-1199)

Mode: batched-sequential (curl against the GitHub Search/Repos API,
this session, one query per axis) — parallel WebFetch/Agent dispatch
was not needed since each query resolved directly via curl.
Stages used: 2 (sweep + one deepening/README-read round). Wall-clock:
well under the 3-minute budget.

Star/fork counts per candidate are not restated here as bare numbers;
each candidate's exact figure is cited with its `curl` canonical
source in this round's proposal (Candidates considered section) and
carried forward into the record — this brief lists rank order only.

## Current-state gaps (from reading the five existing axis files first)

- reversibility-and-spike-scoping.md had no rule forcing explicit
  tradeoff articulation before a candidate is accepted — a session
  could pick the first workable spike design without stating what it
  forecloses.
- threat-model-disposition.md disposed STRIDE rows as
  mitigated/accepted/deferred with no confidence gradation — a
  one-off manual check and a repeatable automated gate both read as
  equally strong "mitigated."
- verdict-and-timebox-selection.md had no rule distinguishing a
  hard-stop blocking condition from a soft caveat noted inside a
  passing verdict.
- build-vs-buy-dependency-health.md (rules 1-10, see file) already
  had strong OpenSSF Scorecard-based rules but no rule on calibrating
  the bar to the candidate project's own maturity stage.
- license-and-regulatory-risk.md used a binary framing with no graded
  risk tier.

## Sweep (Stage 1, GitHub Search API, this session), by rank

- claude+skill+architecture+decision+record → ranked: study8677/architecture-copilot
  highest, then terrylica/cc-skills, then
  caiaffa/claude-code-ultimate-engineering-system, then
  diogoX451/principal-software-architect.
- claude+skill+threat+model+stride → ranked: allsmog/vuln-scout
  highest, then ridges0315/security-audit, then
  aguleykovn8n/security-audit-skill.
- claude+skill+license+scan → ranked: hoangthiep08/license-audit
  (best domain match; lowest star count of the set), belschak/publish-gate,
  ndisisnd/mkpub.
- claude+plugin+spike → canonical: `curl -s "https://api.github.com/search/repositories?q=claude+plugin+spike+in:name,description&sort=stars&order=desc&per_page=5"`,
  run this session — top hits were a plugin marketplace listing and
  unrelated ops tooling, none domain-matched to spike-scoping; no
  candidate adopted from this query.
- claude+skill+dependency+health → ranked: SomeStay07/claude-doctor-skill
  highest.
- claude+skill+feasibility → canonical: `curl -s "https://api.github.com/search/repositories?q=claude+skill+feasibility+in:name,description&sort=stars&order=desc"`,
  run this session — top hit Mostafa-derwy/claude-financial-modeling-skill
  is real-estate-domain, not software-feasibility; not adopted here.

## Judge point 1

Overlap signal: architecture/ADR-shaped skills cluster around
study8677 and terrylica; security/threat-model skills cluster around
allsmog; no skill directly named "build-vs-buy" or "spike-scoping"
exists at meaningful adoption, so the closest adjacent-domain match
(project-health auditing, dependency scanning) was used instead —
consistent with the risk-management/conformance-review precedent of
mapping the closest domain match onto an axis rather than requiring an
exact name match (see this repo's docs/issue-1199/reports/conformance-review.md
and docs/issue-1199/reports/risk-management.md).

## Deepening (Stage 2, README/doc fetches, this session)

Fetched README.md (or, for vuln-scout, its feature-maturity doc,
external to this repo) for study8677/architecture-copilot,
allsmog/vuln-scout, SomeStay07/claude-doctor-skill,
hoangthiep08/license-audit. Quotes and design-move extraction recorded
in this round's own proposal and record (same commit set as this
brief).

## Judge point 2 (saturation)

A third deepening round would not change any fold-in decision: each
of the five axis files already has exactly one clear best-matched
surveyed tool (vuln-scout supplies two, for the two axes with the
thinnest current rule coverage). Stopped after stage 2.

## Sources

- https://api.github.com/repos/study8677/architecture-copilot
- https://raw.githubusercontent.com/study8677/architecture-copilot/main/README.md
- https://api.github.com/repos/terrylica/cc-skills
- https://raw.githubusercontent.com/terrylica/cc-skills/main/README.md
- https://api.github.com/repos/allsmog/vuln-scout
- https://raw.githubusercontent.com/allsmog/vuln-scout/main/README.md
- https://raw.githubusercontent.com/allsmog/vuln-scout/main/docs/feature-maturity.md
- https://api.github.com/repos/SomeStay07/claude-doctor-skill
- https://raw.githubusercontent.com/SomeStay07/claude-doctor-skill/main/README.md
- https://api.github.com/repos/hoangthiep08/license-audit
- https://raw.githubusercontent.com/hoangthiep08/license-audit/master/README.md
- https://api.github.com/search/repositories?q=claude+skill+threat+model+stride
- https://api.github.com/search/repositories?q=claude+skill+dependency+health
