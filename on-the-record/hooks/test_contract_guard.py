"""Tests for contract-guard.sh target-repo resolution (issue #443).

Invokes contract-guard.sh as a subprocess with CG_PAYLOAD set, and a fake
`gh` shim on PATH that resolves canned fixtures by repo — either from a
`-R owner/repo` flag on the argv, or from the subprocess's own cwd (mirrors
how the real hook now calls `gh` with cwd=<target> for the `cd &&` form).
"""
import json
import os
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "contract-guard.sh"

FAKE_GH = """#!/usr/bin/env python3
import json, os, sys

fixtures = json.load(open(os.environ["GH_FIXTURES"]))
cwd_map = fixtures.get("cwd_map", {})
argv = sys.argv[1:]

repo = None
for i, a in enumerate(argv):
    if a in ("-R", "--repo") and i + 1 < len(argv):
        repo = argv[i + 1]
    elif a.startswith("--repo="):
        repo = a.split("=", 1)[1]
if repo is None:
    repo = cwd_map.get(os.getcwd(), cwd_map.get("__default__"))

data = fixtures.get("repos", {}).get(repo)
if data is None:
    sys.exit(1)

if argv[:2] == ["pr", "view"]:
    print(json.dumps({
        "body": data["pr_body"],
        "number": int(argv[2]),
        "commits": data.get("commits", []),
        "files": data.get("files", []),
    }))
elif argv[:2] == ["issue", "view"]:
    print(json.dumps(data.get("issue_comments", [])))
elif argv[:2] == ["pr", "edit"]:
    body_idx = argv.index("--body") + 1
    new_body = argv[body_idx]
    log_path = os.environ.get("GH_EDIT_LOG")
    if log_path:
        calls = json.loads(open(log_path).read()) if os.path.exists(log_path) else []
        calls.append({"repo": repo, "pr": argv[2], "body": new_body})
        open(log_path, "w").write(json.dumps(calls))
    if data.get("edit_fails"):
        sys.stderr.write("gh: simulated pr edit failure\\n")
        sys.exit(1)
else:
    sys.exit(1)
"""


def _write_fake_gh(bin_dir: Path):
    p = bin_dir / "gh"
    p.write_text(FAKE_GH)
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return p


def _approve_comment(issue, login, created_at=None, role="implementation"):
    c = {"body": f"APPROVE issue-{issue}/{role}", "author": {"login": login}}
    if created_at is not None:
        c["createdAt"] = created_at
    return c


def _run_guard(cmd, fixtures, tmp_path, cwd=None, edit_log=None):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    _write_fake_gh(bin_dir)
    fixtures_path = tmp_path / "fixtures.json"
    fixtures_path.write_text(json.dumps(fixtures))

    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["GH_FIXTURES"] = str(fixtures_path)
    env["ORCHESTRATE_OFF"] = ""
    if edit_log is not None:
        env["GH_EDIT_LOG"] = str(edit_log)
    return subprocess.run(
        ["bash", str(GUARD)],
        input=payload, capture_output=True, text=True,
        env=env, cwd=str(cwd) if cwd else None, timeout=20,
    )


def _repo_dir(tmp_path, name, approvers):
    d = tmp_path / name
    (d / "docs" / "specs").mkdir(parents=True)
    (d / "docs" / "specs" / "approvers.md").write_text(
        "\n".join(f"- {a}" for a in approvers) + "\n"
    )
    return d


def _repo_dir_on_branch(tmp_path, name, approvers, branch):
    """Like _repo_dir, but a real git checkout on `branch` — needed for the
    record-file half of the content gate (issue #741), which derives the
    acting role from `git rev-parse --abbrev-ref HEAD`. `rev-parse
    --abbrev-ref HEAD` needs at least one commit (fails on an unborn
    branch), so this commits once with a pinned local identity."""
    d = _repo_dir(tmp_path, name, approvers)
    subprocess.run(["git", "init", "-q"], cwd=d, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", branch], cwd=d, check=True)
    subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com",
                     "commit", "-q", "--allow-empty", "-m", "init"], cwd=d, check=True)
    return d


