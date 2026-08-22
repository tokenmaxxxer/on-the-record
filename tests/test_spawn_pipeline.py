from _spawn_test_support import *  # noqa: F401,F403


class SpawnCmd(unittest.TestCase):
    def test_flags(self):
        cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
        self.assertEqual(cmd[:2], ["claude", "-p"])
        self.assertIn("--settings", cmd)
        self.assertEqual(cmd[cmd.index("--settings") + 1], "/tmp/s.json")
        # issue #700 (2026-08-11): 샌드박스 제거 후 headless 는 승인 분류기에
        # allowlist 밖 명령이 전부 죽는다 — bypassPermissions 가 기본값이고,
        # 집행은 훅(PreToolUse exit 2)이 계속 맡는다.
        self.assertIn("bypassPermissions", cmd)
        self.assertEqual(cmd[cmd.index("--permission-mode") + 1], "bypassPermissions")
        # stream-json: 결과 이벤트 포착 + 라이브 로그 tee 둘 다 여기서 나온다.
        self.assertEqual(cmd[cmd.index("--output-format") + 1], "stream-json")

    def test_core_is_attached_by_path(self):
        # core carries the consent token format and the board gate. It rides
        # in as --plugin-dir, not as a second marketplace: a directory-loaded
        # plugin's hooks fire headless (measured 2026-07-27, CLI 2.1.220) and
        # nothing is installed, so the cache-vs-clone divergence and the
        # registry-name-wins trap never enter this path.
        cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False,
                                 core_plugins=["/x/tokenmaxxxer-core/core",
                                               "/x/tokenmaxxxer-core/terse"])
        dirs = [cmd[i + 1] for i, tok in enumerate(cmd) if tok == "--plugin-dir"]
        self.assertIn("/x/tokenmaxxxer-core/core", dirs)
        self.assertIn("/x/tokenmaxxxer-core/terse", dirs)

    def test_core_dir_resolves_or_halts(self):
        # A role session without core loses token forgery protection and the
        # contract-drift check silently. That is a halt, not a warning.
        # core_dir 이 보는 자리 **둘 다** 를 막아야 검사가 성립한다. 하나라도
        # 살려 두면 그 환경이 있는 머신에서만 통과하는 테스트가 된다 — 실제로
        # TOKENMAXXXER_RULEBOOKS 가 설정된 셸에서 이 케이스가 조용히 통과했다.
        saved = {k: os.environ.pop(k, None)
                 for k in ("TOKENMAXXXER_CORE", "TOKENMAXXXER_RULEBOOKS")}
        saved_root, spawn.ROOT = spawn.ROOT, Path("/nonexistent/muster")
        try:
            os.environ["TOKENMAXXXER_CORE"] = "/nonexistent/core"
            with self.assertRaises(SystemExit):
                spawn.core_root()
        finally:
            spawn.ROOT = saved_root
            os.environ.pop("TOKENMAXXXER_CORE", None)
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v

    def _core_checkout(self, td, plugin_names):
        # marketplace.json + plugin.json 을 갖춘 core 체크아웃 모양을
        # 흉내낸다 — 실제 tokenmaxxxer-core 와 같은 형태.
        root = Path(td)
        (root / ".claude-plugin").mkdir(parents=True)
        (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps({
            "name": "tokenmaxxxer-core",
            "plugins": [{"name": n, "source": f"./{n}"} for n in plugin_names],
        }))
        for n in plugin_names:
            d = root / n / ".claude-plugin"
            d.mkdir(parents=True, exist_ok=True)
            (d / "plugin.json").write_text(json.dumps({"name": n}))

    def test_core_plugin_dirs_pins_five_plugin_set(self):
        # 이슈#282: marketplace.json 이 5개(core, terse, freelunch, scout,
        # warrant)를 선언하면 core_plugin_dirs() 는 하드코드 튜플이 아니라
        # 그 5개 전부를 돌려줘야 한다 — warrant 가 빠지던 원래 버그의 회귀
        # 방지.
        names = ("core", "terse", "freelunch", "scout", "warrant")
        saved = {k: os.environ.pop(k, None)
                 for k in ("TOKENMAXXXER_CORE", "TOKENMAXXXER_RULEBOOKS")}
        try:
            with tempfile.TemporaryDirectory() as td:
                self._core_checkout(td, names)
                os.environ["TOKENMAXXXER_CORE"] = td
                dirs = spawn.core_plugin_dirs()
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v
                else:
                    os.environ.pop(k, None)
        self.assertEqual({p.name for p in dirs}, set(names))

    def test_core_plugin_dirs_halts_on_missing_plugin_dir(self):
        # marketplace.json 이 선언한 플러그인의 디렉터리가 없으면
        # core_plugin_dirs() 는 조용히 건너뛰지 않고 그 이름을 대며 halt
        # 한다 — 공유 게이트 장치가 빠지는 걸 경고 없이 넘기지 않는다.
        saved = {k: os.environ.pop(k, None)
                 for k in ("TOKENMAXXXER_CORE", "TOKENMAXXXER_RULEBOOKS")}
        try:
            with tempfile.TemporaryDirectory() as td:
                self._core_checkout(td, ("core", "terse"))
                root = Path(td)
                mkt = json.loads((root / ".claude-plugin" / "marketplace.json").read_text())
                mkt["plugins"].append({"name": "warrant", "source": "./warrant"})
                (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps(mkt))
                os.environ["TOKENMAXXXER_CORE"] = td
                with self.assertRaises(SystemExit) as cm:
                    spawn.core_plugin_dirs()
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v
                else:
                    os.environ.pop(k, None)
        self.assertIn("warrant", str(cm.exception))

    def test_core_root_prefers_managed_clone_over_sibling_directory(self):
        # 이슈#220: 형제 디렉터리(마켓플레이스 설치 부산물, ROOT.parent /
        # "tokenmaxxxer-core")가 관리 클론보다 먼저 매치되면 sha 비교 없이
        # 그대로 반환돼, 관리 클론(원격과 항상 동기화되는 유일한 경로)이
        # 영구히 도달 불가였다 — 후보 목록에서 형제 디렉터리를 제거한
        # 뒤에도 둘이 공존할 때 관리 클론이 선택되는지 회귀 확인.
        saved = {k: os.environ.pop(k, None)
                 for k in ("TOKENMAXXXER_CORE", "TOKENMAXXXER_RULEBOOKS")}
        try:
            with tempfile.TemporaryDirectory() as td:
                fake_root = Path(td) / "workspace"
                fake_root.mkdir()
                saved_root, spawn.ROOT = spawn.ROOT, fake_root
                try:
                    sibling = fake_root.parent / "tokenmaxxxer-core"
                    (sibling / "core" / ".claude-plugin").mkdir(parents=True)
                    (sibling / "core" / ".claude-plugin" / "plugin.json").write_text("{}")

                    managed = fake_root / "runs" / "rulebooks" / "tokenmaxxxer-core"
                    (managed / "core" / ".claude-plugin").mkdir(parents=True)
                    (managed / "core" / ".claude-plugin" / "plugin.json").write_text("{}")

                    self.assertEqual(spawn.core_root(), managed)
                finally:
                    spawn.ROOT = saved_root
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v

    @pytest.mark.slow
    def test_core_version_reports_managed_clone_sha_when_sibling_also_present(self):
        # 같은 공존 셋업에서 core_version() 도 관리 클론 쪽 sha·라벨을
        # 보고해야 core_root() 가 실제로 고르는 체크아웃과 로그가 일치한다
        # — 형제 디렉터리 쪽 sha 가 섞여 나오면 안 된다.
        saved = {k: os.environ.pop(k, None)
                 for k in ("TOKENMAXXXER_CORE", "TOKENMAXXXER_RULEBOOKS")}
        try:
            with tempfile.TemporaryDirectory() as td:
                fake_root = Path(td) / "workspace"
                fake_root.mkdir()
                saved_root, spawn.ROOT = spawn.ROOT, fake_root
                try:
                    def make_repo(d: Path, marker: str) -> str:
                        # marker 로 트리 내용을 다르게 해 두 저장소가 우연히
                        # 같은 커밋 해시를 갖는 것(같은 초 안에 동일 내용으로
                        # init 하면 발생)을 막는다.
                        (d / "core" / ".claude-plugin").mkdir(parents=True)
                        (d / "core" / ".claude-plugin" / "plugin.json").write_text(
                            json.dumps({"marker": marker}))

                        def git(*a: str) -> str:
                            r = subprocess.run(["git", "-C", str(d), *a],
                                               capture_output=True, text=True)
                            return r.stdout.strip()

                        git("init", "-q")
                        git("config", "user.email", "t@t.t")
                        git("config", "user.name", "t")
                        git("add", "-A")
                        git("commit", "-q", "-m", f"init-{marker}")
                        return git("rev-parse", "--short", "HEAD")

                    sibling = fake_root.parent / "tokenmaxxxer-core"
                    sibling_sha = make_repo(sibling, "sibling")

                    managed = fake_root / "runs" / "rulebooks" / "tokenmaxxxer-core"
                    managed_sha = make_repo(managed, "managed")

                    v = spawn.core_version()
                    self.assertIn(managed_sha, v)
                    self.assertIn("on-the-record 클론", v)
                    self.assertNotIn(sibling_sha, v)
                finally:
                    spawn.ROOT = saved_root
        finally:
            for k, val in saved.items():
                if val is not None:
                    os.environ[k] = val

    @pytest.mark.slow
    def test_core_version_reports_sha_date_and_label_for_local_override(self):
        # 이슈#218: core_root() 는 plugin.json 존재만 보고 sha·신선도는
        # 보지도 보고도 않는다 — core_version() 은 checkout_version() 의
        # core 쪽 대칭으로, 로컬 오버라이드(TOKENMAXXXER_CORE)가 실제로
        # 무슨 sha 를 물었는지 읽기 전용으로 드러낸다.
        with tempfile.TemporaryDirectory() as td:
            core_dir = Path(td) / "tokenmaxxxer-core"
            (core_dir / "core" / ".claude-plugin").mkdir(parents=True)
            (core_dir / "core" / ".claude-plugin" / "plugin.json").write_text("{}")

            def git(*a: str) -> str:
                r = subprocess.run(["git", "-C", str(core_dir), *a],
                                   capture_output=True, text=True)
                return r.stdout.strip()

            git("init", "-q")
            git("config", "user.email", "t@t.t")
            git("config", "user.name", "t")
            git("add", "-A")
            git("commit", "-q", "-m", "init")
            expected_sha = git("rev-parse", "--short", "HEAD")
            expected_date = git("log", "-1", "--format=%cs")

            saved = os.environ.get("TOKENMAXXXER_CORE")
            os.environ["TOKENMAXXXER_CORE"] = str(core_dir)
            try:
                v = spawn.core_version()
            finally:
                if saved is None:
                    os.environ.pop("TOKENMAXXXER_CORE", None)
                else:
                    os.environ["TOKENMAXXXER_CORE"] = saved
            self.assertIn(expected_sha, v)
            self.assertIn(expected_date, v)
            self.assertIn("TOKENMAXXXER_CORE", v)
            self.assertNotIn("커밋 안 된 변경", v)

    @pytest.mark.slow
    def test_core_version_reports_unknown_without_network_when_nothing_found(self):
        # 로컬 후보 둘 + 관리 클론까지 전부 없을 때 core_version() 은
        # core_root() 처럼 halt 하지 않고(로깅용이라 halt 는 core_root() 의
        # 몫), 그렇다고 core_root() 처럼 새로 clone 을 시도하지도 않는다.
        saved = {k: os.environ.pop(k, None)
                 for k in ("TOKENMAXXXER_CORE", "TOKENMAXXXER_RULEBOOKS")}
        saved_root = spawn.ROOT
        try:
            with tempfile.TemporaryDirectory() as broot:
                spawn.ROOT = Path(broot)
                with mock.patch("spawn.subprocess.run") as run:
                    v = spawn.core_version()
                self.assertIn("버전 불명", v)
                # 후보 전부 미스면 describe() 자체가 안 불려 위 mock 이 한
                # 번도 안 불린다 — "clone 이 없다" 는 이 경로에서 자명하다.
                # 진짜 위험은 관리 클론이 **있는** 경로(core_root() 는
                # 거기서 pull 을 돈다)인데, core_version() 은 거기서도
                # pull/clone 을 걸지 않는지를 아래서 실제 subprocess 호출을
                # 가로채 검사한다.
                run.assert_not_called()

                d = Path(broot) / "runs" / "rulebooks" / "tokenmaxxxer-core"
                (d / "core" / ".claude-plugin").mkdir(parents=True)
                (d / "core" / ".claude-plugin" / "plugin.json").write_text("{}")

                def git(*a: str) -> str:
                    r = subprocess.run(["git", "-C", str(d), *a], capture_output=True, text=True)
                    return r.stdout.strip()

                git("init", "-q")
                git("config", "user.email", "t@t.t")
                git("config", "user.name", "t")
                git("add", "-A")
                git("commit", "-q", "-m", "init")
                expected_sha = git("rev-parse", "--short", "HEAD")

                with mock.patch("spawn.subprocess.run", wraps=subprocess.run) as spied:
                    v2 = spawn.core_version()
                self.assertIn(expected_sha, v2)
                self.assertIn("on-the-record 클론", v2)
                for cmd in spied.call_args_list:
                    self.assertNotIn("pull", cmd.args[0], "core_version() 이 관리 클론을 pull 했다")
                    self.assertNotIn("clone", cmd.args[0], "core_version() 이 네트워크 clone 을 시도했다")
        finally:
            spawn.ROOT = saved_root
            for k, val in saved.items():
                if val is not None:
                    os.environ[k] = val

    def test_claude_plugin_root_core_matches_attached_core_dir(self):
        # 이슈#182: 룰북 게이트는 core 공유 라이브러리를
        # ${CLAUDE_PLUGIN_ROOT_CORE:-<상대경로>/core} 로 참조한다. 이 변수가
        # 없으면 상대 fallback 이 룰북 클론 내부를 가리켜 실배포에서 해석
        # 실패 → 게이트 전면 fail-open. 주입된 경로는 --plugin-dir 로 실제
        # 로드되는 core 플러그인 경로와 문자열까지 정확히 일치해야 한다.
        _, env = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False,
                                  core_plugins=["/x/tokenmaxxxer-core/core",
                                                "/x/tokenmaxxxer-core/terse"])
        self.assertEqual(env["CLAUDE_PLUGIN_ROOT_CORE"], "/x/tokenmaxxxer-core/core")

    def test_claude_plugin_root_core_unset_without_core_plugin(self):
        # core 가 결손 상태(plugin.json 없음)여서 core_plugin_dirs() 목록에서
        # 아예 빠지면 변수를 주입하지 않는다 — 조용히 fallback 에 빠지게
        # 두지 않고 stderr 경고로 드러낸다.
        _, env = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False,
                                  core_plugins=["/x/tokenmaxxxer-core/terse"])
        self.assertNotIn("CLAUDE_PLUGIN_ROOT_CORE", env)

    def test_env_stamps(self):
        # D1: 스폰된 세션의 UserPromptSubmit 은 오케스트레이터가 쓴 텍스트다.
        # 그 턴이 사람 턴으로 오인되어 mint 되는 일이 없도록 도장을 찍는다.
        _, env = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
        self.assertEqual(env["CLAUDE_ROLE"], "execution-observation")
        self.assertEqual(env["TOKENMAXXXER_SPAWNED"], "1")
        self.assertNotIn("TOKENMAXXXER_UNATTENDED", env)

    def test_unattended_is_separate(self):
        # SPAWNED(사람 턴 아님)와 UNATTENDED(사람 부재)는 다른 사실이다.
        # 겹쳐 쓰면 attended 스폰이 깨진다.
        _, env = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=True)
        self.assertEqual(env["TOKENMAXXXER_UNATTENDED"], "1")
        self.assertEqual(env["TOKENMAXXXER_SPAWNED"], "1")

    def test_role_model_unset_uses_builtin_default(self):
        # 이슈#93: MUSTER_ROLE_MODEL/config 둘 다 미설정이면 built-in
        # "sonnet" 이 --model 로 붙는다.
        saved = os.environ.pop("MUSTER_ROLE_MODEL", None)
        try:
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
            self.assertIn("--model", cmd)
            self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")
        finally:
            if saved is not None:
                os.environ["MUSTER_ROLE_MODEL"] = saved

    def test_role_model_set_appends_flag(self):
        # MUSTER_ROLE_MODEL 설정 시 --model <value> 가 argv 에 붙는다.
        saved = os.environ.get("MUSTER_ROLE_MODEL")
        try:
            os.environ["MUSTER_ROLE_MODEL"] = "sonnet"
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
            self.assertIn("--model", cmd)
            self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")
        finally:
            if saved is None:
                os.environ.pop("MUSTER_ROLE_MODEL", None)
            else:
                os.environ["MUSTER_ROLE_MODEL"] = saved

    def test_role_model_whitespace_only_uses_builtin_default(self):
        # 이슈#35+#93: 공백만 있는 MUSTER_ROLE_MODEL 은 미설정과 동일하게
        # 취급되어 built-in "sonnet" 이 붙는다 - "--model '   '" 은 안 된다.
        saved = os.environ.get("MUSTER_ROLE_MODEL")
        try:
            os.environ["MUSTER_ROLE_MODEL"] = "   "
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
            self.assertIn("--model", cmd)
            self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")
        finally:
            if saved is None:
                os.environ.pop("MUSTER_ROLE_MODEL", None)
            else:
                os.environ["MUSTER_ROLE_MODEL"] = saved

    def test_role_model_config_only_appends_flag(self):
        # 이슈#60: MUSTER_ROLE_MODEL 미설정, role_model.txt 만 있으면
        # --model <config value> 가 argv 에 붙는다.
        saved_env = os.environ.pop("MUSTER_ROLE_MODEL", None)
        saved_cfg = spawn.ROLE_MODEL_CONFIG.read_text() if spawn.ROLE_MODEL_CONFIG.is_file() else None
        try:
            spawn.ROLE_MODEL_CONFIG.write_text("sonnet")
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
            self.assertIn("--model", cmd)
            self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")
        finally:
            if saved_cfg is None:
                spawn.ROLE_MODEL_CONFIG.unlink(missing_ok=True)
            else:
                spawn.ROLE_MODEL_CONFIG.write_text(saved_cfg)
            if saved_env is not None:
                os.environ["MUSTER_ROLE_MODEL"] = saved_env

    def test_role_model_env_overrides_config(self):
        # 이슈#60: 둘 다 설정되면 env 값이 이긴다.
        saved_env = os.environ.get("MUSTER_ROLE_MODEL")
        saved_cfg = spawn.ROLE_MODEL_CONFIG.read_text() if spawn.ROLE_MODEL_CONFIG.is_file() else None
        try:
            spawn.ROLE_MODEL_CONFIG.write_text("haiku")
            os.environ["MUSTER_ROLE_MODEL"] = "opus"
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
            self.assertEqual(cmd[cmd.index("--model") + 1], "opus")
        finally:
            if saved_cfg is None:
                spawn.ROLE_MODEL_CONFIG.unlink(missing_ok=True)
            else:
                spawn.ROLE_MODEL_CONFIG.write_text(saved_cfg)
            if saved_env is None:
                os.environ.pop("MUSTER_ROLE_MODEL", None)
            else:
                os.environ["MUSTER_ROLE_MODEL"] = saved_env

    def test_role_model_whitespace_only_config_uses_builtin_default(self):
        # 이슈#60+#93: 공백만 있는 config 값도 미설정과 동일하게 취급되어
        # built-in "sonnet" 이 붙는다.
        saved_env = os.environ.pop("MUSTER_ROLE_MODEL", None)
        saved_cfg = spawn.ROLE_MODEL_CONFIG.read_text() if spawn.ROLE_MODEL_CONFIG.is_file() else None
        try:
            spawn.ROLE_MODEL_CONFIG.write_text("   ")
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
            self.assertIn("--model", cmd)
            self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")
        finally:
            if saved_cfg is None:
                spawn.ROLE_MODEL_CONFIG.unlink(missing_ok=True)
            else:
                spawn.ROLE_MODEL_CONFIG.write_text(saved_cfg)
            if saved_env is not None:
                os.environ["MUSTER_ROLE_MODEL"] = saved_env

    def test_role_model_non_utf8_config_uses_builtin_default(self):
        # 이슈#60+#93: role_model.txt 가 UTF-8 이 아니면 read_role_model_config()
        # 는 (docstring 대로) 미설정처럼 "" 를 돌려주고, resolved_role_model()
        # 은 built-in "sonnet" 으로 떨어진다 — 스폰이 UnicodeDecodeError 로
        # 죽으면 안 된다.
        saved_env = os.environ.pop("MUSTER_ROLE_MODEL", None)
        saved_cfg = spawn.ROLE_MODEL_CONFIG.read_text() if spawn.ROLE_MODEL_CONFIG.is_file() else None
        try:
            spawn.ROLE_MODEL_CONFIG.write_bytes(b"\xff\xfe\x00\x01")
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
            self.assertIn("--model", cmd)
            self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")
        finally:
            if saved_cfg is None:
                spawn.ROLE_MODEL_CONFIG.unlink(missing_ok=True)
            else:
                spawn.ROLE_MODEL_CONFIG.write_text(saved_cfg)
            if saved_env is not None:
                os.environ["MUSTER_ROLE_MODEL"] = saved_env

    def test_role_model_no_config_file_uses_builtin_default(self):
        # 이슈#60+#93: role_model.txt 자체가 없으면 미설정과 동일하게 취급되어
        # built-in "sonnet" 이 붙는다.
        saved_env = os.environ.pop("MUSTER_ROLE_MODEL", None)
        saved_cfg = spawn.ROLE_MODEL_CONFIG.read_text() if spawn.ROLE_MODEL_CONFIG.is_file() else None
        try:
            spawn.ROLE_MODEL_CONFIG.unlink(missing_ok=True)
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
            self.assertIn("--model", cmd)
            self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")
        finally:
            if saved_cfg is not None:
                spawn.ROLE_MODEL_CONFIG.write_text(saved_cfg)
            if saved_env is not None:
                os.environ["MUSTER_ROLE_MODEL"] = saved_env

    def test_resolved_role_model_builtin_default_is_sonnet(self):
        # 이슈#93: env, config 둘 다 없으면 resolved_role_model() 은 "sonnet"
        # 을 직접 돌려준다 — never no --model.
        saved_env = os.environ.pop("MUSTER_ROLE_MODEL", None)
        saved_cfg = spawn.ROLE_MODEL_CONFIG.read_text() if spawn.ROLE_MODEL_CONFIG.is_file() else None
        try:
            spawn.ROLE_MODEL_CONFIG.unlink(missing_ok=True)
            self.assertEqual(spawn.resolved_role_model(), "sonnet")
        finally:
            if saved_cfg is not None:
                spawn.ROLE_MODEL_CONFIG.write_text(saved_cfg)
            if saved_env is not None:
                os.environ["MUSTER_ROLE_MODEL"] = saved_env

    def test_role_model_does_not_affect_haiku_probe(self):
        # doctor() 의 haiku 프로브는 spawn_cmd 를 거치지 않는다 - 소스에서
        # 하드코딩된 "--model", "haiku" 가 여전히 남아 있는지 직접 확인한다.
        saved = os.environ.get("MUSTER_ROLE_MODEL")
        try:
            os.environ["MUSTER_ROLE_MODEL"] = "sonnet"
            src = Path(spawn.__file__).read_text()
            self.assertIn('"--model", "haiku"', src)
        finally:
            if saved is None:
                os.environ.pop("MUSTER_ROLE_MODEL", None)
            else:
                os.environ["MUSTER_ROLE_MODEL"] = saved

