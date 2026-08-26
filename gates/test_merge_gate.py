#!/usr/bin/env python3
"""머지 게이트(`gates/merge_gate.py`) 단위테스트 — issue-1323 req 4 원본
(원래 `tests/test_merge_gate.py`)과 issue-2233 회귀 테스트를 한 파일로
합쳤다. `check_runner.py`가 이미 겪은 것과 같은 이유(모듈 옆 `gates/test_x.py`
와 `tests/test_x.py`가 베이스네임을 공유하면 패키지 경계 없이 pytest 수집이
충돌한다 — `gates/test_duplicate_test_basenames.py`가 잡는다): 검사 대상
모듈 옆 이 파일 하나로 합치고, `tests/test_merge_gate.py`는 없앤다.

issue-2233 이 추가한 부분 — 머지 게이트가 실제로 아무것도 못 머지시키던 세
블로커의 회귀 테스트. 네트워크·`gh` 없이, 합성 git 저장소/모킹으로 돈다:

1. check-runner 는 오케스트레이터 체크아웃이 아니라 **PR head 커밋**을
   상대로 검사를 실행해야 한다(`check_runner.worktree_for_ref`) — 이
   테스트가 없으면 `gates/check_runner.py`가 PR 브랜치에만 있는 파일을
   찾다가 다시 `FileNotFoundError`로 죽는 경로가 조용히 되돌아온다.
2. 빈 `## Acceptance` 절(실행가능한 검사 0개)은 `0/0 passed`(우연한 통과)가
   아니라 별개의 "no checks declared" 결과여야 하고, 머지 게이트는 그걸
   만족으로 읽으면 안 된다.
3. 관찰자 record PR(예: `issue-2204/execution-observation`)이 스스로
   공급하는 role 은 "필요한 검증 기록이 없다" 목록에서 빠져야 한다 — 그
   PR 이 자기 자신을 공급 못 한다는 이유로 막히는 순환을 깬다. subject 의
   *다른* 미공급 role 은 여전히 막혀야 한다(구조적 예외가 아니라 자기
   role 하나만의 예외라는 것의 증거).

  python3 -m pytest gates/test_merge_gate.py
  python3 gates/test_merge_gate.py   # monkeypatch 없는 테스트만
"""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import check_runner  # noqa: E402
import merge_gate  # noqa: E402


# ---- issue-1323 req 4 (원래 tests/test_merge_gate.py) --------------------


def test_parse_check_runner_result_all_pass():
    results = [{"check": "`a`", "type": "test", "status": "pass", "output": ""}]
    body = check_runner.format_comment(results)
    assert merge_gate.parse_check_runner_result(body) == {"passed": 1, "total": 1, "no_checks": False}


def test_parse_check_runner_result_partial_fail():
    results = [
        {"check": "`a`", "type": "test", "status": "pass", "output": ""},
        {"check": "`b`", "type": "test", "status": "fail", "output": ""},
    ]
    body = check_runner.format_comment(results)
    assert merge_gate.parse_check_runner_result(body) == {"passed": 1, "total": 2, "no_checks": False}


def test_parse_check_runner_result_non_matching_text():
    assert merge_gate.parse_check_runner_result("hello, this is not a check-runner comment") is None


