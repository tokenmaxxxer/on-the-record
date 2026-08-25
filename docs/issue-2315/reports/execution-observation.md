---
issue: 2315
role: execution-observation
loop_state: handed-off
upstream:
  - path: gates/gh_delta.py
    sha: 2d3c38a42625cb2c3afcf6baf84690ba8d56847e
  - path: gates/test_gh_delta.py
    sha: 2d3c38a42625cb2c3afcf6baf84690ba8d56847e
subject: PR #2321 (issue-2315, "fix(issue-2315): parse gh -i status before returncode, unblock 304 no-change path"), commit 2d3c38a42625cb2c3afcf6baf84690ba8d56847e, branch issue-2315/implementation
test: python3 -m pytest gates/test_gh_delta.py -v, re-executed against commit 2d3c38a42625cb2c3afcf6baf84690ba8d56847e in an isolated git worktree; independent live cache-valid 304 probe and real-error probe against the real tokenmaxxxer/on-the-record repo (commands in body); independent pre-fix regression re-derivation at merge-base 972997f44277ce5d5bc3446e6a156cbe07c4e22f
result: passed
assertedBy: execution-observation session for issue-2315, independent of PR #2321's authoring (implementation) session
---

# issue-2315 — execution-observation record

## What was done

derived: this section's own acceptance blocks below, all executed this
session directly against commit 2d3c38a42625cb2c3afcf6baf84690ba8d56847e
in an isolated `git worktree` (`/tmp/pr2321-verify`), never by reusing
the implementation record's own pasted transcripts as ground truth —
per the `defect-verification-independence-from-upstream-verdicts`
skill, this session re-derived every claim from scratch rather than
trusting the implementation role's prior "pass" verdict.

**Gate re-executed:**

acceptance: `python3 -m pytest gates/test_gh_delta.py -v` — result:
```
10 passed in 0.93s
```
Matches the implementation record's own count (8 pre-existing + 2 new).

**Fix code independently read, matches the PR diff exactly:**

canonical: `2d3c38a42625cb2c3afcf6baf84690ba8d56847e:gates/gh_delta.py:172-183`,
read this session in the isolated worktree — the page-1 `status == 304`
check runs before `r.returncode != 0`, confirming the reorder the
issue's Ask requested.

**Pre-fix regression independently re-derived** (not copied from the
implementation record's own stash-and-rerun transcript — re-run from
scratch against the merge-base file content):

acceptance: `git show 972997f44277ce5d5bc3446e6a156cbe07c4e22f:gates/gh_delta.py`
swapped in for `gates/gh_delta.py` (test file kept at
2d3c38a42625cb2c3afcf6baf84690ba8d56847e), then `python3 -m pytest
test_gh_delta.py -k "no_change or genuine_non_304" -v` — result:
```
AssertionError: assert 'error' == 'no-change'
  - no-change
  + error
1 failed, 1 passed in 16.41s
```
Confirms the issue's root-cause claim independently: pre-fix ordering
classifies a real 304 as `error`. File restored afterward; `git status
--short` in the worktree showed no diff (canonical: same session,
worktree left clean).

