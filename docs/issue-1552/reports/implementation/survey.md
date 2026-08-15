Subject: issue-1552

# Current-state survey

Write set: `on-the-record/hooks/pr-preflight.sh`, `on-the-record/hooks/test_pr_preflight.py`.

canonical: on-the-record/hooks/pr-preflight.sh:269-274 (read directly)
`_MACHINE_BODY_RE` already matches the watchdog `Judgment opened: ` and
`Verdict: PR ` templated shapes.

canonical: on-the-record/hooks/test_pr_preflight.py:539-568 (read directly)
The existing test `test_hook_allows_pr_when_only_machine_comments_post_spawn`
feeds both shapes through the real hook and asserts `gh pr create` is not
blocked. So two of the issue's three named shapes are already covered.

canonical: on-the-record/hooks/pr-preflight.sh:266-274 (read directly)
The third shape — a bare single-account approval string
(`APPROVE issue-N/role`) — is not in `_MACHINE_BODY_RE`. That string is
posted by a human approver account (per contract v3 s19's single-account
approval path) and is currently treated as an ordinary operator comment
by the reconciliation-cursor block (pr-preflight.sh:283-316): if it lands
after session spawn, it counts as the "newest operator comment" and can
block `gh pr create` until reconciled, even though it carries no free-form
operator intent to reconcile — it is a fixed-format approval token, the
same class of comment issue #1310 already exempts for the watchdog shapes.

canonical: on-the-record/hooks/test_pr_preflight.py (grep for "_is_machine_comment\|_MACHINE_BODY_RE", read directly)
No existing test calls `_is_machine_comment`/`_MACHINE_BODY_RE` directly
against all three named shapes plus a negative (non-templated human
comment) case in one place — existing coverage of the two already-handled
shapes is only reachable indirectly through the reconciliation-cursor
integration test, and the bare-APPROVE shape has no coverage at all.

Skip condition: this is a narrow regex-extension bugfix to an existing
classifier (contract v3 s19's proposal-shape-gate pure-bugfix skip
condition) — no design decision is open beyond which two-line regex
alternative to add, so the proposal below is correspondingly short.
