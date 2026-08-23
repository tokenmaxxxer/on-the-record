---
subject: issue-2070
kind: survey
---

# Survey: structural model routing at spawn time

## Write surface

`spawn.py` (single source of truth for the current model-resolution chain),
a new repo-overridable policy file `.on-the-record/model-routing.json`
(sibling of `.on-the-record/test-tiers.json`, issue #1518's pattern), and a
new test module for the routing logic itself.

## Current state (read, not guessed)

- `resolved_role_model(cli_model=None)` is the sole resolution point today:
  `cli_model` (stripped) > `MUSTER_ROLE_MODEL` env > `role_model.txt`
  (repo-root) > `"sonnet"`. canonical: spawn.py:5534-5549 (read this turn).
  No signal from role/phase/design-bearing enters this chain — the function
  body has no such parameter or branch.
- `resolved_role_model()` call sites:
  derived: `grep -n "resolved_role_model(" spawn.py`
  ```
  5534:def resolved_role_model(cli_model: str | None = None) -> str:
  5593:    role_model = resolved_role_model(model)
  5913:    role_model = resolved_role_model(model)
  6222:    cmd += ["--model", model or resolved_role_model()]
  6579:        role_model = resolved_role_model(model)
  7442:        role_model = resolved_role_model(a.model)
  ```
  Line 5593 is `spawn_cmd()` (the main role-spawn argv builder); line 5913
  is `_consult_cmd_and_env()`; line 6222 is `_judge_cmd_and_env()`, whose
  callers hardcode `model="haiku"` (canonical: spawn.py around lines 6328
  and 6363, read this turn), so this branch's `resolved_role_model()`
  fallback never actually runs there; line 6579 is inside a further
  consult-panel helper; line 7442 is the `--dry-run` display path.
- `_spawn_one()` (spawn.py:8289-8293 signature, read this turn) is the
  orchestration body that already computes, before calling `spawn_cmd()`:
  `role` (str param), `single_phase` (bool param, issue #1978 —
  `CORE_BUILD_NOW=1` passthrough at spawn.py:8590), and `issue`/`body`
  (issue body text fetched at spawn.py:8398-8399, used today only for
  requirement-linkage and skill matching per spawn.py:8401-8408). Phase is
  not yet a first-class signal in this function — `single_phase` is the one
  existing phase-shaped bit (single-phase build-now vs. this session's own
  default two-phase flow).
- `gates/design_bearing_classifier.py`: `check_issue_body(issue, body) ->
  Verdict` (TypedDict) at gates/design_bearing_classifier.py:69-104,
  `check(repo, issue)` wrapper with live `gh` fetch at line 106. canonical:
  gates/design_bearing_classifier.py:41-115 (read this turn). `_spawn_one()`
  already imports `design_artifacts_gate` (spawn.py:8397) and already holds
  the fetched `body` string (spawn.py:8399) — a routing layer can reuse that
  `body` rather than re-fetching; when `body is None` (gh fetch failed, per
  the `except Exception` at spawn.py:8406-8408) the design-bearing signal
  should degrade to absent, not raise.
- `ROLE_MODEL_CONFIG = ROOT / "role_model.txt"` (spawn.py:5522) holds a
  single override string, not a tiered policy — structurally different from
  what this issue asks for (a signal-keyed map).
- `.on-the-record/test-tiers.json` (canonical: file read this turn) is the
  existing precedent for a repo-overridable JSON policy with a shipped
  default living under `.on-the-record/`. No `model-routing.json` exists
  yet at that path — derived: `ls .on-the-record/` shows only
  `test-tiers.json`.
- Roster/ledger: `roster_register(roster_key, {...})` at spawn.py:8740-8768
  (read this turn) is the per-spawn roster entry, holding `role`, `issue`,
  `session_id`, etc. — no `model`/`model_rule` field present in that dict
  literal today. `ledger_write({...})` is a separate structured event log
  (`runs/ledger.jsonl` per `_ledger_log_outcomes()` at spawn.py:1528-1531),
  used for gate-outcome events (e.g. `returned_pr_gate_fail_open` at
  spawn.py:8348) rather than per-spawn model choice. The issue's acceptance
  text says "roster/ledger line" — roster is the closer fit since it is
  already the one-row-per-spawn record and already carries `role`/`issue`.
- `--single-phase` CLI flag (spawn.py:7184) sets `CORE_BUILD_NOW=1` in the
  spawned env (spawn.py:8590) — the existing mechanical-work signal the
  issue's "mechanical single-phase (#1978 CORE_BUILD_NOW) -> default/economy
  tier" language names directly.
- Fail-open precedent already in this file for a structurally similar
  failure: gh-query failure in `_undispositioned_role_prs` (spawn.py:8345-
  8349) prints a stderr note, writes a `returned_pr_gate_fail_open` ledger
  event, and proceeds unblocked — this issue's "routing errors fall back to
  the existing default chain" asks for the same shape applied to a new
  failure surface (malformed/unreadable policy JSON), not a new pattern.

## Test harness

`.on-the-record/test-tiers.json`'s `fast` command is
`python3 -m pytest -q -m "not slow"` (budget 300s); canonical:
.on-the-record/test-tiers.json read this turn. Its `slow.trigger_change_classes`
list already names `spawn.py` and several `tests/test_spawn_*.py` files but
no routing-specific test file. A new test file for routing should be added
to that trigger list, since routing logic will live inside/alongside
spawn.py's spawn path.

## Open unknowns for the proposal to resolve

1. Where the routing function should live: inlined in spawn.py (matches
   `resolved_role_model`'s existing precedent) vs. a new sibling module
   under `gates/` (matches `design_bearing_classifier.py`'s existing
   separation of gate-shaped decision logic from spawn.py's body) — this is
   a real fork the proposal's Rationale must resolve, not a foregone
   conclusion.
2. Exact tier-to-model string mapping (shipped default) — the issue names
   three tiers by role but leaves concrete model identifiers (fable/opus/
   sonnet per the operator directive) as policy-file content, not a
   hardcoded constant.
3. Precedence order between the new routing layer and the existing
   `MUSTER_ROLE_MODEL` env / `role_model.txt` chain — the issue states
   "`--model` always wins" but is silent on where routing sits relative to
   env/config-file overrides that already exist.
