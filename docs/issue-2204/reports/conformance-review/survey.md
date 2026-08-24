# issue-2204 conformance-review — current-state survey

Phase-1 survey (survey-order-directive) for the conformance audit of the
three commits on `issue-2204/implementation`, auto-spawned by
`spawn_on_pr.py` on that branch's PR creation.

```
$ git log --oneline origin/main..issue-2204/implementation
38f2427f issue-2204: consult-trace (ok)
262e410d issue-2204: log the tokenmaxxxer-core out-of-scope deviation
924efed8 issue-2204: append protocol/skill directive prose via --append-system-prompt, fix cross-cwd cache miss
```
canonical: git log --oneline origin/main..issue-2204/implementation —
pasted live run above (executed-unit).

## 1. What landed

```
$ git diff --stat origin/main...issue-2204/implementation
 docs/issue-2204/reports/consult-log.md             |   1 +
 docs/issue-2204/reports/implementation.md          | 296 +++++++++++++++++++++
 .../reports/implementation/deviation-log.md        |   3 +
 pipeline.py                                        |  34 ++-
 spawn.py                                           |  86 ++++--
 tests/test_directive_diet_2135.py                  |  31 ++-
 tests/test_spawn_directive_assembly.py             |  41 ++-
 tests/test_spawn_observation_recovery.py           |  32 ++-
 8 files changed, 459 insertions(+), 65 deletions(-)
```
canonical: git diff --stat origin/main...issue-2204/implementation —
pasted live run above (executed-unit). Two source files touched
(`pipeline.py`, `spawn.py`), three test files, plus the implementation
role's own docs/issue-2204/reports paths — none of those three record
paths exist on this review branch's own tree; every citation to any of
them below reads via a `git show issue-2204/implementation:<path>`
command, never a local file.

```
$ git show issue-2204/implementation:docs/issue-2204/reports/implementation.md | head -5
---
issue: 2204
role: implementation
loop_state: landed
```
canonical: git show issue-2204/implementation:docs/issue-2204/reports/implementation.md
— pasted live run above (executed-unit). `loop_state: landed`; body's
"What was done" opens "CORE_BUILD_NOW=1 build-now bypass — delivered
directly on this branch, no phase-1 proposal round" (read in full this
session, quoted verbatim).

## 2. Requirement extraction (conformance-review-requirement-extraction applied)

canonical: gh issue view 2204 — read in full at session start this
session; every quoted line below is verbatim from that read.

**From `## Acceptance` (the formal pass/fail bar), rule 1/rule 6 split
and dimension-tagged:**

1. **REQ-1** (functional-behavior) — "check: a spawned session's log
   shows no Read calls for protocol/contract docs before its first task
   action — verified against a live spawn's session log"
2. **REQ-2** (functional-behavior, exception stated inline per rule 5) —
   "`cache_read_input_tokens` is non-zero on the second and later spawns
   of a session class — read from the live result event"; exception:
   "empty state: a first-ever spawn has nothing cached and legitimately
   shows a cache write, not a read."
3. **REQ-3** (functional-behavior, loosely bounded — rule 2 candidate) —
   "A re-measured docs-only run is materially below the 219s /
   46s-doc-read baseline." No numeric threshold for "materially below";
   not flagged fully unverifiable since a large ratio improvement
   plainly qualifies either way.
4. **REQ-4** (regression) — "Every rule/instruction still reaching the
   session that reached it before (regression guard — assert content
   presence, not just absence of Reads)."
5. **REQ-5** (process/scope-boundary) — "Executed acceptance evidence in
   the record (#2137)."

**From `## Fix` (rule 1 split across its bundled bullets):**

6. **REQ-6** (scope-boundary/process) — "Investigate FIRST... Measure
   both before changing anything" (round-trip-vs-prefill-bound; whether
   the cache is actually missed).
7. **REQ-7** (functional-behavior) — "Move the invariant role contract
   to `--append-system-prompt-file`."
