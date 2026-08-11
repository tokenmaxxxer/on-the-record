"""Tests for gates/delegation_metrics.py — issue #707's pre-registered
metrics (operator_approvals_per_landed_pr, self_approval_violation_count).

Run: python3 -m pytest gates/test_delegation_metrics.py -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import delegation_metrics as dm  # noqa: E402


def test_operator_approvals_counts_only_human_typed():
    comments = [
        {"body": "APPROVE issue-707/implementation", "author": {"login": "octocat"}},
        {"body": "APPROVE issue-707/implementation VIA DELEGATION issue-707/implementation",
         "author": {"login": "octocat"}},
        {"body": "looks good", "author": {"login": "octocat"}},
        {"body": "APPROVE issue-707/implementation", "author": {"login": "not-approver"}},
    ]
    approvers = {"octocat"}
    assert dm.operator_approvals_per_landed_pr(comments, approvers, landed_pr_count=2) == 0.5


def test_operator_approvals_undefined_with_no_landed_prs():
    assert dm.operator_approvals_per_landed_pr([], {"octocat"}, landed_pr_count=0) is None


def test_self_approval_violation_count_only_counts_denials_with_role():
    events = [
        {"hook": "delegation-post-gate", "role": "implementation", "denied": True},
        {"hook": "delegation-post-gate", "role": "", "denied": False},
        {"hook": "delegation-post-gate", "role": "qa", "denied": True},
    ]
    assert dm.self_approval_violation_count(events) == 2


def test_self_approval_violation_count_zero_when_none_denied():
    events = [{"hook": "delegation-post-gate", "role": "implementation", "denied": False}]
    assert dm.self_approval_violation_count(events) == 0


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
