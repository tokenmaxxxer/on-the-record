# Deviation log — issue-2208 (implementation role)

- 2026-08-24T14:21:00Z | inline | before-landing `warrant-hunter` dispatch (stance 0) on the negative-clause-stripping diff (acceptance item 2).
acceptance: docs/issue-2208/reports/implementation/2026-08-24-hunt-skill-selection-followups.md "Fixed" section — result:
```
declared phrases (after fix): ['normal family trigger phrase']
outcome: fail-open   # was fast-path:some-other-family-skill before the fix
```
acceptance: git diff pipeline.py (checkpoint commit 8e934e0d) — result:
```
first pass: _strip_negative_scope() applied to _skill_bm25_document() only
gap: _skill_declared_phrases() (same raw description, feeds fast-path) left unstripped
fixed: same commit, inline, within the frozen write set, mechanical, one-off
```
