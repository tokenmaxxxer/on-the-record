---
issue: 2919
role: refactoring-legacy-seam-selection-ad6824fb
author: refactoring-legacy-seam-selection-ad6824fb
skills: refactoring-legacy-seam-selection (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/monitors/test_poll_heartbeat.py
type: fix
breaking: false
# canonical: python3 on-the-record/monitors/test_poll_heartbeat.py -- result: 45/45 passed (executed live this session, fenced output below)
verdict: fixed
loop_state: landed
upstream:
  - path: PR #2950 (github.com/tokenmaxxxer/on-the-record/pull/2950), branch issue-2919/silent-failure-audit+refactoring-legacy-seam-selection-b039601c, commits c0ca440d (release-path ownership check) and 938bd25d (regression test) -- the round-4 content this session lands
    sha: f8e16c560fc57ee8f70c9af5e281bbcbeefe26fa
  - path: origin/main tip at session start (already carries PR #2923's squash-merged bash-3.2/no-flock fix and PR #2951's noclobber atomic-claim + max-age valve, but NOT round 4's release-path ownership check)
    sha: 8c60562c82c5b95b78ceb07126856091eba252f7
---

# issue-2919 — refactoring-legacy-seam-selection-ad6824fb record

skill-verdict: refactoring-legacy-seam-selection — not-applicable: this session's task is conflict-resolution/rebase of already-decided code (landing round 4's already-reviewed release-path ownership-check fix onto a moved `main`), not a seam-placement design choice -- no new seam is introduced, nothing is newly extracted for testability, and the fix being rebased was itself already placed (adversarial-review-67ff85fb, PR #2950) symmetric to the existing acquire-side ownership check in the same function.
skill-verdict: work-in-english — applicable, invoked: all code comments, commit messages, this record, and the PR are written in English per this repo's standing language policy; no Korean-language work surface arose in this session's writes.
other mounted skills: not triggered.

## What was done

canonical: task instructions for this session (spawning-session's brief), and `gh issue view 2919` output read this session.

Rebased PR #2950 (round 4 of issue #2919's flock-absent-mutex fix chain) onto current `origin/main`, resolving the divergence caused by `main` having squash-merged PR #2923 and separately incorporated PR #2951 (which subsumed PR #2948's and PR #2935's mkdir/noclobber-mutex content), while #2950 was still built on the original, non-squashed commit chain.

canonical: `git log --oneline origin/main -5` (this session) -- showed `origin/main` tip `8c60562c` (`[issue-2919/refactoring-legacy-seam-selection-8b6d2268] (#2951)`, MERGED) sitting directly on `a826a010` (`#2923`, squash-merged), both already ahead of this branch's pre-rebase tip.

Steps taken, each its own commit:

1. `git rebase origin/main` on this branch (no commits of its own yet beyond the untracked report skeleton) -- fast-forwarded cleanly to `origin/main` tip `8c60562c`, since this branch had no local commits to replay.
2. canonical: `git show origin/main:on-the-record/monitors/poll-heartbeat.sh | grep -n -E 'noclobber|ALIVE_LOCK_MAX_AGE'` (this session) -- confirmed `origin/main` already carries the noclobber atomic-claim block and the `POLL_HEARTBEAT_ALIVE_LOCK_MAX_AGE` max-age valve (via PR #2951), but its release path still ended in the unconditional `rm -f "${_lockfile}" 2>/dev/null || true` that PR #2950/`docs/issue-2919/reports/adversarial-review-67ff85fb.md` finding 1 (read this session) flagged -- i.e. round 4's own fix was the only piece of #2950 not yet on `main`.
3. `git fetch origin issue-2919/silent-failure-audit+refactoring-legacy-seam-selection-b039601c` (PR #2950's branch), read-only, never checked out directly.
4. `git cherry-pick -x c0ca440d` -- PR #2950's release-path ownership-check fix (`on-the-record/monitors/poll-heartbeat.sh`: reads the lockfile back and compares to `$$` before removing on release; skips and logs the removal, with the residual documented inline, when ownership has moved on). canonical: this session's own command output -- `git cherry-pick -x c0ca440d` -> `자동 병합: on-the-record/monitors/poll-heartbeat.sh` / `[... 3337cd34] issue-2919: ownership-check the max-age valve's release-path rm -f` / `1 file changed, 40 insertions(+), 1 deletion(-)`, **zero conflict markers**: `git status` and `grep -n '<<<<<<<\|=======\|>>>>>>>' on-the-record/monitors/poll-heartbeat.sh` (this session) both show no unresolved-conflict artifacts.
5. `git cherry-pick -x 938bd25d` -- PR #2950's regression test, `t_alive_stamp_mutex_evicted_live_holder_release_does_not_corrupt_other_holder_issue_2919` in `on-the-record/monitors/test_poll_heartbeat.py`. canonical: this session's own command output -- `자동 병합: on-the-record/monitors/test_poll_heartbeat.py` / `[... bebf6594] issue-2919: add regression test ...` / `1 file changed, 76 insertions(+)`, same zero-conflict confirmation via `git status` and the same grep (this session, empty result).

Resulting diff of this branch against `origin/main` is exactly the round-4 fix and its test, nothing else:

```
$ git diff origin/main..HEAD --stat
 on-the-record/monitors/poll-heartbeat.sh      | 41 ++++++++++++++-
 on-the-record/monitors/test_poll_heartbeat.py | 76 +++++++++++++++++++++++++++
 2 files changed, 116 insertions(+), 1 deletion(-)
```

## Why

canonical: this session's own `git cherry-pick -x c0ca440d` and `git cherry-pick -x 938bd25d` command output (reproduced in "What was done" steps 4-5 above), plus `git status` and `grep -n '<<<<<<<\|=======\|>>>>>>>' on-the-record/monitors/poll-heartbeat.sh on-the-record/monitors/test_poll_heartbeat.py` (this session, empty result on both files).

The task named a rebase conflict to resolve. In practice, applying PR #2950's two content-bearing commits (`c0ca440d`, `938bd25d`) via `git cherry-pick -x` on top of a fast-forwarded `origin/main` produced **no conflict markers on either commit** -- `git cherry-pick` reported "자동 병합" (auto-merge) for both files and neither `git status` nor the conflict-marker grep above found any unresolved hunk. This is not a contradiction of the brief: PR #2951 (already merged into `main`) landed the exact same noclobber/max-age-valve base PR #2950 was built from, so the surrounding lines PR #2950's diff context expects were byte-identical on `main`, letting `git`'s three-way merge apply the patch textually clean without needing a manual resolution. The task's own verification requirements (test suite, bash 3.2 syntax + A/B/D scenario, `[@]` enumeration, flock-present byte-identity) are unaffected by whether a conflict marker literally appeared, and all were re-run for real on the resulting tree rather than assumed -- see "Verification" below.

Cherry-pick (`git cherry-pick -x`, one commit per source commit) was chosen over a bulk `git diff | git apply` or a full-branch `git rebase --onto` because #2950's branch carries an extra commit (`2a542b60`, "bring in PR #2948's content as base") that duplicates content already on `main` via #2951 -- replaying that commit verbatim would have reintroduced the mkdir/rmdir-era code `main` has already moved past. canonical: `git log --oneline FETCH_HEAD -10` (this session) listed `2a542b60` as PR #2950's base-import commit, distinct from `c0ca440d`/`938bd25d`. Cherry-picking only the two commits that are net-new relative to `main` avoids that duplication by construction, per the task's own instruction not to preserve #2948/#2935 as separate deliverables.

## What did not work

None.

## Verification

canonical: this session's own tool-call transcript for every command below; all executed live in this session, no result assumed or carried over from a prior session's record without independent re-execution.

**1. Full test suite.**

```
$ python3 on-the-record/monitors/test_poll_heartbeat.py
...
ok  t_alive_stamp_mutex_evicted_live_holder_release_does_not_corrupt_other_holder_issue_2919
...
45/45 passed
```

derived: `python3 on-the-record/monitors/test_poll_heartbeat.py` (this session) -> `45/45 passed`, including `t_alive_stamp_mutex_evicted_live_holder_release_does_not_corrupt_other_holder_issue_2919` (round 4's regression pin). The count is 45, not the 43 the spawning task's brief anticipated -- `origin/main` had already grown the suite via PR #2951's own additional tests (patrol-skills-genuinely-empty, patrol-skills-query-failure-visible, unguarded-array-detector, etc.) before this session started; round 4 adds exactly 1 test on top of that larger base. derived: `git diff origin/main..HEAD -- on-the-record/monitors/test_poll_heartbeat.py | grep -c '^+def t_'` (this session) -> `1`.

**2. `bash -n` under real bash 3.2.**

```
$ docker run --rm -v "$PWD":/w -w /w bash:3.2 bash -c 'bash --version | head -1; bash -n on-the-record/monitors/poll-heartbeat.sh && echo "SYNTAX_OK exit=$?"'
GNU bash, version 3.2.57(1)-release (x86_64-pc-linux-musl)
SYNTAX_OK exit=0
```

Docker was available and functional this session (`docker version` succeeded, `docker run --rm hello-world` pulled and ran successfully) -- not the `unverifiable: docker not available` case.

**3. Reviewer's A/B/D scenario, real bash 3.2, `flock` removed from PATH.**

Ran a driver script (`/tmp/abd_scenario/run_abd.sh`) inside `docker run --rm -v /tmp/abd_scenario:/w -w /w bash:3.2` that: (a) deletes every `flock` binary found on the container's `PATH` and confirms `command -v flock` returns nothing; (b) extracts the real `_alive_stamp_lock_owner_status` and `_alive_stamp_write` function bodies out of this session's own `on-the-record/monitors/poll-heartbeat.sh` via the test suite's own `_write_mutex_harness()` helper (`on-the-record/monitors/test_poll_heartbeat.py`, invoked this session via a small driver script -- not a hand-copy, so it cannot silently drift from the reviewed code); (c) replays the reviewer's exact A/B/D timing (A holds 5s with `max_age=100` so it is never a waiter itself; B starts 0.5s later with `max_age=1` so its own wait force-reclaims A's still-live lock at ~2s; D starts 2.5s after B, well inside B's 3s hold). Run 3 times for stability:

```
=== RUN 1 ===
flock on PATH: NONE
GNU bash, version 3.2.57(1)-release (x86_64-pc-linux-musl)
=== exit codes ===
worker A exit=0
worker B exit=0
worker D exit=0
=== log ===
1788162257. ENTER A pid=16
1788162259. [log:B] [alive-stamp-lock] lockfile /tmp/abd_run/stamp.lockfile exceeded max wait 1s (owner pid 16) -- force-reclaimed independent of liveness check (zombie/reap-uncertainty safety valve, not a normal stale-lock reclaim)
1788162260. ENTER B pid=26
1788162262. EXIT A pid=16
1788162262. [log:A] [alive-stamp-lock] release skipped: lockfile /tmp/abd_run/stamp.lockfile no longer names this holder (pid 16) -- current owner 26 (this holder was likely force-reclaimed by the max-age valve while still alive; removing would delete a live holder's lock)
1788162263. EXIT B pid=26
1788162263. ENTER D pid=51
1788162263. EXIT D pid=51
=== lockfile left behind? ===
no lockfile remains (good)
```

Runs 2 and 3 (this session, same driver script, immediately following) reproduced the identical shape (B force-reclaims A at max-age expiry; A's own later release is logged as `release skipped`, never an unconditional `rm -f`; D's `ENTER` is always at or after B's `EXIT`, never before; no lockfile left behind at the end) -- across all 3 runs, D never entered before B's genuine release, and A's release was correctly skipped and logged every time, not silent.

**4. `${...[@]}` expansion enumeration.**

Search bounded by: `grep -n '\[@\]' on-the-record/monitors/poll-heartbeat.sh` over the final, post-rebase file (this session).

```
$ grep -n '\[@\]' on-the-record/monitors/poll-heartbeat.sh
564:      # confirmed live under bash 3.2.57. The `${arr[@]+"${arr[@]}"}`
567:      for _patrol_skill in "${POLL_HEARTBEAT_PATROL_SKILLS[@]+"${POLL_HEARTBEAT_PATROL_SKILLS[@]}"}"; do
```

2 hits total: line 564 is a comment (not code), line 567 is the file's only actual `[@]` expansion, and it uses the `${arr[@]+"${arr[@]}"}` guard idiom, not a bare `"${arr[@]}"`. Classified **safe**: derived: `docker run --rm bash:3.2 bash -c 'set -u; unset ARR; for x in "${ARR[@]+"${ARR[@]}"}"; do echo "got: $x"; done; echo "loop completed OK, exit=$?"'` (this session) -> `loop completed OK, exit=0` -- a genuinely unset array under `set -u` does not raise `unbound variable` through this guard, and the loop body correctly never executes. derived: `grep -n '\[@\]\|\$@\|\${@}' on-the-record/monitors/poll-heartbeat.sh` (this session) -> same 2 lines only, confirming no other `[@]`, `$@`, or `${@}` occurrence exists in the file.

**5. Flock-present path byte-identity.**

```
$ diff <(git show origin/main:on-the-record/monitors/poll-heartbeat.sh | sed -n '/if \[ "${_alive_stamp_has_flock}" -eq 1 \]/,/^  else$/p') \
       <(sed -n '/if \[ "${_alive_stamp_has_flock}" -eq 1 \]/,/^  else$/p' on-the-record/monitors/poll-heartbeat.sh)
$ echo exit=$?
exit=0
```

Empty diff -- the `flock`-present branch is byte-identical to pre-rebase `origin/main`, confirming the standing invariant that this round-4 landing does not touch that path.

**6. Per-tick overhead / setup-block placement.**

derived: `git diff origin/main..HEAD -- on-the-record/monitors/poll-heartbeat.sh` (this session) -- the entire diff is confined inside the existing `_alive_stamp_write` function body (a local-variable declaration and the release-path `if`/`else` replacing a single `rm -f` line), which is itself only called from inside the `while true` tick loop at its existing call site. No new top-level setup block was added before or inside the loop; both pre-existing setup blocks (the `command -v flock` detection near the top of the file and the patrol-skills query before `tick=0`) are unchanged and remain before `while true`.

**7. Issue #2919 acceptance criteria, cumulative state after this round.**

canonical: `gh issue view 2919` (this session), "Acceptance" section, 4 `check:` items, cross-referenced against evidence already committed to this repo plus this session's own live checks:

- Check 1 (full tick, bash 3.2, empty patrol-skills result, exit 0): satisfied on the current, post-rebase code. derived, this session, real bash 3.2 container, `flock` removed, a stub `python3` shim on `PATH` that exits 0 with empty stdout (simulating a genuinely-empty, successfully-queried roster):
  ```
  $ docker run --rm -v "$PWD":/w -v /tmp/abd_scenario/fakebin:/fakebin -w /w bash:3.2 bash -c '
    rm -f /usr/bin/flock /bin/flock 2>/dev/null
    export PATH="/fakebin:$PATH"
    export TOKENMAXXXER_CHECKOUT=/w
    mkdir -p /root/.claude/tokenmaxxxer
    POLL_HEARTBEAT_MAX_TICKS=2 POLL_HEARTBEAT_SLEEP_SECONDS=0 bash on-the-record/monitors/poll-heartbeat.sh
    echo "SCRIPT_EXIT_CODE=$?"'
  on-the-record/monitors/poll-heartbeat.sh: line 138: /root/.claude/tokenmaxxxer/poll-watchdog.log: No such file or directory
  SCRIPT_EXIT_CODE=0
  ```
  Two full ticks completed, exit 0. The stderr line is a pre-existing, already-disclosed Alpine/busybox container artifact of `_poll_watchdog_log_append`'s file-redirection against a `$HOME` the image doesn't fully provision -- canonical: `docs/issue-2919/reports/silent-failure-audit+refactoring-legacy-seam-selection-8f663b5d.md` line 68 (read this session) documents an equivalent `wc -c <"${log_path}"` "No such file" quirk as harmless and out of this issue's scope -- not a bash-3.2 array or `flock` defect, and it did not affect the exit code.
- Check 2 (stamp write serialized on macOS, or cost stated): satisfied -- the `noclobber` atomic claim-and-publish (already on `main` via #2951) serializes acquisition, and the max-age valve's disclosed trade-off (force-reclaim past 60s regardless of liveness) is documented inline in `on-the-record/monitors/poll-heartbeat.sh` at the `_alive_stamp_lock_max_age` comment block, unchanged by this round (confirmed by item 6's diff scope above).
- Check 3 (every unguarded `[@]` expansion enumerated): satisfied by this session's own item 4 above.
- Check 4 (line-336-vs-295 discrepancy resolved): already resolved and citable. canonical: `docs/issue-2919/reports/silent-failure-audit+refactoring-legacy-seam-selection-4495e32f.md` lines 51-55 (read this session) -- bash 3.2 attributes an unguarded `"${arr[@]}"` unbound-variable error to the enclosing `for ... done` construct's closing `done` line (336, the file's last line at the time), not the syntactic location of the expansion itself (295) -- confirmed via that session's own isolated `docker run bash:3.2` reproduction of the same shape, and there being only one `[@]` occurrence in the file (this session's own item 4 re-confirms that count still holds after the rebase).

All 4 acceptance `check:` items are satisfied by the cumulative state of this branch (which equals `origin/main` plus exactly round 4's fix). None of the issue's `must not` items are violated: no watch-family signal was touched, the empty-list-vs-failed-query distinction is preserved (`_patrol_skills_query_failed` flag, unchanged by this diff per item 6), `flock`-absence is never silently swallowed (logged distinctly, unchanged), every `[@]` expansion is accounted for (item 4), and per-tick overhead is unchanged (item 6).

## Upstream basis

- PR #2950 (github.com/tokenmaxxxer/on-the-record/pull/2950), branch `issue-2919/silent-failure-audit+refactoring-legacy-seam-selection-b039601c` -- sha `f8e16c560fc57ee8f70c9af5e281bbcbeefe26fa` (branch tip, fetched read-only). canonical: `gh pr view 2950` output (this session). Commits `c0ca440d` and `938bd25d` cherry-picked verbatim (`-x`) onto this branch; commit `2a542b60` ("bring in PR #2948's content as base") deliberately NOT replayed, since its content is already on `main` via PR #2951.
- `origin/main` tip at session start -- sha `8c60562c82c5b95b78ceb07126856091eba252f7` -- this branch's rebase target; already carries PR #2923 (squash-merged) and PR #2951 (mkdir/noclobber mutex + max-age valve + broader test suite). canonical: `git log --oneline origin/main -5` and `gh pr view 2951` (this session).
- `docs/issue-2919/reports/adversarial-review-67ff85fb.md` -- canonical: read in full this session -- the review that found the release-path ownership-check defect round 4 (and, via this rebase, this session) fixes.
- `docs/issue-2919/reports/silent-failure-audit+refactoring-legacy-seam-selection-4495e32f.md`, `...-9f67d71e.md`, `...-8f663b5d.md` -- canonical: read this session (cited passages reproduced in "Verification" item 7 above) -- prior rounds' own live-reproduced evidence for issue #2919's acceptance checks 1 and 4, cited above rather than re-derived from first principles where the underlying code they verified is unchanged by this round.

## Open findings

canonical: `python3 -c "import sys; sys.path.insert(0, 'on-the-record'); import spawn; spawn.role_data()"` (this session) -> `AttributeError: module 'spawn' has no attribute 'role_data'`, confirming the pre-existing, disclosed defect is still present and unchanged by this session's diff.

None new. The pre-existing `spawn.role_data()` `AttributeError` (patrol-skills query genuinely broken, not this issue's scope) remains owned by issue #2925 / PR #2932, per the prior rounds' own determination -- canonical: `docs/issue-2919/reports/silent-failure-audit+refactoring-legacy-seam-selection-9f67d71e.md` "Open findings" section (read this session) -- unchanged by this session and out of this session's scope: patrol code untouched, confirmed by `git diff origin/main..HEAD --stat` (this session, reproduced in "What was done" above) touching only `poll-heartbeat.sh` and `test_poll_heartbeat.py`, and within `poll-heartbeat.sh` confined to `_alive_stamp_write` per item 6 of "Verification" above.

## Next steps

acceptance: `python3 on-the-record/monitors/test_poll_heartbeat.py` -- result:

```
45/45 passed
```

(this session; full output reproduced in "Verification" item 1 above) -- the code fix and its regression test are committed and green on this branch.

Remaining for this session, not yet executed at the point this record was written: open the PR against `main` and post supersession comments closing PR #2950/#2935/#2948, per the spawning task's "Delivery mechanics" section -- the next actions this same session takes immediately after this commit, ahead of the final push+PR-create composite call.
