---
status: proposed
files:
  - docs/issue-878/reports/product-discovery/survey.md
  - docs/issue-878/reports/product-discovery/scout-brief.md
  - docs/issue-878/proposals/2026-08-11-async-completion-drive.md
---

## Request

Issue #878 step 1 (product-discovery): design how an installed
orchestrator self-drives an async delegation to completion with no
human — after spawning a role, later notice the delegated PR is ready
(reusing the landed poll/Monitor loop #829/#835/#782, no new scheduler),
verify it, merge it, rebuild/re-check, emit the 4-part human-legible
`final_report` — AND how the #776 harness measures this multi-turn async
completion so #1/#4 reach a real PASS, never a false one. Survey +
proposal only, no code (contract v3 s19 phase-1 scope).

## Constraints

- Reuse #829 (turn-driven poll rearm), #835 (Monitor heartbeat), #782
  (dual-channel event+poll) verbatim — no new polling/scheduling engine
  (issue's own instruction).
- Contract v3 s22 (this session's own system reminder): a headless/
  single-shot invocation must not end a turn with delegated work
  unconsumed. #878's design must show how the ORCHESTRATOR itself — not
  just role sessions — is held to that same discipline where it applies.
- The design must state, not blur, that a `-p` orchestrator process which
  has already returned `end_turn` cannot be reasoned with again in-process
  (survey citation: `code.claude.com/docs/en/headless.md` §"Background
  tasks at exit") — no amount of hook/Monitor/watchdog cleverness revives
  a dead process; continuation has to come from a new, external
  invocation.
- Never fake a PASS: the harness change must make #1/#4 measurable as a
  real PASS only when merge + a genuine 4-part report actually happened,
  and must return UNMEASURED-with-reason, never a false PASS, when the
  loop cannot complete (issue's own Acceptance line).

## Rationale

**Go, not kill.** The gap is now precisely isolated, not speculative: run
#5 (PR #877) proved every upstream step of the loop — issue creation, role
delegation, the fix itself, PR-open — works end to end; the sole remaining
break is the orchestrator's own process lifecycle (survey, PR #877/run5
citation). This is a narrow, well-scoped completion step, not a
speculative new capability.

**Chosen approach — split the design by process lifecycle, because the
survey shows the two cases need genuinely different mechanisms, not one
mechanism with two names:**

1. **Interactive installed session (a human-owned, long-running process,
   not `-p`).** The reuse target here is real: `directive.sh` already
   instructs `spawn.py watch --issue <n> --follow` in the background so
   Claude Code's own task-notification resumes the session on the next
   material event (survey citation, `directive.sh` lines ~90-108). What's
   missing is not the notify mechanism — it's what the orchestrator does
   once notified. Add one more `directive.sh` paragraph, gated the same
   `CLAUDE_ROLE`-unset way as the existing four: when a `watch --follow`
   notification reports **PR opened / mergeable / checks-passed** for a
   delegation this session itself armed, the orchestrator's very next
   action (same turn the notification lands in, never deferred) is:
   verify (read the PR diff/checks — the same acceptance judgment a human
   approver would apply, reusing `/orchestrate:run` step 6's existing
   relay-action definitions rather than inventing new verify criteria) →
   `gh pr merge` → re-run build/run against the now-updated default
   branch (the same `driver.run_build`/`run_version_check` shape the
   harness itself already uses, so "rebuild/re-check" is not a new
   concept, just applied by the orchestrator too) → emit the 4-part
   `final_report` (`what_broke`/`what_changed`/`what_became_possible`/
   `what_limits_remain`) as the reply text. This is a same-session,
   notification-driven continuation — #829/#835/#782 unchanged, only
   `directive.sh`'s post-notification branch is new.

2. **Headless (`claude -p`) invocation — the shape #776's own driver
   actually exercises.** No in-process mechanism can complete this case;
   the survey's citation is unambiguous that the process is gone by the
   time the delegated PR is ready. The one reuse-eligible primitive that
   actually reaches across that gap is `--resume`/`--continue` session
   chaining (survey citation, scout-brief), which is EXTERNAL to the
   orchestrator's own process by construction — something outside it has
   to notice readiness and re-invoke. That "something outside it" must
   still be the existing dual-channel poll (#782), not a new mechanism:
   whatever process already runs `spawn.py watch`/`roster_watchdog`
   ground-truth checks (a real interactive install's OS-level watchdog,
   or — for measurement — the harness driver itself) is also the natural
   place to capture the orchestrator's `session_id` at spawn time and,
   once its poll observes the delegated PR is ready, run `claude -p
   "<the delegated PR #N is ready — verify, merge, rebuild, and report>"
   --resume "$session_id"`. The resumed turn does the same
   verify→merge→rebuild→report sequence as case 1. This composes with,
   rather than replaces, #829/#835/#782 — it adds one field (`session_id`)
   and one action at an EXISTING poll tick (resume-invoke) instead of the
   current tick's sole action (re-arm-watchdog).
   **Ownership caveat, not per-entry** (after-proposal hunt finding,
   `docs/issue-878/reports/product-discovery/hunt-2026-08-11-async-completion-drive.md`):
   unlike PID/branch, `session_id` is a property of the single
   orchestrator PROCESS that did the spawning, not of each spawned role —
   one orchestrator turn routinely delegates more than one role (the
   roster already supports N concurrent entries per issue by role name),
   and every such entry shares the identical `session_id`. Reusing
   `roster_watchdog`'s existing per-tick loop unchanged (spawn.py
   lines ~2241-2325, iterates entries independently with nothing tying
   two entries back to "same session") would let two entries that become
   ready in the same poll window each fire their own
   `--resume "$session_id"`, racing two turns against one session. The
   resume action must therefore be keyed and claimed at `session_id`
   granularity, not entry granularity: one session_id-scoped atomic
   claim (the same check-and-stamp pattern `spawn.py poll-due` already
   uses for its TTL, reused as the locking primitive rather than
   invented fresh) gates the resume-invoke so only the first ready entry
   under a given session_id triggers it; entries that become ready
   afterward are folded into the SAME resumed turn's nudge text (a
   merged "PRs #N, #M are ready") instead of triggering a second
   `--resume`.

3. **Harness measurement (`harness/driver.py` + `harness/signals.py`),
   so #1/#4 reach a real PASS.** The driver must stop observing the gap
   after the fact (as run5's own account shows it doing) and instead
   drive past it, using exactly the case-2 mechanism above since the
   harness itself launches `-p`: capture `session_id` from the first
   `claude -p --output-format json` run's result; poll ground truth
   (`gh pr view`, reusing the same check run5 already performs manually)
   on a bounded interval/timeout; on readiness, invoke `claude -p
   --resume "$session_id" "<nudge>"`, capture ITS result as the
   transcript's `final_report`; append `resume`-shaped entries to
   `transcript["delegation_events"]` so `check_orchestration_to_completion`
   sees the true multi-turn shape, not a single-turn stub. If the poll
   times out before the PR is ready, or `--resume` itself fails (e.g. the
   documented capability is unavailable on the harness's host), the
   driver marks that run's transcript so `signals.py` returns UNMEASURED
   with the reason recorded — never fabricating a `final_report`. This
   makes #1/#4 a real, mechanically-checked PASS: the signal functions
   themselves (`harness/signals.py:27-36`, `61-71`) already only return
   PASS when `final_report`'s 4 parts are genuinely present, so the fix
   is entirely in what the driver constructs and feeds them, not in
   loosening the check.

**Rejected alternative A — extend the Monitor (#835) or watchdog
(#829/#782) shell scripts themselves to call `gh pr merge` directly, no
LLM turn involved.** Rejected: merge/verify is a judgment (does this PR
actually satisfy the delegated requirement, are its checks the right
checks) that this repo's own contract already treats as requiring a
reasoning turn (`directive.sh`'s existing relay-action framing,
`/orchestrate:run` step 6) — mechanizing it into a shell script would
silently drop the acceptance judgment the whole delegation model depends
on, and would duplicate merge-decision logic outside the one place
(`directive.sh`) that already owns it.

**Rejected alternative B — route delegation through Agent-tool subagents
instead of `spawn.py`'s OS-process model, to benefit from the ~10-minute
background-wait ceiling documented for backgrounded agents in `-p` mode
(scout-brief citation).** Rejected: a role's real fix-and-test cycle
(run5's own delegated role took 16 turns end to end) routinely exceeds
any single-digit-minute ceiling, and re-architecting `spawn.py`'s
cross-repo, cross-workspace delegation model is a far larger change than
this issue's own scope — noted here only because the scout pass surfaced
it as a real but inapplicable lever.

**Rejected alternative C — have the harness driver poll and act on the PR
itself (merge it, run build/run) without ever resuming the orchestrator
session.** Rejected: this would make #1/#4 (`orchestration_to_completion`,
`autonomous_completion_reporting`) pass on the DRIVER's actions, not the
orchestrator's own — exactly the false-PASS shape #878's own Acceptance
explicitly forbids ("never a false PASS"). The resumed-session `final_report`
must come from the orchestrator's own turn for the signal to mean what it
claims to mean.

## What will be done

- `on-the-record/hooks/directive.sh`: one new paragraph, same
  `CLAUDE_ROLE`-unset gate as the existing four, stating the
  verify→merge→rebuild/re-check→report sequence that fires the moment a
  `watch --follow` (or a resumed-turn nudge, case 2/3) reports the
  delegated PR ready — explicitly framed as the completion half of the
  #699 R3 goal loop already documented there (delegate → integrate →
  continue → report), not a new loop.
- `spawn.py`: capture and persist `session_id` per roster entry at spawn
  time (mirroring the per-entry tracking `roster_watchdog` already does
  for PID/branch), plus a SEPARATE session_id-keyed atomic claim (per the
  ownership caveat above — `session_id` is process-scoped, not
  entry-scoped) that serializes the resume-invoke action across every
  entry sharing one `session_id`. Add the resume-invoke action to the
  existing poll tick path (`poll_rearm_arm_if_due`/`roster_watchdog`) for
  the headless case — gated so it only fires when a `session_id` was
  actually captured (never for an interactive session, which uses
  case-1's live notification instead) and only once per claimed
  `session_id` per readiness window.
- `harness/driver.py` + `harness/signals.py`: the driver captures
  `session_id`, polls ground truth, resumes via `--resume`, and feeds the
  resumed turn's `final_report` (or an explicit UNMEASURED-reason marker
  on timeout/unavailable) into the transcript dict `signals.py` already
  consumes unchanged.
- `docs/handbooks/`: a short handbook page stating the interactive-vs-
  headless split above, the `session_id` capture point, and the hard
  boundary that a `-p` process's own end_turn is unrecoverable in-process
  (so future proposals do not re-attempt case-1's mechanism for case 2).
- This survey and this proposal (already phase-1 output).

## Out of scope

- Implementing any of the above — that is #878 step 2, gated on human
  approval of this proposal per contract v3 s19.
- Redesigning `/orchestrate:run` step 6's verify/relay-action criteria —
  reused as-is; not re-litigated here.
- The Agent-tool-subagent delegation model (Rejected alternative B) —
  noted, not designed.
- Re-running the #776 harness — that is #878 step 3
  (execution-observation), after step 2 lands.

## Accumulation

`directive.sh` already carries four standing paragraphs (base flow, #699
R2, #699 R3, #803's pending deviation-loop addition) re-injected on every
prompt of every plain session. This proposal's one paragraph would be the
fifth — the point the #803 proposal's own Accumulation section already
flagged as needing a consolidation pass (folding the norms into one
tighter block, or moving less-frequently-relevant ones to a lazily-loaded
reference). Step 2 of this issue should do that consolidation pass
alongside adding this paragraph, rather than landing a fifth
freestanding addition and deferring the flagged cost again.

## How you'll know it worked

- This proposal, once approved, gates #878 step 2 (implementation).
- Step 2's success check (step 3, execution-observation): a fresh #776
  harness re-run shows `orchestration_to_completion` and
  `autonomous_completion_reporting` moving from baseline FAIL to a real
  PASS — merged PR, rebuilt/re-checked default branch, genuine 4-part
  `final_report` traced to an actual resumed/notified turn, not a
  driver-fabricated one — OR, where the loop genuinely cannot complete
  (e.g. `--resume` unavailable on the harness host), UNMEASURED with the
  reason recorded, never a false PASS. Registered below as the
  pre-committed hypothesis, applied mechanically at step 3.

## Pre-registration (for step 3's future measurement)

We believe the interactive-notification + headless-resume split above,
once implemented, lets the orchestrator self-drive #877/run5's exact
scenario (issue → delegate → PR → merge → report) to completion with no
human turn.

- **Primary metric**: `harness/signals.py::check_orchestration_to_completion`
  and `check_autonomous_completion_reporting` on a #776 harness re-run.
- **Guardrail metric**: zero autonomous merges of a PR that is not
  actually `MERGEABLE` with passing checks — i.e. the verify step must
  reject and hold, not merge-then-discover, checked by asserting the
  transcript's merge action is always preceded by a passing
  verify-checks read in the same turn. A primary PASS reached by merging
  an unverified/failing PR is a reduced-trust result, not a win.
- **Threshold**: primary metric moves from the #776 baseline's FAIL to a
  real PASS (as defined above); guardrail shows zero unverified-merge
  events across the run.
- **Decision rule**: both PASS at step 3 → validated, proceed. Primary
  PASS but guardrail breach → invalidated, the verify step needs
  tightening before this ships as default-on. Primary still FAIL (or
  UNMEASURED because `--resume` is genuinely unavailable) → invalidated
  or re-scoped per the reason recorded, re-open this design rather than
  loosen the signal check.
- **ITWWS follow-up** (if this works we should ...): fold this same
  verify→merge→rebuild→report sequence into #803's deviation-loop FILE
  case (the "when the fix lands (PR merged), the session appends a
  `resolved` line" step that proposal already names but does not yet
  mechanize) — #803 and #878 converge on the identical completion problem
  from two different entry points (a self-filed deviation vs. an
  originally-delegated requirement) and should not grow two separate
  merge-and-report mechanisms.
