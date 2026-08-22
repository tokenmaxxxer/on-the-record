from _spawn_test_support import *  # noqa: F401,F403
from _spawn_test_support import _event  # noqa: F401


class BoardSnapshot(unittest.TestCase):
    def test_delta_shows_changed_and_new(self):
        with tempfile.TemporaryDirectory() as td:
            rec = Path(td) / spawn.BOARD / "issue-3" / "reports"
            rec.mkdir(parents=True)
            (rec / "qa.md").write_text("loop_state: probing\n")
            before = spawn.board_snapshot(td)
            (rec / "qa.md").write_text("loop_state: reproduced\n")
            (rec / "coding.md").write_text("new\n")
            after = spawn.board_snapshot(td)
            delta = sorted(p for p in after if after.get(p) != before.get(p))
            self.assertEqual(delta, [f"{spawn.BOARD}/issue-3/reports/coding.md",
                                     f"{spawn.BOARD}/issue-3/reports/qa.md"])

    def test_no_board_is_empty(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(spawn.board_snapshot(td), {})

class SessionResult(unittest.TestCase):
    def test_parses_json(self):
        got = spawn.session_result('{"session_id": "abc", "total_cost_usd": 0.5}')
        self.assertEqual(got["session_id"], "abc")

    def test_garbage_is_empty_dict(self):
        # 파싱 불가를 성공으로 취급하지 않는다 — 빈 dict 는 아래 classify 에서
        # is_error 도 아니고 필드도 없는, "모른다" 그대로다.
        self.assertEqual(spawn.session_result("not json"), {})
        self.assertEqual(spawn.session_result(""), {})

class OwnershipReport(unittest.TestCase):
    """세션 안 게이트가 안 돌았을 때의 마지막 흔적. 막지는 않고 말만 한다."""
    B = spawn.BOARD

    def test_own_record_and_subtree_are_silent(self):
        self.assertEqual(spawn.ownership_report(
            "/x", "execution-observation", [f"{self.B}/issue-3/reports/execution-observation.md",
                         f"{self.B}/issue-3/reports/execution-observation/run.log"]), [])

    def test_foreign_record_is_named(self):
        out = spawn.ownership_report("/x", "execution-observation",
                                     [f"{self.B}/issue-3/reports/coding.md"])
        self.assertTrue(out and "coding.md" in out[1])

    def test_granted_subtrees_are_silent(self):
        self.assertEqual(spawn.ownership_report(
            "/x", "release-engineering", [f"{self.B}/issue-3/reports/postmortems/x.md"]), [])

    def test_paths_outside_the_board_are_not_its_business(self):
        self.assertEqual(spawn.ownership_report("/x", "execution-observation", ["src/app.py"]), [])

@pytest.mark.slow
class EventReporting(unittest.TestCase):
    """issue #129 phase 2: `.events.jsonl` 기록의 정확성 — 실측된 오탐 3건
    (gate-refusal 오탐 2건, pr-opened 중복 1건)을 보존된 fixture 로 재현.

    issue #1490 rework: 각 케이스가 `_spawn_one`을 통해 실제 subprocess
    (git init + `cat`)을 스폰한다 — 클래스당 20개 넘는 케이스가 건당
    20~105s 걸려 기본(non-slow) 실행 시간의 대부분을 차지했다. slow
    마커의 정의("실제 subprocess spawn ... lifecycle tests")에 그대로
    해당해 slow 티어로 옮긴다."""

    def _run(self, td, task, roster_key="e", pr_for_branch=lambda *a, **k: None,
             branch="b"):
        import subprocess as sp
        from unittest import mock

        work = Path(td) / "work"
        if not work.exists():
            work.mkdir()
            run = lambda *a: sp.run(a, cwd=str(work), capture_output=True,
                                    text=True, check=True)
            run("git", "init", "-q")
            run("git", "config", "user.email", "t@example.com")
            run("git", "config", "user.name", "t")
            (work / "f.txt").write_text("x")
            run("git", "add", "f.txt")
            run("git", "commit", "-q", "-m", "init")
        roster = Path(td) / "active.json"
        old_roster = spawn.ROSTER
        spawn.ROSTER = roster
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            with mock.patch.dict(os.environ, {"MUSTER_WORK_DIR": str(Path(td) / "sweep-base")}), \
                 mock.patch.object(spawn, "issue_workspace",
                                   lambda cwd, issue, role: str(work)), \
                 mock.patch.object(spawn, "checkout_issue_branch",
                                   lambda cwd, issue, role: branch), \
                 mock.patch.object(spawn, "spawn_cmd",
                                   lambda *a, **k: (["cat"], {})), \
                 mock.patch.object(spawn, "ensure_pushed",
                                   lambda *a, **k: None), \
                 mock.patch.object(spawn, "ledger_write",
                                   lambda *a, **k: None), \
                 mock.patch.object(spawn, "_open_pr_for_branch", pr_for_branch):
                spawn._spawn_one(str(work), "execution-observation", task, unattended=True, issue=7)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            spawn.ROSTER = old_roster
        events_path = Path(str(work) + spawn.EVENTS_SUFFIX)
        if not events_path.exists():
            return []
        return [json.loads(l) for l in events_path.read_text().splitlines()]

    @staticmethod
    def _tool_use_line(tool_use_id, name, command=None):
        # 이슈 #246 결함 3: 실제 스트림에서 tool_result 는 언제나 그 도구를
        # 요청한 assistant 의 tool_use 블록(같은 id) 뒤에 온다 — 건별
        # 상관관계 픽스처가 그 순서를 재현한다.
        # 이슈 #558: command 는 Bash tool_use 픽스처에 거부된 명령 텍스트를
        # 싣기 위한 선택적 인자다 — 다른 도구 이름은 그대로 input={}.
        inp = {"command": command} if command is not None else {}
        event = _event("assistant", message={"content": [
            {"type": "tool_use", "id": tool_use_id, "name": name, "input": inp}]})
        return json.dumps(event)

    def test_end_turn_result_is_not_a_gate_refusal(self):
        # issue-46/49 survey fixture: a normal end_turn result JSON line
        # contains the literal key name "permission_denials" — the old
        # raw-text regex misfired on the key name itself.
        line = json.dumps({"type": "result", "stop_reason": "end_turn",
                           "is_error": False, "permission_denials": []})
        events = self._run(tempfile.mkdtemp(), line + "\n")
        self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)

    def test_echoed_source_mentioning_denied_is_not_a_gate_refusal(self):
        # issue-126 survey fixture: mid-session tool output echoing this
        # file's own `_DENIAL_RE = re.compile(r"permission_denial|denied", ...)`
        # source line used to trip the raw-text scan.
        echoed = ('{"type":"user","message":{"content":[{"type":"tool_result",'
                  '"content":"_DENIAL_RE = re.compile(r\\"permission_denial|denied\\", re.IGNORECASE)"}]}}\n')
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": []})
        events = self._run(tempfile.mkdtemp(), echoed + result_line + "\n")
        self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)

    def test_denials_with_no_correlating_tool_result_are_unclassified(self):
        # 층을 확정할 tool_result 줄이 없어도(스트림 누락 등) 최종 result 의
        # permission_denials 가 실려 있으면 거부 자체는 놓치지 않는다 — 다만
        # 예전처럼 layer-1 로 위장하지 않고 별도 라벨(unclassified-refusal)로
        # 남는다(제안서 5번). 옛 코드는 이 케이스에서 gate-refusal 을 냈다.
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Write"}]})
        events = self._run(tempfile.mkdtemp(), result_line + "\n")
        self.assertTrue([e for e in events if e["type"] == "unclassified-refusal"], events)
        self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)

    def test_gate_hook_denial_is_gate_refusal_with_gate_name(self):
        # 이슈 #232 층 1 실물 샘플: PreToolUse hook 이 감싼 gate-lib.sh 의
        # gate_deny 메시지(`<게이트>: refused — <사유>`) — 게이트 이름과
        # 사유가 이미 이 텍스트 안에 있다. 옛 코드는 detail 에
        # `str(denials)[:200]` 만 실어 게이트 이름을 못 냈다.
        text = ("PreToolUse:Bash hook error: "
                "[/Users/jk/.claude/plugins/marketplaces/tokenmaxxxer-core/core/hooks/board-gate.sh] "
                "board-gate: refused — 보드에 없는 파일을 쓰려 했다")
        tool_use = self._tool_use_line("t1", "Write")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Write"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use + "\n" + tool_result + "\n" + result_line + "\n")
        refusals = [e for e in events if e["type"] == "gate-refusal"]
        self.assertEqual(len(refusals), 1, events)
        self.assertEqual(refusals[0]["detail"]["gate"], "board-gate", events)
        self.assertFalse([e for e in events if e["type"] == "unclassified-refusal"], events)

    def test_harness_permission_denial_is_not_labeled_gate_refusal(self):
        # 이슈 #232 실측 사건 재현: 순수 읽기 명령이 하네스 권한(2층)에
        # 막혔는데 옛 코드는 이걸 gate-refusal 로 잘못 보고해 오케스트레이터가
        # "board-gate 가 오탐한다"고 사용자에게 근거 없이 전달했다. 다섯
        # 샘플 모두 이슈 본문에서 그대로 가져온 실물 문자열이다.
        samples = (
            "Permission to use Bash has been denied",
            "This Bash command contains multiple operations. The "
            "following part requires approval: git show <sha>:<path>",
            "This command requires approval",
            "Contains shell syntax (string) that cannot be statically analyzed",
            "Contains simple_expansion",
        )
        for text in samples:
            with self.subTest(text=text):
                tool_use = self._tool_use_line("t1", "Bash")
                tool_result = json.dumps({"type": "user", "message": {"content": [
                    {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
                     "content": text}]}})
                result_line = json.dumps({"type": "result", "is_error": False,
                                          "permission_denials": [{"tool_name": "Bash"}]})
                events = self._run(tempfile.mkdtemp(),
                                   tool_use + "\n" + tool_result + "\n" + result_line + "\n")
                self.assertTrue([e for e in events if e["type"] == "harness-refusal"], events)
                self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)

    def test_harness_refusal_event_carries_refused_command_text(self):
        # 이슈 #558: 하네스 거부 이벤트는 거부 사유 텍스트만이 아니라 어떤
        # Bash 명령이 거부됐는지도 실어야 한다 — 옛 코드는 "requires
        # approval" 같은 고정 사유 문구뿐이라, 오케스트레이터가 정당하게
        # 필요했던 거부(사전 허용에 없던 명령)와 모델이 그냥 안 돌린 걸
        # 구분할 수 없었다(2026-08-09 soongsil-course-registration 런
        # 실측).
        command = "python3 -m venv venv && venv/bin/pip install requests"
        tool_use = self._tool_use_line("t1", "Bash", command=command)
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": "This command requires approval"}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Bash"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use + "\n" + tool_result + "\n" + result_line + "\n")
        refusals = [e for e in events if e["type"] == "harness-refusal"]
        self.assertEqual(len(refusals), 1, events)
        self.assertEqual(refusals[0]["detail"]["command"], command, events)
        self.assertIn("requires approval", refusals[0]["detail"]["text"], events)

    def test_sandbox_denial_is_not_labeled_gate_refusal(self):
        # 이슈 #232 층 3 실물 샘플 — 옛 코드는 이것도 gate-refusal 로 뭉갰다.
        samples = (
            "mkdir: /tmp/foo: Operation not permitted",
            "Claude requested permissions to write to /some/path, but "
            "you haven't granted it yet",
        )
        for text in samples:
            with self.subTest(text=text):
                tool_use = self._tool_use_line("t1", "Write")
                tool_result = json.dumps({"type": "user", "message": {"content": [
                    {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
                     "content": text}]}})
                result_line = json.dumps({"type": "result", "is_error": False,
                                          "permission_denials": [{"tool_name": "Write"}]})
                events = self._run(tempfile.mkdtemp(),
                                   tool_use + "\n" + tool_result + "\n" + result_line + "\n")
                self.assertTrue([e for e in events if e["type"] == "sandbox-refusal"], events)
                self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)

    def test_git_lock_masquerade_is_classified_as_sandbox_refusal(self):
        # 이슈 #289 H2: 샌드박스가 거부한 .git/config 쓰기가 EEXIST 로 변환돼
        # git 이 마치 진짜 잠금 경합인 것처럼 보고한다 — 예전엔 분류기가
        # 이 문구를 놓쳐 unclassified-refusal 로 떨어졌다.
        text = "error: cannot lock config file .git/config: File exists"
        tool_use = self._tool_use_line("t1", "Bash")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Bash"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use + "\n" + tool_result + "\n" + result_line + "\n")
        self.assertTrue([e for e in events if e["type"] == "sandbox-refusal"], events)
        self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)
        self.assertFalse([e for e in events if e["type"] == "unclassified-refusal"], events)

    def test_non_error_tool_result_matching_refusal_text_fires_nothing(self):
        # issue-129 의 구조적 판정(is_error 우선, 텍스트 매치만으로 판정하지
        # 않기) 회귀 방지를 층 분류에도 적용한다 — 성공한(is_error 없는)
        # tool_result 가 거부 문구를 우연히 담아도 아무 이벤트가 없어야 한다.
        for text in ("Permission to use Bash has been denied",
                     "mkdir: /tmp/foo: Operation not permitted",
                     "PreToolUse:Bash hook error: [board-gate.sh] "
                     "board-gate: refused — x"):
            with self.subTest(text=text):
                tool_result = json.dumps({"type": "user", "message": {"content": [
                    {"type": "tool_result", "is_error": False, "content": text}]}})
                events = self._run(tempfile.mkdtemp(), tool_result + "\n")
                self.assertFalse(
                    [e for e in events if e["type"] in
                     ("gate-refusal", "harness-refusal", "sandbox-refusal",
                      "unclassified-refusal")], events)

    def test_layer2_denial_quoting_gate_marker_is_harness_refusal_not_gate(self):
        # 이슈 #235 요구사항 4(i) / execution-observation Finding 1(b): 층 2
        # 하네스 거부가 명령을 원문 인용하는데, 그 인용된 명령에 게이트
        # 마커(`PreToolUse:<tool> hook error: [<path>]`)가 들어 있으면 옛
        # 코드는 이걸 층 1(gate-refusal)로 오분류했다. 마커가 텍스트 시작이
        # 아니라 인용 안에 있으니, 시작-앵커된 정규식은 여기 안 걸려야 한다.
        text = ("This Bash command contains multiple operations. The "
                "following part requires approval: PreToolUse:Bash hook "
                "error: [/plugins/tokenmaxxxer-core/core/hooks/some-gate.sh] "
                "some-gate: refused — 원문 인용된 명령")
        tool_use = self._tool_use_line("t1", "Bash")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Bash"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use + "\n" + tool_result + "\n" + result_line + "\n")
        self.assertTrue([e for e in events if e["type"] == "harness-refusal"], events)
        self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)

    def test_zero_denials_session_with_gate_marker_in_error_output_fires_nothing(self):
        # 이슈 #235 요구사항 4(ii) / execution-observation Finding 1(a): 세션의
        # 최종 result 줄 permission_denials 가 비어 있으면, 실패한 도구 호출의
        # 출력에 게이트 마커가 있어도 거부 이벤트가 전혀 나면 안 된다 — is_error
        # 는 "실패"지 "거부"가 아니라는 요구사항 1의 안전장치.
        text = ("PreToolUse:Write hook error: [/plugins/tokenmaxxxer-core/"
                "core/hooks/some-gate.sh] some-gate: refused — 무관한 실패")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": []})
        events = self._run(tempfile.mkdtemp(),
                           tool_result + "\n" + result_line + "\n")
        self.assertFalse(
            [e for e in events if e["type"] in
             ("gate-refusal", "harness-refusal", "sandbox-refusal",
              "unclassified-refusal")], events)

    def test_spurious_candidate_tool_name_mismatch_does_not_suppress_real_denial_fallback(self):
        # 이슈 #246 결함 3 (범위 확장, 발주자 코멘트): 이슈 #235 요구사항
        # 4(iii)/execution-observation Finding 1(c)가 원래 이름으로 주장했던
        # 비억제 속성의 교체 픽스처 — 옛 픽스처는 앵커된 `_GATE_HOOK_RE` 때문에
        # 아예 분류조차 안 되는 텍스트를 썼다(제안서 결함 3 실측). 이 픽스처는
        # 비-앵커 층 3 패턴("Operation not permitted")에 걸려 실제로 분류되는
        # 스푸리어스 후보를 쓴다 — 그 후보의 tool_use_id 로 상관되는 tool_name
        # ("Read")이 세션의 permission_denials 항목("Write")과 다르므로, 옛
        # 세션 전역 `refusals_seen` 불리언이었다면 이 후보 하나만으로 그
        # unclassified-refusal 폴백이 영구히 억제됐을 것이다. 이슈 #246 결함
        # 3의 건별(tool_name 단위) 상관관계는 그 억제를 없앤다: 스푸리어스
        # 후보 자신은 fire 하지 않지만(진짜 층 라벨을 참칭하지 않음), 상관 안
        # 되는 진짜 거부("Write")의 폴백은 여전히 fire 한다.
        spurious = ("Some unrelated tool output happened to mention: mkdir: "
                    "/tmp/foo: Operation not permitted")
        tool_use = self._tool_use_line("t1", "Read")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": spurious}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Write"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use + "\n" + tool_result + "\n" + result_line + "\n")
        self.assertTrue([e for e in events if e["type"] == "unclassified-refusal"], events)
        self.assertFalse([e for e in events if e["type"] == "sandbox-refusal"], events)
        self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)

    def test_spurious_candidate_tool_name_match_correlates_and_fires_as_real_layer(self):
        # 위 픽스처의 컴패니언(제안서 결함 3): 같은 스푸리어스-패턴 텍스트라도
        # 후보의 tool_name 이 실제로 permission_denials 항목과 일치하면 Counter
        # 상관은 그걸 확정하고 진짜 층 이벤트(sandbox-refusal)로 fire 해야
        # 한다 — tool_name 매치가 무조건 통과가 아니라 실제로 판별함을
        # 확인한다.
        text = ("Some unrelated tool output happened to mention: mkdir: "
                "/tmp/foo: Operation not permitted")
        tool_use = self._tool_use_line("t1", "Write")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Write"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use + "\n" + tool_result + "\n" + result_line + "\n")
        refusals = [e for e in events if e["type"] == "sandbox-refusal"]
        self.assertEqual(len(refusals), 1, events)
        self.assertFalse([e for e in events if e["type"] == "unclassified-refusal"], events)

    def test_record_fields_gate_denial_reports_hook_stem_not_role_name(self):
        # 이슈 #235 요구사항 4(iv) / execution-observation Finding 2 실물 샘플:
        # gate_deny 의 첫 토큰이 게이트가 아니라 역할 이름
        # ("execution-observation")이었다 — hook 경로 stem
        # ("record-fields-gate")이 정답인데 옛 코드는 토큰 쪽을 골랐다.
        text = ("PreToolUse:Write hook error: "
                "[/plugins/tokenmaxxxer-core/core/hooks/record-fields-gate.sh]: "
                "execution-observation: refused — record is missing required "
                "section(s): 코드 리뷰")
        tool_use = self._tool_use_line("t1", "Write")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Write"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use + "\n" + tool_result + "\n" + result_line + "\n")
        refusals = [e for e in events if e["type"] == "gate-refusal"]
        self.assertEqual(len(refusals), 1, events)
        self.assertEqual(refusals[0]["detail"]["gate"], "record-fields-gate", events)

    def test_eof_with_pending_candidate_and_no_result_line_flushes_unverified(self):
        # 이슈 #246 결함 1 (S1/S3): 세션이 터미널 result 줄 없이 끝난다 —
        # 크래시/kill/truncation(S1)과 그 줄 자체가 malformed JSON(S3)은
        # `_spawn_one` 관점에서 같은 관찰(루프가 result 줄 없이 EOF)로
        # 수렴한다. 이미 층 분류된 후보를 메모리에서 잃지 않고
        # unverified-refusal 로 flush 한다 — 확정 라벨(gate-refusal)을
        # 참칭하지 않는다.
        text = ("PreToolUse:Write hook error: [/plugins/tokenmaxxxer-core/"
                "core/hooks/some-gate.sh] some-gate: refused — 잘린 세션")
        tool_use = self._tool_use_line("t1", "Write")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text}]}})
        events = self._run(tempfile.mkdtemp(), tool_use + "\n" + tool_result + "\n")
        self.assertEqual(len([e for e in events if e["type"] == "unverified-refusal"]), 1,
                         events)
        self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)

    def test_result_line_with_untrustworthy_permission_denials_shape_flushes_unverified(self):
        # 이슈 #246 결함 1 (S2): permission_denials 가 absent/None/truthy
        # non-list 면 형태를 신뢰할 수 없다 — `or []`가 이 셋을 "확정 0건"과
        # 구분 없이 뭉갰던 게 원래 결함이었다. 셋 다 같은 unverified-refusal
        # 경로로 간다; 확정된 빈 리스트([])는 별도로
        # test_zero_denials_session_with_gate_marker_in_error_output_fires_nothing
        # 가 이미 "아무 것도 안 남" 을 고정한다.
        text = ("PreToolUse:Write hook error: [/plugins/tokenmaxxxer-core/"
                "core/hooks/some-gate.sh] some-gate: refused — 형태 불량")
        cases = {
            "absent": {"type": "result", "is_error": False},
            "none": {"type": "result", "is_error": False, "permission_denials": None},
            "string": {"type": "result", "is_error": False,
                      "permission_denials": "oops"},
        }
        for label, result_obj in cases.items():
            with self.subTest(shape=label):
                tool_use = self._tool_use_line("t1", "Write")
                tool_result = json.dumps({"type": "user", "message": {"content": [
                    {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
                     "content": text}]}})
                result_line = json.dumps(result_obj)
                events = self._run(tempfile.mkdtemp(),
                                   tool_use + "\n" + tool_result + "\n" + result_line + "\n")
                self.assertEqual(
                    len([e for e in events if e["type"] == "unverified-refusal"]), 1, events)
                self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)

    def test_two_distinct_same_layer_denials_produce_two_distinct_events(self):
        # 이슈 #246 결함 2: 층 전체를 가리는 옛 dedup 키(예: ("harness",))는
        # 첫 번째 텍스트만 남기고 두 번째(진짜 거부일 수 있는) detail 을
        # 잃었다 — 정규화된 텍스트를 키에 포함해 서로 다른 두 사유가 둘 다
        # 살아남는다.
        text1 = "Permission to use Bash has been denied"
        text2 = "This command requires approval"
        tool_use1 = self._tool_use_line("t1", "Bash")
        tool_result1 = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text1}]}})
        tool_use2 = self._tool_use_line("t2", "Bash")
        tool_result2 = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t2",
             "content": text2}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Bash"},
                                                          {"tool_name": "Bash"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use1 + "\n" + tool_result1 + "\n" +
                           tool_use2 + "\n" + tool_result2 + "\n" + result_line + "\n")
        harness = [e for e in events if e["type"] == "harness-refusal"]
        self.assertEqual(len(harness), 2, events)
        self.assertEqual({h["detail"] for h in harness}, {text1, text2}, events)
        self.assertFalse([e for e in events if e["type"] == "unclassified-refusal"], events)

    def test_two_identical_same_layer_denials_still_collapse_to_one(self):
        # 회귀 방지: 정확히 같은 detail 은 여전히 한 번만 — 이슈
        # #235/spawn.py:2619-2622 의 "같은 detail 은 한 번" 의도가 텍스트를
        # 키에 포함시킨 뒤에도 유지된다.
        text = "Permission to use Bash has been denied"
        tool_use1 = self._tool_use_line("t1", "Bash")
        tool_result1 = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text}]}})
        tool_use2 = self._tool_use_line("t2", "Bash")
        tool_result2 = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t2",
             "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Bash"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use1 + "\n" + tool_result1 + "\n" +
                           tool_use2 + "\n" + tool_result2 + "\n" + result_line + "\n")
        self.assertEqual(len([e for e in events if e["type"] == "harness-refusal"]), 1, events)

    def test_two_hook_paths_sharing_filename_stem_are_not_collapsed(self):
        # 이슈 #246 결함 2: `Path(...).stem` 만으로 걸면 서로 다른 디렉터리의
        # 동일 파일명 hook(둘 다 "some-gate")이 충돌했다 — 키는 이제 hook 의
        # 전체 경로를 쓴다. `detail["gate"]` 표시 필드는 여전히 stem.
        text1 = ("PreToolUse:Write hook error: [/plugins/a/some-gate.sh] "
                "some-gate: refused — 사유 A")
        text2 = ("PreToolUse:Write hook error: [/plugins/b/some-gate.sh] "
                "some-gate: refused — 사유 B")
        tool_use1 = self._tool_use_line("t1", "Write")
        tool_result1 = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text1}]}})
        tool_use2 = self._tool_use_line("t2", "Write")
        tool_result2 = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t2",
             "content": text2}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Write"},
                                                          {"tool_name": "Write"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use1 + "\n" + tool_result1 + "\n" +
                           tool_use2 + "\n" + tool_result2 + "\n" + result_line + "\n")
        refusals = [e for e in events if e["type"] == "gate-refusal"]
        self.assertEqual(len(refusals), 2, events)
        self.assertEqual({r["detail"]["gate"] for r in refusals}, {"some-gate"}, events)
        self.assertEqual({r["detail"]["reason"] for r in refusals}, {"사유 A", "사유 B"}, events)

    def test_whitespace_variant_same_layer_denials_still_collapse_to_one(self):
        # 이슈 #246 dedup 키 텍스트 정규화: multi-block tool_result 가 넣는
        # 내부 개행(`_tool_result_text`의 "\n".join)과 우연한 공백 차이는
        # 사유가 실질적으로 같으면 같은 키로 뭉쳐야 한다. denials 를 일부러
        # 2건 실어 둔다 — 정규화가 안 됐다면 두 후보가 서로 다른 키로 갈려
        # 둘 다(2건) fire 하고 남는 denial 이 없다; 정규화가 됐다면 후보가
        # 1개뿐이라 1건만 fire 하고 나머지 denial 1건이 unclassified-refusal
        # 로 남는다 — 그 잔여가 정규화가 실제로 일어났다는 증거다.
        text1 = "mkdir: /tmp/foo: Operation not permitted"
        tool_use1 = self._tool_use_line("t1", "Write")
        tool_result1 = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text1}]}})
        tool_use2 = self._tool_use_line("t2", "Write")
        tool_result2 = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t2", "content": [
                {"type": "text", "text": "mkdir: /tmp/foo:"},
                {"type": "text", "text": "Operation not permitted"}]}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Write"},
                                                          {"tool_name": "Write"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use1 + "\n" + tool_result1 + "\n" +
                           tool_use2 + "\n" + tool_result2 + "\n" + result_line + "\n")
        self.assertEqual(len([e for e in events if e["type"] == "sandbox-refusal"]), 1, events)
        self.assertTrue([e for e in events if e["type"] == "unclassified-refusal"], events)

    def test_denial_entry_missing_tool_name_still_fires_unclassified_fallback(self):
        # 헌트 finding 2: permission_denials 항목이 dict 가 아니거나
        # tool_name 이 없으면 Counter 에서 그냥 빠진다 — 그 항목을 leftover
        # 판정에도 안 넣으면, 매치될 수 없는 denial 자체가 흔적 없이
        # 사라진다(이슈 #246 결함 1 이 없애려던 "0건 = 무해"를 다른 문으로
        # 재도입). 후보의 tool_name 이 그 이상한 모양과 매치되지 않아 real
        # layer 로는 안 뜨더라도, unclassified-refusal 폴백은 반드시 떠야
        # 한다.
        text = "Permission to use Bash has been denied"
        tool_use = self._tool_use_line("t1", "Bash")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"other_field": "Bash"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use + "\n" + tool_result + "\n" + result_line + "\n")
        self.assertTrue([e for e in events if e["type"] == "unclassified-refusal"], events)
        self.assertFalse([e for e in events if e["type"] == "harness-refusal"], events)

    def test_unresolved_tool_use_id_with_well_shaped_denials_degrades_to_unclassified(self):
        # 헌트 finding 3 (커버리지 공백 메움): 후보의 tool_use_id 가 못
        # 풀렸어도(예: assistant 의 tool_use 줄 자체가 유실됐다면) denials 가
        # 정상 모양이면 폴백으로 정확히 떨어져야 한다 — 확정 라벨을
        # 참칭하지 않되, 조용히 사라지지도 않는다. assistant tool_use 줄을
        # 아예 안 보내 tool_use_id 를 의도적으로 못 풀리게 한다.
        text = "Permission to use Bash has been denied"
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "unknown-id",
             "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Bash"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_result + "\n" + result_line + "\n")
        self.assertTrue([e for e in events if e["type"] == "unclassified-refusal"], events)
        self.assertFalse([e for e in events if e["type"] == "harness-refusal"], events)

    def test_repeated_result_line_does_not_double_flush(self):
        # 헌트 finding 5: 옛 코드는 refusals_seen 이 세션 전체에 걸쳐 남아
        # 두 번째 result 줄에 대해 flush 가 no-op 이었다 — result 가 "언제나
        # 스트림의 마지막 줄"이라는 가정은 문서화만 됐을 뿐 강제되지 않는다
        # (docs/issue-235/reports/execution-observation/research-evidence.md:160-164).
        # result_seen 가드가 두 번째 result 줄에서 재-flush 를 막는다.
        text = "Permission to use Bash has been denied"
        tool_use = self._tool_use_line("t1", "Bash")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Bash"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use + "\n" + tool_result + "\n" +
                           result_line + "\n" + result_line + "\n")
        self.assertEqual(len([e for e in events if e["type"] == "harness-refusal"]), 1, events)

    def test_pr_opened_does_not_refire_across_respawns(self):
        # issue-123 survey fixture: PR #124's URL, echoed again on a later
        # respawn of the same workspace, must not append a second
        # pr-opened event — dedup is durable across process restarts.
        td = tempfile.mkdtemp()
        url = "https://github.com/o/r/pull/124"
        pr_for_branch = lambda *a, **k: 124  # 이 브랜치의 실제 PR — 두 respawn 모두 같은 값
        self._run(td, url + "\n", pr_for_branch=pr_for_branch)
        events = self._run(td, "이미 있는 PR 링크를 또 echo 한다: " + url + "\n",
                           pr_for_branch=pr_for_branch)
        opened = [e for e in events if e["type"] == "pr-opened" and e["detail"] == url]
        self.assertEqual(len(opened), 1, events)

    def test_read_only_repo_url_does_not_fire_pr_opened_when_no_pr_exists(self):
        # issue-180 실측: 세션이 자기 레포 PR URL 을 텍스트로 읽기만 했다 —
        # `_pr_for_branch` 는 이 브랜치에 PR 이 없다는 뜻으로 None 을 낸다.
        url = "https://github.com/tokenmaxxxer/on-the-record/pull/142"
        events = self._run(tempfile.mkdtemp(), url + "\n",
                           pr_for_branch=lambda *a, **k: None)
        self.assertFalse([e for e in events if e["type"] == "pr-opened"], events)

    def test_read_only_repo_url_does_not_fire_pr_opened_when_different_pr_open(self):
        # 언급된 번호(142)와 실제 열린 PR 번호(99)가 다르면 여전히 "읽기만"이다.
        url = "https://github.com/tokenmaxxxer/on-the-record/pull/142"
        events = self._run(tempfile.mkdtemp(), url + "\n",
                           pr_for_branch=lambda *a, **k: 99)
        self.assertFalse([e for e in events if e["type"] == "pr-opened"], events)

    def test_pull_new_branch_url_does_not_fire_pr_opened(self):
        # 이슈가 명시적으로 요청한 신규 케이스: `git push` 안내가 찍는
        # `.../pull/new/<branch>` 는 PR 번호가 없어 `_PR_URL_RE` 자체가 안 잡는다.
        calls = []
        url = "https://github.com/tokenmaxxxer/on-the-record/pull/new/issue-180/implementation"
        events = self._run(tempfile.mkdtemp(), url + "\n",
                           pr_for_branch=lambda *a, **k: calls.append(a) or 555)
        self.assertFalse([e for e in events if e["type"] == "pr-opened"], events)
        self.assertEqual(calls, [])  # 후보가 아예 안 뽑혔으니 gh 도 안 불렸다

    def test_actually_opened_pr_fires_pr_opened(self):
        # 실패 신호(제안서): 이게 없으면 "영원한 대기" 회귀를 못 잡는다.
        url = "https://github.com/tokenmaxxxer/on-the-record/pull/555"
        events = self._run(tempfile.mkdtemp(), url + "\n",
                           pr_for_branch=lambda *a, **k: 555)
        opened = [e for e in events if e["type"] == "pr-opened"]
        self.assertEqual(opened, [{"ts": opened[0]["ts"], "type": "pr-opened",
                                   "detail": url}], events)

    def test_pr_opened_reports_new_pr_not_stale_merged_pr_on_reused_branch(self):
        # issue-576: 같은 head 브랜치를 재사용한 라운드에서 이전 PR(#479)이
        # 이미 머지돼 있고 새 PR(#555)이 방금 열렸다 — `_open_pr_for_branch`
        # 는 (`gh pr list --state open`처럼) OPEN 인 새 PR 번호만 낸다. 옛
        # 머지 PR URL 을 세션이 언급해도 pr-opened 는 새 PR 로만 서야 한다.
        merged_url = "https://github.com/tokenmaxxxer/on-the-record/pull/479"
        new_url = "https://github.com/tokenmaxxxer/on-the-record/pull/555"
        events = self._run(tempfile.mkdtemp(), merged_url + "\n" + new_url + "\n",
                           pr_for_branch=lambda *a, **k: 555)
        opened = [e["detail"] for e in events if e["type"] == "pr-opened"]
        self.assertEqual(opened, [new_url], events)

    def test_pr_for_branch_call_count_not_proportional_to_candidate_urls(self):
        # PR #184 리뷰 코멘트의 수용 기준: 브랜치의 실제 PR 번호가 한 번
        # 풀리고 나면, 그 뒤 후보 URL 이 몇 개 더 나와도(실측: 세션 하나가
        # 5개 이상 흘렸다) _pr_for_branch 는 다시 불리지 않는다.
        calls = []

        def counting(root, br):
            calls.append((str(root), br))
            return 555

        urls = [f"https://github.com/tokenmaxxxer/on-the-record/pull/{n}\n"
               for n in (1, 142, 124, 555, 142, 7, 8, 555)]  # 8개 후보, 서로 다른 번호 다수
        events = self._run(tempfile.mkdtemp(), "".join(urls),
                           pr_for_branch=counting)
        self.assertEqual(len(calls), 1, calls)  # 후보 8개인데 호출은 1번
        opened = [e["detail"] for e in events if e["type"] == "pr-opened"]
        self.assertEqual(opened, ["https://github.com/tokenmaxxxer/on-the-record/pull/555"])

    def test_pr_for_branch_keeps_retrying_while_unresolved(self):
        # 위 메모이제이션이 "PR 이 아직 없을 때의 재시도" 성질까지 죽이면
        # 안 된다 — None 인 동안은 새 후보마다 계속 다시 묻는다.
        calls = []

        def always_none(root, br):
            calls.append((str(root), br))
            return None

        urls = [f"https://github.com/tokenmaxxxer/on-the-record/pull/{n}\n"
               for n in (1, 142, 124)]
        events = self._run(tempfile.mkdtemp(), "".join(urls), pr_for_branch=always_none)
        self.assertEqual(len(calls), 3, calls)  # 미해결 상태론 후보마다 재시도
        self.assertFalse([e for e in events if e["type"] == "pr-opened"], events)


