# Scout brief — issue #707: standing-delegation mechanism

Mode: one parallel sweep round, two concurrent WebSearch angles (by-methodology,
by-modern-agent-precedent); no deepening round run — judge point 1 found both hits converge on the
same shape (scoped/dated/revocable grant, provenance distinct from actor), so another round would
not change any build decision. Sweep stayed within the stage and wall-clock budget.

## Must-bes (what every strong precedent requires)

- A delegation is always **scoped, dated, and revocable** — never a blanket "agent decides now."
  ITIL's own modern guidance treats standard-change pre-authorization as scoped by change type/risk,
  not by actor; delegated-authority platforms (Aptly DOA) model grants as time-boxed with explicit
  reinstatement/expiry, not permanent handoffs.
- **Provenance survives the grantor's absence.** OAuth-style on-behalf-of delegation for AI agents
  keeps a persistent audit trail linking the acting agent to the human identity that granted it,
  with scope/expiry/audit metadata attached to every use — the delegation record, not the agent's
  say-so, is what a downstream check trusts.
- **Revocation must be enforceable in real time**, not just recorded — a grant that still "counts"
  after the operator revoked it is the exact failure class every source flags.

## Performance axes strong precedents compete on

1. **Scope precision** — how narrowly the grant is bound (a change type, a risk tier, an issue
   class) vs. how broadly it is read at use time.
2. **Auditability** — whether every delegated act cites back to the grant, or only the aggregate
   policy is logged.
3. **Separation of grantor identity from actor identity** — the party citing the delegation is
   structurally distinct from the party whose action it approves (this is the axis this issue's
   invariant maps onto directly).

## Adopt

Scoped + dated + revocable delegation record as the provenance object a gate checks, cited by an
actor structurally distinct from the one bound to the change under approval — matches this repo's
own #698 (unforgeable session-role-bind identity) precisely: the "distinct actor" axis is already
half-built here.

## Skip

Deep DOA-matrix-style approval hierarchies (multi-level sign-off chains, org-chart-shaped delegation
graphs) — out of proportion to this repo's single-operator, single-approvers.md-list reality; would
add a modeling surface this repo has no second approver tier to justify.

## Segment fit

This repo's shape (single-operator delegation, gate gets checked deterministically, no multi-party
org) is closer to the "on-behalf-of AI agent tool-calling" precedent than to enterprise DOA-matrix
software — the former is scoped to exactly one delegating human and one or more acting agents,
which is this repo's actual topology.

## Gap line

Current state already has: unforgeable actor identity (#698), a human-utterance-only APPROVE
grammar (protocol.md §5), an approvers.md allowlist. Missing against the field's must-bes: no
scoped/dated/revocable grant object exists anywhere in this repo; no gate reads anything but the
literal `APPROVE issue-<n>/<role>` string; no audit trail links an auto-approval back to a specific
grant. All three gaps are what the proposal's candidate 1 targets.

Sources:
- [6 ITIL Change Management Best Practices](https://invgate.com/itsm/change-management/change-management-best-practices)
- [Solved: Change Management -> Standard Change vs Pre-Approved — ServiceNow Community](https://www.servicenow.com/community/itsm-forum/change-management-gt-standard-change-vs-pre-approved-change/m-p/2886679)
- [On-Behalf-Of authentication for AI agents: Secure, scoped, and auditable delegation](https://www.scalekit.com/blog/delegated-agent-access)
- [Delegation of Authority Software | DOA Matrix Management | Aptly](https://www.aptlydone.com/platform/delegation-of-authority)
- [Tool calling authentication for AI agents: Identity, delegation, and auditability](https://www.scalekit.com/blog/oauth-tool-calling)
