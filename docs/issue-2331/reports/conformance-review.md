---
issue: 2331
role: conformance-review
author: conformance-review
loop_state: reported
upstream:
  - path: a1e33a514683e644ff0a430e0bf3df6bb3b6810e:docs/issue-2331/reports/implementation.md
    sha: a1e33a514683e644ff0a430e0bf3df6bb3b6810e
  - path: a1e33a514683e644ff0a430e0bf3df6bb3b6810e:gates/record_lint.py
    sha: a1e33a514683e644ff0a430e0bf3df6bb3b6810e
  - path: a1e33a514683e644ff0a430e0bf3df6bb3b6810e:gates/test_record_lint.py
    sha: a1e33a514683e644ff0a430e0bf3df6bb3b6810e
subject: PR #2351 (branch issue-2331/implementation) against issue #2331's frozen Acceptance section
test: gates/test_record_lint.py (gate) plus independent worktree re-derivation of every replayed instance's source citation and the empty-state/latency/security claims (this session's own, not copied from the PR's pasted transcripts)
result: passed
assertedBy: conformance-review (issue-2331, builder-blind)
---

# issue-2331 — conformance-review record

## What was done

Builder-blind conformance review of PR #2351 (`issue-2331/implementation`,
commit `a1e33a514683e644ff0a430e0bf3df6bb3b6810e`) against issue #2331's
frozen Ask/Acceptance text. Extracted seventeen checkable requirements
(R1a-c, R2a-b, R3, R4a-c, R5, R6, R7a-d, R8, R9 — one obligation per
line, dimension-tagged) from the Ask's three numbered items, the
operator-frozen constraint bundle, and the Acceptance section's gate/
empty-state/provenance/regression/latency clauses.

