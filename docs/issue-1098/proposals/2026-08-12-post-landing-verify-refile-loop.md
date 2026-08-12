---
status: proposed
files:
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/post-landing-obligation-gate.sh
  - on-the-record/hooks/test_post_landing_obligation_gate.py
  - gates/landing_obligation.py
  - gates/test_landing_obligation.py
  - gates/landing_readiness.py
  - gates/test_landing_readiness.py
  - docs/handbooks/hooks.md
  - docs/issue-1098/decisions/2026-08-12-post-landing-obligation.md
---

## Intent

Requirement (northpole req#3, req#5): after a landing, verification and
refiling of found defects must become the default next step of any
installed session, with no operator prompt required each round. Right
now that loop only happens because an orchestrator remembers to run it
by hand (issue #1098 body, provenance list of PRs #1086/#1091/#1093/
#1095/#1085/#1088/#1097).

## Constraints already stated by the issue

- No CI, no explicit skill invocation (req#7) — plugin-side hooks/
  gates/directive text only.
- Do not duplicate #892, `reexecution_gate.py`, `landing_readiness.py`,
  `closure_sweep.py`, `roles_due.py`, or the Monitor watchdog — wire
  them together.
- Empty state must stay quiet: a landing whose verification passes must
  not create an extra issue.

## What will be done

1. **`on-the-record/hooks/post-landing-obligation-gate.sh`** — a new
   `PostToolUse` (`Bash`) hook, registered in `hooks.json` alongside the
   existing `retry-loop-bound.sh post` entry (same matcher,
   `Write|Edit|MultiEdit|Bash`, already covers `gh pr merge`; survey
   confirmed this array has exactly one entry today). It inspects
   `tool_input.command`/`tool_response` the same strict way
   `merge-allow-gate.sh` already tokenizes `gh pr merge` calls
   (reusing that file's shlex-based command-shape check rather than a
   new regex), and only on a *successful* `gh pr merge` for a
   resolvable PR number does it act. Its one action: write a
   verification-obligation record via `gates/landing_obligation.py`
   (below) — never blocks, never denies (`PostToolUse` cannot deny
   anyway); this keeps the hook itself pure side-effect, no judgment.

2. **`gates/landing_obligation.py`** (new module, same shape as
   `reexecution_gate.py`) — `open_obligation(repo, issue, role, pr,
   sha)` writes `.landing-obligations/<issue>-<role>-<pr>.json`
   (`{status: "open", pr, sha, issue, role, opened_at}` — mirrors
   `reexecution_gate.Verdict`'s dataclass-to-JSON shape). Two more pure
   functions: `resolve_with_reexecution_verdict(repo, issue, role)` —
   reads `.reexecution/<issue>-<role>.json` the same way
   `landing_readiness.reexecution_blocking_cause` already does, and
   flips the obligation's `status` to `"resolved"` when a `pass`
   verdict for that issue/role post-dates the obligation's `opened_at`,
   or to `"failing"` on a `fail`/`error` verdict (so the loop's step 1
   — "verified by actually running the changed behavior" — composes
   with #892/`reexecution_gate.py` instead of re-implementing
   execution); `list_open_obligations(repo)` for the classifier below.
   No obligation is ever silently deleted — `"resolved"` keeps the
   record (auditable), it just stops blocking.

3. **`gates/landing_readiness.py`** gets one new pure function,
   `obligation_blocking_cause(root, issue, role, pr)`, same shape as
   the existing `reexecution_blocking_cause` (gates/landing_readiness.py:56-70):
   an `"open"` or `"failing"` obligation for that PR's own issue/role
   becomes a `blocking_causes` entry scoped to that PR's own record path
   (`docs/issue-<n>/reports/<role>.md`), exactly the same scoping fix
   #398/ADR §6 already established for the reexecution cause — never a
   `gates/`-prefix scope that would over-cover unrelated PRs. `classify`
   itself is untouched; only a new caller composes one more cause into
   the existing list.

4. **Refiling composes with `roles_due.py`, not a new filer.** Step 2 of
   the loop ("register on the spot as a structural root-cause issue")
   is deliberately NOT a new issue-creation code path in this proposal
   — `roles_due.py`'s existing `use_when.trigger` mechanism already
   routes a specialist role when a board condition matches; a
   `"failing"` obligation is exactly such a condition. This proposal
   adds one `roles/specs/*.spec.json` trigger shape (in a follow-up,
   scoped separately, since editing `roles/specs/*.spec.json` content
   is outside this write set) rather than teaching this new module to
   call `gh issue create` itself — keeping "who is allowed to file"
   answered in exactly one place (`roles_due.py`'s existing
   spawn-routing path), per the survey's read of that module.

5. `docs/handbooks/hooks.md` gets a new section documenting the hook
   (same doc-per-hook convention every other entry in that file
   follows).

6. `docs/issue-1098/decisions/2026-08-12-post-landing-obligation.md` —
   the ADR (context/decision/consequences/alternatives-considered)
   this role's YOU-DECIDE directive requires for a new component
   boundary, plus a C4 context/container sketch of the four pieces
   above and how they compose with the four pre-existing ones named in
   the issue.

## Alternatives considered

- **A `Stop` hook instead of `PostToolUse`.** Rejected: `Stop` fires at
  session end regardless of whether a merge happened this session, so
  it cannot cheaply scope "did a landing just happen" without
  re-deriving the same `gh pr merge` detection `PostToolUse` gets for
  free from the tool-call boundary.
- **Teach `reexecution_gate.py` itself to auto-run on landing.**
  Rejected: `reexecution_gate.py`'s `run_reexecution` shells out to an
  arbitrary `--command`; a `PostToolUse` hook has no safe way to know
  *which* command that landing's role should re-run without a role-spec
  lookup that belongs in `roles_due.py`'s existing trigger mechanism,
  not duplicated inline in a hook script. Keeping obligation-creation
  and obligation-resolution as two separate steps (open now, resolve
  when `reexecution_gate.py` is later invoked by whatever already
  invokes it) avoids that duplication.
- **A board-wide sweep gate (`closure_sweep.py`-shaped) instead of a
  per-PR hook.** Rejected as the sole mechanism: it would still need a
  trigger to run automatically (the exact gap this proposal closes),
  and would detect the obligation only on the next sweep, not at
  landing time — worse detection latency than the scouted field's own
  must-be (attach to the event, not a poll).

## Out of scope

- The `roles/specs/*.spec.json` trigger wiring for step 2's actual
  issue-filing routing (separate proposal/write-set; this one only
  adds the obligation state the trigger would key on).
- Changing `reexecution_gate.py`'s own execution logic.
- Any CI workflow file (explicitly excluded, req#7).
- The harness/fixture live-smoke acceptance check named in the issue's
  Acceptance section — that is phase-2 build+test work, not proposal
  content.

## How you will know it worked

- `gates/test_landing_obligation.py` proves: opening an obligation on a
  landing, resolving it on a `pass` `reexecution_gate` verdict, keeping
  it `"failing"`/blocking on a `fail`/`error` verdict, and that a
  landing with no obligation ever opened stays silent (empty-state
  requirement).
- `gates/test_landing_readiness.py` gains a case proving
  `obligation_blocking_cause` scopes to the owning PR's own record path
  only, never a board-wide `gates/`-prefix cause (mirrors the existing
  reexecution-cause regression test in that same file).
- `on-the-record/hooks/test_post_landing_obligation_gate.py` drives the
  hook script itself (subprocess, real git repo fixture, same
  convention `test_role_axis_completeness_guard.py` already uses),
  proving it only fires on an actually-successful `gh pr merge` for a
  resolvable PR, and is a no-op (exit 0, no side effect) for every
  other Bash command.
- Acceptance's live-harness smoke round is phase-2 work per the
  handoff contract; this proposal's own check is the three test files
  above.

## Open findings (after-proposal hunt)

canonical: docs/issue-1098/reports/architecture/2026-08-12-hunt-post-landing-verify-refile-loop.md
The hunt found a design gap: obligation-creation is scoped to one
tokenized `gh pr merge` Bash-command shape (mirroring
`merge-allow-gate.sh`'s own detection). A PR that reaches merged state
through any other path — the GitHub web UI, a raw REST call, another
CLI wrapper — never triggers the hook, so no obligation file is
written, and the proposal's own empty-state test criterion ("no
obligation ever opened stays silent") cannot distinguish that skipped
case from a landing whose verification genuinely already happened.

Resolution path: phase-2 build adds a second, independent detection
source alongside the `PostToolUse` command-shape trigger —
`landing_readiness.py`'s existing `_pr_list`/`gh pr list --json state`
read (gates/landing_readiness.py) already gives a per-PR merged/open
state from the API rather than from command-shape sniffing. Phase-2
should add a periodic or Stop-hook-driven reconciliation pass that
lists actually-merged PRs (via that same `gh` read) with no obligation
file on record, and treats each as `"open"` — closing exactly the gap
the hunt reproduced, without abandoning the low-latency
`PostToolUse` path this proposal keeps as the fast/default case.

## Accumulation

This proposal adds one repeatable shape: a `.{something}/<issue>-<role>-
<pr>.json` obligation-file family, the second instance of that pattern
after `.reexecution/<issue>-<role>.json`
(gates/reexecution_gate.py:verdict_path). N further post-landing
obligation classes (e.g. a future "docs-staleness obligation" or
"perf-regression obligation") would each add one more such file family
plus one more `landing_readiness.py` blocking-cause function — the same
shape repeating, not a new abstraction each time. If a third instance
appears, the next proposal touching this area should introduce one
shared `obligation_path(repo, kind, issue, role, pr)` helper in
`gates/landing_obligation.py` instead of a third copy-pasted
`*_path()` function, the same way `reexecution_gate.verdict_path` and
this proposal's own obligation path are still separate today
(two instances — below the field's own N>1-with-evidence bar this
repo's `accumulation.py` gate applies, so this proposal does not
pre-build that shared helper now).
