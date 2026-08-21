---
code_under_review: HEAD
loop_state: landed
type: feature
breaking: false
verdict: pass
---

# issue-1821 implementation record

## What was done

`on-the-record/hooks/approval-gate.sh` now dual-reads both replacement
carriers to completion, per the approved proposal
(docs/issue-1821/proposals/approval-gate-dual-read.md):

1. **Role.** The existing `.on-the-record/role.json` sidecar read
   (#1814) is unchanged. New: when the sidecar resolves, the hook
   *additionally* attempts an independent branch-regex parse purely to
   cross-check — never to replace the sidecar's own values. If the
   branch also parses and its issue number or role token disagrees with
   the sidecar's, the hook denies (fail-closed, exit 2) naming both
   `issue-<n>/<role>` values. If the branch doesn't parse, no comparison
   is possible and the hook proceeds on the sidecar values alone,
   byte-identical to pre-#1821 behavior. The sidecar-absent fallback
   path (branch-regex-only) is untouched.
2. **Approvals.** Before the existing `gh`-based needle scan, the hook
   now reads `.git/gh-read-cache/issue-<n>-approvals.json` (#1818). A
   parseable JSON object containing `role` as a key sets `approved =
   True` immediately, skipping both the `gh issue view` needle scan and
   the delegation-citation scan. Any read/parse failure (missing file,
   invalid JSON, non-dict shape) falls through unchanged to the existing
   `gh` needle scan and delegation logic.
3. Enforcement semantics (what is blocked/allowed) are unchanged; only
   the data source is, per the issue's own framing.

Tests:
- test/test_convention_equivalence.py: two additions to
  `ApprovalGateEquivalenceTest` — one pinning the new approval-record
  read (path + `role in record` check), one pinning the new,
  distinct sidecar-vs-branch mismatch comparison (separate from the
  existing, untouched `if role != branch_role:` fallback-path check).
  No existing golden-case line edited or removed (`git diff` below).
- test/test_approval_gate_carriers.py (new): live-fires the real
  hook via `subprocess.run(["bash", ...])` with a real PreToolUse JSON
  payload on stdin, a fake `gh` shim, and a real git checkout, across
  the full carrier matrix from acceptance §2 — both-carriers,
  sidecar-only, record-only, neither (asserted byte-identical to
  pre-#1821: same approve/deny outcomes and deny message), corrupt
  sidecar, corrupt record (both non-dict-shape and unparseable-JSON
  variants), role-mismatch (both role-token and issue-number variants,
  each naming both values in the deny message), and an unparseable
  (detached-HEAD) branch after the sidecar resolves — proceeds on the
  sidecar alone, no comparison attempted.

## Rationale for deviations

One pre-existing test in test/test_branch_role_field.py (outside this
issue's frozen write set) encoded the exact scenario this issue's new
mismatch guard now intercepts first (a sidecar role deliberately
differing from a decoy branch role) and asserted the *old*
approvers.md-absent deny message. Logged and fixed inline — mechanical,
one assertion, no design judgment — per
docs/issue-1821/reports/implementation/deviation-log.md.

## Why

Requirement 1 (issue body, entry 5 of the frozen skill-axis migration
order, docs/issue-1792/reports/implementation.md §Migration order):
`approval-gate.sh` is the last of the four regex-parse sites to migrate
onto the #1814/#1818 carriers landed by prior entries. Requirement 2
(carrier anomaly hardening) and the Trust note both require a
resolvable sidecar-vs-branch disagreement to fail-closed rather than
fail-open, since it signals workspace-state inconsistency, not an
infrastructure failure the existing fail-open conventions exist for.

## Upstream / basis

- docs/issue-1821/proposals/approval-gate-dual-read.md (approved via
  issue comment `APPROVE issue-1821/implementation` from
  @JiwonJung94, an approvers.md-listed account; single-account mode,
  author == approver, exact string match — canonical: `gh issue view
  1821 --json comments`).
- #1814 (`.on-the-record/role.json` sidecar carrier).
- #1818 (`.git/gh-read-cache/issue-<n>-approvals.json` structured
  approval record).

## What did not work

None.

## Test tiering

`.on-the-record/test-tiers.json` present; diff touches
`on-the-record/hooks/*.sh`, matching the `slow` tier's
`trigger_change_classes`, so both tiers were run.

`python3 -m pytest -q -m "not slow"`:
```
2431 passed, 18 xfailed, 3 xpassed, 2 failed in 36.39s
```
canonical: executed live on this branch. The 2 failures
(tests/test_gh_quota_guard.py test_sweep_call_budget,
tests/test_spawn.py PollHeartbeatMarkerRelocationTest
test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts)
are pre-existing and unrelated to this issue's write set — reproduced
identically with `git stash` applied (this issue's diff removed),
confirming they are not a regression from this change.

`python3 -m pytest -q -m slow`:
```
100 passed, 2 xfailed in 713.14s (0:11:53)
```
canonical: executed live on this branch, clean.

## Acceptance evidence

python3 -m pytest test/test_convention_equivalence.py -q — executed
live:
```
.................................                                        [100%]
33 passed in 0.83s
```

`git diff` over test/test_convention_equivalence.py — additions only
(no existing line touched):
```
+    def test_hook_reads_approval_record_path(self):
+        # issue #1821: dual-reads the #1818 structured approval record
+        # before the gh needle scan.
+        text = self.HOOK_PATH.read_text(encoding="utf-8")
+        self.assertIn('"gh-read-cache", "issue-%d-approvals.json" % issue', text)
+        self.assertIn("if isinstance(record, dict) and role in record:", text)
+
+    def test_hook_has_distinct_sidecar_vs_branch_mismatch_deny(self):
+        # issue #1821: a NEW comparison, distinct from the existing,
+        # untouched `if role != branch_role:` fallback-path check above —
+        # this one compares the sidecar's own role/issue against an
+        # independently branch-parsed role/issue once the sidecar has
+        # already resolved.
+        text = self.HOOK_PATH.read_text(encoding="utf-8")
+        self.assertIn("if cross_issue != issue or cross_role != branch_role:", text)
+        self.assertIn("disagrees with the", text)
+
```

python3 -m pytest test/test_approval_gate_carriers.py -q — executed
live:
```
............                                                             [100%]
12 passed in 0.91s
```

## Open findings

None.
