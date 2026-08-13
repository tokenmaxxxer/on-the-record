"""Per-role quality-bar merge gate — issue #1156.

Pure classifier, network-free, `landing_readiness.classify`-shaped
(gates/landing_readiness.py line 31): given whether a PR's diff is scoped
to a role that owns a `quality_bar` (roles/specs/<role>.spec.json), the
most recent verdict recorded for that (PR, role) pair, and the identity
that authored the verdict record vs. the identity that produced the
bar-scoped diff, returns BAR_MET / BAR_NOT_MET / ESCALATE / NO_BAR_SCOPED.

Anti-circularity (proposal §4, docs/issue-1156/proposals/
per-role-quality-bars.md): identity here means an *account*, not a bare
`CLAUDE_ROLE` string — `CLAUDE_ROLE` is self-declared and
operator-controlled, so comparing it alone lets one operator author the
diff under one role name and the verdict under another in the same
session and pass. Callers must resolve both `record_author_account` and
`producer_account` to git author/committer or PR-author accounts (the
same primitive `pr-preflight.sh`/`approval-gate.sh` already use to
resolve "who authored this") before calling `classify` — this module
takes the resolved accounts as explicit inputs and never re-derives them
from `CLAUDE_ROLE` itself.
"""
from __future__ import annotations

BAR_MET = "BAR_MET"
BAR_NOT_MET = "BAR_NOT_MET"
ESCALATE = "ESCALATE"
NO_BAR_SCOPED = "NO_BAR_SCOPED"

REJECT_CAP = 3  # 3 consecutive bar-not-met verdicts on the same (PR, role) -> ESCALATE


def bar_scoped_roles(pr_files, role_path_patterns):
    """`role_path_patterns`: {role: [glob pattern, ...]} (each role's
    `use_when.trigger.path_patterns`, the same trigger field
    merge-allow-gate.sh's routing-fix already reads). Returns the subset of
    roles whose patterns match at least one file in `pr_files`."""
    import fnmatch

    scoped = set()
    for role, patterns in role_path_patterns.items():
        if not patterns:
            continue
        if any(fnmatch.fnmatch(f, pat) for f in pr_files for pat in patterns):
            scoped.add(role)
    return frozenset(scoped)


def classify(bar_scoped: bool, verdict: str | None,
             record_author_account: str | None,
             producer_account: str | None,
             consecutive_bar_not_met_count: int = 0) -> tuple[str, str | None]:
    """(classification, reason) — reason is None only for BAR_MET/NO_BAR_SCOPED.

    `verdict` is the most recent recorded verdict for this (PR, role) pair:
    "bar-met", "bar-not-met", or None when no record exists at all.
    `record_author_account`/`producer_account` are resolved accounts (see
    module docstring) — None when unresolvable (treated as no record).
    """
    if not bar_scoped:
        return NO_BAR_SCOPED, None

    same_identity = (
        record_author_account is not None
        and producer_account is not None
        and record_author_account == producer_account
    )

    if (
        verdict == "bar-met"
        and record_author_account is not None
        and producer_account is not None
        and not same_identity
    ):
        return BAR_MET, None

    if record_author_account is None or producer_account is None:
        reason = "no bar-met record"
    elif same_identity:
        reason = "record author and producer are the same account (anti-circularity)"
    elif verdict == "bar-not-met":
        reason = "bar-not-met verdict recorded"
    else:
        reason = "no bar-met record"

    if consecutive_bar_not_met_count + 1 >= REJECT_CAP:
        return ESCALATE, reason
    return BAR_NOT_MET, reason
