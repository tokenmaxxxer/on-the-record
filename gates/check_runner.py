#!/usr/bin/env python3
"""결정적 체크러너 — 이슈의 `## Acceptance` 절에 있는 실행가능한
검사(test/grep/file-existence)를 PR 브랜치에 대해 실제로 실행하고,
구조화된 결과를 PR 코멘트 하나로 남긴다(issue-1323 req 2).

LLM 세션이 아니라 기계 단계다 — 판단(judgment)이 필요한 검사는 이
러너의 범위 밖이며, 조용히 건너뛰지 않고 명시적으로 거부한다.

issue #2233: 검사는 `--repo`(기본 `.`)가 아니라 **PR 의 head 커밋**을
기준으로 실행된다 — `--repo`는 여전히 `gh` 호출(코멘트 게시, PR 메타데이터
조회)이 도는 오케스트레이터 체크아웃일 뿐이다. `checkout_pr_worktree()`가
그 체크아웃에서 PR head 를 fetch 해 임시 `git worktree` 로 떼어내고,
검사는 거기서 돈다 — 오케스트레이터 체크아웃 자체를 건드리지(브랜치를
바꾸지) 않는다.

issue #2313: `--repo`는 "**이 PR/이슈가 속한** 저장소의 체크아웃"이다 —
`gh_rest.fetch_issue_body()`도 `post_comment()`도 그 경로를 `cwd`로 `gh`를
부르므로, `gh`가 원격을 그 경로의 git remote 에서 읽는다. on-the-record
자신의 PR을 orchestrate 할 땐 그게 이 플러그인 체크아웃(directive 색인이
`${CHECKOUT}`로 부르는 경로)과 같지만, **target-repo**(소비 저장소) 작업을
orchestrate 할 땐 절대 `${CHECKOUT}`이 아니라 그 소비 저장소의 체크아웃이어야
한다 — `${CHECKOUT}`을 그대로 쓰면 이 플러그인 저장소에서 같은 번호의(대개
없거나 무관한) 이슈를 읽어 "Acceptance 절이 없다"로 잘못 거부한다.

  python3 gates/check_runner.py <pr-number> <issue-number> [--repo <이슈/PR이 속한 저장소 체크아웃, 기본 '.'>]
"""
from __future__ import annotations
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import check_run_artifact as cra  # noqa: E402
import gh_rest  # noqa: E402
sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn  # noqa: E402

ARTIFACT_PATH = Path(".on-the-record/check-run-artifact.json")

# issue #2233: check-runner 결과 코멘트의 "실행가능한 검사가 없다" 마커.
# 숫자 헤더(`_RESULT_HEADER`, merge_gate.py)와 겹치지 않는 별도 문구라야
# `0/0 passed`(빈 목록의 우연한 통과)와 구조적으로 구분된다.
NO_CHECKS_MARKER = "## Acceptance check-runner result: no checks declared"

