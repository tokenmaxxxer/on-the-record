# Current-state survey — conformance review of issue #2039's landed implementation

canonical: docs/issue-2039/reports/implementation.md (read this session)
canonical: gh issue view 2039 (read this session)
Issue #2039 was closed and merged via PR #2042 (phase-1) and PR #2049
(phase-2) on branch `issue-2039/implementation`, adding a
per-mounted-skill verdict obligation: any role record whose spawn
directive mounted N skills must carry N
`skill-verdict: <name> — applied: ... | not-applicable: ...` lines,
enforced by a new Stop hook plus a `gates/record_lint.py` canonical
check. This session's job is to conformance-review that landed work
against issue #2039's own Acceptance block, not to redo the
implementation.

## Acceptance block, decomposed into checkable requirements

canonical: gh issue view 2039 (read this session) — issue #2039's
`## Acceptance` block:

> check: a record write for a session whose directive mounted N skills
> is refused unless N skill-verdict lines are present (one per mounted
> skill, applied-or-NA with content after the dash); a session with zero
> mounted skills is byte-unaffected; the spawn directive states the
> obligation next to the mounted-skill list; hook tests cover
> missing-line, empty-reason, and zero-skill paths.

Decomposed into requirement IDs used through this review (labels only —
verdicts belong in the review record, not this survey):

- R1 — missing-line refusal: N mounted skills, fewer than N
  `skill-verdict:` lines present -> refused.
- R2 — empty-reason refusal: a `skill-verdict:` line present for a
  mounted name but with nothing after the dash -> refused.
- R3 — satisfied case: N mounted skills, N lines each with non-empty
  content after the dash -> not refused.
- R4 — zero-mounted-skill byte-inertness: a session with no mounted
  skills produces no hook output and requires no line.
- R5 — spawn-directive co-location: the obligation is stated in the
  spawn directive text, adjacent to the mounted-skill list itself.
- R6 — hook test coverage: hook tests exist covering missing-line,
  empty-reason, and zero-skill paths as executable tests, not just prose.

## Where each requirement's implementation lives (found this session)

canonical: gates/record_lint.py:385-415 (read this session)
R1/R2/R3 logic: `skill_verdict_reason_check` loops per mounted name;
appends a "no line" violation when a name is absent from the parsed
`found` dict, an "empty reason" violation when `found[name]` is empty
after strip. Consumed by `on-the-record/hooks/skill-verdict-guard.sh`
(Stop hook) and by `record_skill_verdicts_in`
(gates/record_lint.py:418-440), the CI/diff-scoped wrapper for
`gates/ci.py`.

canonical: gates/record_lint.py:394-395 and
on-the-record/hooks/skill-verdict-guard.sh (both read this session)
R4 logic: `skill_verdict_reason_check` returns an empty list
immediately when `mounted` is empty, and the hook exits 0 with no
stdout when its extracted `mounted` list is empty.

canonical: spawn.py:8197-8203 (read this session)
R5: the obligation line is appended immediately after the existing
#1960 스킬 점검 nudge, under the same mount-guard condition as that
nudge. This session's own invocation prompt (this conversation's task
message, the "스킬 점검(이슈 #1960)" paragraph followed by the
mounted-skill list) is a live instance of that same spawn-directive
text, so R5 held for this run's own dispatch.

canonical: derived: `ls on-the-record/hooks/test_skill_verdict_guard.py gates/test_record_lint.py tests/test_spawn_directive_assembly.py` (run this session, all three paths resolved)
R6: three tracked test files exist covering the three code sites (hook,
record_lint, spawn.py directive assembly).

canonical: python3 -m pytest -q on-the-record/hooks/test_skill_verdict_guard.py gates/test_record_lint.py tests/test_spawn_directive_assembly.py (run this session)
```
92 passed in 1.48s
```
Run live this session against the current working tree (not copied
from the implementation record's own pasted summary). The three test
files collect and execute together, exercising the
missing-line/empty-reason/zero-skill cases R6 requires
(`t_missing_skill_verdict_line_is_blocked`,
`t_empty_reason_skill_verdict_line_is_blocked`,
`t_zero_mounted_skills_is_noop` in
on-the-record/hooks/test_skill_verdict_guard.py, read this session).

## Supporting infrastructure checked

canonical: on-the-record/hooks/hooks.json:105 (read this session)
Registers `skill-verdict-guard.sh` in the `Stop` array immediately
after `deviation-log-guard.sh`.

canonical: docs/specs/enforcement-boundary.md:163 and
docs/specs/generated-paths.md:19 (both read this session)
Matching spec rows exist for the new hook.

canonical: python3 gates/spec_index.py (run this session)
```
통과: 모든 spec 문서가 기록된 해시와 일치한다
```
Run live this session against the current working tree; the two
`docs/specs/*` rows this PR touched are correctly reflected in
docs/specs/reconciled-index.md.

canonical: docs/handbooks/skill-verdict-obligation.md (read this
session)
Exists, states the line shape, referenced from the hook's refusal
message text.

canonical: derived: `grep -l "skill_verdict_reason_check\|record_skill_verdicts_in" gates/record_lint.py on-the-record/gates/record_lint.py` (run this session, both paths matched)
The tracked mirror `on-the-record/gates/record_lint.py` that the hook
imports at runtime (per the implementation record's "Rationale for
deviations" section) defines the same two functions as
`gates/record_lint.py`.

## What phase-2 of this review still needs to verify, not yet done here

- Whether the shape-only boundary is honored end-to-end — the hook and
  check never evaluate whether stated applied/not-applicable *content*
  is truthful, only that a non-empty line exists per name. Read from
  code this session; still needs an explicit per-requirement verdict
  line in the review record itself.
- Sampling scope for this review: `code_under_review:` in
  docs/issue-2039/reports/implementation.md lists a short write set —
  canonical: docs/issue-2039/reports/implementation.md (read this
  session) — full enumeration of every listed file is feasible rather
  than needing a sampling derivation.

## Skip-condition note (scout-directive)

Scouting (external field sweep) is skipped for this review. canonical:
gh issue view 2039 (read this session) — the task is
conformance-checking one already-landed, already-scoped implementation
against that issue's own Acceptance block. There is no open
external-facing design decision this review itself introduces — the
review method (inspection of code/tests against decomposed
requirements) is dictated by this role's own mounted skills, not by
external product exemplars. This matches the "spec leaves no design
decision open" skip condition.
