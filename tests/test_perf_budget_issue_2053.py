"""Regression test for issue #2053: per-occurrence standalone budget guard
for the three new engagement/matching/reporting stages -- skill-verdict-guard
(record-write/Stop), BM25 four-surface scoring (spawn), and the
report-framing-check skills-utilization extension (Stop).

Method mirrors issue #2016's phase-2 measurement: standalone (outside the
Claude Code harness), file-based payloads (never a `gh pr`/`git commit`
literal inline in a command string), timed with `time.monotonic()`.

Budgets (issue #2053 Acceptance): skill-verdict-guard.sh and BM25 scoring
each <200ms per occurrence, measured standalone. The `skill_judge` consult
is the only permitted network call and only at spawn time -- never inside
these three per-occurrence stages, so this test also asserts none of the
three shells out to `gh`/the consult path.
"""
import importlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = REPO_ROOT / "on-the-record" / "hooks"
BUDGET_SECONDS = 0.200

_MOUNTED_LINE = (
    "마운트된 스킬(--skills, 이슈 #1742/#1774): "
    "implementation-blueprint (Use whenever...) (trigger match)\n"
    "이 역할은 skill-repository(이슈 #1955, #1758)로 매핑됐다: 스킬 "
    "implementation-complexity-coupling-management — Use when a class's "
    "coupling or cohesion metric crosses a threshold, a caller chains "
    "through nested accessors, a cross-module import direction is being "
    "introduced, or a pre-merge check pipeline needs ordering — decide "
    "whether to split, restructure, widen a contract, remove indirection, "
    "or reorder checks., implementation-blueprint — Use whenever you are "
    "about to produce non-trivial code spanning multiple modules or files "
    "and need to decide structure. (skill-repository 5fadb31) 가이던스만 "
    "붙는다 — 집행은 core 훅뿐이다.\n"
)


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                    text=True)


def _init_repo(repo):
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("init\n")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "init")
    _git(repo, "checkout", "-q", "-B", "issue-2053/implementation")
    reports = repo / "docs" / "issue-2053" / "reports"
    reports.mkdir(parents=True)
    (reports / "implementation.md").write_text(
        "skill-verdict: implementation-blueprint — applied: fixture | "
        "not-applicable: n/a\n"
    )


def _write_payload_file(path, obj):
    path.write_text(json.dumps(obj))


def _time_calls(fn, reps=5):
    times = []
    for _ in range(reps):
        t0 = time.monotonic()
        fn()
        times.append(time.monotonic() - t0)
    return times


def test_skill_verdict_guard_standalone_budget(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    transcript = tmp_path / "transcript.jsonl"
    with transcript.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "type": "user",
            "message": {"role": "user", "content": _MOUNTED_LINE},
        }) + "\n")
    payload_path = tmp_path / "svg_payload.json"
    _write_payload_file(payload_path, {
        "transcript_path": str(transcript),
        "stop_hook_active": False,
    })

    def run_once():
        payload_text = payload_path.read_text()
        return subprocess.run(
            ["bash", str(HOOKS_DIR / "skill-verdict-guard.sh")],
            input=payload_text, capture_output=True, text=True, timeout=20,
            cwd=str(repo),
        )

    times = _time_calls(run_once)
    assert max(times) < BUDGET_SECONDS, (
        f"skill-verdict-guard.sh standalone max {max(times):.4f}s exceeds "
        f"the {BUDGET_SECONDS}s budget (reps={times})"
    )


def test_report_framing_check_standalone_budget(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    msg = (
        "1단계: 완료.\n"
        "이슈 #2053 관련 작업을 해결(fix)했다 -- 이전에는 이 문제 때문에 "
        "비용이 들었지만(previously cost) 이제는 가능해졌다(now possible). "
        "아직 남은 부분(still open)도 있다. 스킬 implementation-blueprint "
        "적용: fixture.\n"
    )
    payload_path = tmp_path / "rfc_payload.json"
    _write_payload_file(payload_path, {
        "last_assistant_message": msg,
        "stop_hook_active": False,
    })

    def run_once():
        payload_text = payload_path.read_text()
        env = dict(os.environ)
        env.pop("CLAUDE_ROLE", None)
        env["REPORT_FRAMING_REPO"] = str(repo)
        return subprocess.run(
            ["bash", str(HOOKS_DIR / "report-framing-check.sh")],
            input=payload_text, capture_output=True, text=True, timeout=20,
            cwd=str(repo), env=env,
        )

    times = _time_calls(run_once)
    assert max(times) < BUDGET_SECONDS, (
        f"report-framing-check.sh standalone max {max(times):.4f}s exceeds "
        f"the {BUDGET_SECONDS}s budget (reps={times})"
    )


def test_bm25_cross_family_scores_standalone_budget():
    sys.path.insert(0, str(REPO_ROOT))
    spawn = importlib.import_module("spawn")
    task_text = (
        "class coupling metric crosses a threshold and caller chains "
        "through nested accessors, deciding whether to split or widen a "
        "contract, GoF design pattern strategy factory, performance data "
        "structure choice, architecture blueprint design"
    )

    def run_once():
        return spawn._bm25_cross_family_scores(
            task_text, "implementation", spawn._skill_repo_root())

    times = _time_calls(run_once)
    assert max(times) < BUDGET_SECONDS, (
        f"_bm25_cross_family_scores standalone max {max(times):.4f}s "
        f"exceeds the {BUDGET_SECONDS}s budget (reps={times})"
    )


def test_bm25_scoring_makes_no_network_or_consult_call():
    """Acceptance (b): the `skill_judge` consult is the only permitted
    network call, and only at spawn -- never inside the per-occurrence
    BM25 scoring stage itself. `_bm25_cross_family_scores` must not call
    `subprocess` at all (pure in-process tokenizing/scoring over
    already-read SKILL.md files)."""
    src = (REPO_ROOT / "spawn.py").read_text(encoding="utf-8")
    m = re.search(
        r"def _bm25_cross_family_scores\(.*?\n(?=\ndef _cross_family_skill_matches\()",
        src, re.S)
    assert m, "could not locate _bm25_cross_family_scores body in spawn.py"
    body = m.group(0)
    assert "subprocess" not in body, (
        "_bm25_cross_family_scores must not shell out -- any network/"
        "process call belongs only to the spawn-time skill_judge consult"
    )


def test_skill_verdict_guard_makes_no_network_call():
    src = (HOOKS_DIR / "skill-verdict-guard.sh").read_text(encoding="utf-8")
    assert not re.search(r"\bgh\b|\bcurl\b|\bwget\b", src), (
        "skill-verdict-guard.sh must not make network calls -- it only "
        "reads the transcript file and runs `git rev-parse` locally"
    )


def test_report_framing_check_makes_no_network_call():
    src = (HOOKS_DIR / "report-framing-check.sh").read_text(encoding="utf-8")
    assert not re.search(r"\bgh\b|\bcurl\b|\bwget\b", src), (
        "report-framing-check.sh must not make network calls -- it only "
        "scans the reply text and the local docs/ tree"
    )
