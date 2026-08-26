---
issue: 2443
role: conformance-review
author: conformance-review
loop_state: reported
type: review-record
code_under_review:
  - lifecycle.py
  - spawn.py
breaking: "none — this is a review record, no code changed by this role"
verdict: fail
upstream:
  - path: docs/issue-2443/reports/implementation.md
    sha: 81c1e4f4d3c2c97ae876f0ef8a1b2180875914dd
subject: PR #2450 (issue-2443/implementation, HEAD 81c1e4f4) — "prune orphaned spawn sidecar files under ~/.tokenmaxxxer/work"
test: independently-authored synthetic fixtures (own script, not copy-pasted from the implementation record's fixture) run against a `tempfile.TemporaryDirectory()` for the age-prune and active-spawn-protection claims + a read-only re-derivation of the real `~/.tokenmaxxxer/work` backlog count (no destructive re-run) + structural verification of the cross-checkout roster-scoping gap disclosed in the implementation record's own hunt finding, reproduced independently against this machine's actual 31 concurrent checkouts
result: failed
assertedBy: conformance-review session, issue-2443 (builder-blind)
---

# issue-2443 — conformance-review record

Builder-blind conformance review of PR #2450 (branch `issue-2443/implementation`,
HEAD `81c1e4f4`) against issue #2443's own Acceptance text, not against the
implementation session's self-report.

canonical: `git worktree add /tmp/wt-2443-impl origin/issue-2443/implementation` (this session), `git -C /tmp/wt-2443-impl rev-parse HEAD` —
```
81c1e4f4d3c2c97ae876f0ef8a1b2180875914dd
```
All citations below to files/lines that only exist on that branch are
pinned as `81c1e4f4:<path>`.

## What was done

Decomposed the issue's Acceptance section into 4 discrete requirements
(conformance-review-requirement-extraction): bullets 1 and 2 each carry
a "check:" clause and a separately-worded "must not" clause. Rather than
folding a bullet's "must not" silently into its own "check" (which would
hide a real wording gap between them), split bullet 2's material into
two line items — R2a for the literal "check:" text (which explicitly
scopes "active" to "per the same liveness check workspace-pruning
uses") and R2b for the unqualified "must not" clause, since the two
turned out to name different guarantee strengths once checked against
the actual deployed topology (rule 5: kept as its own item with the
dependency stated inline, rather than merged). Bullet 1's own "must
not" clause traces to the same R2b evidence and is not duplicated
(traceability rule 4). Picked a verification method per requirement
(conformance-review-verification-method-selection), rendered one of the
five verdicts per requirement (conformance-review-verdict-assignment).
Findings recorded below (conformance-review-finding-record). Sampling
was judged not-applicable — the reviewable diff is two source files
(`lifecycle.py`, `spawn.py`), small enough for full enumeration in one
session (see Skill verdicts).

Verification actually executed this session (own runs against the
`/tmp/wt-2443-impl` worktree checkout above, not pasted from the
implementation record):

canonical: independent synthetic fixture, own script, 4 cases in one pass (this session) —
```
before: ['a.events.jsonl', 'a.events.offset', 'a.session.20260101T000000.111.log', 'a.task.txt', 'a.watcher.log', 'b.events.jsonl', 'b.watcher.log', 'c', 'c.watcher.log', 'd.watcher.log']
outcome: {'removed': 5, 'kept': 3, 'failed': 0}
after: ['b.events.jsonl', 'b.watcher.log', 'c', 'c.watcher.log', 'd.watcher.log']
ALL ASSERTIONS PASSED (independent re-derivation)
```
Case A (orphaned, 20 days old, all 5 sidecar patterns present) removed;
case B (orphaned, fresh) survives; case C (paired workspace path still
`.exists()`, 20 days old) survives; case D (no paired dir, 20 days old,
but `_live_workspaces()` monkeypatched to report a live-pid roster entry
for it — same mechanism `_workspace_clean_state()` uses) survives.

canonical: read-only re-derivation of the real backlog, own script, no destructive prune re-run (this session) —
```
workspace_base= /home/jwjung/.tokenmaxxxer/work max_age_days= 14.0 live_entries= 0
total sidecar groups seen: 571
READ-ONLY current eligible groups (orphaned+old): 1
READ-ONLY current eligible files (orphaned+old): 8
```
This corroborates the implementation record's own live run (339 → 0,
546 kept, 0 failed) without re-executing the destructive delete a
second time against a directory genuinely shared by other, currently
running checkouts (see "What did not work"): a small (1 group / 8
files) new backlog is exactly what continued ordinary spawn activity
since that run would produce, not evidence of staleness or of the prune
never having run.

