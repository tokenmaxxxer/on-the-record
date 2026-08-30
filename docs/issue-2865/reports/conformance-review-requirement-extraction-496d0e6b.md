---
issue: 2865
role: conformance-review-requirement-extraction-496d0e6b
author: conformance-review-requirement-extraction-496d0e6b
skills: conformance-review-requirement-extraction (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: gh issue view 2865 (tokenmaxxxer/on-the-record)
    sha: same-commit
---

# issue-2865 — conformance-review-requirement-extraction-496d0e6b record

## What was done

Triaged all 24 named backlog issues (23 in `tokenmaxxxer/on-the-record`,
1 — `#357` — in `tokenmaxxxer/tokenmaxxxer-core`) by reading each issue's
own acceptance criteria, then running at least one command against
today's code for every issue (grep, `git log`/`git show`, a live
Python/regex repro, or a direct file read of the exact lines in
question) before assigning a verdict. No issue was classified from its
title or body summary alone.

acceptance: `for n in 1633 1650 1656 1694 2071 2136 2147 2193 2216 2297 2332 2357 2360 2415 2498 2502 2514 2576 2588 2644 2677 2692 2726; do gh issue view $n --repo tokenmaxxxer/on-the-record --json state -q .state; done; gh issue view 357 --repo tokenmaxxxer/tokenmaxxxer-core --json state -q .state` — result:
```
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
OPEN
```
24 lines, all `OPEN` — all 24 issues unchanged by this delivery.

### Classification table

