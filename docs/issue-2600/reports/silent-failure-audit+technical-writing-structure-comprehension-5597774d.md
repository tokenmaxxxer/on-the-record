---
issue: 2600
role: silent-failure-audit+technical-writing-structure-comprehension-5597774d
author: silent-failure-audit+technical-writing-structure-comprehension-5597774d
skills: silent-failure-audit (skill-repository(297e350)), technical-writing-structure-comprehension (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review:
  - path: on-the-record (52 files, cherry-picked from PR #2673's `ee7c8c92` and fixed — see "What was done")
    sha: same-commit
  - path: tokenmaxxxer-core (re-derived only, no commits — audited by PR #2673, not touched here)
    sha: 764aebc19c7e01fedd0078805c75740ac777b9a6
type: audit-and-fix
breaking: false
verdict: send-back fix for PR #2673, applied. Fixed exactly the three items independent verification (PR #2674, merged) required: (1) re-derived tokenmaxxxer-core's acceptance-regex count from scratch — the PR's claimed 934->934 was false, true tracked-content count at `764aebc` is 933->933, zero drift from PR #2668's baseline; (2) removed the out-of-scope `consult.py:492-497` hunk (new content about issue #2610, itself containing 4 new "role" occurrences); (3) rebased PR #2673's commit onto current `origin/main` (8862a33b), resolving one merge conflict in `pipeline.py`. Also surfaces one pre-existing defect in the inherited PR content, out of this send-back's 3-item scope: see Open findings.
loop_state: landed
upstream:
  - path: docs/issue-2600/reports/technical-writing-structure-comprehension+silent-failure-audit-2d35eeab.md
    sha: same-commit
  - path: docs/issue-2600/reports/adversarial-review+technical-writing-structure-comprehension-3f30f496.md
    sha: 8862a33b1b6b9a3b1e6e6f7e8b9a9c9d9e9f9a9b
---

# issue-2600 — silent-failure-audit+technical-writing-structure-comprehension-5597774d record

## What was done

This is a send-back fix for PR #2673 ("retire teaching-current-model 'role'/역할 wording from comments and docstrings", on-the-record half of #2600's comment/docstring slice). Independent verification (PR #2674, merged) refused two of that PR's four carrying claims and it went CONFLICTING against `main`. The spawning task authorized exactly three fixes, nothing else. All three are done.

**1. Re-derived tokenmaxxxer-core's acceptance-regex count from scratch.** PR #2673 claimed `grep -rIo --exclude-dir=.git --exclude-dir=docs -iE '\brole\b|역할' .` returned 934 both before and after, at pinned sha `764aebc`, and explained the 1-occurrence drift from PR #2668's 933 baseline as "unrelated landings on main" — impossible, since a commit sha is immutable. Re-running that exact grep against the local `/home/jwjung/tokenmaxxxer-core` working tree (already checked out at `764aebc`) still reproduces 934, but that count is contaminated: an untracked file left over from an unrelated session, `.landing-obligations/218-implementation-219.json`, contains one "role" occurrence and the plain `grep -r .` walks it even though it was never part of the pinned commit.
derived: `cd /home/jwjung/tokenmaxxxer-core && grep -rIo --exclude-dir=.git --exclude-dir=docs -iE '\brole\b|역할' .landing-obligations .on-the-record` — result: 1 hit, in `.landing-obligations/218-implementation-219.json`.
derived: `rm -rf /tmp/core-clean-764aebc && mkdir -p /tmp/core-clean-764aebc && cd /home/jwjung/tokenmaxxxer-core && git archive 764aebc | tar -x -C /tmp/core-clean-764aebc && cd /tmp/core-clean-764aebc && grep -rIo --exclude-dir=.git --exclude-dir=docs -iE '\brole\b|역할' . | wc -l` — result: `933`.
The true tracked-content count at `764aebc` is 933, matching PR #2668's own baseline exactly — zero drift. The PR's negative conclusion (nothing in core was in scope for this comment/docstring slice) is not disturbed by this correction; only the number offered as its evidence was wrong, and it is now the re-derived 933 -> 933 (no commits, no in-scope occurrences, confirmed above).

**2. Removed the `consult.py:492-497` hunk.** That hunk was not a wording rewrite of existing prose — it added a new sentence about issue #2610's behavior (the skill-catalog lookup being unconditionally skipped since that issue landed), and the new sentence itself used "role" 4 times, so a PR whose whole purpose is retiring that word was net-adding 4 new occurrences of it in exactly the file it touches.
derived: `git diff origin/main -- consult.py` (pre-fix, on the cherry-picked commit) — result: single hunk at `@@ -492,8 +492,10 @@`, +4 lines all containing "role" (`role 을`, `role 검증`, `role 카탈로그`, `role 을`).
The hunk is reverted; `consult.py` is now byte-identical to `origin/main`.
derived: `git diff origin/main -- consult.py` (post-fix) — result: empty.
If issue #2610's behavior is worth documenting, that is new content for a separate issue, not a rider on a wording-retirement PR — not attempted here.

**3. Rebased onto `main`.** PR #2673's branch was cut from `d3ef7b8d` (`origin/main` at the time); current `origin/main` is `8862a33b`, four commits ahead (`c4b7578e`, `e593a895`, `ee84c21d`, `8862a33b`), which is what made the PR CONFLICTING.
derived: `git merge-base pr2673-orig origin/main` — result: `d3ef7b8d2c50f37d91837327116495c3c9cf9282` (stale; not `origin/main`'s current tip).
This branch was reset to `origin/main` (`8862a33b`) and PR #2673's single commit (`ee7c8c92`) cherry-picked on top. One conflict, in `pipeline.py`: `origin/main` had already renamed `MUSTER_ROLE_MODEL` to `MUSTER_SKILL_MODEL` in a comment (landed via PR #2668, merged after PR #2673 branched); PR #2673 rewrote the same comment's "역할 세션" to "스폰된 세션" without knowing about that rename. Resolved by keeping `MUSTER_SKILL_MODEL` (the current, already-landed name) with PR #2673's wording rewrite applied on top — combining both independent changes rather than picking one side.
derived: `git diff origin/main -- pipeline.py | grep -A2 'MUSTER_SKILL_MODEL\|MUSTER_ROLE_MODEL'` — result: single line, `# MUSTER_SKILL_MODEL / role_model.txt (이슈#93): 스폰된 세션이 쓰는 모델을`.
acceptance: `git status --short` (after cherry-pick, before this record's own untracked file) — result: no unmerged paths, no conflict markers.
derived: `grep -rn '^<<<<<<<\|^=======$\|^>>>>>>>' --include=*.py --include=*.sh -r .` — result: empty (no leftover conflict markers anywhere in the tree).

**Not done, and correctly so per the spawning task's explicit scope:** the README/UNENFORCED-CLAUSES deferral (claim 4, verified PRESENT by PR #2674) and the vocabulary-substitution claim were both left exactly as PR #2673 left them — not re-litigated here.

## Why

The spawning task named three specific, independently-verifiable defects and said "nothing else." Re-deriving a wrong number the naive way (rerunning the same grep in the same dirty working tree) would have reproduced the same wrong 934 — the fix required noticing *why* the number was wrong (working-tree contamination from an unrelated session's leftover file, not a moving target), which only a clean re-derivation (`git archive` into an empty directory, so only tracked content at the pinned sha is walked) can settle. Presenting a plausible-sounding but false explanation ("unrelated landings on an immutable sha") for a wrong number is worse than the number being wrong in the first place, since it invites a future reader to stop looking — this record replaces that explanation with the actual mechanism and a reproducible command.

`consult.py`'s hunk was reverted wholesale rather than edited down to remove just the retired word from its new sentence, because the sentence's entire reason for existing was to document issue #2610's behavior — trimming the word out while keeping the sentence would still be new content riding on a wording-retirement PR, just with the smell hidden.

The `pipeline.py` conflict was resolved by merging both independent changes (the already-landed env-var rename, this PR's wording rewrite) rather than accepting one side wholesale, since dropping either one would silently regress a change that had already correctly landed on `main` (accepting incoming-only) or reintroduce "역할" prose to a comment already in scope for rewriting (accepting ours-only).

## What did not work

None — no deviation from the three authorized fixes was needed; the pipeline.py conflict was the only unplanned obstacle and resolved as described above without expanding scope.

## Upstream basis

Builds on PR #2673's single commit `ee7c8c92` (cherry-picked, then fixed) and its own record `docs/issue-2600/reports/technical-writing-structure-comprehension+silent-failure-audit-2d35eeab.md` (foreign-authored; contract v3 s11 forbids editing another session's existing lines in that file, so its two false claims — the core count and the consult.py-inclusive file list/counts — are left as originally written there, not corrected in place; the true figures are in this record instead). Also builds on the independent verification in `docs/issue-2600/reports/adversarial-review+technical-writing-structure-comprehension-3f30f496.md` (PR #2674, merged), whose two refusals are what this record fixes.
canonical: `gh pr view 2674 --json state` — result: `state: MERGED`.

## Open findings

1. **A pre-existing defect in PR #2673's own content, discovered incidentally while verifying this fix, out of this send-back's 3-item scope — not fixed here.** `on-the-record/hooks/approval-gate.sh` is asserted byte-identical to `origin/main` by an existing test (`test/test_auto_approval_shadow_wiring.py`, class `SimulatedApprovalAppendsSampleTest`, method `test_approval_gate_sh_is_byte_identical`), but PR #2673's own commit `ee7c8c92` (unchanged by anything in this session) edits that file's comments — so the PR's own test-plan claim of "identical failing-test set before and after" is also false, independent of the two claims PR #2674 already refused.
   derived: `python3 -m pytest test/ -q` — before (`origin/main`, `8862a33b`, via `git worktree add --detach /tmp/onrec-before-wt origin/main`): `15 failed, 358 passed, 3 xfailed`; after (this branch, `HEAD`): `16 failed, 357 passed, 3 xfailed`.
   derived: `diff <(sort /tmp/failed_before.txt) <(sort /tmp/failed_after.txt)` — result: exactly one new failing test, in `test/test_auto_approval_shadow_wiring.py`.
   derived: `git diff d3ef7b8d pr2673-orig -- on-the-record/hooks/approval-gate.sh` — result: non-empty (comment-only, "role-session"/"acting role's own" -> "spawned-session"/"acting session's own"), confirming this is PR #2673's own original content, present before this session's rebase and unrelated to the `pipeline.py` conflict resolution. Not fixed here: reverting it would mean second-guessing which files belong on the load-bearing-exclusion list PR #2673's own author built, which is a 4th item beyond this send-back's authorized three. Resolution path: whoever next touches this file (or re-reviews PR #2673's content) should add `on-the-record/hooks/approval-gate.sh` to the load-bearing exclusion list this slice already built for other files, and revert this one comment hunk.
2. **PR #2673 (`issue-2600/technical-writing-structure-comprehension+silent-failure-audit-2d35eeab`, open, CONFLICTING) is superseded by this branch's PR** and will be closed with a pointer to it, so the board does not carry two competing open PRs for the same slice of work.
   derived: `gh pr view 2673 --json state,mergeable` — result: `state: OPEN`, `mergeable: UNKNOWN` (conflicting against `main` as described in "What was done").

## Next steps

- Land this PR (`Advances #2600`, matching PR #2673's own trailer — this is still a partial slice of the larger retirement issue, not a full close).
- Close PR #2673, pointing at this one.
- A future slice should pick up Open finding 1 above (`approval-gate.sh`) before the comment/docstring kind can be called fully clean.

skill-verdict: silent-failure-audit — not-applicable: invoked (Skill tool call this session, full procedure read); this session's change is a cherry-pick + one comment revert + one merge-conflict resolution in a comment line, with no new try/catch, Promise, result-type, or other fallible-operation code path introduced or touched.
derived: `git diff origin/main -- . ':!docs'` (this session's own diff, see "What was done" above) — result: 52 files, all changed lines confirmed comment/docstring-only by the tokenize-based checker in the linked verification record — no error-handling code path exists in the diff for the skill's procedure to audit.

skill-verdict: technical-writing-structure-comprehension — not-applicable: invoked (Skill tool call this session, full procedure read); this session's writing is a citation-heavy correction record following the mandated record skeleton (numbers, commands, results), not a sentence/paragraph/section restructuring pass on existing prose for reader comprehension.
derived: this record's own "What was done" section above — every paragraph pairs a claim with an inline `derived:`/`acceptance:` command-and-result citation, the skeleton's mandated shape, not a comprehension-driven restructuring of pre-existing prose.
