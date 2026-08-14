#!/usr/bin/env python3
"""플로우 종결-일관성 스윕 게이트 — 보드의 이슈-PR 쌍이 함께 닫히는지 훑는다(issue-135).

`pr_reference.py`(PR 하나, 로컬 판정)와 달리 이 게이트는 보드 전체(여러
subject x role)를 훑고, 위반을 **보고만** 한다 — 아무것도 닫지 않는다
(계약 v3: GitHub 종결은 사람/오케스트레이터의 몫).

  python3 gates/closure_sweep.py [--repo <경로>] [--post]
  종료 코드 0 (위반 없음) / 1 (위반 있음, --post 없이도 보고는 stdout 에 찍는다)
"""
from __future__ import annotations
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
import pr_reference  # noqa: E402
import spawn  # noqa: E402
import ci  # noqa: E402
import accumulation  # noqa: E402

_ACCUMULATION_TREND_STATE = "runs/accumulation_trend.json"

OPEN_PR_ON_CLOSED_ISSUE = "open-pr-on-closed-issue"
MERGED_DELIVERY_ISSUE_OPEN = "merged-delivery-issue-open"

_SWEEP_COMMENT_MARKER = "[on-the-record] closure-sweep: {digest}"


def _refs_issue(body: str, issue: int) -> tuple[bool, bool]:
    """(plain 참조 있음, Closes/Fixes/Resolves 참조 있음) — 이 이슈 번호로 한정."""
    body = body or ""
    has_closes = any(int(m.group(2)) == issue
                      for m in pr_reference._CLOSES_REF.finditer(body))
    has_plain = issue in {int(n) for n in pr_reference._PLAIN_REF.findall(body)}
    return has_plain, has_closes


def classify(issue_state: str, pr_state: str, pr_body: str, issue: int,
             has_record_evidence: bool = False) -> str | None:
    """네트워크 없는 순수 판정 (테스트 용이) — 상태 문자열과 PR 본문만으로 결정한다.

    phase-1 제안 PR(merged, plain-ref 뿐, 이슈는 열림)은 **의도된 모양**이라
    violation 이 아니다 — 계약 v3 s19. Closes/Fixes/Resolves 로 실제 인도를
    약속했을 때만 '머지됐는데 이슈는 열림'이 위반이다.

    `has_record_evidence`(issue #383)는 closes-gate가 #284에서 받아들인
    것과 같은 대안 증거다 — 브랜치의 phase-2 기록 파일이 존재하고
    `loop_state`가 채워져 있으면, PR 본문에 Closes/Fixes/Resolves가
    없어도 실제 인도로 본다. #284가 그 키워드를 선택사항으로 만든
    이후로는 키워드 부재만으로 '인도 아님'을 단정할 수 없다 — 키워드도
    기록 증거도 없을 때만 위반이 아니다."""
    has_plain, has_closes = _refs_issue(pr_body, issue)
    if issue_state == "CLOSED" and pr_state == "OPEN" and (has_plain or has_closes):
        return OPEN_PR_ON_CLOSED_ISSUE
    if pr_state == "MERGED" and issue_state == "OPEN" and (has_closes or has_record_evidence):
        return MERGED_DELIVERY_ISSUE_OPEN
    return None


