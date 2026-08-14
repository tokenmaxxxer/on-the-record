---
subject: issue-443
role: execution-observation
observed_role: implementation
observed_pr: 447
observed_commits:
  - 8e7d1b4  # phase 1 — survey + proposal
  - b73b502  # phase-1 warrant-hunter record, no finding
  - 01a2c9d  # phase 2 — contract-guard.sh fix, test_contract_guard.py, record
observed_merge: 6d058ff
loop_state: terminal
---

# Execution-observation record — issue #443, step 2

## Independence

This role did not author, edit, or in any way participate in producing
the artifacts it judges here. canonical: git show --stat 01a2c9d, quoted
below under "Evidence read this session" — the `implementation` role, on
branch `issue-443/implementation`, wrote
`on-the-record/hooks/contract-guard.sh`,
`on-the-record/hooks/test_contract_guard.py`,
`docs/issue-443/reports/implementation.md`, and a hunt record, landed to
`main` before this session began. Nothing under those paths was modified
by this session. `pytest` was not run against `test_contract_guard.py` or
any other suite this session, and `contract-guard.sh` was not invoked —
CI's own suite-green run on PR #447 is used as evidence below, not a
local re-run, per canonical: docs/issue-443/reports/execution-observation/survey.md,
"No re-execution" paragraph — this role's own phase-1 artifact, read in
full this session. This session's write set is this record only.

This statement precedes every verdict-bearing sentence below.

## What was done

This session re-read `01a2c9d`'s diff and the delivered
`test_contract_guard.py` directly from git this turn (not the working
tree) to independently verify the two facts phase-1's survey had flagged
but not judged, then rendered the three-level verdict below. `gh`
GraphQL access was rate-limited for part of this session (`gh api
rate_limit --jq .resources.graphql` returned `"remaining":0` mid-session);
issue/PR metadata already captured in the phase-1 survey with its own
citations is carried forward from that file below and marked as such,
rather than re-fetched.

## Evidence read this session

```
$ git show --stat 01a2c9d
commit 01a2c9d2c40a8aa9c240c57edbd33decfd849f0f
 docs/issue-443/reports/implementation.md           |  98 +++++++++
 ...8-hunt-contract-guard-target-repo-resolution.md |  57 ++++++
 on-the-record/hooks/contract-guard.sh              |  69 ++++++-
 on-the-record/hooks/test_contract_guard.py         | 220 +++++++++++++++++++++
 4 files changed, 434 insertions(+), 10 deletions(-)
```

```
$ git log --oneline 8e7d1b4^..01a2c9d
01a2c9d2 feat(issue-443): contract-guard target-repo PR resolution
b73b5022 docs: warrant-hunter record for issue-443 phase-1 (no finding)
8e7d1b46 docs(issue-443): phase 1 — survey + proposal for contract-guard target-repo resolution
```

```
$ git show 01a2c9d:on-the-record/hooks/test_contract_guard.py | grep -n "^def "
50:def _write_fake_gh(bin_dir: Path):
57:def _approve_comment(issue, login):
61:def _run_guard(cmd, fixtures, tmp_path, cwd=None):
80:def _repo_dir(tmp_path, name, approvers):
89:def test_cross_repo_same_number_judges_target_not_cwd(tmp_path):
114:def test_repo_flag_targets_repo_but_no_local_approvers_is_unreached(tmp_path):
129:def test_full_pr_url_targets_repo_but_no_local_approvers_is_unreached(tmp_path):
147:def test_cd_prefix_reads_target_approvers_and_denies(tmp_path):
164:def test_cd_prefix_allows_when_target_pr_closes_issue(tmp_path):
180:def test_repo_flag_overrides_cd_prefix_when_they_disagree(tmp_path):
207:def test_no_repo_indicator_unchanged_cwd_behavior(tmp_path):
```

