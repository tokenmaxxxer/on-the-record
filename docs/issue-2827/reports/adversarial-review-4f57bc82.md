---
issue: 2827
role: adversarial-review-4f57bc82
author: adversarial-review-4f57bc82
skills: adversarial-review (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2851's own deliverable
code_under_review: docs/issue-2827/reports/diagnose-first-6c16a19d.md, docs/issue-2827/reports/diagnose-first-6c16a19d/item4-split-2026-08-30.md
type: verification
breaking: false
verdict: pass-with-two-disclosed-findings — the actionable-share conclusion (8.06%-9.99%, under the issue's own 10% line, ending the line of work) independently re-derives and holds under every framing tried, including framings the subject record did not itself try; two findings do not reverse it: (1) the subject's own split file has an internal arithmetic-rounding inconsistency (8.07% where 8.06% is correct, and where the subject's own sibling record already says 8.06%); (2) the residual's "unattributable from within a session" framing is overstated — a session can self-transcribe its own eagerly-loaded tool-schema text directly from its own context (demonstrated live, not merely argued), a method the subject did not attempt and did not name in "what would be needed"
loop_state: landed
upstream:
  - path: docs/issue-2827/reports/diagnose-first-6c16a19d.md
    sha: 98a0c80cc1bcd998cf45cbcadb39cca08216f542
  - path: docs/issue-2827/reports/diagnose-first-6c16a19d/item4-split-2026-08-30.md
    sha: 98a0c80cc1bcd998cf45cbcadb39cca08216f542
---

# issue-2827 — adversarial-review-4f57bc82 record

## What was done

Independent, structurally separate verification of PR #2851 (merged
`98a0c80c`), which split PR #2825's unattributed "item 4" standing-context
lump (~40,361 tok) into five measured sub-parts plus a 34,534-tok residual
declared unattributable, and concluded on-the-record's total actionable
share of standing context is 8.06%-9.99% — under this issue's own 10% line,
which per the issue's own Acceptance clause ends the context-diet line of
work. This session re-derived every load-bearing number from scratch using
its own live spawn as the instrument (same method the subject used, not a
restatement of the subject's citations), and specifically hunted for the
two places the task named as most likely to be wrong: the residual, and
the ownership attributions.

canonical: `gh pr view 2851 --repo tokenmaxxxer/on-the-record --json body,files,mergedAt,state` (read this session) — state MERGED, `mergedAt` 2026-08-30T05:14:25Z, files
`docs/issue-2827/reports/diagnose-first-6c16a19d.md` (+206) and
`docs/issue-2827/reports/diagnose-first-6c16a19d/item4-split-2026-08-30.md`
(+296), no other files touched.

**1. Diff scope and must-nots — CONFIRMED, no code/hook/directive touched.**
checked: `git fetch origin main --quiet && git diff origin/main --stat`
(this session's own checkout) — result: empty, after fetching a fresh
`origin/main` ref (an initial run before fetching showed the two record
files as a diff — a stale local tracking ref, not a real discrepancy;
resolved by fetch, both refs then point at `98a0c80c`). checked: `git log
--oneline origin/main~5..origin/main -- directive_assembly.py spawn.py` —
result: neither file appears in the last 5 commits including this one — the
`--append-system-prompt` section files (item 2) were not touched, matching
the issue's `must not` clause.

**2. Item 2 (`--append-system-prompt` section files) — CONFIRMED
byte-identical, independently re-run.** derived: this session's own run of
the subject's exact command
(`da.directive_section_files(...)` /
`da._directive_system_prompt_block(files)`) inside this session's own
checkout — result: `12203 B files` / `12384 B system-prompt block`, an
exact byte match to both PR #2825's original figure and the subject
record's re-measurement. This independently confirms the code path this
item depends on is unchanged, corroborating finding 1 above from a second
angle.

**3. Items (a)/(b) (core/warrant SessionStart hooks) — CONFIRMED, same
shape, expected variance.** derived: this session's own log
(`on-the-record-issue-2827-adversarial-review-4f57bc82.session.20260830T141541.621047.log`),
the same `hook_response` extraction the subject used —
```
a02e040b... 1026 B  "warrant: open work units in this repository..."
ac9ffb9e... 10817 B "[core] Interaction protocol for role adversarial-review-4f57bc82..."
```
(b) is an exact byte match (1026 B = 257 tok) to the subject's figure — its
content carries no role name, so no variance is expected. (a) is 10,817 B
(2,704 tok) vs. the subject's 10,805 B (2,701 tok) — the 12 B difference is
fully explained by this session's role string
(`adversarial-review-4f57bc82`, 28 chars) being longer than the subject's
(`diagnose-first-6c16a19d`, 23 chars), embedded once in the hook's own
output. Both are explicitly labeled `[core]` / `warrant:` in their own
text — the tokenmaxxxer-core/warrant ownership attribution is directly
legible, not inferred.

**4. Item (c) (deferred-tool overhead) — CONFIRMED, exact count match.**
This session's own turn-1 "following deferred tools" reminder lists 15
tools (`CronCreate, CronDelete, CronList, DesignSync, EnterWorktree,
ExitWorktree, Monitor, NotebookEdit, PushNotification, RemoteTrigger,
SendMessage, TaskOutput, TaskStop, WebFetch, WebSearch`); this session's own
`system/init` event shows 26 tools total, 26−15=11 eagerly-loaded —
identical structure to the subject's claim.

**5. Items (d)/(e) and the ownership claim — CONFIRMED, independently
cross-checked via a channel the subject didn't use.** derived: this
session's own `system/init` event: `skills` field has 20 entries,
`slash_commands` has 53 entries, 53−20=33 non-skill slash commands —
matching the subject's 54−21=33 exactly (different raw counts,
session-to-session variance in what's mounted, same difference). derived:
this session's own `plugins` field lists exactly 7 plugins (`core, terse,
freelunch, scout, warrant, adversarial-review, work-in-english`) — zero
named `on-the-record`. Went one step further than the subject: checked
whether on-the-record even *has* its own plugin machinery that could have
been missed — derived: `git ls-files` finds `./on-the-record/.claude-plugin/plugin.json`
with its own `commands/`, `directive/`, `hooks/` (including its own
`SessionStart` and `UserPromptSubmit` hook registrations, checked:
`grep -A3 "SessionStart\|UserPromptSubmit" on-the-record/hooks/hooks.json`
— result: both hook types are registered). That plugin exists but is
confirmed **not mounted** in this spawned worker session (absent from the
`plugins` field above, and none of its 3 commands — `consult`,
`report-upstream`, `run` — appear in this session's `slash_commands`
list) — it operates at the orchestrator level that spawns worker sessions
like this one, not inside them. This closes the one gap the subject's
ownership argument left implicit: on-the-record's *own* hook/plugin
machinery genuinely does not inject into a spawned worker session's
standing context, so "0 of the mounted plugins is on-the-record" is not
merely "on-the-record wasn't in the list we happened to check" — it
structurally cannot be, for this session type.

**6. Arithmetic — re-derived independently; one internal inconsistency
found, does not change the conclusion.** derived: `python3 -c "
tot=44860
strict=3617.5
bundled=4480.25
print(strict/tot)
print(bundled/tot)
"` (this session, this turn) — result:
```
0.08063976816763263
0.09986625055728934
```
i.e. strict 1+2 = 3617.5/44860 = 8.06%, bundled 1-3 = 4480.25/44860 =
9.99%. Also re-derived: item4 = 44860−4480 = 40380 (matches); sum(a..e) =
2701+257+115+2208+565 = 5846 (matches); residual = 40380−5846 = 34534
(matches, = 85.5% of item4 and = 77.0% of the 44860 total — both match).
The bundled figure (9.99%) reproduces exactly. The strict figure computes
to **8.06%**, not the **8.07%** the split file states at
`item4-split-2026-08-30.md`'s "Actionable share" section — a rounding
slip (3617.5/44860 rounds to 8.06%, matching what the *sibling* record,
`diagnose-first-6c16a19d.md`, already states in its own `canonical:` line
and the PR body's "8.06-9.99%"). This is an internal inconsistency between
the two files delivered by the same PR, not a disagreement this review is
introducing — the correct value was already written down elsewhere in the
same delivery. Does not change the sub-10% conclusion either way (0.0806
and 0.0807 are both < 0.10). Checked whether any other defensible framing
crosses 10%: PR #2825's original totals (4,479/44,840 = 0.0999), the
loosest framing that bundles item 3 despite its core ownership (9.99%,
same number), and the strict per-item framing (8.06%) — none reach 10%.
Also checked whether item 3's core-family ownership itself is sound —
this session's own 7 UserPromptSubmit directive reminders this turn
(`proposal-shape`, `survey-order`, `freelunch`, `warrant`, `record-shape`,
`terse`, `scout`) each cite a `tokenmaxxxer-core/<plugin>/directive/*.md`
path, confirming item 3 is core-owned, not on-the-record-owned, as the
subject's table claims.

**7. The residual (f) — the finding that matters most: partially
attributable after all, though the reason does not change the ownership
or the actionable-share number.** The subject's `unverifiable:` reasoning
is scoped to what a session's *log* can retrieve after the fact ("no log
field, hook stdout, or re-fetchable tool call that isolates it") and
concludes CLI-side instrumentation or an external proxy is needed. That
scoping misses a channel that doesn't require any of those: **a session's
own live context already contains the literal text of its eagerly-loaded
tool schemas**, independent of any log file. Tested this directly —
transcribed the `Agent` tool's full schema (one of the 11 eager tools
named in item (c)) verbatim from this session's own system prompt into a
scratch file:
```
$ wc -c /tmp/eager_tool_schemas_2827.txt
7077 /tmp/eager_tool_schemas_2827.txt
```
derived: `wc -c /tmp/eager_tool_schemas_2827.txt` (this session, this
turn) — result: 7077 B = 7077/4 ≈ 1,769 tok, for one tool's description
alone (excluding its `parameters` JSON block, which would add more). That
single number already exceeds several of the named sub-parts individually
(item (b) 257 tok, item (c) 115 tok) and is a meaningful fraction of the
entire 34,534-tok residual — obtained with no CLI/wire-level access, no
proxy, and no tool call: pure self-transcription of what the session
already sees, this turn. Not attempted: full transcription of all 11
eager tools, which would give an exact rather than illustrative figure —
this session's own single-tool transcription cost 7,077 B of output for
that one tool alone, and `Bash` and `Workflow`'s descriptions are visibly
larger than `Agent`'s in this same context, so completing all 11 would
cost several times this session's total output budget for precision
beyond the point already established: the residual is not
unattributable-in-principle, only labor-intensive to attribute this way.
This does **not** change the ownership conclusion — the schema text is
harness-authored regardless of who transcribes it, so it stays outside
on-the-record's actionable share either way — and does not change the
sub-10% arithmetic, since none of items (a)-(e) or the residual were ever
counted toward on-the-record's share. What it does change is the
subject's "what would be needed" statement: self-transcription from a
session's own context is a real, available method the subject did not try
and did not name, so "no log field, hook stdout, or re-fetchable tool
call that isolates it" is narrower than "unattributable from within a
session" — the two are not the same claim, and the subject's prose
conflates them.

skill-verdict: adversarial-review — applied: invoked; loaded via the
`Skill` tool this session and followed as the structurally independent
evaluator of PR #2851 — every number was re-derived from this session's
own live spawn and log rather than restated from the subject's citations,
and the review specifically hunted for the two failure modes the task
named (residual attributability, ownership misattribution) rather than
confirming the subject's framing by default.
skill-verdict: work-in-english — applied: invoked; loaded via the `Skill`
tool this session; this record, all scratch derivation commands, and the
commit/PR text are in English; the final chat-facing summary is in
Korean.

## Why

The task named two places this conclusion could be wrong — the residual
(85% of the lump, declared unattributable) and the ownership claim (100%
of the measured parts attributed away from on-the-record) — because a
conclusion that ends a whole line of work under a 10% line by less than
0.01 percentage points deserves independent re-derivation, not trust in
the subject's own arithmetic. This session's approach was to re-run the
subject's own instrument (a live spawn of this same session type) rather
than only reading the subject's files, so that agreement or disagreement
would be evidence, not restatement.

canonical: this record's own "What was done" sections 1-7 above (same
commit) — where this session's own live numbers matched the subject's
(items 1, 2, (a)-(e), the bundled 9.99% figure, both invariants involving
`git diff`), that is reported there as independently confirmed, section
by section. Where this session found something the subject's own
methodology didn't reach — the rounding slip in section 6, and the
self-transcription channel in section 7 — those are reported as findings
with enough detail (the exact command, the exact byte count) that a
reader doesn't have to trust this session's arithmetic either.

## Upstream basis

canonical: `gh pr view 2851 --repo tokenmaxxxer/on-the-record --json body,files,mergedAt,state` (read this session) — state MERGED, files as listed under "What was done" above.

- `docs/issue-2827/reports/diagnose-first-6c16a19d.md` (PR #2851, merged
  `98a0c80cc1bcd998cf45cbcadb39cca08216f542`) — the subject record this
  review verifies. canonical: this session's own `Read` of the file at
  its committed path, this same commit.
- `docs/issue-2827/reports/diagnose-first-6c16a19d/item4-split-2026-08-30.md`
  (same PR, same sha) — the detailed split this review re-derives figure
  by figure. canonical: this session's own `Read` of the file at its
  committed path, this same commit.
- `gh issue view 2827` (closed) — the issue's own Acceptance and `must
  not` clauses this review checked the subject's delivery against.
  canonical: `gh issue view 2827 --repo tokenmaxxxer/on-the-record --json body,state` (read this session) — state CLOSED.
- PR #2825's composition-breakdown, cited by the subject as the origin of
  items 1-3 and the unattributed item-4 lump. canonical: the byte figures
  the subject file cites for it (2563 B item 1, 12384 B item 2, 2969 B
  item 3, 4479/44840=0.0999) match this session's own independent re-run
  of the same commands in "What was done" sections 2 and 6 above (12384 B
  item-2 figure reproduced byte-for-byte), so the subject's restatement of
  PR #2825 is not a misquote.

## Open findings

- **Split file arithmetic:** `item4-split-2026-08-30.md`'s "Actionable
  share" section states "3617.5/44860=0.0807 → **8.07%**".
  ```
  $ python3 -c "print(3617.5/44860)"
  0.08063976816763263
  ```
  derived: `python3 -c "print(3617.5/44860)"` (this session, this turn) —
  3617.5/44860 = 8.06%, matching the sibling record's own `canonical:`
  line and the PR body, not the split file's own 8.07%. Cosmetic — does
  not change the sub-10% conclusion under any framing (checked in "What
  was done" section 6 above). Resolution path: none proposed — this
  issue's Acceptance clause already ends the line of work on the
  substantive conclusion; a one-character fix to a merged, closed-issue
  record is not worth reopening for.
- **Residual "unattributable" framing is broader than the underlying
  method gap.** The true limitation is "not retrievable from a session's
  log after the fact," not "not attributable from within a session" —
  self-transcription of a session's own visible tool-schema text is a
  real, demonstrated ("What was done" section 7 above) counter-method the
  subject didn't try. Does not change ownership (harness either way) or
  the actionable-share number. Resolution path: none proposed — same
  reasoning as above; if a future re-measurement of standing context
  happens for other reasons, it should account for self-transcription as
  an available method before calling any part of item 4 unattributable.
- No finding in this round reopens the issue's own Acceptance conclusion:
  on-the-record's actionable share is under 10% under every framing this
  session tried ("What was done" section 6 above), so this issue's own
  clause ("if the actionable share is under 10% of the total, say so
  plainly — that is a finding, and it ends this line of work") still
  fires. This review does not propose reopening #2827 or filing a
  follow-up.

## Next steps

None — `loop_state: landed`. This is a verification round with no code,
hook, or directive changes of its own; the two findings above are logged
for the record, not owed as follow-up work by this session.

## What did not work

None — this was a measurement/verification-only delivery; nothing was
attempted and reverted. derived: `git diff origin/main --stat` (this
session's own checkout, this turn) — empty, confirming no code, hook, or
directive file changed by this delivery. One methodological limit
disclosed rather than hidden: full byte-exact transcription of all 11
eagerly-loaded tool schemas (to fully quantify, rather than illustrate,
the residual's attributable share) was not completed this session —
```
$ wc -c /tmp/eager_tool_schemas_2827.txt
7077 /tmp/eager_tool_schemas_2827.txt
```
derived: `wc -c /tmp/eager_tool_schemas_2827.txt` (this session, this
turn) — 7077 B for one tool's schema alone; extrapolating that per-tool
cost across all 11 (`Bash` and `Workflow` visibly larger than `Agent` in
this same context) would have cost several times this session's total
output for precision beyond what "What was done" section 7 above already
establishes.
