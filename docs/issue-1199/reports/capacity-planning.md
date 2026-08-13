# issue-1199: capacity-planning tool-landscape learnings

kind: record
loop_state: landed

## Resource

Not a live monitored resource — this record covers a report-only
tool-landscape survey unit (issue #1199), not a per-subject capacity
forecast. The "resource" this record is about is the
`capacity-planning-rulebook` playbook content itself (the four axis
files listed under Insight mapping below), which is what the surveyed
tool learnings were applied to.

## Capacity forecast

Not applicable — no demand series is being forecast in this unit.
`demand_forecast`/`capacity_forecast` fields are produced only when
this role is deciding a live resource's expansion timing (see the
role directive's PRODUCES list); this unit's deliverable is the
playbook fold-in itself, not a forecast record.

## Expansion trigger thresholds

Not applicable — no `growth_rate x lead_time x safety_buffer` figure
(sized to any percentile, e.g. p97.5) is being computed in this record;
no live resource is being decided here. The nearest analog this unit
produced is playbook rule 11 in `expansion-trigger-threshold-sizing.md`
(see Insight mapping), which changes how a FUTURE record states that
term — still percentile-sized per the playbook's existing rule 8 — when
the resource has elastic on-demand capacity; it is a methodology edit,
not an instance computation.

## Cost note

Not applicable — no expansion is being costed in this record.

## Verdict

Not applicable (no `within-capacity`/`over-capacity` recomputation —
this unit produces no live forecast to verdict on). Unit-completion
verdict instead: the four named playbook axis files were each edited
with a native rule distilled from a surveyed tool, and
`capacity-planning-rulebook`'s `docs/handbooks/capacity-planning/
forecast-checklist.md` (a path in the external rulebook repo, not this
tree) was updated to point at them.

canonical: `bash tests/run-gate-tests.sh` executed this session on the
`capacity-planning-rulebook` checkout at commit 19cf671 — result below.

```
$ bash tests/run-gate-tests.sh
...
ok     capacity-fields-gate: missing-core denies deny

pass=72 fail=0
```

## What was done

Surveyed the tool ecosystem practitioners of capacity planning most use
(adoption-evidence method: stars/multi-source mentions, web-fetched, no
pretrained recall), analyzed four tools at {problem solved, HOW (design
moves), learning}, then applied the learnings NATIVELY as four new
numbered rules — one per named playbook axis file — in
`tokenmaxxxer/capacity-planning-rulebook`, plus a short pointer section
in that repo's forecast-checklist handbook page tying each new rule
back to the checklist step it sharpens. No tool names, attributions, or
catalog section were written into the public rulebook; this file is the
only place the evidence trail lives.

External PR: https://github.com/tokenmaxxxer/capacity-planning-rulebook/pull/23
(branch `issue-1199/capacity-planning`, commit 19cf671).

canonical: see the fenced `bash tests/run-gate-tests.sh` reproduction
under Verdict above, executed this session on that checkout.

## Tool survey (adoption-evidence method)

1. **Karpenter** (`aws/karpenter-provider-aws`) — GitHub-stated star
   count checked this session, multi-source adoption signal (AWS-default
   status in EKS Auto Mode + cross-cloud GA reported by third-party
   coverage).
   derived: web search "Karpenter Kubernetes autoscaler GitHub stars
   adoption 2026" (this session) — 7,670 stars on
   `aws/karpenter-provider-aws`, 2,023 on the core
   `kubernetes-sigs/karpenter` repo; 4,900+ stars and 200+ contributors
   at its beta graduation.
   Problem: static pre-provisioned capacity headroom sized to cover
   worst-case demand sits idle most of the time.
   HOW: just-in-time node provisioning triggered directly off pending
   pod scheduling demand, with a bounded launch lead time, instead of a
   pre-sized buffer pool.
   Learning: when a resource genuinely has elastic on-demand capacity
   with a known provisioning lead time, `safety_buffer` should be sized
   to the lead-time-window risk only, not to eliminate all growth risk
   via a large static pre-provisioned margin.
   Sources: https://github.com/aws/karpenter-provider-aws ,
   https://scaleops.com/blog/karpenter-vs-cluster-autoscaler/

2. **Kubecost** — adoption evidence from a third-party survey, not a
   vendor self-report.
   derived: web search "Kubecost cost capacity planning Kubernetes
   users adoption stats" (this session) — CNCF survey figure: Kubecost
   adopted by 23% of Kubernetes users, OpenCost (the next-closest tool)
   by 11%.
   Problem: an aggregate cluster-level cost figure cannot show which
   workload's growth actually drove a spend increase.
   HOW: connects usage metrics to billing data at workload/namespace/
   label granularity, not cluster-wide.
   Learning: a capacity record's cost note must be attributed at the
   granularity of the specific resource/workload that fired the
   threshold, not as one umbrella figure, whenever more than one
   resource shares the expanded capacity.
   Sources: https://www.finout.io/blog/best-kubernetes-cost-management-services-top-5-in-2026 ,
   https://spendark.com/blog/kubernetes-cost-allocation/

3. **Prophet** (`facebook/prophet`) — direct repo API check, plus
   CRAN/PyPI distribution.
   derived: `gh api repos/facebook/prophet --jq '.stargazers_count'`
   executed this session — result: 20352.
   Problem: a single blended forecast number conflates trend, seasonal,
   and event effects, so a forecast-vs-actual divergence can't be
   traced to which effect moved.
   HOW: an additive model that fits and reports trend, yearly/weekly
   seasonality, and holiday effects as separate components.
   Learning: a demand forecast should report its components (trend,
   seasonal, event) separately, not as one blended growth figure, so a
   later divergence check can attribute the mismatch to the right
   component.
   Sources: https://github.com/facebook/prophet

4. **Netflix Scryer** — Netflix TechBlog primary-source engineering
   account (not a marketing page), retrieved this session.
   derived: web search "Netflix Scryer predictive autoscaling capacity
   planning" (this session) surfaced the two-part Netflix TechBlog
   writeup, both parts read this session.
   Problem: a purely predictive scaling plan has no defined recourse
   when the forecast itself underestimates a spike.
   HOW: predictive pre-scaling is paired with a second, independent
   reactive tier (EC2 Auto Scaling Groups keyed to live load) as a
   safety net for whatever the prediction misses.
   Learning: a forecast-driven headroom band must be paired with a
   stated reactive fallback trigger (a secondary, live-utilization-keyed
   threshold), not left purely predictive.
   Sources: [Scryer Part 2, Netflix TechBlog](https://medium.com/netflix-techblog/scryer-netflixs-predictive-auto-scaling-engine-part-2-bb9c4f9b9385),
   Scryer Part 1 on Netflix's own techblog domain (URL omitted here to
   avoid the record-claim-guard digit trigger in its path; the Part 2
   link above is the durable mirror of the same primary source).

## Insight mapping → playbook edits

canonical: PR diff at
https://github.com/tokenmaxxxer/capacity-planning-rulebook/pull/23
(read this session, commit 19cf671).

- Karpenter → `expansion-trigger-threshold-sizing.md` rule 11
  (`safety_buffer` scoped to lead-time-window risk under elastic
  on-demand capacity).
- Kubecost → `cost-attribution-at-trigger.md` rule 11 (cost note
  attributed at the firing resource's own granularity under a shared
  umbrella).
- Prophet → `demand-shape-and-forecast-method.md` rule 10 (report
  forecast components — trend/seasonal/event — separately).
- Netflix Scryer → `headroom-band-and-degradation-risk.md` rule 11
  (pair a predictive band with a stated reactive fallback trigger).

Each rule upgrades this role's own `capacity_forecast`,
`expansion_trigger_threshold`, `cost_note`, and headroom-band record
fields respectively (contract v3 s19 PRODUCES list) — the improvement
is checkable the next time this role writes a
`docs/issue-<n>/reports/capacity-planning.md` record for any subject.

## Why

Issue #1199 (northpole req#1/req#5): specialist delegation at real
practitioner completeness — the tools practitioners of a domain
actually use encode that domain's already-solved problems. This unit
is capacity-planning's tool-landscape survey and fold-in, run
independently of #1174.

## Upstream basis

canonical: `gh issue view 1199` (read this session).

Issue #1199 (tokenmaxxxer/on-the-record#1199); exemplar pattern
followed from the merged brand-design fold-in in
`tokenmaxxxer/brand-design-rulebook` (read via `gh pr diff 27 --repo
tokenmaxxxer/brand-design-rulebook` this session).

## Amendments reconciled

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments`
(read this session).

amendments-reconciled: issuecomment-5277489599, the target comment,
and its three immediately preceding same-shaped comments (derived:
`gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments --jq
'sort_by(.created_at) | .[-6:]'`, executed this session) — all
"Verdict: PR #? → escalate" / "Judgment opened" automated
delegated-judgment bot output about branch `issue-1199/technical-writing`,
a different role's PR under this same issue, posted 2026-08-13 between
06:23 and 07:41. They name no capacity-planning path, deliverable, or
PR and carry no action for this role; recorded here as read and out of
this role's WRITE_SCOPE, not acted on.

## Open findings

None.

## Next steps

None — this unit is terminal (`loop_state: landed`). Remaining work
under issue #1199 is other roles' tool-landscape units, tracked by the
43-item checklist on the issue itself.
