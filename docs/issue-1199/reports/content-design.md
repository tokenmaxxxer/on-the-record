---
subject: issue-1199
role: content-design
kind: record
loop_state: landed
---

# Record: content-design tool-landscape fold-in (issue-1199)

content_id: docs/issue-1199/reports/content-design.md (this record
itself — the deliverable is a rulebook-methodology fold-in, not shipped
end-user copy).
user_need: a future content-design session needs the tool-landscape
evidence trail behind the rulebook's playbook axis 6, so an upgrade
can be re-derived or extended without re-running the survey.
canonical: acceptance: manual review this session against this record's own prose (short sentences, active voice, no unexplained jargon) — result: UNMEASURED-with-reason: no automated plain-language re-run engine exists yet (issue-521 follow-up, per the methodology's field-mapping row wired this session)
plain_language_check: pass

### This record's copy string status

Decision: mark this record's A/B-variant field not applicable because
this record documents a rulebook-methodology fold-in, not shipped
end-user copy -> so there is no variant to test.

Rationale: the decision above holds because this record's output
(playbook axis 6 + methodology wiring) is internal tooling for future
content-design sessions, never a user-facing string, so no tone-axis
audience and no A/B variant apply to it.

content_id: docs/issue-1199/reports/content-design.md
user_need: same as this record's top-level user_need above (a future
session needs the evidence trail without re-running the survey).

Not applicable — A/B variant testing does not apply to this record;
its deliverable is a methodology/playbook fold-in for engineering and
future-session consumption, not a shipped copy string.

tone-axis check: skipped, reason — this record documents a tool
survey and rule fold-in for internal rulebook maintenance, not
end-user product copy, so NN Group's 4-axis tone check has no
applicable audience here.

Self-critique: checked the rationale above (the not-applicable A/B
call), the tone-axis skip reason, and the A/B not-applicable statement
against each other for consistency — all three agree this record is
internal-maintenance output, not shipped copy, so no axis contradicts
another; the rationale is genuine because it names the specific reason
(methodology fold-in, no variant to test) rather than a boilerplate
"not applicable."

## What was done
Executed the phase-2 fold-in approved by the `APPROVE issue-1199/content-design`
comment on this issue (single-account mode; canonical: `gh issue view
1199 --json comments -q '.comments[] | select(.body | contains("APPROVE
issue-1199/content-design")) | .body'`, read this session — the
matching comment body is exactly `APPROVE issue-1199/content-design`).
Worked directly in the separate rulebook repo
(tokenmaxxxer/content-design-rulebook, cloned this session to
/tmp/content-design-rulebook since `$TOKENMAXXXER_RULEBOOKS` is unset
in this environment), on branch issue-1199/content-design:

