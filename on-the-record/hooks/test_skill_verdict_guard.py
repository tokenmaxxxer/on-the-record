"""Tests for skill-verdict-guard.sh (issue #2039's per-mounted-skill
verdict obligation)."""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
HOOK = HOOKS_DIR / "skill-verdict-guard.sh"
GATES_DIR = HOOKS_DIR.parent.parent / "gates"

# Issue #2057: the verbatim "이 역할은 skill-repository(...)로 매핑됐다: ..."
# mounted-skill line as it actually appeared in the issue-2044 session's
# first user message (its 6 real skill names each carry a "Use ..."
# trigger sentence with internal commas -- the comma-split bug this
# regression guards against).
_ISSUE_2044_ROLE_MAPPED_LINE = (
    "이 역할은 skill-repository(이슈 #1955, #1758)로 매핑됐다: 스킬 "
    "implementation-complexity-coupling-management — Use when a class's "
    "coupling or cohesion metric crosses a threshold, a caller chains "
    "through nested accessors, a cross-module import direction is being "
    "introduced, or a pre-merge check pipeline needs ordering — decide "
    "whether to split, restructure, widen a contract, remove indirection, "
    "or reorder checks., implementation-design-pattern-selection — Use "
    "when deciding whether to introduce a GoF-style design pattern "
    "(Strategy, Factory, Visitor, Observer, Decorator) or keep the "
    "direct/procedural form, including when an existing pattern's "
    "indirection has only ever served one concrete case., "
    "implementation-performance-data-structure-choice — Use when "
    "choosing a data structure, algorithm, or communication scheme that "
    "could introduce a performance cliff — membership testing in a "
    "loop, comparing algorithms by asymptotic class, per-message "
    "connections, or a cache/index whose maintenance cost may now "
    "outweigh its benefit., implementation-blueprint — Use whenever you "
    "are about to produce non-trivial code spanning multiple modules or "
    "files and need to decide structure — \"how should I structure "
    "this\", \"what pattern should I use\", \"design the architecture\", "
    "\"이 코드 어떻게 구조화할까\", \"아키텍처 잡아줘\" — or before fanning "
    "work out to parallel workers and needing the contract to freeze., "
    "upstream-defect-report-convention — Use when preparing to file a "
    "defect against an upstream project and its issue template, required "
    "pre-submission steps, commit-linking convention, report channel, "
    "contributor tone, or duplicate-check surface haven't yet been "
    "matched to that project's actual current norms., "
    "conformance-review-severity-classification — Use while acting as "
    "the review role in the draft-reported state, when the review's "
    "scope has been explicitly extended into risk-weighting a finding "
    "already recorded by finding-record — not for ordinary "
    "fidelity-checking, and never to decide whether a finding exists. "
    "(skill-repository 5fadb31) 가이던스만 붙는다 — 집행은 core 훅뿐이다. "
    "(이 중 upstream-defect-report-convention, "
    "conformance-review-severity-classification 는 이번 과제 텍스트와의 "
    "키워드 매치로 추가된 크로스-패밀리 스킬 — 이슈 #2001)\n"
)

_ISSUE_2044_REAL_NAMES = [
    "implementation-complexity-coupling-management",
    "implementation-design-pattern-selection",
    "implementation-performance-data-structure-choice",
    "implementation-blueprint",
    "upstream-defect-report-convention",
    "conformance-review-severity-classification",
]


def _git(repo, *args):
    subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )


def _init_repo(repo, branch="issue-2039/implementation"):
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("init\n")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "init")
    _git(repo, "checkout", "-q", "-B", branch)


def _write_transcript(repo, first_user_text):
    transcript = repo / "transcript.jsonl"
    with transcript.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "type": "user",
            "message": {"role": "user", "content": first_user_text},
        }) + "\n")
        fh.write(json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": "did the work."},
        }) + "\n")
    return transcript


