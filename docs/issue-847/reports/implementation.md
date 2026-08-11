---
code_under_review:
  - harness/driver.py
  - harness/test_driver.py
  - docs/handbooks/northpole-harness.md
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #847 phase 2

## What was done

Wired the #776 steady-state scenario to a faithful GitHub host, per the
approved proposal (candidate 1 + candidate 3's empty-state branch) and
the operator's follow-up provisioning comment on issue #847:

- `harness/driver.py`: added `resolve_harness_github_token()`,
  `resolve_harness_github_host()`, `reset_and_push_fixture_to_github()`,
  and `seed_steady_state_github_host(dest_dir)`. The last is the entry
  point: it resolves `NORTHPOLE_HARNESS_GH_REPO` (default
  `JiwonJung94/northpole-harness-fixture`) and a token from
  `NORTHPOLE_HARNESS_GH_TOKEN` or the ambient `gh auth token`; when both
  resolve, it deletes every non-default branch on the host via `gh api`
  and force-pushes the freshly instantiated fixture's HEAD as the
  default branch (a full reset each run), then wires `origin` to the
  real GitHub remote. When no repo/token resolves, it returns
  `{"available": False, "reason": ...}` and leaves the fixture's git
  state untouched — never raises, never a false PASS.
- `harness/test_driver.py`: 5 new unit tests covering the
  UNMEASURED-when-absent branch (no token + `gh auth token` failing, `gh`
  missing entirely), that an explicit env token skips shelling out
  entirely, the default-repo fallback, and that
  `seed_steady_state_github_host` never touches `origin` when the host is
  unavailable. All network-free (`monkeypatch` on `subprocess.run`).
- `docs/handbooks/northpole-harness.md`: documented both new env vars
  (harness-only, same turn as their introduction per the doc-placement
  ladder) and the `GH_TOKEN`/`GITHUB_TOKEN` export needed for the
  delegated role's own `gh` calls to authenticate against the host.

## Why

Issue #847: the harness's prior `seed_remote_dir` seeds a local bare
`file://` repo, which satisfies `git remote get-url origin` but `gh`
refuses it as "not a known GitHub host" — so the delegated role's
issue/PR/merge cycle can never complete and northpole reqs #1/#4 stay
UNMEASURED. The approved phase-1 proposal
(`docs/issue-847/proposals/2026-08-11-faithful-github-host-for-steady-state-harness.md`)
recommends a real throwaway GitHub repo (candidate 1) with an explicit
UNMEASURED empty-state branch (candidate 3), layered together per the
issue's own acceptance bar. The operator's issue-847 comment narrowed
candidate 1 further: a real PRIVATE repo they provisioned themselves
(`https://github.com/JiwonJung94/northpole-harness-fixture`), reset each
run, via harness-only env vars — this record implements exactly that.

## Basis

Upstream: `docs/issue-847/proposals/2026-08-11-faithful-github-host-for-steady-state-harness.md`,
approved via the issue-847 comment `APPROVE issue-847/implementation`
(preceded by the operator's `OPERATOR CONSENT + HOST PROVISIONED`
comment naming the concrete repo, env-var names, and reset-each-run
requirement) — canonical: `gh issue view 847 --comments`, read this
session.

## What did not work

canonical: `docs/issue-847/reports/implementation/2026-08-11-hunt-phase-2-github-host-guard.md` (hunter finding file, read this session) — a whitespace-only `NORTHPOLE_HARNESS_GH_TOKEN` bypassed `resolve_harness_github_token()`'s truthy-only check (no `.strip()`), so it was accepted as a real token instead of degrading to UNMEASURED-with-reason, diverging from the `gh auth token` fallback path a few lines below which already stripped and null-checked its output. Fixed by adding the same `.strip()` to the env read, with a regression test (`test_resolve_harness_github_host_unmeasured_when_token_is_whitespace`).

## Doc placement

- [x] New env vars (`NORTHPOLE_HARNESS_GH_REPO`, `NORTHPOLE_HARNESS_GH_TOKEN`) documented in `docs/handbooks/northpole-harness.md`, same commit as their introduction in `harness/driver.py`.

## Verification run (live, this session)

Ran the new code path live against the real provisioned fixture repo,
using the ambient `gh auth token` (no `NORTHPOLE_HARNESS_GH_TOKEN` set),
confirming the empty-state test claims and the real-host path both hold.

Unit tests (network-free, includes the UNMEASURED-when-absent branch):
canonical: raw pytest output, run this session.

```
$ python3 -m pytest harness/test_driver.py -q
.........                                                                [100%]
9 passed in 0.12s
```

(9 = 8 written before the hunt's whitespace-token finding, plus 1
regression test added after the fix — see "What did not work" and
"Hunt" below.)

Live run against the real provisioned host (ambient `gh auth token`,
`NORTHPOLE_HARNESS_GH_REPO` unset so it used the default repo):
canonical: raw Python REPL output of `seed_steady_state_github_host`,
run this session (token/URL redacted here, not in the raw run).

```
>>> result = seed_steady_state_github_host(dest)
{'available': True, 'repo': 'JiwonJung94/northpole-harness-fixture',
 'token': '<redacted>', 'remote_url': '<redacted>',
 'pushed_ref': 'main'}
```

canonical: `gh api repos/JiwonJung94/northpole-harness-fixture/branches --jq '.[].name'`,
raw output run this session → `main` only (no stale branches from any
prior run). canonical: `gh api repos/JiwonJung94/northpole-harness-fixture/commits --jq '.[0].commit.message'`,
raw output run this session → `harness fixture initial commit` (the
freshly pushed fixture commit, not any prior run's state) — together
these confirm the reset-each-run requirement held on the real host.

Not run this session: the delegated role's actual issue->PR->merge
cycle against the reset host (issue #847's own execution-plan step 3,
`execution-observation` re-run) — that is a separate role's phase-2
step, not part of this proposal's write set.

## Open findings

None.

## Hunt

Stance (index derived from `.warrant-hunt.count`, before-landing
transition, this repo's warrant-directive rotation): stance 2 — assume
this guard goes silent when its own input is malformed — make it go
silent. Dispatched a background `warrant-hunter` (`sonnet`) against the
diff above, on that stance, waited for and consumed its result in this
same turn (contract v3 s22, headless single-shot).

canonical: `docs/issue-847/reports/implementation/2026-08-11-hunt-phase-2-github-host-guard.md`,
read this session — FINDING (whitespace-only token bypass), fixed above
under "What did not work" and re-cleared by re-running the full test
suite (9 passed) after the fix.

closed_checks:
- whitespace-only `NORTHPOLE_HARNESS_GH_TOKEN` env var no longer bypasses
  the UNMEASURED-with-reason guard — code_sha: pending commit on this
  branch (code_under_review: `harness/driver.py`).