# acceptance_gate.py 의 실행가능-산출물 admission 정규식과 같은 계열:
# 백틱으로 감싼 test/gates 경로, 또는 'check:'/'gate:' 줄.
_SECTION_HEADING = re.compile(r"(?im)^#{1,6}\s*acceptance\b.*$")
_NEXT_HEADING = re.compile(r"(?m)^#{1,6}\s")
_CHECK_LINE = re.compile(
    r"^\s*[-*]?\s*(?:check|gate)\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_BACKTICK_CMD = re.compile(r"`([^`]+)`")
_GREP_PREFIXED = re.compile(r"^\s*grep\s*:\s*(.+)$", re.IGNORECASE)


def _acceptance_section(body: str) -> str | None:
    m = _SECTION_HEADING.search(body)
    if not m:
        return None
    rest = body[m.end():]
    nxt = _NEXT_HEADING.search(rest)
    return rest[: nxt.start()] if nxt else rest


# 이슈 #2073: 인터프리터 허용목록. `node`/`npx`/`deno`/`bun` 이 빠져 있어
# `check: `node --check dist/bundle.js`` 가 `file-existence` 로 분류됐다 —
# 즉 "dist/bundle.js 라는 이름의 파일이 있는가"만 보고 명령은 한 번도
# 실행되지 않았다. 정확히 tm-dicequest#44 가 초록으로 통과한 경로다.
INTERPRETERS = ("python3", "python", "bash", "sh", "pytest",
                "node", "npx", "deno", "bun")

# issue #2231 residual gap (from #2233's closing comment, PR #2222 live
# case): a `check:` bullet naming a script in backticks incidentally,
# while the actual criterion is a comparative/quantitative MEASUREMENT
# ("an 8KB heredoc write ... completes in a time comparable to a 1KB
# one — measured, with both numbers in the record", issue #2210) is not
# a file-existence check — the file existing proves nothing about the
# claim. Falling through to `file-existence` mechanically asserted a
# claim the bullet never made and FAILed a correct PR (PR #2222) for a
# reason unrelated to its substance. When this language is present
# alongside a backtick that doesn't already look like an executable
# command, classify as `judgment` instead — the measurement is real but
# not mechanically checkable; requirement_met.py's semantic layer grades
# it now that prose criteria reach it (issue #2231 defect 1).
_MEASUREMENT_LANGUAGE = re.compile(
    r"(?i)\b(measured?|measuring|comparable\s+to|completes?\s+in\s+a?\s*"
    r"time|regression\s+guard|unchanged\s+on|latency|throughput|duration|"
    r"benchmark(?:ed)?|median|percentile)\b")

# issue #2278: check_runner 의 classifier 기본값 반전. 백틱 안 내용이 명령도
# 아니고 measurement 언어도 아니면 예전엔 무조건 file-existence 로 떨어져
# `cross_family`(이슈 #2213/PR #2255), `work-in-english`(이슈 #2208/PR #2218)
# 같은 맨 식별자/스킬명까지 "그 이름의 파일이 없다"며 FAIL 시켰다 — 둘 다
# 기록에서 실행으로 검증된 정답 PR이었다. `/`를 포함하거나 알려진 확장자로
# 끝나는(경로 '모양'인) 백틱만 file-existence 로 남긴다 — 진짜로 없는
# 경로모양 산출물은 여전히 FAIL 한다; 아니면 judgment 로 강등한다.
_PATH_EXTENSIONS = {
    "py", "js", "jsx", "ts", "tsx", "md", "json", "yml", "yaml", "toml",
    "txt", "sh", "cfg", "ini", "go", "rs", "rb", "java", "c", "cpp", "h",
    "hpp", "css", "html", "xml", "sql", "csv", "lock", "env",
}

# issue #2278 hunt finding: bare conventional filenames have no extension
# but are still real paths — without this, `check: \`LICENSE\`` would
# wrongly downgrade to judgment instead of genuinely FAILing when absent.
_BARE_PATH_NAMES = {
    "LICENSE", "README", "CHANGELOG", "Makefile", "Dockerfile",
    "Procfile", "Gemfile", "Rakefile", "Vagrantfile", "Jenkinsfile",
}

# issue #2313: `cd frontend && node scripts/check-hex-tokens.mjs` 류 compound
# 셸 명령. 분류는 마지막 세그먼트(실제로 실행되는 명령)로 해야 한다 — 앞
# 세그먼트의 첫 토큰(`cd`)은 인터프리터 허용목록에도 없고 경로 확장자도
# 없어, 예전엔 전체 문자열이 `_looks_like_path`(안에 `/`가 있으니)로
# 떨어져 file-existence 오분류를 냈다: 명령이 한 번도 실행되지 않고
# "그 이름의 파일이 있는가"만 봤다(#2278 의 non-path 반전은 토큰 자체가
# `/`를 담은 이 모양을 못 잡는다). `run_checks`도 같은 정규식으로 compound
# 여부를 봐서 `shell=True`로 돈다 — `cd`는 별도 프로세스로 exec 할 수
# 없는 셸 내장이라 shlex.split 인자열로는 절대 성공하지 않는다.
_COMPOUND_SEP = re.compile(r"&&|;")

# issue #2463: `issue-<n>/<role>` 류 각괄호 placeholder. 서술문
# ("~is mapped to `issue-<n>/<role>` subject" 같은 naming-convention
# 언급)이 우연히 `/`를 담은 백틱을 갖고 있으면 `_looks_like_path`가 그걸
# 실재 경로로 오인해 file-existence 로 떨어뜨렸다 — 리터럴 `issue-<n>`은
# 디스크에 있을 수 없는 문자열이니 항상 FAIL 한다(이 세션에서 9번 실측:
# 이슈 #2402 PR #2446/#2456의 진짜 Acceptance 문장 포함). `<...>` placeholder
# 를 담은 토큰은 절대 실재 파일명일 수 없으므로 무조건 judgment 로
# 내린다 — 진짜 존재하는 경로 백틱(placeholder 없음)의 FAIL 판정은
# 그대로 유지된다.
_ANGLE_PLACEHOLDER = re.compile(r"<[^\s<>]+>")

