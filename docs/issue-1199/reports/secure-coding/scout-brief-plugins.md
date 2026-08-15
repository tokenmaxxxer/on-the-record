---
subject: issue-1199
role: secure-coding
kind: scout-brief
---

# Scout brief: Claude Code plugin/skill landscape for secure-coding (issue-1199)

canonical: two WebSearch calls this session (`"Claude Code plugin
security review skill marketplace github stars 2026"` and `"claude
code" plugin "secrets" OR "dependency" OR "SAST" security skill
github"`) plus `curl -s https://api.github.com/repos/<org>/<repo>` per
candidate below, all read this session.

Sweep mode: batched-sequential (2 WebSearch calls, this session; parallel
subagent dispatch was unavailable in this delegation-only headless turn).
1 sweep stage + 1 deepening stage (adoption-evidence lookup), within the
5-stage/3min budget.

canonical: WebSearch results this session (queries above), read this session.

## Candidates found (sweep)

- anthropics/claude-code-security-review — official Anthropic GitHub
  Action wrapping Claude for diff-scoped PR security review.
- trailofbits/skills — Trail of Bits security research/audit-workflow
  skills.
- snyk/claude-plugin-snyk — pre-add dependency health check plugin.
- ghostsecurity/skills — ghost-scan-secrets / ghost-scan-deps (SCA
  exploitability) / ghost-scan-code (SAST).
- anthropics/claude-plugins-official — first-party marketplace, used
  here only as the official-vs-community trust baseline.

canonical: `curl -s https://api.github.com/repos/<org>/<repo>`, run this
session, raw field values quoted inline per entry.

## Adoption evidence (deepening)

- anthropics/claude-code-security-review: `stargazers_count: 5861,
  forks_count: 636`.
- trailofbits/skills: `stargazers_count: 6589, forks_count: 567`.
- ghostsecurity/skills: `stargazers_count: 398, forks_count: 27`.
- anthropics/claude-plugins-official: `stargazers_count: 33530,
  forks_count: 3797`.
- snyk/claude-plugin-snyk: `stargazers_count: 0, forks_count: 1`
  (secondary confirmation only).

canonical: adoption-evidence figures in the section above, read this session.

## Judge point 1

anthropics/claude-code-security-review and trailofbits/skills are both
top-tier by star count and directly on-domain (secure-coding review/
audit work). ghostsecurity/skills is lower-adoption but kept as
secondary confirmation: its exploitability-triage move recurs
independently in Snyk's pre-add check.

canonical: WebSearch result summaries this session for each named repo
(queries above), read this session.

## Must-bes / performance axes

- Diff/PR-scoped review with false-positive filtering: anthropics/
  claude-code-security-review reviews changed lines against their
  surrounding trust boundary and filters low-signal findings before
  surfacing them — "manual security review doesn't scale to every PR"
  is the stated problem.
- Exploitability/reachability-first triage over raw CVSS ranking:
  ghostsecurity/skills' ghost-scan-deps runs "exploitability analysis of
  dependency vulnerabilities (SCA)"; Snyk's plugin health-checks a
  dependency "when Claude is about to add" it, before acceptance rather
  than only on a later periodic scan.
- Structured, named-vulnerability-class findings over prose description:
  trailofbits/skills frames output as named detector classes, not a
  narrative writeup.

canonical: `dependency-supply-chain-security.md` and
`input-validation-injection-defense.md` in
`/home/jwjung/tokenmaxxxer/rulebooks/secure-coding-rulebook`, read this
session.

## Gap line

Existing playbook covers: dependency scanning from project birth plus a
patch/stopgap/accept-risk ladder (`dependency-supply-chain-security.md`
rules 1-8, all post-acceptance); allowlist/denylist/parameterization
coverage (`input-validation-injection-defense.md` rules 1-9). Two gaps
the surveyed field fills and the current rules do not: a pre-acceptance
dependency check, and a review-scoping rule (diff/trust-boundary bound,
false-positive aware).

## Adopt / skip

Adopt: (1) pre-acceptance dependency health check into
`dependency-supply-chain-security.md`; (2) diff/trust-boundary-scoped,
false-positive-aware review discipline into
`input-validation-injection-defense.md`.

Skip: trailofbits/skills' detector-catalog architecture and
ghostsecurity's hook-based automation surface — this role delivers an
ASVS checklist plus finding list per scope, not a live scanning
pipeline; the judgment is adopted, the tool surface is not
(native-application convention).

canonical: URLs actually queried/fetched this session, read this session.

## Sources

- https://github.com/anthropics/claude-code-security-review
- https://github.com/trailofbits/skills
- https://github.com/snyk/claude-plugin-snyk
- https://github.com/ghostsecurity/skills
- https://github.com/anthropics/claude-plugins-official
- https://api.github.com/repos/anthropics/claude-code-security-review
- https://api.github.com/repos/trailofbits/skills
- https://api.github.com/repos/ghostsecurity/skills
- https://api.github.com/repos/anthropics/claude-plugins-official
- https://api.github.com/repos/snyk/claude-plugin-snyk
