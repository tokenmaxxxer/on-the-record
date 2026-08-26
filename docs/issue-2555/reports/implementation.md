---
issue: 2555
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: docs/issue-2548/reports/architecture.md
    sha: c0c180e01a22f7ab4d571e00b8677d70bce0b019
  - path: docs/issue-2551/reports/implementation.md
    sha: ea6a064640d4c4a7297b7c5b0236e7fa951ca516
  - path: docs/issue-2553/reports/implementation.md
    sha: f54b00eb13e3e3480ef4cc9214abdaa38444f793
code_under_review:
  - pipeline.py
  - spawn.py
type: feat
breaking: none for existing callers — every legacy `spawn.py <role> "<task>"`
  invocation, its branch/record path, and `--dry-run` JSON output are
  unchanged (verified below, acceptance checks 2 and 4). The only behavior
  change is that a call that used to be REFUSED now succeeds — an
  unrecognized single positional or an unrecognized slug passed explicitly
  used to `sys.exit` at `role_settings()` / exit at "맡길 일이 없다" /
  refuse admission; it now reaches a real dispatch (acceptance checks 1
  and 3 below).
verdict: pass
---

# issue-2555 — implementation record

skill-verdict: work-in-english — applied: invoked; loaded the skill this
session and wrote all new code comments/docstrings, this record, and the
commit/PR text in the mix this repo's existing convention already uses
(Korean inline comments matching the surrounding code, English docstrings
matching newer additions such as `_bootstrap_write_scope`'s, English
commit/PR text matching recent commits — canonical: `git log --oneline -3`
this session showed f54b00eb/ea6a0646 titles are English) — no
project-convention conflict to flag.
skill-verdict: model-routing — not-applicable: this step is a small,
tightly-scoped code change across two files (`pipeline.py`, `spawn.py`)
with a fully-specified design (`docs/issue-2548/reports/architecture.md`,
Step C) to implement directly; there was no sub-task large or independent
enough to warrant delegating to a separate reasoner or executor.

## What was done

Step C of the eight-step role-axis removal — canonical:
`docs/issue-2548/reports/architecture.md`, section `### Order`, Step C
paragraph (read this session) — wired the slug through spawn, branch,
settings, admission, and the CLI's default dispatch, together, as one
change. Five sub-changes, each quoted as the actual diff hunk that landed
it (`derived: git diff -- pipeline.py spawn.py`, executed this session):

**1. `role_settings()` stops hard-exiting on an unrecognized slug**
(`pipeline.py:225-231`):
```python
     data = _sp.role_data()
-    if role not in data:
-        sys.exit(f"모르는 역할: {role}  (있는 것: {', '.join(sorted(data))})")
-    spec = data[role]
+    spec = data.get(role, {})
```
The rest of the function (sandbox forced off centrally, global plugins
disabled, `permissions.allow` topped up, self-hosted-hooks injection) is
unconditional on `spec`'s contents and untouched, so an unrecognized slug
still gets a fully-formed, safe settings baseline (verified in acceptance
check 3 below).

**2. the admission-time `role not in _sp.ROLES` gate is dropped**
(`pipeline.py:1637-1650`, inside `_admission_check_directive_completeness()`):
```python
     role = ctx["role"]
     try:
-        if role not in _sp.ROLES:
-            return False  # role spec is the first directive ingredient
         # Two-phase signal: the contract line must format for this role.
```
Everything this function checks after that line (`_SINGLE_PHASE_CONTRACT_LINE.format(role=role)`,
per-skill trigger-line resolution via `resolved_skill_sources()`/
`resolve_static_policy_source()`) already operates on `role` as a plain
string — canonical: `pipeline.py:1650-1668` (read this session) — none of
it re-derives or re-checks `_sp.ROLES` membership.

**3. `spawn.py`'s own role-indexed spec lookup no longer `KeyError`s**
(`spawn.py:2765/2769`, inside `_spawn_one()`):
```python
-    spec = role_data()[role]
+    spec = role_data().get(role, {})
```
matching the same absent-key-vs-default shape `_bootstrap_write_scope()`
(`spawn.py:56-78`) already uses for the same file.

