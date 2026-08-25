---
issue: 2295
role: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2295/reports/observability.md
    sha: e8b949219046d58d52a29a877be4015c22189e43
subject: "PR #2307 (branch issue-2295/observability, commit e8b94921) — \"issue-2295: fix silent packaged-gate-copy drift and gate-CLI argv crashes\""
test: "issue #2295 ## Acceptance — gate / empty state / provenance clauses"
result: failed
assertedBy: conformance-review session, branch issue-2295/conformance-review
---

# issue-2295 — conformance-review record

## What was done

Builder-blind conformance review of PR #2307 against issue #2295's frozen
`## Acceptance` section (gate / empty-state / provenance clauses), with
the task's own framing emphasizing the empty-state clause ("clean areas
stated explicitly"). Re-executed every check the PR's record claims
independently, rather than trusting the pasted output, against the PR's
exact commit checked out in an isolated worktree.

canonical: gh pr view 2307 --json title,body,files,commits — result:
head commit e8b949219046d58d52a29a877be4015c22189e43, branch
issue-2295/observability, "Closes #2295" in body, files listed include
`docs/issue-2295/reports/observability.md` (ADDED — untracked on this
review's own branch, issue-2295/conformance-review; PR #2307's record is
read throughout this document via `git show <sha>:<path>` against branch
issue-2295/observability, never as a local path on this branch), 3
packaged-copy gate files (MODIFIED), 14 `gates/*.py` CLI files
(MODIFIED), `on-the-record/hooks/test_hook_cache_layout.py` (MODIFIED).

canonical: gh issue view 2295 --json title,body,state — result: OPEN,
`## Acceptance` reads: `gate: on-the-record/hooks/test_hook_cache_layout.py`
/ `empty state: a repo area with zero findings — stated explicitly as
swept-and-clean with the sweep method shown, never silently omitted.` /
`provenance: executed-live — every claimed silent-failure point
demonstrated by actually driving the failure and showing what the
consumer sees (or fails to see); paste real output per finding.`

derived: git fetch origin issue-2295/observability && git worktree add
/tmp/pr2307-review FETCH_HEAD; git rev-parse FETCH_HEAD — result:
worktree created at e8b949219046d58d52a29a877be4015c22189e43, confirmed
identical to the PR API's `commits[0].oid` cited above — this is PR
#2307's exact head commit, not an approximation.

## Why

The task named the empty-state clause specifically, so this review reads
it literally and checks whether the PR's record actually discloses
zero-finding areas explicitly with method shown — and verifies the
disclosure's own supporting citations against the real file rather than
accepting them on the record's word. The same executed-live standard the
issue imposes on the builder ("paste real output per finding") is applied
here to the builder's own record: every claim below was re-run this
session, not re-read.

## Findings

### R1 — gate: `on-the-record/hooks/test_hook_cache_layout.py` passes

requirement: "gate: `on-the-record/hooks/test_hook_cache_layout.py` passes"
spec_ref: "issue #2295 body, `## Acceptance`, `gate:` line"
verdict: Present
evidence: on-the-record/hooks/test_hook_cache_layout.py (full file),
commit e8b949219046d58d52a29a877be4015c22189e43

acceptance: python3 -m pytest on-the-record/hooks/test_hook_cache_layout.py -q
(run in /tmp/pr2307-review, commit e8b949219046d58d52a29a877be4015c22189e43) — result:
```
7 passed in 0.89s
```

rationale: matches PR #2307's own test-plan line verbatim; the named
gate passes, reproduced independently in this session, not accepted from
the pasted transcript alone.

### R2 — empty state: zero-finding areas stated explicitly with sweep method shown

requirement: "empty state: a repo area with zero findings is stated
explicitly as swept-and-clean with the sweep method shown, never
silently omitted"
spec_ref: "issue #2295 body, `## Acceptance`, `empty state:` line"
verdict: Present
evidence: on-the-record/hooks/pretooluse_dispatcher.py:161-233,250-303,352,
commit e8b949219046d58d52a29a877be4015c22189e43 (cited by PR #2307's
record for its zero-finding disclosure)

