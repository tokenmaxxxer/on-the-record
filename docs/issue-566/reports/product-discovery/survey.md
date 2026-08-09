# Survey — issue #566: durable requirements/priorities/philosophy/goals record

## Background / context

`on-the-record/hooks/directive.sh` (UserPromptSubmit) already injects the orchestration
directive into every prompt of the orchestrating session — the session that talks to the user in
the target/consumer repo, upstream of any issue being filed. That directive currently tells the
orchestrator "requirements become ISSUES you draft and the user confirms" — i.e. today the *only*
durable home for a user-stated requirement is a GitHub issue, and only once one gets drafted. A
requirement, priority, philosophy statement, or goal mentioned in conversation that never becomes
an issue text today leaves no trace anywhere in the target repo's `docs/`.

The deployed hook surface (confirmed by directory listing, not assumed) is
`on-the-record/hooks/*.sh`, wired through `on-the-record/hooks/hooks.json` on
`SessionStart` / `UserPromptSubmit` / `PreToolUse` (`Write|Edit|MultiEdit|Bash`) / `PostToolUse` /
`Stop`. This repo already runs several `PreToolUse`-on-`Write|Edit|MultiEdit` guards that block a
write rather than merely check it after the fact (`record-claim-guard.sh`,
`role-spec-reference-guard.sh`, `call-shape-guard.sh`, `accumulation-claim-guard.sh`), and a
`Stop`-time guard (`stop-gate.sh`, `report-framing-check.sh`) that fires at end-of-turn/session.
No GitHub Actions workflow performs any of this — confirmed by `find . -iname '*hook*'` returning
only `on-the-record/hooks/` and `.claude/hooks` (local, not CI), consistent with the issue's
2026-08-08 operator policy that enforcement lives in deployed hooks, not Actions.

## Problem, stated without the proposed solution (JTBD)

The issue already states the problem largely solution-free, but names two sub-mechanisms
("hook-enforced", "structured capture") as constraints rather than as the solution itself.
Restated as a JTBD tuple:

- **Job performer**: the orchestrating session, at every turn of a conversation with the user in
  a target/consumer repo — before any issue exists, before any code is touched.
- **Job**: preserve what the user actually said about what the project should do (requirements),
  what matters most and in what order (priorities), why (philosophy), and what it's for
  (goals) — as something the target repo's own `docs/` can be read back later, distinct from and
  prior to any of it being discharged into an issue or a code change.
- **Circumstance**: the orchestrating session is conversational and stateless across sessions
  (each session ends, memory does not durably persist to the target repo unless something writes
  it there); the *only* existing hook-enforced capture point today acts on tool calls
  (`PreToolUse`/`Stop` on `Write|Edit|MultiEdit|Bash`), not on the conversational turns
  themselves, so a requirement stated in prose with no accompanying tool call currently triggers
  no hook at all.
- **Desired outcome**: a target repo accumulates a structured, evolving corpus of
  requirements/priorities/philosophy/goals in `docs/`, and a session that lets a requirement-
  bearing statement pass unrecorded is made visible or refused by the hook surface itself — not
  by a model's self-report that it "will remember."

## Where this sits on the opportunity-solution tree

- **Outcome**: a target/consumer repo's `docs/` durably reflects what its user has actually told
  the orchestrating session it wants, independent of whether any of it became an issue yet.
- **Opportunity**: today the orchestrating-session-to-target-repo conversation has exactly one
  discharge path (issue drafting) and zero capture path for everything upstream of that — the
  entire class of "requirement stated, never filed as an issue, never written anywhere" is one
  opportunity, symmetric to how #476 named "self-report is the only evidence a gate accepts" as
  one opportunity for the discharge side.
- **Candidate solutions**: scored below — record-shape/layout choice (single ledger vs. four
  files vs. per-statement dated entries), the detection mechanism (prompt-pattern match on the
  live turn vs. end-of-session diff-against-transcript vs. a running session-scoped requirement
  ledger the hook cross-checks at `Stop`), and the granularity of the write trigger
  (`UserPromptSubmit` immediately vs. batched at `Stop`).
- **Discriminating assumption test**: whether a `Stop`-time hook can reliably classify "this
  turn's conversation contained a requirement/priority/philosophy/goal statement" from the
  transcript alone, cheaply enough and with a low enough false-negative rate, to be a real gate
  rather than decorative — this is the open question the pre-registered hypothesis below targets.

## What the repo actually does today (checked, not assumed)

- `directive.sh` (UserPromptSubmit, fires every prompt) tells the orchestrator to draft issues
  from requirements but does not itself write anything to the target repo's `docs/`, and contains
  no detection logic for "a requirement was stated but not recorded" — confirmed by reading the
  full 126-line file; its job is steering text injection, not enforcement.
  Precedent it already sets that answers *one* of the issue's open questions: freshness matters —
  the file's own comment states re-injection every prompt exists "because a session-start-only
  injection drifts out of a long context," which is the identical rationale for why a
  requirements-capture check cannot live in `SessionStart` alone either.
- No hook in `on-the-record/hooks/` inspects prior conversational turns/transcript content; every
  existing `PreToolUse`/`Stop` hook inspects the *tool call about to happen* or the *session's
  produced artifacts* (`record-claim-guard.sh` checks a record's claim structure at write time,
  `report-framing-check.sh` checks framing at `Stop`) — none currently has access to, or acts on,
  the running conversation transcript itself. This is the concrete gap the issue's "how can a hook
  detect an unrecorded requirement" question is asking about.
- `docs/decisions/` and per-issue `docs/issue-<n>/decisions/` already establish the pattern of
  dated, per-topic structured files (e.g. `docs/issue-476/decisions/2026-08-08-h1-h2-mechanism-adr.md`)
  as this repo's own precedent for "accumulating corpus," rather than one continuously-rewritten
  document — directly answers part of the issue's "docs layout" open question by analogy, though
  #566's target is the *target/consumer* repo's docs, not this repo's own.
- #476's discovery (this issue's sibling, same role) already established: (a) gates here check
  field presence, not truth — the same risk applies to a requirements record (a session could
  write a boilerplate "user wants X" that satisfies a shape check without being what was actually
  said); (b) this repo's habit of naming closed vocabularies for record-shape state instead of
  free text, reusable for a requirements/priorities/philosophy/goals taxonomy.
- #310 (cited by #566) is confirmed (via directory listing) to have shipped
  `docs/issue-310/proposals/2026-08-07-discharge-gate.md` — a gate for *discharging* a requirement
  into an issue. #566 is explicitly upstream of that: the discharge gate assumes a requirement
  already exists in some form before it fires; #566's job is capturing the requirement before
  discharge is even attempted, confirmed distinct scope per the issue's own "Scope notes."

## Scout-informed gap (see scout-brief.md)

Current state already meets: structured, dated, per-topic record layout precedent
(`docs/decisions/`), and a deployed hook surface that already blocks non-conforming writes
pre-emptively rather than only checking after the fact. Missing: (1) no record type distinguishing
requirements/priorities/philosophy/goals exists for target/consumer repos; (2) no hook inspects
conversational content for a requirement-shaped statement — every existing hook is tool-call- or
artifact-scoped, not transcript-scoped; (3) no bootstrap behavior defined for a target repo with
no `docs/` tree yet. These three gaps are the discriminating axis carried into the proposal.
