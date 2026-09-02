"""Issue #3081 Acceptance -- `watchdog.requirement_drift`'s cache
(`requirement_drift_cache.json`) is one orchestrator-scoped file shared
across every repo an orchestrator sweeps (issue #2240, unchanged by this
fix). What was missing is a repo dimension on each entry: a sweep read the
whole file back without checking whose entries they were, so one repo's
cached issues/PRs printed under another repo's report, and a failed lookup
for an entry that belonged to a *different* repo was read as "transient
failure, retain" instead of "wrong repo, unresolved".

Test derivation (test-derivation skill): the observable behavior is a
decision table over three conditions -- (a) does a cache entry's repo match
the sweeping repo, (b) does this tick's lookup for that number succeed or
fail, (c) does the entry predate this fix (no `repo` key at all). This file
covers the feasible columns:

  | entry repo == sweep repo | lookup this tick | entry has `repo` key | outcome                         | test                                            |
  |---------------------------|-------------------|------------------------|----------------------------------|--------------------------------------------------|
  | yes                       | n/a (full mode)   | yes                    | full mode merges, doesn't erase  | test_full_mode_merges_other_repos_entries        |
  | no                        | n/a (reuse pass)  | yes                    | excluded from report             | test_delta_reuse_pass_excludes_other_repo        |
  | yes                       | n/a (reuse pass)  | yes                    | included in report               | test_delta_reuse_pass_includes_own_repo          |
  | yes                       | failed            | yes                    | retained (existing behavior)     | test_retention_when_repo_matches                 |
  | no                        | failed            | yes                    | NOT retained -> unknown          | test_no_retention_when_entry_is_another_repos    |
  | --                        | failed            | no (legacy)            | treated as no prior -> unknown   | test_legacy_entry_without_repo_key_not_retained  |

Run:
  python3 -m pytest tests/test_requirement_drift_repo_scope.py -q
"""
from __future__ import annotations
import json
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

REPO_A = "octo/on-the-record"
REPO_B = "octo/study-companion"


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    # issue #2240: orchestrator cross-tick cache/noise state is anchored to
    # STATE_ROOT, not `root` -- isolate it per test like
    # test_watchdog_heartbeat_noise.py / test_requirement_drift_third_state_2980.py do.
    monkeypatch.setattr(state_paths, "STATE_ROOT", tmp_path / "state")


@pytest.fixture()
def repos(tmp_path, monkeypatch):
    root_a = tmp_path / "repo-a"
    root_b = tmp_path / "repo-b"
    for root in (root_a, root_b):
        (root / "docs" / "specs").mkdir(parents=True)
        (root / "docs" / "specs" / "requirement-digest.md").write_text(
            "- R001: something [open] (source: #1)\n")

    def fake_repo_slug(root):
        return REPO_A if root == root_a else REPO_B

    monkeypatch.setattr(spawn, "_repo_slug", fake_repo_slug)
    return root_a, root_b


def _item(number, body="cites nothing"):
    return {"number": number, "title": "", "body": body, "state": "open"}


class TestFullModeMerges:
    """Full mode is authoritative for the sweeping repo's own open set, but
    must merge into the shared cache rather than replace it -- otherwise a
    full sweep of repo B silently erases repo A's memory."""

    def test_full_mode_merges_other_repos_entries(self, repos):
        root_a, root_b = repos

        # Seed repo A's entry via a genuine delta-mode sweep.
        with mock.patch.object(spawn, "_fetch_issue_or_pr_via_cache",
                                return_value=_item(3048)):
            spawn.requirement_drift(root_a, changed_numbers={3048})

        # Repo B does a full-mode sweep (no changed_numbers) with an empty
        # open set of its own.
        empty_board = {"issues": {}, "prs": {}}
        with mock.patch.object(spawn, "_board_read",
                                return_value=(empty_board, {"source": "live"})):
            spawn.requirement_drift(root_b)

        cache_path = spawn._requirement_drift_cache_path(root_a)
        cache = json.loads(cache_path.read_text())
        key = spawn._drift_cache_key(REPO_A, 3048)
        assert key in cache, (
            "repo B's full-mode sweep erased repo A's cache entry -- full "
            "mode must merge into the shared cache, not replace it "
            f"outright. cache contents: {cache!r}")
        assert cache[key]["repo"] == REPO_A


