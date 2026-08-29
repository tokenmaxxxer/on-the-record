"""Ledger + gh plumbing, extracted from spawn.py (issue #2105, extraction 3/N).

Pure move — no behavior change. spawn.py imports this module and re-exports
every moved name, so external callers and tests keep addressing them as
`spawn.<name>`.

Patching-compat mechanism (copied from relay.py, extraction 1/N): every
cross-function reference here resolves at call time through `_sp` — the spawn
module object, injected by spawn.py right after it imports this module
(guarded so only the canonical spawn/__main__ module binds it), so
`mock.patch.object(spawn, "<name>")` patches stay visible to the moved code.
Names that still live in spawn.py and are reached through `_sp` (seams for
later extractions): `ROOT`, `RECONCILE_LEDGER`, `_timed`, and the
`_GH_TOKEN_CACHE` process-wide token cache — the cache variable itself stays
a spawn module global (tests reset it via `spawn._GH_TOKEN_CACHE = None`), so
`_resolve_gh_token` reads/writes it as `_sp._GH_TOKEN_CACHE` instead of a
local `global` statement (attribute writes on the module object are the same
operation a module-global assignment performs).

`NETWORK_TIMEOUT` and `RECONCILE_LEDGER_TTL_SEC` moved here with their
functions (they are default-argument values, which bind at import time —
before `_sp` is injected); spawn.py re-exports both by assignment.
"""
from __future__ import annotations
import contextlib
import fcntl
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# The spawn module object; set by spawn.py on import. All cross-module lookups
# resolve through it at call time so monkeypatches on spawn attributes are seen.
_sp = None

NETWORK_TIMEOUT = 60   # fetch/pull/push


def _run_net(args: list[str], label: str, timeout: float = NETWORK_TIMEOUT,
             **kwargs) -> subprocess.CompletedProcess:
    """`timeout=`을 강제하는 네트워크 subprocess 호출. `TimeoutExpired`가
    그냥 새 나가면 오케스트레이터가 무기한 걸린다(이슈 #285 P5) — 대신
    `_fetch_or_halt`(spawn.py:2577)와 같은 모양의 이름 있는 에러로
    fail-closed."""
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    try:
        return subprocess.run(args, timeout=timeout, **kwargs)
    except subprocess.TimeoutExpired:
        sys.exit(f"{label}: 시간초과({int(timeout)}s) — 네트워크를 확인하라")


_REPO_SLUG_CACHE: dict[str, str | None] = {}


def _repo_slug_cache_clear() -> None:
    """`_repo_slug` 캐시를 비운다 — 한 프로세스에서 여러 레포나 여러 인증
    상태를 순차로 다루는 테스트용."""
    _REPO_SLUG_CACHE.clear()


def _repo_slug(root: Path) -> str | None:
    """레포 슬러그(`owner/name`). 프로세스 수명 동안 root 별로 캐시한다
    (issue #682).

    슬러그는 체크아웃당 상수다. flows-schema.md §4 는 이 호출을 이미
    "1 call (cached)" 로 계약에 적어뒀는데 구현에 캐시가 없어,
    `closure_sweep` 경로에서 `_fetch_ref_file` 이 subject 마다 다시 불러
    182회 · 94초를 썼다. 이 캐시가 그 계약을 구현으로 옮긴다.

    실패(`None`)도 캐시한다 — `gh` 인증/레포 인식 실패는 이 프로세스
    실행 내내 같은 결과이므로 호출마다 느린 재시도를 반복할 이유가 없다."""
    key = str(root)
    if key not in _REPO_SLUG_CACHE:
        try:
            r = subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner",
                                "-q", ".nameWithOwner"], cwd=root, capture_output=True, text=True)
        except FileNotFoundError:
            # 이슈 #1283: `root` 가 이미 지워진 workspace 일 수 있다(reconcile
            # 이 clean 된 workspace 도 훑는다) — `cwd` 부재로 subprocess 가
            # 죽는 대신 슬러그 조회 실패와 같은 `None`으로 처리한다.
            r = None
        _REPO_SLUG_CACHE[key] = (
            r.stdout.strip() if r is not None and r.returncode == 0 and r.stdout.strip() else None)
    return _REPO_SLUG_CACHE[key]


def _repo_name(root: Path) -> str | None:
    """`_repo_slug`의 owner 뗀 짧은 이름 — ledger 엔트리 귀속용(issue #216)."""
    slug = _sp._repo_slug(root)
    return slug.split("/")[-1] if slug else None


