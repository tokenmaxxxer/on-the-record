---
subject: issue-1199
role: legal-compliance
kind: scout-brief
loop_state: scouted
---

# Scout brief: legal-compliance tool landscape (issue-1199)

Mode: parallel WebSearch, one sweep round across four angles (consent-
management platforms, OSS license-compliance scanners, ad-tech consent
standards, vendor/DPA-risk platforms), followed by one targeted
deepening round (star/customer-count confirmation) on the two thinnest
hits.

## Tools surveyed, with adoption evidence

1. **Klaro** (`github.com/kiprotect/klaro`) — ~1.4k GitHub stars, ~290
   forks (fetched 2026-08-13, GitHub search result on the repo). MIT-
   licensed, self-hosted cookie/consent manager.
2. **REUSE tool + spec** (`fsfe/reuse-tool`, `reuse.software`) — 1,300+
   projects registered REUSE-compliant via its own API, adopted by the
   Linux kernel (2017), KDE (2020), Rust, curl, Nextcloud, Weblate
   (fetched 2026-08-13, fsfe.org news posts + api.reuse.software).
3. **ScanCode toolkit** (`github.com/nexB/scancode-toolkit`) — named
   as a leading free/open alternative to commercial scanners (FOSSA,
   Black Duck) in the AppSec Santa and Aikido license-scanner roundups
   (fetched 2026-08-13, appsecsanta.com and aikido.dev).
4. **IAB Europe TCF** (Transparency & Consent Framework) — Global
   Vendor List carries 5,000+ registered vendors; adopted by Google,
   Adobe, Criteo, The Trade Desk, OneTrust, and other major ad-tech/CMP
   platforms (fetched 2026-08-13, iabeurope.eu + jerisaliant.com).
5. **OneTrust** — vendor-stated 8,000+ customers including half of
   the Fortune 500; Vendor Risk Management module bundles DPA-clause
   tracking and retention-policy automation (fetched 2026-08-13,
   onetrust.com news + prnewswire.com).

## Problem / how / learning per tool

- **Klaro**: problem — a consent banner can be legally compliant in its
  visible copy while the tracker it is meant to gate already fired
  before the user acted, because the banner is UI state layered on top
  of scripts that load independently. How — Klaro's snippet
  intercepts and blocks the actual `<script>` execution/injection
  until its internal consent state flips, not just the banner's own
  visibility. Learning → the role's consent-ux review must check
  technical gating (does the tracker actually not fire pre-consent),
  not only banner copy/layout — folded into consent-ux.md rule 5.
- **REUSE / ScanCode**: problem — a repo's single top-level LICENSE
  file is silently wrong the moment any vendored third-party file,
  embedded font, or bundled asset under a different license enters the
  tree, and a manifest-only check (package.json's declared license
  field) misses code that was never declared at all. How — REUSE
  requires a machine-readable per-file SPDX tag instead of one
  repo-wide claim; ScanCode full-text-scans the actual shipped source
  rather than trusting declared metadata. Learning → the role's
  license-compatibility review must check bundled/vendored components
  individually, not assume the top-level license file is exhaustive —
  folded into license-compatibility.md rule 5.
- **IAB TCF**: problem — a controller's DPA with its direct vendor says
  nothing about whether the third, fourth, or fifth party several hops
  down an ad-tech resale chain is actually honoring the user's consent
  choice at the moment it processes data. How — TCF standardizes a
  machine-readable, per-vendor consent-status string that propagates
  with the data through the whole chain, checked at processing time,
  not just contracted in advance. Learning → the role's vendor-DPA
  review must, for multi-hop chains, require a verifiable per-vendor
  runtime signal in addition to the existing contractual flow-down
  clause — folded into vendor-dpa.md rule 5.
- **OneTrust**: problem — a written retention period is not itself
  evidence of compliance if nothing actually executes the deletion —
  "policy on paper, no automation" is the gap this vendor's own
  marketing explicitly targets. How — retention rules are attached to
  a scheduled automated-deletion workflow tied to data classification,
  not left as a text-only policy. Learning → the role's retention
  review must name the enforcement mechanism (scheduled job or a named
  manual owner+cadence) alongside the period itself — folded into
  retention-minimization.md rule 5.

## Adopt / skip
Adopt: the four design moves above, each restated as a native decision
rule sourced to the underlying legal provision (GDPR Recital 32, Art.
5(2), Art. 28(3)(a)), never citing the tool by name in the rulebook —
per this session's explicit no-attribution instruction.
Skip: installing or depending on any surveyed tool; a fifth "Tool
learnings" section in the public rulebook (explicitly out of scope
per this session's instruction, unlike the brand-design precedent).

## Segment fit
This role's phase-2 record is a text/rule-file deliverable (playbook
axis files), not a running consent banner or a live scan pipeline —
the fold-in targets rule wording in the existing playbook files rather
than new tooling, same posture as the brand-design unit's checklist-
wording fold-in.

## Field-vs-current-checklist gap
canonical: playbook/consent-ux.md, playbook/license-compatibility.md,
playbook/vendor-dpa.md, playbook/retention-minimization.md (all four,
read this session in the rulebook repo). None of the four files' rules
1-4 (as landed by issue #1174) asked for: technical gating verification
on consent (only visual/friction checks existed); per-component
license checking on bundled/vendored code (only whole-dependency
pairwise compatibility existed); a runtime per-vendor consent signal
for multi-hop chains (only contractual flow-down existed); a named
enforcement mechanism for retention periods (only the period-length
rule existed). The five new rule-5 entries close exactly these four
gaps (license-compatibility.md gets one new rule covering both REUSE
and ScanCode's shared design move).

## Sources
- https://github.com/kiprotect/klaro
- https://fsfe.org/news/2020 (KDE adoption; general fsfe.org/news/ REUSE posts, fetched 2026-08-13)
- https://api.reuse.software/info/github.com/fsfe/reuse-tool
- https://reuse.software/
- https://github.com/nexB/scancode-toolkit
- https://appsecsanta.com/sca-tools/open-source-license-compliance
- https://www.aikido.dev/blog/top-open-source-license-scanners
- https://iabeurope.eu/tcf/
- https://www.jerisaliant.com/blog/iab-tcf-v2-vendor-management
- https://www.onetrust.com/solutions/third-party-management/
- https://www.onetrust.com/news/onetrust-is-leading-the-market-outright/
- https://gdpr-info.eu/recitals/no-32/
- https://gdpr-info.eu/art-5-gdpr/
- https://gdpr-info.eu/art-28-gdpr/
- https://www.recordinglaw.com/world-laws/world-data-privacy-laws/eu-data-privacy-laws/gdpr-data-processing-agreement/
