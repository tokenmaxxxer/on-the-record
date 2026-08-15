"""이슈 #1491: standing-red zero policy — observe-only watchdog check.

`standing_red_check()` 가 fast tier(#1518 계약)를 유한 주기로 돌려 새로
red 가 된 테스트만 신호로 낸다. 이슈 acceptance 의 네 테스트 +
관찰-손실 회귀 가드 하나.
"""
import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn  # noqa: E402


def _init_git_repo(path: Path) -> str:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True)
    (path / "f.txt").write_text("1")
    subprocess.run(["git", "add", "f.txt"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=path, check=True)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=path,
                           capture_output=True, text=True, check=True).stdout.strip()


def _write_contract(root: Path, command: str) -> None:
    d = root / ".on-the-record"
    d.mkdir(parents=True, exist_ok=True)
    (d / "test-tiers.json").write_text(json.dumps({
        "fast": {"command": command, "budget_seconds": 60},
    }))


def _bump_commit(path: Path) -> str:
    (path / "f.txt").write_text(str(id(path)))
    subprocess.run(["git", "add", "f.txt"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "bump"], cwd=path, check=True)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=path,
                           capture_output=True, text=True, check=True).stdout.strip()


def _fake_pytest_script(root: Path, failing_ids) -> str:
    """진짜 pytest 대신 고정된 FAILED 요약을 찍는 스크립트 — 러너 세부와
    무관하게 파싱/카운팅 로직만 검증한다."""
    lines = "\n".join(f"FAILED {tid}" for tid in failing_ids)
    script = root / "fake_test_run.py"
    script.write_text(
        "import sys\n"
        f"print({lines!r})\n"
        "sys.exit(1)\n"
    )
    return f"{sys.executable} {script}"


def test_new_red_reported_once(tmp_path):
    root = tmp_path / "repo"
    tree_hash = _init_git_repo(root)
    _write_contract(root, _fake_pytest_script(root, ["tests/test_x.py::test_y"]))

    state = {}
    # empty-state: 상태 파일이 처음이면 현재 red 를 baseline 으로 즉시 보고
    signals1 = spawn.standing_red_check(state=state, now=0, root=root)
    assert signals1 == [f"standing-red: tests/test_x.py::test_y — 새 red, tree {tree_hash[:8]}"]

    # 같은 tree, 다음 틱 — 이미 보고된 red 는 재보고하지 않는다
    signals2 = spawn.standing_red_check(
        state=state, now=spawn.STANDING_RED_CADENCE_MIN * 60, root=root)
    assert signals2 == []


def test_flake_needs_two_consecutive(tmp_path):
    root = tmp_path / "repo"
    _init_git_repo(root)
    _write_contract(root, _fake_pytest_script(root, ["tests/test_x.py::test_y"]))

    state = {"standing_red": {}}  # non-empty state -> 정상 플레이크 게이트 적용
    signals1 = spawn.standing_red_check(state=state, now=0, root=root)
    assert signals1 == [], "same-tree 첫 실패는 아직 보고하지 않는다"
    assert state["standing_red"]["tests/test_x.py::test_y"]["consecutive_count"] == 1

    signals2 = spawn.standing_red_check(
        state=state, now=spawn.STANDING_RED_CADENCE_MIN * 60, root=root)
    assert len(signals2) == 1, "같은 tree 에서 두 번째 연속 실패는 보고한다"


def test_observe_only(tmp_path):
    root = tmp_path / "repo"
    _init_git_repo(root)
    _write_contract(root, _fake_pytest_script(root, ["tests/test_x.py::test_y"]))

    state = {}
    with mock.patch("spawn._post_session_end_comment") as post_comment, \
         mock.patch.object(spawn, "_maybe_resume_for_ready_pr") as resume:
        spawn.standing_red_check(state=state, now=0, root=root)
        spawn.standing_red_check(
            state=state, now=spawn.STANDING_RED_CADENCE_MIN * 60, root=root)
    post_comment.assert_not_called()
    resume.assert_not_called()
    # 관측 대상 저장소의 커밋된 트리 자체는 건드려지지 않았다 — HEAD 불변
    # (테스트 fixture 로 심어둔 미추적 파일은 관측 대상 아님)
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                           capture_output=True, text=True, check=True).stdout.strip()
    log = subprocess.run(["git", "-C", str(root), "log", "--oneline"],
                          capture_output=True, text=True, check=True).stdout
    assert log.count("\n") == 1


