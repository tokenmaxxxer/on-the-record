kind: report
subject: issue-1199
doc-type: reference

# devrel — current-state survey (phase-1, issue #1199)

## What was checked

canonical: git -C /tmp/devrel-rulebook-1199 log -1 --format=%H (fresh
clone of tokenmaxxxer/devrel-rulebook, this turn's tool transcript)

Cloned tokenmaxxxer/devrel-rulebook and read its full tree. It has no
separate playbook-style content directory: the role's operating
content lives in its handbook file (docs/handbooks/devrel-plugins.md
in that repo), which documents the 4 sibling methodology gates
(`phase-order`, `rfc-seven-section`, `diataxis-record`,
`metric-record`) that shape what a devrel proposal and record must
contain — `rfc-seven-section` requires an "Adoption-friction evidence"
proposal section, `diataxis-record` requires a `doc-type:`/`segment:`
pair plus an "Adoption-friction list" record header, and
`metric-record` requires `metric_name:`/`product_journey_stage:`/
`value:` record fields. None of these gates carry prose guidance on
*how* to fill those fields well — they only check field presence/shape.

## Gaps this fold-in targets

Every one of the 4 gates enforces structural presence (a header exists,
a field is non-empty, an enum value is one of four) but the handbook
gives no guidance on content quality: an "Adoption-friction evidence"
section can cite friction with no traceable source; an
"Adoption-friction list" entry can merge two distinct failure points
into one bucket; a `product_journey_stage:` value can default to
`adoption` regardless of what the metric actually measures; a
`doc-type:`/`segment:` pair can go undated relative to the product
surface it documents. This is the gap issue #1199 asks this unit to
close: fold tool-encoded design moves (from the practitioner tools
devrel's own domain — API docs, SDK generation, OpenAPI reference
rendering, developer-community analytics — most relies on) into that
handbook as prose guidance that upgrades how authors fill those same
existing fields, without touching gate code.

## kind / loop_state

kind: report
loop_state: phase-1-scouted
