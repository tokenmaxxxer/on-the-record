"""Pre-registered metrics for issue #707's standing-delegation mechanism
(`docs/issue-707/proposals/product-discovery.md`'s H1 hypothesis package).

Both metrics are computed from data the mechanism already makes
distinguishable by construction — a human-typed `APPROVE issue-<n>/<role>`
and a delegation citation `APPROVE issue-<n>/<role> VIA DELEGATION <scope>`
are different strings — so no new persisted instrumentation is needed to
compute them; this module is what "enables" the computation (issue #707
Acceptance: "Emit/enable the pre-registered metrics").

Pure functions only — no network calls. Callers fetch `gh issue view
--json comments` / landed-PR counts themselves (same pattern every other
gates/*.py module in this repo already follows) and pass the data in.
"""
from __future__ import annotations
import re

_HUMAN_APPROVE_RE = re.compile(r"^APPROVE issue-(\d+)/([\w-]+)$")
_DELEGATION_CITE_RE = re.compile(r"^APPROVE issue-(\d+)/([\w-]+) VIA DELEGATION (\S+)$")

# Matches delegation-post-gate.sh's stderr line, so a session log grep of
# the guardrail line count reproduces the same number this function
# computes from structured deny-event records.
SELF_APPROVAL_VIOLATION_MARKER = "self_approval_violation_count"


def operator_approvals_per_landed_pr(comments: list[dict], approvers: set[str],
                                      landed_pr_count: int) -> float | None:
    """H1's primary metric: fresh human-typed `APPROVE` comments (never a
    delegation citation) / landed PRs. Returns None when `landed_pr_count`
    is 0 — the ratio is undefined, not zero, with no PRs landed yet."""
    if landed_pr_count == 0:
        return None
    human_approvals = 0
    for c in comments:
        body = (c.get("body") or "").strip()
        login = (c.get("author", {}) or {}).get("login")
        if login not in approvers:
            continue
        if _HUMAN_APPROVE_RE.match(body):
            human_approvals += 1
    return human_approvals / landed_pr_count


def self_approval_violation_count(deny_events: list[dict]) -> int:
    """The guardrail: count of `deny_events` where `delegation-post-gate.sh`
    (or `approval-gate.sh`'s own delegation path, for defense in depth)
    refused a role-bound session's own delegation citation. Each event is
    `{"hook": str, "role": str, "denied": bool}` — the shape a session-log
    scan of the hooks' stderr output would produce. Counts only genuine
    denials; a hook run that passed through (role absent, not a citation)
    is not a violation attempt and must not inflate this count."""
    return sum(1 for e in deny_events if e.get("denied") and e.get("role"))
