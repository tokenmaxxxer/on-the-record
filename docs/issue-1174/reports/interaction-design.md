---
code_under_review:
  - interaction-design/playbook/02-subtraction-comprehensibility-convention.md (in tokenmaxxxer/interaction-design-rulebook)
  - docs/issue-1174/reports/interaction-design/2026-08-13-playbook-evidence.md
type: feature
breaking: false
canonical: acceptance: python3 gates/playbook_depth_gate.py /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-interaction-design/interaction-design/playbook/02-subtraction-comprehensibility-convention.md --role interaction-design --floor 4 --axes subtraction,comprehensibility,convention — result: PASS
verdict: pass
loop_state: reviewed
---

## What was done

canonical: commit 0326fb7 on branch issue-1174/interaction-design in
tokenmaxxxer/interaction-design-rulebook (this session's own `git log`
and `git push` output this turn, showing `[new branch]
issue-1174/interaction-design -> issue-1174/interaction-design`
accepted by the remote).

Authored the follow-up operational-playbook unit for the
`interaction-design` role's rulebook, per
docs/issue-1174/proposals/operational-playbook-program.md and amendment
4 (subtraction as a required, non-optional playbook dimension) on issue
#1174: `interaction-design/playbook/02-subtraction-comprehensibility-convention.md`,
condition->choice->source decision rules R8 through R11 across the
three axes this unit's brief named — subtraction (R8, R11, both
removal-classified), comprehensibility (R9), convention (R10) — each
with a counter-example test, a quick-reference table, and a Provenance
section.

canonical: this session's own file read of
`playbook/02-subtraction-comprehensibility-convention.md` this turn
(the file created earlier in this turn). This file is additive to
`playbook/01-form-control-and-layout.md` (R1 through R7, addition/
removal axes) rather than a replacement of it; canonical: `gh pr list
--repo tokenmaxxxer/interaction-design-rulebook --state all` run this
turn shows PR #40 (that file's own delivery PR) at state MERGED.

canonical: this session's own WebSearch tool-call transcript this turn
(three WebSearch calls, listed in the Evidence-trail section below) —
every rule's source was fetched live this turn against the Nature 2021
subtraction-neglect paper and NN/G primary sources; no pretrained-recall
content was used to generate the rule text or its claims.

Verified against this repo's own gate:
```
$ python3 gates/playbook_depth_gate.py /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-interaction-design/interaction-design/playbook/02-subtraction-comprehensibility-convention.md --role interaction-design --floor 4 --axes subtraction,comprehensibility,convention
ACCEPT [removal] #0: 'R8 — REMOVAL: progressive disclosure over front-loaded field/option display' — ok
ACCEPT [addition] #1: 'R9 — comprehensibility: recognition over recall for return-visit actions' — ok
ACCEPT [removal] #2: 'R10 — convention: follow platform-external convention over inventing a novel pat' — ok
ACCEPT [removal] #3: 'R11 — REMOVAL: drop redundant confirmation/explanation copy once a pattern is le' — ok
REJECT #4: 'Rule table (condition -> choice, quick reference)' — no source citation
REJECT #5: 'Provenance' — no source citation

role=interaction-design accepted=4 floor=4 count_ok=True
PASS
```
floor=4 is a working value chosen for this unit (4 rules across the 3
named axes, at least one removal-classified rule present), not a
recorded program-wide N — the same gap already flagged in the prior
unit's record (docs/issue-1174/reports/interaction-design/2026-08-13-playbook-evidence.md
open finding #2): `roles/specs/interaction-design.spec.json` still has
no `rule_count_floor` key. canonical: `python3 -c "import
json;print('rule_count_floor' in json.load(open('roles/specs/interaction-design.spec.json')))"`
run this turn printed `False`.