def test_cross_repo_same_number_judges_target_not_cwd(tmp_path):
    """cwd repo and `cd <target>` repo both have PR #7 / issue #9,
    different bodies/approval — the hook must attach the trailer against
    the target repo's PR, not cwd's, and allow the merge (broker-attach,
    issue #653)."""
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    target_dir = _repo_dir(tmp_path, "targetrepo", ["bob"])

    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd", str(target_dir): "target"},
        "repos": {
            "cwd": {
                "pr_body": "Closes #9",  # would PASS if judged (wrong repo)
                "issue_comments": [_approve_comment(9, "alice")],
            },
            "target": {
                "pr_body": "no closing keyword here, just #9",  # needs attach
                "issue_comments": [_approve_comment(9, "bob")],
                "files": [{"path": "src/example.py"}],
            },
        },
    }
    edit_log = tmp_path / "edits.json"
    r = _run_guard(
        f"cd {target_dir} && gh pr merge 7 --merge", fixtures, tmp_path,
        cwd=cwd_dir, edit_log=edit_log,
    )
    assert r.returncode == 0, r.stderr
    calls = json.loads(edit_log.read_text())
    assert len(calls) == 1
    assert calls[0]["repo"] == "target"
    assert "Closes #9" in calls[0]["body"]


def test_repo_flag_targets_repo_but_no_local_approvers_is_unreached(tmp_path):
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd"},
        "repos": {
            "owner/target": {
                "pr_body": "no closing keyword, just #9",
                "issue_comments": [_approve_comment(9, "bob")],
            },
        },
    }
    r = _run_guard("gh pr merge 7 -R owner/target --merge", fixtures, tmp_path, cwd=cwd_dir)
    assert r.returncode == 0, r.stderr  # explicit unreached: no local approvers.md for target


def test_full_pr_url_targets_repo_but_no_local_approvers_is_unreached(tmp_path):
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd"},
        "repos": {
            "owner/target": {
                "pr_body": "no closing keyword, just #9",
                "issue_comments": [_approve_comment(9, "bob")],
            },
        },
    }
    r = _run_guard(
        "gh pr merge https://github.com/owner/target/pull/7 --merge",
        fixtures, tmp_path, cwd=cwd_dir,
    )
    assert r.returncode == 0, r.stderr


