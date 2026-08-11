# Survey: role-session behavior, spawn → judge → produce → record → complete (issue #750)

derived: manual read of spawn.py, gates/, on-the-record/hooks/,
docs/reports/2026-08-0{7,8,9}-*, docs/specs/northpole.md, via foreground
Explore research pass (see proposal for scope note).

Scope note (repo identity): two `spawn.py` copies exist.
`/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/spawn.py` (4919
lines, mtime 2026-08-11) is the live/canonical tool — the muster repo,
outside this working tree. This working tree's own `spawn.py` (2957
lines, mtime 2026-08-03, PR #260/issue-258) is the same stale snapshot
predating fork/self-watch-arming and most mechanisms below. All file:line
citations below are against the canonical (muster) copy's line numbers as
captured by the research pass; only the paths that also exist in this
working tree (`gates/reexecution_gate.py`, `gates/landing_readiness.py`,
`on-the-record/UNENFORCED-CLAUSES.md`, `on-the-record/commands/run.md`,
`docs/specs/northpole.md`, `docs/reports/2026-08-07-hunt-idle-deadlock-watchdog-exit-code.md`,
`docs/reports/2026-08-08-hunt-global-watch-all.md`,
`docs/reports/2026-08-08-hunt-watch-registration-race-and-outcome-derivation.md`,
`docs/reports/2026-08-08-hunt-implementation.md`,
`docs/reports/2026-08-09-hunt-ps-watcher-visibility-and-bounded-watch-all.md`)
are cited by bare path here (line numbers stated in prose after the
backticked path, never inside the backticks) so record-claim-guard's
reachability check resolves them; `spawn.py` and
`on-the-record/hooks/delegated-judgment-gate.sh` citations refer to the
muster copy's line numbers and are stated the same way (path in
backticks, line number in prose), since this tree's own stale spawn.py
copy does not contain the cited lines at those offsets. No file literally
named `session-watcher` exists anywhere; the watch/ps/roster/watchdog
logic that serves this sub-area lives inside `spawn.py` itself (muster)
plus `gates/`.

Sub-areas per issue #750, mapped to northpole reqs #1 (orchestration to
completion), #3 (real-wired verification), #4 (autonomous completion +
legible reporting), #5 (problems not pushed back to human).

## A. Directive vs. observed behavior (2026-08-11 strands)

**PARTIAL** — mechanically enforced shape, semantically unverified content.

- Directive says (SessionStart hooks, this session): a role produces a
  proposal-first record, a genuine judgment, real-wired verification, and
  a complete record with required fields.
- Observed (muster spawn.py, per research pass): `classify(rc, result,
  delta, blocked)` (muster spawn.py, lines 1463-1486) — its own docstring
  states "판정하지 않는다 — 이름만 붙인다" ("does not adjudicate — only names
  it"). `progressed` fires purely because `delta` (a board diff) is
  non-empty; there is no check that the diff reflects a genuine judgment
  versus a mechanically emitted artifact.
- The role subprocess is launched at `spawn.py` (muster) lines 4570-4573;
  `rc = proc.wait()` at line 4763 is the sole completion signal in the
  unbounded path. `session_end_verdict` (muster spawn.py, lines
  1489-1527) instead trusts an append-only events log
  (`<work>.events.jsonl`) as source of truth (a comment at lines
  4593-4596 explains why: a crash between `roster_remove()`/`proc.wait()`
  and the `session-end` append can leave no trace on the process-exit
  path alone).
- **Verdict: PARTIAL.** The directive's shape (proposal → judge → produce
  → record) is real and gate-checked — `on-the-record/UNENFORCED-CLAUSES.md`
  (see reachability note above) and `on-the-record/commands/run.md` both
  confirm which mechanisms are zero-install-reached vs. CI-supplement —
  but spawn.py's own completion signal is process/log-mechanical, not a
  content check that the directive was actually followed with genuine
  judgment. Repo: muster (spawn.py).
