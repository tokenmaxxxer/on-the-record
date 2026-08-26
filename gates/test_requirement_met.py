#!/usr/bin/env python3
"""issue #1651 — `gates/requirement_met.py` 단위 테스트.
네트워크 없음, `grade()` 순수 함수만 픽스처로 검사한다.

  python3 -m pytest gates/test_requirement_met.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import requirement_met as rm


_BODY = """## Acceptance
- check: unit test at `gates/test_requirement_met.py` runs and passes.
  provenance: executed-unit
- check: live check at `gates/requirement_met.py` runs against a real PR.
  provenance: executed-live
"""


def t_yes_with_artifact_present_in_diff_passes():
    diff = (
        "diff --git a/gates/test_requirement_met.py b/gates/test_requirement_met.py\n"
        "--- a/gates/test_requirement_met.py\n"
        "+++ b/gates/test_requirement_met.py\n"
        "+def t_new(): assert Path('gates/test_requirement_met.py').exists()\n"
    )
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.YES,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is False
    assert result["blocking_reasons"] == []


def t_yes_with_artifact_absent_from_diff_fails():
    diff = "diff --git a/other.py b/other.py\n+pass\n"
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.YES,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is True
    assert len(result["blocking_reasons"]) == 1
    assert "gates/test_requirement_met.py" in result["blocking_reasons"][0]


def t_no_verdict_never_blocks_even_without_artifact():
    diff = "diff --git a/other.py b/other.py\n+pass\n"
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.NO,
        "live check at `gates/requirement_met.py` runs against a real PR.": rm.NO,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is False


def t_unknown_verdict_never_blocks():
    diff = "diff --git a/other.py b/other.py\n+pass\n"
    result = rm.grade(_BODY, diff, {})
    assert result["blocked"] is False
    for c in result["criteria"]:
        assert c["verdict"] == rm.UNKNOWN
        assert c["blocking_fail"] is False


def t_yes_with_no_cited_artifact_at_all_blocks():
    body = """## Acceptance
- check: reviewers agree this looks fine.
  provenance: read
