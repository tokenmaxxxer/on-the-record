<!-- on-the-record orchestrate directive, on-demand section file (issue #2102). Loaded via the always-on index injected by hooks/directive.sh. ${CHECKOUT} below means the on-the-record checkout path printed in that index. -->

- ACCEPTANCE FORMAT: when an `## Acceptance` criterion you draft
  references an executable artifact (a backtick command, or a backtick
  `test/`/`gates/` path, or a `gate:`/`check:` line), write `check:`/`empty
  state:`/`provenance:` each on its own line — never inline in one
  sentence. `gates/acceptance_gate.py` enforces this post-hoc as a
  backstop; writing it right the first time skips the reject/rewrite
  round-trip.
- NEGATIVE CRITERIA (issue #2414, Failure A): if your issue's body uses
  a mechanism-shaped verb (append/prune/purge/retire/rotate/refuse/
  reject/deny — the exact list is `gates/acceptance_gate.py`'s
  `_MECHANISM_TRIGGER`), also write a `must not:` line under Acceptance
  — what the mechanism you are adding must NEVER do, or what it must
  leave working. Three same-day incidents (#2291→#2393, #2383/PR
  #2389→#2411) landed an Acceptance that said what a new mechanism must
  DO and never what it must NOT do; a background warrant-hunter or the
  orchestrator caught each one only after merge, costing a full extra
  spawn→observe→land cycle. If the trigger fires on your issue but it
  adds no mechanism (e.g. describing a bug's symptoms in the same
  vocabulary), write `must not: not applicable — <reason>` — the same
  escape shape `empty state:` already uses. Two things this does NOT
  do: it does not close the gap completely (an author who cannot
  imagine the counter-example still passes), and it does not catch a
  mechanism-adding issue that never uses any of the trigger verbs (the
  trigger is deliberately narrow — a broader one was measured to newly
  block 34 of 45 open issues that mostly add no mechanism at all; this
  one blocks 14).
- CONVERGENCE EVIDENCE (issue #2414, Failure B, opt-in): when a `check:`
  is about a mechanism reaching a target population (prune, retire,
  rotate, clear a backlog — not just "ran without error"), add a
  `population: <corpus>` line under it (same indented shape as
  `provenance:`). Declaring it is optional and changes nothing for
  checks that aren't population-shaped. Once declared, a check claiming
  `provenance: executed-live` needs a before/after numeric pair (`341 ->
  41`) somewhere in the PR diff's added lines — `gates/requirement_met.py`
  enforces this deterministically at landing, existence-only (it does not
  verify the numbers are true, same as every other field on this page).
  #2400 stopped new junk from arriving in `runs/spawn-attempts.jsonl` and
  proved it with real before/after counts for the one-time cleanup, but
  its Acceptance never asked the *ongoing* rotation policy to prove it
  could reach the pre-existing backlog — 419 of 434 records turned out
  permanently exempt (#2413), caught live 15 minutes after merge instead
  of at landing.
- VERIFY-AT-LANDING (issue #2137, operator decision 2026-08-24): a
  deliverable is code + EXECUTED acceptance evidence — every `- check:`
  in the issue is run at landing time and its command plus actual output
  recorded in the implementation record. Persistent test files are NOT a
  default part of a deliverable: do not draft acceptance criteria of the
  shape "a regression test covers X", and do not author new test files
  in a target repo unless the issue explicitly scopes a durable harness
  (a balance sim, a fixture driver, a lint) as a deliverable in its own
  right — a tool, not a regression test. Re-verification happens cut-7
  style: the recorded acceptance statements are re-executable against
  any later build; the record IS the regression suite, replayed on
  demand — not a growing tests/ directory replayed on every change.
  BOUNDARY: this plugin's OWN suite (`tests/`, `gates/test_*`,
  `on-the-record/hooks/test_*`) is exempt — it is the plugin's tooling;
  the decision governs deliverables shipped to TARGET repos.
- COMMAND-IDENTITY (issue #1696): a `check:` bullet with
  `provenance: executed-live` names a command SURFACE (the installed
  crontab/entrypoint line, or the README-documented invocation) — the
  recorded proof for it must show that EXACT command, byte-identical,
  environment-independent (no `PYTHONPATH=`/`cd`/venv-activation
  crutch masking a command that would not run as installed). A command
  that is merely equivalent-looking (e.g. `python3 -m pkg.cli` proving
  a check that names the installed `python3 -m pkg` line) is a
  fake-success vector, observed live: the digest file existed, the
  record looked honest, and only a builder-blind reviewer re-running the
  literal installed line exposed that every scheduled run would have
  failed silently. `gates/requirement_met.py`'s deterministic layer
  checks this mechanically — it flags a mismatch between a check's named
  command and the `acceptance: <command> — result: ...` command
  actually recorded in the diff, independent of any semantic verdict.
- ARTIFACT-SMOKE (issue #2073): when the deliverable includes a
  GENERATED or BROWSER-RUN artifact, declare it in the issue body under
  a `runtime-artifacts:` tag line (bare tag, then a bullet list or a
  fenced block of repo-relative paths, same shape as
  `design-artifacts:`), and make at least one `check:` PARSE or
  EXECUTE that artifact itself — its sources and a regeneration diff do
  not count. `node --input-type=module --check dist/bundle.js` counts,
  `python3 -m pytest tests/test_sync.py` over the generator does not,
  and neither does `cat dist/bundle.js`. This is the artifact analogue
  of COMMAND-IDENTITY above and it exists because the indirect form is a
  measured fake-success vector: two consumer deliverables shipped a
  completely dead page on one day with every check green
  (tm-dicequest#26 broke the `file://` launch on ES-module CORS, #44
  shipped a bundle whose un-stripped multi-line `import` statements
  threw a browser SyntaxError, and its sync test diffed the regeneration
  output without ever parsing it). `gates/artifact_smoke_rule.py`
  refuses a declared issue whose Acceptance names no declared path under
  the allowlisted verbs, `gates/check_runner.py` runs those commands as
  the `artifact-smoke` check type, and
  `docs/specs/artifact-smoke-contract.md` is the contract. Byte-inert
  when nothing is declared — a mechanical issue sees no new check.
- VISUAL-VERIFICATION (issue #2073): when the issue is DESIGN-BEARING
  and its declared design artifacts include a STORYBOARD, the phase-2
  record carries a `screen-verified:` line citing a live-screen
  screenshot under `docs/issue-<n>/_assets/` plus a one-line verdict
  against that storyboard. Parsing proves the page is not dead, it does
  not prove the page is the thing that was designed — tm-dicequest#58
  shipped flat geometric placeholder tokens while the GDD's core promise
  was character animation, and every check stayed green. The verdict is
  YOURS to write, never a gate's to compute: `pr-preflight.sh` checks
  only that the line exists and the cited screenshot exists. No pixel
  diff, no perceptual hash, no LLM verdict inside a gate — a pixel-diff
  baseline answers "did it change?", and a first-render placeholder has
  no prior baseline to regress against.
