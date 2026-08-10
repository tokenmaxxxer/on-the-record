# issue-573 — research survey: delegated judgment / tiered approval in existing methodologies

market_argument_supplied: false

This is Step 1 of issue #573 only: a research survey of how existing methodologies and systems
handle delegated judgment / tiered approval. It does not design a mechanism for this repository.
No verdict, no recommendation, no candidate comparison — that is deferred to the proposal that
follows, per the operator's explicit sequencing directive ("RESEARCH FIRST ... and only then
converge").

## Method

Four independent research angles, run as parallel background agents with live web search, one
per named methodology class in the issue: (1) ITIL/CAB risk-based change management, (2)
code-review auto-merge / policy-as-code, (3) aviation and medical delegation protocols, (4)
RFC/ADR-based governance (ASF lazy consensus, Python PEP process, IETF rough consensus). Each
angle reports the three things the issue asks for: what auto-decides vs escalates and on what
recorded criteria, how the delegation rule itself is audited/corrected, and known failure modes.
Findings are graded per angle by source strength (primary regulatory/standards text and vendor
docs above engineering blog posts above tertiary/community summaries) — see the grading table at
the end.

## 1. ITIL / Change Advisory Board (risk-based change management)

**Auto-decided vs escalated.** ITIL 4 defines three change types — Standard (pre-authorized),
Normal (case-by-case, itself split by risk into Major/Significant/Minor), and Emergency —
<source: https://wiki.en.it-processmaps.com/index.php/Change_Management>. A change qualifies for
the pre-authorized Standard tier only if three conditions hold together: the procedure is fully
documented, the risk was formally accepted in advance, and prior runs proved the outcome
predictable; the risk assessment happens once, at template-creation/modification time, not per
instance — <source: http://www.itilfromexperience.com/How+is+a+Standard+Change+Pre-Approved>.
ITIL 4 states plainly that "low-risk or standard changes can be approved automatically or by
delegated change authorities" — <source: https://www.novelvista.com/blogs/it-service-management/itil-change-types>.
ServiceNow operationalizes the criterion as a numeric risk score (a Change Risk Calculator over
predefined properties/conditions, or an equivalent questionnaire) that routes a change to
auto-approval or to CAB — <source: https://www.servicenow.com/community/developer-blog/risk-assessment-in-change-management/ba-p/3340201>.
Standard changes still get logged for audit even though they skip CAB —
<source: https://blogs.helixops.ai/changes-types-standard-vs-normal-vs-emergency-change/>.

**Auditing the delegation rule.** Post-Implementation Review is a named sub-process whose
objective includes verifying the history is complete and that mistakes get analyzed into lessons
learned — <source: https://wiki.en.it-processmaps.com/index.php/Change_Management>. The standard-
change catalog itself is periodically reviewed for retirement/withdrawal and reassessed against
business/regulatory change — <source: https://www.servicenow.com/community/itsm-forum/post-implementation-review-high-risk-change/td-p/668995>.
Any edit to a standard-change procedure forces a full new risk assessment before re-authorization
— <source: http://www.itilfromexperience.com/How+is+a+Standard+Change+Pre-Approved>.

**Failure modes.** CAB rubber-stamping: RFCs arrive without impact assessments, so the board has
no basis to reject and treats CAB as a compliance checkbox; contributing causes cited are change
managers lacking authority to defer, implementers bypassing submission, and shipping pressure
overriding board judgment — <source: https://onplana.com/blog/change-control-board-that-works>.
Membership scope creep: CAB grows to include every conceivably-affected stakeholder, slowing
decisions and dropping attendance — <source: https://faddom.com/change-advisory-boards-in-2026-roles-challenges-and-best-practices/>.
Catalog drift: without periodic review/retirement, standard-change templates can persist or widen
past the low-risk conditions that originally justified pre-authorization (implicit control
failure) — <source: https://www.servicenow.com/community/itsm-forum/post-implementation-review-high-risk-change/td-p/668995>.

## 2. Code-review auto-merge / policy-as-code (merge queues, CODEOWNERS, OPA)

