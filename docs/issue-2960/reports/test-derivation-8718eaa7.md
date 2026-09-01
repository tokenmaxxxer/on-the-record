---
issue: 2960
role: test-derivation-8718eaa7
author: test-derivation-8718eaa7
skills: test-derivation (skill-repository(c05de12))
verifies_subject: true
code_under_review: 71fdf5757a4a17853819d6bc77b671d06a15d938
loop_state: landed
type: docs
breaking: false
verdict: pass
upstream:
  - path: lifecycle.py
    sha: 71fdf5757a4a17853819d6bc77b671d06a15d938
---

# issue-2960 — test-derivation-8718eaa7 record

## What was done

PR #2963 (branch `issue-2960/test-derivation+silent-failure-audit-ccd3b998`,
`lifecycle.py` commit `71fdf5757a4a17853819d6bc77b671d06a15d938`)
implements the workspace-preservation predicate rewrite for this
issue. Its PR body only claimed "removed count dropped vs. pre-fix
baseline" with no numbers.
canonical: `gh pr view 2963 --json body` output, before this session's
edit — the acceptance-checklist line for `python3 spawn.py
clean --dry-run` reads "reports candidates before deleting, removed
count dropped vs. pre-fix baseline on the same host", no numeric pair.

The issue's convergence check declares "population: every workspace
under `~/.tokenmaxxxer/work`," so a before/after numeric pair against
that real population belongs in the delivered evidence. This follow-up
measured it (no predicate code touched — PR #2963's diff is
unchanged by this session).

Ran the same command with the pre-fix and post-fix predicate, back to
back, against this host's live `~/.tokenmaxxxer/work`:

Pre-fix predicate — checked out the commit immediately before the fix
into a scratch worktree (`_HARNESS_NOISE_BASENAMES` whitelist still in
place):
```
$ git worktree add /tmp/prefix-worktree 5c0cc599
$ cd /tmp/prefix-worktree && python3 spawn.py clean --dry-run
...
정리 끝 — 지움 0, 남김 69
```
Post-fix predicate — this checkout at the fix commit
(`check-ignore`-based predicate), run 2 seconds later:
```
$ python3 spawn.py clean --dry-run
...
정리 끝 — 지움 0, 남김 69
```
derived: `diff <(grep -oP '(?<=: ).*$' /tmp/prefix_final.txt | sort) <(grep -oP '(?<=: ).*$' /tmp/postfix_final.txt | sort)` — result: empty — confirms both runs evaluated the identical 69-entry candidate set ("that same live population").

**Before -> after: 0 -> 0 removed, 69 -> 69 preserved**, out of 69
`.git`-bearing dirs under `~/.tokenmaxxxer/work` that `roster_clean()`
considers on this host right now.
derived: `ls ~/.tokenmaxxxer/work | wc -l` — result: 452 total entries
(this count drifts live — other concurrent sessions spawn/clean
workspaces on this host); the remainder are non-workspace files/dirs
(roster/log files, `.archived-logs`, dirs without a `.git`) that
`roster_clean()` skips before the predicate ever runs.
The predicate rewrite reclaimed nothing further on this host's current
population at measurement time: the 69 preserved workspaces are held
for genuine untracked-not-ignored content or unpushed commits, per
their printed reasons in both dry-run outputs above, not the
basename-whitelist/D-only false positives the fix targeted.

A first attempt (post-fix run alone, before the scratch worktree
existed) had shown 지움 1 instead of 0.
canonical: `/tmp/postfix_dryrun.txt` (first standalone post-fix run,
captured before the worktree existed) contains `지움:
on-the-record-issue-2960-test-derivation+silent-failure-audit-ccd3b998`
— that workspace is PR #2963's own authoring session's workspace,
which went from live to dead between that run and the next one. That
is a process-liveness timing artifact of re-running a live host twice,
not a predicate effect, so it is excluded from the reported pair above
in favor of the back-to-back measurement, where both runs saw the
identical 69-entry set (confirmed by the empty-diff `derived:` line
above).

Updated PR #2963's body (`gh pr edit 2963`) to replace the numberless
"removed count dropped vs. pre-fix baseline" line with this measured
0 -> 0 (69 -> 69) pair, the two commands above, and a pointer to this
record for the full output.

## Why

The issue states the predicate change alone is not expected to reach
222 -> 8 on the field-measured population, because
untracked-and-not-gitignored record folders still preserve their
workspace and the operator declined the archive-and-grace stage that
would close that gap further — so a small/zero delta is an expected,
correct outcome to report as-is, not a result to tune or omit.

## What did not work

None — the measurement is the deliverable; no predicate or production
code was changed in this follow-up.

## Upstream basis

- `lifecycle.py` at `71fdf5757a4a17853819d6bc77b671d06a15d938`
  (post-fix `_workspace_clean_state`, `check-ignore`-based) and at
  `5c0cc599` (pre-fix, `_HARNESS_NOISE_BASENAMES` whitelist) — read via
  a scratch `git worktree add`/`git worktree remove` to run both
  predicate versions against the live population; neither file edited
  by this follow-up — sha: 71fdf5757a4a17853819d6bc77b671d06a15d938
- PR #2963 (`gh pr view 2963`, `gh pr edit 2963`) — read for its
  existing numberless claim, then edited to carry the measured pair —
  sha: not applicable (GitHub PR body, not a repo file)

Survey skip: this is a measurement-only follow-up with the predicate's
fix already implemented and reviewed in PR #2963 and this follow-up's
own scope fixed by the spawning instruction (measure, record honestly,
do not change the predicate) — no open design decision to survey
alternatives for.

### skill-verdict

- skill-verdict: test-derivation — not-applicable: no new written
  requirement or acceptance criteria to derive test cases from in this
  follow-up — it measures an already-implemented, already-reviewed
  predicate (PR #2963) against a live population rather than deriving
  new test coverage.
- other mounted skills: not triggered

## Open findings

None new. PR #2963's own open findings (git-subprocess-failure blind
spot in `_workspace_clean_state()`'s new/changed call sites;
untracked-not-ignored dirs like `docs/issue-790/` still preserve)
stand unchanged — this follow-up only measured, it did not touch
`_workspace_clean_state()`.

## Next steps

None — `loop_state: landed`.
