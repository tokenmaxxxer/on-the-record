---
status: proposed
files:
  - spawn.py
  - gates/flows.py
  - on-the-record/hooks/approval-gate.sh
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/contract-guard.sh
  - test/test_convention_equivalence.py
  - test/test_branch_role_field.py
---

## Request

Issue #1814: the role decoded from branch names today is duplicated
across four independent regex copies (approval-gate.sh, pr-preflight.sh,
contract-guard.sh, gates/flows.py — issue #1792 survey's "Dependency
facts" bullet 4). Introduce an explicit `role:` field carried in
session/PR metadata; all four sites dual-read it (prefer the carrier,
fall back to the existing branch regex when absent), byte-identical
behavior on both paths. Branch naming (`issue-<n>/<role>`) is unchanged;
no site stops accepting it.

## Constraints

- `test/test_convention_equivalence.py` (25 tests after #1803) stays
  green with additions only — no edits to existing golden cases.
- Dual-read: carrier preferred, branch-regex fallback identical to
  today when the carrier is absent (fresh-workspace case).
- Carrier must be readable by all four sites, including the three shell
  hooks, without adding a new hard dependency (e.g. network) to sites
  that work offline today.
- New `test/test_branch_role_field.py` covers carrier write shape,
  per-site read, per-site fallback, and the absence case, including
  live-fire hook invocations (real PreToolUse JSON via stdin) for the
  three shell hooks.
- Non-goals (explicit in the issue): APPROVE grammar, approval-gate's
  needle match, rsb, branch naming changes, dropping any regex.

## Rationale

Three carriers were on the table (survey.md): the co-injected directive
file, a workspace sidecar record, and a PR body trailer.

The **co-injected directive file** was rejected: it is
`UserPromptSubmit`-hook machinery that injects text into a *live
session's* model context (spawn.py:2475 comment on `directive.sh`
firing every turn). The three shell hooks run as `PreToolUse`/CI-adjacent
processes with no guaranteed live session to read from at hook-fire
time — this carrier is not a data record at all, so "reading" it from a
hook has no defined meaning.

A **pure PR-body-trailer** design was rejected as the sole carrier: two
of the three shell hooks (`pr-preflight.sh`, `contract-guard.sh`) can
fire before a PR exists or while `pr-preflight.sh` is itself validating
the *candidate* body being submitted (pr-preflight.sh:18ff.) — there is
no committed PR body to read yet at exactly the moment those hooks need
the answer. Requiring every hook invocation to shell out to `gh pr
view`/`gh pr list` also adds a network/auth/rate-limit failure mode to
three call sites that resolve role from local `git` alone today
(survey.md "Candidate carriers" B).

The chosen design is **not a single carrier but a per-site pairing**,
because the survey's open finding shows the four sites do not share one
reachable medium:

- **Workspace sidecar** (`.on-the-record/role.json`, written by
  `spawn.py` at spawn time into the workspace it creates) is the
  primary carrier for the three shell hooks
  (`approval-gate.sh`/`pr-preflight.sh`/`contract-guard.sh`). All three
  already resolve the workspace root via a local `git rev-parse` call
  in the same function they use today; `.on-the-record/` already exists
  there holding `auto-approval-state.json`/`test-tiers.json`
  (survey.md, `ls -la .on-the-record/`), so this is the established
  convention for hook-readable session-local state, not a new
  dependency class. No network call, no live-session dependency.
- **PR body trailer** is the carrier for `gates/flows.py`, because
  flows.py's role-decode call site (`gates/flows.py:319`) reads only
  the remote `gh pr list` JSON row with no local checkout evidenced at
  that call site (survey.md open finding) — the workspace sidecar is
  simply unreachable from that process. flows.py already fetches `body`
  in the same `gh pr list` call that yields `headRefName`
  (`gates/flows.py:57`), so reading a `role:` trailer out of that
  already-fetched body costs no new API call.

Both carriers are written by `spawn.py` at the same point (spawn time):
the sidecar file directly, and the trailer line appended to the PR body
template `spawn.py` already produces for the PR-creation flow. This
keeps the write side single-sourced even though the read side is
per-site, and matches each site's actual reachable medium instead of
forcing one medium onto a site that cannot reach it.

Rejected alternative: forcing all four sites to read the PR body
trailer exclusively (single carrier, simplest mental model) — rejected
because it breaks dual-read's "identical behavior" requirement for the
two shell hooks that can run before a PR body exists; those hooks would
have no live carrier to prefer and would silently always fall back,
making the "prefer carrier" path dead code for 2 of 4 sites.

## Accumulation

The four sites already carry one duplicated regex each (issue #1792
survey bullet 4); this change adds one duplicated read-helper (sidecar
or trailer lookup + fallback) per site on top of that, not a shared
library call — matching the existing per-site inline-copy shape rather
than introducing a new one. If a 5th/6th consumer of branch role needs
this same dual-read later, N more hand-copied read-helpers is the wrong
direction: that would be the trigger to extract one shared `read_role(cwd,
pr)` function (Python, importable directly by the Python-native sites
and reachable from the bash entry points via a thin wrapper) instead of
continuing to inline-copy the dual-read block. This issue stops at 4
copies — the frozen migration order's named scope — and does not
extract the shared helper preemptively, since 4 is the same count
already tolerated for the branch-regex itself, and issue #1792's own
migration plan treats regex unification as a later phase, not this one.

## What will be done

1. `spawn.py`: at role-session spawn, write `.on-the-record/role.json`
   (`{"role": "<role>", "issue": <n>}`) into the spawned workspace, and
   append a `role: <role>` trailer line to the PR body template used
   when the role's PR is created/updated.
2. `on-the-record/hooks/approval-gate.sh`,
   `on-the-record/hooks/pr-preflight.sh`,
   `on-the-record/hooks/contract-guard.sh`: each gains a helper that
   reads `.on-the-record/role.json` relative to the resolved workspace
   root first; on read failure (absent file, unparseable JSON, missing
   `role` key) falls back to the existing `^issue-(\d+)/([\w-]+)$`
   branch-regex parse, unchanged.
3. `gates/flows.py`: the `_BRANCH_RE.match(pr.get("headRefName") or
   "")` site gains a `role:` trailer read from the already-fetched `pr`
   body first; on absence/no-match falls back to the existing
   `_BRANCH_RE` parse against `headRefName`, unchanged.
4. `test/test_convention_equivalence.py`: additions only — new cases
   asserting carrier-present and carrier-absent paths produce identical
   role output to today's regex-only behavior, for each of the 4 sites.
5. New `test/test_branch_role_field.py`: sidecar/trailer write shape
   from spawn.py, per-site field-read, per-site fallback, and the
   fresh-workspace absence case (byte-identical to today), including
   live-fire hook runs (real PreToolUse JSON via stdin) for the three
   shell hooks.

## Out of scope

APPROVE grammar, approval-gate's needle match, rsb, changing branch
naming, dropping any of the four regexes — all named non-goals in the
issue body, deferred to later sub-issues.

## How you'll know it worked

- `python3 -m pytest test/test_convention_equivalence.py -q` passes,
  and `git diff` over that file shows additions only (no lines removed
  or altered in existing cases).
- `python3 -m pytest test/test_branch_role_field.py -q` passes,
  including live-fire hook invocations for the three shell hooks, and
  the fresh-workspace-no-carrier case asserts byte-identical output to
  today's regex-only behavior for all four sites.
