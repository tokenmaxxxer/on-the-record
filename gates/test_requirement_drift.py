"""issue #1080: requirement_drift() 의 infra-tag 예외가
gates/requirement_linkage.py::check_issue_body 의 _INFRA_TAG 예외와
같은 items 을 unreferenced_open 에서 제외하는지 검사한다."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import spawn  # noqa: E402
from requirement_linkage import _INFRA_TAG  # noqa: E402


def _make_root(tmp_path):
    digest = tmp_path / "docs" / "specs" / "requirement-digest.md"
    digest.parent.mkdir(parents=True)
    digest.write_text(
        "- R006: 요구 응축관리 [live] (source: #1)\n", encoding="utf-8")
    return tmp_path


def _fake_gh_list(issues, prs):
    def run(cmd, cwd=None, capture_output=None, text=None):
        class _R:
            pass
        r = _R()
        r.returncode = 0
        if cmd[1] == "issue":
            r.stdout = json.dumps(issues)
        else:
            r.stdout = json.dumps(prs)
        return r
    return run


def test_infra_tagged_item_excluded_from_unreferenced_open(tmp_path, monkeypatch, capsys):
    root = _make_root(tmp_path)
    tagged_issue = {
        "number": 745, "title": "some infra work",
        "body": f"no requirement cited here. {_INFRA_TAG}",
    }
    untagged_issue = {
        "number": 900, "title": "some other work",
        "body": "no requirement cited and no infra tag either",
    }
    monkeypatch.setattr(
        spawn.subprocess, "run",
        _fake_gh_list([tagged_issue, untagged_issue], []))

    spawn.requirement_drift(root)
    out = capsys.readouterr().out

    assert "900" in out
    assert "745" not in out


def test_untagged_item_still_flagged(tmp_path, monkeypatch, capsys):
    root = _make_root(tmp_path)
    untagged_issue = {
        "number": 42, "title": "x", "body": "no requirement, no tag",
    }
    monkeypatch.setattr(
        spawn.subprocess, "run", _fake_gh_list([untagged_issue], []))

    spawn.requirement_drift(root)
    out = capsys.readouterr().out

    assert "42" in out


def test_empty_tagged_items_leaves_drift_output_unchanged(tmp_path, monkeypatch, capsys):
    root = _make_root(tmp_path)
    referenced_issue = {
        "number": 5, "title": "R006 covers this", "body": "cites R006",
    }
    monkeypatch.setattr(
        spawn.subprocess, "run", _fake_gh_list([referenced_issue], []))

    spawn.requirement_drift(root)
    out = capsys.readouterr().out

    assert "전혀 인용하지 않는" not in out
    assert "다이제스트" not in out
