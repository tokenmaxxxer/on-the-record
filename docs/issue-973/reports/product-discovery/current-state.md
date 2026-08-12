# Current-state survey — issue #973: concurrent multi-agent judgment (req#5)

## Background / context

canonical: docs/issue-751/reports/defect-verification.md (read this session)

`docs/issue-751/reports/defect-verification.md`, Finding 1: req#5's literal clause — "1+ agents
judging simultaneously and discussing a judgment" — is unserved today.
`docs/specs/northpole.md`'s req#5 traceability paragraph cites `panel-unanimous-support-v1` and
`consult_cmd()` as serving req#5 without stating that neither runs live concurrent discussion.

canonical: spawn.py:4095-4162 (read this session)

`consult_cmd()` issues exactly one `subprocess.run` per call: one caller, one bounded headless
session, one JSON verdict back. No second session, no exchange, no rebuttal.

derived: `grep -rln "SendMessage\|ListAgents" spawn.py gates/ roles/ docs/specs/`
```
$ grep -rln "SendMessage\|ListAgents" spawn.py gates/ roles/ docs/specs/
(no output)
```
Zero hits — the harness-native cross-session messaging primitive is not adopted, audited, or
referenced anywhere in this repo's own machinery or specs.

canonical: gh issue view 751 --comments (read this session)

