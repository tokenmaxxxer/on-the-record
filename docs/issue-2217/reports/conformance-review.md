---
issue: 2217
role: conformance-review
loop_state: reported
upstream:
  - path: issue #2217 (GitHub, canonical: gh issue view 2217)
    sha: same-commit
  - path: PR #2234 (branch issue-2217/implementation, GitHub)
    sha: af8ddad82138d5a34c1c9adf7be2351ba99d6cc2
subject: PR #2234 ("issue-2217: detect the structured background-delegation act, not the vocabulary") graded against issue #2217's frozen `## Acceptance` section
test: gates/requirement_met.py 2217 2234 (deterministic artifact-presence sub-check); independent re-execution of tests/test_watchdog_local_signals.py from a git worktree at the PR's head commit; independent re-run of the before/after structural-delegation detector against the real session logs the issue and PR name, read fresh from /home/jwjung/.tokenmaxxxer/work/, not transcribed from the PR's own record
result: passed
assertedBy: builder-blind conformance-review session (branch issue-2217/conformance-review) — no access to PR #2234's builder session or its rationale; verdicts below rest on the issue body, the PR diff, and code/tests read from the PR's own head commit
---

# issue-2217 — conformance-review record

## What was done

Builder-blind grading of PR #2234 against issue #2217's frozen `## Acceptance` section, per issue #1651's requirement-met contract.
canonical: gh issue view 2217
canonical: gh pr diff 2234

issue #2217's `## Acceptance` section is one `gate:` line, one `empty state:` line, and one `provenance:` line. The `provenance:` line bundles three obligations — split per conformance-review-requirement-extraction rule 1 into three separate checkable items below, alongside the `gate:` and `empty state:` lines, for six items total. Full enumeration was feasible without sampling.

canonical: python3 gates/requirement_met.py 2217 2234
```
advisory: [UNKNOWN] `tests/test_watchdog_local_signals.py`
게이트 통과 (또는 채점 가능한 기준 없음)
```
The CLI supplies no per-criterion verdict for a bare `gate:` line with no `check:` bullets under it, so it defaults to advisory UNKNOWN with no blocking sub-check triggered — hand-graded below.

Per-criterion findings (verdict set per conformance-review-verdict-assignment: Present/Surface/Absent/Incorrect/Unverifiable):

---
requirement: "gate: `tests/test_watchdog_local_signals.py`"
spec_ref: issue #2217 `## Acceptance`, gate: line
verdict: Present
method: Test — directly re-executed this session from a `git worktree add` checkout at the PR's head commit, not reused from the record's own pasted output
evidence: af8ddad8:tests/test_watchdog_local_signals.py (full file, +89/-1 in the PR diff)
```
$ python3 -m pytest tests/test_watchdog_local_signals.py -v
============================== 16 passed in 0.89s ==============================
```
canonical: python3 -m pytest tests/test_watchdog_local_signals.py -v  (worktree at af8ddad8, this session — output above)
derived: 16 passed, 0 failed, 0 skipped — read directly from the pytest summary line in the fenced output immediately above; hand-typed count equals the pasted summary count
rationale: fresh execution from the PR's own head commit reproduces the full 16-test hold, independent of the record's own pasted output.

---
requirement: "empty state: a session log containing the injected directive and nothing else (spawned, no assistant turns yet) — must produce zero anomalies."
spec_ref: issue #2217 `## Acceptance`, empty state: line
verdict: Present
method: Test (reused, per conformance-review-verification-method-selection rule 4) — `TestBackgroundDelegationStructural.test_injected_directive_text_alone_yields_zero_anomalies`
evidence: af8ddad8:tests/test_watchdog_local_signals.py:206-215 (feeds `spawn._COMPLETION_PROSE`, the real injected-directive text, as the only log content and asserts `watchdog_check_one` returns `[]`); af8ddad8:events.py:189-217 (`_count_structural_delegations` only counts `type: "assistant"` `tool_use` blocks)
```
$ python3 -m pytest tests/test_watchdog_local_signals.py -v -k test_injected_directive_text_alone_yields_zero_anomalies
tests/test_watchdog_local_signals.py::TestBackgroundDelegationStructural::test_injected_directive_text_alone_yields_zero_anomalies PASSED
1 passed in 0.02s
```
canonical: python3 -m pytest tests/test_watchdog_local_signals.py -v -k test_injected_directive_text_alone_yields_zero_anomalies  (worktree at af8ddad8, this session — output above)
derived: 1 passed, 0 failed — read directly from the pytest summary line in the fenced output immediately above
rationale: the test passed independently this session, and the underlying detector logic is content-shape-agnostic beyond assistant+tool_use+run_in_background, so the guarantee holds regardless of which JSONL envelope carries the directive text — see Open findings item 1 for a fixture-fidelity nuance that does not change this verdict.

