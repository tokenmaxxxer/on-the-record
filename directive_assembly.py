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
    "--role {role}\n"
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
        f"await-approval --issue {issue} --role {role}\n"
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
    "보인다.\n")

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
# $MUSTER_WORKSPACE_ROOT, $MUSTER_SKILL_REGISTRY_ROOT) — a concern that
# only arises for a role whose write_scope reaches the code/test buckets
# the role-handoff contract's own Layout line names ("code src/, tests
# test/, docs/ six buckets"). Of the 44 `roles/*.json` specs, only
# `implementation` (`write_scope: ["src/**", "test/**", "tests/**"]`)
# does; the other 43 are report-only (`docs/issue-<n>/reports/<role>.md`,
# `docs/decisions/*.md`, `CHANGELOG.md`, `design-tokens/*.json` — none
# under src/**|test/**|tests/**) — their whole task IS that one file, no
# sibling-workspace/plugin-path lookup in their task shape (several
# roles' own JSON even say so: "implementation의 write_scope가 이미 이
# 도메인을 inline으로 커버"). This reuses `write_scope`, already-declared
# per-role data the gates (`gates/gates.py::role_scope`) already enforce
# post-hoc — no new classifier, no new field.
def _role_touches_code(write_scope: list) -> bool:
    """True when a role's write_scope reaches src/**, test/**, or
    tests/** — the code/test buckets, not the docs-only report path
    every role's write_scope carries by default."""
    return any(g.startswith(("src/", "test/", "tests/"))
               for g in write_scope)


def directive_section_files(*, skills_mounted: bool = False,
                            checkpoint_block: str | None = None,
                            code_scoped: bool = True) -> dict[str, str]:
    """The on-demand section files for one spawn: name -> full prose.

    `completion-and-landing.md`, `repo-discovery.md`, and
    `turn-budget.md` are always materialized — the invariant baseline
    every task gets regardless of path scope (Acceptance 'empty state':
    never an empty directive). `known-paths.md` is scoped to
    `code_scoped` callers (issue #2227 REQ-10, see `_role_touches_code()`
    above); the skill and checkpoint sections only when their own
    condition holds. Default `code_scoped=True` keeps every caller that
    does not pass the kwarg (adhoc spawns with no role write_scope to
    check) on today's full bundle — the safe, over-inclusive default,
    never a narrower directive than before by omission."""
    files = {"completion-and-landing.md":
             _COMPLETION_PROSE + _LANDING_BATCHING_PROSE,
             "repo-discovery.md": _REPO_DISCOVERY_PROSE}
    if code_scoped:
        files["known-paths.md"] = _KNOWN_PATHS_PROSE
    files["turn-budget.md"] = _TURN_BUDGET_PROSE
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


def _stamp_additive_record_fields(issue: int, role: str) -> str:
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
    newline-terminated frontmatter line, written once at skeleton
    creation — `write_record_skeleton` already refuses to touch a record
    file that exists, so a respawn into the same workspace can never
    rewrite a prior session's `author:` line (append-only)."""
    return f"author: {role}\n"


def write_record_skeleton(cwd: str, issue: int, role: str) -> Path | None:
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
        enum = (_sp.json.loads((_sp.ROOT / "roles" / f"{role}.json")
                           .read_text(encoding="utf-8"))
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
    is_coding = role in ("coding", "implementation")
    spec_lines = ""
    try:
        spec = _sp.json.loads((_sp.ROOT / "roles" / "specs" / f"{role}.spec.json")
                          .read_text(encoding="utf-8"))
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
    body = _RECORD_SKELETON.format(issue=issue, role=role,
                                   loop_state=loop_state,
                                   author_line=_stamp_additive_record_fields(issue, role))
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


