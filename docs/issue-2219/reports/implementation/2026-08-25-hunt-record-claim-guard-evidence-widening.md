---
proposal: PR #2246 / commit ff1de0b7 (issue-2219: fix record-claim-guard evidence resolution to see evidence elsewhere in the same record)
---

# Hunt record — record-claim-guard-evidence-widening

## after-proposal — stance 1: widened evidence-recognition logic (_section_bounds/_dewrap/acceptance-fence-pairing) may let a claim pass with no real relationship to its "evidence"

Verdict: FINDING — the section-window built by `_section_bounds`/`_dewrap` in both `canonical_source_claim_check` and `outcome_claim_citation_check` does not exclude fenced code-block lines, so a `canonical:`/`derived:` string appearing only as illustrative example text inside a code fence (e.g. documentation showing the citation syntax, not a real citation of anything read/executed) satisfies the evidence check for any unrelated claim elsewhere in the same section.
Kind: silent-failure
Seed: commit ff1de0b7, gates/record_lint.py hunks around `_section_bounds`, `_dewrap`, `canonical_source_claim_check` (~line 785-850), `outcome_claim_citation_check` (~line 422-495)
cap_seconds: (not specified by dispatcher)
tier: default
diff_stat_lines: 977 insertions(+), 94 deletions(-) across 5 files (per `git show ff1de0b7 --stat`)
started_at: 2026-08-25T00:00:00Z (approx, wall clock not tracked precisely)
ended_at: 2026-08-25T00:15:00Z (approx)

### Reproduce
```python
import sys
sys.path.insert(0, "gates")
import record_lint as rl

# baseline: same claim, no canonical tag anywhere -> correctly flagged
text_baseline = """## Some Section

Role output found 5 defects in the module.
"""
print("baseline:", rl.canonical_source_claim_check(text_baseline))

# with a `canonical:` tag that exists ONLY as documentation/example text
# inside a fenced code block, unrelated to the actual claim below it
text = """## Some Section

Here is an example of the evidence format we use:

```
canonical: pytest -q tests/test_foo.py
```

This is just documentation showing the syntax, not real evidence.

Role output found 5 defects in the module.
"""
print("fenced-example:", rl.canonical_source_claim_check(text))
```

Same repro pattern reproduces for `outcome_claim_citation_check` with an
outcome claim ("requirements are met and the suite passed") and a fenced
`canonical: pytest -q` example line in the same section.

### Observed
```
baseline: ["레코드에 canonical 소스 인용 없는 상태/결함 주장 (issue #793): 'Role output found 5 defects in the module.' — ..."]
fenced-example: []
```
The claim-carrying line is unflagged (empty list = pass) purely because a
`canonical:`-shaped string exists inside a code fence in the same section,
even though it was never intended as a citation for anything and has no
textual/positional relationship to the claim it's "grounding".

### Expected
`_CANONICAL_TAG`/`_CLAIM_DERIVED_TAG` matching should not search fenced
code-block content when building the section window, mirroring the
claim-detection loop's own `in_fence[i]` skip. The per-line loop in both
functions already skips `in_fence[i]` when deciding whether a *line* is a
claim, but `_section_bounds`'s `lines[lo:hi]` slice used to build the
evidence-search `window` includes fence lines verbatim (no `in_fence`
filtering applied when joining), so a fenced example/quote of the tag
syntax is indistinguishable from a real citation. This directly undermines
record-claim-guard's purpose: a claim can now be "grounded" by evidence
that has zero relationship to it, as long as both live in the same
heading-delimited section and the fence merely happens to contain the
tag string (e.g. as documentation, a quoted past rejection message, or an
unrelated code sample).