def test_rearm_on_tree_change(tmp_path):
    root = tmp_path / "repo"
    _init_git_repo(root)
    _write_contract(root, _fake_pytest_script(root, ["tests/test_x.py::test_y"]))

    state = {}
    spawn.standing_red_check(state=state, now=0, root=root)  # empty-state baseline report
    assert state["standing_red"]["tests/test_x.py::test_y"]["reported"] is True

    # tree 가 바뀌면 카운터가 리셋되고 재무장된다
    new_hash = _bump_commit(root)
    spawn.standing_red_check(
        state=state, now=spawn.STANDING_RED_CADENCE_MIN * 60, root=root)
    entry = state["standing_red"]["tests/test_x.py::test_y"]
    assert entry["tree_hash"] == new_hash
    assert entry["consecutive_count"] == 1
    assert entry["reported"] is False, "새 tree 에서는 아직 재보고 문턱을 안 넘었다"

    # 새 tree 에서 두 번째 연속 실패 -> 재보고
    signals = spawn.standing_red_check(
        state=state, now=2 * spawn.STANDING_RED_CADENCE_MIN * 60, root=root)
    assert len(signals) == 1


def test_no_contract_no_run(tmp_path):
    root = tmp_path / "repo"
    _init_git_repo(root)  # .on-the-record/test-tiers.json 없음

    state = {}
    with mock.patch("subprocess.run", wraps=subprocess.run) as run_spy:
        signals = spawn.standing_red_check(state=state, now=0, root=root)
    assert signals == []
    called_cmds = [c.args[0] for c in run_spy.call_args_list]
    assert not any("fake_test_run" in " ".join(map(str, c)) for c in called_cmds)


def test_cadence_gate_skips_before_interval(tmp_path):
    root = tmp_path / "repo"
    _init_git_repo(root)
    _write_contract(root, _fake_pytest_script(root, ["tests/test_x.py::test_y"]))

    state = {}
    spawn.standing_red_check(state=state, now=0, root=root)
    with mock.patch("subprocess.run", wraps=subprocess.run) as run_spy:
        signals = spawn.standing_red_check(state=state, now=60, root=root)  # 1분 후, 15분 미만
    assert signals == []
    assert not any("fake_test_run" in " ".join(map(str, c.args[0]))
                   for c in run_spy.call_args_list)


def test_observation_loss_regression_guard(tmp_path):
    """이슈 #1491 constraint: standing_red_check 추가가
    roster_watchdog() 의 기존 세션-이상 신호(watchdog_check_one 경로)를
    가리지 않는다 — standing-red 신호가 섞여도 기존 [watchdog] 신호는
    그대로 나온다."""
    root = tmp_path / "repo"
    _init_git_repo(root)
    _write_contract(root, _fake_pytest_script(root, ["tests/test_x.py::test_y"]))

    log_path = tmp_path / "session.log"
    log_path.write_text("old\n")
    entry = {
        "log": str(log_path), "work": str(root), "ts": 0.0,
        "issue": 1491, "role": "implementation", "pid": 999999999,
    }
    roster = {"issue-1491/implementation": entry}

    with mock.patch.object(spawn, "_roster_load", return_value=roster), \
         mock.patch.object(spawn, "_board_wide_sweep_all", return_value=0), \
         mock.patch.object(spawn, "standing_red_check", return_value=["fake signal"]), \
         mock.patch.object(spawn, "_undispositioned_role_prs", return_value=([], False)), \
         mock.patch.object(spawn, "_roster_own", return_value=roster), \
         mock.patch.object(spawn, "reconcile", return_value=[]), \
         mock.patch.object(spawn, "_alive", return_value=False), \
         mock.patch.object(spawn, "_post_session_end_comment"), \
         mock.patch.object(spawn, "ledger_check_and_stamp", return_value=True), \
         mock.patch.object(spawn, "diagnose_health",
                            return_value={"state": "STALLED", "detail": "d",
                                          "next_action": "n"}), \
         mock.patch.object(spawn, "_watchdog_state_load", return_value={}), \
         mock.patch.object(spawn, "_watchdog_state_save"), \
         mock.patch.object(spawn, "_respawn_state_load", return_value={}), \
         mock.patch("builtins.print") as mock_print:
        rc = spawn.roster_watchdog(root=root)

    printed = "\n".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
    assert "[standing-red] fake signal" in printed
    assert "STALLED" in printed, (
        "standing-red 신호가 섞여도 기존 poll-report/health 신호는 유실되지 않는다")
    assert rc >= 1  # standing-red 신호가 anomaly_count 에 반영된다
