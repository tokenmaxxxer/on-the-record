"""Tests for gates/patrol_wiring.py (issue #1597 E1): kill-switch
short-circuit, should_fire honored, 3-role cap counted from judge_cmd
HITS only (binding review correction, PR #1601 — a raw trace-line count
would exhaust the cap after 3 prefilter MISSES), and the respawn
regression test proposal item 5 requires (mid-flow process restart must
not re-trigger on patrol's own artifacts, run as genuinely separate
subprocess invocations)."""
import json
import subprocess
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import patrol_wiring as pw  # noqa: E402
import patrol_queue as pq  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "README.md").write_text("init\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    return repo


def _commit(repo: Path, rel_path: str, content: str) -> str:
    p = repo / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    subprocess.run(["git", "add", rel_path], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", f"touch {rel_path}"], cwd=repo, check=True)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True,
                          text=True, check=True).stdout.strip()
    return sha


def test_kill_switch_short_circuits(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / ".on-the-record").mkdir()
    (repo / pw.KILL_SWITCH_REL_PATH).write_text("")
    sha = _commit(repo, "src/app.py", "x = 1\n")

    def boom(*a, **k):
        raise AssertionError("judge_cmd must not be called when kill-switch is active")

    result = pw.run(str(repo), sha, judge_cmd=boom)
    assert result == {"skipped": True, "reason": "kill_switch"}


def test_kill_switch_helper_is_shared_and_checks_presence_only(tmp_path):
    repo = _init_repo(tmp_path)
    assert pw.kill_switch_active(repo) is False
    (repo / ".on-the-record").mkdir()
    (repo / pw.KILL_SWITCH_REL_PATH).write_text("")
    assert pw.kill_switch_active(repo) is True


def test_should_fire_honored_patrol_artifact_only_event_skips(tmp_path):
    repo = _init_repo(tmp_path)
    sha = _commit(repo, pq.QUEUE_REL_PATH, '{"fingerprint": "x"}\n')

    def boom(*a, **k):
        raise AssertionError("judge_cmd must not be called when should_fire is False")

    result = pw.run(str(repo), sha, judge_cmd=boom)
    assert result == {"skipped": True, "reason": "should_fire_false"}


def test_role_cap_stops_at_three_hits(tmp_path):
    repo = _init_repo(tmp_path)
    sha = _commit(repo, "src/app.py", "x = 1\n")

    calls = []

    def stub(role, merge_sha, cwd=None):
        calls.append(role)
        return {"skipped": False, "role": role, "merge": merge_sha, "enqueued": []}

    result = pw.run(str(repo), sha, judge_cmd=stub)
    assert result["hits"] == 3
    assert len(calls) == 3


def test_three_prefilter_misses_do_not_exhaust_cap(tmp_path):
    """Binding review correction (PR #1601): the cap counts HITS, not raw
    attempts — 3 prefilter misses followed by a real hit must still let
    that hit (and up to 2 more) through, not stop the loop at attempt 3."""
    repo = _init_repo(tmp_path)
    sha = _commit(repo, "src/app.py", "x = 1\n")

    calls = []

    def stub(role, merge_sha, cwd=None):
        calls.append(role)
        if len(calls) <= 3:
            return {"skipped": True, "reason": "prefilter_miss", "role": role, "merge": merge_sha}
        return {"skipped": False, "role": role, "merge": merge_sha, "enqueued": []}

    result = pw.run(str(repo), sha, judge_cmd=stub)
    assert result["hits"] == 3
    assert len(calls) == 6  # 3 misses + 3 hits, not capped off after the misses


def test_board_run_gated_on_nonempty_enqueued(tmp_path):
    repo = _init_repo(tmp_path)
    sha = _commit(repo, "src/app.py", "x = 1\n")

    board_calls = []

    def fake_run_patrol_board(root, role, queue_path, dry_run, date):
        board_calls.append(role)
        return {"wrote": True}

    def stub(role, merge_sha, cwd=None):
        enqueued = ["fp1"] if role == "accessibility" else []
        return {"skipped": False, "role": role, "merge": merge_sha, "enqueued": enqueued}

    orig = pw.patrol_board.run_patrol_board
    pw.patrol_board.run_patrol_board = fake_run_patrol_board
    try:
        result = pw.run(str(repo), sha, judge_cmd=stub)
    finally:
        pw.patrol_board.run_patrol_board = orig

    assert board_calls == ["accessibility"]
    assert result["board_roles"] == ["accessibility"]


def test_respawn_mid_flow_does_not_reenqueue_or_bypass_artifact_guard(tmp_path):
    """Proposal item 5: simulate a watchdog killing and restarting the
    process mid-flow, as two genuinely separate subprocess invocations
    sharing the same on-disk state, and assert (a) the respawned run
    does not re-enqueue work the first (killed) run already completed
    and recorded, and (b) a patrol-artifact-only event still returns
    should_fire=False across the respawn boundary."""
    repo = _init_repo(tmp_path)
    sha = _commit(repo, "src/app.py", "x = 1\n")
    calls_log = tmp_path / "calls.json"
    calls_log.write_text("[]")

    driver = textwrap.dedent(f"""
        import json, sys
        sys.path.insert(0, {str(ROOT / "gates")!r})
        import patrol_wiring as pw

        calls_log = {str(calls_log)!r}

        def stub(role, merge_sha, cwd=None):
            calls = json.loads(open(calls_log).read())
            already_hit = any(r == role for r in calls)
            if already_hit:
                # judge_cmd's own per-merge cap already covers this role for
                # this merge sha -- a respawned run must not redo it.
                return {{"skipped": True, "reason": "already_recorded",
                        "role": role, "merge": merge_sha}}
            if role != "accessibility":
                return {{"skipped": True, "reason": "prefilter_miss",
                        "role": role, "merge": merge_sha}}
            calls.append(role)
            open(calls_log, "w").write(json.dumps(calls))
            return {{"skipped": False, "role": role, "merge": merge_sha,
                    "enqueued": ["fp-respawn"]}}

        pw.patrol_board.run_patrol_board = lambda *a, **k: {{"wrote": True}}
        result = pw.run({str(repo)!r}, {sha!r}, judge_cmd=stub)
        print(json.dumps(result))
    """)

    first = subprocess.run([sys.executable, "-c", driver], capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    first_result = json.loads(first.stdout.strip().splitlines()[-1])
    assert first_result["board_roles"] == ["accessibility"]

    # Simulated watchdog respawn: a fresh process, same merge sha, same
    # on-disk calls_log state left by the killed first process.
    second = subprocess.run([sys.executable, "-c", driver], capture_output=True, text=True)
    assert second.returncode == 0, second.stderr
    second_result = json.loads(second.stdout.strip().splitlines()[-1])
    # The role already recorded by the first process must not re-enqueue.
    assert second_result["board_roles"] == []
    assert json.loads(calls_log.read_text()) == ["accessibility"]

    # (b) artifact-only event still refuses to fire across the respawn boundary.
    artifact_sha = _commit(repo, pq.QUEUE_REL_PATH, '{"fingerprint": "y"}\n')
    driver_artifact = driver.replace(repr(sha), repr(artifact_sha))
    third = subprocess.run([sys.executable, "-c", driver_artifact], capture_output=True, text=True)
    assert third.returncode == 0, third.stderr
    third_result = json.loads(third.stdout.strip().splitlines()[-1])
    assert third_result == {"skipped": True, "reason": "should_fire_false"}


def test_one_role_judge_cmd_exception_does_not_abort_later_roles(tmp_path, capsys):
    """issue #1607: judge_cmd raising for one role must not abort the
    per-role loop -- later roles (alphabetically after the raiser) must
    still be invoked, and an error trace line must be emitted."""
    repo = _init_repo(tmp_path)
    sha = _commit(repo, "src/app.py", "x = 1\n")

    calls = []
    known = pw._known_roles()
    raiser_role = known[0]
    later_role = known[1]

    def stub(role, merge_sha, cwd=None):
        calls.append(role)
        if role == raiser_role:
            raise RuntimeError("live session failure, empty stderr")
        return {"skipped": False, "role": role, "merge": merge_sha, "enqueued": []}

    result = pw.run(str(repo), sha, judge_cmd=stub)

    assert raiser_role in calls
    assert later_role in calls
    out = capsys.readouterr().out
    assert f"role={raiser_role} errored (RuntimeError): continuing" in out
    assert result["hits"] == pw.MAX_ROLES_PER_MERGE