"""
    diff = "diff --git a/anything.py b/anything.py\n+pass\n"
    verdicts = {"reviewers agree this looks fine.": rm.YES}
    result = rm.grade(body, diff, verdicts)
    assert result["blocked"] is True


def t_semantic_verdict_is_advisory_only_recorded_not_blocking_by_itself():
    """NO/UNKNOWN semantic verdicts never block on their own — only the
    deterministic artifact-presence sub-check (YES + missing artifact)
    blocks. This asserts the separation the issue requires."""
    diff = (
        "diff --git a/gates/test_requirement_met.py b/gates/test_requirement_met.py\n"
        "+++ b/gates/test_requirement_met.py\n"
        "+# python3 gates/test_requirement_met.py\n"
        "diff --git a/gates/requirement_met.py b/gates/requirement_met.py\n"
        "+++ b/gates/requirement_met.py\n"
        "+# python3 gates/requirement_met.py\n"
    )
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.NO,
        "live check at `gates/requirement_met.py` runs against a real PR.": rm.UNKNOWN,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is False
    kinds = {c["raw"]: c["verdict"] for c in result["criteria"]}
    assert kinds["unit test at `gates/test_requirement_met.py` runs and passes."] == rm.NO
    assert kinds["live check at `gates/requirement_met.py` runs against a real PR."] == rm.UNKNOWN


def t_empty_state_no_check_bullets_is_distinct_result():
    body = "## Acceptance\nunverifiable: this is a subjective UX judgment.\n"
    result = rm.grade(body, "diff --git a/x b/x\n", {})
    assert result["empty_state"] is True
    assert result["criteria"] == []
    assert result["blocked"] is False
    assert "reason" in result


def t_empty_state_no_acceptance_section_is_distinct_result():
    body = "Just a plain issue with no headings."
    result = rm.grade(body, "diff --git a/x b/x\n", {})
    assert result["empty_state"] is True
    assert result["blocked"] is False


def t_multiple_criteria_one_blocking_one_not():
    diff = (
        "diff --git a/gates/test_requirement_met.py b/gates/test_requirement_met.py\n"
        "+++ b/gates/test_requirement_met.py\n"
        "+def t_new(): assert Path('gates/test_requirement_met.py').exists()\n"
    )
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.YES,
        "live check at `gates/requirement_met.py` runs against a real PR.": rm.YES,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is True
    assert len(result["blocking_reasons"]) == 1


def t_red_artifact_named_only_in_diff_header_prose_fails():
    """issue #1660 (#1651 리뷰 픽스, red case): 경로가 diff의 파일 헤더
    줄(`diff --git`/`---`/`+++`)에만 등장하고 실제 추가 hunk 라인에는
    등장하지 않으면 — "prose 로 경로만 이름 붙인 것" — 더 이상 통과하지
    않는다."""
    diff = (
        "diff --git a/gates/test_requirement_met.py b/gates/test_requirement_met.py\n"
        "index abc123..def456 100644\n"
        "--- a/gates/test_requirement_met.py\n"
        "+++ b/gates/test_requirement_met.py\n"
        "+pass\n"
    )
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.YES,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is True
    assert "gates/test_requirement_met.py" in result["blocking_reasons"][0]


def t_green_artifact_in_added_hunk_line_passes():
    """issue #1660 (#1651/#1661 리뷰 픽스, green case): 경로가 실제
    추가된 코드/테스트 hunk 라인 안에(주석이 아닌 진짜 코드로) 문자열로
    등장하면 통과한다."""
    diff = (
        "diff --git a/gates/test_requirement_met.py b/gates/test_requirement_met.py\n"
        "--- a/gates/test_requirement_met.py\n"
        "+++ b/gates/test_requirement_met.py\n"
        "+def t_new(): assert Path('gates/test_requirement_met.py').exists()\n"
    )
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.YES,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is False
    assert result["blocking_reasons"] == []


def t_red_artifact_named_only_in_added_markdown_line_fails():
    """issue #1660 (#1661 리뷰 픽스, red case): 아티팩트 경로가 오직
    추가된 `.md` 산문 라인에서만 이름으로 언급되고 실제 코드/테스트가
    바뀌지 않았다면 — self-attestation theater — 여전히 블록해야
    한다."""
    diff = (
        "diff --git a/docs/report.md b/docs/report.md\n"
        "--- a/docs/report.md\n"
        "+++ b/docs/report.md\n"
        "+We updated `gates/test_requirement_met.py` to cover this.\n"
    )
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.YES,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is True
    assert "gates/test_requirement_met.py" in result["blocking_reasons"][0]


def t_red_artifact_named_only_in_added_comment_line_fails():
    """issue #1660 (#1661 리뷰 픽스, red case): 아티팩트 경로가 코드
    파일 안이어도 주석 전용 추가 라인에만 등장하면 여전히 블록한다."""
    diff = (
        "diff --git a/gates/test_requirement_met.py b/gates/test_requirement_met.py\n"
        "--- a/gates/test_requirement_met.py\n"
        "+++ b/gates/test_requirement_met.py\n"
        "+# see gates/test_requirement_met.py for details\n"
    )
    verdicts = {
        "unit test at `gates/test_requirement_met.py` runs and passes.": rm.YES,
    }
    result = rm.grade(_BODY, diff, verdicts)
    assert result["blocked"] is True
    assert "gates/test_requirement_met.py" in result["blocking_reasons"][0]


def t_check_surfaces_per_criterion_advisory_record():
    """issue #1660: `check()`가 기준별 semantic verdict 를 advisory 로
    노출한다 — blocking_reasons 와 분리된 별도 키."""
    import unittest.mock as mock

    with mock.patch.object(rm.gh_rest, "fetch_issue_body", return_value=_BODY), \
         mock.patch.object(rm, "_pr_diff", return_value=(
             "diff --git a/gates/test_requirement_met.py b/gates/test_requirement_met.py\n"
             "+++ b/gates/test_requirement_met.py\n"
             "+# python3 gates/test_requirement_met.py\n")):
        result = rm.check(Path("."), 1651, 1, {
            "unit test at `gates/test_requirement_met.py` runs and passes.": rm.NO,
        })
    assert result["blocked"] is False
    assert len(result["advisory"]) == 2
    kinds = {a["raw"]: a["verdict"] for a in result["advisory"]}
    assert kinds["unit test at `gates/test_requirement_met.py` runs and passes."] == rm.NO
    assert kinds["live check at `gates/requirement_met.py` runs against a real PR."] == rm.UNKNOWN


_COMMAND_BODY = """## Acceptance
- check: cron job runs the installed line `python3 -m devdigest`.
  provenance: executed-live
