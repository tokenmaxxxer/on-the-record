---
status: proposed
files:
  - .on-the-record/model-routing.json
  - spawn.py
  - tests/test_model_routing.py
  - .on-the-record/test-tiers.json
---

# Structural model routing at spawn time

## Request

Every spawn that omits `--model` today resolves through
`resolved_role_model()`: `--model` > `MUSTER_ROLE_MODEL` env > `role_model.txt`
> `"sonnet"` (canonical: spawn.py:5534-5549, read in survey.md). Nothing in
that chain looks at the task itself, so a design/aesthetics-heavy spawn (a
ux-engineering phase-1, say) gets the same model as a mechanical single-phase
fix — the operator directive names a real dogfood cost from exactly this
underallocation. The issue asks for a routing layer that picks a model tier
from spawn-time signals already computed (`role`, `single_phase`,
design-bearing classification of the issue body) via a repo-overridable
policy file, with `--model` still always winning, fail-open on policy
errors, and the chosen model + rule recorded per spawn.

## Constraints

- `--model` (and the existing `MUSTER_ROLE_MODEL`/`role_model.txt` chain)
  must keep behaving exactly as today when an explicit override is present
  — routing only fires in the gap `resolved_role_model()` currently fills
  with the flat `"sonnet"` default.
- Policy lives as data (JSON) under `.on-the-record/`, not as a Python
  constant, matching the `test-tiers.json` precedent (issue #1518) so a
  consumer repo can override it without touching spawn.py.
  canonical: .on-the-record/test-tiers.json read in survey.md.
- Routing errors (missing file, malformed JSON, unknown role not in policy)
  must never block a spawn — fall back to the pre-issue-2070 chain
  (`"sonnet"` default), matching the fail-open shape spawn.py already uses
  for gh-query failure (canonical: spawn.py:8345-8349, read in survey.md).
- The chosen model and the rule that picked it must be recorded per spawn
  (roster or ledger line) so model-vs-outcome efficiency is measurable
  later against #1991/#2015.
- No change to `_judge_cmd_and_env()`'s hardcoded `model="haiku"` path
  (canonical: spawn.py:6222, spawn.py around 6328/6363, read in survey.md)
  — that path is out of scope; the issue's signals (role/phase/
  design-bearing) describe role-session spawns, not the judge probe.

## Rationale

**Module placement.** Considered inlining the routing function directly in
spawn.py next to `resolved_role_model()` (same file as the chain it
extends, zero new import surface). Rejected in favor of a new
`gates/model_routing.py` sibling module, because `gates/` is already this
repo's home for pure, testable decision logic factored out of spawn.py's
body — `design_bearing_classifier.py` is the exact precedent this routing
layer needs to call into (canonical: gates/design_bearing_classifier.py:
41-115, read in survey.md), and a routing layer that has to import its own
signal source from a sibling module is more naturally itself a sibling
module than a spawn.py-internal function reaching into `gates/`. Keeping
routing logic isolated from spawn.py's very large body also makes the
acceptance criterion's "routing tests" (policy honored, override
precedence, fail-open, ledger line) testable by importing one small module
instead of exercising `_spawn_one()`'s full spawn path.

