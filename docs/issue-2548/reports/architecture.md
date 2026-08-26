---
issue: 2548
role: architecture
author: architecture
loop_state: landed
upstream:
  - path: gates/gates.py
    sha: cdf80483a583faf29ee343db8ca17a112c61c158
  - path: roster.py
    sha: cdf80483a583faf29ee343db8ca17a112c61c158
  - path: pipeline.py
    sha: cdf80483a583faf29ee343db8ca17a112c61c158
  - path: spawn.py
    sha: cdf80483a583faf29ee343db8ca17a112c61c158
  - path: skills.py
    sha: cdf80483a583faf29ee343db8ca17a112c61c158
  - path: board.py
    sha: cdf80483a583faf29ee343db8ca17a112c61c158
  - path: directive_assembly.py
    sha: cdf80483a583faf29ee343db8ca17a112c61c158
  - path: on-the-record/hooks/record-scaffold.sh
    sha: cdf80483a583faf29ee343db8ca17a112c61c158
  - path: gates/landing_readiness.py
    sha: cdf80483a583faf29ee343db8ca17a112c61c158
  - path: gates/ci.py
    sha: cdf80483a583faf29ee343db8ca17a112c61c158
  - path: on-the-record/hooks/approval-gate.sh
    sha: cdf80483a583faf29ee343db8ca17a112c61c158
  - path: on-the-record/hooks/upstream-defect-scope-guard.sh
    sha: cdf80483a583faf29ee343db8ca17a112c61c158
  - path: on-the-record/hooks/deviation-log-guard.sh
    sha: cdf80483a583faf29ee343db8ca17a112c61c158
  - path: docs/issue-2548/reports/architecture/survey.md
    sha: same-commit
  - path: docs/issue-2548/reports/architecture/scout-brief.md
    sha: same-commit
decision_id: issue-2548-post-role-identity-model
context: >
  Three prior attempts (#2537, #2539 stage 6, PR #2547 off issue-2545)
  each retired one role-coupling point in isolation and were forced into
  a rename because the change collided with a sibling coupling point it
  could not see from inside its own slice. This record designs the
  replacement identity model as one structure instead of a fourth
  collision.
considered_options:
  - alt-A-rename-in-place
  - alt-B-role-to-skill-table
  - alt-C-three-concern-split
outcome: accepted
---

# issue-2548 — architecture record

## What was done

Designed a post-role identity model answering the five questions the
issue asks (Identity, Authorization, Naming, Consumers, Order below),
ordered as independently-landable steps labeled A-H, each checked
against a concrete failure mode. No code was written — this issue's
deliverable is a proposal document; `architecture`'s write scope for
this issue is `docs/decisions/*.md` and this record — canonical:
`spawn_roles.json` key `architecture.write_scope` (read this session) —
and the design fits entirely in this record, so no separate ADR file
was created. Current-state survey and scout brief precede this design
per the survey-order norm: `docs/issue-2548/reports/architecture/
survey.md`, `docs/issue-2548/reports/architecture/scout-brief.md`
(both written this session, before this section).

### Identity

A session's identity is a **slug**: a string chosen at spawn time that
names the work unit, not a value checked against a closed enum. The
same string is used in all three places the issue asks about:

- branch: `issue-<n>/<slug>` (today: `issue-<n>/<role>`, produced by
  `checkout_issue_branch`)
  canonical: `pipeline.py:1122` (read this session)
- record filename: `docs/issue-<n>/reports/<slug>.md` (today:
  `docs/issue-<n>/reports/<role>.md`)
  canonical: `directive_assembly.py:582`,
  `on-the-record/hooks/record-scaffold.sh:45` (read this session)
- roster/lease key: `lease_key(issue, slug)` (today: `lease_key(issue,
  role)`)
  canonical: `roster.py:132` (read this session)

This is not role under another label: nothing downstream will validate
the slug against a fixed set once the ordering below lands. Today it
does — canonical: `pipeline.py:225-227` (read this session):

```python
    data = _sp.role_data()
    if role not in data:
        sys.exit(f"모르는 역할: {role}  (있는 것: {', '.join(sorted(data))})")
```

derived: `python3 -c "import json; print(len(json.load(open('spawn_roles.json'))))"`
→ 44 (executed this session). This rejects any string not present in
that key set.
derived: `python3 -c "import spawn; print(len(spawn.ROLES))"` → 43 — a
second, already-drifted count of the same closed-set concept, in
`spawn.py:703-715`'s separate `ROLES` tuple.

The slug is either supplied explicitly by whoever spawns the session,
or, when omitted, derived from the task text the way skill mounting is
already task-composed — canonical: `pipeline.py:719-720` (`MUSTER_SKILLS`,
read this session), reused here only as a pattern (task-text-derived
naming), not as shared code: slug derivation and skill mounting stay
two independent uses of the task text.

`checkout_issue_branch_for_skill()` already has a two-part branch shape
(`issue-<n>/<skill>-<disambiguator>`) but has zero production callers —
canonical: `pipeline.py:1131-1145` def, `spawn.py:2918` calls
`checkout_issue_branch` instead, `spawn.py:524` is a re-export binding
only, three test call sites in `test/test_branch_naming_dual_scheme.py`
(all read this session; `grep -rln "checkout_issue_branch_for_skill" .`
turns up no other production call site). This design does not reuse the
two-part suffix for a session's primary identity — appending a fresh
disambiguator on every spawn would change the branch/filename on every
retry of the same work unit, breaking documented respawn behavior:
canonical: `directive_assembly.py:582` docstring, "never overwrite an
existing record (a respawn into the same workspace)" (read this
session). Step C below wires the underlying `_checkout_named_branch()`
helper directly with the slug alone, not slug-plus-suffix — canonical:
`pipeline.py:1005` (`_checkout_named_branch`, read this session).

