"""Roster / claim / lease machinery, extracted from spawn.py (issue #2105,
extraction 2/N).

Pure move — no behavior change. spawn.py imports this module and re-exports
every moved name, so external callers and tests keep addressing them as
`spawn.<name>`.

Patching-compat mechanism (copied from relay.py, extraction 1/N): the
heavily-patching test suite replaces these functions and their helpers via
`mock.patch.object(spawn, "<name>")`. To keep those patches visible to the
moved code, every cross-function reference here goes through `_sp` — the
spawn module object, injected by spawn.py right after it imports this module
(guarded so only the canonical spawn/__main__ module binds it). Shared
low-level utilities and constants that still live in spawn.py (`ROSTER`,
`ORCHESTRATOR_SESSION_ID_ENV`, `BOARD`, `ROOT`, `DEADMAN_MARKER`,
`DEADMAN_INTERVAL_SEC`, `DEADMAN_STALE_INTERVALS`, `LEASE_TTL_MIN`,
`LEASE_FLAT_RENEWALS_K`, `DECLARED_WAIT_FILENAME`, `ledger_write`,
`ledger_check_and_stamp`, `_event_count`, `_events_path`, `_git_head`,
`_prior_event_details`) are reached the same way — each is a seam for a
later extraction.
"""
from __future__ import annotations
import contextlib
import fcntl
import json
import os
import re
import tempfile
import time
from pathlib import Path

# The spawn module object; set by spawn.py on import. All cross-module lookups
# resolve through it at call time so monkeypatches on spawn attributes are seen.
_sp = None


