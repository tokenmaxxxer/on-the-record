---
status: proposed
files:
  - gates/flows.py
  - test/test_convention_equivalence.py
  - test/test_flows_role_field.py
---

## Request

Issue #1824 (frozen migration order entry 6, docs/issue-1792/reports/
implementation.md §Migration order — the last consumer before the
final-removal cycle): `gates/flows.py` still derives PR approval state
via its own from-scratch `_pr_approved()` needle scan, never touching the
#1818 structured approval record (`.git/gh-read-cache/issue-<n>-approvals.json`).
Migrate `_pr_approved()` to prefer that record, falling back to today's
needle/PR-review scan exactly as now when the record has no entry for the
role — identical `flows_payload()` output on both paths, per the issue's
requirement 1.

## Constraints

- `test/test_convention_equivalence.py` (survey: currently pins
  `_pr_approved`'s needle-only shape at
  `RsbStatusBoardEquivalenceTest.test_pr_approved_needle_shape` and
  `test_pr_approved_rejects_role_mismatch`, lines 366-378) stays green
  with additions only — no edits to existing golden cases (acceptance §1).
- `flows_payload()` output must be byte-identical between the
  record-carrying path and the fallback path on the golden samples, and
  byte-identical to today when no carrier is present (acceptance §2).
- The PR-review-Approve loop in `_pr_approved` (the `for rv in
  pr.get("reviews")` branch) is untouched — the #1818 record only ever
  captures the `APPROVE issue-<n>/role` comment form (survey finding 2),
  so it has nothing to substitute there.
- No new carrier, no new format: read
  `.git/gh-read-cache/issue-<n>-approvals.json` exactly as
  `gates/ci.py._read_approval_record`/`_write_approval_record` already
  write it — this issue only adds a second reader, never a second writer.
- Non-goals (explicit in the issue): the final-removal cycle (dropping the
  regex/needle copies + core board-gate R4 + citation-gate sync), any
  change to the flows JSON schema or rsb rendering, and — per survey
  finding 1 — the `_BRANCH_RE`/`_role_from_pr` site (#1814 already
  migrated it) and — per survey finding 3 — `spawn._front_role()` (no
  carrier dependency; confirmed unchanged by reading its body).

## Rationale

Two designs were open for how `_pr_approved` reads the #1818 record:

1. **Chosen — read the record directly inside `_pr_approved`, scoped to
   the one `role` argument already passed in**: call
   `gates.ci._read_approval_record` (or an equivalent inline read of the
   same file) on `spawn._approval_record_path(root, issue_n)`, and treat
   `role in record` as sufficient to return `True` without also requiring
   the needle scan to match. `issue_n` is derived from the existing
   `subject` parameter (`int(subject.split("-", 1)[1])`, the same idiom
   already used at flows.py:352/391/405) rather than adding a 6th
   parameter to `_pr_approved` or touching either of its two call sites.

2. **Rejected — call `gates.ci._approved_roles_on_issue(root, issue_n)`
   and check `role in <returned set>`.** That function unions record and
   comment-scan results for the *whole issue*, any role — it is
   deliberately issue-level (survey finding 2, citing its own docstring at
   gates/ci.py:216-219: "role 은 상관없이 이 이슈에 대해 *어떤* 역할이
   승인받았는지"), while `_pr_approved`'s contract is role-exact
   (`APPROVE <subject>/<role>`, one specific role). Reusing it would
   silently broaden `_pr_approved`'s semantics — a PR for role A would
   read as approved once any role on the issue is approved, which is not
   today's behavior and not what the issue's byte-identical requirement
   allows. Its own docstring explicitly scopes it out of this issue's
   write set for exactly this reason.

Option 1 keeps `_pr_approved`'s existing role-exact contract intact and
only substitutes where the boolean's `True` case can come from (comment
needle → also a cached record hit), matching the same shape #1821 used
for `approval-gate.sh`'s dual-read (docs/issue-1821/proposals/
approval-gate-dual-read.md, same file being read, no new writer).

## What will be done

1. In `gates/flows.py`, import `_read_approval_record` and
   `_approval_record_path` (from `gates.ci` and `spawn` respectively — no
   circular import per survey finding 2's gates/ci.py:1-40 read) and add a
   record check at the top of `_pr_approved`: derive `issue_n` from
   `subject`, read the record via `spawn._approval_record_path(root,
   issue_n)` — `root` threaded in as a new `root: Path` parameter to
   `_pr_approved` (both call sites already have `root` in scope,
   flows.py:307/390/404) — and short-circuit to `True` when `role` is a
   key in the record. Fall through to the existing needle scan and
   PR-review loop unchanged when the record is absent, empty, or does not
   contain `role`.
2. Add `test/test_flows_role_field.py` covering three cases: a
   record-hit case (a fabricated approval-record file containing the role
   short-circuits to `True` with no matching comment/review present), a
   fallback case (no record file, comment needle present, matches today's
   behavior), and a no-carrier legacy case (neither record nor needle nor
   review — a full `flows_payload()` run, or the relevant slice, checked
   byte-for-byte against a pre-change capture on a fixed input fixture).
3. No edits to `test/test_convention_equivalence.py`'s existing test
   bodies; it is listed in `files:` only because the issue's acceptance
   §1 requires a `git diff` over it showing additions only — this
   proposal adds no equivalence-harness tests there since
   `RsbStatusBoardEquivalenceTest` already covers the needle-only golden
   case (survey "Test file survey"); if phase 2 finds a gap requiring a
   new case, it will be an addition, never an edit to an existing test.

## Out of scope

- Removing `_BRANCH_RE`, the needle string construction, or any other
  parser copy (final-removal cycle, a separate future sub-issue per the
  issue's Non-goals).
- Core board-gate requirement R4 and citation-gate sync noted on #1814 as
  deferred to that same final-removal cycle.
- Any change to `flows_payload()`'s JSON schema, field names, or the rsb
  frontend's rendering of that payload.
- `spawn._front_role()` — survey finding 3 confirms it has no carrier
  dependency to migrate.

## How you'll know it worked

- `python3 -m pytest test/test_convention_equivalence.py -q` — full pass,
  and a `git diff` over that file shows additions only (or no diff, if no
  new case is needed).
- `python3 -m pytest test/test_flows_role_field.py -q` — full pass,
  covering the record-hit, fallback, and no-carrier-legacy cases named
  above, with the no-carrier case checked byte-for-byte for
  `flows_payload()` output against a pre-change baseline.