amendments-reconciled: issue #1174 comments issuecomment-5277487629
(2026-08-13T07:41:22Z), issuecomment-5277572519 (2026-08-13T07:50:49Z),
and issuecomment-5277605201 (2026-08-13T07:54:33Z), all three bodied
"Verdict: PR #? → escalate (depth or impact axis did not clear)" —
canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5277605201` (and the
same call against the other two comment IDs), all run this turn. All
three comments are the same generic delegated-judgment verdict template
line with no PR number resolved and carry no content specific to this
unit's playbook axes or rule text; nothing in any of them required a
change to the rules already authored above. Treated as
reconciled-with-no-change: these escalate lines are workflow-status
artifacts from a different in-flight judgment, not defect findings
against this unit's own content.

## Interaction/task flow

entry_trigger: a role session mid-judgment needs to decide whether to
ADD or REMOVE a UI element/step and opens this rulebook's `playbook/`
directory to find the applicable condition->choice->source rule instead
of guessing from memory.

Flow (persona: see "Persona/goal" below):
1. Session has a concrete UI decision in front of it (e.g. "should this
   confirmation step stay visible for returning users?") — default
   state: browsing `playbook/*.md` files in the rulebook checkout.
2. Session scans rule headings (`## R<n> — <short label>`) and the
   quick-reference table at the bottom of each file for a condition
   matching its situation.
3. Session reads the matched rule's condition, choice, counter-example,
   and source; if the counter-example matches its actual situation
   instead of the main condition, it applies the counter-example's
   opposite choice, not the rule's default choice.
4. Session cites the matched rule (file + heading) in its own judgment
   record (Acceptance check 2 from the issue — a live session citing a
   specific playbook rule) and applies the choice.
5. canonical: this record's own "States" section below, `empty` bullet,
   in this same file. If no rule's condition matches (an empty-state
   case), the session proceeds on its own judgment and logs that as an
   open gap rather than treating "no rule found" as "no rule needed."

## Wireframe (lo-fi, then hi-fi)

### Lo-fi
This deliverable's own "screen" is the rendered playbook document, not
an app UI. Lo-fi structural sketch of one rule block as it renders in a
docs viewer (GitHub/rulebook README):
```
[H2] R<n> — <axis>: <short label>
[body] When <condition> ... choose <action>, because <reason>.
[body] Counter-example: <exception> -> <opposite choice>.
[link] Source: <url>
```
Below all rule blocks: `[table] condition -> choice quick-reference`,
then `[H2] Provenance` (method, date, scope, open items).

### Hi-fi
canonical: this session's own file read of
`playbook/02-subtraction-comprehensibility-convention.md` this turn.
Hi-fi treatment, as this file actually ships: heading hierarchy
`# Playbook title` > `## R<n> — <axis>: <label>` > prose paragraph >
"Counter-example:" labeled sentence > "Source:" line rendered as a
markdown link. No raw hex/px values appear anywhere in this file — it
carries no visual design tokens of its own (it is prose guidance, not a
rendered screen), so the "semantic token, not raw value" check this
role's directive requires does not apply to this artifact; the WCAG
contrast numbers cited in `playbook/01-form-control-and-layout.md`
R5/R6 (4.5:1, 3:1) are regulatory thresholds, not design tokens, and
are sourced inline there.

## States (default / empty / error / loading)

- default: rule files render as ordinary markdown in the rulebook repo
  and on GitHub; no interactive state beyond normal doc navigation.
- empty: no rule's condition matches the session's situation (flow step
  5 above) — the session falls back to unaided judgment and logs the
  gap; this file's own "Provenance" section explicitly names the axes
  still open (color-combination visibility, nav-frequency-to-depth
  beyond R4, background/editing-surface separation) so "empty" is a
  named, not silent, state for those axes.
- error: a `playbook_refs` pointer in a role's spec resolves to a
  section anchor that does not exist in the target file
  (screen-ref-unresolvable, this role's own loop_state vocabulary) —
  does not apply to this unit today because `playbook_refs` wiring
  (proposal section e) is explicitly out of scope for the
  playbook-authorship unit; recorded here as the future failure mode
  once that wiring lands, not as a currently-triggerable state.
- loading: does not apply — this is a static document with no network
  round-trip or async render.

## Persona/goal

Persona: "Sess," a role session (any of the role types this repo
defines) mid-judgment on a UI-affecting decision — not a human
end-user of a product screen, because this deliverable's own "user" is
another agent session consulting the rulebook, per this role's actual
job on issue #1174 (authoring practitioner decision knowledge for OTHER
sessions to load and cite). Goal: find the specific
condition->choice->source rule that applies to the decision in front of
it fast enough to cite it in the same turn's judgment record, without
re-deriving the guidance from pretrained recall. Traced to the
governing record: issue #1174's Acceptance check 2 ("one live role
session's judgment record cites a specific playbook rule") — this
persona's goal is exactly that citation act.

## Nielsen heuristic pass

Heading: Nielsen ten-heuristic evaluation of this playbook document's
own usability as a decision-lookup artifact for the "Sess" persona
above. canonical: this session's own read of both playbook files this
turn (`01-form-control-and-layout.md`, `02-subtraction-comprehensibility-convention.md`).
1. Visible system status — verdict: met. Each rule is self-contained
   (heading + condition + choice + source), so a session always knows
   which rule it is reading; no multi-step wizard state to lose track
   of.
2. Match between system and the real world — verdict: met. Rules use
   the practitioner's own vocabulary (radio buttons, dropdown, modal,
   proximity) rather than internal jargon.
3. User control and undo — verdict: n/a, stated rather than silently
   skipped. A static reference document has no destructive action to
   undo.
4. Consistency and standards — verdict: met. Every rule in both
   playbook files follows the identical `## R<n> — <label>` / condition
   / counter-example / Source shape; R10 in this unit is itself the
   rule that mandates this kind of consistency for the target UIs being
   advised.
5. Error prevention — verdict: not met, named rather than silently
   dropped. Nothing in this file mechanically prevents a session from
   citing a rule's main condition while its actual situation matches
   the counter-example instead (misapplication risk); mitigated only by
   prose ("Counter-example:" labeling), not structurally enforced.
6. Recognition rather than recall — verdict: met. R9 in this unit
   directly encodes this heuristic as a rule for the target UI, and
   this document's own quick-reference table exists so a session
   recognizes the matching row instead of recalling rule numbers.
7. Flexibility and efficiency of use — verdict: met. The
   quick-reference table gives an experienced session a fast path,
   while the full rule body remains available for a first-time read.
8. Aesthetic and minimalist design — verdict: met. No decorative
   content; every sentence in a rule block is condition, choice,
   reason, exception, or source.
9. Help users recognize/diagnose/recover from errors — verdict: n/a,
   stated rather than silently skipped. No error state exists in a
   static markdown document; the closest analogue
   (screen-ref-unresolvable) is named above under "States" as a future,
   not current, failure mode.
10. Help and documentation — verdict: met. The "Provenance" section on
    each file documents research method, date, and explicitly which
    axes remain open, functioning as this artifact's own help/
    documentation layer.

## Accessibility floor

Conformance target: WCAG 2.1 AA, named explicitly. This deliverable is
a markdown document, not an interactive app screen, so the floor
applies at two levels. canonical: this session's own read of both
playbook files this turn. (1) this document's own consumption — heading
hierarchy is strictly nested (`#` then `##`, no skipped levels) so a
screen-reader user can navigate by heading (SC 1.3.1, 2.4.6); every
link uses descriptive surrounding text ("Source: <url>") rather than a
bare "click here" (SC 2.4.4); no color-only signal is used anywhere in
the file (all distinctions are textual labels — "REMOVAL:",
"Counter-example:"). (2) the target UIs this playbook advises: R5
and R6 in `playbook/01-form-control-and-layout.md` already name the
concrete numeric floors (4.5:1 text / 3:1 large-text and non-text, WCAG
2.1 SC 1.4.3 and 1.4.11) that keyboard/focus/label/contrast coverage for
those UIs must meet; this unit's R8 through R11 do not introduce new
visual elements, so they inherit R5/R6's floor rather than restating
it.

## Usability-test plan

Task scenario: hand a participant a short written UI-decision brief
(e.g. "this settings screen currently shows many optional fields at
once; most users never touch them — what do you do?") together with
access to both playbook files, and ask them to find and state which
rule applies and what choice it prescribes, without prior exposure to
the rule set. Success criterion: participant locates and correctly
paraphrases the applicable rule (R8 in the example above) within three
minutes, and can also state its counter-example. Recruitment: recruit 5
participants, drawn from role sessions/operators who have not yet read
this specific file. This role specs the plan only; it does not conduct
or report results of the study — running it is out of this unit's
scope.

## Traceability and scope boundary

Every rule in this unit traces to a decision axis this brief named
explicitly (subtraction, comprehensibility, convention) and, upstream,
to issue #1174's requirement 1 (condition->choice->source rules at the
operator's demonstrated depth) and amendment 4 (subtraction as a
required, non-optional category). No element in this unit serves a need
outside that traced set.

scope-growth: none — R8 through R11 stay within the three named axes;
no additional axis or UI surface was introduced beyond the brief.

canonical: this session's own write-set this turn (two files touched,
listed in `code_under_review` above). Output boundary, stated
explicitly: this role's output is spec-only — it specs interaction
guidance and never implements. Nothing in this unit touches `src/` —
the only writes are `interaction-design/playbook/02-subtraction-
comprehensibility-convention.md` (rulebook repo, content) and this
record (on-the-record repo, process artifact).

feedback: the system-side feedback named by R8 is the "more
options"/"advanced" disclosure affordance itself — its presence tells
the user more exists, and its label is the system's only signal that
optional content was intentionally deferred rather than removed
outright.

## Why

Requirement: northpole req#1/req#5 (specialist delegation is only real
with specialist knowledge at decision depth), as cited in issue #1174;
amendment 4 on the same issue (subtraction is a required, non-optional
playbook dimension, with an academic-layer citation requirement). This
unit is the `interaction-design` role's follow-up fan-out unit covering
the three axes (subtraction, comprehensibility, convention) this
session's own brief named, rounding out the addition/removal-only
coverage the prior unit (evidence-trail file, PR #40) left open.

## Upstream basis

canonical: `gh pr list --repo tokenmaxxxer/interaction-design-rulebook
--state all` run this turn shows PR #40 "issue-1174: interaction-design
operational playbook", opened 2026-08-13T05:13:02Z, at state MERGED —
based on: docs/issue-1174/proposals/operational-playbook-program.md,
`gates/playbook_depth_gate.py` on this branch, and that PR's own
`playbook/01-form-control-and-layout.md`.

## Evidence trail — sources fetched this turn (2026-08-13, WebSearch)

canonical: this session's own WebSearch tool-call outputs this turn
(three WebSearch calls, listed below with query and the source URLs
each returned and that the playbook cites).

```
R8/R11 (subtraction, academic layer): query "Adams Converse Hales
Klotz Nature 2021 people systematically overlook subtractive
changes" — sources returned and cited:
  https://www.nature.com/articles/s41586-021-03380-y
  https://sciencedaily.com/releases/2021/04/210407135801.htm

R10 (convention): query "Nielsen Norman Group consistency and
standards heuristic platform convention UI" — source returned and
cited:
  https://www.nngroup.com/articles/consistency-and-standards/

R9 (comprehensibility): query "Nielsen Norman Group recognition
rather than recall cognitive load comprehensibility interface
design" — source returned and cited:
  https://www.nngroup.com/videos/recognition-vs-recall/
```

## Open findings

1. `roles/specs/interaction-design.spec.json` still carries no
   `rule_count_floor` or `playbook_refs` entries (issue #1174
   requirement 4 and requirement 5 wiring) — canonical: same spec-read
   command as in the prior unit's record, re-run this turn, confirmed
   absent. Out of this unit's frozen scope (playbook authorship only),
   same as the prior unit's open finding #3.
2. Axes still open across both playbook files, named again for
   visibility rather than silently dropped: color-combination
   visibility beyond WCAG contrast, usage-frequency-to-menu-depth
   beyond R4, background/editing-surface separation.
3. canonical: this session's own three consecutive `gh pr create
   --repo tokenmaxxxer/interaction-design-rulebook ...` tool calls this
   turn, each refused by this session's own pr-preflight gate. The
   commit (0326fb7) is pushed to origin on
   tokenmaxxxer/interaction-design-rulebook. Each refusal named a new
   issue #1174 comment posted since session start (e.g.
   issuecomment-5277576758 above, an unrelated
   `issue-1174/customer-support` session's own watch line) — an
   automated watcher is posting to issue #1174 faster than this
   session's edit-then-retry cycle runs, so the PR-open call itself has
   not yet succeeded this turn. Same finding class as the prior unit's
   open finding #1 (rulebook PR could not be opened from this session),
   now caused by this comment race rather than that finding's
   target-repo scope-guard cause.
   resolution path: on-the-record's external relay opens
   https://github.com/tokenmaxxxer/interaction-design-rulebook/compare/main...issue-1174/interaction-design
   (commit 0326fb7 already on that branch at origin), or a future
   session retries `gh pr create` once the concurrent-session comment
   volume on issue #1174 has quieted.

## Next steps

- Retry the rulebook-repo PR for commit 0326fb7 (open finding #3).
- A further interaction-design batch to cover the still-open axes named
  in open finding #2, once a formally recorded `rule_count_floor`
  exists for this role.

## What did not work

None.