8. **REQ-8** (functional-behavior) — "repo conventions to
   CLAUDE.md/`.claude/rules/`."
9. **REQ-9** (functional-behavior) — "anything computed at bootstrap to
   a `SessionStart` hook's `additionalContext`."
10. **REQ-10** (functional-behavior) — "Decompose the monolithic
    contract into path-scoped rule fragments so a docs-only task loads
    only what it needs."
11. **REQ-11** (functional-behavior) — "Ship
    `--exclude-dynamic-system-prompt-sections` and 1h caching together
    with the above."
12. **REQ-12** (scope-boundary, pre-resolved by the issue itself) —
    "Note `--bare` exists... a larger change than this issue needs."

No further split needed (each line above is already one obligation); no
redundant summary line; no sampling derivation stated in the issue to
reuse (§14 states this review's own derivation instead).

## 3. REQ-1 in-repo half — independent live reproduction

```
$ cd <git worktree add /tmp/wt-issue-2204-impl issue-2204/implementation> && python3 -c "
import spawn
files = spawn.directive_section_files(skills_mounted=True)
block = spawn._directive_system_prompt_block(files)
print('files:', list(files.keys()))
print('block_bytes:', len(block.encode()))
"
files: ['completion-and-landing.md', 'repo-discovery.md', 'skill-obligations.md']
block_bytes: 3492
```
canonical: python3 -c "import spawn; ..." against a git worktree
checkout of issue-2204/implementation — pasted live run above
(executed-unit); re-derives the byte-length figure from the fix's own
code, independent of the implementation record's own claim of the same
number.

```
$ echo "<task text, no tool use requested>" | claude -p --output-format stream-json --verbose \
  --max-turns 3 --permission-mode bypassPermissions \
  --exclude-dynamic-system-prompt-sections \
  --append-system-prompt "<the block above>" --setting-sources ""
{"type":"assistant","message":{...,"content":[{"type":"text","text":
"랜딩 시에는 변경을 반드시 이 턴 안에서 직접 커밋하고(미커밋 = 미완료, ...) ...\n\nTASK-DONE"}],
"usage":{"input_tokens":2,"cache_creation_input_tokens":4158,"cache_read_input_tokens":19201,...}}}
{"type":"result",...,"num_turns":1,...}
```
canonical: this session's own live-spawn measurement (session_id
`91a9a01c-7760-4d20-872b-a90610a7cff3`), fresh `git init` cwd, flags
above — pasted live run above (executed-unit); the pasted event stream
carries exactly one `assistant` text message with no `tool_use` blocks,
then one `result` event — the summary text states the injected landing
rule, sourced only from the appended system prompt.

REQ-1 in-repo-half candidate verdict: Present.
canonical: the two pasted live runs directly above this line, this
section.

## 4. REQ-1 end-to-end gap — live self-observation (candidate Surface overall)

```
[this conformance-review session's own first SessionStart hook message,
this turn, quoted verbatim from this conversation's own transcript]:
"[core] Interaction protocol for role conformance-review (role-handoff
contract v3)... Read
/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core/directive/session-protocol.md
NOW, before any work: it is the full protocol..."
```
canonical: this session's own transcript, first SessionStart hook
message this turn — quoted verbatim above; this session's own first
tool call was a `Read` of that exact file, made in direct response to
that instruction, before any task action.

```
$ git show issue-2204/implementation:docs/issue-2204/reports/implementation.md | grep -A3 "session-protocol.md.*Read stays"
```
canonical: git show issue-2204/implementation:docs/issue-2204/reports/implementation.md
— "Open findings" section, pasted live grep above (executed-unit);
states "`tokenmaxxxer-core`'s `session-protocol.md` Read stays in
place... this is the larger of the two Read-round-trip sources the
issue measured... This repo's write set has no commit access to that
repository" (quoted verbatim from that read).

