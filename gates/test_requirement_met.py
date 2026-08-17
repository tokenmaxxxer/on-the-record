#!/usr/bin/env python3
"""issue #1651 — `gates/requirement_met.py` 단위 테스트.
네트워크 없음, `grade()` 순수 함수만 픽스처로 검사한다.

  python3 -m pytest gates/test_requirement_met.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import requirement_met as rm


_BODY = """## Acceptance
- check: unit test at `gates/test_requirement_met.py` runs and passes.
  provenance: executed-unit
- check: live check at `gates/requirement_met.py` runs against a real PR.
  provenance: executed-live
"""


def t_yes_with_artifact_present_in_diff_passes():
    diff = (
        "diff --git a/gates/test_requirement_met.py b/gates/test_requirement_met.py\n"
        "--- a/gates/test_requirement_met.py\n"
        "+++ b/gates/test_requirement_met.py\n"
        "+def t_new(): assert Path('gates/test_requirement_met.py').exists()\n"
    )
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.YES,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is False
    assert result["blocking_reasons"] == []


def t_yes_with_artifact_absent_from_diff_fails():
    diff = "diff --git a/other.py b/other.py\n+pass\n"
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.YES,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is True
    assert len(result["blocking_reasons"]) == 1
    assert "gates/test_requirement_met.py" in result["blocking_reasons"][0]


def t_no_verdict_never_blocks_even_without_artifact():
    diff = "diff --git a/other.py b/other.py\n+pass\n"
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.NO,
        "live check at `gates/requirement_met.py` runs against a real PR.": rm.NO,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is False


def t_unknown_verdict_never_blocks():
    diff = "diff --git a/other.py b/other.py\n+pass\n"
    result = rm.grade(_BODY, diff, {})
    assert result["blocked"] is False
    for c in result["criteria"]:
        assert c["verdict"] == rm.UNKNOWN
        assert c["blocking_fail"] is False


def t_yes_with_no_cited_artifact_at_all_blocks():
    body = """## Acceptance
- check: reviewers agree this looks fine.
  provenance: read
