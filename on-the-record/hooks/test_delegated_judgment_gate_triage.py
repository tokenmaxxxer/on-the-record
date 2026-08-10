#!/usr/bin/env python3
"""issue #609 (implementation phase 2) — open-decision triage added to
delegated-judgment-gate.sh's `gh pr create` heredoc. No test harness exists
for this hook (confirmed by survey: zero-install constraint forbids an
importable module, so the heredoc stays a single inline script). This
harness extracts the heredoc's Python source the same way the shell wrapper
reaches it (`<<'PY' ... PY`) and execs it, via `python3 -c`, against
constructed fixture git repos — a temp dir with a real git history so
`git diff --name-only origin/main...HEAD` resolves, `roles/*.json`, and
role record files carrying `open_decision_item`/`axis_evaluation` blocks.

  python3 -m pytest on-the-record/hooks/test_delegated_judgment_gate_triage.py -q
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parent / "delegated-judgment-gate.sh"
ISSUE = 609
BRANCH = f"issue-{ISSUE}/requirements-engineering"


def _extract_gate_source() -> str:
    text = HOOK_PATH.read_text(encoding="utf-8")
    marker = "<<'PY' || true\n"
    start = text.index(marker) + len(marker)
    end = text.index("\nPY\n", start)
    return text[start:end]


GATE_SRC = _extract_gate_source()


def _run(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True)


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init", "-q", "-b", "main"], repo)
    _run(["git", "config", "user.email", "test@example.com"], repo)
    _run(["git", "config", "user.name", "test"], repo)
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    _run(["git", "add", "README.md"], repo)
    _run(["git", "commit", "-q", "-m", "init"], repo)
    base_sha = _run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    _run(["git", "update-ref", "refs/remotes/origin/main", base_sha], repo)
    _run(["git", "checkout", "-q", "-b", BRANCH], repo)
    return repo


def _write_role(repo: Path, name: str, judgment_axes, record_rel):
    """`record_rel` is the concrete (issue-number-substituted) record path;
    write_scope needs the raw `<n>` placeholder for role_record_path's own
    `"<n>" in g` check to find it, mirroring real roles/*.json."""
    roles_dir = repo / "roles"
    roles_dir.mkdir(exist_ok=True)
    placeholder_glob = record_rel.replace(f"issue-{ISSUE}", "issue-<n>")
    (roles_dir / f"{name}.json").write_text(json.dumps({
        "judgment_axes": judgment_axes,
        "write_scope": [placeholder_glob],
    }), encoding="utf-8")


def _write_record(repo: Path, rel: str, body: str):
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _commit_all(repo: Path):
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-q", "-m", "wip"], repo)


def _run_gate(repo: Path):
    env = dict(os.environ)
    env["DJG_TARGET"] = str(repo)
    env["DJG_PAYLOAD"] = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": "gh pr create --number 1"},
    })
    env["ORCHESTRATE_OFF"] = ""
    return subprocess.run(["python3", "-c", GATE_SRC], cwd=repo, env=env,
                           capture_output=True, text=True, timeout=30)


def _latest_triage_record(repo: Path):
    decisions_dir = repo / "docs" / f"issue-{ISSUE}" / "decisions"
    files = sorted(decisions_dir.glob("triage-*.md"))
    assert files, f"no triage-*.md written in {decisions_dir}"
    return files[-1].read_text(encoding="utf-8")


REQ_ENG_REL = f"docs/issue-{ISSUE}/reports/requirements-engineering.md"


def _item_block(item, source_role, source_path, candidate_axes):
    return (
        "<!-- open_decision_item\n"
        f"item: {item}\n"
        f"source_role: {source_role}\n"
        f"source_path: {source_path}\n"
        f"candidate_axes: {', '.join(candidate_axes)}\n"
        "-->\n"
    )


def _axis_eval_block(axis, verdict, citation):
    return (
        "<!-- axis_evaluation\n"
        f"axis: {axis}\n"
        f"verdict: {verdict}\n"
        f"citation: {citation}\n"
        "-->\n"
    )


def test_empty_corpus_degrades_to_escalated(tmp_path):
    repo = _init_repo(tmp_path)
    _write_role(repo, "role-alpha", ["alignment"],
                f"docs/issue-{ISSUE}/reports/role-alpha.md")
    _write_record(repo, REQ_ENG_REL,
                  _item_block("ambiguous EARS phrasing", "requirements-engineering",
                              REQ_ENG_REL, ["alignment"]))
    _commit_all(repo)
    assert not (repo / "docs" / "product").is_dir()

    result = _run_gate(repo)
    assert result.returncode == 0, result.stderr

    text = _latest_triage_record(repo)
    assert "decision: escalated" in text
    assert f"derivation_source: {REQ_ENG_REL}" in text


def test_panel_conflict_escalates_despite_cleared_threshold(tmp_path):
    repo = _init_repo(tmp_path)
    alpha_rel = f"docs/issue-{ISSUE}/reports/role-alpha.md"
    beta_rel = f"docs/issue-{ISSUE}/reports/role-beta.md"
    _write_role(repo, "role-alpha", ["alignment"], alpha_rel)
    _write_role(repo, "role-beta", ["maintenance_complexity"], beta_rel)
    _write_record(repo, REQ_ENG_REL,
                  _item_block("ambiguous EARS phrasing", "requirements-engineering",
                              REQ_ENG_REL, ["alignment", "maintenance_complexity"]))
    _write_record(repo, alpha_rel, _axis_eval_block("alignment", "supports", REQ_ENG_REL))
    _write_record(repo, beta_rel, _axis_eval_block("maintenance_complexity", "contradicts", REQ_ENG_REL))
    # clear the depth axis: docs/product corpus mentions a changed basename.
    _write_record(repo, "docs/product/priorities.md",
                  f"see {Path(REQ_ENG_REL).name}\n")
    _commit_all(repo)

    result = _run_gate(repo)
    assert result.returncode == 0, result.stderr

    text = _latest_triage_record(repo)
    assert "decision: escalated" in text


def test_single_owner_supports_resolves(tmp_path):
    repo = _init_repo(tmp_path)
    alpha_rel = f"docs/issue-{ISSUE}/reports/role-alpha.md"
    _write_role(repo, "role-alpha", ["alignment"], alpha_rel)
    _write_record(repo, REQ_ENG_REL,
                  _item_block("ambiguous EARS phrasing", "requirements-engineering",
                              REQ_ENG_REL, ["alignment"]))
    _write_record(repo, alpha_rel, _axis_eval_block("alignment", "supports", REQ_ENG_REL))
    _write_record(repo, "docs/product/priorities.md",
                  f"see {Path(REQ_ENG_REL).name}\n")
    _commit_all(repo)

    result = _run_gate(repo)
    assert result.returncode == 0, result.stderr

    text = _latest_triage_record(repo)
    assert "decision: resolved" in text
    assert "role-alpha" in text


if __name__ == "__main__":
    import inspect
    import tempfile
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and inspect.isfunction(v)]
    for t in tests:
        with tempfile.TemporaryDirectory() as d:
            t(Path(d))
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
