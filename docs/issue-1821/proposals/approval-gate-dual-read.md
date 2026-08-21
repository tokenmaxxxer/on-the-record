---
status: proposed
files:
  - on-the-record/hooks/approval-gate.sh
  - test/test_convention_equivalence.py
  - test/test_approval_gate_carriers.py
---

## Request

Issue #1821 (frozen migration order entry 5, docs/issue-1792/reports/
implementation.md §Migration order): `approval-gate.sh` today rebuilds
its own approval decision from two independent, hook-local
implementations — a branch-regex role parse (already partially
dual-read against the #1814 `.on-the-record/role.json` sidecar, but
never cross-checked against the branch parse when the sidecar
resolves) and a from-scratch `gh issue view` comment scan for the
APPROVE needle (never touching the #1818 structured approval record at
`.git/gh-read-cache/issue-<n>-approvals.json`). This issue makes the
hook dual-read both carriers to completion: prefer the sidecar role and
the structured approval record, fall back to the existing branch regex
and needle scan exactly as today when a carrier is absent or
unparseable, and — new — refuse (fail-closed) when the sidecar role and
a still-resolvable branch-parsed role disagree. The hook's enforcement
semantics (what it blocks/allows) do not change; only the data source
does, per the issue's own framing.

## Constraints

- `test/test_convention_equivalence.py` (32 tests after #1818) stays
  green with additions only — no edits to existing golden cases
  (docs/issue-1821/reports/implementation/survey.md, "Dependency /
  ordering facts").
- Byte-identical decisions across every carrier/fallback combination
  the issue's acceptance §2 enumerates: both-carriers, sidecar-only,
  record-only, neither, corrupt-carrier, role-mismatch — the
  neither-carrier case must be byte-identical to today's behavior.
- No code path may weaken a refusal; the record read may only
  substitute where the approval boolean comes from, never skip the
  approvers.md-membership check or the needle-match semantics.
- Any carrier anomaly (missing, unparseable) engages the existing
  fallback; a *resolvable* sidecar-vs-branch role disagreement is the
  one new behavior — fail-closed, with a message naming both values.
- No new carrier, no new format: consume `.on-the-record/role.json`
  (#1814) and `.git/gh-read-cache/issue-<n>-approvals.json` (#1818)
  exactly as already written by `spawn.py`'s `_write_role_sidecar` and
  `gates/ci.py`'s `_write_approval_record` — this hook only reads them.
- Non-goals (explicit in the issue): rsb (entry 6), removing the branch
  regex or needle scan (a later final-removal sub-issue's job, together
  with core's board-gate R4 + citation-gate sync recorded on #1814),
  any change to what the gate enforces.
- New `test/test_approval_gate_carriers.py` must live-fire the real
  hook (`bash on-the-record/hooks/approval-gate.sh` with a real
  PreToolUse JSON payload on stdin, per the issue's acceptance §2 and
  the #1814 precedent of live-fire hook tests in
  `test/test_branch_role_field.py`), not just assert on hook source
  text — the existing `ApprovalGateEquivalenceTest` in
  `test/test_convention_equivalence.py` already does source-shape
  assertions; the carrier matrix needs the hook actually run.

## Rationale

Two designs were open for the approvals-record read:

1. **Chosen — read the record file directly inside the hook's own
   embedded Python** (the same file `gates/ci.py._read_approval_record`
   already reads, `.git/gh-read-cache/issue-<n>-approvals.json`),
   treating a `record.get(role)` hit as sufficient without re-running
   the `gh` needle scan.
2. **Rejected — always run the needle scan and use the record only as
   a tie-breaker/cache-hint, identical to `gates/ci.py`'s own
   `_approved_roles_on_issue` pattern** (record unioned in, but the
   comment scan always still executes).

Option 2 was rejected because it does not solve the problem this issue
exists to fix: the entire point of dual-reading the record is to let
the hook answer without a `gh` network call when the record already
covers the role (mirroring why #1814's sidecar read is preferred over
always re-parsing the branch — cheaper, and works `gh`-less). If the
scan always still runs, the record read is decorative — the hook still
pays the network round-trip on every write, and still fails open on
`gh` unavailability exactly as before, so nothing is gained. Because
the record is provably a write-through cache of a *past* passing scan
(docs/issue-1821/reports/implementation/survey.md, "The #1818
structured approval record" section — `record.get(role)` truthy is a
strict subset of what the scan would find), trusting a record hit
outright cannot approve anything the scan-only path would have refused
— it can only let a *previously proven* approval skip a redundant
re-fetch. This keeps the "hook's own enforcement semantics are
unchanged" constraint intact while actually reducing `gh` dependence,
which option 2 would not.

For the mismatch check, the alternative to fail-closed was **fail-open,
consistent with today's existing unparseable-branch and gh-failure fail-
open conventions** — rejected explicitly by the issue body's own Trust
note ("mismatch is a hard refusal, not a preference"): a role
disagreement between two carriers that both successfully resolved is
not an infrastructure failure (which fail-open exists for) but a
signal the workspace state itself is inconsistent, which is exactly the
shape of anomaly this trust-critical gate must not paper over.

## What will be done

In `on-the-record/hooks/approval-gate.sh`'s embedded Python:

1. **Role resolution — add the missing comparison.** Keep the existing
   sidecar read (`.on-the-record/role.json`) exactly as-is. When the
   sidecar resolves (`issue`/`branch_role` set from it), *additionally*
   attempt the branch-regex parse (today skipped entirely once the
   sidecar resolves) purely to obtain a second, independent role/issue
   pair for comparison — never to replace the sidecar's own values. If
   the branch also parses (`issue-<n>/<role>` matches) and either its
   issue number or its role token differs from the sidecar's, deny
   with a message naming both values (sidecar role/issue vs.
   branch-parsed role/issue) — fail-closed, per the issue's Trust note.
   If the branch does not parse (detached HEAD, non-issue branch), no
   comparison is possible — proceed on the sidecar values alone,
   unchanged from today. When the sidecar is absent/unparseable, the
   existing branch-only fallback path is untouched (byte-identical).
2. **Approvals resolution — add the record read.** Before the existing
   `gh_json`/needle-scan block, attempt to read
   `.git/gh-read-cache/issue-<n>-approvals.json` (same path shape as
   `spawn._approval_record_path`, reimplemented inline as a plain
   `os.path.join(cwd, ".git", "gh-read-cache", "issue-%d-approvals.json"
   % issue)` read — this hook has no import access to `spawn.py`/`gates/
   ci.py`, consistent with its existing standalone-script design). If
   the file parses as a JSON object and `role` is a key in it, treat
   `approved = True` immediately, skipping the `gh` needle scan and the
   delegation-citation scan entirely (both become unnecessary once a
   prior passing scan is already on record for this exact role). Any
   read/parse failure (missing file, invalid JSON, wrong shape) falls
   through unchanged to the existing `gh`-based needle scan and
   delegation-citation logic — byte-identical to today.
3. **Comment/message text**: the existing deny messages
   (`docs/specs/approvers.md` absent, no matching APPROVE comment) are
   unchanged; the new mismatch deny gets its own message per Constraint
   4 ("naming both values").
4. In `test/test_convention_equivalence.py`, add new test methods to
   the existing `ApprovalGateEquivalenceTest` class (additions only,
   no edits to the 32 existing golden-case tests) asserting: the hook
   source now references the approval-record path
   (`gh-read-cache`/`-approvals.json`), and a new source-shape
   assertion for the sidecar-vs-branch mismatch deny path (distinct
   from the existing, untouched `if role != branch_role:` fallback-path
   assertion — see the survey's note that these are two different
   comparisons).
5. New `test/test_approval_gate_carriers.py`: live-fire the real hook
   script via `subprocess.run(["bash", HOOK_PATH], input=<PreToolUse
   JSON>, ...)` in a temp git-workspace fixture, covering every
   combination the issue's acceptance §2 names: both carriers present
   and agreeing/approved; sidecar-only (no record — falls back to
   needle scan, mocked `gh`); record-only (no sidecar — falls back to
   branch regex for role, record read for approval); neither carrier
   (byte-identical to pre-#1821 behavior, asserted against a
   before/after golden fixture); corrupt carrier (unparseable JSON in
   either file — falls back cleanly, no crash); sidecar-vs-branch
   role-mismatch (both resolve, disagree — hard deny, message names
   both values).

## Out of scope

- Removing the branch-regex parse, the needle scan, or the delegation-
  citation logic — all three remain as the fallback path, per the
  issue's Non-goals and the frozen migration order's later
  final-removal sub-issue.
- rsb / `gates/flows.py` / `_pr_approved` (migration order entry 6) —
  untouched, not in this issue's write set.
- Any change to `spawn.py`'s sidecar-write or `gates/ci.py`'s
  record-write logic — both carriers are consumed as-is; this issue
  only adds a second reader to the record file and completes the
  reader-side comparison already half-built for the sidecar.
- Board-gate R4 / citation-gate sync mentioned in the issue body as
  tracked on #1814 — that is a separate, already-recorded item, not
  this issue's write set.

## How you'll know it worked

- `python3 -m pytest test/test_convention_equivalence.py -q` passes,
  32 existing cases plus new additions, `git diff` over that file
  showing additions only (no line of the 32 pre-existing golden
  assertions edited or removed).
- `python3 -m pytest test/test_approval_gate_carriers.py -q` passes,
  live-firing the real hook script across the full carrier matrix
  named in acceptance §2, with the neither-carrier case asserted
  byte-identical to today's (pre-#1821) behavior and the role-mismatch
  case asserted as a hard deny (non-zero exit, message naming both
  role/issue values).
