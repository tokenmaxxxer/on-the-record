---
issue: 5
role: product-discovery-one-pager+product-discovery-jtbd-problem-framing+market-analysis-jtbd-fit+decision-brief-4cd9b7bb
author: product-discovery-one-pager+product-discovery-jtbd-problem-framing+market-analysis-jtbd-fit+decision-brief-4cd9b7bb
skills: product-discovery-one-pager (skill-repository(c05de12)), product-discovery-jtbd-problem-framing (skill-repository(c05de12)), market-analysis-jtbd-fit (skill-repository(c05de12)), decision-brief (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-1/reports/research-evidence-discipline+user-discovery-evidence-strength-tagging-1ae594fd/user-discovery.md
    sha: c3c319d0fc864dd3c51cfc3319b465dbeb7dba1e
---

# issue-5 — product-discovery-one-pager+product-discovery-jtbd-problem-framing+market-analysis-jtbd-fit+decision-brief-4cd9b7bb record

## What was done

Delivered a product one-pager for the comprehension gap, bounded strictly
by issue #1's landed, corrected discovery report (canonical:
`docs/issue-1/reports/research-evidence-discipline+user-discovery-evidence-strength-tagging-1ae594fd/user-discovery.md`;
the superseded copy under `.../user-discovery+...-2d8db0b0/` was read only
to confirm it is superseded, not used as a source for any claim below).

Content delivered, all in one document:
- `## Job` — a solution-free JTBD tuple (performer, job, circumstance,
  three independently measurable desired outcomes) that names the
  **monitoring** framing (row 1/row 2, Fact-tier) as what this product
  builds for, states explicitly that the narrower **articulation**
  framing (row 9, Assumption-tier, unverified — HTTP 403 on the primary
  source) is NOT what it builds for, and states what breaks if that
  choice is wrong (a monitoring signal becomes redundant if students can
  already self-diagnose, and the real unmet job shifts to
  resolution-availability, already partly served per Kestin/Kumar below).
- `## Moment of use` — a walkthrough from the student's situation (just
  finished a solo reading/problem-set session, about to trust a felt
  sense of "done"), not from product features.
- Four `### Against <coping behavior>` sections (Re-reading, Office
  hours, Asking a peer, Generic LLM Q&A — one per issue-1 coping
  behavior), each naming the specific failure mode from the landed
  report and stating attack or explicit decline: attacks Re-reading's
  illusion-of-fluency (primary differentiator) and Office hours'
  question-conversion barrier (narrowly — location, not diagnosis);
  declines Asking-a-peer's shared-ignorance ceiling and Generic-LLM-Q&A's
  crutch-effect/fabrication modes as out of scope by design (this product
  does not generate explanations).
- A counter-evidence section naming Kestin et al. (2025, 194-student
  Harvard RCT) and Kumar (*Harvard Crimson*, 2024) by name, taking a
  split position: resolution is being distributed by existing tools (so
  this product declines to compete there), monitoring is not addressed
  by either piece of evidence (so the product's actual bet stands
  unrebutted by this counter-evidence) — stated with a numeric
  confidence (65/100) and a checkable condition that would flip it.
- `## Falsifier` — a time-bound (6-week) falsifier tied to the landed
  report's own recommended next step (a targeted interview round),
  checkable against whether low-scoring students can name their own gap
  unprompted before seeing a check's result.

**Deviation — delivery path:** the issue's Acceptance section hardcodes
`docs/product/one-pager.md` as the checked path. This repository's
board-gate (`core/hooks/board-gate.sh`, contract v3 s10) refuses any
write under `docs/` that is not `docs/README.md`, one of the six standing
buckets (`_assets`, `decisions`, `handbooks`, `proposals`, `reports`,
`specs`), or an issue tree (`docs/issue-<n>/<bucket>/...`) — `product` is
not a recognized bucket anywhere in that script (`BUCKETS = ("_assets",
"decisions", "handbooks", "proposals", "reports", "specs")`, no alias, no
per-repo override read). Both a `Write` to `docs/product/one-pager.md`
and a `mkdir -p docs/product` were refused live this session with the
identical message:
```
board-gate: docs/product/one-pager.md is neither docs/README.md, one of the six standing
buckets (_assets, decisions, handbooks, proposals, reports, specs), nor an issue tree
(docs/issue-<n>/). (contract v3 s10)
```
derived: `grep -n '^## Job' docs/product/one-pager.md` on this branch —
result: `ugrep: warning: docs/product/one-pager.md: No such file or
directory` (file cannot exist; not merely unwritten).

The content was instead delivered at `docs/issue-5/specs/one-pager.md`
(the `specs` standing bucket, inside this issue's own tree — a fully
compliant write target) with identical section shape, verified against
the issue's own check commands with the path substituted:
```
$ grep -n '^## Job' docs/issue-5/specs/one-pager.md            -> 14:## Job
$ grep -n '^## Moment of use' docs/issue-5/specs/one-pager.md  -> 29:## Moment of use
$ grep -c '^### Against ' docs/issue-5/specs/one-pager.md      -> 4
$ grep -n 'Kestin\|194' docs/issue-5/specs/one-pager.md        -> 3 matches
$ grep -n '^## Falsifier' docs/issue-5/specs/one-pager.md      -> 76:## Falsifier
```
derived: the four commands above, run this session against
`docs/issue-5/specs/one-pager.md` on this branch.