canonical: git show e8b949219046d58d52a29a877be4015c22189e43:docs/issue-2295/reports/observability.md
— result: "Open findings" item 2 states "no finding, ruled out by
trace-forward rather than assumed clean" for the PreToolUse dispatcher's
fail-open/setup-skip paths, citing
`on-the-record/hooks/pretooluse_dispatcher.py:352` and the `GATES` table
at `:250` through `:303`.

acceptance: grep -n "^GATES = \[\|^]$" on-the-record/hooks/pretooluse_dispatcher.py
(run in /tmp/pr2307-review, commit e8b949219046d58d52a29a877be4015c22189e43) — result:
```
250:GATES = [
303:]
```

acceptance: sed -n '352p' on-the-record/hooks/pretooluse_dispatcher.py
(same worktree/commit) — result:
```
    if setup is not None and not setup(payload, env):
```

acceptance: grep -n '^def _env_contract\|^def _env_cng\|^def _env_crg\|^def _env_rcg\|^def _pre_approval' on-the-record/hooks/pretooluse_dispatcher.py
(same worktree/commit) — result:
```
161:def _env_contract(payload, env):
212:def _env_cng(payload, env):
217:def _env_crg(payload, env):
222:def _env_rcg(payload, env):
233:def _pre_approval(payload, env):
```
All five citations land exactly where the record says; reading each
function body (same commit) confirms `_env_contract`, `_env_cng`,
`_env_crg`, `_env_rcg` each unconditionally `return True`, and
`_pre_approval` gates on `os.environ.get("CLAUDE_ROLE", "")`, matching
the record's "documented preamble-mirror of approval-gate.sh's own
`[ -n \"${CLAUDE_ROLE:-}\" ] || exit 0`" description.