**4. the branch-checkout call site names the branch directly**
(`spawn.py:2984-2991`, inside `_spawn_one()`):
```python
     with _timed("branch"):
-        br = checkout_issue_branch(cwd, issue, role)
+        br = _checkout_named_branch(cwd, f"issue-{issue}/{role}")
```
`checkout_issue_branch(cwd, issue, role)` was already exactly
`_sp._checkout_named_branch(cwd, f"issue-{issue}/{role}")` with no role
validation — canonical: `pipeline.py:1122-1129` (`checkout_issue_branch`
def, read this session) — so the produced branch string is byte-identical
for every existing caller (verified in acceptance check 4). The change
only stops routing new-shape spawns through a function whose own
docstring calls it "옛 역할 축 네이밍" (legacy role-axis naming),
scheduled for deletion in the architecture record's Step G.

**5. the CLI's `main()` gains the completion-test behavior**
(`spawn.py:2068-2088`):
```python
     if not a.task:
-        sys.exit("맡길 일이 없다. 사용법: spawn.py <역할> \"<맡길 일>\" [-C <경로>]")
+        try:
+            known_roles = set(role_data())
+        except (OSError, ValueError):
+            known_roles = set()
+        if a.role in known_roles:
+            sys.exit("맡길 일이 없다. 사용법: spawn.py <역할> \"<맡길 일>\" [-C <경로>]")
+        task_text = a.role
+        a.task = task_text
+        a.role = _derive_slug_from_task(task_text)
```
reusing the `task_text = a.role` idiom already at the `--skill` path —
canonical: `spawn.py:1738-1746` (read this session) — and a new
`_derive_slug_from_task()` helper (`spawn.py:56-73`) that derives a
branch/record-filename-safe slug deterministically from the task text (an
ASCII-lowercased prefix plus an 8-hex-char SHA1 digest of the full text,
never a random disambiguator), so a respawn with the same task text
reproduces the same branch/record — canonical: `directive_assembly.py:582`
docstring, "never overwrite an existing record (a respawn into the same
workspace)" (read this session, cited by the architecture record's
Identity section as the reason a fresh per-spawn disambiguator was
rejected).

`gates/gates.py`'s `BRANCH_ROLE` and `gates/ci.py`'s `_ISSUE_ROLE_BRANCH`
are untouched — both already match any single path segment
(`^issue-[^/]+/([^/]+)$`), so a slug occupies the position a role name did
with no regex change (acceptance check 6 below confirms `gates/gates.py`
itself was never touched, packaged copy included).

```
derived: git diff --stat -- pipeline.py spawn.py
 pipeline.py | 17 ++++++++++++-----
 spawn.py    | 56 +++++++++++++++++++++++++++++++++++++++++++++++++++++---
 2 files changed, 65 insertions(+), 8 deletions(-)
```

## Why

canonical: `docs/issue-2548/reports/architecture.md`, "What breaks if the
branch/regex half of Step C lands without the `role_settings()`/admission
half" and "What breaks if the CLI default-dispatch half lands without the
rest of Step C" paragraphs (read this session) — both halves independently
still hit a `sys.exit`/refusal without the other, which is why all five
sub-changes above land in this one commit rather than split across PRs.

canonical: `docs/issue-2548/reports/architecture.md`, "### Identity"
section, the quoted `pipeline.py:225-227` block and its surrounding text
"nothing downstream will validate the slug against a fixed set" (read this
session) — this is the property the issue's own acceptance list judges
Step C against. Both closed-set gates that record names
(`role_settings()`'s exit, `_admission_check_directive_completeness()`'s
`_sp.ROLES` membership check) are removed outright in this diff, not moved
or reimplemented against any table — verified directly in acceptance
check 3 below (grep for the exit message finds nothing repo-wide; the
admission check returns `True` for a slug absent from `spawn_roles.json`).

