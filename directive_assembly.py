"""Spawned-session directive/record assembly + cross-family skill BM25
matching (issue #2207).

Extracted from spawn.py. Pure move — no behavior change. spawn.py imports
this module and re-exports every moved name, so external callers and tests
keep addressing them as `spawn.<name>`.

Patching-compat mechanism (copied from relay.py/roster.py/plumbing.py/
watchdog.py/events.py/consult.py/skills.py/lifecycle.py/board.py/
pipeline.py): every cross-function reference here into spawn.py's own
remaining namespace resolves at call time through `_sp` — the spawn module
object, injected by spawn.py right after it imports this module (guarded so
only the canonical spawn/__main__ module binds it) — so `mock.patch.object(
spawn, "<name>")` patches stay visible to the moved code, including a
moved-to-moved call such as `_cross_family_skill_matches` -> `_sp.
_bm25_cross_family_scores` (test/test_spawn_skill_judge_haiku_timeout_overlap.py
patches that name on `spawn`, not on this module). This also covers
`_sp.__file__`/`_sp.ROOT`: the checkpoint blocks below embed spawn.py's own
path in text handed to a spawned session (`python3 <spawn.py path>
await-approval ...`), so they must resolve through the spawn module object,
never `__file__` local to this file.
"""
from __future__ import annotations
import math
import re
import sys
from pathlib import Path

# The spawn module object; set by spawn.py on import. All cross-module
# lookups resolve through it at call time so monkeypatches on spawn
# attributes are seen, and so text embedding "spawn.py's path" names the
# real entry point rather than this file.
_sp = None


# Issue #2129: checkpoint mode — single-session propose-approve-implement.
# Appended to the directive only under --checkpoint (default spawns stay
# byte-identical). The wait loop lives HERE, in the instructions: the session
# runs ONE deterministic helper command (`spawn.py await-approval`) for the
# whole pause, so the wait costs no model turns. Implements the #1672
# decision (single session with an in-context approval checkpoint dominates
# the two-session split; Cognition/Anthropic research consensus on #1672).
_CHECKPOINT_CONTRACT_BLOCK = (
    "- Checkpoint mode (issue #2129, spawner-authorized via --checkpoint): "
    "this session replaces the two-session split with ONE session that "
    "pauses at the approval boundary.\n"
    "  1. Produce the phase-1 artifacts (survey/proposal under "
    "docs/issue-{issue}/) and open the proposal PR exactly as the default "
    "two-phase contract requires. Nothing about phase-1 changes.\n"
    "  2. Then, instead of ending the session, run EXACTLY ONE foreground "
    "Bash command for the whole wait (one tool call — set its timeout "
    "parameter to at least {bash_timeout_ms} ms; never poll in your own "
    "turns):\n"
    "     {python} {spawn_py} -C . await-approval --issue {issue} "
    "--session {role}\n"
    "     It writes the declared-wait file (.waiting-on.json, "
    "`issue:{issue}` / approve-token — the #2101 watchdog exemption) and "
    "polls `gh issue view {issue} --comments` machinery for the "
    "`APPROVE issue-{issue}/{role}` needle every CHECKPOINT_POLL_SECONDS "
    "(default 60, env-overridable), bounded by CHECKPOINT_WAIT_MAX_SECONDS "
    "(default 1800, env-overridable).\n"
    "  3. Exit code 0 = approved: continue IMMEDIATELY in this same "
    "context into phase-2 (implementation + record + PR). Do not rebuild "
    "context and do not respawn — the in-session approval satisfies the "
    "phase-2 approve token; every other gate and record/format contract "
    "is unchanged.\n"
    "  4. Exit code 3 = timeout: end the session cleanly. The proposal PR "
    "you already opened is the returned state, exactly as the two-session "
    "default leaves it — a later phase-2 session picks it up.\n"
)


def _checkpoint_contract_block(issue: int, role: str) -> str:
    """Render `_CHECKPOINT_CONTRACT_BLOCK` for this spawn. The Bash timeout
    hint covers the full bounded wait plus a one-minute margin."""
    bash_timeout_ms = int((_sp._checkpoint_wait_max_seconds() + 60) * 1000)
    return _CHECKPOINT_CONTRACT_BLOCK.format(
        issue=issue, role=role, python=sys.executable,
        spawn_py=Path(_sp.__file__).resolve(), bash_timeout_ms=bash_timeout_ms)


def _checkpoint_index_block(issue: int, role: str) -> str:
    """Issue #2135: the condensed inline checkpoint invariant. The
    actionable wait command and exit-code semantics stay inline; the full
    contract prose (`_CHECKPOINT_CONTRACT_BLOCK`) is materialized verbatim
    as `{DIRECTIVE_DIR}/checkpoint-mode.md` in the workspace AND (issue
    #2204) delivered via `--append-system-prompt` — no inline "Read that
    file" pointer here any more (see `_directive_system_prompt_block`)."""
    bash_timeout_ms = int((_sp._checkpoint_wait_max_seconds() + 60) * 1000)
    return (
        f"- Checkpoint mode (issue #2129, spawner-authorized via "
        f"--checkpoint): after opening the phase-1 proposal PR, do "
        f"NOT end the session — run EXACTLY ONE foreground Bash call "
        f"(timeout parameter >= {bash_timeout_ms} ms) for the whole "
        f"wait:\n"
        f"     {sys.executable} {Path(_sp.__file__).resolve()} -C . "
        f"await-approval --issue {issue} --session {role}\n"
        f"  exit 0 = approved: continue IMMEDIATELY into phase-2 in "
        f"this same context; exit 3 = timeout: end cleanly (the "
        f"proposal PR is the returned state).\n")


