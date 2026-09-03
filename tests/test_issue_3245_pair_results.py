"""Tests for issue #3245 (R007 consumer-path pair results): the
multi-pair `--report` mode added to `scripts/consumer-path/
verify_manipulation.py`, and the trust-rooted dispatch/argv construction
added by `scripts/consumer-path/run_pair.py`.

Covers: the report's empty-state failure (no manifest anywhere -> says so,
exits nonzero, never a fabricated "0 pairs, all clean"), multi-pair
discovery and per-pair pass/exclude aggregation, the off arm's `skill-repo:`
source qualifier (never a stub -- issue #3245's must-not), and the
verification/cost collectors' fail-closed "None, not fabricated" shape
when their expected artifacts are absent.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CONSUMER_PATH_DIR = ROOT / "scripts" / "consumer-path"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prepare_arms = _load_module("prepare_arms", CONSUMER_PATH_DIR / "prepare_arms.py")
verify_manipulation = _load_module(
    "verify_manipulation", CONSUMER_PATH_DIR / "verify_manipulation.py")
run_pair = _load_module("run_pair", CONSUMER_PATH_DIR / "run_pair.py")


@pytest.fixture
def populated_skills_root(tmp_path):
    root = tmp_path / "skills-corpus"
    for name in ("skill-a", "my-skill"):
        (root / name).mkdir(parents=True)
        (root / name / "SKILL.md").write_text(
            f"---\nname: {name}\n---\nReal guidance body for {name}.\n")
    return root


def _write_pair(pair_dir: Path, skills_root: Path, skill_name: str,
                 tamper_manifest=None, write_transport=True,
                 transport_argv_ok=True):
    pair_dir.mkdir(parents=True, exist_ok=True)
    manifest, created_dirs = prepare_arms.build_manifest(
        skills_root, skill_name, "sonnet", "test-operator")
    if tamper_manifest:
        tamper_manifest(manifest)
    manifest_path = pair_dir / "manifest.json"
    text = prepare_arms.render_manifest_json(manifest)
    manifest_path.write_text(text, encoding="utf-8")
    digest = prepare_arms._sha256_bytes(manifest_path.read_bytes())
    (pair_dir / "manifest.json.sha256").write_text(digest + "\n")
    prepare_arms._cleanup(created_dirs)

    if write_transport:
        transport = run_pair.build_transport(
            manifest, skill_name, "sonnet", "task text",
            "/tmp/fake-repo", 101, 102)
        if not transport_argv_ok:
            transport["arms"]["on"]["argv"] = ["claude", "-p", "task"]
        (pair_dir / "transport.json").write_text(
            json.dumps(transport, indent=2), encoding="utf-8")
    return manifest


# --- run_pair.py: off arm carries the source qualifier, never a stub ----

def test_off_arm_skills_argument_carries_qualifier_not_a_stub():
    assert run_pair._skills_argument("my-skill", "on") == "my-skill"
    assert run_pair._skills_argument("my-skill", "off") == "skill-repo:my-skill"
    # The qualifier is a string on the --skills argument, not a directory
    # this module writes -- nothing under run_pair.py creates files for
    # the off arm's skills root (that remains prepare_arms.py's job, and
    # prepare_arms.py never creates one either).
    assert "stub" not in run_pair._skills_argument("my-skill", "off")


def test_spawn_command_is_byte_identical_except_skills_and_issue():
    argv_on = run_pair.spawn_command("s", "sonnet", "task", 1, "/repo", "on")
    argv_off = run_pair.spawn_command("s", "sonnet", "task", 2, "/repo", "off")
    diffs = [(a, b) for a, b in zip(argv_on, argv_off) if a != b]
    assert {a for a, b in diffs} == {"s", "1"}
    assert {b for a, b in diffs} == {"skill-repo:s", "2"}


def test_build_transport_env_matches_manifest_arms(populated_skills_root):
    manifest, created = prepare_arms.build_manifest(
        populated_skills_root, "my-skill", "sonnet", "op")
    prepare_arms._cleanup(created)
    transport = run_pair.build_transport(
        manifest, "my-skill", "sonnet", "task", "/repo", 19, 20)
    on_arm = [a for a in manifest["arms"] if a["arm"] == "on"][0]
    off_arm = [a for a in manifest["arms"] if a["arm"] == "off"][0]
    assert transport["arms"]["on"]["env"]["HOME"] == on_arm["home"]
    assert transport["arms"]["on"]["env"]["MUSTER_SKILL_REPO"] == on_arm["skills_root"]
    assert transport["arms"]["off"]["env"]["HOME"] == off_arm["home"]
    assert transport["arms"]["off"]["env"]["MUSTER_SKILL_REPO"] == off_arm["skills_root"]
    assert transport["arms"]["on"]["env"]["HOME"] != transport["arms"]["off"]["env"]["HOME"]


def test_build_transport_verifies_clean_against_prepare_arms_manifest(
        tmp_path, populated_skills_root):
    manifest = _write_pair(tmp_path / "pair", populated_skills_root, "my-skill")
    verdict = verify_manipulation.verify(
        tmp_path / "pair" / "manifest.json", tmp_path / "pair" / "transport.json")
    assert verdict["manipulation_held"] is True
    assert verdict["pair_excluded"] is False


# --- seed_arm_credentials: closes the fresh-HOME login gap without ------
# --- touching anything verify_manipulation.py cross-checks --------------
# Issue #3245 round 3: reproduced live that a fresh, empty
# `tempfile.mkdtemp()` HOME (prepare_arms.py's trust root) fails
# `spawn.py doctor()` with the exact "hooks do not fire headless" signature
# PR #3251 misdiagnosed as a CLI regression -- copying only
# `.claude/.credentials.json` into that same empty HOME flips the probe
# back to passing, no CLI change involved. See independent-verification-1/2
# on PR #3251 for the earlier, first-found version of this same result.

def test_seed_arm_credentials_copies_identical_bytes(tmp_path):
    source = tmp_path / "source-credentials.json"
    source.write_text('{"claudeAiOauth": {"accessToken": "tok"}}')
    home_on = tmp_path / "home-on"
    home_off = tmp_path / "home-off"
    home_on.mkdir()
    home_off.mkdir()
    result_on = run_pair.seed_arm_credentials(home_on, source=source)
    result_off = run_pair.seed_arm_credentials(home_off, source=source)
    assert result_on == {"seeded": True, "source": str(source)}
    assert result_off == {"seeded": True, "source": str(source)}
    dest_on = home_on / ".claude" / ".credentials.json"
    dest_off = home_off / ".claude" / ".credentials.json"
    assert dest_on.read_bytes() == source.read_bytes()
    assert dest_off.read_bytes() == source.read_bytes()


def test_seed_arm_credentials_missing_source_reports_not_seeded(tmp_path):
    result = run_pair.seed_arm_credentials(
        tmp_path / "home", source=tmp_path / "no-such-credentials.json")
    assert result["seeded"] is False
    assert "reason" in result and result["reason"]


def test_seed_arm_credentials_copy_oserror_reports_not_seeded_not_raised(
        tmp_path, monkeypatch):
    """silent-failure-audit: an OSError during the copy itself (not just a
    missing source) must be reported the same fail-closed way, never
    propagate as a bare traceback out of run_pair()'s dict comprehension."""
    source = tmp_path / "source-credentials.json"
    source.write_text('{"claudeAiOauth": {}}')
    home = tmp_path / "home"
    home.mkdir()

    def _boom(self, *a, **kw):
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_bytes", _boom)
    result = run_pair.seed_arm_credentials(home, source=source)
    assert result == {"seeded": False,
                       "reason": f"could not seed credential into "
                                 f"{home / '.claude' / '.credentials.json'}: "
                                 "disk full"}


