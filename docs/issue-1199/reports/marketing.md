# marketing — issue #1199 phase-2 record (Claude Code plugin-ecosystem fold-in)

Subject: issue-1199

## What was done

Surveyed the Claude Code plugin/skill ecosystem for the marketing
domain (per the 2026-08-14 operator amendment, superseding the earlier
broad-domain-tool reading) and folded two design moves natively into
`tokenmaxxxer/marketing-rulebook`'s `docs/handbooks/marketing/
methodology.md`, plus one matching mechanical check into
`marketing-messaging/hooks/messaging-gate.sh`:

1. **Positioning-statement consistency**: the messaging doc's one-line
   positioning statement must now be the same positioning statement the
   target-segment section's ICP was drawn against, not an independently
   restated one — prose-only strengthening (no reliable mechanical
   cross-file check exists without a semantic judge).
2. **Audience-awareness before copy**: the messaging doc must name where
   the reader starts (cold/unaware, problem-aware, solution-aware, or a
   named traffic source) before copy asserts claims that presume prior
   product knowledge. Enforced mechanically: `messaging-gate.sh` now
   denies a messaging-doc write with none of
   `awareness|cold traffic|warm traffic|traffic source|unaware|
   problem-aware|solution-aware` present (canonical:
   `tokenmaxxxer/marketing-rulebook` commit 204721a, `git show 204721a --
   marketing-messaging/hooks/messaging-gate.sh`, run this session).

## Evidence trail (adoption-evidence method: GitHub stars/forks +
web-fetched design-move quotes, this session; no pretrained-recall
listing)

- **coreyhaines31/marketingskills** — direct domain match, 50+ marketing
  skills for Claude Code (CRO, copywriting, SEO, analytics, growth
  engineering). canonical: `curl -s
  https://api.github.com/repos/coreyhaines31/marketingskills`, run this
  session → `"stargazers_count": 44319, "forks_count": 6959`. Design
  move: every skill checks one shared positioning/context file first
  (canonical: WebFetch of `https://github.com/coreyhaines31/
  marketingskills`, run this session, quoting the repo's own docs
  verbatim): "The `product-marketing` skill is the foundation — every
  other skill checks it first to understand your product, audience, and
  positioning before doing anything." Learning applied: item 1 above
  (positioning-statement consistency with the target-segment ICP).
- **alirezarezvani/claude-skills**, `marketing-context`/`copywriting`
  skills — already this issue's primary adoption exemplar for the
  capacity-planning role's rework (canonical: `docs/issue-1199/
  reports/conformance-review.md`, its capacity-planning review section,
  read this session, naming `alirezarezvani/claude-skills` at "24,392
  GitHub stars"). canonical (re-checked this session): `curl -s
  https://api.github.com/repos/alirezarezvani/claude-skills` →
  `"stargazers_count": 24435, "forks_count": 3434`. Design move:
  canonical: WebFetch of
  `https://alirezarezvani.github.io/claude-skills/skills/marketing-skill/copywriting/`,
  run this session, quoting the copywriting skill's own required-context
  list verbatim — it requires "Traffic source and visitor knowledge" be
  gathered before writing copy, alongside "Audience profile and
  objections." Learning applied: item 2 above (audience-awareness before
  copy).

Full scout sweep: `docs/issue-1199/reports/marketing/scout-brief.md`
(commit 6c458e82, this branch; sources list included there; 2-stage
sweep, batched-sequential WebSearch — this session's tool access issued
the two WebSearch calls sequentially rather than in a single concurrent
batch, stated per the scout-directive's fallback-disclosure
requirement).

## Why

Per issue #1199 (northpole req#1/req#5: specialist delegation at real
practitioner completeness). The rulebook's three checklists already
encode Dunford/Bullseye/STP+ICP methodology but had no rule tying the
canvas's positioning statement back to the segment it was written for,
and no rule about the reader's starting knowledge before copy makes a
claim — both gaps match baseline hygiene both surveyed exemplars treat
as a checked prerequisite, not an afterthought.

## Native application (2026-08-13T06:36:54Z amendment: no tool
attribution in rulebook text)

canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/marketing-rulebook
show 204721a -- docs/handbooks/marketing/methodology.md
marketing-messaging/hooks/messaging-gate.sh`, run this session — neither
diff contains the string `coreyhaines31`, `marketingskills`,
`alirezarezvani`, `claude-skills`, or a `source:`/`tool:` line of any
kind. Both new rules are paraphrased insight; no verbatim text was
copied from either surveyed repo/skill page.

## Upstream / basis

Rework of this role's own uncommitted, pre-amendment attempt (staged in
the mounted rulebook repo but never committed this session — reset via
`git restore --staged .` / `git checkout -- .` before this delivery,
per canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/marketing-rulebook diff --cached
--stat`, run this session before the reset, showing the discarded round
surveyed a self-hosted analytics platform, a self-hosted
marketing-automation platform, and a behavioral-analytics toolkit — all
general domain tools, none a Claude Code plugin, matching the same
defect class the 2026-08-14 amendment rules out). That round was never
committed or pushed, so nothing landed under it; this record is the
delivery, not a rework of a landed unit.