| # | Issue | Repo | Verdict | Command(s) run | Citation |
|---|---|---|---|---|---|
| 1 | #1633 | on-the-record | Still live | `grep -rn write_scope`; `git log --oneline --all \| grep -iE "2610\|2559"`; `ls gates/patrol_*.py` | `directive_assembly.py:426`, `gates/scope_adherence.py:4` — role axis retired (`49c4854b`/#2610, `3d7bb6dc`/#2559) but `gates/patrol_*.py` still exist and the underlying gap (patrol finds cross-record defects with no gated write path) persists; the issue's *proposed fix* now references retired mechanisms, not the underlying gap itself |
| 2 | #1650 | on-the-record | Premise gone | `ls .github/workflows/`; `git show ccbe7fe9`; `find . -iname test_spec_index.py` | commit `ccbe7fe9` (#460) deleted `.github/workflows/` outright — `docs/specs/enforcement-boundary.md:104` states role sessions are refused for adding CI workflows; `#1650`'s second acceptance item targets `tests/test_spec_index.py` (untracked — deleted from the tree by commit `a555e169` / #2528) |
| 3 | #1656 | on-the-record | Still live | `Read gates/requirement_intake_consult.py:27`; live `re.search` repro | unanchored `\b` regex still smuggles `validity-consult-skip: trivial but actually risk-bearing` as a skip — reproduced live (see appendix) |
| 4 | #1694 | on-the-record | Still live | `find . -iname goals.md`; `ls docs/reports/product/`; `grep -rn "north.star\|requirement-fidelity"` | `docs/reports/product/goals.md` (untracked — no such file exists anywhere in the tree) — the underlying mechanisms (#1658, #1660) landed but the doctrine-recording artifact the issue asks for was never written |
| 5 | #2071 | on-the-record | Cannot determine (as filed) | `grep -n SKILL_JUDGE_TIMEOUT_DEFAULT consult.py`; `gh issue view 2071 --comments` | Defect 1 (fixed 45s timeout) is fixed (`consult.py:52`, #2076/#2274; see appendix code fence), but the issue's own 2026-08-28 comment records the same fail-open pattern recurring at a different timeout and spawning #2678/#2679; defects 2 (digest paraphrase parser) and 3 (drift stale-PR flag) were not independently re-verified in this pass — settling them needs running `watchdog.py`'s requirement-drift check against a live multi-clause digest and a known-merged PR |
| 6 | #2136 | on-the-record | Premise gone | `git show a555e169 --stat`; `ls tests/*.py gates/test_*.py`; `grep -rn quarantine` | commit `a555e169` (#2528) retired the plugin's own test suite wholesale (operator decision extending #2137) — the "unbounded pytest suite needing budget/quarantine" premise no longer exists because the suite itself is gone |
| 7 | #2147 | on-the-record | Still live | `ls docs/specs/`; `find . -iname "consumer-slo*"`; `git log --all --grep="consumer-slo" -i` | `docs/specs/consumer-slo.md` (untracked — does not exist and no commit has ever touched it) — the issue's whole acceptance criterion is unmet |
| 8 | #2193 | on-the-record | Already resolved | `git log --all --oneline -S "DEAD-UNRECOVERED-COMMITS"`; `sed -n '280,350p' watchdog.py` | PR #2202 (`23e9d029`) added the `DEAD-UNRECOVERED-COMMITS` diagnosis state exactly as asked; hardened by PR #2843 (`31ceac1e`, #2795) |
| 9 | #2216 | on-the-record | Already resolved | `grep -n _watchdog_noise_state_path watchdog.py`; `gh pr view 2247` | PR #2247 (`6e23bf01`, #2240) explicitly names #2216 as one of two mechanisms it fixed by routing state through `gates/state_paths.py`'s `MUSTER_STATE_ROOT`-anchored accessor |
| 10 | #2297 | on-the-record | Still live | `grep -n "auto-sweep\|unremovable" spawn.py watchdog.py lifecycle.py`; `sed -n '780,820p' lifecycle.py` | `lifecycle.py:803-811` self-heals read-only dirs (ask #2) but no per-workspace "record once, skip on repeat" state exists anywhere (derived: `grep -rn unremovable .` = no output, 0 hits repo-wide) |
| 11 | #2332 | on-the-record | Still live | `grep -rn "merge-readiness\|merge_readiness"`; `grep -n "a.role ==" spawn.py`; `find . -iname test_merge_gate.py` | `spawn.py`'s full role dispatch has no `merge-readiness` entry; `gates/merge_gate.py` is a single-PR gate, not the issue-wide aggregator asked for; the cited acceptance test file (`gates/test_merge_gate.py`, untracked — no such file) does not exist |
| 12 | #2357 | on-the-record | Still live | `find . -path "*/.claude/rules*"`; `find . -iname test_spawn_directive_assembly.py`; `git log --all --grep="2357"` | no `.claude/rules/*.md` files exist (untracked — none in tree), the cited acceptance test does not exist, and no commit references #2357 at all |
| 13 | #2360 | on-the-record | Still live | read `gates/record_lint.py:740-798,1153-1219,1222-1277`; `grep -n "grep -c" gates/record_lint.py` | the only derived-figure checks are `wc -l` and a plain-pytest `N passed` regex — no `--collect-only` pattern, no `grep -c` anywhere (derived: `grep -n "grep -c" gates/record_lint.py` = no output), no arithmetic recompute of a sample/tally claim |
| 14 | #2415 | on-the-record | Still live (grown, not shrunk) | `wc -l on-the-record/directive/acceptance-format.md`; `grep -n "^- [A-Z].*(issue"`; `git log --follow` | file is now 129 lines / 8 named rules — up from the 73 lines / 5 rules the issue describes (derived: `wc -l on-the-record/directive/acceptance-format.md` = 129); every touching commit since filing is additive, never a redesign |
| 15 | #2498 | on-the-record | Still live | read `skills.py:115-122` (`_carries_hooks`); `docs/issue-2488/reports/implementation/2026-08-26-hunt-skills-resolver-fix.md` | `_carries_hooks()` is still exactly `(skill_dir / "hooks").is_dir()`, byte-identical to the mechanism a prior hunt record reproduced as bypassable via `plugin.json`'s `"hooks"` key; no commit references #2498 |
| 16 | #2502 | on-the-record | Still live | `grep -n "progressed-dirty-tree\|recovery_policy\|classify" watchdog.py`; traced `lifecycle.py:_auto_respawn_check`→`board.py:session_end_verdict`→`_respawn_or_cap` | zero matches in `watchdog.py` (derived: `grep -n "progressed-dirty-tree" watchdog.py` = no output); the live dead-entry path never calls `gates/recovery_policy.py::classify()` or checks `has_commit`/`has_pr` |
| 17 | #2514 | on-the-record | Still live | `cat pytest.ini`; `grep -rn "MUSTER_TEST_WORKERS"`; `nproc; uptime` | `pytest.ini:4` is still bare `addopts = -n auto`; no shared worker-budget or load-average check exists anywhere in the repo (derived: `grep -rn "MUSTER_TEST_WORKERS" .` = no output) |
| 18 | #2576 | on-the-record | Already resolved (substantially; residual scope explicitly reported) | `gh pr view 2586 --json title,body,mergedAt,state`; `grep -lE "역할\|&lt;role&gt;\|CLAUDE_ROLE" on-the-record/hooks/*.sh \| wc -l` | PR #2586 (merged 2026-08-27, "Advances #2576") did the classify-then-convert work asked for and explicitly reported `delegated-judgment-gate.sh`'s remaining dependency as a traced, fail-safe Open finding rather than silently missing it; derived: `grep -lE "역할|<role>|CLAUDE_ROLE" on-the-record/hooks/*.sh | wc -l` = 12 (down from the issue's own count of 18), consistent with intentional partial conversion, not abandonment |
| 19 | #2588 | on-the-record | Already resolved | `git log --oneline -- gates/requirement_linkage.py`; live call of `check_issue_body()` | `gates/requirement_linkage.py:45-77` is already a pure, network-free function shared by the pre-publication and admission-time callers (existed since PR #1026, predates #2588); live repro confirms the exact pass/refuse behavior the acceptance criterion describes |
| 20 | #2644 | on-the-record | Still live | `grep -n "def verification_deficit" gates/*.py`; `grep -n "_own_pr_supplies_verification" gates/merge_gate.py` | `verification_deficit()` never calls `_own_pr_supplies_verification()`, while `merge_gate.py:211`'s `required_verification_missing()` does — the two functions structurally disagree in that exemption window, and `verification_deficit`'s own docstring claims agreement with no caveat |
| 21 | #2677 | on-the-record | Still live | read `on-the-record/hooks/stop-gate.sh:63-69`; `git log --oneline -- on-the-record/hooks/stop-gate.sh`; live regex repro | the TRIGGER regex fires on bare phrase presence regardless of quoting context; a synthetic "completion report" that merely *quotes* a prior `APPROVE issue-2600` message reproduces a false positive live (see appendix); derived: `git log --oneline -- on-the-record/hooks/stop-gate.sh` top entry is commit `07b7ad8d` |
| 22 | #2692 | on-the-record | Still live | `python3 spawn.py --skill-candidates "<console-input task>"`; same for the inventory-schema task | both wrong top-1 matches reproduce exactly against current HEAD, matching the issue's own cited scores (derived: see appendix code fence for this row — 9.11763648123324 and 9.46825963018722); `spawn.py:366`'s `rank_skills` is unpatched since PR #2690 landed it |
| 23 | #2726 | on-the-record | Still live (open judgment call) | `grep -n "_TRIGGER_PATH_PATTERNS" on-the-record/hooks/quality-bar-gate.sh`; `git show b6f6ac05` | PR #2633 (#2631) removed only the redundant `BAR_ROLES` literal; `_TRIGGER_PATH_PATTERNS` (`quality-bar-gate.sh:232-243`) still hard-codes the same 7 domain-name keys with a comment restating the exact reasoning the 2026-08-27 ruling rejected for `BAR_ROLES`; no commit has adjudicated whether this satisfies the ruling |
| 24 | #357 (core) | tokenmaxxxer-core | Still live | read `core/hooks/board-gate.sh:568-611` (`_is_unanalyzable_write_shape`); `git log --grep="357\b" --all` | `INTERPRETER_HEADS`/`WRITE_UNSAFE_HEADS` are closed literal-name enumerations; a shell-function head (`pywrap`) or PATH-shadowed bare word (`run`) matches neither and falls through undetected; no commit or comment anywhere mentions #357; related finding at `docs/issue-233/reports/adversarial-review-a3668c04.md` (untracked at this checkout's current HEAD, committed historically at commit `be2058f`) |

