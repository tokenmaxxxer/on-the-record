---
issue: 2678
role: architecture-interface-contract-shape+silent-failure-audit-766c3784
author: architecture-interface-contract-shape+silent-failure-audit-766c3784
skills: architecture-interface-contract-shape (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
verifies_subject: false
loop_state: landed
upstream:
  - path: consult.py
    sha: same-commit
  - path: spawn.py
    sha: same-commit
  - path: on-the-record/hooks/skill-verdict-guard.sh
    sha: same-commit
  - path: on-the-record/directive/spawn-and-board.md
    sha: same-commit
---

# issue-2678 — architecture-interface-contract-shape+silent-failure-audit-766c3784 record

This delivers issues #2678 and #2681 together, per the spawning
instruction that they are one chain and must not be split: #2678 gives
the orchestrator a way to choose a skill before spawning, #2681 makes it
visible when a chosen skill is never opened. Built under the build-now
bypass (`CORE_BUILD_NOW=1`, set by the spawner) — no separate proposal
round.

## What was done

### #2678 — `rank_skills()` and `spawn.py --skill-candidates`

Added `consult.rank_skills()` (`consult.py:749`, aliased `rank_skills =
consult.rank_skills` at `spawn.py:365`) — a read-only ranking function
the orchestrator calls before committing to `--skills`. It never mutates
anything; it reuses, byte-identical, the two functions spawn's own
internal add-only cross-family mount already calls:
`_bm25_cross_family_scores()` for the ranking and
`_cross_family_skill_matches_with_consult()` for the optional judge
refinement — one scoring implementation, two call sites.

```python
def rank_skills(task_text: str, role: str = "candidates",
                repo_root: Path | None = None, *,
                issue: int | None = None, cwd: str | None = None,
                home: Path | None = None, target_repo_root: Path | None = None,
                use_judge: bool = False, model: str | None = None,
                k: int = 2) -> dict:
```
canonical: `consult.py:749-838` (function body quoted above, read
directly from the working tree this session wrote).

Return contract (issue #2678's third caveat — pin the fail-open contract
down explicitly): always a dict, never `None`, never raises.
- `ranked`: full BM25 order (score desc), `[]` only when nothing shares a
  token with the task text — this stage cannot time out (a local
  tokenize+arithmetic loop over on-disk SKILL.md files, no subprocess).
- `outcome`: `"no-candidates"` (ranked is genuinely empty) |
  `"bm25-only"` (`use_judge=False`, judge never asked) | `"completed"` |
  `"fail-open"` (judge errored/timed out — `ranked` still fully
  populated, never collapses into "ranked nothing") |
  `"fast-path:<names>"` optionally suffixed `"+completed"` or
  `"+fail-open"`.
- `picked`: judge's/fast-path's actual selections, only non-empty when
  `use_judge=True`.

derived: `python3 -m pytest test/test_skill_candidates_ranking.py -q -o
addopts=''` — 6 passed, executed this session, exercising exactly this
return contract (`TaskShapeRankingTest`, `EmptyStateTest`,
`SameScoringTest`, `FailOpenDistinguishableTest`,
`test/test_skill_candidates_ranking.py:1-165`).

CLI entrypoint `spawn.py --skill-candidates "<task>" [--issue <n>]
[--with-judge]` (`spawn.py:1958-1971` flag definitions, `spawn.py:2172`
dispatch) — mirrors the existing no-session `--skill` dispatch pattern
(`spawn.py:2139`), never spawns a session, never touches
roster/lease/board-gate. Forwards `repo_root=_skill_repo_root()`,
`home=Path.home()`, `target_repo_root=Path(a.cwd)` — the identical
arguments `_spawn_one()`'s own cross-family call already uses
(`spawn.py:3336-3338`), so the same task text yields the same ranking
through either entry point, not merely the same function reference.

Documented in `on-the-record/directive/spawn-and-board.md` (new
paragraph right after the existing `--skills` spawn-form paragraph):
names the command, states it never spawns and never chooses for the
orchestrator, and states when to run it (task doesn't obviously match a
known skill; a `--skills` guess was just rejected).

### #2678 — caveat 1 (extractability) verified, not assumed

The delegated consult's own trace recorded `no-evidence:1` for "BM25+judge
logic in spawn.py is cleanly extractable." Traced the actual call graph
instead of assuming it — read the definitions below in full this
session, not via grep:

```
consult.py:749       def rank_skills(task_text, role="candidates", ...
directive_assembly.py:702  def _bm25_cross_family_scores(task_text, role, repo_root, home=None, target_repo_root=None):
pipeline.py:1301     def _skill_trigger_line(skill_dir: Path) -> str | None:
pipeline.py:1425     def _tokenize(text: str) -> set[str]:
pipeline.py:1432     def _cross_family_candidate_corpus(role, repo_root, home=None, target_repo_root=None):
```
canonical: the five function definitions quoted above, their full bodies
read from `directive_assembly.py` and `pipeline.py` this session.

Findings:
- `_bm25_cross_family_scores()` (`directive_assembly.py:702`) takes
  `task_text`/`role`/`repo_root`/`home`/`target_repo_root` as plain
  parameters and touches no spawn-session mutable state — no lease, no
  roster, no workspace lock.
- Its helpers (`pipeline.py:1301-1504`) are equally state-free: pure
  filesystem reads (`SKILL.md` frontmatter parsing) plus arithmetic.
- The only "coupling" is the `_sp` late-binding alias
  (`directive_assembly.py:33`, bound to the spawn module object at
  `spawn.py:585-586`) every extracted module in this cluster already
  uses for test-patchability — `pipeline.py`, `skills.py`, and
  `consult.py` each document the identical pattern in their own module
  docstrings (issue #2105 extraction cluster). This is the established
  idiom the whole cluster already runs on, not spawn-specific state
  coupling introduced for this issue.
- The judge stage (`_skill_judge_consult()`, `consult.py:443`) is
  genuinely not side-effect-free: it spawns a real haiku subprocess,
  writes a consult-trace file, commits it
  (`_sp._commit_consult_trace()`), and appends a `skill_judge_perf`
  ledger event — but that is spawn's own existing per-spawn cost already
  paid on every task-scoped spawn via `_composed_consult_skill_source()`
  (`consult.py:775-778`), reachable one call earlier here, not a new
  cost class.

Conclusion: the caveat's premise (spawn-specific state coupling blocking
extraction) does not hold for the BM25 stage — it was already extracted
in issue #2105. Design consequence: `rank_skills()` defaults
`use_judge=False` (no subprocess, no side effect) and makes the judge
stage opt-in via `--with-judge`, a deviation from the consult's literal
"extract BM25+skill_judge" framing, made because the judge half carries
real per-call costs the BM25 half does not.

### #2678 — Acceptance checks, executed live

**Bullet 1 — ranked output differs and matches the task; empty state.**

```
$ python3 spawn.py --skill-candidates "sync 호출을 이벤트로 바꿀지 orchestration vs choreography 로 saga 를 설계해야 하는 architecture boundary contract 문제" --issue 2678
"outcome": "bm25-only"; ranked[0].name == "architecture-interface-contract-shape"

$ python3 spawn.py --skill-candidates "verify the failing test set is identical before and after the merge, re-run pytest and confirm the deliverable-guard fix integrates cleanly with the existing exemption suffixes without breaking CI" --issue 2678
"outcome": "bm25-only"; ranked[0].name == "test-authoring-isolation-and-fixture-strategy"
(top 5 all test/verification-family skills; "architecture-interface-contract-shape" absent from top 5)

$ python3 spawn.py --skill-candidates "asdkjaslkdj qwoeiqwoe zxsdlkjfslkdj gibberish nonsense" --issue 2678
{"ranked": [], "outcome": "no-candidates", "picked": []}
```
derived: the three `spawn.py --skill-candidates` invocations above,
executed in this session against the real mounted
`skill-repository(297e350)` checkout — full JSON output inspected, not
paraphrased. Also codified as `TaskShapeRankingTest`/`EmptyStateTest` in
`test/test_skill_candidates_ranking.py:47-119`.

**Bullet 2 — candidate path and spawn's own selection use the same
scoring.**

```
$ python3 -m pytest test/test_skill_candidates_ranking.py::SameScoringTest -q -o addopts=''
1 passed
```
derived: the pytest invocation above, executed this session.
`SameScoringTest.test_candidate_path_matches_internal_bm25_scoring`
(`test/test_skill_candidates_ranking.py:103-121`) asserts
`spawn._bm25_cross_family_scores(...)`'s name order equals
`spawn.rank_skills(...)["ranked"]`'s name order for the same task text.

**Bullet 3 — the 12-spawn scenario, on real tasks.**

Searched for the consumer session's actual 12 spawn tasks before
substituting anything:
```
$ find / -xdev -iname "spawn-attempts.jsonl" 2>/dev/null | wc -l
9
$ for f in $(find / -xdev -iname "spawn-attempts.jsonl" 2>/dev/null); do grep -c implementation-blueprint "$f"; done
0
0
0
0
0
0
0
0
0
$ python3 -c "import json; print(list(json.loads(open('$ON_THE_RECORD/runs/spawn-attempts.jsonl').readline()).keys()))"
['event', 'attempt_id', 'issue', 'role', 'pid', 'ts']
$ find / -maxdepth 6 -iname "*consumer*" 2>/dev/null | grep -viE "linux-headers|linux-hwe|cuda|nodejs|/proc|devlink|hermes|docs/issue-(396|444)/proposals"
(no output)
```
derived: the four commands above — 0 of the 9 discovered
`spawn-attempts.jsonl` files contain an `implementation-blueprint` entry,
the schema has no task-text field, and no consumer-repo path was found —
all executed in this session against the live filesystem. The literal
12-task corpus named in the issue is therefore not present in this
sandbox, for the reasons shown in the transcript above (unverifiable: no
such corpus is reachable from this session's environment).

Substituted a real, labeled 12-task corpus instead: this repository's own
12 most recent GH issue titles preceding this chain, run through the
identical `rank_skills()` call used in bullet 1.

```
$ gh issue list --limit 30 --state all --json number,title
# top 12 excluding #2678/#2679/#2681 themselves: #2677,#2670,#2669,#2667,
# #2662,#2661,#2659,#2657,#2652,#2651,#2644,#2637
$ python3 -c "
import sys; sys.path.insert(0, '.')
import spawn
from pathlib import Path
tasks = [(2677,'stop-gate flags retrospective replies as approval requests — 3 false positives in one session'), ...]  # 12 real gh issue titles
repo_root = spawn._skill_repo_root()
for issue_n, title in tasks:
    r = spawn.rank_skills(title, 'orchestrator', repo_root, home=Path.home(), use_judge=False)
    print(issue_n, r['outcome'], r['ranked'][0]['name'] if r['ranked'] else None)
"
2677 bm25-only architecture-module-boundary-definition
2670 bm25-only product-discovery-hypothesis-testing
2669 bm25-only defect-verification-independence-from-upstream-verdicts
2667 bm25-only adversarial-review
2662 bm25-only release-engineering-branching-release-strategy
2661 bm25-only market-analysis-five-forces
2659 bm25-only incident-response-action-item-quality
2657 bm25-only technical-feasibility-build-vs-buy
2652 bm25-only upstream-defect-report-convention
2651 bm25-only knowledge-management-structure-findability
2644 bm25-only defect-verification-independence-from-upstream-verdicts
2637 bm25-only technical-feasibility-reversibility-tag
```
derived: the `gh issue list` call plus the 12-invocation `rank_skills()`
loop above, both executed in this session. Result: 12/12 = 100% top-ranked
to a skill other than `implementation-blueprint` (8 distinct top-1 skills
across the 12 tasks, per the transcript above).

**Bullet 4 — the directive names the candidate command and when to run
it.**
```
$ grep -n "skill-candidates" on-the-record/directive/spawn-and-board.md | head -3
13:  Issue #2678: before picking `--skills`, run
14:  `python3 ${CHECKOUT}/spawn.py --skill-candidates "<task>" --issue <n>` to
```
derived: the grep above, executed this session against the committed
file (`on-the-record/directive/spawn-and-board.md`, this session's own
commit `84d87687`).

### #2681 — zero-invocation signal in `skill-verdict-guard.sh`

Before this change, `on-the-record/hooks/skill-verdict-guard.sh` produced
byte-identical output for two different session shapes — read directly,
the pre-change branches at what are now lines 189-232:
```
if not mounted:
    finish(reminder)
invoked = invoked_skill_names(transcript_path, set(mounted))
if not invoked:
    finish(reminder)
```
canonical: `on-the-record/hooks/skill-verdict-guard.sh` pre-change
content, quoted verbatim above (`git diff 84d87687^ 84d87687 -- on-the-record/hooks/skill-verdict-guard.sh`,
the `-` side, this session's own commit). Both branches called
`finish(reminder)` with nothing to distinguish them, and `reminder` is
`None` after the first Stop-hook fire in a session (per-session dedup
marker at `~/.claude/tokenmaxxxer/obligations-noted/`), so both shapes
could produce literally no output at all.

Added `zero_invocation_notice(mounted_names)`
(`on-the-record/hooks/skill-verdict-guard.sh:197-209`) and changed the
`if not invoked:` branch (line 232) to
`finish(zero_invocation_notice(mounted), reminder)`. The notice names
the mounted-but-unused skills, states explicitly it is advisory only (no
verdict line owed — does not restore #2153's per-mounted-skill
obligation), makes no judgment about whether any of them applied, and
lands in `hookSpecificOutput.additionalContext` (never
`decision:"block"`) — the same channel the pre-existing `reminder`/
`verdict_text` messages already use to reach the session transcript /
`spawn.py watch` output.

### #2681 — frequency measured before deciding severity

Could not access the consumer session's real transcript corpus in this
environment. Measured the zero-invocation rate instead against every
skill-composed session workspace retained locally on this machine.

```
$ cd "$MUSTER_WORKSPACE_ROOT" && python3 - <<'PY'
import glob, os, re
dirs = [d for d in glob.glob("on-the-record-issue-*")
        if os.path.isdir(d) and re.search(r'\+.+-[0-9a-f]{8}$', d)]
landed, has_verdict = 0, 0
for d in dirs:
    m = re.match(r'on-the-record-issue-(\d+)-(.+)$', d)
    issue_n, role = m.group(1), m.group(2)
    p = os.path.join(d, "docs", f"issue-{issue_n}", "reports", f"{role}.md")
    if not os.path.isfile(p): continue
    text = open(p, encoding="utf-8", errors="replace").read()
    fm = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    if not fm or not re.search(r'(?m)^loop_state:\s*landed', fm.group(1)): continue
    landed += 1
    if re.search(r'skill-verdict:\s*\S', text): has_verdict += 1
print(landed, has_verdict)
PY
47 47
```
derived: the script above, executed in this session from
`$MUSTER_WORKSPACE_ROOT`. Result: landed=47, has_verdict=47, i.e.
47/47 = 100% of retained landed skill-composed session records carried at
least one skill-verdict line — zero zero-invocation cases in this local
sample.

unverifiable: this is a survivorship sample of whichever workspace
directories still exist on this machine, not the full historical
population — cleaned-up workspaces are invisible to it, so the true rate
could differ from the measured rate above. Two apparent zero-invocation
hits from an earlier, less careful regex pass (`^skill-verdict:` anchored
at line-start) turned out on inspection not to be real cases: `#2610` and
`#2593` are `loop_state: in-progress` orphaned skeletons (never
delivered, correctly excluded from the `landed`-only count above), and
`#2637`'s initial hit was this session's own regex bug (missing the
actual `- skill-verdict:` bulleted convention) —
```
$ grep -n "skill-verdict" "on-the-record-issue-2637-adversarial-review+secure-coding-input-validation-injection-defense-b0e82077/docs/issue-2637/reports/adversarial-review+secure-coding-input-validation-injection-defense-b0e82077.md"
424:- skill-verdict: adversarial-review — applied: invoked; ...
425:- skill-verdict: secure-coding-input-validation-injection-defense — applied: invoked; ...
426:- skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; ...
427:- skill-verdict: defect-verification-reproduction-evidence-quality — applied: invoked; ...
428:- skill-verdict: work-in-english — applied: invoked; ...
```
derived: the grep above, re-run from `$MUSTER_WORKSPACE_ROOT` this
session — confirms 5 genuine `skill-verdict:` lines in that record, 5/5
lines matching the bulleted convention the earlier regex missed.

Given the measured rate above is low and the issue's own "must not"
independently forbids a blocking gate regardless of rate, the fix stays
fully advisory — consistent with this hook's existing house style (its
pre-existing checks already only ever emit `additionalContext`, never
`decision:"block"`, per the file's own header comment).

### #2681 — Acceptance checks, executed live

```
$ python3 -m pytest test/test_skill_verdict_guard_zero_invocation_signal.py -q -o addopts=''
4 passed
```
derived: the pytest invocation above, executed in this session — the
real shipped hook (`bash on-the-record/hooks/skill-verdict-guard.sh`)
run against a real Stop-event JSON payload on stdin and a fabricated
transcript file, same harness shape as
`test/test_deliverable_guard_priorities_shard.py`.
- `ZeroMountedVsZeroInvokedTest` (bullet 1: mounts-none vs
  mounts-N-invokes-zero artifacts differ; the differing artifact is
  `hookSpecificOutput.additionalContext`).
- `SignalLandsInAdditionalContextTest` (bullet 2: signal lands in
  `additionalContext`, names the mounted skill, states "Advisory only").
- `ConsumerSessionReplayTest` (bullet 3: replays the issue's exact shape —
  `MUSTER_SKILLS=architecture-interface-contract-shape,work-in-english`,
  zero Skill tool_use blocks in the transcript — signal fires).
- `InvokedSuppressesNoticeTest` (regression guard: invoking one mounted
  skill must not trigger the new notice — no change to #2153's existing
  path).

### Test suite, full run

```
$ python3 -m pytest -q -o addopts='' test/
15 failed, 382 passed, 4 xfailed
$ git stash --include-untracked -q && python3 -m pytest -q -o addopts='' test/ 2>&1 | grep '^FAILED' | sort > /tmp/before_failures.txt && git stash pop -q
$ python3 -m pytest -q -o addopts='' test/ 2>&1 | grep '^FAILED' | sort > /tmp/after_failures.txt
$ diff /tmp/before_failures.txt /tmp/after_failures.txt && echo IDENTICAL
IDENTICAL
```
derived: the four commands above, executed in this session. The 15
failures are identical before and after this session's changes (`diff`
printed nothing, exit 0) — all 15 fail with `fatal: 'origin' does not
appear to be a git repository` (no network/remote in this sandbox),
pre-existing and unrelated to this change. This session's changes add 10
new passing tests (`test/test_skill_candidates_ranking.py`,
`test/test_skill_verdict_guard_zero_invocation_signal.py`) and introduce
zero regressions.

## Why

`rank_skills()` reuses rather than reimplements the scoring because the
two-call-sites-disagreeing failure mode (issue #2678's second acceptance
bullet exists specifically to rule out) is only structurally impossible
when there is exactly one scoring implementation. Investigating caveat 1
first — rather than building the extraction the consult assumed was
still needed — found the BM25 stage already factored out cleanly by a
prior extraction. canonical: `directive_assembly.py:702` and
`pipeline.py:1301-1504`, the same function definitions quoted and traced
in the "caveat 1 verified" subsection above. Building a second extraction
on top would have duplicated an already-solved problem; the real open
design question was which of the two already-separate stages (BM25,
judge) the new orchestrator-facing entry point should call by default.
Chose BM25-only-by-default because the judge stage's side effects
(subprocess call, consult-trace commit, ledger write) are real per-call
costs that should be the orchestrator's opt-in choice (`--with-judge`),
not paid silently on every preview.

`--skill-candidates` forwards `_skill_repo_root()`/`Path.home()`/
`Path(cwd)` explicitly (matching `_spawn_one()`'s own call site) rather
than letting `rank_skills()` default them, because "same scoring" only
holds at the acceptance-test level (bullet 2 above) if the arguments
match too, not just the function reference.

`zero_invocation_notice()` stays advisory (never a hard refusal) for two
independent reasons: the issue's own "must not" forbids a blocking gate
outright, and this session's own frequency measurement — derived: the
same `$MUSTER_WORKSPACE_ROOT` scan quoted in the "#2681 — frequency
measured" subsection above, landed=47/has_verdict=47, i.e. 0/47 = 0%
zero-invocation — independently gives no evidence the case is common
enough to justify one even absent that constraint.

## What did not work

An early edit attempt inserted a stray unused key
(`"SKILL_CANDIDATES_MARKER_UNUSED": None`) into the existing `--skill`
dispatch block's JSON output while drafting the new `--skill-candidates`
block nearby. Caught and reverted in the same turn, before it was ever
run or committed — noted here as a real edit-then-undo, not because it
had any functional effect.

## Upstream basis

The delegated consult for issue #2678 (referenced in the spawning
instructions; its own trace tagged `no-evidence:1` for the extractability
caveat) — this session's "caveat 1 verified, not assumed" subsection
above is the resolution of that gap, derived from reading `consult.py`,
`pipeline.py`, and `directive_assembly.py` directly this session rather
than from the consult's text.

## Skill verdicts

- skill-verdict: architecture-interface-contract-shape — applied: invoked; used rule 12 (new module boundary — hide decisions likely to change, expose only the minimal contract) to shape `rank_skills()`'s return dict (`ranked`/`outcome`/`picked`, `consult.py:749-838`) rather than exposing the underlying BM25/judge call internals, and rule 1 (sync call on the caller's real-time critical path) to confirm `--skill-candidates` should stay a synchronous CLI call the orchestrator waits on, not a backgrounded one.
- skill-verdict: silent-failure-audit — applied: invoked; ran the audit's Step 1 against this session's own diff — canonical: `git show 84d87687 -- consult.py spawn.py on-the-record/hooks/skill-verdict-guard.sh | grep -nE "^\+.*(try:|except|catch)"`, empty output, re-run this session. Zero new `try`/`except` sites were added: `rank_skills()` adds no error handling of its own because it delegates to `_cross_family_skill_matches_with_consult()`, whose existing try/except (pre-existing, covered by issue #2679's seven-state judge logging) already guarantees it never raises — the fail-open contract this record's caveat-3 subsection depends on is fully inherited, not reimplemented, so there was no new catch site to classify as Handled/Silently Absorbed/Unreachable.
- other mounted skills: not triggered (work-in-english's own obligation is met by writing this record and all commits in English, per that skill's own convention rather than a Skill-tool invocation).

## Open findings

None.

## Next steps

None — both issues' acceptance criteria are addressed in this same PR.