@pytest.mark.slow

class ProgressEvents(unittest.TestCase):
    """이슈 #180 ②: 세션 진행(산출물 쓰기 + 검증/커밋/푸시)이 `events.jsonl` 에
    `progress` 로 남는다 — 탐색성 호출은 안 남는다(입도 실패 방지).

    issue #1490 rework: `EventReporting`과 같은 이유로 slow 티어."""

    def _run(self, td, lines):
        return EventReporting()._run(td, "\n".join(json.dumps(l) for l in lines) + "\n")

    def test_write_tool_use_fires_progress(self):
        events = self._run(tempfile.mkdtemp(), [
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Write",
                 "input": {"file_path": "docs/issue-180/reports/implementation.md"}},
            ]}},
        ])
        progress = [e for e in events if e["type"] == "progress"]
        self.assertEqual(progress, [{"ts": progress[0]["ts"], "type": "progress",
                                     "detail": {"kind": "tool_use",
                                                "detail": "Write docs/issue-180/reports/implementation.md"}}])

    def test_consecutive_writes_to_same_file_are_deduped(self):
        events = self._run(tempfile.mkdtemp(), [
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Edit", "input": {"file_path": "spawn.py"}},
            ]}},
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Edit", "input": {"file_path": "spawn.py"}},
            ]}},
        ])
        self.assertEqual(len([e for e in events if e["type"] == "progress"]), 1, events)

    def test_writes_to_different_files_both_fire(self):
        events = self._run(tempfile.mkdtemp(), [
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Write", "input": {"file_path": "a.py"}},
            ]}},
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Write", "input": {"file_path": "b.py"}},
            ]}},
        ])
        self.assertEqual(len([e for e in events if e["type"] == "progress"]), 2, events)

    def test_verification_and_commit_commands_fire_progress(self):
        for command in ("git commit -q -m x", "git push -q", "gh pr create --title t",
                        "python3 tests/test_spawn.py", "python3 gates/ci.py ."):
            with self.subTest(command=command):
                events = self._run(tempfile.mkdtemp(), [
                    {"type": "assistant", "message": {"content": [
                        {"type": "tool_use", "name": "Bash", "input": {"command": command}},
                    ]}},
                ])
                progress = [e for e in events if e["type"] == "progress"]
                self.assertEqual(len(progress), 1, events)
                self.assertEqual(progress[0]["detail"]["kind"], "tool_use")

    def test_exploratory_bash_does_not_fire_progress(self):
        # 실패 신호(제안서): 이게 서면 알림 폭탄이 재현된 것이다.
        for command in ("ls docs/", "grep -rn foo .", "cat spawn.py", "git status",
                        "git diff"):
            with self.subTest(command=command):
                events = self._run(tempfile.mkdtemp(), [
                    {"type": "assistant", "message": {"content": [
                        {"type": "tool_use", "name": "Bash", "input": {"command": command}},
                    ]}},
                ])
                self.assertFalse([e for e in events if e["type"] == "progress"], events)

    def test_refusal_parsing_still_works_alongside_progress(self):
        # 거부 판별과 같은 obj 를 재사용하도록 바꾼 뒤에도 기존 동작이
        # 그대로인지 — result 라인은 여전히 result 로만 처리된다. 여기엔
        # 층을 확정할 tool_result 줄이 없으니 unclassified-refusal 이 된다
        # (이슈 #232) — 예전엔 이 케이스가 gate-refusal 이었다.
        events = self._run(tempfile.mkdtemp(), [
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Write", "input": {"file_path": "x.py"}},
            ]}},
            {"type": "result", "is_error": False,
             "permission_denials": [{"tool_name": "Write"}]},
        ])
        self.assertEqual(len([e for e in events if e["type"] == "progress"]), 1, events)
        self.assertEqual(len([e for e in events if e["type"] == "unclassified-refusal"]), 1, events)

