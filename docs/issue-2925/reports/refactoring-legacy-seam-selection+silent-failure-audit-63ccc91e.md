---
issue: 2925
role: refactoring-legacy-seam-selection+silent-failure-audit-63ccc91e
author: refactoring-legacy-seam-selection+silent-failure-audit-63ccc91e
skills: refactoring-legacy-seam-selection (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false
loop_state: done
code_under_review: this session's own patrol-removal diff (14 files, 51 insertions, 2003 deletions)
type: removal
breaking: true
verdict: accepted
upstream:
  - path: gates/precision_measure.py
    sha: same-commit
  - path: on-the-record/monitors/poll-heartbeat.sh
    sha: same-commit
---

# issue-2925 — refactoring-legacy-seam-selection+silent-failure-audit-63ccc91e record

## What was done

Removed the patrol program in full, per the operator decision recorded in issue #2925. Deleted:

- `gates/patrol_board.py`, `gates/patrol_promote.py`, `gates/patrol_queue.py`, `gates/patrol_trigger.py`, `gates/patrol_wiring.py` — the five modules named in the issue, 1,326 lines total per the issue's own count. All five paths were deleted in this commit and no longer exist in the working tree. `derived: git status --short -- gates/patrol_board.py gates/patrol_promote.py gates/patrol_queue.py gates/patrol_trigger.py gates/patrol_wiring.py` shows `D` (deleted) for all five.
- `gates/precision_measure.py` — deleted in this commit, no longer exists in the working tree; not in the issue's original five-module list, but its only functional entry point (`_population()`/`cmd_sample`) called `patrol_queue.scan_record_lint`, `patrol_queue._finding_rule_id`, and `patrol_queue.SWEEP_DISABLED_RULES` directly. Its docstring states its purpose was measuring precision of the patrol sweep-lane scanner (issue #1614 requirement 3, "frozen from the issue #1614 measurement, 2026-08-16") to gate patrol's promote decision. The module's other half (`stratified_sample`, `wilson_lower_bound`, `build_report`, `format_report`, `cmd_report`) is statistics code with no patrol dependency, but `derived: git grep -rn "precision_measure" -- . ':!docs' ':!gates/precision_measure.py'` returns no importers anywhere in the repo — nothing else calls `cmd_report` or feeds it a samples/judgments file. With `cmd_sample` (the only producer of that input) gone, keeping the file would leave a CLI with one dead subcommand and no callers, which is the dormant-copy shape the issue's must-not list forbids more directly than deleting it does. Full removal, not a partial resolve.
- `on-the-record/monitors/test_poll_heartbeat.py`: the fixtures `FAKE_SPAWN_PY_WITH_SKILLS`, `FAKE_PATROL_PROMOTE_PY`, helper `_run_patrol_tick`, and six patrol-specific tests, 248 lines. All remaining tests in that file pass — `derived: python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -v` — 27 passed.

Edited (patrol machinery removed, everything else preserved):

- `on-the-record/monitors/poll-heartbeat.sh` — removed `patrol_tick`, `POLL_HEARTBEAT_PATROL_EVERY_N`, the roster/role_data lookup (`spawn.role_data()` via `IFS=' ' read -r -a POLL_HEARTBEAT_PATROL_SKILLS <<<"$(python3 -c ...)" 2>/dev/null` — the exact silently-failing call the issue names), the per-skill loop that called `gates/patrol_promote.py` (deleted in this commit, no longer exists), the `[patrol-poll]` printf lines, and the `_patrol_count` JSON-parse fallback (`except (ValueError, TypeError): d = {}`). `derived: git diff --stat HEAD -- on-the-record/monitors/poll-heartbeat.sh` shows 94 net lines removed. Three stray comment lines (around old lines 180, 181, and 187) that cited `patrol_promote.py`/`POLL_HEARTBEAT_PATROL_ROLES` inside an unrelated `#2163` checkout-guard comment block were rewritten to describe the `spawn.py` subprocess calls that actually exist now, without changing the guard's own (non-patrol) logic. `derived: git grep -rni patrol -- . ':!docs'` after this edit returns only one unrelated hit (below, in "Acceptance").
  - `#2919`'s own fix is not present on this branch. `derived: git merge-base --is-ancestor acd74b3b HEAD` (the `#2919` fix commit) reports it is NOT an ancestor of this branch's HEAD — it lives only on `origin/issue-2919/...`, unmerged here. `derived: git log --oneline -- on-the-record/monitors/poll-heartbeat.sh` shows no `#2919` commit in this file's history on this branch. So there was no second, non-patrol `#2919`-added visibility line in this file to preserve; the only `#2919`-shaped content that could exist here (the patrol-query failure line) is exactly what this removal deletes.
- `consult.py` — real dependency, resolved: `_judge_trace_path()` returned `runs/patrol-judge-log.md`, renamed to `runs/judge-log.md` (`derived: git grep -rn "runs/patrol-judge-log" -- .` confirms no other file hardcoded the old path). `_judge_validate()`'s docstring dropped a "patrol 큐 오염" (patrol queue contamination) reference for a generic "결과 오염" (result contamination) wording. `judge_cmd()`'s enqueue stage removed `import patrol_queue` and its `load_queue/verify/fingerprint/enqueue/save_queue` calls (the literal patrol promotion queue write path, `.on-the-record/findings/queue.jsonl`), reimplementing the one safeguard worth keeping — re-reading the cited path and confirming the excerpt is verbatim present, guarding against hallucinated findings — inline with `Path.read_text()` + substring check. The return dict's `"enqueued"` key was renamed to `"findings"` since nothing is enqueued anywhere anymore. This session identified and fixed, in the same build, two early-return paths (around lines 1537 and 1542) that had been left still returning the stale `"enqueued": []` key while the success path returned `"findings"` — an inconsistent schema within the same function. `derived: python3 -m py_compile consult.py` is clean after the fix; `derived: git grep -rn "\"enqueued\"" -- . ':!docs'` returns nothing. The only caller, `spawn.py:2651`, JSON-prints the dict verbatim and does not key into it, so this was a latent inconsistency rather than a live crash, but left as found it would have produced a schema that silently differed between the zero-findings and some-findings cases. Edit kept minimal and scoped to the patrol reference only, per the issue's note that #2920 lands in parallel and also touches `consult.py`.
- `gates/gh_rest.py` — two dangling comment/docstring citations of `patrol_board.find_board_issue`'s request pattern and a `patrol_board.py:239-243` file:line reference, reworded to describe the `gh api -i` + `If-None-Match` + 304 pattern and its pitfall without citing a deleted file. No functional code referenced patrol.
- `gates/record_lint.py` and `on-the-record/gates/record_lint.py` (byte-identical mirrors) — `find_records()`'s docstring said `sweep_cutoff`'s default matched "this function's only callers: `main()`'s directory mode and `patrol_queue`'s sweep-lane scanner"; updated to "this function's only caller: `main()`'s directory mode" since the `patrol_queue` caller is gone. `derived: grep -n "find_records(" gates/record_lint.py` shows one remaining caller, `main()`. No functional code referenced patrol.
- `on-the-record/hooks/gh-write-allow-gate.sh` — the `("gh", "issue", "edit")` `VERB_SHAPES` entry was commented as existing solely for "issue #1586: patrol-board edit-in-place." `derived: grep -n "gh issue edit" on-the-record/commands/run.md` shows this verb shape is still live for an unrelated purpose (editing a requirement issue's execution-plan block in place); only the stale comment attribution was corrected, the verb-shape entry itself stays. `derived: bash -n on-the-record/hooks/gh-write-allow-gate.sh` is clean.
- `on-the-record/commands/run.md` — removed the post-merge paragraph instructing the orchestrator to run `python3 gates/patrol_wiring.py run <repo-root> <merge-sha>` (that path no longer exists) and describing its `.on-the-record/patrol-disabled` kill-switch; that entry point is gone. Surrounding merge/close bullets left intact.
- `test/test_retirement_count.py` — no change. Its one "patrol" hit (`retirement_count.line_hits("patrol the controller")`) is an ordinary English test string checking that "patrol" is not mistakenly flagged as containing "role" — unrelated to the patrol program. `derived: python3 -m pytest test/test_retirement_count.py -q` — 16 passed.

## Why

Operator decision (issue #2925, 2026-08-31): the patrol promotion path never once ran. `spawn.role_data()`, which `poll-heartbeat.sh` used to fetch the patrol-skill roster (wired in `#1598`/`#2560`), never existed — `role_data` is retired-axis vocabulary left behind when that axis was removed. Every tick's roster query threw `AttributeError`, silently swallowed by `2>/dev/null`, since the feature landed; the promotion script this fed, `gates/patrol_promote.py` (deleted in this commit, no longer exists), was consequently invoked for zero skills, ever. The job patrol was built to do — surfacing findings and turning approved ones into issues — is already handled by spawned sessions, their independent verifications, and the orchestrator filing what they surface (this session's own parent pipeline is an instance of that path). Repair was rejected because there is no drop-in replacement API (`spawn.py` exposes `_roster_load`, `ROSTER`, `_STATIC_POLICY_SKILLS`, `_installed_plugin_skill_dirs` — none equivalent), repair would still need re-validating rate caps and anti-loop guards for a mechanism with zero demonstrated demand, and a repaired-but-still-silent failure mode was exactly what produced this issue.

Work was fanned out across three independently-owned file groups (5 patrol modules + import-safety grep; `poll-heartbeat.sh` + its test, coupled by the test needing to track the trimmed script; the 8 other referencing files, each requiring individual inspection rather than a blind find-replace) plus a fourth verification round, per this session's freelunch-directive tally. This session then re-verified independently — final grep sweep, both Monitor tick runs, the `consult.py` schema-consistency fix, the `precision_measure.py` deletion-scope justification — rather than taking delegated worker reports at face value, given the number of "must not break" constraints at stake. `derived: git log -1 --stat HEAD` is this session's own commit carrying the 14-file diff enumerated above.

## What did not work

None — no dead ends, no reverted approach, no wrong turn abandoned mid-task. One correctness gap was identified and fixed within this session's own build, not after landing: `consult.py`'s `judge_cmd()` had two early-return paths still returning the stale `"enqueued": []` key while its success path had been rewritten to return `"findings"`. `derived: git diff HEAD -- consult.py` shows both `return` statements now reading `"findings": []`, matching the success path's key. Caught and fixed in this same commit before shipping, not a deviation from the approach taken.

## Upstream basis

No upstream doc record from a prior role under this issue's own reports directory — this record's basis is the issue #2925 body itself (read via `gh issue view 2925`) and this session's own investigation of the live tree. `precision_measure.py`'s scope (delete rather than resolve) and `poll-heartbeat.sh`'s exact patrol boundaries were determined by reading the files in this same commit (`sha: same-commit` for both, per contract §1).

## Open findings

None. `derived: git grep -rni patrol -- . ':!docs'` (final sweep, repeated in "Acceptance" below) returns only the one unrelated `test_retirement_count.py` hit, so no follow-up issue is warranted for leftover patrol surface. The one adjacent inconsistency this session identified (`consult.py`'s return-key mismatch) was fixed in this same commit rather than deferred, per "What did not work" above.

## Next steps

None. This record's frontmatter `loop_state` above carries this session's terminal state for a build-now (`CORE_BUILD_NOW=1`) session: code and record land together in one PR, per the acceptance checks below.

## Acceptance

Every check below is executed live in this session; `derived: git log -1 --format=%H` pins the commit this evidence was gathered against.

- **`grep -rn patrol` over live code, excluding `docs/`, zero remaining references.**
  Bounded as: `git grep -rni patrol -- . ':!docs'` — tracked files only (matches the issue's "live code" framing; untracked scratch/build artifacts are not "live code"), case-insensitive, `docs/` excluded per the must-not list.
  `acceptance: git grep -rni patrol -- . ':!docs' — result:`
  ```
  test/test_retirement_count.py:44:        self.assertFalse(retirement_count.line_hits("patrol the controller"))
  ```
  This is not a patrol-program reference (see "What was done" above) — it is an English test string used to check a `retirement_count` string-matcher doesn't false-positive on "patrol" containing "role". Handled by inspection, not skipped, and left as-is because acting on it would mean changing unrelated test data, not resolving a patrol reference.

- **A Monitor tick runs correctly with the patrol machinery removed, exit 0, under both default bash and bash 3.2.**
  - Default bash: `acceptance: bash -n on-the-record/monitors/poll-heartbeat.sh — result:` syntax OK. `acceptance: TOKENMAXXXER_CHECKOUT=<empty-checkout> POLL_HEARTBEAT_MAX_TICKS=1 POLL_HEARTBEAT_SLEEP_SECONDS=0 FAKE_POLL_DUE=1 HOME=<fresh-home> bash on-the-record/monitors/poll-heartbeat.sh; echo EXIT:$? — result:`
    ```
    poll tick: due, watchdog ran (rc=0, no output)
    EXIT: 0
    ```
  - Bash 3.2 — the platform issue `#2919` identified as sensitive: `acceptance: docker run --rm -v "$(pwd)/on-the-record:/otr:ro" -v <checkout>:/w/checkout:ro bash:3.2 sh -c 'bash --version; bash -n /otr/monitors/poll-heartbeat.sh; export TOKENMAXXXER_CHECKOUT=/w/checkout POLL_HEARTBEAT_MAX_TICKS=1 POLL_HEARTBEAT_SLEEP_SECONDS=0 FAKE_POLL_DUE=1 HOME=/w/home; mkdir -p /w/home; bash /otr/monitors/poll-heartbeat.sh; echo EXIT:$?' — result:`
    ```
    GNU bash, version 3.2.57(1)-release (x86_64-pc-linux-musl)
    SYNTAX OK under bash 3.2
    EXIT: 0
    ```
    A "Read-only file system" line appeared for a lock file because this session's checkout mount was read-only for this ad hoc check, not a code defect — the tick still exited 0 regardless.
  - `derived: python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py test/test_retirement_count.py -q` shows 43 passed.

- **The record names the capability being dropped and shows no other path depended on it.**
  Capability dropped: board-line promotion — turning an approved (checkbox-checked) board line into a structured GitHub issue, subject to rate caps — the entire job of `gates/patrol_promote.py`, queued via `gates/patrol_queue.py`, triggered via `gates/patrol_trigger.py` and `gates/patrol_wiring.py`, sourced from `gates/patrol_board.py` — all five deleted in this commit, no longer exist in the working tree. `acceptance: git grep -rn "patrol_promote\|patrol_queue\|patrol_trigger\|patrol_wiring\|patrol_board" -- . ':!docs' — result:` no importers outside the 10 files issue #2925 named up front, each individually inspected and catalogued in "What was done" above rather than assumed safe to touch. The roster/role_data query this program depended on never worked in the first place (`AttributeError` since inception, per the issue), so the promotion path had zero live consumers to migrate.

## must-not compliance

- `docs/` untouched: `derived: git status --short -- docs/` shows only the new docs/issue-2925 directory (this record's own area); no existing `docs/` file was modified.
- No stub/shim/disabled-flag left behind: all five named modules plus `gates/precision_measure.py` (both no longer exist in the working tree) are fully `git rm`'d, not emptied or flag-gated.
- No name-prefix false positives removed: each of the 10 referencing files was inspected individually and its reference characterized in "What was done" (real dependency in `consult.py`/`gates/precision_measure.py`; stale-comment-only in `gates/gh_rest.py`/`gates/record_lint.py`/`on-the-record/gates/record_lint.py`/`on-the-record/hooks/gh-write-allow-gate.sh`/`on-the-record/monitors/poll-heartbeat.sh`; doc-workflow-step in `on-the-record/commands/run.md`; unrelated test string in `test/test_retirement_count.py`).
- `record_lint.py`, `gh_rest.py`, `precision_measure.py` (its non-patrol half had zero callers, see above), `consult.py`, `gh-write-allow-gate.sh`: none broken. `derived: python3 -m py_compile consult.py gates/gh_rest.py gates/record_lint.py on-the-record/gates/record_lint.py` is clean; `derived: bash -n on-the-record/hooks/gh-write-allow-gate.sh` is clean; existing test suites for the touched files pass (43 passed, above).
- The `#2919` non-patrol visibility line: not present on this branch to weaken (see "What was done" — `#2919`'s fix commit is unmerged here).
- No per-tick overhead increase: pure deletions from the tick loop plus comment-only rewrites; no new work added.
- No watch-family signal made blockable/droppable/advisory-only: `poll-heartbeat.sh`'s due-check and watchdog paths are untouched in behavior; only the patrol branch was removed.
- No retired-axis identifier reintroduced: `derived: git grep -rn "role_data" -- . ':!docs'` returns nothing.
- `consult.py` kept minimal for `#2920` coexistence: only the patrol reference (trace path, docstring wording, enqueue-to-findings rewrite) was touched; no other function in the file was modified.

skill-verdict: refactoring-legacy-seam-selection — applied: invoked; used to decide the seam for `consult.py`'s `judge_cmd()` — the patrol-queue call was Sprout/Wrap-replaced in place (inline re-verification of cited excerpts) rather than introducing a new abstraction layer, since the call site had no tests and the safeguard being preserved (anti-hallucination excerpt check) was small enough to inline directly at the seam `patrol_queue.verify()` occupied.
skill-verdict: silent-failure-audit — applied: invoked; used to catalogue `poll-heartbeat.sh`'s patrol-path failure handling before deletion (the `2>/dev/null`-swallowed `AttributeError` and the `except (ValueError, TypeError): d = {}` fallback that made a malformed payload indistinguishable from zero promotions) and to catch the `consult.py` `judge_cmd()` return-schema inconsistency (`"enqueued"` vs `"findings"` across early-return paths) introduced mid-edit before it shipped.
other mounted skills: not triggered.
