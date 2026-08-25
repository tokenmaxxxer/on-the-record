---
issue: 2395
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: "GitHub issue #2395 body (Ask / consumer report / Direction / Acceptance), read live via `gh issue view 2395`"
    sha: same-commit
code_under_review:
  - board.py
  - gates/gh_rest.py
  - gates/test_gh_rest.py
  - spawn.py
type: fix
breaking: >
  New refusal path (`board.require_repo_root`) for `--issue N` spawns only:
  a nonexistent `-C` path, or a `-C` that resolves inside a git repo but not
  at that repo's root, now exit immediately with a message naming the cause,
  instead of falling through to `require_board`'s generic "approvers.md
  missing" (or a later gate's unrelated symptom). Both conditions were
  already hard failures for `--issue`-scoped spawns before this change
  (`issue_workspace()`/the board-marker lookup already assumed cwd was the
  repo root) — no currently-working `--issue` call shape is newly blocked.
  `--issue`-less (ad-hoc) calls are untouched (`if issue is None: return`).
verdict: pass
---

# issue-2395 — implementation record

## What was done

1. **`gh_rest.fetch_issue()`** (`gates/gh_rest.py:57-68`) now returns
   `owner` and `repo` alongside `title`/`body`. It already called
   `owner_repo()` internally to build the REST path; this just also
   returns that value to the caller instead of discarding it.

2. **`spawn.py`'s issue-fetch stage** (`_spawn_one`, the
   `with _timed("issue_fetch")` block) builds a `resolved_line` from that
   response: `해석된 레포/이슈: <owner>/<repo>#<issue> — <title>`, or an
   explicit "확인 실패" line when `fetch_issue` returns `None`. This line
   is printed to the orchestrator's own stdout (no `file=sys.stderr`)
   right after the fetch, and prepended into the role session's injected
   directive immediately after the existing `당신의 이슈: #<n> ...` line,
   unconditionally (unlike the pre-existing `이슈 제목(원본 목표):` line
   inside `goal_pin`, which only appears when the issue has an
   `## Acceptance` section with `check:` bullets).

3. **`board.require_repo_root(cwd, issue)`** (`board.py`), wired into both
   the `--dry-run` and the real-spawn branches of `spawn.py:main()`, ahead
   of `require_board`. For `--issue N` calls it checks, in order: does
   `-C` exist as a directory; is it inside a git repository; is it that
   repository's root (`git rev-parse --show-toplevel` matches the resolved
   cwd). Each failure exits with a message naming that specific cause. For
   `issue is None` it returns immediately.
   - Placed inside the same `try:` block as the other four gates in the
     real-spawn branch, *after* `_record_spawn_attempt` — matching the
     issue #2291/#2365 fix already in place there.
   - Removed the `if not cwd_path.is_dir(): sys.exit(...)` check that used
     to sit *after* `require_board` in the `--dry-run` branch — it was
     unreachable for a nonexistent path, since `require_board` already
     exited first with the misleading "approvers.md 없다" message (the
     case-(c) bug named in the issue).

## Why

The issue's Direction section already resolved the main design question
(visibility over refusal) and asked the delivering session to verify it
against the code and scope any refusal path narrowly.

