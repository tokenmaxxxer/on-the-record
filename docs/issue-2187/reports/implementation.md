---
issue: 2187
role: implementation
loop_state: landed
upstream:
  - path: docs/issue-2187 (issue #2187 itself — no phase-1 proposal exists; contract v3 s19a build-now bypass, CORE_BUILD_NOW=1)
    sha: same-commit
  - path: on-the-record/hooks/approval-gate.sh (read in full this session)
    sha: same-commit
  - path: tokenmaxxxer-core commit f69b1cf760bdca38007135681d71a617d65552f3 (core PR #296) — read in full this session
    sha: f69b1cf760bdca38007135681d71a617d65552f3
commit_sha: same-commit
code_under_review: same-commit
type: test
breaking: false
verdict: pass
---

# issue-2187 — implementation record

## What was done

Investigated the issue's premise before writing code, per the Fix
section's own third bullet ("check whether core's and on-the-record's
approval-gate.sh are meant to be the same file... or intentionally
divergent").

canonical: `grep -n -i "OPEN\|issue_state\|IssueState\|closed\|state" on-the-record/hooks/approval-gate.sh` (this session) — result: 12 matches, none an issue-open/closed check — every hit is either a comment about the delegation feature's own "state" (e.g. "workspace state is inconsistent"), the trap's "Fails closed on any other non-0/2 exit", the `state_dir`/`OTR_ROLE_BIND_STATE_DIR` role-bind sidecar path, or `sys.stderr.write` text about "approval state" (gh/lookup failure) — no `gh issue view ... state`/`stateReason` call anywhere in the file.

That is the whole file's only code path touching GitHub issue data: it
calls `gh_json("issue", "view", str(issue), "--json", "comments", "-q",
".comments")` and nothing else — no `state`, `stateReason`, or
`closedByPullRequestsReferences` field is ever requested.

canonical: `grep -n 'FAKE_GH = \|issue.*view\|"comments"' on-the-record/hooks/test_approval_gate.py` (this session) — result: `FAKE_GH`'s stub only branches on `argv[:2] == ["issue", "view"] and "comments" in argv`, answering with `comments` alone — no `state`/`stateReason` field is modeled anywhere in this repo's own approval-gate fixture, corroborating the same file-read finding from the test side.

Fetched and read core PR #296 in full (tokenmaxxxer-core commit
`f69b1cf760bdca38007135681d71a617d65552f3`, that repo's own
docs/issue-295/reports/implementation.md — a sibling-repo path, not one
in this repo's own tree).

canonical: `cd /home/jwjung/tokenmaxxxer/tokenmaxxxer-core && git show f69b1cf` (this session) — result: that record's own "Why" section, quoted verbatim: "Diffed core's approval-gate.sh against the local clone of the sibling on-the-record repo ... The two files have completely diverged (different generations of the same hook, not a copy-paste-able shared file) — on-the-record's approval-gate.sh has no issue-open/closed precondition at all... Core's stricter behavior is real, intentional design ... not drift from a shared original — so the fix is not 'port on-the-record's gate' (that would remove the guarantee entirely, for every role) but 'teach core's gate to recognize the one case the guarantee was never meant to cover'."

Core's own author reached this same divergence conclusion independently
(that repo's own diff against this one), landed via that repo's own
build-now bypass, on the same day this issue was filed.

This also resolves an internal contradiction inside issue #2187 itself.
Its live-finding paragraph asserts on-the-record's gate blocks on
closed-issue state, citing PR #2183's survey — but that survey's own
citations, read directly, point at core's copy, not this repo's:

canonical: `gh pr diff 2183` (this session) — result: the survey's "Issue #2180's own state" section cites `sed -n '52,90p' "${CLAUDE_PLUGIN_ROOT_CORE}/hooks/approval-gate.sh"` (core's copy, deployed via the `CLAUDE_PLUGIN_ROOT_CORE` env var — the outer orchestration harness, not `on-the-record/hooks/approval-gate.sh` in this repo) as the source of the deny text "issue #2180 is not open (state: CLOSED, reason: COMPLETED) ... (contract v3 s19)".

`on-the-record/hooks/approval-gate.sh` was reached in that same live
incident too (its own, differently-worded deny appears in the survey's
"Write surface" section, over a missing-comment reason, unrelated to
issue state) — but the closed-issue-shaped deny the issue text quotes
came from core's copy.

canonical: (evidence above, this session) — given there is no closed-issue precondition in `on-the-record/hooks/approval-gate.sh` to attach an exemption to, inventing one now — a new, security-relevant behavior change that would newly deny every role's phase-2 write on every closed issue in this repo unless also exempted — would be new, undiscussed scope for a build-now delivery turn, and runs directly against core's own already-landed conclusion on this exact question.

Delivered instead the part of the acceptance criteria that is real and
checkable: added two regression tests to
`on-the-record/hooks/test_approval_gate.py` that lock in an observer
role's phase-2 record write succeeding on a subject issue shaped
exactly like #2180 (auto-closed via its implementation PR's `Closes`
trailer, no manual reopening anywhere in the test), and that a missing
Approve signal still denies that same observer role on that same
subject — the "exemption only lifts the precondition, not the approval
requirement" half of core's semantics, verified against this repo's
actual design.

Files touched: `on-the-record/hooks/test_approval_gate.py` (two new
tests plus a documentation block), this record.

## Why

Rejected reimplementing core#296's `closedByPullRequestsReferences` +
`gh pr view --json headRefName,state` logic inside
`on-the-record/hooks/approval-gate.sh` verbatim, even though the issue
text asks to "port" it. Doing so would first require inventing a
closed-issue precondition this file has never had, for every role and
every subject in this repo — real blast radius, not implied by "port an
exemption," and explicitly contrary to core's own already-landed
conclusion on this exact question (quoted above). Chose to trust the
two independent, converging primary sources — this session's own direct
read of the file, and core#296's own diff-based record — over issue
#2187's live-finding paragraph, which conflated core's deployed copy
with this repo's copy (an understandable mix-up: both plugins'
PreToolUse hooks fire together in a role session and both scripts share
the name `approval-gate.sh`, but not a fact this session's own reading
of the file supports).

## Upstream basis

- `on-the-record/hooks/approval-gate.sh` and
  `on-the-record/hooks/test_approval_gate.py` (this repo, read in full
  this session).
- tokenmaxxxer-core commit `f69b1cf760bdca38007135681d71a617d65552f3`
  (core PR #296) and its own implementation record at that commit —
  read in full this session.
- GitHub issue #2187 and PR #2183's diff (`gh pr diff 2183`), read this
  session to trace the live-finding paragraph's citations back to their
  actual source file.

## Open findings

- Issue #2187's own live-finding paragraph and core PR #296's record
  (landed the same day) draw opposite conclusions about whether
  on-the-record's gate has a closed-issue check. Resolution path: none
  needed from a future session for this issue — the evidence in the
  investigation section above resolves it in core#296's favor for this
  repo's current state, and a human reviewing this PR can act on #2187
  on that basis. If a human instead wants on-the-record's own gate to
  independently enforce a revocation-by-closing guarantee as
  defense-in-depth (a genuinely new capability, not a port), that is a
  fresh design decision deserving its own issue and its own two-phase
  proposal round, not something to fold into this build-now delivery.

## Next steps

None — `loop_state: landed` (terminal for `coding-record`, contract v3
§2).

## What did not work

None.

## Doc placement

- `docs/specs/` — not touched; no system-design change, so no
  regeneration of `docs/specs/reconciled-index.md` was needed.
- `docs/decisions/` — not touched; the investigation and its reasoning
  are scoped to this one hook/test pair and live in this record's
  rationale sections above, not a repo-wide decision.
- This record — filled the pre-written skeleton per issue #2135.

## Executed acceptance evidence

canonical: `python3 -m pytest on-the-record/hooks/test_approval_gate.py -q` (this session, baseline before adding new tests) — result: 37 passed in 1.24s, 0 failed, no SKIPPED lines.

canonical: `python3 -m pytest on-the-record/hooks/test_approval_gate.py -q` (this session, after adding `test_observer_role_record_write_succeeds_on_merge_auto_closed_issue` and `test_observer_role_still_denied_without_approve_on_closed_issue`) — result: 39 passed in 1.21s, 0 failed, no SKIPPED lines.

Hand-typed pass counts (37, then 39) match the pasted summary counts
exactly in both runs.

## Acceptance criteria (from the issue)

canonical: `python3 -m pytest on-the-record/hooks/test_approval_gate.py -q -k test_observer_role_record_write_succeeds_on_merge_auto_closed_issue` (this session) — result: 1 passed. Satisfies "an observer role's phase-2 record write succeeds on an on-the-record issue that auto-closed via its implementation PR's closing trailer, with no manual reopening" — the test reproduces issue #2180's exact role/branch/record-path shape; no reopening step exists anywhere in it.

canonical: `python3 -m pytest on-the-record/hooks/test_approval_gate.py -q -k test_observer_role_still_denied_without_approve_on_closed_issue` (this session) — result: 1 passed. This is the adjacent guarantee the gate does keep: a missing Approve signal denies an observer role exactly like any other role, on the same subject issue #2180's shape reproduces.

canonical: (evidence in the investigation section above, this session) — the issue's second acceptance line ("a closed issue still blocks non-observer roles and genuinely revoked work, regression guard, same suite") does not hold for `on-the-record/hooks/approval-gate.sh` by design: this gate has never checked issue state for any role, so a subject being in a closed state carries no distinct precondition here — the Approve-comment check is the only gate, for every role alike. See "Open findings" above for the human decision this leaves open.

- "Executed acceptance evidence in the record (#2137)" — see
  "Executed acceptance evidence" above.

skill-verdict: implementation-complexity-coupling-management — not-applicable: no coupling/cohesion metric crossed, no accessor chain, no cross-module import direction introduced.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-pattern introduction/removal decision; this turn added two test functions and investigation prose, no pattern indirection.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: no data structure, algorithm, or communication-scheme choice was made.
skill-verdict: implementation-blueprint — not-applicable: not a multi-module structural build; two additive test functions in one existing test file, no new architecture.