@pytest.fixture()
def fixture_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    docs = repo / "docs" / "issue-9002" / "reports"
    docs.mkdir(parents=True)
    (docs / "implementation.md").write_text("---\nloop_state: landed\n---\nbody\n")
    (docs / "execution-observation.md").write_text("---\nloop_state: landed\n---\nbody\n")
    (docs / "conformance-review.md").write_text("---\nloop_state: landed\n---\nbody\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    return repo


def test_latest_check_runner_comment_builds_expected_argv(monkeypatch, fixture_repo):
    captured = {}

    def fake_run(argv, cwd, capture_output, text):
        captured["argv"] = argv
        captured["cwd"] = cwd
        class R:
            returncode = 0
            stdout = '{"comments": []}'
        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = merge_gate.latest_check_runner_comment(fixture_repo, 42)
    assert result is None
    assert captured["argv"] == ["gh", "pr", "view", "42", "--json", "comments"]
    assert captured["cwd"] == fixture_repo


def test_required_verification_missing_none(fixture_repo):
    assert merge_gate.required_verification_missing(fixture_repo, "issue-9002") == []


def test_required_verification_missing_some(tmp_path):
    repo = tmp_path / "repo2"
    docs = repo / "docs" / "issue-9003" / "reports"
    docs.mkdir(parents=True)
    (docs / "execution-observation.md").write_text("---\nloop_state: landed\n---\nbody\n")
    assert merge_gate.required_verification_missing(repo, "issue-9003") == ["conformance-review"]


def test_evaluate_comment_missing(monkeypatch, fixture_repo):
    monkeypatch.setattr(merge_gate, "latest_check_runner_comment", lambda repo, pr: None)
    result = merge_gate.evaluate(fixture_repo, fixture_repo, 42, "issue-9002")
    assert result["allowed"] is False
    assert any("코멘트" in r for r in result["reasons"])


def test_evaluate_check_runner_failing(monkeypatch, fixture_repo):
    body = check_runner.format_comment([
        {"check": "`a`", "type": "test", "status": "fail", "output": ""}])
    monkeypatch.setattr(merge_gate, "latest_check_runner_comment", lambda repo, pr: body)
    result = merge_gate.evaluate(fixture_repo, fixture_repo, 42, "issue-9002")
    assert result["allowed"] is False


def test_evaluate_verification_missing(monkeypatch, tmp_path):
    repo = tmp_path / "repo3"
    docs = repo / "docs" / "issue-9004" / "reports"
    docs.mkdir(parents=True)
    body = check_runner.format_comment([
        {"check": "`a`", "type": "test", "status": "pass", "output": ""}])
    monkeypatch.setattr(merge_gate, "latest_check_runner_comment", lambda r, pr: body)
    result = merge_gate.evaluate(repo, repo, 42, "issue-9004")
    assert result["allowed"] is False
    assert any("검증 기록" in r for r in result["reasons"])


def test_evaluate_all_clear(monkeypatch, fixture_repo):
    body = check_runner.format_comment([
        {"check": "`a`", "type": "test", "status": "pass", "output": ""}])
    monkeypatch.setattr(merge_gate, "latest_check_runner_comment", lambda repo, pr: body)
    monkeypatch.setattr(merge_gate, "stale_revert_reasons", lambda repo, pr: [])
    result = merge_gate.evaluate(fixture_repo, fixture_repo, 42, "issue-9002")
    assert result == {"allowed": True, "reasons": []}


# ---- issue-1664 (northpole req#6): stale-revert wiring in evaluate() ----

def test_evaluate_refuses_on_stale_revert(monkeypatch, fixture_repo):
    body = check_runner.format_comment([
        {"check": "`a`", "type": "test", "status": "pass", "output": ""}])
    monkeypatch.setattr(merge_gate, "latest_check_runner_comment", lambda repo, pr: body)
    monkeypatch.setattr(merge_gate, "stale_revert_reasons",
                         lambda repo, pr: ["app.py: stale revert"])
    result = merge_gate.evaluate(fixture_repo, fixture_repo, 42, "issue-9002")
    assert result["allowed"] is False
    assert any("app.py" in r for r in result["reasons"])


def test_pr_refs_none_on_gh_failure(monkeypatch, fixture_repo):
    def fake_run(argv, cwd, capture_output, text):
        class R:
            returncode = 1
            stdout = ""
        return R()
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert merge_gate.pr_refs(fixture_repo, 42) is None


def test_stale_revert_reasons_fail_open_when_refs_missing(monkeypatch, fixture_repo):
    monkeypatch.setattr(merge_gate, "pr_refs", lambda repo, pr: None)
    assert merge_gate.stale_revert_reasons(fixture_repo, 42) == []


def _commit(repo, path, content, msg):
    (repo / path).write_text(content)
    _git(repo, "add", path)
    _git(repo, "commit", "-q", "-m", msg)


def test_live_pr_1662_vs_1661_reconstruction(monkeypatch, tmp_path):
    """PR #1662 대 #1661 상황 재구성(2026-08-16 인시던트): #1662 브랜치가
    #1661 의 보안 픽스보다 먼저 갈라져서, 그 픽스를 지우는 채로 머지되면
    안 된다 -- `evaluate()` 가 REFUSE 해야 한다."""
    repo = tmp_path / "live_repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    _commit(repo, "app.py", "def handler():\n    return old_value()\n", "init")

    _git(repo, "branch", "issue-1662/implementation")  # PR #1662's merge-base

    # PR #1661 lands the security fix on main after that merge-base
    _commit(repo, "app.py",
            "def handler():\n    validate(request)\n    return old_value()\n",
            "security fix (PR #1661)")

    # PR #1662, cut before the fix, overlaps that same region without it
    _git(repo, "checkout", "-q", "issue-1662/implementation")
    _commit(repo, "app.py", "def handler():\n    return new_value()\n",
            "feature change (PR #1662, stale)")
    _git(repo, "checkout", "-q", "main")

    monkeypatch.setattr(merge_gate, "pr_refs", lambda r, pr: {
        "base_ref": "main", "head_ref": "issue-1662/implementation"})
    monkeypatch.setattr(merge_gate, "latest_check_runner_comment",
                         lambda r, pr: check_runner.format_comment(
                             [{"check": "`a`", "type": "test", "status": "pass", "output": ""}]))
    # issue #2233: `required_verification_missing`가 이제 선택 인자
    # repo/pr 을 받는다 — `evaluate()`가 항상 넘기므로 monkeypatch 시그니처도
    # 받아줘야 한다(그 값 자체는 이 테스트의 관심사가 아니다).
    monkeypatch.setattr(merge_gate, "required_verification_missing",
                         lambda root, subject, repo=None, pr=None: [])

    result = merge_gate.evaluate(repo, repo, 1662, "issue-1662")
    assert result["allowed"] is False
    assert any("app.py" in r for r in result["reasons"])

    # rebasing PR #1662 onto base HEAD (fix preserved) makes it pass
    _git(repo, "checkout", "-q", "-b", "issue-1662-rebased", "main")
    _commit(repo, "app.py",
            "def handler():\n    validate(request)\n    return new_value()\n",
            "feature change (PR #1662, rebased)")
    monkeypatch.setattr(merge_gate, "pr_refs", lambda r, pr: {
        "base_ref": "main", "head_ref": "issue-1662-rebased"})
    result2 = merge_gate.evaluate(repo, repo, 1662, "issue-1662")
    assert result2 == {"allowed": True, "reasons": []}


# ---- issue-2233 ------------------------------------------------------------


def _git(cwd, *args):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
        env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
             "PATH": "/usr/bin:/bin"},
    )


