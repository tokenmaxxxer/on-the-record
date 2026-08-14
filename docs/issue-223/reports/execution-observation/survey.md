---
subject: issue-223
role: execution-observation
observed_role: implementation
observed_pr: 249
loop_state: phase-1-survey
---

# Survey — issue #223 execution-observation, phase 1

## What is being observed

Issue #223 asked for a mutual-exclusion claim on `_spawn_one()` (the main
spawn path) matching the one `_auto_respawn_check()` already had, so two
concurrent spawns of the same `(issue, role)` cannot corrupt a shared
workspace. The `implementation` role delivered this as PR #249, branch
`issue-223/implementation`, two commits `2272489` (phase 1, survey +
proposal) and `a30f56c` (phase 2, code + record).
canonical: `gh pr view 249 --json commits --jq '.commits[]|{sha:.oid,msg:.messageHeadline,date:.authoredDate}'`, this session

PR #249's merge commit is `48266e7`, `mergedAt` 2026-08-03T10:56:21Z,
`reviews` is an empty array.
canonical: `gh pr view 249 --json mergeCommit,mergedAt,reviews`, this session

Issue #223 carries exactly one comment, body exactly `APPROVE
issue-223/implementation`, author `jjongkwann`, 2026-08-03T08:19:05Z.
canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/223/comments`, this session

Commit `a30f56c`'s stat line: `docs/issue-223/reports/implementation.md`
+249, `spawn.py` +97, `test_spawn.py` +160.
derived:
```
$ git show a30f56c --stat --format=
 docs/issue-223/reports/implementation.md | 249 +++++++++++++++++++++++++++++++
 spawn.py                                 |  97 ++++++++++++
 test_spawn.py                            | 160 ++++++++++++++++++++
 3 files changed, 506 insertions(+)
```

## `spawn.py` diff contents

canonical: `git show a30f56c -- spawn.py`, this session

1. `_spawn_claim_path(work)` — `Path(str(work) + ".spawn-claim")`, same
   sibling-file family as `.respawn-claim-{ts}` (issue #132).
2. `_acquire_spawn_claim(work, issue, role) -> str | None` — writes
   `{"pid", "ts"}` to a `tempfile.mkstemp` sibling, then `os.link()`s it
   onto the claim path (atomic exists-check+create). On
   `FileExistsError`, reads the existing claim, checks `_alive(pid)`:
   alive path returns a string containing the pid and ts; dead path
   unlinks and retries once (2 attempts total, final attempt returns a
   generic string rather than raising).
3. `_rewrite_spawn_claim_pid(work)` — read-modify-`os.replace()`, not
   `Path.write_text()` (which would truncate-then-write and reopen the
   same-shaped race `_acquire_spawn_claim` closes).
4. `_release_spawn_claim(work, pid)` — unlinks only if the claim's
   recorded pid still equals the caller's own pid.
5. Wiring inside `_spawn_one()`: `_acquire_spawn_claim` is called right
   after `cwd = issue_workspace(...)`, before `checkout_issue_branch()`;
   its rejection path prints to stderr and `return`s `1` rather than
   `sys.exit()`. `_rewrite_spawn_claim_pid(cwd)` is called in the fork's
   child branch, immediately before `os.setsid()`.
   `_release_spawn_claim(cwd, os.getpid())` is called right after
   `roster_remove(roster_key)`, guarded by `if issue is not None`.

## `test_spawn.py` diff contents

canonical: `git show a30f56c -- test_spawn.py`, this session

The diff adds one class, `SpawnOneIssueRoleClaim`, containing four
methods matching `def test_`: a two-`threading.Thread` concurrent
`_spawn_one()` construction asserting `checkout_issue_branch` is reached
exactly once and the two results are `[0, 1]`-shaped; a stale-dead-pid
cleanup case; a rejection-message content case; and a mocked-fork case
asserting `_rewrite_spawn_claim_pid` runs before `os.setsid()`.
derived: `git show a30f56c -- test_spawn.py | grep -c '    def test_'` → 4

No method name in that diff hunk contains the string `clean`.
derived: `git show a30f56c -- test_spawn.py | grep -i clean` → no output

## Call-site check — is the new rc observed everywhere it is produced?

canonical: `spawn.py:5732` and `spawn.py:3510-3524`, read in full this session (HEAD, post-merge)

`main()` at `spawn.py:5732` reads `return _spawn_one(...)` — its rc
propagates to the process exit code.

`_respawn_or_cap()` at `spawn.py:3523` reads
`_spawn_one(work, role, task, unattended=True, issue=issue,
bounded=True)` as a bare statement — no name binds its return value
anywhere in `_respawn_or_cap()`'s body. Lines `spawn.py:3513-3519`
(`attempt_n = attempts + 1`, `_append_event(events_path,
"respawn-attempt", ...)`, `_respawn_state_save(state)`) execute before
this call, ahead of whatever rc the call would produce.

The same call site and the same consequence — attempt/event bookkeeping
ahead of a claim rejection whose rc goes nowhere — appear in the
observed record's own text, its "Open findings" section item 1.
canonical: `docs/issue-223/reports/implementation.md`, "Open findings" section item 1, read in full this session

## `clean`-glob coverage, read against the new claim suffix

`spawn.py:5299` reads `for sibling in w.parent.glob(w.name + ".*"):` — a
glob against `w.name + ".*"` matches `w.name + ".spawn-claim"` the same
shape it already matches `w.name + ".respawn-claim-{ts}"`.
canonical: `spawn.py:5299`, read this session (HEAD)

No test in the `a30f56c` `test_spawn.py` hunk exercises this glob
against the new suffix (see the `grep -i clean` result above); the
observed record's own delivery-description section, item 1, names the
glob as sufficient without naming a dedicated test for it.
canonical: `docs/issue-223/reports/implementation.md`, delivery-description section item 1, read in full this session

## Candidate observation surfaces for phase 2

1. **Outcome** — issue #223's three requirements (main-path claim /
   stale-claim cleanup / rejection names the claimant) against the diff
   and the new tests, item by item.
2. **Trajectory** — contract v3 s19 path: survey exists in `2272489`
   before the proposal, approval is a real single-account issue comment
   before phase 2, phase-2 commit follows it.
3. **Step** — candidates: (a) the discarded-rc call site at
   `spawn.py:3523`, already named by the observed role itself — worth
   confirming independently rather than inherited; (b) the `clean` glob
   coverage gap (asserted, not test-guarded); (c) the TOCTOU-fix
   deviation from the approved proposal's literal
   `O_CREAT|O_EXCL`-then-write shape to tempfile+link/replace — whether
   the delivered fix still satisfies the proposal's intent despite the
   shape change.

## Rationale for what phase 2 should weight

The observed record already surfaces the rc-discard gap and a pid-reuse
risk as open items in its own text — re-deriving those from nothing in
phase 2 would spend the phase confirming an already-stated point. What
phase 2 has not yet checked independently: whether the delivered code
stays inside the *approved proposal's* write set and behavioral asks
(not just the observed record's own narrative of itself), and whether
the four new tests' construction exercises what their names claim
(construction-level check only — this role does not re-execute code).
