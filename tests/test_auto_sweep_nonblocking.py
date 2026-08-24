"""이슈 #2195: `auto_sweep` 이 실측 스폰에서 148.7s/154.3s(96%)를 먹었다 —
spawn-time housekeeping 이 세션 시작을 막을 이유가 없는데도 동기로 블로킹
경로에 있었다. 이 스위트는 두 가지를 함께 확인한다: (1) `auto_sweep` 이
느려도 `_spawn_one()`이 그 완료를 기다리지 않고(`auto_sweep` bootstrap
phase 가 짧게 끝나고) 진행한다, (2) 그럼에도 스윕 자체는 실제로 실행된다
(회귀 가드 — 그냥 지워진 게 아니라 경로/케이던스만 바뀌었다)."""
from _spawn_test_support import *  # noqa: F401,F403

_NO_SKILLS = {"source": "skill-repo", "skill_dirs": [], "skills": [],
              "skill_sha": None}

# 실측 148.7s 를 그대로 재현하진 않지만, "join 했다면 테스트가 이 시간만큼
# 멈춰 서야 한다"를 보이기에 충분한 값 — 회귀 시(다시 동기 join 이 되면)
# 테스트가 눈에 띄게 느려지거나 아래 elapsed 단언에서 실패한다.
_SLOW_SWEEP_SECONDS = 2.0