### Authorization

`write_scope` moves from a static, closed-enum lookup
(`spawn_roles.json[role]`) to a value declared at spawn time and stored
on the roster/lease entry, checked fail-closed exactly as today, with
lease expiry now a first-class input to that same fail-closed path.

canonical: `gates/gates.py` (read this session; `grep -c roster
gates/gates.py` → 0) — `role_scope()` has no roster/lease coupling
today. The current authorization path: parse `role` from the branch via
`BRANCH_ROLE` — canonical: `gates/gates.py:866` (read this session):
```python
BRANCH_ROLE = re.compile(r"^issue-[^/]+/([^/]+)$")
```
look it up via `_role_cfg(role)` — canonical: `gates/gates.py:50-53`
(read this session):
```python
def _role_cfg(role: str) -> dict:
    return json.loads(_ROLE_DATA_PATH.read_text(encoding="utf-8"))[role]
```
then fail-closed-check every changed file — canonical:
`gates/gates.py:924-925` (read this session):
```python
return [f"write_scope 이탈: {f} (역할 {role}, 허용: {', '.join(allowed)})"
        for f in files if not any(fnmatch.fnmatch(f, a) for a in allowed)]
```
An unmatched file is a violation — fail-closed by construction. This
design keeps that check unchanged; only `allowed`'s source changes.

New source: `roster.py:132-142`'s lease entry (keyed by
`lease_key(issue, slug)`, already generalized to accept any
disambiguator string per its own docstring — canonical: `roster.py:132-142`
(read this session); the only non-test production callers today,
`spawn.py:3371`, `roster.py:504`, `roster.py:510`, all still supply a
role string as that argument) gains a `write_scope` field, populated
once at spawn time by `spawn.py` from an explicit declaration (a new
CLI value the spawner supplies, or, for a legacy-named slug, a default
copied from `spawn_roles.json[role].write_scope`). `gates.py`'s
`role_scope()` looks up that roster entry via the same
`lease_key(issue, slug)` string the spawn side wrote.