# ------------------------------------------------ directive diet (issue #2135)
# The spawned-session directive follows the #2102 index+sections pattern:
# always-on = task text + a compact invariant index; the long contract prose
# moves VERBATIM into on-demand files materialized into the workspace at
# bootstrap (`.on-the-record/directive/<section>.md`), each referenced by
# exactly one "Read <file> when <condition>" trigger line. Zero normative
# loss: every removed sentence lives verbatim in a section file; the inline
# lines are condensed invariants whose full text the file carries. Adhoc
# spawns (no issue, hence no isolated workspace to materialize into) keep
# the full prose inline — their assembly is byte-identical to before.
DIRECTIVE_DIR = ".on-the-record/directive"

# Issue #2100 item 4 (moved up from the admission section, issue #2262):
# needed by _TURN_BUDGET_PROSE below at module-eval time, so this constant
# has to exist before that string literal is built, not after.
DEFAULT_SESSION_MAX_TURNS = 200

# Moved verbatim from the issue-workspace preamble (issues #132/#1981 and
# the headless/run_in_background warning). The inline index keeps the
# one-line 완료의 정의 invariant plus a trigger line; this file is canon.
_COMPLETION_PROSE = (
    "완료의 정의: 변경이 이 브랜치에 **커밋**되고 push 되어 PR 로\n"
    "제출된 상태다. 미커밋 변경은 존재하지 않는 것과 같다 —\n"
    "세션을 끝내기 전에 반드시 커밋하라. push/PR 이 네트워크로\n"
    "막히면 커밋까지는 해 둬라: on-the-record 가 밖에서 릴레이한다.\n"
    "체크포인트 커밋: 길거나 백그라운드로 넘기는 검증을 시작하기\n"
    "전에 먼저 체크포인트 커밋을 해 두고, 검증이 끝난 뒤 amend 하거나\n"
    "후속 커밋을 추가하라 — 검증부터 하고 나중에 커밋하는 습관은\n"
    "세션이 검증 도중 끊길 때 미커밋 변경을 그대로 좌초시킨다.\n"
    "경고: 이 턴은 headless 이고 단발이다 — 세션이 끝나면 이 프로세스도\n"
    "끝난다. run_in_background 로 넘긴 작업은 부모 턴이 끝나는 순간 함께\n"
    "죽는다(백그라운드 워커가 커밋·push 를 대신 끝내줄 것이라고 가정하지\n"
    "마라 — 실측된 실패 패턴이다). 모든 작업은 이 턴 안에서 직접 끝내라.\n")

# Issue #2135 item 4: landing batching — guidance only, no gate enforces it.
_LANDING_BATCHING_PROSE = (
    "\nLanding batching (issue #2135, guidance only — no gate): when the "
    "work is ready to land, run the landing sequence as ONE composite Bash "
    "call (or the fewest calls possible):\n"
    "  git add <paths> && git commit -m <msg> && git push -u origin "
    "<branch> && gh pr create ...\n"
    "Five separate single-command turns for add/commit/push/pr-create were "
    "the measured pattern this guidance retires.\n")

# Issue #2262: turn-efficiency guidance. Measured (six 2026-08-24/25
# sessions, issues 2173/2186/2193/2204/2208/2240): all six died at the
# 200-turn `--max-turns` cap, and #2240's own anatomy (230 tool calls) was
# 69 grep commands, 68 of them unique — not a loop, serial one-grep-per-
# turn exploration that alone burned roughly a third of the whole budget.
# The session previously had no way to know a cap existed at all.
_TURN_BUDGET_PROSE = (
    "턴 예산(이슈 #2262): 이 세션은 --max-turns 상한 안에서 돈다(기본값 "
    f"{DEFAULT_SESSION_MAX_TURNS}, 스포너가 다르게 줬으면 "
    "$MUSTER_SESSION_MAX_TURNS_RESOLVED 로 실측치를 알 수 있다). 남은 턴이 "
    "적어지면(기본 20턴 전) 지금 이 채널로 수렴하라는 경고가 한 번 더 "
    "온다 — 그 경고가 오면 새 탐색을 시작하지 말고 커밋/PR/기록으로 "
    "수렴하라; 상한을 넘긴 뒤에도 수렴 전용의 소진 유예(wrap-up "
    "allowance)가 조금 있을 뿐, 탐색을 더 할 여유가 아니다. 측정 결과 "
    "(이슈 #2240): 캡에 걸린 세션 하나가 한 턴에 grep 하나씩 69번 실행했고 "
    "그중 68번이 서로 다른 검색이었다 — 루프가 아니라 예산을 선형으로 "
    "쓰는 직렬 탐색이 원인이었다. 이걸 줄이려면 두 가지를 같이 써라: "
    "(1) 관련된 grep 여러 개를 한 Bash 호출에 `&&`나 `|`로 묶어서 한 "
    "턴에 실행하고, 파일 전체를 여러 번 나눠 읽기(paging)보다 필요한 "
    "범위만 짚어 Read 하라. (2) 폭넓은 탐색은 Task 도구로 3-4개 병렬 "
    "Explore 형 서브에이전트에 위임하라 — foreground 배치로 한 턴에 N개 "
    "탐색을 동시에 돌리면, 직렬로 N턴을 쓰는 대신 그 턴들을 편집/검증에 "
    "남길 수 있다(운영자 지시, 이슈 #2262 코멘트: run_in_background "
    "워커는 headless 세션에서 금지 — 부모 턴이 끝나면 죽는다 — 하지만 "
    "foreground Task 배치는 된다). 마운트된 스킬은 서브에이전트에도 "
    "보인다. (3) 이슈 #2409 실측: 세션당 spawn.py 재-Read 105회, 자기 "
    "레코드 파일 재-Read 96회. spawn.py/directive_assembly.py 를 열어 "
    "프로세/env var 이름을 다시 찾지 마라 — 그 내용은 이미 "
    "`.on-the-record/directive/*.md` 로 시스템 프롬프트에 그대로 들어와 "
    "있다(이슈 #2204). 자기 레코드 파일(docs/issue-<n>/reports/<role>.md)도 "
    "Edit 직후마다 다시 Read 하지 마라 — 이미 쓴 내용은 대화 맥락에 있고 "
    "Edit 은 실패하면 에러를 낸다; 남은 섹션을 채우기 직전처럼 정말 "
    "상태를 재확인해야 할 때만 한 번 읽어라.\n")