Official capability facts (issue #751 comment, claude-code-guide 2026-08-12, v2.1.226):
- Cross-session messaging is official: `ListAgents`/`SendMessage` between local sessions sharing a
  filesystem (code.claude.com/docs/en/cross-session-messaging.md). Messages are plain text only,
  never history/files.
- A long-running `claude -p` session binds an inbox socket and appears in `ListAgents` — except in
  `--bare` mode. Held-message dialog expiry is 5min; `crossSessionInbound=accept` is the setting
  for worker sessions to receive without a prompt.
- Agent Teams (lead+teammates, mutual messaging) exist but are experimental
  (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) — not viable for a default-on plugin (req#7).
- Plugins cannot auto-spawn processes or route `SendMessage` themselves; they can surface
  coordination via hooks (blocking), monitors (watch shared state files, notify the session), and
  directives.

canonical: spawn.py:4004-4006, spawn.py:4118-4120 (`spawn_cmd`/`consult_cmd`, read this session)

Both already launch `claude -p ...` without a `--bare` flag.
```
$ grep -n '"--bare"' spawn.py
(no output)
```
Per the official-docs fact above, every role session `spawn.py` launches — both the
deliverable-producing `spawn_cmd()` path and the judgment-only `consult_cmd()` path — is already
non-bare and therefore already binds an inbox socket and already appears in `ListAgents` by
construction. Nothing about session launch needs to change to make sessions messageable; the open
gap is (a) `crossSessionInbound=accept` in the settings given at spawn, (b) an orchestrator step
that actually calls `SendMessage`/`ListAgents` between two such sessions, and (c) a repo location
where the resulting exchange is written down.

canonical: spawn.py:4080-4090 (`_append_consult_trace`, read this session)

`consult_cmd()`'s own trace mechanism ("no traceless consults", operator decision, issue #699)
already establishes the repo's precedent for "every consult call leaves one line, success or
failure" — the closest existing analog to req#2's "every position/rebuttal/verdict lands in the
repo," but scoped to a single consult call's own outcome, not a multi-turn discussion.

`docs/issue-751/proposals/2026-08-12-defect-verification-concurrent-judgment.md` is cited from the
defect-verification record as the phase-1 proposal opened by #751's own follow-up; not read in full
this session (unverifiable: out of scope for this survey — issue #973 is the follow-on
product-discovery entry the #751 record's own Finding 1 asks for, not a re-derivation of that
proposal's own content).

## Problem, stated without the proposed solution (JTBD)

- **Job performer**: the orchestrator (or a deviation-loop session) that currently must accept a
  single role's single judgment as final, and the operator who currently has no on-record trace of
  *why* two agents might have disagreed before a verdict was reached — because no second agent is
  ever consulted concurrently.
- **Job**: get a judgment on a contested or high-stakes question that has been genuinely
  cross-examined by a second independent perspective — positions stated, at least one rebuttal
  exchanged, a joint verdict reached — before the orchestrator treats it as settled, instead of
  accepting one session's unchallenged output as the answer.
- **Circumstance**: `consult_cmd()` today calls exactly one role session per question and returns
  whatever that one session says, with no mechanism for a second, independently-launched session to
  see the first's position and respond to it — even though both consult and spawn sessions already
  run in a message-capable process shape (non-bare `claude -p`), and even though req#5 explicitly
  names concurrent multi-agent discussion as a requirement, not an aspiration.
- **Desired outcome**: for a seeded question, two or more role sessions are launched as
  message-capable processes, exchange at least one position and one rebuttal through the harness's
  own official cross-session messaging, and a joint verdict — together with the full position/
  rebuttal trail — lands in the repo as a re-derivable record, without requiring an explicit skill
  invocation (default-on, req#7) and without silently losing the discussion if messaging is
  unavailable in a given environment (falls back to sequential consults and states that it did).

## Where this sits on the opportunity-solution tree

canonical: docs/issue-751/reports/defect-verification.md (read this session)

- **Outcome**: judgments the orchestrator relies on for contested/high-stakes decisions carry a
  recorded, cross-examined basis instead of a single unchallenged opinion — reducing the rate at
  which a later review finds a verdict that a second independent judge would have contested, without
  materially increasing time-to-verdict for the common case.
- **Opportunity**: req#5's literal text already calls for "1+ agents judging simultaneously and
  discussing a judgment" and #751's own record shows it is currently served only by a naming
  coincidence (`panel-unanimous-support-v1`, `consult_cmd`) — neither of which actually runs
  concurrent discussion. The harness itself already supplies the missing primitive
  (`SendMessage`/`ListAgents`, official, non-experimental) and `spawn.py`'s own session-launch code
  already produces message-capable processes without modification. The gap is purely orchestration:
  nothing today calls `SendMessage`/`ListAgents` between two role sessions, and nothing writes the
  resulting exchange to the repo.
- **Candidate solutions**: scored in the proposal — (a) a new `panel_cmd()` analog to
  `consult_cmd()` that spawns 2+ non-bare `claude -p` judge sessions with
  `crossSessionInbound=accept`, has the orchestrator relay `SendMessage` turns between them (or lets
  them message each other directly if both are addressable), and writes every position/rebuttal/
  verdict to `docs/issue-<n>/reports/panel/`; (b) Agent Teams (rejected — experimental, req#7
  default-on bar); (c) a shared-file "mailbox" convention (each session writes its position to a
  file, a monitor notifies the other) as the degradation path when live messaging is unavailable,
  distinct from the live-messaging primary path.
- **Discriminating assumption test**: whether an orchestrator process can actually address two
  concurrently-running non-bare `claude -p` sessions by name via `ListAgents` and deliver at least
  one `SendMessage` round-trip between them before either session exits — this is what the
  proposal's pre-registered hypothesis targets. A "yes" means req#5's literal clause is buildable as
  designed here (live concurrent discussion, on the record); a "no" (e.g. sessions exit before the
  other's reply arrives, or `ListAgents` cannot see a session spawned via `subprocess.run` the way
  `spawn_cmd()`/`consult_cmd()` do it) would mean the mechanism must fall back to the sequential/
  mailbox degradation path as its normal case rather than its exception.

## Degradation, stated explicitly

canonical: spawn.py:4095-4162 (read this session); docs/issue-751/reports/defect-verification.md
(read this session)

Today, req#5's concurrency clause is served by nothing — every judgment is a single `consult_cmd()`
call to one session, evaluated in isolation. The gap does not currently fail visibly; it fails
quietly, because `docs/specs/northpole.md`'s traceability paragraph asserts req#5 is served when
#751's own record shows it is not. Until this mechanism ships, that quiet gap persists exactly
as-is: no regression is possible from not having built this yet, but no cross-examined judgment is
possible either. Once built, if live cross-session messaging is unavailable in a given environment
(a sandbox without socket support, a session spawned `--bare` by some other caller, a message that
times out past the 5min hold), the mechanism must degrade to sequential consults — call each judge
session in turn via the existing `consult_cmd()` shape, with no live exchange — and record
explicitly, in the same repo location a live panel would have written to, that it degraded and why.
An unlabeled sequential fallback would reproduce the same shape #751's record already surfaces (a
mechanism believed to serve req#5 that in practice does not) — the proposal's own degradation design
is scored explicitly against that risk.
