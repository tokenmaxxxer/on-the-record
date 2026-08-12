---
proposal: docs/issue-1102/proposals/2026-08-12-roles-due-obligation-trigger.md
---

# Hunt record — roles-due-obligation-trigger

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: FINDING — `.gitignore` is a path phase-2 will need but the frozen write set omits, because `.landing-obligations/*.json` is neither listed there nor anywhere else, so those files are picked up as ordinary untracked worktree changes by `gates.changed_files()` (and therefore by the `writeset` gate and any other consumer of it), contradicting the proposal's own load-bearing assumption that these files stay outside git history.
Kind: design-error
Seed: docs/issue-1102/proposals/2026-08-12-roles-due-obligation-trigger.md (2 new files, docs-only)
cap_seconds: 60
tier: default
diff_stat_lines: 2 files added (proposal + survey), 0 code changed yet
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:03:00Z

### Reproduce
```
cd <repo>
mkdir -p .landing-obligations
echo '{"status":"open","pr":1,"sha":"deadbeef","issue":"issue-1102","role":"defect-verification","opened_at":"2026-08-12T00:00:00Z"}' > .landing-obligations/1102-defect-verification-1.json
python3 -c "
import sys; sys.path.insert(0,'gates')
import gates as g
from pathlib import Path
print(g.changed_files(Path('.')))
"
git status --porcelain | grep landing
rm -rf .landing-obligations
```

### Observed
`gates.changed_files()` returns `.landing-obligations/1102-defect-verification-1.json` alongside the real diffed files, and `git status --porcelain` reports `?? .landing-obligations/` — the directory is a plain untracked worktree path, indistinguishable from any other stray file, because no `.gitignore` entry excludes it (checked: `runs/`, `__pycache__/`, `.router.lock`, `.warrant-hunt.*`, `.reexecution/` are listed; `.landing-obligations/` is not, anywhere in the tree).

### Expected
The proposal's own Rationale section states the obligation-status predicate deliberately couples to "a stable *file format*" rather than to `landing_obligation.py`'s API, and `_trigger_matches`'s new branch feeds the obligation JSON's path into the existing `_last_commit_hash`/`_commit_at_or_after` suppression logic, which only behaves correctly (`trigger_hash is None` meaning "uncommitted, fresh") if `.landing-obligations/*.json` never enters git history. Nothing enforces that: the write set (`gates/roles_due.py`, `gates/test_roles_due.py`, `roles/specs/defect-verification.spec.json`, the ADR) never touches `.gitignore`, so a stray `git add -A` or a CI step that commits the working tree would silently flip `_last_commit_hash` from `None` to a real hash, changing suppression behavior, and in the meantime these files show up as ordinary changed-file noise to every gate built on `gates.changed_files()` (e.g. `writeset`'s protected-path check). Phase-2 either needs a `.gitignore` line for `.landing-obligations/` or an explicit statement that these files are expected to be committed — the proposal asserts the former implicitly but lists no path that would make it true.

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — an uncommitted (working-tree-only, never `git add`ed) `docs/<subject>/reports/<role>.md` file suppresses a real failing `.landing-obligations/*.json` obligation from `roles_due()`, because the commit-ancestry "covers" check treats any record with no commit history the same as a record that predates the trigger.
Kind: composition
Seed: gates/roles_due.py `_matching_obligation` / `roles_due()` covers-logic (commit fc47efe, diff against HEAD~1)
cap_seconds: 180
tier: size:large
diff_stat_lines: diff HEAD~1 HEAD touches gates/roles_due.py (+34/-1) and roles/specs/defect-verification.spec.json (+4)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:20:00Z

### Reproduce
In a scratch git repo checked out to branch `issue-999/implementation` (one commit, with `refs/remotes/origin/main` pointed at that same commit so `gates.changed_files` can resolve a base):

```
mkdir -p .landing-obligations roles/specs docs/issue-999/reports
cp roles/specs/defect-verification.spec.json <scratch>/roles/specs/
cat > .landing-obligations/def-verify.json <<'JSON'
{"issue": "issue-999", "status": "failing", "kind": "defect-verification"}
JSON
git add -A && git commit -m wip
```

Baseline (no suppression file present) — `roles_due.roles_due(Path('.'))` correctly reports the role as due:
```
[{'role': 'defect-verification', 'reason': "obligation status 'failing' matched: .landing-obligations/def-verify.json", 'subject': 'issue-999'}]
```

Now create the record file the trigger checks for (`docs/issue-999/reports/defect-verification.md`) but leave it **uncommitted** (plain `write`, no `git add`):
```
echo '# fake suppression file, never committed' > docs/issue-999/reports/defect-verification.md
git status --porcelain   # shows "?? docs/" — untracked, nothing staged
```
Re-run `roles_due.roles_due(Path('.'))`.

### Observed
```
[]
```
The failing obligation is silently dropped — `roles_due()` returns an empty list even though `.landing-obligations/def-verify.json` still says `"status": "failing"` and no real defect-verification record has ever been committed.

Root cause, in `gates/roles_due.py` lines ~216-228: `matched_path` for an obligation match is always the `.landing-obligations/*.json` file itself, which is gitignored/untracked, so `_last_commit_hash(root, matched_path)` is *always* `None` (git has no history for it) regardless of how fresh or stale the obligation actually is. When the suppression record (`docs/<subject>/reports/<role>.md`) also happens to be uncommitted, `record_hash` is `None` too, and the branch:
```python
if trigger_hash is None:
    covers = record_hash is None  # both uncommitted WIP: keep old behavior
```
sets `covers = True`, so the block is treated as "record already covers this diff" and the obligation is skipped — even though the "record" is a throwaway, unstaged, empty-content file that asserts nothing and will vanish on `git status --porcelain` scrutiny or a fresh checkout.

### Expected
An untracked/uncommitted stand-in file with no real content should never be able to mark a `failing` landing obligation as resolved. At minimum, the `trigger_hash is None` (untracked obligation, which is definitionally always true for this trigger kind) branch should not treat an uncommitted candidate record as "covers" — an obligation-status trigger has no commit-anchored trigger path to compare against in the first place, so the WIP/WIP same-old-behavior shortcut inherited from the path-pattern trigger case doesn't apply to it and silently defeats the new mechanism.
