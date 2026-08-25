---
issue: 2395
role: execution-observation
author: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2395/reports/implementation.md
    sha: a76df56f962f7206c2753a7d82638690828d235f
  - path: board.py
    sha: a76df56f962f7206c2753a7d82638690828d235f
  - path: gates/gh_rest.py
    sha: a76df56f962f7206c2753a7d82638690828d235f
  - path: spawn.py
    sha: a76df56f962f7206c2753a7d82638690828d235f
subject: PR #2404 (issue-2395, "echo resolved owner/repo#n + title, refuse
  structurally broken -C"), branch issue-2395/implementation, commits
  e74fc73112575e186694565517a9e11669c6954a / a76df56f962f7206c2753a7d82638690828d235f,
  merge-base ce7fadd78f49e685bcca0ad451aafb96f6d28a28
test: independent re-derivation of every falsifiable claim in
  docs/issue-2395/reports/implementation.md (untracked in this tree — lives
  on branch issue-2395/implementation at a76df56f) plus a fresh probe of the
  gate-ordering path the implementation record's own acceptance evidence
  never exercised — commands and outputs below, all run in this session's
  own git worktrees, never the implementation session's pasted transcripts
  taken as given
result: failed
assertedBy: execution-observation session for issue-2395, independent of PR
  #2404's authoring (implementation) session
---

# issue-2395 — execution-observation record

## What was done

canonical: this session's own `git worktree add /tmp/exec-obs-2395-1
origin/issue-2395/implementation` (detached at `a76df56f`), plus a
`git worktree add /tmp/eo2395-before ce7fadd7` pre-PR baseline, two fresh
local clones of real GitHub repos (`/tmp/eo2395-clean-arcade` =
`tokenmaxxxer/arcade-dodger`, `/tmp/eo2395-clean-otr` =
`tokenmaxxxer/on-the-record`), and independently-authored Python probe
scripts (`/tmp/eo2395_live_probe.py`, `/tmp/eo2395_live_probe_before.py`,
`/tmp/eo2395_latency.py` — not copied from the PR's own `/tmp/live_demo_2395.py`
/ `/tmp/measure_gh_rest_2395.py`, which no longer exist on disk) — never the
authoring session's claims taken as given.

### Claim 1 — `gh_rest.fetch_issue()` returns `owner`/`repo`, one added local `git` call, no added `gh` call (acceptance check 2)

acceptance: `git diff ce7fadd7 a76df56f -- gates/gh_rest.py` (branch
worktree) — result (excerpt):
```
-    return {"title": data.get("title", "") or "", "body": data.get("body", "") or ""}
+    owner_and_repo = owner_repo(repo, run=run)
+    owner, name = owner_and_repo if owner_and_repo else ("", "")
+    return {"title": data.get("title", "") or "", "body": data.get("body", "") or "",
+            "owner": owner, "repo": name}
```
`owner_repo()` (`a76df56f:gates/gh_rest.py:23-35`) is a local `git remote
get-url origin` call, not a `gh` API round trip — confirmed by reading the
function body directly this session.

acceptance: `python3 /tmp/eo2395_latency.py /tmp/eo2395-before` (own
script, counts `gh`/`git` invocations via an injected `run` callback, 5
live reps against `tokenmaxxxer/on-the-record#1`) — result:
```
5 calls: gh=5 git=5 total=4.857s avg/call=971.4ms
```
acceptance: `python3 /tmp/eo2395_latency.py /tmp/exec-obs-2395-1` — result:
```
5 calls: gh=5 git=10 total=5.613s avg/call=1122.6ms
```
`gh` call count identical (5 vs 5, derived: the two result blocks above);
`git` call count doubled (5 vs 10, i.e. +1 per `fetch_issue()` call,
derived: 10-5=5 added over 5 reps) — matches the record's own claim
exactly. Repeated twice more for wall-clock stability (network-dominated,
high run-to-run variance on this host): pair 2 `before=1160.9ms
after=1073.4ms` (after *faster*), pair 3 `before=891.0ms` (after run did
not complete before a tool timeout). Across the two complete pairs, mean
before ≈1066ms, mean after ≈1098ms (+3%, derived: (1098-1066)/1066≈3%,
inside run-to-run noise) — corroborates the record's own "AFTER is not
slower" reading, though my own numbers show more variance than the
record's single-pair ±1%.

