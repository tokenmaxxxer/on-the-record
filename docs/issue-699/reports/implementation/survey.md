## Directive surface (hooks)

Registration file: `on-the-record/hooks/hooks.json`. All hooks below ship
with the plugin and are installed for every session that has
`on-the-record` enabled — there is no separate "role-only" plugin bundle.
What varies is whether an individual hook script no-ops early depending on
`CLAUDE_ROLE`.

| Event | Hook file | Reaches a plain (non-role) session? | What it does |
|---|---|---|---|
| SessionStart | `self-update.sh` | Yes (all sessions) | Refreshes the installed on-the-record checkout via git; silent/offline-safe. No role check. |
| UserPromptSubmit | `directive.sh` | **Yes — this is the one that matters.** Exits early only when `CLAUDE_ROLE` is set (see `on-the-record/hooks/directive.sh`, near the top: `[ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }`). | Injects the full "you are the orchestration session" directive text on every prompt in every plain session with the plugin installed: draft issues, spawn roles via `spawn.py`, read the board, never author deliverables yourself, turn-budget rules, reply-structure rules, pointer to `/orchestrate:run` for the full procedure. There is no lighter-weight variant of this text and no branch for "just consult a role's judgment." |
| PreToolUse (Bash) | `contract-guard.sh` | Yes (deny-only gate on `gh pr merge`) | Enforces contract v3 pre-merge checks (Closes-trailer, CI, closure sweep). |
| PreToolUse (Bash) | `pr-preflight.sh` | Yes | Deny-before-effect gate on `gh pr create`/`gh pr edit` body shape. |
| PreToolUse (Bash) | `claim-scan-preflight.sh` | Yes | Deny-only claim-scan (unevidenced count claims) on `gh pr create`/`edit`. |
| PreToolUse (Bash) | `spec-index-preflight.sh` | Yes | Deny-before-effect on `git commit` spec-index drift (`docs/specs/reconciled-index.md`). |
| PreToolUse (Bash) | `role-axis-completeness-guard.sh` | Yes | Deny-only `git commit` gate on `roles/*.json` axis-ownership completeness. |
| PreToolUse (Bash) | `impact-guard.sh` | Yes | Denies batched `gh pr merge` when a high-reversibility proposal is open in the batch. |
| PreToolUse (Bash) | `delegated-judgment-gate.sh` | Yes | Auto-approve/reject gate on `gh pr merge`/`gh issue reopen`/`gh issue close`/etc when a multi-role panel already reached unanimous consensus and the change is mechanically low-impact (issue #573). This is a merge-approval automation mechanism, not a mid-session "ask a role's judgment" mechanism — see the Delegation-norm section below. |
| PreToolUse (Write/Edit/MultiEdit) | `deliverable-guard.sh` | Yes, and specifically targets the orchestrator: comment says "In an orchestrator session (this plugin enabled, no CLAUDE_ROLE), deliverables are ROLE WORK" — denies writes to `src`, `test`, `tests`, `docs` trees in a target repo from a plain session. | Structural enforcement that a plain session must delegate deliverable *writes* to a spawned role — but only for the write act itself, not a judgment-point mid-conversation. |
| PreToolUse (Write/Edit/MultiEdit) | `record-claim-guard.sh`, `role-spec-reference-guard.sh`, `call-shape-guard.sh`, `accumulation-claim-guard.sh` | Path-scoped (e.g. `docs/issue-*/reports/`), no `CLAUDE_ROLE` early-exit visible in the header excerpts — fire in any session touching those paths. | Various write-time mirrors of `gates` CI checks (claim integrity, ref-resolution, call-shape divergence, accumulation cost). |
| PreToolUse (Write/Edit/MultiEdit) | `approval-gate.sh` | **No** — explicit early no-op: "No-ops immediately unless CLAUDE_ROLE is set... orchestrator-authored writes are deliverable-guard.sh's job, not this hook's." | Role-session-only: checks phase-2 approval state before a role writes its own record/src/test files. |
| PreToolUse/PostToolUse (Write/Edit/MultiEdit/Bash) | `retry-loop-bound.sh pre`/`post` | Yes (all sessions) | Bounds identical-denial retry loops per (tool, target) signature within a session. |
| Stop | `stop-gate.sh` | Header states this is orchestrator-scoped ("Stop: orchestrator-only structural check"). | Checks whether an approval-shaped reply names its issue, states a change, states risk. |
| Stop | `role-test-claim-guard.sh` | **No — role-session only.** Header: "Fires in ROLE sessions only (CLAUDE_ROLE set) — opposite of stop-gate.sh." | Checks a role's own test-run claims for skip/pass-claim mismatches. |
| Stop | `decision-queue-stopgate.sh` | Yes (reads `spawn.py flows --json`'s `decision_queue`) | Surfaces aged unresolved operator decisions; blocks the turn once an item ages past the hook's high-tier threshold. |
| Stop | `report-framing-check.sh` | Yes, but only fires on report-shaped replies (the run.md step-5 header or the Mission Board line shape) | Checks four framing elements (resolved problem, prior cost, newly possible, still broken) on PR/board report turns. |
| Stop | `product-capture-stopgate.sh` | Yes | Nudges the orchestrator to persist requirements/priorities/philosophy/goals mentioned in conversation into a per-issue product doc. A currently-open drift issue is noted in `docs/reports/2026-08-11-hunt-generated-path-disjointness.md`: this hook's write target moved to the issue-scoped path while `delegated-judgment-gate.sh`'s depth-axis reader was not updated to match, so that reader is reported as permanently unsatisfiable against the new location. |

**Summary of the ask ("which directives reach a plain session vs only
orchestrator/role sessions"):**
- Reaching every plain (non-role) session unconditionally: `self-update.sh`
  (SessionStart) and, critically, `directive.sh` (UserPromptSubmit) — the
  full orchestration directive is injected on every single prompt of a
  plain session unless `CLAUDE_ROLE` is set or `ORCHESTRATE_OFF` disables
  it.
- Reaching role sessions only: `approval-gate.sh` (PreToolUse write),
  `role-test-claim-guard.sh` (Stop).
- Reaching orchestrator-shaped replies only (Stop, content-triggered, not
  identity-gated): `stop-gate.sh`, `report-framing-check.sh`.
- Reaching both, path/content-gated rather than role-gated: the
  `gh`-verb PreToolUse gates (`contract-guard.sh`, `pr-preflight.sh`,
  `claim-scan-preflight.sh`, `impact-guard.sh`, `delegated-judgment-gate.sh`),
  the commit-time gates (`spec-index-preflight.sh`,
  `role-axis-completeness-guard.sh`), the write-time claim/shape mirrors,
  and `retry-loop-bound.sh`.

There is no hook that fires only when a plain session is about to make a
judgment call — nothing hooked on a generic "you are deciding something"
moment. The closest thing, `directive.sh`, fires on every prompt
indiscriminately with the same full-pipeline text regardless of whether
the user's message is a small judgment question or a large "start work on
this issue."

## Command surface (/orchestrate and friends)

`on-the-record/commands/` contains exactly one file: `run.md`, written in
Korean. There is no `orchestrate.md`/`consult.md` file — the plugin
manifest's `description` field (`on-the-record/.claude-plugin/plugin.json`)
calls this "the orchestration loop for contract v3," and the slash command
users actually invoke is `/orchestrate:run` (referenced from
`directive.sh` and throughout the docs corpus), which maps to this single
`run.md` file — the plugin name `on-the-record` supplies the `orchestrate`
command namespace via the marketplace/plugin naming convention
(`.claude-plugin/marketplace.json`), not a separate command file per verb.

`run.md` structure (section headers, in file order):
- "당신의 루프 (사용자와의 대화 안에서)" ("your loop, inside the
  conversation with the user") — the top-level loop description.
- "미션 보드 (Mission Board)" — when/what/how to render the board: render
  trigger, inputs, classification logic, render format, with per-state
  sub-sections Running / Waiting-for-human-decision / Done / Parking-lot.
- "실행 계획 (Execution Plan)" — the execution-plan grammar (fixed syntax
  plus a worked example), authoring rules (citing issue #197's parser),
  consensus procedure, a minimal/auditable-edit rule, a no-auto-advance
  rule, partial-rejection-of-parallel-steps handling, and
  streaming-landing-is-default (citing #501's session-idle-time
  measurement).
- "세션 시작/압축 복구의 첫 행동은 대화 기억이 아니라 reconcile 이다
  (#534)" — session-start/compaction recovery must call `reconcile()`,
  not rely on conversational memory.
- "계획 소진 → 사람이 확인해야 닫는다" — plan exhaustion requires human
  confirmation to close.
- "띄우기 전에 확인할 것" — preconditions to check before spawning.
- "게이트 작성 시 지킬 것 (#362)" — gate-authoring rules.
- "턴 예산 규칙 (Turn-Budget Rules, #535)" — the same turn-budget rules
  echoed in `directive.sh`.
- "체크아웃/검증 상태 관련 주의 (#390, #412)".
- "능력/계약 부재 주장은 저장소 범위를 밝힌다 (#415)".
- "행동 주장에는 provenance·empty state 를 붙인다 (#416)".
- "같은 모양의 재발은 마킹하거나 기계가 잡는다 (#419)".
- "proposal 은 반복되는 변경의 축적 비용을 말한다 (#424)".
- "승인 요청 형식 / 생성자 절 / 열린 작업 확인 (#318, #363, #379)" — this
  is the section `directive.sh` explicitly defers to for the exact
  relay-action wording ("read it there before relaying").
- "하지 않는 것" — what the orchestrator does not do.

The flow, end to end, is: decompose issue into an issue the user confirms
→ spawn a role session in the background via `spawn.py <role> "<task>"
--issue <n>` → poll/re-arm with `spawn.py watch --issue <n>` (or
`--follow`) → explain the returning PR (phase-1 proposal vs phase-2
delivery) → relay the user's decision (comment/approve/merge) through the
user's own account → re-read the board and propose the next role. This
entire file is one continuous procedure for the issue-to-spawn-to-PR
pipeline; it contains no separate, shorter procedure for getting a single
role's judgment without going through spawn/branch/PR.

## Existing consult mechanism (or absence thereof)

Searching the repo for "consult" (excluding the general-English sense of
"check/read/look up" used throughout the narrative `docs/issue-*` corpus —
e.g. "the downgrade must consult the blocked signal," "the proposal
should consult flows --json's decision_queue") turns up no command, hook,
or code path named or shaped as a role-consultation mechanism. There is no
`/consult` command, no `spawn.py` consult flag, and no code path that gets
a role's judgment without the full spawn-branch-PR pipeline. Every
mechanism that invokes a role's rulebook goes through `spawn_cmd()`/
`_spawn_one()` in `spawn.py`, which always: creates an `issue-<n>/<role>`
branch, spawns a full headless `claude -p` session with `--plugin-dir`
pointing at the role's rulebook plugin, and produces a PR as its
deliverable. There is no lighter "ask role X what it thinks" primitive.

The nearest adjacent mechanism, `delegated-judgment-gate.sh` (issue #573,
`on-the-record/hooks/delegated-judgment-gate.sh`), does something
superficially similar — it evaluates a panel of roles' stance on a
candidate PR and can auto-approve/auto-reject a `gh pr merge`/`gh issue
close` act — but this operates only as a PreToolUse gate on an
already-existing candidate PR at merge time, requires quorum across
multiple roles that already have standing over the changed paths, and is
not something a plain session (or its user) can invoke ad hoc mid-
conversation to get one role's opinion on an open question. It is a
merge-approval automation, not a consult primitive.

## Role rulebook loading

Each role's rulebook is defined in `roles/<role>.json` (many files
present, e.g. `roles/implementation.json`, `roles/architecture.json`) and,
for a subset of "batch-1" roles, an accompanying
`roles/specs/<role>.spec.json` (present at least for architecture,
implementation, conformance-review, requirements-engineering,
observability, and release-engineering) that adds judgment-axis/
reference-resolution rules consumed by `gates/role_spec_shape.py` and the
write-time hooks (`role-axis-completeness-guard.sh`,
`role-spec-reference-guard.sh`). Most role files under `roles/*.json` have
no matching `roles/specs/*.spec.json` counterpart.

Loading happens exclusively through `spawn.py`'s `role_settings(role,
cwd)` function: it reads `roles/<role>.json`, resolves env substitutions,
forces `sandbox.enabled = False` centrally (issue #695), zeroes
`enabledPlugins` for all globally-installed plugins so only the role's own
rulebook plugin is active, and adds `permissions.allow` entries for
WebSearch/WebFetch/Read/Grep/Glob (issues #58/#153). A comment directly
above the function states explicitly (translated): "turning the rulebook
on doesn't happen here — that's `--plugin-dir`'s job" — i.e. the actual
rulebook activation is a CLI flag assembled by `spawn_cmd()`, which loops
over the plugin-dir list and appends `--plugin-dir <path>` once per
rulebook, into a full headless `claude -p ... --plugin-dir <role-plugin>`
invocation.

There is no code path that loads a role's rulebook/judgment rules into an
already-running session (e.g. injecting the rulebook text into the
current context) — the only realized mechanism is: build settings +
plugin-dir list → spawn a brand-new headless CLI process with
`CLAUDE_ROLE=<role>` set → that new process is the one that has the
rulebook active.

## Delegation norm (or absence thereof)

Verified against issue #699's premise: does an existing directive/hook/doc
tell a plain session to delegate a judgment point to a role
mid-conversation? Searching the repo for "delegat" surfaces a large number
of hits, but on inspection every hit resolves to one of three unrelated
senses:

1. **`delegated-judgment-gate.sh`** (issue #573) and its many satellite
   files (tests, proposals, hunt reports touching issues #587, #597, #609,
   and #641) — a merge-time PreToolUse gate that auto-approves/rejects a
   `gh pr merge` act when a multi-role panel already reached unanimous
   support on an already-produced PR. This delegates a merge decision to a
   computed panel verdict; it does not tell a session to go ask a role
   something.
2. **Code-level "delegates to" comments** meaning ordinary function
   delegation/composition (seen in `gates/role_spec_shape.py` and
   `on-the-record/gates/record_lint.py`) — unrelated to role handoff.
3. **`spawn.py`'s `_DELEGATION_RE`** — a regex (matching `run_in_background`,
   a Korean "background" phrase, the literal word "delegate," or
   "background worker") used by `spawn.py`'s log-anomaly scan to flag when
   a role session's own transcript *claims* it delegated/backgrounded
   work it should have done itself (a fraud-detection check on a role's
   self-report), not a directive telling any session to delegate.

None of these hits is a directive/hook/doc instructing a plain
(non-orchestrator, non-role) working session to escalate a judgment point
to a role instead of deciding it inline. The closest general norm is
`deliverable-guard.sh`'s enforcement that an orchestrator session must not
itself write deliverables (src/test/docs) — but that is scoped to write
acts, not judgment points reached purely in conversation (e.g. "should we
use approach A or B" asked and answered inline with no file write).
**Issue #699's claim that this delegation norm does not yet exist holds**
— verified by exhaustive search, not just spot-check.

## Prior art / related decisions

- Searching for "contract v3" and "role-handoff" both resolve to the same
  underlying artifact: the role-handoff contract (v3) is **not stored in
  this repo**. `protocol.md` states plainly, near its top: "The
  role-handoff contract (v3) is the authority here, not this document. It
  lives only in `core/contract/role-handoff-contract.md`" in the core
  plugin's own repository (no local copy here). All in-repo references to
  "contract v3" (in `README.md`, `on-the-record/commands/run.md`, and
  dozens of `docs/issue-*` records) cite specific sections by number
  (s19 = the `APPROVE issue-<n>/<role>` signal and single-account relay
  path; s20/§20 is referenced once in
  `docs/issue-587/reports/execution-observation/survey.md`) without
  quoting the contract text itself.
- `docs/decisions/` holds five ADRs; the most relevant is
  `docs/decisions/2026-08-11-remove-role-session-sandbox.md` (issue #695)
  — removes the per-role-session sandbox because repeated blockage bugs
  (tracked across several prior issues) exceeded its protective value;
  enforcement moved fully onto the CLI's tool-permission layer plus
  PreToolUse hooks.
- `docs/issue-695/` (proposals/reports/implementation) is the sandbox-
  removal work referenced above; `spawn.py`'s `role_settings()` now
  unconditionally forces `sandbox.enabled = False`.
- **Issue #700 has no matching documentation folder under `docs/` in this
  repo.** Its only trace found in-repo is one commit, "fix(issue-700):
  headless role sessions spawn with bypassPermissions" (hash starting
  `b762681`), which changed `spawn.py` and `test_spawn.py`. Its message
  states: after issues #695 and #697 removed the role-session sandbox,
  every Bash call in a headless role session hit the CLI's approval
  classifier with no one able to answer, causing sessions for issue #698
  and this issue (#699) to die "failed-no-commit" on plain `git add`/`gh`
  calls; the operator decision was to make `--permission-mode
  bypassPermissions` the headless default in `spawn_cmd()`, with
  enforcement staying on hooks (PreToolUse `exit 2`, which
  `bypassPermissions` does not disable) — see the Korean comment block
  directly above the `cmd = ["claude", "-p", ...]` assembly in
  `spawn_cmd()`. A "bootstrap exception" is noted in the same commit
  message: the orchestrator session itself authors the fix because no
  role session can currently produce a commit for issue #700's own
  repair — that note lives only in the commit message, not in a doc file.
- Both #695 and #700 are directly load-bearing for #699's likely proposal:
  role sessions now run fully unsandboxed and with bypassPermissions,
  meaning any new lightweight "consult a role" mechanism this issue might
  propose would inherit the same execution-license question #700 already
  resolved once (hooks, not sandbox/permission-mode, are the enforcement
  layer) — a phase-2 design should account for that rather than
  re-introducing a sandbox/permission debate.

## Write set candidates for the phase-1 proposal (files phase 2 would likely touch)

Purely locational — where future work would touch, not a design:

- **`on-the-record/hooks/directive.sh`** — the only hook that already
  reaches every plain-session prompt unconditionally (`CLAUDE_ROLE` is its
  only gate). Any new "delegate judgment to a role" directive text, if it
  belongs in a hook rather than a command, would be added or edited here.
- **`on-the-record/hooks/hooks.json`** — registration point if a new hook
  file were introduced instead of editing `directive.sh` in place (e.g. a
  new UserPromptSubmit or PreToolUse hook scoped to judgment-shaped
  prompts).
- **`on-the-record/commands/run.md`** — the sole existing command file and
  the canonical location for full-procedure prose; a new `/consult`-style
  command would be a new sibling file under `on-the-record/commands/`
  (there is currently exactly one file there, so precedent for the file
  layout/frontmatter would need to be drawn from `run.md` itself, plus how
  `.claude-plugin/marketplace.json` and
  `on-the-record/.claude-plugin/plugin.json` expose command namespacing).
- **`spawn.py`** — `role_settings()` and `spawn_cmd()` are the only code
  paths that ever activate a role's rulebook; a lighter-weight consult
  primitive that reuses the rulebook without the full branch/PR pipeline
  would touch this file, most likely new functions adjacent to these two
  rather than modifying the existing spawn contract (`spawn_cmd()`'s own
  docstring already frames it as producing "session argv/env" for a full
  headless run — a consult primitive is a different shape of call).
- **`roles/*.json` / `roles/specs/*.spec.json`** — unaffected as data
  files unless a new "consult-mode" role property is introduced; the
  loading code path (`role_settings()`) is the actual point of change. The
  loading code centrally forces the sandbox off regardless of what a role
  file declares (issue #695), so any new consult-mode gating would need
  its own field/flag if role-level opt-in/out is wanted.
  For a goal-loop/delegation norm's location: nothing in the current
  corpus houses a "when should a plain session ask a role" rule — the
  nearest existing home for such a norm, by precedent, is either
  `directive.sh` (mechanically injected every prompt, like the existing
  orchestration directive) or `on-the-record/commands/run.md` (prose
  procedure, referenced by `directive.sh` for full detail) — phase 2 would
  need to decide which of these two loci (or a new third one) it extends.
