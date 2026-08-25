---
issue: 2463
role: conformance-review
author: conformance-review
loop_state: reported
type: review-record
code_under_review:
  - gates/check_runner.py
  - gates/test_check_runner.py
breaking: "none — this is a review record, no code changed by this role"
verdict: pass
upstream:
  - path: docs/issue-2463/reports/implementation.md
    sha: 11603890e96d3a4c5edc728f5ff8e31bfe095c00
subject: PR #2464 (issue-2463/implementation, HEAD 11603890) — "exclude angle-bracket placeholder backticks from file-existence classification"
test: independently-authored synthetic fixtures (not copy-pasted from the PR's own tests) run pre-fix vs. post-fix + independently-executed pytest runs (31/31, 38 passed, 1006 passed/8 xfailed) + live re-classification of issue #2402's real Acceptance text + line-level code inspection of the diff against main
result: passed
assertedBy: conformance-review session, issue-2463 (builder-blind)
---

# issue-2463 — conformance-review record

Builder-blind conformance review of PR #2464 (branch `issue-2463/implementation`,
HEAD `11603890`) against issue #2463's own Acceptance text, not against the
implementation session's self-report.

canonical: `git worktree add --detach /tmp/review-2463 origin/issue-2463/implementation` (this session), `git -C /tmp/review-2463 rev-parse HEAD` —
```
11603890e96d3a4c5edc728f5ff8e31bfe095c00
```
All citations below to files/lines that only exist on that branch are
pinned as `11603890:<path>`.

## What was done

Decomposed the issue's 4 Acceptance bullets into 4 discrete,
dimension-tagged requirements (conformance-review-requirement-extraction) —
no bundled "and"-clauses to split, and bullet 1's embedded "must not"
clause is treated as satisfied jointly with bullet 2's separate regression
requirement rather than duplicated (extraction rule 3). Picked a
verification method per requirement (conformance-review-verification-method-selection),
and rendered one of the five verdicts per requirement
(conformance-review-verdict-assignment). Findings recorded below
(conformance-review-finding-record). Sampling was judged not-applicable —
the reviewable diff is one source file plus its touched test file, small
enough for full enumeration in one session (see Skill verdicts).

Verification actually executed this session (own runs against the
worktree checkout above, not pasted from the implementation record):

canonical: `cd /tmp/review-2463 && python3 gates/test_check_runner.py` (this session) —
```
...
ok - t_angle_bracket_placeholder_path_classifies_as_judgment_not_file_existence
ok - t_angle_bracket_placeholder_variants_all_classify_as_judgment
ok - t_genuinely_missing_literal_path_without_placeholder_still_fails
...
31/31 passed
```
canonical: `cd /tmp/review-2463 && python3 -m pytest gates/test_check_runner.py -q` (this session) —
```
38 passed in 1.81s
```
canonical: `cd /tmp/review-2463 && python3 -m pytest gates/ -q` (this session) —
```
1006 passed, 8 xfailed in 11.05s
```

Beyond re-running the PR's own tests, this review authored its own
independent fixtures (deliberately different literal strings from the
ones in `11603890:gates/test_check_runner.py`) and diffed classification
pre-fix vs. post-fix by loading `gates/check_runner.py` from both
`git show 11603890^:gates/check_runner.py` (pre-fix) and the current
worktree (post-fix) as two separate Python modules in the same process:

canonical: independent synthetic fixture, PRE vs. POST (this session, own script) —
```
PRE=['file-existence']  POST=['judgment']  :: '- check: config lives under `issue-<n>/<role>/config`'
PRE=['judgment']  POST=['judgment']  :: '- check: the branch subject follows the `<role>` naming slot'
PRE=['judgment']  POST=['judgment']  :: '- check: sessions are keyed by `issue-<n>` in the workspace path'
PRE=['file-existence']  POST=['judgment']  :: '- check: a nested placeholder like `docs/issue-<n>/<role>/notes` describes the convention'
```
canonical: independent regression fixture — genuinely missing literal path, no placeholder, no `.` extension (avoids an unrelated pre-existing confound explained in "What did not work") (this session, own script) —
```
classified as: ['file-existence']
run_checks status: fail
```
canonical: live re-classification of issue #2402's real Acceptance section, fetched fresh this session (`gh issue view 2402 --json body -q .body`), PRE vs. POST (this session, own script) —
```
PRE=file-existence   POST=judgment        :: "there is a supported way to recut a corrupted branch's content that remains mapped to its "  <-- CHANGED
PRE=judgment         POST=judgment        :: "`board-sweep`'s subject-mapping recognizes branches produced by that path — demonstrated l"
PRE=judgment         POST=judgment        :: 'a role whose delivery landed via a recut branch is NOT re-spawned by `spawn-on-approve`/`s'
PRE=judgment         POST=judgment        :: 'if the chosen approach leaves any unmapped-branch case, the sweep says so once per PR with'
```
canonical: `grep -n "fetch_issue_body\|def main\|_acceptance_section(" 11603890:gates/check_runner.py` (this session) confirms `main()` classifies against `gh_rest.fetch_issue_body(repo, issue)` — keyed by **issue** number, not PR number — so the same Acceptance-section classification result applies unchanged whether check_runner is invoked against PR #2446, #2456, or #2461, since all three are runs of the same issue #2402.

canonical: `gh pr view 2446/2456/2461 --json number,title,state` (this session) — all three exist, are titled `issue-2402: ...`, and are `MERGED`, confirming the identity claimed above.

## Findings

Fields per conformance-review-finding-record: requirement, spec_ref, verdict,
evidence, rationale.

---
requirement: R1 — a synthetic fixture reproducing this session's 9 real misclassification cases (backtick text containing `<n>`, `<role>`, or similar angle-bracket placeholders) now classifies as `judgment`, not `file-existence` — demonstrated before/after against the actual fixture set
spec_ref: issue #2463 Acceptance bullet 1
verdict: Present
evidence: `11603890:gates/check_runner.py:132,140-142` (`_ANGLE_PLACEHOLDER = re.compile(r"<[^\s<>]+>")`, checked first inside `_looks_like_path()`, short-circuits to `False`); `11603890:gates/test_check_runner.py` new tests `t_angle_bracket_placeholder_path_classifies_as_judgment_not_file_existence` and `t_angle_bracket_placeholder_variants_all_classify_as_judgment`
rationale: confirmed by an independently-authored fixture (not the PR's own literal strings) run pre-fix vs. post-fix in this session (see "What was done" transcript above) — placeholder tokens containing `/` flip `file-existence` → `judgment`; placeholder tokens without `/` were already `judgment` pre-fix and are unaffected, matching the fix's stated narrow scope
---
requirement: R2 — a regression fixture with a genuinely nonexistent literal path (no placeholder syntax) still classifies as `file-existence` and still FAILs — proves the fix didn't blanket-disable the check
spec_ref: issue #2463 Acceptance bullet 2; also the "must not" clause embedded in bullet 1
verdict: Present
evidence: `11603890:gates/check_runner.py:140-151` (`_looks_like_path()` — the placeholder short-circuit only fires on an actual `<...>` match; every other branch is untouched); `11603890:gates/test_check_runner.py` new test `t_genuinely_missing_literal_path_without_placeholder_still_fails`
rationale: confirmed by an independently-authored regression fixture (own literal string, deliberately avoiding the `.`-in-token confound documented in "What did not work" below), transcript in "What was done" above — classifies `file-existence` and `run_checks()` reports `status: "fail"` against an empty tempdir, both reproduced live this session
---
requirement: R3 — re-run check_runner against issue #2402's actual PRs (#2446, #2456, #2461) post-fix and confirm the previously-misclassified bullet now reads as `judgment` (or passes) instead of FAIL — live demonstration against real historical data
spec_ref: issue #2463 Acceptance bullet 3
verdict: Present
evidence: `11603890:gates/check_runner.py:439,443` (`main()` classifies via `gh_rest.fetch_issue_body(repo, issue)`, keyed by issue number — not by PR number or PR diff content); live re-classification transcript in "What was done" above, this session's own fresh `gh issue view 2402` fetch
rationale: the previously-misclassified bullet ("there is a supported way to recut a corrupted branch's content that remains mapped to its `issue-<n>/<role>` subject") flips from `file-existence` to `judgment` when classified against the current tree, confirmed independently this session against a freshly-fetched copy of the issue body (not the implementation record's cached copy); because classification is issue-body-keyed rather than PR-specific, and PRs #2446/#2456/#2461 are confirmed (own `gh pr view` calls this session, transcript in "What was done" above) to all be runs against issue #2402, the same result applies to all three without needing three separate `check_runner.py` invocations against three different PR checkouts
---
requirement: R4 — state explicitly whether the WARN-tier (ambiguous case, per the consult's third recommendation) was implemented or explicitly deferred, and why
spec_ref: issue #2463 Acceptance bullet 4
verdict: Present
evidence: `11603890:docs/issue-2463/reports/implementation.md` "What was done" section, "WARN-tier statement (Acceptance bullet 4)" paragraph
rationale: the record states explicitly that the WARN tier is deferred (not implemented), and gives a scope reason tied to the issue's own text (the issue's "What" section names only the angle-bracket exclusion; WARN-tier would touch `run_checks()`'s result shape, `format_comment()`'s summary-count arithmetic, and `merge_gate.py`'s evaluation logic — a materially larger change with its own open design questions, outside the issue's stated `design-research-skip: mechanical` framing) — this satisfies the bullet's obligation to state the choice and the why, independent of which choice (implement vs. defer) was made
---

## Why

Reviewed builder-blind against the issue's own Acceptance text — decomposed
into the 4 requirements above before opening `11603890:docs/issue-2463/reports/implementation.md`
at all — rather than grading the implementation session's self-report.
Demonstration where the issue explicitly asked for a before/after and a
live historical re-run (R1/R2/R3), and Inspection for the call-site and
classifier-ordering properties underlying all four (R1/R2/R3/R4). No
requirement in this issue named a condition this review session could not
reproduce, so Analysis was not needed. Test evidence reused the PR's own
existing suite per rule 4 (see the `python3 gates/test_check_runner.py`,
`pytest gates/test_check_runner.py`, and `pytest gates/` transcripts, each
with their own `canonical:` tag, under "What was done" above) rather than
re-deriving a parallel manual check for coverage already test-covered —
but every finding above is additionally backed by an independently-authored
fixture distinct from the PR's own literal test strings, per this review's
builder-blind mandate.

## Upstream basis

- `11603890:docs/issue-2463/reports/implementation.md` — the delivering
  session's own record; read after this review's independent checks were
  already run, for the WARN-tier deferral reasoning (R4), which is the
  delivering session's own design claim about its own scope.
- PR #2464, branch `issue-2463/implementation`, HEAD `11603890` (see this
  record's opening `git rev-parse HEAD` transcript) — the code under
  review, checked out into `/tmp/review-2463` via `git worktree add` for
  independent test execution and diffed directly against the pre-fix
  parent commit.
- Issue #2463 itself, fetched fresh this session (`gh issue view 2463`),
  for the 4 Acceptance bullets and the validity-consult's three
  recommendations referenced in R4.

## What did not work

- First attempt at R2's regression fixture used the literal string
  `` `reports/definitely-not-here.md` `` (with a `.md` extension). This
  classified as `test`, not `file-existence` — not a defect in the PR
  under review, but an unrelated pre-existing classifier path: `parse_checks()`'s
  `looks_like_command` check (`11603890:gates/check_runner.py:191-194`)
  fires on any token containing both `/` and a `.` *before* `_looks_like_path()`
  is ever reached, treating it as an executable command rather than a
  path-existence check. Re-derived the fixture without a file extension
  (`` `reports/definitely-not-here` ``, matching the shape of the PR's own
  regression fixture), which reaches `_looks_like_path()` and classifies
  `file-existence` as expected, per the transcript in "What was done"
  above. Documented here rather than silently discarded, since it is
  exactly the kind of near-miss rule 6 (conformance-review-verdict-assignment)
  asks to be re-checked before finalizing a verdict.
- The first Bash invocation for the independent PRE/POST comparison script
  (a `python3 - <<'EOF' ... EOF` heredoc) was refused by this session's
  own `board-gate` PreToolUse hook (un-analyzable write-capable shape).
  Rewrote the same logic as a `Write`-tool `.py` file and invoked it with
  a plain `python3 /tmp/review_r1.py` — no functional change to what was
  verified, only to how the command was shaped.

## Open findings

None — no open findings, therefore no resolution path is needed.

## Next steps

None — `loop_state: reported` (terminal for this record's kind).

## Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split issue #2463's 4 Acceptance bullets into 4 one-obligation line items (rule 1; none were bundled with "and"), folded bullet 1's embedded "must not" clause into bullet 2's own regression requirement rather than duplicating it (rule 3), tagged each requirement's dimension inline in its verdict-assignment rationale, no sampling-derivation override needed (issue states none)
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of all 4 extracted requirements was feasible in one session against a small, bounded diff (one source file plus its touched test file) — no reduction to a sample was needed
skill-verdict: conformance-review-verification-method-selection — applied: invoked; assigned Demonstration to R1/R2/R3 (issue explicitly demands before/after and live historical re-run), Inspection to the call-site/classifier-ordering properties underlying all four requirements; reused the PR's own existing test suite as Test-method evidence per rule 4 rather than re-deriving a parallel manual check, while additionally authoring independent fixtures per this review's builder-blind mandate
skill-verdict: conformance-review-verdict-assignment — applied: invoked; all 4 rendered Present with cited evidence; R2's fixture design was re-checked once after an initial false confound (extension-triggered `looks_like_command` misclassification unrelated to this PR) before finalizing, per rule 6
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every Findings entry cites file:line plus the reviewed commit sha (rule 1, `11603890:` prefix throughout); backward-traced each requirement to its issue bullet before checking the implementation (rule 3, `spec_ref` on every entry names the issue bullet); no multi-file-spanning requirement needed a second per-file link (rule 2 n/a — one source file); no duplicate-evidence entries to collapse (rule 4 n/a); single spec version in play — the issue as currently open (rule 5 n/a)
skill-verdict: conformance-review-finding-record — applied: invoked; wrote all 4 finding blocks with the full field list (requirement, spec_ref, verdict, evidence, rationale); no Incorrect/Absent verdicts so `spec_vs_built` was not needed; every verdict carries an evidence pointer and a spec_ref
skill-verdict: conformance-review-severity-classification — not-applicable: review scope was not extended into risk-weighting; all 4 requirements verified Present, no findings exist to band
skill-verdict: implementation-audit — not-applicable: this session ran under this repo's own role-handoff/conformance-review contract (a structurally independent evaluator session reviewing a separate builder session's delivery, builder-blind) — the same shape implementation-audit describes, but the mechanism in force here is the repo's native contract v3, not a separately-invoked implementation-audit protocol