---
requirement: "provenance: executed-live — run the fixed detector against the real logs of the sessions listed above (under /home/jwjung/.tokenmaxxxer/work/) and paste the actual before/after anomaly output."
spec_ref: issue #2217 `## Acceptance`, provenance: line (clause 1)
verdict: Present
method: Demonstration — independently re-executed against the real log files on disk, not transcribed from the PR's own pasted output
evidence: af8ddad8:events.py:189-217 (`_count_structural_delegations`); the seven real log files under `/home/jwjung/.tokenmaxxxer/work/`, matched by the exact filenames the PR's record cites
```
$ python3 - <<'EOF'   # reconstructs the deleted _DELEGATION_RE inline (byte-identical to
                       # watchdog.py's pre-PR definition) and diffs it against
                       # spawn._count_structural_delegations on each of the 7 named logs
on-the-record-issue-2204-implementation.session.20260824T222535.4130680.log         BEFORE=True  AFTER=True
on-the-record-issue-2204-execution-observation.session.20260824T232057.1632735.log  BEFORE=True  AFTER=False
on-the-record-issue-2204-conformance-review.session.20260824T232215.1632735.log     BEFORE=True  AFTER=True
on-the-record-issue-2208-implementation.session.20260824T231045.1590418.log         BEFORE=True  AFTER=False
on-the-record-issue-2210-implementation.session.20260824T232302.1650855.log         BEFORE=True  AFTER=False
on-the-record-issue-2214-implementation.session.20260824T233348.2080038.log         BEFORE=True  AFTER=False
on-the-record-issue-2215-implementation.session.20260824T233302.2032422.log         BEFORE=True  AFTER=False
TOTAL=7 BEFORE_TRUE=7 AFTER_TRUE=2 AFTER_FALSE=5
```
canonical: python3 - <<'EOF' (script above, worktree at af8ddad8, this session — output above, TOTAL line self-computed and printed by the script)
derived: TOTAL=7, BEFORE_TRUE=7, AFTER_TRUE=2, AFTER_FALSE=5 — read directly from the TOTAL line in the fenced output immediately above
rationale: every BEFORE/AFTER value above matches the PR's own pasted transcript exactly, produced fresh this session against the real files on disk rather than read from the PR's record.

---
requirement: "provenance: ... Before must show the false positives"
spec_ref: issue #2217 `## Acceptance`, provenance: line (clause 2)
verdict: Present
method: Demonstration (same independent run as the prior item, output reproduced again below)
evidence: af8ddad8:events.py:189-217 vs. the reconstructed pre-PR `_DELEGATION_RE`; the 7 real logs named below
```
$ python3 - <<'EOF'   # same reconstruction script as the provenance clause-1 item above
on-the-record-issue-2204-implementation.session.20260824T222535.4130680.log         BEFORE=True  AFTER=True
on-the-record-issue-2204-execution-observation.session.20260824T232057.1632735.log  BEFORE=True  AFTER=False
on-the-record-issue-2204-conformance-review.session.20260824T232215.1632735.log     BEFORE=True  AFTER=True
on-the-record-issue-2208-implementation.session.20260824T231045.1590418.log         BEFORE=True  AFTER=False
on-the-record-issue-2210-implementation.session.20260824T232302.1650855.log         BEFORE=True  AFTER=False
on-the-record-issue-2214-implementation.session.20260824T233348.2080038.log         BEFORE=True  AFTER=False
on-the-record-issue-2215-implementation.session.20260824T233302.2032422.log         BEFORE=True  AFTER=False
TOTAL=7 BEFORE_TRUE=7 AFTER_TRUE=2 AFTER_FALSE=5
```
canonical: python3 - <<'EOF' (reconstruction+diff script, worktree at af8ddad8, this session — output above)
derived: BEFORE_TRUE=7 out of 7 logs — read directly from the TOTAL line in the fenced output immediately above
rationale: the old word-matching regex fires on all 7 real logs the issue named, matching the issue's own reported 100%-false-positive measurement.

