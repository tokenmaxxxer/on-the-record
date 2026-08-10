---
code_under_review:
  - on-the-record/hooks/role-axis-completeness-guard.sh
  - on-the-record/hooks/test_role_axis_completeness_guard.py
  - on-the-record/hooks/hooks.json
  - docs/handbooks/hooks.md
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #650

## What was done

Wired a real operational caller for `gates/role_spec_shape.py`'s
`check_axis_ownership` / `check_role_judgment_axes` — added
`on-the-record/hooks/role-axis-completeness-guard.sh`, a `PreToolUse`
(`Bash`) hook that denies a `git commit` when the staged `roles/*.json`
set violates axis ownership (an axis owned by zero or more than one
role) or a role's own `judgment_axes` names an axis outside the closed
set. Registered it in `on-the-record/hooks/hooks.json`. Added
`on-the-record/hooks/test_role_axis_completeness_guard.py`, driving the
hook script itself via `subprocess.run(["bash", GUARD], ...)` against
real fixture git repos — not the `role_spec_shape.py` CLI — per the
issue's acceptance criterion. Documented the hook in
`docs/handbooks/hooks.md` and recorded the accumulation-shape rationale
in the phase-1 proposal.

## Why

Basis: docs/issue-650/proposals/2026-08-10-role-axis-completeness-gate.md

Hunt finding from #628: the `--roles-dir` CLI entrypoint added in #586
had zero callers outside its own unit tests — the same dead-code class
already fixed once in #594. A CLI entrypoint nobody invokes enforces
nothing; a real caller (a commit-time gate) makes the check actually
run in an operational path.

## Upstream

Basis: docs/issue-650/proposals/2026-08-10-role-axis-completeness-gate.md

## Doc placement

- [x] `docs/handbooks/hooks.md` updated with the new hook's behavior
  (env var: none added; new hook registration is the operational
  change, documented per the doctrine ladder for hook additions).
- [x] `docs/issue-650/proposals/2026-08-10-role-axis-completeness-gate.md`
  carries the accumulation-shape rationale (Accumulation section).

## What did not work

None.

## Open findings

None outstanding. Prior hunt dispatches for this proposal are recorded
in docs/reports/2026-08-10-hunt-role-axis-completeness-gate.md
(docs-only fast path noted where applicable).

## Verification run

`python3 -m pytest on-the-record/hooks/test_role_axis_completeness_guard.py -q`
→ 7 passed.
