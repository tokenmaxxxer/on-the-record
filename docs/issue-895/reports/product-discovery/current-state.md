---
kind: current-state-survey
---

# Current-state survey — issue #895

## Background / context

code_under_review:
- docs/specs/northpole-harness.md
- harness/signals.py
- harness/driver.py
- harness/fixture-target/pyproject.toml
- harness/fixture-target/fixture_target/__init__.py
- harness/fixture-target/test_fixture_target.py
- harness/README.md
- docs/issue-776/reports/execution-observation.md

canonical: `docs/specs/northpole-harness.md` §1-§3 (read in full this
session) — the harness has exactly ONE fixture-target repo template and
ONE representative requirement, both frozen as a single scenario:
`harness/driver.py`'s module-level `REPRESENTATIVE_REQUIREMENT` is one
hardcoded string (`fixture_target`'s `--version` crash), and
`harness/fixture-target/` is one seeded defect in one file
(`fixture_target/__init__.py`'s argument-parsing helper).

canonical: `gh pr view 893 --json body` (executed this session — see
command output above, "Headline" section) — re-measure #7's transcript
scored all 8 rows of `harness.signals.evaluate_all` at the PASS verdict
for exactly this one scenario, and an independent fresh clone build+run
was also verified. That result is real but single-instance: it shows the
loop reached every signal's top verdict on the bug-fix shape one time; it
does not by itself show the same holds for a differently-shaped
requirement, since only one shape has ever been run through the harness.

canonical: `harness/signals.py` (read in full this session) — the 9
signal functions (`check_orchestration_to_completion` through
`check_build_and_run`, plus the #831-added
`check_remote_setup_not_silently_bypassed`) are pure functions over three
opaque dict shapes: `transcript`, `repo_state`, and a `(build_result,
run_result)` pair. None of the 9 functions branches on requirement TYPE,
fixture content, or scenario identity — each only inspects the shape of
whatever dict it is handed (e.g. `transcript.get("delegation_events")`,
`repo_state.get("requirement_records")`). The signal layer is therefore
already scenario-agnostic by construction: extending the matrix does not
require touching `signals.py`'s function bodies, only supplying new
`transcript`/`repo_state`/`build_result`/`run_result` dicts per scenario
— except for exactly one open question, named below (Infeasible-case
scoring gap).

canonical: `harness/driver.py` (read in full this session) —
`instantiate_fixture_target(dest_dir, seed_remote_dir=None)` copies
`FIXTURE_TEMPLATE_DIR` (hardcoded to the single `harness/fixture-target/`
directory) via `shutil.copytree`, then `git init`s and commits it. There
is no parameter or mechanism for selecting among multiple fixture
templates or multiple requirement texts — both are hardcoded module
constants (`FIXTURE_TEMPLATE_DIR`, `REPRESENTATIVE_REQUIREMENT`).
Extending to a matrix therefore requires the driver to accept a scenario
identifier and resolve template dir + requirement text + expected-outcome
kind from it; the copy/git-init mechanics themselves are already
scenario-agnostic (they operate on whatever `FIXTURE_TEMPLATE_DIR`
points to) and need no change.

canonical: `harness/driver.py` `seed_steady_state_github_host` /
`resolve_harness_github_host` / `reset_and_push_fixture_to_github` (read
in full this session, issue #847 origin) — the real-GitHub-host and
steady-state-reset machinery already operates on `dest_dir` generically
(any working copy, pushed to the one configured
`NORTHPOLE_HARNESS_GH_REPO`), so it is reusable across scenarios as-is;
only the fixture *content* pushed to that repo would differ per
scenario, not the push/reset mechanics. Resume machinery (issue #886,
`resume_orchestrator_session`, referenced in PR #893's body) is likewise
a property of the session/orchestrator layer, not the fixture, so it
composes with any new scenario without modification.

canonical: `docs/issue-807/reports/product-discovery/current-state.md`
(read in full this session) — a companion, still-open issue (#807)
already surveyed a distinct gap: none of the 9 signals checks the
CONTENT validity of a role's domain judgment, only wiring facts. #895's
requirement-type matrix is a different axis of coverage (diversity of
REQUIREMENT SHAPE the loop is exercised against) from #807's axis
(diversity/validity of ROLE JUDGMENT within a run) — the two are
complementary, not overlapping: a matrix entry could in principle reach
every signal's top verdict while still containing a #807-shaped hollow
judgment inside one of its delegated roles, since none of the 9 signals
this proposal builds on inspects judgment content. This survey does not
propose folding #807's rubric into #895's matrix; each stays scoped to
its own issue.

## Problem stated without any solution attached (JTBD tuple)

Job performer: the person (or downstream evaluator) who wants to trust
that "the on-the-record loop handles ANY requirement in ANY installed
session" (northpole req#1/#7) based on the #776/#893 harness result.

Job: know whether the autonomous loop's proven single-scenario result
generalizes past the one requirement shape it has actually been run
against, before trusting it on a requirement of a different shape
(feature work, a cross-module change, an underspecified ask, a
multi-role design decision, or a case that should be refused).

Circumstance: the harness's own design doc and driver code hardcode a
single fixture and a single requirement string (canonical: `harness/
driver.py` constants, cited above); the #893 result is real and
independently verified, but nothing in the current harness distinguishes
"proven for one requirement shape" from "proven for requirements in
general" — the gap between those two claims is invisible unless someone
reads the driver/spec closely enough to notice only one scenario exists.

Desired outcome: a small set of additional fixture+requirement scenarios,
each representative of a distinct requirement shape, each scored by the
SAME 9 existing signals (no new metric family, per #895's acceptance
bar), so that a future re-measure run can report a verdict per TYPE, not
just per the one bug-fix instance — turning "proven once" into "proven
across the shapes that matter most for northpole req#1/#3/#4/#5."

The issue text names a solution shape directly ("requirement-TYPE
MATRIX," six candidate types) — the JTBD above restates the underlying
need (know whether generality holds, not just declare a matrix) so the
proposal's type selection and prioritization are justified against
northpole coverage, not adopted as given.

## Where this sits in the opportunity-solution tree (OST vocabulary)

- **Outcome**: the #776/#893 harness result is trustworthy evidence for
  northpole req#1 ("any requirement") and req#7 (inviolable constraint
  holds under the as-installed precondition), not evidence scoped to one
  bug-fix instance.
- **Opportunity**: the harness's signal layer (`harness/signals.py`) is
  already scenario-agnostic (canonical: cited above — no function
  branches on scenario identity), so the missing piece is purely
  additional scenarios (fixture + requirement + expected-outcome kind)
  plus, for exactly one candidate type (infeasible/should-not-build), a
  scoring gap: none of the 9 existing signal functions has a top verdict
  that means "correctly declined to build," so that one type needs
  either a new signal or a documented mapping onto existing signals
  before it can be scored honestly (see proposal).
- **Candidate solutions** (this proposal picks and scopes the set; #895
  step 2 runs each scenario, step 3 fixes structurally and re-measures):
  1. Full six-type matrix as literally listed in #895's issue body
     (feature-add, multi-file, failing-test-driven, ambiguous, multi-role,
     infeasible) — maximal northpole coverage, maximal fixture-authoring
     cost (6 new fixture-target variants + driver plumbing).
  2. Four-type floor matching #895's own acceptance-check line (feature-
     add, multi-file, failing-test-driven, ambiguous) plus the
     already-run bug-fix, deferring multi-role and infeasible as
     explicitly named follow-on scope — matches the field's convergent
     minimum (scout brief: Epoch AI distribution + SWE-Bench Pro / SWE
     Atlas / SWE-Compass widening pattern), lower authoring cost, but
     leaves req#5 (pushback/refusal) and the #807 methodology-layer
     delegation-depth case unexercised.
  3. All six types, but sequenced by northpole-coverage priority
     (proposal's recommendation) — every type gets a defined fixture +
     acceptance + scoring mapping now (so nothing is silently deferred
     without being named), but step 2's actual run order follows the
     priority ranking, so a wall-clock or budget cut lands on the
     lowest-priority types first, never silently.
- **Discriminating assumption test**: whether the infeasible/
  should-not-build type's correct-refusal behavior can be scored by
  composing existing signals (a `check_condensed_requirement_management`-
  style read of the resulting repo state showing no build-affecting
  change, plus a `check_autonomous_completion_reporting`-style final
  report stating the refusal and its rationale) without a new signal
  function — pre-registered as this proposal's own open question for
  step 2, not resolved here (see proposal's Infeasible-case scoring
  section).