Lease expiry becomes load-bearing here for the first time. Today,
`roster.py:404`'s `lease_reconcile_sweep()` only checks
`lease_expires_at` once the session's own PID is no longer live, and its
only effect is requeueing the claimed board item — it never touches
`write_scope`. canonical: `roster.py:404-406` (read this session):
```python
if not alive:
    if expires_at is not None and now > expires_at:
        _lease_requeue(key, e, now)
```
A zombie session with an expired lease is not blocked by
`gates.py:role_scope()` today, since that function never reads roster
state at all. The new design closes this: when the roster lookup finds
an expired `lease_expires_at`, it is treated exactly like a role config
with no `write_scope` key, reusing this existing branch — canonical:
`gates/gates.py:915-916` (read this session):
```python
    if "write_scope" not in role_cfg:
        return [f"write_scope 선언이 없다 (fail closed): {branch}"]
```
— an expired lease returns this same message, so every file on that
branch is refused. `gates.py` gaining a `roster.py` dependency it does
not have today is a deliberate new coupling, introduced in Step B below
rather than bundled with Step A, because it changes observable behavior
(loud refusal on expiry) where Step A alone does not.

Note on the override file the issue references: `gates.py:889-891` also
parses a role-keyed override from a board-repo path, referenced in its
own docstring as `docs/specs/write_scope.md` (untracked in this repo —
canonical: `git ls-files | grep -i write_scope.md` returns nothing,
read this session; the file is an optional runtime override
`gates.py:885` reads if present, not a committed path). This override
source is independent of `spawn_roles.json` and is retired alongside it
in Step D, since it is keyed the same way.

### Naming

Record filename and branch name use the identical slug string — they do
not differ. Every consumer that derives one from the other already
assumes they are the same string — canonical: `gates/gates.py` lines 61
and 301 (`RECORD_PATH`, duplicated definition, same pattern), `gates/
ci.py:75,90-93,427` (`_ISSUE_ROLE_BRANCH`), `board.py:863`
(`ownership_report`) — all read this session. Keeping filename and
branch equal means none of these regex consumers need a second
derivation rule.

This is also a concrete illustration of why PR #2547 failed
structurally. canonical: `gh pr diff 2547` output, `gates/gates.py` hunk
(read this session):
```python
 def _always_writable(role: str) -> list[str]:
+    # 이슈 #2545: 새 레코드는 `reports/{role}.md`가 아니라
+    # `reports/{role}-{lease-disambiguator}.md`에 쓰인다
     return [f"docs/issue-*/reports/{role}.md",
+            f"docs/issue-*/reports/{role}-*.md",
             f"docs/issue-*/reports/{role}/**",
```
canonical: `gh pr view 2547 --repo tokenmaxxxer/on-the-record`, state:
CLOSED (read this session) — the PR added a second filename glob while
leaving `BRANCH_ROLE`, `_role_cfg`, and every filename-from-branch
consumer keyed on the plain `role` string: two names for one identity,
one of which (`role`) still had to satisfy the closed-enum authorization
lookup. This design avoids that by making the Identity slug the single
string used for both naming and authorization's lookup key — no second,
narrower "role" string survives beside it.

### Consumers

