---
kind: record
loop_state: handed-off
---

# Execution observation — issue #288

## Independence statement

This role did not author or edit the observed artifact this session. No
file under spawn.py, tests/test_spawn.py, or
docs/issue-288/reports/implementation.md was touched here — this record
is the only file this session wrote.

## Upstream basis

canonical: gh pr view 315 --json number,title,body,mergeCommit,commits,files,state (read this session) — PR #315 ("issue-288: phase 1 — survey + proposal for CLI truth-vs-action fixes"), state MERGED, mergeCommit 8bcff757baa8136549d2716640c6b59a78436f81, closes #288.

Two commits: 25574ef6 (phase 1, survey+proposal) and d39de19a (phase 2,
the actual spawn.py fix).

canonical: git log --oneline --all | grep 8bcff757 (read this session) — 8bcff757 is on this checkout's history as the merge of PR #315: the fix is present at HEAD, not merely claimed by the PR body.

## Live evidence

Read the issue-288 body (5 named defects: N1 clean --issue scoping, N2
--dry-run -C validation, N3 issue-number validation, N4 non-numeric
issue-* dir vanishing from board, N5 foreign-repo-at-work-path — N6/N7/N8
and the MUSTER_MCP_ALLOW notice explicitly out of scope per the PR body)
and its acceptance list.

canonical: git show d39de19a3fe400732b190754d5962fbbfb9342 -- spawn.py (read this session) — located the four in-scope, live-testable fixes.

N5 requires a real git remote identity mismatch and network access this
sandbox doesn't have for a clean fixture — deferred to the pinning-test
check below rather than hand-driven. Each of N1/N2/N3/N4 was exercised
this session by direct function call or subprocess invocation against
this session's real HEAD checkout — not by re-reading the PR's own
prose, and not by re-running tests/test_spawn.py as this role's only
evidence.

### N3 — `--issue` rejects non-positive values at parse time

```
$ python3 -c "
import spawn, argparse
for v in ['0','-5','3']:
    try:
        r = spawn.positive_int(v)
        print(v, '->', r)
    except argparse.ArgumentTypeError as e:
        print(v, '-> REJECTED:', e)
"
0 -> REJECTED: 양의 정수가 아니다: 0
-5 -> REJECTED: 양의 정수가 아니다: -5
3 -> 3
```

canonical: python3 -c invoking spawn.positive_int directly against this session's HEAD spawn.py, executed this session, output reproduced above — N3: `0` and `-5` rejected, `3` accepted (clean).

### N2 — `--dry-run` validates `-C` before printing settings

```
$ python3 spawn.py execution-observation "test task" --dry-run -C /nonexistent/path/xyz
-C 가 디렉터리가 아니다: /nonexistent/path/xyz
$ echo "exit: $?"
exit: 1
```