Plus the full text of `01a2c9d`'s `contract-guard.sh` diff (read via `git
show 01a2c9d -- on-the-record/hooks/contract-guard.sh`, quoted piecemeal
under Checks below), `docs/issue-443/proposals/2026-08-08-contract-guard-target-repo-resolution.md`,
`docs/issue-443/reports/implementation.md`, this role's own phase-1
`docs/issue-443/reports/execution-observation/survey.md`, and this role's
own approved
`docs/issue-443/proposals/2026-08-08-execution-observation-of-pr-447.md` —
all read in full this session.

Deliberately **not** read as evidence: the current working-tree copy of
`contract-guard.sh` or `test_contract_guard.py`. Both were read at the
`01a2c9d` commit object directly, the admissible post-merge form,
regardless of what the working tree presently contains.

## Checks

### Outcome — against issue #443's three requirements

Requirement text is carried forward from the phase-1 survey's issue read,
canonical: docs/issue-443/reports/execution-observation/survey.md, "What
was read this session," first bullet (`gh issue view 443` full body) —
this role's own phase-1 artifact, and from the approved proposal's
paraphrase quoting acceptance criterion 1 verbatim ("식별 불가 형태는
현행 fail-open 주석 관례대로 명시적 unreached 로 남긴다").

**요구사항 1 (target-repo resolution) is present.** The `01a2c9d` diff to
`contract-guard.sh` adds a `-R`/`--repo` regex, a full-PR-URL regex, and a
`cd <path> &&` prefix regex, each routed to its own branch:

```
+url_m = re.search(r"github\.com/([^/\s]+/[^/\s]+)/pull/(\d+)", rest)
+repo_flag_m = re.search(r"(?:-R|--repo)[= ]([^\s/]+/[^\s/]+)", rest)
+
+if url_m:
+    pr = url_m.group(2)
+    target_cwd = None
+    target_repo_flag = url_m.group(1)
+elif repo_flag_m:
+    ...
+    target_repo_flag = repo_flag_m.group(1)
```

and the unresolvable forms hit an explicit unreached exit:

```
+if target_repo_flag and target_cwd is None:
+    sys.exit(0)
```

with a comment naming the reason — matching acceptance criterion 1's
disjunction. canonical: git show 01a2c9d -- on-the-record/hooks/contract-guard.sh,
read in full this session.

**요구사항 2 (red-green cross-repo case in a gate test suite) is present,
with one documentation gap.** `01a2c9d:on-the-record/hooks/test_contract_guard.py`
defines `test_cross_repo_same_number_judges_target_not_cwd` as one of 7
`def test_*` functions `derived: git show 01a2c9d:on-the-record/hooks/test_contract_guard.py | grep -c "^def test_"`
(output: 7, quoted above under "Evidence read this session"). CI's own
run reported the suite green on PR #447 (`gh pr checks 447` output `test
pass 27s`), carried forward from canonical: docs/issue-443/reports/execution-observation/survey.md,
`gh pr checks 447` citation. The suite is a dedicated
`test_contract_guard.py`, the second option of acceptance criterion 1's
disjunction ("`test_gates.py` 또는 contract-guard 전용 스위트") — that
disjunct is satisfied. The documentary gap is F1 below.

**요구사항 3 (new URL-form parsing kept consistent with existing unreached
comments) is present.** The new `sys.exit(0)` branches carry inline
comments in the same voice as the pre-existing unreached branch beside
them, and that pre-existing branch's own code has no `+`/`-` line against
it anywhere in the diff. canonical: git show 01a2c9d -- on-the-record/hooks/contract-guard.sh,
read in full this session.

**Constraints held.** The `Closes #<issue>` predicate block
(`closes_m`/`plain_refs`/`issue` extraction) sits below the diff's last
hunk and has no `+`/`-` line against it anywhere in the diff. No new
import is added (the diff's only names are `re` functions already
imported at the top of the file); the `-R`/URL-with-no-checkout path
stays fail-open rather than fetching `approvers.md` over the GitHub
contents API, matching the proposal's Rationale section, which rejects
that option, and the Constraints section's zero-install requirement.
canonical: git show 01a2c9d -- on-the-record/hooks/contract-guard.sh,
read in full this session.

### Trajectory — against contract v3 s19