"""


def t_command_identity_mismatch_blocks_even_without_yes_verdict():
    """issue #1696 — pilot-devdigest PR #6 shape: the recorded proof ran
    `python3 -m devdigest.cli` (a sibling, PYTHONPATH-dependent path)
    while the check names the installed `python3 -m devdigest` line. The
    deterministic layer must flag this regardless of the semantic
    verdict — it is a structural mismatch, not a judgment call."""
    diff = (
        "diff --git a/docs/issue-1/reports/implementation.md b/docs/issue-1/reports/implementation.md\n"
        "+++ b/docs/issue-1/reports/implementation.md\n"
        "+acceptance: PYTHONPATH=src python3 -m devdigest.cli — result: PASS\n"
    )
    result = rm.grade(_COMMAND_BODY, diff, {})
    assert result["blocked"] is True
    assert any("command-identity" in r for r in result["blocking_reasons"])
    crit = result["criteria"][0]
    assert crit["command_identity_mismatch"] is True


def t_command_identity_match_does_not_block():
    diff = (
        "diff --git a/docs/issue-1/reports/implementation.md b/docs/issue-1/reports/implementation.md\n"
        "+++ b/docs/issue-1/reports/implementation.md\n"
        "+acceptance: python3 -m devdigest — result: PASS\n"
    )
    result = rm.grade(_COMMAND_BODY, diff, {})
    assert result["blocked"] is False
    assert result["criteria"][0]["command_identity_mismatch"] is False


def t_command_identity_no_recorded_command_does_not_block():
    """No `acceptance:` citation in the diff at all — nothing to compare
    against, so the deterministic layer stays silent rather than
    guessing (false positive prevention)."""
    diff = "diff --git a/other.py b/other.py\n+++ b/other.py\n+pass\n"
    result = rm.grade(_COMMAND_BODY, diff, {})
    assert result["blocked"] is False
    assert result["criteria"][0]["command_identity_mismatch"] is False


def t_command_identity_ignored_for_executed_unit_provenance():
    body = """## Acceptance
- check: unit test runs `python3 -m devdigest`.
  provenance: executed-unit
"""
    diff = (
        "diff --git a/x.md b/x.md\n+++ b/x.md\n"
        "+acceptance: PYTHONPATH=src python3 -m devdigest.cli — result: PASS\n"
    )
    result = rm.grade(body, diff, {})
    assert result["criteria"][0]["command_identity_mismatch"] is False


def t_command_identity_flags_leading_token_mismatch_with_single_citation():
    """warrant-hunt finding 2026-08-17: `python` named vs `python3`
    actually run must not slip past the same-first-token filter when
    there is exactly one recorded citation to pair it with."""
    body = """## Acceptance
- check: cron job runs the installed line `python devdigest.py`.
  provenance: executed-live
"""
    diff = (
        "diff --git a/x.md b/x.md\n+++ b/x.md\n"
        "+acceptance: python3 devdigest.py — result: PASS\n"
    )
    result = rm.grade(body, diff, {})
    assert result["blocked"] is True
    assert result["criteria"][0]["command_identity_mismatch"] is True


def t_command_identity_flags_env_prefix_only_difference():
    """PR #1699 review defect 1: `PYTHONPATH=src python3 -m devdigest`
    recorded against a check naming `python3 -m devdigest` must NOT be
    normalized into a match — env-prefix is the exact crutch the
    command-identity rule forbids, so a prefix-only difference is a
    mismatch, even with >=2 citations in the diff (multi-citation path)."""
    diff = (
        "diff --git a/x.md b/x.md\n+++ b/x.md\n"
        "+acceptance: PYTHONPATH=src python3 -m devdigest — result: PASS\n"
        "+acceptance: other unrelated command — result: PASS\n"
    )
    result = rm.grade(_COMMAND_BODY, diff, {})
    assert result["blocked"] is True
    assert result["criteria"][0]["command_identity_mismatch"] is True


def t_command_identity_strips_cd_wrapper_head_for_candidate_matching():
    """PR #1699 review defect 2: with >=2 acceptance citations, a
    `cd src && python3 -m devdigest` recorded command must not silently
    escape the same-first-token candidate filter (its literal leading
    token is `cd`, not `python3`) — after stripping the cd head it
    matches the check's named command exactly, so no mismatch."""
    diff = (
        "diff --git a/x.md b/x.md\n+++ b/x.md\n"
        "+acceptance: cd src && python3 -m devdigest — result: PASS\n"
        "+acceptance: other unrelated command — result: PASS\n"
    )
    result = rm.grade(_COMMAND_BODY, diff, {})
    assert result["blocked"] is False
    assert result["criteria"][0]["command_identity_mismatch"] is False