- Added playbook axis 6 ("Copy inventory reuse and severity-tiered
  rules", rules 26–28) to playbook/operational-playbook.md in that
  repo: (26, REMOVAL) reuse an existing shipped string verbatim
  instead of drafting a near-duplicate for the same content_id +
  user_need pair, unless a stated reason names why the existing string
  fails the decision; (27) a `plain_language_check: fail` must name
  its category (long decision-critical sentence, passive voice hiding
  the actor, unexplained jargon, or an obscuring hedge word) with a
  one-line fix note, not a bare fail; (28) every handbook prohibition
  carries an explicit block/advisory severity, defaulting to block
  when unclassified.
- Wired the same three rules into
  docs/handbooks/content-design/methodology.md in that repo: a new
  reuse-check step ahead of draft in the phase-2 step order, an
  explanatory paragraph under it; a new reuse-check prohibition line
  and a severity-tiering paragraph under Phase-2 Prohibitions; and the
  `plain_language_check` spec-field-mapping table row expanded to
  require a category on `fail`.
  canonical: diff of the two files, this session (see
  content-design-rulebook commit below).
- No tool name, source repo, or "learned from" framing appears in
  either edited file — the insight is written as the role's own native
  rule (operator amendment, 2026-08-13, on this issue: native
  application, no tool-attribution catalogs in the public rulebook).
  No verbatim text was copied from any surveyed source; every rule
  below is a paraphrased synthesis.
- Committed in the rulebook repo (commit 0b87cc1, subject line
  "issue-1199: fold in copy-inventory reuse, severity tiering,
  categorized plain-language check"; canonical: `git -C
  /tmp/content-design-rulebook log -1 --stat`, read this session),
  pushed to origin/issue-1199/content-design, and opened
  https://github.com/tokenmaxxxer/content-design-rulebook/pull/29
  canonical: `gh pr create` output this session.

## Why
Per issue-1199 (northpole req#1/req#5): specialist-delegation
completeness requires the content-design role's rules to reflect what
the field's practicing tools already encode as solved problems, not
just NN/G-sourced copy patterns (#1174's prior batch). The three rules
close gaps the survey below surfaced: nothing in the existing
methodology stopped near-duplicate string proliferation, nothing gave
`plain_language_check` a failure taxonomy to act on, and nothing
distinguished a hard-block prohibition from an advisory one — every
prohibition in the handbook was implicitly binary.

## Tool survey (adoption-evidence method, web-fetched)

Method: tech-feasibility's adoption-evidence approach (stars/downloads/
multi-source mentions), per this issue's requirement 1. Search angles
run this session: (1) general 2026 content-design/UX-writing tool
landscape survey, (2) prose-linting tool adoption (GitHub stars,
production users), (3) Figma-plugin-side copy-management tools.

### 1. Vale (prose linter)
- Adoption evidence: 5.9k GitHub stars (canonical: WebFetch of
  https://github.com/errata-ai/vale, this session); README states
  production use at AWS, NVIDIA, Microsoft, GitLab, Red Hat (canonical:
  WebSearch "github.com Vale prose linter stars content style guide
  tool", this session, meilisearch.com/blog/prose-linting-with-vale
  and vale.sh sources).
- Problem solved: style-guide drift across many authors/documents —
  the same rule (banned word, passive voice, sentence length) gets
  enforced inconsistently when it lives only in a human reviewer's
  head.
- How: a YAML-configurable rule set with per-rule severity levels
  (suggestion/warning/error), scoped by document format so code blocks
  are excluded from prose rules automatically.
- Learning applied: rule severity should not be binary. Folded into
  playbook rule 28 and the methodology's new severity-tiering
  paragraph — block vs advisory, explicit and defaulting to block, in
  place of the prior implicit single-tier prohibition list.

### 2. Ditto / Frontitude (copy-source-of-truth managers)
- Adoption evidence: both surfaced independently across two of the
  three search angles (general 2026 tool survey and the Figma-plugin-
  specific search) as the two named alternatives in the copy-library
  category (canonical: WebSearch "Figma Content Reel plugin content
  design microcopy tools practitioners use", this session — Medium/
  html.to.design roundups naming both as the standard pairing next to
  Content Reel).
- Problem solved: the same decision-need gets re-worded slightly
  differently every time a new screen needs similar copy, producing
  near-duplicate strings with no single source of truth between design
  and code.
- How: a single reusable text-component library keyed to the copy's
  purpose, pulled from rather than re-typed, with design/code sync.
- Learning applied: folded into playbook rule 26 and the methodology's
  new reuse-check step — check for an existing string serving the same
  content_id + user_need before drafting a new one; reuse verbatim
  unless a stated reason says the existing string fails this decision.

### 3. Content Reel (Figma plugin, Microsoft)
- Adoption evidence: appears as the top result for the Figma-plugin
  copy-tooling search angle, with an official product page and
  Figma Community listing (canonical: WebSearch "Figma Content Reel
  plugin content design microcopy tools practitioners use", this
  session — contentreel.design and figma.com/community listings).
- Problem solved: designs shipped with placeholder ("lorem ipsum")
  copy never get updated to real, approved strings before review,
  masking content problems until late.
- How: categorized collections of real, approved copy substituted
  directly into design files in place of dummy text.
- Learning applied: reinforces the existing `content_id` requirement
  (spec field, already present) rather than adding new rule text — no
  edit made for this tool alone; it corroborates rule 26's reuse-check
  direction rather than adding a fourth rule.

### 4. Hemingway (readability tool)
- Adoption evidence: named directly alongside Ditto/Frontitude/Content
  Reel in the same Figma-plugin-side roundup as a distinct category —
  readability scoring rather than copy management (canonical: same
  WebSearch as above).
- Problem solved: a plain-language binary verdict gives a writer no
  actionable next step — which sentence, which construction, needs to
  change.
- How: sentence/word-level highlighting by category (hard to read,
  very hard to read, passive voice, adverbs), so the issue and its
  location are both visible at once, not just an aggregate score.
- Learning applied: folded into playbook rule 27 and the methodology's
  `plain_language_check` field-mapping row — a `fail` must name its
  category (sentence length, passive voice, jargon, hedge word) with a
  fix note, not a bare fail.

## Upstream basis
Issue #1199 (northpole req#1/req#5); prior #1174 landed playbook
(content-design-rulebook, playbook/operational-playbook.md, axes 1-5);
2026-08-13 operator amendments on #1199 (apply-not-reference; native
application, no tool-attribution catalogs).

## What did not work
None.

## Open findings
None.

amendments-reconciled: issuecomment-5277489599 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is a delegated-judgment
verdict for a different candidate PR on branch `issue-1199/accessibility`
(canonical: `gh issue view 1199 --json comments -q '.comments[-6:]'`,
read this session — the immediately preceding comment reads "Judgment
opened: PR #? — candidate decision on branch `issue-1199/accessibility`
(3 path(s) changed) entered delegated-judgment evaluation."). It does
not name or reference this content-design unit or its rulebook-repo
counterpart (content-design-rulebook#29), so no content amendment to
this record is warranted.

amendments-reconciled: issuecomment-5277572544 ("Judgment opened: PR
#? — candidate decision on branch `issue-1199/content-design` (1
path(s) changed) entered delegated-judgment evaluation.") names this
unit's own branch (canonical: `gh issue view 1199 --json comments -q
'.comments[-3:]'`, read this session — no verdict comment for this
branch's judgment has landed yet as of this read; the two immediately
following comments are a full opened/verdict pair for the unrelated
`issue-1199/execution-observation` branch). No verdict content exists
yet to reconcile against; this record proceeds on the
`APPROVE issue-1199/content-design` comment already on record above,
per contract v3 s19's two approval paths (this being single-account
mode) — the delegated-judgment evaluation is a separate, additional
mechanism this record notes but does not treat as blocking.

amendments-reconciled: issuecomment-5277577397 ("Judgment opened: PR
#? — candidate decision on branch `issue-1199/devrel` (4 path(s)
changed) entered delegated-judgment evaluation.") names branch
`issue-1199/devrel`, not this content-design unit (canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5277577397 -q
.body`, read this session). No content amendment warranted.

## 2026-08-14 amendment: plugin-ecosystem rework

The 2026-08-14 operator amendment on issue-1199 narrowed the survey
target to the Claude Code plugin/skill ecosystem — the fold-in above
(rules 26-28, Vale/Ditto/Content Reel/Hemingway sourcing) was domain-
tool-basis and does not satisfy the amended acceptance check alone.
This section adds plugin-ecosystem coverage on top of the still-valid
rules 26-28.

Scout brief: docs/issue-1199/reports/content-design/scout-brief-plugin-rework.md
(2 stages, parallel sweep + deepening, budget compliant).

canonical: `git -C /tmp/content-design-rulebook show --stat
issue-1199/content-design-plugin-rework`, this session
Upgrade made: playbook/operational-playbook.md axis 7 (rules 29-31 —
staged single-dimension revision with per-phase numeric ceilings, and
a per-UI-element-type template distinct from axis 6's content_id
string reuse), wired into
docs/handbooks/content-design/methodology.md's phase-2 step order
(`template-check` step, `Staged revision` paragraph) in the
content-design-rulebook repo.

canonical: `gh pr view 23 --repo tokenmaxxxer/content-design-rulebook
--json url,headRefName,state`, this session
Committed in the rulebook repo (commit a56d063, branch
issue-1199/content-design-plugin-rework), pushed, PR opened:
https://github.com/tokenmaxxxer/content-design-rulebook/pull/23

Source (Claude Code plugin, adoption evidence): a purpose-built
UX-writing Claude Code skill, 147 GitHub stars (canonical: `gh api
repos/content-designer/ux-writing-skill --jq
'{stars:.stargazers_count}'`, this session → 147), independently
surfaced across two of three search angles run this session. No tool
name or source repo appears in the rulebook text itself (2026-08-13
operator amendment: native application, no tool-attribution catalogs).

canonical: `gh pr view 23 --repo tokenmaxxxer/content-design-rulebook
--json state,mergedAt`, this session → {"mergedAt":null,"state":"OPEN"}
loop_state: awaiting-review (rulebook PR #23 open, not yet approved/merged)

canonical: same `gh pr view 23 --json state,mergedAt` command above,
this session
next steps: rulebook-repo approver reviews and merges PR #23. The
top-of-file `loop_state: landed` line at the head of this record
covers only the earlier axis 6/rules 26-28 fold-in; PR #23's merge
state is not re-asserted as landed here and needs a separate re-read
once it merges.

resolution path: track content-design-rulebook#23 to merge; if
feedback requires rule changes, push follow-up commits to
issue-1199/content-design-plugin-rework in the rulebook repo.
