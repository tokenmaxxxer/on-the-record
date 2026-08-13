kind: report
subject: issue-1199
doc-type: reference

# customer-support — issue #1199 current-state survey

## Governing basis

Issue #1199 (northpole req#1/req#5): survey the plugins/tools
practitioners in this role's domain most use, extract the design moves
each embodies, and fold distilled learnings into the rulebook as this
role's own native rules — no per-tool attribution in the public
rulebook, provenance kept only in this on-the-record trail.

## Rulebook write surface

canonical: git -C /tmp/csr-1199 log -1 --format=%H (this turn's tool transcript, clone of tokenmaxxxer/customer-support-rulebook at main)
`tokenmaxxxer/customer-support-rulebook` main carries eight machine-
enforced plugins (`customer-support-escalation-path`,
`customer-support-evidence-metric`, `customer-support-five-whys`,
`customer-support-kcs`, `customer-support-phase1-order`,
`customer-support-playbook-scenario`, `customer-support-record-fields`,
`customer-support-sla-tier`) plus one combined substantive deliverable
file, `customer-support/handbook.md`.

canonical: `find /tmp/csr-1199 -maxdepth 1 -iname playbook` (this turn's tool transcript) returned empty on a fresh clone of `origin/main`
No separate `playbook/*.md` axis files exist on `main` — those exist
only on the local `issue-1174/customer-support` working copy checked
out under `/home/jwjung/tokenmaxxxer/rulebooks/customer-support-
rulebook` (`git status` there this turn shows current branch
`issue-1174/customer-support`, tracking `origin/issue-1174/customer-
support`, a branch distinct from `origin/main`), so that content is
not yet on `main`. The fold-in write surface for this issue is
`handbook.md` itself, the same single-file convention brand-design's
`methodology.md` fold-in used.

## Handbook shape already in place

`handbook.md` already covers: §1 Impact×Urgency SLA-tier table, §2
three-tier (L1-L3) escalation path, §3 four playbook scenarios (A-D),
§4 evidence-metric (FCR/CSAT) tie-in, §5 5-whys recurring-pattern
check, §6 record fields (`ticket_id`/`csat_score`/`resolution_summary`
+ loop_state vocabulary).

## Gaps this fold-in targets

1. Escalation path (§2) starts at L1 (human triage) — no tier models a
   pre-human automated/self-serve deflection step, even though a
   meaningful share of inbound tickets are resolvable without ever
   reaching L1.
2. Playbook scenarios (§3) state a customer-facing script but no
   accompanying structured ticket actions (tag/priority/macro id) — a
   resolution is not reproducible by another agent without
   reconstructing the same steps from the prose alone.
3. Playbook scenarios (§3) have no "check for an existing article/macro
   before drafting" step — nothing prevents the same resolution being
   free-composed from scratch every time the same trigger recurs.
4. Record fields (§6) require `csat_score` as a real value but say
   nothing about *when* the survey producing it fires relative to
   ticket close, nor which scenario it should be attributable to —
   `resolution_summary` (§6) does not name the resolving scenario.

These four gaps are the scout's targets.
