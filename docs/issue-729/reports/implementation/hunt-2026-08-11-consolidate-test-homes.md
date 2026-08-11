---
proposal: docs/issue-729/proposals/2026-08-11-consolidate-test-homes.md
---

# Hunt record — consolidate-test-homes

Note: the dispatch prompt named the record path as
`docs/issue-729/reports/hunt-2026-08-11-consolidate-test-homes.md` (flat,
directly under `reports/`). This repo's `board-gate.sh` R5 rule refuses
that path for a role-scoped session (`implementation` writes only
`implementation.md` or `implementation/**`), and every existing
`hunt-*.md` in this repo's own history lives under
`reports/<role>/hunt-*.md` — so this record is filed at
`docs/issue-729/reports/implementation/hunt-2026-08-11-consolidate-test-homes.md`
instead, matching the repo's actual convention.

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the proposal's "Zero broken references" acceptance check and its file-location documentation constraint both miss `docs/handbooks/test-fixture-shape-contracts.md`, a live (non-historical) handbook that hard-codes `shape_contracts.py`'s location as "repo root" — the move makes this claim false and nothing in the plan or its verification step would catch or fix it.
Kind: silent-failure
Seed: docs/issue-729/proposals/2026-08-11-consolidate-test-homes.md (+ docs/issue-729/reports/implementation/survey.md, docs/issue-729/reports/implementation/scout-brief.md)
cap_seconds: 60
tier: size:docs-only
diff_stat_lines: 487 insertions, 3 files (all docs, commit d9f6741)
started_at: 2026-08-11T13:40:00+09:00
ended_at: 2026-08-11T13:56:00+09:00

### Reproduce
```
cd /Users/jk/.tokenmaxxxer/work/on-the-record-issue-729-implementation

# 1. The proposal's own "Zero broken references" check text:
grep -n "Zero broken references" -A3 docs/issue-729/proposals/2026-08-11-consolidate-test-homes.md
# -> scopes the grep to: spawn.py, every file under gates/, every file
#    under on-the-record/ only.

# 2. shape_contracts.py is in the move set (proposal's own files: front
#    matter and "What will be done" list it as one of the nine files
#    git-mv'd from root into tests/).

# 3. A live handbook makes a location claim about it, outside the
#    proposal's checked scope:
grep -n "shape_contracts.py.*repo root" docs/handbooks/test-fixture-shape-contracts.md
grep -n "test_spawn.py" docs/handbooks/test-fixture-shape-contracts.md

# 4. The proposal never names or touches this handbook:
grep -n "test-fixture-shape-contracts" docs/issue-729/proposals/2026-08-11-consolidate-test-homes.md
echo "exit=$?"   # 1 -> no match anywhere in the proposal
```

### Observed
`docs/handbooks/test-fixture-shape-contracts.md:7` reads `` `shape_contracts.py` (repo root) ``,
and line 40 references `test_spawn.py` by its current bare name in a
doc-comment example. The proposal's `files:` front matter (19 entries),
"What will be done" section, and "Zero broken references" verification
step (grep of `spawn.py` + `gates/` + `on-the-record/` only) none mention
or cover `docs/handbooks/`. `grep -n "test-fixture-shape-contracts"` over
the proposal returns nothing (exit 1) — the document doesn't know this
handbook exists. If phase-2 executes exactly as written, this handbook
ends up asserting a false location for `shape_contracts.py` and no listed
acceptance check would fail because of it — it's outside every check's
scope by construction, not despite it.

### Expected
Either the handbook is added to the proposal's `files:` list and "What
will be done" (parallel to how `docs/handbooks/operations.md` was
handled), or the "Zero broken references" check's scope is widened to
include `docs/handbooks/` (not just `spawn.py`/`gates/`/`on-the-record/`),
so a stale location claim in a live handbook can't survive the move
undetected. The proposal explicitly claims "the placement rule must end
up recorded in exactly one document a new test author can read" — but
this second handbook, which also states a location, is left with no
update path and no check that would surface its staleness.

## before-landing — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING
Kind: design-error
Seed: docs/issue-729/proposals/2026-08-11-consolidate-test-homes.md — the `test/` + root test-file consolidation into `tests/`, ~22 files touched.
cap_seconds: 180
tier: size:200+
diff_stat_lines: 263 insertions(+), 62 deletions(-) across 21 files (`git diff --stat HEAD` for unstaged changes) plus 16 new files staged (`git diff --stat --staged`), plus 1 new untracked file (docs/handbooks/test-layout.md) — matches the size:200+ tier.
started_at: 2026-08-11T04:49:51Z
ended_at: 2026-08-11T04:54:09Z

