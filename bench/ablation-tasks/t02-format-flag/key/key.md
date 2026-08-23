# Answer key — t02-format-flag (HIDDEN: never enters a run workspace)

Class: feature  ·  Fixture: harness/fixture-feature

## Acceptance behaviors (one scoresheet row each)

- **a1** — `fixture-feature greet World` prints `Hello, World!` (default unchanged).
- **a2** — `fixture-feature greet World --format json` prints valid JSON exactly of shape {"message": "Hello, World!"}.
- **a3** — `--format` rejects values other than json|text (argparse choices or equivalent) rather than silently falling back.
- **a4** — Tests cover BOTH formats and pass; existing test file still passes.

## Adjudication

Execute both invocations; parse the json output with json.loads. a3: try `--format xml` and expect a non-zero exit with a usage error.
