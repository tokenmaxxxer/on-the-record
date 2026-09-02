---
issue: 3127
role: adversarial-review+experiment-trust+silent-failure-audit-6095e2ff
author: adversarial-review+experiment-trust+silent-failure-audit-6095e2ff
skills: adversarial-review (skill-repository(c05de12)), experiment-trust (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true  # independent, builder-blind verification of PR #3169's round-2 repair (commits 466811aa, 34401620), attacking the merge-commit binding and the rename fix, plus a fresh empty-as-pass sweep of the whole file
loop_state: done
code_under_review: PR #3169 head 344016209e383381f7a2dd98cd01689038366eff (round-2 commits 466811aab97277dbb960c01d16fa7b3ce56333cf, 344016209e383381f7a2dd98cd01689038366eff), base origin/main 02335dd8d894670ce855fe3239f60e57c1ad8838
type: verification
breaking: false
verdict: PR #3169 round 2 is Present on both of its own claims (merge-commit
  bind, --follow drop) and Incorrect against one residual defect outside
  its claimed scope (self-disclosed in the round-2 builder's own record,
  independently re-confirmed here via a different reproduction), both
  graded below with reproductions.
upstream:
  - path: PR-3169-branch:scripts/issue-3127/verify_preregistration.py
    sha: 344016209e383381f7a2dd98cd01689038366eff  # this session's own branch carries an EARLIER version of this path (pre-round-2, from main); the round-2 version reviewed here is untracked on this session's own branch and lives on PR #3169's branch, read/exercised via a git worktree of origin/issue-3127/implementation-blueprint+experiment-trust+silent-failure-audit-9afe0675
  - path: PR-3169-branch:tests/test_issue_3127_verify_preregistration.py
    sha: 344016209e383381f7a2dd98cd01689038366eff  # untracked on this session's own branch (does not exist there at all); lives on PR #3169's branch, same worktree basis
  - path: docs/issue-3127/reports/experiment-trust+adversarial-review+silent-failure-audit-760379f7.md
    sha: same-commit  # round-1 verification record (PR #3171), read for the original angle-1 attack shape and grading vocabulary
---

# issue-3127 — adversarial-review+experiment-trust+silent-failure-audit-6095e2ff record

## What was done

Independent, builder-blind verification of PR #3169's round-2 repair
(commits `466811aa` bind, `344016209e` drop-`--follow`), pushed directly
to PR #3169's own branch by the round-2 session (PR #3177 carries only
that session's own record, not the code). Worked in a detached-HEAD git
worktree of `origin/issue-3127/implementation-blueprint+experiment-trust+silent-failure-audit-9afe0675`
(untracked on this session's own branch; lives on PR #3169's branch),
attacking the shipped code with fresh, independently constructed live
fixtures. PR #3169 was not merged or edited.
canonical: `git worktree add /tmp/pr3169-verify origin/issue-3127/implementation-blueprint+experiment-trust+silent-failure-audit-9afe0675 --detach` this session, HEAD 344016209e383381f7a2dd98cd01689038366eff.

### 1. Reproduced PR #3171's original angle-1 attack against round-2 code

