#!/usr/bin/env python3
"""issue #517 — `gates.record_lint` 단일 패스 집계 테스트.

`test_gates_refusal.py`와 같은 오프라인 관례: 임시 디렉터리에 실제 git
저장소를 만들고 그 위에서 돈다. 네트워크 없음.

  python3 gates/test_record_lint.py
  python3 -m pytest gates/test_record_lint.py -q
"""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import record_lint
import gates


def _run(*args, cwd):
    p = subprocess.run(["git", "-C", str(cwd), *args],
                        capture_output=True, text=True)
    assert p.returncode == 0, (args, p.stdout, p.stderr)
    return p.stdout


def _repo_with_record(record_body: str, role: str = "implementation",
                       rel: str | None = None):
    """`test_gates_refusal.py::_repo_with_record`와 같은 관례: origin/main 에
    빈 상태를 커밋하고, HEAD 에서 레코드 하나를 추가한 임시 git repo. 정리는
    호출자 책임이 아니다(임시 디렉터리, 프로세스 종료 시 OS 가 회수)."""
    d = Path(tempfile.mkdtemp())
    _run("init", "-q", "-b", "main", cwd=d)
    _run("config", "user.email", "t@example.com", cwd=d)
    _run("config", "user.name", "t", cwd=d)
    (d / "README.md").write_text("base")
    _run("add", "-A", cwd=d)
    _run("commit", "-q", "-m", "base", cwd=d)
    _run("update-ref", "refs/remotes/origin/main", "HEAD", cwd=d)
    _run("checkout", "-q", "-b", "issue-517/implementation", cwd=d)
    rel = rel or f"docs/issue-517/reports/{role}.md"
    record = d / rel
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(record_body)
    _run("add", "-A", cwd=d)
    _run("commit", "-q", "-m", "head", cwd=d)
    return d, record


def t_one_invocation_reports_all_distinct_violations():
    """네 종류 이상의 서로 다른 체커가 같은 레코드 하나에서 동시에 위반을
    내고, `lint_record` 한 번 호출이 전부를 보고한다 — 첫 실패에서 멈추지
    않는다(issue #517 Acceptance)."""
    body = (
        "---\n"
        "loop_state: landed\n"
        "---\n\n"
        "# record\n\n"
        "body references `gates/does-not-exist-xyz.py`.\n\n"
        "We completed 5 of 10 checks without derivation.\n\n"
        "- claim — checked: some::test — result: unverifiable\n"
        "- unverifiable:\n")
    d, record = _repo_with_record(body)
    bad = record_lint.lint_record(record)

    assert any("Acceptance verification" in b for b in bad), bad   # missing required heading
    assert any("#330" in b for b in bad), bad                      # broken code reference
    assert any("#333" in b for b in bad), bad                      # bare count claim
    assert any("#310" in b for b in bad), bad                      # unverifiable, no reason
    assert any("#331" in b for b in bad), bad                      # checked-claim, no reason
    assert len(bad) >= 4, bad