def _build_repo_with_pr_branch(tmp: Path) -> Path:
    """`main`에는 없고 `pr-branch`에만 있는 파일 하나를 만든다 — 블로커 2의
    바로 그 모양(이슈가 재현한 `tests/test_workspace_checkpoint.py`처럼,
    PR 이 새로 추가한 파일이 오케스트레이터 체크아웃엔 없다)."""
    repo = tmp / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / "base.txt").write_text("base\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")

    _git(repo, "checkout", "-q", "-b", "pr-branch")
    (repo / "pr_only.txt").write_text("only on the PR branch\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "pr adds a file")
    _git(repo, "checkout", "-q", "main")
    return repo


def t_worktree_for_ref_sees_pr_branch_file_repo_cwd_does_not():
    with tempfile.TemporaryDirectory() as d:
        repo = _build_repo_with_pr_branch(Path(d))
        # `repo`(오케스트레이터 체크아웃)는 main 에 있다 — pr_only.txt 가 없다.
        assert not (repo / "pr_only.txt").exists()

        worktree, err = check_runner.worktree_for_ref(repo, "pr-branch")
        try:
            assert err is None, err
            assert (worktree / "pr_only.txt").exists(), (
                "worktree 가 PR 브랜치 커밋이 아니라 오케스트레이터 체크아웃을 "
                "반영했다 — 블로커 2가 그대로 살아있다.")
            assert not (repo / "pr_only.txt").exists(), (
                "worktree 체크아웃이 오케스트레이터 체크아웃 자체를 바꿔버렸다 "
                "— 진행 중인 세션의 작업 트리를 건드리면 안 된다.")
        finally:
            check_runner.remove_worktree(repo, worktree)


def t_worktree_for_ref_fails_closed_on_unknown_ref():
    with tempfile.TemporaryDirectory() as d:
        repo = _build_repo_with_pr_branch(Path(d))
        worktree, err = check_runner.worktree_for_ref(repo, "no-such-ref")
        assert worktree is None
        assert err is not None and "no-such-ref" in err


def t_empty_acceptance_section_produces_distinct_no_checks_result_not_zero_of_zero():
    results = check_runner.run_checks(Path("."), check_runner.parse_checks(""))
    assert results == []
    comment = check_runner.format_comment(results)
    assert comment == check_runner.format_no_checks_comment()
    assert check_runner.NO_CHECKS_MARKER in comment
    # 예전 버그 모양(우연히 통과로 읽히는 "0/0 passed")이 더는 안 나온다.
    assert "0/0 passed" not in comment


def t_merge_gate_parses_no_checks_marker_distinctly_from_numeric_header():
    no_checks = merge_gate.parse_check_runner_result(check_runner.format_no_checks_comment())
    assert no_checks == {"no_checks": True}

    passing = merge_gate.parse_check_runner_result(
        "## Acceptance check-runner result: 2/2 passed\n\n- [PASS] ...")
    assert passing == {"passed": 2, "total": 2, "no_checks": False}


def t_merge_gate_evaluate_refuses_no_checks_as_a_pass(monkeypatch):
    """`evaluate()`를 끝까지 — check-runner 코멘트를 no-checks 로 고정하고,
    나머지 세 검사(필요 기록/stale-revert)는 통과로 고정한 뒤, 그래도
    `allowed`가 아니어야 한다는 것을 확인한다."""
    # issue #2381 R1: `evaluate()` now fetches (`check_runner.fetch_all_role_branches`)
    # before `stale_revert_reasons()` — stub it out so this test stays
    # network-free against the real checkout `repo=Path(".")` passes in.
    monkeypatch.setattr(check_runner, "fetch_all_role_branches", lambda repo: None)
    monkeypatch.setattr(merge_gate, "latest_check_runner_comment",
                         lambda repo, pr: check_runner.format_no_checks_comment())
    monkeypatch.setattr(merge_gate, "required_verification_missing",
                         lambda root, subject, repo=None, pr=None: [])
    monkeypatch.setattr(merge_gate, "stale_revert_reasons", lambda repo, pr: [])

    result = merge_gate.evaluate(Path("."), Path("."), 999, "issue-999")
    assert result["allowed"] is False
    assert any("no checks" in r or "없다" in r for r in result["reasons"]), result["reasons"]


def t_finder_reaches_no_checks_branch_through_evaluate(monkeypatch, fixture_repo):
    """issue-2268 — `_RESULT_HEADER` (the finder `latest_check_runner_comment`
    searches with) 는 예전에 숫자 헤더만 맞춰서 no-checks 코멘트를 영영
    못 찾았다(#2231 이 추가한 브랜치가 죽은 코드였다). 이 테스트는 그 파서를
    직접 부르는 게 아니라 `gh pr view` 를 흉내낸 `subprocess.run` 위로
    `latest_check_runner_comment` -> `parse_check_runner_result` ->
    `evaluate()` 를 실제로 다 통과시킨다."""
    import json
    no_checks_body = check_runner.format_no_checks_comment()

    def fake_run(argv, cwd, capture_output, text):
        class R:
            returncode = 0
            stdout = json.dumps({"comments": [
                {"body": "unrelated comment"},
                {"body": no_checks_body},
            ]})
        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(merge_gate, "required_verification_missing",
                         lambda root, subject, repo=None, pr=None: [])
    monkeypatch.setattr(merge_gate, "stale_revert_reasons", lambda repo, pr: [])

    found = merge_gate.latest_check_runner_comment(fixture_repo, 2228)
    assert found == no_checks_body

    result = merge_gate.evaluate(fixture_repo, fixture_repo, 2228, "issue-9002")
    assert result["allowed"] is False
    assert not any("코멘트를 찾을 수 없다" in r for r in result["reasons"]), result["reasons"]
    assert any("no checks" in r or "없다" in r for r in result["reasons"]), result["reasons"]


def t_finder_empty_state_still_reports_comment_missing(monkeypatch, fixture_repo):
    """양쪽 헤더 모양 다 없는 PR — finder 는 여전히 `None`, `evaluate()` 는
    여전히 comment-not-found 로 막힌다(#2231 이전과 같은 동작)."""
    import json

    def fake_run(argv, cwd, capture_output, text):
        class R:
            returncode = 0
            stdout = json.dumps({"comments": [{"body": "unrelated comment"}]})
        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)

    found = merge_gate.latest_check_runner_comment(fixture_repo, 2228)
    assert found is None

    result = merge_gate.evaluate(fixture_repo, fixture_repo, 2228, "issue-9002")
    assert result["allowed"] is False
    assert any("코멘트" in r for r in result["reasons"])