"""
    diff = "diff --git a/anything.py b/anything.py\n+pass\n"
    verdicts = {"reviewers agree this looks fine.": rm.YES}
    result = rm.grade(body, diff, verdicts)
    assert result["blocked"] is True


def t_semantic_verdict_is_advisory_only_recorded_not_blocking_by_itself():
    """NO/UNKNOWN semantic verdicts never block on their own — only the
    deterministic artifact-presence sub-check (YES + missing artifact)
    blocks. This asserts the separation the issue requires."""
    diff = (
        "diff --git a/gates/test_requirement_met.py b/gates/test_requirement_met.py\n"
        "+++ b/gates/test_requirement_met.py\n"
        "+# python3 gates/test_requirement_met.py\n"
        "diff --git a/gates/requirement_met.py b/gates/requirement_met.py\n"
        "+++ b/gates/requirement_met.py\n"
        "+# python3 gates/requirement_met.py\n"
    )
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.NO,
        "live check at `gates/requirement_met.py` runs against a real PR.": rm.UNKNOWN,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is False
    kinds = {c["raw"]: c["verdict"] for c in result["criteria"]}
    assert kinds["unit test at `gates/test_requirement_met.py` runs and passes."] == rm.NO
    assert kinds["live check at `gates/requirement_met.py` runs against a real PR."] == rm.UNKNOWN


def t_empty_state_no_check_bullets_is_distinct_result():
    body = "## Acceptance\nunverifiable: this is a subjective UX judgment.\n"
    result = rm.grade(body, "diff --git a/x b/x\n", {})
    assert result["empty_state"] is True
    assert result["criteria"] == []
    assert result["blocked"] is False
    assert "reason" in result


def t_empty_state_no_acceptance_section_is_distinct_result():
    body = "Just a plain issue with no headings."
    result = rm.grade(body, "diff --git a/x b/x\n", {})
    assert result["empty_state"] is True
    assert result["blocked"] is False


def t_multiple_criteria_one_blocking_one_not():
    diff = (
        "diff --git a/gates/test_requirement_met.py b/gates/test_requirement_met.py\n"
        "+++ b/gates/test_requirement_met.py\n"
        "+def t_new(): assert Path('gates/test_requirement_met.py').exists()\n"
    )
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.YES,
        "live check at `gates/requirement_met.py` runs against a real PR.": rm.YES,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is True
    assert len(result["blocking_reasons"]) == 1


def t_red_artifact_named_only_in_diff_header_prose_fails():
    """issue #1660 (#1651 리뷰 픽스, red case): 경로가 diff의 파일 헤더
    줄(`diff --git`/`---`/`+++`)에만 등장하고 실제 추가 hunk 라인에는
    등장하지 않으면 — "prose 로 경로만 이름 붙인 것" — 더 이상 통과하지
    않는다."""
    diff = (
        "diff --git a/gates/test_requirement_met.py b/gates/test_requirement_met.py\n"
        "index abc123..def456 100644\n"
        "--- a/gates/test_requirement_met.py\n"
        "+++ b/gates/test_requirement_met.py\n"
        "+pass\n"
    )
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.YES,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is True
    assert "gates/test_requirement_met.py" in result["blocking_reasons"][0]


def t_green_artifact_in_added_hunk_line_passes():
    """issue #1660 (#1651/#1661 리뷰 픽스, green case): 경로가 실제
    추가된 코드/테스트 hunk 라인 안에(주석이 아닌 진짜 코드로) 문자열로
    등장하면 통과한다."""
    diff = (
        "diff --git a/gates/test_requirement_met.py b/gates/test_requirement_met.py\n"
        "--- a/gates/test_requirement_met.py\n"
        "+++ b/gates/test_requirement_met.py\n"
        "+def t_new(): assert Path('gates/test_requirement_met.py').exists()\n"
    )
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.YES,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is False
    assert result["blocking_reasons"] == []


def t_red_artifact_named_only_in_added_markdown_line_fails():
    """issue #1660 (#1661 리뷰 픽스, red case): 아티팩트 경로가 오직
    추가된 `.md` 산문 라인에서만 이름으로 언급되고 실제 코드/테스트가
    바뀌지 않았다면 — self-attestation theater — 여전히 블록해야
    한다."""
    diff = (
        "diff --git a/docs/report.md b/docs/report.md\n"
        "--- a/docs/report.md\n"
        "+++ b/docs/report.md\n"
        "+We updated `gates/test_requirement_met.py` to cover this.\n"
    )
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.YES,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is True
    assert "gates/test_requirement_met.py" in result["blocking_reasons"][0]


def t_red_artifact_named_only_in_added_comment_line_fails():
    """issue #1660 (#1661 리뷰 픽스, red case): 아티팩트 경로가 코드
    파일 안이어도 주석 전용 추가 라인에만 등장하면 여전히 블록한다."""
    diff = (
        "diff --git a/gates/test_requirement_met.py b/gates/test_requirement_met.py\n"
        "--- a/gates/test_requirement_met.py\n"
        "+++ b/gates/test_requirement_met.py\n"
        "+# see gates/test_requirement_met.py for details\n"
    )
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.YES,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is True
    assert "gates/test_requirement_met.py" in result["blocking_reasons"][0]


def t_check_surfaces_per_criterion_advisory_record():
    """issue #1660: `check()`가 기준별 semantic verdict 를 advisory 로
    노출한다 — blocking_reasons 와 분리된 별도 키."""
    import unittest.mock as mock

    with mock.patch.object(rm.gh_rest, "fetch_issue_body", return_value=_BODY), \
         mock.patch.object(rm, "_pr_diff", return_value=(
             "diff --git a/gates/test_requirement_met.py b/gates/test_requirement_met.py\n"
             "+++ b/gates/test_requirement_met.py\n"
             "+# python3 gates/test_requirement_met.py\n")):
        result = rm.check(Path("."), 1651, 1, {
            "unit test at `gates/test_requirement_met.py` runs and passes.": rm.NO,
        })
    assert result["blocked"] is False
    assert len(result["advisory"]) == 2
    kinds = {a["raw"]: a["verdict"] for a in result["advisory"]}
    assert kinds["unit test at `gates/test_requirement_met.py` runs and passes."] == rm.NO
    assert kinds["live check at `gates/requirement_met.py` runs against a real PR."] == rm.UNKNOWN


_COMMAND_BODY = """## Acceptance
- check: cron job runs the installed line `python3 -m devdigest`.
  provenance: executed-live