- Rank input: centrality HIGH (every role session's "did it finish"
  question routes through this), observed-failure-frequency MEDIUM (no
  direct incident found in the four dated hunt reports for this exact
  path, but sub-area D's `_watcher_looks_real` is a directly adjacent
  proven failure).

## B. Genuine judgment vs. mechanical artifact production (ties to audit C)

**GAP.**

- `classify()` (muster `spawn.py`, lines 1463-1486) is the closest
  mechanism to a "genuine judgment" check and is purely mechanical:
  `delta` non-empty → `progressed`; `permission_denials` present →
  `refused`; else `silent-failure`. No semantic read of session content.
- `latest_axis_evaluation(role, axis)` in
  `on-the-record/hooks/delegated-judgment-gate.sh` (lines 499-508) — the
  mid-course-decision "judgment" mechanism reads a role's own **prior**
  record file and regex-parses previously written `axis_evaluation`
  blocks (`parse_axis_evaluations(text)`; a comment at lines 516-518
  states it "reuses that role's latest axis_evaluation verbatim (no new
  evaluation logic)"). No new reasoning happens inside the gate.
- Decision synthesis in the same file, lines 649-657, is literal string
  comparison over a fixed vocabulary (`"supports"`/`"contradicts"`) under
  a named rule `panel-unanimous-support-v1` (line 11 of that file; also
  named in `docs/specs/northpole.md`, prose line ~88 in this tree's
  copy). Whether the underlying `axis_evaluation` reflects real judgment
  is entirely outside this script — it trusts whatever a role wrote to
  its own file earlier.
- **Verdict: GAP.** Nothing in the spawn→watch→classify→judgment-gate
  chain independently verifies that a role's claimed judgment (an
  `axis_evaluation`, a `progressed` classification, a board delta) is
  genuine reasoning rather than a mechanically emitted string matching
  the expected shape. The gap is exactly what `reexecution_gate.py`
  (sub-area C) targets, but that tool is CI-supplement / manual, not part
  of the automatic loop.