def t_exempt_own_record_kind_drops_only_the_supplying_prs_own_kind():
    missing = ["execution-observation", "conformance-review"]

    # issue #2380 (stage 5 하에서 record-kind 축): PR #2220 의 모양 --
    # issue-2204/execution-observation 은 스스로 execution-observation 을
    # 공급하는 관찰자 record PR 이다. #2233 은 자기 kind 만 뺐었지만
    # (순환이 남아있던 지점), 이제는 형제(sibling) kind 인
    # conformance-review 도 함께 빠진다 -- 같은 리뷰 사이클에 나란히 열린
    # 관찰자 PR 이 서로의 선행 머지를 요구하는 순환을 깬다.
    own = merge_gate._exempt_own_record_kind(missing, "issue-2204",
                                              "issue-2204/execution-observation")
    assert own == [], own

    # 거울 방향: conformance-review PR 도 마찬가지로 둘 다 빠진다.
    mirror = merge_gate._exempt_own_record_kind(missing, "issue-2204",
                                                 "issue-2204/conformance-review")
    assert mirror == [], mirror

    # own_kind 가 PR_TRIGGERED_RECORD_KINDS 밖이면(예: subject 의
    # implementation PR) 기존처럼 자기 kind 하나만 빠진다 -- 구조적 예외가
    # 아니라는 증거: implementation PR 은 여전히 두 관찰자 kind 모두 요구한다.
    missing_with_impl = ["implementation", "execution-observation", "conformance-review"]
    impl = merge_gate._exempt_own_record_kind(missing_with_impl, "issue-2204",
                                               "issue-2204/implementation")
    assert impl == ["execution-observation", "conformance-review"], impl

    # 다른 subject/role 의 PR 은 손대지 않는다(no-op).
    other = merge_gate._exempt_own_record_kind(missing, "issue-2204",
                                                "issue-9999/implementation")
    assert other == missing

    # PR 문맥이 없으면(own_branch=None) 오늘과 같은 목록 그대로.
    none_ctx = merge_gate._exempt_own_record_kind(missing, "issue-2204", None)
    assert none_ctx == missing