**Auto-decided vs escalated.** Branch protection/rulesets require N approvals, required status
checks, and optionally CODEOWNERS approval before merge is even eligible; auto-merge only fires
once every condition is green — <source: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners>,
<source: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule>.
CODEOWNERS maps path globs to required reviewers, making the escalation criterion path/ownership-
based rather than diff-size-based — <source: https://www.aviator.co/blog/code-reviews-at-scale/>;
Chromium's OWNERS system is a real-world precedent for the same path-scoped delegation —
<source: https://chromium.googlesource.com/chromium/src/+/main/docs/code_review_owners.md>. Merge
queues test each PR against a speculative merge of the target plus every PR ahead of it in queue
order, evicting and re-testing on any failure — <source: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue>.
GitLab approval rules require a minimum number of eligible approvers per protected branch and are
machine-marked "Auto approved" when structurally unsatisfiable (sole eligible approver is the
author, or the required-approvals count exceeds the eligible-approver count) —
<source: https://docs.gitlab.com/user/project/merge_requests/approvals/rules>. OPA/Gatekeeper
encodes the decision criteria as Rego constraints evaluated against structured input at admission
time or in CI — <source: https://www.wiz.io/academy/application-security/open-policy-agent-opa>,
<source: https://www.openpolicyagent.org/ecosystem/entry/gatekeeper>.

**Auditing the delegation rule.** Only admin/owner-permission users can configure branch-
protection enforcement of CODEOWNERS, but the CODEOWNERS file itself is only protected from
unreviewed edits if it is covered by its own CODEOWNERS entry —
<source: https://www.aviator.co/blog/code-reviews-at-scale/>; GitHub has since added a dedicated
"required reviewer rule" (generally available since February 2026) to close this gap —
<source: https://github.blog/changelog/2026-02-17-required-reviewer-rule-is-now-generally-available/>.
GitLab lets approval-policy settings be enforced instance-wide or group-wide, overriding weaker
project-level settings — <source: https://docs.gitlab.com/user/application_security/policies/merge_request_approval_policies/>.
OPA/Gatekeeper policies live as versioned files in git, so their change history is auditable
through ordinary source control and CI (Conftest) rather than a dedicated policy-review workflow
— <source: https://secure-pipelines.com/ci-cd-security/policy-as-code-ci-cd-opa-rego-security-gates/>.

**Failure modes.** Rubber-stamping under backlog pressure: one telemetry finding cited that the
large majority of prompts in manual-review mode were approved reflexively, without actual review
— <source: https://bryanfinster.substack.com/p/ai-broke-your-code-review-heres-how>. Structural
auto-approval as a documented bypass path in GitLab (see above) —
<source: https://docs.gitlab.com/user/project/merge_requests/approvals/rules>. CODEOWNERS
drift/staleness is flagged directly as a scannable misconfiguration by Prisma Cloud —
<source: https://docs.prismacloud.io/en/enterprise-edition/policy-reference/ci-cd-pipeline-policies/github-cicd-pipeline-policies/gh-code-owners-review-not-required-tomerge>.

## 3. Aviation and medical delegation protocols

**Auto-decided vs escalated.** Aviation MEL: each inoperative item is pre-classified dispatchable
or not, with recorded conditions attached to the MEL entry —
<source: https://pilotinstitute.com/what-is-mel/>. Below the single-item level, judgment escalates
to the pilot-in-command: "the decision as to whether or not to accept for flight an aircraft which
has multiple unserviceabilities which would individually be allowable by MEL provisions ultimately
rests with the designated aircraft commander" — <source: https://skybrary.aero/articles/minimum-equipment-list-mel>.
Deferral is a joint, logged act between maintenance and the pilot-in-command —
<source: https://www.ctsys.com/minimum-equipment-list-mel-pilots-guide/>. Certification functions
are separately delegated wholesale to an authorized organization (e.g. Boeing's ODA unit acting
"on behalf of the FAA") rather than decided case by case —
<source: https://www.congress.gov/crs-product/IF12843>. Medicine: delegation is instrument-based
— a written, dated, physician-signed protocol or Prescriptive Authority Agreement enumerates
exactly which acts an NP/PA may perform independently —
<source: https://www.texmed.org/Template.aspx?id=45849>; standing orders serve the same
auto-decide function for defined, protocolized situations, developed and approved by medical,
pharmacy, and nursing leadership against evidence-based guidelines —
<source: https://nursing.wa.gov/sites/default/files/2022-07/StandingAndVerbalOrders.pdf>. Anything
outside the enumerated scope escalates to the supervising physician.

