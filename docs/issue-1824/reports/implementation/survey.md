# Survey — issue #1824: rsb data path (gates/flows.py) dual-read

## Scope read

`gates/flows.py` (554 lines), `spawn.py` role/approval helpers it calls,
`test/test_convention_equivalence.py`
(`RsbStatusBoardEquivalenceTest`, `BranchRoleFieldDualReadEquivalenceTest`),
and the two prior phase-5 landings this issue depends on: #1814 (PR-body
`role:` trailer + `.on-the-record/role.json` sidecar) and #1818 (structured
approval record at `.git/gh-read-cache/issue-<n>-approvals.json`, read at
gates/ci.py:212-254).

## 1. `_BRANCH_RE` (flows.py:32) — already migrated, not a remaining site

canonical: gates/flows.py:39-49 (`_role_from_pr`), gates/flows.py:336-338
(`pr_by_branch` build loop), test/test_convention_equivalence.py:403-441
(`BranchRoleFieldDualReadEquivalenceTest`) — read this session.

`_BRANCH_RE` itself (the subject-group regex) is unchanged in this issue's
scope per the frozen migration order (entry 3, board-records-derived,
non-goal). What issue #1814 already migrated is the *role* extraction that
rides on top of a `_BRANCH_RE` match: `_role_from_pr()`
(flows.py:39-49) prefers the PR body's `role:` trailer over
`branch_match.group(2)`, falling back to the branch group when the trailer
is absent or the body isn't a string. The one call site building
`pr_by_branch` (flows.py:336-338) already routes through `_role_from_pr`,
not a raw `branch_match.group(2)` read. `BranchRoleFieldDualReadEquivalenceTest`
(test/test_convention_equivalence.py:403-441) already pins this
dual-read/fallback pair.

Conclusion: no remaining branch/role site in flows.py — #1814 covered it
completely. This issue's write set does not need to touch `_role_from_pr`
or `_BRANCH_RE`.

## 2. `_pr_approved()` (flows.py:175-188) — the one remaining site

canonical: gates/flows.py:175-188 (`_pr_approved` body), gates/flows.py:390-402
and gates/flows.py:404-423 (its two call sites), gates/ci.py:189-254
(`_read_approval_record`, `_write_approval_record`, `_approved_roles_on_issue`)
— read this session.

```
def _pr_approved(pr: dict, comments: list[dict], approvers: set[str],
                 subject: str, role: str) -> bool:
    needle = f"APPROVE {subject}/{role}"
    if any(c["body"].strip() == needle and c["login"] in approvers for c in comments):
        return True
    for rv in pr.get("reviews") or []:
        if (rv.get("state") == "APPROVED"
                and (rv.get("author") or {}).get("login") in approvers):
            return True
    return False
```

Two call sites, both in `flows_payload()`: flows.py:394 (inside the
`decision_queue` loop, per PR keyed by `(subject, role)` from
`pr_by_branch`) and flows.py:418 (inside the `unapproved_open_prs` loop,
per role entry with an associated PR). Both already have `comments`
(fetched per-issue/PR via `comments_for()`, flows.py:351-366) and
`approvers` (`spawn._approvers`, flows.py:316) in hand; neither reads the
#1818 structured approval record today.

canonical: gates/ci.py:212-254, read this session — `_approved_roles_on_issue`
is the existing #1818 consumer pattern to mirror. It reads
`spawn._approval_record_path(repo, issue)` via `_read_approval_record`
(gates/ci.py:189-201, fail-open on a missing/corrupt/wrong-type record
file, canonical: gates/ci.py:189-201 read this session), unions the role
tokens found there with a fresh comment-needle scan (the scan always
still runs — the record is a cache, not authoritative), and write-throughs
any newly-scanned role back into the record. Its own docstring
(gates/ci.py:216-219) states it does not reuse, and is not reused by,
`flows._pr_approved` — that function is issue-level/any-role,
`_pr_approved` is role-exact plus a PR-review-Approve path the record does
not carry (the record only captures the `APPROVE issue-<n>/role` comment
form per gates/ci.py:238-250, not `pr["reviews"]` state).

That contract mismatch means `_pr_approved` cannot call
`_approved_roles_on_issue` directly; the dual-read has to be a
same-shaped construction inside `_pr_approved` itself: read the record via
`_read_approval_record`, check `role in record` (a hit means that role was
already scanned/approved for this issue — treat as `True` without
requiring the needle scan to also match, mirroring
`_approved_roles_on_issue`'s own record-then-scan order but scoped to one
role), and leave the PR-review-Approve loop untouched (no #1818 carrier
covers it).

