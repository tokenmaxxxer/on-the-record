# Issue #587 step 3 — e2e fixture-target-repo drive (phase 2)

Driver: a disposable script under this session's scratchpad
(/tmp/claude-*/…/scratchpad/e2e/drive.py, never committed — matches the
proposal's declared write set). It builds a fresh temp-dir git repo per
scenario (never this repo's board), seeds two fixture-internal role
specs (fixture-only roles/architecture.json: write_scope
["docs/decisions/*.md", "docs/issue-<n>/reports/architecture.md"],
judgment_axes ["maintenance_complexity"]; fixture-only roles/coding.json:
write_scope ["src/*.py"]), stubs gh to log every call to a file instead
of touching the network, and invokes the shipped, unmodified
on-the-record/hooks/delegated-judgment-gate.sh (commit a5029be, same as
merged in PR #595) exactly as the "gh pr create" PreToolUse hook would,
plus the shipped, unmodified gates/remediation_spawn.py with its real
(non-mocked) "_branch_exists"/"_pr_already_launched" against the
fixture's own git state — not the mocked unit-test path in
gates/test_remediation_spawn.py.

All file names quoted below with a leading "fixture:" marker are paths
written inside the disposable fixture temp-dir this run created and tore
down — they are not paths in this repository.

## Scenario A — reject to remediation to spawn-task to merge to closure (fixture issue 42)

### Step 2 — drive to reject with a routable finding

Command: bash on-the-record/hooks/delegated-judgment-gate.sh, payload
"gh pr create ... --number 101". Result: exit 0.

Captured gh.log:

> issue comment 42 --body Judgment opened: PR #101 -- candidate decision
> on branch issue-42/architecture (1 path(s) changed) entered
> delegated-judgment evaluation.
>
> pr comment 101 --body ### Delegated judgment: auto-1 -- reject
> (architecture / maintenance_complexity / contradicts)
>
> issue comment 42 --body Verdict: PR #101 -> reject. Audit record:
> fixture:docs/issue-42/decisions/auto-1.md
>
> pr comment 101 --body ### Remediation routed: round 1. Finding from
> fixture:docs/issue-42/decisions/auto-1.md routed to coding (owns
> fixture:src/foo.py via write_scope).
>
> issue comment 42 --body Remediation round 1: PR #101's finding ->
> coding. Remediation record: fixture:docs/issue-42/decisions/remediation-1.md

fixture:remediation-1.md written: routed_to coding, target_path
fixture:src/foo.py, round 1, status open. Events 1 (Judgment opened), 2
(Verdict synthesized), 3 (Remediation routed) all fired in this one run.

### Step 3 — real remediation_spawn.py against the fixture

Command: python3 gates/remediation_spawn.py --issue 42 -C <fixture>.
Result: exit 0. stdout:

> coding [tab] Remediation round 1: fix fixture:src/foo.py -- add null
> check (routed from fixture:docs/issue-42/decisions/remediation-1.md,
> finding: fixture:docs/issue-42/decisions/auto-1.md)

Exactly one task, template-derived from the fixture remediation-1.md's
own fields (matches gates/remediation_spawn.py's _TASK_TEMPLATE constant
verbatim) — never free-authored.

### Step 5a — re-run the gate on PR #101 after the finding is resolved

Architecture's fixture record flipped to supports; re-run. Result: exit
0. gh.log gained: "Judgment opened: PR #101 -- ... (5 path(s) changed)
...", "Delegated judgment: auto-2 -- approve", "Verdict: PR #101 ->
approve. Audit record: fixture:docs/issue-42/decisions/auto-2.md".
Closure confirmed.

### Step 4 — simulate the remediation PR and merge it (fresh issue-42/coding branch off main)

Command: bash on-the-record/hooks/delegated-judgment-gate.sh, payload
"gh pr create ... --number 102". Result: exit 0. gh.log gained:
"Judgment opened: PR #102 -- candidate decision on branch
issue-42/coding (2 path(s) changed) entered delegated-judgment
evaluation.", "Verdict: PR #102 -> escalate (depth or impact axis did
not clear)".

(PR #102 itself escalates rather than approves — the fixture's own
product-priorities corpus was never seeded to mention fixture:src/foo.py's
basename, so its own depth axis never clears. This is a fixture-setup
artifact, not a defect in the observed code — PR #102 was never meant to
be judged, only merged, to observe the merge-detection channel.)

Then: git checkout main && git merge --no-ff issue-42/coding -m "merge
remediation".

No gh call was made by this plain git merge — gh.log gained zero new
lines from it. Searched the entire shipped surface
(on-the-record/hooks/delegated-judgment-gate.sh, spawn.py) this session
via grep -rn -i "Remediation merged|resolves round" --include=*.py
--include=*.sh . : zero matches anywhere in tracked code. spawn.py's
only merge-adjacent reader, _pr_open_or_merged_for_branch (spawn.py line
1082), feeds board()/reconcile() state for spawned role sessions — it
never posts an issue-timeline comment shaped like the architecture
proposal's event-4 template (docs/issue-587/proposals/architecture.md
line 401: "Remediation merged: PR #<m> resolves round <r> of PR #<n>").
Event 4 (Remediation PR merged) does not fire — confirmed both by
absence in the shipped source this session read and by the empirical
drive producing no such comment.

## Scenario B — 4 rejection rounds to escalation (fixture issue 43)

Same fixture shape, required_fix varied each round (a genuine new
attempt each time, so the round bound — not the repeat-contradiction
check — is what exhausts it, per the comment in
on-the-record/hooks/delegated-judgment-gate.sh at that branch). Four
consecutive gate runs on PR #201, one per round:

round 1: reject, fixture:remediation-1.md round 1 status open
round 2: reject, fixture:remediation-2.md round 2 status open
round 3: reject, fixture:remediation-3.md round 3 status open
round 4: reject, fixture:remediation-4.md round 4 status escalated

gh.log gained on round 4: "### Escalated to operator.
fixture:docs/issue-43/decisions/auto-4.md chain, round 4 -- round
exhausted.", "Escalated: PR #201, round 4 -- round exhausted."

Event 5 (Escalation to operator) fired: fixture remediation-4.md carries
status escalated, round 4.

## Per-event table (derived from the fenced runs above)

| # | Event | Fired | Evidence (this file, section above) |
|---|---|---|---|
| 1 | PR opened under judgment | yes | Scenario A step 2 |
| 2 | Verdict synthesized | yes | Scenario A step 2 (reject) and step 5a (approve) |
| 3 | Remediation routed | yes | Scenario A step 2 |
| 4 | Remediation PR merged | no | Scenario A step 4 |
| 5 | Escalation to operator | yes | Scenario B |

Every event except event 4 fired on the shipped, unmodified code driven
against a real fixture repo, per the five rows above.
