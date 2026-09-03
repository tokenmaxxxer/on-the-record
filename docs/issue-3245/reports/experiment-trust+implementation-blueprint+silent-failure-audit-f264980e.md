---
issue: 3245
role: experiment-trust+implementation-blueprint+silent-failure-audit-f264980e
author: experiment-trust+implementation-blueprint+silent-failure-audit-f264980e
skills: experiment-trust (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: scripts/consumer-path/run_pair.py (same-commit)
loop_state: in-progress
type: measurement
breaking: false
verdict: pending -- real pair dispatches for this round are still running; filled in once they finish, see "Next steps"
upstream:
  - path: docs/issue-3245/reports/independent-verification-1.md
    sha: 43475e4ab9edcbaa20be2c9dcf25b78ed15c40cd
  - path: docs/issue-3245/reports/experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-7b04b22b.md
    sha: same-commit
---

# issue-3245 — experiment-trust+implementation-blueprint+silent-failure-audit-f264980e record

canonical: this session's own tool transcript, this turn -- record
assembly is in progress; sections below marked "pending" are filled in
once this round's real pair dispatches finish (`docs/issue-3245/_assets/
01-study-groups/result.json`, `02-onboarding-experiment/result.json`
once written).

## What was done

1. Read PR #3251, verification PR #3253 (merged as commit `43475e4a`,
   canonical: `gh pr view 3253 --json state` this session, result:
   `"state":"MERGED"`), `docs/issue-3245/reports/
   independent-verification-1.md` in full, the issue's addendum comment,
   and PR #3185's trust-root record.
2. Confirmed live that seeding only `~/.claude/.credentials.json` into
   an otherwise-empty, fresh `tempfile.mkdtemp()` HOME is sufficient for
   `claude -p` to authenticate.
   derived: `HOME=<fresh tempdir, only .claude/.credentials.json seeded>
   claude -p --model haiku --output-format json <<< "Run this exact bash
   command and nothing else: echo ok"` -- result: `"is_error":false,
   "result":"Done."` (exit 0)
3. Implemented `seed_arm_credentials()` in `scripts/consumer-path/
   run_pair.py`, called for both arms after `prepare_arms.build_manifest()`
   returns, before the manifest/transport are persisted. `run_pair()`
   fails closed (`status: "credential-seeding-failed"`) if the operator
   credential is missing.
4. silent-failure-audit (invoked via Skill tool this session): audited
   `seed_arm_credentials()` and found its copy step
   (`mkdir`/`write_bytes`/`chmod`) unguarded -- an `OSError` would have
   crashed `run_pair()` with a bare traceback. Fixed with
   `try/except OSError`.
   derived: `python3 -m pytest tests/test_issue_3245_pair_results.py -q`
   -- result:
   ```
   18 passed in 0.91s
   ```
5. experiment-trust (invoked via Skill tool this session, before
   interpreting any pair result): Step 1's scope gate routed this
   measurement away from the skill's SRM/A-A procedure -- this is a
   pre-assigned, small-n paired offline comparison
   (`docs/issue-3245/decisions/pinning-and-sample-size.md`), not random
   assignment of live traffic to variants. No SRM/A-A check applies; the
   pre-registered decision rule in that same file governs interpretation.
6. Dispatched pair `01-study-groups` (issues #19/#20) with the
   credential fix. Both arms' dispatch succeeded
   (`dispatch_returncode: 0`) but `watch` failed on both
   (`status: "watch-failed"`, stderr "기록 없음 -- 아직 스폰된 적이
   없다").
   canonical: `docs/issue-3245/_assets/01-study-groups/result.json`
   (this session's own dispatch attempt, written by `run_pair.py`)
   Read `spawn.py` and confirmed the cause: every `--skills` dispatch
   always assigns a fresh lease-disambiguated session name
   (`a.role = f"{skill_slug}-{disambiguator}"`), never the bare skill
   name `execute_arm()` was passing to `watch --session`.
   derived: `gh pr list -R JiwonJung94/study-companion --json
   number,headRefName,createdAt --limit 6` -- result includes
   `{"number":26,"headRefName":"issue-19/product-discovery-hypothesis-preregistration-dae6a96f"}`,
   confirming the on-arm's real session completed and opened a PR
   despite `run_pair.py` never observing it; no corresponding PR exists
   for issue #20.
   derived: `ls /tmp/consumer-path-off-home-ume6shqm` -- result:
   directory still present (partially deleted: `.claude` subtree
   remains, `.tokenmaxxxer/work/...` subtree gone) after `run_pair.py`'s
   own process had already exited and run `prepare_arms._cleanup()` --
   the off arm's real session was very likely still using that HOME
   when `shutil.rmtree()` ran, since `watch` gave up early on its own
   lookup failure rather than the session actually finishing.
   Full detail in this round's deviation-log entries.
7. Fixed `execute_arm()`'s `watch` call to omit `--session` entirely,
   letting `events._lookup_roster_entry()` match by `--issue`/`-C repo`
   alone and auto-select the single live match -- the fallback
   `spawn.py watch`'s own usage text documents `--session` as optional
   for.
   derived: `python3 -m pytest tests/test_issue_3245_pair_results.py
   tests/test_consumer_path_trust_root.py -q` -- result:
   ```
   36 passed in 0.86s
   ```
8. Re-dispatched pair `01-study-groups` with this fix (in progress at
   the time this section was written; see "Next steps").

## Why

canonical: `docs/issue-3245/reports/independent-verification-1.md`
(merged via PR #3253, `gh pr view 3253 --json state` result:
`"state":"MERGED"`, this session), this session's own live reproduction
cited in "What was done" §2

Round 1's report named an environment-wide CLI/hook regression as the
blocker and said this session had no path to a different CLI version.
Independent-verification-1 falsified the "blocks every dispatch on this
machine right now" half of that claim directly and traced the actual
failure to the fresh, credential-less HOME `prepare_arms.py` builds per
arm. Left standing, that diagnosis would send the next session looking
for a CLI update that was never the actual blocker.

The fix has to respect PR #3185's own design constraint: trust-root
isolation must be launcher-owned and outside the session's reach, closing
two live-reproduced forgeability findings from PR #3180. The resolution
taken: HOME isolation stays exactly as PR #3185 designed it (fresh per
arm, off arm's skills root never created, `verify_manipulation.py`'s
cross-check on `HOME`/`MUSTER_SKILL_REPO` unchanged); the only addition
is seeding an identical, launcher-owned credential copy into both arms
before dispatch. This is safe because skill reachability (the
manipulated variable) is controlled by the `--plugin-dir` argv flag
(built from `MUSTER_SKILL_REPO`), never by anything under `HOME` --
canonical: `pipeline.py` lines 486-512 (`core_plugin_dirs`), read this
session, comment "마켓플레이스 설치가 아니라 --plugin-dir 로 붙인다."
The credential is byte-identical across arms, added by the same launcher
call before dispatch, so it cannot become a distinguishing or forgeable
signal, and it touches no field `verify_manipulation.py` checks.

Placed in `run_pair.py` rather than `prepare_arms.py`: `prepare_arms.py`
is PR #3185's already-shipped module, reused unmodified by design
(canonical: `docs/issue-3183/reports/experiment-trust+implementation-blueprint+silent-failure-audit-ab4333e5.md`
frontmatter, read this session); the credential need only exists because
`run_pair.py` is the module that actually dispatches real sessions.

## Upstream basis

canonical: `gh pr view 3253 --json state,mergeCommit` (this session) --
result `"state":"MERGED"`; this session's own `Read` of the files below

- `docs/issue-3245/reports/independent-verification-1.md` (PR #3253) --
  its resolution-path recommendation ("seeding each arm's isolated HOME
  with read-only Claude Code credentials... while keeping every other
  isolation guarantee intact") is what `seed_arm_credentials()`
  implements.
- `docs/issue-3183/reports/experiment-trust+implementation-blueprint+silent-failure-audit-ab4333e5.md`
  (PR #3185) -- design rationale this fix must not violate.
- `scripts/consumer-path/prepare_arms.py`, `verify_manipulation.py` --
  read to confirm the manipulation check cross-references only `HOME`
  and `MUSTER_SKILL_REPO` (`verify_manipulation.py`'s `cross_check()`,
  read this session).
- `pipeline.py` lines 486-512 (`core_plugin_dirs`) -- confirms skill
  reachability is gated by `--plugin-dir`, not by anything under `HOME`.
- `docs/issue-3245/_assets/01-study-groups/result.json` -- both this
  round's dispatch attempts, read this session.
- `docs/issue-3245/decisions/pinning-and-sample-size.md`,
  `drafted-followup-issues.md` -- this run's registered ceiling (n=2
  reachable) and the six drafted, not-filed follow-up issues.

## What did not work

See "What was done" §6 for the first post-credential-fix dispatch
attempt's `watch`/cleanup-race failure, fixed in §7. Further entries
pending until pair dispatches finish this session.

## Open findings

1. Residual, not fixed this round: `run_pair()` calls
   `prepare_arms._cleanup()` immediately after `execute_arm()` returns
   regardless of status, including `"watch-timed-out"`. If a real
   session genuinely exceeds `watch_timeout_s` (1800s default) for a
   legitimate reason, cleanup would still delete that arm's still-in-use
   HOME. Not addressed this round; named for whoever runs pairs 3-5.
2. Pending: full "Reported results" table and aggregate scoring, filled
   in once this session's real dispatches finish (see "Next steps").

## Next steps

In progress at the time this section was written: pair
`01-study-groups` (issues #19/#20) re-dispatched with the `watch`-session
fix; `02-onboarding-experiment` (issues #21/#22) not yet attempted this
session. `loop_state` stays `in-progress` until both are attempted and
the record is updated with their actual results and the registered
acceptance-check output.

## Skill verdicts

- skill-verdict: silent-failure-audit — applied: invoked; audited
  `scripts/consumer-path/run_pair.py`'s new `seed_arm_credentials()` and
  its call site this session. Found the copy step unguarded and fixed it
  with `try/except OSError`, adding a regression test (see "What was
  done" §4).
  derived: `python3 -m pytest tests/test_issue_3245_pair_results.py -q`
  -- result:
  ```
  18 passed in 0.91s
  ```
- skill-verdict: experiment-trust — applied: invoked; Step 1's scope
  gate routed this measurement away from the skill's SRM/A-A procedure
  this session (pre-assigned small-n paired comparison, not random
  assignment of live traffic -- see "What was done" §5). No SRM/A-A
  claim is made; the pre-registered decision rule in
  `docs/issue-3245/decisions/pinning-and-sample-size.md` governs
  interpretation instead.
- implementation-blueprint — not-applicable: this round's code change is
  a single new function (`seed_arm_credentials()`) added to an existing,
  already-structured module, well under the multi-module/fan-out
  threshold this skill gates on.
- other mounted skills (work-in-english, adversarial-review,
  technical-feasibility-reversibility-tag, prose-modes,
  implementation-audit, technical-feasibility-verdict-and-timebox-selection):
  not triggered.
