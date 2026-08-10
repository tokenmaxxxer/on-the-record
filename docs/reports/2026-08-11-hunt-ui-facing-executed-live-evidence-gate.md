
## after-proposal — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — the proposal's "explicit opt-out" is prose with no defined token/syntax, so it cannot be mechanically distinguished from the "declares no globs → fail-closed fallback" case it is supposed to be exempt from
Kind: design-error
Seed: docs/issue-685/proposals/2026-08-11-ui-facing-executed-live-evidence-gate.md
cap_seconds: 120
tier: default
diff_stat_lines: ~250 across 2 new files (docs-only, no code yet)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:10:00Z

### Reproduce
Read the proposal's "What will be done" §1 and Rationale's closing paragraph:

```
grep -n "none\|opt.out" docs/issue-685/proposals/2026-08-11-ui-facing-executed-live-evidence-gate.md
```
gives only:
```
76:   line), plus the fail-closed fallback list and the opt-out convention
77:   (present file, explicit "none" line) for repos with no UI surface at
```
No other location in the proposal specifies what string, heading, or
placement constitutes the "none" line, nor how `is_ui_facing`'s parser is
meant to tell it apart from an empty/absent `## Globs` section. `ls
gates/ui_evidence_gate.py docs/specs/ui-surfaces.md` confirms neither
exists yet — this is a pure design gap, not an implementation bug.

### Observed
The design defines exactly two parseable states (file absent; file
present with a non-empty `## Globs` list) but three semantically distinct
outcomes are required: (a) absent → fallback fires, (b) present with
globs → use them, (c) present, explicitly declaring no UI surface at
all → skip entirely, exempt from fallback. Outcome (c) is given only the
unparseable description "explicit 'none' line," with no defined literal,
so a target-repo author writing `## Globs` with an empty list, or `##
Globs\n(none)`, or omitting the `## Globs` heading, cannot know — and the
gate as specified cannot determine — whether that counts as (b)-empty
(which triggers the fail-closed fallback per the Rationale) or (c)
opt-out (which suppresses it). The two outcomes are the entire point of
distinguishing "absent" from "present-but-empty" per the Rationale's own
sentence ("A declared-but-empty glob list ... is the one way to opt fully
out — distinguishable from 'file absent' by the file's own presence") —
but that sentence conflates "declared-but-empty" (fallback case, per
"What will be done" bullet 1) with "opt fully out" (exempt case), which
are stated as the same condition and also as opposite outcomes.

### Expected
The proposal should define a literal, parseable opt-out marker (e.g. a
required exact line `## Globs\nnone` or a distinct heading) and resolve
the direct contradiction between "declares no globs → fallback list
applies" (What will be done, §1 fallback rule) and "declared-but-empty
glob list ... is the one way to opt fully out" (Rationale) before any
code is written, since as written the two sentences describe the same
file state (`## Globs` heading present, zero glob lines under it) and
assign it two incompatible outcomes.
