---
issue: 2479
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: on-the-record/hooks/record-claim-guard.sh
    sha: 28c776d929b6efe5541cd1729f3b60b5c0dacea4
  - path: on-the-record/hooks/heredoc-command-refusal-gate.sh
    sha: 28c776d929b6efe5541cd1729f3b60b5c0dacea4
  - path: directive_assembly.py
    sha: same-commit
code_under_review:
  - directive_assembly.py
  - tests/test_directive_diet_2135.py
  - docs/handbooks/spawn-directive-assembly.md
type: docs
breaking: none
verdict: pass
---

# issue-2479 — implementation record

## What was done

Added a new always-on directive section, `hook-contract.md`, to the
role-session spawn-time directive assembled in `directive_assembly.py`:

- `_HOOK_CONTRACT_PROSE` (new constant, `directive_assembly.py`) states
  the exact passing shape plus one worked example each for
  `record-claim-guard.sh` and `heredoc-command-refusal-gate.sh`.
- `directive_section_files()` now includes `"hook-contract.md":
  _HOOK_CONTRACT_PROSE` unconditionally, in the same always-materialized
  tier as `completion-and-landing.md`/`repo-discovery.md`/
  `turn-budget.md` — both gates apply to every role (record-claim-guard.sh
  on any `docs/issue-*/reports/**` write, heredoc-command-refusal-gate.sh
  on any role-session commit/PR Bash call), so there is no narrower scope
  condition to gate it on.
- Because every file in `directive_section_files()`'s return value is
  already joined into `--append-system-prompt` by
  `_directive_system_prompt_block()` (issue #2204's existing mechanism),
  the new section reaches a spawned role session's context at turn 1 with
  no code change needed beyond adding the dict entry.
- Updated `tests/test_directive_diet_2135.py::SectionFileMapping::
  test_skill_and_checkpoint_sections_are_conditional`'s exact-set
  assertion to include `hook-contract.md` (the only existing test
  asserting the always-on file set as an exact set).
- Documented the change in `docs/handbooks/spawn-directive-assembly.md`
  under a new "Gate passing-shape contract (issue #2479)" section, per
  that file's existing per-issue-section convention.

## Why

The issue text (`gh issue view 2479`) reports that a conformance-review
role session (issue-2379) opened its phase-1 PR successfully, then hit
`record-claim-guard.sh` and `heredoc-command-refusal-gate.sh` refusals
back-to-back on a follow-up commit and ended `progressed-dirty-tree` —
unable to close out its own commit — which a watchdog then treated as a
dead session and respawned from scratch.

Both gates' refusal messages are deny-only and fire only after a write
is attempted; up to now, a role session had no way to know either gate's
passing shape before that first attempt. Neither gate's own refusal
logic changes here — this only tells the passing shape earlier, in the
same "verbatim from the enforcing source, delivered up front" pattern
`directive_assembly.py` already uses for the `--single-phase`
build-now-bypass contract line (`_SINGLE_PHASE_CONTRACT_LINE`, mirrored
verbatim from `tokenmaxxxer-core`'s `directive.sh`).

### Acceptance check 1 — baseline reproduction (before)

Reproduced both gates' refusal on a first attempt, directly against the
gate scripts as they exist at this branch's base commit
(`28c776d929b6efe5541cd1729f3b60b5c0dacea4`), independent of any session
harness:

`record-claim-guard.sh`'s underlying checks (`gates/record_lint.py`),
run against a naive OUTCOME claim with no executed-live citation, via
`record_lint.unverifiable_reason_check`, `checked_claim_reason_check`,
`bare_count_claim_check`, `canonical_source_claim_check`,
`outcome_claim_citation_check`, `orphaned_path_reference_check`,
`git_tracked_path_reference_check`, `defect_claim_grounding_check`, on
the fixture string below:

```
input: "Requirement met: all 3 acceptance checks pass, based on the PR review.\n"

$ python3 <checker script calling the eight record_lint functions above>
BAD: 레코드에 실행-근거 없는 OUTCOME 주장 (issue #870): 'Requirement met: all 3 acceptance checks pass, based on the PR review.' — ...
count: 1
```

`heredoc-command-refusal-gate.sh`, run directly against a heredoc-shaped
`git commit` payload:

```
$ HCRG_PAYLOAD=<heredoc-shaped git commit payload> bash on-the-record/hooks/heredoc-command-refusal-gate.sh
heredoc-command-refusal-gate: heredoc-shaped commit message body detected — the host's write-capable-command classifier refuses this shape as un-analyzable. Use two -m flags instead of a heredoc: git commit -m "<title line>" -m "<body line>" (one -m per paragraph; never a heredoc/$(cat <<EOF ...) body) — issue #1976.
rc=2
```

Separately, this session's own first attempt to construct that same
heredoc-shaped test payload inline in a Bash command (rather than via a
file) was itself denied by the live, installed
`heredoc-command-refusal-gate.sh` PreToolUse hook — an unplanned, fully
live instance of the exact gate this issue is about, on the very first
relevant write attempt this session made.

### Acceptance check 2 — after adding the directive text (after)

With `_HOOK_CONTRACT_PROSE` added, re-ran both gates against the shapes
the new directive text's worked examples specify:

`record-claim-guard.sh`'s checks (same eight functions as above) against
the directive's own worked record-claim example:

```
input:
  canonical: `gh pr view 2471` output (state: OPEN)
  Acceptance requirement met — checked: `python3 -m pytest tests/test_x.py` — result: 12 passed

$ python3 <same checker script>
count: 0
```

`heredoc-command-refusal-gate.sh` against the directive's worked commit
example (`git commit -m "issue-2479: add gate passing-shape to spawn
directive" -m "fixes progressed-dirty-tree stall from undocumented gate
shape"`):

```
$ HCRG_PAYLOAD=<two -m flags, no heredoc> bash on-the-record/hooks/heredoc-command-refusal-gate.sh
rc=0
```

Both worked examples clear their respective gate with zero denials
(`count: 0` / `rc=0` above); neither gate's own deny logic was
touched — `on-the-record/hooks/record-claim-guard.sh`
and `on-the-record/hooks/heredoc-command-refusal-gate.sh` are unchanged
by this PR's diff (`code_under_review` above lists only the directive
files actually touched).

### Acceptance check 3 — was the gates' own refusal-message detail sufficient to self-correct from?

In isolation: yes, for both gates. `heredoc-command-refusal-gate.sh`'s
denial message literally states the sanctioned two-`-m`/`--body-file`
alternative (quoted verbatim in the baseline transcript above);
`record-claim-guard.sh`'s per-check denial strings (`gates/record_lint.py`,
e.g. `outcome_claim_citation_check`'s "통과하려면 같은 섹션 안에 실행-라이브
canonical:/derived: 태그 ... 두면 된다") name the exact fix, not just the
violation.

What the messages don't cover is the compounding case the issue #2479
incident actually hit: two independent gates firing back-to-back on the
same landing step, with no message referencing the other and no
guaranteed runway to run a full fix-and-retry cycle twice right as a
session is trying to finish. That is a narrower, distinct gap from "the
session never knew the shape at all" (this issue's scope) — not filed as
a new GitHub issue by this session (role sessions are refused by
`gh-guard` from creating issues — contract v3 s8/s9, "issues are the
user's requirement backlog, user-authored only"; reproduced live:
`gh issue create` from this session was denied with exactly that
message). Naming it here for the orchestrator/user to file: **follow-up
— "record-claim-guard.sh / heredoc-command-refusal-gate.sh refusal
messages don't cover compounding back-to-back hits near end-of-session"**
(see `## Open findings` below for the drafted body). Deviation logged:
`docs/issue-2479/reports/implementation/deviation-log/20260826T011402145329-89f7f09e0aae5ebc.md`.

### Acceptance check 4 — should `progressed-dirty-tree` be reclassified by watchdog?

`progressed-dirty-tree` is already a distinct, non-`errored` outcome
value in spawn.py's own end-of-session classification (`board.py`'s
`fail_closed_downgrade`; `spawn.py`'s `LANDED_OUTCOMES = {"progressed",
"progressed-dirty-tree"}`), and `gates/recovery_policy.py::classify()`
already returns `RESPAWN_WITH_HANDOFF` (not a blind identical respawn)
whenever `has_commit` is true. Whether watchdog's *live* dead-entry
detection path (`watchdog.py`'s dead-but-registered/deadlock heuristics)
actually consults those same signals for a session that died mid-gate-
refusal-retry rather than exiting cleanly through that self-report path
is a separate question this session did not verify — tracing that is a
distinct mechanism change to `watchdog.py`/`lifecycle.py`, not a
directive-text change, so it stays out of this issue's scope per its own
acceptance check 4 instruction. Naming it here for the orchestrator/user
to file: **follow-up — "watchdog: verify/fix whether the live dead-entry
path recognizes a progressed-dirty-tree-shaped end state before
respawning from scratch"** (see `## Open findings` below).

