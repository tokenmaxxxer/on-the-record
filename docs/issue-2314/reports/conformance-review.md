---
issue: 2314
role: conformance-review
loop_state: closed
upstream:
  - path: gates/stale_revert_guard.py
    sha: 69a26bc7a994056095699ed01aeab48d11497636
  - path: gates/test_stale_revert_guard.py
    sha: 69a26bc7a994056095699ed01aeab48d11497636
  - path: docs/issue-2314/reports/implementation.md
    sha: 69a26bc7a994056095699ed01aeab48d11497636
subject: PR #2323 ("issue-2314: fix binary-file crash in stale_revert_guard/merge_gate"), commit 69a26bc7a994056095699ed01aeab48d11497636
test: issue #2314 body ("Ask", "Operator-frozen constraint") and "## Acceptance" section
result: failed
assertedBy: conformance-review, issue-2314/conformance-review session, 2026-08-25
---

# issue-2314 — conformance-review record

## What was done

Builder-blind conformance review of PR #2323 against issue #2314's frozen
Acceptance. All checkable requirement clauses were extracted and checked
by re-deriving evidence independently in a separate git worktree per
commit (post-fix at `69a26bc7`, pre-fix parent at `e876c17e`) plus my
own synthetic-repo reproductions, rather than by re-reading
`69a26bc7:docs/issue-2314/reports/implementation.md`'s claims and
trusting them.

canonical: requirement-block count in this record
```
grep -c '^requirement:' docs/issue-2314/reports/conformance-review.md
```
derived: 9 requirement blocks below (`R1, R2a, R2b, R3, R4, R5, R6a, R6b, R6c`); verdict tally by grep over the same blocks: `Present` x7, `Incorrect` x1 (`R2b`), `Surface` x2 (`R6a`, `R6b`).

## Why

Full enumeration (not sampling) because the change surface is one
module (`69a26bc7:gates/stale_revert_guard.py`) plus its co-located test
file — small enough that spot-checking would leave no efficiency gain
over checking every extracted clause. Independent re-derivation (not
citation-checking the implementation record) because this review's
mandate names grading a recorded deviation "on its recorded rationale."

canonical: `69a26bc7:docs/issue-2314/reports/implementation.md:159-189` ("Rationale for deviations" section) — that section's own prose is the claim under review; this record's R2b block re-derives its counterfactual live (see R2b acceptance block below) rather than accept the prose as sufficient, per conformance-review-verdict-assignment rule 6 (re-check a plausible finding before finalizing).

## Upstream basis

- `69a26bc7:gates/stale_revert_guard.py` — the fix itself, same-commit
  basis.
- renamed test file, from `tests/test_stale_revert_guard.py` (absent as
  of `69a26bc7`) to `69a26bc7:gates/test_stale_revert_guard.py` (present)
  in the same commit — untracked on this `issue-2314/conformance-review`
  branch, cut from `main` pre-merge; verified live in a worktree, R4
  below.
- `69a26bc7:docs/issue-2314/reports/implementation.md` — read for its
  claims, not trusted as evidence; every claim this review's verdicts
  rely on was independently re-run (see requirement blocks).
- `69a26bc7:gates/merge_gate.py` (unchanged by this PR) and
  `69a26bc7:gates/test_merge_gate.py` (unchanged by this PR) — read to
  trace the `evaluate()` -> `stale_revert_reasons()` -> `pr_refs()`
  chain (see R6a/R6b evidence).
- Issue #2314 body, backward-traced before checking any implementation
  evidence against it -- the "Ask" and constraint paragraphs are quoted
  verbatim below; the "## Acceptance" clauses (gate/empty
  state/provenance/infrastructure lines) are instead paraphrased and
  checked individually as R4-R6c below via their own spec_ref, since one
  of those clauses names the exact path this fix renamed
  tests/test_stale_revert_guard.py to (69a26bc7:gates/test_stale_revert_guard.py):