@contextlib.contextmanager
def _roster_locked():
    """runs/active.json 의 load-mutate-save 구간을 프로세스 간에 직렬화한다."""
    lock_path = _sp.ROSTER.with_name(_sp.ROSTER.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def _roster_load() -> dict:
    try:
        return json.loads(_sp.ROSTER.read_text())
    except (OSError, ValueError):
        return {}


def _roster_save(d: dict) -> None:
    _sp.ROSTER.parent.mkdir(parents=True, exist_ok=True)
    _sp.ROSTER.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def _roster_own(d: dict, all_scope: bool) -> dict:
    """이슈 #1013: 로스터 딕셔너리를 호출자 자신의 세션으로 좁힌다.
    `all_scope=True` 면 그대로 돌려준다(`--all`). 그 외에는
    `ORCHESTRATOR_SESSION_ID_ENV` 로 얻은 자기 세션 id 와 엔트리의
    `session_id` 가 같은 것만 남긴다 — 둘 다 `None` 이면(오늘의
    단일-세션/미설정 상태) 같다고 본다(empty-state parity). 다른
    세션이 소유한(둘 다 `None` 이 아니고 다른) 엔트리는 걸러지지만,
    소유자를 특정할 수 없는 고아 엔트리(`session_id` 가 `None` 인데
    자기 세션 id 는 있는 쪽)는 계속 관측 대상에 남긴다 — 관측-손실
    금지 불변식(observation-loss invariant)."""
    if all_scope:
        return d
    own = os.environ.get(_sp.ORCHESTRATOR_SESSION_ID_ENV) or None
    out = {}
    for key, e in d.items():
        sid = e.get("session_id")
        if sid == own or sid is None:
            out[key] = e
    return out


def _watcher_looks_real(pid: int, issue: int | None,
                         role: str | None = None) -> bool:
    """이슈 #488 before-landing hunt 발견: `_alive()` 만으로는 워처가 죽은
    뒤 OS 가 같은 pid 를 다른 프로세스에 재할당한 경우를 못 잡는다 — 살아는
    있지만 그 워처가 아니다. `issue` 를 알면(로스터 엔트리가 준다)
    `/proc/<pid>/cmdline` 이 실제로 이 이슈의 `watch` 호출인지까지 최선
    노력으로 확인한다. `/proc` 없는 플랫폼이나 `issue` 를 모르는 호출(adhoc
    스폰)에서는 `_alive()` 로 저하한다 — 표시적 신원 검사가 리눅스 전용
    기능이라 그 이상은 판단 불가.

    이슈 #559 after-proposal hunt 발견: `issue` 만 보면 같은 이슈의 *다른*
    역할이 무장한 살아있는 워처를 이 역할의 워처로 오인한다 — `role` 을
    넘기면 cmdline 에 그 문자열도 있어야 한다."""
    if not _sp._alive(pid):
        return False
    if issue is None:
        return True
    cmdline_path = Path(f"/proc/{pid}/cmdline")
    if not cmdline_path.exists():
        return True
    try:
        parts = cmdline_path.read_bytes().decode("utf-8", "replace").split("\x00")
    except OSError:
        return True
    if "watch" not in parts or str(issue) not in parts:
        return False
    if role is not None and role not in parts:
        return False
    return True


def _alive(pid: int) -> bool:
    # 이슈 #1462: `os.kill(0, 0)` 은 pid 0 이 아니라 호출자 자신의 프로세스
    # 그룹에 신호를 보내 항상 성공한다 — roster 엔트리의 `pid` 가 없거나
    # 0(세션-종료~재스폰 갭)이면 이 함수가 거짓으로 "살아있음"을 돌려줘
    # `ps` 가 `RUNNING pid 0` 을 그린다. 음수/0 pid 는 애초에 살아있는
    # 프로세스를 가리킬 수 없으니 커널 호출 전에 걸러낸다.
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def roster_register(key: str, entry: dict) -> None:
    with _sp._roster_locked():
        d = _sp._roster_load()
        d[key] = entry
        _sp._roster_save(d)


def roster_remove(key: str) -> None:
    with _sp._roster_locked():
        d = _sp._roster_load()
        if d.pop(key, None) is not None:
            _sp._roster_save(d)


def _declared_wait(work: str | None) -> dict | None:
    """Read the workspace's declared wait, if any (issue #2101 mechanism 5).
    Returns the parsed dict only when it names an awaited object; anything
    unreadable or shapeless is treated as "no declared wait" (never an
    error — this is watch-class, advisory-only machinery)."""
    if not work:
        return None
    try:
        d = json.loads((Path(work) / _sp.DECLARED_WAIT_FILENAME).read_text())
    except (OSError, ValueError):
        return None
    if isinstance(d, dict) and isinstance(d.get("object"), str) and d["object"]:
        return d
    return None


def _declared_wait_object_exists(root: Path, work: str | None, obj) -> bool:
    """Does the awaited object exist? Cheap local checks only — no gh/network
    calls (the sweep runs every tick). Unknown/unparseable object => False,
    which only ever produces an advisory, never a refusal."""
    if not isinstance(obj, str) or not obj:
        return False
    m = re.match(r"^issue:([0-9]+)$", obj)
    if m:
        if (Path(root) / _sp.BOARD / f"issue-{m.group(1)}").is_dir():
            return True
        # Issue #2129: during a checkpoint-mode approval pause the subject
        # tree exists only in the session's WORKSPACE (the proposal PR is
        # open but unmerged, so the target root has no docs/issue-<n>/
        # yet). The workspace copy is the same awaited object — accept it
        # so the #2101 flat-progress exemption covers the whole pause.
        # Advisory-only machinery: at worst this suppresses an advisory.
        return bool(work) and (
            Path(work) / _sp.BOARD / f"issue-{m.group(1)}").is_dir()
    p = Path(obj)
    if not p.is_absolute() and work:
        p = Path(work) / obj
    return p.exists()


def _declared_wait_valid(root: Path, work: str | None) -> bool:
    """A declared wait is valid when it exists and its awaited object exists.
    A valid wait EXEMPTS the session from the flat-progress classification
    (issue #2101 mechanism 5 — a blocked-on-purpose session is not hung)."""
    wait = _sp._declared_wait(work)
    return wait is not None and _sp._declared_wait_object_exists(
        root, work, wait.get("object"))


def _lease_progress_indicator(entry: dict) -> str:
    """Cheap monotonic progress indicator for lease renewal (issue #2101
    mechanism 2): transcript event count (events.jsonl line count — already
    what the watchdog reads) combined with the workspace HEAD SHA. Both are
    local reads; no gh/network calls."""
    work = entry.get("work")
    if not work:
        return ""
    return f"{_sp._event_count(_sp._events_path(work))}:{_sp._git_head(work) or ''}"


def lease_renew(key: str, entry: dict, root: Path = None,
                now: float | None = None) -> list[str]:
    """Issue #2101 mechanisms 1+2: renew the roster entry's lease on behalf
    of the live session (the watchdog tick is the entry's watcher — "the
    owning session or its watcher renews"). Mutates `entry` in place; the
    caller persists it (roster_register). The lease is an EXTENSION of the
    existing roster entry (fields lease_expires_at / lease_progress /
    lease_flat_renewals), not a new registry.

    Each renewal records the progress indicator. A lease renewed
    LEASE_FLAT_RENEWALS_K times with an unchanged indicator returns a
    "flat-progress" anomaly string (advisory-only, consumed by
    diagnose_health as STALLED-FLAT-PROGRESS) — unless the session has a
    valid declared wait (mechanism 5 exemption; the OpenHands
    false-positive lesson: a deliberately blocked session is not hung)."""
    now = time.time() if now is None else now
    root = _sp.ROOT if root is None else root
    indicator = _sp._lease_progress_indicator(entry)
    if indicator == entry.get("lease_progress"):
        entry["lease_flat_renewals"] = entry.get("lease_flat_renewals", 0) + 1
    else:
        entry["lease_progress"] = indicator
        entry["lease_flat_renewals"] = 0
    entry["lease_expires_at"] = now + _sp.LEASE_TTL_MIN * 60
    flat = entry["lease_flat_renewals"]
    if flat >= _sp.LEASE_FLAT_RENEWALS_K:
        if _sp._declared_wait_valid(root, entry.get("work")):
            return []
        return [f"flat-progress: lease renewed {flat}x with unchanged "
                f"progress indicator {indicator!r} (advisory)"]
    return []


def _lease_requeue(key: str, entry: dict, now: float) -> None:
    """Issue #2101 mechanism 1, requeue path. Deliberately DETECTOR-FREE:
    the caller's only admission condition is `now > lease_expires_at` — no
    log classification, no health diagnosis, no liveness heuristics execute
    here. State change (roster entry + spawn claim removed => the item is
    dispatchable again) + ledger event + advisory print. Nothing is killed,
    nothing is refused."""
    work = entry.get("work")
    _sp.roster_remove(key)
    if work:
        try:
            _sp._spawn_claim_path(work).unlink()
        except FileNotFoundError:
            pass
    _sp.ledger_write({"event": "lease_expired_requeued", "key": key,
                  "issue": entry.get("issue"), "role": entry.get("role"),
                  "lease_expires_at": entry.get("lease_expires_at"),
                  "ts": now})
    print(f"[lease] {key}: lease expired — claim released, item returned to "
          f"dispatchable (advisory, self-correcting; no session was killed)")


def _sweep_completion_in_flight(work: str | None) -> bool:
    """True when the workspace's events.jsonl already records a session-end:
    the dead claim is a completion being processed, not a lost item. Used
    only to SUPPRESS the claim_without_live_session advisory (never in the
    requeue path — that stays a pure timestamp comparison)."""
    if not work:
        return False
    try:
        return bool(_sp._prior_event_details(_sp._events_path(work), "session-end"))
    except (OSError, TypeError):  # unhashable detail: unknown => not in flight
        return False


def deadman_mark(now: float | None = None, marker: Path | None = None) -> None:
    """Issue #2101 mechanism 4: append/refresh the periodic coverage-OK
    marker. Called from every reconcile sweep (i.e. every watchdog tick)."""
    now = time.time() if now is None else now
    marker = _sp.DEADMAN_MARKER if marker is None else marker
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps({"ts": now}))
        os.utime(marker, (now, now))
    except OSError:
        pass  # watch-class machinery must never die on a marker write


