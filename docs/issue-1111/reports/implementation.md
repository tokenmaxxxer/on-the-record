---
code_under_review:
  - on-the-record/hooks/deliverable-guard.sh
  - on-the-record/hooks/product-capture-stopgate.sh
  - on-the-record/hooks/test_deliverable_guard.py
  - on-the-record/hooks/test_product_capture_stopgate.py
  - docs/reports/product/priorities.md
type: fix
breaking: false
# canonical: python3 on-the-record/hooks/test_deliverable_guard.py -q — result: 19 passed (executed live this session, fenced output below)
verdict: pass
loop_state: landed
---

Subject: issue-1111

## What was done

canonical: commit 73475d0 on this branch (git show --stat 73475d0)

Phase-2 build per the approved proposal
(docs/issue-1111/proposals/2026-08-13-product-capture-ownership.md),
resolving the deliverable-guard/product-capture-stopgate deadlock (northpole
req#5), landed in commit 73475d0:

1. on-the-record/hooks/product-capture-stopgate.sh: retargeted both write
   path templates from docs/product/<cat>.md /
   docs/issue-<n>/product/<cat>.md to docs/reports/product/<cat>.md /
   docs/issue-<n>/reports/product/<cat>.md — nested inside the reports
   bucket board-gate.sh already admits. No other logic changed.
2. on-the-record/hooks/test_product_capture_stopgate.py: updated all
   path-hardcoded assertions to the new docs/reports/product path targets.
   Also added the missing `if __name__ == "__main__"` runner this file
   never had (its t_-prefixed functions were not collected by pytest and
   the file previously executed nothing when run directly) — same t_-prefix
   scan pattern already used by sibling files in this directory (e.g.
   test_merge_allow_gate.py).
3. on-the-record/hooks/deliverable-guard.sh: replaced the single
   `n.endswith("docs/specs/approvers.md")` check with an EXEMPT_SUFFIXES
   tuple (approvers.md plus the four product-capture category files under
   docs/reports/product/) and a PRODUCT_CAPTURE_ISSUE_RE regex covering the
   issue-scoped equivalents. Updated the header comment.
4. on-the-record/hooks/test_deliverable_guard.py: added three cases —
   orchestrator write to docs/reports/product/priorities.md allowed; write
   to docs/issue-123/reports/product/priorities.md allowed; write to the
   unrelated docs/reports/product/other.md still denied.
5. docs/reports/product/priorities.md: created with the bootstrap header
   and the pending #745 close-out entry (deprioritized
   infrastructure/no-direct-requirement behind #1110, the 7-scenario
   harness re-measurement, and the user's fresh-session E2E test).

## Why

northpole req#5 (problems are not pushed back to the human): the
orchestrator session could neither write the product-capture doc
(deliverable-guard.sh denied it) nor end the turn cleanly
(product-capture-stopgate.sh kept nudging for it) — a deadlock. Exactly
one gate now owns the path: the stopgate writes into a bucket
(docs/reports/product/) that board-gate.sh already recognizes, and
deliverable-guard.sh's exemption follows it there.

## Upstream / basis

docs/issue-1111/proposals/2026-08-13-product-capture-ownership.md

## Acceptance — how you'll know it worked

canonical: python3 on-the-record/hooks/test_deliverable_guard.py -q (executed this turn)
checked: `python3 on-the-record/hooks/test_deliverable_guard.py -q` — result: PASS

```
$ python3 on-the-record/hooks/test_deliverable_guard.py -q
...................                                                      [100%]
19 passed in 0.60s
```

canonical: python3 on-the-record/hooks/test_product_capture_stopgate.py (executed this turn)
checked: `python3 on-the-record/hooks/test_product_capture_stopgate.py` — result: PASS

```
$ python3 on-the-record/hooks/test_product_capture_stopgate.py
PASS t_bootstrap_creates_missing_file_on_first_flag
PASS t_claude_role_set_is_noop
PASS t_flagged_requirement_with_matching_doc_diff_is_silent
PASS t_flagged_requirement_with_no_doc_change_gets_additional_context
PASS t_missing_transcript_path_fails_closed_silently
PASS t_no_flagged_sentence_is_silent
PASS t_off_issue_branch_empty_state_is_silent
PASS t_off_issue_branch_falls_back_to_repo_root_doc_path
PASS t_orchestrate_off_is_noop
9/9 passed
```

canonical: bash on-the-record/hooks/deliverable-guard.sh (executed this turn against a fresh non-board git repo at /tmp/otr-live-check, orchestrator-shaped payload, no CLAUDE_ROLE)
checked: live PreToolUse Write to docs/reports/product/priorities.md — result: exit 0

```
$ env -u CLAUDE_ROLE ORCHESTRATE_OFF="" bash on-the-record/hooks/deliverable-guard.sh <<'EOF'
{"tool_name":"Write","tool_input":{"file_path":"docs/reports/product/priorities.md","content":"x"},"cwd":"/tmp/otr-live-check"}
EOF
$ echo $?
0
```

Exit 0 (was 2 before this change). board-gate.sh is not this repo's own
hook (out of tree, see the proposal's Constraints) so it is not separately
invoked here — docs/reports/product/ is already inside its six admitted
buckets by construction, per the proposal's Rationale.

docs/reports/product/priorities.md exists on this branch (committed in
73475d0) with the #745 entry appended.

## What did not work

None.

## Open findings

canonical: docs/issue-1111/reports/implementation/2026-08-13-hunt-before-landing.md

The before-landing hunt (stance 3) found that board-gate.sh's R3 (a
separate rule from the R1 bucket check the proposal already accounted
for) unconditionally denies any docs/issue-<n>/... write from a
role-less (no CLAUDE_ROLE) session, with no carve-out for the
product-capture orchestrator-scribing exemption deliverable-guard.sh
just added. In a repo where board-gate.sh is wired in alongside
deliverable-guard.sh — on-the-record's own repo included — the
issue-scoped write path docs/issue-<n>/reports/product/<cat>.md clears
deliverable-guard.sh but is still denied by board-gate.sh, so it never
actually lands there. The non-issue-scoped path
(docs/reports/product/<cat>.md, used by priorities.md in this delivery)
is unaffected — board-gate.sh's R3 only fires on the docs/issue-<n>/
tree.

Not fixed here: board-gate.sh lives in a separately-pulled core
rulebook outside this repo's own tree (runs/ is gitignored — same
constraint the proposal's Constraints section already states for the
R1 bucket finding), so this repo's branch cannot durably carry a fix to
it. This is the same class of finding as the after-proposal hunt's R1
result, now extended to R3 — left open for the next session that owns
board-gate.sh (or a follow-up issue against it) to resolve.