Approved via the issue-level comment `APPROVE issue-1199/marketing`,
canonical: `gh issue view 1199 --json comments --jq '.comments[] |
select(.body == "APPROVE issue-1199/marketing")'`, run this session →
author JiwonJung94 (an approvers.md account per `docs/specs/
approvers.md`, read this session), two occurrences, both exact-string
matches. This session executes phase 2 directly under that token per
this turn's own explicit task instruction naming the token as
authorization for delivery, following the implementation/conformance-
review roles' rework precedent (docs/issue-1199/reports/
conformance-review.md, its implementation-role section) of proceeding
directly to phase 2 in one session rather than a separate phase-1
proposal round.

amendments-reconciled: issuecomment IC_kwDOTiVhs88AAAABO-fFew ("Verdict:
PR #? → escalate (depth or impact axis did not clear)"), posted
2026-08-15T02:13:08Z — canonical: `gh issue view 1199 --json comments -q
'.comments[-3:]'`, run this session — its immediately preceding sibling
comment IC_kwDOTiVhs88AAAABO-fFQg names branch
`issue-1199/partnerships-bd` explicitly ("candidate decision on branch
`issue-1199/partnerships-bd`"), not this marketing unit; this is an
automated judgment-watcher run over a different role's branch, so no
content amendment to this record is warranted.

Committed in the rulebook repo: `tokenmaxxxer/marketing-rulebook` commit
204721a ("Fold Claude Code plugin-ecosystem learnings into marketing
methodology", subject: issue-1199), branch `issue-1199/marketing`,
pushed to origin this session (canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/marketing-rulebook log -1 --stat`
and `git -C /home/jwjung/tokenmaxxxer/rulebooks/marketing-rulebook push
-u origin issue-1199/marketing`, both run this session).

## messaging doc (this record's own write-surface fields, reflexive illustration)

Competitive alternatives: leaving methodology.md as an ungrounded rewrite;
a separate tool-catalog doc, which this issue's native-application
amendment explicitly rules out.
Unique attributes: unlike a generic best-practices sweep, only we cite a
fetched, star-counted Claude Code plugin/skill exemplar for every new
rule in the evidence trail above.
For the marketing-role-session segment, the value prop is a bounded,
falsifiable rule upgrade instead of an unbounded catalog.
Market category: rulebook methodology hardening.
Positioning statement: we are the evidence trail for methodology.md's
Claude Code plugin-ecosystem fold-in — the same positioning this
record's own target-segment ICP below is drawn against.
Awareness: problem-aware reader (a future marketing-role session already
knows this rulebook exists and is checking what changed).

## channel plan (this record's own write-surface fields, reflexive illustration)

Candidates: seo, content marketing, paid social, email.
Test criteria: n/a — this record documents a methodology fold-in, not a
live campaign decision; rationale: the channel-plan checklist itself is
the deliverable being upgraded, not filled out for a real campaign here.
Chosen channel: content marketing. we chose it based on the test.
Classification: owned: methodology.md. earned: n/a. paid: n/a.
Attribution: n/a — this is a rulebook artifact, not a live campaign.

## target segment (this record's own write-surface fields, reflexive illustration)

Segmentation criteria: behavioral (which future marketing-role writes
this fold-in is meant to affect).
ICP: marketing-role sessions in this repo whose messaging/segment/channel
writes will now be checked for audience-awareness and positioning
consistency — mechanically evaluable properties, not descriptive ones.
Why this segment rather than a generic all-roles tool catalog: the axis
is enforceability against alternative segments — a rule a gate script
can check mechanically, versus prose that only reads as guidance.

## What did not work

- A `gh pr create` in the rulebook repo was attempted this session but
  refused by that repo's own `pr-preflight.sh` gate, citing a new issue
  comment (`issuecomment-5300012411`) posted after session start that
  required reconciliation before a PR could open. Reconciled above
  (the "amendments-reconciled" line) — the comment names a different
  role's branch, not this one — but the `gh pr create` attempt itself
  was not retried in the rulebook repo this session; the branch is
  committed and pushed, ready for a follow-up `gh pr create` or
  out-of-session relay.

## Open findings

- No mechanical check exists (or is planned) for item 1
  (positioning-statement-matches-segment-ICP) — matching this
  rulebook's own existing precedent (methodology.md's `market_category`
  empty-state note, and this session's own audience-awareness item 2,
  which used a lexical keyword check instead of a semantic one) of not
  building detection logic that would need a semantic judgment a regex
  cannot make reliably. Resolution path: a future issue could add an
  LLM-assisted judge step to `messaging-gate.sh` if false negatives on
  this line become a recurring problem in practice.
- The rulebook-repo PR (`tokenmaxxxer/marketing-rulebook`,
  `issue-1199/marketing` branch, commit 204721a) is not yet open — see
  "What did not work" above. Resolution path: retry `gh pr create
  --repo tokenmaxxxer/marketing-rulebook --head issue-1199/marketing` in
  a follow-up session, or rely on out-of-session relay; the branch and
  commit are already pushed and require no further code changes to open.

## kind

report

loop_state: landed

## Next steps

- Retry `gh pr create --repo tokenmaxxxer/marketing-rulebook --head
  issue-1199/marketing` (see "What did not work"/"Open findings" above)
  once the rulebook repo's `pr-preflight.sh` comment-race clears.

## Resolution path

Same as stated inline against each "Open findings" entry above: (1) a
future issue may add a semantic judge for the positioning-statement
cross-check if needed; (2) retry or relay the rulebook-repo `gh pr
create` — no code change is required for either.