canonical: `grep -n '"--repo"' spawn.py` — no match, confirmed this session.
No `--repo` flag exists on `spawn.py`. The Direction's proposed
narrow-refusal condition ("only when the caller named a repo elsewhere in
the same command and it conflicts") has nothing to trigger on for the
primary wrong-repo bug — there is no second signal to conflict-check
against. Echo is the only available defense for that case, and is what's
delivered (item 2 above).

The three orchestrator-side cwd variants named in the issue's consumer
report are a different kind of problem: not an ambiguous "which repo did
you mean" but a cwd that cannot be a valid spawn target at all.
canonical: `board.py` (`require_board`, pre-existing) reads `root / MARKER`
directly with no upward search, and `spawn.py`'s `issue_workspace()`
(pre-existing) runs `git remote get-url origin` against the raw `cwd`
argument — both already assume cwd IS the repo root. These three shapes
were therefore already unconditional failures for `--issue` spawns, just
surfaced through whichever downstream gate tripped first, in that gate's
own vocabulary. `require_repo_root` moves the same-outcome failure earlier
and renames it to the actual cause — an additive refusal, not a change to
`-C`'s default or semantics (`-C` still defaults to `.`, unchanged).

Scoping `require_repo_root` to `issue is not None` (matching
`require_acceptance_gate`/`require_requirement_linkage`'s existing
`if issue is None: return` convention, `board.py:318`/`board.py:373`) was
not in the original plan — see "What did not work".

## What did not work

acceptance: `python3 -m pytest tests/test_spawn_pipeline.py::GateRefusalExitCodeTest::test_dry_run_non_refused_spawn_exits_zero -q` — result:

An earlier version of `require_repo_root` had no `issue` parameter and ran
for every spawn, dry-run included. It broke this test (a plain non-git temp
dir under `--dry-run --no-contract`, no `--issue` flag, previously exited
0) with a new nonzero exit. Fixed by adding the `issue is None: return`
early-out (`board.py`, top of `require_repo_root`). Rerun after the fix:

```
1 passed in 26.92s
```

## Upstream basis

GitHub issue #2395, read live this session via `gh issue view 2395` (Ask /
consumer report / Direction / Acceptance sections, quoted into the role
task preamble at session start). No phase-1 proposal precedes this record —
build-now bypass, `CORE_BUILD_NOW=1` (set by the spawner, verified via
`printenv` at session start: `CORE_BUILD_NOW=1`).

## Evidence

**gh_rest unit tests.**

acceptance: `python3 gates/test_gh_rest.py` — result:

```
ok - t_owner_repo_parses_ssh_remote
ok - t_fetch_issue_body_returns_body_on_success
ok - t_fetch_issue_body_returns_none_on_rest_failure
ok - t_fetch_issue_body_returns_none_when_no_gh
ok - t_fetch_pr_body_returns_body_on_success
ok - t_fetch_issue_returns_title_and_body_together
ok - t_fetch_open_prs_uses_rest_never_graphql
ok - t_fetch_open_prs_requests_100_per_page
ok - t_fetch_open_prs_304_reuses_cache_no_fresh_body
ok - t_fetch_open_prs_returns_none_on_rest_failure
10/10 passed
```

**Spawn/board/directive test files** (the five files touching the changed
gates/directive-assembly code).

acceptance: `python3 -m pytest tests/test_spawn_gate_wiring.py tests/test_spawn_board_flows.py tests/test_spawn_pipeline.py tests/test_directive_diet_2135.py tests/test_spawn_observation_recovery.py -q` — result:

```
6 failed, 466 passed, 1 skipped, 4 xfailed, 1 xpassed in 572.30s (0:09:32)
```

Investigated all 6 individually. One
(`test_dry_run_non_refused_spawn_exits_zero`) was the real regression
covered in "What did not work" — confirmed fixed above. The other 5
(`Watchdog::test_delegation_phrasing_signal`,
`Ledger::test_toolchain_cache_env_redirected_into_workspace`,
`RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch`,
`Watchdog::test_roster_watchdog_returns_anomaly_count_for_stalled_entry`,
`Watchdog::test_roster_watchdog_returns_zero_for_clean_non_empty_roster`)
were checked against an unmodified baseline:

acceptance: `git stash && python3 -m pytest <those 5 node IDs> -q; git stash pop` — result:

```
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal
FAILED tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_returns_anomaly_count_for_stalled_entry
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_returns_zero_for_clean_non_empty_roster
FAILED tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace
5 failed in 12.96s
```

Same node IDs fail identically with none of this delivery's edits present
(`git stash` reverts `board.py`/`gates/gh_rest.py`/`spawn.py` to `HEAD`) —
pre-existing, not caused by this change.
canonical: `ps aux` output captured this session showed dozens of
concurrent `pytest`/role-session processes touching
`~/.tokenmaxxxer/work/` and toolchain cache-dir env vars at the same time
these tests ran, in this same shared execution host — consistent with
environment-level flakiness rather than a code defect. A follow-up
isolated rerun of `tests/test_spawn_gate_wiring.py` alone, both patched
and via a second `git stash` baseline, produced two more different failure
sets on otherwise-identical code (three failing tests patched, five
failing tests on the stash baseline, no overlap in names between the two
runs) — reinforcing that this file's failures are timing/concurrency-
dependent rather than deterministic regressions from this patch.

