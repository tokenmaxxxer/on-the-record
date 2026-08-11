---
subject: issue-776
role: product-discovery
kind: survey
---

# Current-state survey (issue #776)

## Background / context

`docs/specs/northpole.md` states 7 north-star requirements (issue #748).
`docs/issue-749/reports/conformance-review.md` produced a per-requirement
MET/PARTIAL/GAP verdict and a 17-row fix backlog — but by STATIC code
reading, not by driving a real session against a real target repo. Issue
#776 asks product-discovery to design (not build) the harness that would
make that verdict trustworthy: an execution-based judge, not a doc-read.

## Problem, stated without any solution attached (JTBD)

- **Job performer:** the on-the-record maintainer (issue author,
  `JiwonJung94`), acting as the person accountable for whether the 17-row
  backlog is real progress or busywork.
- **Job:** to know, after each backlog fix lands, whether a specific
  north-star requirement actually became true in a session that never saw
  the on-the-record repo's own internals — not whether the code that was
  supposed to serve it now exists.
- **Circumstance:** the only evidence available today
  (conformance-review.md) was produced by reading code and hooks and
  reasoning about what they should do; no session has ever been driven
  end-to-end against a fresh install to see what actually happens. The
  17-row list itself might be incomplete — gaps that only surface at
  execution time are invisible to static reading by construction.
- **Desired outcome:** a repeatable check that, run before any fix and
  again after each fix, tells the maintainer — per requirement, with
  evidence, not narration — whether that fix moved the needle, without the
  maintainer having to read code or trust a session's self-report.

The issue body names a solution shape already (a fixture repo + a driven
session + 7 signals) — that shape is carried into the proposal below, but
the problem above is the reason it's needed: static analysis cannot
distinguish "the mechanism exists" from "the mechanism fires when it
matters," and the maintainer currently has no other way to tell.

## Where this sits on the opportunity-solution tree

- **Outcome:** the 17-row backlog (and any future northpole fix) is
  trusted as real requirement movement, not code-existence movement.
- **Opportunity:** conformance-review.md's verdict was produced by a
  method (static reading) that structurally cannot detect the gap between
  "code exists" and "code fires end-to-end on a plain install" — and by
  its own admission, violates req #3 (real-wired verification) in
  producing itself.
- **Candidate solutions:** (a) this harness — one fixture repo, one
  representative requirement, 7 pre-registered per-requirement signals,
  re-run after each fix; (b) manually re-reading the code after each fix
  (rejected — same method that produced the unproven backlog, no new
  evidence); (c) trusting each fix's own PR self-report (rejected —
  req #3/#4 explicitly distrust self-report as evidence).
- **Discriminating assumption test:** does a session with on-the-record
  installed as a plugin-only dependency in a fresh, minimal, CI-less
  target repo — given one representative requirement and zero human
  input — actually orchestrate, delegate, resolve a mid-course problem via
  role composition, real-wire-verify, and produce a build-and-run artifact
  satisfying the requirement? This harness is exactly that test,
  operationalized per requirement.

## Order-constraint note

This current-state survey is written before the proposal, as contract
v3 s19 / the scout directive require. The proposal below (a) carries the
scout-brief's adopt/skip findings and (b) is written after this survey.

## Write-surface unknowns this survey identifies (aimed the scout sweep)

- Whether "execution-based, not narrated" verification (req #3's own
  standard) can be satisfied by the harness itself, or whether the harness
  risks reproducing conformance-review.md's own violation.
- Whether a single fixture + single representative requirement is
  sufficient signal density, or whether harness-config drift across reruns
  (different model/session settings) could be mistaken for a fix's effect.
Both are addressed in the scout brief (`scout-brief.md`, same directory)
and carried into the proposal's design choices.
