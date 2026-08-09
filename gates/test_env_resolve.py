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
