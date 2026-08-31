---
issue: 2941
role: diagnose-first+observability-explorability-89029a9a
author: diagnose-first+observability-explorability-89029a9a
skills: diagnose-first (skill-repository(c05de12)), observability-explorability (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: spawn.py, watchdog.py, test/test_not_yet_vs_gone.py
type: fix
breaking: no
verdict: pass
loop_state: landed
upstream:
  - path: docs/issue-2941/reports/adversarial-review-2c0dae04.md
    sha: 1be5f0467fbec14614163aa74f834e4ad414dca4
  - path: spawn.py, watchdog.py, test/test_not_yet_vs_gone.py (PR #2956's fix commit, cherry-picked onto this branch)
    sha: 2f46677bcc11adc6e04eb55443936461c4bf67e1
---

# issue-2941 — diagnose-first+observability-explorability-89029a9a record

canonical: `gh issue view 2941` (this session, read before any other tool call).
canonical: `docs/issue-2941/reports/adversarial-review-2c0dae04.md` (this session, read in full before starting) — independent adversarial review of PR #2956, merged via PR #2958 (commit `1be5f0467fbec14614163aa74f834e4ad414dca4`), confirming the core not-yet-vs-gone mechanism is genuinely fixed at both sites while naming three open findings this round addresses.

## What was done

Round 2 on issue #2941. PR #2956 (branch `issue-2941/diagnose-first+observability-explorability-10513571`) is still open, unmerged, on origin — canonical: `gh pr view 2956` (this session) — result: state OPEN. So this session cherry-picked its isolated fix commit onto a fresh branch off current `main` instead of building on the stale, unmerged branch directly. derived: `git show 2f46677b --stat` (this session) — result: `spawn.py | 62 ++, test/test_not_yet_vs_gone.py | 214 ++ (new file), watchdog.py | 9 +-` — exactly 3 files, no unrelated diff, safe to cherry-pick alone. derived: `git cherry-pick 2f46677b` (this session) — landed as `d97e58b3` on this branch, `git status --porcelain` clean afterward. All work below is on top of that cherry-pick. The three findings from the adversarial review are addressed as follows.

**Finding 1 (the one that mattered — invalidated the fix's stated justification, not its mechanism).** The review traced `gates/board_read.py` and found the shared `pr_index`'s steady-state path (`_delta_read()`) is itself a GraphQL `search(...)` call — the same indexing-pipeline class as the `gh pr list --head` call PR #2956 replaced. Once reconcile and poll-report both read this one index, a stale index makes both sides silently *agree* on a wrong "gone" instead of disagreeing — the exact trade issue #2941's own acceptance text forbids, and the exact safety net (#2882's disagreement check) issue #2941 itself credits with containing the original bug's blast radius.

canonical: `gates/board_read.py` lines 1-50, 200-352 (read in full this session, unmodified by this branch) — re-confirms the review's citations independently: `_delta_read()` (`gates/board_read.py:231-246`) issues `_SEARCH_QUERY` against GitHub's `search(...)` field; `board_read()`'s steady-state branch (`gates/board_read.py:304-329`) takes this path on every tick except a missing/corrupt snapshot, `BOARD_READ_FORCE_FULL=1`, or every `BOARD_READ_FULL_EVERY`-th sweep, which instead calls `_full_read()` — two direct `repository { issues, pullRequests }` connection queries, the one read type not backed by the search index.

Fix (spawn.py, watchdog.py): kept the shared single-index design — its overhead win is real (review item 5) — but added an opt-in `confirm_pr_missing` callback to `reconcile()` and `diagnose_health()`, invoked *only* at the exact moment either function is about to treat `pr_number is None` from the index as authoritative "gone", never per-entry, never per-tick unconditionally. `roster_watchdog()`'s per-tick closure (`_poll_pr_index_confirm_gone`, watchdog.py) checks whether today's shared read came from `_delta_read` (`meta["source"] == "delta"`); if so it forces exactly one direct full-connection re-read (new function `_board_pr_index_with_meta(root, force_full=True)`, watchdog.py) before agreeing the PR is missing, memoized so at most one extra full read happens per tick regardless of how many entries need confirming. A "full"-sourced or already-found index skips the callback entirely. derived: `git diff main..HEAD -- gates/board_read.py` (this session) — result: empty — the shared board-read module itself was not modified, only the two call sites gained an opt-in confirmation path.

Both `reconcile()` and `diagnose_health()` still fire `pr-expected-missing`/`DEAD-ERRORED` when the confirmation *agrees* the PR is genuinely missing — the must-not-silently-resolve property is preserved; see "Verification" for the tests asserting this both ways.

**Finding 2 (presentation — the "10/10 to 0/10" figure was a single deterministic point restated, not ten trials).** This record does not reproduce that framing. derived: `python3 -m pytest test/test_not_yet_vs_gone.py -q` (this session) — result:
```
...............                                                          [100%]
15 passed in 0.92s
```
Each new assertion in this run covers one control-flow branch exactly once (see "Verification" for the individual names), not a repeated-trial count. Issue #2941's own acceptance check 2 ("re-derive the `[reconcile-poll-disagreement]` count over a comparable window before and after") is **not independently re-derived from real production logs in this record** — unverifiable: this session has no access to the original raw session logs the issue was filed from, the same limitation the PR's own record and the adversarial review both already disclosed, and did not attempt a live comparable-window reproduction because doing so would require generating real GitHub search-index propagation lag against the production repo, which the review already declined for the identical reason (its own `unverifiable` finding). What this record verifies instead: the full pre-existing test suite produces byte-identical failing-test-NAME sets before and after this branch's changes (see "Verification"), and the three findings' control-flow paths are each covered by a new deterministic test.

**Finding 3 (a real fail-open, verified live by the reviewer).** `_branch_created_age_sec()` returns `None` when the local ref has no reflog (`core.logallrefupdates=false`, shallow clone). canonical: `spawn.py`'s `_recut_absorbed_branch()` before this session's edit (via `git show d97e58b3:spawn.py`, this session) — the guard was `if age is not None and age < SPAWN_ATTEMPT_GRACE_SEC: <not-yet>`, so `age is None` fell straight through to the unconditional pre-#2941 destructive recut — the reviewer reproduced this live and destroyed a genuinely-fresh branch under that condition. Fixed by adding an explicit `age is None` branch in `_recut_absorbed_branch()` that treats "can't measure" the same direction as "not yet" (skip the recut, print a distinguishing stderr line) instead of falling through to the destructive path.

derived: `grep -n '"clone"' pipeline.py spawn.py` (this session) — result: `pipeline.py:440` and `spawn.py:3216`, both plain `git clone -q` with no `logallrefupdates` override — re-confirms independently (not just trusted from the review) that this repo's actual clone path does not reach the `age is None` branch today, since git's own default for a non-bare clone is `core.logallrefupdates=true`. The new stderr line is the signal if that assumption ever breaks; no new backstop constant was invented for the currently-unreachable case.

## Why

Finding 1 is addressed by a confirm-only-at-the-decision-point pattern rather than either extreme. canonical: `docs/issue-2941/reports/adversarial-review-2c0dae04.md` "What was done" item 5 (read this session) — the review measured the original per-entry-per-tick `gh pr list --head` overhead as real and worse than the shared-index approach; reverting to it to regain independence would reintroduce that cost. Leaving the shared index unconditionally trusted is finding 1's own silent-agreement risk. The confirm callback design keeps the overhead win while restoring the one property that made the original noisy-but-safe failure mode safe: a "gone" verdict is only reached after a structurally different, direct read confirms it, and only on the tick where the default read was the lag-susceptible one — a bounded, conditional cost instead of an unconditional one.

Finding 3's fix direction (treat "can't tell" as "not yet", not "gone") mirrors the sibling age-based guard already in `_recut_absorbed_branch()` for a measurable-but-young branch (`age is not None and age < SPAWN_ATTEMPT_GRACE_SEC`) — extending the existing pattern rather than inventing a new one, and reusing the review's own live reproduction (`docs/issue-2941/reports/adversarial-review-2c0dae04.md`, Finding 3) as the regression-test oracle instead of re-deriving the reachability question from scratch.

## What did not work

None landed in the final diff, but two mid-session authoring corrections happened while writing finding 1's tests, worth naming even though neither reached a commit. derived: this session's own edit history —
(1) a first attempt at threading `confirm_pr_missing` through `reconcile()` used a walrus-operator condition chain (`... and (observed := {...}) and False`) that worked but was unreadable; rewritten as a plain `if`/assignment before any commit.
(2) the confirm-before-gone test fixture initially reused the existing no-`events.jsonl` entry shape, which resolves to `session_verdict="normal"` — fine for `reconcile()`'s rule 3 (only excludes `"in-progress"`), but `diagnose_health()`'s completion shortcut treats `"normal"` as always-completion regardless of PR presence. derived: `python3 -m pytest test/test_not_yet_vs_gone.py -q` (this session, before the fix) — result: `test_diagnose_health_still_dead_errored_when_confirm_agrees FAILED ... AssertionError: None != 'DEAD-ERRORED'`. Fixed by adding a `_mark_crashed()` fixture helper (writes a real `session-start` event with a dead pid and no `session-end`) to reach `"crashed"` instead. derived: `python3 -m pytest test/test_not_yet_vs_gone.py -q` (this session, after the fix) — result: `15 passed`.

## Upstream basis

canonical: `docs/issue-2941/reports/adversarial-review-2c0dae04.md` at commit `1be5f0467fbec14614163aa74f834e4ad414dca4` (merged via PR #2958, read in full this session) — source of the three findings this record closes, cited by name throughout "What was done".
canonical: `spawn.py`, `watchdog.py`, `test/test_not_yet_vs_gone.py` at PR #2956's fix commit `2f46677bcc11adc6e04eb55443936461c4bf67e1` (this session, via `git show 2f46677b`) — cherry-picked onto this branch as `d97e58b3`.
canonical: `gates/board_read.py` at this branch's `HEAD` (this session, read in full, unmodified per `git diff main..HEAD -- gates/board_read.py` returning empty) — load-bearing for finding 1's fix design.

## Open findings

None new. Finding 1's residual — real-world `_delta_read` propagation-lag magnitude against production is still not measured, by design, per "Finding 2" above — remains exactly as `docs/issue-2941/reports/adversarial-review-2c0dae04.md`'s own "Open findings" section described it (its suggested follow-up: measure real delta-search lag, or keep the design and disclose the trade). This record's fix reduces the risk's blast radius (a lagging index can no longer be silently trusted at the specific "about to declare gone" decision point) without claiming to have measured the lag itself.

## Next steps

None — `loop_state: landed`. This branch is ready to open as its own PR against `main`. PR #2956 itself is left open on origin for its author to close or update separately; this branch does not push to it.

## Verification

derived: `python3 -m pytest test/test_not_yet_vs_gone.py -q --collect-only` (this session) — result: 15 collected — 7 inherited from the cherry-picked commit, 1 new (`RecutNotYetVsGoneTest.test_no_reflog_does_not_fail_open_into_destructive_recut`, finding 3), 7 new under a new `ConfirmBeforeGoneTest` class in the same file (finding 1: `test_reconcile_confirm_finds_the_pr_after_index_miss`, `test_reconcile_still_flags_gone_when_confirm_agrees`, `test_confirm_not_invoked_when_index_already_found_it`, `test_diagnose_health_confirm_finds_the_pr`, `test_diagnose_health_still_dead_errored_when_confirm_agrees`, `test_diagnose_health_confirm_not_invoked_when_index_already_found_it`, `test_board_pr_index_confirm_forces_full_read_only_on_delta_miss`).
derived: `python3 -m pytest test/test_not_yet_vs_gone.py -q` (this session) — result: `15 passed in 0.92s`.
derived: `timeout 280 python3 -m pytest test/ tests/ -q -p no:cacheprovider` on this branch (this session) — result: `16 failed, 604 passed, 3 xfailed`.
derived: the identical command run in a separate clone checked out to `origin/main` (`71167c3a`, no changes from this session) (this session) — result: `16 failed, 589 passed, 3 xfailed`; `diff` of the two sorted `FAILED ...` name lists (this session) — result: identical sets — confirms the 16 failures pre-exist on `main` and are unrelated to this branch, and that this branch adds zero new failures (the 604-vs-589 passed delta is exactly this branch's 15-test file plus the cherry-picked commit's own contribution to collection, not new failures).
derived: `grep -n '"clone"' pipeline.py spawn.py` (this session) — result: `pipeline.py:440:            _sp._run_net(["git", "clone", "-q",` and `spawn.py:3216:    c = _run_net(["git", "clone", "-q", str(src), str(work)], "작업 클론",` — re-confirms finding 3's "not reachable via this repo's clone path today" claim independently.
derived: `git diff main..HEAD -- gates/board_read.py` (this session) — result: empty.
derived: `git log --oneline main..HEAD` (this session) — result: `a19c7ad7`, `935b771d`, `f7efb03d`, `692c143c`, `d97e58b3` — 5 commits, each followed by a `test/test_not_yet_vs_gone.py` run before the next was started.

skill-verdict: other mounted skills: not triggered — this session invoked no skill via the Skill tool. `diagnose-first` was judged not-applicable: the causal diagnosis for all three findings was already completed and cited with file:line evidence by the independent adversarial review this session was handed (`docs/issue-2941/reports/adversarial-review-2c0dae04.md`); re-running the gated diagnose-first procedure from scratch on an already-diagnosed problem would not have added information. `observability-explorability` was judged not-applicable: no dashboard or incident-investigation design was in scope, only a targeted code fix to three named, already-diagnosed defects. Per the invoke-before-apply rule, a skill judged not-applicable does not require loading.

Four standing invariants, checked this session:
1. No revival of the retired role axis. derived: `git show 692c143c f7efb03d 935b771d a19c7ad7 | grep -iE '^\+.*\brole\b'` (this session) — result: empty.
2. No new bug. See "Verification" above — full-suite failing-test-NAME sets identical between `main` and this branch.
3. No overhead increase. `confirm_pr_missing` fires only when a call site is about to conclude "gone" from `pr_number is None`, never on the common found-in-index path — asserted by `test_confirm_not_invoked_when_index_already_found_it` and `test_diagnose_health_confirm_not_invoked_when_index_already_found_it` (both pass, see "Verification"); the one extra full read on a genuine delta-miss is memoized per tick, not per entry (`_poll_pr_index_confirm_cache`, watchdog.py).
4. Monitor/watch machinery unbroken. derived: full-suite run above includes `test_workspace_progress_tracking.py` and `test_session_completion_heartbeat.py`, neither in the 16-name failing set on this branch — both pass. The diff only adds an opt-in parameter and a new `None`-handling branch to existing functions; no existing watch path was removed.