REQ-1 end-to-end candidate verdict: Surface — §3's in-repo mechanism
works; a real spawned session's log still shows a Read call for
`session-protocol.md` before its first task action, sourced from a
separate repository outside this PR's write set.
canonical: §3 and §4's live-run/self-observation citations above,
combined.

## 5. REQ-2 — independent verification (candidate Present)

canonical: this session's own live-spawn measurement quoted in §3 above
— `cache_read_input_tokens` field read directly off its `usage` block,
value `19201`, non-zero; this session's own `--append-system-prompt`
content is byte-identical to prior sessions' use of the same directive
prose in this same environment, reproducing the "second or later spawn"
case rather than the stated empty-state exception.

## 6. REQ-3 — partial evidence only (candidate Surface)

```
$ git show issue-2204/implementation:docs/issue-2204/reports/implementation.md | grep -B1 -A3 "Run 1 \`dirA\`"
Run 1 (`dirA`, fresh git repo, `--append-system-prompt <content>`
`--exclude-dynamic-system-prompt-sections`, task: summarize the landing
rule in one sentence then answer only `TASK-DONE`, do not use tools):
```
canonical: git show issue-2204/implementation:docs/issue-2204/reports/implementation.md
— pasted live grep above (executed-unit); the record's own evidence for
this bullet is content-length parity (§3) plus three single-turn smoke
calls on a trivial one-sentence task, not a re-run of a multi-step
docs-only role task shaped like the original baseline. This survey
turned up no timed re-measurement of a real docs-only role spawn
anywhere in that record.

REQ-3 candidate verdict: Surface — the Read-round-trip elimination
itself is independently verified (§3-4) and is the dominant plausible
contributor to the original figure, but the "materially below baseline"
re-measurement itself is missing. Missing-evidence location per
verdict-assignment rule 1 (and rule 3): a timed real docs-only issue
spawn (post-fix) compared against a timed pre-fix control, both through
spawn.py's actual `_spawn_one()` pipeline.
canonical: the grep pasted directly above this subsection, combined with
§3's content-length citation.

## 7. REQ-4 — independent re-execution (candidate Present)

```
$ python3 -m pytest tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py tests/test_spawn_observation_recovery.py -q -m ""
........................................................................ [ 34%]
........................................................................ [ 68%]
xX...X.....x..........................................x............      [100%]
205 passed, 1 skipped, 3 xfailed, 2 xpassed in 377.72s (0:06:17)
```
canonical: pytest tests/test_directive_diet_2135.py
tests/test_spawn_directive_assembly.py tests/test_spawn_observation_recovery.py
-q -m "" against a git worktree checkout of issue-2204/implementation —
pasted live run above (executed-unit), run in background this session.
Combines all three files the implementation record cites separately;
zero failed.

```
$ git show issue-2204/implementation:tests/test_directive_diet_2135.py | grep -n "assertEqual(system_prompt.count"
            self.assertEqual(system_prompt.count(body), 1)
```
canonical: git show issue-2204/implementation:tests/test_directive_diet_2135.py
— pasted live grep above (executed-unit); this is
`test_moved_prose_absent_inline_present_via_system_prompt`'s
content-presence assertion (every materialized section file's exact
byte content must appear inside `append_system_prompt` exactly once),
inside the run pasted directly above this subsection.

## 8. REQ-5 — inspection (candidate Present)

canonical: git show issue-2204/implementation:docs/issue-2204/reports/implementation.md
— read in full this session; its "Acceptance verification" section
carries eight checked-item lines each with its own
`canonical:`/`acceptance:` citation, and its "Acceptance evidence"
section pastes three unit-test runs and three live-spawn measurements
with raw JSON usage fields, matching contract §20/record-shape's "code
plus EXECUTED acceptance evidence" bar.

## 9. Spot-check — the record's two "pre-existing, unrelated" failure claims