def test_run_pair_fails_closed_when_operator_credential_missing(
        monkeypatch, tmp_path, populated_skills_root):
    """silent-failure-audit: a missing operator credential must exclude
    the pair with a stated reason, never silently dispatch an arm that
    would just fail later on "Not logged in" with a misleading message."""
    monkeypatch.setattr(
        run_pair, "seed_arm_credentials",
        lambda home, source=None: {
            "seeded": False, "reason": "no credential on this machine"})
    task_file = run_pair.TASKS_DIR / "01-study-groups.txt"
    assert task_file.is_file()
    monkeypatch.setenv("MUSTER_SKILL_REGISTRY_ROOT", str(populated_skills_root))
    result = run_pair.run_pair(
        "01-study-groups", "/tmp/fake-repo", "my-skill", "sonnet",
        19, 20, tmp_path / "out", 1800, True)
    assert result["status"] == "credential-seeding-failed"
    assert result["excluded_from_h2"] is True
    assert "no credential on this machine" in result["reason"]
    # No manifest/transport is left behind for a pair that never reached
    # the trust-rooted dispatch step.
    assert not (tmp_path / "out" / "manifest.json").exists()


def test_run_pair_success_path_builds_plan_shim_without_nameerror(
        monkeypatch, tmp_path, populated_skills_root):
    """Regression (issue #3245 round 4): `class _P: skill_name =
    skill_name` inside run_pair() was a self-referential class-body
    assignment -- Python resolves a name assigned within a class body via
    the (still-empty) class namespace, never falling back to the
    enclosing function's local `skill_name`, so the RHS always raised
    NameError. No pair before this round had ever reached this line
    (every prior real dispatch failed earlier, at watch or credential
    seeding), so the bug went undetected through three rounds. Exercises
    the full success path (both arms mocked as watched-to-completion)
    end to end."""
    monkeypatch.setenv("MUSTER_SKILL_REGISTRY_ROOT", str(populated_skills_root))

    def _fake_execute_arm(argv, env_override, repo, issue, arm_name,
                           watch_session, watch_timeout_s, confirm_real_spawn):
        return {"arm": arm_name, "issue": issue,
                "status": "watched-to-completion",
                "wall_clock_to_pr_open_s": 1.0, "dispatch_returncode": 0,
                "watch_returncode": 0}

    monkeypatch.setattr(run_pair, "execute_arm", _fake_execute_arm)
    monkeypatch.setattr(
        run_pair.rcp, "gate_pair_on_h1",
        lambda pair_id, workspace_on, workspace_off, **kw: {
            "pair_id": pair_id, "h1": {"differs": True},
            "h1_manipulation_ok": True, "excluded_from_h2": False,
            "exclusion_reason": None, "h2": {"stub": True}})
    monkeypatch.setattr(run_pair, "collect_verification_rounds",
                         lambda *a, **kw: {"measured": False})
    monkeypatch.setattr(run_pair, "collect_cost",
                         lambda *a, **kw: {"measured": False})

    result = run_pair.run_pair(
        "01-study-groups", "/tmp/fake-repo", "my-skill", "sonnet",
        19, 20, tmp_path / "out", 1800, True)
    assert result["h1_manipulation_ok"] is True
    assert result["h2"] == {"stub": True}


