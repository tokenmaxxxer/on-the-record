# Deviation log — issue-1199/execution-observation

canonical: `git -C /tmp/eo-rb log -1 --oneline origin/issue-1199/execution-observation` and `git log -1 --oneline origin/issue-1199/execution-observation`, both read this session — commits 67049c6 and 7774e99 respectively.

2026-08-14T00:10:00Z filed: `gh pr create` for
`issue-1199/execution-observation` (this repo) hit `pr-preflight.sh`'s
per-attempt reconcile gate three consecutive times this session, each
blocked by a fresh automated judgment-watcher comment posted after the
immediately-prior reconcile (issuecomment-5288194557, -5288197397,
-5288200258 on issue #1199) — the same systemic PR-create race
documented for the prior 2026-08-13 attempt in this same log and in
`docs/issue-1199/reports/implementation/deviation-log.md`, not a
one-off; reported, not spawned, per SCOPE-EXCEEDED RULE. This session
stops retrying `gh pr create` here. Both deliverables are committed and
pushed regardless: this repo's commit f69688e9 on
`origin/issue-1199/execution-observation`, and the
execution-observation-rulebook repo's commit 326ec91 on
`origin/issue-1199/execution-observation-plugin-rework` with PR
https://github.com/tokenmaxxxer/execution-observation-rulebook/pull/71
already open. Opening this repo's own PR is left as a follow-up for
whichever session next reconciles a quiet stretch of this issue's
comment thread.

2026-08-14T00:00:00Z inline: 2026-08-14 amendment superseded the
2026-08-13 domain-tool-basis fold-in (67049c6) — reworked in place on
the same `issue-1199/execution-observation` branches (both repos),
adding a Claude Code plugin/skill survey (obra/superpowers,
tag1consulting/claude-comprehensive-review,
aidankinzett/claude-git-pr-skill) without discarding the prior
citation-admissibility rules, per the amendment's own KEEP-existing/
ADD-plugin-learnings instruction; stays inside the frozen write set
(same two files), mechanical fold-in, does not change what the record
claims beyond the new rules — inline per this session's own
deviation-loop classification.

2026-08-13T00:00:00Z filed: `gh pr create` in the execution-observation-rulebook repo hit `pr-preflight.sh`'s per-attempt reconcile gate three consecutive times, each blocked by a fresh automated judgment-watcher comment posted after the immediately-prior reconcile (issuecomment-5277569835, -5277573493, -5277577662 on issue #1199) — the same systemic PR-create race against an external watcher's cadence already documented in `docs/issue-1199/reports/implementation/deviation-log.md` for the sibling `issue-1199/implementation` branch, not a one-off; reported, not spawned, per SCOPE-EXCEEDED RULE. This session stops retrying `gh pr create` here. The execution-observation-rulebook repo's own commit 67049c6 is on `origin/issue-1199/execution-observation` per the citation above, satisfying commit+push for that deliverable; opening the PR there (and this repo's own record PR) is left as a follow-up for whichever session next reconciles a quiet stretch of this issue's comment thread. Both this repo's commit (7774e99) and the execution-observation-rulebook repo's commit (67049c6) are pushed to their respective `issue-1199/execution-observation` branches regardless.
