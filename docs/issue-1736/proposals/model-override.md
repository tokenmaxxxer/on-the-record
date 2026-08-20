---
status: proposed
files:
  - spawn.py
  - test/test_spawn_model_override.py
---

## Request

spawn.py's role-session model is only globally configurable today
(`MUSTER_ROLE_MODEL` env > `role_model.txt` > built-in `"sonnet"`,
`resolved_role_model()`). Add a per-invocation `--model` CLI flag so one
specific spawn/consult/panel call can pick a model without touching the
global config, at precedence `--model` > `MUSTER_ROLE_MODEL` >
`role_model.txt` > `"sonnet"`. The judge prefilter/validator's hardcoded
`haiku` must stay unreachable from `--model`.

## Constraints

- Scope is spawn.py only (issue #1736's own scope line).
- Precedence order is fixed by the issue text, not a design choice.
- Without `--model`, behavior must be byte-identical to today (issue's
  stated empty-state requirement) — env > file > sonnet, unchanged.
- `_judge_cmd_and_env()`'s two hardcoded `model="haiku"` callers
  (prefilter, validator) must never see the CLI value.
- One unit test per precedence level, plus the guard case, in
  `test/test_spawn_model_override.py` (issue's named check).

## Rationale

Two shapes were available for adding the CLI tier: (a) give
`resolved_role_model()` an optional override parameter checked before
the env var, and thread it from `main()`'s new `--model` down through
`spawn_cmd()` / consult's argv builder / `_run_panel_session()`; or (b)
have each of the three call sites read `args.model` directly (e.g. via a
module-level global or by passing the whole `argparse.Namespace` down)
and skip `resolved_role_model()` for the CLI tier, calling it only as
the fallback when `--model` is absent.

(a) is chosen. (b) was rejected: it would leave the precedence logic
split across two places (an if/else at each of three call sites, plus
the existing env>file>default logic staying inside
`resolved_role_model()`), duplicating the "is this value non-empty after
strip" check three times instead of once, and it would make the
judge-path guard harder to state as a single fact ("only these three
functions receive `model=`, `_judge_cmd_and_env()` never does") since
the CLI value would leak as an ambient `args.model` reachable from
anywhere rather than an explicit parameter absent from
`_judge_cmd_and_env()`'s signature.

## What will be done

1. `resolved_role_model(cli_model: str | None = None) -> str`: if
   `cli_model` is non-empty after `.strip()`, return it; else fall
   through to the existing `MUSTER_ROLE_MODEL` env > `role_model.txt` >
   `"sonnet"` chain unchanged.
2. Add `model: str | None = None` params to `spawn_cmd()`, to the
   consult argv-builder function (spawn.py:5547), and to
   `_run_panel_session()`, each passing it through to their
   `resolved_role_model(model)` call in place of the current
   no-arg call.
3. Thread a `model` parameter through `_spawn_one()`, `consult_cmd()`,
   and `panel_cmd()` down to the functions in step 2.
4. Add `ap.add_argument("--model", help=...)` to the `ArgumentParser`,
   and pass `a.model` at the three dispatch sites: the `spawn`
   `_spawn_one(...)` call, the `consult` `consult_cmd(...)` call, and
   the `panel` `panel_cmd(...)` call. Also pass it into the dry-run
   preview block's `resolved_role_model(a.model)` call so `--dry-run`
   previews the override too.
5. Leave `_judge_cmd_and_env()` and its two callers (prefilter,
   validator) untouched — no `model` param added, no `a.model` passed
   in; they keep calling with the literal `model="haiku"`.
6. Write `test/test_spawn_model_override.py` with one test per
   precedence level (CLI > env > file > default) against
   `resolved_role_model()` directly (monkeypatching `os.environ` and
   `ROLE_MODEL_CONFIG`/`role_model.txt`), plus a guard test asserting
   `_judge_cmd_and_env(..., model="haiku")`'s emitted argv still carries
   `haiku` regardless of any `MUSTER_ROLE_MODEL`/CLI value set in the
   test's environment.

## Out of scope

- Any other role/CLI file besides spawn.py (issue's own scope line).
- Changing the default model, the env var name, or `role_model.txt`'s
  format.
- Adding `--model` validation against a known-models list (issue does
  not ask for it; the underlying `claude -p --model` call already
  rejects unknown values).

## Accumulation

This touches the existing repeated
`role_model = resolved_role_model(...); if role_model: cmd += ["--model", role_model]`
two-line pattern already duplicated across `spawn_cmd()`, the consult
argv builder, and `_run_panel_session()` — each site's call becomes
`resolved_role_model(model)` instead of `resolved_role_model()`, same
shape, one more argument, no new call site added. If a fourth
precedence-consuming launcher appears later, it repeats this same
two-line pattern again; that duplication already exists pre-change (not
introduced by this proposal) and consolidating the three sites into one
shared helper is a separate, larger refactor issue #1736's "spawn.py
`--model` only" framing does not ask for here.

## How you'll know it worked

`python3 -m pytest test/test_spawn_model_override.py -v` passes with
one test per precedence level (CLI, env, file, default) plus the guard
case, and a manual `spawn.py spawn <role> ... --model opus --dry-run`
smoke check shows `--model opus` in the previewed argv while
`MUSTER_ROLE_MODEL`/`role_model.txt` values are overridden.