rationale: this is exactly what the clause requires — a swept area with
zero findings, stated as such explicitly rather than folded silently
into a generic scope note, with a method a reader can re-derive — and
every citation this disclosure rests on independently checks out
(contrast R4 below, where a different disclosure's citations do not).

### R3 — provenance: primary findings demonstrated live, real output pasted

requirement: "provenance: every claimed silent-failure point demonstrated
live — actually driving the failure and showing what the consumer sees —
with real output pasted per finding"
spec_ref: "issue #2295 body, `## Acceptance`, `provenance:` line"
verdict: Present
evidence: on-the-record/gates/{role_spec_shape,gates,record_lint}.py,
gates/design_research_consult.py, on-the-record/hooks/test_hook_cache_layout.py:22-70,
commit e8b949219046d58d52a29a877be4015c22189e43

acceptance: diff -q on-the-record/gates/role_spec_shape.py gates/role_spec_shape.py && diff -q on-the-record/gates/gates.py gates/gates.py && diff -q on-the-record/gates/record_lint.py gates/record_lint.py; echo "exit:$?"
(run in /tmp/pr2307-review, commit e8b949219046d58d52a29a877be4015c22189e43) — result:
```
exit:0
```
(all three packaged copies byte-identical to their source-of-truth
counterparts, post-fix, no diff output).

acceptance: python3 gates/design_research_consult.py abc
(same worktree/commit) — result:
```
usage: design_research_consult.py <issue-number> [--repo <경로>] — issue-number must be an integer, got 'abc'
rc=1
```
(clean usage message, no traceback — matches the PR record's pasted
post-fix output for Finding 2).

acceptance: python3 -m pytest gates/ -q
(same worktree/commit) — result:
```
964 passed, 8 xfailed in 215.12s (0:03:35)
```
(exact match to PR #2307's own test-plan line).

acceptance: python3 -c "import re,pathlib; print(sum(1 for f in pathlib.Path('gates').glob('*.py') if not f.name.startswith('test_') and re.search(r'int\(sys.argv\[', f.read_text())))"
(same worktree/commit) — result:
```
15
```
(14 fixed by this PR + `gates/check_runner.py`, confirmed still present
and unguarded at this commit via `grep -n 'int(sys.argv' gates/check_runner.py`
→ line 377 — left out of scope, as the record states, because it is
issue #2278's already-audited exemplar).

canonical: on-the-record/hooks/test_hook_cache_layout.py:22-70 (same
commit) — result: `test_packaged_gates_copy_matches_source_of_truth` is a
real byte-compare of the three synced files (not a string-length check or
a mock), and
`test_packaged_gates_copy_drift_check_actually_catches_drift` seeds one
drifted byte into a `tmp_path` copy and asserts inequality — a genuine
live-fire self-test of the drift check, not a vacuous pass.

rationale: every primary finding's before/after behavior, the regression
test's own live-fire proof, and the numeric derivations were
independently re-executed this session and matched the record's pasted
output exactly — executed-live provenance for the two things the PR
actually built and claims fixed.

### R4 — supporting citations must be re-derivable (traceability rule 1)

requirement: "a finding's supporting citations must be accurate enough
for a reader to re-derive them (traceability-and-evidence rule 1: cite
file:line the reviewer actually read)"
spec_ref: "issue #2295 body, `## Acceptance`, `provenance:` line
(traceability sub-requirement); conformance-review-traceability-and-
evidence rule 1"
verdict: Incorrect
evidence: gates/check_runner.py:179,180,198,214,215,233,342,377, commit
e8b949219046d58d52a29a877be4015c22189e43

canonical: git show e8b949219046d58d52a29a877be4015c22189e43:docs/issue-2295/reports/observability.md
— result: Finding 2's "canonical" line reads "gates/check_runner.py:179
and gates/check_runner.py:198 — `\"status\": \"pass\" if r.returncode ==
0 else \"fail\"`", separately "canonical: gates/check_runner.py:342" for
the `int(sys.argv[...])` pattern, and a fourth citation in the same
paragraph, "captured output is `(r.stdout + r.stderr)[-2000:]` at
gates/check_runner.py:180".

acceptance: awk 'NR==179||NR==180||NR==198||NR==342{print NR": "$0}' gates/check_runner.py
(run in /tmp/pr2307-review, commit e8b949219046d58d52a29a877be4015c22189e43) — result:
```
179: 오늘의 경로로 떨어진다(fail-open — 여기서 막을 일이 아니다)."""
180:     try:
198: for chk in checks:
342: def remove_worktree(repo: Path, worktree: Path) -> None:
```

acceptance: grep -n 'status.*pass.*if r.returncode\|int(sys.argv\|r.stdout + r.stderr' gates/check_runner.py
(same worktree/commit) — result:
```
214:                status = "pass" if r.returncode == 0 else "fail"
215:                output = (r.stdout + r.stderr)[-2000:]
233:                "status": "pass" if r.returncode == 0 else "fail",
377:    pr, issue = int(sys.argv[1]), int(sys.argv[2])
```

Initial pass under this same review missed the `:180` citation — the
grep pattern first used to enumerate offsets (`'status.*pass.*if
r.returncode\|int(sys.argv'`) structurally cannot match the captured-
output line, so the citation-accuracy check itself under-counted its own
defect class on the first attempt; caught by a background warrant-hunter
probe run before landing this record (see "What did not work" note
below) and folded back into this same R4 block rather than filed as a
separate, later requirement.

spec_vs_built: spec requires (provenance clause, read with traceability
rule 1) that a citation point a reader at the actual line the reviewer
read. What was built instead points a reader, four times in the same
paragraph at a consistent +35-line offset, at unrelated code (a
docstring's closing line, a bare `try:`, a `for` loop header, an
unrelated function's `def` line) rather than the exit-code-consumer
pattern, the captured-output slice, and the argv-parse line the prose
describes. `gates/check_runner.py` is not in PR #2307's changed-file
list (confirmed under "What was done"), so the file was not edited
mid-session in a way that could explain a shifting line count.

rationale: re-checked once against the current artifact state before
finalizing (verdict-assignment rule 6) — the +35 offset is exact and
consistent across all four references, not a one-off misread. This does
not undermine either primary finding's own live-demonstrated evidence
(both independently reconfirmed correct under R3 above); it is a narrow,
reproducible defect in four supporting "canonical" citations used to
argue `check_runner.py`'s real-consumer-impact claim. Scored Incorrect
rather than Absent because the citations actively point at specific,
wrong content rather than merely omitting a citation.

## What did not work

R4's first-pass grep pattern (`'status.*pass.*if r.returncode\|int(sys.argv'`)
enumerated only two of the three prose phrases Finding 2's citation
paragraph actually names line numbers for.

derived: git show e8b949219046d58d52a29a877be4015c22189e43:docs/issue-2295/reports/observability.md
| sed -n '221,226p' — result: the paragraph also cites "captured output
is `(r.stdout + r.stderr)[-2000:]` at gates/check_runner.py:180", a
fourth line reference the first-pass grep pattern has no clause capable
of matching (`r.stdout + r.stderr` shares no substring with either
alternation branch).

acceptance: sed -n '180p' gates/check_runner.py; grep -n 'r.stdout + r.stderr' gates/check_runner.py
(run in /tmp/pr2307-review, commit e8b949219046d58d52a29a877be4015c22189e43) — result:
```
    try:
215:                output = (r.stdout + r.stderr)[-2000:]
```
Same +35 offset as the other three (180+35=215) — a fourth instance of
R4's own defect class that R4's first-pass method could not have found,
regardless of how carefully the three already-found offsets were
re-checked. Surfaced by a background warrant-hunter probe run
synchronously against this same commit before this record was landed,
then folded back into R4 above (not filed as a separate later finding,
since it is the same defect class, same offset, same underlying cause —
Finding 2's citation paragraph never getting a fully enumerated pass —
as the other three).

## Upstream basis

- PR #2307's own delivered record — untracked on this branch
  (issue-2295/conformance-review); read throughout this document via
  `git show e8b949219046d58d52a29a877be4015c22189e43:docs/issue-2295/reports/observability.md`
  against branch issue-2295/observability, never as a local path here
  (see "What was done" and the frontmatter `upstream:` entry above).
- Issue #2295 body, read via `gh issue view 2295` (see "What was done")
  — the frozen `## Acceptance` text this review checks against.

## Open findings

1. **Citation defect in Finding 2's supporting evidence** (R4's
   `Incorrect` verdict above).

   derived: the four offsets computed directly from the `awk`/`grep`
   results cited under R4 (179→214 = +35, 180→215 = +35, 198→233 = +35,
   342→377 = +35) — result: a single, consistent +35-line shift across
   all four citations.

   Resolution path: the PR author corrects the four
   `gates/check_runner.py` line citations in the observability record
   (`:179`→`:214`, `:180`→`:215`, `:198`→`:233`, `:342`→`:377`); low
   severity — does not require re-verifying either of the two primary
   findings, both independently reconfirmed correct under R3.

2. **Cross-repo scope — flagged during review, reconciled before landing
   this record.**

   canonical: gh issue view 2295 --json body — result: `## Program`
   states "Sweep **all three repos** — on-the-record, tokenmaxxxer-core,
   skill-repository".

   canonical: git show e8b949219046d58d52a29a877be4015c22189e43:docs/issue-2295/reports/observability.md
   — result: header states "Repo scope for this session: ON-THE-RECORD
   only ... the parent issue #2295 also names tokenmaxxxer-core and
   skill-repository, out of scope here — presumably swept by sibling
   sessions" (the record's own word "presumably" — unconfirmed by that
   record itself).

   amendments-reconciled: issuecomment-5404767770 — gh api
   repos/:owner/:repo/issues/2295/comments --jq '.[] | select(.id ==
   5404767770)' — result: issue #2295 comment
   [issuecomment-5404767770](https://github.com/tokenmaxxxer/on-the-record/issues/2295#issuecomment-5404767770)
   (posted 2026-08-25T03:39:07Z, after this review session started),
   quoted verbatim:
   ```
   Program status: all three repo sweeps delivered and landed.
   on-the-record -> PR #2307 (2 structural fixes included: packaged-gate
   drift + 14 CLI tracebacks; observers grading). tokenmaxxxer-core ->
   PR #302 merged: 31/31 files audited, 23 findings, fix issues filed
   per its own batching -- core#303 (gate-bypass, secure-coding session
   running), core#304 (kill-switch propagation), core#305 (remainder).
   skill-repository -> PR #112 merged: 5 findings, fix issues skill#113
   (F5+F1 root-cause wiring, session running), skill#114 (F2 verdict
   glob), skill#115 (F3+F4). This issue stays open until the filed fix
   issues close.
   ```
   This resolves the "presumably" from this review's own vantage point
   (still outside this session's checkout/access, so not independently
   re-verified against the core and skill-repository repos themselves —
   the operator's own status comment is the evidence here, not this
   review's execution) — cross-repo scope was in fact delivered, not
   silently dropped by sibling sessions, and the operator's own comment
   states the parent issue #2295 stays open on purpose until the filed
   fix issues close, not blocked on this PR's merge.

   This review's task explicitly scoped it to the gate/empty-state/
   provenance clauses, so cross-repo scope is still not scored as a
   fifth requirement above; flagged here so it is not silently dropped —
   the same never-silently-omit standard this review just checked the
   builder against under R2.

   Resolution path: none outstanding on cross-repo scope itself (all
   three repos confirmed swept per the operator's comment above); PR
   #2307's own "Closes #2295" trailer is procedurally valid under the
   build-now bypass, and per the operator's own comment issue #2295 is
   expected to stay open regardless until core#303-305 and skill#113-115
   close — a separate, already-tracked condition this review has no new
   information on.

skill-verdict: conformance-review-requirement-extraction — applied:
invoked; used to decompose issue #2295's `## Acceptance` text into the
four discrete, checkable requirement blocks (R1-R4) above before
rendering any verdict.
skill-verdict: conformance-review-verification-method-selection —
applied: invoked; selected Test (re-running the PR's own pytest gate and
CLI commands in an isolated worktree at the PR's exact commit) over
Inspection for all four requirements, since each had an existing,
replayable command rather than only a static property to read.
skill-verdict: conformance-review-verdict-assignment — applied: invoked;
used the Incorrect-vs-Absent distinction (rule 2) to score the
`check_runner.py` citation defect (R4) as Incorrect — the citations point
at real, wrong content rather than omitting a citation — and re-checked
that evidence once against the artifact (rule 6) before finalizing.
skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; every requirement's evidence is pinned to file:line-range plus
the exact commit sha read (rule 1); its rule 1 is specifically what
surfaced R4 — re-deriving the record's own citations against the
artifact rather than accepting them as written.
skill-verdict: conformance-review-finding-record — applied: invoked;
wrote the four requirement blocks (R1-R4) above with
requirement/spec_ref/verdict/evidence/rationale (+`spec_vs_built` for
R4's `Incorrect` verdict) fields; no verdict was written without both an
evidence pointer and a `spec_ref`.
other mounted skills: not triggered — conformance-review-sampling-
derivation (full enumeration of the frozen Acceptance's clauses plus PR
#2307's own two findings was directly feasible; no sampling scope was
needed), conformance-review-severity-classification (this review's scope
was not explicitly extended into risk-weighting a recorded finding),
implementation-audit (this session already runs the role-handoff
contract's own builder-blind review; the separate two-session
Implementation Audit protocol was not separately invoked), and the
remaining mounted skills (freelunch fan-out, terse, dataviz, code-review,
run, init, security-review, etc.) do not match this task's shape.

## Next steps

None further for this record — `loop_state` is terminal (`reported`).
Open findings 1 and 2 above are handoffs to the PR author / issue owner,
not further conformance-review work in this session.
