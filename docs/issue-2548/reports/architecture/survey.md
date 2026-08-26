# issue-2548 — architecture current-state survey

Current-state survey, written before drafting the design in
`docs/issue-2548/reports/architecture.md`, per the survey-order norm.
Write surface actually touched by this issue: none (proposal-only); the
surfaces this survey maps are the future implementation's write set.

## Coupling chain, re-verified against current code this session

canonical: five parallel read-only investigations this session
re-checked every file:line the issue body cites, against the working
tree at `cdf80483a583faf29ee343db8ca17a112c61c158`. Findings (full
quoted snippets in `architecture.md`):

- `gates/gates.py`: `_role_cfg(role)` (lines 50-53) is the single
  `spawn_roles.json` loader; `BRANCH_ROLE` (line 866, drifted from the
  issue's cited 844) parses role from the branch; `RECORD_PATH` is
  defined twice (lines 61 and 301); `_always_writable(role)` (line 873)
  builds role-keyed record/proposal/decision globs; a second,
  independent role-keyed override source lives at
  `docs/specs/write_scope.md` (untracked in this repo — canonical:
  `git ls-files | grep -i write_scope.md` returns nothing, read this
  session — read via `gates.py:885` only if present).
  canonical: `gates/gates.py:894-925` (read this session) — `write_scope`
  is fail-closed at every layer: branch mismatch, unreadable config,
  missing key, and unmatched file all return a violation string, never
  an empty/silent pass-through.
- Record writer/reader chain: `directive_assembly.py:582`,
  `on-the-record/hooks/record-scaffold.sh:45`,
  `gates/landing_readiness.py:72,91`, `gates/ci.py:427`,
  `board.py:863` all take `role` as a parameter or parse it from the
  branch, and use it only to build/read the path
  `docs/issue-<n>/reports/<role>.md`. canonical: `board.py:788-790`
  (read this session) — board's "roles with no record yet" enumeration
  reads `spawn.py:703-715`'s hardcoded `ROLES` tuple, not
  `spawn_roles.json`.
- canonical: `roster.py:132` (read this session) — `lease_key(issue,
  disambiguator)` is already generalized (its own docstring says so
  explicitly) but every non-test production caller
  (`spawn.py:3371`, `roster.py:504`, `roster.py:510`) still supplies a
  role string as the disambiguator argument. canonical:
  `pipeline.py:1131` def, `spawn.py:2918` call site (read this session)
  — `checkout_issue_branch_for_skill()` is defined, unit-tested, and
  re-exported, but the production spawn path calls the role-only
  `checkout_issue_branch` instead; `grep -rln
  "checkout_issue_branch_for_skill" .` finds no other production call
  site. canonical: `pipeline.py:719-720` (read this session) —
  `MUSTER_SKILLS` is published with no in-repo reader.
- canonical: `grep -rl CLAUDE_ROLE on-the-record/hooks/` and
  `on-the-record/hooks/session-role-bind.sh:18-21` (read this session)
  — of the files mentioning `CLAUDE_ROLE`, only `approval-gate.sh`,
  `upstream-defect-scope-guard.sh`, and `deviation-log-guard.sh` branch
  on its value, matching issue #2538's own classification (commit
  `07b7ad8d`), still true. canonical: `grep -r target_path_regex .`
  and `find . -iname "*citation-config*" -o -iname
  "*facet-keyword-config*"` (read this session, both empty) —
  `citation-config.json` and `facet-keyword-config.json` do not exist
  anywhere in this repo; the only trace is a proposed, unbuilt,
  content-regex (not path-regex) fold target in `docs/reports/
  keep-role-family-classification.md:68-69`.
- canonical: `skills.py:292-343`, `grep -n
  "\.resolve_role_source(" .` (whole repo, read this session) —
  `resolve_role_source()` has exactly two live callers, both in
  `consult.py`, neither on the spawn path; `pipeline.py`'s preflight
  moved to `resolve_static_policy_source()` per issue #2507
  (`pipeline.py:1663`), contradicting `skills.py`'s own docstring.
  canonical: `spawn.py:1569-1571`, `grep -n "choices=" spawn.py`
  (read this session, no hit) — the CLI role argument carries no
  `choices=` restriction; the actual closed-enum enforcement point is
  `pipeline.py:225-227`'s `role_settings()`, not named in the issue's
  consumer list.

## PR #2547 (issue-2545), re-read this session

canonical: `gh pr view 2547 --repo tokenmaxxxer/on-the-record` (state:
CLOSED) and `gh pr diff 2547` (read this session) — the PR added a
second `_always_writable` glob for a `{role}-{lease-disambiguator}.md`
filename while `BRANCH_ROLE`, `_role_cfg`, and the branch-derived
filename logic kept keying off the plain `role` string — a second name
for one identity, one of which still had to satisfy the closed-enum
authorization lookup.

## Gaps this survey narrows for the design

- Whether `checkout_issue_branch_for_skill()`'s two-part branch shape
  is safe to reuse for primary session identity — narrowed: no, its
  disambiguator suffix breaks record-filename stability across retries
  (canonical: `directive_assembly.py:582` docstring, "never overwrite
  an existing record," read this session).
- Whether `gates.py`'s authorization path has any existing coupling to
  `roster.py`/lease state — narrowed: none. derived: `grep -c roster
  gates/gates.py` → 0 (executed this session) — so wiring lease expiry
  into `write_scope` is a new, deliberate coupling, not a rewire of an
  existing one.
- Whether the issue's two named consumer-count corrections hold against
  current code — narrowed: neither holds exactly. derived: `grep -rl
  CLAUDE_ROLE on-the-record/hooks/ | wc -l` → 8 files mention the
  variable, but cross-checked against `session-role-bind.sh:18-21`'s
  own list, only 3 branch on its value (not the issue's implied 8); the
  skill-cardinality figure is checked with its own executed command in
  `architecture.md`'s Consumers section and does not match the issue's
  stated fraction either. See `architecture.md` for the corrected
  figures in full.

## Skip conditions checked

Not skipped: this issue's spec explicitly leaves an open design
decision (the whole point of the issue) and is not a pure bugfix, so
neither survey-order-directive skip condition applies. Scouting also
ran (see `scout-brief.md`), one stage, two parallel angles.
