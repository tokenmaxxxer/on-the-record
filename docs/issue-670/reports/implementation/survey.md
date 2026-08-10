---
subject: issue-670
---

# Current-state survey — issue-670

## Write surface

`on-the-record/hooks/directive.sh` renders the `[orchestrate]` directive
(UserPromptSubmit hook) that the orchestrator session reads every
prompt. It has no section today about `## Acceptance` field format when
drafting issues — the heredoc (lines 52-123) covers issue drafting
(bullet "Requirements become ISSUES..."), spawning, PR relaying, reply
structure, and turn-budget rules, but never Acceptance-clause shape.

## Format contract already enforced downstream

`gates/acceptance_gate.py` (issue-310, extended issue-416) checks an
issue's `## Acceptance` section post-hoc:
- `_ARTIFACT_REF` (line 21-25): requires either a backtick-wrapped
  `test/`/`gates/` path, or a `gate:`/`check:` line, or `unverifiable:`.
- `_EMPTY_STATE` (line 30-31) and `_PROVENANCE` (line 32-34): once an
  executable artifact is referenced, both regexes require `empty
  state:` and `provenance:` as their own `^...:` line
  (`re.MULTILINE`, anchored at line start) — an inline continuation on
  the same line as `check:` does not match either regex, so the
  orchestrator must always emit each of the three fields
  (`check:`/`empty state:`/`provenance:`) on its own line, never
  inline in one sentence.
- `provenance:` values are constrained to
  `executed-live|executed-unit|read` (line 33).

No file today states this contract at the point the orchestrator
drafts the Acceptance clause — the gate only fires after the issue is
already posted, causing rewrite/re-spawn round-trips (issue text cites
#649/#650/#651 as repeated instances). tokenmaxxxer-core#195 solved the
analogous problem for role-record format by embedding the shape in the
role directive itself (see `[implementation]`/`[core]` directive text
injected into this very session, which states record frontmatter/field
requirements up front).

## Precedent pattern in this same file

`directive.sh` already embeds format-contract knowledge inline for
other gates it anticipates (e.g. TURN-BUDGET RULES section cites
`#535`; the PR-relay bullet points to `/orchestrate:run step 6` rather
than restating it). Adding a short ACCEPTANCE FORMAT paragraph next to
the existing "Requirements become ISSUES..." bullet is consistent with
that style — short, imperative, referencing the gate as backstop.

## Alternatives visible from this survey

1. Edit only `directive.sh` (chosen candidate) — steers at the actual
   authoring point (the orchestrator session), matches the core#195
   precedent exactly.
2. Edit `/orchestrate:run` (the slash-command doc `directive.sh`
   already points to for PR-relay wording) instead/also — that command
   is read on-demand, not injected every prompt, so it would not fix
   the "sees it only after already having invented the wording"
   failure mode issue-670 describes (the heredoc bullet for spawning
   already relies on `/orchestrate:run` for *some* things, but the
   repeated-rejection pattern specifically implicates content missing
   from the always-injected heredoc, not the on-demand doc).
3. Strengthen `acceptance_gate.py` itself (e.g. auto-fix or friendlier
   error) — rejected by the issue text itself: the gate is explicitly
   kept as backstop; the ask is to prevent the round-trip by informing
   authorship, not to change the backstop's behavior.

## Unknowns / risk

- `directive.sh` is a heredoc feeding directly into the orchestrator's
  context; adding a section changes token cost of every prompt
  slightly — kept short per the issue's own ask ("짧은 ACCEPTANCE
  FORMAT 절").
- No test currently exercises `directive.sh` output content by
  string-matching (checked: no `test/` file greps its heredoc). The
  issue's own Acceptance clause specifies `check:` as capturing
  directive output and grepping for the format-rule string — this
  becomes the executable check, run manually (`bash
  on-the-record/hooks/directive.sh` with `CLAUDE_ROLE` unset, capture
  stdout, grep).

derived: `grep -rn "test/" -e "directive.sh"` search inconclusive by hand; confirmed via:
```
grep -rl "directive.sh" test/ 2>/dev/null
```
(no output — no existing test references this file, consistent with the issue's own acceptance clause proposing a manual capture/grep check rather than pointing at a pre-existing test.)
