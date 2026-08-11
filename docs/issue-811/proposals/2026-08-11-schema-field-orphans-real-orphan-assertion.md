---
status: proposed
files:
  - gates/test_capability_gates.py
  - docs/issue-811/reports/implementation.md
  - docs/issue-811/reports/implementation/survey.md
  - docs/issue-811/reports/implementation/scout-brief.md
  - docs/issue-811/proposals/2026-08-11-schema-field-orphans-real-orphan-assertion.md
---

## Request

Issue #811: `t_actual_tree_schema_field_orphans_catches_alive`
(gates/test_capability_gates.py) is `main`'s only failing test right now.
It pins a specific `docs/specs/flows-schema.md` field name (`alive`) as
"the one real orphan the gate must catch in the actual tree"; a legitimate
consumer of `alive` now exists, so the pin no longer holds. The same test's
docstring already records one prior exhaustion of this exact shape
(`decision_queue`, issue-466). Decide, with recorded reasoning: swap to
another currently-orphaned field, or change the fixture shape entirely so
this class of failure stops recurring; make failure messages self-
explanatory for any future exhaustion; and enumerate any other test in the
repo with the same live-tree-name-pinning shape.

## Constraints

- Do not change `schema_field_orphans`'s judgment logic
  (gates/gates.py) — the gate did its job; the test's fixture premise is
  what broke.
- Do not revert whatever now reads `alive` — that change is legitimate.
- The fixed test must still exercise the real repo tree (not a synthetic
  temp fixture) for the same reason it was written that way originally:
  the file's other four `schema_field_orphans` tests already cover "the
  gate flags a field it can prove is unread" via synthetic fixtures: any
  fix that drops the real-tree dependency loses coverage those four don't
  provide (real-tree scale/encoding/exclusion-list behavior), which the
  issue explicitly warns against trading away silently.
- `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` must return
  zero failures after the fix (issue's Acceptance #1); the survey's repro
  run already shows this is the only failure on `main` right now.

## Rationale

**Chosen approach: replace the hardcoded field-name assertion with a
structural "the gate flags at least one real orphan" assertion**, and give
it a message that states its own two possible failure causes.

Concretely: `assert any("alive" in b for b in bad), bad` becomes
`assert bad, <message naming both possible causes>` in a renamed test
(`t_actual_tree_schema_field_orphans_catches_alive` →
`t_actual_tree_schema_field_orphans_catches_a_real_orphan`), with a rewritten
docstring recording the `decision_queue` → `alive` → this-fix lineage and
stating plainly that the test intentionally no longer pins any single field
name.

This is the strongest option among those considered because the test's own
docstring already states its true purpose: "the gate catches a real
orphaned field in the actual tree" — not "the gate catches the field named
`alive`." The specific field name was always an implementation detail of
how that purpose got encoded, not the purpose itself; asserting `bad` is
truthy tests the stated purpose directly, is immune to any single field's
future legitimate consumption, and requires no lookahead about which field
is "safe" for a while. It also directly satisfies the issue's Acceptance
#2 ("the next exhaustion is readable from the failure message") without
needing that criterion's explicit N/A escape hatch: the failure mode this
test can still hit (zero fields orphaned repo-wide) is a different, rarer
event than field-level exhaustion, and its assertion message names both
readings up front (the gate is broken, or every documented schema field is
now read somewhere).

**Known limitation, surfaced by this proposal's own after-proposal warrant
hunt** (docs/issue-811/reports/implementation/2026-08-11-hunt-schema-field-orphans-real-orphan-assertion.md):
`schema_field_orphans`'s producer-skip excludes a field name's entire file
the moment any producer-shaped occurrence appears in it (matching its own
docstring — the file that assigns/initializes the field is excluded), so a
field produced and later self-consumed within that same file (e.g.
gates/flows.py's own `errors = payload.get("errors")` read-back) still
reports as orphaned. `assert bad` can therefore stay green off an entry
like `errors` even in a hypothetical world where the gate's ability to
detect a true, no-reader-anywhere orphan regressed to zero. This is not a
new weakness this proposal introduces: it is a property of
`schema_field_orphans`'s own judgment logic (out of scope for this issue to
change), and it applied to `alive`/`decision_queue` equally while they were
the pinned fixture — neither prior pin is known to have been a strict
zero-reader field either, since both were produced (and, before their
independent consumers landed, most likely self-printed) inside
gates/flows.py the same way the five current candidates are. Pinning to a
single "cleaner" field does not remove this limitation: of the five fields
`schema_field_orphans` currently flags, only `ts` is not self-consumed
within its producer file — and the survey ranks `ts` as a worse long-term
pin regardless, since it collides with an unrelated generic local-variable
name used throughout spawn.py. This proposal accepts the limitation rather
than papering over it with test-side special-casing of the gate's
producer-skip semantics, which would itself start coupling the test to the
gate's internal judgment logic — the exact line the issue draws as out of
scope. The rewritten test's docstring states this limitation plainly (see
"What will be done") so a future reader does not need to rediscover it.