class DryRunModelReflection(unittest.TestCase):
    """--dry-run 은 spawn_cmd 를 안 거치므로(세션을 안 띄우니까) 이슈#31
    acceptance 커맨드(MUSTER_ROLE_MODEL=... --dry-run)가 실제로 뭔가
    보여주는지는 main() 의 dry-run 분기가 role_settings() 출력에 model 을
    얹는지에 달려 있다 — 여기서 그 분기를 직접 재현해 검사한다
    (docs/reports/2026-07-29-hunt-muster-role-model-build.md).
    """

    @staticmethod
    def _dry_run_output(role: str) -> dict:
        out = spawn.role_settings(role)
        role_model = spawn.resolved_role_model()
        if role_model:
            out["model"] = role_model
        return out

    def test_unset_output_reflects_builtin_default(self):
        saved = os.environ.pop("MUSTER_ROLE_MODEL", None)
        try:
            out = self._dry_run_output("execution-observation")
            self.assertEqual(out.get("model"), "sonnet")
        finally:
            if saved is not None:
                os.environ["MUSTER_ROLE_MODEL"] = saved

    def test_set_output_reflects_model(self):
        saved = os.environ.get("MUSTER_ROLE_MODEL")
        try:
            os.environ["MUSTER_ROLE_MODEL"] = "sonnet"
            out = self._dry_run_output("execution-observation")
            self.assertEqual(out.get("model"), "sonnet")
        finally:
            if saved is None:
                os.environ.pop("MUSTER_ROLE_MODEL", None)
            else:
                os.environ["MUSTER_ROLE_MODEL"] = saved

    def test_whitespace_only_output_reflects_builtin_default(self):
        # 이슈#35+#93: --dry-run 경로도 공백만 있는 값을 미설정처럼 취급해
        # built-in "sonnet" 을 반영한다.
        saved = os.environ.get("MUSTER_ROLE_MODEL")
        try:
            os.environ["MUSTER_ROLE_MODEL"] = "   "
            out = self._dry_run_output("execution-observation")
            self.assertEqual(out.get("model"), "sonnet")
        finally:
            if saved is None:
                os.environ.pop("MUSTER_ROLE_MODEL", None)
            else:
                os.environ["MUSTER_ROLE_MODEL"] = saved

    def test_config_only_output_reflects_model(self):
        # 이슈#60: env 없이 role_model.txt 만 있어도 dry-run 출력이 반영한다.
        saved_env = os.environ.pop("MUSTER_ROLE_MODEL", None)
        saved_cfg = spawn.ROLE_MODEL_CONFIG.read_text() if spawn.ROLE_MODEL_CONFIG.is_file() else None
        try:
            spawn.ROLE_MODEL_CONFIG.write_text("sonnet")
            out = self._dry_run_output("execution-observation")
            self.assertEqual(out.get("model"), "sonnet")
        finally:
            if saved_cfg is None:
                spawn.ROLE_MODEL_CONFIG.unlink(missing_ok=True)
            else:
                spawn.ROLE_MODEL_CONFIG.write_text(saved_cfg)
            if saved_env is not None:
                os.environ["MUSTER_ROLE_MODEL"] = saved_env

