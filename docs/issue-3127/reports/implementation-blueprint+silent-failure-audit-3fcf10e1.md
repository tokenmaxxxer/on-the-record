---
issue: 3127
role: implementation-blueprint+silent-failure-audit-3fcf10e1
author: implementation-blueprint+silent-failure-audit-3fcf10e1
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: []
type: integration
breaking: false
verdict: all 4 stranded issue-3127 PRs (#3174, #3176, #3172, #3166) merged origin/main clean with zero conflicts and now pass all 3 issue-3127 acceptance checks that origin/main 1245c649 (PR #3169's verify_preregistration.py repair) unblocks. Handled in the assigned order, one at a time, each in its own git worktree (`git worktree add <path> origin/<branch> -B <branch>`). Per PR, in order: (1) `git merge origin/main -m "issue-3127: merge origin/main (picks up verify_preregistration.py fix from #3169)"` -- derived: `git status` immediately after each of the 4 merges -> "커밋할 사항 없음, 작업 폴더 깨끗함" (nothing to commit, clean) every time, confirming zero conflicts on all 4; (2) ran the 3 acceptance checks -- acceptance: `python3 scripts/issue-3127/run_consumer_pair.py --dry-run` — result: exit 0 on all 4; acceptance: `test -f docs/issue-3127/_assets/consumer-path-results.json` — result: exit 0 on all 4; acceptance: `python3 scripts/issue-3127/verify_preregistration.py` — result: exit 0 on all 4, each printing `OK: same-commit collapse resolved via PR #3131's own pre-squash commit history -- docs/issue-3127/decisions/pre-registration.md first appears at commit index 0 (84226988e930981b02d00abd30e22c83100e875f), docs/issue-3127/_assets/consumer-path-results.json at index 1 (9c9801cd470129580de54b78a32abc30875de90e), strictly earlier`; (3) ran the test suite -- derived: `python3 -m pytest tests/ -q` -> #3174: `535 passed, 2 warnings`; #3176: `539 passed, 2 warnings`; #3172: `536 passed, 2 warnings`; #3166: `535 passed, 2 warnings`; origin/main itself (checked before touching any branch, at commit 1245c649): `535 passed, 2 warnings`, matching the orchestrator's stated baseline; (4) pushed each merge commit to its own PR branch -- derived: `git push origin HEAD:<branch>` on all 4, each returning the expected `<old-sha>..<new-sha>` fast-forward line, no errors; (5) confirmed the push resolved GitHub's own conflict view, not just the local merge -- derived: `gh pr view <n> --repo tokenmaxxxer/on-the-record --json mergeable,mergeStateStatus -q '.mergeable, .mergeStateStatus'` on all 4 post-push -> `MERGEABLE` / `CLEAN` for every one. Did not merge any of the 4 PRs. No `keep-both` registry-row conflict resolution was needed on any of the 4 -- verified per-branch, not assumed: derived: `git diff --name-only origin/main...origin/<branch>` for each of the 4 (run before merging) shows none of the 4 touches `scripts/issue-3127/verify_preregistration.py` or `tests/test_issue_3127_verify_preregistration.py`, which are the only issue-3127 files origin/main changed since these branches were cut (commit 1245c649, PR #3169) -- so there was nothing on origin/main's side to collide with any of the 4 branches' own changes.
loop_state: landed
upstream:
  - path: PR #3169 (origin/main), verify_preregistration.py repair each of the 4 branches was blocked on
    sha: 1245c64967eb3c891f6ee50262226e6c834fdfa8
  - path: PR #3174 branch (issue-3127/implementation-blueprint+experiment-trust+silent-failure-audit-5bb45250), pre-merge tip
    sha: 6dd2e88e8b48ea72ba22e6ba0310ea60388cd16a
  - path: PR #3176 branch (issue-3127/implementation-blueprint+experiment-trust+silent-failure-audit-81dab610), pre-merge tip
    sha: db9f7d085c0071ae2171716fbc51201d8e17aead
  - path: PR #3172 branch (issue-3127/experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-e794089c), pre-merge tip
    sha: 570205e4d3e0921ef2892ea87a2659b142f90dc7
  - path: PR #3166 branch (issue-3127/experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-626f0a44), pre-merge tip
    sha: e269c6e92c7edd43a41041d4e04f057d8f1bd843
---

# issue-3127 — implementation-blueprint+silent-failure-audit-3fcf10e1 record

## What was done

Integration only; no deliverable behavior changed on any of the 4 PRs (`code_under_review: []` -- this session made no code changes, only merge commits carrying origin/main's own already-reviewed changes). Handled #3174, #3176, #3172, #3166 in that assigned order, one fully finished before the next started. See frontmatter `verdict:` for the full per-PR command+result citation of every merge, acceptance check, test run, push, and post-push `gh pr view` confirmation.

Post-merge PR head SHAs pushed -- canonical: `git rev-parse origin/<branch>` re-run for all 4 after push:

- #3174: 6fda58a92f8173848d288b97cd272472ea816b36
- #3176: 9568be0239c2940455f3e6c3670b8174d1e93a07
- #3172: 29b1867db2bbdfdab99c8cff4ada852c51d7d91d
- #3166: f3c170c1bcf32f7f36f80c4d2c21dbe8f9c61ea2

canonical: `gh pr view 3174 --repo tokenmaxxxer/on-the-record --json mergeable,mergeStateStatus` (and same command with 3176, 3172, 3166), run individually per PR post-push -- all 4 report `mergeable: MERGEABLE`, `mergeStateStatus: CLEAN`.

Per-PR one-sentence delivery summary, read from each PR's own body -- canonical: `gh pr view 3174 3176 3172 3166 --repo tokenmaxxxer/on-the-record --json body` (read individually, before touching any branch):

- **#3174** — fixes blocker A: threads an optional `skills_csv` pin through `pipeline.py`'s cross-family candidate-corpus check so a `--skills skill-repo:<name>`-qualified name is no longer treated as a cross-family conflict, unblocking the skills-off arm's dispatch that PR #3172 found broken.
- **#3176** — re-operationalizes H1 from a directive-composition-byte proxy (which PR #3172 found cannot see a skills-on/off difference for skills delivered via the runtime Skill tool) to real skill-invocation detection parsed from session logs; states its own delivery as partial, no pair scored yet.
- **#3172** — carries the real (partial) measurement data: both skills-on arms genuinely dispatched via `spawn.py --execute` and landed real phase-1 proposal PRs against the sandbox (`study-companion#23`, `#24`), with real wall-clock/cost/turns/directive-bytes recorded in `consumer-path-results.json`; both skills-off arms failed to dispatch on the cross-family defect #3174 later fixes.
- **#3166** — the first attempt: real execution blocked before any `spawn.py` dispatch (gh-guard refused seed-issue creation), and independently root-caused the squash-merge ordering defect in `verify_preregistration.py` that PR #3169 (and this integration) repairs.

Of the 4, **#3172** (real, partial measurement results) and **#3174** (the cross-family fix later runs, including #3176's own eventual full run, depend on) are the two that carry substance later work builds on; #3176 and #3166 are each an honest partial/blocked attempt layered on top of that substance.

None of the 4 is superseded by tonight's work: derived: `git log --oneline origin/main -30 -- pipeline.py directive_assembly.py spawn.py scripts/issue-3127/ docs/issue-3127/decisions/pre-registration.md` shows the only issue-3127-relevant commits on origin/main since these 4 branches were cut are `1245c649` (PR #3169, the repair each of the 4 needed) and `fb0bb0d3` (PR #3131, already an ancestor of all 4 pre-merge). No other origin/main commit touches `pipeline.py`, `directive_assembly.py`, `spawn.py`, `scripts/issue-3127/run_consumer_pair.py`, or the pre-registration doc -- so nothing on main independently re-does what any of the 4 set out to do; this is a judgment made and stated here, not resolved by integrating.

## Why

Merge (not rebase) preserves each branch's own commit SHAs so each PR's own session/verification records, which cite specific commit SHAs, stay valid after landing origin/main's fix -- per the task's explicit instruction, and consistent with the same merge-not-rebase approach this repo used for the same reason on other stranded PRs -- canonical: `docs/issue-3134/reports/implementation-blueprint+silent-failure-audit-a7bd5b30.md` and `docs/issue-3182/reports/implementation-blueprint+silent-failure-audit-ac57f5ad.md` (both prior integration records citing "merge, not rebase, to keep prior verification records' cited SHAs valid"). Finishing one PR (merge, checks, push, confirm) before starting the next, in the assigned order, keeps each branch's state independently inspectable via the frontmatter `verdict:` citations above and stops a mistake on one branch from compounding across all 4 before it's caught.

## What did not work

None.

## Upstream basis

- PR #3169 / commit `1245c64967eb3c891f6ee50262226e6c834fdfa8` (origin/main) -- the `verify_preregistration.py` repair that is the sole reason all 4 branches were failing acceptance check 3 before this integration.
- PR #3131 / commit `fb0bb0d3` -- the squash-merge collapse that PR #3169's fallback resolves; already an ancestor of all 4 branches pre-merge -- derived: `git merge-base --is-ancestor fb0bb0d3 origin/issue-3127/implementation-blueprint+experiment-trust+silent-failure-audit-5bb45250 && echo yes` -> `yes` (checked for #3174; same ancestry holds for the other 3, all cut from the same post-#3131 main -- derived: `git log --oneline origin/main..origin/<branch>` for each of the 4 shows only 2-3 commits ahead, none of them re-adding pre-registration.md, so #3131 is inherited, not reintroduced).
- `docs/issue-3127/decisions/pre-registration.md` (all 4 branches, unchanged by this integration) -- the pre-registered arms/threshold this measurement is scored against.

## Open findings

None on this integration's own scope -- derived: acceptance checks and `pytest tests/ -q` cited in `verdict:` above all pass on all 4 branches post-merge. #3172's and #3166's own "Open findings" (the gh-guard seed-issue block on #3166; the cross-family dispatch defect on #3172) remain open on those PRs' own deliverables and are unaffected by this merge -- canonical: `gh pr view 3172 3166 --repo tokenmaxxxer/on-the-record --json body` (same read cited above) -- #3174 fixes the cross-family defect, but that fix lives on #3174's own branch; it does not reach #3172's or #3166's branches until a future merge of #3174 (once it lands on main) forward into them. Resolution path: orchestrator merges #3174 to main first, then a follow-up integration merges main forward into #3172 and #3166 to pick up the fix -- out of this integration's own scope, which was limited to unblocking acceptance check 3 on all 4 without merging any PR.

## Next steps

None.
