"""`spawn.py roles-due` — board_condition evaluator for the JUDGMENT
residue (issue #896 step 2, REFRAME: invariant-first). test-authoring's
bar is a standing invariant now (test-authoring-invariant-guard.sh), not
judgment residue, so it deliberately carries no `trigger` here and never
appears in this evaluator's output.

Per role, `use_when.trigger` (added to a handful of `roles/specs/*.spec.json`
so far — the roles whose Korean `use_when` in `roles/<role>.json` already
embeds a parenthetical English `board_condition`) is a small structured
predicate: `path_patterns` (fnmatch globs) and/or `content_patterns`
(regex, checked against the diff'd files' current content), plus
`record_absent_for` naming which role's board record must be missing for
the match to count as "due". A spec with no `trigger` key is never
reported — this evaluator only knows what has been decomposed so far
(out of scope: the remaining role specs, staged as a follow-up).

No LLM re-reading `board_condition` as prose here — determinism and
auditability, so a hard gate (a later step, not this one) could enforce a
reproducible result. The prose stays the spec's contract for what the
pattern approximates; the gap is a spec-quality question, not this
module's job.
"""
from __future__ import annotations
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gates as _gates  # changed_files(), record_frontmatter()


def _specs_dir(root: Path) -> Path:
    return root / "roles" / "specs"


def load_triggered_specs(root: Path) -> dict[str, dict]:
    """role name -> spec dict, for every `roles/specs/*.spec.json` that
    carries a non-empty `use_when.trigger` block."""
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
        trigger = (spec.get("use_when") or {}).get("trigger")
        if isinstance(trigger, dict) and trigger:
            out[spec.get("role") or p.stem] = spec
    return out


def _current_branch(root: Path) -> str | None:
    try:
        r = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return r.stdout.strip() or None


def _subject_from_branch(branch: str | None) -> str | None:
    if not branch:
        return None
    m = re.match(r"^issue-(\d+)/", branch)
    return f"issue-{m.group(1)}" if m else None


def _file_content(root: Path, path: str) -> str:
    try:
        return (root / path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _trigger_matches(trigger: dict, changed: list[str], root: Path) -> str | None:
    """Returns a one-line reason string if the trigger matches, else None."""
    path_patterns = trigger.get("path_patterns") or []
    content_patterns = trigger.get("content_patterns") or []

    for path in changed:
        for pat in path_patterns:
            # fnmatch has no recursive-glob semantics: "**/auth/**" only
            # matches when a literal "/" precedes "auth" in the path, so a
            # repo-root path like "auth/login.py" (no leading segment)
            # would silently never match a leading "**/" pattern. Also try
            # the pattern with its leading "**/" stripped so a root-level
            # match still counts.
            if fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(path, pat.lstrip("*/")):
                return f"path matched {pat!r}: {path}"

    if content_patterns:
        compiled = [re.compile(p) for p in content_patterns]
        for path in changed:
            text = _file_content(root, path)
            if not text:
                continue
            for pat, rx in zip(content_patterns, compiled):
                if rx.search(text):
                    return f"content matched {pat!r} in {path}"
    return None


def roles_due(root: Path, base: str | None = None) -> list[dict]:
    """For each role spec carrying a `trigger`, does it fire against the
    current diff AND is the named record still absent from the board?

    Returns a list of `{role, reason, subject}` dicts, empty when nothing
    is due — the empty state is deliberate (issue #896 acceptance: "a
    branch firing no role condition is unaffected")."""
    root = Path(root).resolve()
    if base:
        _gates.BASE = base
    try:
        changed = _gates.changed_files(root)
    except Exception:
        return []  # fail closed on "can't tell" would over-block; roles-due
        # is surfaced-only, so an unreadable diff means nothing to surface,
        # not a block.

    branch = _current_branch(root)
    subject = _subject_from_branch(branch)
    if subject is None:
        return []

    board_dir = root / "docs" / subject / "reports"
    specs = load_triggered_specs(root)
    due = []
    for role, spec in specs.items():
        trigger = spec["use_when"]["trigger"]
        record_role = trigger.get("record_absent_for") or role
        record_path = board_dir / f"{record_role}.md"
        if record_path.is_file():
            continue  # record already exists — not due regardless of match
        reason = _trigger_matches(trigger, changed, root)
        if reason:
            due.append({"role": role, "reason": reason, "subject": subject})
    return due


def format_report(due: list[dict]) -> list[str]:
    if not due:
        return []
    out = ["[roles-due] 판단(judgment) 잔여 — 조건이 걸렸고 아직 기록 없음:"]
    for d in due:
        out.append(f"  - {d['role']} ({d['subject']}): {d['reason']}")
    return out
