# Current-state survey — issue #2073 (artifact-smoke acceptance)

Scope of this survey: repository `on-the-record`, commit
85a168400f1b2dd3a5b662ce8eb22925481bd9bc (branch
`issue-2073/implementation`). Every absence claim below is scoped to
that repository at that commit, per `docs/specs/survey-conventions.md`.

## What #2073 asks for

Two structural obligations, both to be inherited by every consumer
session through the co-injected directive and the acceptance format:

- (a) generated/browser deliverables: at least one `check:` must
  parse or execute the SHIPPED ARTIFACT, not only its sources;
- (b) design-bearing visual surfaces: a live-screen screenshot judged
  against the phase-1 storyboard before merge.

## Surfaces surveyed (the expected write set)

### 1. `on-the-record/hooks/directive.sh` — the co-injected directive

The operator-facing rulebook text lives here as a heredoc of `- `
bullets. Two existing bullets are the direct shape precedents:

- `ACCEPTANCE FORMAT` (directive.sh:341-347): tells the drafter to put
  `check:`/`empty state:`/`provenance:` each on its own line, and names
  `gates/acceptance_gate.py` as the post-hoc backstop.
- `COMMAND-IDENTITY (issue #1696)` (directive.sh:348-363): the closest
  analogue #2073 itself names — a rule that a check's named command
  must be the literal installed surface, with
  `gates/requirement_met.py` as its deterministic layer.

Finding: the directive already carries a "the check must name the real
thing, not a lookalike" rule for COMMANDS. As of the surveyed commit
there is no equivalent bullet for ARTIFACTS (nothing in directive.sh
mentions parsing/executing a generated bundle, a browser page, or a
screenshot).

### 2. `gates/acceptance_authoring_rule.py` (122 lines)

Judges the drafted issue body's `## Acceptance` section on exactly one
axis: whether full-suite/no-regression work is being pushed onto the
builder (`_FULL_SUITE_REF` vs `_BUILDER_EXEMPT`, lines 27-41). It is
body-text-only (`check_issue_body`) with a thin `gh issue view` wrapper
(`_issue_view_body`) — the shape a second, independent axis would reuse.
Absent at the surveyed commit: any notion of artifact kind (generated
file, browser page), and any requirement about what the checks execute.

### 3. `gates/check_runner.py` (175 lines)

`parse_checks()` classifies each `check:`/`gate:` line into exactly four
types: `test`, `grep`, `file-existence`, `judgment` (lines 39-70).
`run_checks()` refuses `judgment` loudly rather than skipping it.
Notably, `looks_like_command` admits `node` nowhere — its allowlist is
`python3|python|bash|sh|pytest` plus any first token containing `/` and
a `.`. Consequence at the surveyed commit: a check line such as
`` check: `node --check dist/bundle.js` `` classifies as
**file-existence**, not `test` — i.e. the exact artifact-smoke command
#2073 asks for would today be silently mis-run as a path-existence
test. This is a concrete pre-existing defect the requirement lands on.

### 4. `gates/design_bearing_classifier.py` (135 lines) + `gates/design_artifacts_gate.py` + `docs/specs/design-artifacts-contract.md`

The #2012/#2013/#2014 lineage is the structural precedent for
requirement (b):

- the classifier scores an issue body against a fixed design-signal
  vocabulary (`_DESIGN_SIGNAL_KEYWORDS`, overlap >= 3) and honours a
  closed-vocabulary `design-bearing-override: yes|no` escape;
- `design-artifacts:` declarations are parsed by
  `design_artifacts_gate.parse_declaration` and enforced **existence
  only, never content** (design-artifacts-contract.md, "What the gate
  checks") — explicitly: "judging whether a produced artifact is good
  (a real user scenario vs. a placeholder line) is explicitly out of
  this gate's scope";
- the gate fails **closed** when the issue body cannot be fetched.

Finding: requirement (b) is precisely the hole that contract leaves
open — tm-dicequest#58 shipped placeholder-quality visuals while every
declared artifact path existed. The storyboard artifact that (b) wants
the screenshot judged against is already a first-class citizen of that
contract (`storyboard` is both a `_DESIGN_SIGNAL_KEYWORDS` member and a
named member of the default artifact set).

### 5. `spawn.py` — co-injection at spawn time

- `spawn.py:8606-8617` already calls `design_bearing_classifier.check()`
  per issue and threads a `design_bearing_verdict` into `spawn_cmd()`
  (issue #2070, model routing), fail-open to `None`.
- `spawn.py:8500-8540` is the additive task-suffix region: skill
  mapping (#1955), skill check (#1960/#2062), skill-verdict (#2039).
- `spawn.py:8556+` (#2014) already pairs each declared
  `design-artifacts:` path with the best-matching mounted skill and
  appends one line per artifact, reusing `_tokenize` and the parsed
  declaration with **no new fetch** (body is already in hand at
  spawn.py:8085).

Finding: the spawn-time hook #2073 req 3 asks for ("browser-deliverable
issues get the smoke-check trigger line at spawn") has an existing,
proven insertion point and an existing body-in-hand fetch, so it costs
no extra API call. What is absent at the surveyed commit is any
artifact-KIND detection (generated bundle / browser page) — the
classifier answers "design-bearing?", not "browser-rendered?".

### 6. `docs/specs/acceptance-commands.md`

The per-target confirmed-command table that
`acceptance-command-real-run-guard.sh` re-runs. Every row today is a
`python3 -m pytest ...` or a `python3 gates/...` invocation; no row is
a node/browser artifact command. Relevant because an artifact-smoke
command that lands in an `acceptance:` citation would need a row here.

## Unknowns / thin spots the proposal must decide

1. **Detection**: how does the platform know a deliverable is
   generated/browser-rendered? Reuse the #2012 keyword-overlap scorer
   with a second vocabulary, an explicit closed-vocabulary tag, or the
   `design-artifacts:` declaration's file extensions?
2. **Enforcement altitude**: authoring-time refusal (drafting gate),
   check-runner execution class, PR-preflight refusal, or directive
   text only? The #2013 contract deliberately stopped at existence;
   #2073 explicitly asks to go further for one narrow class.
3. **Judgment boundary**: `check_runner` refuses `judgment` checks by
   design. A screenshot "judged against the storyboard" is a judgment
   check — it cannot live in the same runner without breaking that
   invariant.
4. **Coupling direction**: `gates/` is a leaf; `spawn.py` is the CLI
   above it. `design_bearing_classifier.py` copied `_tokenize` from
   spawn.py rather than importing it, precisely to avoid inverting that
   direction. Any new detector inherits that constraint.
5. **Scope of phase 1**: #2073 is an infrastructure issue with three
   numbered requirements plus a scope-addition comment; whether all
   land in one phase-2 change or a staged sequence is a proposal
   decision.

## Skip records

None — scouting was not skipped (see
`docs/issue-2073/reports/implementation/scout-brief.md`).