def t_required_verification_missing_still_blocks_the_role_the_pr_does_not_supply(monkeypatch):
    """순환 예외가 구조적("이 subject 는 절대 안 막힘")이 아니라
    PR 자신의 role 하나에만 좁혀졌다는 것 — subject 의 subject PR
    (issue-<n>/implementation)에는 여전히 두 role 모두 필요하다는 걸
    확인한다."""
    import spawn
    import spawn_on_pr

    monkeypatch.setattr(spawn, "board", lambda root: {
        "issue-2204": {}  # 아직 어떤 관찰자 record 도 랜딩 안 된 board 상태
    })
    monkeypatch.setattr(merge_gate, "pr_refs",
                         lambda repo, pr: {"base_ref": "main",
                                            "head_ref": "issue-2204/implementation"})
    missing = merge_gate.required_verification_missing(
        Path("."), "issue-2204", Path("."), 2212)
    assert set(missing) == set(spawn_on_pr.PR_TRIGGERED_RECORD_KINDS), missing


def t_required_verification_missing_exempts_the_observer_pr_that_supplies_it(monkeypatch):
    import spawn

    monkeypatch.setattr(spawn, "board", lambda root: {"issue-2204": {}})
    monkeypatch.setattr(merge_gate, "pr_refs",
                         lambda repo, pr: {"base_ref": "main",
                                            "head_ref": "issue-2204/execution-observation"})
    missing = merge_gate.required_verification_missing(
        Path("."), "issue-2204", Path("."), 2220)
    # issue #2380: this used to assert `missing == ["conformance-review"]`
    # (i.e. execution-observation's own gate check still demanded its
    # sibling conformance-review already be merged to main) -- that is
    # exactly the deadlock #2380 reports: neither sibling can be first.
    # Both PR_TRIGGERED_ROLES are now exempted when the PR under
    # evaluation is itself one of them.
    assert missing == [], missing


