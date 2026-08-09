# Survey — issue #551: canonical test-env resolution convention

## Confirmed gap
No `docs/specs/` file in this repo (on-the-record) defines a test-env
resolution convention. `docs/specs/` holds `enforcement-boundary.md`,
`platform-capabilities.md`, `role-spec-template.schema.json`, etc. — no
file naming core-resolution order or a SKIP contract for gate tests.
Per the issue body's scan, 23 of 43 `derived: issue #551 body scan line` rulebook repos have gate-test scripts that fail outside the spawn env
(not independently re-run this session). This repo (on-the-record) is
the orchestrator that spawns rulebook role sessions and is the natural
home for a shared cross-repo convention doc, matching how
`docs/issue-182/` already documents the `CLAUDE_PLUGIN_ROOT_CORE`
injection contract that rulebook gates consume (`spawn_cmd()` in
spawn.py:1919-1975, sets `CLAUDE_PLUGIN_ROOT_CORE` to the resolved
`core` plugin dir — see docs/issue-182/reports/implementation.md).

## Existing partial convention (one rulebook, not canonical)
`execution-observation-rulebook/tests/fetch-core.sh` already implements a
3-step resolution order for locating core's `gate-lib.sh` under test:
1. `$CLAUDE_PLUGIN_ROOT_CORE` (real plugin install, if
   `hooks/lib/gate-lib.sh` exists under it)
2. `../core` sibling checkout relative to the test dir (local dev)
3. a cached shallow clone under `$TMPDIR` (network-fetched once)

Gap vs. the issue's ask: step 3 either clones successfully or exits 1
with a diagnostic — there is no explicit SKIP outcome distinct from a
real failure. `run-gate-tests.sh` (same repo) treats fetch-core.sh's
nonzero exit as a hard `exit 2` ("cannot resolve core canon"), i.e. a
misleading failure indistinguishable from an actual gate regression —
exactly the cost the issue reports (manual re-run on main needed to
disambiguate). This is the only prior art found in this session's
exploration of the checked-out rulebooks; it is not a landed canon file
(lives in one rulebook's `tests/`, not `docs/specs/` or core).

## Where core itself already defines the sourcing contract
`core/hooks/lib/gate-lib.sh` (tokenmaxxxer-core, referenced read-only
here) documents the PreToolUse gate-sourcing idiom used by every
rulebook's *runtime* gate script:
```
. "${CLAUDE_PLUGIN_ROOT_CORE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)}/hooks/lib/gate-lib.sh" || { echo "<gate-name>.sh: cannot source gate-lib.sh" >&2; exit 2; }
```
That relative fallback (`../hooks/lib/gate-lib.sh` from the gate script's
own dir) resolves *inside the rulebook's own plugin tree* — it works at
runtime because core is always `--plugin-dir`-loaded alongside the
rulebook (spawn.py, `core_plugin_dirs()`). It does NOT work for a gate
*test* invoked directly on a bare checkout (`python3 -m pytest` / a
shell test runner run standalone) — there is no sibling `../core` unless
the test harness manufactures one, which is exactly what
`fetch-core.sh` does. The runtime idiom and the test-env idiom are
different problems that happen to share a variable name; the issue is
about the test one only (issue body: "gate-test scripts failing when run
on a plain main checkout").

## Where CLAUDE_PLUGIN_ROOT_CORE is injected in spawn (the "spawn env" the tests assume)
`spawn_cmd()` (spawn.py:1919-1975, confirmed via docs/issue-182 record)
sets `CLAUDE_PLUGIN_ROOT_CORE` to the resolved `core` plugin dir from
`core_plugins` (built by `core_plugin_dirs()`, which itself calls
`core_root()` — clone-or-resolve of the `tokenmaxxxer-core` checkout).
This is exactly the "spawn-session environment" the issue says the
failing repos' tests wrongly assume is always present.

## SKIP-contract prior art in this repo
`gates/skip_gate.py` + `gates/test_skip_gate.py` already establish a
distinct-signal-for-skip pattern in this codebase: pytest's own `skip`
outcome (`pytest.skip("environment-gated, not run here")`) is parsed out
of pytest's textual output and turned into a nonzero gate exit
distinguishing "some tests skipped" from "all tests ran clean" — i.e.
this repo already treats "skip" as a first-class outcome distinct from
pass/fail, with its own detection machinery. The convention this issue
asks for needs an analogous distinct signal, but at the *test script's
own* exit code (not a downstream gate parsing pytest's stdout) — the
rulebook gate tests are invoked directly (`python3 -m pytest`, or a
shell runner like `run-gate-tests.sh`), and the issue asks for the SKIP
verdict to be visible directly from that invocation.

## Constraints already given in the issue body
- Convention doc lands under `docs/specs/` (this repo).
- Resolution order: `$CLAUDE_PLUGIN_ROOT_CORE` → known sibling-clone
  fallback(s) → explicit `SKIP: core plugin unreachable — unverifiable
  outside spawn env` with a distinct exit code — never a misleading
  failure.
- A reference implementation snippet, unit-tested via
  `python3 -m pytest`.
- No hardcoded per-repo paths in the convention itself.
- If one convention cannot cover all 23 repos' test shapes, exceptions
  must be enumerated explicitly (empty-state requirement).

## Test-shape variance across the failing repos (bearing on the empty-state requirement)
Sampled `execution-observation-rulebook/tests/run-gate-tests.sh` (bash,
invokes gate scripts as subprocesses, wants `CLAUDE_PLUGIN_ROOT_CORE` as
a directory) vs. this repo's own `gates/test_skip_gate.py` (Python,
`python3 -m pytest`, no core dependency at all — a different class of
test outside this issue's scope). The issue's acceptance check requires
`python3 -m pytest`-runnable reference code, but at least one known
consumer shape (`run-gate-tests.sh`) is a bash test runner, not pytest —
the reference snippet needs a shape (a small sourceable/importable
resolver, not a pytest-only harness) usable from both a bash runner
(source + call a function, or invoke as a script) and a Python test
module (import + call a function), which the proposal must call out
explicitly per the empty-state requirement.

## Alternatives visible from the code as it stands
- Land the convention as prose-only guidance in `docs/specs/`, no
  reference snippet — rejected by the issue's acceptance checks
  themselves (a reference implementation snippet, unit-tested, is
  required).
- Generalize `execution-observation-rulebook/tests/fetch-core.sh`
  in-place as the canonical snippet, referenced by path from the spec —
  rejected: it lives inside one rulebook repo, not `docs/specs/` here,
  so other repos would depend on a third repo's `tests/` directory
  rather than a documented, versioned convention; also its exit-1 path
  is a real failure, not the SKIP contract the issue requires, so it
  needs a substantive contract change, not just a promotion.
