"""Session events / workspace-index / watch machinery, extracted from
spawn.py (issue #2105, extraction 5/N).

Pure move — no behavior change. spawn.py imports this module and re-exports
every moved name, so external callers and tests keep addressing them as
`spawn.<name>`.

Patching-compat mechanism (copied from relay.py/roster.py/plumbing.py/
watchdog.py, extractions 1-4): every cross-function reference here resolves
at call time through `_sp` — the spawn module object, injected by spawn.py
right after it imports this module (guarded so only the canonical
spawn/__main__ module binds it), so `mock.patch.object(spawn, "<name>")`
patches stay visible to the moved code. Names that still live in spawn.py
and are reached through `_sp` include `ROOT`, `_alive`, `_roster_load`,
`session_end_verdict`, the respawn/crash-comment helpers, `roster_remove`,
`_pr_open_or_merged_for_branch`, `ledger_write`, and the roster/lease
functions — each a seam for a later extraction.

Module-level constants whose values bind at import time moved here WITH
their users (`EVENTS_SUFFIX`, `OFFSET_SUFFIX`, `WORKSPACE_INDEX`, the
refusal/gate regex tables, `WATCH_CRASH_RC`, `WATCH_WALLCLOCK_RC`,
`_LEGACY_WORKSPACE_KEY_RE`) — spawn.py re-exports them by assignment.
`ROOT` and `STATE_ROOT` are recomputed here with the exact expressions
spawn.py uses (same directory, same env, same import pass) because
`WORKSPACE_INDEX` derives from `STATE_ROOT` at import time; run-time
references still go through `_sp` so patches on spawn attributes are seen.
One called-out adjustment beyond bare `_sp.` prefixes:
`_rearm_watcher_detached` re-invokes the spawn CLI via
`Path(__file__).resolve()` — moved here that must keep naming spawn.py,
so it becomes `Path(_sp.__file__).resolve()`.
"""
from __future__ import annotations
import contextlib
import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# The spawn module object; set by spawn.py on import. All cross-module lookups
# resolve through it at call time so monkeypatches on spawn attributes are seen.
_sp = None

# Import-time anchors — same expressions as spawn.py.
ROOT = Path(__file__).resolve().parent
STATE_ROOT = (Path(os.environ["MUSTER_STATE_ROOT"]).resolve()
              if os.environ.get("MUSTER_STATE_ROOT") else ROOT / "runs")


def _git_head(cwd: str) -> str | None:
    """현재 HEAD 커밋. 아직 커밋이 없는 새 레포면 None (에러로 취급하지
    않는다 — 커밋이 없는 상태도 유효한 시작점이다)."""
    c = subprocess.run(["git", "-C", cwd, "rev-parse", "HEAD"],
                       capture_output=True, text=True)
    return c.stdout.strip() if c.returncode == 0 else None

EVENTS_SUFFIX = ".events.jsonl"
OFFSET_SUFFIX = ".events.offset"
WORKSPACE_INDEX = STATE_ROOT / "workspaces.json"
_PR_URL_RE = re.compile(r"https://github\.com/[^\s\"'\\]+/pull/\d+")
# progress 이벤트를 세우는 Bash 명령 접두사 — 산출물 쓰기(Write/Edit)와 함께
# "무슨 일이 있었는지"의 저비용 신호. ls/grep/cat 같은 탐색성 호출은 여기
# 없으니 안 걸린다 (이슈 #180).
_PROGRESS_BASH_PREFIXES = ("git commit", "git push", "gh pr create",
                           "python3 tests/test_spawn.py", "python3 gates/ci.py")

# 이슈 #232: 도구 거부를 낸 층 판별 — 세션 로그의 tool_result 스트림에 이미
# 있는 텍스트로 분류한다(새 계측 없음). 층 1(게이트)은 Claude Code 가 감싸는
# `PreToolUse:<tool> hook error: [<hook 경로>]` 뒤에 gate-lib.sh 의
# `gate_deny`가 쓴 `<게이트>: refused — <사유>` 가 따라온다(gate-lib.sh:77-79).
# 층 2(하네스 권한)·층 3(샌드박스) 패턴은 이슈 #232 본문이 실제 세션 로그에서
# 그대로 뽑아온 문자열이다 — 임의 확장 금지, 새 샘플은 이슈로 먼저 확인.
_GATE_HOOK_RE = re.compile(r"^PreToolUse:\S+ hook error: \[([^\]]*)\]")
_GATE_DENY_RE = re.compile(r"(\S+):\s*refused\s*—")
_HARNESS_REFUSAL_PATTERNS = (
    re.compile(r"Permission to use \S+ has been denied"),
    re.compile(r"requires approval"),
    re.compile(r"cannot be statically analyzed"),
    re.compile(r"simple_expansion"),
)
_SANDBOX_REFUSAL_PATTERNS = (
    re.compile(r"Operation not permitted"),
    re.compile(r"haven't granted it yet"),
    # 이슈 #289 H2: 샌드박스가 거부한 생성이 EEXIST 로 변환되면 git 은 이를
    # 진짜 잠금 경합처럼 보고한다(`cannot lock config file .git/config:
    # File exists`) — 실측: 세션이 이걸 실제 잠금으로 오인해
    # `.git/config.lock`을 지웠다. `.git/config`류 경로로 범위를 좁혀 무관한
    # "File exists" 오류를 삼키지 않는다.
    re.compile(r"cannot lock config file .*\.git/config.*: File exists"),
)