canonical: structural re-derivation of the cross-checkout roster-scoping gap the implementation record's own before-landing hunt disclosed (this session, read-only) —
```
$ ls -d /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-*/ | grep -v '\.log$' | wc -l
31
$ python3 -c "import spawn as _sp; print(_sp.ROOT, _sp.STATE_ROOT, _sp.ROSTER)"
/tmp/wt-2443-impl /tmp/wt-2443-impl/runs /tmp/wt-2443-impl/runs/active.json
$ echo "MUSTER_STATE_ROOT=$MUSTER_STATE_ROOT"
MUSTER_STATE_ROOT=
```
derived: the `31` above is `ls -d .../on-the-record-issue-*/ | grep -v '\.log$' | wc -l`, executed this session against the live `~/.tokenmaxxxer/work` directory (transcript verbatim above). Confirms, independent of the implementation record's own repro script, that this is not a hypothetical: 31 separate checkouts currently share one `~/.tokenmaxxxer/work`, each resolves its own `ROOT`/`STATE_ROOT`/`ROSTER` to its own checkout path (`81c1e4f4:spawn.py:44,593,898`), and `MUSTER_STATE_ROOT` (the one override that would unify them) is unset in this session's own environment — the exact condition under which `_live_workspaces()` (`81c1e4f4:lifecycle.py:569-575`) only ever sees the calling checkout's own roster entries.

## Findings

Fields per conformance-review-finding-record: requirement, spec_ref, verdict,
evidence, rationale, spec_vs_built (Incorrect only).