def t_clean_record_yields_no_violations():
    body = (
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\nbody, no claims.\n")
    d, record = _repo_with_record(body)
    bad = record_lint.lint_record(record)
    assert bad == [], bad


def t_invalid_enum_value_is_reported():
    body = "---\nloop_state: bogus-state\n---\n\nbody\n"
    d, record = _repo_with_record(body)
    bad = record_lint.lint_record(record)
    assert any("enum" in b for b in bad), bad


def t_repo_with_no_records_yields_explicit_empty_state():
    d = Path(tempfile.mkdtemp())
    _run("init", "-q", "-b", "main", cwd=d)
    _run("config", "user.email", "t@example.com", cwd=d)
    _run("config", "user.name", "t", cwd=d)
    (d / "README.md").write_text("base")
    _run("add", "-A", cwd=d)
    _run("commit", "-q", "-m", "base", cwd=d)

    assert record_lint.find_records(d) == []
    rc = record_lint.main([str(d)])
    assert rc == 0


def t_non_record_path_is_reported_not_silently_skipped():
    d = Path(tempfile.mkdtemp())
    _run("init", "-q", "-b", "main", cwd=d)
    off_path = d / "docs" / "notes.md"
    off_path.parent.mkdir(parents=True, exist_ok=True)
    off_path.write_text("not a record")
    bad = record_lint.lint_record(off_path)
    assert bad and "레코드 경로 형태" in bad[0], bad


def t_state_claim_without_canonical_tag_is_reported():
    """issue #793: a state-claim line ("role X found Y") with no
    `canonical:` tag within 3 lines above it is flagged."""
    body = (
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\n"
        "The verify role found the defect in the parser.\n")
    d, record = _repo_with_record(body)
    bad = record_lint.lint_record(record)
    assert any("#793" in b for b in bad), bad


def t_state_claim_with_canonical_tag_passes():
    body = (
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\n"
        "canonical: src/parser.py:42-58\n"
        "The verify role found the defect in the parser.\n")
    d, record = _repo_with_record(body)
    bad = record_lint.lint_record(record)
    assert not any("#793" in b for b in bad), bad


def t_outcome_claim_without_executed_live_citation_is_reported():
    """issue #870: a done-claim backed only by a file-read citation (which
    satisfies #793's own state-claim check) is still refused — the
    citation is not itself an executed-live reference."""
    body = (
        "---\n"
        "loop_state: landed\n"
        "---\n\n"
        "# record\n\n"
        "canonical: docs/issue-870/reports/notes.md (read this session)\n"
        "The requirement is met and the deliverable is done.\n")
    d, record = _repo_with_record(body)
    bad = record_lint.lint_record(record)
    assert any("#870" in b for b in bad), bad


def t_outcome_claim_with_executed_live_citation_passes():
    """issue #870: a done-claim backed by a command actually run this
    turn passes without friction."""
    body = (
        "---\n"
        "loop_state: landed\n"
        "---\n\n"
        "# record\n\n"
        "canonical: `pytest -q gates/test_record_lint.py` (exit 0)\n"
        "The requirement is met and the deliverable is done.\n")
    d, record = _repo_with_record(body)
    bad = record_lint.lint_record(record)
    assert not any("#870" in b for b in bad), bad


def t_outcome_claim_with_unbacked_acceptance_prose_is_still_reported():
    """issue #870 before-landing hunt regression pin: `acceptance:` must
    be followed by an actual `result: PASS|FAIL|UNMEASURED` shape, not
    just the literal word — plain prose starting with "acceptance:" must
    not silently satisfy the executed-live citation requirement."""
    body = (
        "---\n"
        "loop_state: landed\n"
        "---\n\n"
        "# record\n\n"
        "canonical: acceptance: reviewer says it looks fine\n"
        "All requirements met, task complete.\n")
    d, record = _repo_with_record(body)
    bad = record_lint.lint_record(record)
    assert any("#870" in b for b in bad), bad


def t_outcome_claim_with_real_acceptance_result_line_passes():
    body = (
        "---\n"
        "loop_state: landed\n"
        "---\n\n"
        "# record\n\n"
        "canonical: acceptance: ./run-tests.sh — result: PASS\n"
        "All requirements met, task complete.\n")
    d, record = _repo_with_record(body)
    bad = record_lint.lint_record(record)
    assert not any("#870" in b for b in bad), bad


def t_outcome_claim_with_real_live_fire_result_line_passes():
    """issue #914 mechanism c: a `live-fire: <path> — result:
    allow|deny|log` citation is a sibling executed-live shape to
    `acceptance: ... — result: PASS|FAIL|UNMEASURED`, additive to #870's
    existing regex set."""
    body = (
        "---\n"
        "loop_state: landed\n"
        "---\n\n"
        "# record\n\n"
        "canonical: live-fire: on-the-record/hooks/new-guard.sh — result: allow\n"
        "All requirements met, task complete.\n")
    d, record = _repo_with_record(body)
    bad = record_lint.lint_record(record)
    assert not any("#870" in b for b in bad), bad


def t_outcome_claim_with_observation_transcript_citation_passes():
    """issue #923: an observation/verdict record's own natural prose
    `canonical:` citation naming the execution transcript/measurement it
    just produced is a third executed-live shape, additive to #870's two
    command-shaped ones — reproduces the #895 ambiguous-scenario
    scoreboard record that #870 previously refused
    (docs/issue-923/reports/defect-verification/current-state.md
    Finding 2)."""
    body = (
        "---\n"
        "loop_state: landed\n"
        "---\n\n"
        "# record\n\n"
        "## Scoreboard\n\n"
        "canonical: execution transcript for the ambiguous-scenario "
        "run, fixture PR #15 merged 2026-08-05\n"
        "- ambiguous-scenario requirement met: PASS\n")
    d, record = _repo_with_record(body)
    bad = record_lint.lint_record(record)
    assert not any("#870" in b for b in bad), bad


def t_outcome_claim_with_bare_file_read_citation_still_reported():
    """issue #923 regression pin: the new observation-live shape must NOT
    widen to a bare "read this session" file-read citation that names no
    transcript/measurement — #870's original fabrication catch stays
    intact."""
    body = (
        "---\n"
        "loop_state: landed\n"
        "---\n\n"
        "# record\n\n"
        "canonical: docs/issue-895/reports/execution-observation.md "
        "(read this session)\n"
        "ambiguous-scenario requirement met: PASS\n")
    d, record = _repo_with_record(body)
    bad = record_lint.lint_record(record)
    assert any("#870" in b for b in bad), bad


def t_no_outcome_claim_is_untouched():
    """issue #870 empty state: no outcome marker -> no #870 violation,
    same empty-state scoping #793 already follows."""
    body = (
        "---\n"
        "loop_state: coding\n"
        "---\n\n"
        "# record\n\n"
        "Still investigating the parser edge case.\n")
    d, record = _repo_with_record(body)
    bad = record_lint.lint_record(record)
    assert not any("#870" in b for b in bad), bad


def t_orphaned_path_reference_check_denies_genuinely_missing_path():
    """#744 item 2 regression pin — the legitimate case that must keep
    failing: a backtick path with no `:identifier()` locator suffix and
    no relationship to a path this same write set will later create.
    #744's own body places `orphaned_path_reference_check`'s logic out of
    scope until #730's guidance-only countermeasure has been observed in
    effect, so this only pins current behavior — it does not change it."""
    body = (
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\n"
        "See `gates/this-file-was-never-written.py` for details.\n")
    d, record = _repo_with_record(body)
    bad = record_lint.lint_record(record)
    assert any(
        "#330" in b and "gates/this-file-was-never-written.py" in b
        for b in bad), bad


def t_orphaned_path_reference_check_locator_suffix_resolved_issue_1620():
    """issue #1620 misfire class 1 fixes half of #744 item 2's documented
    gap: a `path:identifier()` locator suffix now strips before the
    existence check (`gates/claim_scan.py::scan_text()`,
    `gates/ci.py:_phase2_record_evidence()` shapes). The other half of
    #744 item 2 (a path this same write set creates later) is still open
    and out of #1620's scope — not tested here."""
    d, record = _repo_with_record(
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\n"
        "Locator suffix on a real file: "
        "`gates/real_module.py:helper()`.\n")
    (d / "gates").mkdir(parents=True, exist_ok=True)
    (d / "gates" / "real_module.py").write_text("# real file, not the ref\n")
    bad = record_lint.lint_record(record)
    assert not any("#330" in b for b in bad), bad


def t_orphaned_path_reference_check_double_colon_function_suffix():
    """issue #1620 misfire class 1: `path.py::func_name()` (double
    colon) strips the same way as the single-colon locator form."""
    d, record = _repo_with_record(
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\n"
        "See `gates/claim_scan.py::scan_text()` for details.\n")
    (d / "gates").mkdir(parents=True, exist_ok=True)
    (d / "gates" / "claim_scan.py").write_text("# real file\n")
    bad = record_lint.lint_record(record)
    assert not any("#330" in b for b in bad), bad


def t_orphaned_path_reference_check_comma_separated_line_list():
    """issue #1620 misfire class 1: `path.py:60,137` names two lines in
    a real file, not a broken path — the comma-separated line list must
    strip the same way a single `:line` or `:start-end` suffix does."""
    d, record = _repo_with_record(
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\n"
        "See `gates/landing_readiness.py:60,137` for both call sites.\n")
    (d / "gates").mkdir(parents=True, exist_ok=True)
    (d / "gates" / "landing_readiness.py").write_text("# real file\n" * 200)
    bad = record_lint.lint_record(record)
    assert not any("#330" in b for b in bad), bad


def t_orphaned_path_reference_check_exempts_rename_narration():
    """issue #1620 misfire class 2: a record explicitly narrating that a
    path was renamed away must not fire — it is deviation narration
    about a former path, not a live reachability claim."""
    d, record = _repo_with_record(
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\n"
        "`gates/old_module.py` was renamed away from during this pass; "
        "see `gates/new_module.py` instead.\n")
    (d / "gates").mkdir(parents=True, exist_ok=True)
    (d / "gates" / "new_module.py").write_text("# real file\n")
    bad = record_lint.lint_record(record)
    assert not any(
        "#330" in b and "old_module.py" in b for b in bad), bad


def t_orphaned_path_reference_check_still_fires_on_genuinely_missing_rename():
    """Sibling negative for misfire class 2: a citation with no rename
    narration around it still fires on a genuinely missing path — the
    narration exemption must not blanket-suppress the rule."""
    d, record = _repo_with_record(
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\n"
        "See `test/test_bootstrap_timing.py` for the test.\n")
    bad = record_lint.lint_record(record)
    assert any(
        "#330" in b and "test/test_bootstrap_timing.py" in b
        for b in bad), bad


def t_orphaned_path_reference_check_exempts_untracked_out_of_scope_narration():
    """issue #1628: a record explicitly narrating that a cited path is
    untracked/out-of-scope must not fire — the path may legitimately no
    longer exist on disk by the time the record is read back."""
    d, record = _repo_with_record(
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\n"
        "This session found three untracked files, plus\n"
        "(`gates/stray_untracked_artifact.py` and its two test files) —\n"
        "all belonging to a separately-approved PR, not to this proposal.\n")
    bad = record_lint.lint_record(record)
    assert not any(
        "#330" in b and "stray_untracked_artifact.py" in b
        for b in bad), bad


def t_orphaned_path_reference_check_still_fires_on_genuinely_missing_no_narration():
    """Sibling negative for the #1628 misfire class: a citation of a
    genuinely-missing path with no untracked/out-of-scope narration
    around it still fires — the narration exemption must not
    blanket-suppress the rule."""
    d, record = _repo_with_record(
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\n"
        "See `gates/this-file-was-never-written-either.py` for details.\n")
    bad = record_lint.lint_record(record)
    assert any(
        "#330" in b and "this-file-was-never-written-either.py" in b
        for b in bad), bad


def t_orphaned_path_reference_check_exempts_absence_negation():
    """issue #1620 misfire class 3: "no decisions/ entry needed" states
    that a path is deliberately not created, not that it should resolve
    on disk."""
    d, record = _repo_with_record(
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\n"
        "No `docs/decisions/never-written.md` entry needed for this "
        "change.\n")
    bad = record_lint.lint_record(record)
    assert not any("#330" in b for b in bad), bad


def t_git_tracked_path_reference_check_denies_uncommitted_present_path():
    """issue #1085 regression pin: a backtick path that IS present in the
    working tree (so #330's `orphaned_path_reference_check` passes it)
    but was never added in any commit is refused — the #1062 record's
    false-citation class (a path present at authoring time, never
    staged, never committed)."""
    body = (
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\n"
        "canonical: `docs/issue-517/reports/panel/never-committed.md`\n")
    d, record = _repo_with_record(body)
    (d / "docs/issue-517/reports/panel").mkdir(parents=True, exist_ok=True)
    (d / "docs/issue-517/reports/panel/never-committed.md").write_text(
        "present on disk, never git add'ed or committed\n")
    bad = record_lint.lint_record(record)
    assert any(
        "#1085" in b and "docs/issue-517/reports/panel/never-committed.md" in b
        for b in bad), bad


def t_git_tracked_path_reference_check_passes_committed_path():
    """Sibling positive: the same shape, but the path was actually
    committed — must not be flagged."""
    body = (
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\n"
        "canonical: `gates/real_module.py`\n")
    d, record = _repo_with_record(body)
    (d / "gates").mkdir(parents=True, exist_ok=True)
    (d / "gates" / "real_module.py").write_text("# real, committed\n")
    _run("add", "-A", cwd=d)
    _run("commit", "-q", "-m", "add real_module", cwd=d)
    bad = record_lint.lint_record(record)
    assert not any("#1085" in b for b in bad), bad


def t_git_tracked_path_reference_check_exempts_self_citation():
    """The record currently being written cites its own path and is not
    yet committed (mid-authoring, before the closing commit) — exempt,
    since the in-progress write cannot yet have git history for
    itself."""
    d = Path(tempfile.mkdtemp())
    _run("init", "-q", "-b", "main", cwd=d)
    _run("config", "user.email", "t@example.com", cwd=d)
    _run("config", "user.name", "t", cwd=d)
    (d / "README.md").write_text("base")
    _run("add", "-A", cwd=d)
    _run("commit", "-q", "-m", "base", cwd=d)
    _run("checkout", "-q", "-b", "issue-517/implementation", cwd=d)
    rel = "docs/issue-517/reports/implementation.md"
    record = d / rel
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\n"
        f"See `{rel}` for the full record.\n")
    # deliberately not committed — pins the mid-authoring exemption
    bad = record_lint.lint_record(record)
    assert not any("#1085" in b for b in bad), bad


