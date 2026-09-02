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


# ---------------------------------------------------------------------
# issue #3059 -- a check that parses as a real command but whose first
# token isn't on INTERPRETERS must report THAT reason, distinct from a
# check that is genuinely prose (no backtick command at all).
# ---------------------------------------------------------------------

def test_unmapped_interpreter_command_is_still_judgment_but_carries_a_reason():
    # given: an Acceptance bullet whose backtick content is a real,
    # already-mechanical command (grep with a pattern and a real file
    # argument) whose first token just isn't on INTERPRETERS
    section = "## Acceptance\n- x\n  - check: `grep -n foo bar.md`\n"
    # when: parsed
    checks = check_runner.parse_checks(section)
    # then: classification stays `judgment` (must-not: never auto-run an
    # unrecognised token) but the reason names the allowlist gap, not the
    # check's nature
    assert len(checks) == 1
    chk = checks[0]
    assert chk["type"] == "judgment"
    assert chk["reason"] == "unmapped-interpreter"
    assert chk["tool"] == "grep"
    assert chk["command"] == "grep -n foo bar.md"


def test_unmapped_interpreter_never_executes_even_if_fed_to_run_checks():
    # must-not: the diagnostic reason must not become an execution path --
    # run_checks still refuses every `judgment`-typed item, regardless of
    # `reason`.
    chk = {"type": "judgment", "raw": "`grep -n foo bar.md`",
           "reason": "unmapped-interpreter", "command": "grep -n foo bar.md",
           "tool": "grep"}
    try:
        check_runner.run_checks(Path("."), [chk])
        assert False, "run_checks must refuse a judgment-typed check"
    except check_runner.JudgmentCheckError:
        pass


def test_genuinely_prose_check_has_no_backtick_and_no_reason():
    # given: a check with no backtick command at all (issue's own
    # follow-up-comment example of cause 2 -- an author describing an
    # outcome, not naming a command)
    section = ("## Acceptance\n"
               "- check: the documented invocation line, run as written, "
               "produces two workspaces\n")
    checks = check_runner.parse_checks(section)
    assert len(checks) == 1
    assert checks[0]["type"] == "judgment"
    assert "reason" not in checks[0]


def test_stating_verb_prefixed_command_shape_stays_plain_judgment():
    # a stating/demonstrating bullet (issue #2509) is prose even when its
    # backtick token would otherwise look command-shaped -- it must not
    # pick up the unmapped-interpreter reason meant for real commands.
    section = "## Acceptance\n- check: document `grep -n foo bar.md`\n"
    checks = check_runner.parse_checks(section)
    assert checks[0]["type"] == "judgment"
    assert "reason" not in checks[0]


def test_unmapped_interpreter_recognizes_every_curated_tool_name():
    # every entry in the curated diagnostic set (not just `grep`) must
    # actually reach the branch when it is genuinely a command's first
    # token -- guards against a future edit narrowing the membership
    # check without anyone noticing the other five stopped firing.
    for tool, rest in (("jq", ".x file.json"), ("cat", "file.txt"),
                        ("diff", "a.txt b.txt"), ("git", "status"),
                        ("test", "-f file.txt")):
        section = f"## Acceptance\n- check: `{tool} {rest}`\n"
        chk = check_runner.parse_checks(section)[0]
        assert chk["reason"] == "unmapped-interpreter", tool
        assert chk["tool"] == tool


def test_unmapped_interpreter_classification_survives_compound_command():
    # compound `cd X && CMD` commands are this file's most common historical
    # regression source (issues #2313/#2233) -- the classifier keys off the
    # FINAL segment's first token (`grep`), but the suggested `bash -c` wrap
    # must carry the WHOLE original compound string, or `cd` never happens.
    section = "## Acceptance\n- check: `cd frontend && grep -n foo bar.md`\n"
    checks = check_runner.parse_checks(section)
    assert len(checks) == 1
    chk = checks[0]
    assert chk["reason"] == "unmapped-interpreter"
    assert chk["tool"] == "grep"
    assert chk["command"] == "cd frontend && grep -n foo bar.md"


