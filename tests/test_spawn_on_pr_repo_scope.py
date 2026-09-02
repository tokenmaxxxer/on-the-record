"""Issue #3095 Acceptance -- `gates/spawn_on_pr.py`'s park state
(`spawn_on_pr_parked.json`) is one orchestrator-scoped file shared across
every repo an orchestrator sweeps (issue #2240, unchanged by this fix).
Identical shape to #3081's requirement-drift cache leak (PR #3084): a
`parked=True` entry read back with no per-repo filter, so a subject parked
while sweeping one repo printed as `waiting-for-human` on a different
repo's report too -- even naming a subject/issue that repo doesn't have
(the live symptom: `spawn-on-pr: waiting-for-human 1건: ['issue-3059']`
printed on a repo where issue-3059 doesn't exist and is already closed
elsewhere).

Test derivation (test-derivation skill): the observable behavior is a
decision table over two conditions -- (a) does a park-state entry's `repo`
match the sweeping repo, (b) does this tick's own recheck find the subject
still blocked or newly unblocked. This file covers the feasible columns:

  | entry repo == sweep repo | this tick's blocked signal | outcome                          | test                                       |
  |---------------------------|------------------------------|-----------------------------------|---------------------------------------------|
  | yes                       | still blocked                | retained -- stays parked          | test_retention_when_repo_matches            |
  | no                        | still blocked (foreign)      | NOT retained -- evicts, spawns    | test_no_retention_when_entry_is_another_repos |
  | yes                       | n/a (report-time read)       | included in own repo's report     | test_parked_report_includes_own_repo        |
  | no                        | n/a (report-time read)       | excluded from other repo's report | test_parked_report_excludes_other_repo      |
  | both repos parked         | n/a                          | reports not byte-identical        | test_parked_report_not_identical_across_repos |
  | -- (legacy, no repo key)  | n/a (report-time read)       | excluded from a resolvable repo's report | test_legacy_entry_without_repo_key_excluded_from_resolvable_repo |

Run:
  python3 -m pytest tests/test_spawn_on_pr_repo_scope.py -q
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

import spawn  # noqa: E402
import spawn_on_pr  # noqa: E402

REPO_A = "octo/on-the-record"
REPO_B = "octo/study-companion"
SUBJECT = "issue-3059"  # issue #3095's live repro: a repo-local issue number


@pytest.fixture()
def repos(tmp_path, monkeypatch):
    root_a = tmp_path / "repo-a"
    root_b = tmp_path / "repo-b"
    root_a.mkdir()
    root_b.mkdir()
    park_path = tmp_path / "spawn_on_pr_parked.json"  # one shared file, issue #2240

    def fake_repo_slug(root):
        return REPO_A if root == root_a else REPO_B

    monkeypatch.setattr(spawn, "_repo_slug", fake_repo_slug)
    monkeypatch.setattr(spawn_on_pr, "_park_state_path", lambda root: park_path)
    return root_a, root_b, park_path


def _seed(park_path: Path, entries: dict) -> None:
    park_path.write_text(json.dumps(entries))


def _wire(monkeypatch, *, missing: dict, blocked: bool):
    """Monkeypatch every gh/git/spawn boundary spawn_missing_for_pr()
    touches (gates/test_spawn_on_pr.py's idiom), leaving the
    park/ceiling/repo-attribution logic itself real."""
    monkeypatch.setattr(spawn_on_pr, "missing_verification",
                         lambda root, issue_states=None, pr_index=None: dict(missing))
    monkeypatch.setattr(spawn_on_pr, "subject_deliverable_branch",
                         lambda root, subject, pr_index: f"{subject}/impl")
    monkeypatch.setattr(spawn_on_pr, "_pr_number_for_branch",
                         lambda root, branch, pr_index: 1)
    monkeypatch.setattr(spawn_on_pr, "resolve_live_base", lambda root: "deadbeef")
    monkeypatch.setattr(spawn_on_pr, "is_approval_blocked",
                         lambda root, issue, skill: blocked)
    monkeypatch.setattr(spawn_on_pr.spawn, "roster_register", lambda *a, **k: None)
    monkeypatch.setattr(spawn_on_pr.spawn, "_spawn_one", lambda *a, **k: None)
    monkeypatch.setattr(spawn_on_pr.spawn, "ledger_write", lambda entry: None)


class TestParkedReportFiltersByRepo:
    """`parked_report()` is the report-time filter (watchdog's
    `waiting-for-human` line): it must only surface this root's own
    repo's parked subjects."""

    def test_parked_report_includes_own_repo(self, repos):
        root_a, _root_b, park_path = repos
        _seed(park_path, {
            SUBJECT: {"blocked": True, "pr_number": 1, "parked": True,
                      "attempts": 1, "repo": REPO_A},
        })
        assert spawn_on_pr.parked_report(root_a) == [SUBJECT]

    def test_parked_report_excludes_other_repo(self, repos):
        root_a, root_b, park_path = repos
        _seed(park_path, {
            SUBJECT: {"blocked": True, "pr_number": 1, "parked": True,
                      "attempts": 1, "repo": REPO_A},
        })
        assert spawn_on_pr.parked_report(root_b) == [], (
            f"repo A's parked subject {SUBJECT!r} leaked into repo B's "
            "report, which never parked it (issue #3095).")

    def test_parked_report_not_identical_across_repos(self, repos):
        root_a, root_b, park_path = repos
        _seed(park_path, {
            SUBJECT: {"blocked": True, "pr_number": 1, "parked": True,
                      "attempts": 1, "repo": REPO_A},
            "issue-42": {"blocked": True, "pr_number": 2, "parked": True,
                         "attempts": 1, "repo": REPO_B},
        })
        out_a = spawn_on_pr.parked_report(root_a)
        out_b = spawn_on_pr.parked_report(root_b)
        assert out_a == [SUBJECT]
        assert out_b == ["issue-42"]
        assert out_a != out_b, (
            "repo A's and repo B's parked reports are byte-identical -- "
            "each board printing the same union instead of its own "
            f"repo's subjects: {out_a!r} == {out_b!r}")


class TestRetentionRepoScoped:
    """A subject's park/attempts history is retained across ticks only
    when the prior entry actually belongs to the sweeping repo. A
    same-named subject whose only park-state entry belongs to a
    *different* repo must evict -- treated as a fresh candidate, not a
    genuine prior for this repo -- instead of silently inheriting another
    repo's blocked/attempts history."""

    def test_retention_when_repo_matches(self, repos, monkeypatch, capsys):
        root_a, _root_b, park_path = repos
        _seed(park_path, {
            SUBJECT: {"blocked": True, "pr_number": 1, "parked": True,
                      "attempts": 1, "repo": REPO_A},
        })
        _wire(monkeypatch, missing={SUBJECT: 1}, blocked=True)

        pairs = spawn_on_pr.spawn_missing_for_pr(
            root_a, cwd=str(root_a), dry_run=False,
            backoff_state={"sweeps": {}, "recheck": {}})

        assert pairs == [], "still-blocked own-repo subject must stay parked, not spawn"
        state = json.loads(park_path.read_text())
        assert state[SUBJECT]["parked"] is True
        assert state[SUBJECT]["repo"] == REPO_A
        assert spawn_on_pr.parked_report(root_a) == [SUBJECT]

    def test_no_retention_when_entry_is_another_repos(self, repos, monkeypatch):
        root_a, root_b, park_path = repos
        # Repo B's own genuine, deeply-attempted park history for a
        # subject that happens to share repo A's subject name (issue
        # numbers are repo-local -- a collision is plausible).
        _seed(park_path, {
            SUBJECT: {"blocked": True, "pr_number": 1, "parked": True,
                      "attempts": 5, "repo": REPO_B},
        })
        _wire(monkeypatch, missing={SUBJECT: 1}, blocked=True)

        # Repo A sees the same-named subject for the first time from its
        # own perspective -- it must not inherit repo B's blocked/attempts
        # history and must proceed to spawn instead of parking.
        pairs = spawn_on_pr.spawn_missing_for_pr(
            root_a, cwd=str(root_a), dry_run=False,
            backoff_state={"sweeps": {}, "recheck": {}})

        assert pairs != [], (
            "repo A inherited repo B's park/attempts history for the "
            f"same-named subject {SUBJECT!r} instead of evicting it as a "
            "foreign-repo entry (issue #3095 retention split).")
        state = json.loads(park_path.read_text())
        assert state[SUBJECT]["repo"] == REPO_A
        assert state[SUBJECT]["attempts"] == 1, (
            "attempts must restart from repo A's own history (0), not "
            "continue from repo B's unrelated count (5)")

        # Repo A's own report reflects what its own tick just did (a
        # spawn, not a park) -- the eviction did not cause a phantom park.
        assert spawn_on_pr.parked_report(root_a) == [], (
            "repo A's own tick just spawned this subject, so it must not "
            "report as parked yet")


class TestLegacyEntries:
    """Entries written before this fix carry no `repo` key at all. Unlike
    #3081's cache fix, load_park_state() does not drop them at load (kept
    to stay backward-compatible with gates/test_spawn_on_pr.py's existing
    bare-subject-key, no-`repo`-field fixtures) -- but a legacy entry must
    still not surface in a *resolvable*-slug repo's report, since
    `entry.get("repo")` (None) never equals a real slug string."""

    def test_legacy_entry_without_repo_key_excluded_from_resolvable_repo(self, repos):
        root_a, _root_b, park_path = repos
        _seed(park_path, {
            SUBJECT: {"blocked": True, "pr_number": 1, "parked": True,
                      "attempts": 1},  # no "repo" key -- pre-fix shape
        })
        assert spawn_on_pr.parked_report(root_a) == [], (
            "a legacy entry with no repo attribution must not be read "
            "back as though it belonged to a repo whose slug actually "
            f"resolves: {spawn_on_pr.parked_report(root_a)!r}")