class Clean(unittest.TestCase):
    def _make_clean_repo(self, path: Path, remote: Path) -> None:
        __import__("subprocess").run(
            ["git", "init", "-q", "--bare", str(remote)], check=True)
        path.mkdir(parents=True)
        run = lambda *args: __import__("subprocess").run(
            args, cwd=str(path), capture_output=True, text=True, check=True)
        run("git", "init", "-q")
        run("git", "config", "user.email", "t@example.com")
        run("git", "config", "user.name", "t")
        (path / "f.txt").write_text("x")
        run("git", "add", "f.txt")
        run("git", "commit", "-q", "-m", "init")
        run("git", "remote", "add", "origin", str(remote))
        run("git", "push", "-q", "-u", "origin", "HEAD:main")

    def test_keeps_live_session_workspace_but_deletes_dead_sibling(self):
        with tempfile.TemporaryDirectory() as td:
            wb = Path(td) / "work"
            wb.mkdir()
            live_ws = wb / "issue-51-coding"
            dead_ws = wb / "issue-51-review"
            self._make_clean_repo(live_ws, Path(td) / "remote-live.git")
            self._make_clean_repo(dead_ws, Path(td) / "remote-dead.git")

            roster_path = Path(td) / "runs" / "active.json"
            roster_path.parent.mkdir(parents=True)
            roster_path.write_text(json.dumps({
                "issue-51/coding": {
                    "pid": os.getpid(),
                    "work": str(live_ws),
                    "issue": 51,
                    "role": "implementation",
                }
            }))

            old_roster = spawn.ROSTER
            old_argv = sys.argv
            old_environ = dict(os.environ)
            spawn.ROSTER = roster_path
            os.environ["MUSTER_WORK_DIR"] = str(wb)
            sys.argv = ["spawn.py", "clean"]
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                spawn.main()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                sys.argv = old_argv
                os.environ.clear()
                os.environ.update(old_environ)

            out = buf.getvalue()
            self.assertTrue(live_ws.is_dir())
            self.assertIn("실행 중인 세션 있음", out)
            self.assertFalse(dead_ws.exists())

    def test_removes_all_generation_logs_and_sibling_files(self):
        # 이슈 #192 요구사항 4: 재스폰 세대마다 로그가 늘어나므로, `clean`
        # 은 고정 접미사 하나가 아니라 워크스페이스-이름 프리픽스의 형제
        # 파일을 전부(세대별 로그 2개 이상 + events.jsonl + task.txt +
        # respawn-claim 락 파일) 치워야 한다. 살아있는 세션의 형제 파일은
        # 그대로 남는다.
        with tempfile.TemporaryDirectory() as td:
            wb = Path(td) / "work"
            wb.mkdir()
            live_ws = wb / "issue-51-coding"
            dead_ws = wb / "issue-51-review"
            self._make_clean_repo(live_ws, Path(td) / "remote-live.git")
            self._make_clean_repo(dead_ws, Path(td) / "remote-dead.git")

            live_siblings = [
                Path(str(live_ws) + ".session.20260802T150000.111.log"),
                Path(str(live_ws) + ".events.jsonl"),
            ]
            dead_siblings = [
                Path(str(dead_ws) + ".session.20260802T140000.222.log"),
                Path(str(dead_ws) + ".session.20260802T150500.333.log"),
                Path(str(dead_ws) + ".events.jsonl"),
                Path(str(dead_ws) + ".events.offset"),
                Path(str(dead_ws) + ".task.txt"),
                Path(str(dead_ws) + ".respawn-claim-20260802T140500"),
            ]
            for p in live_siblings + dead_siblings:
                p.write_text("x")

            roster_path = Path(td) / "runs" / "active.json"
            roster_path.parent.mkdir(parents=True)
            roster_path.write_text(json.dumps({
                "issue-51/coding": {
                    "pid": os.getpid(),
                    "work": str(live_ws),
                    "issue": 51,
                    "role": "implementation",
                }
            }))

            old_roster = spawn.ROSTER
            old_argv = sys.argv
            old_environ = dict(os.environ)
            spawn.ROSTER = roster_path
            os.environ["MUSTER_WORK_DIR"] = str(wb)
            sys.argv = ["spawn.py", "clean"]
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                spawn.main()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                sys.argv = old_argv
                os.environ.clear()
                os.environ.update(old_environ)

            self.assertTrue(live_ws.is_dir())
            for p in live_siblings:
                self.assertTrue(p.exists(), p)
            self.assertFalse(dead_ws.exists())
            for p in dead_siblings:
                self.assertFalse(p.exists(), p)

    def test_directory_sibling_does_not_abort_the_clean_loop(self):
        # issue #205 defect 3: a directory sibling in the glob used to hit
        # sibling.unlink() unguarded and raise IsADirectoryError, aborting
        # the whole clean loop before later workspaces were reached. The
        # glob currently only ever matches files, so this is latent — the
        # guard must not crash and must still let the rest of the sweep run.
        with tempfile.TemporaryDirectory() as td:
            wb = Path(td) / "work"
            wb.mkdir()
            dead_ws_a = wb / "issue-51-review"
            dead_ws_b = wb / "issue-52-review"
            self._make_clean_repo(dead_ws_a, Path(td) / "remote-a.git")
            self._make_clean_repo(dead_ws_b, Path(td) / "remote-b.git")

            dir_sibling = Path(str(dead_ws_a) + ".somedir")
            dir_sibling.mkdir()
            (dir_sibling / "inner.txt").write_text("x")
            file_sibling = Path(str(dead_ws_a) + ".events.jsonl")
            file_sibling.write_text("x")

            roster_path = Path(td) / "runs" / "active.json"
            roster_path.parent.mkdir(parents=True)
            roster_path.write_text(json.dumps({}))

            old_roster = spawn.ROSTER
            old_argv = sys.argv
            old_environ = dict(os.environ)
            spawn.ROSTER = roster_path
            os.environ["MUSTER_WORK_DIR"] = str(wb)
            sys.argv = ["spawn.py", "clean"]
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                spawn.main()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                sys.argv = old_argv
                os.environ.clear()
                os.environ.update(old_environ)

            self.assertFalse(dead_ws_a.exists())
            self.assertFalse(dead_ws_b.exists())
            self.assertFalse(file_sibling.exists())
            self.assertTrue(dir_sibling.is_dir())

    @pytest.mark.slow
    def test_readonly_file_is_removed_via_chmod_retry(self):
        # issue #229: a read-only file (e.g. Go module cache laid down by
        # `go mod download`) used to make bare shutil.rmtree() raise
        # PermissionError. clean must chmod it writable and retry.
        with tempfile.TemporaryDirectory() as td:
            wb = Path(td) / "work"
            wb.mkdir()
            dead_ws = wb / "issue-51-review"
            self._make_clean_repo(dead_ws, Path(td) / "remote-dead.git")

            # Go's module cache marks the *directory*, not just the file,
            # read-only (0o555) — unlinking a file needs write permission
            # on its parent directory, not the file itself, so this is
            # what actually reproduces the PermissionError on POSIX.
            # Commit it first so `clean`'s git-status safety check still
            # judges the workspace safe to remove (matches the real Go
            # module cache case: it's untracked but .gitignore'd, so it
            # never shows up in `git status --porcelain`).
            ro_dir = dead_ws / "gomod_cache_pkg"
            ro_dir.mkdir()
            ro_file = ro_dir / "readonly.go"
            ro_file.write_text("package x")
            run = lambda *args: __import__("subprocess").run(
                args, cwd=str(dead_ws), capture_output=True, text=True,
                check=True)
            (dead_ws / ".gitignore").write_text("gomod_cache_pkg/\n")
            run("git", "add", ".gitignore")
            run("git", "commit", "-q", "-m", "ignore cache dir")
            run("git", "push", "-q", "origin", "HEAD:main")
            ro_dir.chmod(0o555)
            self.addCleanup(lambda: ro_dir.chmod(0o755) if ro_dir.exists() else None)

            roster_path = Path(td) / "runs" / "active.json"
            roster_path.parent.mkdir(parents=True)
            roster_path.write_text(json.dumps({}))

            old_roster = spawn.ROSTER
            old_argv = sys.argv
            old_environ = dict(os.environ)
            spawn.ROSTER = roster_path
            os.environ["MUSTER_WORK_DIR"] = str(wb)
            sys.argv = ["spawn.py", "clean"]
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                spawn.main()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                sys.argv = old_argv
                os.environ.clear()
                os.environ.update(old_environ)

            out = buf.getvalue()
            self.assertFalse(dead_ws.exists())
            self.assertIn("지움", out)
            self.assertNotIn("PermissionError", out)

    def test_failed_workspace_removal_does_not_abort_the_clean_loop(self):
        # issue #229: a workspace whose removal still fails after the
        # chmod retry (e.g. an unremovable parent dir) must not stop
        # clean from processing subsequent workspaces.
        with tempfile.TemporaryDirectory() as td:
            wb = Path(td) / "work"
            wb.mkdir()
            broken_ws = wb / "issue-51-review"
            healthy_ws = wb / "issue-52-review"
            self._make_clean_repo(broken_ws, Path(td) / "remote-a.git")
            self._make_clean_repo(healthy_ws, Path(td) / "remote-b.git")

            roster_path = Path(td) / "runs" / "active.json"
            roster_path.parent.mkdir(parents=True)
            roster_path.write_text(json.dumps({}))

            old_roster = spawn.ROSTER
            old_argv = sys.argv
            old_environ = dict(os.environ)
            spawn.ROSTER = roster_path
            os.environ["MUSTER_WORK_DIR"] = str(wb)
            sys.argv = ["spawn.py", "clean"]

            import shutil as _shutil
            real_rmtree = _shutil.rmtree

            def _rmtree_fails_for_broken(path, *args, **kwargs):
                if Path(path) == broken_ws:
                    raise PermissionError(f"simulated unremovable: {path}")
                return real_rmtree(path, *args, **kwargs)

            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with unittest.mock.patch.object(
                        _shutil, "rmtree", side_effect=_rmtree_fails_for_broken):
                    spawn.main()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                sys.argv = old_argv
                os.environ.clear()
                os.environ.update(old_environ)

            out = buf.getvalue()
            self.assertTrue(broken_ws.exists())
            self.assertFalse(healthy_ws.exists())
            self.assertIn("실패", out)
            self.assertIn("지움", out)

    def test_clean_issue_scopes_sweep_to_that_issue_only(self):
        # #288 N1: clean --issue N accepted the flag but swept every
        # workspace regardless. Pin: with issue 51 and 52 workspaces both
        # eligible for removal, `--issue 51` removes only 51's and leaves
        # 52's untouched, and 52 isn't even reported.
        with tempfile.TemporaryDirectory() as td:
            wb = Path(td) / "work"
            wb.mkdir()
            ws51 = wb / "myrepo-issue-51-coding"
            ws52 = wb / "myrepo-issue-52-coding"
            self._make_clean_repo(ws51, Path(td) / "remote-a.git")
            self._make_clean_repo(ws52, Path(td) / "remote-b.git")

            roster_path = Path(td) / "runs" / "active.json"
            roster_path.parent.mkdir(parents=True)
            roster_path.write_text(json.dumps({}))

            old_roster = spawn.ROSTER
            old_argv = sys.argv
            old_environ = dict(os.environ)
            spawn.ROSTER = roster_path
            os.environ["MUSTER_WORK_DIR"] = str(wb)
            sys.argv = ["spawn.py", "clean", "--issue", "51"]
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                spawn.main()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                sys.argv = old_argv
                os.environ.clear()
                os.environ.update(old_environ)

            out = buf.getvalue()
            self.assertFalse(ws51.exists())
            self.assertTrue(ws52.exists())
            self.assertNotIn(ws52.name, out)

    def test_clean_issue_with_no_matching_workspace_removes_nothing(self):
        # #288 N1 acceptance: clean --issue 424242 against workspaces that
        # exist for other issues must report zero removed/kept, not sweep
        # everything.
        with tempfile.TemporaryDirectory() as td:
            wb = Path(td) / "work"
            wb.mkdir()
            ws51 = wb / "myrepo-issue-51-coding"
            self._make_clean_repo(ws51, Path(td) / "remote-a.git")

            roster_path = Path(td) / "runs" / "active.json"
            roster_path.parent.mkdir(parents=True)
            roster_path.write_text(json.dumps({}))

            old_roster = spawn.ROSTER
            old_argv = sys.argv
            old_environ = dict(os.environ)
            spawn.ROSTER = roster_path
            os.environ["MUSTER_WORK_DIR"] = str(wb)
            sys.argv = ["spawn.py", "clean", "--issue", "424242"]
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                spawn.main()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                sys.argv = old_argv
                os.environ.clear()
                os.environ.update(old_environ)

            out = buf.getvalue()
            self.assertTrue(ws51.exists())
            self.assertIn("지움 0, 남김 0", out)