**Live cache-valid probe, independently constructed** (own script, own
repo state, not the implementation record's cursor/etag values):

canonical: `gh auth status`, run this session — authenticated as
`JiwonJung94` against `github.com`.

Primed a fresh cursor against the real `tokenmaxxxer/on-the-record`
repo via an unmocked `fetch_delta` call (real `subprocess.run`, real
`gh` binary), then re-probed the same cursor path repeatedly with
minimal delay — this repo has continuous bot/PR activity, so the first
two immediate re-probes each returned `delta` (real concurrent PR
updates in the query window, confirmed non-empty raw `items` before
the issue-only filter zeroed them out) before a third re-probe landed a
genuine quiet window:

acceptance: repeated `gh_delta.fetch_delta(..., path=cursor_path)`
calls against `tokenmaxxxer/on-the-record`, run=real `subprocess.run`,
this session — result:
```
attempt 1: classification=delta items=0 gh_calls=1
attempt 2: classification=delta items=0 gh_calls=1
attempt 3: classification=no-change items=0 gh_calls=1
```
`no-change`, exactly 1 `gh` call, 0 items (0 detail fetches) — matches
the issue's acceptance line and the implementation record's claim.

Independently reproduced the raw HTTP exchange behind that exact
no-change probe with a direct `gh api -i` call (same since/etag values
read back from the cursor file on disk this session):

acceptance: `gh api repos/tokenmaxxxer/on-the-record/issues --method GET -f state=all -f sort=updated -f direction=asc -f per_page=100 -f page=1 -i -f since=2026-08-25T04:09:10Z -H 'If-None-Match: W/"9c1a08b4caccfd966ea7493c4d7b3e42c567d1bce09ae52a14833c773dbeeead"'` — result:
```
HTTP/2.0 304 Not Modified
...
gh: HTTP 304
EXIT CODE: 1
```
Confirms live, independently: real `gh` exits 1 on a real 304, and
`fetch_delta` at 2d3c38a42625cb2c3afcf6baf84690ba8d56847e correctly
classifies that exact scenario `no-change` rather than `error`.

**Real error, independently constructed** (own probe target — a
nonexistent repo slug — not the implementation record's own error
scenario, which used a bad token):

acceptance: `gh_delta.fetch_delta(tmpdir, "tokenmaxxxer/definitely-nonexistent-repo-xyz-2315", "issues", ...)`,
run this session — result:
```
ERROR PROBE classification: error items: None cursor: None gh_calls: 1
```

acceptance: `gh api repos/tokenmaxxxer/definitely-nonexistent-repo-xyz-2315/issues --method GET -f state=all -f sort=updated -f direction=asc -f per_page=100 -f page=1 -i` — result:
```
HTTP/2.0 404 Not Found
...
gh: Not Found (HTTP 404)
EXIT CODE: 1
```
Confirms the reorder did not broaden the no-change path to swallow a
genuine (non-304) failure: a real 404, exit code 1, still classifies
`error`.

**Heartbeat lines independently checked against source, not asserted
from the implementation record's citation:**

canonical: `2d3c38a42625cb2c3afcf6baf84690ba8d56847e:watchdog.py:940-968`,
read this session in the isolated worktree — the `no-change` branch
(`watchdog.py:956-961`) prints `"[watchdog] board-sweep: no-change
(delta empty) — 상세 조회/전체 재훑기 건너뜀"` and calls
`_run_local_only_signals(skip_requirement_drift=True)` before
returning, skipping both the detail-fetch loop and the
requirement-drift sweep; the `error` branch (`watchdog.py:953-955`)
prints `"[watchdog] board-sweep: gh_delta 프로브 실패 (error 분류) —
보수적으로 오늘의 전체 로직으로 폴백"` and falls through to the day's
full logic. Matches the implementation record's citation exactly, and
independently confirms the operator-frozen load-reduction claim: the
same live no-change scenario reproduced above now takes the
short-circuit branch instead of the full-fallback branch.

## Why

canonical: this session's own commands and outputs pasted under "What
was done" above — the basis for every statement in this section.

Independent re-execution rather than a citation check, because the
issue's own acceptance bar is `provenance: executed-live` — a
re-derived live probe is what the acceptance line asks for. Citing the
implementation record's pasted transcript as-is would not add
independent evidence, since a pasted transcript names a scenario
specific to that session's own timing and cursor/etag state; this
session instead built its own cursor, its own probe target, and its
own error scenario, all shown above. The live cache-valid probe needed
several attempts because this repo has real ongoing bot/PR activity —
a single-attempt no-change probe is not guaranteed against a live,
actively-changing repo, so the retry-until-quiet approach was used
instead of a fixed one-shot call, and the intermediate `delta`
attempts are reported above rather than discarded, so the probe is not
cherry-picked to only the successful result.

## Upstream basis

- `gates/gh_delta.py`, `gates/test_gh_delta.py` — same-commit
  (2d3c38a42625cb2c3afcf6baf84690ba8d56847e,
  `issue-2315/implementation`), re-executed and re-read directly this
  session in an isolated worktree (canonical: acceptance blocks under
  "What was done" above).
- `watchdog.py` — same-commit (2d3c38a42625cb2c3afcf6baf84690ba8d56847e),
  read-only (not modified by PR #2321); canonical:
  `2d3c38a42625cb2c3afcf6baf84690ba8d56847e:watchdog.py:940-968`, read
  this session to independently confirm the heartbeat citation and
  load-reduction claim (see "What was done" above).
- merge-base 972997f44277ce5d5bc3446e6a156cbe07c4e22f — the pre-fix
  baseline this record's own isolated worktree used for the
  independent regression re-derivation (canonical: acceptance block
  under "What was done" above).
- Real, unmocked `gh api` calls against `tokenmaxxxer/on-the-record`
  (authenticated as `JiwonJung94`, canonical: `gh auth status`, run
  this session) and against a nonexistent repo slug — both run
  directly this session, not read from the implementation record's
  pasted output.

## Acceptance verification

derived: every bullet below cites the command actually run this
session for that line, restating the acceptance blocks under "What was
done" above.

- Gate re-executed on the PR's own commit — canonical: `python3 -m
  pytest gates/test_gh_delta.py -v`, run this session in the isolated
  worktree — checked: gates/test_gh_delta.py — result: pass
- Pre-fix regression independently re-derived at merge-base —
  canonical: `git show 972997f44277ce5d5bc3446e6a156cbe07c4e22f:gates/gh_delta.py`
  swapped in, then `python3 -m pytest test_gh_delta.py -k "no_change or
  genuine_non_304" -v`, run this session — checked:
  gates/test_gh_delta.py — result: pass (fails against pre-fix code as
  the issue describes, confirming the fix is load-bearing)
- Live cache-valid probe (issue's acceptance line 1) independently
  constructed and re-run against the real repo — canonical: repeated
  `gh_delta.fetch_delta` calls against `tokenmaxxxer/on-the-record`,
  run this session — checked: gates/gh_delta.py — result: pass
- Live real-error probe (issue's acceptance line 1, second clause)
  independently constructed against a nonexistent repo slug —
  canonical: `gh_delta.fetch_delta` against
  `tokenmaxxxer/definitely-nonexistent-repo-xyz-2315`, run this
  session — checked: gates/gh_delta.py — result: pass
- Empty-state acceptance line (no cursor — no `If-None-Match`/`since`
  sent) — canonical: `2d3c38a42625cb2c3afcf6baf84690ba8d56847e:gates/gh_delta.py:143-149`,
  read this session, and `python3 -m pytest gates/test_gh_delta.py -v`
  above (test_pulls_resource_hits_issues_endpoint_no_since_symmetry_bug
  is included in that run) — checked: gates/test_gh_delta.py — result:
  pass
- Heartbeat before/after lines and load-reduction mechanism
  independently checked against watchdog.py source — canonical:
  `2d3c38a42625cb2c3afcf6baf84690ba8d56847e:watchdog.py:940-968`, read
  this session — checked: watchdog.py — result: pass

## Open findings

None — every claim under observation was independently re-derived and
matched. The broader regression sweep (`gates/`,
`tests/test_watchdog_heartbeat_noise.py`,
`tests/test_spawn_observation_recovery.py`) cited in the implementation
record was not independently re-run this session — out of this task's
declared scope ("re-execute the live cache-valid probe ... and the
real-error case yourself"), and its one pre-existing failure is stated
by the implementation record as unrelated to this change. Not
re-derived here; flagged as not independently reproduced rather than
silently endorsed.

Resolution path: none — no open finding requires further action; the
regression-sweep scope note above is informational, not a defect.

## Next steps

None — this record is handed off.

## What did not work

None. The gate re-run, the pre-fix regression re-derivation, and the
real-error probe each produced a directly comparable result on the
first attempt. The live cache-valid probe needed three attempts before
landing a quiet window against the actively-changing real repo (see
"Why" above) — not a failed approach, but expected variance re-running
a live network probe against a repo under continuous activity; all
three attempts are reported above rather than only the successful one.