def t_defect_claim_with_bare_grep_citation_is_reported():
    """issue #791 class 1: a defect/root-cause claim backed only by a
    bare grep-shaped `file:line` mention (no fenced multi-line quote) is
    refused — locating a candidate is not itself evidence."""
    d, record = _repo_with_record(
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\n"
        "grep hit: `gates/real_module.py:5` mentions broken_thing.\n"
        "The root cause is a bug in broken_thing.\n")
    (d / "gates").mkdir(parents=True, exist_ok=True)
    (d / "gates" / "real_module.py").write_text(
        "def helper():\n"
        "    return 1\n\n\n"
        "def broken_thing():\n"
        "    x = 1\n"
        "    raise ValueError('boom')\n")
    bad = record_lint.lint_record(record)
    assert any("#791" in b for b in bad), bad


def t_defect_claim_with_verbatim_grounded_citation_passes():
    """issue #791 class 2: a defect/root-cause claim backed by a >=3-line
    fenced quote that verbatim-matches the cited file:line range in the
    working tree passes without friction."""
    body = (
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\n"
        "`gates/real_module.py:5-7`\n"
        "```\n"
        "def broken_thing():\n"
        "    x = 1\n"
        "    raise ValueError('boom')\n"
        "```\n"
        "The root cause is a bug in broken_thing.\n")
    d, record = _repo_with_record(body)
    (d / "gates").mkdir(parents=True, exist_ok=True)
    (d / "gates" / "real_module.py").write_text(
        "def helper():\n"
        "    return 1\n\n\n"
        "def broken_thing():\n"
        "    x = 1\n"
        "    raise ValueError('boom')\n")
    bad = record_lint.lint_record(record)
    assert not any("#791" in b for b in bad), bad


