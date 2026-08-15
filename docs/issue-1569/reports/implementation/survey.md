# Survey — issue #1569 (GraphQL-backed gh reads -> REST)

derived: `grep -rn "gh issue view\|gh pr view\|gh pr list\|gh issue list" gates/ hooks/ spawn.py`

Files read in this session containing a single-item `gh issue view` /
`gh pr view` body/title lookup (the class this issue targets):

- `gates/requirement_linkage.py`
- `gates/acceptance_gate.py`
- `gates/requirement_intake_consult.py`
- `gates/pr_reference.py`
- `gates/issue_bundling.py`
- `gates/check_runner.py`
- `spawn.py` line ~7002

Files read in this session containing `gh pr list` / `gh issue list` /
`gh pr view --json statusCheckRollup` — a bulk or non-body-lookup shape, not
edited by this change:

- `gates/ci.py`
- `gates/closure_sweep.py`
- `gates/spawn_on_pr.py`
- `gates/open_work.py`
- `gates/landing_readiness.py`

derived: `ls gates/gh_rest.py 2>&1` (did not exist before this session) — no
prior shared gh-read helper; each of the seven files above had its own local
copy of `subprocess.run(["gh", ...]) -> json.loads -> .get(...)`.

Repo owner/repo is needed for REST paths (`repos/{owner}/{repo}/...`).
Alternative considered: `gh repo view --json nameWithOwner` — rejected, that
call is itself GraphQL and would reintroduce the cross-pool coupling this
issue exists to remove. Chosen: `git remote get-url origin` (local git
command, no GraphQL/REST quota), parsed for the trailing `owner/repo`.
