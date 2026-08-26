---
issue: 2381
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: gh issue 2381
    sha: same-commit
code_under_review:
  - path: gates/check_runner.py
    sha: 5a41d0d7a6126ce76e29ba2739be01e66553a470
  - path: gates/merge_gate.py
    sha: same-commit
  - path: gates/test_merge_gate.py
    sha: same-commit
  - path: on-the-record/directive/merge-gates.md
    sha: same-commit
  - path: .gitignore
    sha: same-commit
  - path: docs/issue-2381/reports/implementation/2026-08-26-hunt-orchestrator-fetch-all-branches.md
    sha: same-commit
  - path: docs/issue-2381/reports/implementation/2026-08-26-hunt-untrack-orchestrate-hook-fires.md
    sha: same-commit
type: fix
breaking: none
verdict: pass
---

# issue-2381 — implementation record

## What was done

- `gates/check_runner.py`: extracted the single-branch `git fetch origin
  <head_ref>` call inside `checkout_pr_worktree()` into a new
  `fetch_all_role_branches(repo)` helper that instead runs
  `git fetch origin '+refs/heads/*:refs/remotes/origin/*'` (the full
  mirror refspec, destination explicit). `checkout_pr_worktree()` is the
  only fetch site in `check_runner.py`, and `gates/merge_gate.py` never
  fetches on its own — it reuses the same `--repo` checkout right after
  `check_runner.py` runs — so this one call site covers both gates named
  in the issue.
- `on-the-record/directive/merge-gates.md`: added a note under
  "ACCEPTANCE CHECK-RUNNER AT LANDING" stating the manual full-refspec
  fetch workaround described in the issue is no longer needed, since
  `checkout_pr_worktree()` now does it automatically.
- `.gitignore`: added `.orchestrate-hook-fires.log` (the flat, pre-#2348
  hook-fire counter file named in the issue as a cause of local-`main`
  drift), since nothing writes that exact filename anymore.

