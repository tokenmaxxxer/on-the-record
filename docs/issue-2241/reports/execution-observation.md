---
issue: 2241
role: execution-observation
kind: verify-record
loop_state: cleared
upstream:
  - path: docs/issue-2241/reports/implementation.md
    sha: 71f53cef9ec118395be9d7262920bcdd1c1bb4ad
subject: spawn.py/skills.py at commit 65f5163dc00f2ec50694479e097819faf07ecc03 (PR #2296, open, targets issue #2241 stage 0)
test: >
  independent re-derivation of role-less `--skill` resolution
  (spawn.resolve_skill_source against a skill name absent from every
  _ROLE_SKILLS value, in an isolated skill-repo fixture);
  byte-identity re-diff of resolve_role_source across
  ccee895997e7629495aee4ff7c0588e3082c75bc..65f5163dc00f2ec50694479e097819faf07ecc03;
  empty-skill fail-closed exit code measured via subprocess.run's real
  .returncode (not piped) for whitespace-only and comma-only --skill
  values, plus a self-constructed empty-string --skill edge case not in
  PR #2296's own tests;
  python3 -m pytest test/test_spawn_skill_invocation.py -q
result: passed
assertedBy: independent re-execution, issue-2241/execution-observation session, 2026-08-25
---

# issue-2241 — execution-observation record

## What was done

Independent execution-observation of PR #2296 (`issue-2241: stage 0 —
additive skill-based spawn CLI alongside role path`, open, code commit
`65f5163d`, targets issue #2241 stage 0). This session wrote no change
to `spawn.py` or `skills.py` — it checked out the PR's head
(`origin/issue-2241/implementation`, `71f53cef`) and the specific code
commit `65f5163d` into isolated `git worktree`s
(`/tmp/pr2296-check`, `/tmp/pr2296-check2`) and independently
re-derived, from there, the three checks named by the invoking task
(role-less `--skill` resolution, role-path byte-identity, empty-skill
fail-closed measured by real exit code), plus the PR's own targeted
test file as a sanity cross-check.

Note on citations below: `docs/issue-2241/reports/implementation.md`
(untracked on this branch — that path exists only on
`origin/issue-2241/implementation`, read via the worktree checkout
above), `test/test_spawn_skill_invocation.py` (same: untracked on this
branch, read from the `65f5163d` worktree), and
`docs/issue-2241/reports/implementation/2026-08-25-hunt-stage-0-additive-skill-spawn.md`
(same: untracked on this branch) are all cited below by that same
untracked-on-this-branch status; PR #2296 is still open, not merged.

Check 1 — role-less `--skill` resolution. Built a throwaway
skill-repository fixture (`/tmp/skillrepo-check/{alpha,gamma}`, a git
repo) and confirmed `gamma` appears in none of `spawn._ROLE_SKILLS`'s
values, then called `resolve_skill_source` directly:

```
gamma in any role mapping: False
role-less resolve result: {'source': 'skill-repo', 'skill_dirs': [PosixPath('/tmp/skillrepo-check/gamma')], 'skills': ['gamma'], 'skill_sha': '376ce94'}
```
canonical: `spawn.resolve_skill_source('gamma', Path('/tmp/skillrepo-check'))`, this session — result: PASS. A skill name with no role ever mapped to it resolves cleanly through the `--skill` path without going through `_ROLE_SKILLS`, independently confirming the PR's claim that this path is not a renamed role lookup.

Check 2 — role-path byte-identity. Extracted `resolve_role_source`'s
full function body from `skills.py` at both ends of the PR's own cited
range (`ccee895997e7629495aee4ff7c0588e3082c75bc` before,
`65f5163dc00f2ec50694479e097819faf07ecc03` after, via `git show
<sha>:skills.py` into two throwaway files, not the PR's own diff
transcript) and compared them programmatically:

```
before found: True after found: True
byte-identical: True
```
canonical: regex-extracted `def resolve_role_source(...)` body,
before vs. after, string equality — result: PASS, byte-identical. (The
`git diff` over the same range also shows `_ROLE_SKILLS`/
`_STATIC_POLICY_SKILLS` churn from an unrelated prior commit, issue
#2208's work-in-english change — confirmed by re-reading it, not part
of this PR's own diff, and it touches no line inside
`resolve_role_source`.)

Check 3 — empty-skill fail-closed, exit code measured directly (not
through a shell pipe). Ran `spawn.py` as a real subprocess via
`subprocess.run(...).returncode`, never piping through another command
that would swallow the exit status:

```
--skill ' ': returncode 1, stdout '', stderr "--skill: 빈 스킬 이름이다 — ' '\n"
--skill ',,,': returncode 1, stdout '', stderr "--skill: 빈 스킬 이름이다 — ',,,'\n"
```
canonical: `subprocess.run(['python3', 'spawn.py', '--skill', ' ',
'do the thing', '--issue', '42'], capture_output=True, text=True)` and
the comma-only equivalent, this session — result: PASS. Both exit 1
(nonzero) with empty stdout and the fail-closed Korean error on stderr,
not the false-success empty-skills JSON blob the pre-fix code produced
(per the before-landing hunt record, untracked on this branch, cited by
name above).

Additional self-constructed edge case, not in the PR's own test file
(untracked on this branch, cited by name above): `--skill ''` (a
genuinely empty string, as opposed to whitespace/comma garbage):

```
--skill '': returncode 1, stdout '', stderr '맡길 일이 없다. 사용법: spawn.py <역할> "<맡길 일>" [-C <경로>]\n'
```
This is not a defect: Python's `if a.skill:` truthiness check treats an
empty string the same as `None`/omitted, so `--skill ''` falls through
to the pre-existing role-path dispatch instead of entering the new
`--skill` branch — the remaining positional (`"do the thing"`) is then
consumed as `a.role`, leaving no task text, and the *existing*
role-path "no task" error fires. Still fail-closed (exit 1), just via a
different, pre-existing code path and message than the whitespace/comma
case (which is truthy and does enter the new branch). Distinguishing
this from the whitespace/comma bug the hunt found: an empty string was
never the false-success case (that required a *non-empty* string that
strips to zero names), so this edge case was already safe by
construction, not by the same explicit check.

Check 4 — targeted test file, as a cross-check against the record's
own pasted evidence:

```
$ python3 -m pytest test/test_spawn_skill_invocation.py -q
...........                                                              [100%]
11 passed in 1.05s
```
canonical: pytest run of the file above (untracked on this branch, see
note near the top of this section), this session, from the `65f5163d`
worktree — result: PASS, 11/11, 0 SKIPPED. Matches the PR's own pasted
`11 passed in 3.43s` (same count, different wall-clock, as expected).

## Why

Per this role's governing skill
(`defect-verification-independence-from-upstream-verdicts`), a claim in
an implementation record is pending independent re-derivation, not
evidence in its own right. The invoking task named three specific
checks to re-execute rather than re-read (role-less resolution,
byte-identity, fail-closed exit code) and explicitly flagged the exit
code must be measured directly, not through a pipe — a pipe would let a
downstream command (e.g. `| tail`, `| grep`) report its own exit status
instead of `spawn.py`'s, silently hiding a fail-open regression. Each
check above used its own fixture/script/subprocess call, not PR #2296's
own transcript, and the extra `--skill ''` case was added because the
PR's own test file covers whitespace-only and comma-only garbage but
not the plain-empty-string edge, which exercises a different code path
(Python truthiness) worth confirming doesn't regress into a silent
false-success too.

## Upstream basis

- The PR's own implementation record (untracked on this branch, cited
  by name above) at sha `71f53cef` (PR #2296,
  `origin/issue-2241/implementation`) — the acceptance-evidence claims
  this record's four checks were independently re-derived from and
  re-run against, not re-pasted from.
- `spawn.py`, `skills.py` at commit `65f5163dc00f2ec50694479e097819faf07ecc03`
  — the actual artifacts re-verified by checks 1-3 above (both tracked
  on this branch's ancestry via the fetched commit, read through the
  worktree, not this branch's own working tree).
- The PR's own targeted test file (untracked on this branch, cited by
  name above) — re-verified by check 4.
- The PR's own before-landing warrant-hunt finding (untracked on this
  branch, cited by name above) — the finding whose fix check 3 above
  re-verifies.
- Issue #2241's own decision body — canonical: `gh issue view 2241`.

## Open findings

none — the `--skill ''` observation under Check 3 above is a
pre-existing, unmodified Python-truthiness fact about how `spawn.py`
routes an omitted-vs-empty flag, not a defect this PR introduced or a
gap in the fail-closed guarantee the PR's hunt-fix actually targets
(non-empty garbage that strips to zero names).

## Next steps

None — loop_state is terminal (`cleared`, kind `verify-record`). PR
#2296 is still open (not yet merged); this record's four independent
re-executions match its implementation record's claims exactly, with no
divergence to hand back.
