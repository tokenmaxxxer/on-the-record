# issue-1165 (content-design, step 1 round 2): current-state survey — records/PR bodies/reports

kind: survey
subject: issue-1165

Scope: three human-facing record forms this repo produces — (a) a
role's phase-2 record (`docs/issue-<n>/reports/<role>.md`, scaffolded
by `on-the-record/hooks/record-scaffold.sh`), (b) a PR body, (c) a
proposal/report framing document (`docs/issue-<n>/proposals/*.md`).

## (a) Scaffold shape

canonical: `on-the-record/hooks/record-scaffold.sh`, read this turn.
Emitted section order: YAML frontmatter, then `## Summary of work`,
`## Why`, `## What did not work`, `## Open findings`, `## Next steps`,
`## Resolution path`. No lead-paragraph slot before the first heading
and no section-size bound in the scaffold template itself.

## (a) Real specimen: docs/issue-587/reports/implementation.md, lines 15-22

canonical: `docs/issue-587/reports/implementation.md` lines 15-22, read
this turn, quoted verbatim: "per the approved proposal
(`docs/issue-587/proposals/implementation-remediation-round3-target-root.md`.
canonical: `gh pr view 611 ...` ... merged in PR #611):".

Content-design new-reader read of this quoted span: the `canonical:`
citation clause sits inside the sentence, between the proposal
reference and its own closing parenthesis, ahead of the parenthesis's
content ("merged in PR #611"). A passing shape states the point first
and moves the citation to a trailing clause or its own line, so the
citation requirement (`gates/record_lint.py`, this session's own
directive) never has to split one sentence to satisfy it.

## (b) PR body

canonical: `gates/pr_reference.py`, function `check_body` at line 29,
read this turn. Scope of that function: a phase-appropriate issue
reference (`#<n>` vs `Closes #<n>`) only — no assertion about body
structure, lead paragraph, or section bounds exists in that function.

## (c) Proposal/report framing

canonical: `docs/issue-1165/proposals/2026-08-13-technical-writing-human-comprehensibility.md`,
read this turn. That design's `lead_paragraph_present` rule is
positional (a paragraph exists before the first heading); it does not
reach the sentence/clause grain the (a) specimen above shows — content-
design's round-2 proposal targets that finer grain, one level under
technical-writing's paragraph-level rule.