canonical: `git diff -- gates/check_runner.py on-the-record/directive/merge-gates.md .gitignore` (this commit's diff — matches all three bullets above)

acceptance: `python3 -m pytest gates/test_check_runner.py -q` — result:
```
35 passed in 51.87s
```

### CHANGES round (conformance-review, three gaps)

The prior cut's rationale ("`gates/merge_gate.py` never fetches on its
own — it reuses the same `--repo` checkout right after `check_runner.py`
runs") was true only for callers that happen to run `check_runner.py`
first against that exact checkout. It is not true for
`gates/verdict_gate.py`'s `main()`, which calls `merge_gate.evaluate()`
directly (its own CLI entry point, documented as the actual script the
"VERDICT-ASYMMETRY AT MERGE" landing step in
`on-the-record/directive/merge-gates.md` runs), nor for
`gates/ci.py`'s direct call to `merge_gate.stale_revert_reasons()`. Both
bypass `check_runner.py` entirely, so the exact "fatal: invalid
reference" failure the issue reports could still happen through them.

- R1 fix: `gates/merge_gate.py`'s `evaluate()` now calls
  `check_runner.fetch_all_role_branches(repo)` itself, immediately before
  the one check inside it that resolves an `origin/<base_ref>` ref
  (`stale_revert_reasons()`). `evaluate()` is the single function every
  caller (`merge_gate.main()`, `verdict_gate.py`, and anything importing
  `merge_gate`) funnels through, so this covers all of them regardless of
  call order — mirroring the "one shared call site" shape
  `check_runner.py`'s own fix already used. Best-effort: the call's
  return value is discarded, matching `stale_revert_reasons()`'s existing
  fail-open behavior when refs can't be resolved — a synthetic test repo
  with no `origin` remote fails the fetch fast and harmlessly, and the
  fetch failing does not change any assertion in the tests re-run below.
  `on-the-record/directive/merge-gates.md`'s issue-#2381 paragraph is
  updated to match (it previously asserted `merge_gate.py` has "no fetch
  of its own").

canonical: `gates/merge_gate.py:191-206` (`evaluate()`'s new fetch call and its comment), `on-the-record/directive/merge-gates.md`'s issue-#2381 paragraph (this commit's diff)

acceptance (re-run): `python3 -m pytest gates/test_check_runner.py gates/test_merge_gate.py tests/test_verdict_gate.py -q` — result:
```
73 passed in 1.56s
```

- R2b (investigated, not applied): conformance-review's finding assumed
  a `.gitignore` entry for `roles/implementation.json` exists and is
  ineffective because the file is still tracked. Checked directly —
  `git log --all -S "roles/implementation.json" -- .gitignore` returns no
  commit, on any branch, that ever added such a line; the current
  `.gitignore` has no `roles/implementation.json` entry either. The
  premise does not hold against the actual repository state, so no
  `.gitignore`/`git rm --cached` change was made. Independently
  re-verified the file's own status while here: `git diff origin/main --
  roles/implementation.json` is empty (no local drift on this file), and
  `git log --oneline -- roles/implementation.json` shows no commit since
  the issue-2383 fix (`cea0f583`, which stopped tests from writing to the
  real tracked file). Every non-test reference to `implementation.json`
  in the tree (`gates/gates.py`, `gates/ci.py`, `spawn.py` via
  `spawn.ROOT`) only reads it — it is spawn's role-spec config, read at
  role-resolution time, not session-local scratch, exactly the
  classification the pre-existing record already gave it. Gitignoring
  and untracking it would remove it from any fresh checkout that doesn't
  already carry it in its working tree, breaking `spawn.py`'s
  "implementation" role resolution — a functional regression the issue
  does not ask for and the evidence does not support.

canonical: `git log --all -S 'roles/implementation.json' -- .gitignore` (no output — no such entry ever existed); `git diff origin/main -- roles/implementation.json` (no output — no drift)

- R2c (decided: keep the existing per-session-commit design, apply it to
  this session): `.orchestrate-hook-fires/` shard files are not
  drift-by-accident — `hook_fires.py`'s module docstring and
  `docs/specs/generated-paths.md`/`docs/specs/enforcement-boundary.md`
  both document the per-session shard (issue #2348) as an intentionally
  tracked, session-scoped artifact meant to be committed alongside the
  session's own deliverable, replacing the old single shared
  `.orchestrate-hook-fires.log` specifically so that no two sessions'
  commits touch the same path. `git log --diff-filter=A -- ".orchestrate-hook-fires/*.log"`
  confirms this already works as designed: every shard file currently
  tracked was added by the same commit that landed that session's own PR
  (issue-2413, issue-2431, issue-2383-follow-up, this branch's own
  earlier commit, etc.) — this is the "same treatment" already in force,
  not an unfixed writer. The two treatments R2c offered (gitignore the
  directory, or fix the writer) were both rejected: gitignoring it would
  contradict the two spec docs above, which explicitly classify this
  path as in-repo by design (not "out-of-tree" scratch), and would
  discard the audit trail issue #2348 built; rewriting
  `on-the-record/hooks/hook-fires.sh` to special-case branch context
  (e.g. skip writing on `main`) would add per-fire `git`-awareness to a
  script whose own docstring documents it as deliberately zero-overhead,
  operator-frozen pure-bash-plus-coreutils because it fires on every
  `UserPromptSubmit`/`Stop` event fleet-wide — a real design change to a
  frozen constraint, not a CHANGES-round-sized fix. What this round does
  apply: this session's own new shard
  (`.orchestrate-hook-fires/9f5feb13badaeb330dfcc6e1.log`, untracked at
  the start of this round per `git status`) is committed alongside this
  round's code fix, exactly like every prior example above — the
  designed treatment, executed for this session. The residual gap the
  pre-existing record's "Open findings" section already named — an
  orchestrator's own unspawned top-level session (on `main`, no PR to
  bundle a shard into) would still accumulate untracked shards — is
  unchanged by this round and remains open for the reasons already
  stated there; it is a real design decision (how to distinguish
  "orchestrator session" from "role session" at the hook-script level),
  not something resolvable inside this issue's two acceptance lines.

canonical: `git log --diff-filter=A --oneline -- ".orchestrate-hook-fires/*.log"` (each addition co-lands with that session's own PR commit); `hook_fires.py:1-28` and `docs/specs/generated-paths.md:28` (design docs classifying the path as intentionally tracked); `on-the-record/hooks/hook-fires.sh:14-22` (documented zero-overhead, pure-bash constraint)

### CHANGES round 2 (two gaps, both reversing the round above)

Both findings this round are corrections to conclusions the CHANGES round
directly above reached, not new territory:

- R2b (round 2): the very first cut of this branch added
  `.orchestrate-hook-fires.log` to `.gitignore` but never ran
  `git rm --cached` on it, so the ignore entry had been a no-op against
  `origin/main` this entire time — `git ls-tree origin/main --
  .orchestrate-hook-fires.log` still returned the blob. Fixed with
  `git rm --cached .orchestrate-hook-fires.log`; the working-tree file is
  untouched (`git rm --cached` only drops it from the index), so any hook
  still writing to that exact path — none currently do, per the existing
  "## Why" paragraph below — keeps writing to a now-untracked file
  instead of a tracked one.

canonical: `git ls-tree origin/main -- .orchestrate-hook-fires.log` (returned the blob before this round's fix); this round's commit diff (`git rm --cached .orchestrate-hook-fires.log`)

- R2c (round 2): reverses the R2c decision directly above. That decision
  rested on `docs/specs/generated-paths.md`/`docs/specs/enforcement-
  boundary.md` classifying the shard directory as "intentionally
  tracked, committed alongside the session's own PR." A fresh
  architecture consult plus a live grep this round checked that premise
  against the actual reader code instead of the design docs, and it does
  not hold: `hook_fires.py::_hook_fires_aggregate()` (`hook_fires.py:63-
  79`) globs `_hook_fires_dir(cwd)` — the *session workspace* directory,
  per `_hook_fires_dir`'s own docstring (`hook_fires.py:49-56`): "never
  the shared on-the-record checkout." No code anywhere reads a committed
  copy of a shard across sessions; the only two readers in the tree are
  this aggregator (workspace-local) and the writer itself
  (`on-the-record/hooks/hook-fires.sh`, also workspace-local). Every
  session committing its own shard was therefore pure byproduct —
  audit-trail accumulation nobody consumes — and exactly the mechanical
  cause of the local-`main`-vs-`origin/main` divergence tracked in issue
  #2506: ten shards already on `origin/main`, two more added by this
  branch alone before this round. Untracked with
  `git rm --cached -r .orchestrate-hook-fires/` and gitignored (the
  working tree is untouched, so hooks keep writing/reading shards under
  the workspace exactly as before). Also removed the two shard files
  this branch itself had added
  (`.orchestrate-hook-fires/2cfde9a1f735d756b8e80c6b.log`,
  `.orchestrate-hook-fires/9f5feb13badaeb330dfcc6e1.log`) from tracking
  as part of the same directory-wide `git rm --cached -r`.

  Rollout constraint (from the consult): `git rm --cached` doesn't touch
  a live session's open file descriptor, so nothing breaks mid-session.
  But once the ignore lands, the failure mode changes shape depending on
  how a session stages its shard at landing time — checked both:
  `git add <exact-shard-path>` (an explicit, named add) fails loudly —
  git refuses to stage an ignored path and prints "The following paths
  are ignored ... Use -f if you really want to add them" (verified: exit
  1, non-empty stderr) — so a session that tries to hand-commit its own
  shard the way earlier sessions did gets an immediate, visible error,
  not a silent no-op. `git add -A`/`git add .` (a broad add) skips
  ignored paths with no error at all — verified this too, and confirmed
  it is safe here specifically because of the reader finding above:
  nothing in this program ever expected the shard to survive as a commit
  in the first place, so a broad add silently *not* including it drops
  no deliverable and no observability — the same data keeps landing in
  the same workspace file it always did, only the git side stops seeing
  it. This is not the "silent loss of a real deliverable" failure class
  this program exists to catch, because there was never a deliverable
  there — only accidental tracking that this round removes.

canonical: `hook_fires.py:49-56` (`_hook_fires_dir` docstring: "never the shared on-the-record checkout"), `hook_fires.py:63-79` (`_hook_fires_aggregate`, workspace-local glob, no cross-session/committed read path); `git add .orchestrate-hook-fires/<shard>.log` against the post-ignore tree (exit 1, "ignored by one of your .gitignore files" — explicit add refused loudly); `git add -A` against the same tree (exit 0, ignored shard absent from `git status --short` — broad add skips silently, verified safe per the reader finding)

acceptance (round 2): `python3 -m pytest on-the-record/hooks/test_hook_fire_counter.py -q` (unaffected by untracking — the writer/aggregator behavior this test suite covers only ever touches the workspace path, never git) — result:
```
5 passed in 0.81s
```
Also re-verified working-tree preservation directly: after `git rm --cached -r .orchestrate-hook-fires/`, all 12 shard files (10 pre-existing + this branch's 2) are still present on disk (`ls .orchestrate-hook-fires/ | wc -l` → 12), only their git index entries were dropped.

acceptance (round 2, spec-doc sync): `python3 gates/spec_index.py .` — result:
```
통과: 모든 spec 문서가 기록된 해시와 일치한다
```
(neither `docs/specs/generated-paths.md` nor `enforcement-boundary.md` — the
two docs the prior round cited to justify keeping the shard directory
tracked — was touched by this round, so the reconciled-index hash check
has nothing to drift on.)

Before-landing warrant hunt (this round) targeted whether untracking
breaks any git-facing reader or doc-sync gate elsewhere — NO FINDING.
`gates/test_generated_paths.py`/`gates/test_boundary.py` (the gates
cross-checking those same two spec docs) fail identically on `HEAD` and
`HEAD~2` (before this round's two commits), and neither spec doc
asserts git-tracked-ness of the shard directory in the first place.

canonical: `1ba8370b:docs/issue-2381/reports/implementation/2026-08-26-hunt-untrack-orchestrate-hook-fires.md` (full repro and findings)

## Why

The issue's root cause for unresolvable role branches is that
`git fetch origin <one-branch-name>` returns exit 0 even when the
checkout's `remote.origin.fetch` refspec is narrower than that branch
pattern — it silently skips creating/updating
`refs/remotes/origin/<branch>` in that case. That is exactly why
`worktree_for_ref(repo, "origin/issue-<n>/<role>")` died with
"fatal: invalid reference" for branches pushed minutes earlier. Fetching
an explicit full-mirror destination refspec makes ref creation
independent of whatever refspec happens to be configured, and fixing it
once inside `checkout_pr_worktree()` (the shared fetch site both gates
depend on) is the automation the issue's first acceptance line asks for
— no separate orchestrator-side wrapper script was needed since the gate
code itself owns the only fetch call.

canonical: `gates/check_runner.py:394-411` (`fetch_all_role_branches`) and `gates/check_runner.py:415-425` (`checkout_pr_worktree` calling it) in this commit

For the second acceptance line, the two files named in the issue turned
out to already be dead as drift sources, just not yet cleaned out of
`.gitignore`:
- `roles/implementation.json`'s corrupting writer was already
  root-caused and fixed prior to this branch, in commit `cea0f583`
  (issue-2383): three test methods in `tests/test_spawn_gate_wiring.py`
  used to write directly to the real tracked file with a
  save/restore-in-`finally` pattern, and a worker killed mid-test
  (common under `pytest -n auto`) could leave the real file corrupted.
  It now patches `spawn.ROOT` to an isolated tempdir instead. Every
  remaining reference to `implementation.json` in the tree only reads
  it, so it is legitimate tracked config, not scratch state, and is
  correctly left out of `.gitignore`.
- `.orchestrate-hook-fires.log` was the single shared append-only file
  every session's hooks wrote into, which is exactly the
  local-diverges-from-`origin/main` symptom described. Issue #2348
  already replaced the writer (`on-the-record/hooks/hook-fires.sh` /
  `hook_fires.py`) with per-session shards so no two sessions' commits
  touch the same path; nothing writes the flat filename anymore. It was
  gitignored here so it cannot reappear as untracked drift if any stale
  script still targets it.
  [Corrected by CHANGES round 2 above (R2b): gitignoring it here didn't
  actually untrack the file already committed on `origin/main` —
  `git rm --cached` was missing from this cut, so the ignore entry was a
  no-op until round 2 added it.]

canonical: `git log --oneline --all -- tests/test_spawn_gate_wiring.py` → `cea0f583 issue-2383: legacy-remnant audit — gitignore scratch, root-cause implementation.json corruption, age-prune worktrees`; `tests/test_spawn_gate_wiring.py:20-26,219-225,355-389` (tempdir-patched `spawn.ROOT`, already on this branch pre-existing HEAD)

Rejected alternative: writing a standalone fetch-wrapper script invoked
from `spawn.py ps` before delegating to `check_runner.py`/`merge_gate.py`,
as the issue's phrasing suggests. Rejected because both gates already
funnel through one fetch call site inside `check_runner.py`
(`checkout_pr_worktree`), so fixing it there is strictly smaller and
requires no new call-site wiring in `spawn.py`.
[Corrected by the CHANGES round below: the "cannot be bypassed by a
caller that forgets to invoke the wrapper" half of this claim was wrong
— `gates/verdict_gate.py` calls `merge_gate.evaluate()` directly and did
bypass it. The fix for that gap (R1) still didn't need a `spawn.py`
wrapper; it needed `merge_gate.py`'s own shared function to fetch for
itself, which is what landed.]

## What did not work

- The first cut of `fetch_all_role_branches()` used a plain wildcard
  mirror fetch with no `--prune`. The before-landing warrant hunter
  (stance 0) found this silently broke `checkout_pr_worktree()`'s
  fail-closed contract: a branch deleted upstream after an earlier
  fetch left a stale local `origin/<head_ref>` ref resolvable, so the
  gate checked it out with no error instead of failing the way the old
  single-branch fetch did. Fixed in commit `5a41d0d7` by adding
  `--prune` to the fetch call, so a deleted upstream branch prunes its
  stale local ref and the gate fails closed again.

canonical: commit `5a41d0d7`:`docs/issue-2381/reports/implementation/2026-08-26-hunt-orchestrator-fetch-all-branches.md` (repro, fix, and re-verification), `5a41d0d7`:`gates/check_runner.py:410-412` (the `--prune` fix)

- The first cut's "no separate call-site wiring needed" reasoning missed
  that `gates/verdict_gate.py` calls `merge_gate.evaluate()` directly,
  bypassing `check_runner.py`'s fetch entirely — conformance-review
  caught this as R1 (see the CHANGES-round section above). Fixed by
  moving the fetch into `evaluate()` itself, the one function every
  caller shares, instead of relying on caller ordering.

- The R1 fix's first cut made `evaluate()`'s new fetch call unconditional
  and unmocked. The before-landing warrant hunter (this CHANGES round)
  found it broke two pre-existing `gates/test_merge_gate.py` tests'
  documented "no network" invariant: `t_merge_gate_evaluate_refuses_no_checks_as_a_pass`
  and `t_full_sequence_reaches_allow_merge_once_every_precondition_holds`
  both call `merge_gate.evaluate(Path("."), Path("."), ...)` — the real
  developer/CI checkout — and only monkeypatched the three higher-level
  functions `evaluate()` calls, not `check_runner.fetch_all_role_branches`
  itself, because until R1 landed `evaluate()` made no subprocess calls
  before reaching those three. After R1, both tests started performing a
  real, unmocked `git fetch --prune origin +refs/heads/*:refs/remotes/origin/*`
  against this repo's actual GitHub `origin` on every test run — a
  network dependency the test suite's own docstring says it doesn't have,
  and (since the fetch call has no timeout) a hang risk in
  network-restricted CI rather than the fast deterministic failure the
  other synthetic-repo tests get. Fixed by stubbing
  `check_runner.fetch_all_role_branches` in both tests
  (`monkeypatch.setattr(check_runner, "fetch_all_role_branches", lambda
  repo: None)`), the same seam the rest of the suite already uses.

canonical: `docs/issue-2381/reports/implementation/2026-08-26-hunt-orchestrator-fetch-all-branches.md` (repro, fix, and re-verification for this finding — appended under its own "before-landing" stance section), `gates/test_merge_gate.py` (the two `fetch_all_role_branches` stubs, this commit's diff)

acceptance (re-run after fix): `python3 -m pytest gates/test_check_runner.py gates/test_merge_gate.py tests/test_verdict_gate.py -q` — result:
```
73 passed in 1.59s
```

- The first CHANGES round's R2c decision (keep `.orchestrate-hook-fires/`
  tracked, per-session-commit "by design") took the two spec docs'
  classification of the path at face value instead of checking it
  against the actual reader code. It didn't hold: CHANGES round 2's
  architecture consult plus a live grep found no reader anywhere depends
  on a committed shard (`hook_fires.py`'s own aggregator only globs the
  local workspace copy), so the "by design, must stay tracked" premise
  was wrong, and the ten-plus tracked shards it defended were the exact
  mechanical cause of issue #2506's local-`main` divergence. Reversed in
  round 2: see "CHANGES round 2" above.

canonical: `hook_fires.py:49-56,63-79` (`_hook_fires_dir`/`_hook_fires_aggregate`, workspace-local only, no cross-session read path); this round's "CHANGES round 2" R2c bullet (above) for the fix

## Upstream basis

Issue text (`gh issue view 2381`) — no separate survey/proposal file
exists for this record: `CORE_BUILD_NOW=1` was set in this session's
environment by the spawner, invoking the build-now bypass (role protocol
v3 s19a), so the proposal round was skipped and this record is the sole
deliverable document for the fix.

canonical: `gh issue view 2381 --repo tokenmaxxxer/on-the-record` (Ask/Acceptance sections quoted verbatim in the spawning prompt)

## Open findings

None. The item this section previously carried — "an orchestrator's own
unspawned top-level session has no PR to bundle its shard into, so its
shards accumulate as untracked cruft, distinct from a role session's
tracked-and-committed shard" — is resolved by CHANGES round 2's R2c
(above), not merely superseded: with `.orchestrate-hook-fires/`
gitignored, *no* session's shard is ever git-tracked, orchestrator or
role. There is no longer a distinction to draw between the two cases —
both are equally workspace-local, untracked, and read only by
`_hook_fires_aggregate()`'s local glob — so the design question this
finding used to raise ("how to distinguish an orchestrator session from
a role session at the hook-script level") no longer needs an answer to
close this issue's second acceptance line.

derived: `.gitignore`'s `.orchestrate-hook-fires/` entry (this round's
diff) and `git rm --cached -r .orchestrate-hook-fires/` (this round's
commit) — the same treatment now applies to every session's shard
regardless of role/orchestrator status

## Next steps

None — `loop_state: landed`.

## Skill verdicts

skill-verdict: work-in-english — applied: invoked; this CHANGES round's
new code comment (`gates/merge_gate.py`'s `evaluate()`) and test comments
(`gates/test_merge_gate.py`) were written in Korean instead, deliberately
diverging from the skill's English-comment default — matching the
surrounding file's existing, overwhelmingly Korean docstring/comment
convention (per the skill's own "project convention conflicts — follow
the project" edge case), flagged here as the one-sentence conflict note
the skill asks for. Commit message, PR-facing prose, and this record are
in English per the skill's default.

skill-verdict: implementation-complexity-coupling-management — applied: invoked; considered
rule 9 (order a pre-merge check pipeline cheapest-and-narrowest first)
for the R1 fix, since it's about ensuring a prerequisite fetch runs
before a ref-dependent check inside a pre-merge gate pipeline. Concluded
rule 9 doesn't fit as written — the gap wasn't about reordering checks by
cost, it was a missing correctness dependency (a ref-resolving check ran
without its prerequisite having necessarily run first) — so applied the
more directly relevant existing precedent instead (fetch inside the one
shared function every caller of `evaluate()` funnels through, mirroring
`check_runner.py`'s own `checkout_pr_worktree()` fix) rather than forcing
rule 9's shape onto a problem it doesn't describe.

skill-verdict: work-in-english — applied: invoked; this CHANGES round 2's
`.gitignore` comment additions, the deviation-log entry, and this record
are all in English, matching the surrounding `.gitignore`'s existing
English-comment convention (no conflict to flag, unlike the Korean-
convention file touched in the prior round). The user-facing turn summary
is in Korean per the skill's default.

canonical: `.gitignore` (this round's added comment block, English)

other mounted skills this round: not triggered — implementation-design-pattern-selection,
implementation-performance-data-structure-choice, and implementation-blueprint
don't fit a `git rm --cached`/`.gitignore` tracking fix (no GoF pattern,
data-structure, or multi-module structural decision involved);
implementation-complexity-coupling-management (already invoked and
recorded in a prior round, above) wasn't re-invoked since round 2 made
no new check-pipeline-ordering or coupling decision.
