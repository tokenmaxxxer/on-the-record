---
status: proposed
files:
  - docs/issue-1131/reports/requirements-engineering.md
  - docs/specs/upstream-defect-channel.md
  - docs/specs/requirements.md
  - docs/specs/reconciled-index.md
  - roles/upstream-defect-report.json
  - on-the-record/commands/report-upstream.md
  - on-the-record/hooks/upstream-defect-scope-guard.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/test_upstream_defect_scope_guard.py
  - gates/test_upstream_finding_channel.py
  - docs/upstream-findings/.gitkeep
  - docs/upstream-findings/2026-08-13-watcher-registry-stale-pid.md
---

## Intent
Issue #1131 asks for a consumer→upstream defect-report channel: a
consumer session that notices a plugin bug can produce an upstream issue
draft (version sha + repro + context), check it isn't a duplicate, show
it to the user for confirmation, file it as an issue only (never a PR),
and fall back to a local docs/upstream-findings/ record when upstream is
unreachable. This proposal is the requirements-engineering deliverable
for that channel — a structured requirements doc, a traceability matrix
back to northpole req#2/#5/#7, and the first real case (the watcher
registry stale-pid observation from the issue body) filed through the
channel once built.

## Constraints (fixed by the operator, quoted from issue #1131)
- "Consumers file ISSUES ONLY — never PRs." Structurally enforced, not
  advisory.
- "hooks/command elements only" (req#7) — no CI, no background service.
- "Filing happens only with user confirmation in the consumer session —
  no silent auto-submission."
- Draft carries "plugin version (sha), reproduction evidence,
  observation context."
- "Duplicate check against open upstream issues before filing."
- Unreachable-upstream fallback: draft saved to
  docs/upstream-findings/ and reported.
- First real case: the watcher-registry stale-pid re-arm defect
  recorded in the issue body.

## What will be done
Phase 1 (this proposal, this session): produce the requirements
artifact set only — no channel code yet, per role-handoff contract v3
s19 (phase-2 code waits for Approve).

1. **docs/specs/upstream-defect-channel.md** — the spec: EARS-pattern
   requirements (ubiquitous/event-driven/state-driven per constraint),
   each with an ID, statement, verification method, and verification
   condition. Draws directly on the scout brief's adopted patterns
   (draft→preview→confirm linear flow; dedup-before-draft; auto-attached
   version/repro/context) and the survey's gap line (items 1, 3, 7 in
   docs/issue-1131/reports/requirements-engineering/current-state-survey.md).

2. **docs/issue-1131/reports/requirements-engineering.md** — the phase-2
   record (scaffolded now with loop_state: drafting; filled in on
   Approve per contract v3 s19) carrying: the structured requirements
   doc (ID + statement + ears_pattern + verification_method +
   verification condition per requirement), a traceability matrix (ID +
   description + source + downstream_link + status), and an ambiguity
   list — every reading resolved. The instructions say this file is
   phase-2 output; it is created here as a scaffold only, its body left
   for the phase-2 pass.

3. **roles/upstream-defect-report.json** — a new role element (not a
   command loop, per req#7: consumer-session invocation happens through
   a hooks/command element, and this role is the spec-carrying home for
   its record fields) describing what the channel decides, produces, and
   its write_scope (docs/upstream-findings/ only, plus the upstream
   repo's own issue tracker via `gh issue create` — never PR-shaped
   writes).

4. **on-the-record/commands/report-upstream.md** — the consumer-facing
   command element: assembles the draft (version sha + repro +
   observation context), runs the dedup check against upstream open
   issues, shows the user the exact draft before any network call
   (adopted from the scout brief's VS Code preview pattern), and only on
   explicit confirmation calls `gh issue create` against the upstream
   repo — or, on unreachable upstream, writes the draft to
   docs/upstream-findings/ and reports that fallback took place.

5. **on-the-record/hooks/upstream-defect-scope-guard.sh** (+ its test) —
   a structural PR-path prohibition: a PreToolUse (Bash) deny gate,
   scoped to the new channel's code path. Coverage must span every
   PR-creation surface, not the literal `gh pr create` shape alone — a
   post-proposal warrant hunt (see
   docs/issue-1131/reports/requirements-engineering/2026-08-13-hunt-upstream-defect-channel-requirements.md)
   found the single-shape design would leave `gh api -X POST
   repos/.../pulls`, GraphQL `createPullRequest`, `GH_REPO`-env-var-driven
   `gh pr create`, and non-gh tooling (hub, curl against the GitHub API)
   unguarded, contradicting "structurally enforced, not advisory." Phase
   2's guard implementation and test must therefore assert against this
   fuller surface set, not just the one literal command shape.
   Wired into hooks/hooks.json.

6. **gates/test_upstream_finding_channel.py** — the acceptance gate the
   issue names: exercises a fixture consumer repo, asserts a
   defect-observation statement produces a draft with version sha +
   repro section, asserts the unreachable-upstream fallback lands in
   docs/upstream-findings/, and asserts (call-shape/argument assertion,
   matching acceptance-command-real-run-guard.sh's own convention) that
   the channel never invokes `gh pr create` against the upstream repo.

7. **docs/upstream-findings/2026-08-13-watcher-registry-stale-pid.md** —
   the first real case named in the issue, filed through the new
   fallback path (or upstream issue, if reachable, in which case this
   file documents that outcome instead) once phase 2 builds the channel.

## Out of scope
- Building or wiring any of the above code — this is the phase-1
  proposal; phase 2 starts only after an Approve.
- A general-purpose telemetry/auto-upload path — requirement 3 forbids
  silent submission outright (scout brief "Skip" section).
- Rate-limiting / flood protection for repeat submissions — no
  motivating failure mode exists for a human-confirmed, per-event
  channel (scout brief "Skip" section).
- Any change to `gh-write-allow-gate.sh`'s existing five-verb allowlist —
  survey finding 2 confirms `gh pr create` is already absent from it;
  this proposal treats that as existing favorable infrastructure, not a
  file this work needs to touch.

## How you'll know it worked
- `docs/specs/upstream-defect-channel.md` exists with EARS-pattern
  requirements traceable 1:1 to issue #1131's five numbered requirements
  and its two acceptance-gate bullets.
- `docs/issue-1131/reports/requirements-engineering.md` scaffold exists
  with loop_state: drafting, ready for phase-2 fill-in on Approve.
- A reviewer approving this proposal (APPROVE issue-1131/requirements-engineering,
  per contract v3 s19, single-account mode) is approving exactly the
  seven-file write set above — nothing wider.

## Accumulation
This proposal adds one new file to the `roles/*.json` family
(`roles/upstream-defect-report.json`) and one new `gh issue create`
call site (inside `on-the-record/commands/report-upstream.md`). Neither
is an inline ad-hoc repetition: the role file follows the same shared
schema every other `roles/*.json` already uses (read `roles/
defect-verification.json` this session as the pattern — see
current-state-survey.md finding 8), and the single `gh issue create`
call is the channel's one call site, gated through the same
`gh-write-allow-gate.sh` shape-check convention the orchestrator's five
verbs already use (survey finding 2) — it does not hand-roll a new
subprocess wrapper. If N more upstream-facing channels are added later,
the accumulation shape to watch is `roles/*.json` growing one file per
channel (expected, matches the existing convention for every other
role) and any new `gh` verb call site needing its own shape-check entry
in `gh-write-allow-gate.sh` rather than a bespoke ad-hoc invocation —
the second part is the actual risk if it goes unwatched, since a
channel that skips the shared allow-gate shape-check would duplicate
command-shape validation logic inline instead of reusing it.

## What did not work
None.
