---
subject: issue-1959
kind: survey
loop_state: survey-complete
---

# Current-state survey: tests/test_spawn.py

## What was measured

```
$ wc -l tests/test_spawn.py
11509 tests/test_spawn.py
$ grep -c '^class ' tests/test_spawn.py
106
$ grep -c '    def test_' tests/test_spawn.py
524
$ python3 -m pytest tests/ -q --collect-only 2>&1 | tail -1
920 tests collected in 0.53s
```

canonical: `python3 -m pytest tests/ -q --collect-only` output pasted above
derived: `grep -c '    def test_' tests/test_spawn.py` -> 524; `grep -c '^class ' tests/test_spawn.py` -> 106
Repo-wide baseline is 920 collected tests across `tests/`, of which 524 live
in `test_spawn.py` across 106 `unittest.TestCase` classes. This 524-in-920
split is what phase 2's "same-or-documented count" acceptance check measures
against.

## Class -> concern-group mapping (full inventory)

Every one of the 106 classes was read by name and by the behavior its `def
test_*` methods exercise (spawn/session args, watchdog polling, roster/board
reads, consult/panel CLI wiring, git/gh network calls, or gate/policy
refusals), then assigned to exactly one of six concern groups.

derived: python3 regex-scan of class boundaries + `def test_` counts per class, grouped by the name-list below (script run inline this session, not saved to disk); same script diffed the six name-lists against the full 106-class list (`MISSING: []`, `EXTRA(typo): []`)

| group | classes | tests | source lines (approx) |
|---|---:|---:|---:|
| pipeline | 12 | 62 | 1,592 |
| observation-recovery | 30 | 166 | 3,826 |
| board-flows | 18 | 134 | 2,864 |
| consult-panel | 14 | 59 | 1,069 |
| checkout-network | 17 | 46 | 1,270 |
| gate-wiring | 15 | 57 | 854 |
| **total** | **106** | **524** | **11,475** (+ ~34 lines imports/helpers) |

### pipeline (spawn cmd, session args, workspace identity)
`SpawnCmd, DryRunModelReflection, ResumeOrchestratorSessionPermissionMode,
SessionResumeClaim, OrchestratorSessionIdCapture, Drive, IssueScopedPrompt,
WorkspaceExcludesHomeDotfiles, WorkspaceReuseOriginMismatch,
WorkspaceSyncFailClosed, RepoScopedWorkspaceIndex, StateRootIsolation`

### observation-recovery (watchdog, respawn, liveness, staleness)
`Watchdog, PollHeartbeatMarkerRelocationTest, SelfTriggeredRespawn,
AutoRespawnClaim, ProgressAwareRespawnCounter, SpawnOneNoWait,
SpawnOneIssueRoleClaim, SpawnDeathBeforeRegistration,
AbsorbedBranchRecutMidRun, BootstrapFetchesBeforeVerification,
AwaitBoundedTiming, AwaitBoundedWallClockCap, AwaitBoundedMissingLog,
WatchFollowWallClockCap, TestMaybeResumeForReadyPrRecordsFailureCause,
ConsumerFixtureWatchdogAnchoring, RosterWatchdogIdempotentReconcile,
WatcherSilentSignal, WatcherAutoArm, WatcherPs, PollDue, IsNewCommit,
GitHead, PriorEventDetails, PreambleWarning, Classify, FailClosedDowngrade,
EventExitScope, SessionEndVerdict, StreamingLanding`

### board-flows (board/roster reads, watch/follow, event reporting)
`BoardSnapshot, SessionResult, FlowsPayload, WatchFollow,
WatchFollowSessionScoping, WatchRegistrationRace, WatchMultiRoleAmbiguity,
WatchRosterWorkspaceIndexRace, WatchAll, SessionLastActivity, ProgressEvents,
EventReporting, Clean, ReturnedPrGate, RosterOwnershipScoping,
RosterConcurrency, NoConcurrencyCap, OwnershipReport`

### consult-panel (consult/panel CLI, closure-sweep, reconcile)
`ConsultCmd, PanelDegradeErrorSafety, ConsultVerdictParsing,
PlainSessionDirectiveNorms, ClosureSweepCliWiring, PanelCliWiring,
ClosureSweepCallCountTest, RemediationMergeSweep,
RosterReconcileRemediationMergedCLI,
RosterReconcileRemediationMergedCLITargetRoot, RosterReconcileUnreported,
Reconcile, ReconcilePrExpectedMissingRecoveryPolicy, ReconcileLedger`

