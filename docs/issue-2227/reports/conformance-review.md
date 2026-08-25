---
issue: 2227
role: conformance-review
author: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2204/reports/conformance-review.md
    sha: 3318d8d88084ee9c80179d92adc4491401bf424d
  - path: roles/implementation.json
    sha: 5494b62b52a7b39f81c9d6cfe9d165cc620ca440
subject: PR #2338 (tokenmaxxxer/on-the-record) — per-path context scoping
  for spawn.py's spawned-session directive, branch
  issue-2227/implementation, head b2b9c748979a3ab3a59093af569dfbf7d30d58bd
test: issue #2227 body (`## Ask`, `## Non-goals`, `## Acceptance`),
  decomposed into REQ-A..REQ-G below
result: failed
assertedBy: issue-2227/conformance-review session (builder-blind), 2026-08-25
---

# issue-2227 — conformance-review record

## What was done

Builder-blind conformance review of PR #2338 against issue #2227's frozen
`## Ask`/`## Non-goals`/`## Acceptance` text, independent of the PR's own
implementation record's self-assessment (see Upstream basis for the
sha-pinned citation of that record).

canonical: `gh issue view 2227`, `gh pr view 2338`, `gh pr diff 2338`, then
`git fetch origin issue-2227/implementation` + `git worktree add
/tmp/pr2338-wt FETCH_HEAD` (PR #2338 head
`b2b9c748979a3ab3a59093af569dfbf7d30d58bd`) — all four commands run live
this session; every citation, test run, and independent probe below was
read/executed this session, not reused from the builder's account.