**(a) Core's role-value-dependent hooks.** The issue's count of "8
value-keyed hooks" needs a correction. canonical: `grep -rl CLAUDE_ROLE
on-the-record/hooks/` (read this session) → 8 files mention the
variable, but only 3 branch on its value — canonical:
`on-the-record/hooks/session-role-bind.sh:18-21` (read this session)
names the same 3 explicitly: "approval-gate.sh,
upstream-defect-scope-guard.sh and deviation-log-guard.sh need the
actual role value ... and keep reading CLAUDE_ROLE directly." This
matches issue #2538's own classification — canonical: `git log --grep
2538` → commit `07b7ad8d` (read this session) — and still holds.
Disposition of the 3:
- `approval-gate.sh:92,128-152` cross-checks `CLAUDE_ROLE` against the
  branch-parsed identity — unaffected in shape once `spawn.py` exports
  `CLAUDE_ROLE=<slug>` (Step F) instead of the legacy role name; the
  comparison only needs both sides to agree on one string, guaranteed
  by the Identity/Naming sections above.
- `upstream-defect-scope-guard.sh:59,81,97` compares `role ==
  "upstream-defect-report"` — one reserved sentinel slug, not a table.
  Unaffected; the string simply stays reserved as a slug an ordinary
  spawn must not choose.
- `deviation-log-guard.sh:146-149` builds
  `docs/issue-<n>/reports/<role>/deviation-log` from the role string —
  pure naming, inherits the slug automatically once Step C lands.

**(b) Core's two role-keyed config files.** `citation-config.json` and
`facet-keyword-config.json` do not exist in this repository. canonical:
`grep -r target_path_regex .` and `find . -iname "*citation-config*" -o
-iname "*facet-keyword-config*"` (read this session) both return
nothing. The only trace is a proposed fold target — canonical:
`docs/reports/keep-role-family-classification.md:68-69` (read this
session) — whose proposed shape is content-regex
(`claim_patterns`/`citation_markers`/`facets[].keyword_regex`), not a
path regex keyed on role identity. Nothing to migrate today; when this
fold is eventually built it should not gain a role-keyed
`target_path_regex`, since none exists to inherit. The real current
examples of role-name-in-path coupling are `deviation-log-guard.sh`
(above) and `spawn_roles.json`'s per-role `write_scope` literals —
canonical: `spawn_roles.json` key `architecture.write_scope` = `["docs/
decisions/*.md", "docs/issue-<n>/reports/architecture.md"]` (read this
session) — both retired by Steps B-D.

**(c) `skills.py`'s `_ROLE_SKILLS` and `resolve_role_source()`.** These
do not need to change and were never part of this coupling chain — they
never authorized a write, named a branch, or named a record. canonical:
`grep -n "\.resolve_role_source(" .` (whole repo, read this session) →
exactly 2 live callers, both in `consult.py`
(`_composed_consult_skill_source`, `_readonly_plugin_dirs`), neither on
the spawn-a-session path. `pipeline.py`'s own preflight, which
`skills.py`'s docstring still claims as a consumer, in fact calls
`resolve_static_policy_source()` instead — canonical: `pipeline.py:1663`
and comment `pipeline.py:1652-1662` (read this session, migrated per
issue #2507 / PR #2532) — a second staleness this design corrects rather
than repeats: `skills.py`'s own comment is out of date. `consult.py`'s
use of `_ROLE_SKILLS` is a content selector ("what would the
architecture-flavored advisor say"), a fixed catalog of personas that
stays legitimately fixed — retiring session identity does not imply
retiring a fixed catalog of advisory personas.

The issue's stated role-to-skill cardinality figure also needs a
correction — derived, executed this session:
```
$ python3 -c "
import json
d = json.load(open('spawn_roles.json'))
print('spawn_roles.json keys:', len(d))
import importlib.util
spec = importlib.util.spec_from_file_location('skills', 'skills.py')
skills = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skills)
rs = skills._ROLE_SKILLS
print('_ROLE_SKILLS keys:', len(rs))
multi = [k for k,v in rs.items() if len(v) > 1]
print('multi-skill roles:', len(multi))
print('max list length:', max(len(v) for v in rs.values()))
"
spawn_roles.json keys: 44
_ROLE_SKILLS keys: 43
multi-skill roles: 34
max list length: 10
```
No subset of the size the issue names exists in either file per this
run. The measured max-list-length figure matches the issue's text; the
measured majority-multi-skill figure above is larger than the fraction
the issue's text implied, so the corrected cardinality supports the
issue's own conclusion — no role-to-skill mapping table belongs in the
identity model — at least as strongly as the original claim. This also
matches the field pattern this session's scout brief found: ABAC/PBAC
authorization sourced from declared attributes, not a role-to-resource
lookup table (`docs/issue-2548/reports/architecture/scout-brief.md`,
"Adopt / skip" section, this session).

**(d) Board's per-issue role enumeration.** `board.py:788-790` (inside
`status()`) and `board.py:744-745` (inside `board()`) both iterate
`spawn.py:703-715`'s hardcoded `ROLES` tuple to decide which record
files are "missing" — canonical: both cited lines read this session.
New form (Step E): this enumeration iterates the roster's currently-open
lease slugs for that issue instead of the closed tuple, so "no record
yet" means "a claimed slug with no matching
`docs/issue-<n>/reports/<slug>.md`," not "one of a fixed name list with
no file." It is a pure reader of roster state and gates nothing.

**(e) The spawn entry point.** `spawn.py <role> "<task>"`'s CLI surface
does not change — canonical: `spawn.py:1569-1571` (read this session),
`ap.add_argument("role", nargs="?", ...)` carries no `choices=`
restriction; the positional argument already accepts an arbitrary
string syntactically (`grep -n "choices=" spawn.py` finds no hit tied to
this argument, read this session). The closed-enum enforcement that
makes an arbitrary slug fail today lives one call deeper, in
`role_settings()` — a closed-enum enforcement point this session found
during verification, not named in the issue's own consumer list:
canonical: `pipeline.py:225-227`, quoted under Identity above (read this
session), imported at `spawn.py:537`, called at `spawn.py:2051` and
`spawn.py:3246`. Its new form is folded into Step C: it stops requiring
`role in spawn_roles.json` for the spawn-a-work-session path, falling
back to a generic settings baseline (global plugin block stays
unconditional; sandbox is already forced off centrally regardless of
role — canonical: `docs/decisions/2026-08-11-remove-role-session-
sandbox.md`, "Decision" section (read this session), "`role_settings()`
now forces `sandbox.enabled = False` centrally" — so there is no
sandbox regression here) when the slug is not a legacy role name.
`consult.py`'s advisory paths (item c) keep calling `role_settings()`
with a real role name from the fixed catalog, so they are unaffected.

### Order

Per the issue's fail-closed correction, a good intermediate state after
any step is either a genuine no-op or a loud, identifiable refusal —
never a silent misroute like PR #2547's dual-filename state.

**Step A — roster schema gains `write_scope`; `spawn.py` populates it
at spawn time**, bootstrapped from `spawn_roles.json[role].write_scope`
for legacy-named slugs. No reader yet.
What breaks if the migration stops here: nothing. canonical: `gates/
gates.py` has no roster import (read this session) — `role_scope()`
never reads this field, so this step is fully inert. Safe halt point.

**Step B — `gates.py:role_scope()` reads `write_scope` from the roster
entry first**, via `lease_key(issue, role)` (branch shape unchanged
yet), falling back to `spawn_roles.json` only on a roster miss; an
expired lease is treated as "no `write_scope` declared."
What breaks if Step B lands without Step A already live: every roster
lookup misses (no entry has ever been populated), so every commit on
every branch hits the fail-closed message quoted under Authorization
(`gates/gates.py:915-916`) — a repo-wide write freeze. This is why Step
A must precede Step B.

**Step C — wire the slug into spawn, branch, and settings resolution
together, as one change:** `role_settings()` (`pipeline.py:225-227`)
stops hard-exiting on an unrecognized slug, falling back to the
Consumers-item-e baseline; `spawn.py:2918` calls
`_checkout_named_branch(cwd, f"issue-{issue}/{slug}")`
(`pipeline.py:1005`) instead of the role-only `checkout_issue_branch`;
`gates.py`'s `BRANCH_ROLE` and `ci.py`'s `_ISSUE_ROLE_BRANCH` regexes
keep their existing pattern (`^issue-[^/]+/([^/]+)$`) since the slug
occupies the same single path segment a role name did.
What breaks if the branch/regex half of Step C lands without the
`role_settings()` half: any spawn attempt with a non-legacy slug still
exits at `pipeline.py:226-227`'s `sys.exit` before a branch is ever
created — a loud block on all new-shape work, so both halves must ship
together.
What breaks if Step C lands without Step B already live: PR #2547's
exact failure, reproduced — a branch/filename that no longer matches
`BRANCH_ROLE`'s old capture semantics reaches `_role_cfg()`'s `KeyError`
catch and is refused as unreadable role config — canonical:
`gates/gates.py:910-914` (read this session):
```python
    except (OSError, json.JSONDecodeError, KeyError):
```
every file on that branch blocked. Step B must already read from the
roster (which no longer requires the captured string to be a
`spawn_roles.json` key) before Step C changes what gets captured.

**Step D — remove `spawn_roles.json` as `role_scope()`'s fallback
source; `write_scope` always comes from the roster.**
What breaks if Step D lands before every live spawn path already writes
the roster field (i.e. before Step C is fully rolled out): a session on
an old code path has no roster `write_scope` and no fallback, hitting
the same fail-closed message quoted under Authorization on its first
commit — loud, not silent, and the deliberate final tightening the
fail-closed correction asks for.

**Step E — `board.py:788-790` and `board.py:744-745` stop iterating the
`ROLES` tuple and iterate the roster's live lease slugs for the issue
instead.**
What breaks if Step E lands before Step A: nothing — leases predate this
design (canonical: `roster.py:132`'s docstring cites issue #2241, read
this session), so per-issue roster entries already exist independent of
the `write_scope` field Step A adds; Step E only needs an entry to exist
per open slug, not the field. Safe to land any time at or after Step A;
does not depend on Steps B-D since it never gates a write.

**Step F — `spawn.py` exports `CLAUDE_ROLE=<slug>` instead of the
legacy role name.**
What breaks if Step F lands before Step C: nothing — branches are still
role-shaped, so `CLAUDE_ROLE` and the branch-parsed value are still the
same role name; no-op. What Step F is for: once Step C lands, keeping
the env var's name (`CLAUDE_ROLE`) is cosmetic debt, not a breakage —
`approval-gate.sh:128-152`'s comparison keeps working unchanged as long
as both sides read the same slug, which Step C already guarantees for
the branch side.

**Step G — delete the now-dead `checkout_issue_branch`
(`pipeline.py:1122`) and collapse the duplicate `RECORD_PATH` regex
definition (`gates/gates.py:61` and `:301`, same pattern defined twice)
into one.**
What breaks if Step G lands before Step C: `spawn.py:2918` still calls
`checkout_issue_branch` — deleting it breaks every spawn immediately
(`AttributeError` at the call site). Must be strictly last among the
naming/branch steps.

**Step H — retire `spawn_roles.json`'s closed table itself** (or narrow
it to only the fields `consult.py`'s advisory paths still read; the
`sandbox`/legacy `env` fields are already dead per the sandbox-removal
ADR cited under Consumers item e).
What breaks if Step H lands before Step C/D: `role_settings()` (still
called by `consult.py`'s advisory paths, Consumers item c) and
`role_scope()`'s fallback (Step B/D) both still expect the file to exist
with role keys — deleting it early breaks `consult.py`'s judge/advisory
sessions too, even though they were never part of the identity axis
being retired. Must be last, and must preserve whatever subset
`consult.py` still reads.

## Why

canonical: `docs/decisions/2026-08-25-retire-role-axis-staging.md` and
`docs/decisions/2026-08-21-single-skill-axis.md` (read this session, not
modified) record the staging philosophy this record's ordering builds
on; this record adds the specific sequencing and per-step failure modes
those decisions left open.

Rationale for the three-concern split (identity / authorization /
naming) over the two rejected alternatives:

- **alt-A, rename-in-place** (swap the string `role` for `skill` or
  `slug` everywhere, same one-string-does-everything shape) — rejected.
  This is what PR #2547 did (Naming section above): it changed the
  identity concept's name without separating what the string is used
  for, so authorization kept demanding the old closed-enum shape while
  naming moved to a new one. A repeat attempt at the same shape would
  fail the same way.
- **alt-B, a role-to-skill mapping table** — rejected per the issue's
  own correction and the Consumers-item-c measurement above:
  role-to-skill cardinality is many-to-one in the roles-to-skills
  direction (most roles map to more than one skill), so any table keyed
  by role-or-slug on one side and skill on the other reintroduces a
  closed axis this design retires. Also, `_ROLE_SKILLS`/
  `resolve_role_source()` were never part of the identity/authorization/
  naming chain to begin with — there was nothing to replace with a
  table.
- **alt-C, three-concern split (accepted)** — separates what identifies
  a session (the slug) from what authorizes its writes (a
  roster-declared value, not a lookup table) from what names its
  outputs (the same slug, reused rather than re-derived). This is the
  option under which every consumer above gets a clean, independently
  stated disposition, and whose ordering has genuine per-step failure
  semantics instead of one big-bang cutover. It also matches the field
  pattern this session's scout brief found (identity/authorization
  separation, ABAC/PBAC over closed-enum RBAC) rather than being an
  invented shape — `docs/issue-2548/reports/architecture/
  scout-brief.md`, this session.

## Upstream basis

canonical: issue #2548 body, `gh issue view 2548` (read this session) —
the coupling-chain table, the "must not be reinvented" list
(`roster.py:132`, `pipeline.py:1131`, `pipeline.py:719`), and the two
corrections (`write_scope` fail-closed; role-to-skill cardinality) are
reused verbatim from the issue, not re-derived, per its own instruction.

canonical: `gh pr view 2547 --repo tokenmaxxxer/on-the-record` (state:
CLOSED) and `gh pr diff 2547` (read this session) — verified PR #2547's
actual mechanism rather than relying on the issue text's summary alone.

canonical: `docs/issue-2548/reports/architecture/survey.md` (this
session) — the current-state survey this design was drafted from.

canonical: `docs/issue-2548/reports/architecture/scout-brief.md` (this
session) — the field-pattern check for the three-concern split.

derived: five parallel verification passes this session re-checked
every file:line citation in the issue against current code
(`gates/gates.py`; the record writer/reader chain; `roster.py`/
`pipeline.py`; core hooks plus the two named config files; `skills.py`/
`board.py`/`spawn.py`) and surfaced three corrections beyond the issue's
own two: `gates.py`'s `BRANCH_ROLE` had drifted line numbers (844 in the
issue text, 866 in current code); the role-to-skill cardinality figure
did not match current `_ROLE_SKILLS` data (measured above); and
`pipeline.py:225-227`'s `role_settings()` sys.exit is a closed-enum
enforcement point the issue's own consumer list did not name.

## Open findings

- `spawn_roles.json` and `spawn.py:703-715`'s `ROLES` tuple have
  already drifted apart. derived: the codefence above (Consumers item c)
  measured `spawn_roles.json` and `_ROLE_SKILLS` at different key counts
  in the same run — `_ROLE_SKILLS` and `ROLES` were not diffed directly
  this session, so which exact key is extra is unresolved. Resolution
  path: `implementation` role's first commit for Step H diffs the two
  key sets before deleting anything.
- `skills.py:289-291,368-374`'s docstring claim that `pipeline.py`'s
  preflight still consumes `resolve_role_source()` is stale (Consumers
  item c) — a one-line doc fix, unrelated to this issue's write scope.
  Resolution path: drive-by fix in any future session touching
  `skills.py`.
- `MUSTER_SKILLS` (`pipeline.py:719-720`) has no in-repo reader — it is
  consumed by the spawned Claude process itself, outside this
  repository. Not a gap in this design (identity does not route through
  it), noted only because the issue's "must not be reinvented" list
  cites it as existing infrastructure. Resolution path: none needed.

## Next steps

Hand off to an `implementation` role session, one branch per contract
v3 (`issue-2548/implementation`, opened after this proposal is approved
under the standard two-phase flow — this session used the build-now
bypass for the design deliverable only; the Order section's sequence
still recommends landing Steps A-H as separate PRs, each independently
revertable, per the issue's "order should fall out of the design" ask).
Scope per step: Step A touches `roster.py` + `spawn.py`; Step B touches
`gates/gates.py` only; Step C touches `pipeline.py`, `spawn.py`,
`gates/gates.py`, `gates/ci.py`; Step D touches `gates/gates.py` only;
Step E touches `board.py` only; Step F touches `spawn.py` only; Step G
touches `pipeline.py` + `gates/gates.py`; Step H touches
`spawn_roles.json` + `pipeline.py`. `loop_state: landed` — no further
work in this role for this issue.

## What did not work

None — see Open findings for known drift not addressed in this record's
write scope.

skill-verdict: fmea — not-applicable: this issue asks for a coupling-
chain design with per-step failure-mode citations, which the Order
section above already delivers directly against real gates/code paths;
a generic FMEA severity/occurrence/detection sweep over the same steps
would duplicate that analysis without adding a citation the acceptance
criteria require.
skill-verdict: work-in-english — applied: invoked; this entire record,
its section headers, and all citations were authored in English per the
skill's standing trigger for Korean-language task instructions in this
session.