def t_issue_2380_sibling_observer_prs_neither_blocks_on_the_other(monkeypatch):
    """AC2 regression: spawn two sibling observer PRs for the same issue
    (execution-observation and conformance-review), neither merged to
    main -- `required_verification_missing()` must not flag either as
    missing because of the other's absence. A control case (the
    subject's own implementation PR, which is not itself an observer
    record) must still report both roles missing."""
    import spawn

    # Neither observer role has landed to main yet -- fresh board.
    monkeypatch.setattr(spawn, "board", lambda root: {"issue-7777": {}})

    monkeypatch.setattr(merge_gate, "pr_refs",
                         lambda repo, pr: {"base_ref": "main",
                                            "head_ref": "issue-7777/execution-observation"})
    eo_missing = merge_gate.required_verification_missing(
        Path("."), "issue-7777", Path("."), 9001)
    assert eo_missing == [], eo_missing

    monkeypatch.setattr(merge_gate, "pr_refs",
                         lambda repo, pr: {"base_ref": "main",
                                            "head_ref": "issue-7777/conformance-review"})
    cr_missing = merge_gate.required_verification_missing(
        Path("."), "issue-7777", Path("."), 9002)
    assert cr_missing == [], cr_missing

    # Control: a PR that is not itself an observer record (the subject's
    # own implementation PR) is unaffected -- both roles still missing.
    monkeypatch.setattr(merge_gate, "pr_refs",
                         lambda repo, pr: {"base_ref": "main",
                                            "head_ref": "issue-7777/implementation"})
    impl_missing = merge_gate.required_verification_missing(
        Path("."), "issue-7777", Path("."), 9003)
    assert set(impl_missing) == {"execution-observation", "conformance-review"}, impl_missing