class RosterConcurrency(unittest.TestCase):
    """issue #139: 잠금 없는 read-modify-write 가 동시 등록을 잃어버렸던 문제."""

    def test_concurrent_register_survives(self):
        import threading

        with tempfile.TemporaryDirectory() as td:
            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster
            try:
                n = 20
                barrier = threading.Barrier(n)

                def register(i):
                    barrier.wait()
                    spawn.roster_register(f"issue-{i}/coding",
                                           {"pid": i, "role": "implementation",
                                            "issue": i, "ts": 0,
                                            "log": "", "work": ""})

                threads = [threading.Thread(target=register, args=(i,))
                           for i in range(n)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()

                d = json.loads(roster.read_text())
                self.assertEqual(len(d), n, d)
            finally:
                spawn.ROSTER = old_roster

class NoConcurrencyCap(unittest.TestCase):
    """issue #1510: operator decision 2026-08-15 — quota safety is owned by
    the #1498 guard and #1508 local-first observability, not by throttling
    parallelism. spawn.spawn_cmd() builds argv/env for a role session and
    carries no count-based gate; this locks that down as a regression test
    so a future change cannot silently reintroduce a concurrency cap.
    Respawn-attempt caps (RESPAWN_MAX_ATTEMPTS family) are a separate,
    explicitly out-of-scope concern — they bound retry loops, not
    how many sessions may run at once."""

    def test_no_concurrency_cap(self):
        n = 50
        results = [spawn.spawn_cmd(f"/tmp/s{i}.json", "execution-observation",
                                    unattended=False)
                   for i in range(n)]
        self.assertEqual(len(results), n)
        for cmd, env in results:
            self.assertIn("claude", cmd)
            self.assertEqual(env["CLAUDE_ROLE"], "execution-observation")

    def test_zero_running_sessions_spawns_normally(self):
        cmd, env = spawn.spawn_cmd("/tmp/s0.json", "execution-observation",
                                    unattended=False)
        self.assertIn("claude", cmd)
        self.assertEqual(env["CLAUDE_ROLE"], "execution-observation")

class FlowsPayload(unittest.TestCase):
    """issue #172: `spawn.py flows --json` payload — schema shape per section,
    all `gh`-hitting helpers monkeypatched (no live network in tests)."""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.addCleanup(self.td.cleanup)
        self._patched = []
        self._patch(spawn, "_repo_slug", lambda root: "acme/repo")
        self._patch(spawn, "_issue_comments", lambda root, n: ([], True))
        self._patch(spawn, "_roster_load", lambda: {})
        old_root = spawn.ROOT
        spawn.ROOT = self.root
        self.addCleanup(setattr, spawn, "ROOT", old_root)
        sys.path.insert(0, str((Path(spawn.__file__).parent / "gates").resolve()))
        import flows
        self.flows = flows
        self._patch(flows, "_pr_list_all", lambda root: ([], True))
        self._patch(flows, "_issue_list_all", lambda root: ([], True))

    def _patch(self, obj, name, fn):
        orig = getattr(obj, name)
        setattr(obj, name, fn)
        self.addCleanup(setattr, obj, name, orig)

    def _write_record(self, subject, role, loop_state, verdict=None, upstream=False):
        rec = self.root / spawn.BOARD / subject / "reports"
        rec.mkdir(parents=True, exist_ok=True)
        body = f"---\nloop_state: {loop_state}\n"
        if verdict:
            body += f"verdict: {verdict}\n"
        if upstream:
            body += "upstream:\n  - path: docs/issue-1/reports/other.md\n"
        body += "---\n"
        (rec / f"{role}.md").write_text(body, encoding="utf-8")

    def test_schema_top_level_keys(self):
        payload = self.flows.flows_payload(self.root)
        for key in ("schema_version", "generated_at", "repo", "decision_queue",
                    "flows", "sessions", "ledger", "hygiene"):
            self.assertIn(key, payload)
        self.assertIsInstance(payload["schema_version"], int)
        self.assertIsInstance(payload["hygiene"]["closure_sweep"], list)
        self.assertIsInstance(payload["hygiene"]["unapproved_open_prs"], list)

    def test_flows_section_stage_mapping_and_unmapped_fallback(self):
        self._write_record("issue-10", "product-discovery", "scope-proposed")
        self._write_record("issue-11", "product-discovery", "some-downstream-state")
        payload = self.flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertEqual(by_issue[10]["stage"], "proposal")
        self.assertTrue(by_issue[10]["stage_derived"])
        self.assertEqual(by_issue[11]["stage"], "some-downstream-state")
        self.assertFalse(by_issue[11]["stage_derived"])

    def test_decision_queue_from_open_pr(self):
        self._write_record("issue-20", "product-discovery", "scope-proposed")
        self._patch(self.flows, "_pr_list_all", lambda root: ([
            {"number": 99, "headRefName": "issue-20/product-discovery",
             "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
        ], True))
        payload = self.flows.flows_payload(self.root)
        self.assertEqual(len(payload["decision_queue"]), 1)
        entry = payload["decision_queue"][0]
        self.assertEqual(entry["pr"], 99)
        self.assertEqual(entry["phase"], 1)
        self.assertEqual(entry["awaiting"], "approve-scope")

    def test_decision_queue_from_open_pr_with_no_board_record(self):
        """issue #216 결함 1 회귀: 머지된 레코드도 계획 블록도 없는 이슈의
        PR(PR #86 재현)이 decision_queue 에 phase 1 로 떠야 한다."""
        self._patch(self.flows, "_pr_list_all", lambda root: ([
            {"number": 86, "headRefName": "issue-86/product-discovery",
             "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
        ], True))
        payload = self.flows.flows_payload(self.root)
        self.assertEqual(len(payload["decision_queue"]), 1)
        entry = payload["decision_queue"][0]
        self.assertEqual(entry["issue"], 86)
        self.assertEqual(entry["pr"], 86)
        self.assertEqual(entry["phase"], 1)
        self.assertEqual(entry["awaiting"], "approve-scope")

    def test_decision_queue_phase_2_when_board_record_is_scope_approved(self):
        """issue #216: 레코드가 scope-approved(scope-proposed 아님)면 기존대로
        phase 2 로 분류돼야 한다 — 회귀 방지."""
        self._write_record("issue-31", "implementation", "scope-approved")
        self._patch(self.flows, "_pr_list_all", lambda root: ([
            {"number": 56, "headRefName": "issue-31/implementation",
             "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
        ], True))
        payload = self.flows.flows_payload(self.root)
        self.assertEqual(len(payload["decision_queue"]), 1)
        entry = payload["decision_queue"][0]
        self.assertEqual(entry["phase"], 2)
        self.assertEqual(entry["awaiting"], "approve-full")

    def test_sessions_alive_is_pending_dead_looks_up_ledger(self):
        self._patch(spawn, "_roster_load", lambda: {
            "issue-5/coding": {"role": "coding", "issue": 5, "pid": 999999,
                               "ts": int(time.time())},
        })
        spawn.ledger_write({"role": "coding", "cost_usd": 1.0, "outcome": "progressed",
                           "board_delta": ["docs/issue-5/reports/coding.md"],
                           "repo": "repo"})
        payload = self.flows.flows_payload(self.root)
        self.assertEqual(len(payload["sessions"]), 1)
        s = payload["sessions"][0]
        # pid 999999 is assumed not alive in the test sandbox
        if not s["alive"]:
            self.assertEqual(s["verdict"], "progressed")

    def test_sessions_last_activity_from_tool_use_tail(self):
        log = self.root / "wk.session.log"
        log.write_text(
            json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": "writing the role file"},
                {"type": "tool_use", "name": "Write",
                 "input": {"file_path": "roles/data-modeling.json"}},
            ]}}) + "\n",
            encoding="utf-8")
        self._patch(spawn, "_roster_load", lambda: {
            "issue-5/coding": {"role": "coding", "issue": 5, "pid": 999999,
                               "ts": int(time.time()), "log": str(log)},
        })
        payload = self.flows.flows_payload(self.root)
        la = payload["sessions"][0]["last_activity"]
        self.assertEqual(la["kind"], "tool_use")
        self.assertEqual(la["detail"], "Write roles/data-modeling.json")
        self.assertRegex(la["ts"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_sessions_last_activity_none_when_no_log(self):
        self._patch(spawn, "_roster_load", lambda: {
            "issue-5/coding": {"role": "coding", "issue": 5, "pid": 999999,
                               "ts": int(time.time())},
        })
        payload = self.flows.flows_payload(self.root)
        self.assertIsNone(payload["sessions"][0]["last_activity"])

    def test_ledger_aggregation_per_issue_and_unattributed_bucket(self):
        spawn.ledger_write({"role": "coding", "cost_usd": 1.5, "outcome": "progressed",
                           "board_delta": ["docs/issue-7/reports/coding.md"],
                           "repo": "repo"})
        spawn.ledger_write({"role": "coding", "cost_usd": 0.5, "outcome": "refused",
                           "board_delta": [], "repo": "repo"})
        payload = self.flows.flows_payload(self.root)
        self.assertEqual(len(payload["ledger"]), 1)
        self.assertEqual(payload["ledger"][0]["issue"], 7)
        self.assertEqual(payload["ledger"][0]["sessions"], 1)
        self.assertAlmostEqual(payload["ledger"][0]["cost_usd_total"], 1.5)
        self.assertEqual(payload["unattributed"]["sessions"], 1)
        self.assertAlmostEqual(payload["unattributed"]["cost_usd_total"], 0.5)

    def test_ledger_filtered_by_repo_field_and_cwd_fallback(self):
        """issue #216 결함 2 회귀: `repo` 필드가 다른 엔트리는 걸러지고,
        `repo` 필드 없이 `cwd` 만 있는 옛 형태 엔트리도 basename 파싱으로
        올바르게 필터링돼야 한다(매칭/불일치 둘 다)."""
        spawn.ledger_write({"role": "coding", "cost_usd": 1.0, "outcome": "progressed",
                           "board_delta": ["docs/issue-8/reports/coding.md"],
                           "repo": "repo"})
        spawn.ledger_write({"role": "coding", "cost_usd": 5.0, "outcome": "progressed",
                           "board_delta": ["docs/issue-8/reports/coding.md"],
                           "repo": "other-repo"})
        spawn.ledger_write({"role": "coding", "cost_usd": 2.0, "outcome": "progressed",
                           "board_delta": ["docs/issue-9/reports/coding.md"],
                           "cwd": "/work/repo-issue-9-coding"})
        spawn.ledger_write({"role": "coding", "cost_usd": 9.0, "outcome": "progressed",
                           "board_delta": ["docs/issue-9/reports/coding.md"],
                           "cwd": "/work/other-repo-issue-9-coding"})
        payload = self.flows.flows_payload(self.root)
        by_issue = {l["issue"]: l for l in payload["ledger"]}
        self.assertEqual(set(by_issue), {8, 9})
        self.assertAlmostEqual(by_issue[8]["cost_usd_total"], 1.0)
        self.assertAlmostEqual(by_issue[9]["cost_usd_total"], 2.0)

    def test_hygiene_includes_closure_sweep_and_unapproved_prs(self):
        """issue #674: `closure_sweep` no longer passes through
        `find_violations()` — it stays empty and every board subject is
        reported as not-run-in-flows instead."""
        self._write_record("issue-30", "implementation", "scope-approved")
        self._patch(self.flows, "_pr_list_all", lambda root: ([
            {"number": 55, "headRefName": "issue-30/implementation",
             "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
        ], True))
        payload = self.flows.flows_payload(self.root)
        self.assertEqual(payload["hygiene"]["closure_sweep"], [])
        self.assertEqual(payload["hygiene"]["closure_sweep_skips"],
                         [{"subject": "issue-30", "reason": "not-run-in-flows"}])
        self.assertEqual(len(payload["hygiene"]["unapproved_open_prs"]), 1)
        self.assertEqual(payload["hygiene"]["unapproved_open_prs"][0]["pr"], 55)

    def test_flows_plan_is_null_without_plan_block(self):
        self._write_record("issue-40", "product-discovery", "scope-proposed")
        self._patch(self.flows, "_issue_list_all", lambda root: ([
            {"number": 40, "state": "OPEN", "body": "일반 이슈 본문, 계획 없음"},
        ], True))
        payload = self.flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertIsNone(by_issue[40]["plan"])

    def test_flows_plan_parses_step_lines(self):
        self._write_record("issue-41", "product-discovery", "scope-proposed")
        body = (
            "본문 설명\n\n"
            "## 실행 계획\n"
            "- [x] step 1  product-discovery\n"
            "- [ ] step 2  architecture ‖ security-threat-model\n"
            "\n## 다른 섹션\n"
            "무시되어야 하는 줄\n"
        )
        self._patch(self.flows, "_issue_list_all", lambda root: ([
            {"number": 41, "state": "OPEN", "body": body},
        ], True))
        payload = self.flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertEqual(by_issue[41]["plan"], [
            {"step": 1, "roles": ["product-discovery"], "done": True},
            {"step": 2, "roles": ["architecture", "security-threat-model"], "done": False},
        ])

    def test_flows_plan_only_issue_with_no_board_record_still_gets_entry(self):
        """requirement-4 gap this issue closes: an open issue with a plan
        block but zero merged role records still shows up in `flows[]`."""
        body = "## 실행 계획\n- [ ] step 1  product-discovery\n"
        self._patch(self.flows, "_issue_list_all", lambda root: ([
            {"number": 50, "state": "OPEN", "body": body},
        ], True))
        payload = self.flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertIn(50, by_issue)
        self.assertEqual(by_issue[50]["roles"], [])
        self.assertEqual(by_issue[50]["plan"],
                         [{"step": 1, "roles": ["product-discovery"], "done": False}])

    def test_flows_plan_skips_fenced_example_and_matches_variant_header(self):
        """issue #197 (issue-189 execution-observation finding 1 회귀): 실물
        이슈-189 본문은 펜스 안에 4-스텝 문법 견본(`## 실행 계획` 정확일치
        헤더)을 싣고, 실제 3-스텝 계획은 펜스 밖 변형 헤더
        (`## 실행 계획 (이 이슈 자체 — ...)`) 아래에 있다. 고쳐진 파서는 펜스
        안은 건너뛰고 변형 헤더를 매치해 실제 3-스텝을 낸다 — 펜스 안 4-스텝
        견본이 아니다. role 문자열의 em dash 설명 접미사는
        `_PLAN_STEP_RE`(불변)가 그대로 캡처하는 실물 결과이며 다듬지 않고
        그대로 단언한다(proposal Rationale, hunt pass 발견 사항)."""
        body = '## 배경\n\n스텝별 사람 확인(1단계 승인 / 2단계 머지)과 병렬 spawn 은 이미 동작한다. 없는 것은\n진행 형태를 사전에 합의해 **글로 남기는 자리**다. 지금 "다음은 누구"는 오케스트레이터의\n매 턴 판단으로만 존재하고 어디에도 기록되지 않는다.\n\n측정 (2026-08-02, 이 레포 `docs/issue-*/reports/`):\n\n```\n54개 이슈\n├─ 48개  역할 1개로 끝남           89%\n├─  5개  역할 2~3개 (최대 3)\n└─  0개  같은 역할이 두 번 돈 적 없음\n```\n\n즉 이 레포는 아직 멀티 스텝을 거의 안 써봤다. 계획 기능의 값어치는 반복 관리가 아니라\n**안 쓰던 병렬 스텝을 미리 짜두는 쪽**에 있다.\n\n## 요구사항\n\n1. 이슈를 열 때 사용자와 대화로 **실행 계획**(스텝 순서, 각 스텝의 룰북, 어느 스텝이\n   병렬인지)을 합의하고 이슈에 기록한다.\n2. 계획은 수정 가능하되 최소로. 수정 이력이 남을 것.\n3. **자동 진행 없음** — 스텝이 끝나면 사람 확인을 받고 다음 스텝을 spawn 한다.\n   이슈 #120의 "기계가 평가하는 라우팅 표 금지"는 그대로 유효하다.\n4. `repo-status-board` 에서 계획과 진척(현재 몇 번째 스텝, 각 스텝의 stage)을 본다.\n   이 이슈는 `flows --json` 쪽 데이터 계약까지만 책임진다 (§결정됨 D3).\n5. 계획이 소진되면 오케스트레이터가 보고하고, **사용자가 완료를 응답하면 이슈를 닫는다.**\n   자동 종결 아님 — `closure_sweep.py` 의 "탐지만, 종결은 사람 몫" 원칙 유지.\n\n## 이미 결정된 것 (대화에서 확정, 제안이 뒤집지 말 것)\n\n- **D1. 루프 문법을 만들지 않는다.** 위 측정대로 계획된 루프 사례가 0건이고, 가장\n  가까운 사례(이슈 #162: `coding.md` landed → `implementation.md` progressed,\n  "phase 2 follow-up: fix stale role names after PR #164")도 예정에 없던 사후\n  재작업이었다. 반복이 필요해지면 계획에 줄을 하나 더 붙인다 — #162가 실제로 그렇게\n  처리된 케이스다.\n- **D2. 종결은 사람이 한다.** 요구 5. 자동 종결 없음.\n- **D3. `repo-status-board` 레포 수정은 이 이슈 범위 밖.** 별도 이슈로 그쪽 레포에서\n  다룬다. 근거: 현행 계약이 브랜치(`issue-<n>/<role>`)와 보드 레코드(`docs/issue-<n>/`)를\n  레포 하나에 묶고 있어, 한 이슈로 두 레포를 다루면 레코드가 어디 남는지가 미정의다.\n  그 레포도 자체 보드다(`docs/specs/approvers.md` 보유).\n\n## 알려진 제약 (제안이 다룰 것)\n\n- `flows --json` 은 `gates/flows.py:flows_payload` → `spawn.board(root)` 위에 서 있고,\n  보드는 **머지된 레코드만** 본다. 이슈 생성 직후 ~ 첫 머지 전 구간은 flows 에 아예\n  나타나지 않는다. 계획은 생성 직후부터 보여야 하므로 **이것이 요구 4의 핵심 갭이다.**\n- stage 6개 값(`proposal`/`approval`/`implementation`/`verification`/`merge`/`close`)은\n  `gates/flows.py:_stage_for` 로 이미 나온다. 새로 만들 필요 없음.\n- `docs/specs/flows-schema.md` 는 `schema_version` 정수 하나로 관리되고 소비자 1개를\n  전제한다. 필드 추가 = 버전 범프. `repo-status-board` 레포가 이 스키마 문서의 **사본을\n  따로 들고 있다** — 동기화 필요 (실제 수정은 D3에 따라 별도 이슈).\n\n## 방향 (사용자 선호, 제안이 검토할 것)\n\n계획은 이슈 본문에 체크박스 목록으로. 새 파일·새 보드 레코드·새 게이트 없이,\n`gh issue edit` 로 수정하고 GitHub 편집 이력이 곧 요구 2의 감사 추적이 된다.\n병렬 스텝은 한 줄에 `‖` 로 묶는다.\n\n```markdown\n## 실행 계획\n- [ ] step 1  product-discovery\n- [ ] step 2  architecture ‖ security-threat-model\n- [ ] step 3  implementation\n- [ ] step 4  execution-observation ‖ conformance-review\n```\n\n## 실행 계획 (이 이슈 자체 — 요구 1의 첫 적용 사례)\n\n- [x] step 1  product-discovery — 요구사항·수용기준 확정, 위 갭에 대한 접근 결정\n- [x] step 2  implementation — 확정된 스펙대로 구현\n- [x] step 3  execution-observation — 실제 동작 확인\n\nstep 2 이후는 step 1 결과를 보고 조정한다 (요구 2의 "최소 수정" 대상).\n\n\n\n\n'
        self._patch(self.flows, "_issue_list_all", lambda root: ([
            {"number": 189, "state": "OPEN", "body": body},
        ], True))
        payload = self.flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertEqual(by_issue[189]["plan"], [
            {"step": 1, "roles": [
                "product-discovery — 요구사항·수용기준 확정, 위 갭에 대한 접근 결정"
            ], "done": True},
            {"step": 2, "roles": [
                "implementation — 확정된 스펙대로 구현"
            ], "done": True},
            {"step": 3, "roles": [
                "execution-observation — 실제 동작 확인"
            ], "done": True},
        ])

    def test_flows_plan_fenced_only_body_has_no_real_plan(self):
        """보조 합성 케이스(주 증거는 위 실물 픽스처) — 펜스 안에만 계획
        헤더가 있고 펜스 밖 실제 헤더가 없으면 계획 블록 없음(`None`)."""
        self._write_record("issue-51", "product-discovery", "scope-proposed")
        body = (
            "본문 설명\n\n"
            "```markdown\n"
            "## 실행 계획\n"
            "- [ ] step 1  product-discovery\n"
            "```\n"
        )
        self._patch(self.flows, "_issue_list_all", lambda root: ([
            {"number": 51, "state": "OPEN", "body": body},
        ], True))
        payload = self.flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertIsNone(by_issue[51]["plan"])

    def test_flows_plan_two_unfenced_headers_first_wins(self):
        """보조 합성 케이스 — 펜스 밖 계획 헤더가 둘이면 첫 번째만 파싱된다
        (저작 오류, run.md 저작 규칙)."""
        body = (
            "## 실행 계획\n"
            "- [ ] step 1  product-discovery\n"
            "## 실행 계획 (두 번째, 무시되어야 함)\n"
            "- [ ] step 9  implementation\n"
        )
        self._patch(self.flows, "_issue_list_all", lambda root: ([
            {"number": 52, "state": "OPEN", "body": body},
        ], True))
        payload = self.flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertEqual(by_issue[52]["plan"],
                         [{"step": 1, "roles": ["product-discovery"], "done": False}])

    def test_flows_prs_includes_open_prs_for_roles_with_no_board_record(self):
        """issue #248 재현 회귀 (issue-27 실물 사례): board 레코드가 있는
        role은 하나뿐이고(해당 role의 PR은 이미 머지돼 `pr_by_branch`에
        없음), 레코드 없는 두 role의 open PR이 있을 때 `flows[].prs`에
        그 두 PR 번호가 모두 채워져야 한다 — 이전에는 `roles`(레코드가
        있는 role만) 필터 때문에 빈 배열이었다."""
        self._write_record("issue-27", "implementation", "scope-approved")
        self._patch(self.flows, "_pr_list_all", lambda root: ([
            {"number": 31, "headRefName": "issue-27/execution-observation",
             "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
            {"number": 32, "headRefName": "issue-27/conformance-review",
             "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
        ], True))
        payload = self.flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertEqual(by_issue[27]["prs"], [31, 32])

    def test_flows_prs_and_decision_queue_share_the_same_pr_set(self):
        """issue #248 일관성 회귀: `decision_queue`에 등장하는 PR 번호는
        모두 같은 subject의 `flows[].prs`에도 포함된다 — 승인된 PR과
        미승인 PR을 섞어 `decision_queue`가 부분집합만 가질 때도
        `flows[].prs`는 열려 있는 PR 전체를 갖는지 확인한다."""
        (self.root / "docs" / "specs").mkdir(parents=True, exist_ok=True)
        (self.root / "docs" / "specs" / "approvers.md").write_text(
            "- reviewer1\n", encoding="utf-8")
        self._write_record("issue-45", "conformance-review", "scope-approved")
        self._write_record("issue-45", "execution-observation", "scope-approved")
        self._patch(self.flows, "_pr_list_all", lambda root: ([
            {"number": 101, "headRefName": "issue-45/conformance-review",
             "createdAt": "2026-07-30T00:00:00Z", "body": "",
             "reviews": [{"state": "APPROVED",
                         "author": {"login": "reviewer1"}}]},
            {"number": 102, "headRefName": "issue-45/execution-observation",
             "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
        ], True))
        payload = self.flows.flows_payload(self.root)
        dq_prs = {d["pr"] for d in payload["decision_queue"] if d["issue"] == 45}
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertEqual(dq_prs, {102})
        self.assertEqual(by_issue[45]["prs"], [101, 102])
        self.assertTrue(dq_prs.issubset(set(by_issue[45]["prs"])))

class SessionLastActivity(unittest.TestCase):
    """issue #172 FEEDBACK: `_session_last_activity` — tail-based session.log
    parse, never raises, `kind` covers tool_use/text/result."""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.log = Path(self.td.name) / "wk.session.log"
        sys.path.insert(0, str((Path(spawn.__file__).parent / "gates").resolve()))
        import flows
        self.flows = flows

    def test_none_when_log_missing(self):
        self.assertIsNone(self.flows._session_last_activity(self.log))

    def test_none_when_log_path_is_none(self):
        self.assertIsNone(self.flows._session_last_activity(None))

    def test_bash_tool_use_detail(self):
        self.log.write_text(
            json.dumps({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Bash",
                 "input": {"command": "pytest tests/test_spawn.py"}},
            ]}}) + "\n", encoding="utf-8")
        la = self.flows._session_last_activity(self.log)
        self.assertEqual(la["kind"], "tool_use")
        self.assertEqual(la["detail"], "pytest tests/test_spawn.py 실행")

    def test_result_record_detail(self):
        self.log.write_text(
            json.dumps({"type": "result", "subtype": "success",
                       "result": "done"}) + "\n", encoding="utf-8")
        la = self.flows._session_last_activity(self.log)
        self.assertEqual(la["kind"], "result")
        self.assertEqual(la["detail"], "done")

    def test_last_of_several_lines_wins(self):
        lines = [
            {"type": "assistant", "message": {"content": [
                {"type": "text", "text": "first"}]}},
            {"type": "assistant", "message": {"content": [
                {"type": "text", "text": "second"}]}},
        ]
        self.log.write_text("\n".join(json.dumps(l) for l in lines) + "\n",
                            encoding="utf-8")
        la = self.flows._session_last_activity(self.log)
        self.assertEqual(la["detail"], "second")

    def test_malformed_tail_yields_none_not_error(self):
        self.log.write_text("not json at all\n{also not json\n", encoding="utf-8")
        self.assertIsNone(self.flows._session_last_activity(self.log))

    def test_unreadable_log_yields_none_not_error(self):
        self.log.write_text("{}\n", encoding="utf-8")
        self.log.chmod(0o000)
        self.addCleanup(self.log.chmod, 0o644)
        self.assertIsNone(self.flows._session_last_activity(self.log))

class WatchFollow(unittest.TestCase):
    """이슈 #180 ③: `--follow` 는 `_await_bounded` 시그니처·동작을 바꾸지
    않고 반복 호출하기만 한다 — 가장 최근에 소비한 이벤트 타입이
    session-end 일 때만 멈춘다(실패 신호: 안 멈추면 영원한 대기)."""

    def setUp(self):
        self.td = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.td, ignore_errors=True)
        self.work = Path(self.td) / "wk"
        self.work.mkdir()
        self.events = spawn._events_path(self.work)
        self.offset = spawn._offset_path(self.work)
        self.log = Path(str(self.work) + ".session.log")
        self.log.write_text("")
        old_idx = spawn.WORKSPACE_INDEX
        spawn.WORKSPACE_INDEX = Path(self.td) / "workspaces.json"
        self.addCleanup(setattr, spawn, "WORKSPACE_INDEX", old_idx)
        spawn._workspace_index_put(180, "implementation", str(self.work), str(self.log))
        # 로스터에 살아있는 wrapper_pid(자기 자신)를 심어 둔다 — 이슈 #224의
        # pid 사망 감지가 기존 stall 회귀 테스트를 오탐으로 깨지 않는지
        # 명시적으로 지킨다. `pid`(claude 서브프로세스 자리)는 아무 값이나
        # 넣어도 무방하다 — `_watch` 의 크래시 판정은 `wrapper_pid` 만
        # 본다.
        old_roster = spawn.ROSTER
        spawn.ROSTER = Path(self.td) / "active.json"
        self.addCleanup(setattr, spawn, "ROSTER", old_roster)
        spawn.roster_register("issue-180/implementation", {
            "pid": 999999, "wrapper_pid": os.getpid(), "role": "implementation",
            "issue": 180, "ts": int(time.time()), "work": str(self.work),
            "log": str(self.log)})

    def test_follow_stops_only_at_session_end(self):
        from unittest import mock
        spawn._append_event(self.events, "progress", {"kind": "tool_use", "detail": "x"})
        spawn._append_event(self.events, "gate-refusal", "denied")
        spawn._append_event(self.events, "session-end", "progressed")
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path, **kwargs):
            calls.append(1)
            seen = spawn._read_offset(offset_path)
            lines = events_path.read_text(encoding="utf-8").splitlines()
            if seen < len(lines):
                spawn._write_offset(offset_path, seen + 1)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(180, "implementation", 5.0, follow=True)
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 3, calls)  # progress, gate-refusal, session-end — 각 한 번

    def test_follow_ignores_stall_and_keeps_going(self):
        from unittest import mock
        spawn._append_event(self.events, "session-end", "progressed")
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path, **kwargs):
            calls.append(1)
            if len(calls) < 3:
                return 0  # stall 흉내: offset 은 그대로
            spawn._write_offset(offset_path, spawn._read_offset(offset_path) + 1)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(180, "implementation", 5.0, follow=True)
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 3, calls)  # stall 2번을 지나 session-end 에서만 멈춘다

    def test_follow_detects_dead_session_and_returns_crash_rc(self):
        # 이슈 #224 결함 3: 세션이 크래시해 session-end 가 영영 안 오면
        # --follow 가 무한정 stall 을 반복하면 안 된다 — 로스터 엔트리는
        # 있지만 그 wrapper_pid 가 죽어 있으면(PR #255 피드백 1: session-end
        # 가 이미 잔여로 남아있지 않은 경우에만) 유한 반복 안에
        # WATCH_CRASH_RC 로 리턴한다. 이 events.jsonl 에는 session-end 가
        # 전혀 없다(크래시 세션이라 못 남겼다).
        # 이슈 #266으로 갱신: 이전에는 로스터 엔트리 부재 자체를 pid 사망과
        # 동치로 다뤄 이 시나리오를 재현했으나, #266이 그 동치를 깼다(엔트리
        # 부재는 더 이상 사망 신호가 아니다) — 실제로 남아 있어야 하는
        # 트리거(엔트리는 존재, wrapper_pid 는 죽음)를 여기서 직접
        # 구성한다.
        from unittest import mock
        dead = subprocess.Popen(["true"])
        dead.wait()
        spawn.roster_register("issue-180/implementation", {
            "pid": 999999, "wrapper_pid": dead.pid, "role": "implementation",
            "issue": 180, "ts": int(time.time()), "work": str(self.work),
            "log": str(self.log)})
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path, **kwargs):
            calls.append(1)
            return 0  # 매번 stall 흉내 — offset 진행 없음

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(180, "implementation", 5.0, follow=True)
        self.assertEqual(rc, spawn.WATCH_CRASH_RC)
        self.assertLess(len(calls), 5, calls)  # 유한 반복 — 무한 루프 없음

    def test_follow_prioritizes_pending_session_end_over_pid_check(self):
        # PR #255 피드백 1의 벤인 레이스: 세션이 정상 종료해 session-end 를
        # 이미 events.jsonl 에 남겼는데(progress 다음 줄), 그 줄이 아직
        # 소비되지 않은 첫 반복에서 pid 가 죽어 있어도 잔여 session-end 를
        # 먼저 소진해야지, 그 반복에서 곧장 크래시로 오판하면 안 된다 —
        # spawn.py:1943-1953 의 드레인-우선 블록이 지키는 순서.
        #
        # 이슈 #271 관찰(survey.md §5): 이전 버전은 로스터 엔트리를
        # `roster_remove`로 아예 지워 죽음 신호를 흉내냈는데, 이슈 #266이
        # "엔트리 부재는 사망 신호가 아니다"로 바꾼 뒤로는 그 배치가 드레인
        # 블록과 무관하게(entry-absence 자체가 이미 pid 체크를 건너뛰므로)
        # 같은 결과를 내 더 이상 이 블록을 판별하지 못했다 — 살아있는
        # 로스터 엔트리 + 죽은 wrapper_pid(`test_follow_detects_dead_session_and_returns_crash_rc`
        # 와 같은 구성, test_spawn.py:3719-3747) 로 다시 배치해 판별력을
        # 복원한다: 드레인 블록이 없으면 첫 반복에서 곧장 WATCH_CRASH_RC 로
        # 리턴하고(session-end 잔여를 못 보고 죽은 pid 부터 본다), 있으면
        # 이 테스트가 기대하는 대로 session-end 를 먼저 소진하고 rc=0 이다.
        from unittest import mock
        dead = subprocess.Popen(["true"])
        dead.wait()
        spawn.roster_register("issue-180/implementation", {
            "pid": 999999, "wrapper_pid": dead.pid, "role": "implementation",
            "issue": 180, "ts": int(time.time()), "work": str(self.work),
            "log": str(self.log)})
        spawn._append_event(self.events, "progress", {"kind": "tool_use", "detail": "x"})
        spawn._append_event(self.events, "session-end", "progressed")
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path, **kwargs):
            calls.append(1)
            seen = spawn._read_offset(offset_path)
            lines = events_path.read_text(encoding="utf-8").splitlines()
            if seen < len(lines):
                spawn._write_offset(offset_path, seen + 1)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(180, "implementation", 5.0, follow=True)
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 2, calls)

    def test_follow_tolerates_post_processing_tail_before_session_end(self):
        # 헌트로 확인된 결함: `_spawn_one()`의 claude 서브프로세스
        # (roster `pid`)는 proc.wait() 리턴과 함께 정상 종료에서도 먼저
        # 죽는다 — push/게이트·소유권 리포트/classify/ledger_write 를
        # 거쳐야 session-end 가 남는다. 이 후처리 구간 동안은 `pid`가
        # 이미 죽어 있어도(여기서는 아예 안 심는다) `wrapper_pid`(호출자
        # 자신)가 살아있는 한 크래시로 오판하면 안 된다 — session-end 가
        # 나중에 나타나면 정상 리턴.
        from unittest import mock
        spawn.roster_register("issue-180/implementation", {
            "pid": 999999, "wrapper_pid": os.getpid(), "role": "implementation",
            "issue": 180, "ts": int(time.time()), "work": str(self.work),
            "log": str(self.log)})
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path, **kwargs):
            calls.append(1)
            if len(calls) < 3:
                return 0  # 후처리 구간 흉내: session-end 가 아직 없다
            spawn._append_event(events_path, "session-end", "progressed")
            spawn._write_offset(offset_path, spawn._read_offset(offset_path) + 1)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(180, "implementation", 5.0, follow=True)
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 3, calls)

    def test_self_heal_survives_stall_and_reaches_session_end(self):
        # 이슈 #927 Acceptance: (1) 로그 정지로 stall 유발 (2) 워처(루프)
        # 생존 확인 (3) 세션 종료 후 session-end 수신. `_await_bounded` 를
        # 매 호출 stall_limit_s 를 넘기도록 실제로 잠깐 sleep 시켜 진짜
        # 경과시간으로 stall 을 유발하고, self_heal=True 라면 그 stall 에서
        # 리턴하지 않고 재무장(continue)해 이후 실제로 발화되는 session-end
        # 까지 붙어 있어야 한다.
        from unittest import mock
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path, **kwargs):
            calls.append(1)
            time.sleep(0.05)  # stall_limit_s(아래 0.03s)를 매 호출 넘긴다
            if len(calls) < 3:
                return 0  # offset 진행 없음 — stall 유지
            spawn._append_event(events_path, "session-end", "progressed")
            spawn._write_offset(offset_path, spawn._read_offset(offset_path) + 1)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(180, "implementation", 0.0005, follow=True,
                               self_heal=True)
        self.assertEqual(rc, 0)
        # self-heal 이 없었다면 첫 stall 초과에서 곧장 리턴해 calls==1 이다 —
        # 3번째 호출까지 살아서 session-end 를 받았다는 것이 워처 생존의 증거.
        self.assertEqual(len(calls), 3, calls)

    def test_follow_without_self_heal_returns_on_stall_instead_of_looping(self):
        # 위 테스트의 대조군: self_heal=False(대화형 기본값)는 여전히 첫
        # stall 초과에서 곧장 리턴한다 — 회귀 가드가 self-heal 분기만 새로
        # 통과시키고 기존 대화형 경로를 바꾸지 않았음을 확인한다.
        from unittest import mock
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path, **kwargs):
            calls.append(1)
            time.sleep(0.05)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(180, "implementation", 0.0005, follow=True,
                               self_heal=False)
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 1, calls)

    def test_self_heal_crash_path_still_terminal_and_appends_ended_event(self):
        # crash(pid 확정 소실)는 self-heal 모드에서도 여전히 종료 사유다 —
        # 다만 session-end 없이 끝났다는 사실을 events.jsonl 에 durable
        # event 로 남겨 오케스트레이터가 알 수 있게 한다 (이슈 #927 구조적
        # 수정 방향 2번째 항목, #908 무성사멸 접점).
        from unittest import mock
        dead = subprocess.Popen(["true"])
        dead.wait()
        spawn.roster_register("issue-180/implementation", {
            "pid": 999999, "wrapper_pid": dead.pid, "role": "implementation",
            "issue": 180, "ts": int(time.time()), "work": str(self.work),
            "log": str(self.log)})

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path, **kwargs):
            return 0  # 매번 stall 흉내 — offset 진행 없음

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(180, "implementation", 5.0, follow=True,
                               self_heal=True)
        self.assertEqual(rc, spawn.WATCH_CRASH_RC)
        lines = self.events.read_text(encoding="utf-8").splitlines()
        types = [json.loads(line).get("type") for line in lines]
        self.assertIn("watcher-ended-without-session-end", types)

    def test_self_heal_survives_malformed_events_line_instead_of_crashing(self):
        # before-landing warrant hunt (docs/issue-927/reports/implementation/
        # 2026-08-12-hunt-implementation.md): a single corrupt line in
        # events.jsonl at the offset the follow loop is about to consume
        # used to raise an uncaught JSONDecodeError, killing the self-heal
        # watcher outright with no crash event and no re-arm. Guard it the
        # same way `_prior_event_details()` already does elsewhere in this
        # file (try/except ValueError around json.loads).
        from unittest import mock
        with self.events.open("a", encoding="utf-8") as fh:
            fh.write("{not valid json\n")
        spawn._write_offset(self.offset, 0)
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path, **kwargs):
            calls.append(1)
            if len(calls) < 2:
                spawn._write_offset(offset_path, 1)  # 소비할 오프셋을 malformed 줄로 이동
                return 0
            spawn._append_event(events_path, "session-end", "progressed")
            spawn._write_offset(offset_path, spawn._read_offset(offset_path) + 1)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(180, "implementation", 5.0, follow=True,
                               self_heal=True)
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 2, calls)

    def test_non_follow_mode_calls_await_bounded_exactly_once(self):
        from unittest import mock
        spawn._append_event(self.events, "progress", {"kind": "tool_use", "detail": "x"})
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path, **kwargs):
            calls.append(1)
            spawn._write_offset(offset_path, spawn._read_offset(offset_path) + 1)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(180, "implementation", 5.0, follow=False)
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 1, calls)  # 기존 단일-이벤트 모드는 그대로

    def test_main_wires_follow_flag_through_to_watch(self):
        from unittest import mock
        old_argv = sys.argv
        sys.argv = ["spawn.py", "watch", "--issue", "180", "--follow"]
        captured = {}

        def fake_watch(issue, role, stall_timeout_min, follow=False, repo=None,
                       max_wait_min=None, self_heal=False):
            captured["follow"] = follow
            return 0

        try:
            with mock.patch.object(spawn, "_watch", fake_watch):
                rc = spawn.main()
        finally:
            sys.argv = old_argv
        self.assertEqual(rc, 0)
        self.assertTrue(captured["follow"])

    def test_main_defaults_follow_to_false(self):
        from unittest import mock
        old_argv = sys.argv
        sys.argv = ["spawn.py", "watch", "--issue", "180"]
        captured = {}

        def fake_watch(issue, role, stall_timeout_min, follow=False, repo=None,
                       max_wait_min=None, self_heal=False):
            captured["follow"] = follow
            return 0

        try:
            with mock.patch.object(spawn, "_watch", fake_watch):
                rc = spawn.main()
        finally:
            sys.argv = old_argv
        self.assertEqual(rc, 0)
        self.assertFalse(captured["follow"])

    def test_main_wires_self_heal_flag_through_to_watch(self):
        from unittest import mock
        old_argv = sys.argv
        sys.argv = ["spawn.py", "watch", "--issue", "180", "--follow", "--self-heal"]
        captured = {}

        def fake_watch(issue, role, stall_timeout_min, follow=False, repo=None,
                       max_wait_min=None, self_heal=False):
            captured["self_heal"] = self_heal
            return 0

        try:
            with mock.patch.object(spawn, "_watch", fake_watch):
                rc = spawn.main()
        finally:
            sys.argv = old_argv
        self.assertEqual(rc, 0)
        self.assertTrue(captured["self_heal"])

    def test_main_defaults_self_heal_to_false(self):
        from unittest import mock
        old_argv = sys.argv
        sys.argv = ["spawn.py", "watch", "--issue", "180", "--follow"]
        captured = {}

        def fake_watch(issue, role, stall_timeout_min, follow=False, repo=None,
                       max_wait_min=None, self_heal=False):
            captured["self_heal"] = self_heal
            return 0

        try:
            with mock.patch.object(spawn, "_watch", fake_watch):
                rc = spawn.main()
        finally:
            sys.argv = old_argv
        self.assertEqual(rc, 0)
        self.assertFalse(captured["self_heal"])

    def test_follow_tolerates_roster_entry_fully_absent_before_session_end(self):
        # 이슈 #266: `_spawn_one()`의 후처리 꼬리 동안 `roster_remove(roster_key)`
        # (spawn.py:2995)가 `session-end` 기록(spawn.py:3097)보다 먼저 실행돼,
        # 그 구간 전체에서 명부 엔트리가 아예 없다(setUp 이 심어 둔 엔트리를
        # 여기서 지워 그 상태를 실제로 구성한다 — 이전 회귀
        # test_follow_tolerates_post_processing_tail_before_session_end 는
        # wrapper_pid 가 살아있는 엔트리를 다시 심어서 이 창을 구성하지 않았다).
        # 엔트리 부재는 사망이 아니라 불명으로 다뤄 stall 안전망을 거쳐 계속
        # 대기해야 한다 — 수정 전에는 이 테스트가 WATCH_CRASH_RC 로 fail 한다.
        from unittest import mock
        spawn.roster_remove("issue-180/implementation")
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path, **kwargs):
            calls.append(1)
            if len(calls) < 3:
                return 0  # 엔트리 부재 꼬리 구간 흉내: session-end 가 아직 없다
            spawn._append_event(events_path, "session-end", "progressed")
            spawn._write_offset(offset_path, spawn._read_offset(offset_path) + 1)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(180, "implementation", 5.0, follow=True)
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 3, calls)

    def test_watcher_dead_stale_pid_cleared_by_live_follow_registration(self):
        # 이슈 #1043: 자동 무장한 워처 pid 가 죽어 명부에 남아 있어도, 이
        # follow 호출이 진입 시점에 자기 자신을 워처로 등록해 stale pid 를
        # 덮어써야 한다 — 그 뒤 watchdog_check_one() 은 watcher-dead 도
        # watcher-missing 도 신고하지 않아야 한다.
        from unittest import mock
        spawn._workspace_index_put(180, "implementation", str(self.work), str(self.log),
                                    watcher_pid=999999999)  # 존재 안 할 stale pid
        spawn._append_event(self.events, "session-end", "progressed")

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path, **kwargs):
            seen = spawn._read_offset(offset_path)
            lines = events_path.read_text(encoding="utf-8").splitlines()
            if seen < len(lines):
                spawn._write_offset(offset_path, seen + 1)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(180, "implementation", 5.0, follow=True)
        self.assertEqual(rc, 0)
        key = f"{spawn._repo_identity(str(self.work))}/issue-180/implementation"
        idx_entry = spawn._workspace_index_load()[key]
        self.assertEqual(idx_entry["watcher_pid"], os.getpid())
        wd_entry = {"log": str(self.log), "work": str(self.work), "ts": int(time.time()),
                    "before_head": None, "pid": None}
        out = spawn.watchdog_check_one("issue-180/implementation", wd_entry, state={})
        self.assertFalse(any("watcher-dead" in a for a in out))
        self.assertFalse(any("watcher-missing" in a for a in out))

    def test_watcher_dead_or_missing_still_fires_with_no_watcher_registered(self):
        # 컨트롤 케이스: 이 수정이 너무 관대해지지 않았는지 지킨다 — 애초에
        # 아무 워처도 등록되지 않은 세션(setUp 이 watcher_pid 없이 심은
        # 엔트리 그대로)은 여전히 watcher-missing/watcher-dead 로 잡혀야 한다.
        wd_entry = {"log": str(self.log), "work": str(self.work), "ts": int(time.time()),
                    "before_head": None, "pid": None}
        out = spawn.watchdog_check_one("issue-180/implementation", wd_entry, state={})
        self.assertTrue(any("watcher-missing" in a or "watcher-dead" in a for a in out))

