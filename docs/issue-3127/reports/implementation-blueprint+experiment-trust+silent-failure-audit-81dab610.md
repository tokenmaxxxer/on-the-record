---
issue: 3127
role: implementation-blueprint+experiment-trust+silent-failure-audit-81dab610
author: implementation-blueprint+experiment-trust+silent-failure-audit-81dab610
skills: implementation-blueprint (skill-repository(c05de12)), experiment-trust (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: terminal
code_under_review: scripts/issue-3127/run_consumer_pair.py
type: fix
breaking: false
verdict: H1 re-operationalized from directive_composition_bytes (construct-invalid per PR #3172's live evidence) to collect_skill_invocation(), which parses <workspace>.session.*.log for a real Skill tool_use call naming the target skill; verified against PR #3172's two real skills-on session logs (issues #19, #21) -- both correctly detected as invoked=true. No skills-off arm has produced data and no pair has been scored under either the old or new H1; decision rule, threshold, guardrail, and sample size are unchanged.
upstream:
  - path: docs/issue-3127/decisions/pre-registration.md
    sha: same-commit
  - path: scripts/issue-3127/run_consumer_pair.py
    sha: same-commit
  - path: PR #3172 (tokenmaxxxer/on-the-record, branch issue-3127/experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-e794089c, not merged, not an ancestor of this branch)
    sha: 570205e4d3e0921ef2892ea87a2659b142f90dc7
---

# issue-3127 — implementation-blueprint+experiment-trust+silent-failure-audit-81dab610 record

## What was done

canonical: this session's own live command transcript below.

Re-operationalized H1 (issue #3127's manipulation-check gate) per consult
(`experiment-trust`, `runs/consult-logs/20260902T125610799701-948846.log`)
after PR #3172 found, with live evidence from two real skills-on runs,
that H1's original proxy (`directive_composition_bytes`) has a
construct-validity gap for skills delivered via the runtime Skill tool.

1. derived: `gh pr view 3172` — result: state OPEN, title naming the
   construct-validity finding. derived: `git fetch origin
   issue-3127/experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-e794089c:pr-3172-ref`
   then `git show pr-3172-ref:docs/issue-3127/_assets/consumer-path-results.json`
   — result: `construct_validity_note_on_h1_metric` field present, stating
   both real skills-on workspaces (study-companion issues #19, #21) held
   only the 8 session-universal baseline policy files in
   `.on-the-record/directive/`, byte-identical (13026 bytes) regardless
   of which skill was mounted -- PR #3172 not merged to main and not an
   ancestor of this branch, read via `git fetch`/`git show` only.

2. Compared four candidate non-model-writable artifacts named in the
   consult (transcript tool_use entries, PostToolUse hook trace,
   `runs/ledger.jsonl`, spawn.py's mounted-skill registration) for
   forgeability -- full table in `docs/issue-3127/decisions/
   pre-registration.md`'s 2026-09-02 amendment. Delegated the
   codebase-location part of this comparison to an Explore subagent
   rather than performing the same greps serially myself.
   derived: subagent report (this session, read directly, not summarized
   further) — result: no PostToolUse hook fires on the Skill tool
   (`on-the-record/hooks/hooks.json` matchers are `Write|Edit|MultiEdit|
   Bash` only); `runs/ledger.jsonl`'s session-end entry is written by
   `plumbing.ledger_write()` from the orchestrator/parent process after
   `proc.wait()` returns, to a path outside the spawned session's own
   workspace, current schema has no per-invocation skill field; the
   roster entry (`_skill_roster_fields()`) is written pre-session but
   records only availability, never invocation.
   derived: `grep -n "bypassPermissions\|sandbox\|docker\|chroot\|setsid" spawn.py`
   — result: no per-session filesystem sandbox (no container/chroot) in
   spawn.py's dispatch path -- a spawned session runs unsandboxed, as
   the same OS user.
   derived: `ls ~/.tokenmaxxxer/work/ | grep study-companion-issue-19`
   and the issue-21 equivalent — result: both real session logs still
   present on this machine; `scripts/measure_skill_invocation.py`
   already parses `<workspace>.session.<ts>.<pid>.log` (spawn.py's own
   capture of the spawned CLI's raw stdout) for exactly this signal, in
   production use today, not new instrumentation.

3. Picked `collect_skill_invocation()` (new function, `scripts/
   issue-3127/run_consumer_pair.py`) reusing `measure_skill_invocation.
   analyze()`. Rewired `compute_h1_manipulation()` to gate `differs` on
   invocation (on arm invoked AND off arm did not), demoted
   `directive_composition_bytes` to a secondary `directive_bytes_parity`
   diagnostic field that never gates. Threaded `skill_name` through
   `gate_pair_on_h1()` and `run_pair()`.
   derived: `python3 scripts/issue-3127/run_consumer_pair.py --dry-run`
   — result: exit 0; plan text updated to describe the invocation-based
   manipulation check and the bytes-as-diagnostic-only note.

4. Verified the new manipulation check against PR #3172's real data:
   derived: `python3 scripts/measure_skill_invocation.py
   ~/.tokenmaxxxer/work/study-companion-issue-19-product-discovery-hypothesis-preregistration-f8df81f9.session.20260902T212053.797342.log
   ~/.tokenmaxxxer/work/study-companion-issue-21-product-discovery-hypothesis-preregistration-dbeb1ea3.session.20260902T213536.864722.log`
   — result: both real session logs report `"invoked_skills": [...,
   "product-discovery-hypothesis-preregistration", ...]` -- the target
   skill genuinely detected as invoked for both real skills-on runs.
   canonical: `gh pr view 3172`, read this session — PR #3172's two real
   skills-off arms never dispatched at all (a separate, already-diagnosed
   cross-family skill-source tier conflict, issue #2055's own
   fail-closed check), so no real off-arm data exists to exercise the
   new check's off-arm branch against a real log; stated as an
   unrelated, pre-existing limitation in the pre-registration amendment,
   not papered over.

5. Updated `docs/issue-3127/decisions/pre-registration.md` with a dated
   (2026-09-02) amendment: the forgeability comparison table, the chosen
   artifact and honest residual-risk statement, the cross-check against
   spawn.py's mounted-skill list, the real-data verification result, and
   an explicit statement that the decision rule, threshold, guardrail,
   and sample size are unchanged and that no pair has been scored under
   either manipulation-check observation. Did not touch `scripts/
   issue-3127/verify_preregistration.py` (owned by another session, per
   this session's own spawning instructions).

6. Updated `tests/test_issue_3127_h1_and_scoring.py`
   (`ComputeH1ManipulationTest`, `GatePairOnH1Test`) and
   `tests/test_issue_3127_run_pair.py` (`RunPairTest`,
   `RunPairRealReachabilityTest`) to construct real/fake session-log
   fixtures instead of mocking `collect_directive_bytes()` to control
   the manipulation-check pass/fail.
   derived: `python3 -m pytest tests/test_issue_3127_h1_and_scoring.py
   tests/test_issue_3127_run_pair.py tests/test_issue_3127_run_consumer_pair.py -q`
   — result: 33 passed.
   derived: `python3 -m pytest tests/ -q` — result: 356 passed (2
   pre-existing, unrelated warnings about a stale BM25 pinned fixture in
   `tests/test_skill_candidates_floor.py`, not caused by this session's
   changes).

Acceptance checks:
   derived: `bash -c "python3 scripts/issue-3127/run_consumer_pair.py --dry-run"`
   — result: exit 0.
   derived: `bash -c "test -f docs/issue-3127/_assets/consumer-path-results.json"`
   — result: exit 0 (regenerated via `--emit-not-executed`; byte-identical
   to the committed skeleton, since `emit_not_executed_results()` never
   referenced manipulation-check internals).
   derived: `bash -c "python3 scripts/issue-3127/verify_preregistration.py"`
   — result: exit 1, `"both files were introduced in the same commit
   (fb0bb0d349cfe27837b03c7ed9e3bc470887c9c8)..."` -- reproducing PR
   #3172's independently-found squash-merge git-ancestry defect exactly.
   Left unmodified per this session's own spawning instructions ("Do not
   touch verify_preregistration.py -- another session owns it"); this
   gates landing of a *scored* result, and no result is landed here.

## Why

The manipulation check's job is to prove the manipulation (skill corpus
availability) actually happened before any quality comparison is trusted.
`directive_composition_bytes` looked like it was doing that job -- it
could fail on identical bytes -- but PR #3172's real runs (canonical:
`git show pr-3172-ref:docs/issue-3127/_assets/consumer-path-results.json`,
read this session) showed it structurally cannot: a skill delivered via
the Skill tool never touches the directory the metric sums, so the metric
would report "identical" for every real skills-on run regardless of
whether the manipulation worked, and could equally report "differs" from
an unrelated directive-composition change with nothing to do with skill
mounting. That is a metric that cannot fail informatively in either
direction -- the textbook construct-validity gap `experiment-trust` Step
5 (Twyman's-law: an observation that looks like a clean signal deserves a
forward trace before being trusted) exists to catch.

The four-candidate forgeability comparison (see the pre-registration
amendment for the full table) ruled out the PostToolUse hook trace
outright (it does not exist for the Skill tool) and the mounted-skill
registration outright (it answers availability, not invocation, by
construction, no matter how forge-proof it is). Between the transcript
and `runs/ledger.jsonl`, both ultimately trace back to the same
session-log content once you account for this machine running spawned
sessions unsandboxed on a shared, deliberately-browsable work root (this
session's own directives instructed exactly that browsing pattern) --
neither is cryptographically unforgeable. I picked the artifact
`scripts/measure_skill_invocation.py` already parses in production,
reasoning that *naturalness* (no in-task reason for a model to discover
and tamper with its own protocol stream) is the honest bar available
here, not perfect forgery-resistance, and said so explicitly in the
amendment rather than overclaiming security the design does not have --
`experiment-trust`'s own discipline against reporting more certainty
than the evidence supports.

I verified against PR #3172's real session logs (still present on this
machine, canonical: `ls ~/.tokenmaxxxer/work/`, read this session) rather
than spending a new real `--execute` spawn, because the acceptance
requirement was to show the new check detects invocation in data that
already exists, and a fresh spawn would have re-incurred real GitHub and
compute side effects for a question the existing real data already
answers. I did not attempt to generate a real off-arm data point for
this pair: canonical: `gh pr view 3172`, read this session -- PR #3172's
off-arm dispatch failure is a separate, already-diagnosed defect (issue
#2055's fail-closed cross-family check) unrelated to the manipulation
check's own observation mechanism, and working around it here would
mean weakening a shared safety check to serve one harness -- the same
out-of-scope call PR #3172 itself made.

`implementation-blueprint` was judged not-applicable: this is a
targeted fix to existing functions in one already-structured file
(`scripts/issue-3127/run_consumer_pair.py`), not a new module-spanning
design decision or a fan-out to parallel workers -- the skill's own
classify step vetoes exactly this shape (single-file, non-architectural
change).

`silent-failure-audit` applied to the new code:
`collect_skill_invocation()` and `compute_h1_manipulation()` introduce
zero new `try`/`except` blocks -- canonical: `grep -n "try:\|except"`
over `scripts/issue-3127/run_consumer_pair.py`'s new code range, read
this session -- no matches. Every fallible operation either propagates
uncaught (the `Path.glob()`/`stat()` calls in
`_find_latest_session_log()`) or delegates to `measure_skill_invocation.
analyze()`'s pre-existing, already-handled error paths: `OSError` from
`os.path.getsize()` is caught and returns an explicit `"unmeasurable"`
status (not silently treated as zero); `json.JSONDecodeError` on a
malformed log line is caught and the line is skipped, a deliberate
best-effort semantic for a streaming log parser, not new to this
session. No Silently-Absorbed sites found in the code this session
touched.

## What did not work

None -- no approach was tried and abandoned this session. The
four-candidate comparison in "What was done" step 2 was analysis leading
to a choice, not a false start.

## Upstream basis

- `docs/issue-3127/decisions/pre-registration.md` (sha: same-commit) --
  amended this session with the dated re-operationalization section; the
  pre-existing Theory/Hypotheses/Pre-registration-form/Power-statement
  sections were read but not altered, per the consult's own instruction
  that the decision rule and thresholds stay fixed.
- `scripts/issue-3127/run_consumer_pair.py` (sha: same-commit) -- modified
  this session (`compute_h1_manipulation()`, `gate_pair_on_h1()`,
  `run_pair()`, new `collect_skill_invocation()` /
  `_find_latest_session_log()`, `render_dry_run()`'s manipulation-check
  description).
- `scripts/measure_skill_invocation.py` (sha: same-commit, not modified
  this session, only imported and reused) -- the production skill-usage
  parser this session's `collect_skill_invocation()` wraps.
- PR #3172 (`tokenmaxxxer/on-the-record`, sha
  `570205e4d3e0921ef2892ea87a2659b142f90dc7`, not merged, not on this
  branch; canonical: `gh pr view 3172`, read via `git fetch` + `git show
  pr-3172-ref:<path>` this session) -- the construct-validity finding and
  real session-log data (study-companion issues #19, #21) this
  re-operationalization responds to and verifies against.

## Open findings

None new this session. canonical: `gh pr view 3172`, read this session --
PR #3172's four already-open findings (cross-family skill-source tier
conflict blocking the skills-off arm's dispatch; `spawn.py watch`'s
roster-lookup misreporting `watch-failed` for sessions that finished
running; `verify_preregistration.py`'s squash-merge defect) are
unchanged and out of this session's scope -- none of them concerns the
manipulation check's own observation mechanism, which is what this
session was asked to fix. resolution path: owned by PR #3172's own
open-findings list and by the separate session already redesigning
`verify_preregistration.py`; not reopened here.

## Next steps

None from this session -- `loop_state: terminal`. A future executing
session still needs a real off-arm dispatch (blocked on the cross-family
tier-conflict defect above, not on anything this session touched)
before any pair can pass the re-operationalized manipulation check for
real and reach the quality comparison.

skill-verdict: experiment-trust — applied: invoked; Step 1 scope gate --
canonical: `docs/issue-3127/decisions/pre-registration.md`'s "Scope
note" section, read this session -- confirmed offline, small-n,
pre-assigned comparison, SRM/A-A machinery not applicable; Step 5
Twyman's-law skepticism applied to the four-candidate forgeability
comparison and the honest residual-risk statement in "Why" and the
pre-registration amendment, rather than overclaiming the new signal is
unforgeable
skill-verdict: silent-failure-audit — applied: invoked; classified the
new code's error-handling surface (zero new catch sites; all fallible
operations propagate or delegate to `measure_skill_invocation.analyze()`'s
existing handled paths) in "Why"
skill-verdict: implementation-blueprint — not-applicable: single-file
targeted fix to existing functions, not a new module-spanning
architecture decision or a parallel-worker fan-out (see "Why")
