# Test-env resolution convention (issue #551)

## Problem
Rulebook gate-test scripts assume the spawn-session environment
(`CLAUDE_PLUGIN_ROOT_CORE` set, core plugin reachable) so they can source
core's `hooks/lib/gate-lib.sh` under test. Run outside spawn — a plain
`main` checkout — many fail with a misleading error instead of a clear
verdict, forcing a manual re-run to tell "delivery regression" apart from
"environment". This doc defines one canonical resolution convention so
consumers stop hand-rolling their own.

## Resolution order
1. `$CLAUDE_PLUGIN_ROOT_CORE`, if set and it contains
   `hooks/lib/gate-lib.sh`.
2. The first caller-supplied sibling-checkout candidate path (e.g.
   `../core`, `../../tokenmaxxxer-core/core`) that contains
   `hooks/lib/gate-lib.sh`. Candidates are supplied by the *caller* — no
   path is hardcoded inside the convention/reference module itself.
3. Otherwise: **SKIP**, not a failure. Print
   `SKIP: core plugin unreachable — unverifiable outside spawn env` to
   stderr and exit with a distinct code (`75`, `EX_TEMPFAIL` from BSD
   sysexits) that cannot collide with a gate's own pass (`0`) / fail
   (`1`) / deny (`2`) exit codes.

The module never clones over the network. A network-fetch fallback (as
one rulebook's ad hoc script does) is a repo-local extension a consumer
MAY layer on top of step 2's candidate list — it is not part of the
canonical SKIP contract, because a network dependency turning into a
silent hang or a flaky failure is exactly the ambiguity this convention
removes.

## Adoption per consumer shape
- **Bash test runner** (e.g. a `run-gate-tests.sh` that invokes gate
  scripts as subprocesses): invoke the module as a CLI —
  `python3 -m gates.test_env_resolve <candidate1> <candidate2> ...` —
  and branch on exit code: `0` prints the resolved path on stdout; `75`
  means skip (treat the whole run as skipped/unverifiable, not failed).
- **Pytest suite**: `import` the module directly and call
  `resolve_core()`, or wrap it in a fixture that calls `pytest.skip(...)`
  when `result.skip` is true, so skipped runs show up as pytest SKIPs
  (see `gates/skip_gate.py` in this repo for how skips are already made
  a distinct, non-green signal here) rather than as passes or failures.

## Reference implementation
Verbatim source of `gates/test_env_resolve.py` (this repo), the reference
resolver + CLI wrapper implementing the order above:

```python
#!/usr/bin/env python3
"""issue #551 — canonical test-env resolution convention.

Rulebook gate tests need to locate core's `hooks/lib/gate-lib.sh` when run
directly (outside the spawn-session environment that sets
`CLAUDE_PLUGIN_ROOT_CORE`). `resolve_core()` implements the shared
resolution order — env var, then caller-supplied sibling-checkout
candidates, then an explicit SKIP outcome distinct from a real failure —
so a test cannot mistake "core is unreachable outside spawn env" for
"the gate under test actually regressed".

  python3 -m gates.test_env_resolve <candidate1> <candidate2> ...
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

SKIP_MESSAGE = "SKIP: core plugin unreachable — unverifiable outside spawn env"
EX_TEMPFAIL = 75  # BSD sysexits EX_TEMPFAIL — never collides with a gate's own 0/1/2 exits.

_GATE_LIB_RELPATH = "hooks/lib/gate-lib.sh"


@dataclass
class ResolveResult:
    path: str | None
    skip: bool
    message: str


def _has_gate_lib(candidate: str) -> bool:
    # os.path.getsize, not just isfile: an empty stub named gate-lib.sh
    # (e.g. a stale/partial checkout) must not read as "core reachable" —
    # that would silently reintroduce the environment-vs-regression
    # ambiguity this resolver exists to remove (issue #551 warrant hunt).
    path = os.path.join(candidate, _GATE_LIB_RELPATH)
    return os.path.isfile(path) and os.path.getsize(path) > 0


def resolve_core(env: dict | None = None, candidates: list[str] | None = None) -> ResolveResult:
    """Resolve core's plugin root for a test run outside the spawn env.

    Order: $CLAUDE_PLUGIN_ROOT_CORE (if it contains gate-lib.sh) -> the
    first caller-supplied candidate that contains gate-lib.sh -> SKIP.
    No path is hardcoded here; candidates are supplied by the caller.
    """
    env = os.environ if env is None else env
    candidates = candidates or []

    env_root = env.get("CLAUDE_PLUGIN_ROOT_CORE")
    if env_root and _has_gate_lib(env_root):
        return ResolveResult(path=env_root, skip=False, message=f"resolved via CLAUDE_PLUGIN_ROOT_CORE: {env_root}")

    for candidate in candidates:
        if _has_gate_lib(candidate):
            return ResolveResult(path=candidate, skip=False, message=f"resolved via sibling candidate: {candidate}")

    return ResolveResult(path=None, skip=True, message=SKIP_MESSAGE)


def main(argv: list[str] | None = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]
    result = resolve_core(candidates=argv)
    if result.skip:
        print(result.message, file=sys.stderr)
        return EX_TEMPFAIL
    print(result.path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Unit-tested by `gates/test_test_env_resolve.py`
(`python3 -m pytest gates/test_test_env_resolve.py -q`), covering the
`CLAUDE_PLUGIN_ROOT_CORE` hit, the sibling-candidate hit, the
`CLAUDE_PLUGIN_ROOT_CORE`-set-but-missing-`gate-lib.sh` fall-through, an
empty (zero-byte) stub `gate-lib.sh` not counting as resolved, and
the SKIP outcome (path + exit code).

## Empty state — known exception
Not every failing test needs core resolution at all. This repo's own
`gates/test_skip_gate.py` is a pytest suite with no core dependency
whatsoever — it is out of scope for this convention because it never
resolves core in the first place; nothing about the resolution order
above applies to it. This is the one enumerated exception found in the
issue's survey of test shapes; no other exception is known at this time.

## Out of scope
Adopting this convention inside the 23 rulebook repos' own gate-test
scripts — that is separate work per repo, tracked in each repo's own
issue/PR. This doc and its reference module define the convention only.
