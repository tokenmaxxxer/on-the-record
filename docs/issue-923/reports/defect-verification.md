---
kind: verify-record
loop_state: cleared
---

# defect-verification record — issue #923

## Attempt

canonical: docs/issue-923/reports/defect-verification/current-state.md
Findings 1-4, read this session (the approved phase-1 survey).

- attempt: reproduce, against the pre-fix code, the shape the phase-1
  survey's Findings 2 and 3 already pinned — `outcome_claim_citation_check`
  (issue #870, gates/record_lint.py:96-146) refusing an observation
  record's own prose `canonical:` transcript citation on an OUTCOME
  line.
- outcome: reproduced.
- steps: re-ran `outcome_claim_citation_check` against the #895 record's
  exact shape (a `canonical: execution transcript for the
  ambiguous-scenario run, fixture PR #15 merged 2026-08-05` line
  immediately above an `ambiguous-scenario requirement met: PASS`
  line), first against the pre-fix commit, then live through
  `on-the-record/hooks/record-claim-guard.sh`.

derived: `git stash && python3 -c "import sys; sys.path.insert(0,
'gates'); import record_lint; text =
'---\nloop_state: landed\n---\n\ncanonical: execution transcript for
the ambiguous-scenario run, fixture PR #15 merged
2026-08-05\nambiguous-scenario requirement met:
PASS\n'; print(record_lint.outcome_claim_citation_check(text))" &&
git stash pop`

```
["레코드에 실행-근거 없는 OUTCOME 주장 (issue #870): 'ambiguous-scenario requirement met: PASS' — 'requirement met/done/PASS/complete' 류의 결과 주장을 하면서 3줄 이내에 실행-라이브 인용(...) 없다 — 파일을 읽었다는 인용만으로는 부족하다."]
```

## Finding — addressed_to: coding, resolved this session

- requirement: issue #923 body — the outcome-claim gates must not
  refuse a legitimate observation/verdict record backed by its own
  executed-live measurement citation, while still refusing an unbacked
  claim.
- verdict: Absent, at the pre-fix commit
  a4eed4507144a415464e2c030be6a03a2a0c19d1 — see the attempt's evidence
  above.
- evidence: attempt block above; current-state.md Findings 2 and 3.
- rationale: `_EXECUTED_LIVE_CANONICAL` (gates/record_lint.py:90-93,
  pre-fix) matched only a shell-command-prefixed string or the two fixed
  `acceptance:`/`live-fire:` result-tag shapes — evidence shapes an
  implementation-side delivery claim carries, not an observation role's
  own prose measurement citation.
- severity band: this defect silently blocked landing of a correctly
  measured requirement record with no data-integrity or security
  exposure -> High -> blocking.
- addressed_to: coding. Per this turn's explicit instruction to
  implement the approved diagnosis in this same session/branch, the fix
  below was implemented directly rather than handed off; recorded here
  as resolved.

## What was done

Extended `outcome_claim_citation_check` (gates/record_lint.py, and its
byte-identical copy on-the-record/gates/record_lint.py) with a third
citation shape, `_OBSERVATION_LIVE_CANONICAL` — a `canonical:` citation
whose text names a "transcript" or "measurement" — additive to the two
existing implementation-shaped ones (command-prefixed string;
`acceptance:`/`live-fire:` result-tag). Added two regression tests to
gates/test_record_lint.py: one pinning the #895 shape now succeeds, one
pinning a bare "read this session" citation naming no transcript or
measurement still gets refused.

## Acceptance verification

canonical: acceptance: `python3 -m pytest -q gates/test_record_lint.py on-the-record/hooks/test_record_claim_guard.py` — result: PASS

```
$ python3 -m pytest -q gates/test_record_lint.py on-the-record/hooks/test_record_claim_guard.py
................x......................                                  [100%]
38 passed, 1 xfailed
```

full record-lint test suite outcome above (16 pre-existing plus 2 new
tests in gates/test_record_lint.py).

canonical: acceptance: `bash on-the-record/hooks/record-claim-guard.sh` fed the #895-shaped Write payload via stdin — result: PASS

```
$ python3 -c 'import json; print(json.dumps({"tool_name":"Write","tool_input":{"file_path":"docs/issue-923/reports/defect-verification.md","content":"---\nloop_state: landed\n---\n\ncanonical: execution transcript for the ambiguous-scenario run, fixture PR #15 merged 2026-08-05\nambiguous-scenario requirement met: PASS\n"}}))' | bash on-the-record/hooks/record-claim-guard.sh
$ echo EXIT:$?
EXIT:0
```

live-fire re-run of the exact #895 shape through the real PreToolUse
hook outcome above.

canonical: acceptance: `bash on-the-record/hooks/record-claim-guard.sh` fed a bare-file-read-citation Write payload via stdin — result: FAIL

```
$ python3 -c 'import json; print(json.dumps({"tool_name":"Write","tool_input":{"file_path":"docs/issue-923/reports/defect-verification.md","content":"---\nloop_state: landed\n---\n\ncanonical: file read this session, summary only\nambiguous-scenario requirement met: PASS\n"}}))' | bash on-the-record/hooks/record-claim-guard.sh
$ echo EXIT:$?
record-claim-guard: 레코드에 실행-근거 없는 OUTCOME 주장 (issue #870): ...
EXIT:2
```

live-fire re-run of an unbacked claim through the same hook outcome
above still refuses it — the pre-existing catch of a fabricated claim
is unweakened by this change.

## Why

The issue body distinguishes an observation-role verdict, backed by its
own live measurement citation, from an implementation-side delivery
claim needing a live-fire/acceptance marker, and asks that the first
stop being refused without weakening the second. The phase-1 survey
pinned the exact gap and named the seam; this turn implements that
seam, per the explicit instruction to carry out the approved diagnosis
in this same session/branch instead of handing off to a separate turn.

## Upstream basis

- docs/issue-923/reports/defect-verification/current-state.md (this
  role's own approved phase-1 survey)
- docs/issue-923/proposals/defect-verification.md (approved proposal)
- gates/record_lint.py:96-146 (`outcome_claim_citation_check`, issue
  #870)

## Silent-refusal layer

current-state.md's Finding 4 already pinned that the gate's own refusal
carries a printed reason to stderr and a nonzero exit, reaching the
calling model the same turn (shown again in this record's own
acceptance-verification section above). The remaining half named in the
issue — the prior session ending its turn with no PR and nothing
relayed to the human — sits at the session/role-protocol layer, outside
gates/record_lint.py, and outside what this record can re-derive
without that prior session's own transcript; this session's own
start-of-turn `<system-reminder>` blocks already carry an explicit
instruction that a headless/single-shot session must commit before its
turn ends and must never end having delegated unconsumed work, the
standing behavioral answer for that layer. No further code change is
proposed for it here.

## Open findings

None unresolved — the one finding this record raised is resolved in
this same commit.

## What did not work

None.