`_sp.ROLES` itself is intentionally not touched — canonical:
`docs/issue-2548/reports/architecture.md`, "Scope boundary" section,
"`_sp.ROLES` itself is not deleted here; only `pipeline.py:1643`'s
membership check on it" (read this session) — it stays alive for
`board.py`'s display logic and `gates/patrol_wiring.py`'s patrol sweep
(Steps E/H), neither of which gates a write or an admission decision.
`spawn_roles.json` stays as the `write_scope` fallback source for legacy
roles (Step D retires it) — an unrecognized slug simply has no entry in
it, matching the `.get(role, {})` shape used at all three lookup sites
this diff touches.

The branch-checkout call-site swap (item 4 above) has no observable effect
of its own, since the two functions were already byte-identical in output
for any role/slug string with no validation difference between them; it is
included because the architecture record's Order section names it as one
of Step C's five sub-changes, in preparation for Step G's deletion of the
now-fully-dead `checkout_issue_branch`.

## What did not work

None.

## Acceptance evidence

All six checks were run for real against this session's actual code, in
throwaway git fixtures outside this repository — never against this
repo's own `main`/board (`git status --short` after every run, quoted at
the end of this section, shows only `pipeline.py`/`spawn.py`/this record
touched). No existing test file covers CLI-level spawn dispatch end to
end — canonical: `grep -rln "subprocess.*spawn.py\|Popen.*spawn" test/`
(read this session) → no output — so these are throwaway scripts/direct
CLI invocations, not additions to `test/`.

### 1. `python3 spawn.py "<task>"` with no role argument reaches a real dispatch

Fixture: a scratch git repo (`/tmp/otr-2555-work`, outside this
repository, deleted after this check) with `origin` a local bare clone (no
GitHub remote) and no `approvers.md` (`--no-contract`).

```
derived: timeout 90 python3 spawn.py "issue-2555 acceptance probe task text" \
  --issue 900001 --no-contract --model haiku --max-turns 2 -C /tmp/otr-2555-work
```
stdout:
```
[issue-2555-acceptance-probe-task-text-7961404d] 해석된 레포/이슈: 확인 실패 — cwd(/tmp/otr-2555-work)가 가리키는 레포에서 이슈 #900001 를 못 읽었다(gh 조회 실패).
```
(a fake issue number against a non-GitHub remote fails the gh lookup —
fail-open per `_resolve_and_echo_issue()`, pre-existing behavior unrelated
to this change; the dispatch itself proceeds regardless.)

stderr — the three requested lines, quoted verbatim:
```
[issue-2555-acceptance-probe-task-text-7961404d] 격리 작업 디렉토리: /home/jwjung/.tokenmaxxxer/work/otr-2555-origin-issue-900001-issue-2555-acceptance-probe-task-text-7961404d  (브랜치 issue-900001/issue-2555-acceptance-probe-task-text-7961404d)
[issue-2555-acceptance-probe-task-text-7961404d] bootstrap_timing admission=0.000 skill_resolve=0.000 workspace=0.000 branch=0.000 returned_pr_gate=0.000 auto_sweep=0.000 rulebook=0.000 core=0.000 gh_token=0.028 settings=0.007 cross_family=43.139 issue_fetch=0.063 directive_write=0.000 design_bearing=0.001 spawn_cmd=0.028 board_snapshot=0.000 total=43.267
[issue-2555-acceptance-probe-task-text-7961404d] 워처 자동 무장: pid 1915771 (로그 /home/jwjung/.tokenmaxxxer/work/otr-2555-origin-issue-900001-issue-2555-acceptance-probe-task-text-7961404d.watcher.log)
```
Branch created — `derived: git -C <that scratch workspace> branch --show-current`
→ `issue-900001/issue-2555-acceptance-probe-task-text-7961404d` (matches
the printed line above).

Record path written — `derived: find <that scratch workspace>/docs -maxdepth 3 -type f`
→ one file, at the relative path `docs/issue-900001/reports/<the same slug>.md`
inside that scratch workspace (untracked scratch fixture, outside this
repository, deleted after this check — not a path in this repo's own
tree). Its frontmatter read `role: <the same slug>`, not a legacy role
name.

`--dry-run` sanity check on a second, distinct unrecognized slug (no
session spawned — only the settings baseline `role_settings()` would use):
```
derived: python3 spawn.py "another unique bare task 2555b" --dry-run -C /tmp/otr-2555-work
{
  "enabledPlugins": {"on-the-record@tokenmaxxxer": false},
  "permissions": {"allow": ["WebSearch", "WebFetch", "Read", "Grep", "Glob", ...]},
  "model": "sonnet"
}
```
prints and exits 0 — no "모르는 역할" message, no `sys.exit`.

