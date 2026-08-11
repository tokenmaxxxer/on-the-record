---
decision_id: issue-831-setup-preflight-remote-gate
outcome: accepted
---

# issue-831 architecture report

Phase 2, per role-handoff contract v3 s19. Approved 2026-08-11
(`APPROVE issue-831/architecture`, single-account mode).

loop_state: done

## What was done

canonical: `docs/issue-831/decisions/2026-08-11-setup-preflight-remote-gate.md` (this session)
Wrote the ADR specifying the concrete mechanism direction (c) from the
phase-1 proposal — a new `ensure_target_remote()` preflight gate in
`spawn.py`, called before any role-spawning dispatch.

canonical: `docs/issue-831/decisions/2026-08-11-setup-preflight-remote-gate.md` "Decision" section (this session)
That gate offers/confirms one-time remote setup at the top-level
attended conversation.

canonical: `docs/issue-831/decisions/2026-08-11-setup-preflight-remote-gate.md` "Consequences" section (this session)
The gate never lets a headless or nested call reach `issue_workspace`'s
hard-exit mid-run. This report restates that decision at report level
and specifies the two #776 harness scenarios in measurable terms.

No code — architecture's write scope for this issue is
`docs/issue-831/decisions/**` and this record; `spawn.py` and
`harness/**` changes are implementation-role follow-up.

## Why / upstream basis

canonical: `docs/issue-831/proposals/2026-08-11-no-remote-graceful-setup.md` (read this session)
issue #831 step 2 asked architecture to design the concrete mechanism
recommended by the merged phase-1 proposal (direction (c)): wire the
setup.md-documented install-time offer to `spawn.py::issue_workspace`'s
actual enforcement point (`spawn.py:4328-4330`), so a role session never
stalls mid-delegation on a missing remote, without silently
auto-provisioning.

canonical: `docs/issue-831/reports/architecture/survey.md` (this session)
Upstream: `docs/issue-831/reports/product-discovery/survey.md` and
`scout-brief.md` (phase-1, product-discovery role), the phase-1
proposal, and this session's own `docs/issue-831/reports/architecture/survey.md`
(architecture role's own re-read of `spawn.py`'s dispatch structure and
`docs/issue-776/reports/execution-observation.md`).

## Context

canonical: `docs/issue-831/reports/architecture/survey.md` "Findings" section (this session)
`issue_workspace()` only fires on calls carrying `--issue` (spawn.py:4750)
— #830's transcript shows the top-level headless session's FIRST
`spawn.py implementation` call (no `--issue`) succeeded without ever
reaching the remote check; only the SECOND call (with `--issue`, doing
the actual tracked delegation) hit `issue_workspace`'s unconditional
`sys.exit`.

canonical: `docs/issue-776/reports/execution-observation.md` row #1 and its "Launch command" citation (read this session)
That top-level session was itself headless and single-shot
(`env -u CLAUDE_ROLE claude -p ...`, no synchronous human able to answer
within the process), so the resulting `sys.exit` message — phrased as a
question to an operator — is a directly observed req#5
(`check_problems_not_pushed_back`) FAIL, not a simulated one.

