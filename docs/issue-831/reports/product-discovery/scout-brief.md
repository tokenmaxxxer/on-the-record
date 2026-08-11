# Scout brief — issue #831

canonical: this session's own tool-call sequence (2 `WebSearch` calls issued in one message, then one judge point, no further round)
Stages used: 1 sweep (2 parallel WebSearch calls, genuinely concurrent) + judge point. No deepening round: the sweep confirmed rather than complicated the direction already implied by `docs/handbooks/setup.md` (read this session, section "Once, per target repo"), so a second round would not change any build decision (saturation).

## Must-bes (Kano) the field converges on
- Ask before anything destructive or account-scoped (repo creation, push to a remote you don't yet control) — the 2026 agentic-coding-CLI consensus is "ask before touching your main branch / before anything irreversible."
  canonical: [8 AI Coding Agents That Actually Ship Production Code in 2026](https://dev.to/sonotommy/8-ai-coding-agents-that-actually-ship-production-code-in-2026-18ch) ("ask before they touch your main branch")
- GitHub-adjacent AI-agent tooling has visible 2026 incident history from consent/scoping boundaries that were social-engineerable rather than hard-gated — the "GitLost" disclosure shows a GitHub AI agent tricked into acting on private repos.
  canonical: [GitLost: How Researchers Tricked GitHub's AI Agent Into Leaking Private Repos — DevOps.com](https://devops.com/gitlost-flaw-lets-attackers-trick-github-ai-agent-into-leaking-private-repos/)
  This argues against a *loose* self-provision default, not just for asking once.

## Performance axes the field competes on
1. How much the agent can do *after* one-time consent, without re-asking (session-scoped consent vs. re-prompt-every-time).
2. Whether "no consent yet" degrades to a smaller but still-useful mode, vs. a hard stop.

## Adopt / skip
- **Adopt**: one-time, explicit, narrowly-scoped consent at a natural setup boundary.
  canonical: `docs/handbooks/setup.md` (read this session, section "Once, per target repo") — this repo already treats "a GitHub remote," `approvers.md`, and branch protection as three per-target-repo setup items the orchestrator "offers to do ... in conversation" once, up front — this pattern already exists for the other two items; only the remote item lacks an enforcement-side implementation (see Gap line).
- **Skip**: silent/default-on repo auto-creation with no consent gate — contradicted by the field's ask-before-irreversible norm (above) and by this repo's own existing precedent for the other two setup items (same citation).

## Segment fit
on-the-record is not a consumer coding agent; it is an orchestration layer whose target sessions must run *unattended* after handoff (northpole requirement #4).
canonical: `docs/specs/northpole.md` (read this session, section "4. Autonomous completion + human-legible reporting")
The field's UX pattern (ask once, then don't re-ask) transfers directly; the field's incident pattern (GitLost, above) argues for keeping the consent boundary at install/setup time — a moment a human is already present — rather than inventing a new mid-run consent channel a fully unattended target session cannot use anyway.

## Gap line
canonical: `docs/handbooks/setup.md` (section "Once, per target repo") and `spawn.py:4328-4330` (both read this session)
`docs/handbooks/setup.md` already names "a GitHub remote" as one of three setup-time items the orchestrator offers to fill "in conversation" — but `spawn.py::issue_workspace` (the actual enforcement point, `spawn.py:4314-4330`) has no code path that reads or acts on that offer; it only hard `sys.exit`s citing "계약 v3 s10". The must-be ("ask once, up front, not mid-run") is already the documented intent; what's missing is that enforcement doesn't reflect it, and the #830 stall (canonical: `docs/issue-776/reports/execution-observation.md` row #5) happened inside a spawned role session, not the orchestrator's own conversation — a different actor than the one `setup.md` assumes is "in conversation."

Sources:
- https://dev.to/sonotommy/8-ai-coding-agents-that-actually-ship-production-code-in-2026-18ch
- https://devops.com/gitlost-flaw-lets-attackers-trick-github-ai-agent-into-leaking-private-repos/
