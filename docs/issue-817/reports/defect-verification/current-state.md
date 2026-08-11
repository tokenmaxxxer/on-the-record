---
kind: current-state-survey
loop_state: handed-off
---

# Current-state survey — issue #817 (Cause B: deliverable-guard non-denial)

## Scope

Diagnose exactly why `on-the-record/hooks/deliverable-guard.sh` does not
deny the plain, un-delegated session's direct `Edit` in the #776 harness
fixture. No fix.

canonical: docs/issue-787/reports/execution-observation.md §5
The #787/#815 merged execution-observation record's §5 shows event 8
(`Edit`) as the first successful write to the fixture's deliverable
path, with zero `orchestrate:`-prefixed deny messages anywhere before or
at that event, in the requirement run's `run.jsonl`.

code_under_review:
- on-the-record/hooks/deliverable-guard.sh
- harness/driver.py

## Candidate mechanisms named by the issue, checked one by one

### 1. Relative-`cwd` bypass — RULED OUT (already fixed at HEAD)

canonical: docs/issue-787/reports/implementation/2026-08-11-hunt-h1-deliverable-guard.md
The implementation role's hunt record found that a relative `cwd`
(`"."`) defeated the git-root walk, silently ALLOWing a write an
absolute-`cwd` payload correctly denied.

canonical: derived command below (git log)
```
derived: git log --oneline -- on-the-record/hooks/deliverable-guard.sh
dee7119 fix(deliverable-guard): widen H1 detection for ordinary target repos
495a908 fix(issue-706): resolve CLAUDE_ROLE from session-role-bind snapshot in 4 presence-only hooks
8a652f2 issue-287: phase 2 — fail-closed reporting across closure_sweep, flows, spawn, deliverable-guard
a92ba57 coding(issue-83): rebrand muster -> on-the-record per approved proposal
```
`dee7119` is the only commit since that touches `cwd` handling, and its
own diff already introduces the current guard, which is present in the
working tree read this session (`on-the-record/hooks/deliverable-guard.sh`,
lines 109-114):
```
cwd = e.get("cwd")
if not isinstance(cwd, str) or not cwd or not posixpath.isabs(cwd):
    deny("PreToolUse payload is missing an absolute cwd — ...")
```

canonical: live reproduction, this session
```
$ mkdir -p /home/jwjung/otr-repro2/src && cd /home/jwjung/otr-repro2 && git init -q
$ echo '{"session_id":"s1","tool_name":"Write","tool_input":{"file_path":"src/evil.py"},"cwd":"."}' > payload_rel.json
$ env -u CLAUDE_ROLE bash on-the-record/hooks/deliverable-guard.sh < payload_rel.json
orchestrate: PreToolUse payload is missing an absolute cwd — cannot verify this write's target relative to the session's actual working directory, denying rather than silently resolving a relative cwd against the hook process's own unrelated cwd.
RC=2
```
A relative `cwd` is now DENIED, not silently allowed, against the
working-tree file read this session.

canonical: docs/issue-787/reports/execution-observation.md, "What was done"
This mechanism is closed and is not the live cause of the #815 event-8
non-denial, which the execution-observation record states ran against
`main` at `df347d3`, after `dee7119`.

### 2. Role-session bypass branch — RULED OUT for this transcript

canonical: on-the-record/hooks/deliverable-guard.sh lines 60-81 (read this session)
Lines 60-81 resolve `role` from the `#698` session-role-bind snapshot,
falling back to the live `CLAUDE_ROLE` env var, and return ALLOW
(`sys.exit(0)`) immediately if `role` is truthy — before any H1
path-classification logic runs.

canonical: docs/issue-787/reports/execution-observation.md, "What was done"
The #815 requirement run explicitly launched with `CLAUDE_ROLE` unset
("two live `claude -p` sessions with `CLAUDE_ROLE` unset"), and no
`OTR_ROLE_BIND_STATE_DIR` snapshot would exist for a freshly-generated
harness `session_id` on its first write. This branch cannot have fired
for event 8. It is structurally real (a stale snapshot reused across
session IDs would trip it) but is not this transcript's mechanism.

### 3. Exemption-segment over-match — RULED OUT

canonical: on-the-record/hooks/deliverable-guard.sh lines 100-102 (read this session)
Lines 100-102 exempt any path segment in
`("scratch", "tmp", ".git", "plugin-cache")`.

