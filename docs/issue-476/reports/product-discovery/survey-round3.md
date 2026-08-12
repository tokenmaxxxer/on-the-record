# Current-state survey — issue #476 round 3 (post-enforcement gap sweep)

## Background

canonical: docs/issue-476/proposals/discovery-round2.md, read this
session — Round 2 found H1's check correct but never triggered, and
registered `wiring_coverage_rate`/H1b to wire it into a preflight hook.

canonical: on-the-record/hooks/hooks.json, read this session — the
wiring landed: `derived: grep -n claim-scan-preflight.sh on-the-record/hooks/hooks.json`

```
$ grep -n claim-scan-preflight.sh on-the-record/hooks/hooks.json
42:          { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/claim-scan-preflight.sh" },
```

canonical: docs/specs/enforcement-boundary.md, read this session — still
warn-only, pending its own two-week flip-to-deny window per that row's
own text.

No round-2 execution-observation measurement record exists yet.
derived: git log --oneline --all -- docs/issue-476/reports/execution-observation

```
$ git log --oneline --all -- docs/issue-476/reports/execution-observation
58824ce docs(issue-476): execution-observation phase-1 survey + proposal for step 4
```

Only the round-1 phase-1 entry appears — the round-2 wiring measurement
window is still open. That thread stays with execution-observation, not
this round's scope.

This session's assignment is to read the guards landed since round 2
under other issues and ask, against issue #476's own candidate
directions, which theater vectors those guards leave uncovered.

## What the landed guards actually check

derived: grep -c '^| `' docs/specs/enforcement-boundary.md