def deadman_check(now: float | None = None, marker: Path | None = None) -> int:
    """Issue #2101 mechanism 4, the CHECK side: verify the last coverage-OK
    marker is fresher than DEADMAN_STALE_INTERVALS x DEADMAN_INTERVAL_SEC.
    Standalone and dependency-free on the watchdog process — callable from
    the UserPromptSubmit/Stop poll hooks via `spawn.py deadman-check`
    (that is the point: the watch layer's own death must be observable
    from OUTSIDE it). Returns the advisory count (0 fresh / 1 stale) —
    never raises, never blocks anything."""
    now = time.time() if now is None else now
    marker = _sp.DEADMAN_MARKER if marker is None else marker
    try:
        age = now - marker.stat().st_mtime
    except OSError:
        return 0  # never marked yet (fresh install / first tick): no baseline
    threshold = _sp.DEADMAN_INTERVAL_SEC * _sp.DEADMAN_STALE_INTERVALS
    if age <= threshold:
        return 0
    print(f"[deadman] WATCH LAYER ITSELF IS DEAD: last coverage-OK marker is "
          f"{int(age)}s old (> {int(threshold)}s = {_sp.DEADMAN_STALE_INTERVALS} x "
          f"{int(_sp.DEADMAN_INTERVAL_SEC)}s). The monitor/watchdog tick has not "
          f"run — restart the session Monitor or run `spawn.py watchdog`. "
          f"Advisory only: nothing is blocked or killed.")
    _sp.ledger_write({"event": "deadman_stale", "age_sec": age,
                  "threshold_sec": threshold, "ts": now})
    return 1