`roles/implementation.json` and `roles/specs/implementation.spec.json` declare `write_scope: ["src/**", "test/**"]` (implementation.json also says `"produces": "src/·test/ 코드, ..."`). This move renamed the directory to `tests/` but did not touch `roles/` (confirmed: `git diff HEAD -- roles/` is empty). Nothing in the repo checks that a role's `write_scope` globs actually match the test directory that exists in the tree — `gates/test_role_spec_shape_batch9.py`'s coverage of `check_axis_evaluation_entry` uses a synthetic `_WRITE_SCOPES` fixture, never the real `roles/*.json` against a real repo path.

This `write_scope` is not decorative — it is read live by `on-the-record/hooks/delegated-judgment-gate.sh` (`load_roles()` reads `roles/*.json`, `role_scope(role)` returns its `write_scope`, `glob_matches` does fnmatch + `**`-prefix fallback) to compute `standing_roles` for the changed-file list of a PR/session, which drives `implicated_axes` → `eligible_roles` → the entire judgment-panel quorum/escalation decision. Because `test/**` no longer matches `tests/...` paths (fnmatch requires the literal `test/` prefix; `tests/` fails both the direct fnmatch and the `**`-prefix startswith check), a change that touches only files in the new `tests/` directory now registers zero standing roles instead of `{'implementation'}` — the exact opposite of what `write_scope`'s own docstring/produces field claims it covers. The same stale-glob effect independently breaks `gates/role_spec_shape.py::check_axis_evaluation_entry` (fnmatch only, no prefix fallback at all) for any review finding whose `target_path` lands in `tests/`, and produces a same-shape but floor-masked drift in `gates/risk_report.py`'s `blast_radius_grade`/`propagation_grade`.

### Reproduce
```
python3 -c "
import json, fnmatch
from pathlib import Path

TARGET = Path('.')

def load_roles():
    roles = {}
    for f in sorted((TARGET / 'roles').glob('*.json')):
        try:
            roles[f.stem] = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
    return roles

ROLES = load_roles()

def glob_matches(path, pattern):
    if fnmatch.fnmatch(path, pattern):
        return True
    prefix = pattern.split('**')[0].rstrip('/')
    return bool(prefix) and (path == prefix or path.startswith(prefix + '/'))

def role_scope(role):
    return [g.replace('<n>', '729') for g in (ROLES.get(role, {}).get('write_scope') or [])]

def standing_roles_for(paths):
    standing = set()
    for p in paths:
        for role in ROLES:
            if any(glob_matches(p, g) for g in role_scope(role)):
                standing.add(role)
    return standing

print('OLD path test/test_gates.py  ->', standing_roles_for(['test/test_gates.py']))
print('NEW path tests/test_gates.py ->', standing_roles_for(['tests/test_gates.py']))
"
```
This is the same `glob_matches`/`role_scope`/`load_roles` logic `on-the-record/hooks/delegated-judgment-gate.sh` runs verbatim (lines ~439-495), against the repo's real `roles/*.json`.

A second, independent reproduction shows the same stale-glob effect breaking `gates/role_spec_shape.py::check_axis_evaluation_entry` (used to shape-validate `axis_evaluation` "contradicts" findings):
```
python3 -c "
import sys
sys.path.insert(0, 'gates')
import role_spec_shape as rss
write_scopes = {'implementation': ['src/**', 'test/**']}
entry = lambda p: {'axis': 'a', 'verdict': 'contradicts', 'citation': 'c',
                    'finding': {'target_path': p, 'required_fix': 'fix'}}
print('OLD ->', rss.check_axis_evaluation_entry(entry('test/test_gates.py'), ['a'], write_scopes))
print('NEW ->', rss.check_axis_evaluation_entry(entry('tests/test_gates.py'), ['a'], write_scopes))
"
```

### Observed
First repro:
```
OLD path test/test_gates.py  -> {'implementation'}
NEW path tests/test_gates.py -> set()
```
Second repro:
```
OLD -> []
NEW -> ["axis_evaluation.finding.target_path 'tests/test_gates.py' does not resolve against any role's write_scope"]
```
A change to a file that only exists post-move (e.g. `tests/test_gates.py`, one of this very delivery's moved files) is now invisible to the `implementation` role's declared write scope: `delegated-judgment-gate.sh` computes zero standing roles for it (where the identical old-path change correctly resolved to `{'implementation'}`), and `role_spec_shape.py`'s shape checker rejects any review finding that targets it as "not resolving against any role's write_scope".

### Expected
`roles/implementation.json` and `roles/specs/implementation.spec.json` should declare `"tests/**"` (or both `"test/**", "tests/**"`) in `write_scope` so that the directory this exact move creates stays recognized by every mechanism that reads `write_scope` as ownership/scope truth (`delegated-judgment-gate.sh`'s panel-quorum computation, `role_spec_shape.py`'s finding-target-path validation, `risk_report.py`'s blast-radius/propagation grading). As shipped, the move silently strands `roles/*.json` pointing at a directory name (`test/`) that no longer exists in the tree, and nothing anywhere checks that `write_scope` globs still resolve against the real repo layout.
