---
issue: 2925
role: refactoring-legacy-seam-selection-bc3e1a50
author: refactoring-legacy-seam-selection-bc3e1a50
skills: refactoring-legacy-seam-selection (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
code_under_review: ecea081fab654457b8750e689ce5237dfb017984
type: refactor
breaking: false
verdict: pass
upstream:
  - path: PR #2932 (github.com/tokenmaxxxer/on-the-record/pull/2932), branch origin/issue-2925/refactoring-legacy-seam-selection+silent-failure-audit-63ccc91e
    sha: 53a4f5f10580543354c8b446621da1cd5ca09930  # head of the PR branch this record rebases; not same-commit -- read via `git show`/`git diff` against this branch, this session
---

# issue-2925 — refactoring-legacy-seam-selection-bc3e1a50 record

skill-verdict: refactoring-legacy-seam-selection — not-applicable: this is merge-conflict resolution and deletion of dead code, not introduction of new/changed behavior needing a seam
skill-verdict: work-in-english — applied: invoked; used for all commit/PR/code-comment/record English-language output

## What was done

Rebased PR #2932 ("remove the patrol program") onto current `origin/main`. PR #2932 branched off main before issue #2919's macOS heartbeat mutex work (PR #2923, PR #2951) landed in `on-the-record/monitors/poll-heartbeat.sh`, so a mechanical `git rebase` would conflict on that file (both sides edited it). Instead, PR #2932's non-conflicting changes were reproduced as fresh edits against current main's tree, and `poll-heartbeat.sh` was hand-merged: main's current mutex code (flock detection, the mkdir/noclobber lock claim, the max-age valve, and their inline comments) kept verbatim, with only patrol machinery removed on top of it.

Delivered, in two commits on this branch:
- `0af39af2` — deletes `gates/patrol_board.py` (no longer exists, deleted this commit), `gates/patrol_promote.py` (no longer exists, deleted this commit), `gates/patrol_queue.py` (no longer exists, deleted this commit), `gates/patrol_trigger.py` (no longer exists, deleted this commit), `gates/patrol_wiring.py` (no longer exists, deleted this commit), `gates/precision_measure.py` (no longer exists, deleted this commit).
- `ecea081f` — removes patrol tick machinery from `on-the-record/monitors/poll-heartbeat.sh` and its test file, resolves (not amputates) patrol references in `consult.py`, `gates/gh_rest.py`, `gates/record_lint.py` (both copies), `on-the-record/hooks/gh-write-allow-gate.sh`, `on-the-record/commands/run.md`, reproduces the `judge_cmd()` `"enqueued"`/`"findings"` return-key fix, and updates `docs/specs/reconciled-index.md`'s tracked hash row for `run.md`.

canonical: `git log --oneline -2` this session on this branch -> `ecea081f issue-2925: apply patrol-machinery removal to poll-heartbeat.sh, tests, and remaining referrers` / `0af39af2 issue-2925: rebase patrol removal (#2932) onto main, preserve #2919 mutex work` — both commits present on `issue-2925/refactoring-legacy-seam-selection-bc3e1a50`.

Net diff vs `origin/main` (excluding this record) — derived: `git diff --stat origin/main -- . ':!docs/issue-2925/reports/refactoring-legacy-seam-selection-bc3e1a50.md'` — result: `15 files changed, 52 insertions(+), 2116 deletions(-)`. This differs from PR #2932's own reported shape (163 insertions / 2004 deletions) because main's own `consult.py`/`poll-heartbeat.sh`/`test_poll_heartbeat.py` grew independently since PR #2932's base commit (role→skill rename in `consult.py`, #2919's mutex work and its tests in the other two) — the same patrol-removal content lands on a larger current base, not a smaller diff.

**Capability dropped**: board-line promotion to a structured GitHub issue on checkbox approval, with rate caps (this was `gates/patrol_board.py`'s (no longer exists, deleted this commit) combined job with `patrol_promote.py`/`patrol_wiring.py`, both also no longer existing, deleted this commit). No other live path depended on it — derived: `git grep -rni "MAX_ROLES_PER_MERGE\|board_line\|dependencyDashboard\|checkbox.*promot" -- . ':!docs'` — result: no hits. The roster query the whole mechanism depended on, `spawn.role_data()`, never existed in `spawn.py` — derived: `grep -n "def role_data" spawn.py` — result: no hits — so the patrol tick block always yielded zero configured skills and never actually promoted anything.

### Verification

1. Forward direction (no stray patrol references survive, excluding docs and this record's own prose): `git grep -rni patrol -- . ':!docs'` — result:
```
test/test_retirement_count.py:44:        self.assertFalse(retirement_count.line_hits("patrol the controller"))
```
This is the one hit PR #2932's own record already named as the expected unrelated English test string (an example sentence fed to a retirement-count line-matcher, not a reference to the patrol program). Search bound: whole repo tree via `git grep`, `docs/` excluded via the `':!docs'` pathspec.

2. Reverse direction (mutex work from #2923/#2951 fully intact, nothing patrol-shaped silently kept): `grep -n "noclobber\|ALIVE_LOCK_MAX_AGE" on-the-record/monitors/poll-heartbeat.sh` — result:
```
205:#             noclobber write), so this status is reachable only via a
253:    # command. `set -o noclobber` makes `printf '%s' "$$" >file` open
308:    # POLL_HEARTBEAT_ALIVE_LOCK_MAX_AGE overrides it for tests.
309:    local _alive_stamp_lock_max_age="${POLL_HEARTBEAT_ALIVE_LOCK_MAX_AGE:-60}"
313:    while ! ( set -o noclobber; printf '%s' "$$" >"${_lockfile}" ) 2>/dev/null; do
355:    # only reachable once the noclobber write above has ATOMICALLY
```
Also confirmed the actual diff against main touches nothing but the patrol block — canonical: `git diff origin/main -- on-the-record/monitors/poll-heartbeat.sh` output, this session — every removed line is inside the patrol_tick/roster-query block or the patrol loop block; every kept line includes the full `_alive_stamp_write`/`_alive_stamp_lock_owner_status` mutex machinery, byte-identical to main.

3. Full Monitor tick, default bash, exit 0 — acceptance: `bash on-the-record/monitors/poll-heartbeat.sh` (via a fake `spawn.py` fixture matching the committed test suite's own `FAKE_SPAWN_PY` shape, `POLL_HEARTBEAT_MAX_TICKS=2 POLL_HEARTBEAT_SLEEP_SECONDS=0 FAKE_POLL_DUE=1`) — result: `EXIT CODE: 0`, stdout:
```
[poll-report] roster: empty
[poll-report] quiet, nothing in flight
```
(one benign stderr line about the not-yet-created `poll-watchdog.log` directory on the very first append — reproduced as pre-existing on unmodified `origin/main`'s own copy of the script under the identical harness, not a regression: derived: same harness run against `git show origin/main:on-the-record/monitors/poll-heartbeat.sh`, this session — same stderr line, same `EXIT: 0`.) Bash version this session: `GNU bash, 버전 5.1.16(1)-release (x86_64-pc-linux-gnu)`.

4. Full Monitor tick AND `bash -n`, real bash 3.2, Docker `bash:3.2` (Alpine, musl) — docker was available this session. `docker run --rm bash:3.2 bash --version` — result: `GNU bash, version 3.2.57(1)-release (x86_64-pc-linux-musl)`. `bash -n`: `docker run --rm -v "$PWD/on-the-record:/repo/on-the-record:ro" bash:3.2 bash -n /repo/on-the-record/monitors/poll-heartbeat.sh` — result: exit 0, no output. Full tick: same fake-`spawn.py` harness as item 3, `python3` installed inline via `apk add --no-cache python3` (not present in the base `bash:3.2` image, confirmed via `command -v python3` returning nothing before the install), run with `docker run --rm --init -v "$PWD/on-the-record:/repo/on-the-record:ro" -v <workdir>:/work bash:3.2 sh /work/run.sh` — result: `EXIT CODE: 0`, same stdout as item 3, same benign stderr line.

5. `python3 on-the-record/monitors/test_poll_heartbeat.py` — acceptance: result: `36/36 passed`, no patrol tests remain in the printed roster — all `t_patrol_*` names are gone, all `t_alive_stamp_*_issue_2919` mutex tests remain and pass.

6. `python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py test/test_retirement_count.py -q` — result: `52 passed`.

7. `python3 -m py_compile consult.py gates/gh_rest.py gates/record_lint.py on-the-record/gates/record_lint.py` and `bash -n` on both touched shell files — result: all clean, no output, exit 0 each.

## Why

The operator decision recorded in issue #2925 (and reaffirmed by PR #2932's own body) is that the patrol program should be removed: its promotion path never once ran (the roster query it depended on, `spawn.role_data()`, never existed on this repo's `spawn.py`, so every tick silently yielded zero roles), and the job it was built for — surfacing findings for follow-up — is already handled by spawned sessions, their independent verifications, and the orchestrator filing what they find. PR #2932 already did this work and was reviewed/ready, but it target-branched before #2919's mutex fix landed in the same file, so a plain merge/rebase would conflict. Reproducing the same end state on top of current main (rather than merging #2932's branch and fighting the conflict resolution UI) makes the merge's shape explicit and independently checkable: every line #2923/#2951 added stays, every patrol line goes.

## What did not work

The first attempt to stage all nine modified files in one `git add -A -- <path>...` call failed outright (`fatal: pathspec ... did not match any files`) because one of the paths in that same invocation, `gates/patrol_board.py` (no longer exists, deleted this commit), had already been `git rm`'d in an earlier separate command — git aborts the whole multi-path `add` when any one pathspec fails to resolve, so none of the nine files got staged by that call, not just the one whose spec strictly didn't apply. Recovered immediately by re-checking `git status --short`, discovering the first commit had unintentionally landed as deletions-only (`0af39af2`), and creating a second commit (`ecea081f`) for the remaining edits — canonical: `git log --stat -2` this session, this branch, showing `0af39af2` touching only the six deleted `gates/patrol_*.py`/`precision_measure.py` files and `ecea081f` touching the remaining nine — the record's frontmatter `code_under_review:` cites the second, final commit's sha. No other blockers; no test failures caused by this session's own edits (one unrelated pre-existing failure was observed in `test/test_spawn_artifact_skill_pairing.py`, a network-`git fetch`-dependent test — derived: same test run against unmodified `origin/main` in this sandbox, this session, fails the identical way — not exercised by, or related to, any file this session touched).

An intended one-line update was needed against `docs/specs/reconciled-index.md` (a mechanical spec-content-hash ledger, not a patrol-vocabulary or patrol-history record) because `on-the-record/commands/run.md`'s content changed and `on-the-record/hooks/spec-index-preflight.sh` denies (exit 2, before the commit object is even written) any `git commit` that changes a tracked spec file without updating that file's row in the same staged set. This is noted here rather than under a "Rationale for deviations" heading because it is not a divergence from an approved phase-1 proposal — there was no phase-1 proposal for this task — it is a single mechanically-required byte-for-byte hash update, identical to the hash PR #2932's own equivalent commit recorded for the identical edit — derived: computed `hashlib.sha256` of the committed `on-the-record/commands/run.md` this session (`e48a0aface754bb683cfec0457c08c04cb56934a4576b0dc46fca7c63fd1bfed`), matching PR #2932's `docs/specs/reconciled-index.md` diff hunk verbatim, this session.

## Upstream basis

PR #2932 (github.com/tokenmaxxxer/on-the-record/pull/2932), branch `origin/issue-2925/refactoring-legacy-seam-selection+silent-failure-audit-63ccc91e`, head commit `53a4f5f10580543354c8b446621da1cd5ca09930` — read via `git diff`/`git show` against that ref this session to determine exactly what to reproduce; not same-commit (a separate branch, not a path landing in this commit).

## Open findings

None — canonical: this session's own verification runs above (items 1-7 under "Verification") found no residual patrol reference, no mutex regression, and no test failure attributable to this session's edits. The pre-existing `test/test_spawn_artifact_skill_pairing.py` network-fetch failure noted under "What did not work" is unrelated to any file this session touched (derived: same test run against unmodified `origin/main` in this sandbox, this session, fails identically) and is out of this task's scope to fix.

## Next steps

loop_state is terminal (`landed`) — canonical: this session pushed `issue-2925/refactoring-legacy-seam-selection-bc3e1a50` to `origin` and opened a PR against `main` via `gh pr create`, this session (PR URL recorded in this session's own final report to the requester, not duplicated here to avoid a second, possibly stale, copy of a value `gh pr view` can always re-derive). PR #2932 itself is left open per instruction (not closed by this session) — the human may want to close it manually once this PR supersedes it.
