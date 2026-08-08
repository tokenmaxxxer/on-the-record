# Survey — issue-541

## Reproduced

`python3 -m pytest -q test_gates.py::t_new_roles_resolve_without_a_local_checkout`
fails in this clean checkout too (not contamination):

```
AssertionError: interaction-design: 로컬 경로를 박으면 다른 기계에서 깨진다
assert 'path' not in {..., 'path': '$TOKENMAXXXER_RULEBOOKS/interaction-design-rulebook', ...}
```

## Root cause

`test_gates.py:243-252` asserts that `interaction-design`, `defect-verification`,
and `issue-retrospective` have no `"path"` key in their `roles/*.json` — these
three are the deliberate first case of roles with no local checkout, forcing
`spawn.rulebook_source()` (spawn.py:237-248) to fall back to the `github`
source.

`git log -p -- roles/interaction-design.json` shows commit `88baa3e`
("Realize discovery/design-family batch-2 role specs (issue-524)") added
`"path": "$TOKENMAXXXER_RULEBOOKS/interaction-design-rulebook"` to
`interaction-design.json`, describing it in the commit message as "fixes
interaction-design.json's missing 'path' key" — i.e. that commit treated the
absent `path` as an omission to fix uniformly with the other 40 roles, not
realizing this role was intentionally one of the three github-only exemplars
the test locks in. This is the regression: behavior changed (path added),
not the test's assumption going stale.

Census over `roles/*.json` confirms only two roles lack `"path"`, matching
the test's other two role names exactly:

```
$ python3 -c "
import json, glob
for f in sorted(glob.glob('roles/*.json')):
    d = json.load(open(f))
    print(('path' if 'path' in d else '-'), f)
" | grep '^- '
- roles/defect-verification.json
- roles/issue-retrospective.json
```

## Write set implied

- `roles/interaction-design.json` — drop the `"path"` key (data-only fix,
  restores the file to its pre-88baa3e no-local-checkout shape).

No other file touches this behavior: `spawn.py`'s `rulebook_source`/
`rulebook_dir` already handle the no-`path` case correctly (that's exactly
what `defect-verification.json`/`issue-retrospective.json` exercise today),
and no other gate or spec requires `"path"` to be present (checked
`gates/*.py`, `roles/specs/*.json` — no `path`-presence assertion found).

## Skip condition

Per scout-directive: this is a pure bugfix (a single stray key added by a
prior commit, contradicting an already-existing, still-valid test and
docstring rationale) — no design decision is open, so the scout sweep is
skipped.