def lease_reconcile_sweep(root: Path = None, d_all: dict | None = None,
                          now: float | None = None) -> int:
    """Issue #2101 mechanism 3: level-triggered reconcile sweep, hooked into
    the existing watchdog tick (roster_watchdog). Compares desired vs
    actual state:

      - every claimed board item (roster entry) must have a live session or
        a valid (unexpired) lease; an EXPIRED lease on a dead entry is
        requeued via `_lease_requeue()` (mechanism 1 — the requeue admission
        is a pure timestamp comparison, no detector logic);
      - a dead entry with a still-valid or absent lease is surfaced as a
        `claim_without_live_session` advisory (dedup-gated);
      - every declared wait must reference an existing object
        (`declared_wait_missing_object` advisory otherwise).

    Also drives the dead-man's switch (mechanism 4): checks the previous
    coverage-OK marker at sweep start, then refreshes it. Requeued keys are
    popped from `d_all` in place so the same tick does not re-report them
    through the dead-entry path. Returns the advisory count; everything here
    is advisory-only per the watch-coverage policy — nothing is blocked,
    refused, or killed."""
    now = time.time() if now is None else now
    root = _sp.ROOT if root is None else root
    count = _sp.deadman_check(now=now)
    _sp.deadman_mark(now=now)
    if d_all is None:
        d_all = _sp._roster_load()
    requeued = []
    for key, e in sorted(d_all.items()):
        work = e.get("work")
        alive = _sp._alive(e.get("pid", 0))
        expires_at = e.get("lease_expires_at")
        if not alive:
            if expires_at is not None and now > expires_at:
                _sp._lease_requeue(key, e, now)
                requeued.append(key)
                count += 1
            elif _sp._sweep_completion_in_flight(work):
                # A recorded session-end means the claim is a completion in
                # flight, not a discrepancy — the existing dead-entry
                # poll-report path owns reporting it. Not an anomaly.
                pass
            elif _sp.ledger_check_and_stamp(f"reconcile-sweep-no-session:{key}"):
                _sp.ledger_write({"event": "claim_without_live_session",
                              "key": key, "issue": e.get("issue"),
                              "role": e.get("role"),
                              "lease_expires_at": expires_at, "ts": now})
                lease_desc = ("no lease recorded" if expires_at is None
                              else f"lease valid until {expires_at}")
                print(f"[reconcile-sweep] {key}: claimed item has no live "
                      f"session ({lease_desc}) — advisory only")
                count += 1
        wait = _sp._declared_wait(work)
        if wait is not None and not _sp._declared_wait_object_exists(
                root, work, wait.get("object")):
            if _sp.ledger_check_and_stamp(f"declared-wait-missing:{key}"):
                _sp.ledger_write({"event": "declared_wait_missing_object",
                              "key": key, "object": wait.get("object"),
                              "ts": now})
                print(f"[reconcile-sweep] {key}: declared wait references a "
                      f"missing object {wait.get('object')!r} — advisory only")
                count += 1
        if wait is not None and wait.get("reason") == "approve-token":
            _sp._surface_approval_wait(key, e, wait, now)
    for key in requeued:
        d_all.pop(key, None)
    return count


