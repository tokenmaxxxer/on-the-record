# Deviation log — partnerships-bd (issue #1174)

- 2026-08-13T07:54:00Z | filed | pr-preflight.sh's amendments-reconciled
  check raced new issue comments faster than `gh pr create` could
  complete, on both the rulebook repo (tokenmaxxxer/partnerships-bd-rulebook)
  and this parent repo — 4 new comments arrived across the attempts
  (issuecomment-5277524495, -5277594777, -5277599016, -5277607684), the
  first 3 reconciled in turn (commits 4d80975, 030f481, a964dd1). Same
  pr-preflight-race pattern already logged by issue-retrospective and
  other role sessions on this issue. Stopping retries after this turn's
  budget per that precedent: commits through a964dd1 are pushed to
  issue-1174/partnerships-bd (this repo) and issue-1174/operational-playbook
  (partnerships-bd-rulebook) for on-the-record's outside relay to open
  both PRs. reported, not spawned.