**Auditing the delegation rule.** Medical delegation agreements require mandatory annual
re-review/re-signature by both parties — <source: https://www.hhs.texas.gov/handbooks/primary-health-care-program-policy-manual/5300-prescriptive-authority-agreements-clinical-protocols-standing-delegation-orders-client>.
Aviation ODA delegation is corrected reactively via federal audit: DOT OIG found "management and
oversight weaknesses limit FAA's ability to assess and mitigate risks with the Boeing ODA,"
triggering a federal notice requiring ODA holders to eliminate undue interference —
<source: https://www.oig.dot.gov/sites/default/files/FAA%20Certification%20of%20737%20MAX%20Boeing%20II%20Final%20Report%5E2-23-2021.pdf>.

**Failure modes.** Checklist complacency / automation complacency — "signing off on procedures
without thorough verification," over-reliance on automation reducing vigilance —
<source: https://www.acclivix.com/casestudies/normalization-of-deviance>,
<source: https://nbaa.org/aircraft-operations/safety/human-factors/strengthening-safety-a-look-at-human-factors-in-business-aviation/>.
Normalization of deviance: "in the absence of immediate adverse consequences, the unacceptable
becomes acceptable" — <source: https://en.wikipedia.org/wiki/Normalization_of_deviance>. Scope
creep of delegated authority with weak oversight: the Boeing 737 MAX case is the canonical
documented failure of a delegation-heavy certification model going undetected until fatal crashes,
with a later post-incident audit again finding noncompliance despite years of self-certification
— <source: https://www.oig.dot.gov/sites/default/files/FAA%20Certification%20of%20737%20MAX%20Boeing%20II%20Final%20Report%5E2-23-2021.pdf>,
<source: https://www.faa.gov/newsroom/updates-boeing-737-9-max-aircraft>.

## 4. RFC/ADR-based governance (ASF lazy consensus, Python PEP, IETF rough consensus)

**Auto-decided vs escalated.** ASF default mode is lazy consensus for most day-to-day decisions:
announce intent, wait roughly three days, silence counts as approval —
<source: https://community.apache.org/committers/decisionMaking.html>. Formal voting is reserved
for named triggers: releases, adding a committer/PMC member, and code changes under
Review-Then-Commit — lazy consensus is explicitly disallowed there —
<source: https://www.apache.org/foundation/voting.html>. Two vote types carry different
thresholds: Consensus Approval (code) needs a minimum of three "+1" votes and zero "-1" votes, any
single "-1" being a binding veto; Majority Approval (releases) needs at least three affirmative
PMC votes with more affirmative than negative, and releases cannot be vetoed — same source. A
veto is only valid with a technical justification; an unsubstantiated "-1" carries no weight —
same source. Python PEP 1 and PEP 13: routine PEP review is delegated to a PEP-Delegate a
Steering Council approves per-PEP, while the Council reserves full-body votes for un-delegated PEP
accept/reject, code-of-conduct actions, project asset management, and ejecting a core team member
(a two-thirds supermajority) — <source: https://peps.python.org/pep-0013/>. IETF (RFC 2418): a WG
Chair decides at their discretion when "rough consensus" (dominant view, not a vote count) has
been reached and issues WG Last Call, a recorded two-week procedural gate —
<source: https://datatracker.ietf.org/doc/html/rfc2418>,
<source: https://en.wikipedia.org/wiki/Rough_consensus>.

**Auditing the delegation rule.** PEP 13 amendments to the governance document itself require a
two-thirds supermajority over a two-week core-team vote (only non-substantive roster/history
edits skip voting), and codifies a Vote of No Confidence procedure that can remove a council
member or the whole council by the same threshold — <source: https://peps.python.org/pep-0013/>.
IETF decisions, including a chair's rough-consensus call, are appealable under RFC 2026 section
6.5 — chair/AD, then IESG, then IAB, which can annul an IESG decision —
<source: https://www.ietf.org/standards/process/appeals/>,
<source: https://tools.ietf.org/html/rfc2026>. ASF lazy-consensus thresholds are set and amended
per-project in each project's own Bylaws page rather than centrally (e.g. Apache ORC requires at
least one "+1" and no "-1"s; Apache Hadoop requires only no "-1"s) —
<source: https://cwiki.apache.org/confluence/display/KAFKA/Bylaws>,
<source: https://orc.apache.org/develop/bylaws/>, <source: https://hadoop.apache.org/bylaws.html>.