def test_cd_prefix_reads_target_approvers_and_attaches(tmp_path):
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    target_dir = _repo_dir(tmp_path, "targetrepo", ["bob"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd", str(target_dir): "target"},
        "repos": {
            "target": {
                "pr_body": "no closing keyword, just #9",
                "issue_comments": [_approve_comment(9, "bob")],
                "files": [{"path": "src/example.py"}],
            },
        },
    }
    edit_log = tmp_path / "edits.json"
    r = _run_guard(
        f"cd {target_dir} && gh pr merge 7 --merge", fixtures, tmp_path,
        cwd=cwd_dir, edit_log=edit_log,
    )
    assert r.returncode == 0, r.stderr
    calls = json.loads(edit_log.read_text())
    assert len(calls) == 1 and "Closes #9" in calls[0]["body"]


def test_cd_prefix_allows_when_target_pr_closes_issue(tmp_path):
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    target_dir = _repo_dir(tmp_path, "targetrepo", ["bob"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd", str(target_dir): "target"},
        "repos": {
            "target": {
                "pr_body": "Closes #9",
                "issue_comments": [_approve_comment(9, "bob")],
            },
        },
    }
    r = _run_guard(f"cd {target_dir} && gh pr merge 7 --merge", fixtures, tmp_path, cwd=cwd_dir)
    assert r.returncode == 0, r.stderr


def test_repo_flag_overrides_cd_prefix_when_they_disagree(tmp_path):
    """Regression for before-landing hunt finding: `cd <path> &&` combined
    with an explicit `-R other/repo` naming a *different* repo must not
    silently judge the `cd`-target repo and drop the flag — the flag wins
    (matching real `gh` semantics) and, with no local checkout of the
    flagged repo, falls into the explicit unreached/fail-open path rather
    than a false "compliant" verdict."""
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    target_dir = _repo_dir(tmp_path, "targetrepo", ["bob"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd", str(target_dir): "target"},
        "repos": {
            "target": {  # cd-target repo: looks compliant
                "pr_body": "Closes #9",
                "issue_comments": [_approve_comment(9, "bob")],
            },
            "other/repo": {  # -R-named repo: actually violates phase-2
                "pr_body": "no closing keyword, just #9",
                "issue_comments": [_approve_comment(9, "eve")],
            },
        },
    }
    cmd = f"cd {target_dir} && gh pr merge 7 -R other/repo --merge"
    r = _run_guard(cmd, fixtures, tmp_path, cwd=cwd_dir)
    assert r.returncode == 0, r.stderr  # explicit unreached, not a false-compliant allow


def test_no_repo_indicator_unchanged_cwd_behavior(tmp_path):
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd"},
        "repos": {
            "cwd": {
                "pr_body": "no closing keyword, just #9",
                "issue_comments": [_approve_comment(9, "alice")],
                "files": [{"path": "src/example.py"}],
            },
        },
    }
    edit_log = tmp_path / "edits.json"
    r = _run_guard("gh pr merge 7 --merge", fixtures, tmp_path, cwd=cwd_dir, edit_log=edit_log)
    assert r.returncode == 0, r.stderr
    calls = json.loads(edit_log.read_text())
    assert len(calls) == 1 and "Closes #9" in calls[0]["body"]


def test_write_failure_still_denies_merge(tmp_path):
    """The one remaining deny path (issue #653): a phase-2 merge with a
    missing trailer whose `gh pr edit` write itself fails must still be
    denied — auto-attach must never silently wave through an unfixed
    body."""
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd"},
        "repos": {
            "cwd": {
                "pr_body": "no closing keyword, just #9",
                "issue_comments": [_approve_comment(9, "alice")],
                "edit_fails": True,
                "files": [{"path": "src/example.py"}],
            },
        },
    }
    r = _run_guard("gh pr merge 7 --merge", fixtures, tmp_path, cwd=cwd_dir)
    assert r.returncode == 2, r.stderr
    assert "phase-2 issue (#9)" in r.stderr
    assert "gh pr edit" in r.stderr




# --- round-scoping matrix (issue #577) ---------------------------------

def test_prior_round_approval_allows_new_phase1_pr(tmp_path):
    """An approval predating this PR's own head branch's first commit is a
    prior round's approval — must not gate a new round's phase-1 PR (no
    Closes obligation)."""
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd"},
        "repos": {
            "cwd": {
                "pr_body": "proposal(issue-9): phase-1 for round 2, no closing keyword",
                "commits": [{"committedDate": "2026-08-10T12:00:00Z"}],
                "issue_comments": [_approve_comment(9, "alice", created_at="2026-08-01T00:00:00Z")],
            },
        },
    }
    r = _run_guard("gh pr merge 7 --merge", fixtures, tmp_path, cwd=cwd_dir)
    assert r.returncode == 0, r.stderr


def test_same_round_approval_attaches_closes_when_missing(tmp_path):
    """An approval newer than this PR's own first commit is the same round
    — a delivering PR with no Closes must have it attached, not just
    denied (broker-attach, issue #653)."""
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd"},
        "repos": {
            "cwd": {
                "pr_body": "no closing keyword here, just #9",
                "commits": [{"committedDate": "2026-08-01T00:00:00Z"}],
                "issue_comments": [_approve_comment(9, "alice", created_at="2026-08-05T00:00:00Z")],
                "files": [{"path": "src/example.py"}],
            },
        },
    }
    edit_log = tmp_path / "edits.json"
    r = _run_guard("gh pr merge 7 --merge", fixtures, tmp_path, cwd=cwd_dir, edit_log=edit_log)
    assert r.returncode == 0, r.stderr
    calls = json.loads(edit_log.read_text())
    assert len(calls) == 1 and "Closes #9" in calls[0]["body"]