# issue #2509 (#2463 의 잔여 결함): #2463 는 각괄호 placeholder 만 뺐다 —
# 백틱 토큰이 *다른 어딘가*(설치된 플러그인 자신의 디렉터리, target/소비
# 저장소의 로컬 레이아웃)에 있는 실재 경로를 가리켜도 진짜 `/`를 담고
# 있어 여전히 "이 저장소에 이 경로가 있어야 한다"로 읽혔다. 라이브
# 재현(이슈 #2488, PR #2497/#2499/#2500): "설치된 플러그인의 `skills/`"에서
# 스킬 이름이 풀리는지를 묻는 불릿과 "target repo 의 로컬 `.claude/skills`"를
# 언급하는 불릿 둘 다, 두 경로 어느 쪽도 있다고 주장한 적 없는 저장소에서
# 기계적으로 FAIL 했다. 신호는 텍스트 기반이어야지 존재-여부 기반이면 안
# 된다(존재 여부로 판정하면 분류기가 자기참조적이 되고, "진짜로 없는
# in-repo 경로는 여전히 FAIL 해야 한다"는 non-goal 을 깬다) — 백틱 바로
# 앞의 명시적 foreign-owner 소유격("installed plugin's", "target repo's" 등)은
# 그 불릿이 "여기 있다"를 주장하는 게 아니라 "다른 곳에 있다"를 설명하고
# 있다는 뜻이다.
_FOREIGN_OWNER = re.compile(
    r"(?i)\b(?:installed|target|another|other|downstream|external|"
    r"consuming|third-party)\s+(?:plugin|repo(?:sitory)?)'s\b")
# 창을 일부러 짧게 잡는다 — 백틱 *바로 앞*에서 그 토큰의 소유자를 이름하는
# 소유격만 쳐준다. 긴 불릿 앞부분에서 다른 대상을 두고 언급한 foreign-owner
# 구절이 뒤로 새어나가 문장 뒤쪽의 무관한, 진짜 로컬 경로를 삼키면 안 된다.
_FOREIGN_OWNER_WINDOW = 60

# issue #2509: 불릿 텍스트가 stating/demonstrating 동사로 시작하면 그건
# 실행할 명령이 아니라 무엇을 보여주거나 문서화해야 하는지를 말하는
# 서술문이다 — 같은 불릿 뒤쪽 백틱이 무엇처럼 생겼든 상관없다
# (`.claude/skills` 는 아래 `looks_like_command`엔 compound 경로형 명령
# 토큰으로 읽힌다). 라이브 재현: "state explicitly what trust distinction
# ... a target repo's local `.claude/skills`"가 `test`로 분류돼, 원래
# 실행할 뜻이 전혀 없던 셸 명령으로 돌아갔다.
_STATING_VERB_PREFIX = re.compile(
    r"(?i)^\s*(?:state\s+explicitly|demonstrate\s+live|document)\b")


def _final_segment(cmd: str) -> str:
    parts = _COMPOUND_SEP.split(cmd)
    return parts[-1].strip() if len(parts) > 1 else cmd


def _looks_like_path(token: str) -> bool:
    if _ANGLE_PLACEHOLDER.search(token):
        return False
    if "/" in token:
        return True
    if token in _BARE_PATH_NAMES:
        return True
    if token.startswith(".") and len(token) > 1:
        return True
    if "." in token:
        return token.rsplit(".", 1)[-1].lower() in _PATH_EXTENSIONS
    return False


