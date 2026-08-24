---
issue: 2164
role: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2164/reports/conformance-review/survey.md
    sha: e6e16007c1ac56797818365993abf6aa765c1ac0
  - path: docs/issue-2164/proposals/2026-08-24-conformance-review-issue-2164.md
    sha: e6e16007c1ac56797818365993abf6aa765c1ac0
subject: commit 3ea0ec889010a8aeed7caec795261618707ad4cb (consult.py, pipeline.py; landed on main via #2168)
test: issue #2164 "## Change"/"## Acceptance" text, decomposed into REQ-1..REQ-8 (docs/issue-2164/reports/conformance-review/survey.md §2)
result: cantTell
assertedBy: issue-2164/conformance-review session (role-handoff contract v3)
---

# issue-2164 — conformance-review record

## What was done

canonical: `git show 3ea0ec88 --stat` (survey §1) — this session's read
of the commit's own changed-file list; `gh issue view 2164` (read this
session) for the issue's own "Sweep finding"/"## Change"/"##
Acceptance" text the survey's REQ-1..REQ-8 split (survey §2) traces
back to.

Audited commit `3ea0ec88` (issue #2164's own delivery, landed on `main`
via #2168) against the eight requirement line items the survey (§2)
extracted: the `룰북`→스킬-저장소 가이던스 rename across `consult.py`'s
docstrings and LLM-facing prompt strings, the `pipeline.py:215`
dangling-`plugin_dirs()` reference fix, the untouched
`runs/rulebooks/tokenmaxxxer-core` exclusion, the grep-based zero-hit
acceptance check, the meaning-unchanged constraint, and the test-suite
acceptance bullet.

The per-requirement verdicts are in the Findings section below. Six of
eight requirements verify `Present`. REQ-7 (the test-suite acceptance
bullet) also verifies `Present`, on the strength of a parent-commit
before/after comparison that separates this diff's own regressions from
pre-existing ones (see REQ-7's block). REQ-8 (the implementation
record's own executed-acceptance-evidence claim) verifies `Surface`,
which per the role spec's worst-case recomputation rule
(`roles/specs/conformance-review.spec.json` `recomputation.rule`) drives
this record's frontmatter `result` down from the fully-conforming
baseline to `cantTell`. Three open findings are carried into this
record from the survey; none of them implicate `3ea0ec88`'s own
content.

## Why

The verdicts below render the approved proposal
(`docs/issue-2164/proposals/2026-08-24-conformance-review-issue-2164.md`)
without re-derivation — method and evidence were already fixed during
phase 1's survey, and phase 2's job is to instantiate those decisions as
per-requirement finding blocks in this role's own record file, not to
re-litigate them.

canonical: `git show 3ea0ec88 -- consult.py pipeline.py` (survey §5,
test-re-execution section) — the method choices this paragraph
describes.

Two choices carry over from the proposal's Rationale, unchanged: test
evidence was independently re-executed rather than taken on trust from
the implementation record's own pasted output (this is what surfaced
REQ-8's discrepancy in the first place); and a regression judgment used
a parent-commit `d9a1e826` before/after comparison rather than "any
failure observed during review fails the acceptance bullet," which
would have wrongly blamed `3ea0ec88` for two pre-existing failures.

## Findings

---
requirement: `consult.py` docstrings renamed off `룰북` at lines 432,
  438-439 (REQ-1)
spec_ref: issue #2164 body, sweep-finding paragraph, bullet
  "docstrings: lines 432, 438-439"
verdict: Present
canonical: `grep -n "스킬-저장소 가이던스" consult.py pipeline.py`
  (survey §3, first grep fence) — both docstring lines carry the
  renamed term
evidence: `3ea0ec88:consult.py:432`, `3ea0ec88:consult.py:438`
rationale: the grep fence lists exactly the two docstring lines the
  issue names, each carrying the renamed term; a companion
  `grep -rn '룰북' consult.py pipeline.py` fence in the same survey
  section shows zero `consult.py` hits, so no unrenamed instance
  survives at these lines.

---
requirement: `consult.py` LLM-facing prompt strings renamed off `룰북`
  at lines 467, 475, 586, 874, 937-938, 1093 (REQ-2)
spec_ref: issue #2164 body, sweep-finding paragraph, bullet "LLM-facing
  PROMPT TEXT sent to spawned judge/panel/consult sessions ... lines
  467, 475, 586, 874, 937-938, 1093"
verdict: Present
canonical: `grep -n "스킬-저장소 가이던스" consult.py pipeline.py`
  (survey §3, first grep fence) — all seven cited lines carry the
  renamed term
evidence: `3ea0ec88:consult.py:467`, `3ea0ec88:consult.py:475`,
  `3ea0ec88:consult.py:586`, `3ea0ec88:consult.py:874`,
  `3ea0ec88:consult.py:937`, `3ea0ec88:consult.py:1093`
rationale: every line the issue names by number appears in the grep
  fence's output with the renamed term substituted in place; REQ-6's
  diff-read shows no wording beyond the term itself changed at these
  sites.

---
requirement: `pipeline.py:215`'s `role_settings()` docstring dangling
  `plugin_dirs()` reference fixed to name what the code actually calls
  (REQ-3)
spec_ref: issue #2164 body, sweep-finding paragraph, third bullet, plus
  "## Change" bullet 2
verdict: Present
canonical: `grep -rn "^def plugin_dirs" . --include=*.py` (survey §3) —
  zero matches anywhere in the repo, so the pre-fix name was dangling by
  construction
evidence: `3ea0ec88:pipeline.py:215`
rationale: the exact site the issue names no longer references the
  nonexistent function name — the docstring now reads "...
  (`spawn_cmd()` 의 plugins/core_plugins/skill_dirs 참고)" (survey §3,
  quoted fence) — and the replacement names real call targets that do
  exist in this codebase.

---
requirement: `runs/rulebooks/tokenmaxxxer-core` and other core-plugin-
  bundle paths/strings left untouched by this commit (REQ-4)
spec_ref: issue #2164 body, "## Change", exclusion sentence ("Do not
  touch runs/rulebooks/tokenmaxxxer-core or any other core-plugin-bundle
  path/string")
verdict: Present
canonical: `git show 3ea0ec88 --stat` (survey §1) — the commit's full
  changed-file list
evidence: `3ea0ec88:consult.py:1`, `3ea0ec88:pipeline.py:1`
rationale: the commit's four changed paths are `consult.py`,
  `pipeline.py`, `docs/issue-2164/reports/implementation.md`, and
  `docs/issue-2164/reports/implementation/deviation-log.md` — zero paths
  under the excluded `runs/rulebooks/tokenmaxxxer-core` tree or any
  other core-plugin-bundle path.

---
requirement: "`grep -rn '룰북' consult.py pipeline.py` returns zero hits
  (or only hits inside a comment explicitly about the retired
  path/history, judged case by case)" (REQ-5)
spec_ref: issue #2164 body, "## Acceptance", first bullet
verdict: Present
canonical: `grep -rn '룰북' consult.py pipeline.py` (survey §3, second
  `룰북` grep fence) — zero `consult.py` hits, three `pipeline.py` hits
evidence: `3ea0ec88:pipeline.py:380`, `3ea0ec88:pipeline.py:659`,
  `3ea0ec88:pipeline.py:661`
rationale: the three surviving `pipeline.py` hits are each a comment
  describing the `runs/rulebooks/tokenmaxxxer-core` clone or its gates
  ("로컬 체크아웃이 없으면 룰북과 같은 길", "룰북 게이트는 core 공유
  라이브러리를", "룰북 클론 내부를 가리켜") — the exact carve-out the
  acceptance bullet itself states.

---
requirement: no prompt string's meaning changes, only its terminology
  (REQ-6)
spec_ref: issue #2164 body, "## Acceptance", second bullet, first
  clause
verdict: Present
canonical: `git show 3ea0ec88 -- consult.py pipeline.py` (survey §4) —
  full diff read this session
evidence: `3ea0ec88:consult.py:432` (representative hunk; all ten
  renamed sites share the same shape, survey §4)
rationale: every hunk in the diff swaps exactly one term (`룰북`→
  `스킬-저장소 가이던스`, or `룰북/훅`→`스킬-저장소 가이던스/훅`) with
  identical surrounding wording, punctuation, and sentence boundary on
  both sides of the swap across all ten renamed sites. Analysis method
  per `conformance-review-verification-method-selection` rule 2 —
  demonstrating "meaning unchanged" via a live judge/panel session would
  be disproportionate to a same-line terminology diff, and the diff
  text itself is the evidence.

---
requirement: every existing consult/judge/panel-related test still
  runs clean against this commit (REQ-7)
spec_ref: issue #2164 body, "## Acceptance", second bullet, second
  clause
verdict: Present
canonical: `pytest tests/test_consult_trace_root.py
  tests/test_spawn_consult_panel.py tests/test_spawn_judge.py
  gates/test_consult_gate_lib_env.py gates/test_consult_verdict_parsing.py
  gates/test_consult_siblings.py gates/test_requirement_intake_consult.py
  gates/test_consult_json_parse.py gates/test_design_research_consult.py
  harness/fixture-concurrent-judgment/test_panel.py -q` (survey §5,
  batched re-run) — zero failures across all nine files
  (`3ea0ec88:tests/test_consult_trace_root.py:1`).
evidence: `pytest tests/test_spawn_pipeline.py -q` (survey §5,
  `3ea0ec88:tests/test_spawn_pipeline.py:1`) — 2 failed, 77 clean;
  `git checkout d9a1e826 -- consult.py pipeline.py && pytest
  tests/test_spawn_pipeline.py -k
  "test_unset_output_reflects_builtin_default or
  test_role_model_unset_uses_builtin_default" -q` (survey §5,
  `d9a1e826:tests/test_spawn_pipeline.py:1`) — the identical
  `'haiku' != 'sonnet'` failure reproduces on the parent commit,
  byte-for-byte
rationale: independent standalone re-execution of every consult/judge/
  panel-named test file, run live this review session rather than taken
  on trust from the implementation record, shows every file clean
  except `tests/test_spawn_pipeline.py`'s two `DryRunModelReflection`/
  `SpawnCmd` cases. Checking out `consult.py`/`pipeline.py` at the
  parent commit `d9a1e826` and re-running those same two cases
  reproduces the identical failure byte-for-byte, proving it predates
  `3ea0ec88` and is unrelated to its `룰북`-rename diff — REQ-7 concerns
  tests broken by this commit, and independent re-execution finds none.

---
requirement: executed acceptance evidence present in the implementation
  record (REQ-8)
spec_ref: issue #2164 body, "## Acceptance", third bullet
verdict: Surface
canonical: the implementation record's own pasted transcript (survey
  §5, quoted at top of that section,
  `3ea0ec88:docs/issue-2164/reports/implementation.md:1`) claims `183
  passed, 4 xfailed in 134.50s`, zero failures shown for
  `tests/test_spawn_pipeline.py`; `pytest tests/test_spawn_pipeline.py
  -q` (survey §5, `3ea0ec88:tests/test_spawn_pipeline.py:1`, this
  session's independent standalone re-run) shows 2 failed, 77 clean
evidence: `3ea0ec88:docs/issue-2164/reports/implementation.md:1`,
  `3ea0ec88:tests/test_spawn_pipeline.py:1`
rationale: the record's evidence block has the right shape — a pasted
  command plus a pasted summary line, this repo's verify-at-landing
  convention — but the specific zero-failure claim it makes for
  `tests/test_spawn_pipeline.py` does not, on independent replay,
  reproduce in this session. REQ-7's parent-commit comparison shows the
  two failures are pre-existing, so they do not indict `3ea0ec88`'s own
  content, but this one file's evidence in the implementation record is
  present in form without being independently reproducible in substance
  as written — what `Surface` names rather than `Present` (fully
  reproduced) or `Incorrect` (the claim is not fabricated; a clean run
  plausibly occurred in that session's own environment, per Open finding
  2 below).

## Upstream basis

- `docs/issue-2164/reports/conformance-review/survey.md`, sha
  `e6e16007c1ac56797818365993abf6aa765c1ac0` — the requirement
  extraction (§2), static inspection (§3), semantic-equivalence check
  (§4), independent test re-execution (§5), and the three open findings
  (§6) this record's Findings and Open findings sections cite directly.
- `docs/issue-2164/proposals/2026-08-24-conformance-review-issue-2164.md`,
  sha `e6e16007c1ac56797818365993abf6aa765c1ac0` — the phase-1 proposal
  this record instantiates. The `APPROVE issue-2164/conformance-review`
  issue comment (posted by `JiwonJung94`, listed in
  `docs/specs/approvers.md`) opened this phase.
- commit `3ea0ec889010a8aeed7caec795261618707ad4cb` — the audited
  subject itself, landed on `main` via #2168.

## Open findings

1. **Residual dangling `plugin_dirs()` reference at `pipeline.py:451`,
   outside REQ-3's literal scope.** `core_plugin_dirs()`'s own docstring
   at `pipeline.py:451` still reads "... 확장(`plugin_dirs()`)과 달리
   ..." — the same dangling-name pattern fixed at `pipeline.py:215` and
   `consult.py:438`, but issue #2164 named only `pipeline.py:215` for
   this fix, with no repo-wide sweep obligation for this bug class
   (canonical: `grep -n "plugin_dirs" pipeline.py consult.py`, survey
   §3). Not a conformance failure of `3ea0ec88` against its own issue
   text. Resolution path: candidate for a follow-up issue naming
   `pipeline.py:451` explicitly.
2. **The implementation record's pasted `tests/test_spawn_pipeline.py`
   evidence does not independently reproduce in this review session**
   (REQ-8 above; survey §5-6). The two failures are proven pre-existing
   via the parent-commit comparison, so `3ea0ec88` is not at fault, but
   REQ-8's `Surface` verdict stands because the record's own
   zero-failure claim for this one file does not, on independent
   replay, hold. Resolution path: re-run `tests/test_spawn_pipeline.py`
   in the implementation session's own environment (or a clean CI run)
   to determine whether this is session-state drift or test-order
   dependence — neither of which blocks #2164 itself.
3. **This review session's own environment denies executing two classes
   of command** (survey §6, third finding): the implementation record's
   original 10-file combined `pytest` invocation, and any invocation of
   `test/test_spawn_skill_judge_haiku_timeout_overlap.py`, both via this
   session's `pretooluse-dispatcher.sh` approval-gate hook, which denies
   by default when its own `gh --json state_reason` query fails against
   the installed `gh` CLI's unrecognized field name (canonical: the
   denial text quoted verbatim in survey §6, encountered live,
   repeatedly, this session). An environment defect, not a
   `consult.py`/`pipeline.py` content defect. Resolution path: fix the
   hook's `gh` invocation to a field name (or version check) the
   installed CLI recognizes, so a phase-state read failure does not
   silently widen into denying unrelated command classes.

## Next steps

None needed from this role or branch — `loop_state` above is already
this record kind's terminal value, `reported`
(`roles/specs/conformance-review.spec.json` `loop_state.terminal`). The
three open findings above name their own resolution paths for whoever
picks them up next: a follow-up issue for finding 1, a re-run in a
different environment for finding 2, a hook fix for finding 3.

## What did not work

Nothing, for this phase-2 write itself — the record above instantiates
the approved proposal's already-decided verdicts and evidence without
deviation. (Phase 1's after-proposal warrant-hunter dispatch never
converged in that earlier session — logged separately at
`docs/issue-2164/reports/conformance-review/deviation-log.md`, sha
`ddc69ed4d581a041cf27f02e2d687d57ae0658ae` — but that is a phase-1
event, not a divergence from this phase-2 record's own plan.)

## Skill verdicts

skill-verdict: conformance-review-finding-record — applied: invoked;
its field list (`requirement`/`spec_ref`/`verdict`/`evidence`/
`rationale`) shaped every block in the Findings section above, one per
REQ-1..REQ-8, each carrying an evidence pointer and a `spec_ref` per the
skill's own refusal rule.

skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; every evidence citation above pins a `sha:path:line` triple
(rule 1), `consult.py` and `pipeline.py` are cited as separate
contributing files for REQ-1/REQ-2 vs REQ-3 rather than bundled (rule
2), and REQ-1..REQ-8 were each backward-traced to a named issue-#2164
clause in the survey before evidence was gathered (rule 3; carried
forward from survey §2).

other mounted skills: not triggered — requirement-extraction,
verification-method-selection, verdict-assignment, sampling-derivation,
and severity-classification were invoked in the phase-1 session
(proposal skill-verdicts section) to produce the already-approved
requirement list, method choices, and verdicts this phase-2 record
instantiates; this session did not re-invoke them, since re-deriving
already-approved decisions is what "instantiate the approved proposal"
rules out.