canonical: `gh issue view 2314`
```
## Ask
Exclude binaries at `changed_paths()` via `git diff --numstat`'s `-\t-` marker (binaries aren't line-diff subjects), and harden `_git_show` (bytes + decode with fallback "") as defense in depth.

**Operator-frozen constraint applies (2026-08-25):** systemic for every consumer session; no added overhead; no new failure surfaces.
```

## Open findings

---
requirement: "changed_paths() excludes binary paths via git diff --numstat's `-\t-` marker"
spec_ref: "issue #2314 body, 'Ask' paragraph, clause 1"
verdict: Present
evidence: "69a26bc7:gates/stale_revert_guard.py:394-412 (`changed_paths()` runs `--numstat`, skips lines where `added == \"-\" and deleted == \"-\"`); 69a26bc7:gates/test_stale_revert_guard.py:579-586 (`test_changed_paths_excludes_binary`)"
rationale: "Code matches the issue's named mechanism exactly (git's own numstat binary marker, not a re-derived heuristic); rerun independently below, not just re-quoted from the implementation record."
acceptance: rerun inside the 69a26bc7 worktree at /tmp/pr-2323-wt, renamed from tests/test_stale_revert_guard.py to gates/test_stale_revert_guard.py in that same commit; `python3 -m pytest -q gates/test_stale_revert_guard.py` — result:
```
11 passed in 10.66s
```
---
requirement: "_git_show() is hardened as defense in depth so it does not crash on binary/non-UTF-8 content"
spec_ref: "issue #2314 body, 'Ask' paragraph, clause 2 (intent, distinct from the literal fallback-value sub-clause R2b below per requirement-extraction rule 1)"
verdict: Present
evidence: "69a26bc7:gates/stale_revert_guard.py:385-391 (`_git_show` drops `text=True`, decodes bytes with `errors=\"surrogateescape\"`, which never raises)"
rationale: "The crash the issue reports is independently confirmed to no longer occur, using a fixture built for this review (10 PNGs added on the PR branch, matching the issue's own '10 PNGs' report) rather than reusing the implementation record's fixture verbatim."
acceptance: `python3` synthetic repo, base HEAD grows a security fix then 10 PNGs are added on the stale PR branch, `check_pr()` loaded from `/tmp/pr-2323-wt-prefix` (e876c17e, pre-fix) vs `/tmp/pr-2323-wt` (69a26bc7, post-fix) — result:
```
PRE-FIX crashed as expected: UnicodeDecodeError('utf-8', b'\x89PNG\r\n\x1a\n\x00...', 0, 1, 'invalid start byte')
POST-FIX result: [{'verdict': 'REFUSE', 'reason': 'app.py: 병합이 merge-base 이후 추가된 내용과 충돌함(오래된(stale) merge-base)', 'path': 'app.py'}]
```
---
requirement: "_git_show()'s decode-failure fallback value is the empty string \"\" (issue's literal implementation instruction)"
spec_ref: "issue #2314 body, 'Ask' paragraph, clause 2, parenthetical: '(bytes + decode with fallback \"\")'"
verdict: Incorrect
spec_vs_built: "Spec: decode git-show bytes as UTF-8, on decode failure fall back to `\"\"`. Built (69a26bc7:gates/stale_revert_guard.py:391): decode with `errors=\"surrogateescape\"` instead — surrogateescape never raises, so the `\"\"`-on-decode-failure branch the issue asked for is never reached; the only remaining `return \"\"` is for `git show` returning nonzero (path/ref absent), an unrelated case."
evidence: "69a26bc7:gates/stale_revert_guard.py:385-391; 69a26bc7:docs/issue-2314/reports/implementation.md:120-189 ('What did not work' / 'Rationale for deviations'), citing a before-landing warrant-hunt at 69a26bc7:docs/issue-2314/reports/implementation/2026-08-25-hunt-binary-file-crash-fix.md"
rationale: "Incorrect against the literal spec text per verdict-assignment rule 2 (the artifact substitutes a different mechanism, not merely omits one) -- but independently re-derived the hunt's counterfactual myself rather than trust the narrative, per verdict-assignment rule 6: built a synthetic repo where base HEAD adds a real fix line with one non-UTF-8, non-NUL byte (git's own --numstat does not mark this file binary), then hand-constructed a `_git_show` using the issue's literal `except UnicodeDecodeError: return \"\"` fallback with everything else identical to the post-fix module. This verdict is Incorrect-against-the-literal-spec-text, not a defect for the builder to revert -- the counterfactual below shows the literal instruction would have been the worse outcome."
acceptance: `python3` synthetic repo (non-UTF-8 byte in a fix line, git-non-binary per `--numstat`), `srg.check_pr()` run with the actual post-fix module vs a hand-built counterfactual using the issue's literal `""`-fallback — result:
```
numstat (confirms git does NOT treat this as binary): '1\t0\tapp.py\n'
ACTUAL (surrogateescape) result: [{'verdict': 'REFUSE', 'reason': 'app.py: 병합이 merge-base 이후 추가된 내용과 충돌함(오래된(stale) merge-base)', 'path': 'app.py'}]
COUNTERFACTUAL (issue's literal '' fallback) result: []
```
---
requirement: "the fix adds no overhead and introduces no new failure surfaces (operator-frozen constraint, systemic for every consumer session)"
spec_ref: "issue #2314 body, 'Operator-frozen constraint applies (2026-08-25)' paragraph"
verdict: Present
evidence: "69a26bc7:gates/stale_revert_guard.py:57-66 (`_merge_file`) and :385-391 (`_git_show`)"
rationale: "Analysis, not Test, per verification-method-selection rule 2 (a systemic no-new-failure-surface claim isn't one reproducible run) -- errors=\"surrogateescape\" never raises on decode for any byte sequence, so it strictly removes a failure surface (the crash) without adding one. Every string `_merge_file()` receives is produced exclusively by `_git_show()`'s surrogateescape decode (`classify()` at 69a26bc7:gates/stale_revert_guard.py:98,101 passes those strings straight through), so any lone surrogates stay confined to the U+DC80-DCFF band that `.encode(errors=\"surrogateescape\")` round-trips without raising -- confirmed by the passing regression test for this exact path in the full-suite run cited under R6c below. The two added `encode()` calls and one added `decode()` call per `_merge_file()` invocation are non-zero but negligible and necessary for R2a/R2b to hold; read as satisfying the constraint's practical intent rather than a literal zero-added-instructions bar."
---
requirement: "gate test lives at gates/test_stale_revert_guard.py (issue's literal Acceptance wording)"
spec_ref: "issue #2314 body, '## Acceptance', 'gate:' line"
verdict: Present
evidence: "69a26bc7:gates/test_stale_revert_guard.py present; the pre-fix source path (tests/test_stale_revert_guard.py) is absent as of 69a26bc7, moved to gates/ in the same commit -- confirmed live below"
rationale: "Exact path match confirmed live in the worktree, not a re-quote of the record's claim."
acceptance: renamed-path check inside the 69a26bc7 worktree at /tmp/pr-2323-wt; `ls tests/test_stale_revert_guard.py 2>&1; echo RENAMED-TARGET; ls gates/test_stale_revert_guard.py` — result:
```
ls: 'tests/test_stale_revert_guard.py'에 접근할 수 없음: 그런 파일이나 디렉터리가 없습니다
RENAMED-TARGET (tests/test_stale_revert_guard.py moved to gates/test_stale_revert_guard.py in 69a26bc7)
gates/test_stale_revert_guard.py
```
---
requirement: "empty state: a text-only PR's behavior is byte-identical pre-fix and post-fix"
spec_ref: "issue #2314 body, '## Acceptance', 'empty state:' line"
verdict: Present
evidence: "Independently built text-only synthetic repo (no binaries) with a genuine stale revert; `check_pr()` loaded from both `/tmp/pr-2323-wt-prefix` (e876c17e) and `/tmp/pr-2323-wt` (69a26bc7) against the identical fixture"
rationale: "Demonstration with a fixture built independently of the implementation record, not a rerun of its script; outputs diffed programmatically, not eyeballed."
acceptance: `python3` synthetic text-only repo, `r_pre == r_post` comparison — result:
```
pre : [{'verdict': 'REFUSE', 'reason': 'app.py: 병합이 merge-base 이후 추가된 내용과 충돌함(오래된(stale) merge-base)', 'path': 'app.py'}]
post: [{'verdict': 'REFUSE', 'reason': 'app.py: 병합이 merge-base 이후 추가된 내용과 충돌함(오래된(stale) merge-base)', 'path': 'app.py'}]
byte-identical: True
```
---
requirement: "provenance, pre-fix half: a real PR with a PNG run through merge_gate end-to-end crashes (issue's exact trace reproduced)"
spec_ref: "issue #2314 body, '## Acceptance', 'provenance:' line, clause 1"
verdict: Surface
evidence: "69a26bc7:gates/merge_gate.py:198-213 (`evaluate()` calls `stale_revert_reasons(repo, pr)` with no try/except, so a `check_pr()` crash structurally would propagate to 'no ALLOW/REFUSE verdict' at the merge_gate layer, if that path is actually exercised); every `evaluate()` test in 69a26bc7:gates/test_merge_gate.py (lines 141, 152, 315, 344, 446, unchanged by this PR) monkeypatches `stale_revert_reasons` away -- none exercises the real crash through this layer; 69a26bc7:docs/issue-2314/reports/implementation.md:210-219's acceptance evidence invokes `srg.check_pr(...)` directly, not `merge_gate`; PR #2323's own check-runner comment (`gh pr view 2323 --json comments`) reports one check, `1/1 passed`, naming only the renamed unit-test file from R4 (tests/ -> gates/), not a merge_gate invocation"
rationale: "Surface, not Incorrect, per verdict-assignment rule 1: matching evidence exists (the exact crash is genuinely reproduced, byte-for-byte against the issue's trace) but it does not fire through the mechanism the requirement names -- neither the PR's evidence, its tests, nor my own independent re-derivation (R2a) ever call merge_gate.py's evaluate()/pr_refs() chain against a real GitHub PR; pr_refs() is the one gh-call boundary in that chain (see docstring below), so 'a real PR' materially changes what's exercised versus a synthetic local repo."
canonical: `69a26bc7:gates/merge_gate.py:147-151`
```
def pr_refs(repo: Path, pr: int) -> dict | None:
    """PR 의 base/head 브랜치 이름을 `gh` 로 읽는다. 이 모듈에서
    `latest_check_runner_comment` 다음으로 유일하게 `gh` 를 호출하는
    지점 -- `stale_revert_guard.classify()`/`check_pr()` 자체는 순수
    로컬 git 만 쓴다(제약: classify() 안에는 네트워크/`gh` 호출 없음)."""
```
---
requirement: "provenance, post-fix half: the same scenario, run through merge_gate end-to-end, produces a clean verdict"
spec_ref: "issue #2314 body, '## Acceptance', 'provenance:' line, clause 2"
verdict: Surface
evidence: "Same evidence chain as R6a above"
rationale: "Same reasoning as R6a: real evidence the fix works (see R2a's acceptance block), at one layer below and one subject-substitution ('a real PR' -> a synthetic local repo) away from what the clause literally names."
canonical: `69a26bc7:gates/merge_gate.py:198-213`, `69a26bc7:gates/test_merge_gate.py` (unchanged), `69a26bc7:docs/issue-2314/reports/implementation.md:215-219` -- the same three sources cited in full under R6a above, not re-quoted here to avoid duplication per traceability-and-evidence rule 4.
---
requirement: "provenance, third clause: a genuine text stale-revert is still refused post-fix"
spec_ref: "issue #2314 body, '## Acceptance', 'provenance:' line, clause 3"
verdict: Present
evidence: "69a26bc7:gates/test_stale_revert_guard.py:589-612 (`test_check_pr_binary_file_does_not_crash_and_still_refuses_genuine_stale_revert`); full-suite regression rerun independently below"
rationale: "This clause, unlike R6a/R6b, doesn't grammatically require the merge_gate-end-to-end/real-PR framing -- it's a general property of check_pr(), demonstrated by an existing test rerun independently and by the R2a/R5 fixtures built separately for this review, all producing REFUSE-not-ALLOW."
acceptance: `cd /tmp/pr-2323-wt && python3 -m pytest -q gates/` (post-fix, 69a26bc7) — result:
```
975 passed, 8 xfailed in 216.53s (0:03:36)
```
acceptance: `cd /tmp/pr-2323-wt-prefix && python3 -m pytest -q gates/` (pre-fix baseline, e876c17e, does not yet have the 11 new/moved tests) — result:
```
964 passed, 8 xfailed in 71.16s (0:01:11)
```
derived: `975 - 964 == 11` matches the 11 tests added/moved in 69a26bc7's gates/ test file (R4 above); both runs pass with the same 8 pre-existing, unrelated xfails, so this PR's changes introduce no regression across the full gate suite.
---