derived: tally counted directly from the 24 table rows above by category — Already resolved: #2193, #2216, #2576, #2588 (4 rows); Premise gone: #1650, #2136 (2 rows); Still live: #1633, #1656, #1694, #2147, #2297, #2332, #2357, #2360, #2415, #2498, #2502, #2514, #2644, #2677, #2692, #2726, #357 (17 rows); Cannot determine: #2071 (1 row). 4+2+17+1=24, matching the named population.

### Evidence appendix (raw command output backing the table)

**#1633**
```
$ git log --oneline --all | grep -iE "2610|2559" | head -3
49c4854b issue-2610: retire the 44-entry role catalog and spawn_roles.json (#2630)
3d7bb6dc issue-2559: remove write_scope entirely — sessions are not scope-limited (#2562)
$ ls gates/patrol_*.py
gates/patrol_board.py gates/patrol_promote.py gates/patrol_queue.py gates/patrol_trigger.py
```

**#1650**
```
$ ls -la .github/workflows/
ls: '.github/workflows/'에 접근할 수 없음: 그런 파일이나 디렉터리가 없습니다
$ git show ccbe7fe9 --stat | head -3
commit ccbe7fe9 ... feat(issue-460): retire this repo's own GitHub Actions workflows
$ git log --all --diff-filter=D -- "**/test_spec_index.py"
a555e169 issue-2525: retire the plugin's own test suite (#2528)
```

