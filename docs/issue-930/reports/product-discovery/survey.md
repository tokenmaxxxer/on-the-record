---
subject: issue-930
kind: survey
---

# Current-state survey — requirement digest / drift guard (issue #930)

## Background / context

canonical: docs/issue-930 (`gh issue view 930`, read this session) —
northpole req#6 ("condensed requirement management") has no dedicated
mechanism yet: requirements live scattered across individual issues;
nothing maintains a single condensed digest of what's currently live;
there is no standing drift guard checking in-flight work against that
set.

canonical: docs/specs/northpole.md, requirement 6 section (read this
session) — the repo's own traceability note for req#6 already points
at `docs/specs/requirements.md` (an append-only registry tied to an
executable check, `gates.requirement_registry`) as partial coverage,
and explicitly frames this document itself as the condensed home for
the 7 north-star requirements — but that note pre-dates #930 and does
not claim a maintained per-requirement digest or a drift guard exist.

canonical: derived: `wc -l docs/specs/requirements.md` (read this
session) — 27 lines, one entry (R001). The registry is real but has
not yet needed condensation at scale; #930's ask is the mechanism that
keeps it condensed AS it grows, not a fix for today's already-small
size.

canonical: gates/gates.py, `requirement_registry` (read this session,
around line 641) — checks only that each entry's `check` path still
exists at HEAD; it does not produce a digest, does not compare
requirements against active work, and does not read anything besides
`requirements.md` itself.

canonical: on-the-record/hooks/spec-index-preflight.sh and
gates/spec_index.py (read this session) — an existing, proven,
req#7-compliant pattern: a PreToolUse Bash hook recomputes a derived
artifact's expected content from the staged git diff and DENIES the
commit when a tracked source file changed but the derived index
wasn't regenerated alongside it. This is the auto-maintenance shape
#930's digest needs; nothing today applies this pattern to a
requirement digest.

canonical: docs/specs/enforcement-boundary.md, the `accumulation_trend()`
row (read this session) — an existing, proven, non-blocking advisory
report already runs every `roster_watchdog()` tick (inside
`spawn.py`'s `_board_wide_sweep()`), giving a board-wide, cross-session
view that compensates for authoring-time hooks' local-diff-only
visibility. This is the precedent for a watch-class, advisory drift
guard; nothing today compares active work against the live requirement
set specifically.

canonical: on-the-record/hooks/hooks.json (read this session) —
`directive.sh` fires on every `UserPromptSubmit`, in every installed
session, no explicit skill call required; this is the existing
zero-onboarding delivery channel a digest pointer would ride.

## Problem stated without any solution attached (JTBD tuple)

The issue text names its own preferred mechanism shape (an
auto-maintained digest plus a drift guard) before stating the job.
Restated in the operator's terms, stripped of that mechanism:

- **Job performer**: any session — orchestrator or role — working in a
  target repo with on-the-record installed, at any point after the
  repo has accumulated many issues, PRs, and reports.
- **Job**: figure out, without reading the repo's full history, what
  the user actually asked for that is still live, and choose the next
  unit of work so it demonstrably serves one of those still-live asks
  — not a plausible-sounding task that has quietly drifted from them.
- **Circumstance**: requirements arrive one issue at a time and never
  get consolidated; the repo's record volume (issues, PRs, reports)
  grows much faster than the requirement count itself, so the cost of
  reconstructing "what's the goal" from raw records grows with every
  session while the actual number of live requirements does not.
- **Desired outcome**: a session can learn the full live-requirement
  set from a single, small, current artifact — without reading issue
  history — and a standing (advisory) check exists that would notice,
  and say so, if in-flight work stopped tracing back to any of those
  requirements.

Gap note: the issue already specifies the shape (digest + drift guard,
hook/plugin-only, advisory). That shape is accepted as the direction
this proposal designs into (req#7's own constraints are given, not
negotiable), but the JTBD above is stated independently so the design
is checked against the actual job — "reconstruct the goal cheaply,
notice drift early" — rather than against the mechanism description
alone.

## Where this sits in the opportunity-solution tree (OST)

- **Outcome**: on-the-record actually holds to the goal the user
  stated, even as the repo's own record volume grows — the same
  standing outcome req#2 (zero-onboarding) and req#6 (condensed
  requirement management) both serve.
- **Opportunity**: `docs/specs/requirements.md` already gives an
  append-only, O(requirement-count) SOURCE of truth with a staleness
  check, and this repo already has two proven mechanism families
  (`spec_index.py`-style auto-regenerate-or-deny, and
  `accumulation_trend()`-style advisory board-wide reporting) that
  between them cover exactly the two capabilities #930 asks for — but
  neither has been pointed at a condensed requirement digest or a
  requirement-to-work drift check specifically. The opportunity is
  narrow: combine two already-proven patterns onto a new artifact,
  not invent a new enforcement class.
- **Candidate solutions** (evaluated in the proposal's RICE table):
  1. New derived digest file, auto-regenerated/denied on commit via
     the `spec_index.py` pattern, plus a drift check added to the
     existing `accumulation_trend()`-style advisory sweep.
  2. Fold digest content directly into `docs/specs/requirements.md`
     itself (no separate derived file) and skip a distinct drift
     check, relying on the registry's own staleness check.
  3. A digest computed by scanning the full `docs/issue-*/reports/`
     tree each time (richer content — could include per-issue
     status), rather than deriving only from the small
     `requirements.md` registry.
- **Discriminating assumption test**: does a digest derived ONLY from
  `requirements.md` (O(requirement count)) stay materially smaller
  than the record tree as records multiply, while still letting a
  fresh session pick goal-aligned work from it alone? Candidate 3
  trades this away for richer per-issue detail at O(record count)
  cost — the proposal must show candidate 1's leaner derivation still
  suffices for the acceptance harness's "fresh session picks aligned
  work" bar before rejecting candidate 3, and must state why folding
  into the raw registry (candidate 2) does not already meet the
  "condensed, single small artifact" bar on its own.
