#!/usr/bin/env python3
"""요구사항 원장(digest) 생성기 (issue #930, northpole req#6).

`docs/specs/requirements.md` 는 append-only 원시 레지스트리라 레코드가
쌓일수록 훑어 읽기 비용이 커진다. 이 모듈은 그 파일에서 살아있는(=
`stale` 이 아닌) 요구사항만 한 줄씩 응축한 `docs/specs/requirement-digest.md`
를 만든다 — 새 세션이 이 파일 하나만 읽고 "지금 살아있는 요구가 무엇인지"
재구성할 수 있게 하는 게 목적이다. 렌더 비용은 요구사항 개수에만
비례한다(O(요구 수)) — 원시 레지스트리에 딸린 과거 기록·이슈·PR 총량과는
무관하다.

`update()` 는 렌더 직전에 각 항목의 `check` 경로가 여전히 HEAD 에
존재하는지 재확인하고, 더 이상 존재하지 않으면 그 항목의 `status:` 줄을
`stale` 로 제자리에서 고쳐 쓴다 — `requirements.md` 자신의 필드 설명이
이미 "computed by gates.requirement_registry" 라고 약속하는 필드이므로,
이 모듈이 그 계산을 실제로 수행하는 지점이다.

  python3 gates/requirement_digest.py [<repo 경로>]              # 검사 모드
  python3 gates/requirement_digest.py [<repo 경로>] --update      # 갱신
  종료 코드 0 통과(또는 --update 완료) / 1 차단
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

_REGISTRY_REL = "docs/specs/requirements.md"
_DIGEST_REL = "docs/specs/requirement-digest.md"
_REQ_HEADING = re.compile(r"^##\s+(R\d+)\s*$")
_REQ_FIELD = re.compile(r"^([a-z_]+):\s*(.*)$")
_REQ_REQUIRED = ("quote", "source_issue", "check", "status")
_MAX_PARAPHRASE = 120


def parse(text: str) -> list[dict[str, str]]:
    """`requirements.md` 텍스트를 `## R###` 블록 목록으로 파싱한다. 필수
    필드가 빠진 블록은 건너뛴다(레지스트리 자신의 파싱 차단은
    `gates.requirement_registry` 의 몫 — 여기는 렌더만 담당)."""
    entries: list[dict[str, str]] = []
    current_id: str | None = None
    current: dict[str, str] = {}

    def flush() -> None:
        if current_id is None:
            return
        if all(f in current for f in _REQ_REQUIRED):
            entries.append({"id": current_id, **current})

    for line in text.splitlines():
        m = _REQ_HEADING.match(line)
        if m:
            flush()
            current_id, current = m.group(1), {}
            continue
        m = _REQ_FIELD.match(line.strip())
        if m and current_id is not None:
            current[m.group(1)] = m.group(2).strip()
    flush()
    return entries


def _paraphrase(quote: str) -> str:
    q = " ".join(quote.split())
    if len(q) <= _MAX_PARAPHRASE:
        return q
    return q[: _MAX_PARAPHRASE - 1].rstrip() + "…"


def render(entries: list[dict[str, str]]) -> str:
    """`stale` 이 아닌 항목만 한 줄씩 응축한 digest 본문을 반환한다."""
    lines = [
        "# Requirement Digest (auto-generated — do not hand-edit)",
        "",
        f"Source: `{_REGISTRY_REL}`. Regenerate: "
        "`python3 gates/requirement_digest.py --update`.",
        "",
    ]
    live = [e for e in entries if e.get("status") != "stale"]
    if not live:
        lines.append("(no live requirements)")
    for e in live:
        lines.append(
            f"- {e['id']}: {_paraphrase(e['quote'])} [{e['status']}] "
            f"(source: #{e['source_issue']})"
        )
    lines.append("")
    return "\n".join(lines)


def _rewrite_stale(root: Path, registry_path: Path) -> str:
    """`check` 경로가 더 이상 HEAD 에 없는 항목의 `status:` 줄을 `stale`
    로 제자리에서 고쳐 쓴 새 레지스트리 텍스트를 반환한다. 파일 자체는
    쓰지 않는다 — 호출자가 원자적으로 쓴다."""
    text = registry_path.read_text(encoding="utf-8-sig", errors="replace")
    entries = parse(text)
    dead_ids = set()
    for e in entries:
        check = e["check"]
        if check.startswith("UNVERIFIABLE:"):
            continue
        if e.get("status") == "stale":
            continue
        path = check.split("::", 1)[0].strip()
        if not path or not (root / path).exists():
            dead_ids.add(e["id"])
    if not dead_ids:
        return text

    out_lines = []
    current_id: str | None = None
    for line in text.splitlines(keepends=True):
        m = _REQ_HEADING.match(line.rstrip("\n"))
        if m:
            current_id = m.group(1)
            out_lines.append(line)
            continue
        m = _REQ_FIELD.match(line.strip())
        if m and m.group(1) == "status" and current_id in dead_ids:
            nl = "\n" if line.endswith("\n") else ""
            out_lines.append(f"status: stale{nl}")
            continue
        out_lines.append(line)
    return "".join(out_lines)


def check(repo: Path) -> list[str]:
    """차단 사유 목록. 비어 있으면 통과. 레지스트리가 없으면 검사할 게
    없다로 통과시킨다(digest 자신이 첫 커밋에서 아직 없을 수 있다)."""
    registry_path = repo / _REGISTRY_REL
    if not registry_path.exists():
        return []
    text = registry_path.read_text(encoding="utf-8-sig", errors="replace")
    entries = parse(text)
    expected = render(entries)
    digest_path = repo / _DIGEST_REL
    if not digest_path.exists():
        return [f"{_DIGEST_REL} 없음 — `python3 gates/requirement_digest.py "
                 f"--update` 로 생성하라"]
    actual = digest_path.read_text(encoding="utf-8", errors="replace")
    if actual != expected:
        return [f"{_DIGEST_REL} 이 현재 {_REGISTRY_REL} 내용과 불일치 — "
                 f"`python3 gates/requirement_digest.py --update` 로 재생성하라"]
    return []


def update(repo: Path) -> None:
    """`stale` 재계산 후 `requirement-digest.md` 를 재생성해 쓴다."""
    registry_path = repo / _REGISTRY_REL
    if not registry_path.exists():
        return
    rewritten = _rewrite_stale(repo, registry_path)
    if rewritten != registry_path.read_text(encoding="utf-8-sig", errors="replace"):
        registry_path.write_text(rewritten, encoding="utf-8")
    entries = parse(rewritten)
    digest_path = repo / _DIGEST_REL
    digest_path.parent.mkdir(parents=True, exist_ok=True)
    digest_path.write_text(render(entries), encoding="utf-8")


def main() -> int:
    argv = sys.argv[1:]
    do_update = "--update" in argv
    positional = [a for a in argv if a != "--update"]
    repo = Path(positional[0] if positional else ".").resolve()
    if do_update:
        update(repo)
        print(f"{_DIGEST_REL} 갱신됨")
        return 0
    bad = check(repo)
    if bad:
        print("게이트 차단:")
        for b in bad:
            print(f"  - {b}")
        return 1
    print(f"통과: {_DIGEST_REL} 이 {_REGISTRY_REL} 과 일치한다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
