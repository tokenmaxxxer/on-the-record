# Current-state survey — issue #566 implementation

Write set this proposal will freeze (the first two paths do not exist yet; the third is edited):
- new hook script: `product-capture-stopgate.sh`, under `on-the-record/hooks/`
- new test file: `test_product_capture_stopgate.py`, under `on-the-record/hooks/`
- edited: `on-the-record/hooks/hooks.json` (fifth `Stop` entry)

## What exists

`docs/issue-566/proposals/architecture.md` (merged PR #569) is the frozen design: hook name,
transcript-walk payload shape, four-category EN+KO regex vocabulary, `docs/product/*.md` git-diff
cross-check, bootstrap-on-first-flag behavior, advisory `additionalContext` output, `hooks.json`
placement as the fifth `Stop` entry after `report-framing-check.sh`. This proposal does not reopen
any of those decisions — it is the build plan for exactly what architecture specified.

The `Stop` array in the hook-registration file currently holds four entries in order:
`stop-gate.sh`, `role-test-claim-guard.sh`, `decision-queue-stopgate.sh`, `report-framing-check.sh`.
Architecture's placement instruction appends a fifth after the last.

Two existing `Stop` hooks model the two techniques this hook combines:
- `decision-queue-stopgate.sh` — the "not a single last-message check" shape: no-ops on
  `CLAUDE_ROLE` set, honors `ORCHESTRATE_OFF`, fails closed via
  `trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT`, resolves the
  on-the-record checkout via a `_checkout_resolve` cascade (env var → walk-up → marketplace →
  own-checkout → clone), shells to Python for the actual logic via a heredoc fed through an env
  var, emits `hookSpecificOutput.additionalContext` (advisory) or `decision: block`.
- `stop-gate.sh` — the `last_assistant_message`-driven regex-detection shape: same kill-switch/
  fail-closed skeleton, a Python heredoc doing `re.search` category matching, advisory
  `additionalContext` naming what was missing.

This hook's payload is `transcript_path`, not `last_assistant_message` — architecture's
"Payload" section calls this out explicitly as additive to the existing `*_PAYLOAD`-env
convention. No existing `Stop` hook here walks a transcript JSONL today, so this is new plumbing
inside the established skeleton, not a reused code path.

`record-scaffold.sh` is the only existing "create the skeleton, never overwrite" precedent
(CLI-invoked, per-role record files) — architecture's bootstrap section explicitly mirrors its
write-if-absent rule while noting this hook's bootstrap fires automatically rather than via CLI
invocation.

`gates/` is a separate mechanical-gate surface, out of this proposal's write set; this hook lives
entirely under the deployed hooks directory the issue names as the enforcement surface.

Test convention: the existing stopgate test files both invoke the hook as a subprocess
(`subprocess.run(["bash", str(HOOK)], input=<json>, env=<patched>)`), stub external state via a
temp directory (a fake checkout, or a fake git repo), and use bare `t_*` functions (no pytest
class, no fixtures) as the test-collection convention throughout the hooks directory. This hook's
tests will need a temp git repo (for the product-docs diff cross-check and bootstrap) plus a temp
transcript JSONL file (for `transcript_path`) — no existing test file combines both, so the
fixture helpers are new but the `t_*`/subprocess pattern is reused verbatim.

## Skip condition check

Scout-directive skip conditions (pure bugfix / spec leaves no design decision open): this is a
new hook build with architecture's design already fully fixing every decision that would
otherwise need scouting (vocabulary, cross-check mechanism, bootstrap, wiring) — the second skip
condition applies. No open design surface remains for this proposal to scout; it translates an
already-frozen design into code. Scouting is skipped on that basis.
