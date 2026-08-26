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
    sha: 8da6f0094b906b5726f980df85596b727f3d3003
  - path: docs/issue-2381/reports/implementation/2026-08-26-hunt-orchestrator-fetch-all-branches.md
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

## Upstream basis

Issue text (`gh issue view 2381`) — no separate survey/proposal file
exists for this record: `CORE_BUILD_NOW=1` was set in this session's
environment by the spawner, invoking the build-now bypass (role protocol
v3 s19a), so the proposal round was skipped and this record is the sole
deliverable document for the fix.

canonical: `gh issue view 2381 --repo tokenmaxxxer/on-the-record` (Ask/Acceptance sections quoted verbatim in the spawning prompt)

## Open findings

- The *new* per-session shard directory `.orchestrate-hook-fires/` is
  itself not gitignored — by design (per `hook_fires.py`'s own docstring
  and `docs/specs/generated-paths.md`/`docs/specs/enforcement-boundary.md`),
  a spawned role session is expected to commit its own shard alongside
  its own PR. This record's original commit did that for its own shard,
  and the CHANGES round (R2c, above) did it again for the new shard this
  round's session produced. An orchestrator's own top-level, unspawned
  session still has no PR to bundle its shard into, so its shards would
  still accumulate as untracked cruft in the canonical checkout — the
  same drift class under a new path, and the same open item as before
  this round: distinguishing "orchestrator session" from "role session"
  at the hook-script level is a real design decision (whether the
  orchestrator's own shards should be gitignored, swept, or bundled into
  its own periodic commit), not a minimal fix within this issue's two
  acceptance criteria. Confirmed still open — this round evaluated and
  rejected both R2c treatments (blanket-gitignore, and adding
  branch-awareness to the zero-overhead writer) as wrong-sized fixes for
  this issue; a future issue scoped to that specific orchestrator-session
  case is the right place for it, not this one.

derived: `git status` at the time of the original commit showed `.orchestrate-hook-fires/2cfde9a1f735d756b8e80c6b.log` as untracked; at the start of this CHANGES round it showed `.orchestrate-hook-fires/9f5feb13badaeb330dfcc6e1.log` as untracked (both now committed, one per session, matching the by-design pattern)

## Next steps

None — `loop_state: landed`.
