---
kind: current-state-survey
issue: 2241
role: architecture
---

# issue-2241 — current-state survey

Scope surveyed: every coupling point the issue names as "load-bearing for
roles," plus the concrete shape of the three new concepts it proposes
(lease, author identity, record-kind), plus a re-check of the issue's own
"15 PRs open" claim and its "known unverified" list. Read-only research
this session (Explore agent, foreground, consumed this turn); no repo
writes performed during the sweep itself.

## 1. `spawn.py` `ROLES` and the spawn-time claim

`ROLES` — `spawn.py:557-569`, a flat 43-name tuple, the single definition
site. It is barely consumed inside `spawn.py` itself (no `role not in
ROLES` validation there); the real consumers are `board.py:667,691,699`
(board discovery walks the fixed 43-name enum to find
`docs/issue-<n>/reports/<role>.md`) and two test files asserting its
shape.

Branch derivation: `pipeline.py:893-923` `checkout_issue_branch(cwd,
issue, role)` — `br = f"issue-{issue}/{role}"` (`pipeline.py:900`),
justified inline by a comment that board-gate's R4 only allows board
writes from that exact branch.

Two *different* concurrency primitives already exist, not one:
- **`.spawn-claim`** (`roster.py:462-513`, `_acquire_spawn_claim`) — an
  `O_CREAT|O_EXCL` file at `<work>.spawn-claim` holding `{pid, ts}`,
  liveness-checked via `_alive(pid)`. Dies with the process. Keyed 1:1
  on the workspace path, which is derived from `(issue, role)`.
- **A TTL lease** (`roster.py:235-287`, issue #2101) layered on the same
  roster entry: `lease_expires_at` / `lease_progress` /
  `lease_flat_renewals` fields, `LEASE_TTL_MIN` (default 90 min),
  `LEASE_FLAT_RENEWALS_K` (default 3), a detector-free requeue path
  (`_lease_requeue`, `roster.py:268-287`) that fires purely on `now >
  lease_expires_at` — no kill, just "dispatchable again." Roster key:
  `roster_key = f"issue-{issue}/{role}"` (`spawn.py:2784`).

**This survey's load-bearing finding for stage 1**: the lease mechanism
issue #2241 asks to "land" already exists, fully built (TTL, renewal,
flat-progress detection, requeue), keyed on `issue-{issue}/{role}`. The
open design work is not inventing a lease — it's generalizing what the
second half of that key means once role is no longer guaranteed unique
per session.

## 2. `board-gate.sh` R4/R5 — cross-repo location

`board-gate.sh` does **not live in this repo**. It lives in
`tokenmaxxxer/tokenmaxxxer-core`, mounted locally at
`/home/jwjung/tokenmaxxxer-core/core/hooks/board-gate.sh` (849 lines);
the copy actually wired into this session's PreToolUse hooks resolves
through `CLAUDE_PLUGIN_ROOT_CORE=/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core`.
Two prior surveys in this repo already hit this same cross-repo
boundary (`docs/issue-651/reports/implementation/survey.md:16-31`).
**This matters directly for stage 3**: a board-gate rewrite is a PR
against a different repository than this one, with its own review/merge
cycle — not a same-PR edit alongside this repo's other stage work.

R4 (branch) resolves role from `.on-the-record/role.json` sidecar when
present (issue #1827), else `CLAUDE_ROLE`/branch string
(`board-gate.sh:614,723-762`); this repo's live sidecar today is
`{"role": "architecture", "issue": 2241}`.

R5 (foreign-record ownership), `board-gate.sh:821-837`: a role may write
`docs/issue-<n>/reports/<role>.md`, `<role>/**`, and one
`EXTRA_SUBTREE` entry (`{"feasibility": "spikes", "ops": "postmortems"}`,
`board-gate.sh:77`) — everything else under `reports/` for that issue is
refused. `EXTRA_SUBTREE`'s keys (`"feasibility"`, `"ops"`) are **stale**:
`spawn.py`'s current 43-name `ROLES` tuple has no `"ops"` entry (only
`"technical-feasibility"`, not `"feasibility"`) — an orphaned mapping,
already-drifted evidence of exactly the kind of role-string coupling
issue #2241 is retiring.

## 3. `merge_gate.py` / `spawn_on_pr.py` — the observer hardcode

`gates/merge_gate.py:129-144` `required_verification_missing()`
delegates entirely to `gates/spawn_on_pr.py:38`:
```python
PR_TRIGGERED_ROLES = ("execution-observation", "conformance-review")
```
and `applicable_roles()` (`spawn_on_pr.py:66-70`) returns the subset of
that fixed pair missing from `subject_board`. The module docstring
(`spawn_on_pr.py:5-8`) is explicit that this is a deliberate narrowing:
of 10 roles carrying a `use_when.board_condition`, only these two are
mechanically PR-triggerable by presence-check alone; the other 8 need
content classification. `_exempt_own_role` (`merge_gate.py:115-126`)
breaks the circularity where an observer's own PR would otherwise block
on its own missing record. **For stage 5**: this is the single hardcode
point the issue's "rewriting `merge_gate.required_verification_missing()`
from role matching to record-kind presence" targets; it's two role
strings in one tuple, not a diffuse pattern.

## 4. `roles/*.json` / `roles/specs/*.spec.json` — consumers beyond `quality_bar`

