---
status: approved
files:
  - on-the-record/hooks/pr-base-guard.sh
  - on-the-record/hooks/hooks.json
  - tests/test_pr_base_guard.py
  - docs/specs/generated-paths.md
  - docs/specs/enforcement-boundary.md
  - docs/specs/reconciled-index.md
  - docs/issue-1461/reports/implementation.md
---

Skip condition (survey-order-directive / scout-directive): this is a pure
bugfix/defect-hardening change — a PreToolUse gate that ports the same
zero-install inline-Python-in-heredoc shape `pr-preflight.sh` and
`contract-guard.sh` already use, with no product-facing surface or design
decision left open by the issue. Scouting and a separate survey file are
skipped per both directives' stated skip condition; this proposal's own
"## Rationale" documents the one alternative considered.

## Request

Root-cause the wrong `--base` on a `gh pr create`, then add a PreToolUse
gate that refuses `gh pr create`/REST pulls-create from a role workspace
when `--base` isn't the repo's default branch, unless the issue body names
a different base explicitly. Fail closed when the default branch can't be
resolved.

## Constraints

- Zero-install: ships with the plugin, no `gates/` checkout required in a
  consumer repo (matches `pr-preflight.sh`/`contract-guard.sh`).
- Fail-open on every unrelated lookup failure (no git, no `gh`, non-role
  branch, no `--base` flag) — only the default-branch resolution itself
  fails closed, per requirement 3.
- Tests at `tests/test_pr_base_guard.py` per Acceptance, driving the real
  hook end-to-end against a stub `gh` (same pattern as
  `on-the-record/hooks/test_pr_preflight.py`).

## Rationale

Considered porting the check as an importable `gates/pr_base_guard.py`
module with a thin bash wrapper (like `check_runner.py`-style gates)
instead of inline-heredoc Python. Rejected: every other `gh pr create`-
intercepting PreToolUse hook in this plugin (`pr-preflight.sh`,
`contract-guard.sh`) already uses the zero-install inline-heredoc shape
specifically so the hook works in a consumer repo with no `gates/`
checkout on `sys.path`; splitting this one gate into an importable module
would make it the only `gh pr create` hook that silently no-ops in a
consumer repo missing that checkout, reintroducing exactly the kind of
authoring-time gap issue #1461 is about closing.

## What will be done

- `on-the-record/hooks/pr-base-guard.sh`: new PreToolUse+Bash hook,
  registered alongside `pr-preflight.sh` in `hooks.json`'s matcher group.
  Extracts `--base` (or REST `base=`) from `gh pr create`/`gh api
  .../pulls`, resolves the repo default branch via `gh repo view --json
  defaultBranchRef`, denies when `--base` differs and the issue body names
  no explicit alternate base; denies (fail-closed) when the default branch
  can't be resolved.
- `tests/test_pr_base_guard.py`: the three Acceptance-named tests plus
  supporting cases (no `--base` flag, REST shape, non-role branch,
  explicit-alternate-base allowance).
- `docs/specs/generated-paths.md` / `docs/specs/enforcement-boundary.md`:
  register the new hook per this repo's existing spec-registration
  convention; `docs/specs/reconciled-index.md` regenerated in the same
  commit.
- Investigation note in the delivery record naming where the wrong base
  value originated, citing the incident log.

## Out of scope

- Root-causing *why* the model chose `issue-247/conformance-review`
  specifically (unrecoverable — no log captures the model's own reasoning
  for that command). The investigation note states what the log evidence
  does and doesn't show.
- Any change to `spawn.py`/gates that *compute* a `--base` value for a
  session to consume — the investigation found none exists; this delivery
  only adds authoring-time enforcement, not a new base-computation path.

## Accumulation

This adds one more inline-heredoc `gh`-calling `PreToolUse`+`Bash` hook to
the `gh pr create` matcher group (`pr-preflight.sh`, `claim-scan-
preflight.sh`, now `pr-base-guard.sh`) — the same accumulation shape
`enforcement-boundary.md`'s existing rows already track. If N more such
hooks land, each still ports its own check inline (per this proposal's
Rationale: no shared importable module, to keep every hook independently
zero-install), so the cost that grows is the matcher group's own length in
`hooks.json` and the number of subprocess `gh` calls one `gh pr create`
now triggers serially (currently 3: `pr-preflight.sh`, `claim-scan-
preflight.sh`, `pr-base-guard.sh`). No shared list/helper file is
introduced or extended by this change, so there is no per-file repeated-
edit accumulation beyond the `hooks.json`/`enforcement-boundary.md`/
`generated-paths.md` registration rows this delivery already adds.

## How you'll know it worked

`python3 -m pytest tests/test_pr_base_guard.py -v` — all cases pass,
including the three Acceptance-named tests
(`test_rejects_nonmain_base`, `test_allows_default_base`,
`test_fail_closed_on_unknown_default`).