canonical: docs/issue-787/reports/execution-observation.md, "What was done"
The fixture path (`fixture_target/__init__.py`, under a workspace such
as `otr-harness-787-req/`) contains none of those segments. Not the
mechanism.

canonical: on-the-record/hooks/deliverable-guard.sh lines 115-124 (read this session)
### 4. Git-root-absence branch — CONFIRMED live bypass

```python
root = None
d = n if posixpath.isabs(n) else posixpath.normpath(posixpath.join(cwd, n))
probe = posixpath.dirname(d)
while probe and probe != "/":
    if os.path.isdir(posixpath.join(probe, ".git")):
        root = probe
        break
    probe = posixpath.dirname(probe)
if root is None:
    sys.exit(0)
```

canonical: on-the-record/hooks/deliverable-guard.sh lines 115-124 and header comment (read this session)
The guard only denies a write once it has walked from the file's
directory up to `/` and found a `.git` directory somewhere in that
ancestry (the H1 policy's own header comment: "Only guard writes inside
a git repo reachable from cwd").

canonical: on-the-record/hooks/deliverable-guard.sh lines 126-130 (read this session)
If no ancestor carries `.git`, `root` stays `None` and the function
returns `sys.exit(0)` — silent ALLOW, no deny message, before the
deliverable-classification branch is ever reached.

canonical: derived command below (harness/driver.py, read this session)
```
derived: grep -n "git init\|\.git\|copytree" harness/driver.py
23:def instantiate_fixture_target(dest_dir):
31:    shutil.copytree(FIXTURE_TEMPLATE_DIR, dest)
```
No `git init` line exists anywhere in `harness/driver.py`. The fixture
copy `instantiate_fixture_target` produces is plain, un-versioned files.

canonical: docs/issue-787/reports/execution-observation.md, "What was done"
The #815 requirement run's workspace, an `otr-harness-787-req`-named
directory under `$HOME`, is an ordinary `$HOME` subdirectory — never
itself version-controlled and with no ancestor up to `/` that is either.

canonical: docs/issue-787/reports/execution-observation.md §5 (cited above)
Every deliverable write inside it walks the full ancestry, finds no
`.git`, and the guard exits 0 before the deny branch — matching event
8's observed shape (no `orchestrate:`-prefixed deny anywhere in
`run.jsonl`, immediate silent `Edit` success).

### Minimal reproduction (this session, live)

canonical: live reproduction, this session (commands and output below)
```
$ mkdir -p /home/jwjung/otr-repro-clean/fixture_target && cd /home/jwjung/otr-repro-clean
$ echo '{"session_id":"s1","tool_name":"Edit","tool_input":{"file_path":"fixture_target/__init__.py","old_string":"a","new_string":"b"},"cwd":"/home/jwjung/otr-repro-clean"}' > payload.json
$ env -u CLAUDE_ROLE bash on-the-record/hooks/deliverable-guard.sh < payload.json
RC(no-git)=0
$ git init -q
$ env -u CLAUDE_ROLE bash on-the-record/hooks/deliverable-guard.sh < payload.json
orchestrate: this is an orchestrator session and fixture_target/__init__.py is a deliverable path in a board repo. Deliverables are role work: draft the issue, get the user's confirmation, and spawn the role (spawn.py <role> ... --issue <n>). You author only confirmed issues, PR comments, and docs/specs/approvers.md.
RC(with-git)=2
```
Identical payload, identical file path, identical session; the only
variable is whether `.git` exists in the ancestry. No-`.git` → silent
ALLOW (rc=0, no stderr). `.git` present → DENY (rc=2, deny-and-redirect
message). This is the mechanism behind #815's event 8.

## Conclusion

canonical: sections 1-4 above (this file)
Cause B is the git-root-absence branch in
`on-the-record/hooks/deliverable-guard.sh` (`if root is None:
sys.exit(0)`), triggered because the harness never `git init`s the
fixture-target working copy it instantiates in `harness/driver.py`. This
is a distinct mechanism from the relative-`cwd` candidate (already fixed
at HEAD), the role-session branch (structurally real, but not this
transcript's cause), and the exemption-segment-over-match candidate
(ruled out, no matching segment in the fixture path). It is also
distinct from Cause A (#810, permission-mode denial of
`spawn.py`/board-read calls) — Cause B is a guard-logic gap independent
of permission mode.

## What did not work

None.