"""


def t_command_identity_mismatch_blocks_even_without_yes_verdict():
    """issue #1696 — pilot-devdigest PR #6 shape: the recorded proof ran
    `python3 -m devdigest.cli` (a sibling, PYTHONPATH-dependent path)
    while the check names the installed `python3 -m devdigest` line. The
    deterministic layer must flag this regardless of the semantic
    verdict — it is a structural mismatch, not a judgment call."""
    diff = (
        "diff --git a/docs/issue-1/reports/implementation.md b/docs/issue-1/reports/implementation.md\n"
        "+++ b/docs/issue-1/reports/implementation.md\n"
        "+acceptance: PYTHONPATH=src python3 -m devdigest.cli — result: PASS\n"
    )
    result = rm.grade(_COMMAND_BODY, diff, {})
    assert result["blocked"] is True
    assert any("command-identity" in r for r in result["blocking_reasons"])
    crit = result["criteria"][0]
    assert crit["command_identity_mismatch"] is True


def t_command_identity_match_does_not_block():
    diff = (
        "diff --git a/docs/issue-1/reports/implementation.md b/docs/issue-1/reports/implementation.md\n"
        "+++ b/docs/issue-1/reports/implementation.md\n"
        "+acceptance: python3 -m devdigest — result: PASS\n"
    )
    result = rm.grade(_COMMAND_BODY, diff, {})
    assert result["blocked"] is False
    assert result["criteria"][0]["command_identity_mismatch"] is False


def t_command_identity_no_recorded_command_does_not_block():
    """No `acceptance:` citation in the diff at all — nothing to compare
    against, so the deterministic layer stays silent rather than
    guessing (false positive prevention)."""
    diff = "diff --git a/other.py b/other.py\n+++ b/other.py\n+pass\n"
    result = rm.grade(_COMMAND_BODY, diff, {})
    assert result["blocked"] is False
    assert result["criteria"][0]["command_identity_mismatch"] is False


def t_command_identity_ignored_for_executed_unit_provenance():
    body = """## Acceptance
- check: unit test runs `python3 -m devdigest`.
  provenance: executed-unit
"""
    diff = (
        "diff --git a/x.md b/x.md\n+++ b/x.md\n"
        "+acceptance: PYTHONPATH=src python3 -m devdigest.cli — result: PASS\n"
    )
    result = rm.grade(body, diff, {})
    assert result["criteria"][0]["command_identity_mismatch"] is False


def t_command_identity_flags_leading_token_mismatch_with_single_citation():
    """warrant-hunt finding 2026-08-17: `python` named vs `python3`
    actually run must not slip past the same-first-token filter when
    there is exactly one recorded citation to pair it with."""
    body = """## Acceptance
- check: cron job runs the installed line `python devdigest.py`.
  provenance: executed-live
"""
    diff = (
        "diff --git a/x.md b/x.md\n+++ b/x.md\n"
        "+acceptance: python3 devdigest.py — result: PASS\n"
    )
    result = rm.grade(body, diff, {})
    assert result["blocked"] is True
    assert result["criteria"][0]["command_identity_mismatch"] is True


def t_command_identity_flags_env_prefix_only_difference():
    """PR #1699 review defect 1: `PYTHONPATH=src python3 -m devdigest`
    recorded against a check naming `python3 -m devdigest` must NOT be
    normalized into a match — env-prefix is the exact crutch the
    command-identity rule forbids, so a prefix-only difference is a
    mismatch, even with >=2 citations in the diff (multi-citation path)."""
    diff = (
        "diff --git a/x.md b/x.md\n+++ b/x.md\n"
        "+acceptance: PYTHONPATH=src python3 -m devdigest — result: PASS\n"
        "+acceptance: other unrelated command — result: PASS\n"
    )
    result = rm.grade(_COMMAND_BODY, diff, {})
    assert result["blocked"] is True
    assert result["criteria"][0]["command_identity_mismatch"] is True


def t_command_identity_strips_cd_wrapper_head_for_candidate_matching():
    """PR #1699 review defect 2: with >=2 acceptance citations, a
    `cd src && python3 -m devdigest` recorded command must not silently
    escape the same-first-token candidate filter (its literal leading
    token is `cd`, not `python3`) — after stripping the cd head it
    matches the check's named command exactly, so no mismatch."""
    diff = (
        "diff --git a/x.md b/x.md\n+++ b/x.md\n"
        "+acceptance: cd src && python3 -m devdigest — result: PASS\n"
        "+acceptance: other unrelated command — result: PASS\n"
    )
    result = rm.grade(_COMMAND_BODY, diff, {})
    assert result["blocked"] is False
    assert result["criteria"][0]["command_identity_mismatch"] is False


def t_command_identity_flags_mismatch_inside_cd_wrapper_head():
    """Companion to the above: the cd/wrapper-head fallback must still
    catch a genuine mismatch, not just let wrapped commands through
    unconditionally — `cd src && python3 -m devdigest.cli` differs from
    the named `python3 -m devdigest` even after the cd head is stripped."""
    diff = (
        "diff --git a/x.md b/x.md\n+++ b/x.md\n"
        "+acceptance: cd src && python3 -m devdigest.cli — result: PASS\n"
        "+acceptance: other unrelated command — result: PASS\n"
    )
    result = rm.grade(_COMMAND_BODY, diff, {})
    assert result["blocked"] is True
    assert result["criteria"][0]["command_identity_mismatch"] is True


def _run(fn):
    try:
        fn()
        print(f"ok  {fn.__name__}")
        return True
    except AssertionError as e:
        print(f"FAIL {fn.__name__}: {e}")
        return False


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    results = [_run(t) for t in tests]
    ok = all(results)
    print(f"{sum(results)}/{len(results)} passed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