# Issue #2409: exploratory-Bash reduction. Measured (177 sessions,
# 2026-08-25): 62% of all Bash calls are neither pytest/git/gh — grep/
# find/python3 -c probing to locate files a task touches. A single
# supported lookup (scripts/related_files.py) returns what N ad-hoc
# greps currently return: the issue's own docs/issue-<n>/ tree plus every
# code/test/spec file that already mentions the issue number, in one call.
_TASK_LOOKUP_PROSE = (
    "작업 파일 사전탐색(이슈 #2409): 이번 작업이 건드릴 파일을 찾으려고 "
    "grep/find 를 여러 번 반복하지 마라 — 177개 세션 실측에서 Bash 호출의 "
    "62%가 pytest/git/gh 가 아닌 탐색성 호출이었다. "
    "`python3 scripts/related_files.py <issue-number> [--keyword <word> "
    "...]` 를 먼저 한 번 실행하라: docs/issue-<n>/ 트리, 이슈 번호/제목을 "
    "이미 언급하는 코드·테스트·스펙 파일, (준 경우) 키워드가 들어간 파일을 "
    "한 호출로 돌려준다 — 지금까지 grep 여러 번으로 하던 일을 lookup "
    "하나로 대체한다. 이걸로도 못 찾은 파일만 개별 grep/git ls-files 로 "
    "좁혀라.\n")

# Issue #2409: hook-refusal-as-upfront-contract. Measured (177 sessions):
# 6.9 tool_result errors/session (~10% of turns), largely this repo's own
# PreToolUse gates refusing a write/command that was one shape detail off
# — the refusal is correct, but it arrives one at a time, after the fact.
# This section states the shape up front instead. Content is a direct
# summary of the real gates in on-the-record/hooks/pretooluse_dispatcher.py
# (GATES list) most likely to trip a role session's own writes/commands —
# not invented rules.
_HOOK_CONTRACT_PROSE = (
    "훅 거부 계약(이슈 #2409): 아래는 세션을 자주 막는 PreToolUse 게이트가 "
    "요구하는 형태다 — 하나씩 거부당하며 알아내지 말고 미리 맞춰라.\n"
    "1. 커밋/PR/이슈 본문에 heredoc(`$(cat <<EOF ... EOF)`)을 쓰지 마라 — "
    "역할 세션(CLAUDE_ROLE 설정됨)의 heredoc 형태 `git commit`/`gh pr "
    "create`/`gh issue create`/`gh pr comment`/`gh issue comment` 는 매번 "
    "거부된다(이슈 #1976, heredoc-command-refusal-gate.sh). 대신 "
    "`git commit -m \"title\" -m \"body\"`(두 개의 -m) 와 "
    "`gh ... --body-file <path>` 를 써라.\n"
    "2. docs/** 에 상태/결함 주장을 쓸 때는 바로 위 3줄 안에 `canonical:` "
    "또는 `derived:` 태그로 실제로 읽은 근거를 대라(record-claim-"
    "guard.sh). \"완료/동작함/PASS/충족\" 같은 결과 주장은 그 canonical: "
    "인용이 실제로 지금 실행한(executed-live) 근거여야 한다 — 파일만 읽고 "
    "요약한 인용으로는 안 된다. 백틱으로 인용한 경로는 git 에 커밋된 "
    "경로여야 하고(작업 트리에만 있는 파일은 거부), 개수만 대는 주장에는 "
    "그 개수를 어떻게 셌는지 근거가 필요하다.\n"
    "3. `acceptance:`/`live-fire:` 로 인용한 명령·결과는 지금 다시 실행한 "
    "결과와 일치해야 한다(acceptance-command-real-run-guard.sh, "
    "live-fire-claim-real-run-guard.sh) — 과거 실행 결과를 재사용해 적으면 "
    "거부된다.\n"
    "4. docs/specs/* 를 건드리는 커밋은 같은 커밋 안에서 "
    "`python3 gates/spec_index.py --update` 를 먼저 돌려 "
    "reconciled-index.md 를 갱신해야 한다(spec-index-preflight.sh).\n"
    "5. 새 gate/hook 스크립트를 스테이징하면 "
    "docs/specs/enforcement-boundary.md(on-the-record/hooks/*.sh 라면 "
    "generated-paths.md 도)에 매칭되는 행이 있어야 한다"
    "(gate-registration-guard.sh).\n"
    "6. CORE_BUILD_NOW=1 세션은 phase-2 승인 게이트(approval-gate.sh, "
    "pr-preflight.sh)가 이미 우회되어 있다 — APPROVE 코멘트를 따로 만들 "
    "필요 없다.\n")

# Issue #2185: measured cost — spawned sessions run `find` (including
# unscoped `find /` whole-tree traversals) to locate files whose path they
# don't already know, burning tens of seconds per spawn (58s single gap on
# the issue's fixture measurement). `git ls-files` covers the repo-local
# case: faster, respects .gitignore, no full traversal.
_REPO_DISCOVERY_PROSE = (
    "저장소 파일 탐색(이슈 #2185): 이름은 알지만 정확한 경로를 모르는 "
    "파일/디렉토리를 찾을 때는 `find`(특히 `find /`처럼 저장소 밖이나 "
    "전체 트리를 훑는 호출)보다 `git ls-files`를 먼저 써라 — .gitignore "
    "를 존중하고 훨씬 빠르다. 예: `git ls-files | grep -i readme`, "
    "`git ls-files docs/ test/`. 위 디렉티브 인덱스에 이미 전체 경로가 "
    "적힌 파일은 다시 찾지 말고 그 경로 그대로 Read 하라.\n")

