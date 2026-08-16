#!/usr/bin/env python3
"""Stale-revert merge guard — issue #1664 (northpole req#6).

`merge_gate.py`'s existing checks (check-runner result, required
verification records) never look at what a PR's merge would actually do
to content. This module adds that: refuse a PR whose merge would delete
content that base HEAD already has and that was added strictly after the
PR's merge-base — a "stale revert".

Binding design condition (independent review on issue #1664, phase-1 PR
#1666 approval comment, `gh issue view 1664 --comments`): a naive 2-way
textual compare of base-HEAD vs head manufactures false refusals — a
stale branch that co-edits a file the base also independently grew,
with no overlapping hunks, is a case git's own 3-way merge integrates
cleanly with nothing lost, yet a raw content diff would flag it as a
"revert" anyway. `classify()` therefore simulates the actual merge (via
`git merge-file`, a local diff3 3-way merge — no network, no `gh` call)
of base-HEAD (current) x merge-base (ancestor) x head (other), and only
REFUSEs when that simulated result still lacks lines base HEAD has that
were added since the merge-base. A clean merge that preserves them, or a
conflict that doesn't touch them, ALLOWs.

  python3 gates/stale_revert_guard.py check <repo> <base_ref> <pr_merge_base_ref> <pr_head_ref>
"""
from __future__ import annotations
import difflib
import subprocess
import sys
import tempfile
from pathlib import Path

ALLOW = "ALLOW"
REFUSE = "REFUSE"


def _added_lines(merge_base_content: str, base_head_content: str) -> list[str]:
    """base HEAD 대비 merge-base 에 없던, C 이후 새로 추가된 줄들."""
    sm = difflib.SequenceMatcher(
        a=merge_base_content.splitlines(), b=base_head_content.splitlines())
    added: list[str] = []
    for tag, _, _, j1, j2 in sm.get_opcodes():
        if tag in ("insert", "replace"):
            added.extend(sm.b[j1:j2])
    return added


def _merge_file(current: str, base: str, other: str) -> tuple[bool, str]:
    """`git merge-file` 로 로컬 3-way 병합 시뮬레이션. 반환:
    `(clean: bool, merged_or_conflict_text: str)`. 네트워크 없음 — 임시
    파일에 대한 로컬 git 서브프로세스 호출뿐."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        cur_p, base_p, other_p = tdp / "current", tdp / "base", tdp / "other"
        cur_p.write_text(current)
        base_p.write_text(base)
        other_p.write_text(other)
        r = subprocess.run(
            ["git", "merge-file", "-p", str(cur_p), str(base_p), str(other_p)],
            capture_output=True, text=True)
        return r.returncode == 0, r.stdout


def _conflict_blocks(merged: str) -> list[tuple[list[str], list[str]]]:
    """`git merge-file` 충돌 마커 사이의 (ours, theirs) 줄 쌍 목록."""
    blocks: list[tuple[list[str], list[str]]] = []
    ours: list[str] | None = None
    theirs: list[str] | None = None
    for line in merged.splitlines():
        if line.startswith("<<<<<<<"):
            ours, theirs = [], None
        elif line.startswith("=======") and ours is not None and theirs is None:
            theirs = []
        elif line.startswith(">>>>>>>") and ours is not None and theirs is not None:
            blocks.append((ours, theirs))
            ours, theirs = None, None
        elif theirs is not None:
            theirs.append(line)
        elif ours is not None:
            ours.append(line)
    return blocks


def classify(base_head_content: str, merge_base_content: str, head_content: str,
             path: str = "") -> dict:
    """세 스냅샷(순수 텍스트, 파일/네트워크 접근 없음)에 대한 판정.
    `{"verdict": ALLOW|REFUSE, "reason": str, "path": path}`."""
    if merge_base_content == base_head_content:
        # merge-base 가 base HEAD 와 같다 -- 오늘과 동일하게 byte-identical
        # ALLOW (empty-state 인수 기준).
        return {"verdict": ALLOW, "reason": "merge-base가 base HEAD와 동일함", "path": path}

    added = _added_lines(merge_base_content, base_head_content)
    if not added:
        return {"verdict": ALLOW, "reason": "merge-base 이후 새로 추가된 줄 없음", "path": path}

    clean, merged = _merge_file(base_head_content, merge_base_content, head_content)

    if clean:
        merged_lines = set(merged.splitlines())
        lost = [line for line in added if line not in merged_lines]
        if not lost:
            return {"verdict": ALLOW, "reason": "시뮬레이션된 병합 결과가 추가된 내용을 보존함", "path": path}
        return {"verdict": REFUSE,
                "reason": f"{path}: 충돌 없는 병합인데도 merge-base 이후 추가된 내용이 사라짐(오래된(stale) merge-base)",
                "path": path}

    # 충돌: base HEAD 쪽(ours)에만 있고 head 쪽(theirs)엔 없는 추가된 줄이
    # 충돌 블록 안에 있으면, staleness 가 만들어낸 진짜 되돌림 위험이다.
    for ours, theirs in _conflict_blocks(merged):
        at_risk = [line for line in added if line in ours and line not in theirs]
        if at_risk:
            return {"verdict": REFUSE,
                    "reason": f"{path}: 병합이 merge-base 이후 추가된 내용과 충돌함(오래된(stale) merge-base)",
                    "path": path}
    return {"verdict": ALLOW, "reason": "충돌이 있지만 추가된 내용과는 무관함", "path": path}


def _git_show(repo: Path, ref: str, path: str) -> str:
    r = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=repo,
                        capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def changed_paths(repo: Path, merge_base_ref: str, head_ref: str) -> list[str]:
    r = subprocess.run(
        ["git", "diff", "--name-only", f"{merge_base_ref}..{head_ref}"],
        cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return []
    return [p for p in r.stdout.splitlines() if p]


def check_pr(repo: Path, base_ref: str, pr_merge_base_ref: str, pr_head_ref: str) -> list[dict]:
    """PR 이 건드린 각 경로에 대해 classify() 를 돌려 REFUSE 판정만
    모아 돌려준다. `pr_merge_base_ref` 는 이미 계산된 merge-base
    커밋(예: `git merge-base <base_ref> <pr_head_ref>` 결과)이어야 한다."""
    refusals: list[dict] = []
    for path in changed_paths(repo, pr_merge_base_ref, pr_head_ref):
        base_head_content = _git_show(repo, base_ref, path)
        merge_base_content = _git_show(repo, pr_merge_base_ref, path)
        head_content = _git_show(repo, pr_head_ref, path)
        verdict = classify(base_head_content, merge_base_content, head_content, path=path)
        if verdict["verdict"] == REFUSE:
            refusals.append(verdict)
    return refusals


def main() -> int:
    if len(sys.argv) != 6 or sys.argv[1] != "check":
        print("usage: stale_revert_guard.py check <repo> <base_ref> <pr_merge_base_ref> <pr_head_ref>")
        return 1
    repo, base_ref, merge_base_ref, head_ref = (
        Path(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5])
    refusals = check_pr(repo, base_ref, merge_base_ref, head_ref)
    if not refusals:
        print("허용: stale-revert 없음")
        return 0
    print("거절: stale revert 발견")
    for r in refusals:
        print(f"  - {r['reason']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