canonical: `spawn.py:3952-3953`, `spawn.py:3798` (read this session)
`main()` already threads an `a.unattended` flag through every
role-spawning call (→ `spawn_cmd()`'s `TOKENMAXXXER_UNATTENDED` env) —
this is the codebase's existing, harness-scriptable signal for "no human
present to answer," used nowhere else.

canonical: `docs/issue-831/reports/architecture/survey.md` "Findings" section (this session)
It survives a scripted-stdin harness invocation where TTY detection
would not (a piped confirmation still has `isatty() == False` even when
the scenario intends to simulate an attended session).

## Decision

canonical: `docs/issue-831/decisions/2026-08-11-setup-preflight-remote-gate.md` "Decision" section (this session)
Full decision, alternatives, and line-cited rationale in the ADR.
Summary: a new `ensure_target_remote(cwd, unattended)` preflight, called
from `main()` right after argument parsing, before the two dispatch
branches that can reach `issue_workspace` (`drive`, and the bottom-of-
`main()` bare-spawn fallback).

canonical: `docs/issue-831/decisions/2026-08-11-setup-preflight-remote-gate.md` "Decision" section, step 1-2 (this session)
If `origin` already resolves, no-op (steady state unaffected). If it
does not resolve and `unattended` is `True`, fail fast with a
pre-delegation message — before any rulebook checkout or role session is
spawned, instead of after.

canonical: `docs/issue-831/decisions/2026-08-11-setup-preflight-remote-gate.md` "Decision" section, step 3 (this session)
If it does not resolve and `unattended` is `False` (the default — this
is the attended top-level conversation `setup.md` already documents),
print the existing documented offer, read a confirmation via `input()`,
run the corresponding `gh repo create --private --source . --push` or
point-at-existing-remote command on confirmation.

canonical: `spawn.py:3475` (`ledger_write`), read this session
Write a `ledger_write({"event": "remote_setup_confirmed", ...})` record
— the same `ledger_write` mechanism `_spawn_one` already uses for its
`returned_pr_gate_*` events.

canonical: `docs/issue-831/decisions/2026-08-11-setup-preflight-remote-gate.md` "Decision" section, step 3 (this session)
So the harness (and any later reviewer) can distinguish "asked once,
confirmed" from a remote that appeared with no recorded consent event.

canonical: `spawn.py:4328-4330` (`issue_workspace`), read this session
`issue_workspace`'s existing hard-exit is untouched, remaining the
fail-closed backstop for the explicitly out-of-scope residual (a remote
removed between a confirmed setup and a later spawn).

## Consequences

- `spawn.py` needs the new `ensure_target_remote()` function and its two
  `main()` call sites (implementation-role follow-up, listed below).
- `harness/signals.py` needs a new check reading the
  `remote_setup_confirmed` ledger event to score the no-remote scenario;
  its absence alongside a resolved `origin` is the new FAIL condition the
  phase-1 proposal named ("silently auto-provisioned with no confirmation
  event in the transcript").
- `harness.driver`'s `instantiate_fixture_target` needs a launch-actor
  parameter (top-level attended vs bare role spawn) per the scenario spec
  below — today's fixture always launches a bare role/headless
  invocation, which is exactly the wrong-actor-boundary shape the phase-1
  survey diagnosed.
- `docs/handbooks/setup.md`'s existing prose needs no wording change —
  the offer text it already documents is what `ensure_target_remote`
  prints and executes on confirmation.

## Alternatives considered

canonical: `docs/issue-831/decisions/2026-08-11-setup-preflight-remote-gate.md` "Alternatives considered" section (this session)
- **`sys.stdin.isatty()` instead of `--unattended`** — rejected: a
  scripted harness confirmation pipes stdin, making `isatty()` false even
  when the scenario deliberately simulates an attended session; it would
  misclassify the harness's own no-remote scenario as unattended.
- **Wire the offer inside `issue_workspace` itself** rather than an
  earlier `main()`-level gate — rejected: `issue_workspace` is reached
  only by `--issue`-carrying calls (spawn.py:4750); a no-`--issue` call,
  exactly like #830's first successful delegation call, would never
  trigger the offer, leaving the same class of gap this ADR closes.
- **Candidates (a) self-provision with no consent and (b) local-only
  degraded mode** — already rejected at the phase-1 proposal stage
  (RICE table); not re-litigated here.

## Harness scenario spec (#776), measurable form

canonical: `docs/issue-831/proposals/2026-08-11-no-remote-graceful-setup.md` "Harness measurement" section (read this session)
Both scenarios extend `harness.driver.instantiate_fixture_target`, per
the phase-1 proposal's scenario shape — this report pins the scenarios
to the concrete mechanism above so #1/#4/#5 become measurable rather
than UNMEASURED/FAIL.

1. **Steady-state (remote present).** `instantiate_fixture_target` seeds
   a real or local-bare-repo-stand-in `origin` before the representative-
   requirement session launches. `ensure_target_remote` no-ops on every
   call (`git remote get-url origin` resolves at step 1 of the gate).
   Assertion: the run reaches the same delegation depth #830 reached (a
   `--issue`-carrying `spawn.py implementation` call) and continues past
   it to a completed `final_report`, `human_input_stalls` empty, no
   `remote_setup_confirmed` ledger event expected (setup was never
   needed) — req#1/#4/#5 all measurable and PASSing.
2. **No-remote graceful-degrade.** `instantiate_fixture_target` seeds NO
   `origin` (today's existing fixture behavior). The harness launches the
   *orchestrator's own top-level conversation* WITHOUT `--unattended`
   (simulating the attended moment `setup.md` documents — not a bare
   headless role spawn the way #830's fixture did) and scripts stdin
   with the confirmation answer (`y` plus, if pointing at an existing
   remote, a URL) for `ensure_target_remote`'s `input()` prompt.

   canonical: `docs/issue-831/proposals/2026-08-11-no-remote-graceful-setup.md` "Harness measurement" section (read this session)
   Assertions, all against the transcript/ledger:
   - `ensure_target_remote` fires before the first role-spawning call
     (a `remote_setup_confirmed` ledger event's timestamp precedes any
     `_spawn_one`/`issue_workspace` log line).
   - `git remote get-url origin` resolves afterward.
   - the subsequent delegation proceeds with `human_input_stalls` empty
     at the `issue_workspace` gate specifically — distinguishing "asked
     once, at setup, and proceeded" (PASS) from #830's "stalled
     mid-delegation with no remote" (FAIL, today's behavior) and from a
     new FAIL condition: `origin` resolves but no `remote_setup_confirmed`
     ledger event precedes it (a silent auto-provision — candidate (a)
     sneaking back in per the phase-1 proposal's own naming of this
     failure mode).

   canonical: `docs/issue-831/reports/architecture/survey.md` "Gap this survey narrows for the mechanism design" section (this session)
   - a variant with `--unattended` passed and no `origin` seeded asserts
     the fast pre-delegation `sys.exit` (residual fail-closed path)
     fires before any rulebook checkout or role spawn — i.e. cheaper
     than #830's failure, not a new success case.

canonical: `docs/issue-831/proposals/2026-08-11-no-remote-graceful-setup.md` "Harness measurement" section (read this session)
Both scenarios reuse `harness/signals.py`'s existing
`check_problems_not_pushed_back` and `check_orchestration_to_completion`
unmodified, per the phase-1 proposal — only `instantiate_fixture_target`
(launch-actor + scripted-stdin support) and one new ledger-event check
need new code.

## C4 container diagram

```
+--------------------------------------------------------------------+
|                    on-the-record plugin (spawn.py)                 |
|                                                                      |
|  main()  parse_args()                                               |
|     |                                                                |
|     v                                                                |
|  ensure_target_remote(cwd, unattended)   <-- NEW, this ADR           |
|     |            |                    |                             |
|     | resolves   | !resolves          | !resolves                   |
|     | (no-op)    | unattended=False   | unattended=True              |
|     v            v                    v                             |
|   dispatch    offer + input()      sys.exit                         |
|   continues   confirm -> gh/git    (pre-delegation,                 |
|               remote command       fail fast)                       |
|               ledger_write(                                         |
|                "remote_setup_confirmed")                            |
|                    |                                                |
|                    v                                                |
|               dispatch continues                                    |
|                    |                                                |
|                    v                                                |
|         drive() / bare-spawn -> _spawn_one()                        |
|                    |                                                |
|                    v  (only if --issue)                             |
|            issue_workspace()   <-- UNCHANGED, existing hard-exit    |
|            (fail-closed backstop: remote removed after setup,       |
|             out of scope for this issue)                            |
+--------------------------------------------------------------------+
```

No new container. The boundary this decision touches is entirely inside
`spawn.py`'s existing `main()` dispatch layer — one new call edge before
the two dispatch branches that can reach `issue_workspace`, which itself
is unchanged.

## What did not work

None.

## Open findings

None new.

## Hand-off

Implementation-role session, one branch (`issue-831/implementation`),
per contract v3. Scope: `ensure_target_remote()` in `spawn.py` and its
two `main()` call sites; the `remote_setup_confirmed` ledger-event check
in `harness/signals.py`; the launch-actor + scripted-stdin support in
`harness.driver.instantiate_fixture_target`; the two new #776 fixture
scenarios per the spec above. Architecture's role in this issue ends
here.