class AutoSweepNonBlocking(unittest.TestCase):
    def _prep_repo(self, td, name="work"):
        work = Path(td) / name
        work.mkdir()
        run = lambda *a: subprocess.run(a, cwd=str(work), capture_output=True,
                                        text=True, check=True)
        run("git", "init", "-q")
        run("git", "config", "user.email", "t@example.com")
        run("git", "config", "user.name", "t")
        (work / "f.txt").write_text("x")
        run("git", "add", "f.txt")
        run("git", "commit", "-q", "-m", "init")
        return work

    def setUp(self):
        self._old_roster = spawn.ROSTER
        self._old_idx = spawn.WORKSPACE_INDEX
        self._td = tempfile.TemporaryDirectory()
        spawn.ROSTER = Path(self._td.name) / "active.json"
        spawn.WORKSPACE_INDEX = Path(self._td.name) / "workspaces.json"

    def tearDown(self):
        spawn.ROSTER = self._old_roster
        spawn.WORKSPACE_INDEX = self._old_idx
        self._td.cleanup()

    @pytest.mark.slow
    def test_slow_auto_sweep_does_not_block_spawn_or_its_timed_phase(self):
        started = threading.Event()
        release = threading.Event()
        calls = []

        def slow_auto_sweep(wb, max_age_days, max_bytes):
            calls.append((wb, max_age_days, max_bytes))
            started.set()
            # 실측 148.7s 대신 release 될 때까지(또는 타임아웃까지) 막아 —
            # `_spawn_one` 이 이 함수의 완료를 기다린다면 아래 elapsed 단언이
            # 그 블로킹을 그대로 드러낸다.
            release.wait(_SLOW_SWEEP_SECONDS)
            # 실제 `auto_sweep()`과 같은 반환 shape(#2195 헌트: 백그라운드
            # 완료 시 이 값을 stderr 로 찍어야 한다 — 아래에서 확인).
            return {"removed": 3, "failed": 0}

        stderr_buf = io.StringIO()
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            real_roster_register = spawn.roster_register
            roster_calls = []

            def spy_roster_register(key, entry):
                roster_calls.append((key, dict(entry)))
                return real_roster_register(key, entry)

            spawn._BOOTSTRAP_TIMING.clear()
            t0 = time.monotonic()
            with contextlib.redirect_stderr(stderr_buf), \
                 mock.patch.object(spawn, "issue_workspace",
                                   lambda cwd, issue, role: str(work)), \
                 mock.patch.object(spawn, "checkout_issue_branch",
                                   lambda cwd, issue, role: "b"), \
                 mock.patch.object(spawn, "resolve_role_source",
                                   lambda role, repo_root: _NO_SKILLS), \
                 mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
                 mock.patch.object(spawn, "core_version", lambda: "v0"), \
                 mock.patch.object(spawn, "_clean_auto_enabled", lambda: True), \
                 mock.patch.object(spawn, "auto_sweep", slow_auto_sweep), \
                 mock.patch.object(spawn, "spawn_cmd",
                                   lambda *a, **k: (["cat"], {})), \
                 mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None), \
                 mock.patch.object(spawn, "_rewrite_spawn_claim_pid", lambda w: None), \
                 mock.patch.object(spawn, "_await_bounded", lambda *a, **k: 0), \
                 mock.patch.object(spawn, "_undispositioned_role_prs",
                                   lambda root, exclude_issue=None: ([], True)), \
                 mock.patch.object(spawn, "roster_register", spy_roster_register), \
                 mock.patch.object(spawn, "ledger_write", lambda *a, **k: None):
                rc = spawn._spawn_one(str(work), "implementation", "일.\n",
                                      unattended=True, issue=31, bounded=False,
                                      no_wait=True, single_phase=False)
                elapsed = time.monotonic() - t0

                self.assertEqual(rc, 0)
                # (1) 블로킹 경로에서 빠졌다: 스윕 함수가 2s 를 쥐고 있어도,
                # 정확히 이 지점을 재는 `auto_sweep` bootstrap phase 자체는
                # 짧다(디스패치만 쟀지, 완료를 기다리지 않았다) — 이 값이 곧
                # 이슈가 읽으라고 한 `bootstrap_timing` 줄의 `auto_sweep=`
                # 항목이다. (elapsed 는 참고용 — subprocess 스폰/로그 tee 등
                # 스윕과 무관한 오버헤드가 섞여 있어 정밀 단언에는 안 쓴다.)
                self.assertLess(
                    spawn._BOOTSTRAP_TIMING.get("auto_sweep", 0.0),
                    _SLOW_SWEEP_SECONDS / 2,
                    f"auto_sweep phase 가 스윕 완료를 기다린 것으로 보인다 "
                    f"(phase={spawn._BOOTSTRAP_TIMING.get('auto_sweep')}, "
                    f"elapsed={elapsed:.3f}s)")

                # (2) 회귀 가드: 스윕이 그냥 없어진 게 아니라 실제로
                # (백그라운드에서) 호출된다 — 새 케이던스/경로에서도 여전히
                # 돈다.
                self.assertTrue(started.wait(_SLOW_SWEEP_SECONDS),
                                 "auto_sweep 이 백그라운드에서도 호출되지 않았다")
                release.set()
                self.assertEqual(len(calls), 1)

                # (3) 회귀 가드(#2195 헌트 반영): 백그라운드 완료가 stderr 에서
                # 완전히 안 보이게 되진 않는다 — 걸린 시간/결과가 찍힌다.
                deadline = time.monotonic() + _SLOW_SWEEP_SECONDS
                while ("auto-sweep(백그라운드)" not in stderr_buf.getvalue()
                       and time.monotonic() < deadline):
                    time.sleep(0.02)

        self.assertIn("auto-sweep(백그라운드)", stderr_buf.getvalue())
        self.assertIn("지움 3", stderr_buf.getvalue())

    @pytest.mark.slow
    def test_auto_sweep_disabled_flag_still_skips_dispatch(self):
        """`MUSTER_CLEAN_AUTO` 끄기 계약(#1179)이 백그라운드 디스패치로
        바뀐 뒤에도 그대로 유지된다는 회귀 가드."""
        calls = []

        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)

            with mock.patch.object(spawn, "issue_workspace",
                                   lambda cwd, issue, role: str(work)), \
                 mock.patch.object(spawn, "checkout_issue_branch",
                                   lambda cwd, issue, role: "b"), \
                 mock.patch.object(spawn, "resolve_role_source",
                                   lambda role, repo_root: _NO_SKILLS), \
                 mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
                 mock.patch.object(spawn, "core_version", lambda: "v0"), \
                 mock.patch.object(spawn, "_clean_auto_enabled", lambda: False), \
                 mock.patch.object(spawn, "auto_sweep",
                                   lambda *a, **k: calls.append(1)), \
                 mock.patch.object(spawn, "spawn_cmd",
                                   lambda *a, **k: (["cat"], {})), \
                 mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None), \
                 mock.patch.object(spawn, "_rewrite_spawn_claim_pid", lambda w: None), \
                 mock.patch.object(spawn, "_await_bounded", lambda *a, **k: 0), \
                 mock.patch.object(spawn, "_undispositioned_role_prs",
                                   lambda root, exclude_issue=None: ([], True)), \
                 mock.patch.object(spawn, "ledger_write", lambda *a, **k: None):
                rc = spawn._spawn_one(str(work), "implementation", "일.\n",
                                      unattended=True, issue=31, bounded=False,
                                      no_wait=True, single_phase=False)

        self.assertEqual(rc, 0)
        time.sleep(0.2)  # 디스패치됐다면 데몬 스레드가 이미 돌았을 시간
        self.assertEqual(calls, [])