**Alternative A — swap the pin to another currently-orphaned field
(`closure_sweep_skips`, `elapsed_min`, `errors`, `ts`, or
`unapproved_open_prs`; survey ranks `closure_sweep_skips` as the most
durable of the five, since it is a single-locus fact with no name
collision, versus `errors`/`ts` colliding with an unrelated `word=`
kwarg/local-variable idiom used throughout the codebase, and versus
`unapproved_open_prs` sitting in an actively-developing governance area
this session's own directives reference).** Rejected: swapping only delays
the identical failure — it does not address why the issue calls this a
"예고된 재발" (foretold recurrence). Pinning to any single field name keeps
the test coupled to an incidental fact about today's repo instead of the
invariant it is actually meant to prove; a third exhaustion under this
alternative is not a possibility to plan message-clarity around, it is a
near-certainty on the same timeline as the first two.

**Alternative B — synthesize a temp-dir fixture, matching the file's other
four `schema_field_orphans` tests, and drop the real-tree dependency
entirely.** Rejected: those four synthetic tests already fully cover "the
gate correctly flags a field it can prove is unread / clears a field it can
prove is read" in isolation. This test's only incremental value is proving
the gate's logic still behaves correctly when it runs against the real
tree's actual scale, encodings, and exclusion-list interactions — a class
of bug synthetic minimal fixtures cannot surface. Fully synthesizing away
would silently drop that coverage, which is exactly the tradeoff the issue
asks to be judged explicitly rather than defaulted into — and the chosen
approach gets the recurrence fix without paying that cost.

## What will be done

- gates/test_capability_gates.py: rename
  `t_actual_tree_schema_field_orphans_catches_alive` to
  `t_actual_tree_schema_field_orphans_catches_a_real_orphan`; replace the
  hardcoded `"alive" in b` assertion with `assert bad, <message>` where the
  message states, inline, that a failure means either every documented
  `docs/specs/*.md` field is now read somewhere (test needs a new case) or
  `schema_field_orphans()` itself regressed; rewrite the docstring to
  record the `decision_queue` (issue-466) → `alive` (issue-811) lineage,
  state the test no longer pins any single field name, and note the
  producer-skip limitation the after-proposal warrant hunt surfaced (a
  field self-consumed only within its own producer file still counts as
  orphaned, by the gate's own documented design) so a future reader does
  not need to rediscover either fact.
- Confirm `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` returns
  zero failures.
- docs/issue-811/reports/implementation.md: the phase-2 record, written at
  the start of phase 2 per contract v3 s19, carrying the survey's
  same-shaped-test audit finding (`t_actual_tree_ci_reachable_gates_catches_writeset_and_record_enums`
  is the same brittle shape, not fixed here) and the warrant-hunt result
  from this proposal's after-proposal dispatch.
- This survey, this scout brief, and this proposal (already phase-1
  output).

## Out of scope

- `schema_field_orphans`'s judgment logic (gates/gates.py) — untouched,
  per the issue's explicit exclusion.
- Reverting whichever change made `alive` a legitimate read.
- Fixing `t_actual_tree_ci_reachable_gates_catches_writeset_and_record_enums`
  (gates/test_capability_gates.py) — the survey's audit places it in the
  identical brittle shape (pinned to `gates.writeset`/`gates.record_enums`
  staying CI-unwired), but issue #811's acceptance criteria are scoped to
  the `schema_field_orphans` test only, and `gates/ci.py`'s CI-wiring is a
  separate subsystem. Recorded as a same-shape candidate for a follow-up
  issue, per this issue's own ask to enumerate and record, not to fix.
- Any other repo-wide test failure — the survey's full-suite run shows
  exactly one failure, the one this proposal fixes.
- Fixing `schema_field_orphans`'s whole-file producer-skip (it hides a
  field genuinely self-consumed within its own producer file, per the
  after-proposal warrant hunt) — this is the gate's own judgment logic,
  out of scope per the issue text; recorded above as an accepted
  limitation and flagged here as a second same-shape candidate for a
  follow-up issue, alongside `ci_reachable_gates`'s CI-wiring pin.

## How you'll know it worked

- `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` reports zero
  failures (issue Acceptance #1).
- The rewritten test's assertion message, read on its own, states both
  possible root causes for any future failure without requiring a second
  investigation session to derive them (issue Acceptance #2, satisfied
  directly rather than via its N/A escape hatch).
- The phase-2 record names the same-shaped-test audit finding explicitly,
  matching the issue's third ask.
