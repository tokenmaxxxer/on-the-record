"""이슈 #1456: watchdog 단일-인스턴스 락 + 틱마다 코드-신선도 자가점검 +
canonical-체크아웃 가드 — #1360 재발(구코드를 물고 5시간 돌며 129건을
스폰한 독립 워치독) 방지."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn  # noqa: E402


def _init_git_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True)
    (path / "f.txt").write_text("1")
    subprocess.run(["git", "add", "f.txt"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=path, check=True)


def test_second_instance_exits_with_pointer_line(tmp_path):
    """이슈 #1456 요구 1 / 수용 (a): 첫 인스턴스가 락을 쥔 채면, 두 번째
    호출은 pid + 시작시각을 담은 안내줄과 함께 즉시 실패한다."""
    lock_path = tmp_path / "watchdog.lock"
    my_pid = os.getpid()
    ok1, msg1 = spawn.watchdog_lock_acquire(lock_path, pid=my_pid)
    assert ok1 and msg1 == ""

    ok2, msg2 = spawn.watchdog_lock_acquire(lock_path, pid=my_pid + 1)
    assert ok2 is False
    assert str(my_pid) in msg2
    assert "lock=" in msg2


def test_stale_lock_dead_pid_is_reclaimed(tmp_path):
    """이슈 #1456 요구 1 / 수용 (b): 죽은 pid 가 남긴 락은 자동 회수된다."""
    lock_path = tmp_path / "watchdog.lock"
    dead_pid = 999999
    while spawn._alive(dead_pid):
        dead_pid -= 1
    lock_path.write_text(json.dumps({"pid": dead_pid, "start_time": "123"}))

    ok, msg = spawn.watchdog_lock_acquire(lock_path, pid=os.getpid())
    assert ok is True
    assert msg == ""
    assert json.loads(lock_path.read_text())["pid"] == os.getpid()


def test_stale_lock_pid_reuse_start_time_mismatch_is_reclaimed(tmp_path):
    """이슈 #1456 요구 1 caveat: pid 는 살아있어도(재사용) 프로세스 시작
    시각이 락에 적힌 값과 다르면 다른 프로세스이므로 회수한다."""
    lock_path = tmp_path / "watchdog.lock"
    my_pid = os.getpid()
    real_start = spawn._proc_start_time(my_pid)
    assert real_start is not None
    lock_path.write_text(json.dumps({"pid": my_pid, "start_time": "not-" + real_start}))

    ok, msg = spawn.watchdog_lock_acquire(lock_path, pid=my_pid)
    assert ok is True
    assert msg == ""


