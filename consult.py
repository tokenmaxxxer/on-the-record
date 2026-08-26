"""Consult / verb / judge / panel machinery, extracted from spawn.py
(issue #2105, extraction 6/N).

Pure move — no behavior change. spawn.py imports this module and re-exports
every moved name, so external callers and tests keep addressing them as
`spawn.<name>`.

Patching-compat mechanism (copied from relay.py/roster.py/plumbing.py/
watchdog.py/events.py, extractions 1-5): every cross-function reference here
resolves at call time through `_sp` — the spawn module object, injected by
spawn.py right after it imports this module (guarded so only the canonical
spawn/__main__ module binds it), so `mock.patch.object(spawn, "<name>")`
patches stay visible to the moved code. Names that still live in spawn.py
and are reached through `_sp` are exactly: `ROOT`,
`_CROSS_FAMILY_CONSULT_TOPN`, `_bm25_cross_family_scores`,
`_skill_repo_root`, `_skill_trigger_line`, `core_plugin_dirs`,
`ledger_write`, `resolve_role_source`, `resolved_role_model`,
`role_settings`, `session_result` — each a seam for a later extraction.
Cluster-internal cross-function calls also go through `_sp` (same as the
prior extractions), so patches on any moved name stay visible.

The #2104 evidence-check call-out inside `_append_consult_trace` /
`consult_cmd` moves verbatim — its behavior is identical.

Module-level constants whose values bind at import time moved here WITH
their users (`CONSULT_TIMEOUT`, `SKILL_JUDGE_TIMEOUT_DEFAULT`,
`PANEL_TIMEOUT`, `JUDGE_TIMEOUT`, `JUDGE_MAX_ROLES_PER_MERGE`,
`_VERB_REQUIRED_KEY`, `_VERB_INSTRUCTIONS`, `_VERB_JSON_SHAPE`,
`_JUDGE_EXCLUDED_CORE_PLUGINS`) — spawn.py re-exports them by assignment.
Run-time references still go through `_sp` so patches on spawn attributes
are seen.
"""
from __future__ import annotations
import json
import os
import re
import shlex
import contextlib
import tempfile
import concurrent.futures
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# The spawn module object; set by spawn.py on import. All cross-module lookups
# resolve through it at call time so monkeypatches on spawn attributes are seen.
_sp = None

CONSULT_TIMEOUT = 180  # consult: bounded headless run — no branch/PR to wait on
SKILL_JUDGE_TIMEOUT_DEFAULT = 90  # issue #2076: measured completion rate at 45s was <80% in
# consumer dogfood (issue #2071 defect 1) — raised to give the haiku judge more room before
# BM25 fail-open, still env-overridable via SKILL_JUDGE_TIMEOUT

# issue #2274: below this many genuine `skill_judge_perf` samples, the
# p90-derived cutoff below stays off (empty state — current fixed-default
# behavior unchanged); a fresh/low-volume ledger has too few points for a
# percentile to mean anything.
_SKILL_JUDGE_PERF_MIN_EVENTS = 50

# issue #2274 (warrant-hunt before-landing, stance 0 "gate is bypassable"):
# a nested `claude -p` classify call cannot plausibly finish in under a
# second — process spawn plus a haiku network round trip. `duration_ms`
# alone isn't a safe "this is a real call" marker: a mocked `subprocess.run`
# in any unit test (this file's own included) can echo back a fabricated
# `duration_ms` while `wall_s` truly is ~0, and 50+ of those landing in the
# shared ledger would collapse the p90 cutoff — and with it
# `_skill_judge_timeout()` — to ~0s, making every real call fail open.
# Requiring `wall_s` above this floor closes that regardless of what
# `duration_ms` claims.
_MIN_PLAUSIBLE_JUDGE_WALL_S = 1.0

# issue #2274 (operator-frozen constraint, 2026-08-25: "no added per-spawn
# overhead or steady-state load"): `runs/ledger.jsonl` is append-only and
# never rotated, so a full-file scan on every `_skill_judge_timeout()` call
# would grow with the installation's *total lifetime* event count, not with
# anything bounded — the exact steady-state-cost regression the constraint
# forbids. Reading only the last `_LEDGER_TAIL_READ_BYTES` bytes makes the
# read cost constant regardless of how large the ledger has grown; that
# window is generously sized to hold several times
# `_SKILL_JUDGE_PERF_MIN_EVENTS` recent lines even under heavy noise (each
# observed `skill_judge_perf` line is ~150-250 bytes).
_LEDGER_TAIL_READ_BYTES = 512 * 1024


def _skill_judge_perf_samples(ledger_path: Path | None = None) -> list[float]:
    """issue #2274: 실측 skill_judge 호출 지연(초) 목록 —
    `runs/ledger.jsonl` 의 마지막 `_LEDGER_TAIL_READ_BYTES` 바이트 안
    `skill_judge_perf` 이벤트 중 (1) `duration_ms` 가 있고 (2) `wall_s`
    가 `_MIN_PLAUSIBLE_JUDGE_WALL_S` 이상인 것만 쓴다. 전체 대신 꼬리만
    읽는 이유는 성능(위 상수 독스트링) — 필터 자체의 이유는 이 파일을
    공유하는 다른 세션들의 유닛테스트가 `subprocess.run` 을 몽키패치해
    남기는, 진짜 모델 호출이 아닌 잡음을 걸러내는 것이다: 그 잡음을
    그대로 퍼센타일에 넣으면 p90 이 0에 가깝게 무너져 사실상 모든 실제
    호출이 타임아웃되어 fail-open 해버린다. 두 조건 다 걸어야 안전하다:
    `duration_ms` 단독으로는 몽키패치가 그 값도 함께 꾸며낼 수 있어(가짜
    완료 응답에 `duration_ms` 필드를 얹는 것만으로 통과), `wall_s` 하한이
    최후 방어선이다."""
    path = ledger_path or (_sp.ROOT / "runs" / "ledger.jsonl")
    samples: list[float] = []
    if not path.exists():
        return samples
    with path.open("rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        truncated = size > _sp._LEDGER_TAIL_READ_BYTES
        f.seek(max(0, size - _sp._LEDGER_TAIL_READ_BYTES), os.SEEK_SET)
        chunk = f.read()
    lines = chunk.split(b"\n")
    if truncated:
        lines = lines[1:]  # 앞쪽 한 줄은 중간에서 잘렸을 수 있어 버린다
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if obj.get("event") != "skill_judge_perf":
            continue
        if obj.get("duration_ms") is None:
            continue
        wall = obj.get("wall_s")
        if wall is None or wall < _sp._MIN_PLAUSIBLE_JUDGE_WALL_S:
            continue
        samples.append(float(wall))
    return samples


def _percentile(sorted_data: list[float], p: float) -> float:
    """선형보간 퍼센타일(예: numpy 기본 'linear' 방식과 동일) — `sorted_data`
    는 이미 오름차순이어야 한다."""
    if not sorted_data:
        raise ValueError("empty data")
    k = (len(sorted_data) - 1) * p
    f = int(k)
    c = min(f + 1, len(sorted_data) - 1)
    if f == c:
        return sorted_data[f]
    return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)


def _skill_judge_p90_cutoff(ledger_path: Path | None = None) -> float | None:
    """issue #2274: 원장에 쌓인 실측 지연의 p90 — `_SKILL_JUDGE_PERF_MIN_EVENTS`
    개 미만이면 None(호출부가 고정 기본값으로 떨어진다)."""
    samples = sorted(_sp._skill_judge_perf_samples(ledger_path))
    if len(samples) < _sp._SKILL_JUDGE_PERF_MIN_EVENTS:
        return None
    return _sp._percentile(samples, 0.9)


def _skill_judge_timeout() -> float:
    """env-overridable 타임박스(issue #2061) — 매 호출마다 읽어 테스트가
    `os.environ`을 몽키패치한 뒤에도 값을 반영한다.

    issue #2274: env override 가 없으면 실측 원장의 p90 컷오프를 쓴다
    (`_skill_judge_p90_cutoff()`) — 표본이 `_SKILL_JUDGE_PERF_MIN_EVENTS`
    미만이면 그 함수가 None 을 돌려줘 기존 고정 기본값으로 그대로
    떨어진다(empty state, 오늘의 동작 그대로). 타임아웃 초과는 이미
    `_cross_family_skill_matches_with_consult()` 의 일반 `except Exception`
    이 BM25 top-k 로 fail-open 하므로(#2040) — 새 fail-open 경로가 아니라
    기존 error fail-open 을 느림에도 그대로 적용하는 것뿐이다."""
    raw = os.environ.get("SKILL_JUDGE_TIMEOUT")
    if raw is not None:
        try:
            return float(raw)
        except ValueError:
            pass
    cutoff = _sp._skill_judge_p90_cutoff()
    return cutoff if cutoff is not None else _sp.SKILL_JUDGE_TIMEOUT_DEFAULT

PANEL_TIMEOUT = 240    # panel: two judges + a rebuttal round, wider than a single consult
JUDGE_TIMEOUT = 120           # issue #1587: per-judge-call hard cap (prefilter/judge/validator each)
JUDGE_MAX_ROLES_PER_MERGE = 3  # issue #1587: cost/API-strain cap — counted from the trace log


def _parse_consult_verdict(text: str) -> dict | None:
    """모델 출력에서 자문 판단 JSON 을 찾는다. 마지막 줄이 아니거나 코드펜스에
    감싸여 있어도, 텍스트 안에서 가장 나중에 나온(뒤에서부터 훑어 처음 파싱
    되는) `{...}` 객체를 쓴다 — 모델이 답 앞에 설명을 붙여도 견딘다."""
    if not text:
        return None
    for i in reversed([j for j, c in enumerate(text) if c == "{"]):
        try:
            obj, _ = json.JSONDecoder().raw_decode(text, i)
        except ValueError:
            continue
        if isinstance(obj, dict) and "answer" in obj:
            return obj
    return None


def _evidence_stamp_summary(answer_text: str, root: str) -> str:
    """issue #2104: gates/evidence_check.py 의 얇은 배선 — 모든 로직은
    게이트 모듈에 있고, 여기는 import + 호출뿐이다 (merge-conflict 최소화)."""
    sys.path.insert(0, str(_sp.ROOT / "gates"))
    import evidence_check
    return evidence_check.stamp_summary(answer_text, Path(root))


def _consult_evidence_suffix(verdict: dict, cwd: str | None) -> str:
    """issue #2104: consult 답변의 evidence 포인터를 기계 검증해 트레이스
    라인에 붙일 요약을 만든다. env OTR_EVIDENCE_CHECK=0 로 끈다(기본 ON).
    검증기 자체가 죽어도 consult 는 멈추지 않는다 — fail-open, ledger 에
    이벤트만 남긴다."""
    if os.environ.get("OTR_EVIDENCE_CHECK", "1").strip().lower() in ("0", "false", "off"):
        return ""
    try:
        return " | " + _sp._evidence_stamp_summary(
            str(verdict.get("answer", "")), cwd or str(_sp.ROOT))
    except Exception as e:
        with contextlib.suppress(Exception):
            _sp.ledger_write({"event": "evidence_check_crash", "error": str(e)[:300],
                          "ts": datetime.now(timezone.utc).isoformat()})
        return " | evidence=error(fail-open)"


def _consult_root(cwd: str | None) -> Path:
    """자문(consult) 계열 기록 경로 전부가 공유하는 앵커. `-C`/cwd 로 대상
    레포가 주어지면 그 레포를, 없으면 플러그인 저장소(`ROOT`)를 앵커로
    쓴다 — 트레이스/사이드파일/패널 기록 경로와 커밋 루트
    (`_commit_consult_trace()`)가 서로 다른 앵커를 쓰면 `relative_to()` 가
    터진다(이슈 #1313 근본원인)."""
    return Path(cwd).resolve() if cwd else _sp.ROOT