def t_command_identity_flags_mismatch_inside_cd_wrapper_head():
    """Companion to the above: the cd/wrapper-head fallback must still
    catch a genuine mismatch, not just let wrapped commands through
    unconditionally — `cd src && python3 -m devdigest.cli` differs from
    the named `python3 -m devdigest` even after the cd head is stripped."""
    diff = (
        "diff --git a/x.md b/x.md\n+++ b/x.md\n"
        "+acceptance: cd src && python3 -m devdigest.cli — result: PASS\n"
        "+acceptance: other unrelated command — result: PASS\n"
    )
    result = rm.grade(_COMMAND_BODY, diff, {})
    assert result["blocked"] is True
    assert result["criteria"][0]["command_identity_mismatch"] is True


def t_evidence_in_record_command_output_only_passes():
    """issue #2137 (verify-at-landing): a record whose ONLY evidence is a
    command + output citation (`acceptance: <cmd> — result: PASS`) inside
    a record .md satisfies a YES-graded command check — no test file in
    the diff at all."""
    body = """## Acceptance
- check: `python3 scripts/build.py --check` exits 0.
  provenance: executed-live
"""
    diff = (
        "diff --git a/docs/issue-9/reports/implementation.md "
        "b/docs/issue-9/reports/implementation.md\n"
        "+++ b/docs/issue-9/reports/implementation.md\n"
        "+- acceptance: python3 scripts/build.py --check — result: PASS\n"
        "+  output: ok (exit 0)\n"
    )
    verdicts = {"`python3 scripts/build.py --check` exits 0.": rm.YES}
    result = rm.grade(body, diff, verdicts)
    assert result["blocked"] is False, result["blocking_reasons"]
    assert result["criteria"][0]["artifact_in_diff"] is True
    assert result["criteria"][0]["command_identity_mismatch"] is False


def t_evidence_in_record_bare_prose_mention_still_not_evidence():
    """A bare prose mention of the command in a .md (no `acceptance: ... —
    result:` shape) stays excluded — the #2137 exception is citation-shaped
    executed evidence only."""
    body = """## Acceptance
- check: `python3 scripts/build.py --check` exits 0.
  provenance: executed-live
"""
    diff = (
        "diff --git a/docs/issue-9/reports/implementation.md "
        "b/docs/issue-9/reports/implementation.md\n"
        "+++ b/docs/issue-9/reports/implementation.md\n"
        "+We plan to run python3 scripts/build.py --check later.\n"
    )
    verdicts = {"`python3 scripts/build.py --check` exits 0.": rm.YES}
    result = rm.grade(body, diff, verdicts)
    assert result["blocked"] is True


# --- issue #2231: grade prose bullets and bare empty state:/provenance:
# lines, not only check:/gate: bullets ---------------------------------

_PROSE_BODY = """## Acceptance
- Kill a role session mid-edit with uncommitted changes; the edits are
  recoverable from the checkpoint ref afterward.
- Checkpointing leaves the session's branch, HEAD, and index unchanged.
- Untracked files are captured, not just tracked modifications.

gate: `tests/test_workspace_checkpoint.py`
empty state: a workspace with a clean tree and no edits yet.
provenance: executed-live — the kill-mid-edit recovery must be real.
"""


def t_prose_bullets_and_bare_labels_are_all_graded():
    """issue #2231 repro: issue #2215's shape parsed 1/8 items before this
    fix. This trimmed fixture is 3 prose bullets + gate: + empty state: +
    provenance: = 6 items, all reachable now."""
    result = rm.grade(_PROSE_BODY, "diff --git a/x b/x\n+pass\n", {})
    assert result["empty_state"] is False
    assert len(result["criteria"]) == 6
    raws = {c["raw"] for c in result["criteria"]}
    assert "Untracked files are captured, not just tracked modifications." in raws
    assert "a workspace with a clean tree and no edits yet." in raws
    assert any(r.startswith("executed-live") for r in raws)


