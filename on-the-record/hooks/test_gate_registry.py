#!/usr/bin/env python3
"""issue #2138 — gate-retirement registry pin (fast tier).

The #2138 evidence table dispositioned the 58 hook registrations into
KEEP 28 / DEMOTE 15 / RETIRE 15. This test pins the executed outcome as
data:

1. every KEEP script is registered in hooks.json (and its file exists);
2. no RETIREd script name ever reappears in hooks.json, and no retired
   script file returns to hooks/;
3. the registration set is exactly the KEEP set — a new gate must be
   added here deliberately, not slipped in.

DEMOTEd scripts may remain on disk (their tests still exercise them) but
must not be registered.
"""
from __future__ import annotations

import json
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
HOOKS_JSON = HOOKS_DIR / "hooks.json"

# KEEP 28 registrations / 27 unique scripts (#2138 evidence table;
# retry-loop-bound.sh is registered twice, pre + post).
KEEP = {
    "self-update.sh",
    "session-role-bind.sh",
    "directive.sh",
    "retry-loop-bound.sh",
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
                # command shape: "...fail-open-wrapper.sh .../<script>.sh [arg]"
                target = hook["command"].split()[1]
                names.append(Path(target).name)
    return names


def test_every_keep_script_is_registered_and_exists():
    registered = set(_registered_scripts())
    missing = KEEP - registered
    assert not missing, f"KEEP gates missing from hooks.json: {sorted(missing)}"
    for name in sorted(KEEP):
        assert (HOOKS_DIR / name).is_file(), f"KEEP script file missing: {name}"


def test_no_retired_script_reappears():
    registered = set(_registered_scripts())
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
    # retry-loop-bound.sh is the only double registration (pre + post).
    assert registered.count("retry-loop-bound.sh") == 2
    assert len(registered) == 28


def test_demoted_scripts_are_not_registered():
    registered = set(_registered_scripts())
    back = DEMOTED & registered
    assert not back, f"demoted gates still/again registered: {sorted(back)}"