```
$ grep -c '^| `' docs/specs/enforcement-boundary.md
77
```

Seventy-seven mechanism rows exist. canonical:
docs/specs/enforcement-boundary.md, read this session — the rows
germane to this issue share one shape: each verifies that a claim
already written into a record or commit is textually backed by a
citation, and — the newest generation — that the cited command or test
actually re-runs and its result matches what was claimed.

- The record-lint checks require a state, outcome, or defect claim in
  prose to carry a citation pointing at something read or run — checked
  at write time, by pattern-matching the prose around the claim.
  canonical: gates/record_lint.py, read this session.
- The read-before-claim check requires a defect or root-cause claim
  specifically to carry either a >=3-line verbatim-matched quote or a
  `derived:` command — closing "claimed a bug without reading the
  file." canonical: gates/record_lint.py line near `_DEFECT_CLAIM_MARKER`,
  read this session.
- The live-fire and acceptance-real-run hooks, at `git commit` time,
  take a citation naming a command or test and actually execute it
  again, right now, denying the commit if the real result contradicts
  the claim — closing "the citation names a command that was never
  actually run this turn." canonical: docs/specs/enforcement-boundary.md,
  read this session.

All of this is downstream of a claim already existing: the guard fires
on the record's prose, after the role has already decided what to write
and how to spawn. Every one of these mechanisms answers "is this
specific claim traceable and re-runnable," never "did this role need to
be spawned to answer a real question," "was the answer decided before
the role ran," or "would an honest null result have been reported."

## Issue #476's candidate directions, checked against the landed set

The issue text names several non-exhaustive candidate directions. Each
is checked below with its own search, run this session.

**Independent re-execution as the only accepted evidence.** Built: H1/H1b
plus the live-fire/acceptance-real-run triad generalize this to nearly
every citation shape a record can carry.

**Information asymmetry — a verifier that sees only the artifact, never
the builder's intent.**
derived: grep -rl "verifier.*only.*artifact\|blind.*verif" gates/ docs/specs/ docs/handbooks/

```
$ grep -rl "verifier.*only.*artifact\|blind.*verif" gates/ docs/specs/ docs/handbooks/
```

No output. Every landed guard reads the same record the builder wrote;
none constructs a separate verifier session denied the builder's stated
intent. The `adversarial-review` skill exists but is session-invocable,
not a mechanized gate — optional, not structural.

**Pre-registration — the orchestrator states the question, not the
answer, before spawning.**
derived: grep -rl "task.string.*solution\|question.*before.*spawn" docs/specs/*.md docs/handbooks/*.md gates/

```
$ grep -rl "task.string.*solution\|question.*before.*spawn" docs/specs/*.md docs/handbooks/*.md gates/
```

No output. The issue's own second observed instance — an orchestrator
task string containing the solution, reducing the role to transcription
— has no mechanized check anywhere in the landed set.

**Refusal as a first-class success outcome.**
derived: grep -rl "refusal.*first.class\|nothing.to.do.*equal.cost" gates/ docs/specs/ docs/handbooks/ roles/

```
$ grep -rl "refusal.*first.class\|nothing.to.do.*equal.cost" gates/ docs/specs/ docs/handbooks/ roles/
```

No output. H2's refusal vocabulary gives a role a string to write when
it cannot verify something, but nothing checks that a refusal record is
scored or costed the same as a deliverable record.

**Spawn-necessity checks — why this role needs to run, falsifiable.**
derived: grep -rl "spawn.necessity\|falsifiable.*spawn" gates/ docs/specs/ docs/handbooks/

```
$ grep -rl "spawn.necessity\|falsifiable.*spawn" gates/ docs/specs/ docs/handbooks/
```

No output.

**Sampling audits — random independent re-verification of a fraction of
records.**
derived: grep -rl "sampling.audit\|random.*re.verif" gates/ docs/specs/ docs/handbooks/

```
$ grep -rl "sampling.audit\|random.*re.verif" gates/ docs/specs/ docs/handbooks/
```

No output. Every landed guard is deterministic and citation-triggered —
it fires only when a record already carries a qualifying claim shape.
None samples records that carry no claim at all.

**Diversity checks against answer-copying — the deliverable must contain
something not derivable from the task string.**
derived: grep -rl "diversity.check\|answer.copying" gates/ docs/specs/ docs/handbooks/

```
$ grep -rl "diversity.check\|answer.copying" gates/ docs/specs/ docs/handbooks/
```

No output.

Summing the seven searches above: one candidate direction is built
(re-execution); the other six return zero matches across gates/,
docs/specs/, docs/handbooks/, and roles/.

## Opportunity-solution-tree placement (OST four-layer vocabulary)

- **Outcome** (unchanged across all three rounds, canonical:
  docs/issue-476/proposals/discovery.md, read this session): reduce the
  rate at which role-play-without-expertise — predetermined answers,
  gate-satisfying theater, fabricated verification — survives into a
  landed, operator-trusted state undetected.
- **Opportunity** (narrowed again this round, canonical:
  docs/specs/enforcement-boundary.md, read this session): rounds 1-2
  together with the independently-landed record-lint/live-fire work now
  cover the downstream opportunity — a claim, once written, is
  traceable and re-runnable. What remains open is the upstream
  opportunity: nothing checks whether the role was spawned out of
  genuine need, given a real question rather than a decided answer, or
  allowed to refuse at equal cost to delivering. This is a distinct
  branch from rounds 1-2's "does the check exist"/"does the check fire"
  — it is "does the incentive structure make performing the check
  cheaper than doing the work," the issue's own framing verbatim.
- **Candidate solutions** (this round's scope, scored in the sibling
  proposal): (a) a spawn-time task-string check that refuses a task
  string embedding an imperative solution clause without an accompanying
  open question; (b) a refusal-cost-parity mechanism making a
  registered refusal/null-result `loop_state` explicitly exempt from any
  "deliverable produced" scoring path; (c) a sampling audit — an
  orchestrator-loop-reachable periodic re-spawn of an independent
  verifier session against a random fraction of the already-landed
  record set, blind to the builder's own record, scoring divergence;
  (d) a diversity/non-transcription check comparing a delivered record's
  substantive content against its own spawning task string, flagging
  near-identical restatement as advisory, non-blocking.
- **Discriminating assumption test**: the test that discriminates a
  candidate here from more citation-shape theater is whether it can be
  satisfied by a role that changes only its own record's prose or
  citations — the landed 77-row set is entirely first-person-satisfiable
  this way, since a role controls its own citations. A structurally
  resistant mechanism here must involve either a second, blind actor
  (candidate c) or a comparison whose second term the role does not
  control (candidates a/d compare against the orchestrator's own task
  string, not the role's prose; candidate b changes scoring outside the
  role's own record).

## JTBD tuple (problem stated before any solution)

- **Job performer**: the orchestrator/spawn layer — the actor deciding
  whether and how a role gets spawned — not the spawned role session
  itself.
- **Job**: when about to hand a task to a role session, be able to tell
  mechanically, not by trusting the role's own eventual record, whether
  that spawn was necessary, was framed without a predetermined answer,
  and whether an honest "nothing to verify" outcome will cost the role
  nothing relative to fabricating a deliverable.
- **Circumstance**: the downstream half of this problem — is a written
  claim traceable and re-runnable — is now well covered (seventy-seven
  rows, canonical: docs/specs/enforcement-boundary.md, read this
  session); the upstream half has zero mechanized coverage, per the six
  zero-match searches, each `derived:`-tagged in the section above.
- **Desired outcome**: a spawn decision and a role's refusal/deliverable
  choice are each subject to at least one structural check a role cannot
  satisfy purely by controlling its own record's prose.

## Sources

This round is a repo-internal enforcement-coverage audit, not an
external product comparison; per the scout-directive, the scout brief
(sibling file, `scout-brief-round3.md`) draws on established audit-
design and metric-gaming literature located this session via web
search — see that file's own Sources list.
