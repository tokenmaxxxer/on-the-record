---
issue: 2204
role: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2204/reports/conformance-review/survey.md
    sha: fe76ff154c3729a82ec5a3b6af80351469f7f3e3
  - path: docs/issue-2204/proposals/2026-08-24-conformance-review-issue-2204.md
    sha: fe76ff154c3729a82ec5a3b6af80351469f7f3e3
subject: commits 924efed8f9df6df382e6aa54706ff7631e186325,
  262e410dfd444431685c546070991f3afc65f240,
  38f2427ff22fd907ceffe0a9bd3cf1eebb37e027 (pipeline.py, spawn.py;
  branch issue-2204/implementation, PR #2212)
test: issue #2204 body (`## Acceptance`/`## Fix`), decomposed into
  REQ-1..REQ-12 (docs/issue-2204/reports/conformance-review/survey.md,
  "Requirement extraction" section)
result: failed
assertedBy: issue-2204/conformance-review session (role-handoff contract v3)
---

# issue-2204 — conformance-review record

## What was done

Audited the three commits (`924efed8f9df6df382e6aa54706ff7631e186325`,
`262e410dfd444431685c546070991f3afc65f240`,
`38f2427ff22fd907ceffe0a9bd3cf1eebb37e027`) on `issue-2204/implementation`
against the
twelve requirements the phase-1 survey extracted from issue #2204's own
`## Acceptance` (5 bullets) and `## Fix` (6 bullets) text, re-deriving
every verdict against the artifact and, where possible, against a fresh
live reproduction this session ran itself, rather than reusing the
implementation record's own self-assessment.

canonical: this session's own live-spawn measurement (session_id
`91a9a01c-7760-4d20-872b-a90610a7cff3`), docs/issue-2204/reports/conformance-review/survey.md
§3-5.
canonical: pytest tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py
tests/test_spawn_observation_recovery.py -q -m "" — result: pass, 205
passed, 0 failed (survey §7, this session's own combined re-run).
The twelve finding blocks below carry two `Absent` verdicts (REQ-8,
REQ-10); per `roles/specs/conformance-review.spec.json`'s
`recomputation` rule (worst-case across cited entries), that recomputes
this record's own `result` frontmatter field down to the enum value one
step above `Absent`/`Incorrect` in EARL's severity order.
canonical: this session's own live-spawn measurement (session_id
`91a9a01c-7760-4d20-872b-a90610a7cff3`) cited above, combined with the
twelve `verdict:` lines inside the Findings section directly below this
paragraph, this same record, this session.

Two Open Findings are recorded outside the REQ-1..REQ-12 set (below).

## Why

The approved proposal's Rationale rejected trusting the implementation
record's own pasted evidence as sufficient on its own — this role's
`conformance-review-verdict-assignment` skill requires evidence the
review session itself re-derived, and the requirement-extraction skill's
rule 1 requires splitting the `## Fix` section's six bundled bullets
into separate line items rather than scoring the section as one Present
because most of it shipped. Every citation below is this session's own
read, command execution, or live spawn against the artifact, not a copy
of the implementer's account; the full derivation for each lives in
`docs/issue-2204/reports/conformance-review/survey.md`, cited per finding
below.

## Findings