def parse_checks(section: str,
                 runtime_artifacts: list[str] | None = None) -> list[dict]:
    """Acceptance 절 텍스트에서 각 `check:`/`gate:` 줄을 뽑아 분류한다.

    분류: `artifact-smoke`(이슈 #2073 — 백틱 안 명령이 허용목록 동사로
    시작하면서 선언된 런타임 산출물 하나를 argv 에서 이름함), `test`
    (백틱 안이 실행가능 shell/pytest/node 계열 명령), `grep`(`grep:`
    접두 패턴), `file-existence`(백틱 안이 명령이 아니라 맨 파일 경로),
    `judgment`(무엇에도 해당하지 않음 — 실행 거부 대상).

    `runtime_artifacts` 는 이슈 본문의 `runtime-artifacts:` 선언
    (`gates/artifact_smoke_rule.py`)이다. None/빈 목록이면
    `artifact-smoke` 분류는 아예 일어나지 않는다 — 선언이 없는 이슈의
    분류 결과는 오늘과 바이트 단위로 같다.
    """
    declared = list(runtime_artifacts or [])
    checks = []
    for m in _CHECK_LINE.finditer(section):
        raw = m.group(1).strip()
        gm = _GREP_PREFIXED.match(raw)
        if gm:
            checks.append({"type": "grep", "raw": raw, "pattern": gm.group(1).strip()})
            continue
        bm = _BACKTICK_CMD.search(raw)
        if bm:
            cmd = bm.group(1).strip()
            classify_cmd = _final_segment(cmd)
            tokens = classify_cmd.split()
            # issue #2313: the artifact-touch check keys off the first
            # token too (`artifact_smoke_rule.command_touches_artifact`) —
            # same compound-command blind spot as the classifier below, so
            # it gets the same final-segment fix.
            artifact = _artifact_touched(classify_cmd, declared) if declared else None
            if artifact is not None:
                checks.append({"type": "artifact-smoke", "raw": raw,
                                "command": cmd, "artifact": artifact})
                continue
            looks_like_command = bool(tokens) and (
                "/" in tokens[0] and tokens[0].count(".") >= 1
                or tokens[0] in INTERPRETERS
            )
            # issue #2509: stating/demonstrating 불릿은 서술문이지 실행할
            # 명령이 아니다 — 그 안 백틱이 명령 토큰 모양(`dir/name`)이라도
            # 마찬가지다(위 looks_like_command 는 `cd` 없는 compound 상대
            # 경로 명령과 이 모양을 구별 못 한다).
            if _STATING_VERB_PREFIX.match(raw):
                looks_like_command = False
            is_foreign_owned = bool(_FOREIGN_OWNER.search(
                raw[:bm.start()][-_FOREIGN_OWNER_WINDOW:]))
            if looks_like_command:
                # issue #2233: 이 저장소가 실제로 가장 흔히 쓰는 형태 —
                # 인터프리터 접두 없는 bare `.py` 경로 하나짜리
                # (`gate: \`tests/test_x.py\``, 이슈 #2215/#2214/#2217이
                # 전부 이 모양). 셔뱅/실행권한 없는 게 정상인 테스트
                # 파일을 직접 exec 하면 실행권한 오류로 항상 FAIL 처리되고
                # 실제로는 한 번도 실행되지 않는다 — PR #2223 라이브
                # 실행에서 실측됨. `pytest`로 감싸 진짜로 돈다.
                if (len(tokens) == 1 and classify_cmd.endswith(".py")
                        and tokens[0] not in INTERPRETERS):
                    wrapped = f"python3 -m pytest {classify_cmd}"
                    if classify_cmd != cmd:
                        prefix = cmd[: cmd.rfind(classify_cmd)]
                        cmd = f"{prefix}{wrapped}"
                    else:
                        cmd = wrapped
                checks.append({"type": "test", "raw": raw, "command": cmd})
            elif _MEASUREMENT_LANGUAGE.search(raw):
                checks.append({"type": "judgment", "raw": raw})
            elif is_foreign_owned:
                checks.append({"type": "judgment", "raw": raw})
            elif len(tokens) == 1 and _looks_like_path(classify_cmd):
                # issue #2509: file-existence 판정은 원래 경로 하나에 대한
                # 것이지 여러 단어짜리 문자열이 아니다 — 이 분기가 다중
                # 토큰 `classify_cmd`로 오는 경우는 위 stating-verb 억제가
                # 명령 모양의 첫 토큰을 `test`에서 빼낸 경우뿐이다. 토큰
                # 개수 가드가 없으면 그 남은 다중 단어 문자열("gates/x.py
                # --flag" 같은)이 하나의 가짜 리터럴 경로로 기계적으로
                # "검사"돼 버린다.
                checks.append({"type": "file-existence", "raw": raw, "path": classify_cmd})
            else:
                checks.append({"type": "judgment", "raw": raw})
            continue
        checks.append({"type": "judgment", "raw": raw})
    return checks


