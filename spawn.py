#!/usr/bin/env python3
"""역할별 플러그인 환경으로 에이전트를 띄운다. on-the-record 의 핵심 동작 하나.

  python3 spawn.py <역할> <맡길 일> [-C <작업 디렉터리>] [--dry-run]
  python3 spawn.py review "PR 12 를 리뷰해라"
  python3 spawn.py qa "/testrun:testrun smoke" -C ~/work/some-repo

**왜 스크립트가 필요한가**: `--settings` 는 덮어쓰기가 아니라 **병합**이다. 역할
파일에 qa 플러그인만 적어도 사용자 전역 설정의 플러그인 17개가 그대로 딸려온다 —
"코딩 에이전트가 qa 룰북까지 본다"는 원래 문제의 다른 얼굴이다. 전역 목록을 읽어
역할이 켜지 않은 것을 전부 `false` 로 덮어야 격리가 성립한다(실측 확인).

`--settings` 는 사용자 설정보다 우선순위가 높으므로 이 덮어쓰기가 이긴다.

**CLAUDE_CONFIG_DIR 로 통째 격리하지 않는 이유**: 설정은 완전히 갈리지만 macOS
키체인 항목이 설정 디렉터리에 묶여 있어 인증이 끊긴다("Not logged in"). 인증을
그대로 쓰는 것이 컨테이너 대신 샌드박스를 고른 이유이므로, 그 이점을 버리지 않는다.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import contextlib
import re
import fcntl
import hashlib
import io
import json
import math
import os
import signal
import stat
import string
import subprocess
import sys
import traceback
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# 이슈 #1274: roster_watchdog() 의 반환값(anomaly count, rc>=0)과 절대 겹치지
# 않도록 고른 예약 종료 코드 — watchdog CLI 분기가 처리 못 한 예외를 이
# 코드로 종료해, 파이썬 기본 트레이스백 종료(exit 1)가 anomaly_count==1 과
# 구분 안 되는 문제를 없앤다. poll-heartbeat.sh 는 rc>=128(시그널 사망) 이거나
# rc==이 값일 때만 [watchdog-crash] 를 찍는다.
WATCHDOG_CRASH_SENTINEL = 97
# 이슈 #1456: #1360 재발(구코드를 5시간 물고 있던 워치독) 방지용 예약
# 종료 코드 — WATCHDOG_CRASH_SENTINEL 과 마찬가지로 roster_watchdog() 의
# 정상 반환값(anomaly count, rc>=0)과 겹치지 않게 고른 상수다.
WATCHDOG_LOCKED_SENTINEL = 96          # 이미 다른 인스턴스가 락을 쥐고 있다
WATCHDOG_STALE_CODE_SENTINEL = 95      # 체크아웃 HEAD 가 시작 시점과 달라졌다
WATCHDOG_NONCANONICAL_SENTINEL = 94    # 워치독 자신이 canonical 체크아웃 밖이다

# 이슈 #878: 오케스트레이터 자신의 (headless `-p`) 세션 ID를 전달하는 환경
# 변수 이름 — 이 프로세스(spawn.py)를 부른 오케스트레이터 프로세스가 이미
# 알고 있을 때만(interactive 세션은 모른다/필요없다; harness driver 는
# `claude -p --output-format json` 의 첫 턴 결과에서 얻은 뒤 다음 스폰부터
# export 한다) 심어준다. 이름 자체는 새 스케줄러가 아니라 기존 roster 엔트리
# 필드 하나를 채우는 관례일 뿐이다.
ORCHESTRATOR_SESSION_ID_ENV = "ORCHESTRATOR_SESSION_ID"
# 이슈 #878 after-proposal hunt 발견: session_id 는 프로세스 단위지 roster
# 엔트리 단위가 아니다 — 같은 오케스트레이터 세션이 무장한 여러 엔트리가
# 같은 폴 창에서 동시에 ready 가 되면 이 TTL 로 session_id 당 딱 한 번만
# resume-invoke 가 나가게 한다(ledger_check_and_stamp 를 그대로 락으로
# 재사용, 새 락 프리미티브를 만들지 않는다).
SESSION_RESUME_CLAIM_TTL_SEC = 15 * 60
USER_SETTINGS = Path.home() / ".claude" / "settings.json"

# 이슈 #857: 로스터(ROSTER)/워크스페이스 인덱스(WORKSPACE_INDEX)가 기본으로
# 가리키는 상태 루트. 기본값은 기존 동작과 동일(설치 디렉터리 아래
# runs/) — MUSTER_STATE_ROOT 를 주면 그쪽을 대신 쓴다. 하네스가 띄우는
# fixture 세션에 관측 세션과 다른 값을 주면, 같은 플러그인 설치를
# 공유하고 같은 --issue 번호를 써도 로스터/워크스페이스 인덱스 파일
# 자체가 물리적으로 갈려 서로의 항목을 볼 수 없다(PR #855 finding 5).
STATE_ROOT = (Path(os.environ["MUSTER_STATE_ROOT"]).resolve()
              if os.environ.get("MUSTER_STATE_ROOT") else ROOT / "runs")

NETWORK_TIMEOUT = 60   # fetch/pull/push
CLONE_TIMEOUT = 180    # clone — bigger initial transfer
CONSULT_TIMEOUT = 180  # consult: bounded headless run — no branch/PR to wait on
SKILL_JUDGE_TIMEOUT_DEFAULT = 45  # issue #2061: judge is a tiny classification, not a full consult


def _skill_judge_timeout() -> float:
    """env-overridable 타임박스(issue #2061) — 매 호출마다 읽어 테스트가
    `os.environ`을 몽키패치한 뒤에도 값을 반영한다."""
    raw = os.environ.get("SKILL_JUDGE_TIMEOUT")
    if raw is None:
        return SKILL_JUDGE_TIMEOUT_DEFAULT
    try:
        return float(raw)
    except ValueError:
        return SKILL_JUDGE_TIMEOUT_DEFAULT

PANEL_TIMEOUT = 240    # panel: two judges + a rebuttal round, wider than a single consult
JUDGE_TIMEOUT = 120           # issue #1587: per-judge-call hard cap (prefilter/judge/validator each)
JUDGE_MAX_ROLES_PER_MERGE = 3  # issue #1587: cost/API-strain cap — counted from the trace log


def _run_net(args: list[str], label: str, timeout: float = NETWORK_TIMEOUT,
             **kwargs) -> subprocess.CompletedProcess:
    """`timeout=`을 강제하는 네트워크 subprocess 호출. `TimeoutExpired`가
    그냥 새 나가면 오케스트레이터가 무기한 걸린다(이슈 #285 P5) — 대신
    `_fetch_or_halt`(spawn.py:2577)와 같은 모양의 이름 있는 에러로
    fail-closed."""
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    try:
        return subprocess.run(args, timeout=timeout, **kwargs)
    except subprocess.TimeoutExpired:
        sys.exit(f"{label}: 시간초과({int(timeout)}s) — 네트워크를 확인하라")


_BOOTSTRAP_TIMING: dict[str, float] = {}
_BOOTSTRAP_PHASES = ("workspace", "branch", "rulebook", "core", "gh_token", "settings",
                     "cross_family")


@contextlib.contextmanager
def _timed(phase: str):
    """부트스트랩 단계 하나의 소요 시간을 `_BOOTSTRAP_TIMING`에 누적한다
    (이슈 #711) — `_spawn_one` 제어 흐름·종료 코드는 그대로, 측정만 덧붙인다."""
    t0 = time.monotonic()
    try:
        yield
    finally:
        _BOOTSTRAP_TIMING[phase] = _BOOTSTRAP_TIMING.get(phase, 0.0) + (time.monotonic() - t0)


def _bootstrap_timing_line(role: str) -> str:
    parts = [f"{p}={_BOOTSTRAP_TIMING.get(p, 0.0):.3f}" for p in _BOOTSTRAP_PHASES]
    total = sum(_BOOTSTRAP_TIMING.get(p, 0.0) for p in _BOOTSTRAP_PHASES)
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
    return ROOT / "runs" / "ttl-markers" / key


def _pull_is_fresh(d: Path) -> bool:
    """TTL 창 안이면 True — 이번엔 `git pull` 을 건너뛴다(이슈 #285 P4).
    `MUSTER_RULEBOOK_TTL=0` 이면 항상 False(매번 pull, 오늘의 동작)."""
    ttl_min = _rulebook_ttl_min()
    if ttl_min <= 0:
        return False
    m = _ttl_marker(d)
    try:
        age_s = time.time() - m.stat().st_mtime
    except OSError:
        return False
    return age_s < ttl_min * 60


def _mark_pulled(d: Path) -> None:
    try:
        marker = _ttl_marker(d)
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
    lock_path = _rulebook_lock_path(d)
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
    f = ROOT / "roles" / f"{role}.json"
    if not f.exists():
        have = ", ".join(sorted(p.stem for p in (ROOT / "roles").glob("*.json")))
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
        globals_ = json.loads(USER_SETTINGS.read_text()).get("enabledPlugins", {})
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
        for pattern in _workspace_bash_allow(cwd):
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
        injected = self_hosted_hooks(cwd)
        if injected:
            s["hooks"] = injected
    return s



# 역할 순서. 보드를 읽을 때 이 순서로 보여준다.
ROLES = ("product-discovery", "interaction-design", "technical-feasibility",
         "implementation", "execution-observation", "conformance-review",
         "defect-verification", "issue-retrospective", "release-engineering",
         "user-discovery", "requirements-engineering", "refactoring-legacy",
         "test-authoring", "observability", "incident-response",
         "capacity-planning", "knowledge-management",
         "ux-engineering", "api-design", "architecture", "security-threat-model",
         "data-modeling", "performance-engineering", "accessibility", "secure-coding",
         "ml-engineering", "data-engineering",
         "market-analysis", "finance-unit-economics", "pricing", "sales", "marketing",
         "growth-analytics", "customer-support", "partnerships-bd", "pr-communications",
         "risk-management", "legal-compliance",
         "technical-writing", "brand-design", "content-design", "localization", "devrel")
BOARD = "docs"                          # v3: subject trees live at docs/issue-<n>/
MARKER = "docs/specs/approvers.md"      # 보드 opt-in + 승인자 allowlist (v3)
REQUIREMENT_DIGEST_MARKER = "docs/specs/requirement-digest.md"  # issue #1695
# 계약 v1 이 쓰던 자리. 아직 v2 로 안 옮긴 레포를 **말해주기 위해서만** 본다
LEGACY = {"conformance-review": "review-record.md",
          "technical-feasibility": "feasibility-record.md",
          "release-engineering": "state.md",
          "product-discovery": "product-record.md"}


def slug(cwd: str) -> str:
    """레포 디렉터리 이름 (계약 v2 §9).

    v1 은 origin 리모트에서 <owner>-<repo> 를 뽑았는데, 그건 폐지된
    `$QA_WORKSPACE` 의 레포 간 경로 때문에만 있던 것이다. 리모트 없는 레포에서
    깨지지 않는 것이 §9 가 이 규칙을 고른 이유다.
    """
    return Path(cwd).resolve().name


def init_board(cwd: str, login: str | None = None) -> int:
    """대상 레포를 보드로 선언한다: docs/specs/approvers.md 를 만든다.

    v3: 계약 심기는 폐지됐다 — 정본은 core 플러그인에만 있고, 레포 사본은
    해시 검사로 강제 동일해져 정보량이 0이었다. 보드 표식이자 승인자
    allowlist 인 approvers.md 만 있으면 된다. **사용자의 파일이다** —
    이미 있으면 절대 덮지 않는다.
    """
    root = Path(cwd).resolve()
    dest = root / MARKER
    if dest.exists():
        print(f"이미 있다: {dest}")
        init_requirement_digest(cwd)
        return 0
    if not login:
        r = subprocess.run(["gh", "api", "user", "--jq", ".login"],
                           capture_output=True, text=True)
        login = r.stdout.strip() if r.returncode == 0 else ""
    if not login:
        sys.exit("승인자 로그인을 모른다. gh auth login 을 하거나 "
                 "init --login <github-login> 으로 준다.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(f"- {login}\n", encoding="utf-8")
    print(f"보드로 선언했다: {dest}  (approver: {login})")
    init_requirement_digest(cwd)

    # issue #2022: 로컬 작업 트리에만 쓰고 끝내면, 신선한 클론에서 스폰한
    # 세션이 approvers.md 를 못 봐서 board-gate 에 막혀 죽는다(실측:
    # skill-repository #50). 커밋하고 push 까지 해야 다음 스폰이 성공한다.
    rels = [MARKER]
    if (root / REQUIREMENT_DIGEST_MARKER).exists():
        rels.append(REQUIREMENT_DIGEST_MARKER)
    try:
        subprocess.run(["git", "-C", str(root), "add", *rels],
                       check=True, capture_output=True, text=True)
        subprocess.run(["git", "-C", str(root), "commit",
                        "-m", "board-setup: init approvers.md",
                        "-m", "Subject: board-setup"],
                       check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        sys.exit(f"보드 파일을 커밋하지 못했다: "
                 f"{e.stderr.strip() if e.stderr else e}")
    push = subprocess.run(["git", "-C", str(root), "push"],
                          capture_output=True, text=True)
    if push.returncode != 0:
        sys.exit(f"보드 파일을 커밋했지만 push 하지 못했다 — 이 파일들이 "
                 f"리모트에 올라가기 전까지는 모든 스폰이 board-gate 에 막혀 "
                 f"실패한다: {push.stderr.strip() if push.stderr else push}")
    print(f"보드 파일을 커밋하고 push 했다.")
    return 0


def init_requirement_digest(cwd: str) -> bool:
    """대상 레포에 `docs/specs/requirement-digest.md` 스텁을 만든다
    (issue #1695).

    요구 연결 게이트(`require_requirement_linkage`)는 이슈 본문의 `R\\d+`
    인용만 보고 이 파일 자체를 읽지 않는다 — 새 레포에는 인용할 R-ID가
    아예 없어서 첫 스폰이 막힌다. 이 스텁은 사람이 첫 이슈에 R1 을 바로
    적어 넣을 수 있는 형식 예시를 준다. `gates/requirement_digest.py` 의
    생성기는 재사용하지 않는다 — 그건 `docs/specs/requirements.md` 레지스트리를
    읽어야 하는데, 갓 init 된 레포엔 그 파일도 없다.

    이미 있으면 절대 덮지 않는다 — approvers.md 와 같은 처분.
    """
    root = Path(cwd).resolve()
    dest = root / REQUIREMENT_DIGEST_MARKER
    if dest.exists():
        print(f"이미 있다: {dest}")
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        "# Requirement Digest\n"
        "\n"
        "이 레포가 향하는 살아있는 요구사항 목록. 요구 연결 게이트(issue #1017)는\n"
        "새로 드래프트되는 이슈 본문이 아래 형식의 R-ID를 인용하기를 기대한다.\n"
        "\n"
        "## R-entry format\n"
        "\n"
        "  - R<n>: <한 줄 설명> [<status>] (source: #<issue-number>)\n"
        "\n"
        "예:\n"
        "  - R1: 사용자가 X 를 할 수 있어야 한다 [enforced] (source: #12)\n"
        "\n"
        "## Entries\n"
        "\n"
        "(아직 없음 — 첫 이슈를 드래프트할 때 R1 부터 여기에 추가한다)\n",
        encoding="utf-8")
    print(f"요구 원장 스텁을 만들었다: {dest}")
    return True


def require_board(cwd: str, override: bool) -> None:
    """대상 레포가 보드인지(approvers.md 가 있는지) 본다. 없으면 멈춘다.

    core 의 게이트가 어차피 보드·실행 쓰기를 거부하므로, 세션을 태우기 전에
    같은 사실을 말해주는 것뿐이다 — 버려질 세션에 과금하지 않는다.
    """
    root = Path(cwd).resolve()
    if (root / MARKER).is_file():
        return
    if override:
        return
    sys.exit(
        f"대상 레포에 {MARKER} 가 없다: {root}\n"
        f"  이 파일이 보드 opt-in 이자 승인자 allowlist 다. 만들려면:\n"
        f"    python3 spawn.py init -C {root}\n"
        f"  보드를 안 쓸 작업이면 --no-contract 로 건너뛴다.")


REPO_CONFIG = (".claude/settings.json", ".claude/settings.local.json", ".claude/hooks",
               ".claude/agents", ".mcp.json")


def require_no_repo_config(cwd: str, override: bool) -> None:
    """대상 레포가 자기 Claude 설정을 들고 있으면 멈춘다.

    **on-the-record 의 샌드박스는 이걸 못 막는다.** 설정 우선순위는
    `--settings` > `<레포>/.claude/settings.json` > `~/.claude/settings.json` 인데,
    on-the-record 는 양 끝만 읽고 가운데를 안 본다. 그리고 `hooks` 는 덮어쓰기가 아니라
    **더해지고**, 훅 명령은 선언한 `sandbox.filesystem` 정책을 받지 않는다.

    실측 2026-07-27. `denyWrite` 와 `denyRead` 를 선언한 역할 설정으로 띄웠는데,
    레포가 커밋해 둔 SessionStart 훅이 **denyWrite 경로에 쓰고 denyRead 인
    `~/.claude/settings.json` 을 읽어냈다.** 사용자 권한 그대로, 프롬프트 없이,
    `env={**os.environ}` 을 통째로 들고. 레포를 클론해서 on-the-record 를 겨눈 것만으로
    성립한다.

    계약 파일과 같은 처분을 한다 — 경고가 아니라 정지, 그리고 명시적 opt-out.
    사고가 아니라 결정이 되게.

    신뢰는 **내용 해시에 고정**된다: --trust-repo-config 로 한 번 통과시키면
    그 시점의 .claude/ 내용 다이제스트를 기록하고, 이후 스폰은 내용이 같을
    때만 자동 통과한다. 내용이 바뀌면 다시 멈춘다 — "어제 읽어본 훅"이 아닌
    "오늘 바뀐 훅"이 무검토로 도는 일을 막는다.
    """
    root = Path(cwd).resolve()
    rogue = [p for p in REPO_CONFIG if (root / p).exists()]
    if not rogue:
        return

    import hashlib
    h = hashlib.sha256()
    for rel in sorted(rogue):
        p = root / rel
        h.update(rel.encode())
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file():
                    h.update(str(f.relative_to(p)).encode())
                    h.update(f.read_bytes())
        else:
            h.update(p.read_bytes())
    digest = h.hexdigest()

    # MUSTER_TOKENMAXXXER_HOME: 실제 ~/.tokenmaxxxer 대신 쓸 경로. 테스트가
    # 실제 홈을 건드리지 않고 격리하기 위한 오버라이드(이슈#367) — 기본은
    # 그대로 Path.home().
    home_override = os.environ.get("MUSTER_TOKENMAXXXER_HOME")
    tokenmaxxxer_home = Path(home_override) if home_override else Path.home() / ".tokenmaxxxer"
    pins = tokenmaxxxer_home / "trusted-repo-config.json"
    try:
        table = json.loads(pins.read_text())
    except (OSError, ValueError):
        table = {}
    key = str(root)

    if override:
        table[key] = digest
        pins.parent.mkdir(parents=True, exist_ok=True)
        pins.write_text(json.dumps(table, indent=2))
        print(f"[trust] 레포 설정을 이 내용({digest[:12]})으로 신뢰 고정했다: "
              f"{', '.join(rogue)}", file=sys.stderr)
        return
    if table.get(key) == digest:
        return          # 전에 읽고 신뢰한 그 내용 그대로다

    changed = key in table
    sys.exit(
        f"대상 레포가 자기 Claude 설정을 들고 있다: {', '.join(rogue)}\n"
        f"  {root}\n"
        + ("  전에 신뢰했던 내용에서 **바뀌었다** — 다시 읽어보고 판단해야 한다.\n"
           if changed else "")
        + f"  그 훅들은 on-the-record 가 선언한 샌드박스 경계를 **받지 않는다**. 띄우면\n"
        f"  denyRead 로 막은 경로까지 읽힌다(실측). 내용을 직접 읽어보고,\n"
        f"  믿을 수 있으면 --trust-repo-config 로 명시한다 — 이 내용 해시로\n"
        f"  고정되어, 같은 내용인 동안은 다시 묻지 않는다.")


def require_acceptance_gate(cwd: str, issue: int | None) -> None:
    """issue #441: phase-2 세션은 이슈의 `## Acceptance` 가 실행가능한
    산출물을 가리키지 않으면 아예 안 띄운다(`gates/acceptance_gate.py`,
    issue #310) — 머지 시점이 아니라 세션 시작 전에 거절한다, #424 가 요구한
    "잘못된 상태에서 나가는 배선" 모양 그대로.

    phase 판정은 `gates/ci.py._approved_roles_on_issue` 와 같은 술어를
    쓴다: 승인자 계정의 `APPROVE issue-<n>/<role>` 코멘트가 이슈에 하나라도
    있으면 phase-2(issue #312, phase 는 role 이 아니라 이슈의 속성). phase-1
    이슈는 Acceptance 가 아직 초안 단계이므로 건드리지 않는다.

    `--issue` 없이 스폰하면(보드 밖 작업) 검사할 이슈가 없어 통과시킨다.
    `gh` 조회 실패는 통과가 아니라 차단이다 — 검사 불가를 통과로 읽지
    않는다는 게이트들의 공통 원칙(`acceptance_gate.py`/`ci.py` 동일).
    """
    if issue is None:
        return
    root = Path(cwd).resolve()
    if not (root / MARKER).is_file():
        return  # require_board 가 이미 --no-contract 없이는 여기까지 안 보낸다
    sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
    import ci as _ci
    import acceptance_gate as _acceptance_gate
    approved_roles = _ci._approved_roles_on_issue(root, issue)
    if not approved_roles:
        return  # phase-1: Acceptance 가 아직 초안, 게이트 대상 아님
    bad = _acceptance_gate.check(root, issue)
    if not bad:
        return
    sys.exit(
        f"이슈 #{issue} 는 phase-2 승인({', '.join(sorted(approved_roles))})을 "
        f"받았지만 'Acceptance' 절이 실행가능한 산출물을 가리키지 않는다:\n"
        + "\n".join(f"  - {b}" for b in bad)
        + f"\n  세션을 안 띄운다 — 프로즈만 있는 Acceptance 로는 델리버리를 "
        f"검증할 수 없다(issue #310, #441).")


def require_requirement_linkage(cwd: str, issue: int | None) -> None:
    """issue #1017 (northpole req#6): 이슈가 아직 phase-2 승인을 받지
    않았으면(=드래프트/phase-1 단계) 요구 ID 인용 또는 명시적
    `infrastructure/no-direct-requirement` 태그를 요구한다.
    `require_acceptance_gate` 와 반대 방향의 phase 게이트다 — 그쪽은
    phase-2 승인 **후에만** 발동해 Acceptance 절의 실행가능성을 검사하고,
    이쪽은 phase-2 승인 **전에만**(=아직 새로 드래프트되는 중) 발동해
    요구 연결을 검사한다. 이미 phase-2 승인을 받은 기존 이슈는 이 게이트가
    절대 소급 차단하지 않는다(제안서 제약: "Advisory stays advisory for
    existing issues (no retroactive blocking)").

    두 번째 소급 방지: phase-2 승인 전이라도, 이 이슈로 `issue-<n>/*`
    브랜치가 이미 하나라도 있으면(=이 기능이 생기기 전에 이미 최소 한 번
    스폰돼 phase-1 이 진행 중인 기존 이슈) 새 게이트가 재스폰을 막지
    않는다 — before-landing 워런트 헌트(stance 1)가 실측한 그대로, 이
    조건이 없으면 phase-2 승인만으로 "기존 이슈"를 가려내다가 아직
    미승인인 기존 phase-1 이슈까지 소급 차단해 그 이슈의 애초 phase-1
    세션(요구 연결을 처음 정하는 바로 그 세션)조차 못 띄우는
    닭-달걀 모순이 생긴다. `issue-<n>/*` 브랜치가 전혀 없는 이슈만 "새
    이슈"로 보고 이 게이트를 적용한다.
    """
    if issue is None:
        return
    root = Path(cwd).resolve()
    if not (root / MARKER).is_file():
        return
    sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
    import ci as _ci
    import requirement_linkage as _requirement_linkage
    approved_roles = _ci._approved_roles_on_issue(root, issue)
    if approved_roles:
        return  # phase-2: 이미 승인됐다 — 소급 차단하지 않는다
    br = subprocess.run(
        ["git", "for-each-ref",
         f"refs/heads/issue-{issue}/**", f"refs/remotes/*/issue-{issue}/**"],
        cwd=root, capture_output=True, text=True)
    if br.returncode == 0 and br.stdout.strip():
        return  # 이 이슈로 스폰된 적이 이미 있다(로컬 또는 원격) — 소급 차단하지 않는다
    bad = _requirement_linkage.check(root, issue)
    if not bad:
        return
    sys.exit(
        f"이슈 #{issue} 가 요구 연결이 없다:\n"
        + "\n".join(f"  - {b}" for b in bad)
        + f"\n  세션을 안 띄운다 — 요구 ID(`R\\d+` 또는 'northpole req#<n>')를 "
        f"인용하거나 'infrastructure/no-direct-requirement' 태그를 달아야 "
        f"한다(issue #1017, northpole req#6).")


def _approvers(root: Path) -> set[str]:
    """`docs/specs/approvers.md` 한 줄에 하나씩 적힌 GitHub 로그인."""
    p = root / MARKER
    if not p.is_file():
        return set()
    out = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*-\s*(\S+)", line)
        if m:
            out.add(m.group(1))
    return out


_REPO_SLUG_CACHE: dict[str, str | None] = {}


def _repo_slug_cache_clear() -> None:
    """`_repo_slug` 캐시를 비운다 — 한 프로세스에서 여러 레포나 여러 인증
    상태를 순차로 다루는 테스트용."""
    _REPO_SLUG_CACHE.clear()


def _repo_slug(root: Path) -> str | None:
    """레포 슬러그(`owner/name`). 프로세스 수명 동안 root 별로 캐시한다
    (issue #682).

    슬러그는 체크아웃당 상수다. flows-schema.md §4 는 이 호출을 이미
    "1 call (cached)" 로 계약에 적어뒀는데 구현에 캐시가 없어,
    `closure_sweep` 경로에서 `_fetch_ref_file` 이 subject 마다 다시 불러
    182회 · 94초를 썼다. 이 캐시가 그 계약을 구현으로 옮긴다.

    실패(`None`)도 캐시한다 — `gh` 인증/레포 인식 실패는 이 프로세스
    실행 내내 같은 결과이므로 호출마다 느린 재시도를 반복할 이유가 없다."""
    key = str(root)
    if key not in _REPO_SLUG_CACHE:
        try:
            r = subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner",
                                "-q", ".nameWithOwner"], cwd=root, capture_output=True, text=True)
        except FileNotFoundError:
            # 이슈 #1283: `root` 가 이미 지워진 workspace 일 수 있다(reconcile
            # 이 clean 된 workspace 도 훑는다) — `cwd` 부재로 subprocess 가
            # 죽는 대신 슬러그 조회 실패와 같은 `None`으로 처리한다.
            r = None
        _REPO_SLUG_CACHE[key] = (
            r.stdout.strip() if r is not None and r.returncode == 0 and r.stdout.strip() else None)
    return _REPO_SLUG_CACHE[key]


def _repo_name(root: Path) -> str | None:
    """`_repo_slug`의 owner 뗀 짧은 이름 — ledger 엔트리 귀속용(issue #216)."""
    slug = _repo_slug(root)
    return slug.split("/")[-1] if slug else None


def _pr_for_branch(root: Path, branch: str) -> int | None:
    r = subprocess.run(["gh", "pr", "list", "--head", branch, "--state", "all",
                        "--json", "number", "-q", ".[0].number"],
                       cwd=root, capture_output=True, text=True)
    out = r.stdout.strip()
    return int(out) if r.returncode == 0 and out.isdigit() else None


def _open_pr_for_branch(root: Path, branch: str) -> int | None:
    """`_pr_for_branch`(spawn.py:1071)의 `--state all` 은 브랜치 재사용 시
    이미 머지된 과거 라운드 PR 을 먼저 돌려줄 수 있다 — `_watch`의
    `pr-opened` 판정에 그대로 쓰면 새로 열린 PR 대신 머지된 PR 을
    보고한다(issue #576). 여기선 OPEN 만 센다. `_pr_for_branch` 자체를
    좁히지 않는 이유: `approve_scope`(spawn.py:1225)는 이미 머지된
    phase-1 PR 코멘트에 달린 승인도 찾아야 해서 `--state all`이 필요하다.
    """
    r = subprocess.run(["gh", "pr", "list", "--head", branch, "--state", "open",
                        "--json", "number", "-q", ".[0].number"],
                       cwd=root, capture_output=True, text=True)
    out = r.stdout.strip()
    return int(out) if r.returncode == 0 and out.isdigit() else None


def _pr_open_or_merged_for_branch(root: Path, branch: str) -> int | None:
    """`_pr_for_branch`의 `--state all` 은 머지 없이 닫힌 PR 도 "있음"으로
    센다 — outcome-derivation 의 already_delivered 판정에 그대로 쓰면
    실패한 세션을 delivered 로 오분류한다(issue #484 after-proposal
    hunt). 여기서는 OPEN/MERGED 만 "배달됨"으로 센다.
    """
    r = subprocess.run(["gh", "pr", "list", "--head", branch, "--state", "all",
                        "--json", "number,state"],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        prs = json.loads(r.stdout)
    except ValueError:
        return None
    for pr in prs:
        if pr.get("state") in ("OPEN", "MERGED"):
            return pr.get("number")
    return None


def _merged_pr_for_branch(root: Path, branch: str) -> int | None:
    """`_pr_open_or_merged_for_branch`(spawn.py:1082) 의 MERGED 전용 버전 —
    이슈 #587 §12 event-4(remediation PR merged) 는 OPEN 은 세지 않는다,
    아직 안 끝난 PR 을 merged 로 오탐하면 안 되므로."""
    r = subprocess.run(["gh", "pr", "list", "--head", branch, "--state", "all",
                        "--json", "number,state"],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        prs = json.loads(r.stdout)
    except ValueError:
        return None
    for pr in prs:
        if pr.get("state") == "MERGED":
            return pr.get("number")
    return None


def _open_role_prs(root: Path) -> tuple[list[dict], bool]:
    """열린 `issue-*/` 브랜치 PR 목록. `(prs, ok)` — `ok=False` 는 `gh` 조회
    실패(`_issue_comments`/`_pr_for_branch` 와 같은 튜플 관례, issue #287 S6).
    각 항목은 `number`, `headRefName`, `body`, `url`, 그리고 파싱해 뽑은
    `issue`(int) 를 담는다."""
    slug = _repo_slug(root)
    if not slug:
        return [], False
    r = subprocess.run(["gh", "pr", "list", "--repo", slug, "--state", "open",
                        "--json", "number,headRefName,body,url,createdAt"],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return [], False
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return [], False
    out = []
    for pr in data:
        m = re.match(r"^issue-(\d+)/", pr.get("headRefName", ""))
        if not m:
            continue
        out.append({**pr, "issue": int(m.group(1))})
    return out, True


def _undispositioned_role_prs(root: Path, exclude_issue: int | None = None
                               ) -> tuple[list[dict], bool]:
    """열린 `issue-*/` PR 중 아직 처분(phase-1 승인 또는 phase-2 머지/닫힘)
    되지 않은 것들. phase 판정은 `gates/ci.py._approved_roles_on_issue` 를
    재사용한다 — `_approved_roles_on_issue` 가 비어 있으면 phase-1 미승인,
    있으면 phase-2 진행 중(그 이슈의 phase-2 PR 은 정의상 아직 열려 있으니
    처분 전). `exclude_issue` 와 같은 이슈 번호는 건너뛴다(진행 중인 그
    이슈 자신을 막지 않는다). `(blockers, ok)` — `ok` 는 `_open_role_prs`
    의 실패를 그대로 전파한다.
    """
    prs, ok = _open_role_prs(root)
    if not ok:
        return [], False
    sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
    import ci as _ci
    # 이슈 #1013 block C: 자기 세션이 소유한 로스터 엔트리의 브랜치는
    # 게이트에서 뺀다 — `_roster_own()` 이 이미 고아 엔트리(session_id
    # 없음)는 own-scope 에도 남겨두므로, 그런 엔트리의 브랜치는 여기서도
    # 계속 걸린다(관측-손실 없음).
    own_branches = {key for key in _roster_own(_roster_load(), all_scope=False)}
    blockers = []
    for pr in prs:
        if exclude_issue is not None and pr["issue"] == exclude_issue:
            continue
        if pr.get("headRefName") in own_branches:
            continue
        approved_roles = _ci._approved_roles_on_issue(root, pr["issue"])
        phase = "phase2" if approved_roles else "phase1"
        age_hours = None
        created_at = pr.get("createdAt")
        if created_at:
            try:
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                age_hours = (datetime.now(timezone.utc) - created).total_seconds() / 3600.0
            except ValueError:
                age_hours = None
        blockers.append({**pr, "phase": phase, "age_hours": age_hours})
    return blockers, True


def _print_returned_pr_surfaced(blockers: list[dict], source: str) -> None:
    """이슈 #1239: 처분 안 된 issue-*/ PR 목록을 (issue/phase/age/URL) 로
    찍고 `returned_pr_surfaced` 원장 이벤트를 남긴다 — #680 의 거절 게이트를
    대체하는 무조건적(non-blocking) surfacing. `_spawn_one()` 과
    `roster_watchdog()` 양쪽에서 같은 모양으로 쓰기 위해 뽑았다."""
    if not blockers:
        return
    for b in blockers:
        age = f"{b['age_hours']:.1f}h" if b.get("age_hours") is not None else "?"
        print(f"[returned-pr] issue #{b['issue']} ({b['phase']}): age={age} — {b['url']}")
    ledger_write({"event": "returned_pr_surfaced", "source": source,
                  "issues": [b["issue"] for b in blockers], "ts": int(time.time())})


def _etag_cache_path(root: Path, number: int) -> Path:
    """이슈 #1459: `number` 스레드의 ETag 조건부-재조회 캐시 위치.
    `.git/` 아래(레포별, 워크트리 공유)에 둔다 — 커밋되지 않고, 레포
    삭제/재클론 시 자연히 사라진다."""
    return root / ".git" / "gh-read-cache" / f"issue-{number}-comments.json"


def _approval_record_path(root: Path, number: int) -> Path:
    """이슈 #1818: `number` 이슈의 구조화 승인 레코드 위치 — 기존
    `_etag_cache_path`(comments 캐시)와 같은 `.git/gh-read-cache/`
    컨벤션의 형제 파일. 커밋되지 않고, write-through 캐시로만 쓰인다
    (`gates/ci.py._approved_roles_on_issue` 가 읽고/쓴다)."""
    return root / ".git" / "gh-read-cache" / f"issue-{number}-approvals.json"


def _issue_comments_uncached(root: Path, slug: str, number: int
                              ) -> tuple[list[dict] | None, int]:
    """무조건(non-conditional) 전체 재조회 — fail-open 폴백 경로.
    `per_page=100`(이슈 #1459 요구사항 1)로 페이지 수를 ~3.3배 줄인다.
    반환: (평탄화된 원본 코멘트 리스트 또는 실패시 None, 소모한 호출 수)."""
    r = subprocess.run(["gh", "api", f"repos/{slug}/issues/{number}/comments",
                        "-f", "per_page=100", "--paginate", "--slurp"],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return None, 1
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None, 1
    return [c for page in data for c in page], max(len(data), 1)


def _issue_comments_more_pages(root: Path, slug: str, number: int) -> list[dict] | None:
    """이슈 #1459: 1페이지 조건부 조회가 200 이고 더 있는 것으로 표시될 때
    2페이지부터 무조건(non-conditional) `--paginate --slurp`로 나머지를
    읽는다 — 1페이지는 이미 읽었으니 중복 없이 이어붙인다."""
    r = subprocess.run(["gh", "api", f"repos/{slug}/issues/{number}/comments",
                        "-f", "per_page=100", "-f", "page=2",
                        "--paginate", "--slurp"],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None
    return [c for page in data for c in page]


def _issue_comments(root: Path, number: int) -> tuple[list[dict], bool]:
    """`number` 앞으로 달린 코멘트. GitHub 는 이슈든 PR 이든 같은
    `/issues/<n>/comments` 로 대화 코멘트를 낸다 — PR 리뷰 코멘트가 아니라
    일반 코멘트가 필요하므로 이 엔드포인트로 충분하다.

    이슈 #1459: 첫 페이지(`per_page=100`)를 캐시된 ETag 와 함께
    `If-None-Match` 조건부로 조회한다. GitHub 컬렉션 엔드포인트의 ETag는
    그 쿼리가 반환할 전체 결과 집합을 반영하므로(스레드 어디에 코멘트가
    추가되든 1페이지 ETag가 바뀐다), 1페이지 304 는 "스레드 전체가
    안 변했다"는 신호로 쓸 수 있다 — 그러면 캐시된 전체 본문을 그대로
    돌려주고, 이 재조회는 rate-limit 소모 호출로 세지 않는다(304 는
    카운트되지 않는다는 GitHub 정의 그대로). 200 이면 그 페이지부터
    나머지 페이지를 마저 무조건 읽어 캐시를 갱신한다. 캐시 파일이
    없거나/손상됐거나/쓰기가 실패하면 무조건 전체 재조회로 폴백한다
    (fail-open — 캐시 없이도 항상 정답을 돌려준다는 게 우선이다).

    `(comments, ok)` 를 돌려준다(issue #287 S6) — `ok=False` 는 `gh` 호출
    자체가 실패했다는 뜻이고, 그때 `comments` 는 빈 리스트지만 "코멘트가
    0개"로 읽으면 안 된다: 호출부가 "승인 코멘트가 없다"와 "코멘트를
    못 읽었다"를 구별할 수 있게 하는 게 이 튜플의 존재 이유다.
    """
    slug = _repo_slug(root)
    if not slug:
        return [], False

    cache_path = _etag_cache_path(root, number)
    etag = None
    cached_raw = None
    try:
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            etag = cached.get("etag")
            cached_raw = cached.get("raw")
            if not isinstance(etag, str) or not isinstance(cached_raw, list):
                etag, cached_raw = None, None
    except (OSError, ValueError, UnicodeDecodeError):
        etag, cached_raw = None, None

    # 1페이지를 항상 -i(헤더 포함)로 조회한다 — 캐시된 ETag 가 있으면
    # `If-None-Match` 를 실어 조건부로, 없으면(첫 조회거나 캐시가 깨졌을
    # 때) 조건 없이 그대로 보내 이번 응답의 ETag 를 다음 호출을 위해
    # 캐시에 심는다. 프로브 자체가 실패/파싱불가하면 무조건 전체
    # 재조회로 폴백한다(fail-open).
    cmd = ["gh", "api", f"repos/{slug}/issues/{number}/comments", "--method", "GET",
           "-f", "per_page=100", "-i"]
    if etag:
        cmd = cmd + ["-H", f"If-None-Match: {etag}"]
    r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    if r.returncode == 0:
        status, headers, body = _split_gh_api_i_output(r.stdout)
        if status == 304 and cached_raw is not None:
            return [{"login": c.get("user", {}).get("login", ""),
                      "body": c.get("body", "")} for c in cached_raw], True
        if status == 200:
            try:
                page1 = json.loads(body)
            except ValueError:
                page1 = None
            if isinstance(page1, list):
                raw = page1
                if len(page1) == 100 and "rel=\"next\"" in headers.get("link", ""):
                    more = _issue_comments_more_pages(root, slug, number)
                    if more is not None:
                        raw = page1 + more
                new_etag = headers.get("etag")
                _write_etag_cache(cache_path, new_etag, raw)
                return [{"login": c.get("user", {}).get("login", ""),
                          "body": c.get("body", "")} for c in raw], True

    raw, _n = _issue_comments_uncached(root, slug, number)
    if raw is None:
        return [], False
    return [{"login": c.get("user", {}).get("login", ""), "body": c.get("body", "")}
            for c in raw], True


def _split_gh_api_i_output(stdout: str) -> tuple[int | None, dict[str, str], str]:
    """`gh api -i` 출력(상태줄 + 헤더 + 빈줄 + 바디)을 파싱한다.
    이슈 #1459: ETag 조건부 재조회의 상태 코드/`Etag` 헤더를 읽는 데 쓴다."""
    if "\r\n\r\n" in stdout:
        head, body = stdout.split("\r\n\r\n", 1)
        sep = "\r\n"
    elif "\n\n" in stdout:
        head, body = stdout.split("\n\n", 1)
        sep = "\n"
    else:
        return None, {}, stdout
    lines = head.split(sep)
    status = None
    if lines:
        parts = lines[0].split()
        for p in parts:
            if p.isdigit():
                status = int(p)
                break
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    return status, headers, body


def _write_etag_cache(cache_path: Path, etag: str | None, raw_comments: list[dict]) -> None:
    """이슈 #1459: 새 ETag(있으면) 와 원본 코멘트 목록을 캐시에 쓴다.
    쓰기 실패는 다음 호출을 무조건 재조회로 되돌릴 뿐이므로 조용히
    무시한다(fail-open)."""
    if not etag:
        return
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps({"etag": etag, "raw": raw_comments}),
                               encoding="utf-8")
    except OSError:
        pass


_UPSTREAM_PATH = re.compile(r"^\s*-\s*path:\s*(\S+)", re.M)


def _record_upstream(record: Path) -> dict[str, str]:
    """기록의 `upstream:` 목록에서 path 만 뽑는다 (첫 빌드 판별용).

    frontmatter 의 중첩 블록이라 frontmatter() 의 평면 파서로는 안 잡힌다.
    """
    try:
        text = record.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    block = text.split("---", 2)
    if len(block) < 3:
        return {}
    return {m.group(1): "" for m in _UPSTREAM_PATH.finditer(block[1])}


def _front_role(root: Path, subject: str, roles: dict) -> str | None:
    """그 subject 의 front record — subject 를 처음 연 역할 (첫 빌드 승인 게이트).

    upstream 이 빈 역할이 하나뿐이면 그게 체인 루트다. 못 가리면 관례 순서
    (product, 아니면 feasibility)로 물러난다.
    """
    rootless = [r for r in roles
                if not _record_upstream(root / BOARD / subject / "reports" / f"{r}.md")]
    if len(rootless) == 1:
        return rootless[0]
    for r in ("product-discovery", "technical-feasibility"):
        if r in roles:
            return r
    return None


def approve_scope(cwd: str, issue: int) -> int:
    """s19 의 정확한 문자열 댓글을 승인자 allowlist 로 검증하고, front record 를
    `scope-approved` 로 올리는 커밋을 직접 쓴다 (이슈 #115).

    승인은 여전히 사람의 몫이다 — 이 함수는 그 결정을 **표현하는 방법**(댓글)에서
    **기록에 반영하는 방법**(커밋)으로 옮길 뿐, 어느 역할도 스스로 승인하지
    못한다는 규칙은 그대로 둔다.
    """
    root = Path(cwd).resolve()
    subject = f"issue-{issue}"
    approvers = _approvers(root)
    if not approvers:
        sys.exit(f"승인자 목록이 비어 있다: {root / MARKER}")

    roles = board(root).get(subject)
    if not roles:
        sys.exit(f"{subject} 의 보드 기록이 없다: {root / BOARD / subject / 'reports'}")

    front = _front_role(root, subject, roles)
    if not front:
        sys.exit(f"{subject} 의 front record 를 판별할 수 없다.")

    record_path = root / BOARD / subject / "reports" / f"{front}.md"
    fm = frontmatter(record_path)
    state = fm.get("loop_state")
    if state == "scope-approved":
        print(f"이미 scope-approved 다: {record_path}")
        return 0
    if state != "scope-proposed":
        sys.exit(f"{record_path} 의 loop_state 가 scope-proposed 가 아니다 "
                 f"(지금: {state or '(없음)'}) — 승인 대상이 아니다.")

    needle = f"APPROVE {subject}/scope"
    pr = _pr_for_branch(root, f"{subject}/{front}")
    # 이슈 댓글이 승인 정본이다 — 먼저 본다. PR 댓글은 PR 이 있을 때만 보는
    # fallback 이지 대등한 소스가 아니다(issue-126: 위치 드리프트로 승인을
    # 놓친 사례가 있었다). 순서를 바꾸지 말 것.
    comments, issue_ok = _issue_comments(root, issue)
    pr_ok = True
    if pr:
        pr_comments, pr_ok = _issue_comments(root, pr)
        comments += pr_comments
    match = next((c for c in comments
                  if c["body"].strip() == needle and c["login"] in approvers), None)
    if not match:
        where = f"이슈 #{issue}" + (f" 또는 PR #{pr}" if pr else "")
        if not issue_ok or not pr_ok:
            sys.exit(f"이슈/PR 코멘트를 읽지 못했다 ({where}) — gh 호출이 실패했다. "
                     f"승인 코멘트가 없는지조차 확인할 수 없다.")
        sys.exit(f"승인 코멘트를 못 찾았다: 정확히 \"{needle}\" 를 "
                 f"{', '.join(sorted(approvers))} 중 한 계정이 {where} 에 달아야 한다.")

    text = record_path.read_text(encoding="utf-8")
    new_text = re.sub(r"(?m)^loop_state:.*$", "loop_state: scope-approved", text, count=1)
    if new_text == text:
        sys.exit(f"{record_path} 에서 loop_state 줄을 찾지 못해 고치지 못했다.")
    record_path.write_text(new_text, encoding="utf-8")

    # git add/commit 이 중간에 실패하면(정체성 없음, 훅 거부, 락, 디스크 없음)
    # 파일은 scope-approved 인데 커밋은 없는 상태가 남는다 — 다음 호출이
    # idempotency 가드(state == "scope-approved")에 걸려 커밋 없이 성공을
    # 보고한다(실측: warrant-hunter, 2026-07-30). 파일 쓰기를 되돌려 그 상태를
    # 만들지 않는다.
    rel = str(record_path.relative_to(root))
    try:
        subprocess.run(["git", "-C", str(root), "add", rel],
                       check=True, capture_output=True, text=True)
        subprocess.run(["git", "-C", str(root), "commit", "-m",
                        f"{subject}: scope-approved (approved by {match['login']} "
                        f"via spawn.py approve-scope)"],
                       check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        record_path.write_text(text, encoding="utf-8")
        sys.exit(f"커밋 실패 — 기록을 되돌렸다({record_path}), 다시 시도해도 된다: "
                 f"{e.stderr.strip() if e.stderr else e}")

    print(f"{subject}: {front} 기록을 scope-approved 로 올리고 커밋했다 — "
          f"{match['login']} 의 승인. push 는 별도로 한다.")
    return 0


def frontmatter(p: Path) -> dict[str, str]:
    """맨 앞 `---` 블록만 얕게 읽는다. 값의 트레일링 주석은 떼어낸다 —
    계약 §2: 주석을 허용하지 않는 파서는 **게이트 결함이지 기록의 위반이 아니다**."""
    try:
        text = p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    body = text.split("---", 2)
    if len(body) < 3:
        return {}
    out = {}
    for line in body[1].splitlines():
        k, sep, v = line.partition(":")
        if sep and k.strip() and not k.startswith((" ", "-", "\t")):
            out[k.strip()] = v.split("#")[0].strip()
    return out


def board(root: Path) -> dict[str, dict[str, dict[str, str]]]:
    """Read the board: subject (issue-<n>) -> role -> frontmatter (v3 s10).

    A subject is a docs/issue-<n>/ tree; role records sit in its reports/.
    """
    docs = root / BOARD
    if not docs.is_dir():
        return {}
    found = {}
    for d in sorted(p for p in docs.iterdir() if p.is_dir()):
        if not d.name.startswith("issue-"):
            continue
        if not re.match(r"^issue-[0-9]+$", d.name):
            print(f"board: 숫자가 아닌 issue-* 디렉터리라 보드에서 뺀다: "
                  f"{d.name}", file=sys.stderr)
            continue
        rep = d / "reports"
        roles = {r: frontmatter(rep / f"{r}.md") for r in ROLES
                 if (rep / f"{r}.md").is_file()}
        if roles:
            found[d.name] = roles
    return found


def status(cwd: str) -> list[str]:
    """보드를 **읽는다**. 쓰지 않는다 (protocol.md §1).

    상태는 에이전트의 것이다. on-the-record 가 이걸 고치기 시작하면 룰북의 전이 게이트를
    우회하게 된다 — 게이트는 기록 쓰기를 가로채 막지만, 그 파일을 밖에서 고치면
    문지기를 안 거친다.
    """
    root = Path(cwd).resolve()
    out = [f"프로젝트: {slug(cwd)}   경로: {root}"]

    if not (root / MARKER).is_file():
        out.append(f"⚠ {MARKER} 없음 — 보드 opt-in 이자 승인자 allowlist 다. "
                   f"`spawn.py init` 으로 만든다.")
    b = board(root)
    if b:
        for subject, roles in b.items():
            out.append(f"subject: {subject}")
            for r in ROLES:
                fm = roles.get(r)
                if fm is None:
                    continue
                bits = [f"loop_state: {fm.get('loop_state', '(없음)')}"]
                if fm.get("verdict"):          # feasibility. coding 이 여기 깨어난다(§3)
                    bits.append(f"verdict: {fm['verdict']}")
                out.append(f"  [{r}] " + "   ".join(bits))
            missing = [r for r in ROLES if r not in roles]
            if missing:
                out.append(f"  (기록 없음: {', '.join(missing)})")
        return out

    # 보드가 없다. "아무 일도 없다"와 "옛 자리에 있다"는 정반대 처분을 받아야 한다.
    stale = sorted(r for r, name in LEGACY.items()
                   if (root / name).exists() or (root / "docs" / name).exists())
    if stale:
        out.append(f"보드 없음. 계약 v1 자리에 기록이 있다: {', '.join(stale)}")
        out.append("  이 레포는 v3 이전 판이다. v3 는 docs/issue-<n>/reports/<역할>.md 다.")
    else:
        out.append("보드 없음 (docs/issue-<n>/). 아직 아무 역할도 기록을 쓰지 않았다.")
    return out


def _base(cwd: str) -> str:
    """비교 기준 ref. origin/HEAD 가 가리키는 기본 브랜치를 우선 쓴다."""
    p = subprocess.run(["git", "-C", cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
                       capture_output=True, text=True)
    if p.returncode == 0 and p.stdout.strip():
        return p.stdout.strip()
    for cand in ("origin/main", "origin/master"):
        if subprocess.run(["git", "-C", cwd, "rev-parse", "--verify", "-q", cand],
                          capture_output=True).returncode == 0:
            return cand
    return "origin/main"          # 없으면 그대로 실패시켜 "검사 불가"로 보고한다


def gate_report(cwd: str) -> list[str]:
    """세션이 무엇을 건드렸는지 결정론적으로 본다. LLM 0회.

    **막지는 않는다.** 세션이 끝난 뒤라 되돌릴 수 없고, on-the-record 는 판정하지 않는다.
    대신 조용히 넘어가지도 않는다 — 보호 경로(인증·시크릿·마이그레이션·CI 설정)를
    건드렸거나 실재하지 않는 패키지를 넣었으면 사람이 알아야 한다.

    게이트가 못 돌아도 그것을 "이상 없음"으로 말하지 않는다. 검사 불가와 통과는
    정반대 처분을 받아야 한다는 게 게이트의 원칙이고, 보고에도 같이 적용된다.
    """
    sys.path.insert(0, str(ROOT / "gates"))
    try:
        import ci, gates
        # 비교 기준을 레포에서 찾는다. origin/main 을 고정하면 기본 브랜치가
        # master·develop 인 레포에서 매번 "검사 불가"가 뜨고, 그러면 게이트가
        # 있으나 마나가 된다.
        gates.BASE = os.environ.get("GATE_BASE") or _base(cwd)
        bad = ci.check(Path(cwd).resolve())
    except Exception as e:                       # git 아님, base 부재, import 실패 등
        return [f"[게이트] 검사 불가 — {type(e).__name__}: {str(e)[:120]}"]
    return ["[게이트] 이상 없음"] if not bad else \
           ["[게이트] 확인 필요:"] + [f"  - {b}" for b in bad]


def ownership_report(cwd: str, role: str, delta: list) -> list[str]:
    """이 세션이 **자기 것이 아닌** 보드 경로를 건드렸는지 사후로 본다.

    세션 안에서는 룰북과 core 의 게이트가 막는다. 이건 그 게이트가 어떤
    이유로든 안 돌았을 때 흔적이라도 남기려는 것이다 — 새 훅이 trap 을
    빠뜨려 fail-open 이 되거나, 룰북 하나가 아직 마이그레이션 안 됐거나.
    막지는 않는다(이미 쓴 뒤다). 대신 조용히 넘어가지도 않는다.
    """
    bad = []
    for p in delta:
        m = re.match(r"^docs/(issue-[0-9]+)/reports/(.+)$", p)
        if not m:
            continue
        rest = m.group(2)
        if rest == f"{role}.md" or rest.startswith(f"{role}/"):
            continue
        if role == "technical-feasibility" and rest.startswith("spikes/"):
            continue
        if role == "release-engineering" and rest.startswith("postmortems/"):
            continue
        bad.append(f"  - {p} (다른 역할의 기록)")
    if not bad:
        return []
    return [f"[소유권] {role} 이 자기 것이 아닌 보드 경로를 건드렸다 — "
            f"세션 안의 게이트가 안 돌았다는 뜻이다 (계약 §11):"] + bad


def _git_head(cwd: str) -> str | None:
    """현재 HEAD 커밋. 아직 커밋이 없는 새 레포면 None (에러로 취급하지
    않는다 — 커밋이 없는 상태도 유효한 시작점이다)."""
    c = subprocess.run(["git", "-C", cwd, "rev-parse", "HEAD"],
                       capture_output=True, text=True)
    return c.stdout.strip() if c.returncode == 0 else None


def _is_new_commit(cwd: str, before_head: str | None, after_head: str | None) -> bool:
    """`after_head` 가 `before_head` 위에 실제로 새 커밋을 얹었는지 판단한다.

    단순히 `after_head != before_head` 로는 부족하다 — 기존에 있던 브랜치나
    커밋으로 체크아웃만 해도 HEAD 는 바뀌지만 새 커밋은 없다. before_head 가
    after_head 의 조상(ancestor)인지까지 확인해야 "진짜 새 커밋"이라고 말할 수
    있다. before_head 가 None (아직 커밋이 없던 새 레포)이면 after_head 가
    있는 것만으로 새 커밋이다.
    """
    if after_head is None:
        return False
    if before_head is None:
        return True
    if before_head == after_head:
        return False
    c = subprocess.run(
        ["git", "-C", cwd, "merge-base", "--is-ancestor", before_head, after_head],
        capture_output=True, text=True,
    )
    return c.returncode == 0


def board_snapshot(cwd: str) -> dict[str, str]:
    """보드 파일들의 내용 해시. 세션 전후를 비교해 §6 의 '바뀐 보드'를 잰다.

    git 이 아니라 파일 내용을 재는 이유: 세션이 커밋했든 안 했든 바뀐 것은
    바뀐 것이고, 계약 §6 의 단위는 커밋이 아니라 보드다.
    """
    base = Path(cwd).resolve()
    docs = base / BOARD
    if not docs.is_dir():
        return {}
    out: dict[str, str] = {}
    for d in sorted(docs.glob("issue-*")):
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*")):
            if p.is_file():
                out[str(p.relative_to(base))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def session_result(stdout: str) -> dict:
    """--output-format json 의 결과 오브젝트. 파싱 불가면 빈 dict — 모르는
    것을 성공으로 취급하지 않는다."""
    try:
        got = json.loads(stdout)
        return got if isinstance(got, dict) else {}
    except ValueError:
        return {}


# issue #476 round 3, candidate E (refusal-cost-parity). 등록된 refusal/
# null-result 어휘만 인정한다 — 자유 문장이 아니라 이 닫힌 집합과 정확히
# 일치해야 한다("REFUSAL: <state> — <reason>" 형태), 그래야 역할 세션이
# 임의 텍스트로 스스로를 이 경로에 밀어넣지 못한다. rounds 1-2 의
# loop_state 어휘(H2)와 issue #983 의 role-session 변형에서 이미 쓰는
# 이름들을 재사용한다 — 새 어휘를 이 라운드가 새로 발명하지 않는다.
REGISTERED_NULL_RESULT_STATES = frozenset({
    "hypothesis-not-falsifiable",
    "evidence-log-unreadable",
    "nothing-to-do",
})

_NULL_RESULT_RE = re.compile(
    r"(?m)^REFUSAL:\s*(?P<state>[a-z0-9-]+)\s*—\s*(?P<reason>\S.*)$"
)


def _null_result_declared(result: dict) -> str | None:
    """`result["result"]` 최종 텍스트에서 등록된 REFUSAL 선언을 찾는다.

    이슈 #476 라운드 3, candidate E 의 게이밍-저항 근거: 세션이 쓸 수 있는
    자유 텍스트가 아니라 `REGISTERED_NULL_RESULT_STATES` 라는 닫힌 집합과
    정확히 일치하는 토큰만 인정한다 — 세션이 아무 문구나 써서 이 경로로
    스스로를 밀어넣을 수 없다. 실패 신호: 이 집합 밖의 새 loop_state 가
    실제로 필요해지면(다른 플러그인이 새 refusal 어휘를 등록하면) 이 상수를
    갱신하지 않는 한 그 세션은 조용히 다시 `silent-failure` 로 떨어진다 —
    그래서 이 목록은 코드 리뷰에서 다른 플러그인의 loop_state 어휘 변경과
    함께 갱신 대상으로 다뤄야 한다.
    """
    text = result.get("result")
    if not isinstance(text, str):
        return None
    m = _NULL_RESULT_RE.search(text)
    if not m:
        return None
    state = m.group("state")
    if state not in REGISTERED_NULL_RESULT_STATES:
        return None
    return state


def classify(rc: int, result: dict, delta: list, blocked: list) -> str:
    """세션 하나의 처분. 판정하지 않는다 — 이름만 붙인다 (보고 전용).

    순서가 곧 의미다. 보드가 움직였으면 일부가 막혔어도 그 run 은
    progressed 이고(거부 건수는 따로 찍힌다), 사람 게이트가 서 있으면 그게
    가장 행동 가능한 사실이다.

    refused 와 silent-failure 를 가르는 이유: 게이트가 막아서 아무것도 안
    바뀐 것은 **시스템이 작동한 것**이고, 아무것도 안 바뀌었는데 막힌 것도
    없는 것은 아무도 이유를 모르는 것이다. 실측 2026-07-27 — reflect 를
    띄웠더니 룰북 게이트가 §20 필수 섹션 없음을 이유로 쓰기를 거부했고,
    세션은 그 이유를 또렷이 말하고 끝났는데 분류는 '침묵-사망'이라고 했다.
    이 레포의 원칙("검사 불가와 이상 없음은 정반대 처분을 받아야 한다")이
    여기에도 그대로 적용된다.

    `refused-null-result` (issue #476 round 3, candidate E): 위와 같은
    도구-거부(permission_denials) 없이, 세션이 등록된 REFUSAL 어휘로
    "이 작업은 애초에 할 게 없었다/검증 불가였다"를 명시적으로 선언하고
    끝난 경우. 지금까지는 이 경로가 `silent-failure`(죽은 세션과 동일
    라벨)로 떨어져 있었다 — 이슈 #476 이 지목한 바로 그 비대칭: "정직한
    거부/무결과 보고가 조용한 죽음과 똑같이 실패로 읽힌다." 이 라벨은
    별도 카운터로만 쓰인다(§ fail_closed_downgrade 는 이 라벨을 건드리지
    않는다) — 커밋/PR 없이도 "실패"로 깎이지 않는다는 게 이 후보의
    전부다.
    """
    if rc != 0 or result.get("is_error"):
        return "errored"
    if delta:
        return "progressed"
    if blocked:
        return "waiting-on-human"
    if result.get("permission_denials"):
        return "refused"
    if _null_result_declared(result) is not None:
        return "refused-null-result"
    return "silent-failure"


# 이슈 #1124: `spawn.py clean` 이 세션 로그를 지워도 되는지 판단할 때
# `fail_closed_downgrade` 가 실제로 확정하는, "커밋이 origin 에 닿았다"는
# 라벨 두 개만 "landed" 로 친다. 그 외(refused/errored/silent-failure 등)는
# 유일한 증거인 로그를 지우지 않고 archive 한다.
LANDED_OUTCOMES = {"progressed", "progressed-dirty-tree"}


def _ledger_log_outcomes() -> dict[str, str]:
    """`runs/ledger.jsonl` 을 `{log 경로: 마지막 outcome}` 으로 접는다.
    파일이 없으면 빈 dict — clean 은 ledger 없이도 동작해야 한다(빈 상태)."""
    p = ROOT / "runs" / "ledger.jsonl"
    out: dict[str, str] = {}
    if not p.is_file():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        log = entry.get("log")
        outcome = entry.get("outcome")
        if log and outcome:
            out[log] = outcome
    return out


def session_end_verdict(work: str, log_path: Path | None, now: float | None = None,
                        alive_fn=None) -> str:
    """워크스페이스 하나의 세션-종료 3분법: `normal` / `crashed` / `stalled` /
    `in-progress` (이슈 #132).

    `<work>.events.jsonl` 에서 마지막 `session-start` 를 찾고, 그 뒤에
    `session-end` 가 이미 왔는지부터 본다 — 죽었다고 보고된 pid 가 사실은
    그 찰나에 정상 종료했을 수도 있는 벤인 레이스를, `_alive()` 보다 먼저
    확인해 `normal` 로 되돌린다. 매치가 없을 때만 `_alive()`/로그 mtime 을
    본다.

    `log_path` 는 호출자가 넘긴다 — 이 함수가 스스로 고정 접미사로
    재구성하면 세대별로 고유해진 로그 명명 규약(이슈 #192,
    `_session_log_path()`)을 놓친다.
    """
    now = time.time() if now is None else now
    alive_fn = _alive if alive_fn is None else alive_fn
    events_path = _events_path(work)
    if not events_path.exists():
        return "normal"
    events = []
    for line in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if isinstance(ev, dict):
            events.append(ev)
    start_idx = None
    for i in range(len(events) - 1, -1, -1):
        if events[i].get("type") == "session-start":
            start_idx = i
            break
    if start_idx is None:
        return "normal"
    if any(ev.get("type") == "session-end" for ev in events[start_idx + 1:]):
        return "normal"
    detail = events[start_idx].get("detail") or {}
    pid = detail.get("pid")
    if not alive_fn(pid):
        return "crashed"
    if log_path is not None and log_path.exists():
        silent_min = (now - log_path.stat().st_mtime) / 60
        if silent_min > WATCHDOG_SILENCE_MIN:
            return "stalled"
    return "in-progress"


def fail_closed_downgrade(outcome: str, issue: int | None, blocked: list,
                          new_commit: bool, uncommitted: list,
                          already_delivered: bool = False,
                          push_succeeded: bool = False) -> str:
    """`classify()` 뒤에 붙는 별도 단계 — git 상태로 `progressed` 를
    검증한다. `classify()` 자체는 손대지 않는다: git 상태를 모르고, 기존
    계약(rc/result/delta/blocked)과 기존 테스트를 그대로 둔다.

    `issue is not None` 스폰만 대상이다 — 전용 git 워크스페이스가 있는
    경로만 커밋 여부를 검사할 수 있다.

    `blocked` 를 먼저 확인한다 (hunt-phase1 발견 반영): `classify()` 는
    delta 를 blocked 보다 먼저 보므로, 보드가 움직였고 동시에 사람 게이트가
    아직 서 있는 run 은 오늘도 "progressed" 로 분류된다. 그런 run 을 커밋이
    없다고 FAILED 로 깎으면 정직한 blocked 신호를 완전히 지워버린다 — 그래서
    `blocked` 가 비어있지 않으면 이 다운그레이드는 아예 건드리지 않는다.

    `already_delivered` (issue #129 phase 2): 이 세션 자신의 before→after
    HEAD 델타만 보면, 같은 브랜치에서 이전 phase 가 이미 커밋+PR 을 남긴
    뒤 이번 세션이 검증만 하고 새 커밋 없이 끝난 경우를 "실패"로 오분류한다
    — 브랜치에 이미 PR 이 있다는 사실을 호출부에서 확인해 넘긴다. 미커밋
    변경이 남아있으면(더러운 트리) 여전히 다운그레이드한다: "이미 배달됨" 이
    "이번 세션이 남긴 새 변경도 안전하다"를 의미하지 않는다.

    `silent-failure` 업그레이드 (issue #484): `classify()` 는 docs 보드
    델타만 보므로, 이미 배달된 작업 위에 재실행되어 아무것도 할 게 없던
    세션이나 docs 밖(코드) 커밋만 남긴 세션은 델타가 비어 `silent-failure`
    로 잡힌다. 여기서도 `already_delivered`/`new_commit`+push-성공 사실은
    `classify()` 의 원판정과 무관하게 그대로 유효하므로, 같은 신호로
    `silent-failure` 를 끌어올린다 — `progressed` 경로의 다운그레이드
    로직과 대칭이지만 방향이 반대다.
    """
    if outcome == "silent-failure" and issue is not None and not blocked:
        if uncommitted:
            return outcome
        if already_delivered:
            return "progressed"
        if new_commit and push_succeeded:
            return "progressed"
        return outcome
    if outcome != "progressed" or issue is None:
        return outcome
    if blocked:
        return outcome
    if new_commit and uncommitted:
        return "progressed-dirty-tree"
    if uncommitted:
        return "failed-no-commit"
    if new_commit or already_delivered:
        return outcome
    return "failed-no-commit"


def _recovery_policy_module():
    """`gates/recovery_policy.py` 를 지연 import 한다 — 다른 `gates.*` 지연
    import 자리(예: 라인 1667)와 같은 패턴."""
    sys.path.insert(0, str(ROOT / "gates"))
    import recovery_policy
    return recovery_policy


def _reconcile_pr_expected_missing(expected: dict, observed: dict, verdict: str | None,
                                    recovery_state_dir: Path | None = None) -> list[dict]:
    """이슈 #1678: `pr-expected-missing` 죽음을 무조건 `respawn` 으로
    이름 붙이던 걸 `recovery_policy.classify_from_state()` 의 판정으로
    바꾼다 — cap 과 실패-서명 반복을 보고 ESCALATE 할지, 커밋 유무로
    RESPAWN_IDENTICAL/RESPAWN_WITH_HANDOFF 를 가릴지 결정한다.

    `expected["issue"]` 가 없으면(카운터를 걸 (issue, role) 이 없음) 상태
    파일을 건드리지 않고 커밋 유무만으로 즉시 판정한다 — 기존
    `test_expects_pr_missing_not_in_progress_is_respawn` 류처럼 `issue`
    없이 부르는 순수-비교 호출부는 여전히 상태 I/O 없이 동작한다.
    """
    role = expected.get("role")
    branch = expected.get("branch")
    issue = expected.get("issue")
    has_commit = bool(observed.get("new_commit"))
    failure_signature = observed.get("failure_signature")
    death_id = observed.get("death_id")
    base_detail = (f"role={role} branch={branch}: "
                   f"expects_pr=True pr_number=None session_verdict={verdict!r}")

    if issue is not None and role:
        recovery_policy = _recovery_policy_module()
        kwargs = {}
        if recovery_state_dir is not None:
            kwargs["state_dir"] = recovery_state_dir
        policy_verdict = recovery_policy.classify_from_state(
            issue, role, has_commit=has_commit, has_pr=False,
            failure_signature=failure_signature, death_id=death_id, **kwargs)
    else:
        policy_verdict = ("RESPAWN_WITH_HANDOFF" if has_commit
                           else "RESPAWN_IDENTICAL")

    if policy_verdict == "ESCALATE":
        return [{
            "kind": "pr-expected-missing",
            "detail": f"{base_detail} policy=ESCALATE (cap reached or repeat failure signature)",
            "next_action": "manual-review",
        }]
    return [{
        "kind": "pr-expected-missing",
        "detail": f"{base_detail} policy={policy_verdict}",
        "next_action": "respawn",
        "handoff": policy_verdict == "RESPAWN_WITH_HANDOFF",
    }]


def reconcile(expected: dict, observed: dict, recovery_state_dir: Path | None = None) -> list[dict]:
    """이슈-492 step 2 (ADR: `docs/issue-492/decisions/2026-08-08-reconciliation-step-for-supervision.md`).

    순수 함수: 로스터/보드/PR/git 에서 이미 읽은 값을 받아 비교만 한다 —
    여기서 새 `gh` 호출을 하지 않는다. 예외 하나(이슈 #1678): `pr-expected-missing`
    가지에서 `expected["issue"]` 가 있으면 `recovery_policy.classify_from_state()`
    를 불러 per-(issue, role) 재기동 카운터를 읽고 쓴다 — 이건 `gh`/git 재조회가
    아니라 이 reconcile 자신의 판정 상태이므로 순수성 취지(외부 세계 재조회
    없음)는 유지된다.

    `expected = {"expects_pr": bool, "role": str, "branch": str, "issue": int|None}`
    `observed = {"session_verdict": str, "pr_number": int|None,
                 "loop_state": str|None, "new_commit": bool,
                 "failure_signature": str|None}`

    반환: `[{"kind": str, "detail": str, "next_action": str}, ...]` —
    divergence 없으면 빈 리스트. next_action 집합은 닫혀 있다: `respawn`,
    `resume-watch`, `manual-review`, `none` 뿐 (ADR Decision 3).

    규칙 순서(이슈의 실측 예시 그대로):
    1. `session_verdict == "crashed"` → `respawn` — kill -9 등으로 세션이
       죽었는데 침묵하지 않는다.
    2. `session_verdict == "stalled"` → `resume-watch` — #132 의 관찰-전용
       standing decision 그대로, 자동 재무장은 안 하고 이름만 붙인다.
    3. PR 을 기대했는데(`expects_pr`) 아직 없고(`pr_number is None`) 세션이
       진행 중도 아니면(`session_verdict != "in-progress"`) → `respawn` —
       이슈의 "push 없이 죽음" 예시.
    4. 위 어디에도 안 걸리는데 입력 자체가 앞뒤가 안 맞으면(예:
       `loop_state` 는 있는데 `session_verdict` 가 없거나 인식 불가) →
       `manual-review` — 침묵 대신 사람 검토로 보낸다.
    5. 그 외엔 divergence 없음(빈 리스트) — 깨끗한 경우.
    """
    verdict = observed.get("session_verdict")
    known_verdicts = ("normal", "crashed", "stalled", "in-progress")

    if verdict == "crashed":
        return [{
            "kind": "session-crashed",
            "detail": f"role={expected.get('role')} branch={expected.get('branch')}: "
                       "session_verdict=crashed",
            "next_action": "respawn",
        }]
    if verdict == "stalled":
        return [{
            "kind": "session-stalled",
            "detail": f"role={expected.get('role')} branch={expected.get('branch')}: "
                       "session_verdict=stalled",
            "next_action": "resume-watch",
        }]
    if (expected.get("expects_pr") and observed.get("pr_number") is None
            and verdict != "in-progress"):
        return _reconcile_pr_expected_missing(expected, observed, verdict,
                                               recovery_state_dir=recovery_state_dir)
    # 이슈 #1678 review D2: PR 이 존재하거나 세션이 정상 종료로 끝난
    # 건강한 (issue, role) 은 재기동 카운터를 초기화한다 — 아니면 일시적
    # flake 두 번이 이후의 진짜 죽음까지 영구히 ESCALATE 로 몰아간다.
    _issue = expected.get("issue")
    _role = expected.get("role")
    if _issue is not None and _role and (
            observed.get("pr_number") is not None or verdict == "normal"):
        recovery_policy = _recovery_policy_module()
        kwargs = {}
        if recovery_state_dir is not None:
            kwargs["state_dir"] = recovery_state_dir
        recovery_policy.reset_state(_issue, _role, **kwargs)
    if verdict is None:
        if observed.get("loop_state") is not None:
            # loop_state 는 관측됐는데 session_verdict 가 없다 — 앞뒤가
            # 안 맞는 입력, 침묵 대신 사람 검토로 보낸다.
            return [{
                "kind": "inconsistent-observed-state",
                "detail": f"role={expected.get('role')} branch={expected.get('branch')}: "
                           f"session_verdict=None loop_state={observed.get('loop_state')!r}",
                "next_action": "manual-review",
            }]
        return []
    if verdict not in known_verdicts:
        return [{
            "kind": "inconsistent-observed-state",
            "detail": f"role={expected.get('role')} branch={expected.get('branch')}: "
                       f"session_verdict={verdict!r} loop_state={observed.get('loop_state')!r}",
            "next_action": "manual-review",
        }]
    return []


def _build_expected(entry: dict) -> dict:
    """로스터 엔트리 → `reconcile()` 의 `expected` 입력. 새 스키마 없음 —
    `roster_register()` 가 이미 쓰는 필드(`role`, `expects_pr`)와 워크
    경로에서 도출한 브랜치 이름만 쓴다."""
    work = entry.get("work")
    branch = Path(work).name if work else None
    return {
        "expects_pr": bool(entry.get("expects_pr")),
        "role": entry.get("role"),
        "branch": branch,
        "issue": entry.get("issue"),
    }


def _build_observed(root: Path, entry: dict) -> dict:
    """로스터 엔트리 → `reconcile()` 의 `observed` 입력. 기존 리더만 쓴다
    (`session_end_verdict`, `_pr_open_or_merged_for_branch`, `board`,
    `_is_new_commit`) — 새 `gh` 호출을 추가하지 않는다."""
    work = entry.get("work")
    log = entry.get("log")
    verdict = session_end_verdict(work, Path(log) if log else None) if work else None
    branch = Path(work).name if work else None
    pr_number = _pr_open_or_merged_for_branch(root, branch) if branch else None
    loop_state = None
    issue = entry.get("issue")
    role = entry.get("role")
    if issue is not None and role:
        subject = f"issue-{issue}"
        loop_state = board(root).get(subject, {}).get(role, {}).get("loop_state")
    new_commit = False
    if work:
        after_head = _git_head(work)
        new_commit = _is_new_commit(work, entry.get("before_head"), after_head)
    return {
        "session_verdict": verdict,
        "pr_number": pr_number,
        "loop_state": loop_state,
        "new_commit": new_commit,
        "death_id": entry.get("ts"),
    }


ROSTER = STATE_ROOT / "active.json"


@contextlib.contextmanager
def _roster_locked():
    """runs/active.json 의 load-mutate-save 구간을 프로세스 간에 직렬화한다."""
    lock_path = ROSTER.with_name(ROSTER.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def _roster_load() -> dict:
    try:
        return json.loads(ROSTER.read_text())
    except (OSError, ValueError):
        return {}


def _roster_save(d: dict) -> None:
    ROSTER.parent.mkdir(parents=True, exist_ok=True)
    ROSTER.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def _roster_own(d: dict, all_scope: bool) -> dict:
    """이슈 #1013: 로스터 딕셔너리를 호출자 자신의 세션으로 좁힌다.
    `all_scope=True` 면 그대로 돌려준다(`--all`). 그 외에는
    `ORCHESTRATOR_SESSION_ID_ENV` 로 얻은 자기 세션 id 와 엔트리의
    `session_id` 가 같은 것만 남긴다 — 둘 다 `None` 이면(오늘의
    단일-세션/미설정 상태) 같다고 본다(empty-state parity). 다른
    세션이 소유한(둘 다 `None` 이 아니고 다른) 엔트리는 걸러지지만,
    소유자를 특정할 수 없는 고아 엔트리(`session_id` 가 `None` 인데
    자기 세션 id 는 있는 쪽)는 계속 관측 대상에 남긴다 — 관측-손실
    금지 불변식(observation-loss invariant)."""
    if all_scope:
        return d
    own = os.environ.get(ORCHESTRATOR_SESSION_ID_ENV) or None
    out = {}
    for key, e in d.items():
        sid = e.get("session_id")
        if sid == own or sid is None:
            out[key] = e
    return out


def _watcher_looks_real(pid: int, issue: int | None,
                         role: str | None = None) -> bool:
    """이슈 #488 before-landing hunt 발견: `_alive()` 만으로는 워처가 죽은
    뒤 OS 가 같은 pid 를 다른 프로세스에 재할당한 경우를 못 잡는다 — 살아는
    있지만 그 워처가 아니다. `issue` 를 알면(로스터 엔트리가 준다)
    `/proc/<pid>/cmdline` 이 실제로 이 이슈의 `watch` 호출인지까지 최선
    노력으로 확인한다. `/proc` 없는 플랫폼이나 `issue` 를 모르는 호출(adhoc
    스폰)에서는 `_alive()` 로 저하한다 — 표시적 신원 검사가 리눅스 전용
    기능이라 그 이상은 판단 불가.

    이슈 #559 after-proposal hunt 발견: `issue` 만 보면 같은 이슈의 *다른*
    역할이 무장한 살아있는 워처를 이 역할의 워처로 오인한다 — `role` 을
    넘기면 cmdline 에 그 문자열도 있어야 한다."""
    if not _alive(pid):
        return False
    if issue is None:
        return True
    cmdline_path = Path(f"/proc/{pid}/cmdline")
    if not cmdline_path.exists():
        return True
    try:
        parts = cmdline_path.read_bytes().decode("utf-8", "replace").split("\x00")
    except OSError:
        return True
    if "watch" not in parts or str(issue) not in parts:
        return False
    if role is not None and role not in parts:
        return False
    return True


def _alive(pid: int) -> bool:
    # 이슈 #1462: `os.kill(0, 0)` 은 pid 0 이 아니라 호출자 자신의 프로세스
    # 그룹에 신호를 보내 항상 성공한다 — roster 엔트리의 `pid` 가 없거나
    # 0(세션-종료~재스폰 갭)이면 이 함수가 거짓으로 "살아있음"을 돌려줘
    # `ps` 가 `RUNNING pid 0` 을 그린다. 음수/0 pid 는 애초에 살아있는
    # 프로세스를 가리킬 수 없으니 커널 호출 전에 걸러낸다.
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def roster_register(key: str, entry: dict) -> None:
    with _roster_locked():
        d = _roster_load()
        d[key] = entry
        _roster_save(d)


def roster_remove(key: str) -> None:
    with _roster_locked():
        d = _roster_load()
        if d.pop(key, None) is not None:
            _roster_save(d)


def _format_roster_row(key: str, e: dict, ws_idx: dict,
                        now: float | None = None) -> tuple[bool, list[str]]:
    """`key`/`e`(로스터 엔트리 하나) 를 `ps` 출력 줄 목록으로 순수하게
    변환한다 — 부수효과(roster_remove 등) 없음, 테스트가 실제 프로세스를
    띄우지 않고 합성 상태로 직접 부를 수 있는 지점 (이슈 #1462).

    돌려주는 `bool` 은 "살아있음" — 호출자가 정리 대상 여부를 판단하는 데
    쓴다. 행 하나는 자기 자신의 `work`/`log` 필드만 표시한다 — 다른
    키(`ws_idx` 포함)의 값으로 대체하는 폴백은 어디에도 없다(행 격리
    불변식, requirement 3)."""
    now = time.time() if now is None else now
    pid = e.get("pid")
    pid = pid if isinstance(pid, int) else 0
    alive = _alive(pid)
    if "ts" in e and isinstance(e.get("ts"), (int, float)):
        age = f"{(int(now) - int(e['ts'])) // 60}분"
    else:
        # 이슈 #1462: ts 가 없으면 epoch(0) 을 기준으로 나이를 계산하지
        # 않는다 — "29778226분" 처럼 터무니없는 나이를 찍던 버그.
        age = "unknown"
    pid_disp = pid if pid else "unknown"
    if alive:
        state = "RUNNING"
    else:
        # 이슈 #1462 requirement 2: 세션-종료~재스폰 갭은 RUNNING/pid 0 이
        # 아니라 truthful terminal state(마지막으로 알려진 pid 를 들고)로
        # 보여야 한다.
        state = "ENDED"
    lines = [
        f"{state:14s} {e.get('role','?'):12s} issue-{e.get('issue','?')}  "
        f"{age}  pid {pid_disp}",
        f"               log: {e.get('log','')}",
        f"               work: {e.get('work','')}",
    ]
    work = e.get("work")
    ws_key = f"{_repo_identity(work)}/{key}" if work else key
    ws_entry = ws_idx.get(ws_key)
    watcher_pid = ws_entry.get("watcher_pid") if ws_entry else None
    role = key.split("/", 1)[1] if "/" in key else None
    if watcher_pid is None:
        lines.append("               워처: UNWATCHED")
    elif not alive:
        # 이슈 #1462 requirement 4: 세션이 정상 종료해서 이 행 자체가 이미
        # ENDED 이면, 워처의 by-design 동반 종료를 DEAD 로 오라벨하지
        # 않는다 — 그건 세션이 살아있는데 워처만 죽은 경우의 라벨이다.
        lines.append(f"               워처: exited-with-session (pid {watcher_pid})")
    elif _watcher_looks_real(watcher_pid, e.get("issue"), role):
        armed_at = ws_entry.get("watcher_armed_at")
        armed_mins = (int(now) - int(armed_at)) // 60 \
            if armed_at is not None else "?"
        own_sid = os.environ.get(ORCHESTRATOR_SESSION_ID_ENV) or None
        sid = e.get("session_id")
        if sid is not None and sid != own_sid:
            # 이슈 #1013 block E: 워처가 살아있어도 이 워처를 무장한
            # 세션이 나(호출자)와 다르면 로컬 소유를 암시하지 않는다.
            lines.append(f"               워처: pid {watcher_pid}  "
                         f"armed {armed_mins}분 전  (다른 세션 소유)")
        else:
            lines.append(f"               워처: pid {watcher_pid}  "
                         f"armed {armed_mins}분 전  follow=True")
    else:
        lines.append(f"               워처: DEAD(pid {watcher_pid})")
    return alive, lines


def roster_ps() -> int:
    """돌고 있는 역할 세션들. 죽은 항목은 표시 후 정리한다.

    이슈 #559: 각 살아있는 세션마다 붙은 워처(있으면)를 함께 보여준다 —
    "워처가 무장됐는지 죽었는지 바깥에서 알 방법이 없다"는 관찰에 대한
    응답. `ROSTER`(`issue-<n>/<role>` 키)와 `WORKSPACE_INDEX`(레포 접두사
    포함 키)를 `_watch`/`watchdog_check_one`과 같은 방식으로 조인한다."""
    d = _roster_load()
    if not d:
        print("돌고 있는 역할 세션 없음")
        return 0
    ws_idx = _workspace_index_load()
    dead = []
    for key, e in sorted(d.items()):
        alive, lines = _format_roster_row(key, e, ws_idx)
        for line in lines:
            print(line)
        if not alive:
            dead.append(key)
    for k in dead:
        roster_remove(k)
    return 0


RECONCILE_LEDGER = ROOT / "runs" / "reconcile_ledger.json"
# 이슈 #782 step 2: 이벤트 채널과 폴링 채널이 같은 완료/헬스 신호를 각자
# 관측해도 next-action 은 한 번만 나가야 한다(멱등 reconcile) — 프로포절의
# TTL 근거: WATCHDOG_SILENCE_MIN/WATCHDOG_NO_COMMIT_MIN 보다 짧게 잡아,
# 15분 안에 다시 폴링 틱이 돌아도 이미 찍힌 키는 조용히 넘어간다.
RECONCILE_LEDGER_TTL_SEC = 15 * 60


def _reconcile_ledger_lock_path() -> Path:
    return RECONCILE_LEDGER.with_name(RECONCILE_LEDGER.name + ".lock")


@contextlib.contextmanager
def _reconcile_ledger_locked():
    lock_path = _reconcile_ledger_lock_path()
    lock_path.parent.mkdir(exist_ok=True)
    with open(lock_path, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def _reconcile_ledger_load() -> dict:
    try:
        return json.loads(RECONCILE_LEDGER.read_text())
    except (OSError, ValueError):
        return {}


def _reconcile_ledger_save(d: dict) -> None:
    RECONCILE_LEDGER.parent.mkdir(exist_ok=True)
    RECONCILE_LEDGER.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def ledger_check_and_stamp(dedup_key: str, now: float | None = None,
                            ttl: float = RECONCILE_LEDGER_TTL_SEC) -> bool:
    """`dedup_key` 가 지난 `ttl` 초 안에 이미 찍힌 적 없으면 True(=행동해도
    됨, 지금 찍는다), 있으면 False(=이미 처리됐다, 침묵) 를 돌려주며 항상
    락을 잡고 read-modify-write 한다 — 이벤트 채널과 폴링 채널이 같은
    completion/health 를 동시에 봐도 next-action 이 한 번만 나가게 하는
    유일한 관문(이슈 #782 Acceptance test 3)."""
    now = time.time() if now is None else now
    with _reconcile_ledger_locked():
        d = _reconcile_ledger_load()
        last = d.get(dedup_key)
        due = last is None or (now - last) >= ttl
        if due:
            d[dedup_key] = now
            _reconcile_ledger_save(d)
        return due


def ledger_stamp(dedup_key: str, now: float | None = None) -> None:
    """조건 없이 찍기만 한다 — `_spawn_one()` 의 이벤트-발신 지점에서
    completion 을 이미 확정적으로 안 순간 쓴다. 이후 같은 키로 도착하는
    폴링 틱의 `ledger_check_and_stamp()` 는 TTL 안이면 False 를 받아
    조용히 넘어간다(Acceptance test 2: watch 가 먼저 잡은 완료를 폴링이
    다시 보고하지 않는다)."""
    with _reconcile_ledger_locked():
        d = _reconcile_ledger_load()
        d[dedup_key] = time.time() if now is None else now
        _reconcile_ledger_save(d)


POLL_STATE = ROOT / "runs" / "poll_state.json"
POLL_INTERVAL_SEC = 60  # 이슈 #782 스코프-확장(operator, 2026-08-11): 15분은 stall/deadlock 포착이 너무 늦다 — 1분


def poll_due(now: float | None = None, poll_state: Path = POLL_STATE,
             interval: float = POLL_INTERVAL_SEC) -> bool:
    """`spawn.py poll-due` (이슈 #782 req #7): `runs/poll_state.json` 의
    마지막 폴 시각을 원자적으로 확인+갱신한다. True 를 돌려주면 그 호출이
    바로 '지금 폴링 틱을 돌려도 된다'는 허가이자 갱신 — `directive.sh`
    가 매 턴 `UserPromptSubmit` 훅에서 부르므로, 같은 1분 창 안의 다음
    호출들은 False 를 받아 백그라운드 `watchdog` 를 또 띄우지 않는다."""
    now = time.time() if now is None else now
    lock_path = poll_state.with_name(poll_state.name + ".lock")
    lock_path.parent.mkdir(exist_ok=True)
    with open(lock_path, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            try:
                st = json.loads(poll_state.read_text())
            except (OSError, ValueError):
                st = {}
            last = st.get("last_poll")
            due = last is None or (now - last) >= interval
            if due:
                st["last_poll"] = now
                poll_state.parent.mkdir(exist_ok=True)
                poll_state.write_text(json.dumps(st, ensure_ascii=False))
            return due
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


WATCHDOG_STATE = ROOT / "runs" / "watchdog_state.json"
WATCHDOG_SILENCE_MIN = 90     # 이슈 #90 proposal, signal 1
WATCHDOG_NO_COMMIT_MIN = 71   # 이슈 #90 proposal, signal 4 (0.5 * p90 ≈ 142.6)
WATCHDOG_DENIAL_THRESHOLD = 3 # 이슈 #90 proposal, signal 3
WATCHDOG_HEARTBEAT_ONLY_MIN = 18  # 이슈 #1966, signal 7: 하트비트만-성장 관측 창(분)
_DELEGATION_RE = re.compile(
    r"run_in_background|백그라운드|delegate|background worker", re.IGNORECASE)


def _watchdog_state_load() -> dict:
    try:
        return json.loads(WATCHDOG_STATE.read_text())
    except (OSError, ValueError):
        return {}


def _watchdog_state_save(d: dict) -> None:
    WATCHDOG_STATE.parent.mkdir(exist_ok=True)
    WATCHDOG_STATE.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def _classify_log_lines_heartbeat_only(text: str, now: float,
                                        window_min: float = WATCHDOG_HEARTBEAT_ONLY_MIN
                                        ) -> str:
    """이슈 #1966: `text`(로그 스캔 구간)를 줄 단위 JSONL 로 구조적 파싱해
    최근 `window_min`분간의 타임스탬프 있는 활동이 `tool_progress`
    하트비트 줄만으로 이뤄져 있는지 판정한다 — `_count_structural_denials()`
    (spawn.py:3614)와 같은 구조적 파싱 관용(파싱 실패 줄은 조용히 건너뜀)을
    따른다, 단어/정규식 매치가 아니다.

    반환: `"heartbeat-only"`(창 안 타임스탬프 있는 활동이 하나 이상 있고
    전부 `tool_progress`), `"healthy"`(창 안에 substantive 줄이 하나라도
    있거나 창 안에 타임스탬프 있는 활동이 아예 없음), `"unmeasurable"`(스캔
    구간 전체에 `tool_progress` 태그가 단 하나도 없어 — 이 트랜스크립트가
    애초에 하트비트를 찍는 종류인지 판별할 근거가 없음 — 조용히 STALLED로
    오판하지 않고 명시적으로 "판정 불가"를 돌려준다)."""
    timestamped: list[tuple[float, bool]] = []
    saw_heartbeat_tag = False
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if not isinstance(obj, dict):
            continue
        ts_raw = obj.get("timestamp")
        if not isinstance(ts_raw, str):
            continue
        try:
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).timestamp()
        except ValueError:
            continue
        is_heartbeat = obj.get("type") == "tool_progress"
        if is_heartbeat:
            saw_heartbeat_tag = True
        timestamped.append((ts, is_heartbeat))
    if not saw_heartbeat_tag:
        return "unmeasurable"
    window_start = now - window_min * 60
    in_window = [is_hb for ts, is_hb in timestamped if ts >= window_start]
    if in_window and all(in_window):
        return "heartbeat-only"
    return "healthy"


def watchdog_check_one(key: str, entry: dict, now: float | None = None,
                       state: dict | None = None) -> list[str]:
    """이슈 #90 phase-2: 살아있는 세션 하나에 대해 관찰만 하는(observe-only)
    이상 신호 목록을 돌려준다. 세션의 프로세스·프롬프트·워크트리는 건드리지
    않는다 — 로그 mtime/내용, 로스터 필드, git 상태만 읽는다.

    `state` 를 넘기면 그 dict 를 제자리에서 갱신하고 저장하지 않는다(테스트
    용). 생략하면 `runs/watchdog_state.json` 을 읽고 쓴다.
    """
    now = time.time() if now is None else now
    anomalies: list[str] = []
    log_path = Path(entry["log"]) if entry.get("log") else None
    work = entry.get("work")
    ts = entry.get("ts", 0)
    elapsed_min = (now - ts) / 60

    # signal 1: 로그 무응답 — 프로포절 §Anomaly-signal-list #1
    if log_path is not None and log_path.exists():
        mtime = log_path.stat().st_mtime
        silent_min = (now - mtime) / 60
        if silent_min > WATCHDOG_SILENCE_MIN:
            anomalies.append(
                f"log-silence: {int(silent_min)}분째 로그 무응답 ({log_path})")

    # 마지막 스캔 이후 새로 쓰인 로그 내용만 본다 — 신호 2/3
    own_state = state if state is not None else _watchdog_state_load()
    st = own_state.get(key, {"offset": 0})
    text = ""
    start_offset = st.get("offset", 0)
    new_offset = start_offset
    if log_path is not None and log_path.exists():
        # 로그가 이전 스캔 오프셋보다 짧아졌다면 그 사이 세션이 재시작되며
        # 로그가 truncate 된 것이다(spawn 은 같은 경로를 "w" 로 다시 연다) —
        # 옛 오프셋을 그대로 쓰면 새 세션의 신호 2/3 이 로그가 옛 길이를
        # 다시 넘어설 때까지 조용히 못 잡힌다. 이 경우 처음부터 다시 읽는다.
        if log_path.stat().st_size < start_offset:
            start_offset = 0
        with log_path.open("r", encoding="utf-8", errors="replace") as fh:
            fh.seek(start_offset)
            raw = fh.read()
            # 이슈 #994 구조적 파싱은 줄 단위 JSON 이라 마지막 줄이 쓰기
            # 도중(같은 spawn 프로세스가 다음 이벤트를 쓰는 사이) 잘려 있으면
            # 그 스캔에서는 그냥 건너뛴다 — 하지만 offset 을 파일 끝까지
            # 밀어버리면 다음 틱은 그 뒤부터 읽으므로 잘렸던 줄이 영영
            # 다시 오지 않는다(실제 거부가 그 줄에 있었다면 영구 유실).
            # 마지막 줄바꿈까지만 커밋하고 미완성 꼬리는 다음 스캔에 남긴다.
            if raw and not raw.endswith("\n"):
                split_at = raw.rfind("\n")
                committed = raw[:split_at + 1] if split_at != -1 else ""
            else:
                committed = raw
            text = committed
            fh.seek(start_offset)
            fh.read(len(committed))
            new_offset = fh.tell()
    own_state[key] = {"offset": new_offset}
    if state is None:
        _watchdog_state_save(own_state)

    # signal 2: 백그라운드-위임 언급 — 시점 무관, 매치 즉시 신고
    if _DELEGATION_RE.search(text):
        anomalies.append(f"background-delegation-phrasing: {log_path}")

    # signal 3: 반복된 거부된 도구 호출 (이번 스캔 구간 내) — 이슈 #994:
    # 단어 매치가 아니라 구조적 tool_result/is_error 만 센다.
    new_denials = _count_structural_denials(text)
    if new_denials >= WATCHDOG_DENIAL_THRESHOLD:
        anomalies.append(
            f"denied-tool-calls: 이번 스캔 구간에 {new_denials}건")

    # signal 7 (이슈 #1966): mtime 은 계속 움직이지만(log-silence 는 안 잡힘)
    # 최근 WATCHDOG_HEARTBEAT_ONLY_MIN 분간 tool_progress 하트비트 줄만
    # 기록된 경우 — advisory 전용, STALLED 는 아니다(diagnose_health 에서
    # 별도 서브상태로 분리).
    hb_status = _classify_log_lines_heartbeat_only(text, now)
    if hb_status == "heartbeat-only":
        anomalies.append(
            f"heartbeat-only-growth: 최근 {WATCHDOG_HEARTBEAT_ONLY_MIN}분간 "
            f"tool_progress 하트비트만 기록됨 ({log_path})")

    # signal 4: 반환점 지났는데 커밋 없음 — 이슈 스코프 스폰만 (before_head 필요)
    before_head = entry.get("before_head")
    if work and before_head and elapsed_min > WATCHDOG_NO_COMMIT_MIN:
        r = subprocess.run(
            ["git", "-C", str(work), "rev-list", "--count",
             f"{before_head}..HEAD"],
            capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip() == "0":
            anomalies.append(
                f"no-commits-late: {int(elapsed_min)}분 경과, "
                f"{before_head} 이후 커밋 0건")

    # signal 5 (이슈 #488): 자동 무장한 워처가 죽었거나 애초에 없으면 신고한다
    # — 죽은 워처는 조용히 넘어가면 auto-arm 의 요구("워처 없는 스폰 불가")를
    # 관측 시점에서 다시 어기는 셈이라, watchdog 틱마다 여기서 잡는다.
    ws_key = f"{_repo_identity(work)}/{key}" if work else key
    ws_entry = _workspace_index_load().get(ws_key)
    if ws_entry is not None:
        watcher_pid = ws_entry.get("watcher_pid")
        watcher_role = key.split("/", 1)[1] if "/" in key else None
        if watcher_pid is None:
            anomalies.append(f"watcher-missing: {key} 에 등록된 워처가 없다")
        elif not _watcher_looks_real(watcher_pid, entry.get("issue"), watcher_role):
            anomalies.append(
                f"watcher-dead: 워처 pid {watcher_pid} 가 죽어 있거나(또는 다른 "
                f"프로세스가 그 pid 를 물려받았거나) — spawn.py watch --issue "
                f"<n> --role <role> --rearm 로 재무장하라 (non-blocking)")
        else:
            # signal 6 (이슈 #782): 워처 pid 는 살아 있고 신원도 진짜인데
            # (_watcher_looks_real 통과) 워처 자신의 로그가 무장 이후로
            # mtime 이 안 움직인다 — 2026-08-11 실측 실패 모드(첫 줄에서
            # 멈춘 watch --follow): pid 는 살아 있어 watcher-dead 로는
            # 안 잡힌다. `watcher_armed_at` 을 못 읽으면(구 로스터 엔트리)
            # 판정하지 않는다 — 없는 기준선으로 조용한 오탐을 내지 않는다.
            armed_at = ws_entry.get("watcher_armed_at")
            watcher_log = Path(str(work) + ".watcher.log") if work else None
            if armed_at is not None and watcher_log is not None and watcher_log.exists():
                w_mtime = watcher_log.stat().st_mtime
                silence_min = (now - max(w_mtime, float(armed_at))) / 60
                if silence_min > WATCHDOG_SILENCE_MIN:
                    anomalies.append(
                        f"watcher-silent: 워처 pid {watcher_pid} 는 살아 있지만 "
                        f"{int(silence_min)}분째 로그 무응답 ({watcher_log}) — "
                        f"spawn.py watch --issue <n> --role <role> --rearm 로 "
                        f"재무장하라 (non-blocking)")

    return anomalies


_HEALTH_REFUSAL_TYPES = ("gate-refusal", "harness-refusal", "sandbox-refusal")
DEADLOCK_MIN_REPEATS = 3  # 스코프-확장 코멘트: "짧은 간격으로 반복" 최소 재현 횟수


def _deadlock_signature(work: str | None, min_repeats: int = DEADLOCK_MIN_REPEATS
                         ) -> str | None:
    """`work` 워크스페이스의 `.events.jsonl` 꼬리를 읽어, 마지막
    `progress` 이벤트(있으면) 이후로 같은 거부/게이트-거부 signature 가
    `min_repeats` 번 이상 반복됐으면 그 signature 문자열을, 아니면 None
    을 돌려준다 — DEADLOCKED 판정의 유일한 근거(이슈 #782 스코프-확장
    코멘트: "같은 에러/거부 signature 가 짧은 간격으로 반복, 새 진행
    이벤트 없음"). 순수 읽기: 이벤트 파일에 아무것도 쓰지 않는다."""
    if not work:
        return None
    events_path = _events_path(work)
    if not events_path.exists():
        return None
    events = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if isinstance(ev, dict):
            events.append(ev)
    last_progress_ts = max(
        (e.get("ts", -1) for e in events if e.get("type") == "progress"),
        default=-1)
    tail = [e for e in events
            if e.get("type") in _HEALTH_REFUSAL_TYPES and e.get("ts", -1) > last_progress_ts]
    if len(tail) < min_repeats:
        return None
    sigs = [json.dumps(e.get("detail"), sort_keys=True, ensure_ascii=False)
            for e in tail[-min_repeats:]]
    if len(set(sigs)) == 1:
        return sigs[0]
    return None


def _pr_state_from_index(pr_index: dict, branch: str) -> int | None:
    """이슈 #1508 요구 2: `closure_sweep._pr_index_all()`(gates/closure_sweep.py:91)
    이 이미 만든 브랜치->{number,state} 벌크 인덱스에서 OPEN/MERGED 만
    "배달됨"으로 센다 — `_pr_open_or_merged_for_branch()`(spawn.py:1162)와
    같은 시맨틱을 별도 `gh` 호출 없이 재현한다."""
    pr = pr_index.get(branch)
    if pr is None:
        return None
    return pr.get("number") if pr.get("state") in ("OPEN", "MERGED") else None


def diagnose_health(key: str, entry: dict, root: Path = ROOT,
                     now: float | None = None, state: dict | None = None,
                     anomalies: list[str] | None = None,
                     pr_index: dict | None = None) -> dict:
    """이슈 #782 스코프-확장, 이슈 #1966 확장: 살아있는(또는 방금 죽은) 로스터
    엔트리 하나를 HEALTHY/STALLED/STALLED-HEARTBEAT-ONLY(advisory)/
    DEADLOCKED/DEAD-ERRORED 다섯 상태 중 하나로 진단하고
    next-action 을 매긴다. 완료(정상 session-end + PR)는 이 함수의 대상이
    아니다 — `roster_watchdog()`의 기존 completion 경로가 다룬다; 여기는
    "완료가 아닌데 뭐가 문제인가"만 답한다.

    반환: `{"state": str, "next_action": str, "detail": str}`. 완료로
    판정되면(죽었는데 verdict=="normal" 이거나 PR 이 있음) `state` 는
    `None` — 호출부가 그 경우를 건너뛴다는 신호.

    원자료(raw ground truth)만 쓴다: `_alive()`(raw ps), 세션 로그
    mtime/내용(`watchdog_check_one()`), `_pr_open_or_merged_for_branch()`
    — 새 `gh`/git 호출 타입을 추가하지 않는다(프로포절 제약).

    `anomalies`: 호출부가 같은 틱에서 이미 `watchdog_check_one()` 을
    돌렸으면 그 결과를 넘긴다 — `watchdog_check_one()` 은 로그 오프셋
    상태를 소비하는 부수효과가 있어(signal 2/3), 한 틱에 두 번 부르면
    두 번째 호출이 빈 텍스트만 보고 신호를 놓친다. 생략하면(단독/테스트
    호출) 이 함수가 직접 한 번 돌린다.

    `pr_index`: 이슈 #1508 요구 2 — 호출부가 같은 틱에서 이미
    `closure_sweep._pr_index_all()` 벌크 조회를 돌렸으면 그 인덱스를
    넘긴다. 넘기면 dead-entry PR 확인이 `_pr_state_from_index()`로
    인덱스만 보고 끝나 이 호출에서 `gh`를 안 부른다. 생략하면(단독/테스트
    호출, 또는 벌크 조회를 아직 안 도는 호출부) 기존
    `_pr_open_or_merged_for_branch()` 개별 `gh pr list` 로 되돌아간다."""
    now = time.time() if now is None else now
    pid = entry.get("pid", 0)
    work = entry.get("work")
    branch = Path(work).name if work else None
    alive = _alive(pid)
    if not alive:
        verdict = session_end_verdict(
            work, Path(entry["log"]) if entry.get("log") else None, now=now) \
            if work else None
        if branch is None:
            pr_number = None
        elif pr_index is not None:
            pr_number = _pr_state_from_index(pr_index, branch)
        else:
            pr_number = _pr_open_or_merged_for_branch(root, branch)
        if verdict == "normal" or pr_number is not None:
            return {"state": None, "next_action": "none",
                    "detail": "completion, not a health diagnosis"}
        return {"state": "DEAD-ERRORED", "next_action": "respawn",
                "detail": f"{key}: pid {pid} 부재, PR 없음, "
                          f"session_verdict={verdict!r}"}
    deadlock_sig = _deadlock_signature(work)
    if deadlock_sig is not None:
        return {"state": "DEADLOCKED", "next_action": "surface-repeating-cause",
                "detail": f"{key}: 같은 거부 signature 반복, 새 진행 없음 — {deadlock_sig[:200]}"}
    if anomalies is None:
        anomalies = watchdog_check_one(key, entry, now=now, state=state)
    if any(a.startswith("log-silence") or a.startswith("watcher-silent")
           for a in anomalies):
        return {"state": "STALLED", "next_action": "resume-watch",
                "detail": f"{key}: idle > {WATCHDOG_SILENCE_MIN}분, RUNNING"}
    if any(a.startswith("heartbeat-only-growth") for a in anomalies):
        # 이슈 #1966: log-silence 는 안 잡히지만(mtime 계속 갱신) 최근
        # WATCHDOG_HEARTBEAT_ONLY_MIN 분간 tool_progress 하트비트만 관측된
        # 경우 — advisory 전용 서브상태. next_action 은 STALLED 와 동일하게
        # "resume-watch"(재관찰만) 로, kill/spawn-거부/게이트-블록 경로는
        # 이 상태에서 전혀 도달 불가하다.
        return {"state": "STALLED-HEARTBEAT-ONLY", "next_action": "resume-watch",
                "detail": f"{key}: 최근 {WATCHDOG_HEARTBEAT_ONLY_MIN}분간 "
                          f"tool_progress 하트비트만 관측, RUNNING (advisory)"}
    return {"state": "HEALTHY", "next_action": "none",
            "detail": f"{key}: 최근 로그 성장, RUNNING"}


def _session_resume_claim(session_id: str, now: float | None = None) -> bool:
    """이슈 #878: `session_id` 하나에 대해 지난
    `SESSION_RESUME_CLAIM_TTL_SEC` 안에 이미 resume-invoke 를 찍은 적
    없으면 True(=지금 이 호출이 그 유일한 소유자, 찍는다), 있으면
    False(=이미 다른 엔트리가 같은 세션을 깨웠다, 침묵) — `spawn.py
    poll-due` 가 이미 쓰는 원자적 체크+스탬프(ledger_check_and_stamp)를
    그대로 락으로 재사용한다(hunt 발견: session_id 는 엔트리가 아니라
    프로세스 단위라 별도 키 네임스페이스가 필요하다)."""
    return ledger_check_and_stamp(
        f"session-resume:{session_id}", now=now, ttl=SESSION_RESUME_CLAIM_TTL_SEC)


def _resume_orchestrator_session(session_id: str, nudge: str,
                                  cwd: str | None = None) -> subprocess.Popen | None:
    """이슈 #878 케이스 2: 이미 `end_turn` 으로 끝난 헤드리스 오케스트레이터
    프로세스 그 자체는 인프로세스로 되살릴 수 없다(생존해 있는 프로세스가
    하나도 없다) — `claude -p "<nudge>" --resume "<session_id>"` 로 새
    프로세스를 띄우는 것이 유일한 경로다(survey 인용:
    code.claude.com/docs/en/headless.md "Background tasks at exit"). 그
    새 턴이 verify→merge→rebuild/re-check→`final_report` 를 스스로
    수행한다 — 이 함수는 그 턴을 놓는 것만 하고 기다리지 않는다(watchdog
    틱을 블록하지 않는다는 기존 observe-only 계약과 동일).

    `claude` 실행 파일이 없거나(테스트/부분 설치 환경) Popen 자체가
    실패하면 None — 호출부가 UNMEASURED-shaped 로 보고할 신호.

    이슈 #886: `--permission-mode` 를 안 주면(또는 `acceptEdits` 를 주면)
    이 재개 턴은 파일 편집만 자동승인되고 Bash(`gh pr merge`, `git
    fetch`, `spawn.py`)는 그대로 거부된다 — `acceptEdits` 는 편집 전용
    이지 Bash 자동승인이 아니다(PR #885 실측, `.permission_denials`).
    `bypassPermissions` 는 #700 이 실제 롤 스폰 경로에 이미 쓰는 것과
    같은 헤드리스 기본값이며, 여는 것은 호스트 권한 프롬프트뿐이다 —
    PreToolUse 훅으로 걸린 게이트(gh-write-allow-gate.sh,
    merge-allow-gate.sh, deliverable-guard)는 이 모드와 무관하게 여전히
    실행된다. 단, 정확한 경계 하나: 이 훅들은 "allow" 만 내고 "deny"
    는 내지 않는 설계라, 자기 허용목록 밖의 셰이프(예: `gh repo delete`,
    `git push --force`)에 대해서는 원래 host 기본-거부에 기대고 있었다
    — bypassPermissions 아래서는 그 기본-거부 자체가 없다(issue #886
    hunt 실측, docs/issue-886/reports/implementation/
    hunt-issue-886-permission-mode-fix.md). 이는 #700 이 이미 프로덕션
    롤 스폰에 쓰는 동일 모드의 기존 속성이며, 이 diff 가 새로 만든
    회귀는 아니다."""
    try:
        return subprocess.Popen(
            ["claude", "-p", nudge, "--resume", session_id,
             "--permission-mode", "bypassPermissions"],
            cwd=cwd, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        # issue #910 finding #1: a Popen failure here (e.g. the `claude`
        # binary is missing/unspawnable) was previously indistinguishable
        # from the ordinary claim-skip path in _maybe_resume_for_ready_pr —
        # both returned False with no roster/record trace. Record it here
        # so the caller's event carries the real cause.
        return ("popen-failed", str(exc))


def _maybe_resume_for_ready_pr(key: str, entry: dict, pr_number: int) -> bool:
    """이슈 #878: 죽은(=역할 세션이 끝난) roster 엔트리가 PR 을 남겼을 때,
    그 스폰을 무장한 오케스트레이터가 headless 세션이었다면(`session_id`
    가 찍혀 있으면) `--resume` 으로 그 세션을 재개해 merge→rebuild/
    re-check→`final_report` 턴을 잇는다. 인터랙티브 세션(`session_id`
    없음)은 케이스 1 의 라이브 `watch --follow` notify 경로가 이미
    맡으므로 여기서는 아무것도 하지 않는다(중복 트리거 방지).

    반환: 실제로 resume 를 쐈으면 True, 건너뛰었으면(session_id 없음/이미
    다른 엔트리가 같은 세션을 깨움/Popen 실패) False.

    이슈 #910 finding #1: Popen 실패와 claim-skip 은 이전에는 둘 다
    아무 기록 없이 False 로 수렴했다 — 어느 쪽인지 events.jsonl 에 남긴다."""
    session_id = entry.get("session_id")
    if not session_id:
        return False
    work = entry.get("work")
    events_path = _events_path(work) if work else None
    if not _session_resume_claim(session_id):
        if events_path is not None:
            _append_event(events_path, "resume-skipped-claimed",
                          {"session_id": session_id, "pr_number": pr_number})
        return False
    nudge = (f"delegated PR #{pr_number} ({key}) is ready — verify, merge, "
             f"rebuild/re-check, and emit the 4-part final_report.")
    proc = _resume_orchestrator_session(session_id, nudge, cwd=work)
    if isinstance(proc, tuple) and proc[0] == "popen-failed":
        if events_path is not None:
            _append_event(events_path, "resume-attempt-failed",
                          {"session_id": session_id, "pr_number": pr_number,
                           "reason": proc[1]})
        return False
    return proc is not None


_REQ_ID_RE = re.compile(r"\bR(\d+)\b")
_NORTHPOLE_REQ_RE = re.compile(r"northpole\s+req\s*#\s*(\d+)", re.IGNORECASE)


def _requirement_drift_cache_path(root: Path) -> Path:
    return root / "runs" / "requirement_drift_cache.json"


def _load_requirement_drift_cache(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_requirement_drift_cache(path: Path, data: dict) -> None:
    # issue #1688: same atomic temp+rename pattern as
    # gates/gh_delta.py::_atomic_write_json (that helper is module-private,
    # so this is a small local duplicate rather than reaching into it).
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".req-drift-", suffix=".tmp")
    except OSError:
        return
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp_name, path)
    except OSError:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass


def _fetch_issue_or_pr_via_cache(root: Path, number: int) -> dict | None:
    """issue #1688: single-number detail fetch for delta-mode
    requirement-drift rechecks, routed through `gates.gh_cache.cached_get`
    (shared ETag cache, #1682) rather than a bare `gh` call."""
    slug = _repo_slug(root)
    if not slug:
        return None
    sys.path.insert(0, str((ROOT / "gates").resolve()))
    import gh_cache
    data, ok, _billed = gh_cache.cached_get(f"repos/{slug}/issues/{number}", root=root)
    if not ok or not isinstance(data, dict):
        return None
    return data


def requirement_drift(root: Path, changed_numbers: set[int] | None = None) -> None:
    """이슈 #930 (northpole req#6): digest 에 살아있는(=stale 아닌) 요구
    각각이 열린 이슈/PR 중 최소 하나에서 언급되는지, 그리고 열린
    proposal/PR 이 요구 ID 를 하나라도 인용하는지 점검한다. `_board_wide_sweep`
    의 `accumulation_trend()` 와 같은 계약 — 결과를 출력만 하고
    `anomaly_count` 에는 절대 합산하지 않는다(advisory, non-blocking).
    `gh` 실패는 조용히 건너뛴다(watch 계열 불가침 원칙 — 이 스윕 자체는
    블로킹 게이트가 아니라 이 함수도 그 계약을 넘지 않는다). 틱당 비용은
    O(열린 이슈/PR 수) + O(digest 요구 수) — `accumulation_trend()` 가 같은
    틱에서 이미 지불하는 것과 같은 자릿수.

    이슈 #1688: `changed_numbers` 가 주어지면(델타 모드) 그 번호들만
    `gates.gh_cache.cached_get` 으로 다시 조회하고, 나머지는
    `runs/requirement_drift_cache.json` 에 저장된 이전 판정용 본문을 그대로
    재사용한다 — `None` 이면(기본) 기존처럼 열린 이슈/PR 전체를 재훑는다."""
    digest_path = root / "docs" / "specs" / "requirement-digest.md"
    if not digest_path.exists():
        return
    digest_text = digest_path.read_text(encoding="utf-8", errors="replace")
    # issue #1017: 각 살아있는 요구의 (이미 파싱된) 다이제스트 줄을
    # 통째로 잡아둔다 — id 집합만 뽑던 이전 판과 달리, 아래 next-action
    # 출력이 paraphrase/source 를 다시 gh 로 조회하지 않고 이 메모리에서
    # 바로 쓴다(제안서 Accumulation 절이 명시한 "이미 파싱된 다이제스트
    # 엔트리 재사용, 새 gh 호출 없음").
    live_entries: dict[str, tuple[str, str, str]] = {
        m.group(1): (m.group(2), m.group(3), m.group(4))
        for m in re.finditer(
            r"^- (R\d+): (.+?) \[(\S+)\] \(source: #(\d+)\)$", digest_text, re.M)
    }
    live_ids = set(live_entries) or set(
        re.findall(r"^- (R\d+):", digest_text, re.M))
    if not live_ids:
        return

    def _list(kind: str) -> list[dict] | None:
        r = subprocess.run(
            ["gh", kind, "list", "--state", "open", "--json", "number,title,body",
             "--limit", "1000"],
            cwd=root, capture_output=True, text=True)
        if r.returncode != 0:
            return None
        try:
            return json.loads(r.stdout)
        except ValueError:
            return None

    cache_path = _requirement_drift_cache_path(root)
    if changed_numbers is None:
        issues = _list("issue")
        prs = _list("pr")
        if issues is None or prs is None:
            print("[watchdog] requirement-drift: gh 실패 — 판정 불가 (advisory, 미집계)")
            return
        all_items = issues + prs
        # issue #1688: full-mode run also refreshes the verdict cache so a
        # later delta-mode tick can reuse today's fetch for unchanged numbers.
        cache = {str(item.get("number")): {"title": item.get("title", ""),
                                            "body": item.get("body", "") or ""}
                 for item in all_items if item.get("number") is not None}
        _save_requirement_drift_cache(cache_path, cache)
    else:
        # issue #1688: delta mode — only re-fetch the changed numbers (via
        # the shared gh_cache), reuse the on-disk verdict cache for the rest.
        cache = _load_requirement_drift_cache(cache_path)
        all_items = []
        any_fetch_ok = not changed_numbers
        failed_numbers: list[int] = []
        for num in sorted(changed_numbers):
            item = _fetch_issue_or_pr_via_cache(root, num)
            if item is None:
                failed_numbers.append(num)
                continue
            any_fetch_ok = True
            all_items.append(item)
            cache[str(num)] = {"title": item.get("title", ""),
                                "body": item.get("body", "") or ""}
        for key, val in cache.items():
            try:
                key_num = int(key)
            except ValueError:
                continue
            if key_num in changed_numbers:
                continue
            all_items.append({"number": key_num, "title": val.get("title", ""),
                               "body": val.get("body", "")})
        _save_requirement_drift_cache(cache_path, cache)
        if not any_fetch_ok:
            print("[watchdog] requirement-drift: gh 실패 — 판정 불가 (advisory, 미집계)")
            return
        if failed_numbers:
            # 리뷰 non-blocking 노트: 델타 모드에서 개별 번호 조회 실패는
            # 조용히 사라지지 않고 이 한 줄로 남는다 — 해당 번호는 이번
            # 틱에서 재평가 안 되고 캐시된 이전 판정을 그대로 쓴다.
            print(f"[watchdog] requirement-drift: 조회 실패 {failed_numbers} — "
                  "이전 캐시 판정 유지")

    # 이슈 #1219: gates 코드는 언제나 이 체크아웃(ROOT)에서 온다 — root 가
    # 컨슈머의 타깃 프로젝트일 때 거기엔 gates/ 가 없다.
    sys.path.insert(0, str((ROOT / "gates").resolve()))
    try:
        import requirement_linkage as _requirement_linkage
        infra_tag = _requirement_linkage._INFRA_TAG
    except ImportError:
        # advisory 계약(이 함수 docstring): gh 실패처럼 import 실패도
        # 이 스윕 전체를 죽이지 않고 조용히 건너뛴다 — infra-tag 예외
        # 없이 기존 동작으로 계속한다.
        infra_tag = None

    mentioned_reqs: set[str] = set()
    unreferenced_open = []
    for item in all_items:
        text = f"{item.get('title', '')}\n{item.get('body', '') or ''}"
        found = set(_REQ_ID_RE.findall(text)) | set(
            f"R{n.zfill(3)}" for n in _NORTHPOLE_REQ_RE.findall(text))
        # _REQ_ID_RE 는 "R001" 형태의 raw 캡처가 아니라 숫자만 잡으므로
        # digest ID 형식(R\d+)과 직접 비교하려면 원문 재검색이 더 정확하다.
        raw_ids = set(re.findall(r"\bR\d+\b", text))
        mentioned_reqs |= raw_ids
        # 이슈 #1080: gates/requirement_linkage.py::check_issue_body 가 이미
        # 인정하는 infra-tag 예외를 여기서도 그대로 존중한다 — 같은
        # _INFRA_TAG 리터럴을 import 해서 두 검사가 서로 어긋나지 않게 한다.
        if infra_tag is not None and infra_tag in text:
            continue
        if not (raw_ids or _NORTHPOLE_REQ_RE.search(text)):
            unreferenced_open.append(item.get("number"))

    unmentioned_live = sorted(live_ids - mentioned_reqs)
    # issue #1142: `enforced` (배송 완료, 라이브 enforcement 경로 있음) 요구는
    # 인용 없이도 드리프트로 잡지 않는다 — `open`(미배송) 요구만 인용을
    # 요구한다. 다이제스트 파싱 실패 등으로 상태를 못 얻은 id 는 기존처럼
    # 보수적으로(=open 취급) 계속 플래그한다.
    unmentioned_live = [
        rid for rid in unmentioned_live
        if live_entries.get(rid, (None, "open", None))[1] == "open"
    ]
    unreferenced_open = sorted(unreferenced_open)
    if unmentioned_live:
        # issue #1017: 바래 ID 목록 대신, 요구마다 다이제스트 paraphrase/
        # source 와 — 있으면 — 요구 인용이 전혀 없는 열린 이슈/PR(연결
        # 후보) 을 named next-action 으로 출력한다.
        for rid in unmentioned_live:
            paraphrase, _status, source_issue = live_entries.get(
                rid, ("(다이제스트에 paraphrase 없음)", "open", "?"))
            candidates = unreferenced_open[:5]
            cand_note = (f" 후보(요구 인용이 전혀 없는 열린 이슈/PR): {candidates}"
                         if candidates else "")
            print(f"[watchdog] requirement-drift: 요구 {rid} — 다이제스트: "
                  f"\"{paraphrase}\" (source: #{source_issue}) — 열린 이슈/PR "
                  f"어디에도 인용되지 않는다.{cand_note}")
    if unreferenced_open:
        print(f"[watchdog] requirement-drift: 요구 ID 를 전혀 인용하지 않는 "
              f"열린 이슈/PR {unreferenced_open}")


def _roster_target_repos(d_all: dict) -> list[Path]:
    """이슈 #1276 요구#1: 로스터 엔트리(live + returned-undisposed — 처분된
    엔트리는 `roster_remove()`가 지우므로 `_roster_load()`가 담는 건 항상
    이 둘뿐이다)의 `work`(각 엔트리가 등록될 때 넘겨받은 -C/cwd) 필드에서
    distinct 타깃 레포를 뽑는다. 등장 순서를 안정적으로 유지하려고
    `dict`(Python 3.7+ 삽입 순서 보존) 를 dedup 에 쓴다."""
    repos: dict[Path, None] = {}
    for e in d_all.values():
        work = e.get("work")
        if not work:
            continue
        repos.setdefault(Path(work).resolve(), None)
    return list(repos)


def _board_wide_sweep_all(root: Path, d_all: dict) -> int:
    """이슈 #1276 요구#2/#3/#4: `_board_wide_sweep`(closure_sweep +
    spawn_coverage)를 arm-root 하나가 아니라 arm-root(seed/default) +
    로스터가 가리키는 distinct 타깃 레포마다 돈다. 로스터가 비어 있으면
    오늘과 동일하게 arm-root 하나만 스윕한다(empty-state parity). 매 틱
    로스터를 다시 읽으므로 새 레포로의 스폰이 재무장 없이 다음 틱부터
    잡힌다. 각 레포의 출력 줄은 그 레포 라벨로 접두된다 — 멀티보드 출력의
    귀속을 지킨다. 보드가 아닌(docs/specs/approvers.md 없는) 로스터
    레포는 매 틱 노이즈 없이 한 줄만 찍고 건너뛴다(#1245/#1275 와 합성).
    이슈 #1280: arm-root 자체도 보드가 아니면(예: 비-보드 레포에서 무장된
    세션) 스윕 대상에서 조용히 제외된다 — 라인도 찍지 않는다. 그래도
    로스터가 가리키는 보드 타깃은 계속 스윕한다(#1276 요구를 살린다).
    arm-root 의 비-git 검증은 CLI 진입점(#1275)에서 이미 끝난 뒤라
    여기서는 건드리지 않는다."""
    root = root.resolve()
    targets: dict[Path, None] = {root: None}
    for repo in _roster_target_repos(d_all):
        targets.setdefault(repo, None)
    count = 0
    for repo in targets:
        label = _repo_identity(repo)
        if not (repo / MARKER).exists():
            if repo == root:
                continue
            print(f"[watchdog] board-sweep: {label} — 로스터 타깃 레포지만 "
                  f"보드 아님({MARKER} 없음), 건너뜀")
            continue
        got, lock_msg = cross_workspace_board_sweep_lock_acquire(repo)
        if not got:
            print(f"[watchdog] board-sweep: {label} 건너뜀 (다른 워크스페이스가 스윕 중) — {lock_msg}")
            continue
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            count += _board_wide_sweep(repo)
        for line in buf.getvalue().splitlines():
            print(f"[{label}] {line}")
    return count


# 이슈 #1688 blocker 2: gh_budget(#1681, gates/gh_budget.py — 이미 merged,
# PR #1685)로 워치독 클래스를 미터링한다. 계정 리저브 바닥은 closure_sweep
# 의 기존 가드 문턱과 동일하게 맞춰 이중 가드를 만들지 않는다. 예산 값은
# 틱당 최대 gh 호출 수(call_budget=8)의 몇 배로 넉넉히 잡아, 정상 동작에서
# 절대 안 걸리고 실제 폭주(무한 루프성 재시도 등)에서만 백스톱으로 걸리게
# 한다.
_WATCHDOG_GH_BUDGET_CLASSES = {"watchdog": 200}


_HEAD_REF_SUBJECT_RE = re.compile(r"^issue-(\d+)/")


def _board_wide_sweep(root: Path) -> int:
    """이슈 #464: closure_sweep/spawn_coverage 를 한 틱씩 돌려 보고만 한다
    (observe-only, roster_watchdog 계약과 동일). 위반/미커버 이슈 수를
    합쳐서 돌려준다 — gh 실패(skips 있음 / open_issues=None)도 "깨끗함"이
    아니라 이상 신호 1건으로 센다(조용한 실패가 진행과 구분 안 되는 결함을
    재현하지 않기 위해).

    이슈 #1219: `root` 는 스캔 대상(보드) — 컨슈머 세션이면 타깃 프로젝트다.
    gates 코드 자체는 언제나 이 체크아웃(ROOT)에서 임포트한다 — 타깃
    프로젝트엔 gates/ 가 없다.

    이슈 #1498: gh 를 부르는 세 신호(spawn-on-pr, closure-sweep,
    spawn-coverage)는 셋 다 요구 1(쿼터 바닥) · 요구 3(스윕 백오프) ·
    요구 5(틱당 호출 예산)의 게이팅을 받는다 — 로컬 전용 신호
    (`accumulation_trend`, `requirement_drift`)는 게이팅 없이 항상 돈다.

    이슈 #1554 요구 1/3: 세 신호는 `closure_sweep.next_categories()`로
    이번 틱에 돌릴 카테고리(최대 `call_budget`개)만 골라 돈다 — 나머지는
    드롭되지 않고 `runs/board_sweep_queue.json`에 이월되어 다음 틱(들)에
    반드시 돈다(watch-coverage 불가침 계약). 예산=8 은 오늘의
    call_budget 과 같은 값을 유지해 기존 관측 동작(사실상 매 틱 세
    카테고리 다 돔)을 그대로 보존한다.

    이슈 #1688: 백오프/레이트리밋 가드를 통과하면, 카테고리를 고르기 전에
    `gates.gh_delta.fetch_delta(root, slug, "issues")` 를 틱당 정확히 1회
    부른다 — 이 틱의 유일한 조건부 프로브. `"no-change"` 면 상세 조회를
    전부 건너뛰고(`accumulation_trend()` 만 예외로 계속 돈다),
    `"delta"` 면 closure-sweep/requirement-drift 를 델타의 이슈/PR 번호로만
    좁히고, `"full-rescan"`/`"error"`/(비-GitHub 레포라 `slug` 가 없는 경우)
    는 오늘의 전체 로직으로 그대로 떨어진다."""
    sys.path.insert(0, str(ROOT / "gates"))
    import closure_sweep
    import spawn_coverage
    import spawn_on_pr
    import gh_delta
    import gh_budget
    count = 0
    call_budget = 8
    budget: "gh_budget.GhBudget | None" = None

    def _charge_watchdog_budget(source: str, cost: int = 1) -> bool:
        result = budget.charge("watchdog", cost=cost)
        if not result["ok"]:
            print(gh_budget.budget_message(source, result["remaining"], result.get("until")))
        return result["ok"]

    def _run_local_only_signals(changed_numbers: set[int] | None = None,
                                 skip_requirement_drift: bool = False) -> None:
        # 이슈 #512 요구사항 4 / #930 요구#6: advisory only — 아무것도
        # 막지 않고 anomaly count 에도 합산하지 않는다. gh 를 쓰지 않으므로
        # 쿼터 바닥/백오프와 무관하게 항상 돈다.
        trend = closure_sweep.accumulation_trend(root)
        print(f"[watchdog] {closure_sweep.format_accumulation_trend(trend)}")
        if skip_requirement_drift:
            return
        requirement_drift(root, changed_numbers=changed_numbers)

    backoff_state = closure_sweep.load_backoff_state(root)
    if not closure_sweep.sweep_should_run(backoff_state, "board-sweep"):
        closure_sweep.save_backoff_state(root, backoff_state)
        print("[watchdog] board-sweep: 건너뜀 (백오프 간격, gh 호출 없음)")
        _run_local_only_signals()
        return count

    remaining, guard_ok = closure_sweep.rate_limit_remaining(root)
    calls_made = 1
    # 이슈 #1745: 방금 위에서 이미 `gh api rate_limit` 을 한 번 불렀다 —
    # GhBudget 이 자기 스냅샷을 또 부르면 같은 틱에 같은 쿼리가 두 번
    # 나간다. 방금 받은 결과를 preseed 해 두 번째 호출을 없앤다.
    budget = gh_budget.GhBudget(root, classes=_WATCHDOG_GH_BUDGET_CLASSES,
                                 reserve=closure_sweep._RATE_LIMIT_GUARD_THRESHOLD,
                                 preseeded_snapshot=(remaining, guard_ok))
    if guard_ok and remaining < closure_sweep._RATE_LIMIT_GUARD_THRESHOLD:
        closure_sweep.record_sweep_result(backoff_state, "board-sweep", True)
        closure_sweep.save_backoff_state(root, backoff_state)
        count += 1
        print(f"[watchdog] board-sweep: 미집계 (rate-limit, remaining={remaining})")
        _run_local_only_signals()
        return count

    # 이슈 #1688: 틱당 단일 변경-커서 프로브. gh_budget(#1681, landed —
    # gates/gh_budget.py) 미터링을 프로브 자체보다 먼저 건다 — 예산 소진이면
    # 프로브조차 안 나가고 이번 틱은 로컬 신호만 돈다.
    slug = _repo_slug(root)
    delta_items: list[dict] | None = None
    delta_classification: str | None = None
    changed_numbers: set[int] = set()
    if slug:
        if not _charge_watchdog_budget("board-sweep gh_delta probe"):
            count += 1
            _run_local_only_signals()
            return count
        try:
            delta_items, _delta_cursor, delta_classification = gh_delta.fetch_delta(
                root, slug, "issues", include_prs=True)
        except Exception as ex:
            delta_classification = "error"
            print(f"[watchdog] gh_delta 프로브 예외: {ex}", file=sys.stderr)

        if delta_classification == "error":
            print("[watchdog] board-sweep: gh_delta 프로브 실패 (error 분류) — "
                  "보수적으로 오늘의 전체 로직으로 폴백")
        elif delta_classification == "no-change":
            closure_sweep.record_sweep_result(backoff_state, "board-sweep", False)
            closure_sweep.save_backoff_state(root, backoff_state)
            print("[watchdog] board-sweep: no-change (delta empty) — "
                  "상세 조회/전체 재훑기 건너뜀")
            _run_local_only_signals(skip_requirement_drift=True)
            return count
        elif delta_classification == "full-rescan":
            print("[watchdog] board-sweep: full-rescan (gh_delta 분류 — 커서 "
                  "없음/손상, 페이지 오버플로, 또는 재훑기 주기 도래 중 하나; "
                  "gh_delta 는 구체적 사유 문자열을 노출하지 않는다) — "
                  "오늘의 전체 로직으로 폴백")
        elif delta_classification == "delta":
            pr_numbers: set[int] = set()
            for it in (delta_items or []):
                n = it.get("number")
                if not isinstance(n, int):
                    continue
                if "pull_request" in it:
                    pr_numbers.add(n)
                else:
                    changed_numbers.add(n)
            if pr_numbers:
                # 이슈 #1688 blocker 1: PR 만 바뀐 틱은 이슈 번호가 델타에
                # 안 잡힌다 — 각 PR 을 headRefName(issue-<n>/<role>)으로
                # subject 이슈에 매핑해 narrowing set 에 합친다.
                # closure_sweep._pr_index_all 은 이 파일이 이미 다른
                # 경로(closure-sweep 처리)에서 쓰는 동일한 `gh pr list`
                # 인덱스 — PR 변경이 있을 때만(무변경 틱엔 안 나감) 도는
                # 추가 1회 호출이다.
                pr_index, pr_index_ok = closure_sweep._pr_index_all(root)
                if pr_index_ok and pr_index is not None:
                    number_to_branch = {v.get("number"): k for k, v in pr_index.items()}
                    for prn in sorted(pr_numbers):
                        branch = number_to_branch.get(prn)
                        m = _HEAD_REF_SUBJECT_RE.match(branch) if branch else None
                        if m:
                            changed_numbers.add(int(m.group(1)))
                        else:
                            print(f"[watchdog] board-sweep: PR #{prn} 변경 감지했으나 "
                                  f"subject 매핑 실패 (브랜치={branch!r}, issue-<n>/<role> "
                                  "형식 아님) — 이 PR 은 narrowing 에서 무시")
                else:
                    print(f"[watchdog] board-sweep: PR {sorted(pr_numbers)} 변경 감지했으나 "
                          "PR 인덱스 조회 실패 — subject 매핑 불가, 이 PR 들은 narrowing 에서 무시")
            print(f"[watchdog] board-sweep: delta {len(changed_numbers)}건 "
                  f"변경 {sorted(changed_numbers)} — 해당 subject/이슈만 재평가")
    delta_mode = slug is not None and delta_classification == "delta"

    this_tick, carried_over = closure_sweep.next_categories(root, call_budget)
    if carried_over:
        print(f"[watchdog] board-sweep: 이월 (예산) {carried_over}")

    if this_tick and not _charge_watchdog_budget("board-sweep sweep calls", cost=len(this_tick)):
        count += 1
        closure_sweep.record_sweep_result(backoff_state, "board-sweep", False)
        closure_sweep.save_backoff_state(root, backoff_state)
        _run_local_only_signals(changed_numbers=changed_numbers if delta_mode else None)
        return count

    issue_states, issue_states_ok = (None, True)
    if "spawn-on-pr" in this_tick or "closure-sweep" in this_tick:
        issue_states, issue_states_ok = closure_sweep.issue_state_index_all(root)
        calls_made += 1

    rate_limited_this_tick = False

    # 이슈 #1745: spawn-on-pr 과 closure-sweep 이 둘 다 이번 틱에 돌면
    # 벌크 PR 인덱스를 여기서 한 번만 가져와 공유한다 — 각자
    # `closure_sweep._pr_index_all()` 을 따로 부르면 `gh api .../pulls`
    # 페이지네이션이 틱당 두 번 나갔다(#1745 관측).
    shared_pr_index: dict | None = None
    if "spawn-on-pr" in this_tick and "closure-sweep" in this_tick:
        shared_pr_index, _ = closure_sweep._pr_index_all(root)

    if "spawn-on-pr" in this_tick:
        try:
            spawned = spawn_on_pr.spawn_missing_for_pr(
                root, str(root), issue_states=issue_states, pr_index=shared_pr_index)
            if spawned:
                print(f"[watchdog] spawn-on-pr: {len(spawned)}건 스폰: {spawned}")
            parked = spawn_on_pr.parked_report(root)
            if parked:
                # issue #1476: park 된 항목도 watch-coverage 는 유지한다 — 스폰만
                # 건너뛰고 waiting-for-human 으로 계속 보인다.
                print(f"[watchdog] spawn-on-pr: waiting-for-human {len(parked)}건: {parked}")
        except Exception as ex:
            count += 1
            print(f"[watchdog] spawn-on-pr 실패: {ex}", file=sys.stderr)

    if "closure-sweep" in this_tick:
        # 이슈 #1688: delta 모드면 board() 를 델타의 이슈/PR 번호로 필터한
        # subjects 만 넘겨 그 subject 만 재평가한다(전체 보드 아님).
        sweep_subjects = None
        if delta_mode:
            sweep_subjects = {}
            for subj, roles in board(root).items():
                parts = subj.split("-", 1)
                if len(parts) == 2 and parts[1].isdigit() and int(parts[1]) in changed_numbers:
                    sweep_subjects[subj] = roles
        violations, skips = closure_sweep.find_violations(
            root, subjects=sweep_subjects, issue_states=issue_states,
            pr_index=shared_pr_index)
        calls_made += 1
        if violations:
            count += len(violations)
            print(f"[watchdog] closure-sweep: 위반 {len(violations)}건")
            print(closure_sweep.format_report(violations))
        rate_limited_this_tick = bool(skips) and not issue_states_ok
        if skips:
            count += 1
            print(f"[watchdog] closure-sweep: 확인 불가 (gh 실패) {len(skips)}건")

    _run_local_only_signals(changed_numbers=changed_numbers if delta_mode else None)

    if "spawn-coverage" in this_tick:
        open_issues = spawn_coverage._list_open_issues(root)
        calls_made += 1
        if open_issues is None:
            count += 1
            rate_limited_this_tick = True
            print("[watchdog] spawn-coverage: 이슈 목록을 읽을 수 없다 (gh 실패) — 판정 불가")
        else:
            uncovered = spawn_coverage.find_uncovered(
                open_issues, board(root), datetime.now(timezone.utc))
            if uncovered:
                count += len(uncovered)
                print(f"[watchdog] spawn-coverage: 커버되지 않은 이슈 {uncovered}")

    closure_sweep.record_sweep_result(backoff_state, "board-sweep", rate_limited_this_tick)
    closure_sweep.save_backoff_state(root, backoff_state)
    if calls_made > call_budget:
        count += 1
        print(f"[watchdog] board-sweep: 예산 초과 ({calls_made}건 > {call_budget})")
    return count


WATCHDOG_LOCK_PATH = STATE_ROOT / "watchdog.lock"
WATCHDOG_FRESHNESS_STATE_PATH = STATE_ROOT / "watchdog-freshness-state.json"


def _proc_start_time(pid: int) -> str | None:
    """`/proc/<pid>/stat` 필드 22(starttime, 부팅 이후 클럭틱)를 읽는다 (이슈
    #1456) — pid 만으론 크래시 뒤 재사용된 pid 를 "그 프로세스가 아직
    살아있다"고 오판한다(요구 1의 caveat 1). comm 필드가 괄호/공백을 담을 수
    있어 마지막 ')' 뒤부터 잘라 필드 3(state)부터 다시 센다."""
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
    except (FileNotFoundError, ProcessLookupError, PermissionError, OSError):
        return None
    rest = raw[raw.rfind(")") + 2:]
    fields = rest.split()
    if len(fields) < 20:
        return None
    return fields[19]  # starttime = 필드 22, state(필드3)부터 0-based 로 19번째


def watchdog_lock_acquire(lock_path: Path = WATCHDOG_LOCK_PATH,
                           pid: int | None = None) -> tuple[bool, str]:
    """`spawn.py watchdog` 단일-인스턴스 락(이슈 #1456 요구 1). 이미 살아있는
    인스턴스가 있으면 (False, 안내줄) — pid 재사용을 피하려 pid *와*
    프로세스 시작 시각이 둘 다 일치해야 "살아있다"로 본다. 죽은 프로세스가
    남긴 락(또는 pid 재사용으로 시작시각이 달라진 락)은 그대로 회수한다."""
    my_pid = pid if pid is not None else os.getpid()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = json.loads(lock_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        existing = None
    if existing:
        other_pid = existing.get("pid")
        other_start = existing.get("start_time")
        if (isinstance(other_pid, int) and _alive(other_pid)
                and _proc_start_time(other_pid) == other_start):
            return False, (f"[watchdog] 이미 실행 중: pid={other_pid} "
                            f"start_time={other_start} — lock={lock_path}")
    lock_path.write_text(json.dumps({"pid": my_pid,
                                      "start_time": _proc_start_time(my_pid)}))
    return True, ""


def _cross_workspace_board_sweep_lock_path(repo_root: Path) -> Path:
    """이슈 #1554 요구 2: board-wide 스윕 락의 위치는 *실행 중인 checkout*
    (`STATE_ROOT`, `ROOT`가 정의된 곳 — 워크스페이스마다 다르다)이 아니라
    *스윕 대상 레포의 identity*로 정해져야 한다 — 그래야 서로 다른
    워크스페이스에서 뜬 워치독들도 같은 파일을 놓고 경합한다(#1510
    single-instance 정책의 cross-workspace enforcement gap). `_workspace_base()`
    가 이미 `MUSTER_WORK_DIR`(기본 `~/.tokenmaxxxer/work`) 오버라이드를
    존중하므로, 그 부모 아래 고정 `locks/` 디렉터리를 쓴다 — 어느 체크아웃의
    spawn.py 가 이 코드를 실행하든 물리적으로 같은 경로가 나온다.
    `_repo_identity()`(순수 로컬, gh 호출 없음)를 키로 쓴다."""
    return (_workspace_base().parent / "locks" /
            f"board-sweep-{_repo_identity(repo_root)}.lock")


def cross_workspace_board_sweep_lock_acquire(
        repo_root: Path, pid: int | None = None) -> tuple[bool, str]:
    """이슈 #1554 요구 2: 레포 하나에 board-wide 스위퍼가 딱 하나만 뜨게
    한다. 세션별 헬스 워처(`roster_watchdog` 개별 엔트리)는 이 락을 타지
    않는다 — 여기 거치는 건 `_board_wide_sweep_all`이 부르는 board-wide
    스윕뿐이다. 락 자체는 `watchdog_lock_acquire`와 같은 pid+시작시각
    liveness 판정을 그대로 재사용한다(죽은 홀더의 락은 회수됨)."""
    return watchdog_lock_acquire(
        lock_path=_cross_workspace_board_sweep_lock_path(repo_root), pid=pid)


def watchdog_current_head(cwd: Path = ROOT) -> str | None:
    """워치독이 코드를 로드한 체크아웃의 현재 HEAD (이슈 #1456 요구 2)."""
    r = subprocess.run(["git", "-C", str(cwd), "rev-parse", "HEAD"],
                        capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def watchdog_freshness_check(startup_head: str, cwd: Path = ROOT,
                              fetched_this_tick: bool = False,
                              state_path: Path | None = None) -> tuple[bool, str]:
    """틱마다 체크아웃 HEAD 를 시작 시점 HEAD 와 비교한다 (이슈 #1456 요구 2)
    — #1360 이 재발한 원인은 merge != deploy: 장수 워치독이 구코드를 계속
    물고 있었다. 이 틱이 아직 fetch 를 하지 않았으면(caveat 2), 비교 전에
    한 번 fetch 해 로컬 체크아웃을 최신 origin HEAD 에 맞춘다 — 기존
    per-spawn fetch cadence 가 이미 하는 일과 같은 모양이라 새 원격 호출
    경로를 늘리지 않는다. git 실패는 advisory 로 두고 틱을 막지 않는다
    (fail-open — 네트워크 문제로 매 틱을 재기동시키면 더 나쁘다).

    `state_path` 가 주어지면(이슈 #1755) 같은 HEAD 전환에 대해 안내줄을
    한 번만 낸다 — 틱마다 별도 CLI 서브프로세스로 재호출되므로(장수
    파이썬 프로세스가 아니다) 인메모리 dedup 은 불가능하고, `state_path`
    에 마지막으로 알린 HEAD 를 남겨 다음 서브프로세스 호출이 읽는다.
    `state_path=None` 이면 오늘의 동작(dedup 없음, 기존 테스트) 그대로다."""
    if not fetched_this_tick:
        subprocess.run(["git", "-C", str(cwd), "fetch", "--quiet", "origin"],
                        capture_output=True, text=True)
        pull = subprocess.run(["git", "-C", str(cwd), "merge", "--ff-only",
                                "--quiet", "origin/HEAD"],
                               capture_output=True, text=True)
        del pull  # 실패해도(로컬 커밋 등) advisory — HEAD 비교로 판정한다
    current = watchdog_current_head(cwd)
    if current is None:
        return True, ""
    if current == startup_head:
        return True, ""
    msg = (f"[watchdog] 코드-신선도: 체크아웃 HEAD 가 바뀌었다 "
           f"(시작={startup_head[:12]} 현재={current[:12]}) — "
           f"재기동 필요")
    if state_path is not None:
        try:
            last_alerted = json.loads(state_path.read_text()).get("last_alerted_head")
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            last_alerted = None
        if last_alerted == current:
            return False, ""
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({"last_alerted_head": current}))
    return False, msg


def watchdog_canonical_guard(module_path: Path = Path(__file__)) -> tuple[bool, str]:
    """워치독 자신의 파일 경로가 canonical 보드 체크아웃 밖(예:
    `~/.tokenmaxxxer/work/*` 역할 워크스페이스)이면 시작을 거부한다 (이슈
    #1456 요구 3, #1360 재발 원인 그 자체 — 역할 워크스페이스에서 뜬
    독립 워치독이 rearm 을 못 받았다). `SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1`
    로 테스트/운영 오버라이드."""
    override = os.environ.get("SPAWN_WATCHDOG_ALLOW_NONCANONICAL", "")
    if override not in ("", "0", "false", "no", "off"):
        return True, ""
    resolved = module_path.resolve()
    try:
        resolved.relative_to(_workspace_base().resolve())
    except ValueError:
        return True, ""
    return False, (f"[watchdog] 비-canonical 체크아웃에서 시작 거부: "
                    f"{resolved} — SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1 로 재정의")


STANDING_RED_STATE = ROOT / "runs" / "standing_red_state.json"
# 이슈 #1491: #1490 fast-tier 예산(<=300s)에 맞춰 고른, 유한 주기(분).
# 값 자체는 phase-1 프로포절이 phase-2로 미룬 튜닝 대상이다.
STANDING_RED_CADENCE_MIN = 15
_PYTEST_FAILED_RE = re.compile(r"^FAILED (\S+)")


def _standing_red_state_load(path: Path = STANDING_RED_STATE) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def _standing_red_state_save(d: dict, path: Path = STANDING_RED_STATE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def _standing_red_tree_hash(root: Path = ROOT) -> str | None:
    r = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                        capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout.strip()


def _standing_red_load_contract(root: Path):
    """이슈 #1518 계약 파서를 재사용한다 — 이 체크 자신은 tier 선택/예산
    로직을 다시 만들지 않는다(#1491 프로포절 Constraints)."""
    gates_dir = str(ROOT / "gates")
    if gates_dir not in sys.path:
        sys.path.insert(0, gates_dir)
    import test_tier_contract
    return test_tier_contract.load_contract(root)


def _standing_red_parse_failed_ids(output: str) -> set[str]:
    """pytest 요약의 `FAILED <test_id> ...` 줄에서 테스트 id 만 뽑는다.
    매칭 없는 출력(다른 러너, 크래시 등)은 빈 set — 새 실패로 오인해
    소음을 만들지 않는 fail-closed 파싱이다."""
    ids: set[str] = set()
    for line in output.splitlines():
        m = _PYTEST_FAILED_RE.match(line.strip())
        if m:
            ids.add(m.group(1))
    return ids


def standing_red_check(state: dict | None = None, now: float | None = None,
                        root: Path = ROOT) -> list[str]:
    """이슈 #1491: main 위 fast tier(이슈 #1518 계약)를 유한 주기로 돌려,
    새로 red 가 된 테스트를 관찰만 하는(observe-only) 신호 목록으로
    돌려준다. 절대 스위트를 고치거나, 이슈를 파거나, 세션을 스폰하지
    않는다 — 기존 watchdog 철학(watchdog_check_one) 그대로.

    req 3(플레이크): 같은 tree_hash 에서 두 번 연속 실패해야 신호가
    나간다 — 단, 이 상태 파일 자체가 처음(=이전에 `standing_red` 키가
    없던) 이면 그 첫 스캔에서 현재 red 전부를 baseline 으로 즉시
    한 번 보고한다(이슈 acceptance 의 empty-state 요구).
    req 4(중복 억제): 이미 보고된 red 는 같은 tree_hash 에서 재보고하지
    않는다 — tree_hash 가 바뀌면 그 테스트의 카운터가 리셋되며 재무장된다.

    `state` 를 넘기면 그 dict 를 제자리에서 갱신하고 저장하지 않는다
    (테스트용). 생략하면 `runs/standing_red_state.json` 을 읽고 쓴다.
    """
    now = time.time() if now is None else now
    own_state = state if state is not None else _standing_red_state_load()

    last_run = own_state.get("last_run")
    if last_run is not None and (now - last_run) / 60 < STANDING_RED_CADENCE_MIN:
        return []
    own_state["last_run"] = now

    contract = _standing_red_load_contract(root)
    if contract is None:
        # 이슈 #1518 no_contract_gap 경로 — 계약 없이 조용히 전체 스위트를
        # 돌리지 않는다. 이번 틱은 신호 없이 넘어간다.
        if state is None:
            _standing_red_state_save(own_state)
        return []

    is_empty_state = "standing_red" not in own_state
    standing_red = own_state.setdefault("standing_red", {})

    try:
        import shlex
        cmd = shlex.split(contract.fast_command)
        result = subprocess.run(cmd, cwd=str(root), capture_output=True,
                                 text=True, timeout=contract.budget_seconds)
        output = (result.stdout or "") + "\n" + (result.stderr or "")
    except (OSError, subprocess.TimeoutExpired):
        # advisory — 러너 자체가 못 뜨거나 예산을 넘겨도 틱을 막지 않는다.
        if state is None:
            _standing_red_state_save(own_state)
        return []

    failing_ids = _standing_red_parse_failed_ids(output)
    tree_hash = _standing_red_tree_hash(root)

    signals: list[str] = []
    for test_id in sorted(failing_ids):
        prev = standing_red.get(test_id)
        same_tree = bool(prev) and prev.get("tree_hash") == tree_hash
        consecutive = (prev.get("consecutive_count", 0) + 1) if same_tree else 1
        reported_before = bool(same_tree and prev.get("reported"))
        should_report = (not reported_before) and (is_empty_state or consecutive >= 2)
        standing_red[test_id] = {
            "tree_hash": tree_hash,
            "consecutive_count": consecutive,
            "reported": reported_before or should_report,
        }
        if should_report:
            signals.append(
                f"standing-red: {test_id} — 새 red, tree {(tree_hash or '?')[:8]}")

    # 더 이상 실패하지 않는 테스트는 상태에서 지운다 — 재발 시 처음부터
    # (empty-state 아님, 플레이크 규칙대로) 다시 카운트된다.
    for test_id in list(standing_red):
        if test_id not in failing_ids:
            del standing_red[test_id]

    if state is None:
        _standing_red_state_save(own_state)
    return signals


def roster_watchdog(auto_respawn: bool = False, all_scope: bool = False,
                     root: Path = ROOT) -> int:
    """`spawn.py watchdog` — 살아있는 모든 역할 세션을 한 번 스캔해서 이상
    신호를 사람이 읽을 수 있게 출력한다. observe-only: 아무 것도 고치거나
    죽이지 않는다. 오케스트레이터가 10-15분 간격으로 반복 호출한다
    (이슈 #90 phase-2 프로포절).

    `auto_respawn=True` (이슈 #132): 죽은 로스터 엔트리도 스캔 대상에
    넣어(원래는 살아있는 것만 봤다) `session_end_verdict` 를 매겨, `crashed`
    에 한해서만 재스폰/상한-코멘트를 시도한다. `stalled` 는 여전히
    보고만 한다 — 아무 것도 고치거나 죽이지 않는다는 계약은 그대로다.

    반환값(이슈 #327): 이상 신호가 하나 이상 나온 로스터 엔트리 수 — 깨끗한
    스캔이면 0(기존과 동일), 아니면 0 초과. `spawn.py watchdog` CLI 가 이
    값을 그대로 프로세스 종료 코드로 쓴다(spawn.py:2445) — stdout 파싱 없이
    idle/deadlock/불필요한 작업이 있었는지 종료 코드만으로 알 수 있게 한다.
    `auto_respawn` 의 부작용(재스폰/상한-코멘트)은 이 변경과 무관 — 반환값만
    바뀐다.

    이슈 #1274: 이 rc 는 이상 신호 "개수"이지 크래시 플래그가 아니다 —
    poll-heartbeat.sh 등 호출부는 `rc != 0` 을 크래시로 오독하면 안 된다.
    진짜 크래시(watchdog 프로세스 자체가 죽었다는 뜻)는 이 함수의 반환값과
    별개의 두 경로로만 신호한다: (1) 시그널 사망 — 셸이 관측하는 종료
    코드가 128+N (예: SIGKILL=137, SIGSEGV=139); (2) `main()` 의 watchdog
    분기가 처리 못 한 예외를 잡아 `WATCHDOG_CRASH_SENTINEL`
    (spawn.py 정의, 현재 97) 로 종료하는 예약 코드 — 파이썬 기본
    트레이스백 종료(exit 1)를 그대로 두면 anomaly_count==1 과 구분이 안
    되므로 반드시 이 센티널을 거친다. 호출부는 `rc >= 128 or rc ==
    WATCHDOG_CRASH_SENTINEL` 일 때만 크래시로 표시해야 한다.

    이슈 #464: 로스터 스캔과 별도로, 매 틱마다 보드-전체(closure_sweep /
    spawn_coverage) 스윕도 한 번 돈다 — 로스터가 비어 있어도 건너뛰지
    않는다(로스터가 빈 상태에서 보드가 방치될 위험이 가장 크다). 위반/미커버
    이슈는 로스터 이상 신호와 같은 모양으로 출력되고 `anomaly_count`에
    합산된다. observe-only 계약은 그대로 — 아무것도 고치거나 닫지 않는다.

    이슈 #1219: `root` 는 이 워치독이 보는 보드다 — CLI 는 호출자의 `-C`
    (컨슈머 세션이면 타깃 프로젝트, dev 세션이면 이 체크아웃 자신)를 그대로
    넘긴다. 기본값 `ROOT`(spawn.py 자신의 체크아웃)는 CLI 를 거치지 않는
    직접 호출/테스트만을 위한 하위호환 폴백이다 — 워치독 코드(closure_sweep
    등 gates 모듈) 임포트는 항상 `ROOT` 를 쓰고(코드는 언제나 체크아웃에서
    온다), 보드 스캔 대상(이슈/PR/다이제스트)만 `root` 를 쓴다."""
    # 이슈 #1276: 로스터를 여기서 먼저 읽는다 — 보드 스윕이 로스터가
    # 가리키는 distinct 타깃 레포까지 커버해야 해서(요구#1), 로스터 스캔
    # 루프가 쓰는 `d_all` 과 같은 한 번의 읽기를 그대로 재사용한다.
    d_all = _roster_load()
    anomaly_count = _board_wide_sweep_all(root, d_all)
    # 이슈 #1491: standing-red 관찰은 살아있는 로스터와 무관하게 매 틱
    # 시도한다(자체 유한-주기 게이트로 실제 스위트 실행은 걸러낸다) —
    # 아래 `if not d` 조기 반환에 걸리지 않게 board-wide sweep 바로 뒤에
    # 둔다.
    for sr_signal in standing_red_check(root=root):
        anomaly_count += 1
        print(f"[standing-red] {sr_signal}")
    # 이슈 #1239: 워치독 틱마다 처분 안 된 issue-*/ PR 목록을 always-emit
    # 카테고리로 찍는다 — poll-heartbeat.sh 의 #1220 delta-suppression 이
    # `[returned-pr]` 태그 줄을 ALWAYS_RE 로 인식해 매 틱 살아남는다. 스폰
    # 시점뿐 아니라 매 60초 틱마다 방치를 보이게 하는 게 이 이슈의 요구다.
    blockers, ok = _undispositioned_role_prs(root)
    if ok:
        _print_returned_pr_surfaced(blockers, source="watchdog")
    # 이슈 #1013 block B: 자기 세션 소유(또는 소유 미기재=empty-state)
    # 엔트리로 스캔을 좁힌다. `--all` 이면 그대로 전체.
    d = _roster_own(d_all, all_scope)
    if not all_scope:
        # 이슈 #1013 block D: 다른 세션 소유로 걸러진(own-scope 밖) 죽은
        # 엔트리는 관측-손실 방지를 위해 [orphaned] 로 계속 보고한다 —
        # 다만 own-scope 루프 밖이므로 아래의 `_auto_respawn_check()` 는
        # 결코 이들에 대해 불리지 않는다(다른 세션 소유 작업을 재스폰하지
        # 않는다).
        for key in sorted(set(d_all) - set(d)):
            e = d_all[key]
            if _alive(e.get("pid", 0)):
                continue
            anomaly_count += 1
            print(f"[orphaned] {key}: session {e.get('session_id')} 소유, "
                  f"이 세션 소유 아님 — 재스폰하지 않음")
    if not d:
        print("돌고 있는 역할 세션 없음")
        if not anomaly_count:
            print("이상 신호 없음")
        return anomaly_count
    state = _watchdog_state_load()
    respawn_state = _respawn_state_load() if auto_respawn else {}
    issue_role_key = lambda e: (e.get("issue"), e.get("role"))
    for key, e in sorted(d.items()):
        # 이슈 #492: 같은 틱에서 reconcile() 도 한 번 태운다 — 새 폴러가
        # 아니라 이 기존 스캔에 올라탄다(ADR 결정 4).
        divergences = reconcile(_build_expected(e), _build_observed(root, e),
                                 recovery_state_dir=root / ".on-the-record" / "recovery-state")
        if divergences:
            issue_n, role_n = issue_role_key(e)
            for div in divergences:
                dedup_key = f"health-repair:{issue_n}:{role_n}:{div['kind']}"
                if not ledger_check_and_stamp(dedup_key):
                    continue  # 이슈 #782: 이미 같은 TTL 창에서 보고됨 — 조용히
                anomaly_count += 1
                print(f"[reconcile] {key}: divergence — "
                      f"{div['kind']}: {div['detail']} -> {div['next_action']}")
        if not _alive(e.get("pid", 0)):
            work = e.get("work")
            issue_n = e.get("issue")
            if work and issue_n is not None:
                # 이슈 #534: self-trigger 가 놓친(프로세스가 그 줄에 닿기 전에
                # 죽는 등) dead-but-registered 엔트리를 best-effort 로 잡는다
                # — 주 경로는 _spawn_one() 의 self-trigger 다, 이 틱이 아니다.
                _post_session_end_comment(root, issue_n, key, work, e.get("log", ""))
            # 이슈 #782 스코프-확장(operator, 2026-08-11): 폴링 틱마다 세션별
            # 상태 한 줄을 찍는다. diagnose_health() 는 죽은 엔트리에 한해
            # `_pr_open_or_merged_for_branch()`(gh pr list)를 새로 부르므로,
            # 원장(TTL=RECONCILE_LEDGER_TTL_SEC)으로 그 비싼 재확인 빈도를
            # 60초 폴 간격과 분리한다 — dedup 은 반복 escalation 소음만
            # 거른다는 계약은 그대로, 여기서 걸러지는 건 gh 호출 자체다
            # (경보 전 hunt: dead-registered 엔트리가 15배 빈도로 gh 를
            # 때리는 문제).
            if ledger_check_and_stamp(f"poll-report-dead-check:{key}"):
                dead_health = diagnose_health(key, e, state=state, root=root)
                state[f"{key}:dead_report"] = dead_health
            dead_health = state.get(f"{key}:dead_report")
            if dead_health is not None:
                dead_label = "COMPLETED" if dead_health["state"] is None else dead_health["state"]
                print(f"[poll-report] {key}: {dead_label} — {dead_health['detail']}")
                if dead_health["state"] is None:
                    # 이슈 #878 케이스 2: 완료(PR 존재) 이면서 이 엔트리를
                    # 무장한 오케스트레이터가 headless(session_id 있음) 였다면
                    # 여기서 --resume 을 쏜다 — 인터랙티브 케이스 1 은
                    # 라이브 notify 로 이미 처리되므로 session_id 없는 엔트리는
                    # 그대로 통과한다(중복 트리거 없음).
                    branch = Path(work).name if work else None
                    pr_number = _pr_open_or_merged_for_branch(root, branch) if branch else None
                    if pr_number is not None and _maybe_resume_for_ready_pr(key, e, pr_number):
                        print(f"[resume] {key}: PR #{pr_number} ready — "
                              f"resumed session {e.get('session_id')}")
            if auto_respawn:
                _auto_respawn_check(key, e, respawn_state)
            continue
        anomalies = watchdog_check_one(key, e, state=state)
        # 이슈 #782 스코프-확장: HEALTHY/STALLED/DEADLOCKED/DEAD-ERRORED 네
        # 상태로 진단하고, 완료가 아닌 진단 결과만 원장으로 게이팅해 보고한다
        # (완료는 위 reconcile()/아래 죽음-분기가 이미 다룬다). 같은 틱에서
        # 이미 계산한 anomalies 를 넘겨 watchdog_check_one() 의 오프셋
        # 소비를 두 번 겪지 않는다.
        health = diagnose_health(key, e, state=state, anomalies=anomalies, root=root)
        # 이슈 #782 스코프-확장: dedup 원장과 무관하게 매 틱 상태를 보고한다.
        print(f"[poll-report] {key}: {health['state']} — {health['detail']}")
        if health["state"] is not None and health["state"] != "HEALTHY":
            issue_n, role_n = issue_role_key(e)
            dedup_key = f"health:{issue_n}:{role_n}:{health['state']}"
            if ledger_check_and_stamp(dedup_key):
                anomaly_count += 1
                print(f"[health] {key}: {health['state']} — "
                      f"{health['detail']} -> {health['next_action']}")
        if anomalies:
            anomaly_count += 1
            print(f"[watchdog] {key}: 이상 신호 {len(anomalies)}건")
            for a in anomalies:
                print(f"  - {a}")
        else:
            print(f"[watchdog] {key}: 정상")
    _watchdog_state_save(state)
    if not anomaly_count:
        print("이상 신호 없음")
    return anomaly_count


def _roster_reconcile_unreported(issue: int | None = None) -> int:
    """`spawn.py reconcile --unreported [--issue N]` (이슈 #534): roster 는
    session-end 직후 곧바로 지워지므로(`roster_remove()`, spawn.py:3988)
    끝난 세션의 흔적을 담지 못한다 — 대신 세션이 끝나도 지워지지 않는
    `_workspace_index_put()` 의 workspace 인덱스(`WORKSPACE_INDEX`)를
    훑는다. `verdict == "normal"` 인데 `_SESSION_END_COMMENT_MARKER`
    코멘트가 아직 없는 엔트리를 "미보고"로 찍는다 — self-trigger/watchdog
    이 둘 다 놓친 경우(프로세스가 코멘트 줄에 닿기 전에 죽는 등)를
    오케스트레이터가 아무 때나 한 번의 호출로 회복하는 창구다."""
    idx = _workspace_index_load()
    total = 0
    found_any = False
    for key, e in sorted(idx.items()):
        m = re.search(r"(?:^|/)issue-(\d+)/", key)
        if not m:
            continue
        issue_n = int(m.group(1))
        if issue is not None and issue_n != issue:
            continue
        found_any = True
        work = e.get("work")
        if not work:
            continue
        # 이슈 #1283: workspace 가 이미 `clean` 에 지워졌다고 여기서
        # 건너뛰면(구 #1124 조치), session-end(normal) 인데 아직 미보고인
        # 세션이 영영 사라진다 — session_end_verdict/`_issue_comments`
        # 둘 다 없는 workspace 를 이미 안전하게 다루므로(survey 참고)
        # 여기서 따로 건너뛸 필요가 없다.
        log = e.get("log")
        verdict = session_end_verdict(work, Path(log) if log else None)
        if verdict != "normal":
            continue
        # 이슈 #533: 마커는 `_post_session_end_comment` 가 실제로 코멘트에
        # 박아 둔 bare `issue-<n>/<role>` 형태여야 한다 — workspace 인덱스
        # `key` 는 이제 레포 접두사가 붙어 그대로 쓰면 마커가 영원히
        # 안 맞아 매번 미보고로 오탐한다.
        m2 = re.search(r"issue-\d+/[^/]+$", key)
        roster_key = m2.group(0) if m2 else key
        marker = _SESSION_END_COMMENT_MARKER.format(key=roster_key)
        # `_issue_comments`가 `ok=False`(코멘트를 못 읽음)면 마커 부재를
        # 확인할 수 없다 — "확인 못 함은 통과가 아니다"(#287) 원칙대로
        # 미보고 쪽으로 넘어간다(중복 코멘트를 감수).
        comments, ok = _issue_comments(Path(work), issue_n)
        if ok and any(marker in c.get("body", "") for c in comments):
            continue
        total += 1
        print(f"[reconcile --unreported] {key}: session-end(normal) 미보고 "
              f"— issue #{issue_n}, work={work}, log={log}")
    if not found_any:
        print("reconcile --unreported: 대상 workspace 엔트리 없음")
    elif not total:
        print("reconcile --unreported: 미보고 없음")
    return total


_REMEDIATION_MERGE_COMMENT_MARKER = "[watch] remediation-merged: {path}"


def _remediation_merge_sweep(root: Path, issue: int) -> int:
    """`spawn.py reconcile --remediation-merged --issue N` (이슈 #587 §12
    event 4): `docs/issue-<n>/decisions/remediation-*.md` 중 `status: open`
    인 기록의 `routed_to` 역할 브랜치(`issue-<n>/<role>`, 관례는
    `remediation_spawn.py` 의 멱등성 체크와 동일)가 머지됐으면 §12 형식의
    한 줄 코멘트를 이슈에 남긴다.

    `_roster_reconcile_unreported`와 같은 read-then-check 멱등 패턴: 고정
    마커가 이미 있으면 건너뛴다 — 같은 remediation 기록에 두 번 코멘트를
    달지 않는다."""
    decisions_dir = root / BOARD / f"issue-{issue}" / "decisions"
    if not decisions_dir.is_dir():
        return 0
    slug = _repo_slug(root)
    posted = 0
    for rem_path in sorted(decisions_dir.glob("remediation-*.md")):
        fm = frontmatter(rem_path)
        if fm.get("status") != "open":
            continue
        routed_to = fm.get("routed_to")
        if not routed_to or routed_to == "UNRESOLVED":
            continue
        round_n = fm.get("round", "?")
        candidate_pr = fm.get("candidate_pr", "?")
        marker = _REMEDIATION_MERGE_COMMENT_MARKER.format(
            path=f"docs/issue-{issue}/decisions/{rem_path.name}")
        comments, ok = _issue_comments(root, issue)
        if ok and any(marker in c.get("body", "") for c in comments):
            continue
        branch = f"issue-{issue}/{routed_to}"
        merged_pr = _merged_pr_for_branch(root, branch)
        if merged_pr is None:
            continue
        if not slug:
            continue
        body = (f"{marker}\n\n"
                f"Remediation merged: PR #{merged_pr} resolves round {round_n} "
                f"of PR #{candidate_pr}\n"
                f"https://github.com/{slug}/pull/{merged_pr}")
        r = subprocess.run(["gh", "api", f"repos/{slug}/issues/{issue}/comments",
                            "-f", f"body={body}"], cwd=root, capture_output=True, text=True)
        if r.returncode == 0:
            posted += 1
        else:
            print(f"[spawn] 이슈 #{issue} remediation-merged 코멘트 게시 실패: "
                  f"{r.stderr.strip()}", file=sys.stderr)
    return posted


def roster_reconcile(issue: int | None = None, unreported: bool = False,
                      remediation_merged: bool = False,
                      root: Path | None = None) -> int:
    """`spawn.py reconcile [--issue N] [--unreported] [--remediation-merged]`
    — 이슈-492 step 2 CLI verb, 이슈 #534 로 `--unreported` 모드가, 이슈
    #587 round 2 로 `--remediation-merged` 모드가 추가됐다.

    `unreported=True` 면 `_roster_reconcile_unreported()` 로 위임한다 —
    roster 가 아니라 workspace 인덱스를 보는, 다른 데이터소스/다른 질문
    (divergence 가 아니라 "미보고 session-end")이라 별도 함수로 분리했다.

    `remediation_merged=True` 면 `_remediation_merge_sweep(target_root,
    issue)` 로 위임한다 — `target_root` 는 `root` (호출자의 `-C` 대상)가
    주어지면 그것, 아니면 `ROOT`(spawn.py 자신의 체크아웃)다. 이슈 #587
    round 3: `_remediation_merge_sweep` 이 항상 `ROOT` 로만 불려서 다른
    레포를 대상으로 한 CLI 호출에서 조용히 no-op 됐던 결함의 수정 —
    `issue` 가 없으면 대상을 특정할 수 없으므로 아무 것도 하지 않고 0 을
    반환한다.

    기본 모드(둘 다 False)는 그대로다: 로스터(살아있는 것 + 죽은 것
    전부, `watchdog --auto-respawn` 의 스캔 범위와 같다)를 훑어 엔트리마다
    `reconcile()` 을 한 번씩 돌린다. `--issue` 를 주면 그 이슈 번호의
    엔트리로만 좁힌다. divergence 한 줄씩 찍고, 종료 코드는 divergence 총
    개수(0 = 깨끗함) — `roster_watchdog` 의 반환값과 같은 관례
    (spawn.py:1752-1755)."""
    if unreported:
        return _roster_reconcile_unreported(issue)
    if remediation_merged:
        if issue is None:
            return 0
        target_root = root if root is not None else ROOT
        return _remediation_merge_sweep(target_root, issue)
    d = _roster_load()
    if issue is not None:
        d = {k: e for k, e in d.items() if e.get("issue") == issue}
    if not d:
        print("reconcile: 대상 로스터 엔트리 없음")
        return 0
    total = 0
    for key, e in sorted(d.items()):
        divergences = reconcile(_build_expected(e), _build_observed(ROOT, e),
                                 recovery_state_dir=ROOT / ".on-the-record" / "recovery-state")
        for div in divergences:
            total += 1
            print(f"[reconcile] {key}: {div['kind']}: {div['detail']} "
                  f"-> next_action={div['next_action']}")
    if not total:
        print("reconcile: divergence 없음")
    return total


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
    hook_m = _GATE_HOOK_RE.search(text)
    if hook_m:
        hook_path = hook_m.group(1)
        gate = Path(hook_path).stem
        deny_m = _GATE_DENY_RE.search(text)
        reason = (" ".join(text[deny_m.end():].strip().split())[:300] if deny_m
                  else " ".join(text.strip().split())[:300])
        return ("gate-refusal", ("gate", hook_path, reason),
                {"gate": gate, "reason": reason})
    for pat in _HARNESS_REFUSAL_PATTERNS:
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
    for pat in _SANDBOX_REFUSAL_PATTERNS:
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
            result_text = _tool_result_text(block.get("content"))
            if _classify_refusal_text(result_text) is not None:
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
    remaining = Counter(d.get("tool_name") for d in denials
                        if isinstance(d, dict) and d.get("tool_name"))
    unattributable = sum(1 for d in denials
                         if not (isinstance(d, dict) and d.get("tool_name")))
    for ev_type, detail, tool_name in pending_refusals.values():
        if tool_name and remaining.get(tool_name):
            remaining[tool_name] -= 1
            _append_event(events_path, ev_type, detail)
    if sum(remaining.values()) + unattributable > 0:
        _append_event(events_path, "unclassified-refusal", str(denials)[:200])


def _flush_unverified(events_path: Path, pending_refusals: dict) -> None:
    """이슈 #246 결함 1: 터미널 `result` 줄이 아예 없거나(EOF/크래시 — S1/S3)
    `permission_denials` 형태를 신뢰할 수 없을 때(S2, 리스트가 아닌 값)
    호출된다. `permission_denials` 와 상관시킬 확정 근거가 없으므로 이미
    층 분류는 된 후보를 그 확정 라벨(gate-refusal 등)로 참칭하지 않고,
    `unverified-refusal` 로 정직하게 남긴다 — 버리는 대신, 그러나 확정도
    아닌 채로."""
    for ev_type, detail, _tool_name in pending_refusals.values():
        _append_event(events_path, "unverified-refusal", detail)


def _events_path(work: str) -> Path:
    return Path(str(work) + EVENTS_SUFFIX)


def _offset_path(work: str) -> Path:
    return Path(str(work) + OFFSET_SUFFIX)


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


RESPAWN_STATE = ROOT / "runs" / "respawn_state.json"
RESPAWN_MAX_ATTEMPTS = 2
# 이슈 #678: no-progress 스트릭이 매 재스폰마다 진행을 인정해 리셋되더라도,
# 토큰 비용 백스톱으로 전체 재스폰 횟수에 독립적인 절대 상한을 둔다 —
# 진짜 진행 중인 작업(스트릭 리셋)을 방해하지 않을 만큼 넉넉히, 그러나
# 무한하지 않게: RESPAWN_MAX_ATTEMPTS 의 4배.
RESPAWN_ABSOLUTE_MAX = RESPAWN_MAX_ATTEMPTS * 4
_CRASH_COMMENT_MARKER = "[on-the-record] {key}: crashed, respawn cap ({cap}) reached"
_STALL_COMMENT_MARKER = "[on-the-record] {key}: stalled"


def _respawn_state_load() -> dict:
    try:
        return json.loads(RESPAWN_STATE.read_text())
    except (OSError, ValueError):
        return {}


def _respawn_state_save(d: dict) -> None:
    RESPAWN_STATE.parent.mkdir(exist_ok=True)
    RESPAWN_STATE.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def _post_crash_comment(root: Path, issue: int, key: str, work: str, log: str,
                        trigger: str = "crashed", absolute: bool = False) -> None:
    """재스폰 상한 도달 시 이슈에 남기는 코멘트. 멱등: 고정 마커 문자열을
    기존 코멘트에서 먼저 찾는다(`_issue_comments`/`approve_scope` 와 같은
    read-then-check 패턴) — 워치독을 반복 호출해도 두 번째 코멘트는 없다.

    `trigger` (이슈 #247): 어느 경로가 상한을 채웠는지(예:
    `watchdog-observed-crashed` / `self-triggered-abandoned`) 본문에
    남긴다 — 마커 문자열 자체는 이슈 #132 부터 쓰던 그대로 둔다. 멱등성
    키는 트리거 종류와 무관하게 key+상한 하나여야 두 경로가 같은
    attempt-cap 예산을 공유한다는 프로포절의 결정이 그대로 성립한다.

    `absolute` (이슈 #678): no-progress 스트릭 상한(`RESPAWN_MAX_ATTEMPTS`)
    이 아니라 `RESPAWN_ABSOLUTE_MAX` 총 시도 상한이 찼을 때 True — 마커의
    `cap` 값 자체가 달라지므로(2 vs `RESPAWN_ABSOLUTE_MAX`) 두 캡은 서로
    다른 멱등성 키를 쓰고, 어느 쪽이 찼는지가 코멘트 본문에서도 구분된다."""
    cap = RESPAWN_ABSOLUTE_MAX if absolute else RESPAWN_MAX_ATTEMPTS
    marker = _CRASH_COMMENT_MARKER.format(key=key, cap=cap)
    comments, ok = _issue_comments(root, issue)
    if ok and any(marker in c.get("body", "") for c in comments):
        return
    slug = _repo_slug(root)
    if not slug:
        return
    cap_label = "absolute total-respawn ceiling" if absolute else "no-progress respawn cap"
    body = (f"{marker}\n\n"
            f"trigger: {trigger}\nworkspace: {work}\nlog: {log}\n\n"
            f"All {cap} automatic respawns exhausted ({cap_label}) — needs human intervention.")
    r = subprocess.run(["gh", "api", f"repos/{slug}/issues/{issue}/comments",
                    "-f", f"body={body}"], cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[spawn] 이슈 #{issue} 크래시-캡 코멘트 게시 실패 (사람 개입 필요 경고가 "
              f"전달되지 않았다): {r.stderr.strip()}", file=sys.stderr)


def _post_stall_comment(root: Path, issue: int, key: str, work: str, log: str) -> None:
    """이슈 #325: `stalled` 판정을 최초 1회 이슈 코멘트로 남긴다.

    `stalled` 는 재스폰을 트리거하지 않는다(관찰-전용 정책, 이슈 #132 —
    바뀌지 않는다) — 다만 지금까지는 그 판정이 워치독을 부른 터미널의
    `print()` 한 줄로만 남아, 진행 중인 세션과 조용히 멈춘 세션이 밖에서
    구분되지 않았다. `_post_crash_comment` 와 같은 read-then-check
    멱등 패턴: 고정 마커가 이미 있으면 아무것도 하지 않는다."""
    marker = _STALL_COMMENT_MARKER.format(key=key)
    comments, ok = _issue_comments(root, issue)
    if ok and any(marker in c.get("body", "") for c in comments):
        return
    slug = _repo_slug(root)
    if not slug:
        return
    body = (f"{marker}\n\n"
            f"workspace: {work}\nlog: {log}\n\n"
            f"Session judged stalled — automatic respawn will not trigger "
            f"(observation-only policy). Needs human check.")
    subprocess.run(["gh", "api", f"repos/{slug}/issues/{issue}/comments",
                    "-f", f"body={body}"], cwd=root, capture_output=True, text=True)


_SESSION_END_COMMENT_MARKER = "[watch] {key}: session-end:"


def _pr_list_call_ok(root: Path, branch: str) -> bool:
    """`_pr_open_or_merged_for_branch()`(spawn.py:1049)와 같은 `gh pr list`
    호출이되, PR 상태 판정 로직은 재사용하고 이건 그 밑에 깔린 `gh` 호출
    자체가 성공했는지만 본다 — "PR 없음"과 "확인 못 함"을 구별하는 데 쓴다
    (이슈 #534, 프로포절의 empty-state 규정: `gh` 호출이 실패하면
    `(pr-check-failed)` 접미사를 붙인다)."""
    r = subprocess.run(["gh", "pr", "list", "--head", branch, "--state", "all",
                        "--json", "number,state"],
                       cwd=root, capture_output=True, text=True)
    return r.returncode == 0


def _post_session_end_comment(root: Path, issue: int, key: str, work: str,
                              log: str) -> None:
    """이슈 #534: 세션 종료(`normal`)를 GitHub 이슈 코멘트로 durable 하게
    남긴다 — 오케스트레이터의 대화 상태(재무장 루프)가 아니라 이 코멘트가
    "세션이 끝났다"는 사실을 관찰할 다리가 되도록 한다.

    `crashed`/`stalled` 는 이 함수의 범위가 아니다 — 이미
    `_post_crash_comment`/`_post_stall_comment` 가 처리한다. 이 함수는
    `verdict == "normal"` 인 세션에만 코멘트를 남긴다.

    `_post_stall_comment`/`_post_crash_comment` 와 같은 멱등 read-then-check
    패턴: 고정 마커(`{key}` 까지만 — PR 유무와 무관하게 한 번만 남긴다)가
    이미 있으면 아무것도 하지 않는다.
    """
    verdict = session_end_verdict(work, Path(log) if log else None)
    if verdict != "normal":
        return
    marker = _SESSION_END_COMMENT_MARKER.format(key=key)
    comments, ok = _issue_comments(root, issue)
    if ok and any(marker in c.get("body", "") for c in comments):
        return
    slug = _repo_slug(root)
    if not slug:
        return
    branch = subprocess.run(["git", "-C", work, "rev-parse", "--abbrev-ref", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    pr_number = _pr_open_or_merged_for_branch(root, branch) if branch else None
    if pr_number is not None:
        line = f"PR https://github.com/{slug}/pull/{pr_number} opened"
    elif branch and not _pr_list_call_ok(root, branch):
        line = "no PR (pr-check-failed)"
    else:
        line = "no PR"
    body = f"{marker} {line}\n\nworkspace: {work}\nlog: {log}"
    r = subprocess.run(["gh", "api", f"repos/{slug}/issues/{issue}/comments",
                        "-f", f"body={body}"], cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[spawn] 이슈 #{issue} session-end 코멘트 게시 실패: {r.stderr.strip()}",
              file=sys.stderr)


_STRANDED_PUSH_COMMENT_MARKER = "[on-the-record] stranded-relay: {key}"


def _post_stranded_push_comment(root: Path, issue: int, role: str, branch: str,
                                reason: str, detail: str) -> None:
    """이슈 #326: `ensure_pushed()`의 push/PR-생성 실패가 조용히 사라지지
    않게, `_post_crash_comment`와 같은 멱등 read-then-check 패턴으로 이슈에
    코멘트를 남긴다. `key`는 `branch:reason`이라 같은 브랜치의 push-failed와
    이후 pr-create-failed가 서로 다른 마커를 쓰고 둘 다 드러난다."""
    key = f"{branch}:{reason}"
    marker = _STRANDED_PUSH_COMMENT_MARKER.format(key=key)
    comments, ok = _issue_comments(root, issue)
    if ok and any(marker in c.get("body", "") for c in comments):
        return
    slug = _repo_slug(root)
    if not slug:
        return
    body = (f"{marker}\n\n"
            f"branch: {branch}\nreason: {reason}\ndetail: {detail[:200]}\n\n"
            f"The {role}-role session's work stopped here — resume it (retry the "
            f"push/PR creation from the host), or close the issue with a stated "
            f"reason. Needs human intervention.")
    subprocess.run(["gh", "api", f"repos/{slug}/issues/{issue}/comments",
                    "-f", f"body={body}"], cwd=root, capture_output=True, text=True)


def _respawn_fingerprint(work: str) -> dict:
    """이슈 #678: no-progress 스트릭 판정에 쓰는 지문 — git HEAD sha 와
    `board_snapshot()` 의 안정적 해시(정렬된 dict 를 직렬화해 해시하므로,
    같은 내용이면 dict 순서가 달라도 같은 해시). 두 재스폰 시점의 지문이
    같으면 "그 사이에 관측 가능한 진행이 없었다"는 뜻이다."""
    board = board_snapshot(work)
    board_hash = hashlib.sha256(
        json.dumps(board, sort_keys=True).encode("utf-8")).hexdigest()
    return {"head": _git_head(work), "board": board_hash}


_CONTINUATION_PREAMBLE = (
    "workspace contains uncommitted work from the previous session — "
    "verify briefly, then commit/push/PR; do not redo"
)

_RECORD_PATH_RE = re.compile(r"docs/issue-\d+/(reports|proposals)/")


def _classify_workspace_completion(work: str, role: str) -> str:
    """이슈 #1982: 재스폰 시점 dirty workspace 를 "finished"/"unfinished" 로
    분류한다. `git status --porcelain` 이 비어 있으면(clean) 바로
    "unfinished". dirty 라도, 변경분에 이 저장소의 record-shape 규약이
    요구하는 경로(`docs/issue-<n>/reports/**`, `docs/issue-<n>/proposals/**`)
    아래 파일이 없으면 "unfinished". 있으면 그 파일을 읽어 frontmatter 를
    걷어낸 본문이 비어있지 않은 경우에만(= frontmatter-only 스텁이 아닌
    경우에만) "finished" — 프로포절의 conservative-default 결정: 신호가
    모호하거나 얇으면 항상 "unfinished" 쪽으로 판정한다."""
    st = subprocess.run(["git", "-C", work, "status", "--porcelain", "-uall"],
                        capture_output=True, text=True)
    lines = [l for l in st.stdout.splitlines() if l.strip()]
    if not lines:
        return "unfinished"
    record_paths = []
    for line in lines:
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if _RECORD_PATH_RE.search(path):
            record_paths.append(path)
    for rel in record_paths:
        full = Path(work) / rel
        if not full.exists():
            continue
        text = full.read_text(encoding="utf-8", errors="replace")
        body = text
        if text.startswith("---"):
            end = text.find("\n---", 3)
            if end != -1:
                body = text[end + 4:]
        if body.strip():
            return "finished"
    return "unfinished"


def _respawn_or_cap(key: str, work: str, issue: int, role: str, log: str,
                    session_start_ts, state: dict, trigger: str) -> None:
    """공유 재스폰 시퀀스: 원자적 클레임 확인, 상한(`RESPAWN_MAX_ATTEMPTS`)
    확인, `.task.txt` 를 통한 `_spawn_one()` 재생, 상한 도달 시 캡-코멘트.

    이슈 #678: `attempts` 는 이제 no-progress *스트릭* 이다 — 직전 재스폰
    시점에 저장해둔 지문(`_respawn_fingerprint()`)과 지금 지문이 다르면
    (새 커밋 또는 보드 델타) 진행이 있었다고 보고 스트릭을 0 으로 리셋한
    뒤 이번 시도를 1 로 센다. 지문이 없으면(최초 재스폰) 비교할 것이
    없으므로 진행/무진행 어느 쪽으로도 치지 않고 오늘처럼 스트릭을
    1부터 시작한다. `total_attempts` 는 스트릭과 무관하게 매 재스폰마다
    증가하는 별도 카운터로, `RESPAWN_ABSOLUTE_MAX` 총 상한과 비교한다 —
    스트릭이 계속 리셋돼도 무한정 재스폰하지 않게 하는 토큰 비용
    백스톱(프로포절의 명시적 결정).

    이슈 #132 워치독 `crashed` 경로(`_auto_respawn_check()`)와 이슈 #247
    self-trigger 경로(`_spawn_one()` 자신이 정상 종료하며 미커밋 작업을
    감지한 경우, spawn.py `_self_trigger_respawn()`)가 이 시퀀스를
    그대로 공유한다 — 재스폰 로직을 두 벌 두지 않고, attempt-cap 카운터도
    `key` 하나로 공유해 두 경로가 같은 예산을 쓴다(프로포절의 명시적
    결정). `trigger` 는 어느 쪽이 불렀는지 로그/코멘트에 남겨 사람이
    나중에 구분할 수 있게 한다.

    `session_start_ts` 로 세션마다 다른 클레임 키(`.respawn-claim-{ts}`)를
    만든다 — 두 트리거가 같은 세션(같은 ts)을 동시에 관측해도, 실제 락은
    이 원자적 파일 생성 하나뿐이다: O_CREAT|O_EXCL 은 POSIX 에서 프로세스
    간에도 원자적이라 정확히 하나만 이 파일을 만들 수 있다(실측:
    warrant-hunter 리포트, 이슈 #132).
    """
    events_path = _events_path(work)
    events = []
    if events_path.exists():
        for line in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if isinstance(ev, dict):
                events.append(ev)
    already_claimed = any(
        ev.get("type") == "respawn-attempt"
        and isinstance(ev.get("detail"), dict)
        and ev["detail"].get("session_start_ts") == session_start_ts
        for ev in events)
    if already_claimed:
        return
    prior = state.get(key, {})
    attempts = prior.get("attempts", 0)
    total_attempts = prior.get("total_attempts", 0)
    prev_fingerprint = prior.get("fingerprint")
    cur_fingerprint = _respawn_fingerprint(work)
    if prev_fingerprint is not None and cur_fingerprint != prev_fingerprint:
        attempts = 0
    root = Path(work)
    if total_attempts >= RESPAWN_ABSOLUTE_MAX:
        _post_crash_comment(root, issue, key, work, log, trigger, absolute=True)
        return
    if attempts >= RESPAWN_MAX_ATTEMPTS:
        _post_crash_comment(root, issue, key, work, log, trigger)
        return
    claim_path = Path(str(work) + f".respawn-claim-{session_start_ts}")
    try:
        fd = os.open(str(claim_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        return
    task_path = Path(str(work) + ".task.txt")
    if not task_path.exists():
        print(f"[respawn] {key}: {trigger} 인데 {task_path} 가 없어 재스폰 불가 "
              f"— 사람이 직접 재스폰해야 한다", file=sys.stderr)
        return
    task = task_path.read_text(encoding="utf-8")
    if _classify_workspace_completion(work, role) == "finished":
        task = _CONTINUATION_PREAMBLE + "\n\n" + task
    attempt_n = attempts + 1
    total_attempt_n = total_attempts + 1
    _append_event(events_path, "respawn-attempt",
                  {"session_start_ts": session_start_ts, "attempt": attempt_n})
    state[key] = {"attempts": attempt_n, "total_attempts": total_attempt_n,
                  "fingerprint": cur_fingerprint}
    _respawn_state_save(state)
    print(f"[respawn] {key}: {trigger} — 재스폰 시도 {attempt_n}/{RESPAWN_MAX_ATTEMPTS} "
          f"(총 {total_attempt_n}/{RESPAWN_ABSOLUTE_MAX})",
          file=sys.stderr)
    _spawn_one(work, role, task, unattended=True, issue=issue, bounded=True)


def _auto_respawn_check(key: str, entry: dict, state: dict) -> None:
    """죽은 로스터 엔트리 하나에 대해 `crashed` 인지 판정하고, 그렇다면
    `_respawn_or_cap()` 에 넘긴다. `stalled`/`normal`/`in-progress` 는
    재스폰을 걸지 않는다(관찰-전용 계약 유지, 이슈 #132) — 다만 `stalled`
    는 최초 1회 이슈 코멘트로 남는다(이슈 #325): 재스폰하지 않는 것과
    아무도 모르게 재스폰하지 않는 것은 다르다."""
    work = entry.get("work")
    issue = entry.get("issue")
    role = entry.get("role")
    if not work or issue is None or not role:
        return
    log_path = Path(entry["log"]) if entry.get("log") else None
    verdict = session_end_verdict(work, log_path)
    print(f"[watchdog] {key}: {verdict}")
    if verdict == "stalled":
        _post_stall_comment(Path(work), issue, key, work, entry.get("log", ""))
        return
    if verdict != "crashed":
        return
    events_path = _events_path(work)
    events = []
    if events_path.exists():
        for line in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if isinstance(ev, dict):
                events.append(ev)
    start_ts = None
    for ev in reversed(events):
        if ev.get("type") == "session-start":
            start_ts = (ev.get("detail") or {}).get("ts")
            break
    _respawn_or_cap(key, work, issue, role, entry.get("log", ""), start_ts, state,
                    "watchdog-observed-crashed")


_ABANDONED_WORK_OUTCOMES = ("uncommitted-work", "failed-no-commit", "silent-failure")


def _self_trigger_respawn(outcome: str, roster_key: str, work: str, issue: int,
                          role: str, log: str, session_start_ts) -> None:
    """이슈 #247/#675: `_spawn_one()` 자신이 정상 종료(`session-end` 가 이미
    남는다)했지만 outcome 이 미커밋-방치 신호(`uncommitted-work`/
    `failed-no-commit`) 이거나, 원인 없이 그냥 멈춘 `silent-failure` 일 때,
    다음 `spawn.py watchdog` 틱을 기다리지 않고 지금 이 자리에서 바로
    `_respawn_or_cap()` 을 부른다.

    `roster_watchdog()`/`_auto_respawn_check()` 의 crashed 판정은 이
    경우에 절대 못 걸린다 — `roster_remove()` 가 `proc.wait()` 직후
    동기적으로 로스터 엔트리를 지우고, `session-end` 이벤트도 이미
    남으므로(spawn.py `_spawn_one()` 끝부분), 이후 어떤 워치독 틱도
    dead-but-registered 엔트리를 볼 수 없다(survey.md). `refused`/
    `waiting-on-human` 은 정당한 게이트 거부/대기이지 이 결함의 모양이
    아니라서 여기서 건드리지 않는다(프로포절의 두 번째 기각안). 다만
    `silent-failure` 는 `fail_closed_downgrade()` 를 이미 거쳐 실제로는
    진행됐다고 판명되면 `progressed` 로 승격되므로, 여기 도달하는
    `silent-failure` 는 이미 원인 없는(causeless) 경우로 걸러져 있다.
    """
    if outcome not in _ABANDONED_WORK_OUTCOMES:
        return
    state = _respawn_state_load()
    trigger = ("self-triggered-causeless" if outcome == "silent-failure"
               else "self-triggered-abandoned")
    _respawn_or_cap(roster_key, work, issue, role, log, session_start_ts, state,
                    trigger)


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
        d = json.loads(WORKSPACE_INDEX.read_text())
    except (OSError, ValueError):
        return {}
    migrated = False
    for key in list(d.keys()):
        if _LEGACY_WORKSPACE_KEY_RE.match(key):
            entry = d[key]
            new_key = f"{_repo_identity(entry['work'])}/{key}"
            if new_key in d and new_key != key:
                raise RuntimeError(
                    f"workspace index migration collision: {key!r} -> "
                    f"{new_key!r} already exists (live entries: "
                    f"{d[new_key]!r} vs {entry!r})")
            del d[key]
            d[new_key] = entry
            migrated = True
    if migrated:
        WORKSPACE_INDEX.write_text(json.dumps(d, indent=2, ensure_ascii=False))
    return d


@contextlib.contextmanager
def _workspace_index_locked():
    """이슈 #857 finding 4(경고 발견): `WORKSPACE_INDEX` 의 load-mutate-save
    구간에 `ROSTER`(`_roster_locked()`)와 달리 잠금이 없어, 서로 다른 키에
    쓰는 두 프로세스가 동시에 로드-변경-저장하면 나중에 저장한 쪽이 먼저
    저장한 쪽의 키를 조용히 지운다 — `_workspace_index_put()` 자체의
    같은-키 충돌 가드(위)는 한 프로세스의 로드 시점 안에서만 보이므로 이
    레이스를 못 잡는다. `ROSTER` 와 같은 fcntl 잠금 파일 패턴으로 직렬화."""
    lock_path = WORKSPACE_INDEX.with_name(WORKSPACE_INDEX.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def _workspace_index_put(issue: int, role: str, work: str, log: str,
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
    WORKSPACE_INDEX.parent.mkdir(parents=True, exist_ok=True)
    with _workspace_index_locked():
        d = _workspace_index_load()
        key = f"{_repo_identity(work)}/issue-{issue}/{role}"
        existing = d.get(key)
        if existing is not None and existing.get("work") != work:
            raise RuntimeError(
                f"workspace index collision on {key!r}: existing entry "
                f"{existing!r} has a different work dir than {work!r} — "
                f"refusing to overwrite silently (issue #533)")
        entry = {"work": work, "log": log, "role": role}
        if watcher_pid is not None:
            entry["watcher_pid"] = watcher_pid
        if watcher_armed_at is not None:
            entry["watcher_armed_at"] = watcher_armed_at
        d[key] = entry
        WORKSPACE_INDEX.write_text(json.dumps(d, indent=2, ensure_ascii=False))


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
    seen = _read_offset(offset_path)
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
                _write_offset(offset_path, seen + 1)
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
                      f"것이다 — clean 이력을 확인하거나 역할을 다시 스폰하라",
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
            return WATCH_WALLCLOCK_RC
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
    roster = _roster_load()
    live = []
    for k, v in matches:
        role = v.get("role") or k.rsplit("/", 1)[1]
        e = roster.get(f"issue-{issue}/{role}")
        if e is not None and _alive(e.get("pid", 0)):
            live.append((k, v))
    return live


def _ambiguous_watch_exit(issue: int, matches: list, repo: str | None) -> None:
    """이슈 #554: 애매할 때(살아있는 세션이 0개 또는 2개 이상) 그대로
    붙여넣을 수 있는 명령을 에러에 찍는다 — `--role` 없이 재시도하면 같은
    메시지가 또 나오는 죽은 재시도 구간을 없앤다."""
    cwd_flag = f" -C {repo}" if repo else ""
    roles = [v.get("role") or k.rsplit("/", 1)[1] for k, v in matches]
    cmds = "; ".join(
        f"spawn.py watch --issue {issue} --role {r}{cwd_flag}" for r in roles)
    sys.exit(f"이슈 {issue} 에 역할이 여럿 기록돼 있다 — 역할을 지정하라 "
             f"(후보: {', '.join(roles)}): {cmds}")


def _roster_fallback_entry(issue: int, role: str | None, repo: str | None):
    """이슈 #1585: `watch`(워크스페이스 인덱스)와 `ps`(ROSTER)가 서로 다른
    소스를 읽어, 스폰 직후 워크스페이스 인덱스 쓰기가 아직 안 보이는
    짧은 창에서 `ps` 는 RUNNING 인데 `watch` 는 '기록 없음'을 내는 레이스가
    있었다(실측: 이슈-1582 phase-2 드라이브, 5초 지연 재시도에도 재현).
    ROSTER 엔트리도 `work`/`log` 필드를 들고 있으므로(roster_register 호출부
    참고), 워크스페이스 인덱스에 없을 때 ROSTER 의 살아있는 엔트리로부터
    같은 모양의 엔트리를 재구성해 두 소스가 존재 여부에서 일치하게 한다.
    조회만 하고 아무것도 기다리지 않는다 — 블로킹을 새로 넣지 않는다."""
    roster = _roster_load()
    if role:
        e = roster.get(f"issue-{issue}/{role}")
        if not (e is not None and _alive(e.get("pid", 0)) and e.get("work") and e.get("log")):
            return None, None
        if repo is not None and _repo_identity(e["work"]) != repo:
            return None, None
        key = f"{_repo_identity(e['work'])}/issue-{issue}/{role}"
        return key, {"work": e["work"], "log": e["log"]}
    candidates = []
    for k, e in roster.items():
        found_role = e.get("role")
        if found_role is None:
            m = re.match(rf"^issue-{issue}/([^/]+)$", k)
            if not m:
                continue
            found_role = m.group(1)
        elif not k.startswith(f"issue-{issue}/"):
            continue
        if not (_alive(e.get("pid", 0)) and e.get("work") and e.get("log")):
            continue
        if repo is not None and _repo_identity(e["work"]) != repo:
            continue
        candidates.append((found_role, e))
    if len(candidates) != 1:
        return None, None
    found_role, e = candidates[0]
    key = f"{_repo_identity(e['work'])}/issue-{issue}/{found_role}"
    return key, {"work": e["work"], "log": e["log"]}


def _lookup_roster_entry(idx: dict, issue: int, role: str | None, repo: str | None = None):
    """이슈 #533: `repo` 가 주어지면 그 레포로만 조회를 좁힌다 — `-C` 가
    지금까지 조회에 안 먹히던 구멍을 막는다. 안 주면(기존 기본값) 모든
    레포를 대상으로 이슈+역할 접미사로 매칭하던 예전 동작을 유지한다.

    이슈 #554: 역할을 안 줬는데 매치가 여럿이면, 그중 살아있는 세션이
    정확히 하나면 그걸 자동 선택한다 — watch 는 어차피 실행 중인 세션만
    보고하므로 그게 유일하게 뜻이 통하는 선택이다. 0개 또는 2개 이상
    살아있으면 여전히 애매하니 `--role`을 요구한다(실행 가능한 명령까지
    같이 찍는다)."""
    key, entry = _lookup_workspace_entry(idx, issue, role, repo=repo)
    if entry is None:
        fb_key, fb_entry = _roster_fallback_entry(issue, role, repo)
        if fb_entry is not None:
            return fb_key, fb_entry
    return key, entry


def _lookup_workspace_entry(idx: dict, issue: int, role: str | None, repo: str | None = None):
    if repo is not None:
        if role:
            key = f"{repo}/issue-{issue}/{role}"
            entry = idx.get(key)
        else:
            matches = [(k, v) for k, v in idx.items()
                       if k.startswith(f"{repo}/issue-{issue}/")]
            if len(matches) > 1:
                live = _live_roster_matches(matches, issue)
                if len(live) == 1:
                    matches = live
                else:
                    _ambiguous_watch_exit(issue, matches, repo)
            key = matches[0][0] if matches else None
            entry = matches[0][1] if matches else None
        return key, entry
    if role:
        matches = [(k, v) for k, v in idx.items() if k.endswith(f"/issue-{issue}/{role}")]
        if len(matches) > 1:
            sys.exit(f"이슈 {issue}/{role} 이 레포 여럿에 기록돼 있다 — -C 로 "
                     "레포를 지정하라: " + ", ".join(k.rsplit("/issue-", 1)[0] for k, _ in matches))
        key = matches[0][0] if matches else None
        entry = matches[0][1] if matches else None
    else:
        matches = [(k, v) for k, v in idx.items() if f"/issue-{issue}/" in k]
        if len(matches) > 1:
            live = _live_roster_matches(matches, issue)
            if len(live) == 1:
                matches = live
            else:
                _ambiguous_watch_exit(issue, matches, repo)
        key = matches[0][0] if matches else None
        entry = matches[0][1] if matches else None
    return key, entry


def _watch(issue: int, role: str | None, stall_timeout_min: float,
           follow: bool = False, repo: str | None = None,
           max_wait_min: float | None = None, self_heal: bool = False) -> int:
    idx = _workspace_index_load()
    key, entry = _lookup_roster_entry(idx, issue, role, repo=repo)
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
            idx = _workspace_index_load()
            key, entry = _lookup_roster_entry(idx, issue, role, repo=repo)
    if entry is None:
        print(f"[watch] issue-{issue}{'/' + role if role else ''}: 기록 없음 — "
              f"아직 스폰된 적이 없다", file=sys.stderr)
        return 1
    work = entry["work"]
    events_path = _events_path(work)
    offset_path = _offset_path(work)
    log_path = Path(entry["log"])
    # 이슈 #557: 무장 시점에 살아있는 세션의 pid 를 명부에서 찾아, 그
    # session-start 줄보다 앞선(=이전 세션 몫인) 이벤트는 커서가 절대
    # 재생하지 않도록 offset 바닥을 그 줄로 끌어올린다. pid 를 못 찾으면
    # (명부 엔트리 부재) 오늘의 동작(스코프 없음)으로 그대로 떨어진다.
    m = re.search(r"issue-\d+/[^/]+$", key) if key else None
    roster_entry = _roster_load().get(m.group(0)) if m else None
    live_pid = roster_entry.get("pid") if roster_entry else None
    session_idx = _live_session_start_index(events_path, live_pid)
    session_tag = None
    if session_idx is not None:
        if _read_offset(offset_path) < session_idx:
            _write_offset(offset_path, session_idx)
        lines = events_path.read_text(encoding="utf-8").splitlines()
        detail = json.loads(lines[session_idx]).get("detail", {})
        session_tag = (detail.get("pid"), detail.get("ts"))
    if not follow:
        return _await_bounded(events_path, offset_path, stall_timeout_min, log_path,
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
    follow_role_m = re.search(r"issue-\d+/([^/]+)$", key) if key else None
    follow_role = follow_role_m.group(1) if follow_role_m else role
    current_watcher_pid = entry.get("watcher_pid")
    if not (current_watcher_pid is not None and
            _watcher_looks_real(current_watcher_pid, issue, follow_role)):
        _workspace_index_put(issue, follow_role, work, str(log_path),
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
        before = _read_offset(offset_path)
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
                return WATCH_WALLCLOCK_RC
            call_max_wait_s = remaining
        rc = _await_bounded(events_path, offset_path, stall_timeout_min, log_path,
                             session_tag=session_tag, show_banner=not banner_shown,
                             max_wait_s=call_max_wait_s)
        if rc == WATCH_WALLCLOCK_RC:
            if self_heal:
                follow_start = time.monotonic()
                last_progress = time.monotonic()
                continue
            return rc
        after = _read_offset(offset_path)
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
        roster_entry = _roster_load().get(m.group(0)) if m else None
        pid = roster_entry.get("wrapper_pid") if roster_entry else None
        # 명부 엔트리 부재는 사망 신호로 안 쓴다(이슈 #266) — `_spawn_one()`의
        # 후처리 꼬리 동안 `roster_remove`(spawn.py:2995)가 `session-end`
        # 기록(spawn.py:3097)보다 먼저 실행돼 그 구간 전체에서 엔트리가
        # 없다. 엔트리가 있고 그 안의 wrapper_pid 가 죽어 있을 때만 크래시로
        # 본다 — 엔트리 부재는 불명으로 취급해 stall 안전망까지 계속 대기한다.
        if pid is not None and not _alive(pid):
            print(f"[watch] 세션 프로세스가 사라졌다(pid {pid}) — session-end "
                  f"없이 끝났다. 크래시로 보고 멈춘다", file=sys.stderr)
            _append_event(events_path, "watcher-ended-without-session-end",
                          {"pid": pid, "reason": "crash"})
            return WATCH_CRASH_RC
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


def _rearm_watcher_detached(issue: int, role: str | None, stall_timeout_min: float,
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
    with _workspace_index_locked():
        idx = _workspace_index_load()
        key, entry = _lookup_roster_entry(idx, issue, role, repo=repo)
        if entry is None:
            print(f"[watch] issue-{issue}{'/' + role if role else ''}: 기록 없음 — "
                  f"재무장할 대상이 없다", file=sys.stderr)
            return 1
        work = entry["work"]
        log_path = entry["log"]
        m = re.search(r"issue-\d+/([^/]+)$", key) if key else None
        rearm_role = m.group(1) if m else role
        current_watcher_pid = entry.get("watcher_pid")
        if (current_watcher_pid is not None and
                _watcher_looks_real(current_watcher_pid, issue, rearm_role)):
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
                if silence_min > WATCHDOG_SILENCE_MIN:
                    session_log_path = Path(str(log_path)) if log_path else None
                    if (session_log_path is not None and session_log_path.exists()
                            and session_log_path.stat().st_mtime > baseline):
                        stale = True
            if not stale:
                print(f"[watch] issue-{issue}/{rearm_role}: 워처 pid "
                      f"{current_watcher_pid} 이미 살아있다 — 재무장 안 함",
                      file=sys.stderr)
                return 0
            print(f"[watch] issue-{issue}/{rearm_role}: 워처 pid "
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
                    [sys.executable, str(Path(__file__).resolve()),
                     "-C", resolved_cwd,
                     "watch", "--issue", str(issue), "--role", rearm_role,
                     "--follow", "--self-heal",
                     "--stall-timeout", str(stall_timeout_min)],
                    stdin=subprocess.DEVNULL, stdout=wf,
                    stderr=subprocess.STDOUT, start_new_session=True,
                )
        except OSError as exc:
            print(f"[watch] issue-{issue}/{rearm_role}: 워처 재무장 실패 — {exc}",
                  file=sys.stderr)
            return 1
        d = _workspace_index_load()
        existing = d.get(key)
        if existing is not None and existing.get("work") != work:
            raise RuntimeError(
                f"workspace index collision on {key!r}: existing entry "
                f"{existing!r} has a different work dir than {work!r} — "
                f"refusing to overwrite silently (issue #533)")
        d[key] = {"work": work, "log": log_path,
                  "watcher_pid": wproc.pid, "watcher_armed_at": time.time()}
        WORKSPACE_INDEX.write_text(json.dumps(d, indent=2, ensure_ascii=False))
        print(f"[watch] issue-{issue}/{rearm_role}: 워처 재무장 pid {wproc.pid} "
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
            idx = _workspace_index_load()
            for key, entry in sorted(idx.items()):
                if key in seen_end:
                    continue
                work = entry.get("work")
                log_path = Path(entry["log"]) if entry.get("log") else None
                if not work or log_path is None:
                    continue
                events_path = _events_path(work)
                offset_path = _offset_path(work)
                seen = _read_offset(offset_path)
                if not events_path.exists():
                    continue
                lines = events_path.read_text(encoding="utf-8").splitlines()
                while len(lines) > seen:
                    ev = json.loads(lines[seen])
                    seen += 1
                    _write_offset(offset_path, seen)
                    print(f"[watch-all] {key} {ev['type']}: {ev['detail']}")
                    if ev["type"] == "session-end":
                        seen_end.add(key)
                        break
            if until_idle and all(key in seen_end for key in idx):
                return 0
            time.sleep(poll_s)
    except KeyboardInterrupt:
        return 0


def roster_kill(issue: int, role: str) -> int:
    d = _roster_load()
    key = f"issue-{issue}/{role}"
    e = d.get(key)
    if not e:
        print(f"로스터에 없다: {key}", file=sys.stderr)
        return 1
    pid = e.get("pid", 0)
    if _alive(pid):
        os.kill(pid, 15)
        print(f"종료 신호를 보냈다: {key} (pid {pid}). 워크스페이스와 라이브 "
              f"로그는 남는다 — 재스폰이 이어받는다.")
    else:
        print(f"이미 죽어 있다: {key}")
    roster_remove(key)
    return 0


def ledger_write(entry: dict) -> Path:
    """runs/ledger.jsonl 에 한 줄. runs/ 는 gitignore 되어 있다 — 측정 데이터는
    소스가 아니다."""
    d = ROOT / "runs"
    d.mkdir(exist_ok=True)
    p = d / "ledger.jsonl"
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return p


def _core_candidates() -> list[tuple[str, Path]]:
    """core_root() 가 순서대로 보는 로컬 오버라이드 후보 (라벨, 경로).
    관리 클론(runs/rulebooks/tokenmaxxxer-core)은 이 목록 밖 — 둘 다
    없을 때만 core_root() 가 그리로 떨어지는 별도 단계라 후보가 아니다.
    """
    return [
        ("TOKENMAXXXER_CORE", os.environ.get("TOKENMAXXXER_CORE")),
        ("TOKENMAXXXER_RULEBOOKS/tokenmaxxxer-core",
         "$TOKENMAXXXER_RULEBOOKS/tokenmaxxxer-core"),
    ]


def _skill_repo_valid(d: Path) -> bool:
    """`d` 를 `resolved_skill_dirs()` 가 이미 쓰는 것과 같은 바로 그 기준으로
    "실제 체크아웃"으로 본다: non-dot 서브디렉터리가 하나라도 있는
    디렉터리(요구사항 2 — env/sibling/managed 세 경로 모두 같은 바)."""
    if not d.is_dir():
        return False
    return any(p.is_dir() and not p.name.startswith(".") for p in d.iterdir())


def _skill_repo_managed_root() -> Path | None:
    """관리 클론(이슈 #1789): env 도 형제 체크아웃도 없을 때 on-the-record 가
    직접 `https://github.com/tokenmaxxxer/skill-repository` 를 관리 영역에
    받아 쓴다 — `core_root()` 가 이미 쓰는 다섯 단계
    (로컬 오버라이드 확인은 호출자 쪽에서 이미 끝남 → 관리 디렉터리 유효성
    확인 → 신선하면 재사용 → 아니면 pull-or-clone → 재확인) 를 그대로
    따른다. 네트워크가 죽었을 때 기존 관리 클론이 있으면 그걸 그대로 쓴다
    (오프라인 재사용, 요구사항 1).

    저장소 최상위가 아니라 그 안의 `skills/` 서브디렉터리를 돌려준다 —
    env(`MUSTER_SKILL_REPO`)와 sibling(`$TOKENMAXXXER_RULEBOOKS/
    skill-repository`) 두 경로 모두 실측상 이미 `skills/` 를 직접 가리키고
    있고(레포 최상위에는 skills 외에도 docs/scripts/install.sh 가 있다),
    `resolved_skill_dirs()` 는 그 셋을 구분 없이 같은 root 로 받는다 —
    요구사항 2 의 "env-pointed checkout 과 동일한 스킬 해석"이 성립하려면
    관리 클론도 같은 `skills/` 레벨을 돌려줘야 한다."""
    d = ROOT / "runs" / "rulebooks" / "skill-repository"
    d.parent.mkdir(parents=True, exist_ok=True)
    with _locked_rulebook_dir(d):
        skills_dir = d / "skills"
        if _skill_repo_valid(skills_dir):
            if not _pull_is_fresh(d):
                _run_net(["git", "-C", str(d), "pull", "-q", "--ff-only"],
                         "[skill-repo] pull")
                _mark_pulled(d)
            return skills_dir
        try:
            print("[skill-repo] skill-repository 를 받는 중", file=sys.stderr)
            _run_net(["git", "clone", "-q",
                     "https://github.com/tokenmaxxxer/skill-repository.git",
                     str(d)], "[skill-repo] clone", timeout=CLONE_TIMEOUT)
            _mark_pulled(d)
        except OSError:
            pass
        if _skill_repo_valid(skills_dir):
            return skills_dir
    return None


def _skill_repo_root() -> Path | None:
    """`--skills` 가 마운트할 skill-repository 체크아웃 루트. 순서:
    `MUSTER_SKILL_REPO` env > 형제 클론 (`$TOKENMAXXXER_RULEBOOKS/
    skill-repository`) > 관리 클론(이슈 #1789 — skill-repository가 공개된
    뒤로는 on-the-record 소유 클론이 다른 관리 체크아웃과 같은 fallback을
    쓸 수 있다). 셋 다 없으면 `None`."""
    env_value = os.environ.get("MUSTER_SKILL_REPO")
    if env_value:
        p = Path(os.path.expanduser(os.path.expandvars(env_value)))
        if p.is_dir():
            return p
    sibling = os.path.expandvars("$TOKENMAXXXER_RULEBOOKS/skill-repository")
    if "$" not in sibling:
        p = Path(os.path.expanduser(sibling))
        if p.is_dir():
            return p
    return _skill_repo_managed_root()


def resolved_skill_dirs(skills_csv: str | None,
                         repo_root: Path | None) -> list[Path]:
    """`--skills a,b,c` 를 skill-repository 체크아웃 안의 디렉터리 목록으로
    푼다. `skills_csv` 가 비면 빈 목록(마운트 없음, byte-identical 경로).
    이름 하나라도 `<repo_root>/<name>` 으로 해석되지 않으면 워크스페이스/
    브랜치를 건드리기 전에 fail-closed(이슈 #1742 요구사항 2)."""
    names = [n.strip() for n in (skills_csv or "").split(",") if n.strip()]
    if not names:
        return []
    if repo_root is None:
        sys.exit("--skills: skill-repository 체크아웃을 못 찾았다 — "
                  "MUSTER_SKILL_REPO 나 $TOKENMAXXXER_RULEBOOKS/skill-repository 를 확인하고, "
                  "관리 클론도 시도했지만(네트워크나 기존 클론 없음) 실패했다")
    available = sorted(p.name for p in repo_root.iterdir()
                        if p.is_dir() and not p.name.startswith("."))
    unknown = [n for n in names if n not in available]
    if unknown:
        sys.exit(f"--skills: 모르는 스킬 {', '.join(unknown)} "
                  f"— 쓸 수 있는 이름: {', '.join(available)}")
    return [repo_root / n for n in names]


def _installed_plugin_skill_dirs() -> dict[str, list[tuple[str, Path, str]]]:
    """`~/.claude/plugins/installed_plugins.json` (실제 shape:
    `{"plugins": {"<name>@<marketplace>": [{"installPath":...,
    "version"|"gitCommitSha":...}, ...]}}`, `_installed()` 와 같은 파일)을
    읽어 설치된 각 플러그인의 `skills/<name>/` 서브디렉터리를 이름별로
    인덱싱한다: name -> [(qualifier "<name>@<marketplace>", 디렉터리,
    version-or-sha 문자열), ...]. 파일이 없거나 못 읽으면 빈 매핑(이슈
    #1774 요구사항 4: 이 함수는 `--skills` 가 실제로 이름을 낼 때만
    불린다)."""
    p = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    try:
        data = json.loads(p.read_text())
    except (OSError, ValueError):
        return {}
    plugins = data.get("plugins") if isinstance(data, dict) else None
    if not isinstance(plugins, dict):
        return {}
    index: dict[str, list[tuple[str, Path, str]]] = {}
    for qualifier, entries in plugins.items():
        if not isinstance(entries, list):
            continue
        for e in entries:
            if not isinstance(e, dict):
                continue
            install_path = e.get("installPath")
            if not install_path:
                continue
            skills_root = Path(install_path) / "skills"
            if not skills_root.is_dir():
                continue
            version = e.get("version") or e.get("gitCommitSha") or "?"
            for skill_dir in skills_root.iterdir():
                if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                    index.setdefault(skill_dir.name, []).append(
                        (str(qualifier), skill_dir, str(version)))
    return index


def _local_skill_dirs(root: Path) -> dict[str, Path]:
    """`root` 바로 아래의 디렉터리들을 이름 -> 경로로 나열한다(이슈 #1774
    tiers 3/4 공용 — 호출자가 어느 root 를 넘기는지로만 tier 가 갈린다).
    `root` 가 없으면 빈 매핑."""
    if not root.is_dir():
        return {}
    return {p.name: p for p in root.iterdir()
            if p.is_dir() and not p.name.startswith(".")}


def _skill_content_hash(skill_dir: Path) -> str:
    """tier 3/4 소스 정체성(이슈 #1774): 저장소 sha 도 플러그인 버전도 없는
    로컬 디렉터리라, `SKILL.md` 내용의 sha256 을 그 대신 쓴다(proposal
    Rationale: 이 저장소의 스킬 정의 관례가 이미 `SKILL.md` 를 정식 정의
    파일로 취급한다). `SKILL.md` 가 없으면 빈 바이트의 해시."""
    try:
        data = (skill_dir / "SKILL.md").read_bytes()
    except OSError:
        data = b""
    return hashlib.sha256(data).hexdigest()


def _describe_skill_match(m: dict) -> str:
    """에러 메시지/태스크 문구에 쓸, 소스 하나를 사람이 읽는 한 줄로."""
    if m["source"] == "skill-repo":
        return f"skill-repository({m['sha']})"
    if m["source"] == "plugin":
        return f"plugin {m['plugin']}@{m['version']}"
    if m["source"] == "local-user":
        return f"~/.claude/skills ({m['path']})"
    if m["source"] == "local-repo":
        return f".claude/skills ({m['path']})"
    return m["source"]


def resolved_skill_sources(skills_csv: str | None, repo_root: Path | None,
                            home: Path | None = None,
                            target_repo_root: Path | None = None) -> list[dict]:
    """이슈 #1774: `--skills a,b,c` 를 네 소스(skill-repository, 설치된
    플러그인, `~/.claude/skills`, 타깃 저장소 `.claude/skills`)에 걸쳐
    푼다. `skills_csv` 가 비면 빈 목록(마운트 없음, byte-identical 경로 —
    이 경우 네 소스 중 어느 것도 읽지 않는다, 요구사항 4).

    이름 하나가 소스 하나에서만 잡히면 그 소스로 확정. 소스 두 개 이상에서
    잡히면(같은 tier 안의 플러그인-대-플러그인 충돌 포함) 워크스페이스/
    브랜치를 건드리기 전에 fail-closed, 잡힌 소스를 전부 이름 붙여
    보고한다 — 어느 tier 도 다른 tier 를 조용히 가리지 않는다(이슈 #1774
    SCOPE EXTENSION). 어디서도 안 잡히면 오늘과 같은 fail-closed.

    각 소스가 가리키는 디렉터리에 `hooks/` 서브디렉터리가 있으면 —
    스킬 마운트는 가이던스 전용이라는 원칙 위반 — 역시 워크스페이스/
    브랜치 전에 fail-closed(네 소스 모두 동일 규칙).

    반환값은 이름당 dict 하나: 최소 `name`/`source`/`dir` 를 들고, 소스별
    정체성 필드(`sha`|`plugin`+`version`|`path`+`content_sha256`)가
    추가된다."""
    names = [n.strip() for n in (skills_csv or "").split(",") if n.strip()]
    if not names:
        return []
    home = home or Path.home()
    plugin_index = _installed_plugin_skill_dirs()
    tier3 = _local_skill_dirs(home / ".claude" / "skills")
    tier4 = (_local_skill_dirs(target_repo_root / ".claude" / "skills")
             if target_repo_root is not None else {})
    results = []
    for name in names:
        matches: list[dict] = []
        if repo_root is not None and repo_root.is_dir():
            cand = repo_root / name
            if cand.is_dir() and not name.startswith("."):
                matches.append({"source": "skill-repo", "dir": cand,
                                 "sha": skill_repo_sha(repo_root)})
        for qualifier, plugin_skill_dir, version in plugin_index.get(name, []):
            matches.append({"source": "plugin", "dir": plugin_skill_dir,
                             "plugin": qualifier, "version": version})
        if name in tier3:
            d = tier3[name]
            matches.append({"source": "local-user", "dir": d, "path": str(d),
                             "content_sha256": _skill_content_hash(d)})
        if name in tier4:
            d = tier4[name]
            matches.append({"source": "local-repo", "dir": d, "path": str(d),
                             "content_sha256": _skill_content_hash(d)})
        if not matches:
            sys.exit(
                f"--skills: 모르는 스킬 {name} — skill-repository, 설치된 "
                f"플러그인, ~/.claude/skills, 타깃 저장소 .claude/skills "
                f"어디에도 없다")
        if len(matches) > 1:
            sys.exit(
                f"--skills: {name} 가 둘 이상의 소스에서 겹친다 — "
                f"{', '.join(_describe_skill_match(m) for m in matches)} "
                f"(precedence 는 검색 순서일 뿐 충돌을 가리지 않는다)")
        m = matches[0]
        if (m["dir"] / "hooks").is_dir():
            sys.exit(
                f"--skills: {name} ({_describe_skill_match(m)}) 가 hooks/ "
                f"를 들고 있다 — 스킬 마운트는 가이던스 전용이다(집행은 "
                f"core 훅뿐)")
        m["name"] = name
        results.append(m)
    return results


def skill_repo_sha(repo_root: Path) -> str:
    """`repo_root` 체크아웃이 물고 있는 커밋(짧은 sha). `rulebook_version()`
    과 같은 shape — git 실패는 조용히 "?" 로 대체."""
    p = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "--short=7", "HEAD"],
                        capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else "?"


# 이슈 #1955: 전이용 역할-소스 허용목록(#1758)/rulebook 해석 경로 은퇴 —
# 매핑은 더 이상 대상 저장소의 선택적 파일이 아니라 여기 고정된다. 43개
# 역할 전부가 예전 docs/specs 아래 허용목록 파일과 값이 같다(그 파일이
# 이미 모든 역할을 매핑하고 있었다 — 이 상수는 그 내용을 그대로 옮긴 것).
_ROLE_SKILLS = {
    'accessibility': ['accessibility-aria-and-contrast-rules'],
    'api-design': ['api-design-error-design', 'api-design-http-semantics', 'api-design-payload-design', 'api-design-resource-modeling', 'api-design-tool-landscape', 'api-design-versioning-evolution'],
    'architecture': ['architecture-coupling-classification', 'architecture-decomposition-strategy', 'architecture-dependency-direction', 'architecture-interface-contract-shape', 'architecture-module-boundary-definition'],
    'brand-design': ['brand-design-brand-consistency-governance', 'brand-design-brand-identity-strategy', 'brand-design-color-visibility', 'brand-design-logo-clear-space-size', 'brand-design-typography-pairing'],
    'capacity-planning': ['capacity-planning-cost-attribution-at-trigger', 'capacity-planning-demand-shape-and-forecast-method', 'capacity-planning-expansion-trigger-threshold-sizing', 'capacity-planning-headroom-band-and-degradation-risk', 'capacity-planning-safety-buffer-sizing-by-criticality'],
    'conformance-review': ['conformance-review-requirement-extraction', 'conformance-review-sampling-derivation', 'conformance-review-traceability-and-evidence', 'conformance-review-verdict-assignment', 'conformance-review-verification-method-selection', 'conformance-review-finding-record', 'conformance-review-severity-classification'],
    'content-design': ['content-design-operational-playbook'],
    'customer-support': ['customer-support-escalation-path', 'customer-support-five-whys-recurring-scope', 'customer-support-kcs-article-authoring', 'customer-support-research-log', 'customer-support-sla-tier-priority', 'customer-support-subtraction-comprehensibility'],
    'data-engineering': ['data-engineering-data-quality', 'data-engineering-failure-handling', 'data-engineering-pipeline-design'],
    'data-modeling': ['data-modeling-datavault', 'data-modeling-inmon', 'data-modeling-kimball', 'data-modeling-structure'],
    'defect-verification': ['defect-verification-evidence-artifact-completeness', 'defect-verification-independence-from-upstream-verdicts', 'defect-verification-reproduction-evidence-quality', 'defect-verification-severity-band-assignment', 'verify-finding-record', 'verify-severity-classification'],
    'devrel': ['devrel-channel-convention', 'devrel-content-comprehensibility', 'devrel-program-subtraction'],
    'finance-unit-economics': ['finance-unit-economics-cac-payback', 'finance-unit-economics-evidence-chain', 'finance-unit-economics-ltv-cac-band', 'finance-unit-economics-ltv-churn-assumption', 'finance-unit-economics-proposal-shape', 'finance-unit-economics-sensitivity-scenario'],
    'growth-analytics': ['growth-analytics-experiment-trust', 'growth-analytics-funnel-stage-attribution', 'growth-analytics-metric-selection', 'growth-analytics-reporting-reduction', 'growth-analytics-segmentation'],
    'implementation': ['implementation-complexity-coupling-management', 'implementation-design-pattern-selection', 'implementation-performance-data-structure-choice', 'implementation-blueprint'],
    'incident-response': ['incident-response-action-item-quality', 'incident-response-blameless-language-editing', 'incident-response-rca-method-selection', 'incident-response-severity-classification-scoping', 'incident-response-timeline-construction', 'incident-response-tool-landscape'],
    'interaction-design': ['interaction-design-form-control-and-layout'],
    'issue-retrospective': ['issue-retrospective-timeline-comprehensibility-and-subtraction-rules'],
    'knowledge-management': ['knowledge-management-curation-pruning', 'knowledge-management-structure-findability', 'knowledge-management-taxonomy-tagging', 'knowledge-management-supersession-lifecycle', 'knowledge-management-pattern-extraction'],
    'legal-compliance': ['legal-compliance-consent-ux', 'legal-compliance-cross-border-transfer', 'legal-compliance-lawful-basis-selection', 'legal-compliance-license-compatibility', 'legal-compliance-research-log', 'legal-compliance-retention-minimization', 'legal-compliance-vendor-dpa'],
    'localization': ['localization-locale-convention-formatting', 'localization-pluralization-and-grammar', 'localization-rtl-and-script-support', 'localization-string-externalization', 'localization-text-expansion-and-layout'],
    'market-analysis': ['market-analysis-competitor-mapping', 'market-analysis-evidence-rigor', 'market-analysis-five-forces', 'market-analysis-jtbd-fit', 'market-analysis-mece-proposal'],
    'marketing': ['marketing-channel-selection', 'marketing-message-persuasion', 'marketing-positioning-differentiation', 'marketing-scope-pruning', 'marketing-segment-targeting'],
    'ml-engineering': ['ml-engineering-evaluation-discipline', 'ml-engineering-ml-test-score-scoring', 'ml-engineering-model-provenance-versioning', 'ml-engineering-rollout-promotion-rollback', 'ml-engineering-serving-pattern-selection', 'ml-engineering-slo-definition-tradeoffs'],
    'observability': ['observability-cardinality-budget', 'observability-explorability', 'observability-methodology-selection', 'observability-phase-trace', 'observability-signal-golden', 'observability-signal-red', 'observability-signal-use'],
    'partnerships-bd': ['partnerships-bd-deal-structure-selection', 'partnerships-bd-exclusivity-and-scope-terms', 'partnerships-bd-governance-cadence-and-kpi', 'partnerships-bd-negotiation-positioning', 'partnerships-bd-term-sheet-comprehensibility-and-convention'],
    'performance-engineering': ['performance-engineering-operational-playbook'],
    'pr-communications': ['pr-communications-message-planning-and-evaluation-rules'],
    'pricing': ['pricing-design-rigor', 'pricing-method-family', 'pricing-scope-gate', 'pricing-tier-structure', 'pricing-verdict-report'],
    'product-discovery': ['product-discovery-guardrail-metric-status', 'product-discovery-hypothesis-preregistration', 'product-discovery-jtbd-problem-framing', 'product-discovery-opportunity-solution-tree-branching', 'product-discovery-rice-ice-prioritization', 'product-discovery-assumption-mapping', 'product-discovery-guardrail-metrics', 'product-discovery-hypothesis-testing', 'product-discovery-one-pager', 'product-discovery-opportunity-solution-tree'],
    'refactoring-legacy': ['refactoring-legacy-characterization-test-scope', 'refactoring-legacy-refactoring-step-decomposition', 'refactoring-legacy-seam-selection', 'refactoring-legacy-strangler-fig-migration', 'refactoring-legacy-verification-cadence'],
    'release-engineering': ['release-engineering-branching-release-strategy', 'release-engineering-changelog-entry-categorization', 'release-engineering-deployment-rollout-strategy', 'release-engineering-release-cadence-and-toil', 'release-engineering-rollback-and-recovery', 'release-engineering-semver-bump-selection', 'release-engineering-error-budget-policy', 'release-engineering-postmortem', 'release-engineering-readiness-checklist', 'release-engineering-rollout-plan'],
    'requirements-engineering': ['requirements-engineering-rules'],
    'risk-management': ['risk-management-aggregation-consolidation', 'risk-management-appetite-tolerance-threshold', 'risk-management-likelihood-impact-scale', 'risk-management-monitoring-review-cadence', 'risk-management-response-strategy-selection'],
    'sales': ['sales-objection-handling', 'sales-pitch-scoping-and-messaging-handoff', 'sales-qualification-and-discovery'],
    'secure-coding': ['secure-coding-authorization-access-control', 'secure-coding-cryptography-secrets-management', 'secure-coding-dependency-supply-chain-security', 'secure-coding-input-validation-injection-defense', 'secure-coding-session-authentication'],
    'security-threat-model': ['security-threat-model-threat-modeling-decision-rules'],
    'technical-feasibility': ['technical-feasibility-build-vs-buy-dependency-health', 'technical-feasibility-license-and-regulatory-risk', 'technical-feasibility-reversibility-and-spike-scoping', 'technical-feasibility-threat-model-disposition', 'technical-feasibility-verdict-and-timebox-selection', 'technical-feasibility-build-vs-buy', 'technical-feasibility-license-scan', 'technical-feasibility-reversibility-tag', 'technical-feasibility-spike-report', 'technical-feasibility-stride-table'],
    'technical-writing': ['technical-writing-doc-type-selection', 'technical-writing-minimalism-scoping', 'technical-writing-persuasion-trust', 'technical-writing-structure-comprehension', 'technical-writing-style-guide-compliance', 'technical-writing-tool-landscape'],
    'test-authoring': ['test-authoring-isolation-and-fixture-strategy'],
    'upstream-defect-report': ['upstream-defect-report-subtraction', 'upstream-defect-report-comprehensibility', 'upstream-defect-report-convention'],
    'user-discovery': ['user-discovery-evidence-strength-tagging', 'user-discovery-follow-up-ladder-depth', 'user-discovery-question-design-past-behavior', 'user-discovery-saturation-stopping-rule', 'user-discovery-switch-timeline-causal-forces', 'user-discovery-verdict-prevalence-reporting'],
    'ux-engineering': ['ux-engineering-color-visibility', 'ux-engineering-control-selection', 'ux-engineering-layout-grouping', 'ux-engineering-navigation-depth', 'ux-engineering-research-log', 'ux-engineering-surface-contrast'],
}


def resolve_role_source(role: str, repo_root: Path | None) -> dict:
    """`role` 을 skill-repository 가이던스로 무조건 해석한다(이슈 #1955:
    전이용 역할-소스 허용목록/rulebook 해석 경로 은퇴, #1758 이 얼린 phase 5
    제약 이행 — 매핑 없는 역할이라는 상태 자체가 더 이상 없다).

    이름을 `resolved_skill_dirs()` 로 푼다(모르는 이름은 이미 거기서
    워크스페이스/브랜치 전에 fail-closed). 풀린 디렉터리 중 하나라도
    `hooks/` 서브디렉터리를 들고 있으면 — skill-repository 는 가이던스
    전용이라는 얼어붙은 프로그램 원칙 위반 — 역시 워크스페이스/브랜치 전에
    fail-closed. {"source": "skill-repo", "skill_dirs": [...],
    "skills": [이름...], "skill_sha": <첫 디렉터리의 부모 저장소 sha>} 를
    돌려준다."""
    names = _ROLE_SKILLS.get(role, [])
    skill_dirs = resolved_skill_dirs(",".join(names), repo_root)
    hooked = [d for d in skill_dirs if (d / "hooks").is_dir()]
    if hooked:
        sys.exit(
            f"resolve_role_source: 역할 {role!r} 이 매핑한 스킬 중 "
            f"{', '.join(d.name for d in hooked)} 가 hooks/ 를 들고 있다 — "
            f"skill-repository 는 가이던스 전용이다(훅 없음, 이슈 #1758)")
    return {"source": "skill-repo", "skill_dirs": skill_dirs,
            "skills": [d.name for d in skill_dirs],
            "skill_sha": skill_repo_sha(skill_dirs[0].parent) if skill_dirs else None}


def _skill_source_roster_row(m: dict) -> dict:
    """이슈 #1774 요구사항 3: 마운트된 스킬 한 줄의 로스터/기록용 row —
    소스별로 정체성 필드 shape 가 다르다(proposal `## What will be done`
    item 6)."""
    if m["source"] == "skill-repo":
        return {"name": m["name"], "source": "skill-repo", "sha": m["sha"]}
    if m["source"] == "plugin":
        return {"name": m["name"], "source": "plugin",
                "plugin": m["plugin"], "version": m["version"]}
    return {"name": m["name"], "source": m["source"], "path": m["path"],
            "content_sha256": m["content_sha256"]}


def _skill_roster_fields(skill_sources: list[dict], skill_sha: str | None) -> dict:
    """`--skills` 로 마운트된 스킬들의 로스터/기록 필드. `skills_detail` 은
    쓰였을 때 항상 붙어 소스별 identity(요구사항 3)를 나른다. 오늘의 flat
    `skills`/`skills_sha` shape 는 전부 skill-repo 매치일 때만 additive 로
    같이 붙는다(empty-state 요구: skill-repo-only 조합은 오늘 shape 유지) —
    안 쓰면(빈 목록) 키 자체가 없다."""
    if not skill_sources:
        return {}
    fields = {"skills_detail": [_skill_source_roster_row(m) for m in skill_sources]}
    if all(m["source"] == "skill-repo" for m in skill_sources):
        fields["skills"] = [m["name"] for m in skill_sources]
        fields["skills_sha"] = skill_sha
    return fields


def _role_source_roster_fields(role_source: dict) -> dict:
    """이슈 #1758 요구사항 3 계승, 이슈 #1955 로 단순화: 로스터 엔트리마다
    항상 붙는 resolution 필드. source 는 이제 언제나 skill-repo(rulebook
    해석 경로는 은퇴했다) — resolution_source/resolution_skills/
    resolution_skill_sha 를 채운다."""
    return {"resolution_source": "skill-repo",
            "resolution_skills": role_source["skills"],
            "resolution_skill_sha": role_source["skill_sha"]}


# sibling: core_version
def core_root() -> Path:
    """tokenmaxxxer-core 체크아웃 루트. 없으면 멈춘다.

    core 는 상호작용 프로토콜의 게이트(보드·승인·gh-guard)와 정본 계약을
    들고 있다. 없이 띄우면 역할은 그대로 돌지만 아무도 이탈을 막지 않는다 —
    조용히 보호가 사라지는 쪽이라 경고가 아니라 정지다.
    """
    for _label, cand in _core_candidates():
        if not cand:
            continue
        p = Path(os.path.expanduser(os.path.expandvars(cand)))
        if "$" in str(p):
            continue
        if (p / "core" / ".claude-plugin" / "plugin.json").is_file():
            return p
    # 로컬 체크아웃이 없으면 룰북과 같은 길: on-the-record 소유 클론을 받아 쓴다.
    # 로컬 우선은 개발용 오버라이드일 뿐이다.
    d = ROOT / "runs" / "rulebooks" / "tokenmaxxxer-core"
    try:
        d.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    with _locked_rulebook_dir(d):
        if (d / "core" / ".claude-plugin" / "plugin.json").is_file():
            _migrate_legacy_ttl_marker(d)
            if not _pull_is_fresh(d):
                _run_net(["git", "-C", str(d), "pull", "-q", "--ff-only"], "[core] pull")
                _mark_pulled(d)
            return d
        try:
            print("[core] tokenmaxxxer-core 를 받는 중", file=sys.stderr)
            _run_net(["git", "clone", "-q",
                     "https://github.com/tokenmaxxxer/tokenmaxxxer-core.git",
                     str(d)], "[core] clone", timeout=CLONE_TIMEOUT)
            _mark_pulled(d)
        except OSError:
            pass
        if (d / "core" / ".claude-plugin" / "plugin.json").is_file():
            return d
    sys.exit(
        "tokenmaxxxer-core 를 찾지 못했고 받지도 못했다. 역할 세션은 core 없이\n"
        "  뜨지 않는다 — 프로토콜 게이트와 정본 계약이 거기 있다.\n"
        "  네트워크를 확인하거나 체크아웃을 두고 $TOKENMAXXXER_CORE 로 가리켜라.")


# sibling: core_root
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

    for label, cand in _core_candidates():
        if not cand:
            continue
        p = Path(os.path.expanduser(os.path.expandvars(cand)))
        if "$" in str(p):
            continue
        if (p / "core" / ".claude-plugin" / "plugin.json").is_file():
            return describe(p, label)
    d = ROOT / "runs" / "rulebooks" / "tokenmaxxxer-core"
    if (d / "core" / ".claude-plugin" / "plugin.json").is_file():
        _migrate_legacy_ttl_marker(d)
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
    root = core_root()
    plugins = json.loads(_mkt(root).read_text())["plugins"]
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


def drive(cwd: str, unattended: bool, limit: int = 12) -> int:
    """드라이버의 유일한 계약상 임무: 더 띄울 게 없으면 멈춘다.

    "누구를 다음에 띄울지"는 기계가 평가하는 라우팅 표가 아니라 오케스트레이터가
    보드(기록, loop_state)를 직접 읽고 내리는 판단이다(이슈 #120) — 그래서
    drive 는 스스로 역할을 고르지 않는다. 자동으로 고를 표가 없으므로 이
    호출은 항상 즉시 멈춘다; 남은 인자는 향후 호출부 호환을 위해 받되 쓰지
    않는다.

    이슈 #492 (ADR): `reconcile()` 이 낸 divergence 를 소비하는 것으로
    바뀐다 — 로스터를 읽어 엔트리마다 `reconcile()` 을 돌리고 결과와
    `next_action` 을 출력한다. #120 계약은 그대로다: drive() 는 여전히
    아무 역할도 스스로 고르지 않고, 무엇을 띄울지는 오케스트레이터의
    판단으로 남긴다 — 여기서 respawn/resume-watch 를 자동 실행하지 않는다.
    """
    root = Path(cwd).resolve()
    d = _roster_load()
    if not d:
        print("[drive] 돌고 있는 역할 세션 없음 — 보고할 divergence 없음. 멈춘다.",
              file=sys.stderr)
        return 0
    found = False
    for key, e in sorted(d.items()):
        divergences = reconcile(_build_expected(e), _build_observed(root, e),
                                 recovery_state_dir=root / ".on-the-record" / "recovery-state")
        for div in divergences:
            found = True
            print(f"[drive] {key}: {div['kind']}: {div['detail']} "
                  f"-> next_action={div['next_action']}", file=sys.stderr)
    if not found:
        print("[drive] divergence 없음 — 다음 역할을 자동으로 고르는 라우팅 "
              "표는 없다(이슈 #120). 오케스트레이터가 보드를 읽고 판단한다. "
              "띄울 게 없다고 보고 멈춘다.", file=sys.stderr)
    return 0


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
    v = version if version is not None else _claude_version()
    ok = ROOT / "runs" / "doctor-ok"
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
        if doctor() != 0 or not (ok.is_file() and ok.read_text().strip() == v):
            sys.exit(
                f"이 CLI({v})에서 플러그인 훅이 headless 로 발화하지 않는다 — "
                f"게이트 전부가 조용히 사라지는 버전이라 스폰을 막는다.")


def doctor() -> int:
    """프로브 플러그인 하나로 실 세션을 띄워 UserPromptSubmit / PreToolUse 가
    실제로 발화하는지 잰다. 성공하면 runs/doctor-ok 에 CLI 버전을 적는다."""
    v = _claude_version()
    if not v:
        print("claude --version 실패", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as td:
        plug = Path(td) / "probe"
        (plug / ".claude-plugin").mkdir(parents=True)
        (plug / "hooks").mkdir()
        (plug / ".claude-plugin" / "plugin.json").write_text(json.dumps(
            {"name": "muster-probe", "version": "0.0.0",
             "description": "hook-firing canary"}))
        ups, pre = Path(td) / "ups", Path(td) / "pre"
        (plug / "hooks" / "hooks.json").write_text(json.dumps({"hooks": {
            "UserPromptSubmit": [{"hooks": [
                {"type": "command", "command": f"touch {ups}"}]}],
            "PreToolUse": [{"matcher": "Bash", "hooks": [
                {"type": "command", "command": f"touch {pre}"}]}],
        }}))
        work = Path(td) / "work"
        work.mkdir()
        subprocess.run(["git", "init", "-q", str(work)], check=False)
        # --model haiku: 프로브의 관심사는 훅 로딩이지 모델이 아니다. 싸게 간다.
        subprocess.run(
            ["claude", "-p", "--plugin-dir", str(plug), "--model", "haiku",
             "--max-turns", "2", "--output-format", "json"],
            cwd=work, input="Run this exact bash command and nothing else: echo ok",
            text=True, capture_output=True, timeout=180)
        fired_ups, fired_pre = ups.is_file(), pre.is_file()
    print(f"UserPromptSubmit: {'발화' if fired_ups else '침묵'} / "
          f"PreToolUse: {'발화' if fired_pre else '침묵'}  (CLI {v})")
    if fired_ups and fired_pre:
        d = ROOT / "runs"
        d.mkdir(exist_ok=True)
        (d / "doctor-ok").write_text(v)
        print("doctor-ok 기록. 이 버전에서 스폰이 열린다.")
        return 0
    print("훅이 headless 에서 발화하지 않는다 — 이 CLI 버전으로는 룰북 집행이 "
          "성립하지 않는다. 스폰은 계속 막힌다.", file=sys.stderr)
    return 1


ROLE_MODEL_CONFIG = ROOT / "role_model.txt"


def read_role_model_config() -> str:
    """이슈#60: repo-root role_model.txt 에서 기본 모델 값을 읽는다. 파일이
    없거나 읽기 오류가 나면 미설정과 동일하게 "" 를 돌려준다."""
    try:
        return ROLE_MODEL_CONFIG.read_text().strip()
    except (OSError, UnicodeDecodeError):
        return ""


def resolved_role_model(cli_model: str | None = None) -> str:
    """이슈#93: env > config > built-in default("sonnet"). MUSTER_ROLE_MODEL 이
    (strip 후) 비어 있지 않으면 그것이 이긴다 — config 는 그때는 아예 안 읽힌
    값처럼 무시된다. 둘 다 비어 있으면 "sonnet" — --model 이 항상 붙는다,
    호출자의(비쌀 수 있는) 세션 모델을 조용히 물려받지 않도록.

    이슈#1736: `cli_model` 이(strip 후) 비어 있지 않으면 최우선으로 이긴다
    — 단일 스폰에 대한 per-invocation 오버라이드, env/config 는 아예 안
    읽힌 것처럼 건너뛴다. 생략하면(기본값 None) 이전 동작과 byte-identical."""
    cli_value = (cli_model or "").strip()
    if cli_value:
        return cli_value
    env_value = (os.environ.get("MUSTER_ROLE_MODEL") or "").strip()
    if env_value:
        return env_value
    return read_role_model_config() or "sonnet"


def spawn_cmd(settings_path: str, role: str, unattended: bool,
              core_plugins: list | None = None,
              plugins: list | None = None,
              model: str | None = None,
              skill_dirs: list | None = None,
              skill_repo_sha_value: str | None = None) -> tuple[list[str], dict[str, str]]:
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
    role_model = resolved_role_model(model)
    if role_model:
        cmd += ["--model", role_model]
    env = {"CLAUDE_ROLE": role, "TOKENMAXXXER_SPAWNED": "1"}
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
    agent_token = _resolve_gh_token()
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


def _parse_consult_verdict(text: str) -> dict | None:
    """모델 출력에서 자문 판단 JSON 을 찾는다. 마지막 줄이 아니거나 코드펜스에
    감싸여 있어도, 텍스트 안에서 가장 나중에 나온(뒤에서부터 훑어 처음 파싱
    되는) `{...}` 객체를 쓴다 — 모델이 답 앞에 설명을 붙여도 견딘다."""
    if not text:
        return None
    for i in reversed([j for j, c in enumerate(text) if c == "{"]):
        try:
            obj, _ = json.JSONDecoder().raw_decode(text, i)
        except ValueError:
            continue
        if isinstance(obj, dict) and "answer" in obj:
            return obj
    return None


def _consult_root(cwd: str | None) -> Path:
    """자문(consult) 계열 기록 경로 전부가 공유하는 앵커. `-C`/cwd 로 대상
    레포가 주어지면 그 레포를, 없으면 플러그인 저장소(`ROOT`)를 앵커로
    쓴다 — 트레이스/사이드파일/패널 기록 경로와 커밋 루트
    (`_commit_consult_trace()`)가 서로 다른 앵커를 쓰면 `relative_to()` 가
    터진다(이슈 #1313 근본원인)."""
    return Path(cwd).resolve() if cwd else ROOT


def _persist_consult_raw_output(issue: int | None, ts: str, attempt: int, text: str,
                                cwd: str | None = None) -> Path:
    """파싱 실패 시 모델의 원본 출력 전체를 사이드 파일에 저장한다 —
    트레이스 줄에는 경로 + 짧은 발췌만 남기고(#1123 제안서 Constraints:
    "트레이스 파일 크기를 실패마다 부풀리면 안 된다"), 전체 텍스트는 여기
    보존해 재현이 아니라 실제 원인 분석이 가능하게 한다."""
    base = _consult_root(cwd) / "docs" / (f"issue-{issue}" if issue is not None else "reports")
    if issue is not None:
        out_dir = base / "reports" / "consult-raw-failures"
    else:
        out_dir = base / "consult-raw-failures"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_ts = ts.replace(":", "").replace("+", "")
    path = out_dir / f"{safe_ts}-{attempt}.txt"
    path.write_text(text, encoding="utf-8")
    return path


def _consult_trace_path(issue: int | None, cwd: str | None = None) -> Path:
    """이슈가 있으면 그 이슈 트리 아래, 없으면 표준 6개 버킷 중
    `reports/` 아래 — `docs/` 는 표준 버킷과 `docs/issue-<n>/` 트리만
    허용한다(contract v3 s10, board-gate.sh 가 강제). 앵커는
    `_consult_root()` 로 대상 레포(`-C`/cwd)에 맞춘다."""
    root = _consult_root(cwd)
    if issue is not None:
        return root / "docs" / f"issue-{issue}" / "reports" / "consult-log.md"
    return root / "docs" / "reports" / "consult-log.md"


def _append_consult_trace(path: Path, ts: str, role: str, issue: int | None,
                          question: str, outcome: str, verb: str = "consult") -> None:
    """자문 한 건마다 한 줄 — 성공/실패 가리지 않고 남긴다("no traceless
    consults", 운영자 결정, 이슈 #699). 함수 자체가 실패해도(디렉터리를
    못 만든다 등) 예외를 그대로 올려, 호출부의 finally 가 "트레이스 남김"을
    조용히 거짓으로 만들지 않게 한다.

    이슈 #1202 requirement 5: consult 의 형제 verb(ideate/draft/review) 도
    같은 트레이스 파일 하나를 공유한다 — 별도 파일로 갈라지면 drift 가
    난다(`consult_cmd()` 독스트링과 같은 이유). `verb=` 는 기본값
    "consult" 라 기존 호출부는 그대로 동작한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = (f"- {ts} | role={role} | verb={verb} "
            f"| issue={issue if issue is not None else 'none'} "
            f"| question={question[:200]!r} | outcome={outcome[:300]!r}\n")
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


def _commit_consult_trace(paths: list[Path], issue: int | None, role: str,
                          outcome: str, cwd: str | None) -> None:
    """자문 트레이스(및 이번 호출에서 쓴 원본 사이드 파일)를 커밋해
    체크아웃을 깨끗하게 유지한다(이슈 #1134, northpole req#2 — 로컬
    미커밋 상태만 있는 기록은 기록이 아니다). `approve-scope`
    선례(spawn.py:1367-1387)와 같은 add-then-commit 모양이지만, 되돌릴
    "이전 전문"이 없다(append 이지 overwrite 가 아니다) — 커밋 실패시
    파일 쓰기는 그대로 두고 경고만 남긴다."""
    root = _consult_root(cwd)
    rels = [str(p.relative_to(root)) for p in paths]
    outcome_word = "error" if outcome.startswith("error") else "ok"
    message = (f"issue-{issue}: consult-trace ({outcome_word})" if issue is not None
               else f"consult-trace ({outcome_word})")
    try:
        subprocess.run(["git", "-C", str(root), "add", *rels],
                       check=True, capture_output=True, text=True)
        subprocess.run(["git", "-C", str(root), "commit", "-m", message],
                       check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"consult-trace 커밋 실패 — {', '.join(rels)} 가 커밋 안 된 채 남았다: "
              f"{e.stderr.strip() if e.stderr else e}", file=sys.stderr)


def _skill_judge_consult(task_text: str, role: str,
                         candidates: list[tuple[str, Path, str]],
                         issue: int | None, cwd: str | None,
                         model: str | None = None
                         ) -> tuple[list[Path], dict]:
    """이슈 #2040: BM25 상위 후보를 자문(consult)에 넘겨, 트리거 문장의
    조건이 실제로 이번 과제에 맞는지(단어 겹침이 아니라)를 판단시킨다.
    반환은 (picked_paths, {"picked":[...], "rejected":[...], "reasons":{}})
    — 실패시(파싱 실패/타임아웃/비영시종료) RuntimeError 를 그대로 올려,
    호출자(`_cross_family_skill_matches_with_consult()`)가 BM25 top-2 로
    fail-open 하게 한다(제안서 Constraints).

    `_verb_cmd()` 를 재사용하지 않는 이유: 그 함수의 기본 트레이스 줄은
    `outcome = f"ok: {parsed[required_key]}"` 로 picked 값만 남기고
    rejected+reason 을 놓친다 — Acceptance 가 요구하는 "picked+rejected+
    reasons 를 자문 트레이스에" 를 만족하려면 이 함수가 트레이스 줄을
    직접 조립해야 한다. session-assembly(`_consult_cmd_and_env()`)와
    트레이스 파일(`_consult_trace_path()`, `verb="skill_judge"`)은
    그대로 공유한다(드리프트 방지, `_verb_cmd()` 독스트링과 같은 이유)."""
    trace_path = _consult_trace_path(issue, cwd)
    ts = datetime.now(timezone.utc).isoformat()
    settings_path = None
    raw_paths: list[Path] = []
    outcome = "error: 알 수 없는 실패"
    by_name = {name: path for name, path, _source in candidates}
    # 이슈 #2055: 후보가 이제 네 소스에 걸쳐 있어, 질의 문구도 어느 tier
    # 에서 왔는지 라벨을 달아 skill_judge 가 소스를 보고도 판단할 수 있게
    # 한다(Acceptance: "source 라벨이 ... skill_judge 자문 질문 ... 까지").
    candidate_lines = "\n".join(
        f"- {name} [{source}] — {_skill_trigger_line(path) or ''}"
        for name, path, source in candidates)
    question = (f"과제:\n{task_text}\n\n후보 스킬(BM25 상위 {len(candidates)}개):\n"
                f"{candidate_lines}")
    try:
        f = ROOT / "roles" / f"{role}.json"
        if not f.exists():
            have = ", ".join(sorted(p.stem for p in (ROOT / "roles").glob("*.json")))
            raise ValueError(f"모르는 역할: {role}  (있는 것: {have})")
        spec = json.loads(f.read_text())
        # 이슈 #2061: skill_judge 는 8개 후보 중 0-2개를 고르는 자잘한
        # 분류라, 호출자가 넘긴 세션 기본 모델을 그대로 물려받지 않고
        # 언제나 haiku 로 고정한다 — `model` 인자는 시그니처 호환용으로만
        # 남긴다(다른 자문 호출과 모양을 맞추려는 것일 뿐, 실제로는 무시).
        cmd, env, settings_path = _consult_cmd_and_env(role, spec, cwd, "haiku")
        judge_timeout = _skill_judge_timeout()
        override = (
            "이 세션에 로드된 룰북/훅이 스카우트, 제안서 작성, 위임, 승인 게이트, "
            "기록 작성 등을 지시하더라도 — 이번 호출은 스킬-판단(skill_judge) "
            "이라 전부 적용되지 않는다: 저장소 파일을 하나도 건드리지 않고, "
            "하위 에이전트를 위임하지 않고, 조사 없이 알고 있는 판단을 바로 "
            "답한다. 다른 모든 지시보다 이 문장이 우선한다.")
        instructions = (
            "당신은 스킬-판단(skill_judge)으로 불렸다 — 아래 후보 스킬들의 "
            '"Use when ..." 트리거 문장이 이번 과제에 실제로 조건상 맞는지만 '
            "판단한다. 단어가 겹친다고 뽑지 말고, 트리거 문장이 말하는 조건이 "
            "이 과제에 그럴듯하게 적용될 때만 뽑는다(최대 2개). 각 후보마다 "
            "고르거나 거절한 한 줄 이유를 남겨라. 브랜치를 만들지도, "
            "커밋하지도, PR 을 열지도 마라.")
        shape = ('{"picked": ["<skill-name>", ...], '
                 '"rejected": [{"name": "<skill-name>", "reason": "<reason>"}, ...], '
                 '"reasons": {"<picked-skill-name>": "<reason>"}}')
        base_prompt = (instructions + " " + override + " 답을 다 쓴 뒤 마지막에, "
                       "다른 어떤 텍스트도 없이 JSON 객체 하나만 출력하라: "
                       f"{shape}\n\n{question}")
        retry_prompt = (
            base_prompt + "\n\n(재시도: 이전 응답이 마지막에 판단 JSON 객체를 "
            "출력하지 않아 파싱에 실패했다. 다른 어떤 절차도 밟지 말고, 지금 "
            "바로 위 형식의 JSON 객체 하나만 출력하라.)")
        attempts_exhausted = "알 수 없는 실패"
        parsed = None
        for attempt_num, attempt_prompt in enumerate((base_prompt, retry_prompt), start=1):
            r = subprocess.run(cmd, cwd=cwd or str(ROOT), input=attempt_prompt, text=True,
                               capture_output=True, timeout=judge_timeout, env=env)
            if r.returncode != 0:
                attempts_exhausted = f"세션 종료 코드 {r.returncode}: {r.stderr.strip()[:300]}"
                continue
            result = session_result(r.stdout)
            raw_text = result.get("result", "")
            parsed = _parse_verb_json(raw_text, "picked")
            if parsed is None:
                raw_path = _persist_consult_raw_output(issue, ts, attempt_num, raw_text, cwd)
                raw_paths.append(raw_path)
                excerpt = raw_text[-300:].replace("\n", " ")
                attempts_exhausted = (
                    f"모델 출력에서 skill_judge JSON 을 못 찾음 (원본: `{raw_path}`, "
                    f"끝부분: {excerpt!r})")
                parsed = None
                continue
            break
        if parsed is None:
            outcome = f"error: {attempts_exhausted} (재시도 1회 포함, 모두 실패)"
            raise RuntimeError(outcome)
        picked_names = [n for n in parsed.get("picked", []) if n in by_name][:2]
        rejected = parsed.get("rejected", [])
        reasons = parsed.get("reasons", {})
        rejected_summary = "; ".join(
            f"{r.get('name')}={str(r.get('reason', ''))[:80]}" for r in rejected
            if isinstance(r, dict) and r.get("name"))
        picked_summary = "; ".join(
            f"{n}={str(reasons.get(n, ''))[:80]}" for n in picked_names)
        outcome = f"ok: picked=[{picked_summary}] rejected=[{rejected_summary}]"
        detail = {"picked": picked_names, "rejected": rejected, "reasons": reasons}
        return [by_name[n] for n in picked_names], detail
    except subprocess.TimeoutExpired:
        outcome = f"error: 시간초과({judge_timeout}s)"
        raise
    finally:
        if settings_path:
            with contextlib.suppress(OSError):
                os.unlink(settings_path)
        _append_consult_trace(trace_path, ts, role, issue, question, outcome,
                              verb="skill_judge")
        commit_paths = [trace_path] + raw_paths
        _commit_consult_trace(commit_paths, issue, role, outcome, cwd)


def _cross_family_skill_matches_with_consult(task_text: str, role: str,
                                             repo_root: Path | None,
                                             issue: int | None, cwd: str | None,
                                             k: int = 2,
                                             model: str | None = None,
                                             home: Path | None = None,
                                             target_repo_root: Path | None = None
                                             ) -> list[Path]:
    """이슈 #2040: BM25 상위 `_CROSS_FAMILY_CONSULT_TOPN` 개를 자문
    (skill_judge)에 넘겨 조건-매치 여부로 좁힌다. BM25 후보가 아예 없으면
    (score>0 인 것이 없으면) 자문을 부르지 않고 빈 목록을 바로 돌려준다
    — 자문 한 번(<= 스폰당 자문 1회, Acceptance)조차 아까운 no-candidate
    경로를 오늘처럼 조용히 통과시킨다. 자문이 에러(타임아웃/파싱 실패/
    세션 실패 전부 포함)를 내면 BM25 자체의 top-`k` 로 fail-open 한다
    (`_cross_family_skill_matches()`, 제안서 Constraints — "오늘의
    raw-overlap top-2" 가 아니라 BM25 가 새 기준 프리필터이므로)."""
    scored = _bm25_cross_family_scores(task_text, role, repo_root, home, target_repo_root)
    if not scored:
        return []
    candidates = [(name, d, source)
                  for _, name, d, source in scored[:_CROSS_FAMILY_CONSULT_TOPN]]
    try:
        picked, _detail = _skill_judge_consult(task_text, role, candidates, issue, cwd,
                                               model=model)
        return picked
    except Exception as ex:
        print(f"[{role}] skill_judge 자문 실패 — BM25 top-{k} 로 fail-open: {ex}",
              file=sys.stderr)
        return [d for _, _, d, _ in scored[:k]]


def _consult_cmd_and_env(role: str, spec: dict, cwd: str | None,
                         model: str | None = None) -> tuple[list[str], dict[str, str], str]:
    """`consult_cmd()`의 argv/env/settings-file 조립만 떼어낸, subprocess 를
    직접 부르지 않는 build-then-return 헬퍼 — `spawn_cmd()` 와 같은 모양이다.
    `(cmd, env, settings_path)` 를 돌려준다 — settings_path 는 호출자가
    끝에 `os.unlink` 로 치워야 하는 임시 파일이라 별도로 넘긴다.

    이슈 #1141: `CLAUDE_PLUGIN_ROOT_CORE` 를 `core_plugin_dirs()` 에서
    주입한다 — `spawn_cmd()` 가 이슈 #182 때부터 갖고 있던 것과 똑같은
    한 줄(spawn.py 의 `spawn_cmd()` 참조). 이 변수가 없으면 core 훅이
    `hooks/lib/gate-lib.sh` 를 상대경로 fallback 으로 찾다가 자문 세션의
    작업 디렉터리 밑에서는 실패해 하드블록한다 — 그 블록 에러 텍스트가
    "모델 출력"으로 캡처되어 판단 JSON 파싱이 매번 실패하는 게 이 이슈의
    근본원인이었다.

    분리 이유: 이대로 `consult_cmd()` 안에 인라인해두면 테스트가 이
    주입 로직을 재구현해야만 검증할 수 있다 — 실제 코드경로를 안 타는
    테스트는 이 이슈가 닫으려는 드리프트류를 그대로 재현한다(경고 문서:
    docs/issue-1141/reports/implementation/2026-08-13-hunt-consult-core-plugin-root-injection.md).

    이슈 #1955: 역할 가이던스는 이제 항상 skill-repository 에서 온다 —
    `resolve_role_source()` 가 매핑하는 스킬 디렉터리를 그대로 붙인다."""
    plugins = resolve_role_source(role, _skill_repo_root())["skill_dirs"]
    s = role_settings(role, cwd, inject_self_hosted_hooks=False)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(s, tf)
        settings_path = tf.name
    cmd = ["claude", "-p", "--settings", settings_path,
           "--permission-mode", "bypassPermissions",
           "--output-format", "json"]
    for p in plugins:
        cmd += ["--plugin-dir", str(p)]
    for p in core_plugin_dirs():
        cmd += ["--plugin-dir", str(p)]
    role_model = resolved_role_model(model)
    if role_model:
        cmd += ["--model", role_model]
    env = {**os.environ, "CLAUDE_ROLE": role, "TOKENMAXXXER_SPAWNED": "1"}
    core_dir = next((p for p in core_plugin_dirs() if Path(p).name == "core"), None)
    if core_dir:
        env["CLAUDE_PLUGIN_ROOT_CORE"] = str(core_dir)
    return cmd, env, settings_path


def consult_cmd(role: str, question: str, issue: int | None = None,
                cwd: str | None = None, model: str | None = None) -> dict:
    """자문(consult): 역할의 룰북을 로드해 판단만 돌려받는다 — 브랜치도
    커밋도 PR 도 만들지 않는다(이슈 #699 R1). `spawn_cmd()`/`_spawn_one()`
    의 발급 파이프라인과는 별개의, 훨씬 작은 조립이다: 그 함수들이 여는
    브랜치/워크스페이스/워처/roster 등록은 전부 배달물(deliverable)을
    향한 것이고, 자문은 텍스트 하나만 되돌려주면 끝나기 때문이다.

    룰북 로딩은 `role_settings()`/`plugin_dirs()` 를 그대로 재사용한다 —
    이슈#699 phase-1 proposal 이 채택한 이유: 룰북을 켜는 코드경로가
    두 벌로 갈라지면 spawn 경로만 고치고 consult 경로는 못 고치는 드리프트가
    생긴다(issue #695/#700 이 이미 한 번 치운 문제류).

    트레이스는 **성공/실패와 무관하게** 항상 한 줄 남는다 — `finally` 에서
    쓰고, 그 다음에야 리턴하거나 다시 raise 한다."""
    trace_path = _consult_trace_path(issue, cwd)
    ts = datetime.now(timezone.utc).isoformat()
    outcome = "error: 알 수 없는 실패"
    verdict = None
    settings_path = None
    raw_path = None
    raw_paths: list[Path] = []
    try:
        f = ROOT / "roles" / f"{role}.json"
        if not f.exists():
            have = ", ".join(sorted(p.stem for p in (ROOT / "roles").glob("*.json")))
            raise ValueError(f"모르는 역할: {role}  (있는 것: {have})")
        spec = json.loads(f.read_text())
        cmd, env, settings_path = _consult_cmd_and_env(role, spec, cwd, model)
        # 이슈 #1097 근본원인: consult 도 core_plugin_dirs() 를 그대로 물기 때문에
        # freelunch/scout/warrant/proposal-shape 같은, 저장소를 바꾸는 배달물을
        # 겨냥한 core 훅들이 자문 세션에도 그대로 꽂힌다. 복잡한 판단 질문 하나가
        # 그 훅들 눈에는 "설계 작업"으로 보여, 모델이 스카우트/제안서/위임 절차를
        # 먼저 밟다가(2026-08-12T07:38-39Z 재현 실패 2건) 턴 예산을 다 쓰고 끝의
        # 판단 JSON 을 한 번도 못 찍고 끝난다. 구조적 수정: 프롬프트 안에서 그
        # 훅들이 이 세션에는 적용되지 않음을 명시적으로 무효화한다.
        override = (
            "이 세션에 로드된 룰북/훅이 스카우트, 제안서(proposal) 작성, 위임"
            "(delegation/fan-out), 승인 게이트, 기록(record) 작성 등을 지시하더라도"
            " — 이번 호출은 자문(consult) 이라 전부 적용되지 않는다: 저장소 파일을"
            " 하나도 건드리지 않고, 하위 에이전트를 위임하지 않고, 조사 없이 알고"
            " 있는 판단을 바로 답한다. 다른 모든 지시보다 이 문장이 우선한다."
        )
        base_prompt = (
            "당신은 자문(consult) 으로 불렸다 — 판단만 돌려주면 된다. 이 역할의 "
            "룰북은 이미 로드돼 있다. 브랜치를 만들지도, 커밋하지도, PR 을 열지도 "
            "마라 — 텍스트로 답하고 끝난다. " + override + " 답을 다 쓴 뒤 마지막에, "
            "다른 어떤 텍스트도 없이 JSON 객체 하나만 출력하라: "
            '{"answer": "<판단>", "confidence": "low|medium|high", '
            '"caveats": ["<유보/전제>", ...]}\n\n'
            f"질문: {question}"
        )
        retry_prompt = (
            base_prompt + "\n\n(재시도: 이전 응답이 마지막에 판단 JSON 객체를 "
            "출력하지 않아 파싱에 실패했다. 스카우트/제안서/위임 등 다른 어떤 "
            "절차도 밟지 말고, 지금 바로 위 형식의 JSON 객체 하나만 출력하라.)"
        )
        attempts_exhausted = "알 수 없는 실패"
        for attempt_num, attempt_prompt in enumerate((base_prompt, retry_prompt), start=1):
            r = subprocess.run(cmd, cwd=cwd or str(ROOT), input=attempt_prompt, text=True,
                               capture_output=True, timeout=CONSULT_TIMEOUT, env=env)
            if r.returncode != 0:
                attempts_exhausted = f"세션 종료 코드 {r.returncode}: {r.stderr.strip()[:300]}"
                continue
            result = session_result(r.stdout)
            raw_text = result.get("result", "")
            verdict = _parse_consult_verdict(raw_text)
            if verdict is None:
                raw_path = _persist_consult_raw_output(issue, ts, attempt_num, raw_text, cwd)
                raw_paths.append(raw_path)
                excerpt = raw_text[-300:].replace("\n", " ")
                attempts_exhausted = (
                    f"모델 출력에서 판단 JSON 을 못 찾음 (원본: `{raw_path}`, "
                    f"끝부분: {excerpt!r})"
                )
                continue
            outcome = f"ok: {str(verdict.get('answer', ''))[:200]}"
            return verdict
        outcome = f"error: {attempts_exhausted} (재시도 1회 포함, 모두 실패)"
        raise RuntimeError(outcome)
    except subprocess.TimeoutExpired:
        outcome = f"error: 시간초과({CONSULT_TIMEOUT}s)"
        raise
    finally:
        if settings_path:
            with contextlib.suppress(OSError):
                os.unlink(settings_path)
        _append_consult_trace(trace_path, ts, role, issue, question, outcome)
        commit_paths = [trace_path] + raw_paths
        _commit_consult_trace(commit_paths, issue, role, outcome, cwd)


_VERB_REQUIRED_KEY = {"ideate": "options", "draft": "draft", "review": "findings"}
_VERB_INSTRUCTIONS = {
    "ideate": (
        "당신은 아이디어 발산(ideate)으로 불렸다 — 하나의 판단이 아니라 서로 다른 "
        "선택지 여럿을 내놓아야 한다. 브랜치를 만들지도, 커밋하지도, PR 을 열지도 "
        "마라 — 텍스트로 답하고 끝난다."
    ),
    "draft": (
        "당신은 초안 작성(draft)으로 불렸다 — 산출물의 스케치를 텍스트로 돌려주면 "
        "된다. 저장소에 파일을 쓰지 마라 — 호출자가 이 초안을 쓸지 말지 결정한다. "
        "브랜치를 만들지도, 커밋하지도, PR 을 열지도 마라."
    ),
    "review": (
        "당신은 검토(review)로 불렸다 — 아래 제시된 텍스트/diff 에 대한 구조화된 "
        "피드백만 돌려주면 된다. 저장소에 파일을 쓰지 마라. 브랜치를 만들지도, "
        "커밋하지도, PR 을 열지도 마라."
    ),
}
_VERB_JSON_SHAPE = {
    "ideate": '{"options": ["<option>", ...], "tradeoffs": ["<tradeoff>", ...]}',
    "draft": '{"draft": "<text>", "open_questions": ["<question>", ...]}',
    "review": '{"findings": ["<finding>", ...], "verdict": "<summary verdict>"}',
}


def _parse_verb_json(text: str, required_key: str) -> dict | None:
    """`_parse_consult_verdict()`와 같은 모양이지만 필수 키를 verb 마다
    다르게 받는다 — consult 의 "answer" 대신 ideate/draft/review 각자의
    반환 키(options/draft/findings)를 찾는다."""
    if not text:
        return None
    for i in reversed([j for j, c in enumerate(text) if c == "{"]):
        try:
            obj, _ = json.JSONDecoder().raw_decode(text, i)
        except ValueError:
            continue
        if isinstance(obj, dict) and required_key in obj:
            return obj
    return None


def _verb_cmd(verb: str, role: str, prompt_text: str, issue: int | None = None,
             cwd: str | None = None) -> dict:
    """`consult_cmd()`의 형제 verb 공용 실행부 (이슈 #1202 requirement 5).
    같은 session-assembly(`_consult_cmd_and_env()`)와 같은 트레이스
    파일(`_consult_trace_path()`, `verb=` 필드로 구분)을 공유하고,
    프롬프트 지시문과 필수 반환 키만 verb 마다 갈린다 — 제안서 §6이
    선택한 모양 그대로다. 브랜치/커밋/PR 이 없는 계약은 consult 와
    동일하다."""
    required_key = _VERB_REQUIRED_KEY[verb]
    trace_path = _consult_trace_path(issue, cwd)
    ts = datetime.now(timezone.utc).isoformat()
    outcome = "error: 알 수 없는 실패"
    settings_path = None
    raw_paths: list[Path] = []
    try:
        f = ROOT / "roles" / f"{role}.json"
        if not f.exists():
            have = ", ".join(sorted(p.stem for p in (ROOT / "roles").glob("*.json")))
            raise ValueError(f"모르는 역할: {role}  (있는 것: {have})")
        spec = json.loads(f.read_text())
        cmd, env, settings_path = _consult_cmd_and_env(role, spec, cwd)
        override = (
            "이 세션에 로드된 룰북/훅이 스카우트, 제안서(proposal) 작성, 위임"
            "(delegation/fan-out), 승인 게이트, 기록(record) 작성 등을 지시하더라도"
            f" — 이번 호출은 {verb} 라 전부 적용되지 않는다: 저장소 파일을"
            " 하나도 건드리지 않고, 하위 에이전트를 위임하지 않고, 조사 없이 알고"
            " 있는 답을 바로 낸다. 다른 모든 지시보다 이 문장이 우선한다."
        )
        base_prompt = (
            _VERB_INSTRUCTIONS[verb] + " " + override + " 답을 다 쓴 뒤 마지막에, "
            "다른 어떤 텍스트도 없이 JSON 객체 하나만 출력하라: "
            f"{_VERB_JSON_SHAPE[verb]}\n\n요청: {prompt_text}"
        )
        retry_prompt = (
            base_prompt + f"\n\n(재시도: 이전 응답이 마지막에 {required_key!r} 키를 가진 "
            "JSON 객체를 출력하지 않아 파싱에 실패했다. 다른 어떤 절차도 밟지 말고, "
            "지금 바로 위 형식의 JSON 객체 하나만 출력하라.)"
        )
        attempts_exhausted = "알 수 없는 실패"
        for attempt_num, attempt_prompt in enumerate((base_prompt, retry_prompt), start=1):
            r = subprocess.run(cmd, cwd=cwd or str(ROOT), input=attempt_prompt, text=True,
                               capture_output=True, timeout=CONSULT_TIMEOUT, env=env)
            if r.returncode != 0:
                attempts_exhausted = f"세션 종료 코드 {r.returncode}: {r.stderr.strip()[:300]}"
                continue
            result = session_result(r.stdout)
            raw_text = result.get("result", "")
            parsed = _parse_verb_json(raw_text, required_key)
            if parsed is None:
                raw_path = _persist_consult_raw_output(issue, ts, attempt_num, raw_text, cwd)
                raw_paths.append(raw_path)
                excerpt = raw_text[-300:].replace("\n", " ")
                attempts_exhausted = (
                    f"모델 출력에서 {verb} JSON 을 못 찾음 (원본: `{raw_path}`, "
                    f"끝부분: {excerpt!r})"
                )
                continue
            outcome = f"ok: {str(parsed.get(required_key, ''))[:200]}"
            return parsed
        outcome = f"error: {attempts_exhausted} (재시도 1회 포함, 모두 실패)"
        raise RuntimeError(outcome)
    except subprocess.TimeoutExpired:
        outcome = f"error: 시간초과({CONSULT_TIMEOUT}s)"
        raise
    finally:
        if settings_path:
            with contextlib.suppress(OSError):
                os.unlink(settings_path)
        _append_consult_trace(trace_path, ts, role, issue, prompt_text, outcome, verb=verb)
        commit_paths = [trace_path] + raw_paths
        _commit_consult_trace(commit_paths, issue, role, outcome, cwd)


def ideate_cmd(role: str, prompt_text: str, issue: int | None = None,
              cwd: str | None = None) -> dict:
    """divergent options — `{"options": [...], "tradeoffs": [...]}`."""
    return _verb_cmd("ideate", role, prompt_text, issue=issue, cwd=cwd)


def draft_cmd(role: str, prompt_text: str, issue: int | None = None,
             cwd: str | None = None) -> dict:
    """deliverable sketch — `{"draft": "...", "open_questions": [...]}`.
    No `write_scope` applies: the caller decides whether to use the
    text, the verb itself never writes to the repo."""
    return _verb_cmd("draft", role, prompt_text, issue=issue, cwd=cwd)


def review_cmd(role: str, prompt_text: str, issue: int | None = None,
              cwd: str | None = None) -> dict:
    """structured feedback — `{"findings": [...], "verdict": "..."}`."""
    return _verb_cmd("review", role, prompt_text, issue=issue, cwd=cwd)


# ---------------------------------------------------------------------------
# issue #1587 — `judge`: read-only, budgeted role judgment over a merge diff.
#
# 격리는 프롬프트 문장이 아니라 세션 조립(`--plugin-dir`/`permissions`)에서
# 난다 — consult/`_verb_cmd()`가 겪은 #1097 근본원인(공격 가능한 diff 내용이
# 모델을 설득할 수 있는 문자열 무효화)을 judge 는 구조적으로 피한다. 그래서
# `_consult_cmd_and_env()`를 재사용하지 않고 judge 전용 조립을 따로 둔다
# (제안서 Rationale 참고).
# ---------------------------------------------------------------------------

# core 플러그인 중 "배달(delivery)" 지향인 것 — 제안 작성/승인 게이트/팬아웃
# 위임을 모델에게 지시한다. judge 세션은 diff 를 읽고 판단만 돌려주면
# 끝이라 이런 훅이 꽂히면 안 된다(이슈가 명시한 구조적 격리 지점). core 의
# 나머지(core 자체, terse)는 무해하므로 남긴다.
_JUDGE_EXCLUDED_CORE_PLUGINS = {"freelunch", "scout", "warrant"}


def _readonly_plugin_dirs(role: str, spec: dict) -> list[Path]:
    """judge 세션에 붙일 플러그인 — 역할 가이던스(이슈 #1955: skill-repository,
    `resolve_role_source()`)는 그대로 싣는다(무엇을 위반했는지 판단하려면
    가이던스 전체가 필요하다), core 는 `_JUDGE_EXCLUDED_CORE_PLUGINS` 로
    배달 지향 훅만 걸러낸다."""
    out = list(resolve_role_source(role, _skill_repo_root())["skill_dirs"])
    for p in core_plugin_dirs():
        if p.name not in _JUDGE_EXCLUDED_CORE_PLUGINS:
            out.append(p)
    return out


def _readonly_bash_allow(cwd: str) -> list[str]:
    """`git show`/`git diff`/`git log` 만 — `_workspace_bash_allow()`와 같은
    모양으로 `cwd` 에 앵커링한다. gh, Write, Edit 을 향한 경로는 여기 없다
    (grep-checkable 제약, 제안서 Constraints)."""
    return [
        f"Bash(cd {cwd} && git show *)",
        f"Bash(cd {cwd} && git diff *)",
        f"Bash(cd {cwd} && git log *)",
        f"Bash(git -C {cwd} show *)",
        f"Bash(git -C {cwd} diff *)",
        f"Bash(git -C {cwd} log *)",
    ]


def _readonly_settings(role: str, cwd: str) -> dict:
    """읽기 전용 세션 설정 — `role_settings()`의 샌드박스/전역-플러그인
    차단은 그대로 쓰되, `permissions.allow`를 Read/Grep/Glob + git 플루밍
    Bash 로만 한정하고 Write/Edit/`gh `를 `permissions.deny`로 명시적으로
    막는다. `--permission-mode bypassPermissions`를 주지 않는 것과 짝을
    이룬다 — headless 세션은 허용 목록에 없는 도구를 답할 사람 없이
    그냥 거부한다(role_settings() #742 문단이 서술하는 바로 그 실측 동작을,
    judge 는 위험이 아니라 안전장치로 쓴다)."""
    s = role_settings(role, cwd, inject_self_hosted_hooks=False)
    s["permissions"] = {
        "allow": ["Read", "Grep", "Glob", *_readonly_bash_allow(cwd)],
        "deny": ["Write", "Edit", "Bash(gh *)"],
    }
    return s


def _judge_cmd_and_env(role: str, spec: dict, cwd: str,
                       model: str | None = None) -> tuple[list[str], dict[str, str], str]:
    """judge 계열(judge 본세션/prefilter/validator) 공용 argv/env/settings
    조립. `_consult_cmd_and_env()`와 같은 build-then-return 모양이지만
    `--permission-mode bypassPermissions`를 주지 않고(읽기전용 강제),
    `_readonly_plugin_dirs()`/`_readonly_settings()`를 쓴다."""
    plugins = _readonly_plugin_dirs(role, spec)
    s = _readonly_settings(role, cwd)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(s, tf)
        settings_path = tf.name
    cmd = ["claude", "-p", "--settings", settings_path, "--output-format", "json"]
    for p in plugins:
        cmd += ["--plugin-dir", str(p)]
    cmd += ["--model", model or resolved_role_model()]
    env = {**os.environ, "CLAUDE_ROLE": role, "TOKENMAXXXER_SPAWNED": "1"}
    core_dir = next((p for p in core_plugin_dirs() if Path(p).name == "core"), None)
    if core_dir:
        env["CLAUDE_PLUGIN_ROOT_CORE"] = str(core_dir)
    return cmd, env, settings_path


def _compress_diff(diff_text: str, cap_tokens: int = 18000) -> str:
    """PR-Agent 식 압축: 추가분을 남기고, 삭제-only 훅은 버리고, 삭제된
    파일은 이름만 남긴다. 그래도 `cap_tokens`(대략 4문자/토큰)를 넘으면
    실패가 아니라 파일명 목록으로 더 내려간다(제안서 Constraints:
    "graceful degradation to name lists, not a hard failure")."""
    cap_chars = cap_tokens * 4
    blocks = [b for b in re.split(r"(?=^diff --git )", diff_text, flags=re.MULTILINE) if b.strip()]

    def file_name(block: str) -> str:
        m = re.match(r"diff --git a/(\S+) b/(\S+)", block)
        return m.group(2) if m else "?"

    kept, collapsed = [], []
    for block in blocks:
        name = file_name(block)
        if "deleted file mode" in block:
            collapsed.append(f"deleted: {name}")
            continue
        hunks = re.split(r"(?=^@@ )", block, flags=re.MULTILINE)
        header, hunks = hunks[0], hunks[1:]
        surviving = [h for h in hunks
                     if any(l.startswith("+") and not l.startswith("+++") for l in h.splitlines())]
        if not surviving:
            collapsed.append(f"no-addition: {name}")
            continue
        kept.append(header + "".join(surviving))

    compressed = "\n".join(kept)
    if collapsed:
        compressed += "\n\n[collapsed files]\n" + "\n".join(collapsed)
    if len(compressed) <= cap_chars:
        return compressed

    names = "\n".join(file_name(b) for b in blocks)
    degraded = "[diff 압축 후에도 상한 초과 — 파일명 목록으로 축소]\n" + names
    return degraded[:cap_chars]


def _judge_trace_path(cwd: str) -> Path:
    """모든 judge 실행이 공유하는 트레이스 — `runs/patrol-judge-log.md`
    (제안서 §Constraints "trace-always", consult-log `finally` 관례와
    같은 이유). `runs/`는 git-ignored라 커밋 없이도 대상 트리를
    더럽히지 않는다(이슈 #1730)."""
    return _consult_root(cwd) / "runs" / "patrol-judge-log.md"


def _append_judge_trace(path: Path, ts: str, role: str, merge_sha: str, outcome: str) -> None:
    """judge 실행 한 건당 한 줄 — 성공/실패/캡-초과 가리지 않는다. `merge=`
    필드는 `_judge_roles_run_today()`가 3-역할 캡을 세는 데 쓰는 grep
    앵커다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = (f"- {ts} | role={role} | verb=judge | merge={merge_sha} "
            f"| outcome={outcome[:300]!r}\n")
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


def _judge_roles_run_today(trace_path: Path, merge_sha: str) -> int:
    """이 merge_sha 에 대해 이미 트레이스에 남은 **실제 judge 세션 실행** 수 —
    3-역할 캡 판정에 쓴다. prefilter-미스 줄(`ok: prefilter 미스`)과
    캡-초과 거절 줄(`error: 캡 초과`)은 judge 세션이 실제로 돌지 않았으므로
    세지 않는다(이슈 #1605 — 이 두 outcome 을 세면 처음 3역할이 미스만 내도
    캡이 소진되고, 이후 매 역할의 거절 줄이 또 카운트를 올려 눈덩이처럼
    불어난다). ok-findings/ok-zero-findings/실제 실행 오류(타임아웃, 파싱
    실패 등)는 세션이 실제로 돈 것이므로 그대로 센다.

    **방어적으로 읽는다**: 트레이스 파일이 없거나(회전/최초 실행) 손상돼
    있으면 0 을 돌려준다 — 로그 부재/회전이 캡 판정을 막으면 안 된다는
    PR #1590 binding review note. 읽기 실패는 절대 캡을 가짜로 채우지
    않는다(항상 허용 쪽으로 fail)."""
    try:
        text = trace_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0
    needle = f"| merge={merge_sha} "
    count = 0
    for line in text.splitlines():
        if "verb=judge" not in line or needle not in line:
            continue
        if "prefilter 미스" in line or "캡 초과" in line:
            continue
        count += 1
    return count


_JUDGE_ROLE_EXCLUSIONS: dict[str, list[str]] = {
    # 역할별 알려진 오탐 패턴(문자열 부분일치) — validator 가 이 목록에
    # 걸리는 finding 은 무조건 버린다. 지금은 빈 채로 시작해, 실제 오탐이
    # 나타나면 그때 항목을 더한다(운영 결정 없이 상상으로 채우지 않는다).
}


def _judge_prefilter(role: str, spec: dict, diff_summary: str, cwd: str) -> bool:
    """관할 사전필터 — 하이쿠급 단일 호출로 "이 diff 가 이 역할의 관할에
    조금이라도 걸리는가"만 묻는다(제안서 §5, 가장 큰 비용 절감 지점).
    호출 자체가 실패하면(타임아웃/파싱 실패) **관련 있다고 가정**한다 —
    사전필터는 비용 절감 장치일 뿐 판단 장치가 아니라, 실패를 놓침으로
    바꾸면 안 된다."""
    cmd, env, settings_path = _judge_cmd_and_env(role, spec, cwd, model="haiku")
    prompt = (
        f"역할 '{role}' 의 관할(rulebook jurisdiction) 안에 아래 diff 요약이 "
        "조금이라도 걸리는지만 판단하라. 다른 텍스트 없이 JSON 객체 하나만 "
        '출력하라: {"relevant": true|false}\n\ndiff 요약:\n' + diff_summary
    )
    try:
        r = subprocess.run(cmd, cwd=cwd, input=prompt, text=True,
                           capture_output=True, timeout=JUDGE_TIMEOUT, env=env)
        if r.returncode != 0:
            return True
        result = session_result(r.stdout)
        parsed = _parse_verb_json(result.get("result", ""), "relevant")
        if parsed is None:
            return True
        return bool(parsed.get("relevant", True))
    except subprocess.TimeoutExpired:
        return True
    finally:
        with contextlib.suppress(OSError):
            os.unlink(settings_path)


def _judge_validate(role: str, spec: dict, findings: list[dict], diff_summary: str,
                    cwd: str) -> list[dict]:
    """확인/반박 검증 — 하이쿠급 단일 호출로 judge 가 낸 findings 를
    확인/기각하고, `_JUDGE_ROLE_EXCLUSIONS[role]`에 걸리는 것은 호출 전에
    이미 버린다(Anthropic security-review 패턴, 제안서 §5). 호출 자체가
    실패하면 **아무것도 큐에 넣지 않는다** — 검증 못 한 finding 을 큐로
    흘리는 쪽보다, 이번 실행에서 놓치는 쪽이 patrol 큐 오염보다 싸다."""
    exclusions = _JUDGE_ROLE_EXCLUSIONS.get(role, [])
    candidates = [f for f in findings
                  if not any(x in f.get("excerpt", "") for x in exclusions)]
    if not candidates:
        return []
    cmd, env, settings_path = _judge_cmd_and_env(role, spec, cwd, model="haiku")
    prompt = (
        f"역할 '{role}' 가 낸 아래 findings 를 diff 요약과 대조해 확인(confirm)/"
        "반박(refute)하라. 실제로 룰북을 위반하는 것만 남기고, 다른 텍스트 "
        '없이 JSON 객체 하나만 출력하라: {"findings": [{"path": "...", '
        '"finding_class": "...", "excerpt": "...", "promotable": true|false}, '
        "...]}  (반박된 것은 배열에서 뺀다)\n\n"
        f"diff 요약:\n{diff_summary}\n\nfindings:\n{json.dumps(candidates, ensure_ascii=False)}"
    )
    try:
        r = subprocess.run(cmd, cwd=cwd, input=prompt, text=True,
                           capture_output=True, timeout=JUDGE_TIMEOUT, env=env)
        if r.returncode != 0:
            return []
        result = session_result(r.stdout)
        parsed = _parse_verb_json(result.get("result", ""), "findings")
        if parsed is None:
            return []
        return [f for f in parsed.get("findings", []) if isinstance(f, dict) and f.get("path")]
    except subprocess.TimeoutExpired:
        return []
    finally:
        with contextlib.suppress(OSError):
            os.unlink(settings_path)


def judge_cmd(role: str, merge_sha: str, cwd: str | None = None) -> dict:
    """`spawn.py judge <role> --merge <sha>` 의 본체 — 읽기 전용, 4단계
    파이프라인(prefilter -> judge -> validator -> enqueue), 트레이스는
    성공/실패/캡초과 가리지 않고 항상 한 줄(이슈 #1587, 제안서 §What will
    be done 6).

    3-역할/머지 캡(`JUDGE_MAX_ROLES_PER_MERGE`)은 트레이스 로그에서
    세되, `_judge_roles_run_today()`가 방어적으로 읽는다 — 로그가 없거나
    깨져 있어도 캡을 오탐하지 않고(0으로 fail), 이 실행 자체는 트레이스에
    한 줄을 항상 남긴다(binding review note, PR #1590)."""
    root = str(Path(cwd).resolve()) if cwd else str(ROOT)
    trace_path = _judge_trace_path(root)
    ts = datetime.now(timezone.utc).isoformat()
    outcome = "error: 알 수 없는 실패"
    try:
        already = _judge_roles_run_today(trace_path, merge_sha)
        if already >= JUDGE_MAX_ROLES_PER_MERGE:
            outcome = (f"error: 캡 초과 (merge={merge_sha} 에 이미 {already}개 역할 실행, "
                       f"상한 {JUDGE_MAX_ROLES_PER_MERGE})")
            return {"skipped": True, "reason": "cap_exceeded", "role": role, "merge": merge_sha}

        f = ROOT / "roles" / f"{role}.json"
        if not f.exists():
            have = ", ".join(sorted(p.stem for p in (ROOT / "roles").glob("*.json")))
            raise ValueError(f"모르는 역할: {role}  (있는 것: {have})")
        spec = json.loads(f.read_text())

        show = subprocess.run(["git", "-C", root, "show", "--no-color", merge_sha],
                              capture_output=True, text=True, timeout=JUDGE_TIMEOUT)
        if show.returncode != 0:
            outcome = f"error: git show 실패: {show.stderr.strip()[:300]}"
            raise RuntimeError(outcome)
        diff_summary = _compress_diff(show.stdout)

        if not _judge_prefilter(role, spec, diff_summary, root):
            outcome = "ok: prefilter 미스 — judge 미호출"
            return {"skipped": True, "reason": "prefilter_miss", "role": role, "merge": merge_sha}

        cmd, env, settings_path = _judge_cmd_and_env(role, spec, root)
        prompt = (
            f"당신은 judge 로 불렸다 — 역할 '{role}' 의 룰북 관점에서 아래 merge diff 가 "
            "룰북을 위반하는지만 판단한다. 저장소 파일을 하나도 건드리지 말고(Write/Edit "
            "도구 없음), 브랜치/커밋/PR 을 만들지 마라. 필요하면 `git show`/`git diff`/"
            "`git log` 로 더 살펴봐도 된다. 답을 다 쓴 뒤 마지막에, 다른 어떤 텍스트도 "
            '없이 JSON 객체 하나만 출력하라: {"findings": [{"path": "...", '
            '"finding_class": "...", "excerpt": "...", "promotable": true|false}, ...]}\n\n'
            f"merge diff ({merge_sha}):\n{diff_summary}"
        )
        try:
            r = subprocess.run(cmd + ["--max-turns", "6"], cwd=root, input=prompt, text=True,
                               capture_output=True, timeout=JUDGE_TIMEOUT, env=env)
        finally:
            with contextlib.suppress(OSError):
                os.unlink(settings_path)
        if r.returncode != 0:
            outcome = f"error: judge 세션 종료 코드 {r.returncode}: {r.stderr.strip()[:300]}"
            raise RuntimeError(outcome)
        result = session_result(r.stdout)
        parsed = _parse_verb_json(result.get("result", ""), "findings")
        raw_findings = parsed.get("findings", []) if parsed else []
        if not raw_findings:
            outcome = "ok: findings 없음"
            return {"skipped": False, "role": role, "merge": merge_sha, "enqueued": []}

        validated = _judge_validate(role, spec, raw_findings, diff_summary, root)
        if not validated:
            outcome = f"ok: {len(raw_findings)}건 중 validator 통과 0건"
            return {"skipped": False, "role": role, "merge": merge_sha, "enqueued": []}

        sys.path.insert(0, str((ROOT / "gates").resolve()))
        import patrol_queue
        queue_path = Path(root) / patrol_queue.QUEUE_REL_PATH
        queue = patrol_queue.load_queue(queue_path)
        enqueued = []
        # patrol_queue.verify(): 인용된 경로/발췌를 실제로 다시 읽어 확인한다
        # (run_scan() 이 이미 밟는 scan -> verify -> budget -> enqueue 파이프라인의
        # 그 단계) — validator(하이쿠급 반박 콜)는 모델의 자기평가일 뿐이라,
        # 환각된 path/excerpt 를 그대로 통과시킬 수 있다. verify() 를 건너뛰면
        # judge 만 유일하게 검증 안 된 finding 을 큐에 넣는 경로가 된다.
        for vf in validated:
            if not patrol_queue.verify(vf, Path(root)):
                continue
            fp = patrol_queue.fingerprint(f"judge:{role}", vf["path"], [vf.get("excerpt", "")])
            finding = {
                "fingerprint": fp,
                "scanner_id": f"judge:{role}",
                "path": vf["path"],
                "finding_class": vf.get("finding_class", "judge-finding"),
                "excerpt": vf.get("excerpt", ""),
                "last_seen": ts,
                "lane": "diff",
                "promotable": bool(vf.get("promotable", False)),
            }
            queue = patrol_queue.enqueue(queue, finding)
            enqueued.append(fp)
        patrol_queue.save_queue(queue_path, queue)
        outcome = (f"ok: {len(raw_findings)}건 중 {len(validated)}건 검증, "
                  f"{len(enqueued)}건 verify 통과 후 큐 반영")
        return {"skipped": False, "role": role, "merge": merge_sha, "enqueued": enqueued}
    except subprocess.TimeoutExpired:
        outcome = f"error: 시간초과({JUDGE_TIMEOUT}s)"
        raise
    finally:
        _append_judge_trace(trace_path, ts, role, merge_sha, outcome)


class _PanelMessagingUnavailable(RuntimeError):
    """실측: crossSessionInbound 를 못 걸었거나 SendMessage 왕복이 한 번도
    안 잡혔다 — panel_cmd() 가 순차 consult 로 내려가는 신호."""


def _panel_slug(question: str) -> str:
    """질문을 파일명 조각으로 — 영숫자 외 문자는 `-`, 연속 `-`는 하나로,
    최대 60자(파일시스템/가독성 여유)."""
    s = re.sub(r"[^a-z0-9]+", "-", question.lower()).strip("-")
    return (s[:60].rstrip("-")) or "question"


def _panel_record_path(issue: int | None, slug: str, cwd: str | None = None) -> Path:
    """`docs/issue-<n>/reports/panel/` — 이슈가 없으면 표준 6버킷 중
    `reports/panel/` (`_consult_trace_path()` 와 같은 분기 이유). 앵커는
    `_consult_root()` 로 대상 레포(`-C`/cwd)에 맞춘다."""
    root = _consult_root(cwd)
    if issue is not None:
        return root / "docs" / f"issue-{issue}" / "reports" / "panel" / f"{slug}.md"
    return root / "docs" / "reports" / "panel" / f"{slug}.md"


def _append_panel_turn(path: Path, ts: str, role: str, kind: str, text: str) -> None:
    """턴 하나당 한 줄 — 라이브 경로와 저하 경로가 이 한 헬퍼를 같이
    쓴다(제안서 §What will be done 2) — 두 경로가 서로 다른 기록 포맷으로
    갈라지지 않는다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = f"- {ts} | role={role} | {kind} | {text[:2000]!r}\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


def _extract_sendmessage_turns(stream_lines: list[dict]) -> list[str]:
    """`--output-format stream-json` 이벤트에서 `SendMessage` 도구 호출의
    `message` 인자만 뽑는다 — 세션 하나가 주고받은 실제 왕복을, 최종
    verdict 와 별개로 관찰하기 위해서다."""
    turns = []
    for ev in stream_lines:
        if ev.get("type") != "assistant":
            continue
        for block in (ev.get("message", {}).get("content") or []):
            if isinstance(block, dict) and block.get("type") == "tool_use" \
                    and block.get("name") == "SendMessage":
                msg = (block.get("input") or {}).get("message")
                if msg:
                    turns.append(str(msg))
    return turns


def _run_panel_session(role: str, peer_role: str, question: str, cwd: str | None,
                       model: str | None = None) -> dict:
    """판정 세션 하나를 non-bare `claude -p` 로 띄운다 — `crossSessionInbound`
    를 걸어 `SendMessage` 를 받을 수 있게 한다(이슈#973 phase-1 조사: 공식
    문서, ListAgents/SendMessage 은 non-bare 세션에서만 열린다). 세션
    설정은 `consult_cmd()` 와 똑같이 `role_settings()`/`resolve_role_source()`
    로 조립한다 — 두 코드경로가 갈라지면 한쪽만 고쳐지는 드리프트가 난다
    (#695/#700, `consult_cmd()` 독스트링과 같은 이유).

    `TOKENMAXXXER_PANEL_MESSAGING=unavailable` 이 켜져 있으면
    `_PanelMessagingUnavailable` 을 던진다 — 크로스세션 소켓이 막힌
    샌드박스/CI 환경이 스스로 신고하는 경로다. 호출자는 이걸 순차
    consult 로 내리는 신호로 쓴다."""
    if os.environ.get("TOKENMAXXXER_PANEL_MESSAGING") == "unavailable":
        raise _PanelMessagingUnavailable(f"{role}: TOKENMAXXXER_PANEL_MESSAGING=unavailable")
    f = ROOT / "roles" / f"{role}.json"
    if not f.exists():
        have = ", ".join(sorted(p.stem for p in (ROOT / "roles").glob("*.json")))
        raise ValueError(f"모르는 역할: {role}  (있는 것: {have})")
    spec = json.loads(f.read_text())
    plugins = resolve_role_source(role, _skill_repo_root())["skill_dirs"]
    s = role_settings(role, cwd, inject_self_hosted_hooks=False)
    s["crossSessionInbound"] = "accept"
    settings_path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
            json.dump(s, tf)
            settings_path = tf.name
        cmd = ["claude", "-p", "--settings", settings_path,
               "--permission-mode", "bypassPermissions",
               "--output-format", "stream-json", "--verbose"]
        for p in plugins:
            cmd += ["--plugin-dir", str(p)]
        for p in core_plugin_dirs():
            cmd += ["--plugin-dir", str(p)]
        role_model = resolved_role_model(model)
        if role_model:
            cmd += ["--model", role_model]
        env = {**os.environ, "CLAUDE_ROLE": role, "TOKENMAXXXER_SPAWNED": "1"}
        prompt = (
            "당신은 판정단(panel) 판정자로 불렸다 — 다른 역할 판정자 "
            f"'{peer_role}' 와 함께 아래 질문을 판정한다. 이 역할의 룰북은 "
            "이미 로드돼 있다. 브랜치를 만들지도, 커밋하지도, PR 을 열지도 "
            "마라. 상대 세션은 이 세션과 거의 동시에 떴다 — 아직 인박스가 "
            "등록되지 않았을 수 있다. 먼저 ListAgents 를 호출해 상대를 "
            f"찾아라('{peer_role}' 역할일 것이다). 안 보이면 몇 초 뒤 다시 "
            "ListAgents 를 호출하는 식으로 몇 차례 재시도하라 — 한 번만 "
            "확인하고 포기하지 마라. 상대가 보이면, ListAgents 가 실제로 "
            f"반환한 이름으로 SendMessage 를 보내라('{peer_role}' 같은 "
            "역할명이 아니라 그 이름 그대로 주소를 써라). 먼저 당신의 "
            "입장(position)을 한 문단으로 정리해 SendMessage 로 상대에게 "
            "보내라. 상대의 응답을 받은 뒤 최소 한 차례 반박(rebuttal)을 "
            "SendMessage 로 주고받아라. 교환이 끝나면 다른 어떤 텍스트도 "
            "없이 JSON 객체 하나만 출력하라: "
            '{"answer": "<판단>", "confidence": "low|medium|high", '
            '"caveats": ["<유보/전제>", ...]}\n\n'
            f"질문: {question}"
        )
        r = subprocess.run(cmd, cwd=cwd or str(ROOT), input=prompt, text=True,
                           capture_output=True, timeout=PANEL_TIMEOUT, env=env)
        if r.returncode != 0:
            raise RuntimeError(f"{role}: 세션 종료 코드 {r.returncode}: "
                               f"{r.stderr.strip()[:300]}")
        stream_lines = []
        for line in r.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            with contextlib.suppress(ValueError):
                stream_lines.append(json.loads(line))
        turns = _extract_sendmessage_turns(stream_lines)
        final_text = ""
        for ev in reversed(stream_lines):
            if ev.get("type") == "result":
                final_text = ev.get("result", "")
                break
        verdict = _parse_consult_verdict(final_text)
        return {"turns": turns, "verdict": verdict}
    finally:
        if settings_path:
            with contextlib.suppress(OSError):
                os.unlink(settings_path)


def _consult_or_record_error(path: Path, ts: str, role: str, question: str,
                              issue: int | None, cwd: str | None) -> tuple[dict | None, str | None]:
    """`consult_cmd()` 를 호출하되, 실패해도 밖으로 던지지 않는다 — 저하
    경로에서 `consult_cmd()` 실패는 panel 실행 전체를 크래시시켜선 안
    된다(#1045 결함 2). 실패하면 `consult-error` 턴으로 기록하고
    `(None, <에러 메시지>)` 를 돌려준다."""
    try:
        verdict = consult_cmd(role, question, issue, cwd)
    except Exception as e:  # noqa: BLE001 - 어떤 실패든 절대 밖으로 던지지 않는다
        msg = str(e)
        _append_panel_turn(path, ts, role, "consult-error", msg)
        return None, msg
    _append_panel_turn(path, ts, role, "verdict", str(verdict))
    return verdict, None


def _panel_degrade(path: Path, ts: str, role_a: str, role_b: str, question: str,
                    issue: int | None, cwd: str | None, reason: str) -> dict:
    """저하 경로 — 순차 `consult_cmd()` 두 번으로 판단을 받고, 저하했다는
    사실과 이유를 `degraded:` 마커로 기록에 남긴다(제안서, 병합 설계
    Open Question 4). 각 `consult_cmd()` 호출은 `_consult_or_record_error()`
    로 감싸 — 한쪽이 실패해도(#1045 결함 2) panel 실행 자체는 절대 raise
    하지 않고, 실패는 기록에 남기고 그 쪽 verdict 만 None 이 된다."""
    _append_panel_turn(path, ts, "panel", "degraded", f"sequential-consult — {reason}")
    verdict_a, error_a = _consult_or_record_error(path, ts, role_a, question, issue, cwd)
    verdict_b, error_b = _consult_or_record_error(path, ts, role_b, question, issue, cwd)
    return {"degraded": True, "reason": reason,
            "verdict_a": verdict_a, "verdict_b": verdict_b,
            "error_a": error_a, "error_b": error_b,
            "record_path": str(path)}


def panel_cmd(role_a: str, role_b: str, question: str, issue: int | None = None,
              cwd: str | None = None, run_session=None,
              model: str | None = None) -> dict:
    """동시-판정(concurrent judgment): 두 역할을 non-bare 세션으로 띄워
    `SendMessage` 로 입장과 반박을 주고받게 하고, 매 턴을
    `docs/issue-<n>/reports/panel/<question-slug>.md` 에 남긴다(req#2/#5,
    이슈#973). `consult_cmd()` 의 형제 함수 — 브랜치/PR 없이 판단만
    돌려받는다는 점은 같고, 판정자가 둘이고 서로 대화한다는 점이 다르다.

    `run_session`: 판정 세션 하나를 실행하는 콜러블
    `(role, peer_role, question, cwd) -> {"turns": [...], "verdict": dict|None}`,
    기본은 `_run_panel_session()`(실제 `claude -p` 스폰). 테스트는 이
    인자로 진짜 프로세스 없이 씨드된 응답을 주입한다 — 이 파라미터가
    제안서의 "transport boundary" 다.

    메시징이 안 되면(`_PanelMessagingUnavailable`) 순차 `consult_cmd()`
    두 번으로 저하하고, 저하했다는 사실과 이유를 기록에 남긴다."""
    slug = _panel_slug(question)
    path = _panel_record_path(issue, slug, cwd)
    launcher = run_session or _run_panel_session
    ts = datetime.now(timezone.utc).isoformat()
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            fut_a = ex.submit(launcher, role_a, role_b, question, cwd, model)
            fut_b = ex.submit(launcher, role_b, role_a, question, cwd, model)
            result_a = fut_a.result()
            result_b = fut_b.result()
    except _PanelMessagingUnavailable as e:
        return _panel_degrade(path, ts, role_a, role_b, question, issue, cwd, str(e))
    if not (result_a.get("turns") or result_b.get("turns")):
        # 두 세션 다 SendMessage 왕복이 한 건도 안 잡혔다 — 메시징이
        # 켜지긴 했지만 실제로는 왕복이 안 닿은 경우(제안서 §3의 두 번째
        # 저하 트리거). 이미 스폰된 세션의 verdict 는 버리고, 순차 consult
        # 로 다시 판단을 받아 저하했다는 사실과 함께 기록한다.
        return _panel_degrade(path, ts, role_a, role_b, question, issue, cwd,
                               "no SendMessage round-trip observed")
    for role, result in ((role_a, result_a), (role_b, result_b)):
        turns = result.get("turns") or []
        for i, text in enumerate(turns):
            kind = "position" if i == 0 else "rebuttal"
            _append_panel_turn(path, ts, role, kind, text)
        if result.get("verdict") is not None:
            _append_panel_turn(path, ts, role, "verdict", str(result["verdict"]))
    return {"degraded": False, "verdict_a": result_a.get("verdict"),
            "verdict_b": result_b.get("verdict"), "record_path": str(path)}


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
    ledger_write({"event": "remote_setup_confirmed", "cwd": str(Path(cwd).resolve()),
                  "origin": origin, "ts": int(time.time())})


def positive_int(s: str) -> int:
    """argparse type=: `--issue` 는 1 이상만 유효하다 — 0/음수/거대정수는
    존재할 수 없는 이슈 번호이므로 파싱 시점에 바로 거부한다(#288 N3)."""
    v = int(s)
    if v < 1:
        raise argparse.ArgumentTypeError(f"양의 정수가 아니다: {s}")
    return v


def _workspace_base() -> Path:
    """워크스페이스 루트: `MUSTER_WORK_DIR` 오버라이드, 기본
    `~/.tokenmaxxxer/work` (이슈 #1179 — 이전엔 `clean` CLI 분기와
    `issue_workspace()` 두 곳에 이 네 줄이 따로 있었다)."""
    base = os.environ.get("MUSTER_WORK_DIR")
    return Path(base) if base else Path.home() / ".tokenmaxxxer" / "work"


def _live_workspaces() -> dict[Path, dict]:
    """살아있는(pid alive) 로스터 엔트리를 워크스페이스 절대경로로 인덱싱."""
    roster = _roster_load()
    live = {}
    for e in roster.values():
        if _alive(e.get("pid", 0)):
            live[Path(e["work"]).resolve()] = e
    return live


# 이슈 #1179 (reopen): 훅이 워크스페이스 안에 직접 심어놓는 자체 부기
# 파일 — 사용자가 만든 내용이 아니라 harness 자신의 상태 마커라
# untracked 로 남아도 "미보존 작업"이 아니다. 이 목록에 없는 파일은
# 전부 그대로 dirty 취급(안전 기본값 유지) — 이름을 아는 것만 뺀다.
_HARNESS_NOISE_BASENAMES = frozenset({
    ".pull-check", ".shallow-check", ".orchestrate-greeted",
    ".warrant-hunt.count", ".warrant-hunt.lock",
    # 파이썬 바이트코드 캐시 — 어느 리포에서도 소스에서 재생성되는
    # 순수 파생물이라 "미보존 작업"일 수가 없다(실측 최다 노이즈,
    # 320개 워크스페이스 중 335건).
    "__pycache__",
    # project-rich 리포의 테스트/빌드 산출물 — `file` 로 확인한 SQLite
    # db 와 컴파일된 JS/HTML 번들, 소스 아님(실측: project-rich-issue-*
    # 워크스페이스 다수가 이 파일 하나 때문에만 dirty 로 잡혔다).
    "fundamentals.db", "fundamentals.db-shm", "fundamentals.db-wal",
    "web_out_snapshot", "web_out",
})


def _workspace_clean_state(w: Path, live: dict[Path, dict]) -> tuple[str | None, str]:
    """워크스페이스 하나가 지워도 안전한지 판정한다. `(reason, detail)` —
    `reason` 이 `None` 이면 안전(지워도 됨), 아니면 남기는 이유
    (`"live"`/`"dirty"`) 와 사람이 읽을 상세 문자열.

    `roster_clean()`(수동)과 `auto_sweep()`(자동, 이슈 #1179)이 같은 판정을
    쓴다 — 두 곳에 독립적으로 안전 검사를 두면 한쪽만 고치고 다른 쪽은
    #1124 보장이 조용히 깨진다."""
    e = live.get(w.resolve())
    if e is not None:
        return ("live",
                f"실행 중인 세션 있음: issue-{e.get('issue', '?')}/"
                f"{e.get('role', '?')}, pid {e.get('pid', '?')}")
    raw_st = subprocess.run(["git", "-C", str(w), "status", "--porcelain"],
                            capture_output=True, text=True).stdout.strip()
    # untracked(`??`)이면서 harness 자체 마커 파일인 줄만 걸러낸다 —
    # staged/tracked 변경(M/D/A 등)은 절대 걸러내지 않는다: 실측
    # (2026-08-13, 이 머신) 잔여 320개 워크스페이스 중 293개가 이
    # 마커 파일들 때문에 dirty 로 잘못 잡혔다.
    st_lines = [ln for ln in raw_st.splitlines()
                if not (ln[:2] == "??"
                        and os.path.basename(ln[3:].rstrip("/"))
                        in _HARNESS_NOISE_BASENAMES)]
    st = "\n".join(st_lines)
    ahead = subprocess.run(
        ["git", "-C", str(w), "log", "--branches", "--not", "--remotes",
         "--oneline"], capture_output=True, text=True).stdout.strip()
    if ahead:
        # 레거시 워크스페이스는 생성 뒤 다시 fetch 된 적이 없어, 브랜치가
        # 이미 origin 에 머지됐어도 로컬 remote-tracking ref 가 그 사실을
        # 모른다 — "ahead" 로 영원히 오판된다(실측, accessibility-rulebook
        # issue-19: fetch 전 2건 ahead, fetch 후 0건). 작업트리가 이미
        # 깨끗할 때만 한 번 fetch 로 갱신하고 재판정한다 — fetch 는
        # 로컬을 지우지 않으니 안전.
        if not st:
            try:
                subprocess.run(["git", "-C", str(w), "fetch", "-q", "--all"],
                               capture_output=True, text=True, timeout=30)
            except (subprocess.TimeoutExpired, OSError):
                pass
            ahead = subprocess.run(
                ["git", "-C", str(w), "log", "--branches", "--not",
                 "--remotes", "--oneline"],
                capture_output=True, text=True).stdout.strip()
    if st or ahead:
        detail = "미보존 작업 있음"
        if st:
            detail += f"  [미커밋 {len(st.splitlines())}건]"
        if ahead:
            detail += f"  [미push 커밋 {len(ahead.splitlines())}건]"
        return ("dirty", detail)
    return (None, "")


def _delete_workspace(w: Path, wb: Path, log_outcomes: dict[str, str],
                       archive_dir: Path) -> None:
    """안전 판정을 이미 통과한 워크스페이스 하나를 지운다. 디렉터리는
    그대로 삭제, 형제 파일(로그 등)은 ledger outcome 이 `LANDED_OUTCOMES`
    밖이면(refused/errored/silent-failure 등) 유일한 증거이므로 지우지
    않고 `<wb>/.archived-logs/` 로 옮긴다(이슈 #1124). 실패하면
    예외를 그대로 던진다 — 호출자가 removed/failed 집계를 한다."""

    def _chmod_retry(func, path, exc_info):
        # Go 모듈 캐시 등 읽기 전용 디렉터리/파일에서 rmtree 가
        # PermissionError 로 죽는 문제(이슈 #229). POSIX 에서 파일
        # 삭제는 그 파일 자체가 아니라 부모 디렉터리의 쓰기 권한이
        # 좌우하므로, 실패한 경로와 그 부모 모두에 쓰기 권한을 주고
        # 한 번 재시도한다.
        os.chmod(path, stat.S_IWRITE)
        parent = os.path.dirname(path)
        if parent:
            os.chmod(parent, stat.S_IWRITE | stat.S_IEXEC | stat.S_IREAD)
        func(path)

    import shutil
    if sys.version_info >= (3, 12):
        shutil.rmtree(w, onexc=_chmod_retry)
    else:
        shutil.rmtree(
            w, onerror=lambda func, path, exc_info: _chmod_retry(
                func, path, exc_info))
    # 세대별 로그(`.session.<ts>.<pid>.log`, 이슈 #192)와
    # `.events.jsonl`/`.events.offset`/`.task.txt`/
    # `.respawn-claim-*` 같은 형제 산출 파일을 전부 글롭으로 잡는다 —
    # 접미사를 하나씩 나열하면 다음에 하나 더 생길 때 또 빠뜨린다.
    for sibling in w.parent.glob(w.name + ".*"):
        if not sibling.is_file():
            continue
        outcome = log_outcomes.get(str(sibling))
        if outcome is not None and outcome not in LANDED_OUTCOMES:
            archive_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(sibling), str(archive_dir / sibling.name))
        else:
            sibling.unlink()


def roster_clean(wb: Path, issue: int | None) -> int:
    """`spawn.py clean [--issue N]`: 안전한 것만 지운다 — 미커밋 변경 없음 +
    origin 에 없는 커밋 없음. 워크스페이스 디렉터리는 그 조건만 지키면
    그대로 삭제한다(이슈 #1124 범위 밖). 형제 파일(로그 등)은
    `_delete_workspace()` 가 archive-or-delete 판정을 한다."""
    live = _live_workspaces()
    log_outcomes = _ledger_log_outcomes()
    archive_dir = wb / ".archived-logs"

    scope = f"-issue-{issue}-" if issue is not None else None
    removed = kept = failed = 0
    for w in sorted(wb.glob("*")) if wb.is_dir() else []:
        if not (w / ".git").is_dir():
            continue
        if scope is not None and scope not in w.name:
            continue
        reason, detail = _workspace_clean_state(w, live)
        if reason is not None:
            print(f"남김 ({detail}): {w.name}")
            kept += 1
            continue
        try:
            _delete_workspace(w, wb, log_outcomes, archive_dir)
        except Exception as ex:
            print(f"실패 (삭제 중 예외): {w.name}  [{ex}]")
            failed += 1
            continue
        print(f"지움: {w.name}")
        removed += 1
    summary = f"정리 끝 — 지움 {removed}, 남김 {kept}"
    if failed:
        summary += f", 실패 {failed}"
    print(summary)
    return 0


# 이슈 #1465: poll-heartbeat.sh 의 alive 마커는 세션 시작 시 한 번만
# touch 된다(60초 tick 루프가 시작하기 전, monitors/poll-heartbeat.sh:100-108
# 부근) — 그 스크립트 자신의 tick cadence 상수가 `POLL_HEARTBEAT_SLEEP_SECONDS`
# 기본값 60초다. GC 임계값은 그 cadence 보다 안전하게 커야 한다(그렇지
# 않으면 아직 살아있는 세션의 마커까지 지울 수 있다) — 7일로 잡아 세션이
# 하루 이상 이어져도 안전하게 남긴다.
MONITOR_ALIVE_TOUCH_CADENCE_SECONDS = 120
MONITOR_ALIVE_STALE_THRESHOLD_SECONDS = 7 * 24 * 3600
assert MONITOR_ALIVE_STALE_THRESHOLD_SECONDS > MONITOR_ALIVE_TOUCH_CADENCE_SECONDS

LEGACY_MONITOR_ALIVE_DIRNAME = ".orchestrate-monitor-alive"


def _monitor_alive_root() -> Path:
    """`~/.claude/tokenmaxxxer/monitor-alive` — poll-heartbeat.sh 가 alive
    마커를 쓰는 곳과 같은 해시 규약(이슈 #947/#1280 relocation).
    `MUSTER_TOKENMAXXXER_HOME` 오버라이드는 `~/.tokenmaxxxer`용이라 여기엔
    안 쓴다 — 대신 이 GC 전용 오버라이드로 테스트를 격리한다."""
    override = os.environ.get("MUSTER_MONITOR_ALIVE_ROOT")
    if override:
        return Path(override)
    return Path.home() / ".claude" / "tokenmaxxxer" / "monitor-alive"


def gc_monitor_alive(root: Path | None = None,
                      now: float | None = None,
                      threshold_seconds: float = MONITOR_ALIVE_STALE_THRESHOLD_SECONDS
                      ) -> dict[str, int]:
    """`~/.claude/tokenmaxxxer/monitor-alive/<hash24>/` 아래 stale 마커
    디렉터리를 지운다. `alive` 파일의 mtime(없으면 디렉터리 자체의 mtime)이
    `threshold_seconds` 보다 오래됐으면 지운다. 한 항목에서 나는 오류는
    전체 GC 를 죽이지 않는다(watch-coverage 는 observe-only 라 정리 실패로
    죽으면 안 된다, 이슈 #1465 요구사항 4) — per-entry try/except 로 흡수하고
    `errors` 카운트만 올린다."""
    if root is None:
        root = _monitor_alive_root()
    if now is None:
        now = time.time()
    removed = kept = errors = 0
    try:
        entries = sorted(root.glob("*")) if root.is_dir() else []
    except OSError:
        return {"removed": 0, "kept": 0, "errors": 1}
    for entry in entries:
        try:
            if not entry.is_dir():
                continue
            alive_marker = entry / "alive"
            try:
                mtime = alive_marker.stat().st_mtime
            except OSError:
                mtime = entry.stat().st_mtime
            age = now - mtime
            if age > threshold_seconds:
                import shutil
                shutil.rmtree(entry)
                removed += 1
            else:
                kept += 1
        except OSError:
            errors += 1
    return {"removed": removed, "kept": kept, "errors": errors}


def detect_legacy_monitor_alive_dirs(repo_root: Path) -> list[Path]:
    """`.orchestrate-monitor-alive/` 레거시 디렉터리(relocation 이전,
    이슈 #947/#1280)를 리포트만 한다 — 절대 지우지 않는다(이슈 #1465
    요구사항 3)."""
    try:
        candidate = repo_root / LEGACY_MONITOR_ALIVE_DIRNAME
        if candidate.is_dir():
            return [candidate]
    except OSError:
        pass
    return []


def monitor_alive_gc_cli(cwd: Path) -> int:
    """`spawn.py gc-monitor-alive` — heartbeat 시작 시 poll-heartbeat.sh 가
    호출한다(non-fatal, `|| true`로 감싸 호출됨). GC 자체는 위 함수들에서
    이미 예외를 흡수하지만, 이 진입점도 한 번 더 감싸 정말로 절대 죽지
    않게 한다."""
    try:
        stats = gc_monitor_alive()
        print(f"monitor-alive gc: removed {stats['removed']}, "
              f"kept {stats['kept']}, errors {stats['errors']}")
    except Exception as ex:
        print(f"monitor-alive gc: 실패 (예외, non-fatal) [{ex}]")
    try:
        for legacy in detect_legacy_monitor_alive_dirs(cwd):
            print(f"[legacy-monitor-alive] {legacy} — 레거시 디렉터리, "
                  f"수동 확인 필요 (자동 삭제 안 함)")
    except Exception as ex:
        print(f"monitor-alive gc: 레거시 탐지 실패 (예외, non-fatal) [{ex}]")
    return 0


def _dir_size_bytes(w: Path) -> int:
    """워크스페이스 디렉터리 전체 크기(바이트) — `du` 대신 순수 파이썬으로,
    심볼릭 링크는 따라가지 않는다(순환 방지, 대부분 워크스페이스엔 없다)."""
    total = 0
    for p in w.rglob("*"):
        if p.is_file() and not p.is_symlink():
            try:
                total += p.stat().st_size
            except OSError:
                pass
    return total


def _clean_auto_enabled() -> bool:
    """`MUSTER_CLEAN_AUTO` — 기본 on. `MUSTER_KEEP_SSH` 와 같은 boolean
    파싱 관례(spawn.py:5351 부근)를 따른다."""
    return os.environ.get("MUSTER_CLEAN_AUTO", "") not in (
        "0", "false", "no", "off")


def _clean_max_age_days() -> float:
    """`MUSTER_CLEAN_MAX_AGE_DAYS` — 기본 14일."""
    return float(os.environ.get("MUSTER_CLEAN_MAX_AGE_DAYS", "14"))


def _clean_max_bytes() -> int:
    """`MUSTER_CLEAN_MAX_BYTES` — 기본 5GiB."""
    return int(os.environ.get("MUSTER_CLEAN_MAX_BYTES", str(5 * 1024**3)))


def auto_sweep(wb: Path, max_age_days: float, max_bytes: int,
               now: float | None = None) -> dict[str, int]:
    """이슈 #1179: 스폰-타임 자동 정리. `roster_clean()` 과 같은 안전 판정
    (`_workspace_clean_state()`)만 지운다 — 살아있는 세션, 미커밋/미push
    작업은 절대 건드리지 않는다(#1124 보장 유지).

    두 단계 bound: 1) `max_age_days` 보다 오래된 안전 워크스페이스는
    무조건 지운다. 2) 그러고도 안전 워크스페이스 총합 크기가
    `max_bytes` 를 넘으면, 오래된 것부터 더 지워서 bound 아래로 낮춘다.
    나이만으로는 스폰이 늘면 디스크가 계속 자라고, 크기만으로는 방금
    생긴 워크스페이스도 지울 수 있다 — 두 축을 다 잡는다(각 축이 막는
    실패 모드가 다르다).

    `now`: 테스트가 `time.time()` 대신 고정 시각을 주입한다."""
    now = now if now is not None else time.time()
    live = _live_workspaces()
    log_outcomes = _ledger_log_outcomes()
    archive_dir = wb / ".archived-logs"
    max_age_sec = max_age_days * 86400

    candidates = []  # (mtime, size, path)
    if wb.is_dir():
        for w in sorted(wb.glob("*")):
            if not (w / ".git").is_dir():
                continue
            reason, _detail = _workspace_clean_state(w, live)
            if reason is not None:
                continue
            try:
                mtime = w.stat().st_mtime
            except OSError:
                continue
            candidates.append([mtime, None, w])

    removed = failed = 0

    def _reap(entry) -> None:
        nonlocal removed, failed
        try:
            _delete_workspace(entry[2], wb, log_outcomes, archive_dir)
            removed += 1
        except Exception as ex:
            print(f"[auto-sweep] 실패 (삭제 중 예외): {entry[2].name}  [{ex}]",
                  file=sys.stderr)
            failed += 1

    remaining = []
    for entry in candidates:
        if now - entry[0] > max_age_sec:
            _reap(entry)
        else:
            remaining.append(entry)

    if max_bytes > 0 and remaining:
        for entry in remaining:
            entry[1] = _dir_size_bytes(entry[2])
        remaining.sort(key=lambda e: e[0])  # 오래된 것부터
        total = sum(e[1] for e in remaining)
        i = 0
        while total > max_bytes and i < len(remaining):
            entry = remaining[i]
            total -= entry[1]
            _reap(entry)
            i += 1

    if removed or failed:
        print(f"[auto-sweep] 지움 {removed}" + (f", 실패 {failed}" if failed else ""),
              file=sys.stderr)
    return {"removed": removed, "failed": failed}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("role", nargs="?", help="역할. 생략하면 상태만 보여준다")
    ap.add_argument("task", nargs="?", help="맡길 일. 룰북 커맨드면 '/plugin:command 인자'")
    ap.add_argument("consult_question", nargs="?",
                    help="consult <역할> \"<질문>\": 세 번째 위치 인자로 질문을 받는다")
    ap.add_argument("panel_question", nargs="?",
                    help="panel <역할A> <역할B> \"<질문>\": 네 번째 위치 인자로 질문을 받는다")
    ap.add_argument("-C", "--cwd", default=".", help="작업 디렉터리")
    ap.add_argument("--dry-run", action="store_true", help="합쳐진 설정만 보고 안 띄운다")
    ap.add_argument("--no-contract", action="store_true",
                    help="대상 레포에 계약이 없어도 띄운다. 보드를 안 쓸 작업에만")
    ap.add_argument("--trust-repo-config", action="store_true",
                    help="대상 레포의 .claude/ 설정·훅을 신뢰한다. 읽어본 뒤에만")
    ap.add_argument("--issue", type=positive_int,
                    help="이 이슈 번호로 스폰한다: issue-<n>/<역할> 브랜치를 만들고 프롬프트에 명시")
    ap.add_argument("--model",
                    help="이 스폰 한 번만 쓸 모델 오버라이드: --model > "
                         "MUSTER_ROLE_MODEL > role_model.txt > \"sonnet\" (이슈#1736). "
                         "judge prefilter/validator 의 하드코딩 haiku 는 영향받지 않는다")
    ap.add_argument("--skills", default=None,
                    help="쉼표로 구분한 스킬 이름 목록을 skill-repository 체크아웃"
                         "(MUSTER_SKILL_REPO 또는 형제-클론)에서 마운트한다"
                         "(이슈 #1742). 생략하면 스폰 argv/env 는 이전과 동일")
    ap.add_argument("--merge", help="judge <역할> --merge <sha>: 판단할 머지의 커밋 sha")
    ap.add_argument("--unattended", action="store_true",
                    help="사람이 없는 실행. mint 는 안 되고, 휴먼 게이트는 선다")
    ap.add_argument("--limit", type=int, default=12,
                    help="drive: 한 번에 띄울 최대 횟수 (기본 12, 폭주 방지)")
    ap.add_argument("--login", help="init: approvers.md 에 넣을 GitHub 로그인 (기본: gh api user)")
    ap.add_argument("--stall-timeout", type=float, default=5.0,
                    help="분 단위. role task/watch 가 이벤트 없이 블록하는 최대 시간 (기본 5)")
    ap.add_argument("--role", dest="watch_role",
                    help="watch: 같은 이슈에 역할이 여럿 기록돼 있을 때 지정")
    ap.add_argument("--follow", action="store_true",
                    help="watch: 이벤트마다 재무장하지 않고 session-end 까지 "
                         "_await_bounded 를 반복 호출하며 스트리밍한다")
    ap.add_argument("--rearm", action="store_true",
                    help="watch: 죽은 워처를 non-blocking 으로 재무장하고 즉시 "
                         "리턴한다 — --follow 와 달리 호출자가 죽어도 워처는 "
                         "살아남는다 (이슈 #1133)")
    ap.add_argument("--self-heal", action="store_true",
                    help="watch --follow: auto-arm 워처 전용. stall/wall-clock "
                         "에서 리턴 대신 진행 상태를 리셋하고 루프를 계속 돌아 "
                         "session-end 까지 스스로 재무장한다 (이슈 #927). "
                         "대화형 호출에는 쓰지 않는다")
    ap.add_argument("--max-wait", type=float, default=None,
                    help="분 단위. watch --follow 반복 전체에 걸친 wall-clock "
                         "상한 — 활동(로그 증가)이 있어도 이 시간이 지나면 "
                         "리턴한다 (기본 없음=비활성, 이슈 #645)")
    ap.add_argument("--no-wait", action="store_true",
                    help="spawn --issue: fork 직후 _await_bounded 없이 즉시 "
                         "리턴한다 — 재개 명령(spawn.py watch)을 찍는다 (이슈 #645)")
    ap.add_argument("--despite-returned", action="store_true",
                    help="[DEPRECATED, 이슈 #1239] no-op — 게이트가 이제 "
                         "항상 non-blocking surfacing 이라 스폰을 거절하지 "
                         "않으므로 무시할 것이 없다. CLI 호환성을 위해 남아 "
                         "있을 뿐 (이슈 #680)")
    ap.add_argument("--single-phase", action="store_true",
                    help="스폰하는 세션에 CORE_BUILD_NOW=1 을 실어 phase-1 "
                         "제안 라운드를 건너뛰게 한다(contract v3 s19a 우회, "
                         "이슈 #1672/#1978). 스포너가 명시적으로 결정할 "
                         "때만 켠다 — 세션 스스로는 절대 켤 수 없다.")
    ap.add_argument("--all", action="store_true",
                    help="watch: 워크스페이스 인덱스 전체를 다중화해 스트리밍한다 "
                         "(오케스트레이터가 대화당 한 번 무장하는 집계 뷰, 이슈 #488)")
    ap.add_argument("--until-idle", action="store_true",
                    help="watch --all: 워치 중인 세션이 모두 session-end 를 "
                         "남기면(또는 인덱스가 비어 있으면) 영원히 블록하지 "
                         "않고 리턴한다 (--all 하고만 쓴다, 이슈 #559)")
    ap.add_argument("--auto-respawn", action="store_true",
                    help="watchdog: crashed 세션에 한해 최대 2회 자동 재스폰, "
                         "상한 도달 시 이슈 코멘트 (기본 off, 관찰-전용 유지)")
    ap.add_argument("--unreported", action="store_true",
                    help="reconcile: roster 대신 workspace 인덱스를 훑어, "
                         "session-end(normal) 인데 아직 [watch] 코멘트가 없는 "
                         "엔트리를 찍는다 (이슈 #534, 압축/재시작 뒤 복구용 단일 스윕)")
    ap.add_argument("--remediation-merged", action="store_true",
                    help="reconcile --issue N: docs/issue-N/decisions/remediation-*.md 중 "
                         "status: open 인 기록의 routed_to 역할 브랜치가 머지됐으면 "
                         "이슈에 코멘트를 남긴다 (이슈 #587 round 2, §12 event 4)")
    ap.add_argument("--post", action="store_true",
                    help="closure-sweep: 위반을 해당 이슈에 코멘트로도 남긴다 (기본은 stdout 만)")
    ap.add_argument("--json", action="store_true",
                    help="flows: 사람용 표 대신 flows-schema.md 계약대로 JSON 을 stdout 에 찍는다")
    a = ap.parse_args()

    if a.role == "init":
        # 보드로 선언한다(approvers.md). on-the-record 가 남의 레포에 쓰는 유일한 경우.
        return init_board(a.cwd, a.login)
    if a.role == "ps":
        return roster_ps()
    if a.role == "recut-if-absorbed":
        return recut_if_absorbed_cli(str(Path(a.cwd).resolve()))
    if a.role == "watchdog":
        # 이슈 #1219: `-C` (기본값 ".") 를 그대로 넘긴다 — 컨슈머 세션은
        # 타깃 프로젝트를, dev 세션(cwd == 이 체크아웃)은 이 체크아웃
        # 자신을 본다. 이전에는 이 호출이 `-C` 를 무시하고 전역 ROOT(=이
        # 체크아웃)만 스캔해, 컨슈머 세션이 on-the-record 자신의
        # 이슈/PR/다이제스트를 받는 원인이었다.
        # 이슈 #1274: 예약 센티널로만 진짜(파이썬 레벨) 크래시를 신호한다 —
        # roster_watchdog() 의 정상 반환값(anomaly count)과 절대 안 겹치게.
        # 이슈 #1456: 틱을 돌리기 전에 canonical-체크아웃 가드 -> 단일-인스턴스
        # 락 -> 시작 HEAD 기록 순으로 통과해야 한다; 틱을 돌린 뒤에는
        # 코드-신선도를 다시 확인해 구코드로 계속 도는 것을 막는다.
        ok, msg = watchdog_canonical_guard()
        if not ok:
            print(msg)
            return WATCHDOG_NONCANONICAL_SENTINEL
        ok, msg = watchdog_lock_acquire()
        if not ok:
            print(msg)
            return WATCHDOG_LOCKED_SENTINEL
        startup_head = watchdog_current_head()
        try:
            rc = roster_watchdog(auto_respawn=a.auto_respawn, all_scope=a.all,
                                  root=Path(a.cwd).resolve())
        except Exception:
            traceback.print_exc(file=sys.stderr)
            return WATCHDOG_CRASH_SENTINEL
        if startup_head is not None:
            fresh, msg = watchdog_freshness_check(
                startup_head, state_path=WATCHDOG_FRESHNESS_STATE_PATH)
            if not fresh:
                if msg:
                    print(msg)
                return WATCHDOG_STALE_CODE_SENTINEL
        return rc
    if a.role == "poll-due":
        return 0 if poll_due(poll_state=POLL_STATE) else 1
    if a.role == "gc-monitor-alive":
        return monitor_alive_gc_cli(Path(a.cwd).resolve())
    if a.role == "reconcile":
        return roster_reconcile(a.issue, unreported=a.unreported,
                                 remediation_merged=a.remediation_merged,
                                 root=Path(a.cwd).resolve())
    if a.role == "flows":
        sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
        import flows
        return flows.flows(a.cwd, a.json, all_scope=a.all)
    if a.role == "roles-due":
        # board_condition 평가기 — 판단(judgment) 잔여만 (issue #896 step 2).
        # 표준 발동(test-authoring 등)은 이제 항상-켜짐 훅이 맡고, 여기는
        # 스폰 여부까지 판단이 필요한 나머지 역할만 surfaced-only 로 보고한다.
        sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
        import roles_due as _roles_due
        due = _roles_due.roles_due(Path(a.cwd).resolve())
        lines = _roles_due.format_report(due)
        for line in lines:
            print(line)
        return 0
    if a.role == "needs-due":
        # need-detector 평가기 — 대상 프로젝트가 이 역할의 실제 산출물을
        # "필요로 하는지" 판정한다 (issue #1160 step 3 machinery).
        # roles-due 와 마찬가지로 advisory-only: 절대 자동 스폰하지 않는다.
        sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
        import need_detector as _need_detector
        due = _need_detector.needs_due(
            Path(a.cwd).resolve(), root=Path(__file__).parent.resolve())
        lines = _need_detector.format_report(due)
        for line in lines:
            print(line)
        return 0
    if a.role == "closure-sweep":
        # 보드 전체를 훑어 이슈-PR 종결 불일치를 보고한다 — 명시적 단발 호출
        # (approve-scope 와 마찬가지로 watchdog 틱에 자동으로 안 물린다, 이슈 #135).
        sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
        import closure_sweep
        root = Path(a.cwd).resolve()
        issue_states, _ = closure_sweep.issue_state_index_all(root)
        violations, skips = closure_sweep.find_violations(root, issue_states=issue_states)
        if skips:
            print("종결 일관성 스윕: 확인 불가")
            print(f"{len(skips)}건 확인 못함: " +
                  ", ".join(s.get("subject", "?") for s in skips))
            if violations:
                print("(부분적으로 확인된 위반)")
                print(closure_sweep.format_report(violations))
            if a.post and violations:
                closure_sweep.post_sweep_comments(root, violations)
            return 2
        if not violations:
            print("종결 일관성 스윕: 위반 없음")
            return 0
        print("종결 일관성 스윕: 위반 발견")
        print(closure_sweep.format_report(violations))
        if a.post:
            closure_sweep.post_sweep_comments(root, violations)
        return 1
    if a.role == "consult":
        if not a.task or not a.consult_question:
            sys.exit('사용법: spawn.py consult <역할> "<질문>" [--issue <n>]')
        try:
            verdict = consult_cmd(a.task, a.consult_question, issue=a.issue, cwd=a.cwd,
                                  model=a.model)
        except Exception as e:
            sys.exit(f"consult 실패(트레이스는 남았다): {e}")
        print(json.dumps(verdict, indent=2, ensure_ascii=False))
        return 0
    if a.role in ("ideate", "draft", "review"):
        if not a.task or not a.consult_question:
            sys.exit(f'사용법: spawn.py {a.role} <역할> "<{a.role} 요청>" [--issue <n>]')
        verb_fn = {"ideate": ideate_cmd, "draft": draft_cmd, "review": review_cmd}[a.role]
        try:
            result = verb_fn(a.task, a.consult_question, issue=a.issue, cwd=a.cwd)
        except Exception as e:
            sys.exit(f"{a.role} 실패(트레이스는 남았다): {e}")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    if a.role == "judge":
        if not a.task or not a.merge:
            sys.exit('사용법: spawn.py judge <역할> --merge <sha> [-C <repo>]')
        try:
            result = judge_cmd(a.task, a.merge, cwd=a.cwd)
        except Exception as e:
            sys.exit(f"judge 실패(트레이스는 남았다): {e}")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    if a.role == "findings-due":
        # 자문(consult) 계열과 달리 advisory-only — 절대 자동으로 이슈를 파지
        # 않는다(이슈 #1202 requirement 4). roles-due/needs-due 와 같은
        # print-only 모양.
        sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
        import findings_due as _findings_due
        due = _findings_due.findings_due(Path(a.cwd).resolve())
        lines = _findings_due.format_report(due)
        for line in lines:
            print(line)
        return 0
    if a.role == "panel":
        if not a.task or not a.consult_question or not a.panel_question:
            sys.exit('사용법: spawn.py panel <역할A> <역할B> "<질문>" [--issue <n>]')
        if a.task == a.consult_question:
            sys.exit("panel 은 서로 다른 두 역할이 필요하다 — 같은 역할을 두 번 줬다")
        try:
            verdict = panel_cmd(a.task, a.consult_question, a.panel_question,
                                 issue=a.issue, cwd=a.cwd, model=a.model)
        except Exception as e:
            sys.exit(f"panel 실패(트레이스는 남았다): {e}")
        print(json.dumps(verdict, indent=2, ensure_ascii=False))
        return 0
    if a.role == "kill":
        if not a.task or a.issue is None:
            sys.exit("사용법: spawn.py kill <역할> --issue <n>")
        return roster_kill(a.issue, a.task)
    if a.role == "watch":
        if a.all:
            if a.issue is not None:
                sys.exit("사용법: spawn.py watch --all 은 --issue 와 함께 못 쓴다")
            return _watch_all(a.stall_timeout, until_idle=a.until_idle)
        if a.until_idle:
            sys.exit("사용법: spawn.py watch --until-idle 은 --all 과 함께만 쓴다")
        if a.issue is None:
            sys.exit("사용법: spawn.py watch --issue <n> [--role <역할>] "
                     "[--stall-timeout <분>], 또는 spawn.py watch --all")
        # 이슈 #554: `kill <역할> --issue N` 과 같은 위치 인자 문법을
        # `watch` 에도 허용한다 — `--role` 이 이미 있으면 그게 우선한다.
        watch_role = a.watch_role or a.task
        if a.rearm:
            return _rearm_watcher_detached(a.issue, watch_role, a.stall_timeout,
                                            repo=_repo_identity(a.cwd), cwd=a.cwd)
        return _watch(a.issue, watch_role, a.stall_timeout, follow=a.follow,
                      repo=_repo_identity(a.cwd), max_wait_min=a.max_wait,
                      self_heal=a.self_heal)
    if a.role == "clean":
        return roster_clean(_workspace_base(), a.issue)
    if a.role == "doctor":
        # 훅 발화 실측. 버전마다 한 번 — 룰북 집행의 전제조건이다.
        return doctor()
    if a.role == "approve":
        sys.exit("v3: 승인은 파일 발행이 아니라 GitHub 행위다 — 오케스트레이터가\n"
                 "  사용자와의 대화에서 gh pr review --approve / gh pr merge 로 중계한다.")
    if a.role == "approve-scope":
        if a.issue is None:
            sys.exit("사용법: spawn.py approve-scope --issue <n> [-C <레포>]")
        return approve_scope(a.cwd, a.issue)
    if a.role == "drive":
        # 보드가 지목하는 역할을 하나씩, 멈출 때까지.
        require_board(a.cwd, a.no_contract)
        require_no_repo_config(a.cwd, a.trust_repo_config)
        require_doctor()
        ensure_target_remote(a.cwd, a.unattended)
        return drive(a.cwd, a.unattended, a.limit)
    if not a.role:
        print("\n".join(status(a.cwd)))
        print("\n역할:")
        for p in sorted((ROOT / "roles").glob("*.json")):
            try:
                meta = json.loads(p.read_text())
            except ValueError:
                meta = {}
            print(f"  {p.stem:12s} {meta.get('decides','')}  — {meta.get('use_when','')}")
        return 0
    if not a.task:
        sys.exit("맡길 일이 없다. 사용법: spawn.py <역할> \"<맡길 일>\" [-C <경로>]")

    # --dry-run 은 세션을 안 태운다. 계약 검사는 버려질 세션을 막으려는 것이므로
    # 아무것도 안 띄우는 호출까지 막을 이유가 없다.
    require_board(a.cwd, a.no_contract or a.dry_run)
    # 드라이런도 막는다 — 레포가 자기 훅을 들고 있으면 그건 세션을 띄우기
    # 전에 알아야 할 사실이지, 띄우고 나서 알 일이 아니다.
    require_no_repo_config(a.cwd, a.trust_repo_config)
    require_acceptance_gate(a.cwd, a.issue)
    require_requirement_linkage(a.cwd, a.issue)
    if a.dry_run:
        cwd_path = Path(a.cwd)
        if not cwd_path.is_dir():
            sys.exit(f"-C 가 디렉터리가 아니다: {a.cwd}")
        out = role_settings(a.role, a.cwd)
        # MUSTER_ROLE_MODEL / role_model.txt (이슈#93): spawn_cmd 는 이
        # dry-run 경로를 안 타므로(세션을 안 띄우니까) --model 부착 여부가
        # 여기 안 보이면 이슈#31 acceptance 커맨드(`--dry-run`)로는 이 기능을
        # 검증할 수 없다(실측:
        # docs/reports/2026-07-29-hunt-muster-role-model-build.md). resolved_role_model()
        # 로 spawn_cmd 와 동일한 env > config > built-in "sonnet" 경로를 태워,
        # 둘 다 비어있어도 built-in 값을 키에 넣는다.
        role_model = resolved_role_model(a.model)
        if role_model:
            out["model"] = role_model
        print(json.dumps(out, indent=2, ensure_ascii=False))
        if role_model:
            # 실제 스폰 시 spawn_cmd 가 argv 에 붙이는 것과 같은 두 토큰을
            # 여기서도 보여준다 — 이슈#31 acceptance("--dry-run 이 --model
            # sonnet 을 보여준다")가 겨냥하는 문구 그대로.
            print(f"--model {role_model}")
        return 0
    require_doctor()
    ensure_target_remote(a.cwd, a.unattended)
    return _spawn_one(a.cwd, a.role, a.task, a.unattended, a.issue,
                      bounded=a.issue is not None,
                      stall_timeout_min=a.stall_timeout,
                      no_wait=a.no_wait,
                      despite_returned=a.despite_returned,
                      model=a.model, skills=a.skills,
                      single_phase=a.single_phase)


_GH_TOKEN_CACHE: str | None = None


def _resolve_gh_token() -> str:
    """`MUSTER_AGENT_GH_TOKEN` 이 있으면 그것, 없으면 `gh auth token` 을 한
    번만 불러 프로세스 전체에서 캐시한다(issue_workspace/checkout_issue_branch
    가 한 스폰에서 `_fetch_or_halt` 를 최대 2번까지 부르므로, 캐시 없이는
    `gh auth token` 을 그만큼 다시 shell-out 한다). 실패하면 빈 문자열 —
    호출부가 "주입 안 함"으로 처리한다.

    `spawn_cmd()` 가 역할 세션의 `GH_TOKEN` env 를 채울 때 쓰던 것과 같은
    로직이다(중복 제거) — 두 소비자가 정확히 같은 우선순위를 공유해야,
    오케스트레이터 자신의 git 호출과 역할 세션이 서로 다른 계정으로 인증하는
    일이 없다."""
    global _GH_TOKEN_CACHE
    if _GH_TOKEN_CACHE is not None:
        return _GH_TOKEN_CACHE
    token = os.environ.get("MUSTER_AGENT_GH_TOKEN")
    if not token:
        with _timed("gh_token"):
            try:
                t = subprocess.run(["gh", "auth", "token"], capture_output=True,
                                   text=True, timeout=15)
                token = t.stdout.strip() if t.returncode == 0 else ""
            except Exception:
                token = ""
    _GH_TOKEN_CACHE = token
    return token


def _git_env() -> dict[str, str] | None:
    """오케스트레이터 자신이 origin 에 하는 git 호출(fetch/push)에 얹을 env.

    `issue_workspace()` 가 작업 클론에 심는 credential.helper
    (`!f() { ...; echo password=$GH_TOKEN; }; f`)는 그 helper 를 실행하는
    프로세스의 `$GH_TOKEN` 을 읽는다. 역할 세션에는 `spawn_cmd()` 가 이
    값을 명시 주입하지만, `_fetch_or_halt()`/`ensure_pushed()` 는
    오케스트레이터 자신의 프로세스에서 돈다 — 아무도 이 프로세스의 env 에는
    넣어주지 않았다(실측: reasona 검증 중 `GH_TOKEN` 없이 `python3
    spawn.py` 를 그냥 돌리면 재사용 워크스페이스 fetch 가 인증 실패로
    막힌다. 이 개발 기계에서는 github.com 용 osxkeychain 항목이 우연히
    있어서 처음엔 안 보였다 — `security find-internet-password -s
    github.com` 으로 그 항목이 fetch 를 대신 통과시켰다는 것과, env 헬퍼
    하나만 남기면 `Authentication failed` 로 재현된다는 것 둘 다 확인했다).

    토큰을 못 구하면 `None` 을 돌려 `subprocess.run` 이 부모 env 를 그대로
    물려받게 한다 — 빈 문자열로 덮어써서 사용자의 다른 자격증명 경로
    (ssh-agent, osxkeychain)를 막지 않는다."""
    token = _resolve_gh_token()
    if not token:
        return None
    return {**os.environ, "GH_TOKEN": token,
            "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "true"}


_FETCHED_THIS_SPAWN: dict[str, float] = {}

# 이슈 #1507 — work_dir 별 부트스트랩 fetch 기록(origin/main sha + fetch
# 시각). 세션이 절대-부재 주장을 쓰기 전에 이 기록이 이미 있어야 한다.
_BOOTSTRAP_FETCH_RECORD: dict[str, dict] = {}


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
    r = _run_net(["git", "-C", work_dir, "fetch", "--prune", "-q", "origin"],
                label, env=_git_env())
    if r.returncode != 0 or "failed to store" in r.stderr:
        sys.exit(f"{label}: fetch 실패 — {r.stderr.strip()[:200]}")
    base = _base(work_dir)
    sha_r = subprocess.run(["git", "-C", work_dir, "rev-parse", base],
                           capture_output=True, text=True)
    sha = sha_r.stdout.strip() if sha_r.returncode == 0 else ""
    record = {"sha": sha, "fetched_at": datetime.now(timezone.utc).isoformat()}
    _BOOTSTRAP_FETCH_RECORD[str(Path(work_dir).resolve())] = record
    return record


def get_bootstrap_fetch_record(work_dir: str) -> dict | None:
    """이슈 #1507 — `bootstrap_fetch_and_record_sha()`가 이 work_dir 에
    이미 남긴 기록을 조회한다. 없으면 None(아직 부트스트랩 fetch 전)."""
    return _BOOTSTRAP_FETCH_RECORD.get(str(Path(work_dir).resolve()))


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
    if key in _FETCHED_THIS_SPAWN:
        if after is not None:
            after()
        return
    r = _run_net(["git", "-C", work_dir, "fetch", "-q", "origin"], label,
                env=_git_env())
    if after is not None:
        after()
    if r.returncode != 0 or "failed to store" in r.stderr:
        sys.exit(f"{label}: fetch 실패 — {r.stderr.strip()[:200]}")
    _FETCHED_THIS_SPAWN[key] = time.monotonic()


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


def issue_workspace(cwd: str, issue: int, role: str) -> str:
    """이슈 스폰마다 on-the-record 소유의 격리 클론을 만든다.

    산출물이 PR 로만 돌아오는 모델에서 역할 세션이 사용자의 체크아웃을
    공유할 이유가 없다 — 공유하면 동시 스폰 둘이 같은 .git/index 와 현재
    브랜치를 두고 경합한다(실측: issue-45 와 issue-59 coding 세션이 한
    트리에서 충돌 직전까지 갔다). 로컬에서 클론하고 origin 을 실제 원격으로
    되돌려 push/gh 가 GitHub 로 가게 한다. 재스폰이면 기존 작업 디렉토리를
    fetch 로 재사용한다 — 진행 중이던 브랜치 작업을 버리지 않는다.
    """
    src = Path(cwd).resolve()
    r = subprocess.run(["git", "-C", str(src), "remote", "get-url", "origin"],
                       capture_output=True, text=True)
    origin = r.stdout.strip()
    # 샌드박스는 HTTP 프록시만 뚫려 있다 — ssh(22번)는 나갈 수 없으므로
    # 작업 클론의 origin 은 기본으로 https 로 정규화한다. 회사 정책이 ssh
    # 원격만 허용하면 MUSTER_KEEP_SSH=1 로 끈다 — 그 경우 세션 안 push 는
    # 실패하지만, 세션 뒤 on-the-record 가 호스트 환경(사용자의 ssh 키)에서
    # push/PR 를 대신한다(아래 ensure_pushed).
    if os.environ.get("MUSTER_KEEP_SSH", "") not in ("", "0", "false", "no", "off"):
        pass
    else:
        m = re.match(r"^(?:ssh://)?git@github\.com[:/](.+?)(?:\.git)?$", origin)
        if m:
            origin = "https://github.com/%s.git" % m.group(1)
    if not origin:
        sys.exit(f"대상 레포에 origin 원격이 없다: {src} — 이슈/PR 모델은 "
                 f"GitHub 원격이 전제다 (계약 v3 s10)")
    # 보호 경로 밖이어야 한다: on-the-record 가 ~/.claude/plugins/ 아래 설치되면
    # ROOT/runs/work 도 그 아래가 되는데, 거긴 Claude Code 의 전역 sensitive
    # 경로라 역할 세션의 Write 가 전부 거부된다(실측: phase 2 가 코드 한 줄
    # 못 쓰고 $2.68 을 태웠다). 기본은 ~/.tokenmaxxxer/work, 오버라이드는
    # MUSTER_WORK_DIR.
    work_base = _workspace_base()
    # 이름은 origin 의 레포명에서 뽑는다 — 디렉토리 이름(slug)을 쓰면
    # 워크스페이스를 -C 로 다시 넘겼을 때 이름이 이중으로 붙는다(실측:
    # ...-issue-45-coding-issue-45-coding). origin 은 위에서 이미 읽었다.
    repo_name = re.sub(r"\.git$", "", origin.rstrip("/").rsplit("/", 1)[-1]) or slug(cwd)
    work = work_base / f"{repo_name}-issue-{issue}-{role}"
    # cwd 가 이미 이 (이슈,역할)의 워크스페이스면 그대로 쓴다 — 중첩 금지.
    if src == work.resolve():
        _fetch_or_halt(str(src), "재사용 워크스페이스")
        _write_role_sidecar(str(src), issue, role)
        return str(src)
    if (work / ".git").exists():
        # 이 경로가 우리가 만든 워크스페이스가 아니라 우연히 같은 이름으로
        # 미리 놓인 남의 레포일 수 있다(#288 N5) — origin 이 다르면 그건
        # 네트워크 문제가 아니라 신원 불일치이므로 fetch 를 시도하기 전에
        # 여기서 끊는다.
        rw = subprocess.run(["git", "-C", str(work), "remote", "get-url", "origin"],
                            capture_output=True, text=True)
        work_origin = rw.stdout.strip()
        def _norm(u):
            # ssh/https 형태 차이는 신원이 아니다 — MUSTER_KEEP_SSH 가 두
            # 스폰 사이에 토글되면 `origin`(위에서 이미 그 시점의 env로
            # 정규화됨)과 예전에 클론된 work_origin 의 스킴이 다를 수
            # 있으므로, 비교 직전에 둘 다 무조건 https 형태로 다시 맞춘다
            # (실측: warrant hunt, MUSTER_KEEP_SSH 토글이 진짜 재사용을
            # "다른 레포"로 오판).
            u = re.sub(r"^(?:ssh://)?git@github\.com[:/](.+?)(?:\.git)?$",
                       r"https://github.com/\1", u)
            return re.sub(r"\.git$", "", u.rstrip("/"))
        if _norm(work_origin) != _norm(origin):
            sys.exit(f"작업 경로에 다른 레포가 있다 (origin 불일치): {work} "
                     f"— 기대: {origin}, 실제: {work_origin or '(없음)'}")
        _fetch_or_halt(str(work), "재사용 워크스페이스")
        _write_role_sidecar(str(work), issue, role)
        return str(work)
    work.parent.mkdir(parents=True, exist_ok=True)
    c = _run_net(["git", "clone", "-q", str(src), str(work)], "작업 클론",
                timeout=CLONE_TIMEOUT)
    if c.returncode != 0:
        sys.exit(f"작업 클론을 만들지 못했다: {c.stderr.strip()[:200]}")
    subprocess.run(["git", "-C", str(work), "remote", "set-url", "origin",
                    origin], capture_output=True, text=True)
    # https push 자격증명: 디스크에 토큰을 남기지 않고 env(GH_TOKEN)를 읽는
    # credential helper 를 작업 클론에만 심는다.
    ex = work / ".git" / "info" / "exclude"
    lines = [".muster-cache/"]
    # 이슈 #289 H1: Claude Code 샌드박스는 홈 디렉터리의 이 dotfile 들을
    # 워크스페이스 루트에 오버레이한다 — 밖에서 보면 없고, 세션 안에서만
    # `git status`에 untracked 로 잡힌다. `git add -A` 한 번이면
    # .mcp.json/.gitconfig 같은 자격증명성 파일이 공개 레포에 커밋된다.
    # .muster-cache/ 와 같은 방식(워크스페이스 로컬 exclude)으로 막는다.
    lines += [".bashrc", ".bash_profile", ".profile", ".zshrc",
              ".zprofile", ".gitconfig", ".gitmodules", ".mcp.json",
              ".claude/", ".idea", ".vscode", ".ripgreprc"]
    skipped = lines
    try:
        ex.parent.mkdir(parents=True, exist_ok=True)
        existing = ex.read_text() if ex.exists() else ""
        missing = [ln for ln in lines if ln.rstrip("/") not in existing]
        skipped = missing
        if missing:
            with ex.open("a") as fh:
                for ln in missing:
                    fh.write(ln + "\n")
    except OSError as e:
        print(f"경고: 워크스페이스 {work} 의 자격증명 유출 방지 exclude 항목을 "
              f"쓰지 못했다 ({e}) — 빠진 항목: {', '.join(skipped)}",
              file=sys.stderr)
    subprocess.run(["git", "-C", str(work), "config", "credential.helper",
                    "!f() { echo username=x-access-token; echo password=$GH_TOKEN; }; f"],
                   capture_output=True, text=True)
    # clone 은 clone 시점 src 의 HEAD 를 origin/HEAD 로 물려받는다 — 방금
    # origin 을 실제 원격으로 바꿨으니 origin/HEAD 도 그 원격 기준으로
    # 다시 계산해야 `_base()`가 오염된 기본 브랜치를 읽지 않는다. `after=`
    # 로 넘겨서 fetch 가 fail-closed 로 halt 하더라도 먼저 시도되게 한다.
    _fetch_or_halt(str(work), "신규 워크스페이스", after=lambda: subprocess.run(
        ["git", "-C", str(work), "remote", "set-head", "origin", "-a"],
        capture_output=True, text=True))
    _write_role_sidecar(str(work), issue, role)
    return str(work)


def _recut_absorbed_branch(cwd: str, br: str):
    """`br` 이 이미 로컬에 체크아웃돼 있다고 가정하고, base 에 흡수됐는지
    검사해 필요하면 재컷한다 (untracked 작업은 stash 로 보존). 스폰 시점
    `checkout_issue_branch()` 와 세션 자신의 mid-run 재검사
    (`recut_if_absorbed_cli`, 이슈 #784) 양쪽에서 재사용하는 공유 헬퍼 —
    로직은 #732 가 이미 검증한 것 그대로, 호출 시점만 늘어난다.

    반환값은 최종 `git checkout`/`checkout -B` 의 CompletedProcess."""
    def git(*a):
        return subprocess.run(["git", "-C", cwd, *a], capture_output=True, text=True)
    base = _base(cwd)
    ahead = git("rev-list", "--count", f"{base}..{br}")
    remote_ahead = git("rev-list", "--count", f"{base}..origin/{br}")
    local_zero = ahead.returncode == 0 and ahead.stdout.strip() == "0"
    # 로컬은 0-ahead 라도 origin/br 이 base 보다 앞서 있으면, 이
    # 워크스페이스의 로컬 ref 가 그저 stale 한 것뿐이지 브랜치 자체가
    # base 에 흡수된 게 아니다 — 그 상태에서 base 로 재설정하면 다른
    # 워크스페이스가 이미 push 해 둔 커밋을 조용히 버린다 (이슈 #719).
    # remote_ahead 조회가 실패하면(원격 브랜치 없음 등) 로컬 판단만으로
    # 진행 — 오늘과 동일한 fail-open.
    remote_stale_only = (
        local_zero and remote_ahead.returncode == 0
        and remote_ahead.stdout.strip() != "0"
    )
    if remote_stale_only:
        print(f"[spawn] {br} 는 로컬만 {base} 에 흡수된 것처럼 보인다 — "
              f"origin/{br} 이 앞서 있어 재컷 대신 origin 을 따라간다.",
              file=sys.stderr)
        return git("checkout", "-B", br, f"origin/{br}")
    if local_zero:
        print(f"[spawn] {br} 는 {base} 에 완전히 흡수돼 커밋이 없다 — "
              f"로컬 브랜치를 지우고 새로 판다.", file=sys.stderr)
        # 흡수된 브랜치는 base 대비 영원히 0-ahead 라 재컷 없이는
        # 이 워크스페이스가 다시 PR 을 열 수 없다 (issue-732). 그런데
        # 워크스페이스에 untracked 파일만 있으면(커밋된 고유 작업은
        # 없음) `checkout -B` 가 그 파일들과 base 트리 사이의 경로
        # 충돌로 실패할 수 있어 조용히 no-op 재컷으로 빠진다. 재컷
        # 전에 untracked 파일을 stash 로 치워 뒀다가 재컷 뒤 새
        # 브랜치 위에 다시 풀어준다 — 절대 조용히 버리지 않는다.
        stash_marker = f"checkout_issue_branch-preserve-{br}"
        # 이전 실행이 push 와 pop 사이에서 중단됐다면 stash 가
        # working tree 에는 안 보이는 채로 남아있을 수 있다 (`git
        # status --porcelain` 은 stash 를 보지 않는다) — 그 상태로
        # clean 의 보존 가드를 통과하면 워크스페이스 전체가 지워지며
        # 안에 숨은 작업까지 조용히 사라진다. 재컷 전에 먼저 회수한다.
        leftover = git("stash", "list", "--grep", stash_marker)
        if leftover.returncode == 0 and leftover.stdout.strip():
            pop_r = git("stash", "pop", "-q")
            if pop_r.returncode != 0:
                print(f"[spawn] {br} 의 이전 실행이 남긴 stash 를 "
                      f"복구하지 못했다 — 수동 확인 필요: "
                      f"git -C {cwd} stash list", file=sys.stderr)
        untracked = git("ls-files", "--others", "--exclude-standard")
        has_untracked = (
            untracked.returncode == 0 and untracked.stdout.strip() != ""
        )
        if has_untracked:
            stash_r = git("stash", "push", "-u", "-q", "-m", stash_marker)
            has_untracked = stash_r.returncode == 0
        # -B 는 br 이 현재 체크아웃된 브랜치여도(재사용 워크스페이스가
        # 이미 그 위에 있는 경우) 지우지 않고 그대로 재설정한다 —
        # `branch -D` 는 체크아웃된 브랜치는 못 지운다.
        r = git("checkout", "-B", br, base)
        if r.returncode != 0:   # base 없음(원격 없음 등) — 현 HEAD 에서라도 재설정
            r = git("checkout", "-B", br)
        if has_untracked:
            pop_r = git("stash", "pop", "-q")
            if pop_r.returncode != 0:
                print(f"[spawn] {br} 재컷은 됐지만 보존해 둔 untracked "
                      f"작업을 자동으로 못 풀었다(충돌) — 수동 확인 "
                      f"필요: git -C {cwd} stash list / "
                      f"git -C {cwd} stash show -p", file=sys.stderr)
        return r
    return git("checkout", br)


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
    base = _base(cwd)
    subprocess.run(["git", "-C", cwd, "fetch", "-q", "origin",
                    base.removeprefix("origin/")],
                   capture_output=True, text=True)
    r = _recut_absorbed_branch(cwd, br)
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
    bootstrap_fetch_and_record_sha(cwd, "브랜치 체크아웃")
    _fetch_or_halt(cwd, "브랜치 체크아웃")
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
        r = _recut_absorbed_branch(cwd, br)
    elif git("rev-parse", "--verify", "-q", f"origin/{br}").returncode == 0:
        # rev-parse --verify -q br 는 로컬 ref 만 본다 — 워크스페이스가 새로
        # 클론된 직후라면 origin 에는 이미 있는 브랜치도 로컬엔 없어, 여기서
        # base 로 새로 파면 origin 의 기존 이력을 버리고 영구 분기한다
        # (실측: issue-235 phase 2). origin 전용이면 그걸 트래킹해 만든다.
        r = git("checkout", "-b", br, f"origin/{br}")
    else:
        base = _base(cwd)
        r = git("checkout", "-b", br, base)
        if r.returncode != 0:      # base 없음(원격 없음 등) — 현 HEAD 에서라도 만든다
            r = git("checkout", "-b", br)
    if r.returncode != 0:
        sys.exit(f"브랜치 {br} 로 못 갈아탔다: {r.stderr.strip()[:200]}")
    return br


def ensure_pushed(work: str, issue: int, role: str) -> dict:
    """세션이 남긴 커밋을 호스트 환경에서 push 하고, PR 이 없으면 연다.

    샌드박스의 GitHub egress 는 환경마다 다르게 막힌다(https 프록시 403,
    ssh-only 정책, 키링 불가시 등 — 전부 실측). 산출물이 로컬 커밋으로만
    남으면 보드에 존재하지 않는 것과 같으므로, on-the-record 가 세션 종료 후
    바깥에서 릴레이한다. 역할이 스스로 push/PR 에 성공했으면 전부 no-op.

    리턴은 `{"status": ..., "reason": <str|None>}` — status 는
    `nothing-to-push` / `pushed` / `push-rejected` / `pr-create-failed` /
    `pr-opened` / `pr-already-open`. 기존 stderr 프린트는 전부 그대로 두고
    (사람이 로그를 tail 할 때 보는 것은 안 바뀐다), 호출자가 원격의 거부
    사유를 이벤트/원장에 실을 수 있도록 구조화된 결과를 추가로 리턴한다
    (이슈 #301 B2).
    """
    br = f"issue-{issue}/{role}"
    def git(*a):
        # env=_git_env(): 이 클로저의 유일한 네트워크 호출은 아래 push 다 —
        # rev-parse/rev-list 는 로컬이라 영향 없다. push 도 _fetch_or_halt
        # 와 같은 원인(오케스트레이터 자신의 env 에 GH_TOKEN 이 없음)으로
        # 막힐 수 있다 — 이 함수 자체가 "샌드박스 egress 가 막히면 호스트
        # 에서 대신 push 한다"는 백업 경로인데, 그 백업 경로 자신이
        # 무인증으로 막히면 산출물이 로컬 커밋으로만 남는다.
        return _run_net(["git", "-C", work, *a], f"[{role}] 호스트 git",
                        env=_git_env())
    if git("rev-parse", "--verify", "-q", br).returncode != 0:
        return {"status": "nothing-to-push", "reason": None}
    ahead = git("rev-list", "--count", f"origin/{br}..{br}")
    unborn = ahead.returncode != 0          # 원격에 브랜치 자체가 없음
    n = ahead.stdout.strip() if ahead.returncode == 0 else "?"
    if unborn or n not in ("", "0"):
        r = git("push", "-q", "-u", "origin", br)
        if r.returncode != 0:
            reason = r.stderr.strip()[:200]
            print(f"[{role}] 호스트 push 실패: {reason}", file=sys.stderr)
            _post_stranded_push_comment(Path(work), issue, role, br,
                                        "push-failed", r.stderr.strip())
            return {"status": "push-rejected", "reason": reason}
        print(f"[{role}] 호스트에서 push 했다: {br}", file=sys.stderr)
    # "PR 있음" 판정은 OPEN 만 센다 — gh pr view <브랜치> 는 같은 브랜치의
    # 머지된 과거 PR(phase 1)도 잡아서, phase 2 의 새 PR 생성을 조용히
    # 건너뛰게 했다(실측: #60 머지 후 phase 2 커밋이 PR 없이 남았다).
    pr = subprocess.run(["gh", "pr", "list", "--head", br, "--state", "open",
                         "--json", "number", "--jq", "length"],
                        capture_output=True, text=True, cwd=work)
    has_open = pr.returncode == 0 and pr.stdout.strip() not in ("", "0")
    if not has_open:
        # 참조만 한다 — Closes 를 박으면 record PR 하나가 머지되는 순간
        # 이슈가 조기에 닫힌다(실측 직전 발견). 이슈 닫기는 라운드가 끝났을
        # 때 사람의 행위다 (계약 s8).
        body = (f"Part of #{issue}.\n\nOpened by on-the-record on behalf of the "
                f"{role} role session (sandbox egress relay); the branch "
                f"content is the role's own work.\n\nrole: {role}")
        c = subprocess.run(["gh", "pr", "create", "--head", br,
                            "--title", f"[{br}]",
                            "--body", body],
                           capture_output=True, text=True, cwd=work)
        if c.returncode == 0:
            print(f"[{role}] PR 을 열었다: {c.stdout.strip().splitlines()[-1] if c.stdout.strip() else br}",
                  file=sys.stderr)
            return {"status": "pr-opened", "reason": None}
        else:
            reason = c.stderr.strip()[:200]
            print(f"[{role}] PR 생성 실패: {reason}", file=sys.stderr)
            _post_stranded_push_comment(Path(work), issue, role, br,
                                        "pr-create-failed", c.stderr.strip())
            return {"status": "pr-create-failed", "reason": reason}
    return {"status": "pr-already-open", "reason": None}


def _session_log_path(cwd: str) -> Path:
    """이슈-스코프 세션 하나의 라이브 로그 경로 — 타임스탬프+PID 접미사로
    세대마다 고유하게 만든다 (이슈 #192). 같은 워크스페이스로 재스폰해도
    이전 세대의 로그(`<work>.session.<ts>.<pid>.log`)를 truncate-open 으로
    덮어쓰지 않는다. `ts` 는 `time.strftime` 이라 사전순 정렬이 생성 순서와
    일치한다."""
    ts = time.strftime("%Y%m%dT%H%M%S", time.localtime())
    return Path(str(cwd) + f".session.{ts}.{os.getpid()}.log")


def _spawn_claim_path(work: str) -> Path:
    return Path(str(work) + ".spawn-claim")


def _acquire_spawn_claim(work: str, issue: int, role: str) -> str | None:
    """(issue, role) 하나의 동시 스폰을 막는 O_CREAT|O_EXCL 클레임을 취득한다
    — 재스폰 경로의 `.respawn-claim-{ts}`(이슈 #132)와 같은 계열이지만,
    재시도-단위가 아니라 이 (issue,role) 자체가 생존해 있는 동안 유지되는
    클레임이라 pid 로 생존검사를 한다. 성공하면 None, 이미 살아있는 세션이
    쥐고 있으면 그 세션의 pid/시작시각을 담은 거부 사유 문자열을 리턴한다
    (이슈 #223 요구사항 3). 죽은 세션이 남긴 stale 클레임이면 정리하고 1회
    재시도한다(요구사항 2)."""
    claim_path = _spawn_claim_path(work)
    payload = json.dumps({"pid": os.getpid(), "ts": int(time.time())}).encode()
    for _ in range(2):
        # O_CREAT|O_EXCL 로 만들고 나서 내용을 쓰면, 만든 직후·쓰기 전 사이에
        # 다른 스레드/프로세스가 FileExistsError 를 잡고 내용을 읽어 빈
        # 파일을 "손상"으로 오판해 stale 정리로 방금 만든 클레임을 지워버릴
        # 수 있다(TOCTOU, 로컬에서 실측: 스레드 두 개 재현 시 간헐적으로 둘
        # 다 통과). 임시 파일에 내용을 먼저 다 쓴 뒤 `os.link()`로 옮기면
        # link 자체가 원자적 존재-검사+생성이라 이 창이 없다.
        tmp_fd, tmp_name = tempfile.mkstemp(dir=str(claim_path.parent),
                                            prefix=claim_path.name + ".tmp")
        try:
            with os.fdopen(tmp_fd, "wb") as f:
                f.write(payload)
            try:
                os.link(tmp_name, str(claim_path))
                return None
            except FileExistsError:
                pass
        finally:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass
        try:
            existing = json.loads(claim_path.read_text())
        except (OSError, ValueError):
            existing = {}
        pid = existing.get("pid")
        if isinstance(pid, int) and _alive(pid):
            return (f"issue-{issue}/{role}: 이미 세션(pid {pid}, 시작 ts "
                    f"{existing.get('ts')})이 이 (issue,role) 스폰 클레임을 "
                    f"쥐고 있다 — 거부")
        try:
            claim_path.unlink()
        except FileNotFoundError:
            pass
    return f"issue-{issue}/{role}: 스폰 클레임 취득 실패(재시도 소진)"


def _rewrite_spawn_claim_pid(work: str) -> None:
    """fork 직후 자식 분기에서 클레임의 pid 를 자기 자신(자식)으로 재기록한다.
    클레임을 fork 전 pid(곧 죽는 부모)로 남겨 두면, 부모가 죽는 순간 생존검사
    (`_alive`)가 stale 로 오판한다 — 실제로는 자식이 세션을 계속 몰고 있는데도
    (이슈 #223 착수 프롬프트가 지목한 함정, 로컬 독립 검증에서 실측).
    `Path.write_text()`(truncate 후 쓰기)는 다른 프로세스가 그 사이 빈 파일을
    읽어 손상으로 오판하는 창을 새로 연다 — `_acquire_spawn_claim`이 이미
    피한 바로 그 TOCTOU(hunt 발견). 임시 파일에 다 쓴 뒤 `os.replace()`로
    교체해 그 창을 없앤다."""
    claim_path = _spawn_claim_path(work)
    try:
        existing = json.loads(claim_path.read_text())
    except (OSError, ValueError):
        return
    existing["pid"] = os.getpid()
    tmp_fd, tmp_name = tempfile.mkstemp(dir=str(claim_path.parent),
                                        prefix=claim_path.name + ".tmp")
    with os.fdopen(tmp_fd, "w") as f:
        json.dump(existing, f)
    os.replace(tmp_name, str(claim_path))


def _release_spawn_claim(work: str, pid: int) -> None:
    """스폰 클레임을 해제한다 — 취득 이후 다른 프로세스가 stale-정리로 같은
    경로를 재취득했을 수 있으므로, 지금 쥔 pid 가 여전히 우리 자신일 때만
    지운다."""
    claim_path = _spawn_claim_path(work)
    try:
        existing = json.loads(claim_path.read_text())
    except (OSError, ValueError):
        return
    if existing.get("pid") == pid:
        try:
            claim_path.unlink()
        except FileNotFoundError:
            pass


_ACCEPTANCE_CHECK_LINE = re.compile(r"^\s*-\s*check\s*:\s*(.+)$", re.MULTILINE)


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
    sys.path.insert(0, str((ROOT / "gates").resolve()))
    import acceptance_gate as _acceptance_gate
    section = _acceptance_gate._acceptance_section(body)
    if section is None:
        return ""
    checks = [c.strip() for c in _ACCEPTANCE_CHECK_LINE.findall(section)]
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


# 이슈 #1978: directive.sh(tokenmaxxxer-core, contract v3 s19a)가 매
# 세션에 SessionStart 로 이미 내보내는 "Build-now bypass" 불릿을 그대로
# 미러링한다(제안서 Rationale: 새 문구를 지어내면 두 서술이 계약 개정마다
# 따로 드리프트한다) — 2인칭 "your issue" 프레이밍만 스폰-시점 프리픽스로
# 조정했을 뿐, 문장 자체는 바꾸지 않는다.
_SINGLE_PHASE_CONTRACT_LINE = (
    "- Build-now bypass (contract v3 s19a): when the task that spawned this "
    "session explicitly authorizes delivery-only — its environment carries "
    "CORE_BUILD_NOW=1, set by the spawner, never by you — skip the proposal "
    "round and deliver directly: build on issue-<n>/{role}, commit code and "
    "your record, and open one PR carrying the work. Without "
    "CORE_BUILD_NOW=1 the default two-phase flow is unchanged; a session "
    "cannot grant itself this bypass by setting the variable on its own.\n"
)

_SKILL_USE_SENTENCE_RE = re.compile(r"(Use\b[^.]*\.)", re.S)


def _skill_trigger_line(skill_dir: Path) -> str | None:
    """`skill_dir/SKILL.md` 프론트매터의 `description:` 필드에서 "Use ..."로
    시작하는 트리거 문장을 뽑는다. 파일/프론트매터/description/트리거 문장
    중 무엇이든 없으면 None — 예외를 던지지 않는다(호출부가 이름만이라도
    싣는 empty-state 처리를 하도록).

    폴딩 블록 스칼라(`description: >-`)를 포함해 여러 줄 description 을
    다루려면 전체 YAML 파서가 필요하지만, 이 함수가 필요한 건 딱 한
    문장뿐이라(제안서 Rationale) 프론트매터 블록만 떼어내 정규식으로
    훑는다."""
    md = skill_dir / "SKILL.md"
    try:
        text = md.read_text(encoding="utf-8")
    except OSError:
        return None
    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not fm:
        return None
    dm = re.search(r"(?m)^description:[ \t]*(.*(?:\n(?:[ \t]+.*)?)*)", fm.group(1))
    if not dm:
        return None
    desc = dm.group(1).strip()
    desc = desc.lstrip(">|-+").strip()
    desc = desc.strip("\"'")
    desc = re.sub(r"\s+", " ", desc)
    um = _SKILL_USE_SENTENCE_RE.search(desc)
    return um.group(1).strip() if um else None


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset({"a", "the", "use", "when", "or", "and", "is", "an"})
# 이슈 #2040: raw-overlap 시절의 고정 임계값(_CROSS_FAMILY_MIN_OVERLAP=2)은
# BM25 점수 스케일로 옮겨오지 않는다 — score > 0 (질의-문서 토큰이 하나라도
# 겹치면 IDF 가중치가 붙어 양수) 를 바닥으로 쓴다. 재현: 16쌍 리플레이에서
# conformance-review-severity-classification 이 16/16 -> 7/16 로, model-routing
# 은 5/16 -> 5/16 로 남았다(docs/issue-2040/reports/implementation/survey.md
# BM25 spike, floor=score>0 그대로 재사용) — 그 잔여 오탐(모두 model-routing
# 류의 "의도적으로 광범위한" 트리거)을 걷어내는 건 임계값 조정이 아니라
# consult-judge 단계의 몫이다(제안서 Rationale).
_BM25_K1 = 1.5
_BM25_B = 0.75
_CROSS_FAMILY_CONSULT_TOPN = 8  # 이슈 본문: consult 에 넘기는 BM25 상위 후보 수


def _tokenize(text: str) -> set[str]:
    """소문자화 + 비영숫자 분리 + 작은 불용어 목록 제거. "Use when" 처럼
    트리거 문장이면 어디에나 있는 일반 단어가 그 자체로 매치를 만들지
    않게 한다(제안서 What will be done)."""
    return {t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS}


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
    family_names = set(_ROLE_SKILLS.get(role, []))
    matches: dict[str, list[tuple[str, Path]]] = {}

    def add(source: str, name: str, d: Path) -> None:
        if (d / "hooks").is_dir():
            return
        matches.setdefault(name, []).append((source, d))

    if repo_root is not None and repo_root.is_dir():
        for name, d in _local_skill_dirs(repo_root).items():
            add("skill-repo", name, d)
    for name, entries in _installed_plugin_skill_dirs().items():
        for _qualifier, d, _version in entries:
            add("plugin", name, d)
    if home is not None:
        for name, d in _local_skill_dirs(home / ".claude" / "skills").items():
            add("local-user", name, d)
    if target_repo_root is not None:
        for name, d in _local_skill_dirs(target_repo_root / ".claude" / "skills").items():
            add("local-repo", name, d)

    corpus: list[tuple[str, Path, str]] = []
    for name, ms in matches.items():
        if name in family_names:
            continue
        if len(ms) > 1 and len({_skill_content_hash(d) for _, d in ms}) == 1:
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


def _bm25_cross_family_scores(task_text: str, role: str,
                               repo_root: Path | None,
                               home: Path | None = None,
                               target_repo_root: Path | None = None
                               ) -> list[tuple[float, str, Path, str]]:
    """`task_text` 를 질의로, 역할의 family 밖 스킬 각각의 "Use ..." 트리거
    문장을 문서로 삼아 Okapi BM25(k1=1.5, b=0.75, 표준 기본값)로 채점한다
    — 트리거 문장은 집합으로 토큰화되므로 문서 내 항 빈도(f)는 항상 1
    (존재/부재만 본다, 트리거 문장 반복 서술 여부에 좌우되지 않기 위함).
    score > 0(질의와 최소 한 토큰 겹침) 인 것만 이름 오름차순 타이브레이크로
    내림차순 정렬해 돌려준다 — floor 근거는 위 상수 주석.

    이슈 #2055: 후보 코퍼스는 `_cross_family_candidate_corpus()` 가 네 소스에
    걸쳐 해석한다 — 각 행이 source 라벨을 달고 나온다(반환 튜플의 4번째
    자리). `home`/`target_repo_root` 를 생략하면(오늘의 호출부 호환)
    각각 `Path.home()`, 빈 tier 로 취급된다."""
    query_tokens = _tokenize(task_text)
    if not query_tokens:
        return []
    corpus = _cross_family_candidate_corpus(role, repo_root, home, target_repo_root)
    docs: list[tuple[str, Path, str, set[str]]] = []
    for name, d, source in corpus:
        trigger = _skill_trigger_line(d)
        if not trigger:
            continue
        docs.append((name, d, source, _tokenize(trigger)))
    if not docs:
        return []
    n = len(docs)
    avgdl = sum(len(toks) for _, _, _, toks in docs) / n
    df: dict[str, int] = {}
    for _, _, _, toks in docs:
        for t in toks:
            df[t] = df.get(t, 0) + 1
    scored: list[tuple[float, str, Path, str]] = []
    for name, d, source, toks in docs:
        dl = len(toks) or 1
        score = 0.0
        for t in query_tokens:
            if t not in toks:
                continue
            idf = math.log((n - df[t] + 0.5) / (df[t] + 0.5) + 1)
            score += idf * (_BM25_K1 + 1) / (1 + _BM25_K1 * (1 - _BM25_B + _BM25_B * dl / avgdl))
        if score > 0:
            scored.append((score, name, d, source))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return scored


def _cross_family_skill_matches(task_text: str, role: str,
                                 repo_root: Path | None,
                                 k: int = 2,
                                 home: Path | None = None,
                                 target_repo_root: Path | None = None) -> list[Path]:
    """BM25 프리필터의 상위 k 개(이슈 #2040 — 예전 raw-overlap 채점을
    대체, 호출부/시그니처는 그대로다). consult-judge 단계 없이 이 함수
    단독으로도 오늘의 fail-open 경로(자문 에러시 이 함수의 top-k)와
    동일한 모양을 낸다."""
    scored = _bm25_cross_family_scores(task_text, role, repo_root, home, target_repo_root)
    return [d for _, _, d, _ in scored[:k]]


def _spawn_one(cwd: str, role: str, task: str, unattended: bool,
               issue: int | None = None, bounded: bool = False,
               stall_timeout_min: float = 5.0, no_wait: bool = False,
               despite_returned: bool = False, model: str | None = None,
               skills: str | None = None, single_phase: bool = False) -> int:
    """역할 하나를 띄우고, 무슨 일이 있었는지 원장에 남기고, 처분을 말한다.

    main() 과 drive() 가 같은 몸통을 쓴다 — 드라이버가 따로 스폰 경로를 들고
    있으면 둘이 갈라지고, 갈라진 쪽이 조용히 게이트 하나를 빠뜨린다.
    """
    spec = json.loads((ROOT / "roles" / f"{role}.json").read_text())
    _BOOTSTRAP_TIMING.clear()
    # 이슈 #2001: 크로스-패밀리 스코어링은 이 함수가 받은 원본 task 텍스트를
    # 대상으로 한다 — 아래에서 task 에 여러 안내 문단이 계속 덧붙는데, 그
    # 덧붙은 텍스트(스킬 목록 자체 등)가 스코어링 입력에 섞이면 결정론이
    # 스폰마다 달라진다.
    _cross_family_task_text = task
    cross_family_dirs: list[Path] = []
    # 이슈 #1742/#1774: --skills 이름 검증(네 소스 모두)은 워크스페이스/
    # 브랜치를 건드리기 전에 끝난다(fail-closed, 요구사항 2) — 아래
    # 워크스페이스 생성보다 먼저 온다.
    skill_sources = resolved_skill_sources(skills, _skill_repo_root(),
                                            target_repo_root=Path(cwd))
    skill_dirs = [m["dir"] for m in skill_sources]
    # 오늘 shape 과 맞추기 위한 flat sha: 전부 skill-repo 매치일 때만 채운다
    # (요구사항: skill-repo-only 조합은 오늘의 skills/skills_sha shape 를
    # 그대로 유지한다) — 그 외 조합은 skills_detail 의 per-skill 소스로만
    # 표현되고 이 flat 필드는 None.
    skill_sha = (skill_sources[0]["sha"]
                 if skill_sources and all(m["source"] == "skill-repo"
                                           for m in skill_sources)
                 else None)
    # 이슈 #1955(이슈 #1758 phase 5 이행): skill-repository 해석도 같은
    # 이유로 워크스페이스/브랜치 생성보다 먼저 온다 — 역할이 매핑한 스킬
    # 이름이 모르는 이름이거나 hooks/ 를 들고 있으면 여기서 fail-closed.
    role_source = resolve_role_source(role, _skill_repo_root())
    # 이슈 #2061: skill_judge 자문(BM25 프리필터 + haiku 판단)을 워크스페이스
    # 클론/브랜치 체크아웃(~12s)과 겹치도록 그 전에 먼저 던진다 — 아래
    # "cross_family" 단계에서 join 만 한다. 자문은 읽기 전용(저장소 파일을
    # 건드리지 않는다, `_skill_judge_consult()` 의 override 문구)이라
    # 워크스페이스가 아직 없어도(원본 cwd 로) 안전하게 먼저 돌 수 있다.
    _cross_family_executor: concurrent.futures.ThreadPoolExecutor | None = None
    _cross_family_future = None
    if issue is not None and role_source["source"] == "skill-repo":
        _cross_family_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        _cross_family_future = _cross_family_executor.submit(
            _cross_family_skill_matches_with_consult,
            _cross_family_task_text, role, _skill_repo_root(), issue, cwd,
            home=Path.home(), target_repo_root=Path(cwd))
    if issue is not None:
        root = Path(cwd).resolve()
        # 이슈 #1239: #680 의 거절 게이트를 무조건적 surfacing 으로 대체한다
        # — 처분 안 된 PR 이 있어도 스폰은 결코 막지 않는다(북극-요구#1,
        # never-missed != never-spawn). `--despite-returned` 는 이제 아무
        # 것도 바꾸지 않는 no-op (CLI 호환성 보존, deprecation 안내만 찍는다).
        blockers, ok = _undispositioned_role_prs(root, exclude_issue=issue)
        if not ok:
            print(f"[{role}] returned-PR 게이트: gh 조회 실패 — fail-open 으로 "
                  f"통과시킨다 (이슈 #680)", file=sys.stderr)
            ledger_write({"event": "returned_pr_gate_fail_open", "role": role,
                          "issue": issue, "ts": int(time.time())})
        else:
            _print_returned_pr_surfaced(blockers, source="spawn")
        if despite_returned:
            print(f"[{role}] --despite-returned 는 더 이상 아무 효과가 없다 "
                  f"(deprecated, 이슈 #1239) — 게이트가 항상 non-blocking "
                  f"surfacing 이라 무시할 거절이 없다", file=sys.stderr)
        # 이슈 #1179: 워크스페이스 하나 더 만들기 전에 먼저 안전하게
        # 쓸어낸다(spawn-time sweep) — 정리는 사람이 `spawn.py clean` 을
        # 기억해야만 도는 게 아니라 기본으로 켜져 있어야 한다(northpole
        # req#7). 스윕 실패가 스폰 자체를 막으면 안 되므로 예외를 삼킨다.
        if _clean_auto_enabled():
            try:
                auto_sweep(_workspace_base(), _clean_max_age_days(),
                           _clean_max_bytes())
            except Exception as ex:
                print(f"[{role}] auto-sweep 실패(스폰은 계속): {ex}",
                      file=sys.stderr)
        # 격리 작업 클론에서 돈다 — 사용자의 체크아웃은 건드리지 않고,
        # 동시 스폰들이 서로의 index/브랜치를 밟지 않는다.
        with _timed("workspace"):
            cwd = issue_workspace(cwd, issue, role)
        claim_rejection = _acquire_spawn_claim(cwd, issue, role)
        if claim_rejection is not None:
            print(f"[{role}] {claim_rejection}", file=sys.stderr)
            return 1
        with _timed("branch"):
            br = checkout_issue_branch(cwd, issue, role)
        print(f"[{role}] 격리 작업 디렉토리: {cwd}  (브랜치 {br})", file=sys.stderr)
        # 원본(프리픽스 붙기 전) 맡길 일을 한 번만 저장 — 재스폰(다른 spawn.py
        # 프로세스일 수 있다)이 이걸 읽어 그대로 넘기면, 아래에서 프리픽스를
        # 다시 붙여도 중복되지 않는다 (이슈 #132).
        task_path = Path(str(cwd) + ".task.txt")
        if not task_path.exists():
            task_path.write_text(task, encoding="utf-8")
        # issue #1017 (northpole req#6): 이슈가 인용하는 요구 ID를 스폰
        # 텍스트에 그대로 실어, 스폰된 역할 세션이 첫 턴부터 어느 요구를
        # 섬기는지 안다. gh 조회 실패는 조용히 건너뛴다 — 이 줄이 없다고
        # 스폰 자체를 막을 이유는 없다(require_requirement_linkage 가 이미
        # phase-1 드래프트 시점에 구조적으로 막는다).
        req_line = ""
        goal_pin = ""
        body = None
        _design_artifacts_gate = None
        try:
            sys.path.insert(0, str((ROOT / "gates").resolve()))
            import gh_rest as _gh_rest
            import requirement_linkage as _requirement_linkage
            import design_artifacts_gate as _design_artifacts_gate
            issue_data = _gh_rest.fetch_issue(Path(cwd), issue)
            body = issue_data.get("body") if issue_data else None
            title = issue_data.get("title") if issue_data else None
            if body is not None:
                req_ids = _requirement_linkage.cited_requirement_ids(body)
                if req_ids:
                    req_line = f"이 이슈가 인용하는 요구: {', '.join(req_ids)}\n"
                goal_pin = _goal_pin_block(title, body)
        except Exception:
            req_line = ""
            goal_pin = ""
        task = (f"당신의 이슈: #{issue} (subject issue-{issue}, 브랜치 {br}).\n"
                + req_line + goal_pin +
                f"gh issue view {issue} 로 이슈를 먼저 읽어라.\n"
                f"완료의 정의: 변경이 이 브랜치에 **커밋**되고 push 되어 PR 로\n"
                f"제출된 상태다. 미커밋 변경은 존재하지 않는 것과 같다 —\n"
                f"세션을 끝내기 전에 반드시 커밋하라. push/PR 이 네트워크로\n"
                f"막히면 커밋까지는 해 둬라: on-the-record 가 밖에서 릴레이한다.\n"
                f"체크포인트 커밋: 길거나 백그라운드로 넘기는 검증을 시작하기\n"
                f"전에 먼저 체크포인트 커밋을 해 두고, 검증이 끝난 뒤 amend 하거나\n"
                f"후속 커밋을 추가하라 — 검증부터 하고 나중에 커밋하는 습관은\n"
                f"세션이 검증 도중 끊길 때 미커밋 변경을 그대로 좌초시킨다.\n"
                f"경고: 이 턴은 headless 이고 단발이다 — 세션이 끝나면 이 프로세스도\n"
                f"끝난다. run_in_background 로 넘긴 작업은 부모 턴이 끝나는 순간 함께\n"
                f"죽는다(백그라운드 워커가 커밋·push 를 대신 끝내줄 것이라고 가정하지\n"
                f"마라 — 실측된 실패 패턴이다). 모든 작업은 이 턴 안에서 직접 끝내라.\n\n") + task
        # 이슈 #1978 (A): --single-phase 신호가 없으면 이 블록은 아무 것도
        # 안 붙인다 — 오늘의 프롬프트와 바이트 단위로 동일해야 한다는
        # 제안서 제약. B(스킬 트리거 줄)보다 먼저 온다(A before B, 제안서
        # 순서).
        if single_phase:
            task = task + "\n\n" + _SINGLE_PHASE_CONTRACT_LINE.format(role=role)
        if skill_sources:
            skill_lines = ", ".join(
                f"{m['name']}"
                + (f" — {_skill_trigger_line(m['dir'])}"
                   if _skill_trigger_line(m['dir']) else "")
                + f" ({_describe_skill_match(m)})"
                for m in skill_sources)
            task = task + (
                f"\n\n마운트된 스킬(--skills, 이슈 #1742/#1774): {skill_lines}\n")
        if role_source["source"] == "skill-repo":
            # 이슈 #1978 (B): 스킬 이름 옆에 SKILL.md 의 "Use ..." 트리거
            # 문장을 인라인한다(#1960 의 1/9 발화율 넛지를 대체) — 트리거
            # 문장이 없는 스킬도 이름은 절대 빠뜨리지 않는다(empty-state
            # 요구).
            # 이슈 #2001/#2040: family 밖 top-K(K=2) 크로스-패밀리 스킬을
            # add-only 로 얹는다 — 매치가 없으면 cross_family_dirs 는 빈
            # 목록이라 아래 줄들은 오늘과 바이트 단위로 동일하게 남는다.
            # 이슈 #2040: BM25 프리필터 + skill_judge 자문 판단(스폰당
            # 최대 자문 1회) — 소요 시간은 "cross_family" 단계로 측정해
            # 부트스트랩 타이밍 요약에 실린다(Acceptance: per-spawn latency).
            with _timed("cross_family"):
                # 이슈 #2061: 위에서 워크스페이스/브랜치 셋업보다 먼저 던져둔
                # 자문을 여기서 join 만 한다 — 이 단계의 측정치는 이제 겹친
                # 대기 시간이 아니라 순수 join 대기(자문이 셋업보다 오래
                # 걸린 나머지)만 반영한다.
                cross_family_dirs = (_cross_family_future.result()
                                     if _cross_family_future is not None else [])
                if _cross_family_executor is not None:
                    _cross_family_executor.shutdown(wait=False)
            role_skill_lines = ", ".join(
                d.name + (f" — {_skill_trigger_line(d)}" if _skill_trigger_line(d) else "")
                for d in role_source["skill_dirs"]
            ) if role_source["skill_dirs"] else ", ".join(role_source["skills"])
            if cross_family_dirs:
                cross_family_lines = ", ".join(
                    d.name + (f" — {_skill_trigger_line(d)}" if _skill_trigger_line(d) else "")
                    for d in cross_family_dirs)
                role_skill_lines = (role_skill_lines + ", " + cross_family_lines
                                     if role_skill_lines else cross_family_lines)
                cross_family_clause = (
                    f" (이 중 {', '.join(d.name for d in cross_family_dirs)} 는 "
                    f"이번 과제 텍스트와의 키워드 매치로 추가된 크로스-패밀리 "
                    f"스킬 — 이슈 #2001)")
            else:
                cross_family_clause = ""
            task = task + (
                f"\n\n이 역할은 skill-repository(이슈 #1955, #1758)로 매핑됐다: "
                f"스킬 {role_skill_lines} "
                f"(skill-repository {role_source['skill_sha']}) 가이던스만 붙는다 — "
                f"집행은 core 훅뿐이다.{cross_family_clause}\n")
        # 이슈 #1960 phase B: 마운트된 스킬이 하나라도 있으면(--skills 든
        # 역할 매핑이든) 실체 작업을 시작하기 전에 그 목록을 이번 과제와
        # 대조해보라고 스폰 시점에 못박는다. 베이스라인 측정
        # (docs/issue-1960/reports/execution-observation/baseline-measurement.md)
        # 이 relevance-gated 세션 38개 전부에서 Skill 호출 0건을 보였다 —
        # 스킬이 안 맞아서가 아니라 애초에 호출을 고려하지 않는 구조적
        # 공백이라는 뜻이라, trigger 문구를 손보는 대신 이 지시문 한 줄을
        # 추가한다(단일 변경, 순차 적용).
        if skill_sources or role_source["skills"]:
            task = task + (
                "\n\n스킬 점검(이슈 #1960): 실체 작업을 시작하기 전에, 위에 "
                "마운트된 스킬 목록을 이번 과제와 대조하라. trigger 조건이 "
                "이번 과제에 그럴듯하게 들어맞는 스킬이 있으면 Skill 도구로 "
                "호출하고, 없으면 검토했다는 사실만 유념하고 넘어가라.\n")
            # 이슈 #2039: 마운트된 스킬 하나마다 레코드에 한 줄씩 verdict를
            # 남겨야 한다 — 스킬을 조용히 무시하는 걸 불가능하게 만든다.
            # 스킬이 하나도 안 마운트되면 이 블록 전체가 안 붙으므로
            # (위 조건과 동일), 무-스킬 세션은 오늘과 바이트 단위로 같다.
            task = task + (
                "\n\n스킬-verdict 의무(이슈 #2039): 위에 마운트된 스킬 "
                "이름마다, 레코드에 `skill-verdict: <스킬명> — applied: "
                "<어디서/어떻게> | not-applicable: <한 줄 이유>` 형태의 줄을 "
                "정확히 하나씩 남겨야 한다 — 적용 여부 판단은 전적으로 이 "
                "세션의 몫이지만, 그 판단을 아예 안 밝히는 것은 더 이상 "
                "허용되지 않는다.\n")
        # 이슈 #2014 (artifact-gate phase 3): `design-artifacts:` 선언이
        # 있으면 선언된 각 아티팩트 경로를, 그 basename 이 마운트된 스킬들의
        # 트리거 문장과 가장 많이 겹치는 스킬 하나와 짝지어 한 줄씩 붙인다
        # (#2013 parse_declaration + #1978B/#2001 tokenize/trigger 재사용,
        # 새 fetch 없음 — body 는 spawn.py:8085 에서 이미 받았다). 태그가
        # 없거나(parse_declaration 이 None) 어떤 아티팩트도 마운트된
        # 스킬과 겹치지 않으면 이 블록은 아무 것도 안 붙인다(제안서
        # Constraints — byte-identical on absence).
        declared_artifacts = _design_artifacts_gate.parse_declaration(body) \
            if body is not None and _design_artifacts_gate is not None else None
        if declared_artifacts:
            artifact_all_dirs = list(skill_dirs) + [
                d for d in role_source["skill_dirs"] if d not in skill_dirs]
            artifact_all_dirs = artifact_all_dirs + [
                d for d in cross_family_dirs if d not in artifact_all_dirs]
            pairing_lines = []
            for artifact_path in declared_artifacts:
                basename = Path(artifact_path).stem
                artifact_tokens = _tokenize(basename)
                if not artifact_tokens:
                    continue
                scored: list[tuple[int, str, Path]] = []
                for d in artifact_all_dirs:
                    trigger = _skill_trigger_line(d)
                    if not trigger:
                        continue
                    overlap = len(artifact_tokens & _tokenize(trigger))
                    if overlap > 0:
                        scored.append((overlap, d.name, d))
                if not scored:
                    continue
                scored.sort(key=lambda t: (-t[0], t[1]))
                _, best_name, best_dir = scored[0]
                pairing_lines.append(
                    f"{artifact_path} ↔ {best_name} — {_skill_trigger_line(best_dir)}")
            if pairing_lines:
                task = task + (
                    "\n\n아티팩트-스킬 짝짓기(이슈 #2014): 선언된 각 아티팩트를 "
                    "그것을 만드는 절차를 담은 스킬과 짝지었다.\n"
                    + "\n".join(pairing_lines) + "\n")
    # 이슈 #1955: 역할은 룰북을 아예 마운트하지 않는다 — rulebook 해석
    # 경로 자체가 은퇴했다(요구사항: 룰북 마운트가 "붙었지만 무시됨"이
    # 아니라 argv 에서 통째로 빠져야 한다는 #1758 요구사항 2를 무조건화).
    plugins: list[Path] = []
    # core_plugin_dirs() 를 print 보다 먼저 불러 core_root() 의 관리 클론
    # pull 이 먼저 일어나게 한다 — 순서가 뒤집히면(예전처럼 print 뒤에서
    # 부르면) 로그에는 pull 전 sha, ledger 에는 pull 후 sha 가 찍혀 같은
    # run 안에서 두 기록이 어긋난다.
    with _timed("core"):
        core_plugins = core_plugin_dirs()
    with _timed("settings"):
        s = role_settings(role, cwd)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(s, f)
            settings = f.name
    # --skills(#1742)와 역할 매핑 스킬(#1758/#1955)은 additive — 같은
    # --plugin-dir 마운트 목록에 합쳐 붙인다.
    all_skill_dirs = list(skill_dirs) + [d for d in role_source["skill_dirs"]
                                          if d not in skill_dirs]
    all_skill_dirs = all_skill_dirs + [d for d in cross_family_dirs
                                        if d not in all_skill_dirs]
    try:
        rulebook_desc = "skill-repo(이슈 #1955)"
        roster_resolution_fields = _role_source_roster_fields(role_source)
        print(f"[{role}] 플러그인 {len(plugins)}개, 룰북 {rulebook_desc}, "
              f"core 플러그인 {', '.join(p.name for p in core_plugins)}, "
              f"core {core_version()}, 작업 디렉터리 {cwd}", file=sys.stderr)
        print(_bootstrap_timing_line(role), file=sys.stderr)
        # 맡길 일은 stdin 으로 넘긴다. 인자로 주면 가변 인자 플래그가 삼키고,
        # 셸 보간을 거치면 신뢰할 수 없는 값의 $(…) 가 실행된다.
        cmd, extra_env = spawn_cmd(settings, role, unattended,
                                   core_plugins, plugins, model,
                                   all_skill_dirs,
                                   skill_sha or role_source["skill_sha"])
        # 이슈 #1978 (A): --single-phase 신호일 때만 얹는다 — 없으면
        # extra_env 는 오늘과 바이트 단위로 동일한 채로 남는다.
        if single_phase:
            extra_env["CORE_BUILD_NOW"] = "1"
        if issue is not None:
            # 툴체인 캐시를 워크스페이스 안으로 — go 등이 홈(~/Library/...)에
            # 캐시·설정을 쓰려다 샌드박스에 막혀 빌드가 승인 프롬프트로
            # 빠졌다(실측: phase 2 가 go build 를 한 번도 못 돌림). 쓰기가
            # 전부 cwd 아래로 오면 샌드박스 안에서 승인 없이 돈다.
            wcache = os.path.join(cwd, ".muster-cache")
            extra_env.update({
                "GOCACHE": os.path.join(wcache, "go-build"),
                "GOMODCACHE": os.path.join(wcache, "gomod"),
                "GOENV": os.path.join(wcache, "goenv"),
                "GOPATH": os.path.join(wcache, "gopath"),
                "XDG_CACHE_HOME": os.path.join(wcache, "xdg"),
                "npm_config_cache": os.path.join(wcache, "npm"),
                "PIP_CACHE_DIR": os.path.join(wcache, "pip"),
                "CARGO_HOME": os.path.join(wcache, "cargo"),
            })
        before = board_snapshot(cwd)
        before_head = _git_head(cwd) if issue is not None else None
        t0 = time.monotonic()
        # stream-json 을 줄 단위로 받아 라이브 로그에 tee 한다 — "지금 뭐
        # 하는 중인가"가 세션이 끝나기 전에도 보이게. 최종 result 이벤트가
        # 옛 --output-format json 의 결과 오브젝트와 같은 필드를 든다.
        log_path = (_session_log_path(cwd) if issue is not None
                    else ROOT / "runs" / "last-session.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[{role}] 라이브 로그: {log_path}", file=sys.stderr)
        result = {}
        roster_key = f"issue-{issue}/{role}" if issue is not None else f"adhoc/{role}/{os.getpid()}"
        events_path = _events_path(cwd)
        offset_path = _offset_path(cwd)
        is_parent_return = False
        if bounded and issue is not None:
            _workspace_index_put(issue, role, str(cwd), str(log_path))
            # 부모(호출한 CLI 콜)는 이벤트 하나 또는 stall 시간까지만 기다리고
            # 리턴한다 — 자식이 세션을 끝까지 몰고 간다 (이슈 #114). setsid 로
            # 자식을 새 세션에 놓아, 부모가 속한 프로세스 그룹에 신호가 가도
            # 자식은 안 죽는다. settings 임시파일은 자식이 아직 쓰는 중이라
            # 부모 쪽 finally 에서 지우면 안 된다 (is_parent_return 이 막는다).
            #
            # 기다리기 전에 offset 을 지금의 파일 끝으로 민다. events.jsonl 은
            # append-only 이고 같은 워크스페이스로 재스폰하면 이전 세션의 줄이
            # 그대로 남아 있어서, offset 이 그 앞을 가리키면 새 스폰이 **과거
            # 이벤트**로 즉시 리턴한다 — 세션은 계속 도는데 호출자는 끝났다고
            # 듣는다. 실측 2026-07-30(core issue-53 phase 2): 78분 전 phase 1 이
            # 남긴 pr-opened 로 복귀했다. 이 스폰이 소비할 수 있는 것은 이
            # 세션이 낸 이벤트뿐이어야 한다 (이슈 #142).
            _write_offset(offset_path, _event_count(events_path))
            child_pid = os.fork()
            if child_pid == 0:
                # 이슈 #908: fork-child 설정(setsid/dup2)과 Popen() 은 첫
                # roster_register/session-start (아래, Popen 뒤) 이전에
                # 실행된다 — 그 구간에서 죽으면(SIGKILL/segfault 포함, 예외를
                # 던지지 않는 죽음도) roster_watchdog() 은 등록된 엔트리만
                # 스캔하므로 구조적으로 못 본다(실측: #895/#907, 흔적 없는
                # 사망). 이 구간에 들어가기 전에 자신의 pid 로 로스터 스텁과
                # 이른 session-start 를 먼저 남겨, 어떻게 죽든
                # roster_watchdog() 의 기존 dead-entry 경로가 이 엔트리를
                # 보게 한다. try/except 는 죽음 자체를 잡는 게 아니라(신호로
                # 죽으면 못 잡는다) 사람이 읽을 spawn-death 이벤트를 남기는
                # 용도로만 아래에서 덧붙인다.
                _early_roster_entry = {
                    "pid": os.getpid(), "role": role,
                    "issue": issue, "ts": int(time.time()),
                    "work": str(cwd), "log": str(log_path),
                    "expects_pr": issue is not None,
                    "session_id": os.environ.get(ORCHESTRATOR_SESSION_ID_ENV) or None,
                    "before_head": before_head,
                    "wrapper_pid": os.getpid(),
                }
                _early_roster_entry.update(_skill_roster_fields(skill_sources, skill_sha))
                _early_roster_entry.update(roster_resolution_fields)
                roster_register(roster_key, _early_roster_entry)
                _append_event(events_path, "session-start",
                              {"pid": os.getpid(), "ts": time.time()})
            if child_pid > 0:
                is_parent_return = True
                # 이슈 #488: watch 는 여태 사람/오케스트레이터가 스폰마다 따로
                # 재무장해야 하는 opt-in 이었다 — 재무장을 깜빡하면 세션이
                # 조용히 끝났다(실측: #472/#473/#484/#173 재스폰 라운드).
                # 여기서 스폰 자신이 `spawn.py watch --follow` 를 detached
                # 프로세스로 띄우고 그 pid 를 workspace index 에 등록한다.
                # 워처를 못 띄우면 스폰 자체를 완료로 치지 않는다 — 구조적으로
                # "워처 없는 스폰"이 불가능해야 한다는 요구이기 때문이다.
                watcher_log = Path(str(cwd) + ".watcher.log")
                resolved_watch_cwd = str(Path(cwd).resolve())
                try:
                    with watcher_log.open("a", encoding="utf-8") as wf:
                        wproc = subprocess.Popen(
                            [sys.executable, str(Path(__file__).resolve()),
                             "-C", resolved_watch_cwd,
                             "watch", "--issue", str(issue), "--role", role,
                             "--follow", "--self-heal",
                             "--stall-timeout", str(stall_timeout_min)],
                            stdin=subprocess.DEVNULL, stdout=wf,
                            stderr=subprocess.STDOUT, start_new_session=True,
                        )
                except OSError as exc:
                    print(f"[{role}] 워처 자동 무장 실패 — 스폰을 완료로 치지 "
                          f"않는다: {exc}", file=sys.stderr)
                    return 1
                _workspace_index_put(issue, role, str(cwd), str(log_path),
                                      watcher_pid=wproc.pid,
                                      watcher_armed_at=time.time())
                print(f"[{role}] 워처 자동 무장: pid {wproc.pid} "
                      f"(로그 {watcher_log})", file=sys.stderr)
                # 이슈 #1154: 워처는 `start_new_session=True` 로 detach 됐지만,
                # 아래 `_await_bounded()` 를 그대로 거치면 이 스폰 프로세스
                # 자신이 호출자의 bounded 호출 안에 계속 살아 있는다 —
                # `_rearm_watcher_detached()`(#1133/#1149) 가 등록 직후 바로
                # 리턴해 살아남는 것과 달리, 여기는 그 리턴이 `no_wait` 뒤에만
                # 있어서 기본 경로(non-`--no-wait`)의 워처가 호출자와 함께
                # 죽는 걸로 관측됐다(이슈 #1154 8/8). 등록 직후 항상 리턴해
                # `_rearm_watcher_detached()` 와 같은 모양으로 맞춘다.
                # 기존 bounded 진행 대기가 필요하면 별도
                # `spawn.py watch --issue <n> --role <role>` 호출로 이어본다.
                print(f"[{role}] 스폰은 리턴했지만 세션은 계속 돈다 — 상태는 "
                      f"spawn.py ps, 이어보려면 spawn.py watch --issue "
                      f"{issue} --role {role}", file=sys.stderr)
                return 0
            try:
                _rewrite_spawn_claim_pid(cwd)
                os.setsid()
                # 부모(호출자)가 물려준 stdout/stderr 를 그대로 두면, 곧 띄울
                # claude 서브프로세스가 Popen() 에서 stdout/stderr 를 안 지정해도
                # 그 fd 를 그대로 상속해 세션 끝까지 파이프를 쥐고 있는다 —
                # 부모가 bounded 리턴으로 먼저 나가도, 호출자가 그 파이프의 EOF
                # 를 기다리고 있었다면 여전히 세션 끝까지 블록한다 (실측: 헌트로
                # 발견). devnull 로 갈아치워 파이프 소유권을 끊는다.
                devnull_fd = os.open(os.devnull, os.O_RDWR)
                os.dup2(devnull_fd, 0)
                os.dup2(devnull_fd, 1)
                os.dup2(devnull_fd, 2)
                os.close(devnull_fd)
            except OSError as exc:
                _append_event(events_path, "spawn-death",
                              {"pid": os.getpid(), "stage": "fork-setup",
                               "error": str(exc)})
                raise
        try:
            proc = subprocess.Popen(
                cmd, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                text=True, env={**os.environ, **extra_env}, start_new_session=True,
            )
        except OSError as exc:
            if issue is not None:
                _append_event(events_path, "spawn-death",
                              {"pid": os.getpid(), "stage": "popen",
                               "error": str(exc)})
            raise
        roster_register(roster_key, {
            "pid": proc.pid, "role": role,
            "issue": issue, "ts": int(time.time()),
            "work": str(cwd), "log": str(log_path),
            "expects_pr": issue is not None,  # 이슈 #492: reconcile() 의 expected 입력
            # 이슈 #878: 이 스폰을 무장한 오케스트레이터 자신의 세션 ID —
            # `ORCHESTRATOR_SESSION_ID_ENV` 로 호출자(인터랙티브 호스트나
            # harness driver)가 심어준 값을 그대로 옮겨 담는다. spawn.py
            # 자신은 이 값을 지어내지 않는다 — 없으면 None(해당 세션은
            # headless-resume 대상이 아니라는 신호, 케이스 1 의 라이브
            # notify 경로만 쓴다).
            "session_id": os.environ.get(ORCHESTRATOR_SESSION_ID_ENV) or None,
            "before_head": before_head,  # 이슈 #90 watchdog signal 4 재료
            # `pid`(claude 서브프로세스)는 proc.wait() 리턴과 함께 정상
            # 종료에서도 먼저 죽는다 — push/게이트·소유권 리포트/classify/
            # ledger_write 를 거쳐야 session-end 가 남는 후처리 구간
            # (spawn.py:proc.wait()~_append_event("session-end")) 동안은
            # `pid` 만으로 생존을 재는 소비자가 이 구간을 크래시로 오판한다
            # (이슈 #224 hunt 발견). 그 구간까지 살아있는 이 fork-child(또는
            # non-bounded 경로에서는 현재 프로세스) 자신의 pid 를 별도
            # 필드로 남겨 `_watch --follow` 의 크래시 판정이 여기 대신
            # 참조하게 한다 — `pid`(roster_kill 의 SIGTERM 대상)의 기존
            # 의미는 그대로 둔다.
            "wrapper_pid": os.getpid(),
            # 이슈 #1742/#1774: --skills 사용 시에만 채운다 — 안 쓰면 키
            # 자체가 없어서(빈 값이 아니라) no-flag 경로의 JSON shape 는
            # 그대로다.
            **_skill_roster_fields(skill_sources, skill_sha),
            **roster_resolution_fields,
        })
        if issue is not None:
            # 크래시가 roster_remove/종료 이벤트 사이에서 나면 이 이전엔
            # events.jsonl 에 아무 흔적도 안 남았다(실측: survey.md 사건 #2) —
            # append-only 라 크래시에도 살아남는 이 기록이 session_end_verdict
            # 의 기준선이다 (이슈 #132).
            # session_start_ts 를 변수로 남겨 두는 이유(이슈 #247): 이 세션
            # 자신이 정상 종료하며 미커밋 작업을 남기면, 아래 self-trigger
            # 호출이 워치독처럼 events.jsonl 을 다시 읽어 이 ts 를 재구성할
            # 필요 없이 같은 값을 그대로 재스폰 claim 키로 쓴다.
            # 이슈 #132 의 워치독-전용 재스폰은 ~10-15분 워치독 주기가 자연히
            # 세대 사이를 벌려 놓아 초 단위(int) ts 충돌이 실무에서 안 났지만,
            # self-trigger 는 그 간격 없이 곧바로 다음 세대를 낳을 수 있다 —
            # 초 단위로 자르면 같은 초 안에서 시작한 서로 다른 세대의
            # session_start_ts 가 우연히 같아져 `_respawn_or_cap()` 의
            # already_claimed 검사가 남의 respawn-attempt 를 자기 것으로
            # 오인하고 상한 확인도 없이 조용히 빠져나갈 수 있다(실측:
            # 어써샬-브로큰 헌트). 초 단위로 자르지 않아 충돌 창을 좁힌다.
            session_start_ts = time.time()
            _append_event(events_path, "session-start",
                          {"pid": proc.pid, "ts": session_start_ts})
        try:
            proc.stdin.write(task)
            proc.stdin.close()
        except (BrokenPipeError, OSError):
            pass
        pr_seen = _prior_event_details(events_path, "pr-opened") if issue is not None else set()
        # 이슈 #232: 층(게이트/하네스/샌드박스) 단위 dedup — 예전엔 불리언
        # 하나(gate_refusal_seen)가 세 층을 전부 한 라벨로 뭉갰다. 키는
        # ("gate", <게이트명>, <사유>) / ("harness", <detail>) /
        # ("sandbox", <detail>) — 층·게이트·정규화된 텍스트별로 구분한다
        # (이슈 #246 결함 2: 텍스트를 안 실으면 같은 층의 서로 다른 두 거부가
        # 첫 번째 것에 가려진다).
        # 이슈 #235: per-line 분류는 세션의 마지막 result 줄에만 실리는
        # permission_denials 로 상관돼야 한다(Claude Code 스트림에서 result
        # 는 항상 맨 끝 줄) — 그 전까지는 emit 하지 않고 여기 모아 둔다.
        # is_error 는 "이 도구 호출이 실패했다"지 "거부됐다"가 아니라는
        # 구분이 결함의 뿌리였다(제안서 요구사항 1). 값은 이제
        # (이벤트 타입, detail, tool_name) — tool_name 은 이슈 #246 결함 3의
        # 건별 상관관계에 쓰인다(아래 tool_use_names).
        pending_refusals: dict = {}
        # 이슈 #246 결함 3: 각 tool_use 블록의 id -> name — 뒤이어 오는
        # tool_result 블록의 tool_use_id 를 통해 어느 도구 호출이 거부됐는지
        # 건별로 되짚는다. 두 필드 모두 이미 파싱 중인 스트림에 있던 것이라
        # 새 계측이 아니다(제안서 제약).
        # 이슈 #558: 값이 name 단독에서 (name, command) 로 바뀌었다 — Bash
        # 블록이면 command, 아니면 None. 이미 진행 리포팅(아래 elif name ==
        # "Bash")이 뽑던 값을 재사용한다.
        tool_use_names: dict[str, tuple[str, str | None]] = {}
        # 이슈 #246 결함 1: 터미널 result 줄을 실제로 파싱했는지 — 스트림이
        # 그 줄 전에 끝나면(크래시/kill/truncation, S1) 또는 그 줄이 malformed
        # JSON 이면(S3, 위의 `except ValueError: continue`) 이 플래그는 False 로
        # 남고, 루프가 끝난 뒤 남은 pending_refusals 를 unverified-refusal 로
        # 대신 flush 한다.
        result_seen = False
        # A URL the session **read** is indistinguishable from a PR it
        # **opened** unless the owner/repo is checked: octocat/Hello-World/pull/1
        # is GitHub's own documentation example and appears in gh help output.
        # 실측 2026-07-30 — 그 URL 하나로 pr-opened 가 서고 스폰이 조기 복귀했다
        # (이슈 #142). origin 을 못 읽으면 접두사는 None 이고 예전처럼 전부 받는다.
        pr_prefix = _origin_pr_prefix(cwd) if issue is not None else None
        # br 의 실제(또는 과거) PR 번호를 세션당 한 번만 gh 로 풀고 메모이즈한다.
        # 후보 URL 마다 부르면 gh 서브프로세스가 후보 수만큼 뜨고, 이 호출이
        # `for line in proc.stdout:` 루프 안이라 gh 가 네트워크에서 블록하는
        # 동안 세션의 stdout 파이프가 차면 세션 자신이 멈춘다 — _pr_for_branch
        # 는 URL 이 아니라 브랜치의 함수라 세션 안에서 값이 같다(PR #184 리뷰).
        # PR 이 아직 없으면(None) 다음 후보에서 다시 풀어, 일시적 gh 실패 후
        # 재시도 성질은 유지한다.
        pr_number: int | None = None
        # 연속으로 같은 file_path 에 나는 Write/Edit progress 를 억제하는
        # 상태 — 직전에 기록한 progress 이벤트의 file_path(Write/Edit 가
        # 아니었으면 None)를 들고 있는다.
        last_progress_file: str | None = None
        with open(log_path, "w", encoding="utf-8") as lf:
            for line in proc.stdout:
                lf.write(line)
                lf.flush()
                if issue is not None:
                    for m in _PR_URL_RE.findall(line):
                        if pr_prefix and not m.startswith(pr_prefix):
                            continue
                        if m in pr_seen:
                            continue
                        if pr_number is None:
                            pr_number = _open_pr_for_branch(Path(cwd), br)
                        if pr_number is not None and int(m.rsplit("/", 1)[-1]) == pr_number:
                            pr_seen.add(m)
                            _append_event(events_path, "pr-opened", m)
                            if issue is not None:
                                # 이슈 #782: 이벤트 채널이 완료를 확정적으로
                                # 안 순간 원장에 찍어 둔다 — 뒤이은 폴링
                                # 틱의 ledger_check_and_stamp() 가 같은 키를
                                # 보면 TTL 안이라 조용히 넘어간다(Acceptance
                                # test 2).
                                ledger_stamp(
                                    f"health-repair:{issue}:{role}:pr-expected-missing")
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(obj, dict):
                    continue
                if obj.get("type") == "result":
                    result = obj
                    # `result` 줄은 "언제나 스트림의 마지막 줄"이라고 문서화만
                    # 돼 있을 뿐 강제되지 않는다(이슈 #235 실행-관찰 연구,
                    # research-evidence.md:160-164) — 두 번째 `result` 줄이
                    # 오면 result_seen 이 이미 True 라 이 블록을 건너뛰어
                    # pending_refusals 를 다시 flush 하지 않는다. 옛
                    # refusals_seen 집합이 세션 전체에 걸쳐 지녔던 "한 번만
                    # flush" 성질을 대신한다(이슈 #246 헌트 finding 5).
                    if not result_seen:
                        result_seen = True
                        if issue is not None:
                            raw_denials = result.get("permission_denials")
                            if isinstance(raw_denials, list):
                                # 확정된 리스트(비었을 수도 있음) — 이슈 #246
                                # 결함 3: 후보마다 tool_name 으로 건별 상관시킨다.
                                _flush_correlated_refusals(events_path, pending_refusals,
                                                           raw_denials)
                            else:
                                # 이슈 #246 결함 1 (S2): permission_denials 가
                                # absent/None/truthy-non-list — 형태를 신뢰할
                                # 수 없다. 상관은 시도하지 않고 이미 분류된
                                # 후보를 unverified-refusal 로 정직하게
                                # 남긴다.
                                _flush_unverified(events_path, pending_refusals)
                elif issue is not None and obj.get("type") == "user":
                    for block in (obj.get("message") or {}).get("content") or []:
                        if not isinstance(block, dict) or block.get("type") != "tool_result":
                            continue
                        if not block.get("is_error"):
                            continue
                        text = _tool_result_text(block.get("content"))
                        tool_use_id = block.get("tool_use_id")
                        name_cmd = (tool_use_names.get(tool_use_id)
                                   if isinstance(tool_use_id, str) else None)
                        tool_name, tool_command = name_cmd if name_cmd else (None, None)
                        classified = _classify_refusal_text(text, command=tool_command)
                        if classified is None:
                            continue
                        ev_type, key, detail = classified
                        if key not in pending_refusals:
                            pending_refusals[key] = (ev_type, detail, tool_name)
                elif issue is not None and obj.get("type") == "assistant":
                    # gate-refusal/pr-opened 와 같은 파싱 결과(obj)를 재사용한다
                    # — 이 줄에 대해 json.loads 를 두 번 부르지 않는다.
                    for block in (obj.get("message") or {}).get("content") or []:
                        if not isinstance(block, dict) or block.get("type") != "tool_use":
                            continue
                        name = block.get("name")
                        inp = block.get("input") or {}
                        command = str(inp.get("command") or "") if name == "Bash" else None
                        # 이슈 #246 결함 3: 이 tool_use 의 id -> (name, command) 를
                        # 기록해 둔다 — 뒤이어 올 tool_result 의 tool_use_id 가
                        # 이걸 통해 어느 도구 호출이 거부됐는지 되짚는다.
                        # Write/Edit/Bash 로 좁히지 않고 전부 기록한다(진행
                        # 리포팅과 달리 상관관계는 모든 도구가 대상). command 는
                        # 이슈 #558: Bash 가 아니면 None.
                        block_id = block.get("id")
                        if isinstance(block_id, str) and isinstance(name, str):
                            tool_use_names[block_id] = (name, command)
                        if name in ("Write", "Edit"):
                            fp = inp.get("file_path")
                            if fp and fp != last_progress_file:
                                last_progress_file = fp
                                _append_event(events_path, "progress",
                                             {"kind": "tool_use", "detail": f"{name} {fp}"})
                        elif name == "Bash":
                            if command.startswith(_PROGRESS_BASH_PREFIXES):
                                last_progress_file = None
                                _append_event(events_path, "progress",
                                             {"kind": "tool_use",
                                              "detail": f"{command[:60]} 실행"})
        if issue is not None and not result_seen and pending_refusals:
            # 이슈 #246 결함 1 (S1/S3): 스트림이 result 줄 없이 EOF 에
            # 닿았다(크래시/kill/truncation, 또는 터미널 줄 자체가 malformed
            # JSON) — 이미 층 분류된 후보를 잃지 않고 unverified-refusal 로
            # 남긴다.
            _flush_unverified(events_path, pending_refusals)
        rc = proc.wait()
        roster_remove(roster_key)
    finally:
        if not is_parent_return:
            os.unlink(settings)
    if result.get("result"):
        print(result["result"])                  # 세션의 마지막 답 — 기존 UX
    elif not result:
        print(f"[{role}] 결과 이벤트를 받지 못했다 — 라이브 로그를 봐라: {log_path}",
              file=sys.stderr)

    after = board_snapshot(cwd)
    delta = sorted(p for p in set(before) | set(after)
                   if before.get(p) != after.get(p))
    # 사람 게이트에 막힌 줄을 자동으로 판별하던 표는 없다(이슈 #120) —
    # classify() 는 이제 이 경로로는 waiting-on-human 을 못 낸다.
    blocked: list = []

    uncommitted = []
    after_head = None
    if issue is not None:
        after_head = _git_head(cwd)
        st = subprocess.run(["git", "-C", cwd, "status", "--porcelain"],
                            capture_output=True, text=True)
        uncommitted = [l for l in st.stdout.splitlines() if l.strip()]
        if uncommitted:
            print(f"[{role}] 세션이 미커밋 변경 {len(uncommitted)}건을 남기고 "
                  f"끝났다 — 커밋되지 않은 작업은 PR 에 존재하지 않는다. "
                  f"같은 이슈로 재스폰하면 이 워크스페이스를 이어받아 커밋부터 "
                  f"끝낼 수 있다:\n  " + "\n  ".join(uncommitted[:10]),
                  file=sys.stderr)
        try:
            push_result = ensure_pushed(cwd, issue, role)
        finally:
            # ensure_pushed() 안의 `gh`/`git` 호출이 예외를 던져도(이슈 #719
            # hunt: gh 바이너리 부재 등) 클레임은 반드시 풀려야 한다 — 안
            # 그러면 release 지점을 여기로 늦춘 바로 그 변경이 클레임을
            # stale-timeout 까지 새게 만드는 회귀가 된다.
            _release_spawn_claim(cwd, os.getpid())
    else:
        push_result = None
    gates = gate_report(cwd) + ownership_report(cwd, role, delta)
    outcome = classify(rc, result, delta, blocked)
    if outcome == "silent-failure" and uncommitted:
        outcome = "uncommitted-work"
    elif outcome == "silent-failure" and push_result and push_result["status"] == "push-rejected":
        outcome = "push-rejected"
        print(f"[{role}] 호스트 push 가 거부됐다 — 커밋은 로컬에 있다: "
              f"{push_result['reason']}", file=sys.stderr)
    new_commit = issue is not None and _is_new_commit(cwd, before_head, after_head)
    already_delivered = False
    push_succeeded = push_result is not None and push_result["status"] not in (
        "push-rejected", "pr-create-failed")
    if issue is not None and not blocked and not new_commit:
        branch = subprocess.run(["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
                                capture_output=True, text=True).stdout.strip()
        if branch:
            already_delivered = _pr_open_or_merged_for_branch(Path(cwd), branch) is not None
    downgraded = fail_closed_downgrade(outcome, issue, blocked, new_commit, uncommitted,
                                       already_delivered, push_succeeded)
    if downgraded != outcome:
        if downgraded == "progressed-dirty-tree":
            print(f"[{role}] 페일-클로즈드: progressed 로 자기보고 했고 새 "
                  f"커밋도 있지만(before {before_head}, after {after_head}) "
                  f"워크스페이스에 미커밋 변경 {len(uncommitted)}건이 남았다 — "
                  f"{outcome} 를 progressed-dirty-tree 로 표기한다. 기대한 것: "
                  f"이 세션이 끝나기 전에 트리까지 clean. 관찰한 것: 커밋은 "
                  f"있으나 더러운 트리.",
                  file=sys.stderr)
        elif outcome == "silent-failure" and downgraded == "progressed":
            reason = ("이미 브랜치에 open/merged PR 이 있다" if already_delivered
                      else "새 커밋이 push 됐다")
            print(f"[{role}] silent-failure 로 자기보고 됐지만 관측된 git/PR "
                  f"상태가 배달을 보여준다({reason}) — {outcome} 를 progressed "
                  f"로 끌어올린다. 기대한 것: docs 보드 델타로 성공을 포착. "
                  f"관찰한 것: 델타는 없지만 실제로는 배달됨.",
                  file=sys.stderr)
        else:
            print(f"[{role}] 페일-클로즈드: progressed 로 자기보고 했지만 "
                  f"새 커밋이 없고(before {before_head}, after {after_head})"
                  + (f" 미커밋 변경 {len(uncommitted)}건도 남았다" if uncommitted else "")
                  + f" — {outcome} 를 failed-no-commit 으로 깎는다. 기대한 것: "
                  f"이 세션이 끝나기 전에 실제 커밋. 관찰한 것: 커밋 없음"
                  + (" + 더러운 트리" if uncommitted else "") + ".",
                  file=sys.stderr)
        outcome = downgraded
    denials = result.get("permission_denials") or []
    ledger_write({
        "ts": int(time.time()), "role": role, "cwd": str(Path(cwd).resolve()),
        "repo": _repo_name(Path(cwd).resolve()),
        "session_id": result.get("session_id"),
        "cost_usd": result.get("total_cost_usd"),
        "turns": result.get("num_turns"), "rc": rc, "outcome": outcome,
        "board_delta": delta, "denials": len(denials),
        "duration_s": round(time.monotonic() - t0, 1),
        "rulebook": rulebook_desc,
        "core": core_version(),
        "gates": gates,
        "log": str(log_path),
        "push_reason": push_result.get("reason") if push_result else None,
    })

    for line in gates:
        print(line, file=sys.stderr)
    print(f"[{role}] {outcome}"
          + (f", 보드 변화 {len(delta)}건" if delta else ", 보드 무변화")
          + (f", 비용 ${result.get('total_cost_usd'):.2f}"
             if isinstance(result.get("total_cost_usd"), (int, float)) else ""),
          file=sys.stderr)
    sid = f" (session {result.get('session_id')})" if result.get("session_id") else ""
    if denials:
        print(f"[{role}] 거부된 도구 호출 {len(denials)}건 — 게이트가 막았거나 "
              f"답할 사람이 없어 거부됐다. 무엇을 막았는지는 세션 출력에 있다",
              file=sys.stderr)
    if outcome == "refused":
        print(f"[{role}] 게이트가 막아서 보드가 안 바뀌었다 — 이건 실패가 아니라 "
              f"규칙이 지켜진 것일 수 있다. 위 거부 사유를 읽고 맡길 일을 "
              f"고쳐서 다시 띄워라{sid}", file=sys.stderr)
    if outcome == "silent-failure":
        print(f"[{role}] exit 0 인데 보드도 안 바뀌고 막힌 것도 없다 — 성공이 "
              f"아니라 실측된 침묵-사망 모드다. 세션 로그를 확인하라{sid}",
              file=sys.stderr)
    if outcome == "refused-null-result":
        print(f"[{role}] 등록된 REFUSAL 어휘로 무결과를 선언하고 끝났다 — "
              f"커밋/보드 델타가 없어도 이건 실패가 아니라 정직한 거부다"
              f"(이슈 #476 round 3, candidate E){sid}", file=sys.stderr)
    if bounded and issue is not None:
        # 자식(detach 된 프로세스)만 여기 닿는다 — 부모는 이미 fork 직후
        # _await_bounded 에서 리턴했다. session-end 를 self-trigger 보다
        # **먼저** 남긴다(이슈 #247 hunt finding 1). self-trigger 가 상한
        # 안이면 `_respawn_or_cap()` -> `_spawn_one(..., bounded=True)` 를
        # 재귀 호출하는데, 그 재귀 호출은 새 세대가 자기 `session-start` 를
        # 남길 때까지 `_await_bounded()` 에서 이 프로세스 자신을 블록한다.
        # session-end 를 그 뒤로 미루면(제안서의 원래 문구가 그랬다) 이
        # 세션 자신의 session-end 가 events.jsonl 에 새 세대의 session-start
        # **뒤에** 찍힌다 — `session_end_verdict()` 는 마지막
        # session-start(새 세대의 것) 뒤에 session-end 가 있는지만 보므로,
        # 이 순서에서는 그 자리에 남의(이 세션 자신의) session-end 를 보고
        # 새 세대가 진짜 죽어도 영원히 `normal` 로 오판한다 — 이 이슈가
        # 넓히려는 바로 그 안전망이 재귀 지점에서 스스로 꺼진다(실측:
        # 어써샬-브로큰 헌트, 실제 재귀 이벤트 시퀀스로 재현). 먼저
        # session-end 를 남기면 새 세대의 session-start 가 이 세션 자신의
        # session-end **뒤에** 오므로 그 오판이 구조적으로 불가능해진다.
        push_reason = push_result.get("reason") if push_result else None
        _append_event(events_path, "session-end",
                      {"outcome": outcome, "reason": push_reason}
                      if push_reason is not None else outcome)
        # 이슈 #782: session-end 를 이미 확정적으로 아는 순간 원장에 찍는다
        # — 뒤이은 폴링 틱이 이 세션을 죽었다고(DEAD-ERRORED/session-crashed)
        # 다시 보고하지 않게 한다(Acceptance test 2/3).
        ledger_stamp(f"health-repair:{issue}:{role}:session-crashed")
        ledger_stamp(f"health:{issue}:{role}:DEAD-ERRORED")
        # 이슈 #534: session-end 직후, self-trigger 재스폰과 같은 자리에서
        # durable 코멘트도 남긴다 — roster_watchdog() 틱이 이 엔트리를 볼
        # 무렵엔 roster_remove()(spawn.py:3988)가 이미 지워버린 뒤라
        # _self_trigger_respawn()과 같은 dead-entry-invisible 레이스를
        # 그대로 겪는다.
        _post_session_end_comment(Path(cwd), issue, roster_key, cwd, str(log_path))
        _self_trigger_respawn(outcome, roster_key, cwd, issue, role,
                              str(log_path), session_start_ts)
        os._exit(rc if isinstance(rc, int) else 0)
    return rc


if __name__ == "__main__":
    sys.exit(main())
