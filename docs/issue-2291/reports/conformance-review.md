---
issue: 2291
role: conformance-review
author: conformance-review
loop_state: reported
upstream:
  - path: gates/state_paths.py
    sha: 6e406a1acf97b0f10a56171a997856ac9237de5d
  - path: board.py
    sha: same-commit
subject: PR #2305 (tokenmaxxxer/on-the-record) — durable spawn-attempt trace
  + watchdog pre-workspace halt visibility, branch issue-2291/implementation,
  head 53347a118202acfddd7024ab1e88d511019b694f
test: issue #2291 body (`## Ask` bullets 1-2, `## Acceptance` gate/empty
  state/provenance, frozen-constraint paragraph), decomposed into R1-R11 below
result: failed
assertedBy: issue-2291/conformance-review session (builder-blind), 2026-08-25
---

# issue-2291 — conformance-review record

## What was done

Builder-blind conformance review of PR #2305 against issue #2291's frozen
`## Ask`/`## Acceptance` text and its "Frozen constraint" paragraph,
independent of the PR's own
`53347a118202acfddd7024ab1e88d511019b694f:docs/issue-2291/reports/implementation.md`
self-assessment (untracked on this `conformance-review` branch, PR-only path
— cited by sha throughout, never trusted as evidence on its own).

