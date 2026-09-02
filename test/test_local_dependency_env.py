"""Tests for issue #2159: wire spawned worktrees to the origin checkout's
local dependency directories (node_modules, .venv, vendor/) via env var —
no copy, no symlink into the isolated clone.

`spawn.local_dependency_env(origin, work)` is the pure function under test:
it only reads the filesystem and returns an env-var dict; the wiring at the
`_spawn_one()` call site (origin path captured before `issue_workspace()`
overwrites `cwd`, result merged into `extra_env`) is pinned by a
source-level test the same way test_branch_skill_field.py pins
`issue_workspace()`'s sidecar-write call count.

Run: python3 -m pytest test/test_local_dependency_env.py -q
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import spawn  # noqa: E402


class NoLocalDepDirsTest(unittest.TestCase):
    def test_no_known_dirs_gives_empty_env(self):
        """No regression: a target repo with none of the well-known
        directories gets a byte-identical (empty) env contribution."""
        with tempfile.TemporaryDirectory() as origin, \
             tempfile.TemporaryDirectory() as work:
            (Path(origin) / "src").mkdir()
            self.assertEqual(spawn.local_dependency_env(origin, work), {})

    def test_origin_equals_work_gives_empty_env(self):
        """Reused-workspace case (`issue_workspace()`'s src==work return
        point): no separate origin to point at."""
        with tempfile.TemporaryDirectory() as same:
            (Path(same) / "node_modules").mkdir()
            self.assertEqual(spawn.local_dependency_env(same, same), {})


class NodeModulesTest(unittest.TestCase):
    def test_root_node_modules_sets_node_path(self):
        with tempfile.TemporaryDirectory() as origin, \
             tempfile.TemporaryDirectory() as work:
            nm = Path(origin) / "node_modules"
            nm.mkdir()
            env = spawn.local_dependency_env(origin, work)
            self.assertEqual(env.get("NODE_PATH"), str(nm))

    def test_one_level_subdir_node_modules_sets_node_path(self):
        """Monorepo shape: frontend/node_modules exists only in origin."""
        with tempfile.TemporaryDirectory() as origin, \
             tempfile.TemporaryDirectory() as work:
            nm = Path(origin) / "frontend" / "node_modules"
            nm.mkdir(parents=True)
            env = spawn.local_dependency_env(origin, work)
            self.assertEqual(env.get("NODE_PATH"), str(nm))

    def test_multiple_node_modules_joined_by_pathsep(self):
        with tempfile.TemporaryDirectory() as origin, \
             tempfile.TemporaryDirectory() as work:
            root_nm = Path(origin) / "node_modules"
            fe_nm = Path(origin) / "frontend" / "node_modules"
            root_nm.mkdir()
            fe_nm.mkdir(parents=True)
            env = spawn.local_dependency_env(origin, work)
            got = set(env.get("NODE_PATH", "").split(os.pathsep))
            self.assertEqual(got, {str(root_nm), str(fe_nm)})

    def test_node_modules_already_in_work_is_not_overridden(self):
        """A respawn reusing a persistent `work` dir may already have its
        own node_modules from a prior `npm install` inside that workspace
        — pointing NODE_PATH at origin's copy instead could version-skew
        it, so the existing-in-work case is left alone."""
        with tempfile.TemporaryDirectory() as origin, \
             tempfile.TemporaryDirectory() as work:
            (Path(origin) / "node_modules").mkdir()
            (Path(work) / "node_modules").mkdir()
            env = spawn.local_dependency_env(origin, work)
            self.assertNotIn("NODE_PATH", env)

    def test_require_resolve_succeeds_via_node_path_alone(self):
        """Acceptance (issue #2159): a probe confirms `require.resolve`
        succeeds using only the env this function produces — no manual
        NODE_PATH, no copy into the isolated clone."""
        with tempfile.TemporaryDirectory() as origin, \
             tempfile.TemporaryDirectory() as work:
            pkg_dir = Path(origin) / "node_modules" / "probe-pkg"
            pkg_dir.mkdir(parents=True)
            (pkg_dir / "package.json").write_text(
                '{"name": "probe-pkg", "main": "index.js"}')
            (pkg_dir / "index.js").write_text("module.exports = 1;\n")
            env = spawn.local_dependency_env(origin, work)
            self.assertIn("NODE_PATH", env)
            # Isolation guarantee (issue #513): nothing landed in `work`.
            self.assertEqual(list(Path(work).iterdir()), [])
            probe_env = {**os.environ, "NODE_PATH": env["NODE_PATH"]}
            r = subprocess.run(
                ["node", "-e", "require.resolve('probe-pkg')"],
                cwd=work, env=probe_env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)


class VenvTest(unittest.TestCase):
    def _make_venv(self, base: Path, with_site_packages: bool = True) -> Path:
        venv = base / ".venv"
        if with_site_packages:
            (venv / "lib" / "python3.11" / "site-packages").mkdir(parents=True)
        else:
            venv.mkdir()
        return venv

    def test_single_venv_sets_virtual_env_and_pythonpath(self):
        with tempfile.TemporaryDirectory() as origin, \
             tempfile.TemporaryDirectory() as work:
            venv = self._make_venv(Path(origin))
            env = spawn.local_dependency_env(origin, work)
            self.assertEqual(env.get("VIRTUAL_ENV"), str(venv))
            self.assertEqual(env.get("PYTHONPATH"),
                              str(venv / "lib" / "python3.11" / "site-packages"))

    def test_venv_without_resolvable_site_packages_skips_pythonpath(self):
        with tempfile.TemporaryDirectory() as origin, \
             tempfile.TemporaryDirectory() as work:
            venv = self._make_venv(Path(origin), with_site_packages=False)
            env = spawn.local_dependency_env(origin, work)
            self.assertEqual(env.get("VIRTUAL_ENV"), str(venv))
            self.assertNotIn("PYTHONPATH", env)

    def test_ambiguous_multiple_venvs_skips_entirely(self):
        """Two .venv candidates (e.g. root + a subdir) — which interpreter
        is the right one is undecidable, so skip both VIRTUAL_ENV and
        PYTHONPATH rather than guess."""
        with tempfile.TemporaryDirectory() as origin, \
             tempfile.TemporaryDirectory() as work:
            self._make_venv(Path(origin))
            (Path(origin) / "backend").mkdir()
            self._make_venv(Path(origin) / "backend")
            env = spawn.local_dependency_env(origin, work)
            self.assertNotIn("VIRTUAL_ENV", env)
            self.assertNotIn("PYTHONPATH", env)

    def test_venv_already_in_work_is_not_overridden(self):
        with tempfile.TemporaryDirectory() as origin, \
             tempfile.TemporaryDirectory() as work:
            self._make_venv(Path(origin))
            (Path(work) / ".venv").mkdir()
            env = spawn.local_dependency_env(origin, work)
            self.assertNotIn("VIRTUAL_ENV", env)
            self.assertNotIn("PYTHONPATH", env)


class VendorTest(unittest.TestCase):
    def test_vendor_dir_never_gets_an_env_var(self):
        """vendor/ conventions differ per ecosystem (Go/PHP/Ruby/...) — no
        single lookup var applies, so detection never turns into an env
        pointer for it (issue #2159's 'skip vendor/ if ambiguous')."""
        with tempfile.TemporaryDirectory() as origin, \
             tempfile.TemporaryDirectory() as work:
            (Path(origin) / "vendor").mkdir()
            env = spawn.local_dependency_env(origin, work)
            self.assertEqual(env, {})

    def test_vendor_alongside_node_modules_still_sets_node_path(self):
        with tempfile.TemporaryDirectory() as origin, \
             tempfile.TemporaryDirectory() as work:
            (Path(origin) / "vendor").mkdir()
            nm = Path(origin) / "node_modules"
            nm.mkdir()
            env = spawn.local_dependency_env(origin, work)
            self.assertEqual(env, {"NODE_PATH": str(nm)})


class NoFilesystemMutationTest(unittest.TestCase):
    def test_function_never_writes_to_origin_or_work(self):
        with tempfile.TemporaryDirectory() as origin, \
             tempfile.TemporaryDirectory() as work:
            (Path(origin) / "node_modules").mkdir()
            (Path(origin) / ".venv" / "lib" / "python3.11"
             / "site-packages").mkdir(parents=True)
            before_origin = sorted(str(p) for p in Path(origin).rglob("*"))
            before_work = sorted(str(p) for p in Path(work).rglob("*"))
            spawn.local_dependency_env(origin, work)
            after_origin = sorted(str(p) for p in Path(origin).rglob("*"))
            after_work = sorted(str(p) for p in Path(work).rglob("*"))
            self.assertEqual(before_origin, after_origin)
            self.assertEqual(before_work, after_work)

    def test_no_symlink_or_copy_calls_in_implementation(self):
        """Source-level pin: the function body never calls os.symlink,
        shutil.copy*, or shutil.copytree — the isolation guarantee (issue
        #513) that motivates env-var-pointer-only, not file movement."""
        text = (REPO_ROOT / "spawn.py").read_text(encoding="utf-8")
        start = text.index("def local_dependency_env(")
        end = text.index("\ndef issue_workspace(", start)
        body = text[start:end]
        for forbidden in ("os.symlink(", "shutil.copy", "shutil.move("):
            self.assertNotIn(forbidden, body)


class CallSiteWiringTest(unittest.TestCase):
    """Source-level pin (same convention as test_branch_skill_field.py's
    ApprovalGateEquivalenceTest / sidecar-count tests): `_spawn_one()` must
    capture the origin cwd *before* `issue_workspace()` reassigns `cwd` to
    the isolated clone, and must fold `local_dependency_env()`'s result
    into `extra_env` before the session subprocess spawns."""

    def test_origin_captured_before_workspace_reassignment(self):
        # issue #2731 renamed the `role` parameter to `skill` throughout
        # spawn.py, and issue #2742 (PR #2794) wrapped the direct
        # `issue_workspace()` call in `_create_workspace_with_signal_guard()`
        # -- search from the capture point on, since an unrelated adhoc-task
        # branch earlier in this same function also calls
        # `_create_workspace_with_signal_guard()` for a different reason.
        text = (REPO_ROOT / "spawn.py").read_text(encoding="utf-8")
        start = text.index("def _spawn_one(")
        end = text.index('\nif __name__ == "__main__":', start)
        body = text[start:end]
        capture_at = body.index("origin_cwd = cwd")
        reassign_at = body.index(
            "cwd = _create_workspace_with_signal_guard(", capture_at)
        self.assertLess(capture_at, reassign_at)

    def test_local_dependency_env_merged_into_extra_env(self):
        text = (REPO_ROOT / "spawn.py").read_text(encoding="utf-8")
        start = text.index("def _spawn_one(")
        end = text.index('\nif __name__ == "__main__":', start)
        body = text[start:end]
        self.assertIn("extra_env.update(local_dependency_env(origin_cwd, cwd))",
                       body)


if __name__ == "__main__":
    unittest.main()