def test_same_round_approval_with_closes_allows(tmp_path):
    """Same-round approval plus a proper Closes must still allow — the fix
    must not turn same-round delivery into a false denial."""
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd"},
        "repos": {
            "cwd": {
                "pr_body": "Closes #9",
                "commits": [{"committedDate": "2026-08-01T00:00:00Z"}],
                "issue_comments": [_approve_comment(9, "alice", created_at="2026-08-05T00:00:00Z")],
            },
        },
    }
    r = _run_guard("gh pr merge 7 --merge", fixtures, tmp_path, cwd=cwd_dir)
    assert r.returncode == 0, r.stderr


def test_cross_role_approval_still_gates_phase2(tmp_path):
    """#312 regression: an approval for a *different* role than the PR's
    own, but newer than the PR's first commit, must still count as
    phase-2 — role stays out of the scoping signal, and the missing
    trailer still gets attached rather than silently skipped."""
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd"},
        "repos": {
            "cwd": {
                "pr_body": "no closing keyword here, just #9",
                "commits": [{"committedDate": "2026-08-01T00:00:00Z"}],
                "issue_comments": [
                    _approve_comment(9, "alice", created_at="2026-08-05T00:00:00Z", role="architect"),
                ],
                "files": [{"path": "src/example.py"}],
            },
        },
    }
    edit_log = tmp_path / "edits.json"
    r = _run_guard("gh pr merge 7 --merge", fixtures, tmp_path, cwd=cwd_dir, edit_log=edit_log)
    assert r.returncode == 0, r.stderr
    calls = json.loads(edit_log.read_text())
    assert len(calls) == 1 and "Closes #9" in calls[0]["body"]


# --- content-based phase-2 gate (issue #741) ----------------------------
#
# #741's actual failure: a docs-only phase-1 proposal PR (PR #747/#739-
# shaped) merged with a same-round approval comment already on the issue —
# the round-scoping `phase2` bool above is trivially true the moment
# approval postdates the PR's own first commit, since phase-1 and phase-2
# share one branch. These cases pin the second, content-based condition
# that must also hold before Closes is attached/required.

def test_docsonly_pr_with_same_round_approval_gets_no_closes(tmp_path):
    """The #741 regression itself, PR-#747/#739-shaped: a phase-1 proposal
    PR carrying only docs/ paths, approved in the same round, must NOT get
    `Closes` attached — the issue must stay open for the phase-2 delivery
    PR still to come."""
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd"},
        "repos": {
            "cwd": {
                "pr_body": "proposal(issue-9): phase-1, Refs #9",
                "commits": [{"committedDate": "2026-08-01T00:00:00Z"}],
                "issue_comments": [_approve_comment(9, "alice", created_at="2026-08-05T00:00:00Z")],
                "files": [{"path": "docs/issue-9/proposals/2026-08-01-plan.md"}],
            },
        },
    }
    edit_log = tmp_path / "edits.json"
    r = _run_guard("gh pr merge 7 --merge", fixtures, tmp_path, cwd=cwd_dir, edit_log=edit_log)
    assert r.returncode == 0, r.stderr
    assert not edit_log.exists()


