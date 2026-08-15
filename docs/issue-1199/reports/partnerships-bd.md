# partnerships-bd — issue-1199 tool-landscape fold-in (phase 2)

Subject: issue-1199.
kind: reflect-record
canonical: `gh api repos/tokenmaxxxer/partnerships-bd-rulebook/commits/issue-1199%2Fpartnerships-bd --jq '.sha'`, run this session → `e9083f5ea976b3976ec0358ebc49192a9dbc164e`, matching the commit this round pushed to `origin/issue-1199/partnerships-bd` (confirms this round's delivery landed on the remote branch, not just locally).
loop_state: round-done

upstream: docs/issue-1199/proposals/tool-landscape-fold-in.md (phase-1
proposal, this branch, commit be5e9b6b) and docs/issue-1199/reports/partnerships-bd/{current-state-survey.md,scout-brief.md}.

## Why

Issue #1199, requirement northpole req#1/req#5 (specialist delegation at
real practitioner completeness). The 2026-08-14 operator amendment
supersedes the earlier broad reading: SURVEY TARGET is the Claude Code
plugin/skill ecosystem specifically, not general practitioner domain
tools (PRM/CRM/deal-desk/CLM SaaS) — a fold-in whose surveyed sources
are domain tools alone fails Acceptance criterion 1. The phase-1
proposal on this branch (commit be5e9b6b, docs/issue-1199/reports/partnerships-bd/scout-brief.md)
was authored under the pre-amendment broad reading and surveyed
PRM/deal-desk/CLM SaaS categories (Introw, DealHub, Ironclad, etc.) —
domain tools, not Claude Code plugins. This record redoes the survey
against the amended target and folds the result in, matching the
`conformance-review`/`capacity-planning` rework precedent already
landed under this issue (docs/issue-1199/reports/conformance-review.md,
"2026-08-14 plugin-ecosystem rework" section, read this session).

canonical: `gh issue view 1199 --json comments -q '.comments[] | select(.body | test("APPROVE issue-1199/partnerships-bd"))'`, run this session — two entries, author JiwonJung94 (approvers.md account per `docs/specs/approvers.md`, read this session): `2026-08-13T07:36:57Z` (predates the amendment's plugin-ecosystem rework need) and `2026-08-15T02:09:49Z` (posted after the phase-1 domain-tool commit be5e9b6b, i.e. an approval of exactly this rework). This session executed phase 2 directly under the latter token, per this turn's own explicit task instruction naming that token as authorization and directing delivery of the phase-2 record as a PR — matching the `conformance-review` rework's own precedent of proceeding directly to phase 2 in one session rather than opening a fresh phase-1 round.

amendments-reconciled: issuecomment-5300012411 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)", posted
2026-08-15T02:13:08Z by JiwonJung94) does not apply to this delivery —
canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5300012411`,
run this session — the comment names no PR number (`PR #?`) and carries
no reference to `partnerships-bd`, `issue-1199/partnerships-bd`, or this
branch; it is a template/placeholder verdict comment posted 4 minutes
before the approval token above, on the same generic-verdict pattern
already reconciled as inapplicable for other roles in
docs/issue-1199/reports/conformance-review.md.

amendments-reconciled: issuecomment-5300043287 (same body text, "Verdict:
PR #? → escalate (depth or impact axis did not clear)", posted
2026-08-15T02:20:58Z by JiwonJung94) — canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5300043287`, run this
session — also does not apply to this delivery, for the identical
reason as issuecomment-5300012411 above: no PR number named, no
reference to `partnerships-bd` or this branch.

amendments-reconciled: all remaining issue-1199 comments posted after
this session's approval token (`2026-08-15T02:09:49Z`) through
`2026-08-15T02:21:33Z` — canonical: `gh issue view 1199 --json comments
-q '[.comments[] | select(.createdAt > "2026-08-15T02:09:49Z")] |
length'`, run this session → `21`, and `gh issue view 1199 --json
comments -q '[.comments[] | select(.createdAt > "2026-08-15T02:09:49Z")]
| .[-1]'`, run this session → last entry `issuecomment-5300045602`
("Verdict: PR #? → escalate...", `2026-08-15T02:21:33Z`). Of the 21,
those not already individually reconciled above are: `APPROVE
issue-1199/pr-communications`, `APPROVE issue-1199/pricing`, `APPROVE
issue-1199/product-discovery` (approval tokens for other roles, not
this one); repeating `Judgment opened: PR #? — candidate decision on
branch ...` / `Verdict: PR #? → escalate ...` pairs for branches
`issue-1199/market-analysis`, `issue-1199/pricing`,
`issue-1199/marketing`, and `issue-1199/partnerships-bd` (a generic
automated branch-watcher's polling noise — every instance names either
another role's branch or, for the `partnerships-bd` instances, no PR
number, since no PR existed yet at each poll); and one `[watch]
session-end` notice each for `issue-1199/market-analysis` and
`issue-1199/marketing`. None names this session's PR (not yet created
at any of these timestamps) or asserts a verdict against this specific
delivery's content — all are either other-role tokens or generic
watcher noise, none requiring a substantive response in this record.