---
requirement: "provenance: ... after must show none, while a log containing a genuine `run_in_background: true` tool_use still trips it"
spec_ref: issue #2217 `## Acceptance`, provenance: line (clause 3)
verdict: Present
method: Demonstration (same independent run) + Inspection of the two logs that stay `AFTER=True`, to check whether they reflect a real tool_use or a residual false positive
evidence: the fenced AFTER column and the two `tool_use` block dumps below
```
$ python3 - <<'EOF'   # same reconstruction script as the provenance clause-1 item above
on-the-record-issue-2204-implementation.session.20260824T222535.4130680.log         BEFORE=True  AFTER=True
on-the-record-issue-2204-execution-observation.session.20260824T232057.1632735.log  BEFORE=True  AFTER=False
on-the-record-issue-2204-conformance-review.session.20260824T232215.1632735.log     BEFORE=True  AFTER=True
on-the-record-issue-2208-implementation.session.20260824T231045.1590418.log         BEFORE=True  AFTER=False
on-the-record-issue-2210-implementation.session.20260824T232302.1650855.log         BEFORE=True  AFTER=False
on-the-record-issue-2214-implementation.session.20260824T233348.2080038.log         BEFORE=True  AFTER=False
on-the-record-issue-2215-implementation.session.20260824T233302.2032422.log         BEFORE=True  AFTER=False
TOTAL=7 BEFORE_TRUE=7 AFTER_TRUE=2 AFTER_FALSE=5

$ python3 - <<'EOF'   # filters the two AFTER=True logs for tool_use blocks with input.run_in_background truthy
on-the-record-issue-2204-implementation.session...: name=Bash input={"command": "timeout 590 python3 -m pytest tests/ test/ -q ...", "run_in_background": true}
on-the-record-issue-2204-conformance-review.session...: name=Agent input={"description": "Warrant hunt after-proposal, stance 0", "subagent_type": "warrant:warrant-hunter", "model": "sonnet", "run_in_background": true, ...}
```
canonical: python3 - <<'EOF' (both scripts above, worktree at af8ddad8, this session — output above)
derived: AFTER_FALSE=5 (2204-execution-observation, 2208, 2210, 2214, 2215) and AFTER_TRUE=2 (2204-implementation, 2204-conformance-review) — read directly from the TOTAL line and the two tool_use dumps in the fenced output immediately above
rationale: both remaining `AFTER=True` logs carry, per the fenced inspection output directly above, a real `tool_use` block (one `Bash`, one `Agent`, matching the issue's own "Bash ... or an Agent/Task call" wording) with `run_in_background: true` — genuine positives, not detector false positives — while the other 5 logs, whose only match was the injected-directive vocabulary, correctly clear to no-anomaly.

## Why

The task specifies builder-blind grading against issue #2217's frozen `## Acceptance` section: read the issue and the PR diff, run `gates/requirement_met.py`, and independently re-verify rather than trust the PR's own pasted evidence. Independent re-verification (worktree checkout at the PR's exact head commit, fresh pytest run, and a fresh re-run of the before/after detector comparison against the real log files still present on disk) was chosen over reading the PR record's pasted output, because the acceptance criterion's own `provenance: executed-live` clause is specifically about evidence a reader can reproduce, not evidence a reader must take on faith.

## Upstream basis

- issue #2217 (GitHub) — canonical: gh issue view 2217 — the frozen `## Acceptance` section graded above.
- issue #1651 (GitHub, closed) — canonical: gh issue view 1651 — defines gates/requirement_met.py's intended contract: deterministic artifact-presence blocks a landing; the semantic YES/NO/UNKNOWN verdict is advisory-only.
- issue #994 (GitHub, closed) — the precedent transition (`_count_structural_denials`) PR #2234 names and this record cross-checked events.py against.
- PR #2234 — canonical: gh pr view 2234 --json title,body,headRefName,state,commits,files; gh pr diff 2234 — branch issue-2217/implementation, head af8ddad82138d5a34c1c9adf7be2351ba99d6cc2.
- events.py, spawn.py, watchdog.py, tests/test_watchdog_local_signals.py — read and executed from a `git worktree add` checkout of the PR's exact head commit (worktree removed after use, not part of this branch's own tree).
- The seven real session logs named in the issue and cited in the PR's own record, read fresh from `/home/jwjung/.tokenmaxxxer/work/` this session.

