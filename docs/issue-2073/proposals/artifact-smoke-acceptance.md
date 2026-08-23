---
status: proposed
files:
  - gates/artifact_smoke_rule.py
  - gates/test_artifact_smoke_rule.py
  - gates/check_runner.py
  - gates/test_check_runner.py
  - on-the-record/hooks/directive.sh
  - on-the-record/hooks/pr-preflight.sh
  - spawn.py
  - tests/test_spawn_directive_assembly.py
  - docs/specs/artifact-smoke-contract.md
  - docs/specs/reconciled-index.md
  - docs/issue-2073/reports/implementation.md
---

# Artifact-smoke acceptance + live-screen visual verification (issue #2073)

Upstream: issue #2073; survey
`docs/issue-2073/reports/implementation/survey.md`; scout brief
`docs/issue-2073/reports/implementation/scout-brief.md`; repository
`on-the-record` at 85a168400f1b2dd3a5b662ce8eb22925481bd9bc.

## Request

Acceptance for generated and browser-rendered deliverables is currently
allowed to be indirect — unit tests over sources, or diff-equality over
regenerated output — so a shipped artifact can be completely dead while
every check stays green (tm-dicequest#26, #44). The scope addition of
2026-08-23 adds a third recurrence class: design-bearing visual
surfaces shipped at placeholder quality with acceptance still green
(tm-dicequest#58). The ask is a structural fix in the acceptance
contract itself: (a) at least one check must parse or execute the
shipped artifact, and (b) design-bearing visual surfaces need a
live-screen screenshot judged against the phase-1 storyboard before
merge — both wired into the acceptance format and the co-injected
directive so every consumer session inherits them.

## Constraints

- **Byte-inert on absence.** An issue that declares no runtime artifact
  and is not design-bearing must produce a byte-identical spawn task
  and an untouched gate path, exactly as #2013/#2014 required of the
  design-artifacts surfaces.
- **Precision-first detection.** A false positive on a mechanical issue
  is far more expensive than a false negative here — the #2012 corpus
  calibration set that posture and this inherits it.
- **The judgment invariant holds.** `check_runner.run_checks` refuses
  `judgment` checks rather than mechanizing them; requirement (b) is a
  judgment and must not be smuggled into the runner.
- **No browser in the runner's environment.** `check_runner` executes
  on a PR-branch checkout with no build step and no browser binary; any
  design that requires a headless browser inside the runner is
  unrunnable here.
- **Dependency direction.** `gates/` is a leaf below `spawn.py`; the
  new detector must not import `spawn.py` (the #2012 classifier copied
  `_tokenize` for exactly this reason).
- **Operational-surface rule (contract §21)** and the
  `docs/specs/*` → `reconciled-index.md` regeneration rule both bind
  the phase-2 commits.

## Rationale

The chosen shape is: an explicit `runtime-artifacts:` declaration in
the issue body (syntax reused verbatim from the #2013
`design-artifacts:` contract), a new leaf module
`gates/artifact_smoke_rule.py` that refuses a drafted issue whose
`## Acceptance` section declares such artifacts without at least one
`check:` naming one of them under an execute/parse verb, a
`check_runner` classification fix so those commands actually run, and
two new directive bullets plus one spawn-time co-injected line.

Alternatives considered and rejected:

- **Headless-browser boot executed by `check_runner`** (the highest
  runtime-fidelity option on the scout brief's axis 1, and the option
  the issue's own sketch gestures at with "headless-DOM boot smoke").
  Rejected: the runner has no browser binary and no build step on the
  PR checkout (survey §3), so the check would be structurally
  unrunnable and would degrade into a skip — reproducing the very
  fake-success class #2073 exists to close. The declaration + literal
  artifact-naming rule keeps the fidelity requirement while leaving the
  boot command itself in the deliverable repo, where the build exists.
- **Pixel-diff baseline infrastructure (Percy/Chromatic class)** for
  requirement (b). Plausible — it is the field's dominant answer and
  holds the merge for a human verdict, which is exactly the shape
  wanted. Rejected because the baseline it compares against is the
  previous screenshot, answering "did it change?", while #2073 asks
  "does it match the phase-1 storyboard?" — a first-render placeholder
  has no prior baseline to regress against, so tm-dicequest#58 would
  have cleared a pixel-diff gate untouched.
- **Growing `gates/acceptance_authoring_rule.py` with the second
  axis.** Plausible — it already owns `## Acceptance`-section judgment
  and has the `gh issue view` wrapper. Rejected on cohesion grounds
  (complexity-coupling-management rule 3): the artifact axis shares no
  state or regex with the builder-attribution axis, and the two would
  be two modules in one file. The call site is widened instead of a new
  cross-module edge being added (same skill, rule 4).
- **Keyword-only detection with no explicit tag** (mirroring #2012's
  scorer alone). Rejected: #2012's own corpus work shows the scorer
  needs an overlap threshold of 3 to reach zero false positives on
  mechanical issues, and the artifact vocabulary ("page", "bundle",
  "build", "generated") collides with mechanical issues far more than
  the design vocabulary does. The scorer is kept, but only as a
  drafting-time advisory line, never as the refusal trigger.
- **Directive text only, no gate.** Rejected: the operator-flagged
  failures are precisely cases where a session read a directive and
  still shipped an indirect check; #2073 asks for a structural fix.

## What will be done

1. **`docs/specs/artifact-smoke-contract.md`** — the declaration
   contract: `runtime-artifacts:` syntax (bulleted list or fenced
   block, per #2013), the closed allowlist of parse/execute verbs that
   count as artifact-touching, the `artifact-smoke-override: yes|no`
   escape, and the fail-closed posture on unfetchable bodies. Index
   regenerated via `python3 gates/spec_index.py --update` in the same
   commit.
2. **`gates/artifact_smoke_rule.py`** (+ tests) — leaf module, no
   `spawn.py` import. `parse_declaration()` (reused shape),
   `check_issue_body(issue, body)` returning a list of refusal strings:
   refuse when `runtime-artifacts:` is declared and no `check:`/`gate:`
   line in `## Acceptance` names a declared path under an allowlisted
   verb. Advisory (non-refusing) line when the keyword scorer fires but
   no tag is present.
3. **`gates/check_runner.py`** (+ tests) — add `node`, `npx`, `deno` to
   `parse_checks`'s interpreter allowlist and introduce the
   `artifact-smoke` check type for a command whose argv names a
   declared runtime artifact. This closes the surveyed defect that
   `` check: `node --check dist/bundle.js` `` classifies today as
   `file-existence` and is therefore never executed.
4. **`on-the-record/hooks/directive.sh`** — two new bullets alongside
   `ACCEPTANCE FORMAT`/`COMMAND-IDENTITY`: `ARTIFACT-SMOKE (issue
   #2073)` (a generated/browser deliverable's acceptance must contain a
   check that parses or executes the shipped artifact itself, not its
   sources or a regeneration diff) and `VISUAL-VERIFICATION (issue
   #2073)` (a design-bearing visual surface's record must carry a
   `screen-verified:` line citing a live-screen screenshot under
   `docs/issue-<n>/_assets/` plus a one-line verdict against the named
   phase-1 storyboard).
5. **`on-the-record/hooks/pr-preflight.sh`** — existence-and-citation
   refusal for `screen-verified:` when the issue is design-bearing and
   its declared design artifacts include a storyboard. Existence of the
   screenshot and presence of the verdict line only; the verdict's
   content stays a human/session judgment, never mechanized.
6. **`spawn.py`** (+ `tests/test_spawn_directive_assembly.py`) — at the
   existing #2014 insertion point, using the body already in hand
   (spawn.py:8085, no new fetch): when `runtime-artifacts:` is declared
   or the advisory scorer fires, append one artifact-smoke trigger line
   naming the declared paths; when the issue is design-bearing with a
   storyboard artifact, append one live-screen verification line.
7. **`docs/issue-2073/reports/implementation.md`** — the phase-2
   record.

Staging within phase 2: (1)+(2) land first as a self-contained refusal
path, then (3), then (4)+(6) as one directive/spawn commit, then (5).
Each stage is independently revertible.

## Out of scope

- Executing a real browser or taking the screenshot automatically —
  the screenshot is produced by the deliverable's own session and
  cited, not captured by this platform.
- Judging screenshot quality mechanically (pixel diff, perceptual
  hashing, or an LLM verdict inside a gate).
- Retrofitting existing issues' acceptance sections.
- Any change inside consumer repositories (tm-dicequest and peers).
- Widening `check_runner` beyond classification + execution of
  already-authored commands.

## Accumulation

Two accumulation surfaces are touched, and both are held to a shared
helper rather than a growing inline list:

- **Issue-body declaration parsers.** `runtime-artifacts:` is the
  second closed-vocabulary declaration after `design-artifacts:`. If a
  third and fourth arrive with each writing its own parser, the same
  bullet/fence-parsing regex accumulates once per tag. Phase 2 therefore
  imports `design_artifacts_gate.parse_declaration` with a tag
  parameter rather than copying it — one parser, N tags. The `gh issue
  view` fetch is likewise not duplicated: `artifact_smoke_rule` is
  called from the existing acceptance-authoring call site with the body
  already in hand, so the number of `gh` calls per drafted issue does
  not grow with the number of authoring axes.
- **Spawn-time co-injected lines.** The task suffix already carries the
  #1955/#1960/#2039/#2062/#2014 blocks; #2073 adds up to two more
  conditional lines. At N more directives this suffix becomes the
  session's dominant prompt cost. Phase 2 keeps both new lines strictly
  conditional (nothing appended when the tags are absent) and appends
  them at the existing #2014 block rather than opening a new
  injection site, so the unconditional baseline stays byte-identical
  and the growth is bounded by declarations the issue author actually
  wrote.

## How you'll know it worked

- `check:` `python3 -m pytest gates/test_artifact_smoke_rule.py
  gates/test_check_runner.py -q` — new refusal cases and the
  `node`-classification fix are exercised.
- `check:` `python3 -m pytest tests/test_spawn_directive_assembly.py -q
  -o addopts=""` — byte-identical spawn task on an issue that declares
  no runtime artifact and is not design-bearing.
- `check:` a fixture issue body declaring `runtime-artifacts:` with an
  acceptance section whose only check is a source-level pytest run is
  refused by `python3 gates/artifact_smoke_rule.py`, and the same body
  with `` check: `node --check dist/bundle.js` `` added is admitted.
- `grep:` `ARTIFACT-SMOKE` and `VISUAL-VERIFICATION` present in
  `on-the-record/hooks/directive.sh`.
- Regression floor: `python3 -m pytest -q -m "not slow"` executed by
  the check-runner or an independent verification role, not by the
  builder.