# --- fetch_deliverable_files: regression (issue #3245 round 7) ---------
#
# `rcp._default_deliverable_fetcher()` reads the arm's own PR *body*
# (`gh pr view <branch> --json body`) using a guessed branch name with no
# lease disambiguator. Round 3 and round 4 both scored that PR body and
# got a meaningless tie -- neither arm's brief lives there; it is a
# committed file under docs/issue-<n>/{specs,reports}/*.md, per every
# measurement issue's own acceptance check. `fetch_deliverable_files()`
# must fetch that file's real content off the discovered branch instead.

def test_deliverable_file_paths_filters_to_specs_and_reports(monkeypatch):
    def _fake_run(cmd, cwd, capture_output, text):
        assert cmd[:3] == ["gh", "pr", "view"]
        return subprocess.CompletedProcess(
            cmd, 0, stdout=json.dumps({"files": [
                {"path": "docs/issue-19/reports/skill-abc123.md"},
                {"path": "docs/issue-19/specs/some-brief.md"},
                {"path": "README.md"},
            ]}), stderr="")

    monkeypatch.setattr(run_pair.subprocess, "run", _fake_run)
    paths = run_pair._deliverable_file_paths("/repo", "issue-19/skill-abc123")
    assert paths == ["docs/issue-19/reports/skill-abc123.md",
                      "docs/issue-19/specs/some-brief.md"]


