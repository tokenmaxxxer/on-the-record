"""issue #1587 — `spawn.py judge`: read-only, budgeted role judgment over a
merge diff, writing validated findings to the tier-1 patrol queue (diff
lane). Mirrors tests/test_spawn.py's ConsultCmd conventions: subprocess
calls are patched, no real `claude`/`git` session runs.
"""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str((Path(__file__).resolve().parent.parent / "gates")))
import spawn
import patrol_queue


class ReadonlySettingsTest(unittest.TestCase):
    """제안서 §Constraints: Write/Edit 없음, Bash 허용목록에 `gh ` 없음,
    permissions.deny 로도 명시적으로 막는다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = str(Path(self.tmp.name))

    def test_no_write_edit_tools_and_no_gh_in_allow(self):
        s = spawn._readonly_settings("implementation", self.root)
        allow = s["permissions"]["allow"]
        self.assertNotIn("Write", allow)
        self.assertNotIn("Edit", allow)
        self.assertFalse(any("gh " in a for a in allow))
        self.assertIn("Write", s["permissions"]["deny"])
        self.assertIn("Edit", s["permissions"]["deny"])
        self.assertTrue(any("gh " in d for d in s["permissions"]["deny"]))

    def test_bash_allow_is_git_plumbing_only(self):
        allow = spawn._readonly_bash_allow(self.root)
        for pattern in allow:
            self.assertIn("git", pattern)
            self.assertNotIn("gh ", pattern)
            self.assertNotRegex(pattern, r"\brm\b|\bcurl\b|\bwget\b")

    def test_judge_cmd_and_env_omits_bypass_permissions(self):
        spec = json.loads((spawn.ROOT / "roles" / "implementation.json").read_text())
        self._patch(spawn, "plugin_dirs", lambda role, s: [Path("/fake/plugin")])
        self._patch(spawn, "core_plugin_dirs", lambda: [])
        cmd, env, settings_path = spawn._judge_cmd_and_env("implementation", spec, self.root)
        self.addCleanup(lambda: Path(settings_path).unlink(missing_ok=True))
        self.assertNotIn("bypassPermissions", cmd)
        self.assertNotIn("--permission-mode", cmd)

    def _patch(self, obj, name, value):
        orig = getattr(obj, name)
        setattr(obj, name, value)
        self.addCleanup(lambda: setattr(obj, name, orig))


class PluginDirFilterTest(unittest.TestCase):
    """제안서 §What will be done 2: core 의 배달-지향 플러그인은 걸러지고,
    역할 자신의 룰북은 그대로 남는다."""

    def test_excludes_delivery_oriented_core_plugins(self):
        role_plugin = Path("/fake/role-plugin")
        core_plugins = [Path("/fake/core/core"), Path("/fake/core/terse"),
                        Path("/fake/core/freelunch"), Path("/fake/core/scout"),
                        Path("/fake/core/warrant")]
        orig_plugin_dirs = spawn.plugin_dirs
        orig_core_plugin_dirs = spawn.core_plugin_dirs
        spawn.plugin_dirs = lambda role, spec: [role_plugin]
        spawn.core_plugin_dirs = lambda: core_plugins
        try:
            out = spawn._readonly_plugin_dirs("implementation", {})
        finally:
            spawn.plugin_dirs = orig_plugin_dirs
            spawn.core_plugin_dirs = orig_core_plugin_dirs

        names = {p.name for p in out}
        self.assertIn("role-plugin", names)
        self.assertIn("core", names)
        self.assertIn("terse", names)
        self.assertNotIn("freelunch", names)
        self.assertNotIn("scout", names)
        self.assertNotIn("warrant", names)


class CompressDiffTest(unittest.TestCase):
    """제안서 §Constraints: PR-Agent 식 압축 — 삭제파일은 이름만, 삭제-only
    훅은 버리고, 여전히 상한을 넘으면 실패가 아니라 파일명 목록으로
    내려간다."""

    def test_deleted_file_collapses_to_name_only(self):
        diff = (
            "diff --git a/old.py b/old.py\n"
            "deleted file mode 100644\n"
            "index 1234567..0000000\n"
            "--- a/old.py\n"
            "+++ /dev/null\n"
            "@@ -1,3 +0,0 @@\n"
            "-line one\n"
            "-line two\n"
            "-line three\n"
        )
        out = spawn._compress_diff(diff)
        self.assertIn("deleted: old.py", out)
        self.assertNotIn("line one", out)

    def test_addition_hunk_survives(self):
        diff = (
            "diff --git a/new.py b/new.py\n"
            "index 1234567..89abcde 100644\n"
            "--- a/new.py\n"
            "+++ b/new.py\n"
            "@@ -1,2 +1,3 @@\n"
            " context\n"
            "+added line\n"
            " context2\n"
        )
        out = spawn._compress_diff(diff)
        self.assertIn("added line", out)

    def test_graceful_degradation_to_name_list_when_over_cap(self):
        blocks = []
        for i in range(50):
            blocks.append(
                f"diff --git a/file{i}.py b/file{i}.py\n"
                "index 1111111..2222222 100644\n"
                f"--- a/file{i}.py\n+++ b/file{i}.py\n"
                "@@ -1,1 +1,2 @@\n context\n" + ("+" + "x" * 500 + "\n")
            )
        diff = "\n".join(blocks)
        out = spawn._compress_diff(diff, cap_tokens=100)
        self.assertLessEqual(len(out), 400)
        self.assertIn("file0.py", out)


class JudgeCapTest(unittest.TestCase):
    """binding review note (PR #1590): 3-역할/머지 캡은 트레이스 로그에서
    세지만, 로그가 없거나 회전돼 있어도 방어적으로 0(허용)으로 fail —
    로그 부재가 판정을 막지 않는다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_missing_trace_log_defaults_to_zero(self):
        missing = self.root / "does" / "not" / "exist.md"
        self.assertEqual(spawn._judge_roles_run_today(missing, "abc123"), 0)

    def test_counts_only_matching_merge_sha(self):
        path = self.root / "patrol-judge-log.md"
        path.write_text(
            "- t | role=implementation | verb=judge | merge=abc123 | outcome='ok'\n"
            "- t | role=qa | verb=judge | merge=abc123 | outcome='ok'\n"
            "- t | role=implementation | verb=judge | merge=other456 | outcome='ok'\n"
            "- t | role=implementation | verb=consult | merge=abc123 | outcome='ok'\n",
            encoding="utf-8",
        )
        self.assertEqual(spawn._judge_roles_run_today(path, "abc123"), 2)
        self.assertEqual(spawn._judge_roles_run_today(path, "other456"), 1)
        self.assertEqual(spawn._judge_roles_run_today(path, "never-seen"), 0)

    def test_corrupted_log_defaults_to_zero_not_exception(self):
        path = self.root / "binary.md"
        path.write_bytes(b"\xff\xfe\x00\x01garbage")
        # 디코드 실패 없이(파일이 UTF-8 아님) 조용히 0을 돌려준다 — 예외로
        # 판단을 막지 않는다.
        try:
            count = spawn._judge_roles_run_today(path, "abc123")
        except UnicodeDecodeError:
            self.fail("_judge_roles_run_today() must not raise on a corrupted log")
        self.assertEqual(count, 0)


class JudgeTraceAlwaysTest(unittest.TestCase):
    """제안서 §Constraints: trace-always — 성공/실패 가리지 않고 한 줄."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self._patches = []
        self._patch(spawn, "plugin_dirs", lambda role, spec: [Path("/fake/plugin")])
        self._patch(spawn, "core_plugin_dirs", lambda: [])

    def _patch(self, obj, name, value):
        orig = getattr(obj, name)
        setattr(obj, name, value)
        self._patches.append((obj, name, orig))
        self.addCleanup(lambda: setattr(obj, name, orig))

    def _trace_lines(self):
        p = self.root / "docs" / "reports" / "patrol-judge-log.md"
        return p.read_text(encoding="utf-8").splitlines() if p.is_file() else []

    def test_traces_on_git_show_failure(self):
        def fake_run(cmd, **kw):
            if cmd[:3] == ["git", "-C", str(self.root)]:
                return subprocess.CompletedProcess(cmd, 128, stdout="", stderr="unknown revision")
            raise AssertionError(f"unexpected subprocess call: {cmd}")
        self._patch(spawn.subprocess, "run", fake_run)

        with self.assertRaises(RuntimeError):
            spawn.judge_cmd("implementation", "deadbeef", cwd=str(self.root))

        lines = self._trace_lines()
        self.assertEqual(len(lines), 1)
        self.assertIn("verb=judge", lines[0])
        self.assertIn("merge=deadbeef", lines[0])
        self.assertIn("error:", lines[0])

    def test_traces_on_cap_exceeded_without_dispatching_git(self):
        trace_path = self.root / "docs" / "reports" / "patrol-judge-log.md"
        trace_path.parent.mkdir(parents=True)
        trace_path.write_text(
            "- t | role=implementation | verb=judge | merge=deadbeef | outcome='ok'\n"
            "- t | role=qa | verb=judge | merge=deadbeef | outcome='ok'\n"
            "- t | role=review | verb=judge | merge=deadbeef | outcome='ok'\n",
            encoding="utf-8",
        )
        calls = []
        def fake_run(cmd, **kw):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        self._patch(spawn.subprocess, "run", fake_run)

        result = spawn.judge_cmd("implementation", "deadbeef", cwd=str(self.root))

        self.assertEqual(result["skipped"], True)
        self.assertEqual(result["reason"], "cap_exceeded")
        self.assertEqual(calls, [])  # 캡 초과면 git show 조차 안 부른다
        lines = self._trace_lines()
        self.assertEqual(len(lines), 4)
        self.assertIn("캡 초과", lines[-1])


class JudgePrefilterSkipTest(unittest.TestCase):
    """prefilter 가 관할 미스라고 하면 judge 본세션은 아예 호출되지 않는다
    (제안서 §5 "largest cost saver")."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self._patches = []
        self._patch(spawn, "plugin_dirs", lambda role, spec: [Path("/fake/plugin")])
        self._patch(spawn, "core_plugin_dirs", lambda: [])

    def _patch(self, obj, name, value):
        orig = getattr(obj, name)
        setattr(obj, name, value)
        self._patches.append((obj, name, orig))
        self.addCleanup(lambda: setattr(obj, name, orig))

    def test_prefilter_miss_skips_judge_subprocess_call(self):
        claude_calls = []

        def fake_run(cmd, **kw):
            if cmd[0] == "git":
                return subprocess.CompletedProcess(
                    cmd, 0,
                    stdout="diff --git a/x.py b/x.py\n@@ -1 +1,2 @@\n context\n+added\n",
                    stderr="")
            if cmd[0] == "claude":
                claude_calls.append(cmd)
                payload = json.dumps({"result": '{"relevant": false}', "is_error": False})
                return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")
            raise AssertionError(f"unexpected: {cmd}")
        self._patch(spawn.subprocess, "run", fake_run)

        result = spawn.judge_cmd("implementation", "deadbeef", cwd=str(self.root))

        self.assertEqual(result["skipped"], True)
        self.assertEqual(result["reason"], "prefilter_miss")
        self.assertEqual(len(claude_calls), 1)  # prefilter 딱 한 번, judge 본세션은 없음


class JudgeValidatorDropTest(unittest.TestCase):
    """validator 가 finding 을 기각하면 그 finding 은 큐(`enqueue()`)에
    절대 닿지 않는다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self._patches = []
        self._patch(spawn, "plugin_dirs", lambda role, spec: [Path("/fake/plugin")])
        self._patch(spawn, "core_plugin_dirs", lambda: [])

    def _patch(self, obj, name, value):
        orig = getattr(obj, name)
        setattr(obj, name, value)
        self._patches.append((obj, name, orig))
        self.addCleanup(lambda: setattr(obj, name, orig))

    def test_refuted_finding_never_reaches_enqueue(self):
        enqueue_calls = []
        orig_enqueue = patrol_queue.enqueue

        def spy_enqueue(queue, finding):
            enqueue_calls.append(finding)
            return orig_enqueue(queue, finding)
        self._patch(patrol_queue, "enqueue", spy_enqueue)

        claude_responses = iter([
            {"relevant": True},                     # prefilter
            {"findings": []},                        # judge session: one finding surfaced below
        ])

        def fake_run(cmd, **kw):
            if cmd[0] == "git":
                return subprocess.CompletedProcess(
                    cmd, 0,
                    stdout="diff --git a/x.py b/x.py\n@@ -1 +1,2 @@\n context\n+added\n",
                    stderr="")
            if cmd[0] == "claude":
                if "--max-turns" in cmd:  # judge 본세션
                    payload = json.dumps({"result": json.dumps({
                        "findings": [{"path": "x.py", "finding_class": "violation",
                                     "excerpt": "added", "promotable": True}]}),
                        "is_error": False})
                    return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")
                # prefilter 또는 validator — 프롬프트로 구분
                prompt = kw.get("input", "")
                if "relevant" in prompt:
                    payload = json.dumps({"result": '{"relevant": true}', "is_error": False})
                else:
                    # validator: 전부 반박한다
                    payload = json.dumps({"result": '{"findings": []}', "is_error": False})
                return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")
            raise AssertionError(f"unexpected: {cmd}")
        self._patch(spawn.subprocess, "run", fake_run)

        result = spawn.judge_cmd("implementation", "deadbeef", cwd=str(self.root))

        self.assertEqual(enqueue_calls, [])
        self.assertEqual(result["enqueued"], [])
        queue_path = self.root / patrol_queue.QUEUE_REL_PATH
        self.assertFalse(queue_path.exists())


class JudgeEnqueueTest(unittest.TestCase):
    """validator 를 통과한 finding 은 `lane="diff"`로 patrol 큐에 실제
    기록된다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self._patches = []
        self._patch(spawn, "plugin_dirs", lambda role, spec: [Path("/fake/plugin")])
        self._patch(spawn, "core_plugin_dirs", lambda: [])

    def _patch(self, obj, name, value):
        orig = getattr(obj, name)
        setattr(obj, name, value)
        self._patches.append((obj, name, orig))
        self.addCleanup(lambda: setattr(obj, name, orig))

    def test_validated_finding_lands_in_queue_with_diff_lane(self):
        def fake_run(cmd, **kw):
            if cmd[0] == "git":
                return subprocess.CompletedProcess(
                    cmd, 0,
                    stdout="diff --git a/x.py b/x.py\n@@ -1 +1,2 @@\n context\n+added\n",
                    stderr="")
            if cmd[0] == "claude":
                prompt = kw.get("input", "")
                if "--max-turns" in cmd:
                    payload = json.dumps({"result": json.dumps({
                        "findings": [{"path": "x.py", "finding_class": "violation",
                                     "excerpt": "added", "promotable": True}]}),
                        "is_error": False})
                elif "relevant" in prompt:
                    payload = json.dumps({"result": '{"relevant": true}', "is_error": False})
                else:
                    payload = json.dumps({"result": json.dumps({
                        "findings": [{"path": "x.py", "finding_class": "violation",
                                     "excerpt": "added", "promotable": True}]}),
                        "is_error": False})
                return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")
            raise AssertionError(f"unexpected: {cmd}")
        self._patch(spawn.subprocess, "run", fake_run)

        result = spawn.judge_cmd("implementation", "deadbeef", cwd=str(self.root))

        self.assertEqual(len(result["enqueued"]), 1)
        queue_path = self.root / patrol_queue.QUEUE_REL_PATH
        queue = patrol_queue.load_queue(queue_path)
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["lane"], "diff")
        self.assertEqual(queue[0]["scanner_id"], "judge:implementation")
        self.assertEqual(queue[0]["path"], "x.py")


if __name__ == "__main__":
    unittest.main()