class WorkspaceSyncFailClosed(unittest.TestCase):
    """issue #221: fetch fail-closed + 재사용 브랜치 origin 트래킹 실 git 회귀.

    mock.patch.object 로 issue_workspace/checkout_issue_branch 를 대체하는
    기존 Ledger/IssueScopedPrompt/EventReporting 테스트들과 달리, 여기는 실
    git 저장소 두 개(origin 역할 + 그걸 clone 한 work_dir)로 함수 자체의
    동작을 검사한다.
    """

    def _git(self, cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a],
                              capture_output=True, text=True)

    def _init_repo(self, path):
        path.mkdir(parents=True, exist_ok=True)
        self._git(path, "init", "-q")
        self._git(path, "config", "user.email", "t@t.t")
        self._git(path, "config", "user.name", "t")

    def test_fetch_halts_on_nonzero_returncode(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            self._init_repo(work)
            (work / "a.txt").write_text("x")
            self._git(work, "add", "a.txt")
            self._git(work, "commit", "-q", "-m", "init")
            # 존재하지 않는 origin 경로 — 실제 fetch 가 non-zero 로 실패한다.
            self._git(work, "remote", "add", "origin", "/no/such/path-xyz")
            with self.assertRaises(SystemExit):
                spawn._fetch_or_halt(str(work), "test-label")

    def test_fetch_halts_on_exit_zero_with_failed_to_store_stderr(self):
        # core issue-90 실측 재현: fetch 가 stderr 에 "failed to store"를
        # 남기고도 exit 0 으로 끝나는 케이스는 실 git 으로 결정론적으로
        # 재현할 수 없어(개별 ref 갱신 실패는 레이스/서버 상태 의존), fetch
        # 를 가로채는 실행 가능한 wrapper 로 그 정확한 관측 결과(stdout
        # 없음, stderr 에 그 문구, returncode 0)를 만든다 — 이 프로세스가
        # 실제로 실행되고 실제로 반환하는 실 subprocess 호출이라는 점에서
        # Python mock 과 다르다.
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            self._init_repo(work)
            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            git_wrapper = fake_bin / "git"
            git_wrapper.write_text(
                "#!/bin/sh\n"
                "for a in \"$@\"; do\n"
                "  if [ \"$a\" = fetch ]; then\n"
                "    echo 'failed to store: 100001' 1>&2\n"
                "    exit 0\n"
                "  fi\n"
                "done\n"
                "exit 1\n"
            )
            git_wrapper.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            try:
                with self.assertRaises(SystemExit):
                    spawn._fetch_or_halt(str(work), "test-label")
            finally:
                os.environ["PATH"] = old_path

    @pytest.mark.slow
    def test_set_head_attempted_even_when_fresh_clone_fetch_fails(self):
        # hunt 발견(composition-regression stance): _fetch_or_halt 가 halt
        # 하기 전에 after=(remote set-head) 를 먼저 시도하지 않으면, 신규
        # clone 의 첫 fetch 가 실패할 때마다 origin/HEAD 정정 기회를 영영
        # 잃는다 — 재사용 분기는 set-head 를 다시 안 부른다. fetch 만
        # 실패시키고 나머지(clone/remote/set-head)는 real git 에 위임하는
        # wrapper 로, halt 되고도 set-head 는 실제로 실행됐는지 검사한다.
        real_git = shutil.which("git")
        self.assertIsNotNone(real_git)
        with tempfile.TemporaryDirectory() as td:
            github = Path(td) / "github"
            src = Path(td) / "src"
            self._init_repo(github)
            (github / "a.txt").write_text("x")
            self._git(github, "add", "a.txt")
            self._git(github, "commit", "-q", "-m", "init")
            self._git(github, "branch", "-m", "main")

            r = subprocess.run(["git", "clone", "-q", str(github), str(src)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(src, "config", "user.email", "t@t.t")
            self._git(src, "config", "user.name", "t")
            self._git(src, "checkout", "-q", "-b", "feature-wip")

            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            git_wrapper = fake_bin / "git"
            git_wrapper.write_text(
                "#!/bin/sh\n"
                "for a in \"$@\"; do\n"
                "  if [ \"$a\" = fetch ]; then\n"
                "    echo 'failed to store: 100001' 1>&2\n"
                "    exit 0\n"
                "  fi\n"
                "done\n"
                f"exec {real_git} \"$@\"\n"
            )
            git_wrapper.chmod(0o755)

            work_base = Path(td) / "workbase"
            old_path = os.environ.get("PATH", "")
            old_base = os.environ.get("MUSTER_WORK_DIR")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            os.environ["MUSTER_WORK_DIR"] = str(work_base)
            try:
                with self.assertRaises(SystemExit):
                    spawn.issue_workspace(str(src), 999904, "implementation")
            finally:
                os.environ["PATH"] = old_path
                if old_base is None:
                    os.environ.pop("MUSTER_WORK_DIR", None)
                else:
                    os.environ["MUSTER_WORK_DIR"] = old_base

            work_dirs = list(work_base.glob("*-issue-999904-implementation"))
            self.assertEqual(len(work_dirs), 1, work_dirs)
            head = subprocess.run(
                ["git", "-C", str(work_dirs[0]), "symbolic-ref", "--short",
                 "refs/remotes/origin/HEAD"],
                capture_output=True, text=True).stdout.strip()
            self.assertEqual(head, "origin/main")

    @pytest.mark.slow
    def test_checkout_tracks_origin_only_branch(self):
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("base")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "base commit")
            base_branch = subprocess.run(
                ["git", "-C", str(origin), "symbolic-ref", "--short", "HEAD"],
                capture_output=True, text=True).stdout.strip()

            issue, role = 999901, "implementation"
            br = f"issue-{issue}/{role}"
            self._git(origin, "checkout", "-q", "-b", br)
            (origin / "b.txt").write_text("origin-only work")
            self._git(origin, "add", "b.txt")
            self._git(origin, "commit", "-q", "-m", "origin-only commit")
            self._git(origin, "checkout", "-q", base_branch)

            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")

            # 사전 조건: 로컬엔 아직 br 브랜치가 없다.
            self.assertNotEqual(
                self._git(work, "rev-parse", "--verify", "-q", br).returncode, 0)

            result = spawn.checkout_issue_branch(str(work), issue, role)
            self.assertEqual(result, br)
            log = self._git(work, "log", "--oneline", br).stdout
            self.assertIn("origin-only commit", log)

    @pytest.mark.slow
    def test_checkout_preserves_existing_local_branch_with_unpushed_commit(self):
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("base")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "base commit")
            base_branch = subprocess.run(
                ["git", "-C", str(origin), "symbolic-ref", "--short", "HEAD"],
                capture_output=True, text=True).stdout.strip()

            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")

            issue, role = 999902, "implementation"
            br = f"issue-{issue}/{role}"
            self._git(work, "checkout", "-q", "-b", br)
            (work / "c.txt").write_text("local wip")
            self._git(work, "add", "c.txt")
            self._git(work, "commit", "-q", "-m", "local unpushed commit")
            self._git(work, "checkout", "-q", base_branch)
            before = self._git(work, "rev-parse", br).stdout.strip()

            result = spawn.checkout_issue_branch(str(work), issue, role)
            self.assertEqual(result, br)
            after = self._git(work, "rev-parse", br).stdout.strip()
            self.assertEqual(before, after)
            log = self._git(work, "log", "--oneline", br).stdout
            self.assertIn("local unpushed commit", log)

    @pytest.mark.slow
    def test_checkout_starts_fresh_on_stale_branch_merged_into_base(self):
        # issue-441 shape: a reused workspace's local issue-<n>/<role>
        # branch is fully absorbed into base (merged + --delete-branch
        # removed only the remote ref) — checkout must not resume it as-is,
        # it must delete the stale local ref and branch fresh from base, so
        # a subsequent commit + ensure_pushed() has something to push
        # instead of hitting GitHub's "No commits between main and
        # issue-<n>/<role>".
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("base")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "base commit")
            base_branch = subprocess.run(
                ["git", "-C", str(origin), "symbolic-ref", "--short", "HEAD"],
                capture_output=True, text=True).stdout.strip()

            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")

            issue, role = 999903, "implementation"
            br = f"issue-{issue}/{role}"
            # phase-1 round happened, merged into base, remote branch
            # deleted by --delete-branch — but the reused clone's local
            # branch ref survives untouched (the actual issue-428 fault).
            self._git(work, "checkout", "-q", "-b", br)
            (work / "phase1.txt").write_text("phase 1 work")
            self._git(work, "add", "phase1.txt")
            self._git(work, "commit", "-q", "-m", "phase 1 commit")
            # simulate: PR merged (br's commit lands on base at origin),
            # remote branch deleted by --delete-branch — via fetch-as-push
            # into origin's local base_branch ref (git refuses fetching
            # into the currently-checked-out branch, so detach first).
            self._git(origin, "checkout", "-q", "--detach")
            self._git(origin, "fetch", "-q", str(work), f"{br}:{base_branch}")
            self._git(origin, "checkout", "-q", base_branch)
            self._git(work, "checkout", "-q", base_branch)
            self._git(work, "fetch", "-q", "origin")
            self._git(work, "checkout", "-q", br)
            # sanity: the stale local branch is 0-ahead of base right now.
            self.assertEqual(
                self._git(work, "rev-list", "--count", f"origin/{base_branch}..{br}")
                .stdout.strip(),
                "0")

            result = spawn.checkout_issue_branch(str(work), issue, role)
            self.assertEqual(result, br)
            head = self._git(work, "symbolic-ref", "--short", "HEAD").stdout.strip()
            self.assertEqual(head, br)
            self.assertEqual(
                self._git(work, "rev-list", "--count", f"origin/{base_branch}..{br}")
                .stdout.strip(),
                "0")
            self.assertEqual(
                self._git(work, "rev-parse", br).stdout.strip(),
                self._git(work, "rev-parse", f"origin/{base_branch}").stdout.strip())

            (work / "phase2.txt").write_text("phase 2 work")
            self._git(work, "add", "phase2.txt")
            self._git(work, "commit", "-q", "-m", "phase 2 commit")
            self.assertNotEqual(
                self._git(work, "rev-list", "--count", f"origin/{base_branch}..{br}")
                .stdout.strip(),
                "0")

    @pytest.mark.slow
    def test_checkout_starts_fresh_on_general_stale_zero_ahead_branch(self):
        # General mechanism case (independent of which issue first exposed
        # it, per #428 survey's own issue-999 fixture): a local branch that
        # is exactly base (0 commits ahead) must be replaced with a fresh
        # branch from base rather than checked out as-is.
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("base")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "base commit")
            base_branch = subprocess.run(
                ["git", "-C", str(origin), "symbolic-ref", "--short", "HEAD"],
                capture_output=True, text=True).stdout.strip()

            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")

            issue, role = 999, "implementation"
            br = f"issue-{issue}/{role}"
            # A local branch that never diverged from base at all —
            # zero-ahead from the start, no merge history involved.
            self._git(work, "checkout", "-q", "-b", br, base_branch)

            result = spawn.checkout_issue_branch(str(work), issue, role)
            self.assertEqual(result, br)
            head = self._git(work, "symbolic-ref", "--short", "HEAD").stdout.strip()
            self.assertEqual(head, br)
            self.assertEqual(
                self._git(work, "rev-list", "--count", f"origin/{base_branch}..{br}")
                .stdout.strip(),
                "0")


    @pytest.mark.slow
    def test_checkout_tracks_origin_instead_of_recut_when_locally_stale_only(self):
        # 이슈 #719: 로컬 `base..br` 은 0(흡수된 것처럼 보임)이지만
        # `origin/br` 은 base 보다 앞서 있는 경우 — 다른 워크스페이스가 이미
        # 그 브랜치에 push 해 뒀는데 이 워크스페이스의 로컬 ref 만 뒤처진
        # 상황. base 로 재컷하면 그 커밋을 조용히 버리므로, 대신
        # origin/br 을 따라가야 한다.
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("base")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "base commit")
            base_branch = subprocess.run(
                ["git", "-C", str(origin), "symbolic-ref", "--short", "HEAD"],
                capture_output=True, text=True).stdout.strip()

            issue, role = 999905, "implementation"
            br = f"issue-{issue}/{role}"
            # origin 에 br 을 만들고 base 를 앞서는 커밋을 얹는다(다른
            # 워크스페이스가 이미 push 해 둔 상태를 흉내낸다).
            self._git(origin, "checkout", "-q", "-b", br)
            (origin / "other-workspace.txt").write_text("pushed elsewhere")
            self._git(origin, "add", "other-workspace.txt")
            self._git(origin, "commit", "-q", "-m", "pushed from another workspace")
            self._git(origin, "checkout", "-q", base_branch)

            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")
            # 이 워크스페이스는 아직 원격이 br 을 갖기 전에 로컬 br 을 만들어
            # base 와 정확히 같게(0-ahead) 남긴다 — clone 뒤 origin/br 은
            # 이미 fetch 됐지만, 로컬 br 은 fetch 로 갱신되지 않는다.
            self._git(work, "checkout", "-q", "-b", br, base_branch)
            self.assertEqual(
                self._git(work, "rev-list", "--count", f"{base_branch}..{br}")
                .stdout.strip(), "0")
            remote_commit = self._git(
                work, "rev-parse", f"origin/{br}").stdout.strip()

            result = spawn.checkout_issue_branch(str(work), issue, role)

            self.assertEqual(result, br)
            after = self._git(work, "rev-parse", br).stdout.strip()
            self.assertEqual(after, remote_commit,
                             "재컷이 origin 에 이미 push 된 커밋을 버렸다")

    @pytest.mark.slow
    def test_checkout_recuts_when_truly_fully_absorbed_local_and_remote(self):
        # empty state: 로컬·원격 모두 0-ahead(진짜 완전 흡수) → 오늘과 동일하게
        # base 에서 새로 판다.
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("base")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "base commit")
            base_branch = subprocess.run(
                ["git", "-C", str(origin), "symbolic-ref", "--short", "HEAD"],
                capture_output=True, text=True).stdout.strip()

            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")

            issue, role = 999906, "implementation"
            br = f"issue-{issue}/{role}"
            self._git(work, "checkout", "-q", "-b", br, base_branch)
            base_commit = self._git(work, "rev-parse", base_branch).stdout.strip()

            result = spawn.checkout_issue_branch(str(work), issue, role)

            self.assertEqual(result, br)
            after = self._git(work, "rev-parse", br).stdout.strip()
            self.assertEqual(after, base_commit)

    @pytest.mark.slow
    def test_checkout_recuts_absorbed_branch_and_preserves_untracked_files(self):
        # 이슈 #732: 로컬 br 이 base 에 완전히 흡수됐고(0-ahead) 워크스페이스에
        # untracked 파일만 있는 경우(커밋된 고유 작업 없음) — 재컷 전에
        # 파일을 stash 로 보존했다가 재컷된 새 브랜치 위에 다시 풀어야 한다.
        # base 트리에 이미 있는 경로와 충돌하는 untracked 파일도 포함해
        # `checkout -B` 가 실패하는 재현 시나리오를 함께 검증한다.
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("base")
            (origin / "colliding.txt").write_text("from base tree")
            self._git(origin, "add", "a.txt", "colliding.txt")
            self._git(origin, "commit", "-q", "-m", "base commit")
            base_branch = subprocess.run(
                ["git", "-C", str(origin), "symbolic-ref", "--short", "HEAD"],
                capture_output=True, text=True).stdout.strip()

            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")

            issue, role = 999907, "implementation"
            br = f"issue-{issue}/{role}"
            self._git(work, "checkout", "-q", "-b", br, base_branch)
            base_commit = self._git(work, "rev-parse", base_branch).stdout.strip()
            (work / "scratch-work.txt").write_text("uncommitted, untracked")
            (work / "colliding.txt").write_text("untracked version, collides with base")

            result = spawn.checkout_issue_branch(str(work), issue, role)

            self.assertEqual(result, br)
            after = self._git(work, "rev-parse", br).stdout.strip()
            self.assertEqual(after, base_commit,
                             "재컷된 브랜치가 base 팁과 일치해야 한다")
            self.assertEqual((work / "scratch-work.txt").read_text(),
                             "uncommitted, untracked",
                             "untracked 작업이 재컷 뒤 새 브랜치에 남아있어야 한다")
            self.assertEqual((work / "colliding.txt").read_text(),
                             "untracked version, collides with base",
                             "충돌하는 untracked 파일도 보존돼야 한다")
            status = self._git(work, "status", "--porcelain").stdout
            self.assertIn("scratch-work.txt", status)
            self.assertEqual(
                self._git(work, "stash", "list").stdout.strip(), "",
                "성공한 재컷 뒤엔 stash 가 남아있으면 안 된다")

    @pytest.mark.slow
    def test_checkout_recovers_leftover_stash_from_interrupted_recut(self):
        # 이전 실행이 stash push 와 pop 사이에서 중단됐다고 가정 — stash 는
        # `git status --porcelain`에 안 보이므로, 이번 호출이 먼저 그걸
        # 회수해야 다음 clean 의 보존 가드가 숨은 작업을 놓치지 않는다.
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("base")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "base commit")
            base_branch = subprocess.run(
                ["git", "-C", str(origin), "symbolic-ref", "--short", "HEAD"],
                capture_output=True, text=True).stdout.strip()

            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")

            issue, role = 999908, "implementation"
            br = f"issue-{issue}/{role}"
            self._git(work, "checkout", "-q", "-b", br, base_branch)
            base_commit = self._git(work, "rev-parse", base_branch).stdout.strip()
            (work / "leftover.txt").write_text("stashed by an interrupted prior run")
            stash_marker = f"checkout_issue_branch-preserve-{br}"
            stash_r = self._git(work, "stash", "push", "-u", "-q", "-m", stash_marker)
            self.assertEqual(stash_r.returncode, 0, stash_r.stderr)
            self.assertFalse((work / "leftover.txt").exists())
            self.assertEqual(self._git(work, "status", "--porcelain").stdout.strip(),
                             "", "stash 뒤엔 working tree 가 깨끗해야 한다")

            result = spawn.checkout_issue_branch(str(work), issue, role)

            self.assertEqual(result, br)
            after = self._git(work, "rev-parse", br).stdout.strip()
            self.assertEqual(after, base_commit)
            self.assertEqual((work / "leftover.txt").read_text(),
                             "stashed by an interrupted prior run",
                             "중단된 실행이 남긴 stash 가 복구돼야 한다")
            self.assertEqual(
                self._git(work, "stash", "list").stdout.strip(), "",
                "복구 뒤엔 stash 가 남아있으면 안 된다")

    @pytest.mark.slow
    def test_checkout_preserves_workspace_unchanged_when_commits_ahead(self):
        # empty state: 커밋된 고유 작업이 있는(base 대비 ahead) 워크스페이스는
        # untracked 파일이 섞여 있어도 stash 왕복 없이 오늘과 동일하게
        # 그대로 유지돼야 한다.
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("base")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "base commit")
            base_branch = subprocess.run(
                ["git", "-C", str(origin), "symbolic-ref", "--short", "HEAD"],
                capture_output=True, text=True).stdout.strip()

            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")

            issue, role = 999909, "implementation"
            br = f"issue-{issue}/{role}"
            self._git(work, "checkout", "-q", "-b", br, base_branch)
            (work / "progress.txt").write_text("real committed work")
            self._git(work, "add", "progress.txt")
            self._git(work, "commit", "-q", "-m", "in-progress work, ahead of base")
            ahead_commit = self._git(work, "rev-parse", br).stdout.strip()
            (work / "scratch.txt").write_text("also untracked, should stay untouched")

            result = spawn.checkout_issue_branch(str(work), issue, role)

            self.assertEqual(result, br)
            after = self._git(work, "rev-parse", br).stdout.strip()
            self.assertEqual(after, ahead_commit,
                             "커밋이 앞서 있으면 브랜치가 재컷되면 안 된다")
            self.assertEqual((work / "scratch.txt").read_text(),
                             "also untracked, should stay untouched")
            self.assertEqual(
                self._git(work, "stash", "list").stdout.strip(), "",
                "ahead 워크스페이스에선 stash 를 쓰면 안 된다")

