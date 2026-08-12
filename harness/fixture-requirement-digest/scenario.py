"""issue #930 harness scenario — requirement digest & drift guard.

Follows the `harness/fixture-*` + `harness/driver.py` pattern the sibling
scenarios use, but this one does not need a live Claude Code session: the
four acceptance points from the merged design
(`docs/issue-930/proposals/requirement-digest-drift-guard.md` "How you
will know it worked") are all mechanically checkable — digest
condensation, hook deny/allow, digest-only task selection, and the
drift-guard's advisory-only firing — against `gates.requirement_digest`
and `spawn.requirement_drift` directly, on a seeded scratch repo.

`select_next_task_from_digest()` is the one place this scenario stands in
for "a fresh session reading only the digest": it is a plain, mechanical
selection over the digest's own `[status]` field (first non-`stale`,
non-`enforced` entry — i.e. the first entry still marked `open`), not a
simulated LLM. It exercises exactly what the acceptance point asks for —
that goal-aligned next-task selection is POSSIBLE from the digest alone,
with no other record in scope — without claiming a live model run this
scenario does not perform.

  python3 harness/fixture-requirement-digest/scenario.py
  exits 0 and prints all 4 acceptance rows PASS, non-zero otherwise.
"""
from __future__ import annotations
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = HARNESS_DIR.parent

sys.path.insert(0, str(REPO_ROOT / "gates"))
sys.path.insert(0, str(REPO_ROOT))
import requirement_digest as rd  # noqa: E402
import spawn  # noqa: E402

# 요구 3개(open/enforced/한 개는 check 경로가 나중에 사라짐), 그리고
# 기록 폭증을 흉내내는 다수의 synthetic docs/issue-* 파일 — 원장 line
# count 가 기록 수가 아니라 요구 수에만 비례함을 실증하는 게 목적.
_SEED_REGISTRY = """# Requirements Registry

## R001

quote: 첫 번째 살아있는 요구 — 아직 open
source_issue: 9001
check: gates/seed_check_a.py::check_a
status: open

## R002

quote: 두 번째 살아있는 요구 — 이미 enforced
source_issue: 9002
check: gates/seed_check_b.py::check_b
status: enforced

## R003

quote: check 경로가 사라질 예정인 요구 — --update 가 stale 로 고쳐써야 한다
source_issue: 9003
check: gates/seed_check_c.py::check_c
status: open
"""

_N_SYNTHETIC_RECORDS = 40


def _init_repo(d: Path) -> None:
    (d / "docs" / "specs").mkdir(parents=True)
    (d / "gates").mkdir(parents=True)
    (d / "docs" / "specs" / "requirements.md").write_text(_SEED_REGISTRY)
    (d / "gates" / "seed_check_a.py").write_text("")
    (d / "gates" / "seed_check_b.py").write_text("")
    (d / "gates" / "seed_check_c.py").write_text("")
    # 기록 폭증 흉내: 요구 수(3)와 무관하게 커지는 synthetic 기록들.
    for i in range(_N_SYNTHETIC_RECORDS):
        rec = d / "docs" / f"issue-{9100 + i}" / "reports" / "implementation.md"
        rec.parent.mkdir(parents=True, exist_ok=True)
        rec.write_text(f"# synthetic record {i}\n\nunrelated body text.\n")
    subprocess.run(["git", "init", "-q"], cwd=d, check=True)
    subprocess.run(["git", "add", "-A"], cwd=d, check=True)
    subprocess.run(["git", "-c", "user.email=h@h.com", "-c", "user.name=h",
                    "commit", "-q", "-m", "seed"], cwd=d, check=True)


def check_1_digest_line_count_is_requirement_count() -> list[str]:
    """acceptance point 2 (part a): digest line count == 3 (요구 수),
    40개 synthetic 기록이 있어도 record 수와 무관하다."""
    d = Path(tempfile.mkdtemp())
    try:
        _init_repo(d)
        rd.update(d)
        digest = (d / "docs" / "specs" / "requirement-digest.md").read_text()
        req_lines = [l for l in digest.splitlines() if l.startswith("- R")]
        problems = []
        if len(req_lines) != 3:
            problems.append(f"expected 3 requirement lines, got {len(req_lines)}: {req_lines}")
        return problems
    finally:
        shutil.rmtree(d)


