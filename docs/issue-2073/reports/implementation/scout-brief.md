# Scout brief — issue #2073 (artifact-smoke acceptance)

Mode: parallel tool calls (4 concurrent WebSearch angles in one turn).
Stages used: 1 sweep + judge point 1; stopped at judge point 2
(saturation — no further round would change a build decision).
Angles: generated-bundle smoke in CI; headless-browser blank-page
detection; visual regression vs. design mockup as a merge gate;
publish-time artifact linters (publint class).

## Category must-bes (what strong practice assumes)

- The thing tested is the SAME artifact that ships: "build the artifact
  once and test that artifact over the pipeline" — a check over sources
  or a re-generation diff is not the smoke test.
  (semaphore.io/community/tutorials/smoke-testing)
- The smoke check runs the artifact in an environment approximating its
  runtime ("the image actually starts" gate), post-build, pre-publish.
  (harness.io devops-academy; publint.dev docs — "run it after the
  package is built and before the registry publish step")
- Artifact-shape linters exist precisely because entry points that are
  declared can still fail to resolve — declaration-existence is a known
  insufficient check. (blog.logrocket.com/publint-package-validation/)
- Visual surfaces: the verdict is a HUMAN one over a rendered image, and
  the merge is HELD until that verdict lands — not an automated
  green/red signal. (browserstack.com/percy; augmentcode.com guide)
- Design drift is expected to be caught at PR level, not at a later
  design review. (augmentcode.com guide)

## Performance axes the field competes on

1. Fidelity to the real runtime (syntax-parse < module-load < headless
   boot < real browser with console-error capture).
2. Cost/latency of the gate (parse checks are ~free; headless boots are
   the expensive tail — hence "run the cheap artifact check always, the
   browser boot on browser-deliverable issues only").
3. Reviewability of the failure (a blank page must produce a named
   artifact — console error, screenshot — not just a red X).

## Adopt / skip

- ADOPT: the publint posture — a cheap, mechanical, artifact-shaped
  check placed at the publish boundary, whose whole value is that it
  reads the shipped file rather than the source. Maps onto
  `check_runner` gaining an artifact-smoke class.
- ADOPT: the "hold the merge for a human verdict on a rendered image"
  shape for design-bearing surfaces — explicitly NOT an automated
  pixel-diff verdict, which is also what this repo's existing invariant
  requires (`check_runner` refuses `judgment` checks rather than
  mechanizing them).
- SKIP: pixel-diff baseline infrastructure (Percy/Chromatic class). It
  needs a stored baseline per viewport, and #2073's judgment target is
  the phase-1 STORYBOARD, not a previous screenshot. Adopting baseline
  diffing would answer "did it change?" when the asked question is
  "does it match what was designed?".
- SKIP: an AI/LLM smoke-test generator (browserbash class) — the gap
  here is that no check touches the artifact at all, not that the checks
  are hard to author.

## Segment fit

Same segment: pre-merge/pre-publish mechanical gating of a shipped
artifact, plus a held human verdict on visual output. The exemplars are
CI pipelines and package-publish workflows; this repo's equivalent
boundary is `gh pr create` preflight + the check-runner's PR comment.

## GAP LINE

Already in place at 85a1684: mechanical PR-time gating
(`check_runner`, `pr-preflight.sh`), declaration-existence checking for
design artifacts (#2013), and a literal-command-identity rule for
commands (#1696). MISSING: (1) any check class that reads the shipped
artifact itself — `check_runner.parse_checks` does not even classify
`node ...` as a command (survey §3); (2) any runtime-fidelity
requirement in the acceptance format; (3) any held human verdict over a
rendered screen against the storyboard — the design-artifacts contract
stops at path existence by explicit design.

Sources:
- https://semaphore.io/community/tutorials/smoke-testing
- https://www.harness.io/harness-devops-academy/integrating-smoke-testing-into-your-ci-cd-pipeline-what-devops-needs-to-know
- https://publint.dev/docs/troubleshooting
- https://blog.logrocket.com/publint-package-validation/
- https://www.browserstack.com/percy/visual-regression-testing
- https://www.augmentcode.com/guides/visual-regression-testing-ai-generated-uis
