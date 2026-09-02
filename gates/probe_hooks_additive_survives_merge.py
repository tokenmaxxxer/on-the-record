#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3083, Cluster A.

tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::
test_pre_existing_post_tool_use_commands_are_all_still_present used to
assert `len(after_commands) > len(before_commands)` -- true only while
this change sits unmerged on a branch (`before` read from
`origin/main`), and false the moment it merges (`origin/main` then
contains the addition too). Landing the change was the failure
condition.

This probe exercises the shared guard function directly
(`tests/test_spawn_gate_wiring.py::_assert_post_tool_use_additive`, the
same function the test itself now calls) against two synthetic states,
never against the real repo's `hooks.json` or git history:

- post-merge state -- `before` and `after` identical -- must PASS.
- a removal -- something in `before` missing from `after` -- must FAIL.

Run as `python3 gates/probe_hooks_additive_survives_merge.py` from the
repo root, no arguments. Prints `ok` and exits 0 on success; prints a
message to stderr and exits non-zero otherwise.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
import test_spawn_gate_wiring as wiring  # noqa: E402


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    identical = {
        "${CLAUDE_PLUGIN_ROOT}/hooks/fail-open-wrapper.sh a.sh",
        "${CLAUDE_PLUGIN_ROOT}/hooks/fail-open-wrapper.sh b.sh",
    }
    try:
        wiring._assert_post_tool_use_additive(identical, identical)
    except AssertionError as exc:
        _fail("guard rejected the post-merge state (before == after, "
              f"nothing removed or added): {exc}")

    before = {
        "${CLAUDE_PLUGIN_ROOT}/hooks/fail-open-wrapper.sh a.sh",
        "${CLAUDE_PLUGIN_ROOT}/hooks/fail-open-wrapper.sh b.sh",
    }
    after_with_removal = {
        "${CLAUDE_PLUGIN_ROOT}/hooks/fail-open-wrapper.sh a.sh",
    }
    try:
        wiring._assert_post_tool_use_additive(before, after_with_removal)
    except AssertionError:
        pass
    else:
        _fail("guard failed to detect a removed PostToolUse command "
              "(the regression that motivated this file, PR #2872)")

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
