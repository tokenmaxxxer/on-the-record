---
issue: 2941
role: adversarial-review-2c0dae04
author: adversarial-review-2c0dae04
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2956 (diagnose-first+observability-explorability-10513571's deliverable)
code_under_review: spawn.py, watchdog.py, test/test_not_yet_vs_gone.py (PR #2956, commit 2f46677bcc11adc6e04eb55443936461c4bf67e1)
type: verification
breaking: no
verdict: pass-with-findings — core mechanism confirmed live at both sites with independently-constructed fixtures; one significant open finding on a safety-net-erosion risk the PR's own record understates as merely "unmeasured" (see Finding 1); two lower-severity findings. See "Findings".
loop_state: landed
upstream:
  - path: docs/issue-2941/reports/diagnose-first+observability-explorability-10513571.md
    sha: fd5a93f9a28b6c715e29420c27edb19a877a34a3
  - path: spawn.py, watchdog.py, test/test_not_yet_vs_gone.py
    sha: 2f46677bcc11adc6e04eb55443936461c4bf67e1
---

# issue-2941 — adversarial-review-2c0dae04 record

canonical: `gh pr view 2956` (this session) — result: state OPEN, +436/-4, author JiwonJung94, url https://github.com/tokenmaxxxer/on-the-record/pull/2956.
canonical: `gh issue view 2941` (this session, read before any other tool call) — full body captured; the "43 firings", four confirmed PR numbers (#2930/#2934/#2937/#2919-verification), and the "must not resolve disagreements silently" clause quoted below are the issue's own text as read this session, not re-derived independently (this session has no access to the original raw session logs — same limitation the builder's record discloses).

## What was done

Independently re-verified PR #2956 against issue #2941's acceptance criteria, per the assignment's five attack points. Read `fd5a93f9a28b6c715e29420c27edb19a877a34a3:docs/issue-2941/reports/diagnose-first+observability-explorability-10513571.md` only to locate claims, then re-derived every claim from the diff, a `git worktree` checkout of the PR's real head, and live execution — not from the record's own prose. The worktree (`/tmp/review-2956/wt`, checked out at `fd5a93f9a28b6c715e29420c27edb19a877a34a3`) was removed after use this session (`git worktree remove /tmp/review-2956/wt --force`); citations below to files under that commit use the `<sha>:<path>` form since that path does not exist on this session's own branch.

**1. Both sites' tests, independently re-run.**
derived: `python3 -m pytest test/test_not_yet_vs_gone.py -q` (this session, in the PR worktree at `fd5a93f9a28b6c715e29420c27edb19a877a34a3`) — result:
```
7 passed in 0.90s
```
Matches the PR's claim.

**2. Pre-fix comparison via `git checkout` of the merge-base (not `git stash` — the worktree had no uncommitted diff to stash).**
derived: `git merge-base HEAD origin/main` → `8c60562c82c5b95b78ceb07126856091eba252f7`; `git checkout 8c60562c -- spawn.py watchdog.py && python3 -m pytest test/test_not_yet_vs_gone.py -q` (this session, in the PR worktree) — result:
```
FAILED test/test_not_yet_vs_gone.py::ReconcilePrIndexConsistencyTest::test_still_flags_a_real_missing_pr
FAILED test/test_not_yet_vs_gone.py::ReconcilePrIndexConsistencyTest::test_with_index_reads_the_same_source_as_poll_report
FAILED test/test_not_yet_vs_gone.py::ReconcilePrIndexConsistencyTest::test_no_more_pr_expected_missing_when_index_already_has_it
FAILED test/test_not_yet_vs_gone.py::RecutNotYetVsGoneTest::test_construction_actually_differs
FAILED test/test_not_yet_vs_gone.py::RecutNotYetVsGoneTest::test_freshly_started_branch_is_not_recut
5 failed, 2 passed in 0.92s
```
Exact same 5-name failure set the PR's record names. `git checkout HEAD -- spawn.py watchdog.py` restored the PR versions afterward; `git status --porcelain` (this session) — result: empty. Confirms claim (c).

**3. Full suite, both sides, failing-test-name comparison (not just count).**
derived: `timeout 280 python3 -m pytest test/ tests/ -q -p no:cacheprovider` on PR head (this session, in the PR worktree) — result:
```
16 failed, 590 passed, 3 xfailed in 32.25s
```
Matches PR's claim.
derived: same command against `8c60562c`-restored `spawn.py`/`watchdog.py` (this session, in the PR worktree) — result:
```
21 failed, 585 passed, 3 xfailed in 32.14s
```
Both full 16- and 21-name lists were captured in this session's tool output; the 21 pre-fix names are exactly the 16 post-fix names plus the 5 named in item 2 (the new test file requires the fix). Confirms the "same by NAME" requirement, not just count — both full name lists are visible in this session's own transcript, compared line by line this session.

**4. Both live cases (issue's acceptance check 1), constructed independently of the PR's own test harness.**
The PR's own `test_genuinely_absorbed_branch_is_still_recut` (`2f46677bcc11adc6e04eb55443936461c4bf67e1:test/test_not_yet_vs_gone.py`) uses `mock.patch.object(spawn, "time")`. This session deliberately used a different technique for both cases — a real git repo/reflog, with the reflog file's own on-disk timestamp rewritten directly, never `mock.patch` — so a bug the mock technique itself might hide would not also hide from this review.

- **Case A (freshly-started, no mocking at all):** ad hoc script `/tmp/review-live/probe2.py` (this session; scratch, not committed) — real `git clone`, real `checkout -b`, base advanced past the branch by a second clone pushing to origin/main, then called `spawn._recut_absorbed_branch()` for real. derived: this session's own script run — result:
```
[spawn] issue-2941/live-probe 는 origin/main 대비 0-ahead 지만 0초 전에 막 만들어졌다 — 아직 커밋할 시간이 없었을 뿐일 수 있어 (not yet, not gone) 재컷하지 않고 그대로 둔다.
CASE A: returncode 0 unchanged? True
```
- **Case B (genuinely absorbed, reflog timestamp edited on disk):** same script — `_branch_created_age_sec()` measured age directly from the edited file, `_recut_absorbed_branch()` recut. derived: this session's own script run — result:
```
measured age via real function (no mock): 3900.7844376564026 vs grace 300
[spawn] issue-2941/live-probe-old 는 origin/main 에 완전히 흡수돼 커밋이 없다 — 로컬 브랜치를 지우고 새로 판다.
CASE B: returncode 0 recut happened? True matches base tip? True
```
This satisfies #2941's acceptance check 1 (both cases constructed live, classified differently) and, independently, confirms #732's original requirement (absorbed branches still get recut) is not regressed by this PR — attack point 4 of the assignment.

**5. Overhead claim, re-derived from source, not trusted from the record's stated diff-stat.**
canonical: `2f46677bcc11adc6e04eb55443936461c4bf67e1:watchdog.py` lines 1770-1790 (read this session, in the worktree before it was removed) — `_poll_pr_index()` is a per-`roster_watchdog()`-call memoized closure (`_poll_pr_index_cache: list = []`, `if not _poll_pr_index_cache: _poll_pr_index_cache.append(_sp._board_pr_index(root))`), defined once above the `for key, e in sorted(d.items())` loop and now called from the issue-#492 `reconcile()` line (previously called `_sp._build_observed(root, e)` with no `pr_index`, now `pr_index=_poll_pr_index()`) for every entry, live or dead. Pre-fix, that same line called `_pr_open_or_merged_for_branch()` (one `gh pr list --head <branch>` subprocess) once per entry, every tick, unconditionally — confirmed by reading `8c60562c82c5b95b78ceb07126856091eba252f7:spawn.py`'s `_build_observed()` body (`pr_number = _pr_open_or_merged_for_branch(root, branch) if branch else None`, no `pr_index` parameter existed pre-fix). Post-fix this becomes at most one `_board_pr_index()` GraphQL call total per tick (memoized), shared across every entry — a bigger decrease than the PR's own description ("removes a gh call per dead entry per tick"), since it also removes the call for live entries, and ticks with zero dead entries previously made zero board calls (lazy) but N per-branch calls; now they make one board call and zero per-branch calls. Site 2: derived: `grep -n "_recut_absorbed_branch(cwd\|_checkout_named_branch(cwd" pipeline.py spawn.py` (this session, worktree) — result: called from `checkout_issue_branch()`/`_checkout_named_branch()` (once per spawn attempt) and `recut_if_absorbed_cli()` (once per pre-commit gate invocation), never the per-tick watchdog loop. Claim (e) holds, understated if anything.

**6. `SPAWN_ATTEMPT_GRACE_SEC` reuse, not a new constant.**
derived: `grep -n "SPAWN_ATTEMPT_GRACE_SEC" roster.py spawn.py` (this session, worktree) — result includes `roster.py:568:SPAWN_ATTEMPT_GRACE_SEC = 180 + 60 + 60` and `spawn.py:1856: now - ts < SPAWN_ATTEMPT_GRACE_SEC:` (a pre-existing, unrelated use for the analogous "how long can a legitimate spawn attempt take" judgment). Confirms claim (b)'s "not a new guessed constant" half.

**7. No retired-role-axis revival.**
derived: `git show 2f46677bcc11adc6e04eb55443936461c4bf67e1 -- spawn.py watchdog.py test/test_not_yet_vs_gone.py | grep -iE '^\+.*\brole\b'` (this session, worktree) — result: empty output. Confirmed.

## Why

This session re-derived every claim from primary sources rather than trusting the builder's record, per the assignment and the adversarial-review skill's core mechanism (session separation defeats self-defense of prior reasoning). Where the PR's own test harness used mocking, this session deliberately used a structurally different construction (direct reflog-file editing instead of `mock.patch`) for the two live cases in item 4, so a bug hidden by the mock technique itself would not also hide from this review.

## Findings

**Finding 1 (assignment's attack point 2 — most severe, not blocking): the site-1 "architectural difference" justification does not hold for the steady-state path, and the safety-net-erosion risk is real, not merely unmeasured.**

canonical: `2f46677bcc11adc6e04eb55443936461c4bf67e1:docs/issue-2941/reports/diagnose-first+observability-explorability-10513571.md` (this session, worktree) — the PR's own record frames `_board_pr_index()` as immune to propagation lag, citing "bulk connection query vs. search-index-backed head filter" and lists the shared-source-staleness risk only as an unmeasured, assumed-away open finding ("assumed, not measured, to be free of the same propagation lag").

canonical: `2f46677bcc11adc6e04eb55443936461c4bf67e1:gates/board_read.py` (this session, worktree, full file read) — this framing is only true for the full read (Layer 1: two direct `repository { issues, pullRequests }` connection queries, run on snapshot-miss, `BOARD_READ_FORCE_FULL=1`, or every `BOARD_READ_FULL_EVERY`-th sweep, `_DEFAULT_FULL_EVERY = 20` at `gates/board_read.py:44`). The steady-state read — used on most ticks per the module's own docstring ("an unchanged board costs exactly 1 API call") — is `_delta_read()` (`gates/board_read.py:231-246`), which issues a GraphQL `search(query: "repo:<slug> updated:>=<since>", type: ISSUE, ...)` call (`_SEARCH_QUERY`, `gates/board_read.py:81-96`):
```
231:def _delta_read(run: Callable, root: Path, slug: str,
232:               since: str) -> tuple[list[dict] | None, bool]:
...
239:    q = f"repo:{slug} updated:>={since}"
240:    docs = _run_graphql(run, root, _SEARCH_QUERY, {"q": q}, paginate=False)
```
That is GitHub's Search API — the same indexing-pipeline class as `gh pr list --head <branch>` (also search/list-index-backed per `board.py:526`'s `gh pr list --head` call this PR replaces), not a direct DB read. A brand-new PR GitHub's search index has not yet indexed is exactly as reachable to go missing from a delta-read snapshot as from the original per-branch call.

This matters specifically because of what the fix does: it makes reconcile's `_build_observed()` and poll-report's `diagnose_health()` read the literal same `pr_index` object within a tick (see "What was done" item 5 above). Before this fix, the two sides had independent propagation-lag windows — issue #2941's own text credits this independence with turning the reported disagreements into a safe, if noisy, failure ("43 false positives cost attention rather than duplicate sessions", per the `gh issue view 2941` canonical citation above). After this fix, if the shared board snapshot itself has not caught up on a new PR — architecturally plausible per the two code citations above — both reconcile and poll-report derive `pr_number=None` from the identical stale index and agree with each other, wrongly, with no `[reconcile-poll-disagreement]` line printed. That is the exact trade issue #2941's own acceptance criteria forbid (`gh issue view 2941`, "must not" section: "must not fix this by ... resolving disagreements silently instead of reducing them — trades a noisy failure for an invisible one").

unverifiable: this session did not attempt to construct the shared-source-staleness case live — reason: no safe way to time real GitHub search-index propagation lag without spamming the production repo with throwaway PRs, the same limitation the builder's own record discloses for the opposite direction. This finding is source-code-grounded (the two `gates/board_read.py` citations above), not a live-observed regression, and does not mean the fix is net-negative — it genuinely closes the originally-reported two-independent-readers disagreement shape (confirmed live in "What was done" items 1-4). But it reframes the PR's own "unmeasured assumption" framing: the "architectural difference" claim does not hold for the steady-state delta path by direct code reading, not merely unquantified, and the consequence specifically targets the one safety net (#2882's disagreement check) issue #2941 itself credits with containing the original failure's blast radius.

**Finding 2 (assignment's attack point 1, minor — evidentiary rigor, not correctness): the PR's synthetic before/after batch does not add independent trials of evidence beyond a single run.**

canonical: `2f46677bcc11adc6e04eb55443936461c4bf67e1:docs/issue-2941/reports/diagnose-first+observability-explorability-10513571.md` section "4. Re-derived false-positive count" — the record's script mocks `_pr_open_or_merged_for_branch` to return `None` and always supplies a `pr_index` that already has the PR, repeated across a batch of fresh throwaway git repos, reported as `BEFORE: 10/10 pr-expected-missing` and `AFTER: 0/10 pr-expected-missing`.
canonical: `2f46677bcc11adc6e04eb55443936461c4bf67e1:spawn.py` `_build_observed()` body — `if pr_index is not None: pr_number = _pr_state_from_index(pr_index, branch)` (no branching on the mocked call's own return value once `pr_index` is supplied). Given this control flow, the outcome is deterministic given the two mocked inputs — every repetition exercises the identical branch with the identical result; varying the underlying git repo per repetition does not vary the thing being measured. This session independently confirmed the same deterministic behavior via `test_with_index_reads_the_same_source_as_poll_report`/`test_no_more_pr_expected_missing_when_index_already_has_it` (item 1 above, `assert_not_called()` on the live call), which assert the identical thing without repetition. Not a fabricated result — the PR's own framing ("synthetic... not a re-read of a raw log file") is honest about not being the real 43 firings from the issue — but it does not disclose that the repeated batch itself adds no statistical weight over a single run; it is one data point restated many times. Does not affect the correctness verdict: the fix's control-flow logic is genuinely and correctly tested elsewhere (item 1's `7 passed`, independently re-run by this session). Presentation/evidentiary-weight note only.

**Finding 3 (assignment's attack point 3, low severity, verified live, currently unreachable via this repo's own clone path): `_branch_created_age_sec()` fails open into the exact pre-fix destructive behavior when the local ref has no reflog.**

derived: ad hoc script `/tmp/review-live/probe3.py` (this session; scratch, not committed) — constructed a repo with `git config core.logallrefupdates false` set before the branch was created, then called the real `spawn._branch_created_age_sec()` and `spawn._recut_absorbed_branch()`. Result:
```
age with logallrefupdates=false: None
[spawn] issue-2941/no-reflog 는 origin/main 에 완전히 흡수돼 커밋이 없다 — 로컬 브랜치를 지우고 새로 판다.
returncode: 0 recut happened (destroyed the fresh branch)? True
```
`_branch_created_age_sec()` correctly returned `None` per its documented fail-open contract, but `_recut_absorbed_branch()`'s `if age is not None and age < SPAWN_ATTEMPT_GRACE_SEC` guard then fell through to the pre-fix unconditional recut, destroying a genuinely-fresh branch with no distinguishing stderr message (identical output to a genuinely-absorbed branch). canonical: `2f46677bcc11adc6e04eb55443936461c4bf67e1:spawn.py` `_recut_absorbed_branch()` — a few lines above the new guard, the pre-existing `remote_ahead` lookup-failure path takes the identical "proceed as if fine" shape, so this is consistent with — not a new deviation from — this function's own pre-existing convention, and the function's own docstring comment states this explicitly. derived: `grep -n '"clone"' pipeline.py spawn.py` (this session, worktree) — result: `pipeline.py:440` and `spawn.py:3200` both call plain `git clone -q` with no `--bare`/`--shared`/`logallrefupdates` override, and git's own default for a non-bare clone is `core.logallrefupdates=true` — so this repo's actual clone path should not trigger the reflog-absent case under normal operation. Flagged as a disclosed residual, not a live-reachable defect in this repo today: the fix's efficacy is contingent on an environmental assumption (reflogs enabled) that is asserted nowhere and logged nowhere as missing, so a future change to the clone/workspace strategy could silently reopen the exact bug this issue reports.

**Finding 4 (assignment's attack point 4 — checked, no defect, confirmed working): #732's requirement is intact.**
See "What was done" item 4, Case B — independently reproduced with a construction technique different from the PR's own tests (direct reflog-file edit vs. `mock.patch`). A genuinely old/absorbed branch is still recut to the current base tip.

## What did not work

None — every re-derivation this session attempted succeeded in reproducing or refuting the specific claim it targeted; no dead end required backtracking to a different method. One scratch script needed a mid-session fix — a workspace-object mix-up in `probe2.py`'s `advance_base()` helper, corrected before the result quoted in item 4 above was captured — ordinary script debugging, not a deviation from the review's approach.

## Upstream basis

- `fd5a93f9a28b6c715e29420c27edb19a877a34a3:docs/issue-2941/reports/diagnose-first+observability-explorability-10513571.md` — used only to locate claims to independently re-derive, not trusted as evidence in itself, per this session's spawn contract. Not present on this session's own branch; cited commit-pinned throughout.
- `2f46677bcc11adc6e04eb55443936461c4bf67e1:spawn.py`, `2f46677bcc11adc6e04eb55443936461c4bf67e1:watchdog.py`, `2f46677bcc11adc6e04eb55443936461c4bf67e1:test/test_not_yet_vs_gone.py` (PR #2956 head `fd5a93f9a28b6c715e29420c27edb19a877a34a3`, fix commit `2f46677bcc11adc6e04eb55443936461c4bf67e1`) — the code under review, checked out in a `git worktree` this session created and removed.
- `2f46677bcc11adc6e04eb55443936461c4bf67e1:gates/board_read.py` — unchanged by this PR, read this session; load-bearing for Finding 1's tracing of the PR's own safety-net justification.

## Open findings

**Finding 1 above** is the load-bearing one. Suggested follow-up body:

> **Title:** Measure `_board_pr_index()`'s own new-PR propagation lag — #2941's fix unifies reconcile and poll-report onto a source that is itself GraphQL-search-backed on its steady-state path
>
> #2941's fix (PR #2956) threads a shared `pr_index` into both `reconcile()`'s `_build_observed()` and poll-report's `diagnose_health()`, justified by `_board_pr_index()` (`gates/board_read.py`) being architecturally immune to the search-index propagation lag that caused the original false `pr-expected-missing` firings. That is only true for the full read (every `BOARD_READ_FULL_EVERY`-th sweep); the steady-state delta read (`_delta_read()`, `gates/board_read.py:231-246`) issues its own GraphQL `search(...)` query and is subject to the same lag class (see this record's Finding 1 for the citations). Because both reconcile and poll-report now read this one source, a lag here would make the two sides agree silently instead of disagreeing loudly — exactly the trade #2941's own acceptance criteria forbid. Acceptance: either measure real-world delta-search lag for newly-created PRs against this repo, or restore some independent cross-check between reconcile and poll-report that does not depend on both reading byte-identical data.

## Next steps

None — `loop_state: landed`. This record is the terminal deliverable for this session; no code changes made to the PR itself, per the assignment ("you evaluate this PR, you do not fix it").

## Verification

derived: `gh pr view 2956` (this session) — result: state OPEN, +436/-4, author JiwonJung94.
derived: `git fetch origin pull/2956/head:pr-2956 && git worktree add /tmp/review-2956/wt pr-2956` (this session) — worktree created, later removed via `git worktree remove /tmp/review-2956/wt --force`; `git worktree list` (this session, after removal) — result: only this session's own working directory listed.
derived: `python3 -m pytest test/test_not_yet_vs_gone.py -q` (this session, in the PR worktree at `fd5a93f9a28b6c715e29420c27edb19a877a34a3`) — result: `7 passed in 0.90s`.
derived: `git checkout 8c60562c -- spawn.py watchdog.py && python3 -m pytest test/test_not_yet_vs_gone.py -q` (this session, in the PR worktree) — result: `5 failed, 2 passed in 0.92s`; `git checkout HEAD -- spawn.py watchdog.py` restored the PR versions, confirmed via `git status --porcelain` (this session) — result: empty.
derived: `timeout 280 python3 -m pytest test/ tests/ -q -p no:cacheprovider` on PR head (this session, in the PR worktree) — result: `16 failed, 590 passed, 3 xfailed in 32.25s`.
derived: same command against `8c60562c`-restored `spawn.py`/`watchdog.py` (this session, in the PR worktree) — result: `21 failed, 585 passed, 3 xfailed in 32.14s`; full 16- and 21-name lists visible in this session's own tool-call transcript, confirmed by manual line-by-line comparison this session (16 names identical on both sides, 21 = 16 + the 5 new-test failures from item 2).
derived: two standalone Python scripts (`/tmp/review-live/probe2.py`, `/tmp/review-live/probe3.py`, this session, scratch, not committed, cleaned up with the rest of `/tmp/review-live`) — full output quoted in "What was done" item 4 and "Findings" Finding 3 above.
derived: `grep -n "_SEARCH_QUERY\|def _delta_read\|def board_read\|def _board_pr_index" gates/board_read.py watchdog.py` (this session, worktree) — confirms the delta read's search-API backing (Finding 1).
derived: `grep -n "SPAWN_ATTEMPT_GRACE_SEC" roster.py spawn.py` (this session, worktree) — result: `roster.py:568:SPAWN_ATTEMPT_GRACE_SEC = 180 + 60 + 60`, pre-existing, not invented by this PR.
derived: `git show 2f46677bcc11adc6e04eb55443936461c4bf67e1 -- spawn.py watchdog.py test/test_not_yet_vs_gone.py | grep -iE '^\+.*\brole\b'` (this session, worktree) — result: empty, no retired-axis revival.

skill-verdict: adversarial-review — applied: invoked; this entire session is the evaluator role the skill describes (structurally independent session, receives the PR diff, re-derives every claim from primary sources rather than trusting the builder's record) — the skill's "session separation defeats self-defense" mechanism is the reason this session was spawned separately from the one that authored PR #2956.
other mounted skills: not triggered (work-in-english applies via core hook enforcement, not a Skill-tool invocation; implementation-audit and verify-finding-record were configured for this task's text match but this session followed the assignment's own explicit framing — an adversarial review of a PR, attacking five named points — rather than a claim-by-claim requirements audit).

Four standing invariants, each checked this session:
1. No revival of the retired role axis — see "Verification" above, `grep` result empty.
2. No new bug — full-suite failing-test-NAME set is identical pre-fix vs. post-fix (16 names both sides, confirmed by inspection above); Finding 1 is an architectural risk in the fix's own design (no test fails, no crash, no live-observed incident this session could produce), not a conventional regression.
3. No overhead increase — confirmed and understated in the PR's own favor, see "What was done" item 5.
4. Monitor/watch machinery unbroken — full suite (item 3 above) includes `test_workspace_progress_tracking.py`/`test_session_completion_heartbeat.py`, both passing on PR head; this diff touches `spawn.py`/`watchdog.py` but only adds a threaded parameter (site 1) and a new fail-open-consistent guard (site 2) — this session found no removal or narrowing of existing watch paths.