# Issue #2211: #2185's `git ls-files` guidance only covers the repo the
# session is IN — it says nothing about where the on-the-record plugin
# checkout, core plugin, skill-repository, or sibling role workspaces are
# installed. Measured (issue-2201 session, 2026-08-24): a session that
# needed exactly those four burned 126s on unscoped `find /` /
# `find /home` scans because it had no other way to learn the paths. The
# spawner already knows them at spawn time (`spawn_cmd()`, issue #2211) —
# this section tells the session they exist as env vars instead of a
# filesystem search.
_KNOWN_PATHS_PROSE = (
    "알려진 경로 환경변수(이슈 #2211): 저장소 밖 경로를 찾을 때 `find /`나 "
    "`find /home`으로 전체 파일시스템을 훑지 마라 — 스포너가 스폰 시점에 "
    "이미 아는 경로 넷을 env var 로 심어 뒀다. `$ON_THE_RECORD`(on-the-record "
    "플러그인 체크아웃 루트 — 훅 스크립트, harness fixture 템플릿이 여기 "
    "있다), `$CLAUDE_PLUGIN_ROOT_CORE`(core 플러그인 루트), "
    "`$MUSTER_WORKSPACE_ROOT`(역할 워크스페이스들의 루트 — 다른 세션의 "
    "작업 디렉토리나 상태 파일을 찾을 때 이 아래를 `ls`/`git ls-files`로 "
    "좁혀라), `$MUSTER_SKILL_REGISTRY_ROOT`(skill-repository 체크아웃 — "
    "마운트된 skill-repository 가 없으면 이 변수 자체가 없다, 빈 문자열이 "
    "아니라 unset). 넷 다 `printenv`로 바로 읽을 수 있다.\n")

# Issue #2479: record-claim-guard.sh and heredoc-command-refusal-gate.sh
# used to be learned only from their own refusal message, mid-session —
# observed live (issue-2379 conformance-review session): a PR was already
# open when a follow-up commit hit both gates back-to-back and the session
# ended `progressed-dirty-tree`, unable to close out its own commit; a
# watchdog then respawned it from scratch as if it were dead. Neither
# gate's refusal logic changes here — this only tells the passing shape
# up front, before the first write that could trip either one.
#
# Item 3 (issue #2508): pr-preflight.sh's phase-2 linkage requirement used
# to force a session delivering a deliberate partial into a false `Closes`
# claim — observed live on PR #2495 (issue #2289), where the session added
# the trailer and then had to invent its own disclosure paragraph stating
# the trailer was false. pr-preflight.sh's mechanism now accepts a
# non-closing `Advances`/`Part of` trailer for exactly this case; this
# item states the choice up front so the next partial-delivery session
# picks the right trailer instead of reaching for Closes-plus-disclaimer.
_HOOK_CONTRACT_PROSE = (
    "게이트 통과 모양(이슈 #2479): 아래 게이트들은 거절되면 커밋을 못 "
    "닫은 채 PR 만 열려 있는 상태로 좌초할 수 있다(progressed-dirty-"
    "tree) — 거절을 겪고 나서 배우지 말고 첫 시도부터 이 모양을 써라. "
    "두 게이트의 거절 로직 자체는 안 바뀐다, 더 일찍 알려줄 뿐이다.\n"
    "\n"
    "1. record-claim-guard.sh (docs/issue-*/reports/** 아래 모든 Write/"
    "Edit/MultiEdit): 각 주장이 속한 markdown 섹션(가장 가까운 헤딩 "
    "사이) 안에서 아래를 만족해야 한다.\n"
    "   - `unverifiable:` 줄과 `checked: ... — result: unverifiable` 줄은 "
    "반드시 콜론 뒤에 이유를 붙인다.\n"
    "   - \"N of M\"/\"N개\" 같은 bare count 주장은 `derived: <명령어>` "
    "나 코드펜스 재현이 있어야 한다.\n"
    "   - 백틱 경로는 작업 트리에 실제로 존재하고 git 이력에 커밋된 적이 "
    "있어야 한다(자기 자신의 레코드 파일은 예외).\n"
    "   - role output / session·PR·board 상태 / 결함 주장은 같은 섹션 "
    "안에 `canonical: <실제로 읽은 것>` 또는 `derived: <명령어>` 태그가 "
    "있어야 한다 — 요약·grep 신호만으로는 부족하다.\n"
    "   - \"requirement met\"/\"done\"/\"PASS\"/\"complete\" 류의 OUTCOME "
    "주장은 그 `canonical:`/`derived:` 태그 자체가 실행-라이브 참조여야 "
    "한다(명령어 문자열, 또는 `acceptance: <명령어> — result: ...` 줄) — "
    "파일을 읽었다는 인용만으로는 부족하다.\n"
    "   - 결함/근본원인 주장은 인용한 file:line 범위를 3줄 이상 그대로 "
    "코드펜스로 뜨거나 `derived: <명령어>` 재현이 있어야 한다 — grep/"
    "키워드 히트만으로는 부족하다.\n"
    "   worked example (한 섹션 안에서 canonical/outcome 규칙을 동시에 "
    "만족, record-claim-guard.sh 통과 확인됨):\n"
    "   ```\n"
    "   canonical: `gh pr view 2471` output (state: OPEN)\n"
    "   Acceptance requirement met — checked: `python3 -m pytest "
    "tests/test_x.py` — result: 12 passed\n"
    "   ```\n"
    "\n"
    "2. heredoc-command-refusal-gate.sh (역할 세션의 모든 Bash 호출): "
    "`git commit`/`gh issue|pr create`/`gh issue|pr comment` 명령에 `<<` "
    "헤어독 리다이렉션이 하나라도 있으면 통째로 거절된다 — 커밋 메시지나 "
    "--body 를 절대 heredoc(`$(cat <<EOF ... EOF)`)으로 만들지 마라.\n"
    "   - `git commit`: `-m` 두 개로 나눠라 — `git commit -m \"<제목 "
    "줄>\" -m \"<본문 줄>\"` (문단마다 -m 하나).\n"
    "   - `gh issue|pr create`/`gh issue|pr comment`: 본문을 파일로 먼저 "
    "쓰고 `--body-file <path>` 를 써라 — `--body \"$(...)\"` 금지.\n"
    "   worked example (heredoc-command-refusal-gate.sh 통과 확인됨):\n"
    "   ```\n"
    "   git commit -m \"issue-2479: add gate passing-shape to spawn "
    "directive\" -m \"fixes progressed-dirty-tree stall from undocumented "
    "gate shape\"\n"
    "   ```\n"
    "\n"
    "3. pr-preflight.sh (이슈 #2508, `gh pr create`/`gh pr edit` on a "
    "phase-2 delivery PR): 이슈를 실제로 완결하면 지금처럼 "
    "`Closes`/`Fixes`/`Resolves #<n>`을 쓴다. 의도적 partial delivery라서 "
    "이 PR이 이슈를 닫으면 안 될 때는 `Advances #<n>` 또는 `Part of #<n>`을 "
    "대신 쓴다 — 게이트는 이 형태도 링크 요건을 만족한 것으로 받아들이고, "
    "머지돼도 이슈를 자동으로 닫지 않는다. 어느 쪽도 없으면(이슈 참조 "
    "자체가 없으면) 여전히 거절된다. 트레일러를 고르는 것은 세션 자신의 "
    "판단이다 — Closes를 써 놓고 본문에 \"사실 안 닫혔다\"는 disclaimer "
    "문단을 따로 지어낼 필요가 없다.\n"
    "   worked example (partial delivery, pr-preflight.sh 통과 확인됨):\n"
    "   ```\n"
    "   Advances #2289\n"
    "   ```\n")

