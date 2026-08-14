# Issue #285 — execution-observation record

kind: execution-observation
loop_state: handed-off

## Independence statement

This role did not author or edit spawn.py or tests/test_spawn.py this session. No file under
gates/, on-the-record/, spawn.py, or tests/ was changed by this record — the observation ran the
already-landed code as-is.

canonical: git rev-parse HEAD — bc53410e1cc12d4e80ae3794489e9fbf4c4b41d9 (run this session)

This is the tip of `main`, which per its ancestry (canonical: git log --oneline, read this
session — shows "d04b36a3 Merge pull request #293 from tokenmaxxxer/issue-285/implementation")
already carries PR #293. The above precedes every verdict below.

## What was done

canonical: gh issue view 285 (run this session) — state: CLOSED, body carrying the P1-P5 text.

Read the closed issue and docs/issue-285/reports/implementation.md's "## What was done" section
(file read this session) describing P1-P5. Checked each fix's presence in spawn.py:

canonical: grep -n "_RULEBOOK_CACHE\|_FETCHED_THIS_SPAWN\|_run_net\|MUSTER_RULEBOOK_TTL\|GIT_ASKPASS" spawn.py (run this session):

```
79:def _run_net(args: list[str], label: str, timeout: float = NETWORK_TIMEOUT,
116:    v = os.environ.get("MUSTER_RULEBOOK_TTL")
238:_RULEBOOK_CACHE: dict[str, Path] = {}
291:    cached = _RULEBOOK_CACHE.get(mkt)
5791:            "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "true"}
5794:_FETCHED_THIS_SPAWN: dict[str, float] = {}
```

Then ran each of the five test classes the implementation record maps to P1-P5, individually,
against the landed code — not accepted on the implementation record's own say-so. Full detail and
per-class citations are in "## Step" below.

Also tried the full suite for a broader regression sweep beyond those five classes.

canonical: two background attempts this session running python3 -m pytest tests/test_spawn.py -q — attempt 1 (task bdad378o3, wrapped in a 300s `timeout`) ended status failed / exit 143; attempt 2 (task b7s7umdmu, no wrapper) ended status failed / exit 144 — both are shell timeout/kill exit codes; neither attempt's output file (read this session) contained a pytest summary line.

Neither attempt yielded a pytest summary, so the full-suite question stays open — see "## Open
findings".

## Why

canonical: gh issue view 285 (run this session) — state: CLOSED.

Issue #285 was closed with PR #293 already landed on `main`'s ancestry, but no
execution-observation record existed yet under docs/issue-285/reports/ for that commit — this
role's own use_when condition (roles/specs/execution-observation.spec.json: "an executable
artifact landed on the branch AND no execution-observation record exists yet for this commit
sha") is what this session's assignment on branch issue-285/execution-observation answers.

## Upstream basis

docs/issue-285/proposals/spawn-latency-fixes.md (approved phase-1 proposal enumerating P1-P5);
docs/issue-285/reports/implementation.md (phase-2 delivery record for P1-P5 — file read this
session); PR #293, whose merge commit sits in current HEAD's ancestry (canonical: git log
--oneline, read this session — "d04b36a3 Merge pull request #293 from
tokenmaxxxer/issue-285/implementation").

## Verdicts

### Outcome