def t_no_defect_claim_is_untouched():
    """issue #791 class 3 (empty state): a record with no defect/
    root-cause trigger line is unaffected — additive/doc-only records
    and legitimate locate-only references stay untouched."""
    body = (
        "---\n"
        "loop_state: coding\n"
        "---\n\n"
        "# record\n\n"
        "Added the new export in `gates/real_module.py:5`. "
        "No bugs found in this pass.\n")
    d, record = _repo_with_record(body)
    (d / "gates").mkdir(parents=True, exist_ok=True)
    (d / "gates" / "real_module.py").write_text("def broken_thing():\n    pass\n")
    bad = record_lint.lint_record(record)
    assert not any("#791" in b for b in bad), bad


def t_terminal_loop_state_dict_shaped_states_no_crash():
    """issue #1105: `role_cfg['record_fields']['loop_state']` 가 리스트가
    아니라 dict(progress/terminal/refusal/error 로 나뉜 형태 — 저장소의
    다수 role 정의가 실제로 이 형태다)면 `states[-1]` 은 KeyError: -1 로
    터진다(정수 -1 키가 dict 에 없으므로). 클린 트리에서도 재현되는
    조건이지만, 오케스트레이터가 실제로 마주친 건 머지 중 작업 트리였다
    (2026-08-12, PR #1100). `_terminal_loop_state` 는 이런 atypical 형태에
    None 을 돌려줘야지 죽어선 안 된다."""
    body = (
        "---\n"
        "loop_state: landed\n"
        "---\n\n"
        "# record\n\n"
        "## Acceptance verification\n"
        "checked: something — result: pass\n"
    )
    d, record = _repo_with_record(
        body, role="architecture",
        rel="docs/issue-517/reports/architecture.md")
    role_cfg = json.loads(
        (Path(__file__).parent.parent / "roles" / "architecture.json")
        .read_text(encoding="utf-8"))
    assert isinstance(
        role_cfg.get("record_fields", {}).get("loop_state"), dict), (
        "fixture assumption broke: architecture.json's loop_state is no "
        "longer dict-shaped")
    assert gates._terminal_loop_state(role_cfg) is None
    bad = record_lint.lint_record(record)
    assert isinstance(bad, list)


def t_terminal_loop_state_empty_states_returns_none():
    """empty state 케이스: `loop_state` 리스트가 비어 있으면(혹은 키
    자체가 없으면) 오늘도 그랬듯 None — 정상 레코드 린트는 그대로다."""
    assert gates._terminal_loop_state({"record_fields": {"loop_state": []}}) is None
    assert gates._terminal_loop_state({"record_fields": {}}) is None
    assert gates._terminal_loop_state({}) is None
    assert gates._terminal_loop_state(
        {"record_fields": {"loop_state": ["a", "b"]}}) == "b"


def t_path_ref_with_line_suffix_existence_check_strips_suffix():
    """issue #1599 fix 1: `docs/specs/approvers.md:2` names a real file
    plus a `:line` suffix — the suffix must be stripped before the
    existence check, or a genuinely-existing file is flagged broken."""
    body = (
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\n"
        "See `docs/specs/approvers.md:2` for the approver list.\n")
    d, record = _repo_with_record(body)
    (d / "docs" / "specs").mkdir(parents=True, exist_ok=True)
    (d / "docs" / "specs" / "approvers.md").write_text("line1\nline2\n")
    bad = record_lint.lint_record(record)
    assert not any("#330" in b for b in bad), bad


def t_path_ref_with_range_suffix_existence_check_strips_suffix():
    """Same fix, range-suffix form: `path.md:129-132`."""
    body = (
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\n"
        "See `docs/specs/approvers.md:1-2` for the approver list.\n")
    d, record = _repo_with_record(body)
    (d / "docs" / "specs").mkdir(parents=True, exist_ok=True)
    (d / "docs" / "specs" / "approvers.md").write_text("line1\nline2\n")
    bad = record_lint.lint_record(record)
    assert not any("#330" in b for b in bad), bad


