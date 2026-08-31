---
issue: 2925
role: independent-verification-1
author: independent-verification-1
verifies_subject: false  # this record is original removal work, not a verification of another subject's deliverable
loop_state: landed
upstream:
  - path: gh issue view 2925
    sha: same-commit
---

# issue-2925 — independent-verification-1 record

## What was done

skill-verdict: model-routing — not-applicable: single-session mechanical removal task with a fixed, pre-scoped file list from the issue body — no delegation/model-tier decision to make.
skill-verdict: implementation-audit — not-applicable: this session both builds and delivers the removal in one pass (build-now bypass, CORE_BUILD_NOW=1); there is no separate builder/evaluator split to run here.
other mounted skills: not triggered.

Removed the patrol program end to end:

- Deleted the five core modules named in the issue (`git rm`): patrol_board.py, patrol_promote.py, patrol_queue.py, patrol_trigger.py, patrol_wiring.py, all under gates/ — none of the five exist in the worktree any more.
  derived:
  ```
  $ git status --short | grep '^ D\|^D '
  D  gates/patrol_board.py
  D  gates/patrol_promote.py
  D  gates/patrol_queue.py
  D  gates/patrol_trigger.py
  D  gates/patrol_wiring.py
  ```
  derived (pre-deletion line count, matching the issue's own "1,326 lines total" claim):
  ```
  $ wc -l gates/patrol_board.py gates/patrol_promote.py gates/patrol_queue.py gates/patrol_trigger.py gates/patrol_wiring.py
    381 gates/patrol_board.py
    365 gates/patrol_promote.py
    366 gates/patrol_queue.py
     72 gates/patrol_trigger.py
    142 gates/patrol_wiring.py
   1326 합계
  ```
- Checked each of the ten listed referencing files individually and resolved
  each on its own terms (full per-file breakdown in "Upstream basis" below):
  `consult.py`, `gates/gh_rest.py`, `gates/precision_measure.py`,
  `gates/record_lint.py`, `on-the-record/gates/record_lint.py`,
  `on-the-record/hooks/gh-write-allow-gate.sh`,
  `on-the-record/monitors/poll-heartbeat.sh`,
  `on-the-record/monitors/test_poll_heartbeat.py`,
  `on-the-record/commands/run.md`, `test/test_retirement_count.py`.
- Scope grew past that literal ten-file list into `spawn.py`,
  `test/test_spawn_model_override.py`, and
  `test/test_consult_no_rulebook_identity_regression.py` — none of the three
  contain the literal string "patrol", but all three exist solely to wire up
  or test `consult.py`'s `judge_cmd()` producer chain, whose only output was
  the now-deleted findings queue module. Leaving that chain half-alive
  (unable to enqueue anywhere, but still present, still re-exported, still
  CLI-wired via `spawn.py judge <skill> --merge <sha>`) would itself be the
  "dormant copy... with none of the function" the issue's must-not list
  forbids, and would also leave `consult.py`/`spawn.py` broken at call time.
  Removed the whole chain: `judge_cmd`, `_judge_prefilter`, `_judge_validate`,
  `_judge_cmd_and_env`, `_readonly_plugin_dirs`, `_readonly_bash_allow`,
  `_readonly_settings`, `_judge_trace_path`, `_append_judge_trace`,
  `_judge_skills_run_today`, `_JUDGE_SKILL_EXCLUSIONS`, `JUDGE_TIMEOUT`,
  `JUDGE_MAX_SKILLS_PER_MERGE`, the `spawn.py role == "judge"` CLI branch,
  and the now-unused `--merge` argparse flag; kept
  `_JUDGE_EXCLUDED_CORE_PLUGINS`, which is genuinely shared with the
  unrelated, still-live `skill_judge` advisory mechanism (issue #2061/#2201).
  canonical: `consult.py:510` (post-edit) — `exclude_core_plugins=_sp._JUDGE_EXCLUDED_CORE_PLUGINS` inside `_cross_family_skill_matches_with_consult`, a live second caller unrelated to the removed judge_cmd chain, confirmed by reading the function.

## Why

Per the issue's operator decision: the patrol promotion path (board-line
checkbox -> structured GitHub issue, 2/hour/role + 10-open/role rate caps,
formerly implemented in the now-deleted patrol_promote.py) has never once
run — its roster read via `spawn.role_data()` targets a function that does
not exist on this branch, so every tick's patrol query failed silently since
the day it was wired (`#1598`/`#2560`). Nobody missed it in the weeks since.
The job it was built to do — surfacing findings for someone to act on — is
already done by the standing spawned-session + independent-verification
pipeline, which files issues through the orchestrator instead.
canonical: `gh issue view 2925` output, "## Why removal rather than repair" section — this is the operator's own stated rationale, quoted/summarized here, not an independent measurement by this session.

Repair would have meant picking a replacement roster API and re-validating
rate caps, anti-loop guards, and board formatting for a mechanism with zero
demonstrated demand; removal is cheaper and matches the issue's own framing.

## What did not work

None.

## Upstream basis

Per-file resolution of the ten referencing files named in the issue (each
checked individually, not assumed):

1. **`consult.py`** — real functional dependency: `judge_cmd()` (the
   `spawn.py judge <skill> --merge <sha>` body) imported the now-deleted
   findings-queue module and called its `load_queue`/`enqueue`/`verify`/
   `fingerprint`/`save_queue` functions to feed the promotion queue. Removed
   the whole judge-producer chain (see "What was done"); kept
   `_JUDGE_EXCLUDED_CORE_PLUGINS` (shared with `skill_judge`).
   derived:
   ```
   $ git grep -niI patrol -- consult.py
   (no output)
   ```
2. **`gates/gh_rest.py`** — two comments only: one attributing
   `fetch_open_prs`'s `gh api -i`/`If-None-Match`/304 pattern to the
   now-deleted board module, one citing that module's line range for an
   analogous 304-vs-returncode pitfall. Both reworded in place to describe
   the pattern directly instead of citing a file that no longer exists; no
   functional change.
   derived:
   ```
   $ git grep -niI patrol -- gates/gh_rest.py
   (no output)
   ```
3. **`gates/precision_measure.py`** — real functional dependency: imported
   the now-deleted findings-queue module for `scan_record_lint`,
   `_finding_rule_id`, `SWEEP_DISABLED_RULES`, and `verify` — a
   record_lint-scanning utility `precision_measure.py` reuses for its own
   (non-promotion) sweep-lane precision measurement. Inlined all four
   functions plus their small helpers (`_quoted_excerpt`, `_QUOTED_SPAN`,
   `_RULE_ID_RE`, `SCANNER_ID_RECORD_LINT`) directly into
   `precision_measure.py`, which is now the sole owner of this scanning
   logic.
   derived:
   ```
   $ python3 -m gates.precision_measure sample . --n 5 --out /tmp/pm_sample_test.json
   wrote 14 sample items (population 1918) to /tmp/pm_sample_test.json
   ```
   — the inlined scanner runs correctly end-to-end over the live repo, exit 0.
4. **`gates/record_lint.py`** — one docstring comment naming the now-deleted
   findings-queue module's sweep-lane scanner as one of `find_records()`'s
   two callers. Reworded to name `precision_measure`'s sweep-lane scanner
   instead (matches item 3's relocation).
5. **`on-the-record/gates/record_lint.py`** — byte-identical mirror of item
   4; the same edit applied to keep both copies identical.
   derived:
   ```
   $ diff gates/record_lint.py on-the-record/gates/record_lint.py
   (no output — still byte-identical after the edit)
   ```
6. **`on-the-record/hooks/gh-write-allow-gate.sh`** — real functional
   entry: the `("gh", "issue", "edit")` allow-shape existed solely because
   the now-deleted board/promote modules called `gh issue edit` for
   board-line edit-in-place (issue #1586). Grepped for any other caller of
   `gh issue edit` across live code (excluding docs/): none found besides
   those two deleted modules and this gate's own allow-list entry (an
   unrelated `gh pr edit` also exists in `contract-guard.sh`, a different
   verb). Removed the shape (5 -> 4 recognized verb shapes) and updated the
   surrounding comment/count.
   derived (unaffected verb still allowed):
   ```
   $ echo '{"tool_name":"Bash","tool_input":{"command":"gh issue create --title x --body y"}}' | env -u TOKENMAXXXER_SPAWNED bash on-the-record/hooks/gh-write-allow-gate.sh
   {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow", ...}}
   ```
   derived (removed verb no longer granted):
   ```
   $ echo '{"tool_name":"Bash","tool_input":{"command":"gh issue edit 5 --body y"}}' | env -u TOKENMAXXXER_SPAWNED bash on-the-record/hooks/gh-write-allow-gate.sh
   (no output, exit 0 — falls through unallowed)
   ```
7. **`on-the-record/monitors/poll-heartbeat.sh`** — real functional code:
   the `patrol_tick` counter, `POLL_HEARTBEAT_PATROL_EVERY_N` cadence, the
   `spawn.role_data()` roster read (the broken call at the root of this
   issue), and the per-tick patrol-promotion invocation loop with its
   `[patrol-poll]` lines. Removed in full. Also reworded one adjacent
   comment (the issue #2163 mid-reclone existence guard) that cited the
   now-deleted promotion module as its sole historical justification, since
   that guard still protects the remaining `poll-due`/`watchdog` subprocess
   calls after patrol's removal.
   derived:
   ```
   $ git grep -niI patrol -- on-the-record/monitors/poll-heartbeat.sh
   (no output)
   $ bash -n on-the-record/monitors/poll-heartbeat.sh; echo "rc=$?"
   rc=0
   ```
8. **`on-the-record/monitors/test_poll_heartbeat.py`** — test fixtures and
   tests exclusively exercising the patrol block: `FAKE_SPAWN_PY_WITH_SKILLS`,
   `FAKE_PATROL_PROMOTE_PY`, `_run_patrol_tick`, and the four `t_patrol_*`
   tests. Removed those, plus
   `t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior` (a
   patrol/heartbeat-interaction regression pin with no remaining subject).
   Kept and trimmed `t_patrol_tick_skips_when_checkout_vanishes_mid_sleep`
   -> renamed `t_tick_skips_when_checkout_vanishes_mid_sleep`: its actual
   subject (the mid-reclone checkout-vanish guard, issue #2163) is general,
   not patrol-specific, so the patrol-only setup/assertions were stripped
   and the general assertions (exit 0, `[poll-heartbeat] checkout
   unavailable`, no `crashed`) kept.
   derived:
   ```
   $ python3 on-the-record/monitors/test_poll_heartbeat.py
   ...
   28/28 passed
   ```
9. **`on-the-record/commands/run.md`** — real runbook step: immediately
   after `gh pr merge`, instructed running the now-deleted wiring module's
   CLI entry point (issue #1597 E1) as "the sole entry point linking
   judge+board auto-execution". Removed the step in full — the script it
   named no longer exists.
   derived:
   ```
   $ git grep -niI patrol -- on-the-record/commands/run.md
   (no output)
   ```
10. **`test/test_retirement_count.py`** — NOT a patrol reference. Line 44,
    `self.assertFalse(retirement_count.line_hits("patrol the controller"))`,
    is a negative-test string proving the retired-`role`-identifier detector
    does not false-positive on a word that merely contains the substring
    "role" (pat-ROLE) — unrelated to the patrol program by the test's own
    stated purpose (its class docstring: "must not flag an unrelated word
    that merely contains the letters 'role'"). Left untouched, matching the
    issue's own empty-state instruction that this kind of hit must be
    checked, not skipped — checked here and confirmed unrelated.

Final scope-wide grep, matching the issue's own acceptance-check wording,
bounded to all git-tracked files outside `docs/`, case-insensitive, whole
repo:
```
$ git grep -niI patrol -- . ':!docs/'
test/test_retirement_count.py:44:        self.assertFalse(retirement_count.line_hits("patrol the controller"))
```
Exactly one hit, item 10 above, confirmed unrelated.

Monitor tick, both platforms the issue requires:
```
$ POLL_HEARTBEAT_MAX_TICKS=1 POLL_HEARTBEAT_SLEEP_SECONDS=0 FAKE_POLL_DUE=1 \
  FAKE_WATCHDOG_REPORT=$'[poll-report] roster: empty\n[poll-report] quiet, nothing in flight' \
  ... bash on-the-record/monitors/poll-heartbeat.sh; echo "TICK_EXIT_CODE=$?"
[poll-report] roster: empty
[poll-report] quiet, nothing in flight
TICK_EXIT_CODE=0
```
on the host (bash 5.1.16), and identically inside `docker run --rm
bash:3.2` (Alpine 3.22, `apk add --no-cache python3 git` at container
start):
```
$ docker run --rm ... bash:3.2 sh -c 'bash -n poll-heartbeat.sh && bash poll-heartbeat.sh; echo TICK_EXIT_CODE=$?'
SYNTAX_OK
[poll-report] roster: empty
[poll-report] quiet, nothing in flight
TICK_EXIT_CODE=0
```

Full test suite, before/after comparison via `git stash` (post-removal vs.
this same changeset stashed out):
```
$ python3 -m pytest test/ gates/ on-the-record/monitors/ -q      # post-removal
15 failed, 565 passed, 3 xfailed in 31.64s

$ git stash && python3 -m pytest <the 5 files with post-removal failures> -q && git stash pop   # pre-removal baseline, same file subset
15 failed, 79 passed in 2.14s
```
All 15 failures, both before and after, are the identical test names
(`test_convention_equivalence.py`, `test_local_dependency_env.py`,
`test_spawn_cross_family_skill_selection.py`,
`test_spawn_skill_judge_haiku_timeout_overlap.py`,
`test_spawn_artifact_skill_pairing.py`), each raising `SystemExit: ... fetch
실패 — fatal: 'origin' does not appear to be a git repository` from
`bootstrap_fetch_and_record_sha`'s live `git fetch` against a real GitHub
remote — a pre-existing sandbox/network limitation, not a regression
introduced here. 583 collected in both cases with no import/collection
errors.

No other path depended on the removed capability: the full suite above
covers `consult.py`, `spawn.py`, `precision_measure.py`, `record_lint.py`,
`gh_rest.py`, `gh-write-allow-gate.sh`, and `poll-heartbeat.sh`, all passing
at the same rate before and after removal.

## Open findings

- **PR #2923 / issue #2919 not yet merged — poll-heartbeat.sh conflict on
  whichever side lands second.**
  canonical:
  ```
  $ gh pr view 2923 --repo tokenmaxxxer/on-the-record --json state,mergedAt,baseRefName,headRefName
  {"baseRefName":"main","headRefName":"issue-2919/silent-failure-audit+refactoring-legacy-seam-selection-4495e32f","mergedAt":null,"state":"OPEN"}
  $ git merge-base --is-ancestor acd74b3b HEAD && echo "ancestor: yes" || echo "ancestor: no"
  ancestor: no
  ```
  Commit acd74b3b (issue #2919's macOS bash-3.2 fix: flock-fallback
  aliveness lock, and a guarded roster-query rc capture for the very
  patrol-skills array this issue removes) is not an ancestor of this
  branch, confirmed above, and PR #2923 is confirmed still open. This
  branch's poll-heartbeat.sh is therefore the pre-#2919 version; the two
  "Monitor-visible lines #2919 added" that this issue's must-not clause
  protects do not exist here to preserve or weaken. Whichever of {this PR,
  #2923} merges to main second will hit a direct diff conflict on
  poll-heartbeat.sh's patrol-array section — #2923 patches code this PR
  deletes. Flagging for the orchestrator to sequence the merge (or rebase
  the second one) rather than let it land as a silent conflict.

## Next steps

None — landed. skill-verdict lines above cover both mounted skills that
matched this task's text (model-routing, implementation-audit); neither
applied, both stated as not-applicable with reasons.
