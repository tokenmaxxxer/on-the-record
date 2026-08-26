---
issue: 2451
role: execution-observation
author: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2451/reports/implementation.md
    sha: b9656656c214a3ac802eeba32e0a605620ee1dc1
  - path: on-the-record/directive/merge-gates.md
    sha: b9656656c214a3ac802eeba32e0a605620ee1dc1
subject: PR #2470 (issue-2451/implementation, head b9656656c214a3ac802eeba32e0a605620ee1dc1, base main)
test: issue #2451 Acceptance section — 3 check bullets
result: untested
assertedBy: execution-observation, independently re-run this turn
---

# issue-2451 — execution-observation record

Path convention: `on-the-record/directive/merge-gates.md` cited below with
an explicit sha lives on `issue-2451/implementation` at
`b9656656c214a3ac802eeba32e0a605620ee1dc1` (PR #2470, still OPEN at
observation time — `mergeable: MERGEABLE`, not yet on `main`). All `gh`/
`git` queries against the live remote were re-run fresh this turn, not
copied from the implementation record's transcripts.

## What was done

Independently re-derived all three of issue #2451's acceptance checks
against PR #2470, rather than citing the implementation record's own
claims.

**Acceptance bullet 1 — `merge-gates.md` diff carries an explicit
`--delete-branch` instruction:**

acceptance: `git show b9656656c214a3ac802eeba32e0a605620ee1dc1:on-the-record/directive/merge-gates.md | grep -n -A6 DELETE-BRANCH` (this turn, fetched `origin/issue-2451/implementation` directly, not via the PR diff text) — result:
```
101:- DELETE-BRANCH ON MERGE (issue #2451): every `gh pr merge` call MUST pass
102-  `--delete-branch`. The repo's `deleteBranchOnMerge` setting does not
103-  reliably cover API/CLI-driven merges — this session directly observed
104-  merged PRs (e.g. #2439, #2413) whose head branch survived without it.
105-  Omitting the flag leaves stray `issue-<n>/<role>` branches on the
106-  remote after merge.
```
acceptance: `git show --stat b9656656c214a3ac802eeba32e0a605620ee1dc1` (this turn) — result:
```
 docs/issue-2451/reports/implementation.md | 143 ++++++++++++++++++++++++++++++
 on-the-record/directive/merge-gates.md    |   6 ++
 2 files changed, 149 insertions(+)
```
Confirms the diff touches only `merge-gates.md` (+6) and the
implementation record itself (+143) — no other file changed. The bullet
sits in the same pre-merge-steps section as the neighboring
`VERDICT-ASYMMETRY`/`STALE-REVERT` bullets, matching their citation style
(`(issue #NNNN)`, concrete observed-PR examples). Bullet 1 outcome:
derived directly from the two command outputs immediately above, not
cited from the implementation record.

**Acceptance bullet 2 — backfill cleanup, before/after stray-branch
count:**

Independently re-ran the same cross-reference live against the current
remote, not by re-reading the implementation record's pasted numbers.

acceptance: `gh pr list --repo tokenmaxxxer/on-the-record --state merged --json headRefName,number --limit 3000` (this turn) piped through a Python cross-reference against `git ls-remote --heads origin` (this turn) and `gh pr list --state open --json headRefName,number` (this turn) — result:
```
merged PRs fetched: 1507
open PRs fetched: 24
total remote heads: 33
stray branches (merged-PR head, not open, still on remote): 0
```
Matches the implementation record's claimed `AFTER stray count: 0`,
independently re-derived rather than re-cited.

acceptance: `git ls-remote --heads origin | grep -E '(issue-1978/implementation|issue-2001/implementation|issue-2156/conformance-review|issue-2186/implementation|issue-2187/implementation|issue-2227/execution-observation|issue-2274/conformance-review|issue-2293/execution-observation|issue-2413/conformance-review|issue-2413/execution-observation|issue-2414/conformance-review)'` (this turn, the 11 branches the implementation record claims it deleted) — result:
```
(no output — none of the 11 names match any current remote head)
```

acceptance: `gh pr list --repo tokenmaxxxer/on-the-record --state all --head <branch> --json number,state,headRefName` run once per each of the same 11 branch names (this turn) — result: every PR entry returned across all 11 lookups is `state: MERGED` or `state: CLOSED`; zero `OPEN` entries. No still-open PR was orphaned by the backfill. Bullet 2 outcome: derived directly from the three command outputs immediately above.