def t_sweep_mode_skips_record_authored_before_linter_birth():
    """issue #1599 fix 2: `find_records`'s whole-repo sweep mode must not
    grade a record last committed before the linter's own birth date
    (2026-08-09) — retro-grading a frozen historical record against
    rules it predates fabricates provenance if "fixed" post hoc."""
    d = Path(tempfile.mkdtemp())
    _run("init", "-q", "-b", "main", cwd=d)
    _run("config", "user.email", "t@example.com", cwd=d)
    _run("config", "user.name", "t", cwd=d)
    (d / "README.md").write_text("base")
    _run("add", "-A", cwd=d)
    _run("commit", "-q", "-m", "base", cwd=d)
    rel = "docs/issue-1/reports/implementation.md"
    record = d / rel
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(
        "---\nloop_state: landed\n---\n\n# record\n\nSession halted.\n")
    env = dict(**__import__("os").environ,
               GIT_AUTHOR_DATE="2026-07-29T10:00:00",
               GIT_COMMITTER_DATE="2026-07-29T10:00:00")
    subprocess.run(["git", "-C", str(d), "add", "-A"],
                    check=True, capture_output=True)
    subprocess.run(["git", "-C", str(d), "commit", "-q", "-m", "pre-cutoff"],
                    check=True, capture_output=True, env=env)
    found_default = record_lint.find_records(d)
    assert record not in found_default, found_default
    found_uncapped = record_lint.find_records(d, sweep_cutoff=False)
    assert record in found_uncapped, found_uncapped


def t_sweep_mode_keeps_record_authored_after_linter_birth():
    """Sibling positive: a record committed after the cutoff date stays
    in the sweep — the cutoff excludes pre-existing history, not
    everything."""
    d = Path(tempfile.mkdtemp())
    _run("init", "-q", "-b", "main", cwd=d)
    _run("config", "user.email", "t@example.com", cwd=d)
    _run("config", "user.name", "t", cwd=d)
    (d / "README.md").write_text("base")
    _run("add", "-A", cwd=d)
    _run("commit", "-q", "-m", "base", cwd=d)
    rel = "docs/issue-1/reports/implementation.md"
    record = d / rel
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(
        "---\nloop_state: landed\n---\n\n# record\n\nSession halted.\n")
    env = dict(**__import__("os").environ,
               GIT_AUTHOR_DATE="2026-08-10T10:00:00",
               GIT_COMMITTER_DATE="2026-08-10T10:00:00")
    subprocess.run(["git", "-C", str(d), "add", "-A"],
                    check=True, capture_output=True)
    subprocess.run(["git", "-C", str(d), "commit", "-q", "-m", "post-cutoff"],
                    check=True, capture_output=True, env=env)
    found = record_lint.find_records(d)
    assert record in found, found


def t_misfire_metadata_field_not_flagged_as_outcome_claim():
    """issue #1599 fix 3(a): `loop_state: done` inside YAML frontmatter is
    structural metadata, not a prose outcome claim."""
    text = "---\nloop_state: done\nverdict: landed\n---\n\n# record\n"
    assert record_lint.outcome_claim_citation_check(text) == []


def t_misfire_heading_not_flagged_as_state_claim():
    """issue #1599 fix 3(b): a section heading ("## Findings confirmed")
    names a section, it does not itself assert a state — extend the
    heading-skip already present in the outcome/defect checks to
    `canonical_source_claim_check`, which lacked it."""
    text = "## Findings confirmed\n\nSee below for detail.\n"
    assert record_lint.canonical_source_claim_check(text) == []


def t_misfire_blockquote_not_flagged_as_state_claim():
    """issue #1599 fix 3(c): a blockquote quoting another document's claim
    ("> ... was merged ...") is a quotation, not the author's own
    assertion."""
    text = "> The upstream PR says this was merged already.\n"
    assert record_lint.canonical_source_claim_check(text) == []


def t_misfire_hyphenated_name_not_flagged_as_ratio():
    """issue #1599 fix 3(d): "layer-2/3" is a hyphenated compound name,
    not a "2 of 3"-shaped ratio count claim."""
    text = "The change touches the layer-2/3 boundary code.\n"
    assert record_lint.bare_count_claim_check(text) == []


def t_misfire_absence_negation_not_flagged_as_bare_count():
    """issue #1620 misfire class 3: "not yet measurable (0/30)" negates
    the count claim itself, not just a claim marker word."""
    text = "Coverage is not yet measurable (0/30).\n"
    assert record_lint.bare_count_claim_check(text) == []


def t_misfire_inline_computed_percentage_not_flagged_as_bare_count():
    """issue #1620 misfire class 4a: a tally whose computation is shown
    inline (percentage next to the raw fraction) is self-evidencing."""
    text = "rule 330: 33.3% precision (4 TP / 12).\n"
    assert record_lint.bare_count_claim_check(text) == []


def t_misfire_fenced_output_above_not_flagged_as_bare_count():
    """issue #1620 misfire class 4b: a tally backed by a fenced
    raw-output block a few lines above it is already evidenced."""
    text = (
        "```\n"
        "4 passed, 0 failed\n"
        "```\n\n"
        "So 4 of 4 tests passed.\n")
    assert record_lint.bare_count_claim_check(text) == []


def t_misfire_canonical_tag_same_line_not_flagged_as_bare_count():
    """issue #1620 misfire class 4c: a `canonical:` citation on the
    count's own evidence line is itself the citation #333 asks for."""
    text = "canonical: 4 of 12 findings — docs/issue-1614/reports/panel.md\n"
    assert record_lint.bare_count_claim_check(text) == []


def t_misfire_unrelated_fence_far_above_still_flagged_as_bare_count():
    """PR #1622 review finding 1: a fence must CLOSE within a few lines
    above the count — an unrelated fence far above must not blanket-
    suppress every later bare count in the record."""
    text = (
        "```\n"
        "unrelated setup output\n"
        "```\n" +
        "\n".join(f"filler line {n}" for n in range(20)) +
        "\n\nWe found 4 of 12 findings to be genuine.\n")
    bad = record_lint.bare_count_claim_check(text)
    assert any("#333" in b for b in bad), bad


