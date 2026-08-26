---
proposal: none (contract v3 s19a CORE_BUILD_NOW=1 bypass)
---

# Hunt record — conformance-review-2381

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — record-claim-guard's #793/#870 section-scoping treats a whole `## Findings` heading block as one section, so a citation in one `---`-delimited requirement sub-block silently grounds an ungrounded state/defect claim in a sibling sub-block under the same heading, letting the claim pass with exit 0 (no refusal).
Kind: composition
Seed: on-the-record/hooks/record-claim-guard.sh -> gates/record_lint.py (canonical_source_claim_check / outcome_claim_citation_check, both use `_section_bounds`); docs/issue-2381/reports/conformance-review.md's own `## Findings` section (4 `---`-delimited requirement blocks under one heading) is the real-world shape that exercises this.
cap_seconds: 180
tier: size:>200-lines
diff_stat_lines: 248 lines across 4 files (docs/issue-2381/reports/conformance-review.md, two .orchestrate-hook-fires/<hash>.log shards, one deviation-log entry)
started_at: 2026-08-26T00:37:00Z
ended_at: 2026-08-26T00:50:30Z

### Reproduce
`gates/record_lint._section_bounds` scopes a claim's required-citation search to "the nearest markdown heading above/below" (`_HEADING_LINE` matches only `#`-lines), never a `---` horizontal rule. This project's own Findings convention (visible in the real, just-landed `docs/issue-2381/reports/conformance-review.md`) packs several independent requirement blocks under one `## Findings` heading, each delimited only by `---`. That means `canonical_source_claim_check`'s per-claim evidence search covers every sibling block, not just the one the claim is actually in.

Payload A (decoy present — an unrelated commit-pinned citation sits in a sibling `---` block under the same `## Findings` heading; the actual claim's own block has zero citation):
```
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "docs/issue-2381/reports/conformance-review-repro.md",
    "content": "## Findings\n\n---\nrequirement: R1\nevidence: `abcdef1:gates/record_lint.py:10-20`\nrationale: cited evidence supports this claim.\n---\nrequirement: R2\nevidence: (nothing at all cited here)\nrationale: the background worker session is halted and its queue entry is confirmed stale, with no citation of its own for this specific claim.\n---\n\n## Why\n"
  },
  "cwd": "<repo root>"
}
```
```
on-the-record/hooks/record-claim-guard.sh < payload.json ; echo "EXIT: $?"
```

Payload B (control — identical R2 block, but R1's sibling block carries no citation either, so the section as a whole has none):
```
{ ... "evidence: nothing pinned here at all\nrationale: no citation in this block." ... same R2 block ... }
```
```
on-the-record/hooks/record-claim-guard.sh < payload2.json ; echo "EXIT: $?"
```

### Observed
Payload A: `EXIT: 0` — the hook allows the write. R2's "halted"/"confirmed stale" state-claim, which carries zero citation in its own block, passes silently because R1's `abcdef1:gates/record_lint.py:10-20` decoy citation sits somewhere earlier in the same (heading-bounded, not `---`-bounded) section.

Payload B (control, same R2 claim, no decoy anywhere in the section): `EXIT: 2`, refused —
```
record-claim-guard: 레코드에 canonical 소스 인용 없는 상태/결함 주장 (issue #793): 'rationale: the background worker session is halted and its queue entry is confirmed stale, with no citation of its own for this specific claim.' — ... 같은 섹션 안에 `canonical: ...` 태그가 없다 ...
```
This confirms the pass in Payload A is caused specifically by the decoy citation in the sibling block, not by some other exemption matching R2's line.

### Expected
`canonical_source_claim_check` (issue #793 mirror) and `outcome_claim_citation_check` (issue #870 mirror) should refuse Payload A the same way they refuse Payload B: a state/defect/outcome claim's own citation should be scoped to the requirement block it is actually made in (bounded by `---` as well as `#`-headings, given this project's own Findings-block convention), not to every sibling requirement crammed under the same markdown heading. As written, one grounded requirement block anywhere under a `## Findings` heading silently vouches for every other, ungrounded requirement block sharing that heading.