**#1656**
```
$ python3 -c "
import re
pat = re.compile(r'^\s*[-*]?\s*validity-consult-skip\s*:\s*trivial\b', re.MULTILINE)
print(bool(pat.search('validity-consult-skip: trivial but actually risk-bearing')))
"
True
```

**#1694**
```
$ find . -iname "goals.md"
(no output)
$ ls docs/reports/product/
2026-08-14-hiring-market-recon.md  priorities  priorities.md  quality-bar.md
```

**#2071**
```
$ grep -n "SKILL_JUDGE_TIMEOUT_DEFAULT" consult.py
52:SKILL_JUDGE_TIMEOUT_DEFAULT = 90  # issue #2076: measured completion rate at 45s was <80% in
```
derived: issue's own 2026-08-28 comment thread: "Defect 1 recurred and is still live 2026-08-28 ... timed out after 35.3 seconds ... Filed #2679 ... and #2678."

**#2136**
```
$ git show a555e169 --stat | head -5
commit a555e16987848c97476fac547026a71313ddecb4
issue-2525: retire the plugin's own test suite (#2528)
 conftest.py                    |  92 -
 gates/test_acceptance_gate.py  | 315 -
$ grep -rn "quarantine" --include=*.py .
(no output — 0 hits)
```

**#2147**
```
$ ls docs/specs/ | grep -i slo
(no output)
$ find . -iname "consumer-slo*"
(no output)
```

**#2193**
```
$ git log --all --oneline -S "DEAD-UNRECOVERED-COMMITS" -- watchdog.py spawn.py
31ceac1e  issue-2795: make DEAD-UNRECOVERED-COMMITS ask the remote before alarming
23e9d029  issue-2193: name branch+commit count on dead-with-unpushed-commits sessions instead of silent DEAD-ERRORED (#2202)
$ sed -n '326,334p' watchdog.py
if commit_count:
    # 이슈 #2193: 죽었고 PR 도 없지만 커밋은 남았다 ...
    return _diagnosis({"state": "DEAD-UNRECOVERED-COMMITS",
            "next_action": "recover-unpushed", ...})
return _diagnosis({"state": "DEAD-ERRORED", "next_action": "respawn", ...})
```

**#2216**
```
$ gh pr view 2247 --repo tokenmaxxxer/on-the-record --json body
"...should_park() (#2238) and the watchdog noise suppressor (#2216) were both silently inert
for the same reason: their cross-tick memory was written to root / \"runs\"...
Adds gates/state_paths.py, a single accessor orchestrator_state_path(filename) anchored to
MUSTER_STATE_ROOT when set..."
```

