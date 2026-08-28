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
untouched — this module only conditions whether execution-observation is
spawned.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))
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


# issue #2609: `classify_for_subject()` (and its private helpers
# `_numstat`/`_deleted_paths`/`read_record_text`/`_ref_resolvable`) are
# deleted here, not just their two dead `"implementation"` fallback
# strings (docs/issue-2593/reports/architecture-module-boundary-definition+
# architecture-decomposition-strategy-386ff408.md flagged the fallbacks
# alone as dead code, before the operator ruling on this issue's own Open
# finding 1 decided the skip-eligibility exemption goes entirely, not just
# its dead defaults). `classify_for_subject()`'s sole production caller,
# `spawn_on_pr.py`'s per-subject execution-observation skip-eligibility
# filter, is deleted in the same change (issue #2609: "every subject takes
# the same count requirement") -- confirmed zero remaining callers
# repo-wide (`grep -rn classify_for_subject` this session). `classify_rows`/
# `non_docs_lines_changed`/`hard_to_revert_hit`/`claim_vocabulary_hit`
# above stay: `trivial_lane_gate.py` still imports them directly, unrelated
# to the deleted per-subject wrapper.
