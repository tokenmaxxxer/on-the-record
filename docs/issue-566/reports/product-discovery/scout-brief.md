# Scout brief — issue #566: durable requirements/priorities/philosophy/goals record

Mode: batched-sequential (2 WebSearch calls, one turn) — no parallel subagent fan-out used; this
is an internal architecture question (hook design against this repo's own conventions), so the
"best-in-class product" sweep is aimed at prior art for the mechanism (ADR/decision-log practice,
commit-hook traceability enforcement), not at consumer products. 2 stages (sweep only; judge
point 1 found no decision-relevant deepening needed — the hits converged fast and the repo's own
existing patterns, not external tools, are the load-bearing precedent).

## Must-bes (Kano), from ADR / decision-log literature
- A record captures context, options considered, decision, and consequences — not just the
  decision (adr.github.io).
- The collection accumulates into a queryable log, not a single ever-rewritten file (adr.github.io).
- Compliance/traceability practice pairs a structured artifact with an *enforcement point* (commit-
  msg hook, PR template) that a change cannot bypass silently — "if your project relies heavily on
  code documentation, consider hooks that enforce documentation standards" (pixelfreestudio,
  techvzero).

## Performance axes the field competes on
1. Granularity: one ADR per decision vs. one giant living doc — this repo's own `docs/decisions/`
   (per-issue ADR files, e.g. `docs/issue-476/decisions/2026-08-08-h1-h2-mechanism-adr.md`) already
   answers this for *decisions*; issue #566 is a sibling category (requirements/priorities/
   philosophy/goals), not decisions, so the existing ADR granularity is adoptable but the content
   type is new.
2. Enforcement point: pre-commit / commit-msg hook (blocks the write) vs. PR-template checklist
   (asks, doesn't block) — the literature is split; this repo's own `on-the-record/hooks/` surface
   already commits to the harder "blocks the write" pattern for other invariants
   (`record-claim-guard.sh`, `contract-guard.sh` fire on `PreToolUse` for `Write|Edit|Bash`).
3. Automatic detection of *missed* capture (the record wasn't written) vs. only checking the
   *shape* of what was written when it is written — external traceability practice mostly checks
   the latter only (commit message contains an issue ID); it does not solve "a requirement was
   stated in conversation and nothing was ever written." That detection axis is the issue's harder,
   unsolved half and has no external precedent found in this sweep.

## Adopt / skip
- Adopt: per-issue-tree structured files mirroring `docs/decisions/` granularity, keyed to this
  repo's own four nouns (requirements/priorities/philosophy/goals) rather than inventing a new
  taxonomy — matches this repo's existing habit (confirmed in survey.md) of naming closed
  vocabularies for record shape instead of free text.
- Adopt: hook fires on `PreToolUse`/`Stop`, not `SessionStart`-only — this repo's own
  `directive.sh` comment states the rationale directly ("steering must be freshly read to steer, a
  session-start-only injection drifts out of a long context"); the same reasoning applies to
  detecting an unrecorded requirement stated mid-conversation.
- Skip: a single monolithic `requirements.md` ledger — literature and this repo's own
  `docs/decisions/` precedent both favor structured, dated, per-topic files over one rewritten
  document (harder to diff, harder to gate on "was this decision's write actually made").
- Skip: enforcing via commit-msg content alone (grep for keywords in the commit message) — this
  repo's own `Subject:` trailer already serves a different purpose (issue linkage), and keyword-
  matching a commit message cannot detect a requirement stated in *conversation* that produced no
  commit at all, which is the issue's actual failure mode.

## Segment fit
This is an internal-tooling / dev-process feature, not a consumer product — "user expectations"
read as this repo's own existing operator/contributor expectations (contract v3, the four
non-discharge rules of #310, #476's "no self-report as sole evidence") rather than external
product reviews. No external review corpus applies; this is noted as a fit judgment, not a gap.

## Gap line
Current state already meets: per-issue structured decision records exist for architectural
decisions (`docs/decisions/`), and a deployed hook surface already blocks non-conforming writes
pre-emptively (`on-the-record/hooks/*.sh` on `PreToolUse`). Missing: (1) no record type exists yet
for requirements/priorities/philosophy/goals as distinct from architectural decisions or per-role
acceptance criteria; (2) no hook today inspects the *conversation transcript* for a requirement-
shaped statement and cross-checks it against what got written to docs — every existing hook
inspects the *tool call about to happen*, not the turn's prior conversational content; (3) no
target-project bootstrap behavior is defined for a fresh repo with no docs/ tree.

## Sources
- https://adr.github.io/
- https://microsoft.github.io/code-with-engineering-playbook/design/design-reviews/decision-log/
- https://blog.pixelfreestudio.com/how-to-use-git-hooks-for-code-quality-enforcement/
- https://techvzero.com/git-compliance-documentation-guide/