# Issue #2133: a fresh-wait line flips to [EXPIRING] when the remaining
# time drops under this fraction of the wait budget.
APPROVAL_WAIT_EXPIRING_FRACTION = 0.2
# Per-wait-instance ledger dedup TTL — must exceed any plausible
# CHECKPOINT_WAIT_MAX_SECONDS so one wait instance never re-emits its
# `approval_wait_surfaced` event when the default 15-minute reconcile
# TTL lapses mid-pause.
APPROVAL_WAIT_LEDGER_TTL_SEC = 7 * 24 * 3600


def _surface_approval_wait(key: str, entry: dict, wait: dict,
                           now: float) -> None:
    """Issue #2133: actively surface a HEALTHY checkpoint-mode approval
    pause (declared wait with reason `approve-token`, written by
    `await_approval_cmd`) on every watchdog tick. The negative cases
    (missing object, dead session) were already advisories; the healthy
    wait emitted nothing, so a missed approval silently degraded to the
    two-session path at CHECKPOINT_WAIT_MAX_SECONDS.

    Prints one first-class `[awaiting-approval]` line per tick (prefixed
    `[EXPIRING]` when remaining < APPROVAL_WAIT_EXPIRING_FRACTION of the
    budget) and writes ONE `approval_wait_surfaced` ledger event per wait
    instance (dedup-keyed on the wait file's start timestamp, not per
    tick). Remaining time comes from the wait file's `ts` +
    `budget_sec` fields; a wait file predating those fields surfaces as
    remaining=unknown rather than crashing. Advisory-only per the
    watch-coverage policy: nothing is blocked, refused, or killed —
    the surfacing IS the fix."""
    issue = wait.get("issue", entry.get("issue"))
    role = wait.get("role", entry.get("role"))
    subject = f"issue-{issue}/{role}"
    ts, budget = wait.get("ts"), wait.get("budget_sec")
    prefix, remaining_desc = "[awaiting-approval]", "remaining unknown"
    if isinstance(ts, (int, float)) and isinstance(budget, (int, float)) \
            and not isinstance(ts, bool) and not isinstance(budget, bool) \
            and budget > 0:
        remaining = max(0.0, ts + budget - now)
        remaining_desc = (f"{remaining / 60:.0f}m remaining "
                          f"of {budget / 60:.0f}m")
        if remaining < APPROVAL_WAIT_EXPIRING_FRACTION * budget:
            prefix = "[awaiting-approval][EXPIRING]"
    print(f"{prefix} {subject}: APPROVE {subject} needed, {remaining_desc}")
    if _sp.ledger_check_and_stamp(f"approval-wait-surfaced:{key}:{ts}",
                                  now=now,
                                  ttl=_sp.APPROVAL_WAIT_LEDGER_TTL_SEC):
        _sp.ledger_write({"event": "approval_wait_surfaced", "key": key,
                          "issue": issue, "role": role, "wait_ts": ts,
                          "budget_sec": budget, "ts": now})


def _spawn_claim_path(work: str) -> Path:
    return Path(str(work) + ".spawn-claim")