def t_prose_bullet_graded_yes_without_artifact_does_not_block():
    """A non-structural item (prose bullet, no check:/gate: label) is
    never required to cite an artifact — ACCEPTANCE FORMAT only demands
    that structure for criteria that reference an executable artifact.
    Blocking these would turn 'grade more' into 'block more than the
    format ever asked for' (the issue's own non-goal)."""
    diff = "diff --git a/x b/x\n+pass\n"
    verdicts = {
        "Untracked files are captured, not just tracked modifications.": rm.YES,
    }
    result = rm.grade(_PROSE_BODY, diff, verdicts)
    assert result["blocked"] is False, result["blocking_reasons"]
    crit = next(c for c in result["criteria"]
                if c["raw"] == "Untracked files are captured, "
                               "not just tracked modifications.")
    assert crit["structural"] is False
    assert crit["blocking_fail"] is False


def t_structural_check_bullet_among_prose_still_blocks_on_missing_artifact():
    """The check:/gate: item in a mixed section keeps the old, stricter
    behavior — only non-structural items get the new leniency."""
    diff = "diff --git a/other.py b/other.py\n+pass\n"
    verdicts = {"`tests/test_workspace_checkpoint.py`": rm.YES}
    result = rm.grade(_PROSE_BODY, diff, verdicts)
    assert result["blocked"] is True
    assert any("tests/test_workspace_checkpoint.py" in r
               for r in result["blocking_reasons"])


def t_no_gradable_criteria_is_distinguishable_from_a_real_pass_via_check():
    """issue #2231 defect 2: `check()`'s empty_state key lets a caller
    tell 'nothing was gradable' apart from 'graded and nothing blocked' —
    both have blocked=False but must not be reported the same way."""
    import unittest.mock as mock
    body = "## Acceptance\nunverifiable: this is a subjective UX judgment.\n"
    with mock.patch.object(rm.gh_rest, "fetch_issue_body", return_value=body), \
         mock.patch.object(rm, "_pr_diff", return_value="diff --git a/x b/x\n"):
        empty_result = rm.check(Path("."), 1, 1)
    with mock.patch.object(rm.gh_rest, "fetch_issue_body", return_value=_BODY), \
         mock.patch.object(rm, "_pr_diff", return_value=(
             "diff --git a/gates/test_requirement_met.py b/gates/test_requirement_met.py\n"
             "+++ b/gates/test_requirement_met.py\n"
             "+# python3 gates/test_requirement_met.py\n")):
        real_pass_result = rm.check(Path("."), 1, 1, {})
    assert empty_result["blocked"] is False
    assert real_pass_result["blocked"] is False
    assert empty_result["empty_state"] is True
    assert real_pass_result["empty_state"] is False
    assert empty_result != real_pass_result


def t_unverifiable_only_section_stays_empty_state_not_a_new_criterion():
    """`unverifiable:` is issue #310's explicit escape for 'no gradable
    criteria, here's why' — it must not itself become a gradable prose
    item under the new bullet parser."""
    body = "## Acceptance\nunverifiable: this is a subjective UX judgment.\n"
    result = rm.grade(body, "diff --git a/x b/x\n", {})
    assert result["empty_state"] is True
    assert result["criteria"] == []


# --- issue #2231 defect 3: citation-FORMAT false-block on the artifact-
# presence sub-check (PR #2223 live case: the record cited its evidence
# via a `canonical:` tag, not `acceptance: ... — result: ...`) ----------


def t_evidence_in_record_canonical_tag_citation_passes():
    body = "## Acceptance\ngate: `tests/test_workspace_checkpoint.py`\n"
    diff = (
        "diff --git a/docs/issue-9/reports/implementation.md "
        "b/docs/issue-9/reports/implementation.md\n"
        "+++ b/docs/issue-9/reports/implementation.md\n"
        "+canonical: `python3 -m pytest tests/test_workspace_checkpoint.py -v` — "
        "run against a live spawned workspace, all green.\n"
    )
    verdicts = {"`tests/test_workspace_checkpoint.py`": rm.YES}
    result = rm.grade(body, diff, verdicts)
    assert result["blocked"] is False, result["blocking_reasons"]
    assert result["criteria"][0]["artifact_in_diff"] is True


def t_bare_prose_mention_still_not_evidence_even_with_canonical_fix():
    """The canonical: fix stays narrow — a bare prose mention of the
    artifact (no citation tag at all) must keep blocking, exactly as
    t_red_artifact_named_only_in_added_markdown_line_fails already
    requires for the acceptance: shape."""
    body = "## Acceptance\ngate: `tests/test_workspace_checkpoint.py`\n"
    diff = (
        "diff --git a/docs/issue-9/reports/implementation.md "
        "b/docs/issue-9/reports/implementation.md\n"
        "+++ b/docs/issue-9/reports/implementation.md\n"
        "+We touched `tests/test_workspace_checkpoint.py` for this.\n"
    )
    verdicts = {"`tests/test_workspace_checkpoint.py`": rm.YES}
    result = rm.grade(body, diff, verdicts)
    assert result["blocked"] is True


