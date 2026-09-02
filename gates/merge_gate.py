#!/usr/bin/env python3
"""머지 게이트 — PR 하나가 머지될 자격이 있는지 판정한다(issue-1323
req 4): phase 2 의 check-runner 결과(전부 pass) + 필요한 검증 기록(subject
당 독립 검증 기록 2건, kind/이름 무관 — issue #2609) 이 모두 갖춰져야
`allowed`.

`.github/workflows/` 파일이 아니다 — 이 레포엔 그런 CI 표면이 없고,
세션은 그걸 추가하는 게 거절된다. `check_runner.py` 와 같은 자세로
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
# issue #3057 (same collision and fix shape as `gates/record_lint.py`/
# `gates/claims.py`: see their comments for the full rationale) — a bare
# `import gates` here resolves to the sibling `gates/gates.py` when this
# file is run as a script (`sys.path[0]` is `gates/`), but under
# `python3 -m gates.merge_gate` the name `gates` is already bound to the
# enclosing namespace package, so the bare import silently binds to that
# package instead and `gates.record_frontmatter` raises AttributeError.
# Load the sibling file by explicit path under the same private,
# process-shared key the other fixed modules use.
import importlib.util as _importlib_util
_GATES_IMPL_KEY = "_on_the_record_gates_sibling_impl"
if _GATES_IMPL_KEY not in sys.modules:
    _spec = _importlib_util.spec_from_file_location(
        _GATES_IMPL_KEY, str(Path(__file__).parent / "gates.py"))
    _impl = _importlib_util.module_from_spec(_spec)
    sys.modules[_GATES_IMPL_KEY] = _impl
    _spec.loader.exec_module(_impl)
gates = sys.modules[_GATES_IMPL_KEY]

sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn  # noqa: E402

ARTIFACT_PATH = Path(".on-the-record/check-run-artifact.json")

_RESULT_HEADER = re.compile(
    r"^## Acceptance check-runner result:\s*(?:(\d+)/(\d+)\s*passed|"
    r"no checks declared|record-only PR — implementation checks not scored)",
    re.MULTILINE)


def parse_check_runner_result(comment_body: str) -> dict | None:
    """`check_runner.format_comment()` 가 만드는 정확한 헤더 모양과
    맞춰본다. 안 맞으면 `None`.

    issue #2233 empty-state: `check_runner.NO_CHECKS_MARKER` 를 숫자 헤더보다
    먼저 확인한다 — 실행가능한 검사가 0개면 `{"no_checks": True}` 를
    돌려준다. 이걸 숫자 파싱으로 흘려보내면 `0/0` 같은 우연한 통과 형태가
    나올 수 있다(에러가 아니라 진짜 있었던 결함, 아래 `evaluate()` 참고).

    issue #2974: `check_runner.RECORD_ONLY_MARKER` 도 숫자 헤더보다 먼저
    확인한다 — `{"record_only": True}`. `no_checks`(이슈 자체에 실행가능한
    검사가 없다, 수상해서 fail-closed)와 의도적으로 다른 결과다: 이건 이
    PR 자신이 record-only 라 애초에 그 검사의 채점 대상이 아니라는
    뜻이라, `evaluate()`는 이걸 통과로 취급한다."""
    if check_runner.RECORD_ONLY_MARKER in comment_body:
        return {"record_only": True}
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


def _own_pr_supplies_verification(repo: Path, subject: str, own_branch: str | None,
                                   subject_author: str | None) -> bool:
    """issue #2609 (Option 2, docs/issue-2593/reports/architecture-module-
    boundary-definition+architecture-decomposition-strategy-386ff408.md):
    kind-free replacement for the old kind-based sibling-pair cycle break
    (issue #2233 blocker 3, issue #2380) -- an observer record PR (e.g.
    `issue-2204/execution-observation`) must not be blocked from merging by
    the very record it is itself about to supply.

    True when `own_branch`(the PR under evaluation's own head, not yet
    landed so `spawn.board()` has nothing to join against yet) itself
    carries a record self-declaring `verifies_subject: true` with an
    `author:` different from `subject_author` -- read directly via `git
    show` against the branch tip, the same self-declared field
    `spawn_on_pr.verifying_record_count()` checks against landed records.
    No `kind:` value or branch-suffix identity match participates.

    issue #2609 (silent-failure-audit skill-verdict): reads
    `origin/{own_branch}`, not the bare branch name -- `repo` here is the
    orchestrator checkout `evaluate()`/`main()` operate against, which has
    an `origin` remote but no local branch of that exact name;
    `check_runner.fetch_all_skill_branches()` (already run once at the top
    of `evaluate()`) mirrors every origin branch to local `origin/<branch>`
    refs, the same convention `check_runner.checkout_pr_worktree()` uses
    (`origin/{head_ref}`, not bare `head_ref`) for the identical PR-head
    resolution problem. Reading the bare name here would have made this
    exemption never actually fire in production -- every call would take
    the `git show` failure branch below and silently fall through to the
    normal count (never wrong, but never the intended cycle-break either,
    and with nothing to distinguish that from a genuinely unqualifying
    branch).

    Unlike the old mechanism (which dropped the whole closed two-kind set
    from `missing` whenever `own_branch`'s suffix was one of the two
    named kinds -- a hack specific to there being exactly two required
    names), this exempts the evaluated PR from the check outright: landing
    a PR that itself supplies a qualifying verification can only help the
    subject meet `spawn_on_pr.REQUIRED_INDEPENDENT_VERIFICATIONS`, never
    hurt it, so blocking it on the very count it is about to increase
    serves no purpose regardless of what that required count is.

    `own_branch` outside `subject`'s prefix, unresolvable, or lacking a
    qualifying record: False (no exemption -- same conservative no-op as
    the old `own_branch=None`/other-subject cases). Not a pure function
    (shells out to `git show`), unlike the old mechanism."""
    if not own_branch or not own_branch.startswith(f"{subject}/"):
        return False
    slug = own_branch[len(subject) + 1:]
    issue_num = int(subject.split("-", 1)[1])
    r = subprocess.run(
        ["git", "-C", str(repo), "show",
         f"origin/{own_branch}:docs/issue-{issue_num}/reports/{slug}.md"],
        capture_output=True, text=True)
    if r.returncode != 0:
        return False
    fm = gates.record_frontmatter(r.stdout)
    if fm.get("verifies_subject") != "true":
        return False
    return subject_author is None or fm.get("author") != subject_author


def required_verification_missing(root: Path, subject: str, repo: Path | None = None,
                                   pr: int | None = None) -> int:
    """issue #2609 (Option 2 of docs/issue-2593/reports/architecture-
    module-boundary-definition+architecture-decomposition-strategy-
    386ff408.md): how many more independent verifying records `subject`
    still needs -- `spawn_on_pr.REQUIRED_INDEPENDENT_VERIFICATIONS` minus
    the count of records self-declaring `verifies_subject: true` with an
    `author:` different from the subject's own deliverable author
    (`spawn_on_pr.verifying_record_count()`, reusing the existing
    self-verification guard unchanged in spirit). `0` when satisfied. No
    `kind:` value, filename, or skill name decides this -- the closed
    two-name tuple this used to match against is gone entirely, not
    re-expressed under another name.

    `subject`'s deliverable record (`spawn_on_pr.subject_deliverable_record()`,
    unchanged, issue #2575) supplies `subject_author`; no deliverable
    landed yet (e.g. local standalone call) -> `None`, which skips the
    self-verification guard.

    `repo`/`pr` (issue #2233/#2380, kind-free as of #2609): when both are
    given, a PR that itself supplies a qualifying verifying record for
    `subject` is exempt outright (`_own_pr_supplies_verification()`) --
    breaks the same sibling mutual-block cycle the old kind-based
    exemption did, without matching on any name. Both omitted: no
    exemption, same as today."""
    b = spawn.board(root)
    subject_board = b.get(subject, {})
    _slug, subject_fm = spawn_on_pr.subject_deliverable_record(subject_board)
    subject_author = subject_fm.get("author")
    if repo is not None and pr is not None:
        refs = pr_refs(repo, pr)
        own_branch = refs["head_ref"] if refs is not None else None
        if _own_pr_supplies_verification(repo, subject, own_branch, subject_author):
            return 0
    count = spawn_on_pr.verifying_record_count(subject_board, subject_author=subject_author)
    return max(0, spawn_on_pr.REQUIRED_INDEPENDENT_VERIFICATIONS - count)


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


def staleness(repo: Path, merge_base_ref: str, base_head_ref: str, head_ref: str) -> dict:
    """issue #2403 — pre-merge staleness probe, pure local git (no `gh`).
    `{"behind": int, "conflicting": bool}`: `behind` is how many commits
    `base_head_ref` has added since `merge_base_ref` that `head_ref` lacks;
    `conflicting` is whether a 3-way merge of those would actually clash.

    `git merge-tree <base> <a> <b>` (this repo's git 2.34, pre `--write-tree`)
    always exits 0 and reports conflicts in its *output* via `<<<<<<<`
    markers -- exit code is not a signal here, unlike newer git."""
    behind = subprocess.run(["git", "rev-list", "--count", f"{merge_base_ref}..{base_head_ref}"],
                             cwd=repo, capture_output=True, text=True)
    behind_n = (int(behind.stdout.strip())
                if behind.returncode == 0 and behind.stdout.strip().isdigit() else 0)
    if behind_n == 0:
        return {"behind": 0, "conflicting": False}
    mt = subprocess.run(["git", "merge-tree", merge_base_ref, base_head_ref, head_ref],
                         cwd=repo, capture_output=True, text=True)
    return {"behind": behind_n, "conflicting": "<<<<<<<" in mt.stdout}


def staleness_for_pr(repo: Path, pr: int, refs: dict | None = None) -> dict | None:
    """`evaluate()`'s pre-merge caller (issue #2403) -- resolves `pr`'s
    base/head via `gh` (unless `refs` is already known -- `evaluate()`
    passes its own `pr_refs()` result through here and to
    `stale_revert_reasons()` so one `evaluate()` call makes one `gh pr
    view` round trip for this pair, not two) then delegates to the pure
    `staleness()`. `None` if refs or merge-base can't be resolved
    (fail-open, same convention as `stale_revert_reasons()`: this probe
    never blocks a PR it can't read)."""
    if refs is None:
        refs = pr_refs(repo, pr)
    if refs is None:
        return None
    base_ref, head_ref = refs["base_ref"], refs["head_ref"]
    base_head_ref = f"origin/{base_ref}"
    mb = subprocess.run(["git", "merge-base", base_head_ref, head_ref],
                         cwd=repo, capture_output=True, text=True)
    if mb.returncode != 0:
        base_head_ref = base_ref
        mb = subprocess.run(["git", "merge-base", base_ref, head_ref],
                             cwd=repo, capture_output=True, text=True)
    if mb.returncode != 0:
        return None
    return staleness(repo, mb.stdout.strip(), base_head_ref, head_ref)


def stale_revert_reasons(repo: Path, pr: int, refs: dict | None = None) -> list[str]:
    """req#6(issue #1664) -- PR 이 stale merge-base 로 인해 base HEAD의
    내용을 되돌리는지 검사한다. refs 를 못 읽거나 merge-base 를 계산할
    수 없으면 (fail-open) 빈 목록 -- 이 게이트가 못 읽어서 무해한 PR을
    막는 일은 없어야 한다; 실제 위반은 산출물이 갖춰지면 잡힌다.

    `refs`: issue #2403 -- `evaluate()`'s already-resolved `pr_refs()`,
    reused here and by `staleness_for_pr()` so one `evaluate()` call
    doesn't make two identical `gh pr view` round trips."""
    if refs is None:
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
    기록 모두 존재, stale-revert 없음(issue #1664).

    이슈 #2506: 위 넷을 따지기 전에, 이 게이트를 실행 중인 코드 자체의
    체크아웃(`spawn.ROOT` — `--repo` 로 받은 대상 PR 저장소와는 다른 축)이
    origin 대비 뒤처졌는지 먼저 본다. 뒤처졌으면 넷 중 무엇도 계산하지
    않고 즉시 거절한다 — 낡은 `_exempt_own_role`/`required_verification_missing`
    구현이 낸 "확신에 찬 오답"이 바로 이 이슈가 실측한 사고였다. 판정
    보류(`checked: False` — 원격 없는 합성 테스트 저장소, 이슈가 정의한
    empty state)는 오늘처럼 그대로 통과시킨다."""
    checkout = spawn.checkout_staleness()
    if checkout["checked"] and checkout["stale"]:
        reason = (f"checkout-stale (코드 결함 아님 — 이 게이트를 실행한 체크아웃이 낡았다): "
                  f"{checkout['detail']} — `git -C {spawn.ROOT} pull --ff-only` 로 갱신 후 재실행하라")
        return {"allowed": False, "reasons": [reason], "checkout_staleness": checkout}
    # issue #2381 R1 (conformance-review CHANGES round): 아래 `stale_revert_reasons()`
    # 는 `origin/<base_ref>` 를 resolve 한다 — 예전엔 `check_runner.py`의
    # `checkout_pr_worktree()`가 같은 `--repo` 체크아웃에 먼저
    # `fetch_all_skill_branches()`를 실행해 뒀다는 걸 전제로 삼았지만,
    # `verdict_gate.py`(및 그걸 통하지 않고 `evaluate()`를 직접 부르는 다른
    # 호출부)는 그 실행 순서를 보장하지 않는다 — 그러면 이슈 #2381 이 고치려던
    # "fatal: invalid reference"(방금 push된 role 브랜치를 못 찾는 문제)가
    # `merge_gate.py` 쪽에서 그대로 재발한다. `evaluate()` 자신이 이 함수의
    # 유일한 origin-ref 의존 호출부(`stale_revert_reasons`) 바로 앞에서
    # fetch 함으로써, 어느 스크립트를 거쳐 들어오든 매번 커버한다.
    # best-effort: 리턴값을 보지 않는다 — origin 리모트가 없는 합성 테스트
    # 저장소 등에서 실패해도, `stale_revert_reasons()`는 이미 ref 를 못 읽으면
    # fail-open 이라 결과가 달라지지 않는다.
    check_runner.fetch_all_skill_branches(repo)
    reasons: list[str] = []
    comment = latest_check_runner_comment(repo, pr)
    if comment is None:
        reasons.append("check-runner 코멘트를 찾을 수 없다")
    else:
        result = parse_check_runner_result(comment)
        if result is None:
            reasons.append(f"check-runner 결과를 파싱할 수 없다: {comment[:200]!r}")
        elif result.get("record_only"):
            # issue #2974: 이 PR 자신이 record-only 라 애초에 구현
            # Acceptance 검사의 채점 대상이 아니다 — no_checks(이슈 자체에
            # 실행가능한 검사가 없다, 수상함)와 달리 이건 정상적인 결과라
            # 통과로 취급한다. 거부 사유를 추가하지 않는다.
            pass
        elif result.get("no_checks"):
            # issue #2233 empty-state: 이슈의 Acceptance 절에 실행가능한
            # 검사가 없다는 것 자체가 명시적 결과다 — 통과로 취급하지 않는다.
            reasons.append("check-runner: 이슈의 Acceptance 절에 실행가능한 검사가 "
                            "없다(no checks declared) — 통과로 취급하지 않는다")
        elif result["passed"] != result["total"]:
            reasons.append(f"check-runner 결과가 전부 pass 가 아니다: {result}")
    missing = required_verification_missing(root, subject, repo, pr)
    if missing:
        required = spawn_on_pr.REQUIRED_INDEPENDENT_VERIFICATIONS
        seen = required - missing
        reasons.append(
            f"required_verification_missing(): 독립 검증 기록이 부족하다 -- "
            f"{seen}/{required}개 확인됨 ({missing}개 더 필요)")
    # issue #2403: resolve once, share with staleness_for_pr() -- these two
    # are the only callers here that need base/head refs, so one `gh pr
    # view` covers both instead of one each (implementation-complexity-
    # coupling-management rule 8/9: don't duplicate an expensive network
    # step across sibling checks in the same pipeline).
    refs = pr_refs(repo, pr)
    reasons.extend(stale_revert_reasons(repo, pr, refs=refs))
    stale = staleness_for_pr(repo, pr, refs=refs)
    if stale is not None and stale["conflicting"]:
        # issue #2403: worded as "stale-branch", not "code defect" -- this
        # is what lets a reader (human or orchestrator) tell the two apart
        # without re-deriving it from a failed `gh pr merge`.
        reasons.append(
            f"stale-branch: base 대비 {stale['behind']}개 커밋 뒤처졌고 merge 충돌 -- "
            f"코드 결함이 아니라 기계적 rebase 필요(`python3 spawn.py rebase -C <워크스페이스>`)")
    result = {"allowed": not reasons, "reasons": reasons}
    if stale is not None:
        result["staleness"] = stale
    return result


# issue #3057: exit code is the only signal a shell caller has, and
# `evaluate()` raising was previously indistinguishable from a refusal —
# both surfaced as rc=1 (the crash, via Python's default handler for an
# uncaught exception; the refusal, via the old explicit `return 1`).
# Three outcomes now get three distinct codes so a caller branching on
# `$?` can tell "don't merge, here is why" (EXIT_REFUSED) apart from
# "the gate itself did not run to completion" (EXIT_COULD_NOT_DECIDE) —
# the latter must never be read as either an allow or a considered
# refuse.
EXIT_ALLOWED = 0
EXIT_REFUSED = 1
EXIT_COULD_NOT_DECIDE = 2


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: merge_gate.py <pr> <subject> [--repo <경로>]")
        return EXIT_COULD_NOT_DECIDE
    try:
        pr = int(sys.argv[1])
    except ValueError:
        print(f"usage: merge_gate.py <pr> <subject> [--repo <경로>] "
              f"— pr must be an integer, got {sys.argv[1]!r}")
        return EXIT_COULD_NOT_DECIDE
    subject = sys.argv[2]
    repo = Path(".").resolve()
    if "--repo" in sys.argv:
        repo = Path(sys.argv[sys.argv.index("--repo") + 1]).resolve()
    # issue #3057 must-not: this does not catch-and-continue -- a crash
    # inside `evaluate()` still aborts with its full traceback printed
    # (nothing is swallowed) and still returns a non-zero code; the only
    # change is which non-zero code, so a crash can never be read as a
    # `EXIT_REFUSED` verdict the gate actually considered.
    try:
        result = evaluate(repo, repo, pr, subject)
    except Exception:
        import traceback
        traceback.print_exc()
        print(f"판정 불가: PR #{pr} ({subject}) — 게이트 실행 중 처리되지 않은 예외 발생, "
              f"위 트레이스백 참고. 이 종료 코드를 거절({EXIT_REFUSED})로 읽지 말 것.")
        return EXIT_COULD_NOT_DECIDE
    stale = result.get("staleness")
    if stale is not None:
        # issue #2403: reported unconditionally, before any merge attempt --
        # allowed or not -- so the orchestrator never has to learn this from
        # a failed `gh pr merge`.
        print(f"stale: behind by {stale['behind']}, conflicting: "
              f"{'yes' if stale['conflicting'] else 'no'}")
    if result["allowed"]:
        print(f"허용: PR #{pr} ({subject}) 머지 자격 있음")
        return EXIT_ALLOWED
    print(f"거절: PR #{pr} ({subject})")
    for reason in result["reasons"]:
        print(f"  - {reason}")
    return EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
