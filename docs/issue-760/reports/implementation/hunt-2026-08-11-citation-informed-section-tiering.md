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

## before-landing — stance 0: assume the gate/mechanism just implemented is bypassable — find the bypass

Verdict: FINDING — splitting the heading and the padded "None..." body across two separate Edit tool calls bypasses record-tiering-guard.sh entirely, even though the same content submitted as one fragment is correctly denied
Kind: composition
Seed: on-the-record/hooks/record-tiering-guard.sh, on-the-record/hooks/test_record_tiering_directive.py (diff: 299 lines across 6 files)
cap_seconds: 180
tier: size:>200-lines
diff_stat_lines: 299
started_at: 2026-08-11T07:18:25Z
ended_at: 2026-08-11T07:19:17Z

### Reproduce
```bash
GUARD=on-the-record/hooks/record-tiering-guard.sh

# Call 1: an Edit that inserts only the section heading (e.g. scaffolding
# the report skeleton before filling in the body separately).
printf '%s' '{"tool_name":"Edit","tool_input":{"file_path":"docs/issue-999/reports/implementation.md","old_string":"PLACEHOLDER_HEADING","new_string":"## What did not work\n"}}' \
  | ORCHESTRATE_OFF= bash "$GUARD"; echo "call1 exit: $?"

# Call 2: a later, separate Edit that inserts the padded "None..." body
# against a different anchor in the file. Its new_string never contains
# the heading text "## What did not work" at all.
printf '%s' '{"tool_name":"Edit","tool_input":{"file_path":"docs/issue-999/reports/implementation.md","old_string":"PLACEHOLDER_BODY","new_string":"None. Actually the citation extraction failed silently for large batches and we spent two days debugging before finding the root cause.\n"}}' \
  | ORCHESTRATE_OFF= bash "$GUARD"; echo "call2 exit: $?"

# Comparison: the identical final text, submitted as one fragment (as a
# Write), IS correctly denied by the same guard.
printf '%s' '{"tool_name":"Write","tool_input":{"file_path":"docs/issue-999/reports/implementation.md","content":"## What did not work\n\nNone. Actually the citation extraction failed silently for large batches and we spent two days debugging before finding the root cause.\n"}}' \
  | ORCHESTRATE_OFF= bash "$GUARD"; echo "call3 exit: $?"
```

### Observed
```
call1 exit: 0
call2 exit: 0
call3 exit: 2   (denied: "starts with \"None\" ... but is not the bare marker")
```
Both Edit calls exit 0 (silently pass). After both edits land on disk, the
file contains the exact heading-plus-padded-body pair the guard exists to
catch (`## What did not work` immediately followed by a "None..."-prefixed
body that is not the bare marker) — but the guard's PreToolUse invocation
never receives that combined text in a single content fragment, so it never
fires. The gate's own comment (lines 57-60 of record-tiering-guard.sh)
acknowledges the fragment-only view is a "write-time-approximation," but the
guard still no-ops (exit 0) rather than either flagging cross-call
uncertainty or deferring to a whole-file check — an author (or an agent
scaffolding the heading first and filling the body via a later edit, with no
adversarial intent) produces the exact denied-when-combined text on disk
while every individual gated call reports success.

### Expected
Either the gate should refuse to no-op when it cannot see the full section
(e.g. by reading the current on-disk file and merging the edit before
matching, the same way it would need to for MultiEdit's edits list to be
combined), or the guard's stated scope in the proposal/spec should
acknowledge that per-call fragment inspection provides no enforcement
against a body assembled across multiple Edit calls — a gap distinct from
the single-call MultiEdit fragment-joining it already implements at lines
68-73.

### Resolution

Fixed in `on-the-record/hooks/record-tiering-guard.sh`, same commit as this
hunt record: took the first option above. For `Edit`/`MultiEdit`, the guard
now reads the target file's current on-disk content and applies the same
edit(s) a real Edit/MultiEdit call would apply, then checks the section
extracted from that *reconstructed full content* instead of just the
changed fragment. Because `PreToolUse` fires before the tool executes, by
the time a second `Edit` call's hook runs, the first `Edit` has already
landed on disk, so reading current content at that point correctly picks up
state assembled across calls. Falls back to the prior fragment-only
behavior only when the file can't be read (new file, race, permissions) —
unchanged from before this fix for that one case.

Reproduced fixed behavior with a new regression test,
`test_record_tiering_directive.py::t_split_edit_heading_then_padded_body_is_still_denied`,
which performs the identical two-call split against a real on-disk file and
asserts the second call now exits 2 (a second test,
`t_edit_falls_back_to_fragment_when_file_unreadable`, covers the
file-can't-be-read fallback path still denying via the fragment):

```
$ python3 -m pytest -q on-the-record/hooks/test_record_tiering_directive.py
..............                                                           [100%]
14 passed in 0.43s
```
