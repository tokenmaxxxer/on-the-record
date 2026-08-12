# Current-state survey (issue #983)

## Write surfaces

- `on-the-record/hooks/directive.sh` — orchestrator-only UserPromptSubmit
  hook (`CLAUDE_ROLE` unset gate, line 12) that injects the #803 deviation
  loop paragraph. Role sessions never see this text.
- `on-the-record/hooks/deviation-log-guard.sh` — Stop hook enforcing the
  no-traceless-deviation invariant. Line 29
  (`[ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }`) makes it a
  no-op whenever `CLAUDE_ROLE` is set, i.e. it never binds in a role
  session — the exact gap #754/#983 name.
- `on-the-record/hooks/hooks.json` — registers `directive.sh` in
  `UserPromptSubmit` and `deviation-log-guard.sh` in `Stop`. A role-scoped
  directive needs its own `UserPromptSubmit` registration alongside the
  existing `record-tiering-directive.sh` / `record-claim-shape-directive.sh`
  entries, which already follow the "role-audience, `CLAUDE_ROLE` set"
  pattern this issue needs.
- `on-the-record/hooks/test_deviation_log_guard.py` — has
  `t_claude_role_set_is_noop` (repo-relative line ~96) asserting the
  guard is silent when `CLAUDE_ROLE` is set; this assertion is the
  encoded form of the bug and must invert once the guard binds for role
  sessions too.
- `docs/handbooks/deviation-loop.md` — reference doc for the entry
  format; states the loop nests inside `directive.sh`'s orchestrator
  paragraph only. Needs a role-session subsection once a role variant
  ships.

## Existing role-audience directive pattern

`record-tiering-directive.sh` and `record-claim-shape-directive.sh` are
both `UserPromptSubmit` hooks gated the opposite way from `directive.sh`:
`[ -n "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }` — fires only for a
spawned role session, silent for the orchestrator. This is the template
to reuse for a role-scoped deviation directive rather than inventing a
new gating convention.

## Guard mechanics reusable as-is

`deviation-log-guard.sh`'s branch-to-path resolution (regex
`^issue-(\d+)/([\w-]+)$`, mapping to a per-issue reports path when it
matches and a top-level reports path otherwise) already matches a role
session's own branch name (`issue-<n>/<role>`, e.g. this session's
`issue-983/implementation`) with no change needed — the guard's marker
scan and git-diff check are role-agnostic. The only defect is the early
`CLAUDE_ROLE` exit at line 29.

## Constraint the role variant must respect

Role sessions cannot spawn peer roles or open issues unilaterally
mid-task (role-handoff contract v3's `SCOPE-EXCEEDED RULE`: when a role
hits work outside its frozen write set, it finishes what the proposal
covers, STOPS, and reports — never widens scope, never spawns another
role mid-build). So a role session's FILE-AS-ISSUE branch cannot mirror
the orchestrator's `spawn.py spawn` call literally; it must resolve to
the existing scope-exceeded stop-and-report behavior, with the
deviation-log entry recording that the deviation was surfaced for the
orchestrator/next role to pick up rather than spawned directly.

## Alternatives considered while surveying

1. Make `directive.sh` itself emit the deviation-loop paragraph
   regardless of `CLAUDE_ROLE` (drop the whole-file orchestrator gate).
   Rejected: `directive.sh`'s other paragraphs (issue drafting, role
   spawning, board reading) are orchestrator-only by design; a role
   session must not see instructions to spawn other roles or draft
   issues on its own initiative — that would blur the phase-1/phase-2
   contract this very issue depends on.
2. Add a role-session branch inside `deviation-log-guard.sh` alone,
   without ever telling the role session about the loop via a directive.
   Rejected: the guard is a Stop-time backstop; a role session that never
   receives the RECOGNIZE/CLASSIFY/RESOLVE steering has no way to comply
   with it proactively — matches the audit's own framing ("bind" means
   directive + guard together, not the guard alone).
