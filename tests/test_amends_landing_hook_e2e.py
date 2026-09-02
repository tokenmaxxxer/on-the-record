"""Issue #3134 repair round 4: PR #3168's independent verification found
that `gates/amends_landing.py::land()` is sound but the `PostToolUse`
trigger that calls it automatically, `on-the-record/hooks/amends-landing-
apply.sh`, was not -- its command-shape check matched `gh pr merge
--help`, and its old "no failure marker in the tool_response text"
success heuristic treated that non-merge command as a successful merge.
PR #3168 reproduced a real clone+push to a scratch remote's default
branch in response to `gh pr merge --help`.

This file drives the REAL hook script with realistic `PostToolUse`
payloads -- the exact gap PR #3168 named: "The new e2e test never drives
the hook script itself (only calls `land()` directly), so this defect
has zero test coverage." A fake `gh` on `PATH` answers `gh pr view --json
state,mergedAt` (the new authoritative signal the fixed hook requires);
everything else -- `git`, the real `gates/amends_landing.py` -- is real.

  python3 -m pytest tests/test_amends_landing_hook_e2e.py -q
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = ROOT / "on-the-record" / "hooks"
HOOK = HOOKS_DIR / "amends-landing-apply.sh"

FAKE_GH_SCRIPT = """#!/usr/bin/env bash
# fake `gh` for tests -- only implements `gh pr view ... --json state,mergedAt`,
# the one subcommand amends-landing-apply.sh's fixed trigger calls.
if [ "$1" = "pr" ] && [ "$2" = "view" ]; then
  if [ -n "${FAKE_GH_EXIT:-}" ] && [ "${FAKE_GH_EXIT}" != "0" ]; then
    echo "${FAKE_GH_STDERR:-no such pull request}" >&2
    exit "${FAKE_GH_EXIT}"
  fi
  json="${FAKE_GH_JSON:-}"
  [ -n "$json" ] || json='{}'
  printf '%s' "$json"
  exit 0
