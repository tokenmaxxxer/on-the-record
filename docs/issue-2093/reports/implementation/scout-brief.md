# Scout brief — issue #2093 hook-crash class fix

kind: scout-brief
loop_state: scouted

Mode: parallel fan-out. Stage 1 sweep ran 4 angles concurrently in one dispatch
(hook-platform semantics / total-parsing prior art / registry-driven conformance testing /
shell-string parsing robustness); the pass stopped at 2 stages — the sweep plus one
deepening round — on the saturation rule, inside the 3-minute budget. Angles were aimed at
the survey's §5 (where a shared module may live), §6 (test cost), §7 (ledger shape) and §9
(exit-code semantics) gaps, not at the issue text alone.

## Category must-bes

- A hook's crash is fail-open **by platform design**: exit 0 = success, exit 2 = blocking
  (stderr becomes the block reason), and *any other nonzero — including the 1 an unhandled
  Python traceback produces — is non-blocking*. The action proceeds. Timeouts and missing
  scripts behave the same way. [1]
- Read all of stdin before attempting to parse it, and exit 0 with empty output for
  "no decision" rather than exit 1. [1]
- Convert unstructured input to a structured type or an explicit failure value once, at
  the boundary, so downstream code cannot observe the invalid state. Python has no native
  Result type; the working idiom is a small typed union — a success dataclass or a typed
  `Unparseable(reason)` — returned, never raised. [2][3]
- Shell-string parsing must catch broadly and degrade, not crash: `shlex.split()` raises
  `ValueError` on unbalanced quotes and has no heredoc support. [4]
- A registry-driven conformance gate should be a fixed, versioned `pytest.mark.parametrize`
  table over the declared hook list, so the merge signal is deterministic. [5]

## Performance axes the field competes on

1. Determinism of the gate signal (fixed corpus, table-driven) vs. discovery power
   (Hypothesis-style generation). A merge gate cannot maximise both. [5][6]
2. Fail-open vs fail-closed under guard failure — already resolved by the platform's
   exit-code table, so the remaining lever is *visibility*, not enforcement strength. [1]
3. Parse fidelity vs. cost: full shell-grammar parsing (bashlex) is more correct than
   `shlex`, heavier, and *still* throws on edge grammar — so both paths need a fallback. [4][7]

## Adopt

Typed non-exception failure return from the shared parser, with a broad-catch fallback to
an opaque/unknown verdict. Two independent sources converge on it: parse-don't-validate as
the principle [2][3], and the gptme project's concrete precedent of wrapping
`bashlex.parse()` in try/except and falling back to treating the whole string as one opaque
command with a logged warning rather than crashing [7].

## Skip

Do **not** try to make a crashing guard fail *closed* (e.g. by having the hook exit 2 on
its own internal error). The platform's table means a nonzero-but-not-2 exit is already
non-blocking, and reaching a deliberate exit 2 requires the crash-handling code to have run
correctly in the first place. Engineering effort belongs in the ledger that makes the
silent failure loud afterwards, not in fighting the exit-code semantics. [1]

## Segment fit

The comparable class is not "a linter" but "a fleet of small advisory guards driven from a
manifest" — the field's exemplars here are the platform's own hook docs and registry-driven
parametrized test suites, both of which this repo is already close to structurally.

## Gap line

Already met by the current state: exit-0-on-environment-gap discipline (documented in
`docs/handbooks/hooks.md`, honoured throughout), and the JSON-decode step is already
try/except-wrapped in every sampled hook. Missing: the typed-failure boundary (there is no
shared parser at all — three divergent ad-hoc `cd` extractions instead), the registry-driven
conformance corpus (no test enumerates `hooks.json`), and the fail-open ledger (only
`contract-guard.sh` writes any provenance line, and it records verdicts, not crashes).

## Assumptions (no source found — stated as assumptions, not findings)

- "Fail-open is correct for advisory guards" as a general security-design principle. The
  searched sources did not state such a rule; what *is* sourced is that Claude Code's hook
  runtime enforces fail-open unconditionally on crash [1], so the design must accept it.
- No off-the-shelf edge-input corpus for shell-command parsing exists; the corpus
  (unexpanded `~`, heredoc body, nested quotes, unicode, empty command, 100KB command,
  missing fields, non-dict payload) has to be authored here.

Sources:
1. https://code.claude.com/docs/en/hooks
2. https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/
3. https://www.ricardodecal.com/opinions/parse-don-t-validate-in-python/
4. https://pymotw.com/3/shlex/
5. https://docs.pytest.org/en/stable/example/parametrize.html
6. https://oneuptime.com/blog/post/2026-01-30-how-to-build-property-based-testing-with-hypothesis/view
7. https://github.com/gptme/gptme/issues/799