def t_issue_2380_sibling_observer_prs_evaluate_end_to_end(monkeypatch):
    """Same scenario as above but through `evaluate()` -- confirms
    neither sibling PR is refused for a missing-verification reason
    when the other is only an open (unmerged) sibling. The manual
    override pattern (release-eng consult + basis comment) should not
    be necessary for this to clear."""
    import spawn

    monkeypatch.setattr(spawn, "board", lambda root: {"issue-7777": {}})
    monkeypatch.setattr(merge_gate, "stale_revert_reasons", lambda repo, pr: [])
    body = check_runner.format_comment([
        {"check": "`a`", "type": "test", "status": "pass", "output": ""}])
    monkeypatch.setattr(merge_gate, "latest_check_runner_comment", lambda repo, pr: body)

    monkeypatch.setattr(merge_gate, "pr_refs",
                         lambda repo, pr: {"base_ref": "main",
                                            "head_ref": "issue-7777/execution-observation"})
    eo_result = merge_gate.evaluate(Path("."), Path("."), 9001, "issue-7777")
    assert not any("검증 기록" in r for r in eo_result["reasons"]), eo_result

    monkeypatch.setattr(merge_gate, "pr_refs",
                         lambda repo, pr: {"base_ref": "main",
                                            "head_ref": "issue-7777/conformance-review"})
    cr_result = merge_gate.evaluate(Path("."), Path("."), 9002, "issue-7777")
    assert not any("검증 기록" in r for r in cr_result["reasons"]), cr_result


def t_full_sequence_reaches_allow_merge_once_every_precondition_holds(monkeypatch):
    """issue #2233 acceptance provenance, mechanical half: no PR open in this
    repo today has both `execution-observation`/`conformance-review` merged
    to `main` while its own implementation PR is still open (verified live —
    see the implementation record's Acceptance section) — so ALLOW_MERGE
    cannot be produced against a real open PR without merging someone else's
    role PR first, which is outside this session's write scope. This test
    proves the *mechanism* deterministically: once check-runner genuinely
    passes, no verification record is missing, and stale-revert is clean,
    `verdict_gate.classify()` reaches `ALLOW_MERGE` on a `MERGE` verdict —
    same code path `gates/merge_gate.py`/`gates/verdict_gate.py` run live
    against PR #2223 in the record, just with the one precondition this
    session cannot itself supply (another role's merged record) held true."""
    import verdict_gate

    # issue #2381 R1: stub the new `evaluate()` fetch — see the sibling
    # comment on `t_merge_gate_evaluate_refuses_no_checks_as_a_pass`.
    monkeypatch.setattr(check_runner, "fetch_all_role_branches", lambda repo: None)
    monkeypatch.setattr(merge_gate, "latest_check_runner_comment",
                         lambda repo, pr: "## Acceptance check-runner result: 1/1 passed\n\n"
                                          "- [PASS] (test) `tests/test_x.py`")
    monkeypatch.setattr(merge_gate, "required_verification_missing",
                         lambda root, subject, repo=None, pr=None: [])
    monkeypatch.setattr(merge_gate, "stale_revert_reasons", lambda repo, pr: [])

    gate_result = merge_gate.evaluate(Path("."), Path("."), 2223, "issue-2215")
    assert gate_result == {"allowed": True, "reasons": []}, gate_result

    # `classify()` 는 순수 함수라 여기까지 오면 더 흉내낼 게 없다 —
    # `evaluate()`가 만든 진짜 결과를 그대로 넣는다(issue #1669).
    action = verdict_gate.classify("Verdict: MERGE", gate_result, tests_pass=True)
    assert action == "ALLOW_MERGE", action


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
    # monkeypatch 를 쓰는 테스트는 pytest 전용 — 직접 실행 모드에서는
    # pytest 를 통해서만 돈다(`python3 -m pytest gates/test_merge_gate.py`).
    import inspect
    direct = [(n, f) for n, f in tests if "monkeypatch" not in inspect.signature(f).parameters]
    _run(direct)
    skipped = [n for n, f in tests if "monkeypatch" in inspect.signature(f).parameters]
    if skipped:
        print(f"SKIPPED (pytest 전용, monkeypatch 필요): {', '.join(skipped)}")