def _issue_view(root: Path, issue: int) -> tuple[str | None, bool]:
    """(state, ok) — ok=False means the `gh` call itself failed; state is
    then meaningless and must not be read as "no such issue"."""
    r = subprocess.run(["gh", "issue", "view", str(issue), "--json", "state",
                        "-q", ".state"], cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return None, False
    state = r.stdout.strip()
    return (state or None), True


def _pr_view_state_body(root: Path, pr: int) -> tuple[tuple[str, str] | None, bool]:
    """(view, ok) — ok=False means the `gh` call itself failed/unparseable."""
    r = subprocess.run(["gh", "pr", "view", str(pr), "--json", "state,body"],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return None, False
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None, False
    return (data.get("state", ""), data.get("body", "") or ""), True


_PR_INDEX_LIMIT = 1000


def _pr_index_all(root: Path) -> tuple[dict[str, dict] | None, bool]:
    """브랜치 이름 -> `{number, state, body}` 사전, `gh` 한 번(issue #682).

    이전에는 subject x role 마다 `spawn._pr_for_branch`(브랜치->번호)와
    `_pr_view_state_body`(번호->state/body)를 각각 불러 179+179회 · 199초를
    썼다. 두 조회가 필요로 하는 필드는 `gh pr list --state all` 하나에 다
    들어 있다.

    `_pr_for_branch` 의 "같은 브랜치에 PR 이 여럿이면 가장 최근 것" 시맨틱은
    `gh pr list` 의 기본 정렬(생성 역순)에서 **첫 번째** 항목만 채택해
    보존한다.

    `(index, ok)` — `ok=False` 는 `gh` 호출 자체가 실패했다는 뜻이고, 그때
    `index` 는 `None` 이다: 호출부가 "그 브랜치에 PR 이 없다"와 "PR 목록을
    못 읽었다"를 구별해야 한다(issue #287 S1 과 같은 이유).

    `--limit` 상한에 정확히 걸리면 잘렸을 수 있으므로 `(None, True)` 를
    돌려 호출부가 레포별 개별 조회로 되돌아가게 한다 — 조용한 절단으로
    위반을 놓치느니 느린 옛 경로가 낫다(issue #224 가 같은 절단을 지적)."""
    r = subprocess.run(["gh", "pr", "list", "--state", "all", "--json",
                        "number,headRefName,state,body",
                        "--limit", str(_PR_INDEX_LIMIT)],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return None, False
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None, False
    if not isinstance(data, list):
        return None, False
    if len(data) >= _PR_INDEX_LIMIT:
        return None, True
    index: dict[str, dict] = {}
    for pr in data:
        branch = pr.get("headRefName") or ""
        if branch and branch not in index:
            index[branch] = {"number": pr.get("number"),
                             "state": pr.get("state", ""),
                             "body": pr.get("body", "") or ""}
    return index, True


_ISSUE_INDEX_LIMIT = 1000


def issue_state_index_all(root: Path) -> tuple[dict[int, str] | None, bool]:
    """이슈번호 -> state 사전, `gh` 한 번(issue #743) — `_pr_index_all` 과
    같은 `(index, ok)`/잘림-안전 모양.

    `find_violations` 는 이미 `issue_states` 를 받으면 subject 별
    `_issue_view` 호출을 건너뛴다(issue #189) — 문제는 배포된 호출자
    아무도 그 맵을 채워 넘기지 않아 subject 수만큼 `gh issue view` 를
    부른다는 것이었다(watchdog 틱당 166 subject x ~0.61s ≈ 101초, issue
    #743 측정). 이 헬퍼는 그 맵을 한 번의 `gh issue list` 로 만든다 —
    `find_violations` 자체는 바뀌지 않는다.

    `(index, ok)` — `ok=False` 는 `gh` 호출 자체가 실패했다는 뜻이고,
    그때 `index` 는 `None` 이다: "이슈 없음"으로 읽으면 안 된다(`_pr_index_all`
    과 같은 이유, issue #287 S1 계열).

    `--limit` 상한에 정확히 걸리면 잘렸을 수 있으므로 `(None, True)` 를
    돌려준다 — 호출부는 이를 `issue_states=None` 으로 `find_violations` 에
    넘겨 기존 subject 별 개별 조회로 되돌아가야 한다(조용한 절단으로 위반을
    놓치느니 느린 옛 경로가 낫다, issue #224)."""
    r = subprocess.run(["gh", "issue", "list", "--state", "all", "--json",
                        "number,state", "--limit", str(_ISSUE_INDEX_LIMIT)],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return None, False
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None, False
    if not isinstance(data, list):
        return None, False
    if len(data) >= _ISSUE_INDEX_LIMIT:
        return None, True
    index: dict[int, str] = {}
    for item in data:
        number = item.get("number")
        if number is not None:
            index[number] = item.get("state", "")
    return index, True


def find_violations(root: Path, subjects: dict | None = None,
                     issue_states: dict[int, str] | None = None) -> tuple[list[dict], list[dict]]:
    """보드의 각 subject x role 브랜치에 대해 이슈/PR 상태를 읽고 위반을 모은다.

    `subjects` 는 `spawn.board(root)` 와 같은 모양(subject -> role -> ...) —
    안 주면 직접 읽는다. `issue_states` 는 이슈번호 -> state 사전(선택,
    issue #189) — 주어지고 그 subject 의 이슈가 안에 있으면 `_issue_view`
    호출을 건너뛰고 그 값을 그대로 쓴다(레포 전체 한 번짜리 프리페치 재사용,
    새 `gh` 호출 종류를 추가하지 않는다). 네트워크(`gh`)만 쓰고 아무것도
    쓰지 않는다.

    `(violations, skips)` 를 돌려준다 — `skips` 는 `gh` 호출이 실패해서
    끝내 확인하지 못한 subject/role 목록이다(issue #287 S1): 위반이
    0건이어도 skips 가 있으면 "위반 없음"이 아니라 "확인 불가"다.
    """
    if subjects is None:
        subjects = spawn.board(root)
    if issue_states is None:
        # issue #1320: no per-item `gh issue view` fallback in the sweep
        # path — compute the bulk index here so O(1) gh calls holds
        # regardless of whether the caller pre-fetched it.
        issue_states, issue_states_ok = issue_state_index_all(root)
    else:
        issue_states_ok = True
    violations = []
    skips = []
    pr_index, pr_index_ok = _pr_index_all(root)
    for subject, roles in subjects.items():
        m = subject.split("-", 1)
        if len(m) != 2 or not m[1].isdigit():
            continue
        issue = int(m[1])
        if issue_states is None:
            reason = "gh-issue-list-failed" if not issue_states_ok else "gh-issue-list-truncated"
            skips.append({"subject": subject, "reason": reason})
            continue
        if issue not in issue_states:
            continue
        issue_state = issue_states[issue]
        if issue_state is None:
            continue
        for role in roles:
            branch = f"{subject}/{role}"
            if not pr_index_ok:
                skips.append({"subject": subject, "role": role,
                              "reason": "gh-pr-list-failed"})
                continue
            if pr_index is None:
                # 목록이 --limit 에 걸려 잘렸다 — issue #1320: 개별
                # `gh pr view` 조회로 되돌아가지 않는다(스윕 경로는 O(1)
                # gh 호출만), 대신 skip 으로 남긴다.
                skips.append({"subject": subject, "role": role,
                              "reason": "gh-pr-list-truncated"})
                continue
            entry = pr_index.get(branch)
            if entry is None:
                continue
            pr = entry["number"]
            pr_state, pr_body = entry["state"], entry["body"]
            # `_phase2_record_evidence` 는 subject 마다 `gh api .../contents`
            # 한 번을 쓰는 원격 조회다(179회 · 163초, issue #682). `classify`
            # 가 그 값을 쓰는 곳은 `pr_state == MERGED and issue_state ==
            # OPEN` 가지 하나뿐이고, 거기서도 `has_closes` 와 OR 이라 값은
            # `None -> MERGED_DELIVERY_ISSUE_OPEN` 방향으로만 작용한다.
            # 따라서 증거 없이 한 번 판정해 보고, 결과가 `None` 이면서 그
            # 가지 조건일 때만 조회해 재판정해도 결과가 동치다.
            kind = classify(issue_state, pr_state, pr_body, issue, False)
            if kind is None and pr_state == "MERGED" and issue_state == "OPEN":
                if ci._phase2_record_evidence(root, pr, branch, issue):
                    kind = classify(issue_state, pr_state, pr_body, issue, True)
            if kind:
                violations.append({"issue": issue, "pr": pr, "role": role, "kind": kind})
    return violations, skips


def format_report(violations: list[dict]) -> str:
    return "\n".join(f"issue #{v['issue']} / PR #{v['pr']}: {v['kind']}"
                     for v in violations)


def _violations_digest(violations: list[dict]) -> str:
    key = sorted((v["issue"], v["pr"], v["kind"]) for v in violations)
    return hashlib.sha256(json.dumps(key).encode("utf-8")).hexdigest()[:12]


def _current_accumulation_counts(root: Path) -> dict:
    """이슈 #512 요구사항 4: 병합된 트리(diff 아님)에서 모양 1/5 인스턴스
    수를 센다 — `accumulation.py`가 검사에 쓰는 것과 같은 두 모양(inline
    subprocess/gh 호출, roles/*.json)만, 일반 중복 탐지기는 재도입하지
    않는다 (#419/#424 오탐 홍수 거부 재확인)."""
    p = subprocess.run(["git", "-C", str(root), "ls-files", "*.py"],
                       capture_output=True, text=True)
    py_files = p.stdout.splitlines() if p.returncode == 0 else []
    shape1_sites = 0
    for rel in py_files:
        f = root / rel
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        shape1_sites += accumulation._inline_subprocess_call_count(text)

    p5 = subprocess.run(["git", "-C", str(root), "ls-files", "roles/*.json"],
                        capture_output=True, text=True)
    shape5_files = len(p5.stdout.splitlines()) if p5.returncode == 0 else 0
    return {"shape1_sites": shape1_sites, "shape5_files": shape5_files}


def accumulation_trend(root: Path) -> dict:
    """워치독 틱(issue #512 요구사항 4)마다 도는 advisory 측정 — 병합된
    트리를 훑어 모양 1/5 인스턴스 수를 세고, 직전 틱과 비교한 변화량을
    보고한다. 아무것도 막지 않는다(count report, blocking gate 아님).

    직전 틱 데이터가 없으면(첫 실행, 또는 `runs/` 이 비어있는 새 fixture
    저장소) `has_prior: False`인 유효한 "no data" artifact 를 낸다 — 예외를
    던지지 않는다."""
    state_path = root / _ACCUMULATION_TREND_STATE
    prior = None
    if state_path.is_file():
        try:
            prior = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            prior = None

    current = _current_accumulation_counts(root)
    result = {"current": current, "has_prior": prior is not None}
    if prior is not None:
        result["prior"] = prior
        result["delta"] = {
            k: current[k] - prior.get(k, 0) for k in current
        }

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(current), encoding="utf-8")
    return result


def format_accumulation_trend(trend: dict) -> str:
    c = trend["current"]
    if not trend.get("has_prior"):
        return (f"accumulation-trend: no prior tick data (first run) — "
                f"shape1_sites={c['shape1_sites']} shape5_files={c['shape5_files']}")
    d = trend["delta"]
    return (f"accumulation-trend: shape1_sites={c['shape1_sites']} "
           f"({'+' if d['shape1_sites'] >= 0 else ''}{d['shape1_sites']}), "
           f"shape5_files={c['shape5_files']} "
           f"({'+' if d['shape5_files'] >= 0 else ''}{d['shape5_files']})")


def post_sweep_comments(root: Path, violations: list[dict]) -> list[int]:
    """위반이 있는 이슈마다, 그 이슈의 위반 집합에 대해 한 번만 코멘트를 단다.

    마커에 위반 집합의 해시를 넣어 — 위반 집합이 바뀌면 새 코멘트, 그대로면
    무음(`_post_crash_comment` 와 같은 read-then-check 패턴).

    코멘트 POST 자체가 실패한 이슈 번호 목록을 돌려준다(issue #287 S7) —
    호출부가 "위반은 찾았는데 알림이 안 갔다"를 조용히 삼키지 않게.
    """
    by_issue: dict[int, list[dict]] = {}
    for v in violations:
        by_issue.setdefault(v["issue"], []).append(v)
    failed: list[int] = []
    for issue, vs in by_issue.items():
        marker = _SWEEP_COMMENT_MARKER.format(digest=_violations_digest(vs))
        comments, ok = spawn._issue_comments(root, issue)
        if ok and any(marker in c.get("body", "") for c in comments):
            continue
        slug = spawn._repo_slug(root)
        if not slug:
            failed.append(issue)
            continue
        body = f"{marker}\n\n" + format_report(vs)
        r = subprocess.run(["gh", "api", f"repos/{slug}/issues/{issue}/comments",
                        "-f", f"body={body}"], cwd=root, capture_output=True, text=True)
        if r.returncode != 0:
            failed.append(issue)
    return failed


_RATE_LIMIT_GUARD_THRESHOLD = 500


def rate_limit_remaining(root: Path) -> tuple[int | None, bool]:
    """(remaining, ok) — GraphQL 리소스의 남은 포인트, REST `gh api
    rate_limit` 로 읽는다(issue #1320). REST 조회 자체는 GraphQL 포인트를
    쓰지 않는다. `ok=False` 는 `gh` 호출/파싱 실패."""
    r = subprocess.run(["gh", "api", "rate_limit"], cwd=root,
                        capture_output=True, text=True)
    if r.returncode != 0:
        return None, False
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None, False
    remaining = data.get("resources", {}).get("graphql", {}).get("remaining")
    if not isinstance(remaining, int):
        return None, False
    return remaining, True


def main() -> int:
    root = Path(".").resolve()
    argv = sys.argv[1:]
    if "--repo" in argv:
        root = Path(argv[argv.index("--repo") + 1]).resolve()
    post = "--post" in argv

    remaining, guard_ok = rate_limit_remaining(root)
    if guard_ok and remaining < _RATE_LIMIT_GUARD_THRESHOLD:
        print(f"[watchdog] board-sweep: 미집계 (rate-limit, remaining={remaining})")
        return 2

    issue_states, _ = issue_state_index_all(root)
    violations, skips = find_violations(root, issue_states=issue_states)
    if skips:
        print("종결 일관성 스윕: 확인 불가")
        print(f"{len(skips)}건 확인 못함: " +
              ", ".join(s.get("subject", "?") for s in skips))
        if violations:
            print("(부분적으로 확인된 위반)")
            print(format_report(violations))
        if post and violations:
            failed = post_sweep_comments(root, violations)
            if failed:
                print(f"코멘트 게시 실패: 이슈 {', '.join(str(i) for i in failed)}")
        return 2
    if not violations:
        print("종결 일관성 스윕: 위반 없음")
        return 0
    print("종결 일관성 스윕: 위반 발견")
    print(format_report(violations))
    if post:
        failed = post_sweep_comments(root, violations)
        if failed:
            print(f"코멘트 게시 실패: 이슈 {', '.join(str(i) for i in failed)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
