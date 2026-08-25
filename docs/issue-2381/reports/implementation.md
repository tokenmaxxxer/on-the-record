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
    sha: same-commit
  - path: on-the-record/directive/merge-gates.md
    sha: same-commit
  - path: .gitignore
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
(`checkout_pr_worktree`), so fixing it there is strictly smaller,
requires no new call-site wiring in `spawn.py`, and cannot be bypassed by
a caller that forgets to invoke the wrapper.

## What did not work

None.

## Upstream basis

Issue text (`gh issue view 2381`) — no separate survey/proposal file
exists for this record: `CORE_BUILD_NOW=1` was set in this session's
environment by the spawner, invoking the build-now bypass (role protocol
v3 s19a), so the proposal round was skipped and this record is the sole
deliverable document for the fix.

canonical: `gh issue view 2381 --repo tokenmaxxxer/on-the-record` (Ask/Acceptance sections quoted verbatim in the spawning prompt)

## Open findings

- The *new* per-session shard directory `.orchestrate-hook-fires/` is
  itself not gitignored, and produced a real untracked shard in this
  very session. By design (per `hook_fires.py`'s own docstring and
  `docs/specs/generated-paths.md`), a spawned role session is expected to
  commit its own shard alongside its own PR — which this record's commit
  does. But an orchestrator's own top-level, unspawned session has no PR
  to bundle its shard into, so its shards would accumulate as untracked
  cruft in the canonical checkout — the same drift class under a new
  path. Left open: distinguishing "orchestrator session" from "role
  session" at the hook-script level is a real design decision (whether
  the orchestrator's own shards should be gitignored, swept, or bundled
  into its own periodic commit), not a minimal fix within this issue's
  two acceptance criteria, and is not something this record's diff
  touches.

derived: `git status` at the time of this record showed `.orchestrate-hook-fires/2cfde9a1f735d756b8e80c6b.log` as untracked in this working copy

## Next steps

None — `loop_state: landed`.