## Rationale for deviations

canonical: python3 harness/fixture-target/scenario.py (executed this turn)

harness/fixture-target/scenario.py (not in the frozen write set) contains a
scenario, scenario_capture_fires_in_target_repo, that hardcodes the old
fallback path and the substring "docs/product/" in an advisory-text
assertion. Retargeting product-capture-stopgate.sh per proposal step 1
breaks this scenario:

```
$ python3 harness/fixture-target/scenario.py
[FAIL] capture-fires: advisory did not reference fallback path: 'product-capture-stopgate: statements matching these categories were not reflected in docs/reports/product/: requirements.md (e.g. "the project must support offline mode"). Record them as structured entries before ending the turn.'
[PASS] empty-state: no docs/product/* writes, no advisory
```

Per the SCOPE-EXCEEDED RULE, this file is outside the proposal's frozen
write set, so it was not edited here. Filed as a deviation instead — see
docs/issue-1111/reports/implementation/deviation-log.md. Follow-up: update
harness/fixture-target/scenario.py's two hardcoded docs/product path
references to docs/reports/product, matching this proposal's retarget.

## Next steps

File a follow-up issue (or fold into the next #1111-adjacent proposal) to
update harness/fixture-target/scenario.py's two docs/product references to
docs/reports/product, matching this change.

## Resolution path

The follow-up scenario-path fix is mechanical (two path strings) and
low-risk; route it through a normal phase-1 proposal on a fresh issue
(or as an addendum to this one if reopened), scoped only to
harness/fixture-target/scenario.py.