def _artifact_touched(command: str, declared: list[str]) -> str | None:
    """`artifact_smoke_rule` 의 판정을 그대로 쓴다 — 허용 동사/경로 매칭
    규칙이 두 군데로 갈라지면 게이트가 거부한 형태를 러너가 실행하는
    (혹은 그 반대의) 어긋남이 생긴다. 모듈을 못 불러오면 분류를 포기하고
    오늘의 경로로 떨어진다(fail-open — 여기서 막을 일이 아니다)."""
    try:
        import artifact_smoke_rule
    except Exception:
        return None
    return artifact_smoke_rule.command_touches_artifact(command, declared)


class JudgmentCheckError(Exception):
    """A check could not be classified as test/grep/file-existence."""


def run_checks(repo: Path, checks: list[dict]) -> list[dict]:
    """`checks`를 `repo`(PR 브랜치 체크아웃) 기준으로 실제 실행한다.

    `judgment` 타입은 실행하지 않고 명시적 에러를 낸다 — 이 러너는
    기계적으로 판정 가능한 검사만 다룬다.
    """
    results = []
    for chk in checks:
        kind = chk["type"]
        if kind == "judgment":
            raise JudgmentCheckError(
                f"판단이 필요한 검사는 체크러너 범위 밖이다: {chk['raw']!r}")
        if kind in ("test", "artifact-smoke"):
            # issue #2233: PR 워크트리에 실제로 있는 파일이라도 실행권한이
            # 없는 `.py` 검사 파일(인터프리터 접두 없는 bare 경로, 이
            # 저장소의 흔한 `gate: \`tests/test_x.py\`` 관용구)을 직접
            # exec 하면 `PermissionError`가 난다 — 블로커 2를 고친 뒤
            # 실제 PR(issue-2215/#2223)에 대해 돌려보다가 실측한 두 번째
            # 크래시 경로. 이런 OS 레벨 실행 실패는 "이 검사가 실패했다"는
            # 결과일 뿐 러너 전체가 죽을 이유가 아니다.
            try:
                # issue #2313: `cd X && CMD`/`cd X; CMD` — `cd`는 셸 내장이라
                # argv 로 직접 exec 할 수 없다. compound 명령만 `shell=True`로
                # 돈다; 단순 명령은 지금까지처럼 shlex 로 토큰화해 셸을 거치지
                # 않는다(범위를 넓히지 않는다).
                if _COMPOUND_SEP.search(chk["command"]):
                    r = subprocess.run(chk["command"], shell=True, cwd=repo,
                                        capture_output=True, text=True)
                else:
                    r = subprocess.run(shlex.split(chk["command"]), cwd=repo,
                                        capture_output=True, text=True)
                status = "pass" if r.returncode == 0 else "fail"
                output = (r.stdout + r.stderr)[-2000:]
            except OSError as e:
                status = "fail"
                output = f"검사 명령을 실행할 수 없다: {e}"
            entry = {
                "check": chk["raw"], "type": kind, "command": chk["command"],
                "status": status,
                "output": output,
            }
            if kind == "artifact-smoke":
                entry["artifact"] = chk["artifact"]
            results.append(entry)
        elif kind == "grep":
            r = subprocess.run(
                ["grep", "-r", "--exclude-dir=.on-the-record", chk["pattern"], "."],
                cwd=repo, capture_output=True, text=True)
            results.append({
                "check": chk["raw"], "type": kind, "pattern": chk["pattern"],
                "status": "pass" if r.returncode == 0 else "fail",
                "output": r.stdout[-2000:],
            })
        elif kind == "file-existence":
            exists = (repo / chk["path"]).exists()
            results.append({
                "check": chk["raw"], "type": kind, "path": chk["path"],
                "status": "pass" if exists else "fail",
                "output": f"{chk['path']} {'exists' if exists else 'missing'}",
            })
        else:
            raise JudgmentCheckError(
                f"알 수 없는 검사 타입: {kind!r} ({chk['raw']!r})")
    return results