**Failure modes.** Warnock's Dilemma: silence is structurally ambiguous — agreement, apathy,
non-comprehension, or nobody saw the post — undermining "silence = consent" as a real signal —
<source: https://en.wikipedia.org/wiki/Wikipedia:Silence_and_consensus>. Late-breaking objections:
passive review lets objections surface only after significant implementation work, causing costly
rework that active review would have caught earlier —
<source: https://communityrule.info/modules/lazy_consensus/>. Scope creep of the lazy-consensus
tier: practitioner guidance explicitly restricts it to low-stakes, reversible decisions in
high-trust, well-documented environments, implying misuse on high-stakes/irreversible changes is
a recognized failure — same source. Veto abuse is checked but not eliminated by the
justification requirement — ASF's own acknowledgment that an unjustified veto "carries no weight"
is itself an admission that bad-faith vetoes are anticipated —
<source: https://www.apache.org/foundation/voting.html>. IETF's rough-consensus standard
deliberately avoids a mechanical vote count to prevent gaming, but this makes the outcome
dependent on individual chair judgment, a documented locus of dispute the RFC 2026 section 6.5
appeal path exists to remedy — <source: https://en.wikipedia.org/wiki/Rough_consensus>,
<source: https://www.ietf.org/standards/process/appeals/>.

## Cross-cutting grading

| Angle | Source strength | Auto-tier criterion is recorded, not tacit | Delegation rule has a named audit/correction loop | Failure modes documented from real incidents (not just theory) |
|---|---|---|---|---|
| ITIL/CAB | High — vendor (ServiceNow) plus ITSM community docs, no single primary standard body cited | Yes — numeric risk score / documented template preconditions | Yes — Post-Implementation Review plus periodic catalog review | Partial — practitioner blog account, not an audited incident |
| Auto-merge / policy-as-code | High — GitHub/GitLab primary docs plus OPA docs plus one real precedent (Chromium OWNERS) | Yes — path ownership, required checks, Rego constraints | Partial — mostly "protect the policy file too," not a formal review cadence | Yes — reflexive-approval telemetry finding plus GitLab's own documented bypass path |
| Aviation/medical | Very high — FAA/DOT OIG federal documents, hospital/state policy manuals | Yes — MEL entries, written delegation protocols/standing orders | Yes — annual re-signature (medical); reactive federal audit (aviation) | Yes — Boeing 737 MAX is a fully investigated, named incident |
| RFC/ADR governance | Very high — ASF/IETF/PEP primary process documents | Yes — explicit vote-type/trigger lists per body | Yes — PEP 13 supermajority amendment plus Vote of No Confidence; IETF appeals chain | Partial — Warnock's Dilemma and late-objection risk are named patterns, not one investigated incident |

## Cross-cutting observations (descriptive, not a recommendation)

- Every methodology surveyed separates the auto-tier **criterion** (what qualifies) from the
  **rule that sets the criterion** (who may change it, and how often it is re-checked) — none of
  the four treats the auto-tier as self-maintaining. This directly matches the issue's requirement
  that "the delegation rule itself" be auditable, not just the individual decisions.
- Two failure modes recur across all four independent domains: (a) rubber-stamping — the
  escalation path exists but the human treats it as a formality (CAB, code review, medical/
  aviation automation complacency, IETF chair judgment under social pressure); (b) scope creep of
  the auto tier — the pre-approved/delegated category widens past what its original risk
  justification covered (ITIL catalog drift, GitLab's auto-approve-when-unsatisfiable bypass,
  ODA/Boeing, lazy-consensus misuse on high-stakes changes).
