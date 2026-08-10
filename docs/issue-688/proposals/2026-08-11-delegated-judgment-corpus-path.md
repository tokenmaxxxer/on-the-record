---
status: proposed
files:
  - on-the-record/hooks/delegated-judgment-gate.sh
  - on-the-record/hooks/test_delegated_judgment_gate.py
---

## Request

`delegated-judgment-gate.sh`'s depth-axis corpus read still points at the
retired flat product-doc directory; issue #684 moved the writer
(`product-capture-stopgate.sh`) to an issue-scoped location. The reader
and writer now disagree on where the corpus lives, so the depth axis
silently evaluates against nothing. Update the reader to the post-#684
issue-scoped location per `docs/specs/generated-paths.md`, with the
empty-state behavior stated explicitly, and cover it with a test.

## Constraints

- Zero-install consumer surface: the fix must not add a gates-package
  import or on-the-record checkout resolution to the hook itself (the
  hook already ports its logic inline for this reason).
- The `issue` variable the script already derives from the
  `issue-<n>/<role>` branch match must be the single source for the
  issue number used in the new corpus path — no second derivation path.
- Empty/absent corpus at the new location must continue to escalate
  (return `False` from `depth_match`) exactly as today's absent-corpus
  case does — no new special-case branch, matching the AND-composition
  architecture the script's own header documents.

## Rationale

Two ways to identify the corpus path were available: (a) reuse the
already-in-scope `issue` int the branch-match produced, string-formatted
the same way `decisions_dir` (line 660) already builds its issue-scoped
path; or (b) re-derive the issue number independently inside
`depth_match` (e.g. re-reading the branch or a payload field passed
in). (b) was rejected: it would create a second issue-number derivation
path in a script whose own docstring already flags the single-derivation
branch-match as the intended source of truth, and would risk the two
derivations disagreeing on a malformed branch name — a duplicate of
exactly the reader/writer disagreement this issue exists to fix, just
moved one level down. (a) is chosen: one derivation, reused everywhere,
matching the pattern the script already uses for its decisions path.

## What will be done

- In `delegated-judgment-gate.sh`, change `depth_match`'s `corpus_dir`
  from the flat product path to the issue-scoped product path, built
  from the same `issue` variable already in scope at the call site
  (passed into `depth_match` as an argument, not re-derived).
- Update the docstring header (lines 6, 14) and the
  `derivation_source: ...` citation string (line 667) to describe the
  issue-scoped corpus, so the comments and the posted audit-trail text
  stop describing a path the code no longer reads.
- In `test_delegated_judgment_gate.py`, move the `_product_corpus` test
  helper's write target to the issue-scoped path matching the fixture's
  fixed `issue-42` branch, so existing corpus-match tests keep passing
  against the new location.
- Add one test asserting the script's own source text no longer contains
  the retired flat product path (grep-shaped, run inline in the test
  module — the acceptance criterion's second check), and confirm the
  existing empty-corpus escalation test continues to pass unchanged
  against the new location (first + empty-state checks).

## Out of scope

Nothing else — this is the single stale-reference fix issue #688 scopes,
per its "Still broken / out of scope" section. No changes to
`product-capture-stopgate.sh` (already fixed under #684), no changes to
`docs/specs/generated-paths.md`'s table (the reader row already exists
and is not reclassified by this fix), no broader sweep for other
possible stale references outside this one file.

## Accumulation

This edit touches one inline-`gh`/subprocess-heavy hook script that
already carries several prior issue-numbered patches inline (see its own
header: issues #573, #597, #641, #684-adjacent). This fix adds no new
inline call, no new roles/*.json-style repeated file, and no new
per-file loop — it is a one-line path-string change plus matching
docstring/citation text, applied once at the single call site. If more
such stale-path corrections arrive later (one per retired path, as
happened after #684), each still lands as its own one-line diff at its
own call site; nothing here creates a pattern that would need factoring
out before an N-th occurrence, since there is exactly one corpus-path
read in this file and it is not duplicated elsewhere in the script.

## How you'll know it worked

`python3 on-the-record/hooks/test_delegated_judgment_gate.py` passes,
including the new corpus-location and no-retired-reference tests, and
`python3 -m pytest on-the-record/hooks/ -q -k delegated_judgment` (the
issue's named check) passes.
