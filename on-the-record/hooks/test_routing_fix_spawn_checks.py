"""Tests for the 4 cause-b routing-fix spawn-check hooks (issue #1130):
test-authoring-spawn-check.sh, issue-retrospective-spawn-check.sh,
interaction-design-spawn-check.sh, ux-engineering-spawn-check.sh.

Each seeds a minimal target checkout (its own roles/specs/<role>.spec.json
plus git history) and exercises one refusal case + one pass case.
"""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
ROOT = HOOKS_DIR.parent.parent


def _run(guard, tool_input, cwd):
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": tool_input,
        "cwd": str(cwd),
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    return subprocess.run(
        ["bash", str(HOOKS_DIR / guard)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
    )


def _seed_repo(tmp_path, role, spec):
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    specs_dir = tmp_path / "roles" / "specs"
    specs_dir.mkdir(parents=True)
    (specs_dir / f"{role}.spec.json").write_text(json.dumps(spec))
    (tmp_path / "README.md").write_text("seed\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "seed"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "remote", "add", "origin", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "update-ref", "refs/remotes/origin/main", "main"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "checkout", "-q", "-b", f"issue-42/{role}"], check=True)


TEST_AUTHORING_SPEC = {
    "role": "test-authoring",
    "use_when": {
        "trigger": {
            "path_patterns": ["src/**"],
            "content_patterns": [],
            "record_absent_for": "test-authoring",
        }
    },
}


def t_test_authoring_denies_merge_when_trigger_matched_and_record_absent(tmp_path):
    _seed_repo(tmp_path, "test-authoring", TEST_AUTHORING_SPEC)
    src = tmp_path / "src"
    src.mkdir()
    (src / "new.py").write_text("def f(): pass\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "add behavior"], check=True)

    r = _run("test-authoring-spawn-check.sh", {"command": "gh pr merge 1", "cwd": str(tmp_path)}, tmp_path)
    assert r.returncode == 2
    assert "test-authoring" in r.stderr


def t_test_authoring_passes_when_record_present(tmp_path):
    _seed_repo(tmp_path, "test-authoring", TEST_AUTHORING_SPEC)
    src = tmp_path / "src"
    src.mkdir()
    (src / "new.py").write_text("def f(): pass\n")
    reports = tmp_path / "docs" / "issue-42" / "reports"
    reports.mkdir(parents=True)
    (reports / "test-authoring.md").write_text("record\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "add behavior + record"], check=True)

    r = _run("test-authoring-spawn-check.sh", {"command": "gh pr merge 1", "cwd": str(tmp_path)}, tmp_path)
    assert r.returncode == 0


ISSUE_RETROSPECTIVE_SPEC = {
    "role": "issue-retrospective",
    "use_when": {
        "trigger": {"path_patterns": [], "content_patterns": [], "record_absent_for": "issue-retrospective"}
    },
}


def t_issue_retrospective_denies_close_when_record_absent(tmp_path):
    _seed_repo(tmp_path, "issue-retrospective", ISSUE_RETROSPECTIVE_SPEC)
    r = _run("issue-retrospective-spawn-check.sh", {"command": "gh issue close 42", "cwd": str(tmp_path)}, tmp_path)
    assert r.returncode == 2
    assert "issue-retrospective" in r.stderr


def t_issue_retrospective_passes_when_record_present(tmp_path):
    _seed_repo(tmp_path, "issue-retrospective", ISSUE_RETROSPECTIVE_SPEC)
    reports = tmp_path / "docs" / "issue-42" / "reports"
    reports.mkdir(parents=True)
    (reports / "issue-retrospective.md").write_text("record\n")
    r = _run("issue-retrospective-spawn-check.sh", {"command": "gh issue close 42", "cwd": str(tmp_path)}, tmp_path)
    assert r.returncode == 0


INTERACTION_DESIGN_SPEC = {
    "role": "interaction-design",
    "use_when": {
        "trigger": {
            "path_patterns": ["docs/issue-*/reports/product-discovery.md"],
            "content_patterns": [],
            "record_absent_for": "interaction-design",
        }
    },
}


def t_interaction_design_denies_merge_when_trigger_matched_and_record_absent(tmp_path):
    _seed_repo(tmp_path, "interaction-design", INTERACTION_DESIGN_SPEC)
    reports = tmp_path / "docs" / "issue-42" / "reports"
    reports.mkdir(parents=True)
    (reports / "product-discovery.md").write_text("finding\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "product-discovery record"], check=True)

    r = _run("interaction-design-spawn-check.sh", {"command": "gh pr merge 1", "cwd": str(tmp_path)}, tmp_path)
    assert r.returncode == 2
    assert "interaction-design" in r.stderr


UX_ENGINEERING_SPEC = {
    "role": "ux-engineering",
    "use_when": {
        "trigger": {
            "path_patterns": ["**/*.tsx", "**/*.jsx", "**/*.vue", "**/*.svelte"],
            "content_patterns": ["design-token"],
            "record_absent_for": "ux-engineering",
        }
    },
}


def t_ux_engineering_denies_merge_when_trigger_matched_and_record_absent(tmp_path):
    _seed_repo(tmp_path, "ux-engineering", UX_ENGINEERING_SPEC)
    components = tmp_path / "components"
    components.mkdir()
    (components / "Button.tsx").write_text("export const Button = () => <button className=\"tok\" />;\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "add component"], check=True)

    r = _run("ux-engineering-spawn-check.sh", {"command": "gh pr merge 1", "cwd": str(tmp_path)}, tmp_path)
    assert r.returncode == 2
    assert "ux-engineering" in r.stderr


def t_test_authoring_denies_merge_with_harmless_substitution_present(tmp_path):
    # issue #1130 before-landing warrant hunt: an earlier version of this
    # hook bailed out (exit 0) on ANY command containing "$(" or a
    # backtick, letting `gh pr merge $(echo 1)` through unchecked even
    # though it is the same violation as the plain `gh pr merge 1` case.
    _seed_repo(tmp_path, "test-authoring", TEST_AUTHORING_SPEC)
    src = tmp_path / "src"
    src.mkdir()
    (src / "new.py").write_text("def f(): pass\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "add behavior"], check=True)

    r = _run("test-authoring-spawn-check.sh", {"command": "gh pr merge $(echo 1)", "cwd": str(tmp_path)}, tmp_path)
    assert r.returncode == 2
    assert "test-authoring" in r.stderr


def t_orchestrate_off_disables_all_four(tmp_path):
    _seed_repo(tmp_path, "test-authoring", TEST_AUTHORING_SPEC)
    src = tmp_path / "src"
    src.mkdir()
    (src / "new.py").write_text("def f(): pass\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "add behavior"], check=True)

    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "gh pr merge 1", "cwd": str(tmp_path)}})
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = "1"
    r = subprocess.run(
        ["bash", str(HOOKS_DIR / "test-authoring-spawn-check.sh")],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
    )
    assert r.returncode == 0