def test_docsonly_pr_with_no_approval_gets_no_closes(tmp_path):
    """Empty-state pairing: a docs-only PR with no approval comment at all
    must also pass through untouched (unchanged from pre-#741 behavior —
    phase2 is already False here, so the content gate is never reached)."""
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd"},
        "repos": {
            "cwd": {
                "pr_body": "proposal(issue-9): phase-1, Refs #9",
                "commits": [{"committedDate": "2026-08-01T00:00:00Z"}],
                "issue_comments": [],
                "files": [{"path": "docs/issue-9/proposals/2026-08-01-plan.md"}],
            },
        },
    }
    edit_log = tmp_path / "edits.json"
    r = _run_guard("gh pr merge 7 --merge", fixtures, tmp_path, cwd=cwd_dir, edit_log=edit_log)
    assert r.returncode == 0, r.stderr
    assert not edit_log.exists()


def test_code_bearing_pr_with_same_round_approval_gets_closes(tmp_path):
    """Regression guard, generalized to the new content-gated code path: a
    PR that actually touches src/ still gets Closes attached on same-round
    approval, exactly as before #741's fix."""
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd"},
        "repos": {
            "cwd": {
                "pr_body": "no closing keyword here, just #9",
                "commits": [{"committedDate": "2026-08-01T00:00:00Z"}],
                "issue_comments": [_approve_comment(9, "alice", created_at="2026-08-05T00:00:00Z")],
                "files": [{"path": "src/contract_guard.py"}],
            },
        },
    }
    edit_log = tmp_path / "edits.json"
    r = _run_guard("gh pr merge 7 --merge", fixtures, tmp_path, cwd=cwd_dir, edit_log=edit_log)
    assert r.returncode == 0, r.stderr
    calls = json.loads(edit_log.read_text())
    assert len(calls) == 1 and "Closes #9" in calls[0]["body"]


def test_unrelated_file_under_reports_dir_gets_no_closes(tmp_path):
    """After-proposal hunt finding, pinned as a permanent regression: a
    file that merely lives under docs/issue-<n>/reports/ but is NOT the
    acting role's own exact record filename (another role's record, a
    stray note) must not be misread as phase-2-shaped — the role-agnostic
    version of this bug must not silently return."""
    cwd_dir = _repo_dir_on_branch(tmp_path, "cwdrepo", ["alice"], "issue-9/implementation")
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd"},
        "repos": {
            "cwd": {
                "pr_body": "no closing keyword here, just #9",
                "commits": [{"committedDate": "2026-08-01T00:00:00Z"}],
                "issue_comments": [_approve_comment(9, "alice", created_at="2026-08-05T00:00:00Z")],
                "files": [{"path": "docs/issue-9/reports/architect.md"}],
            },
        },
    }
    edit_log = tmp_path / "edits.json"
    r = _run_guard("gh pr merge 7 --merge", fixtures, tmp_path, cwd=cwd_dir, edit_log=edit_log)
    assert r.returncode == 0, r.stderr
    assert not edit_log.exists()


def test_own_record_file_alone_gets_closes(tmp_path):
    """A genuine docs-only phase-2 delivery (no src/tests touched) is still
    recognized: the acting role's own exact record file
    (docs/issue-<n>/reports/<role>.md), derived from the branch name,
    counts as phase-2-shaped on its own."""
    cwd_dir = _repo_dir_on_branch(tmp_path, "cwdrepo", ["alice"], "issue-9/implementation")
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd"},
        "repos": {
            "cwd": {
                "pr_body": "no closing keyword here, just #9",
                "commits": [{"committedDate": "2026-08-01T00:00:00Z"}],
                "issue_comments": [_approve_comment(9, "alice", created_at="2026-08-05T00:00:00Z")],
                "files": [{"path": "docs/issue-9/reports/implementation.md"}],
            },
        },
    }
    edit_log = tmp_path / "edits.json"
    r = _run_guard("gh pr merge 7 --merge", fixtures, tmp_path, cwd=cwd_dir, edit_log=edit_log)
    assert r.returncode == 0, r.stderr
    calls = json.loads(edit_log.read_text())
    assert len(calls) == 1 and "Closes #9" in calls[0]["body"]
