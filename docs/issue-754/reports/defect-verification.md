# Defect-verification record (issue #754, phase 2)

code_under_review:
- spawn.py
- on-the-record/hooks/directive.sh
- on-the-record/monitors/poll-heartbeat.sh
- on-the-record/commands/run.md

canonical: `git rev-parse --short HEAD` (run this session) = 7fe9652.

## What was done

Phase-2 execution of the plan approved via the issue-level comment
`APPROVE issue-754/defect-verification` (single-account mode,
JiwonJung94, an account listed in `docs/specs/approvers.md`), following
the proposal at
`docs/issue-754/proposals/2026-08-12-composition-defect-verification-record.md`.

canonical: `git log origin/main --oneline -1` (run this session) =
`7fe9652 issue-754 defect-verification phase-1: composition-audit
survey + proposal (#977)`. PR #977's phase-1 content is already on
`main`; this branch was rebased onto `origin/main` (not recreated).
canonical: `git diff --stat HEAD origin/main` (run this session,
before the rebase) touched only `docs/issue-753/**` and
`docs/issue-973/**`, zero lines under `docs/issue-754/**` — the
rebase was a clean fast-forward-equivalent for this issue's files.

This record independently re-derives, against current HEAD (7fe9652),
every citation the phase-1 survey
(`docs/issue-754/reports/defect-verification/survey.md`) made against
the architecture survey's (PR #761) claims and its own two
self-devised attempts. All four attempts' outcomes are unchanged from
phase 1; two line numbers moved (`spawn_cmd` def, `consult_cmd`
docstring block) and are corrected below to their current-HEAD
locations.

## Why

Issue #754 requires a detailed, read-only audit of automated
problem-resolution composition against northpole req #5, with every
sub-area classified MET/PARTIAL/GAP and file:line evidence, verified
independently rather than accepting the architecture survey's own
verdicts at face value — this role's mandate is to catch a defect that
neither the build nor the earlier review step caught, by attempting
independent reproduction of each claim.

## Upstream basis