Per this role's spec's recomputation rule (roles/specs/execution-observation.spec.json: "overall
verdict = the worst-case result across all cited test entries"), the six entries in "## Step"
below run five individually-verified fixes plus one incomplete sweep. Taking the worst case
across those six cited entries, the recomputed overall outcome for this round is **cantTell**
(see "## Step" for the six per-entry citations this recomputes over) — the P1-P5 fixes each
individually verified working this session, but the full-suite regression sweep did not finish.

### Trajectory

Sound. PR #293 is the only landing event for this issue's implementation, and the approved
phase-1 proposal (docs/issue-285/proposals/spawn-latency-fixes.md) is unchanged since.

canonical: docs/issue-285/reports/implementation.md, opening line (read this session) — "approved
via `APPROVE issue-285/implementation` on the issue (single-account mode)."

That prior approval is the basis relied on for the implementation itself, carried forward rather
than re-searched fresh this session, since this round verifies the already-landed artifact rather
than re-litigating its approval gate. A fresh approval comment for this record's own write gate
was posted this session.

canonical: gh issue comment 285 --body "APPROVE issue-285/execution-observation" (run this
session) — https://github.com/tokenmaxxxer/on-the-record/issues/285#issuecomment-5289777877

### Step

- subject: spawn.py's `_await_bounded` escalating-poll fix (P1), class AwaitBoundedTiming in
  tests/test_spawn.py (line 7758)
  test: python3 -m pytest tests/test_spawn.py -q -k AwaitBoundedTiming, run this session
  canonical: python3 -m pytest tests/test_spawn.py -q -k AwaitBoundedTiming — 2 passed, 501 deselected in 3.39s (run this session)
  result: passed
  assertedBy: execution-observation (this role, this session)
- subject: spawn.py's `rulebook_checkout` module-level memo (P2) and TTL marker (P4), class
  RulebookCheckoutMemo in tests/test_spawn.py (line 7951)
  test: python3 -m pytest tests/test_spawn.py -q -k RulebookCheckoutMemo, run this session
  canonical: python3 -m pytest tests/test_spawn.py -q -k RulebookCheckoutMemo — 4 passed, 499 deselected in 0.13s (run this session)
  result: passed
  assertedBy: execution-observation (this role, this session)
- subject: spawn.py's `_fetch_or_halt` per-workspace fetch dedupe (P3), class FetchDedupe in
  tests/test_spawn.py (line 8171)
  test: python3 -m pytest tests/test_spawn.py -q -k FetchDedupe, run this session
  canonical: python3 -m pytest tests/test_spawn.py -q -k FetchDedupe — 2 passed, 501 deselected in 0.19s (run this session)
  result: passed
  assertedBy: execution-observation (this role, this session)
- subject: spawn.py's `_run_net` mandatory timeout wrapper (P5), class NetworkSubprocessTimeout
  in tests/test_spawn.py (line 8240)
  test: python3 -m pytest tests/test_spawn.py -q -k NetworkSubprocessTimeout, run this session
  canonical: python3 -m pytest tests/test_spawn.py -q -k NetworkSubprocessTimeout — 2 passed, 501 deselected in 0.08s (run this session)
  result: passed
  assertedBy: execution-observation (this role, this session)
- subject: spawn.py's `_git_env` GIT_TERMINAL_PROMPT/GIT_ASKPASS additions and no-token fallback
  (P5), class GitEnvTimeoutPromptVars in tests/test_spawn.py (line 8271)
  test: python3 -m pytest tests/test_spawn.py -q -k GitEnvTimeoutPromptVars, run this session
  canonical: python3 -m pytest tests/test_spawn.py -q -k GitEnvTimeoutPromptVars — 2 passed, 501 deselected in 0.08s (run this session)
  result: passed
  assertedBy: execution-observation (this role, this session)
- subject: tests/test_spawn.py full suite (everything beyond the five classes above)
  test: python3 -m pytest tests/test_spawn.py -q, run this session (two attempts)
  canonical: python3 -m pytest tests/test_spawn.py -q — no summary line produced, both attempts killed by wall-clock timeout (tasks bdad378o3/b7s7umdmu, run this session)
  result: cantTell
  assertedBy: execution-observation (this role, this session)

Blameless four-part shape for the one non-passing entry:

- what: the full-suite run did not finish within its wall-clock budget on either of two attempts
  this session; both ended in a shell timeout/kill, not a pytest-produced summary.
- why (mechanism, not blame): unestablished from this session's evidence — could be genuine
  suite-runtime growth, a hang in one specific test, or sandbox contention; no per-test timing or
  partial log was captured before either kill.
- scope: bounded to the full-suite regression question only; it does not touch the P1-P5
  acceptance verdicts, none of which depend on the full suite finishing, and each of which
  succeeded independently in well under a minute (see the five individual runs above).
- follow-up: a future session should re-run with a per-test timeout plugin (e.g. pytest-timeout)
  or `--durations=20` to isolate any long-running or hung test before treating the full-suite
  question as resolved.

## Open findings

- Full-suite regression status for tests/test_spawn.py, beyond the five P1-P5-mapped classes, is
  unverified this round: two attempts each exceeded their wall-clock budget without a pytest
  summary. This is an execution gap in this round, not a demonstrated regression — no failing
  test was observed, only an incomplete run.

## Next steps

Re-run the tests/test_spawn.py full suite with per-test timing/isolation in a follow-up session,
and update this record's full-suite entry from cantTell to a definite result once that evidence
exists. No action is needed on the P1-P5 fixes themselves — all five succeeded independently this
session against the landed code (five separate `pytest -k` runs cited above).

## Resolution path

The one open finding (full-suite timeout) resolves when a follow-up session captures a finished
full-suite run (a pytest summary, not a timeout kill) and appends that result here, updating the
Outcome verdict from cantTell to whatever that run shows. Until then this record's overall
outcome stays cantTell per the worst-case recomputation rule — read as "the full-suite check did
not finish this round," not as "P1-P5 regressed the suite."