def _etag_cache_path(root: Path, number: int) -> Path:
    """이슈 #1459: `number` 스레드의 ETag 조건부-재조회 캐시 위치.
    `.git/` 아래(레포별, 워크트리 공유)에 둔다 — 커밋되지 않고, 레포
    삭제/재클론 시 자연히 사라진다."""
    return root / ".git" / "gh-read-cache" / f"issue-{number}-comments.json"


def _approval_record_path(root: Path, number: int) -> Path:
    """이슈 #1818: `number` 이슈의 구조화 승인 레코드 위치 — 기존
    `_etag_cache_path`(comments 캐시)와 같은 `.git/gh-read-cache/`
    컨벤션의 형제 파일. 커밋되지 않고, write-through 캐시로만 쓰인다
    (`gates/ci.py._approved_skills_on_issue` 가 읽고/쓴다)."""
    return root / ".git" / "gh-read-cache" / f"issue-{number}-approvals.json"


def _issue_comments_uncached(root: Path, slug: str, number: int
                              ) -> tuple[list[dict] | None, int]:
    """무조건(non-conditional) 전체 재조회 — fail-open 폴백 경로.
    `per_page=100`(이슈 #1459 요구사항 1)로 페이지 수를 ~3.3배 줄인다.
    반환: (평탄화된 원본 코멘트 리스트 또는 실패시 None, 소모한 호출 수)."""
    r = subprocess.run(["gh", "api", f"repos/{slug}/issues/{number}/comments",
                        "-f", "per_page=100", "--paginate", "--slurp"],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return None, 1
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None, 1
    return [c for page in data for c in page], max(len(data), 1)


def _issue_comments_more_pages(root: Path, slug: str, number: int) -> list[dict] | None:
    """이슈 #1459: 1페이지 조건부 조회가 200 이고 더 있는 것으로 표시될 때
    2페이지부터 무조건(non-conditional) `--paginate --slurp`로 나머지를
    읽는다 — 1페이지는 이미 읽었으니 중복 없이 이어붙인다."""
    r = subprocess.run(["gh", "api", f"repos/{slug}/issues/{number}/comments",
                        "-f", "per_page=100", "-f", "page=2",
                        "--paginate", "--slurp"],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None
    return [c for page in data for c in page]


def _issue_comments(root: Path, number: int) -> tuple[list[dict], bool]:
    """`number` 앞으로 달린 코멘트. GitHub 는 이슈든 PR 이든 같은
    `/issues/<n>/comments` 로 대화 코멘트를 낸다 — PR 리뷰 코멘트가 아니라
    일반 코멘트가 필요하므로 이 엔드포인트로 충분하다.

    이슈 #1459: 첫 페이지(`per_page=100`)를 캐시된 ETag 와 함께
    `If-None-Match` 조건부로 조회한다. GitHub 컬렉션 엔드포인트의 ETag는
    그 쿼리가 반환할 전체 결과 집합을 반영하므로(스레드 어디에 코멘트가
    추가되든 1페이지 ETag가 바뀐다), 1페이지 304 는 "스레드 전체가
    안 변했다"는 신호로 쓸 수 있다 — 그러면 캐시된 전체 본문을 그대로
    돌려주고, 이 재조회는 rate-limit 소모 호출로 세지 않는다(304 는
    카운트되지 않는다는 GitHub 정의 그대로). 200 이면 그 페이지부터
    나머지 페이지를 마저 무조건 읽어 캐시를 갱신한다. 캐시 파일이
    없거나/손상됐거나/쓰기가 실패하면 무조건 전체 재조회로 폴백한다
    (fail-open — 캐시 없이도 항상 정답을 돌려준다는 게 우선이다).

    `(comments, ok)` 를 돌려준다(issue #287 S6) — `ok=False` 는 `gh` 호출
    자체가 실패했다는 뜻이고, 그때 `comments` 는 빈 리스트지만 "코멘트가
    0개"로 읽으면 안 된다: 호출부가 "승인 코멘트가 없다"와 "코멘트를
    못 읽었다"를 구별할 수 있게 하는 게 이 튜플의 존재 이유다.
    """
    slug = _sp._repo_slug(root)
    if not slug:
        return [], False

    cache_path = _sp._etag_cache_path(root, number)
    etag = None
    cached_raw = None
    try:
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            etag = cached.get("etag")
            cached_raw = cached.get("raw")
            if not isinstance(etag, str) or not isinstance(cached_raw, list):
                etag, cached_raw = None, None
    except (OSError, ValueError, UnicodeDecodeError):
        etag, cached_raw = None, None

    # 1페이지를 항상 -i(헤더 포함)로 조회한다 — 캐시된 ETag 가 있으면
    # `If-None-Match` 를 실어 조건부로, 없으면(첫 조회거나 캐시가 깨졌을
    # 때) 조건 없이 그대로 보내 이번 응답의 ETag 를 다음 호출을 위해
    # 캐시에 심는다. 프로브 자체가 실패/파싱불가하면 무조건 전체
    # 재조회로 폴백한다(fail-open).
    cmd = ["gh", "api", f"repos/{slug}/issues/{number}/comments", "--method", "GET",
           "-f", "per_page=100", "-i"]
    if etag:
        cmd = cmd + ["-H", f"If-None-Match: {etag}"]
    r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    if r.returncode == 0:
        status, headers, body = _sp._split_gh_api_i_output(r.stdout)
        if status == 304 and cached_raw is not None:
            return [{"login": c.get("user", {}).get("login", ""),
                      "body": c.get("body", "")} for c in cached_raw], True
        if status == 200:
            try:
                page1 = json.loads(body)
            except ValueError:
                page1 = None
            if isinstance(page1, list):
                raw = page1
                if len(page1) == 100 and "rel=\"next\"" in headers.get("link", ""):
                    more = _sp._issue_comments_more_pages(root, slug, number)
                    if more is not None:
                        raw = page1 + more
                new_etag = headers.get("etag")
                _sp._write_etag_cache(cache_path, new_etag, raw)
                return [{"login": c.get("user", {}).get("login", ""),
                          "body": c.get("body", "")} for c in raw], True

    raw, _n = _sp._issue_comments_uncached(root, slug, number)
    if raw is None:
        return [], False
    return [{"login": c.get("user", {}).get("login", ""), "body": c.get("body", "")}
            for c in raw], True


def _split_gh_api_i_output(stdout: str) -> tuple[int | None, dict[str, str], str]:
    """`gh api -i` 출력(상태줄 + 헤더 + 빈줄 + 바디)을 파싱한다.
    이슈 #1459: ETag 조건부 재조회의 상태 코드/`Etag` 헤더를 읽는 데 쓴다."""
    if "\r\n\r\n" in stdout:
        head, body = stdout.split("\r\n\r\n", 1)
        sep = "\r\n"
    elif "\n\n" in stdout:
        head, body = stdout.split("\n\n", 1)
        sep = "\n"
    else:
        return None, {}, stdout
    lines = head.split(sep)
    status = None
    if lines:
        parts = lines[0].split()
        for p in parts:
            if p.isdigit():
                status = int(p)
                break
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    return status, headers, body


def _write_etag_cache(cache_path: Path, etag: str | None, raw_comments: list[dict]) -> None:
    """이슈 #1459: 새 ETag(있으면) 와 원본 코멘트 목록을 캐시에 쓴다.
    쓰기 실패는 다음 호출을 무조건 재조회로 되돌릴 뿐이므로 조용히
    무시한다(fail-open)."""
    if not etag:
        return
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps({"etag": etag, "raw": raw_comments}),
                               encoding="utf-8")
    except OSError:
        pass


# 이슈 #782 step 2: 이벤트 채널과 폴링 채널이 같은 완료/헬스 신호를 각자
# 관측해도 next-action 은 한 번만 나가야 한다(멱등 reconcile) — 프로포절의
# TTL 근거: WATCHDOG_SILENCE_MIN/WATCHDOG_NO_COMMIT_MIN 보다 짧게 잡아,
# 15분 안에 다시 폴링 틱이 돌아도 이미 찍힌 키는 조용히 넘어간다.
RECONCILE_LEDGER_TTL_SEC = 15 * 60


def _reconcile_ledger_lock_path() -> Path:
    return _sp.RECONCILE_LEDGER.with_name(_sp.RECONCILE_LEDGER.name + ".lock")


@contextlib.contextmanager
def _reconcile_ledger_locked():
    lock_path = _sp._reconcile_ledger_lock_path()
    lock_path.parent.mkdir(exist_ok=True)
    with open(lock_path, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def _reconcile_ledger_load() -> dict:
    try:
        return json.loads(_sp.RECONCILE_LEDGER.read_text())
    except (OSError, ValueError):
        return {}


def _reconcile_ledger_save(d: dict) -> None:
    _sp.RECONCILE_LEDGER.parent.mkdir(exist_ok=True)
    _sp.RECONCILE_LEDGER.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def ledger_check_and_stamp(dedup_key: str, now: float | None = None,
                            ttl: float = RECONCILE_LEDGER_TTL_SEC) -> bool:
    """`dedup_key` 가 지난 `ttl` 초 안에 이미 찍힌 적 없으면 True(=행동해도
    됨, 지금 찍는다), 있으면 False(=이미 처리됐다, 침묵) 를 돌려주며 항상
    락을 잡고 read-modify-write 한다 — 이벤트 채널과 폴링 채널이 같은
    completion/health 를 동시에 봐도 next-action 이 한 번만 나가게 하는
    유일한 관문(이슈 #782 Acceptance test 3)."""
    now = time.time() if now is None else now
    with _sp._reconcile_ledger_locked():
        d = _sp._reconcile_ledger_load()
        last = d.get(dedup_key)
        due = last is None or (now - last) >= ttl
        if due:
            d[dedup_key] = now
            _sp._reconcile_ledger_save(d)
        return due


def ledger_stamp(dedup_key: str, now: float | None = None) -> None:
    """조건 없이 찍기만 한다 — `_spawn_one()` 의 이벤트-발신 지점에서
    completion 을 이미 확정적으로 안 순간 쓴다. 이후 같은 키로 도착하는
    폴링 틱의 `ledger_check_and_stamp()` 는 TTL 안이면 False 를 받아
    조용히 넘어간다(Acceptance test 2: watch 가 먼저 잡은 완료를 폴링이
    다시 보고하지 않는다)."""
    with _sp._reconcile_ledger_locked():
        d = _sp._reconcile_ledger_load()
        d[dedup_key] = time.time() if now is None else now
        _sp._reconcile_ledger_save(d)


def ledger_write(entry: dict) -> Path:
    """runs/ledger.jsonl 에 한 줄. runs/ 는 gitignore 되어 있다 — 측정 데이터는
    소스가 아니다."""
    d = _sp.ROOT / "runs"
    d.mkdir(exist_ok=True)
    p = d / "ledger.jsonl"
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return p


def _resolve_gh_token() -> str:
    """`MUSTER_AGENT_GH_TOKEN` 이 있으면 그것, 없으면 `gh auth token` 을 한
    번만 불러 프로세스 전체에서 캐시한다(issue_workspace/checkout_issue_branch
    가 한 스폰에서 `_fetch_or_halt` 를 최대 2번까지 부르므로, 캐시 없이는
    `gh auth token` 을 그만큼 다시 shell-out 한다). 실패하면 빈 문자열 —
    호출부가 "주입 안 함"으로 처리한다.

    `spawn_cmd()` 가 세션의 `GH_TOKEN` env 를 채울 때 쓰던 것과 같은
    로직이다(중복 제거) — 두 소비자가 정확히 같은 우선순위를 공유해야,
    오케스트레이터 자신의 git 호출과 세션이 서로 다른 계정으로 인증하는
    일이 없다."""
    if _sp._GH_TOKEN_CACHE is not None:
        return _sp._GH_TOKEN_CACHE
    token = os.environ.get("MUSTER_AGENT_GH_TOKEN")
    if not token:
        with _sp._timed("gh_token"):
            try:
                t = subprocess.run(["gh", "auth", "token"], capture_output=True,
                                   text=True, timeout=15)
                token = t.stdout.strip() if t.returncode == 0 else ""
            except Exception:
                token = ""
    _sp._GH_TOKEN_CACHE = token
    return token


def _git_env() -> dict[str, str] | None:
    """오케스트레이터 자신이 origin 에 하는 git 호출(fetch/push)에 얹을 env.

    `issue_workspace()` 가 작업 클론에 심는 credential.helper
    (`!f() { ...; echo password=$GH_TOKEN; }; f`)는 그 helper 를 실행하는
    프로세스의 `$GH_TOKEN` 을 읽는다. 세션에는 `spawn_cmd()` 가 이
    값을 명시 주입하지만, `_fetch_or_halt()`/`ensure_pushed()` 는
    오케스트레이터 자신의 프로세스에서 돈다 — 아무도 이 프로세스의 env 에는
    넣어주지 않았다(실측: reasona 검증 중 `GH_TOKEN` 없이 `python3
    spawn.py` 를 그냥 돌리면 재사용 워크스페이스 fetch 가 인증 실패로
    막힌다. 이 개발 기계에서는 github.com 용 osxkeychain 항목이 우연히
    있어서 처음엔 안 보였다 — `security find-internet-password -s
    github.com` 으로 그 항목이 fetch 를 대신 통과시켰다는 것과, env 헬퍼
    하나만 남기면 `Authentication failed` 로 재현된다는 것 둘 다 확인했다).

    토큰을 못 구하면 `None` 을 돌려 `subprocess.run` 이 부모 env 를 그대로
    물려받게 한다 — 빈 문자열로 덮어써서 사용자의 다른 자격증명 경로
    (ssh-agent, osxkeychain)를 막지 않는다."""
    token = _sp._resolve_gh_token()
    if not token:
        return None
    return {**os.environ, "GH_TOKEN": token,
            "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "true"}
