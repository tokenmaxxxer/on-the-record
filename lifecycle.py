"""Session lifecycle machinery — the reconcile CLI helpers
(`_roster_reconcile_unreported`/`_remediation_merge_sweep`), the
respawn/crash-comment cluster (`RESPAWN_*` .. `_self_trigger_respawn`,
`roster_kill`), and the workspace clean/sweep + monitor-alive GC cluster
(`_workspace_base` .. `auto_sweep`) — extracted from spawn.py (issue
#2105, extraction 7/N).

Pure move — no behavior change. spawn.py imports this module and re-exports
every moved name, so external callers and tests keep addressing them as
`spawn.<name>`.

`reconcile()` itself, `_build_expected`/`_build_observed`,
`roster_reconcile`, and `watchdog_check_one` stay in spawn.py —
gates/test_boundary.py pins the `reconcile()` signature and drive()'s call
site to spawn.py source, tests/test_spawn_observation_recovery.py pins
`roster_reconcile`'s streaming shape (bare `reconcile(` call and
`print(f"[reconcile]` in its getsource), and
gates/test_watch_rearm_registry.py pins `watchdog_check_one` strings
(#2117 report). This module reaches them through `_sp`.

Patching-compat mechanism (copied from relay.py/roster.py/plumbing.py/
watchdog.py/events.py/consult.py, extractions 1-6): every cross-function
reference here resolves at call time through `_sp` — the spawn module
object, injected by spawn.py right after it imports this module (guarded so
only the canonical spawn/__main__ module binds it), so
`mock.patch.object(spawn, "<name>")` patches stay visible to the moved
code. Cluster-internal cross-function calls also go through `_sp`.

Module-level constants whose values bind at import time moved here WITH
their users (`RESPAWN_STATE`, `RESPAWN_MAX_ATTEMPTS`,
`RESPAWN_ABSOLUTE_MAX`, the crash/stall/session-end comment markers,
`_CONTINUATION_PREAMBLE`, `_RECORD_PATH_RE`,
`_REMEDIATION_MERGE_COMMENT_MARKER`, `_ABANDONED_WORK_OUTCOMES`,
the `MONITOR_ALIVE_*` cadence constants,
`LEGACY_MONITOR_ALIVE_DIRNAME`) — spawn.py re-exports them by assignment.
`ROOT` is recomputed here with the exact expression spawn.py uses (same
directory, same import pass) because `RESPAWN_STATE` derives from it at
import time; run-time references still go through `_sp`.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

# The spawn module object; set by spawn.py on import. All cross-module lookups
# resolve through it at call time so monkeypatches on spawn attributes are seen.
_sp = None

# Import-time anchor — same expression as spawn.py.
ROOT = Path(__file__).resolve().parent

def _roster_reconcile_unreported(issue: int | None = None) -> int:
    """`spawn.py reconcile --unreported [--issue N]` (이슈 #534): roster 는
    session-end 직후 곧바로 지워지므로(`roster_remove()`, spawn.py:3988)
    끝난 세션의 흔적을 담지 못한다 — 대신 세션이 끝나도 지워지지 않는
    `_workspace_index_put()` 의 workspace 인덱스(`WORKSPACE_INDEX`)를
    훑는다. `verdict == "normal"` 인데 `_SESSION_END_COMMENT_MARKER`
    코멘트가 아직 없는 엔트리를 "미보고"로 찍는다 — self-trigger/watchdog
    이 둘 다 놓친 경우(프로세스가 코멘트 줄에 닿기 전에 죽는 등)를
    오케스트레이터가 아무 때나 한 번의 호출로 회복하는 창구다."""
    idx = _sp._workspace_index_load()
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
        verdict = _sp.session_end_verdict(work, Path(log) if log else None)
        if verdict != "normal":
            continue
        # 이슈 #533: 마커는 `_post_session_end_comment` 가 실제로 코멘트에
        # 박아 둔 bare `issue-<n>/<role>` 형태여야 한다 — workspace 인덱스
        # `key` 는 이제 레포 접두사가 붙어 그대로 쓰면 마커가 영원히
        # 안 맞아 매번 미보고로 오탐한다.
        m2 = re.search(r"issue-\d+/[^/]+$", key)
        roster_key = m2.group(0) if m2 else key
        marker = _sp._SESSION_END_COMMENT_MARKER.format(key=roster_key)
        # `_issue_comments`가 `ok=False`(코멘트를 못 읽음)면 마커 부재를
        # 확인할 수 없다 — "확인 못 함은 통과가 아니다"(#287) 원칙대로
        # 미보고 쪽으로 넘어간다(중복 코멘트를 감수).
        comments, ok = _sp._issue_comments(Path(work), issue_n)
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
    decisions_dir = root / _sp.BOARD / f"issue-{issue}" / "decisions"
    if not decisions_dir.is_dir():
        return 0
    slug = _sp._repo_slug(root)
    posted = 0
    for rem_path in sorted(decisions_dir.glob("remediation-*.md")):
        fm = _sp.frontmatter(rem_path)
        if fm.get("status") != "open":
            continue
        routed_to = fm.get("routed_to")
        if not routed_to or routed_to == "UNRESOLVED":
            continue
        round_n = fm.get("round", "?")
        candidate_pr = fm.get("candidate_pr", "?")
        marker = _sp._REMEDIATION_MERGE_COMMENT_MARKER.format(
            path=f"docs/issue-{issue}/decisions/{rem_path.name}")
        comments, ok = _sp._issue_comments(root, issue)
        if ok and any(marker in c.get("body", "") for c in comments):
            continue
        branch = f"issue-{issue}/{routed_to}"
        merged_pr = _sp._merged_pr_for_branch(root, branch)
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


RESPAWN_STATE = ROOT / "runs" / "respawn_state.json"
# Automatic respawn was removed (2026-09-03). These two names survive only
# because `spawn.py` re-exports them and out-of-tree callers may still read
# them; nothing in this repository branches on their values any more. They
# are deliberately 0 rather than 2 and 8, so that anything still consulting
# them as a retry budget gets "no retries", not a stale allowance.
RESPAWN_MAX_ATTEMPTS = 0
RESPAWN_ABSOLUTE_MAX = 0
# Kept because `_auto_respawn_check()` still requires two consecutive
# `crashed` verdicts before it reports one (issue #2969): a single verdict
# snapshot was measured misjudging live sessions as dead, and that is a
# reporting-accuracy guard, independent of whether anything is relaunched.
RESPAWN_CONSECUTIVE_CONFIRMATIONS = 2
_CRASH_COMMENT_MARKER = ("[on-the-record] {key}: crashed — not respawned, "
                         "needs a human decision")
_STALL_COMMENT_MARKER = "[on-the-record] {key}: stalled"


def _respawn_state_load() -> dict:
    try:
        return json.loads(_sp.RESPAWN_STATE.read_text())
    except (OSError, ValueError):
        return {}


def _respawn_state_save(d: dict) -> None:
    _sp.RESPAWN_STATE.parent.mkdir(exist_ok=True)
    _sp.RESPAWN_STATE.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def _post_crash_comment(root: Path, issue: int, key: str, work: str, log: str,
                        trigger: str = "crashed", absolute: bool = False) -> None:
    """Comment posted when a session is observed dead and NOT relaunched.

    Idempotent: the fixed marker string is looked up among existing
    comments first (the `_issue_comments`/`approve_scope` read-then-check
    pattern), so repeated watchdog ticks over the same dead entry leave one
    comment, not one per tick.

    Before 2026-09-03 this comment meant "the retry budget is exhausted".
    There is no retry now, so it means "this session died and nothing will
    restart it" — which is why the marker text changed. `absolute` is
    accepted and ignored: it used to select which of two caps had filled,
    and both caps are gone. It stays in the signature because `spawn.py`
    re-exports this function and callers outside this repository may still
    pass it.

    `trigger` (issue #247) still records which path observed the death
    (`watchdog-observed-crashed` / `self-triggered-abandoned`), so a reader
    can tell the two apart.
    """
    marker = _sp._CRASH_COMMENT_MARKER.format(key=key)
    comments, ok = _sp._issue_comments(root, issue)
    if ok and any(marker in c.get("body", "") for c in comments):
        return
    slug = _sp._repo_slug(root)
    if not slug:
        return
    body = (f"{marker}\n\n"
            f"trigger: {trigger}\nworkspace: {work}\nlog: {log}\n\n"
            "Automatic respawn was removed — this session will not be "
            "restarted on its own. The workspace and log above are intact; "
            "re-run the work deliberately if it is still wanted.")
    r = subprocess.run(["gh", "api", f"repos/{slug}/issues/{issue}/comments",
                    "-f", f"body={body}"], cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[spawn] 이슈 #{issue} 크래시 코멘트 게시 실패 (사람 개입 필요 경고가 "
              f"전달되지 않았다): {r.stderr.strip()}", file=sys.stderr)


def _post_stall_comment(root: Path, issue: int, key: str, work: str, log: str) -> None:
    """이슈 #325: `stalled` 판정을 최초 1회 이슈 코멘트로 남긴다.

    `stalled` 는 재스폰을 트리거하지 않는다(관찰-전용 정책, 이슈 #132 —
    바뀌지 않는다) — 다만 지금까지는 그 판정이 워치독을 부른 터미널의
    `print()` 한 줄로만 남아, 진행 중인 세션과 조용히 멈춘 세션이 밖에서
    구분되지 않았다. `_post_crash_comment` 와 같은 read-then-check
    멱등 패턴: 고정 마커가 이미 있으면 아무것도 하지 않는다."""
    marker = _sp._STALL_COMMENT_MARKER.format(key=key)
    comments, ok = _sp._issue_comments(root, issue)
    if ok and any(marker in c.get("body", "") for c in comments):
        return
    slug = _sp._repo_slug(root)
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
    verdict = _sp.session_end_verdict(work, Path(log) if log else None)
    if verdict != "normal":
        return
    marker = _sp._SESSION_END_COMMENT_MARKER.format(key=key)
    comments, ok = _sp._issue_comments(root, issue)
    if ok and any(marker in c.get("body", "") for c in comments):
        return
    slug = _sp._repo_slug(root)
    if not slug:
        return
    branch = subprocess.run(["git", "-C", work, "rev-parse", "--abbrev-ref", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    pr_number = _sp._pr_open_or_merged_for_branch(root, branch) if branch else None
    if pr_number is not None:
        line = f"PR https://github.com/{slug}/pull/{pr_number} opened"
    elif branch and not _sp._pr_list_call_ok(root, branch):
        line = "no PR (pr-check-failed)"
    else:
        line = "no PR"
    body = f"{marker} {line}\n\nworkspace: {work}\nlog: {log}"
    r = subprocess.run(["gh", "api", f"repos/{slug}/issues/{issue}/comments",
                        "-f", f"body={body}"], cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[spawn] 이슈 #{issue} session-end 코멘트 게시 실패: {r.stderr.strip()}",
              file=sys.stderr)


def _respawn_fingerprint(work: str) -> dict:
    """이슈 #678: no-progress 스트릭 판정에 쓰는 지문 — git HEAD sha 와
    `board_snapshot()` 의 안정적 해시(정렬된 dict 를 직렬화해 해시하므로,
    같은 내용이면 dict 순서가 달라도 같은 해시). 두 재스폰 시점의 지문이
    같으면 "그 사이에 관측 가능한 진행이 없었다"는 뜻이다."""
    board = _sp.board_snapshot(work)
    board_hash = hashlib.sha256(
        json.dumps(board, sort_keys=True).encode("utf-8")).hexdigest()
    return {"head": _sp._git_head(work), "board": board_hash}


_CONTINUATION_PREAMBLE = (
    "workspace contains uncommitted work from the previous session — "
    "verify briefly, then commit/push/PR; do not redo"
)

_RECORD_PATH_RE = re.compile(r"docs/issue-\d+/(reports|proposals)/")


def _classify_workspace_completion(work: str, skill: str) -> str:
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
        if _sp._RECORD_PATH_RE.search(path):
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


def _respawn_or_cap(key: str, work: str, issue: int, skill: str, log: str,
                    session_start_ts, state: dict, trigger: str,
                    single_phase: bool) -> None:
    """Crash observation for one dead session. Records the death, posts the
    human-intervention comment, and relaunches nothing.

    Automatic respawn was removed on 2026-09-03 (see the block below for
    the incident and the numbers). The function keeps its name and its
    signature so that every caller, ledger consumer and test that already
    speaks in terms of this seam keeps working; `single_phase` and
    `session_start_ts` are still accepted because callers still know them
    and the events they gate are still written, but nothing here starts a
    process any more.

    Two callers share this sequence, as before: the watchdog's `crashed`
    verdict (`_auto_respawn_check()`, issue #132) and the self-trigger
    path for abandoned uncommitted work (`_self_trigger_respawn()`, issue
    #247). Both now report instead of retrying.

    The issue-state guard below is unchanged and still runs first: a
    CLOSED subject flags its branch for cleanup and returns without
    commenting (issue #2068), and a failed `gh` lookup fails open the same
    way the returned-PR gate does (issue #680).
    """
    events_path = _sp._events_path(work)
    events = []
    if events_path.exists():
        for line in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if isinstance(ev, dict):
                events.append(ev)
    # Issue #132's per-session claim: one report per dead session, not one
    # per watchdog tick. The event name stays `respawn-attempt` so existing
    # readers of these event files keep resolving it.
    already_claimed = any(
        ev.get("type") == "respawn-attempt"
        and isinstance(ev.get("detail"), dict)
        and ev["detail"].get("session_start_ts") == session_start_ts
        for ev in events)
    if already_claimed:
        return
    root = Path(work)
    # Issue #2068: level-triggered guard — re-read the subject issue's
    # state at act time, before any side effect. CLOSED => flag the branch
    # for cleanup and say nothing else. A failed gh lookup fails open —
    # same convention as the returned-PR gate (issue #680): a broken gh
    # must not silently strand a crashed session's report.
    issue_state, state_ok = _sp._subject_issue_state(root, issue)
    if not state_ok:
        print(f"[respawn] {key}: issue-state lookup failed — failing open "
              f"(returned-PR gate convention, issue #680)", file=sys.stderr)
        _sp.ledger_write({"event": "issue_state_gate_fail_open", "source": "respawn",
                      "issue": issue, "skill": skill, "ts": int(time.time())})
    elif issue_state == "CLOSED":
        _sp._flag_stale_returned_branch(issue, skill, f"issue-{issue}/{skill}",
                                    source="respawn")
        return
    _sp._append_event(events_path, "respawn-attempt",
                  {"session_start_ts": session_start_ts, "attempt": 1,
                   "respawned": False})
    # Respawn removal: this sequence no longer relaunches anything. It
    # observes that a session died, records that fact, and posts the
    # human-intervention comment that the attempt cap used to post only
    # after exhausting its retries. Whether the work runs again is an
    # orchestrator judgment, exactly as `stalled` already was.
    #
    # Why the retry went away rather than getting its cap repaired: on
    # 2026-09-03 one session on issue #3245 became 90 sessions in about
    # twenty minutes, exhausted the account's GitHub API budget, and could
    # not be stopped from inside the tool -- `spawn.py kill` removes the
    # roster entry, but the kill itself reads as a crash, which is this
    # path's own trigger. `runs/respawn_state.json` from that machine also
    # shows the cap was not holding: 90 of its 93 keys came from that one
    # incident, and 83 of the 93 recorded no attempt count at all, because
    # since issue #2432 the roster key carries a per-lease disambiguator
    # and the respawn call did not pass the original session's
    # disambiguator through, so most respawns minted a fresh key and a
    # fresh budget.
    #
    # Repairing the key would have restored a cap on a feature with no
    # evidence of ever helping: outside that incident the same state file
    # held three keys in total, all from the same night. Measured cost,
    # unevidenced benefit -- so the retry is gone and the observation
    # stays. `_post_crash_comment()` is unchanged and still idempotent, so
    # repeated watchdog ticks over the same dead entry leave one comment.
    _sp._post_crash_comment(root, issue, key, work, log, trigger)
    _sp.ledger_write({
        "event": "crash_observed_no_respawn",
        "issue": issue, "skill": skill, "key": key,
        "trigger": trigger, "work": str(work), "log": str(log),
        "ts": int(time.time())})
    print(f"[respawn] {key}: {trigger} — 재스폰하지 않는다(자동 재스폰 제거). "
          f"워크스페이스와 로그는 남아 있다: {work}", file=sys.stderr)


def _subject_has_deliverable(root: Path, subject: str) -> dict | None:
    """Lazy-import wrapper (same idiom as `watchdog.py`'s
    `_fetch_issue_or_pr_via_cache`/`_board_read`) around
    `gates/spawn_on_pr.py::subject_has_deliverable()` -- root-level
    lifecycle.py cannot import `gates/spawn_on_pr.py` at module load time
    (that module itself imports `spawn` at its own top level, which would
    close a cycle back through this one), so the import is deferred to
    call time, same as every other root -> gates crossing in this
    codebase. See `subject_has_deliverable()`'s own docstring for why it
    answers "does `subject` already have a deliverable PR" and how it
    tells a real deliverable apart from a record-only verification PR
    (issue #2981)."""
    sys.path.insert(0, str(ROOT / "gates"))
    import spawn_on_pr
    return spawn_on_pr.subject_has_deliverable(root, subject)


def _auto_respawn_check(key: str, entry: dict, state: dict) -> None:
    """죽은 로스터 엔트리 하나에 대해 `crashed` 인지 판정하고, 그렇다면
    `_respawn_or_cap()` 에 넘긴다. `stalled`/`normal`/`in-progress` 는
    재스폰을 걸지 않는다(관찰-전용 계약 유지, 이슈 #132) — 다만 `stalled`
    는 최초 1회 이슈 코멘트로 남는다(이슈 #325): 재스폰하지 않는 것과
    아무도 모르게 재스폰하지 않는 것은 다르다.

    이슈 #2874: `entry.get("wrapper_pid")` 를 `session_end_verdict()` 에
    넘긴다 — 이게 없으면 이 함수가 `_build_expected`/`_build_observed`
    (reconcile 의 입력)와 서로 다른 판정을 내릴 수 있다: 자식(claude) pid
    만 보고 crashed 로 오판한 채로 바로 `_respawn_or_cap()` 을 태우면,
    이미 성공적으로 끝나 PR 까지 낸 세션이 재스폰된다(실측: 이슈 #2874)."""
    work = entry.get("work")
    issue = entry.get("issue")
    skill = entry.get("skill")
    if not work or issue is None or not skill:
        return
    log_path = Path(entry["log"]) if entry.get("log") else None
    verdict = _sp.session_end_verdict(work, log_path, wrapper_pid=entry.get("wrapper_pid"))
    print(f"[watchdog] {key}: {verdict}")
    if verdict == "stalled":
        _sp._post_stall_comment(Path(work), issue, key, work, entry.get("log", ""))
        return
    # 이슈 #2969: "crashed" 판정 하나로 바로 재스폰(파괴적 행동)하지
    # 않는다 — 단일 verdict 스냅샷을 믿고 살아있는 세션 둘을 죽인 사례가
    # 실측됐다(이슈 본문). 같은 key 에 대해 연속으로
    # `RESPAWN_CONSECUTIVE_CONFIRMATIONS`번 "crashed"가 나와야 아래
    # `_respawn_or_cap()`에 도달한다 — 중간에 다른 verdict 가 끼면(진짜
    # 살아있었거나 판정이 흔들린 것) 카운터를 0 으로 되돌린다. 카운터는
    # `_respawn_or_cap()`이 이미 쓰는 `state`(respawn_state.json)에
    # 얹는다 — 새 저장소를 만들지 않는다.
    confirm_prior = state.get(key, {})
    if verdict != "crashed":
        if confirm_prior.get("crash_confirms"):
            state[key] = {**confirm_prior, "crash_confirms": 0}
            _sp._respawn_state_save(state)
        return
    crash_confirms = confirm_prior.get("crash_confirms", 0) + 1
    if crash_confirms < _sp.RESPAWN_CONSECUTIVE_CONFIRMATIONS:
        state[key] = {**confirm_prior, "crash_confirms": crash_confirms}
        _sp._respawn_state_save(state)
        print(f"[watchdog] {key}: crashed 판정 {crash_confirms}/"
              f"{_sp.RESPAWN_CONSECUTIVE_CONFIRMATIONS}회 연속 확인 대기 중 — "
              "아직 재스폰하지 않음", file=sys.stderr)
        return
    # Issue #2981: a correct "crashed" verdict alone does not mean this
    # subject needs a new PR -- it only means this one session died. A
    # deliverable PR for the same subject may already exist (opened by an
    # earlier, actually-successful round this verdict merely raced with,
    # or by a sibling session), and respawning over it is exactly how one
    # issue accumulated five competing PRs (issue #2981 report). This is
    # deliberately NOT a verdict-reliability fix (that is issue #2969's
    # separate scope, untouched here) -- the gate below fires even when
    # `verdict == "crashed"` is entirely correct.
    #
    # `_subject_has_deliverable()` returns `None` on genuine absence, on a
    # subject whose only PR is record-only (verification/measurement, not
    # a deliverable), and on any lookup error -- all three fall through to
    # respawn exactly as before (fail-open toward recovery: a missed
    # respawn of a truly dead session is worse than an occasional
    # duplicate PR, issue #2981 acceptance). Only a positive match (a real
    # open or merged deliverable PR) skips the respawn, and that skip is
    # always reported by name/number here -- never silent.
    subject = f"issue-{issue}"
    existing = _sp._subject_has_deliverable(Path(work), subject)
    if existing is not None:
        pr_number = existing.get("number")
        pr_label = f"PR #{pr_number}" if pr_number is not None else existing.get("branch")
        state = existing.get("state", "existing")
        print(f"[respawn] {key}: crashed, but {subject} already has a {state} "
              f"deliverable ({pr_label}) — skipping respawn", file=sys.stderr)
        _sp.ledger_write({
            "event": "respawn_skipped_existing_deliverable",
            "issue": issue, "skill": skill, "subject": subject,
            "pr_number": pr_number, "branch": existing.get("branch"),
            "state": state, "ts": int(time.time())})
        return
    events_path = _sp._events_path(work)
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
    # 이슈 #2574 disposition: 고정값이 아니라 '상속' — 이 크래시한 세션이
    # 실제로 어느 처분으로 스폰됐는지 roster 엔트리에서 그대로 읽는다.
    # 필드가 없으면(이 필드가 생기기 전에 스폰된 낡은 엔트리) False 로
    # fail-closed — 원래 값을 모를 때 build-now 로 잘못 승격시키는
    # 쪽보다, 예전처럼 two-phase 로 두고 사람의 승인을 다시 받게 하는
    # 쪽이 안전하다.
    single_phase = entry.get("single_phase", False)
    _sp._respawn_or_cap(key, work, issue, skill, entry.get("log", ""), start_ts, state,
                    "watchdog-observed-crashed", single_phase)


_ABANDONED_WORK_OUTCOMES = ("uncommitted-work", "failed-no-commit", "silent-failure")


def _self_trigger_respawn(outcome: str, roster_key: str, work: str, issue: int,
                          skill: str, log: str, session_start_ts,
                          single_phase: bool) -> None:
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

    이슈 #2969 follow-up (독립 검증 두 건, PR #2999/#3000 이 동일하게 지적):
    이 경로는 `_auto_respawn_check()` 의 `RESPAWN_CONSECUTIVE_CONFIRMATIONS`
    게이트를 거치지 않고 `_respawn_or_cap()` 을 바로 부른다 — 의도적이다,
    빠뜨린 게 아니다. 그 게이트가 막는 위험(아직 살아있는 세션을 흔들리는
    외부 관측 하나만 믿고 죽었다고 오판)이 여기엔 없다: 이 함수는
    `_spawn_one()` 자신이 `proc.wait()` 로 프로세스 종료를 이미 직접
    확인한 뒤에만 불린다 — "살아있나?"를 추측할 대상 자체가 없다. 같은
    이유로 두 번째 관측을 기다리는 것도 불가능하다: 위 문단대로
    `roster_remove()` 가 이 시점 이미 로스터 엔트리를 지웠으므로, 어떤
    후속 워치독 틱도 이 키를 다시 볼 수 없다 — 카운터를 채우려 기다리면
    영원히 안 채워진다. 이 경로의 실제 안전장치는 다른 층에 이미 있다:
    `_respawn_or_cap()` 자신의 `RESPAWN_MAX_ATTEMPTS`/`RESPAWN_ABSOLUTE_MAX`
    상한(무한 재스폰 방지)과, 여기 도달하기 전 `silent-failure` 를 이미
    걸러내는 `fail_closed_downgrade()`(위 문단) — crash_confirms 카운터를
    이 경로에도 붙이면 카운터가 절대 2 에 못 미쳐(두 번째 관측이 원천
    불가능하므로) self-trigger 재스폰 자체가 영구히 죽는다(이슈
    #247/#675 회귀).
    """
    if outcome not in _sp._ABANDONED_WORK_OUTCOMES:
        return
    state = _sp._respawn_state_load()
    trigger = ("self-triggered-causeless" if outcome == "silent-failure"
               else "self-triggered-abandoned")
    # 이슈 #2574 disposition: 고정값 아님, 상속 — `single_phase` 는 이
    # 세션 자신을 스폰했던 처분 그대로다(spawn.py 호출부가 자기 자신의
    # `_spawn_one()` 파라미터를 그대로 넘긴다).
    _sp._respawn_or_cap(roster_key, work, issue, skill, log, session_start_ts, state,
                    trigger, single_phase)




def roster_kill(issue: int, skill: str) -> int:
    d = _sp._roster_load()
    key = f"issue-{issue}/{skill}"
    e = d.get(key)
    if not e:
        # 이슈 #2432 이후 라이브 로스터 키는 항상 `<skill>-<8-hex-리스>`
        # 접미사가 붙는다(new_lease_disambiguator()) — 그런데 `kill`
        # 서브커맨드의 사용법 문구는 여전히 `<역할>`이라 접미사 없는 bare
        # skill 이름으로 부르는 호출이 실제로 생긴다(#2873 재현). 정확히
        # 하나의 라이브 엔트리가 그 skill 이름으로 시작하면 그걸로 대신
        # 죽인다 — 둘 이상이면 조용히 하나를 고르지 않고 후보를 나열하며
        # 실패한다.
        prefix = f"issue-{issue}/{skill}-"
        candidates = {k: v for k, v in d.items() if k.startswith(prefix)}
        if len(candidates) == 1:
            key, e = next(iter(candidates.items()))
        elif len(candidates) > 1:
            names = ", ".join(sorted(candidates))
            print(f"{skill}: 라이브 후보가 여럿이다 — 전체 리스 키를 지정하라: {names}",
                  file=sys.stderr)
            return 1
        else:
            print(f"로스터에 없다: {key}", file=sys.stderr)
            return 1
    pid = e.get("pid", 0)
    if _sp._alive(pid):
        os.kill(pid, 15)
        # Respawn removal (2026-09-03): this line used to promise "재스폰이
        # 이어받는다". It was true, and it was the reason a kill could not
        # stop a runaway — the kill itself read as a crash and triggered the
        # next respawn. Nothing takes over now, and the message says so.
        print(f"종료 신호를 보냈다: {key} (pid {pid}). 워크스페이스와 라이브 "
              f"로그는 남는다 — 자동 재스폰은 없다, 다시 돌리려면 직접 스폰하라.")
    else:
        print(f"이미 죽어 있다: {key}")
    _sp.roster_remove(key)
    return 0


def _workspace_base() -> Path:
    """워크스페이스 루트: `MUSTER_WORK_DIR` 오버라이드, 기본
    `~/.tokenmaxxxer/work` (이슈 #1179 — 이전엔 `clean` CLI 분기와
    `issue_workspace()` 두 곳에 이 네 줄이 따로 있었다)."""
    base = os.environ.get("MUSTER_WORK_DIR")
    return Path(base) if base else Path.home() / ".tokenmaxxxer" / "work"


def _live_workspaces() -> dict[Path, dict]:
    """살아있는(pid alive) 로스터 엔트리를 워크스페이스 절대경로로 인덱싱."""
    roster = _sp._roster_load()
    live = {}
    for e in roster.values():
        if _sp._alive(e.get("pid", 0)):
            live[Path(e["work"]).resolve()] = e
    return live


def _sibling_checkout_roots(shared_root: Path) -> list[Path]:
    """`shared_root`(예: `~/.tokenmaxxxer/work`) 바로 아래 자식들 중,
    spawn.py 자신이 자기 `ROOT`를 잡는 것과 같은 관례("이 파일(spawn.py)이
    들어있는 디렉터리가 곧 체크아웃 루트다", `ROOT =
    Path(__file__).resolve().parent`)로 체크아웃 루트라고 인식할 수 있는
    것만 돌려준다 — 자식 안에 `spawn.py`가 있으면 그 자식이 체크아웃
    루트. 한 단계만 본다(재귀 없음) — 임의 깊이 트리를 훑지 않는다."""
    try:
        children = sorted(shared_root.iterdir())
    except OSError:
        return []
    return [c for c in children if c.is_dir() and (c / "spawn.py").is_file()]


def _sibling_live_sessions(sibling_root: Path) -> tuple[dict[Path, dict], str | None]:
    """한 sibling 체크아웃 자신의 `runs/active.json`(그 체크아웃 자신의
    STATE_ROOT/ROSTER 관례, `STATE_ROOT = ROOT / "runs"`,
    `ROSTER = STATE_ROOT / "active.json"`)에서 살아있는(pid-alive) 엔트리만
    워크스페이스 절대경로로 인덱싱 — `_live_workspaces()`와 같은 모양,
    다만 로컬 `_sp.ROSTER` 대신 남의 체크아웃 로스터를 읽는다. 예외를
    던지지 않는다: 이웃 체크아웃 하나가 망가졌다고 이쪽 체크아웃의 prune 이
    죽거나 막히면 안 된다.

    반환은 `(live, load_error)`. 로스터 파일이 아예 없으면(그 sibling 이
    한 번도 스폰한 적 없는, 정당한 빈 상태) `({}, None)` — 지금처럼 그
    sibling 의 워크스페이스는 그대로 prunable. 파일은 있는데 못 읽거나
    파싱이 깨지면(권한 오류, 쓰기 도중 읽은 절반짜리 내용) `({}, <이유>)` —
    이슈 #2603: 예전엔 이 경우도 그냥 `{}`(빈 로스터, "세션 없음")로 흡수해
    그 sibling 의 진짜 라이브 워크스페이스까지 prune 대상으로 보이게
    만들었다. `_roster_load_checked()`(이슈 #2203)가 이미 같은 절대-빈 vs
    못-읽음 구분을 하므로 그걸 그대로 재사용한다 — 두 분류기가 "모른다"의
    뜻을 따로 정의하면 이 결함이 다시 생긴다. 호출부(`_live_workspaces_union()`)
    는 `load_error`가 아니면 절대 "라이브 세션 0개"로 읽으면 안 된다."""
    roster_path = sibling_root / "runs" / "active.json"
    roster, load_error = _sp._roster_load_checked(path=roster_path)
    if load_error is not None:
        return {}, load_error
    live = {}
    for e in roster.values():
        if not isinstance(e, dict):
            continue
        if not _sp._alive(e.get("pid", 0)):
            continue
        work = e.get("work")
        if not work:
            continue
        try:
            live[Path(work).resolve()] = e
        except OSError:
            continue
    return live, None


def _live_workspaces_union() -> tuple[dict[Path, dict], list[str]]:
    """이슈 #2492: `_live_workspaces()`(체크아웃-로컬)를 이 체크아웃과 같은
    공유 작업 디렉터리(`_sp._workspace_base()`, 예: `~/.tokenmaxxxer/work`)
    아래 다른 체크아웃들의 로스터까지 합쳐서 넓힌다. 이 host 에 31개
    체크아웃이 같은 `~/.tokenmaxxxer/work`를 공유하는데(MUSTER_STATE_ROOT
    미설정이면 각자 독립적으로 ROOT/STATE_ROOT/ROSTER 를 계산) prune 이 자기
    체크아웃 로스터만 보면, 세션 A 의 prune 이 체크아웃 B 의 로스터만 아는
    살아있는 세션을 죽었다고 오판해 지울 수 있었다.

    설계 노트 — 어떤 로스터를 보는지와 왜 그게 맞고 안전한지: 로컬
    로스터(`_sp.ROSTER`, 이 체크아웃 자신의 `_live_workspaces()`) +
    공유 작업 디렉터리 바로 아래(한 단계만, 재귀 없음) 있고 체크아웃
    루트로 인식되는 sibling 들의 로스터, 그 합집합만 본다 — 지금 prune
    하는 그 작업 디렉터리를 실제로 공유하는 체크아웃으로 범위가 묶여있고,
    그보다 넓히지 않는다.

    반환은 `(live, unreadable)`. 이슈 #2603: sibling 로스터가 아예 없으면
    (정당한 빈 상태) 지금처럼 그냥 합집합에 기여하는 게 없을 뿐이다. 하지만
    있는데 못 읽거나 파싱이 깨지면(`_sibling_live_sessions()`가 돌려주는
    `load_error`) 그 sibling 을 "라이브 세션 0개"로 깎아 읽으면 안 된다 —
    그건 그 sibling 이 실제로 추적 중인 워크스페이스까지 조용히 prune
    대상으로 만든다(이 host 에서 워크스페이스 삭제가 진행 중이던 작업을
    두 번 파괴한 바로 그 경로). `unreadable`(사람이 읽을 `"<경로>: <이유>"`
    문자열 목록, 보통 비어있음)에 그 사실만 쌓아 돌려준다 — 이름을 못 아는
    sibling 하나 때문에 이 체크아웃의 prune 자체를 죽이거나 막지는
    않는다(#2597 의 그 판단은 유지): 호출부가 `unreadable`을 보고 "라이브
    여부 확인 불가"인 후보들을 개별적으로 보수적으로 남기는 몫이다."""
    live = dict(_sp._live_workspaces())
    unreadable: list[str] = []
    try:
        shared_root = _sp._workspace_base().resolve()
    except OSError:
        return live, unreadable
    try:
        own_root = _sp.ROOT.resolve()
    except OSError:
        own_root = None
    for sibling in _sp._sibling_checkout_roots(shared_root):
        try:
            sibling_resolved = sibling.resolve()
        except OSError:
            continue
        if own_root is not None and sibling_resolved == own_root:
            continue  # 이미 위에서 로컬 로스터로 커버됨
        sibling_live, load_error = _sp._sibling_live_sessions(sibling_resolved)
        if load_error is not None:
            unreadable.append(f"{sibling_resolved}: {load_error}")
            continue
        for k, v in sibling_live.items():
            live.setdefault(k, v)
    return live, unreadable


# 내용 변경으로 취급하는 porcelain 상태 문자 — staged/unstaged 를
# 가리지 않고 M(수정)/A(추가)/R(rename)/C(copy)/U(unmerged, 충돌)
# 중 하나가 X 나 Y 자리에 있으면 그 파일은 "잃을 게 있다".
_CONTENT_DIFF_CODES = frozenset("MARCU")


def _workspace_in_progress_merge(w: Path) -> bool:
    """진행 중인 merge/rebase/cherry-pick/bisect 상태가 있으면 True.
    `git rev-parse --git-dir`로 얻은 경로를 쓴다 — worktree 체크아웃은
    이 마커들이 `.git/worktrees/<name>/` 아래 따로 있어, `w / ".git"`을
    직접 뒤지면 놓친다."""
    r = subprocess.run(["git", "-C", str(w), "rev-parse", "--git-dir"],
                        capture_output=True, text=True)
    if r.returncode != 0:
        return False
    git_dir = Path(r.stdout.strip())
    if not git_dir.is_absolute():
        git_dir = w / git_dir
    return any((git_dir / marker).exists() for marker in (
        "MERGE_HEAD", "CHERRY_PICK_HEAD", "rebase-merge", "rebase-apply",
        "BISECT_LOG"))


_HARNESS_SCAFFOLDING_PREFIX = ".on-the-record/"


def _is_harness_scaffolding_path(rel: str) -> bool:
    """이슈 #3266: 세션이 시작할 때 하니스 자신이 심는 `.on-the-record/`
    아래 설정 파일(`role.json`, `model-routing.json`, `directive/*.md` 등)은
    어느 세션도 실제로 작성한 작업물이 아니다. 대부분의 워크스페이스는
    이미 이 경로를 `.gitignore`나 `.git/info/exclude`로 걸러 여기까지
    오지도 않지만(이 저장소에서 실측: 27개 살아있는 워크스페이스 중 이
    경로가 실제로 남아있던 곳은 0개), 이슈가 관측한 macOS 머신처럼 그
    설정이 없는 워크스페이스에서도 같은 답이 나와야 한다 — 경로 자체가
    하니스 소유라는 사실은 어느 워크스페이스에서나 똑같다."""
    return rel == ".on-the-record" or rel.startswith(_HARNESS_SCAFFOLDING_PREFIX)


_REPORT_STUB_PATH_RE = re.compile(r"^docs/issue-\d+/reports/.*\.md$")


_STRUCTURAL_HEADING_RE = re.compile(r"^#{1,2}(?:\s.*)?$")


def _report_stub_has_no_content(w: Path, rel: str) -> bool:
    """이슈 #3266: `docs/issue-<n>/reports/**/*.md` 파일에서 frontmatter,
    구조용 마크다운 헤딩(레코드 스켈레톤 자신의 `#`/`##` 제목 줄 — 예:
    `## What was done`), HTML 주석(`<!-- fill: ... -->`), 스켈레톤 기본값
    `None.` 을 걷어내고도 실질 텍스트가 하나도 안 남으면 True — 세션이
    시작할 때 만들고 한 글자도 못 채운 채 죽은 리포트 스텁의 모양 그대로다
    (`~/.tokenmaxxxer/salvage-20260903` 코퍼스로 검증: 리포트 성격 파일
    151개 중 131개가 이 모양이었고, 나머지 20개 — consult-log 한 줄짜리까지
    포함 — 는 전부 이 필터를 통과하는 실질 프로즈가 남았다).

    이슈 #3266 라운드 2 (PR #3272 독립검증): `#` 로 시작하는 줄을 전부
    걷어내면 헤딩 텍스트 자체에 실제 소견이 실린 줄(`### Root cause: ...`)
    이나 헤딩 문법조차 아닌 bare `#`-접두 줄(`#3266 was the root cause,
    ...`)까지 같이 사라져 실제 내용을 스텁으로 오판했다 — 레코드 스켈레톤은
    항상 레벨 1(문서 제목)·레벨 2(섹션 제목)만 구조용으로 쓰고 그 텍스트는
    항상 일반 제목이다, 레벨 3 이상이나 `#` 뒤에 공백 없이 바로 글자가
    오는 줄은 스켈레톤 구조가 아니라 본문이므로 걷어내지 않는다.

    `_classify_workspace_completion()`(위, 이슈 #1982)의 "frontmatter 만
    걷어내고 strip() 이 truthy 면 finished"보다 훨씬 엄격하게 걷어낸다 —
    그 함수는 이어서 할 작업 안내 문구를 붙일지만 결정해 과대 판정의
    대가가 작지만(스텁을 finished 로 오판해도 다음 세션이 손해볼 게
    없다), 여기서는 삭제 여부를 가르는 판정이라 헤딩/주석/기본값까지
    걷어내지 않으면 모든 스텁이 "내용 있음"으로 남아 이 이슈가 고치려는
    문제 그대로 재현된다."""
    if not _REPORT_STUB_PATH_RE.match(rel):
        return False
    path = w / rel
    try:
        st = path.lstat()
    except OSError:
        return False
    if stat.S_ISLNK(st.st_mode):
        # 이슈 #3266 라운드 2 (PR #3271 독립검증): 워크스페이스 밖을
        # 가리키는 심볼릭 링크는 그 바깥 파일의 내용이 아니라 "이
        # 워크스페이스 자신의 파일에 내용이 있는가"를 물어야 한다 —
        # 컨테인먼트를 먼저 확인하지 않으면 외부 타겟이 우연히 스텁
        # 모양이라는 이유만으로 워크스페이스 자신의 파일을 삭제 대상으로
        # 오판한다.
        try:
            target = path.resolve(strict=True)
        except OSError:
            return False
        try:
            target.relative_to(w.resolve(strict=True))
        except ValueError:
            return False
        try:
            st = target.stat()
        except OSError:
            return False
    if not stat.S_ISREG(st.st_mode):
        # 이슈 #3266 라운드 2 (PR #3271 독립검증): FIFO 는 OSError 를
        # 던지지 않고 read_text() 를 무기한 블록시킨다 -- 열기 전에
        # 정규 파일인지부터 확인해 그 read 자체를 시도하지 않는다.
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            nl = text.find("\n", end + 1)
            text = text[nl + 1:] if nl != -1 else ""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    for line in text.splitlines():
        s = line.strip()
        if not s or s == "None.":
            continue
        if _STRUCTURAL_HEADING_RE.match(s):
            continue
        return False
    return True


def _is_reclaimable_untracked_noise(w: Path, rel_bytes: bytes) -> bool:
    """이슈 #3266: untracked-and-not-gitignored 파일 하나가 그래도 "잃을 게
    없는" 두 모양(하니스 스캐폴딩, 내용 없는 리포트 스텁) 중 하나인지."""
    rel = os.fsdecode(rel_bytes)
    return (_is_harness_scaffolding_path(rel)
            or _report_stub_has_no_content(w, rel))


def _workspace_untracked_not_ignored(w: Path) -> list[bytes]:
    """gitignore 에 안 걸리는 untracked 파일 목록(이슈 #2960: basename
    화이트리스트 대신 `git check-ignore` 로 판정 — 그 리포 자신의
    `.gitignore` 가 harness noise 든 빌드 산출물이든 이미 아는 파일을
    걸러내고, 모르는 새 파일은 안전 기본값대로 "잃을 게 있다"로 남는다).

    이슈 #3266: gitignore 를 통과한 뒤에도 하니스 스캐폴딩이나 내용 없는
    리포트 스텁(`_is_reclaimable_untracked_noise()`)이면 "잃을 게 있다"
    목록에서 뺀다 — 크래시한 세션이 시작 때 만들고 절대 못 채우는 바로 그
    모양이라, 이 둘을 빼지 않으면 정리가 가장 필요한 워크스페이스일수록
    지우면 안 되는 것으로 영원히 오판된다. 내용이 조금이라도 있는 리포트,
    다른 untracked 파일(예: 실험 산출물 JSON)은 이 필터를 안 타고 그대로
    "잃을 게 있다"로 남는다."""
    listed = subprocess.run(
        ["git", "-C", str(w), "ls-files", "-z", "--others"],
        capture_output=True).stdout
    untracked = [p for p in listed.split(b"\0") if p]
    if not untracked:
        return []
    checked = subprocess.run(
        ["git", "-C", str(w), "check-ignore", "-z", "--stdin"],
        input=b"\0".join(untracked), capture_output=True)
    ignored = {p for p in checked.stdout.split(b"\0") if p}
    return [p for p in untracked
            if p not in ignored
            and not _sp._is_reclaimable_untracked_noise(w, p)]


def _workspace_clean_state(
    w: Path, live: dict[Path, dict], unreadable: list[str] | None = None,
) -> tuple[str | None, str]:
    """워크스페이스 하나가 지워도 안전한지 판정한다. `(reason, detail)` —
    `reason` 이 `None` 이면 안전(지워도 됨), 아니면 남기는 이유
    (`"live"`/`"unknown"`/`"dirty"`) 와 사람이 읽을 상세 문자열.

    이슈 #2960: 판정 기준은 "작업트리가 깨끗한가"가 아니라 "지우면 뭘
    잃는가"다 — unpushed 커밋, stash, 진행 중 merge/rebase, staged/
    unstaged 내용 변경(M/A/R/C/U), gitignore 안 걸리는 untracked 파일
    중 하나라도 있으면 "잃을 게 있다"(dirty). 삭제(D)만 있는 트리는
    예외: 지워진 내용은 이미 커밋 히스토리에 있으므로, 그 커밋이 이미
    push 돼 있을 때만(= `ahead` 가 비어있을 때만) 안전하다 — 커밋이
    unpush 상태면 D 항목과 무관하게 `ahead` 검사가 그대로 dirty 로
    잡는다.

    `roster_clean()`(수동)과 `auto_sweep()`(자동, 이슈 #1179)이 같은 판정을
    쓴다 — 두 곳에 독립적으로 안전 검사를 두면 한쪽만 고치고 다른 쪽은
    #1124 보장이 조용히 깨진다.

    `unreadable`(이슈 #2603, `_live_workspaces_union()`이 돌려주는 못-읽은
    sibling 목록): 이번 실행에 못 읽은 sibling 로스터가 하나라도 있으면,
    이 워크스페이스가 `live`에 없다는 사실이 "죽었다"를 증명하지 못한다 —
    그 sibling 의 로스터를 읽을 수 있었다면 이 경로를 라이브로 알았을 수도
    있다("unknown must not mean empty", 이슈 #2603). 그래서 git-dirty
    판정으로 내려가지 않고 바로 `"unknown"`으로 남긴다 — 실제로 죽었는지는
    다음 실행(sibling 이 다시 읽힐 때)에 다시 판정된다."""
    e = live.get(w.resolve())
    if e is not None:
        return ("live",
                f"실행 중인 세션 있음: issue-{e.get('issue', '?')}/"
                f"{e.get('skill', '?')}, pid {e.get('pid', '?')}")
    if unreadable:
        return ("unknown",
                 "이웃 체크아웃 로스터를 못 읽어 라이브 여부 확인 불가 — "
                 + "; ".join(unreadable))

    if _sp._workspace_in_progress_merge(w):
        return ("dirty", "미보존 작업 있음  [merge/rebase 진행 중]")

    stash_out = subprocess.run(["git", "-C", str(w), "stash", "list"],
                               capture_output=True, text=True).stdout.strip()
    if stash_out:
        return ("dirty",
                 f"미보존 작업 있음  [stash {len(stash_out.splitlines())}건]")

    raw_st = subprocess.run(["git", "-C", str(w), "status", "--porcelain"],
                            capture_output=True, text=True).stdout.strip()
    st_lines = raw_st.splitlines() if raw_st else []
    tracked_lines = [ln for ln in st_lines if not ln.startswith("??")]
    content_diff_lines = [ln for ln in tracked_lines
                           if set(ln[:2]) & _sp._CONTENT_DIFF_CODES]
    not_ignored = _sp._workspace_untracked_not_ignored(w)

    ahead = subprocess.run(
        ["git", "-C", str(w), "log", "--branches", "--not", "--remotes",
         "--oneline"], capture_output=True, text=True).stdout.strip()
    if ahead and not content_diff_lines and not not_ignored:
        # 레거시 워크스페이스는 생성 뒤 다시 fetch 된 적이 없어, 브랜치가
        # 이미 origin 에 머지됐어도 로컬 remote-tracking ref 가 그 사실을
        # 모른다 — "ahead" 로 영원히 오판된다(실측, accessibility-rulebook
        # issue-19: fetch 전 2건 ahead, fetch 후 0건). 다른 이유로 이미
        # dirty 가 아닐 때만 한 번 fetch 로 갱신하고 재판정한다 — fetch 는
        # 로컬을 지우지 않으니 안전.
        try:
            subprocess.run(["git", "-C", str(w), "fetch", "-q", "--all"],
                           capture_output=True, text=True, timeout=30)
        except (subprocess.TimeoutExpired, OSError):
            pass
        ahead = subprocess.run(
            ["git", "-C", str(w), "log", "--branches", "--not",
             "--remotes", "--oneline"],
            capture_output=True, text=True).stdout.strip()

    if content_diff_lines or not_ignored or ahead:
        detail = "미보존 작업 있음"
        if content_diff_lines:
            detail += f"  [내용 변경 {len(content_diff_lines)}건]"
        if not_ignored:
            detail += f"  [미추적 파일 {len(not_ignored)}건]"
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
        if outcome is not None and outcome not in _sp.LANDED_OUTCOMES:
            archive_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(sibling), str(archive_dir / sibling.name))
        else:
            sibling.unlink()


def _worktree_max_age_hours() -> float:
    """`MUSTER_WORKTREE_MAX_AGE_HOURS` — 기본 24시간. `check_runner.py`/
    `reexecution_gate.py`가 만드는 임시 worktree 는 검사 하나(분 단위)
    동안만 살아야 정상이다 — 워크스페이스의 `MUSTER_CLEAN_MAX_AGE_DAYS`
    (기본 14일)보다 훨씬 짧은 게 맞다: 그 값은 사람이 며칠씩 붙들고 있는
    워크스페이스용이고, 이 worktree 는 한 프로세스의 생애 동안만 존재할
    임시물이다."""
    return float(os.environ.get("MUSTER_WORKTREE_MAX_AGE_HOURS", "24"))


def _worktree_last_activity(path: Path) -> float:
    """`path`(worktree 루트) 자신의 mtime 이 아니라, 그 아래 모든
    파일/서브디렉터리 mtime 중 최댓값을 본다. warrant-hunt 실측(이슈
    #2383, 2026-08-25): git 은 디렉터리 엔트리가 추가/삭제/rename 될 때만
    그 디렉터리 자체의 mtime 을 갱신한다 — 이미 있는 파일에 계속
    append/overwrite 하는(체크 실행 중 로그·아티팩트를 쓰는 것과 같은)
    프로세스는 최상위 디렉터리의 mtime 을 전혀 안 건드린다. 최상위
    mtime 만 보면, 체크아웃 직후로 고정된 그 값이 24시간을 넘기는 순간
    지금 실제로 쓰는 중인 worktree 도 '오래됨'으로 오판해 지운다 —
    재현: 디렉터리를 backdate 하고 그 안 기존 파일 하나만 방금 건드린
    뒤 `_prune_worktrees`를 부르면, 고쳐지기 전 코드는 그 worktree를
    지웠다."""
    latest = path.stat().st_mtime
    for p in path.rglob("*"):
        try:
            latest = max(latest, p.stat().st_mtime)
        except OSError:
            continue
    return latest


def _prune_worktrees(repo: Path, max_age_hours: float | None = None,
                      now: float | None = None) -> None:
    """`spawn.py clean`이 워크스페이스 삭제와 같은 지나가는 길에 `repo`(호출
    시점의 orchestrator 체크아웃, 보통 `-C`/cwd)에 등록된 `git worktree`
    항목도 훑는다 — issue #2383: `check_runner.py`/`reexecution_gate.py`가
    만드는 임시 worktree 는 각자 try/finally 로 지우지만, 프로세스가
    죽으면(타임아웃/OOM) 그 finally 는 안 돈다. 이 정기 스윕이 그 잔재의
    유일한 안전망이다. `repo`가 git 체크아웃이 아니면 조용히 건너뛴다 —
    이 정리는 있으면 좋은 것이지 실패해야 할 전제조건이 아니다.

    두 단계로 훑는다(issue #2383 Acceptance check 2 — count 뿐 아니라
    age 도 monitored/pruned 여야 한다): 1) `git worktree prune`은 디렉터리가
    이미 사라진 등록 항목만 지운다(existence 축). 2) 그러고도 디렉터리가
    여전히 남아있는 항목은 나이만으로는 안 걸린다 — 하드-킬된 프로세스가
    지우다 만 게 아니라 아예 못 지운 경우 디렉터리 자체가 그대로 남기
    때문이다. 그 잔재를 잡으려면 별도로 각 worktree 의 마지막 활동 시각
    (`_worktree_last_activity()` — 트리 전체에서 가장 최근 mtime, 최상위
    디렉터리 자신의 mtime 만으로는 안 된다)을 `max_age_hours`와 비교해
    오래된 것을 `git worktree remove --force`로 지운다(age 축) — 두
    축이 잡는 실패 모드가 다르다."""
    if not (repo / ".git").exists():
        return
    before = subprocess.run(["git", "-C", str(repo), "worktree", "list"],
                            capture_output=True, text=True).stdout.splitlines()
    if len(before) > 1:
        print(f"worktree 목록 (정리 전 {len(before)}개):")
        for line in before:
            print(f"  {line}")
    pruned = subprocess.run(["git", "-C", str(repo), "worktree", "prune", "-v"],
                            capture_output=True, text=True)
    if pruned.stdout.strip():
        print(f"worktree prune: {pruned.stdout.strip()}")

    max_age_hours = _worktree_max_age_hours() if max_age_hours is None else max_age_hours
    now = time.time() if now is None else now
    max_age_sec = max_age_hours * 3600
    listing = subprocess.run(["git", "-C", str(repo), "worktree", "list", "--porcelain"],
                             capture_output=True, text=True).stdout
    repo_resolved = repo.resolve()
    for i, block in enumerate(listing.split("\n\n")):
        lines = block.splitlines()
        if not lines or not lines[0].startswith("worktree "):
            continue
        if i == 0:
            continue  # 첫 항목은 항상 이 `repo` 자신(주 체크아웃) — 절대 안 건드린다.
        wt_path = Path(lines[0][len("worktree "):])
        try:
            if wt_path.resolve() == repo_resolved:
                continue
            age_sec = now - _worktree_last_activity(wt_path)
        except OSError:
            continue  # 디렉터리가 이미 없다 — existence 축(위)이 이미 처리했다.
        if age_sec <= max_age_sec:
            continue
        print(f"worktree age-prune: {wt_path} ({age_sec / 3600:.1f}h > "
              f"{max_age_hours}h) — 지운다")
        removed = subprocess.run(
            ["git", "-C", str(repo), "worktree", "remove", "--force", str(wt_path)],
            capture_output=True, text=True)
        if removed.returncode != 0:
            print(f"worktree age-prune 실패 (non-fatal): {wt_path}  "
                  f"[{removed.stderr.strip()}]")


def roster_clean(wb: Path, issue: int | None, repo: Path | None = None,
                 dry_run: bool = False) -> int:
    """`spawn.py clean [--issue N] [--dry-run]`: 안전한 것만 지운다 — 미커밋
    변경 없음 + origin 에 없는 커밋 없음. 워크스페이스 디렉터리는 그 조건만
    지키면 그대로 삭제한다(이슈 #1124 범위 밖). 형제 파일(로그 등)은
    `_delete_workspace()` 가 archive-or-delete 판정을 한다.

    `repo`(주어지면, 보통 호출 시점의 `-C`/cwd)에 등록된 stale `git
    worktree` 항목도 같이 정리한다(issue #2383 — 누적된 채 방치되지 않게
    routine landing/cleanup 의 일부로 만든다).

    `dry_run` (이슈 #3274): 아무것도 지우지 않고 무엇을 지웠을지만 찍는다.
    이 함수는 원래 이 파라미터가 없었고 `spawn.py` 의 `clean` 분기도
    `a.dry_run` 을 넘기지 않았다 — 최상위 `--dry-run` 플래그는 파싱만 되고
    이 경로에서 읽히지 않아, `spawn.py clean --dry-run` 이 실제로 삭제했다.
    바로 두 줄 아래 `sweep-orphans` 분기는 같은 플래그를 제대로 넘긴다.
    운영자가 PR 비교용으로 "읽기 전용"이라 믿고 두 번 실행했고 워크스페이스
    하나가 실제로 사라졌다 — 무엇이었는지는 아무 기록도 남지 않아 특정할 수
    없었다. 되돌릴 수 없는 행동에 안전해 보이는 이름이 붙어 있는 것이
    이 결함의 본체다.

    `worktree` prune 도 dry-run 에서는 건너뛴다 — 그것도 상태를 바꾼다."""
    if repo is not None and not dry_run:
        _prune_worktrees(repo)
    live, unreadable = _sp._live_workspaces_union()
    for msg in unreadable:
        print(f"경고: 이웃 체크아웃 로스터를 읽지 못함 — {msg} — 그 로스터가 "
              f"아는 워크스페이스를 놓쳤을 수 있어, 이번 정리에서 확인 불가 "
              f"항목은 남긴다")
    log_outcomes = _sp._ledger_log_outcomes()
    archive_dir = wb / ".archived-logs"

    scope = f"-issue-{issue}-" if issue is not None else None
    removed = kept = failed = 0
    for w in sorted(wb.glob("*")) if wb.is_dir() else []:
        if not (w / ".git").is_dir():
            continue
        if scope is not None and scope not in w.name:
            continue
        reason, detail = _sp._workspace_clean_state(w, live, unreadable)
        if reason is not None:
            print(f"남김 ({detail}): {w.name}")
            kept += 1
            continue
        if dry_run:
            # 이슈 #3274: 여기서 실제로 지우지 않는다. 세는 건 그대로 세서
            # 요약 숫자가 실제 실행과 같게 나오게 한다 — dry-run 이 다른
            # 숫자를 내면 비교 용도로 쓸 수 없다.
            print(f"[dry-run] 지웠을 것: {w.name}")
            removed += 1
            continue
        try:
            _sp._delete_workspace(w, wb, log_outcomes, archive_dir)
        except Exception as ex:
            print(f"실패 (삭제 중 예외): {w.name}  [{ex}]")
            failed += 1
            continue
        # 이슈 #3274: 되돌릴 수 없는 행동은 흔적을 남긴다. stdout 한 줄은
        # 호출자가 잡아두지 않으면 사라진다 — 실제로 그래서 무엇이
        # 지워졌는지 특정할 수 없었다.
        _sp.ledger_write({"event": "workspace_reclaimed", "workspace": w.name,
                      "path": str(w), "issue": issue, "ts": int(time.time())})
        print(f"지움: {w.name}")
        removed += 1
    prefix = "[dry-run] " if dry_run else ""
    summary = f"{prefix}정리 끝 — 지움 {removed}, 남김 {kept}"
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
        root = _sp._monitor_alive_root()
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
        candidate = repo_root / _sp.LEGACY_MONITOR_ALIVE_DIRNAME
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
        stats = _sp.gc_monitor_alive()
        print(f"monitor-alive gc: removed {stats['removed']}, "
              f"kept {stats['kept']}, errors {stats['errors']}")
    except Exception as ex:
        print(f"monitor-alive gc: 실패 (예외, non-fatal) [{ex}]")
    try:
        for legacy in _sp.detect_legacy_monitor_alive_dirs(cwd):
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


def _workspace_merge_trigger_status(w: Path) -> tuple[bool, str]:
    """이슈 #2447: 세션이 이미 끝난(=`_workspace_clean_state()`가 이미
    non-live/non-dirty 로 판정한) 워크스페이스가 age/size 상한과 무관하게
    지금 지워도 되는지 — 그 브랜치의 PR 이 gh API 로 확인된 MERGED 일
    때만. 독립 안전검사가 아니라 `auto_sweep()`의 이미-안전한 후보
    집합 위에 얹는 가속 신호이므로, 호출자가 `_workspace_clean_state()`를
    먼저 통과시킨 뒤에만 불러야 한다.

    `(removable, detail)` 를 돌려준다 — `removable=False` 인 모든 경로
    (브랜치 없음, gh API 호출 자체 실패, PR 이 아직 open/없음)는 "머지
    안 됨"이 아니라 "모름/아직"으로 취급해 이 트리거를 no-op 으로
    물러나게 한다: 그 워크스페이스는 그대로 기존 age/size prune 판정으로
    넘어간다(요구사항 — GitHub API 실패가 age/size prune 을 막으면
    안 된다)."""
    branch = subprocess.run(
        ["git", "-C", str(w), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True).stdout.strip()
    if not branch:
        return (False, "no-branch")
    if not _sp._pr_list_call_ok(w, branch):
        return (False, "pr-check-failed")
    merged_pr = _sp._merged_pr_for_branch(w, branch)
    if merged_pr is None:
        return (False, "not-merged")
    return (True, f"PR #{merged_pr} merged")


def _temp_repos_base() -> Path:
    """이슈 #2973: 세션이 자기 몫 scratch repo 복사본/빌드 트리를 두는
    plugin-managed 루트. `_workspace_base()`(세션 워크스페이스 자체,
    이슈 #2960 스코프)와는 별개 위치라 아래 `sweep_temp_repos()`가
    `~/.tokenmaxxxer/work` 를 절대 건드리지 않는다. `MUSTER_TEMP_REPOS_ROOT`
    오버라이드는 `_workspace_base()`의 `MUSTER_WORK_DIR` 관례와 같다 —
    운영/테스트 격리용이며, 스포너가 심어 주는 값이지 세션이 스스로
    고르는 값이 아니다."""
    override = os.environ.get("MUSTER_TEMP_REPOS_ROOT")
    if override:
        return Path(override)
    return Path.home() / ".tokenmaxxxer" / "tmp-repos"


def session_temp_root(roster_key: str) -> Path:
    """세션 하나의 관리형 temp repo root:
    `<_temp_repos_base()>/<roster_key 를 세이프하게 바꾼 이름>`, 없으면
    만든다. 스포너가 이 경로를 `MUSTER_TEMP_ROOT` env 로 심어 주면,
    세션이 repo 복사본/빌드 트리를 두려고 `/tmp/tas-<n>-repos` 같은
    경로를 스스로 고르는 대신 이 plugin-managed 위치를 쓰게 된다 —
    그래야 `sweep_temp_repos()`가 세션의 협조 없이도 되찾을 수 있다
    (이슈 #2973)."""
    safe_name = roster_key.replace("/", "-")
    root = _sp._temp_repos_base() / safe_name
    root.mkdir(parents=True, exist_ok=True)
    return root


def sweep_temp_repos(base: Path | None = None,
                      max_age_days: float | None = None,
                      now: float | None = None) -> dict[str, int]:
    """`session_temp_root()`가 만든 세션별 temp repo root 를 나이 기준으로
    되찾는다(이슈 #2973) — 세션이 스스로 지우는 것에 기대지 않는다:
    턴 한도에서 죽거나 자기 정리 코드에 닿기 전에 크래시한 세션도 이
    스윕이 되찾는다. `/tmp`를 이름 패턴으로 훑지 않는다 — 오직
    plugin-managed `base` 아래만 본다. 살아있는(pid-alive) 세션의
    roster key 를 `session_temp_root()`와 같은 규칙으로 새니타이즈해
    디렉터리 이름과 비교하므로, 그 세션의 temp root 는 나이와 무관하게
    지우지 않는다 — 역-매핑 없이 한 방향 규칙 비교만으로 성립한다.

    `base`/`max_age_days`/`now`: 테스트가 위치/정책/시각을 주입한다.
    빈 상태(`base`가 없거나 항목이 없음)는 removed=kept=failed=0 을
    돌려준다."""
    base = base if base is not None else _sp._temp_repos_base()
    now = now if now is not None else time.time()
    max_age_days = (max_age_days if max_age_days is not None
                     else _sp._clean_max_age_days())
    max_age_sec = max_age_days * 86400
    roster = _sp._roster_load()
    live_names = {k.replace("/", "-") for k, e in roster.items()
                  if _sp._alive(e.get("pid", 0))}
    removed = kept = failed = 0
    entries = sorted(base.glob("*")) if base.is_dir() else []
    for entry in entries:
        if not entry.is_dir():
            continue
        if entry.name in live_names:
            kept += 1
            continue
        try:
            mtime = max((p.stat().st_mtime for p in entry.rglob("*")),
                        default=entry.stat().st_mtime)
        except OSError:
            failed += 1
            continue
        if now - mtime > max_age_sec:
            try:
                shutil.rmtree(entry)
                removed += 1
            except OSError:
                failed += 1
        else:
            kept += 1
    return {"removed": removed, "kept": kept, "failed": failed}


def auto_sweep(wb: Path, max_age_days: float, max_bytes: int,
               now: float | None = None) -> dict[str, int]:
    """이슈 #1179: 스폰-타임 자동 정리. `roster_clean()` 과 같은 안전 판정
    (`_workspace_clean_state()`)만 지운다 — 살아있는 세션, 미커밋/미push
    작업은 절대 건드리지 않는다(#1124 보장 유지).

    세 가지 독립 트리거, 이 순서로 본다(각 트리거가 막는 실패 모드가
    다르다):
    1) merge-트리거(이슈 #2447, additive): 안전 후보 중 브랜치 PR 이
       이미 MERGED 로 확인되면 나이/크기와 무관하게 바로 지운다 — 세션이
       끝나고 PR 이 머지된 순간부터는 더 지킬 게 없다. gh API 호출이
       실패/에러면 이 트리거는 그 워크스페이스에 한해 no-op 으로 물러나고
       (`_workspace_merge_trigger_status()`), 아래 age/size 판정으로
       그대로 넘어간다 — API 실패가 기존 prune 을 막지 않는다.
    2) age-bound: `max_age_days` 보다 오래된 안전 워크스페이스는 무조건
       지운다.
    3) size-bound: 그러고도 안전 워크스페이스 총합 크기가 `max_bytes`
       를 넘으면, 오래된 것부터 더 지워서 bound 아래로 낮춘다.
    나이만으로는 스폰이 늘면 디스크가 계속 자라고, 크기만으로는 방금
    생긴 워크스페이스도 지울 수 있다.

    `now`: 테스트가 `time.time()` 대신 고정 시각을 주입한다."""
    now = now if now is not None else time.time()
    live, unreadable = _sp._live_workspaces_union()
    for msg in unreadable:
        print(f"[auto-sweep] 경고: 이웃 체크아웃 로스터를 읽지 못함 — {msg} — "
              f"확인 불가 워크스페이스는 이번 스윕에서 남긴다", file=sys.stderr)
    log_outcomes = _sp._ledger_log_outcomes()
    archive_dir = wb / ".archived-logs"
    max_age_sec = max_age_days * 86400

    candidates = []  # (mtime, size, path)
    if wb.is_dir():
        for w in sorted(wb.glob("*")):
            if not (w / ".git").is_dir():
                continue
            reason, _detail = _sp._workspace_clean_state(w, live, unreadable)
            if reason is not None:
                continue
            try:
                mtime = w.stat().st_mtime
            except OSError:
                continue
            candidates.append([mtime, None, w])

    removed = failed = 0
    by_trigger = {"merge": 0, "age": 0, "size": 0}

    def _reap(entry, trigger: str, detail: str = "") -> None:
        nonlocal removed, failed
        try:
            _sp._delete_workspace(entry[2], wb, log_outcomes, archive_dir)
            removed += 1
            by_trigger[trigger] += 1
            suffix = f" ({detail})" if detail else ""
            print(f"[auto-sweep] 지움 ({trigger}-triggered): "
                  f"{entry[2].name}{suffix}", file=sys.stderr)
        except Exception as ex:
            print(f"[auto-sweep] 실패 (삭제 중 예외): {entry[2].name}  [{ex}]",
                  file=sys.stderr)
            failed += 1

    after_merge = []
    for entry in candidates:
        removable, detail = _sp._workspace_merge_trigger_status(entry[2])
        if removable:
            _reap(entry, "merge", detail)
        else:
            after_merge.append(entry)

    remaining = []
    for entry in after_merge:
        if now - entry[0] > max_age_sec:
            _reap(entry, "age")
        else:
            remaining.append(entry)

    if max_bytes > 0 and remaining:
        for entry in remaining:
            entry[1] = _sp._dir_size_bytes(entry[2])
        remaining.sort(key=lambda e: e[0])  # 오래된 것부터
        total = sum(e[1] for e in remaining)
        i = 0
        while total > max_bytes and i < len(remaining):
            entry = remaining[i]
            total -= entry[1]
            _reap(entry, "size")
            i += 1

    if removed or failed:
        print(f"[auto-sweep] 지움 {removed} "
              f"(merge {by_trigger['merge']}, age {by_trigger['age']}, "
              f"size {by_trigger['size']})"
              + (f", 실패 {failed}" if failed else ""), file=sys.stderr)
    return {"removed": removed, "failed": failed}


# 이슈 #2443: `_delete_workspace()`(위)가 세대별 세션 로그/`.events.jsonl`/
# `.events.offset`/`.watcher.log`/`.task.txt` 같은 sidecar 산출 파일을
# 지우는 건 그 짝이 되는 워크스페이스 디렉터리를 지우는 그 순간뿐이다
# (`w.parent.glob(w.name + ".*")`, 위). `auto_sweep()`/`roster_clean()`
# 모두 `wb.glob("*")`로 디렉터리만 순회하므로, 짝 디렉터리가 이미 없어진
# (수동 삭제·크래시로 워크스페이스만 사라지고 sidecar 만 `~/.tokenmaxxxer/
# work` 바로 아래 flat 하게 남는) sidecar 세트는 두 정리 경로 어느 쪽도
# 절대 방문하지 않는다 — 무한정 쌓인다. 다섯 패턴을 전부 여기서 인식한다.
_SIDECAR_SUFFIX_MARKERS = (".events.jsonl", ".events.offset",
                            ".watcher.log", ".task.txt")
_SIDECAR_SESSION_LOG_RE = re.compile(r"^(.+)\.session\.[^./]+\.[^./]+\.log$")


def _sidecar_workspace_name(filename: str) -> str | None:
    """`filename`이 다섯 sidecar 패턴 중 하나에 맞으면 그 짝 워크스페이스
    디렉터리 이름(`w.name`)을, 안 맞으면 `None`을 돌려준다."""
    for marker in _SIDECAR_SUFFIX_MARKERS:
        if filename.endswith(marker):
            return filename[: -len(marker)]
    m = _SIDECAR_SESSION_LOG_RE.match(filename)
    return m.group(1) if m else None


def _sidecar_groups(wb: Path) -> dict[str, list[Path]]:
    """`wb` 바로 아래 flat 하게 놓인 sidecar 파일들을 짝 워크스페이스 이름으로
    그룹핑만 한다(orphan 판정은 `_orphaned_sidecar_groups()`가 한다) — 이슈
    #3118 `sweep_orphans()`와 `_prune_orphaned_sidecars()`가 같은 그룹핑을
    공유한다."""
    groups: dict[str, list[Path]] = {}
    if wb.is_dir():
        for p in wb.iterdir():
            if not p.is_file():
                continue
            name = _sidecar_workspace_name(p.name)
            if name is None:
                continue
            groups.setdefault(name, []).append(p)
    return groups


def _orphaned_sidecar_groups(wb: Path, live: dict[Path, dict], now: float,
                              max_age_sec: float) -> dict[str, list[Path]]:
    """`_sidecar_groups(wb)` 중 짝 워크스페이스 디렉터리가 이미 없어졌고(존재도
    안 하고, roster 에도 pid-alive 로 안 남아 있고) `max_age_sec` 보다 오래된
    그룹만 돌려준다. `_prune_orphaned_sidecars()`(14일 기본 트리거)와
    `sweep_orphans()`(이슈 #3118, 더 짧은 온디맨드 임계값)가 이 판정을
    공유한다 — 두 곳에 독립적으로 같은 안전 검사를 두면 한쪽만 고치고 다른
    쪽은 조용히 어긋난다는 `_workspace_clean_state()` 교훈을 그대로 따른다."""
    eligible: dict[str, list[Path]] = {}
    for name, files in _sidecar_groups(wb).items():
        workspace_dir = wb / name
        if workspace_dir.exists():
            continue
        if workspace_dir.resolve() in live:
            continue
        try:
            age_sec = now - max(f.stat().st_mtime for f in files)
        except OSError:
            continue
        if age_sec <= max_age_sec:
            continue
        eligible[name] = files
    return eligible


def _prune_orphaned_sidecars(wb: Path, max_age_days: float | None = None,
                              now: float | None = None) -> dict[str, int]:
    """`~/.tokenmaxxxer/work`(`wb`) 바로 아래 flat 하게 놓인, 짝 워크스페이스
    디렉터리가 이미 없어진 sidecar 파일 세트를 지운다. `auto_sweep()`과
    정책을 그대로 재사용한다 — 새 임계값/새 트리거 지점을 만들지 않는다
    (이슈 #2443 요구사항): 나이 임계값은 같은 `_clean_max_age_days()`
    (`MUSTER_CLEAN_MAX_AGE_DAYS`, 기본 14일), liveness 판정은 같은
    `_live_workspaces()`(roster 의 pid-alive 엔트리, `_workspace_clean_state()`
    가 쓰는 바로 그 함수) — 스폰타임 auto-sweep 백그라운드 스레드가 같은
    호출에서 이 함수도 함께 부른다(spawn.py `_run_auto_sweep`), 새 cron/
    one-off 훅이 아니다.

    세트 하나를 "protected"(=지우지 않음)로 보는 두 조건 중 하나만
    맞아도 지우지 않는다: (a) 짝이 되는 워크스페이스 디렉터리
    (`wb / name`)가 아직 있다 — 그러면 그 디렉터리의 own lifecycle
    (`_delete_workspace()`)이 알아서 같이 처리할 몫이다. (b) 디렉터리는
    없어졌어도 그 워크스페이스 경로로 등록된 살아있는(pid-alive) roster
    엔트리가 있다 — `_live_workspaces()`는 workspace 절대경로로 인덱싱하므로
    디렉터리 존재 여부와 무관하게 조회된다.

    세트의 "나이"는 그 세트에 속한 파일들 mtime 중 최댓값이다(파일 하나만
    보면, issue #2383 후속(2ca4b4de)이 worktree age-prune 에서 겪은 것과
    같은 오판 — 계속 append 중인 세션 로그가 있는데 다른 형제 파일 하나가
    오래됐다고 세트 전체를 지우는 실패 모드 — 를 그대로 재도입한다).

    `wb`: 워크스페이스 루트를 인자로 받는다(테스트가 실제
    `~/.tokenmaxxxer/work` 대신 scratch 디렉터리를 넘길 수 있게, 하드코딩
    하지 않는다). `max_age_days`/`now`: 테스트가 정책/시각을 주입한다."""
    max_age_days = _clean_max_age_days() if max_age_days is None else max_age_days
    now = time.time() if now is None else now
    max_age_sec = max_age_days * 86400
    live, unreadable = _sp._live_workspaces_union()
    for msg in unreadable:
        print(f"[sidecar-prune] 경고: 이웃 체크아웃 로스터를 읽지 못함 — {msg} — "
              f"확인 불가 워크스페이스의 sidecar 는 이번 정리에서 남긴다",
              file=sys.stderr)

    total_groups = len(_sidecar_groups(wb))
    eligible = _orphaned_sidecar_groups(wb, live, now, max_age_sec)

    removed = failed = 0
    for name, files in eligible.items():
        for f in files:
            try:
                f.unlink()
            except OSError as ex:
                print(f"[sidecar-prune] 실패 (삭제 중 예외): {f.name}  [{ex}]",
                      file=sys.stderr)
                failed += 1
            else:
                removed += 1
    kept = total_groups - len(eligible)
    return {"removed": removed, "kept": kept, "failed": failed}


# Issue #3118: `spawn.py sweep-orphans [--dry-run]` — a standalone,
# operator-invoked reclaim pass for the three orphan classes measured after
# one day of heavy parallel-session use: 193 `/tmp` worktree directories
# (190 of which no `git worktree prune`/`auto_sweep()` can see, because the
# checkout that registered them via `git worktree add` is itself already
# gone), 236 session logs, and 68 `_workspace_base()` workspaces whose
# branch never merged. `auto_sweep()` and `_prune_orphaned_sidecars()`
# already cover parts of this, but only at spawn time and only past a
# generous 14-day age floor — this command runs on demand, with a tighter
# floor, and lists every candidate with its reason before touching
# anything.
#
# Every category below is gated on process-state liveness FIRST — the same
# `_live_workspaces_union()` pid-alive roster lookup `_workspace_clean_state()`
# uses — never on age alone: a session in this repo routinely runs 40+
# minutes and must survive whatever the age floor is. `min_age_seconds` is
# only ever an extra guard against a create-time race (pointer file/roster
# entry written, but not yet flushed when a sweep happens to run
# concurrently), not a standalone trigger.

_ORPHAN_MIN_AGE_SECONDS_DEFAULT = 3600.0


def _orphan_min_age_seconds() -> float:
    """`MUSTER_ORPHAN_MIN_AGE_SECONDS` — default 3600 (1 hour)."""
    return float(os.environ.get("MUSTER_ORPHAN_MIN_AGE_SECONDS",
                                 str(_ORPHAN_MIN_AGE_SECONDS_DEFAULT)))


def _sweep_temp_roots() -> list[Path]:
    """Where `sweep_orphans()` looks for ad-hoc verification-session
    worktrees. Two roots, deduplicated in order: `tempfile.gettempdir()`
    (the platform's real scratch root — on macOS a per-user directory
    under `$TMPDIR`, not `/tmp`) and the literal `/tmp` (this project's
    own verification briefs write `/tmp/...` paths directly, so both may
    hold orphans on a Mac). Pure `tempfile`/`Path` — no `stat`/`find`/`du`
    subprocess, per the portability requirement: GNU and BSD userland
    differ on those, `os.stat`/`pathlib` do not."""
    roots: list[Path] = []
    seen: set[str] = set()
    for candidate in (Path(tempfile.gettempdir()), Path("/tmp")):
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        roots.append(candidate)
    return roots


def _worktree_admin_dir(git_file: Path) -> Path | None:
    """`git worktree add` leaves a `.git` FILE at the worktree root
    containing `gitdir: <repo>/.git/worktrees/<name>` — read it back.
    Returns `None` for anything else (a plain `.git` DIRECTORY from a full
    clone, a missing/unreadable `.git`, or a non-pointer file), so callers
    treat those as out of scope rather than guessing at ownership."""
    try:
        if not git_file.is_file():
            return None
        text = git_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    line = text.strip()
    if not line.startswith("gitdir:"):
        return None
    target = line[len("gitdir:"):].strip()
    if not target:
        return None
    path = Path(target)
    return path if path.is_absolute() else (git_file.parent / path)


def _scan_orphan_worktrees(temp_roots: list[Path], live: dict[Path, dict],
                            unreadable: list[str], now: float,
                            min_age_seconds: float) -> list[dict]:
    """Category 1 (issue #3118): ad-hoc `git worktree add /tmp/...`
    checkouts a verification session's own brief creates directly in bash
    — never registered via `session_temp_root()`, and invisible to `git
    worktree list` run from any repo that is still alive, because the
    repo that registered them (the verification session's own throwaway
    workspace under `_workspace_base()`) is usually the one that gets
    swept away first, orphaning the child `/tmp` checkout with no admin
    record left anywhere to prune it from.

    Liveness never comes from the `/tmp` directory's own age — it comes
    from the OWNING checkout: read the `.git` pointer file back to its
    admin dir (`<owner-repo>/.git/worktrees/<name>`), and ask whether
    `owner-repo` is a currently pid-alive session workspace via the same
    `live`/`unreadable` `_live_workspaces_union()` produces elsewhere. A
    plain `.git` directory (a full clone, not a worktree) has no such
    pointer to resolve an owner from, so it is left out of scope rather
    than guessed at."""
    results: list[dict] = []
    for root in temp_roots:
        if not root.is_dir():
            continue
        try:
            entries = sorted(root.iterdir())
        except OSError as ex:
            print(f"[sweep-orphans] 경고: {root} 못 읽음 ({ex}) — 이 temp root 는 "
                  f"이번 스윕에서 건너뜀", file=sys.stderr)
            continue
        for entry in entries:
            if not entry.is_dir():
                continue
            admin_dir = _worktree_admin_dir(entry / ".git")
            if admin_dir is None:
                continue
            try:
                mtime = max((p.stat().st_mtime for p in entry.rglob("*")),
                            default=entry.stat().st_mtime)
            except OSError:
                continue
            age_sec = now - mtime
            if age_sec < min_age_seconds:
                continue
            if unreadable:
                continue
            if admin_dir.exists():
                owner_repo = admin_dir.parent.parent.parent
                if owner_repo.resolve() in live:
                    continue
                reason = "no live pid (owning session ended)"
            else:
                reason = "owning checkout gone (worktree admin dir missing)"
            results.append({"path": entry, "reason": reason,
                             "age_hours": age_sec / 3600})
    return results


def _scan_orphan_workspaces(wb: Path, live: dict[Path, dict],
                             unreadable: list[str], now: float,
                             min_age_seconds: float) -> list[dict]:
    """Category 3 (issue #3118): workspaces whose session ended without
    the branch ever merging — killed sessions, refused spawns, held PRs.
    `auto_sweep()`'s age trigger already reclaims these too, but only past
    `_clean_max_age_days()` (14 days by default, deliberately generous so
    a slow-to-merge branch is never raced). This adds a second, tighter,
    on-demand signal: a workspace whose branch has no OPEN or MERGED pull
    request at all (closed unmerged, or never opened) has nothing left
    worth protecting, so it is eligible sooner — but only once
    `_workspace_clean_state()` has already cleared it (not live, not
    dirty, not unknown) and it has cleared `min_age_seconds`. A `gh`
    call that fails outright leaves the workspace out of this pass
    (unknown, not "no PR") rather than risk treating an API hiccup as
    grounds for removal."""
    results: list[dict] = []
    if not wb.is_dir():
        return results
    for w in sorted(wb.glob("*")):
        if not (w / ".git").is_dir():
            continue
        reason, _detail = _sp._workspace_clean_state(w, live, unreadable)
        if reason is not None:
            continue
        try:
            age_sec = now - w.stat().st_mtime
        except OSError:
            continue
        if age_sec < min_age_seconds:
            continue
        branch = subprocess.run(
            ["git", "-C", str(w), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True).stdout.strip()
        if not branch:
            continue
        if not _sp._pr_list_call_ok(w, branch):
            continue
        if _sp._pr_open_or_merged_for_branch(w, branch) is not None:
            continue
        results.append({"path": w,
                         "reason": f"no live pid, no open PR (branch {branch})",
                         "age_hours": age_sec / 3600})
    return results


def _force_rmtree(path: Path) -> None:
    """Same permission-retry `shutil.rmtree()` `_delete_workspace()` uses
    (issue #229: a read-only file/dir inside the tree, e.g. a Go module
    cache, would otherwise raise `PermissionError`) — reused verbatim here
    so an orphaned `/tmp` worktree with the same shape doesn't need a
    second bug report to get the same fix."""
    def _chmod_retry(func, p, exc_info):
        os.chmod(p, stat.S_IWRITE)
        parent = os.path.dirname(p)
        if parent:
            os.chmod(parent, stat.S_IWRITE | stat.S_IEXEC | stat.S_IREAD)
        func(p)
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_chmod_retry)
    else:
        shutil.rmtree(path, onerror=_chmod_retry)


def sweep_orphans(wb: Path, temp_roots: list[Path] | None = None,
                   now: float | None = None,
                   min_age_seconds: float | None = None,
                   dry_run: bool = False) -> dict:
    """`spawn.py sweep-orphans [--dry-run]` (issue #3118). Scans all three
    orphan categories and, unless `dry_run`, removes exactly the ones it
    lists. See the module comment above `_ORPHAN_MIN_AGE_SECONDS_DEFAULT`
    for the full picture; every category here defers its liveness
    judgement to `_live_workspaces_union()` before it ever looks at age."""
    now = now if now is not None else time.time()
    min_age_seconds = (_sp._orphan_min_age_seconds() if min_age_seconds is None
                        else min_age_seconds)
    temp_roots = _sp._sweep_temp_roots() if temp_roots is None else temp_roots
    live, unreadable = _sp._live_workspaces_union()

    tmp_worktrees = _scan_orphan_worktrees(temp_roots, live, unreadable, now,
                                            min_age_seconds)
    workspaces = _scan_orphan_workspaces(wb, live, unreadable, now,
                                          min_age_seconds)
    sidecar_groups = _orphaned_sidecar_groups(wb, live, now, min_age_seconds)
    sidecars = [
        {"name": name, "files": files,
         "reason": "orphaned sidecar (paired workspace gone)",
         "age_hours": (now - max(f.stat().st_mtime for f in files)) / 3600}
        for name, files in sidecar_groups.items()
    ]

    report = {
        "tmp_worktrees": tmp_worktrees,
        "workspaces": workspaces,
        "sidecars": sidecars,
        "unreadable": unreadable,
        "dry_run": dry_run,
    }
    if dry_run:
        return report

    for item in tmp_worktrees:
        try:
            _sp._force_rmtree(item["path"])
            item["removed"] = True
        except OSError as ex:
            item["removed"] = False
            item["error"] = str(ex)

    log_outcomes = _sp._ledger_log_outcomes()
    archive_dir = wb / ".archived-logs"
    for item in workspaces:
        try:
            _sp._delete_workspace(item["path"], wb, log_outcomes, archive_dir)
            item["removed"] = True
        except Exception as ex:
            item["removed"] = False
            item["error"] = str(ex)

    for item in sidecars:
        failed_files = []
        for f in item["files"]:
            try:
                f.unlink()
            except OSError:
                failed_files.append(f)
        item["removed"] = not failed_files

    return report


def sweep_orphans_cli(wb: Path, dry_run: bool) -> int:
    """`spawn.py sweep-orphans [--dry-run]` entry point — prints every
    candidate with its reason before removing anything, and says so
    explicitly when there is nothing to remove (the symmetric negative
    the issue's probe checks for).

    A real (non-dry-run) removal can fail per item (`sweep_orphans()`
    records `item["removed"]`/`item["error"]` rather than raising, so one
    bad `rmtree`/`unlink` never aborts the rest of the sweep) -- this must
    say so per line and in the exit code, or a failed deletion prints the
    exact same line as a real one and a caller checking only the return
    code sees success either way."""
    report = _sp.sweep_orphans(wb, dry_run=dry_run)
    prefix = "[dry-run] " if dry_run else ""
    total = failed = 0

    def _outcome_suffix(item: dict) -> str:
        nonlocal failed
        if dry_run or item.get("removed", True):
            return ""
        failed += 1
        return f"  ** 삭제 실패: {item.get('error', '알 수 없는 오류')} **"

    for item in report["tmp_worktrees"]:
        total += 1
        print(f"{prefix}tmp-worktree: {item['path']}  "
              f"[{item['reason']}; age {item['age_hours']:.1f}h]"
              f"{_outcome_suffix(item)}")
    for item in report["workspaces"]:
        total += 1
        print(f"{prefix}workspace: {item['path']}  "
              f"[{item['reason']}; age {item['age_hours']:.1f}h]"
              f"{_outcome_suffix(item)}")
    for item in report["sidecars"]:
        total += 1
        print(f"{prefix}session-log: {item['name']} "
              f"({len(item['files'])} files)  "
              f"[{item['reason']}; age {item['age_hours']:.1f}h]"
              f"{_outcome_suffix(item)}")
    for msg in report["unreadable"]:
        print(f"[sweep-orphans] 경고: 이웃 체크아웃 로스터를 읽지 못함 — {msg} — "
              f"확인 불가 항목은 이번 스윕에서 남긴다", file=sys.stderr)
    if total == 0:
        print(f"{prefix}지울 후보 없음 — 모두 안전(라이브거나, 나이/PR 기준 미달)")
    else:
        verb = "지울 후보" if dry_run else "지움"
        if dry_run:
            suffix = ""
        elif failed:
            suffix = f" (성공 {total - failed}, 실패 {failed})"
        else:
            suffix = " (실제로 지워짐)"
        print(f"[sweep-orphans] {verb} {total}건{suffix}")
    return 1 if failed else 0
