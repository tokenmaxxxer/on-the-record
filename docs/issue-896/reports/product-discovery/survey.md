# Current-state survey — issue-896

kind: current-state-survey
subject: issue-896
code_under_review:
- spawn.py
- roles/security-threat-model.json
- roles/secure-coding.json
- roles/test-authoring.json
- roles/performance-engineering.json
- roles/accessibility.json
- roles/risk-management.json
- roles/specs/security-threat-model.spec.json
- gates/role_spec_shape.py
- harness/driver.py
- harness/signals.py

## Background / context
Issue #896 is the coverage/activation half of "make the 43 roles real" (#807 is the methodology-quality half). #894 (open, unassigned — canonical: `gh issue view 894`, run this session) is a single instance of the same gap: this session landed several permission-broadening changes with no security-threat-model record even though the condition for that role plainly fired.

## Problem, stated without any solution attached (JTBD tuple)
- **Job performer**: the orchestrator session driving `spawn.py drive` (and, one layer up, the human operator relying on that session's role selection).
- **Job**: choose which specialist roles a change needs, correctly, every time.
- **Circumstance**: the orchestrator picks among 43 roles from issue text and its own judgment alone, under time/attention pressure, with no computed signal for which roles a given diff or landed spec currently calls for.
- **Desired outcome**: when a change's shape matches a role's stated trigger condition (a trust-boundary change, new untested code, a new interaction pattern, etc.), that role runs, or an explicit, attributable reason is on record for why it did not.

The issue text already names a solution shape (`spawn.py roles-due`, hard/soft gates). Restated in the performer's terms above, the underlying job is *trustworthy role coverage*, not any particular CLI subcommand — the evaluator/gate is one candidate solution, not the problem itself.

## Verified facts (this session, read live)
derived: `grep -l board_condition roles/specs/*.spec.json | wc -l` and `ls roles/specs/*.spec.json | wc -l`
```
$ grep -l board_condition roles/specs/*.spec.json | wc -l
43
$ ls roles/specs/*.spec.json | wc -l
43
```
- Every `roles/specs/*.spec.json` file carries a non-empty `use_when.board_condition` string — this is the machine-readable trigger. `roles/*.json`'s own `use_when` field is instead a Korean-language human-readable string with the condition folded into prose (checked for `security-threat-model`, `secure-coding`, `test-authoring`, `performance-engineering`, `accessibility`, `risk-management`), not machine-parseable on its own.
- canonical: `gates/role_spec_shape.py`, read this session (function body around line 85)
  `gates/role_spec_shape.py` validates that `use_when.board_condition` exists and is a non-empty string — a shape check only. It never reads a diff, a branch, or the board; it has no code path that evaluates whether a condition currently fires.
- canonical: `spawn.py`, read this session (role-listing branch near line 4345)
  When `spawn.py` is invoked with no role argument, it prints every role's `use_when` in one flat listing. This is the only place `use_when` reaches an operator, and it is undifferentiated — every role prints, fired or not, on every invocation.
- canonical: `spawn.py`, read this session (`board()` at line 1351, `status()` at line 1375)
  `board()`/`status()` read `docs/issue-<n>/reports/<role>.md` frontmatter and report `loop_state` per role that has a record, plus a list of roles with no record at all (`기록 없음: ...`). That "missing" list is unconditional — every role without a record, always — not conditioned on whether that role's trigger fired for this branch. It cannot distinguish "role never needed" from "role needed, never ran."
- canonical: `grep -rln board_condition gates/ hooks/`, run this session — only `gates/role_spec_shape.py` and its tests match; no gate or hook evaluates `board_condition` as a predicate against live diff/branch state.
- canonical: `gh issue view 894`, run this session — state OPEN, unassigned; no dedicated enforcement code exists for it beyond the same shape-only `role_spec_shape.py`.
- canonical: `harness/driver.py`, `harness/signals.py`, read this session — the harness instantiates a fixture target and captures a transcript/requirement text; `signals.py` holds signal-detection logic for the harness's existing checks. Neither file has a code path asserting which roles ran during a harness session.

## Opportunity-solution tree placement (OST, four-layer vocabulary)
- **Outcome**: role output is trustworthy — every landed change is reviewed by the specialists its own content calls for, not by whichever ~6 roles the orchestrator happens to default to.
- **Opportunity**: the orchestrator has no computed signal for which of the 43 roles a given branch/diff currently needs — the specific pain this issue targets, upstream of #894's single-role instance and sibling to #807 (role output quality once a role does run, orthogonal to whether it runs at all).
- **Candidate solutions** (not yet chosen; scored in the proposal): (a) a read-only `spawn.py roles-due` evaluator that surfaces fired-and-unrun roles to the orchestrator/board, no blocking; (b) the same evaluator plus a hard gate on a named subset of load-bearing roles, with an explicit N/A escape; (c) folding role-due computation into the existing `require_acceptance_gate`/`require_board` gate family in `spawn.py` rather than a new subcommand.
- **Discriminating assumption test**: run against a #776 harness scenario engineered to fire a specific role's board_condition (e.g. a trust-boundary-introducing spec) — does a `roles-due`-style evaluator report that role as due, and, for the hard-gated subset, does that harness scenario's session invoke that role before the scenario resolves? This is the acceptance-level test the issue itself specifies; the proposal states how the harness asserts it.

## Existing risk-of-over-blocking evidence (grounds the enforcement design)
- The `status()`/board "missing" list already shows every role without a record on every subject, unconditionally — a naive hard-gate-on-any-unfired-role design would multiply this noise across all 43 roles per subject, which is the over-blocking failure #896 explicitly warns against.
- canonical: `grep -rn "N/A\|waiver" roles/ gates/`, run this session — no structured escape/waiver field exists anywhere in `roles/` or `gates/`; an escape hatch is a net-new mechanism, not an extension of something present.
