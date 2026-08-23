---
code_under_review:
  - .on-the-record/model-routing.json
  - .on-the-record/test-tiers.json
  - gates/model_routing.py
  - spawn.py
  - tests/test_model_routing.py
  - tests/test_spawn_pipeline.py
  - test/test_spawn_artifact_skill_pairing.py
  - test/test_spawn_cross_family_skill_selection.py
type: feature
breaking: false
# canonical: python3 -m pytest -q -m "not slow" — result: 2606 passed, 20 xfailed, 1 xpassed (executed live this session, fenced output below)
verdict: pass
loop_state: landed
---

Subject: issue-2070

## What was done

canonical: docs/issue-2070/proposals/model-routing.md (read this session) — approved via the issue-level comment `APPROVE issue-2070/implementation` (`gh issue view 2070 --comments`, read this session)
canonical: 57d2831e409377c095e7ca19a39b1c588db75ead (commit landed this session, carries every file below)

Implemented the approved phase-1 proposal:

- `.on-the-record/model-routing.json`: shipped 3-tier default policy —
  `judgment` (fable, roles ux-engineering/brand-design/content-design/
  architecture), `mid-design` (opus), `mechanical` (sonnet), plus
  `design_bearing_override: "judgment"`, `single_phase_tier: "mechanical"`,
  `default_tier: "mid-design"`.
- `gates/model_routing.py`: `load_policy(repo_root)` (reads the policy
  file, falls back to an in-module `DEFAULT_POLICY` on any read/parse
  error) and `route_model(role, single_phase, design_bearing_verdict,
  policy) -> (model, rule)`, both pure and fail-open — precedence inside
  routing is design-bearing override > role-tier > single-phase tier >
  default tier > `("sonnet", "fail-open-default")`.
- `spawn.py`: `resolved_role_model()` gained optional `role`/
  `single_phase`/`design_bearing_verdict` params. The existing three
  rungs (`--model` / `MUSTER_ROLE_MODEL` / `role_model.txt`) are checked
  first, unchanged; only when all three are empty AND `role` is given
  does it call into the routing layer instead of the old hardcoded
  `"sonnet"`. Omitting `role` (every pre-existing call site except the
  one below) keeps the function's three rungs and plain-string return
  byte-identical to before.
  `spawn_cmd()` (the per-role-spawn path `_spawn_one()` uses) now takes
  `single_phase`/`design_bearing_verdict` params, forwards them into
  `resolved_role_model()`, and stamps two internal env keys
  (`_MODEL_ROUTING_MODEL`, `_MODEL_ROUTING_RULE`) that `_spawn_one()`
  pops before building the real subprocess env, recording them as
  `model`/`model_rule` fields on both the fork-child's early roster stub
  and the main roster entry. `_spawn_one()` computes
  `design_bearing_verdict` by calling
  `gates/design_bearing_classifier.check(cwd, issue)` when `issue is not
  None`, wrapped in `try/except Exception` so a `gh` failure degrades to
  `None` (no override) rather than blocking the spawn.
  Other `resolved_role_model()` call sites (consult/judge/panel argv
  builders, `--dry-run` reflection) were left passing no `role`, per the
  proposal's scope — only the `_spawn_one()`/`spawn_cmd()` path this
  issue's signals (role/single_phase/design-bearing) actually describe
  gained routing; the judge probe's hardcoded `model="haiku"` is
  untouched.
- `tests/test_model_routing.py`: policy file honored, override
  precedence (`--model` > `MUSTER_ROLE_MODEL` > `role_model.txt` >
  routing > `"sonnet"` terminal default), fail-open on malformed/absent/
  non-dict policy, `spawn_cmd()`'s env carrying both model and rule.
- `.on-the-record/test-tiers.json`: added `tests/test_model_routing.py`
  to the `slow` tier's `trigger_change_classes` list alongside the other
  `spawn.py`-adjacent test files.
- `docs/specs/enforcement-boundary.md` + regenerated
  `docs/specs/reconciled-index.md`: added `gates/model_routing.py`'s
  required boundary row (verdict: repo-local, since it is a routing
  helper, not an allow/deny gate).

canonical: python3 -m pytest -q -m "not slow" — result: 2606 passed, 20 xfailed, 1 xpassed (executed live this session)

```
2606 passed, 20 xfailed, 1 xpassed in 41.52s
```

## Rationale for deviations

The shipped policy's `default_tier` (opus) intentionally replaces the old
flat `"sonnet"` terminal default in the gap `resolved_role_model()` used
to fill — exactly the behavior this issue asks for. That broke five
pre-existing `execution-observation` "uses builtin default" assertions in
`tests/test_spawn_pipeline.py` (they asserted the old literal `"sonnet"`)
and two `spy_spawn_cmd` test stubs in `test/test_spawn_artifact_skill_pairing.py`
and `test/test_spawn_cross_family_skill_selection.py` that had a fixed
positional signature and choked on the new `single_phase`/
`design_bearing_verdict` keyword arguments `spawn_cmd()` now accepts.
None of these three files were in the proposal's frozen `files:` list.
Fixed inline (mechanical, no design judgment, required to keep the fast
tier green per this issue's own acceptance text): the five assertions now
expect `"opus"`, the two stubs gained `**kwargs`. Logged at
docs/issue-2070/reports/implementation/deviation-log.md.

## What did not work

None.

## Open findings

None.
