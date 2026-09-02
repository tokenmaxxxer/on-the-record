---
issue: 3042
role: implementation-audit+silent-failure-audit+conformance-review-verdict-assignment+defect-verification-independence-from-upstream-verdicts-0d4eb553
author: implementation-audit+silent-failure-audit+conformance-review-verdict-assignment+defect-verification-independence-from-upstream-verdicts-0d4eb553
skills: implementation-audit (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), conformance-review-verdict-assignment (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: (none — no prior docs/issue-3042/ artifact exists; this record is the first)
    sha: same-commit
---

# issue-3042 — implementation-audit+silent-failure-audit+conformance-review-verdict-assignment+defect-verification-independence-from-upstream-verdicts-0d4eb553 record

## What was done

derived: the seven per-mechanism `canonical:`/`derived:` command+output
transcripts under "Mechanism 1" through "Mechanism 7" below, all captured
live in this same record during this session.

Report only, per issue #3042's "must not" clause — no mechanism audited below
was changed. Seven skill-layer mechanisms named in the issue's Scope were each: (1)
traced to a source-of-truth citation, (2) actually executed against this checkout
(not read-only inference from source), (3) assigned one of Present / Surface /
Absent / Incorrect / Unverifiable per `conformance-review-verdict-assignment`'s
rules, and (4) checked for whether a failure of the mechanism announces itself
or is silently absorbed as success, per `silent-failure-audit`'s
Handled/Silently-Absorbed distinction. Execution was independent per mechanism
(seven separate execution rounds, one per mechanism, each re-deriving its own
evidence rather than citing the parent issue's problem-statement claims) — the
parent issue's own claims about `skill_judge` and about `cross_family` timing
were themselves treated as testable hypotheses, not settled facts, per
`defect-verification-independence-from-upstream-verdicts` rule 1.

skill-verdict: implementation-audit — applied: invoked; used the P/S/A/I/U
taxonomy and the "depth-check a Present claim for edge/error handling" rule to
require every mechanism verdict below to cite executed command+output evidence,
not a reading of source alone
skill-verdict: silent-failure-audit — applied: invoked; used the
Handled/Silently-Absorbed/Unreachable classification to derive the
self-announcing-vs-silent field for every row, in particular the two
enforcement-hook rows (skill-verdict obligation, invoke-before-apply) where
detection exists but enforcement is silent
skill-verdict: conformance-review-verdict-assignment — applied: invoked; used
rule 2 (Incorrect vs Absent — code exists but contradicts the spec) to assign
Incorrect to `cross_family` and to invoke-before-apply, rule 5 (name the
failing clause) on every non-Present row, and rule 3 (Unverifiable names the
missing evidence location, never a favorable/unfavorable guess) on the
directive-payload row
skill-verdict: defect-verification-independence-from-upstream-verdicts —
applied: invoked; re-derived the parent issue's own `skill_judge`
indistinguishability claim and 87%-bootstrap-cost claim live instead of citing
them, per rule 1 and rule 6 — the `skill_judge` claim did not survive
re-derivation (see Mechanism 3 below)

### Mechanism 1: skill resolution from `--skills` (unknown-name and symlinked-source paths)

**Claimed behavior** (source: `docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md:20-116`, `skills.py:302-417`)
`resolved_skill_sources()` resolves each `--skills` name across four sources
(skill-repository checkout, installed plugins, `~/.claude/skills`, target-repo
`.claude/skills`) before any workspace/branch mutation (`spawn.py:3900-3903`).
An unknown name is a hard fail-closed `sys.exit` naming the requested skill
plus the full candidate list (`skills.py:384-388`). A name matching in ≥2
sources is normally a fail-closed collision naming every source
(`skills.py:402-408`) — except when every match's `SKILL.md` content is
byte-identical (e.g. `~/.claude/skills` symlinked to the same physical
directory as the skill-repo checkout), in which case
`_collapse_identical_matches()` (`skills.py:273-286`) merges them into one
match and resolution proceeds with no error.

**Observed behavior**

canonical: `python3 -m pytest test/test_spawn_skills_mount.py -v -k "Symlink or nowhere_found or ambiguity"`
```
SymlinkCollapseAndSourceQualifierTest::test_symlinked_duplicate_is_not_a_collision PASSED
SymlinkCollapseAndSourceQualifierTest::test_genuinely_different_content_still_refuses PASSED
ResolvedSkillSourcesFourTierTest::test_nowhere_found_fails_closed PASSED
ResolvedSkillSourcesFourTierTest::test_ambiguity_repo_and_plugin_hard_error_names_both PASSED
16 passed in 0.91s
```

canonical: `python3 -c "import spawn; spawn.resolved_skill_sources('adversarial-review', spawn._skill_repo_root(), home=Path.home(), target_repo_root=Path('.'))"` — run against this sandbox's real, pre-existing environment where `~/.claude/skills` is an actual symlink to `/home/jwjung/skill-registry/skills` (the same directory `MUSTER_SKILL_REGISTRY_ROOT` points at) — i.e. a live instance of the symlinked-source case, not a synthetic fixture
```
VALID/SYMLINKED RESULT: [{"source": "skill-repo", "dir": ".../skill-registry/skills/adversarial-review",
  "sha": "c05de12", "name": "adversarial-review"}]
```
One match returned (not a collision error) — a physical symlink collision resolves cleanly.

canonical: `python3 -c "import spawn; spawn.resolved_skill_sources('this-skill-does-not-exist-bogus-xyz-789', ...)"`
```
SystemExit: --skills: 모르는 스킬 this-skill-does-not-exist-bogus-xyz-789 — skill-repository, 설치된
플러그인, ~/.claude/skills, 타깃 저장소 .claude/skills 어디에도 없다 — 쓸 수 있는 이름: accessibility-aria-and-contrast-rules,
adversarial-review, ... work-in-english
```
Non-zero `SystemExit`, unknown name plus the full candidate list — matches the fail-closed contract.

Note: a full `python3 spawn.py --skills <name> "..." --issue 999999 --dry-run` CLI-level attempt was tried for both a valid and an unknown name and produced byte-identical output for both (an unrelated admission gate — issue-requirement-linkage via `gh api`, which fails first because this sandbox has no real GitHub-backed issue #999999 — short-circuits before `resolved_skill_sources()` is ever reached), so it is not usable evidence for this mechanism; the direct function-level calls above are the narrowest correct read-only exercise of the resolution code itself.

**Verdict**: Present

**Self-announcing or silent**: Split by sub-path, both matching spec intent. The
unknown-name path is self-announcing — non-zero `SystemExit` naming the
offending name and the full candidate list, always before any
workspace/branch creation. The symlinked-duplicate collapse is silent by
design — no log/print statement exists anywhere around
`_collapse_identical_matches()` — but this is not a defect: the spec frames
this case as "not a collision," so no announcement is expected, and the
resolved-source roster still records exactly one provenance row either way.

### Mechanism 2: `cross_family` add-only mounting at spawn time

**Claimed behavior** (source: `docs/issue-2001/proposals/task-aware-cross-family-skill-selection.md:29-30,86-87`)
"Family set (`_ROLE_SKILLS`) is never reduced — add-only... No-match path must
be byte-identical to today." Candidate discovery is scoped to "every candidate
skill directory... whose name is not in `_ROLE_SKILLS.get(role, [])`."

**Observed behavior**

canonical: `grep -n "_ROLE_SKILLS" *.py`
```
(5 hits, all comments, zero definitions — e.g. pipeline.py:1442 "이슈 #2507:
`_ROLE_SKILLS[role]` exclusion 은 없앴다")
```
`_ROLE_SKILLS` does not exist in this checkout; the spec's own cited anchor
(`spawn.py:5068-5112`) now holds unrelated ledger/completion-notification
code, not a role→skill table.

The add-only *merge* step itself, `merge_composed_skill_source()`
(`skills.py:529-541`), is genuinely add-only and non-destructive:
```python
seen = {d.name for d in skill_source["skill_dirs"]}
merged_dirs = list(skill_source["skill_dirs"]) + [
    d for d in matched_dirs if d.name not in seen]
```
No removal path exists here or at its caller (`spawn.py:4308`).

But the candidate-*exclusion* half of "add-only" (never re-offering a skill
already in the role's baseline) is gone: `_cross_family_candidate_corpus()`
(`pipeline.py:1423-1481`) excludes only one static policy skill
(`skills.py:440`, `{'work-in-english'}`), confirmed live and failing:

canonical: `python3 -m pytest test/test_spawn_cross_family_skill_selection.py -v -o addopts=''`
```
Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate FAILED
AssertionError: Lists differ: [PosixPath('.../implementation-blueprint')] != []
...
6 failed, 17 passed in 0.45s
```
Among the 6 failures are both of the spec's own mandated live acceptance
tests (`docs/issue-2001/proposals/task-aware-cross-family-skill-selection.md:179-183`):
`SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive`
and `...test_non_matching_task_mounts_and_directive_byte_identical_to_baseline`
— both fail before reaching cross-family logic, inside branch checkout
(`pipeline.py:1060` → `pipeline.py:856`), which now hard-requires a real
`origin` git remote the test fixture never configures — a fixture/harness
drift, not evidence for or against the cross-family logic itself, but it does
mean the spec's own acceptance gate cannot currently execute to completion in
this checkout.

`--dry-run` cannot observe `cross_family` at all — reading `spawn.py:2874-2911`
shows the dry-run branch returns after `skill_settings()` and never reaches
`_spawn_one()`'s `cross_family` timed block (`spawn.py:4288`). A live
wall-clock re-measurement of the issue's "17.9s of 20.6s (87%)" claim would
require a real network spawn (git fetch + `gh issue view` + a launched
session) — out of scope for a read-only, no-network audit round, so that
number could not be re-derived this session. `spawn.py:768-773` and
`spawn.py:4285-4292` (bootstrap timing grew from 7 to 16 instrumented phases,
and the `skill_judge` consult future is now dispatched before
workspace/branch setup, with `cross_family` only joining an already-running
future) are circumstantial evidence the original 87% figure reflects a
structurally different, likely smaller, measurement point today — but this is
not a re-derived number and is reported only as a lead, not a finding.

**Verdict**: Incorrect

**Failing clause**: `docs/issue-2001/proposals/task-aware-cross-family-skill-selection.md:29-30,86-87` — the family-exclusion clause of "add-only" no longer holds: `_ROLE_SKILLS` was deleted repo-wide (issue #2507/#2610), the candidate pool now excludes only one static policy skill instead of the role's baseline family, and the test written to enforce the original clause fails with a concrete repro (`test/test_spawn_cross_family_skill_selection.py:82-93`). The merge step itself is correctly add-only; the exclusion half of the same "add-only" contract is not.

**Self-announcing or silent**: Silent for a reader of the spec doc — `docs/issue-2001/proposals/task-aware-cross-family-skill-selection.md` was never updated to reflect the #2507 removal of `_ROLE_SKILLS`, so it still asserts an invariant the code no longer honors. Partially self-announcing for a code reader — `pipeline.py:1442-1446`'s own comment is explicit about the removal — and fully self-announcing for anyone who runs the mandated test file, which fails loudly (`6 failed`) rather than silently succeeding or being skipped.

**Consumer-reaching or repo-local**: repo-local — this affects which skills get mounted into a spawned session's directive/plugin-dir, an internal orchestration decision; it does not leak past `spawn.py`'s own bootstrap into an external consumer-facing surface.

### Mechanism 3: `skill_judge` selection, abstention path, timeout/fail-open path

**Claimed behavior** (source: `consult.py:527-546`, `consult.py:703-711`, `consult.py:855-931`)
`_skill_judge_consult()` returns `(picked_paths, {"picked":[...], "rejected":[...], "reasons":{}})` on success — abstention is `picked=[]` with populated `rejected`/`reasons`. On parse-failure/timeout/non-zero-exit it raises instead of returning, so the caller fail-opens to a BM25 fallback. The caller (`_cross_family_skill_matches_with_consult()`, consult.py:703-711) and `rank_skills()` (consult.py:855-931) both tag every result with an explicit `outcome` ∈ {`completed`, `fail-open`, `no-candidates`}, documented as never collapsing fail-open into something a caller could mistake for abstention.

**Observed behavior**

canonical: `python3 spawn.py --skill-candidates "please write a haiku about the ocean waves at sunset" -C . --with-judge`
```
"outcome": "completed", "picked": []
```
Backing trace: `outcome='ok: picked=[] rejected=[parallel-decomposition=Task is
writing a single haiku, not parallel agent coordination...; ...'`

canonical: `SKILL_JUDGE_TIMEOUT=0.001 python3 spawn.py --skill-candidates "please write a haiku about the ocean waves at sunset" -C . --with-judge`
```
"outcome": "fail-open", "picked": ["parallel-decomposition", "api-design-versioning-evolution"]
```
Backing trace: `outcome='error: 시간초과(0.001s)'`

canonical: `python3 spawn.py --skill-candidates "our checkout latency suddenly doubled last week and I need to figure out the root cause..." -C . --with-judge`
```
"outcome": "completed", "picked": ["diagnose-first"]
```

Per-spawn ledger side (not just the CLI preview): `spawn.py:3875` initializes
`skill_judge_outcome = "not-run"`, `spawn.py:5074` writes the real outcome
into every spawn's `ledger_write()` record, independently asserted by
`test/test_spawn_skill_judge_haiku_timeout_overlap.py:376,382,410`.

derived: `python3 -m pytest test/test_spawn_skill_judge_haiku_timeout_overlap.py -v` → `4 failed, 14 passed`. All 4 failures share one root cause unrelated to the outcome-tagging logic: `spawn.py:4116` calls `_checkout_named_branch` directly, but the tests mock a different, no-longer-called wrapper, so the real function runs unmocked and dies on `git fetch --prune origin` against a fixture repo with no `origin` remote — a stale-mock/test-drift bug in the harness, not evidence against `skill_judge_outcome` itself.

Disclosure: reproducing the abstain/fail-open cases required real `--with-judge` invocations, which (per `consult.py:552-560`'s own documented side effects) wrote consult-trace files under `docs/reports/consult-log/` — an unavoidable, documented side effect of executing this mechanism as the issue instructs, not a change to the mechanism.

**Verdict**: Present

**Self-announcing or silent**: Distinguishable at every layer inspected — the
raw exception vs. return from `_skill_judge_consult()`, the `outcome` string
in both the CLI JSON and the ledger's `skill_judge_outcome` field. Abstention
(`outcome="completed"`, `picked=[]`, populated `rejected`/`reasons`) and
failure (`outcome="fail-open"`, `picked=<BM25 names>`, trace shows a
timeout/error message) carry different, explicit tags, and no caller in this
codebase keys off bare `picked` emptiness instead of `outcome`. This directly
contradicts the parent issue's own problem-statement claim that these two
states are "indistinguishable at the call site" — re-derivation live, rather
than deferring to that claim (`defect-verification-independence-from-upstream-verdicts` rule 1 and rule 6), shows the claim does not hold against the current source.

### Mechanism 4: `--skill-candidates` with/without `--with-judge`, k=2 vs k=5 divergence

**Claimed behavior** (source: `consult.py:828-833`, `spawn.py:658-661`, `spawn.py:3910-3916`, `on-the-record/directive/spawn-and-board.md:33-36`)
`consult.rank_skills(..., k: int = 2)` is what `--skill-candidates` calls
(spawn.py:2515-2521, no override, so `k=2` applies to the judge-refinement
slot count). Spawn's real mount inside `_spawn_one()` calls the same
underlying function with `k=_COMPOSED_SKILLS_TOPK = 5` (spawn.py:661,3915).
`on-the-record/directive/spawn-and-board.md:33-36` names this exact gap:
"this preview asks for `k=2` candidates by default while spawn's own internal
mount asks for `k=5`... not a byte-identical result to what spawn would
actually mount."

**Observed behavior**

canonical: `python3 spawn.py --skill-candidates "Audit the error handling paths in spawn.py for silently swallowed exceptions" --issue 3042`
```
"ranked": [{"name": "silent-failure-audit", "score": 17.61...}, ...201 entries...],
"outcome": "bm25-only", "picked": []
```
derived: `python3 -c "import json,sys; print(len(json.load(sys.stdin)['ranked']))"` on the above → `201` (the full corpus is scored; only `picked` is k-bounded, not the display).

Controlled repro isolating the `k` parameter, calling the production function
directly with a stubbed judge that accepts every offered candidate up to
`max_picks`:
```
k=2: ['silent-failure-audit', 'merge-gates']
k=5: ['silent-failure-audit', 'merge-gates', 'parallel-decomposition',
      'technical-writing-minimalism-scoping', 'refactoring-legacy-characterization-test-scope']
```
Same task text, same BM25 order, same judge — only the `k` argument differs —
and the real mount path admits 3 more skills than `--skill-candidates
--with-judge` would ever report as `picked`.

derived: `python3 -m pytest tests/test_skill_candidates_floor.py tests/test_skill_candidates_signal.py tests/test_skill_candidates_false_positive_rate.py test/test_skill_candidates_ranking.py -v` → `30 passed, 2 warnings` (warnings are an unrelated, self-reported `pinned-fixture-divergence (issue #3019)` notice, not a failure).

**Verdict**: Present

**Self-announcing or silent**: Silent at the tool/runtime level. Neither
`--help` text nor either JSON payload nor the stderr progress line mentions
`k`, `2`, `5`, or `_COMPOSED_SKILLS_TOPK` — an operator who only runs the
command has no way to learn from the tool itself that the judge-preview slot
count differs from the real mount's slot count. The divergence is disclosed
exactly once, in `on-the-record/directive/spawn-and-board.md`'s prose, not
emitted by the code path it describes.

**Consumer-reaching or repo-local**: N/A — verdict is Present (mechanism
matches its documented behavior); noted anyway as a candidate observability
gap in Open findings below.

### Mechanism 5: per-skill verdict obligation in records

**Claimed behavior** (source: `on-the-record/gates/record_lint.py:548-600,603-629`, `on-the-record/hooks/skill-verdict-guard.sh:29,212-222`)
For every skill actually invoked via the Skill tool this session (issue
#2153 narrowed this from "every mounted skill"), the record must carry a
`skill-verdict: <name> — applied: ... | not-applicable: ...` line, and an
`applied:` line must start with `invoked;` (issue #2062). When mounted skills
exist but none were invoked, the record must carry `other mounted skills: not
triggered` (issue #2893). Both are wired into the session's Stop hook. Per the
hook's own header comment: violations surface only via
`hookSpecificOutput.additionalContext`, never `decision: "block"`.

**Observed behavior**

canonical: `MUSTER_SKILLS="silent-failure-audit" HOME=<fixture> bash on-the-record/hooks/skill-verdict-guard.sh < payload_b.json` (record entirely lacks the skill-verdict line for an invoked skill)
```
EXIT:0
stdout: {"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext":
"skill-verdict-guard: ... 마운트된 스킬에 skill-verdict 줄이 없다 (issue #2039): 'silent-failure-audit' ..."}}
```

canonical: `MUSTER_SKILLS="silent-failure-audit,another-mounted-skill" HOME=<fixture> bash on-the-record/hooks/skill-verdict-guard.sh < payload_c.json` (2 mounted skills, zero invocations, no summary line)
```
EXIT:0
stdout: {"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext":
"skill-verdict-guard: zero-invocation (issue #2681) -- ... 요약 줄이 없다 (issue #2893) ..."}}
```

canonical: `python3 -m pytest test/test_skill_verdict_guard_zero_invocation_signal.py -v` → `7 passed in 0.88s` (includes an assertion that `"decision"` is never in the hook's parsed JSON output).

derived: `grep -rn "record_skill_verdicts_in" --include="*.py" .` → only its own definition at `gates/record_lint.py:632` / `on-the-record/gates/record_lint.py:632`; no caller in `gates/ci.py`. `grep -n "skill.verdict\|skill_verdict\|MUSTER_SKILLS" gates/ci.py` → no matches. The CI/merge-time path that lands PRs never runs any skill-verdict check; the Stop hook is the obligation's only live caller.

**Verdict**: Surface

**Failing clause**: `on-the-record/hooks/skill-verdict-guard.sh:29,326` — the hook correctly detects both violation shapes (missing per-skill line, missing zero-invocation summary line) but reports them exclusively through `additionalContext`, never blocking. A session can end with the required line missing and the hook exits 0. Separately, `record_skill_verdicts_in` (`gates/record_lint.py:632-654`) claims in its own docstring to be used by both `gates/ci.py` and the Stop hook, but has zero actual callers in `gates/ci.py` — no merge-time gate re-derives the obligation independently of the advisory Stop hook.

**Self-announcing or silent**: Detection is self-announcing (specific, correctly-named violation text, in the same channel session logs surface). Enforcement is silent: nothing stops the record from being written, committed, or merged with the violation present — the check never blocks at Stop time and is never re-checked at merge time.

**Consumer-reaching or repo-local**: repo-local — the violation surfaces only inside the producing session's own transcript/Stop-hook output; it never reaches a durable, cross-session artifact a downstream consumer of the merged record would see.

### Mechanism 6: invoke-before-apply obligation in the spawn directive

**Claimed behavior** (source: `directive_assembly.py:421-450`)
A skill judged applicable to the task must be loaded via the Skill tool
before being applied (issue #2062); only not-applicable skills are exempt.
The `applied:` line's free text must start with `invoked;` as "evidence that
the Skill tool was actually called" (`directive_assembly.py:448`).

**Observed behavior**

canonical: `grep -rln "Skill tool\|tool_name.*Skill\|SkillInvocation\|skill-verdict" gates/ on-the-record/gates/ on-the-record/hooks/`
```
gates/record_lint.py, gates/merge_gate.py, on-the-record/gates/record_lint.py,
on-the-record/hooks/skill-verdict-guard.sh, on-the-record/hooks/hooks.json,
on-the-record/hooks/hook_classification.json, on-the-record/hooks/fail-open-wrapper.sh,
on-the-record/hooks/report-framing-check.sh, on-the-record/hooks/test_heredoc_failure_bails.py
```
`on-the-record/hooks/skill-verdict-guard.sh:117-153` (`invoked_skill_names`)
does do a real transcript cross-check — it scans the session transcript for
`tool_use` blocks named `"Skill"` and collects the real invoked names,
intersected with the mounted set. That real, transcript-derived `invoked`
list is passed to `gates/record_lint.py`'s `skill_verdict_reason_check`
(`skill-verdict-guard.sh:314`).

But `skill_verdict_reason_check` (`gates/record_lint.py:548-600`) only checks
the required direction: for each transcript-proven-invoked name, does a
`skill-verdict:` line exist with an `invoked;`-prefixed `applied:` text
(shape only — "never judging the marker's truth", line 562-566). It never
checks the converse: whether an `applied: invoked; ...` line for a name *not*
in the transcript-proven set is false.

Synthetic repro — canonical: `python3 -c "..."` simulating a session that
mounted `conformance-review-verdict-assignment`, never actually called the
Skill tool (`invoked = []` from the transcript scan), but wrote a record
falsely claiming `applied: invoked; ...` for it, alongside the required
zero-invocation summary line:
```
zero_invocation_summary_check violations: []
skill_verdict_reason_check(text, invoked=[]) violations: []
=> record accepted (no violations) despite the invoked; line being FALSE: True
```
Both checks return an empty violation list — the false `invoked;` claim is
accepted.

canonical: `grep -n "invoked\|Skill\|transcript" on-the-record/hooks/record-claim-guard.sh` → no output — that hook performs no invocation/transcript cross-referencing at all.

canonical: `grep -n "record_skill_verdicts_in\|transcript" gates/merge_gate.py gates/ci.py` → no output — per `gates/record_lint.py:632-638`'s own docstring ("CI has no transcript to read it from"), no CI/merge-time caller ever invokes the transcript-aware check either.

**Verdict**: Incorrect

**Failing clause**: `directive_assembly.py:436-450` (and `gates/record_lint.py:562-566`) promise the `invoked;` marker is evidence the Skill tool was actually called — but the one mechanical check that does read the real transcript (`skill-verdict-guard.sh`'s `invoked_skill_names`) uses that evidence only to compute which names *require* a line, never to reject a line whose target the transcript proves was *not* invoked. A false `applied: invoked; ...` claim for a mounted-but-never-called skill is mechanically indistinguishable from a true one in every branch tested.

**Self-announcing or silent**: Silent. A session that writes `applied: invoked; ...` for a skill it never ran through the Skill tool produces zero violations, zero blocked exit codes, and zero `additionalContext` warnings — nothing downstream re-examines the claim, even though the transcript evidence that would refute it is already being read for a different purpose in the same hook invocation.

**Consumer-reaching or repo-local**: repo-local — the gap lives entirely inside this repo's own session-integrity tooling; it affects the trustworthiness of this project's own audit records, not an external consumer/API surface.

### Mechanism 7: skill-related directive payload assembled at spawn

**Claimed behavior** (source: `directive_assembly.py:463-502`, `spawn.py:4269-4360`, `spawn.py:4436-4439`)
`directive_section_files()` attaches `skill-obligations.md` only if skills are
mounted. `spawn.py` conditionally adds a `mounted-skills` block naming
`--skills` entries, a `role-skill-triggers` block for skill-repository
composed skills with provenance tags, and a `skill-obligations` block
restating the two obligations above. Every real spawn prints
`composition_breakdown(_directive_parts)` (`directive_assembly.py:708-714`) to
stderr — a per-label byte breakdown, built as "이슈 #2135's measure-first
instrument."

**Observed behavior**

canonical: `grep -n "composition_breakdown\|mounted-skills\|role-skill-triggers\|skill-obligations" spawn.py directive_assembly.py` — confirmed the instrument and all three injection points exist at the cited lines (spot-checked by reading each site).

canonical (execution attempt): a harness invoking `spawn._spawn_one(..., skills='silent-failure-audit,implementation-audit', issue=3042)` with `issue_workspace`/`_skill_repo_root`/`spawn_cmd` mocked, spying on `composition_breakdown`'s input
```
[implementation] returned-pr 게이트(백그라운드) 0.000s 만에 끝남 (걸린 PR 0개)
SYSEXIT 브랜치 체크아웃: fetch 실패 — fatal: 'origin' does not appear to be a git repository
[implementation] skill_judge 자문 완료 — 2개 선택
NO_PARTS_CAPTURED — assembly never reached composition_breakdown()
```
The harness reached real skill resolution and a real `skill_judge` consult
(2 skills picked from the live skill-repository) but hit a `SystemExit` inside
branch checkout on an unmocked internal `git fetch` before reaching
`_spawn_one()`'s `composition_breakdown()` call site. The remaining git
dependency was not patched and re-run within this session's turn budget.

derived: none produced — the byte counts (3,909B of 7,261B, ~53.8%, from the
issue's problem statement) were not independently re-derived this session,
and are not restated here as fact.

**Verdict**: Unverifiable

**Failing clause**: The quantitative claim (skill payload ≈53.8% of the total
directive) could not be independently re-derived: execution reached skill
resolution but crashed before `composition_breakdown()` (`spawn.py:4438`) on
an unmocked git-fetch dependency inside branch checkout. The code paths that
would produce the number are confirmed present and wired to run on every
spawn (`spawn.py:4269-4360,4436-4439`), but no fresh byte count was obtained
to compare against the issue's figures — the missing evidence location is
specifically "a completed, non-network `_spawn_one()` run (or an isolated
`composition_breakdown()` call) with the branch-checkout git dependency
mocked out."

**Self-announcing or silent**: Partially self-announcing by design —
`spawn.py:4438` prints a per-source byte breakdown to stderr on every real
spawn, which is exactly the instrumentation that would let an operator notice
a bloated/duplicated skill payload. But the print is stderr-only, descriptive
(no threshold, no alert, no gate) — a spawn producing a >50%-skill-payload
directive prints the fact but nothing stops, warns loudly, or fails the spawn
over it, and if the byte split were wrong (stale/duplicated content) the
instrument would show it in the numbers but nothing downstream reacts.

**Consumer-reaching or repo-local**: consumer-reaching — every `--skills`
spawn into every consumer repo goes through this same `_spawn_one()`
task-assembly path and the same `--append-system-prompt` injection, so any
bloat or incorrectness in the skill-related portion inflates every spawned
session's bootstrap context budget across all consumer repos, not just this
one.

## Why

derived: the seven `canonical:`/`derived:` transcripts under Mechanisms 1-7
above, all produced by this session's own live execution.

The parent issue's problem statement itself demonstrates why execution beats
source-reading: it names three cases where a symptom pointed the wrong
direction (a ranker believed to have a defect that it did not have; a
`skill_judge` `picked=[]` believed ambiguous between abstention and failure; a
`cross_family` timing cost believed to dominate bootstrap). Rather than
auditing each mechanism from its own comments and docs, each of the seven
mechanisms was assigned to an independent execution round that re-derived its
own evidence against the live checkout — including, per
`defect-verification-independence-from-upstream-verdicts`, re-testing the
parent issue's own claims rather than carrying them forward. That produced a
mixed and asymmetric result set (2 Incorrect, 1 Surface, 1 Unverifiable, 3
Present) rather than a uniform outcome in either direction — which is itself
evidence the independence discipline held, since a systematically biased
execution round would tend to skew toward one verdict rather than split this
way.

## Upstream basis

No prior `docs/issue-3042/` artifact exists — this is the first record for
this issue. The concrete inputs are the seven source files/handbooks/tests
cited per-mechanism above (`skills.py`, `pipeline.py`, `consult.py`,
`spawn.py`, `directive_assembly.py`, `gates/record_lint.py`,
`on-the-record/hooks/skill-verdict-guard.sh`, `on-the-record/directive/spawn-and-board.md`,
`docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md`,
`docs/issue-2001/proposals/task-aware-cross-family-skill-selection.md`) plus
the parent issue's own problem statement, whose `skill_judge` and
`cross_family`-timing claims were re-tested rather than cited (Mechanisms 2
and 3 above).

## Open findings

canonical: the seven per-mechanism `canonical:`/`derived:` transcripts above
(Mechanisms 1-7, this same record) — the items below name only what those
transcripts already established; no new claim is introduced here.

Defects found are named here with drafted bodies for the orchestrator to
file as separate issues.

1. **`cross_family` "add-only" no longer excludes the role's baseline family
   (Mechanism 2, Incorrect).** Drafted body: `docs/issue-2001/proposals/task-aware-cross-family-skill-selection.md`'s
   add-only contract still documents a `_ROLE_SKILLS`-based exclusion that
   was deleted in issue #2507/#2610; the candidate pool now excludes only one
   static policy skill (`work-in-english`), so cross-family ranking can
   re-offer a skill already in the caller's baseline. Repro:
   `python3 -m pytest test/test_spawn_cross_family_skill_selection.py::Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate -o addopts=''`
   fails with a concrete `Lists differ` assertion. Separately, the same test
   file's two mandated live acceptance tests error out during branch checkout
   because the test fixture never configures a git `origin` remote that
   `pipeline.py:856`'s `bootstrap_fetch_and_record_sha` now requires — a
   fixture/harness drift that should be fixed so the spec's own acceptance
   gate can execute again.

2. **Skill-verdict and invoke-before-apply obligations detect but never
   block or merge-gate (Mechanisms 5 and 6, Surface / Incorrect).** Drafted
   body: `on-the-record/hooks/skill-verdict-guard.sh` correctly detects a
   missing per-skill verdict line and a missing zero-invocation summary line,
   but reports both only via `additionalContext`, never `decision: "block"`,
   and `gates/record_lint.py`'s `record_skill_verdicts_in` (documented as
   used by `gates/ci.py`) has no actual caller there — so a violating record
   can reach the merged branch uncaught. Worse, the same hook already reads
   the real session transcript to compute which skills were actually invoked
   (`invoked_skill_names`, `skill-verdict-guard.sh:117-153`) but never uses
   that evidence to reject a record's `applied: invoked; ...` line for a
   skill the transcript proves was never called — demonstrated live: a
   synthetic record with a false `invoked;` claim and a matching
   zero-invocation summary line clears both `zero_invocation_summary_check`
   and `skill_verdict_reason_check` with zero violations returned by either.
   Fix should either (a) make the Stop hook block or add a `gates/ci.py`
   caller for `record_skill_verdicts_in`, or both, and (b) have
   `skill_verdict_reason_check` reject an `applied: invoked;` line whose
   target name is absent from the hook's own `invoked` list.

3. **`--skill-candidates` k=2 vs k=5 divergence is undisclosed at the tool
   level (Mechanism 4, Present-as-designed, observability gap only).**
   Drafted body: the preview tool's default judge-refinement slot count
   (`k=2`, `consult.py:833`) is 3 slots narrower than what a real spawn mounts
   (`k=5`, `spawn.py:661,3915`), and this is disclosed only in
   `on-the-record/directive/spawn-and-board.md`'s prose, not in `--help`
   text, the JSON payload, or the stderr progress line. Suggest either
   printing the active `k` value in the CLI's JSON output, or defaulting the
   preview to `k=5` to match the real mount unless a smaller preview is
   explicitly requested.

4. **Skill-related directive payload byte-share is unverified this session
   (Mechanism 7, Unverifiable).** Drafted body: the harness built to
   re-measure the issue's 3,909B/7,261B (~53.8%) claim crashed before
   reaching `composition_breakdown()` on an unmocked `git fetch` inside
   branch checkout. Recommend a follow-up attempt with that dependency
   mocked, or a `--dry-run` extension that reaches `composition_breakdown()`
   without a network-backed branch checkout, so this number can be
   re-derived without a live spawn.

5. **Correction to the parent issue's own problem statement (Mechanism 3,
   Present, not a defect to file).** Noted so the correction is not lost:
   the issue's claim that `skill_judge` `picked=[]` on abstention is
   "indistinguishable from a total selection failure at the call site" does
   not hold against current source or live reproduction. Every layer
   inspected (the raw consult return/exception, the `outcome` field, the
   ledger's `skill_judge_outcome`) tags abstention (`outcome="completed"`)
   and failure (`outcome="fail-open"`) with different, explicit values, and
   no caller in this codebase keys off bare `picked` emptiness instead of
   `outcome`.

## Next steps

None — `loop_state: landed`. The four numbered items above are drafted for
the orchestrator to file as issues per this issue's "Open findings"
convention; item 5 is a correction note, not a defect; no further action is
expected from this record itself.
