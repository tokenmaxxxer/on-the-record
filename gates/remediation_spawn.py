#!/usr/bin/env python3
"""finding -> spawn-task 생성기(issue #587) — status: open 인
`docs/issue-<n>/decisions/remediation-*.md` 레코드를 읽어 스폰할
role/task 를 고정 템플릿으로 만든다. task 텍스트는 레코드 필드에서만
파생된다 — 절대 자유 작문하지 않는다(architecture Decision §1).

  python3 gates/remediation_spawn.py --issue <n> [--repo <경로>]
  대기 중인 태스크가 있으면 한 줄씩(`<role>\t<task>`) 찍는다.
"""
from __future__ import annotations
import argparse
import re
import subprocess
import sys
from pathlib import Path

_FIELD_RE = re.compile(r"^([a-zA-Z_]+):\s*(.*)$")

_TASK_TEMPLATE = (
    "Remediation round {round}: fix `{target_path}` — {required_fix} "
    "(routed from `{remediation_path}`, finding: `{finding_source}`)"
)


def _parse_frontmatter(text: str) -> dict[str, str]:
    """`---`로 감싼 `key: value` 줄만 읽는다 — 이 레포 게이트들이 이미
    쓰는 레코드 형식(yaml 파서 없이 평문 key: value)과 동일."""
    fields: dict[str, str] = {}
    in_block = False
    for line in text.splitlines():
        if line.strip() == "---":
            if in_block:
                break
            in_block = True
            continue
        if not in_block:
            continue
        m = _FIELD_RE.match(line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    return fields


def _branch_exists(root: Path, branch: str) -> bool:
    """정확한 refname 존재 여부만 본다 — `git branch --list <패턴>`은 glob
    으로 해석되어 `role` 값에 `*` 등이 섞이면 무관한 브랜치에 오탐할 수
    있다(issue #587 warrant hunt)."""
    r = subprocess.run(["git", "rev-parse", "--verify", "--quiet",
                        f"refs/heads/{branch}"], cwd=root,
                        capture_output=True, text=True)
    return r.returncode == 0


def _pr_already_launched(root: Path, remediation_path: str) -> bool:
    r = subprocess.run(["gh", "pr", "list", "--state", "all", "--json",
                        "headRefName,body"], cwd=root, capture_output=True,
                        text=True)
    if r.returncode != 0:
        return False
    marker = f"Remediation: {remediation_path}"
    return marker in r.stdout


def pending_remediation_tasks(root: Path, issue: int) -> list[dict]:
    """docs/issue-<n>/decisions/remediation-*.md 를 읽어, status: open 이고
    아직 스폰되지 않은 레코드마다 {role, task, remediation_path, round}
    딕셔너리를 돌려준다. 빈 목록은 오류가 아니다 — 대기 중인 게 없다는
    뜻이다."""
    decisions_dir = root / f"docs/issue-{issue}/decisions"
    tasks: list[dict] = []
    if not decisions_dir.is_dir():
        return tasks
    for path in sorted(decisions_dir.glob("remediation-*.md")):
        fields = _parse_frontmatter(path.read_text(encoding="utf-8", errors="ignore"))
        if fields.get("status") != "open":
            continue
        role = fields.get("routed_to", "")
        remediation_path = f"docs/issue-{issue}/decisions/{path.name}"
        if _branch_exists(root, f"issue-{issue}/{role}"):
            continue
        if _pr_already_launched(root, remediation_path):
            continue
        task = _TASK_TEMPLATE.format(
            round=fields.get("round", ""),
            target_path=fields.get("target_path", ""),
            required_fix=fields.get("required_fix", ""),
            remediation_path=remediation_path,
            finding_source=fields.get("finding_source", ""),
        )
        tasks.append({
            "role": role,
            "task": task,
            "remediation_path": remediation_path,
            "round": fields.get("round", ""),
        })
    return tasks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue", type=int, required=True)
    ap.add_argument("--repo", "-C", default=".")
    args = ap.parse_args()
    root = Path(args.repo)
    for t in pending_remediation_tasks(root, args.issue):
        print(f"{t['role']}\t{t['task']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