def _persist_consult_raw_output(issue: int | None, ts: str, attempt: int, text: str,
                                cwd: str | None = None) -> Path:
    """파싱 실패 시 모델의 원본 출력 전체를 사이드 파일에 저장한다 —
    트레이스 줄에는 경로 + 짧은 발췌만 남기고(#1123 제안서 Constraints:
    "트레이스 파일 크기를 실패마다 부풀리면 안 된다"), 전체 텍스트는 여기
    보존해 재현이 아니라 실제 원인 분석이 가능하게 한다."""
    base = _sp._consult_root(cwd) / "docs" / (f"issue-{issue}" if issue is not None else "reports")
    if issue is not None:
        out_dir = base / "reports" / "consult-raw-failures"
    else:
        out_dir = base / "consult-raw-failures"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_ts = ts.replace(":", "").replace("+", "")
    path = out_dir / f"{safe_ts}-{attempt}.txt"
    path.write_text(text, encoding="utf-8")
    return path


_CONSULT_SESSION_SHARD_ID: str | None = None


def _consult_session_shard_id() -> str:
    """issue #2333: 이 프로세스(=하나의 자문 세션)를 식별하는 `<session-ts-pid>`
    조각 — 첫 호출에서 한 번 계산해 프로세스 수명 내내 캐시한다. 같은
    세션 안에서 여러 번 자문(consult/verb/skill_judge)을 불러도 전부 같은
    샤드 파일에 쌓이고, 서로 다른 프로세스(=동시에 도는 다른 세션)는
    타임스탬프나 pid 둘 중 하나만 같아도(같은 초에 뜬 서로 다른 세션,
    또는 재시작으로 재사용된 pid) 절대 같은 파일을 안 쓴다 — 결합이
    충돌을 만드는 유일한 경로였다(이슈 #2333 본문의 append-only +
    concurrent-writers + one-path 3요소)."""
    global _CONSULT_SESSION_SHARD_ID
    if _CONSULT_SESSION_SHARD_ID is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        _CONSULT_SESSION_SHARD_ID = f"{ts}-{os.getpid()}"
    return _CONSULT_SESSION_SHARD_ID


def _consult_trace_dir(issue: int | None, cwd: str | None = None) -> Path:
    """이슈가 있으면 그 이슈 트리 아래, 없으면 표준 6개 버킷 중
    `reports/` 아래 — `docs/` 는 표준 버킷과 `docs/issue-<n>/` 트리만
    허용한다(contract v3 s10, board-gate.sh 가 강제). 앵커는
    `_consult_root()` 로 대상 레포(`-C`/cwd)에 맞춘다.

    이슈 #2333: 파일 하나가 아니라 세션당 샤드 파일을 담는 디렉터리를
    돌려준다 — `consult-log.md`(단일 append-only 파일)를 여러 세션이
    동시에 자문하면 100% 예측 가능한 git merge 충돌을 만들었다(이슈
    본문 "6+ manual conflict resolutions in one session"). 경로 하나에
    쓰던 것을 세션마다 다른 경로에 쓰게 바꾸면 그 충돌 클래스 자체가
    구조적으로 사라진다 — 해소가 아니라 제거."""
    root = _sp._consult_root(cwd)
    if issue is not None:
        return root / "docs" / f"issue-{issue}" / "reports" / "consult-log"
    return root / "docs" / "reports" / "consult-log"


def _consult_trace_path(issue: int | None, cwd: str | None = None) -> Path:
    """이슈 #2333: 이 세션이 쓸 샤드 파일 — `_consult_trace_dir()` 아래
    `_consult_session_shard_id()`.md. 다른 세션은 절대 이 경로를 쓰지
    않는다(pid+타임스탬프가 같은 두 프로세스는 없다)."""
    return _sp._consult_trace_dir(issue, cwd) / f"{_sp._consult_session_shard_id()}.md"


def _consult_log_aggregate(issue: int | None, cwd: str | None = None) -> str:
    """이슈 #2333: 오늘까지의 단일-파일 뷰를 재구성하는 리더/애그리게이터
    — `_consult_trace_dir()` 아래 모든 세션 샤드를 파일명(=`<타임스탬프>-
    <pid>`, 타임스탬프가 고정 폭이라 사전순 정렬이 곧 시간순) 순으로 이어
    붙인다. 각 샤드 파일 자체가 `_append_consult_trace()`가 쓰던 것과
    바이트 단위로 같은 줄 형식이라, 결과는 예전 `consult-log.md` 를 그대로
    읽은 것과 동일한 텍스트다(사람이 보거나 게이트가 파싱하는 쪽 모두
    변경 없음). 디렉터리가 아직 없으면(자문이 한 번도 없었으면) 빈 문자열
    — 예전의 "파일 없음"과 같은 empty state."""
    d = _sp._consult_trace_dir(issue, cwd)
    if not d.is_dir():
        return ""
    return "".join(p.read_text(encoding="utf-8") for p in sorted(d.glob("*.md")))


