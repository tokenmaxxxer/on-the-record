---
status: proposed
files:
  - docs/issue-1130/reports/conformance-review.md
---

# Conformance-review proposal — issue-1130 role expertise realization (phase 1)

kind: proposal
subject: issue-1130

## Upstream / basis

canonical: `gh issue view 1130`, read directly this session. Merged
implementation: `docs/issue-1130/reports/implementation.md` (basis
`103130b`, `dbe8d53`). Proposal:
`docs/issue-1130/proposals/role-expertise-realization.md`. Survey:
`docs/issue-1130/reports/conformance-review/survey.md`.

## Requirement list (extracted, verdict deferred to phase 2)

1. **R1 — Scope restricted to #1129's cause-d/cause-b roles.** Source:
   issue body requirement 1 ("the roles the diagnosis issue (#1129)
   classifies as under-realized — not all 43 blindly"). Check: the
   landed write set touches exactly the 14 cause-d specs + 6 cause-b
   specs/hooks named in the proposal's frontmatter, no cause-a or
   cause-c role file.

2. **R2 — Five activities extended with named methodology/artifact-form
   and degree-level knowledge, sourced.** Source: issue body requirement
   2 ("each carry named canonical methodologies, artifact forms, and
   degree-level domain knowledge, with sources cited in the phase-1
   proposal ... no templating from memory"). Check: each of the 14
   in-scope specs carries non-empty `judgment_methodology`,
   `planning_methodology`, `deliverable_form`, `feedback_methodology`,
   `review_methodology` (each `{method, source}`), and a
   `degree_level_knowledge` array of `{concept, source}` entries with
   real, non-fabricated sources; the scout-brief's `## Sources` section
   backs each cited source with a verifiable text/URL.

3. **R3 — Gate-now-but-unwired invariants wired, hooks-only,
   default-on.** Source: issue body requirement 3 (accessibility,
   api-design, performance-engineering named explicitly). Check: each of
   the three has a new hook registered in `on-the-record/hooks/hooks.json`,
   fires by default (no opt-in flag required), and is a hook, not a
   spawn.

4. **R4 — Enforcement anchored to an arbitrary target project root.**
   Source: issue body requirement 4. Check: each of the three new
   gate-now guard scripts' file-pattern matching resolves against the
   tool-invocation's own `tool_input.file_path` (or an equivalent
   target-repo-relative signal), never against a path hardcoded to this
   repo's own layout.

5. **R5 — Spec/rulebook depth machine-checked for the five activities.**
   Source: Acceptance bullet 1's check clause ("extended spec-schema
   validation test in `gates/` asserts each in-scope role's spec names
   methodology+artifact-form entries for all five activities;
   `python3 -m pytest gates/ -q -k spec` exits 0"). Check: that exact
   command exits 0, and the passing set includes the five-activity
   assertions for all 14 in-scope specs (not merely pre-existing
   spec-schema tests happening to still pass).

6. **R6 — Empty-state (workload-never-triggers roles) explicitly listed
   as out of scope, not silently skipped.** Source: Acceptance bullet
   1's empty-state clause. Check: the spec-depth test or its
   surrounding documentation states which roles are out of scope and
   why, rather than the test's role list simply omitting them with no
   record.

7. **R7 — Unwired gate-now hooks each carry a refusal-case test.**
   Source: Acceptance bullet 2's check clause ("its hook appears in
   `on-the-record/hooks/hooks.json` and a gate test exercises one refusal
   case"). Check: `accessibility-guard.sh`, `api-version-guard.sh`,
   `perf-measurement-guard.sh` each have a corresponding
   `test_*_guard.py` that exercises at least one case where the hook
   denies.

8. **R8 — Empty-state for unwired-invariant wiring (spawn-only/
   directive-only rows untouched).** Source: Acceptance bullet 2's
   empty-state clause. Check: no role that `role-invariant-coverage.md`
   classifies spawn-only/directive-only gained a new default-on hook
   under this issue's write set.

9. **R9 — Cause-b routing-fix cluster: `record_absent_for` triggers
   wired to a merge/close-time consumer.** Source: not one of the
   issue's four numbered requirements verbatim, but the proposal's
   `## Constraints`/`## What will be done §3` frames it as the concrete
   fix for the same underlying gap requirement 3 targets (a role's own
   hook working but the role session never spawning). Check: each of the
   6 cause-b specs (secure-coding, test-authoring, issue-retrospective,
   release-engineering, interaction-design, ux-engineering) has a
   `trigger`/`record_absent_for` shape, and each of the 4 new routing
   hooks plus `merge-allow-gate.sh`'s secure-coding path has a
   refusal-case test in `test_routing_fix_spawn_checks.py` or an
   equivalent.

## What is out of scope for this review

- Cause-a and cause-c roles — issue #1130 itself excludes them (`gh
  issue view 1130`, requirement 1); this review does not check any
  cause-a/cause-c file for five-activity depth.
- Substance/quality grading of the cited methodologies beyond
  source-realness — the issue's own Acceptance block states quality is
  human PR review, not a mechanical check, and this role never renders a
  holistic quality judgment.
- Any fix to a finding — findings route to the owning role (architecture
  or implementation) per contract v3 s19 hand-off; this role only
  records verdicts.

## How you will know it worked (for phase 2)

Phase 2 renders one Present/Surface/Absent/Incorrect/Unverifiable
verdict per R1-R9 above, working from the artifact and spec only, and
records it in `docs/issue-1130/reports/conformance-review.md` per the
role's record format (code_under_review as a file list, one verdict
block per requirement, Open findings + resolution path for any non-Present
verdict).
