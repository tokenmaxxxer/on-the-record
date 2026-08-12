proposal: docs/issue-993/proposals/implementation.md
transition: after-proposal
stance: 3
tier: default

# Hunt record — implementation

## after-proposal — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — the proposed gate's "count records per `roles/*.json` stem by walking `docs/issue-*/reports/`" step depends on a role-name-to-report-path mapping that no file in the repo maintains; the board's actual filenames don't match what the roles' own `write_scope` declares.
Kind: design-error
Seed: docs/issue-993/proposals/implementation.md step 2(a)-(b); docs/issue-993/reports/implementation/survey.md lines ~80-88
cap_seconds: 120
tier: default
diff_stat_lines: 2 new files (survey.md, implementation.md), docs-only
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:05:00Z

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-993-implementation
grep -n "write_scope" -A2 roles/refactoring-legacy.json roles/test-authoring.json
find docs/issue-*/reports -maxdepth 1 -type f -name "refactoring-legacy.md" -o -name "test-authoring.md"
find docs/issue-*/reports -mindepth 2 -type f -name "*.md" | wc -l
find docs/issue-*/reports -maxdepth 1 -type f -name "*.md" | wc -l
```

### Observed
`roles/refactoring-legacy.json` and `roles/test-authoring.json` both declare
`"write_scope": ["docs/issue-<n>/reports/<role>.md"]` — a single flat file
per issue. But no `refactoring-legacy.md` or `test-authoring.md` flat file
exists anywhere under `docs/issue-*/reports/` (the find for those two
literal names returns nothing), and the actual board convention has split:
339 flat `<role>.md` files coexist with 619 files nested one level deeper
under `docs/issue-<n>/reports/<role>/<arbitrary-name>.md` (e.g.
`docs/issue-1077/reports/implementation/survey.md`,
`docs/issue-1006/reports/implementation/deviation-log.md`). The proposal's
step 2(a) says the new gate will walk `docs/issue-*/reports/` "the same way
the current-state survey's own `find` derivation did" — but the survey's
own `find` derivations (grep -n "find " docs/issue-993/reports/implementation/survey.md)
never actually enumerated or counted per-role-stem records from
`docs/issue-*/reports/` at all; the only `find` calls in the survey are
`find gates -iname "*utilization*"` and a grep over `implementation.md`
files specifically. There is no code anywhere in the repo, and no
convention documented in any role spec, that reconciles a role stem like
`refactoring-legacy` against a report tree that mixes flat files, per-role
subdirectories, and freely-named files inside those subdirectories. The
gate the proposal describes ("counting records per roles/*.json stem")
therefore names a mapping mechanism that nothing in the repository
currently maintains or has ever computed.

### Expected
Either the proposal should specify the exact parsing rule the new gate
will use to turn an arbitrary `docs/issue-<n>/reports/**/*.md` path into a
role stem (and that rule should already exist and be demonstrated against
the real board, not asserted by analogy to a `find` call that doesn't
appear in the survey), or the proposal should acknowledge that
`write_scope`'s flat-filename convention is stale/unmaintained relative to
actual practice before building a gate that silently either (a) undercounts
every role whose records live in a subdirectory, or (b) fails to build at
all because the stem-derivation step has no defined behavior for e.g.
`docs/issue-100/reports/coding.md` (a directory name, "coding", matching no
current `roles/*.json` stem).