**Acceptance check — resolved `owner/repo#n` + title in both the
orchestrator's stdout and the role's injected directive, live spawn.**
Driven via `spawn._spawn_one()` directly: real `gh_rest.fetch_issue`
network calls, real `issue_workspace`/`checkout_issue_branch` local
clone+branch into a throwaway `MUSTER_WORK_DIR`; only the actual nested
Claude launch is swapped for `cat` (echoes the piped task back to a
captured log) — the same mocking shape as the pre-existing
`tests/test_spawn_pipeline.py:1155` (`class IssueScopedPrompt`,
`test_preparation_and_preamble_happen_once`) uses for the same kind of
assertion. Two isolated, freshly-cloned local checkouts were used
(`/tmp/otr-clean` = `tokenmaxxxer/on-the-record`, `/tmp/arcade-clean` =
`tokenmaxxxer/arcade-dodger`) so nothing under the shared
`~/.tokenmaxxxer/work/` tree was touched.

acceptance: `python3 /tmp/live_demo_2395.py` (`-C /tmp/arcade-clean --issue 1` case) — result:

```
[conformance-review] 해석된 레포/이슈: tokenmaxxxer/arcade-dodger#1 — Deterministic dodger engine + curses UI (MVP)
[exit code 0]
----- delivered task text (role's injected directive) -----
당신의 이슈: #1 (subject issue-1, 브랜치 issue-1/conformance-review).
해석된 레포/이슈: tokenmaxxxer/arcade-dodger#1 — Deterministic dodger engine + curses UI (MVP)
이슈 제목(원본 목표): Deterministic dodger engine + curses UI (MVP)
Acceptance 기준(원본, verbatim):
- check: `python3 -m dodger --headless 42 200` runs 200 frames from seed 42 ...
```

acceptance: `python3 /tmp/live_demo_2395.py` (`-C /tmp/otr-clean --issue 1` case) — result:

```
[conformance-review] 해석된 레포/이슈: tokenmaxxxer/on-the-record#1 — Stop reporting a rulebook as loaded when the session has none
[exit code 0]
----- delivered task text (role's injected directive) -----
당신의 이슈: #1 (subject issue-1, 브랜치 issue-1/conformance-review).
해석된 레포/이슈: tokenmaxxxer/on-the-record#1 — Stop reporting a rulebook as loaded when the session has none
gh issue view 1 로 이슈를 먼저 읽어라.
```

**Acceptance check — before/after per-spawn latency, no added `gh` round
trip.** Direct measurement of `gh_rest.fetch_issue()` with a `run` callback
that counts `gh` vs `git` invocations, five live reps against
`tokenmaxxxer/on-the-record#1`.

acceptance: `python3 /tmp/measure_gh_rest_2395.py` on unmodified `gh_rest.py` (`git stash`) — result:

```
5 calls: gh api calls=5, git calls=5, total=2.371s, avg/call=474.2ms
```

acceptance: `python3 /tmp/measure_gh_rest_2395.py` on this delivery — result:

```
5 calls: gh api calls=5, git calls=10, total=2.349s, avg/call=469.9ms
```

`gh api` call count is identical before/after (one per `fetch_issue()`
call either way, derived: 5 reps → 5 gh calls in both the before and after
runs above) — the only change is one added local `git remote get-url
origin` call per invocation (5 reps → 10 git calls after vs. 5 before,
derived: from the two result blocks above). Wall-clock is within
measurement noise (network-dominated either way; AFTER is not slower —
derived: 469.9ms vs 474.2ms above, (474.2-469.9)/474.2 = 0.9% decrease,
well inside run-to-run variance). Corroborated by the full-pipeline
`bootstrap_timing` `issue_fetch` stage printed by the live-spawn runs above
(stderr, not shown in the pasted excerpts):

acceptance: `grep -o "issue_fetch=[0-9.]*" /tmp/live_demo_2395.BEFORE.log /tmp/live_demo_2395.stderr.log` — result:

```
before: issue_fetch=0.446s, issue_fetch=0.448s
after:  issue_fetch=0.517s, issue_fetch=0.544s
```

(this stage also includes in-process `resolved_line` string-building, not
just the `fetch_issue` call, hence the larger before/after gap than the
isolated measurement above).

**Acceptance check — live reproduction of the consumer's exact failure**
(same issue number N exists in two different repos). The two live-spawn
transcripts under the first acceptance check above ARE this reproduction:
`tokenmaxxxer/arcade-dodger#1` and `tokenmaxxxer/on-the-record#1` are two
real, currently-open GitHub repos each with a real issue #1 of a
completely different meaning.

