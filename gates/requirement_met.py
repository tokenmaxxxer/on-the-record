#!/usr/bin/env python3
"""requirement-met verification — issue #1651 (northpole req#6).

이슈의 `## Acceptance` 절 `- check:` 불릿을 등급 매긴다. 파서는
`check_runner.parse_checks`(acceptance_gate 와 같은 계열의 section
추출 + check/gate 줄 파서)를 재사용한다 — 새로 만들지 않는다.

두 겹의 판정이 섞이지 않게 분리한다:
- **결정적** 아티팩트-존재 서브체크(artifact_in_diff)만 블록한다: 기준이
  YES 로 채점됐는데 그 기준이 인용한 아티팩트(백틱 경로/커맨드)가 PR
  diff 안에 없으면 실패. 이건 LLM 판단이 아니라 문자열 포함 검사다.
- **의미론적** verdict(YES/NO/UNKNOWN, builder-blind 세션이 매긴 것)는
  advisory 로만 기록된다 — 그 자체로는 절대 블록하지 않는다(연구 근거:
  LLM judge 는 게임 가능/편향 — 토큰 하나로 35% FP, 모듈 docstring 참고
  대신 이슈 본문에 있음).

`- check:` 불릿이 0개인 이슈(예: `unverifiable:` 로만 채워진 절)는
'no gradable criteria' 로 구분되는 결과를 낸다 — 크래시도 아니고 기존
게이트들의 결과와 바이트 단위로 같지도 않은, 별도 상태다.

  python3 gates/requirement_met.py <issue-number> <pr-number> [--repo <경로>]
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import acceptance_gate  # noqa: E402
import check_runner  # noqa: E402
import gh_rest  # noqa: E402

YES = "YES"
NO = "NO"
UNKNOWN = "UNKNOWN"

_ARTIFACT = re.compile(r"`([^`]+)`")

# issue #1696 — command-identity: an executed-live check must prove the
# EXACT installed/documented command surface it names, not a merely
# equivalent one (e.g. `python3 -m pkg.cli` proving a check that names
# the installed `python3 -m pkg` line — a real fake-success vector
# observed live, pilot-devdigest PR #6). `raw`'s own bullet text plus its
# indented continuation lines (`provenance:`/`empty state:`, per the
# ACCEPTANCE FORMAT convention — each metadata field on its own indented
# line under the `check:` bullet) carry the provenance; this regex pairs
# a `check:`/`gate:` bullet with those continuation lines so we can tell
# which checks are executed-live without re-parsing the whole section.
_CHECK_WITH_META = re.compile(
    r"^[ \t]*[-*]?[ \t]*(?:check|gate)[ \t]*:[ \t]*(?P<raw>.+?)[ \t]*$\n"
    r"(?P<meta>(?:^[ \t]+\S.*\n?)*)",
    re.IGNORECASE | re.MULTILINE)
_PROVENANCE_LINE = re.compile(
    r"provenance\s*:\s*(executed-live|executed-unit|read)", re.IGNORECASE)
# same citation shape gates/record_lint.py's _EXECUTED_LIVE_CANONICAL
# already recognizes as executed-live proof: `acceptance: <command> —
# result: PASS|FAIL|UNMEASURED`.
_ACCEPTANCE_CITATION = re.compile(
    r"acceptance\s*:\s*(.+?)\s*(?:—|-{1,2})\s*result\s*:\s*"
    r"(?:PASS|FAIL|UNMEASURED)\b", re.IGNORECASE)
_ENV_PREFIX = re.compile(r"^(?:[A-Za-z_][A-Za-z0-9_]*=\S+\s+)+")
_CD_PREFIX = re.compile(r"^cd\s+\S+\s*(?:&&|;)\s*", re.IGNORECASE)
_WRAPPER_PREFIX = re.compile(r"^(?:bash|sh)\s+-c\s+", re.IGNORECASE)


def _strip_env_prefix(cmd: str) -> str:
    """환경변수 접두(`PYTHONPATH=src `류)를 벗겨 첫-토큰 후보 매칭에
    쓴다 — PR #1699 리뷰 픽스(issue #1696): 최종 동일성 비교에는 이
    정규화를 쓰지 않는다. env-prefix 는 규칙이 명시적으로 금지하는
    크러치이므로, 접두 유무 차이 자체가 mismatch 로 잡혀야 한다."""
    return _ENV_PREFIX.sub("", cmd.strip()).strip()


def _strip_wrapper_head(cmd: str) -> str:
    """`cd <path> && `/`bash -c`류 헤드 크러치를 벗긴다 — PR #1699
    리뷰 픽스(issue #1696): 이런 헤드가 있으면 첫 토큰이 `cd`/`bash`가
    되어 후보 필터를 통째로 빠져나가 mismatch 판정이 조용히 스킵됐다.
    env-prefix 와 달리 cd/wrapper 헤드 자체는 동일성 비교에서도 벗겨서
    비교한다 — 실행 위치/셸 래핑은 커맨드 표면의 정체성이 아니다."""
    s = cmd.strip()
    s = _CD_PREFIX.sub("", s).strip()
    s = _WRAPPER_PREFIX.sub("", s).strip()
    if len(s) >= 2 and s[0] in "'\"" and s[-1] == s[0]:
        s = s[1:-1].strip()
    return s


def _provenance_map(section: str) -> dict[str, str]:
    """`raw` 체크 문구 -> provenance 값(lower-cased). 메타 줄이 없거나
    provenance 줄이 없으면 그 raw 는 매핑에 없다(= 판정 보류)."""
    result: dict[str, str] = {}
    for m in _CHECK_WITH_META.finditer(section):
        raw = m.group("raw").strip()
        pm = _PROVENANCE_LINE.search(m.group("meta") or "")
        if pm:
            result[raw] = pm.group(1).lower()
    return result


def _recorded_commands_in_diff(diff: str) -> list[str]:
    """diff 의 추가(`+`) 라인에서 `acceptance: <command> — result: ...`
    인용을 뽑는다 — 빌더가 실제로 돌렸다고 기록한 커맨드 라인."""
    cmds = []
    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        m = _ACCEPTANCE_CITATION.search(line[1:])
        if m:
            cmds.append(m.group(1).strip())
    return cmds


def _command_identity_mismatch(artifact: str | None, provenance: str | None,
                                recorded_commands: list[str]) -> bool:
    """`artifact`(체크가 이름 붙인 커맨드 표면)와 diff 에 실제로 기록된
    `acceptance:` 커맨드가 서로 다른지 결정론적으로 판정한다. cd/wrapper
    헤드(`cd src && `, `bash -c '...'`)는 동일성 비교에서 벗기지만,
    env-prefix(`PYTHONPATH=src `류)는 벗기지 않는다 — 규칙이 명시적으로
    금지하는 크러치이므로 접두 유무 차이 자체가 mismatch 여야 한다
    (PR #1699 리뷰 결함 1). 같은 첫 토큰(env-prefix/wrapper 제외)으로
    시작하는 기록 커맨드가 하나라도 있는데 그중 어느 것도 `artifact`와
    (cd/wrapper 헤드 제외) 정확히 일치하지 않으면 mismatch. 첫 토큰조차
    일치하는 후보가 없으면 이 체크에 대한 증거가 diff 에 없다는 뜻이므로
    판정을 보류한다(false positive 방지)."""
    if provenance != "executed-live" or not artifact or not recorded_commands:
        return False
    norm_artifact = _strip_wrapper_head(artifact.strip())
    artifact_tokens = _strip_env_prefix(norm_artifact).split()
    if not artifact_tokens:
        return False
    # Unambiguous case first: exactly one recorded command in the whole
    # diff is compared directly, even when its leading token differs
    # from the artifact's (e.g. artifact names `python` but the recorded
    # proof ran `python3 ...` — a same-first-token filter alone would
    # find no candidate and silently miss this, warrant-hunt finding
    # 2026-08-17). Only fall back to the same-first-token heuristic when
    # more than one recorded command exists and a direct 1:1 pairing
    # isn't possible.
    if len(recorded_commands) == 1:
        return norm_artifact != _strip_wrapper_head(recorded_commands[0].strip())

    def _candidate_token(c: str) -> list[str]:
        return _strip_env_prefix(_strip_wrapper_head(c.strip())).split()[:1]

    candidates = [c for c in recorded_commands
                  if _candidate_token(c) == artifact_tokens[:1]]
    if not candidates:
        return False
    normalized_candidates = {_strip_wrapper_head(c.strip()) for c in candidates}
    return norm_artifact not in normalized_candidates


def _cited_artifact(raw: str) -> str | None:
    """`- check:` 불릿 텍스트에서 인용된 아티팩트(백틱으로 감싼 경로/
    커맨드)를 뽑는다. 백틱이 없으면 아티팩트 미인용 — None."""
    m = _ARTIFACT.search(raw)
    if not m:
        return None
    return m.group(1).strip()


_PROSE_FILE_SUFFIXES = (".md", ".markdown", ".txt")
_COMMENT_PREFIXES = ("#", "//", "*", "/*")


def _is_comment_only_line(content: str) -> bool:
    """추가된 hunk 라인(선행 `+` 제거 후)이 주석/문서 텍스트로만
    이루어졌는지 판단한다 — 코드가 실제로 아티팩트를 참조하는지와
    아티팩트 경로를 산문으로만 언급하는지를 구별하기 위함."""
    stripped = content.strip()
    return stripped.startswith(_COMMENT_PREFIXES)


def _artifact_in_diff_hunk(artifact: str, diff: str) -> bool:
    """이슈 #1660 (northpole req#6) — #1651/#1661 리뷰 픽스: 아티팩트가
    diff의 실제 추가/변경 hunk 라인 중 코드/콘텐츠 라인에 등장하는지
    검사한다. 다음은 통과시키지 않는다 (파일이 건드려졌다는 사실이나
    경로를 산문으로만 이름 붙인 것에 불과하므로):
      - `diff --git a/<path> b/<path>`, `--- a/<path>`, `+++ b/<path>`
        같은 파일 헤더 줄에만 경로가 등장하는 것
      - `.md`/`.markdown`/`.txt` 같은 산문 전용 파일에 추가된 줄 — 단,
        issue #2137(verify-at-landing) 예외: `acceptance: <command> —
        result: ...` 모양의 실행-증거 인용 줄은 레코드 .md 안에 있어도
        증거로 인정한다(레코드가 곧 회귀 스위트다)
      - `#`/`//`/`*`/`/*` 로 시작하는 주석 전용 추가 줄
    반드시 `+`로 시작하는(파일 헤더가 아닌) 실제 코드/콘텐츠 추가 라인
    안에 문자열로 등장해야 한다."""
    if not artifact:
        return False
    current_file = None
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[len("+++ b/"):].strip()
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if not line.startswith("+"):
            continue
        content = line[1:]
        if artifact not in content:
            continue
        if current_file and current_file.lower().endswith(_PROSE_FILE_SUFFIXES):
            # issue #2137 (verify-at-landing): a recorded EXECUTED-evidence
            # citation (`acceptance: <command> — result: ...`) in a record
            # .md IS the evidence under the new contract — the record is
            # the regression suite. Only bare prose mentions stay excluded;
            # command-identity (#1696) still checks the cited command
            # matches byte-identically.
            if _ACCEPTANCE_CITATION.search(content):
                return True
            continue
        if _is_comment_only_line(content):
            continue
        return True
    return False


def grade(issue_body: str, diff: str, per_check_verdicts: dict[str, str]) -> dict:
    """순수 함수. `issue_body`의 Acceptance 절에서 `- check:` 불릿을 뽑아
    각각을 채점한다.

    `per_check_verdicts`: 불릿의 원문(`raw`, `check_runner.parse_checks`가
    돌려주는 그대로)을 키로 하는 YES/NO/UNKNOWN 매핑 — builder-blind
    세션이 낸 semantic verdict. 없는 키는 UNKNOWN 취급한다.

    반환값:
      {"empty_state": bool, "criteria": [...], "blocked": bool,
       "blocking_reasons": [str]}
    각 criterion: {"raw", "artifact", "verdict", "artifact_in_diff",
                   "blocking_fail"}.
    """
    issue_body = issue_body or ""
    diff = diff or ""
    section = acceptance_gate._acceptance_section(issue_body)
    if section is None:
        return {"empty_state": True, "criteria": [], "blocked": False,
                "blocking_reasons": [],
                "reason": "이슈 본문에 '## Acceptance' 절이 없다"}
    checks = check_runner.parse_checks(section)
    if not checks:
        return {"empty_state": True, "criteria": [], "blocked": False,
                "blocking_reasons": [],
                "reason": "Acceptance 절에 '- check:' 불릿이 0개다 "
                          "(예: unverifiable: 로만 채워짐) — 채점 가능한 "
                          "기준이 없다"}

    provenance_map = _provenance_map(section)
    recorded_commands = _recorded_commands_in_diff(diff)

    criteria = []
    blocking_reasons = []
    for chk in checks:
        raw = chk["raw"]
        artifact = _cited_artifact(raw)
        verdict = per_check_verdicts.get(raw, UNKNOWN)
        artifact_in_diff = bool(artifact) and _artifact_in_diff_hunk(artifact, diff)
        provenance = provenance_map.get(raw)
        # issue #1696 — command-identity: this fires independent of the
        # semantic verdict (unlike the artifact-presence check below,
        # which only blocks a YES claim) because a command-identity
        # mismatch is a structural fact about what was actually proven,
        # not a judgment call the builder-blind session could still get
        # right or wrong.
        command_identity_mismatch = _command_identity_mismatch(
            artifact, provenance, recorded_commands)
        blocking_fail = (verdict == YES and not artifact_in_diff) or \
            command_identity_mismatch
        if verdict == YES and not artifact_in_diff:
            if artifact is None:
                blocking_reasons.append(
                    f"기준 '{raw}'이 YES 로 채점됐지만 인용된 아티팩트가 없다 "
                    f"(백틱으로 감싼 test/gates 경로 또는 커맨드 필요)")
            else:
                blocking_reasons.append(
                    f"기준 '{raw}'이 YES 로 채점됐지만 인용된 아티팩트 "
                    f"'{artifact}'이 PR diff 에 없다")
        if command_identity_mismatch:
            blocking_reasons.append(
                f"기준 '{raw}'의 executed-live 증거가 이름 붙인 커맨드 표면 "
                f"'{artifact}'과 다르다 — diff 에 기록된 커맨드가 그와 "
                f"동일하지 않다(command-identity mismatch, issue #1696)")
        criteria.append({
            "raw": raw, "artifact": artifact, "verdict": verdict,
            "artifact_in_diff": artifact_in_diff,
            "provenance": provenance,
            "command_identity_mismatch": command_identity_mismatch,
            "blocking_fail": blocking_fail,
        })
    return {"empty_state": False, "criteria": criteria,
            "blocked": bool(blocking_reasons),
            "blocking_reasons": blocking_reasons}


def _pr_diff(repo: Path, pr: int) -> str | None:
    r = subprocess.run(["gh", "pr", "diff", str(pr)], cwd=repo,
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout


def check(repo: Path, issue: int, pr: int,
          per_check_verdicts: dict[str, str] | None = None) -> dict:
    """`gh`-wrapped 버전. `per_check_verdicts`는 builder-blind 세션이 낸
    semantic verdict 매핑 — 이 함수 자체는 그 세션을 스폰하지 않는다(그건
    호출부/오케스트레이터의 몫). 생략하면 모든 기준이 UNKNOWN 으로
    채점되고, UNKNOWN 은 절대 블록하지 않는다(YES 만 아티팩트 부재 시
    블록).

    반환값은 `{"blocked": bool, "blocking_reasons": [str],
    "advisory": [...]}"` — 이슈 #1660 (#1651 리뷰 픽스): 결정적
    아티팩트-존재 서브체크만 `blocked`/`blocking_reasons`로 landing 을
    막고, 기준별 semantic verdict 는 `advisory`로 그대로 노출된다(호출부
    /오케스트레이터가 참고용으로 기록·표시할 수 있게). 각 advisory 항목:
    `{"raw", "verdict", "artifact", "artifact_in_diff"}`."""
    body = gh_rest.fetch_issue_body(repo, issue)
    if body is None:
        return {"blocked": True, "advisory": [], "blocking_reasons": [
            f"이슈 #{issue} 본문을 읽을 수 없다(`gh api repos/.../issues/{issue}` 실패) — "
            f"검사 불가는 통과가 아니다."]}
    diff = _pr_diff(repo, pr)
    if diff is None:
        return {"blocked": True, "advisory": [], "blocking_reasons": [
            f"PR #{pr} diff 를 읽을 수 없다(`gh pr diff {pr}` 실패) — "
            f"검사 불가는 통과가 아니다."]}
    result = grade(body, diff, per_check_verdicts or {})
    if result["empty_state"]:
        return {"blocked": False, "advisory": [], "blocking_reasons": []}
    advisory = [
        {"raw": c["raw"], "verdict": c["verdict"], "artifact": c["artifact"],
         "artifact_in_diff": c["artifact_in_diff"],
         "provenance": c["provenance"],
         "command_identity_mismatch": c["command_identity_mismatch"]}
        for c in result["criteria"]
    ]
    return {"blocked": result["blocked"], "advisory": advisory,
            "blocking_reasons": result["blocking_reasons"]}


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: requirement_met.py <issue-number> <pr-number> [--repo <경로>]")
        return 1
    issue = int(sys.argv[1])
    pr = int(sys.argv[2])
    repo = Path(".").resolve()
    if "--repo" in sys.argv:
        repo = Path(sys.argv[sys.argv.index("--repo") + 1]).resolve()

    result = check(repo, issue, pr)
    for a in result["advisory"]:
        print(f"advisory: [{a['verdict']}] {a['raw']}")
    bad = result["blocking_reasons"]
    if not bad:
        print("게이트 통과 (또는 채점 가능한 기준 없음)")
        return 0
    print("게이트 차단:")
    for b in bad:
        print(f"  - {b}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