---
requirement: a spawned session's log shows no Read calls for protocol/contract docs before its first task action (REQ-1)
canonical: docs/issue-2204/reports/conformance-review/survey.md §3-4, this session's own live reproduction plus live self-observation.
spec_ref: issue #2204 body, `## Acceptance`, bullet 1
verdict: Surface
evidence: `924efed8:spawn.py` (the `--append-system-prompt`/`_directive_system_prompt_block` wiring, in-repo half — survey §3); this session's own first SessionStart hook message and first tool call, this turn (end-to-end gap — survey §4)
rationale: the in-repo mechanism is independently verified working —
```
$ echo "<task text, no tool use requested>" | claude -p --output-format stream-json --verbose --max-turns 3 --permission-mode bypassPermissions --exclude-dynamic-system-prompt-sections --append-system-prompt "<3492-byte block>" --setting-sources ""
{"type":"assistant","message":{...,"content":[{"type":"text","text":"...TASK-DONE"}],"usage":{...}}}
{"type":"result",...,"num_turns":1,...}
```
canonical: claude -p, fresh git init cwd, flags above — pasted live run
above (executed-unit), session_id `91a9a01c-7760-4d20-872b-a90610a7cff3`
— exactly one `assistant` text message, zero `tool_use` blocks. But
issue #2204's own literal bar names "a spawned session's log", and this
conformance-review session's own first tool call — this turn, before any
task action — was a `Read` of `session-protocol.md`, forced by
`tokenmaxxxer-core`'s separate `directive.sh` `SessionStart` hook, a
repository this PR's write set cannot touch. Failing clause: `##
Acceptance` bullet 1's "no Read calls... before its first task action",
taken end-to-end rather than scoped to this repo's own contribution.

---
requirement: `cache_read_input_tokens` is non-zero on the second and later spawns of a session class (REQ-2)
canonical: docs/issue-2204/reports/conformance-review/survey.md §5, this session's own live-spawn measurement.
spec_ref: issue #2204 body, `## Acceptance`, bullet 2
verdict: Present
evidence: `924efed8:pipeline.py` (`ENABLE_PROMPT_CACHING_1H`/`--exclude-dynamic-system-prompt-sections`, both unconditional in `spawn_cmd()`)
rationale: this session's own live-spawn measurement (session_id
`91a9a01c-7760-4d20-872b-a90610a7cff3`) reads
`cache_read_input_tokens=19201` off the `usage` block, non-zero, using
`--append-system-prompt` content byte-identical to prior sessions' use
of the same directive prose in this same environment — the "second or
later spawn" case, not the stated empty-state exception.

---
requirement: a re-measured docs-only run is materially below the 219s/46s-doc-read baseline (REQ-3)
canonical: docs/issue-2204/reports/conformance-review/survey.md §6, this session's own inspection of the implementation record's own evidence.
spec_ref: issue #2204 body, `## Acceptance`, bullet 3
verdict: Surface
evidence: the implementation record's own "Live-spawn measurement" subsection (read via `git show issue-2204/implementation:docs/issue-2204/reports/implementation.md` this session)
rationale: the Read-round-trip elimination itself is independently
verified (REQ-1's in-repo half, REQ-4 below) and is the dominant
plausible contributor to the original 46s figure, but the record's own
evidence for this specific bullet is content-length parity plus three
single-turn smoke calls on a trivial one-sentence task, not a timed
re-run of a multi-step docs-only role task shaped like the original
219s/46s baseline. Missing-evidence location: a timed real docs-only
issue spawn (post-fix) compared against a timed pre-fix control, both
through `spawn.py`'s actual `_spawn_one()` pipeline — neither the
implementation record nor this review produced one.

---
requirement: every rule/instruction still reaching the session that reached it before (REQ-4)
canonical: docs/issue-2204/reports/conformance-review/survey.md §7, this session's own independent pytest re-execution.
spec_ref: issue #2204 body, `## Acceptance`, bullet 4
verdict: Present
evidence: `924efed8:tests/test_directive_diet_2135.py::DietIntegration::test_moved_prose_absent_inline_present_via_system_prompt`
rationale: independent Test-method re-run per
`conformance-review-verification-method-selection` rule 4 (not a
manual content diff):
```
$ python3 -m pytest tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py tests/test_spawn_observation_recovery.py -q -m ""
205 passed, 1 skipped, 3 xfailed, 2 xpassed in 377.72s (0:06:17)
```
canonical: pytest against a `git worktree add` checkout of
`issue-2204/implementation` — pasted live run above (executed-unit),
combining all three test files the implementation record cites
separately; the content-presence assertion (every materialized section
file's exact byte content inside `append_system_prompt` exactly once)
is inside this 205-passed count.

---
requirement: executed acceptance evidence in the record (REQ-5)
canonical: docs/issue-2204/reports/conformance-review/survey.md §8, this session's own inspection.
spec_ref: issue #2204 body, `## Acceptance`, bullet 5
verdict: Present
evidence: the implementation record's "Acceptance verification"/"Acceptance evidence" sections (read via `git show issue-2204/implementation:docs/issue-2204/reports/implementation.md` this session)
rationale: eight checked-item lines each with their own
`canonical:`/`acceptance:` citation, plus three pasted unit-test runs
and three live-spawn measurements with raw JSON usage fields, matching
contract §20/record-shape's "code plus EXECUTED acceptance evidence"
bar.

---
requirement: investigate first — measure round-trip-vs-prefill-bound and actual cache-miss before changing anything (REQ-6)
canonical: the implementation record's "What was done"/"Why" sections, read via `git show issue-2204/implementation:docs/issue-2204/reports/implementation.md` this session.
spec_ref: issue #2204 body, `## Fix`, "Investigate FIRST" paragraph
verdict: Present
evidence: `924efed8:docs/issue-2204/reports/implementation.md` "What was done" section's scout subsection (its own citation of `on-the-record/hooks/hooks.json` and `spawn.py`'s directive-assembly functions)
rationale: the record's own text shows genuine investigation (isolating
the two Read sources, one in-repo and one in `tokenmaxxxer-core`) before
any code change, and separately reads `cache_read_input_tokens` off a
live spawn's result event per REQ-2's evidence above — both named
sub-conditions of REQ-6 are satisfied.