def test_deliverable_file_paths_empty_when_gh_fails(monkeypatch):
    def _fake_run(cmd, cwd, capture_output, text):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="not found")

    monkeypatch.setattr(run_pair.subprocess, "run", _fake_run)
    assert run_pair._deliverable_file_paths("/repo", "issue-19/skill") == []


def test_fetch_deliverable_files_returns_none_when_branch_undiscoverable(
        monkeypatch):
    monkeypatch.setattr(run_pair.rcp, "_discover_arm_branch",
                         lambda repo, issue: {"found": False, "branch": None})
    assert run_pair.fetch_deliverable_files("acme/repo", "/repo", 19) is None


def test_fetch_deliverable_files_reads_branch_file_content_not_pr_body(
        monkeypatch):
    monkeypatch.setattr(
        run_pair.rcp, "_discover_arm_branch",
        lambda repo, issue: {"found": True,
                              "branch": "issue-19/skill-abc123"})
    monkeypatch.setattr(
        run_pair, "_deliverable_file_paths",
        lambda local_repo, branch: ["docs/issue-19/reports/skill-abc123.md"])

    def _fake_content(local_repo, branch, path):
        assert branch == "issue-19/skill-abc123"
        assert path == "docs/issue-19/reports/skill-abc123.md"
        return "# the real brief body\n"

    monkeypatch.setattr(run_pair, "_file_content_from_branch", _fake_content)
    result = run_pair.fetch_deliverable_files("acme/repo", "/repo", 19)
    assert "the real brief body" in result
    assert "docs/issue-19/reports/skill-abc123.md" in result


def test_fetch_deliverable_files_none_when_no_deliverable_paths(monkeypatch):
    monkeypatch.setattr(
        run_pair.rcp, "_discover_arm_branch",
        lambda repo, issue: {"found": True, "branch": "issue-19/skill"})
    monkeypatch.setattr(run_pair, "_deliverable_file_paths",
                         lambda local_repo, branch: [])
    assert run_pair.fetch_deliverable_files("acme/repo", "/repo", 19) is None


# --- _github_slug_from_local_repo: regression (issue #3245 round 4) ----
#
# `run_pair()` passed its own `--repo` value (a local clone filesystem
# path, per this module's own CLI help text) straight through to
# `gate_pair_on_h1()` -> `_discover_arm_branch()`'s `gh pr list -R
# <repo>`, which requires an `owner/repo` slug, not a path. Live-
# reproduced on pair 1's first fresh round-4 dispatch: both arms reached
# `watched-to-completion` but H1 came back `unknown` because `gh pr list
# -R '/home/jwjung/study-companion'` failed outright ("expected the
# [HOST/]OWNER/REPO format") -- a real, successful arm reported as
# unobservable for a reason that had nothing to do with observability.

def test_github_slug_resolves_from_https_origin(monkeypatch):
    def _fake_run(cmd, capture_output, text, timeout):
        assert cmd == ["git", "-C", "/some/local/clone", "remote",
                        "get-url", "origin"]
        return subprocess.CompletedProcess(
            cmd, 0, stdout="https://github.com/JiwonJung94/study-companion.git\n",
            stderr="")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    assert run_pair._github_slug_from_local_repo("/some/local/clone") == \
        "JiwonJung94/study-companion"


