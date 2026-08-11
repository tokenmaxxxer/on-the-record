---
status: proposed
files:
  - docs/issue-857/reports/defect-verification.md
---

# Proposal — issue #857 defect-verification, step 1

## Intent

Reproduce and pin exactly where `spawn.py`'s roster/state namespace is
shared between the observing session and a fixture session it launches,
per PR #855 finding 5 (a fixture's `spawn.py watch --issue 776` resolved
to the observing session's own roster entry for issue 776 on a different
repository). No fix — that is issue #857 step 2 (implementation), gated
on this record.

## Constraints

- Cite `gh issue view 857` (which quotes PR #855 finding 5's `ps aux`
  evidence verbatim) as canonical evidence for the collision facts; do
  not re-litigate #855's own findings.
- Pin the exact shared file/key/lookup path in `spawn.py`, not just
  restate the issue's already-known symptom.
- No fix, no test additions — those belong to step 2.

## What will be done

Write
`docs/issue-857/reports/defect-verification/current-state.md` (already
committed alongside this proposal, phase-1 survey home) pinning:

1. `ROSTER` (spawn.py:1757, `ROOT / "runs" / "active.json"`) is a
   single file per `spawn.py` plugin installation — `ROOT`
   (spawn.py:37) is the running script's own directory, not anything
   derived from `-C`/the invoking repo — keyed bare `issue-<n>/<role>`
   (spawn.py:4894, no repo identifier), and `roster_register()`
   (spawn.py:1824-1828) blind-overwrites on a repeat key with no
   collision guard.
2. A partial, repo-scoped mitigation (`WORKSPACE_INDEX`, spawn.py:2487,
   issue #533's `_repo_identity()`/`_workspace_index_put()`,
   spawn.py:3018-3088) exists alongside it, but depends entirely on the
   caller threading a correct `-C`/cwd (spawn.py:3987, default `.`)
   into `_repo_identity()`; the #855 evidence's fixture-session process
   ran with `-C` pointed at the observer's own checkout path rather
   than the fixture's directory, collapsing this layer's
   disambiguation to the same collision.
3. Even where `WORKSPACE_INDEX` does resolve to a correctly
   repo-scoped key, `_watch()` still falls through to the
   repo-unscoped `ROSTER` for pid/offset data (spawn.py:3385-3390,
   with a comment recording this as knowingly out of scope since issue
   #533).

Recommend, without implementing, the isolation seam for step 2: give
each harness-launched fixture session its own `ROSTER`/`WORKSPACE_INDEX`
state dir (e.g. an env var or `-C`-derived per-run state root
`spawn.py` writes to instead of the fixed `ROOT / "runs"`), so a
fixture's roster/watch state is physically a different file from the
observer's own installation-wide state, independent of whether `-C`/cwd
was threaded correctly — closing Finding 2 and Finding 3's shared
`-C`-dependence, not just Finding 1's bare key.

On phase-2 approval, `docs/issue-857/reports/defect-verification.md`
(the role's own contract-mandated record — findings, severity,
`loop_state`) is written per `verify:finding-record` /
`verify:severity-classification`, restating this survey's confirmed
mechanism as a formal finding addressed to `implementation`, with
severity assigned by the deterministic band lookup.

## Out of scope

- Any change to `spawn.py`'s roster/state machinery, `harness/driver.py`,
  or the fixture-session launch mechanism (step 2, implementation role).
- Re-running the #776 harness (execution-observation role).
- Designing the exact isolation seam's shape in code (per-run env var
  vs. `-C`-derived state root vs. issue-number namespacing) — a design
  decision out of this role's scope, for step 2 to decide; this
  proposal names the seam, not its implementation.

## How you'll know it worked

`docs/issue-857/reports/defect-verification/current-state.md` pins the
exact file/key/lookup chain (`ROSTER` spawn.py:1757+1824-1828+4894,
`WORKSPACE_INDEX` spawn.py:2487+3018-3088, the repo-unscoped `ROSTER`
fallback in `_watch()` spawn.py:3385-3390) behind the #855 finding-5
collision, with file:line citations for every claim, and names an
isolation seam (per-run state dir) for step 2 without implementing it.

## Scout

Skip: investigative reproduction/pinning task with no product-facing
design decision open — the issue asks for the shared-namespace code
path to be pinned and an isolation seam recommended, not for a design
direction to be chosen among external products; there is no external
field to scout.

## What did not work

None.