class WatchFollowSessionScoping(unittest.TestCase):
    """이슈 #557: --follow 커서는 무장 시점에 살아있는 세션(pid+ts)에만
    스코프된다 — 같은 워크스페이스 로그에 남은 이전 세션의 이벤트를
    재생하면 안 되고, 배너는 호출당 한 번만 찍고, 찍히는 모든 이벤트
    줄은 원본 세션의 pid/ts 를 달고 나와야 한다."""

    def setUp(self):
        self.td = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.td, ignore_errors=True)
        self.work = Path(self.td) / "wk"
        self.work.mkdir()
        self.events = spawn._events_path(self.work)
        self.offset = spawn._offset_path(self.work)
        self.log = Path(str(self.work) + ".session.log")
        self.log.write_text("")
        old_idx = spawn.WORKSPACE_INDEX
        spawn.WORKSPACE_INDEX = Path(self.td) / "workspaces.json"
        self.addCleanup(setattr, spawn, "WORKSPACE_INDEX", old_idx)
        spawn._workspace_index_put(557, "implementation", str(self.work), str(self.log))
        old_roster = spawn.ROSTER
        spawn.ROSTER = Path(self.td) / "active.json"
        self.addCleanup(setattr, spawn, "ROSTER", old_roster)

    def _register_live(self, pid):
        spawn.roster_register("issue-557/implementation", {
            "pid": pid, "wrapper_pid": os.getpid(), "role": "implementation",
            "issue": 557, "ts": int(time.time()), "work": str(self.work),
            "log": str(self.log)})

    def test_no_replay_of_earlier_session_events(self):
        # pid A(옛 세션)의 이벤트 다음에 pid B(지금 살아있는 세션)의
        # session-start 와 이벤트를 남긴다 — 무장 시점에 B 가 살아있으니
        # A 몫 이벤트는 하나도 재생돼선 안 된다.
        spawn._append_event(self.events, "session-start", {"pid": 111, "ts": 1.0})
        spawn._append_event(self.events, "progress", {"kind": "old-session-marker"})
        spawn._append_event(self.events, "session-end", "old-progressed")
        spawn._append_event(self.events, "session-start", {"pid": 222, "ts": 2.0})
        spawn._append_event(self.events, "progress", {"kind": "new-session-marker"})
        spawn._append_event(self.events, "session-end", "new-progressed")
        self._register_live(222)

        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = spawn._watch(557, "implementation", 5.0, follow=True)
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertNotIn("old-session-marker", out)
        self.assertNotIn("old-progressed", out)
        self.assertIn("new-session-marker", out)
        self.assertIn("new-progressed", out)

    def test_banner_prints_at_most_once_per_invocation(self):
        spawn._append_event(self.events, "session-start", {"pid": 333, "ts": 3.0})
        spawn._append_event(self.events, "progress", {"kind": "a"})
        spawn._append_event(self.events, "progress", {"kind": "b"})
        spawn._append_event(self.events, "progress", {"kind": "c"})
        spawn._append_event(self.events, "session-end", "progressed")
        self._register_live(333)

        import io
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with redirect_stderr(buf):
            rc = spawn._watch(557, "implementation", 5.0, follow=True)
        self.assertEqual(rc, 0)
        banner = "스폰은 리턴했지만"
        self.assertEqual(buf.getvalue().count(banner), 1)

    def test_events_tagged_with_session_pid_ts(self):
        spawn._append_event(self.events, "session-start", {"pid": 444, "ts": 4.5})
        spawn._append_event(self.events, "progress", {"kind": "tagged"})
        spawn._append_event(self.events, "session-end", "progressed")
        self._register_live(444)

        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = spawn._watch(557, "implementation", 5.0, follow=True)
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        lines = [l for l in out.splitlines() if l.strip()]
        self.assertTrue(lines)
        for line in lines:
            self.assertIn("pid=444", line)
            self.assertIn("ts=4.5", line)