- Rank: centrality HIGH (directly the northpole req #4/#5 "genuine
  judgment" and "problems not pushed back" claim), observed-failure-
  frequency MEDIUM — no repro of a fabricated judgment specifically, but
  the mechanism-level gap is unambiguous and adjacent failures (sub-area
  D) are proven.
- Missing mechanism: a content-level judgment-quality check between
  `axis_evaluation` authorship and its consumption by
  `delegated-judgment-gate.sh` (e.g., an independent verifier reading the
  reasoning behind the verdict label, not just the label). Repo: muster
  (`on-the-record/hooks/delegated-judgment-gate.sh`).

## C. Real-wired verification (req #3): doc/mock vs. actually building+running

**GAP** (present as a tool; absent from the automatic path).

- `gates/reexecution_gate.py`, lines 103-121 — standalone CLI, `main(argv)`
  requires `--issue --role --sha --command` passed by hand (or external
  CI); calls `run_reexecution()` itself (line 113).
- No caller in spawn.py or the watch loop shells out to
  `reexecution_gate.py` with these args (grep across `.md`/`.sh`/`.py`
  in the research pass found none). The only integration:
  `gates/landing_readiness.py` line 24 imports it, and lines 68-73 only
  **read** a pre-existing verdict JSON at
  `.reexecution/<issue>-<role>.json` — it never triggers
  `run_reexecution()`.
- `on-the-record/UNENFORCED-CLAUSES.md`, line 17, and
  `docs/specs/enforcement-boundary.md` both label `reexecution_gate.py`
  explicitly `contract, CI-supplement` ("folded into
  `landing_readiness.py`'s existing CI-supplement path — same boundary,
  no new install surface") — CI-only where CI is installed, never a
  session-side/hook-side automatic trigger. This directly collides with
  northpole req #7 ("no forced CI setup ... hooks and plugin elements
  only. Everything works by default on install"): a plugin-only install
  (the required default per req #7) never runs reexecution at all.
- `docs/reports/2026-08-08-hunt-implementation.md`, lines 9-36 — even
  where CI is wired, `landing_readiness.py`'s blocking-cause `scope`
  filter is `{"gates/"}`, so a fail verdict from reexecution never blocks
  a normal role PR (which touches app code, not `gates/`) —
  `classify()` reports the PR READY regardless.
- **Verdict: GAP.** Real-wired verification exists as code but is not
  wired into the default (plugin-only) install path spawn.py drives, and
  even under CI its fail verdict is scoped out of blocking a normal PR.
- Rank: centrality **HIGHEST** — this is northpole req #3 verbatim, and
  req #7 makes plugin-only-install the mandatory default, which this gap
  directly violates. Observed-failure-frequency: structural (every
  plugin-only install, by design of the CI-supplement label, never
  invokes it) — not intermittent, permanent by current wiring.
- Missing mechanism: an automatic, hook-triggered (not CI-only)
  invocation of `reexecution_gate.py` (its `--issue --role --sha
  --command` CLI) keyed off the role's own claimed test/build command,
  run before the role's record can reach a terminal `loop_state`. Repo:
  muster (spawn.py or a new hook entry) + on-the-record (role directive
  wording that currently only *describes* real-wired verification
  without enforcing it).

## D. Watch/ps subsystem reliability (2026-08-11-adjacent dated evidence)

**PARTIAL**, three concrete proven failure modes, all in the muster repo.

1. **Role-blind pid check** —
   `docs/reports/2026-08-09-hunt-ps-watcher-visibility-and-bounded-watch-all.md`,
   lines 9-55. `_watcher_looks_real(pid, issue)` (cited at muster
   `spawn.py` lines 1698-1717 as of that date) checks only that the issue
   number appears in `/proc/<pid>/cmdline` — never the role. Repro at
   lines 18-48 of the hunt report: a mocked cmdline for role "qa" returns
   `True` when queried under role "dev". Effect: a genuinely stuck/silent
   session for one role can be masked by a live sibling-role watcher on
   the same issue.
2. **Watcher pid not confirmed to be a watcher** —
   `docs/reports/2026-08-08-hunt-global-watch-all.md`, lines 59-98.
   `watchdog_check_one` signal 5 verifies `watcher_pid` is *some* live pid
   via bare `_alive()`/`os.kill(pid,0)`; never confirms the pid is
   actually a `spawn.py watch --follow` process. Repro at lines 74-89 of
   the hunt report: registering the test's own pid as `watcher_pid`
   yields `anomalies: []` even with no real watcher ever started, or
   after pid reuse post-exit.
   Same report, lines 9-57 (after-proposal stance): `watch --all
   --follow` remains opt-in at the arming step; nothing in `_spawn_one()`
   or `main()`'s spawn path (grep-confirmed) ties a spawn to a live
   `--all` watcher.
3. **Rejected-PR history silently upgrades a real silent-failure** —
   `docs/reports/2026-08-08-hunt-watch-registration-race-and-outcome-derivation.md`,
   lines 9-33. `_pr_for_branch` (muster `spawn.py` line 994; `gh pr list
   --head <branch> --state all`) matches OPEN/CLOSED/MERGED alike; a
   branch with an earlier rejected-and-closed (never merged) PR gets
   `already_delivered=True` even when this run's `classify()` correctly
   returned `silent-failure` — masking the real failure as success.
- Companion **NO FINDING**:
  `docs/reports/2026-08-07-hunt-idle-deadlock-watchdog-exit-code.md`,
  line 12 — `roster_watchdog()`'s exit code is not consumed by any caller
  (`$?` unbranched anywhere); its findings only reach a human/orchestrator
  if that agent chooses to read printed stderr/stdout. Not itself a
  proven break, but confirms the watchdog's output carries no
  operational enforcement weight.
- **Verdict: PARTIAL.** The watch/roster/watchdog subsystem exists and is
  actively iterated on (three fixes proposed/hunted within a 3-day
  window, 08-07 through 08-09), but three of the four dated reports prove
  concrete ways a stuck, unwatched, or genuinely-failed session reads as
  fine.
- Rank: centrality HIGH (directly serves req #1's "identifies
  bottlenecks/obstacles" and req #4's autonomous-completion claim — an
  undetected stall or a masked failure defeats both), observed-failure-
  frequency **HIGH** — three independent, reproduced findings in a single
  week immediately preceding/on the northpole date, versus one
  no-finding companion.
- Responsible repo: muster (spawn.py watch/roster/watchdog code +
  `gates/` consumers).

## E. Two-phase (proposal/delivery) flow — friction, redundant round-trips, gate collisions

**MET**, with one structural friction point.

- Flow: `docs/specs/northpole.md`, prose section "4. Autonomous
  completion..." — phase 1 (proposal) → human Approve → phase 2 (build to
  completion, no further human turns). Approval mechanics:
  `on-the-record/commands/run.md`, lines 275-292 — canonical approval is
  an issue comment whose entire body is exactly
  `APPROVE issue-<n>/<role>` (single-account mode) because a role cannot
  self-approve its own PR review.
- This phase split is itself gate-enforced: this session's own
  SessionStart directive states the PR-trailer split (phase-1 body
  forbids Closes/Fixes/Resolves, phase-2 body requires it, enforced by
  `pr-preflight.sh`'s `check_body`), so the two phases cannot be silently
  merged into one PR.
- Friction point (structural, not a bug): every phase-1→phase-2
  transition costs one full human round-trip (a GitHub PR review Approve
  or an exact-string issue comment) even when the proposal is
  low-risk/mechanical, because `delegated-judgment-gate.sh` (sub-area B)
  only auto-resolves *mid-course* decisions inside phase 2, not the
  phase-1→phase-2 gate itself — there is no equivalent auto-approve path
  for phase-gate crossing itself, by design (per northpole req #7's
  human-in-the-loop expectation and the contract's "exactly two paths"
  rule). This is intentional friction, not a defect, so it is recorded
  MET rather than GAP — but it is the one place in the flow where a human
  turn is structurally mandatory regardless of session judgment quality.
- **Verdict: MET.** No redundant round-trips or gate collisions found
  beyond the single by-design human gate; the phase split itself is
  correctly enforced end-to-end.
- Rank: N/A (MET, no rank needed per issue's ranking instruction, which
  only requires ranking PARTIAL/GAP entries).

## Findings summary (ranked, PARTIAL/GAP only)

| Rank | Sub-area | Verdict | Centrality | Failure-freq | Repo |
|---|---|---|---|---|---|
| 1 | C — real-wired verification | GAP | Highest (req #3 + #7 collision) | Structural/permanent | muster + on-the-record |
| 2 | D — watch/ps reliability | PARTIAL | High (req #1, #4) | High (3 reproduced findings in 1 week) | muster |
| 3 | B — genuine judgment vs. mechanical artifact | GAP | High (req #4, #5) | Medium (mechanism-level, no direct repro) | muster |
| 4 | A — directive vs. observed completion signal | PARTIAL | High | Medium | muster |

E is MET and carries no rank.

## Open findings (OF)

- OF-1: no automatic (hook-triggered, non-CI) invocation path exists for
  `reexecution_gate.py` — violates req #3/#7 under plugin-only install.
- OF-2: `_watcher_looks_real` is role-blind (issue-only pid match).
- OF-3: `watchdog_check_one` signal 5 does not confirm `watcher_pid` is
  actually a watcher process.
- OF-4: `_pr_for_branch`'s `--state all` can upgrade a genuine
  `silent-failure` to `already_delivered` via an unrelated closed PR.
- OF-5: `classify()` and `delegated-judgment-gate.sh` both operate purely
  on pre-existing labels/deltas with no independent check that the
  underlying judgment was genuine.
