---
subject: issue-831
kind: adr
status: accepted
---

# ADR — top-level setup preflight replaces mid-delegation remote stall

## Context

`spawn.py::issue_workspace` (spawn.py:4328-4330) hard-exits when the
target repo's `origin` remote does not resolve (`git remote get-url
origin` returns empty), citing contract v3 s10 ("issue/PR model presumes
a GitHub remote"). This check only fires when a call carries `--issue`
(`_spawn_one`, spawn.py:4736, the `if issue is not None:` block at
spawn.py:4750) — a delegation call made without `--issue` (e.g. an
initial diagnosis-only `spawn.py implementation "..."`) never reaches
`issue_workspace` at all.

canonical: `docs/issue-776/reports/execution-observation.md` rows #1, #5, and its "Launch command" citation (`env -u CLAUDE_ROLE claude -p ...`, no `--unattended`), plus `docs/issue-831/reports/product-discovery/survey.md` (read this session)

PR #830's harness run reproduced the failure exactly this way: the
top-level session (headless `claude -p`, no synchronous human — this is
the requirement-delivery session itself, not a nested role spawn) made a
first `spawn.py implementation` call with no `--issue` (succeeded — never
touched `issue_workspace`), then a second call WITH `--issue` (to do the
actual tracked fix) that reached `issue_workspace` and hit the
unconditional `sys.exit`. Because that top-level session is headless and
single-shot (this session's own SessionStart hook text: "headless 이고
단발이다 — 세션이 끝나면 이 프로세스도 끝난다"), the `sys.exit` message —
a question addressed to an operator who cannot answer within this
process — is a direct, observed northpole req#5 FAIL
(`check_problems_not_pushed_back`), not a hypothetical.

`docs/handbooks/setup.md` ("Once, per target repo" section) already
documents the intended resolution shape: the orchestrator offers, in
conversation, to run `gh repo create --private --source . --push` or
point at an existing remote — the same pattern already used for
`docs/specs/approvers.md` and branch protection. That offer is not wired
to any code path today; nothing forces it to run, or to run before the
first role-spawning call, so a target repo can reach `spawn.py <role>
--issue N` (headless or not) with no remote and no prior offer ever
having been made.

`main()`'s existing `a.unattended` flag (spawn.py:3952-3953, threaded
into `spawn_cmd()` as `TOKENMAXXXER_UNATTENDED`, spawn.py:3798) is
already the codebase's one true signal for "no human is present to
answer a question this process asks" — it is not overloaded for
anything else, and every other CLI-level human-facing gate in this file
(`require_board`, `require_no_repo_config`) already conditions on
similar attended/unattended distinctions rather than TTY detection.

## Decision

Add one new preflight gate, `ensure_target_remote(cwd: str, unattended:
bool) -> None`, called from `main()` immediately after `a =
ap.parse_args()` and before the two dispatch branches that can reach
`issue_workspace`: the `a.role == "drive"` branch (spawn.py:4157) and the
bottom-of-`main()` fallback bare-spawn branch (spawn.py:4203-4205,
guarded the same way `require_board`/`require_doctor` already guard that
branch — i.e. skipped for `--dry-run`, matching the existing convention
that dry-run never mutates or blocks on live state). Read-only /
non-repo-scoped subcommands (`init`, `ps`, `doctor`, `update`, `watch`,
`kill`, `consult`, `closure-sweep`, `reconcile`, `approve-scope`, `flows`)
are unchanged — they either don't reach `issue_workspace` or (`init`)
are themselves part of setup.

`ensure_target_remote` behavior:

1. `git -C cwd remote get-url origin` resolves → return immediately
   (no-op). This is the steady-state path — every existing call site
   downstream (`issue_workspace`, `_origin_pr_prefix`) is unchanged.
2. Does not resolve, `unattended` is `True` → `sys.exit` immediately,
   before any role spawn is attempted (never mid-delegation), with a
   message stating plainly that the target repo has never completed
   one-time remote setup and that setup must be run once from an
   attended (non-`--unattended`) invocation first. This is the fail-closed
   residual: a headless run launched against a never-set-up repo still
   fails, but fails at the earliest possible point instead of after real
   delegated work has already happened deep in `issue_workspace` — the
   difference the #830 transcript shows costs a stalled session and
   burned tokens (`docs/handbooks/setup.md`'s installation-time offer is
   the intended venue for this to have already been resolved; this branch
   only fires when that step was skipped).
3. Does not resolve, `unattended` is `False` (the default — this IS the
   attended top-level conversation, matching `setup.md`'s existing
   documented moment) → print the same offer `setup.md` already
   documents, read a confirmation via `input()` (`y` to run `gh repo
   create --private --source . --push`, or a pasted remote URL to point
   at an existing repo, matching the CLI shape `spawn.py init` already
   uses for `--login`), then:
   - on confirmation: run the corresponding `git`/`gh` command, verify
     `git remote get-url origin` now resolves, and write
     `ledger_write({"event": "remote_setup_confirmed", "cwd": ..., "origin": ..., "ts": ...})`
     (same `ledger_write` mechanism `_spawn_one` already uses for
     `returned_pr_gate_*` events, spawn.py:3475) — an explicit,
     auditable confirmation event distinct from "origin happens to
     resolve," so a harness or a later reviewer can tell "asked once,
     confirmed" apart from a remote that appeared with no recorded
     consent.
   - on refusal/empty input: `sys.exit` with the same message as branch 2
     (no silent auto-provision, no silent skip — declining leaves the
     repo exactly where it was, and every subsequent call re-asks, since
     nothing was confirmed).

`issue_workspace`'s existing hard-exit (spawn.py:4328-4330) is
unchanged — it remains the fail-closed backstop for the explicitly
out-of-scope residual gap (a remote removed between a confirmed setup
and a later spawn). This ADR does not touch that function.

## Consequences

- The confirmation moment moves from "wherever the first `--issue` call
  happens to land, however deep in delegation" to "the very first
  role-spawning call of any kind, in the top-level conversation" —
  closing the req#4/#5 gap #830 measured, without granting any
  account-scoped action (`gh repo create`) the ability to run without a
  human answering `input()` in the same process that asked.
- A production headless full-autonomous launch (`--unattended` passed
  intentionally) against a never-set-up repo now fails in under a second,
  before any rulebook checkout, plugin resolution, or role session spawn
  happens — cheaper than #830's failure (two delegation calls, a role
  session spawned, tokens spent) and the failure message names the exact
  missing precondition instead of surfacing as a mid-run question.
- `docs/handbooks/setup.md`'s existing prose now has a concrete
  implementation to point at; no wording change needed since the
  behavior described (`gh repo create --private --source . --push` /
  point at existing) is exactly what `ensure_target_remote` runs on
  confirmation.
- New harness requirement: `harness/signals.py` needs a check for the
  `remote_setup_confirmed` ledger event (or its absence) to score the
  no-remote scenario correctly — implementation-role follow-up, listed
  in the phase-2 report's hand-off section.

## Alternatives considered

- **Detect attendedness via `sys.stdin.isatty()` instead of the existing
  `--unattended` flag.** Rejected: a scripted harness confirmation (the
  #776 scenario this issue specifies) pipes stdin, which makes
  `isatty()` `False` even when the scenario is deliberately simulating
  an attended session — it would misclassify the harness's own no-remote
  scenario as unattended and defeat the test. `--unattended` is already
  the codebase's explicit, harness-controllable signal for the same
  distinction (spawn.py:3952-3953), so reusing it needs no new detection
  logic and composes with the existing `TOKENMAXXXER_UNATTENDED` env
  plumbing.
- **Wire the offer inside `issue_workspace` itself** (prompt at the
  point of the existing check, rather than adding an earlier gate).
  Rejected: `issue_workspace` is reached by calls carrying `--issue`
  only (spawn.py:4750) — a no-`--issue` call, exactly like #830's first
  successful delegation call, would never trigger the offer, leaving the
  same class of gap (setup deferred until a `--issue` call finally
  happens, possibly headless by then) that this ADR closes by gating at
  the top of `main()` instead.
- **Candidates (a) self-provision with no consent and (b) local-only
  degraded mode.** Rejected at the phase-1 proposal stage
  (`docs/issue-831/proposals/2026-08-11-no-remote-graceful-setup.md`,
  RICE table) — restated here only as: (a) would satisfy req#4/#5 but
  violates the consent requirement this ADR's step 3 is built around;
  (b) is out of proportion to this issue's scope (redesigns the
  GitHub-native approval model). Not re-litigated in this ADR.
