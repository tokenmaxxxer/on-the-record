---
code_under_review:
  - on-the-record/hooks/skill-verdict-guard.sh
  - on-the-record/hooks/test_skill_verdict_guard.py
loop_state: landed
type: bugfix
breaking: false
verdict: pass
---

# Implementation — skill-verdict-guard extract_names comma-split fix (issue #2057)

canonical: on-the-record/hooks/skill-verdict-guard.sh:98-158 (read this session)
skill-verdict: implementation-complexity-coupling-management — not-applicable: the change is a parser-boundary fix inside one already-single-purpose function (`extract_names`), not a coupling/cohesion refactor of existing module structure.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-style pattern decision arose; the fix is a manual depth/state scanner replacing a naive `str.split(",")`, not an indirection choice.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: the scan is a single linear walk over one short prompt line; no performance-cliff-shaped structure/algorithm choice was involved.
skill-verdict: implementation-blueprint — not-applicable: the write set (one function inside an existing embedded-python heredoc, plus its regression test) was fully determined by the frozen issue text — no fresh multi-module architecture decision was open.
skill-verdict: test-derivation — applied: the issue's own Acceptance criterion was pulled directly into the two new regression tests named below (`t_issue_2044_line_yields_exactly_six_real_names`, `t_issue_2044_line_with_all_six_verdicts_passes`), one per Acceptance clause.

## What was done

1. `on-the-record/hooks/skill-verdict-guard.sh` — rewrote `extract_names()`.
   The old version split a mounted-skill line on every comma and took
   each fragment's text before its first `" ("`/`" — "`. Real mounted-
   skill lines (spawn.py:8318-8361) join entries with `", "`, but each
   entry's own `"Use ..."` trigger sentence is itself free text that
   can contain internal commas (e.g. "Use when a class's coupling ...
   crosses a threshold, a caller chains ..."), so the naive split
   fragmented those sentences into bogus "skill names" — observed live
   by the issue-2044 session.

   canonical: docs/reports/deviation-log.md:95 (read this session,
   deviation-log entry filed by the issue-2044 session)

   The fix exploits a structural invariant in spawn.py's own trigger
   extraction: `_SKILL_USE_SENTENCE_RE = re.compile(r"(Use\b[^.]*\.)")`
   (spawn.py:8080) guarantees a trigger never contains a literal `.`
   except its own terminating one. `extract_names` now walks the line
   character-by-character, tracking paren depth and whether it is
   inside an unterminated `"Use "` sentence, and only splits on a comma
   that sits at paren-depth 0 AND outside such a sentence. Each
   resulting fragment is still run through the original
   before-first-`" ("`/`" — "` trim, then validated against a bare
   identifier pattern (`^[A-Za-z0-9][A-Za-z0-9._-]*$`) before being
   accepted as a name — this discards leftover prose/paren tails (e.g.
   the trailing `"(skill-repository <sha>) 가이던스만 붙는다 ..."` clause
   and the cross-family parenthetical) that the split alone cannot
   fully separate from a real name.

2. `on-the-record/hooks/test_skill_verdict_guard.py` — added two
   regression tests using the verbatim issue-2044 mounted-skill line
   (recovered from that session's own local transcript, since the
   deviation-log entry only paraphrases it):
   - `t_issue_2044_line_yields_exactly_six_real_names` — unit-level:
     execs `extract_names` straight out of the hook's embedded python
     heredoc and asserts it returns exactly the 6 real names, in order,
     for the verbatim line.
   - `t_issue_2044_line_with_all_six_verdicts_passes` — end-to-end:
     runs the full hook subprocess against the verbatim line plus a
     record carrying one `skill-verdict:` line per real skill, and
     asserts the hook stays silent (exit 0, empty stdout).

## Why

The bug stranded a session whose mounted-skill descriptions contain
commas with a verdict obligation it could never satisfy, since the
guard demanded lines for fragment names that do not exist (the
issue-2044 session's concrete case). The fix targets the parser's
actual failure mode (comma-inside-trigger) rather than papering over it
with a broader allowlist or disabling the check.

## Upstream / basis

Issue #2057. Upstream context: issue #2039 (per-mounted-skill verdict
obligation, the guard this hook enforces) and issue #2044 (the session
whose live prompt exposed the bug).

## Acceptance verification

canonical: acceptance: python3 -m pytest -q on-the-record/hooks/test_skill_verdict_guard.py — result: PASS

```
$ python3 -m pytest -q on-the-record/hooks/test_skill_verdict_guard.py
..........                                                               [100%]
10 passed in 0.94s
```

Coverage: extract_names over the verbatim issue-2044 line (exactly 6
real names), a record with one verdict line per real skill, and all
pre-existing guard-behavior tests (zero-mounted noop, missing/empty
verdict blocked, dual-assembly-point union, satisfied-verdicts case,
stop_hook_active silence, malformed payload fail-closed, ORCHESTRATE_OFF
noop).

canonical: acceptance: python3 -m pytest -q -m "not slow" — result: PASS

```
$ python3 -m pytest -q -m "not slow"
2574 passed, 19 xfailed, 2 xpassed in 43.45s
```

Fast tier per `.on-the-record/test-tiers.json`; 19 xfailed/2 xpassed are
pre-existing marked outcomes carried over from before this change.

Tiering note: this diff also matches `.on-the-record/test-tiers.json`'s
`slow` trigger classes (`on-the-record/hooks/*.sh`,
`on-the-record/hooks/test_*.py`), so the `slow` command
(`python3 -m pytest -q -m slow`) was also launched; per the
observe-only test-tier directive this is recorded as a tiering-gap note
rather than a claimed result, since it was still running in the
background as this record was drafted.

## What did not work

None.

## Rationale for deviations

None — this session ran under the build-now bypass (contract v3 s19a,
CORE_BUILD_NOW=1), so there is no approved phase-1 proposal to diverge
from; the delivered write set matches the issue's frozen scope exactly.

## Open findings

None.
