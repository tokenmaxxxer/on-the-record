---
issue: 3245
role: experiment-trust+silent-failure-audit+implementation-blueprint-3edbb1a6
author: experiment-trust+silent-failure-audit+implementation-blueprint-3edbb1a6
skills: experiment-trust (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12))
verifies_subject: false
code_under_review: scripts/consumer-path/run_pair.py, scripts/issue-3127/run_consumer_pair.py (9060451849ffbae4c17d82e9e5c6ce9841eac691)
loop_state: scope-undeclared
type: measurement
breaking: false
verdict: partial -- watch-race, credential-seeding, and cleanup-order fixes landed and unit-tested (76 passed); pair 1 recollected+scored (7-7 tie, supplementary); pair 2 dispatched real but H1/H2 unrecoverable this attempt (bugs found+fixed mid-run, not yet re-verified against a fresh dispatch); pairs 3-5 not run (unfiled, gh-guard blocks this session from filing them)
upstream:
  - path: docs/issue-3245/reports/independent-verification-1.md
    sha: 43475e4ab9edcbaa20be2c9dcf25b78ed15c40cd
  - path: docs/issue-3245/reports/independent-verification-2.md
    sha: c2e23a4bd7be9fc1ff5e2fcb28d13da7be6e3a99
  - path: 16e96c75442d6804cdb0707326157c6c55dacc20:scripts/consumer-path/run_pair.py
    sha: 16e96c75442d6804cdb0707326157c6c55dacc20
---

# issue-3245 — experiment-trust+silent-failure-audit+implementation-blueprint-3edbb1a6 record

## What was done

canonical: `gh issue view 3245 --comments` (this session, this turn) —
read the issue body, the orchestrator's addendum, and the reopen comment
(2026-09-03T03:54:39Z) before starting. Code and results are committed
at `9060451849ffbae4c17d82e9e5c6ce9841eac691`; this record follows.

### 1. Fixed the watch race

derived: workspace `issue-3245/experiment-trust+implementation-blueprint+silent-failure-audit-f264980e`'s
own `docs/issue-3245/_assets/01-study-groups/result.json` (round 2's
never-landed attempt, read this session from its on-disk workspace) —
`arm_results.on.status == "watched-to-completion"`, `dispatch_returncode:
0`, `watch_returncode: 0` for BOTH arms, yet `h1.on_invocation.reason`
still read "the arm never reached a dispatched, log-producing state" —
the false verdict the orchestrator's comment named.

