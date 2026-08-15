---
subject: issue-1199
role: risk-management
kind: scout-brief
---

# Scout brief: risk-management Claude Code plugin/skill fold-in (issue-1199)

Mode: parallel WebSearch fan-out (4 angles, 1 sweep round), 1 curl-based
adoption-check stage, 1 WebFetch deepening stage on the top 3 hits — 3
stages total, under the 5-stage/3min budget.

Survey-first: current rulebook state (`playbook/*.md`, main branch,
tokenmaxxxer/risk-management-rulebook) read before the sweep — 5 axis
files, 4-5 numbered rules each, ISO 31000/ISO 27005-style
likelihood-impact + response-strategy + appetite/tolerance +
monitoring-cadence + aggregation-consolidation methodology, no
identification-method-selection axis, no prioritization-ordering rule
distinct from raw score.

## Adoption evidence (GitHub API, this session)
- Sushegaad/Claude-Skills-Governance-Risk-and-Compliance: 829 stars, 170 forks
- borghei/Claude-Skills (risk-management-specialist skill): 479 stars, 109 forks
- Masriyan/Claude-Code-CyberSecurity-Skill: 335 stars, 60 forks
- ddunnock/claude-plugins (fmea-analysis skill): 10 stars — secondary,
  direct-domain-match confirmation only, not primary adoption evidence

## Must-bes (what the strong hits assume)
- Every risk-treatment recommendation cites the specific governance/
  regulatory clause it is anchored to, not a generic bucket
  (Sushegaad: NIST AI RMF skill "with per-risk AI RMF category
  citations (e.g. MAP 5.2)").
- Prioritization/action-ordering must not let a multiplicative score
  hide a high-severity, low-frequency risk (ddunnock fmea-analysis:
  "Action Priority... prioritizes Severity first, then Occurrence,
  then Detection. Unlike RPN (S×O×D), AP ensures safety-critical
  issues... are never ignored regardless of O and D").
- Control selection follows a hierarchy (source-elimination before
  add-on protection before information/monitoring), not a flat control
  list (borghei risk-management-specialist: "Applies hierarchy:
  inherent safety -> protective measures -> safety information").
- Residual risk is a distinct re-evaluation step after control
  application, not assumed from the pre-control rating (borghei:
  "residual-risk re-evaluation" as its own numbered lifecycle stage;
  Post-Production Monitoring stage "tracks signals, updates Risk
  Management File").
- Quantitative loss-expectancy scoring runs alongside the qualitative
  band, not instead of it (Masriyan: "risk register scoring (qualitative
  + ALE)").

## Performance axes these hits compete on
- Framework/citation traceability per risk line
- Severity-gated (not multiplied) prioritization
- Control-selection ordering discipline
- Explicit residual-risk lifecycle step

## Adopt / skip
- Adopt: severity-gated prioritization ordering; control-source-first
  hierarchy; explicit post-control residual re-score trigger; per-risk
  framework-clause anchoring; qualitative+quantitative (ALE) dual
  scoring.
- Skip: full FMEA/FTA/HAZOP method-selection machinery — out of this
  rulebook's existing axis scope (identification-method selection is
  not one of its 5 axes); not folded in this round.

## Gap line
Current rulebook already gates severity independently on the raw
likelihood-impact axis (`likelihood-impact-scale.md` rule 2) but has no
rule for how a *combined/rolled-up* prioritization queue orders
severity vs. likelihood, no control-hierarchy ordering rule, no
explicit residual-re-score trigger tied to control completion, no
framework-clause anchoring rule, and no dual qualitative+ALE scoring
rule. All five gaps map 1:1 onto the five existing axis files.

## Sources
- https://github.com/Sushegaad/Claude-Skills-Governance-Risk-and-Compliance
- https://github.com/borghei/Claude-Skills/blob/main/ra-qm-team/risk-management-specialist/SKILL.md
- https://github.com/ddunnock/claude-plugins/blob/main/skills/fmea-analysis/SKILL.md
- https://github.com/Masriyan/Claude-Code-CyberSecurity-Skill
- https://api.github.com/repos/Sushegaad/Claude-Skills-Governance-Risk-and-Compliance
- https://api.github.com/repos/borghei/Claude-Skills
- https://api.github.com/repos/ddunnock/claude-plugins
- https://api.github.com/repos/Masriyan/Claude-Code-CyberSecurity-Skill