class TestDeltaReusePassFiltersByRepo:
    """The reuse pass (delta mode, numbers not re-fetched this tick) is the
    report-time filter: it must only feed back this sweep's own repo's
    entries."""

    def test_delta_reuse_pass_excludes_other_repo(self, repos, capsys):
        root_a, root_b = repos
        with mock.patch.object(spawn, "_fetch_issue_or_pr_via_cache",
                                return_value=_item(3048)):
            spawn.requirement_drift(root_a, changed_numbers={3048})
        capsys.readouterr()

        with mock.patch.object(spawn, "_fetch_issue_or_pr_via_cache",
                                return_value=_item(77)):
            spawn.requirement_drift(root_b, changed_numbers={77})
        out = capsys.readouterr().out

        assert "3048" not in out, (
            "repo A's cached entry leaked into repo B's sweep output "
            f"(issue #3081): {out!r}")

    def test_delta_reuse_pass_includes_own_repo(self, repos, capsys):
        root_a, _root_b = repos
        # Tick 1: cache #3048 for repo A.
        with mock.patch.object(spawn, "_fetch_issue_or_pr_via_cache",
                                return_value=_item(3048)):
            spawn.requirement_drift(root_a, changed_numbers={3048})
        capsys.readouterr()

        # Tick 2: a different number changes; #3048 is only reachable via
        # the reuse pass, no other repo involved -- must still surface.
        with mock.patch.object(spawn, "_fetch_issue_or_pr_via_cache",
                                return_value=_item(99)):
            spawn.requirement_drift(root_a, changed_numbers={99})
        out = capsys.readouterr().out

        assert "3048" in out, (
            "a sweep must not suppress its own repo's genuine cached "
            f"drift entries: {out!r}")


class TestRetentionRepoScoped:
    """A failed lookup retains the previous verdict only when the cached
    entry actually belongs to the sweeping repo. A mismatch (the entry
    belongs to a different repo) must fall through to the existing
    no-genuine-prior / unknown path instead of being silently retained."""

    def test_retention_when_repo_matches(self, repos, capsys):
        root_a, _root_b = repos
        with mock.patch.object(spawn, "_fetch_issue_or_pr_via_cache",
                                return_value=_item(2960)):
            spawn.requirement_drift(root_a, changed_numbers={2960})
        capsys.readouterr()

        with mock.patch.object(spawn, "_fetch_issue_or_pr_via_cache",
                                return_value=None):
            spawn.requirement_drift(root_a, changed_numbers={2960})
        out = capsys.readouterr().out

        assert "requirement-drift-cache-retained:" in out
        assert "2960" in out

    def test_no_retention_when_entry_is_another_repos(self, repos, capsys):
        root_a, root_b = repos
        # Repo A caches #3048 (its own genuine entry).
        with mock.patch.object(spawn, "_fetch_issue_or_pr_via_cache",
                                return_value=_item(3048)):
            spawn.requirement_drift(root_a, changed_numbers={3048})
        capsys.readouterr()

        # Repo B's sweep tries to (re)resolve the same number and its
        # lookup fails -- it fails precisely because #3048 is not repo B's
        # PR. This must not be reported as a retained verdict: repo B has
        # no genuine prior for #3048 at all.
        with mock.patch.object(spawn, "_fetch_issue_or_pr_via_cache",
                                return_value=None):
            spawn.requirement_drift(root_b, changed_numbers={3048})
        out = capsys.readouterr().out

        assert "requirement-drift-cache-retained:" not in out, (
            "a lookup failure for a number that only exists in another "
            f"repo's cache must not be reported as retained: {out!r}")
        assert "requirement-drift-unknown:" in out
        assert "3048" in out


class TestLegacyCacheEntries:
    """Entries written before this fix carry no `repo` key at all and
    cannot be attributed after the fact -- they must be dropped rather than
    keep matching every repo's lookups forever."""

    def test_legacy_entry_without_repo_key_not_retained(self, repos, capsys):
        root_a, _root_b = repos
        cache_path = spawn._requirement_drift_cache_path(root_a)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps({
            "3048": {"title": "", "body": "cites nothing",
                     "cached_at": "2020-01-01T00:00:00+00:00"},
        }))

        with mock.patch.object(spawn, "_fetch_issue_or_pr_via_cache",
                                return_value=None):
            spawn.requirement_drift(root_a, changed_numbers={3048})
        out = capsys.readouterr().out

        assert "requirement-drift-cache-retained:" not in out, (
            "a pre-fix, unattributed cache entry must not be silently "
            f"retained as though it were this repo's genuine prior: {out!r}")
        assert "requirement-drift-unknown:" in out

        # The legacy entry must not survive being loaded and re-saved.
        cache = json.loads(cache_path.read_text())
        assert "3048" not in cache