### checkout-network (git/gh network calls, checkout caching, PR comments)
`RulebookCheckoutMemo, RulebookCacheLock, CoreRootCacheLock, FetchDedupe,
NetworkSubprocessTimeout, GitEnvTimeoutPromptVars, EnsureTargetRemote,
RepoSlugCacheTest, OrchestratorGitToken, EnsurePushedResult,
EnsurePushedStrandedComment, PostCrashComment, PostStallComment,
PostSessionEndComment, IssueComments, IssueCommentsEtagProbeUsesExplicitGetMethod,
PrOpenOrMergedForBranch`

### gate-wiring (policy refusals, requirement/doctor gates, sandbox/env allowlists)
`RepoConfigRefusal, MustMcpAllowEnv, WorkspaceBashAllowlist,
RoleSessionSandboxRemoved, RequireDoctor, RequirementIntakeValidityConsult,
RequireRequirementLinkageRemoteBranch, RequirementDigestScaffold,
DryRunCwdValidation, IssueArgValidation, BoardNonNumericSubjectWarning,
FixtureShapeContracts, WebToolPermissionAccess, Ledger, DiagnoseHealth`

## Shared fixtures / helpers

canonical: `sed -n '1,34p' tests/test_spawn.py` (module imports) read this session
`test_spawn.py` has module-level imports (lines 1-34) and a number of
`_make_*`/`_stub_*` helper functions used across many of the classes above.
This session did not exhaustively trace every helper's call sites across all
106 classes. Phase 2 must do that before moving classes, since a helper used
by classes now assigned to different target files becomes a shared-fixture-
placement decision, not a mechanical cut. Called out as an open finding
below.

## Pruning-candidate scan (name-level only, not yet behavior-verified)

```
$ grep -oP '(?<=    def )test_\w+' tests/test_spawn.py | sort | uniq -c | sort -rn | awk '$1>1'
      4 test_skips_when_marker_already_present
      2 test_posts_when_marker_absent
```

derived: `grep -oP '(?<=    def )test_\w+' tests/test_spawn.py | sort | uniq -c | sort -rn`
canonical: `grep -n 'def test_skips_when_marker_already_present\|^class ' tests/test_spawn.py` output read this session — 4 hits at line 6707 (class `PostCrashComment`, defined line 6704), 6772 (`PostStallComment`, 6769), 6886 (`PostSessionEndComment`, 6860), 7014 (`RemediationMergeSweep`, 6960)
Each of those 4 classes guards a different comment-posting function's
idempotency marker (crash marker vs. stall marker vs. session-end marker vs.
remediation-merge marker) — same method name, different target function and
different setup fixtures per class name/line above, not the same behavior
asserted four times. The 2-way `test_posts_when_marker_absent` hit follows
the same reasoning, inside `PostCrashComment` and `PostStallComment`.

canonical: the two `grep -n`/`grep -oP` command outputs above, read this session
This name-level scan found no same-name collision inside a single class and
is a candidate list for phase 2 to re-check against actual test bodies, not
a pruning decision made here. Deeper overlap (same behavior asserted under
different method names, or under different setups within the same class)
was not checked in this session and is deferred to phase 2's per-class read.

## Open findings

- Shared helper functions (`_make_*`/`_stub_*`) are not yet mapped to call
  sites; phase 2 must do this before splitting, since a helper used across
  classes now landing in different files needs its own new home.
- Overlap/pruning was only scanned at the test-method-name level in this
  session; true behavioral duplication (two tests with different names
  asserting the same thing under the same setup) has not been checked and
  is deferred to phase 2, gated on the refactoring-legacy skill's
  characterization-test-scope method so every prune names its surviving
  coverage per the issue's acceptance check.

## Skip-condition record

Scouting (external prior-art sweep) was skipped: this is an internal
test-file reorganization with no external product/library surface to
benchmark against — the refactoring-legacy skill family
(characterization-test-scope, step-decomposition) named in the issue's
design-research line is the applicable internal methodology and was
consulted for the split/prune approach below, not web-scouted external
exemplars.
