# issue-2548 — architecture scout brief

Mode: batched web search, one stage, two parallel `WebSearch` calls in
one turn (angle 1: identity/authorization/naming separation patterns;
angle 2: capability-based / attribute-based alternatives to a fixed
role table). Aimed at the survey's open gap: whether separating
identity from authorization from naming (this design's alt-C) is a
recognized pattern, or an invented one, before committing to it.

## Must-bes the field agrees on

- Identity and authorization are treated as distinct concerns with
  distinct owners/lifecycles in mainstream IAM literature — identity is
  established first and is comparatively stable; authorization is
  decided against an already-trusted identity and can change
  independently of it (source: nhimg.org FAQ, OneLogin).
- OAuth's resource-server/authorization-server split is the field's
  canonical instance of this: the party deciding access must be
  separable from the party naming/hosting the resource (source:
  nhimg.org FAQ).

## Performance axes the strong examples compete on

- Closed-enum vs. declarative authorization: RBAC (identity resolves to
  a fixed role, then to fixed permissions) is explicitly contrasted in
  the field with ABAC/PBAC, which grant access from declared
  attributes/policies instead of a role lookup (source: Zentera RBAC
  guide via search summary).
- Decoupling the authorization service from the application/session
  layer at scale — cited example: Slack separated its RBAC service from
  the web app specifically so new roles/permissions could be added
  without touching session/business logic (source: Stytch RBAC blog via
  search summary).

## Adopt / skip

- Adopt: identity (who) / authorization (what they may write) as
  separate data, authorization sourced from a declared, per-session
  value rather than a static closed-enum table — matches ABAC/PBAC's
  move away from role-only lookup, and matches this design's roster-
  declared `write_scope` (Authorization section of `architecture.md`).
- Skip: full ABAC (arbitrary attribute-matching policy engine) — this
  repo's `write_scope` is a short glob allow-list per session, not a
  general policy language; adopting full ABAC would be a much larger
  change than the issue asks for and reintroduces exactly the kind of
  new abstraction the issue's non-goals warn against.

## Segment fit

This is an internal infrastructure identity model, not a product
surface — the closest fit is the IAM/access-control literature's
identity/authorization split, not a product-category comparison; scout
therefore targeted a pattern class, not competitor products.

## Gap line

What current state already meets: fail-closed authorization
(`gates.py:915-916`, `924-925`) already matches the field's
"deny-unless-matched" norm — no gap there. What was missing before this
session: current state coupled identity, authorization, and naming into
one string (`role`) with no declared/attribute-based alternative source
— the gap this design's Authorization section closes by moving
`write_scope`'s source to a roster-declared value.

Sources:
- [How should security teams separate authentication from authorization in practice?](https://nhimg.org/faq/how-should-security-teams-separate-authentication-from-authorization-in-practice/)
- [Authentication vs. Authorization: What's the Difference? | OneLogin](https://www.onelogin.com/learn/authentication-vs-authorization)
- [What is role-based access control (RBAC)? - Stytch](https://stytch.com/blog/what-is-rbac/)
- [Role-Based Access Control (RBAC) Zero Trust guide - Zentera](https://www.zentera.net/cybersecurity/role-based-access-control-rbac-zero-trust-guide)
