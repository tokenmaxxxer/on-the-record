scout-skip: pure bugfix — no design decision open (adding entries to an existing .gitignore, same shape as PR #1109's `.landing-obligations/` entry).

## Current state

`.gitignore` (repo root) lists `.landing-obligations/` but not the other
runtime marker files hooks write into the target repo root.

canonical: `grep -rn` over `on-the-record/hooks/*.sh` for repo-root marker-write patterns (excluding `.landing-obligations/`, already handled by #1109)
- `on-the-record/hooks/directive.sh` line 139 — `GREETED_MARKER="$(pwd -P)/.orchestrate-greeted"`
- `on-the-record/hooks/self-update.sh` lines 44 and 47 — writes `"$CHECKOUT/.pull-check"`
- `on-the-record/hooks/directive.sh` line 34 — `OTR_MN_DIR="$(pwd -P)/.orchestrate-monitor-alive"` (a directory)

canonical: `touch .orchestrate-greeted .pull-check && python3 -m pytest tests/test_gates.py::t_rulebook_version_is_recorded -q` run before the .gitignore fix
Result reproduced the issue's reported failure: `AssertionError: assert '커밋안됨' not in '...(issue-1110/implementation) — 설치본 없음'`.

## Write set

- `.gitignore` — add the three marker paths.
