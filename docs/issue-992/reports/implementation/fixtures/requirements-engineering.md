Subject: issue-992

# Live-fire seed tasks — requirements-engineering (`finding_method`/`anti_pattern`)

Per `roles/specs/requirements-engineering.spec.json`'s new
`finding_method` and `anti_pattern` fields.

## Fixture 1 — grammar-fit mismatch masked by a plausible-sounding tag

Hypothetical requirement entry under test:

```
statement: "THE system SHALL retry a failed upload up to 3 times before surfacing an error to the user"
ears_pattern: ubiquitous
```

- Generic reasoning: the statement starts with "THE system SHALL", the
  ubiquitous template's opening words, so the pattern tag looks right.
- Methodology-correct (finding_method item 1, grammar-fit check per
  Mavin et al., IEEE RE'09): the statement describes behavior
  conditioned on a triggering event (an upload failing) — this is the
  event-driven template ("WHEN <trigger>, THE system SHALL <response>"),
  not the ubiquitous template, which by definition carries no trigger
  clause. Finding: anti_pattern "Untraceable pattern claim" — the
  declared pattern does not match the statement's own grammar, meaning
  the trigger/precondition analysis EARS requires for event-driven
  requirements was skipped for this statement.

Divergence: surface word-matching on the opening clause reaches "tag is
fine"; checking the full grammar against the declared pattern's
definition reaches "mismatched pattern, trigger analysis skipped."

## Fixture 2 — compound requirement hidden behind a single verification_method

Hypothetical requirement entry under test:

```
statement: "WHEN a user submits a payment, THE system SHALL validate the card number and SHALL send a confirmation email"
ears_pattern: event-driven
verification_method: Test
downstream_link: docs/issue-<n>/reports/implementation.md
```

- Generic reasoning: one statement, one pattern tag, one
  verification_method, one downstream_link — looks like a normal,
  well-formed entry.
- Methodology-correct (finding_method item 4, single-requirement check):
  the <response> clause asserts two independently verifiable outcomes
  (card validation, confirmation email) joined by "and" — a single test
  and a single downstream_link cannot unambiguously cover both, so a
  failure in either outcome is untraceable to which half broke. Finding:
  anti_pattern "Compound requirement" — split into two statements, each
  with its own verification_method and downstream_link.

Divergence: field-population scanning (every field is filled in)
reaches "well-formed"; the single-requirement check reaches
"structurally hides two requirements," which changes what
downstream_link and verification_method must each independently point
to.
