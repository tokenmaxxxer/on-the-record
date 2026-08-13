---
proposal: docs/issue-1165/proposals/2026-08-13-technical-writing-human-comprehensibility.md
---

# Hunt record — technical-writing-human-comprehensibility

## after-proposal — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — tier-1 rule `lead_with_the_point` is declared purely-automatable ("automated structural scan ... no LLM judgment call") but its predicate ("states what the doc covers/what changed, why it matters, and what the reader does next") is a semantic judgment no regex/markdown-AST scan can perform, contradicting #1156's own decomposition principle 3 that non-automatable criteria must be a named human-review checklist item, not an automated proxy.
Kind: design-error
Seed: docs/issue-1165/proposals/2026-08-13-technical-writing-human-comprehensibility.md (new, untracked), § "1. Tier 1 — automatable structure rules (document side)", rule 1 and the `verification_method` line immediately after the four rules.
cap_seconds: 180
tier: size:200+
diff_stat_lines: 3 new files (proposal + 2 reports)
started_at: 2026-08-13T00:00:00Z
ended_at: 2026-08-13T00:03:00Z

### Reproduce

```
grep -n "no LLM judgment call" docs/issue-1165/proposals/2026-08-13-technical-writing-human-comprehensibility.md
```
→ line 73-75: "`verification_method` for all four: automated structural
scan (regex/markdown-AST over the prose body) — no LLM judgment call,
per #1156's automatable-tier bar."

Compare against rule 1 (lines 52-56):
"**lead_with_the_point** — the first paragraph of the prose body
states what the doc covers/what changed, why it matters, and what
the reader does next (what/why/so-what), before step-by-step detail,
background, or raw context."

Compare against the cited "#1156's automatable-tier bar" itself:

```
sed -n '108,121p' docs/issue-1156/proposals/per-role-quality-bars.md
```
→ principle 3: "Non-automatable → named human-review checklist, never
a lowered bar ... where a domain's bar criterion cannot be automated
(e.g. positioning quality, negotiation soundness, content voice), the
checkable form is a named checklist item requiring a human verdict
... the criterion is never dropped or replaced with an easier
automatable proxy."

### Observed

The proposal asserts a purely mechanical (regex/AST) verification
method can determine whether a paragraph "states what/why/so-what" —
i.e. whether the paragraph's *meaning* covers a change, its rationale,
and a next action. No regex or AST structural scan can determine
semantic content ("why it matters", "what the reader does next" as
distinct from mere presence of a paragraph). Nothing in phase 2's plan
(§ "Plan for phase 2" item 1: "gate fixture tests ... a passing
lead-summary+bounded-section fixture, a failing raw-dump fixture")
proposes any mechanism capable of judging semantic content either —
the fixtures described (bounded-section, raw-dump) match rules
2-4 (structural), not rule 1 (semantic).

### Expected

Per #1156 principle 3 (which the proposal itself cites as governing
"automatable-tier bar"), `lead_with_the_point` should either be
demoted to tier-2 (a human-review checklist item — it closely
resembles tier-2's own `what-changed`/`why`/`what-next` items, which
*are* correctly given `verification_method: human-review-checklist`
equivalent), or the proposal should specify a concrete automatable
proxy and justify why it is not "an easier automatable proxy"
replacing a criterion that cannot really be automated. As written,
phase 2 has no state/mechanism that keeps the tier-1 "no LLM judgment
call" claim true for rule 1 specifically — the gap is invisible until
someone tries to implement the regex/AST check and discovers it
cannot determine "why it matters."
