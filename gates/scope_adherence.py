#!/usr/bin/env python3
"""Scope-adherence landing gate — issue #1658 (northpole req#6).

(Issue #2559: the static role write_scope this module's design note used
to lean on for context — "the static gate already blocks writes outside a
role's area" — is gone; sessions are no longer scope-limited by role at
all.) This module's own mechanism is unrelated and unaffected: an issue's
`scope: <prefix list>` field, opted into per-issue in the issue body, not
derived from the (now-deleted) role catalog. It still catches INTENT drift: an issue
"fix the login bug" whose PR wanders into an unrelated module can diverge
from what the issue asked even though nothing blocks the write itself
anymore. File paths are deterministic (not an LLM judgment), so a
landing-time trajectory-vs-goal check can block this safely without
touching mid-flight watch-coverage.

Same shape as `gates/landing_readiness.py`: a pure `classify()` on
`{scope: frozenset[str] | None, pr_files: frozenset[str]}`, plus a
gh-wrapped `check()`.

  python3 gates/scope_adherence.py <issue> <pr> [--repo <path>]
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

BLOCKED = "BLOCKED_ON_SCOPE"
PASS = "PASS"
ADVISORY = "scope-undeclared"

_SCOPE_LINE_RE = re.compile(r"^\s*scope\s*:\s*(.+)$", re.IGNORECASE)


def parse_declared_scope(body: str) -> frozenset[str] | None:
    """`scope: <prefix list>` 필드를 파싱한다. `maintenance-targets:` 와
    같은 철자 계열(콤마로 나눈 경로 접두어 목록) — 없으면 None."""
    for line in body.splitlines():
        m = _SCOPE_LINE_RE.match(line)
        if not m:
            continue
        prefixes = {p.strip() for p in m.group(1).split(",") if p.strip()}
        if prefixes:
            return frozenset(prefixes)
    return None


def classify(declared_scope: frozenset[str] | None, pr_files: frozenset[str],
             issue: int) -> tuple[str, str | None]:
    """(판정, 사유) 를 돌려준다. 네트워크 없는 순수 판정.

    `declared_scope` 가 None 이면 advisory — 절대 block 하지 않는다
    (consumer-repo friendly, 새 필수 필드 아님). 선언되어 있으면, 이
    issue의 own record tree(`docs/issue-<issue>/`)는 항상 허용하고, 그
    외의 모든 pr_files 는 선언된 접두어 중 하나 아래 있어야 한다. 하나라도
    벗어나면 그 구체적 경로를 사유에 싣는다."""
    if declared_scope is None:
        return PASS, ADVISORY
    own_record_tree = f"docs/issue-{issue}/"
    allowed = tuple(declared_scope) + (own_record_tree,)
    offending = sorted(f for f in pr_files if not f.startswith(allowed))
    if offending:
        return BLOCKED, f"outside declared scope: {', '.join(offending)}"
    return PASS, None


def _issue_body(root: Path, issue: int) -> str | None:
    r = subprocess.run(
        ["gh", "issue", "view", str(issue), "--json", "body"],
        cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout).get("body", "")
    except ValueError:
        return None


def _pr_files(root: Path, pr: int) -> frozenset[str]:
    r = subprocess.run(["gh", "pr", "diff", str(pr), "--name-only"], cwd=root,
                       capture_output=True, text=True)
    if r.returncode != 0:
        return frozenset()
    return frozenset(line.strip() for line in r.stdout.splitlines() if line.strip())


def check(root: Path, issue: int, pr: int) -> tuple[str, str | None]:
    """gh 로 issue body 와 PR files 를 읽어 `classify()` 를 적용한다."""
    body = _issue_body(root, issue)
    declared_scope = parse_declared_scope(body) if body is not None else None
    pr_files = _pr_files(root, pr)
    return classify(declared_scope, pr_files, issue)


def main() -> int:
    argv = sys.argv[1:]
    root = Path(".").resolve()
    if "--repo" in argv:
        idx = argv.index("--repo")
        root = Path(argv[idx + 1]).resolve()
        argv = argv[:idx] + argv[idx + 2:]
    if len(argv) < 2:
        print("usage: scope_adherence.py <issue> <pr> [--repo <path>]")
        return 2
    issue, pr = int(argv[0]), int(argv[1])
    kind, reason = check(root, issue, pr)
    suffix = f" ({reason})" if reason else ""
    print(f"PR #{pr}: {kind}{suffix}")
    return 1 if kind == BLOCKED else 0


if __name__ == "__main__":
    sys.exit(main())
