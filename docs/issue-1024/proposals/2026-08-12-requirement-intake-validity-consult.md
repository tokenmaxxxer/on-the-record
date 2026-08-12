---
status: proposed
files:
  - on-the-record/hooks/directive.sh
  - gates/requirement_intake_consult.py
  - gates/test_requirement_intake_consult.py
  - tests/test_spawn.py
  - docs/issue-1024/reports/implementation.md
---

## Request

The orchestrator memorizes and tracks stated requirements
(requirement-digest #930, drift watchdog, #1017 linkage) but does not
systematically analyze a new requirement's feasibility, its consistency
with the live digest, or its ordering relative to other live work —
that judgment happens ad hoc, in the orchestrator's own head, or not at
all. The user asks for a default step at requirement intake: consult
`requirements-engineering` (feasibility + testability) and, for
risk-bearing asks, `risk-management`, before an issue is drafted, and a
check that a drafted issue carries either the consult's trace reference
or an explicit skip reason. Trivial asks must have a first-class skip
path with no added latency.

## Constraints

- No turn-blocking latency for trivial/mechanical asks — the skip path
  is first-class, not an afterthought bolted onto the consult path.
- The skip reason must be a distinct, greppable tag string (mirrors
  `acceptance_gate.py`'s `unverifiable:` and #1017's proposed
  `infrastructure/no-direct-requirement` convention), not free prose.
- Must not duplicate requirement-digest (#930), the drift watchdog, or
  #1017's linkage check — this gate checks a different property (was a
  validity consult run/skipped) than #1017 (is a requirement ID cited)
  or #930/watchdog (is a live requirement still referenced anywhere
  open). All three can coexist on the same drafted-issue body.
- Default-on, no config flag to disable it, matching how
  `acceptance_gate.py` and #1017's proposed check both are default-on.

## Rationale

Considered folding the validity-consult trace requirement into
`gates/acceptance_gate.py` itself, since both fire on drafted-issue
bodies. Rejected: `acceptance_gate.py` checks one specific section
(`## Acceptance`) for one specific property (does it name an executable
artifact) and is wired to fire after phase-2 approval, the opposite
lifecycle point from intake — before any drafting decision is even
made. Piggybacking would either weaken `acceptance_gate.py`'s
phase-2-only trigger or force an intake-time concern onto a wiring
point that does not fire at intake time. A separate module
(`gates/requirement_intake_consult.py`) mirroring `acceptance_gate.py`'s
shape (pure `check_issue_body(issue, body)`, offline-testable) keeps
both checks independently wired at their own correct lifecycle point.

Considered making the consult step itself block issue drafting until
`requirements-engineering` (and, for risk-bearing asks,
`risk-management`) actually runs, rather than accepting an explicit
skip reason as an equally valid path. Rejected: the issue's own
constraint explicitly demands a first-class skip path for trivial asks
with no added latency — a hard block on every intake would violate that
constraint outright and would also duplicate the REQUIREMENT
ELICITATION block's existing acceptance-shape gate (issue #1006 req#4,
`on-the-record/hooks/directive.sh` lines 72-80), which already routes
vague asks through clarifying questions before drafting. The two-path
design (consult-trace-ref OR explicit skip reason) keeps the default
step real without re-litigating #1006's own precedent for when a detour
is warranted.

## What will be done

1. `on-the-record/hooks/directive.sh`: extend the REQUIREMENT
   ELICITATION block with a default validity-consult step — after the
   existing acceptance-shape check and before drafting, route the
   confirmed ask through the `requirements-engineering` skill/role
   (feasibility, testability, consistency with
   `docs/specs/requirement-digest.md`, ordering against other live
   work) and, when the ask is risk-bearing (touches auth, data
   deletion, external credentials, or is flagged risk-bearing by
   `requirements-engineering` itself), also through `risk-management`.
   The directive text instructs recording the consult's trace reference
   (or an explicit skip reason for a trivial/mechanical ask) into the
   drafted issue body before it is created.
2. `gates/requirement_intake_consult.py`: `check_issue_body(issue,
   body) -> list[str]` — pass-through when the body carries a
   validity-consult trace reference (a distinct greppable tag, e.g.
   `validity-consult: <ref>`) or the literal skip tag
   `validity-consult-skip: trivial` — a fixed, closed vocabulary (not
   an arbitrary named reason: the after-proposal hunt
   (docs/issue-1024/reports/implementation/2026-08-12-hunt-requirement-intake-validity-consult.md)
   found that accepting any named reason lets a self-evidently
   risk-bearing ask skip past on a fabricated excuse; closing the
   vocabulary to `trivial` only removes that specific bypass).
   Presence-only checking (does the tag exist, not whether the
   trace ref points to a real consult record) is an accepted, known
   limitation shared with `acceptance_gate.py`'s own `unverifiable:`
   tag — verifying trace authenticity is out of scope for this gate,
   same as `acceptance_gate.py` never verifies an `unverifiable:`
   reason's truth. `check(root, issue)` wraps it with a `gh issue
   view` fetch, mirroring `acceptance_gate.check`'s shape.
3. `gates/test_requirement_intake_consult.py`: unit tests for
   `check_issue_body` covering a body carrying a consult trace (passes),
   a body carrying the skip tag (passes), and a body with neither
   (flagged).
4. `tests/test_spawn.py`: add `intake`-named test cases per the issue's
   own Acceptance section — intake with the consult trace recorded
   passes; intake without consult and without skip reason is flagged.
5. `docs/issue-1024/reports/implementation.md`: phase-2 record, written
   at the start of phase 2 per the record-shape directive.

## Accumulation

`gates/requirement_intake_consult.check(root, issue)` adds one more `gh
issue view` call to the same family `acceptance_gate.check` and
#1017's proposed `requirement_linkage.check` already make at drafting
time — it does not add a per-tick loop and does not scale with
open-issue count. It fires once per drafted issue, independent of how
many issues exist. If drafting volume grows Nx, the added cost is Nx
one-shot `gh issue view` calls at draft time, each already bounded by
the same per-issue-view cost `acceptance_gate.check` pays today — no
new unbounded list/scan is introduced, and no per-role JSON file is
touched repeatedly by this change.

## Out of scope

- Changing `acceptance_gate.py`, `requirement_digest.py`, or
  `spawn.py::requirement_drift()` — this issue adds a new, independently
  wired check; it does not modify existing gates.
- Building or depending on #1017's proposed `gates/requirement_linkage.py`
  — that module does not exist yet; #1024's gate is self-contained and
  checks a different property.
- Any UI/prompt design for how `requirements-engineering`/
  `risk-management` are actually invoked as skills/roles — that is
  existing rulebook-skeleton machinery this issue routes to, not builds.
- Retroactive checking of already-drafted issues — the check applies to
  newly drafted issues only, matching #1017's own precedent for scoping
  structural checks to new drafts.

## How you'll know it worked

- `python3 gates/test_requirement_intake_consult.py` passes.
- `python3 -m pytest tests/test_spawn.py -k intake` passes, covering: an
  intake carrying the consult trace passes; an intake carrying neither
  trace nor skip reason is flagged.
- `gates/requirement_intake_consult.check_issue_body` returns `[]` for a
  drafted-issue body carrying either `validity-consult:` or
  `validity-consult-skip:`, and a violation otherwise.