def test_github_slug_resolves_from_ssh_origin(monkeypatch):
    def _fake_run(cmd, capture_output, text, timeout):
        return subprocess.CompletedProcess(
            cmd, 0, stdout="git@github.com:acme/sandbox.git\n", stderr="")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    assert run_pair._github_slug_from_local_repo("/some/clone") == "acme/sandbox"


def test_github_slug_returns_none_not_fabricated_when_remote_lookup_fails(
        monkeypatch):
    def _fake_run(cmd, capture_output, text, timeout):
        return subprocess.CompletedProcess(cmd, 128, stdout="", stderr="not a git repo")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    assert run_pair._github_slug_from_local_repo("/not/a/repo") is None


# --- _rebase_workspace_to_arm_home: regression (issue #3245 round 4) ---
#
# `rcp.arm_workspace_dir()`'s guess is computed from THIS orchestrating
# process's own HOME, never the dispatched arm's isolated HOME -- so its
# guessed workspace can never point at the arm's real one for a trust-
# rooted (isolated-HOME) dispatch. Live-reproduced on pair 1's first
# fresh round-4 dispatch, after the `-R`-vs-local-path slug fix above
# was already in place: H1 still came back `unknown`, this time because
# `collect_skill_invocation()`'s own discovery-fallback reconstruction
# rebuilds the real workspace under `workspace.parent` -- which was still
# this orchestrator's own `$MUSTER_WORKSPACE_ROOT`, not the arm's
# isolated HOME's `.tokenmaxxxer/work`, where the session log actually
# was.

def test_rebase_workspace_to_arm_home_swaps_home_prefix():
    guessed = Path("/home/orchestrator/.tokenmaxxxer/work/"
                    "study-companion-issue-19-my-skill")
    result = run_pair._rebase_workspace_to_arm_home(
        guessed, "/tmp/consumer-path-on-home-zflb8501")
    assert result == Path("/tmp/consumer-path-on-home-zflb8501/"
                           ".tokenmaxxxer/work/"
                           "study-companion-issue-19-my-skill")


def test_rebase_workspace_to_arm_home_passes_through_none():
    assert run_pair._rebase_workspace_to_arm_home(None, "/tmp/home") is None


# --- collect_verification_rounds / collect_cost: fail-closed, not fabricated

def test_collect_verification_rounds_missing_pr_returns_none(tmp_path):
    result = run_pair.collect_verification_rounds(
        str(tmp_path), 999999, "no-such-skill")
    assert result["verification_rounds"] is None
    assert result["measured"] is False
    assert result["reason"]


def test_collect_cost_missing_ledger_returns_none(monkeypatch, tmp_path):
    monkeypatch.setattr(run_pair, "ROOT", tmp_path)
    result = run_pair.collect_cost(str(tmp_path), 1, "skill")
    assert result["cost_usd"] is None
    assert result["measured"] is False


def test_collect_cost_sums_matching_ledger_entries(monkeypatch, tmp_path):
    monkeypatch.setattr(run_pair, "ROOT", tmp_path)
    (tmp_path / "runs").mkdir()
    ledger = tmp_path / "runs" / "ledger.jsonl"
    ledger.write_text(
        json.dumps({"issue": 19, "skill": "s", "cost_usd": 1.25}) + "\n"
        + json.dumps({"issue": 19, "skill": "s", "cost_usd": 0.75}) + "\n"
        + json.dumps({"issue": 20, "skill": "s", "cost_usd": 9.0}) + "\n")
    result = run_pair.collect_cost(str(tmp_path), 19, "s")
    assert result["measured"] is True
    assert result["cost_usd"] == pytest.approx(2.0)


