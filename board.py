"""Board / approval / lint / report / session-verdict machinery

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

def slug(cwd: str) -> str:
    """레포 디렉터리 이름 (계약 v2 §9).

    v1 은 origin 리모트에서 <owner>-<repo> 를 뽑았는데, 그건 폐지된
    `$QA_WORKSPACE` 의 레포 간 경로 때문에만 있던 것이다. 리모트 없는 레포에서
    깨지지 않는 것이 §9 가 이 규칙을 고른 이유다.
    """
    return Path(cwd).resolve().name


def _current_branch(root: Path) -> str:
    """현재 브랜치 이름 (detached HEAD 등이면 'HEAD')."""
    r = subprocess.run(["git", "-C", str(root), "symbolic-ref", "--short", "HEAD"],
                       capture_output=True, text=True)
    name = r.stdout.strip() if r.returncode == 0 else ""
    return name or "HEAD"


def _verify_board_on_remote(root: Path, push: bool) -> int:
    """issue #2125: init 은 파일 생성에서 멈추면 안 된다 — 모든 워크스페이스는
    리모트에서 클론하므로, 리모트 기본 브랜치에 보드 표식이 없으면 스폰이
    admission(#2123)에서 거부된다. 여기서 리모트를 검증하고, 없으면
    `--push` 로 직접 올리거나 복붙 가능한 명령 블록을 출력하고 비0으로
    끝낸다. 이미 리모트에 있으면 조용히 0."""
    slug = _sp._repo_slug(root)
    if slug is not None and _sp._board_marker_probe(slug) is True:
        return 0  # 이미 리모트에 있다 — 조용히 성공
    rels = [_sp.MARKER]
    if (root / _sp.REQUIREMENT_DIGEST_MARKER).exists():
        rels.append(_sp.REQUIREMENT_DIGEST_MARKER)
    branch = _current_branch(root)
    if push:
        # issue #2022 의 근거 그대로: 커밋+push 까지 가야 다음 스폰이 성공한다.
        try:
            subprocess.run(["git", "-C", str(root), "add", *rels],
                           check=True, capture_output=True, text=True)
            staged = subprocess.run(
                ["git", "-C", str(root), "diff", "--cached", "--quiet"],
                capture_output=True, text=True)
            if staged.returncode != 0:  # 스테이징된 변경이 있을 때만 커밋
                subprocess.run(["git", "-C", str(root), "commit",
                                "-m", "board-setup: init approvers.md",
                                "-m", "Subject: board-setup"],
                               check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            sys.exit(f"보드 파일을 커밋하지 못했다: "
                     f"{e.stderr.strip() if e.stderr else e}")
        push_r = subprocess.run(
            ["git", "-C", str(root), "push", "--set-upstream", "origin", branch],
            capture_output=True, text=True)
        if push_r.returncode != 0:
            sys.exit(f"보드 파일을 커밋했지만 push 하지 못했다 — 이 파일들이 "
                     f"리모트에 올라가기 전까지는 모든 스폰이 admission 에서 "
                     f"거부된다: {push_r.stderr.strip() if push_r.stderr else push_r}")
        print(f"보드 파일을 커밋하고 push 했다 (origin/{branch}).")
        return 0
    print(
        f"경고: board not yet on the remote — spawns will be refused at "
        f"admission until pushed.\n"
        f"리모트 기본 브랜치에 {_sp.MARKER} 가 없다(또는 origin 이 없다). "
        f"아래를 그대로 실행하거나, `spawn.py init --push` 로 다시 실행한다:\n\n"
        f"  git add {' '.join(rels)}\n"
        f"  git commit -m 'board-setup: init approvers.md'\n"
        f"  git push --set-upstream origin {branch}\n",
        file=sys.stderr)
    return 2


def init_board(cwd: str, login: str | None = None, push: bool = False) -> int:
    """대상 레포를 보드로 선언한다: docs/specs/approvers.md 를 만든다.

    v3: 계약 심기는 폐지됐다 — 정본은 core 플러그인에만 있고, 레포 사본은
    해시 검사로 강제 동일해져 정보량이 0이었다. 보드 표식이자 승인자
    allowlist 인 approvers.md 만 있으면 된다. **사용자의 파일이다** —
    이미 있으면 절대 덮지 않는다.

    issue #2125: 파일을 쓴 뒤 리모트 검증까지가 init 의 일이다 —
    `_verify_board_on_remote` 참조. `--push` 면 add+commit+push 까지 직접 한다.
    """
    root = Path(cwd).resolve()
    dest = root / _sp.MARKER
    if dest.exists():
        print(f"이미 있다: {dest}")
        _sp.init_requirement_digest(cwd)
        return _verify_board_on_remote(root, push)
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
    _sp.init_requirement_digest(cwd)

    # issue #2022 → #2125: 로컬 작업 트리에만 쓰고 끝내면, 신선한 클론에서
    # 스폰한 세션이 approvers.md 를 못 본다(실측: skill-repository #50).
    # 리모트를 검증하고, --push 면 커밋+push 까지 직접 한다.
    return _verify_board_on_remote(root, push)


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
    dest = root / _sp.REQUIREMENT_DIGEST_MARKER
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
        "각 항목은 반드시 한 줄이다(줄바꿈 없음) — 그 안의 <설명> 과 <출처>는\n"
        "여러 절로 이루어진 자유 형식 텍스트여도 된다(issue #2077). 정확한\n"
        "문법(파서 — `spawn.py::requirement_drift` — 가 그대로 받아들이는 형태):\n"
        "\n"
        "  - R<n>: <설명, 자유 형식> [<status>] (source: <출처, 자유 형식>)\n"
        "\n"
        "<설명>과 <출처>는 쉼표·세미콜론·마침표를 포함한 여러 절이어도 되고,\n"
        "<출처>는 `#<issue-number>` 로 국한되지 않는다 — \"user directive\n"
        "2026-08-23, issue #1\" 처럼 issue 번호를 포함하지 않는 자유 텍스트도\n"
        "허용된다. `[<status>]` 는 공백 없는 단일 토큰이어야 한다.\n"
        "\n"
        "예(한 줄 설명):\n"
        "  - R1: 사용자가 X 를 할 수 있어야 한다 [enforced] (source: #12)\n"
        "\n"
        "예(문서화된 자유 형식 — multi-clause, 자유 형식 source):\n"
        "  - R1: A browser-playable character-growth RPG whose progression "
        "systems benchmark Random Dice 2 — deterministic no-gacha "
        "Dice-Tree acquisition, in-match merge 1→7 pips with 7-pip "
        "Awakening, Supporter-analog companions [live] (source: user "
        "directive 2026-08-23, issue #1)\n"
        "\n"
        "## Entries\n"
        "\n"
        "(아직 없음 — 첫 이슈를 드래프트할 때 R1 부터 여기에 추가한다)\n",
        encoding="utf-8")
    print(f"요구 원장 스텁을 만들었다: {dest}")
    return True


def require_repo_root(cwd: str, issue: int | None) -> None:
    """issue #2395: cwd 가 구조적으로 깨진 세 경우 -- 존재하지 않음, git
    레포 안이 아님, git 레포이지만 레포 루트가 아님(하위 디렉터리) --
    를 그 원인 그대로 이름 붙여 멈춘다. 이 검사가 없으면 세 경우 모두
    `require_board` 의 `approvers.md 없다`(또는 그 이후 게이트의 다른
    증상)로 떨어져, "cwd 가 생각하는 그 레포가 아니다"라는 실제 원인이
    안 보이는 다운스트림 증상만 남는다(이슈 실측: on-the-record 서브
    디렉터리, 존재하지 않는 경로, 아예 다른 레포 각각 다른 오탐 메시지).

    정상 호출 모양(`cd repo && spawn.py --skills <skill> "<일>" --issue N`,
    이슈 #2572, cwd 기본값 `.`)에서는 cwd 가 언제나 레포 루트이므로 이 세 조건 중
    무엇에도 걸리지 않고 그대로 지나간다 -- 이 게이트가 새로 막는
    스폰은 오늘 이미(더 늦게, 더 헷갈리는 메시지로) 막히던 것들뿐이다.

    `issue is None` 이면 통과시킨다: 이 게이트가 지키는 것은 `--issue N`
    이 엉뚱한 레포로 풀리는 사고뿐이다(이슈 제목 그대로) — 이슈 번호가
    아예 없는 ad-hoc 스폰은 지킬 "N" 이 없고, git 레포가 아닌 디렉터리를
    향한 ad-hoc/--no-contract/--dry-run 호출은 오늘도 유효한 모양이다
    (require_acceptance_gate/require_requirement_linkage 와 같은
    `if issue is None: return` 관례).
    """
    if issue is None:
        return
    p = Path(cwd)
    if not p.is_dir():
        sys.exit(
            f"-C 가 존재하지 않는 디렉터리다: {cwd}\n"
            f"  cwd 는 레포 루트를 가리켜야 한다 — 경로를 다시 확인해라.")
    resolved = p.resolve()
    r = subprocess.run(["git", "-C", str(resolved), "rev-parse", "--show-toplevel"],
                        capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(
            f"-C 가 git 레포 안이 아니다: {cwd}\n"
            f"  cwd 는 레포 루트를 가리켜야 한다 — 클론된 레포로 다시 잡아라.")
    toplevel = Path(r.stdout.strip()).resolve()
    if toplevel != resolved:
        sys.exit(
            f"-C 가 레포 루트가 아니라 그 하위 디렉터리다: {cwd}\n"
            f"  실제 레포 루트: {toplevel}\n"
            f"  cwd 가 생각하는 그 레포가 맞는지부터 확인해라 — -C {toplevel} 로 "
            f"다시 잡거나, 그 루트에서 -C 없이 불러라(이슈 #2395).")


def require_board(cwd: str, override: bool) -> None:
    """대상 레포가 보드인지(approvers.md 가 있는지) 본다. 없으면 멈춘다.

    core 의 게이트가 어차피 보드·실행 쓰기를 거부하므로, 세션을 태우기 전에
    같은 사실을 말해주는 것뿐이다 — 버려질 세션에 과금하지 않는다.
    """
    root = Path(cwd).resolve()
    if (root / _sp.MARKER).is_file():
        return
    if override:
        return
    sys.exit(
        f"대상 레포에 {_sp.MARKER} 가 없다: {root}\n"
        f"  이 파일이 보드 opt-in 이자 승인자 allowlist 다. 만들려면:\n"
        f"    python3 spawn.py init -C {root}\n"
        f"  보드를 안 쓸 작업이면 --no-contract 로 건너뛴다.")


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
    rogue = [p for p in _sp.REPO_CONFIG if (root / p).exists()]
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

    phase 판정은 `gates/ci.py._approved_skills_on_issue` 와 같은 술어를
    쓴다: 승인자 계정의 `APPROVE issue-<n>/<role>` 코멘트가 이슈에 하나라도
    있으면 phase-2(issue #312, phase 는 role 이 아니라 이슈의 속성).

    issue #2173: phase-1 이슈는 Acceptance 가 아직 초안 단계이므로 스폰을
    막지는(sys.exit) 않지만, 같은 검사를 advisory 로 한 번 돌려 지금
    형식대로면 phase-2 스폰이 거절될 것을 stderr 에 미리 찍는다 — #2165
    관측(승인 코멘트가 이미 달린 뒤에야 형식 거절을 만나 이슈 본문을
    2-3회 편집-재시도한 왕복)을 승인 *전에* 드러내, 승인자가 phase-2 가
    실제로 시작될 수 있는 상태인지 알고 승인하게 한다.

    `--issue` 없이 스폰하면(보드 밖 작업) 검사할 이슈가 없어 통과시킨다.
    `gh` 조회 실패는 통과가 아니라 차단이다 — 검사 불가를 통과로 읽지
    않는다는 게이트들의 공통 원칙(`acceptance_gate.py`/`ci.py` 동일);
    phase-1 advisory 갈래는 차단이 아니므로 이 원칙 대신 조용히 넘어간다
    (경고 자체가 조회 실패로 못 뜨는 것은 세션을 잃는 것보다 싸다).
    """
    if issue is None:
        return
    root = Path(cwd).resolve()
    if not (root / _sp.MARKER).is_file():
        return  # require_board 가 이미 --no-contract 없이는 여기까지 안 보낸다
    sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
    import ci as _ci
    import acceptance_gate as _acceptance_gate
    approved_skills = _ci._approved_skills_on_issue(root, issue)
    if not approved_skills:
        try:
            bad = _acceptance_gate.check(root, issue)
        except Exception:
            return  # advisory 조회 실패는 침묵 — phase-1 스폰을 막지 않는다
        if bad:
            print(
                f"[acceptance-gate] 경고: 이슈 #{issue} 의 'Acceptance' 절이 "
                f"지금 형식대로면 phase-2 승인 후 스폰이 거절된다:\n"
                + "\n".join(f"  - {b}" for b in bad)
                + f"\n  승인자가 APPROVE 코멘트를 달기 전에 고쳐두면 phase-2 가 "
                f"바로 스폰된다(issue #2173, #310, #441).",
                file=sys.stderr)
        return  # phase-1: advisory 뿐, 스폰은 막지 않는다
    bad = _acceptance_gate.check(root, issue)
    if not bad:
        return
    sys.exit(
        f"이슈 #{issue} 는 phase-2 승인({', '.join(sorted(approved_skills))})을 "
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
    if not (root / _sp.MARKER).is_file():
        return
    sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
    import ci as _ci
    import requirement_linkage as _requirement_linkage
    approved_skills = _ci._approved_skills_on_issue(root, issue)
    if approved_skills:
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
        f"한다(issue #1017, northpole req#6).\n"
        f"  R-ID 목록은 docs/specs/requirement-digest.md 에 있다"
        f"(없으면 `spawn.py init` 이 스텁을 만든다).\n"
        f"  예시 — 이슈 본문에 이런 한 줄이면 된다: Targets R1.\n"
        f"  'infrastructure/no-direct-requirement' 태그는 이슈가 어떤 제품 "
        f"요구에도 직접 닿지 않는 순수 기반 작업(빌드·CI·게이트·리팩터링 등)일 "
        f"때만 적절하다.")


def lint_issue(cwd: str, issue: int) -> list[str]:
    """issue #2088: `require_acceptance_gate`/`require_requirement_linkage` 와
    같은 body-only 게이트를 스폰 없이 미리 돌려본다 — 전자는 phase-2 승인
    후 Acceptance 절의 실행가능성을, 후자는 phase-2 승인 전 요구 연결을
    검사한다(두 게이트는 서로 반대 phase 에서만 발동한다, 위 두 함수의
    docstring 참고). 두 함수와 달리 `sys.exit` 하지 않고 위반을 전부 모아
    반환한다 — 스폰을 시도해 첫 게이트에서 막히고서야 두 번째 위반을
    알게 되는 왕복(issue #2088 리포로 실측: 5회 스폰 거절)을 없앤다.
    """
    root = Path(cwd).resolve()
    violations: list[str] = []
    if not (root / _sp.MARKER).is_file():
        return violations  # require_board 가 이미 --no-contract 없이는 여기까지 안 보낸다
    sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
    import ci as _ci
    import acceptance_gate as _acceptance_gate
    import requirement_linkage as _requirement_linkage
    approved_skills = _ci._approved_skills_on_issue(root, issue)
    if approved_skills:
        bad = _acceptance_gate.check(root, issue)
        violations.extend(f"acceptance: {b}" for b in bad)
        return violations  # phase-2: require_requirement_linkage 도 소급 차단하지 않는다
    br = subprocess.run(
        ["git", "for-each-ref",
         f"refs/heads/issue-{issue}/**", f"refs/remotes/*/issue-{issue}/**"],
        cwd=root, capture_output=True, text=True)
    if br.returncode == 0 and br.stdout.strip():
        return violations  # 이미 스폰된 적 있는 이슈 — 소급 차단하지 않는다
    bad = _requirement_linkage.check(root, issue)
    violations.extend(f"requirement-linkage: {b}" for b in bad)
    return violations


def _approvers(root: Path) -> set[str]:
    """`docs/specs/approvers.md` 한 줄에 하나씩 적힌 GitHub 로그인."""
    p = root / _sp.MARKER
    if not p.is_file():
        return set()
    out = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*-\s*(\S+)", line)
        if m:
            out.add(m.group(1))
    return out


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
    return {m.group(1): "" for m in _sp._UPSTREAM_PATH.finditer(block[1])}


def _front_skill(root: Path, subject: str, skills: dict) -> str | None:
    """그 subject 의 front record — subject 를 처음 연 참가자 (첫 빌드 승인 게이트).

    upstream 이 빈 참가자가 하나뿐이면 그게 체인 루트다. 못 가리면 관례 순서
    (product, 아니면 feasibility)로 물러난다.
    """
    rootless = [r for r in skills
                if not _sp._record_upstream(root / _sp.BOARD / subject / "reports" / f"{r}.md")]
    if len(rootless) == 1:
        return rootless[0]
    for r in ("product-discovery", "technical-feasibility"):
        if r in skills:
            return r
    return None


def approve_scope(cwd: str, issue: int) -> int:
    """s19 의 정확한 문자열 댓글을 승인자 allowlist 로 검증하고, front record 를
    `scope-approved` 로 올리는 커밋을 직접 쓴다 (이슈 #115).

    승인은 여전히 사람의 몫이다 — 이 함수는 그 결정을 **표현하는 방법**(댓글)에서
    **기록에 반영하는 방법**(커밋)으로 옮길 뿐, 어느 참가자도 스스로 승인하지
    못한다는 규칙은 그대로 둔다.
    """
    root = Path(cwd).resolve()
    subject = f"issue-{issue}"
    approvers = _sp._approvers(root)
    if not approvers:
        sys.exit(f"승인자 목록이 비어 있다: {root / _sp.MARKER}")

    skills = _sp.board(root).get(subject)
    if not skills:
        sys.exit(f"{subject} 의 보드 기록이 없다: {root / _sp.BOARD / subject / 'reports'}")

    front = _sp._front_skill(root, subject, skills)
    if not front:
        sys.exit(f"{subject} 의 front record 를 판별할 수 없다.")

    record_path = root / _sp.BOARD / subject / "reports" / f"{front}.md"
    fm = _sp.frontmatter(record_path)
    state = fm.get("loop_state")
    if state == "scope-approved":
        print(f"이미 scope-approved 다: {record_path}")
        return 0
    if state != "scope-proposed":
        sys.exit(f"{record_path} 의 loop_state 가 scope-proposed 가 아니다 "
                 f"(지금: {state or '(없음)'}) — 승인 대상이 아니다.")

    needle = f"APPROVE {subject}/scope"
    pr = _sp._pr_for_branch(root, f"{subject}/{front}")
    # 이슈 댓글이 승인 정본이다 — 먼저 본다. PR 댓글은 PR 이 있을 때만 보는
    # fallback 이지 대등한 소스가 아니다(issue-126: 위치 드리프트로 승인을
    # 놓친 사례가 있었다). 순서를 바꾸지 말 것.
    comments, issue_ok = _sp._issue_comments(root, issue)
    pr_ok = True
    if pr:
        pr_comments, pr_ok = _sp._issue_comments(root, pr)
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


def _issue_num(dirname: str) -> int | None:
    """`"issue-2560"` -> `2560`. `None` if `dirname` isn't that shape."""
    m = re.match(r"^issue-([0-9]+)$", dirname)
    return int(m.group(1)) if m else None


def _lease_slugs_for_issue(issue: int | None) -> set[str]:
    """이슈 #2560: 고정 `_sp.ROLES` 튜플을 대신해, 이 이슈에 로스터
    lease 를 가졌던(현재 살아있든 아니든, roster entry 가 아직 로스터에
    남아있는) 실제 참가자 slug 집합을 돌려준다 (docs/issue-2548/reports/
    architecture.md, Step E) — roster entry 가 하나도 없으면 빈 집합이고,
    43개짜리 고정 이름 목록이 아니다."""
    if issue is None:
        return set()
    try:
        roster = _sp._roster_load()
    except Exception:
        return set()
    return {e.get("role") for e in roster.values()
            if e.get("issue") == issue and e.get("role")}


def _skill_axis_report_names(rep: Path) -> list[str]:
    """이슈 #2432 (role retirement stage 4), 이슈 #2560 개정: `reports/`
    바로 아래에 있지만 이 이슈의 roster lease slug 집합(옛 `_sp.ROLES`
    고정 역할 enum 자리) 에는 없는 `.md` 파일 중, 실제 레코드처럼
    보이는(frontmatter 에 `loop_state` 키가 있는) 파일 이름만 돌려준다.

    새 스킬 축 네이밍은 `single-skill-axis` 동결 결정 때문에 고정 enum이
    없다 — `checkout_issue_branch_for_skill`이 만드는 브랜치 이름 세그먼트
    (`<skill>-<lease-disambiguator>`) 는 임의 문자열이라, 이름 모양으로
    "새 스킬 축 레코드인지" 판별할 수 없다. `loop_state` 존재 여부를 쓰는
    이유: `write_record_skeleton()`(모든 진짜 role/skill 레코드가 거치는
    유일한 생성 경로)이 항상 이 키를 찍는다 — before-landing warrant hunt
    발견(이슈 #2432): 단순 "frontmatter 블록 있음"만 보면, hunt/감사 레코드
    (`---\\nproposal: ...\\n---`처럼 frontmatter 는 있지만 `loop_state` 는
    없는 `docs/issue-1077/reports/hunt-implementation.md` 같은 파일)까지
    쓸려 들어와 `_front_skill()`의 "rootless 레코드는 하나뿐" 불변식을 깨고
    `approve_scope()`(실제 커밋을 쓴다)의 판정을 바꿔 버렸다 — 29개 기존
    subject 에서 실측(`issue-1077`이 그 중 하나, `_front_skill`이
    `implementation` 대신 `None`을 반환하게 됨). `rep.iterdir()`는 한 단계만
    보므로 `reports/<role>/` 같은 중첩 디렉터리(예:
    docs/issue-2241/reports/architecture/survey.md)의 파일들은 여기 걸리지
    않는다."""
    if not rep.is_dir():
        return []
    known = {f"{r}.md" for r in _sp._lease_slugs_for_issue(_sp._issue_num(rep.parent.name))}
    return sorted(p.stem for p in rep.iterdir()
                  if p.is_file() and p.suffix == ".md" and p.name not in known
                  and "loop_state" in _sp.frontmatter(p))


def board(root: Path) -> dict[str, dict[str, dict[str, str]]]:
    """Read the board: subject (issue-<n>) -> role -> frontmatter (v3 s10).

    A subject is a docs/issue-<n>/ tree; role records sit in its reports/.

    이슈 #2432 (stage 4), 이슈 #2560 개정: 이 이슈에 로스터 lease 를 가졌던
    참가자 slug(옛 역할 축 브랜치가 쓰던 고정 `_sp.ROLES` 이름 자리)와 그
    밖의 frontmatter 있는 파일(새 스킬 축 브랜치가 쓰는 이름) 을 함께
    walk 해서 합친다 — 어느 쪽 네이밍으로 만들어진 레코드든 이 dict
    하나에 같이 나온다."""
    docs = root / _sp.BOARD
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
        lease_slugs = _sp._lease_slugs_for_issue(_sp._issue_num(d.name))
        skills = {r: _sp.frontmatter(rep / f"{r}.md") for r in lease_slugs
                 if (rep / f"{r}.md").is_file()}
        for name in _sp._skill_axis_report_names(rep):
            skills[name] = _sp.frontmatter(rep / f"{name}.md")
        if skills:
            found[d.name] = skills
    return found


def status(cwd: str) -> list[str]:
    """보드를 **읽는다**. 쓰지 않는다 (protocol.md §1).

    상태는 에이전트의 것이다. on-the-record 가 이걸 고치기 시작하면 룰북의 전이 게이트를
    우회하게 된다 — 게이트는 기록 쓰기를 가로채 막지만, 그 파일을 밖에서 고치면
    문지기를 안 거친다.
    """
    root = Path(cwd).resolve()
    out = [f"프로젝트: {_sp.slug(cwd)}   경로: {root}"]

    if not (root / _sp.MARKER).is_file():
        out.append(f"⚠ {_sp.MARKER} 없음 — 보드 opt-in 이자 승인자 allowlist 다. "
                   f"`spawn.py init` 으로 만든다.")
    b = _sp.board(root)
    if b:
        for subject, skills in b.items():
            out.append(f"subject: {subject}")
            # 이슈 #2560: 옛 고정 `_sp.ROLES` 튜플 대신, 이 이슈에 실제로
            # 로스터 lease 를 가졌던 참가자 slug 집합만 돈다 — roster entry
            # 가 없는 이슈는 여기서 빈 집합이 되어 "43개 중 몇 개 없음" 줄이
            # 더 이상 나오지 않는다 (docs/issue-2548/reports/architecture.md,
            # Step E).
            lease_slugs = _sp._lease_slugs_for_issue(_sp._issue_num(subject))
            for r in sorted(lease_slugs):
                fm = skills.get(r)
                if fm is None:
                    continue
                bits = [f"loop_state: {fm.get('loop_state', '(없음)')}"]
                if fm.get("verdict"):          # feasibility. coding 이 여기 깨어난다(§3)
                    bits.append(f"verdict: {fm['verdict']}")
                # 이슈 #2593: bracket 이 record 파일명(과거 role 이름을
                # 포함해 무엇이든 될 수 있다)을 담고, 그게 --skills 에
                # 넣을 스폰 가능한 스킬 이름과 같은 것으로 읽혔다 -- 실제
                # 사고 사례(이슈 #2593 본문 인용). `record:` 접두어는
                # 이 줄이 과거 기록 파일을 가리킨다는 것만 밝힌다 -- 무엇을
                # --skills 에 타이핑해야 하는지는 여기서 답하지 않는다
                # (그 답은 `spawn.py --skills` 자체의 도움말과
                # `consult.md` 가 가리키는 skill-repository 디렉터리
                # 목록이며, 닫힌 이름 목록을 board.py 에 다시 들여오지
                # 않는다 -- #2139 컨설트가 이미 기각한 모양).
                out.append(f"  [record: {r}] " + "   ".join(bits))
            # 이슈 #2432/#2560: 이 이슈의 lease slug 집합 밖 이름(스킬 축
            # 네이밍으로 만들어진 레코드, 또는 lease 가 이미 로스터에서
            # 지워진 뒤에도 남은 레코드) 도 같은 줄 형식으로 보여준다 —
            # 안 그러면 그런 레코드가 `board()` 에는 잡히는데 사람이 읽는
            # 이 목록에서는 조용히 사라진다.
            for r in sorted(r for r in skills if r not in lease_slugs):
                fm = skills[r]
                bits = [f"loop_state: {fm.get('loop_state', '(없음)')}"]
                if fm.get("verdict"):
                    bits.append(f"verdict: {fm['verdict']}")
                out.append(f"  [record: {r}] " + "   ".join(bits))
            missing = [r for r in sorted(lease_slugs) if r not in skills]
            if missing:
                out.append(f"  (기록 없음: {', '.join(missing)})")
        return out

    # 보드가 없다. "아무 일도 없다"와 "옛 자리에 있다"는 정반대 처분을 받아야 한다.
    stale = sorted(name for name in _sp.LEGACY_FILES
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
    sys.path.insert(0, str(_sp.ROOT / "gates"))
    try:
        import ci, gates
        # 비교 기준을 레포에서 찾는다. origin/main 을 고정하면 기본 브랜치가
        # master·develop 인 레포에서 매번 "검사 불가"가 뜨고, 그러면 게이트가
        # 있으나 마나가 된다.
        gates.BASE = os.environ.get("GATE_BASE") or _sp._base(cwd)
        bad = ci.check(Path(cwd).resolve())
        # 이슈 #2543: `requirement_registry()`가 `continue`로 건너뛰는
        # UNVERIFIABLE 항목은 `bad`(위)에 안 들어간다 — 그래서 여기, 같은
        # 게이트 리포트 안에 별도 줄로 항상 낸다. `bad` 가 비어도(즉
        # "[게이트] 이상 없음" 이어도) 이 줄은 낸다 — 조용한 통과와
        # "3 of 4 UNVERIFIABLE" 는 다른 결과다.
        req_summary = gates.requirement_registry_unverifiable_summary(
            Path(cwd).resolve(), {})
    except Exception as e:                       # git 아님, base 부재, import 실패 등
        return [f"[게이트] 검사 불가 — {type(e).__name__}: {str(e)[:120]}"]
    report = (["[게이트] 이상 없음"] if not bad else
              ["[게이트] 확인 필요:"] + [f"  - {b}" for b in bad])
    return report + [f"  ({req_summary})"]


# issue #2719: this used to carve out `spikes/` and `postmortems/` by
# testing `role == "technical-feasibility"` / `role == "release-
# engineering"` — a 2-name closed-set membership test, the retired
# role-catalog dispatch shape reproduced under skill identity (issue
# #2626 finding A). The fact this branch actually needs is not "which
# role wrote it" but "is this path shape a recognized alternate
# own-record convention distinct from `<role-or-slug>.md`" — a path-only
# signal with no identity read at all. `ALT_RECORD_SUBDIRS` names that
# convention once, independent of any role/skill name, and the two
# subdirectories are exempted for whichever role writes to them, not
# just the two that historically did. Stated behavior change: a role
# other than technical-feasibility/release-engineering writing to
# `spikes/` or `postmortems/` is no longer flagged either (previously it
# was, same as any other role writing outside its own record). Verified,
# not assumed: `git log --all --diff-filter=A -- 'docs/issue-*/reports/
# spikes/*' 'docs/issue-*/reports/postmortems/*'` returns zero commits in
# this repo's history — no role, including the two that were named here,
# has ever actually written to either subdirectory, so this widening has
# reclassified no real write; see test/test_board_ownership_report.py for
# the pinned before/after cases.
ALT_RECORD_SUBDIRS = ("spikes/", "postmortems/")


def ownership_report(cwd: str, skill: str, delta: list) -> list[str]:
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
        if rest == f"{skill}.md" or rest.startswith(f"{skill}/"):
            continue
        if rest.startswith(ALT_RECORD_SUBDIRS):
            continue
        bad.append(f"  - {p} (다른 역할의 기록)")
    if not bad:
        return []
    return [f"[소유권] {skill} 이 자기 것이 아닌 보드 경로를 건드렸다 — "
            f"세션 안의 게이트가 안 돌았다는 뜻이다 (계약 §11):"] + bad


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


def _session_commit_count(cwd: str, before_head: str | None, after_head: str | None) -> int:
    """`before_head`~`after_head` 사이에 실제로 쌓인 커밋 개수 —
    `_is_new_commit()` 과 같은 (before_head, after_head) 랜드마크를 쓰지만
    bool 이 아니라 count (이슈 #2193). dead 세션이 committed-but-unpushed
    상태로 죽었을 때 복구 신호에 "커밋 몇 개"를 실어 보내는 용도 — PR 이
    없는 죽은 세션은 push 자체가 안 됐다는 뜻이라, 이 새 커밋 개수가 곧
    unpushed 커밋 개수와 같다."""
    if not _is_new_commit(cwd, before_head, after_head):
        return 0
    rng = f"{before_head}..{after_head}" if before_head else after_head
    c = subprocess.run(
        ["git", "-C", cwd, "rev-list", "--count", rng],
        capture_output=True, text=True,
    )
    if c.returncode != 0:
        return 0
    try:
        return int(c.stdout.strip())
    except ValueError:
        return 0


def board_snapshot(cwd: str) -> dict[str, str]:
    """보드 파일들의 내용 해시. 세션 전후를 비교해 §6 의 '바뀐 보드'를 잰다.

    git 이 아니라 파일 내용을 재는 이유: 세션이 커밋했든 안 했든 바뀐 것은
    바뀐 것이고, 계약 §6 의 단위는 커밋이 아니라 보드다.
    """
    base = Path(cwd).resolve()
    docs = base / _sp.BOARD
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
    m = _sp._NULL_RESULT_RE.search(text)
    if not m:
        return None
    state = m.group("state")
    if state not in _sp.REGISTERED_NULL_RESULT_STATES:
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
    if _sp._null_result_declared(result) is not None:
        return "refused-null-result"
    return "silent-failure"


def _ledger_log_outcomes() -> dict[str, str]:
    """`runs/ledger.jsonl` 을 `{log 경로: 마지막 outcome}` 으로 접는다.
    파일이 없으면 빈 dict — clean 은 ledger 없이도 동작해야 한다(빈 상태)."""
    p = _sp.ROOT / "runs" / "ledger.jsonl"
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
    alive_fn = _sp._alive if alive_fn is None else alive_fn
    events_path = _sp._events_path(work)
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
        if silent_min > _sp.WATCHDOG_SILENCE_MIN:
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
    sys.path.insert(0, str(_sp.ROOT / "gates"))
    import recovery_policy
    return recovery_policy


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
    alive = _sp._alive(pid)
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
    ws_key = f"{_sp._repo_identity(work)}/{key}" if work else key
    ws_entry = ws_idx.get(ws_key)
    watcher_pid = ws_entry.get("watcher_pid") if ws_entry else None
    skill = key.split("/", 1)[1] if "/" in key else None
    if watcher_pid is None:
        lines.append("               워처: UNWATCHED")
    elif not alive:
        # 이슈 #1462 requirement 4: 세션이 정상 종료해서 이 행 자체가 이미
        # ENDED 이면, 워처의 by-design 동반 종료를 DEAD 로 오라벨하지
        # 않는다 — 그건 세션이 살아있는데 워처만 죽은 경우의 라벨이다.
        lines.append(f"               워처: exited-with-session (pid {watcher_pid})")
    elif _sp._watcher_looks_real(watcher_pid, e.get("issue"), skill):
        armed_at = ws_entry.get("watcher_armed_at")
        armed_mins = (int(now) - int(armed_at)) // 60 \
            if armed_at is not None else "?"
        own_sid = os.environ.get(_sp.ORCHESTRATOR_SESSION_ID_ENV) or None
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
    """돌고 있는 세션들. 죽은 항목은 표시 후 정리한다.

    이슈 #559: 각 살아있는 세션마다 붙은 워처(있으면)를 함께 보여준다 —
    "워처가 무장됐는지 죽었는지 바깥에서 알 방법이 없다"는 관찰에 대한
    응답. `ROSTER`(`issue-<n>/<role>` 키)와 `WORKSPACE_INDEX`(레포 접두사
    포함 키)를 `_watch`/`watchdog_check_one`과 같은 방식으로 조인한다.

    이슈 #2203: 로스터 파일을 못 읽거나 못 파싱하면(권한 오류, 또는 쓰기
    도중 읽은 절반짜리 내용) 예전엔 그냥 빈 딕셔너리로 흡수돼 "돌고 있는
    역할 세션 없음"과 구분 없이 찍혔다 — 이 빈 출력이 두 차례 실제로
    살아있는 세션을 "죽음"으로 오판해 그 위에서 강제 push/merge, git
    stash 같은 파괴적 조치를 부른 원인이었다. 이제 그 실패를
    `_roster_load_checked()` 로 구분해 "확인 불가"로 명시하고, 로스터
    read/write 자체는 멀쩡해도 로스터에 없는 살아있는 세션이 있을 수
    있다는 걸 스폰-클레임(별도 진실원, 스폰 거부 경로가 신뢰하는 것과
    같은 파일)과 교차 확인해 불일치를 알린다 — 로스터가 아는 것만 보여주고
    나머지를 조용히 빠뜨리지 않는다. 클레임 스캔 자체가 못 미더웠으면
    (베이스 디렉터리 스캔 실패, 개별 클레임 파일 파싱 실패) 그것도
    `claim_warnings` 로 그대로 드러낸다 — silent-failure 감사 발견:
    클레임 쪽 스캔 실패를 조용히 빈 결과로 흡수하면, 로스터 실패를 감추던
    것과 같은 모양의 구멍이 클레임 쪽에도 그대로 남는다."""
    d, load_error = _sp._roster_load_checked()
    claim_only, claim_warnings = _sp._claim_only_live_sessions(d)
    for warning in claim_warnings:
        print(f"경고: {warning} — 이 파일이 가리켰을 살아있는 세션을 놓쳤을 수 있다")
    if load_error is not None:
        print(f"돌고 있는 역할 세션: 확인 불가 — 로스터 파일을 읽지 못함({load_error})")
        print("               이 결과를 '세션 없음'으로 읽지 마라 — 로스터 자체가 신뢰 불가 상태다.")
        if claim_only:
            print("               스폰 클레임으로 발견된 살아있는 세션(로스터 미확인):")
            for work, pid in claim_only:
                print(f"               claim-only  pid {pid}  work: {work}")
        return 2
    if not d and not claim_only and not claim_warnings:
        print("돌고 있는 역할 세션 없음")
        return 0
    ws_idx = _sp._workspace_index_load()
    dead = []
    for key, e in sorted(d.items()):
        alive, lines = _sp._format_roster_row(key, e, ws_idx)
        for line in lines:
            print(line)
        if not alive:
            dead.append(key)
            work = e.get("work")
            # 이슈 #2193: 이 엔트리는 이 루프가 끝나면 아래 roster_remove()
            # 로 지워진다 — plugin reload 로 워처 자신까지 함께 죽어
            # `ensure_pushed()`(spawn.py:3073)가 못 돈 세션은, 그 삭제가
            # 곧 "커밋은 있는데 push/PR 도 없이 흔적도 없이 사라짐"이었다
            # (실측: 이슈 #2185/#2186/#2187). `_format_roster_row()`
            # 자신은 순수-무부수효과 계약이 있어(이슈 #1462,
            # test_ps_state_rows.py 가 합성 work 경로로 그 계약을 지킨다)
            # git/gh 호출을 못 넣는다 — 지우기 직전인 여기서, 실제
            # 워크스페이스가 있을 때만 diagnose_health() 로 한 번 더
            # 진단해 recovery 신호를 찍는다.
            if work and Path(work).is_dir():
                commit_count = _sp._session_commit_count(
                    work, e.get("before_head"), _sp._git_head(work))
                health = _sp.diagnose_health(key, e, root=Path(work),
                                          commit_count=commit_count)
                if health["state"] not in (None, "DEAD-ERRORED"):
                    print(f"               health: {health['state']} — "
                          f"{health['detail']}")
    for k in dead:
        _sp.roster_remove(k)
    if claim_only:
        print("경고: 스폰 클레임은 살아있는데 로스터엔 없는 세션 발견(로스터와 불일치, 이슈 #2203):")
        for work, pid in claim_only:
            print(f"               claim-only  pid {pid}  work: {work}")
    return 2 if claim_warnings else 0