---
requirement: move the invariant role contract to `--append-system-prompt-file` (REQ-7)
canonical: docs/issue-2204/reports/conformance-review/survey.md §10, this session's own CLI inspection.
spec_ref: issue #2204 body, `## Fix`, bullet 1, clause 1
verdict: Present
evidence: `924efed8:pipeline.py:559-608` (`spawn_cmd()`'s new `append_system_prompt` parameter and `--append-system-prompt` argv wiring)
rationale: independent inspection of this session's own installed CLI:
```
$ claude -p --help | grep -n "^\s*--" | grep -i prompt
  --append-system-prompt <prompt>       Append a system prompt to the default
  --exclude-dynamic-system-prompt-sections
  --system-prompt <prompt>              System prompt to use for the session
```
canonical: claude -p --help — pasted live run above (executed-unit); no
standalone `--append-system-prompt-file`/`--system-prompt-file` flag is
listed, confirming the record's own claim that this environment's CLI
lacks the `-file` variant the issue's cited docs name — `--append-system-prompt`
is the closest available equivalent and is what shipped.

---
requirement: move repo conventions to CLAUDE.md/`.claude/rules/` (REQ-8)
canonical: docs/issue-2204/reports/conformance-review/survey.md §11, this session's own filesystem/diff inspection.
spec_ref: issue #2204 body, `## Fix`, bullet 1, clause 2
verdict: Absent
evidence: repo root (no `CLAUDE.md`, no `.claude/rules/`, either before or after the PR's diff)
rationale:
```
$ git ls-files | grep -i "^CLAUDE.md$"
$ ls .claude/rules/ 2>&1
ls: cannot access '.claude/rules/': No such file or directory
$ git diff origin/main...issue-2204/implementation -- CLAUDE.md .claude/rules/
```
canonical: the three commands and their pasted output directly above —
executed-unit, this session; empty on all three. No file, and no
rationale for the omission anywhere in the implementation record,
deviation log, or consult log (survey §11). Failing clause: `## Fix`
bullet 1's second clause, "repo conventions to CLAUDE.md/`.claude/rules/`".

---
requirement: move anything computed at bootstrap to a `SessionStart` hook's `additionalContext` (REQ-9)
canonical: docs/issue-2204/reports/conformance-review/survey.md §12, this session's own inspection.
spec_ref: issue #2204 body, `## Fix`, bullet 1, clause 3
verdict: Present
evidence: `924efed8:docs/decisions/2026-08-21-single-enforcement-surface.md` (cited in the implementation record's "Upstream basis"); `924efed8:spawn.py` (`_checkpoint_contract_block(issue, role)`, delivered via the same `--append-system-prompt` channel REQ-7 uses)
rationale: this repo has a frozen decision ruling out adding a
`SessionStart` hook to on-the-record as an alternative design; the
bootstrap-computed content this bullet names (the checkpoint contract
block, computed per-spawn) is delivered zero-round-trip via the same
`--append-system-prompt` channel REQ-7 uses instead — the practical
intent (bootstrap content reaching the session with zero Read round
trips) is satisfied through a documented, decision-cited substitute
channel, distinct from REQ-8/REQ-10's silent omission.

---
requirement: decompose the monolithic contract into path-scoped rule fragments so a docs-only task loads only what it needs (REQ-10)
canonical: docs/issue-2204/reports/conformance-review/survey.md §11, this session's own code inspection.
spec_ref: issue #2204 body, `## Fix`, bullet 2
verdict: Absent
evidence: `924efed8:spawn.py:1961` (`directive_section_files()`'s own signature)
rationale:
```
$ git show issue-2204/implementation:spawn.py | grep -n "^def directive_section_files"
def directive_section_files(*, skills_mounted: bool = False,
```
canonical: git show issue-2204/implementation:spawn.py — pasted live
grep above (executed-unit); the function's signature carries no
path/task-shape parameter, so no per-task-shape decomposition exists to
select a subset — the shipped fix still selects a fixed file bundle by
`skills_mounted`/`checkpoint` flags only, regardless of whether the
spawned task is docs-only. No rationale for the omission anywhere in
the implementation record, deviation log, or consult log. Failing
clause: `## Fix` bullet 2 in full.

---
requirement: ship `--exclude-dynamic-system-prompt-sections` and 1h caching together with the above (REQ-11)
canonical: docs/issue-2204/reports/conformance-review/survey.md §10, this session's own diff inspection plus live measurement.
spec_ref: issue #2204 body, `## Fix`, bullet 3
verdict: Present
evidence: `924efed8:pipeline.py` (both flags added unconditionally in `spawn_cmd()`)
rationale:
```
$ git show issue-2204/implementation:pipeline.py | grep -n "exclude-dynamic-system-prompt-sections\|ENABLE_PROMPT_CACHING_1H"
           "--exclude-dynamic-system-prompt-sections"]
           "ENABLE_PROMPT_CACHING_1H": "1",
```
canonical: git show issue-2204/implementation:pipeline.py — pasted live
grep above (executed-unit), corroborated by REQ-2's own live
`cache_read_input_tokens` reading.

---
requirement: `--bare` exists; evaluate but likely out of scope (REQ-12)
canonical: docs/issue-2204/reports/conformance-review/survey.md §12, this session's own diff inspection.
spec_ref: issue #2204 body, `## Fix`, bullet 4
verdict: Present
evidence: `git diff origin/main...issue-2204/implementation --stat` (survey §1, no `--bare`-related change anywhere in the diff)
rationale: the issue's own text pre-concludes `--bare` out of scope
("a larger change than this issue needs"); no independent action is
required beyond not contradicting that pre-scoping, which holds.

## Upstream basis

- `docs/issue-2204/reports/conformance-review/survey.md`, sha
  `fe76ff154c3729a82ec5a3b6af80351469f7f3e3` — requirement extraction
  (REQ-1..REQ-12) and every independent live-reproduction/re-execution
  this record's Findings section builds on.
- `docs/issue-2204/proposals/2026-08-24-conformance-review-issue-2204.md`,
  sha `fe76ff154c3729a82ec5a3b6af80351469f7f3e3` — the approved phase-1
  proposal.
  canonical: `gh issue view 2204 --json comments -q '.comments[] | .author.login+": "+.body'` — executed this session, output below (executed-unit):
  ```
  $ gh issue view 2204 --json comments -q '.comments[] | .author.login+": "+.body'
  JiwonJung94: [watch] issue-2204/implementation: ...
  JiwonJung94: APPROVE issue-2204/execution-observation
  JiwonJung94: APPROVE issue-2204/conformance-review
  JiwonJung94: [watch] issue-2204/execution-observation: ...
  ```
  canonical: fence directly above (executed-unit, this session) — the
  third line matches `APPROVE issue-2204/conformance-review` exactly
  (contract v3 s19 string-equality gate); `JiwonJung94` is listed in
  `docs/specs/approvers.md`, read this session.
  canonical: this session's own measurement — the Findings section
  above (REQ-1..REQ-12) uses exactly the methods and candidate verdicts
  the proposal planned; no divergence from the plan occurred this
  session (see "What did not work" below).
- the implementation record at commit `38f2427f`
  (read via `git show issue-2204/implementation:docs/issue-2204/reports/implementation.md`
  this session, since that path does not exist on this branch's own
  tree) — the artifact this record's Findings independently re-derive
  against, not reuse from.

## Open findings

1. REQ-1 does not hold end-to-end for a real spawned session — the
   larger Read-round-trip source (`tokenmaxxxer-core`'s `directive.sh`
   `SessionStart` hook) is untouched, outside this repo's write set, and
   was freshly reproduced by this review session's own first tool call.
   Already disclosed in the implementation record's own open findings;
   this record's REQ-1 finding adds independent, live corroboration.
   Resolution path: a companion issue against `tokenmaxxxer-core` to
   move `directive.sh`'s output to the `SessionStart`-hook
   `additionalContext` channel — already named in the implementation
   record's own open findings.
2. REQ-8 and REQ-10, two of the six `## Fix` bullets, are `Absent` and
   unacknowledged anywhere in the implementation record, deviation log,
   or consult log — unlike REQ-9, which is at least cited against a
   frozen decision. Resolution path: either a follow-up issue scoping
   the path-scoped `.claude/rules/` decomposition as its own unit of
   work, or an explicit statement (in a revision of the implementation
   record) of why they were judged out of scope for this issue's actual
   fix.

## Next steps

None from this role or branch — `loop_state` above is already this
record kind's terminal value, `reported`.
canonical: `roles/specs/conformance-review.spec.json`'s `loop_state.terminal`
field, read this session — lists `reported` as the sole terminal value.
The two Open Findings above each name their own resolution path and
owner for whoever picks them up next.

## What did not work

The proposal's stated verification command,
`python3 -m gates.record_lint docs/issue-2204/reports/conformance-review.md`,
crashes rather than reporting a violation count:
```
$ python3 -m gates.record_lint docs/issue-2204/reports/conformance-review/survey.md
AttributeError: module 'gates' has no attribute 'RECORD_PATH'
```
canonical: python3 -m gates.record_lint <path>, this session — pasted
live run above (executed-unit); a background warrant-hunter dispatch
this session independently reproduced the same crash and traced it to
`gates/record_lint.py`'s `import gates` resolving to a namespace
package (`gates/` carries no `__init__.py`) rather than `gates/gates.py`
when invoked via `-m`. Out of this role's write set to fix
(`gates/record_lint.py` is shared infra, not this record itself).
Worked around by
using the direct-script form instead, `python3 gates/record_lint.py
<path>`, which does not hit this import path and reports violations
correctly — this is the command actually used to validate this record
and its survey before each write.

Otherwise nothing — this session's re-derivation matched the approved
proposal's plan; every requirement kept the method and candidate
verdict the proposal set out, and no new file outside the proposal's
`files:` set was written by this role.

## Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied: invoked; produced the REQ-1..REQ-12 split in docs/issue-2204/reports/conformance-review/survey.md §2 (this session's own phase-1 half) — one obligation per line, dimension-tagged, backward-traced to issue #2204's own `## Acceptance`/`## Fix` text.

skill-verdict: conformance-review-verification-method-selection — applied: invoked; used rule 4 (Test method for REQ-4/REQ-5's independent pytest re-run, not re-deriving a fresh manual check where an executable test already exists), rule 1 (Inspection for REQ-7/REQ-8/REQ-10/REQ-12's static CLI-help/file-existence/code-signature checks), and Analysis/live reproduction for REQ-1/REQ-2/REQ-3, which only a real spawn could settle (see Findings above, this session).

skill-verdict: conformance-review-verdict-assignment — applied: invoked; used rule 1 (Surface, not Present, for REQ-1/REQ-3: matching evidence exists but does not establish the requirement's literal full condition), rule 5 (REQ-8/REQ-10's Absent verdicts each name their own failing clause rather than a bare label), and rule 4 (REQ-9's Present verdict via a cited substitute mechanism rather than the literal one named). See Findings above, this session.

skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; used rule 1 (`sha:path` pointer via `924efed8:<path>` or an explicit `git show issue-2204/implementation:<path>` command, since none of the implementation branch's own record paths exist on this review branch's tree) and rule 2 (`pipeline.py` and `spawn.py` cited separately per requirement rather than bundled). See Findings above, this session.

skill-verdict: conformance-review-finding-record — applied: invoked; used the field list (`requirement`/`spec_ref`/`verdict`/`evidence`/`rationale`) to shape every block, one per REQ-1..REQ-12. See the Findings section above, this session.

skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of REQ-1..REQ-12 was feasible at this size (three commits, twelve requirement line items) — no stratified sample was needed.

skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope was not explicitly extended into risk-weighting a recorded finding; no severity band was requested.
