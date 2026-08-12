#!/usr/bin/env python3
"""issue #1098: post-landing verification obligation state machine.

  python3 -m pytest gates/test_landing_obligation.py
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import landing_obligation as lo
import reexecution_gate as rg


def t_open_writes_open_status(tmp_path):
    root = Path(tmp_path)
    lo.open_obligation(root, 1098, "implementation", 1101, "deadbeef")
    obligation = lo.read_obligation(root, 1098, "implementation", 1101)
    assert obligation.status == lo.OPEN
    assert obligation.pr == 1101
    assert obligation.sha == "deadbeef"


def t_open_is_idempotent_does_not_reset_opened_at(tmp_path):
    root = Path(tmp_path)
    lo.open_obligation(root, 1098, "implementation", 1101, "deadbeef")
    first = lo.read_obligation(root, 1098, "implementation", 1101)
    lo.open_obligation(root, 1098, "implementation", 1101, "cafebabe")
    second = lo.read_obligation(root, 1098, "implementation", 1101)
    assert first.opened_at == second.opened_at
    assert second.sha == "deadbeef"


def t_no_obligation_is_none(tmp_path):
    assert lo.read_obligation(Path(tmp_path), 1098, "implementation", 1101) is None


def t_resolve_with_no_obligation_is_none(tmp_path):
    root = Path(tmp_path)
    result = lo.resolve_with_reexecution_verdict(root, 1098, "implementation", 1101)
    assert result is None


def t_resolve_with_no_verdict_stays_open(tmp_path):
    root = Path(tmp_path)
    lo.open_obligation(root, 1098, "implementation", 1101, "deadbeef")
    result = lo.resolve_with_reexecution_verdict(root, 1098, "implementation", 1101)
    assert result.status == lo.OPEN


def t_pass_verdict_after_opening_resolves(tmp_path):
    root = Path(tmp_path)
    lo.open_obligation(root, 1098, "implementation", 1101, "deadbeef")
    obligation = lo.read_obligation(root, 1098, "implementation", 1101)
    v = rg.Verdict(rg.PASS, "pytest", "deadbeef", 0, "ok", obligation.opened_at + 1)
    rg.write_verdict(root, 1098, "implementation", v)
    result = lo.resolve_with_reexecution_verdict(root, 1098, "implementation", 1101)
    assert result.status == lo.RESOLVED


def t_fail_verdict_after_opening_marks_failing(tmp_path):
    root = Path(tmp_path)
    lo.open_obligation(root, 1098, "implementation", 1101, "deadbeef")
    obligation = lo.read_obligation(root, 1098, "implementation", 1101)
    v = rg.Verdict(rg.FAIL, "pytest", "deadbeef", 1, "boom", obligation.opened_at + 1)
    rg.write_verdict(root, 1098, "implementation", v)
    result = lo.resolve_with_reexecution_verdict(root, 1098, "implementation", 1101)
    assert result.status == lo.FAILING


def t_error_verdict_after_opening_marks_failing(tmp_path):
    root = Path(tmp_path)
    lo.open_obligation(root, 1098, "implementation", 1101, "deadbeef")
    obligation = lo.read_obligation(root, 1098, "implementation", 1101)
    v = rg.Verdict(rg.ERROR, "pytest", "deadbeef", None, "worktree fail",
                   obligation.opened_at + 1)
    rg.write_verdict(root, 1098, "implementation", v)
    result = lo.resolve_with_reexecution_verdict(root, 1098, "implementation", 1101)
    assert result.status == lo.FAILING


def t_verdict_predating_opening_is_ignored(tmp_path):
    """랜딩 이전에 찍힌 verdict는 이번 랜딩을 검증한 게 아니다 — resolve의
    근거가 될 수 없다."""
    root = Path(tmp_path)
    v = rg.Verdict(rg.PASS, "pytest", "oldsha", 0, "ok", 100.0)
    rg.write_verdict(root, 1098, "implementation", v)
    lo.open_obligation(root, 1098, "implementation", 1101, "deadbeef")
    result = lo.resolve_with_reexecution_verdict(root, 1098, "implementation", 1101)
    assert result.status == lo.OPEN


def t_list_open_obligations_no_directory_is_empty(tmp_path):
    assert lo.list_open_obligations(Path(tmp_path)) == []


def t_list_open_obligations_excludes_resolved(tmp_path):
    root = Path(tmp_path)
    lo.open_obligation(root, 1098, "implementation", 1101, "sha1")
    lo.open_obligation(root, 1099, "implementation", 1102, "sha2")
    obligation = lo.read_obligation(root, 1099, "implementation", 1102)
    v = rg.Verdict(rg.PASS, "pytest", "sha2", 0, "ok", obligation.opened_at + 1)
    rg.write_verdict(root, 1099, "implementation", v)
    lo.resolve_with_reexecution_verdict(root, 1099, "implementation", 1102)
    open_list = lo.list_open_obligations(root)
    assert len(open_list) == 1
    assert open_list[0].pr == 1101


def t_empty_state_stays_quiet(tmp_path):
    """issue #1098 acceptance: 검증이 깔끔히 통과한 랜딩은 추가 이슈를
    만들지 않는다 — resolve된 obligation은 open 목록에 남지 않는다."""
    root = Path(tmp_path)
    lo.open_obligation(root, 1098, "implementation", 1101, "deadbeef")
    obligation = lo.read_obligation(root, 1098, "implementation", 1101)
    v = rg.Verdict(rg.PASS, "pytest", "deadbeef", 0, "ok", obligation.opened_at + 1)
    rg.write_verdict(root, 1098, "implementation", v)
    lo.resolve_with_reexecution_verdict(root, 1098, "implementation", 1101)
    assert lo.list_open_obligations(root) == []