class WorkspaceExcludesHomeDotfiles(unittest.TestCase):
    """이슈 #289 H1: 샌드박스가 홈 dotfile 을 워크스페이스 루트에 오버레이해
    `git status`에 untracked 로 잡힌다 — `.muster-cache/`와 같은 방식으로
    `.git/info/exclude`에 등록해 `git add -A`가 이들을 못 줍게 한다."""

    def _git(self, cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a],
                              capture_output=True, text=True)

    def _init_repo(self, path):
        path.mkdir(parents=True, exist_ok=True)
        self._git(path, "init", "-q")
        self._git(path, "config", "user.email", "t@t.t")
        self._git(path, "config", "user.name", "t")

    @pytest.mark.slow
    def test_fresh_workspace_excludes_dotfile_set(self):
        with tempfile.TemporaryDirectory() as td:
            github = Path(td) / "github.git"
            self._git(github.parent, "init", "-q", "--bare", str(github))
            src = Path(td) / "src"
            r = subprocess.run(["git", "clone", "-q", str(github), str(src)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(src, "config", "user.email", "t@t.t")
            self._git(src, "config", "user.name", "t")
            (src / "a.txt").write_text("x")
            self._git(src, "add", "a.txt")
            self._git(src, "commit", "-q", "-m", "init")
            self._git(src, "push", "-q", "origin", "HEAD:main")

            work_base = Path(td) / "workbase"
            old_base = os.environ.get("MUSTER_WORK_DIR")
            os.environ["MUSTER_WORK_DIR"] = str(work_base)
            try:
                work = spawn.issue_workspace(str(src), 999905, "implementation")
            finally:
                if old_base is None:
                    os.environ.pop("MUSTER_WORK_DIR", None)
                else:
                    os.environ["MUSTER_WORK_DIR"] = old_base

            exclude = (Path(work) / ".git" / "info" / "exclude").read_text()
            for dotfile in (".bashrc", ".bash_profile", ".profile",
                            ".zshrc", ".zprofile", ".gitconfig",
                            ".gitmodules", ".mcp.json", ".claude",
                            ".idea", ".vscode", ".ripgreprc"):
                self.assertIn(dotfile, exclude, exclude)

class Drive(unittest.TestCase):
    """드라이버의 유일한 일은 **멈추는 것**이다 — 누구를 다음에 띄울지는
    자동 라우팅 표가 아니라 오케스트레이터의 판단이다(이슈 #120), 그래서
    drive() 는 스스로 역할을 고르지 않고 항상 즉시 멈춘다."""

    def _with_roster(self, td):
        old = spawn.ROSTER
        spawn.ROSTER = Path(td) / "active.json"
        return old

    def test_stops_when_nothing_to_spawn(self):
        with tempfile.TemporaryDirectory() as td:
            old = self._with_roster(td)
            try:
                self.assertEqual(spawn.drive("/x", False), 0)
            finally:
                spawn.ROSTER = old

    def test_never_calls_spawn_one(self):
        calls = []
        old_spawn = spawn._spawn_one
        spawn._spawn_one = lambda *a, **k: calls.append(a) or 0
        with tempfile.TemporaryDirectory() as td:
            old_roster = self._with_roster(td)
            try:
                spawn.drive("/x", False, limit=3)
                self.assertEqual(calls, [], "drive 가 역할을 자동으로 스폰했다")
            finally:
                spawn._spawn_one = old_spawn
                spawn.ROSTER = old_roster

class IssueScopedPrompt(unittest.TestCase):
    """이슈 스코프 준비는 정확히 한 번 일어난다.

    프리앰블이 두 번 붙으면 역할은 같은 지시를 두 벌 읽는다 — 모델이 중복을
    모순으로 읽을 여지를 주는 것도 문제지만, 준비 자체가 두 번 돌면
    워크스페이스 준비와 브랜치 체크아웃도 두 번 돈다. 세션이 실제로 받는
    프롬프트를 관측해서 잡는다: 스폰 명령을 `cat` 으로 갈아끼우면 stdin 으로
    넘어간 맡길 일이 그대로 라이브 로그에 떨어진다.
    """

    @pytest.mark.slow
    def test_preparation_and_preamble_happen_once(self):
        import subprocess as sp
        from unittest import mock

        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "issue-7-qa"
            work.mkdir()
            run = lambda *a: sp.run(a, cwd=str(work), capture_output=True,
                                    text=True, check=True)
            run("git", "init", "-q")
            run("git", "config", "user.email", "t@example.com")
            run("git", "config", "user.name", "t")
            (work / "f.txt").write_text("x")
            run("git", "add", "f.txt")
            run("git", "commit", "-q", "-m", "init")

            prep = []

            def fake_workspace(cwd, issue, role):
                prep.append(("workspace", str(cwd)))
                return str(work)

            def fake_branch(cwd, issue, role):
                prep.append(("branch", str(cwd)))
                return f"issue-{issue}-{role}"

            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster
            roster_calls = []
            orig_roster_register = spawn.roster_register

            def spy_roster_register(key, entry):
                roster_calls.append((key, dict(entry)))
                return orig_roster_register(key, entry)

            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with mock.patch.object(spawn, "issue_workspace", fake_workspace), \
                     mock.patch.object(spawn, "checkout_issue_branch", fake_branch), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "ensure_pushed",
                                       lambda *a, **k: None), \
                     mock.patch.object(spawn, "roster_register",
                                       spy_roster_register), \
                     mock.patch.object(spawn, "ledger_write",
                                       lambda *a, **k: None):
                    spawn._spawn_one(str(work), "execution-observation", "원래 맡긴 일.\n",
                                     unattended=True, issue=7)
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster

            log_path = [e for k, e in roster_calls
                       if k == "issue-7/execution-observation"][0]["log"]
            delivered = Path(log_path).read_text()
            self.assertEqual(delivered.count("당신의 이슈:"), 1, delivered)
            self.assertEqual(delivered.count("원래 맡긴 일."), 1, delivered)
            self.assertEqual([p for p, _ in prep].count("workspace"), 1, prep)
            self.assertEqual([p for p, _ in prep].count("branch"), 1, prep)


class WorkspaceReuseOriginMismatch(unittest.TestCase):
    """#288 N5: 작업 경로에 우연히 다른 origin 을 가진 레포가 이미 있으면
    재사용 분기로 들어가 fetch 실패를 네트워크 문제로 오보했다."""

    def _init_repo(self, path: Path, origin_url: str) -> None:
        path.mkdir(parents=True)
        run = lambda *args: subprocess.run(
            args, cwd=str(path), capture_output=True, text=True, check=True)
        run("git", "init", "-q")
        run("git", "config", "user.email", "t@example.com")
        run("git", "config", "user.name", "t")
        (path / "f.txt").write_text("x")
        run("git", "add", "f.txt")
        run("git", "commit", "-q", "-m", "init")
        run("git", "remote", "add", "origin", origin_url)

    @pytest.mark.slow
    def test_foreign_origin_at_work_path_is_refused_by_identity(self):
        with tempfile.TemporaryDirectory() as td:
            src_remote = Path(td) / "src-remote.git"
            subprocess.run(["git", "init", "-q", "--bare", str(src_remote)], check=True)
            src = Path(td) / "src"
            self._init_repo(src, str(src_remote))
            subprocess.run(["git", "-C", str(src), "push", "-q", "-u", "origin", "HEAD:main"],
                           check=True)

            work_base = Path(td) / "work"
            work_base.mkdir()
            repo_name = "src-remote"  # derived from src_remote's basename, like issue_workspace() does
            issue = 999
            role = "coding"
            work = work_base / f"{repo_name}-issue-{issue}-{role}"
            self._init_repo(work, "https://github.com/someone/unrelated.git")

            old_environ = dict(os.environ)
            os.environ["MUSTER_WORK_DIR"] = str(work_base)
            try:
                with self.assertRaises(SystemExit) as cm:
                    spawn.issue_workspace(str(src), issue, role)
            finally:
                os.environ.clear()
                os.environ.update(old_environ)

            msg = str(cm.exception)
            self.assertIn("origin 불일치", msg)
            self.assertNotIn("fetch 실패", msg)
            self.assertTrue((work / "f.txt").exists())

    def test_ssh_vs_https_origin_form_is_not_treated_as_mismatch(self):
        # warrant hunt finding: toggling MUSTER_KEEP_SSH between spawns of
        # the same issue/role must not make the identity check (N5 fix)
        # falsely refuse a legitimately matching workspace just because
        # one side is ssh-form and the other https-form.
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src"
            self._init_repo(src, "git@github.com:someorg/somerepo.git")

            work_base = Path(td) / "work"
            work_base.mkdir()
            repo_name = "somerepo"
            issue = 998
            role = "coding"
            work = work_base / f"{repo_name}-issue-{issue}-{role}"
            self._init_repo(work, "https://github.com/someorg/somerepo.git")

            old_environ = dict(os.environ)
            os.environ["MUSTER_WORK_DIR"] = str(work_base)
            os.environ.pop("MUSTER_KEEP_SSH", None)
            try:
                with mock.patch.object(spawn, "_fetch_or_halt") as fake_fetch:
                    result = spawn.issue_workspace(str(src), issue, role)
            finally:
                os.environ.clear()
                os.environ.update(old_environ)

            self.assertEqual(result, str(work))
            fake_fetch.assert_called_once()

class RepoScopedWorkspaceIndex(unittest.TestCase):
    """이슈 #533: 서로 다른 레포가 같은 이슈+역할로 워크스페이스 인덱스
    키가 충돌하던 문제 — 키에 레포 정체성을 넣고, 조회를 `-C`로 좁히고,
    같은 키에 다른 work 로 덮어쓰면 조용히 넘어가지 않고 에러낸다."""

    def _init_repo(self, path: Path, origin_url: str) -> None:
        path.mkdir(parents=True)
        run = lambda *args: subprocess.run(
            args, cwd=str(path), capture_output=True, text=True, check=True)
        run("git", "init", "-q")
        run("git", "remote", "add", "origin", origin_url)

    def setUp(self):
        self.td = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.td, ignore_errors=True)
        old_idx = spawn.WORKSPACE_INDEX
        spawn.WORKSPACE_INDEX = Path(self.td) / "workspaces.json"
        self.addCleanup(setattr, spawn, "WORKSPACE_INDEX", old_idx)
        self.repo_a = Path(self.td) / "repoA"
        self._init_repo(self.repo_a, "https://github.com/acme/repo-a.git")
        self.repo_b = Path(self.td) / "repoB"
        self._init_repo(self.repo_b, "https://github.com/acme/repo-b.git")

    def test_two_repos_same_issue_role_keep_distinct_entries(self):
        spawn._workspace_index_put(19, "implementation", str(self.repo_a), "log-a")
        spawn._workspace_index_put(19, "implementation", str(self.repo_b), "log-b")
        idx = spawn._workspace_index_load()
        self.assertEqual(len(idx), 2)
        self.assertEqual(idx["repo-a/issue-19/implementation"]["log"], "log-a")
        self.assertEqual(idx["repo-b/issue-19/implementation"]["log"], "log-b")

    def test_same_key_different_work_raises_regardless_of_watcher_pid(self):
        spawn._workspace_index_put(19, "implementation", str(self.repo_a), "log-a")
        with self.assertRaises(RuntimeError):
            spawn._workspace_index_put(19, "implementation", str(self.repo_a) + "/",
                                        "log-a-other")

    def test_same_key_different_work_raises_before_watcher_pid_set(self):
        # 이슈 #533 after-proposal hunt: watcher_pid 가 아직 안 붙은 첫 등록
        # 시점에도(스폰 초입, spawn.py:3860) 충돌은 똑같이 에러여야 한다 —
        # watcher_pid 유무로 완화하면 그 창에서 조용히 덮어써지는 원래 버그가
        # 재현된다.
        spawn._workspace_index_put(19, "implementation", str(self.repo_a), "log-a")
        with self.assertRaises(RuntimeError):
            spawn._workspace_index_put(19, "implementation", str(self.repo_a) + "/",
                                        "log-a-other", watcher_pid=None)

    def test_same_key_same_work_is_a_normal_update_not_a_collision(self):
        spawn._workspace_index_put(19, "implementation", str(self.repo_a), "log-a")
        spawn._workspace_index_put(19, "implementation", str(self.repo_a), "log-a",
                                    watcher_pid=4242)
        idx = spawn._workspace_index_load()
        self.assertEqual(idx["repo-a/issue-19/implementation"]["watcher_pid"], 4242)

    def test_lookup_roster_entry_scoped_by_repo_ignores_other_repo(self):
        spawn._workspace_index_put(19, "implementation", str(self.repo_a), "log-a")
        spawn._workspace_index_put(19, "implementation", str(self.repo_b), "log-b")
        idx = spawn._workspace_index_load()
        key, entry = spawn._lookup_roster_entry(idx, 19, "implementation", repo="repo-a")
        self.assertEqual(key, "repo-a/issue-19/implementation")
        self.assertEqual(entry["log"], "log-a")

    def test_watch_scoped_by_cwd_never_returns_other_repo_entry(self):
        from unittest import mock
        spawn._workspace_index_put(19, "implementation", str(self.repo_a), "log-a")
        spawn._workspace_index_put(19, "implementation", str(self.repo_b), "log-b")
        seen = {}

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path, **kwargs):
            seen["log_path"] = log_path
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            old_argv = sys.argv
            sys.argv = ["spawn.py", "watch", "--issue", "19", "--role", "implementation",
                        "-C", str(self.repo_a)]
            try:
                rc = spawn.main()
            finally:
                sys.argv = old_argv
        self.assertEqual(rc, 0)
        self.assertEqual(seen["log_path"], Path("log-a"))

    def test_legacy_bare_key_migrates_on_load(self):
        spawn.WORKSPACE_INDEX.parent.mkdir(parents=True, exist_ok=True)
        spawn.WORKSPACE_INDEX.write_text(json.dumps(
            {"issue-19/implementation": {"work": str(self.repo_a), "log": "log-a"}}))
        idx = spawn._workspace_index_load()
        self.assertNotIn("issue-19/implementation", idx)
        self.assertEqual(idx["repo-a/issue-19/implementation"]["log"], "log-a")
        # 재로딩은 멱등 — 두 번째 로드에서 다시 안 바뀐다.
        idx2 = spawn._workspace_index_load()
        self.assertEqual(idx2, idx)

