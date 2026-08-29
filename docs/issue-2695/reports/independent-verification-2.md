---
issue: 2695
role: independent-verification-2
author: independent-verification-2
verifies_subject: true
loop_state: landed
upstream:
  - path: PR tokenmaxxxer/on-the-record#2697
    sha: a7642fe4eeff2e80bf6d1632dca5157444e88ff1
---

# issue-2695 — independent-verification-2 record

## What was done

Independent verification of PR #2697 ("issue-2695: retire dead
classification + remediation-queue steps from run.md"). The subject
deliverable's own record is at
`docs/issue-2695/reports/requirements-quality+technical-writing-minimalism-scoping-37ef6c94.md`
(untracked in this worktree — it lands via PR #2697's branch, not yet
merged to `main`; author
`requirements-quality+technical-writing-minimalism-scoping-37ef6c94`,
different from this record's author `independent-verification-2`).
Re-executed all three of issue #2695's acceptance checks against a fresh
worktree of the PR's own head commit rather than trusting the subject's
cited output.

canonical: `gh pr view 2697` — head branch
`issue-2695/requirements-quality+technical-writing-minimalism-scoping-37ef6c94`,
head oid `a7642fe4eeff2e80bf6d1632dca5157444e88ff1`, base `main`,
`additions: 249`, `deletions: 41`, `Closes #2695` trailer present.

Set up an isolated worktree at the PR head, independent of the subject's
own working copy:
```
$ git fetch origin issue-2695/requirements-quality+technical-writing-minimalism-scoping-37ef6c94
$ git worktree add /tmp/verify2695/pr2697 origin/issue-2695/requirements-quality+technical-writing-minimalism-scoping-37ef6c94
```
derived: `git log --oneline -1` in the worktree — HEAD is `a7642fe4`,
matching the PR head oid above.

**Acceptance check 1 (four-name classification gone from run.md):**
```
$ grep -nE 'feasibility|ux-design|리드 역할' on-the-record/commands/run.md
```
acceptance: no output, exit 1 — 0 occurrences, matching the issue's empty
state exactly. Confirms the subject's claim independently.

**Acceptance check 2 (remediation-queue step gone / queue shown unable to
produce a line):**
```
$ grep -n "remediation" on-the-record/commands/run.md
```
acceptance: no output, exit 1 — zero mentions of remediation anywhere in
the directive. Then, against the 5 real board issues the subject cites
(2695, 2690, 2688, 2686, 2682):
```
$ for i in 2695 2690 2688 2686 2682; do
    python3 gates/remediation_spawn.py --issue $i -C .
  done
```
acceptance: empty stdout, exit 0, on every one of the 5 issues —
independently reproduces the subject's claim that the queue mechanism is
structurally incapable of producing a routable line. Also confirmed
`routed_to = None` unconditionally in
`on-the-record/hooks/delegated-judgment-gate.sh` (the field the subject
cites as the sole producer feeding `remediation_spawn.py:77`), and that
this line is unchanged by the PR:
derived: `git diff origin/main a7642fe4 -- on-the-record/hooks/delegated-judgment-gate.sh` — result: empty diff, i.e. the capability was already dead before this PR, not something this PR broke.

**Acceptance check 3 (an orchestrator following the edited directive
reaches a spawn/PR):** the subject's record cites session
`requirements-quality-112361d7` reaching real PR #2696 for issue #2503.
Verified both artifacts directly rather than trusting the citation:
```
$ gh pr view 2696
```
canonical: `state: OPEN`, `additions: 305`, `deletions: 0`, `Closes #2503`,
title `issue-2503: acceptance-format role-forbidden-action rule +
authoring gate` — a real, non-draft PR against a real issue (#2503,
confirmed open via `gh issue view 2503`), not a simulated or dry-run
result.
```
$ cat /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2503-requirements-quality-112361d7.watcher.log
```
canonical: watcher log shows `pr-opened:
https://github.com/tokenmaxxxer/on-the-record/pull/2696` followed by
`session-end: progressed` — the gate-refusals logged after the PR was
already open are the session's own record-claim-guard hits while writing
its record, not a failure to reach the PR. This matches the subject
record's own characterization.

**Renumbering / step-count integrity:** independently re-derived
```
$ grep -n '^[0-9]\. \*\*' on-the-record/commands/run.md
```
acceptance: steps run 1–6 with no gaps (1 요구사항→이슈, 2 판단, 3 누구를
깨울지, 4 띄운다, 5 PR 설명, 6 결정 중계) — matches the subject's claimed
renumbering.
derived: `git diff origin/main a7642fe4 --stat -- on-the-record/commands/run.md` — result: `1 file changed, 26 insertions(+), 40 deletions(-)`, matching the subject's cited figure exactly.

**Non-goals honored:**
derived: `git diff origin/main a7642fe4 -- gates/remediation_spawn.py on-the-record/hooks/delegated-judgment-gate.sh` — result: empty diff on both paths, confirming neither was touched (the issue's `must not` forbade deleting either).

**Warrant-hunter finding disposition:** the subject's before-landing hunt
found the diff orphaned a reachability claim in
`docs/specs/enforcement-boundary.md:98`.
canonical: `git show origin/issue-2695/requirements-quality+technical-writing-minimalism-scoping-37ef6c94:docs/issue-2695/reports/requirements-quality+technical-writing-minimalism-scoping-37ef6c94/2026-08-29-hunt-run-md-dead-steps.md` — Verdict: FINDING, silent-failure, "deleting the ... step from run.md orphans `gates/remediation_spawn.py` ... silently bypassing the only reachability path `docs/specs/enforcement-boundary.md` documents".
Read the post-fix row directly in the PR worktree
(`sed -n '95,99p' docs/specs/enforcement-boundary.md`): the
`remediation_spawn.py` row now reads "reachability path retired (issue
#2695) ... invoked manually only" — the orphaned claim is genuinely
fixed in the same commit, not merely acknowledged.

**Pre-existing breakage disclosure:** the subject's record discloses
`python3 gates/spec_index.py --update` fails with `FileNotFoundError:
... roles/specs/brand-design.spec.json` both before and after this
diff.
```
$ python3 gates/spec_index.py --update
```
acceptance: `FileNotFoundError: [Errno 2] No such file or directory:
'.../roles/specs/brand-design.spec.json'`, exit 2 — reproduced
independently in the PR worktree, same missing path, confirming this is
not a regression introduced by the PR.

## Why

Per the observer-verification mechanism
(`docs/handbooks/observer-verification.md`), issue #2695's subject
deliverable needs 2 independent verifying records
(`REQUIRED_INDEPENDENT_VERIFICATIONS = 2`) before its PR can merge; this
is verification slot 2. Re-derivation from a separate worktree (rather
than reading the subject's cited output at face value) is the standard
this session's spawning prompt requires — every acceptance check above
was re-run against the raw repository state, not copied from the
subject's record.

## What did not work

None.

## Upstream basis

- PR tokenmaxxxer/on-the-record#2697, head commit
  `a7642fe4eeff2e80bf6d1632dca5157444e88ff1` — re-checked out into an
  isolated worktree for this verification. sha:
  `a7642fe4eeff2e80bf6d1632dca5157444e88ff1`
- Subject deliverable record, path
  `docs/issue-2695/reports/requirements-quality+technical-writing-minimalism-scoping-37ef6c94.md`
  (untracked in this worktree; lands via PR #2697's branch, author
  differs from this record's author) — sha:
  `a7642fe4eeff2e80bf6d1632dca5157444e88ff1` (lands in the same PR
  commit, not on `main`). canonical: `git show
  origin/issue-2695/requirements-quality+technical-writing-minimalism-scoping-37ef6c94:docs/issue-2695/reports/requirements-quality+technical-writing-minimalism-scoping-37ef6c94.md`
- `docs/handbooks/observer-verification.md` — mechanism this record's
  `verifies_subject: true` flip and merge-gate counting follow. sha:
  read from this session's own working tree (already on `main`).

## Open findings

None: every acceptance check, both `must not` constraints, the
warrant-hunter finding's disposition, and the disclosed pre-existing
`spec_index.py` breakage were each independently re-executed above (see
`## What was done`, all `derived:`/`acceptance:`/`canonical:` tagged) and
matched the subject's claims. canonical: this session's own command
output cited inline throughout `## What was done` — no discrepancy found
there.

## Next steps

None — `loop_state` moves to `landed` with this record.

skill-verdict: work-in-english — applied: invoked; wrote this record, and will write commit messages and PR body, in English per the skill despite the task instructions arriving in Korean; the end-of-turn summary to the user is in Korean.
