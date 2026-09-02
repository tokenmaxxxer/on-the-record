---
issue: 3127
role: experiment-trust+adversarial-review+silent-failure-audit-760379f7
author: experiment-trust+adversarial-review+silent-failure-audit-760379f7
skills: experiment-trust (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true  # independent, builder-blind verification of PR #3169's redesign of scripts/issue-3127/verify_preregistration.py against 5 attack angles named in this session's task
loop_state: done
code_under_review: PR #3169 head 63ab85bc2deee637e6823cfaf866af8966763633, base main 771a173f19a3080e131a068bf280ab312a02557f
type: verification
breaking: false
verdict: PR #3169 is Incorrect overall. Attack angles 2, 3 and 4 are Present
  -- gh failure/malformed-input/wrong-order/partial-failure all fail closed
  (one Unguarded loud-crash path, self-disclosed, not silent); the check is
  self-consistent after its own squash-merge landing; the constructed
  violation is refused and independently confirmed to discriminate. Angle 1
  is Incorrect -- confirmed live -- a fabricated same-commit collision
  pinned via `verification_pr` at any OLD, LEGITIMATE, UNRELATED PR that
  happens to have the two paths in the right order passes, because
  `_resolve_via_pr_history` never checks that the referenced PR is the
  actual source of the commit under review, only that some PR has the
  right order somewhere in its own history. This is not a hidden defect --
  PR #3169's own record names it verbatim in "Open findings" and leaves it
  unfixed -- but the task explicitly required grading whether the check
  confirms the pinned PR actually introduced both paths, and it does not.
  Angle 5 (rejected digest alternative) -- agree with the rejection, see
  "What was done" item 5.
upstream:
  - path: PR-3169-branch:scripts/issue-3127/verify_preregistration.py
    sha: 1bd821e8b827f64b9827c0cf7a2db3a2c7148d08  # untracked on this session's own branch; lives on PR #3169's branch, read/exercised via git worktree + git fetch of refs/pull/3169/head
  - path: PR-3169-branch:tests/test_issue_3127_verify_preregistration.py
    sha: 1bd821e8b827f64b9827c0cf7a2db3a2c7148d08  # untracked here, same basis
  - path: PR-3169-branch:docs/issue-3127/decisions/pre-registration.md
    sha: ddc091f065f0b36d1379aa0f37adfb03f12c06b8  # untracked here, adds verification_pr: 3131 frontmatter
  - path: docs/issue-3127/reports/implementation-blueprint+experiment-trust+silent-failure-audit-9afe0675.md
    sha: same-commit  # PR #3169's own record, tracked on this branch as part of the PR diff read via `gh pr diff 3169`, not merged
---

# issue-3127 — experiment-trust+adversarial-review+silent-failure-audit-760379f7 record

## What was done

Independent, builder-blind verification of PR #3169 (`scripts/issue-3127/
verify_preregistration.py`'s redesign to survive squash-merge landing —
root-caused by PR #3166, fixed by PR #3169) against the 5 attack angles
named in this session's task. Read PR #3166's and PR #3169's records
first — derived: `gh pr view 3166 --json body,title,url` and `gh pr view
3169 --json body,title,commits,files` (both run this session) — then
attacked the running code directly with constructed fixtures, not by
reading the builder's own claims about it.

1. **Trust root of the `verification_pr:` fallback — Incorrect.**
   `_resolve_via_pr_history` (`scripts/issue-3127/verify_preregistration.py:
   138-195` on PR #3169's branch) reads `verification_pr` from the
   pre-registration's own frontmatter — attacker-controlled working-tree
   content — fetches that PR's commit list via `gh pr view <n> --json
   commits`, and checks only that *some* commit in that PR's history
   touches `PREREG_PATH` before some other commit touches `RESULTS_PATH`.
   It never checks that the referenced PR is the actual origin of the
   *current* same-commit collision under review. Constructed the attack
   live (fixture: `/tmp/attack1_unrelated_pin.py`, reproducible from this
   record): a fresh git repo, one new commit adding both
   `PREREG_PATH` (fabricated threshold, rigged post-hoc) and
   `RESULTS_PATH` (fabricated "WIN" result) together — the textbook
   squash-collision shape — with `verification_pr: 9999` pointing at an
   entirely unrelated PR whose own (legitimate, real) history happens to
   touch the two paths in the correct order. `verify()` returned
   `ok=True`. derived:
   ```
   $ python3 /tmp/attack1_unrelated_pin.py
   ok= True
   msg= OK: same-commit collapse resolved via PR #9999's own pre-squash commit history -- docs/issue-3127/decisions/pre-registration.md first appears at commit index 0 (legit1), docs/issue-3127/_assets/consumer-path-results.json at index 1 (legit2), strictly earlier
   VULNERABLE: fabricated commit pinned to an unrelated legitimate PR PASSES
   ```
   PR #3169's own record (`docs/issue-3127/reports/implementation-blueprint
   +experiment-trust+silent-failure-audit-9afe0675.md`, "Open findings",
   second bullet) names this exact gap verbatim and leaves it unfixed as
   out of scope. Self-disclosed, not hidden — but the task's angle-1
   wording ("must confirm the pinned PR actually introduced both paths,
   not merely that some PR has them in the right order") is not met by
   the shipped code, so the item grades Incorrect regardless of
   disclosure.

2. **`gh` unavailable or lying — Present.** derived: `python3
   /tmp/attack2_gh_lying.py` — six scenarios A through F, output:
   ```
   $ python3 /tmp/attack2_gh_lying.py
   A_gh_missing -> UNCAUGHT EXCEPTION (loud crash, non-zero exit): gh: command not found
   B_malformed_json -> ok=False msg=`gh pr view 3131 --json commits` failed or returned no commits -- cannot resolve the pre-squash order (fail closed: unavailable evidence is not a pass)
   C_missing_oid_field -> ok=False msg=`gh pr view 3131 --json commits` failed or returned no commits -- cannot resolve the pre-squash order (fail closed: unavailable evidence is not a pass)
   D_results_path_missing -> ok=False msg=PR #3131's commit history has no commit touching docs/issue-3127/_assets/consumer-path-results.json (or the lookup failed) -- cannot resolve ordering (fail closed)
   E_wrong_order -> ok=False msg=PR #3131's own pre-squash commit history does NOT show docs/issue-3127/decisions/pre-registration.md strictly before docs/issue-3127/_assets/consumer-path-results.json (indices 1 vs 0) -- the pre-registration did not precede the results even before the squash collapsed the ordering on this branch
   F_partial_api_failure -> ok=False msg=PR #3131's commit history has no commit touching both files (or the lookup failed) -- cannot resolve ordering (fail closed)
   ```
   - A: `gh` binary missing (`FileNotFoundError`): uncaught, loud crash —
     Unguarded, not Silently Absorbed; matches PR #3169's own
     `silent-failure-audit` disclosure. Independently confirmed above,
     not just cited.
   - B: malformed JSON from `gh pr view`: fails closed.
   - C: a commit entry missing the `oid` field: fails closed
     (`_pr_commit_order`'s `any(not isinstance(s, str)...)` guard).
   - D: `RESULTS_PATH` absent from every commit in the PR's history:
     fails closed.
   - E: results-before-prereg (wrong order): fails closed.
   - F: one `gh api` call mid-loop returns non-zero (simulating a rate
     limit/network blip on one commit): fails closed — no partial-
     success path treats a mid-loop failure as "not found, therefore
     fine."
   No case above read a `gh` failure as "could not check, therefore
   proceed."

3. **Self-consistency after PR #3169's own squash-merge — Present.**
   PR #3169 modifies `PREREG_PATH` (adds the `verification_pr:` field)
   but does not re-add it and does not touch `RESULTS_PATH` at all, so
   `_first_commit_for_path` (`--diff-filter=A`, added-only) still
   resolves both paths to the original `fb0bb0d3` commit after landing —
   the collision persists by construction, but the fallback re-reads
   *current* frontmatter content each run, so this is not a problem.
   Verified by literally simulating the squash: `git worktree add
   /tmp/main-plus-squash main && git merge --squash pr3169-review &&
   git commit` (one new commit, exactly how this repo's own squash-merge
   landing works), then ran the check for real against the real `gh` and
   the real PR #3131. derived:
   ```
   $ git log --diff-filter=A --follow --format=%H --reverse -- docs/issue-3127/decisions/pre-registration.md
   fb0bb0d349cfe27837b03c7ed9e3bc470887c9c8
   $ git log --diff-filter=A --follow --format=%H --reverse -- docs/issue-3127/_assets/consumer-path-results.json
   fb0bb0d349cfe27837b03c7ed9e3bc470887c9c8
   $ python3 scripts/issue-3127/verify_preregistration.py; echo "exit=$?"
   OK: same-commit collapse resolved via PR #3131's own pre-squash commit history -- docs/issue-3127/decisions/pre-registration.md first appears at commit index 0 (84226988e930981b02d00abd30e22c83100e875f), docs/issue-3127/_assets/consumer-path-results.json at index 1 (9c9801cd470129580de54b78a32abc30875de90e), strictly earlier
   exit=0
   ```
   No self-recreated collision blocks the check's own landing.

4. **Constructed-violation test — Present, independently re-derived.**
   PR #3169's own new test (`VerifyEndToEndCollisionTest::
   test_constructed_violation_is_refused_end_to_end`) was not taken on
   faith: rebuilt the same shape with an independent fixture
   (`/tmp/attack4_constructed_violation.py`, different tmpdir, different
   fake PR number `7777`, different commit SHAs `c1`/`c2` from the
   original test's `aaa1`/`bbb2`) through `verify()` end-to-end against
   a real local git repo reproducing the squash-collapse. derived:
   ```
   $ python3 /tmp/attack4_constructed_violation.py
   violation case: ok= False msg= PR #7777's own pre-squash commit history does NOT show docs/issue-3127/decisions/pre-registration.md strictly before docs/issue-3127/_assets/consumer-path-results.json (indices 1 vs 0) -- ...
   flipped (legitimate) case: ok= True msg= OK: same-commit collapse resolved via PR #7777's own pre-squash commit history -- ... strictly earlier
   DISCRIMINATES CORRECTLY: refuses violation, passes legitimate order
   ```
   Flipping the injected PR history from wrong-order to right-order flips
   the verdict from refused to passed, confirming the test discriminates
   rather than being a tautological always-`False`.

5. **Rejected content-digest alternative — agree with the rejection.**
   PR #3169's record rejects a self-digest scheme (pre-registration
   embeds a digest, results embeds the same digest) because it proves
   content correspondence, not temporal order: a single fabricated
   same-commit write can compute both freely. The task asked whether a
   digest committed on its own in an *earlier, separate* commit (which
   plain git ancestry would then order) closes that gap. It does not,
   for a structural reason the PR's record did not spell out explicitly:
   if such an earlier commit is a genuine, distinct ancestor of the
   later commit, plain ancestry *already* resolves the ordering for that
   case without needing any digest at all — `_first_commit_for_path`
   for `PREREG_PATH` would already predate `_first_commit_for_path` for
   `RESULTS_PATH`, hitting the plain-ancestry branch of `verify()`
   (`scripts/issue-3127/verify_preregistration.py:238-247` on PR #3169's
   branch), never `_resolve_via_pr_history` at all. The digest adds
   nothing there. The digest only matters in the exact problem case this
   PR exists for — everything squashed into one commit — and in that
   case there is no earlier distinct commit by definition, so a same-
   commit digest cannot establish that the threshold predates the
   result. Making the digest do real work requires binding it to
   evidence external to the collapsible git history (an issue comment,
   a PR's own retained pre-squash commit list) — which is not a digest
   scheme anymore, it is a variant of option (a), the PR's own chosen
   design. The rejection holds.

Ran the full test suite and the 12 new tests, both via `git worktree add
/tmp/pr3169-wt pr3169-review` (PR #3169's branch fetched as
`refs/pull/3169/head`) — derived:
```
$ cd /tmp/pr3169-wt && python3 -m pytest tests/ -q
364 passed, 2 warnings in 10.46s
$ grep -c "def test_" tests/test_issue_3127_verify_preregistration.py
12
```
The 2 warnings are the pre-existing `pinned-fixture-divergence` (issue
#3019) notices, unrelated to this change — matches PR #3169's own claim.

`silent-failure-audit` invoked on the new error-handling paths
independently of the builder's own audit: every explicit `gh`/JSON/
frontmatter failure path returns `False` with a reason (Handled) — see
cases B-F in item 2's derived output above; the `gh`/`git`-binary-missing
path is Unguarded (uncaught exception, loud exit) — case A in the same
derived output. Zero Silently Absorbed paths found independently.

`adversarial-review` applied directly in this single session rather
than via a spawned blind sub-session: this session did not build PR
#3169 (a different session/branch did — commit `1bd821e8` on branch
`issue-3127/...-9afe0675`), so builder/evaluator separation already
holds structurally — the skill's core mechanism (no shared context
window with the artifact's own reasoning) is satisfied without an extra
spawn. Findings were reached by running the code against constructed
adversarial fixtures, not by reading or trusting the builder's record's
own claims.

## Why

Graded by attacking, per the task's explicit instruction, not by
reading — canonical: this session's own task prompt text, angles 1-5,
quoted/paraphrased inline in "What was done" items 1-5 above. Angle 1
is the one substantive finding: the fallback's trust root binds to "a
PR with the right order somewhere in its history," not to "the PR that
produced the commit under review" — canonical: task prompt angle-1
wording, tested directly against the shipped code via `/tmp/attack1_
unrelated_pin.py` (derived output in item 1 above, `ok=True` on the
fabricated commit). Items 1-4 each have a runnable reproduction with
derived output shown inline above; item 5 has an explicit structural
argument in item 5 above (no code needed — it is a proof about which
branch of `verify()` a given commit-graph shape hits, not a runtime
behavior to exercise). Item 1 was graded Incorrect, not merely logged
as an open finding, because the task itself framed the check's
confirmation of PR provenance as the thing being graded — canonical:
`/tmp/attack1_unrelated_pin.py` derived output above, `ok=True` on a
commit the pinned PR never produced — and self-disclosure by the
builder does not change whether that property holds in the shipped
code.

## What did not work

None.

## Upstream basis

This record verifies PR #3169's own commit `1bd821e8b827f64b9827c0cf7a2
db3a2c7148d08` (the code/test commit) and `ddc091f065f0b36d1379aa0f37
adfb03f12c06b8` (the pre-registration-frontmatter commit) on branch
`issue-3127/...-9afe0675`, fetched locally as `refs/pull/3169/head`
(local alias `pr3169-review`, resolved head `63ab85bc2deee637e6823cfaf
866af8966763633` — derived: `git rev-parse pr3169-review`, run this
session) and exercised via `git worktree add /tmp/pr3169-wt
pr3169-review` plus a separate simulated-squash worktree (`git worktree
add /tmp/main-plus-squash main && git merge --squash pr3169-review &&
git commit`), both removed after use (`git worktree remove --force` —
derived: `git worktree list` after removal shows only this session's
own working tree). PR #3166's record was read via `gh pr view 3166
--json body` for root-cause context, not modified. Per contract, PR
#3169's branch is untracked on this session's own branch, so it is
cited as `PR-3169-branch:<path>` with the real commit sha in the
frontmatter `upstream:` list above, not as a plain tracked path.

## Open findings

- Angle 1 (Incorrect, see "What was done" item 1, derived: `/tmp/attack1_
  unrelated_pin.py` output, `ok=True`): `verification_pr:` binds trust
  to "any PR with the right order in its history," not to "the PR that
  produced the commit under review." Resolution path (not attempted
  here, out of this verification session's scope): require the
  collapsed commit under review to itself equal (or be reachable from)
  one of the referenced PR's own commit SHAs — e.g. compare the local
  HEAD commit's tree/parent against the PR's `headRefOid`/commit list,
  not just resolve the referenced PR's *own* internal order in
  isolation. PR #3169's own record already names this gap; a follow-up
  PR against `scripts/issue-3127/verify_preregistration.py` is the
  right vehicle, not a further verification round.
- The `gh`/`git`-binary-missing Unguarded path (angle 2): already
  self-disclosed by PR #3169 as an accepted, non-silent, out-of-scope
  gap. Confirmed independently this session — derived: `/tmp/attack2_
  gh_lying.py` case A output, "What was done" item 2 above — not
  disputed.

## Next steps

None for this verification session. `loop_state: done` refers only to
this session's own attack-and-grade work — canonical: `python3 -m
pytest tests/ -q` derived output above, `364 passed`, and the 5
attack-angle derived outputs throughout "What was done" — all
independently exercised with runnable output, no further check pending
in this session. The angle-1 finding (derived: `/tmp/attack1_
unrelated_pin.py`, `ok=True` on a fabricated pin) remains open as a
defect for a future repair PR against `scripts/issue-3127/
verify_preregistration.py` — not further work in this verification
session, which was scoped to attack-and-grade PR #3169 as it stands,
not to fix it.

## Skill verdicts

skill-verdict: adversarial-review — applied: invoked; ran the 5 attack
angles as live, runnable fixtures against PR #3169's code directly
(fixtures under /tmp/attack{1,2,4}_*.py, listed above with derived
output) rather than trusting the builder's own record's claims;
structural builder/evaluator separation already held since this session
did not author PR #3169.
skill-verdict: silent-failure-audit — applied: invoked; classified every
new error-handling path in `_resolve_via_pr_history` and its helpers
(gh repo/pr/api failures, malformed JSON, missing fields, path-absent,
wrong-order, mid-loop partial failure) as Handled or Unguarded, 0
Silently Absorbed, independently reproduced rather than cited from the
builder's own audit.
skill-verdict: experiment-trust — not-applicable: no A/B experiment
result is being interpreted or trusted this session; this is a
pre-registration ordering-check verification, not an experiment-result
review.
other mounted skills: implementation-audit and work-in-english were
also invoked (task-text-matched, not originally mounted) —
implementation-audit's Present/Surface/Absent/Incorrect/Unverifiable
taxonomy was applied to grade the 5 attack angles above; work-in-english
governed this record's and the fixtures' language (Korean reserved for
the final user-facing summary only).