def t_misfire_fence_close_within_proximity_not_flagged_as_bare_count():
    """Positive twin: a fence that closes within the proximity window
    above the count is still exempted."""
    text = (
        "```\n"
        "4 passed, 0 failed\n"
        "```\n"
        "So 4 of 4 tests passed.\n")
    assert record_lint.bare_count_claim_check(text) == []


def t_misfire_unrelated_equals_above_still_flagged_as_bare_count():
    """PR #1622 review finding 2: an unrelated `=` above the count (e.g.
    a config assignment) must not suppress the finding — the computed
    signal must be on the count's own line."""
    text = "set FOO=bar in config.\nWe found 4 of 12 findings to be genuine.\n"
    bad = record_lint.bare_count_claim_check(text)
    assert any("#333" in b for b in bad), bad


def t_misfire_digits_adjacent_equals_same_line_not_flagged_as_bare_count():
    """Positive twin: digits directly adjacent to `=` on the count's own
    line is a genuine inline computation and stays exempted."""
    text = "9 keywords x 3 cases = 27 cases total.\n"
    assert record_lint.bare_count_claim_check(text) == []


def t_bare_count_claim_check_still_fires_without_evidence():
    """Sibling negative: a bare count with none of the #1620 evidence
    shapes nearby still fires — the exemptions must not blanket-suppress
    the rule."""
    text = "We found 4 of 12 findings to be genuine.\n"
    bad = record_lint.bare_count_claim_check(text)
    assert any("#333" in b for b in bad), bad


def t_misfire_cli_flag_pass_not_flagged_as_outcome():
    """issue #1599 fix 3(e): "pass" inside a CLI flag name (`--pass`,
    `--pass-through`) is not the outcome word "PASS"."""
    text = "Run `record_lint.py --pass-through` to skip this rule.\n"
    assert record_lint.outcome_claim_citation_check(text) == []


def t_misfire_counterfactual_sentence_not_flagged_as_state_claim():
    """issue #1599 fix 3(f): "Had this round found new bugs, ..." states
    a hypothetical, not an actual finding."""
    text = ("Had this round found new bugs, the queue would have grown "
            "further.\n")
    assert record_lint.canonical_source_claim_check(text) == []
    assert record_lint.outcome_claim_citation_check(
        "Had this been done differently, the result would differ.\n"
    ) == []


def t_commit_pinned_citation_recognized_as_evidence():
    """issue #1599 fix 4: a commit-pinned citation
    (`e7a13db:gates/record_lint.py:151`) is evidence in its own right —
    an OUTCOME/state claim carrying one should not also be refused for
    lacking a literal `canonical:`/`derived:` prefix."""
    outcome_text = (
        "Tests PASS (e7a13db1234:gates/test_record_lint.py:151).\n")
    assert record_lint.outcome_claim_citation_check(outcome_text) == []
    state_text = (
        "The prior session's PR was merged "
        "(e7a13db1234:docs/issue-1/reports/implementation.md:10).\n")
    assert record_lint.canonical_source_claim_check(state_text) == []


def t_1614_class1_pass_as_noun_not_flagged():
    """issue #1614 misfire class 1: "scout pass" uses "pass" as a noun
    (a round of scouting), not the outcome word PASS."""
    text = "The scout pass surfaced four candidate exemplars.\n"
    assert record_lint.outcome_claim_citation_check(text) == []


def t_1614_class1_pass_as_argument_passing_not_flagged():
    """issue #1614 misfire class 1: "passed a dict" is the verb "pass" in
    its argument-passing sense, not a completion claim."""
    text = "The caller passed a dict of options into the constructor.\n"
    assert record_lint.outcome_claim_citation_check(text) == []


def t_1614_class1_genuine_pass_claim_still_flagged():
    """A real completion claim ("Tests PASS") with no evidence still
    fires — the word-sense guard must not blanket-exempt the marker."""
    text = "Tests PASS for this change.\n"
    assert record_lint.outcome_claim_citation_check(text) != []


def t_1614_class1_done_as_attributive_participle_not_flagged():
    """issue #1614 misfire class 1: "once done" / "done work" are
    participle/attributive uses of "done", not a completion claim."""
    assert record_lint.outcome_claim_citation_check(
        "Once done, proceed to the next stage.\n") == []
    assert record_lint.outcome_claim_citation_check(
        "The already-done setup work stays untouched.\n") == []


def t_1614_class1_genuine_done_claim_still_flagged():
    """A real completion claim ("the migration is done.") with no
    evidence still fires."""
    text = "The migration is done.\n"
    assert record_lint.outcome_claim_citation_check(text) != []


def t_1614_class2_quoted_section_title_not_flagged():
    """issue #1614 misfire class 2: referencing the record-shape section
    name '## What was done' / "What will be done" in prose is a literal
    section-title mention, not a completion claim."""
    text = ('As required by the record shape, fill in the '
            '"What was done" section before merging.\n')
    assert record_lint.outcome_claim_citation_check(text) == []
    text2 = 'See "What will be done" below for the plan.\n'
    assert record_lint.outcome_claim_citation_check(text2) == []


def t_1614_class3_evidence_below_claim_recognized():
    """issue #1614 misfire class 3: a `canonical:`/executed-live citation
    up to 3 lines BELOW the claim (not just above) satisfies the
    adjacency requirement — previously only the above direction counted."""
    outcome_text = (
        "Tests PASS for this change.\n"
        "canonical: `pytest gates/test_record_lint.py -q`\n")
    assert record_lint.outcome_claim_citation_check(outcome_text) == []
    state_text = (
        "The upstream PR was merged.\n"
        "canonical: gh pr view 42\n")
    assert record_lint.canonical_source_claim_check(state_text) == []


