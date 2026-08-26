---
issue: 2381
role: conformance-review
author: conformance-review
loop_state: reported
type: review-record
code_under_review:
  - gates/check_runner.py
  - gates/merge_gate.py
  - .gitignore
  - on-the-record/directive/merge-gates.md
breaking: "none — this is a review record, no code changed by this role"
verdict: "pass — canonical: `python3 -m pytest gates/test_merge_gate.py gates/test_check_runner.py -q` (this session, ed4e1444) — 60 passed; ed4e1444:gates/merge_gate.py:208 (fetch call), ed4e1444:.gitignore:14-29 (untrack pattern)"
upstream:
  - path: docs/issue-2381/reports/implementation.md
    sha: dd55936b8b7a3626a8098311aa22483acf329f25
  - path: docs/issue-2381/reports/implementation.md
    sha: ed4e14449448cb2499a0e650c7c2621a2deb5b56
subject: PR #2445 (issue-2381/implementation, HEAD ed4e14449448cb2499a0e650c7c2621a2deb5b56) — "fetch all origin branches before gate worktree checkout"
test: issue #2381's own Acceptance section, https://github.com/tokenmaxxxer/on-the-record/issues/2381
result: "passed — canonical: `python3 -m pytest gates/test_merge_gate.py gates/test_check_runner.py -q` (this session, ed4e1444) — 60 passed; ed4e1444:gates/merge_gate.py:208 (fetch call), ed4e1444:.gitignore:14-29 (untrack pattern)"
assertedBy: conformance-review session, issue-2381 (builder-blind); re-review at ed4e1444 against a prior failed verdict at dd55936b
---

# issue-2381 — conformance-review record

Builder-blind conformance review of PR #2445 (branch `issue-2381/implementation`,
HEAD `dd55936b`, not present on `main` — `git merge-base --is-ancestor
8da6f009 origin/main` returned false this session) against issue #2381's
own Acceptance text, not against the implementation session's self-report.

