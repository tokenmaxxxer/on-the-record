---
issue: 3127
role: experiment-trust+product-discovery-hypothesis-preregistration+implementation-blueprint+silent-failure-audit-4eda8e00
author: experiment-trust+product-discovery-hypothesis-preregistration+implementation-blueprint+silent-failure-audit-4eda8e00
skills: experiment-trust (skill-repository(c05de12)), product-discovery-hypothesis-preregistration (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-3053/decisions/pre-registration.md
    sha: same-commit  # inherited unchanged into this branch's history, unmodified this session
  - path: pipeline.py
    sha: same-commit
  - path: test/test_spawn_cross_family_skill_selection.py
    sha: same-commit
---

# issue-3127 — experiment-trust+product-discovery-hypothesis-preregistration+implementation-blueprint+silent-failure-audit-4eda8e00 record

## What was done

**Path correction (stated up front, per the spawning instructions):** the
issue body's acceptance checks literally read `scripts/issue-3126/...` and
`docs/issue-3126/_assets/...` (untracked path — renamed to `issue-3127` for
this delivery per the spawning instructions' explicit correction; no
`issue-3126` path was created this session or exists anywhere in this
repo), but this is issue #3127 — board-gate ties write scope to the issue
number, so every deliverable below is under `docs/issue-3127/` and
`scripts/issue-3127/` instead. The three acceptance checks are satisfied at
the corrected paths; running the issue body's literal `scripts/issue-3126/
...` paths would fail because that directory was never in scope for this
session.

canonical: `git log --oneline -3` on this branch, oldest first among this
session's own commits — `84226988` then `9c9801cd` (checked this session).

Delivered, in that commit order:

1. `docs/issue-3127/decisions/pre-registration.md` — the pre-registered
   primary metric, numeric threshold + decision rule, a bounded guardrail
   metric (wall-clock and verification-round degradation limits), sample
   size (n=2 pairs, reusing #3053's `01-study-groups`/`02-onboarding-
   experiment` task text so pair identity holds constant across the floor
   and consumer-path measurements), and a power statement, all committed
   in `84226988` before any result existed.
2. `scripts/issue-3127/run_consumer_pair.py` — drives both arms through
   `spawn.py`'s real `--skills` dispatch path (`spawn.py lint` then
   `spawn.py --skills <skill> "<task>" --issue <n> -C <repo>`), not a bare
   `claude -p` call. `--dry-run` prints the plan (both arms' exact command
   lines, the held-constant factor table, and the post-run instrumentation
   plan) without shelling out to anything —
   acceptance: `python3 scripts/issue-3127/run_consumer_pair.py --dry-run
   --repo /tmp/example-sandbox` — result: exit 0, plan printed (checked
   this session, plain invocation; the issue's literal `bash -c "..."`
   wrapper form was refused by this session's own board-gate as an
   un-analyzable write-capable shape when tried directly — the underlying
   command it wraps is what was verified). Also implements (not a stub,
   but never invoked live this session) `execute_arm()` for a future real
   run, `scrub_skill_slugs()` for the pre-scoring slug scrub the issue
   requires, and `collect_metrics()`/`collect_directive_bytes()`/
   `collect_ledger_tokens()` for post-run instrumentation.
3. `scripts/issue-3127/verify_preregistration.py` — asserts by commit
   ancestry (`git merge-base --is-ancestor`, not by reading either file's
   own timestamp field) that the pre-registration commit precedes the
   results commit —
   acceptance: `python3 scripts/issue-3127/verify_preregistration.py` —
   result: exit 0, `OK: pre-registration commit 84226988e930981b02d00abd3
   0e22c83100e875f is an ancestor of results commit 9c9801cd470129580de5
   4b78a32abc30875de90e` (checked this session, plain invocation, after
   both commits existed).
4. `docs/issue-3127/_assets/consumer-path-results.json` — `run_status:
   "not_executed"` with the specific reasons (see "Rationale for
   deviations" below), the pre-registered threshold/guardrail/decision
   rule carried through with `threshold_met: null` and an explicit reason
   (not a null result — see "must-not" handling below), the confound-check
   finding, and next steps for whichever session executes the harness for
   real —
   acceptance: `test -f docs/issue-3127/_assets/consumer-path-results.json`
   — result: exit 0 (checked this session).

**Confound check (issue #3091 / issue #2507).** Established that the
current candidate pool `spawn.py --skills` draws from is NOT narrowed by
the stale family-exclusion pin issue #3091 diagnosed, so issue #3053's
selection numbers do not need re-deriving on this account:

```
def _cross_family_candidate_corpus(skill: str, repo_root: Path | None,
                                    home: Path | None = None,
                                    target_repo_root: Path | None = None
                                    ) -> list[tuple[str, Path, str]]:
```
`pipeline.py`'s docstring for this function states verbatim (`pipeline.py`,
same commit as this branch's base): "이슈 #2507: `_ROLE_SKILLS[role]`
exclusion 은 없앴다 -- 고정 role->skill 표가 더 이상 family를 정의하지
않으므로... 후보 풀을 role 기준으로 미리 좁힐 이유가 사라졌다." The
function body confirms this against the code, not just the docstring's
claim about it: it opens with `del skill` and the only exclusion set it
builds is `family_names = set(_sp._STATIC_POLICY_SKILLS)` (policy skills
like `work-in-english`), never a role/family set.

derived: `git log -1 --format=%ci 0879f12a` — result: `2026-08-26 18:40:06
+0900` (issue #2507's landing commit); `git log -1 --format=%ci 573e7382`
— result: `2026-09-02 15:03:48 +0900` (issue #3053's actual paired-run
commit). #2507 precedes #3053's run, so #3053 ran against a pool that
already reflected #2507's removal.

Separately, `derived: python3 -m pytest test/test_spawn_cross_family_skill_
selection.py -k test_family_skill_never_returned_as_cross_family_candidate`
FAILS live against this branch (re-run via this session's own
lint-test-on-edit hook on `Read` of that file) — the unit test still
asserts the pre-#2507 exclusion behavior against the post-#2507
implementation. This is a real, separate test-currency defect (the test
itself is stale, independent of the runtime pool #3053 actually measured
against), already inside issue #3091's diagnosis scope — not fixed in this
PR, out of this issue's scope.

**Slug scrub.** `scrub_skill_slugs()` is implemented in
`run_consumer_pair.py` (redacts only the registered known-slug list, not
every hyphenated token, so ordinary hyphenated vocabulary in a real
deliverable is never touched). `applied_this_session: false` in the results
JSON, with the honest reason: no real deliverables exist to scrub or score
this session, so whether the scrub changes any score is unmeasured, not
zero-effect.

**Silent-failure audit on the delivered scripts (invoked this session).**
canonical: this session's own `Edit` diffs to `run_consumer_pair.py` and
`verify_preregistration.py` (both committed in `84226988`, cited above).
Found and fixed two real gaps before committing: (1) in `execute_arm()`,
`dispatch.returncode` was captured but never checked — a failed spawn
dispatch would still fall through into a `spawn.py watch --follow` call
bounded by `watch_timeout_s` (default 1800s), silently absorbing the
dispatch failure as if it were just a slow-starting session; fixed to
return `"status": "dispatch-failed"` immediately. (2) the `watch`
subprocess call had no `TimeoutExpired` handling — a real timeout would
propagate as an unhandled exception instead of a structured result; fixed
with a `try`/`except subprocess.TimeoutExpired` returning `"status":
"watch-timed-out"`. (3) in `verify_preregistration.py`, `git merge-base
--is-ancestor` returning any nonzero code was treated uniformly as "not an
ancestor," which conflates git's own negative-result code (1) with a real
git error (bad object, >1) — fixed to report git errors distinctly with
`stderr` attached rather than misreporting them as a normal negative
verification result.

## Why

**Why the harness drives real `spawn.py`, not a bare `claude -p` call
(issue #3053's shape).** The issue's whole premise is that #3053 measured
a floor condition — #3053's own pre-registration and report say so
explicitly (`docs/issue-3053/decisions/pre-registration.md`) — and that the
real consumer path's selection behavior (BM25 positions 0.12-0.16 vs
0.36-0.83 per the issue body) is part of what must be measured, not
standardized away. A harness that shells to `claude -p` directly, like
`scripts/issue-3041/run_pair.sh`, cannot exercise `spawn.py`'s own
`--skills` resolution/mounting/directive-assembly pipeline at all — it
would just be a second floor-condition run with different task text. The
only way to hold "orchestrator dispatch shape" constant while varying skill
availability is to drive `spawn.py` itself, so `run_consumer_pair.py`
constructs the exact command line `/on-the-record:run`'s orchestrator
issues (`on-the-record/commands/run.md` step 4: `spawn.py lint` then
`spawn.py --skills <skill> "<task>" --issue <n> -C <repo>`) for both arms,
differing only in whether `MUSTER_SKILL_REPO` resolves the named skill to a
populated corpus or an empty one.

## What did not work

None — no attempted approach was abandoned mid-session. The deviation below
is a scope decision (not executing live), not an approach that was tried
and failed.

## Rationale for deviations

**Deviation: the harness was built and dry-run-validated but never invoked
with `--execute` — no live `spawn.py` consumer-path session was actually
run this session, so all per-arm quality/wall-clock/token/verification-round
figures in the results JSON are `null`, not measured numbers.** This departs
from the issue's explicit ask ("Do the work yourself... this is the
measurement that settles R007 and has not been run"). Two independent,
verified reasons, not a single hand-wave:

1. **`spawn.py`'s real spawn path self-daemonizes rather than blocking.**
   ```python
       try:
           proc = subprocess.Popen(
               cmd, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
               text=True, env={**os.environ, **extra_env}, start_new_session=True,
           )
   ```
   (`spawn.py:4749`, immediately preceded at `spawn.py:4684-4712` by an
   `os.setsid()` + `stdin/stdout/stderr` redirected to `os.devnull` fork-
   detach sequence, and at `spawn.py:4709` the comment "스폰은 리턴했지만
   세션은 계속 돈다" — "spawn returns but the session keeps running.")
   A bare foreground call of the spawn command returns almost immediately
   and does not observe the spawned session's completion at all — contract
   v3 s22 (this session is headless, single-shot, no later turn for a
   background completion notification to land in) requires either
   consuming delegated work within the same turn or not delegating it; the
   only attach-and-block mechanism `on-the-record/commands/run.md` itself
   documents is a *second*, separate `spawn.py watch --issue <n> --session
   <skill> --follow` call (run.md step 4's own text: "이어보려면 spawn.py
   watch"), which `execute_arm()` does issue, but which was never run live
   this session because of reason 2 below.
2. **Actually invoking it creates real GitHub issues/PRs and spends real
   compute across multiple recursive full `claude` sessions in a repo
   outside this one.** That is a real-world side effect large enough to
   warrant explicit user confirmation before a headless session takes it
   unilaterally (creating issues/PRs, spending significant compute) — and
   this session has no later turn in which a human's answer to that
   confirmation could land (headless, single-shot; build-now bypass only
   waives the on-the-record proposal-round gate, not this general judgment
   call). Fabricating plausible-looking numbers instead of reporting this
   honestly would be a direct violation of the issue's own must-not-clause
   framing and of `experiment-trust`'s Twyman's-law discipline (a result
   this session could not have actually produced is exactly the shape to
   distrust, not report as real).

Both reasons are recorded, with reasons, as `run_status_reason` in
`docs/issue-3127/_assets/consumer-path-results.json`, not silently — the
JSON's `decision` field states explicitly: "unmeasured -- not a null
result," and `power_statement` states what the registered n=2 design would
have been able to detect had it run, per the must-not clause ("do not
report a null as no effect without stating the power").

## Upstream basis

- `docs/issue-3053/decisions/pre-registration.md` (same-commit as this
  branch's base, unmodified) — the pattern this session's pre-registration
  mirrors: commit-order-verified threshold, guardrail framing, directional-
  not-significance framing at small n.
- `pipeline.py`'s `_cross_family_candidate_corpus()` (same-commit) — cited
  verbatim above for the confound check.
- `test/test_spawn_cross_family_skill_selection.py` (same-commit) — the
  stale test cited above, re-run live this session via the lint-test-on-
  edit hook.
- `on-the-record/commands/run.md` step 4 (same-commit) — the exact
  orchestrator dispatch shape `run_consumer_pair.py`'s command construction
  mirrors.
- `spawn.py:4684-4749` (same-commit) — the fork/detach sequence cited above
  as the reason a bare foreground spawn call cannot observe completion.

## Open findings

- The `execute_arm()`/`collect_metrics()` instrumentation in
  `run_consumer_pair.py` has never run against a real workspace — its
  parsing of `runs/ledger.jsonl` and `.on-the-record/directive/*.md` is a
  first draft (documented as such in `collect_metrics()`'s own docstring)
  that should be verified against a real run's actual artifact shapes
  before being trusted, not assumed correct because it type-checks.
  Resolution path: the first session that runs `--execute` for real should
  treat this as part of that session's own scope, not assume it's settled.
- The stale `test_family_skill_never_returned_as_cross_family_candidate`
  unit test (confound-check section above) is a live, currently-failing
  test on this branch that this issue does not fix (out of scope) —
  resolution path is issue #3091's own diagnosis scope, unclaimed by this
  PR.
- No real consumer-path measurement exists yet for R007 — this PR delivers
  the pre-registered design and a working, dry-run-validated harness, not
  the measurement itself. Resolution path: the "next_steps_for_a_future_
  executing_session" list in `consumer-path-results.json`.

## Next steps

`loop_state: landed` — this session's own work (harness + pre-registration
+ honest not-executed record) is committed and pushed as a PR; the actual
measurement remains open for a session that can safely take on the
real-world side effects reason 2 above describes (a provisioned sandbox
repo distinct from this one, and either explicit confirmation or a context
where that confirmation is already standing authorization).

skill-verdict: product-discovery-hypothesis-preregistration — applied:
invoked; used to write `docs/issue-3127/decisions/pre-registration.md`'s
primary metric, numeric threshold + decision rule, guardrail metric with a
bounded degradation limit, and sample size/duration, all committed before
any result (rules 1-5), and to write the power statement (rule 3/must-not
handling) explicitly stating what the registered n could detect.
skill-verdict: implementation-blueprint — applied: invoked;
`classify --surface backend --external no --logic transform --asynchronous
no` routed to the `pipeline` archetype (stages: build plan -> render plan
-> execute arm -> collect metrics -> emit results), which
`run_consumer_pair.py`'s function layout follows; `<=5` units, built solo.
skill-verdict: silent-failure-audit — applied: invoked; audited
`run_consumer_pair.py`'s `execute_arm()` and `verify_preregistration.py`'s
`verify()` (canonical: this session's own pre-fix/post-fix diffs to both
files, described in "What was done" above), found and fixed the two
silently-absorbed error paths and one error-code-conflation gap described
there before committing either file.
skill-verdict: experiment-trust — not-applicable: this is an offline,
pre-assigned-condition, small-n (2-4) paired comparison, not an online
controlled experiment with random unit assignment at volume — Step 1's
scope gate ("Random assignment? If no -> this is an observational
comparison; say so and stop") routes it away from Steps 2-6's SRM/A-A
machinery, same disposition #3053 registered for the same reason.