## What did not work

None.

## Upstream basis

`on-the-record/hooks/record-claim-guard.sh` and
`on-the-record/hooks/heredoc-command-refusal-gate.sh` (both pre-existing,
unchanged by this PR, sha `28c776d929b6efe5541cd1729f3b60b5c0dacea4`) are
the two gates whose passing shape this issue documents. `gates/record_lint.py`
(same sha) is the module `record-claim-guard.sh` calls into for its
citation checks; its check functions' docstrings are what
`_HOOK_CONTRACT_PROSE`'s rule list is hand-condensed from. `directive_assembly.py`
(this commit) is where the new section is defined and wired into
`directive_section_files()`.

## Open findings

1. Follow-up (not filed as a GitHub issue by this session — see
   Acceptance check 3 above): the two gates' refusal messages don't
   reference each other when both patterns are present in the same
   intended landing step, and there's no measured guarantee of runway
   for a session to fix-and-retry twice right before it would otherwise
   end. Drafted body: `/tmp/otr-2479-followup-a.md` (this session's
   scratch path, not committed — the orchestrator/user files the actual
   issue from the summary in Acceptance check 3 above).
2. Follow-up (same reason, not filed): watchdog's live dead-entry
   detection path was not verified to consult the same has-commit/has-PR/
   dirty-tree signals `gates/recovery_policy.py::classify()` already
   uses, for a session that died mid-gate-refusal-retry rather than
   exiting cleanly. Drafted body: `/tmp/otr-2479-followup-b.md` (same
   caveat as above).

## Skill verdicts

skill-verdict: work-in-english — applied: invoked; kept the new
`_HOOK_CONTRACT_PROSE` directive text in Korean, matching this file's
existing neighboring constants (`_COMPLETION_PROSE`, `_TURN_BUDGET_PROSE`,
`_REPO_DISCOVERY_PROSE`, `_KNOWN_PATHS_PROSE` are all Korean) per the
skill's project-convention-conflict edge case, while writing this record,
the PR title/body, and commit messages in English.
other mounted skills (implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice,
implementation-blueprint): not triggered — this change is a single
dict-entry-plus-constant addition inside an established, already-frozen
directive-assembly pattern, with no coupling/cohesion, GoF-pattern, data-
structure, or multi-module structural decision in it.

## Next steps

None — `loop_state: landed`, both acceptance-demonstration checks ran
live (before/after above), and both scope-boundary questions are
answered explicitly per the issue's acceptance criteria.