class WatchRegistrationRace(unittest.TestCase):
    """이슈 #484: 스폰이 막 리턴한 직후 `watch` 가 명부 엔트리를 아직 못
    찾는 레이스 — #451(끝내 안 나타남)과 달리, 엔트리가 stall_timeout_min
    안에 나타나면 watch 는 기록-없음으로 죽지 않고 붙어야 한다."""

    def setUp(self):
        self.td = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.td, ignore_errors=True)
        self.work = Path(self.td) / "wk"
        self.work.mkdir()
        self.events = spawn._events_path(self.work)
        self.offset = spawn._offset_path(self.work)
        self.log = Path(str(self.work) + ".session.log")
        self.log.write_text("")
        old_idx = spawn.WORKSPACE_INDEX
        spawn.WORKSPACE_INDEX = Path(self.td) / "workspaces.json"
        self.addCleanup(setattr, spawn, "WORKSPACE_INDEX", old_idx)

    def test_entry_appearing_within_grace_window_attaches_and_streams(self):
        from unittest import mock
        spawn._append_event(self.events, "session-end", "progressed")
        entry = {"work": str(self.work), "log": str(self.log)}
        calls = {"n": 0}

        def fake_load():
            calls["n"] += 1
            # 처음 두 번은 아직 명부 쓰기가 안 반영된 것처럼 빈 명부 —
            # 세 번째 폴에서 등록이 나타난다.
            if calls["n"] >= 3:
                return {"wk/issue-484/implementation": entry}
            return {}

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path, **kwargs):
            print(f"[watch] session-end: progressed")
            return 0

        with mock.patch.object(spawn, "_workspace_index_load", fake_load), \
             mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(484, "implementation", 5.0, follow=False)
        self.assertEqual(rc, 0)
        self.assertGreaterEqual(calls["n"], 3, calls)

    def test_entry_never_appearing_times_out_and_reports_absence(self):
        from unittest import mock
        with mock.patch.object(spawn, "_workspace_index_load", lambda: {}):
            rc = spawn._watch(484, "implementation", 0.001, follow=False)
        self.assertEqual(rc, 1)