# Issue #2527: measured live (issue-2516 implementation session,
# 2026-08-26, 11.2 min total): the record-to-PR phase alone cost 28% of
# the session's wall clock. The record's first write landed at +6.9 min,
# 2.9 minutes BEFORE the first code Edit/Write at +9.8 min — the record
# was written with nothing yet done to cite, so all 5 record-claim-guard
# refusals in that session fell inside that 3-minute window. After the
# first write, the record was assembled across 11 separate Write/Edit
# calls, each one re-entering record-claim-guard.sh from scratch, plus 9
# redundant git diff/status/log calls re-checking what the session had
# just done. Guidance only — record-claim-guard.sh's refusal logic does
# not change; the fix is arriving at the record with citable results
# already in hand, never accepting less from the gate.
_RECORD_ORDER_PROSE = (
    "\nRecord ordering (issue #2527, guidance only — no gate; does NOT "
    "loosen record-claim-guard.sh or any citation gate): change the code, "
    "run the acceptance checks, THEN write the record from those executed "
    "results — never the reverse. A record written before the code exists "
    "has nothing to cite yet, and every Write/Edit under "
    "docs/issue-*/reports/** re-enters record-claim-guard.sh — an uncited "
    "number there is refused on the spot. Measured live (issue-2516 "
    "implementation session, 2026-08-26): the record's first write landed "
    "3 minutes before the first code edit, and all 5 refusals that session "
    "hit fell inside that window.\n"
    "Assemble the record ONCE, after the checks have run, from the "
    "finished results — not grown across many small edits as you go. Each "
    "Write/Edit is a separate gate entry; the same session wrote its "
    "record in 11 separate pieces, each one re-checked from scratch, plus "
    "9 redundant git diff/status/log calls re-inspecting work already "
    "done. One assembled write with the executed evidence already in hand "
    "passes once instead of eleven times.\n"
    "This batching covers the record's RESULT content only — it does NOT "
    "defer deviation logging. A deviation (a scope-exceeded stop, an "
    "alternative swap from the approved proposal, something you wrote and "
    "then undid or replaced, something you expected to hold that did "
    "not) is still appended to `## What did not work` / `## Rationale for "
    "deviations` the moment it happens, per the warrant and record-shape "
    "directives — never saved up for the single end-of-session record "
    "write.\n")

# Moved verbatim: the mounted-skill inspection nudge (issue #1960 phase B)
# + invoke-before-apply (issue #2062).
_SKILL_CHECK_PROSE = (
    "스킬 점검(이슈 #1960): 실체 작업을 시작하기 전에, 위에 "
    "마운트된 스킬 목록을 이번 과제와 대조하라. trigger 조건이 "
    "이번 과제에 그럴듯하게 들어맞는 스킬이 있으면 Skill 도구로 "
    "호출하고, 없으면 검토했다는 사실만 유념하고 넘어가라. "
    "invoke-before-apply(이슈 #2062): APPLICABLE 로 판단한 "
    "스킬은 적용하기 전에 반드시 Skill 도구로 그 스킬의 전체 "
    "SKILL.md 를 로드해야 한다 — not-applicable 로 판단한 "
    "스킬은 이 의무에서 면제된다(강제 로드도, 토큰 낭비도 "
    "없다).\n")

# Moved verbatim: the per-mounted-skill verdict obligation (issue #2039,
# invocation marker per issue #2062, scoped to invoked skills only per
# issue #2153).
_SKILL_VERDICT_PROSE = (
    "스킬-verdict 의무(이슈 #2039) — 대상 범위는 이슈 #2153 갱신: 위에 "
    "마운트된 스킬 중 이번 세션에서 실제로 Skill 도구로 호출한 스킬 "
    "이름마다, 레코드에 `skill-verdict: <스킬명> — applied: "
    "<어디서/어떻게> | not-applicable: <한 줄 이유>` 형태의 줄을 "
    "정확히 하나씩 남겨야 한다 — 적용 여부 판단은 전적으로 이 "
    "세션의 몫이지만, 그 판단을 아예 안 밝히는 것은 더 이상 "
    "허용되지 않는다. 마운트만 되고 호출하지 않은 스킬은 이 줄이 "
    "필요 없다 — 선택적으로 요약 한 줄만 남겨도 된다: "
    "`other mounted skills: not triggered`. applied: 줄은 위 "
    "invoke-before-apply 의무에 따라 실제로 Skill 도구를 호출했다는 "
    "증거로 `invoked;` 를 자유 텍스트 맨 앞에 붙여야 한다(이슈 "
    "#2062) — not-applicable: 줄은 이 마커가 필요 없다.\n")