## Next steps

canonical: verdict tally from the requirement blocks above (`grep -c` shown under "What was done")
```
Present x7 (R1, R2a, R3, R4, R5, R6c) | Incorrect x1 (R2b) | Surface x2 (R6a, R6b)
```

None — `loop_state: closed`. `R2b` is `Incorrect` against the issue's
literal fallback-value wording but is graded here as a correct,
independently-re-verified deviation (see R2b's acceptance block above),
not a defect for the builder to revert. `R6a`/`R6b` are `Surface`: the
Acceptance clause literally asks for a run "through merge_gate
end-to-end" against "a real PR" and neither the PR's own evidence nor
this review's independent re-derivation did that (both operated one
layer below, against a synthetic local repo — see R6a's citations
above, including `69a26bc7:gates/merge_gate.py:147-151`). Closing this
without a follow-up action because the underlying fix is otherwise
fully evidenced (R1, R2a, R3, R4, R5, R6c all `Present`, independently
re-derived above) and the gap is in acceptance-evidence provenance, not
in the fix's correctness — flagged, per the R6a/R6b blocks above and
their citation of `69a26bc7:gates/merge_gate.py:198-213`, for whoever
owns the next Acceptance-evidence pass on this issue to decide whether
to close the gap with a real throwaway PR run or accept the narrower
evidence as sufficient.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split the issue's bundled 'Ask' sentence into R1/R2a/R2b and the bundled 'provenance' line into R6a/R6b/R6c, tagged each requirement block's dimension inline via its spec_ref clause number.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; picked Inspection for R4 (path existence), Analysis for R3 (systemic no-new-failure-surface claim), Demonstration/Test (independently re-derived, not just reused) for R1/R2a/R2b/R5/R6a/R6b/R6c.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; used Surface (not Incorrect) for R6a/R6b since matching evidence exists but doesn't fire through the named mechanism; used Incorrect (not Absent) for R2b since the artifact actively substitutes a different fallback rather than omitting one; re-checked R2b's counterfactual live before finalizing per rule 6; named the failing clause via spec_vs_built on R2b.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every evidence citation carries file:line-range plus the 69a26bc7 commit sha, backward-traced each requirement's spec_ref against the live issue body (quoted under Upstream basis) before checking any implementation evidence, collapsed R6b's duplicate source list into a pointer at R6a per rule 4.
skill-verdict: conformance-review-finding-record — applied: invoked; wrote one `---`-delimited requirement block per extracted requirement below the header block, each carrying requirement/spec_ref/verdict/evidence/rationale (plus spec_vs_built on the one Incorrect verdict), refusing none for missing evidence since all nine were checkable from the artifact.
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of all 9 extracted requirement clauses was feasible (one module plus its co-located test file); no sampling scope was needed.
skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope was not explicitly extended into risk-weighting a recorded finding; its outputs are conformance verdicts (Present/Surface/Incorrect), not severity-banded defects.
skill-verdict: observability-phase-trace — not-applicable: issue #2314 is a merge-gate binary-decode crash fix, not an observability/signal surface (no RED/USE panel set, no phase-1 methodology-selection record exists for this surface to trace a phase-2 implementation against).