class ResumeOrchestratorSessionPermissionMode(unittest.TestCase):
    """이슈 #886: acceptEdits 는 파일 편집만 자동승인하고 Bash(gh pr merge,
    git fetch)는 거부한다(PR #885 실측) — 재개 호출은 bypassPermissions 를
    명시적으로 실어야 한다."""

    def test_popen_command_carries_bypass_permissions(self):
        captured = {}

        def fake_popen(cmd, **kwargs):
            captured["cmd"] = cmd
            return unittest.mock.Mock()

        with unittest.mock.patch.object(spawn.subprocess, "Popen", fake_popen):
            spawn._resume_orchestrator_session("sess-1", "nudge")

        cmd = captured["cmd"]
        self.assertEqual(cmd[:2], ["claude", "-p"])
        self.assertIn("--resume", cmd)
        idx = cmd.index("--permission-mode")
        self.assertEqual(cmd[idx + 1], "bypassPermissions")

class SessionResumeClaim(unittest.TestCase):
    """이슈 #878: session_id 는 roster 엔트리가 아니라 오케스트레이터
    프로세스 단위 — 같은 session_id 를 공유하는 두 엔트리가 같은 폴 창에서
    ready 가 돼도 resume-invoke 는 한 번만 나가야 한다(after-proposal hunt
    발견에 대한 응답)."""

    def setUp(self):
        self._orig = spawn.RECONCILE_LEDGER
        self._td = tempfile.TemporaryDirectory()
        spawn.RECONCILE_LEDGER = Path(self._td.name) / "reconcile_ledger.json"

    def tearDown(self):
        spawn.RECONCILE_LEDGER = self._orig
        self._td.cleanup()

    def test_first_claim_for_a_session_id_succeeds(self):
        self.assertTrue(spawn._session_resume_claim("sess-1", now=1000.0))

    def test_second_claim_for_same_session_id_within_ttl_fails(self):
        spawn._session_resume_claim("sess-1", now=1000.0)
        self.assertFalse(spawn._session_resume_claim(
            "sess-1", now=1000.0 + spawn.SESSION_RESUME_CLAIM_TTL_SEC - 1))

    def test_two_roster_entries_sharing_a_session_id_resume_exactly_once(self):
        # roster_watchdog 의 완료-감지 틱에서, session_id 를 공유하는 두 엔트리가
        # 같은 창에서 ready 가 되는 상황을 시뮬레이션한다.
        entry_a = {"session_id": "sess-shared", "work": "/tmp/a"}
        entry_b = {"session_id": "sess-shared", "work": "/tmp/b"}
        with unittest.mock.patch.object(
                spawn, "_resume_orchestrator_session",
                return_value=unittest.mock.Mock()) as fake_resume:
            fired_a = spawn._maybe_resume_for_ready_pr("issue-1/impl-a", entry_a, 10)
            fired_b = spawn._maybe_resume_for_ready_pr("issue-1/impl-b", entry_b, 11)
        self.assertTrue(fired_a)
        self.assertFalse(fired_b)
        fake_resume.assert_called_once()

    def test_no_session_id_never_resumes(self):
        with unittest.mock.patch.object(
                spawn, "_resume_orchestrator_session") as fake_resume:
            fired = spawn._maybe_resume_for_ready_pr(
                "issue-1/impl", {"session_id": None, "work": "/tmp/a"}, 10)
        self.assertFalse(fired)
        fake_resume.assert_not_called()

    def test_resume_popen_failure_reports_not_fired(self):
        with unittest.mock.patch.object(
                spawn, "_resume_orchestrator_session", return_value=None):
            fired = spawn._maybe_resume_for_ready_pr(
                "issue-1/impl", {"session_id": "sess-2", "work": "/tmp/a"}, 10)
        self.assertFalse(fired)

