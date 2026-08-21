---
status: proposed
files:
  - spawn.py
  - test/test_spawn_role_skill_resolution.py
---

## Request

#1758 (skill-axis phase 3/4 mechanism, operator-frozen framing, second
correction): a transitional config file
(docs/specs/role-source-allowlist.json, absent = empty) maps a legacy
role name to a list of skill-repository skill names. A mapped role
mounts those named skills (guidance only — skill-repository never
carries hooks) instead of its rulebook; an unmapped role resolves
byte-identically to today. Fail-closed before any workspace/branch
mutation when a mapped role names a missing skill. Records (roster
entries) carry which source resolved the role — rulebook sha, or
skill-repo sha + skill list.

## Constraints

- Single skill axis, single enforcement surface: enforcement for a
  mapped role comes from core hooks alone; the rulebook mount (which
  carries the rulebook's own hooks) must not be mounted for a mapped
  role — not "mounted but ignored," actually absent from the argv.
- skill-repository is guidance-only, categorically: no hook ever
  attaches there. This is stronger than "the mapping doesn't add
  hooks" — a resolved skill directory that itself contains a hooks/
  subdirectory is a violation of the frozen program principle and must
  refuse, the same way a missing skill must refuse.
- Unmapped roles: byte-identical spawn_cmd() argv/env to pre-#1758 —
  this is a hard acceptance check (mount-layout assertions, case-diffed).
  The mapping resolution must be structurally incapable of touching an
  unmapped role's plugin/skill mount path.
- Transitional only: this mapping is explicitly removed in phase 5. No
  new abstraction beyond what #1742 already established for the
  "--skills" mount mechanism should be introduced — this issue reuses
  that mechanism for a second call site (mapping-driven instead of
  flag-driven), not a parallel one.
- Fail-closed ordering: any refusal (missing skill, or a mapped skill
  carrying hooks/) must happen before issue_workspace()/
  checkout_issue_branch() run, matching the existing --skills fail-closed
  ordering (survey: spawn.py:7817 resolves before spawn.py:7850/7856
  create the workspace/branch).

## Rationale

Chosen approach: add one new inline resolution function in spawn.py,
resolve_role_source(role, root, repo_root), that reads
docs/specs/role-source-allowlist.json and returns which source (rulebook
vs skill-repo) a role resolves from, reusing #1742's resolved_skill_dirs()
for the actual skill-name-to-directory + fail-closed-on-missing-name
work. _spawn_one() then either skips plugin_dirs()/checkout_version()
(mapped role) or calls them as before (unmapped role), and appends
resolution fields to the roster entries unconditionally (both cases,
distinguishing them by value rather than by key presence).

Alternative considered and rejected: mount a mapped role's named skills
additively alongside the rulebook, and rely on convention (skills simply
don't contain hooks/ by policy) to keep the "no hooks ever" invariant.
Rejected because requirement 2 in the issue is explicit that the
rulebook mount itself — not just its hooks — stops for a mapped role
("rulebook hooks are no longer mounted for mapped roles... the mapping
file is therefore the per-rulebook go/no-go switch"); keeping the
rulebook mounted alongside skills would leave the old hooks live and
make the mapping file a no-op for its stated purpose. It would also
leave "no hooks ever" as an unenforced convention with no fail-closed
mechanism, which acceptance 1's "no skill-side hook dirs" mount-layout
assertion needs to be able to check against something concrete.

A second alternative — a standalone module for the allowlist lookup
instead of an inline spawn.py function — was rejected too: #1742's
_skill_repo_root()/resolved_skill_dirs()/skill_repo_sha() already live
inline in spawn.py for the same class of lookup (config -> mount
decision), and this issue is explicitly a mechanical extension of that
same pattern (design-research-skip: mechanical, per the issue body) — a
new module would split one resolution concern across files for no
functional gain.

## What will be done

1. spawn.py: add _role_source_allowlist(root) — reads
   docs/specs/role-source-allowlist.json under root, returns {} if the
   file is absent (empty mapping = every role resolves as today).
2. spawn.py: add resolve_role_source(role, root, repo_root) — looks up
   role in the allowlist; unmapped -> {"source": "rulebook", "skill_dirs":
   [], "skills": [], "skill_sha": None}; mapped -> resolves the named
   skills via the existing resolved_skill_dirs() (which already
   fail-closes on any unresolvable name before returning), then checks
   each resolved skill directory for a hooks/ subdirectory and
   sys.exit()s (non-zero, before any workspace/branch mutation) if one
   is found, then returns {"source": "skill-repo", "skill_dirs": [...],
   "skills": [names...], "skill_sha": <skill_repo_sha of the first dir's
   parent>}.
3. spawn.py: in _spawn_one(), call resolve_role_source() at the same
   point --skills is resolved today (before issue_workspace()/
   checkout_issue_branch()). Use its "source" to decide whether
   plugin_dirs(role, spec) and the checkout_version(role, spec) log call
   run at all (rulebook path, unmapped) or are skipped entirely
   (skill-repo path, mapped) — a mapped role's argv never carries a
   rulebook --plugin-dir entry, and the log line reports the skill-repo
   source instead of fetching a rulebook it doesn't use. Append the
   mapped role's skill_dirs to the plugin-dir mount list passed into
   spawn_cmd() (same --plugin-dir mechanism #1742 already uses for
   --skills), additive to (not replacing) any explicit --skills dirs.
4. spawn.py: add resolution_source (always), plus resolution_skills/
   resolution_skill_sha (mapped) or resolution_rulebook_sha (unmapped)
   to both the early and full roster entries — present for every role,
   distinguishing source by value, contrasting with #1742's
   present-only-when-used skills/skills_sha shape (acceptance 3's
   "unchanged shape" for the unmapped case means these fields are always
   there and just reflect rulebook, not that they're sometimes absent).
5. test/test_spawn_role_skill_resolution.py (new): mount-layout
   assertions (no rulebook plugin dir + no skill-side hooks/ dir for a
   mapped role; byte-identical case-diffed argv/env for an unmapped
   role vs. pre-#1758 behavior); refusal cases (missing named skill,
   and a named skill directory containing hooks/ — both non-zero exit,
   both proven to happen before issue_workspace()/checkout_issue_branch()
   run, following the existing UnknownSkillFailsClosedBeforeWorkspaceTest
   pattern); record-fields case (roster entry shape for both a mapped
   and an unmapped role).

## Accumulation

resolve_role_source() adds exactly one new inline lookup function
alongside spawn.py's existing _skill_repo_root()/resolved_skill_dirs()/
skill_repo_sha() trio (#1742) — it does not add a new per-role branch
that grows with each mapped role; the allowlist file itself is the only
thing that grows as more rulebooks get mapped, and it is a flat
{role: [skill names]} JSON table, not code. If N more roles are mapped
in future phase-4 work, that is N more entries in
docs/specs/role-source-allowlist.json (data, reviewed per-rulebook per
the issue's own "mapping file is the per-rulebook go/no-go switch"
framing) — no additional spawn.py branch, subprocess call, or
conditional is added per mapped role. This mirrors #1742's --skills
CSV, which already scales the same way.

## Out of scope

- The disposition of the ~300 remaining rulebook hooks (fold into
  parameterized core gate families, or demote to skill guidance) — the
  issue states this explicitly belongs to phase 4's own issue.
- Populating docs/specs/role-source-allowlist.json with any real role
  entries — this issue ships the mechanism only; the file stays absent
  (or empty) until a later phase-4 per-rulebook go/no-go decision maps a
  real role.
- Any change to the --skills flag's own behavior (#1742) beyond reusing
  its resolved_skill_dirs()/skill_repo_sha() functions as-is.
- Removing or renaming the mapping mechanism for phase 5 — this issue
  ships it as transitional, not its removal.

## How you'll know it worked

- python3 -m pytest test/test_spawn_role_skill_resolution.py -q passes,
  covering: mount-layout (no rulebook plugin dir + no hooks/ dir mounted
  for a mapped role; byte-identical argv/env for an unmapped role),
  fail-closed refusal (missing skill; skill with hooks/) with non-zero
  exit and no workspace/branch created, and roster record-fields shape
  for both mapped and unmapped roles.
- Manual read-through confirms docs/specs/role-source-allowlist.json
  absence still resolves every role exactly as before (empty-state
  acceptance case).