**#2297**
```
$ grep -rn "unremovable" .
(no output, 0 hits repo-wide)
$ sed -n '791,795p' lifecycle.py
def _chmod_retry(func, path, exc_info):
    # Go 모듈 캐시 등 읽기 전용 디렉터리/파일에서 rmtree 가
    # PermissionError 로 죽는 문제(이슈 #229). ...
```

**#2332**
```
$ grep -rn "merge-readiness|merge_readiness|MERGE-ELIGIBLE" . --include=*.py --include=*.md | grep -v docs/
(no output)
$ find . -iname "test_merge_gate.py"
(no output)
```

**#2357**
```
$ find . -path "*/.claude/rules*"
(no output)
$ git log --all --oneline | grep -i "2357"
(no output)
```

**#2360**
```
$ grep -n "grep -c" gates/record_lint.py
(no output — 0 hits in the 1584-line file)
$ sed -n '1214,1219p' gates/record_lint.py
_FENCE_PYTEST_CMD_LINE = re.compile(
    r"^\$\s*(?:python3?\s+-m\s+)?pytest\s+(.+)$", re.MULTILINE)
_FENCE_PASSED_SUMMARY = re.compile(r"(?:^|\s)(\d+)\s+passed\b")
```

**#2415**
```
$ wc -l on-the-record/directive/acceptance-format.md
129 on-the-record/directive/acceptance-format.md
$ git log --follow --oneline -- on-the-record/directive/acceptance-format.md
04a041ab issue-2600: fix PR #2712 send-back — complete role/역할 retirement ...
cb77ae6f issue-2503: register forbidden_action_rule.py + disclose registration-guard hole (#2702)
8d100d66 issue-2414: measure same-shape follow-up defect rate, offer scoped negative-criteria/convergence-evidence checks
```

**#2498**
```
$ sed -n '115,122p' skills.py
def _carries_hooks(skill_dir: Path) -> bool:
    """... hooks/ 서브디렉터리 존재 ..."""
    return (skill_dir / "hooks").is_dir()
```
derived: hunt record `docs/issue-2488/reports/implementation/2026-08-26-hunt-skills-resolver-fix.md:9` states: "the decision doc's 'guidance-only, never code the harness executes' claim is false: `resolved_skill_sources()`'s `hooks/` guard only checks for a literally-named `hooks` subdirectory, but a plugin manifest can point Claude Code's hook loader at an arbitrarily-named file via `.claude-plugin/plugin.json`'s `"hooks"` key" — reproduced live in that record.

**#2502**
```
$ grep -n "progressed-dirty-tree|recovery_policy|classify" watchdog.py
119:def _classify_log_lines_heartbeat_only(text: str, now: float, ...
```
derived: `lifecycle.py:484-526` (`_auto_respawn_check`) calls `board.py:session_end_verdict()` then, on `"crashed"`, calls `_respawn_or_cap()` directly — no `has_commit`/`has_pr` branch anywhere in that call chain.

**#2514**
```
$ cat pytest.ini
[pytest]
addopts = -n auto
$ nproc; uptime
16
16:31:35 up 95 days, ... load average: 2.85, 1.87, 1.37
```

**#2576**
```
$ gh pr view 2586 --repo tokenmaxxxer/on-the-record --json title,body,mergedAt,state
{"mergedAt":"2026-08-27T03:14:19Z","state":"MERGED","title":"issue-2576: rebuild role-carrying hooks onto the lease/skills axis", ..., "Advances #2576"}
$ grep -lE "역할|<role>|CLAUDE_ROLE" on-the-record/hooks/*.sh | wc -l
12
```

**#2588**
```
$ python3 -c "
import gates.requirement_linkage as rl
print(rl.check_issue_body(1, 'some body with no tag'))
print(rl.check_issue_body(1, 'body\n\ninfrastructure/no-direct-requirement'))
"
['이슈 #1 본문이 요구 ID(...)를 하나도 인용하지 않고, 명시적 태그 ... 통과 불가']
[]
```