```
$ python3 -m pytest tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch -q -m ""
1 failed, 1 passed in 11.80s
FAILED tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
```
canonical: pytest tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
-q -m "", run on this session's own branch
(`issue-2204/conformance-review`, based on `origin/main`, zero code diff
per §1's `git diff --stat`) — pasted live run above (executed-unit).
`RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch`
fails identically on plain `main` here, matching the record's claim for
that one test.
`SinglePhaseSignal::test_without_flag_is_byte_identical_to_today` shows
green here on plain `main`.

```
$ env | grep CORE_BUILD
[empty]
```
canonical: env | grep CORE_BUILD, this session — pasted live run above
(executed-unit); this session's own environment carries no
`CORE_BUILD_NOW`. This corroborates rather than contradicts the
implementation record's own explanation (§1's citation of that record's
"Acceptance evidence" section) that the failure is an artifact of the
implementation session's own `CORE_BUILD_NOW=1` process environment
leaking into `spy_popen`'s captured `os.environ` snapshot, not a
`main`-branch code defect.

## 10. REQ-7, REQ-11 — static inspection (candidate Present)

```
$ claude -p --help | grep -n "^\s*--" | grep -i prompt
  --append-system-prompt <prompt>       Append a system prompt to the default
                                        --append-system-prompt[-file], --add-dir
  --exclude-dynamic-system-prompt-sections
  --system-prompt <prompt>              System prompt to use for the session
```
canonical: claude -p --help — pasted live run above (executed-unit),
`claude --version` = `2.1.241` this session; no standalone
`--append-system-prompt-file`/`--system-prompt-file` flag is listed (the
`[-file]` bracket is a mutual-exclusivity group label on the
`--append-system-prompt` help line, not a separate flag) — matches the
record's own claim that this CLI lacks the `-file` variant the issue's
cited docs name.

```
$ git show issue-2204/implementation:pipeline.py | grep -n "exclude-dynamic-system-prompt-sections\|ENABLE_PROMPT_CACHING_1H"
           "--exclude-dynamic-system-prompt-sections"]
           "ENABLE_PROMPT_CACHING_1H": "1",
```
canonical: git show issue-2204/implementation:pipeline.py — pasted live
grep above (executed-unit); both added unconditionally, corroborated by
§5's live `cache_read_input_tokens` reading.

## 11. REQ-8, REQ-10 — static inspection (candidate Absent)

```
$ git ls-files | grep -i "^CLAUDE.md$"
$ ls .claude/rules/ 2>&1
ls: cannot access '.claude/rules/': No such file or directory
$ git diff origin/main...issue-2204/implementation -- CLAUDE.md .claude/rules/
```
canonical: the three commands and their pasted output directly above —
executed-unit, this session; no `CLAUDE.md`, no `.claude/rules/`, either
before or after this PR's diff.

```
$ git show issue-2204/implementation:docs/issue-2204/reports/implementation/deviation-log.md
- 2026-08-24T00:00:00Z | filed | tokenmaxxxer-core's directive.sh SessionStart hook (a separate git repository) still tells every spawned session to Read session-protocol.md before its first task action ...
```
canonical: git show issue-2204/implementation:docs/issue-2204/reports/implementation/deviation-log.md
— pasted live run above (executed-unit); its one entry is REQ-1's
cross-repo gap (§4), not REQ-8 or REQ-10.

```
$ git show issue-2204/implementation:docs/issue-2204/reports/consult-log.md
```
canonical: git show issue-2204/implementation:docs/issue-2204/reports/consult-log.md
— read in full this session; a single skill-selection consult entry, no
mention of REQ-8 or REQ-10.

```
$ git show issue-2204/implementation:spawn.py | grep -n "^def directive_section_files"
def directive_section_files(*, skills_mounted: bool = False,
```
canonical: git show issue-2204/implementation:spawn.py — pasted live
grep above (executed-unit); the function's own signature carries no
path/task-shape parameter, so no per-task-shape decomposition exists to
select a subset.