def t_1614_class4_historical_narration_not_flagged():
    """issue #1614 misfire class 4: narrating an already-fixed, prior-
    round defect is historical narration, not a live defect claim."""
    text = ("Previously, the parser was broken — this has since been "
            "fixed and is no longer an issue.\n")
    assert record_lint.canonical_source_claim_check(text) == []
    defect_text = "Previously the root cause is a stale cache entry.\n"
    assert record_lint.defect_claim_grounding_check(
        Path(tempfile.mkdtemp()), defect_text) == []


def t_1614_class5_rule_self_quotation_exempted():
    """issue #1614 misfire class 5: a record documenting rule #870 itself
    (filed under docs/issue-870/) quotes the rule's own marker vocabulary
    to explain it — that quotation must not be graded as the author's own
    unevidenced claim, since `lint_record` exempts this rule for records
    under the rule's own issue tree."""
    body = (
        "---\nloop_state: landed\n---\n\n"
        "# record\n\n"
        "The rule fires on lines like 'the migration is done.' with no "
        "`canonical:` tag — see the OUTCOME_CLAIM_MARKER vocabulary.\n\n"
        "## What did not work\n\nNone.\n")
    d, record = _repo_with_record(
        body, rel="docs/issue-870/reports/implementation.md")
    bad = record_lint.lint_record(record)
    assert not any("#870" in b for b in bad), bad


def t_1614_class5_same_marker_still_flagged_outside_rule_issue():
    """The #870 exemption is scoped to docs/issue-870/ — an unrelated
    issue's record making the same bare claim is still graded."""
    body = (
        "---\nloop_state: landed\n---\n\n"
        "# record\n\n"
        "The migration is done.\n\n"
        "## What did not work\n\nNone.\n")
    d, record = _repo_with_record(
        body, rel="docs/issue-517/reports/implementation.md")
    bad = record_lint.lint_record(record)
    assert any("#870" in b for b in bad), bad


def t_1614_class6_negated_hypothetical_not_flagged():
    """issue #1614 misfire class 6: "cannot detect" / "would still pass"
    are negated/hypothetical, not an actual outcome or defect claim."""
    assert record_lint.outcome_claim_citation_check(
        "The lint rule would still pass on a fabricated excerpt.\n") == []
    assert record_lint.canonical_source_claim_check(
        "This scanner cannot detect a merged PR reliably.\n") == []


def t_1614_class6_genuine_claim_with_would_elsewhere_still_flagged():
    """A negation word elsewhere in a different, unrelated claim sentence
    must not blanket-exempt a real same-line completion claim."""
    text = "The build is done and ready to ship.\n"
    assert record_lint.outcome_claim_citation_check(text) != []


def t_2039_skill_verdict_missing_line_flagged():
    """issue #2039: a mounted skill with no matching `skill-verdict:` line
    in the record is refused, naming that skill."""
    body = "---\nloop_state: landed\n---\n\n## What did not work\nNone.\n"
    d, record = _repo_with_record(body)
    bad = record_lint.record_skill_verdicts_in(d, ["implementation-blueprint"])
    assert any("implementation-blueprint" in b for b in bad), bad


def t_2039_skill_verdict_empty_reason_flagged():
    """issue #2039: a `skill-verdict:` line present but with nothing after
    the dash is refused."""
    body = (
        "---\nloop_state: landed\n---\n\n"
        "skill-verdict: implementation-blueprint —\n\n"
        "## What did not work\nNone.\n")
    d, record = _repo_with_record(body)
    bad = record_lint.record_skill_verdicts_in(d, ["implementation-blueprint"])
    assert any("implementation-blueprint" in b for b in bad), bad


def t_2039_skill_verdict_satisfied_passes():
    """issue #2039: every mounted skill has a non-empty `skill-verdict:`
    line -> no violations."""
    body = (
        "---\nloop_state: landed\n---\n\n"
        "skill-verdict: implementation-blueprint — applied: invoked; used at spawn.py:8181.\n\n"
        "## What did not work\nNone.\n")
    d, record = _repo_with_record(body)
    bad = record_lint.record_skill_verdicts_in(d, ["implementation-blueprint"])
    assert bad == []


def t_2039_zero_mounted_skills_is_noop():
    """issue #2039: a session with zero mounted skills gets no violations,
    even against a record with no skill-verdict lines at all."""
    body = "---\nloop_state: landed\n---\n\n## What did not work\nNone.\n"
    d, record = _repo_with_record(body)
    bad = record_lint.record_skill_verdicts_in(d, [])
    assert bad == []


# --- issue #2219: evidence-resolution false-rejection fix ------------------
#
# 815 recorded sessions hit 2,543 gate denials; record-claim-guard alone
# fired in 46% of sessions. Some of those denials landed on records that
# DID carry evidence — the guard only looked a fixed few PHYSICAL lines
# away from the claim, so evidence living earlier in the same markdown
# section (a different "### N. <item>" subsection), or split across a
# soft-wrapped multi-line sentence, was invisible to it. Verbatim
# reproductions below, from docs/issue-2208's live session log
# (on-the-record-issue-2208-implementation.session.20260824T231045.
# 1590418.log) — recovered as directed by this issue's own Acceptance
# section.

def t_2219_outcome_claim_evidenced_earlier_in_same_section_passes():
    """issue #2219 repro 1 (issue #870 verbatim): a done/PASS-shaped
    outcome-summary line citing "the two fenced runs above" is grounded
    by two earlier `acceptance: <cmd> — result:` + fence pairs in the
    SAME section, several physical lines away — well outside the old
    3-4 line window. Before this fix, `outcome_claim_citation_check`
    denied this exact line (record-claim-guard: 레코드에 실행-근거 없는
    OUTCOME 주장 (issue #870): 'acceptance: diff of the two fenced runs
    above — result: both negative cases read `completed`')."""
    body = (
        "### 2. Strip negative clauses from the BM25 field\n\n"
        "`pipeline.py`: added the guard, cutting the negative clause "
        "before indexing.\n\n"
        "acceptance: pytest tests/test_retrieval_eval.py -v (BEFORE) "
        "— result:\n"
        "```\n"
        "9 passed in 0.7s\n"
        "```\n"
        "acceptance: same command (AFTER) — result:\n"
        "```\n"
        "9 passed in 14.12s\n"
        "```\n"
        "acceptance: diff of the two fenced runs above — result: both "
        "negative cases read `completed` in both runs, so neither "
        "changed outcome.\n")
    bad = record_lint.outcome_claim_citation_check(body)
    assert not any("diff of the two fenced runs above" in b for b in bad), bad