def check_2_hook_deny_and_allow_and_stale_rewrite() -> list[str]:
    """acceptance point 2 (parts b+c): 훅이 digest 없는 커밋은 거부하고
    있는 커밋은 허용하며, check 경로가 사라진 항목은 --update 가
    requirements.md 안에서 stale 로 고쳐 쓴다."""
    d = Path(tempfile.mkdtemp())
    hook = REPO_ROOT / "on-the-record" / "hooks" / "requirement-digest-preflight.sh"
    problems = []
    try:
        _init_repo(d)
        rd.update(d)
        subprocess.run(["git", "add", "-A"], cwd=d, check=True)
        subprocess.run(["git", "-c", "user.email=h@h.com", "-c", "user.name=h",
                        "commit", "-q", "-m", "digest base"], cwd=d, check=True)

        # R003 의 check 경로 삭제 후, requirements.md 만 고쳐서 stage —
        # digest 는 아직 안 맞는 상태.
        (d / "gates" / "seed_check_c.py").unlink()
        text = (d / "docs" / "specs" / "requirements.md").read_text()
        (d / "docs" / "specs" / "requirements.md").write_text(text + "\n")
        subprocess.run(["git", "add", "docs/specs/requirements.md"], cwd=d, check=True)

        import json
        payload = json.dumps({"tool_name": "Bash",
                              "tool_input": {"command": "git commit -m x"}})
        r = subprocess.run(["bash", str(hook)], cwd=d, input=payload,
                           capture_output=True, text=True)
        if r.returncode != 2:
            problems.append(f"expected deny (rc=2) with no digest staged, got rc={r.returncode}: {r.stderr}")

        rd.update(d)
        reg_after = (d / "docs" / "specs" / "requirements.md").read_text()
        r003 = next(e for e in rd.parse(reg_after) if e["id"] == "R003")
        if r003["status"] != "stale":
            problems.append(f"expected R003 rewritten to stale after --update, got {r003['status']!r}")
        digest_after = (d / "docs" / "specs" / "requirement-digest.md").read_text()
        if "R003" in digest_after:
            problems.append("expected R003 excluded from digest after going stale")

        subprocess.run(["git", "add", "-A"], cwd=d, check=True)
        r2 = subprocess.run(["bash", str(hook)], cwd=d, input=payload,
                            capture_output=True, text=True)
        if r2.returncode != 0:
            problems.append(f"expected allow (rc=0) with matching digest staged, got rc={r2.returncode}: {r2.stderr}")
        return problems
    finally:
        shutil.rmtree(d)


def select_next_task_from_digest(digest_text: str) -> str | None:
    """digest 텍스트 하나만 주어졌을 때(다른 기록 없음), 목표-정렬된 다음
    작업으로 첫 `open` 상태 요구 ID 를 고른다. "fresh session, digest-only"
    선택 로직의 기계적 구현 — 실제 LLM 세션이 아니라, digest 만으로
    목표-정렬 선택이 가능하다는 acceptance 주장 자체를 검사 가능한
    형태로 실행한다."""
    m = re.search(r"^- (R\d+): .+ \[open\]", digest_text, re.M)
    return m.group(1) if m else None


def check_3_fresh_session_digest_only_selects_aligned_task() -> list[str]:
    """acceptance point 3: digest 만 주어진 세션이 여전히 open 인 요구
    ID 를 골라야 한다 — R002 는 이미 enforced 라 골라서는 안 된다."""
    d = Path(tempfile.mkdtemp())
    try:
        _init_repo(d)
        rd.update(d)
        digest = (d / "docs" / "specs" / "requirement-digest.md").read_text()
        chosen = select_next_task_from_digest(digest)
        problems = []
        if chosen != "R001":
            problems.append(f"expected digest-only selection to pick R001 (first open), got {chosen!r}")
        return problems
    finally:
        shutil.rmtree(d)


def check_4_drift_guard_advisory_only() -> list[str]:
    """acceptance point 4: requirement_drift() 는 gh 실패를 포함해 절대
    예외를 던지지 않고, 아무 것도 anomaly_count/커밋에 반영하지 않는다
    (advisory, non-blocking) — 함수 시그니처 자체가 반환값 없음(None)."""
    d = Path(tempfile.mkdtemp())
    problems = []
    try:
        _init_repo(d)
        rd.update(d)
        result = spawn.requirement_drift(d)
        if result is not None:
            problems.append(f"expected requirement_drift() to return None (advisory print-only), got {result!r}")
        return problems
    finally:
        shutil.rmtree(d)


def check_5_no_workflows_touched() -> list[str]:
    """req#7 wiring check: 이 이슈의 변경이 `.github/workflows/` 를
    건드리지 않았는지 실제 git diff 로 확인한다."""
    r = subprocess.run(
        ["git", "diff", "--stat", "main...HEAD", "--", ".github/workflows/"],
        cwd=REPO_ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        return [f"git diff failed: {r.stderr.strip()}"]
    if r.stdout.strip():
        return [f"expected no .github/workflows/ changes, got: {r.stdout.strip()}"]
    return []


CHECKS = [
    ("digest condenses to requirement-count, not record-count", check_1_digest_line_count_is_requirement_count),
    ("hook denies/allows correctly, stale rewrite lands", check_2_hook_deny_and_allow_and_stale_rewrite),
    ("fresh digest-only selection is goal-aligned", check_3_fresh_session_digest_only_selects_aligned_task),
    ("drift guard fires advisory-only, never blocking", check_4_drift_guard_advisory_only),
    ("no .github/workflows/ changes (req#7)", check_5_no_workflows_touched),
]


def run() -> int:
    failures = 0
    for name, fn in CHECKS:
        problems = fn()
        if problems:
            failures += 1
            print(f"FAIL {name}")
            for p in problems:
                print(f"  - {p}")
        else:
            print(f"PASS {name}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run())
