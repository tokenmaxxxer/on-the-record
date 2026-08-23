<!-- on-the-record orchestrate directive, on-demand section file (issue #2102). Loaded via the always-on index injected by hooks/directive.sh. ${CHECKOUT} below means the on-the-record checkout path printed in that index. -->

- ACCEPTANCE FORMAT: when an `## Acceptance` criterion you draft
  references an executable artifact (a backtick `test/` or `gates/`
  path, or a `gate:`/`check:` line), write `check:`/`empty
  state:`/`provenance:` each on its own line — never inline in one
  sentence. `gates/acceptance_gate.py` enforces this post-hoc as a
  backstop; writing it right the first time skips the reject/rewrite
  round-trip.
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
