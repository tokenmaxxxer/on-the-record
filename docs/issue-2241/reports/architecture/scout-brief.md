---
kind: scout-brief
issue: 2241
role: architecture
---

# issue-2241 — scout brief

Mode: batched-sequential fallback (one general-purpose agent, foreground,
ran four WebSearch angles inside a single turn — not four parallel
Agent-tool dispatches). Stated per scout-directive's fallback-disclosure
requirement. Stage count: 1 sweep stage; judge point reached saturation
immediately (see below), so no deepening stage ran.

Angles swept: (1) lease/claim patterns keyed away from actor role, (2)
append-only author-identity under concurrent writers, (3) check-kind
tagging kept distinct from checker identity / self-verification
prevention, (4) staged addressing-scheme cutover with in-flight units.

## Must-bes (what strong systems assume)

- A lease/claim's key is the resource being contended for, never the
  claimant's type — Kubernetes Lease objects key on `holderIdentity`
  (an instance identity) with a separate `leaseDurationSeconds`; job
  queues (Sidekiq/Celery-class) key a claim on the job plus a token, not
  the worker's role.
- Append-only authorship is a field alongside the payload, not folded
  into what the entry IS — event-sourcing convention carries `id`,
  `type`, `payload`, and the producing actor as separate fields.
- Check-kind and checker-identity are separate object graphs — SARIF's
  `run.tool.driver` (who) and `run.tool.driver.rules` (what kind of
  check) are distinct; GitHub branch protection blocks the PR *author*
  specifically from counting as approver, not "the checker" generically.
- A live cutover needs a transparent-proxy/dual-write seam, not a flag
  day — Strangler Fig's routing facade forwards 100% to the old scheme
  first, then migrates incrementally; CDC-tap → dual-write → backfill →
  read-cutover → write-cutover is the recommended per-unit sequence.

## Performance axes strong systems compete on

1. **Renewal/expiry ergonomics** — TTL length, flat-progress detection,
   requeue-without-kill (k8s optimistic `resourceVersion` races;
   sidekiq-unique-jobs' reaper for orphaned locks).
2. **Provenance strength** — plain actor-ID field vs. cryptographic
   per-writer signature for multi-writer audit trails.
3. **Self-verification prevention** — GitHub's author-exclusion is a
   hard platform rule, not configurable-away, but only blocks the
   *author*, not other committers (a known gap some teams patch with
   extra gates).

## Adopt / skip

- **Adopt**: keep lease and author-identity as two separate fields
  rather than combining them into one object — matches angle 1+2's
  pattern of one key per concern.
- **Skip**: cryptographic per-writer signatures for author identity —
  no threat model in this repo calls for tamper-resistance beyond
  git's own commit provenance; adding it would be scope this issue's
  non-goals don't ask for.

## Segment fit

This is an internal dev-automation harness, not a consumer product —
"segment" here is "mature distributed-systems/audit-log practice,"
which the angles above target directly (no consumer-product exemplar
applies).

## Gap line

The current system already has something record-kind-shaped (angle 3 —
`role` today marks that a verification kind happened) and something
author-identity-shaped (angle 2 — `role` also tags who wrote a record),
but it is **missing** a dedicated lease primitive decoupled from actor
type (angle 1 — this repo's roster TTL lease, per the survey, is
real and already built, but keyed on `issue/role`, not on an
identity-free resource key) and **missing** a stated dual-scheme
cutover period for branch/record naming (angle 4 — nothing in the
issue's own staging names an explicit coexistence window for in-flight
branches beyond "state what happens to them," which stage 4's proposal
must supply).

Sources:
- https://www.golinuxcloud.com/operator-leader-election-explained/
- https://carlosbecker.com/posts/k8s-leader-election/
- https://ssushant.me/systemdesign/distributed-task-queue-celery-sidekiq-class-analysis/
- https://www.rubydoc.info/gems/sidekiq-unique-jobs/6.0.12
- https://event-driven.io/en/audit_log_event_sourcing/
- https://medium.com/sundaytech/event-sourcing-audit-logs-and-event-logs-deb8f3c54663
- https://fizalihsan.github.io/technology/eventsourcing.html
- https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/sarif-support-for-code-scanning
- https://medium.com/@aneeqr25/ensuring-fair-code-reviews-how-to-block-self-approval-in-github-pull-requests-6338341e4765
- https://firstprinciplesengineering.tech/01-fundamentals/01-concepts/02-architecture/05-strangler-fig
- https://dev.to/axeldlv/strangler-fig-migration-strategy-on-aws-17l0
- https://theartofcto.com/frameworks/2026-02-06-fig-tree-strangler-pattern-replace-legacy-without-big-bang
