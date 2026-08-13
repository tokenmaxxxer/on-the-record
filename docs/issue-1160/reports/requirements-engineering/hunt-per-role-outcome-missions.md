---
proposal: docs/issue-1160/proposals/per-role-outcome-missions.md
---

# Hunt record — per-role-outcome-missions

## after-proposal — stance 0: assume "reuse #1156's anti-circularity, don't reinvent" or the write-set freeze is bypassable or hollow

Verdict: FINDING — the proposal claims to name which role records the bar verdict for each pilot role's mission_deliverable but never actually does, leaving the mission deliverable ungraded by construction
Kind: design-error
Seed: docs/issue-1160/proposals/per-role-outcome-missions.md (new file)
cap_seconds: 60
tier: default
diff_stat_lines: ~200 (new file, docs-only)
started_at: 2026-08-13T00:00:00Z
ended_at: 2026-08-13T00:01:00Z

### Reproduce
grep -n "verdict\|verifier\|records\|checked by\|checks it against" docs/issue-1160/proposals/per-role-outcome-missions.md

### Observed
Line 68-74 states: "Bar verdicts on mission deliverables reuse #1156's
anti-circularity design ... This proposal does not redesign that
mechanism; it only names which role records the verdict for each pilot
role's mission deliverable (§3 below)." But §3 is titled "content-design"
and, like §2 (brand-design) and §4 (market-analysis), only ever says
"a different role checks it against [fit_criterion]" (line 103-104) —
it never names *which* role that is, for any of the three pilots. No
section in the document assigns a verifying/recording role to any
pilot role's mission_deliverables. The forward reference "(§3 below)"
points at a section that does not contain the promised content.

### Expected
Either §2/§3/§4 (or a dedicated §3-equivalent) should explicitly name,
per pilot role, which existing role's spec is the author-identity that
records the #1156-style bar verdict on that mission_deliverable (e.g.
"brand-design's token-consumption deliverable is verified by
ux-engineering, per anti-circularity producer/author check"). Without
that wiring, the anti-circularity mechanism has nothing to attach to —
mission_deliverables are declared but no role is on record as the
verifier, so a BAR_MET/BAR_NOT_MET verdict can never actually be
produced for them; the deliverable stays permanently ungraded while
looking like it is covered by "reuse #1156's mechanism."

### Resolution

Fixed in the same proposal, same session: the brand-design,
content-design, and market-analysis sections each now carry a
"Verified by:" line naming the specific role that records the
producer-differs-from-author bar verdict for that pilot role's
mission_deliverables (brand-design -> ux-engineering; content-design
and market-analysis -> requirements-engineering), and the "Constraints
stated so far" bullet on anti-circularity now points at those lines
instead of a forward reference that pointed at a section without the
promised content.
canonical: docs/issue-1160/proposals/per-role-outcome-missions.md
"Verified by:" lines, read this turn
