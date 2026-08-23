---
name: artifact-smoke-contract
description: >
  The `runtime-artifacts:` issue-body declaration, the closed
  parse/execute verb allowlist an Acceptance check must use to touch a
  declared artifact, and the override/fail-closed postures — the
  contract `gates/artifact_smoke_rule.py` and `gates/check_runner.py`
  implement (issue #2073).
---

# Artifact-smoke acceptance contract

## Why this exists

Acceptance for a generated or browser-rendered deliverable was allowed
to be indirect: a unit test over the sources, or a diff-equality check
over regenerated output. Neither one ever parses or runs the bytes that
actually ship. Two consumer deliverables shipped a completely dead page
on one day with every check green — `tm-dicequest#26` (ES-module CORS
broke the `file://` launch) and `tm-dicequest#44` (the generated
single-file bundle still carried multi-line `import` statements, so the
browser threw a SyntaxError before the first frame). The sync test in
#44 diffed the regeneration output and never parsed it.

This contract closes that class the same way `COMMAND-IDENTITY`
(issue #1696) closed the command-surface class: the shipped thing itself
must appear, literally, under a verb that parses or executes it.

## The declaration

An issue whose deliverable includes generated or browser-run artifacts
declares them in its own body, using the same closed shape as
`design-artifacts:` (issue #2013): a bare tag line, followed by a bullet
list or a fenced block, one repo-relative path per line.

```
runtime-artifacts:
- dist/bundle.js
- dist/index.html
```

or

````
runtime-artifacts:
```
dist/bundle.js
```
````

The tag line itself carries nothing after the colon. `runtime-artifacts:
dist/bundle.js` on one line is **not** the contract shape and is refused
loudly rather than parsed as no declaration at all (the byte-inert
failure mode observed live on `design-artifacts:` in issue #2037).

## The rule

When `runtime-artifacts:` is declared, at least one `check:` or `gate:`
line in the issue's `## Acceptance` section must carry a backticked
command that

1. begins with a verb on the allowlist below, and
2. names one of the declared paths in its argv.

Otherwise the issue is refused at drafting time.

### Parse/execute verb allowlist (closed)

`node`, `npx`, `deno`, `bun`, `esbuild`, `tsc`, `swc`, `playwright`,
`puppeteer`, `chromium`, `chrome`, `google-chrome`, `firefox`,
`html5validator`, `xmllint`, `tidy`, `php`

The list is closed on purpose. If any command that merely mentions the
artifact counted, `cat dist/bundle.js` would clear the gate and the
fake-success vector would reopen. Widening the list is a change to this
file, not a judgment call at drafting time.

Canonical passing form:

```
check: `node --input-type=module --check dist/bundle.js` (provenance: executed-unit)
```

## Override

```
artifact-smoke-override: yes
```

anywhere in the issue body suppresses the refusal. It is an explicit,
auditable escape for the case where the artifact genuinely cannot be
parsed or executed in any available environment — not a default. The
absence of the line, or `artifact-smoke-override: no`, leaves the rule
in force.

## Postures

- **Byte-inert on absence.** No `runtime-artifacts:` tag means no check,
  no new refusal, and no new network call. A mechanical issue sees
  exactly today's behaviour.
- **Fail-closed on an unreadable body.** `check()` returns an actionable
  violation when the issue body cannot be fetched — a gate that opens on
  a broken `gh` is bypassable by breaking `gh`
  (`docs/decisions/2026-07-25-gate-unknown-tool-fails-closed.md`).
- **Advisory, never refusing, without a tag.** A body with no
  declaration but a strong generated/browser vocabulary gets one
  non-refusing hint line. The keyword scorer never refuses: the artifact
  vocabulary collides with mechanical issues far more often than the
  design vocabulary does (issue #2012's corpus calibration).

## Mechanical layer

`gates/check_runner.py` classifies and runs these commands:

- the interpreter allowlist for the `test` type includes `node`, `npx`,
  `deno`, and `bun`, so `` check: `node --check dist/bundle.js` `` is no
  longer misclassified as `file-existence` and silently never executed;
- a command that names a declared runtime artifact under an allowlisted
  verb is classified as the `artifact-smoke` check type and executed the
  same way a `test` check is, so the artifact-smoke result appears under
  its own type in the posted check-runner comment.

The runner still refuses `judgment` checks rather than mechanizing them.

## Spawn-time and directive surface

`on-the-record/hooks/directive.sh` carries the `ARTIFACT-SMOKE (issue
#2073)` and `VISUAL-VERIFICATION (issue #2073)` bullets, and `spawn.py`
appends, conditionally:

- one artifact-smoke trigger line naming the declared paths, when
  `runtime-artifacts:` is declared (or the advisory scorer fires);
- one live-screen verification line, when the issue is design-bearing
  and its declared design artifacts include a storyboard.

Neither line is appended when its condition is absent — the
unconditional spawn task stays byte-identical.

## Visual verification (the judgment half)

A design-bearing surface with a phase-1 storyboard needs a
`screen-verified:` line in its phase-2 record citing a live-screen
screenshot under `docs/issue-<n>/_assets/` plus a one-line verdict
against that storyboard. `on-the-record/hooks/pr-preflight.sh` checks
the line's presence and the screenshot's existence only. The verdict's
*content* is a human/session judgment and is never mechanized — no pixel
diff, no perceptual hash, no LLM verdict inside a gate. A pixel-diff
baseline answers "did it change?", while the failure this closes
(`tm-dicequest#58`, placeholder-quality first render) has no prior
baseline to regress against.
