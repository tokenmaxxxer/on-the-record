kind: report
subject: issue-1199
doc-type: reference

## Scout brief: Claude Code plugin/skill ecosystem for api-design

2026-08-14 amendment rework — supersedes the earlier domain-tool-basis
survey (Spectral/buf/Optic/Redocly) recorded in this issue's prior
landed record; this brief covers the CLAUDE CODE PLUGIN ecosystem per
the amendment's narrowed survey target.
canonical: this session's WebSearch/WebFetch transcript this turn (3
WebSearch calls, 3 WebFetch calls).
Mode: batched-sequential (3 WebSearch calls this turn, one round; no
parallel Agent fan-out used for this rework pass) plus 3 WebFetch
attempts, two of which returned HTTP 429 (noted below).
canonical: this session's WebFetch tool-result transcript this turn
(mcpmarket.com/tools/skills/openapi-design and
mcpmarket.com/tools/skills/api-design-best-practices-1 both returned
HTTP 429).
Stages used: 1 sweep + 1 deepening fetch = 2 of the 5-stage budget;
stopped at judge point 1 — the sweep's three queries converged on the
same marketplace repo and the same four API-relevant skills, so a
further round would not change the fold-in.

### Exemplar marketplace

`jeremylongshore/claude-code-plugins-plus-skills` — 2.6k GitHub stars
canonical: this session's WebFetch of
https://github.com/jeremylongshore/claude-code-plugins-plus-skills
this turn (star badge read directly off the fetched repo page).
Listing 471 plugins/3,069 skills/347 agents, packaged with the `ccpi`
CLI package manager at tonsofskills.com. Used as the adoption-evidence
anchor for the four skills below (star count is the marketplace's;
each skill entry itself has no independent public star count exposed
on the marketplace page).
Source: https://github.com/jeremylongshore/claude-code-plugins-plus-skills

### Skills folded in (-> playbook/tool-landscape.md rules 1-4)

1. **api-mock-server**. Problem: consumers can't start integrating
   until a real backend exists, blocking parallel work. How: generates
   a mock server directly from an OpenAPI spec. Learning -> rule 1
   (a published interface-spec should be able to drive a mock; that's
   also a completeness check on the spec itself).
2. **api-schema-validator**. Problem: a documented payload schema can
   silently drift from what the service actually accepts once hand-
   maintained validation diverges from the doc. How: validates API
   schemas with JSON Schema/Joi/Yup/Zod. Learning -> rule 2 (schema
   must be mechanically enforced at the boundary, not left as prose).
3. **api-sdk-generator**. Problem: every version bump requires
   consumers to hand-update hand-written clients. How: generates client
   SDKs from OpenAPI specs for multiple languages. Learning -> rule 3
   (treat SDK regeneration as part of shipping a version, not a
   consumer-side afterthought).
4. **api-contract-generator**. Problem: a spec and a deprecation-plan
   are prose promises that a provider still satisfies what a consumer
   actually calls; nothing fails loudly when that breaks. How:
   generates API contracts for consumer-driven contract testing.
   Learning -> rule 4 (make compatibility a run artifact, not only a
   policy statement).
canonical: this session's WebFetch of
https://github.com/jeremylongshore/claude-code-plugins-plus-skills
this turn (all four skill descriptions read from the fetched
marketplace listing page).
Source (all four): https://github.com/jeremylongshore/claude-code-plugins-plus-skills

### Noted but not folded in

derived: this session's WebSearch transcript this turn, query
`"claude code" plugin marketplace most popular list
awesome-claude-code-plugins` — top result snippet reported
`superpowers` at 752,000+ installs.
`superpowers` is the single highest-adoption community plugin surfaced
in this sweep, but it is a general workflow plugin (brainstorming,
sub-agent driven dev, TDD, code review) with no API-design-specific
design move to extract — excluded per the amendment's domain-relevance
requirement, not for lack of adoption evidence.

`mcpmarket.com`'s dedicated `openapi-design` and
`api-design-best-practices-1` skill pages returned HTTP 429 on fetch
this turn (rate-limited)
canonical: this session's WebFetch tool-result transcript this turn
(both calls returned "The server returned HTTP 429 Too Many Requests").
and were not deepened further given the 2-stage budget already spent
and the marketplace convergence already observed; not used as a
source.

### Gap line

The prior (superseded) domain-tool survey already covered spec-lint/
breaking-change/bundling as CI-gate concerns (Spectral, buf, Optic-
successors, Redocly). This plugin sweep's must-bes are downstream of
that: once a spec exists and is linted, the plugin ecosystem's
recurring pattern is generate-from-spec (mock server, validator, SDK,
contract test) rather than hand-maintain-alongside-spec — the four
rules above target exactly that gap, none of which the prior fold-in's
rules 13-15 already cover.
