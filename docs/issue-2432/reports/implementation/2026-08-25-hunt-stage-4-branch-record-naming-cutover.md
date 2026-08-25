---
proposal: docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-cutover.md
---

# Hunt record — stage-4-branch-record-naming-cutover

## after-proposal — stance 1: board() discovery composition regression — does the skill-axis sweep collide with or corrupt the ROLES-axis dict, or break an existing caller that assumes ROLES-only keys?

Verdict: FINDING — `board._skill_axis_report_names()` sweeps in ANY non-ROLES-named `.md` file under `reports/` that merely has a frontmatter block — not just real `<skill>-<lease-disambiguator>` records — so pre-existing, unrelated files (old pre-cutover role names like `coding.md`/`qa.md`/`verify.md`, and even this hunt-record format itself, e.g. `hunt-implementation.md`) get treated as live skill-axis role records by `board()`, silently changing board membership/content for dozens of already-existing subjects and breaking `_front_role()`'s single-rootless-record invariant (used by `approve_scope()`, which writes a real git commit).
Kind: composition
Seed: board.py's `_skill_axis_report_names()`/`board()` diff (this PR); reproduced against this repo's own real `docs/issue-*/` tree, no synthetic fixture needed
cap_seconds: n/a (not given a dispatcher cap in this invocation)
tier: n/a
diff_stat_lines: n/a (not given a diff-stat by the dispatcher; board.py's diff alone is ~35 lines per `git diff main...issue-2432/implementation -- board.py`)
started_at: 2026-08-25T00:00:00Z
ended_at: 2026-08-25T00:40:00Z

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2432-implementation

# 1. Confirm docs/issue-31/reports/ holds only PRE-CUTOVER role names
#    (coding.md, qa.md, verify.md) — none of them a `<skill>-<disambiguator>`
#    shaped name, none related to checkout_issue_branch_for_skill at all:
git ls-tree -r --name-only HEAD -- docs/issue-31/reports/

# 2. Old (pre-#2432) board() semantics never surfaced issue-31 at all
#    (no file there matches a current ROLES member):
python3 -c "
import sys; sys.path.insert(0,'.')
from pathlib import Path
import spawn, re
docs = Path('.') / spawn.BOARD
found = {}
for d in sorted(p for p in docs.iterdir() if p.is_dir()):
    if not re.match(r'^issue-[0-9]+\$', d.name):
        continue
    rep = d / 'reports'
    roles = {r: spawn.frontmatter(rep / f'{r}.md') for r in spawn.ROLES if (rep / f'{r}.md').is_file()}
    if roles:
        found[d.name] = roles
print('issue-31 in OLD-semantics board:', 'issue-31' in found)
"

# 3. Current (post-#2432) board() now includes it, with the stale
#    pre-cutover names presented as if they were skill-axis records:
python3 -c "
import sys; sys.path.insert(0,'.')
from pathlib import Path
import spawn
b = spawn.board(Path('.'))
print('issue-31' in b, list(b.get('issue-31', {}).keys()))
"

# 4. Concrete downstream breakage: issue-1077 has a real current-scheme
#    record (implementation.md) AND an unrelated hunt-record file that
#    happens to sit directly under reports/ (hunt-implementation.md,
#    frontmatter: `proposal: docs/issue-1077/proposals/implementation.md`
#    — not a role/skill record at all). board._front_role(), which
#    approve_scope() uses to pick which record file to write the
#    scope-approved commit into, resolves correctly under old semantics
#    but breaks under the new sweep:
python3 -c "
import sys; sys.path.insert(0,'.')
from pathlib import Path
import spawn, board as board_mod
root = Path('.').resolve()
roles = spawn.board(root)['issue-1077']
print('keys:', list(roles.keys()))
print('front (post-diff, polluted):', board_mod._front_role(root, 'issue-1077', roles))
roles_old = {r: fm for r, fm in roles.items() if r in spawn.ROLES}
print('front (old semantics, ROLES-only):', board_mod._front_role(root, 'issue-1077', roles_old))
"
```

### Observed
```
$ git ls-tree -r --name-only HEAD -- docs/issue-31/reports/
docs/issue-31/reports/coding.md
docs/issue-31/reports/qa.md
docs/issue-31/reports/qa/survey.md
docs/issue-31/reports/verify.md
docs/issue-31/reports/verify/survey.md

issue-31 in OLD-semantics board: False

issue-31 in NEW (post-diff) board: True ['coding', 'qa', 'verify']

keys: ['implementation', 'hunt-implementation']
front (post-diff, polluted): None
front (old semantics, ROLES-only): implementation
```
A repo-wide scan shows this is not a one-off: 29 already-existing subjects (issue-31, issue-35, issue-38, issue-40, issue-43, issue-54, issue-64, issue-73, issue-74, issue-95, issue-100, issue-103, issue-105, issue-109, issue-114, issue-115, issue-120, issue-126, issue-129, issue-132, issue-135, issue-140, issue-145, issue-149, issue-155, issue-162, issue-1077, issue-1174, issue-1199) get non-`<skill>-<disambiguator>`-shaped keys injected into `board()` purely because they contain an old-scheme (`coding`, `qa`, `verify`, `review`, `feasibility`, `ux-design`) or altogether-unrelated (`hunt-implementation`, `upstream-defect-report`) frontmatter'd `.md` file directly under `reports/`.

### Expected
`_skill_axis_report_names()` should only surface files that are actually new-scheme skill-axis records (i.e. shaped like `<skill>-<lease-disambiguator>`, where the disambiguator is `roster.new_lease_disambiguator()`'s 8 lowercase-hex-char output, per `checkout_issue_branch_for_skill`) — not every frontmatter'd `.md` file that merely fails to match today's fixed `ROLES` tuple. As written, `board()` cannot tell "new-scheme record" apart from "any other stray file that happens to have a `---` block," so it resurrects unrelated pre-existing files (including this very hunt-record format) into live board state for subjects where they were never board-visible before, and it can make `_front_role()` (which `approve_scope()` relies on to know which record file to commit a scope-approval into) silently regress from a working single-rootless resolution to an unresolvable multi-rootless one.