not independently re-derived: `owner_repo()` is called twice per
`fetch_issue()` (once inside the pre-existing `_api_json()` to build the
REST URL, once again by the new code to populate the return dict) rather
than reusing the value `_api_json()` already computed — canonical:
`a76df56f:gates/gh_rest.py:38-43` (`_api_json`) and `:57-68`
(`fetch_issue`), read directly this session. A real but minor
inefficiency (one extra subprocess fork, not an extra network round trip)
that the record's own prose ("this just also returns that value ...
instead of discarding it") slightly overstates as reuse. Does not affect
the acceptance check's actual claim (no added `gh` round-trip), which
holds per the latency measurement above.

### Claim 2 — resolved `owner/repo#n` + title echoed to stdout and prepended into the delivered directive, unconditionally (acceptance check 1)

acceptance: own probe, `spawn._spawn_one()` called directly with only
`spawn_cmd`/`ensure_pushed`/`roster_register`/`ledger_write` mocked (same
narrow-mock shape as the pre-existing `tests/test_spawn_pipeline.py:1155`
`IssueScopedPrompt` test the record cites, independently re-derived rather
than reused) — real `gh_rest.fetch_issue` network calls, real
`issue_workspace`/`checkout_issue_branch` local clone+branch into an
isolated `MUSTER_WORK_DIR`. `python3 eo2395_live_probe.py
/tmp/eo2395-clean-arcade 1 conformance-review "AFTER arcade#1"` — stdout
result:
```
[conformance-review] 해석된 레포/이슈: tokenmaxxxer/arcade-dodger#1 — Deterministic dodger engine + curses UI (MVP)
```
delivered directive (session log,
`arcade-dodger-issue-1-conformance-review.session.*.log`), first two lines:
```
당신의 이슈: #1 (subject issue-1, 브랜치 issue-1/conformance-review).
해석된 레포/이슈: tokenmaxxxer/arcade-dodger#1 — Deterministic dodger engine + curses UI (MVP)
```
Repeated for `/tmp/eo2395-clean-otr` (real `tokenmaxxxer/on-the-record`,
also issue #1) — stdout:
```
[conformance-review] 해석된 레포/이슈: tokenmaxxxer/on-the-record#1 — Stop reporting a rulebook as loaded when the session has none
```
same line prepended in that run's delivered directive. canonical: both
session-log files under `/tmp/eo2395-workdir/`, this run. Matches the
record's own two-repo demonstration exactly, independently reproduced
against the same two real repos with fresh probe code.

### Claim 3 — before/after: no repo attribution anywhere in the pre-fix output (acceptance check 3, echo half)

acceptance: same probe pattern, `sys.path` pointed at
`/tmp/eo2395-before` (pre-PR worktree, `ce7fadd7`) instead —
`python3 eo2395_live_probe_before.py /tmp/eo2395-clean-arcade 1
conformance-review "BEFORE arcade#1"` — result: no
"해석된 레포/이슈" line anywhere in stdout (canonical:
`/tmp/eo2395_probe_before.log`, this run); delivered directive, first two
lines:
```
당신의 이슈: #1 (subject issue-1, 브랜치 issue-1/conformance-review).
이슈 제목(원본 목표): Deterministic dodger engine + curses UI (MVP)
```
Title only, no repo name — an orchestrator or role reading this cannot
tell it isn't on-the-record's own issue #1. Matches the record's "no repo
attribution anywhere in that BEFORE output" claim, independently
reproduced.

### Claim 4 — the three structurally-broken `-C` variants name the actual cause (acceptance check 4, two of three)

acceptance: `python3 spawn.py implementation "test" --issue 1 -C
/tmp/eo2395-fixtures/does-not-exist` (branch worktree) — result:
```
-C 가 존재하지 않는 디렉터리다: /tmp/eo2395-fixtures/does-not-exist
  cwd 는 레포 루트를 가리켜야 한다 — 경로를 다시 확인해라.
exit=1
```
acceptance: `python3 spawn.py implementation "test" --issue 1 -C
/tmp/exec-obs-2395-1/gates` — result:
```
-C 가 레포 루트가 아니라 그 하위 디렉터리다: /tmp/exec-obs-2395-1/gates
  실제 레포 루트: /tmp/exec-obs-2395-1
exit=1
```
Both messages independently reproduced, own fixture paths (not the
record's own `/tmp/otr-clean`), same wording and cause-naming as the
record's claim.

acceptance: `python3 spawn.py implementation "test" --issue 2395 -C
/tmp/exec-obs-2395-1 --dry-run` (valid repo root, real linked issue) —
result:
```
exit=0
```
canonical: own command output above, this same record — no cwd-refusal
message, confirming `require_repo_root` passes a genuinely valid root
through cleanly (own case, not in the record).

### Claim 5 — normal consumer call shape unchanged (acceptance check 5)

canonical: Claim 2 above, this same record — both probes ended `exit=0`
with a well-formed delivered directive using the exact `-C <repo> --issue
N` shape (no other path flags) — independently reproduced, matches.

### Claim 6 — no `--repo` flag exists; refusal-path honesty (acceptance check 6)

acceptance: `grep -n '"--repo"' spawn.py` (branch worktree) — result: no
match. canonical: own grep above, this same record — independently
confirms the record's own basis for scoping `require_repo_root` to only
the two unambiguous structural failures and leaving the "valid but wrong"
repo-root case to the echo alone.

### Claim 7 (not asserted by the PR, found independently) — the echo does not fire when a wrong-repo resolution also fails an earlier gate, reproducing the exact consumer incident the issue reports

`require_repo_root`/`require_board`/`require_no_repo_config`/
`require_acceptance_gate`/`require_requirement_linkage` all run in
`main()`, **before** `_spawn_one()` is ever called — and the new
"해석된 레포/이슈" echo lives entirely inside `_spawn_one()`'s issue-fetch
block (Claim 2's own citation, `a76df56f:spawn.py:2354` region).
canonical: `a76df56f:spawn.py:1655-1670` and `:1697-1703` (both `main()`
gate-call sites, read directly this session) versus `:2354-2373`
(`_spawn_one`'s echo block) — the gate calls are in a different function,
called earlier, with a `sys.exit`/refusal path that returns before
`_spawn_one` is ever reached.

If a wrong-repo cwd resolves to an issue that also fails
`require_acceptance_gate` or `require_requirement_linkage` — exactly the
shape the issue's own body reports happened for `#574` — the spawn is
refused before `_spawn_one()` runs at all, so the echo never prints.
Independently reproduced this session:

acceptance: `python3 spawn.py execution-observation "test task" --issue
574 -C /tmp/eo2395-clean-otr --no-wait` (branch worktree, real
`tokenmaxxxer/on-the-record` clone, real on-the-record issue #574) —
result:
```
[acceptance-gate] 경고: 이슈 #574 의 'Acceptance' 절이 지금 형식대로면 phase-2 승인 후 스폰이 거절된다:
  - 이슈 #574 본문에 '## Acceptance' 절이 없다 ...
이슈 #574 가 요구 연결이 없다:
  - 이슈 #574 본문이 요구 ID(`R\d+` 또는 'northpole req#<n>')를 하나도 인용하지 않고 ...
  세션을 안 띄운다 ...
exit=1
```
No "해석된 레포/이슈" line anywhere in this output — the orchestrator sees
exactly the same undifferentiated "no requirement linkage" downstream
symptom the issue's own consumer report names ("An earlier `#574
conformance-review` respawn ... was rejected as 'no requirement linkage' —
same cause, grading on-the-record's #574"). This is the exact acceptance
check 3 failure mode, still live on this PR's own head commit — canonical:
own command output above, this same record.

This finding was reached independently (own probe, own issue number,
before reading any other review of this PR) and then found to match
PR #2408 ("issue-2395: builder-blind conformance review of PR #2404",
branch `issue-2395/conformance-review`), which reports the same root
cause against the same code region and additionally names it as affecting
acceptance check 4's "wrong repo root" variant too — a syntactically
valid but semantically wrong repo root that happens to fail
`require_acceptance_gate`/`require_requirement_linkage` gets no echo
either, undermining the issue's own "echo alone is sufficient" defense for
that case (see the issue's Direction section). canonical: `gh pr view 2408
--json body`, read this session — cross-check only, not the source of
this claim; I did not copy PR #2408's repro, and the `on-the-record#574`
case above is my own choice, made before reading that PR's body.

### Claim 8 — test suite: gh_rest unit tests and the targeted acceptance test both pass, independently reproduced

acceptance: `python3 gates/test_gh_rest.py` (branch worktree) — result:
```
10/10 passed
```
identical to the record's claim.

acceptance: `python3 -m pytest
tests/test_spawn_pipeline.py::GateRefusalExitCodeTest::test_dry_run_non_refused_spawn_exits_zero
-q` — result:
```
1 passed in 1.44s
```
confirming `issue is None` (ad-hoc) calls remain unaffected by
`require_repo_root`.

### Claim 9 — the wider 5-file suite's failure set is unstable across runs/hosts, broader than the record's own disclosure, but orthogonal to this PR's code

acceptance: `python3 -m pytest tests/test_spawn_gate_wiring.py
tests/test_spawn_board_flows.py -q` (branch worktree, this session, no `-n
auto`) — result:
```
4 failed, 201 passed in 441.35s
```
Failing:
`RoleSessionSandboxRemoved::test_sandbox_never_enabled_regardless_of_role_declaration`,
`WebToolPermissionAccess::test_role_declared_permissions_allow_entries_preserved`,
`Ledger::test_toolchain_cache_env_redirected_into_workspace`,
`RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch`.
derived: comparing these 4 node IDs against the record's own listed 5
(`docs/issue-2395/reports/implementation.md` "Investigated all 6
individually" paragraph, untracked in this tree, at a76df56f) — only
`Ledger::test_toolchain_cache_env_redirected_into_workspace` and
`RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch`
overlap; the other 2 are new, not in the record's list. Re-run of just
those 2 new failures in isolation:

acceptance: `python3 -m pytest
tests/test_spawn_gate_wiring.py::RoleSessionSandboxRemoved::test_sandbox_never_enabled_regardless_of_role_declaration
tests/test_spawn_gate_wiring.py::WebToolPermissionAccess::test_role_declared_permissions_allow_entries_preserved
-q` — result:
```
2 passed in 8.39s
```
Both pass in isolation — flaky, not a deterministic regression; neither
test's subject (`role_settings()` sandbox/permission merging) is anywhere
in this PR's diff (canonical: `git diff ce7fadd7 a76df56f --stat` output
below, this same record).

acceptance: `python3 -m pytest tests/test_spawn_pipeline.py
tests/test_directive_diet_2135.py tests/test_spawn_observation_recovery.py
-q` — result:
```
5 failed, 263 passed, 4 xfailed, 1 xpassed in 78.34s
```
all 5 in the `Watchdog` class of `tests/test_spawn_observation_recovery.py`
(file exists, confirmed via this pytest run itself). derived: comparing
these 5 against the record's list — 3 overlap
(`test_delegation_phrasing_signal`,
`test_roster_watchdog_returns_anomaly_count_for_stalled_entry`,
`test_roster_watchdog_returns_zero_for_clean_non_empty_roster`), 2 are new
(`test_roster_watchdog_folds_board_wide_sweep_into_anomaly_count`,
`test_roster_watchdog_reports_completed_for_session_end_written_after_arming_turn`).
Re-run of just `Watchdog` in isolation reproduces the same 5 (not flaky at
the class level, this run):
```
5 failed, 32 passed in 71.78s
```
e.g. `test_roster_watchdog_returns_zero_for_clean_non_empty_roster` fails
with `AssertionError: 135 != 0`.

derived: `ps aux | grep -c pytest` at observation time — result: `233`
pytest-related processes alive on this shared host, including
multi-day-old idle `pytest-xdist` workers (`[pytest-xdist idle]`, PIDs
dated `8월22`, i.e. 3 days stale) never reaped. `roster_watchdog()`'s
returned anomaly count (`135`, `134` in a second isolated rerun) tracking
host-wide process counts rather than the fixture's own single roster entry
is consistent with the watchdog's anomaly detection reading real host
process state, not a fixture-isolated one.

acceptance: `cd /tmp/eo2395-before && python3 -m pytest
tests/test_spawn_observation_recovery.py -k Watchdog -q` (pre-PR code,
same shared host) — result:
```
1 failed, 36 passed in 368.11s
```
only `test_delegation_phrasing_signal` — a *different* single-test
failure, and a 5x longer runtime than the after-branch's 71.78s run
(derived: 368.11/71.78≈5.1x), consistent with host-load variance rather
than a deterministic before/after comparison.

canonical: `git diff ce7fadd7 a76df56f --stat` (branch worktree) — result:
```
board.py                                  |  44 ++
docs/issue-2395/reports/implementation.md | 379 ++
gates/gh_rest.py                          |  10 +-
gates/test_gh_rest.py                     |   3 +-
spawn.py                                  |  34 +-
```
`roster_watchdog`/`diagnose_health`/`_board_wide_sweep` (the `Watchdog`
class's subject functions) are not in this diff at all.

This independently corroborates the record's own claim (test-file
failures here are timing/concurrency-dependent, not deterministic
regressions from this patch) with more samples than the record itself
ran, while showing the record's specific enumerated failure list
undersells how unstable the signal actually is on this host.

### Claim 10 — mergeability against the current main tip

acceptance: `gh pr view 2404 --json mergeable,mergeStateStatus` — result:
```
{"mergeable":"CONFLICTING","mergeStateStatus":"DIRTY"}
```
acceptance: `git merge --no-commit --no-ff origin/main` (branch worktree,
`a76df56f`) — result: one conflicting file,
`git diff --name-only --diff-filter=U` → `.orchestrate-hook-fires.log`
only. `git diff ce7fadd7 origin/main -- .orchestrate-hook-fires.log` shows
a single appended timestamp line — a shared, append-only hook-fire log,
not any of this PR's own three code files. `git merge --abort` run
immediately after, no trace left in this observation's own tree. Real but
low-severity: trivially resolved (take-both/re-append), and the branch's
own merge-base (`ce7fadd7`) is 7 commits behind the current `origin/main`
tip (derived: `git log --oneline ce7fadd7..origin/main | wc -l` → `7`,
this session), ordinary unrebased-branch drift on a fast-moving shared log
file, not a content conflict in
`board.py`/`gates/gh_rest.py`/`spawn.py` themselves.

## Why

skill-verdict: defect-verification-independence-from-upstream-verdicts —
applied: canonical: Claim 7 above, this same record — the gate-ordering
defect was found by this session's own choice of probe (`on-the-record`
issue `#574`, chosen before reading any other review of this PR) rather
than by citing PR #2408's already-filed finding, and Claim 9 ran two
additional independent isolation passes and a `ps aux` host-load check
beyond what either the implementation record or the conformance-review
record report.

canonical: a76df56f962f7206c2753a7d82638690828d235f:docs/issue-2395/reports/implementation.md:25
(`verdict: pass`) — the record this session set out to independently
falsify rather than accept on the strength of its own frontmatter. Six of
the issue's six acceptance checks were independently re-derived as
claimed (Claims 1-6, 8); Claim 7 shows acceptance check 3 (and part of
check 4) is not actually met on this PR's own head commit for the specific
failure shape the issue exists to fix — a wrong-repo resolution that also
trips an earlier board gate reproduces the exact "no requirement linkage"
symptom from the issue's own consumer report, with no repo-attribution
echo anywhere in the refusal. This is a genuine gap in the delivered fix,
not a documentation-only nit: the issue's Direction section explicitly
scoped refusal narrowly and named echo as the primary defense against
exactly this incident shape, and the delivered echo does not reach the one
code path (early gate refusal) the original incident actually took.

## Upstream basis

- docs/issue-2395/reports/implementation.md, PR #2404, branch
  issue-2395/implementation (untracked in this tree). sha:
  a76df56f962f7206c2753a7d82638690828d235f
- board.py, gates/gh_rest.py, gates/test_gh_rest.py, spawn.py, same branch
  (untracked in this tree). sha: a76df56f962f7206c2753a7d82638690828d235f
- PR #2408 ("issue-2395: builder-blind conformance review of PR #2404"),
  branch issue-2395/conformance-review — read after independently reaching
  Claim 7, used only to cross-check (not derive) the finding. Not this
  record's own upstream input for any other claim.
- main tip at observation time, `20ace71a...` (`issue-2382: builder-blind
  conformance review of PR #2392`) — the mergeability target for Claim 10.
  sha: 20ace71a

## Open findings

- Claim 7 above, this same record: the resolved-repo echo lives entirely
  inside `_spawn_one()`, which `main()`'s gate chain (`require_repo_root` /
  `require_board` / `require_no_repo_config` / `require_acceptance_gate` /
  `require_requirement_linkage`) can refuse before ever reaching — so a
  wrong-repo cwd whose resolved issue also fails an earlier gate reproduces
  the exact pre-fix "downstream symptom, no repo attribution" failure the
  issue reports, live-reproduced against real `on-the-record#574` above.
  Resolution path: move (or duplicate) the resolved-repo echo ahead of
  `require_acceptance_gate`/`require_requirement_linkage` in `main()`'s
  gate chain — those two gates already need the fetched issue body/title,
  so the echo could reuse that same `gh_rest.fetch_issue()` call already
  being made there instead of introducing a second one; alternatively,
  have each of those two gates' own refusal messages prepend the resolved
  `owner/repo#n` line themselves. Either way this needs re-verification
  live against the same `on-the-record#574` reproduction above before it
  can be marked closed. Independently corroborated by PR #2408 (canonical:
  Claim 7 above).
- Claim 9 above, this same record: `tests/test_spawn_gate_wiring.py` /
  `tests/test_spawn_board_flows.py` / the `Watchdog` class of
  `tests/test_spawn_observation_recovery.py` produce a different failing-
  test set on every run on this shared host (233 concurrent pytest
  processes observed, some idle `pytest-xdist` workers 3 days stale) — not
  resolved this session, out of this role's write scope. Resolution path:
  reap the stale idle `pytest-xdist` workers and/or isolate
  `roster_watchdog()`'s process-state inspection from real host `/proc`
  state in tests (it currently appears to read live host process counts
  rather than a fixture-scoped view) — a pre-existing environmental issue,
  not something this PR introduced.
- Claim 10 above, this same record: PR #2404 does not currently merge
  cleanly into `origin/main` — a single-file, single-line conflict in
  `.orchestrate-hook-fires.log` (an append-only shared log, not this PR's
  own code). Resolution path: whoever lands this PR re-fetches/rebases
  onto current `origin/main` and takes both log lines (or re-appends after
  merge) — trivial, does not require touching
  `board.py`/`gates/gh_rest.py`/`spawn.py`.

## Next steps

None — loop_state handed-off is terminal for this role. Closing Claim 7
(the gate-ordering fix) is out of this role's own write scope; it belongs
to whichever session next touches issue-2395/implementation or opens a
follow-up round.

## What did not work

None.