canonical: python3 spawn.py execution-observation "test task" --dry-run -C /nonexistent/path/xyz, executed this session against a real nonexistent path, output reproduced above — N2: exits before printing any settings JSON (the issue body's original repro exited 0 and printed the full settings JSON for the same input); clean.

### N1 — `clean --issue N` scopes the sweep instead of ignoring the flag

Built three real git repos under /tmp/n1test named
ws-issue-138-implementation, ws-issue-280-execution-observation,
ws-issue-30-implementation, each with one committed (unpushed, no origin
remote) commit:

```
$ python3 -c "
import spawn
from pathlib import Path
wb = Path('/tmp/n1test')
r = spawn.roster_clean(wb, 138)
print('return:', r)
print('remaining:', sorted(p.name for p in wb.iterdir()))
"
남김 (미보존 작업 있음  [미push 커밋 1건]): ws-issue-138-implementation
정리 끝 — 지움 0, 남김 1
return: 0
remaining: ['ws-issue-138-implementation', 'ws-issue-280-execution-observation', 'ws-issue-30-implementation']
```

canonical: python3 -c invoking spawn.roster_clean(wb, 138) against a real fixture workspace tree built this session, executed this session, output reproduced above — N1: only ws-issue-138-implementation is evaluated and printed; ws-issue-280-* and ws-issue-30-* are never mentioned in the output at all (never entered the removal decision), unlike the issue body's original repro where `clean --issue 138` deleted workspaces for issues 280 and 30 too. Clean.

For contrast, the unscoped call against the same fixture tree evaluates all three:
```
남김 (미보존 작업 있음  [미push 커밋 1건]): ws-issue-138-implementation
남김 (미보존 작업 있음  [미push 커밋 1건]): ws-issue-280-execution-observation
남김 (미보존 작업 있음  [미push 커밋 1건]): ws-issue-30-implementation
정리 끝 — 지움 0, 남김 3
return: 0
```

canonical: python3 -c invoking spawn.roster_clean(wb, None) against the same fixture tree, executed this session, output reproduced above — the contrast shows `--issue N` narrows the evaluated set to matching workspaces only.

### N4 — non-numeric `issue-*` dir warns to stderr and drops from the board

```
$ python3 -c "
import spawn
from pathlib import Path
b = spawn.board(Path('/tmp/n4test'))
print('board keys:', list(b.keys()))
"
board: 숫자가 아닌 issue-* 디렉터리라 보드에서 뺀다: issue-NaN
board keys: []
```

canonical: python3 -c invoking spawn.board(Path('/tmp/n4test')) against a fixture docs/ tree built this session (not a path in this repository) containing a non-numeric issue-NaN subdirectory, executed this session, output reproduced above — N4: the "board: 숫자가 아닌 issue-* 디렉터리라..." stderr line names the offending directory (the issue body's original repro had issue-NaN disappear from board output with zero diagnostic). Clean.

### N5 — foreign-repo-at-work-path identity check (deferred to pinning tests)

Not hand-driven this session: reproducing N5 live requires two distinct
git remotes and a real fetch attempt, which this sandbox's isolated
fixture setup does not cleanly support without network calls outside the
allowed domains.

canonical: git show d39de19a -- spawn.py (read this session) — `issue_workspace()`'s reuse branch adds an origin-comparison `sys.exit` before calling `_fetch_or_halt`. Corroborated only by the pinning-test run below, which includes MUSTER_KEEP_SSH-toggle regression coverage per the PR body's stated warrant-hunt finding — N5 result: cantTell (not independently exercised this session).

### Full pinning-test run

```
$ python3 -m pytest -q tests/test_spawn.py -k "clean or positive_int or dry_run or board or origin_mismatch or foreign"
46 passed, 457 deselected in 31.42s
```

canonical: python3 -m pytest -q tests/test_spawn.py -k "clean or positive_int or dry_run or board or origin_mismatch or foreign", executed this session against this session's HEAD checkout, output reproduced above — pinning tests covering N1/N2/N3/N4/N5, clean (corroborating, not the sole evidence for N1-N4, which were independently hand-driven above).

## Why

Contract: an executable artifact (PR #315 / commit 8bcff757, closing
#288) landed on the branch and no execution-observation record existed
yet for it (per `roles/specs/execution-observation.spec.json`'s
`use_when.board_condition`).

## Verdicts

### Outcome

Recomputation per `roles/specs/execution-observation.spec.json`: overall
result = the worst-case single result across all cited test entries,
ranked worst-to-best as failed, cantTell, inapplicable, untested, then
the clean result — never asserted as a standalone summary independent
of the cited results.

canonical: python3 -c invoking spawn.positive_int, spawn.roster_clean, spawn.board, and python3 spawn.py --dry-run, all executed this session (see "Live evidence" §§ N1-N4 above for full transcripts) — N1, N2, N3, N4 each independently reproduce clean.

canonical: git show d39de19a -- spawn.py plus python3 -m pytest -q tests/test_spawn.py -k "..." (read/executed this session, "Live evidence" § N5 and "Full pinning-test run" above) — N5 was not independently hand-driven this session, result: cantTell.

Recomputed worst case across the five: N5's cantTell outranks (is worse
than) N1-N4's clean result under the worst-case rule, so this record's
own outcome is **cantTell** — not a uniform clean result across the
full scope.

### Trajectory

canonical: gh pr view 315 --json ... (read this session, "Upstream basis" above) plus gh issue view 288 --comments (read this session) — single PR (#315) carried both phase-1 (survey+proposal) and phase-2 (fix) commits, merged, closing #288; the comment trail shows a bare "APPROVE issue-288/implementation" comment from JiwonJung94, single-account author/approver, consistent with this repo's documented single-account mode.

Trajectory verdict, per that same citation: sound — proposal,
implementation, and pinning tests landed together and match the
approved proposal's stated scope (N6/N7/N8 and the MUSTER_MCP_ALLOW
notice explicitly excluded, matching the issue body's own framing of
"Verified correct (no change wanted)" and out-of-acceptance items).

### Step

canonical: the python3/pytest invocations reproduced in "Live evidence" §§ N1-N4 and "Full pinning-test run" above, all executed this session against this session's HEAD checkout — `spawn.py`'s `positive_int`, `roster_clean`, the `--dry-run` `-C` check, and `board()`'s non-numeric warning each reproduce the acceptance-list behavior exactly against real invocation this session; no deficiency observed in any of the four.

canonical: git show d39de19a -- spawn.py (read this session) — `issue_workspace()`'s origin-comparison branch was read but not exercised live this session; that coverage gap, not a defect observed in the read code, is what this record's overall cantTell result (recomputed above) reflects.

## Open findings

None. The only open item is N5 verification depth (code-read + existing
pinning test, not this session's own live drive) — not a finding against
the shipped artifact, a coverage gap in this observation session.

## Next steps

A future execution-observation session, with network access to build a
scratch GitHub-backed fixture repo pair with mismatched origins, should
hand-drive N5 against `issue_workspace()`'s reuse branch — the same way
N1-N4 were hand-driven in this record.

canonical: git show d39de19a -- spawn.py (read this session) — the origin-comparison `sys.exit` block that a future session should drive live.

## Resolution path

Whoever next builds that scratch fixture pair (or touches
`issue_workspace()` itself) can close the N5 coverage gap named above;
until then this record's own recomputed outcome (see "Verdicts" §
Outcome above) stands.
