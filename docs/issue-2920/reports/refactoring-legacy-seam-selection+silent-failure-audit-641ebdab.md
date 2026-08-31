---
issue: 2920
role: refactoring-legacy-seam-selection+silent-failure-audit-641ebdab
author: refactoring-legacy-seam-selection+silent-failure-audit-641ebdab
skills: refactoring-legacy-seam-selection (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: skills.py, test/test_consult_skill_resolution_2920.py
type: fix
breaking: no
verdict: pass
loop_state: landed
upstream:
  - path: docs/issue-2920/reports/adversarial-review-e466be2e.md
    sha: 16e6bc568c7e93ba4c1bf7fbcb5e10a3a3b0d8b9
  - path: PR #2927 (github.com/tokenmaxxxer/on-the-record/pull/2927), branch issue-2920/refactoring-legacy-seam-selection+silent-failure-audit-b9f1e0f4
    sha: 6199011258ef78b062457fcc3363e655a845f549
---

# issue-2920 — refactoring-legacy-seam-selection+silent-failure-audit-641ebdab record

skill-verdict: refactoring-legacy-seam-selection — applied: invoked; loaded via Skill tool this session, before editing `skills.py`. Rule 1 (Sprout Method for a single, clearly-localized behavior change) and rule 6 (narrow the seam to the smallest enclosing scope) both applied directly: Finding 2's fix is confined to the single list-comprehension that builds `unresolved` inside `resolve_consult_skill_source()` — no surrounding refactor of the function, no touch to `_composed_consult_skill_source()`/`consult_cmd()`/env-var plumbing, which all already read the corrected value with no further change needed.
skill-verdict: silent-failure-audit — applied: invoked; loaded via Skill tool this session. Used the H/S/U classification to frame Finding 2 itself: a resolved, successfully-mounted POLICY skill being reported through the same `unresolved` channel as a genuine miss is a misclassification that would make the "mounted only work-in-english" corpus signal built by PR #2927 lie in exactly the direction the audit's Step 3 (trace forward to downstream consequence) flags — the false-positive lands silently in a metric, not in a crash, which is the harder-to-catch shape.
skill-verdict: work-in-english — applied: invoked; loaded via Skill tool this session, followed for commit/test/comment language and this record; final chat summary in Korean.
other mounted skills: not triggered — merge-gates was configured for this task's text match but this round only edits two already-open-PR files on one branch (no concurrent-landing gate design question), so it was not invoked.

## What was done

This is round 2 on issue #2920, extending the already-open PR #2927
(branch `issue-2920/refactoring-legacy-seam-selection+silent-failure-audit-b9f1e0f4`,
commits `b0fb23a7`/`61990112`). canonical:
`docs/issue-2920/reports/adversarial-review-e466be2e.md` (independent
verification, `## Open findings` section) confirmed the core of that PR
(resolution parity with `--skills`, three-channel visibility,
cross-family match untouched, identical pre-existing test failures) and
raised two open findings there. Both are addressed here, on the PR's own
branch (this session's local branch was reset to point at the PR's
branch tip, then merged with `origin/main` to pick up the adversarial
review file and unrelated commits that landed after the PR branched, so
these commits land as continuations of PR #2927, not a second competing
PR).

**Finding 2 (real defect, fixed).** `resolve_consult_skill_source()`
(`skills.py`) built `unresolved` as "every requested name not in
`matched`," and `matched` itself excludes `_STATIC_POLICY_SKILLS`
members by construction (so a POLICY name is never double-counted when
`merge_composed_skill_source()` adds the baseline). The result: a
caller who explicitly named the POLICY skill `work-in-english` as (part
of) their selector — and who got it mounted, because the baseline
always mounts it — saw it reported as `unresolved` anyway. That is
wrong on its own terms (a skill that mounted is not unresolved), and it
directly corrupts the corpus count issue #2920's own acceptance check 3
depends on ("how many consults mounted only `work-in-english`"): a
fully successful, legitimately-generic `work-in-english`-only consult
would be indistinguishable, in the new visibility channel this PR
built, from a typo'd/failed one.

Fix, `skills.py:512`:
```python
-    unresolved = [n for n in names if n not in matched]
+    unresolved = [n for n in names
+                  if n not in matched and n not in _STATIC_POLICY_SKILLS]
```
Two regression tests added to `test/test_consult_skill_resolution_2920.py`
(`test_explicitly_requested_policy_skill_is_not_reported_unresolved`,
`test_policy_skill_combined_with_real_leaf_is_not_unresolved`).

**Finding 1 (record-accuracy failure, corrected — not a code change).**
PR #2927's own record claimed `gates/retirement_count.py` moved
1135 → 1098 and that its 14 added-line role-token hits were "all
docstring citations, zero code identifiers." Both numbers are wrong;
re-derived live below (see "Re-derivation of Finding 1's numbers"). The
wrong number and the false "zero code identifiers" claim are not fixed
by editing the old record (historical docs/ records are never modified)
— they are corrected here, in this round's own record, with the live
re-derivation and the identifier question resolved explicitly (renamed
the one flagged identifier; see below).

## Why

**Finding 2's fix location.** The alternative considered was filtering
`unresolved` at every call site that reads it
(`_consult_cmd_and_env()`'s env-var assembly, `consult_cmd()`'s verdict
fields, `_append_consult_trace()`'s trace line) — rejected because
`resolve_consult_skill_source()` is the single seam all three already
read from. canonical: `skills.py:527`,
`merged["unresolved"] = unresolved` (the one return-site all three
downstream readers consume) — fixing the source list means every
downstream reader is correct for free, with zero additional lines
touched outside the one function. This is rule 5 of
refactoring-legacy-seam-selection (seam closest to the point of actual
behavioral difference) applied directly: the actual difference is "was
this name resolved," which is entirely decided inside this one
function.

**Finding 1's resolution — the identifier question.** The flagged
identifier is `test/test_consult_skill_resolution_2920.py:129`,
`test_retired_role_name_no_longer_pulls_in_family_members` — a Python
function name, not a persisted key and not a runtime-compared string:
it is never written to a trace, never compared against a caller's
input, and exists purely so a human/pytest reads the test's intent. The
task named a real precedent for keeping a "role"-token identifier:
`gates/retirement_count.py`'s own self-exclusion, justified in its
docstring as "a citation of the retired axis by a named contract... not
a live use of it" (canonical: `gates/retirement_count.py`, comment block
directly above `_SELF_EXCLUDED`) — but that citation is of a *specific*
named contract (this gate and its test, by file path, `_SELF_EXCLUDED`
membership). This test's function name does not cite a specific named
contract; it describes a general concept ("a retired role name") in
English prose form, which is not the same trade. It was renamed rather
than kept:
```python
-    def test_retired_role_name_no_longer_pulls_in_family_members(self):
+    def test_retired_family_prefix_no_longer_pulls_in_family_members(self):
```
`"family prefix"` was chosen because it is already the vocabulary this
same PR's own docstrings/comments use for the retired concept
(`resolve_skill_family_source()`; the sibling test class one class below
carries the docstring "family-prefix 로 다른 스킬을 안 끌어온다" —
canonical: `test/test_consult_skill_resolution_2920.py:108-109`,
`JudgeReadonlyPluginDirsNoFamilyExpansionTest`'s class docstring). No
other reference to the old name exists — checked: `grep -rn
"test_retired_role_name_no_longer_pulls_in_family_members" .` — result:
only the one definition site (removed by this rename); no external
caller, no reflection-based lookup by name in the test runner.

## What did not work

None.

## Upstream basis

- `docs/issue-2920/reports/adversarial-review-e466be2e.md`
  (sha `16e6bc568c7e93ba4c1bf7fbcb5e10a3a3b0d8b9`) — the independent
  verification this round responds to; Findings 1 and 2 in its `## Open
  findings` section are the two items addressed above.
- PR #2927, branch
  `issue-2920/refactoring-legacy-seam-selection+silent-failure-audit-b9f1e0f4`,
  commits `b0fb23a7` (role-axis removal) and `61990112` (trace threading
  + PR record) — this round's commits continue that branch.

## Re-derivation of Finding 1's numbers (acceptance check 2)

canonical: `gates/retirement_count.py`, executed live in this checkout,
not reimplemented.

Repo-wide, at PR #2927 head (commit `61990112`, before this round's fix)
vs. true merge-base (`85d9f61d2acd5fe0e795593caa676f0bf306f420`, verified
via `git merge-base origin/main HEAD` returning that sha, run in a worktree
at the merge-base checkout before this round's merge commit):

```
derived: `python3 gates/retirement_count.py` at 85d9f61d2acd5fe0e795593caa676f0bf306f420 — result:
retirement_count: 1135 occurrence(s) of the retired role/roles axis in py/sh sources (docs/ excluded)

derived: `python3 gates/retirement_count.py` at 61990112 (PR #2927 head, before this round's fix) — result:
retirement_count: 1101 occurrence(s) of the retired role/roles axis in py/sh sources (docs/ excluded)
```

This matches the adversarial review's re-derivation
(canonical: `docs/issue-2920/reports/adversarial-review-e466be2e.md`,
section "SECOND"), not PR #2927's own claimed 1135 → 1098. The record
that shipped with PR #2927 was wrong; this round does not re-edit that
historical file (never modified per standing rule) — this is the
correction, made here.

Added-line role-token count, using the gate's own `rc.line_hits()`
(imported directly, not reimplemented), applied to every `+` line of
`git diff 85d9f61d2acd5fe0e795593caa676f0bf306f420 -- consult.py skills.py spawn.py 'test/*.py'`
at PR #2927 head (before this round's fix):

```
derived: python3 script importing gates/retirement_count.rc, filtering
`git diff 85d9f61d2acd5fe0e795593caa676f0bf306f420 -- consult.py skills.py
spawn.py 'test/*.py'` added lines through `rc.line_hits()` — result:
added lines total: 453
hits: 17
```

17, not the claimed 14. Of those 17: 16 are docstring/comment prose
(shape: "the retired role axis / role->skill table / retired role
name," all past-tense citations of what was deleted — the same 17-item
listing the adversarial review already enumerated, canonical:
`docs/issue-2920/reports/adversarial-review-e466be2e.md`, section
"SECOND"). The 17th was the function name identifier addressed above —
a genuine code identifier, contradicting PR #2927's "zero code
identifiers" claim.

**Where the 14-vs-17 and 1098-vs-1101 gaps come from:** it is not a
scope mismatch between the PR's two commits — checked and ruled out.
derived: `git log -S
"test_retired_role_name_no_longer_pulls_in_family_members" --oneline --
test/test_consult_skill_resolution_2920.py` — result: the identifier
was introduced in the PR's *first* commit, `b0fb23a7`, not the second
(`61990112`). derived: re-running the PR record's own stated method
(`git show b0fb23a7 | grep '^+' | rc.line_hits(...)`) exactly, isolated
to that one commit — result: `450` added lines, `17` hits, the same 17
as the full PR-head count above, not the claimed 14. derived: `python3
gates/retirement_count.py` at commit `b0fb23a7` alone (a worktree
checked out at that sha) — result: `1101 occurrence(s)`, the same
1101 as PR head, not the claimed 1098; derived: `git diff b0fb23a7..
61990112 -- consult.py skills.py spawn.py 'test/*.py'` — result: `3`
added lines, `0` role-token hits, confirming the second commit changes
neither figure. The gate program itself is byte-identical between trees
(canonical: `git diff origin/main...HEAD -- gates/retirement_count.py`
— empty output), so this is not a tooling bug either: re-executing the
PR record's own cited method, on the exact commit it was run against,
reproduces 17/1101 every time (derived: ran three times at `b0fb23a7`,
all three printed `1101 occurrence(s)`), not the 14/1098 the record
states. No scope, tooling, or commit-boundary explanation accounts for
the gap — the PR record's figures do not match a re-execution of its
own stated method against its own cited commit, and should be treated
as a plain miscount rather than attributed to any specific mechanism.

After this round's fix (rename only — the `unresolved` fix in
`skills.py` touches no `role`-shaped identifier either way):

```
derived: `python3 gates/retirement_count.py`, this round's commit — result:
retirement_count: 1100 occurrence(s) of the retired role/roles axis in py/sh sources (docs/ excluded)
```

1100, one fewer than the pre-rename 1101, exactly the renamed
identifier. Re-running `line_hits()` over the same added-line
population after the rename:

```
derived: same script, diff base updated to this round's HEAD — result:
hits: 16
```

16, all docstring/comment prose, **zero code identifiers** — this claim
now holds because it was verified against the gate's own function, not
restated.

## Confirmation — Finding 2 fixed by construction

derived, executed live against the real skill-repository
(`$MUSTER_SKILL_REPO`, `MUSTER_SKILL_REPO_SHA=c05de12`), before/after
this round's `skills.py` fix:

```
spawn.resolve_consult_skill_source("work-in-english", repo)
  before fix: {'skills': ['work-in-english'], 'unresolved': ['work-in-english']}
  after fix:  {'skills': ['work-in-english'], 'unresolved': []}

spawn.resolve_consult_skill_source("work-in-english,adversarial-review", repo)
  after fix:  skills=['work-in-english', 'adversarial-review'], unresolved=[]
```

Env-var layer, derived: `spawn._consult_cmd_and_env("work-in-english",
None, None, task_text="", issue=None)` — after the fix,
`env["MUSTER_SKILLS"] == "work-in-english"` and
`"MUSTER_SKILLS_UNRESOLVED" not in env` (the key is only set when
`unresolved` is non-empty — canonical: `consult.py:1003-1004`,
`if unresolved: env["MUSTER_SKILLS_UNRESOLVED"] = ...` — so absence
here is correct behavior, not a missed write).

Verdict layer, derived: `consult.consult_cmd("work-in-english", "a
genuinely generic question", cwd=<tmp>)` with `subprocess.run` mocked to
a valid session JSON and `spawn._cross_family_skill_matches_with_consult`
stubbed to isolate the resolution path (must patch the `spawn.`-bound
name, not `consult.`'s own module-level def — canonical:
`spawn.py:348`, `_cross_family_skill_matches_with_consult =
consult._cross_family_skill_matches_with_consult`, binds at import
time, and `consult.py`'s call sites read it via `_sp.` = that `spawn`
binding) — result:
```
verdict["skills_mounted"] == ['work-in-english']
verdict["skills_unresolved"] == []
```
**This is the corpus-count derivability check the round-2 task asked
for**: a future consult that genuinely mounts only `work-in-english` on
an explicit request now lands on the "mounted" side of the acceptance-3
count, not the "unresolved" side — the field this PR built to make the
silent failure measurable no longer corrupts that same measurement for
this input shape.

Standing acceptance-1 parity and multi-skill form re-checked after the
fix (unaffected by it, confirmed rather than assumed): derived,
`resolve_consult_skill_source("adversarial-review", repo)["skill_dirs"]`
vs `resolve_skill_source("adversarial-review", repo)["skill_dirs"]`
(minus `work-in-english`) — result: `True` (equal as sets). Multi-skill
CSV, derived:
```
resolve_consult_skill_source("adversarial-review,code-architecture", repo)
  -> skills=['work-in-english', 'adversarial-review', 'code-architecture'], unresolved=[]
```

## Test evidence

```
derived: python3 -m pytest test/test_consult_skill_resolution_2920.py -q — result:
15 passed in 0.86s
```
15 = 13 pre-existing + 2 new regression tests for Finding 2.

```
derived: python3 -m pytest test/ -q — result:
523 passed, 3 xfailed, 15 failed
```
acceptance: `python3 -m pytest test/ -q 2>&1 | grep "^FAILED" | sort` at
this round's HEAD, diffed (`diff`) against the identical command run in
a worktree at the true merge-base
(`85d9f61d2acd5fe0e795593caa676f0bf306f420`) — result:
```
15 FAILED lines on each side; diff output: (empty — identical)
```
No new failure name traces to this round's two-line fix (the diff
above is empty, run this session; a different tree pair than the
identical-set finding `docs/issue-2920/reports/adversarial-review-e466be2e.md`
already reports independently for the merge-base vs. PR #2927 head, via
its own `diff <(...) <(...)`). 521 = PR #2927 head's own recorded pass
count (canonical:
`docs/issue-2920/reports/refactoring-legacy-seam-selection+silent-failure-audit-b9f1e0f4.md`,
"Test evidence" section); `523 - 521 = 2`, this round's two new
regression tests — the only source of the pass-count increase, given
the FAILED-set diff above is empty.

## Standing invariants re-checked

1. No reshaped role axis: derived,
   `grep -nE "def [a-zA-Z_]+\(.*\brole\b" consult.py skills.py spawn.py`
   — empty (unchanged from the adversarial review's own check —
   canonical: `docs/issue-2920/reports/adversarial-review-e466be2e.md`,
   "Standing invariants" section 1; this round's diff touches no
   function signature).
2. No retired role name kept working as a selector: this round's fix
   makes an *already-working* selector (`work-in-english`, always
   mounted) stop being *mis-reported*; it does not add resolution
   coverage for any role-shaped name — `conformance-review`/
   `implementation`/etc. remain unresolved+POLICY-only, unchanged
   (re-confirmed in the acceptance-1 re-check above).
3. `--skills` validation unweakened, resolution cost unchanged: the
   diff (canonical: `git diff 61990112 -- skills.py` — one hunk, two
   lines changed) is a two-line list-comprehension edit inside an
   already-O(n) loop over `names` (n = comma-separated selector count,
   always small) — no new I/O, no new subprocess, no new directory
   scan.
4. Cross-family BM25+skill_judge match untouched: no lines inside
   `merge_composed_skill_source()` or
   `_cross_family_skill_matches_with_consult()` are touched by this
   round's diff — canonical: `git diff 61990112 -- skills.py` shows only
   the one `unresolved` list comprehension changed (no other hunks).
5. Historical docs never modified: `docs/issue-2920/reports/
   refactoring-legacy-seam-selection+silent-failure-audit-b9f1e0f4.md`
   and `docs/issue-2920/reports/adversarial-review-e466be2e.md` are
   untouched by this round (canonical: `git diff 61990112 --name-status
   -- docs/issue-2920/` after this round's commit, excluding this
   record's own new file, shows no `M`/`D` against either path) —
   corrections to their numbers live in this record instead, per the
   standing rule.

## Open findings

None from this session — both findings raised by
`docs/issue-2920/reports/adversarial-review-e466be2e.md` are addressed
above (Finding 2: code fix + regression tests; Finding 1: re-derived
numbers, identifier renamed, record corrected in this file).

## Next steps

None — issue #2920's acceptance checks 1-3 hold after this round's fix
(re-demonstrated above); PR #2927 is ready to land with these two
additional commits.