def _tool_result_text(content) -> str:
    """tool_result 블록의 content 는 문자열이거나 텍스트 블록 리스트다."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return ""


def _classify_refusal_text(text: str, command: str | None = None):
    """거부 tool_result 텍스트를 층으로 분류한다. 매치 없으면 None, 있으면
    (이벤트 타입, 세션당 dedup 키, detail) — 층 1 의 게이트 이름은 hook 경로
    stem 에서만 뽑는다. `gate_deny <role-or-gate-name> <message>` 의 첫
    토큰(`_GATE_DENY_RE`)은 게이트 이름을 보장하지 않는다(gate-lib.sh:75,
    이슈 #235 Finding 2 실측: 역할 이름이 실렸다) — 사유 텍스트를 자르는
    위치로만 쓴다.

    이슈 #246 결함 2: dedup 키는 이제 분류된 텍스트(정규화·절삭 후)를
    포함한다 — 같은 층의 서로 다른 두 거부가 첫 번째 것에 가려지지 않는다.
    내부 공백/줄바꿈(`_tool_result_text`의 여러 텍스트 블록 join 이 넣는
    `\n` 포함)은 단일 스페이스로 뭉친 뒤 기존 300자 한도로 자른다 — 대소문자는
    그대로 둔다(서로 다른 사유 문자열을 대소문자만으로 뭉개지 않기 위해).
    층 1 의 키는 stem 이 아니라 hook 의 전체 경로로 건다 — 같은 파일명
    stem 을 공유하는 서로 다른 hook 스크립트가 충돌하지 않도록; `stem` 은
    사람이 보는 `detail["gate"]` 필드로만 남는다."""
    hook_m = _sp._GATE_HOOK_RE.search(text)
    if hook_m:
        hook_path = hook_m.group(1)
        gate = Path(hook_path).stem
        deny_m = _sp._GATE_DENY_RE.search(text)
        reason = (" ".join(text[deny_m.end():].strip().split())[:300] if deny_m
                  else " ".join(text.strip().split())[:300])
        return ("gate-refusal", ("gate", hook_path, reason),
                {"gate": gate, "reason": reason})
    for pat in _sp._HARNESS_REFUSAL_PATTERNS:
        if pat.search(text):
            detail_text = " ".join(text.strip().split())[:300]
            # 이슈 #558: 거부 사유 문구만으로는 오케스트레이터가 "정당하게
            # 필요했던 거부(사전 허용에 없던 명령)"와 "모델이 그냥 안 돌린
            # 것"을 구분할 수 없었다 — 상관된 Bash 명령이 있으면 이벤트
            # detail 에 얹는다. dedup 키(위 튜플)는 detail_text 만 쓴다:
            # 같은 사유 문구의 서로 다른 명령까지 별도 이벤트로 쪼개는 건
            # 이 변경의 범위 밖이다(제안서 "What will be done" 참고).
            detail = ({"text": detail_text, "command": command[:300]}
                      if command else detail_text)
            return ("harness-refusal", ("harness", detail_text), detail)
    for pat in _sp._SANDBOX_REFUSAL_PATTERNS:
        if pat.search(text):
            detail = " ".join(text.strip().split())[:300]
            return ("sandbox-refusal", ("sandbox", detail), detail)
    return None


def _count_structural_denials(text: str) -> int:
    """이슈 #994: watchdog 신호 3 이 트랜스크립트 텍스트에서 "denied" 단어를
    세던 것(예: 게이트 소스를 인용/설명하는 세션이 실제 거부 0건인데도 카운터를
    올림 — 이슈-476 실측: 89건 신고, 실제 0건)을 구조적 파싱으로 대체한다.
    `text` 를 줄 단위 JSONL 로 파싱해 `type: "user"` 줄의 `tool_result` 블록 중
    `is_error` 이고 `_classify_refusal_text` 가 실제 거부 모양으로 분류하는
    것만 센다 — 어시스턴트/파일 텍스트에 우연히 등장하는 단어는 세지 않는다.

    `watchdog_check_one` 이 보는 `text` 는 로그 스캔 구간을 바이트 오프셋으로
    자른 슬라이스라 마지막 줄이 쓰기 도중 잘렸을 수 있다(라이브 스트림 루프가
    이미 관용하는 것과 동일, spawn.py:5573-5575 부근) — 그런 줄은 `json.loads`
    가 실패하므로 조용히 건너뛴다(관찰 전용 신호는 fatal 이 될 수 없다).
    """
    count = 0
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if not isinstance(obj, dict) or obj.get("type") != "user":
            continue
        for block in (obj.get("message") or {}).get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "tool_result":
                continue
            if not block.get("is_error"):
                continue
            result_text = _sp._tool_result_text(block.get("content"))
            if _sp._classify_refusal_text(result_text) is not None:
                count += 1
    return count


def _count_structural_delegations(text: str) -> int:
    """이슈 #2217: watchdog 신호 2("background-delegation-phrasing")가
    `run_in_background`/`delegate` 같은 단어를 세던 것을 구조적 파싱으로
    대체한다 — 우리 자신이 매 세션에 주입하는 headless 경고 프롬프트가
    바로 그 단어들로 배경 위임을 하지 말라고 경고하는 바람에, 단어 매치는
    100% 세션에서 오탐했다(이슈 #2217 실측). `_count_structural_denials`
    (이슈 #994)와 같은 관용: `text` 를 줄 단위 JSONL 로 파싱해
    `type: "assistant"` 줄의 `tool_use` 블록 중 `input.run_in_background`
    가 참인 것만 센다 — 지시문 텍스트(`type: "system"`)나 어시스턴트가
    인용/설명하는 단어는 세지 않는다.
    """
    count = 0
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if not isinstance(obj, dict) or obj.get("type") != "assistant":
            continue
        for block in (obj.get("message") or {}).get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            if (block.get("input") or {}).get("run_in_background"):
                count += 1
    return count


def _flush_correlated_refusals(events_path: Path, pending_refusals: dict,
                                denials: list) -> None:
    """이슈 #246 결함 3: 확정된 `permission_denials`(리스트, 비었을 수도 있음)와
    버퍼링된 후보를 `tool_name` 별 건별(per-candidate)로 상관시킨다 — 세션
    전체를 가리는 불리언 하나(`refusals_seen`) 대신, 후보마다 독립적으로
    denials 의 남은 수량을 소비한다. 상관 안 되는(스푸리어스이거나
    `tool_use_id` 를 못 찾은) 후보는 실제 층 라벨로 내보내지 않고 그냥
    버린다 — denials 가 남아 있다는 확정 근거가 없는 한 확정 라벨을
    참칭하지 않는다.

    `tool_name` 이 없거나 dict 가 아닌 denial 항목은 `remaining`(Counter)에서
    자연히 빠지므로 애초에 어느 후보와도 매치되지 않는다 — 그런데 그 항목을
    그냥 버리면, 매치될 수 없는 그 denial 자체가 세든 흔적 없이 사라진다
    (실측된 회귀: 실측 근거인 `docs/decisions/2026-07-29-headless-cli-measured-facts.md`
    가 확인한 `{"tool_name": ...}` 형태를 벗어나는 항목이 오면 이벤트가 0건이
    된다 — 이슈 #246 결함 1 이 없애려던 바로 그 "0건 = 무해" 결과를 다른
    문으로 재도입한다). `unattributable` 로 그 개수를 별도로 세어 leftover
    판정에 더한다 — tool_name 이 있는 denial 은 남은 매치 실패분만, 없는
    denial 은 통째로 leftover 로 잡혀 폴백을 놓치지 않는다. 모든 후보를
    확인한 뒤에도 denials 에 남은/귀속 못한 수량이 있으면(후보가 하나도
    없던 경우 포함) `unclassified-refusal` 폴백을 한 번 낸다."""
    remaining = _sp.Counter(d.get("tool_name") for d in denials
                        if isinstance(d, dict) and d.get("tool_name"))
    unattributable = sum(1 for d in denials
                         if not (isinstance(d, dict) and d.get("tool_name")))
    for ev_type, detail, tool_name in pending_refusals.values():
        if tool_name and remaining.get(tool_name):
            remaining[tool_name] -= 1
            _sp._append_event(events_path, ev_type, detail)
    if sum(remaining.values()) + unattributable > 0:
        _sp._append_event(events_path, "unclassified-refusal", str(denials)[:200])


def _flush_unverified(events_path: Path, pending_refusals: dict) -> None:
    """이슈 #246 결함 1: 터미널 `result` 줄이 아예 없거나(EOF/크래시 — S1/S3)
    `permission_denials` 형태를 신뢰할 수 없을 때(S2, 리스트가 아닌 값)
    호출된다. `permission_denials` 와 상관시킬 확정 근거가 없으므로 이미
    층 분류는 된 후보를 그 확정 라벨(gate-refusal 등)로 참칭하지 않고,
    `unverified-refusal` 로 정직하게 남긴다 — 버리는 대신, 그러나 확정도
    아닌 채로."""
    for ev_type, detail, _tool_name in pending_refusals.values():
        _sp._append_event(events_path, "unverified-refusal", detail)


def _events_path(work: str) -> Path:
    return Path(str(work) + _sp.EVENTS_SUFFIX)


def _offset_path(work: str) -> Path:
    return Path(str(work) + _sp.OFFSET_SUFFIX)


def _append_event(events_path: Path, ev_type: str, detail) -> None:
    with events_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts": int(time.time()), "type": ev_type,
                              "detail": detail}, ensure_ascii=False) + "\n")


def _prior_event_details(events_path: Path, ev_type: str) -> set:
    """`events_path` 에 이미 남은 `ev_type` 이벤트들의 `detail` 집합.

    프로세스 재시작(같은 워크스페이스로 재스폰)을 건너 `pr-opened` 를
    멱등하게 만드는 데 쓴다 — 이 워크스페이스의 `.events.jsonl` 은
    append-only 이므로 과거 기록을 읽으면 이전 프로세스의 in-memory
    `pr_seen` 을 재구성할 수 있다."""
    if not events_path.exists():
        return set()
    out = set()
    for line in events_path.read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if isinstance(ev, dict) and ev.get("type") == ev_type:
            out.add(ev.get("detail"))
    return out

def _read_offset(offset_path: Path) -> int:
    try:
        return int(offset_path.read_text().strip())
    except (OSError, ValueError):
        return 0


def _event_count(events_path: Path) -> int:
    """events.jsonl 의 줄 수 — offset 과 같은 단위(줄)다."""
    try:
        return len(events_path.read_text(encoding="utf-8").splitlines())
    except OSError:
        return 0


def _origin_pr_prefix(cwd) -> str | None:
    """이 레포 자신의 PR URL 접두사. 판별 못 하면 None(=범위 검사 생략)."""
    try:
        out = subprocess.run(["git", "-C", str(cwd), "remote", "get-url", "origin"],
                             capture_output=True, text=True)
    except OSError:
        return None
    if out.returncode != 0:
        return None
    m = re.search(r"github\.com[:/]+([^/\s]+/[^/\s]+?)(?:\.git)?\s*$", out.stdout)
    return f"https://github.com/{m.group(1)}/pull/" if m else None


def _write_offset(offset_path: Path, n: int) -> None:
    offset_path.write_text(str(n))


def _repo_identity(cwd) -> str:
    """이슈 #533: workspace 인덱스 키의 레포 구분자 — 순수 로컬, 네트워크
    호출 없음(`_origin_pr_prefix` 와 같은 방식). origin remote 가 없거나
    git 저장소가 아니면 디렉터리 basename 으로 떨어진다 — 항상 성공한다."""
    try:
        out = subprocess.run(["git", "-C", str(cwd), "remote", "get-url", "origin"],
                             capture_output=True, text=True)
        if out.returncode == 0:
            m = re.search(r"github\.com[:/]+[^/\s]+/([^/\s]+?)(?:\.git)?\s*$", out.stdout)
            if m:
                return m.group(1)
    except OSError:
        pass
    return Path(str(cwd)).resolve().name


_LEGACY_WORKSPACE_KEY_RE = re.compile(r"^issue-\d+/[^/]+$")


def _workspace_index_load() -> dict:
    try:
        d = json.loads(_sp.WORKSPACE_INDEX.read_text())
    except (OSError, ValueError):
        return {}
    migrated = False
    for key in list(d.keys()):
        if _sp._LEGACY_WORKSPACE_KEY_RE.match(key):
            entry = d[key]
            new_key = f"{_sp._repo_identity(entry['work'])}/{key}"
            if new_key in d and new_key != key:
                raise RuntimeError(
                    f"workspace index migration collision: {key!r} -> "
                    f"{new_key!r} already exists (live entries: "
                    f"{d[new_key]!r} vs {entry!r})")
            del d[key]
            d[new_key] = entry
            migrated = True
    if migrated:
        _sp.WORKSPACE_INDEX.write_text(json.dumps(d, indent=2, ensure_ascii=False))
    return d


@contextlib.contextmanager
def _workspace_index_locked():
    """이슈 #857 finding 4(경고 발견): `WORKSPACE_INDEX` 의 load-mutate-save
    구간에 `ROSTER`(`_roster_locked()`)와 달리 잠금이 없어, 서로 다른 키에
    쓰는 두 프로세스가 동시에 로드-변경-저장하면 나중에 저장한 쪽이 먼저
    저장한 쪽의 키를 조용히 지운다 — `_workspace_index_put()` 자체의
    같은-키 충돌 가드(위)는 한 프로세스의 로드 시점 안에서만 보이므로 이
    레이스를 못 잡는다. `ROSTER` 와 같은 fcntl 잠금 파일 패턴으로 직렬화."""
    lock_path = _sp.WORKSPACE_INDEX.with_name(_sp.WORKSPACE_INDEX.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def _workspace_index_put(issue: int, skill: str, work: str, log: str,
                          watcher_pid: int | None = None,
                          watcher_armed_at: float | None = None) -> None:
    """이슈 #488: `watcher_pid` 는 이 스폰이 자동 무장한 워처 프로세스의
    pid(있으면) — `watchdog`이 여기서 읽어 워처가 죽었는지 신고한다.

    이슈 #559: `watcher_armed_at` 은 그 워처가 무장된 시각(`time.time()`)—
    `ps` 가 세션 시작 시각(`ts`)과 구분해 "워처가 언제 붙었는지"를 보여준다.

    이슈 #533: 키는 레포 정체성(`_repo_identity`)까지 포함한다 — 서로 다른
    레포가 같은 이슈 번호+역할로 충돌하면 이전 엔트리가 조용히 덮어써지던
    문제. 같은 키에 다른 `work` 값이 이미 있으면(=진짜 충돌이거나 버그)
    조용히 덮지 않고 즉시 에러낸다.

    이슈 #857 finding 4: load-mutate-save 전체를 `_workspace_index_locked()`
    로 감싸 동시 쓰기 레이스에서 한쪽 키가 조용히 사라지지 않게 한다."""
    _sp.WORKSPACE_INDEX.parent.mkdir(parents=True, exist_ok=True)
    with _sp._workspace_index_locked():
        d = _sp._workspace_index_load()
        key = f"{_sp._repo_identity(work)}/issue-{issue}/{skill}"
        existing = d.get(key)
        if existing is not None and existing.get("work") != work:
            raise RuntimeError(
                f"workspace index collision on {key!r}: existing entry "
                f"{existing!r} has a different work dir than {work!r} — "
                f"refusing to overwrite silently (issue #533)")
        entry = {"work": work, "log": log, "skill": skill}
        if watcher_pid is not None:
            entry["watcher_pid"] = watcher_pid
        if watcher_armed_at is not None:
            entry["watcher_armed_at"] = watcher_armed_at
        d[key] = entry
        _sp.WORKSPACE_INDEX.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def _live_session_start_index(events_path: Path, pid) -> int | None:
    """이슈 #557: 지금 살아있는 세션(`pid`)의 `session-start` 이벤트가
    events.jsonl 에서 몇 번째 줄(0-based)인지 찾는다. 같은 워크스페이스
    로그에 이전 세션들의 이벤트가 남아 있어도, 이 줄보다 앞선 이벤트는
    전부 이전 세션 몫이므로 follow 커서가 재생하면 안 된다. 같은 pid 를
    쓴 세션이 여럿 기록돼 있으면(재사용) 가장 최근 것을 고른다."""
    if pid is None:
        return None
    try:
        lines = events_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    idx = None
    for i, line in enumerate(lines):
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "session-start" and ev.get("detail", {}).get("pid") == pid:
            idx = i
    return idx


def _await_bounded(events_path: Path, offset_path: Path, stall_timeout_min: float,
                    log_path: Path, session_tag: tuple | None = None,
                    show_banner: bool = True, max_wait_s: float | None = None) -> int:
    """이벤트 하나가 뜨거나 stall 시간이 다 찰 때까지 — 둘 중 먼저 오는
    쪽에서 리턴한다. 무한정 블록하지 않는다 (이슈 #114 proposal).

    stall 은 events.jsonl 에 안 남고 offset 도 안 미룬다 — 다음 watch 가
    같은 미보고 구간을 다시 본다.

    `session_tag` (pid, ts) 가 주어지면 찍는 이벤트 줄마다 원본 세션을
    표시한다 — `--all` 처럼 여러 세션을 다중화해 보는 소비자가 어느
    이벤트가 어느 세션 것인지 알 수 있게 한다(이슈 #557).
    `show_banner=False` 면 "스폰은 리턴했지만" 배너를 찍지 않는다 —
    `--follow` 반복 호출 중 이미 한 번 찍었으면 호출자가 이걸로 끈다.

    `max_wait_s` (기본 None=비활성) 는 활동(로그 크기 변화)과 무관하게
    호출 진입 시점부터 잰 순수 wall-clock 상한이다 — stall 시계는
    로그가 계속 자라면 절대 안 찍히므로(이슈 #645), 수다스럽지만
    끝나지 않는 세션에도 리턴 보장이 필요한 호출자가 옵트인한다. stall
    과 마찬가지로 offset 을 안 미루고 리턴한다 — 다음 호출이 같은
    미보고 구간을 다시 본다.
    """
    limit_s = stall_timeout_min * 60
    seen = _sp._read_offset(offset_path)
    try:
        last_size = log_path.stat().st_size
    except OSError:
        last_size = 0
    last_change = time.monotonic()
    start = time.monotonic()
    poll_s = 0.05
    while True:
        if events_path.exists():
            lines = events_path.read_text(encoding="utf-8").splitlines()
            if len(lines) > seen:
                ev = json.loads(lines[seen])
                _sp._write_offset(offset_path, seen + 1)
                tag = f" [session pid={session_tag[0]} ts={session_tag[1]}]" if session_tag else ""
                print(f"[watch]{tag} {ev['type']}: {ev['detail']}")
                # exit 0 는 "스폰이 리턴했다"이지 "세션이 끝났다"가 아니다.
                # 호출자가 그 둘을 추론하게 두면 오케스트레이터가 사람에게
                # 끝났다고 오보한다 — 이 저장소가 가장 비싸게 치는 실패다
                # (이슈 #142). session-end 만이 종료를 뜻한다.
                if ev["type"] != "session-end" and show_banner:
                    print("[watch] 스폰은 리턴했지만 세션은 계속 돈다 — "
                          "상태는 spawn.py ps, 이어보려면 spawn.py watch",
                          file=sys.stderr)
                return 0
        try:
            size = log_path.stat().st_size
        except OSError:
            size = last_size
        if size != last_size:
            last_size = size
            last_change = time.monotonic()
        if time.monotonic() - last_change >= limit_s:
            if not log_path.exists():
                print(f"[watch] cannot observe: 세션 로그 파일이 없다 — "
                      f"{log_path}. stall 이 아니라 관측 채널 자체가 사라진 "
                      f"것이다 — clean 이력을 확인하거나 스킬을 다시 스폰하라",
                      file=sys.stderr)
                return 0
            secs = int(time.monotonic() - last_change)
            print(f"[watch] stall: 세션 로그 {secs}초째 무변화 — 이벤트 없이 "
                  f"멈춘다. 다시 spawn.py watch 로 재무장하라", file=sys.stderr)
            return 0
        if max_wait_s is not None and time.monotonic() - start >= max_wait_s:
            secs = int(time.monotonic() - start)
            print(f"[watch] wall-clock cap: {secs}초 경과 — 활동 여부와 무관하게 "
                  f"상한에 도달했다. 다시 spawn.py watch 로 재무장하라", file=sys.stderr)
            return _sp.WATCH_WALLCLOCK_RC
        time.sleep(poll_s)
        poll_s = min(poll_s * 2, 2.0)


WATCH_CRASH_RC = 2  # `--follow`가 session-end 없이 pid 사망을 감지했을 때
                    # 리턴하는 종료 코드 — 0(정상, session-end 도달)과도,
                    # 1(사용법 오류/기록 없음)과도 구분한다(이슈 #224,
                    # docs/issue-224/decisions/watch-crash-exit-code.md).
WATCH_WALLCLOCK_RC = 3  # `_await_bounded`/`_watch --follow` 가 활동과 무관한
                    # wall-clock 상한(`max_wait_s`/`--max-wait`)에 걸려
                    # 리턴했을 때의 종료 코드 — 0(이벤트/정상), 1(사용법
                    # 오류), 2(crash) 와 모두 구분한다(이슈 #645).


def _live_roster_matches(matches: list, issue: int) -> list:
    """`matches` (workspace-index (key, entry) 쌍들) 중 실제로 살아있는
    세션(roster 의 pid 로 판단)이 있는 것만 걸러낸다 — 이슈 #554: 역할이
    여럿 기록돼 있어도 그중 하나만 살아있으면 그게 사용자가 보고 싶은
    세션이다."""
    roster = _sp._roster_load()
    live = []
    for k, v in matches:
        skill = v.get("skill") or k.rsplit("/", 1)[1]
        e = roster.get(f"issue-{issue}/{skill}")
        if e is not None and _sp._alive(e.get("pid", 0)):
            live.append((k, v))
    return live


def _ambiguous_watch_exit(issue: int, matches: list, repo: str | None) -> None:
    """이슈 #554: 애매할 때(살아있는 세션이 0개 또는 2개 이상) 그대로
    붙여넣을 수 있는 명령을 에러에 찍는다 — `--session` 없이 재시도하면 같은
    메시지가 또 나오는 죽은 재시도 구간을 없앤다."""
    cwd_flag = f" -C {repo}" if repo else ""
    skills = [v.get("skill") or k.rsplit("/", 1)[1] for k, v in matches]
    cmds = "; ".join(
        f"spawn.py watch --issue {issue} --session {r}{cwd_flag}" for r in skills)
    sys.exit(f"이슈 {issue} 에 스킬이 여럿 기록돼 있다 — 스킬을 지정하라 "
             f"(후보: {', '.join(skills)}): {cmds}")


def _roster_fallback_entry(issue: int, skill: str | None, repo: str | None):
    """이슈 #1585: `watch`(워크스페이스 인덱스)와 `ps`(ROSTER)가 서로 다른
    소스를 읽어, 스폰 직후 워크스페이스 인덱스 쓰기가 아직 안 보이는
    짧은 창에서 `ps` 는 RUNNING 인데 `watch` 는 '기록 없음'을 내는 레이스가
    있었다(실측: 이슈-1582 phase-2 드라이브, 5초 지연 재시도에도 재현).
    ROSTER 엔트리도 `work`/`log` 필드를 들고 있으므로(roster_register 호출부
    참고), 워크스페이스 인덱스에 없을 때 ROSTER 의 살아있는 엔트리로부터
    같은 모양의 엔트리를 재구성해 두 소스가 존재 여부에서 일치하게 한다.
    조회만 하고 아무것도 기다리지 않는다 — 블로킹을 새로 넣지 않는다."""
    roster = _sp._roster_load()
    if skill:
        e = roster.get(f"issue-{issue}/{skill}")
        if not (e is not None and _sp._alive(e.get("pid", 0)) and e.get("work") and e.get("log")):
            return None, None
        if repo is not None and _sp._repo_identity(e["work"]) != repo:
            return None, None
        key = f"{_sp._repo_identity(e['work'])}/issue-{issue}/{skill}"
        return key, {"work": e["work"], "log": e["log"]}
    candidates = []
    for k, e in roster.items():
        found_skill = e.get("skill")
        if found_skill is None:
            m = re.match(rf"^issue-{issue}/([^/]+)$", k)
            if not m:
                continue
            found_skill = m.group(1)
        elif not k.startswith(f"issue-{issue}/"):
            continue
        if not (_sp._alive(e.get("pid", 0)) and e.get("work") and e.get("log")):
            continue
        if repo is not None and _sp._repo_identity(e["work"]) != repo:
            continue
        candidates.append((found_skill, e))
    if len(candidates) != 1:
        return None, None
    found_skill, e = candidates[0]
    key = f"{_sp._repo_identity(e['work'])}/issue-{issue}/{found_skill}"
    return key, {"work": e["work"], "log": e["log"]}


def _lookup_roster_entry(idx: dict, issue: int, skill: str | None, repo: str | None = None):
    """이슈 #533: `repo` 가 주어지면 그 레포로만 조회를 좁힌다 — `-C` 가
    지금까지 조회에 안 먹히던 구멍을 막는다. 안 주면(기존 기본값) 모든
    레포를 대상으로 이슈+역할 접미사로 매칭하던 예전 동작을 유지한다.

    이슈 #554: 역할을 안 줬는데 매치가 여럿이면, 그중 살아있는 세션이
    정확히 하나면 그걸 자동 선택한다 — watch 는 어차피 실행 중인 세션만
    보고하므로 그게 유일하게 뜻이 통하는 선택이다. 0개 또는 2개 이상
    살아있으면 여전히 애매하니 `--session`을 요구한다(실행 가능한 명령까지
    같이 찍는다)."""
    key, entry = _sp._lookup_workspace_entry(idx, issue, skill, repo=repo)
    if entry is None:
        fb_key, fb_entry = _sp._roster_fallback_entry(issue, skill, repo)
        if fb_entry is not None:
            return fb_key, fb_entry
    return key, entry


def _lookup_workspace_entry(idx: dict, issue: int, skill: str | None, repo: str | None = None):
    if repo is not None:
        if skill:
            key = f"{repo}/issue-{issue}/{skill}"
            entry = idx.get(key)
        else:
            matches = [(k, v) for k, v in idx.items()
                       if k.startswith(f"{repo}/issue-{issue}/")]
            if len(matches) > 1:
                live = _sp._live_roster_matches(matches, issue)
                if len(live) == 1:
                    matches = live
                else:
                    _sp._ambiguous_watch_exit(issue, matches, repo)
            key = matches[0][0] if matches else None
            entry = matches[0][1] if matches else None
        return key, entry
    if skill:
        matches = [(k, v) for k, v in idx.items() if k.endswith(f"/issue-{issue}/{skill}")]
        if len(matches) > 1:
            sys.exit(f"이슈 {issue}/{skill} 이 레포 여럿에 기록돼 있다 — -C 로 "
                     "레포를 지정하라: " + ", ".join(k.rsplit("/issue-", 1)[0] for k, _ in matches))
        key = matches[0][0] if matches else None
        entry = matches[0][1] if matches else None
    else:
        matches = [(k, v) for k, v in idx.items() if f"/issue-{issue}/" in k]
        if len(matches) > 1:
            live = _sp._live_roster_matches(matches, issue)
            if len(live) == 1:
                matches = live
            else:
                _sp._ambiguous_watch_exit(issue, matches, repo)
        key = matches[0][0] if matches else None
        entry = matches[0][1] if matches else None
    return key, entry


def _watch(issue: int, skill: str | None, stall_timeout_min: float,
           follow: bool = False, repo: str | None = None,
           max_wait_min: float | None = None, self_heal: bool = False) -> int:
    idx = _sp._workspace_index_load()
    key, entry = _sp._lookup_roster_entry(idx, issue, skill, repo=repo)
    if entry is None:
        # 등록 레이스(이슈 #484): 스폰이 막 리턴했지만 명부 쓰기가 아직
        # 반영되지 않았을 수 있다 — #451 의 "끝내 안 나타남"과는 구분되는
        # 경우로, 같은 stall_timeout_min 한도 안에서 _await_bounded 와
        # 동일한 백오프로 잠깐 재시도한다. 한도 안에 나타나면 계속
        # 진행하고, 끝내 안 나타나면 오늘의 기록-없음 처리로 떨어진다.
        limit_s = stall_timeout_min * 60
        start = time.monotonic()
        poll_s = 0.05
        while entry is None and time.monotonic() - start < limit_s:
            time.sleep(poll_s)
            poll_s = min(poll_s * 2, 2.0)
            idx = _sp._workspace_index_load()
            key, entry = _sp._lookup_roster_entry(idx, issue, skill, repo=repo)
    if entry is None:
        print(f"[watch] issue-{issue}{'/' + skill if skill else ''}: 기록 없음 — "
              f"아직 스폰된 적이 없다", file=sys.stderr)
        return 1
    work = entry["work"]
    events_path = _sp._events_path(work)
    offset_path = _sp._offset_path(work)
    log_path = Path(entry["log"])
    # 이슈 #557: 무장 시점에 살아있는 세션의 pid 를 명부에서 찾아, 그
    # session-start 줄보다 앞선(=이전 세션 몫인) 이벤트는 커서가 절대
    # 재생하지 않도록 offset 바닥을 그 줄로 끌어올린다. pid 를 못 찾으면
    # (명부 엔트리 부재) 오늘의 동작(스코프 없음)으로 그대로 떨어진다.
    m = re.search(r"issue-\d+/[^/]+$", key) if key else None
    roster_entry = _sp._roster_load().get(m.group(0)) if m else None
    live_pid = roster_entry.get("pid") if roster_entry else None
    session_idx = _sp._live_session_start_index(events_path, live_pid)
    session_tag = None
    if session_idx is not None:
        if _sp._read_offset(offset_path) < session_idx:
            _sp._write_offset(offset_path, session_idx)
        lines = events_path.read_text(encoding="utf-8").splitlines()
        detail = json.loads(lines[session_idx]).get("detail", {})
        session_tag = (detail.get("pid"), detail.get("ts"))
    if not follow:
        return _sp._await_bounded(events_path, offset_path, stall_timeout_min, log_path,
                               session_tag=session_tag)
    # --follow: _await_bounded 자체는 바꾸지 않고 반복 호출한다 — 매 호출이
    # 소비한 이벤트를 계속 찍다가, 그 이벤트 타입이 session-end 일 때만
    # 멈춘다. _await_bounded 는 이벤트 소비 여부와 무관하게 항상 0 을
    # 리턴하므로(stall 도 0), 무엇을 멈출 신호로 볼지는 offset 진행분을
    # 직접 읽어 판단한다 (이슈 #180).
    # 명부 엔트리가 끝내 나타나지 않으면 이 반복 자체가 무한정 돈다 —
    # session-end 도, 죽은 wrapper_pid 도 신호가 안 되기 때문이다(이슈
    # #451, #445 발견 2). `_await_bounded` 는 호출 한 번의 stall 만
    # 보장하므로, 여기서는 반복에 걸친 무진전 누적 시간을 직접 잰다.
    # 이슈 #1043: follow 진입 시점에 이미 살아있는 워처(자동 무장이든
    # 이전 follow 든)가 이 세션을 커버하고 있으면 그대로 두고, 없거나
    # 죽어있을 때만 이 follow 프로세스 자신을 워처로 등록한다 — 그래야
    # watchdog 이 살아있는 follow 를 stale 자동무장 pid 로 오인해 매
    # 틱마다 watcher-dead 를 오탐하지 않는다.
    follow_skill_m = re.search(r"issue-\d+/([^/]+)$", key) if key else None
    follow_skill = follow_skill_m.group(1) if follow_skill_m else skill
    current_watcher_pid = entry.get("watcher_pid")
    if not (current_watcher_pid is not None and
            _sp._watcher_looks_real(current_watcher_pid, issue, follow_skill)):
        _sp._workspace_index_put(issue, follow_skill, work, str(log_path),
                              watcher_pid=os.getpid(),
                              watcher_armed_at=time.time())
    stall_limit_s = stall_timeout_min * 60
    last_progress = time.monotonic()
    banner_shown = False  # 이슈 #557: --follow 반복 전체에서 배너는 한 번만
    # 이슈 #645: `_await_bounded` 는 호출 한 번의 stall 만 본다 — 로그가
    # 계속 자라는(진전은 있지만 끝나지 않는) 세션에 대해 `--follow` 전체의
    # 누적 wall-clock 을 여기서 잰다. 반복에 걸쳐 남은 예산을 매 호출마다
    # `max_wait_s` 로 좁혀 넘긴다.
    follow_start = time.monotonic()
    follow_budget_s = max_wait_min * 60 if max_wait_min is not None else None
    while True:
        before = _sp._read_offset(offset_path)
        try:
            before_size = log_path.stat().st_size
        except OSError:
            before_size = None
        call_max_wait_s = None
        if follow_budget_s is not None:
            remaining = follow_budget_s - (time.monotonic() - follow_start)
            if remaining <= 0:
                if self_heal:
                    print(f"[watch] follow wall-clock cap 도달 — self-heal: "
                          f"예산 창을 리셋하고 재무장한다", file=sys.stderr)
                    follow_start = time.monotonic()
                    last_progress = time.monotonic()
                    continue
                print(f"[watch] follow wall-clock cap 도달 — 다시 spawn.py "
                      f"watch --follow 로 재무장하라", file=sys.stderr)
                return _sp.WATCH_WALLCLOCK_RC
            call_max_wait_s = remaining
        rc = _sp._await_bounded(events_path, offset_path, stall_timeout_min, log_path,
                             session_tag=session_tag, show_banner=not banner_shown,
                             max_wait_s=call_max_wait_s)
        if rc == _sp.WATCH_WALLCLOCK_RC:
            if self_heal:
                follow_start = time.monotonic()
                last_progress = time.monotonic()
                continue
            return rc
        after = _sp._read_offset(offset_path)
        try:
            after_size = log_path.stat().st_size
        except OSError:
            after_size = None
        if after > before or after_size != before_size:
            last_progress = time.monotonic()
        if after > before:
            lines = events_path.read_text(encoding="utf-8").splitlines()
            try:
                ev = json.loads(lines[after - 1])
            except ValueError:
                ev = {}
            if ev.get("type") != "session-end":
                banner_shown = True
            if ev.get("type") == "session-end":
                return rc
        # 세션 프로세스 사망 판정보다 session-end 잔여 이벤트 소진을 먼저
        # 본다 — session_end_verdict() (spawn.py:1191-1236) 와 같은 순서
        # (PR #255 피드백 1). 정상 종료가 이미 session-end 를 남겼는데
        # 아직 offset 이 그 줄까지 못 갔다는 이유만으로 pid 사망과
        # 경합시켜 크래시로 오판하면 안 된다 — 다음 반복이 그 줄을
        # 소비하게 둔다.
        if events_path.exists():
            lines = events_path.read_text(encoding="utf-8").splitlines()
            def _ev_type(line):
                try:
                    return json.loads(line).get("type")
                except ValueError:
                    return None
            if any(_ev_type(line) == "session-end" for line in lines[after:]):
                continue
        # `pid`(claude 서브프로세스)가 아니라 `wrapper_pid`(호출자
        # 프로세스, roster_register() 참고)로 생존을 잰다 — `pid`는
        # push/리포트/ledger_write 를 거쳐 session-end 를 남기기 전에
        # proc.wait() 로 이미 정상적으로 죽어 있어서, 그 시점의 `pid`
        # 사망만으로 판정하면 아직 정상 진행 중인 후처리 구간을 크래시로
        # 오판한다(이슈 #224 hunt 발견).
        # 이슈 #533: `key` 는 workspace 인덱스 키(레포 접두사 포함)지만
        # ROSTER 는 별도 메커니즘으로 `issue-<n>/<role>` 그대로 키를 쓴다
        # (이번 변경의 out-of-scope) — 여기서 조회할 때는 접두사를 떼어
        # bare 형태로 되돌린다.
        m = re.search(r"issue-\d+/[^/]+$", key) if key else None
        roster_entry = _sp._roster_load().get(m.group(0)) if m else None
        pid = roster_entry.get("wrapper_pid") if roster_entry else None
        # 명부 엔트리 부재는 사망 신호로 안 쓴다(이슈 #266) — `_spawn_one()`의
        # 후처리 꼬리 동안 `roster_remove`(spawn.py:2995)가 `session-end`
        # 기록(spawn.py:3097)보다 먼저 실행돼 그 구간 전체에서 엔트리가
        # 없다. 엔트리가 있고 그 안의 wrapper_pid 가 죽어 있을 때만 크래시로
        # 본다 — 엔트리 부재는 불명으로 취급해 stall 안전망까지 계속 대기한다.
        if pid is not None and not _sp._alive(pid):
            print(f"[watch] 세션 프로세스가 사라졌다(pid {pid}) — session-end "
                  f"없이 끝났다. 크래시로 보고 멈춘다", file=sys.stderr)
            _sp._append_event(events_path, "watcher-ended-without-session-end",
                          {"pid": pid, "reason": "crash"})
            return _sp.WATCH_CRASH_RC
        if time.monotonic() - last_progress >= stall_limit_s:
            secs = int(time.monotonic() - last_progress)
            if self_heal:
                print(f"[watch] follow stall: {secs}초째 진행 없음 — "
                      f"self-heal: 재무장한다", file=sys.stderr)
                last_progress = time.monotonic()
                continue
            print(f"[watch] follow stall: {secs}초째 진행 없음 — 이벤트도 "
                  f"로그 변화도 없이 멈춘다. 다시 spawn.py watch --follow 로 "
                  f"재무장하라", file=sys.stderr)
            return 0


def _rearm_watcher_detached(issue: int, skill: str | None, stall_timeout_min: float,
                             repo: str | None = None, cwd: str | None = None) -> int:
    """이슈 #1133: `spawn.py watch --rearm` 의 본체 — 죽은 워처를 non-blocking
    으로 재무장한다. `_watch(..., follow=True)`는 워처 등록 뒤에도 자기
    자신이 blocking `--await_bounded` 루프를 돌아 호출자(오케스트레이터
    턴, 시간제한 Bash 호출)가 죽으면 방금 무장한 워처까지 함께 죽는다
    (실측: 2m 타임아웃으로 재무장한 워처 5/5 전원 사망) — 이 함수는 워처를
    detached 프로세스로만 띄우고 즉시 리턴한다.

    읽기(현재 워처가 죽었는가)-결정-스폰-쓰기(새 pid 등록) 전체를
    `_workspace_index_locked()` 한 번으로 감싼다: after-proposal hunt
    (stance 0)가 찾은 대로, 마지막 등록 write 만 잠그면 두 개의 동시
    `--rearm` 호출이 둘 다 "죽었다" 판정을 통과한 뒤 하나만 등록되고
    나머지 detached 자식은 추적 안 되는 채로 leak 된다. 그래서 자기
    자신의 flock 을 잡는 `_workspace_index_put()`(non-reentrant)을 이
    잠금 안에서 부르지 않고, 그 함수의 dict-shape/충돌 검사를 여기 안에서
    직접 반복한다."""
    with _sp._workspace_index_locked():
        idx = _sp._workspace_index_load()
        key, entry = _sp._lookup_roster_entry(idx, issue, skill, repo=repo)
        if entry is None:
            print(f"[watch] issue-{issue}{'/' + skill if skill else ''}: 기록 없음 — "
                  f"재무장할 대상이 없다", file=sys.stderr)
            return 1
        work = entry["work"]
        log_path = entry["log"]
        m = re.search(r"issue-\d+/([^/]+)$", key) if key else None
        rearm_skill = m.group(1) if m else skill
        current_watcher_pid = entry.get("watcher_pid")
        if (current_watcher_pid is not None and
                _sp._watcher_looks_real(current_watcher_pid, issue, rearm_skill)):
            # 이슈 #1975: pid 생존(및 신원 확인)만으로는 관측성을 보장하지
            # 않는다 — 워처는 살아있는데 이벤트가 흐르지 않는 "alive but
            # event-silent" 상태를 못 잡으면 --rearm 이 그 상태를 회복
            # 불가능하게 만든다(실측: 92분 무응답). watchdog signal 6(위
            # `_health_anomalies` 의 watcher-silent 판정)과 같은 기준으로,
            # 워처 로그가 armed 이후로 WATCHDOG_SILENCE_MIN 분 넘게 조용한
            # *동시에* 세션 로그가 그 이후로도 계속 자랐으면(진행은 있는데
            # 워처만 먹통) 죽은 워처와 동일하게 취급해 교체한다. 세션 로그가
            # 같이 멈춰 있으면(세션 자체가 정지) 오탐이라 교체하지 않는다.
            stale = False
            silence_min = None
            armed_at = entry.get("watcher_armed_at")
            watcher_log_path = Path(str(work) + ".watcher.log")
            if armed_at is not None and watcher_log_path.exists():
                w_mtime = watcher_log_path.stat().st_mtime
                baseline = max(w_mtime, float(armed_at))
                silence_min = (time.time() - baseline) / 60
                if silence_min > _sp.WATCHDOG_SILENCE_MIN:
                    session_log_path = Path(str(log_path)) if log_path else None
                    if (session_log_path is not None and session_log_path.exists()
                            and session_log_path.stat().st_mtime > baseline):
                        stale = True
            if not stale:
                print(f"[watch] issue-{issue}/{rearm_skill}: 워처 pid "
                      f"{current_watcher_pid} 이미 살아있다 — 재무장 안 함",
                      file=sys.stderr)
                return 0
            print(f"[watch] issue-{issue}/{rearm_skill}: 워처 pid "
                  f"{current_watcher_pid} 는 살아있지만 {int(silence_min)}분째 "
                  f"event-silent (세션 로그는 진행 중) — 옛 워처를 종료하고 "
                  f"재무장한다", file=sys.stderr)
            try:
                os.kill(current_watcher_pid, signal.SIGTERM)
            except OSError:
                pass
        watcher_log = Path(str(work) + ".watcher.log")
        resolved_cwd = str(Path(cwd if cwd is not None else ".").resolve())
        try:
            with watcher_log.open("a", encoding="utf-8") as wf:
                wproc = subprocess.Popen(
                    [sys.executable, str(Path(_sp.__file__).resolve()),
                     "-C", resolved_cwd,
                     "watch", "--issue", str(issue), "--session", rearm_skill,
                     "--follow", "--self-heal",
                     "--stall-timeout", str(stall_timeout_min)],
                    stdin=subprocess.DEVNULL, stdout=wf,
                    stderr=subprocess.STDOUT, start_new_session=True,
                )
        except OSError as exc:
            print(f"[watch] issue-{issue}/{rearm_skill}: 워처 재무장 실패 — {exc}",
                  file=sys.stderr)
            return 1
        d = _sp._workspace_index_load()
        existing = d.get(key)
        if existing is not None and existing.get("work") != work:
            raise RuntimeError(
                f"workspace index collision on {key!r}: existing entry "
                f"{existing!r} has a different work dir than {work!r} — "
                f"refusing to overwrite silently (issue #533)")
        d[key] = {"work": work, "log": log_path,
                  "watcher_pid": wproc.pid, "watcher_armed_at": time.time()}
        _sp.WORKSPACE_INDEX.write_text(json.dumps(d, indent=2, ensure_ascii=False))
        print(f"[watch] issue-{issue}/{rearm_skill}: 워처 재무장 pid {wproc.pid} "
              f"(로그 {watcher_log})", file=sys.stderr)
        return 0


def _watch_all(stall_timeout_min: float, until_idle: bool = False) -> int:
    """`spawn.py watch --all --follow` — 이슈 #488 요구 (2): 워크스페이스
    인덱스 전체를 다중화해 하나의 장수명 호출로 스트리밍한다. 매 반복마다
    인덱스를 다시 읽으므로, 이 호출이 시작된 *뒤*에 등록된 스폰도 잡힌다
    (auto-arm 이 개별 워처를 이미 세우지만, 이건 그 전체를 한 화면에서
    보는 오케스트레이터용 집계 뷰다). SIGINT/SIGTERM 으로 끊길 때까지 돈다.

    이슈 #559: `until_idle=True` 면 매 전체 패스가 끝날 때마다 인덱스의
    모든 키가 이미 `seen_end` 에 있는지(빈 인덱스도 idle로 친다) 확인해,
    맞으면 자며 다시 돌지 않고 0으로 리턴한다 — `--follow` 없이 영원히
    블록하던 오케스트레이터 대기 문제(#559 "Additional finding")에 대한
    응답. `_watch`(단수)가 `session-end` 를 종료의 유일한 신호로 삼는
    정의를 그대로 재사용한다(프로세스 생존은 부차 신호일 뿐이라는 이유는
    `_watch` 쪽 주석 참고).
    """
    seen_end: set[str] = set()
    poll_s = 0.2
    try:
        while True:
            idx = _sp._workspace_index_load()
            for key, entry in sorted(idx.items()):
                if key in seen_end:
                    continue
                work = entry.get("work")
                log_path = Path(entry["log"]) if entry.get("log") else None
                if not work or log_path is None:
                    continue
                events_path = _sp._events_path(work)
                offset_path = _sp._offset_path(work)
                seen = _sp._read_offset(offset_path)
                if not events_path.exists():
                    continue
                lines = events_path.read_text(encoding="utf-8").splitlines()
                while len(lines) > seen:
                    ev = json.loads(lines[seen])
                    seen += 1
                    _sp._write_offset(offset_path, seen)
                    print(f"[watch-all] {key} {ev['type']}: {ev['detail']}")
                    if ev["type"] == "session-end":
                        seen_end.add(key)
                        break
            if until_idle and all(key in seen_end for key in idx):
                return 0
            time.sleep(poll_s)
    except KeyboardInterrupt:
        return 0