# Issue #2227 (REQ-10, carried forward from #2204's unaddressed `## Fix`
# bullet 2): `known-paths.md` covers cross-repo/plugin/sibling-workspace
# path discovery ($ON_THE_RECORD, $CLAUDE_PLUGIN_ROOT_CORE,
# $MUSTER_WORKSPACE_ROOT, $MUSTER_SKILL_REGISTRY_ROOT). This used to be
# scoped per-role via `write_scope` (only `implementation` reached the
# code/test buckets the role-handoff contract's Layout line names) — issue
# #2559 removed `write_scope` outright (sessions are not scope-limited, so
# every role can touch code/test now), which retired that classifier along
# with it. `code_scoped` stays a plain kwarg below, defaulting True (the
# safe, over-inclusive bundle) for every caller.
def directive_section_files(*, skills_mounted: bool = False,
                            checkpoint_block: str | None = None,
                            code_scoped: bool = True) -> dict[str, str]:
    """The on-demand section files for one spawn: name -> full prose.

    `completion-and-landing.md`, `repo-discovery.md`, `turn-budget.md`,
    `hook-contract.md`, and `record-order.md` are always materialized —
    the invariant baseline every task gets regardless of path scope
    (Acceptance 'empty state': never an empty directive). `hook-contract.md`
    (issue #2479) is unconditional because both gates it documents fire
    for every role: record-claim-guard.sh on any docs/issue-*/reports/**
    write, heredoc-command-refusal-gate.sh on any role-session commit/PR
    Bash call. `record-order.md` (issue #2527) is unconditional for the
    same reason: every role writes its own record through
    record-claim-guard.sh, so the code-then-checks-then-record ordering
    and single-assembly guidance apply regardless of scope.
    `known-paths.md` and `task-lookup.md` (issue #2409) are
    scoped to `code_scoped` callers (issue #2227 REQ-10); the skill and
    checkpoint sections only when their own condition holds. Default
    `code_scoped=True` keeps every caller that does not pass the kwarg on
    today's full bundle — the safe, over-inclusive default, never a
    narrower directive than before by omission (issue #2559 retired the
    only caller that ever passed `code_scoped=False`, so every spawn gets
    the full bundle today)."""
    files = {"completion-and-landing.md":
             _COMPLETION_PROSE + _LANDING_BATCHING_PROSE,
             "repo-discovery.md": _REPO_DISCOVERY_PROSE,
             "hook-contract.md": _HOOK_CONTRACT_PROSE,
             "record-order.md": _RECORD_ORDER_PROSE}
    if code_scoped:
        files["known-paths.md"] = _KNOWN_PATHS_PROSE
        files["task-lookup.md"] = _TASK_LOOKUP_PROSE
    files["turn-budget.md"] = _TURN_BUDGET_PROSE
    files["hook-contract.md"] = _HOOK_CONTRACT_PROSE
    if skills_mounted:
        files["skill-obligations.md"] = (_SKILL_CHECK_PROSE + "\n"
                                          + _SKILL_VERDICT_PROSE)
    if checkpoint_block:
        files["checkpoint-mode.md"] = checkpoint_block
    return files


def materialize_directive_sections(cwd: str, files: dict[str, str]) -> None:
    """Write the section files into `<cwd>/.on-the-record/directive/`."""
    d = Path(cwd) / ".on-the-record" / "directive"
    d.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (d / name).write_text(text, encoding="utf-8")


# Issue #2204: platform-native injection for the on-demand section files.
# `directive_section_files()` used to be paired with an inline "Read <file>
# when <condition>" pointer in the stdin task text (issue #2135's design) —
# a live-spawn session log showed sessions read every pointed-at file
# sequentially before their first task action (~46s), because "read it
# when the condition holds" reads, in practice, as "read it now to be
# safe." The section files are still materialized into the workspace
# (`materialize_directive_sections()`, unchanged — a durable, inspectable
# copy), but their content also rides `--append-system-prompt`
# (`spawn_cmd(..., append_system_prompt=...)`) so it is already in the
# session's context at turn 1 — no Read tool call, no round trip.
def _directive_system_prompt_block(files: dict[str, str]) -> str:
    """Join the on-demand section files' full prose for
    `--append-system-prompt`. Empty input (adhoc spawns, which keep the
    full prose inline in `task` instead — no workspace to materialize
    into) returns "" so `spawn_cmd()` adds no flag, byte-identical to a
    pre-#2204 spawn."""
    if not files:
        return ""
    return "\n\n".join(f"# {name}\n\n{body}" for name, body in files.items())


# Issue #2135 item 3: record skeleton pre-generation. The session fills
# judgment content instead of authoring structure. The skeleton satisfies
# core's record-fields-gate structure checks as it stands: what-was-done /
# why / upstream-basis headings, a `loop_state:` line (non-terminal, so the
# next-steps + resolution-path spellings are present too), an open-findings
# heading, and a value-less `sha:` frontmatter line (the gate's issue-153 F2
# carve-out — never a placeholder string, which the gate denies).
_RECORD_SKELETON = """\
---
issue: {issue}
role: {role}
{author_line}loop_state: {loop_state}
upstream:
  - path: <docs/issue-{issue}/... or code path this record builds on>
    sha:
---

# issue-{issue} — {role} record

## What was done

<!-- fill: the delivered work, concretely -->

## Why

<!-- fill: rationale for the approach taken -->

## Upstream basis

<!-- fill: the concrete upstream inputs (docs/issue-{issue}/ paths or commit
shas); per contract §1, frontmatter `sha:` is `same-commit` when the cited
path lands in this same commit, else the real 40-char sha -->

## Open findings

<!-- fill: each open finding with its resolution path, or "none" -->

## Next steps

<!-- fill while loop_state is non-terminal; set loop_state to the terminal
value for this record kind when done -->
"""


