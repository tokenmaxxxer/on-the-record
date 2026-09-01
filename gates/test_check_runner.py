#!/usr/bin/env python3
"""issue #2974 — the check-runner must distinguish a record-only PR from
an implementation PR using whether the diff touches implementation paths
(primary signal), corroborated by record frontmatter (secondary signal),
and must report disagreement between the two rather than silently
resolving it. Live motivation: PR #2965 (a test-derivation record with no
predicate code) scored 2/4 against issue-2960's implementation Acceptance
checks — the checks target code that already landed via a sibling PR, not
this record-only branch.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))
import check_runner  # noqa: E402


# ---------------------------------------------------------------------
# touches_implementation_paths(): pure, primary signal.
# ---------------------------------------------------------------------

def test_touches_implementation_paths_all_docs_paths_is_record_only():
    assert check_runner.touches_implementation_paths(
        ["docs/issue-2960/reports/test-derivation-8718eaa7.md"]) is False


def test_touches_implementation_paths_any_non_docs_path_counts_as_implementation():
    assert check_runner.touches_implementation_paths(
        ["docs/issue-1/reports/x.md", "gates/check_runner.py"]) is True


def test_touches_implementation_paths_unreadable_diff_fails_closed_to_scored():
    # must-not (issue #2974): never skip scoring a PR that touches
    # implementation paths -- when the diff itself can't be read, default
    # to "touches implementation" (score it), never to "record-only".
    assert check_runner.touches_implementation_paths(None) is True
    assert check_runner.touches_implementation_paths([]) is True


# ---------------------------------------------------------------------
# frontmatter_record_only_signal(): corroborating signal from `kind:`.
# ---------------------------------------------------------------------

def _write_record(tmp_path, rel, frontmatter_body):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\n{frontmatter_body}\n---\n\nbody\n")
    return rel


def test_frontmatter_signal_verify_record_kind_says_record_only(tmp_path):
    rel = _write_record(tmp_path, "docs/issue-1/reports/x.md", "kind: verify-record")
    assert check_runner.frontmatter_record_only_signal(tmp_path, [rel]) is True


def test_frontmatter_signal_implementation_kind_says_not_record_only(tmp_path):
    rel = _write_record(tmp_path, "docs/issue-1/reports/x.md", "kind: implementation")
    assert check_runner.frontmatter_record_only_signal(tmp_path, [rel]) is False


def test_frontmatter_signal_absent_kind_line_abstains(tmp_path):
    rel = _write_record(tmp_path, "docs/issue-1/reports/x.md", "role: x\nauthor: x")
    assert check_runner.frontmatter_record_only_signal(tmp_path, [rel]) is None


def test_frontmatter_signal_no_record_paths_abstains(tmp_path):
    assert check_runner.frontmatter_record_only_signal(tmp_path, []) is None


# ---------------------------------------------------------------------
# main(): full record-only vs. implementation scoring decision.
# ---------------------------------------------------------------------

def _acceptance_issue_body():
    return "## Acceptance\n\n- check: `python3 -m pytest gates/test_x.py -q`\n"


def _wire_main(monkeypatch, tmp_path, *, diff_paths, run_checks_result=None):
    monkeypatch.setattr(check_runner.gh_rest, "fetch_issue_body",
                         lambda repo, issue: _acceptance_issue_body())
    monkeypatch.setattr(check_runner, "pr_diff_paths", lambda repo, pr: diff_paths)
    monkeypatch.setattr(check_runner, "checkout_pr_worktree",
                         lambda repo, pr: (tmp_path, None))
    monkeypatch.setattr(check_runner, "remove_worktree", lambda repo, wt: None)

    posted = {}
    monkeypatch.setattr(check_runner, "post_comment",
                         lambda pr, body, repo: posted.setdefault("body", body) or True)

    ran = []

    def _run_checks(repo, checks):
        ran.append(checks)
        return run_checks_result if run_checks_result is not None else []

    monkeypatch.setattr(check_runner, "run_checks", _run_checks)
    monkeypatch.setattr(sys, "argv",
                         ["check_runner.py", "1", "1", "--repo", str(tmp_path)])
    return posted, ran


def test_record_only_pr_not_scored(monkeypatch, tmp_path):
    # empty state (issue #2974 acceptance): a PR touching implementation
    # paths is scored exactly as today -- covered by the reverse-direction
    # test below, which shows `run_checks` IS called when the diff touches
    # a non-docs/ path.
    posted, ran = _wire_main(
        monkeypatch, tmp_path,
        diff_paths=["docs/issue-1/reports/x.md"])

    rc = check_runner.main()

    assert rc == 0
    assert not ran, "mechanical checks must not be run against a record-only branch"
    assert check_runner.RECORD_ONLY_MARKER in posted["body"]


def test_record_only_pr_not_scored_implementation_pr_still_scored(monkeypatch, tmp_path):
    posted, ran = _wire_main(
        monkeypatch, tmp_path,
        diff_paths=["gates/some_module.py"],
        run_checks_result=[{"check": "`python3 -m pytest gates/test_x.py -q`",
                             "type": "test", "command": "python3 -m pytest gates/test_x.py -q",
                             "status": "pass", "output": ""}])

    rc = check_runner.main()

    assert ran, "an implementation-touching PR must still be scored"
    assert check_runner.RECORD_ONLY_MARKER not in posted["body"]
    assert rc == 0


def test_record_signal_disagreement_record_only_diff_wins_over_implementation_kind(
        monkeypatch, tmp_path):
    rel = _write_record(tmp_path, "docs/issue-1/reports/x.md", "kind: implementation")
    posted, ran = _wire_main(monkeypatch, tmp_path, diff_paths=[rel])

    rc = check_runner.main()

    # diff says record-only (no non-docs/ path); frontmatter kind says
    # implementation -- the two disagree. The diff signal wins (still not
    # scored), but the disagreement is reported, not silently dropped.
    assert rc == 0
    assert not ran
    body = posted["body"]
    assert check_runner.RECORD_ONLY_MARKER in body
    assert "불일치" in body


def test_record_signal_disagreement_implementation_diff_still_scored_but_reported(
        monkeypatch, tmp_path):
    rel = _write_record(tmp_path, "docs/issue-1/reports/x.md", "kind: verify-record")
    posted, ran = _wire_main(
        monkeypatch, tmp_path, diff_paths=[rel, "gates/some_module.py"],
        run_checks_result=[{"check": "`python3 -m pytest gates/test_x.py -q`",
                             "type": "test", "command": "python3 -m pytest gates/test_x.py -q",
                             "status": "pass", "output": ""}])

    rc = check_runner.main()

    # diff touches an implementation path -> still scored (must-not: never
    # skip scoring a PR that touches implementation paths), but the
    # frontmatter's record-only kind disagrees with that -- reported.
    assert ran
    body = posted["body"]
    assert check_runner.RECORD_ONLY_MARKER not in body
    assert "불일치" in body
    assert rc == 0
