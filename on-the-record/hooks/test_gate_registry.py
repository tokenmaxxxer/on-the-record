#!/usr/bin/env python3
"""issue #2138 — gate-retirement registry pin (fast tier), amended by
issue #2146 — single-dispatcher PreToolUse execution.

The #2138 evidence table dispositioned the 58 hook registrations into
KEEP 28 / DEMOTE 15 / RETIRE 15. #2146 then collapsed the 20 PreToolUse
KEEP registrations into ONE dispatcher registration
(pretooluse-dispatcher.sh) that runs the same 20 gate scripts in-process
— the scripts remain on disk as the dispatcher's sources. This test pins
the executed outcome as data:

1. every directly-registered KEEP script is in hooks.json (and its file
   exists);
2. the dispatcher's coverage (pretooluse_dispatcher.GATES) is exactly
   the 20 PreToolUse KEEP gates, and each source script exists;
3. no RETIREd script name ever reappears in hooks.json or the
   dispatcher, and no retired script file returns to hooks/;
4. the registration set is exactly the KEEP set — a new gate must be
   added here deliberately, not slipped in.

DEMOTEd scripts may remain on disk (their tests still exercise them) but
must be neither registered nor dispatched.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
HOOKS_JSON = HOOKS_DIR / "hooks.json"
sys.path.insert(0, str(HOOKS_DIR))
from pretooluse_dispatcher import DISPATCHED_SCRIPTS  # noqa: E402

# The 20 PreToolUse KEEP gates (#2138 evidence table): since #2146 they
# are executed by the dispatcher, not registered individually.
DISPATCHED_KEEP = {
    "retry-loop-bound.sh",  # PreToolUse "pre" leg; the PostToolUse
    # "post" leg stays a direct registration below.
    "deliverable-guard.sh",
    "heredoc-command-refusal-gate.sh",
    "upstream-defect-scope-guard.sh",
    "contract-guard.sh",
    "pr-preflight.sh",
    "pr-base-guard.sh",
    "spec-index-preflight.sh",
    "gate-registration-guard.sh",
    "acceptance-command-real-run-guard.sh",
    "live-fire-claim-real-run-guard.sh",
    "impact-guard.sh",
    "merge-allow-gate.sh",
    "spawn-allow-gate.sh",
    "gh-write-allow-gate.sh",
    "credential-network-guard.sh",
    "credential-record-guard.sh",
    "record-claim-guard.sh",
    "accumulation-claim-guard.sh",
    "approval-gate.sh",
}

# Directly-registered KEEP rows: 9 registrations / 9 unique scripts
# (#2138 KEEP set minus the 20 dispatched PreToolUse gates, plus the
# #2146 dispatcher; retry-loop-bound.sh keeps its PostToolUse "post"
# registration).
KEEP = {
    "self-update.sh",
    "session-role-bind.sh",
    "directive.sh",
    "pretooluse-dispatcher.sh",
    "retry-loop-bound.sh",
    "post-landing-obligation-gate.sh",
    "stop-poll-rearm.sh",
    "stop-gate.sh",
    "skill-verdict-guard.sh",
}

# RETIRE 15 (#2138 evidence table): registration rows removed AND script
# files deleted; neither may come back under these names.
RETIRED = {
    "record-tiering-directive.sh",
    "test-tier-directive.sh",
    "test-authoring-invariant-guard.sh",
    "role-axis-completeness-guard.sh",
    "perf-measurement-guard.sh",
    "test-authoring-spawn-check.sh",
    "issue-retrospective-spawn-check.sh",
    "interaction-design-spawn-check.sh",
    "ux-engineering-spawn-check.sh",
    "record-tiering-guard.sh",
    "role-spec-reference-guard.sh",
    "design-rationale-guard.sh",
    "accessibility-guard.sh",
    "api-version-guard.sh",
    "role-test-claim-guard.sh",
}

# DEMOTE 15 (#2138 evidence table): deregistered, normative content
# landed in guidance (directive/*.md, roles/specs quality bars, or the
# merged obligations Stop gate skill-verdict-guard.sh).
DEMOTED = {
    "record-claim-shape-directive.sh",
    "role-deviation-directive.sh",
    "absorbed-branch-recut-guard.sh",
    "delegation-post-gate.sh",
    "claim-scan-preflight.sh",
    "requirement-digest-preflight.sh",
    "live-fire-test-guard.sh",
    "plan-order-guard.sh",
    "delegated-judgment-gate.sh",
    "quality-bar-gate.sh",
    "call-shape-guard.sh",
    "deviation-log-guard.sh",
    "decision-queue-stopgate.sh",
    "report-framing-check.sh",
    "product-capture-stopgate.sh",
}


def _registered_scripts() -> list[str]:
    data = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
    names = []
    for groups in data["hooks"].values():
        for group in groups:
            for hook in group["hooks"]:
                # wrapped shape: ".../fail-open-wrapper.sh .../<script>.sh
                # [arg]"; direct shape (#2146 dispatcher): ".../<script>.sh"
                tokens = hook["command"].split()
                target = tokens[1] if (
                    Path(tokens[0]).name == "fail-open-wrapper.sh"
                    and len(tokens) > 1
                ) else tokens[0]
                names.append(Path(target).name)
    return names


def test_every_keep_script_is_registered_and_exists():
    registered = set(_registered_scripts())
    missing = KEEP - registered
    assert not missing, f"KEEP gates missing from hooks.json: {sorted(missing)}"
    for name in sorted(KEEP):
        assert (HOOKS_DIR / name).is_file(), f"KEEP script file missing: {name}"


def test_dispatcher_coverage_is_exactly_the_pretooluse_keep_set():
    """issue #2146: the dispatcher runs exactly the 20 PreToolUse KEEP
    gates — coverage drift in either direction fails here."""
    dispatched = set(DISPATCHED_SCRIPTS)
    assert dispatched == DISPATCHED_KEEP, (
        f"dispatcher coverage drift: extra={sorted(dispatched - DISPATCHED_KEEP)} "
        f"missing={sorted(DISPATCHED_KEEP - dispatched)}"
    )
    assert len(DISPATCHED_SCRIPTS) == 20
    for name in sorted(dispatched):
        assert (HOOKS_DIR / name).is_file(), (
            f"dispatched gate source file missing: {name}"
        )
    # the dispatched gates are the dispatcher's sources, never their own
    # registrations
    registered = set(_registered_scripts())
    double = (dispatched - {"retry-loop-bound.sh"}) & registered
    assert not double, (
        f"dispatched gates also registered directly: {sorted(double)}"
    )
    # retry-loop-bound.sh's remaining direct registration must be the
    # PostToolUse "post" leg only
    data = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
    rlb_rows = [
        (event, hook["command"])
        for event, groups in data["hooks"].items()
        for group in groups
        for hook in group["hooks"]
        if "retry-loop-bound.sh" in hook["command"]
    ]
    assert rlb_rows == [("PostToolUse", rlb_rows[0][1])]
    assert rlb_rows[0][1].endswith("retry-loop-bound.sh post")


def test_no_retired_script_reappears():
    registered = set(_registered_scripts()) | set(DISPATCHED_SCRIPTS)
    back = RETIRED & registered
    assert not back, f"retired gates re-registered in hooks.json: {sorted(back)}"
    on_disk = {p.name for p in HOOKS_DIR.glob("*.sh")} & RETIRED
    assert not on_disk, f"retired script files back on disk: {sorted(on_disk)}"


def test_registration_set_is_exactly_the_keep_set():
    registered = _registered_scripts()
    assert set(registered) == KEEP, (
        f"hooks.json registration drift: extra={sorted(set(registered) - KEEP)} "
        f"missing={sorted(KEEP - set(registered))}"
    )
    # #2146: 28 registrations -> 9 (20 PreToolUse rows collapsed into the
    # dispatcher; retry-loop-bound.sh keeps only its PostToolUse leg).
    assert registered.count("retry-loop-bound.sh") == 1
    assert len(registered) == 9
    # hooks.json has exactly ONE PreToolUse row: the dispatcher.
    data = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
    pre_rows = data["hooks"]["PreToolUse"]
    assert len(pre_rows) == 1
    assert len(pre_rows[0]["hooks"]) == 1
    assert pre_rows[0]["hooks"][0]["command"].endswith(
        "pretooluse-dispatcher.sh")


def test_demoted_scripts_are_not_registered():
    registered = set(_registered_scripts()) | set(DISPATCHED_SCRIPTS)
    back = DEMOTED & registered
    assert not back, f"demoted gates still/again registered: {sorted(back)}"