canonical: `gh issue view 2291`, `gh issue view 2291 --json comments`, `gh pr
view 2305`, `gh pr view 2305 --json headRefName,headRefOid,baseRefName,files`,
then `git fetch origin issue-2291/implementation` + `git worktree add
/tmp/pr2305-wt 53347a118202acfddd7024ab1e88d511019b694f` (PR #2305 head) — all
run live this session; every citation, test run, and independent probe below
was read/executed this session, not reused from the builder's account.

Requirement extraction (conformance-review-requirement-extraction): issue
#2291's `## Ask` bullet 1 bundles three independent obligations with "and" —
split into R1 (append the record before any network/workspace work, to a
STATE_ROOT-scoped, never-target-repo location), R2 (append the outcome when
known), R3 (every halt in that window lands its reason even when stdout is
swallowed). Bullet 2 is already singular (R4). The unlabelled "Frozen
constraint" paragraph bundles four sub-clauses — split per the same rule into
R5 (systemic), R6 (no added overhead), R7 (no new conflict/stall surfaces),
R8 (nothing written into the consumer's tree), matching how the issue-2312
review record treated the identically-worded frozen-constraint bundle.
`## Acceptance`'s three lines (gate/empty state/provenance) are each already
singular — R9/R10/R11, no split needed.

Requirement count derived: `## Ask` bullet 1 (3 obligations) + bullet 2 (1) +
frozen constraint (4 sub-clauses) + `## Acceptance` (3 lines) = 3+1+4+3 = 11
items — canonical: `gh issue view 2291`'s output this session, full
enumeration, no sampling needed (one PR, 7 changed files per `gh pr view
2305 --json files`).

Requirement list (dimension-tagged, rule 6):
- **R1** (functional) — append a durable spawn-attempt record (issue, role,
  pid, ts) *before any network or workspace work*, to an orchestrator-scoped
  location (STATE_ROOT per #2240 — never the target repo).
- **R2** (functional) — append the outcome (halt reason or session-log path)
  when known.
- **R3** (error-handling) — every `_fetch_or_halt`-class halt must land its
  reason there even when stdout is swallowed.
- **R4** (functional) — a spawn-attempt record with no matching roster entry
  after a grace period is a reportable state; the watchdog surfaces it.
- **R5** (scope-boundary) — frozen constraint: systemic for all consumer
  sessions.
- **R6** (scope-boundary/edge-case) — frozen constraint: no added overhead.
- **R7** (scope-boundary/edge-case) — frozen constraint: no new
  conflict/stall surfaces.
- **R8** (scope-boundary) — frozen constraint: nothing written into the
  consumer's tree.
- **R9** (functional/gate) — gate: `tests/test_spawn_pipeline.py` passes.
- **R10** (edge-case) — empty state: a successful spawn — the attempt record
  gains a `"session-log"` outcome and the watchdog reports nothing new.
- **R11** (functional/evidence) — provenance: executed-live, a real
  `_fetch_or_halt` halt forced with spawn stdout piped through `tail`, the
  halt reason present in the durable trace, and the watchdog's next tick
  naming the pre-workspace halt — real pasted output of both.

## Why

This role's mandate is builder-blind re-derivation, not reuse of the
implementation record's own account. Every code citation below was read from
a fresh `git worktree` at the PR's head commit, and every acceptance/probe
command was re-run independently this session with fixtures deliberately
different from the builder's own — different synthetic issue numbers, seen
in the R1/R2/R4/R10/R11 findings blocks below (their own `derived`/pasted
command output), different unreachable-remote paths, and direct-function-call
reproductions instead of replaying the builder's own script — per
verdict-assignment rule 6 (re-check a leaning-negative verdict against the
artifact before finalizing it) and to avoid rubber-stamping the exact
scenario the builder already exercised.

Mid-review incident, disclosed for the record: while probing R1/R3 (whether
a halt in `main()`'s *pre*-instrumentation gates — `require_acceptance_gate`/
`require_requirement_linkage` — is traced), an early probe invoked the real
`spawn.py` CLI entry point end-to-end (`python3 spawn.py implementation
"synthetic real halt probe" --issue 99999999 -C /tmp/otr2291-scratch
--no-contract`, this session, unmocked) against a real GitHub remote with a
nonexistent issue number. It did not halt where expected and instead
completed a real spawn — acceptance: `ps aux` (this session, captured
immediately after) — result:
```
jwjung   1923350  ...  python3 -c ... spawn.main() ...
jwjung   1923351  ...  /usr/bin/python3 /tmp/pr2305-wt/spawn.py -C .../on-the-record-issue-99999999-implementation watch --issue 99999999 --role implementation ...
jwjung   1923353  ...  claude -p --settings ... --permission-mode bypassPermissions --output-format stream-json ...
```
and `pgrep -P 1923350` returning `1923353`, confirming pid 1923353 (a real
`claude -p --permission-mode bypassPermissions` agent session) was a live
child of this review's own probe script — not the intended effect (the
intent was to inspect a halt path, not spawn a session).

canonical: this session's own `kill -TERM 1923353 1923350 1923351` followed
by `ps -p 1923353,1923350,1923351 -o pid,cmd` returning nothing (exit code
1) — all three processes confirmed terminated within seconds of discovery,
before committing or pushing anything.

canonical: `cd .../on-the-record-issue-99999999-implementation && git
status && git log --oneline -5 && git branch -vv && git remote -v`, this
session, run before cleanup — showed the branch `issue-99999999/implementation`
sitting on `[origin/main]` (never diverged/pushed) with only uncommitted
scratch files; `gh pr list --search 99999999 --state all` returned no rows.
The scratch workspace was removed afterward
(`rm -rf .../on-the-record-issue-99999999-implementation*`, this session,
confirmed by a follow-up `ls`/`pgrep -af 99999999` both empty).

All *subsequent* R1/R3 probing used safe, non-CLI reproductions instead
(direct calls to the same functions `main()` calls, e.g.
`board.require_requirement_linkage` forced via a controlled `SystemExit` of
the same shape it already raises in production, and
`pipeline._fetch_or_halt`/`watchdog.roster_watchdog()` called directly
against scratch git repos with unreachable remotes) — none of which spawn a
session; see R1/R4 findings below for the exact commands and pasted output,
and "## What did not work" below for this incident stated plainly.

## Upstream basis

- `53347a118202acfddd7024ab1e88d511019b694f:docs/issue-2291/reports/implementation.md`
  (PR #2305 branch `issue-2291/implementation`, untracked on this
  `conformance-review` branch — hence the sha pin throughout this record)
- `spawn.py`, `roster.py`, `watchdog.py`, `board.py`, `pipeline.py`,
  `plumbing.py`, `gates/requirement_linkage.py`, `gates/ci.py`
  (`53347a118202acfddd7024ab1e88d511019b694f`)
- issue #2291 body (`## Ask`, `## Acceptance`, frozen-constraint paragraph)
  and its corrective comment (`issuecomment-5403883219`), read this session
  via `gh issue view 2291` / `gh issue view 2291 --json comments`
- PR #2305 (`tokenmaxxxer/on-the-record`, branch `issue-2291/implementation`,
  head `53347a118202acfddd7024ab1e88d511019b694f`), read via `gh pr view
  2305` and a local worktree checkout of that commit (`/tmp/pr2305-wt`)

## Requirement findings

---
requirement: R1 — append a durable spawn-attempt record before any network
  or workspace work, STATE_ROOT-scoped (never the target repo)
spec_ref: issue #2291 body, `## Ask` bullet 1, "before any network or
  workspace work, append a spawn-attempt record ... to an orchestrator-scoped
  location (STATE_ROOT per #2240 — never the target repo)"
verdict: Incorrect
evidence: `53347a11:spawn.py:1564-1569` (`require_board`,
  `require_no_repo_config`, `require_acceptance_gate`,
  `require_requirement_linkage`, all called in that order) vs.
  `53347a11:spawn.py:1597` (`_record_spawn_attempt(...)`, the first line of
  the new #2291 instrumentation) — the four board-gate calls run
  unconditionally *before* line 1597 for every non-dry-run `--issue` spawn.
  `53347a11:board.py:295-333` (`require_acceptance_gate`) and
  `53347a11:board.py:352-396` (`require_requirement_linkage`) both call
  `gates/ci.py:226-259`'s `_approved_roles_on_issue()`, which calls
  `53347a11:plumbing.py:145-...`'s `_issue_comments()` — a real `gh api`
  subprocess call (network) — and both can `sys.exit()` (board.py:332-333 for
  a malformed-Acceptance phase-2 halt, board.py:391-396 for a missing
  requirement-ID-linkage halt on a fresh issue).
rationale: independent Inspection of the exact call order in `main()`
  confirmed network work (the `gh api` call inside `_approved_roles_on_issue`)
  and two live `sys.exit()`-capable gates both precede
  `_record_spawn_attempt()`.

canonical: `grep -n "def main\|require_board(\|require_no_repo_config(\|require_acceptance_gate(\|require_requirement_linkage(\|if a.dry_run:\|_record_spawn_attempt(" spawn.py`, this session, PR head worktree — result:
```
1564:    require_board(a.cwd, a.no_contract or a.dry_run)
1567:    require_no_repo_config(a.cwd, a.trust_repo_config)
1568:    require_acceptance_gate(a.cwd, a.issue)
1569:    require_requirement_linkage(a.cwd, a.issue)
1570:    if a.dry_run:
1597:    attempt_id = (_record_spawn_attempt(a.issue, a.role, os.getpid())
```

Re-checked with a live Demonstration (verdict-assignment rule 6), using the
same `sys.exit()` shape `require_requirement_linkage` already raises in
production rather than inventing a new failure mode — acceptance:
```
$ python3 -c "
import tempfile, os, sys
sys.path.insert(0, '.')
os.environ['MUSTER_STATE_ROOT'] = tempfile.mkdtemp(prefix='otr2291state3_')
import spawn
from unittest import mock
def fake_halt(cwd, issue):
    sys.exit('이슈 #9903 가 요구 연결이 없다 (synthetic, forced — same sys.exit shape board.require_requirement_linkage already uses)')
with mock.patch.object(spawn, 'require_requirement_linkage', side_effect=fake_halt):
    sys.argv = ['spawn.py', 'implementation', 'synthetic halt probe', '--issue', '9903', '-C', '/tmp/otr2291-scratch', '--no-contract']
    try:
        spawn.main()
        print('main() returned normally — UNEXPECTED')
    except SystemExit as e:
        print('main() raised SystemExit as expected:', e)
print('trace file exists after the halt:', spawn.SPAWN_ATTEMPTS_PATH.exists())
"
```
result:
```
main() raised SystemExit as expected: 이슈 #9903 가 요구 연결이 없다 (synthetic, forced — same sys.exit shape board.require_requirement_linkage already uses)
trace file exists after the halt: False
```
  `SPAWN_ATTEMPTS_PATH` is not merely missing an entry — the file is never
  even created, because `_record_spawn_attempt()` (the function that creates
  it) has not been reached yet at the point this halt fires. The
  implementation record's own "What was done" claims this trace is wired in
  "before `require_doctor()`/`ensure_target_remote()` (the first network
  call)" (canonical:
  `53347a118202acfddd7024ab1e88d511019b694f:docs/issue-2291/reports/implementation.md`
  lines 36-43, "## What was done" bullet 1) — that characterization is
  itself wrong per the grep and acceptance run above: `require_acceptance_gate`/
  `require_requirement_linkage` already perform a real network call and can
  already halt, earlier in the same function.
spec_vs_built: issue #2291 Ask bullet 1 requires the durable record to exist
  "before any network or workspace work" — unqualified. PR #2305 built the
  instrumentation to start after four pre-existing board gates, two of which
  (`require_acceptance_gate`, `require_requirement_linkage`) already perform
  a real `gh api` network call and can already fail-closed via `sys.exit()`.
  A halt in either of those two gates reproduces the exact traceless-halt bug
  class issue #2291 was filed to fix (a fail-closed `sys.exit()` in a window
  with no durable trace, swallowed by a `2>&1 | tail` pipe) — just one layer
  earlier in `main()` than the window PR #2305 actually instruments.