def _append_consult_trace(path: Path, ts: str, role: str, issue: int | None,
                          question: str, outcome: str, verb: str = "consult") -> None:
    """자문 한 건마다 한 줄 — 성공/실패 가리지 않고 남긴다("no traceless
    consults", 운영자 결정, 이슈 #699). 함수 자체가 실패해도(디렉터리를
    못 만든다 등) 예외를 그대로 올려, 호출부의 finally 가 "트레이스 남김"을
    조용히 거짓으로 만들지 않게 한다.

    이슈 #1202 requirement 5: consult 의 형제 verb(ideate/draft/review) 도
    같은 트레이스 파일 하나를 공유한다 — 별도 파일로 갈라지면 drift 가
    난다(`consult_cmd()` 독스트링과 같은 이유). `verb=` 는 기본값
    "consult" 라 기존 호출부는 그대로 동작한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = (f"- {ts} | role={role} | verb={verb} "
            f"| issue={issue if issue is not None else 'none'} "
            f"| question={question[:200]!r} | outcome={outcome[:300]!r}\n")
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


def _commit_consult_trace(paths: list[Path], issue: int | None, role: str,
                          outcome: str, cwd: str | None) -> None:
    """자문 트레이스(및 이번 호출에서 쓴 원본 사이드 파일)를 커밋해
    체크아웃을 깨끗하게 유지한다(이슈 #1134, northpole req#2 — 로컬
    미커밋 상태만 있는 기록은 기록이 아니다). `approve-scope`
    선례(spawn.py:1367-1387)와 같은 add-then-commit 모양이지만, 되돌릴
    "이전 전문"이 없다(append 이지 overwrite 가 아니다) — 커밋 실패시
    파일 쓰기는 그대로 두고 경고만 남긴다."""
    root = _sp._consult_root(cwd)
    rels = [str(p.relative_to(root)) for p in paths]
    outcome_word = "error" if outcome.startswith("error") else "ok"
    message = (f"issue-{issue}: consult-trace ({outcome_word})" if issue is not None
               else f"consult-trace ({outcome_word})")
    try:
        subprocess.run(["git", "-C", str(root), "add", *rels],
                       check=True, capture_output=True, text=True)
        subprocess.run(["git", "-C", str(root), "commit", "-m", message],
                       check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"consult-trace 커밋 실패 — {', '.join(rels)} 가 커밋 안 된 채 남았다: "
              f"{e.stderr.strip() if e.stderr else e}", file=sys.stderr)


def _skill_judge_consult(task_text: str, role: str,
                         candidates: list[tuple[str, Path, str]],
                         issue: int | None, cwd: str | None,
                         model: str | None = None,
                         max_picks: int = 2
                         ) -> tuple[list[Path], dict]:
    """이슈 #2040: BM25 상위 후보를 자문(consult)에 넘겨, 트리거 문장의
    조건이 실제로 이번 과제에 맞는지(단어 겹침이 아니라)를 판단시킨다.
    반환은 (picked_paths, {"picked":[...], "rejected":[...], "reasons":{}})
    — 실패시(파싱 실패/타임아웃/비영시종료) RuntimeError 를 그대로 올려,
    호출자(`_cross_family_skill_matches_with_consult()`)가 BM25 top-2 로
    fail-open 하게 한다(제안서 Constraints).

    `_verb_cmd()` 를 재사용하지 않는 이유: 그 함수의 기본 트레이스 줄은
    `outcome = f"ok: {parsed[required_key]}"` 로 picked 값만 남기고
    rejected+reason 을 놓친다 — Acceptance 가 요구하는 "picked+rejected+
    reasons 를 자문 트레이스에" 를 만족하려면 이 함수가 트레이스 줄을
    직접 조립해야 한다. session-assembly(`_consult_cmd_and_env()`)와
    트레이스 파일(`_consult_trace_path()`, `verb="skill_judge"`)은
    그대로 공유한다(드리프트 방지, `_verb_cmd()` 독스트링과 같은 이유)."""
    trace_path = _sp._consult_trace_path(issue, cwd)
    ts = datetime.now(timezone.utc).isoformat()
    settings_path = None
    raw_paths: list[Path] = []
    outcome = "error: 알 수 없는 실패"
    # 이슈 #2213: 이 함수가 곧 "cross_family" 단계의 실측 비용이다
    # (`_spawn_one` 이 이 호출을 감싼 future 를 join 만 재는 이유는
    # `_cross_family_skill_matches_with_consult()` 독스트링 참고) —
    # per-spawn wall time / 모델 자체 duration_ms / cache_read_input_tokens
    # / 동시 스폰 수를 여기서 직접 재 runs/ledger.jsonl 에 남긴다
    # (Acceptance: 스폰 10건+ 계측). `result`/`call_wall_s` 는 실패
    # 경로(타임아웃/파싱실패/비영시종료)에서도 finally 가 안전하게 읽도록
    # 미리 초기화한다 — 실패해도 무계측 스폰을 만들지 않는다("no traceless
    # consults"과 같은 이유, `_append_consult_trace()` 독스트링).
    result: dict = {}
    call_wall_s: float | None = None
    concurrency = len(_sp._live_workspaces())
    by_name = {name: path for name, path, _source in candidates}
    # 이슈 #2055: 후보가 이제 네 소스에 걸쳐 있어, 질의 문구도 어느 tier
    # 에서 왔는지 라벨을 달아 skill_judge 가 소스를 보고도 판단할 수 있게
    # 한다(Acceptance: "source 라벨이 ... skill_judge 자문 질문 ... 까지").
    # 이슈 #2124 part 3 (judge prompt diet): 후보 줄은 이름 + 트리거 문장만
    # — source 라벨(#2055)은 완료율을 깎는 군더더기라 뺐다(측정 근거는
    # PR 본문의 before/after 바이트). 질문/지시문 전부 최소 영어.
    candidate_lines = "\n".join(
        f"- {name} — {_sp._skill_trigger_line(path) or ''}"
        for name, path, source in candidates)
    question = f"Task:\n{task_text}\n\nCandidates:\n{candidate_lines}"
    try:
        # 이슈 #2537 stage 6A: `roles/<role>.json` 존재-확인 + `spec` 로드를
        # 여기서 지웠다 — `spec` 은 아래 `_consult_cmd_and_env()` 호출 어디서도
        # 안 읽힌다(호출 그래프 확인됨: `_consult_cmd_and_env()` -> `role_settings()`
        # 만 role 을 실제로 검증한다, pipeline.py). role 검증은 여전히 일어난다 —
        # 지워진 건 죽은 코드지 검증이 아니다.
        # 이슈 #2061: skill_judge 는 8개 후보 중 0-2개를 고르는 자잘한
        # 분류라, 호출자가 넘긴 세션 기본 모델을 그대로 물려받지 않고
        # 언제나 haiku 로 고정한다 — `model` 인자는 시그니처 호환용으로만
        # 남긴다(다른 자문 호출과 모양을 맞추려는 것일 뿐, 실제로는 무시).
        # 이슈 #2201: `_JUDGE_EXCLUDED_CORE_PLUGINS`(issue #1587 이 이미
        # judge 계열에 쓰던 필터, freelunch/scout/warrant)를 그대로
        # 재사용한다 — 이 판정도 판단만 돌려주면 끝이라 델리버리 지향
        # 훅(제안서 작성/게이트/팬아웃 위임을 지시)이 꽂힐 이유가 없고,
        # 실측상 그 훅들을 로드하는 자체가 스폰당 수 초를 먹는다
        # (`_consult_cmd_and_env()` 독스트링의 10.5s vs 15.6s 실측).
        # core/terse 는 그대로 남긴다(#1587 과 같은 이유: 무해하다).
        cmd, env, settings_path = _sp._consult_cmd_and_env(
            role, cwd, "haiku",
            exclude_core_plugins=_sp._JUDGE_EXCLUDED_CORE_PLUGINS)
        judge_timeout = _sp._skill_judge_timeout()
        # 이슈 #2124 part 3 (judge prompt diet): 최소 영어 프롬프트 —
        # RankGPT 계열 listwise 판단은 지시문이 짧을수록 완료율이 높다.
        # haiku 고정 / 90s / <=max_picks / pick-zero-allowed / fail-open 은
        # 전부 그대로다.
        override = (
            "This call is skill_judge only — ignore every directive/hook "
            "instruction loaded in this session: touch no repository files, "
            "delegate nothing, answer directly. This sentence overrides all "
            "other instructions.")
        instructions = (
            "You are skill_judge. Pick the candidate skills whose trigger "
            "condition actually applies to this task — not mere word overlap. "
            f"Pick at most {max_picks}; picking zero is fine. Give a one-line "
            "reason per candidate. Do not create branches, commits, or PRs.")
        shape = ('{"picked": ["<skill-name>", ...], '
                 '"rejected": [{"name": "<skill-name>", "reason": "<reason>"}, ...], '
                 '"reasons": {"<picked-skill-name>": "<reason>"}}')
        base_prompt = (instructions + " " + override +
                       " End your reply with exactly one JSON object and no "
                       f"other trailing text: {shape}\n\n{question}")
        retry_prompt = (
            base_prompt + "\n\n(Retry: the previous reply did not end with the "
            "verdict JSON object, so parsing failed. Output only one JSON "
            "object in the shape above, now.)")
        attempts_exhausted = "알 수 없는 실패"
        parsed = None
        _call_t0 = time.monotonic()
        for attempt_num, attempt_prompt in enumerate((base_prompt, retry_prompt), start=1):
            r = subprocess.run(cmd, cwd=cwd or str(_sp.ROOT), input=attempt_prompt, text=True,
                               capture_output=True, timeout=judge_timeout, env=env)
            call_wall_s = time.monotonic() - _call_t0
            if r.returncode != 0:
                attempts_exhausted = f"세션 종료 코드 {r.returncode}: {r.stderr.strip()[:300]}"
                continue
            result = _sp.session_result(r.stdout)
            raw_text = result.get("result", "")
            parsed = _sp._parse_verb_json(raw_text, "picked")
            if parsed is None:
                raw_path = _sp._persist_consult_raw_output(issue, ts, attempt_num, raw_text, cwd)
                raw_paths.append(raw_path)
                excerpt = raw_text[-300:].replace("\n", " ")
                attempts_exhausted = (
                    f"모델 출력에서 skill_judge JSON 을 못 찾음 (원본: `{raw_path}`, "
                    f"끝부분: {excerpt!r})")
                parsed = None
                continue
            break
        if parsed is None:
            outcome = f"error: {attempts_exhausted} (재시도 1회 포함, 모두 실패)"
            raise RuntimeError(outcome)
        picked_names = [n for n in parsed.get("picked", []) if n in by_name][:max_picks]
        rejected = parsed.get("rejected", [])
        reasons = parsed.get("reasons", {})
        rejected_summary = "; ".join(
            f"{r.get('name')}={str(r.get('reason', ''))[:80]}" for r in rejected
            if isinstance(r, dict) and r.get("name"))
        picked_summary = "; ".join(
            f"{n}={str(reasons.get(n, ''))[:80]}" for n in picked_names)
        outcome = f"ok: picked=[{picked_summary}] rejected=[{rejected_summary}]"
        detail = {"picked": picked_names, "rejected": rejected, "reasons": reasons}
        return [by_name[n] for n in picked_names], detail
    except subprocess.TimeoutExpired:
        call_wall_s = time.monotonic() - _call_t0
        outcome = f"error: 시간초과({judge_timeout}s)"
        raise
    finally:
        if settings_path:
            with contextlib.suppress(OSError):
                os.unlink(settings_path)
        _sp._append_consult_trace(trace_path, ts, role, issue, question, outcome,
                              verb="skill_judge")
        commit_paths = [trace_path] + raw_paths
        _sp._commit_consult_trace(commit_paths, issue, role, outcome, cwd)
        usage = result.get("usage") or {}
        _sp.ledger_write({
            "event": "skill_judge_perf", "ts": int(time.time()), "role": role,
            "issue": issue, "wall_s": (round(call_wall_s, 3)
                                        if call_wall_s is not None else None),
            "duration_ms": result.get("duration_ms"),
            "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
            "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
            "concurrency": concurrency,
            "outcome_ok": outcome.startswith("ok:"),
        })


# 이슈 #2205: 과제 텍스트에서 매치된 declared-phrase 를 지운 나머지가 이
# 토큰 수 미만이면(=과제가 사실상 그 문구 자체뿐이면) fast-path 재검증을
# 건너뛰고 원래 설계대로 문구를 그대로 신뢰한다 — 5토큰짜리 synthetic
# "문구 두 개만 이어붙인" 과제와, 실제 이슈 재현(수십 토큰의 무관한
# 기술 내용)을 가르는 문턱. 값 10 은 두 극단(관측 5 vs 26/51) 사이의
# 여유 있는 중간값.
_FAST_PATH_CORROBORATION_MIN_TOKENS = 10


def _cross_family_skill_matches_with_consult(task_text: str, role: str,
                                             repo_root: Path | None,
                                             issue: int | None, cwd: str | None,
                                             k: int = 2,
                                             model: str | None = None,
                                             home: Path | None = None,
                                             target_repo_root: Path | None = None
                                             ) -> tuple[list[Path], str]:
    """이슈 #2040: BM25 상위 `_CROSS_FAMILY_CONSULT_TOPN` 개를 자문
    (skill_judge)에 넘겨 조건-매치 여부로 좁힌다. BM25 후보가 아예 없으면
    (score>0 인 것이 없으면) 자문을 부르지 않고 빈 목록을 바로 돌려준다
    — 자문 한 번(<= 스폰당 자문 1회, Acceptance)조차 아까운 no-candidate
    경로를 오늘처럼 조용히 통과시킨다. 자문이 에러(타임아웃/파싱 실패/
    세션 실패 전부 포함)를 내면 BM25 자체의 top-`k` 로 fail-open 한다
    (`_cross_family_skill_matches()`, 제안서 Constraints — "오늘의
    raw-overlap top-2" 가 아니라 BM25 가 새 기준 프리필터이므로).

    이슈 #2076: 반환이 이제 `(picked_dirs, outcome)` 튜플이다 — `outcome`
    은 "completed"(자문 성공) | "fail-open"(자문 에러/타임아웃) |
    "no-candidates"(BM25 후보 0개라 자문 자체를 안 부름) 중 하나로,
    호출부(`_spawn_one`)가 그대로 per-spawn 원장 필드에 남겨 완료율을
    측정할 수 있게 한다.

    이슈 #2124 part 2: exact-phrase fast-path 픽이 있으면 outcome 에
    "fast-path:<이름들>" 이 접두된다 — 상한을 fast-path 만으로 채우면
    그 접두가 outcome 전부이고 자문은 아예 안 불린다; 남는 슬롯이 있으면
    "fast-path:<이름들>+completed|fail-open" 형태다(원장 태깅)."""
    scored = _sp._bm25_cross_family_scores(task_text, role, repo_root, home, target_repo_root)
    if not scored:
        return [], "no-candidates"
    # 이슈 #2124 part 2 (exact-phrase fast path, OpenHands microagents 키워드
    # tier): description 에 따옴표로 선언된 트리거 문구가 과제 텍스트에
    # 그대로(대소문자 무시) 들어 있으면 그 스킬은 판단 없이 자동 픽 —
    # 판단 fail-open(#2071/#2076)이 확실-매치에는 무해해진다. fast-path
    # 픽도 기존 <=k 크로스-패밀리 상한 안에서 세고(판단 픽보다 우선),
    # 남는 슬롯만 판단에 넘긴다. 결정론: 과제 텍스트 안 첫 등장 위치,
    # 그다음 이름 오름차순.
    #
    # 이슈 #2166: 스캔 대상을 `scored` 전체가 아니라 판단에 넘기는 것과
    # 같은 BM25 상위 `_CROSS_FAMILY_CONSULT_TOPN` 개로 좁힌다 — declared
    # phrase 는 "이미 그럴듯한 후보를 확정 짓는 신호"로 설계됐지, BM25
    # 랭킹과 무관하게 문구 하나로 판단을 통째로 건너뛰는 무제한 우회로가
    # 아니다. 예: work-in-english 의 declared phrase 는 "이 버그 고쳐줘"/
    # "fix this bug and open a pr" 처럼 흔한 요청 예문이라 거의 모든 한국어
    # 과제 텍스트에 그대로 등장하는데, 고정 폭 없이 전체 `scored` 를 훑으면
    # 그 스킬의 BM25 순위가 무관한 과제에서 47위여도(재현: 이슈-525 과제
    # 텍스트) 판단 없이 자동 픽된다. topN 으로 좁히면 애초에 BM25로도
    # 상위 후보가 아닌 스킬은 fast-path 대상에서 빠져 정상적으로
    # 판단(consult) 단계로 넘어가거나(top-N 안이면) 아예 후보에서 배제된다
    # (top-N 밖이면). 결정론적 정렬(입력 순서/타이브레이크)은 그대로다.
    task_lower = task_text.lower()
    fast: list[tuple[int, str, Path]] = []
    for _score, name, d, _source in scored[:_sp._CROSS_FAMILY_CONSULT_TOPN]:
        for phrase in _sp._skill_declared_phrases(d):
            pos = task_lower.find(phrase)
            if pos < 0:
                continue
            # 이슈 #2205: BM25 문서 자체가 같은 따옴표 문구를 담고 있어
            # (`_skill_bm25_document`, 이슈 #2124 part 1), 과제 텍스트에
            # 그 문구가 그대로 들어 있으면 스킬 자신의 topN 순위가 그
            # 문구 하나만으로 부풀려질 수 있다 — "이미 topN 안이라 그럴듯
            # 하다"는 전제가 문구 자신에 의해 자기증명되어버려 독립
            # 신호가 아니게 된다(재현: work-in-english 의 예시 문구 "fix
            # this bug and open a pr" 는 무관한 DB 인덱싱 버그 과제에서도
            # 269개 중 1위로 올라간다). 과제가 사실상 그 문구 자체뿐이면
            # (다른 판단 근거가 없는 것 자체가 정상 — synthetic
            # 테스트/실제 "이 문구 그대로만 요청" 케이스 둘 다) 문구를
            # 신뢰하고 그대로 픽한다: 문구를 지운 나머지 텍스트의
            # 불용어-제외 토큰 수가 `_FAST_PATH_CORROBORATION_MIN_TOKENS`
            # 미만이면 재검증 없이 통과. 그 문턱을 넘는(=이 스킬과 무관한
            # 실질 내용이 따로 있는) 과제에서만 문구를 지우고 다시
            # 스코어링해 이 스킬이 그래도 topN 안에 남는지 확인한다 —
            # 남으면 문구 외의 내용도 독립적으로 관련 있다는 뜻이라
            # fast-path 를 허용하고, 문구 제거만으로 topN 밖으로 빠지면
            # 문구 자체가 유일한 근거였다는 뜻이라 이 문구는 건너뛴다
            # (판단 단계로 넘기지 않고 다음 후보로 넘어간다 — 이미 topN
            # 밖일 리스크가 있는 스킬을 판단에 넘기는 것도 원래 설계
            # 의도가 아니다).
            stripped_task = re.sub(re.escape(phrase), " ", task_text,
                                    flags=re.I)
            if len(_sp._tokenize(stripped_task)) >= _FAST_PATH_CORROBORATION_MIN_TOKENS:
                stripped_scored = _sp._bm25_cross_family_scores(
                    stripped_task, role, repo_root, home, target_repo_root)
                stripped_names = [n for _s, n, _d, _src in
                                   stripped_scored[:_sp._CROSS_FAMILY_CONSULT_TOPN]]
                if name not in stripped_names:
                    continue
            fast.append((pos, name, d))
            break
    fast.sort()
    fast = fast[:k]
    fast_dirs = [d for _pos, _name, d in fast]
    fast_names = [name for _pos, name, _d in fast]
    outcome_prefix = f"fast-path:{','.join(fast_names)}" if fast_names else ""
    remaining = k - len(fast_dirs)
    if remaining <= 0:
        return fast_dirs, outcome_prefix
    candidates = [(name, d, source)
                  for _, name, d, source in scored[:_sp._CROSS_FAMILY_CONSULT_TOPN]
                  if name not in fast_names]
    if not candidates:
        return fast_dirs, (outcome_prefix or "no-candidates")
    try:
        picked, _detail = _sp._skill_judge_consult(task_text, role, candidates, issue, cwd,
                                               model=model, max_picks=remaining)
        outcome = "completed"
    except Exception as ex:
        print(f"[{role}] skill_judge 자문 실패 — BM25 top-{remaining} 로 fail-open: {ex}",
              file=sys.stderr)
        picked = [d for _, name, d, _ in scored if name not in fast_names][:remaining]
        outcome = "fail-open"
    if outcome_prefix:
        outcome = f"{outcome_prefix}+{outcome}"
    return fast_dirs + picked, outcome


def _composed_consult_skill_source(role: str, task_text: str | None,
                                   issue: int | None, cwd: str | None,
                                   model: str | None) -> dict:
    """이슈 #2507: consult/verb/panel 세션이 마운트할 skill_dirs 를,
    역할 가이던스(`resolve_role_source()` — 오늘의 기준선, 절대 안
    줄어든다)에 과제 텍스트 기반 cross-family 매치(스폰 마운트 경로와
    같은 `_cross_family_skill_matches_with_consult()` BM25+skill_judge
    매치)를 add-only 로 얹어 구성한다(`merge_composed_skill_source()`).
    role_source 를 대체하지 않고 얹기만 하는 이유: 자문 질문/verb
    요청문은 스폰 과제 텍스트보다 훨씬 짧고 좁을 수 있어(예: 한 줄
    판단 질문), 대체 방식은 "세션이 스킬을 예전보다 덜 갖고 도착"하는
    실패 모드(이슈 acceptance 가 명시적으로 금지)를 낳을 위험이 있다 —
    add-only 는 그 위험을 구조적으로 없앤다.

    `task_text` 가 없으면(빈 문자열/None) 매치 단계를 건너뛰고
    role_source 를 그대로 돌려준다 — 이 가드가 없으면
    `_skill_judge_consult()` -> `_consult_cmd_and_env()` -> 이 함수 ->
    `_cross_family_skill_matches_with_consult()` ->
    `_skill_judge_consult()` 순환 재귀가 생긴다(`_skill_judge_consult()`
    자신도 `_consult_cmd_and_env()` 를 통해 세션을 조립하기 때문 — 호출
    그래프 확인됨, 그 호출부는 이 함수 시그니처에 `task_text` 를 안
    넘겨 자동으로 매치 단계를 건너뛴다)."""
    role_source = _sp.resolve_role_source(role, _sp._skill_repo_root())
    if not task_text:
        return role_source
    matched_dirs, _outcome = _sp._cross_family_skill_matches_with_consult(
        task_text, role, _sp._skill_repo_root(), issue, cwd,
        k=_sp._COMPOSED_SKILLS_TOPK, model=model)
    return _sp.merge_composed_skill_source(role_source, matched_dirs)


def _consult_cmd_and_env(role: str, cwd: str | None,
                         model: str | None = None,
                         exclude_core_plugins: frozenset[str] = frozenset(),
                         task_text: str | None = None,
                         issue: int | None = None
                         ) -> tuple[list[str], dict[str, str], str]:
    """`consult_cmd()`의 argv/env/settings-file 조립만 떼어낸, subprocess 를
    직접 부르지 않는 build-then-return 헬퍼 — `spawn_cmd()` 와 같은 모양이다.
    `(cmd, env, settings_path)` 를 돌려준다 — settings_path 는 호출자가
    끝에 `os.unlink` 로 치워야 하는 임시 파일이라 별도로 넘긴다.

    이슈 #1141: `CLAUDE_PLUGIN_ROOT_CORE` 를 `core_plugin_dirs()` 에서
    주입한다 — `spawn_cmd()` 가 이슈 #182 때부터 갖고 있던 것과 똑같은
    한 줄(spawn.py 의 `spawn_cmd()` 참조). 이 변수가 없으면 core 훅이
    `hooks/lib/gate-lib.sh` 를 상대경로 fallback 으로 찾다가 자문 세션의
    작업 디렉터리 밑에서는 실패해 하드블록한다 — 그 블록 에러 텍스트가
    "모델 출력"으로 캡처되어 판단 JSON 파싱이 매번 실패하는 게 이 이슈의
    근본원인이었다.

    분리 이유: 이대로 `consult_cmd()` 안에 인라인해두면 테스트가 이
    주입 로직을 재구현해야만 검증할 수 있다 — 실제 코드경로를 안 타는
    테스트는 이 이슈가 닫으려는 드리프트류를 그대로 재현한다(경고 문서:
    docs/issue-1141/reports/implementation/2026-08-13-hunt-consult-core-plugin-root-injection.md).

    이슈 #1955: 역할 가이던스는 이제 항상 skill-repository 에서 온다 —
    `resolve_role_source()` 가 매핑하는 스킬 디렉터리를 그대로 붙인다.

    이슈 #2507: `task_text` 가 주어지면(consult_cmd/`_verb_cmd` 가 각자
    질문/요청문을 넘긴다) `_composed_consult_skill_source()` 로 과제-텍스트
    매치를 role_source 위에 add-only 로 얹는다 — 안 주어지면(예:
    `_skill_judge_consult()` 자신의 내부 호출) 예전과 바이트 단위로
    같은 role_source 만 쓴다.

    이슈 #2201: `exclude_core_plugins` 는 `_JUDGE_EXCLUDED_CORE_PLUGINS`
    (issue #1587) 와 같은 모양의 opt-in 필터 — 기본값(빈 집합)은 오늘의
    모든 호출부(consult_cmd/panel/judge 계열)를 바이트 단위로 그대로
    둔다. `--plugin-dir` 로 붙는 core 마켓플레이스 플러그인(core/terse/
    freelunch/scout/warrant) 은 저마다 SessionStart 훅을 달고 있어,
    "판단 하나만 돌려주면 끝"인 좁은 판정 호출(예: skill_judge)에도
    무조건 전부 로드된다 — 실측(이 함수와 같은 argv 모양, `--plugin-dir`
    5개 vs 0개, /tmp 빈 디렉터리): 0개일 때 real 10.5s, 5개일 때 real
    15.6s(둘 다 haiku, 동일 트리비얼 프롬프트) — 델리버리 지향 훅
    (freelunch/scout/warrant) 을 제외하는 것만으로 세션당 수 초가
    빠진다.

    이슈 #2213: PR #2212 이 바깥 역할 스폰(`spawn_cmd()`, pipeline.py)에
    얹은 `--exclude-dynamic-system-prompt-sections` +
    `ENABLE_PROMPT_CACHING_1H=1` 를 이 함수는 그동안 물려받지 않았다 —
    consult/skill_judge/verb/judge 계열이 전부 이 함수 하나로 조립되는데
    (독스트링 "재사용" 절 참고), cwd 가 매 호출(특히 매 스폰의
    `_skill_judge_consult`)마다 격리 워크스페이스로 바뀌면 그 가변 cwd/
    git 상태가 시스템 프롬프트 프리픽스에 박혀 프롬프트 캐시가 절대
    히트하지 않는다 — cross_family 단계의 19s-74s 스프레드로 실측된
    바로 그 증상(이슈 #2213 본문의 강한 가설). 두 플래그 모두 바깥
    스폰과 동일한 근거(위 `spawn_cmd()` 독스트링)로 무조건 얹는다 —
    `--system-prompt` 전체 교체를 안 쓰는 한 no-op 위험이 없고, 1h 캐시
    TTL 옵트인도 부작용이 없다. 실측(이슈 #2213 계측 18건, 아래 기록):
    cache 관련 플래그가 붙으면 매 호출 cache_read_input_tokens 가
    18140->21937 로 오르고 cache_creation_input_tokens 는
    ~11.6k->~7.7k 로 줄어 — 캐시 자체는 실제로 개선된다. 하지만 wall
    time p50 만 53.1s->39.9s 로 줄고 p90/max(66-70s대)는 거의 그대로다
    — 이 플래그 하나로 19s-74s 스프레드 전체가 설명되지는 않는다(기록
    본문 "Investigate" 절 참고, 잔여 변동은 모델 자체
    duration_ms 변동과 거의 1:1 로 움직인다)."""
    plugins = _sp._composed_consult_skill_source(
        role, task_text, issue, cwd, model)["skill_dirs"]
    s = _sp.role_settings(role, cwd, inject_self_hosted_hooks=False)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(s, tf)
        settings_path = tf.name
    _sp._record_tmp_resource(settings_path, os.getpid(), "settings")  # issue #2468
    cmd = ["claude", "-p", "--settings", settings_path,
           "--permission-mode", "bypassPermissions",
           "--output-format", "json",
           "--exclude-dynamic-system-prompt-sections"]
    for p in plugins:
        cmd += ["--plugin-dir", str(p)]
    for p in _sp.core_plugin_dirs():
        if p.name not in exclude_core_plugins:
            cmd += ["--plugin-dir", str(p)]
    role_model = _sp.resolved_role_model(model)
    if role_model:
        cmd += ["--model", role_model]
    env = {**os.environ, "CLAUDE_ROLE": role, "TOKENMAXXXER_SPAWNED": "1",
           "ENABLE_PROMPT_CACHING_1H": "1"}
    core_dir = next((p for p in _sp.core_plugin_dirs() if Path(p).name == "core"), None)
    if core_dir:
        env["CLAUDE_PLUGIN_ROOT_CORE"] = str(core_dir)
    return cmd, env, settings_path


def consult_cmd(role: str, question: str, issue: int | None = None,
                cwd: str | None = None, model: str | None = None) -> dict:
    """자문(consult): 역할의 스킬-저장소 가이던스를 로드해 판단만 돌려받는다 — 브랜치도
    커밋도 PR 도 만들지 않는다(이슈 #699 R1). `spawn_cmd()`/`_spawn_one()`
    의 발급 파이프라인과는 별개의, 훨씬 작은 조립이다: 그 함수들이 여는
    브랜치/워크스페이스/워처/roster 등록은 전부 배달물(deliverable)을
    향한 것이고, 자문은 텍스트 하나만 되돌려주면 끝나기 때문이다.

    스킬-저장소 가이던스 로딩은 `role_settings()`/`resolve_role_source()` 를 그대로 재사용한다 —
    이슈#699 phase-1 proposal 이 채택한 이유: 가이던스를 켜는 코드경로가
    두 벌로 갈라지면 spawn 경로만 고치고 consult 경로는 못 고치는 드리프트가
    생긴다(issue #695/#700 이 이미 한 번 치운 문제류).

    트레이스는 **성공/실패와 무관하게** 항상 한 줄 남는다 — `finally` 에서
    쓰고, 그 다음에야 리턴하거나 다시 raise 한다."""
    trace_path = _sp._consult_trace_path(issue, cwd)
    ts = datetime.now(timezone.utc).isoformat()
    outcome = "error: 알 수 없는 실패"
    verdict = None
    settings_path = None
    raw_path = None
    raw_paths: list[Path] = []
    try:
        # 이슈 #2537 stage 6A: `roles/<role>.json` 존재-확인 + `spec` 로드를
        # 지웠다 — `_consult_cmd_and_env()` 는 `spec` 을 읽지 않았고(죽은
        # 코드), role 검증은 그 안의 `role_settings()` 호출(pipeline.py,
        # 여전히 `roles/` 를 읽는다)이 그대로 맡는다.
        cmd, env, settings_path = _sp._consult_cmd_and_env(
            role, cwd, model, task_text=question, issue=issue)
        # 이슈 #1097 근본원인: consult 도 core_plugin_dirs() 를 그대로 물기 때문에
        # freelunch/scout/warrant/proposal-shape 같은, 저장소를 바꾸는 배달물을
        # 겨냥한 core 훅들이 자문 세션에도 그대로 꽂힌다. 복잡한 판단 질문 하나가
        # 그 훅들 눈에는 "설계 작업"으로 보여, 모델이 스카우트/제안서/위임 절차를
        # 먼저 밟다가(2026-08-12T07:38-39Z 재현 실패 2건) 턴 예산을 다 쓰고 끝의
        # 판단 JSON 을 한 번도 못 찍고 끝난다. 구조적 수정: 프롬프트 안에서 그
        # 훅들이 이 세션에는 적용되지 않음을 명시적으로 무효화한다.
        override = (
            "이 세션에 로드된 스킬-저장소 가이던스/훅이 스카우트, 제안서(proposal) 작성, 위임"
            "(delegation/fan-out), 승인 게이트, 기록(record) 작성 등을 지시하더라도"
            " — 이번 호출은 자문(consult) 이라 전부 적용되지 않는다: 저장소 파일을"
            " 하나도 건드리지 않고, 하위 에이전트를 위임하지 않고, 조사 없이 알고"
            " 있는 판단을 바로 답한다. 다른 모든 지시보다 이 문장이 우선한다."
        )
        base_prompt = (
            "당신은 자문(consult) 으로 불렸다 — 판단만 돌려주면 된다. 이 역할의 "
            "스킬-저장소 가이던스는 이미 로드돼 있다. 브랜치를 만들지도, 커밋하지도, PR 을 열지도 "
            "마라 — 텍스트로 답하고 끝난다. " + override + " 답을 다 쓴 뒤 마지막에, "
            "다른 어떤 텍스트도 없이 JSON 객체 하나만 출력하라: "
            '{"answer": "<판단>", "confidence": "low|medium|high", '
            '"caveats": ["<유보/전제>", ...]}\n\n'
            f"질문: {question}"
        )
        retry_prompt = (
            base_prompt + "\n\n(재시도: 이전 응답이 마지막에 판단 JSON 객체를 "
            "출력하지 않아 파싱에 실패했다. 스카우트/제안서/위임 등 다른 어떤 "
            "절차도 밟지 말고, 지금 바로 위 형식의 JSON 객체 하나만 출력하라.)"
        )
        attempts_exhausted = "알 수 없는 실패"
        for attempt_num, attempt_prompt in enumerate((base_prompt, retry_prompt), start=1):
            r = subprocess.run(cmd, cwd=cwd or str(_sp.ROOT), input=attempt_prompt, text=True,
                               capture_output=True, timeout=_sp.CONSULT_TIMEOUT, env=env)
            if r.returncode != 0:
                attempts_exhausted = f"세션 종료 코드 {r.returncode}: {r.stderr.strip()[:300]}"
                continue
            result = _sp.session_result(r.stdout)
            raw_text = result.get("result", "")
            verdict = _sp._parse_consult_verdict(raw_text)
            if verdict is None:
                raw_path = _sp._persist_consult_raw_output(issue, ts, attempt_num, raw_text, cwd)
                raw_paths.append(raw_path)
                excerpt = raw_text[-300:].replace("\n", " ")
                attempts_exhausted = (
                    f"모델 출력에서 판단 JSON 을 못 찾음 (원본: `{raw_path}`, "
                    f"끝부분: {excerpt!r})"
                )
                continue
            outcome = (f"ok: {str(verdict.get('answer', ''))[:200]}"
                       + _sp._consult_evidence_suffix(verdict, cwd))  # issue #2104
            return verdict
        outcome = f"error: {attempts_exhausted} (재시도 1회 포함, 모두 실패)"
        raise RuntimeError(outcome)
    except subprocess.TimeoutExpired:
        outcome = f"error: 시간초과({_sp.CONSULT_TIMEOUT}s)"
        raise
    finally:
        if settings_path:
            with contextlib.suppress(OSError):
                os.unlink(settings_path)
        _sp._append_consult_trace(trace_path, ts, role, issue, question, outcome)
        commit_paths = [trace_path] + raw_paths
        _sp._commit_consult_trace(commit_paths, issue, role, outcome, cwd)


_VERB_REQUIRED_KEY = {"ideate": "options", "draft": "draft", "review": "findings"}
_VERB_INSTRUCTIONS = {
    "ideate": (
        "당신은 아이디어 발산(ideate)으로 불렸다 — 하나의 판단이 아니라 서로 다른 "
        "선택지 여럿을 내놓아야 한다. 브랜치를 만들지도, 커밋하지도, PR 을 열지도 "
        "마라 — 텍스트로 답하고 끝난다."
    ),
    "draft": (
        "당신은 초안 작성(draft)으로 불렸다 — 산출물의 스케치를 텍스트로 돌려주면 "
        "된다. 저장소에 파일을 쓰지 마라 — 호출자가 이 초안을 쓸지 말지 결정한다. "
        "브랜치를 만들지도, 커밋하지도, PR 을 열지도 마라."
    ),
    "review": (
        "당신은 검토(review)로 불렸다 — 아래 제시된 텍스트/diff 에 대한 구조화된 "
        "피드백만 돌려주면 된다. 저장소에 파일을 쓰지 마라. 브랜치를 만들지도, "
        "커밋하지도, PR 을 열지도 마라."
    ),
}
_VERB_JSON_SHAPE = {
    "ideate": '{"options": ["<option>", ...], "tradeoffs": ["<tradeoff>", ...]}',
    "draft": '{"draft": "<text>", "open_questions": ["<question>", ...]}',
    "review": '{"findings": ["<finding>", ...], "verdict": "<summary verdict>"}',
}


def _parse_verb_json(text: str, required_key: str) -> dict | None:
    """`_parse_consult_verdict()`와 같은 모양이지만 필수 키를 verb 마다
    다르게 받는다 — consult 의 "answer" 대신 ideate/draft/review 각자의
    반환 키(options/draft/findings)를 찾는다."""
    if not text:
        return None
    for i in reversed([j for j, c in enumerate(text) if c == "{"]):
        try:
            obj, _ = json.JSONDecoder().raw_decode(text, i)
        except ValueError:
            continue
        if isinstance(obj, dict) and required_key in obj:
            return obj
    return None


def _verb_cmd(verb: str, role: str, prompt_text: str, issue: int | None = None,
             cwd: str | None = None) -> dict:
    """`consult_cmd()`의 형제 verb 공용 실행부 (이슈 #1202 requirement 5).
    같은 session-assembly(`_consult_cmd_and_env()`)와 같은 트레이스
    파일(`_consult_trace_path()`, `verb=` 필드로 구분)을 공유하고,
    프롬프트 지시문과 필수 반환 키만 verb 마다 갈린다 — 제안서 §6이
    선택한 모양 그대로다. 브랜치/커밋/PR 이 없는 계약은 consult 와
    동일하다."""
    required_key = _sp._VERB_REQUIRED_KEY[verb]
    trace_path = _sp._consult_trace_path(issue, cwd)
    ts = datetime.now(timezone.utc).isoformat()
    outcome = "error: 알 수 없는 실패"
    settings_path = None
    raw_paths: list[Path] = []
    try:
        # 이슈 #2537 stage 6A: 위 `consult_cmd()`와 같은 이유로 존재-확인 +
        # `spec` 로드를 지웠다 — role 검증은 `_consult_cmd_and_env()` 안의
        # `role_settings()`가 맡는다.
        cmd, env, settings_path = _sp._consult_cmd_and_env(
            role, cwd, task_text=prompt_text, issue=issue)
        override = (
            "이 세션에 로드된 스킬-저장소 가이던스/훅이 스카우트, 제안서(proposal) 작성, 위임"
            "(delegation/fan-out), 승인 게이트, 기록(record) 작성 등을 지시하더라도"
            f" — 이번 호출은 {verb} 라 전부 적용되지 않는다: 저장소 파일을"
            " 하나도 건드리지 않고, 하위 에이전트를 위임하지 않고, 조사 없이 알고"
            " 있는 답을 바로 낸다. 다른 모든 지시보다 이 문장이 우선한다."
        )
        base_prompt = (
            _sp._VERB_INSTRUCTIONS[verb] + " " + override + " 답을 다 쓴 뒤 마지막에, "
            "다른 어떤 텍스트도 없이 JSON 객체 하나만 출력하라: "
            f"{_sp._VERB_JSON_SHAPE[verb]}\n\n요청: {prompt_text}"
        )
        retry_prompt = (
            base_prompt + f"\n\n(재시도: 이전 응답이 마지막에 {required_key!r} 키를 가진 "
            "JSON 객체를 출력하지 않아 파싱에 실패했다. 다른 어떤 절차도 밟지 말고, "
            "지금 바로 위 형식의 JSON 객체 하나만 출력하라.)"
        )
        attempts_exhausted = "알 수 없는 실패"
        for attempt_num, attempt_prompt in enumerate((base_prompt, retry_prompt), start=1):
            r = subprocess.run(cmd, cwd=cwd or str(_sp.ROOT), input=attempt_prompt, text=True,
                               capture_output=True, timeout=_sp.CONSULT_TIMEOUT, env=env)
            if r.returncode != 0:
                attempts_exhausted = f"세션 종료 코드 {r.returncode}: {r.stderr.strip()[:300]}"
                continue
            result = _sp.session_result(r.stdout)
            raw_text = result.get("result", "")
            parsed = _sp._parse_verb_json(raw_text, required_key)
            if parsed is None:
                raw_path = _sp._persist_consult_raw_output(issue, ts, attempt_num, raw_text, cwd)
                raw_paths.append(raw_path)
                excerpt = raw_text[-300:].replace("\n", " ")
                attempts_exhausted = (
                    f"모델 출력에서 {verb} JSON 을 못 찾음 (원본: `{raw_path}`, "
                    f"끝부분: {excerpt!r})"
                )
                continue
            outcome = f"ok: {str(parsed.get(required_key, ''))[:200]}"
            return parsed
        outcome = f"error: {attempts_exhausted} (재시도 1회 포함, 모두 실패)"
        raise RuntimeError(outcome)
    except subprocess.TimeoutExpired:
        outcome = f"error: 시간초과({_sp.CONSULT_TIMEOUT}s)"
        raise
    finally:
        if settings_path:
            with contextlib.suppress(OSError):
                os.unlink(settings_path)
        _sp._append_consult_trace(trace_path, ts, role, issue, prompt_text, outcome, verb=verb)
        commit_paths = [trace_path] + raw_paths
        _sp._commit_consult_trace(commit_paths, issue, role, outcome, cwd)


def ideate_cmd(role: str, prompt_text: str, issue: int | None = None,
              cwd: str | None = None) -> dict:
    """divergent options — `{"options": [...], "tradeoffs": [...]}`."""
    return _sp._verb_cmd("ideate", role, prompt_text, issue=issue, cwd=cwd)


def draft_cmd(role: str, prompt_text: str, issue: int | None = None,
             cwd: str | None = None) -> dict:
    """deliverable sketch — `{"draft": "...", "open_questions": [...]}`.
    No `write_scope` applies: the caller decides whether to use the
    text, the verb itself never writes to the repo."""
    return _sp._verb_cmd("draft", role, prompt_text, issue=issue, cwd=cwd)


def review_cmd(role: str, prompt_text: str, issue: int | None = None,
              cwd: str | None = None) -> dict:
    """structured feedback — `{"findings": [...], "verdict": "..."}`."""
    return _sp._verb_cmd("review", role, prompt_text, issue=issue, cwd=cwd)


# ---------------------------------------------------------------------------
# issue #1587 — `judge`: read-only, budgeted role judgment over a merge diff.
#
# 격리는 프롬프트 문장이 아니라 세션 조립(`--plugin-dir`/`permissions`)에서
# 난다 — consult/`_verb_cmd()`가 겪은 #1097 근본원인(공격 가능한 diff 내용이
# 모델을 설득할 수 있는 문자열 무효화)을 judge 는 구조적으로 피한다. 그래서
# `_consult_cmd_and_env()`를 재사용하지 않고 judge 전용 조립을 따로 둔다
# (제안서 Rationale 참고).
# ---------------------------------------------------------------------------

# core 플러그인 중 "배달(delivery)" 지향인 것 — 제안 작성/승인 게이트/팬아웃
# 위임을 모델에게 지시한다. judge 세션은 diff 를 읽고 판단만 돌려주면
# 끝이라 이런 훅이 꽂히면 안 된다(이슈가 명시한 구조적 격리 지점). core 의
# 나머지(core 자체, terse)는 무해하므로 남긴다.
_JUDGE_EXCLUDED_CORE_PLUGINS = {"freelunch", "scout", "warrant"}


def _readonly_plugin_dirs(role: str) -> list[Path]:
    """judge 세션에 붙일 플러그인 — 역할 가이던스(이슈 #1955: skill-repository,
    `resolve_role_source()`)는 그대로 싣는다(무엇을 위반했는지 판단하려면
    가이던스 전체가 필요하다), core 는 `_JUDGE_EXCLUDED_CORE_PLUGINS` 로
    배달 지향 훅만 걸러낸다.

    이슈 #2507 disposition: 여기는 과제 텍스트 매치로 옮기지 않고
    role-shaped 그대로 유지한다 — `judge_cmd()`가 판단하는 대상은 "이번
    과제가 뭔지"가 아니라 "이 merge 가 role 의 write_scope/record
    계약을 지켰는지"이므로 판단 기준 자체가 role 고정이다. 과제 텍스트
    매치로 좁히면 그 role 계약 조항 중 이번 diff 와 표면적으로 안
    겹치는 항목(예: 드물게 걸리는 write-scope 예외)이 후보에서 빠져
    위반을 놓칠 위험이 있다 — 자문 guidance 완화가 아니라 fail-closed
    enforcement 정확성 문제라 add-only 매치조차 불필요한 잡음이다."""
    out = list(_sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"])
    for p in _sp.core_plugin_dirs():
        if p.name not in _sp._JUDGE_EXCLUDED_CORE_PLUGINS:
            out.append(p)
    return out


def _readonly_bash_allow(cwd: str) -> list[str]:
    """`git show`/`git diff`/`git log` 만 — `_workspace_bash_allow()`와 같은
    모양으로 `cwd` 에 앵커링한다. gh, Write, Edit 을 향한 경로는 여기 없다
    (grep-checkable 제약, 제안서 Constraints)."""
    return [
        f"Bash(cd {cwd} && git show *)",
        f"Bash(cd {cwd} && git diff *)",
        f"Bash(cd {cwd} && git log *)",
        f"Bash(git -C {cwd} show *)",
        f"Bash(git -C {cwd} diff *)",
        f"Bash(git -C {cwd} log *)",
    ]


def _readonly_settings(role: str, cwd: str) -> dict:
    """읽기 전용 세션 설정 — `role_settings()`의 샌드박스/전역-플러그인
    차단은 그대로 쓰되, `permissions.allow`를 Read/Grep/Glob + git 플루밍
    Bash 로만 한정하고 Write/Edit/`gh `를 `permissions.deny`로 명시적으로
    막는다. `--permission-mode bypassPermissions`를 주지 않는 것과 짝을
    이룬다 — headless 세션은 허용 목록에 없는 도구를 답할 사람 없이
    그냥 거부한다(role_settings() #742 문단이 서술하는 바로 그 실측 동작을,
    judge 는 위험이 아니라 안전장치로 쓴다)."""
    s = _sp.role_settings(role, cwd, inject_self_hosted_hooks=False)
    s["permissions"] = {
        "allow": ["Read", "Grep", "Glob", *_sp._readonly_bash_allow(cwd)],
        "deny": ["Write", "Edit", "Bash(gh *)"],
    }
    return s


def _judge_cmd_and_env(role: str, cwd: str,
                       model: str | None = None) -> tuple[list[str], dict[str, str], str]:
    """judge 계열(judge 본세션/prefilter/validator) 공용 argv/env/settings
    조립. `_consult_cmd_and_env()`와 같은 build-then-return 모양이지만
    `--permission-mode bypassPermissions`를 주지 않고(읽기전용 강제),
    `_readonly_plugin_dirs()`/`_readonly_settings()`를 쓴다."""
    plugins = _sp._readonly_plugin_dirs(role)
    s = _sp._readonly_settings(role, cwd)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(s, tf)
        settings_path = tf.name
    _sp._record_tmp_resource(settings_path, os.getpid(), "settings")  # issue #2468
    cmd = ["claude", "-p", "--settings", settings_path, "--output-format", "json"]
    for p in plugins:
        cmd += ["--plugin-dir", str(p)]
    cmd += ["--model", model or _sp.resolved_role_model()]
    env = {**os.environ, "CLAUDE_ROLE": role, "TOKENMAXXXER_SPAWNED": "1"}
    core_dir = next((p for p in _sp.core_plugin_dirs() if Path(p).name == "core"), None)
    if core_dir:
        env["CLAUDE_PLUGIN_ROOT_CORE"] = str(core_dir)
    return cmd, env, settings_path


def _compress_diff(diff_text: str, cap_tokens: int = 18000) -> str:
    """PR-Agent 식 압축: 추가분을 남기고, 삭제-only 훅은 버리고, 삭제된
    파일은 이름만 남긴다. 그래도 `cap_tokens`(대략 4문자/토큰)를 넘으면
    실패가 아니라 파일명 목록으로 더 내려간다(제안서 Constraints:
    "graceful degradation to name lists, not a hard failure")."""
    cap_chars = cap_tokens * 4
    blocks = [b for b in re.split(r"(?=^diff --git )", diff_text, flags=re.MULTILINE) if b.strip()]

    def file_name(block: str) -> str:
        m = re.match(r"diff --git a/(\S+) b/(\S+)", block)
        return m.group(2) if m else "?"

    kept, collapsed = [], []
    for block in blocks:
        name = file_name(block)
        if "deleted file mode" in block:
            collapsed.append(f"deleted: {name}")
            continue
        hunks = re.split(r"(?=^@@ )", block, flags=re.MULTILINE)
        header, hunks = hunks[0], hunks[1:]
        surviving = [h for h in hunks
                     if any(l.startswith("+") and not l.startswith("+++") for l in h.splitlines())]
        if not surviving:
            collapsed.append(f"no-addition: {name}")
            continue
        kept.append(header + "".join(surviving))

    compressed = "\n".join(kept)
    if collapsed:
        compressed += "\n\n[collapsed files]\n" + "\n".join(collapsed)
    if len(compressed) <= cap_chars:
        return compressed

    names = "\n".join(file_name(b) for b in blocks)
    degraded = "[diff 압축 후에도 상한 초과 — 파일명 목록으로 축소]\n" + names
    return degraded[:cap_chars]


def _judge_trace_path(cwd: str) -> Path:
    """모든 judge 실행이 공유하는 트레이스 — `runs/patrol-judge-log.md`
    (제안서 §Constraints "trace-always", consult-log `finally` 관례와
    같은 이유). `runs/`는 git-ignored라 커밋 없이도 대상 트리를
    더럽히지 않는다(이슈 #1730)."""
    return _sp._consult_root(cwd) / "runs" / "patrol-judge-log.md"


def _append_judge_trace(path: Path, ts: str, role: str, merge_sha: str, outcome: str) -> None:
    """judge 실행 한 건당 한 줄 — 성공/실패/캡-초과 가리지 않는다. `merge=`
    필드는 `_judge_roles_run_today()`가 3-역할 캡을 세는 데 쓰는 grep
    앵커다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = (f"- {ts} | role={role} | verb=judge | merge={merge_sha} "
            f"| outcome={outcome[:300]!r}\n")
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


def _judge_roles_run_today(trace_path: Path, merge_sha: str) -> int:
    """이 merge_sha 에 대해 이미 트레이스에 남은 **실제 judge 세션 실행** 수 —
    3-역할 캡 판정에 쓴다. prefilter-미스 줄(`ok: prefilter 미스`)과
    캡-초과 거절 줄(`error: 캡 초과`)은 judge 세션이 실제로 돌지 않았으므로
    세지 않는다(이슈 #1605 — 이 두 outcome 을 세면 처음 3역할이 미스만 내도
    캡이 소진되고, 이후 매 역할의 거절 줄이 또 카운트를 올려 눈덩이처럼
    불어난다). ok-findings/ok-zero-findings/실제 실행 오류(타임아웃, 파싱
    실패 등)는 세션이 실제로 돈 것이므로 그대로 센다.

    **방어적으로 읽는다**: 트레이스 파일이 없거나(회전/최초 실행) 손상돼
    있으면 0 을 돌려준다 — 로그 부재/회전이 캡 판정을 막으면 안 된다는
    PR #1590 binding review note. 읽기 실패는 절대 캡을 가짜로 채우지
    않는다(항상 허용 쪽으로 fail)."""
    try:
        text = trace_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0
    needle = f"| merge={merge_sha} "
    count = 0
    for line in text.splitlines():
        if "verb=judge" not in line or needle not in line:
            continue
        if "prefilter 미스" in line or "캡 초과" in line:
            continue
        count += 1
    return count


_JUDGE_ROLE_EXCLUSIONS: dict[str, list[str]] = {
    # 역할별 알려진 오탐 패턴(문자열 부분일치) — validator 가 이 목록에
    # 걸리는 finding 은 무조건 버린다. 지금은 빈 채로 시작해, 실제 오탐이
    # 나타나면 그때 항목을 더한다(운영 결정 없이 상상으로 채우지 않는다).
}


def _judge_prefilter(role: str, diff_summary: str, cwd: str) -> bool:
    """관할 사전필터 — 하이쿠급 단일 호출로 "이 diff 가 이 역할의 관할에
    조금이라도 걸리는가"만 묻는다(제안서 §5, 가장 큰 비용 절감 지점).
    호출 자체가 실패하면(타임아웃/파싱 실패) **관련 있다고 가정**한다 —
    사전필터는 비용 절감 장치일 뿐 판단 장치가 아니라, 실패를 놓침으로
    바꾸면 안 된다."""
    cmd, env, settings_path = _sp._judge_cmd_and_env(role, cwd, model="haiku")
    prompt = (
        f"역할 '{role}' 의 관할(role jurisdiction) 안에 아래 diff 요약이 "
        "조금이라도 걸리는지만 판단하라. 다른 텍스트 없이 JSON 객체 하나만 "
        '출력하라: {"relevant": true|false}\n\ndiff 요약:\n' + diff_summary
    )
    try:
        r = subprocess.run(cmd, cwd=cwd, input=prompt, text=True,
                           capture_output=True, timeout=_sp.JUDGE_TIMEOUT, env=env)
        if r.returncode != 0:
            return True
        result = _sp.session_result(r.stdout)
        parsed = _sp._parse_verb_json(result.get("result", ""), "relevant")
        if parsed is None:
            return True
        return bool(parsed.get("relevant", True))
    except subprocess.TimeoutExpired:
        return True
    finally:
        with contextlib.suppress(OSError):
            os.unlink(settings_path)


def _judge_validate(role: str, findings: list[dict], diff_summary: str,
                    cwd: str) -> list[dict]:
    """확인/반박 검증 — 하이쿠급 단일 호출로 judge 가 낸 findings 를
    확인/기각하고, `_JUDGE_ROLE_EXCLUSIONS[role]`에 걸리는 것은 호출 전에
    이미 버린다(Anthropic security-review 패턴, 제안서 §5). 호출 자체가
    실패하면 **아무것도 큐에 넣지 않는다** — 검증 못 한 finding 을 큐로
    흘리는 쪽보다, 이번 실행에서 놓치는 쪽이 patrol 큐 오염보다 싸다."""
    exclusions = _sp._JUDGE_ROLE_EXCLUSIONS.get(role, [])
    candidates = [f for f in findings
                  if not any(x in f.get("excerpt", "") for x in exclusions)]
    if not candidates:
        return []
    cmd, env, settings_path = _sp._judge_cmd_and_env(role, cwd, model="haiku")
    prompt = (
        f"역할 '{role}' 가 낸 아래 findings 를 diff 요약과 대조해 확인(confirm)/"
        "반박(refute)하라. 실제로 스킬-저장소 가이던스를 위반하는 것만 남기고, 다른 텍스트 "
        '없이 JSON 객체 하나만 출력하라: {"findings": [{"path": "...", '
        '"finding_class": "...", "excerpt": "...", "promotable": true|false}, '
        "...]}  (반박된 것은 배열에서 뺀다)\n\n"
        f"diff 요약:\n{diff_summary}\n\nfindings:\n{json.dumps(candidates, ensure_ascii=False)}"
    )
    try:
        r = subprocess.run(cmd, cwd=cwd, input=prompt, text=True,
                           capture_output=True, timeout=_sp.JUDGE_TIMEOUT, env=env)
        if r.returncode != 0:
            return []
        result = _sp.session_result(r.stdout)
        parsed = _sp._parse_verb_json(result.get("result", ""), "findings")
        if parsed is None:
            return []
        return [f for f in parsed.get("findings", []) if isinstance(f, dict) and f.get("path")]
    except subprocess.TimeoutExpired:
        return []
    finally:
        with contextlib.suppress(OSError):
            os.unlink(settings_path)


def judge_cmd(role: str, merge_sha: str, cwd: str | None = None) -> dict:
    """`spawn.py judge <role> --merge <sha>` 의 본체 — 읽기 전용, 4단계
    파이프라인(prefilter -> judge -> validator -> enqueue), 트레이스는
    성공/실패/캡초과 가리지 않고 항상 한 줄(이슈 #1587, 제안서 §What will
    be done 6).

    3-역할/머지 캡(`JUDGE_MAX_ROLES_PER_MERGE`)은 트레이스 로그에서
    세되, `_judge_roles_run_today()`가 방어적으로 읽는다 — 로그가 없거나
    깨져 있어도 캡을 오탐하지 않고(0으로 fail), 이 실행 자체는 트레이스에
    한 줄을 항상 남긴다(binding review note, PR #1590)."""
    root = str(Path(cwd).resolve()) if cwd else str(_sp.ROOT)
    trace_path = _sp._judge_trace_path(root)
    ts = datetime.now(timezone.utc).isoformat()
    outcome = "error: 알 수 없는 실패"
    try:
        already = _sp._judge_roles_run_today(trace_path, merge_sha)
        if already >= _sp.JUDGE_MAX_ROLES_PER_MERGE:
            outcome = (f"error: 캡 초과 (merge={merge_sha} 에 이미 {already}개 역할 실행, "
                       f"상한 {_sp.JUDGE_MAX_ROLES_PER_MERGE})")
            return {"skipped": True, "reason": "cap_exceeded", "role": role, "merge": merge_sha}

        # 이슈 #2537 stage 6A: `roles/<role>.json` 존재-확인 + `spec` 로드를
        # 지웠다 — `_judge_prefilter()`/`_judge_cmd_and_env()` 는 `spec` 을
        # 안 읽었다(죽은 코드). role 검증은 `_judge_prefilter()` 안의
        # `role_settings()` 호출(pipeline.py, 여전히 `roles/` 를 읽는다)이
        # 여전히 맡는다 — 다만 그 검증이 아래 `git show` 뒤로 밀린다는
        # 차이는 있다(무효 role 은 여전히 거절되지만, 거절 전에 무해한
        # `git show` 서브프로세스 호출 하나가 더 실행된다).
        show = subprocess.run(["git", "-C", root, "show", "--no-color", merge_sha],
                              capture_output=True, text=True, timeout=_sp.JUDGE_TIMEOUT)
        if show.returncode != 0:
            outcome = f"error: git show 실패: {show.stderr.strip()[:300]}"
            raise RuntimeError(outcome)
        diff_summary = _sp._compress_diff(show.stdout)

        if not _sp._judge_prefilter(role, diff_summary, root):
            outcome = "ok: prefilter 미스 — judge 미호출"
            return {"skipped": True, "reason": "prefilter_miss", "role": role, "merge": merge_sha}

        cmd, env, settings_path = _sp._judge_cmd_and_env(role, root)
        prompt = (
            f"당신은 judge 로 불렸다 — 역할 '{role}' 의 스킬-저장소 가이던스 관점에서 아래 merge diff 가 "
            "그 가이던스를 위반하는지만 판단한다. 저장소 파일을 하나도 건드리지 말고(Write/Edit "
            "도구 없음), 브랜치/커밋/PR 을 만들지 마라. 필요하면 `git show`/`git diff`/"
            "`git log` 로 더 살펴봐도 된다. 답을 다 쓴 뒤 마지막에, 다른 어떤 텍스트도 "
            '없이 JSON 객체 하나만 출력하라: {"findings": [{"path": "...", '
            '"finding_class": "...", "excerpt": "...", "promotable": true|false}, ...]}\n\n'
            f"merge diff ({merge_sha}):\n{diff_summary}"
        )
        try:
            r = subprocess.run(cmd + ["--max-turns", "6"], cwd=root, input=prompt, text=True,
                               capture_output=True, timeout=_sp.JUDGE_TIMEOUT, env=env)
        finally:
            with contextlib.suppress(OSError):
                os.unlink(settings_path)
        if r.returncode != 0:
            outcome = f"error: judge 세션 종료 코드 {r.returncode}: {r.stderr.strip()[:300]}"
            raise RuntimeError(outcome)
        result = _sp.session_result(r.stdout)
        parsed = _sp._parse_verb_json(result.get("result", ""), "findings")
        raw_findings = parsed.get("findings", []) if parsed else []
        if not raw_findings:
            outcome = "ok: findings 없음"
            return {"skipped": False, "role": role, "merge": merge_sha, "enqueued": []}

        validated = _sp._judge_validate(role, raw_findings, diff_summary, root)
        if not validated:
            outcome = f"ok: {len(raw_findings)}건 중 validator 통과 0건"
            return {"skipped": False, "role": role, "merge": merge_sha, "enqueued": []}

        sys.path.insert(0, str((_sp.ROOT / "gates").resolve()))
        import patrol_queue
        queue_path = Path(root) / patrol_queue.QUEUE_REL_PATH
        queue = patrol_queue.load_queue(queue_path)
        enqueued = []
        # patrol_queue.verify(): 인용된 경로/발췌를 실제로 다시 읽어 확인한다
        # (run_scan() 이 이미 밟는 scan -> verify -> budget -> enqueue 파이프라인의
        # 그 단계) — validator(하이쿠급 반박 콜)는 모델의 자기평가일 뿐이라,
        # 환각된 path/excerpt 를 그대로 통과시킬 수 있다. verify() 를 건너뛰면
        # judge 만 유일하게 검증 안 된 finding 을 큐에 넣는 경로가 된다.
        for vf in validated:
            if not patrol_queue.verify(vf, Path(root)):
                continue
            fp = patrol_queue.fingerprint(f"judge:{role}", vf["path"], [vf.get("excerpt", "")])
            finding = {
                "fingerprint": fp,
                "scanner_id": f"judge:{role}",
                "path": vf["path"],
                "finding_class": vf.get("finding_class", "judge-finding"),
                "excerpt": vf.get("excerpt", ""),
                "last_seen": ts,
                "lane": "diff",
                "promotable": bool(vf.get("promotable", False)),
            }
            queue = patrol_queue.enqueue(queue, finding)
            enqueued.append(fp)
        patrol_queue.save_queue(queue_path, queue)
        outcome = (f"ok: {len(raw_findings)}건 중 {len(validated)}건 검증, "
                  f"{len(enqueued)}건 verify 통과 후 큐 반영")
        return {"skipped": False, "role": role, "merge": merge_sha, "enqueued": enqueued}
    except subprocess.TimeoutExpired:
        outcome = f"error: 시간초과({_sp.JUDGE_TIMEOUT}s)"
        raise
    finally:
        _sp._append_judge_trace(trace_path, ts, role, merge_sha, outcome)


class _PanelMessagingUnavailable(RuntimeError):
    """실측: crossSessionInbound 를 못 걸었거나 SendMessage 왕복이 한 번도
    안 잡혔다 — panel_cmd() 가 순차 consult 로 내려가는 신호."""


def _panel_slug(question: str) -> str:
    """질문을 파일명 조각으로 — 영숫자 외 문자는 `-`, 연속 `-`는 하나로,
    최대 60자(파일시스템/가독성 여유)."""
    s = re.sub(r"[^a-z0-9]+", "-", question.lower()).strip("-")
    return (s[:60].rstrip("-")) or "question"


def _panel_record_path(issue: int | None, slug: str, cwd: str | None = None) -> Path:
    """`docs/issue-<n>/reports/panel/` — 이슈가 없으면 표준 6버킷 중
    `reports/panel/` (`_consult_trace_path()` 와 같은 분기 이유). 앵커는
    `_consult_root()` 로 대상 레포(`-C`/cwd)에 맞춘다."""
    root = _sp._consult_root(cwd)
    if issue is not None:
        return root / "docs" / f"issue-{issue}" / "reports" / "panel" / f"{slug}.md"
    return root / "docs" / "reports" / "panel" / f"{slug}.md"


def _append_panel_turn(path: Path, ts: str, role: str, kind: str, text: str) -> None:
    """턴 하나당 한 줄 — 라이브 경로와 저하 경로가 이 한 헬퍼를 같이
    쓴다(제안서 §What will be done 2) — 두 경로가 서로 다른 기록 포맷으로
    갈라지지 않는다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = f"- {ts} | role={role} | {kind} | {text[:2000]!r}\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


def _extract_sendmessage_turns(stream_lines: list[dict]) -> list[str]:
    """`--output-format stream-json` 이벤트에서 `SendMessage` 도구 호출의
    `message` 인자만 뽑는다 — 세션 하나가 주고받은 실제 왕복을, 최종
    verdict 와 별개로 관찰하기 위해서다."""
    turns = []
    for ev in stream_lines:
        if ev.get("type") != "assistant":
            continue
        for block in (ev.get("message", {}).get("content") or []):
            if isinstance(block, dict) and block.get("type") == "tool_use" \
                    and block.get("name") == "SendMessage":
                msg = (block.get("input") or {}).get("message")
                if msg:
                    turns.append(str(msg))
    return turns


def _run_panel_session(role: str, peer_role: str, question: str, cwd: str | None,
                       model: str | None = None) -> dict:
    """판정 세션 하나를 non-bare `claude -p` 로 띄운다 — `crossSessionInbound`
    를 걸어 `SendMessage` 를 받을 수 있게 한다(이슈#973 phase-1 조사: 공식
    문서, ListAgents/SendMessage 은 non-bare 세션에서만 열린다). 세션
    설정은 `consult_cmd()` 와 똑같이 `role_settings()`/`resolve_role_source()`
    로 조립한다 — 두 코드경로가 갈라지면 한쪽만 고쳐지는 드리프트가 난다
    (#695/#700, `consult_cmd()` 독스트링과 같은 이유).

    `TOKENMAXXXER_PANEL_MESSAGING=unavailable` 이 켜져 있으면
    `_PanelMessagingUnavailable` 을 던진다 — 크로스세션 소켓이 막힌
    샌드박스/CI 환경이 스스로 신고하는 경로다. 호출자는 이걸 순차
    consult 로 내리는 신호로 쓴다."""
    if os.environ.get("TOKENMAXXXER_PANEL_MESSAGING") == "unavailable":
        raise _sp._PanelMessagingUnavailable(f"{role}: TOKENMAXXXER_PANEL_MESSAGING=unavailable")
    # 이슈 #2537 stage 6A: `roles/<role>.json` 존재-확인 + `spec` 로드를
    # 지웠다 — 아래 `_sp.role_settings()` 호출(pipeline.py, 여전히
    # `roles/` 를 읽는다)이 role 검증을 그대로 맡는다.
    # 이슈 #2507: `issue` 가 이 함수 시그니처에 없어(`panel_cmd()` 는 갖고
    # 있지만 그 아래 세션 하나씩 실행하는 이 헬퍼는 원래부터 안 받았다)
    # None 으로 넘긴다 — `_composed_consult_skill_source()`/
    # `_skill_judge_consult()` 양쪽 다 issue=None 을 trace/raw-output 경로
    # 네이밍에만 쓰고(이미 adhoc consult 호출이 매일 거치는 경로) 판단
    # 로직 자체에는 안 쓴다.
    plugins = _sp._composed_consult_skill_source(
        role, question, None, cwd, model)["skill_dirs"]
    s = _sp.role_settings(role, cwd, inject_self_hosted_hooks=False)
    s["crossSessionInbound"] = "accept"
    settings_path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
            json.dump(s, tf)
            settings_path = tf.name
        _sp._record_tmp_resource(settings_path, os.getpid(), "settings")  # issue #2468
        cmd = ["claude", "-p", "--settings", settings_path,
               "--permission-mode", "bypassPermissions",
               "--output-format", "stream-json", "--verbose"]
        for p in plugins:
            cmd += ["--plugin-dir", str(p)]
        for p in _sp.core_plugin_dirs():
            cmd += ["--plugin-dir", str(p)]
        role_model = _sp.resolved_role_model(model)
        if role_model:
            cmd += ["--model", role_model]
        env = {**os.environ, "CLAUDE_ROLE": role, "TOKENMAXXXER_SPAWNED": "1"}
        prompt = (
            "당신은 판정단(panel) 판정자로 불렸다 — 다른 역할 판정자 "
            f"'{peer_role}' 와 함께 아래 질문을 판정한다. 이 역할의 스킬-저장소 가이던스는 "
            "이미 로드돼 있다. 브랜치를 만들지도, 커밋하지도, PR 을 열지도 "
            "마라. 상대 세션은 이 세션과 거의 동시에 떴다 — 아직 인박스가 "
            "등록되지 않았을 수 있다. 먼저 ListAgents 를 호출해 상대를 "
            f"찾아라('{peer_role}' 역할일 것이다). 안 보이면 몇 초 뒤 다시 "
            "ListAgents 를 호출하는 식으로 몇 차례 재시도하라 — 한 번만 "
            "확인하고 포기하지 마라. 상대가 보이면, ListAgents 가 실제로 "
            f"반환한 이름으로 SendMessage 를 보내라('{peer_role}' 같은 "
            "역할명이 아니라 그 이름 그대로 주소를 써라). 먼저 당신의 "
            "입장(position)을 한 문단으로 정리해 SendMessage 로 상대에게 "
            "보내라. 상대의 응답을 받은 뒤 최소 한 차례 반박(rebuttal)을 "
            "SendMessage 로 주고받아라. 교환이 끝나면 다른 어떤 텍스트도 "
            "없이 JSON 객체 하나만 출력하라: "
            '{"answer": "<판단>", "confidence": "low|medium|high", '
            '"caveats": ["<유보/전제>", ...]}\n\n'
            f"질문: {question}"
        )
        r = subprocess.run(cmd, cwd=cwd or str(_sp.ROOT), input=prompt, text=True,
                           capture_output=True, timeout=_sp.PANEL_TIMEOUT, env=env)
        if r.returncode != 0:
            raise RuntimeError(f"{role}: 세션 종료 코드 {r.returncode}: "
                               f"{r.stderr.strip()[:300]}")
        stream_lines = []
        for line in r.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            with contextlib.suppress(ValueError):
                stream_lines.append(json.loads(line))
        turns = _sp._extract_sendmessage_turns(stream_lines)
        final_text = ""
        for ev in reversed(stream_lines):
            if ev.get("type") == "result":
                final_text = ev.get("result", "")
                break
        verdict = _sp._parse_consult_verdict(final_text)
        return {"turns": turns, "verdict": verdict}
    finally:
        if settings_path:
            with contextlib.suppress(OSError):
                os.unlink(settings_path)


def _consult_or_record_error(path: Path, ts: str, role: str, question: str,
                              issue: int | None, cwd: str | None) -> tuple[dict | None, str | None]:
    """`consult_cmd()` 를 호출하되, 실패해도 밖으로 던지지 않는다 — 저하
    경로에서 `consult_cmd()` 실패는 panel 실행 전체를 크래시시켜선 안
    된다(#1045 결함 2). 실패하면 `consult-error` 턴으로 기록하고
    `(None, <에러 메시지>)` 를 돌려준다."""
    try:
        verdict = _sp.consult_cmd(role, question, issue, cwd)
    except Exception as e:  # noqa: BLE001 - 어떤 실패든 절대 밖으로 던지지 않는다
        msg = str(e)
        _sp._append_panel_turn(path, ts, role, "consult-error", msg)
        return None, msg
    _sp._append_panel_turn(path, ts, role, "verdict", str(verdict))
    return verdict, None


def _panel_degrade(path: Path, ts: str, role_a: str, role_b: str, question: str,
                    issue: int | None, cwd: str | None, reason: str) -> dict:
    """저하 경로 — 순차 `consult_cmd()` 두 번으로 판단을 받고, 저하했다는
    사실과 이유를 `degraded:` 마커로 기록에 남긴다(제안서, 병합 설계
    Open Question 4). 각 `consult_cmd()` 호출은 `_consult_or_record_error()`
    로 감싸 — 한쪽이 실패해도(#1045 결함 2) panel 실행 자체는 절대 raise
    하지 않고, 실패는 기록에 남기고 그 쪽 verdict 만 None 이 된다."""
    _sp._append_panel_turn(path, ts, "panel", "degraded", f"sequential-consult — {reason}")
    verdict_a, error_a = _sp._consult_or_record_error(path, ts, role_a, question, issue, cwd)
    verdict_b, error_b = _sp._consult_or_record_error(path, ts, role_b, question, issue, cwd)
    return {"degraded": True, "reason": reason,
            "verdict_a": verdict_a, "verdict_b": verdict_b,
            "error_a": error_a, "error_b": error_b,
            "record_path": str(path)}


def panel_cmd(role_a: str, role_b: str, question: str, issue: int | None = None,
              cwd: str | None = None, run_session=None,
              model: str | None = None) -> dict:
    """동시-판정(concurrent judgment): 두 역할을 non-bare 세션으로 띄워
    `SendMessage` 로 입장과 반박을 주고받게 하고, 매 턴을
    `docs/issue-<n>/reports/panel/<question-slug>.md` 에 남긴다(req#2/#5,
    이슈#973). `consult_cmd()` 의 형제 함수 — 브랜치/PR 없이 판단만
    돌려받는다는 점은 같고, 판정자가 둘이고 서로 대화한다는 점이 다르다.

    `run_session`: 판정 세션 하나를 실행하는 콜러블
    `(role, peer_role, question, cwd) -> {"turns": [...], "verdict": dict|None}`,
    기본은 `_run_panel_session()`(실제 `claude -p` 스폰). 테스트는 이
    인자로 진짜 프로세스 없이 씨드된 응답을 주입한다 — 이 파라미터가
    제안서의 "transport boundary" 다.

    메시징이 안 되면(`_PanelMessagingUnavailable`) 순차 `consult_cmd()`
    두 번으로 저하하고, 저하했다는 사실과 이유를 기록에 남긴다."""
    slug = _sp._panel_slug(question)
    path = _sp._panel_record_path(issue, slug, cwd)
    launcher = run_session or _sp._run_panel_session
    ts = datetime.now(timezone.utc).isoformat()
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            fut_a = ex.submit(launcher, role_a, role_b, question, cwd, model)
            fut_b = ex.submit(launcher, role_b, role_a, question, cwd, model)
            result_a = fut_a.result()
            result_b = fut_b.result()
    except _sp._PanelMessagingUnavailable as e:
        return _sp._panel_degrade(path, ts, role_a, role_b, question, issue, cwd, str(e))
    if not (result_a.get("turns") or result_b.get("turns")):
        # 두 세션 다 SendMessage 왕복이 한 건도 안 잡혔다 — 메시징이
        # 켜지긴 했지만 실제로는 왕복이 안 닿은 경우(제안서 §3의 두 번째
        # 저하 트리거). 이미 스폰된 세션의 verdict 는 버리고, 순차 consult
        # 로 다시 판단을 받아 저하했다는 사실과 함께 기록한다.
        return _sp._panel_degrade(path, ts, role_a, role_b, question, issue, cwd,
                               "no SendMessage round-trip observed")
    for role, result in ((role_a, result_a), (role_b, result_b)):
        turns = result.get("turns") or []
        for i, text in enumerate(turns):
            kind = "position" if i == 0 else "rebuttal"
            _sp._append_panel_turn(path, ts, role, kind, text)
        if result.get("verdict") is not None:
            _sp._append_panel_turn(path, ts, role, "verdict", str(result["verdict"]))
    return {"degraded": False, "verdict_a": result_a.get("verdict"),
            "verdict_b": result_b.get("verdict"), "record_path": str(path)}
