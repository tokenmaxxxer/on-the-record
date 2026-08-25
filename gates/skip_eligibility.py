#!/usr/bin/env python3
"""issue #745 Item 3 — diff/risk-conditioned `execution-observation` spawn
eligibility (per docs/issue-745/proposals/item3-execution-observation-
conditioning.md, approved).

Three axes, checked against a landed diff and its landing record:

1. size        — non-docs changed lines (added+removed) >= 50
2. reversibility — diff touches a hard-to-revert path (`gates/*.py`,
   `on-the-record/hooks/*.sh`/`hooks.json`, `roles/*.json`, a
   `migrations/` path) or deletes any path
3. claim vocabulary — the landing record trips `claim_scan.CLAIM_RE`

`execution-observation` is skip-eligible (population S) only when ALL
three axes read low-risk; any single trip routes the PR to population R
(required). `#476`'s `fabrication_survival_rate` guardrail machinery is
untouched — this module only conditions whether the role is spawned.
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))
# issue #2226: same sibling-import collision and fix shape as
# `gates/record_lint.py` (see its comment for the full rationale, incl.
# why evicting `sys.modules["gates"]` was tried and rejected) — load
# `gates/gates.py` by explicit path under a private, process-shared key
# instead of a bare `import gates`, which under
# `python3 -m gates.skip_eligibility` would silently resolve to the
# namespace package instead.
import importlib.util as _importlib_util
_GATES_IMPL_KEY = "_on_the_record_gates_sibling_impl"
if _GATES_IMPL_KEY not in sys.modules:
    _spec = _importlib_util.spec_from_file_location(
        _GATES_IMPL_KEY, str(ROOT / "gates" / "gates.py"))
    _impl = _importlib_util.module_from_spec(_spec)
    sys.modules[_GATES_IMPL_KEY] = _impl
    _spec.loader.exec_module(_impl)
gates = sys.modules[_GATES_IMPL_KEY]  # noqa: E402
from claim_scan import CLAIM_RE  # noqa: E402

NON_DOCS_LINE_THRESHOLD = 50

HARD_TO_REVERT_RE = re.compile(
    r"^(gates/[^/]+\.py|on-the-record/hooks/[^/]+\.sh|"
    r"on-the-record/hooks/hooks\.json|roles/[^/]+\.json|(?:.*/)?migrations?/.*)$"
)


def non_docs_lines_changed(rows: list[tuple[int, int, str]]) -> int:
    """`rows`(`(added, removed, path)`) 중 `docs/` 밖 경로의 추가+삭제 합."""
    return sum(a + r for a, r, path in rows if not path.startswith("docs/"))


def hard_to_revert_hit(rows: list[tuple[int, int, str]],
                        deleted: set[str]) -> str | None:
    """축 2 — 걸린 첫 경로, 없으면 None. 삭제는 경로 패턴과 무관하게 걸린다."""
    for _, _, path in rows:
        if HARD_TO_REVERT_RE.match(path):
            return path
    for path in sorted(deleted):
        return path
    return None


def claim_vocabulary_hit(record_text: str) -> str | None:
    """축 3 — `claim_scan.CLAIM_RE` 매치 텍스트, 없으면 None."""
    m = CLAIM_RE.search(record_text or "")
    return m.group(0) if m else None


def classify_rows(rows: list[tuple[int, int, str]], deleted: set[str],
                   record_text: str) -> dict:
    """세 축을 순수 데이터로부터 판정한다 (I/O 없음, 테스트용 진입점)."""
    non_docs = non_docs_lines_changed(rows)
    hard_path = hard_to_revert_hit(rows, deleted)
    claim = claim_vocabulary_hit(record_text)

    size_trip = non_docs >= NON_DOCS_LINE_THRESHOLD
    reversibility_trip = hard_path is not None
    claim_trip = claim is not None
    required = size_trip or reversibility_trip or claim_trip

    return {
        "non_docs_lines_changed": non_docs,
        "size_axis_trip": size_trip,
        "hard_to_revert_path": hard_path,
        "reversibility_axis_trip": reversibility_trip,
        "claim_match": claim,
        "claim_axis_trip": claim_trip,
        "population": "R" if required else "S",
        "skip_eligible": not required,
    }


def _numstat(root: Path, base: str, ref: str) -> list[tuple[int, int, str]]:
    p = subprocess.run(
        ["git", "-C", str(root), "diff", "--numstat", f"{base}...{ref}"],
        capture_output=True, text=True)
    if p.returncode != 0 or not p.stdout.strip():
        return []
    rows = []
    for line in p.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        a, r, path = parts[0], parts[1], parts[2]
        added = int(a) if a.isdigit() else 0
        removed = int(r) if r.isdigit() else 0
        rows.append((added, removed, path))
    return rows


def _deleted_paths(root: Path, base: str, ref: str) -> set[str]:
    p = subprocess.run(
        ["git", "-C", str(root), "diff", "--diff-filter=D", "--name-only",
         f"{base}...{ref}"],
        capture_output=True, text=True)
    if p.returncode != 0:
        return set()
    return {l for l in p.stdout.strip().splitlines() if l}


def read_record_text(root: Path, ref: str, issue: int) -> str:
    """`ref`(브랜치/커밋)에서 `docs/issue-<issue>/reports/implementation.md`
    본문. 아직 없으면(phase-1만 랜딩) 빈 문자열 — 축 3이 그냥 안 걸린다."""
    p = subprocess.run(
        ["git", "-C", str(root), "show",
         f"{ref}:docs/issue-{issue}/reports/implementation.md"],
        capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else ""


def _ref_resolvable(root: Path, ref: str) -> bool:
    p = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", ref],
                        capture_output=True, text=True)
    return p.returncode == 0


def classify_for_subject(root: Path, subject: str, ref: str | None = None,
                          base: str | None = None) -> dict:
    """`subject`(예: `issue-745`)의 `<subject>/implementation` 브랜치를
    `base`(기본 `gates.BASE`) 대비 분류한다. `ref`/`base` 어느 쪽도
    resolve 되지 않으면(브랜치 없음/아직 fetch 안 됨) 예외로 실패시켜
    호출부가 fail-closed(population R 취급)로 처리하게 한다 — diff 를
    아예 못 본 상태를 조용히 population S 로 내주지 않는다."""
    issue = int(subject.split("-", 1)[1])
    ref = ref or f"{subject}/implementation"
    base = base or gates.BASE
    if not _ref_resolvable(root, ref) or not _ref_resolvable(root, base):
        raise RuntimeError(f"cannot resolve {ref!r} or {base!r} for classification")
    rows = _numstat(root, base, ref)
    deleted = _deleted_paths(root, base, ref)
    record_text = read_record_text(root, ref, issue)
    result = classify_rows(rows, deleted, record_text)
    result["subject"] = subject
    result["ref"] = ref
    return result