class OrchestratorSessionIdCapture(unittest.TestCase):
    """이슈 #878: `ORCHESTRATOR_SESSION_ID_ENV` 가 심어져 있으면 roster
    엔트리에 그대로 옮겨 담긴다 — 없으면 spawn.py 는 절대 지어내지 않고
    None 으로 남긴다(케이스 1/인터랙티브 세션은 이 필드가 필요 없다)."""

    def test_env_var_name_is_stable(self):
        self.assertEqual(spawn.ORCHESTRATOR_SESSION_ID_ENV, "ORCHESTRATOR_SESSION_ID")

    def test_roster_register_call_site_reads_env_at_spawn_time(self):
        # 전체 _spawn_one() 을 굴리지 않고, 그 줄이 실제로 참조하는 계약만
        # 좁게 확인한다: os.environ.get(ORCHESTRATOR_SESSION_ID_ENV) or None.
        with unittest.mock.patch.dict(
                os.environ, {spawn.ORCHESTRATOR_SESSION_ID_ENV: "sess-abc"}):
            self.assertEqual(
                os.environ.get(spawn.ORCHESTRATOR_SESSION_ID_ENV) or None,
                "sess-abc")
        with unittest.mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(spawn.ORCHESTRATOR_SESSION_ID_ENV, None)
            self.assertIsNone(
                os.environ.get(spawn.ORCHESTRATOR_SESSION_ID_ENV) or None)