def test_interpreters_allowlist_is_not_widened():
    # must-not (issue #3059, re-affirming #2509): the diagnostic-only tool
    # set must never be folded into INTERPRETERS -- pin the exact tuple so
    # a future edit that merges the two is caught here, not live.
    assert check_runner.INTERPRETERS == (
        "python3", "python", "bash", "sh", "pytest",
        "node", "npx", "deno", "bun")
    assert not (check_runner._COMMON_NON_INTERPRETER_TOOLS
                & set(check_runner.INTERPRETERS))


def test_format_no_checks_comment_unmapped_only_names_interpreter_and_bash_c():
    judgment = [{"type": "judgment", "raw": "`grep -n foo bar.md`",
                 "reason": "unmapped-interpreter",
                 "command": "grep -n foo bar.md", "tool": "grep"}]
    body = check_runner.format_no_checks_comment(judgment)
    # the header must disclaim the judgment-nature framing, not assert it
    assert "판단이 필요한(judgment) 기준이라서가 아니라" in body
    assert "전부 판단이 필요한(judgment) 기준이라 기계적으로 실행할 검사가 없다" not in body
    assert "인터프리터" in body
    assert "bash -c" in body
    assert check_runner.NO_CHECKS_MARKER in body


def test_format_no_checks_comment_genuine_only_is_byte_identical_to_before():
    # empty state (issue #3059 acceptance): a check that is genuinely
    # prose still reports as judgment, unchanged.
    judgment = [{"type": "judgment", "raw": "some prose criterion"}]
    body = check_runner.format_no_checks_comment(judgment)
    expected = (
        f"{check_runner.NO_CHECKS_MARKER}\n\n"
        "이 이슈의 `## Acceptance` 절에 있는 1개 `check:`/"
        "`gate:` 항목이 전부 판단이 필요한(judgment) 기준이라 기계적으로 "
        "실행할 검사가 없다. 이것은 통과가 아니라 별개의 결과다 — 머지 "
        "게이트는 이걸 만족으로 취급하면 안 된다. semantic 채점은 "
        "`gates/requirement_met.py`가 담당한다:\n"
        "- some prose criterion")
    assert body == expected


def test_format_no_checks_comment_mixed_names_both_counts():
    judgment = [
        {"type": "judgment", "raw": "some prose criterion"},
        {"type": "judgment", "raw": "`grep -n foo bar.md`",
         "reason": "unmapped-interpreter",
         "command": "grep -n foo bar.md", "tool": "grep"},
    ]
    body = check_runner.format_no_checks_comment(judgment)
    expected = (
        f"{check_runner.NO_CHECKS_MARKER}\n\n"
        "이 이슈의 `## Acceptance` 절에 있는 2개 `check:`/`gate:` 항목이 "
        "기계적으로 실행되지 않았다 — 1개는 첫 토큰이 인터프리터 허용목록에 "
        "없어서고, 1개는 실제로 판단이 필요한(judgment) 기준이다. 이것은 "
        "통과가 아니라 별개의 결과다 — 머지 게이트는 이걸 만족으로 취급하면 "
        "안 된다. genuine 항목의 semantic 채점은 `gates/requirement_met.py`가 "
        "담당한다:\n"
        "- some prose criterion\n"
        "- `grep -n foo bar.md` — 첫 토큰 `grep`이 인터프리터 허용목록"
        "(python3, python, bash, sh, pytest, node, npx, deno, bun)에 없어 "
        "명령으로 실행되지 않았다(판단이 필요한 기준이라서가 아니다). 허용된 "
        "형태로 감싸 실행하라: `bash -c 'grep -n foo bar.md'`")
    assert body == expected


def test_format_comment_skipped_section_uses_the_distinct_reason_line():
    results = [{"check": "`python3 -m pytest gates/test_x.py`", "type": "test",
                "command": "python3 -m pytest gates/test_x.py",
                "status": "pass", "output": ""}]
    skipped = [{"type": "judgment", "raw": "`grep -n foo bar.md`",
                "reason": "unmapped-interpreter",
                "command": "grep -n foo bar.md", "tool": "grep"}]
    body = check_runner.format_comment(results, skipped)
    assert "bash -c" in body
    assert "1/1 passed" in body