canonical: `git worktree add --detach /tmp/review-2381 origin/issue-2381/implementation` (this session), `git -C /tmp/review-2381 rev-parse HEAD` —
```
dd55936b8b7a3626a8098311aa22483acf329f25
```
All citations below to files/lines that only exist on that branch are pinned as `dd55936b:<path>` (this checkout's own tree, based on `main`, does not contain them).

## Re-review at ed4e1444 (CHANGES round 2)

A CHANGES round landed on `issue-2381/implementation` addressing all
three open findings from the `dd55936b` review below (R1 Surface, R2b
Incorrect, R2c Absent — R2a was already Present and is carried forward
unchanged, its evidence untouched by any commit since). Re-derived each
independently against the PR's current head, not against the
implementation record's self-report of what it fixed.

canonical: `git fetch origin issue-2381/implementation && git worktree add --detach /tmp/review-2381b ed4e14449448cb2499a0e650c7c2621a2deb5b56 && git -C /tmp/review-2381b rev-parse HEAD` (this session) —
```
ed4e14449448cb2499a0e650c7c2621a2deb5b56
```
`gh pr view 2445 --repo tokenmaxxxer/on-the-record --json headRefOid -q .headRefOid` (this session) confirms the same sha is the PR's actual current head, not a stale local fetch.

**R1 (was Surface).** canonical: `sed -n '190,208p' /tmp/review-2381b/gates/merge_gate.py` (this session) —
```
    check_runner.fetch_all_role_branches(repo)
```
— this line sits inside `evaluate()`, immediately before the function's
only origin-ref-resolving call (`stale_revert_reasons()`), landed at
commit `19d20817` ("wire full-refspec fetch into merge_gate.py's own
landing path"). `grep -n "fetch" /tmp/review-2381b/gates/merge_gate.py`
(this session) now returns this call site plus its explaining comment,
where the `dd55936b` review's identical grep returned nothing. This
closes the exact gap R1 named: `merge_gate.py`'s `evaluate()` — and
`verdict_gate.py`, which calls it directly — no longer depends on
`check_runner.checkout_pr_worktree()` having already fetched the same
`--repo` checkout earlier in the same session; every caller now fetches
for itself. canonical: `python3 -m pytest gates/test_merge_gate.py gates/test_check_runner.py -q` (this session, `/tmp/review-2381b`, ed4e1444) —
```
60 passed in 1.29s
```
`grep -n "fetch_all_role_branches" /tmp/review-2381b/gates/test_merge_gate.py` (this session) shows the two `test_merge_gate.py` tests with a documented "no network" invariant now `monkeypatch.setattr(check_runner, "fetch_all_role_branches", lambda repo: None)` — the commit message for `19d20817` states its own before-landing hunt caught and fixed a regression here (an unstubbed real `git fetch` against GitHub origin breaking that invariant); independently confirmed present in the current test file rather than trusted from the message alone. Verdict: **Present**.

**R2b (was Incorrect).** canonical: `git diff main ed4e14449448cb2499a0e650c7c2621a2deb5b56 -- .orchestrate-hook-fires.log` (this session) shows the file's entire tracked content deleted (2845 lines); `git -C /tmp/review-2381b ls-files | grep -x '.orchestrate-hook-fires.log'` (this session) — empty output, exit 1: the path is no longer tracked at `ed4e1444`, where the `dd55936b` review's identical check returned it tracked (exit 0). This is a `git rm --cached`, not a bare `.gitignore` addition — the `dd55936b` review's finding was specifically that gitignoring an already-tracked path is a no-op against status drift; that gap is now closed. Verdict: **Present**.

**R2c (was Absent).** canonical: `git -C /tmp/review-2381b ls-tree -r --name-only main | grep -c '^\.orchestrate-hook-fires/'` (this session) —
```
9
```
— tracked shard files on `main` before this branch; `git -C /tmp/review-2381b ls-files | grep -c '^\.orchestrate-hook-fires/'` (this session, at `ed4e1444`) —
```
0
```
— zero remain tracked. `git -C /tmp/review-2381b show d74a24a99b6486140b3afedf251d0e9e6b7ec001 --name-only` (this session) lists the 10 shard-directory paths this commit's `git rm --cached` removed from the index (9 pre-existing on `main` plus 2 this branch itself had added meanwhile: `2cfde9a1f735d756b8e80c6b.log`, `9f5feb13badaeb330dfcc6e1.log` — one of the two, `9f5feb13...`, was added by this same branch's own `19d20817` commit, confirming the branch was still adding to the tracked pile mid-review). `.gitignore` at `ed4e1444` (diff quoted below) adds `.orchestrate-hook-fires/` as a directory-wide ignore pattern, closing the parenthetical's "or whichever local files keep drifting" gap the `dd55936b` review named. Verdict: **Present**.

canonical: `git diff main ed4e14449448cb2499a0e650c7c2621a2deb5b56 -- .gitignore` (this session) —
```diff
+.orchestrate-hook-fires.log
+.orchestrate-hook-fires/
```
(comment lines in the actual diff omitted here; full diff independently read this session, both new patterns confirmed present with no typo/anchoring defect — `.orchestrate-hook-fires/` with a trailing slash correctly matches the directory and its contents, not just a same-named file).

**Rollout-safety claim (architecture-consult concern).** The consult
flagged: once the ignore pattern lands, a session's attempt to commit
its own shard could be *silently* dropped — the exact failure class this
whole program (issue #2381/#2506) exists to eliminate, so the record
needs to state, not assume, why that doesn't happen here. `ed4e1444:docs/issue-2381/reports/implementation.md:200-217` (this session) states two distinct outcomes were checked, not assumed: an explicit `git add <exact-shard-path>` on an ignored path fails loudly (git refuses, non-empty stderr, exit 1), while a broad `git add -A`/`git add .` skips the ignored path with no error — and states that the broad-add case is safe specifically because `hook_fires.py`'s aggregator (`_hook_fires_dir`/`_hook_fires_aggregate`) only ever reads shards from the local session workspace on disk, never from a committed copy, so no reader anywhere depends on the shard surviving as a git object. Independently reproduced both outcomes this session rather than trusting the record's prose:

canonical: `cd /tmp/review-2381b && mkdir -p .orchestrate-hook-fires && touch .orchestrate-hook-fires/test-repro-shard.log && git add .orchestrate-hook-fires/test-repro-shard.log; echo "exit=$?"` (this session) —
```
다음 경로는 .gitignore 파일 중 하나 때문에 무시합니다:
.orchestrate-hook-fires
힌트: Use -f if you really want to add them.
exit=1
```
`git add -A; git status --short | grep orchestrate; echo "exit=$?"` (this session, same worktree) —
```
exit=1
```
(`grep` found nothing to match, confirming the broad add staged nothing under `.orchestrate-hook-fires/` — no output before the `grep`'s own non-match exit code). Both outcomes match the implementation record's claim exactly: explicit add loud-fails, broad add silently no-ops, and the silent no-op is verified safe here because it drops no reader-visible state, not asserted safe by assumption. This is a substantive answer to the consult's concern, not a restatement of it — **the rollout-safety statement is present and adequately grounded**.

## What was done

Decomposed issue #2381's 2 Acceptance `check:` bullets into 4 discrete,
dimension-tagged requirements (conformance-review-requirement-extraction):
bullet 1 stayed one item (its "documents or automates" clause is a
disjunctive success condition, not a bundled "and" obligation — rule 1
does not split it); bullet 2 named two specific files but explicitly
generalized with "(or whichever local files keep drifting)", so it was
split into three conditional line items — `roles/implementation.json`,
the literal `.orchestrate-hook-fires.log`, and the parenthetical's actual
current drift source — each independently checkable per rule 5, since
their expected verdicts do not depend on each other. Picked a verification
method per requirement (conformance-review-verification-method-selection):
Inspection for the structural/call-site claims (a function exists, is
wired to a call site, a `.gitignore` pattern is present, a path is
tracked or untracked), reusing the PR's own existing test suite as
Test-method evidence per rule 4 rather than re-deriving a parallel manual
check. Rendered one of the five verdicts per requirement
(conformance-review-verdict-assignment). Findings recorded below
(conformance-review-finding-record). Sampling was judged not-applicable —
the reviewable diff is 7 files (287 additions, 3 deletions), small enough
for full enumeration in one session (see Skill verdicts).

Verification actually executed this session (own commands against the
worktree checkout above and this checkout's own working tree, not pasted
from the implementation or investigation-agent's report):

canonical: `cd /tmp/review-2381 && python3 -m pytest gates/test_check_runner.py -q` (this session) —
```
35 passed in 53.64s
```
canonical: `grep -rn "fetch_all_role_branches" --include="*.py" /tmp/review-2381` (this session) —
```
gates/check_runner.py:394:def fetch_all_role_branches(repo: Path) -> subprocess.CompletedProcess:
gates/check_runner.py:430:    fetch = fetch_all_role_branches(repo)
```
canonical: `grep -n "fetch_all_role_branches\|checkout_pr_worktree" /tmp/review-2381/spawn.py` (this session) — empty output, confirming no wiring into `spawn.py`.

canonical: `grep -n "fetch" /tmp/review-2381/gates/merge_gate.py` (this session) — empty output, confirming `merge_gate.py` has no fetch call of its own; it relies entirely on `check_runner.checkout_pr_worktree()` having already refreshed the shared `--repo` checkout's `origin/*` refs earlier in the same session.

canonical: `sed -n '388,432p' /tmp/review-2381/gates/check_runner.py` (this session) — full body of `fetch_all_role_branches()` and its single caller `checkout_pr_worktree()`, quoted in R1's evidence below.

canonical: `git diff main origin/issue-2381/implementation -- .gitignore` (this session, from this checkout) —
```diff
+# issue #2381: pre-#2348 flat hook-fires counter. Issue #2348 replaced it
+# with per-session shards under .orchestrate-hook-fires/ (hook_fires.py /
+# on-the-record/hooks/hook-fires.sh) specifically to stop every session's
+# local edits to this one shared tracked path from diverging local main
+# from origin/main. Nothing writes this exact filename anymore; ignored
+# so no stray pre-#2348 branch/script can reintroduce that drift.
+.orchestrate-hook-fires.log
```
canonical: `git ls-files | grep -x '.orchestrate-hook-fires.log'` (this session, run against both this checkout's `main`-based tree and `/tmp/review-2381`'s PR-branch tree) — both print `.orchestrate-hook-fires.log`, exit 0: the path is tracked on `main` and remains tracked on the PR branch; no `git rm --cached` in the PR's diff.

canonical: this checkout's own `git status` at session start (see gitStatus in the session transcript) —
```
?? .orchestrate-hook-fires/dda3c5185257f38523a8dded.log
```
— an untracked file under the shard **directory**, not the flat `.orchestrate-hook-fires.log` the PR's `.gitignore` entry names. A second shard (`05d24bdde73e7204ae6254ee.log`) appeared later in the same session, confirming this is live, ongoing drift, not a one-off.

canonical: `git log --oneline -1 cea0f583 && git show cea0f583 --stat && git show cea0f583 -- .gitignore && git log --oneline -1 8ef2e3b7` (this session, this checkout) —
```
cea0f583 issue-2383: legacy-remnant audit — gitignore scratch, root-cause implementation.json corruption, age-prune worktrees
 .gitignore                                |   3 +
 .orchestrate-hook-fires.log               | 469 ++++++++++++++++++++++++++++++
 docs/issue-2383/reports/implementation.md | 431 +++++++++++++++++++++++++++
 gates/test_clean_reconcile_safety.py      |  67 +++++
 lifecycle.py                              |  82 +++++-
 spawn.py                                  |  30 +-
 tests/test_spawn_gate_wiring.py           |  80 ++---
 tests/test_spawn_pipeline.py              |  32 ++
8ef2e3b7 issue-2383: CHANGES round — root-cause implementation.json corruption, age-prune worktrees
```
`git merge-base --is-ancestor cea0f583 HEAD` (this session, this checkout) → exit 0 (true) — both commits are already on this branch's `main` base, independent of and prior to PR #2445.

Investigation of the PR's diff content, commit history, and self-authored
implementation/hunt/deviation records was delegated to one background
`freelunch:freelunch-worker` (per this session's freelunch directive,
consumed in-turn per contract v3 s22) before the checks above were run
independently; every claim taken from that delegated report that feeds a
verdict below was independently re-verified with the session's own
commands quoted above rather than trusted as-is.

## Findings

Fields per conformance-review-finding-record: requirement, spec_ref,
verdict, evidence, rationale, spec_vs_built (Incorrect only).

---
requirement: R1 — the orchestrator-facing directive or a spawn.py/gates helper documents or automates fetching all role branches (not just main) before running check_runner/merge_gate, so this isn't rediscovered per-session
spec_ref: issue #2381 Acceptance bullet 1
verdict: Present (re-derived at ed4e1444; was Surface at dd55936b — see original evidence/rationale below the update)
evidence: `ed4e1444:gates/merge_gate.py:190-208` — `evaluate()` now calls `check_runner.fetch_all_role_branches(repo)` itself, directly before its only origin-ref-resolving call (`stale_revert_reasons()`), landed at commit `19d20817`; `grep -n "fetch" gates/merge_gate.py` (this session, `/tmp/review-2381b`) now returns this call site plus its explaining comment, where the `dd55936b` review's identical grep returned nothing (see "Re-review at ed4e1444" section above); `python3 -m pytest gates/test_merge_gate.py gates/test_check_runner.py -q` (this session) — 60 passed, including two `test_merge_gate.py` tests whose documented "no network" invariant is preserved by stubbing the new call (`grep -n "fetch_all_role_branches" gates/test_merge_gate.py` shows `monkeypatch.setattr(check_runner, "fetch_all_role_branches", lambda repo: None)` at both sites)
rationale: the `dd55936b` Surface verdict rested on `merge_gate.py`'s `evaluate()` — and `verdict_gate.py`, which calls it directly — having no fetch of its own, meaning the original "fatal: invalid reference" failure could recur through either entry point independent of `check_runner.checkout_pr_worktree()`'s ordering. The CHANGES round closes exactly that gap: `evaluate()` fetches unconditionally on every call, regardless of caller or prior ordering, satisfying the bullet's literal "before running check_runner/merge_gate" condition for both gates rather than only the one that happened to run first. Present per conformance-review-verdict-assignment rule 1 (the code now fires on the literal condition the requirement names, not merely existing under a matching name).
---
Original `dd55936b` finding (superseded by the CHANGES round above, kept for traceability):
requirement: R1 — the orchestrator-facing directive or a spawn.py/gates helper documents or automates fetching all role branches (not just main) before running check_runner/merge_gate, so this isn't rediscovered per-session
spec_ref: issue #2381 Acceptance bullet 1
verdict: Surface
evidence: `dd55936b:gates/check_runner.py:394-417` (`fetch_all_role_branches()`, full-mirror refspec `+refs/heads/*:refs/remotes/origin/*` with `--prune`) called at `dd55936b:gates/check_runner.py:430` inside `checkout_pr_worktree()` — its only call site (see "What was done" grep, 2 hits, both in `check_runner.py`); `grep -n "fetch_all_role_branches\|checkout_pr_worktree" spawn.py` → no hits (same section above); `grep -n "fetch" gates/merge_gate.py` → no hits (same section above); documentation added at `dd55936b:on-the-record/directive/merge-gates.md` lines 336-349 ("you do NOT need to `git fetch` `--repo` yourself before this step")
rationale: a correct full-refspec, prune-safe fetch exists and is documented, and does cover the `check_runner.py` entry point end-to-end — but it fires from exactly one call site inside `check_runner.checkout_pr_worktree()`, never from `spawn.py` or any landing-sequence script as the bullet's own example ("a small wrapper... as part of `spawn.py ps`/the landing sequence") describes, and `merge_gate.py` has no fetch of its own — it only benefits because it happens to reuse the same `--repo` checkout `check_runner.py` already fetched into earlier in the same session. Run `merge_gate.py` against a `--repo` that hasn't already been through `checkout_pr_worktree()` in that session (e.g. a fresh persistent checkout, or `merge_gate.py` invoked standalone) and the original "fatal: invalid reference" failure this issue reports can still occur — the documentation's unconditional "you do NOT need to fetch yourself before this step" does not state that precondition. Matching code exists at the right name and shape and handles the common case, but does not fire on the literal condition the bullet names ("before running check_runner/merge_gate", both gates, unconditionally) — Surface, not Present, per conformance-review-verdict-assignment rule 1.
---
requirement: R2a — `roles/implementation.json`'s local drift is resolved: either gitignored (if session-local) or the process that dirties it is identified and fixed
spec_ref: issue #2381 Acceptance bullet 2
verdict: Present
evidence: `roles/implementation.json` remains tracked (`git ls-files | grep -x 'roles/implementation.json'` → tracked, not gitignored — the PR takes the "fix the process" branch of the disjunction, not the "gitignore" branch); root cause fixed at `8ef2e3b7:tests/test_spawn_gate_wiring.py` (three test methods patched to write to an isolated `spawn.ROOT` tempdir copy instead of the real tracked file), landed via `cea0f583` (issue-2383), both already ancestors of this branch's `main` base (see "What was done" canonical block above)
rationale: this half of the acceptance check is satisfied, but not by anything in PR #2445 itself — PR #2445 makes zero code changes toward it. `dd55936b:docs/issue-2381/reports/implementation.md` correctly cites `cea0f583`/`8ef2e3b7` as already having root-caused the corrupting writer before this PR opened; independently re-verified this session against the actual commit content (test methods now use a tempdir-patched `spawn.ROOT`, see "What was done" canonical block), not just trusted as an assertion.
---
requirement: R2b — `.orchestrate-hook-fires.log`'s local drift is resolved so local `main` doesn't need a stash before every rebase
spec_ref: issue #2381 Acceptance bullet 2
verdict: Present (re-derived at ed4e1444; was Incorrect at dd55936b — see original evidence/rationale below the update)
evidence: `git diff main ed4e14449448cb2499a0e650c7c2621a2deb5b56 -- .orchestrate-hook-fires.log` (this session) shows the tracked file's entire content deleted (2845 lines) by commit `d74a24a9`; `git -C /tmp/review-2381b ls-files | grep -x '.orchestrate-hook-fires.log'` (this session, at `ed4e1444`) — empty output, exit 1, confirming the path is no longer tracked (see "Re-review at ed4e1444" section above)
rationale: the `dd55936b` Incorrect verdict rested on the `.gitignore` pattern having no effect on an already-tracked path, since ignore rules don't retroactively untrack. The CHANGES round adds the missing `git rm --cached` (commit `d74a24a9`) alongside the existing ignore pattern, so the path is now both untracked and ignored — future edits to the working-tree file no longer surface in `git status`, eliminating the exact "stash before every rebase" symptom this requirement names. Present per conformance-review-verdict-assignment rule 1.
---
Original `dd55936b` finding (superseded by the CHANGES round above, kept for traceability):
requirement: R2b — `.orchestrate-hook-fires.log`'s local drift is resolved so local `main` doesn't need a stash before every rebase
spec_ref: issue #2381 Acceptance bullet 2
verdict: Incorrect
evidence: `dd55936b:.gitignore` adds `.orchestrate-hook-fires.log` (diff quoted above in "What was done"); `git ls-files | grep -x '.orchestrate-hook-fires.log'` on both `main` and `origin/issue-2381/implementation` → tracked on both (exit 0), confirming no `git rm --cached` accompanies the new ignore pattern (same canonical block, "What was done")
rationale: `git` ignore patterns have no effect on a path that is already tracked — future writes to a tracked-but-gitignored file still show as `modified` in `git status`, not suppressed, so the exact "stash before every rebase" symptom this half of the check exists to eliminate is undiminished for this path. This is not hypothetical: commits landing *after* the #2348 per-session-shard cutover the PR's own `.gitignore` comment cites as making the file dormant still wrote to it — `cea0f583` (+469 lines, see "What was done" canonical block), `a34a3aa5` (+1 line), `86f774d8` (+238 lines), all later than `96513f8c` (the #2348 sharding commit).
spec_vs_built: the acceptance wants the named file's drift eliminated ("gitignored... so local main doesn't need a stash before every rebase"); the PR added only a `.gitignore` pattern with no `git rm --cached`, which is a no-op against status-drift for a path git already tracks.
---
requirement: R2c — the parenthetical "(or whichever local files keep drifting)" is honored: the actual current source of untracked local drift is gitignored or its writer is fixed
spec_ref: issue #2381 Acceptance bullet 2, parenthetical clause
verdict: Present (re-derived at ed4e1444; was Absent at dd55936b — see original evidence/rationale below the update)
evidence: `git -C /tmp/review-2381b ls-tree -r --name-only main | grep -c '^\.orchestrate-hook-fires/'` (this session) — 9 tracked shard files on `main`; `git -C /tmp/review-2381b ls-files | grep -c '^\.orchestrate-hook-fires/'` (this session, at `ed4e1444`) — 0, none remain tracked; `git -C /tmp/review-2381b show d74a24a99b6486140b3afedf251d0e9e6b7ec001 --name-only` lists the 10 shard-directory paths `git rm --cached` removed from the index in that commit (see "Re-review at ed4e1444" section above for the full path list); `.gitignore` diff (`git diff main ed4e14449448cb2499a0e650c7c2621a2deb5b56 -- .gitignore`) adds `.orchestrate-hook-fires/` as a directory-wide ignore pattern
rationale: the `dd55936b` Absent verdict rested on the shard directory being neither gitignored nor untracked, while this same review session's own `git status` produced live untracked shards as evidence of ongoing drift. The CHANGES round's architecture consult re-examined the "keep it tracked by design" decision from the first CHANGES round against the actual reader code (`hook_fires.py`'s aggregator only ever globs the local workspace, never a committed copy) and reversed it: `git rm --cached -r .orchestrate-hook-fires/` plus the new ignore pattern closes the parenthetical's "or whichever local files keep drifting" gap this requirement names. Present per conformance-review-verdict-assignment rule 1.
---
Original `dd55936b` finding (superseded by the CHANGES round above, kept for traceability):
requirement: R2c — the parenthetical "(or whichever local files keep drifting)" is honored: the actual current source of untracked local drift is gitignored or its writer is fixed
spec_ref: issue #2381 Acceptance bullet 2, parenthetical clause
verdict: Absent
evidence: this session's own `git status` at start showed `.orchestrate-hook-fires/dda3c5185257f38523a8dded.log` (and later `05d24bdde73e7204ae6254ee.log`) untracked (quoted in "What was done" canonical block) — files inside the `.orchestrate-hook-fires/` shard directory, which the PR's `.gitignore` diff does not touch; `dd55936b:docs/issue-2381/reports/implementation.md` "Open findings" section explicitly names this exact gap ("The *new* per-session shard directory `.orchestrate-hook-fires/` is itself not gitignored, and produced a real untracked shard in this very session... Left open") rather than disputing it
rationale: the acceptance bullet names two specific legacy files but explicitly widens its own scope with "or whichever local files keep drifting" — i.e. the check is about whatever is *actually* causing drift, not only the two literally-named paths. The artifact this very review session observed drifting is the shard directory, not the flat log the PR gitignores; nothing in the PR's diff addresses it, and the PR's own implementation record concedes the gap rather than closing it. Nothing addresses this requirement — Absent, not Incorrect, per conformance-review-verdict-assignment rule 2 (omission, not a contradiction).
---

## Why

Reviewed builder-blind against the issue's own Acceptance text — the
2-bullet text was fetched and decomposed into the 4 requirements above
before opening `dd55936b:docs/issue-2381/reports/implementation.md` at
all. Inspection was the correct method for every requirement here (rule 1,
conformance-review-verification-method-selection): all four turn on
static/structural properties — does a function exist and where is it
called from, does a `.gitignore` pattern exist, is a path tracked or
untracked — none concern behavior under conditions this session could not
reproduce (Analysis) or a qualitative flow needing live exercise
(Demonstration) beyond the one existing test suite, reused per rule 4
rather than re-derived (see the `pytest gates/test_check_runner.py -q`
canonical block in "What was done": 35 passed). R2a additionally required
backward-tracing to a commit outside this PR (`8ef2e3b7`/`cea0f583`) —
independently re-inspected rather than taken on the implementation
record's word (canonical block in "What was done").

## Upstream basis

canonical: `gh issue view 2381 --repo tokenmaxxxer/on-the-record` (this session) — the 2 Acceptance bullets quoted/paraphrased above; `gh pr view 2445 --repo tokenmaxxxer/on-the-record` and `git worktree add --detach /tmp/review-2381 origin/issue-2381/implementation` (this session) — the code under review, checked out for independent grep/test execution (see "What was done").

- `dd55936b:docs/issue-2381/reports/implementation.md` — the delivering
  session's own record, including its self-authored "Open findings"
  section, which independently corroborates R2c (evidence quoted in R2c
  above).
- PR #2445, branch `issue-2381/implementation`, HEAD `dd55936b` (see this
  record's opening `git rev-parse HEAD` transcript) — the code under
  review, checked out into `/tmp/review-2381` via `git worktree add` for
  independent grep/test execution.
- Issue #2381 itself (`gh issue view 2381`, fetched fresh this session)
  for the 2 Acceptance bullets.
- `8ef2e3b7` / `cea0f583` (issue-2383, both already merged to `main`,
  outside PR #2445) — cited by the implementation record for R2a, and
  independently re-inspected this session (canonical block above and in
  "What was done") rather than trusted as-is.

## What did not work

canonical: `git ls-files | grep -x '.orchestrate-hook-fires.log'` and `cd /tmp/review-2381 && python3 -m pytest gates/test_check_runner.py -q` re-run independently this session after the delegated investigation report came back (transcripts in "What was done" above: tracked-file grep exit 0 on both trees, 35 passed) —
```
35 passed in 53.64s
```
- The first investigation pass (delegated to a background
  `freelunch:freelunch-worker`) reported `.gitignore` and tracked-file
  findings; this session did not treat that report as sufficient on its
  own and re-ran the tracked-file check (`git ls-files`), the `.gitignore`
  diff, the call-site greps, and the test suite independently against a
  fresh worktree before writing any verdict (canonical block immediately
  above, and the full set in "What was done") — no discrepancy turned up
  between the delegated report and the independent re-check, but the
  re-check was run regardless per this review's builder-blind mandate and
  conformance-review-verdict-assignment rule 6 (re-check a plausible
  false positive before finalizing Absent/Incorrect).
- A `git check-ignore -v --no-index -q` combination attempted mid-session
  (`-v` and `-q` together) errored (`--quiet 및 --verbose 옵션을 같이 쓸 수
  없습니다`); dropped `-q` for a version-agnostic `--porcelain`/`git status`
  based check instead (see the untracked-shard `git status` canonical
  block in "What was done"), which produced the same conclusion (the
  shard file is not matched by the PR's new `.gitignore` pattern) without
  depending on `check-ignore`'s conflicting-flag behavior.

Re-review at `ed4e1444` (this session): no dead ends. All three checks
(R1's `merge_gate.py` grep, R2b/R2c's `git ls-files` tracked-path counts,
and the rollout-safety `git add` reproduction) resolved cleanly on the
first independent attempt against the fresh `/tmp/review-2381b` worktree,
with no discrepancy against the implementation record's own claims —
canonical: "Re-review at ed4e1444" section above, all four canonical
blocks.

## Open findings

None remain open as of the `ed4e1444` re-review — canonical: full
independent re-derivation of R1/R2b/R2c in "Re-review at ed4e1444" above
(this session, `/tmp/review-2381b` at `ed4e14449448cb2499a0e650c7c2621a2deb5b56`).

- R1 (was Surface at `dd55936b`) — closed at `ed4e1444:gates/merge_gate.py:190-208`
  (`evaluate()` now fetches for itself, covering `verdict_gate.py` and
  any other direct caller regardless of execution order — see "Re-review
  at ed4e1444" above).
- R2b (was Incorrect at `dd55936b`) — closed by `d74a24a9`:
  `.orchestrate-hook-fires.log` untracked via `git rm --cached`, not just
  gitignored (`git -C /tmp/review-2381b ls-files | grep -x '.orchestrate-hook-fires.log'` this session, empty output).
- R2c (was Absent at `dd55936b`) — closed by `d74a24a9`: all shard files
  under `.orchestrate-hook-fires/` untracked and the directory gitignored
  (`git -C /tmp/review-2381b ls-files | grep -c '^\.orchestrate-hook-fires/'` this session — 0), reversing the first CHANGES round's
  "keep tracked by design" decision after an architecture consult found
  no reader depends on the tracked copy (`ed4e1444:docs/issue-2381/reports/implementation.md:190-217`).

R2a remains Present, carried forward unchanged from the `dd55936b`
review — no commit since has touched its evidence.

## Next steps

None — `loop_state: reported` (terminal for this record's kind).

## Skill verdicts

canonical: `cd /tmp/review-2381 && python3 -m pytest gates/test_check_runner.py -q` (first-pass session, transcript already given in full in "What was done" above) — 35 passed in 53.64s.
canonical: `python3 -m pytest gates/test_merge_gate.py gates/test_check_runner.py -q` (re-review session, `/tmp/review-2381b` at `ed4e14449448cb2499a0e650c7c2621a2deb5b56`, transcript in "Re-review at ed4e1444" above) — 60 passed in 1.29s.

First-pass session (against `dd55936b`):

skill-verdict: conformance-review-requirement-extraction — applied: invoked; kept bullet 1 as one item (disjunctive "documents or automates", not a bundled "and" — rule 1 doesn't apply), split bullet 2 into R2a/R2b/R2c because its parenthetical "(or whichever local files keep drifting)" widens the checkable scope beyond the two literally-named files and each sub-item's verdict does not depend on the others (rule 5), tagged each requirement's dimension inline in its rationale, no sampling-derivation override needed (issue states none)
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of the PR's 7 changed files was feasible in one session (287 additions, 3 deletions) — no reduction to a sample was needed
skill-verdict: conformance-review-verification-method-selection — applied: invoked; Inspection for all four requirements (structural/call-site/tracked-path properties, none needing Analysis or Demonstration); reused the PR's own `gates/test_check_runner.py` suite as Test-method evidence per rule 4 (independently re-run this session per the canonical block immediately above) rather than re-deriving a parallel manual check for the `--prune` fail-closed behavior
skill-verdict: conformance-review-verdict-assignment — applied: invoked; R1 Surface (rule 1 — matching code exists but doesn't fire on the literal "before running check_runner/merge_gate" condition for a standalone merge_gate run), R2a Present, R2b Incorrect (rule 2 — the built ignore-pattern doesn't address an already-tracked path, and `spec_vs_built` states the gap), R2c Absent (rule 2 — omission, not contradiction); R2c and R2b were both re-checked once against the current artifact state before finalizing (rule 6, see "What did not work")
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every Findings entry cites file:line plus the reviewed commit sha (`dd55936b:` prefix, or the specific external sha for R2a); backward-traced each requirement to its issue bullet before checking the implementation (rule 3, `spec_ref` names the bullet and, for R2c, the specific parenthetical clause); no multi-file-spanning requirement needed a second per-file link beyond what's already cited (rule 2 n/a); no duplicate-evidence entries to collapse (rule 4 n/a); single spec version in play — the issue as currently open (rule 5 n/a)
skill-verdict: conformance-review-finding-record — applied: invoked; wrote all 4 finding blocks with the full field list (requirement, spec_ref, verdict, evidence, rationale); R2b (the only Incorrect verdict) carries `spec_vs_built`; every verdict carries an evidence pointer and a spec_ref
skill-verdict: conformance-review-severity-classification — not-applicable: review scope was not extended into risk-weighting a recorded finding; this record only renders conformance verdicts (Present/Surface/Absent/Incorrect), not a severity band on top of them
skill-verdict: implementation-audit — not-applicable: this session ran under this repo's own role-handoff/conformance-review contract (a structurally independent evaluator session reviewing a separate builder session's delivery, builder-blind) — the same shape implementation-audit describes, but the mechanism in force here is the repo's native contract v3, not a separately-invoked implementation-audit protocol

Re-review session (against `ed4e1444`, this session):

skill-verdict: conformance-review-verification-method-selection — applied: invoked; Inspection for R1/R2b/R2c (structural call-site/tracked-path re-checks against the new head) and for the rollout-safety claim (re-reading the implementation record's stated reasoning); reused `gates/test_merge_gate.py`/`gates/test_check_runner.py` as Test-method evidence per rule 4 (re-run this session, 60 passed) rather than re-deriving a parallel manual check; additionally ran two ad hoc `git add` reproductions (Test-method, not Inspection) for the rollout-safety claim specifically because that claim is about live git behavior, not a static property, per rule 3 (qualitative functional claim needing actual stimuli, not just code-reading)
skill-verdict: conformance-review-verdict-assignment — applied: invoked; R1/R2b/R2c each moved Surface/Incorrect/Absent → Present (rule 1 — the code now fires on the literal condition each requirement names, not merely a matching name); R2a's prior Present carried forward unchanged since no commit since `dd55936b` touches its evidence (rule 4); none of the three moves risked being false positives in the Absent/Incorrect→favorable direction that rule 6 guards against (rule 6 is for the reverse direction — a plausible false-positive Absent/Incorrect — so it does not gate re-upgrading a verdict on new evidence; the upgrade was instead grounded in independently re-run commands, not trusted from the CHANGES-round commit messages alone)
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every updated Findings entry cites file:line plus the `ed4e1444`-pinned commit sha, and the superseded `dd55936b` blocks are kept rather than deleted so the verdict history traces backward (rule 1); R2c's evidence spans `.gitignore` and the shard-directory commit, both cited separately (rule 2); backward-traced each requirement to the same issue-#2381 bullet already established in the first pass, not re-derived (rule 3)
skill-verdict: conformance-review-finding-record — applied: invoked; updated the three Present verdicts in place with the full field list, kept the original Surface/Incorrect/Absent blocks below each as superseded-but-traceable rather than overwriting them silently
skill-verdict: conformance-review-requirement-extraction — not-applicable: no new requirements to extract this round — re-deriving the same four requirements the first-pass session already decomposed from issue #2381's Acceptance text
skill-verdict: conformance-review-sampling-derivation — not-applicable: the re-review scope was fully named by the task (R1, R2b, R2c, plus the rollout-safety claim) — no sampling decision to make
skill-verdict: conformance-review-severity-classification — not-applicable: this round still only renders conformance verdicts, not a severity band
skill-verdict: implementation-audit — not-applicable: same reasoning as the first-pass session — the repo's native contract v3 role-handoff, not a separately-invoked implementation-audit protocol
skill-verdict: silent-failure-audit — not-applicable: no error-handling paths (try/catch, Promise rejection, result type) were in scope for this re-review; the rollout-safety check exercised git's own ignore/add behavior directly (a git-level "silent no-op" concern, not an application-level swallowed exception), and was checked by direct reproduction rather than this skill's error-path enumeration method
other mounted skills: not triggered
