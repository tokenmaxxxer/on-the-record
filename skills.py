"""Skill-resolution machinery (skill repo discovery, --skills resolution,
skill-family -> skill-source mapping, roster provenance fields), extracted from
spawn.py (issue #2105, extraction 7/N).

Pure move — no behavior change. spawn.py imports this module and re-exports
every moved name, so external callers and tests keep addressing them as
`spawn.<name>`.

Patching-compat mechanism (copied from relay.py/roster.py/plumbing.py/
watchdog.py/events.py/consult.py, extractions 1-6): every cross-function
reference here resolves at call time through `_sp` — the spawn module
object, injected by spawn.py right after it imports this module (guarded so
only the canonical spawn/__main__ module binds it), so
`mock.patch.object(spawn, "<name>")` patches stay visible to the moved
code. Cluster-internal cross-function calls also go through `_sp`.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# The spawn module object; set by spawn.py on import. All cross-module lookups
# resolve through it at call time so monkeypatches on spawn attributes are seen.
_sp = None

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


def _skill_repo_git_env() -> dict[str, str]:
    """이슈 #3231 round-3 residual-risk fix: `_skill_repo_managed_root()`가
    SessionStart 훅(`skill-corpus-bootstrap.sh` -> `spawn.py ensure-skills`)
    에서 도는 clone/pull 두 `_run_net()` 호출에 얹을 env.

    round-2 독립검증(PR #3247, `docs/issue-3231/reports/adversarial-review+
    silent-failure-audit+test-depth-audit-88bb8a1f.md`)이 실제 pty +
    자격증명을 요구하는 로컬 `401` 서버로 재현: env 없이 돌면 git 이
    `Username for '...': ` 에서 그대로 블록한다 — `_run_net()`의
    `timeout=CLONE_TIMEOUT`/`NETWORK_TIMEOUT` 이 결국은 막아 fail-closed
    로 끝나지만(무한정 걸리지는 않는다), 그 사이 SessionStart 자체가 최대
    180초 지연된다. 이 저장소의 다른 git 네트워크 호출 지점
    (`plumbing.py:364-390` `_git_env()`, `relay.py`/`pipeline.py`가 이미
    사용)이 정확히 이 위험에 쓰는 그 두 키를 그대로 재사용한다 — 새 관례를
    만들지 않는다.

    `_git_env()` 자신과 달리 `GH_TOKEN` 유무로 게이팅하지 않는다:
    `_git_env()`는 push 권한이 필요한 오케스트레이터 자신의 fetch/push용이라
    토큰이 없으면 `None`을 돌려 사용자의 다른 자격증명 경로(ssh-agent,
    osxkeychain)를 막지 않으려 한다. 이 호출 지점은 익명 읽기 전용 clone/pull
    (공개 레포 `skill-repository`, push 없음)이라 토큰이 있든 없든 대화형
    프롬프트를 막아야 한다 — 게이팅하면 정확히 이 함수가 고치려는 그
    (토큰 없는) 경우에 가드가 빠진다.

    round-3 독립검증(PR #3256)이 이 두 키로 못 막는 별도 경로를 로컬
    `sshd` + 패스프레이즈로 잠긴 키로 재현했다: SSH 키 패스프레이즈 프롬프트는
    git 자신의 자격증명 레이어가 아니라 `ssh` 클라이언트가 직접 tty 를
    읽는 별도 경로라 `GIT_TERMINAL_PROMPT`/`GIT_ASKPASS` 가 안 닿는다. 이
    호출부는 지금 `https://` URL 을 그대로 써서 오늘은 도달 불가능하다고
    검증됐지만("not reachable today" 는 이 한 호출 지점의 성질이지 이
    가드 함수의 성질이 아니다), 가드는 메커니즘 쪽에 둔다: `GIT_SSH_COMMAND`
    에 `BatchMode=yes` 를 얹어 SSH 쪽 프롬프트도 같은 fail-fast 로
    막는다 — 기존 `GIT_SSH_COMMAND` 커스터마이즈가 있으면 덮어쓰지 않고
    그 위에 옵션만 얹는다. `BatchMode=yes` 는 ssh-agent/pubkey 처럼 이미
    비대화식으로 성립하는 인증은 그대로 통과시키고, 대화식 프롬프트가
    실제로 필요한 경우만 막는다."""
    ssh_cmd = os.environ.get("GIT_SSH_COMMAND", "ssh")
    return {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "true",
            "GIT_SSH_COMMAND": f"{ssh_cmd} -o BatchMode=yes"}


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
    d = _sp.ROOT / "runs" / "rulebooks" / "skill-repository"
    d.parent.mkdir(parents=True, exist_ok=True)
    with _sp._locked_rulebook_dir(d):
        skills_dir = d / "skills"
        if _sp._skill_repo_valid(skills_dir):
            if not _sp._pull_is_fresh(d):
                # silent-failure-audit round 2 (issue #3231): `_run_net`
                # itself deliberately `sys.exit()`s on a real
                # `TimeoutExpired` (plumbing.py, issue #285 P5 -- correct
                # for its orchestrator callers, which must halt). This
                # function's own contract is the opposite: best-effort,
                # never sys.exit, always return -- a slow-but-alive
                # network on a refresh pull must fall back to the
                # already-valid corpus below, not crash the caller.
                try:
                    _sp._run_net(["git", "-C", str(d), "pull", "-q", "--ff-only"],
                             "[skill-repo] pull", env=_sp._skill_repo_git_env())
                    _sp._mark_pulled(d)
                except SystemExit as exc:
                    print(f"[skill-repo] pull failed: {exc}", file=sys.stderr)
            # 이슈 #2616: core_root() 와 완전히 같은 TTL-pull 패턴(같은
            # _pull_is_fresh/_run_net/_mark_pulled) 을 쓰는 관리 클론이라
            # 같은 결함(TTL 창 안에서 실제 stale 여부와 무관하게 "현재"로
            # 보임)을 그대로 물려받는다 — 같은 보고 레이어를 그대로 재사용.
            _sp._report_managed_clone_staleness(d, "skill-repo")
            return skills_dir
        # 이슈 #3231 must-not: `git clone` 을 최종 경로 `d` 에 바로 걸면,
        # 중간에 죽은 프로세스가 `d` 를 "일부만 받아진 채" 남기고 그 상태가
        # `_skill_repo_valid()` 를 우연히 통과할 수 있다(체크아웃이 skill
        # 디렉터리 몇 개를 만든 시점과 죽는 시점 사이) — 그러면 이후의
        # 모든 해석이 불완전한 corpus 를 "있다"고 조용히 믿는다. 그래서
        # clone 은 `d` 옆의 스크래치 디렉터리로 받고, 유효성 확인을 통과한
        # 뒤에만 `os.replace()` 로 `d` 자리에 원자적으로 바꿔 끼운다 — 죽으면
        # 스크래치만 지저분해지고 `d` 는 손대지 않은 채(대개 부재) 남아
        # 계속 unsatisfied 로 읽힌다.
        for stale in d.parent.glob(d.name + ".tmp-*"):
            shutil.rmtree(stale, ignore_errors=True)
        tmp_dir = d.parent / f"{d.name}.tmp-{os.getpid()}-{int(time.time() * 1e6)}"
        try:
            print("[skill-repo] skill-repository 를 받는 중", file=sys.stderr)
            result = _sp._run_net(["git", "clone", "-q",
                     "https://github.com/tokenmaxxxer/skill-repository.git",
                     str(tmp_dir)], "[skill-repo] clone", timeout=_sp.CLONE_TIMEOUT,
                     env=_sp._skill_repo_git_env())
            # returncode 도 확인한다 -- 디렉터리 내용만 보면, 네트워크가 체크아웃
            # 도중(일부 skill 디렉터리는 이미 받아졌지만 전부는 아닌 시점)
            # 끊겨 git 이 스스로 0이 아닌 채 종료해도 "그 몇 개는 진짜 있으니
            # valid" 로 오판할 수 있다. 종료 코드가 0일 때만 그 스크래치를
            # 신뢰한다 -- 두 신호(종료 코드 + 실제 내용) 를 같이 요구해야
            # "일부만 받아진 채 있다 코드로는 성공"과 "일부만 받아진 채 있다
            # 코드도 실패"를 구별하지 않고 둘 다 거른다.
            if result.returncode == 0 and _sp._skill_repo_valid(tmp_dir / "skills"):
                if d.exists():
                    shutil.rmtree(d, ignore_errors=True)
                os.replace(str(tmp_dir), str(d))
                _sp._mark_pulled(d)
        except (OSError, SystemExit) as exc:
            # silent-failure-audit (issue #3231): a bare `except OSError:
            # pass` here would discard exactly the detail a stuck fetch
            # needs to be diagnosable -- git missing, `runs/` read-only,
            # disk full during os.replace() all degrade to the identical
            # unhelpful "not fetched yet" message downstream in
            # ensure_skill_corpus_cli() otherwise, forever, with nothing
            # distinguishing a transient network hiccup from a permanent
            # local misconfiguration.
            #
            # silent-failure-audit round 2 (issue #3231): `SystemExit` is
            # added here alongside `OSError` because `_run_net` (called
            # just above with `timeout=CLONE_TIMEOUT`) itself deliberately
            # `sys.exit()`s on a real `TimeoutExpired` -- correct for its
            # orchestrator callers (plumbing.py, issue #285 P5), but this
            # function's own contract (and `ensure_skill_corpus_cli()`'s,
            # which calls it transitively) is best-effort: never raise,
            # always report and return. Without this clause a slow-but-
            # alive network (a real timeout, not a fast refusal) escaped
            # as an uncaught `SystemExit` and killed the whole
            # `spawn.py ensure-skills` process -- reproduced live in
            # PR #3238's verification record, section 5.
            print(f"[skill-repo] fetch failed: {type(exc).__name__}: {exc}",
                  file=sys.stderr)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        if _sp._skill_repo_valid(skills_dir):
            return skills_dir
    return None


def _skill_repo_root() -> Path | None:
    """`--skills` 가 마운트할 skill-repository 체크아웃 루트. 순서:
    `MUSTER_SKILL_REPO` env > 형제 클론 (`$TOKENMAXXXER_RULEBOOKS/
    skill-repository`) > 관리 클론(이슈 #1789 — skill-repository가 공개된
    뒤로는 on-the-record 소유 클론이 다른 관리 체크아웃과 같은 fallback을
    쓸 수 있다). 셋 다 없으면 `None`.

    이슈 #3277: `MUSTER_SKILL_REPO` 가 **설정됐지만 그 경로가 없을 때**는
    아래 티어로 흘려보내지 않고 `None` 을 돌려준다. 예전에는 "일부러 없는
    경로로 지정했다"와 "아예 지정 안 했다"를 똑같이 처리해, 관리 클론(항상
    채워져 있다)으로 조용히 빠졌다. 그래서 스킬을 끄려고 없는 경로를
    지정한 실험 팔이 실제로는 스킬을 그대로 받았다 — R007(이슈 #3245)이
    네 라운드 동안 켠 팔과 끈 팔이 아니라 켠 팔과 켠 팔을 비교하고 있었던
    이유다. env 를 명시적으로 준 호출자는 어느 저장소를 쓸지 이미 정한
    것이고, 그 선택을 조용히 뒤집는 fallback 은 선택이 아니라 사고다.

    비어 있는 문자열은 여전히 미지정으로 본다(`MUSTER_SKILL_REPO=`는 셸에서
    변수를 지우는 관용구다) — 구별하는 건 "설정됐고 값이 있는데 그 경로가
    없다" 하나뿐이다."""
    env_value = os.environ.get("MUSTER_SKILL_REPO")
    if env_value:
        p = Path(os.path.expanduser(os.path.expandvars(env_value)))
        if p.is_dir():
            return p
        # 이슈 #3277: 명시적 선택은 존중한다 — 없으면 없는 것이다.
        print(f"[skills] MUSTER_SKILL_REPO={env_value!r} 가 가리키는 경로가 "
              f"없다 — 스킬 저장소 없음으로 처리한다(fallback 하지 않는다).",
              file=sys.stderr)
        return None
    sibling = os.path.expandvars("$TOKENMAXXXER_RULEBOOKS/skill-repository")
    if "$" not in sibling:
        p = Path(os.path.expanduser(sibling))
        if p.is_dir():
            return p
    return _sp._skill_repo_managed_root()


def _carries_hooks(skill_dir: Path) -> bool:
    """스킬 마운트가 항상 거부되는 조건 — `hooks/` 서브디렉터리 존재.
    `resolve_static_policy_source()`/`resolve_consult_skill_source()`/
    `resolve_skill_source()`/`resolved_skill_sources()` 의 실제 마운트-거부
    판정과, 이슈 #2679 send-back 이후 후보 목록 필터가 같은 정의를 쓰게
    하는 단일 소스 — 후보 목록이 거부 판정과 별도의 두 번째 사본으로
    갈라지면 "후보로 나열됐지만 실제로는 거부되는" 항목이 다시 생긴다."""
    return (skill_dir / "hooks").is_dir()


def _available_skills_clause(available: list[str]) -> str:
    """이슈 #2679: unknown-skill 거부의 두 출구(`resolved_skill_dirs`,
    `resolved_skill_sources`)가 후보 절을 같은 모양으로 낸다 — 후보는 항상
    거부한 바로 그 resolver 가 이미 나열한 목록에서 오지, 손으로 관리하는
    별도 표에서 오지 않는다(그래야 실제 마운트 가능한 것과 어긋날 수
    없다). 후보가 하나도 없으면(스킬을 하나도 못 찾은 설치) 빈 목록을
    찍는 대신 그렇다고 명시한다(empty-state 요구).

    이슈 #2679 send-back (독립 검증에서 재현): 호출자는 `available` 로
    `_carries_hooks()` 를 이미 통과시킨(hooks/ 를 든 디렉터리를 뺀) 이름만
    넘겨야 한다 — 안 그러면 여기 나열된 이름이 실제로는
    `resolve_skill_source()` 등에서 다시 거부되는, "후보라고 나열했지만
    한 걸음 뒤에서 막다른 길" 재발이 된다."""
    if not available:
        return "사용 가능한 스킬이 하나도 없다"
    return f"쓸 수 있는 이름: {', '.join(available)}"


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
        # 이슈 #2679 send-back (독립 검증에서 재현): 이 이름-존재 판정
        # (`available`) 은 그대로 두되, 에러 절에 나열할 후보만
        # `_carries_hooks()` 로 걸러 실제 마운트 가능한 이름만 보여준다 —
        # hooks/ 를 든 디렉터리를 정확한 이름으로 요청하면 여전히
        # (이 목록이 아니라) `resolve_skill_source()` 등의 hooks/ 전용
        # 거부 메시지로 fail-closed 된다; 여기서 걸러지는 건 "모르는
        # 이름" 에러가 그 항목을 마치 쓸 수 있는 것처럼 후보에 얹는
        # 경우뿐이다.
        mountable = [n for n in available
                     if not _sp._carries_hooks(repo_root / n)]
        sys.exit(f"--skills: 모르는 스킬 {', '.join(unknown)} "
                  f"— {_sp._available_skills_clause(mountable)}")
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


def ensure_skill_corpus_cli() -> int:
    """`spawn.py ensure-skills` -- 이슈 #3231. `--skills`/`--skill` 이 실제로
    스폰을 시도하기 전에, 이 세션의 SessionStart 훅에서 한 번 미리 불러
    corpus 를 "필요해지는 시점"이 아니라 "세션이 뜨는 시점"으로 당긴다
    (tier: on-first-need-with-notice — 자동으로 clone/pull 하되 매번
    무엇을 하는지 stderr 에 알린다, must-not: 조용히 하지 않는다).

    두 가지를 순서대로 한다, 각각 실패해도 나머지를 막지 않는다(best-effort,
    항상 0 을 돌려준다 — SessionStart 훅은 세션을 막으면 안 된다):
    1. `~/.claude/skills` 를 없으면 만든다(내용은 안 채운다 — 그건 사용자
       로컬 오버라이드 tier 라 이 스크립트가 대신 채울 데이터가 없다;
       존재 여부만이 skills.py:338 이 실제로 보는 것이다). 빈 디렉터리
       생성은 되돌리기 쉽고(rmdir) 아무 내용도 안 쓰므로 자동으로 해도
       안전하다 — must-not 이 겨냥하는 "몰래 컨텐츠를 심는다"에 해당하지
       않는다.
    2. `_skill_repo_root()` 를 불러 skill-repository 관리 클론을 필요하면
       받는다 — 이미 `_skill_repo_managed_root()` 가 하는 일 그대로, 여기서
       새 경로를 만들지 않는다. 이 함수가 하는 일은 그 호출을 **언제**
       하느냐를 첫 실제 `--skills` 스폰에서 세션 시작으로 당기는 것뿐이다.
    """
    try:
        home_skills = Path.home() / ".claude" / "skills"
        if not home_skills.is_dir():
            home_skills.mkdir(parents=True, exist_ok=True)
            print(f"[ensure-skills] {home_skills} 를 만들었다 (로컬 스킬 오버라이드용, 내용은 비어 있다)",
                  file=sys.stderr)
    except OSError as exc:
        print(f"[ensure-skills] {Path.home() / '.claude' / 'skills'} 를 만들지 못했다: "
              f"{type(exc).__name__}: {exc}", file=sys.stderr)

    # `_skill_repo_root()` 자체는 sys.exit 하지 않는다(그건 `resolved_skill_dirs()`
    # 가 실제 스킬 이름을 요청받았을 때만 하는 fail-closed) -- 못 받으면 그냥
    # None 을 돌려주고, 다음 실제 --skills 스폰이 다시 시도한다.
    root = _sp._skill_repo_root()
    if root is None:
        print("[ensure-skills] skill-repository corpus 를 아직 못 받았다 -- "
              "네트워크가 없거나 관리 클론이 실패했다; 다음 --skills 스폰 때 "
              "다시 시도한다", file=sys.stderr)
    else:
        print(f"[ensure-skills] skill-repository corpus 는 {root} 에서 쓸 수 있다",
              file=sys.stderr)
    return 0


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


def _skill_identity_key(skill_dir: Path) -> object:
    """이슈 #2579 dedup 전용 정체성 키. `_skill_content_hash()`와 달리
    `SKILL.md` 를 못 읽으면 빈-바이트 해시(모든 "못 읽음" 케이스가 공유하는
    같은 문자열)로 떨어지지 않고 매번 새 유니크 객체를 돌려준다 —
    `SKILL.md` 가 둘 다 없는, 서로 무관한 두 디렉터리를 "내용이 같다"고
    오판해 `_collapse_identical_matches()` 가 잘못 합치는 사고를 막는다."""
    try:
        data = (skill_dir / "SKILL.md").read_bytes()
    except OSError:
        return object()
    return hashlib.sha256(data).hexdigest()


_SKILL_SOURCE_LABELS = ("skill-repo", "plugin", "local-user", "local-repo")


def _split_skill_qualifier(raw: str) -> tuple[str | None, str]:
    """이슈 #2579: `--skills <source>:<name>` 를 (source, name) 으로 쪼갠다.
    prefix 가 네 소스 라벨(`_SKILL_SOURCE_LABELS`) 중 하나가 아니면
    한정자가 아니라 이름 자체의 일부로 본다(콜론 없는 이름이 압도적
    다수라 오탐 여지가 없다) — 이름에 소스가 없으면 (None, raw) 그대로."""
    if ":" in raw:
        prefix, _, rest = raw.partition(":")
        if prefix in _SKILL_SOURCE_LABELS and rest:
            return prefix, rest
    return None, raw


def skill_branch_slug(skill_names: list[str]) -> str:
    """이슈 #2579: `--skills` 의 브랜치/스킬-이름 슬러그를 스킬 *이름*으로만
    짓는다 — `<source>:<name>` 한정자의 콜론을 그대로 넣으면 git 브랜치
    이름이 깨진다(실측: `--skills skill-repo:diagnose-first` 실 스폰에서
    `checkout -b issue-<n>/skill-repo:diagnose-first-<lease>` 가 "올바른
    브랜치 이름이 아니다"로 실패). 한정자는 소스 해석에만 쓰고 신원/표시용
    슬러그에는 반영하지 않는다."""
    return "+".join(_split_skill_qualifier(n)[1] for n in skill_names)


def _collapse_identical_matches(matches: list[dict]) -> list[dict]:
    """이슈 #2579: 같은 스킬 이름이 둘 이상의 소스에서 잡혀도, 그 내용이
    바이트 단위로 같으면(예: `~/.claude/skills` 가 skill-repository 체크아웃과
    같은 디렉터리를 가리키는 심링크) 진짜 충돌이 아니다 — 한 디렉터리를 두
    경로로 두 번 센 것뿐이다. 전부 같은 내용이면 검색 순서상 첫 매치 하나로
    합친다(내용이 같으므로 어느 쪽을 골라도 결과는 동일 — precedence 로
    "다른 것 중 하나를 조용히 고르는" 문제와는 다르다). 내용이 하나라도
    다르면 원래 목록을 그대로 돌려줘 기존 fail-closed 충돌 처리로 넘긴다."""
    if len(matches) <= 1:
        return matches
    keys = {m["_content_key"] for m in matches}
    if len(keys) == 1:
        return matches[:1]
    return matches


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

    이슈 #2579: 이름 앞에 소스 라벨을 붙여(`<source>:<name>`, 라벨은
    `skill-repo`/`plugin`/`local-user`/`local-repo`) 소스를 항상(충돌이
    있을 때만이 아니라 언제나) 명시적으로 고를 수 있다 — 한정자가 가리키는
    소스에 그 이름이 없으면 소스와 이름을 모두 이름 붙여 fail-closed.
    한정자가 없으면(압도적 다수) 오늘처럼 이름만으로 찾는다. 같은 이름이
    둘 이상의 소스에서 잡혀도 내용이 바이트 단위로 같으면(예: 심링크로
    같은 디렉터리를 두 경로로 두 번 센 경우) 충돌이 아니다 —
    `_collapse_identical_matches()`; 내용이 하나라도 다르면 여전히
    fail-closed, precedence 로 조용히 고르지 않는다.

    반환값은 이름당 dict 하나: 최소 `name`/`source`/`dir` 를 들고, 소스별
    정체성 필드(`sha`|`plugin`+`version`|`path`+`content_sha256`)가
    추가된다."""
    raw_names = [n.strip() for n in (skills_csv or "").split(",") if n.strip()]
    if not raw_names:
        return []
    home = home or Path.home()
    plugin_index = _sp._installed_plugin_skill_dirs()
    tier3 = _sp._local_skill_dirs(home / ".claude" / "skills")
    tier4 = (_sp._local_skill_dirs(target_repo_root / ".claude" / "skills")
             if target_repo_root is not None else {})
    # 이슈 #2679: 거부 메시지의 후보 목록 — 네 소스 각각이 이미 이 호출
    # 안에서 실제로 찾아낸 이름들의 합집합이지, 손으로 관리하는 별도
    # 목록이 아니다(같은 resolver 가 거부하고 같은 resolver 가 후보를
    # 댄다, `resolved_skill_dirs()`의 :132 출구와 같은 원칙).
    # 이슈 #2679 send-back (독립 검증에서 재현): 위 union 은 hooks/ 를 든
    # 디렉터리도 그대로 후보로 냈다 — `resolve_skill_source()` 등이
    # 아래에서 쓰는 것과 같은 `_carries_hooks()` 판정으로 미리 걸러,
    # 후보로 나열된 이름은 실제로 마운트도 된다는 보장을 지킨다(소스가
    # 여럿인 이름은 그중 하나라도 hooks/ 가 없으면 마운트 가능하다고
    # 본다 — 실제 마운트는 `<source>:<name>` 한정자로 그 소스를 골라
    # 성공할 수 있으므로).
    repo_names = (sorted(p.name for p in repo_root.iterdir()
                          if p.is_dir() and not p.name.startswith(".")
                          and not _sp._carries_hooks(p))
                  if repo_root is not None and repo_root.is_dir() else [])
    plugin_names = {name for name, entries in plugin_index.items()
                     if any(not _sp._carries_hooks(d) for _, d, _ in entries)}
    tier3_names = {name for name, d in tier3.items()
                    if not _sp._carries_hooks(d)}
    tier4_names = {name for name, d in tier4.items()
                    if not _sp._carries_hooks(d)}
    all_available = sorted(set(repo_names) | plugin_names
                            | tier3_names | tier4_names)
    results = []
    for raw in raw_names:
        source_filter, name = _sp._split_skill_qualifier(raw)
        matches: list[dict] = []
        if repo_root is not None and repo_root.is_dir():
            cand = repo_root / name
            if cand.is_dir() and not name.startswith("."):
                matches.append({"source": "skill-repo", "dir": cand,
                                 "sha": _sp.skill_repo_sha(repo_root)})
        for qualifier, plugin_skill_dir, version in plugin_index.get(name, []):
            matches.append({"source": "plugin", "dir": plugin_skill_dir,
                             "plugin": qualifier, "version": version})
        if name in tier3:
            d = tier3[name]
            matches.append({"source": "local-user", "dir": d, "path": str(d),
                             "content_sha256": _sp._skill_content_hash(d)})
        if name in tier4:
            d = tier4[name]
            matches.append({"source": "local-repo", "dir": d, "path": str(d),
                             "content_sha256": _sp._skill_content_hash(d)})
        if not matches:
            sys.exit(
                f"--skills: 모르는 스킬 {name} — skill-repository, 설치된 "
                f"플러그인, ~/.claude/skills, 타깃 저장소 .claude/skills "
                f"어디에도 없다 — {_sp._available_skills_clause(all_available)}")
        for m in matches:
            m["_content_key"] = _sp._skill_identity_key(m["dir"])
        if source_filter is not None:
            filtered = [m for m in matches if m["source"] == source_filter]
            if not filtered:
                sys.exit(
                    f"--skills: {source_filter}:{name} — 소스 {source_filter} "
                    f"에 스킬 {name} 이 없다"
                    + (f" (다른 소스에서는 발견: "
                       f"{', '.join(_sp._describe_skill_match(mm) for mm in matches)})"
                       if matches else ""))
            matches = filtered
        matches = _sp._collapse_identical_matches(matches)
        if len(matches) > 1:
            sys.exit(
                f"--skills: {name} 가 둘 이상의 소스에서 겹친다 — "
                f"{', '.join(_sp._describe_skill_match(m) for m in matches)} "
                f"(precedence 는 검색 순서일 뿐 충돌을 가리지 않는다 — "
                f"소스를 <source>:{name} 형태로 지정해 골라라, 예: "
                f"skill-repo:{name})")
        m = matches[0]
        if _sp._carries_hooks(m["dir"]):
            sys.exit(
                f"--skills: {name} ({_sp._describe_skill_match(m)}) 가 hooks/ "
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


# 이슈 #2208: POLICY 스킬 — 특정 task family 를 겨냥한 트리거가 아니라
# 세션 전체에 걸쳐 적용되는 규칙(언어 정책, 모델 라우팅 등)이라 cross-family
# 후보 풀에서 경쟁할 이유가 없다. 여기 이름은 역할과 무관하게
# `_cross_family_candidate_corpus()` 가 항상 걸러낸다 — declared-phrase
# self-inflation(work-in-english 의 예시 문구가 코드와 무관한 태스크에
# verbatim 매치되는 문제, 골드 케이스
# `work-in-english-declared-phrase-self-inflation-fp`)처럼 판정 없이 BM25만
# 으로 마운트되는 경로를 원천 차단한다. 감사 결과(이슈 #2208 report) 이
# 모양의 다른 스킬은 model-routing 뿐이었으나, model-routing 은 현재
# 어떤 역할에도 정적으로 매핑돼 있지 않고(family 목록 없음) 실측 로그에서
# 반복적으로 옳게 골라지고 있어 이번 변경 범위에서는 제외했다 — 리포트의
# 감사 섹션 참고.
_STATIC_POLICY_SKILLS = {'work-in-english'}


def resolve_static_policy_source(repo_root: Path | None) -> dict:
    """이슈 #2507 (role retirement stage 6): 역할과 무관하게 항상 적용되는
    POLICY 스킬(`_STATIC_POLICY_SKILLS`, 예: work-in-english)을 무조건
    해석한다. 스폰 마운트 경로의 role 축 없는 기준선 — 과제별 스킬은 전부
    task-text 매치(BM25+judge, add-only)가 그 위에 얹는다. 반환 shape 는
    `{"source": "skill-repo", "skill_dirs": [...], "skills": [이름...],
    "skill_sha": ...}`."""
    skill_dirs = _sp.resolved_skill_dirs(
        ",".join(sorted(_STATIC_POLICY_SKILLS)), repo_root)
    hooked = [d for d in skill_dirs if _sp._carries_hooks(d)]
    if hooked:
        sys.exit(
            f"resolve_static_policy_source: POLICY 스킬 중 "
            f"{', '.join(d.name for d in hooked)} 가 hooks/ 를 들고 있다 — "
            f"skill-repository 는 가이던스 전용이다(훅 없음, 이슈 #1758)")
    return {"source": "skill-repo", "skill_dirs": skill_dirs,
            "skills": [d.name for d in skill_dirs],
            "skill_sha": _sp.skill_repo_sha(skill_dirs[0].parent) if skill_dirs else None}


def resolve_consult_skill_source(skill: str, repo_root: Path | None) -> dict:
    """이슈 #2920: consult/verb/skill_judge/panel/judge 세션의 스킬 축
    기준선. 이 함수가 대체하는 `resolve_skill_family_source()`(이슈 #2561)
    는 `f"{skill}-"` 로 시작하는 skill-repository 디렉터리 전부를 family
    로 유도했다 — 그 컨벤션 자체가 은퇴했다던 `_ROLE_SKILLS`/
    `resolve_role_source()` 고정 표를, 딕셔너리에서 디렉터리 이름 규칙으로
    자리만 옮겨 그대로 살려 둔 것이었다(이슈 #2920 진단). 그 결과 실제
    skill-repository 의 리프 스킬 이름(예: `adversarial-review`,
    `code-architecture` — 그 자체가 다른 무엇의 접두어가 아니다)을 넘기면
    가족이 하나도 안 잡혀 POLICY 스킬만 마운트되면서도 그렇다는 신호가
    전혀 없었다 — retired role 이름(`architecture`/`conformance-review`
    등, 실제 디렉터리가 아니라 접두어일 뿐인 이름)만 골라야 커버리지가
    나오는, 정확히 거꾸로 된 동작.

    이 함수는 `--skills`/`resolve_skill_source()`가 쓰는 것과 같은
    정확한-이름 해석이다: 콤마로 여러 스킬을 받고(멀티 스킬 consult),
    `repo_root` 바로 아래 그 이름과 정확히 같은 디렉터리가 있을 때만
    마운트한다 — family-prefix 추측은 없다. `_STATIC_POLICY_SKILLS`
    베이스라인은 그대로 add-only 로 얹는다.

    이슈 #2569: consult 의 인자는 자유 형식이다(질문 문구, 존재하지 않는
    스킬 이름, 콤마로 구분된 여러 실제 스킬 이름 모두 올 수 있다) — 이름
    하나가 어떤 디렉터리와도 안 맞아도 `sys.exit` 하지 않는다(그건
    `--skills` 자체의 계약이지 이 함수의 계약이 아니다). 대신 매치 안 된
    토큰을 반환 dict 의 `"unresolved"` 키에 그대로 담아, 호출자가 그
    사실을 트레이스/응답에 실어 보이게 한다(이 이슈가 요구하는
    "empty/failed resolution 은 visible 해야 한다" — silently absorbed
    가 아니라).

    `resolve_skill_family_source()` 가 주던 능력 중, 여기서 사라진 것:
    retired role 이름 하나로 그 역할이 예전에 매핑했던 스킬 전체
    (예: `conformance-review` -> 8개)를 한 번에 묶어 싣는 "family
    coverage" — 이제 그런 이름은 실제 디렉터리와 안 맞으므로 아무 것도
    안 잡히고 `unresolved` 에 나타난다. 그 커버리지가 필요하면 정확한
    스킬 이름을 콤마로 나열해서 명시적으로 요청해야 한다(가디언스 전체를
    한 selector 뒤에 숨기지 않는다).

    풀린 디렉터리 중 하나라도 `hooks/` 서브디렉터리를 들고 있으면
    (skill-repository 는 가이던스 전용) fail-closed — `--skills`/
    `resolve_skill_source()`와 같은 규칙."""
    baseline = resolve_static_policy_source(repo_root)
    names = [n.strip() for n in skill.split(",") if n.strip()]
    if repo_root is not None and repo_root.is_dir():
        matched = [n for n in names
                   if n not in _STATIC_POLICY_SKILLS
                   and not n.startswith(".")
                   and (repo_root / n).is_dir()]
    else:
        matched = []
    unresolved = [n for n in names
                  if n not in matched and n not in _STATIC_POLICY_SKILLS]
    if not matched:
        baseline["unresolved"] = unresolved
        return baseline
    exact_dirs = _sp.resolved_skill_dirs(",".join(matched), repo_root)
    hooked = [d for d in exact_dirs if _sp._carries_hooks(d)]
    if hooked:
        sys.exit(
            f"resolve_consult_skill_source: 스킬 {matched!r} 중 "
            f"{', '.join(d.name for d in hooked)} 가 hooks/ 를 들고 있다 — "
            f"skill-repository 는 가이던스 전용이다(훅 없음, 이슈 #1758)")
    merged = _sp.merge_composed_skill_source(baseline, exact_dirs)
    merged["unresolved"] = unresolved
    return merged


def merge_composed_skill_source(skill_source: dict, matched_dirs: list) -> dict:
    """이슈 #2507: 위 `resolve_static_policy_source()`의 결과에 cross-family
    BM25+judge 매치(`_cross_family_skill_matches_with_consult()`)를
    add-only 로 얹는다 — 스폰이 도착할 때 들고 오는 스킬 목록이 고정 표
    조회가 아니라 이번 과제 텍스트에 대한 매치로 구성되게 하는, 이 이슈의
    핵심 변경. 반환은 새 dict(입력을 변형하지 않는다)."""
    seen = {d.name for d in skill_source["skill_dirs"]}
    merged_dirs = list(skill_source["skill_dirs"]) + [
        d for d in matched_dirs if d.name not in seen]
    return {"source": "skill-repo", "skill_dirs": merged_dirs,
            "skills": [d.name for d in merged_dirs],
            "skill_sha": (_sp.skill_repo_sha(merged_dirs[0].parent)
                          if merged_dirs else None)}


def resolve_skill_source(skill_name: str, repo_root: Path | None) -> dict:
    """이슈 #2241 stage 0: `spawn.py --skill` 경로용. `skill_name`(콤마로
    여러 개 가능)을 role 축 없이 곧장 skill-repository 가이던스로 해석한다
    — `resolve_static_policy_source()`와 반환 shape 은 같지만
    ("source"/"skill_dirs"/"skills"/"skill_sha"), 입력이 role 이 아니라
    스킬 이름 자체다."""
    skill_dirs = _sp.resolved_skill_dirs(skill_name, repo_root)
    hooked = [d for d in skill_dirs if _sp._carries_hooks(d)]
    if hooked:
        sys.exit(
            f"resolve_skill_source: {skill_name!r} 이 지정한 스킬 중 "
            f"{', '.join(d.name for d in hooked)} 가 hooks/ 를 들고 있다 — "
            f"skill-repository 는 가이던스 전용이다(훅 없음, 이슈 #1758)")
    return {"source": "skill-repo", "skill_dirs": skill_dirs,
            "skills": [d.name for d in skill_dirs],
            "skill_sha": _sp.skill_repo_sha(skill_dirs[0].parent) if skill_dirs else None}


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
    fields = {"skills_detail": [_sp._skill_source_roster_row(m) for m in skill_sources]}
    if all(m["source"] == "skill-repo" for m in skill_sources):
        fields["skills"] = [m["name"] for m in skill_sources]
        fields["skills_sha"] = skill_sha
    return fields


def _skill_source_roster_fields(skill_source: dict) -> dict:
    """이슈 #1758 요구사항 3 계승, 이슈 #1955 로 단순화: 로스터 엔트리마다
    항상 붙는 resolution 필드. source 는 이제 언제나 skill-repo(rulebook
    해석 경로는 은퇴했다) — resolution_source/resolution_skills/
    resolution_skill_sha 를 채운다."""
    return {"resolution_source": "skill-repo",
            "resolution_skills": skill_source["skills"],
            "resolution_skill_sha": skill_source["skill_sha"]}
