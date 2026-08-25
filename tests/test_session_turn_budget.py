"""Issue #2262: approach-cap warning + wrap-up allowance instead of a hard
kill at the session turn cap.

Six sessions (2173/2186/2193/2204/2208/2240) died at the 200-turn
`--max-turns` cap mid-action with no warning and no terminal act. The
actual enforcement lives in the `claude` CLI itself, outside this repo;
the levers this repo controls are (a) the `--max-turns` value handed to
that CLI (`pipeline.py:spawn_cmd`) and (b) an in-session PreToolUse/
PostToolUse hook (`on-the-record/hooks/approach-cap-warning.sh`, covered
by its own live-fire test) that injects a converge-now warning before the
padded turns run out.

This file covers the pure resolution/wiring logic in spawn.py/pipeline.py:
- DEFAULT_SESSION_MAX_TURNS is untouched (the issue's "do not raise the
  cap as the primary fix" constraint) — the wrap-up allowance is an
  *additive* buffer on the CLI's `--max-turns` flag, never a change to
  the advertised/nominal cap.
- the wrap-up allowance and approach-warning threshold resolve from env
  with the documented defaults/overrides.
- `spawn_cmd()` widens the actual `--max-turns` flag by the allowance
  while passing the *nominal* (unwidened) cap and the warning threshold
  to the spawned session via env, so the in-session hook warns against
  the budget the session was told about, not the padded one.
- empty state (issue's acceptance): a spawn with no resolved turn budget
  (max_turns None or <= 0/unlimited) is byte-identical to pre-#2262 —
  no `--max-turns` flag, no new env vars, nothing for the in-session hook
  to act on.
"""
from _spawn_test_support import *  # noqa: F401,F403
import pipeline


class DefaultCapUnchanged(unittest.TestCase):
    def test_default_session_max_turns_is_still_200(self):
        # The issue's own ask #3: do not raise the default cap as the
        # primary fix — six cap-hits with 68/69 unique greps means the
        # budget is being spent, not looped.
        self.assertEqual(spawn.DEFAULT_SESSION_MAX_TURNS, 200)


class ResolverDefaultsAndOverrides(unittest.TestCase):
    def test_wrap_up_allowance_default(self):
        env = dict(os.environ)
        env.pop("MUSTER_WRAP_UP_ALLOWANCE_TURNS", None)
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(pipeline._resolve_wrap_up_allowance_turns(), 20)

    def test_wrap_up_allowance_env_override(self):
        with mock.patch.dict(os.environ, {"MUSTER_WRAP_UP_ALLOWANCE_TURNS": "5"}):
            self.assertEqual(pipeline._resolve_wrap_up_allowance_turns(), 5)

    def test_wrap_up_allowance_invalid_env_falls_back_to_default(self):
        with mock.patch.dict(os.environ,
                             {"MUSTER_WRAP_UP_ALLOWANCE_TURNS": "not-an-int"}):
            self.assertEqual(pipeline._resolve_wrap_up_allowance_turns(), 20)

    def test_approach_warning_turns_default(self):
        env = dict(os.environ)
        env.pop("MUSTER_APPROACH_WARNING_TURNS", None)
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(pipeline._resolve_approach_warning_turns(), 20)

    def test_approach_warning_turns_env_override(self):
        with mock.patch.dict(os.environ, {"MUSTER_APPROACH_WARNING_TURNS": "8"}):
            self.assertEqual(pipeline._resolve_approach_warning_turns(), 8)


class SpawnCmdWiring(unittest.TestCase):
    def _spawn_cmd(self, **kw):
        env = dict(os.environ)
        env["MUSTER_AGENT_GH_TOKEN"] = "dummy-token-no-network"
        with mock.patch.dict(os.environ, env):
            return spawn.spawn_cmd("settings.json", "implementation", True, **kw)

    def test_max_turns_flag_widened_by_wrap_up_allowance(self):
        with mock.patch.dict(os.environ, {"MUSTER_WRAP_UP_ALLOWANCE_TURNS": "20"}):
            cmd, env = self._spawn_cmd(max_turns=30)
        self.assertIn("--max-turns", cmd)
        self.assertEqual(cmd[cmd.index("--max-turns") + 1], "50")
        # the session itself is told the NOMINAL cap, not the padded one
        self.assertEqual(env["MUSTER_SESSION_MAX_TURNS_RESOLVED"], "30")

    def test_max_turns_flag_widened_by_overridden_allowance(self):
        with mock.patch.dict(os.environ, {"MUSTER_WRAP_UP_ALLOWANCE_TURNS": "5"}):
            cmd, env = self._spawn_cmd(max_turns=30)
        self.assertEqual(cmd[cmd.index("--max-turns") + 1], "35")
        self.assertEqual(env["MUSTER_SESSION_MAX_TURNS_RESOLVED"], "30")

    def test_approach_warning_turns_env_carried_to_session(self):
        with mock.patch.dict(os.environ, {"MUSTER_APPROACH_WARNING_TURNS": "8"}):
            _, env = self._spawn_cmd(max_turns=30)
        self.assertEqual(env["MUSTER_APPROACH_WARNING_TURNS"], "8")

    def test_unresolved_max_turns_is_byte_identical_to_before_2262(self):
        # Empty state (issue #2262 acceptance): no resolved budget -> no
        # --max-turns flag, no new env vars. Pre-existing callers that
        # never resolved a budget see no behavior change.
        cmd, env = self._spawn_cmd(max_turns=None)
        self.assertNotIn("--max-turns", cmd)
        self.assertNotIn("MUSTER_SESSION_MAX_TURNS_RESOLVED", env)
        self.assertNotIn("MUSTER_APPROACH_WARNING_TURNS", env)

    def test_unlimited_max_turns_is_untouched(self):
        # <= 0 means an explicit, admission-approved unlimited run (issue
        # #2100 item 4) -- the wrap-up allowance/warning threshold have
        # nothing to pad or warn against, so neither is set.
        cmd, env = self._spawn_cmd(max_turns=0)
        self.assertNotIn("--max-turns", cmd)
        self.assertNotIn("MUSTER_SESSION_MAX_TURNS_RESOLVED", env)
        self.assertNotIn("MUSTER_APPROACH_WARNING_TURNS", env)


if __name__ == "__main__":
    unittest.main()
