## Scope of this scout pass

This is a non-product, internal test-infrastructure decision (which
assertion shape a single pytest function should use), not a product-facing
comparison. Per the scout directive's own guidance for non-product roles
("scout the best of their own deliverable's kind"), the relevant prior art
is established software-testing practice on tests coupled to
implementation/production state, not an exemplar product. One search angle
was run (not the full 4-angle sweep) — stated explicitly here as the
directive requires when a reduced pass is used: a single well-scoped
question ("how do strong test suites avoid coupling a test to an incidental,
mutable fact about the system under test") does not need multiple
concurrent angles to saturate; a second angle was judged unlikely to change
the build decision already visible from the survey (gates/gates.py's own
producer-exclusion regex plus the two swap-candidate fields already
enumerate the realistic option space).

Mode: single-angle WebSearch, one stage, well under the 5-stage/3-minute
budget.

## Must-bes (from the field, applied to this decision)

- Tests should assert on **behavior/invariants**, not on **incidental
  implementation details** that can change without the behavior being
  wrong — coupling to an incidental detail produces failures on correct
  changes ("brittle tests"), which is exactly this issue's second
  occurrence.
- When a test needs to verify "the system correctly flags condition X
  somewhere," and multiple instances of X exist or come and go over time,
  asserting existence of *any* qualifying instance is a stronger, more
  durable claim than pinning one instance by name — the pinned-name
  version re-fails every time that one instance stops qualifying, even
  though the behavior under test never changed.
- Prefer isolating unit-level assertions (synthetic fixtures) for the core
  logic, and reserve a smaller number of real-state/integration checks for
  what synthetic fixtures cannot prove (e.g., that the logic still behaves
  correctly at the real system's scale/encoding/exclusion-list surface) —
  this repo's own test file already follows this split (four synthetic
  `schema_field_orphans` tests, one real-tree test), which matches the
  general pattern rather than contradicting it.

## Adopt / skip, applied to this build

- **Adopt**: replace the single hardcoded field-name assertion with a
  structural "the gate flags at least one real orphan" assertion — this
  keeps the real-tree integration check (the one thing the four synthetic
  tests cannot cover) while removing the brittle coupling to one field's
  name.
- **Skip**: rewriting the test as a synthetic/tempdir fixture (mirroring
  the file's other four `schema_field_orphans` tests) — per the survey
  (docs/issue-811/reports/implementation/survey.md, "Audit" section), those
  four already fully cover "the gate correctly flags a field it can
  prove is unread." Converting the fifth test to match would drop its only
  incremental value (real-tree integration coverage) rather than fix the
  brittleness, which is a worse trade than the adopted option.

## Gap line

The field's must-be ("assert invariants, not incidental details") is
already partly met by this repo's test suite (four of five
`schema_field_orphans` tests are synthetic/invariant-shaped); the gap is
narrow and specific — exactly the one real-tree test pins an incidental
detail (a field's current name) instead of the invariant its own docstring
already claims to test ("the gate catches a real orphaned field in the
actual tree"). Closing that one gap does not require adopting a
new pattern this repo lacks; it requires the existing test's assertion to
match what its own stated purpose already says.

## Sources

- [Preventing Brittle Tests (and Production Code) — James Grenning](http://blog.wingman-sw.com/preventing-brittle-tests)
- [Software Engineering at Google: Unit Testing, ch. 12](https://abseil.io/resources/swe-book/html/ch12.html)
- [What Are Brittle Tests? Definition & How to Prevent Them — Autify](https://autify.com/blog/brittle-tests)
