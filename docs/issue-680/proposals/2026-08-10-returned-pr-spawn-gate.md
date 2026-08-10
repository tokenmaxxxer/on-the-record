---
status: proposed
files:
  - spawn.py
  - test_spawn.py
---

## Request

`spawn.py <role> ... --issue N` currently spawns unconditionally. Make it
refuse when other `issue-*/**` PRs on the target repo are open and
undispositioned (no phase-1 approval token, or a phase-2 PR not yet
merged/closed) and the new spawn doesn't itself address one of those
issues. Add `--despite-returned` to override, recording the bypass in the
ledger. Decide fail-open vs fail-closed on a `gh` lookup failure at the
gate, with rationale.

## Constraints

- Disposition read must come from observable GitHub state (`gh pr list` /
  issue comments), never conversational memory or roster state.
- Refusal exits nonzero and lists each blocking PR with its issue number
  and phase (proposal vs delivery).
- Spawn allowed when the open PR belongs to the same issue being
  progressed, or when all open role PRs are dispositioned.
- `--despite-returned` bypasses refusal and writes a ledger event.
- No new dependency, no new environment variable, no schema/migration.
- Empty state (no open `issue-*/` PRs) passes silently.

## Rationale

**Reuse over reinvention:** the disposition predicate is not new logic —
`gates/ci.py._approved_roles_on_issue` already answers "has this issue's
phase-1 been approved" (an `APPROVE issue-<n>/<role>` comment from an
approvers.md login), and `gh pr list --state open` already answers
"is this PR still open" (merged/closed PRs simply drop out of that list).
The gate composes these two existing predicates rather than adding a
third notion of "disposition." Alternative considered and rejected:
writing a fresh disposition check directly against issue comments/PR
state inside the new gate function, duplicating what
`_approved_roles_on_issue` already does. Rejected because two divergent
implementations of "is phase-1 approved" is exactly the kind of drift
that produces the silent-inconsistency bugs this repo's own contract
tooling (`gates/ci.py`) was written to prevent — one predicate, reused.

**Fail-open on `gh` failure, with a loud warning and a ledger note.**
Alternative considered and rejected: fail-closed (refuse every spawn
whenever the `gh` lookup errors). Rejected because this gate runs on
*every* `spawn.py ... --issue N` invocation — the routine, frequent path
— not on a single deliberate action like `gh pr merge`
(`on-the-record/hooks/contract-guard.sh`, which itself chose fail-open
for exactly this reason: "gh/network failures are common in sandboxed
sessions" and blocking an unrelated action on a lookup failure is worse
than passing it through). Fail-closed here would make spawn.py globally
unusable during any `gh` flakiness or auth hiccup, which is a materially
larger availability cost than the risk it's guarding against (a
returned-PR pipeline stall that already has a Stop-side backstop in
`decision-queue-stopgate.sh`). Fail-open is not silent, though: a `gh`
failure at the gate prints a clear warning to stderr identifying which
lookup failed, and writes a `returned_pr_gate_fail_open` ledger event
(mirroring the `--despite-returned` bypass event) so the bypass is
auditable even when unattended — this closes the gap that would
otherwise make fail-open indistinguishable from "no gate at all" in the
ledger's own record.

## What will be done

- Add `_open_role_prs(root) -> tuple[list[dict], bool]` to `spawn.py`,
  next to the existing `_pr_comments`/`_repo_slug` helpers: runs
  `gh pr list --state open --json number,headRefName,body,url` against
  the target repo (via `_repo_slug`), filters to `headRefName` matching
  `issue-(\d+)/`, and returns `(prs, ok)` — `ok=False` on any `gh`
  failure, following the existing `_pr_comments` return-shape
  convention.
- Add `_undispositioned_role_prs(root, exclude_issue=None) ->
  tuple[list[dict], bool]`: for each PR from `_open_role_prs`, determine
  phase (phase-1 proposal vs phase-2 delivery — same predicate spawn.py
  already uses at :1018-1020: `_ci._approved_roles_on_issue` populated
  means phase-2 in flight) and disposition (phase-1: approved via
  `_approved_roles_on_issue`; phase-2: not open — already excluded by
  construction, since only open PRs are listed, so every phase-2 PR
  reaching this function is by definition undispositioned). Skips PRs
  whose issue number equals `exclude_issue`. Returns `(blockers, ok)`
  with the same `ok` propagation as `_open_role_prs`.