---
requirement: R2 — append the outcome (halt reason or session-log path) when
  known
spec_ref: issue #2291 body, `## Ask` bullet 1, "append the outcome (halt
  reason or session-log path) when known"
verdict: Present
evidence: `53347a11:spawn.py:1598-1615` (`try/except (SystemExit,
  Exception)` around `require_doctor()`/`ensure_target_remote()`/
  `_spawn_one()`, calling `_record_spawn_outcome(attempt_id, "halted",
  reason)` in the `except` branch) and `53347a11:spawn.py:2932-2938`
  (`_record_spawn_outcome(attempt_id, "session-log", str(log_path))` at the
  point the live-log path is computed)
rationale: independent re-derivation, different fixture than the builder's
  (issue 9901 vs. the builder's 538 per
  `53347a118202acfddd7024ab1e88d511019b694f:docs/issue-2291/reports/implementation.md`
  line ~305), isolated `MUSTER_STATE_ROOT` — acceptance:
```
$ python3 -c "
import tempfile, os, sys
sys.path.insert(0, '.')
os.environ['MUSTER_STATE_ROOT'] = tempfile.mkdtemp(prefix='otr2291state_')
import spawn, roster
aid = spawn._record_spawn_attempt(9901, 'implementation', 424242)
spawn._record_spawn_outcome(aid, 'session-log', '/fake/path/session.log')
n = roster.spawn_attempt_sweep(d_all={})
print('independent empty-state anomaly count (expect 0):', n)
print(spawn.SPAWN_ATTEMPTS_PATH.read_text())
"
```
result:
```
independent empty-state anomaly count (expect 0): 0
{"event": "spawn_attempt", "attempt_id": "9901:implementation:424242:1787634874126", "issue": 9901, "role": "implementation", "pid": 424242, "ts": 1787634874.1264691}
{"event": "spawn_attempt_outcome", "attempt_id": "9901:implementation:424242:1787634874126", "outcome": "session-log", "detail": "/fake/path/session.log", "ts": 1787634874.126685}
```
  both event lines land in the trace, distinctly keyed by `attempt_id`, for
  the window this PR actually instruments (scoped separately from R1's
  finding, which is about an earlier, uninstrumented window).