def format_comment(results: list[dict], skipped: list[dict] | None = None) -> str:
    """구조화된 마크다운 PR 코멘트 본문 하나를 만든다.

    `results`가 빈 목록이면(파싱된 `check:`/`gate:` 줄이 하나도 없음, 또는
    이슈 #2231 — 있었지만 전부 `judgment` 로 분류돼 기계적으로 돌릴 게
    없음) `format_no_checks_comment()`로 위임한다 — 예전엔 여기서
    `0/0 passed`를 찍었는데, `passed == total`(0==0)이 참이라
    `merge_gate.evaluate()`가 이걸 통과로 읽었다(issue #2233 empty-state
    결함). 빈 검사 목록은 이제 숫자 헤더 자체를 안 찍어 그 우연한 통과를
    구조적으로 막는다.

    `skipped`(issue #2231 잔여 결함 (a), #2233 종료 코멘트): `judgment`
    로 분류된 항목들 — 기계적으로 실행하지 않았지만 존재는 밝힌다.
    숫자 헤더의 분모/분자에는 안 들어간다(이 러너의 범위 밖이라
    pass/fail 판정 자체가 없다) — 채점은
    `gates/requirement_met.py`의 semantic 레이어 몫이다."""
    skipped = skipped or []
    if not results:
        return format_no_checks_comment(skipped)
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "pass")
    lines = [f"## Acceptance check-runner result: {passed}/{total} passed", ""]
    for r in results:
        mark = "PASS" if r["status"] == "pass" else "FAIL"
        lines.append(f"- [{mark}] ({r['type']}) {r['check']}")
    if skipped:
        lines.append("")
        lines.append(f"judgment (기계 실행 범위 밖, {len(skipped)}개 — "
                      "semantic 채점은 requirement_met.py 몫):")
        for s in skipped:
            lines.append(f"- {s['raw']}")
    return "\n".join(lines)


def format_no_checks_comment(judgment: list[dict] | None = None) -> str:
    """이슈의 `## Acceptance` 절에 기계적으로 실행 가능한 검사가 하나도
    없을 때 남기는 코멘트(issue #2233 empty-state). `NO_CHECKS_MARKER`로
    시작해 `merge_gate.parse_check_runner_result()`가 숫자 헤더와
    구조적으로 구분해 감지한다 — 이 결과를 통과로 취급하지 않는다.

    `judgment`(issue #2231 잔여 결함 (a)): `check:`/`gate:` 줄이 있긴
    있었지만 전부 `judgment` 로 분류된 경우 — 이 러너가 무엇을 왜 못
    돌렸는지 밝힌다. 생략하면(진짜로 줄이 0개) 예전과 바이트 단위로
    같은 문구를 낸다."""
    if not judgment:
        return (f"{NO_CHECKS_MARKER}\n\n"
                "이 이슈의 `## Acceptance` 절에 기계적으로 실행 가능한 "
                "`check:`/`gate:` 줄이 없다. 이것은 통과가 아니라 별개의 결과다 "
                "— 머지 게이트는 이걸 만족으로 취급하면 안 된다.")
    lines = [
        NO_CHECKS_MARKER, "",
        f"이 이슈의 `## Acceptance` 절에 있는 {len(judgment)}개 `check:`/"
        "`gate:` 항목이 전부 판단이 필요한(judgment) 기준이라 기계적으로 "
        "실행할 검사가 없다. 이것은 통과가 아니라 별개의 결과다 — 머지 "
        "게이트는 이걸 만족으로 취급하면 안 된다. semantic 채점은 "
        "`gates/requirement_met.py`가 담당한다:",
    ]
    for j in judgment:
        lines.append(f"- {j['raw']}")
    return "\n".join(lines)


