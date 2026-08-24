"""Spawn pipeline machinery (settings/rulebook/core resolution, spawn_cmd,
issue workspace + checkout/bootstrap, directive-assembly helpers, admission)

Extracted from spawn.py (issue #2105, extraction 8/N, endgame). Pure move —
no behavior change. spawn.py imports this module and re-exports every moved
name, so external callers and tests keep addressing them as `spawn.<name>`.

Patching-compat mechanism (copied from relay.py/roster.py/plumbing.py/
watchdog.py/events.py/consult.py/skills.py/lifecycle.py, extractions 1-7):
every cross-function reference here resolves at call time through `_sp` —
the spawn module object, injected by spawn.py right after it imports this
module (guarded so only the canonical spawn/__main__ module binds it), so
`mock.patch.object(spawn, "<name>")` patches stay visible to the moved
code. Cluster-internal cross-function calls also go through `_sp`.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import contextlib
import fcntl
import hashlib
import io
import json
import math
import os
import re
import shutil
import signal
import stat
import string
import subprocess
import sys
import tempfile
import time
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# The spawn module object; set by spawn.py on import. All cross-module lookups
# resolve through it at call time so monkeypatches on spawn attributes are seen.
_sp = None

@contextlib.contextmanager
def _timed(phase: str):
    """부트스트랩 단계 하나의 소요 시간을 `_BOOTSTRAP_TIMING`에 누적한다
    (이슈 #711) — `_spawn_one` 제어 흐름·종료 코드는 그대로, 측정만 덧붙인다."""
    t0 = time.monotonic()
    try:
        yield
    finally:
        _sp._BOOTSTRAP_TIMING[phase] = _sp._BOOTSTRAP_TIMING.get(phase, 0.0) + (time.monotonic() - t0)


def _bootstrap_timing_line(role: str) -> str:
    parts = [f"{p}={_sp._BOOTSTRAP_TIMING.get(p, 0.0):.3f}" for p in _sp._BOOTSTRAP_PHASES]
    total = sum(_sp._BOOTSTRAP_TIMING.get(p, 0.0) for p in _sp._BOOTSTRAP_PHASES)
    parts.append(f"total={total:.3f}")
    return f"[{role}] bootstrap_timing " + " ".join(parts)


def _rulebook_ttl_min() -> float:
    v = os.environ.get("MUSTER_RULEBOOK_TTL")
    if v is None:
        return 15.0
    try:
        return float(v)
    except ValueError:
        return 15.0


def _ttl_marker(d: Path) -> Path:
    """클론 밖, `runs/` 아래 마커를 둔다(이슈 #296) — 클론 안에 두면
    untracked 파일이 남아 `git status --porcelain` 이 영영 비지 않고,
    그 결과 `(커밋 안 된 변경 있음)`/`+커밋안됨` 이 모든 클론에 상시로 붙는다."""
    key = hashlib.sha256(str(d.resolve()).encode()).hexdigest()[:16]
    return _sp.ROOT / "runs" / "ttl-markers" / key


def _pull_is_fresh(d: Path) -> bool:
    """TTL 창 안이면 True — 이번엔 `git pull` 을 건너뛴다(이슈 #285 P4).
    `MUSTER_RULEBOOK_TTL=0` 이면 항상 False(매번 pull, 오늘의 동작)."""
    ttl_min = _sp._rulebook_ttl_min()
    if ttl_min <= 0:
        return False
    m = _sp._ttl_marker(d)
    try:
        age_s = time.time() - m.stat().st_mtime
    except OSError:
        return False
    return age_s < ttl_min * 60


def _mark_pulled(d: Path) -> None:
    try:
        marker = _sp._ttl_marker(d)
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(str(time.time()))
    except OSError:
        pass


def _migrate_legacy_ttl_marker(d: Path) -> None:
    """이슈 #313: #297 은 새 마커를 쓸 곳만 `runs/ttl-markers/` 로
    옮겼다 — pre-#297 코드가 클론 안에 이미 써 둔 `.muster-last-pull` 은
    그대로 남아, 지우기 전까진 `git status --porcelain` 이 영영 비지
    않는다(untracked, gitignore 안 됨). 그 결과 `checkout_version()` 의
    dirty 접미사가 그 클론에 매 spawn 마다 상시로 붙는다. 매번 확인해서
    지운다 — 있으면 지우고 없으면 조용히 넘어간다(그 자체로 멱등)."""
    legacy = d / ".muster-last-pull"
    try:
        legacy.unlink()
    except OSError:
        pass


def _mkt(d: Path) -> Path:
    return d / ".claude-plugin" / "marketplace.json"


def _rulebook_lock_path(d: Path) -> Path:
    """`d` 옆에 두는 락 파일 경로 — 클론 디렉터리 안이 아니라 형제
    (`git status --porcelain` 을 깨끗하게 유지, #296 의 TTL 마커와 같은 이유)."""
    return d.parent / (d.name + ".lock")


@contextlib.contextmanager
def _locked_rulebook_dir(d: Path):
    """`d` 를 채우는(clone/pull) 구간을 프로세스 간에 직렬화한다. `ROSTER` 의
    lock 패턴(spawn.py:1732-1739)과 동일한 `fcntl.flock` 관용구 — 커널이
    보유 프로세스가 죽으면 자동으로 lock 을 푼다, 그래서 별도 stale-lock
    회수 코드가 필요 없다(issue #773)."""
    lock_path = _sp._rulebook_lock_path(d)
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        f = open(lock_path, "w")
    except OSError:
        # 부모 디렉터리를 만들거나 락 파일을 열 수 없다(예: 읽기 전용
        # 루트) — 락 없이 진행한다. 아래 clone/pull 자체가 곧 같은 이유로
        # 실패해 fail-closed 로 떨어진다.
        yield
        return
    with f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def self_hosted_hooks(cwd: str) -> dict | None:
    """스폰 대상이 on-the-record 자기 자신이면 그 hooks.json 의 "hooks" 값을,
    아니면 None 을 돌려준다(이슈 #508).

    자기 자신 판정은 `<cwd>/on-the-record/hooks/hooks.json` 존재 여부다 — 이
    저장소는 플러그인 매니페스트를 `on-the-record/` 서브디렉터리에 담고
    있고, 자기 자신을 스폰 대상으로 삼을 때만 그 경로가 cwd 아래 나타난다.
    체크인된 `.claude/settings.json` 을 쓰지 않는 이유는
    `require_no_repo_config`(스폰이 임의 대상 레포에 대해 도는 별도 검사)와
    충돌하기 때문 — 여기서 --settings 임시 파일에 병합해 넣으면 그 검사를
    아예 건드리지 않는다.

    `${CLAUDE_PLUGIN_ROOT}` 는 컨슈머 설치 경로에서는 Claude CLI 가
    `--plugin-dir` 로 채우지만, 여기서는 그 경로로 로드하지 않으므로 직접
    치환한다 — on-the-record 레포 안의 플러그인 루트로.
    """
    root = Path(cwd).resolve()
    hooks_path = root / "on-the-record" / "hooks" / "hooks.json"
    if not hooks_path.is_file():
        return None
    try:
        raw = hooks_path.read_text()
    except OSError as e:
        print(f"self_hosted_hooks: {hooks_path} 를 못 읽어 훅 주입을 건너뛴다: {e}",
              file=sys.stderr)
        return None
    plugin_root = str(hooks_path.parent.parent)
    text = raw.replace("${CLAUDE_PLUGIN_ROOT}", plugin_root)
    try:
        parsed = json.loads(text)
    except ValueError as e:
        # 여기서 조용히 None 을 돌려주면 self-hosted 세션이 훅 없이 정상
        # 종료처럼 보인다 — 깨진 hooks.json 이 "가드가 다 붙었다"로 오독되는
        # 케이스다(실측: before-landing hunt, issue #508).
        print(f"self_hosted_hooks: {hooks_path} 파싱 실패, 훅 주입을 건너뛴다: {e}",
              file=sys.stderr)
        return None
    return parsed.get("hooks")


def _workspace_bash_allow(cwd: str) -> list[str]:
    """이슈 #558: 이 스폰의 격리된 워크스페이스(cwd) 안에서 정당한 venv
    생성/pip install/워크스페이스 test/ 스크립트 실행을 스폰 시점에 미리
    허용한다. `Bash(cd {cwd}*)` 처럼 `cd` 뒤에 트레일링 와일드카드만 붙이면
    `cd {cwd} && rm -rf ~` 같은 임의 셸까지 통과한다 — after-proposal
    warrant-hunt(stance 0)가 잡아낸 실패 모양이라, 각 항목은 `cd` 뒤에 올
    명령 자체까지 구체적으로 명시한다. `cwd` 는 *어디*를, 나머지 패턴은
    *무엇*을 좁힌다 — 이 스폰과 다른 cwd 를 받은 스폰은 다른 문자열을
    받는다."""
    venv = f"{cwd}/venv"
    return [
        f"Bash(cd {cwd} && python3 -m venv venv)",
        f"Bash(python3 -m venv {venv})",
        f"Bash(cd {cwd} && {venv}/bin/pip install *)",
        f"Bash({venv}/bin/pip install *)",
        f"Bash(cd {cwd} && python3 test/*.py)",
        f"Bash(cd {cwd} && {venv}/bin/python3 test/*.py)",
    ]


def role_settings(role: str, cwd: str | None = None,
                   inject_self_hosted_hooks: bool = True) -> dict:
    """역할의 샌드박스 경계 + 전역 플러그인 차단.

    **룰북을 켜는 일은 여기서 하지 않는다.** 그건 `--plugin-dir` 이 한다
    (plugin_dirs 참고). 설정으로 켜려면 마켓플레이스를 등록하고 설치해야
    하는데, 그 경로에는 조용한 함정이 셋 있고 전부 "의도한 것과 다른 커밋이
    붙는다"로 끝난다.

    남는 일은 두 가지다: 역할이 선언한 샌드박스를 펼치는 것, 그리고 사용자
    전역 플러그인을 빠짐없이 끄는 것. 후자는 `--settings` 가 교체가 아니라
    **병합**이라 필요하다 — 안 끄면 qa 룰북만 적은 세션에 전역 17개가 딸려
    온다.
    """
    f = _sp.ROOT / "roles" / f"{role}.json"
    if not f.exists():
        have = ", ".join(sorted(p.stem for p in (_sp.ROOT / "roles").glob("*.json")))
        sys.exit(f"모르는 역할: {role}  (있는 것: {have})")
    spec = json.loads(f.read_text())

    s = {k: v for k, v in spec.items() if k not in ("marketplace", "path", "repo")}

    # 역할 파일의 env 는 **기본값**이지 강제가 아니다. 이미 환경에 있으면 그쪽이 이긴다 —
    # 안 그러면 bench 처럼 격리된 워크스페이스를 넘기려는 호출이 조용히 무시되고,
    # 실행이 실제 워크스페이스에 쓰게 된다(실제로 그렇게 오염시켰다).
    # 역할 파일이 기본값으로 적은 값 자체에도 `~` 와 `$VAR` 가 들어갈 수 있다 —
    # 절대경로를 박지 않으려면 그래야 한다. 여기서 먼저 펴지 않으면 아래의
    # safe_substitute 는 한 번만 도므로 `$QA_WORKSPACE` → `$HOME/...` 로 끝나고,
    # 안 풀린 `$` 때문에 역할이 아예 안 뜬다(실측 2026-07-27: qa 가 그랬다).
    for k in list(s.get("env", {})):
        if k in os.environ:
            s["env"][k] = os.environ[k]
        else:
            v = s["env"][k]
            if isinstance(v, str):
                s["env"][k] = os.path.expanduser(os.path.expandvars(v))

    # 샌드박스 경로는 그 env 를 **참조**해야 한다. 같은 값을 두 곳에 적으면 위의
    # 덮어쓰기가 조용히 무력화된다 — env 는 격리된 경로를 가리키는데 경계는 원래
    # 경로만 허용하는 상태가 되고, 그건 "격리했다고 믿는 오염"이다.
    # 해석된 env 를 기준으로 펼친다: 역할 파일이 선언했지만 os.environ 에 없는
    # 값도 있고, 환경이 이긴 값도 여기 이미 반영돼 있다.
    resolved = {**os.environ, **s.get("env", {})}
    fs = s.get("sandbox", {}).get("filesystem", {})
    for key in ("allowWrite", "denyWrite", "denyRead"):
        if key in fs:
            fs[key] = [string.Template(p).safe_substitute(resolved) for p in fs[key]]
            unresolved = [p for p in fs[key] if "$" in p]
            if unresolved:
                # 안 풀린 변수를 그대로 넘기면 경계가 존재하지 않는 경로를 가리킨다.
                sys.exit(f"[{role}] sandbox.filesystem.{key} 의 변수를 풀 수 없다: "
                         f"{', '.join(unresolved)}")

    # 이슈 #695: 롤-세션 샌드박스를 role_settings() 가 중앙에서 끈다.
    # roles/*.json 이 어떤 sandbox.enabled 값을 선언하든 여기서 무조건
    # 거짓으로 강제한다 — 반복된 차단 버그(#38/#58/#65/#72/#153, 2026-08-11
    # tas 리포트)의 비용이 경계의 보호 가치를 넘어섰다는 운영자 결정.
    # 이 결과로 예전에 여기 있던 레지스트리/웹 도메인 병합(#38/#58),
    # 기본값 스위치 개방(#72), 패키지 캐시 allowRead 마운트(#38)는 전부
    # 도달 불가능해져 issue-695 에서 함께 제거했다.
    if "sandbox" in s:
        s["sandbox"]["enabled"] = False

    # 전역 플러그인은 전부 끈다. 켜야 할 것을 적는 게 아니라 꺼야 할 것을
    # 빠짐없이 적는 쪽이라, 전역에 플러그인이 새로 깔려도 새지 않는다.
    s["enabledPlugins"] = {}
    try:
        globals_ = json.loads(_sp.USER_SETTINGS.read_text()).get("enabledPlugins", {})
    except (OSError, ValueError):
        globals_ = {}
    for name in globals_:
        s.setdefault("enabledPlugins", {}).setdefault(name, False)

    # 갱신 — 이슈 #742 (2026-08-11): 아래 세 문단(WebSearch/WebFetch/Read/
    # Grep/Glob, 워크스페이스-bash 패턴, MUSTER_MCP_ALLOW)이 서술하는
    # "permissions.allow 에 규칙이 없으면 거부된다" 는 판정 근거는 #58/#65/
    # #153/#558 당시(headless 세션이 --permission-mode acceptEdits 로 떴던
    # 시절)의 것이다. #700(커밋 b762681, 2026-08-11 10:38)이 실제 롤 스폰
    # 경로(spawn_cmd()/consult_cmd())를 --permission-mode bypassPermissions
    # 로 옮긴 뒤로는 이 permissions.allow 목록 전체가 그 경로들에서 더 이상
    # 판정에 관여하지 않는다 — Anthropic 문서
    # (code.claude.com/docs/en/permission-modes): "Allow rules have no
    # effect in bypassPermissions because everything else is already
    # approved." 이슈-742 phase-1 조사가 이 사실을 4패턴 라이브 프로브로
    # 실측했다(거부 0건). bypassPermissions 아래서 도구 호출을 실제로
    # 판정하는 층은 PreToolUse/PermissionRequest 훅뿐이다.
    #
    # 그런데도 목록을 지우지 않는 이유 둘: (1) role_settings() 는
    # `--dry-run` 경로(main() 의 a.dry_run 분기)에서도 호출되는데 그
    # 경로는 claude 프로세스를 아예 안 띄우므로 permission-mode 자체가
    # 없다 — 거기 출력되는 permissions.allow 는 이 함수가 만드는 그대로다;
    # (2) 롤 스폰이 bypassPermissions 아닌 모드로 되돌아가면(#700 이전
    # 상태) 이 목록이 그 즉시 다시 유효한 경계가 된다 — 지금 지우면 그
    # 되돌림이 이 항목들 없이 조용히 일어난다.
    #
    # WebSearch/WebFetch 는 두 층에서 막힌다(이슈 #65, #58 후속). #58 은 샌드박스
    # NETWORK 층(allowedDomains)만 열었다 — TOOL-PERMISSION 층은 별개로, (당시)
    # headless 세션은 --permission-mode acceptEdits 로 뜨고 답할 사람이 없어서
    # permissions.allow 에 규칙이 없는 도구는 그냥 거부됐다(#58 조사가 놓친 지점).
    # 모든 역할에 적용한다(#58 과 동일한 operator 결정: option B) — 샌드박스
    # 활성 여부와 무관하다, 이 층은 샌드박스가 아니라 CLI 권한 프롬프트이므로.
    # Read/Grep/Glob 도 같은 이유로 추가한다(이슈 #153) — 읽기 전용 조회이고
    # 도달 가능한 경로는 여전히 sandbox.filesystem.allowRead/denyRead 가 정한다;
    # 이 층은 그 경계를 넓히지 않는다. Bash 하위 패턴은 "읽기 전용"으로 안전하게
    # 한정할 수 없어 제외한다(survey 3절).
    allow = s.setdefault("permissions", {}).setdefault("allow", [])
    for tool in ("WebSearch", "WebFetch", "Read", "Grep", "Glob"):
        if tool not in allow:
            allow.append(tool)

    # 이슈 #558: 격리된 워크스페이스(cwd) 안에서 정당한 venv 생성/pip
    # install/워크스페이스 test/ 스크립트 실행은 하네스 권한(2층)에 막혔다
    # (당시) — headless 세션은 답할 사람이 없어 permissions.allow 에 없는
    # 명령은 그냥 거부됐다(2026-08-09 soongsil-course-registration 런
    # 실측; 위 갱신 문단 참고 — #700 이후 실제 롤 스폰에는 더 안 해당). 위의
    # Bash 하위 패턴 제외 사유(바로 위 주석)는 "경로 앵커 없는" 패턴에만
    # 해당한다 — 여기 항목은 이 스폰의 cwd 로 완전히 앵커링되므로 별개다.
    # cwd 가 없으면(레지스트리 점검 등 워크스페이스 없는 호출) 아무것도
    # 추가하지 않는다.
    if cwd is not None:
        for pattern in _sp._workspace_bash_allow(cwd):
            if pattern not in allow:
                allow.append(pattern)

    # MUSTER_MCP_ALLOW: 같은 TOOL-PERMISSION 층 결함이 사용자가 직접 붙인
    # MCP 서버에도 그대로 있다 — 서버 연결은 되는데(`mcp_servers` 에
    # "connected" 로 뜬다) 도구 호출은 permissions.allow 에 규칙이 없어
    # #58/#65 와 똑같이 거부된다(실측: reasona issue-3, world-data MCP).
    # #58/#65 와 다른 점은 대상이 tokenmaxxxer 가 아는 고정 도구가 아니라
    # **사용자마다 다른 이름의 개인 MCP 서버**라는 것 — 코드에 이름을 박을
    # 수 없다. 그래서 운영자가 스폰 시점에 콤마로 나열한다
    # (MUSTER_ROLE_MODEL/MUSTER_AGENT_GH_TOKEN/MUSTER_WORK_DIR 와 같은
    # 환경변수 관례). 빈 문자열/공백뿐인 항목은 미설정과 동일하게 버린다.
    #
    # `mcp__` 접두사만 받는다 — 이 통로는 MCP 도구 permission 층의 구멍을
    # 메우는 것이 유일한 목적이고, Write/Edit/Bash 처럼 board-gate/
    # approval-gate 가 지키는 도구까지 여는 우회로가 되면 안 된다. 접두사가
    # 안 맞는 항목은 조용히 버린다 — 운영자가 실수로 `MUSTER_MCP_ALLOW=Bash`
    # 를 넣어도 게이트가 지키는 표면은 넓어지지 않는다.
    extra_mcp = [t.strip() for t in os.environ.get("MUSTER_MCP_ALLOW", "").split(",")
                 if t.strip().startswith("mcp__")]
    for tool in extra_mcp:
        if tool not in allow:
            allow.append(tool)

    # on-the-record 가 자기 자신을 대상으로 스폰할 때만, 자기 hooks.json 을
    # 병합해 넣는다 — 컨슈머 설치 경로 밖에서는 늘 inert 였다(이슈 #508).
    if cwd is not None and inject_self_hosted_hooks:
        injected = _sp.self_hosted_hooks(cwd)
        if injected:
            s["hooks"] = injected
    return s


def core_root() -> Path:
    """tokenmaxxxer-core 체크아웃 루트. 없으면 멈춘다.

    core 는 상호작용 프로토콜의 게이트(보드·승인·gh-guard)와 정본 계약을
    들고 있다. 없이 띄우면 역할은 그대로 돌지만 아무도 이탈을 막지 않는다 —
    조용히 보호가 사라지는 쪽이라 경고가 아니라 정지다.
    """
    for _label, cand in _sp._core_candidates():
        if not cand:
            continue
        p = Path(os.path.expanduser(os.path.expandvars(cand)))
        if "$" in str(p):
            continue
        if (p / "core" / ".claude-plugin" / "plugin.json").is_file():
            return p
    # 로컬 체크아웃이 없으면 룰북과 같은 길: on-the-record 소유 클론을 받아 쓴다.
    # 로컬 우선은 개발용 오버라이드일 뿐이다.
    d = _sp.ROOT / "runs" / "rulebooks" / "tokenmaxxxer-core"
    try:
        d.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    with _sp._locked_rulebook_dir(d):
        if (d / "core" / ".claude-plugin" / "plugin.json").is_file():
            _sp._migrate_legacy_ttl_marker(d)
            if not _sp._pull_is_fresh(d):
                _sp._run_net(["git", "-C", str(d), "pull", "-q", "--ff-only"], "[core] pull")
                _sp._mark_pulled(d)
            return d
        try:
            print("[core] tokenmaxxxer-core 를 받는 중", file=sys.stderr)
            _sp._run_net(["git", "clone", "-q",
                     "https://github.com/tokenmaxxxer/tokenmaxxxer-core.git",
                     str(d)], "[core] clone", timeout=_sp.CLONE_TIMEOUT)
            _sp._mark_pulled(d)
        except OSError:
            pass
        if (d / "core" / ".claude-plugin" / "plugin.json").is_file():
            return d
    sys.exit(
        "tokenmaxxxer-core 를 찾지 못했고 받지도 못했다. 역할 세션은 core 없이\n"
        "  뜨지 않는다 — 프로토콜 게이트와 정본 계약이 거기 있다.\n"
        "  네트워크를 확인하거나 체크아웃을 두고 $TOKENMAXXXER_CORE 로 가리켜라.")


def core_version() -> str:
    """core_root() 가 실제로 고를 체크아웃이 **무엇인지** — 읽기 전용, pull 도
    clone 도 하지 않는다. checkout_version() 의 core 쪽 대칭 — 로컬 오버라이드를
    건드리지 않으면서 무엇이 도는지만 매 spawn 로그·ledger 에 남긴다(이슈
    #218: 같은 sha 가 며칠째 안 바뀌어도 로그에 안 남아 stale 게이트로 계속
    돌았다).
    """
    def git(d: Path, *a: str) -> str:
        p = subprocess.run(["git", "-C", str(d), *a], capture_output=True, text=True)
        return p.stdout.strip() if p.returncode == 0 else ""

    def describe(d: Path, label: str) -> str:
        sha = git(d, "rev-parse", "--short", "HEAD") or "?"
        date = git(d, "log", "-1", "--format=%cs") or "?"
        dirty = " (커밋 안 된 변경 있음)" if git(d, "status", "--porcelain") else ""
        return f"{sha}{dirty} ({date}, {label})"

    for label, cand in _sp._core_candidates():
        if not cand:
            continue
        p = Path(os.path.expanduser(os.path.expandvars(cand)))
        if "$" in str(p):
            continue
        if (p / "core" / ".claude-plugin" / "plugin.json").is_file():
            return describe(p, label)
    d = _sp.ROOT / "runs" / "rulebooks" / "tokenmaxxxer-core"
    if (d / "core" / ".claude-plugin" / "plugin.json").is_file():
        _sp._migrate_legacy_ttl_marker(d)
        return describe(d, "on-the-record 클론")
    return "버전 불명 (core 체크아웃 없음)"


def core_plugin_dirs() -> list[Path]:
    """core 마켓플레이스가 선언한 플러그인 전부 — marketplace.json 이 정본이다.

    마켓플레이스 설치가 아니라 `--plugin-dir` 로 붙인다(실측 2026-07-27,
    CLI 2.1.220: 디렉터리로 넘긴 플러그인의 훅이 headless 에서 그대로
    발화한다). 설치를 거치지 않으므로 캐시·클론 갈라짐도 유령 등록 항목도
    이 경로에는 없다.

    core 플러그인은 scope-gate·hunt-guard 같은 공유 강제 장치라 role 자체
    확장(plugin_dirs())과 달리 하나라도 빠지면 조용히 넘길 수 없다 — 선언은
    됐는데 디렉터리가 없으면 즉시 sys.exit (이슈 #282: 4개짜리 하드코드
    튜플이 marketplace.json 이 다섯 번째로 늘린 warrant 를 계속 빠뜨렸는데
    아무 신호도 없었다).
    """
    root = _sp.core_root()
    plugins = json.loads(_sp._mkt(root).read_text())["plugins"]
    out = []
    for p in plugins:
        src = p.get("source") or f"./{p['name']}"
        if not isinstance(src, str):
            continue                      # {source: github, ...} 같은 원격 지정 — core 는 항상 로컬
        sub = (root / src.lstrip("./")).resolve()
        if not (sub / ".claude-plugin" / "plugin.json").is_file():
            sys.exit(f"core 플러그인 '{p['name']}' 이 marketplace.json 에는 선언됐지만 "
                      f"{sub / '.claude-plugin' / 'plugin.json'} 이 없다 — 조용히 건너뛰지 않는다.")
        out.append(sub)
    return out


def _claude_version() -> str:
    try:
        out = subprocess.run(["claude", "--version"], capture_output=True,
                             text=True, timeout=30)
        return out.stdout.strip().splitlines()[0] if out.stdout.strip() else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def require_doctor(version: str | None = None) -> None:
    """이 CLI 버전에서 훅이 headless 로 도는 것을 doctor 가 실측했는지 본다.

    룰북 집행 전체가 '플러그인 훅이 -p 세션에서 돈다'는 한 문장 위에 서
    있는데, 그 문장은 공식 문서에 없다 — 실측(2026-07-27, 2.1.220)뿐이다.
    CLI 는 자동 업데이트되므로, 버전이 바뀌면 게이트 전부가 소리 없이
    사라질 수 있다. 그래서 버전마다 한 번, 실측을 다시 요구한다.
    """
    v = version if version is not None else _sp._claude_version()
    ok = _sp.ROOT / "runs" / "doctor-ok"
    if not v:
        sys.exit("claude --version 을 읽지 못했다. claude 가 PATH 에 있나?")
    if not ok.is_file() or ok.read_text().strip() != v:
        if version is not None:
            # 명시된 버전(테스트 포함)에는 프로브를 태우지 않는다 — 옛 계약
            # 그대로 정지한다.
            sys.exit(
                f"이 CLI({v})에서 훅이 headless 로 도는 것을 아직 실측하지 않았다.\n"
                f"먼저 돌려라: python3 spawn.py doctor   (실 세션 1회, 소액 과금)")
        # 미측정 버전이면 그 자리에서 잰다 — 사용자에게 명령 하나를 더
        # 요구할 이유가 없다. 프로브 세션 1회(하이쿠, 소액)가 돈다.
        print(f"[doctor] CLI {v} 는 아직 실측 전이다 — 훅 발화 프로브를 "
              f"먼저 돌린다 (실 세션 1회, 소액 과금)", file=sys.stderr)
        if _sp.doctor() != 0 or not (ok.is_file() and ok.read_text().strip() == v):
            sys.exit(
                f"이 CLI({v})에서 플러그인 훅이 headless 로 발화하지 않는다 — "
                f"게이트 전부가 조용히 사라지는 버전이라 스폰을 막는다.")


def read_role_model_config() -> str:
    """이슈#60: repo-root role_model.txt 에서 기본 모델 값을 읽는다. 파일이
    없거나 읽기 오류가 나면 미설정과 동일하게 "" 를 돌려준다."""
    try:
        return _sp.ROLE_MODEL_CONFIG.read_text().strip()
    except (OSError, UnicodeDecodeError):
        return ""


def resolved_role_model(cli_model: str | None = None, role: str | None = None,
                         single_phase: bool = False,
                         design_bearing_verdict: bool | None = None) -> tuple[str, str] | str:
    """이슈#93: env > config > built-in default("sonnet"). MUSTER_ROLE_MODEL 이
    (strip 후) 비어 있지 않으면 그것이 이긴다 — config 는 그때는 아예 안 읽힌
    값처럼 무시된다. 둘 다 비어 있으면 "sonnet" — --model 이 항상 붙는다,
    호출자의(비쌀 수 있는) 세션 모델을 조용히 물려받지 않도록.

    이슈#1736: `cli_model` 이(strip 후) 비어 있지 않으면 최우선으로 이긴다
    — 단일 스폰에 대한 per-invocation 오버라이드, env/config 는 아예 안
    읽힌 것처럼 건너뛴다. 생략하면(기본값 None) 이전 동작과 byte-identical.

    이슈#2070: `role` 이 주어지면(기존 세 rung 이 전부 비었을 때만) built-in
    `"sonnet"` 종착점 대신 `gates/model_routing.py`의 구조적 라우팅 계층을
    태운다 — `--model` 과 `MUSTER_ROLE_MODEL`/`role_model.txt` 는 그대로
    최우선으로 이긴다(회귀 없음). 반환값은 (model, rule) 튜플로 바뀌지만
    `role` 을 생략하면(기본값 None) 이전 세 rung 은 그대로이고 반환값도
    문자열 하나 그대로다 — byte-identical."""
    cli_value = (cli_model or "").strip()
    if cli_value:
        return (cli_value, "cli-override") if role is not None else cli_value
    env_value = (os.environ.get("MUSTER_ROLE_MODEL") or "").strip()
    if env_value:
        return (env_value, "env-override") if role is not None else env_value
    config_value = _sp.read_role_model_config()
    if config_value:
        return (config_value, "config-override") if role is not None else config_value
    if role is not None:
        sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
        import model_routing
        policy = model_routing.load_policy(_sp.ROOT)
        return model_routing.route_model(role, single_phase, design_bearing_verdict, policy)
    return "sonnet"


def spawn_cmd(settings_path: str, role: str, unattended: bool,
              core_plugins: list | None = None,
              plugins: list | None = None,
              model: str | None = None,
              skill_dirs: list | None = None,
              skill_repo_sha_value: str | None = None,
              single_phase: bool = False,
              design_bearing_verdict: bool | None = None,
              max_turns: int | None = None) -> tuple[list[str], dict[str, str]]:
    """세션 argv 와 env **추가분**. 호출자가 os.environ 위에 얹는다.

    --permission-mode bypassPermissions (issue #700): 샌드박스 제거(#695/#697)
    이후 모든 Bash 가 승인 분류기 앞에 서는데 headless 는 답할 사람이 없어
    allowlist 밖 명령이 전부 죽는다(실측 2026-08-11: issue-698 세션이
    `git add`/`gh issue view` 에서 failed-no-commit). 운영자 결정으로
    bypassPermissions 가 기본값이다 — 집행은 훅(PreToolUse exit 2)이 계속
    맡고, bypassPermissions 는 훅을 끄지 않는다(#697 이전의 acceptEdits
    실측과 동일 근거).

    TOKENMAXXXER_SPAWNED: 스폰된 세션의 프롬프트는 오케스트레이터가 쓴
    텍스트이지 사람 턴이 아니다. core 의 mint 훅이 이 도장을 보고 발행을
    거른다. UNATTENDED 와 별개다 — 그쪽은 "사람이 없다"는 사실이고, 겹쳐
    쓰면 attended 스폰이 깨진다.
    """
    cmd = ["claude", "-p", "--settings", settings_path,
           "--permission-mode", "bypassPermissions",
           "--output-format", "stream-json", "--verbose"]
    # Issue #2135 (measured composition): a role session inheriting the
    # operator's USER-scope settings mounts the operator's entire personal
    # skill registry (273 skills / ~410KB of trigger descriptions on the
    # measured machine) into its standing system prompt — the dominant
    # share of the ~55K-token session-start context, none of it addressed
    # to the role (role skills mount explicitly via --plugin-dir above).
    # Restrict setting sources to the target project. Everything the role
    # session needs rides on explicit flags: --settings (generated file),
    # --plugin-dir (core + role skills), --model, env (GH_TOKEN, CLAUDE_ROLE).
    # Kill switch / override: MUSTER_SETTING_SOURCES ("user,project,local"
    # restores the old behavior; empty string omits the flag entirely).
    setting_sources = os.environ.get("MUSTER_SETTING_SOURCES",
                                     "project,local")
    if setting_sources:
        cmd += ["--setting-sources", setting_sources]
    # Issue #2100 item 4: session turn budget pass-through. `None` keeps
    # today's argv byte-identical (callers that never resolved a budget);
    # `_spawn_one` always passes the resolved cap. <= 0 means an explicit,
    # admission-approved unlimited run — no flag is attached.
    if max_turns is not None and max_turns > 0:
        cmd += ["--max-turns", str(max_turns)]
    # 룰북도 core 와 같은 길로 붙는다 — 디렉터리로 넘긴 플러그인의 훅은
    # headless 에서 그대로 발화하고(실측 2026-07-27, CLI 2.1.220), 설치를
    # 안 거치므로 캐시-클론 갈라짐도 유령 등록 항목도 이 경로엔 없다.
    for p in (plugins or []):
        cmd += ["--plugin-dir", str(p)]
    for p in (core_plugins or []):
        cmd += ["--plugin-dir", str(p)]
    # 이슈 #1742: --skills 로 마운트한 스킬 디렉터리. rulebook/core 뒤에
    # 붙는다 — 순서는 우선순위가 아니라 추가분(additive)이라 어디 붙어도
    # 무방하지만, skill_dirs 가 falsy 면(기본값) 이 루프가 아무 것도 안 붙여
    # no-flag 경로의 argv 를 바이트 단위로 그대로 둔다.
    for p in (skill_dirs or []):
        cmd += ["--plugin-dir", str(p)]
    # MUSTER_ROLE_MODEL / role_model.txt (이슈#93): 역할 세션이 쓰는 모델을
    # 고정한다. env > config > built-in "sonnet". 둘 다 비어있어도 built-in
    # 이 이겨 --model 이 항상 붙는다 — haiku 프로브(doctor())는 이 함수를
    # 거치지 않으므로 영향 없다.
    role_model, model_rule = _sp.resolved_role_model(
        model, role=role, single_phase=single_phase,
        design_bearing_verdict=design_bearing_verdict)
    if role_model:
        cmd += ["--model", role_model]
    env = {"CLAUDE_ROLE": role, "TOKENMAXXXER_SPAWNED": "1",
           # 이슈 #2070: roster 기록용 — `_spawn_one()` 이 실제 subprocess env
           # 로 넘기기 전에 이 두 내부 키를 꺼내 roster 엔트리에 옮겨 담는다.
           "_MODEL_ROUTING_MODEL": role_model or "",
           "_MODEL_ROUTING_RULE": model_rule}
    # Two-account model (core README): role sessions act as the AGENT
    # account. MUSTER_AGENT_GH_TOKEN, if set, becomes the session's GH_TOKEN
    # so gh in the container/sandbox authenticates as the agent — never the
    # user. gh-guard denies the human's acts in role sessions regardless.
    # 샌드박스 안에서는 macOS 키링이 안 보여 gh 토큰이 무효로 읽힌다(실측).
    # 그래서 토큰을 env 로 명시 주입한다: 에이전트 토큰이 있으면 그것,
    # 없으면(1계정 기본) 사용자의 gh 토큰을 꺼내 넘긴다. gh-guard 가
    # 역할 세션의 사람-행위 명령은 어차피 막는다.
    # `_resolve_gh_token()` 과 로직을 공유한다(중복 제거, 이슈 발견:
    # 오케스트레이터 자신의 git 호출은 이 로직이 없어서 인증 없이 돌았다) —
    # 캐시도 공유해서, 이 스폰에서 `_fetch_or_halt()` 가 먼저 불렸다면
    # `gh auth token` 을 또 shell-out 하지 않는다.
    agent_token = _sp._resolve_gh_token()
    if agent_token:
        env["GH_TOKEN"] = agent_token
        env["GIT_TERMINAL_PROMPT"] = "0"
    if unattended:
        env["TOKENMAXXXER_UNATTENDED"] = "1"
    if skill_dirs:
        env["MUSTER_SKILLS"] = ",".join(Path(p).name for p in skill_dirs)
        env["MUSTER_SKILL_REPO_SHA"] = skill_repo_sha_value or "?"
    # 룰북 게이트는 core 공유 라이브러리를
    # ${CLAUDE_PLUGIN_ROOT_CORE:-<상대경로>/core} 로 참조한다(이슈#182). 이
    # 변수를 주입하지 않으면 상대 fallback 이 룰북 클론 내부를 가리켜
    # 실배포에서 해석 실패 → 무가드 source 와 결합 시 게이트 전면
    # fail-open. core_plugins 는 core_plugin_dirs() 가 이미 해결해
    # --plugin-dir 로 넘기는 그 경로이므로, 여기서 재사용하면 "주입된
    # 경로 == 실제 로드된 core 플러그인 경로" 불변식이 코드 구조로
    # 보장된다.
    core_dir = next((p for p in (core_plugins or []) if Path(p).name == "core"), None)
    if core_dir:
        env["CLAUDE_PLUGIN_ROOT_CORE"] = str(core_dir)
    else:
        print("spawn_cmd: core_plugins 에 'core' 엔트리가 없다 — "
              "CLAUDE_PLUGIN_ROOT_CORE 미주입, 게이트가 fallback 경로로 "
              "빠질 수 있다", file=sys.stderr)
    return cmd, env


def ensure_target_remote(cwd: str, unattended: bool) -> None:
    """`origin` 원격 유무를 역할 스폰 전에 정리한다(이슈 #831).

    #830 실측: 헤드리스 top-level 세션이 `--issue` 없는 첫 스폰은 통과하고
    (issue_workspace 를 안 거치므로), 실제 작업을 시키는 두 번째 `--issue`
    스폰에서야 `issue_workspace`(4303행)의 무조건 `sys.exit` 에 걸렸다 —
    사람이 답할 수 없는 프로세스 안에서 사람에게 묻는 모양(req#5 FAIL).
    이 게이트를 `main()` 스폰 분기 앞으로 당겨, 그 질문이 원래
    `docs/handbooks/setup.md` 가 문서화한 대로 사람이 실제로 있는
    top-level 대화에서만 나오게 한다. `docs/issue-831/decisions/
    2026-08-11-setup-preflight-remote-gate.md` 의 결정을 그대로 구현한다.
    """
    r = subprocess.run(["git", "-C", cwd, "remote", "get-url", "origin"],
                       capture_output=True, text=True)
    if r.stdout.strip():
        return
    fail_msg = (f"대상 레포에 origin 원격이 없다: {cwd} — 이슈/PR 모델은 "
                f"GitHub 원격이 전제다 (계약 v3 s10). 최초 1회, attended "
                f"세션(--unattended 없이)에서 먼저 설정하라.")
    if unattended:
        sys.exit(fail_msg)
    print("대상 레포에 GitHub 원격(origin)이 없다. 최초 1회 설정이 필요하다:\n"
          "  y  — gh repo create --private --source . --push 로 새로 만든다\n"
          "  <기존 원격 URL>  — 그 원격을 origin 으로 붙인다\n"
          "  (그 외 입력/빈 입력)  — 거절, 아무것도 안 한다")
    answer = input("설정할까? [y/<URL>/N]: ").strip()
    if answer.lower() == "y":
        subprocess.run(["gh", "repo", "create", "--private", "--source", cwd,
                        "--push"], cwd=cwd, check=True)
    elif answer:
        subprocess.run(["git", "-C", cwd, "remote", "add", "origin", answer],
                       check=True)
    else:
        sys.exit(fail_msg)
    r = subprocess.run(["git", "-C", cwd, "remote", "get-url", "origin"],
                       capture_output=True, text=True)
    origin = r.stdout.strip()
    if not origin:
        sys.exit(fail_msg)
    _sp.ledger_write({"event": "remote_setup_confirmed", "cwd": str(Path(cwd).resolve()),
                  "origin": origin, "ts": int(time.time())})


def positive_int(s: str) -> int:
    """argparse type=: `--issue` 는 1 이상만 유효하다 — 0/음수/거대정수는
    존재할 수 없는 이슈 번호이므로 파싱 시점에 바로 거부한다(#288 N3)."""
    v = int(s)
    if v < 1:
        raise argparse.ArgumentTypeError(f"양의 정수가 아니다: {s}")
    return v


def bootstrap_fetch_and_record_sha(work_dir: str,
                                    label: str = "부트스트랩 fetch") -> dict:
    """이슈 #1507 — 세션의 첫 verification/absence-claim 단계보다 먼저
    `git fetch --prune`으로 origin 을 갱신하고 origin/main(또는 origin/HEAD
    가 가리키는 기본 브랜치) 의 sha 와 fetch 시각을 기록한다.

    `checkout_issue_branch()`가 부트스트랩 중 가장 먼저 이 함수를 부른다 —
    세션이 아직 아무 검증도 하지 않은 시점이다. fail-closed: fetch 가
    실패하면 `_fetch_or_halt`와 같은 house style 로 즉시 중단한다.

    반환값 `{"sha": <40자 hex>, "fetched_at": <ISO8601 UTC>}` 은
    `_BOOTSTRAP_FETCH_RECORD[work_dir]`에도 저장되어 이후
    `get_bootstrap_fetch_record()`로 조회할 수 있다 — 절대-부재 주장을
    쓰는 시점에 "verified against origin/main at <sha>, fetched
    <timestamp>" 문구를 채우는 근거가 된다(gates/repo_scope.py 확장)."""
    r = _sp._run_net(["git", "-C", work_dir, "fetch", "--prune", "-q", "origin"],
                label, env=_sp._git_env())
    if r.returncode != 0 or "failed to store" in r.stderr:
        sys.exit(f"{label}: fetch 실패 — {r.stderr.strip()[:200]}")
    base = _sp._base(work_dir)
    sha_r = subprocess.run(["git", "-C", work_dir, "rev-parse", base],
                           capture_output=True, text=True)
    sha = sha_r.stdout.strip() if sha_r.returncode == 0 else ""
    record = {"sha": sha, "fetched_at": datetime.now(timezone.utc).isoformat()}
    _sp._BOOTSTRAP_FETCH_RECORD[str(Path(work_dir).resolve())] = record
    return record


def get_bootstrap_fetch_record(work_dir: str) -> dict | None:
    """이슈 #1507 — `bootstrap_fetch_and_record_sha()`가 이 work_dir 에
    이미 남긴 기록을 조회한다. 없으면 None(아직 부트스트랩 fetch 전)."""
    return _sp._BOOTSTRAP_FETCH_RECORD.get(str(Path(work_dir).resolve()))


def _fetch_or_halt(work_dir: str, label: str, after=None) -> None:
    """fail-closed fetch. returncode 만 보면 놓치는 실패가 있다 — 실측:
    core issue-90 관찰 세션에서 `git fetch origin`이 stderr 에 "failed to
    store: 100001"을 남기고도 exit 0으로 끝났다. returncode != 0 이거나
    stderr 에 "failed to store"가 있으면 낡은 코드로 조용히 진행하는 대신
    중단한다(ensure_pushed 의 2380/2420 라인과 같은 house style).

    `after`(있으면)는 halt 여부 판정 **전에** 실행한다 — 신규 clone 직후의
    `remote set-head origin -a` 처럼, fetch 가 fail-closed 로 halt 하더라도
    반드시 시도돼야 하는 부수 효과가 있어서다. 순서를 반대로 하면(halt
    먼저) fetch 가 실패할 때마다 그 부수 효과가 영영 안 돌 수 있다 — 신규
    clone 경로 한정으로, `.git`은 이미 생겨 재사용 분기로 넘어가 버려 다시
    시도할 기회 자체가 없다(hunt 발견, composition-regression stance).

    같은 프로세스 안에서 같은 work_dir 을 이미 fetch 했으면 다시 네트워크로
    나가지 않는다(이슈 #285 P3 — `issue_workspace()` 다음의
    `checkout_issue_branch()` 가 수 초 뒤 같은 경로를 또 fetch 하던 것).
    최초 fetch 가 실패하면 이 함수가 바로 sys.exit 하므로 성공한 fetch만
    "fresh" 로 기록된다 — 두 번째 호출자가 halt 를 건너뛰는 일은 없다."""
    key = str(Path(work_dir).resolve())
    if key in _sp._FETCHED_THIS_SPAWN:
        if after is not None:
            after()
        return
    r = _sp._run_net(["git", "-C", work_dir, "fetch", "-q", "origin"], label,
                env=_sp._git_env())
    if after is not None:
        after()
    if r.returncode != 0 or "failed to store" in r.stderr:
        sys.exit(f"{label}: fetch 실패 — {r.stderr.strip()[:200]}")
    _sp._FETCHED_THIS_SPAWN[key] = time.monotonic()


def _write_role_sidecar(work: str, issue: int, role: str) -> None:
    """이슈 #1814: 워크스페이스 루트에 `.on-the-record/role.json` 을 남긴다 —
    네 개의 브랜치-정규식 사이트 중 셸 훅 세 곳(approval-gate.sh,
    pr-preflight.sh, contract-guard.sh)이 이미 로컬 `git rev-parse` 로
    풀던 워크스페이스에서 role 을 직접 읽게 하는 명시적 캐리어. 실패해도
    fail-open — 사이트들은 이 파일이 없으면 기존 브랜치-정규식 파싱으로
    그대로 떨어진다.

    이슈 #1891: 이 사이드카는 세션마다 바뀌는 워크스페이스-로컬 상태라
    git 이 절대 스테이징하면 안 된다 — issue #1882/PR #1890 에서 실제로
    커밋됐다가 머지 전에 걸러진 근접 사고. 스폰 시점에 워크스페이스의
    `.git/info/exclude` 에 추가한다(레포 `.gitignore` 는 건드리지 않는다).
    fresh-clone 경로의 자격증명 유출 방지 exclude 블록(issue_workspace()
    쪽)과 별개의 관심사라 여기서 직접 쓴다 — 호출부 3곳 모두를 한 곳에서
    커버한다."""
    d = Path(work) / ".on-the-record"
    try:
        d.mkdir(parents=True, exist_ok=True)
        (d / "role.json").write_text(
            json.dumps({"role": role, "issue": issue}) + "\n", encoding="utf-8")
        ex = Path(work) / ".git" / "info" / "exclude"
        ex.parent.mkdir(parents=True, exist_ok=True)
        existing = ex.read_text() if ex.exists() else ""
        if ".on-the-record/role.json" not in existing:
            with ex.open("a") as fh:
                fh.write(".on-the-record/role.json\n")
    except OSError as e:
        print(f"경고: {work} 에 role.json 사이드카를 쓰지 못했다 ({e})",
              file=sys.stderr)


def recut_if_absorbed_cli(cwd: str) -> int:
    """`spawn.py recut-if-absorbed -C <cwd>` — mid-run 세션이 자기 자신의
    브랜치를 재검사한다 (이슈 #784). 스폰 이후 이미 살아있는 세션은
    `checkout_issue_branch()`를 다시 부르지 않으므로, 그 세션이 떠 있는 동안
    orchestrator 가 phase-1 PR 을 `--delete-branch`로 머지하면 로컬 브랜치가
    base 에 흡수된 채로 조용히 남는다 — 다음 `git commit`/`gh pr create` 가
    "No commits between main and issue-<n>/<role>"로 실패하기 직전까지
    아무도 모른다. `absorbed-branch-recut-guard.sh`(PreToolUse/Bash)가 그
    커맨드들 직전에 이 함수를 호출한다.

    roster/cross-process 조회 없이 세션 자신의 현재 `HEAD` 에서 브랜치
    이름을 얻는다 — `issue-<n>/<role>` 모양이 아니면(분리 HEAD, 무관한
    브랜치 등) 아무 것도 안 하고 0 을 반환한다(오늘과 동일하게 fail-open).
    """
    br_r = subprocess.run(["git", "-C", cwd, "symbolic-ref", "--short", "-q", "HEAD"],
                          capture_output=True, text=True)
    br = br_r.stdout.strip()
    if br_r.returncode != 0 or not re.fullmatch(r"issue-\d+/[A-Za-z0-9_-]+", br):
        return 0
    # 흡수 여부 판단(local_zero/remote_ahead)이 최신 원격 상태를 봐야 하니
    # 이 브랜치와 base 만 갱신한다 — 실패해도(네트워크 등) 로컬 판단만으로
    # 진행하는 기존 fail-open 을 그대로 따른다.
    subprocess.run(["git", "-C", cwd, "fetch", "-q", "origin", br],
                   capture_output=True, text=True)
    base = _sp._base(cwd)
    subprocess.run(["git", "-C", cwd, "fetch", "-q", "origin",
                    base.removeprefix("origin/")],
                   capture_output=True, text=True)
    r = _sp._recut_absorbed_branch(cwd, br)
    if r.returncode != 0:
        print(f"[recut-if-absorbed] {br} 재검사 실패: {r.stderr.strip()[:200]}",
              file=sys.stderr)
        return 1
    return 0


def checkout_issue_branch(cwd: str, issue: int, role: str) -> str:
    """대상 레포에서 issue-<n>/<역할> 브랜치를 만든다(있으면 갈아탄다).

    core 의 board-gate R4 가 보드 쓰기를 이 브랜치에서만 허용하므로, 스폰
    전에 서 있어야 세션이 첫 쓰기부터 막히지 않는다. base 는 원격 기본
    브랜치 — 역할 산출물은 main 에서 갈라져 PR 로만 돌아간다 (계약 v3 s10).
    """
    br = f"issue-{issue}/{role}"
    def git(*a):
        return subprocess.run(["git", "-C", cwd, *a], capture_output=True, text=True)
    # 이슈 #1507 — 세션의 첫 verification/absence-claim 단계보다 먼저
    # 이 fetch --prune 이 origin/main sha 를 기록해야 한다.
    _sp.bootstrap_fetch_and_record_sha(cwd, "브랜치 체크아웃")
    _sp._fetch_or_halt(cwd, "브랜치 체크아웃")
    if git("rev-parse", "--verify", "-q", br).returncode == 0:
        # 재사용 워크스페이스의 로컬 브랜치가 base 에 완전히 흡수된 채로
        # 남아있을 수 있다 (머지 후 --delete-branch 는 원격만 지운다, 로컬
        # ref 는 그대로 살아남는다 — 실측: issue-441, issue-428 survey 의
        # issue-999 픽스처). 그 상태로 그냥 checkout 하면 이후 커밋이 없는
        # 한 origin 대비 0-ahead 브랜치로 PR 을 열게 되어 "No commits
        # between main and issue-<n>/<role>" 로 조용히 실패한다. base 대비
        # 커밋이 하나도 없으면 (완전 흡수) 로컬 ref 를 지우고 base 에서
        # 새로 판다 — 진행 중 작업(유니크 커밋 있음)은 오늘과 동일하게
        # 그대로 재사용한다.
        r = _sp._recut_absorbed_branch(cwd, br)
    elif git("rev-parse", "--verify", "-q", f"origin/{br}").returncode == 0:
        # rev-parse --verify -q br 는 로컬 ref 만 본다 — 워크스페이스가 새로
        # 클론된 직후라면 origin 에는 이미 있는 브랜치도 로컬엔 없어, 여기서
        # base 로 새로 파면 origin 의 기존 이력을 버리고 영구 분기한다
        # (실측: issue-235 phase 2). origin 전용이면 그걸 트래킹해 만든다.
        r = git("checkout", "-b", br, f"origin/{br}")
    else:
        base = _sp._base(cwd)
        r = git("checkout", "-b", br, base)
        if r.returncode != 0:      # base 없음(원격 없음 등) — 현 HEAD 에서라도 만든다
            r = git("checkout", "-b", br)
    if r.returncode != 0:
        sys.exit(f"브랜치 {br} 로 못 갈아탔다: {r.stderr.strip()[:200]}")
    return br


def _session_log_path(cwd: str) -> Path:
    """이슈-스코프 세션 하나의 라이브 로그 경로 — 타임스탬프+PID 접미사로
    세대마다 고유하게 만든다 (이슈 #192). 같은 워크스페이스로 재스폰해도
    이전 세대의 로그(`<work>.session.<ts>.<pid>.log`)를 truncate-open 으로
    덮어쓰지 않는다. `ts` 는 `time.strftime` 이라 사전순 정렬이 생성 순서와
    일치한다."""
    ts = time.strftime("%Y%m%dT%H%M%S", time.localtime())
    return Path(str(cwd) + f".session.{ts}.{os.getpid()}.log")


def _artifact_smoke_task_lines(body: str | None) -> str:
    """이슈 #2073: 스폰 과제 뒤에 붙는 최대 두 줄의 조건부 코-인젝션.

    (a) 본문이 `runtime-artifacts:` 를 선언했거나(또는 선언은 없지만
        생성물/브라우저 어휘 자문 스코어러가 울리면) artifact-smoke
        트리거 한 줄 — 선언된 경로를 그대로 이름한다.
    (b) 이슈가 design-bearing 이면서 선언된 design-artifacts 중 하나가
        스토리보드면 live-screen 검증 한 줄.

    어느 조건도 안 걸리면 빈 문자열을 돌려준다 — 오늘의 과제 텍스트와
    바이트 단위로 같아야 한다. 새 네트워크 호출은 하지 않는다(본문은
    이미 받아온 것). gates 모듈을 못 불러오면 조용히 빈 문자열이다.
    """
    if not body:
        return ""
    try:
        sys.path.insert(0, str((_sp.ROOT / "gates").resolve()))
        import artifact_smoke_rule as _asr
        import design_artifacts_gate as _dag
        import design_bearing_classifier as _dbc
    except Exception:
        return ""

    out = ""
    try:
        declared = _asr.parse_declaration(body)
    except Exception:
        declared = None
    if declared:
        out += (
            "\n\nARTIFACT-SMOKE(이슈 #2073): 이 이슈는 런타임 산출물을 "
            f"선언했다 — {', '.join(declared)}. 이 산출물 자체를 파싱하거나 "
            "실행하는 검사가 최소 하나 있어야 한다(소스 유닛 테스트도, "
            "재생성 diff 도 그 자리를 대신하지 못한다). 허용 동사와 계약은 "
            "docs/specs/artifact-smoke-contract.md 에 있다.\n")
    elif declared is None:
        try:
            advisory = _asr.advisory_line(0, body)
        except Exception:
            advisory = None
        if advisory:
            out += (
                "\n\nARTIFACT-SMOKE(이슈 #2073): 이 이슈 본문이 생성물/"
                "브라우저 산출물 어휘를 담고 있는데 `runtime-artifacts:` "
                "선언이 없다 — 배송되는 산출물이 있으면 선언하고, 그 산출물을 "
                "실제로 파싱/실행하는 검사를 `## Acceptance` 에 하나 둬라"
                "(docs/specs/artifact-smoke-contract.md).\n")

    try:
        verdict = _dbc.check_issue_body(0, body)
        design_bearing = bool(verdict and verdict.get("design_bearing"))
        design_artifacts = _dag.parse_declaration(body) or []
    except Exception:
        design_bearing, design_artifacts = False, []
    storyboards = [p for p in design_artifacts if _sp._STORYBOARD_RE.search(p)]
    if design_bearing and storyboards:
        out += (
            "\n\nVISUAL-VERIFICATION(이슈 #2073): 이 이슈는 design-bearing "
            f"이고 스토리보드({', '.join(storyboards)})를 선언했다 — 레코드에 "
            "`screen-verified:` 줄을 남겨라: docs/issue-<n>/_assets/ 아래의 "
            "실화면 스크린샷 경로와, 그 스토리보드에 비춘 한 줄 판정. 판정 "
            "내용은 네 몫이다(게이트는 줄과 파일의 존재만 본다).\n")
    return out


def _goal_pin_block(title: str | None, body: str | None) -> str:
    """이슈 #1652 (northpole req#6): 제목 + '## Acceptance' 의 'check:'
    불릿을 스폰 프롬프트에 그대로(verbatim) 박아, 스폰된 역할 세션이
    첫 턴부터 원본 목표를 본다 — 코멘트 히스토리 등 오염된 문맥은 절대
    섞지 않는다. Acceptance 절이 없거나 check: 불릿이 하나도 없으면
    빈 문자열을 돌려준다(오늘의 프롬프트와 바이트 단위로 동일해야
    한다 — 빈 헤더를 주입하지 않는다).
    """
    title = (title or "").strip()
    body = body or ""
    sys.path.insert(0, str((_sp.ROOT / "gates").resolve()))
    import acceptance_gate as _acceptance_gate
    section = _acceptance_gate._acceptance_section(body)
    if section is None:
        return ""
    checks = [c.strip() for c in _sp._ACCEPTANCE_CHECK_LINE.findall(section)]
    checks = [c for c in checks if c]
    if not checks:
        return ""
    lines = []
    if title:
        lines.append(f"이슈 제목(원본 목표): {title}")
    lines.append("Acceptance 기준(원본, verbatim):")
    for c in checks:
        lines.append(f"- check: {c}")
    return "\n".join(lines) + "\n"


def _skill_trigger_line(skill_dir: Path) -> str | None:
    """`skill_dir/SKILL.md` 프론트매터의 `description:` 필드에서 "Use ..."로
    시작하는 트리거 문장을 뽑는다. 파일/프론트매터/description/트리거 문장
    중 무엇이든 없으면 None — 예외를 던지지 않는다(호출부가 이름만이라도
    싣는 empty-state 처리를 하도록).

    폴딩 블록 스칼라(`description: >-`)를 포함해 여러 줄 description 을
    다루려면 전체 YAML 파서가 필요하지만, 이 함수가 필요한 건 딱 한
    문장뿐이라(제안서 Rationale) 프론트매터 블록만 떼어내 정규식으로
    훑는다."""
    desc = _skill_frontmatter_description(skill_dir)
    if desc is None:
        return None
    um = _sp._SKILL_USE_SENTENCE_RE.search(desc)
    return um.group(1).strip() if um else None


def _skill_frontmatter(skill_dir: Path) -> str | None:
    """`skill_dir/SKILL.md` 의 프론트매터 블록 텍스트. 없으면 None."""
    md = skill_dir / "SKILL.md"
    try:
        text = md.read_text(encoding="utf-8")
    except OSError:
        return None
    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return fm.group(1) if fm else None


def _skill_frontmatter_description(skill_dir: Path) -> str | None:
    """프론트매터 `description:` 필드 전체(폴딩 블록 스칼라 포함)를 공백
    정규화해 돌려준다 — `_skill_trigger_line()` 이 쓰던 추출을 그대로
    분리한 것(이슈 #2124: BM25 문서가 첫 "Use ..." 문장이 아니라 이 전체
    description 을 색인해야 한다). 없으면 None."""
    fm = _skill_frontmatter(skill_dir)
    if fm is None:
        return None
    dm = re.search(r"(?m)^description:[ \t]*(.*(?:\n(?:[ \t]+.*)?)*)", fm)
    if not dm:
        return None
    desc = dm.group(1).strip()
    desc = desc.lstrip(">|-+").strip()
    desc = desc.strip("\"'")
    desc = re.sub(r"\s+", " ", desc)
    return desc or None


def _skill_frontmatter_axis(skill_dir: Path) -> str | None:
    """프론트매터 `metadata:` 블록 아래 `axis:` 값(#101 이후 위치). 없으면
    None — 전체 YAML 파서 없이, metadata 블록 안의 들여쓴 `axis:` 줄만
    정규식으로 집는다."""
    fm = _skill_frontmatter(skill_dir)
    if fm is None:
        return None
    mm = re.search(r"(?m)^metadata:[ \t]*\n((?:[ \t]+.*\n?)*)", fm)
    if not mm:
        return None
    am = re.search(r"(?m)^[ \t]+axis:[ \t]*(.+)$", mm.group(1))
    return am.group(1).strip().strip("\"'") or None if am else None


def _skill_bm25_document(name: str, skill_dir: Path) -> str:
    """이슈 #2124 part 1: `_bm25_cross_family_scores` 가 색인하는 문서 =
    프론트매터 description 전문 + 스킬 이름 토큰(family 프리픽스는 이름의
    선행 세그먼트라 이름 토큰에 자동 포함 — 토큰화가 집합이라 별도 반복은
    무의미하다) + `metadata.axis` 토큰. 결정론적 문자열 조립만 한다 —
    스코어링 입력 외에는 아무 동작도 바꾸지 않는다. description 이 없으면
    이름+axis 만으로도 문서를 만든다(empty-state: 이름은 절대 안 빠진다)."""
    parts = [name.replace("-", " ")]
    desc = _skill_frontmatter_description(skill_dir)
    if desc:
        parts.append(desc)
    axis = _skill_frontmatter_axis(skill_dir)
    if axis:
        parts.append(axis.replace("-", " "))
    return " ".join(parts)


_SKILL_QUOTED_PHRASE_RE = re.compile(r'["“‘]([^"“”‘’]{3,80})["”’]')


def _skill_declared_phrases(skill_dir: Path) -> list[str]:
    """이슈 #2124 part 2: description 안에 따옴표로 선언된 트리거 문구들
    (#99 의 "Trigger on requests like \"...\"" 포맷). 소문자로 돌려준다.
    한 단어짜리 흔한 토큰이 fast-path 자동 픽을 만드는 걸 막으려고,
    공백을 포함하거나 8자 이상인 문구만 남긴다."""
    desc = _skill_frontmatter_description(skill_dir)
    if not desc:
        return []
    phrases = []
    for m in _SKILL_QUOTED_PHRASE_RE.finditer(desc):
        p = m.group(1).strip().lower()
        if p and (" " in p or len(p) >= 8):
            phrases.append(p)
    return phrases


def _tokenize(text: str) -> set[str]:
    """소문자화 + 비영숫자 분리 + 작은 불용어 목록 제거. "Use when" 처럼
    트리거 문장이면 어디에나 있는 일반 단어가 그 자체로 매치를 만들지
    않게 한다(제안서 What will be done)."""
    return {t for t in _sp._TOKEN_RE.findall(text.lower()) if t not in _sp._STOPWORDS}


def _cross_family_candidate_corpus(role: str, repo_root: Path | None,
                                    home: Path | None = None,
                                    target_repo_root: Path | None = None
                                    ) -> list[tuple[str, Path, str]]:
    """이슈 #2055: `_bm25_cross_family_scores` 의 후보 코퍼스를 skill-repository
    단일 소스에서 네 소스(skill-repository, 설치된 플러그인, `~/.claude/skills`,
    타깃 저장소 `.claude/skills`)로 넓힌다 — `resolved_skill_sources()`(이슈
    #1774)와 같은 해석 규칙을 재사용한다: 이름 하나가 소스 두 개 이상에
    걸리면(같은 tier 안의 플러그인-대-플러그인 충돌 포함) fail-closed, 잡힌
    소스를 전부 이름 붙여 보고한다. `hooks/` 서브디렉터리를 든 후보는
    코퍼스에서 조용히 제외된다(스킬 마운트는 가이던스 전용 원칙 — 이건
    사용자가 이름을 지목한 `--skills` 가 아니라 자동 탐색이라 fail-closed
    가 아니라 그냥 후보에서 빠진다).

    반환은 (name, dir, source) 튜플 목록 — source 는 `_describe_skill_match()`
    가 아는 값(`"skill-repo"|"plugin"|"local-user"|"local-repo"`)과 같은
    어휘를 쓴다. family 안 스킬(`_ROLE_SKILLS[role]`)은 호출자가 이미
    걸러내던 대로 여기서도 걸러 반환에서 뺀다.

    `home`/`target_repo_root` 를 생략하면(`None`) 해당 tier 는 아예 안
    읽는다 — 기존 호출부(테스트 포함)가 skill-repository tier 만 보는
    오늘의 동작을 그대로 유지하기 위한 명시적 opt-in 이다. 설치된 플러그인
    tier 는 `_installed_plugin_skill_dirs()` 자체가 이름이 실제로 필요할
    때만 파일을 읽으므로 별도 게이트가 필요 없다."""
    family_names = set(_sp._ROLE_SKILLS.get(role, []))
    matches: dict[str, list[tuple[str, Path]]] = {}

    def add(source: str, name: str, d: Path) -> None:
        if (d / "hooks").is_dir():
            return
        matches.setdefault(name, []).append((source, d))

    if repo_root is not None and repo_root.is_dir():
        for name, d in _sp._local_skill_dirs(repo_root).items():
            add("skill-repo", name, d)
    for name, entries in _sp._installed_plugin_skill_dirs().items():
        for _qualifier, d, _version in entries:
            add("plugin", name, d)
    if home is not None:
        for name, d in _sp._local_skill_dirs(home / ".claude" / "skills").items():
            add("local-user", name, d)
    if target_repo_root is not None:
        for name, d in _sp._local_skill_dirs(target_repo_root / ".claude" / "skills").items():
            add("local-repo", name, d)

    corpus: list[tuple[str, Path, str]] = []
    for name, ms in matches.items():
        if name in family_names:
            continue
        if len(ms) > 1 and len({_sp._skill_content_hash(d) for _, d in ms}) == 1:
            # 실제 운영 환경에서는 `~/.claude/skills` 가 skill-repository 를
            # 그대로 미러링해두는 경우가 흔하다 — 같은 이름이 같은
            # `SKILL.md` 내용을 가리키면 어느 tier 를 골라도 채점 결과가
            # 바이트 단위로 같으므로, 이건 "가리기"가 아니라 중복이다.
            # fail-closed 는 내용이 실제로 갈릴 때만 발동한다.
            ms = ms[:1]
        if len(ms) > 1:
            described = ", ".join(f"{source}({d})" for source, d in ms)
            sys.exit(f"cross-family 후보 스킬 {name} 가 둘 이상의 소스에서 "
                      f"겹친다 — {described} (이슈 #2055: 네 소스 중 어느 "
                      f"tier 도 다른 tier 를 조용히 가리지 않는다)")
        source, d = ms[0]
        corpus.append((name, d, source))
    return corpus


def _resolve_session_max_turns(cli_value: int | None) -> int:
    """Session turn budget: explicit CLI value > MUSTER_SESSION_MAX_TURNS
    env > built-in default. A value <= 0 means "unlimited" and is refused
    at admission unless explicitly overridden (issue #2100 item 4 — the
    Claude Agent SDK default is unlimited; production guidance is to
    always cap)."""
    if cli_value is not None:
        return cli_value
    env = os.environ.get("MUSTER_SESSION_MAX_TURNS")
    if env:
        try:
            return int(env)
        except ValueError:
            pass
    return _sp.DEFAULT_SESSION_MAX_TURNS


def _checkpoint_poll_seconds() -> float:
    """Issue #2129: comment-poll cadence of the in-session approval wait.
    Read at call time so tests and operators can override per-run."""
    try:
        return float(os.environ.get("CHECKPOINT_POLL_SECONDS", "60"))
    except ValueError:
        return 60.0


def _checkpoint_wait_max_seconds() -> float:
    """Issue #2129: total bounded wait of the in-session approval pause."""
    try:
        return float(os.environ.get("CHECKPOINT_WAIT_MAX_SECONDS", "1800"))
    except ValueError:
        return 1800.0


AWAIT_APPROVAL_TIMEOUT_RC = 3


def await_approval_cmd(cwd: str, issue: int, role: str,
                       timeout: float | None = None,
                       interval: float | None = None) -> int:
    """Issue #2129 checkpoint mode: the deterministic in-session approval
    wait. The spawned session runs this ONE command at the phase-1/phase-2
    boundary instead of burning model turns on a poll loop.

    Behavior: writes the #2101 declared-wait file (`.waiting-on.json`,
    object `issue:<n>` — the exact format `_declared_wait` reads, so the
    watchdog's flat-progress exemption applies for the whole pause), then
    polls the issue comments for the `APPROVE issue-<n>/<role>` needle with
    the SAME predicate the phase-2 merge gate reads
    (`gates/ci.py._approved_roles_on_issue` — this call IS the approve-token
    check at the boundary, which is why admission's approve-token row cedes
    to checkpoint spawns). Returns 0 on approval, 3
    (AWAIT_APPROVAL_TIMEOUT_RC) on timeout. The declared-wait file is
    removed on both exits — the pause is over either way."""
    root = Path(cwd).resolve()
    interval = _sp._checkpoint_poll_seconds() if interval is None else interval
    timeout = _sp._checkpoint_wait_max_seconds() if timeout is None else timeout
    sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
    import ci as _ci
    wait_path = root / _sp.DECLARED_WAIT_FILENAME
    try:
        wait_path.write_text(json.dumps({
            "object": f"issue:{issue}", "reason": "approve-token",
            "issue": issue, "role": role, "ts": int(time.time()),
            # Issue #2133: the watchdog sweep computes the remaining wait
            # from ts + budget_sec to surface the healthy pause
            # ([awaiting-approval] line); a wait file without budget_sec
            # surfaces as remaining=unknown.
            "budget_sec": timeout,
        }), encoding="utf-8")
    except OSError as exc:
        # Advisory-only machinery: a wait that cannot be declared must not
        # abort the pause itself (worst case is a watchdog advisory).
        print(f"[await-approval] could not write {wait_path}: {exc}",
              file=sys.stderr)
    deadline = time.monotonic() + timeout
    try:
        while True:
            if role in _ci._approved_roles_on_issue(root, issue):
                print(f"[await-approval] APPROVE issue-{issue}/{role} "
                      f"observed — continue to phase-2 in this session.")
                return 0
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                print(f"[await-approval] timeout after {timeout:.0f}s — no "
                      f"APPROVE issue-{issue}/{role}. End the session "
                      f"cleanly; the proposal PR is the returned state.",
                      file=sys.stderr)
                return _sp.AWAIT_APPROVAL_TIMEOUT_RC
            time.sleep(min(interval, remaining))
    finally:
        try:
            wait_path.unlink()
        except OSError:
            pass


def _admission_check_approve_token(ctx: dict) -> bool | None:
    """Item 1 (issue #2100): on a phase-2 issue the spawned role's APPROVE
    token must already be published — checked with the same predicate the
    consuming gate uses (`gates/ci.py._approved_roles_on_issue`, the exact
    scan the phase-2 merge gate later reads). This reconstructs the 3x
    APPROVE-token incident at admission time: phase-2 issue, role differs
    from every approved role, token not yet published => refuse now
    instead of stranding the session on the gate mid-flight."""
    issue, role = ctx.get("issue"), ctx["role"]
    if issue is None or ctx.get("single_phase"):
        return True  # adhoc spawn / explicit build-now bypass: no token gate
    if ctx.get("checkpoint"):
        # Issue #2129: a checkpoint-mode spawn deliberately starts BEFORE
        # any APPROVE token exists — the session itself enforces the token
        # at the phase-1/phase-2 boundary (`spawn.py await-approval`, the
        # same `_approved_roles_on_issue` predicate this row consults).
        # Without this exemption the row would double-block every
        # checkpoint spawn on a phase-2 issue whose approved role differs,
        # which is exactly the state a checkpoint spawn is designed to
        # enter. The boundary check is strictly later and strictly
        # equivalent, so admission cedes this row to it.
        return True
    root = Path(ctx["cwd"]).resolve()
    if not (root / _sp.MARKER).is_file():
        return True  # off-board work: no approver machinery to consult
    # Distinguish "no approval comments" from "could not read comments":
    # `_approved_roles_on_issue` deliberately collapses the two (it
    # fail-closes to phase-1), but admission must fail OPEN on a gh
    # failure — so probe the comment fetch first and fail open on error.
    _, ok = _sp._issue_comments(root, issue)
    if not ok:
        return None  # gh/network failure — fail-open (ledger event + proceed)
    sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
    import ci as _ci
    approved = _ci._approved_roles_on_issue(root, issue)
    if not approved:
        return True  # phase-1 issue: no token is required yet
    return role in approved


def _admission_check_directive_completeness(ctx: dict) -> bool | None:
    """Item 2 (issue #2100): the co-injected directive items (record-format
    contract / single-vs-two-phase signal — core#195 lineage via
    `_SINGLE_PHASE_CONTRACT_LINE`; per-skill trigger lines — issue #1978)
    must assemble without error BEFORE spawn. An assembly failure here is
    an admission refusal, not a mid-flight surprise. This is deterministic
    local work (role spec file, skill-repository checkout, SKILL.md
    frontmatter), so a failure is a refusal — never fail-open."""
    role = ctx["role"]
    try:
        if not (_sp.ROOT / "roles" / f"{role}.json").is_file():
            return False  # role spec is the first directive ingredient
        # Two-phase signal: the contract line must format for this role.
        _sp._SINGLE_PHASE_CONTRACT_LINE.format(role=role)
        # Per-skill trigger lines (issue #1978 B): resolve every skill
        # source the spawn body will resolve, and extract each trigger
        # line, exactly as the assembly code does.
        srcs = _sp.resolved_skill_sources(ctx.get("skills"), _sp._skill_repo_root(),
                                      target_repo_root=Path(ctx["cwd"]))
        role_source = _sp.resolve_role_source(role, _sp._skill_repo_root())
        for m in srcs:
            _sp._skill_trigger_line(m["dir"])
        for d in role_source["skill_dirs"]:
            _sp._skill_trigger_line(d)
    except Exception:
        # The directive cannot be assembled — refuse. SystemExit from the
        # fail-closed resolvers (unknown/invalid skill names) is NOT
        # caught here: `admission_gate()` records the named refusal and
        # re-raises it so the resolver's actionable message reaches the
        # caller unchanged (pre-#2100 behavior, still before any
        # workspace exists).
        return False
    return True


def _admission_check_watch_registration(ctx: dict) -> bool | None:
    """Item 3 (issue #2100): a live watch/monitor registration must be able
    to succeed for this session's terminal event — verified at admission,
    not after the fork. The auto-armed watcher (issue #488) is
    `sys.executable spawn.py watch --follow` plus a workspace-index /
    roster write under STATE_ROOT; verify those exact ingredients exist
    and the state directory accepts writes. Purely local — deterministic,
    so a failure is a refusal, never fail-open."""
    if ctx.get("issue") is None:
        return True  # adhoc spawns register in-roster in-process only
    if not Path(sys.executable).exists() or not Path(__file__).resolve().exists():
        return False
    try:
        _sp.ROSTER.parent.mkdir(parents=True, exist_ok=True)
        probe = _sp.ROSTER.parent / f".admission-watch-probe-{os.getpid()}"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError:
        return False
    return True


def _admission_check_budget_caps(ctx: dict) -> bool | None:
    """Item 4 (issue #2100): the spawn must carry a turn/budget cap. A
    resolved max-turns is always present (default applies when nothing is
    set); only an EXPLICIT unlimited (<= 0) without the override flag is
    refused."""
    max_turns = ctx.get("max_turns")
    if max_turns is None:
        return True  # resolver guarantees a default; None means "not plumbed here"
    if max_turns <= 0:
        return bool(ctx.get("allow_unlimited_turns"))
    return True


def _board_marker_probe(slug: str) -> bool | None:
    """Probe the remote DEFAULT branch of `slug` for the board marker
    (`docs/specs/approvers.md`) via the gh contents API — the branch the
    workspace clone will be cut from and the record write will target.
    Returns True (present), False (confirmed missing — HTTP 404), or None
    (gh/network failure: the probe could not be evaluated)."""
    try:
        r = subprocess.run(
            ["gh", "api", f"repos/{slug}/contents/{_sp.MARKER}",
             "-q", ".path"],
            capture_output=True, text=True, timeout=_sp.NETWORK_TIMEOUT)
    except (subprocess.TimeoutExpired, OSError):
        return None
    if r.returncode == 0:
        return True
    if "404" in (r.stderr or ""):
        return False  # the API answered: the file is not there
    return None  # gh broken / auth / network — cannot evaluate


def _admission_check_board_validity(ctx: dict) -> bool | None:
    """Item 5 (issue #2123): the TARGET must be a valid board — its remote
    default branch must carry docs/specs/approvers.md — BEFORE any session
    starts. Live incident (2026-08-23 E2E): the marker was missing on the
    remote (operator push error), the spawn was admitted, ran 5 minutes to
    a complete PR, then stranded at the record write on the fail-closed
    board-gate. A deterministic, cheap, guaranteed-to-strand precondition
    is exactly what admission exists to catch.

    Pre-clone gh contents probe (implementer's choice per the issue): it
    refuses before any workspace exists, matching the #2100 "no workspace
    left behind" contract; the cost is one extra gh API call vs reusing a
    checkout that would already have been made."""
    root = Path(ctx["cwd"]).resolve()
    slug = _sp._repo_slug(root)
    if slug is None:
        # No resolvable remote (local-only target, or gh cannot map one):
        # there is no remote default branch to probe — the workspace
        # materializes from the local checkout, where board.py's own
        # marker check governs. Not a gh failure; nothing to fail open on.
        return True
    verdict = _sp._board_marker_probe(slug)
    if verdict is False:
        print(f"[admission] board-validity: the default branch of {slug} "
              f"has no {_sp.MARKER} — the session would run to completion "
              f"and then strand at its record write (board-gate is "
              f"fail-closed). Run `spawn.py init --push` on the target "
              f"(plain `init` verifies the remote and prints the exact "
              f"push commands), then dispatch again.", file=sys.stderr)
    return verdict


def admission_gate(ctx: dict) -> str | None:
    """Run every ADMISSION_CHECKS row against `ctx`. Returns the name of
    the first missing precondition (after writing ONE `admission_refused`
    ledger event naming it), or None when admission passes. A refusal is
    deterministic and NON-RETRYABLE by the caller — the fix is publishing
    the missing precondition, never retrying the same dispatch."""
    for name, predicate in _sp.ADMISSION_CHECKS:
        try:
            verdict = predicate(ctx)
        except SystemExit:
            # A fail-closed resolver exits with its own actionable message
            # (e.g. "--skills: unknown skill ..."). That IS a refusal of
            # this item: record it under the item's name, then let the
            # original exit propagate unchanged — still before any session
            # or workspace exists.
            _sp.ledger_write({"event": "admission_refused", "item": name,
                          "role": ctx.get("role"), "issue": ctx.get("issue"),
                          "ts": int(time.time())})
            raise
        except Exception as exc:
            # A check that crashes must not become a new stall class:
            # follow the returned-PR gate fail-open convention (issue
            # #680) — record the fact, let the spawn proceed.
            verdict = None
            print(f"admission check {name!r} crashed — fail-open: {exc}",
                  file=sys.stderr)
        if verdict is None:
            _sp.ledger_write({"event": "admission_gate_fail_open", "item": name,
                          "role": ctx.get("role"), "issue": ctx.get("issue"),
                          "ts": int(time.time())})
            continue
        if not verdict:
            _sp.ledger_write({"event": "admission_refused", "item": name,
                          "role": ctx.get("role"), "issue": ctx.get("issue"),
                          "ts": int(time.time())})
            return name
    return None