def t_issue_2414_population_not_declared_is_unaffected():
    """Backward compat: a check: with no `population:` metadata line never
    triggers the convergence check, regardless of provenance or diff
    content — the field is opt-in (issue-2414 Failure B)."""
    body = """## Acceptance
- check: `gates/requirement_met.py` runs against a real PR.
  provenance: executed-live
"""
    diff = "diff --git a/x.py b/x.py\n+++ b/x.py\n+pass\n"
    result = rm.grade(body, diff, {})
    assert result["blocked"] is False
    assert result["criteria"][0]["convergence_evidence_missing"] is False


def t_issue_2414_population_declared_without_before_after_blocks():
    """issue-2414 Failure B repro: a check: opts into `population:` and
    claims executed-live, but the diff shows only a command that ran —
    no before/after count. #2400's own shape: 'the prune command ran
    with exit 0' does not prove it reached the population it was built
    for (#2413: 419 of 434 records were exempt from the very prune added
    to clear them)."""
    body = """## Acceptance
- check: spawn.py prunes stale spawn-attempt records.
  provenance: executed-live
  population: runs/spawn-attempts.jsonl
"""
    diff = (
        "diff --git a/spawn.py b/spawn.py\n"
        "+++ b/spawn.py\n"
        "+def _prune_spawn_attempts(): ...\n"
        "diff --git a/docs/issue-2400/reports/implementation.md "
        "b/docs/issue-2400/reports/implementation.md\n"
        "+++ b/docs/issue-2400/reports/implementation.md\n"
        "+acceptance: python3 spawn.py prune-spawn-attempts — result: PASS\n"
    )
    result = rm.grade(body, diff, {})
    assert result["blocked"] is True
    assert any("population" in b for b in result["blocking_reasons"])


def t_issue_2414_population_declared_with_before_after_passes():
    """The same check:, now with a before/after count recorded anywhere
    in the diff's added lines — matches the real shape PR #2400's own
    body used ('One-time cleanup of the live runs/spawn-attempts.jsonl:
    341 -> 41 lines')."""
    body = """## Acceptance
- check: spawn.py prunes stale spawn-attempt records.
  provenance: executed-live
  population: runs/spawn-attempts.jsonl
"""
    diff = (
        "diff --git a/spawn.py b/spawn.py\n"
        "+++ b/spawn.py\n"
        "+def _prune_spawn_attempts(): ...\n"
        "diff --git a/docs/issue-2400/reports/implementation.md "
        "b/docs/issue-2400/reports/implementation.md\n"
        "+++ b/docs/issue-2400/reports/implementation.md\n"
        "+acceptance: python3 spawn.py prune-spawn-attempts — result: PASS\n"
        "+One-time cleanup of the live runs/spawn-attempts.jsonl: 341 -> 41 lines.\n"
    )
    result = rm.grade(body, diff, {})
    assert result["blocked"] is False
    assert result["criteria"][0]["convergence_evidence_missing"] is False


def t_issue_2414_real_case_2413_gap_would_have_blocked():
    """Demonstrated against the real case (issue-2414 Acceptance: 'if B
    is judged worth addressing... demonstrated against a real case').
    #2413 reports the actual live numbers after PR #2400 landed: 434
    total, 419 orphaned, exempt forever ('unresolved -- 항상 유지').
    Recreate the shape #2400's Acceptance (issue #2393) would have had
    under this rule for its ONGOING rotation-reaches-the-backlog claim
    (as opposed to the one-time cleanup, which #2400 already evidenced
    with real before/after numbers) — no before/after count for the
    backlog exists anywhere in the diff, because none was produced; this
    is exactly the gap #2413 found live 15 minutes after merge."""
    body = """## Acceptance
- check: the ongoing prune/rotation policy reaches the orphaned
  test-origin backlog, not just new inflow.
  provenance: executed-live
  population: runs/spawn-attempts.jsonl (orphaned, no-outcome entries)
"""
    diff = (
        "diff --git a/spawn.py b/spawn.py\n"
        "+++ b/spawn.py\n"
        "+    if outcome is None: keep_ids.add(aid)  # unresolved -- always kept\n"
        "diff --git a/docs/issue-2400/reports/implementation.md "
        "b/docs/issue-2400/reports/implementation.md\n"
        "+++ b/docs/issue-2400/reports/implementation.md\n"
        "+acceptance: python3 spawn.py watchdog — result: PASS\n"
        "+The rotation policy ran without error.\n"
    )
    result = rm.grade(body, diff, {})
    assert result["blocked"] is True, (
        "the ongoing-rotation claim has no before/after backlog count in "
        "the diff -- this rule would have refused it at landing, which is "
        "exactly the gap #2413 found live")