- `docs/issue-754/reports/architecture/survey.md` (PR #761) —
  cite-and-skip for its step-by-step composition-loop description and
  its scoping of issue-authorship/merge as deliberate human gates;
  re-derived (not cited) for its two structural code claims (Attempts
  1 and 2 below).
- `docs/issue-754/reports/defect-verification/survey.md` (this
  session's own phase-1 output) — re-derived in full against current
  HEAD rather than cited, since role-handoff contract v3 s19 treats a
  survey as phase-1 research feeding phase-2, not as a closed_checks
  entry to cite against a matching sha.

## Attempts and outcomes

**Attempt 1 (source: architecture survey — "no code path in
`spawn.py` has one role's own session invoke
`_spawn_one()`/`spawn_cmd()` against itself").** Outcome:
**reproduced.**
canonical: `grep -n "^def _spawn_one\|^def spawn_cmd" spawn.py` (run
this session):
```
$ grep -n "^def _spawn_one\|^def spawn_cmd" spawn.py
3985:def spawn_cmd(settings_path: str, role: str, unattended: bool,
5037:def _spawn_one(cwd: str, role: str, task: str, unattended: bool,
```
canonical: `grep -n "_spawn_one(\|spawn_cmd(" spawn.py` (run this
session):
```
$ grep -n "_spawn_one(\|spawn_cmd(" spawn.py | grep -v "^39\|^50"
3107:    _spawn_one(work, role, task, unattended=True, issue=issue, bounded=True)
4506:    return _spawn_one(a.cwd, a.role, a.task, a.unattended, a.issue,
5121:        cmd, extra_env = spawn_cmd(settings, role, unattended,
```
Line 3107's caller is `_respawn_or_cap` (def at spawn.py:3025 — the
crash/stall watcher). Line 4506 is the CLI's `argparse` dispatch. Line
5121 is `spawn_cmd` invoked from inside `_spawn_one` itself, its own
issuing pipeline. None of these three call sites originates from
role-session code choosing, on its own initiative, to invoke either
function against itself. Verdict unchanged from the architecture
survey; `spawn_cmd`'s def line moved from 4020 (phase-1 survey's
citation) to 3985 at current HEAD — re-derived here, not copied.

**Attempt 2 (source: architecture survey — "`consult_cmd()` ... is
opinion-only. A role that consults another role gets a text judgment
back into its own session; it cannot hand off actual work").**
Outcome: **reproduced.**
canonical: `sed -n '4095,4102p' spawn.py` (run this session):
```
def consult_cmd(role: str, question: str, issue: int | None = None,
                cwd: str | None = None) -> dict:
    """자문(consult): 역할의 룰북을 로드해 판단만 돌려받는다 — 브랜치도
    커밋도 PR 도 만들지 않는다(이슈 #699 R1). `spawn_cmd()`/`_spawn_one()`
    의 발급 파이프라인과는 별개의, 훨씬 작은 조립이다: 그 함수들이 여는
    브랜치/워크스페이스/워처/roster 등록은 전부 배달물(deliverable)을
    향한 것이고, 자문은 텍스트 하나만 되돌려주면 끝나기 때문이다.
```
The docstring (spawn.py:4097-4098) states plainly it creates no
branch, no commit, no PR. canonical: `grep -n '"answer"\|"confidence"\|"caveats"' spawn.py`
(run this session) = lines 4068, 4142-4143 — the subprocess prompt
asks for a fixed JSON shape `{"answer","confidence","caveats"}` only,
no branch/spawn instruction.
canonical: `awk '/^def consult_cmd/,0' spawn.py | grep -n "_spawn_one\|spawn_cmd(\|gh pr" | head -5`
(run this session) — no output before the function's closing brace:
no `_spawn_one`/`spawn_cmd`/`gh pr` call anywhere in the function
body. Verdict unchanged; docstring line range corrected from the
phase-1 survey's 4095-4099 to 4095-4102 (the block extends two lines
further at current HEAD).

**Attempt 3 (source: self-devised — does #958's deviation loop, which
the issue names as providing structure, actually reach a spawned role
session, or only the orchestrator?).** Outcome: **reproduced**, as a
gap: the deviation loop is orchestrator-only and never reaches a role
session.
canonical: `sed -n '1,12p' on-the-record/hooks/directive.sh` (run this
session):
```
#!/usr/bin/env bash
# UserPromptSubmit: the orchestration directive, injected EVERY prompt —
# the coding-rulebook pattern (terse/freelunch/scout): steering must be
# freshly read to steer, and a session-start-only injection drifts out of
# a long context. Installing this plugin IS the opt-in. Kill switch:
# ORCHESTRATE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
# A spawned role session is never the orchestrator, even if the plugin leaks in.
[ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
```
`directive.sh` is the UserPromptSubmit hook that injects the goal loop
and, nested inside it, "YOUR DEVIATION LOOP (issue #803)" (the
FILE-AS-ISSUE branch that calls `spawn.py spawn <role> "<task>"
--issue <n> --background`, per the phase-1 survey's citation of
directive.sh:157-183, unchanged at current HEAD). Line 12 exits before
any of that text is emitted whenever `CLAUDE_ROLE` is set — the env
var this very session runs under.
canonical: this session's own SessionStart reminders, visible earlier
in this conversation, carried the defect-verification role directive,
warrant, scout, freelunch, and terse directives and no deviation-loop
text, consistent with the `CLAUDE_ROLE` early-exit above. So the loop
that would let a role compose FILE-AS-ISSUE + spawn on its own
initiative fires only in the orchestrator's own `/run` conversation.

**Attempt 4 (source: self-devised — is poll-heartbeat.sh a
counter-example, #922).** Outcome: **not-reproduced.**
canonical: `grep -n "spawn_cmd\|_spawn_one\|gh issue create\|gh pr merge" on-the-record/monitors/poll-heartbeat.sh`
(run this session) — no match: poll-heartbeat.sh does not close the
gap.
canonical: on-the-record/monitors/poll-heartbeat.sh:1-60 (read this
session) — the due-tick branch runs `spawn.py watchdog
--auto-respawn` in the foreground and echoes its captured stdout only;
per the grep above it never files an issue, spawns a different role,
or merges. It surfaces a report to the human Monitor channel for the
orchestrator to act on next turn — same human-turn dependency as
Attempt 3, via a different channel.

## Classification (MET / PARTIAL / GAP, ranked)

- **role-initiated cross-role spawn** (a role composes its own fix):
  **GAP**, file:line spawn.py:5037 (`_spawn_one`), call sites
  spawn.py:3107, 4506, 5121, per Attempt 1's canonical greps above.
  Rank: **High** — the exact primitive northpole req #5 asks for;
  #958's deviation loop was purpose-built for it yet structurally
  cannot reach the sessions that would use it (Finding 1).
- **deviation loop reaching role sessions**: **GAP**, file:line
  on-the-record/hooks/directive.sh:12 (`CLAUDE_ROLE` early-exit), per
  Attempt 3's canonical `sed` above. Rank: **High** — #958 is the
  mechanism the issue names as "providing structure"; it exists but is
  scoped out of exactly the sessions (spawned roles) where unassisted
  problem-to-resolution composition would occur (Finding 1).
- **cross-role consult** (judgment only): **PARTIAL**, file:line
  spawn.py:4095-4102 (per Attempt 2's canonical `sed` above). Rank:
  Medium — lets a role get another role's judgment without a human
  turn, but the answer cannot become a branch/PR itself; this is the
  one piece of req #5 ("research AND discuss the fix") that already
  works unattended (Finding 2).
- **unattended reporting** (poll-heartbeat, #922): **PARTIAL**,
  file:line on-the-record/monitors/poll-heartbeat.sh:1-60 (per Attempt
  4's canonical grep above). Rank: Medium — surfaces watchdog state
  without a human prompt, but composes nothing: detection/report, not
  resolution.
- **same-role retry on crash/stall**: **MET** (retry, explicitly not
  composition), file:line spawn.py:3025 (`_respawn_or_cap`),
  spawn.py:3153 (`_self_trigger_respawn`).
  canonical: `grep -n "^def _respawn_or_cap\|^def _self_trigger_respawn" spawn.py`
  (run this session):
  ```
  3025:def _respawn_or_cap(key: str, work: str, issue: int, role: str, log: str,
  3153:def _self_trigger_respawn(outcome: str, roster_key: str, work: str, issue: int,
  ```
  `_self_trigger_respawn`'s line moved from the phase-1 survey's 3151
  to 3153 at current HEAD, per the grep just above — re-derived here.
  Rank: Low.
- **issue authorship, merge**: **MET** (human-gated by design, out of
  scope for req #5), file:line on-the-record/commands/run.md:20-22.
  canonical: `grep -n "pr merge" spawn.py` (run this session) —
  matches at spawn.py:2246 and spawn.py:4450 are both comments/log
  strings about a *human's* resume turn and printed guidance to relay
  a `gh pr merge`, not a call site; no automated-merge call exists.
  Rank: Low.

## Open findings

**Finding 1** — addressed_to: architecture (or a follow-up
implementation issue). Severity band: **blocking** (deterministic band
lookup: High-centrality per northpole req #5, independently reproduced
against current HEAD 7fe9652, not freehand). Evidence:
on-the-record/hooks/directive.sh:12 combined with directive.sh:157-183
(the deviation-loop body that early-exit skips, per Attempt 3 above).

**Finding 2** — addressed_to: architecture. Severity band: **advisory**
(deterministic band lookup: Medium — `consult_cmd` already covers
"research and discuss"; the missing half is the same primitive as
Finding 1, not a separate build). Evidence: spawn.py:4095-4102
(`consult_cmd`) has no code path back into `_spawn_one`/`spawn_cmd`,
per Attempt 2's canonical greps above.

## Accumulation

Not accumulation-cost-shaped: this record is one independent
verification round covering four attempts already scoped in phase 1,
run once against one fixed commit — not a change whose cost grows
with repeated application or accretion over time.

## What did not work

None.

kind: verify-record
loop_state: reproduced
next steps: hand Finding 1 (blocking) and Finding 2 (advisory) to the
architecture role or a follow-up implementation issue; no code fix
belongs in this record per this role's read-only mandate.
resolution path: architecture role opens (or the human opens) a
follow-up issue scoping a `CLAUDE_ROLE`-aware path for #958's deviation
loop to reach spawned role sessions (Finding 1), and, lower priority,
a `consult_cmd` → `spawn_cmd`/`_spawn_one` handoff path (Finding 2).