Requirement extraction (conformance-review-requirement-extraction):
issue #2227's `## Ask` bundles two independent design questions ("and" —
rule 1) — split into REQ-D (the `.claude/rules/*.md` `paths:`-glob
question, carried from #2204 REQ-8) and REQ-E (directive decomposition by
task class, carried from #2204 REQ-10). `## Acceptance` has three lines —
`gate` (REQ-A), `empty state` (REQ-B), `provenance` (REQ-C) — each already
singular, no split needed. `## Non-goals` has two bullets, kept as their
own scope-boundary items (REQ-F, REQ-G) per rule 6 dimension tagging
rather than folded into REQ-D/REQ-E. No summary line met the rule-3 drop
threshold (three-plus restated sub-points) in this issue body.

Requirement count: `## Ask` (2 bullets) + `## Non-goals` (2 bullets) +
`## Acceptance` (3 lines: gate/empty state/provenance) = 2+2+3 = 7 items
— derived: counted directly off the issue text quoted in `gh issue view
2227`'s output this session; full enumeration, no sampling needed.

Requirement list (dimension-tagged, rule 6):
- **REQ-A** (functional) — gate: `tests/test_spawn_directive_assembly.py`
  passes.
- **REQ-B** (edge-case) — empty state: a task matching no path scope
  still receives the invariant baseline directive, never an empty one.
- **REQ-C** (functional/evidence) — provenance: executed-live, both a
  real docs-only and a real engineering spawn, actual measured directive
  sizes and bootstrap timings pasted, docs-only genuinely smaller; a size
  claim without both live spawns does not satisfy this.
- **REQ-D** (scope-boundary/decision) — decide whether repo conventions
  belong in `.claude/rules/*.md` with `paths:` globs (the platform's
  native mechanism) rather than the injected directive (#2204 REQ-8,
  carried forward).
- **REQ-E** (functional/decision) — decide whether the directive itself
  should decompose by task class, so a docs-only task loads less (#2204
  REQ-10, carried forward); conditional on REQ-D's outcome per rule 5 —
  if REQ-D finds a native mechanism viable, REQ-E's implementation channel
  changes.
- **REQ-F** (scope-boundary) — non-goal: do not revisit
  `--append-system-prompt` or the caching flags from #2212.
- **REQ-G** (scope-boundary/error-handling) — non-goal: do not reduce
  what sessions are told in a way that weakens gates or the record
  contract; any speed gain must not come with a correctness regression.

## Why

This role's mandate is builder-blind re-derivation, not reuse of the
implementation record's own account — per verdict-assignment rule 6
(re-check an Absent/Incorrect-leaning verdict against the artifact before
finalizing it) rather than trusting a self-report. This review's own
brief specifically named REQ-D's evidence for closer scrutiny; see the
REQ-D finding below for why `verification-method-selection` rule 1
(Inspection for a structural "does this primitive exist" claim) still
applies but over a different, more direct artifact than the one PR #2338
inspected.

## Findings

---
requirement: gate `tests/test_spawn_directive_assembly.py` passes (REQ-A)
canonical: this session's own independent pytest re-execution against PR
#2338's head commit, in a fresh worktree.
spec_ref: issue #2227 body, `## Acceptance`, `gate` line
verdict: Present
evidence: `b2b9c748:tests/test_spawn_directive_assembly.py` (full file, 39
tests across 6 classes)
rationale: independent re-run, PR head, and independent re-run against
`main` (pre-change) to isolate whether the one failure is a regression:
```
$ git worktree add /tmp/pr2338-wt b2b9c748979a3ab3a59093af569dfbf7d30d58bd
$ cd /tmp/pr2338-wt && python3 -m pytest tests/test_spawn_directive_assembly.py -q -m ""
1 failed, 38 passed in 1.42s
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
$ git worktree add /tmp/main-wt main
$ cd /tmp/main-wt && python3 -m pytest tests/test_spawn_directive_assembly.py -q -m "" -k test_without_flag_is_byte_identical_to_today
1 failed in 1.51s
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
```
canonical: both pytest invocations and their pasted output above —
executed-unit, this session; the failure reproduces identically on `main`
(this session's own `CORE_BUILD_NOW=1` leaking into `os.environ`, which
the test's own assertion inspects directly), confirming it predates this
diff and is not a regression PR #2338 introduced.

---
requirement: a task matching no path scope still gets the invariant
  baseline directive, never an empty one (REQ-B)
canonical: this session's own independent pytest re-execution plus
inspection of `directive_section_files()`'s body, PR #2338 head.
spec_ref: issue #2227 body, `## Acceptance`, `empty state` line
verdict: Present
evidence: `b2b9c748:spawn.py` `directive_section_files()` —
`completion-and-landing.md`/`repo-discovery.md`/`turn-budget.md` are
assigned to the `files` dict unconditionally, before the
`if code_scoped:` branch that adds `known-paths.md`
rationale: independent re-run, PR head worktree:
```
$ python3 -m pytest tests/test_spawn_directive_assembly.py -q -m "" -k "RoleTouchesCode or DirectiveSectionFilesCodeScoping or PerPathContextScopingEndToEnd"
10 passed in 1.08s
```
canonical: pytest invocation and pasted output above — executed-unit,
this session; combined with the inspection of `directive_section_files()`
above (the three baseline keys are set before the conditional branch, so
`code_scoped=False`/an empty `write_scope` never removes them) this
satisfies the empty-state bar.

---
requirement: provenance — executed-live docs-only and engineering
  spawns, actual measured sizes/timings pasted, docs-only genuinely
  smaller (REQ-C)
canonical: this session's own re-run of the implementation record's
directive-size snippet, plus inspection of the record's pasted live
`claude -p` output; cross-check against the #2204 record's evidence
format for the same claim type.
spec_ref: issue #2227 body, `## Acceptance`, `provenance` line
verdict: Present
evidence: `b2b9c748979a3ab3a59093af569dfbf7d30d58bd:docs/issue-2227/reports/implementation.md`
"Live-spawn measurement" and "Directive-size comparison" subsections
(untracked on this `conformance-review` branch, PR-only path, hence the
sha pin)
rationale: re-ran the record's own directive-size snippet against the PR
head worktree:
```
$ python3 -c "
import spawn
code = spawn.directive_section_files(skills_mounted=True, code_scoped=True)
docs = spawn.directive_section_files(skills_mounted=True, code_scoped=False)
print(len(spawn._directive_system_prompt_block(code).encode()),
      len(spawn._directive_system_prompt_block(docs).encode()))
"
5885 5035
```
canonical: python3 -c snippet and pasted output above — executed-unit,
this session; byte-identical to the record's own pasted figures (5885 /
5035), and internally consistent with the record's pasted live `claude
-p` `result.duration_api_ms`/`usage.cache_creation_input_tokens` pair
(8694ms/8595 tokens engineering vs. 7958ms/8173 tokens docs-only) — a
smaller appended block plausibly costing fewer cache-creation tokens and
less API time. One evidence-citation gap noted, not scored as failing
this requirement: the record cites `--append-system-prompt
"$SYS_ENG"`/`"$SYS_DOCS"` without pasting the command that assigned those
shell variables from `_directive_system_prompt_block(directive_section_files(...))`,
so a reader cannot mechanically re-derive that the live-spawn content was
byte-identical to the code's actual output. Checked whether this is a
fresh gap in this PR or inherited: `3318d8d8:docs/issue-2204/reports/implementation.md`
line 243 uses the identical unexplained `"$SYS_PROMPT"` pattern for the
analogous #2204 claim, and that specific gap was not among the two
`Absent` findings `3318d8d8:docs/issue-2204/reports/conformance-review.md`
raised against #2204 — a pre-existing, previously-tolerated repo
convention, not a defect PR #2338 introduced.

---
requirement: decide whether repo conventions belong in
  `.claude/rules/*.md` with `paths:` globs rather than the injected
  directive (REQ-D, #2204 REQ-8 carried forward)
canonical: this session's own independent CLI-binary inspection, same
machine/CLI install PR #2338 cites.
spec_ref: issue #2227 body, `## Ask`, bullet 1
verdict: Incorrect
evidence: `b2b9c748979a3ab3a59093af569dfbf7d30d58bd:docs/issue-2227/reports/implementation.md`
"REQ-8 mechanism check" subsection (`claude --help 2>&1 | grep -iE
"rule|claude\.md|setting-sources"`, no hit) (untracked on this
`conformance-review` branch, PR-only path, hence the sha pin)
rationale: re-ran the record's version check, then inspected a different,
more direct artifact than `--help` — the installed CLI binary's own
embedded prompt strings:
```
$ claude --version
2.1.243 (Claude Code)
$ strings "$CLAUDE_CODE_EXECPATH" | grep -iE "claude/rules" | head -3
LOCAL files: `~/.claude/CLAUDE.md` and `CLAUDE.local.md` (project root and ancestor dirs). Checked-in files: `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/rules/*.md` in the project, including nested directories.
- Mind loading scope: a `.claude/rules/*.md` file with `paths` frontmatter (or a nested-directory CLAUDE.md) loads only when Claude works with matching files, while LOCAL files are always in context ...
... Config surfaces: `.claude/settings*.json`, `CLAUDE.md`, `CLAUDE.local.md`, `.claude.json`, `.claude/rules/`, `.claude/hooks/`, `.claude/commands/`, `.claude/agents/`, `.claude/skills/`, ...
```
canonical: `claude --version` and the `strings`/`grep` command above,
pasted live run this session, same `2.1.243` install PR #2338 cites —
`--help` lists CLI invocation flags only; it does not list `CLAUDE.md`,
`.claude/skills/`, `.claude/hooks/`, or `.claude/agents/` either, and none
of those are disputed as real, working features, so absence from
`--help` is not evidence of absence for a file-convention feature. The
CLI's own bundled prompt text above describes `.claude/rules/*.md` with
`paths` frontmatter as a real, loaded, path-scoped config surface,
directly contradicting "there is nothing to move injected-directive
content into." Incorrect per verdict-assignment rule 2: the artifact
(the rejection decision) actively contradicts the requirement's actual
condition (whether the native mechanism exists), rather than merely
omitting an answer.
spec_vs_built: issue #2227 asked "whether repo conventions belong in
`.claude/rules/*.md` with `paths:` globs (the platform's native
mechanism)" — a decision presupposing a check of whether that mechanism
exists. PR #2338 built a decision record concluding it does not exist,
checked via a CLI-flag listing (`--help`) that was never going to list a
file-convention feature. The mechanism does exist on the same installed
CLI version the PR itself cites (pasted above), so the actual design
question issue #2227 raised — whether the injected-directive content
should move into `.claude/rules/*.md` instead of `spawn.py`'s
`--append-system-prompt` channel — remains genuinely open and undecided,
dressed as a closed one by `Closes #2227`.

---
requirement: decide whether the directive should decompose by task
  class so a docs-only task loads less, and implement it (REQ-E, #2204
  REQ-10 carried forward)
canonical: this session's own independent pytest re-execution plus
independent re-run of the record's role inventory snippet, PR head.
spec_ref: issue #2227 body, `## Ask`, bullet 2
verdict: Present
evidence: `b2b9c748:spawn.py` — `_role_touches_code(write_scope: list)`
(new helper) and `directive_section_files(..., code_scoped: bool =
True)` gating `known-paths.md`; call site
`directive_section_files(..., code_scoped=_role_touches_code(spec.get("write_scope", [])))`
inside `_run_auto_sweep()`, where `spec = json.loads((ROOT / "roles" /
f"{role}.json").read_text())` is assigned earlier in the same function
scope (inspected directly, not shadowed)
rationale: independent re-run of the record's own role-inventory snippet
against the PR head worktree:
```
$ python3 -c "
import spawn, json
n=0
for p in sorted((spawn.ROOT/'roles').glob('*.json')):
    spec = json.loads(p.read_text())
    n+=1
    if spawn._role_touches_code(spec.get('write_scope', [])):
        print(p.stem, spec.get('write_scope'))
print('total roles', n)
"
implementation ['src/**', 'test/**', 'tests/**']
total roles 44
```
canonical: python3 -c snippet and pasted output above — executed-unit,
this session; matches the record's claim exactly (`implementation` sole
code_scoped role among 44). REQ-E is implemented and test-covered on its
own technical merits, independent of REQ-D's outcome — but see Open
findings: the record's own "Why" section states this channel was chosen
"instead" of `.claude/rules/*.md` specifically because REQ-D found no
native mechanism, a premise this review found Incorrect above.

---
requirement: do not revisit `--append-system-prompt` or the caching
  flags from #2212 (REQ-F)
canonical: this session's own diff inspection between `main` and PR
#2338's head.
spec_ref: issue #2227 body, `## Non-goals`, bullet 1
verdict: Present
evidence: `git diff origin/main...b2b9c748979a3ab3a59093af569dfbf7d30d58bd -- spawn.py`
(read this session)
rationale:
```
$ git diff origin/main...b2b9c748979a3ab3a59093af569dfbf7d30d58bd --stat -- spawn.py pipeline.py
spawn.py                    | 42 +++++++++++++++++++---
```
canonical: git diff above, this session — `pipeline.py` (the file
`--append-system-prompt`/`ENABLE_PROMPT_CACHING_1H`/
`--exclude-dynamic-system-prompt-sections` live in, per REQ-7's citation
in the #2204 record) shows zero changed lines; the `spawn.py` diff's only
behavior-changing hunk is the `code_scoped` conditional and the one
call-site kwarg.

---
requirement: do not reduce what sessions are told in a way that weakens
  gates or the record contract; no correctness regression alongside any
  speed gain (REQ-G)
canonical: this session's own independent pytest re-execution of the
surrounding suites, PR head worktree.
spec_ref: issue #2227 body, `## Non-goals`, bullet 2
verdict: Present
evidence: `b2b9c748:spawn.py` `directive_section_files()` default
`code_scoped: bool = True`; `b2b9c748:tests/test_directive_diet_2135.py`,
`tests/test_spawn_observation_recovery.py` (existing suites, unchanged
call sites)
rationale: independent re-run, PR head worktree:
```
$ python3 -m pytest tests/test_spawn_observation_recovery.py tests/test_directive_diet_2135.py -q -m ""
1 failed, 177 passed, 1 skipped, 4 xfailed, 1 xpassed in 84.28s (0:01:24)
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal
```
canonical: pytest invocation and pasted output above — executed-unit,
this session; matches the record's own pasted count exactly. The one
failure is an unrelated background-delegation-phrasing subsystem, not
touched by this diff. Every pre-existing caller of
`directive_section_files()` omits the new kwarg and so keeps
`code_scoped=True` (today's full bundle) — no narrowing by omission, no
gate or record-contract content removed for any role.

## Upstream basis

- `docs/issue-2204/reports/conformance-review.md`
  (`sha: 3318d8d88084ee9c80179d92adc4491401bf424d`) — the REQ-8/REQ-10
  `Absent` findings issue #2227 carries forward; both re-derived above as
  REQ-D (now Incorrect, not Absent — a decision was made this time, and
  it is wrong) and REQ-E (Present).
- `roles/implementation.json` / `roles/*.json`
  (`sha: 5494b62b52a7b39f81c9d6cfe9d165cc620ca440`) — the `write_scope`
  inventory REQ-E's finding re-derives independently.
- PR #2338 (`tokenmaxxxer/on-the-record`, branch
  `issue-2227/implementation`, head
  `b2b9c748979a3ab3a59093af569dfbf7d30d58bd`) — `spawn.py`,
  `tests/test_spawn_directive_assembly.py`,
  `docs/issue-2227/reports/implementation.md` (untracked on this
  `conformance-review` branch, PR-only path, hence the sha pin throughout
  this record), all read via `gh pr diff 2338` and a local worktree
  checkout of `FETCH_HEAD`.
- This machine's installed `claude` CLI, `$CLAUDE_CODE_EXECPATH`, the
  target of the independent CLI-binary inspection cited in the REQ-D
  finding above.

```
$ claude --version
2.1.243 (Claude Code)
```
canonical: `claude --version` above, pasted live run this session,
version-matched to the one PR #2338 cites — full `strings`/`grep` command
and output pasted in the REQ-D finding in `## Findings` above.

## Open findings

1. REQ-D is `Incorrect`, per the finding above:
```
$ strings "$CLAUDE_CODE_EXECPATH" | grep -iE "claude/rules" | head -1
LOCAL files: `~/.claude/CLAUDE.md` and `CLAUDE.local.md` (project root and ancestor dirs). Checked-in files: `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/rules/*.md` in the project, including nested directories.
```
   canonical: `strings`/`grep` command and pasted output above —
   executed-unit, this session, same as the REQ-D finding in
   `## Findings`. PR #2338's rejection of the `.claude/rules/*.md`
   `paths:`-glob mechanism rests on evidence (`claude --help` grep) that
   does not actually test for the mechanism's existence; the independent
   CLI-binary inspection above finds the mechanism real and documented
   as a loaded config surface. Until re-decided, issue #2227's `## Ask`
   bullet 1 is not genuinely resolved and the `Closes #2227` trailer on
   PR #2338 overstates what was delivered. Resolution path: re-open the
   REQ-D decision against the correct evidence (the CLI's actual
   `CLAUDE.md`/`.claude/rules/*.md` discovery behavior — e.g. a
   `.claude/rules/*.md` file with `paths:` frontmatter placed in a
   scratch repo and observed to load only for matching files — not a
   `--help` flag grep), then decide with eyes open whether REQ-E's
   injected-directive channel is still the right mechanism or whether
   some/all of it should move to the native `.claude/rules/*.md`
   primitive.
2. REQ-C's evidence-citation gap (unexplained `$SYS_ENG`/`$SYS_DOCS`
   shell variables) — not scored as a failure (inherited,
   previously-tolerated convention from #2204's own record, see REQ-C
   finding above). Resolution path: a future record in this lineage
   should paste the variable-assignment command alongside the live
   `claude -p` invocation; no action required on this PR specifically
   since it did not introduce the gap.

## Next steps

None from this review's own side — `loop_state` above is this record
kind's terminal value, `reported`. For the owning role: PR #2338 should
not be treated as having closed issue #2227; REQ-D needs to be
re-investigated against the CLI's actual `.claude/rules/*.md` behavior
(not `--help`) and the resulting design decision re-recorded before the
issue is re-closed. REQ-A/B/C/E/F/G stand as independently verified
Present and do not need rework on their own account.

canonical: `gh pr view 2338 --json body -q .body` — result: `Closes
#2227` trailer present in the PR body pasted this session (see `## What
was done`); the recommendation above rests on the REQ-D finding's
`strings`/`grep` command and pasted output in `## Findings`.

## What did not work

None for this review's own execution — every citation above was read or
re-run live this session. Noted as an evidence gap in the artifact under
review, not a review-process failure: PR #2338's own record has one small
evidence-citation gap on REQ-C (see Findings), inherited from established
repo convention rather than introduced by this PR.

## Skill verdicts

canonical: `gh issue view 2227` — result: `## Ask`/`## Non-goals`/
`## Acceptance` text pasted/decomposed in `## What was done` above,
executed-unit this session; the skill-verdict lines below summarize how
that decomposition and the Findings above were produced.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; used to split issue #2227's `## Ask` into REQ-D/REQ-E, keep `## Non-goals`' two bullets as separate scope-boundary items, and dimension-tag the full REQ-A..REQ-G list before any verdict was rendered.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; routed REQ-A/REQ-E/REQ-G to Test (reusing/re-running the existing suite) and REQ-D's structural "does this primitive exist" claim to Inspection, over a second more direct artifact (the CLI binary) after recognizing the PR's own Inspection target (`--help`) was the wrong one for a file-convention feature.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; used rule 2 to assign REQ-D `Incorrect` rather than `Absent` (a decision was made and recorded, and it is wrong, not merely missing) and rule 6 to re-check that verdict against a second independent evidence source before finalizing it.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every Findings-block evidence line above cites file/section plus the exact PR head sha (`b2b9c748979a3ab3a59093af569dfbf7d30d58bd`) or the independently-run command, and REQ-C's finding applies rule 1 to flag the builder's own record for the same citation gap this skill guards against.
skill-verdict: conformance-review-finding-record — applied: invoked; each Findings block carries the full field list (requirement, spec_ref, verdict, evidence, rationale, and `spec_vs_built` for the one `Incorrect` verdict), and no verdict above was written without an evidence pointer and a spec_ref.
skill-verdict: conformance-review-sampling-derivation — not-applicable: `## Ask`(2)+`## Non-goals`(2)+`## Acceptance`(3) = 2+2+3 = 7 items total, full enumeration against one PR, no sampling scope needed — derived: counted in `## What was done` above, canonical: `gh issue view 2227`, executed-unit this session.
skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope was not explicitly extended into risk-weighting a recorded finding; REQ-D's `Incorrect` verdict and its `Closes #2227`-overstatement consequence are stated in the finding itself, not banded.
skill-verdict: implementation-audit — not-applicable: this task is already the more specific `conformance-review` role/skill family (builder-blind structural independence already satisfied by this being a separate reviewing session with no access to the builder session); no separate builder/evaluator claim-extraction split was layered on top.
other mounted skills (freelunch, terse, scout, warrant, dataviz,
code-review, etc.): not triggered — this task's own directives route
delegation/style/scouting through the core rulebook hooks referenced at
session start, not through these plugin-listed skills.
