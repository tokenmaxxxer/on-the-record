"""Relay / returned-PR machinery, extracted from spawn.py (issue #2105, extraction 1/N).

Pure move — no behavior change. spawn.py imports this module and re-exports
every moved name, so external callers and tests keep addressing them as
`spawn.<name>`.

Patching-compat mechanism: the heavily-patching test suite replaces these
functions and their helpers via `mock.patch.object(spawn, "<name>")`. To keep
those patches visible to the moved code, every cross-function reference here
goes through `_sp` — the spawn module object, injected by spawn.py right after
it imports this module (`relay._sp = sys.modules[__name__]`, which also works
when spawn.py runs as `__main__`). Shared helpers that still live in spawn.py
(`_repo_slug`, `_roster_load`, `_roster_own`, `_alive`, `ledger_write`,
`_issue_comments`, `_run_net`, `_git_env`, `ROOT`) are reached the same way —
each is a seam for a later extraction.
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# The spawn module object; set by spawn.py on import. All cross-module lookups
# resolve through it at call time so monkeypatches on spawn attributes are seen.
_sp = None


def _open_skill_prs(root: Path) -> tuple[list[dict], bool]:
    """열린 `issue-*/` 브랜치 PR 목록. `(prs, ok)` — `ok=False` 는 `gh` 조회
    실패(`_issue_comments`/`_pr_for_branch` 와 같은 튜플 관례, issue #287 S6).
    각 항목은 `number`, `headRefName`, `body`, `url`, 그리고 파싱해 뽑은
    `issue`(int) 를 담는다."""
    slug = _sp._repo_slug(root)
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


def _undispositioned_skill_prs(root: Path, exclude_issue: int | None = None
                               ) -> tuple[list[dict], bool]:
    """열린 `issue-*/` PR 중 아직 처분(phase-1 승인 또는 phase-2 머지/닫힘)
    되지 않은 것들. phase 판정은 `gates/ci.py._approved_skills_on_issue` 를
    재사용한다 — `_approved_skills_on_issue` 가 비어 있으면 phase-1 미승인,
    있으면 phase-2 진행 중(그 이슈의 phase-2 PR 은 정의상 아직 열려 있으니
    처분 전). `exclude_issue` 와 같은 이슈 번호는 건너뛴다(진행 중인 그
    이슈 자신을 막지 않는다). `(blockers, ok)` — `ok` 는 `_open_role_prs`
    의 실패를 그대로 전파한다.
    """
    prs, ok = _sp._open_skill_prs(root)
    if not ok:
        return [], False
    sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
    import ci as _ci
    # 이슈 #1013 block C: 자기 세션이 소유한 로스터 엔트리의 브랜치는
    # 게이트에서 뺀다 — `_roster_own()` 이 이미 고아 엔트리(session_id
    # 없음)는 own-scope 에도 남겨두므로, 그런 엔트리의 브랜치는 여기서도
    # 계속 걸린다(관측-손실 없음).
    # 이슈 #2098: 단, 이미 죽은(pid 사라진) own 엔트리는 제외 대상에서
    # 뺀다 — 로스터 엔트리 제거는 self-trigger 가 비동기로 하므로, 세션이
    # 죽고 PR 이 열린 바로 그 틱에도 own_branches 가 여전히 이 브랜치를
    # 물고 있어 `[returned-pr]` 이 다음 틱까지 미뤄지는 버그가 있었다.
    own_branches = {key for key, e in _sp._roster_own(_sp._roster_load(), all_scope=False).items()
                    if _sp._alive(e.get("pid", 0))}
    blockers = []
    for pr in prs:
        if exclude_issue is not None and pr["issue"] == exclude_issue:
            continue
        if pr.get("headRefName") in own_branches:
            continue
        approved_skills = _ci._approved_skills_on_issue(root, pr["issue"])
        phase = "phase2" if approved_skills else "phase1"
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
    _sp.ledger_write({"event": "returned_pr_surfaced", "source": source,
                  "issues": [b["issue"] for b in blockers], "ts": int(time.time())})


_STRANDED_PUSH_COMMENT_MARKER = "[on-the-record] stranded-relay: {key}"


def _post_stranded_push_comment(root: Path, issue: int, skill: str, branch: str,
                                reason: str, detail: str) -> None:
    """이슈 #326: `ensure_pushed()`의 push/PR-생성 실패가 조용히 사라지지
    않게, `_post_crash_comment`와 같은 멱등 read-then-check 패턴으로 이슈에
    코멘트를 남긴다. `key`는 `branch:reason`이라 같은 브랜치의 push-failed와
    이후 pr-create-failed가 서로 다른 마커를 쓰고 둘 다 드러난다."""
    key = f"{branch}:{reason}"
    marker = _sp._STRANDED_PUSH_COMMENT_MARKER.format(key=key)
    comments, ok = _sp._issue_comments(root, issue)
    if ok and any(marker in c.get("body", "") for c in comments):
        return
    slug = _sp._repo_slug(root)
    if not slug:
        return
    body = (f"{marker}\n\n"
            f"branch: {branch}\nreason: {reason}\ndetail: {detail[:200]}\n\n"
            f"The {skill}-role session's work stopped here — resume it (retry the "
            f"push/PR creation from the host), or close the issue with a stated "
            f"reason. Needs human intervention.")
    subprocess.run(["gh", "api", f"repos/{slug}/issues/{issue}/comments",
                    "-f", f"body={body}"], cwd=root, capture_output=True, text=True)


def _subject_issue_state(root: Path, issue: int) -> tuple[str | None, bool]:
    """Issue #2068: read the subject issue's CURRENT open/closed state at
    act time (level-triggered shape — the decision derives from board state
    read now, not from a stored event payload). Returns `(state, ok)` —
    `ok=False` means the `gh` lookup itself failed and `state` must not be
    read as "no such issue" (same tuple convention as
    `closure_sweep._issue_view`, which this delegates to)."""
    sys.path.insert(0, str(_sp.ROOT / "gates"))
    import closure_sweep
    try:
        return closure_sweep._issue_view(root, issue)
    except OSError:
        # gh missing, or the workspace dir itself is gone — same "lookup
        # failed" meaning as a non-zero gh exit: report ok=False so the
        # caller fails open.
        return None, False


def _flag_stale_returned_branch(issue: int, skill: str, branch: str,
                                source: str) -> None:
    """Issue #2068: a returned/stranded branch whose subject issue is
    CLOSED must never be re-opened as a PR or respawned — flag it for
    cleanup instead. Advisory only: no branch is deleted here (there is no
    existing auto-delete mechanism to hook into; the ledger event plus the
    printed line is the cleanup signal for the operator/sweeps)."""
    print(f"[stale-branch] issue #{issue} is CLOSED — refusing to "
          f"{'respawn' if source == 'respawn' else 're-open a PR'} from "
          f"returned branch {branch}; branch flagged for cleanup",
          file=sys.stderr)
    _sp.ledger_write({"event": "stale_branch_cleanup_flagged", "issue": issue,
                  "role": skill, "branch": branch, "source": source,
                  "ts": int(time.time())})


def _current_issue_task_text(root: Path, issue: int) -> str | None:
    """Issue #2068 requirement 2: a legitimate respawn must carry the
    CURRENT task text, re-read from the issue at respawn time — not the
    text captured at original spawn (stale stored text produced zero-output
    sessions concluding "nothing to do"). Returns None when the fetch
    fails, so the caller can fall back to the stored `.task.txt` — fail-open,
    mirroring the returned-PR gate's gh-failure convention (issue #680):
    a broken gh must not block a legitimate respawn."""
    sys.path.insert(0, str(_sp.ROOT / "gates"))
    import gh_rest
    data = gh_rest.fetch_issue(root, issue)
    if data is None:
        return None
    title = data.get("title", "")
    body = data.get("body", "")
    return f"Issue #{issue}: {title}\n\n{body}".rstrip() + "\n"


def ensure_pushed(work: str, issue: int, skill: str) -> dict:
    """세션이 남긴 커밋을 호스트 환경에서 push 하고, PR 이 없으면 연다.

    샌드박스의 GitHub egress 는 환경마다 다르게 막힌다(https 프록시 403,
    ssh-only 정책, 키링 불가시 등 — 전부 실측). 산출물이 로컬 커밋으로만
    남으면 보드에 존재하지 않는 것과 같으므로, on-the-record 가 세션 종료 후
    바깥에서 릴레이한다. 세션이 스스로 push/PR 에 성공했으면 전부 no-op.

    리턴은 `{"status": ..., "reason": <str|None>}` — status 는
    `nothing-to-push` / `pushed` / `push-rejected` / `pr-create-failed` /
    `pr-opened` / `pr-already-open` / `issue-closed-stale-branch` (issue
    #2068: subject issue is CLOSED — no PR is (re)opened, the branch is
    flagged for cleanup). 기존 stderr 프린트는 전부 그대로 두고
    (사람이 로그를 tail 할 때 보는 것은 안 바뀐다), 호출자가 원격의 거부
    사유를 이벤트/원장에 실을 수 있도록 구조화된 결과를 추가로 리턴한다
    (이슈 #301 B2).
    """
    br = f"issue-{issue}/{skill}"
    def git(*a):
        # env=_git_env(): 이 클로저의 유일한 네트워크 호출은 아래 push 다 —
        # rev-parse/rev-list 는 로컬이라 영향 없다. push 도 _fetch_or_halt
        # 와 같은 원인(오케스트레이터 자신의 env 에 GH_TOKEN 이 없음)으로
        # 막힐 수 있다 — 이 함수 자체가 "샌드박스 egress 가 막히면 호스트
        # 에서 대신 push 한다"는 백업 경로인데, 그 백업 경로 자신이
        # 무인증으로 막히면 산출물이 로컬 커밋으로만 남는다.
        return _sp._run_net(["git", "-C", work, *a], f"[{skill}] 호스트 git",
                        env=_sp._git_env())
    if git("rev-parse", "--verify", "-q", br).returncode != 0:
        return {"status": "nothing-to-push", "reason": None}
    ahead = git("rev-list", "--count", f"origin/{br}..{br}")
    unborn = ahead.returncode != 0          # 원격에 브랜치 자체가 없음
    n = ahead.stdout.strip() if ahead.returncode == 0 else "?"
    if unborn or n not in ("", "0"):
        r = git("push", "-q", "-u", "origin", br)
        if r.returncode != 0:
            reason = r.stderr.strip()[:200]
            print(f"[{skill}] 호스트 push 실패: {reason}", file=sys.stderr)
            _sp._post_stranded_push_comment(Path(work), issue, skill, br,
                                        "push-failed", r.stderr.strip())
            return {"status": "push-rejected", "reason": reason}
        print(f"[{skill}] 호스트에서 push 했다: {br}", file=sys.stderr)
    # "PR 있음" 판정은 OPEN 만 센다 — gh pr view <브랜치> 는 같은 브랜치의
    # 머지된 과거 PR(phase 1)도 잡아서, phase 2 의 새 PR 생성을 조용히
    # 건너뛰게 했다(실측: #60 머지 후 phase 2 커밋이 PR 없이 남았다).
    pr = subprocess.run(["gh", "pr", "list", "--head", br, "--state", "open",
                         "--json", "number", "--jq", "length"],
                        capture_output=True, text=True, cwd=work)
    has_open = pr.returncode == 0 and pr.stdout.strip() not in ("", "0")
    if not has_open:
        # Issue #2068: before (re)creating a PR from a returned branch, read
        # the subject issue's CURRENT state at act time (level-triggered —
        # branch existence alone re-opened PRs for issues already closed
        # with delivery merged; 5 stale re-opens for one closed issue in one
        # night). CLOSED => never re-open: flag the stale branch for cleanup
        # instead. A failed gh lookup fails open — same convention as the
        # returned-PR gate (issue #680): a broken gh must not strand a live
        # deliverable that genuinely needs its relay PR.
        issue_state, state_ok = _sp._subject_issue_state(Path(work), issue)
        if not state_ok:
            print(f"[{skill}] relay PR gate: issue-state lookup failed — "
                  f"failing open (returned-PR gate convention, issue #680)",
                  file=sys.stderr)
            _sp.ledger_write({"event": "issue_state_gate_fail_open",
                          "source": "relay", "issue": issue, "role": skill,
                          "ts": int(time.time())})
        elif issue_state == "CLOSED":
            _sp._flag_stale_returned_branch(issue, skill, br, source="relay")
            return {"status": "issue-closed-stale-branch", "reason": None}
        # 참조만 한다 — Closes 를 박으면 record PR 하나가 머지되는 순간
        # 이슈가 조기에 닫힌다(실측 직전 발견). 이슈 닫기는 라운드가 끝났을
        # 때 사람의 행위다 (계약 s8).
        body = (f"Part of #{issue}.\n\nOpened by on-the-record on behalf of the "
                f"{skill} role session (sandbox egress relay); the branch "
                f"content is the role's own work.\n\nrole: {skill}")
        c = subprocess.run(["gh", "pr", "create", "--head", br,
                            "--title", f"[{br}]",
                            "--body", body],
                           capture_output=True, text=True, cwd=work)
        if c.returncode == 0:
            print(f"[{skill}] PR 을 열었다: {c.stdout.strip().splitlines()[-1] if c.stdout.strip() else br}",
                  file=sys.stderr)
            return {"status": "pr-opened", "reason": None}
        else:
            reason = c.stderr.strip()[:200]
            print(f"[{skill}] PR 생성 실패: {reason}", file=sys.stderr)
            _sp._post_stranded_push_comment(Path(work), issue, skill, br,
                                        "pr-create-failed", c.stderr.strip())
            return {"status": "pr-create-failed", "reason": reason}
    return {"status": "pr-already-open", "reason": None}
