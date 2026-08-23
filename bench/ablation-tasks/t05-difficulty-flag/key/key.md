# Answer key — t05-difficulty-flag (HIDDEN: never enters a run workspace)

Class: feature  ·  Fixture: harness/fixture-arcade

## Acceptance behaviors (one scoresheet row each)

- **a1** — `fight --seed 1 --battles 5` output with --difficulty normal (and with the flag omitted) is byte-identical to the pre-change output for the same seed.
- **a2** — easy produces strictly weaker monsters and hard strictly stronger ones (by the arm's own stated rule), observable in outcomes or stats.
- **a3** — The design choice (what is scaled, by how much, and why) is explicitly stated in the deliverable/report — not implicit in the diff.
- **a4** — Tests cover at least normal-unchanged plus one non-normal difficulty, and pass.

## Adjudication

a1 requires capturing pre-change output from a clean fixture copy and diffing. a3 is a design-articulation row: judge the report text.
