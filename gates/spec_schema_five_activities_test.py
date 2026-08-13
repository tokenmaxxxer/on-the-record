"""issue #1130: five-activity depth check for the 14 cause-d role specs.

Asserts each in-scope spec names a methodology+source for judgment,
planning, deliverable production, feedback, and review, plus a non-empty
degree_level_knowledge list — the machine-checkable half of the
acceptance criterion (substance quality stays human PR review).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = ROOT / "roles" / "specs"

# The 14 roles issue #1129 diagnosed cause-d (no standing duty wired) and
# #1130 in-scope for five-activity depth. Cause-a roles are intentionally
# excluded here, not silently skipped.
IN_SCOPE_ROLES = [
    "content-design",
    "data-engineering",
    "data-modeling",
    "growth-analytics",
    "knowledge-management",
    "localization",
    "ml-engineering",
    "observability",
    "pr-communications",
    "refactoring-legacy",
    "user-discovery",
    "accessibility",
    "api-design",
    "performance-engineering",
]

ACTIVITY_FIELDS = [
    "judgment_methodology",
    "planning_methodology",
    "deliverable_form",
    "feedback_methodology",
    "review_methodology",
]


def _load(role):
    return json.loads((SPECS_DIR / f"{role}.spec.json").read_text())


def test_cause_a_roles_are_not_in_scope():
    # Empty-state case (acceptance criterion): a role diagnosed as
    # "workload never triggers the domain" is asserted absent from this
    # test's role list, not silently skipped.
    cause_a_sample = ["defect-verification", "requirements-engineering"]
    for role in cause_a_sample:
        assert role not in IN_SCOPE_ROLES


def test_every_in_scope_role_spec_exists():
    for role in IN_SCOPE_ROLES:
        assert (SPECS_DIR / f"{role}.spec.json").is_file(), role


def test_every_in_scope_role_has_five_activity_fields_with_sources():
    for role in IN_SCOPE_ROLES:
        spec = _load(role)
        for field in ACTIVITY_FIELDS:
            entry = spec.get(field)
            assert isinstance(entry, dict), f"{role}.{field} missing or not an object"
            method = entry.get("method")
            source = entry.get("source")
            assert isinstance(method, str) and method.strip(), f"{role}.{field}.method empty"
            assert isinstance(source, str) and source.strip(), f"{role}.{field}.source empty"


def test_every_in_scope_role_has_degree_level_knowledge():
    for role in IN_SCOPE_ROLES:
        spec = _load(role)
        entries = spec.get("degree_level_knowledge")
        assert isinstance(entries, list) and len(entries) >= 2, role
        for item in entries:
            assert isinstance(item, dict)
            concept = item.get("concept")
            source = item.get("source")
            assert isinstance(concept, str) and concept.strip(), f"{role} degree_level_knowledge concept empty"
            assert isinstance(source, str) and source.strip(), f"{role} degree_level_knowledge source empty"


def test_every_in_scope_role_still_has_source_standard():
    for role in IN_SCOPE_ROLES:
        spec = _load(role)
        source_standard = spec.get("source_standard")
        assert isinstance(source_standard, str) and source_standard.strip(), role