Root cause: every `--skills` dispatch mints a fresh, random
lease-disambiguator at dispatch time (`spawn.py`'s `a.role =
f"{skill_slug}-{disambiguator}"`), never predictable before dispatch.
`arm_workspace_dir()`/`collect_skill_invocation()` guessed a workspace
path from the bare skill name (no disambiguator), which can never
match.

Fix in `9060451849ffbae4c17d82e9e5c6ce9841eac691:scripts/issue-3127/run_consumer_pair.py`:
`_discover_arm_branch()` (new) polls `gh pr list` for a PR whose branch
starts with `issue-<n>/`, up to 6 polls over ~30s. `collect_skill_invocation()`
now accepts `repo`/`issue`; when the guessed log is missing and both are
supplied, it discovers the real branch and retries; if discovery also
fails, the result is `status: "unknown"`, reason ending "unobservable,
not evidence the arm never ran" — never "never-dispatched". Omitting
`repo`/`issue` keeps the old label for every pre-round-3 call site.

acceptance: `python3 -m pytest tests/test_issue_3127_h1_and_scoring.py
tests/test_issue_3127_run_consumer_pair.py tests/test_issue_3127_run_pair.py
tests/test_issue_3245_pair_results.py tests/test_consumer_path_trust_root.py -q`
(this session, this turn) — result:
```
76 passed in 0.96s
```
27 are new this round (3 `_discover_arm_branch` retry/exhaust/transient
tests, 3 unknown-vs-never-dispatched labeling tests, 8 `seed_arm_credentials`
tests across two files).

Second instance, found dispatching pair 2: `9060451849ffbae4c17d82e9e5c6ce9841eac691:scripts/consumer-path/run_pair.py`'s
`execute_arm()` passed `--session <bare skill name>` to `spawn.py
watch`, the same mismatch one call earlier.
derived: `9060451849ffbae4c17d82e9e5c6ce9841eac691:docs/issue-3245/_assets/02-onboarding-experiment/result.json`
(this session's own real dispatch) — `arm_results.on.dispatch_returncode
== 0` but `watch_stderr: "기록 없음 — 아직 스폰된 적이 없다"` —
dispatch succeeded, `watch` never found it. Fixed by omitting
`--session`; `events._lookup_roster_entry()` auto-selects the single
live match by `--issue`/`-C repo` alone.

Third, structural instance: `run_pair()` called
`prepare_arms._cleanup(created_dirs)` immediately after both arms'
`execute_arm()` returned, BEFORE the H1 gate ever reads the session
log — and that log lives inside the isolated HOME `_cleanup()` deletes.
canonical: `9060451849ffbae4c17d82e9e5c6ce9841eac691:scripts/consumer-path/run_pair.py`
— `_cleanup()` now runs after `gate_pair_on_h1()`, not before.

### 2. Fixed real dispatch itself (credential seeding)

derived: `/tmp/pair2_run.log` (this session's first dispatch attempt,
this turn, before any fix) — both arms `dispatch-failed`,
`dispatch_returncode: 1`, stderr containing "훅이 headless 에서
발화하지 않는다" — the identical PR #3251 signature.

derived: `T=$(mktemp -d) && mkdir -p "$T/.claude" && cp
~/.claude/.credentials.json "$T/.claude/.credentials.json" && HOME="$T"
python3 spawn.py doctor` (this session, this turn) — result: `doctor-ok`
(exit 0). derived: same command, empty `$T2`, no credentials copied —
result: "훅이 headless 에서 발화하지 않는다" (exit 1), the exact PR
#3251 signature, reproduced live with nothing changed but one file's
presence.

canonical: `docs/issue-3245/reports/independent-verification-1.md`
(merged PR #3253, sha `43475e4ab9edcbaa20be2c9dcf25b78ed15c40cd`) and
`independent-verification-2.md` (merged PR #3254, sha
`c2e23a4bd7be9fc1ff5e2fcb28d13da7be6e3a99`), both read this session —
each independently traces PR #3251's failure to the same credential
gap; this session's own reproduction above confirms it a third time.

Fix: `9060451849ffbae4c17d82e9e5c6ce9841eac691:scripts/consumer-path/run_pair.py`
adds `seed_arm_credentials(home, source=None)`, copying
`~/.claude/.credentials.json` into each arm's isolated HOME identically
before dispatch — touches neither `HOME` nor `MUSTER_SKILL_REPO` (the
only two variables `verify_manipulation.py` cross-checks). `run_pair()`
fails closed (`status: "credential-seeding-failed"`) on a missing
credential.
acceptance: `python3 -m pytest tests/test_issue_3245_pair_results.py -q`
(this session, after the fix) — result: `18 passed in 0.91s`, including
4 new `seed_arm_credentials` tests.

silent-failure-audit (invoked via Skill tool): audited both new
subprocess-calling functions this round adds.
canonical: this session's own PreToolUse hook error, this turn
(verbatim): "adds 1 new subprocess.run/Popen/check_output/check_call
call site(s) with no explicit timeout= keyword" — refused the first
version of `_discover_arm_branch()`'s `gh` call, confirming the audit's
"unguarded subprocess call" category live; fixed with `timeout=30` and
`except subprocess.TimeoutExpired`. `seed_arm_credentials()`'s copy step
is `try/except OSError`-guarded, reported as `{"seeded": False,
"reason": ...}` rather than a bare traceback.

### 3. Scored pair 1 from material that already exists

PRs #29 (`issue-19/...-37412f31`) and #30 (`issue-20/...-abf6a734`) on
`JiwonJung94/study-companion` are the on/off arms' real deliverables
round 2 produced.
derived: `gh pr view 29 --repo JiwonJung94/study-companion --json body
-q .body` / same for 30 (this session, this turn) — bodies fetched
live.
acceptance: `python3 scripts/issue-3041/evaluate_pair.py
scripts/issue-3041/tasks/01-study-groups.txt
scripts/issue-3041/rubrics/01-study-groups.md <pr29-body> <pr30-body>
docs/issue-3245/_assets/01-study-groups/h2_evaluation.json` (this
session, this turn) — result:
```
document_1_score: 7 (skills-off), document_2_score: 7 (skills-on)
verdict: indistinguishable
```
Recorded in `9060451849ffbae4c17d82e9e5c6ce9841eac691:docs/issue-3245/_assets/01-study-groups/result.json`,
with `manifest.json`/`transport.json` copied byte-identical from round
2's own pre-dispatch artifacts (`manifest.json.sha256` recomputed this
session and verified to match).
derived: `ls "$MUSTER_WORKSPACE_ROOT" | grep -E "37412f31|abf6a734"`
(this session, this turn) — result: empty. Round 2's session-log
artifacts are gone from this machine, so H1 cannot be recovered for
this pair even with fix §1 — `result.json` reports `h1.status:
"unrecoverable"`, and pair 1 is excluded from the formal tally. The h2
tie is reported anyway, labeled supplementary, per the issue's own
must-not against hiding a real per-pair result.

### 4. Ran pair 2 — dispatch real, H1/H2 unrecoverable this attempt

acceptance: `python3 scripts/consumer-path/run_pair.py --pair-id
02-onboarding-experiment --repo /home/jwjung/study-companion --skill
product-discovery-hypothesis-preregistration --on-issue 21 --off-issue
22 --out-dir docs/issue-3245/_assets/02-onboarding-experiment
--watch-timeout 1200 --execute
--i-understand-this-spawns-real-sessions` (this session, after §2's
credential fix, before §1's `--session`/cleanup-order fixes existed on
disk) — result
(`9060451849ffbae4c17d82e9e5c6ce9841eac691:docs/issue-3245/_assets/02-onboarding-experiment/result.json`):
both arms `dispatch_returncode: 0` (real dispatch succeeded), both arms
`watch_returncode: 1` (`"기록 없음 — 아직 스폰된 적이 없다"`), pair
excluded, `h1`/`h2` both `null`.
derived: `gh pr list --repo JiwonJung94/study-companion --json
number,headRefName,createdAt` (this session, after the run finished) —
result: PR #31 (`issue-21/...-c2e23e59`) exists — the on arm really did
produce a real deliverable, `watch` simply never found it. No PR yet
for issue 22 as of this check.

Both underlying bugs are fixed as of `9060451849ffbae4c17d82e9e5c6ce9841eac691`,
but this specific attempt predates both fixes and its session-log
evidence is gone (destroyed by the pre-fix cleanup ordering, same
mechanism as pair 1's loss). Given the turn budget, a third real
dispatch under the now-fixed code was not run this session.
`result.json` states this plainly.

### Pairs 3-5

Not run.
derived: `gh issue list --repo JiwonJung94/study-companion` (this
session, this turn) — lists only issues 1-22. The six follow-up issues
pairs 3-5 need are drafted
(`9060451849ffbae4c17d82e9e5c6ce9841eac691:docs/issue-3245/decisions/drafted-followup-issues.md`,
carried forward unmodified from round 2) but not filed.
derived: `printenv CLAUDE_SKILL` (this session, this turn) — non-empty,
the same condition `gh-guard.sh` denies `gh issue create` under. This
session cannot file them.

### PR #3251 diagnosis correction

canonical: PR #3251's own record (branch
`issue-3245/experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-7b04b22b`,
head `16e96c75442d6804cdb0707326157c6c55dacc20`, read this session via
`gh pr view 3251`), plus the reproductions and verifications cited in
full in §2 above.

PR #3251's record attributes both arms' dispatch failure to "CLI 2.1.259
does not fire plugin hooks in headless mode... blocks every `spawn.py
--skills` dispatch on this machine right now." **That diagnosis does
not hold up** — confirmed three times (§2): by independent-verification-1,
independent-verification-2, and this session's own live reproduction.
The real cause is `prepare_arms.py`'s fresh, isolated HOME carrying no
OAuth credential.

The round-3 spawning prompt's own framing ("no plugin installation") is
close but not precise: skill mounting is via `--plugin-dir` (built from
`MUSTER_SKILL_REPO`), unaffected by `HOME` — it is a missing OAuth
*credential*, not a missing *plugin installation*. Stated precisely so
an imprecise correction does not itself become the next thing taken on
faith.

## Why

canonical: `docs/issue-3245/decisions/pinning-and-sample-size.md`
(carried forward unmodified from round 2, read this session) — the
pre-registered decision rule this round's interpretation must not
deviate from.

The watch-race fix preserves the invariant the orchestrator's finding
named: an arm that genuinely never dispatched must still report "never
happened" — only an arm known to have dispatched, whose post-hoc log
lookup then comes up empty, gets "unknown". `repo`/`issue` are opt-in
per call site so this cannot silently relabel a genuine absence.

Pair 1's H1 was reported unrecoverable rather than inferred from the PR
body's own content because session logs, not PR bodies, are H1's trust
root precisely because the model's own generation cannot forge them —
substituting a forgeable signal would defeat the reason H1 exists.

experiment-trust (invoked via Skill tool): Step 1's scope gate routes
this measurement away from SRM/A-A — a pre-assigned, small-n paired
offline comparison, not random assignment of live traffic.
`docs/issue-3245/decisions/pinning-and-sample-size.md` governs
interpretation instead. Step 5 (Twyman's law): neither result this
round is a record-breaking effect needing independent validation before
reporting — pair 1 is a 7-7 tie, pair 2 has no H2 at all.

## What did not work

canonical: `/tmp/pair2_run.log`, this session's own artifact this turn.

The first pair-2 dispatch attempt failed closed with the exact PR #3251
signature before the credential-seeding fix landed (§2). The attempt
that followed (after the credential fix, before the
`--session`/cleanup-order fixes) succeeded at dispatch but lost its
H1/H2 evidence to the two bugs found mid-run, cited with their own
commands/results in §1 and §4 above.
acceptance: `python3 -m pytest tests/test_issue_3127_h1_and_scoring.py
tests/test_issue_3127_run_consumer_pair.py tests/test_issue_3127_run_pair.py
tests/test_issue_3245_pair_results.py tests/test_consumer_path_trust_root.py -q`
(this session, this turn) — result:
```
76 passed in 0.96s
```
Those fixes are landed and unit-tested but not re-verified against a
fresh real dispatch, for turn-budget reasons — a future round should
re-run pair 2 first, before pairs 3-5, to confirm the fix closes the
loop end-to-end.

## Upstream basis

canonical: this session's own tool transcript, this turn, for every
citation above.

- `docs/issue-3245/reports/independent-verification-1.md` (PR #3253,
  merged `43475e4a`) and `independent-verification-2.md` (PR #3254,
  merged `c2e23a4b`) — both traced PR #3251's failure to the same
  credential gap; this round's own live reproduction (§2) confirms it a
  third time, independently.
- `16e96c75442d6804cdb0707326157c6c55dacc20:scripts/consumer-path/run_pair.py`
  (PR #3251, open, not merged, not edited by this session) — the
  launcher this round builds forward from.
- The never-landed workspace at branch
  `issue-3245/experiment-trust+implementation-blueprint+silent-failure-audit-f264980e`
  (stranded on `pr-create-failed`, never opened a PR) — its
  `seed_arm_credentials()` was ported directly (with its own test suite)
  after confirming its `transport.json` records a real, successful
  credential-seeded dispatch; this session independently found and
  fixed the `--session`/cleanup-order bugs before reading that
  workspace's own account of the `--session` half of the same finding.
- `docs/issue-3245/decisions/pinning-and-sample-size.md`,
  `drafted-followup-issues.md` — round 2's pre-registration and n<=2
  ceiling, carried forward unmodified.

## Open findings

canonical: this session's own tool transcript, this turn (the
acceptance runs and artifacts cited in full in §1-4 above).

1. Pairs 3-5 remain unfiled and unrun (gh-guard blocks this session from
   filing them). Resolution path: the orchestrator files the six
   drafted issues on `JiwonJung94/study-companion`, then a future round
   runs them against this branch's fixes.
2. Pair 1's H1 is permanently unrecoverable on this machine. Resolution
   path: none — the evidence no longer exists; stated so the exclusion
   reads as "couldn't check," not "checked and failed."
3. Pair 2's dispatch succeeded (§4) but its H1/H2 evidence was lost to
   the two bugs found and fixed this round (§1), which pass 76 unit
   tests (§1's `acceptance:` block) but are not yet re-verified against
   a fresh real dispatch. Resolution path: re-run pair 2 first in the
   next round, before attempting pairs 3-5.

## Next steps

canonical: `9060451849ffbae4c17d82e9e5c6ce9841eac691:docs/issue-3245/_assets/01-study-groups/result.json`
and `.../02-onboarding-experiment/result.json`, plus the `h2_evaluation.json`
acceptance run cited in full in §3 above.

Reported results (the only two pairs this round could attempt, per the
registered n<=2 ceiling):

| pair | H1 | H2 | tally |
|---|---|---|---|
| 01-study-groups | unrecoverable | 7-7, indistinguishable (supplementary, not gated) | tie (unscored formally) |
| 02-onboarding-experiment | unrecoverable this attempt | not computed | unscored |

Wins: 0. Ties: 1 (pair 1, supplementary color, not formally scored since
H1 could not pass). Losses: 0. n=0 of the registered n>=5 floor formally
scored this round — stated plainly, not softened, per Open findings
#2-#3's resolution paths above. The question the issue poses ("does
skills-on win, and by how much") has no answer yet; this round's
contribution is a harness that can actually produce one, once a fresh
dispatch is re-run under the fixes landed here.

`loop_state: scope-undeclared` — round 3's three explicit tasks are
addressed to the extent this session's turn budget and gh-guard's own
scope allowed; what remains belongs to a future round, per Open findings
#1 and #3's resolution paths, not an open loop this session is still
working.

## Skill verdicts

canonical: this session's own tool transcript, this turn -- every Skill
tool invocation and its result cited below happened this session, this
turn.

- skill-verdict: silent-failure-audit — applied: invoked; audited
  `_discover_arm_branch()` and `seed_arm_credentials()` — see "What was
  done" §1-2 for the specific findings.
- skill-verdict: experiment-trust — applied: invoked; Step 1's scope
  gate routed this measurement away from SRM/A-A — see "Why".
- skill-verdict: implementation-blueprint — not-applicable: this
  round's changes are a handful of new functions added to already-
  structured existing modules; `prep.py classify --surface backend
  --external no --logic crud --asynchronous no` (run this session)
  returned `data-centric`, but the actual diff is well under this
  skill's single-file/small-function threshold.
- other mounted/considered skills: work-in-english applied throughout
  (record, commits, code comments in English; this end-of-turn summary
  in Korean per its own routing rule). adversarial-review not-applicable
  per skill_judge's own logged reasoning (`docs/issue-3245/reports/
  consult-log/20260903T040711961123-1763660.md`, read this session):
  "Diagnosis is already proven false; task is correcting a known error,
  not assessing [a fresh] creation." prose-modes (skill_judge's
  post-dispatch amendment pick) attempted via Skill tool this session,
  result `Unknown skill: prose-modes` — present under
  `$MUSTER_SKILL_REGISTRY_ROOT` but not registered in this session's
  harness skill list, so it could not be loaded despite being judged
  applicable.