The record read needs an issue number, not the `subject` string
(`"issue-<n>"`) `_pr_approved` currently takes. Both call sites already
derive `issue_n = int(subject.split("-", 1)[1])` in scope before calling
`_pr_approved` (flows.py:391, flows.py:405) — the same idiom flows.py
already uses at flows.py:352. Deriving `issue_n` the same way inside
`_pr_approved` from its existing `subject` parameter avoids adding a 6th
parameter or touching either call site's argument list.

canonical: gates/ci.py:1-40, read this session — imports `spawn` and
stdlib only, no import of `flows`. Importing `gates.ci._read_approval_record`
from gates/flows.py introduces no circular import on that evidence.

## 3. `spawn._front_role()` dependency (flows.py:413) — confirmed no change needed

canonical: gates/flows.py:413-414 (call site), spawn.py:1513-1526
(`_front_role` body), spawn.py:1496-1510 (`_record_upstream`) — read this
session.

```
if spawn._front_role(root, subject, roles) == role:
    stage_source = loop_state
```

`_front_role()` (spawn.py:1513-1526) determines which role's `loop_state`
drives the subject's overall `stage` in the flows payload. Its body does
not parse role or approval state from any of the three migrated/migrating
carriers (branch names, APPROVE grammar, approval records): it walks
`roles` (already a dict of role → frontmatter dict, sourced from board
records — migration-order entry 1, marked unchanged, zero parse sites per
docs/issue-1792/reports/implementation.md:98-100) and calls
`_record_upstream()` (spawn.py:1496-1510), a frontmatter `upstream:` block
reader unrelated to any of the 6 convention consumers' carriers. Its
fallback ("관례 순서 product, 아니면 feasibility") is a literal role-name
list, not a parsed value.

canonical: docs/issue-1792/reports/implementation.md:132-134, read this
session — the migration-order note there flags `_front_role()` only as
cross-module coupling ("a cross-module dependency on consumer 4's
module"), i.e. flows.py reaching into spawn.py at all, not as a
role/approval-derivation site itself. Consumer 4 (APPROVE grammar) is
`_pr_approved`, covered in finding 2; `_front_role` is unrelated to it
beyond living in the same module.

Conclusion, on the code read above: `_front_role()` gets no dual-read
change in this issue's write set — it already reads board records only
(entry 1, frozen as unchanged per this issue's own text: "board records'
`ROLES`-tuple membership (entry 1, unchanged)").

## Test file survey

canonical: `find test -iname "*flows*"` (run this session) returned only
test/test_convention_equivalence.py.

- test/test_convention_equivalence.py (445 lines): `RsbStatusBoardEquivalenceTest`
  (lines 360-393) already golden-pins `_pr_approved`'s needle-only shape
  (`test_pr_approved_needle_shape`, `test_pr_approved_rejects_role_mismatch`)
  and `_BRANCH_RE` (`test_branch_re_extracts_subject_and_role`) — the
  no-carrier-present cases the dual-read must stay byte-identical against
  (both tests construct `_pr_approved` calls with no approval-record file
  on disk, so a fail-open empty-record read reproduces today's result
  unchanged). `BranchRoleFieldDualReadEquivalenceTest` (lines 403-441)
  already pins the #1814 role-trailer dual-read — nothing to add there
  per finding 1.
- a new test/test_flows_role_field.py file is not present on disk (the
  `find` command above is the check); this issue's acceptance §2 names it
  as a required new file, covering carrier-read, fallback, and the
  no-carrier legacy case (byte-identical `flows_payload()` output).

## Prior-issue proposal shape reused

canonical: docs/issue-1821/proposals/approval-gate-dual-read.md, read this
session. That file (issue #1821, entry 5 of the same migration order) is
the closest precedent: same dual-read/fallback shape against the same
#1818 carrier this issue also reads. Its section order — files, Request,
Constraints, Rationale with a rejected alternative, a build-steps section,
Out of scope, and a closing verification section — is the template this
issue's proposal follows.

## Dependency / ordering facts carried forward

- #1814 (role trailer + sidecar): flows.py's `_role_from_pr` already
  consumes it (finding 1) — no new work in this issue.
- #1818 (structured approval record): gates/ci.py is the only current
  reader (`_approved_roles_on_issue`); `_pr_approved` in flows.py is the
  new reader this issue adds, mirroring the same fail-open record-read
  shape but scoped to a single role instead of an issue-wide union
  (finding 2).
- canonical: spawn.py:1513-1526, read this session. `_front_role()` has no
  carrier dependency on this evidence (finding 3).
- Non-goal per the issue text: dropping the regex/needle copies entirely
  (final-removal cycle, out of scope here).
