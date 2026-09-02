# Requirements Registry

Append-only. Each entry records one requirement in the operator's own words,
the issue it came from, and the executable artifact that fails if the
requirement's enforcement regresses. Do not edit or remove existing entries
— only append new ones, or update `status` on an existing entry.

Fields:
- `quote`: the operator's verbatim words (Korean or English, unedited).
- `source_issue`: the GitHub issue number the quote came from.
- `check`: `path/to/file.py::name` of the executable artifact that fails on
  regression, or the literal `UNVERIFIABLE: <reason>` when genuinely not
  mechanically checkable (per #310's precedent for stating that plainly).
- `status`: `open` | `enforced` | `stale`. `stale` is computed by
  `gates.requirement_registry`; `open`/`enforced` are set by whichever
  role discharges or re-checks the requirement.

`gates.requirement_registry` (wired into `gates/ci.py`) fails the check for
any entry whose `check` path no longer exists at HEAD — a requirement
quietly losing its enforcement as the codebase moves.

## R001

quote: 기록이 많아짐으로써 사용자가 핵심으로 제시하는 요구사항들이 희석되는 문제 (requirements dilute as the record grows)
source_issue: 321
check: gates/gates.py::requirement_registry
status: enforced

## R002

quote: Consumers file ISSUES ONLY — never PRs. The channel must not offer, scaffold, or allow an upstream PR path from consumer sessions.
source_issue: 1131
check: UNVERIFIABLE: gates/test_upstream_finding_channel.py was deleted when the plugin's own pytest suite was retired (#2137 — persistent test files are not a default deliverable); no replacement test file was reintroduced per that policy
status: enforced

## R003

quote: Filing happens only with user confirmation in the consumer session — no silent auto-submission.
source_issue: 1131
check: UNVERIFIABLE: gates/test_upstream_finding_channel.py was deleted when the plugin's own pytest suite was retired (#2137 — persistent test files are not a default deliverable); no replacement test file was reintroduced per that policy
status: enforced

## R004

quote: If the upstream repo is unreachable (permissions/network), the draft is saved to the consumer repo's docs/upstream-findings/ and reported.
source_issue: 1131
check: UNVERIFIABLE: gates/test_upstream_finding_channel.py was deleted when the plugin's own pytest suite was retired (#2137 — persistent test files are not a default deliverable); no replacement test file was reintroduced per that policy
status: enforced

## R005

quote: a PR is refused when merging it would delete or overwrite content that exists at the base branch HEAD but was added by a commit the PR's merge-base does NOT contain (i.e. the PR is stale relative to that commit and its merge reverts it)
source_issue: 1664
check: gates/stale_revert_guard.py::classify
status: enforced

## R006

quote: Dominant-axis rule: no summing/averaging across axes; worst reversibility grade alone forces individual human approval.
source_issue: 511
check: gates/risk_report.py::classify_axes
status: enforced

## R007

quote: A consumer session working on a target repo must use the mounted methodology skills so that they actually change the deliverable — selected to fit the task, opened before the work they are meant to guide, combined when more than one applies, and demonstrably better than the same session without them.
source_issue: 3041
check: scripts/issue-3041/run_pair.sh + evaluate_pair.py — MEASURED ONCE, ON A FLOOR CONDITION, RESULT INDISTINGUISHABLE. Issue #3053's corrected run (PR #3074) verified the mount in 4 of 4 skills-on arms and recorded 8 skill opens against 0 in the skills-off arms, closing the zero-mount confound that invalidated the first attempt. Deliverable scores: skills-on won 2 of 4 blind pairs, tied 1, lost 1; combined 35 vs 34, inside the pre-registered +/-3 threshold, so no quality difference was detected. BOUND: both arms launched `claude -p` directly, with no orchestrator and no --skills argument. That is a bare session with a reachable corpus, not the consumer path, which runs an on-the-record orchestrator selecting skills via spawn.py. The consumer-path comparison — both arms through spawn.py, differing only in whether the skill layer is available — has not been run. Separately measured on that path: orchestrator-named skills opened 4 of 4 at 12-16% of the tool sequence, against 0.36-0.83 on the floor condition.
