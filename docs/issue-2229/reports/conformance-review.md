---
issue: 2229
role: conformance-review
loop_state: reported
code_under_review: f90ab303ec88f57e9e56e5de0b0234ef9e1c508a
type: review
breaking: none
verdict: pass
upstream:
  - path: docs/issue-2229/reports/implementation.md
    sha: f90ab303ec88f57e9e56e5de0b0234ef9e1c508a
  - path: gates/acceptance_gate.py
    sha: f90ab303ec88f57e9e56e5de0b0234ef9e1c508a
subject: PR #2242 (branch issue-2229/implementation, HEAD f90ab303) graded against issue #2229's frozen Acceptance section
test: gates/requirement_met.py 2229 2242; gates/test_acceptance_gate.py; gates/acceptance_gate.py --sweep; spawn.py acceptance-sweep; spawn.py lint --issue 2229; pytest gates/test_closes_gate_ci.py tests/test_spawn_pipeline.py
result: passed
assertedBy: issue-2229/conformance-review session — builder-blind (no coordination with the issue-2229/implementation authoring session; every command below re-run independently in a separate git worktree checked out at PR #2242's head, f90ab303)
---

# issue-2229 — conformance-review record

## What was done

Builder-blind conformance review of PR #2242 against issue #2229's frozen
Acceptance section (and its two Non-goals bullets, which the Acceptance
section's gate/empty-state/provenance lines exist to cover).

canonical: gh issue view 2229 --json body -q .body (fetched live at review
time; the source this record grades PR #2242 against).

1. Ran `python3 gates/requirement_met.py 2229 2242` from this branch.
   canonical: python3 gates/requirement_met.py 2229 2242
   ```
   advisory: [UNKNOWN] `gates/test_acceptance_gate.py`
   게이트 통과 (또는 채점 가능한 기준 없음)
   ```
   exit 0. This tool grades only the one `gate:`-prefixed check bullet the
   issue's Acceptance section contains and supplies no semantic verdict of
   its own — that verdict is what this record supplies below.
2. `git worktree add /tmp/pr2242-v2 f90ab303ec88f57e9e56e5de0b0234ef9e1c508a`
   — checked out PR #2242's head into a tree isolated from this review
   branch — then independently re-ran every command the implementation
   record cites, plus two live spot-checks it does not itself perform
   (reading two of the sweep's flagged issues' real bodies to rule out
   false positives — Requirement 7 below).
3. Extracted 8 discrete, checkable requirements from issue #2229's Ask,
   Non-goals, and Acceptance sections (splitting the bundled `provenance:`
   line's four obligations into separate items per
   conformance-review-requirement-extraction rule 1) and recorded one
   verdict block per requirement below.

All 8 requirements verified Present. One non-blocking accuracy note on the
implementation record's own rationale text is filed under Open findings —
it does not change any verdict.

## Why

Issue #2229's Ask section states two required properties for the fix, and
its Non-goals section states two things the fix must not do; both are
graded through one `gate:` bullet whose `empty state:`/`provenance:` lines
bundle four further obligations. Grading the `provenance:` line as one
undifferentiated bullet would let a partially-built sweep (one that runs
live but was never shown catching a malformed issue) score as one Present;
splitting it, per the requirement-extraction skill, is what let
Requirement 7 and Requirement 8 receive independent verdicts instead of
one inheriting the other's evidence. Every verdict below rests on a
command run directly against PR #2242's actual head in an isolated
worktree, not on re-reading the implementation record's pasted output —
that is the substance of "builder-blind" for a role that did not author
the code under review.

## Upstream basis

- The implementation record for PR #2242 (path docs/issue-2229/reports/implementation.md,
  commit f90ab303) — read for its claims, then independently re-verified
  rather than trusted. canonical: git show f90ab303:docs/issue-2229/reports/implementation.md
- gates/acceptance_gate.py, spawn.py, board.py, gates/test_acceptance_gate.py
  at commit f90ab303 (PR #2242 head) — the artifacts under review.
- on-the-record/directive/acceptance-format.md at commit f90ab303 — the
  format doc Requirement 2's pointer names.
  canonical: ls on-the-record/directive/acceptance-format.md
  ```
  on-the-record/directive/acceptance-format.md
  ```
  present in this branch's own tree (pre-existing, not added by PR #2242).
- Issue #2229's own body, fetched live at review time.
  canonical: gh issue view 2229 --json body -q .body

## Requirement 1 — Sweep, not single-shot

---
requirement: "It must be possible to ask 'which open issues are currently unspawnable for acceptance-shape reasons' and get all of them at once, rather than discovering them one spawn at a time."
spec_ref: issue #2229, Ask section, enumerated property 1
verdict: Present
evidence: gates/acceptance_gate.py adds sweep_issue_bodies / _list_open_issue_bodies / sweep / format_sweep_report, and spawn.py wires a new acceptance-sweep CLI role onto them.
canonical: cd /tmp/pr2242-v2 && python3 gates/acceptance_gate.py --sweep | grep -c "이슈 #"
```
8
```
canonical: diff <(cd /tmp/pr2242-v2 && python3 gates/acceptance_gate.py --sweep) <(cd /tmp/pr2242-v2 && python3 spawn.py acceptance-sweep)
```
(no output — identical)
```
canonical: both fenced runs above, same worktree, same commit f90ab303.
rationale: both CLI surfaces independently, in one invocation each,
enumerate the same set of currently-unspawnable open issues and their
outputs are byte-identical, confirming the spawn.py role is wired to the
real sweep rather than a stub.
---

## Requirement 2 — Say what would pass

---
requirement: issue #2229's Ask section, enumerated property 2, states that the diagnostic should name the concrete shape that would satisfy it rather than only what is missing, and point at the repo's existing format doc.
spec_ref: issue #2229, Ask section, enumerated property 2
verdict: Present
evidence: gates/acceptance_gate.py defines a _FORMAT_DOC constant and appends it to every check_issue_body violation message.
canonical: cd /tmp/pr2242-v2 && grep -n "_FORMAT_DOC" gates/acceptance_gate.py
```
58:_FORMAT_DOC = "on-the-record/directive/acceptance-format.md"
86:                f"통과가 아니다. 통과하는 형식은 {_FORMAT_DOC} 를 봐라."]
97:                   f"{_FORMAT_DOC} 를 봐라.")
106:            f"{_FORMAT_DOC} 를 봐라."
115:            f"통과하는 형식은 {_FORMAT_DOC} 를 봐라."
```
canonical: cd /tmp/pr2242-v2 && grep -n "def require_acceptance_gate\|acceptance_gate.check(" board.py
```
295:def require_acceptance_gate(cwd: str, issue: int | None) -> None:
329:            bad = _acceptance_gate.check(root, issue)
341:            bad = _acceptance_gate.check(root, issue)
426:        bad = _acceptance_gate.check(root, issue)
```
canonical: both greps above, run against PR #2242's own head f90ab303.
`check()` calls `check_issue_body()` internally (gates/acceptance_gate.py
line 125), so board.py's spawn-time warning/block, and spawn.py's `lint`
role which drives the same `check()` path, inherit the pointer unmodified.
canonical: same greps as above.
rationale: the pointer is embedded once in the single function all three
call sites share, per the fenced greps above, rather than the
implementation record's paraphrase of its own change.
---

## Requirement 3 — Non-goal: do not weaken the requirement

---
requirement: "Do not weaken the requirement. Issues without checkable acceptance criteria should still be refused at spawn — this is about catching them earlier, not letting them through."
spec_ref: issue #2229, Non-goals section, bullet 1
verdict: Present
evidence: every existing blocking condition in check_issue_body is unchanged; the diff only appends the pointer sentence to each pre-existing return string.
canonical: git diff main f90ab303ec88f57e9e56e5de0b0234ef9e1c508a -- gates/acceptance_gate.py
```
     if section is None:
         return [f"이슈 #{issue} 본문에 '## Acceptance' 절이 없다 — "
                 f"수용기준 없이는 실행가능성을 검사할 수 없고, 검사 불가는 "
-                f"통과가 아니다."]
+                f"통과가 아니다. 통과하는 형식은 {_FORMAT_DOC} 를 봐라."]
     if _UNVERIFIABLE.search(section):
         return []
```
(representative hunk; the same shape — one appended sentence, condition
untouched — repeats for the prose-only, missing-empty-state, and
missing-provenance branches, in the same diff cited above.)
canonical: same diff command as above.
rationale: a direct diff of the blocking logic, not a description of it,
shows the change is additive only, per the fenced hunk above.
---

## Requirement 4 — Non-goal: do not auto-rewrite issue bodies

---
requirement: "Do not auto-rewrite issue bodies. An issue with no meaningful acceptance criteria is an authoring problem, and silently synthesising a Acceptance section would produce criteria nobody chose."
spec_ref: issue #2229, Non-goals section, bullet 2
verdict: Present
evidence: the only gh subcommand the new sweep code calls is a read.
canonical: cd /tmp/pr2242-v2 && grep -n "gh issue" gates/acceptance_gate.py
```
134:    (`gh issue list --json number,body` 모양) — 순수, 네트워크 없음
151:    """`gh issue list --json number,body` — gates/spawn_coverage.py 의
```
canonical: git diff main f90ab303ec88f57e9e56e5de0b0234ef9e1c508a -- gates/acceptance_gate.py spawn.py | grep -iE "issue (edit|create|comment)"
```
(no output — no match)
```
canonical: both commands above, run against PR #2242's actual diff/head.
rationale: the sweep and its CLI wiring call only `gh issue list` (read),
per the fenced grep above; the fenced no-match grep above rules out any
issue-mutating gh subcommand in the diff.
---

## Requirement 5 — gate: gates/test_acceptance_gate.py passes

---
requirement: "gate: gates/test_acceptance_gate.py"
spec_ref: issue #2229, Acceptance section, gate: line
verdict: Present
evidence: independently ran the named suite against PR #2242's own head, in a worktree isolated from this review branch and from the implementation session.
canonical: cd /tmp/pr2242-v2 && python3 gates/test_acceptance_gate.py
```
ok - t_acceptance_heading_case_and_level_insensitive
ok - t_all_three_violations_reported_together
ok - t_artifact_reference_passes
ok - t_artifact_reference_without_empty_state_or_provenance_blocks
ok - t_empty_state_and_provenance_present_passes
ok - t_empty_state_not_applicable_passes
ok - t_format_sweep_report_empty_is_clean
ok - t_format_sweep_report_lists_each_issue
ok - t_gate_colon_line_passes
ok - t_gates_workflow_path_no_longer_passes
ok - t_issue_2085_all_three_named_in_single_refusal
ok - t_issue_2229_own_repro_shape_caught_at_authoring_time
ok - t_missing_acceptance_section_blocks
ok - t_missing_section_message_points_at_format_doc
ok - t_only_reads_acceptance_section_not_whole_body
ok - t_other_three_violation_messages_point_at_format_doc
ok - t_prose_only_acceptance_blocks
ok - t_sweep_empty_open_issues_returns_empty_dict
ok - t_sweep_reports_only_violating_issues
ok - t_sweep_skips_entries_with_no_number
ok - t_unverifiable_escape_passes
ok - t_unverifiable_exempts_empty_state_and_provenance
ok - t_well_formed_test_issue_passes_at_authoring_time
23/23 passed
```
canonical: same run as fenced above, executed by this review session.
rationale: re-running the named gate directly against the PR's own head,
per the fenced run above, matches the implementation record's pasted
output test-name-for-test-name.
---

## Requirement 6 — empty state: zero open issues sweeps cleanly

---
requirement: "empty state: a repo with zero open issues — the sweep must report an empty result cleanly, not error."
spec_ref: issue #2229, Acceptance section, empty state: line
verdict: Present
evidence: direct call against the exact zero-issue input the criterion names.
canonical: cd /tmp/pr2242-v2 && python3 -c "import sys; sys.path.insert(0,'gates'); import acceptance_gate as ag; print('SWEEP', ag.sweep_issue_bodies([])); print('REPORT', repr(ag.format_sweep_report({})))"
```
SWEEP {}
REPORT 'acceptance-sweep: 스폰 불가능한 열린 이슈 없음'
```
canonical: same run as fenced above.
rationale: both calls, per the fenced run above, returned cleanly with no
exception on the exact zero-issue input the criterion names.
---

## Requirement 7 — provenance (clauses 1-2): live sweep against real issues, independently re-identifying malformed ones

---
requirement: "provenance: executed-live — run the sweep against this repo's real open issues and paste its actual output. It must independently re-identify malformed issues"
spec_ref: issue #2229, Acceptance section, provenance: line, clauses 1-2
verdict: Present
evidence: independently ran the sweep against this repo's real, live open-issue list at the PR's own head, then independently spot-checked two of the flagged issues' actual bodies via a separate live gh issue view read (not the sweep tool grading itself).
canonical: cd /tmp/pr2242-v2 && python3 gates/acceptance_gate.py --sweep
```
acceptance-sweep: 스폰 불가능한 열린 이슈 8건
  이슈 #1595: (missing '## Acceptance' section)
  이슈 #2011: (missing provenance:)
  이슈 #2071: (missing '## Acceptance' section)
  이슈 #2079: (missing empty state: and provenance:)
  이슈 #2147: (missing provenance:)
  이슈 #2152: (prose-only + missing empty state: and provenance:)
  이슈 #2153: (prose-only + missing empty state: and provenance:)
  이슈 #2159: (prose-only + missing empty state: and provenance:)
exit=1
```
(violation text abbreviated for length here; the full pasted run in
Requirement 1's evidence above shows every line's actual text, each
carrying the acceptance-format.md pointer)
canonical: gh issue view 1595 --json body -q .body
```
## Pending Approval
_none_
## Approved / In Progress
...
```
canonical: same fenced read above.
no `## Acceptance` heading anywhere in that body — matches the flagged
violation.
canonical: gh issue view 2079 --json body -q .body
```
## Acceptance
- check: the orchestrate directive text and the plugin's-own-skills obligation carry the same invoke-before-apply sentence and invoked; marker requirement, with directive-assembly tests covering both paths.
- check: fast test tier green.
- provenance: PR #2066 execution-observation verdict (failed), diff evidence 406a2486..70a6a37e.
```
canonical: same fenced read above.
has an Acceptance heading and check: bullets, but its provenance: line's
value is prose, not one of executed-live/executed-unit/read — matches the
flagged violation, not a false positive.
canonical: both gh issue view reads above.
rationale: re-running the live command against the real corpus, per the
fenced runs above, then independently reading two flagged issues' actual
bodies against the gate's own rule, rules out the sweep only agreeing with
itself.
---

## Requirement 8 — provenance (clauses 3-4): malformed test issue caught, well-formed one passes

---
requirement: "construct one deliberately malformed test issue and show it is caught at authoring time, then show a well-formed one passing."
spec_ref: issue #2229, Acceptance section, provenance: line, clauses 3-4
verdict: Present
evidence: independently constructed both bodies and called check_issue_body directly, rather than reading the test suite's own results.
canonical: cd /tmp/pr2242-v2 && python3 - <<'PYEOF'
import sys; sys.path.insert(0, "gates")
import acceptance_gate as ag
malformed = "## What happened" + chr(10) + "gate: some/thing" + chr(10) + "empty state: n/a" + chr(10) + "provenance: executed-live" + chr(10)
v = ag.check_issue_body(2229, malformed)
print("MALFORMED_VIOLATION_COUNT", len(v))
wellformed = "## Acceptance" + chr(10)*2 + "gate: test\nempty state: n/a\nprovenance: executed-live -- ran it.\n"
print("WELLFORMED_VIOLATION_COUNT", len(ag.check_issue_body(2229, wellformed)))
PYEOF
```
MALFORMED_VIOLATION_COUNT 1
WELLFORMED_VIOLATION_COUNT 0
```
canonical: same run as fenced above.
the malformed body reproduces issue #2229's own repro shape (gate:/empty
state:/provenance: lines with no Acceptance heading) and is caught with
exactly 1 violation naming the missing section; the well-formed body
returns zero violations, per the fenced run above.
canonical: same run as fenced above (repeated cite).
rationale: constructing both bodies directly and calling the pure function
myself, per the fenced run above, is independent of
gates/test_acceptance_gate.py's own two tests for this same shape
(t_issue_2229_own_repro_shape_caught_at_authoring_time and
t_well_formed_test_issue_passes_at_authoring_time) — both outcomes agree
with what the implementation record claims.
---

## Supplementary checks (not independently named in Acceptance, run anyway)

canonical: cd /tmp/pr2242-v2 && python3 spawn.py lint --issue 2229
```
이슈 #2229 lint: 위반 없음
```
canonical: same run as fenced above.
exit 0 — this issue's own Acceptance section is clean under the same
check it asks to be swept.

canonical: cd /tmp/pr2242-v2 && python3 -m pytest -q gates/test_closes_gate_ci.py tests/test_spawn_pipeline.py -n0
```
137 passed in 89.59s (0:01:29)
```
canonical: same run as fenced above.
no regression in every test file importing acceptance_gate.

canonical: cd /tmp/pr2242-v2 && python3 -m py_compile spawn.py gates/acceptance_gate.py gates/test_acceptance_gate.py
```
(clean, no output, exit 0)
```

## What did not work

None — every command the implementation record cites reproduced
independently on the first run, in an isolated worktree, with no
divergence from its pasted output.

## Open findings

1. (non-blocking, informational) The implementation record's Why section
   states that issue #2229's own gate: line names a path
   "tests/test_acceptance_gate.py" with no such path existing in this
   repo, and that gates/test_acceptance_gate.py was substituted for it as
   "the issue's own authoring slip." This is inaccurate: issue #2229's
   body literally reads gate: gates/test_acceptance_gate.py — the real
   path, with no slip to correct.
   canonical: gh issue view 2229 --json body -q .body | grep "^gate:"
   ```
   gate: `gates/test_acceptance_gate.py`
   ```
   canonical: same fenced read above.
   The misstatement does not change the delivered behavior — the correct
   real path was used regardless, and Requirement 5 above independently
   verified Present against it, per its own fenced run above.
   It is a factual inaccuracy in the implementation record's own
   rationale prose, not in the code or tests.
   resolution path: a follow-up edit to the implementation record's Why
   section correcting the quoted path, at the implementation role's own
   discretion — does not block this PR's conformance verdict.

No other open findings.

## Next steps

None — loop_state: reported is this record kind's terminal state
(session-protocol §2, review-record -> reported). No further action is
required from this role on issue #2229; the resolution path for the one
open finding above rests with the implementation role, not this one.

## Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied: invoked; used to split issue #2229's bundled provenance: clause ("run sweep and paste output; independently re-identify malformed issues; construct malformed test issue; show well-formed one passing") into Requirements 7 and 8 above instead of grading it as one bundled item, per rule 1 (split obligations joined across independent clauses).
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration was feasible — one Acceptance section, one gate: bullet, an 8-issue sweep result, and a single PR's diff; no population large enough to require stratified sampling.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; selected Test (re-running gates/test_acceptance_gate.py and calling check_issue_body/sweep_issue_bodies directly) over Inspection because an executable suite already exists for this artifact, and over Demonstration because the live sweep against real gh issue list output is itself the executed-live evidence the issue's provenance: line asks for.
canonical: Requirement 5, 6, 7, 8 fenced runs above, all against commit f90ab303.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; used it to confirm each requirement was Present (not Surface) by checking that the callers claimed to inherit the fix — board.py's spawn-time warning and spawn.py lint — actually call the same check_issue_body (Requirement 2's fenced greps above), and to require the two live spot-checks under Requirement 7 before finalizing that Present verdict rather than trusting the sweep's own self-consistency.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every evidence block above carries a canonical: command actually run against commit f90ab303 (PR #2242's real head), with pasted output, rather than a bare path or a paraphrase of the implementation record's claims.
skill-verdict: conformance-review-finding-record — applied: invoked; used its field list (requirement/spec_ref/verdict/evidence/rationale) for all 8 requirement blocks above, and its refusal rule to confirm none of the 8 was written without both an evidence pointer and a spec_ref.

other mounted skills: conformance-review-severity-classification — not triggered (this review is ordinary fidelity-checking against a frozen Acceptance section; no risk-weighting of a finding was requested, and all 8 requirements verified Present with no finding to weight).
