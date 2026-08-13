---
status: approved
files:
  - docs/issue-1199/reports/growth-analytics.md
---

# Proposal: growth-analytics tool-landscape fold-in (issue-1199)

## Intent
Survey the tool ecosystem growth-analytics practitioners rely on most,
with adoption evidence per tool, and fold the design moves those tools
embody into the role's own rulebook methodology — not as a tool catalog
or attribution, but as native rule upgrades to the existing
pre-registration, funnel-diagnosis, and result-trust walkthroughs.

## Constraints
- Adoption-evidence method only (stars/downloads/multi-source), no
  pretrained-recall listing (per issue-1199 requirement 1).
- Fold-in must upgrade the rulebook's own operating content (methodology
  files, not a catalog section); no "learned from X" attribution and no
  verbatim copying (per this turn's operator instruction, which narrows
  issue-1199 requirement 3's original "tool-learnings section" ask).
- Full evidence trail (tools surveyed, adoption evidence, insight
  mapping) lives only in this on-the-record report — not in the public
  rulebook.
- Named upgrade targets must be actually edited, not merely referenced.

## What will be done
Survey four tool categories real practitioners use (open-source
variant-testing/feature-flag platforms, open-source product analytics,
warehouse-native statistics engines, hosted product-analytics
platforms), extract one design move per category, and apply each as a
concrete rule addition to the corresponding walkthrough/directive file
in tokenmaxxxer/growth-analytics-rulebook: ga-trust's trust-gate-walker
(randomization-integrity step), ga-funnel's funnel-localizer (segment
and bottleneck steps), and ga-prereg's directive (sample-size step).

## Out of scope
Any change to a gate `.sh` script's enforcement logic, to
`growth-analytics.spec.json`'s required fields, or to any other role's
rulebook.

## Verification
Each target file diff is readable in the rulebook-repo PR; this record
cites the exact before/after rule text and the adoption evidence behind
each change.
