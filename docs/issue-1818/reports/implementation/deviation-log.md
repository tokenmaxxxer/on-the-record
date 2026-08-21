2026-08-21T00:00:00Z | filed | write-through approval-record cache (gates/ci.py:189 `_approved_roles_on_issue`, per the approved proposal docs/issue-1818/proposals/approval-record-carrier.md) breaks a subset of `gates/test_closes_gate_ci.py` — canonical: `python3 -m pytest gates/test_closes_gate_ci.py -q` executed live on this branch's working tree after this issue's implementation edits, output below.

derived: `python3 -m pytest gates/test_closes_gate_ci.py -q`
```
FAILED gates/test_closes_gate_ci.py::t_phase_from_approval_no_signal_is_phase1
FAILED gates/test_closes_gate_ci.py::t_autodetect_success_derives_issue_role_and_phase_from_approval
FAILED gates/test_closes_gate_ci.py::t_phase_from_approval_non_approver_comment_is_phase1
FAILED gates/test_closes_gate_ci.py::t_autodetect_closes_only_blocks_commit_message_keyword_with_clean_body
FAILED gates/test_closes_gate_ci.py::t_autodetect_reachability_fix_blocks_closes_keyword_without_approval
FAILED gates/test_closes_gate_ci.py::t_phase_from_approval_pr_thread_comment_is_not_issue_level_is_phase1
FAILED gates/test_closes_gate_ci.py::t_autodetect_missing_approval_refusal_names_role_searched_and_approvals_present
7 failed, 47 items ran in 1.25s
```

Those tests call `_approved_roles_on_issue`/`_phase_from_approval`/`_autodetect_issue_phase` with `Path(".")` (the real repo checkout, not a tmp dir) and reuse the same literal issue number (245) across scenarios that mock contradictory comment bodies per test. The new record write persists real approval state from one such test into a later, unrelated one within the same process (write-through cache keyed by issue number under `.git/gh-read-cache/`, gates/ci.py:189-224) — the tests assume the function under test is memoryless, an assumption that stops holding once it gains a persistent cache. On main (pre-issue-1818, verified via `git stash` before re-running the same command), this same test file has no such failures.

Resolving this needs test-isolation work (a cache-clearing fixture, or a scoped tmp repo root given to those tests instead of `Path(".")`) in `conftest.py` or `gates/test_closes_gate_ci.py` — both outside this issue's frozen write set (`gates/ci.py`, `spawn.py`, `test/test_convention_equivalence.py`, `test/test_approval_role_field.py`, per docs/issue-1818/proposals/approval-record-carrier.md `files:`) — reported, not spawned. Resolution path: a follow-up issue scoped to `conftest.py`/`gates/test_closes_gate_ci.py` adding a `.git/gh-read-cache/*-approvals.json` cleanup fixture (or switching those tests to a tmp repo root) ahead of any broader rollout of this cache design.
