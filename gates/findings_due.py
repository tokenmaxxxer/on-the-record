"""`spawn.py findings-due` — advisory-queue board-reading source (issue
#1202 requirement 4). Mirrors `gates/need_detector.py`'s two-function
shape exactly: a pure classifier plus a pure formatter, wired into the
orchestrator's board-reading step alongside `roles-due`/`needs-due`.

Advisory-only: this module never files a `gh issue` and never spawns a
role session — scribe rule stays intact (the role discovers and queues,
the user confirms into an issue, the orchestrator then stamps
`relayed_to_issue:` on the finding after that confirmation).
"""
from __future__ import annotations
import re
from pathlib import Path

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)


def _frontmatter(text: str) -> dict:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fm: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()
    return fm


def _findings_dirs(target_root: Path) -> list[Path]:
    """Every `findings/<role>/` directory this repo's finding files can
    live under: the standard-bucket home
    (`docs/reports/findings/<role>/`) plus each per-issue variant
    (`docs/issue-<n>/reports/findings/<role>/`) — the two homes the
    proposal's §2 Queue location names."""
    dirs = []
    standard = target_root / "docs" / "reports" / "findings"
    if standard.is_dir():
        dirs.extend(d for d in standard.iterdir() if d.is_dir())
    for issue_dir in sorted(target_root.glob("docs/issue-*/reports/findings")):
        if issue_dir.is_dir():
            dirs.extend(d for d in issue_dir.iterdir() if d.is_dir())
    return dirs


def findings_due(target_root: Path) -> list[dict]:
    """Un-relayed queued findings under `target_root`. A finding is
    "un-relayed" until the orchestrator appends a `relayed_to_issue: <n>`
    frontmatter field to it, post user-confirmation (scribe-rule
    boundary: role discovers/queues, user confirms, orchestrator
    records). Session-summary files (`<date>-session-summary.md`) are
    not findings and are skipped.

    Pure classifier, no side effects, no spawning — empty list is the
    deliberate default (`need_detector.needs_due()`'s same false-positive
    bound: a target repo with nothing queued stays silent)."""
    target_root = Path(target_root).resolve()
    due = []
    for role_dir in _findings_dirs(target_root):
        role = role_dir.name
        for p in sorted(role_dir.glob("*.md")):
            if p.name.endswith("-session-summary.md"):
                continue
            fm = _frontmatter(p.read_text(encoding="utf-8"))
            if fm.get("relayed_to_issue"):
                continue
            due.append({
                "role": role,
                "path": str(p.relative_to(target_root)),
                "domain_rule": fm.get("domain_rule", ""),
                "date": fm.get("date", ""),
            })
    return due


def format_report(due: list[dict]) -> list[str]:
    if not due:
        return []
    out = ["[findings-due] 역할이 기록한 도메인 발견 — advisory-only, 사용자 확인 대기중:"]
    for d in due:
        out.append(f"  - {d['role']} ({d['date']}): {d['domain_rule']} — {d['path']}")
    return out