**Acceptance bullet 3 — future-merge observation ("after this issue
lands, this session's or a future session's next `gh pr merge` call is
observed to include `--delete-branch`, branch deletion confirmed via
`git ls-remote`"):**

acceptance: `gh pr view 2470 --repo tokenmaxxxer/on-the-record --json state` (this turn) — result:
```
{"state":"OPEN"}
```
The `merge-gates.md` directive change has not landed on `main` yet, and
this session (execution-observation) holds no merge authority under the
role-handoff contract ("never approve or merge yourself"), so it cannot
itself produce the triggering event. Bullet 3 outcome: derived directly
from the command output immediately above — no post-landing `gh pr
merge` event exists yet for this bullet to observe. Not a defect in the
delivered work — see Open findings below.

## Why

canonical: `gh pr view 2470 --repo tokenmaxxxer/on-the-record --json state` (this turn), same command shown under `## What was done` bullet 3 above — result: `{"state":"OPEN"}`.

The implementation record asserts `verdict: pass` for all three
acceptance checks. Bullets 1 and 2 were re-derived from scratch against
the live remote and the PR's actual commit sha rather than treating the
record's own transcripts as sufficient, and both independently landed on
the same outcome the record claims (see the `acceptance:` transcripts
under `## What was done` above). Bullet 3 cannot be independently
re-derived by any method available in this session: its own acceptance
text is conditioned on the fix having landed ("after this issue lands")
and on a subsequent real merge event, neither of which has happened yet
(the `canonical:` citation above still shows `OPEN`). Reporting bullet 3
as satisfied on the strength of the implementation record's
forward-looking claim, without a real merge event behind it, would
describe something no one has actually observed happen. Per this role's
own recomputation rule (`roles/specs/execution-observation.spec.json`:
worst-case across cited results, failed > cantTell > inapplicable >
untested > passed), the frontmatter `result` reflects bullet 3 alone.

Considered and rejected: merging PR #2470 myself (with `--delete-branch`)
to force bullet 3 into an observable state this turn — rejected, since
execution-observation has no merge authority under the role-handoff
contract, and manufacturing the triggering event rather than observing
one that occurs naturally would conflate this role with the orchestrator
role bullet 3 is actually about.

## Upstream basis

- `b9656656c214a3ac802eeba32e0a605620ee1dc1:docs/issue-2451/reports/implementation.md` — the delivered work's own account; re-derived rather than cited, per this role's independent-execution mandate.
- `b9656656c214a3ac802eeba32e0a605620ee1dc1:on-the-record/directive/merge-gates.md` — the actual directive diff, read directly this turn via `git show`.
- `gh issue view 2451 --repo tokenmaxxxer/on-the-record` (read this session) — the Acceptance section's exact three bullets.
- Live `gh pr list` / `git ls-remote --heads origin` / `gh pr view 2470` queries (all this turn) — the current remote and PR state each bullet above cites.

## Open findings

canonical: `gh pr view 2470 --repo tokenmaxxxer/on-the-record --json state` (this turn) — result: `{"state":"OPEN"}`, the same transcript cited under `## What was done` bullet 3.

Acceptance bullet 3 is unobservable until PR #2470 actually merges — not
a defect, a sequencing fact (the bullet's own text is conditioned on the
issue having landed). Resolution path: a future session (execution-
observation re-run, or whichever session performs or watches the next
real `gh pr merge` after this PR lands) independently confirms that call
included `--delete-branch` and that `git ls-remote --heads origin`
no longer lists that branch immediately after. Until then this record's
overall `result` field reflects that open point, per the worst-case
recomputation rule cited under `## Why` above — this does not reopen
bullets 1 or 2, whose own executed-live transcripts under `## What was
done` independently confirm the same outcome the implementation record
claims.

## Next steps

None from this session — loop_state set to `handed-off`. Bullet 3
remains open for whichever session next observes a real post-landing
`gh pr merge` call.

acceptance: summary of the three independently-executed/observed checks above — result:
```
bullet 1 (merge-gates.md diff, --delete-branch instruction present): passed (this turn, git show against the real commit sha)
bullet 2 (backfill before/after stray count): passed — independently re-derived AFTER count = 0, matches record's claim; all 11 named branches confirmed non-open in their PR history
bullet 3 (next real gh pr merge post-landing uses --delete-branch, branch deletion confirmed): untested — PR #2470 not yet merged, no post-landing merge event exists yet to observe
overall (worst-case recomputation): untested
```