---
requirement: R3 — every `_fetch_or_halt`-class halt lands its reason in the
  durable trace even when stdout is swallowed
spec_ref: issue #2291 body, `## Ask` bullet 1, "Every `_fetch_or_halt`-class
  halt must land its reason there even when stdout is swallowed"
verdict: Incorrect
evidence: same as R1 — `53347a11:board.py:332-333`,
  `53347a11:board.py:391-396`
rationale: "every" is the operative word this clause adds beyond R1's
  placement claim, and it is falsified by the same Demonstration cited under
  R1 above (`trace file exists after the halt: False`): a halt in
  `require_requirement_linkage` (not literally `pipeline.py:810`'s
  `_fetch_or_halt`, but the same fail-closed
  `sys.exit()`-in-a-swallowed-stdout-window failure shape the issue's own
  "Ask" prose is written broadly enough to cover — "before any network or
  workspace work") produces zero trace, not a trace with a `"halted"`
  outcome. Within the window PR #2305 actually instruments (`require_doctor`
  onward), the claim holds — see R1's Incorrect verdict for why the window
  itself starts too late relative to the issue's own wording.
spec_vs_built: see R1 — the same gap.

---
requirement: R4 — a spawn-attempt record with no matching roster entry after
  a grace period is reportable; the watchdog surfaces it
spec_ref: issue #2291 body, `## Ask` bullet 2
verdict: Present
evidence: `53347a11:roster.py` (new `SPAWN_ATTEMPT_GRACE_SEC = 180 + 60 + 60`
  and `spawn_attempt_sweep()`), `53347a11:watchdog.py:1480-1483`
  (`anomaly_count += _sp.spawn_attempt_sweep(d_all=d_all)`, called
  immediately after `lease_reconcile_sweep` and before the `if not d:` early
  return further down)