This is a real dispatch, not a simulated one — `derived: tail -c 2000
<that scratch workspace>.session.<timestamp>.<pid>.log` showed an actual
`claude-haiku-4-5` assistant `thinking`/`message` block was streamed
before the `--max-turns 2` budget ended the session. The background
watcher process (pid quoted above) and the scratch workspace directory
were killed/removed after capturing this evidence
(`kill 1915771`; `rm -rf` on the scratch workspace and `/tmp/otr-2555-work`,
`/tmp/otr-2555-origin.git`); nothing from this fixture was pushed to any
remote.

### 2. A bare positional that IS a known legacy role name still exits with "맡길 일이 없다"

```
derived: python3 spawn.py implementation
맡길 일이 없다. 사용법: spawn.py <역할> "<맡길 일>" [-C <경로>]
```
exit code 1 — unchanged from before this change, since `implementation` is
a `spawn_roles.json` key (`derived: python3 -c "import json;
print('implementation' in json.load(open('spawn_roles.json')))"` →
`True`), so `main()`'s new branch takes the "genuinely missing task" exit,
not the reinterpret-as-task-text path.

### 3. An unrecognized slug survives `role_settings()` and the admission check — no closed-set rejection

```
derived: grep -rn "모르는 역할" --include="*.py" .
```
→ no output (the message string is gone from the codebase entirely; this
grep ran from this repo's root, this session, after the diff above).

```
derived: python3 -c "
import sys; sys.path.insert(0, '.')
import spawn as _sp, pipeline
pipeline._sp = _sp
ctx = {'role': 'totally-unknown-slug-xyz-2555', 'skills': None, 'cwd': '.'}
print('admission:', pipeline._admission_check_directive_completeness(ctx))
print('role_settings keys:', sorted(pipeline.role_settings('totally-unknown-slug-xyz-2555', None).keys()))
"
admission: True
role_settings keys: ['enabledPlugins', 'permissions']
```
Both checks pass for a slug present nowhere in `spawn_roles.json` —
`derived: python3 -c "import json; print('totally-unknown-slug-xyz-2555'
in json.load(open('spawn_roles.json')))"` → `False`.

### 4. A legacy `spawn.py <role> "<task>"` invocation still works unchanged

Same fixture shape, a second scratch repo (`/tmp/otr-2555-work2`, outside
this repository, deleted after this check).

```
derived: timeout 90 python3 spawn.py implementation \
  "legacy role invocation acceptance probe 2555" --issue 900002 \
  --no-contract --model haiku --max-turns 2 -C /tmp/otr-2555-work2
```
stderr:
```
[implementation] 격리 작업 디렉토리: /home/jwjung/.tokenmaxxxer/work/otr-2555-origin2-issue-900002-implementation  (브랜치 issue-900002/implementation)
[implementation] bootstrap_timing admission=0.000 skill_resolve=0.000 workspace=0.000 branch=0.000 returned_pr_gate=0.000 auto_sweep=0.000 rulebook=0.000 core=0.000 gh_token=0.035 settings=0.002 cross_family=23.645 issue_fetch=0.023 directive_write=0.000 design_bearing=0.000 spawn_cmd=0.035 board_snapshot=0.000 total=23.740
```
Branch — `derived: git -C <that scratch workspace> branch --show-current`
→ `issue-900002/implementation`, the same role-only shape produced before
this change (`checkout_issue_branch`'s old output was byte-identical, per
item 4 in "What was done").

Record path — `derived: find <that scratch workspace>/docs -maxdepth 3 -type f`
→ the relative path `docs/issue-900002/reports/implementation.md` inside
that scratch workspace (untracked scratch fixture, outside this
repository, deleted after this check).

Cleaned up the same way as check 1 after capturing this evidence.

### 5. `write_scope` still refuses an out-of-scope diff under a slug-named branch

Built a throwaway git repo, seeded a roster entry
(`{"issue-9555/issue-2555-writescope-probe-abc123": {"write_scope":
["docs/onlyme/**"]}}`, keyed by `roster.lease_key(9555, slug)` exactly as
Step B's `gates.role_scope()` reads it — canonical:
`docs/issue-2553/reports/implementation.md`, "What was done" section, the
`_roster_write_scope()` description, read this session) for a slug absent
from `spawn_roles.json`, checked out branch
`issue-9555/issue-2555-writescope-probe-abc123`, committed an out-of-scope
file (`src.py`), and called the real `gates.role_scope()` loaded from this
session's actual `gates/gates.py`:

```
derived: python3 /tmp/verify_2555_writescope.py
branch: issue-9555/issue-2555-writescope-probe-abc123
slug (unrecognized w.r.t. spawn_roles.json): True
refusal result: ['write_scope 이탈: src.py (역할 issue-2555-writescope-probe-abc123, 허용: docs/onlyme/**, docs/issue-*/reports/issue-2555-writescope-probe-abc123.md, docs/issue-*/reports/issue-2555-writescope-probe-abc123/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)']
ALL ASSERTIONS PASSED
```
The refusal is sourced from the roster's declared `write_scope`
(`docs/onlyme/**`) — `src.py` doesn't match it — proving the roster-first
authorization path (issue #2553, already live before this step) works
identically for a slug the `spawn_roles.json` closed set has never heard
of; nothing in this path checks slug membership in any table. (This
throwaway script, `/tmp/verify_2555_writescope.py`, was not committed —
same convention issue-2553's own verification used.)

### 6. `on-the-record/gates/gates.py` stays byte-identical to `gates/gates.py`

```
derived: diff -q gates/gates.py on-the-record/gates/gates.py
```
→ no output (byte-identical; `diff -q` prints nothing when the files
match).

```
derived: git status --short
 M pipeline.py
 M spawn.py
?? docs/issue-2555/reports/implementation.md
```
(the untracked line is this record itself, written in this same session —
canonical: this `git status --short` output, read this session.) Neither
`gates.py` copy appears in the changed-files list — this step never
touched either.

### Regression check

```
derived: python3 -m pytest test/ -q
13 failed, 255 passed in 1.69s
```
The same 13 failures exist on the pre-change tree —
`derived: git stash && python3 -m pytest test/ -q && git stash pop` →
identical 13 failures, identical 255-pass count. All 13 are
`SystemExit: --skills: 모르는 스킬 work-in-english` (this sandbox's
`MUSTER_SKILL_REPO` checkout only has a `work` directory, not
`work-in-english` — canonical: the pytest traceback output itself,
`skills.py:127`, read this session) — a pre-existing environment mismatch
unrelated to this change. No test that mocks `spawn.checkout_issue_branch`
broke from the `_checkout_named_branch` call-site swap (item 4 above) —
`derived: python3 -m pytest test/test_branch_naming_dual_scheme.py
test/test_spawn_skills_mount.py test/test_spawn_role_skill_resolution.py -q`
→ `49 passed` — those tests assert the function is never called on paths
that don't reach the branch-checkout step at all (the `--skill` early
return), not that this exact module attribute is the one invoked from
`_spawn_one()`.

## Open findings

None beyond what the architecture record's own "Open findings" section
already tracks — canonical: `docs/issue-2548/reports/architecture.md`,
"## Open findings" section (read this session) — out of this step's
scope: the `spawn_roles.json`/`spawn.ROLES` key-set diff reserved for
Step H, `skills.py`'s stale docstring.

## Next steps

`loop_state: landed` — no further work in this role for this issue.
canonical: `docs/issue-2548/reports/architecture.md`, "### Order" section,
Steps D through H (read this session) — Step D (retire `spawn_roles.json`
as `role_scope()`'s fallback), Step E (`board.py` reads roster lease slugs
instead of the `ROLES` tuple), Step F (`CLAUDE_ROLE` export), Step G
(delete `checkout_issue_branch`, collapse the duplicate `RECORD_PATH`
regex), and Step H (retire/narrow `spawn_roles.json`'s closed table)
remain, as separate, later issues.
