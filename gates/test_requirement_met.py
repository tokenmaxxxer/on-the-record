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
    diff = "diff --git a/gates/test_requirement_met.py b/gates/test_requirement_met.py\n+pass\n"
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
    diff = "diff --git a/gates/test_requirement_met.py b/gates/test_requirement_met.py\n+pass\ndiff --git a/gates/requirement_met.py b/gates/requirement_met.py\n+pass\n"
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
    diff = "diff --git a/gates/test_requirement_met.py b/gates/test_requirement_met.py\n+pass\n"
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.YES,
        "live check at `gates/requirement_met.py` runs against a real PR.": rm.YES,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is True
    assert len(result["blocking_reasons"]) == 1


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