- The domains with the strongest documented audit loop (medicine's mandatory annual re-signature,
  Python's PEP 13 supermajority amendment) are also the domains where the delegation instrument is
  a single, explicit, dated document — suggesting (as an observation to carry into later steps,
  not a decision made here) that auditability tracks how legible the delegation rule's own record
  is, independent of which axis (risk, depth, path-ownership) it delegates on.
- No methodology surveyed found or claimed a way to eliminate rubber-stamping or scope creep
  outright; every mitigation found (justification requirements, periodic re-review, protecting the
  policy file itself, federal audit) is a detection/correction mechanism applied after the fact,
  not a design that prevents the failure mode from arising.

## Scope and what this survey does not do

This document is Step 1 only. It surveys the four required domains with primary-source citations
per the acceptance criterion, and stops there. It does not propose a depth axis, an impact grade,
an expert-role-evaluation format, or any combination of the two required by the issue — that
convergence is explicitly deferred to later steps (product-discovery, architecture,
implementation) per the operator's sequencing directive and the issue's execution plan.

## Sources

```
https://wiki.en.it-processmaps.com/index.php/Change_Management
http://www.itilfromexperience.com/How+is+a+Standard+Change+Pre-Approved
https://www.novelvista.com/blogs/it-service-management/itil-change-types
https://www.servicenow.com/community/developer-blog/risk-assessment-in-change-management/ba-p/3340201
https://blogs.helixops.ai/changes-types-standard-vs-normal-vs-emergency-change/
https://www.servicenow.com/community/itsm-forum/post-implementation-review-high-risk-change/td-p/668995
https://onplana.com/blog/change-control-board-that-works
https://faddom.com/change-advisory-boards-in-2026-roles-challenges-and-best-practices/
https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule
https://www.aviator.co/blog/code-reviews-at-scale/
https://chromium.googlesource.com/chromium/src/+/main/docs/code_review_owners.md
https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue
https://docs.gitlab.com/user/project/merge_requests/approvals/rules
https://docs.gitlab.com/user/application_security/policies/merge_request_approval_policies/
https://www.wiz.io/academy/application-security/open-policy-agent-opa
https://www.openpolicyagent.org/ecosystem/entry/gatekeeper
https://github.blog/changelog/2026-02-17-required-reviewer-rule-is-now-generally-available/
https://secure-pipelines.com/ci-cd-security/policy-as-code-ci-cd-opa-rego-security-gates/
https://bryanfinster.substack.com/p/ai-broke-your-code-review-heres-how
https://docs.prismacloud.io/en/enterprise-edition/policy-reference/ci-cd-pipeline-policies/github-cicd-pipeline-policies/gh-code-owners-review-not-required-tomerge
https://pilotinstitute.com/what-is-mel/
https://skybrary.aero/articles/minimum-equipment-list-mel
https://www.ctsys.com/minimum-equipment-list-mel-pilots-guide/
https://www.congress.gov/crs-product/IF12843
https://www.texmed.org/Template.aspx?id=45849
https://nursing.wa.gov/sites/default/files/2022-07/StandingAndVerbalOrders.pdf
https://www.hhs.texas.gov/handbooks/primary-health-care-program-policy-manual/5300-prescriptive-authority-agreements-clinical-protocols-standing-delegation-orders-client
https://www.oig.dot.gov/sites/default/files/FAA%20Certification%20of%20737%20MAX%20Boeing%20II%20Final%20Report%5E2-23-2021.pdf
https://www.acclivix.com/casestudies/normalization-of-deviance
https://nbaa.org/aircraft-operations/safety/human-factors/strengthening-safety-a-look-at-human-factors-in-business-aviation/
https://en.wikipedia.org/wiki/Normalization_of_deviance
https://www.faa.gov/newsroom/updates-boeing-737-9-max-aircraft
https://community.apache.org/committers/decisionMaking.html
https://www.apache.org/foundation/voting.html
https://peps.python.org/pep-0013/
https://datatracker.ietf.org/doc/html/rfc2418
https://en.wikipedia.org/wiki/Rough_consensus
https://www.ietf.org/standards/process/appeals/
https://tools.ietf.org/html/rfc2026
https://cwiki.apache.org/confluence/display/KAFKA/Bylaws
https://orc.apache.org/develop/bylaws/
https://hadoop.apache.org/bylaws.html
https://en.wikipedia.org/wiki/Wikipedia:Silence_and_consensus
https://communityrule.info/modules/lazy_consensus/
```

Stage count: one sweep stage (four parallel angles, genuinely concurrent background agents), zero
deepening stages — each angle returned decision-relevant, saturated findings directly (multiple
independent primary sources converging on the same criterion/audit/failure-mode pattern per
domain), so a second round was judged not to change any build decision at this research stage.
Mode: parallel (Agent tool, one message, four concurrent dispatches).
