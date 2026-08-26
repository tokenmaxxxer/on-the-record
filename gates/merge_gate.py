#!/usr/bin/env python3
"""머지 게이트 — PR 하나가 머지될 자격이 있는지 판정한다(issue-1323
req 4): phase 2 의 check-runner 결과(전부 pass) + 필요한 검증 기록(req 3
이 스폰하는 2개 role) 이 모두 갖춰져야 `allowed`.

`.github/workflows/` 파일이 아니다 — 이 레포엔 그런 CI 표면이 없고,
role 세션은 그걸 추가하는 게 거절된다. `check_runner.py` 와 같은 자세로
PR 번호를 받는 스크립트다.

  python3 gates/merge_gate.py <pr> <subject> [--repo <경로>]
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import spawn_on_pr  # noqa: E402
import check_run_artifact as cra  # noqa: E402
import check_runner  # noqa: E402
import stale_revert_guard  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn  # noqa: E402

ARTIFACT_PATH = Path(".on-the-record/check-run-artifact.json")

_RESULT_HEADER = re.compile(
    r"^## Acceptance check-runner result:\s*(?:(\d+)/(\d+)\s*passed|no checks declared)",
    re.MULTILINE)


def parse_check_runner_result(comment_body: str) -> dict | None:
    """`check_runner.format_comment()` 가 만드는 정확한 헤더 모양과
    맞춰본다. 안 맞으면 `None`.

    issue #2233 empty-state: `check_runner.NO_CHECKS_MARKER` 를 숫자 헤더보다
    먼저 확인한다 — 실행가능한 검사가 0개면 `{"no_checks": True}` 를
    돌려준다. 이걸 숫자 파싱으로 흘려보내면 `0/0` 같은 우연한 통과 형태가
    나올 수 있다(에러가 아니라 진짜 있었던 결함, 아래 `evaluate()` 참고)."""
    if check_runner.NO_CHECKS_MARKER in comment_body:
        return {"no_checks": True}
    m = _RESULT_HEADER.search(comment_body)
    if not m:
        return None
    return {"passed": int(m.group(1)), "total": int(m.group(2)), "no_checks": False}


def latest_check_runner_comment(repo: Path, pr: int) -> str | None:
    """이 모듈에서 유일하게 `gh` 를 호출하는 함수. 헤더 정규식에 맞는
    마지막 코멘트를 돌려준다."""
    r = subprocess.run(["gh", "pr", "view", str(pr), "--json", "comments"],
                        cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    import json
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None
    comments = data.get("comments", [])
    for c in reversed(comments):
        body = c.get("body", "")
        if _RESULT_HEADER.search(body):
            return body
    return None


def verify_artifact(repo: Path) -> dict:
    """issue-1493 req 2 — check-run 산출물 읽기 쪽 정책.
    `{"trust": bool, "reasons": [str, ...]}`.

    Fail-closed: 산출물 없음/스키마 무효/tree_hash 불일치 -> 신뢰 안함
    (전체 재실행 경로). tree_hash 일치 시: 스키마 검증 후
    per_test_results 의 무작위 샘플(+non-hermetic 항목 전부)을 실제로
    재실행해 라이브 결과와 비교 -- 하나라도 다르면 산출물 전체를
    신뢰 안함으로 되돌린다. 이 함수는 유일하게 `check_runner.run_checks`
    를 호출해 재실행하는 지점이다."""
    artifact = cra.read_artifact(repo / ARTIFACT_PATH)
    if artifact is None:
        return {"trust": False, "reasons": ["산출물이 없거나 파싱할 수 없다"]}
    try:
        cra.validate(artifact)
    except cra.ArtifactValidationError as e:
        return {"trust": False, "reasons": [f"산출물 스키마가 유효하지 않다: {e}"]}

    current_tree = cra.tree_hash(repo)
    if current_tree is None or current_tree != artifact["tree_hash"]:
        return {"trust": False, "reasons": ["tree_hash 불일치 (PR head와 산출물이 다르다)"]}

    per_test = artifact["per_test_results"]
    mandatory = [e for e in per_test if e.get("non_hermetic", True)]
    sample = cra.select_sample(cra.sample_eligible(per_test))
    to_reexecute = {id(e): e for e in mandatory + sample}.values()

    reasons = []
    for entry in to_reexecute:
        chk = {"type": entry["type"], "raw": entry["check"]}
        for extra in ("command", "pattern", "path"):
            if extra in entry:
                chk[extra] = entry[extra]
        try:
            live = check_runner.run_checks(repo, [chk])[0]
        except check_runner.JudgmentCheckError:
            continue
        if (live["status"] != entry["status"]
                or cra.output_hash(live["output"]) != entry["output_hash"]):
            reasons.append(f"샘플 재실행 결과가 산출물과 다르다: {entry['check']}")
    if reasons:
        reasons.append("산출물 전체를 신뢰할 수 없음 -- 전체 재실행으로 폴백")
        return {"trust": False, "reasons": reasons}
    return {"trust": True, "reasons": []}


def _exempt_own_record_kind(missing: list[str], subject: str, own_branch: str | None) -> list[str]:
    """`own_branch`(평가 대상 PR 자신의 head 브랜치)가 `subject`의
    record-kind 브랜치(`<subject>/<kind>`)이고 그 kind 가 `missing` 에
    있으면 빼고 돌려준다(issue #2233 블로커 3, issue #2241 stage 5 하에서
    record-kind 축으로 재키잉) — 관찰자 record PR(예:
    `issue-2204/execution-observation`)이 스스로 공급하는 바로 그 기록을
    "그 기록이 없다"는 이유로 막는 순환을 깬다.

    `PR_TRIGGERED_RECORD_KINDS` 의 두 값은 그 자체가 관찰자 세션의
    `author:` 값이기도 하다(스켈레톤이 `author:` 를 쓰는 role 문자열로
    채운다, `docs/handbooks/record-contract.md`) — `spawn_on_pr.py` 는
    stage 4 의 스킬 축 브랜치 네이밍을 쓰지 않고 이 두 kind 는
    여전히 `<subject>/<kind>` 로 브랜치를 딴다(stage 4 write set 밖,
    `checkout_issue_branch` 그대로) 그래서 브랜치 서픽스를 그 PR 자신의
    (아직 랜딩 전이라 로컬 board 에는 안 잡히는) `author:`/kind 값의
    대리 신호로 그대로 쓸 수 있다 — 이 함수가 순수 함수로 남는 이유이기도
    하다(own_branch 트리를 따로 읽지 않는다).

    issue #2380 (stage 5 하에서 record-kind 축으로 재키잉): #2233 은 각
    관찰자 PR 이 "자기 자신의" kind 만 빼줬다 — `own_kind`가
    `spawn_on_pr.PR_TRIGGERED_RECORD_KINDS`(정확히
    execution-observation/conformance-review 두 개)에 속하면, 그 둘은
    같은 리뷰 사이클에서 나란히 열리는 형제(sibling) PR 이라
    서로가 서로의 선행 머지를 요구하는 순환이 그대로 남아있었다 —
    conformance-review PR 은 execution-observation 이 먼저 main 에
    있어야 하고, 그 역도 마찬가지라 둘 다 먼저가 될 수 없었다. 이
    PR 자신이 이미 그 두 kind 중 하나를 스스로 공급하는 관찰자
    record 라면, 나머지 하나(형제)가 아직 main 에 없다는 이유로도
    막지 않는다 — `PR_TRIGGERED_RECORD_KINDS` 전체를 `missing`에서 뺀다.
    구조적 예외가 아니다: `own_kind`가 이 닫힌 두-kind 집합 밖이면(예:
    `<subject>/implementation`) 기존처럼 자기 kind 하나만 빠지고, 나머지
    kind(들)은 여전히 막힌다 — subject 의 implementation PR 은 오늘처럼
    두 관찰자 기록이 모두 main 에 있어야 한다.

    `own_branch`가 없거나 subject 소속이 아니면 그대로 통과(no-op) —
    로컬 단독 호출(PR 문맥 없음)에서는 오늘과 동일하게 동작한다. 순수
    함수."""
    if not own_branch or not own_branch.startswith(f"{subject}/"):
        return missing
    own_kind = own_branch[len(subject) + 1:]
    if own_kind in spawn_on_pr.PR_TRIGGERED_RECORD_KINDS:
        return [k for k in missing if k not in spawn_on_pr.PR_TRIGGERED_RECORD_KINDS]
    return [k for k in missing if k != own_kind]


def required_verification_missing(root: Path, subject: str, repo: Path | None = None,
                                   pr: int | None = None) -> list[str]:
    """req 3 의 record-kind 목록을 재사용하는 얇은 래퍼 — 두 번째 목록을
    만들지 않는다(issue #2241 stage 5: role 이름이 아니라 `kind:`
    frontmatter 로 매칭한다).

    subject 의 `implementation` 레코드가 있으면 그 `author:` 값을
    `subject_author` 로 넘겨 셀프-verification 을 막는다(작성자가 같은
    kind 는 "충족됨"으로 안 친다) — subject 아직 없으면(로컬 단독 호출
    등) `None` 이라 이 검사를 건너뛴다.

    `repo`/`pr` 을 주면(issue #2233) 평가 대상 PR 자신이 공급하는
    record-kind 을 `_exempt_own_record_kind()`로 뺀다 — 둘 다 없으면(예:
    로컬 단독 호출) 예외 없이 오늘과 같은 목록을 돌려준다."""
    b = spawn.board(root)
    subject_board = b.get(subject, {})
    subject_author = subject_board.get("implementation", {}).get("author")
    missing = spawn_on_pr.applicable_record_kinds(subject_board, subject_author=subject_author)
    if repo is not None and pr is not None:
        refs = pr_refs(repo, pr)
        own_branch = refs["head_ref"] if refs is not None else None
        missing = _exempt_own_record_kind(missing, subject, own_branch)
    return missing


def pr_refs(repo: Path, pr: int) -> dict | None:
    """PR 의 base/head 브랜치 이름을 `gh` 로 읽는다. 이 모듈에서
    `latest_check_runner_comment` 다음으로 유일하게 `gh` 를 호출하는
    지점 -- `stale_revert_guard.classify()`/`check_pr()` 자체는 순수
    로컬 git 만 쓴다(제약: classify() 안에는 네트워크/`gh` 호출 없음)."""
    r = subprocess.run(
        ["gh", "pr", "view", str(pr), "--json", "baseRefName,headRefName"],
        cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    import json
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None
    base_ref, head_ref = data.get("baseRefName"), data.get("headRefName")
    if not base_ref or not head_ref:
        return None
    return {"base_ref": base_ref, "head_ref": head_ref}


def stale_revert_reasons(repo: Path, pr: int) -> list[str]:
    """req#6(issue #1664) -- PR 이 stale merge-base 로 인해 base HEAD의
    내용을 되돌리는지 검사한다. refs 를 못 읽거나 merge-base 를 계산할
    수 없으면 (fail-open) 빈 목록 -- 이 게이트가 못 읽어서 무해한 PR을
    막는 일은 없어야 한다; 실제 위반은 산출물이 갖춰지면 잡힌다."""
    refs = pr_refs(repo, pr)
    if refs is None:
        return []
    base_ref, head_ref = refs["base_ref"], refs["head_ref"]
    mb = subprocess.run(
        ["git", "merge-base", f"origin/{base_ref}", head_ref],
        cwd=repo, capture_output=True, text=True)
    if mb.returncode != 0:
        mb = subprocess.run(["git", "merge-base", base_ref, head_ref],
                             cwd=repo, capture_output=True, text=True)
    if mb.returncode != 0:
        return []
    merge_base_ref = mb.stdout.strip()
    refusals = stale_revert_guard.check_pr(repo, base_ref, merge_base_ref, head_ref)
    return [r["reason"] for r in refusals]


def evaluate(root: Path, repo: Path, pr: int, subject: str) -> dict:
    """`{"allowed": bool, "reasons": [str, ...]}`. 넷 다 깨끗해야
    `allowed`: check-runner 코멘트 존재, `passed == total`, 필요 검증
    기록 모두 존재, stale-revert 없음(issue #1664)."""
    reasons: list[str] = []
    comment = latest_check_runner_comment(repo, pr)
    if comment is None:
        reasons.append("check-runner 코멘트를 찾을 수 없다")
    else:
        result = parse_check_runner_result(comment)
        if result is None:
            reasons.append(f"check-runner 결과를 파싱할 수 없다: {comment[:200]!r}")
        elif result.get("no_checks"):
            # issue #2233 empty-state: 이슈의 Acceptance 절에 실행가능한
            # 검사가 없다는 것 자체가 명시적 결과다 — 통과로 취급하지 않는다.
            reasons.append("check-runner: 이슈의 Acceptance 절에 실행가능한 검사가 "
                            "없다(no checks declared) — 통과로 취급하지 않는다")
        elif result["passed"] != result["total"]:
            reasons.append(f"check-runner 결과가 전부 pass 가 아니다: {result}")
    missing = required_verification_missing(root, subject, repo, pr)
    if missing:
        reasons.append(f"필요한 검증 기록이 없다: {missing}")
    reasons.extend(stale_revert_reasons(repo, pr))
    return {"allowed": not reasons, "reasons": reasons}


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: merge_gate.py <pr> <subject> [--repo <경로>]")
        return 1
    try:
        pr = int(sys.argv[1])
    except ValueError:
        print(f"usage: merge_gate.py <pr> <subject> [--repo <경로>] "
              f"— pr must be an integer, got {sys.argv[1]!r}")
        return 1
    subject = sys.argv[2]
    repo = Path(".").resolve()
    if "--repo" in sys.argv:
        repo = Path(sys.argv[sys.argv.index("--repo") + 1]).resolve()
    result = evaluate(repo, repo, pr, subject)
    if result["allowed"]:
        print(f"허용: PR #{pr} ({subject}) 머지 자격 있음")
        return 0
    print(f"거절: PR #{pr} ({subject})")
    for reason in result["reasons"]:
        print(f"  - {reason}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
