"""Issue #2980 Acceptance — `spawn.requirement_drift`/`watchdog.requirement_drift`
must not report a failed lookup in the same channel/shape as a reached
verdict, and must not silently misrepresent what a retained-on-failure
cached entry is (or a never-cached subject isn't).

Test derivation (test-derivation skill, equivalence-partitioning on the
lookup outcome for a subject/number this tick cares about): the function's
observable states partition into four classes, one per test below plus the
untouched fresh-verdict path already covered by other tests:
  1. total lookup failure (board/all numbers unreachable) -> its own state,
     never printed under the `requirement-drift:` verdict channel, and
     never resolved as a pass (no unmentioned_live line) or a violation
     (no unreferenced_open line).
  2. a changed number whose fetch failed but has a genuine prior cache
     entry -> reported as retained, naming when that prior was observed;
     never presented as a fresh judgment (distinct tag from a computed
     verdict line).
  3. a changed number whose fetch failed and has no prior cache entry (a
     newly filed subject) -> reported as unknown, never as "retained".
  4. empty state (no failed lookups at all) -> none of the above lines
     print; covered inline in each test via the success-tick assertion.

  python3 -m pytest tests/test_requirement_drift_third_state_2980.py
  python3 -m pytest tests/ -k requirement_drift_lookup_failure_state -q
  python3 -m pytest tests/ -k requirement_drift_cached_verdict_marked -q
  python3 -m pytest tests/ -k requirement_drift_no_prior_reports_unknown -q
"""
from __future__ import annotations
import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "gates"))
sys.path.insert(0, str(ROOT))

import state_paths  # noqa: E402
import spawn  # noqa: E402
import watchdog  # noqa: E402

watchdog._sp = spawn


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    # issue #2240: orchestrator cross-tick cache/noise state is anchored to
    # STATE_ROOT, not `root` -- isolate it per test like
    # test_watchdog_heartbeat_noise.py does.
    monkeypatch.setattr(state_paths, "STATE_ROOT", tmp_path / "state")


@pytest.fixture()
def board_repo(tmp_path):
    root = tmp_path / "repo"
    (root / "docs" / "specs").mkdir(parents=True)
    (root / "docs" / "specs" / "requirement-digest.md").write_text(
        "- R001: something [open] (source: #1)\n")
    return root


def _item(number, body=""):
    return {"number": number, "title": "", "body": body, "state": "open"}


class TestLookupFailureState:
    """Acceptance 1: a lookup failure is reported as its own state,
    distinct from a reached verdict, and never resolved as a pass or a
    violation."""

    def test_requirement_drift_lookup_failure_state(self, board_repo, capsys):
        with mock.patch.object(spawn, "_board_read", return_value=(None, {"source": None})):
            for _ in range(watchdog.WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD):
                spawn.requirement_drift(board_repo)
        out = capsys.readouterr().out

        # own channel: the failure line carries its own tag, never the
        # verdict-line tag `requirement-drift:` (a real verdict line looks
        # like "requirement-drift: 요구 R001 -- ...").
        assert "requirement-drift-lookup-failed:" in out
        assert "requirement-drift: " not in out
        # must not: never resolved as a pass (no "인용되지 않는다" verdict
        # text) or a violation (no unreferenced-open line) -- the failure
        # short-circuits before any verdict is computed at all.
        assert "인용되지 않는다" not in out
        assert "전혀 인용하지 않는" not in out

    def test_requirement_drift_lookup_failure_state_empty_when_no_failure(
            self, board_repo, capsys):
        empty_board = {"issues": {}, "prs": {}}
        with mock.patch.object(spawn, "_board_read",
                                return_value=(empty_board, {"source": "live"})):
            spawn.requirement_drift(board_repo)
        out = capsys.readouterr().out
        assert "requirement-drift-lookup-failed:" not in out


class TestCachedVerdictMarked:
    """Acceptance 2: a retained cached verdict is marked as retained,
    names when it was observed, and is never presented as a fresh
    judgment."""

    def test_requirement_drift_cached_verdict_marked(self, board_repo, capsys):
        # Tick 1 (delta mode): #2960 fetched successfully -> cached with an
        # observation timestamp, and used in the verdict this tick.
        with mock.patch.object(spawn, "_fetch_issue_or_pr_via_cache",
                                return_value=_item(2960, "cites nothing")):
            spawn.requirement_drift(board_repo, changed_numbers={2960})
        capsys.readouterr()

        # Tick 2: #2960 changed again but this time its fetch fails -- it
        # has a genuine prior (tick 1's cache entry).
        with mock.patch.object(spawn, "_fetch_issue_or_pr_via_cache",
                                return_value=None):
            spawn.requirement_drift(board_repo, changed_numbers={2960})
        out = capsys.readouterr().out

        assert "requirement-drift-cache-retained:" in out
        assert "2960" in out
        assert "관측:" in out
        # the observation marker must carry an actual timestamp, not the
        # placeholder used when no prior observation time is on record.
        assert "관측: unknown" not in out
        # never presented as a fresh judgment: not the plain unmarked
        # "이전 캐시 판정 유지" wording from before this fix, printed under
        # the verdict channel.
        assert "[watchdog] requirement-drift: 조회 실패" not in out

    def test_requirement_drift_cached_verdict_retention_not_dropped(
            self, board_repo, capsys):
        # must-not: retention itself (a genuine prior still counting toward
        # this tick's verdict) must not stop just because the marker was
        # added -- the defect being fixed is the missing marker, not the
        # retention. #2960's cached body ("cites R001") should still count
        # toward R001 being mentioned even on the tick its refetch fails.
        (board_repo / "docs" / "specs" / "requirement-digest.md").write_text(
            "- R001: something [open] (source: #1)\n")
        with mock.patch.object(spawn, "_fetch_issue_or_pr_via_cache",
                                return_value=_item(2960, "cites R001")):
            spawn.requirement_drift(board_repo, changed_numbers={2960})
        capsys.readouterr()

        with mock.patch.object(spawn, "_fetch_issue_or_pr_via_cache",
                                return_value=None):
            spawn.requirement_drift(board_repo, changed_numbers={2960})
        out = capsys.readouterr().out

        # R001 is still cited (via the retained cached body), so it must
        # not be reported as an unmentioned live requirement.
        assert "요구 R001" not in out


class TestNoPriorReportsUnknown:
    """Acceptance 3: a subject with no prior verdict reports unknown
    rather than retaining a verdict it never had."""

    def test_requirement_drift_no_prior_reports_unknown(self, board_repo, capsys):
        def _fetch(root, num):
            if num == 3099:
                return None  # never-before-seen subject, fetch fails
            return _item(num, "cites nothing")

        with mock.patch.object(spawn, "_fetch_issue_or_pr_via_cache",
                                side_effect=_fetch):
            spawn.requirement_drift(board_repo, changed_numbers={3099, 4000})
        out = capsys.readouterr().out

        assert "requirement-drift-unknown:" in out
        assert "3099" in out
        # must not retain a verdict it never had -- no "cache-retained"
        # line for the never-cached number, and no claim of prior verdict.
        assert "requirement-drift-cache-retained:" not in out
        assert "이전 캐시 판정 유지" not in out

    def test_requirement_drift_no_prior_reports_unknown_empty_when_all_succeed(
            self, board_repo, capsys):
        with mock.patch.object(spawn, "_fetch_issue_or_pr_via_cache",
                                return_value=_item(4000, "cites nothing")):
            spawn.requirement_drift(board_repo, changed_numbers={4000})
        out = capsys.readouterr().out
        assert "requirement-drift-unknown:" not in out
