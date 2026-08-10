#!/usr/bin/env python3
"""UI-facing executed-live 증거 게이트 (issue-685).

diff 가 화면(UI) 표면을 건드리는데 레코드가 `verdict: pass` 를 주장하면,
`provenance: executed-live` 줄에 증거 참조(실행 로그/스크린샷 경로/
헬스체크 출력)가 함께 있어야 한다 — unit 테스트만으로 통과를 주장한
델리버리가 실제로는 죽은 화면을 냈던 사고(issue-685)를 막는다.

존재-검사만 한다: 증거 참조가 실제로 그 화면을 보여주는지는 검사하지
않는다 — 이 레포의 다른 provenance 검사(`acceptance_gate.py`,
docs/issue-474/decisions/416-provenance-and-empty-state.md)와 같은
rigor.
"""
from __future__ import annotations
import re
from pathlib import Path

_GLOBS_HEADING = re.compile(r"(?im)^#{1,6}\s*globs\s*$")
_NEXT_HEADING = re.compile(r"(?m)^#{1,6}\s")

# fallback: docs/specs/ui-surfaces.md 가 없거나 선언이 비어 있을 때만 쓰인다.
_FALLBACK_EXTS = (".tsx", ".jsx", ".vue", ".svelte", ".html")
_FALLBACK_DIRS = ("/components/", "/pages/", "/views/", "/screens/", "/ui/")

_PROVENANCE_LIVE = re.compile(
    r"^\s*[-*]?\s*provenance\s*:\s*executed-live\s*(?:[-:—]\s*(\S.*))?$",
    re.IGNORECASE | re.MULTILINE)


def _declared_globs(root: Path) -> list[str] | None:
    """`docs/specs/ui-surfaces.md` 의 `## Globs` 절을 읽는다.

    반환: None = 선언 없음(파일 없음 또는 절 비어 있음) → fallback 적용.
    빈 리스트 = `none` 으로 명시적으로 fallback 을 껐다.
    비어있지 않은 리스트 = 선언된 glob 들만 사용.
    """
    spec = root / "docs" / "specs" / "ui-surfaces.md"
    if not spec.exists():
        return None
    text = spec.read_text(encoding="utf-8", errors="replace")
    m = _GLOBS_HEADING.search(text)
    if not m:
        return None
    rest = text[m.end():]
    nxt = _NEXT_HEADING.search(rest)
    section = rest[: nxt.start()] if nxt else rest
    lines = [ln.strip() for ln in section.splitlines() if ln.strip()]
    if not lines:
        return None
    if lines == ["none"]:
        return []
    return lines


def _fallback_matches(path: str) -> bool:
    p = path.lower()
    if p.endswith(_FALLBACK_EXTS):
        return True
    return any(seg in f"/{p}" for seg in _FALLBACK_DIRS)


def is_ui_facing(root: Path, changed_paths: list[str]) -> bool:
    """diff 로 변경된 경로 중 하나라도 UI-facing 이면 True.

    선언(`docs/specs/ui-surfaces.md`)이 있으면 그 glob 만 쓴다(`none` 은
    fallback 을 끄고 항상 False). 선언이 없거나 비어 있으면 fail-closed
    fallback 패턴을 쓴다.
    """
    import fnmatch
    globs = _declared_globs(root)
    if globs is None:
        return any(_fallback_matches(p) for p in changed_paths)
    if not globs:
        return False
    return any(fnmatch.fnmatch(p, g) for p in changed_paths for g in globs)


def check_record(root: Path, record_path: str, record_text: str,
                  changed_paths: list[str]) -> list[str]:
    """레코드가 `verdict: pass` 를 주장하는데 diff 가 UI-facing 이면
    `provenance: executed-live` + 증거 참조를 요구한다."""
    import gates
    fm = gates.record_frontmatter(record_text)
    if fm.get("verdict") != "pass":
        return []
    if not is_ui_facing(root, changed_paths):
        return []
    m = _PROVENANCE_LIVE.search(record_text)
    if m and m.group(1):
        return []
    return [
        f"{record_path}: diff 가 UI 표면을 건드리는데 verdict: pass 인 "
        f"레코드에 'provenance: executed-live' 증거가 없다 — 화면이 실제로 "
        f"실행됐다는 증거(실행 로그 경로/스크린샷 경로/헬스체크 출력)를 "
        f"명시해야 한다. 예: "
        f"'provenance: executed-live — screenshot: docs/issue-685/_assets/"
        f"screen.png'"
    ]