def t_2219_bare_derived_paragraph_wrapped_across_lines_satisfies_count():
    """issue #2219 repro 2 (issue #333 verbatim): a `derived:` citation
    written as a bare (non-backtick) paragraph lead-in, soft-wrapped
    across 4 physical lines, with the count claim itself on the LAST
    line of that same sentence. Before this fix,
    `bare_count_claim_check` denied this exact line (record-claim-guard:
    레코드에 근거 없는 개수 주장 (issue #333): '`fail-open`, with the full
    suite still passing 9/9.') because the same-line tail check never
    saw a `derived:` label three lines above, and the label itself
    lacked the backticks the old regex required."""
    body = (
        "acceptance: hunter's reproduction script, re-run after the "
        "fix — result:\n"
        "```\n"
        "outcome: fail-open\n"
        "```\n"
        "acceptance: `pytest -q` re-run after this fix — result:\n"
        "```\n"
        "9 passed in 14.12s\n"
        "```\n"
        "derived: per the two fenced results directly above, the "
        "leaked phrase is\n"
        "gone and the fast-path auto-pick outcome flips to\n"
        "`fail-open`, with the full suite still passing 9/9.\n")
    bad = record_lint.bare_count_claim_check(body)
    assert not any("9/9" in b for b in bad), bad


def t_2219_genuinely_unevidenced_claim_still_refused():
    """The fix must not weaken what the guards enforce: an outcome/
    state/count claim with NO fenced block, NO `canonical:`/`derived:`
    tag, and NO `acceptance: ... — result:` pairing anywhere in its
    section is still refused by all three rules."""
    body = (
        "## Some section\n\n"
        "The migration is done and the requirement is met.\n"
        "We found 4 of 12 findings to be genuine.\n")
    assert any("#870" in b for b in
               record_lint.outcome_claim_citation_check(body))
    assert any("#793" in b for b in
               record_lint.canonical_source_claim_check(body))
    assert any("#333" in b for b in
               record_lint.bare_count_claim_check(body))


def t_2219_acceptance_leadin_without_adjacent_fence_does_not_count():
    """Negative control: an `acceptance: ... — result:` lead-in that is
    NOT immediately followed by a fenced block is prose, not proof — it
    must not satisfy #793/#870 on its own (distinguishes the new
    acceptance+fence pairing from a blanket "any acceptance: line
    anywhere" exemption)."""
    body = (
        "## Some section\n\n"
        "acceptance: reviewer says it looks fine — result:\n\n"
        "Not a fenced block, just more prose here.\n\n"
        "The requirement is met and the deliverable is done.\n")
    bad = record_lint.outcome_claim_citation_check(body)
    assert any("#870" in b for b in bad), bad


def t_2219_derived_and_canonical_tags_evidence_a_claim_across_a_different_section_never_leak():
    """A `derived:`/`canonical:` tag in one section must not vouch for a
    claim in an UNRELATED later section — the widened search is
    section-scoped, not whole-record (PR #1622 already found the
    whole-record form too permissive for bare_count_claim_check's fence
    exemption; this pins the same boundary for #2219's widened
    canonical/derived/acceptance search)."""
    body = (
        "## Section 1\n\n"
        "canonical: `pytest -q gates/test_record_lint.py` (exit 0)\n"
        "derived: per the fenced run above, everything passed.\n\n"
        "## Section 2\n\n"
        "The requirement is met and the deliverable is done.\n")
    bad = record_lint.outcome_claim_citation_check(body)
    assert any("#870" in b and "deliverable is done" in b for b in bad), bad


def t_2219_rejection_message_names_the_passing_shape():
    """issue #2219 ask 2: a rejection must say what shape would pass,
    not just why it failed — cheap enough that the fix is one edit
    instead of a guess-and-retry loop."""
    body = "We found 4 of 12 findings to be genuine.\n"
    bad = record_lint.bare_count_claim_check(body)
    assert any("통과하려면" in b for b in bad), bad
    bad2 = record_lint.canonical_source_claim_check(
        "The verify role found the defect in the parser.\n")
    assert any("통과하려면" in b for b in bad2), bad2
    bad3 = record_lint.outcome_claim_citation_check(
        "The requirement is met and the deliverable is done.\n")
    assert any("통과하려면" in b for b in bad3), bad3


def t_2219_empty_record_passes_every_claim_guard_cleanly():
    """issue #2219 Acceptance — empty state: an empty record file with
    no claims at all must pass all guards cleanly, producing no denial.
    Scoped to the claim-shape checks record-claim-guard.sh runs
    (unlike `lint_record`'s full aggregate, this does not also run
    gates.py's unrelated frontmatter-wellformedness/tool-residue
    checks, which reject an empty file for a different, pre-existing
    reason that #2219 is not about)."""
    text = ""
    assert record_lint.unverifiable_reason_check(text) == []
    assert record_lint.checked_claim_reason_check(text) == []
    assert record_lint.bare_count_claim_check(text) == []
    assert record_lint.canonical_source_claim_check(text) == []
    assert record_lint.outcome_claim_citation_check(text) == []
    assert record_lint.defect_claim_grounding_check(
        Path(tempfile.mkdtemp()), text) == []


def _run_all():
    tests = [(n, f) for n, f in globals().items()
             if n.startswith("t_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
        except AssertionError as e:
            failed += 1
            print(f"FAIL {name}: {e}")
        else:
            print(f"ok {name}")
    print(f"{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