This is an alternative-swap forced by a hard tool-level gate, not a
scope-exceeded stop and not a content shortcut: no section, evidence
bound, or prohibition from the issue was relaxed — only the file's
path changed. Per Step 1 of `decision-brief`, this specific call (which
compliant path to use) clears none of the four escalation conditions
(not costly to reverse — a follow-up move/copy fixes it; does not set
product direction; trades off no value the user owns; not a reserved
decision class), so it was decided in-session rather than escalated, and
is logged here rather than built into a formal brief.

## Why

Issue #1's report draws a sharp line the issue text requires respecting:
rows 1-2 (monitoring failure) are Fact-tier and behavioral; row 9
(articulation failure) is Assumption-tier, unverified, and the report's
own stated weak point. Building the product definition around monitoring
keeps the one-pager's central bet resting on the strongest evidence in
the upstream report, and keeps the falsifier honest — it tests exactly
the claim (row 9) the report flagged as untested, rather than assuming
it. The four `### Against` sections were split attack/decline rather
than claiming the product beats every coping behavior, because the
issue explicitly requires the differentiator to "attack one of those
failure modes specifically, not restate the category" — a product that
claimed to fix all four would be restating the category, not
differentiating. The counter-evidence position was split by job step
(resolution vs. monitoring) rather than a flat yes/no, because Kestin and
Kumar are both about resolution quality/availability and neither
measures whether their subjects lacked awareness of their own gap before
engaging — collapsing them into a single verdict on "is this solved"
would have overclaimed in one direction and underclaimed in the other.

## Upstream basis

- `docs/issue-1/reports/research-evidence-discipline+user-discovery-evidence-strength-tagging-1ae594fd/user-discovery.md`
  — the landed, corrected discovery report (canonical per the spawn
  instruction); lands on `main` at commit
  `c3c319d0fc864dd3c51cfc3319b465dbeb7dba1e` (PR #2), unchanged by this
  session — no new citations were added beyond what this file already
  verified (rows 1-9 as tagged there).
- GitHub issue #5 (`gh issue view 5`), read live this session for its
  Context, Deliverable, Scope, and Acceptance sections verbatim.

## Open findings

1. **`docs/product/one-pager.md` cannot be created under this repo's
   current board-gate policy** (see Deviation above) — the issue's
   Acceptance check commands, run verbatim against that exact path, will
   report "no such file" regardless of content quality. Resolution path:
   a human either (a) merges this PR and separately relocates/copies
   `docs/issue-5/specs/one-pager.md` to `docs/product/one-pager.md`
   outside a gated role session (a plain repo-owner file operation, not
   a role-session write), or (b) updates the issue's acceptance script
   to check the issue-tree path instead, or (c) extends
   `board-gate.sh`'s `BUCKETS` to recognize a `product` top-level
   standing area if that is meant to be a durable repo convention beyond
   this one issue. This is not something a role session can resolve
   itself — it requires either a policy change to shared gate code
   outside this repo, or a human file move after merge. Flagged, not
   silently worked around: no attempt was made to route around
   `board-gate.sh`'s detection.

## Next steps

None from this role — `loop_state: landed`. The open finding above is
for the human merging this PR to resolve; no further work is planned in
this session.

skill-verdict: product-discovery-one-pager — applied: invoked; used its opportunity-framing structure (problem/solution separation, target-market-equivalent job performer, competitive-alternatives-equivalent Against sections, differentiator) adapted into the one-pager; its literal ask-one-field-interactively procedure was not run verbatim since this is a headless build-now delivery (CORE_BUILD_NOW=1) with no user turn to interview.
skill-verdict: product-discovery-jtbd-problem-framing — applied: invoked; used to write `## Job` as a solution-free four-part tuple (performer, job, circumstance, measurable outcomes) before any solution content, with UI/mechanism language kept out of the job statement itself.
skill-verdict: market-analysis-jtbd-fit — applied: invoked; used to name the job at underlying-progress level (not product category), identify the true competing alternative (doing nothing / trusting felt fluency, not a same-category rival), state the differentiation verdict against a measurable outcome (the predicted-vs-actual gap), and address why-now against that do-nothing baseline.
skill-verdict: decision-brief — applied: invoked; used its frame/alternatives/recommendation/falsifier discipline in abbreviated (medium-stakes) form for the two in-document position calls (job framing choice; distribution-of-solved-capability question) per the issue's own instruction that the artifact state these positions itself, and used its Step 1 trigger test in-session for the delivery-path deviation logged above.
skill-verdict: work-in-english — applied: invoked; the one-pager, this record, and commit messages are written in English; the final chat-facing summary is in Korean.
skill-verdict: research-evidence-discipline — applied: invoked; every claim in the one-pager restates only rows already Fact/Inference/Assumption-labeled in the landed issue-1 report (e.g. row 9 kept explicitly unverified/Assumption, not upgraded to a premise), and no new citation was added.
skill-verdict: user-discovery-evidence-strength-tagging — applied: invoked; when restating landed-report claims, preserved their behavioral/recounted/opinion tiers (row 6's single-course scale and row 9's unverified status are both carried into the one-pager's own hedging language) rather than flattening them into unqualified facts.

## What did not work

None — the content delivery succeeded on the first draft against the
issue's acceptance shape (verified above); the only obstacle was the
delivery-path conflict logged under Deviation/Open findings, which was
resolved by relocating to a compliant path rather than by any retry.
