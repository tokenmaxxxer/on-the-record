---
subject: issue-751
role: architecture
kind: survey
loop_state: n/a
---

# Current-state survey — inter-agent communication (northpole audit B)

Scope: how spawned roles actually exchange information — consult (#699),
board record read paths, spawn-time context, PR-comment relay — against
northpole req #5 (problems not pushed back to the human) and req #4
(autonomous completion). Read-only; no code changed.

code_under_review:
- spawn.py
- on-the-record/commands/consult.md
- protocol.md
- docs/handbooks/operations.md

## Sub-area 1 — consult (#699): reach and limits

**MET** for its stated scope (bounded judgment relay), **GAP** for context transfer.

`consult_cmd()` at spawn.py line 3556 loads the target role's rulebook via
`plugin_dirs()`/`role_settings()` and runs one bounded headless session
(`CONSULT_TIMEOUT = 180`, spawn.py line 42) whose entire input is a fixed
prompt template plus the caller's free-text `question` (spawn.py lines
3598-3606). The session is told not to branch, commit, or open a PR
(spawn.py line 3600 — enforced only by the prompt, not a distinct
sandbox rule). Every call appends a one-line trace, success or failure
(`_append_consult_trace`, spawn.py lines 3543-3554), to
`docs/issue-<n>/reports/consult-log.md` (spawn.py lines 3534-3540) — "no
traceless consults" (spawn.py line 3546).

`on-the-record/commands/consult.md` states explicitly what consult does
**not** do (see its "무엇을 하지 않나" section): no board write
(`docs/issue-<n>/reports/<role>.md`), no roster/watcher registration. The
consult call site never reads `docs/issue-<n>/reports/` and never passes
prior board records, another role's findings, or hand-off notes into the
prompt — the callee's only context is (a) its own rulebook and (b) the
literal question string the caller composed. Any board content the caller
wants reflected has to be hand-copied into the question text by whoever
calls `consult`.

GAP: consult has no structural path from "role A's board record" to "role
B's consult context" — it is purely a Q&A function over a rulebook, and the
caller is the only bridge.

## Sub-area 2 — board record read paths (one role's findings → another's input)

**PARTIAL.** The board is real and in-repo (`docs/issue-<n>/reports/<role>.md`,
per protocol.md's board section), and gates read `loop_state` for
status/routing (`gates/flows.py`, `_stage_for`/board-join logic around
lines 350-385). But two things are true at once:

1. on-the-record itself reads only the frontmatter, never the body — stated
   plainly in protocol.md: "on-the-record reads the frontmatter and nothing
   else." Nothing in spawn.py extracts another role's findings text and
   hands it to a new session.
2. Reading a predecessor's record body is left to the orchestrating
   conversation's judgment, by design: "who runs next is not a table lookup
   — it is a judgment call the orchestrating conversation makes by reading
   the board directly" (docs/handbooks/operations.md, "The loop" section).
   The worked example there shows the orchestrator manually composing the
   next role's task string with "read the board: …" as free text — nothing
   guarantees this phrase is present, or that the spawned role actually
   reads the right predecessor file.
3. Only `main`-merged records count as board state — "The board is what is
   MERGED to main. An open PR is not yet on the board" (role-handoff
   contract v3 s19, echoed in this session's own SessionStart hook text). A
   role spawned while a predecessor's PR is still open has no access to
   that predecessor's findings at all, through any channel — not board, not
   consult, not spawn-time context — until the PR merges.

So the read path exists (git-native: a spawned role's workspace clone can
read `docs/issue-<n>/reports/` on `main` like any other file) but nothing
makes a spawned role actually do it. It is available, not wired.

## Sub-area 3 — spawn-time context (task string only, or more?)

**GAP**, confirmed by direct read of the issue-mode task construction.

`_spawn_one()` (spawn.py, function starting line 4382), for `--issue`
spawns, builds the task handed to the session as: the caller's free-text
`task` argument, prefixed with a fixed template (spawn.py lines 4435-4444)
that says: which issue/branch this is, the definition of done
(commit+push+PR), and a headless/single-shot warning. That prefix is the
**entire** structural addition on top of the caller's text — no prior board
record, no scout brief, no consult trace, no hand-off note, no other role's
findings are read from disk and appended. The spawned session's only route
to that information is (a) whatever the caller typed into `task`, or (b)
the session's own subsequent tool calls (`gh issue view`, reading
`docs/issue-<n>/reports/` itself) — both of which depend on the session
choosing to look, not on the spawn mechanism supplying it.

