# Survey: post-PR hunt/record write vs. gate expectations (issue #705)

## Scope

Three sources instruct an implementation-role session's post-PR hunt/record
write. All three live outside this repo's write set (deployed plugins), so
this survey documents them as read-only findings; issue #705's fix targets
authoring-time guidance across repos, but this phase-1 proposal's own write
set stays inside `docs/issue-705/**` per warrant.

Sources read (session-installed copies, canonical repo per plugin.json):

1. `warrant` plugin — `hooks/directive.sh`
   (`~/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/warrant/hooks/directive.sh`)
2. `coding` plugin (= role `implementation`) — `hooks/directive.sh`
   (`.../tokenmaxxxer-implementation/coding/hooks/directive.sh`)
3. `record-shape` plugin — `hooks/directive.sh` + `hooks/record-shape-gate.sh`
   (`.../tokenmaxxxer-implementation/record-shape/`)

Gates checked against (this repo, `on-the-record`):

- `gates/gates.py` function `role_scope` / `_always_writable` — the actual
  in-scope glob per role: `docs/issue-*/reports/{role}.md` and
  `docs/issue-*/reports/{role}/**` (line ~826). This is board-gate's
  logic; `role_scope` derives `role` structurally from the branch name
  `issue-<n>/<role>`.
- `gates/record_lint.py` functions `bare_count_claim_check`,
  `unverifiable_reason_check`, `checked_claim_reason_check` — the
  record-claim-guard checks, run both as a `PreToolUse` mirror
  (`on-the-record/hooks/record-claim-guard.sh`) and in CI
  (`gates/ci.py`).
- record-fields-gate (per `record-shape/hooks/record-shape-gate.sh` +
  contract v3 §2/§20) — non-terminal `loop_state` requires `next steps`
  and a `resolution path` line when open findings exist.

## Finding 1 — warrant's hunt-record path is out of role scope

`warrant/hooks/directive.sh` line 78 (the literal text every role session
receives at dispatch time) tells the session its hunt record goes to
`docs/issue-<n>/reports/hunt-<proposal-slug>.md` when the proposal path
carries an issue segment, or `docs/reports/<date>-hunt-<proposal-slug>.md`
unchanged when it does not.

Neither branch matches the in-scope globs `role_scope` enforces. The
issue-scoped branch is missing the role segment entirely: it names a bare
file directly under `reports/`, which is a foreign-role path under
board-gate — nothing distinguishes it as the hunting role's own record.
`role_scope` only ever allows `reports/{role}.md` or `reports/{role}/**`;
a hunt record must live at `docs/issue-<n>/reports/<role>/hunt-<slug>.md`.

This already went through one partial fix. An older cached copy of this
same file (found under a `tokenmaxxxer-core-canon-cache` scratch path)
still says unconditionally `docs/reports/<date>-hunt-<proposal-slug>.md` —
no issue segment at all. The fix that landed on top of it added the issue
segment but never added the role segment, so it still collides with
board-gate. `warrant/agents/warrant-hunter.md` and `warrant/README.md`
carry the same stale/wrong path text and need the same correction.

`warrant`'s directive has no notion of "current role" today — it is
role-agnostic by design (used by every plugin, not just `coding`). The
role is only knowable from the branch name (`issue-<n>/<role>`), which
`gates.py` already parses structurally via its `BRANCH_ROLE` pattern for
`role_scope`. The fix must either (a) have the directive derive the role
the same structural way `role_scope` does, or (b) have each role's own
rulebook (e.g. `coding`) own the concrete hunt-record path and pass it to
warrant, rather than warrant hardcoding a role-blind template.

## Finding 2 — record-claim-guard: no derived-claim template in authoring guidance

`coding/hooks/directive.sh`'s `HAND_OFF` block sets the record path,
frontmatter fields, and `loop_state` vocabulary, but supplies no template
line for how to phrase a count claim (for example, a "closed N of M
findings" style line) safely. `record_lint.py`'s bare-count check requires
either a code-fenced reproduction or a `derived: <command or path>` tag
immediately before the number; `coding`'s directive never mentions the
`derived:` tag at all, so a session writing an unbacked count by habit
trips the gate with no warning that the phrasing needs backing.

Similarly the guard's other two checks require any `unverifiable:` line,
or a `checked: ... result: unverifiable` line, to carry a reason; neither
`coding` nor `record-shape` directive states this requirement or shows the
required shape.

## Finding 3 — record-fields-gate: non-terminal shape not templated

`coding/hooks/directive.sh` states the `loop_state` vocabulary and that
`landed` is terminal, but the directive text carries no line reminding the
session that a *non-terminal* state (`coding`, `committing`, etc.) must
carry `next steps` and a `resolution path` for any open finding (contract
v3 §20, mirrored by `record-shape-gate.sh`). Sessions that stop
mid-build (a scope-exceeded stop, or simply running out of turn budget
with an open finding) have no template line to reach for and regularly
land at `commit-unreachable`/`coding` with the required fields missing.

## Alternative considered during survey

`gates.py`'s `role_scope` is already the single source of truth for "what
path is in-scope for role X." The warrant directive's hunt-path template
could either (a) hardcode the corrected path pattern as a second copy of
the same rule, or (b) have warrant's directive derive the record
*directory* — `docs/issue-<n>/reports/<role>/` — from the role name the
same structural way `role_scope` does, rather than deriving it from the
record *file* path each rulebook declares (that file and the hunt-record
directory are siblings, not parent/child; appending onto the file path
produces a broken directory named literally `<role>.md`). (b) avoids a
second hardcoded copy of
the role-scope rule — the drift class this whole issue is about — at the
cost of coupling warrant's directive text to a value the calling role's
rulebook must supply. This is the concrete "why this, not that" input for
the proposal's Rationale section.