def _acquire_spawn_claim(work: str, issue: int, role: str) -> str | None:
    """(issue, role) 하나의 동시 스폰을 막는 O_CREAT|O_EXCL 클레임을 취득한다
    — 재스폰 경로의 `.respawn-claim-{ts}`(이슈 #132)와 같은 계열이지만,
    재시도-단위가 아니라 이 (issue,role) 자체가 생존해 있는 동안 유지되는
    클레임이라 pid 로 생존검사를 한다. 성공하면 None, 이미 살아있는 세션이
    쥐고 있으면 그 세션의 pid/시작시각을 담은 거부 사유 문자열을 리턴한다
    (이슈 #223 요구사항 3). 죽은 세션이 남긴 stale 클레임이면 정리하고 1회
    재시도한다(요구사항 2)."""
    claim_path = _sp._spawn_claim_path(work)
    payload = json.dumps({"pid": os.getpid(), "ts": int(time.time())}).encode()
    for _ in range(2):
        # O_CREAT|O_EXCL 로 만들고 나서 내용을 쓰면, 만든 직후·쓰기 전 사이에
        # 다른 스레드/프로세스가 FileExistsError 를 잡고 내용을 읽어 빈
        # 파일을 "손상"으로 오판해 stale 정리로 방금 만든 클레임을 지워버릴
        # 수 있다(TOCTOU, 로컬에서 실측: 스레드 두 개 재현 시 간헐적으로 둘
        # 다 통과). 임시 파일에 내용을 먼저 다 쓴 뒤 `os.link()`로 옮기면
        # link 자체가 원자적 존재-검사+생성이라 이 창이 없다.
        tmp_fd, tmp_name = tempfile.mkstemp(dir=str(claim_path.parent),
                                            prefix=claim_path.name + ".tmp")
        try:
            with os.fdopen(tmp_fd, "wb") as f:
                f.write(payload)
            try:
                os.link(tmp_name, str(claim_path))
                return None
            except FileExistsError:
                pass
        finally:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass
        try:
            existing = json.loads(claim_path.read_text())
        except (OSError, ValueError):
            existing = {}
        pid = existing.get("pid")
        if isinstance(pid, int) and _sp._alive(pid):
            return (f"issue-{issue}/{role}: 이미 세션(pid {pid}, 시작 ts "
                    f"{existing.get('ts')})이 이 (issue,role) 스폰 클레임을 "
                    f"쥐고 있다 — 거부")
        try:
            claim_path.unlink()
        except FileNotFoundError:
            pass
    return f"issue-{issue}/{role}: 스폰 클레임 취득 실패(재시도 소진)"


def _rewrite_spawn_claim_pid(work: str) -> None:
    """fork 직후 자식 분기에서 클레임의 pid 를 자기 자신(자식)으로 재기록한다.
    클레임을 fork 전 pid(곧 죽는 부모)로 남겨 두면, 부모가 죽는 순간 생존검사
    (`_alive`)가 stale 로 오판한다 — 실제로는 자식이 세션을 계속 몰고 있는데도
    (이슈 #223 착수 프롬프트가 지목한 함정, 로컬 독립 검증에서 실측).
    `Path.write_text()`(truncate 후 쓰기)는 다른 프로세스가 그 사이 빈 파일을
    읽어 손상으로 오판하는 창을 새로 연다 — `_acquire_spawn_claim`이 이미
    피한 바로 그 TOCTOU(hunt 발견). 임시 파일에 다 쓴 뒤 `os.replace()`로
    교체해 그 창을 없앤다."""
    claim_path = _sp._spawn_claim_path(work)
    try:
        existing = json.loads(claim_path.read_text())
    except (OSError, ValueError):
        return
    existing["pid"] = os.getpid()
    tmp_fd, tmp_name = tempfile.mkstemp(dir=str(claim_path.parent),
                                        prefix=claim_path.name + ".tmp")
    with os.fdopen(tmp_fd, "w") as f:
        json.dump(existing, f)
    os.replace(tmp_name, str(claim_path))


def _release_spawn_claim(work: str, pid: int) -> None:
    """스폰 클레임을 해제한다 — 취득 이후 다른 프로세스가 stale-정리로 같은
    경로를 재취득했을 수 있으므로, 지금 쥔 pid 가 여전히 우리 자신일 때만
    지운다."""
    claim_path = _sp._spawn_claim_path(work)
    try:
        existing = json.loads(claim_path.read_text())
    except (OSError, ValueError):
        return
    if existing.get("pid") == pid:
        try:
            claim_path.unlink()
        except FileNotFoundError:
            pass

