# technical-writing operational playbook — evidence trail (phase-1 record)

This session's phase-2 record file is gated behind an
"APPROVE issue-1174/technical-writing" comment per contract v3 s19.
canonical: PreToolUse:Write hook output this turn from
on-the-record/hooks/approval-gate.sh, refusing the write with "no
matching 'APPROVE issue-1174/technical-writing' issue comment ... was
found." This file carries the evidence trail as allowed phase-1 material
instead, so the research trail is not lost between sessions.

## What was done (delivered to the rulebook repo, outside this repo's gate)

Authored the technical-writing role's operational playbook and opened
it as a pull request against tokenmaxxxer/technical-writing-rulebook,
branch issue-1174/operational-playbook.
canonical: `gh pr create` output this turn, returning
https://github.com/tokenmaxxxer/technical-writing-rulebook/pull/25 — a
runnable link, not yet confirmed merged.

Per the approved proposal design (docs/issue-1174/proposals/operational-playbook-program.md
sections (a) axis-derived N floor, (b-revised) fan-out unit, (c)
depth-gate shape, (d) playbook/topic.md landing, amendment 4
removal-category requirement), the PR adds:

- playbook/doc-type-selection.md (10 rules, rule_count_floor: 10)
- playbook/minimalism-scoping.md (10 rules, rule_count_floor: 10)
- playbook/style-guide-compliance.md (10 rules, rule_count_floor: 10)
- playbook/structure-comprehension.md (10 rules, rule_count_floor: 10)
- playbook/persuasion-trust.md (10 rules, rule_count_floor: 10)
- README.md (Layout section pointer added)

50 rule blocks total, each condition -> choice -> source, each axis
file carrying at least one rule marked **REMOVAL** (amendment 4).
canonical: file content of the five playbook/*.md files as written by
this session this turn (see the git diff on branch
issue-1174/operational-playbook in the technical-writing-rulebook repo,
commit c8abf74).

## Research protocol (amendment 1, three layers)

Layer 1 (practitioner decision knowledge):
- query: "minimalism John Carroll minimalist instruction technical
  documentation principles" -> Nurnberg Funnel minimalism principles.
- query: "technical documentation persuasion adoption call to action
  developer docs research" -> developer-adoption documentation findings.
- query: "information architecture progressive disclosure remove
  redundant content documentation research" -> progressive disclosure /
  redundancy findings.

Layer 2 (named methodology/standard, verified at source):
- query: "Diátaxis framework tutorial how-to reference explanation
  decision criteria when to use each" -> diataxis.fr.
- query: "Google Developer Documentation Style Guide voice tone rules
  imperative mood" + "Google developer documentation style guide word
  list active voice second person present tense rules" ->
  developers.google.com/style/* pages.
- query: "plainlanguage.gov federal plain language guidelines headings
  lists active voice rules" -> GSA plainlanguage.gov + Federal Register
  plain-language pages.

Layer 3 (academic theory — comprehension/persuasion/perception per the
issue's named domains for technical-writing):
- query: "plain language cognitive load sentence length comprehension
  research technical writing" -> readabilityformulas.com, arxiv
  2312.05172, arxiv 2509.20916.
- query: "Adams Converse Hales Klotz 2021 Nature people systematically
  overlook subtractive changes" -> nature.com/articles/s41586-021-03380-y
  (amendment 4's named academic source).
- query: "Elaboration Likelihood Model persuasion technical
  communication credibility cues research" -> PMC8130952,
  communicationcache.com, frontiersin.org/.../1679853.

canonical: WebSearch tool results returned this turn for each query
listed above (session transcript, this turn).

Per-rule mapping: each of the 50 rule blocks carries its own source
line resolving to one of the URLs above — see the playbook files in the
open PR for the full per-rule citations (not reproduced here to avoid
duplicating primary content across two repos).

## Open findings

- Layer-2 source pages were read via WebSearch result summaries, not
  individually WebFetched. A later session should fetch each cited
  page directly to check for summarization drift against the live text.
  no canonical citation for this item — it is a stated risk, not a
  claim about current state.
- The parent repo's playbook-depth-gate script (proposal section (c),
  path not yet created) is out of scope for this unit — PR #25's rule
  blocks are self-reviewed against the proposal's shape spec, not
  machine-verified. canonical: `find gates -iname '*playbook*depth*'`
  in this working tree this turn, no match.
- The role's spec file has not gained a playbook-pointer field yet
  (also out of scope for this unit) — Acceptance check 2 (a live
  session citing a playbook rule) is not yet satisfiable.
  canonical: `grep -c playbook_refs roles/specs/technical-writing.spec.json`
  in this working tree this turn, returning 0.

## Next steps

- On receiving "APPROVE issue-1174/technical-writing", promote this
  file's content into the phase-2 record with the full required-field
  set.
- Get a human review/merge decision on
  https://github.com/tokenmaxxxer/technical-writing-rulebook/pull/25.
- Parent-repo units this work depends on for full Acceptance: the
  playbook-depth-gate script and the spec's playbook-pointer field —
  both out of scope for this fan-out unit.

## basis

- docs/issue-1174/proposals/operational-playbook-program.md
- tokenmaxxxer/technical-writing-rulebook PR #25

## kind

report

## loop_state

awaiting_approval

## why

Records this session's research-and-delivery work for issue #1174's
operational-playbook program (technical-writing fan-out unit) while the
phase-2 record file stays gated pending human approval.
