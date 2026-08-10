---
proposal: docs/issue-587/proposals/implementation.md
---

# Hunt record — issue-587-implementation

## before-landing — stance 0: assume the gate/mechanism just touched is bypassable — find the bypass

Verdict: FINDING — `_branch_exists()` in gates/remediation_spawn.py passes the `routed_to` frontmatter field straight into `git branch --list <pattern>`, which treats the argument as a glob; any remediation record whose `routed_to` value contains a glob metacharacter (or, more subtly, one whose `role` happens to be a plausible prefix of an existing branch name once combined with `issue-<n>/`) causes a false-positive "branch exists" match against an unrelated branch, so the still-open remediation record is silently skipped by `pending_remediation_tasks` — no error, no output, nothing spawned.
Kind: silent-failure
Seed: gates/remediation_spawn.py (new file), gates/test_remediation_spawn.py (new file), on-the-record/commands/run.md (step renumbering)
cap_seconds: 180
tier: size:large
diff_stat_lines: (gates/remediation_spawn.py ~115 new, gates/test_remediation_spawn.py new, on-the-record/commands/run.md renumbering edits)
started_at: 2026-08-10T00:00:00Z
ended_at: 2026-08-10T00:20:00Z

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-587-implementation
python3 -c "
from gates.remediation_spawn import _branch_exists
from pathlib import Path
# real repo already has local branch 'issue-587/implementation'
print('wildcard role matches unrelated existing branch:', _branch_exists(Path('.'), 'issue-587/*'))
print('a role that truly has no branch:', _branch_exists(Path('.'), 'issue-587/totally-nonexistent-role-zzz'))
"
```

### Observed
```
wildcard role matches unrelated existing branch: True
a role that truly has no branch: False
```
`git branch --list "issue-587/*"` matches the *existing, unrelated* `issue-587/implementation` branch, so `_branch_exists(root, "issue-587/*")` returns `True` even though no branch named literally `issue-587/*` (nor any branch actually spawned for this remediation's role) exists. Any `remediation-*.md` record whose `routed_to` field is `*`, contains `*`/`?`/`[...]`, or is otherwise a valid git-glob-special string will therefore be treated as "already spawned" by `pending_remediation_tasks` and dropped from its output with `status: open` — the orchestrator's step 3 (per the new run.md) will see nothing to launch and move on, with no signal that a pending remediation was lost. `routed_to` is free plain-text (`_parse_frontmatter` does no validation/escaping), so a malformed or copy-pasted record (e.g. `routed_to: role-*` from a template placeholder left unedited) reproduces this in practice, not just in a contrived test.

### Expected
`_branch_exists` should do an exact-name comparison (e.g. `git show-ref --verify --quiet refs/heads/<branch>`, or compare `git branch --list` output lines exactly against the target string) so a malformed/glob-containing `routed_to` value cannot cause an unrelated branch to be mistaken for evidence that this specific remediation was already spawned, and so it fails loudly (or is rejected) instead of silently dropping an open remediation task.