rationale: `CLONE_TIMEOUT`/`NETWORK_TIMEOUT` = 180/60 derived: `grep -n
  "^CLONE_TIMEOUT\|^NETWORK_TIMEOUT" *.py`, this session, PR head worktree —
  result: `plumbing.py:38:NETWORK_TIMEOUT = 60`,
  `spawn.py:538:CLONE_TIMEOUT = 180` — matching `roster.py`'s
  `SPAWN_ATTEMPT_GRACE_SEC = 180 + 60 + 60` comment exactly (180+60+60=300).
  Independent live Demonstration, different fixture (issue 9905, a different
  unreachable-remote path, direct function calls rather than the builder's
  CLI-level repro), unrelated board/lease/standing-red sweeps mocked out to
  isolate `spawn_attempt_sweep` — no session spawned by this repro (safe,
  non-CLI, per the incident noted under "## Why") — acceptance:
```
$ python3 -u -c "
import os, sys
from pathlib import Path
sys.path.insert(0, '.')
os.environ['MUSTER_STATE_ROOT'] = '/tmp/otr2291-state5persist'
import spawn, pipeline, watchdog
from unittest import mock
attempt_id = spawn._record_spawn_attempt(9905, 'implementation', os.getpid())
try:
    pipeline._fetch_or_halt('/tmp/otr2291-fetchhalt', '독립 재현: 신규 워크스페이스')
except SystemExit as e:
    reason = e.code if isinstance(e.code, str) else str(e.code)
    spawn._record_spawn_outcome(attempt_id, 'halted', reason)
with mock.patch.object(watchdog._sp, '_board_wide_sweep_all', return_value=0), \\
     mock.patch.object(watchdog._sp, 'standing_red_check', return_value=[]), \\
     mock.patch.object(watchdog._sp, '_undispositioned_role_prs', return_value=([], True)), \\
     mock.patch.object(watchdog._sp, 'lease_reconcile_sweep', return_value=0):
    rc = watchdog.roster_watchdog(root=Path('/tmp/otr2291-fetchhalt'))
print('watchdog rc:', rc)
"
```
result:
```
[spawn-attempt] issue-9905/implementation: spawn halted pre-workspace: 독립 재현: 신규 워크스페이스: fetch 실패 — fatal: '/no/such/independent-path-9905' does not appear to be a git repository
fatal: 리모트 저장소에서 읽을 수 없습니다

올바른 접근 권한이 있는지, 그리고 저장소가 있는지
확인하십시오.
돌고 있는 역할 세션 없음
watchdog rc: 1
```
  the watchdog's next tick names the pre-workspace halt, matching the issue's
  own acceptance wording, for the window R1/R2/R3 confirm this PR actually
  instruments.

---
requirement: R5 — frozen constraint: systemic for all consumer sessions
spec_ref: issue #2291 body, "Frozen constraint applies ... systemic for all
  consumer sessions"
verdict: Present
evidence: `53347a11:watchdog.py:1480-1483` (`spawn_attempt_sweep` call site,
  unconditional, inside the single shared `roster_watchdog()` entry point)
rationale: same reasoning as
  `848fd537c3738e625cd7706ab4718e3c20497f77:docs/issue-2312/reports/conformance-review.md`'s
  R5 systemic finding (read this session) — no per-consumer branch in the
  diff; every poll tick that already calls `roster_watchdog()` picks this up
  automatically. canonical:
  `53347a11:watchdog.py:1480-1483` (cited above) — single call site, no
  conditional guard on which consumer/issue triggered the tick.

---
requirement: R6 — frozen constraint: no added overhead
spec_ref: issue #2291 body, "Frozen constraint applies ... no added
  overhead"
verdict: flagged, not scored Present or Absent/Incorrect — see rationale and
  Open findings
evidence: `53347a11:spawn.py:850-861` (`_append_spawn_attempt_event`, opens
  `SPAWN_ATTEMPTS_PATH` in append mode, no truncation/rotation anywhere in
  the diff) and `53347a11:spawn.py:893-910` (`_load_spawn_attempts`, reads
  and JSON-parses the *entire* file every call)
