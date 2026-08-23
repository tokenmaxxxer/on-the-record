#!/usr/bin/env python3
"""issue-2104 — constitution check: scope intersection + disposition contract.

Fast tier, no network. Reproduces the hooks-beside-skills drift case
textually (issue #2104 acceptance).

  python3 -m pytest gates/test_constitution_check.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import constitution_check as cc
from frozen_decisions import Decision

REG = [
    Decision(decision_id="single-skill-axis", status="frozen", path=Path("a.md"),
             globs=["roles/**"], keywords=["role manifest", "role concept"]),
    Decision(decision_id="single-enforcement-surface", status="frozen", path=Path("b.md"),
             globs=["hooks/**", "skills/**"], keywords=["hooks-beside-skills",
                                                        "hook in the skill repo"]),
]

HOOKS_BESIDE_SKILLS_RECO = (
    "Recommendation: ship enforcement with each skill — carry a hook in the "
    "skill repo next to the skill definition so drift is caught at authoring time."
)


def t_intersecting_recommendation_needs_disposition():
    r = cc.check_recommendation(HOOKS_BESIDE_SKILLS_RECO, [], REG)
    assert r["status"] == "needs-disposition"
    assert r["conflicts"] == ["single-enforcement-surface"]
    assert "hook in the skill repo" in r["detail"]


def t_glob_intersection_via_touched_paths():
    r = cc.check_recommendation("add a manifest file per capability",
                                ["roles/reviewer.json"], REG)
    assert r["status"] == "needs-disposition"
    assert "single-skill-axis" in r["conflicts"]
    assert "roles/reviewer.json" in r["detail"]


def t_non_intersecting_skips_with_reason():
    r = cc.check_recommendation("rename the ledger file and add a retry",
                                ["gates/ledger.py"], REG)
    assert r["status"] == "skip"
    assert "intersects none" in r["reason"]


def t_disposition_missing_names_the_conflict():
    issue = "Adopting the consult recommendation from consult-log.md. Fixes #999."
    d = cc.check_disposition(issue, ["single-enforcement-surface"])
    assert d["ok"] is False
    assert d["missing"] == ["single-enforcement-surface"]
    assert "single-enforcement-surface" in d["detail"]
    assert "silent adoption is blocked" in d["detail"]


def t_disposition_reaffirms_passes():
    issue = ("Adopting the recommendation; it keeps hooks in core — "
             "reaffirms single-enforcement-surface.")
    d = cc.check_disposition(issue, ["single-enforcement-surface"])
    assert d["ok"] is True and d["missing"] == []


def t_disposition_escalation_passes_and_covers_all():
    issue = ("Named conflict with frozen decisions; "
             "escalated-to-operator: https://github.com/x/y/issues/2104#issuecomment-1 "
             "(operator approved the exception)")
    d = cc.check_disposition(issue, ["single-skill-axis", "single-enforcement-surface"])
    assert d["ok"] is True
    assert "escalated-to-operator" in d["detail"]


def t_reaffirms_must_cover_every_intersecting_decision():
    issue = "reaffirms single-skill-axis."
    d = cc.check_disposition(issue, ["single-skill-axis", "single-enforcement-surface"])
    assert d["ok"] is False and d["missing"] == ["single-enforcement-surface"]


def t_repo_registry_catches_the_recorded_drift_cases():
    """End-to-end against the real docs/decisions registry."""
    r = cc.check_recommendation(HOOKS_BESIDE_SKILLS_RECO, [])
    assert r["status"] == "needs-disposition"
    assert "single-enforcement-surface" in r["conflicts"]
    r2 = cc.check_recommendation(
        "Introduce a role concept separate from skills, with roles/<role> manifests.", [])
    assert r2["status"] == "needs-disposition"
    assert "single-skill-axis" in r2["conflicts"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