This session (issue-751/architecture) is itself the evidence: this turn's
own spawn-time task string was exactly the fixed template plus the
human-authored audit brief — no other role's board record content was
attached, even though issue #751 explicitly references issue #699's design
(consult) and issue #748 (northpole spec), both of which have their own
board/records this session had to go fetch itself via `gh issue view` and
manual file reads.

## Sub-area 4 — PR-comment relay

**PARTIAL.** Comments exist and are durable/idempotent, but they carry
status only, never findings content.

- `_post_session_end_comment` (spawn.py line 2458): one line — a fixed
  marker, then either the PR URL or "no PR" (spawn.py lines 2485-2491). No
  summary of what changed, no findings, no loop_state.
- `_post_crash_comment` (spawn.py line 2385) and `_post_stall_comment`
  (spawn.py line 2420): same shape — status marker + workspace/log paths,
  not content.
- `_post_stranded_push_comment` (spawn.py line 2502): marker + `branch` +
  `reason` + first 200 chars of a `detail` string (spawn.py lines
  2516-2517) — the one relay that carries any substantive text, and it is
  capped at 200 chars and reserved for a specific push-failure class, not
  general findings.

None of the four comment-posting functions read `docs/issue-<n>/reports/`
or forward record content into the comment body. A human (or another role)
reading the issue thread learns "a PR exists" or "it crashed", never what
was found — they must open the PR/board record themselves to get content.
This matches protocol.md's stated design ("coding never ships another
role's verdict, spec, or record artifact") but that design choice means the
comment thread cannot function as an agent-to-agent findings channel by
itself, only as a pointer to where findings live.

## What forces a human/orchestrator bridge (req #5 relevance)

1. **Predecessor-record discovery.** Nothing structurally makes a spawned
   role read the right prior `docs/issue-<n>/reports/<role>.md` — the
   orchestrating conversation composes the task string by hand each time.
   If the orchestrator omits or mis-states the pointer, the role proceeds
   blind and re-derives.
2. **Open-PR isolation.** Two roles worked concurrently on the same issue
   via separate `--issue` spawns cannot see each other's in-flight findings
   at all (board is merged-only) — only after a merge, which is a
   human/gate act.
3. **Consult has no board access.** A role invoked via `consult` for a
   quick judgment cannot be given "what role X already found" except by the
   caller pasting it into the question string by hand — every consult is
   informationally isolated from the board by construction.
4. **Comments don't carry content.** A human scanning the issue thread for
   "what happened" gets status only; substance requires opening the PR/board
   file — an extra human step every time, at exactly the moment req #4
   (human-legible reporting) needs it cheapest.

## Open findings

- OF-1: no mechanism forwards a predecessor role's board-record body into a
  successor's spawn-time task string; reliance is entirely on the
  orchestrating conversation composing it by hand each spawn.
- OF-2: `consult_cmd()` has zero board-record read access — every consult is
  contextually isolated except for what the caller manually pastes into the
  question.
- OF-3: PR-status comments (`_post_session_end_comment`,
  `_post_crash_comment`, `_post_stall_comment`) never carry board-record
  content, only a status line and a URL/path.
- OF-4: concurrent roles on the same issue cannot see each other's findings
  until one side merges (board is `main`-only by contract), which is
  correct isolation for write safety but is unannounced anywhere as a
  communication limit.

## Why

northpole req #5 requires mid-course problems to be resolved by spawning and
discussing WITH the appropriate agents, not pushed to the human. That
presupposes agent-to-agent context actually reaches the next agent. This
survey traces the four channels literally available today (consult, board,
spawn-time task string, PR comments) and finds all four structurally sound
for their narrow stated purpose but none of them automatically carries
substance from one role to the next — every hand-off today is either (a)
the orchestrating human/conversation typing a pointer or excerpt by hand, or
(b) the next role re-deriving by reading files it was never told to read.

## Upstream basis

- issue #751 (this audit)
- issue #699 (consult design, R1 constraint: judgment-only, no board writes)
- issue #748 and docs/specs/northpole.md (the 7 requirements, req #4 and #5)
- role-handoff contract v3 s19 (board = merged-only)

## Next steps

Phase-2 proposal (see docs/issue-751/proposals/2026-08-11-inter-agent-comm-audit-record.md)
is to write the formal MET/PARTIAL/GAP classification with rank as the
architecture record for this issue, once approved — this survey is the
evidence base for that record; ranking and named-repo/component assignment
happen there.

## Resolution path

Each OF above resolves by opening a dedicated issue against the responsible
repo once the phase-2 record ranks it (rank determines which OF gets an
issue first); this survey does not open those issues itself (read-only,
proposal-gated).
