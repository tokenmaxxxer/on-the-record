"""이슈 #2152: 스폰 기본값 반전 — 아무 플래그도 없으면 이제 single-phase
(build-now, CORE_BUILD_NOW=1). --two-phase 가 오늘까지의 proposal-first
흐름으로 opt-in 한다. --single-phase 는 no-op 별칭(기본값이 이미 같은
결과)이고, --checkpoint 는 phase-1 제안 라운드에서 멈춰야 하므로 다른
플래그와 무관하게 언제나 two-phase 로 취급한다(기존 --checkpoint 테스트는
건드리지 않는다, tests/test_checkpoint_mode.py)."""
from _spawn_test_support import *  # noqa: F401,F403

_ROLE = "implementation"
_ISSUE = 31


def _spawn_main_with_argv(argv, extra_patches=()):
    calls = {}

    def fake_spawn_one(*a, **k):
        calls.update(k)
        return 0

    patches = [
        mock.patch.object(spawn, "_spawn_one", fake_spawn_one),
        mock.patch.object(spawn, "require_board", lambda *a, **k: None),
        mock.patch.object(spawn, "require_no_repo_config", lambda *a, **k: None),
        mock.patch.object(spawn, "require_acceptance_gate", lambda *a, **k: None),
        mock.patch.object(spawn, "require_requirement_linkage", lambda *a, **k: None),
        mock.patch.object(spawn, "require_doctor", lambda *a, **k: None),
        mock.patch.object(spawn, "ensure_target_remote", lambda *a, **k: None),
        mock.patch.object(sys, "argv", argv),
    ] + list(extra_patches)
    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        rc = spawn.main()
    return rc, calls


class DefaultFlipToSinglePhase(unittest.TestCase):
    def test_no_flags_defaults_to_single_phase(self):
        rc, calls = _spawn_main_with_argv(
            ["spawn.py", _ROLE, "task", "--issue", str(_ISSUE)])
        self.assertEqual(rc, 0)
        self.assertIs(calls.get("single_phase"), True)

    def test_two_phase_flag_opts_out_of_single_phase(self):
        rc, calls = _spawn_main_with_argv(
            ["spawn.py", _ROLE, "task", "--issue", str(_ISSUE), "--two-phase"])
        self.assertEqual(rc, 0)
        self.assertIs(calls.get("single_phase"), False)

    def test_single_phase_flag_is_a_noop_alias(self):
        """--single-phase 는 기본값이 이미 같은 결과라 값이 안 바뀐다."""
        rc, calls = _spawn_main_with_argv(
            ["spawn.py", _ROLE, "task", "--issue", str(_ISSUE), "--single-phase"])
        self.assertEqual(rc, 0)
        self.assertIs(calls.get("single_phase"), True)

    def test_checkpoint_forces_two_phase_regardless_of_default(self):
        """체크포인트는 phase-1 제안에서 멈춰야 하므로, 기본값이 반전돼도
        --checkpoint 는 언제나 single_phase=False 로 스폰한다."""
        rc, calls = _spawn_main_with_argv(
            ["spawn.py", _ROLE, "task", "--issue", str(_ISSUE), "--checkpoint"])
        self.assertEqual(rc, 0)
        self.assertIs(calls.get("checkpoint"), True)
        self.assertIs(calls.get("single_phase"), False)

    def test_checkpoint_with_explicit_two_phase_stays_false(self):
        rc, calls = _spawn_main_with_argv(
            ["spawn.py", _ROLE, "task", "--issue", str(_ISSUE), "--checkpoint",
             "--two-phase"])
        self.assertEqual(rc, 0)
        self.assertIs(calls.get("checkpoint"), True)
        self.assertIs(calls.get("single_phase"), False)


if __name__ == "__main__":
    unittest.main()
