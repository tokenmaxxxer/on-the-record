"""Skill-resolution machinery (skill repo discovery, --skills resolution,
role -> skill-source mapping, roster provenance fields), extracted from
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
                _sp._run_net(["git", "-C", str(d), "pull", "-q", "--ff-only"],
                         "[skill-repo] pull")
                _sp._mark_pulled(d)
            return skills_dir
        try:
            print("[skill-repo] skill-repository 를 받는 중", file=sys.stderr)
            _sp._run_net(["git", "clone", "-q",
                     "https://github.com/tokenmaxxxer/skill-repository.git",
                     str(d)], "[skill-repo] clone", timeout=_sp.CLONE_TIMEOUT)
            _sp._mark_pulled(d)
        except OSError:
            pass
        if _sp._skill_repo_valid(skills_dir):
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
    return _sp._skill_repo_managed_root()


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


# 이슈 #2579: 네 소스 라벨 — `--skills` 이름 토큰의 `<source>:<name>` 접두어로
# 언제든(모호하지 않을 때도) 소스를 명시할 수 있게 한다.
_SKILL_SOURCE_LABELS = {"skill-repo", "plugin", "local-user", "local-repo"}


def _parse_skill_token(tok: str) -> tuple[str | None, str]:
    """`--skills` 이름 토큰 하나를 (요청된 소스 또는 None, 이름)으로 쪼갠다.
    `<source>:<name>` 형태이고 `<source>` 가 네 라벨 중 하나면 명시적 소스
    요청으로 읽는다. 그 외(콜론이 없거나, `:` 앞이 네 라벨이 아닌 경우 —
    예: 이름 자체에 우연히 `:` 가 있는 경우)는 이름 전체를 그대로 쓴다,
    소스 미지정."""
    if ":" in tok:
        source, _, name = tok.partition(":")
        if source in _SKILL_SOURCE_LABELS and name:
            return source, name
    return None, tok


def _skill_token_name(tok: str) -> str:
    """토큰의 이름 부분만(소스 접두어 제외) — 브랜치/슬러그 이름에 쓴다
    (콜론은 git ref 에 못 쓴다)."""
    return _parse_skill_token(tok)[1]


def _skill_content_identity(m: dict) -> str:
    """매치 하나의 내용 정체성(이슈 #2579): 소스 종류와 무관하게
    `SKILL.md` 내용의 sha256 — 심볼릭 링크로 같은 실체를 두 경로로 본
    매치들(신고된 버그: skill-repository 체크아웃과 그걸 가리키는
    `~/.claude/skills` 심링크)이 내용 기준으로 하나로 합쳐지게 한다.
    이미 tier3/4 매치엔 `content_sha256` 이 있지만(#1774), tier1/2엔
    없었다 — 이제 넷 다 같은 필드를 쓴다."""
    if "content_sha256" not in m:
        m["content_sha256"] = _sp._skill_content_hash(m["dir"])
    return m["content_sha256"]


def _dedupe_matches_by_content(matches: list[dict]) -> list[dict]:
    """내용이 같은 매치들을 하나로 묶는다(첫 발견 순서 유지) — 진짜
    충돌(서로 다른 내용)만 남기고, 같은 스킬을 두 경로로 본 것뿐인
    매치는 하나로 합친다. 그룹당 대표 하나(그 그룹에서 처음 발견된
    매치)만 돌려준다."""
    seen: dict[str, dict] = {}
    for m in matches:
        key = _sp._skill_content_identity(m)
        if key not in seen:
            seen[key] = m
    return list(seen.values())


def resolved_skill_sources(skills_csv: str | None, repo_root: Path | None,
                            home: Path | None = None,
                            target_repo_root: Path | None = None) -> list[dict]:
    """이슈 #1774: `--skills a,b,c` 를 네 소스(skill-repository, 설치된
    플러그인, `~/.claude/skills`, 타깃 저장소 `.claude/skills`)에 걸쳐
    푼다. `skills_csv` 가 비면 빈 목록(마운트 없음, byte-identical 경로 —
    이 경우 네 소스 중 어느 것도 읽지 않는다, 요구사항 4).

    이름 하나가 소스 하나에서만 잡히면 그 소스로 확정. 소스 두 개 이상에서
    잡히되 내용(SKILL.md sha256)이 전부 같으면 — 심볼릭 링크로 같은 실체를
    두 경로로 본 것뿐이라 — 충돌이 아니라 하나로 합친다(이슈 #2579).
    내용이 실제로 다른 소스가 둘 이상 남으면(같은 tier 안의 플러그인-대-
    플러그인 충돌 포함) 워크스페이스/브랜치를 건드리기 전에 fail-closed,
    남은 소스를 전부 이름 붙여 보고한다 — 어느 tier 도 다른 tier 를
    조용히 가리지 않는다(이슈 #1774 SCOPE EXTENSION). 어디서도 안 잡히면
    오늘과 같은 fail-closed.

    이름 토큰은 `<source>:<name>` 로 소스를 언제나(모호할 때만이 아니라)
    명시할 수 있다(이슈 #2579) — `_parse_skill_token()`. 명시된 소스에
    그 이름이 없으면(소스 자체가 비어 있어도 마찬가지, empty-state) 소스와
    이름을 둘 다 이름 붙여 fail-closed.

    각 소스가 가리키는 디렉터리에 `hooks/` 서브디렉터리가 있으면 —
    스킬 마운트는 가이던스 전용이라는 원칙 위반 — 역시 워크스페이스/
    브랜치 전에 fail-closed(네 소스 모두 동일 규칙).

    반환값은 이름당 dict 하나: 최소 `name`/`source`/`dir` 를 들고, 소스별
    정체성 필드(`sha`|`plugin`+`version`|`path`+`content_sha256`)와 항상
    `content_sha256`(소스 무관, 이슈 #2579)이 추가된다."""
    tokens = [n.strip() for n in (skills_csv or "").split(",") if n.strip()]
    if not tokens:
        return []
    home = home or Path.home()
    plugin_index = _sp._installed_plugin_skill_dirs()
    tier3 = _sp._local_skill_dirs(home / ".claude" / "skills")
    tier4 = (_sp._local_skill_dirs(target_repo_root / ".claude" / "skills")
             if target_repo_root is not None else {})
    results = []
    for tok in tokens:
        requested_source, name = _sp._parse_skill_token(tok)
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
                f"어디에도 없다")
        if requested_source is not None:
            qualified = [m for m in matches if m["source"] == requested_source]
            if not qualified:
                sys.exit(
                    f"--skills: {name} 는 소스 {requested_source} 에 없다 — "
                    f"{name} 를 실제로 들고 있는 소스: "
                    f"{', '.join(_sp._describe_skill_match(m) for m in matches)}")
            matches = qualified
        matches = _sp._dedupe_matches_by_content(matches)
        if len(matches) > 1:
            sys.exit(
                f"--skills: {name} 가 둘 이상의 소스에서 겹친다 — "
                f"{', '.join(_sp._describe_skill_match(m) for m in matches)} "
                f"(precedence 는 검색 순서일 뿐 충돌을 가리지 않는다, "
                f"내용이 서로 다르다 — <source>:{name} 로 소스를 명시하라)")
        m = matches[0]
        if (m["dir"] / "hooks").is_dir():
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
    hooked = [d for d in skill_dirs if (d / "hooks").is_dir()]
    if hooked:
        sys.exit(
            f"resolve_static_policy_source: POLICY 스킬 중 "
            f"{', '.join(d.name for d in hooked)} 가 hooks/ 를 들고 있다 — "
            f"skill-repository 는 가이던스 전용이다(훅 없음, 이슈 #1758)")
    return {"source": "skill-repo", "skill_dirs": skill_dirs,
            "skills": [d.name for d in skill_dirs],
            "skill_sha": _sp.skill_repo_sha(skill_dirs[0].parent) if skill_dirs else None}


def resolve_role_family_source(role: str, repo_root: Path | None) -> dict:
    """이슈 #2561: `consult.py`(consult/verb/skill_judge/panel 세션)와
    judge 세션의 role 축 기준선 — `_ROLE_SKILLS` 정적 표 없이, 실제
    skill-repository 디렉터리 이름이 `f"{role}-"` 로 시작하는 스킬 전부를
    매 호출마다 기계적으로 유도한다(표가 아니라 저장소 내용 자체를
    읽으므로 드리프트가 없다) + `_STATIC_POLICY_SKILLS`.

    실측 근거(이 세션 레코드 "Evidence" 참고): `resolve_static_policy_source()`
    (POLICY 스킬만) 를 이 두 소비부의 기준선으로 그대로 쓰면, cross-family
    task-text 매치가 role 특유 스킬을 못 건지는 실제 과제 문구에서 세션이
    이전보다 스킬을 덜 갖고 도착한다(측정: 이슈 #2561 세션이 실제
    skill-repository 로 재현, before=5/after=4) — acceptance 가 명시적으로
    금지하는 실패 모드. 접두어 유도는 43개 역할 중 41개에서 옛
    `_ROLE_SKILLS[role]` 과 정확히 같은 집합을 낸다(유일한 예외:
    `defect-verification` 이 매핑했던 `verify-finding-record`/
    `verify-severity-classification` 은 role 접두어를 안 따르는 두 스킬 —
    이 세션 레코드 "Open findings" 참고). 이름 하나를 두 소스(예: 역할
    접두어와 정책 스킬)가 같이 낼 수 있으므로 합집합으로 중복을 없앤 뒤
    `resolved_skill_dirs()` 로 해석한다(모르는 이름은 이미 있을 수
    없다 — 디렉터리 목록 자체에서 유도했으므로).

    이름을 `resolved_skill_dirs()` 로 푼다. 풀린 디렉터리 중 하나라도
    `hooks/` 서브디렉터리를 들고 있으면(skill-repository 는 가이던스
    전용) fail-closed. 반환 shape 는 `resolve_static_policy_source()`와
    같다."""
    prefix = f"{role}-"
    family_names = (sorted(p.name for p in repo_root.iterdir()
                            if p.is_dir() and p.name.startswith(prefix))
                     if repo_root is not None and repo_root.is_dir() else [])
    names = sorted(set(family_names) | _STATIC_POLICY_SKILLS)
    skill_dirs = _sp.resolved_skill_dirs(",".join(names), repo_root)
    hooked = [d for d in skill_dirs if (d / "hooks").is_dir()]
    if hooked:
        sys.exit(
            f"resolve_role_family_source: 역할 {role!r} 접두어로 유도한 "
            f"스킬 중 {', '.join(d.name for d in hooked)} 가 hooks/ 를 들고 "
            f"있다 — skill-repository 는 가이던스 전용이다(훅 없음, "
            f"이슈 #1758)")
    return {"source": "skill-repo", "skill_dirs": skill_dirs,
            "skills": [d.name for d in skill_dirs],
            "skill_sha": _sp.skill_repo_sha(skill_dirs[0].parent) if skill_dirs else None}


def merge_composed_skill_source(role_source: dict, matched_dirs: list) -> dict:
    """이슈 #2507: 위 `resolve_static_policy_source()`의 결과에 cross-family
    BM25+judge 매치(`_cross_family_skill_matches_with_consult()`)를
    add-only 로 얹는다 — 스폰이 도착할 때 들고 오는 스킬 목록이 고정 표
    조회가 아니라 이번 과제 텍스트에 대한 매치로 구성되게 하는, 이 이슈의
    핵심 변경. 반환은 새 dict(입력을 변형하지 않는다)."""
    seen = {d.name for d in role_source["skill_dirs"]}
    merged_dirs = list(role_source["skill_dirs"]) + [
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
    hooked = [d for d in skill_dirs if (d / "hooks").is_dir()]
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


def _role_source_roster_fields(role_source: dict) -> dict:
    """이슈 #1758 요구사항 3 계승, 이슈 #1955 로 단순화: 로스터 엔트리마다
    항상 붙는 resolution 필드. source 는 이제 언제나 skill-repo(rulebook
    해석 경로는 은퇴했다) — resolution_source/resolution_skills/
    resolution_skill_sha 를 채운다."""
    return {"resolution_source": "skill-repo",
            "resolution_skills": role_source["skills"],
            "resolution_skill_sha": role_source["skill_sha"]}