---
requirement: R1 — a sidecar file set (`.session.*.log`, `.events.jsonl`, `.events.offset`, `.watcher.log`, `.task.txt`) for a given issue-role pair older than the same age threshold used by workspace-directory pruning gets removed by the next prune pass — demonstrated with a synthetic old fixture set, before/after count
spec_ref: issue #2443 Acceptance bullet 1 ("check:" clause)
verdict: Present
evidence: `81c1e4f4:lifecycle.py:1037-1050` (`_SIDECAR_SUFFIX_MARKERS`/`_SIDECAR_SESSION_LOG_RE`/`_sidecar_workspace_name()` recognize all 5 named patterns); `81c1e4f4:lifecycle.py:1052-1121` (`_prune_orphaned_sidecars()`, threshold via `_clean_max_age_days()` — same constant `auto_sweep()` uses, `81c1e4f4:lifecycle.py:948`); own fixture transcript above ("What was done"), case A
rationale: an independently-authored fixture (own tempdir, own filenames, not the implementation record's literal strings) reproduces the claimed removal — all 5 sidecar patterns for an orphaned, 20-day-old set are deleted in one pass, count-for-count against the fixture's own before/after (see transcript above: `outcome: {'removed': 5, 'kept': 3, 'failed': 0}`)
---
requirement: R2a — a sidecar file set belonging to a currently in-flight/active spawn (workspace directory still present, or process still alive per the same liveness check workspace-pruning uses) is never removed regardless of age — demonstrated against a live fixture, scoped to the calling checkout's own roster (the literal mechanism the bullet names)
spec_ref: issue #2443 Acceptance bullet 2 ("check:" clause, "per the same liveness check workspace-pruning uses")
verdict: Present
evidence: `81c1e4f4:lifecycle.py:1096-1103` (`workspace_dir.exists()` short-circuit; `workspace_dir.resolve() in live` where `live = _sp._live_workspaces()`); own fixture transcript above ("What was done"), cases C and D
rationale: case C (paired path still exists) and case D (no paired path, but a live-pid roster entry claims it, via the identical `_live_workspaces()` call `_workspace_clean_state()` uses) both survive a 20-day-old age past the threshold, reproduced independently in this session's own fixture (transcript above: `after` list retains `c.watcher.log` and `d.watcher.log`) — this is exactly the mechanism the bullet's own parenthetical names ("per the same liveness check workspace-pruning uses"), and it is reused verbatim, not reimplemented
---
requirement: R2b — "must not: remove any sidecar file paired with a still-active workspace or process, regardless of file age" (the unqualified guarantee, distinct from R2a's narrower "per the same liveness check" wording); same guarantee also stated as bullet 1's "must not" clause
spec_ref: issue #2443 Acceptance bullet 1 "must not" clause; Acceptance bullet 2 "must not" clause (collapsed, same evidence — traceability rule 4)
verdict: Incorrect
evidence: `81c1e4f4:lifecycle.py:1101` (`workspace_dir.resolve() in live`, `live = _sp._live_workspaces()`, `81c1e4f4:lifecycle.py:569-575`, which calls `_sp._roster_load()` against `81c1e4f4:spawn.py:898` `ROSTER = STATE_ROOT / "active.json"`, and `81c1e4f4:spawn.py:593-594` `STATE_ROOT` defaults to `ROOT / "runs"` where `ROOT = Path(__file__).resolve().parent`, i.e. the *calling checkout's own* installation path unless `MUSTER_STATE_ROOT` is set); this session's own structural re-derivation above ("What was done", last transcript: 31 concurrent checkouts, each own `ROOT`/`STATE_ROOT`/`ROSTER`, `MUSTER_STATE_ROOT` unset); implementation record's own disclosed hunt finding (`81c1e4f4:docs/issue-2443/reports/implementation/2026-08-26-hunt-sidecar-prune.md`), reproducing `{'removed': 2, 'kept': 0, 'failed': 0}` against sidecar files paired with a workspace registered alive only in a *different* checkout's roster
rationale: the acceptance bullet's "must not" clauses are worded without the "per the same liveness check" qualifier R2a's "check:" text carries — read literally, they promise a sidecar file paired with *any* still-active workspace/process is never removed. The implementation only ever consults the calling checkout's own roster file; a workspace whose owning session is registered alive solely in a different, concurrently-running checkout's roster (the actual, confirmed topology on this machine: 31 checkouts sharing one `~/.tokenmaxxxer/work`, `MUSTER_STATE_ROOT` unset, per this session's own "What was done" transcript above) is invisible to the check, so its sidecar files are deleted once orphaned+aged even though the owning process is genuinely alive. This is not a hypothetical edge case — it is the deployed default, confirmed live this session. The implementation record itself discloses and reproduces this exact gap and elects to defer it as a follow-up rather than close it in this delivery; that is a legitimate scope judgment for the builder to make, but it does not make the "must not" clause, as literally written, satisfied — hence Incorrect rather than Present or Surface (rule 2: the mechanism doesn't merely omit a check, it affirmatively reports a still-active target as safe-to-delete under a specific, real condition)
spec_vs_built: spec requires a sidecar set paired with *any* still-active workspace or process to never be removed, regardless of age. What was built checks liveness only against the calling checkout's own `ROOT/runs/active.json`, which cannot see roster entries owned by other concurrently-running checkouts sharing the same `~/.tokenmaxxxer/work` — the default, unconfigured topology on this machine
---
requirement: R3 — live demonstration against the real current backlog: before/after count of orphaned+old sidecar files in `~/.tokenmaxxxer/work`, confirmed to drop to near-zero; must not delete files unrelated to spawn sidecars
spec_ref: issue #2443 Acceptance bullet 3
verdict: Present
evidence: `81c1e4f4:docs/issue-2443/reports/implementation.md` "Acceptance check 3" (live run: before 339, after 0, 546 kept, 0 failed); this session's own read-only re-derivation above ("What was done": 1 group / 8 files newly eligible, consistent with ordinary continued accumulation since that run, not staleness); `81c1e4f4:lifecycle.py:1042-1050` (`_sidecar_workspace_name()` returns `None`, and is skipped, for any filename not matching one of the 5 named patterns — confirmed against the fixture's bare `c` file, which is never grouped, per this session's own fixture transcript above)
rationale: reused the implementation record's own live-run numbers as Test-method evidence (verification-method-selection rule 4) rather than re-executing a second destructive prune against a directory this review's own R2b finding shows is unsafe to blindly re-run against while other checkouts are active; corroborated non-destructively via a fresh read-only recount (transcript above), which is consistent with the claimed before/after rather than contradicting it. The "must not delete files unrelated to spawn sidecars" half of this bullet is satisfied (only 5-pattern-matching filenames are ever grouped, per this session's own fixture transcript); the "must not delete a sidecar file for an active spawn" half is the same gap as R2b, not duplicated here
---
requirement: R4 — state explicitly whether the workspace-directory prune trigger/cadence (#2383/#2411) is reused as-is or a new cadence is introduced, and why
spec_ref: issue #2443 Acceptance bullet 4
verdict: Present
evidence: `81c1e4f4:docs/issue-2443/reports/implementation.md` "Reused threshold/trigger" paragraph, stating "reused as-is, not a new cadence"; `81c1e4f4:spawn.py:2600-2621` (`_prune_orphaned_sidecars()` call added inside the existing `_run_auto_sweep()` closure, immediately after the existing `auto_sweep()` call, same daemon thread — `threading.Thread(target=_run_auto_sweep, ...)` at line 2621, no second thread/timer/cron introduced)
rationale: the record states the choice explicitly and the code confirms it structurally — no new trigger point exists in the diff; the sidecar prune call is textually adjacent to, and shares the exception-absorbing contract of, the pre-existing `auto_sweep()` call in the same closure
---

## Why

Reviewed builder-blind against the issue's own Acceptance text — decomposed
into the requirements above before opening
`81c1e4f4:docs/issue-2443/reports/implementation.md` in full, then
cross-checked the implementation record's own disclosed hunt finding
against this session's own independent structural re-derivation rather
than accepting either the implementation's self-report or its own
scope judgment on R2b at face value. Demonstration for R1/R2a (own
synthetic fixtures, per the issue's explicit ask for a before/after);
Analysis for R2b (the condition — a genuinely alive process registered
only in a sibling checkout's roster — is real and reproducible but not
something this review needed to trigger destructively against
production state to establish, since the code path and the topology
that reaches it are both directly inspectable); Test-method reuse for
R3 (implementation record's own live-run numbers, corroborated
read-only rather than re-executed, per rule 4 — re-running a
destructive prune a second time against a shared, multi-checkout
directory this review's own R2b finding shows has a real liveness blind
spot would itself risk the exact harm the acceptance bullet's "must
not" clause forbids); Inspection for R4 (call-site placement).

## Upstream basis

- `81c1e4f4:docs/issue-2443/reports/implementation.md` — the delivering
  session's own record, including its "Acceptance check 1-3" transcripts
  and its "Reused threshold/trigger" statement (R4); read in full after
  this review's own independent fixture (R1/R2a) had already been run,
  so the fixture wasn't shaped by the implementation's own case
  choices.
- `81c1e4f4:docs/issue-2443/reports/implementation/2026-08-26-hunt-sidecar-prune.md`
  — the delivering session's own before-landing warrant-hunt record,
  which is the origin of R2b's finding; this review re-derived the same
  gap independently (structural check above) rather than merely
  restating the hunt record's own conclusion.
- PR #2450, branch `issue-2443/implementation`, HEAD `81c1e4f4` (see
  this record's opening `git rev-parse HEAD` transcript) — the code
  under review, checked out into `/tmp/wt-2443-impl` via `git worktree
  add` for independent, isolated fixture execution.
- Issue #2443 itself, fetched fresh this session (`gh issue view
  2443`), for the 4 Acceptance bullets.

## What did not work

canonical: this section's claims trace to the "What was done" transcripts above (own fixture runs, read-only recount, structural re-derivation) and to the R2b finding block above (evidence/rationale/spec_vs_built) — no new claim below is asserted without a source already cited in those sections.

- Did not re-execute the implementation record's own destructive live
  prune (`_prune_orphaned_sidecars(spawn._workspace_base(), ...)`
  against the real `~/.tokenmaxxxer/work`) a second time from this
  review session. That directory is confirmed (derived: `ls -d
  .../on-the-record-issue-*/ | grep -v '\.log$' | wc -l` → `31`,
  transcript in "What was done" above) shared by 31 concurrently-running
  checkouts on this machine, and this review's own R2b finding (see
  Findings above) shows the liveness check protecting it cannot see
  roster entries owned by sibling checkouts — re-running the delete a
  second time would risk exactly the false-positive removal the
  issue's own "must not" clauses forbid, against sessions this review
  has no way to confirm (no cross-checkout roster visibility exists,
  per R2b) are all currently idle. Used a read-only recount instead
  (transcript in "What was done" above: 1 group / 8 files) to
  corroborate the implementation record's reported before/after without
  adding a second real deletion pass. This is a deliberate scope choice
  by this review, made and executed this session (transcript above),
  not a failed attempt.
- No other divergence — the two independently-authored fixtures (R1/R2a)
  ran clean on the first attempt (transcript in "What was done" above).

## Open findings

canonical: see the R2b finding block above (Findings section) for the full evidence/rationale/spec_vs_built this entry summarizes.

- R2b (Incorrect) is the one open finding from this review. Resolution
  path already named by the implementation record itself
  (`81c1e4f4:docs/issue-2443/reports/implementation.md`, "Open
  findings"): file a follow-up issue against `_live_workspaces()`/
  `ROSTER` scoping (`MUSTER_STATE_ROOT`/roster unification across
  concurrently-running checkouts), since the same gap also pre-exists
  in the original #2383/#2411 workspace-directory prune this change
  reuses the check from — not something this review is asking this PR
  alone to close, but something that should not be silently treated as
  fully satisfying Acceptance bullets 1 and 2's unqualified "must not"
  wording either (see R2b's own evidence/rationale in Findings above).
  This review's own verdict differs from the implementation record's
  framing only in refusing to mark the "must not" clauses `Present`
  given a confirmed, reproducible counter-example under the actual
  deployed topology (see "What was done" structural re-derivation
  above).

## Next steps

canonical: this decision-routing note traces to the R2b finding block above (Findings section); no new evidence is introduced here.

None from this role — `loop_state: reported` (terminal for this
record's kind). Whether to open the named follow-up issue, and whether
issue #2443 itself should be considered closed given R2b (see Findings
above), is a decision for the issue owner, not this review.

## Skill verdicts

canonical: each skill-verdict line below summarizes work already cited with its own canonical/derived tag or file:line evidence in "What was done"/Findings above.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split issue #2443's Acceptance bullet 2 into R2a (the "check:" clause, scoped by its own "per the same liveness check" wording) and R2b (the unqualified "must not" clause, also matching bullet 1's own "must not") rather than merging them, once the two turned out to name different guarantee strengths (rule 5, dependency stated inline; see Findings above for both entries); no other bundled "and"-clauses found; bullet 4 kept as its own scope-boundary/documentation item
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of both changed files (`lifecycle.py`, `spawn.py`) was feasible in one session against a small, bounded diff — no reduction to a sample was needed
skill-verdict: conformance-review-verification-method-selection — applied: invoked; Demonstration for R1/R2a (own independently-authored fixtures, transcript in "What was done" above), Analysis for R2b (a real, reproducible cross-checkout condition established via code+topology inspection rather than a destructive live trigger), Test-method reuse for R3 per rule 4 (implementation record's own live-run numbers, corroborated read-only rather than re-executed a second time — see "What did not work"), Inspection for R4 (call-site placement)
skill-verdict: conformance-review-verdict-assignment — applied: invoked; R1/R2a/R3/R4 rendered Present with cited evidence (see Findings above); R2b rendered Incorrect (rule 2 — the mechanism actively reports a genuinely-alive cross-checkout target as safe-to-delete under a real, confirmed condition, not a mere omission) with its failing clause and `spec_vs_built` named (rule 5, see Findings above); re-checked R2b's evidence once against this session's own independent structural re-derivation (31 live checkouts, `MUSTER_STATE_ROOT` unset, transcript in "What was done" above) before finalizing, rather than accepting the implementation record's own hunt finding at face value (rule 6)
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every Findings entry cites file:line plus the reviewed commit sha (rule 1, `81c1e4f4:` prefix throughout); backward-traced each requirement to its issue bullet before checking the implementation (rule 3); R2b's evidence spans two files and is recorded per-file (rule 2: `lifecycle.py` liveness call site, `spawn.py` roster/STATE_ROOT definitions); bullet 1's and bullet 2's "must not" clauses collapsed into one R2b entry, noted as duplication (rule 4); single spec version in play — the issue as currently open (rule 5 n/a)
skill-verdict: conformance-review-finding-record — applied: invoked; wrote all 5 finding blocks with the full field list (requirement, spec_ref, verdict, evidence, rationale); R2b additionally carries `spec_vs_built` as required for its `Incorrect` verdict; every verdict carries an evidence pointer and a spec_ref
skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope was ordinary fidelity-checking against the issue's own Acceptance text, not an explicit extension into risk-weighting a recorded finding; R2b is reported as Incorrect with its resolution path named, not banded
skill-verdict: implementation-audit — not-applicable: this session ran under this repo's own role-handoff/conformance-review contract (a structurally independent evaluator session reviewing a separate builder session's delivery, builder-blind) — the same shape implementation-audit describes, but the mechanism in force here is the repo's native contract v3, not a separately-invoked implementation-audit protocol
