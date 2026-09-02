---
issue: 3134
role: adversarial-review+silent-failure-audit+test-depth-audit-0516652a
author: adversarial-review+silent-failure-audit+test-depth-audit-0516652a
skills: adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3165 round four (code, on PR #3165's own branch) and PR #3173 (the merged round-four record)
code_under_review: e109ddadfb7562ad558ea4c22c6c77436821c2f2 (PR #3165's branch tip, HEAD of issue-3134/implementation-blueprint+silent-failure-audit+test-derivation+knowledge-management-supersession-lifecycle-b6857f11, checked live via `gh pr view 3165 --json headRefOid` this session; parent a9ebd8d7 is the pre-fix state)
loop_state: done
type: verification
breaking: false
verdict: canonical `gh pr view 3165` output (state OPEN, headRefOid e109ddad) plus this session's own live attacks against the real hook binary, both run against PR #3165's own branch (worktree checkout, never merged) -- all five of round four's claims (docs/issue-3134/reports/silent-failure-audit+test-derivation+implementation-blueprint-f38777c2.md, merged to main via PR #3173) are Present, reproduced live in "What was done" below. Two new, unaddressed gaps were found by attacking command shapes the round-four test suite never drives: a `-R`/`--repo` confirmation-scope drop, and stderr silence on every declined path including the confirmation step's own tooling failures. Neither is claimed as fixed by the round-four record, so neither makes its claims Incorrect; both are reported as Open findings for a possible next round. PR #3165 itself remains OPEN and unmerged -- the round-four code fix (e109ddad) lives only on its branch; only the round-four record (PR #3173) has landed on `main`.
upstream:
  - path: docs/issue-3134/reports/silent-failure-audit+test-derivation+implementation-blueprint-f38777c2.md (untracked on this branch -- merged to main via PR #3173, this branch has not pulled that main commit)
    sha: cad779163dd9704ad109c153f2a2d1d5bd050f9e
  - path: on-the-record/hooks/amends-landing-apply.sh, gates/amends_landing.py, tests/test_amends_landing_hook_e2e.py (all untracked on this branch -- exist only on PR #3165's own branch, not merged to main)
    sha: e109ddadfb7562ad558ea4c22c6c77436821c2f2
---

# issue-3134 — adversarial-review+silent-failure-audit+test-depth-audit-0516652a record

## What was done

canonical: `gh pr view 3165 --json title,body,headRefName,commits,state`, read this session in full. The code fix from this repair round (commit e109ddad) sits on PR #3165's own branch (state OPEN); the record for this round landed standalone on `main` via PR #3173. derived: `git ls-tree -r --name-only origin/main | grep -i amends` (run this session) -- result: no hook/gate/landing-test file present on `main`, only the earlier `amends_index.py` family. derived: `gh pr diff 3173 --name-only` (run this session) -- result: only the record file plus one deviation-log entry. Both scratch worktrees used for this session's own attacks (one at e109ddad, one at its parent a9ebd8d7) were built from a live `git fetch` of PR #3165's own branch, never from `main`; both were removed via `git worktree remove` before this record was written (git history of e109ddad on `origin` remains the citable source for every file:line below).

Per this round's spawning task ("attack the trigger, do not read it"), the real hook binary was driven with realistic `PostToolUse` JSON on stdin against a real bare-git remote + local checkout fixture built independently by this session (mirroring the test file's own fixture shape, not reusing its code), with a fake `gh` shim on `PATH` answering only `gh pr view ... --json state,mergedAt`. `git` and the real landing function were untouched. derived: this session's own driver script and fixture, `bash <hook>` invoked once per row below with a JSON PostToolUse payload on stdin, checking the bare remote's own tip commit before/after as ground truth for "did this push" -- full transcript is this turn's own tool-call history (scenarios re-run live, not from memory):

| # | Scenario | Expected | Result |
|---|---|---|---|
| A | `gh pr merge 42 --squash`, `gh pr view` confirms MERGED, one unresolved `amends:` edge present | push | pushed (`e4bfa3d1` → `218ffdf7`) |
| B | `gh pr merge --help`, `gh pr view` confirms MERGED (worst case), edge present | no push | no push, tip unchanged |
| C | `gh pr merge 42 --squash`, `gh pr view` reports `state: OPEN` (a real "not mergeable" failure), edge present | no push | no push |
| D | `gh pr merge 42 --squash`, `gh pr view` itself fails (exit 4, an auth-error shape), edge present | no push | no push |
| E | `gh pr merge --squash 42` (PR number AFTER the flag), `gh pr view` confirms MERGED, edge present | push | pushed -- PR-ref resolution is a bare digit-substring search over the whole post-`merge` command text, order-independent |
| F | `gh pr merge 42 -R someorg/other-repo --squash` (merging a PR in a DIFFERENT repo), `gh pr view` confirms MERGED | should confirm the `-R` target specifically, not an unrelated same-numbered local PR | pushed anyway -- `-R`/`--repo` is silently dropped before the confirmation call; see Open findings item one |
| G | `gh pr merge 42 --squash`, tool_response text contains the word "merged" inside a PR *title* (deceptively), but `gh pr view` reports `state: OPEN` | no push | no push -- tool_response text is not consulted at all |
| H | `cd DIR && gh pr merge --help` (the `cd DIR &&` variant), `gh pr view` confirms MERGED, edge present | no push | no push -- the non-merge-flag check is matched against every token, not a fixed position |
| I | `gh pr merge --squash` with NO explicit PR number, `gh pr view` (bare, no ref) confirms MERGED, edge present | untested by the suite; upstream record's own prose claims this shape is "left unreached" under real `gh` semantics | pushed, under a fake `gh` that answers unconditionally regardless of args -- see Open findings item three |

Scenarios B, C, D, G, H each produced empty stderr on the declining run -- checked this session by inspecting each run's captured `stderr` directly, not inferred. Only the final landing-function call's own execution failures write to stderr (two sites cited under silent-failure-audit below).

Separately, the hook-driving test file's `test_help_invocation_never_pushes` test was reproduced pre-fix by checking out the literal parent commit (not `git stash`, which the upstream record used and which this round's own task named as insufficient evidence) into a second worktree, with the test file copied over since it is new on the post-fix branch. derived: run this session, in order --
```
$ git log --oneline -1 a9ebd8d7
a9ebd8d7 issue-3134: repair round three -- deviation-log entry for record-claim-guard retries

# post-fix (e109ddad):
$ python3 -m pytest tests/test_amends_landing_hook_e2e.py -v
4 passed

# pre-fix (a9ebd8d7, test file copied in):
$ python3 -m pytest tests/test_amends_landing_hook_e2e.py -v
3 passed, 1 failed -- test_help_invocation_never_pushes:
AssertionError: 'd043e8d5...' != 'e6a03662...'
```
The bare remote's own tip commit changed in response to `gh pr merge --help` on the pre-fix hook -- the same defect PR #3168 originally reproduced.

Full acceptance + suite checks, run this session against PR #3165's own branch at e109ddad:
```
python3 -m pytest tests/test_amends_resolution.py -q      # 19 passed
python3 gates/probe_amends_is_discoverable.py; echo $?     # exit 0
python3 gates/probe_amends_fails_closed.py; echo $?         # exit 0
python3 -m pytest tests/ -q                                 # 335 passed, 2 warnings
python3 -m pytest test/ -q                                  # 563 passed, 3 xfailed, 0 failed
```
derived: all five commands above run this session, in order, against the e109ddad worktree -- every number matches the upstream record's own reported figures exactly.

**silent-failure-audit**, applied against the hook script's PostToolUse guard and the landing function's `land()` body (both read in full this session at e109ddad, both untracked on this branch). derived: manual enumeration this session, one row per distinct `except`/`if ... returncode`/`sys.exit(0)` site walked in source order --
```
1. json.loads(payload) except ValueError -> sys.exit(0)                         Silently Absorbed (no stderr)
2. shlex parse except ValueError -> sys.exit(0)                                  Silently Absorbed (no stderr)
3. NON_MERGE_FLAGS match -> sys.exit(0)                                         intentional decline, not an error path
4. gh pr view: except (OSError, SubprocessError) -> sys.exit(0)                  Silently Absorbed (no stderr)
5. gh pr view: returncode != 0 -> sys.exit(0)                                    Silently Absorbed (no stderr)
6. gh pr view: json.loads except ValueError -> sys.exit(0)                       Silently Absorbed (no stderr)
7. gh pr view: state != MERGED or no mergedAt -> sys.exit(0)                     intentional decline, not an error path
8. git remote get-url origin fails -> sys.exit(0)                                Silently Absorbed (no stderr)
9. land() subprocess: except (OSError, SubprocessError) -> stderr write, exit 0  Handled
10. land() subprocess: returncode != 0 -> stderr write                          Handled
11. amends_landing.py::land() git-status returncode != 0 -> explicit error      Handled (this round's own fix)
```
Verdict per row confirmed by direct read of the source (not just grep): only rows 9, 10 and 11 write to stderr on failure; rows 1, 2, 4, 5, 6 and 8 are all silent, and the forward trace for each is identical -- a genuine tooling failure at that site (bad `gh` auth, network error, malformed JSON, `git` misconfigured) is indistinguishable on stderr from a legitimate "not merged yet" decline (rows 3, 7). This confirms the upstream record's own git-status-porcelain fix claim (row 11: Present) and surfaces the asymmetry named in Open findings item two, which the upstream record does not claim to have addressed.

**test-depth-audit**, applied against the hook-driving test file's test methods (`test_help_invocation_never_pushes`, `test_failed_merge_never_pushes`, `test_successful_merge_zero_edges_never_pushes`, `test_genuine_merge_with_edge_pushes_the_backlink`, all read in full this session at e109ddad, untracked on this branch). Each contains at least one falsifiable `assertEqual`/`assertNotEqual`/`assertIn` on the bare remote's own tip commit or landed content -- classified Genuine Assertion, derived: read of all four test bodies this session, no test found with an execution-only or mock-dominated shape. verification density (derived: computed this session from that classification, every listed test classifies Genuine Assertion) = 100%. One of them (`test_help_invocation_never_pushes`) was additionally confirmed via live mutation -- checking out the literal pre-fix parent commit is a real mutation of the code under test, and exactly that one test fails as a direct consequence (reproduced above), proving its assertion is load-bearing rather than decorative. The other tests pass unchanged at both commits, which is expected (this round fixed one specific defect) and does not demote them. Suite-level gap: none of the tests drive `-R`, a `cd DIR &&` prefix, a PR number preceding its flags, an implicit no-number merge, or a `gh pr view`-itself-fails shape -- derived: scenarios D, E, F, H, I above, each run manually this session precisely because the suite does not cover that shape.

## Why

This session ran as a structurally independent evaluator per the adversarial-review skill: it never built any part of any prior repair round, received only the artifact (PR #3165's branch plus PR #3173's record) and this round's own attack list, and drove the real hook binary directly rather than trusting either record's prose description of what the code does. Code was read only to locate exact file:line citations for findings already reproduced live, per this repo's own defect-citation requirement, never as a substitute for driving the binary. Checking out the literal parent commit (rather than `git stash`) was used for the pre-fix reproduction because this round's own task named `git stash` explicitly as insufficient evidence -- a stash can be popped incorrectly, restore into a dirty tree, or leave uncommitted state that doesn't match what a reviewer merging the PR would actually get; checking out the parent commit in a second worktree reproduces the literal commit the PR forked from.

The two new findings (the `-R` confirmation-scope drop, and stderr silence on tooling failures) came from extending the attack list past the scenarios the upstream suite itself covers, per the adversarial-review incentive that a report with zero findings on a non-trivial deliverable means the attack wasn't thorough enough. Both were reproduced live in this session's own scratch fixture, not merely reasoned about from reading the source.

## What did not work

None -- every scenario in this round's attack list was reproduced against the real hook binary on the first attempt; no scenario required rebuilding the fixture for a failed attempt (fixtures were rebuilt between push-consuming scenarios by design, since a successful push consumes the fixture's only `amends:` edge).

## Upstream basis

canonical: `gh pr view 3165` and `gh pr view 3173` output, both read in full this session -- see frontmatter `upstream:` for the exact paths and shas cited. `docs/issue-3134/reports/silent-failure-audit+test-derivation+implementation-blueprint-f38777c2.md` is the record whose claims this session graded (untracked on this branch, sha in frontmatter). The three code files this session attacked live only on PR #3165's own branch (untracked on this branch, sha in frontmatter). `docs/issue-3134/reports/adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-b2918fea.md` (PR #3168, merged to `main`, tracked on this branch at commit a9ebd8d7) was read for context on what PR #3168 originally reproduced, not relied on for this session's own verdicts -- every verdict above was reproduced live this session, independent of PR #3168's own account.

## Open findings

1. **`-R`/`--repo` is accepted by the command-shape check but dropped before the confirmation call.** The hook's guard builds the `gh pr view` confirmation command with no `-R`/`--repo` flag even when the original `gh pr merge` command carried one -- reproduced live as scenario F above. Real `gh pr view <n>` without `-R` resolves the repo from the checkout's own `origin` remote, not the `-R` target, so a merge of PR #N in a different repo is "confirmed" against whatever PR #N happens to exist in the checkout's OWN repo -- which may not exist, may be OPEN, or may coincidentally be MERGED and unrelated. Blast radius is bounded: the landing function is always scoped to the checkout's own `origin`/default-branch regardless of `-R`, per the hook's own "repo-local" design premise (read this session, its own header comment), so this can never push to the wrong external repo -- but the confirmation step's own stated guarantee ("state comes from `gh pr view` itself, never from tool_response text") does not hold for `-R`-shaped commands. Resolution path: either reject any command containing `-R`/`--repo` (conservative, matches the hook's own repo-local scope), or parse `-R`'s value through to the confirmation call. Out of this session's own scope (verification only); left for a future round.
2. **Every declined path is silent on stderr**, including the confirmation step's own tooling failures (`gh` unauthenticated, network error, malformed JSON, missing `origin` remote) -- see the silent-failure-audit table above, rows 1, 2, 4, 5, 6 and 8. An operator cannot distinguish "correctly declined, not merged yet" from "the confirmation mechanism itself is broken" from stderr alone. Given the hook's own explicit fail-open-and-silent design intent for legitimate declines, logging every decline may be over-scoped for a PostToolUse side-effect hook -- but logging specifically the tooling-failure branches while leaving the legitimate-decline branches silent would close the ambiguity without changing the fail-open posture. Left for a future round.
3. **The implicit no-number `gh pr merge` shape has zero test coverage**, reproduced as scenario I above under a fake `gh` shim that cannot distinguish it from the numbered case. Not a code defect by itself -- the upstream record's own reasoning for why real `gh pr view` would fail closed here is plausible -- but it is an unverified claim with no regression guard in the suite.

None of the items above make any of this round's explicit claims Incorrect; all of them are Present, reproduced live in "What was done" above.

## Next steps

None. derived: this turn's own tool-call history -- no `gh pr merge`, `gh pr edit`, or `gh pr comment` call was made against PR #3165 this session, and no file under PR #3165's own branch was edited; only this record file and scratch state under `/tmp` (removed) were written. `loop_state: done` is set on the basis of the acceptance-block codefence above (all five commands run this session, matching the upstream record's own numbers) plus the nine-scenario table and the pre-fix/post-fix pytest reproduction, both reproduced live this turn rather than assumed from either upstream record's prose.

skill-verdict: adversarial-review — applied: invoked; this session ran as a structurally independent evaluator of PR #3165/#3173's own deliverable, drove the real hook binary rather than trusting the upstream record's prose, and extended the attack surface past the upstream suite's own scenarios to reach the Open findings above
skill-verdict: silent-failure-audit — applied: invoked; enumerated and classified the error-handling sites in the hook's PostToolUse guard and the landing function's `land()` body (table above), confirmed the upstream record's own git-status-porcelain fix Handled, and found the confirmation step's own tooling failures Silently Absorbed under the same silence as a legitimate decline (Open finding on stderr silence)
skill-verdict: test-depth-audit — applied: invoked; classified the tests in the hook-driving test file as Genuine Assertion, confirmed one via live mutation (checkout of the pre-fix parent commit), and named the suite's own command-shape coverage gap (the implicit-merge Open finding, plus scenarios F, H and I run manually this session)