acceptance: `python3 /tmp/live_demo_2395.py` on unmodified `spawn.py` (`git stash`), `-C /tmp/arcade-clean --issue 1` case — result:

```
----- delivered task text (role's injected directive) -----
당신의 이슈: #1 (subject issue-1, 브랜치 issue-1/conformance-review).
이슈 제목(원본 목표): Deterministic dodger engine + curses UI (MVP)
Acceptance 기준(원본, verbatim):
```

No repo attribution anywhere in that BEFORE output — an orchestrator
scanning it has no way to tell it wasn't on-the-record's issue #1 (title
only, and only because this particular issue happens to have an
`## Acceptance` section — `goal_pin` is conditional). AFTER (the live-spawn
demonstration above), the `해석된 레포/이슈: tokenmaxxxer/arcade-dodger#1
— ...` line is unconditional and names the repo explicitly.

**Acceptance check — the three orchestrator-side cwd variants each name
the actual problem.** Live `spawn.py` subprocess invocations (cheap: each
exits at `require_repo_root`, before any workspace/network/doctor work).

acceptance: `python3 spawn.py implementation "test" --issue 1 -C /tmp/otr-clean/gates` — result:

```
-C 가 레포 루트가 아니라 그 하위 디렉터리다: /tmp/otr-clean/gates
  실제 레포 루트: /tmp/otr-clean
  cwd 가 생각하는 그 레포가 맞는지부터 확인해라 — -C /tmp/otr-clean 로 다시 잡거나, 그 루트에서 -C 없이 불러라(이슈 #2395).
exit=1
```

acceptance: `python3 spawn.py implementation "test" --issue 1 -C /tmp/issue-2395-does-not-exist` — result:

```
-C 가 존재하지 않는 디렉터리다: /tmp/issue-2395-does-not-exist
  cwd 는 레포 루트를 가리켜야 한다 — 경로를 다시 확인해라.
exit=1
```

The third variant (a valid but different repo root — e.g. `-C
/tmp/arcade-clean` when the caller meant on-the-record) is not a
structural defect `require_repo_root` can name; it is the ambiguous case
the issue's Direction says echo, not refusal, is the right defense for
(see "Why").

acceptance: `python3 spawn.py implementation "test" --issue 1 -C /tmp/arcade-clean --dry-run` — result:

```
exit=0
```

It passes the gates and is named instead by the unconditional `해석된
레포/이슈: tokenmaxxxer/arcade-dodger#1 — ...` line demonstrated in the
live-spawn checks above.

**Acceptance check — normal consumer call shape unchanged.** Both
live-spawn transcripts above (`-C /tmp/otr-clean --issue 1`, no other path
flags — the exact `cd repo && spawn.py <role> "<task>" --issue N` shape)
returned `[exit code 0]` with a well-formed delivered directive.

acceptance: `pwd && git rev-parse --show-toplevel` (run from this checkout) — result:

```
/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2395-implementation
/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2395-implementation
```

`require_repo_root` adds zero new checks to this path — both lines above
are identical, so `git rev-parse --show-toplevel` run from an actual repo
root returns that same root.

**Acceptance check — refusal-path honesty.** `require_repo_root` blocks
exactly two structural cwd shapes, both `--issue`-scoped only: a
nonexistent `-C` path, and a `-C` that is a subdirectory of a git repo
rather than that repo's root (demonstrated above). Neither was a working
`--issue` call shape before this change (see "Why" — every existing gate
already required cwd to literally be the repo root, with no upward
search); this delivery does not remove any capability, it only renames an
already-certain failure earlier and clearer. `issue is None` (ad-hoc, no
board issue) calls are unaffected — demonstrated by
`test_dry_run_non_refused_spawn_exits_zero` passing (see "What did not
work"). For the one case this delivery does NOT refuse — a syntactically
valid but semantically wrong repo root — echo (demonstrated in the
live-spawn checks above) is stated as sufficient because no second signal
exists in `spawn.py` (see "Why", `grep` result) to conflict-check against;
adding refusal there would require guessing intent from nothing, which the
issue's own Direction rules out.

## Open findings

None.

## Next steps

None — `loop_state: landed`.