fi
echo "fake gh: unsupported invocation: $*" >&2
exit 1
"""


def _git(*args, cwd):
    r = subprocess.run(["git", "-C", str(cwd), *args],
                        capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, f"git {args} failed: {r.stderr}"
    return r.stdout


class AmendsLandingHookEndToEndTest(unittest.TestCase):
    """Builds a bare remote + a local checkout (`origin` pointed at it,
    matching what `gh pr merge` runs against for real), then invokes the
    real hook binary with a realistic `PostToolUse` payload for each
    scenario and asserts on the remote's own tip commit -- the only
    ground truth for "did this push."
    """

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp())

        fake_bin = self._tmp / "fakebin"
        fake_bin.mkdir()
        gh_path = fake_bin / "gh"
        gh_path.write_text(FAKE_GH_SCRIPT, encoding="utf-8")
        gh_path.chmod(gh_path.stat().st_mode | stat.S_IEXEC)
        self._fake_bin = fake_bin

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _build_fixture(self, name: str, with_edge: bool) -> tuple[Path, Path]:
        """A bare remote + a local checkout with `origin` set to it and
        `origin/HEAD` resolvable (what the hook's own remote/branch
        resolution needs) -- optionally carrying one unresolved `amends:`
        edge, landed and pushed, exactly what a merged correcting PR's
        checkout looks like right before the landing step runs."""
        base = self._tmp / name
        bare = base / "remote.git"
        work = base / "work"
        base.mkdir()

        subprocess.run(["git", "init", "-q", "--bare", str(bare)],
                        check=True, capture_output=True)

        work.mkdir()
        _git("init", "-q", "-b", "main", cwd=work)
        _git("config", "user.email", "t@t", cwd=work)
        _git("config", "user.name", "t", cwd=work)

        target_dir = work / "docs" / "issue-97001" / "reports"
        target_dir.mkdir(parents=True)
        (target_dir / "target.md").write_text(
            "---\nissue: 97001\nrole: target-record\n---\n\n"
            "# issue-97001 record\n\n"
            "## Limitation\n\nThe claim in this section is wrong.\n",
            encoding="utf-8",
        )
        (work / "docs" / "specs").mkdir(parents=True, exist_ok=True)
        sys.path.insert(0, str(ROOT / "gates"))
        import amends_index as _amends_index_for_fixture
        _amends_index_for_fixture.update(work)

        _git("add", "-A", cwd=work)
        _git("commit", "-q", "-m", "initial landed tree", cwd=work)

        if with_edge:
            corrector_dir = work / "docs" / "issue-97002" / "reports"
            corrector_dir.mkdir(parents=True)
            (corrector_dir / "corrector.md").write_text(
                "---\nissue: 97002\nrole: corrector\n"
                "amends: docs/issue-97001/reports/target.md#limitation"
                "  # verified independently: it is actually right"
                "\n---\n\n## Correction\n\ntext\n",
                encoding="utf-8",
            )
            _git("add", "-A", cwd=work)
            _git("commit", "-q", "-m", "issue-97002: correction", cwd=work)

        _git("push", "-q", str(bare), "main", cwd=work)
        subprocess.run(["git", "-C", str(bare), "symbolic-ref", "HEAD",
                         "refs/heads/main"], check=True, capture_output=True)

        _git("remote", "add", "origin", str(bare), cwd=work)
        _git("fetch", "-q", "origin", cwd=work)
        _git("remote", "set-head", "origin", "-a", cwd=work)

        return bare, work

    def _bare_tip(self, bare: Path) -> str:
        return _git("rev-parse", "main", cwd=bare).strip()

    def _run_hook(self, run_cwd: Path, command: str, tool_response: str,
                  gh_json: str | None = None, gh_exit: str | None = None,
                  session_id: str = "hook-e2e") -> subprocess.CompletedProcess:
        payload = json.dumps({
            "tool_name": "Bash",
            "session_id": session_id,
            "cwd": str(run_cwd),
            "tool_input": {"command": command},
            "tool_response": tool_response,
        })
        env = {
            "PATH": f"{self._fake_bin}:/usr/bin:/bin:/usr/local/bin",
            "HOME": os.environ.get("HOME", "/tmp"),
        }
        if gh_json is not None:
            env["FAKE_GH_JSON"] = gh_json
        if gh_exit is not None:
            env["FAKE_GH_EXIT"] = gh_exit
        return subprocess.run(
            ["bash", str(HOOK)], input=payload, env=env,
            capture_output=True, text=True, timeout=60, cwd=str(run_cwd),
        )

    def test_help_invocation_never_pushes(self):
        bare, work = self._build_fixture("help", with_edge=True)
        before = self._bare_tip(bare)
        r = self._run_hook(
            work, "gh pr merge --help",
            tool_response="Usage: gh pr merge [<number> | <url> | <branch>] [flags]\n...",
            gh_json='{"state": "MERGED", "mergedAt": "2026-09-02T00:00:00Z"}',
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            before, self._bare_tip(bare),
            "`gh pr merge --help` must never push a landing-step commit -- "
            "PR #3168 reproduced exactly this as a real push to main",
        )

    def test_failed_merge_never_pushes(self):
        bare, work = self._build_fixture("failed", with_edge=True)
        before = self._bare_tip(bare)
        r = self._run_hook(
            work, "gh pr merge 42 --squash",
            tool_response="X Failed to merge pull request #42: Pull "
                           "Request is not mergeable: the merge commit "
                           "cannot be cleanly created.",
            gh_json='{"state": "OPEN", "mergedAt": null}',
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            before, self._bare_tip(bare),
            "a merge `gh pr view` itself reports as still OPEN must never push",
        )

    def test_successful_merge_zero_edges_never_pushes(self):
        bare, work = self._build_fixture("clean", with_edge=False)
        before = self._bare_tip(bare)
        r = self._run_hook(
            work, "gh pr merge 42 --squash",
            tool_response="Merged pull request #42 (some unrelated PR) "
                           "into main from feature-branch",
            gh_json='{"state": "MERGED", "mergedAt": "2026-09-02T00:00:00Z"}',
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            before, self._bare_tip(bare),
            "a genuine merge with no amends: edges has nothing to apply -- "
            "must not push an empty landing-step commit",
        )

    def test_genuine_merge_with_edge_pushes_the_backlink(self):
        bare, work = self._build_fixture("edge", with_edge=True)
        before = self._bare_tip(bare)
        r = self._run_hook(
            work, "gh pr merge 42 --squash",
            tool_response="Merged pull request #42 (issue-97002: "
                           "correction) into main from issue-97002-branch",
            gh_json='{"state": "MERGED", "mergedAt": "2026-09-02T00:00:00Z"}',
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        after = self._bare_tip(bare)
        self.assertNotEqual(
            before, after,
            "a genuine merge with an unresolved amends: edge must push "
            "the landing-step backlink commit -- this is the only "
            "scenario of the four that should push",
        )
        landed_target = _git("show", "main:docs/issue-97001/reports/"
                              "target.md", cwd=bare)
        self.assertIn("> **Amended**", landed_target)


if __name__ == "__main__":
    unittest.main()
