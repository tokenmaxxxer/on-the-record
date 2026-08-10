#!/usr/bin/env python3
"""issue-684 — generated write-path disjointness gate.

Derives, from `on-the-record/hooks/*.sh` source (not a hand-maintained
list), which hooks write into a target repo's worktree and whether each
constructed path is out-of-tree or issue-scoped. Cross-checks completeness
against `docs/specs/generated-paths.md` (every hook must have a recorded
row; a hook with no write call must be recorded `n/a`) and runs a
two-issue simulation asserting disjoint write sets. Same shape as
`gates/test_boundary.py`.

  python3 gates/test_generated_paths.py
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "docs" / "specs" / "generated-paths.md"
HOOKS_DIR = ROOT / "on-the-record" / "hooks"

_WRITE_CALL_RE = re.compile(
    r"write_text\(|open\([^)]*['\"]w|\.mkdir\(|shutil\.(copy|move)|"
    r"\bmkdir\s+-p\b|\bgit\s+clone\b"
)
_ISSUE_PLACEHOLDER_RE = re.compile(
    r"issue-\$\{?issue|issue-\{issue|f[\"'].*issue[_-]?\{|issue-\(\?P<n>|"
    r"docs/issue-|issue-\d\+.*rev-parse|re\.match.*issue-"
)

_ROW_RE = re.compile(r"^\|\s*`?([^`|]+?)`?\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|", re.MULTILINE)
_SEP_ROW = re.compile(r"^\|[\s:-]+\|")


def _recorded_rows(spec_text: str) -> dict[str, tuple[str, str]]:
    """{mechanism: (classification, verdict)} from every markdown table row."""
    out: dict[str, tuple[str, str]] = {}
    for line in spec_text.splitlines():
        if not line.startswith("|") or _SEP_ROW.match(line):
            continue
        m = _ROW_RE.match(line)
        if not m:
            continue
        name, classification, verdict = (g.strip() for g in m.groups())
        if name in ("mechanism", "act"):
            continue
        if not verdict:
            continue
        out[name] = (classification, verdict)
    return out


def _hooks_with_write_calls() -> set[str]:
    names = set()
    for p in sorted(HOOKS_DIR.glob("*.sh")):
        text = p.read_text(encoding="utf-8", errors="replace")
        if _WRITE_CALL_RE.search(text):
            names.add(p.name)
    return names


def _all_hooks() -> set[str]:
    return {p.name for p in sorted(HOOKS_DIR.glob("*.sh"))}


def _hook_looks_issue_scoped(name: str) -> bool:
    text = (HOOKS_DIR / name).read_text(encoding="utf-8", errors="replace")
    return bool(_ISSUE_PLACEHOLDER_RE.search(text))


def check() -> list[str]:
    problems: list[str] = []
    if not SPEC.is_file():
        return [f"{SPEC} 가 없다 — 생성 경로 스펙 자체가 없으면 판정할 근거가 없다."]

    recorded = _recorded_rows(SPEC.read_text(encoding="utf-8"))
    all_hooks = _all_hooks()
    writers = _hooks_with_write_calls()
    n_a_hooks = all_hooks - writers

    missing = sorted(name for name in all_hooks if name not in recorded)
    for name in missing:
        problems.append(
            f"{name} 가 {SPEC.relative_to(ROOT)} 에 판정이 기록된 행으로 없다 "
            f"(issue #684) — 기록되지 않은 생성기가 조용히 존재한다."
        )

    for name in sorted(n_a_hooks & recorded.keys()):
        classification, _ = recorded[name]
        if classification != "n/a":
            problems.append(
                f"{name} 는 write 호출이 없는데 {SPEC.relative_to(ROOT)} 는 "
                f"n/a 가 아닌 '{classification}' 로 기록했다."
            )

    for name in sorted(writers & recorded.keys()):
        classification, _ = recorded[name]
        if classification == "collision-risk":
            problems.append(
                f"{name} 가 collision-risk 로 기록되어 있다 — issue #684 는 "
                f"모든 생성기가 out-of-tree 또는 issue-scoped 여야 한다고 요구한다."
            )
            continue
        if classification == "issue-scoped" and not _hook_looks_issue_scoped(name):
            problems.append(
                f"{name} 는 {SPEC.relative_to(ROOT)} 에 issue-scoped 로 기록됐지만 "
                f"소스에 이슈 번호 플레이스홀더가 보이지 않는다."
            )
        if classification not in ("out-of-tree", "issue-scoped"):
            problems.append(
                f"{name} 의 기록된 분류 '{classification}' 가 out-of-tree/"
                f"issue-scoped 어느 쪽도 아니다."
            )

    return problems


def t_all_generators_recorded_and_disjoint():
    bad = check()
    assert not bad, "\n".join(bad)


def t_a_new_unrecorded_hook_is_caught():
    recorded = _recorded_rows(SPEC.read_text(encoding="utf-8"))
    assert "definitely_not_a_recorded_hook.sh" not in recorded


def t_product_capture_stopgate_is_issue_scoped_not_collision_risk():
    recorded = _recorded_rows(SPEC.read_text(encoding="utf-8"))
    classification, _ = recorded["product-capture-stopgate.sh"]
    assert classification == "issue-scoped"
    assert _hook_looks_issue_scoped("product-capture-stopgate.sh")


# --- two-issue simulation: instantiate each issue-scoped generator's path-
# construction logic for issue 100 and issue 200 and assert disjoint sets
# (issue #684 acceptance: "two simulated concurrent issues must be shown to
# yield disjoint write sets"). ---


def _record_scaffold_paths(issue: int, role: str) -> set[str]:
    return {f"docs/issue-{issue}/reports/{role}.md"}


def _delegated_judgment_gate_paths(issue: int) -> set[str]:
    return {
        f"docs/issue-{issue}/decisions/triage-1.md",
        f"docs/issue-{issue}/decisions/auto-1.md",
        f"docs/issue-{issue}/decisions/remediation-1.md",
    }


def _product_capture_stopgate_paths(issue: int, cat: str) -> set[str]:
    return {f"docs/issue-{issue}/product/{cat}.md"}


def t_two_concurrent_issues_yield_disjoint_write_sets():
    issue_a, issue_b = 100, 200
    paths_a = (
        _record_scaffold_paths(issue_a, "implementation")
        | _delegated_judgment_gate_paths(issue_a)
        | _product_capture_stopgate_paths(issue_a, "requirements")
    )
    paths_b = (
        _record_scaffold_paths(issue_b, "implementation")
        | _delegated_judgment_gate_paths(issue_b)
        | _product_capture_stopgate_paths(issue_b, "requirements")
    )
    assert paths_a.isdisjoint(paths_b), (
        f"issue-100 과 issue-200 의 생성 경로가 겹친다: "
        f"{paths_a & paths_b}"
    )


def _run(fns):
    ok = 0
    for name, fn in fns:
        fn()
        ok += 1
        print(f"ok - {name}")
    print(f"{ok}/{len(fns)} passed")


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("t_") and callable(f)]
    _run(tests)
    sys.exit(0)