Checked out `origin/issue-2331/implementation` into an isolated git
worktree (`/tmp/pr2351-review`, commit `a1e33a51`) and, for every
requirement, independently re-derived evidence rather than trusting
PR #2351's own pasted transcripts: re-ran the full gate suite myself,
wrote my own adversarial fixtures (an absolute-path escape attempt, a
`..`-escaping path, an abs-path `wc -l` claim, and — the review's one
substantive finding — a fixture reproducing issue #2207's own
"sample 20 vs 21" / per-session tally-undercount sub-defects, distinct
from the wc-l fixture the builder used), cross-checked all four replayed
instances' quoted record fragments against the real historical commits
they claim to come from (byte-for-byte `git show`, not trusting the
docstring's "verbatim" label), and independently re-derived the real
`spawn.py` line count (2940) the wc-l replay depends on straight from
PR #2207's own merge commit. Full commands and pasted output for every
requirement are under "## Requirement findings" below.

## Why

Verify-at-landing and builder-blind review both require the reviewing
session's own executed evidence, not the builder's word for it —
doubly so here, since the artifact under review is itself a machine-
verification gate against exactly this failure mode (a session typing a
number instead of re-deriving it), so trusting this PR's own pasted
numbers without independent re-derivation would be the same unguarded
step the issue exists to close. Using a separate worktree keeps the
review's test runs isolated from this branch's own tree. Writing an
independent adversarial fixture for #2207's non-wc-l sub-defects (rather
than only replaying the builder's own four fixtures) surfaced a real,
demonstrable gap the builder's own record does not flag.

## Upstream basis

- `a1e33a514683e644ff0a430e0bf3df6bb3b6810e:docs/issue-2331/reports/implementation.md`
  (PR #2351; on branch `issue-2331/implementation`, untracked in this
  checkout)
- `a1e33a514683e644ff0a430e0bf3df6bb3b6810e:gates/record_lint.py`,
  `a1e33a514683e644ff0a430e0bf3df6bb3b6810e:gates/test_record_lint.py`,
  `a1e33a514683e644ff0a430e0bf3df6bb3b6810e:on-the-record/gates/record_lint.py`
- issue #2331 body (`gh issue view 2331`, read this session)
- historical source commits independently re-read for the four replayed
  instances: `85a9611f6809183fa49ec9c270c2fbcae7079d8a` (#2207, PR #2308),
  `b38ef7e3033c9a013b93d416eeab18f050c0295f` (#2244, PR #2244/issue-2231),
  `e8b949219046d58d52a29a877be4015c22189e43` (#2295, PR #2307),
  `3a45a135` (the orchestrator's own stale `spawn.py:3930` citation's
  origin, `docs/reports/2026-08-09-hunt-repo-scoped-workspace-index-keys.md`)

## Requirement findings

---
requirement: R1a — a `` `wc -l <path>` `` derived-figure claim is re-counted against the working tree and refused on mismatch, naming the real count
spec_ref: issue #2331, Ask 1, "(wc, ...)" example; replayed by Acceptance's "#2207" instance
verdict: Present
evidence: a1e33a51:gates/record_lint.py:1089-1156 (`wc_l_recompute_check`); a1e33a51:gates/test_record_lint.py:1197-1214 (`t_2331_replay_2207_wc_l_after_figure_off_by_eleven`)
acceptance: cd /tmp/pr2351-review (commit a1e33a51) && python3 -m pytest gates/test_record_lint.py -k t_2331_replay_2207 -v — result:
```
t_2331_replay_2207_wc_l_after_figure_off_by_eleven PASSED
```
canonical: independently re-derived the real `spawn.py` line count the replay fixture depends on straight from PR #2207's merge commit — `git show 57ae2499:spawn.py | wc -l` — result: `2940`, matching both the check's own recomputation and the fixture's claim (not merely re-running the builder's fixture with the builder's own claimed number).
canonical: cross-checked the replay docstring's "verbatim" quote against the real historical record — `git show 85a9611f6809183fa49ec9c270c2fbcae7079d8a:docs/issue-2207/reports/refactoring-legacy.md | grep -n "wc -l spawn.py"` — result: `67:derived: \`wc -l spawn.py\` before = 3347, after = 2929 (424 lines moved,` — matches the fixture exactly.
rationale: the check function exists, is wired unconditionally into `lint_record()` (a1e33a51:gates/record_lint.py:1426), and this session's own independent re-derivation of the real line count (from the actual historical commit, not the builder's fixture alone) confirms the recomputation is genuine, not a fixture rigged to match a pre-baked expected value.
---
requirement: R1b — a fenced `$ pytest <files>` / "N passed" transcript is re-derived from the named files' test-function count and refused on mismatch, naming the real count
spec_ref: issue #2331, Ask 1, "(..., pytest --collect-only, ...)" — proxy shape actually implemented; replayed by Acceptance's "#2244" instance
verdict: Present
evidence: a1e33a51:gates/record_lint.py:1158-1220 (`pytest_count_recompute_check`); a1e33a51:gates/test_record_lint.py:1218-1246 (`t_2331_replay_2244_pytest_fenced_count_wrong_by_three_recomputations`)
acceptance: cd /tmp/pr2351-review && python3 -m pytest gates/test_record_lint.py -k t_2331_replay_2244 -v — result:
```
t_2331_replay_2244_pytest_fenced_count_wrong_by_three_recomputations PASSED
```
canonical: cross-checked the replay docstring's "verbatim" quote against the real historical record — `git show b38ef7e3033c9a013b93d416eeab18f050c0295f:docs/issue-2231/reports/implementation.md | grep -n "93 passed"` — result: `219:93 passed in 41.73s` — matches the fixture exactly.
rationale: same construction and independent-source-check as R1a; a real pytest re-run was deliberately not chosen by the builder (out of the gate's own <1s budget) in favor of a module-level `def test_`/`def t_` count proxy — a documented, reasonable substitution, not a silent one (stated in the implementation record's "Why").
---
requirement: R1c — a `grep -c`-shaped, `pytest --collect-only`-shaped, or generic arithmetic-over-fenced-numbers derived-figure claim is re-run/recomputed and refused on mismatch
spec_ref: issue #2331, Ask 1, "(wc, grep -c, pytest --collect-only, arithmetic over fenced numbers)" — the other two named example shapes, plus the general "arithmetic over fenced numbers" category
verdict: Absent
evidence: a1e33a51:gates/record_lint.py:1010-1360 (the entire new-check block) — no regex/function in this range matches a `grep -c`/`grep -cE` command shape, a `pytest --collect-only` shape, or a generic declared-count-vs-actual-list-length / per-item-tally shape
acceptance: python3 /tmp/check_2331_gap.py against a fixture reproducing issue #2207's own second and third named sub-defects verbatim in shape ("a sample of 20 session logs listed in the appendix, found the pattern recurring in 13 of them" / "per-session read tally for issue-2262: 7 reads counted") — result:
```
violations on #2207-shaped sample-size/tally claim: []
```
canonical: issue #2207's own real recurring-class description, independently re-read — `git show 85a9611f6809183fa49ec9c270c2fbcae7079d8a:docs/issue-2207/reports/refactoring-legacy.md | grep -n "sample"` and the real "20 vs 21" / tally-undercount finding at `docs/issue-2207/reports/execution-observation.md:246-252` ("an 11-line miscount ... a mismatch between the declared sample size (20) and the actual brace-expanded list (21), and undercounts in 2 of the 7 detailed per-session read tallies") — confirms these are real, named sub-defects of the same instance this PR partially replays, not an invented scenario.
rationale: the issue's own "recurring class this kills" bullet for #2207 names three sub-defects — "wc -l off by 11, sample 20 vs 21, two tally undercounts." Only the first is covered (R1a). The other two are exactly the "arithmetic over fenced numbers" example Ask 1 names, and my own fixture (independent of the builder's, deliberately shaped after #2207's own uncaught sub-defects rather than its caught one) shows zero of the four new checks fire on it. This is not a failure of the frozen Acceptance text itself — Acceptance ties provenance to "the four real instances" at whole-instance granularity ("#2207", "#2244", "#2295", spawn.py:3930), each of which does now produce at least one refusal, which is what R7a-d below verify — but it is a real, demonstrated gap against the Ask's own stated scope and against two of the three defects the issue's own motivating example names. The implementation record's "Why" section explains the `grep -c`/`pytest --collect-only` omission (no replayed instance needs them as a standalone tag shape) but does not address the sample-size/tally-undercount sub-defects at all — this finding is not one the builder's own record flags. See "Open findings" below.
---
requirement: R2a — a `path:line`/`path:line-range` citation whose number(s) exceed the file's actual current line count is refused as a phantom citation, naming the real count
spec_ref: issue #2331, Ask 2, "verify the cited line exists"; replayed by Acceptance's "spawn.py:3930" instance
verdict: Present
evidence: a1e33a51:gates/record_lint.py:1222-1269 (`citation_line_bounds_check`); a1e33a51:gates/test_record_lint.py:1287-1305 (`t_2331_replay_spawn_py_3930_phantom_citation`)
acceptance: cd /tmp/pr2351-review && python3 -m pytest gates/test_record_lint.py -k t_2331_replay_spawn -v — result:
```
t_2331_replay_spawn_py_3930_phantom_citation PASSED
```
canonical: cross-checked the replay docstring's "verbatim" quote against its named origin — `git show 3a45a135:docs/reports/2026-08-09-hunt-repo-scoped-workspace-index-keys.md | grep -n "spawn.py:3930"` — result: `75:built at spawn.py:3930 as \`f"issue-{issue}/{role}"\`, the substring check` — matches the fixture's quoted phrase.
rationale: the check exists, is wired unconditionally into `lint_record()`, and the replay fixture's source phrase is independently confirmed to be the real, verbatim phrase named in the issue body's own motivating example, not a paraphrase invented for the test.
---
requirement: R2b — a single-line `path:line` citation paired with a quoted code fragment is checked against that exact line's content, refused if the fragment lives elsewhere, naming the real line
spec_ref: issue #2331, Ask 2, "verify ... it contains the quoted fragment at the cited commit"; replayed by Acceptance's "#2295" instance
verdict: Present
evidence: a1e33a51:gates/record_lint.py:1295-1360 (`citation_line_content_check`); a1e33a51:gates/test_record_lint.py:1249-1285 (`t_2331_replay_2295_four_check_runner_citations_shifted_by_35`)
acceptance: cd /tmp/pr2351-review && python3 -m pytest gates/test_record_lint.py -k t_2331_replay_2295 -v — result:
```
t_2331_replay_2295_four_check_runner_citations_shifted_by_35 PASSED
```
canonical: cross-checked the replay docstring's "verbatim" quote against the real historical record — `git show e8b949219046d58d52a29a877be4015c22189e43:docs/issue-2295/reports/observability.md | grep -n "check_runner.py:179\|check_runner.py:198\|check_runner.py:180"` — result: lines 221 and 225 match the fixture's quoted citations exactly.
canonical: re-ran the four new checks directly against the currently-committed `docs/issue-2295/reports/conformance-review.md` (not the replay fixture) — result: 2 violations, both the record's own self-quoted `gates/check_runner.py:180` (`(r.stdout + r.stderr)[-2000:]` actually at line 215) — a true positive the builder's own implementation record's "Open findings" already discloses (that record quotes a prior defect to illustrate it, and the new check has no exemption for that shape yet), not a regression this review is newly reporting.
rationale: the check exists, is wired unconditionally, and independently reproduces both the crafted replay and a live, already-landed record's real self-quote case with the same result the builder's record claims. A known, disclosed limitation (a paraphrased, non-verbatim citation is not caught — the implementation record's Open finding 1) is outside Ask 2's own literal wording ("the quoted fragment"), not a gap in this requirement as written.
---
requirement: R3 — a `derived-unverified: <why>` line anywhere in a claim's enclosing markdown section opts it out of recomputation, visibly not silently
spec_ref: issue #2331, Ask 3
verdict: Present
evidence: a1e33a51:gates/record_lint.py:1033-1051 (`_is_derived_unverified`, `_DERIVED_UNVERIFIED_MARK`); a1e33a51:gates/test_record_lint.py:1338-1354 (`t_2331_derived_unverified_escape_is_visible_not_silent`)
acceptance: cd /tmp/pr2351-review && python3 -m pytest gates/test_record_lint.py -k t_2331_derived_unverified -v — result:
```
t_2331_derived_unverified_escape_is_visible_not_silent PASSED
```
rationale: the escape is a literal prose line in the record's own rendered markdown (visible to any reader, not a hidden config flag), and the test pins that it actually suppresses a genuinely-wrong `wc -l` claim rather than merely existing as dead code — satisfies "exempt explicitly ... visible not silent."
---
requirement: R4a — the four checks apply systemically to all consumer sessions, not opt-in per session
spec_ref: issue #2331, "Operator-frozen constraint applies: systemic for all consumer sessions"
verdict: Present
evidence: a1e33a51:gates/record_lint.py:1420-1426 (all four checks appended to `bad` unconditionally, not behind an `if not _exempt(...)` gate the way three pre-existing checks are); `diff gates/record_lint.py on-the-record/gates/record_lint.py` (this session, worktree a1e33a51) — result: no diff, byte-identical
rationale: every session running either the source-of-truth gate or the packaged copy gets all four checks unconditionally on every `lint_record()` call — Inspection of the aggregation site plus an independent byte-identity diff of the two copies confirms this, not the builder's own claim of it.
---
requirement: R4b — no side effects (no shell-out, no filesystem writes, no code execution)
spec_ref: issue #2331, "Operator-frozen constraint applies: ... no side effects"
verdict: Present
evidence: a1e33a51:gates/record_lint.py:1010-1360 (entire new-check block)
acceptance: sed -n '1010,1360p' gates/record_lint.py \| grep -n "subprocess\|os.system\|write_text\|open(.*'w\|shutil\|Popen" (this session, worktree a1e33a51) — result: no matches
canonical: independently probed the one identified filesystem-access surface for an escape — `_safe_repo_path(root, "/etc/passwd")` -> `None`, `_safe_repo_path(root, "../../../etc/passwd")` -> `None`, and a `wc -l /etc/passwd` claim through `wc_l_recompute_check` -> `[]` (correctly out of scope, not resolved against the real filesystem) — this session's own adversarial probe, not the builder's pasted example.
rationale: grep confirms no subprocess/shell/write calls in the new code, and my own adversarial probe (not reusing the builder's own test) confirms the one path-resolution surface actually rejects the absolute-path and `..`-escape cases the implementation record's "What did not work" section says a first draft leaked on.
---
requirement: R4c — trade-offs measured
spec_ref: issue #2331, "Operator-frozen constraint applies: ... trade-offs measured"
verdict: Present
evidence: a1e33a51:docs/issue-2331/reports/implementation.md, "## Why" (pure-Python-vs-subprocess reasoning, narrow-scope-vs-general-engine reasoning) and "## Acceptance" (latency measurement)
rationale: Inspection of the implementation record shows the recompute-vs-shell-out and narrow-four-shapes-vs-general-engine choices are each stated and justified, and the latency cost is a measured number (R9 below), not an assertion.
---
requirement: R5 — gate `gates/test_record_lint.py`
spec_ref: issue #2331, Acceptance, "gate: `gates/test_record_lint.py`"
verdict: Present
evidence: gates/test_record_lint.py (a1e33a51), executed this session in an isolated worktree
acceptance: cd /tmp/pr2351-review (commit a1e33a51) && python3 -m pytest gates/test_record_lint.py -q — result:
```
........................................................................ [ 85%]
............                                                             [100%]
84 passed in 1.11s
```
rationale: an existing repo test suite already covers the gate named by the issue; reused it as Test-method evidence per verification-method-selection rule 4, re-run in an isolated worktree rather than trusting the PR's own pasted count. Count matches the PR's own claimed 84.
---
requirement: R6 — empty state: a record with no derived figures fires zero new checks, at zero added latency
spec_ref: issue #2331, Acceptance, "empty state: a record with no derived figures — zero new checks fire, zero added latency"
verdict: Present
evidence: a1e33a51:gates/test_record_lint.py:1357-1365 (`t_2331_empty_record_fires_zero_new_checks`)
acceptance: this session's own script (not the builder's test) calling all four checks directly against `text = ""` — result:
```
empty-state violations: [] elapsed_ms: 0.02
```
rationale: independent Demonstration (own script, own timer) against the empty-text case confirms both zero violations and negligible (sub-millisecond) added latency, not merely that the builder's own pinned test passes.
---
requirement: R7a — replay of #2207 (real `wc -l` fragment, verbatim) now refused, naming the correct number
spec_ref: issue #2331, Acceptance, "provenance: executed-live — replay the four real instances above ... showing each now refused with the correct number/line named"
verdict: Present
evidence: same as R1a
rationale: carried forward from R1a — this is the Acceptance-level statement of the same evidence.
---
requirement: R7b — replay of #2244 (real fenced pytest transcript, verbatim) now refused, naming the correct number
spec_ref: issue #2331, Acceptance, provenance clause
verdict: Present
evidence: same as R1b
rationale: carried forward from R1b.
---
requirement: R7c — replay of #2295 (real four-citation fragment, verbatim) now refused, naming the correct line(s)
spec_ref: issue #2331, Acceptance, provenance clause
verdict: Present
evidence: same as R2b
rationale: carried forward from R2b.
---
requirement: R7d — replay of the orchestrator's own stale `spawn.py:3930` citation (real fragment, verbatim) now refused as a phantom citation, naming the correct count
spec_ref: issue #2331, Acceptance, provenance clause
verdict: Present
evidence: same as R2a
rationale: carried forward from R2a.
---
requirement: R8 — a correct record passes unchanged (no false positive introduced by the four new checks)
spec_ref: issue #2331, Acceptance, "a correct record passes unchanged" (provenance clause)
verdict: Present
evidence: a1e33a51:gates/test_record_lint.py:1307-1336 (`t_2331_correct_derived_figures_pass_unchanged`); this session's own re-run of the four checks against the real, already-committed `docs/issue-2207/reports/execution-observation.md`
acceptance: python3 /tmp/check_2331.py (this session's own script, against `docs/issue-2207/reports/execution-observation.md` and `docs/issue-2295/reports/conformance-review.md` in the a1e33a51 worktree) — result:
```
docs/issue-2207/reports/execution-observation.md -> 0 new-check violations
docs/issue-2295/reports/conformance-review.md -> 2 new-check violations
```
rationale: independent re-run against a real, already-landed record (not the builder's crafted fixture) confirms zero false positives on the record whose own absolute-path `wc -l` citations are correctly out of `_safe_repo_path`'s hermetic scope; the 2 violations on the other record are the disclosed true-positive self-quote case (R2b), not a regression.
---
requirement: R9 — added gate latency on a real record is measured and stays under the issue's <1s budget
spec_ref: issue #2331, Acceptance, "measure added gate latency on a real record (<1s budget)"
verdict: Present
evidence: this session's own timing script against `docs/issue-2295/reports/conformance-review.md` (390 lines, a1e33a51 worktree)
acceptance: python3 /tmp/check_2331b.py (this session's own script, 20-iteration average of all four new checks combined) — result:
```
lines: 390
avg ms/call over 20: 6.688
```
rationale: independently measured (own script, own clock, own iteration count) rather than trusting the PR's pasted "6.47 ms/call" — the two numbers agree within measurement noise, both several orders of magnitude under the 1s budget.
---

## Open findings

1. **R1c (Absent) — the "arithmetic over fenced numbers" / `grep -c` example
   shape from Ask 1 is unimplemented, and this is demonstrably not just an
   academic gap.** canonical: issue #2331's own motivating list — "#2207
   (wc -l off by 11, sample 20 vs 21, two tally undercounts)" — names three
   sub-defects in one real observer round; independently confirmed against
   `docs/issue-2207/reports/execution-observation.md:246-252` in the a1e33a51
   worktree (quoted under R1c above). This PR's `wc_l_recompute_check`
   catches the first. Nothing in the delivered gate would catch the other
   two: this session's own adversarial fixture, shaped after #2207's own
   uncaught sub-defects (a declared "sample of 20" vs. an actual differing
   count, and a per-session tally claim), produces zero violations against
   all four new checks (script and output under R1c above). If #2207's real
   record were re-authored verbatim today, two of its three named defects
   would still pass silently through this gate.
   Not a failure of the frozen Acceptance text as written — Acceptance
   names "the four real instances" at whole-instance granularity, and every
   instance does now produce at least one refusal (R7a-d, all Present) — but
   it is a real, evidenced gap against the Ask's own stated scope and against
   two of the three defects in the issue's own headline example. The
   implementation record's "Why" section explains omitting `grep -c` and
   `pytest --collect-only` as standalone tag shapes but does not mention the
   sample-size/tally-undercount sub-defects at all — this finding is new, not
   a re-statement of the builder's own disclosed Open findings 1-2.
   Resolution path: a follow-up issue, if this gap is judged worth closing,
   would need a check for a declared count in prose (a `derived:`/`canonical:`
   line stating "N of/sample of/tally of ...") against an independently
   enumerable list or count named nearby — a materially different, harder
   shape than the four command-transcript/citation shapes this PR
   implements, likely deserving its own scoping pass rather than a quick
   addition here.
2. **R2b's live-record re-run reconfirms the builder's own disclosed
   Open finding 2.** canonical: `docs/issue-2295/reports/conformance-review.md`
   (a1e33a51 worktree), a real already-landed record, now trips
   `citation_line_content_check` twice on its own self-quoted illustration of
   a prior defect — independently reproduced under R8's acceptance run above,
   which shows the same 2-violation count the builder's implementation
   record claims. Not a new finding; recorded here only because this
   review's own independent re-run happened to touch the same record, and to
   confirm the builder's disclosed number is accurate.

## Next steps

None — `loop_state` is terminal (`reported`). R1a, R1b, R2a, R2b, R3, R4a-c,
R5, R6, R7a-d, R8, and R9 (issue #2331's frozen Ask items 1-3, operator-frozen
constraint bundle, and every Acceptance clause) are each recorded Present
above with independently executed or cross-checked evidence. R1c is recorded
Absent with a concrete, independently-derived demonstration; it does not
block the frozen Acceptance text (satisfied at instance granularity by
R7a-d) but is flagged as a real, unresolved gap against the issue's own
stated motivating example for whoever next revisits this gate.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; decomposed issue #2331's three Ask items, the operator-frozen constraint bundle, and the Acceptance section into R1a-c/R2a-b/R3/R4a-c/R5/R6/R7a-d/R8/R9, splitting Ask 1's bundled command-shape examples and the #2207 instance's own bundled sub-defects per rule 1, before any verdict was rendered.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; Test (reused `gates/test_record_lint.py` and its `t_2331_*` group) for R1a/R1b/R2a/R2b/R3/R5/R7a-d/R8, Demonstration (own scripts, own fixtures) for R1c/R4b/R6/R8/R9, Inspection for R4a/R4c.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; Present for R1a-b/R2a-b/R3/R4a-c/R5/R6/R7a-d/R8/R9 with independent re-derivation (not the builder's word), Absent for R1c with the specific failing sub-clause named and a fresh demonstration (not a guessed verdict), per rule 5.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every evidence line cites file:line plus commit sha `a1e33a514683e644ff0a430e0bf3df6bb3b6810e` for the artifact under review, and every replayed instance's "verbatim" docstring claim was independently cross-checked (backward-traced) against the real historical commit it names before being accepted as evidence.
skill-verdict: conformance-review-finding-record — applied: invoked; wrote the seventeen `---`-delimited requirement blocks above with the full field list (requirement, spec_ref, verdict, evidence/acceptance/canonical, rationale), no block written without an evidence pointer or spec_ref.
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of issue #2331's Ask/Acceptance text (3 Ask items, one constraint bundle, 5 Acceptance clauses) against a 6-file, ~360-new-line diff was feasible; no sampling scope was needed.
skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope was not explicitly extended into risk-weighting a recorded finding; only fidelity-checking against issue #2331's frozen Acceptance was requested.
skill-verdict: implementation-audit — applied: invoked; followed its independent-evaluator framing — see R1c and the Open findings above for the one gap this framing surfaced that the builder's own record does not disclose — even though the concrete requirement/verdict mechanics ran through the more specific conformance-review-* family above.
other mounted skills: not triggered — freelunch:freelunch-code-fanout/freelunch:freelunch-site-fanout (no code-generation fan-out task), dataviz (no chart/visualization produced), claude-api (no LLM/Anthropic-API-shaped work in this review).
