---
issue: 2314
role: execution-observation
loop_state: handed-off
upstream:
  - path: gates/stale_revert_guard.py
    sha: 69a26bc7a994056095699ed01aeab48d11497636
  - path: cfad1136f209828576aa7bfda9a58a14b9b0a6af:docs/issue-2314/reports/implementation.md
    sha: cfad1136f209828576aa7bfda9a58a14b9b0a6af
subject: PR #2323 (issue-2314/implementation @ cfad1136f209828576aa7bfda9a58a14b9b0a6af, fix commit 69a26bc7a994056095699ed01aeab48d11497636)
test: independent re-execution of PNG-PR end-to-end pre/post (crash -> clean verdict), surrogateescape non-UTF-8 stale-revert-still-REFUSED, and text-only byte-identity
result: passed
assertedBy: execution-observation
---

# issue-2314 — execution-observation record

## What was done

Independently re-executed PR #2323's three named claims with a
self-authored harness (`/tmp/eo2314/harness.py`, not
`69a26bc7:gates/test_stale_revert_guard.py`) that loads the pre-fix and
post-fix `stale_revert_guard.py` modules by path via `importlib` and
drives `check_pr()` against freshly-built real git-repo fixtures — a real
67-byte PNG (valid header + IHDR/IDAT/IEND chunks, not just the `\x89PNG`
magic bytes) and hand-picked non-UTF-8 byte sequences distinct from the
PR's own fixtures. All three hold.

**1. PNG-PR end-to-end, pre-fix crash -> post-fix clean verdict.**
canonical: `main:gates/stale_revert_guard.py:119` (pre-fix `_git_show`,
`text=True`) vs. `69a26bc7:gates/stale_revert_guard.py:135-139` (post-fix,
bytes + `errors="surrogateescape"`).
derived: `python3 /tmp/eo2314/harness.py` scenario A — fixture repo with a
base HEAD that grows a screenshot PNG then a real security fix, and a PR
branch that adds its own PNG plus a stale, unrelated edit that drops the
fix —
```
== Scenario A: PNG-PR end-to-end pre/post ==
pre-fix crashed: True  (UnicodeDecodeError: 'utf-8' codec can't decode byte 0x89 in position 0: invalid start byte)
post-fix verdicts: [{'verdict': 'REFUSE', 'reason': 'app.py: 병합이 merge-base 이후 추가된 내용과 충돌함(오래된(stale) merge-base)', 'path': 'app.py'}]
RESULT: PASS
```
Pre-fix `check_pr()` raises `UnicodeDecodeError` at the same byte (`0x89`,
position 0) the issue reported; post-fix `check_pr()` returns a clean
verdict list, REFUSEs the genuine `app.py` stale revert, and cites no
`.png` path. `merge_gate.py`'s own CLI (`main()`) was not run directly —
it requires a live `gh pr view` round-trip
(`main:gates/merge_gate.py:52-57`) that a local fixture can't supply — so
this re-execution goes through `check_pr()`, the exact function
`merge_gate.py` calls for the stale-revert check and the one the issue's
own trace names.

**2. surrogateescape non-UTF-8 line, stale revert still REFUSED (not
silently ALLOWed).**
canonical: `69a26bc7:gates/stale_revert_guard.py:124-139` (`_git_show`,
docstring names the exact regression: a `""`-on-decode-failure fallback
would make `classify()` see "no added lines" and silently ALLOW a genuine
stale revert).
derived: `python3 /tmp/eo2314/harness.py` scenario B — fixture where the
security fix commit's line contains a non-UTF-8-decodable accented-letter
byte (see `scenario_b_non_utf8_still_refused()` in the harness source for
the exact byte string) with no NUL byte, so git's own binary heuristic
does not mark the file binary and `changed_paths()`'s numstat filter lets
it through —
```
== Scenario B: surrogateescape non-UTF-8, stale revert still REFUSED ==
fixture stays non-binary per git's own numstat: True
post-fix verdicts: [{'verdict': 'REFUSE', 'reason': 'app.py: 병합이 merge-base 이후 추가된 내용과 충돌함(오래된(stale) merge-base)', 'path': 'app.py'}]
RESULT: PASS
```
Confirms the harder claim than "does not crash": the fix does not trade
the crash for a silent fail-open on non-UTF-8-but-git-non-binary content.
`_merge_file()` (`69a26bc7:gates/stale_revert_guard.py:47-65`, bytes +
matching `surrogateescape` round-trip) is exercised on this same path
inside `classify()` and did not raise, corroborating the PR's claim that
hardening `_git_show()` alone would have re-crashed here without the
matching `_merge_file()` change.