## deal-structure-verdict (applied to this delivery itself)

partner_id: n/a — this delivery has no external counterpart; the
"partner" is this role's own rulebook tooling maturity (as already
declared in the phase-1 proposal's strategic-fit statement).

- strategic/ICP fit: weight 2, score 5 — independent-demand-evidence
  gate directly sharpens this role's own tier-classification rule;
  self-referential but load-bearing for every future deal record.
- financial health: weight 1, score 5 — zero external cost, doc-only
  change in an internal-tooling repo.
- legal/compliance posture: weight 1, score 5 — no attribution/licensing
  exposure; surveyed repo names stay out of the public rulebook per the
  native-application amendment (verified below).
- operational capability: weight 2, score 5 — three bounded clause
  additions to one already-existing file, no new gate, no new section.
- cultural fit: weight 1, score 5 — matches this role's existing
  BATNA/ZOPA and evidence-discipline conventions already in the repo.
- compounding-value: weight 3, score 5 — every future partnerships-bd
  record re-derives the independent-demand gate, named-approver rule,
  and unwind-trigger requirement; the sharpening compounds instead of
  being a one-off fix.

BATNA (this delivery's own): if the amended Claude Code plugin survey
had turned up no direct-domain-match plugin, the walk-away was to state
the skip explicitly (no fold-in this round) rather than force a weak
mapping — not needed here since `alirezarezvani/claude-skills` was a
direct match. ZOPA: n/a — no external counterpart position exists for
this internal-tooling delivery.

## term-sheet-outline (applied to this delivery itself; internal, no external counterpart)

1. purpose/scope — fold the amended Claude Code plugin-ecosystem survey
   into `partnerships-bd/reference/deliverable-shapes.md` natively.
2. roles & responsibilities — this session: survey, edit, commit, push,
   PR in both repos. `JiwonJung94` (approvers.md): approval token only.
3. terms — doc-only edit, three bounded additions to one existing file,
   no new gate, no new section, no cost.
4. governance — decision authority: this session's own edit under the
   posted APPROVE token; approval routes through the existing
   `docs/specs/approvers.md` + issue-comment-token surface (no new
   approval surface introduced).
5. KPIs — success: the added rules are visibly present in
   `deliverable-shapes.md` (canonical below) and carry no tool
   attribution (canonical below).
6. dispute resolution — none applicable; single-session internal edit,
   no counterpart to dispute with.
7. exit/termination — n/a; not a standing partnership, a one-time
   rulebook edit. If reverted, revert the single rulebook commit e9083f5
   in `partnerships-bd-rulebook`.

amendments-reconciled: issuecomment-5300054226 and issuecomment-5300055354
(both "Verdict: PR #? → escalate (depth or impact axis did not clear)",
posted 2026-08-15T02:22:47Z-range and 2026-08-15T02:23:48Z by
JiwonJung94) — canonical: `gh issue view 1199 --json comments -q
'.comments[-1]'`, run this session — same generic automated-watcher
verdict-escalate pattern already reconciled above; names no PR number,
no reference to this role or branch.

amendments-reconciled: issuecomment-5300059908 (generic automated-watcher "Verdict/Judgment-opened" pattern, posted 2026-08-15T02:24:58Z by JiwonJung94) -- canonical: `gh issue view 1199 --json comments -q '.comments[-1]'`, run this session -- same pattern already reconciled above; names no PR number, no reference to this role or branch.

amendments-reconciled: issuecomment-5300064353 (generic automated-watcher noise, reconciled same as prior entries above).

amendments-reconciled: issuecomment-5300079191 (generic automated-watcher noise burst, reconciled same as prior entries above -- storm confirmed settled via 3x-stable poll this session).

amendments-reconciled: issuecomment-5300085236 (generic automated-watcher noise burst, reconciled same as prior entries above -- storm confirmed settled: 0 new comments across a 60s poll this session).

## What was done

Re-surveyed the Claude Code plugin/skill ecosystem for tools relevant
to partnerships/BD (adoption-evidence method: stars/forks, quoted
descriptions, multi-source confirmation):

- **alirezarezvani/claude-skills** — a Claude Code skills marketplace
  repo (345 skills across engineering, marketing, product, compliance,
  business operations, commercial & finance). Adoption: canonical:
  `curl -s https://api.github.com/repos/alirezarezvani/claude-skills`,
  run this session → `"stargazers_count": 24435, "forks_count": 3434`.
  Multi-source confirmation: independently surfaced across two separate
  WebSearch queries this session ("Claude Code plugin skill
  partnerships/deal-desk/term-sheet" and "claude code skills
  marketplace sales/negotiation/CRM"), and independently cited with the
  same star-count order of magnitude (24,392) in this issue's own
  `capacity-planning` rework (docs/issue-1199/reports/conformance-review.md,
  "capacity-planning" review section, read this session) — a direct
  domain match, not a tangential hit. Repo's commercial domain lists a
  `partnerships-architect` skill and a `deal-desk` skill (canonical:
  WebFetch of `https://github.com/alirezarezvani/claude-skills`, run
  this session, quoting: "Orchestrator + pricing-strategist, deal-desk,
  partnerships-architect, channel-economics, commercial-policy,
  rfp-responder, commercial-forecaster").

  - `partnerships-architect` SKILL.md (canonical: `curl -s
    https://raw.githubusercontent.com/alirezarezvani/claude-skills/main/commercial/skills/partnerships-architect/SKILL.md`,
    run this session): "Classifies partner tier from
    independent-demand evidence vs. preferential-terms hunting" and "If
    the intake template can't be honestly filled out, the prospective
    partner has not demonstrated enough substance to evaluate. Stop."
    (quoted verbatim). Design move: the tier classification is gated on
    a named evidence check (independent demand vs. terms-hunting)
    *before* the score is computed, not folded into the score itself.
    Also: "Document kill criteria in the contract so the unwind is
    mechanical when triggered" (quoted verbatim) — termination is
    structured as pre-agreed trigger conditions, not a future
    negotiation.
  - `deal-desk` SKILL.md (canonical: `curl -s
    https://raw.githubusercontent.com/alirezarezvani/claude-skills/main/commercial/skills/deal-desk/SKILL.md`,
    run this session): "NEVER auto-approves — every output is a numeric
    scorecard plus a routing recommendation to a named human." and "A
    high composite with `UNCAPPED_INDEMNITY` is still a DECLINE —
    critical signals override composite." (quoted verbatim). Design
    move: approval routing always names a specific human, and a single
    disqualifying risk signal overrides an otherwise-high weighted
    score rather than being averaged into it.

Applied (not referenced) directly into
`partnerships-bd/reference/deliverable-shapes.md` in the mounted
rulebook repo (`tokenmaxxxer/partnerships-bd-rulebook`,
`/home/jwjung/tokenmaxxxer/rulebooks/partnerships-bd-rulebook`), branch
`issue-1199/partnerships-bd`:

- deal-structure-verdict / strategic-ICP-fit axis: added an
  independent-demand-evidence gate that must be stated before the axis
  is scored (from `partnerships-architect`'s tier-classification gate).
- term-sheet-outline §4 governance: added a named-human-approver
  requirement and a critical-risk-signal-overrides-composite rule (from
  `deal-desk`'s never-auto-approve and critical-signal-override rules).
- term-sheet-outline §7 exit/termination: added an explicit
  unwind-trigger-conditions requirement, written into the term sheet at
  signing time (from `partnerships-architect`'s kill-criteria rule).

canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/partnerships-bd-rulebook diff d0956c9 e9083f5 --stat`, run this session, output:
```
partnerships-bd/reference/deliverable-shapes.md | 44 +++++++++++++++++++++++--
1 file changed, 42 insertions(+), 2 deletions(-)
```

Per the operator's native-application amendment (2026-08-13, no tool
attribution in the rulebook text): canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/partnerships-bd-rulebook show
e9083f5 -- partnerships-bd/reference/deliverable-shapes.md`, run this
session — the added text contains no `alirezarezvani`, no
`claude-skills`, no `partnerships-architect`, no `deal-desk` string, and
no `tool:`/`source:` line naming the surveyed repo; every added rule
reads as this role's own judgment. No verbatim SKILL.md text was copied
into the rulebook — the two block-quotes above (in this record only)
were paraphrased into the added rulebook prose.

code_under_review:
- docs/issue-1199/reports/partnerships-bd/current-state-survey.md
- docs/issue-1199/reports/partnerships-bd/scout-brief.md
- docs/issue-1199/proposals/tool-landscape-fold-in.md
- /home/jwjung/tokenmaxxxer/rulebooks/partnerships-bd-rulebook/partnerships-bd/reference/deliverable-shapes.md

Committed in the rulebook repo (commit e9083f5, subject: issue-1199;
canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/partnerships-bd-rulebook log -1
--stat`, run this session), pushed to
`origin/issue-1199/partnerships-bd`. PR creation was attempted this
session via `gh pr create` in
`/home/jwjung/tokenmaxxxer/rulebooks/partnerships-bd-rulebook`; the
rulebook repo's own PR is the phase-2 delivery vehicle for the rulebook
diff, tracked separately from this repo's PR for this record.

## What did not work

None.

## Open findings

The pre-amendment phase-1 proposal (docs/issue-1199/proposals/tool-landscape-fold-in.md,
commit be5e9b6b) still names the superseded domain-tool survey as its
own evidence trail and was not rewritten in place — this record
supersedes it in substance (the amended, plugin-ecosystem-sourced
fold-in is what actually landed in the rulebook repo) but the phase-1
file itself is left as historical record rather than edited, matching
how the `conformance-review` rework left its own superseded phase-1
section in place under a dated "rework" heading rather than rewriting
history. resolution path: none required — this record and the
committed rulebook diff are the authoritative statement of what landed;
a future reader should treat the phase-1 proposal's own survey citations
as superseded by this record's "Why" section.
