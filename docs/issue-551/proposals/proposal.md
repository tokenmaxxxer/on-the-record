---
status: proposed
files:
  - docs/specs/test-env-resolution.md
  - gates/test_env_resolve.py
  - gates/test_test_env_resolve.py
---

# Proposal — canonical test-env resolution convention (issue #551)

## Request
23 of 43 rulebook repos' gate-test scripts fail on a plain main checkout
because they assume the spawn-session environment (`CLAUDE_PLUGIN_ROOT_CORE`
set, core plugin reachable at a known path). Define one canonical
test-environment resolution convention — resolution order, an explicit
SKIP contract distinct from a real failure, and a reference snippet — so
each of the 23 repos can adopt the same convention instead of hand-rolling
their own (as `execution-observation-rulebook/tests/fetch-core.sh`
currently does, without the SKIP outcome).

## Constraints
- Convention doc lands under `docs/specs/` in this repo.
- Resolution order: `$CLAUDE_PLUGIN_ROOT_CORE` → known sibling-clone
  fallback(s) → explicit `SKIP: core plugin unreachable — unverifiable
  outside spawn env` with a distinct exit code — never a misleading
  failure.
- A reference implementation snippet, unit-tested via `python3 -m pytest`.
- No hardcoded per-repo paths in the convention itself.
- If one convention cannot cover all 23 repos' test shapes, exceptions
  must be enumerated explicitly.
- This delivery is the convention + reference snippet only — adopting it
  in the 23 rulebook repos is out of scope (separate repos, separate
  issues/PRs; see Out of scope).

## Rationale
**Chosen approach**: a small standalone Python module
(`gates/test_env_resolve.py`) exposing one function,
`resolve_core(env=os.environ) -> ResolveResult`, implementing the
3-outcome contract (RESOLVED / RESOLVED-fallback / SKIP), plus a thin CLI
entry point (`python3 -m gates.test_env_resolve` — prints the resolved
path on stdout, or the `SKIP: ...` line on stderr with a distinct exit
code) so a bash test runner can call it as a subprocess without needing a
Python import, and a Python test module can `import` it directly. The
`docs/specs/test-env-resolution.md` doc documents the contract in prose
and embeds this module's exact source as the reference snippet (not a
paraphrase), with a short adoption note per consumer shape (bash runner:
invoke as CLI and branch on exit code; pytest suite: import and call, or
use a `pytest.skip()` wrapper).

**Alternative considered and rejected**: generalize
`execution-observation-rulebook/tests/fetch-core.sh` in place and have
the spec document merely *point* at that file by path. Rejected because
(a) it lives in one rulebook repo's `tests/` directory, not in this
repo's `docs/specs/`, so the other 22 repos would depend on a third
repo's test-only file rather than on a documented, versioned convention
owned by the orchestrator repo; and (b) its current fallback-exhausted
path is a hard `exit 1` treated by its own caller as a real failure —
there is no SKIP outcome distinct from "gate actually regressed," which
is precisely the ambiguity issue #551 exists to remove, so promoting it
as-is would carry the defect forward rather than fix it.

**Alternative considered and rejected**: bash-only reference snippet (no
Python), since most current rulebook gate scripts are themselves bash.
Rejected because the issue's acceptance check requires the reference
snippet be unit-tested via `python3 -m pytest`, and this repo's own
existing SKIP-adjacent prior art (`gates/skip_gate.py`) is Python — a
Python module with a CLI entry point satisfies both the pytest
requirement and bash-consumer adoption (via subprocess/exit-code), while
a bash-only snippet cannot be `pytest`-unit-tested without a Python
wrapper anyway.

## What will be done
- Write `gates/test_env_resolve.py`: a module with `resolve_core(env)`
  returning a small result object (resolved path or None + a `skip`
  flag + a message), covering the three-step order: (1)
  `CLAUDE_PLUGIN_ROOT_CORE` if set and `hooks/lib/gate-lib.sh` exists
  under it; (2) a caller-supplied list of sibling-checkout candidate
  paths (e.g. `../core`, `../../tokenmaxxxer-core/core`) checked the same
  way — the convention takes candidates as a parameter, so no path is
  hardcoded inside the module itself; (3) SKIP: prints/returns
  `SKIP: core plugin unreachable — unverifiable outside spawn env` and a
  distinct exit code (`75`, `EX_TEMPFAIL` in BSD sysexits — chosen over
  1/2 specifically so it cannot collide with a gate's existing
  pass/fail/deny exit codes) — the module never clones over the network;
  network fallback (as `fetch-core.sh` step 3 does) is named in the doc
  as a repo-local extension a consumer MAY add on top, not part of the
  canonical SKIP contract.
- Add a `main(argv)` CLI wrapper in the same file so a bash test runner
  can invoke `python3 -m gates.test_env_resolve <candidate1> <candidate2>
  ...` and branch on exit code (0 = resolved, 75 = skip).
- Write `gates/test_test_env_resolve.py` covering: `CLAUDE_PLUGIN_ROOT_CORE`
  hit; env var unset, sibling-candidate hit; env var unset, no candidate
  exists → SKIP outcome and exit code 75; env var set but pointing at a
  path missing `gate-lib.sh` → falls through to candidates (not treated
  as resolved).
- Write `docs/specs/test-env-resolution.md`: states the resolution order,
  the SKIP contract (message text + exit code, both fixed/canonical), the
  no-hardcoded-paths rule, embeds the reference module's source, and adds
  the empty-state section enumerating known non-conforming test shapes
  found in the survey (a pytest suite with no core dependency at all,
  such as this repo's `gates/test_skip_gate.py`, is out of scope for this
  convention — it never needed core resolution in the first place; that
  is stated as the one enumerated exception).

## Accumulation
`gates/test_env_resolve.py`'s CLI wrapper runs no `subprocess`/`gh` calls
itself — it is the resolver being defined, not a caller of one. It adds
one new file, not a repeated per-repo pattern in this codebase; the
convention is meant to be *referenced* by the 23 rulebook repos (each in
its own separate issue/PR, see Out of scope), not copy-pasted N more
times into this repo. If a future issue needs a second reference
resolver variant here, the fix is to extend `resolve_core()`'s
`candidates` parameter, not add a parallel file.

## Out of scope
- Modifying any of the 23 rulebook repos' actual gate-test scripts to
  adopt this convention — each is a separate repo needing its own
  issue/PR.
- Network-clone fallback as part of the canonical contract (documented as
  an optional repo-local extension only).
- Changing `spawn.py`'s `CLAUDE_PLUGIN_ROOT_CORE` injection (issue #182,
  already landed) — this proposal only documents how a *test*, run
  outside spawn, should resolve the same variable's absence.

## How you'll know it worked
- `docs/specs/test-env-resolution.md` exists with the resolution order
  and SKIP contract stated explicitly.
- `python3 -m pytest gates/test_test_env_resolve.py -q` passes, covering
  all three resolution-order branches plus the SKIP branch.
- `python3 -m gates.test_env_resolve nonexistent-path` (no
  `CLAUDE_PLUGIN_ROOT_CORE` set, no valid candidate) exits 75 and prints
  the exact `SKIP: core plugin unreachable — unverifiable outside spawn
  env` line to stderr — manually confirmed in a clean shell, not just
  asserted in the pytest suite.
