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
