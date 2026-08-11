---
proposal: docs/issue-745/proposals/product-discovery.md
---

# Hunt record — product-discovery

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass.

Verdict: FINDING — `gates/record_lint.py`'s `bare_count_claim_check` (and its
sibling `gates.py::record_derived_counts_in`, which shares the same regex)
accepts any `` `derived: ...` `` tag as proof of a bare count claim, verifying
only that the string pattern is present — not that the cited content is a
real, reproducible derivation of the number. A fabricated tag like
`` `derived: trust me bro` `` silences the gate exactly as a genuine
`` `derived: grep -c foo bar.txt` `` citation would.
Kind: silent-failure
Seed: candidate #1 from stance context — `gates/record_lint.py`'s
`bare_count_claim_check`, `_CLAIM_DERIVED_TAG = re.compile(r"`derived:\s*\S.*?`")`
at gates/record_lint.py:66, used at line 114; mirrored verbatim as
`_DERIVED_TAG` in gates/gates.py:463, used in `record_derived_counts_in` at
gates/gates.py:490.
cap_seconds: 180
tier: size:200+
diff_stat_lines: 207 insertions across 3 docs-only files (git diff --stat main...HEAD -- docs/)
started_at: 2026-08-11T05:20:00Z
ended_at: 2026-08-11T05:30:00Z

### Reproduce
```
python3 -c "
import sys
sys.path.insert(0, 'gates')
import record_lint

fake_ratio        = '- Found 12 of 15 \`derived: yes\` in the survey.'
fake_ratio_fluff   = '- Found 12 of 15 \`derived: trust me bro\` in the survey.'
real_looking       = '- Found 12 of 15 \`derived: grep -c pattern file.txt\` in the survey.'

for label, text in [('fake, empty derived: yes', fake_ratio),
                     ('fake, fluff derived: trust me bro', fake_ratio_fluff),
                     ('real-looking derived citation', real_looking)]:
    print(label, '->', record_lint.bare_count_claim_check(text))
"
```
(run from the repo root, against the real, unmodified
`gates/record_lint.py` shipped in this repo — no repo files were created or
modified to produce this output, it is a direct call into the shipped
function.)

### Observed
```
fake, empty derived: yes -> []
fake, fluff derived: trust me bro -> []
real-looking derived citation -> []
```
All three produce **zero violations** — the gate is equally satisfied by a
content-free placeholder (`derived: yes`), an explicitly dismissive fabrication
(`derived: trust me bro`), and an actual reproducible citation.

Caveat observed along the way: this bypass fires only for a bare ratio claim
immediately followed by the tag; a noun-suffixed variant is caught instead by
a *different*, unconditional path (the ratio sub-match there is never
adjacent to the tag, so it always flags, tag or no tag) — a separate defect
in the opposite direction, not claimed as this finding.

### Expected
`bare_count_claim_check` (and `record_derived_counts_in`) either (a) require
the `derived:` payload to match a stricter shape that at least looks like a
command/path (e.g. containing a recognizable shell verb or an existing
in-repo path per the same module's `orphaned_path_reference_check` idiom), or
(b) accept that this gate is deliberately shape-only and say so — as written
it silently launders any fabricated count past review with no signal that
the citation was never checked for realness. The gate's own docstring
("`derived:` 인용" / "citation") and its accompanying issue numbers (#333,
#517) both frame this as a *substantive* derivation requirement, not a
free-text opt-out, so the gap is a silent failure: absence of a real citation
looks exactly like presence of one.
