kind: scout-brief
subject: issue-1160
mode: batched-sequential (no web fan-out — see scope note below)
stages: 1

## Scope note (why no external/product sweep)

This deliverable is internal orchestration machinery (a predicate
evaluator + an advisory print surface + a bar-verdict linkage
function), not a product-facing artifact — there is no external
category with best-in-class exemplars to sweep (no comparable public
"role need-detector" product). Per scout-directive, the comparable
field for a non-product role deliverable is "the best of comparable
systems already in this repo" — so the sweep angle used is: how does
this repo already solve the same three shapes (predicate evaluator,
advisory-only print surface, anti-circular verdict linkage)? Answered
by reading the actual implementations, single session, no parallel
fan-out needed (all three answers live in two files already read in
the survey).

## Must-bes (what the existing in-repo pattern requires)

- A predicate evaluator is a **pure classifier over structured fields**,
  never prose re-read by an LLM at gate time — `gates/roles_due.py`'s
  own docstring states this explicitly ("No LLM re-reading
  `board_condition` as prose here — determinism and auditability").
  canonical: gates/roles_due.py lines 1-17 (read this session, quoted
  in the survey).
- An advisory surface prints reasons, it does not act — `roles_due.py`'s
  `format_report()` returns plain text lines; the caller (`spawn.py`'s
  `roles-due` subcommand) prints them and does nothing else.
  canonical: gates/roles_due.py `format_report` (tail of file, read this
  session) and spawn.py lines ~5072-5079 (`roles-due` subcommand, read
  this session).
- Anti-circular verdict linkage is **account-resolved, never
  `CLAUDE_ROLE`-resolved** — `quality_bar.classify`'s own docstring
  states the same-operator bypass this guards against.
  canonical: gates/quality_bar.py module docstring + `classify` body
  (full file, read this session).

## Performance axes this build competes on

1. Determinism/auditability (structured fields, not prose re-parsing).
2. Reuse over reinvention (extend `quality_bar.classify`, don't
   duplicate its anti-circularity logic).
3. Hermetic testability (pure functions over in-memory fixtures, the
   `test_quality_bar.py` convention, not shelled-out `/tmp` dirs).

## Adopt / skip

- Adopt: `roles_due.py`'s split between a pure evaluator module and a
  thin `spawn.py` subcommand that only prints — mirrored for the
  need-detector.
- Adopt: `quality_bar.classify`'s account-based anti-circularity,
  called (not reimplemented) for `verified_by` linkage.
- Skip: parsing `need_detector.condition`'s free-form prose with a
  regex/heuristic. Prose is exactly what `roles_due.py`'s docstring
  warns against re-reading at gate time. Instead the proposal adds a
  small structured sibling shape next to the existing prose field (the
  prose stays as the human-readable spec contract, matching how
  `board_condition` prose already coexists with `trigger`'s structured
  fields on other specs).

## Gap line

Repo already has (meets the bar): a structured predicate evaluator
pattern (`roles_due.py`) and an anti-circular verdict classifier
(`quality_bar.py`) — both reusable, not novel.
Repo is missing: any evaluator that reads `use_when.need_detector` at
all, any print surface for it, and any call site that feeds
`mission_deliverables`/`verified_by` into `quality_bar.classify`.
canonical: docs/issue-1160/reports/execution-observation.md's own
`grep -rn "need_detector" gates/ spawn.py on-the-record/hooks/` (zero
hits, cited there) and this session's survey.

## Sources

(Internal-only sweep — no web sources consulted; all claims above cite
in-repo file:line reads listed in docs/issue-1160/reports/implementation/survey.md.)