**Precedence: where routing sits vs. the existing env/config chain.**
Considered making routing the top of the chain (routing tier picks first,
then `MUSTER_ROLE_MODEL`/`role_model.txt` only apply if routing produced
nothing). Rejected: `MUSTER_ROLE_MODEL`/`role_model.txt` are today's
explicit, deliberate operator-set overrides (issue #93's rationale, per
spawn.py:5535-5538's own docstring) — an operator who sets
`role_model.txt` to pin a specific model is making a stronger, more
explicit statement than a structural policy-file default, and routing
silently overriding that would regress issue #93's guarantee. Routing
therefore sits *below* `MUSTER_ROLE_MODEL`/`role_model.txt` in the chain:
`--model` > `MUSTER_ROLE_MODEL` env > `role_model.txt` > routing-layer tier
> `"sonnet"`. This keeps `resolved_role_model()`'s three existing rungs
byte-identical when either env or config-file is set, and only exercises
routing in the exact gap the issue names (today's terminal `"sonnet"`
default).

**Ledger vs. roster for the model+rule record.** Considered a new
`ledger_write()` event (`{"event": "model_routed", ...}`) alongside the
existing per-spawn roster entry. Rejected as the sole record: roster is
already the one-row-per-spawn table carrying `role`/`issue`
(canonical: spawn.py:8740-8768, read in survey.md), so a `model`/`model_rule`
field there is directly joinable with every other per-spawn fact without a
separate cross-reference into `runs/ledger.jsonl`. Adding fields to the
roster entry is chosen; a supplementary ledger event is not added in this
phase (kept out of scope below) since the issue's acceptance text accepts
either surface ("roster/ledger line") and roster alone satisfies it with
less surface area.

## Accumulation

`route_model()` will be called once per spawn as a pure function — it does
not open a subprocess, shell out, or make a network call, so repeated
spawns do not accumulate inline `subprocess`/`gh` calls. The one repeated-
file-edit-shaped surface is `.on-the-record/model-routing.json`'s tier
membership lists (adding a role to `judgment`/`mid-design`/`mechanical`):
this is intentionally a data edit, not a code change — the whole point of
shipping policy as JSON (per the Constraints section) is that N future
role-to-tier reassignments are single-line edits to one file, not N
spawn.py diffs. If tier membership grows to the point the flat JSON lists
become hard to reason about, the fix is to add a `default_tier` fallback
key to the policy (already planned as part of fail-open behavior) rather
than exhaustively enumerating every role — this proposal does not need
that yet since the shipped default only needs to seed the roles already
special-cased at spawn.py:451-452.

## What will be done

1. Ship `.on-the-record/model-routing.json` with a default three-tier
   policy: `judgment` (design/aesthetics-critical roles — ux-engineering,
   brand-design, architecture phase-1, per the roles already special-cased
   at spawn.py:451-452), `mid-design` (other phase-1/multi-phase roles),
   `mechanical` (single-phase / `CORE_BUILD_NOW` spawns) — each tier mapped
   to a model string (fable/opus/sonnet respectively, per the operator's
   3-tier directive), plus a `design_bearing_override` entry naming which
   tier a positive design-bearing verdict promotes a spawn to regardless of
   role.
2. Add `gates/model_routing.py`: a `route_model(role, single_phase,
   design_bearing_verdict, policy) -> tuple[str, str]` (model, rule-name)
   pure function, plus a `load_policy(repo_root) -> dict` loader that reads
   `.on-the-record/model-routing.json`, falls back to a shipped in-module
   default dict on any read/parse error, and never raises.
3. Wire `resolved_role_model()` (spawn.py:5534) to call the routing layer
   only when both `cli_model` and `MUSTER_ROLE_MODEL`/`role_model.txt` are
   empty, passing the role/single_phase/design-bearing signals already
   available in `_spawn_one()` (spawn.py:8289) through the existing
   `spawn_cmd()` call chain; on any routing exception, fall back to the
   literal `"sonnet"` string spawn.py returns today.
4. Add `model`/`model_rule` fields to the `roster_register()` entry dict
   (spawn.py:8740-8768) reflecting the resolved model and which rule chose
   it (`cli-override` / `env-override` / `config-override` / a routing
   tier name / `fail-open-default`).
5. Add `tests/test_model_routing.py` covering: policy file honored (custom
   tier mapping applied), override precedence (`--model` beats routing,
   `MUSTER_ROLE_MODEL`/`role_model.txt` beats routing, routing beats the
   `"sonnet"` terminal default), fail-open on malformed/missing policy
   JSON, and the roster entry recording model+rule.
6. Add the new test file to `.on-the-record/test-tiers.json`'s
   `slow.trigger_change_classes` list alongside the existing
   `spawn.py`-adjacent entries.

## Out of scope

- `_judge_cmd_and_env()`'s hardcoded `model="haiku"` probe path — unchanged.
- A supplementary `ledger_write()` event for model routing — roster fields
  satisfy the acceptance text's "roster/ledger line" alone; can be added
  later if #1991/#2015 need a separate append-only event stream.
- Retroactively re-tiering the role-list already special-cased at
  spawn.py:451-452 for skill-mount purposes — the shipped policy's
  `judgment` tier reuses that list as its starting membership, but changing
  which roles are on it is a policy-file edit, not a code change, once this
  lands.
- Any change to `role_model.txt` / `MUSTER_ROLE_MODEL` semantics — both
  keep winning over routing exactly as they do today.

## How you'll know it worked

`.on-the-record/test-tiers.json`'s `fast` tier
(`python3 -m pytest -q -m "not slow"`) runs green including
`tests/test_model_routing.py`'s new cases: policy file honored, override
precedence (`--model` > env/config > routing > `"sonnet"`), fail-open on
malformed policy (missing file, invalid JSON, unknown role — each falls
back to `"sonnet"` without raising or blocking the spawn), and a roster
entry produced by a routed spawn carries both the chosen model and the
deciding rule name.