canonical: git log --oneline 8e7d1b4^..01a2c9d, quoted above under
"Evidence read this session" — the commit order is `8e7d1b4` (phase 1:
proposal + survey), then `b73b502` (phase-1 warrant-hunter record, no
finding), then `01a2c9d` (phase 2: fix + test + record), independently
checked this session. The approval-comment text and exact timestamps
(`APPROVE issue-443/implementation` by `JiwonJung94`, 2026-08-08T08:12:56Z,
sitting between `b73b502` at 08:12:42Z and `01a2c9d` at 08:20:09Z) are
carried forward from canonical: docs/issue-443/reports/execution-observation/survey.md,
"What was read this session" — this role's own phase-1 artifact, not
re-fetched this session because `gh` GraphQL was rate-limited; the
commit-order check above is independently consistent with that account.
PR #447's `reviews: []` state is per the same survey citation, the
single-account path contract v3 s19 allows. The trajectory holds up on
the evidence available this session.

### Step — per artifact

`docs/issue-443/reports/implementation.md`'s test-count and red-run
sentences are the one deficient span this session located;
`contract-guard.sh`'s diff and `test_contract_guard.py` itself hold up on
the checks run this session.

## Verdicts

### Outcome — present, no functional qualification

PR #447 shipped all three of issue #443's requirements and the stated
constraints, per the Checks above, each with an adjacent citation to the
`01a2c9d` diff read this session. The one deficiency this session located
(F1) is in the implementation record's own prose, not in the shipped hook
or test behavior.

### Trajectory — sound

Survey and proposal preceded a real human approval from an
`approvers.md`-listed account, and phase-2 delivery followed it, per
canonical: git log --oneline 8e7d1b4^..01a2c9d (this session's own read,
quoted above) plus the phase-1 survey's citation for the approval text
and timestamps.

### Step — one deficient artifact

`docs/issue-443/reports/implementation.md` (F1). `contract-guard.sh` and
`test_contract_guard.py` hold up on the checks run this session.

## Findings

### F1 — the implementation record's test-count sentence and its red-run pointer don't match the delivered file

**Impact.** `docs/issue-443/reports/implementation.md`, line 31, states a
case count for `test_contract_guard.py` that does not match the delivered
file: `derived: git show 01a2c9d:on-the-record/hooks/test_contract_guard.py | grep -c "^def test_"`
returns 7 (quoted above under "Evidence read this session"), one short of
what that line states. The same file's lines 32-33 point to a red-run
transcript with "— see below", but no transcript, `git stash` output, or
failure text appears anywhere else in that record — checked by reading
the file's full text this session, canonical: docs/issue-443/reports/implementation.md,
read in full this session. Neither defect changes what shipped — the test
suite itself is real and CI reported it green per the `gh pr checks 447`
citation carried forward above — but a reader relying on the record's own
account cannot independently verify the case count or the red-green claim
from the record text alone.

**Timeline.** Both lines were authored in `01a2c9d`, the same commit that
added the test file they describe.

**Root cause.** The record's count and the red-run claim read as written
from recollection rather than copy-checked against the delivered file or
a saved transcript at write time — a one-off slip, not an established
pattern (the only implementation record this role has observed to date).

**Action item (for the human to judge; this role files nothing).** A
follow-up could correct the count sentence at line 31 to match the
delivered file and either paste the actual red-run output below the claim
at lines 32-33 or drop the "see below" clause if no transcript was saved.
Low priority: it does not affect the shipped fix or the test suite's own
correctness, and this role's own inspection ceiling (no re-execution)
means it cannot itself distinguish "the red-run happened but wasn't
transcribed" from "the claim is inaccurate" — only that the record does
not let a reader tell the two apart.

## Open findings

F1 is open as of this record. Not fixable by this role: the
implementation record is `issue-443/implementation`'s own artifact,
outside this role's approved write set (its sole write target is this
record).

## Next steps

None for this role. Step 2 of issue #443's execution plan is delivered by
this record; all three verdict levels are answered above with citations,
and all three candidate discrepancies the phase-1 survey flagged are
resolved — the first two fold into F1, the third (dedicated test module
vs. `test_gates.py` addition) is checked and clear under "요구사항 2"
above.

## Open-finding resolution path

The human judges F1 on this role's PR. Under contract v3 issues are
user-authored only, so this role files nothing and edits nothing of the
observed artifacts; if the human judges F1 valid, they file it and it
enters the board as its own subject.
