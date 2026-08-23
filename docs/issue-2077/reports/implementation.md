---
code_under_review:
  - path: spawn.py
  - path: gates/test_requirement_drift.py
loop_state: landed
type: bugfix
breaking: false
canonical: python3 -m pytest -q gates/test_requirement_drift.py executed live this session (8 passed)
verdict: pass
---

## What was done

Requirement: R1, R2 (Subject: issue-2077). Fixes issue #2077 (provenance:
#2071 defect 2) — build-now bypass (`CORE_BUILD_NOW=1` set by the spawner),
delivered directly without a separate phase-1 proposal round.

canonical: gh api repos/tokenmaxxxer/tm-dicequest/contents/docs/specs/requirement-digest.md
executed live this session, base64-decoded body read directly.

Root cause, confirmed against that live-fetched tm-dicequest digest: the
digest R-entry format doc always documented `source: <free text>`, but
`spawn.py::requirement_drift`'s parsing regex hard-coded
`\(source: #(\d+)\)$` — a numeric `#<issue>` only. tm-dicequest's live
R1/R2 entries use `(source: user directive 2026-08-23, issue #1)`,
free-form text that is not a bare `#<number>`, so the regex never matched
and the watchdog fell back to the `"(다이제스트에 paraphrase 없음)"`
default.

- `spawn.py`: extracted the inline regex into a new module-level
  `parse_digest_live_entries(digest_text)` (with `_DIGEST_LIVE_ENTRY_RE`),
  widening the `source` capture group from `#(\d+)` to `(.+)` — any
  free-form text up to the line's closing paren is accepted verbatim, not
  just a bare issue number. `requirement_drift()` now calls this helper.
  Downstream, `paraphrase, _status, source = live_entries.get(...)` and the
  next-action print line now interpolate `source` directly
  (`f"(source: {source})"`) instead of always prepending a literal `#`,
  since a free-form source string may or may not already carry one.
- `spawn.py::init_requirement_digest`: rewrote the `## R-entry format`
  stub section to state the exact accepted grammar — one line per entry
  (no embedded newline), `<설명>` and `<출처>` both free-form multi-clause
  text, `[<status>]` a single whitespace-free token, `source:` explicitly
  not limited to `#<issue-number>` — and added the tm-dicequest-shaped
  multi-clause example alongside the original short one-liner.
- `gates/test_requirement_drift.py`: added
  `test_tm_dicequest_r1_r2_multi_clause_free_form_source_parses`
  (regression, calls `parse_digest_live_entries` directly on the R1/R2
  digest lines fetched verbatim from `tokenmaxxxer/tm-dicequest`'s
  `docs/specs/requirement-digest.md`, asserts both ids parse with
  non-empty paraphrase, `status == "live"`, and
  `source == "user directive 2026-08-23, issue #1"`) and
  `test_tm_dicequest_r1_r2_flagged_with_paraphrase_when_open` (same
  verbatim shapes, `[live]`→`[open]`, through the full
  `spawn.requirement_drift()` path, asserting the paraphrase-missing
  fallback string no longer appears and the real source text does).

## What did not work

None — no dead ends worth recording; the fix was a single regex/format
change plus a doc-stub rewrite, verified directly against the field data
that produced the original defect report.

## Doc placement ladder

- [x] this record — phase-2 record, build-now bypass (no separate phase-1
  survey/proposal files were written; see Rationale for deviations).

## Rationale for deviations

The role-handoff contract's default flow calls for a phase-1
survey+proposal round before any code lands. This session ran under the
build-now bypass (contract v3 s19a): the invoking task's environment
carried `CORE_BUILD_NOW=1`, set by the spawner, so the proposal round was
skipped per that clause and the fix was delivered directly on
`issue-2077/implementation` in one PR, as the clause specifies.

## Why

`spawn.py::requirement_drift`'s digest-line parser rejected the documented
free-form R-entry grammar whenever `source:` held anything other than a
bare `#<number>` — exactly the shape tm-dicequest's real R1/R2 entries use
(`source: user directive 2026-08-23, issue #1`). This silently degraded the
watchdog's requirement-drift next-action output to a placeholder
(`"(다이제스트에 paraphrase 없음)"`) instead of the real paraphrase/source,
even though the entries were valid per the format doc's own stub.

## Upstream / basis

- docs/issue-1017 (`gates/requirement_linkage.py`, `_INFRA_TAG` convention
  reused unchanged) and issue #1080's exception-parity test file
  `gates/test_requirement_drift.py`, extended in place here.
- Live digest text fetched from `tokenmaxxxer/tm-dicequest` at commit time
  via `gh api repos/tokenmaxxxer/tm-dicequest/contents/docs/specs/requirement-digest.md`
  (cited above).

## Acceptance verification

- check: parser accepts the documented free-form (multi-clause
  single-line) and extracts paraphrase+source; regression test includes
  the tm-dicequest R1/R2 shapes verbatim.
  canonical: python3 -m pytest -q gates/test_requirement_drift.py
  result: pass, 8 passed (includes both new tm-dicequest tests), executed
  live this session.
- check: init_board digest stub states the exact accepted grammar.
  canonical: python3 -c "import spawn,inspect; s=inspect.getsource(spawn.init_requirement_digest); print('#<issue-number>' in s and '자유 형식' in s)"
  result: pass (printed True), executed live this session;
  `spawn.py::init_requirement_digest` stub text states one-line-per-entry,
  free-form `<설명>`/`<출처>`, `source:` not limited to
  `#<issue-number>`, and a tm-dicequest-shaped multi-clause example.

## skill-verdicts

- skill-verdict: implementation-complexity-coupling-management —
  not-applicable: no coupling/cohesion threshold, accessor-chaining, or
  cross-module import-direction decision was in scope — this was a single
  regex/format widening plus a doc-stub rewrite in one existing module.
- skill-verdict: implementation-design-pattern-selection —
  not-applicable: no GoF-style pattern (Strategy/Factory/Visitor/
  Observer/Decorator) was being introduced or reconsidered; the change is
  a direct regex/format fix.
- skill-verdict: implementation-performance-data-structure-choice —
  not-applicable: no data-structure/algorithm/communication-scheme choice
  was in scope — parsing stays a single-pass regex over an already-small
  digest file, unchanged in shape from before.
- skill-verdict: implementation-blueprint — invoked; applied: loaded
  SKILL.md before editing (skill mandates checking before non-trivial
  multi-module structure work); its classify step vetoed structure here —
  this is a small single-file regex/format fix with no new
  module-spanning architecture, so no blueprint/pattern was applied beyond
  extracting the inline regex into one named, directly-testable module
  function (`parse_digest_live_entries`), which the skill's own classify
  step treats as the correct minimal move for a change this size.

## Open findings

None.

## Next steps

None — `loop_state: landed`, terminal for this record's kind. PR carries
`Closes #2077`.