def _stamp_additive_record_fields(issue: int, role: str,
                                   skill_sources: list | None = None) -> str:
    """Issue #2241 stage 1 (Accumulation note in the stage-1 proposal): the
    single call site every additive record-field stamp goes through —
    `author:` today; a later stage's new stamped field extends this same
    helper rather than adding another inline write in
    `write_record_skeleton`. `author:` is the session's stable identity —
    not the lease key, which expires and renews
    (docs/decisions/2026-08-25-retire-role-axis-staging.md Option D
    explains why those stay separate fields). Roles are still fully in
    place at this stage, so the only session-scoped identity available is
    the role itself; a later stage may widen what populates this line
    once a non-role-shaped identity axis exists. Returns a trailing-
    newline-terminated frontmatter block, written once at skeleton
    creation — `write_record_skeleton` already refuses to touch a record
    file that exists, so a respawn into the same workspace can never
    rewrite a prior session's stamped lines (append-only).

    Issue #2579: when `--skills` mounted at least one skill, a second
    stamped line names which of the four sources each one actually
    resolved from (`_sp._describe_skill_match()` — the same one-line
    description already used in the task-injected "마운트된 스킬" text,
    issue #1742/#1774) — a record naming only the skill, never its
    source, cannot be re-judged later once resolution order changes.
    Omitted entirely when no `--skills` were mounted (empty-state:
    byte-identical to before this issue)."""
    line = f"author: {role}\n"
    if skill_sources:
        detail = ", ".join(f"{m['name']} ({_sp._describe_skill_match(m)})"
                            for m in skill_sources)
        line += f"skills: {detail}\n"
    return line


_CODE_EXTENSION_RE = re.compile(
    r"\.(?:py|js|jsx|ts|tsx|go|rs|java|kt|rb|c|cc|cpp|h|hpp|cs|php|sh|sql)\b")


def write_record_skeleton(cwd: str, issue: int, role: str,
                           task_text: str = "",
                           skill_sources: list | None = None) -> Path | None:
    """Pre-write the role's own record skeleton at bootstrap; never
    overwrite an existing record (a respawn into the same workspace)."""
    p = Path(cwd) / "docs" / f"issue-{issue}" / "reports" / f"{role}.md"
    if p.exists():
        return None
    # Initial loop_state: the role's own record_fields enum is authoritative
    # (record_lint treats an out-of-enum value as a violation) — prefer
    # `in-progress` when the enum carries it, else the enum's first value.
    loop_state = "in-progress"
    try:
        enum = (_sp.role_data().get(role, {})
                .get("record_fields", {}).get("loop_state"))
        if isinstance(enum, dict):
            # grouped shape {progress: [...], terminal: [...], ...} —
            # prefer the progress group's first value
            flat = [v for vs in enum.values() for v in vs]
            if "in-progress" not in flat:
                loop_state = (enum.get("progress") or [flat[0]])[0]
        elif enum and "in-progress" not in enum:
            loop_state = enum[0]
    except Exception:
        pass
    # roles/specs/<role>.spec.json required_fields become empty frontmatter
    # keys (with the enum as a YAML comment) so the session fills values,
    # not structure — observed in the first post-diet run: without these the
    # session spent turns excavating git history for a prior record's shape.
    #
    # issue-2190: for the two roles record-fields-gate.sh special-cases
    # (coding, implementation), the spec's raw `commit_sha` field name never
    # appears in an actual record — the gate checks `code_under_review:`
    # instead (a file-list citation, not a bare sha; see
    # docs/issue-100/decisions/2026-08-03-record-citation-format-and-kind-
    # convention.md), and `breaking:` is universal delivery-record practice
    # despite being marked optional in the spec. Emitting the spec's field
    # names unrenamed left the session to re-derive both the rename and the
    # optional-but-always-present field on every run (measured: docs/issue-45
    # fixture, ~37s of thinking before converging on `code_under_review:` +
    # `breaking:` across three Edit passes).
    # issue #2575: `role` is a free-form slug under slug identity (#2555)
    # and is never validated against a closed role set any more (#2555/
    # #2560/#2561) — a literal name match against a fixed tuple can no
    # longer answer "is this a code-producing session" (it never matches
    # any real slug, e.g. this very session's own
    # "silent-failure-audit+diagnose-first-a9ef3af5"). No structural
    # per-session signal survives slugs here either: `role_data()` only
    # covers the closed set of legacy role names (so a spec-content check
    # would be permanently False for exactly the slug sessions this issue
    # is about), mounted skills carry no code-vs-doc metadata, and no
    # CLI flag/roster field declares "this session produces code"
    # (investigated this session — none of `spawn.py`'s `add_argument`
    # calls or `roster.py`'s roster-entry fields carry one). The
    # task-composed-skills axis's only available proxy at this call site
    # is the session's own pristine spawn task text (`task_text`, the
    # `spawn.py` caller's `_cross_family_task_text` — read before any
    # skill-mounting mutation, same pristine-text precedent that axis
    # already uses for cross-family skill matching): a task that names
    # code-file paths is code work regardless of what the session ends up
    # being named. Heuristic, not exact — a task that only *reads* code
    # files for a doc-only deliverable can still false-positive; accepted
    # because no better structural signal exists (see this issue's own
    # record for the investigation this rules out).
    is_coding = bool(_CODE_EXTENSION_RE.search(task_text or ""))
    spec_lines = ""
    try:
        spec = _sp.role_data().get(role, {}).get("record_spec") or {}
        for fld in spec.get("required_fields", []):
            name = fld.get("name")
            if name == "loop_state":
                continue
            if not fld.get("required") and not (is_coding and name == "breaking"):
                continue
            if is_coding and name == "commit_sha":
                spec_lines += "code_under_review:\n  - PLACEHOLDER: path/to/file\n"
                continue
            enum = fld.get("enum")
            hint = " # one of: %s" % "|".join(enum) if enum else \
                   " # %s" % fld.get("type", "fill")
            spec_lines += "%s:%s\n" % (name, hint)
    except Exception:
        pass
    body = _RECORD_SKELETON.format(
        issue=issue, role=role, loop_state=loop_state,
        author_line=_stamp_additive_record_fields(issue, role, skill_sources))
    if spec_lines:
        body = body.replace("sha:\n---\n", "sha:\n" + spec_lines + "---\n", 1)
    if is_coding:
        body = body.replace(
            "\n## Upstream basis\n",
            "\n## What did not work\n\nNone.\n\n## Upstream basis\n", 1)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def composition_breakdown(parts: list[tuple[str, str]]) -> str:
    """One-line byte breakdown of the assembled directive by source —
    issue #2135's measure-first instrument, printed at every spawn."""
    total = sum(len(t.encode("utf-8")) for _, t in parts)
    cells = ", ".join(f"{label}={len(text.encode('utf-8'))}B"
                      for label, text in parts if text)
    return f"directive composition: total={total}B ({cells})"