def _advisory(*verdicts):
    return [{"raw": f"c{i}", "verdict": v} for i, v in enumerate(verdicts)]


def t_summarize_all_unknown_is_not_the_pass_string():
    # issue #2510 — live-observed on issue #2479/PR #2493: 4 criteria, all
    # UNKNOWN, printed "게이트 통과 (4개 기준 채점, 차단 사유 없음)".
    result = {"empty_state": False, "blocking_reasons": [],
              "advisory": _advisory(rm.UNKNOWN, rm.UNKNOWN, rm.UNKNOWN, rm.UNKNOWN)}
    text, code = rm.summarize(result)
    assert code == 0
    assert "UNKNOWN" in text
    assert text != "게이트 통과 (4개 기준 채점, 차단 사유 없음)"
    assert not text.startswith("게이트 통과")


def t_summarize_at_least_one_met_and_unblocked_reads_unchanged():
    # issue #2510 acceptance "must not": when every criterion has a
    # settled verdict (no UNKNOWN) and at least one is met, with nothing
    # blocking, the summary is byte-for-byte unchanged from before the fix.
    result = {"empty_state": False, "blocking_reasons": [],
              "advisory": _advisory(rm.YES, rm.NO, rm.YES)}
    text, code = rm.summarize(result)
    assert code == 0
    assert text == "게이트 통과 (3개 기준 채점, 차단 사유 없음)"


def t_summarize_partial_unknown_reports_explicit_counts():
    result = {"empty_state": False, "blocking_reasons": [],
              "advisory": _advisory(rm.YES, rm.YES, rm.UNKNOWN, rm.NO)}
    text, code = rm.summarize(result)
    assert code == 0
    assert "met 2" in text and "unknown 1" in text and "blocked 0" in text
    assert not text.startswith("게이트 통과 (")


def t_summarize_all_no_without_unknown_also_avoids_pass_word():
    result = {"empty_state": False, "blocking_reasons": [],
              "advisory": _advisory(rm.NO, rm.NO)}
    text, code = rm.summarize(result)
    assert code == 0
    assert "met 0" in text and "unknown 0" in text


def t_summarize_blocked_still_refuses_with_individual_reasons():
    result = {"empty_state": False,
              "blocking_reasons": ["기준 'x'이 YES 로 채점됐지만 ..."],
              "advisory": _advisory(rm.YES)}
    text, code = rm.summarize(result)
    assert code == 1
    assert text.startswith("게이트 차단:")
    assert "기준 'x'이 YES" in text


def t_summarize_empty_advisory_not_blocked_is_not_all_unknown():
    # warrant-hunt finding 2026-08-26: not reachable via check()/grade()
    # (empty_state=False implies non-empty advisory), but summarize() is a
    # pure function callable directly with hand-built dicts — it must not
    # read a 0/0 vacuous match as "0 criteria, all UNKNOWN".
    result = {"empty_state": False, "blocking_reasons": [], "advisory": []}
    text, code = rm.summarize(result)
    assert code == 0
    assert "UNKNOWN" not in text
    assert not text.startswith("게이트 통과")


def t_summarize_empty_state_unchanged():
    result = {"empty_state": True, "reason": "테스트 사유"}
    text, code = rm.summarize(result)
    assert code == 0
    assert text == "채점 가능한 기준 없음 — 이건 통과가 아니라 별개의 결과다 (테스트 사유)"


def _run(fn):
    try:
        fn()
        print(f"ok  {fn.__name__}")
        return True
    except AssertionError as e:
        print(f"FAIL {fn.__name__}: {e}")
        return False


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    results = [_run(t) for t in tests]
    ok = all(results)
    print(f"{sum(results)}/{len(results)} passed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
