---
issue: 2610
role: architecture-interface-contract-shape+silent-failure-audit-04261cd0
author: architecture-interface-contract-shape+silent-failure-audit-04261cd0
skills: architecture-interface-contract-shape (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2609/reports/architecture-interface-contract-shape+silent-failure-audit-b3934eed.md
    sha: same-commit
---

# issue-2610 — architecture-interface-contract-shape+silent-failure-audit-04261cd0 record

## What was done

Deleted `spawn_roles.json` (44-entry role catalog) and repointed every
non-docs consumer so no `role`/task-derived slug is ever looked up in a
closed set again.

canonical: this session's own spawn task text — "the decisive test,
unchanged since #2548: not 'did the name change' but 'does anything
still validate identity against a closed set'... if a capability cannot
be provided without enumerating identities, the capability is dropped."

derived: `git show --stat HEAD` this session ->
```
consult.py, directive_assembly.py, gates/ci.py, gates/closure_sweep.py,
gates/gates.py, gates/patrol_wiring.py, gates/record_lint.py,
gates/roles_due.py (deleted), gates/scope_adherence.py,
gates/spawn_on_pr.py, gates/spec_schema_five_activities_test.py (deleted),
on-the-record/commands/consult.md, on-the-record/gates/gates.py,
on-the-record/gates/record_lint.py,
on-the-record/hooks/delegated-judgment-gate.sh,
on-the-record/hooks/merge-allow-gate.sh,
on-the-record/hooks/quality-bar-gate.sh,
on-the-record/hooks/record-scaffold.sh, pipeline.py, spawn.py,
spawn_roles.json (deleted), test/test_spawn_role_skill_resolution.py,
test/test_spawn_skills_mount.py
```

Outcome 1 (task-derived, no enumeration): `on-the-record/hooks/
delegated-judgment-gate.sh` — the per-role `judgment_axes` lookup
(which named role owns axis X) is replaced by scanning
`docs/issue-<n>/reports/*.md` for self-declared `axis:` inside
`<!-- axis_evaluation -->` blocks — the same pattern
`open_decision_item.candidate_axes` already used. Quorum is per axis
now (every implicated axis needs >=1 evaluation from some record)
instead of per role. `gates/patrol_wiring.py`'s merge-sweep role
iteration is derived from the merge's own changed
`docs/issue-<n>/reports/<role>.md` paths instead of a fixed 44-name
list.

Outcome 3 (dropped): per-role frontmatter enum validation in
`gates/gates.py`, per-role terminal-loop_state detection (replaced with
a role-independent structural rule: not empty, not "in-progress", not a
refusal state), per-role env/sandbox in
`pipeline.py`'s spawn-settings assembly, per-role record scaffolding
fields in `directive_assembly.py`'s record skeleton writer, the whole
role-triggered "roles due" nudge feature, and the test file that
asserted the catalog's own internal data shape.

`spawn.py`'s bare-invocation `역할:` catalog print is removed;
`on-the-record/commands/consult.md` now points at the skill-repository
checkout's real directory listing instead. `on-the-record/hooks/
record-scaffold.sh` now calls `directive_assembly.write_record_skeleton()`
(the function every real session's bootstrap already uses) instead of
its own separately-hardcoded, drifted template.

## Why

canonical: `gh issue view 2610 --comments` output, read this session —
the operator's ruling: "if a capability cannot be provided without
enumerating identities, the capability is dropped... What is not
acceptable is keeping the enumeration because the capability seemed
worth it." Every consumer above was checked against that test. The
judgment-gate and patrol-sweep consumers had task-derived substitutes
already present elsewhere in the codebase. Every Outcome-3 consumer's
per-role lookup already returned an empty/no-op default for any role
not literally one of the 44 catalog names — verified per-consumer while
reading each file this session (`pipeline.py`'s own comment already
documented the empty-fallback behavior for slug roles;
`directive_assembly.py`'s try/except around the same kind of lookup
swallowed every non-catalog role identically) — so dropping those paths
removes code that was already unreachable under the current
free-form-slug identity axis (#2555/#2560/#2561), not an observed
capability.

derived: reading `gates/gates.py`'s refusal-reason check before this
session's edit — its role-config lookup raised `KeyError` for any
non-catalog role and the exception branch appended a "cannot check"
violation, while the check's own verdict line two lines below (state
membership in a role-independent global set) never referenced the
looked-up role config at all. That is a silent-failure shape (the
lookup gated whether the check ran; the check itself never needed the
lookup) fixed by this session's edit.

Did not run a consult for the Outcome-2-vs-3 line: each consumer had
direct, checkable evidence (the catalog's own contents, or an
already-existing empty-fallback already in the code) rather than a
genuinely close tradeoff.

## What did not work

None.

## Upstream basis

See frontmatter `upstream:`. derived: `git log --oneline -5` this
session at start showed no issue-2610 commits ahead of `origin/main` —
started from a clean branch, not from PR #2625's shards. Design
re-derived from the issue body and #2625's closing comment, both quoted
in the spawn task text.

## Open findings

The issue's third acceptance check ("spawn a session end-to-end and
show it reaching PR") is satisfied by this session's own delivery —
this PR is that spawn, landing through the unmodified pipeline this
session repointed. A separate additional throwaway spawn was not run
given turn-budget constraints late in this session.

## Next steps

None for this issue.

## Acceptance verification

acceptance: `python3 spawn.py | grep -c '역할:'` — result:
```
0
```

acceptance: `ls spawn_roles.json; grep -rln 'spawn_roles' --include=*.py --include=*.sh --include=*.md . | grep -v '^./docs'` — result:
```
ls: cannot access 'spawn_roles.json': No such file or directory
(0 non-docs hits)
```

acceptance: `bash on-the-record/hooks/record-scaffold.sh smoke-test-role-xyz 999999 /tmp/rs-smoke` — result:
```
record-scaffold: wrote /tmp/rs-smoke/docs/issue-999999/reports/smoke-test-role-xyz.md
```

acceptance: `python3 -m py_compile spawn.py pipeline.py consult.py directive_assembly.py gates/gates.py gates/ci.py gates/record_lint.py gates/patrol_wiring.py gates/closure_sweep.py gates/scope_adherence.py gates/spawn_on_pr.py on-the-record/gates/gates.py on-the-record/gates/record_lint.py test/test_spawn_role_skill_resolution.py test/test_spawn_skills_mount.py` — result:
```
(no output, exit 0 — all compile)
```

acceptance: `bash -n on-the-record/hooks/delegated-judgment-gate.sh on-the-record/hooks/merge-allow-gate.sh on-the-record/hooks/quality-bar-gate.sh on-the-record/hooks/record-scaffold.sh` — result:
```
(no output, exit 0 — all valid bash)
```

### Skill verdicts

skill-verdict: architecture-interface-contract-shape — applied: invoked; derived: used the boundary-contract framing (published-language, no per-producer negotiation) from this skill's own catalog to choose task-derived self-declaration over a new lookup table for the judgment gate.
skill-verdict: silent-failure-audit — applied: invoked; derived: found and fixed the refusal-check silent-failure cited in the Why section above by reading every role-lookup fail path across the consumer list this session touched.
