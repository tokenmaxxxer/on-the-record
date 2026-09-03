---
issue: 3245
role: independent-verification-1
author: independent-verification-1
verifies_subject: true  # independent verification of PR #3251 (branch issue-3245/experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-7b04b22b)
loop_state: done
upstream:
  - path: scripts/consumer-path/run_pair.py (PR #3251, commit 94a785f9)
    sha: same-commit
  - path: docs/issue-3245/reports/experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-7b04b22b.md (PR #3251)
    sha: same-commit
  - path: docs/issue-3245/_assets/01-study-groups/result.json (PR #3251)
    sha: same-commit
  - path: scripts/consumer-path/prepare_arms.py (PR #3185)
    sha: same-commit
---

# issue-3245 — independent-verification-1 record

## What was done

canonical: this session's own tool transcript (checkout of PR #3251's changed
files onto this branch, three acceptance-check runs, full suite run, and a
live reproduction of `spawn.py`'s `doctor()` under both a normal and an
isolated-HOME environment)

1. Read the issue (`gh issue view 3245`) and PR #3251 (only PR referencing
   issue #3245: `gh pr list --search 3245`), then materialized PR #3251's
   changed files onto this working tree (`git checkout
   origin/issue-3245/experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-7b04b22b
   -- .`, then reverted the handful of unrelated files that checkout also
   touched due to branch divergence from main) so the acceptance checks run
   against the actual PR content, not a description of it.
2. Ran all three of the issue's registered acceptance checks against that
   tree.
   derived: `python3 -m pytest tests/test_issue_3245_pair_results.py -q`
   ```
   14 passed in 0.95s
   ```
   derived: `python3 -m pytest tests/test_consumer_path_trust_root.py -q`
   ```
   18 passed in 0.84s
   ```
   derived: `python3 scripts/consumer-path/verify_manipulation.py --report`
   ```
   {"pairs_found": 1, "pairs_included": [".../01-study-groups"],
    "pairs_excluded": [], "status": "reported"}
   ```
   exit=0
   All three match the PR's own claimed counts and exit codes.
   derived: `python3 -m pytest tests/ -q`
   ```
   571 passed, 2 warnings in 33.71s
   ```
   The PR's test plan claims 554 passed for this same command; this is a
   pre-existing count drift (other PRs landed on main between when the PR
   author ran it and this session), not a regression -- no failures either
   way, and this full-suite run is not one of the issue's three registered
   acceptance checks.
3. Read `scripts/consumer-path/run_pair.py` in full and cross-checked the
   two silent-failure-audit fixes the report claims
   (`collect_cost()`'s `skipped_malformed_lines` counter,
   `run_pair()`'s try/except around `prepare_arms.build_manifest()`)
   against the actual diff -- both are present and match the report's
   description.
   canonical: `scripts/consumer-path/run_pair.py` lines 249-276 (`collect_cost`)
   and 287-298 (`run_pair`'s try/except), read this session
4. Read the diff to `scripts/consumer-path/verify_manipulation.py` (the new
   `--report`/`find_pair_dirs()`/`report()` path) and confirmed it matches
   acceptance check 3's empty-state requirement: an empty `--root` returns
   `status: "no-manifests-found"` and exits nonzero.
   derived: `python3 scripts/consumer-path/verify_manipulation.py --report --root /tmp/empty-3245-check`
   ```
   {"status": "no-manifests-found", "pairs_found": 0, ...}
   ```
   exit=1
5. Independently re-derived the report's central causal claim rather than
   accepting the quoted stderr text at face value. The report's "Open
   finding 1" states CLI 2.1.259 does not fire plugin hooks in headless
   mode on this machine, calling it an environment-wide regression that
   blocks every `spawn.py --skills` dispatch on this machine right now.
   That claim is falsifiable in-place (`runs/doctor-ok` is a stateful,
   gitignored probe result), so it was tested directly instead of trusted.
   derived: `rm -f runs/doctor-ok && python3 spawn.py doctor` (run twice, back to back)
   ```
   UserPromptSubmit: 발화 / PreToolUse: 발화  (CLI 2.1.259 (Claude Code))
   doctor-ok 기록. 이 버전에서 스폰이 열린다.
   ```
   Both runs succeeded -- hooks fire headless on this exact machine, this
   exact CLI version, right now. This directly contradicts the "blocks
   every dispatch on this machine right now" framing.
   Reproduced the doctor probe's own internal steps
   (`spawn.py:2175-2219`, read this session) a third time, this time
   under a fresh, empty `HOME` (`tempfile.mkdtemp()`, no `~/.claude.json`
   or `~/.claude/` copied in) -- the exact condition
   `prepare_arms.py::build_manifest()` creates for every arm (`on_home =
   Path(tempfile.mkdtemp(prefix="consumer-path-on-home-"))`, `off_home`
   likewise, neither seeded with credentials).
   canonical: `scripts/consumer-path/prepare_arms.py` lines 196-206
   (`build_manifest`'s `on_home`/`off_home` construction), read this session
   derived: probe script run with `HOME=<fresh tempdir>` reproducing
   `spawn.py:doctor()`'s own steps (temp plugin, `claude -p --plugin-dir
   ... --model haiku --output-format json`)
   ```
   returncode 1
   STDOUT ... "result":"Not logged in · Please run /login" ...
   ups fired True, pre fired False
   ```
   derived: `printenv | grep -i anthropic` -- no output (no
   `ANTHROPIC_API_KEY` set on this machine as a fallback credential path)
   Under the isolated HOME, the `claude -p` subprocess fails immediately
   on missing authentication. `PreToolUse` never fires because the
   session errors out before invoking any tool; `UserPromptSubmit` fires
   because that hook runs before the login check. `doctor()`'s check
   (`fired_ups and fired_pre`) cannot distinguish "hooks are silenced by
   the CLI" from "the session never got past login" -- both present as
   `PreToolUse` not firing.
6. Read `docs/issue-3245/decisions/pinning-and-sample-size.md` and the
   deviation-log entry; both are internally consistent with the report and
   with each other, and the pre-registration-before-running discipline
   (skill pinning, n>=5 floor, stated ceiling of n<=2 reachable issues) is
   genuine -- timestamped/ordered before any dispatch, not retrofitted.
   canonical: `docs/issue-3245/decisions/pinning-and-sample-size.md`
   (`status: registered-before-any-pair-scored-under-this-run` frontmatter,
   §3's stated n<=2 ceiling) and the deviation-log file at
   `docs/issue-3245/reports/experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-7b04b22b/deviation-log/20260903T005455151220-9c195d8b5503a750.md`,
   both read this session

## Why

canonical: this session's own transcript, created this turn -- two
`spawn.py doctor` runs and one isolated-HOME probe reproduction, both
quoted in "What was done" §5

Confirming that the three registered acceptance checks succeed is a
necessary step, but is not sufficient on its own, for a report whose
entire deliverable is a causal claim (0 of the registered n>=5 pairs
scored, attributed to an external CLI regression) -- those three checks
exercise the launcher's own machinery, not that causal claim itself.
Since `runs/doctor-ok`/`spawn.py doctor` is cheap and directly
falsifiable on this same machine, reproducing it under both the reported
(isolated-HOME) condition and this session's own normal condition was
the only way to actually check the claim rather than restate it, and it
produced a different, more specific explanation (see "Open findings"
below).

## What did not work

None.

## Upstream basis

canonical: `gh pr view 3251` (title, body, commits, files, state:
MERGEABLE, read this session); this session's own `Read` of
`scripts/consumer-path/prepare_arms.py` lines 196-225 (fresh-
`tempfile.mkdtemp()` HOME construction, no credential seeding) and
`spawn.py:2175-2219` (`doctor()`)

- PR #3251 (issue-3245: R007 consumer-path pair launcher; 0/5 pairs
  scored (CLI/hook regression found)), commits `94a785f9`, `087c1dbe`,
  `16e96c75` -- the subject of this verification.
- `docs/issue-3245/reports/experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-7b04b22b.md`
  -- the PR's own record, read in full.
- `docs/issue-3245/_assets/01-study-groups/manifest.json` (untracked here --
  PR #3251's own artifact, removed from this branch's tree per board-gate
  after being read),
  `docs/issue-3245/_assets/01-study-groups/transport.json` (untracked here,
  same reason), and `docs/issue-3245/_assets/01-study-groups/result.json`
  (untracked here, same reason) -- the actual artifacts the report's
  table is drawn from, read this session.
- `scripts/consumer-path/prepare_arms.py` (PR #3185) -- the trust-root
  construction this PR builds on; its fresh-HOME-per-arm design is the
  mechanism behind finding 1 below.
- `pipeline.py:524` (`require_doctor`), `spawn.py:2175-2219` (`doctor()`)
  -- read directly to understand what the probe actually checks and why a
  login failure and a hook-silencing failure are indistinguishable to it.

## Open findings

canonical: this session's own transcript, created this turn (`spawn.py
doctor` run twice, isolated-HOME probe reproduction, both in "What was
done" §5), and `docs/issue-3245/_assets/01-study-groups/result.json`
(untracked here, same reason as "Upstream basis" above) `dispatch_stderr`
(read this session, its full text quoted verbatim in "What was done" §5)

amendments-reconciled: issuecomment-5518683506 (posted 2026-09-03T00:58:36Z
by JiwonJung94 on issue #3245, read this session via `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5518683506`) asks both
independent-verification sessions to treat the report's "CLI does not
fire plugin hooks headless" claim as the primary thing to verify.
canonical: issuecomment-5518683506's own text, quoted verbatim: "Of 24
spawned-session logs from today on this machine, 20 contain plugin hook
activity" -- a contradicting signal from the orchestrator's own side,
independent of and prior to this session reading it. This session's
finding 1 below, reached independently in "What was done" §5 before this
comment was read, answers the comment's request: not "hooks generally
fire fine so the report is simply wrong," but the specific mechanism --
the fresh, credential-less `HOME` `prepare_arms.py` builds per arm makes
`claude -p` fail to authenticate, which `doctor()`'s coarse `fired_ups
and fired_pre` check cannot distinguish from genuine hook silence.

1. **The report's "environment-wide CLI/hook regression" diagnosis (its
   own Open finding 1) is very likely a misdiagnosis of a credential-
   isolation gap in `prepare_arms.py`, not a CLI defect.** Reproduced live
   (see "What was done" §5): `spawn.py doctor` succeeds twice in a row
   under this session's normal environment on the identical CLI version
   (2.1.259) the PR's session used, directly contradicting "blocks every
   `spawn.py --skills` dispatch on this machine right now." Reproducing
   the doctor probe's internals under a fresh, empty `HOME` (the exact
   condition `prepare_arms.py` constructs for both arms) instead fails
   with `"Not logged in · Please run /login"` -- an authentication gap,
   not a hook-firing regression. `doctor()`'s `fired_ups and fired_pre`
   check cannot tell these two failure modes apart, so its stderr message
   (훅이 headless 에서 발화하지 않는다) is misleading in this specific
   case, and the PR's report took that message at face value rather than
   inspecting the underlying `claude -p` subprocess output (which
   `doctor()` itself never surfaces on failure -- a second, smaller
   silent-failure gap in already-landed code, outside this PR's own diff,
   that this PR's silent-failure-audit scope skipped, since that audit
   covered only its own new code in `run_pair.py` rather than the
   pre-existing `doctor()` it called into).
   Practical consequence: the report's stated next step ("this session has
   no path to a different CLI version") is likely the wrong fix. The more
   plausible fix is inside this project's own reach -- seeding each arm's
   isolated `HOME` with read-only Claude Code credentials (or an
   `ANTHROPIC_API_KEY` override) while keeping every other isolation
   guarantee (`MUSTER_SKILL_REPO`, skills-root absence for the off arm)
   intact -- not an external wait. This does not change the PR's reported
   result count itself (acceptance check 3 above shows `pairs_found: 1`,
   matching the report's own single attempted pair, and `result.json`'s
   `excluded_from_h2: true` is accurate either way), but the *reason*
   given for finding 1, and the resulting triage priority, should be
   revisited before anyone waits on a CLI update that may not be the
   actual blocker.
   Resolution path: whoever picks up pairs 2-5 should first re-run
   `01-study-groups` after seeding arm credentials (or confirm
   independently that a properly-authenticated fresh-HOME session still
   fails the same way, which would restore the original CLI-regression
   theory) before spending further real dispatches.
2. Carried forward from the PR's own report, independently confirmed
   accurate and not superseded by finding 1 above: issues #19/#20's
   `## Acceptance` sections lack the `provenance:`/`empty state:` lines
   `on-the-record/directive/acceptance-format.md` requires (visible
   verbatim in `result.json`'s `dispatch_stderr`, quoted above -- a
   separate warning from the doctor failure) -- this session cannot edit
   them either (`gh-guard` applies to this session's own `CLAUDE_SKILL`
   the same way it applied to the PR's), named for the human/orchestrator
   to fix.
3. Carried forward, confirmed accurate against
   `docs/issue-3245/decisions/drafted-followup-issues.md` (read this
   session): six follow-up issues (pairs 3-5) are drafted but not filed,
   and the registered n>=5 floor is unmet at 0 scored this run -- both
   correctly and honestly reported by the PR, no correction needed on
   either.
4. The PR's acceptance-check must-not (no pair reported as scored without
   a passing manipulation check) holds trivially and correctly: no pair is
   reported as scored at all this run, verified directly against
   `result.json`'s own `excluded_from_h2: true` field, quoted above.

## Next steps

acceptance: `python3 -m pytest tests/test_issue_3245_pair_results.py -q` -- result:
```
14 passed in 0.95s
```
acceptance: `python3 -m pytest tests/test_consumer_path_trust_root.py -q` -- result:
```
18 passed in 0.84s
```
acceptance: `python3 scripts/consumer-path/verify_manipulation.py --report` -- result:
```
{"pairs_found": 1, "pairs_excluded": [], "status": "reported"}
```
(exit 0)

All three registered acceptance checks succeed against PR #3251's tree, so
`loop_state` is set to the terminal value `done` for this record. Remaining
action belongs to whoever picks up pairs 2-5 or triages finding 1 above:
re-attempt `01-study-groups` with a credentialed isolated HOME before
accepting the CLI-regression theory as the blocker, per finding 1's
resolution path.

## Skill verdicts

- skill-verdict: work-in-english — applied: invoked; wrote this record's
  exhaust (headings, citations, findings) in English per the skill,
  reserving Korean for the end-of-turn summary to the user.
- other mounted skills: not triggered.