rationale: unlike issue-2312's R5 (where the issue text gave no numeric
  overhead threshold to check against and no concrete mechanism was found
  either), here the issue text also gives no threshold, per
  requirement-extraction rule 2 — but this review additionally located a
  concrete, non-hypothetical mechanism. canonical: `grep -n
  SPAWN_ATTEMPTS_PATH spawn.py roster.py watchdog.py`, this session, PR head
  worktree — result: three hits, all in `spawn.py` (definition, the append
  helper, and the read-back helper), none in `roster.py`/`watchdog.py` —
  confirming no consumer of the file prunes it. `spawn_attempt_sweep()`
  calls `_load_spawn_attempts()` — a full file-read-and-parse — on *every*
  watchdog tick. On an install that spawns frequently — canonical: `ps aux`
  output captured this session (see "## Why" mid-review-incident block)
  independently showed roughly ten pre-existing `spawn.py ... watch`
  processes already running for unrelated issues at review time — per-tick
  I/O for this sweep grows without bound over the install's lifetime. Not
  scored Incorrect because the issue names no numeric bound this could be
  checked against (rule 2) — but this is a concrete growth mechanism, not
  merely an unstated threshold; see Open findings.

---
requirement: R7 — frozen constraint: no new conflict/stall surfaces
spec_ref: issue #2291 body, "Frozen constraint applies ... no added ...
  conflict/stall surfaces"
verdict: Present
evidence: `53347a11:spawn.py:853-856` (`_append_spawn_attempt_event`, a
  single `open(..., "a").write(...)` per event, no new lock) and
  `53347a11:roster.py` (`spawn_attempt_sweep`'s dedup via the pre-existing
  `ledger_check_and_stamp`, the same reconcile-ledger mechanism every other
  watchdog advisory already uses)
rationale: append-mode single-`write()` calls for a short JSON line are
  atomic on POSIX (`O_APPEND` + a write under `PIPE_BUF`), matching this same
  file's own code comment rationale (`53347a11:spawn.py:844-849`) for
  choosing append-only JSONL over a load-modify-save structured file; no new
  lock is introduced, and the sweep reuses an existing dedup mechanism rather
  than inventing a new one that could itself stall.

---
requirement: R8 — frozen constraint: nothing written into the consumer's
  tree
spec_ref: issue #2291 body, "Frozen constraint applies ... nothing written
  into the consumer's tree"
verdict: Present
evidence: `53347a11:spawn.py:534-535` (`STATE_ROOT = ... ROOT / "runs"` or
  `MUSTER_STATE_ROOT` override — never the caller-supplied `root`) and
  `53347a11:spawn.py:850` (`SPAWN_ATTEMPTS_PATH = STATE_ROOT / ...`)
rationale: confirmed by construction (the constant is never parameterized by
  a target-repo path) and by this review's own R2/R4 repros (see their
  `acceptance:` blocks above) — each used a distinct scratch git repo as the
  "consumer tree" (`/tmp/otr2291-scratch`, `/tmp/otr2291-fetchhalt`) and a
  separate `MUSTER_STATE_ROOT` scratch dir for the trace; canonical: `git
  status --porcelain` in both scratch repos, this session, after every R2/R4
  run — empty in both, confirming zero new files landed in the "consumer"
  tree from any of these runs.

---
requirement: R9 — gate: `tests/test_spawn_pipeline.py` passes
spec_ref: issue #2291 body, `## Acceptance`, "gate:
  `tests/test_spawn_pipeline.py`"
verdict: Present
evidence: `53347a11:tests/test_spawn_pipeline.py`, executed this session in a
  fresh worktree
rationale: independent re-run, PR head worktree — acceptance: `cd
  /tmp/pr2305-wt && python3 -m pytest tests/test_spawn_pipeline.py -q` —
  result:
```
86 passed in 52.16s
```
  matches the PR's own post-CHANGES-round figure (canonical:
  `53347a118202acfddd7024ab1e88d511019b694f:docs/issue-2291/reports/implementation.md`,
  "## Rationale for deviations" section — documents an earlier
  `role_model.txt` pytest-xdist race, independently diagnosed and fixed
  within this same PR; this session's own re-run above confirms the fixed
  state, not the pre-fix one).

---
requirement: R10 — empty state: a successful spawn — the attempt record
  gains a `"session-log"` outcome and the watchdog reports nothing new
spec_ref: issue #2291 body, `## Acceptance`, "empty state: a successful
  spawn — the attempt record gains its session-log path and the watchdog
  reports nothing new"