REQ-8 candidate verdict: Absent — failing clause per verdict-assignment
rule 5: `## Fix` bullet 1's second clause ("repo conventions to
CLAUDE.md/`.claude/rules/`"); no file, no rationale anywhere in the
record/deviation-log/consult-log for the omission.
canonical: the three citation blocks in this section, combined.

REQ-10 candidate verdict: Absent — failing clause: `## Fix` bullet 2 in
full ("Decompose the monolithic contract into path-scoped rule fragments
so a docs-only task loads only what it needs"); the shipped fix still
selects a fixed file bundle by `skills_mounted`/`checkpoint` flags only.
canonical: the `directive_section_files` grep in this section, combined
with §1's `git diff --stat`.

## 12. REQ-9, REQ-12 — candidate Present

```
$ git show issue-2204/implementation:docs/issue-2204/reports/implementation.md | grep -B2 -A2 "single-enforcement-surface"
```
canonical: git show issue-2204/implementation:docs/issue-2204/reports/implementation.md
— pasted live grep above (executed-unit); its "Upstream basis" section
cites `docs/decisions/2026-08-21-single-enforcement-surface.md` as a
frozen decision ruling out a `SessionStart` hook alternative for this
repo, stating this "forecloses that alternative during design," though
"moot for the fix actually shipped."

REQ-9 candidate verdict: Present — the bootstrap-computed content REQ-9
names (e.g. `_checkpoint_contract_block(issue, role)`, computed
per-spawn) is delivered zero-round-trip via the same
`--append-system-prompt` channel REQ-7 uses (§3's live run carries the
same delivery mechanism); the practical intent is satisfied through a
documented, decision-cited substitute channel, not a silent omission the
way REQ-8/REQ-10 are.
canonical: the grep pasted directly above this subsection, combined with
§3's live-run citation.

REQ-12 candidate verdict: Present, inapplicable in practice — no
`--bare` usage anywhere in the diff.
canonical: §1's `git diff --stat` output, which lists every changed
file; none is a `--bare`-related change.

## 13. Open findings surfaced during survey

1. REQ-1 does not hold end-to-end for a real spawned session — the
   larger Read-round-trip source (`tokenmaxxxer-core`'s `directive.sh`
   `SessionStart` hook) is untouched, outside this repo's write set, and
   freshly reproduced by this review session's own first tool call
   (§4). Already disclosed in the implementation record's own open
   findings; this survey adds independent, live corroboration.
   Resolution path: a companion issue against `tokenmaxxxer-core`
   (already named in the implementation record) to move `directive.sh`'s
   output to the `SessionStart`-hook `additionalContext` channel.
2. REQ-3 has no direct timed re-measurement in the record (§6) — only
   content-length parity and a trivial single-turn smoke call.
   Resolution path: a timed real docs-only issue spawn through
   spawn.py's actual pipeline, pre-fix vs. post-fix; out of this review's
   own write set to produce unilaterally.
3. REQ-8 and REQ-10, two of the six `## Fix` bullets, are not addressed
   and not acknowledged anywhere in the record, deviation log, or
   consult log (§11) — unlike REQ-9, which is at least cited against a
   frozen decision. Candidate verdict Absent for both. Resolution path:
   either a follow-up issue scoping the path-scoped `.claude/rules/`
   decomposition as its own unit of work, or an explicit statement of
   why they were judged out of scope.

## 14. Sampling scope

Full enumeration, not a sample: three commits (§0), two source files
plus three updated test files (§1), twelve requirement line items
derived from the issue's own `## Acceptance` (five bullets) and `## Fix`
(six bullets, one — `--bare` — folded to REQ-12) sections (§2).
canonical: §1's `git diff --stat` output and §2's requirement list, both
pasted above in this same document; small enough that spot-checking
would cost more setup than it saves. The
`conformance-review-sampling-derivation` skill is not invoked this
session (see the proposal's skill-verdict section for the
not-applicable reasoning).