class WatchMultiRoleAmbiguity(unittest.TestCase):
    """이슈 #554: 이슈에 역할이 여럿 기록돼 있을 때 `watch` 가 죽은
    재시도 구간으로 빠지지 않게 한다 — (1) 살아있는 세션이 정확히
    하나면 자동 선택, (2) 여전히 애매하면 그대로 실행 가능한 `--role`
    명령을 에러에 찍는다, (3) `watch <역할> --issue N` 위치 인자 문법을
    `kill` 과 동일하게 받는다."""

    def setUp(self):
        self.td = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.td, ignore_errors=True)
        old_idx = spawn.WORKSPACE_INDEX
        spawn.WORKSPACE_INDEX = Path(self.td) / "workspaces.json"
        self.addCleanup(setattr, spawn, "WORKSPACE_INDEX", old_idx)
        old_roster = spawn.ROSTER
        spawn.ROSTER = Path(self.td) / "active.json"
        self.addCleanup(setattr, spawn, "ROSTER", old_roster)
        self.work_a = Path(self.td) / "wk-a"
        self.work_b = Path(self.td) / "wk-b"
        self.work_a.mkdir()
        self.work_b.mkdir()
        spawn._workspace_index_put(1, "technical-feasibility", str(self.work_a), "log-a")
        spawn._workspace_index_put(1, "implementation", str(self.work_b), "log-b")

    def _register(self, role: str, pid: int, work: Path):
        spawn.roster_register(f"issue-1/{role}", {
            "pid": pid, "role": role, "issue": 1, "ts": int(time.time()),
            "work": str(work), "log": str(work) + ".session.log"})

    def _dead_pid(self) -> int:
        dead = subprocess.Popen(["true"])
        dead.wait()
        return dead.pid

    def test_auto_selects_the_one_role_with_a_live_session(self):
        self._register("technical-feasibility", self._dead_pid(), self.work_a)
        self._register("implementation", os.getpid(), self.work_b)
        idx = spawn._workspace_index_load()
        key, entry = spawn._lookup_roster_entry(idx, 1, None)
        self.assertEqual(key, next(iter(
            k for k in idx if k.endswith("/implementation"))))
        self.assertEqual(entry["log"], "log-b")

    def test_ambiguous_error_names_runnable_role_command_when_zero_live(self):
        self._register("technical-feasibility", self._dead_pid(), self.work_a)
        self._register("implementation", self._dead_pid(), self.work_b)
        idx = spawn._workspace_index_load()
        with self.assertRaises(SystemExit) as cm:
            spawn._lookup_roster_entry(idx, 1, None)
        msg = str(cm.exception)
        self.assertIn("--role", msg)
        self.assertIn("spawn.py watch --issue 1 --role technical-feasibility", msg)
        self.assertIn("spawn.py watch --issue 1 --role implementation", msg)

    def test_ambiguous_error_names_runnable_role_command_when_two_live(self):
        self._register("technical-feasibility", os.getpid(), self.work_a)
        self._register("implementation", os.getpid(), self.work_b)
        idx = spawn._workspace_index_load()
        with self.assertRaises(SystemExit) as cm:
            spawn._lookup_roster_entry(idx, 1, None)
        msg = str(cm.exception)
        self.assertIn("--role", msg)
        self.assertIn("technical-feasibility", msg)
        self.assertIn("implementation", msg)

    def test_positional_role_resolves_identically_to_role_flag(self):
        from unittest import mock
        seen = {}

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path, **kwargs):
            seen["log_path"] = log_path
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            old_argv = sys.argv
            sys.argv = ["spawn.py", "watch", "implementation", "--issue", "1",
                        "-C", str(self.work_b)]
            try:
                rc = spawn.main()
            finally:
                sys.argv = old_argv
        self.assertEqual(rc, 0)
        self.assertEqual(seen["log_path"], Path("log-b"))

class WatchRosterWorkspaceIndexRace(unittest.TestCase):
    """이슈 #1585: `watch` 는 워크스페이스 인덱스를, `ps` 는 ROSTER 를
    본다 — 스폰 직후 워크스페이스 인덱스 쓰기가 아직 반영되지 않은 창에서
    ROSTER 에는 이미 살아있는 세션이 등록돼 있으면 `watch` 와 `ps` 가
    존재 여부에서 갈렸다(실측: 이슈-1582 phase-2 드라이브, 5초 지연
    재시도로도 재현). 워크스페이스 인덱스에 엔트리가 아예 없어도 ROSTER
    에 등록된 살아있는 세션이 있으면 `watch` 가 '기록 없음'이 아니라
    그 세션에 붙어야 한다."""

    def setUp(self):
        self.td = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.td, ignore_errors=True)
        old_idx = spawn.WORKSPACE_INDEX
        spawn.WORKSPACE_INDEX = Path(self.td) / "workspaces.json"
        self.addCleanup(setattr, spawn, "WORKSPACE_INDEX", old_idx)
        old_roster = spawn.ROSTER
        spawn.ROSTER = Path(self.td) / "active.json"
        self.addCleanup(setattr, spawn, "ROSTER", old_roster)
        self.work = Path(self.td) / "wk"
        self.work.mkdir()
        self.log = Path(str(self.work) + ".session.log")
        self.log.write_text("")
        # 워크스페이스 인덱스는 의도적으로 비워 둔다 — 이게 관측된 레이스
        # 창이다: ROSTER 는 이미 등록돼 살아있는데 워크스페이스 인덱스는
        # 아직 안 쓰였다.
        spawn.roster_register("issue-1585/implementation", {
            "pid": os.getpid(), "wrapper_pid": os.getpid(),
            "role": "implementation", "issue": 1585, "ts": int(time.time()),
            "work": str(self.work), "log": str(self.log)})

    def test_lookup_falls_back_to_live_roster_entry_when_workspace_index_empty(self):
        idx = spawn._workspace_index_load()
        self.assertEqual(idx, {})
        key, entry = spawn._lookup_roster_entry(idx, 1585, "implementation")
        self.assertIsNotNone(entry, "ROSTER 에 살아있는 세션이 있는데도 조회가 "
                                     "None 을 돌려줬다 — ps 와 watch 가 다시 갈렸다")
        self.assertEqual(entry["work"], str(self.work))
        self.assertEqual(entry["log"], str(self.log))

    def test_watch_attaches_instead_of_reporting_no_record(self):
        from unittest import mock
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path, **kwargs):
            calls.append(log_path)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(1585, "implementation", 5.0)
        self.assertEqual(rc, 0)
        self.assertEqual(calls, [self.log])

    def test_watch_role_auto_select_also_falls_back_to_roster(self):
        from unittest import mock
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path, **kwargs):
            calls.append(log_path)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(1585, None, 5.0)
        self.assertEqual(rc, 0)
        self.assertEqual(calls, [self.log])

class WatchAll(unittest.TestCase):
    """이슈 #488: `watch --all` — 워크스페이스 인덱스 전체를 다중화한다.
    루프 자체는 무한이라 테스트에서 직접 돌리지 않고, 그 루프 몸통이
    도는 매 반복의 로직(한 키의 새 이벤트를 소비해 offset 을 그 키만큼만
    미는 것)을 한 이터레이션 상당으로 재현해 검증한다.
    """

    def setUp(self):
        self.td = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.td, ignore_errors=True)
        old_idx = spawn.WORKSPACE_INDEX
        spawn.WORKSPACE_INDEX = Path(self.td) / "workspaces.json"
        self.addCleanup(setattr, spawn, "WORKSPACE_INDEX", old_idx)
        self.work_a = Path(self.td) / "a"
        self.work_a.mkdir()
        self.work_b = Path(self.td) / "b"
        self.work_b.mkdir()

    def _run_one_iteration(self, seen_end):
        idx = spawn._workspace_index_load()
        reported = []
        for key, entry in sorted(idx.items()):
            if key in seen_end:
                continue
            events_path = spawn._events_path(entry["work"])
            offset_path = spawn._offset_path(entry["work"])
            seen = spawn._read_offset(offset_path)
            if not events_path.exists():
                continue
            lines = events_path.read_text(encoding="utf-8").splitlines()
            while len(lines) > seen:
                ev = json.loads(lines[seen])
                seen += 1
                spawn._write_offset(offset_path, seen)
                reported.append((key, ev["type"]))
                if ev["type"] == "session-end":
                    seen_end.add(key)
                    break
        return reported

    def test_multiplexes_two_keys_independently(self):
        spawn._workspace_index_put(1, "implementation", str(self.work_a),
                                    str(self.work_a) + ".log")
        spawn._workspace_index_put(2, "implementation", str(self.work_b),
                                    str(self.work_b) + ".log")
        spawn._append_event(spawn._events_path(self.work_a), "progress", "x")
        spawn._append_event(spawn._events_path(self.work_b), "progress", "y")
        seen_end = set()
        reported = self._run_one_iteration(seen_end)
        keys = {k for k, _ in reported}
        self.assertEqual(keys, {"a/issue-1/implementation", "b/issue-2/implementation"})

    def test_key_registered_after_polling_started_is_picked_up(self):
        # 워처가 시작된 뒤에 등록된 스폰도 다음 이터레이션에서 잡힌다 —
        # 매 반복 인덱스를 다시 읽기 때문.
        seen_end = set()
        first = self._run_one_iteration(seen_end)
        self.assertEqual(first, [])
        spawn._workspace_index_put(3, "implementation", str(self.work_a),
                                    str(self.work_a) + ".log")
        spawn._append_event(spawn._events_path(self.work_a), "session-end", "done")
        second = self._run_one_iteration(seen_end)
        self.assertEqual(second, [("a/issue-3/implementation", "session-end")])
        self.assertIn("a/issue-3/implementation", seen_end)

    def test_offset_advances_only_for_consumed_key(self):
        spawn._workspace_index_put(1, "implementation", str(self.work_a),
                                    str(self.work_a) + ".log")
        spawn._workspace_index_put(2, "implementation", str(self.work_b),
                                    str(self.work_b) + ".log")
        spawn._append_event(spawn._events_path(self.work_a), "progress", "x")
        seen_end = set()
        self._run_one_iteration(seen_end)
        self.assertEqual(spawn._read_offset(spawn._offset_path(self.work_a)), 1)
        self.assertEqual(spawn._read_offset(spawn._offset_path(self.work_b)), 0)

    def test_all_flag_rejects_issue_combo_in_cli(self):
        with self.assertRaises(SystemExit):
            with mock.patch.object(sys, "argv",
                                    ["spawn.py", "watch", "--all", "--issue", "1"]):
                spawn.main()

    def test_until_idle_returns_once_all_watched_sessions_end(self):
        # 이슈 #559: 모든 세션이 session-end 를 남기면 --until-idle 은
        # 영원히 자며 다시 돌지 않고 리턴해야 한다.
        spawn._workspace_index_put(1, "implementation", str(self.work_a),
                                    str(self.work_a) + ".log")
        spawn._append_event(spawn._events_path(self.work_a), "session-end", "done")
        rc = spawn._watch_all(0.01, until_idle=True)
        self.assertEqual(rc, 0)

    def test_until_idle_does_not_exit_while_a_session_is_still_live(self):
        # 한 세션은 끝났고 다른 세션은 아직 살아있으면 idle 이 아니다 —
        # KeyboardInterrupt 로 직접 끊어서 무한 루프가 실제로 돌았음을 확인한다.
        spawn._workspace_index_put(1, "implementation", str(self.work_a),
                                    str(self.work_a) + ".log")
        spawn._workspace_index_put(2, "implementation", str(self.work_b),
                                    str(self.work_b) + ".log")
        spawn._append_event(spawn._events_path(self.work_a), "session-end", "done")
        spawn._append_event(spawn._events_path(self.work_b), "progress", "still going")

        call_count = {"n": 0}
        real_sleep = time.sleep

        def counting_sleep(s):
            call_count["n"] += 1
            if call_count["n"] >= 2:
                raise KeyboardInterrupt
            real_sleep(0)

        with mock.patch.object(time, "sleep", counting_sleep):
            rc = spawn._watch_all(0.01, until_idle=True)
        self.assertEqual(rc, 0)
        self.assertGreaterEqual(call_count["n"], 2)

    def test_until_idle_empty_index_returns_immediately(self):
        rc = spawn._watch_all(0.01, until_idle=True)
        self.assertEqual(rc, 0)

    def test_until_idle_flag_rejected_without_all(self):
        with self.assertRaises(SystemExit):
            with mock.patch.object(sys, "argv",
                                    ["spawn.py", "watch", "--until-idle",
                                     "--issue", "1"]):
                spawn.main()