verdict: Present
evidence: see R2's finding block above (same repro; `anomaly count: 0`)
rationale: independent re-run above (issue 9901, distinct from the builder's
  own fixture) confirms the empty-state acceptance line directly.

---
requirement: R11 — provenance: executed-live, a real `_fetch_or_halt` halt
  forced with stdout piped through `tail`, halt reason present in the
  durable trace, watchdog's next tick naming the pre-workspace halt
spec_ref: issue #2291 body, `## Acceptance`, "provenance: executed-live —
  force a `_fetch_or_halt` halt against a real spawn ..., with spawn stdout
  piped through `tail` exactly as the consumer did; show the halt reason
  present in the durable trace, and the watchdog's next tick naming the
  pre-workspace halt. Paste real output of both."
verdict: Present
evidence: see R4's finding block above (same repro)
rationale: independent Demonstration, different fixture from the builder's
  (issue 9905 vs. 538, a different unreachable-remote path, direct
  `pipeline._fetch_or_halt()`/`watchdog.roster_watchdog()` calls rather than
  the builder's own script or the full CLI) — both halves the Acceptance line
  asks for (durable trace holding the reason, watchdog tick naming it) are
  independently reproduced above, real pasted output, this session.

## Open findings

1. R1/R3 — `Incorrect`: the durable spawn-attempt trace only covers the
   window from `require_doctor()` onward, not "before any network or
   workspace work" as issue #2291's own `## Ask` bullet 1 states. Two
   pre-existing gates (`require_acceptance_gate`, `require_requirement_linkage`
   — both already shipped, both already capable of a real network call and a
   real `sys.exit()`) run earlier in `main()` and are not covered; a halt in
   either reproduces the exact traceless-halt failure mode issue #2291 was
   filed to fix. Demonstrated live under R1 above (`trace file exists after
   the halt: False`).
   Resolution path: move `_record_spawn_attempt()` to the very top of
   `main()`'s non-dry-run path (before `require_board()`, the first call in
   that sequence — canonical: `53347a11:spawn.py:1564`, cited under R1's
   grep output above, is the earliest gate call in this sequence), and wrap
   `require_board()`/`require_no_repo_config()`/`require_acceptance_gate()`/
   `require_requirement_linkage()` in the same `try/except (SystemExit,
   Exception)` this PR already wraps around `require_doctor()`/
   `ensure_target_remote()`/`_spawn_one()`. `a.issue`/`a.role` are already
   parsed before line 1564 in the current diff (canonical:
   `53347a11:spawn.py:1597`, cited under R1's grep output above, already
   reads `a.issue`/`a.role` at that later point via the same `a` argparse
   namespace, confirming both fields are available earlier too) — the two
   windows have the identical fail-closed-halt shape and no structural
   reason to be instrumented differently.
2. R6 — flagged, not scored, non-blocking on its own but worth tracking:
   `spawn-attempts.jsonl` has no pruning/rotation/expiry, and every watchdog
   tick reads and parses the whole file. On a long-lived, actively-spawning
   install this grows unboundedly. Issue #2291 names no numeric overhead
   threshold to score this against (requirement-extraction rule 2), so this
   is reported as a concrete mechanism rather than a guessed verdict.
   Resolution path: either prune `spawn-attempts.jsonl` entries once their
   outcome has been swept and reported once (mirroring the ledger-dedup
   pattern already used for other advisories), or cap/rotate the file by
   size or age; a future issue amendment, not a blocker for #2291's own
   Acceptance (R9-R11), which is unaffected by this.

## Next steps

None from this review's own side — `loop_state` above is this record kind's
terminal value, `reported`. For the owning role: PR #2305 satisfies issue
#2291's own three literal `## Acceptance` lines (R9/R10/R11, all
independently re-derived Present above) and the `## Ask` bullet 2 mechanism
(R4, Present) and most of the frozen-constraint bundle (R5/R7/R8 Present, R6
flagged non-blocking) — but `## Ask` bullet 1's "before any network or
workspace work" placement claim (R1/R3) is `Incorrect`, not merely
under-covered: two pre-existing, already-network-touching, already-halt-
capable gates run before the new instrumentation, reproducing the exact
failure class issue #2291 exists to close. `Closes #2291` on PR #2305
overstates what was delivered until R1/R3 are re-addressed per the
resolution path in Open findings above.