- Wire the check into `_spawn_one` itself (spawn.py ~4109-4150), not only
  into `main()`'s argparse dispatch: the auto-respawn path
  (`_auto_respawn_check`/`_self_trigger_respawn` -> `_respawn_or_cap` ->
  `_spawn_one`, spawn.py:2570-2648) calls `_spawn_one()` directly,
  bypassing `main()`'s dispatch entirely (found by the after-proposal
  warrant hunt — docs/reports/2026-08-10-hunt-returned-pr-spawn-gate.md).
  Gating only at `main()` would leave every auto-respawn ungated. When
  `issue` is set and `_spawn_one` is entered, call
  `_undispositioned_role_prs(root, exclude_issue=issue)` before the
  fork. On `ok=False` (gh failure): print the fail-open warning to
  stderr, `ledger_write` the `returned_pr_gate_fail_open` event, and
  proceed. On `ok=True` with non-empty blockers and no
  `--despite-returned`: print each blocker as `issue #N (phase-1|
  phase-2): <PR url>`, `ledger_write` a `returned_pr_gate_refused` event,
  exit nonzero without spawning. With `--despite-returned` set and
  blockers present: `ledger_write` a `returned_pr_gate_bypassed` event
  (listing the bypassed issue numbers) and proceed.
- Add `ap.add_argument("--despite-returned", action="store_true", ...)`
  next to the other spawn flags in `main()`.
- `test_spawn.py`: add a `ReturnedPrGate`-suffixed test class per the
  issue's named `pytest -k "ReturnedPrGate"` filter, covering: refusal
  when an undispositioned `issue-*/` PR exists for a different issue;
  allowed when the open PR belongs to the same issue being progressed;
  allowed when all open role PRs are dispositioned; empty-state pass
  (no open `issue-*/` PRs); override flag bypasses and writes a ledger
  event; `gh` failure fails open with a printed warning and a ledger
  event. `gh` calls mocked via the existing `subprocess.run`-patching
  pattern already used elsewhere in `test_spawn.py`.

## Accumulation

This adds one more inline `gh` subprocess call site to `spawn.py`
(`_open_role_prs`), alongside the ~6 already there (`_repo_slug`,
`_pr_comments`, the per-branch `gh pr list` calls at :1075/:1090/:1122/
:2486/:4109). If a future issue adds another `gh`-backed gate at this
call frequency, the file accretes another near-identical
`subprocess.run(["gh", ...])` + `(result, ok)`-tuple block; at roughly
N=10 such sites the existing convention (return `(data, ok)`, let the
caller decide fail-open/fail-closed) is still legible per-site but starts
to warrant one shared `_gh_json(args) -> tuple[Any, bool]` wrapper. This
proposal does not add that wrapper now — the existing sites already
tolerate this shape (see `_pr_comments`'s docstring at spawn.py:1140-1166
explaining why the tuple exists), and one more site does not cross that
threshold — but a `_gh_json` extraction is the identified follow-up if a
third or fourth similar gate lands after this one.

## Out of scope

- Cross-repo aggregation of returned PRs (explicitly out of scope per
  the issue).
- Changing `decision-queue-stopgate.sh`'s Stop-side behavior — it stays
  the backstop for orchestrators that never spawn.
- Any change to how phase-1 approval or phase-2 merge/close is detected
  beyond reusing `_ci._approved_roles_on_issue` and `gh pr list`'s open/
  closed state as-is.

## How you'll know it worked

`python3 -m pytest test_spawn.py -k "ReturnedPrGate"` passes, covering
the four acceptance-criteria cases plus the empty-state and gh-failure
cases named above. Manual check: `spawn.py <role> ... --issue N` on a
repo with an open, unapproved `issue-M/` PR (M != N) exits nonzero and
prints the blocking PR; `--despite-returned` bypasses and a
`returned_pr_gate_bypassed` line appears in `runs/ledger.jsonl`.
