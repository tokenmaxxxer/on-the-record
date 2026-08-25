---
issue: 2312
role: conformance-review
loop_state: reported
upstream:
  - path: 848fd537c3738e625cd7706ab4718e3c20497f77:docs/issue-2312/reports/implementation.md
    sha: 848fd537c3738e625cd7706ab4718e3c20497f77
  - path: watchdog.py
    sha: 848fd537c3738e625cd7706ab4718e3c20497f77
subject: PR #2340 (branch issue-2312/implementation) against issue #2312's frozen Acceptance section
test: tests/test_poll_watchdog_log.py (gate) plus independent live-tick demonstrations (this session's own, not copied from the PR)
result: passed
assertedBy: conformance-review (issue-2312, builder-blind)
---

# issue-2312 — conformance-review record

## What was done

Builder-blind conformance review of PR #2340 (`issue-2312/implementation`,
commit `848fd537c3738e625cd7706ab4718e3c20497f77`) against issue #2312's
frozen Acceptance section. Extracted five checkable requirements from the
issue body (Acceptance section plus the Ask's retire/mark conditional), one
obligation per line:

- R1 — the gate test named by the issue, `tests/test_poll_watchdog_log.py`.
- R2 — the empty-state (no dead roster entries in a tick) output-identity
  requirement.
- R3a — the executed-live, single-print-per-instance requirement across
  three real ticks.
- R3b — the executed-live retire-or-mark conditional (nothing-to-watch vs.
  still-tracked).
- R4 — the Ask's "state lives per #2240's STATE_ROOT rules" placement
  constraint.
- R5 — the operator-frozen constraint bundle (systemic scope; added
  overhead; conflict/stall surfaces; consumer-tree residue; trade-offs
  stated).

Checked out `origin/issue-2312/implementation` into an isolated git worktree
(`/tmp/pr2340-check`, commit `848fd537c3738e625cd7706ab4718e3c20497f77`) and,
for every requirement, independently re-derived evidence rather than
trusting PR #2340's own pasted transcripts: re-ran the gate test myself, and
wrote fresh live-tick scripts exercising `spawn.roster_watchdog()` directly —
one with two dead entries in the same tick (one retiring, one retained), one
with an all-live/empty roster (R2) — deliberately different fixtures from
the ones the builder used in
`848fd537c3738e625cd7706ab4718e3c20497f77:docs/issue-2312/reports/implementation.md`
(on branch `issue-2312/implementation`; untracked in this checkout), so the
independent check isn't just replaying the builder's own script. Full
commands and pasted output for every requirement are under
"## Requirement findings" below.

## Why

Verify-at-landing and builder-blind review both require the reviewing
session's own executed evidence, not the builder's word for it. Using a
separate worktree keeps the review's test runs isolated from this branch's
own tree. Using different live-tick fixtures than the builder's (two
simultaneous dead entries instead of one at a time; explicit empty-roster
early-return check) was a deliberate choice to avoid rubber-stamping the
exact scenario the builder already exercised.

## Upstream basis

- `848fd537c3738e625cd7706ab4718e3c20497f77:docs/issue-2312/reports/implementation.md`
  (PR #2340; on branch `issue-2312/implementation`, untracked in this
  checkout)
- `848fd537c3738e625cd7706ab4718e3c20497f77:watchdog.py`
- issue #2312 body (Acceptance section), read this session via
  `gh issue view 2312 --json title,body,number,state,url`

## Requirement findings