class ReturnedPrGate(unittest.TestCase):
    """이슈 #680: 다른 issue-*/ PR 이 아직 처분(phase-1 승인 또는 phase-2
    머지/닫힘)되지 않았으면 `_spawn_one()` 이 스폰을 거절한다."""

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

    # -- _open_role_prs / _undispositioned_role_prs -----------------------

    def test_open_role_prs_filters_to_issue_dash_branches(self):
        prs = [
            {"number": 1, "headRefName": "issue-11/implementation",
             "body": "", "url": "https://example/1"},
            {"number": 2, "headRefName": "some-other-branch",
             "body": "", "url": "https://example/2"},
        ]

        def fake_run(cmd, **k):
            if cmd[:2] == ["gh", "repo"]:
                return subprocess.CompletedProcess(cmd, 0, "o/r\n", "")
            if cmd[:3] == ["gh", "pr", "list"]:
                return subprocess.CompletedProcess(cmd, 0, json.dumps(prs), "")
            raise AssertionError(cmd)

        with mock.patch.object(spawn.subprocess, "run", fake_run):
            out, ok = spawn._open_role_prs(Path("."))
        self.assertTrue(ok)
        self.assertEqual([p["number"] for p in out], [1])
        self.assertEqual(out[0]["issue"], 11)

    def test_open_role_prs_fails_open_marker_on_gh_error(self):
        def fake_run(cmd, **k):
            if cmd[:2] == ["gh", "repo"]:
                return subprocess.CompletedProcess(cmd, 0, "o/r\n", "")
            return subprocess.CompletedProcess(cmd, 1, "", "boom")

        with mock.patch.object(spawn.subprocess, "run", fake_run):
            out, ok = spawn._open_role_prs(Path("."))
        self.assertFalse(ok)
        self.assertEqual(out, [])

    def test_undispositioned_excludes_same_issue_and_classifies_phase(self):
        prs = [
            {"number": 1, "headRefName": "issue-11/implementation",
             "body": "", "url": "https://example/1"},
            {"number": 2, "headRefName": "issue-22/qa",
             "body": "", "url": "https://example/2"},
        ]

        def fake_run(cmd, **k):
            if cmd[:2] == ["gh", "repo"]:
                return subprocess.CompletedProcess(cmd, 0, "o/r\n", "")
            if cmd[:3] == ["gh", "pr", "list"]:
                return subprocess.CompletedProcess(cmd, 0, json.dumps(prs), "")
            raise AssertionError(cmd)

        sys.path.insert(0, str((Path(spawn.__file__).parent / "gates").resolve()))
        import ci as _ci

        def fake_approved(repo, issue):
            return {"implementation"} if issue == 22 else set()

        with mock.patch.object(spawn.subprocess, "run", fake_run), \
             mock.patch.object(_ci, "_approved_roles_on_issue", fake_approved):
            blockers, ok = spawn._undispositioned_role_prs(Path("."), exclude_issue=11)
        self.assertTrue(ok)
        self.assertEqual(len(blockers), 1)
        self.assertEqual(blockers[0]["issue"], 22)
        self.assertEqual(blockers[0]["phase"], "phase2")

    def test_undispositioned_empty_when_all_excluded_or_dispositioned(self):
        with mock.patch.object(spawn, "_open_role_prs", lambda root: ([], True)):
            blockers, ok = spawn._undispositioned_role_prs(Path("."), exclude_issue=11)
        self.assertTrue(ok)
        self.assertEqual(blockers, [])

    # -- _spawn_one wiring ---------------------------------------------

    @pytest.mark.slow
    def test_spawn_one_surfaces_but_succeeds_on_undispositioned_pr(self):
        """이슈 #1239: 처분 안 된 PR 이 있어도 스폰은 거절되지 않는다 —
        issue/phase/age/URL 을 찍고 성공한다 (northpole req#1)."""
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            old_roster, old_idx = spawn.ROSTER, spawn.WORKSPACE_INDEX
            spawn.ROSTER = Path(td) / "active.json"
            spawn.WORKSPACE_INDEX = Path(td) / "workspaces.json"
            blockers = [{"issue": 22, "phase": "phase1", "url": "https://example/2",
                         "number": 2, "headRefName": "issue-22/qa", "body": "",
                         "age_hours": 3.25}]
            captured_stdout = io.StringIO()
            ledger_calls = []
            try:
                with mock.patch.object(spawn, "_undispositioned_role_prs",
                                       lambda root, exclude_issue=None: (blockers, True)), \
                     mock.patch.object(spawn, "ledger_write",
                                       lambda entry: ledger_calls.append(entry)), \
                     contextlib.redirect_stdout(captured_stdout), \
                     contextlib.ExitStack() as stack:
                    for cm in self._full_mock_scaffold(work):
                        stack.enter_context(cm)
                    rc = spawn._spawn_one(str(work), "implementation", "task\n",
                                          unattended=True, issue=11, bounded=True,
                                          no_wait=True)
            finally:
                spawn.ROSTER, spawn.WORKSPACE_INDEX = old_roster, old_idx
            self.assertEqual(rc, 0)
            printed = captured_stdout.getvalue()
            self.assertIn("issue #22", printed)
            self.assertIn("phase1", printed)
            self.assertIn("3.2h", printed)
            self.assertIn("https://example/2", printed)
            events = [e["event"] for e in ledger_calls]
            self.assertIn("returned_pr_surfaced", events)
            surfaced = next(e for e in ledger_calls if e["event"] == "returned_pr_surfaced")
            self.assertEqual(surfaced["issues"], [22])
            self.assertNotIn("returned_pr_gate_refused", events)

    def _full_mock_scaffold(self, work):
        class FakeWatcherProc:
            pid = 424242

        real_popen = subprocess.Popen

        def selective_popen(cmd, *a, **k):
            if isinstance(cmd, list) and "watch" in cmd:
                return FakeWatcherProc()
            return real_popen(cmd, *a, **k)

        return [
            mock.patch.dict(os.environ, {"MUSTER_WORK_DIR": str(work.parent / "sweep-base")}),
            mock.patch.object(spawn, "issue_workspace",
                               lambda cwd, issue, role: str(work)),
            mock.patch.object(spawn, "checkout_issue_branch",
                               lambda cwd, issue, role: "b"),
            mock.patch.object(spawn, "resolve_role_source",
                              lambda role, repo_root: {"source": "skill-repo",
                                  "skill_dirs": [], "skills": [], "skill_sha": None}),
            mock.patch.object(spawn, "core_plugin_dirs", lambda: []),
            mock.patch.object(spawn, "core_version", lambda: "v0"),
            mock.patch.object(spawn, "spawn_cmd", lambda *a, **k: (["cat"], {})),
            mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None),
            mock.patch.object(spawn, "_rewrite_spawn_claim_pid", lambda w: None),
            mock.patch.object(spawn.subprocess, "Popen", selective_popen),
            mock.patch.object(spawn, "_await_bounded", lambda *a, **k: 0),
            mock.patch.object(os, "fork", return_value=4321),
        ]

    @pytest.mark.slow
    def test_spawn_one_passes_silently_when_no_blockers(self):
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            old_roster, old_idx = spawn.ROSTER, spawn.WORKSPACE_INDEX
            spawn.ROSTER = Path(td) / "active.json"
            spawn.WORKSPACE_INDEX = Path(td) / "workspaces.json"
            ledger_calls = []
            try:
                with mock.patch.object(spawn, "_undispositioned_role_prs",
                                       lambda root, exclude_issue=None: ([], True)), \
                     mock.patch.object(spawn, "ledger_write",
                                       lambda entry: ledger_calls.append(entry)), \
                     contextlib.ExitStack() as stack:
                    for cm in self._full_mock_scaffold(work):
                        stack.enter_context(cm)
                    rc = spawn._spawn_one(str(work), "implementation", "task\n",
                                          unattended=True, issue=11, bounded=True,
                                          no_wait=True)
            finally:
                spawn.ROSTER, spawn.WORKSPACE_INDEX = old_roster, old_idx
            self.assertEqual(rc, 0)
            events = [e.get("event") for e in ledger_calls]
            self.assertNotIn("returned_pr_gate_refused", events)
            self.assertNotIn("returned_pr_surfaced", events)

    @pytest.mark.slow
    def test_spawn_one_despite_returned_is_deprecated_noop(self):
        """이슈 #1239: `--despite-returned` 는 이제 아무 것도 바꾸지 않는다
        — surfacing + 성공은 플래그 유무와 무관하고, deprecation 안내만
        추가로 찍힌다."""
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            old_roster, old_idx = spawn.ROSTER, spawn.WORKSPACE_INDEX
            spawn.ROSTER = Path(td) / "active.json"
            spawn.WORKSPACE_INDEX = Path(td) / "workspaces.json"
            blockers = [{"issue": 22, "phase": "phase1", "url": "https://example/2",
                         "number": 2, "headRefName": "issue-22/qa", "body": "",
                         "age_hours": 1.0}]
            ledger_calls = []
            captured_stderr = io.StringIO()
            try:
                with mock.patch.object(spawn, "_undispositioned_role_prs",
                                       lambda root, exclude_issue=None: (blockers, True)), \
                     mock.patch.object(spawn, "ledger_write",
                                       lambda entry: ledger_calls.append(entry)), \
                     contextlib.redirect_stderr(captured_stderr), \
                     contextlib.ExitStack() as stack:
                    for cm in self._full_mock_scaffold(work):
                        stack.enter_context(cm)
                    rc = spawn._spawn_one(str(work), "implementation", "task\n",
                                          unattended=True, issue=11, bounded=True,
                                          no_wait=True, despite_returned=True)
            finally:
                spawn.ROSTER, spawn.WORKSPACE_INDEX = old_roster, old_idx
            self.assertEqual(rc, 0)
            events = [e["event"] for e in ledger_calls]
            self.assertIn("returned_pr_surfaced", events)
            self.assertNotIn("returned_pr_gate_bypassed", events)
            self.assertIn("deprecated", captured_stderr.getvalue())

    @pytest.mark.slow
    def test_spawn_one_fails_open_on_gh_failure_with_warning(self):
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            old_roster, old_idx = spawn.ROSTER, spawn.WORKSPACE_INDEX
            spawn.ROSTER = Path(td) / "active.json"
            spawn.WORKSPACE_INDEX = Path(td) / "workspaces.json"
            captured_stderr = io.StringIO()
            ledger_calls = []
            try:
                with mock.patch.object(spawn, "_undispositioned_role_prs",
                                       lambda root, exclude_issue=None: ([], False)), \
                     mock.patch.object(spawn, "ledger_write",
                                       lambda entry: ledger_calls.append(entry)), \
                     contextlib.redirect_stderr(captured_stderr), \
                     contextlib.ExitStack() as stack:
                    for cm in self._full_mock_scaffold(work):
                        stack.enter_context(cm)
                    rc = spawn._spawn_one(str(work), "implementation", "task\n",
                                          unattended=True, issue=11, bounded=True,
                                          no_wait=True)
            finally:
                spawn.ROSTER, spawn.WORKSPACE_INDEX = old_roster, old_idx
            self.assertEqual(rc, 0)
            self.assertIn("gh 조회 실패", captured_stderr.getvalue())
            events = [e["event"] for e in ledger_calls]
            self.assertIn("returned_pr_gate_fail_open", events)

class RosterOwnershipScoping(unittest.TestCase):
    """이슈 #1013 acceptance: 두 세션이 동시에 로스터를 채운 상태에서
    기본 스코프는 자기 세션 엔트리(+ session_id 미기재 empty-state)만
    보고, `--all` 은 전체를, 다른 세션 소유 죽은 엔트리는 [orphaned] 로
    계속 표면화한다 — 단일 세션/미설정 머신은 오늘과 동일하게 동작한다."""

    def _entry(self, log, work=None, pid=None, issue=1, role="implementation",
               session_id=None):
        return {"log": str(log), "work": work, "ts": int(time.time()),
                "before_head": None, "pid": pid, "issue": issue, "role": role,
                "session_id": session_id}

    # -- _roster_own -----------------------------------------------------

    def test_roster_own_default_scope_keeps_own_and_none_sid(self):
        d = {"a": {"session_id": "sess-mine"}, "b": {"session_id": None},
             "c": {"session_id": "sess-other"}}
        with mock.patch.dict(os.environ, {spawn.ORCHESTRATOR_SESSION_ID_ENV: "sess-mine"}):
            out = spawn._roster_own(d, all_scope=False)
        self.assertEqual(set(out), {"a", "b"})

    def test_roster_own_all_scope_returns_everything_unchanged(self):
        d = {"a": {"session_id": "sess-mine"}, "c": {"session_id": "sess-other"}}
        with mock.patch.dict(os.environ, {spawn.ORCHESTRATOR_SESSION_ID_ENV: "sess-mine"}):
            out = spawn._roster_own(d, all_scope=True)
        self.assertEqual(out, d)

    def test_roster_own_empty_state_parity_when_env_unset(self):
        d = {"a": {"session_id": None}, "b": {"session_id": None}}
        os.environ.pop(spawn.ORCHESTRATOR_SESSION_ID_ENV, None)
        out = spawn._roster_own(d, all_scope=False)
        self.assertEqual(set(out), {"a", "b"})

    # -- roster_watchdog scoping + orphan surfacing -----------------------

    def test_roster_watchdog_default_scope_sees_own_all_sees_both_orphan_surfaces(self):
        with tempfile.TemporaryDirectory() as td:
            roster_path = Path(td) / "active.json"
            own_log = Path(td) / "own.log"
            own_log.write_text('{"type":"text"}\n')
            other_log = Path(td) / "other.log"
            other_log.write_text('{"type":"text"}\n')
            roster_path.write_text(json.dumps({
                "issue-1/implementation": self._entry(
                    own_log, pid=os.getpid(), issue=1, session_id="sess-mine"),
                "issue-2/implementation": self._entry(
                    other_log, pid=999999999, issue=2, session_id="sess-other"),
            }))
            old_roster, old_state, old_ledger = (
                spawn.ROSTER, spawn.WATCHDOG_STATE, spawn.RECONCILE_LEDGER)
            spawn.ROSTER = roster_path
            spawn.WATCHDOG_STATE = Path(td) / "watchdog_state.json"
            spawn.RECONCILE_LEDGER = Path(td) / "reconcile_ledger.json"
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with mock.patch.dict(
                        os.environ, {spawn.ORCHESTRATOR_SESSION_ID_ENV: "sess-mine"}), \
                     mock.patch.object(spawn, "_board_wide_sweep", return_value=0), \
                     mock.patch.object(spawn, "_post_session_end_comment"), \
                     mock.patch.object(spawn, "diagnose_health",
                                        return_value={"state": None, "detail": "d"}):
                    spawn.roster_watchdog()
                default_out = buf.getvalue()
                buf.seek(0); buf.truncate(0)
                with mock.patch.dict(
                        os.environ, {spawn.ORCHESTRATOR_SESSION_ID_ENV: "sess-mine"}), \
                     mock.patch.object(spawn, "_board_wide_sweep", return_value=0), \
                     mock.patch.object(spawn, "_post_session_end_comment"), \
                     mock.patch.object(spawn, "diagnose_health",
                                        return_value={"state": None, "detail": "d"}):
                    spawn.roster_watchdog(all_scope=True)
                all_out = buf.getvalue()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                spawn.WATCHDOG_STATE = old_state
                spawn.RECONCILE_LEDGER = old_ledger
            self.assertIn("[orphaned] issue-2/implementation", default_out)
            self.assertNotIn("issue-1/implementation: session sess-mine",
                              default_out.replace("[orphaned] ", ""))
            self.assertIn("issue-2/implementation", all_out)
            self.assertNotIn("[orphaned]", all_out)

    # -- _undispositioned_role_prs scoping --------------------------------

    def test_undispositioned_role_prs_excludes_own_roster_branch(self):
        prs = [
            {"number": 1, "headRefName": "issue-11/implementation",
             "body": "", "url": "https://example/1"},
            {"number": 2, "headRefName": "issue-22/qa",
             "body": "", "url": "https://example/2"},
        ]

        def fake_run(cmd, **k):
            if cmd[:2] == ["gh", "repo"]:
                return subprocess.CompletedProcess(cmd, 0, "o/r\n", "")
            if cmd[:3] == ["gh", "pr", "list"]:
                return subprocess.CompletedProcess(cmd, 0, json.dumps(prs), "")
            raise AssertionError(cmd)

        sys.path.insert(0, str((Path(spawn.__file__).parent / "gates").resolve()))
        import ci as _ci
        roster = {
            "issue-11/implementation": {"session_id": "sess-mine"},
            "issue-22/qa": {"session_id": "sess-other"},
        }
        with mock.patch.object(spawn.subprocess, "run", fake_run), \
             mock.patch.object(spawn, "_roster_load", lambda: roster), \
             mock.patch.dict(os.environ, {spawn.ORCHESTRATOR_SESSION_ID_ENV: "sess-mine"}), \
             mock.patch.object(_ci, "_approved_roles_on_issue",
                                lambda repo, issue: {"implementation"}):
            blockers, ok = spawn._undispositioned_role_prs(Path("."))
        self.assertTrue(ok)
        self.assertEqual([b["issue"] for b in blockers], [22])

    # -- roster_ps watcher identity ---------------------------------------

    def test_roster_ps_labels_watcher_owned_by_other_session(self):
        with tempfile.TemporaryDirectory() as td:
            roster_path = Path(td) / "active.json"
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            roster_path.write_text(json.dumps({
                "issue-3/implementation": self._entry(
                    log, work=str(Path(td) / "work"), pid=os.getpid(), issue=3,
                    session_id="sess-other"),
            }))
            old_roster = spawn.ROSTER
            old_ws_idx_load = spawn._workspace_index_load
            spawn.ROSTER = roster_path
            ws_entry = {"watcher_pid": os.getpid(), "watcher_armed_at": int(time.time())}
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with mock.patch.dict(
                        os.environ, {spawn.ORCHESTRATOR_SESSION_ID_ENV: "sess-mine"}), \
                     mock.patch.object(spawn, "_workspace_index_load",
                                        lambda: {f"{spawn._repo_identity(str(Path(td) / 'work'))}/issue-3/implementation": ws_entry}), \
                     mock.patch.object(spawn, "_watcher_looks_real", return_value=True):
                    spawn.roster_ps()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
            self.assertIn("다른 세션 소유", buf.getvalue())

    # -- CLI --all thread-through ------------------------------------------

    def test_cli_watchdog_all_flag_threads_all_scope(self):
        # 이슈 #1486: sibling test_cli_watchdog_no_all_flag_threads_cwd_as_root
        # 와 같은 이유로 락 PATH 를 격리한다 — 자세한 설명은 그 테스트의
        # 주석 참고.
        with tempfile.TemporaryDirectory() as td:
            tmp_lock_path = Path(td) / "watchdog.lock"
            with mock.patch.object(spawn, "roster_watchdog", return_value=0) as m, \
                 mock.patch.object(spawn.watchdog_lock_acquire, "__defaults__",
                                    (tmp_lock_path, None)), \
                 mock.patch.dict(os.environ,
                                  {"SPAWN_WATCHDOG_ALLOW_NONCANONICAL": "1"}), \
                 mock.patch.object(sys, "argv",
                                    ["spawn.py", "watchdog", "--all"]):
                spawn.main()
        m.assert_called_once_with(auto_respawn=False, all_scope=True,
                                   root=Path(".").resolve())

    def test_cli_watchdog_no_all_flag_threads_cwd_as_root(self):
        # 이슈 #1219: `-C` 없이(기본값 ".") 불러도 `roster_watchdog` 은
        # 컨슈머 세션의 cwd 를 `root` 로 받아야 한다 — 전역 ROOT(체크아웃)를
        # 암묵적으로 스캔하던 예전 경로가 이 트립을 우회하지 않는지 확인.
        #
        # 이슈 #1486: #1456 이 도입한 단일-인스턴스 락은 전역
        # `WATCHDOG_LOCK_PATH` (`<STATE_ROOT>/watchdog.lock`) 에 걸리는데,
        # 이 경로는 이 체크아웃에서 실제로 도는 Monitor 워치독과 공유된다
        # — 락을 mock/no-op 하면 #1456 의 회귀 커버리지가 죽으므로, 대신
        # `watchdog_lock_acquire` 의 `lock_path` 기본값만 tmp 로 바꿔치기해
        # 진짜 flock 획득/기록 로직은 그대로 tmp 경로 위에서 돈다(sibling
        # 유닛 테스트 tests/test_watchdog_freshness.py 가 `lock_path` 를
        # 인자로 주입하는 것과 같은 격리 패턴 — CLI 진입점에는 그 인자를
        # 실어 나를 통로가 없어 기본값 자체를 바꾼다). canonical-체크아웃
        # 가드도 role-workspace 체크아웃에서 도는 이 테스트 자신이 걸리지
        # 않도록 기존 `SPAWN_WATCHDOG_ALLOW_NONCANONICAL` 오버라이드를 쓴다
        # — 이 역시 락과 무관한 별개 가드라 no-op 대상이 아니다.
        with tempfile.TemporaryDirectory() as td:
            tmp_lock_path = Path(td) / "watchdog.lock"
            with mock.patch.object(spawn, "roster_watchdog", return_value=0) as m, \
                 mock.patch.object(spawn.watchdog_lock_acquire, "__defaults__",
                                    (tmp_lock_path, None)), \
                 mock.patch.dict(os.environ,
                                  {"SPAWN_WATCHDOG_ALLOW_NONCANONICAL": "1"}), \
                 mock.patch.object(sys, "argv",
                                    ["spawn.py", "watchdog", "-C", td]):
                spawn.main()
            m.assert_called_once_with(auto_respawn=False, all_scope=False,
                                       root=Path(td).resolve())
            self.assertTrue(tmp_lock_path.exists(),
                             "isolated lock path 에 실제로 락 파일이 기록돼야 "
                             "한다 — 락 획득 자체는 mock 되지 않았다.")
