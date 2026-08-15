---
subject: issue-1199
role: legal-compliance
kind: scout-brief
loop_state: scouted
---

# Scout brief: legal-compliance Claude Code plugin rework (issue-1199, 2026-08-14 amendment)

Mode: parallel WebSearch, one sweep round across four angles (Claude
Code marketplace legal/GDPR/privacy skills; contract-review/license
skill repos; plugin-marketplace directories; compliance/GDPR-tagged
skill repos by star count), followed by one targeted deepening round
(WebFetch star/fork/benchmark confirmation) on the three thinnest-but-
most-cited hits. canonical: WebSearch results and WebFetch of
github.com/Sushegaad/Claude-Skills-Governance-Risk-and-Compliance,
github.com/evolsb/claude-legal-skill, and
github.com/mukul975/privacy-data-protection-skills (all run this
session).

Reason for this rework: the 2026-08-13 survey (docs/issue-1199/reports/
legal-compliance/scout-brief.md) surveyed general legal-compliance
domain tools (Klaro, REUSE, ScanCode, IAB TCF, OneTrust) — none of
which is a Claude Code plugin/skill. The 2026-08-14 issue-1199
amendment narrows the survey target to the Claude Code plugin/skill
ecosystem specifically; the prior survey fails the amended acceptance
check on that basis alone (survey basis, not survey quality). canonical:
the issue-1199 tool-landscape REWORK amendment text delivered in this
session's invocation prompt (2026-08-14 amendment paragraph, read this
session).

## Tools surveyed, with adoption evidence

1. **Claude Skills for Governance, Risk & Compliance**
   (`github.com/Sushegaad/Claude-Skills-Governance-Risk-and-Compliance`)
   — 826 GitHub stars, 170 forks (canonical: WebFetch of that URL, this
   session); the repo's own README states a 150-test-case/752-assertion
   comparison of 94% correct with its skills loaded against 81% without
   (canonical: same WebFetch, this session — a vendor-stated figure
   from the repo's own README, not independently re-run by this
   session).
2. **Claude Legal Skill** (`github.com/evolsb/claude-legal-skill`) —
   408 GitHub stars (canonical: WebFetch of that URL, this session);
   built on the CUAD dataset's 41 legal-risk categories drawn from 510
   real contracts; compatible with Claude Code, Cursor, GitHub Copilot,
   and 26+ tools via the open Agent Skills standard.
3. **Privacy & Data Protection Skills**
   (`github.com/mukul975/privacy-data-protection-skills`) — 223 GitHub
   stars, 52 forks (canonical: WebFetch of that URL, this session);
   282+ structured privacy procedures (GDPR, CCPA, EU AI Act, HIPAA,
   LGPD, PIPL, DPDP Act), each with a `references/` folder of
   regulatory citations.

Other hits surfaced but not deepened (sweep only): mcpmarket.com's
GDPR-Compliance / Legal-Advisor / Compliance-Review skill listings (no
star/adoption figure surfaced on the listing pages themselves);
alirezarezvani/claude-skills (345-skill multi-domain collection,
GDPR/DSGVO-expert sub-skill; adoption figure not independently
distinguishable from the parent repo's aggregate count); Anthropic's
own `claude-for-legal` plugin suite (official-org provenance is itself
adoption-relevant, but no star/usage figure surfaced this round) —
noted as a gap, not folded in. canonical: WebSearch result titles and
snippets for these four (this session, sweep round).

## Problem / how / learning per tool

- **Sushegaad GRC skills**: problem — a compliance review that names
  one regime ("GDPR-compliant") gives no signal on whether an
  overlapping regime was checked or just not contradicted. How — each
  skill states an explicit cross-framework mapping (e.g. ISO 27001
  control → NIST CSF control) instead of one collapsed verdict.
  Learning → vendor-dpa reviews spanning more than one regime must name
  each regime checked explicitly.
- **evolsb claude-legal-skill**: problem — a binary compliant/
  non-compliant flag collapses low-stakes and high-stakes findings into
  one signal, blocking urgency triage. How — every flagged risk carries
  a severity rating (Critical/Important/Acceptable) plus a
  market-benchmark comparison. Learning → license-compatibility
  findings must carry a per-finding severity rating, distinct from any
  single repo-wide verdict.
- **mukul975 privacy-data-protection-skills**: problem — a rule citing
  a regulation by name only ("per GDPR") is not independently checkable
  against source text. How — every skill's action traces to a specific
  cited provision in its own reference material. Learning →
  retention-minimization's enforcement-mechanism citation must name the
  specific article/section, not the regulation alone.

## Adopt / skip
Adopt: the three design moves above, folded into a new
tool-learnings.md file under docs/handbooks/legal-compliance/ in the
separate rulebook repo (tokenmaxxxer/legal-compliance-rulebook,
mounted at
/home/jwjung/tokenmaxxxer/rulebooks/legal-compliance-rulebook — this
path is not inside this working tree), each entry naming the existing
playbook rule-5 it upgrades (vendor-dpa.md, license-compatibility.md,
retention-minimization.md). canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/legal-compliance-rulebook show
7579074 --stat` (executed this session).
Skip: installing or depending on any surveyed skill/plugin; a
deepening round on the four unfetched hits noted above. canonical:
WebSearch results for the four unfetched hits (this session, sweep
round, "Other hits surfaced but not deepened" paragraph above) — the
saturation judge point found the three fetched hits already cover the
three relevant axes with no open decision the fourth angle would
change.

## Segment fit
Same posture as the 2026-08-13 unit and the brand-design precedent:
this role's phase-2 deliverable is a text/rule-file fold-in, not a
runnable skill install — the survey targets design-move learnings, not
adoption of the surveyed plugins themselves.

## Field-vs-current-checklist gap
canonical: playbook/vendor-dpa.md, playbook/license-compatibility.md,
playbook/retention-minimization.md rule 5 (all three, as landed by the
2026-08-13 unit, read this session in the rulebook repo). None of the
existing rule-5 entries required: naming each regulatory regime
explicitly when a review spans more than one; a per-finding severity
rating distinct from a repo-wide verdict; or a specific article/section
citation (as opposed to a bare regulation name) for the stated
enforcement mechanism. The three tool-learnings entries close exactly
these three gaps.

## Sources
- https://github.com/Sushegaad/Claude-Skills-Governance-Risk-and-Compliance
- https://sushegaad.github.io/Claude-Skills-Governance-Risk-and-Compliance/
- https://github.com/evolsb/claude-legal-skill
- https://github.com/evolsb/claude-legal-skill/blob/main/skill.md
- https://github.com/mukul975/privacy-data-protection-skills
- https://mcpmarket.com/tools/skills/gdpr-compliance-expert
- https://github.com/alirezarezvani/claude-skills
- https://github.com/anthropics/claude-for-legal
- https://github.com/anthropics/claude-plugins-official
