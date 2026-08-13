"""`spawn.py needs-due` — need-detector evaluator (issue #1160 step 3
machinery). Mirrors `roles_due.py`'s shape but evaluates a target repo's
file tree against each pilot spec's structured `use_when.need_detector`
`present_patterns`/`absent_patterns` globs, instead of a diff/board
predicate.

Advisory-only (issue #1160 requirement 2): this module never spawns a role
session — `needs_due()` is a pure classifier, `format_report()` only
formats text for an orchestrator's existing board-reading step to print
alongside `roles-due`'s own advisory output.

Hand-rolled glob matching (`fnmatch`/`pathlib.Path.rglob`), no new
dependency — the same constraint `role_spec_shape.py` already states for
itself, and the same primitive `roles_due.py`'s `_trigger_matches` already
uses for `path_patterns`.
"""
from __future__ import annotations
import fnmatch
import json
from pathlib import Path


def _specs_dir(root: Path) -> Path:
    return root / "roles" / "specs"


def load_need_detector_specs(root: Path) -> dict[str, dict]:
    """role name -> spec dict, for every `roles/specs/*.spec.json` that
    carries a non-empty `use_when.need_detector`."""
    out = {}
    d = _specs_dir(root)
    if not d.is_dir():
        return out
    for p in sorted(d.glob("*.spec.json")):
        try:
            spec = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(spec, dict):
            continue
        need_detector = (spec.get("use_when") or {}).get("need_detector")
        if isinstance(need_detector, dict) and need_detector:
            out[spec.get("role") or p.stem] = spec
    return out


def _any_glob_matches(target_root: Path, patterns: list[str]) -> str | None:
    """Returns the first pattern that matches at least one path under
    `target_root`, or None. Uses `Path.glob` per pattern (the pattern is a
    glob relative to `target_root`, e.g. "**/*.tsx" or
    "design-tokens/*.json") — same `fnmatch` primitive `roles_due.py`
    already relies on.

    A spec-supplied pattern containing a ".." segment is skipped outright
    (never globbed) — `Path.glob` honors ".." and would otherwise let a
    pattern escape `target_root` and match files elsewhere on disk,
    breaking the "arbitrary target project" trust boundary this module
    exists to hold (warrant-hunt finding,
    docs/issue-1160/reports/implementation/2026-08-13-hunt-step3-machinery-before-landing.md)."""
    for pat in patterns:
        if ".." in Path(pat).parts:
            continue
        try:
            if any(target_root.glob(pat)):
                return pat
        except (OSError, ValueError):
            continue
    return None


def needs_due(target_root: Path, root: Path | None = None) -> list[dict]:
    """For each pilot spec (loaded from `root`, the specs-owning repo —
    defaults to `target_root` when a target project vendors its own
    `roles/specs/`), does its `need_detector` fire against `target_root`'s
    actual file tree?

    A role is "due" iff at least one `present_patterns` glob matches under
    `target_root` AND no `absent_patterns` glob matches — the
    present-AND-absent shape every pilot spec's prose `condition` already
    describes.

    Returns `{"role", "reason"}` dicts, pure classifier, no side effects,
    no spawning. Empty list is the deliberate default: a target repo with
    none of the needs present stays silent (issue #1160 requirement 2's
    false-positive bound)."""
    target_root = Path(target_root).resolve()
    spec_root = Path(root).resolve() if root is not None else target_root
    specs = load_need_detector_specs(spec_root)

    due = []
    for role, spec in specs.items():
        need_detector = spec["use_when"]["need_detector"]
        present_patterns = need_detector.get("present_patterns") or []
        absent_patterns = need_detector.get("absent_patterns") or []
        if not present_patterns:
            continue  # nothing to match on -> never fires

        present_hit = _any_glob_matches(target_root, present_patterns)
        if not present_hit:
            continue

        absent_hit = _any_glob_matches(target_root, absent_patterns)
        if absent_hit:
            continue

        due.append({
            "role": role,
            "reason": f"present pattern matched {present_hit!r}, "
                      f"no absent pattern matched",
        })
    return due


def format_report(due: list[dict]) -> list[str]:
    if not due:
        return []
    out = ["[needs-due] 프로젝트가 이 역할의 실제 산출물을 필요로 함 — advisory-only:"]
    for d in due:
        out.append(f"  - {d['role']}: {d['reason']}")
    return out