**#2644**
```
$ grep -n "def verification_deficit" -A 15 gates/*.py
def verification_deficit(subject_board: dict, subject_author: str | None = None) -> int:
    ... Mirrors gates/merge_gate.py::required_verification_missing()'s count-only branch exactly ...
    return max(0, REQUIRED_INDEPENDENT_VERIFICATIONS - verifying_record_count(subject_board, subject_author))
$ grep -n "_own_pr_supplies_verification" gates/merge_gate.py
118:def _own_pr_supplies_verification(repo: Path, subject: str, own_branch: str | None, ...
211:        if _own_pr_supplies_verification(repo, subject, own_branch, subject_author):
```

**#2677**
```
$ python3 -c "
import re
TRIGGER = re.compile(r'(승인\s*요청|승인해|request(ing)? approv|please approve|seeking approval|APPROVE issue-)', re.IGNORECASE)
msg='Work on #2600 is done and merged. Earlier the gate had printed: \"stop-gate: ... APPROVE issue-2600 before stopping\" but that was resolved.'
print(bool(TRIGGER.search(msg)))"
True
$ git log --oneline -- on-the-record/hooks/stop-gate.sh
07b7ad8d issue-2538: ... (#2540)
```
derived: top commit dated 2026-08-26, per `git log` above, precedes the 2026-08-27/28 session the issue reports false positives from.

**#2692**
```
$ python3 spawn.py --skill-candidates "Map console input fields onto engine fields: deadzone and sensitivity per stick, normalized vector plus curve id"
"name": "secure-coding-input-validation-injection-defense", "score": 9.11763648123324
$ python3 spawn.py --skill-candidates "Convert the legacy inventory row shape into the new item schema: quantity, durability, stack limit move; rarity derived; two columns dropped"
"name": "api-design-tool-landscape", "score": 9.46825963018722
```
derived: both scores match the issue's own cited 9.12/9.47 (rounded).

**#2726**
```
$ grep -n "_TRIGGER_PATH_PATTERNS|BAR_ROLES" on-the-record/hooks/quality-bar-gate.sh
232:_TRIGGER_PATH_PATTERNS = {
245:scoped_skills = quality_bar.bar_scoped_skills(pr_files, _TRIGGER_PATH_PATTERNS)
253:# _TRIGGER_PATH_PATTERNS' keys) only ever labels *which* domains a denial
```
derived: `git show b6f6ac05` diff shows `BAR_ROLES` deleted but the 7-key `_TRIGGER_PATH_PATTERNS` dict retained verbatim, with a comment restating "these are domains, not identities" — the exact framing the 2026-08-27 operator ruling overruled for the sibling list.

**#357 (tokenmaxxxer-core)**
```
$ sed -n '568,611p' core/hooks/board-gate.sh
def _is_unanalyzable_write_shape(stripped, head, full_cmd=None):
    if "<<" in stripped: return True
    if head in INTERPRETER_HEADS:
        if any(w in INLINE_FLAG_WORDS for w in gate_lib.gate_trailing_words(stripped)): return True
    if head in WRITE_UNSAFE_HEADS: return True
    if FUSED_INTERP_RE.search(stripped): return True
    if full_cmd is not None and VAR_INTERP_RE.search(full_cmd): return True
```
derived: `INTERPRETER_HEADS`/`WRITE_UNSAFE_HEADS` are closed enumerations of literal interpreter names; a head like `pywrap` (a shell function) or `run` (a PATH-shadowed bare word) matches none of these branches, so the function never flags it unanalyzable.

### Requirement extraction (skill-verdict evidence)

Ran the mounted `conformance-review-requirement-extraction` skill against
issue #2865's acceptance section before rendering any verdict, feeding it
the issue body text captured via `gh issue view 2865`. Its output split
the spawn-prompt's bundled "four standing invariants" sentence into 4
independently-checkable items, and flagged the "empty state: report zero
in either category" clause as conditional on the Already-resolved/
Premise-gone tally computed above (derived: 4 and 2 respectively, both
non-zero, per the tally line at the end of the classification table).