# --- verify_manipulation.py --report: multi-pair aggregation -----------

def test_report_empty_state_says_so_and_would_exit_nonzero(tmp_path):
    empty_root = tmp_path / "nothing-here"
    result = verify_manipulation.report(empty_root)
    assert result["status"] == "no-manifests-found"
    assert result["pairs_found"] == 0
    assert "reason" in result and result["reason"]


def test_report_cli_empty_state_exits_nonzero(tmp_path):
    r = subprocess.run(
        [sys.executable, str(CONSUMER_PATH_DIR / "verify_manipulation.py"),
         "--report", "--root", str(tmp_path / "empty")],
        capture_output=True, text=True)
    assert r.returncode != 0
    payload = json.loads(r.stdout)
    assert payload["status"] == "no-manifests-found"


def test_report_finds_multiple_pair_dirs(tmp_path, populated_skills_root):
    _write_pair(tmp_path / "pair-a", populated_skills_root, "skill-a")
    _write_pair(tmp_path / "pair-b", populated_skills_root, "skill-a")
    result = verify_manipulation.report(tmp_path)
    assert result["pairs_found"] == 2
    assert len(result["pairs_included"]) == 2
    assert result["pairs_excluded"] == []


def test_report_excludes_pair_with_bad_argv_and_keeps_others(
        tmp_path, populated_skills_root):
    _write_pair(tmp_path / "pair-good", populated_skills_root, "skill-a")
    _write_pair(tmp_path / "pair-bad", populated_skills_root, "skill-a",
                transport_argv_ok=False)
    result = verify_manipulation.report(tmp_path)
    assert result["pairs_found"] == 2
    assert len(result["pairs_included"]) == 1
    assert len(result["pairs_excluded"]) == 1
    excluded_dir = result["pairs_excluded"][0]["pair_dir"]
    assert excluded_dir.endswith("pair-bad")
    assert "spawn.py" in result["pairs_excluded"][0]["reason"]


def test_report_excludes_pair_missing_transport(tmp_path, populated_skills_root):
    _write_pair(tmp_path / "pair-no-transport", populated_skills_root,
                "skill-a", write_transport=False)
    result = verify_manipulation.report(tmp_path)
    assert result["pairs_found"] == 1
    assert result["pairs_included"] == []
    assert len(result["pairs_excluded"]) == 1
    assert "transport" in result["pairs_excluded"][0]["reason"]


def test_report_cli_exits_zero_when_all_pairs_verify(
        tmp_path, populated_skills_root):
    _write_pair(tmp_path / "pair-a", populated_skills_root, "skill-a")
    r = subprocess.run(
        [sys.executable, str(CONSUMER_PATH_DIR / "verify_manipulation.py"),
         "--report", "--root", str(tmp_path)],
        capture_output=True, text=True)
    assert r.returncode == 0
    payload = json.loads(r.stdout)
    assert payload["pairs_found"] == 1
    assert payload["pairs_excluded"] == []


def test_no_pair_reported_as_scored_without_passing_manipulation_check(
        tmp_path, populated_skills_root):
    """issue #3245's must-not: every pair reported as scored has a
    passing manipulation check recorded against it. Simulates a results
    aggregation step reading `report()`'s output and asserts it can only
    ever treat `pairs_included` (manipulation_held=True) pairs as scored
    -- `pairs_excluded` entries carry no manipulation_held=True verdict
    to be misread as a pass."""
    _write_pair(tmp_path / "pair-good", populated_skills_root, "skill-a")
    _write_pair(tmp_path / "pair-bad", populated_skills_root, "skill-a",
                transport_argv_ok=False)
    result = verify_manipulation.report(tmp_path)
    for pair in result["pairs"]:
        if pair["pair_dir"] in result["pairs_included"]:
            assert pair["manipulation_held"] is True
        else:
            assert pair.get("manipulation_held") is not True