class StateRootIsolation(unittest.TestCase):
    """이슈 #857 (PR #855 finding 5): 관측 세션과 하네스가 띄우는 fixture
    세션이 같은 플러그인 설치를 공유해도, `MUSTER_STATE_ROOT` 를 다르게
    주면 로스터/워크스페이스 인덱스 파일 자체가 물리적으로 갈려 서로의
    항목을 못 본다 — 같은 --issue 번호를 써도, `-C` 가 실수로 관측 세션
    쪽 레포를 가리켜도(#855 재현 정확히 그 모양) 마찬가지다. 두 개의
    실제 `python3 spawn.py` 서브프로세스로 검증한다 — production 에서
    fixture 세션과 관측 세션은 실제로 별개 인터프리터 프로세스이므로,
    모듈 속성을 직접 바꿔치기하는 다른 테스트들과 달리 이 회귀는
    프로세스 경계를 넘는 env var 전파가 핵심이라 서브프로세스가 필요하다."""

    def setUp(self):
        self.td = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.td, ignore_errors=True)
        self.observer_state = str(Path(self.td) / "observer-state")
        self.fixture_state = str(Path(self.td) / "fixture-state")
        self.observer_repo = str(Path(self.td) / "observer-repo")
        self.fixture_repo = str(Path(self.td) / "fixture-repo")
        for repo in (self.observer_repo, self.fixture_repo):
            Path(repo).mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True,
                            capture_output=True)

    def _register_in_subprocess(self, state_root: str, cwd: str) -> None:
        """`state_root` 를 `MUSTER_STATE_ROOT` 로 준 별도 파이썬 프로세스에서,
        `cwd` 를 작업 디렉터리로 이슈 776/execution-observation 항목을
        워크스페이스 인덱스와 로스터 양쪽에 등록한다 — `roster_register()`
        도 같이 호출해 Finding 1(로스터 자체의 bare-key 충돌)까지 같이
        재현/검증한다."""
        script = (
            "import sys; sys.path.insert(0, %r)\n"
            "import spawn\n"
            "spawn._workspace_index_put(776, 'execution-observation', %r, 'log.txt')\n"
            "spawn.roster_register('issue-776/execution-observation', "
            "{'pid': 999999, 'wrapper_pid': 999999})\n"
        ) % (str(Path(__file__).parent.parent), cwd)
        env = {**os.environ, "MUSTER_STATE_ROOT": state_root}
        r = subprocess.run([sys.executable, "-c", script], cwd=cwd,
                            capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_fixture_state_root_never_resolves_observers_roster(self):
        # 관측 세션: 자기 state root 에 이슈 776 항목을 등록한다.
        self._register_in_subprocess(self.observer_state, self.observer_repo)

        # fixture 세션: 다른 state root 에서, 같은 --issue 번호로, 그리고
        # #855 실측처럼 -C 가 (실수로) 관측 세션의 레포를 가리켜도 관측
        # 세션의 로스터 항목을 절대 못 본다 — watch 는 "기록 없음"으로
        # 끝나야 한다(자기 자신의 격리된 state 에는 아무것도 없으므로).
        watch_script = (
            "import sys; sys.path.insert(0, %r)\n"
            "import spawn\n"
            "idx = spawn._workspace_index_load()\n"
            "key, entry = spawn._lookup_roster_entry(idx, 776, "
            "'execution-observation', repo=spawn._repo_identity(%r))\n"
            "assert entry is None, f'fixture resolved observer entry: {entry!r}'\n"
            "assert spawn._roster_load().get("
            "'issue-776/execution-observation') is None, "
            "'fixture resolved observer roster entry'\n"
            "print('OK')\n"
        ) % (str(Path(__file__).parent.parent), self.observer_repo)
        env = {**os.environ, "MUSTER_STATE_ROOT": self.fixture_state}
        r = subprocess.run([sys.executable, "-c", watch_script],
                            cwd=self.observer_repo, capture_output=True,
                            text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OK", r.stdout)

        # 관측 세션 쪽 파일은 fixture 가 아무것도 등록하지 않았으니 손대지
        # 않은 채 그대로다(empty state 인수 확인).
        observer_idx_path = Path(self.observer_state) / "workspaces.json"
        self.assertTrue(observer_idx_path.exists())
        observer_idx = json.loads(observer_idx_path.read_text())
        self.assertEqual(len(observer_idx), 1)

    def test_state_root_env_var_overrides_default_runs_dir(self):
        script = (
            "import sys; sys.path.insert(0, %r)\n"
            "import spawn\n"
            "print(spawn.STATE_ROOT)\n"
            "print(spawn.ROSTER)\n"
            "print(spawn.WORKSPACE_INDEX)\n"
        ) % (str(Path(__file__).parent.parent),)
        env = {**os.environ, "MUSTER_STATE_ROOT": self.fixture_state}
        r = subprocess.run([sys.executable, "-c", script],
                            capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.strip().splitlines()
        self.assertEqual(lines[0], str(Path(self.fixture_state).resolve()))
        self.assertEqual(lines[1], str(Path(self.fixture_state).resolve() / "active.json"))
        self.assertEqual(lines[2],
                          str(Path(self.fixture_state).resolve() / "workspaces.json"))