def _run(repo, transcript, orchestrate_off="", stop_hook_active=False):
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = orchestrate_off
    payload = json.dumps({
        "transcript_path": str(transcript),
        "stop_hook_active": stop_hook_active,
    })
    return subprocess.run(
        ["bash", str(HOOK)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
        cwd=str(repo),
    )


_MOUNTED_LINE = (
    "마운트된 스킬(--skills, 이슈 #1742/#1774): "
    "implementation-blueprint (Use whenever...) (trigger match)\n"
)

_ROLE_MAPPED_LINE = (
    "이 역할은 skill-repository(이슈 #1955, #1758)로 매핑됐다: "
    "스킬 implementation-blueprint, code-architecture "
    "(skill-repository abc1234) 가이던스만 붙는다 — 집행은 core 훅뿐이다.\n"
)


def _write_record(repo, body, role="implementation"):
    d = repo / "docs" / "issue-2039" / "reports"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{role}.md"
    p.write_text(body)
    return p


def t_zero_mounted_skills_is_noop():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(repo, "no skill lines here, just the task.")
        r = _run(repo, transcript)
        assert r.returncode == 0
        assert r.stdout == ""


def t_missing_skill_verdict_line_is_blocked():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(repo, _MOUNTED_LINE)
        _write_record(repo, "---\nloop_state: landed\n---\n\n## What did not work\nNone.\n")
        r = _run(repo, transcript)
        assert r.returncode == 0
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        assert "implementation-blueprint" in ctx


def t_empty_reason_skill_verdict_line_is_blocked():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(repo, _MOUNTED_LINE)
        _write_record(
            repo,
            "---\nloop_state: landed\n---\n\n"
            "skill-verdict: implementation-blueprint —\n\n"
            "## What did not work\nNone.\n")
        r = _run(repo, transcript)
        assert r.returncode == 0
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        assert "implementation-blueprint" in ctx


def t_both_assembly_points_union_without_double_count():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(repo, _MOUNTED_LINE + "\n" + _ROLE_MAPPED_LINE)
        _write_record(
            repo,
            "---\nloop_state: landed\n---\n\n"
            "skill-verdict: implementation-blueprint — applied: used it.\n"
            "skill-verdict: code-architecture — not-applicable: n/a.\n\n"
            "## What did not work\nNone.\n")
        r = _run(repo, transcript)
        assert r.returncode == 0
        assert r.stdout == ""


def t_satisfied_skill_verdicts_pass():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(repo, _MOUNTED_LINE)
        _write_record(
            repo,
            "---\nloop_state: landed\n---\n\n"
            "skill-verdict: implementation-blueprint — applied: used it at spawn.py:8181.\n\n"
            "## What did not work\nNone.\n")
        r = _run(repo, transcript)
        assert r.returncode == 0
        assert r.stdout == ""


def t_stop_hook_active_emits_nothing():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(repo, _MOUNTED_LINE)
        _write_record(repo, "---\nloop_state: landed\n---\n\n## What did not work\nNone.\n")
        r = _run(repo, transcript, stop_hook_active=True)
        assert r.returncode == 0
        assert r.stdout == ""


def t_malformed_payload_fails_closed():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        r = subprocess.run(
            ["bash", str(HOOK)],
            input="not json", capture_output=True, text=True,
            env=dict(os.environ, ORCHESTRATE_OFF=""), timeout=20, cwd=str(repo),
        )
        assert r.returncode == 2
        assert r.stdout == ""


def t_orchestrate_off_is_noop():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(repo, _MOUNTED_LINE)
        _write_record(repo, "---\nloop_state: landed\n---\n\n## What did not work\nNone.\n")
        r = _run(repo, transcript, orchestrate_off="1")
        assert r.returncode == 0
        assert r.stdout == ""


def _load_extract_names():
    """Pull `extract_names` out of the hook's embedded python heredoc
    and exec it standalone, so the regression test below exercises the
    real parser function rather than a reimplementation of it."""
    text = HOOK.read_text(encoding="utf-8")
    m = re.search(r"_NAME_RE = re\.compile.*?\n    return names\n", text, re.S)
    assert m, "could not locate extract_names in skill-verdict-guard.sh"
    ns = {"re": re}
    exec(m.group(0), ns)
    return ns["extract_names"]


def t_issue_2044_line_yields_exactly_six_real_names():
    """Issue #2057 regression: extract_names over the verbatim
    issue-2044 mounted-skill line must yield exactly its 6 real skill
    names, not the comma-fragmented bogus names ("restructure",
    "widen a contract", ...) the naive comma split used to fabricate."""
    extract_names = _load_extract_names()
    prefix = "이 역할은 skill-repository("
    line = _ISSUE_2044_ROLE_MAPPED_LINE.strip()
    assert line.startswith(prefix)
    names = extract_names(line[len(prefix):])
    assert names == _ISSUE_2044_REAL_NAMES


def t_issue_2044_line_with_all_six_verdicts_passes():
    """End-to-end: a record carrying exactly one skill-verdict line per
    the issue-2044 session's 6 real mounted skills passes clean -- the
    fabricated per-fragment demand issue #2057 reports never fires."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo, branch="issue-2044/implementation")
        transcript = _write_transcript(repo, _ISSUE_2044_ROLE_MAPPED_LINE)
        verdict_lines = "\n".join(
            f"skill-verdict: {name} — not-applicable: no fresh decision was open."
            for name in _ISSUE_2044_REAL_NAMES
        )
        d = repo / "docs" / "issue-2044" / "reports"
        d.mkdir(parents=True, exist_ok=True)
        (d / "implementation.md").write_text(
            "---\nloop_state: landed\n---\n\n"
            + verdict_lines
            + "\n\n## What did not work\nNone.\n"
        )
        r = _run(repo, transcript)
        assert r.returncode == 0
        assert r.stdout == ""