def _pr_head_ref(repo: Path, pr: int) -> str | None:
    """PR 의 head 브랜치 이름 — `gh pr view`, `gates/ci.py:_pr_head_ref`와
    같은 모양(issue #2233). 여기서 별도로 두는 이유는 `ci.py`가
    `check_runner`를 불러오지 않아(순환 임포트 없음) 공유할 얇은 모듈이
    아직 없기 때문 — 두 곳 모두 이 정도로 작은 함수다."""
    r = subprocess.run(["gh", "pr", "view", str(pr), "--json", "headRefName"],
                        cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    import json
    try:
        return json.loads(r.stdout).get("headRefName")
    except ValueError:
        return None


def worktree_for_ref(repo: Path, ref: str) -> tuple[Path | None, str | None]:
    """`ref`(예: `origin/issue-<n>/<role>`, `repo`에 이미 존재하는 로컬
    git ref)를 임시 `git worktree`로 떼어낸다(issue #2233 블로커 2 — 검사가
    PR 코드가 아니라 오케스트레이터 체크아웃을 상대로 돌던 결함). 순수
    로컬 git 만 쓴다 — fetch 는 호출부(`checkout_pr_worktree`) 책임.
    `(worktree_path, None)` 또는 `(None, 에러메시지)`."""
    tmpdir = tempfile.mkdtemp(prefix="check-runner-pr-")
    # issue #2468: SIGKILL/하드크래시는 아래 `git worktree add`가 끝나기도
    # 전에, 또는 main() 의 try/finally(정상 종료 경로)에 닿기도 전에 이
    # 프로세스를 죽일 수 있다 — 그러면 이 디렉터리는 영원히 고아가 된다.
    # 소유 pid 를 지금 남겨 GC 스윕(`spawn.tmp_resource_sweep()`)이 나중에
    # 이 pid 생사만으로 지울지 말지 정할 수 있게 한다.
    spawn._record_tmp_resource(tmpdir, os.getpid(), "worktree")
    r = subprocess.run(["git", "worktree", "add", "--detach", tmpdir, ref],
                        cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return None, f"git worktree add 실패({ref}): {r.stderr.strip()}"
    return Path(tmpdir), None


def remove_worktree(repo: Path, worktree: Path) -> None:
    """`worktree_for_ref`가 만든 임시 worktree 를 되돌린다 — 실패해도
    조용히 넘어간다(정리 실패가 검사 결과를 뒤집으면 안 된다); 디렉터리는
    `git worktree remove`가 못 지워도 `shutil.rmtree`로 한 번 더 지운다."""
    subprocess.run(["git", "worktree", "remove", "--force", str(worktree)],
                    cwd=repo, capture_output=True, text=True)
    shutil.rmtree(worktree, ignore_errors=True)


def fetch_all_role_branches(repo: Path) -> subprocess.CompletedProcess:
    """issue #2381: 플레인 `git fetch origin`(또는 `git fetch origin
    <one-branch>`) 은 `repo`의 `remote.origin.fetch` 설정이 그 브랜치
    패턴을 포함하지 않으면 exit 0 으로 "성공"해도
    `refs/remotes/origin/<branch>` 를 만들거나 갱신하지 않는다 — 그러면
    막 스폰돼 push 된 `issue-<n>/<role>` 브랜치처럼 아직 로컬에 없는
    참조에 대해 아래 `worktree_for_ref`/`git worktree add
    origin/issue-<n>/<role>` 가 "fatal: invalid reference" 로 실패한다
    (실측: 이 문제를 매 세션 `git fetch origin
    '+refs/heads/*:refs/remotes/origin/*'` 로 손으로 우회해야 했다).
    목적지 refspec 을 명시한 전체-미러 fetch 로, `repo`에 설정된 refspec과
    무관하게 origin 의 모든 브랜치를 항상 로컬 `origin/*` 로 갱신한다 —
    `checkout_pr_worktree()`(check_runner.py 가 fetch 하는 유일한 지점)가
    호출하므로, 뒤이어 같은 `--repo` 체크아웃을 재사용하는
    `gates/merge_gate.py`(자체 fetch 없음)도 별도 처리 없이 최신
    `origin/*` 참조를 그대로 쓴다. `--prune` 필수(hunt finding, before-landing
    stance 0): prune 없이는 origin 에서 삭제된 브랜치의 로컬 `origin/<branch>`
    ref 가 stale 상태로 남아 fetch 가 exit 0 을 반환하고, 뒤이은
    `worktree_for_ref`/`git worktree add` 도 그 stale ref 로 조용히 성공해
    `checkout_pr_worktree()`의 fail-closed 계약(에러는 항상 거부)을 깬다 —
    `--prune` 은 삭제된 브랜치의 로컬 ref 를 제거해, 사라진 head 는 다시
    "fatal: invalid reference" 로 fail-closed 하게 만든다."""
    return subprocess.run(
        ["git", "fetch", "--prune", "origin",
         "+refs/heads/*:refs/remotes/origin/*"],
        cwd=repo, capture_output=True, text=True)


def checkout_pr_worktree(repo: Path, pr: int) -> tuple[Path | None, str | None]:
    """PR #`pr`의 head 커밋을 `repo`(오케스트레이터 체크아웃, `origin`
    리모트를 가짐)에서 fetch 해 임시 worktree 로 체크아웃한다(issue #2233).
    `(worktree_path, None)` 또는 `(None, 에러메시지)` — 에러는 항상
    fail-closed(호출부가 검사를 실행하지 않고 거부)로 다뤄진다."""
    head_ref = _pr_head_ref(repo, pr)
    if head_ref is None:
        return None, f"PR #{pr} 의 head 브랜치를 읽을 수 없다(`gh pr view` 실패)"
    fetch = fetch_all_role_branches(repo)
    if fetch.returncode != 0:
        return None, f"origin fetch 실패: {fetch.stderr.strip()}"
    return worktree_for_ref(repo, f"origin/{head_ref}")


def post_comment(pr: int, body: str, repo: Path) -> bool:
    """이 러너에서 유일하게 `gh`를 호출해 PR 에 코멘트를 남기는 함수."""
    r = subprocess.run(["gh", "pr", "comment", str(pr), "--body", body],
                        cwd=repo, capture_output=True, text=True)
    return r.returncode == 0


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: check_runner.py <pr-number> <issue-number> "
              "[--repo <이슈/PR이 속한 저장소 체크아웃, 기본 '.'>]")
        return 1
    pr, issue = int(sys.argv[1]), int(sys.argv[2])
    repo = Path(".").resolve()
    if "--repo" in sys.argv:
        repo = Path(sys.argv[sys.argv.index("--repo") + 1]).resolve()

    body = gh_rest.fetch_issue_body(repo, issue)
    if body is None:
        print(f"이슈 #{issue} 본문을 읽을 수 없다(`gh api repos/.../issues/{issue}` 실패)")
        return 1
    section = _acceptance_section(body)
    if section is None:
        print(f"이슈 #{issue}에 '## Acceptance' 절이 없다")
        return 1
    # 이슈 #2073: 선언이 있으면 산출물을 실제로 파싱/실행하는 검사를
    # `artifact-smoke` 로 분류해 실행한다. 선언이 없으면 None 이 넘어가
    # 오늘과 같은 분류 결과가 나온다.
    try:
        import artifact_smoke_rule as _asr
        runtime_artifacts = _asr.parse_declaration(body)
    except Exception:
        runtime_artifacts = None
    checks = parse_checks(section, runtime_artifacts)
    # issue #2231 residual gap (a), from #2233's closing comment: a
    # judgment-type check used to make `run_checks` raise and abort the
    # ENTIRE run before anything was executed or any comment posted — an
    # Acceptance section with even one judgment-shaped bullet alongside
    # otherwise-mechanical ones got zero PR feedback (PRs #2228/#2218
    # live examples). Judgment checks are out of this runner's scope by
    # design (that's the whole point of the type), so split them out
    # BEFORE calling `run_checks` — it only ever sees checks it can
    # actually run, and mechanical checks still get graded and posted
    # even when judgment ones are present.
    mechanical = [c for c in checks if c["type"] != "judgment"]
    judgment = [c for c in checks if c["type"] == "judgment"]

    # issue #2233 empty-state (issue #2231 확장: 있었지만 전부 judgment
    # 여도 같은 결과): 기계적으로 실행 가능한 검사가 하나도 없으면 PR
    # 코드를 체크아웃할 것도 없다 — 별개의 결과를 남기고 fail-closed
    # (0/0 이 "통과"로 읽히던 예전 경로를 없앤다).
    if not mechanical:
        comment = format_no_checks_comment(judgment)
        print(comment)
        post_comment(pr, comment, repo)
        return 1

    # issue #2233 블로커 2: PR 의 head 커밋을 임시 worktree 로 떼어내
    # 거기서 검사를 돈다 — `repo`(오케스트레이터 체크아웃)를 상대로 돌면
    # PR 이 새로 추가한 파일이 없어 `FileNotFoundError`로 죽는다.
    worktree, err = checkout_pr_worktree(repo, pr)
    if err is not None:
        print(f"거부: PR #{pr} 코드를 체크아웃할 수 없다 — {err}")
        return 1
    try:
        results = run_checks(worktree, mechanical)
        comment = format_comment(results, judgment)
        print(comment)
        post_comment(pr, comment, repo)

        exit_code = 0 if all(r["status"] == "pass" for r in results) else 1
        artifact = cra.build_artifact(
            command=f"check_runner.py {pr} {issue}", tier="fast", repo=worktree,
            check_results=results, exit_code=exit_code,
            produced_by="check_runner")
        cra.write_artifact(repo / ARTIFACT_PATH, artifact)
        return exit_code
    finally:
        remove_worktree(repo, worktree)


if __name__ == "__main__":
    sys.exit(main())