## What did not work

None — the independent re-execution held on the first attempt for every item checked; no dead end here for the next reader to avoid repeating.

## Open findings

1. The `empty state:` acceptance test (`test_injected_directive_text_alone_yields_zero_anomalies`) feeds the directive as a synthetic `{"type": "system", "subtype": "hook_started", "text": ...}` line, but a real production log carries it differently:
```
$ python3 -c "
import json
with open('/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2215-implementation.session.20260824T233302.2032422.log', encoding='utf-8', errors='replace') as fh:
    for i, line in enumerate(fh):
        if '완료의 정의' in line:
            print(i, json.loads(line).get('type')); break
"
35 user
```
canonical: python3 -c "..." (this session's own read, output above)
derived: line 35, type "user" — read directly from the fenced output immediately above
rationale: the directive arrives as a `type: "user"` message's `tool_result` content block (the session `Read`ing the materialized `.on-the-record/directive/completion-and-landing.md` file per `directive_section_files()`, af8ddad8:spawn.py:1963-1979), not the synthetic `type: "system"` envelope the test uses.
   Net effect: none on correctness — see the provenance "after must show none" item above (this same record), which already independently confirms real logs carrying only directive prose (in whatever real envelope it arrives in) clear to zero anomalies. This is a test-fixture-fidelity note, not a functional gap. Resolution path: none required for this PR to land; optionally a future test could assert against a captured real-log fixture instead of a hand-built envelope.

## Next steps

None — `loop_state: reported` is terminal for a review-record (contract v3's per-kind table).

## skill-verdicts

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split the `provenance:` line's three bundled obligations into separate checkable items (rule 1), alongside the `gate:` and `empty state:` lines, for six items total.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; chose Test (rule 4) for the gate/empty-state items, Demonstration for the three provenance clauses, and Inspection (rule 1) for the two remaining `AFTER=True` logs — see the per-criterion blocks above for the fenced evidence and canonical citations backing each choice.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; assigned Present to all six items with evidence located and independently re-derived in each case (rule 3, Unverifiable, was considered and set aside — all evidence was locatable and re-executable); the fixture-fidelity nuance was recorded as an open finding rather than downgrading the empty-state verdict, since it does not affect the requirement's actual behavior (rule 6, re-checked the specific evidence before finalizing — see Open findings item 1 above).
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every code citation above pins file:line plus the PR head commit sha af8ddad82138d5a34c1c9adf7be2351ba99d6cc2 actually read, in `sha:path:line` form (rule 1); the real-log evidence is pinned to exact filenames under `/home/jwjung/.tokenmaxxxer/work/` (rule 5, version pin — these are the exact log files the issue and PR both name, not a re-derived set).
skill-verdict: conformance-review-finding-record — applied: invoked; wrote six per-criterion blocks with the full field list (requirement, spec_ref, verdict, evidence, rationale), inside the skeleton's own narrative section rather than adding new top-level headings (rules 2, 3).

other mounted skills (conformance-review-sampling-derivation, conformance-review-severity-classification): not-applicable — full enumeration of all six checkable items was feasible without sampling, and this review's scope was never extended into risk-weighting an already-recorded finding.