The issue's "known unverified: whether `roles/specs/*.spec.json` has
consumers beyond `quality_bar`" is **refuted** — it has at least four:
`gates/need_detector.py` (lines 28 and 34, role→spec map),
`gates/roles_due.py` (lines 7, 40, and 46, reads `use_when.trigger` for
due-ness), `gates/role_spec_shape.py`
(the shape validator itself), and `gates/quality_bar.py:5` (only 21 of
43 spec files even carry a `quality_bar` key). Stage 6's deletion write
set must list all four, not just the one the issue names.

Top-level `roles/*.json` files carry no `quality_bar` key themselves
(that lives only in `roles/specs/*.spec.json`); shape varies per role —
e.g. `roles/conformance-review.json` adds `"judgment_axes"`,
`roles/architecture.json` (this role) sets `"judgment_axes":
["maintenance_complexity"]` and `"write_scope": ["docs/decisions/*.md",
"docs/issue-<n>/reports/architecture.md"]`.

## 5. `consult.py` / `skills.py` — judgment-source resolution, post-#1955

Guidance *content* resolution is unconditional skill-repo already
(`consult.py:470-471,484`; `skills.py:333-355` `resolve_role_source()` —
no allowlist branch remains, per #1955). What still reads role identity:
`consult.py` validates the caller's `role` string against
`roles/<role>.json` file existence at five call sites (e.g.
`consult.py:231-234`), and `_ROLE_SKILLS` (`skills.py:286-330`) is a
hardcoded `{role_name: [skill_name, ...]}` table keyed by the same
43-name legacy strings — the sole remaining place "role" survives as an
identity *key* into skill-set resolution, even though the *source* of
what's resolved is already 100% skill-repo. **This directly explains why
the issue frames stage 2 as "role identity still exposed" rather than
"still needed"**: most of stage 2's stated goal is already landed by
#1955; only the `_ROLE_SKILLS` key and the existence-check remain, and
those are exactly stage 4's (naming) and stage 6's (deletion) targets,
not new work stage 2 itself must do.

## 6. Prior decisions — #1758, #1955, and two frozen principles

- `docs/issue-1758/proposals/role-skill-resolution.md` shipped the
  transitional role→skill allowlist, explicit "removed in phase 5,"
  deferring "disposition of the ~300 remaining rulebook hooks" to its
  own future issue.
- `docs/issue-1955/proposals/retire-role-source-allowlist.md` executed
  that phase-5 removal for the *source*-resolution conditional only;
  its own out-of-scope note says directly: "Any change to which skills
  map to which role, or to skill-repository content itself... this
  issue only removes the now-redundant conditional resolution logic,
  not the skill-repo guidance mapping already in effect for every
  role." That's the exact remaining surface #2241 targets.
- **`docs/decisions/2026-08-21-single-skill-axis.md`** (frozen,
  `id: single-skill-axis`): "There is exactly one capability axis:
  skills... No design may reintroduce a separate role concept... as an
  architectural primitive." Scope globs include `roles/**`; keywords
  include "role concept," "separate role axis." #2241's own program —
  retiring role as a distinct axis entirely rather than preserving it
  under a new name — **reaffirms**, not contradicts, this frozen
  decision (see ADR disposition line).
- **`docs/decisions/2026-08-21-single-enforcement-surface.md`** (frozen,
  `id: single-enforcement-surface`): "Enforcement (hooks) has exactly
  one surface: core." Scope globs include `hooks/**`,
  `on-the-record/hooks/**`. #2241's constraint ("Enforcement stays
  core-only... skills carry guidance, never hooks") **reaffirms** this
  too — the ADR states both dispositions explicitly.

## 7. Open-PR count — issue's "15" is stale

`gh pr list --state open --json number,headRefName,title` returned
**4** open PRs (`2234, 2228, 2221, 2218`, all `issue-<n>/implementation`
branches), not 15. The count will keep moving; stage 4's in-flight-branch
handling should be written to be correct at whatever count exists at
that stage's own build time, not hardcoded against either number.

## 8. Record-kind vocabulary already exists ad hoc

A `kind:` frontmatter key already appears in ~420 files repo-wide, but
inconsistently — common on nested sub-reports (`kind: survey`, `kind:
scout-brief`, `kind: adr`) and occasionally on a top-level record (e.g.
`docs/issue-587/reports/execution-observation.md:3`), but **absent**
from the `docs/issue-2210` and `docs/issue-2215` top-level
implementation/execution-observation/conformance-review records this
survey read for comparison — those use `role:` for that job today.
Stage 1 formalizes `kind:` into a spec'd, always-present field rather
than inventing new vocabulary from nothing.

## 9. `docs/specs/approvers.md`

canonical: `docs/specs/approvers.md`, read this session.
A flat bullet list of two GitHub logins (`JiwonJung94`, `jjongkwann`),
nothing else — the file board-gate's R2 rule reads to confirm board
opt-in, and that also authorizes `APPROVE issue-<n>/<role>` comments.

## 10. No design decision left unopen

This is not a pure bugfix and the issue explicitly leaves multiple
design choices open (lease-key shape post-role, author-identity field
shape, record-kind taxonomy granularity, in-flight-branch handling) —
scouting and a full alternatives-considered ADR both apply; no skip
condition is claimed anywhere in this proposal set.
