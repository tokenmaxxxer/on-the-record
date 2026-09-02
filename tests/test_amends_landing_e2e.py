"""Issue #3134 repair round 3: the end-to-end scenario the reopen comment
named as "the test that matters" -- through the REAL commit-time hook
(`on-the-record/hooks/amends-index-preflight.sh`, simulated with a
realistic `PreToolUse` payload, same technique PR #3160's own independent
verification used), then through the real landing step
(`gates/amends_landing.py::land()`, the automatic caller
`on-the-record/hooks/amends-landing-apply.sh` invokes on a successful
`gh pr merge`), against a local bare-repo remote so no GitHub credentials
or network access are needed:

  1. an unrelated session's report commit (no `amends:` field) is never
     blocked;
  2. a correcting session commits its own target+corrector pair through
     the real preflight hook -- must succeed (round-3 finding 1);
  3. the PR "lands" (its branch merges into the remote's default branch)
     and `land()` -- with NO human step, no CLI run by hand -- applies the
     backlink and pushes it back (round-3 finding 3);
  4. a reader who fetches the landed tree and opens the target directly
     meets the amendment (the discoverability property the whole `amends:`
     primitive exists for).

  python3 -m pytest tests/test_amends_landing_e2e.py -q
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = ROOT / "on-the-record" / "hooks"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))

import amends_landing  # noqa: E402


def _git(*args, cwd):
    r = subprocess.run(["git", "-C", str(cwd), *args],
                        capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, f"git {args} failed: {r.stderr}"
    return r.stdout


def _run_preflight_hook(cwd: Path) -> subprocess.CompletedProcess:
    """Invokes the REAL `amends-index-preflight.sh` with a realistic
    `PreToolUse` payload for a `git commit` in `cwd` -- the same
    simulate-the-actual-hook technique the #3134 repair round's own
    independent verification (PR #3160) used, not a re-implementation of
    the hook's own logic."""
    payload = json.dumps({
        "tool_name": "Bash",
        "session_id": "e2e-test",
        "cwd": str(cwd),
        "tool_input": {"command": "git commit -m e2e"},
    })
    env = {
        "AIP_PAYLOAD": payload,
        "OTR_HOOKS_DIR": str(HOOKS_DIR),
        "PATH": "/usr/bin:/bin:/usr/local/bin",
    }
    import os
    return subprocess.run(
        ["bash", str(HOOKS_DIR / "amends-index-preflight.sh")],
        input=payload, env=env, capture_output=True, text=True, timeout=30,
        cwd=str(cwd),
    )


class AmendsLandingEndToEndTest(unittest.TestCase):
    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp())
        self.bare = self._tmp / "remote.git"
        self.work = self._tmp / "work"
        self.pr_clone = self._tmp / "pr-clone"

        _git("init", "-q", "--bare", "--initial-branch=main", cwd=self._tmp,
             ) if False else None
        subprocess.run(["git", "init", "-q", "--bare", str(self.bare)],
                        check=True, capture_output=True)

        self.work.mkdir()
        _git("init", "-q", "-b", "main", cwd=self.work)
        _git("-c", "user.email=t@t", "-c", "user.name=t", "config",
             "user.email", "t@t", cwd=self.work)
        _git("config", "user.name", "t", cwd=self.work)

        for rel in ("gates", "amends.py", "amends_backlink.py"):
            src = ROOT / rel
            dst = self.work / rel
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                dst.write_bytes(src.read_bytes())

        target_dir = self.work / "docs" / "issue-96001" / "reports"
        target_dir.mkdir(parents=True)
        (target_dir / "target.md").write_text(
            "---\nissue: 96001\nrole: target-record\n---\n\n"
            "# issue-96001 record\n\n"
            "## Summary\n\nAll good here.\n\n"
            "## Limitation\n\nThe claim in this section is wrong: X never "
            "happens.\n",
            encoding="utf-8",
        )
        # A committed docs/specs/amends-index.md, matching the real repo's
        # own always-present state (empty git trees never carry an
        # otherwise-empty directory, so a fixture that skipped this would
        # diverge from what an actual `git clone` of this repo produces).
        (self.work / "docs" / "specs").mkdir(parents=True, exist_ok=True)
        import amends_index as _amends_index_for_fixture
        _amends_index_for_fixture.update(self.work)

        _git("add", "-A", cwd=self.work)
        _git("commit", "-q", "-m", "initial landed tree", cwd=self.work)
        _git("push", "-q", str(self.bare), "main", cwd=self.work)
        # `origin/HEAD` must resolve for amends_landing/the hook to pick a
        # default branch -- a bare repo created with `git init --bare` has
        # no HEAD ref pointing at a branch with content until something is
        # pushed to it; set it explicitly once "main" exists.
        subprocess.run(["git", "-C", str(self.bare), "symbolic-ref",
                         "HEAD", "refs/heads/main"], check=True,
                        capture_output=True)

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_full_amends_lifecycle_with_no_human_step(self):
        # --- 1. an unrelated session's report commit is never blocked ---
        unrelated_dir = self.work / "docs" / "issue-96002" / "reports"
        unrelated_dir.mkdir(parents=True)
        (unrelated_dir / "unrelated.md").write_text(
            "---\nissue: 96002\nrole: unrelated\n---\n\n"
            "nothing to do with amends: at all.\n",
            encoding="utf-8",
        )
        _git("add", "-A", cwd=self.work)
        r = _run_preflight_hook(self.work)
        self.assertEqual(
            r.returncode, 0,
            "an unrelated session's own commit must never be blocked: "
            + r.stderr,
        )
        _git("commit", "-q", "-m", "unrelated report", cwd=self.work)

        # --- 2. correcting session commits target+corrector -- must
        # succeed through the REAL preflight hook (round-3 finding 1) ---
        corrector_dir = self.work / "docs" / "issue-96003" / "reports"
        corrector_dir.mkdir(parents=True)
        (corrector_dir / "corrector.md").write_text(
            "---\nissue: 96003\nrole: corrector\n"
            "amends: docs/issue-96001/reports/target.md#limitation"
            "  # verified independently: X does happen under condition Y"
            "\n---\n\n## Correction\n\ntext\n",
            encoding="utf-8",
        )
        _git("add", "-A", cwd=self.work)
        r = _run_preflight_hook(self.work)
        self.assertEqual(
            r.returncode, 0,
            "a correcting session's own first commit of its own "
            "still-unlinked amends: record must succeed: " + r.stderr,
        )
        _git("commit", "-q", "-m", "issue-96003: correction", cwd=self.work)
        _git("push", "-q", str(self.bare), "main", cwd=self.work)

        # Sanity: the backlink does NOT exist yet -- nobody has landed it.
        pre_land_target = _git("show", "main:docs/issue-96001/reports/"
                                "target.md", cwd=self.bare)
        self.assertNotIn("Amended", pre_land_target)

        # --- 3. land it: amends_landing.land(), representing exactly what
        # amends-landing-apply.sh calls automatically after a successful
        # `gh pr merge` -- no human runs the CLI by hand ---
        result = amends_landing.land(str(self.bare), "main")
        self.assertIsNone(result["error"], result["error"])
        self.assertTrue(result["pushed"], "land() must push the applied "
                         "backlink back to the remote")
        self.assertIn("docs/issue-96001/reports/target.md",
                       result["written"])
        self.assertEqual(result["remaining"], [])

        # --- 4. a reader who fetches the landed tree and opens the target
        # directly meets the amendment ---
        landed_target = _git("show", "main:docs/issue-96001/reports/"
                              "target.md", cwd=self.bare)
        self.assertIn(
            "> **Amended** by "
            "`docs/issue-96003/reports/corrector.md`: verified "
            "independently: X does happen under condition Y",
            landed_target,
        )
        # Section grain: the Summary section is untouched.
        self.assertIn("## Summary\n\nAll good here.", landed_target)
        # The marker sits directly under the Limitation heading, not only
        # in a generated index -- "opening A" is the route, not
        # "consulting the index."
        heading_idx = landed_target.index("## Limitation")
        marker_idx = landed_target.index("> **Amended**")
        self.assertLess(
            heading_idx, marker_idx,
            "the backlink must live under the amended heading itself",
        )


if __name__ == "__main__":
    unittest.main()