_SKILL_USE_SENTENCE_RE = re.compile(r"(Use\b[^.]*\.)", re.S)


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset({"a", "the", "use", "when", "or", "and", "is", "an"})
# 이슈 #2040: raw-overlap 시절의 고정 임계값(_CROSS_FAMILY_MIN_OVERLAP=2)은
# BM25 점수 스케일로 옮겨오지 않는다 — score > 0 (질의-문서 토큰이 하나라도
# 겹치면 IDF 가중치가 붙어 양수) 를 바닥으로 쓴다. 재현: 16쌍 리플레이에서
# conformance-review-severity-classification 이 16/16 -> 7/16 로, model-routing
# 은 5/16 -> 5/16 로 남았다(docs/issue-2040/reports/implementation/survey.md
# BM25 spike, floor=score>0 그대로 재사용) — 그 잔여 오탐(모두 model-routing
# 류의 "의도적으로 광범위한" 트리거)을 걷어내는 건 임계값 조정이 아니라
# consult-judge 단계의 몫이다(제안서 Rationale).
_BM25_K1 = 1.5
_BM25_B = 0.75
_CROSS_FAMILY_CONSULT_TOPN = 8  # 이슈 본문: consult 에 넘기는 BM25 상위 후보 수


def _bm25_cross_family_scores(task_text: str, role: str,
                               repo_root: Path | None,
                               home: Path | None = None,
                               target_repo_root: Path | None = None
                               ) -> list[tuple[float, str, Path, str]]:
    """`task_text` 를 질의로, 역할의 family 밖 스킬 각각의 BM25 문서
    (`_skill_bm25_document()` — description 전문 + 이름 토큰 + metadata.axis,
    이슈 #2124 part 1; 예전에는 "Use ..." 트리거 문장 한 개)를 문서로 삼아
    Okapi BM25(k1=1.5, b=0.75, 표준 기본값)로 채점한다
    — 트리거 문장은 집합으로 토큰화되므로 문서 내 항 빈도(f)는 항상 1
    (존재/부재만 본다, 트리거 문장 반복 서술 여부에 좌우되지 않기 위함).
    score > 0(질의와 최소 한 토큰 겹침) 인 것만 이름 오름차순 타이브레이크로
    내림차순 정렬해 돌려준다 — floor 근거는 위 상수 주석.

    이슈 #2055: 후보 코퍼스는 `_cross_family_candidate_corpus()` 가 네 소스에
    걸쳐 해석한다 — 각 행이 source 라벨을 달고 나온다(반환 튜플의 4번째
    자리). `home`/`target_repo_root` 를 생략하면(오늘의 호출부 호환)
    각각 `Path.home()`, 빈 tier 로 취급된다."""
    query_tokens = _sp._tokenize(task_text)
    if not query_tokens:
        return []
    corpus = _sp._cross_family_candidate_corpus(role, repo_root, home, target_repo_root)
    docs: list[tuple[str, Path, str, set[str]]] = []
    for name, d, source in corpus:
        # 이슈 #2124 part 1: 문서 = description 전문 + 이름 토큰 + metadata.axis
        # (예전에는 첫 "Use ..." 트리거 문장 한 개만 색인했다 — dicequest
        # #72 골드 케이스에서 Recall@8=0 을 만든 empty-state).
        doc = _sp._skill_bm25_document(name, d)
        toks = _sp._tokenize(doc)
        if not toks:
            continue
        docs.append((name, d, source, toks))
    if not docs:
        return []
    n = len(docs)
    avgdl = sum(len(toks) for _, _, _, toks in docs) / n
    df: dict[str, int] = {}
    for _, _, _, toks in docs:
        for t in toks:
            df[t] = df.get(t, 0) + 1
    scored: list[tuple[float, str, Path, str]] = []
    for name, d, source, toks in docs:
        dl = len(toks) or 1
        score = 0.0
        for t in query_tokens:
            if t not in toks:
                continue
            idf = math.log((n - df[t] + 0.5) / (df[t] + 0.5) + 1)
            score += idf * (_BM25_K1 + 1) / (1 + _BM25_K1 * (1 - _BM25_B + _BM25_B * dl / avgdl))
        if score > 0:
            scored.append((score, name, d, source))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return scored


def _cross_family_skill_matches(task_text: str, role: str,
                                 repo_root: Path | None,
                                 k: int = 2,
                                 home: Path | None = None,
                                 target_repo_root: Path | None = None) -> list[Path]:
    """BM25 프리필터의 상위 k 개(이슈 #2040 — 예전 raw-overlap 채점을
    대체, 호출부/시그니처는 그대로다). consult-judge 단계 없이 이 함수
    단독으로도 오늘의 fail-open 경로(자문 에러시 이 함수의 top-k)와
    동일한 모양을 낸다."""
    scored = _sp._bm25_cross_family_scores(task_text, role, repo_root, home, target_repo_root)
    return [d for _, _, d, _ in scored[:k]]