---
requirement: R1 — gate `tests/test_poll_watchdog_log.py`
spec_ref: issue #2312, Acceptance, "gate: `tests/test_poll_watchdog_log.py`"
verdict: Present
evidence: tests/test_poll_watchdog_log.py (848fd537c3738e625cd7706ab4718e3c20497f77), executed this session — see acceptance run below
acceptance: cd /tmp/pr2340-check (commit 848fd537, origin/issue-2312/implementation) && python3 -m pytest tests/test_poll_watchdog_log.py -q — result:
```
....                                                                     [100%]
4 passed in 0.97s
```
rationale: an existing repo test already covers the gate named by the issue; reused it as Test-method evidence per verification-method-selection rule 4 rather than re-deriving a parallel manual check, and re-ran it myself in an isolated worktree rather than trusting the PR's pasted count (PR #2340's own transcript claims the same 4-pass count at a different wall time, consistent with this independent run).
---
requirement: R2 — empty state (no dead entries): output byte-identical
spec_ref: issue #2312, Acceptance, "empty state: no dead entries — output byte-identical."
verdict: Present
evidence: 848fd537c3738e625cd7706ab4718e3c20497f77:watchdog.py:1513-1517, 1588-1603
canonical: 848fd537c3738e625cd7706ab4718e3c20497f77:watchdog.py:1513-1517 (`if not d: ... return anomaly_count`) — the entire new dead-entry-report block (848fd537:watchdog.py:1588-1603) sits inside the per-entry loop reached only after this early return, so a tick with an empty/all-live roster never reaches it.
acceptance: cd /tmp/pr2340-check && python3 -u -c "import spawn, json; from pathlib import Path; import tempfile; from unittest import mock; td=Path(tempfile.mkdtemp()); (td/'active.json').write_text('{}'); spawn.ROSTER=td/'active.json'; spawn.WATCHDOG_STATE=td/'watchdog_state.json'; \
with mock.patch.object(spawn,'_board_wide_sweep',return_value=0), mock.patch.object(spawn,'standing_red_check',return_value=[]), mock.patch.object(spawn,'_undispositioned_role_prs',return_value=([],True)), mock.patch.object(spawn,'lease_reconcile_sweep',return_value=0): rc=spawn.roster_watchdog(root=td); print('rc:',rc,'state file exists:',(td/'watchdog_state.json').exists())" — result:
```
돌고 있는 역할 세션 없음
이상 신호 없음
rc: 0 state file exists: False
```
rationale: Analysis of the control flow (the diff's only change is inside a branch unreachable when no dead entry exists) plus a Demonstration run against a literal empty roster both show the new code path never executes in the empty-state case, and the new save call never fires (`watchdog_state.json` is not created), matching the issue's byte-identical requirement.
---
requirement: R3a — terminal line prints exactly once across three real ticks
spec_ref: issue #2312, Acceptance, "provenance: executed-live — ... show COMPLETED printed exactly once across three real ticks ..."
verdict: Present
evidence: this session's live-tick run against 848fd537c3738e625cd7706ab4718e3c20497f77:watchdog.py:1588-1599 — see acceptance run below
acceptance: cd /tmp/pr2340-check && python3 -u /tmp/indep_repro_2312.py (this session's own script, two dead entries: issue-100/reviewer expects_pr=False/issue=None, issue-200/implementation issue=200/expects_pr=True, driven through the real spawn.roster_watchdog() for 3 ticks) — result:
```
--- independent tick 1 ---
[poll-report] issue-100/reviewer: COMPLETED — independent-repro fake completion
[poll-report] issue-200/implementation: COMPLETED — independent-repro fake completion
이상 신호 없음
roster keys after tick 1: ['issue-200/implementation']
--- independent tick 2 ---
이상 신호 없음
roster keys after tick 2: ['issue-200/implementation']
--- independent tick 3 ---
이상 신호 없음
roster keys after tick 3: ['issue-200/implementation']
COMPLETED lines total across 3 ticks: 2
   [poll-report] issue-100/reviewer: COMPLETED — independent-repro fake completion
   [poll-report] issue-200/implementation: COMPLETED — independent-repro fake completion
final roster: {'issue-200/implementation': {'pid': 42425, 'role': 'implementation', 'issue': 200, 'expects_pr': True, 'session_id': None, 'work': None}}
```
rationale: executed-live Demonstration per the issue's own explicitly-named verification method, using a fixture (two simultaneous entries) independent of the builder's sequential single-entry scripts: each entry's COMPLETED line appears exactly once (both on tick 1), zero times on ticks 2-3.
---
requirement: R3b — entry removed when nothing to watch, else retained and not reprinted
spec_ref: issue #2312, Ask, "either remove the entry (safe immediately when `expects_pr: false` and `issue: null`) or mark `reported_terminal` and skip the print thereafter"; Acceptance, "the entry removed/marked"
verdict: Present
evidence: 848fd537c3738e625cd7706ab4718e3c20497f77:watchdog.py:1600-1603, and this session's live-tick run (same as R3a) — see acceptance below
canonical: 848fd537c3738e625cd7706ab4718e3c20497f77:watchdog.py:1600-1603 (`if not e.get("expects_pr") and issue_n is None: _sp.roster_remove(key)`)
acceptance: same run as R3a (/tmp/indep_repro_2312.py) — result quoted above under R3a shows `roster keys after tick 1: ['issue-200/implementation']` — `issue-100/reviewer` (expects_pr=False, issue=None) is gone after tick 1, `issue-200/implementation` (issue=200) remains present and unreprinted through ticks 2-3, and `final roster` above contains only the retained entry.
rationale: both branches of the conditional named in the Ask (kept as its own requirement item with the dependency stated inline, per requirement-extraction rule 5) fire correctly on the code as committed, confirmed by execution rather than reading alone.
---
requirement: R4 — state lives per #2240's STATE_ROOT rules (no new/ad hoc state location)
spec_ref: issue #2312, Ask, "State lives per #2240's STATE_ROOT rules."
verdict: Present
evidence: 848fd537c3738e625cd7706ab4718e3c20497f77:watchdog.py:1588, 1594, 1518, 106-115
canonical: 848fd537c3738e625cd7706ab4718e3c20497f77:watchdog.py:1588 (`terminal_key = f"{key}:{e.get('pid', 0)}:reported_terminal"`) and :1594 (`state[terminal_key] = True`) write into the same `state` dict already obtained from `_sp._watchdog_state_load()` at 848fd537:watchdog.py:1518 and persisted via the pre-existing `_watchdog_state_save()` at 848fd537:watchdog.py:106-115; `git diff main origin/issue-2312/implementation -- watchdog.py` shows no change to any `WATCHDOG_STATE`/`ROSTER`/`STATE_ROOT`/`ROOT` definition.
rationale: Inspection of the diff shows the fix reuses the existing STATE_ROOT-governed state file and adds no new path/global, so the Ask's placement constraint is satisfied by construction, not by a new mechanism this review would need to separately validate.
---
requirement: R5 — operator-frozen constraint: systemic; no added overhead; no new conflict/stall surfaces; no consumer-tree residue; trade-offs measured and stated
spec_ref: issue #2312, "Operator-frozen constraint applies (2026-08-25)"
verdict: Present for the systemic-scope, consumer-tree-residue, and trade-offs-stated sub-clauses; flagged (not a guessed verdict) for the other two — see Open findings
evidence: 848fd537c3738e625cd7706ab4718e3c20497f77:watchdog.py:1430; `gh pr view 2340 --json files` (this session); 848fd537c3738e625cd7706ab4718e3c20497f77:docs/issue-2312/reports/implementation.md "## Why"
canonical: systemic scope — 848fd537:watchdog.py:1430 `def roster_watchdog(...)` is the single shared entry point every consumer/orchestrator session's poll tick already calls (no per-consumer branch in the diff). consumer-tree residue — `gh pr view 2340 --json files` lists only `watchdog.py`, `docs/issue-2312/reports/implementation.md`, `docs/issue-2312/reports/implementation/2026-08-25-hunt-dead-active-json-retire.md`; roster/watchdog state lives under `STATE_ROOT`/`ROOT/runs` (spawn.py:540-541, 845), outside any consumer session's git-tracked tree. trade-offs stated — 848fd537c3738e625cd7706ab4718e3c20497f77:docs/issue-2312/reports/implementation.md, "## Why" section, states and justifies the pid-scoping-vs-clear-on-respawn trade-off explicitly (on branch `issue-2312/implementation`; untracked in this checkout).
rationale: three of the five sub-clauses have an observable, checkable condition and were inspected directly against the diff and PR file list; "no added overhead" and "no new conflict/stall surfaces" have no numeric/observable threshold in the issue text, so per verdict-assignment rule 3 / requirement-extraction rule 2 they are flagged rather than given an invented verdict — detail under Open findings.
---

## Open findings

- R5, sub-clause "no new conflict/stall surfaces" — flagged, non-blocking.
  canonical: 848fd537c3738e625cd7706ab4718e3c20497f77:watchdog.py:1599 calls
  `_sp._watchdog_state_save(state)` (defined 848fd537:watchdog.py:113,
  unlocked — no `fcntl` around it, unlike `_roster_locked()`'s writes to
  `active.json` in roster.py:40-49) a second time within one tick, in
  addition to the pre-existing single end-of-tick call at
  848fd537:watchdog.py:1660. The save was already lock-free before this PR
  (roster.py's own comment notes `_watchdog_state_save` has no equivalent to
  `_roster_locked()`), so this is a widening of an existing lock-free window
  between concurrent watchdog ticks, not a newly-invented one. Issue #2312's
  own Acceptance section names only the gate test, the empty-state
  requirement, and the executed-live provenance (R1-R3b above, all Present),
  none of which this observation touches.
  Resolution path: no action needed for issue #2312's own Acceptance items;
  if `_watchdog_state_save` should be lock-protected, file that as its own
  issue — the absence of a lock pre-dates this PR.
- R5, sub-clause "no added overhead" — flagged as unverifiable-as-written,
  not scored Present or Absent. The issue gives no numeric/observable
  overhead threshold to check against. Qualitatively, per
  848fd537:watchdog.py:1588-1599, the added cost is one extra dict write per
  dead-entry instance's first report only (not per tick thereafter) — stated
  here as a qualitative note, not as a pass/fail claim, per
  requirement-extraction rule 2 (flag unverifiable-as-written rather than
  invent a threshold).
  Resolution path: a concrete overhead threshold, if wanted, belongs in a
  future issue amendment.

## Next steps

None — loop_state is terminal (`reported`). R1, R2, R3a, R3b, and R4 (issue
#2312's frozen Acceptance items plus the Ask's placement constraint) are
each recorded Present above with independently executed or inspected
evidence; R5's two flagged sub-clauses are recorded as non-blocking Open
findings with a resolution path, not as outstanding acceptance gaps.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; decomposed issue #2312's Acceptance section (plus the Ask's retire/mark conditional) into R1-R5 (R3 split into R3a/R3b, one obligation per line) with dimension tags before any verdict was rendered.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; Test for R1 (reused `tests/test_poll_watchdog_log.py`), Analysis+Demonstration for R2, Demonstration for R3a/R3b (per the issue's own "executed-live" ask), Inspection for R4 and most of R5.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; Present for R1-R4, Present-with-flagged-sub-clauses for R5, and an explicit flag (not a guessed Present/Absent) for R5's "no added overhead" sub-clause per rule 3.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every evidence line cites file:line plus commit sha `848fd537c3738e625cd7706ab4718e3c20497f77`, and issue #2312's Acceptance text was read (backward-traced) before any implementation file was inspected.
skill-verdict: conformance-review-finding-record — applied: invoked; wrote the five `---`-delimited requirement blocks above with the full field list (requirement, spec_ref, verdict, evidence/acceptance/canonical, rationale), no block written without an evidence pointer or spec_ref.
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of issue #2312's Acceptance section (3 bullets, single-file diff) was feasible; no sampling scope was needed.
skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope was not explicitly extended into risk-weighting a recorded finding; only fidelity-checking against issue #2312's frozen Acceptance was requested.
skill-verdict: implementation-audit — applied: invoked; followed its independent-evaluator framing (this session read PR #2340's implementation as claims to independently re-derive, not as evidence to trust, and wrote its own fixtures rather than replaying the builder's), even though the concrete requirement/verdict mechanics ran through the more specific conformance-review-* family above.
other mounted skills: not triggered