`verification_pr: 9999` pinned at an unrelated, legitimately-ordered PR
(`legit1`→PREREG, `legit2`→RESULTS) whose merge commit does NOT equal the
colliding commit. Before round 2 this returned `ok=True` (PR #3171).
acceptance: `python3 /tmp/atk/attack_binding.py` — result:
```
[PASS] A: unrelated-legit-PR pin (original PR3171 attack): ok=False msg=PR #9999's merge commit (cafebabecafebabecafebabecafebabecafebabe) does not match the colliding commit under review (fca782e58c1c268972816f94d2b115f921fd0032) -
```
Grade: **Present.**

### 2. Attacked the merge-commit binding with four further shapes

Each constructed independently (own temp git repo + own fake `gh` runner,
distinct from the shipped test file's fixtures):
- merge commit equal to the colliding commit, but the PR's own recorded
  history never touches `PREREG_PATH`/`RESULTS_PATH`
- pin at a still-open/closed-unmerged PR (`mergeCommit` null)
- pin at a PR number that does not exist (`gh pr view` fails)
- `gh repo view` failing after the merge-commit bind already succeeded

acceptance: `python3 /tmp/atk/attack_binding.py` — result:
```
[PASS] B: bound-PR merge commit matches, but PR never touched the two paths: ok=False msg=PR #4242's commit history has no commit touching both files (or the lookup failed) -- cannot resolve ordering (fail closed)
[PASS] C: pin at open/unmerged PR (mergeCommit null): ok=False msg=PR #5001 has no recorded merge commit (`gh pr view 5001 --json mergeCommit` failed or returned none) -- cannot confirm it actually produced the colliding commit
[PASS] D: nonexistent PR number (gh pr view fails): ok=False msg=PR #999999 has no recorded merge commit (`gh pr view 999999 --json mergeCommit` failed or returned none) -- cannot confirm it actually produced the colliding co
[PASS] E: repo-view fails post-bind: ok=False msg=could not resolve the GitHub owner/repo (`gh repo view` failed) -- cannot query PR #3131's commit history
```
All five (this item's four plus item 1) fail closed with a message naming
what did not match. `/tmp/atk/attack_binding.py` is a scratch harness
this session wrote, not committed to any repo (evidence is the quoted
output above, run this session). Grade: **Present.**

### 3. Merge-strategy variants (rebase-merge, merge-commit-strategy PRs)

Not attacked with a constructed fixture; reasoned instead. The bind
(untracked on this session's own branch; `scripts/issue-3127/verify_preregistration.py:213`
on PR-3169-branch sha 344016209e383381f7a2dd98cd01689038366eff) is a
full 40-char content-addressed SHA comparison
(`merge_commit != colliding_commit`) that neither side is
attacker-controllable on: `gh pr view --json mergeCommit` reports the
pinned PR's real GitHub-recorded landing commit regardless of merge
strategy, and the colliding commit is the actual local commit under
review. Equality by anything other than the local commit literally being
that same real commit would require a SHA collision. No merge-strategy
value changes this argument; item 2's "matches but PR never touched the
paths" case already exercises the SHA-equality mechanism itself. Grade:
**Present, by reasoning, no fixture attempted** (not miscounted as a
fixture-verified item).

### 4. Attacked the rename fix

First reproduced the underlying git behavior directly (not through the
script) on this box's git.
acceptance: `git --version && git log --diff-filter=A --format=%H --reverse --follow -- a/real.txt && git log --diff-filter=A --format=%H --reverse -- a/real.txt` (in a fresh scratch repo with a placeholder renamed via `git mv` into `a/real.txt`) — result:
```
git version 2.34.1
--- with --follow ---
(empty)
--- without --follow (current fix) ---
4667f5fcf5364de0dbd0c14f43862364d0a60916
```
This confirms the shipped docstring's claim (untracked on this session's
own branch; `scripts/issue-3127/verify_preregistration.py:66-79` on
PR-3169-branch sha 344016209e383381f7a2dd98cd01689038366eff) against raw
git, not against the script's own framing of it.

Then two fresh end-to-end scenarios through `verify()` (own temp repos,
covering the side the shipped test file does not: `PREREG_PATH` renamed,
not `RESULTS_PATH`):
acceptance: `python3 /tmp/atk/attack_rename.py` — result:
```
[PASS] S1: prereg renamed-in AFTER results already committed (violation): ok=False expect_ok=False msg=pre-registration commit 1078100a6e98b74904d48477133b37065cff431f is NOT an ancestor of results commit e92e1654357ccdc2f81facd13d99d45d2c7c2c
[PASS] S2: both paths renamed-in, correct order (legitimate): ok=True expect_ok=True msg=OK: pre-registration commit a2d0cd9526429e20b888fd8e392e1cfc415bba07 is an ancestor of results commit 2e7e6156fe5814d47596b85989d7f14756014d

ALL PASS
```
S1 refuses the violation (results renamed-in before a late-renamed
prereg); S2 passes the legitimate case, showing the fix doesn't
overcorrect into "any rename anywhere fails." Grade: **Present.**

### 5. Swept the whole file for other empty/failure-as-pass shapes

Applied `silent-failure-audit`'s enumerate→classify→trace-forward steps
over every fallible git/`gh` call in `verify_preregistration.py`
(untracked on this session's own branch; PR-3169-branch sha
344016209e383381f7a2dd98cd01689038366eff).

- `_run_git`/`_default_gh_runner` (no try/except around
  `subprocess.run`): classified Unguarded — a missing `git`/`gh` binary
  is a loud crash, not a silent one. Same as round-1 verification's
  finding on this point (`docs/issue-3127/reports/experiment-trust+adversarial-review+silent-failure-audit-760379f7.md`,
  same-commit, angle 2), unchanged by round 2.
- `_read_frontmatter`, `_repo_owner_repo`, `_pr_merge_commit`,
  `_pr_commit_order`, `_first_pr_commit_touching`: classified Handled —
  every failure mode returns `None`/`{}`, and every caller treats that
  as fail-closed (already exercised live in items 1-2's fixtures).
- `git merge-base --is-ancestor`'s exit code (untracked on this
  session's own branch; `verify_preregistration.py:302-318` on
  PR-3169-branch) is explicitly split three ways (ancestor /
  not-ancestor / real git error reported as an error) — classified
  Handled, a correct counter-example in the same file.
- **`_first_commit_for_path`** (untracked on this session's own branch;
  `verify_preregistration.py:81-86` on PR-3169-branch) classified
  **Silently Absorbed downstream**: `if r.returncode != 0: return None`
  is followed by `return lines[0] if lines else None` — a real command
  failure and a genuinely-empty-but-successful result both collapse to
  `None`. `verify()`'s `results_commit is None` branch (untracked on
  this session's own branch; `verify_preregistration.py:284-291` on
  PR-3169-branch) reads that `None` as "results not yet committed" and
  returns `ok=True` — correct for genuine-empty, wrong for
  command-failure.

Forward trace, reproduced live by monkeypatching `vp._run_git` to return
`returncode=128` for exactly the `RESULTS_PATH` query, in a repo where
`RESULTS_PATH` is genuinely already committed in the correct order (so a
forced failure here cannot be explained away as "would have failed
anyway"):
acceptance: `python3 /tmp/atk/attack_empty_as_pass.py` — result:
```
Results genuinely committed at: 6299f42f18581f6f52d51ba0a2f8065439dac136
verify() -> True OK: docs/issue-3127/decisions/pre-registration.md committed at 1cdb5fadafd30d12b1239d89bfac014064ac99d3; docs/issue-3127/_assets/consumer-path-results.json not yet committed (working tree only), so it cannot precede the pre-registration
CONFIRMED: a git-command failure on the RESULTS_PATH lookup is
silently read as 'not yet committed' and the check PASSES, even
though the results file is genuinely already committed (at 6299f42f18581f6f52d51ba0a2f8065439dac136 ) and the ordering was never actually checked.
```
site → return value → caller behavior → downstream consequence:
`_first_commit_for_path` line 83-84 → `None` (on a simulated real git
failure, not a genuine absence) → `verify()` line 284 reads `None` as
"not yet committed" → returns `ok=True` with a fabricated-sounding "not
yet committed" message while the file is in fact already committed and
the true order was never checked. This contradicts the module's own
docstring (untracked on this session's own branch;
`verify_preregistration.py:29-31` on PR-3169-branch sha
344016209e383381f7a2dd98cd01689038366eff): "Unavailable evidence is a
failure, never a pass." Grade: **Incorrect** — residual, not closed by
round 2.
derived: `git show --stat 344016209e383381f7a2dd98cd01689038366eff` this session — round 2's own diff touches only `scripts/issue-3127/verify_preregistration.py` and its test file, +17/-1 lines, none of it the `_first_commit_for_path` returncode branch this finding is about.

**Not a fresh discovery — already self-disclosed.** The round-2 builder
session itself found and named this exact site
(untracked on this session's own branch;
`docs/issue-3127/reports/implementation-blueprint+experiment-trust+silent-failure-audit-cc11fc03.md`,
same-commit, "Open findings" first bullet, lines 313-328) after invoking
`silent-failure-audit` post-landing, with its own reproduction (a
different forcing method — an unknown `git log` flag —
`git log --diff-filter=A --format=%H --reverse --nonexistent-flag -- <path>`
exits 128) reaching the same `_first_commit_for_path`/`results_commit is
None` conclusion this session's monkeypatch reproduction reaches
independently. Same pattern as round 1's angle-1 finding, which was
also self-disclosed in PR #3169's own record before being formally
graded — this session's contribution is an independent reproduction via
a different mechanism (direct `_run_git` monkeypatch vs. an invalid CLI
flag) confirming the same conclusion, not the discovery itself.

No injection seam exists for `_run_git` failures through the public
`verify(repo_root, gh_runner=...)` API — reproducing this required
monkeypatching the module attribute directly. This looks more like a
reliability gap under real git failures (disk pressure, a corrupt pack,
a concurrent `git gc`) than an attacker-controlled bypass on demand:
both pathspecs are fixed string constants, so there is no obvious way
from outside the process to make only the `RESULTS_PATH` query fail.

### 6. The standing question

What would it take to satisfy this check without genuinely
pre-registering first:
- genuine two-commit ancestry — this **is** the real property, not a
  bypass.
- the same-commit fallback post-round-2 — requires the local colliding
  commit to be SHA-identical to a real, already-merged PR's recorded
  merge commit (item 3's argument); achieving that requires literally
  holding the real commit, at which point its real history is
  legitimately trustworthy evidence, not a forgery.
- item 5's defect — inducing a real git-command failure on the
  `RESULTS_PATH` lookup specifically. Not ruled out, not shown reliably
  attacker-triggerable either.
- the property no git-ancestry-only check can verify, round 2 or
  otherwise: git ancestry proves *construction order in the repo*
  (commit B's parent-hash must reference commit A, so A must already
  exist as an object before B can be created), not *decision order in
  the author's head*. An author who already knows the intended result
  content can author the threshold to fit it, then commit prereg first
  and results second — identical git state to doing it honestly. This
  costs exactly the same two-commit sequence either way, so it is not
  "easier than doing it honestly" in effort, but the check cannot
  distinguish the two cases at all. Not something round 2 (or round 1)
  claimed to solve; flagged as an inherent limitation of the whole
  design approach, not a defect specific to this PR.

### 7. Ran the issue's three acceptance checks, live, on this branch

acceptance: `python3 scripts/issue-3127/run_consumer_pair.py --dry-run` — result: exit 0 (plan printed; unaffected by round 2, out of this task's scope, run per the task instruction).
acceptance: `test -f docs/issue-3127/_assets/consumer-path-results.json` — result: present.
acceptance: `python3 scripts/issue-3127/verify_preregistration.py` — result:
```
OK: same-commit collapse resolved via PR #3131's own pre-squash commit history -- docs/issue-3127/decisions/pre-registration.md first appears at commit index 0 (84226988e930981b02d00abd30e22c83100e875f), docs/issue-3127/_assets/consumer-path-results.json at index 1 (9c9801cd470129580de54b78a32abc30875de90e), strictly earlier
```
exit 0. This is the real-world instance of item 3's "legitimate
squash-collapse, real gh, real already-merged PR" case, using real PR
#3131. Grade: **Present**, all three.

### 8. Ran `tests/` in full on this branch

acceptance: `python3 -m pytest tests/ -q` (cwd `/tmp/pr3169-verify`) — result:
```
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
1 failed, 367 passed, 2 warnings in 11.24s
```
`tests/test_spawn_gate_wiring.py` is untracked on this session's own
branch; it lives on PR #3169's branch, same worktree basis as above.

Confirmed unrelated to round 2, not a regression:
derived: `git show --stat 466811aab97277dbb960c01d16fa7b3ce56333cf 344016209e383381f7a2dd98cd01689038366eff` this session — both commits together touch only two paths, `scripts/issue-3127/verify_preregistration.py` (this session's own branch carries an earlier, pre-round-2 version of this same path) and `tests/test_issue_3127_verify_preregistration.py`, which is untracked on this session's own branch and lives only on PR #3169's branch.
acceptance: `python3 -m pytest tests/test_spawn_gate_wiring.py -q` run in a second worktree checked out at `origin/main` (02335dd8d894670ce855fe3239f60e57c1ad8838) — result:
```
27 passed in 9.99s
```
So the failure is this PR branch predating main's later, unrelated
hooks.json additions, not something round 2 broke.

`tests/test_issue_3127_verify_preregistration.py` is untracked on this
session's own branch; it lives only on PR #3169's branch.
acceptance: `python3 -m pytest tests/test_issue_3127_verify_preregistration.py -q` (cwd `/tmp/pr3169-verify`) — result:
```
16 passed in 0.86s
```
Grade: **Present, with the staleness caveat stated** — PR #3177's own
claim of "368 passed" reflects that this failure had not yet appeared
when round 2 ran its own check; main has since advanced.
derived: `git merge-base --is-ancestor origin/main HEAD` this session, run inside the PR #3169 worktree — result: exit 1 (origin/main is NOT an ancestor of this branch's HEAD, confirming this branch was cut before main's later commits).

## Why

The task asked for an adversarial attack on two specific claims (the
merge-commit bind, the `--follow` drop) plus a fresh sweep for the same
defect shape elsewhere in the file, plus the standing question about
what the check can and cannot prove. All four are load-bearing for
whether issue #3127's acceptance check 3 (`verify_preregistration.py`)
is trustworthy enough to gate a real experiment's pre-registration — the
reason `experiment-trust` is mounted even though the object of study
here is a verification tool, not an experiment result (see skill
verdicts below). Constructing fresh fixtures independently, rather than
re-running the shipped test suite or trusting PR #3171/#3177's own
narration, is `adversarial-review`'s mechanism.
canonical: items 1-5 above, each with its own `acceptance:`/`derived:` citation and quoted command output produced this session.

## Open findings

1. **`_first_commit_for_path`'s command-failure/genuine-empty
   conflation** (untracked on this session's own branch;
   `verify_preregistration.py:83-86` on PR-3169-branch sha
   344016209e383381f7a2dd98cd01689038366eff), consumed by `verify()`'s
   `results_commit is None` pass-branch (same file, line 284-291) — not
   fixed by round 2, and already self-disclosed by the round-2 builder
   session itself (untracked on this session's own branch;
   `docs/issue-3127/reports/implementation-blueprint+experiment-trust+silent-failure-audit-cc11fc03.md`,
   same-commit, "Open findings" first bullet). This session's
   contribution is an independent reproduction via a different
   mechanism: `/tmp/atk/attack_empty_as_pass.py`,
   quoted in full under item 5 above (ephemeral scratch script, not
   committed — exists to demonstrate the defect this turn, not as
   permanent coverage; fixing it is a future round's call, not this
   session's, per "do not edit PR #3169"). Suggested direction for a
   future round: distinguish a real command failure
   (`r.returncode != 0`) from a genuine empty result
   (`returncode == 0` with no matching lines) inside
   `_first_commit_for_path` itself, the same distinction
   `merge-base --is-ancestor`'s own three-way exit-code split already
   makes two functions further down the same file (item 5 above).
2. **The construction-order-vs-decision-order gap** (item 6 above) is
   not resolvable by any git-ancestry check, this one included — not
   routed anywhere as a fix, flagged for the next reader's awareness.
3. Merge-strategy variants (item 3) verified analytically only, no
   fixture. Reasonable next step for defense in depth, not a currently
   open gap.

## Next steps

No further action identified for this session; any fix to Open finding 1
is left to a future round, per the task's instruction not to edit PR
#3169.

## What did not work

The `board-gate` hook refused an initial `cat > file << 'EOF'` heredoc
used to stage a scratch attack script (a shape it cannot read the write
target of, per that hook's own stated jurisdiction) — switched to the
`Write` tool for all scratch attack scripts under `/tmp/atk/`, which are
outside this session's own repo write set entirely (ephemeral evidence,
not a repository write). No retry against the gate was needed after
that.

## Skill verdicts

- skill-verdict: adversarial-review — applied: invoked; structurally
  independent evaluator session (this session did not build PR #3169's
  round-2 code) attacking the shipped code with fresh, independently
  constructed fixtures rather than trusting PR #3171/#3177's own
  narration or re-running only the shipped test suite.
  canonical: items 1-5 above (this record, this section).
- skill-verdict: silent-failure-audit — applied: invoked; ran the
  enumerate-classify-trace-forward procedure over
  `verify_preregistration.py` (item 5 above), which surfaced Open
  finding 1.
  canonical: item 5 above (this record, this section).
- skill-verdict: experiment-trust — not-applicable: this task verifies a
  pre-registration-ordering tool, not an actual randomized experiment
  result (no assignment, no traffic, no metric to run an SRM/A-A check
  against) — the skill's own Step 1 scope gate routes this shape of work
  elsewhere; its "pre-committed design" framing informed why the check
  matters (see "Why"), but none of its numeric gates (SRM, A/A) apply.