def test_head_mismatch_tick_exits_nonzero_with_restart_line(tmp_path):
    """이슈 #1456 요구 2 / 수용 (c): 시작 시점 HEAD 와 현재 HEAD 가 다르면
    재기동-필요 줄을 찍고 실패로 보고한다."""
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    startup_head = spawn.watchdog_current_head(repo)
    assert startup_head is not None

    (repo / "f.txt").write_text("2")
    subprocess.run(["git", "add", "f.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "second"], cwd=repo, check=True)

    fresh, msg = spawn.watchdog_freshness_check(startup_head, cwd=repo, fetched_this_tick=True)
    assert fresh is False
    assert "재기동" in msg


def test_matching_head_ticks_proceed_normally(tmp_path):
    """이슈 #1456 요구 2 / 수용 (d): HEAD 가 그대로면 틱은 정상 진행된다
    (fresh=True, 안내줄 없음)."""
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    startup_head = spawn.watchdog_current_head(repo)

    fresh, msg = spawn.watchdog_freshness_check(startup_head, cwd=repo, fetched_this_tick=True)
    assert fresh is True
    assert msg == ""


def test_noncanonical_path_refused_unless_override(tmp_path, monkeypatch):
    """이슈 #1456 요구 3 / 수용 (e): 워치독 파일 경로가
    `~/.tokenmaxxxer/work/*` 같은 비-canonical 체크아웃 아래면 시작을
    거부하고, SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1 이면 통과시킨다."""
    work_base = tmp_path / "work-base"
    monkeypatch.setenv("MUSTER_WORK_DIR", str(work_base))
    noncanonical = work_base / "some-issue-role-workspace" / "spawn.py"
    noncanonical.parent.mkdir(parents=True, exist_ok=True)
    noncanonical.write_text("")

    monkeypatch.delenv("SPAWN_WATCHDOG_ALLOW_NONCANONICAL", raising=False)
    ok, msg = spawn.watchdog_canonical_guard(noncanonical)
    assert ok is False
    assert "비-canonical" in msg

    monkeypatch.setenv("SPAWN_WATCHDOG_ALLOW_NONCANONICAL", "1")
    ok, msg = spawn.watchdog_canonical_guard(noncanonical)
    assert ok is True
    assert msg == ""


def test_canonical_path_is_allowed(tmp_path, monkeypatch):
    """이슈 #1456 요구 3: canonical 체크아웃(워크스페이스 트리 밖)에서는
    가드를 그냥 통과한다."""
    work_base = tmp_path / "work-base"
    monkeypatch.setenv("MUSTER_WORK_DIR", str(work_base))
    monkeypatch.delenv("SPAWN_WATCHDOG_ALLOW_NONCANONICAL", raising=False)
    canonical = tmp_path / "board-checkout" / "spawn.py"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text("")

    ok, msg = spawn.watchdog_canonical_guard(canonical)
    assert ok is True
    assert msg == ""


def test_three_ticks_changed_unchanged_changed_again_alerts_twice(tmp_path):
    """이슈 #1755 수용: HEAD 가 바뀐 틱(1), 그대로인 틱(2), 다시 바뀐 틱(3)
    을 시뮬레이션 — 정확히 두 번만 안내줄이 난다(state_path dedup)."""
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    state_path = tmp_path / "watchdog-freshness-state.json"
    startup_head = spawn.watchdog_current_head(repo)

    (repo / "f.txt").write_text("2")
    subprocess.run(["git", "add", "f.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "second"], cwd=repo, check=True)

    fresh1, msg1 = spawn.watchdog_freshness_check(
        startup_head, cwd=repo, fetched_this_tick=True, state_path=state_path)
    assert fresh1 is False
    assert msg1 != ""

    fresh2, msg2 = spawn.watchdog_freshness_check(
        startup_head, cwd=repo, fetched_this_tick=True, state_path=state_path)
    assert fresh2 is False
    assert msg2 == ""

    (repo / "f.txt").write_text("3")
    subprocess.run(["git", "add", "f.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "third"], cwd=repo, check=True)

    fresh3, msg3 = spawn.watchdog_freshness_check(
        startup_head, cwd=repo, fetched_this_tick=True, state_path=state_path)
    assert fresh3 is False
    assert msg3 != ""

    alerts = [msg1, msg2, msg3]
    assert sum(1 for m in alerts if m) == 2


def test_freshness_dedup_empty_state_alerts_and_seeds_state(tmp_path):
    """이슈 #1755 empty-state 케이스: state 파일이 없으면 첫 관측은 알리고
    state 를 새로 만든다."""
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    state_path = tmp_path / "watchdog-freshness-state.json"
    assert not state_path.exists()
    startup_head = spawn.watchdog_current_head(repo)

    (repo / "f.txt").write_text("2")
    subprocess.run(["git", "add", "f.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "second"], cwd=repo, check=True)
    current = spawn.watchdog_current_head(repo)

    fresh, msg = spawn.watchdog_freshness_check(
        startup_head, cwd=repo, fetched_this_tick=True, state_path=state_path)
    assert fresh is False
    assert msg != ""
    assert state_path.exists()
    assert json.loads(state_path.read_text())["last_alerted_head"] == current


def test_empty_state_fresh_board_starts_normally_and_creates_lock(tmp_path):
    """이슈 #1456 수용 (f): 락 파일이 없는 신선한 보드는 정상 시작하며 락을
    새로 만든다."""
    lock_path = tmp_path / "runs" / "watchdog.lock"
    assert not lock_path.exists()

    ok, msg = spawn.watchdog_lock_acquire(lock_path, pid=os.getpid())
    assert ok is True
    assert msg == ""
    assert lock_path.exists()
    data = json.loads(lock_path.read_text())
    assert data["pid"] == os.getpid()