**3. Text-only PR, byte-identical pre vs. post (issue's Acceptance empty
state).**
canonical: issue #2314 body, `## Acceptance` — "empty state: a text-only
PR — behavior byte-identical."
derived: `python3 /tmp/eo2314/harness.py` scenario C — fixture with no
binary file anywhere in its history, a genuine stale revert as the only
change —
```
== Scenario C: text-only PR, byte-identical pre vs post ==
pre-fix  verdicts: [{'verdict': 'REFUSE', 'reason': 'app.py: 병합이 merge-base 이후 추가된 내용과 충돌함(오래된(stale) merge-base)', 'path': 'app.py'}]
post-fix verdicts: [{'verdict': 'REFUSE', 'reason': 'app.py: 병합이 merge-base 이후 추가된 내용과 충돌함(오래된(stale) merge-base)', 'path': 'app.py'}]
RESULT: PASS
```
`pre == post` on the returned verdict list (Python equality on the
list-of-dicts), not merely "both REFUSE" — confirms no behavior change
for the no-binary path.

derived: full harness run, all three scenarios in one process —
```
TOTAL: 3/3 scenarios passed
```

Also re-ran the PR's own pasted acceptance command against a
`git worktree add --detach` checkout of its head
(`cfad1136f209828576aa7bfda9a58a14b9b0a6af`, at `/tmp/eo2314/pr-checkout`)
rather than trusting the pasted numbers:
acceptance: `python3 -m pytest -q gates/test_stale_revert_guard.py` (run
inside the `cfad1136` worktree, where that path exists — it does not
exist on this session's own `issue-2314/execution-observation` branch,
which sits at pre-fix `main`) — result:
```
11 passed in 18.71s
```
Matches the PR's own claimed count (6 pre-existing + 5 new). Did not
re-run the full `python3 -m pytest -q gates/` (975 passed, 8 xfailed)
sweep independently — out of scope for this pass, which the issue's task
scoped to the three named claims (PNG pre/post, surrogateescape-REFUSED,
text-only byte-identity), not a full-suite re-certification.

## Why

canonical: the three re-execution results in "What was done" above
(Scenario A/B/C, and the `69a26bc7:gates/test_stale_revert_guard.py`
acceptance re-run).
Chose a self-authored harness that loads both the pre-fix
(`main:gates/stale_revert_guard.py`) and post-fix
(`69a26bc7:gates/stale_revert_guard.py`) modules by path in the same
process, against fixtures built from primary git subprocess calls rather
than borrowed fixture-builder functions — this lets pre/post comparison
(Scenario C) run against byte-identical fixtures in one process instead of
reasoning about two separate checkouts drifting apart, and keeps the
probes distinct from `69a26bc7:gates/test_stale_revert_guard.py`'s own
`_commit_binary`/`_PNG_BYTES` helpers per this role's independence
requirement (a test suite authored by the same session that wrote the fix
can share its blind spots). Rejected re-running only
`69a26bc7:gates/test_stale_revert_guard.py` in place as the sole evidence:
that would corroborate the PR's own claims but not independently
re-derive them from primary evidence, which is what execution-observation
exists to do. Also rejected driving `merge_gate.py`'s CLI end-to-end: its
`main()` requires a live `gh pr view` call
(`main:gates/merge_gate.py:52-57`, `latest_check_runner_comment`) with no
local-fixture substitute, so re-execution goes through `check_pr()` — the
function `merge_gate.py` delegates to for exactly this check, and the one
named in the issue's own crash trace — instead.

## Upstream basis

- `69a26bc7a994056095699ed01aeab48d11497636:gates/stale_revert_guard.py`
  — the fix commit. derived: `git log --oneline -1 -- gates/stale_revert_guard.py`
  on `origin/issue-2314/implementation` → `69a26bc7 issue-2314: fix
  binary-file UnicodeDecodeError crash in stale_revert_guard`.
- `cfad1136f209828576aa7bfda9a58a14b9b0a6af:docs/issue-2314/reports/implementation.md`
  — PR #2323's own delivery record (commit-pinned; does not exist on this
  session's own branch) — read for its claims, then independently
  re-derived above rather than trusted.
- `gh pr view 2323 --json title,body,headRefName,baseRefName,files,state`
  — the PR's stated summary and file list.
- issue #2314 body — `## Acceptance` section (gate, empty-state, and
  provenance requirements re-executed above).

## Open findings

None. All three re-executed claims hold (Scenario A/B/C above).
derived: `git merge-base main origin/issue-2314/implementation` →
`e876c17e8869d11fb60b8edf094ece6c43ca9477`, and `git log --oneline
e876c17e..origin/main -- gates/merge_gate.py` → `ba879983 issue-2295: fix
silent packaged-gate-copy drift and gate-CLI argv crashes (#2307)` — the
`gates/merge_gate.py` argv-parsing lines that appear in a naive `git diff
main origin/issue-2314/implementation` are base drift from PR #2307
landing on `main` after PR #2323 branched, not a PR #2323 change — noted
so a future pass doesn't mistake it for scope creep, no resolution path
needed.

## Next steps

None — `loop_state: handed-off` is execution-observation's terminal state
(`roles/specs/execution-observation.spec.json`'s `loop_state.terminal`).
derived: re-run of both commands from "What was done", confirming the
terminal evidence still holds —
```
$ python3 /tmp/eo2314/harness.py | tail -1
TOTAL: 3/3 scenarios passed
$ (cd /tmp/eo2314/pr-checkout && python3 -m pytest -q gates/test_stale_revert_guard.py | tail -1)
11 passed in 1.13s
```
No further action items remain for this record.