canonical: `gh pr view 2305` output captured this session (see "## What was
done" above) — PR #2305's own body ends with a bare `Closes #2291` trailer;
the recommendation above rests on the R1 finding's live Demonstration and
the `spawn.py` line-number citations from that grep, both above.

## What did not work

This review's own execution had one real incident, disclosed in full under
"## Why" above: an early, unmocked probe of R1/R3 invoked the real `spawn.py`
CLI end-to-end against a real GitHub remote with a fabricated issue number
(99999999), expecting `require_requirement_linkage` to halt before any
network/workspace work occurred — it did not halt where expected (canonical:
see "## Why" mid-review-incident block above for the `ps aux`/`pgrep -P`
output proving a real `claude -p --permission-mode bypassPermissions`
session was live), and the spawn proceeded to actually start that background
session plus its watcher process. This was killed immediately (`kill` on all
three related pids, canonical: same block above) once discovered, before
anything committed or pushed (canonical: same block above, the
`git status`/`git branch -vv`/`gh pr list` output); the scratch workspace
directory was removed afterward. All further R1/R3/R4/R11 evidence in this
record was gathered through safe, non-CLI reproductions (direct calls to the
functions `main()` itself calls) that cannot spawn a session, per the
incident note under "## Why". Reported here as a review-process failure on
this session's own part — not an ambiguity in the artifact under review — so
a future review of this issue's lineage does not repeat the same probe shape
unmocked.

No other execution gap: every other citation above was read or re-run live
this session against the PR's actual head commit.

## Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split issue #2291's `## Ask` bullet 1 into R1/R2/R3 (three obligations bundled by "and"), kept bullet 2 as its own item (R4), split the frozen-constraint paragraph into R5-R8 by the same rule, and kept `## Acceptance`'s three already-singular lines as R9-R11, before any verdict was rendered.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; Inspection for R1/R3/R5/R7/R8's structural claims (call-order, file-write mechanics), Test (reused `tests/test_spawn_pipeline.py`) for R9, Demonstration for R2/R4/R10/R11 (per the issue's own "executed-live" ask), and flagged R6 rather than force it through any single method since the issue names no observable overhead threshold to test against (verification-method-selection rule 2 read alongside requirement-extraction rule 2).
skill-verdict: conformance-review-verdict-assignment — applied: invoked; assigned R1/R3 `Incorrect` (rule 2 — the artifact's own "before require_doctor()/ensure_target_remote() (the first network call)" claim actively contradicts the actual call order, not merely omits coverage), named the failing clause for both (rule 5), and re-checked the finding once against the live artifact via an actual `SystemExit`-shaped Demonstration before finalizing (rule 6) rather than resting on Inspection alone.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every Findings-block evidence line above cites file:line-range plus the PR head sha (`53347a118202acfddd7024ab1e88d511019b694f`) or the independently-run command and its pasted output; R1 and R3 share the same root-cause evidence location and are recorded as two distinct clause-level entries (per extraction rule 5's "keep as own item, state dependency inline") rather than collapsed, since they check two distinct clauses of the same Ask bullet, not the same requirement twice.
skill-verdict: conformance-review-finding-record — applied: invoked; every requirement block above carries the full field list (requirement, spec_ref, verdict, evidence, rationale, and `spec_vs_built` for both `Incorrect` verdicts), no block written without an evidence pointer or spec_ref.
skill-verdict: conformance-review-sampling-derivation — not-applicable: `## Ask`(1 bullet, 3 obligations)+bullet-2(1)+frozen-constraint(4)+`## Acceptance`(3) = 3+1+4+3 = 11 items, full enumeration against one PR (7 changed files), no sampling scope needed — derived: counted in "## What was done" above, canonical: `gh issue view 2291`, executed-unit this session.
skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope was not explicitly extended into risk-weighting a recorded finding; R1/R3's `Incorrect` verdict and its `Closes #2291`-overstatement consequence are stated in the finding itself, not banded.
skill-verdict: implementation-audit — not-applicable: this task is already the more specific `conformance-review` role/skill family (builder-blind structural independence already satisfied by this being a separate reviewing session with no access to the builder session); no separate builder/evaluator claim-extraction split was layered on top.
other mounted skills (freelunch, terse, scout, warrant, dataviz, code-review, etc.): not triggered — this task's own directives route delegation/style/scouting through the core rulebook hooks referenced at session start, not through these plugin-listed skills.
