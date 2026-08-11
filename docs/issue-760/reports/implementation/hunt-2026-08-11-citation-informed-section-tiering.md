---
proposal: docs/issue-760/proposals/2026-08-11-citation-informed-section-tiering.md
---

# Hunt record — citation-informed-section-tiering

## after-proposal — stance 0: assume the gate/mechanism just proposed is bypassable — find the bypass

Verdict: FINDING — the directive-only mechanism this proposal is about to duplicate has already demonstrably failed, unenforced, for this exact section, and the proposal's own survey sample contains the proof without drawing the conclusion.
Kind: silent-failure
Seed: docs/issue-760/proposals/2026-08-11-citation-informed-section-tiering.md, docs/issue-760/reports/implementation/survey.md, on-the-record/hooks/record-claim-shape-directive.sh, on-the-record/hooks/record-claim-guard.sh, plus (found by following the survey's own citation) runs/rulebooks/tokenmaxxxer-implementation/record-shape/hooks/directive.sh and record-shape-gate.sh
cap_seconds: 60
tier: default
diff_stat_lines: n/a (new untracked proposal+survey docs, no diff)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:10:00Z

### Reproduce

```
grep -n -A2 "^## What did not work" docs/issue-759/reports/implementation.md docs/issue-674/reports/implementation.md
grep -n "explicit content such as" runs/rulebooks/tokenmaxxxer-implementation/record-shape/hooks/directive.sh
grep -n "has_wdnw\|missing.append" runs/rulebooks/tokenmaxxxer-implementation/record-shape/hooks/record-shape-gate.sh
```

### Observed

`runs/rulebooks/tokenmaxxxer-implementation/record-shape/hooks/directive.sh` (the
already-existing, already-injected `UserPromptSubmit` directive from the
separate `implementation-rulebook` plugin — the very one this proposal's own
survey cites as covering this section) already states, verbatim, line 38:

    Criterion: "present even when empty" means the heading exists with
    explicit content such as "None." — not an omitted heading.

That is directive-only guidance for the identical norm phase-2's new
`record-tiering-directive.sh` is proposed to add a second time. Its paired
gate, `record-shape-gate.sh`, only checks `has_wdnw` — heading presence via
`^##\s+What did not work\s*$` — and never inspects body content; a
non-"None." body cannot fail this gate (confirmed by reading the full
`missing.append(...)` list in the gate source: five frontmatter-key checks,
heading-presence, and the conditional deviation-heading check — no content
check exists for this section anywhere in the gate).

Consequently the existing directive's "None." guidance is already being
silently ignored in live records, right now, with zero mechanical
consequence: `docs/issue-759/reports/implementation.md` and
`docs/issue-674/reports/implementation.md` (both inside the proposal's own
survey's 20-record sample, both explicitly flagged in the survey's "Sample
of what 'empty' currently looks like — not uniformly terse" section) carry
146- and 180-char explanatory paragraphs instead of the directive-stated
"None." example, and nothing in the toolchain flagged, blocked, or recorded
this deviation.

### Expected

The proposal's Rationale argues a directive-only mechanism is safe here
because #195 and #730 (its cited precedents) each pair their directive with
an *existing, unchanged, already-effective* mechanical gate — the directive
only closes an authoring-time information gap, the gate remains the real
backstop. But for this exact section, the only "gate" is presence-only
(`record-shape-gate.sh`), and a directive already exists that states the
"None." norm and is already not followed by real sessions with no
consequence — this is not a hypothetical failure mode, it already happened
inside the proposal's own baseline sample. The proposal should have treated
this as direct evidence that stacking a second, near-identical
directive-only layer on the same section is unlikely to change author
behavior any more than the first one already installed did, and that the
20-record re-measurement window (the only backstop left) has no owner or
trigger named anywhere in the proposal's "How you'll know it worked"
section — so a second silent-ignore cycle would again surface only "weeks
later," if a human remembers to run the re-measurement at all.

### Resolution

Both points addressed directly in
`docs/issue-760/proposals/2026-08-11-citation-informed-section-tiering.md`'s
Rationale/What-will-be-done, same commit as this hunt record: (1) the
chosen mechanism is now a directive **paired with** a new narrowly-scoped
`record-tiering-guard.sh` gate — fires only on a body that self-declares
"none" and is not the bare marker, never touches real content regardless
of length, so it adds real mechanical consequence without reproducing the
rejected blanket-length-cap failure mode; (2) the proposal's phase-2 record
now names an explicit re-measurement owner/trigger (the next
`product-discovery` round touching `#745`, or a follow-up issue against
`#760`, once 20 post-tiering records exist) instead of leaving the 20-record
window ownerless.