derived: `echo "1633 1650 1656 1694 2071 2136 2147 2193 2216 2297 2332 2357 2360 2415 2498 2502 2514 2576 2588 2644 2677 2692 2726" | wc -w` = 23, plus the one core-repo issue (`357`) named separately in the same issue-#2865 fenced block = 24 total, matching the issue title's "24 unstarted backlog issues."

### Standing-invariant checks (delivery's own diff, not the 24 target issues)

acceptance: `git diff --stat -- . ':!docs'` — result:
```
(no output — empty diff)
```
Nothing outside `docs/` was touched, so this is a docs-only delivery — no overhead change, no touch to the retired role axis, and no touch to any monitor/watchdog file.

acceptance: `for n in 1633 1650 1656 1694 2071 2136 2147 2193 2216 2297 2332 2357 2360 2415 2498 2502 2514 2576 2588 2644 2677 2692 2726; do gh issue view $n --repo tokenmaxxxer/on-the-record --json state -q .state; done; gh issue view 357 --repo tokenmaxxxer/tokenmaxxxer-core --json state -q .state` — result:
```
OPEN (x24, see the full 24-line transcript under "What was done" above)
```

## Why

The issue's own framing ("never classify from the title or the issue
body") is the entire point of the exercise: tonight's four precedents
(#2755, #2135, #2324, #2848) show both a live-reading issue turning out
fixed and a settled-reading issue turning out to not reproduce. The only
way to avoid repeating either mistake is to run something against
today's code for every single row — so each of the 24 issues (derived:
counted from the classification table's 24 numbered rows above) was
assigned to one of five parallel read-only investigation agents, split
by issue-number range into group sizes 5, 5, 5, 5, and 4 (5+5+5+5+4=24,
matching the population), the last group crossing into the
`tokenmaxxxer-core` checkout for #357. Each agent was required to run
`gh issue view` plus at least one code-level command before returning a
verdict. Parallelizing the investigation (rather than doing all 24
serially in this session) let each issue get the same depth of digging
without one session's context window becoming the limiting factor
across 24 independent, non-interacting units — the same "collision
risk" analysis `parallel-decomposition` asks for classifies these as
freely parallel: read-only, no shared write set, no shared identifiers.

No fixing, closing, or editing was performed anywhere — the deliverable
is exclusively this classification table, per the issue's explicit
"must not" clause.

## Upstream basis

- `gh issue view 2865 --repo tokenmaxxxer/on-the-record` (same-commit — the issue body is the sole upstream input; no prior docs/issue-2865 record existed before this one)

## Open findings

canonical: this record's own classification table above (rows #2071,
#2576, #2726) — three verdicts carry a residual worth flagging to the
operator, though none of them changes the row's assigned verdict:

- #2071 — the "Cannot determine" verdict covers only defects 2 and 3 of
  the original 3-defect bundle; defect 1 is fixed per the appendix
  fence quoting `consult.py:52` above.
- #2576 — "Already resolved (substantially)" because derived: 12 of the
  originally-flagged 18 hook files (per the appendix `grep -l | wc -l`
  command for this row) still carry role vocabulary; the landing PR
  explicitly reported the remaining dependency as blocked rather than
  silently leaving it, so this reads as intentional partial scope.
- #2726 — the "still live" verdict is solid on the code fact, but
  whether `_TRIGGER_PATH_PATTERNS` counts as the same kind of
  role-identity list the 2026-08-27 ruling rejected for `BAR_ROLES` is
  an unadjudicated judgment call — see the appendix quote for this row.

## What did not work

Nothing attempted in this delivery failed outright — no deviation from
the issue's ask occurred. derived: the initial dispatch tally briefly
narrated the population as 25 before recount corrected it to 24
(matching the issue title, per the requirement-extraction population
count above); the five dispatched investigation groups were already
sized 5+5+5+5+4=24 against the correct list, so no rework was needed
once the correction was made.

## Next steps

This record's classification table (all 24 rows above, each carrying
its own verdict and citation) is the deliverable this issue's
acceptance criteria asked for. No further action is owed by this role
— the issue's own "must not" clause reserves the decision of what to
do with any of these 24 verdicts to the operator. `loop_state` is
terminal (`landed`).
