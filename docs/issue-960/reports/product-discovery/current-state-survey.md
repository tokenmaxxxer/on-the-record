# issue-960 current-state survey (product-discovery, phase 1)

kind: survey
subject: issue-960

## Scout skip record

Skip condition: spec-literal, no external design decision. This is an
internal engineering-process audit of this repo's own hook/gate
infrastructure — there is no external product category or exemplar
product to benchmark the coverage matrix against. Scouting is skipped;
proceeding on stated internal evidence only.

## Background / context

on-the-record enforces some role duties as standing hooks (`on-the-record/hooks/*.sh`,
wired in `on-the-record/hooks/hooks.json`) that run on every matching tool
call, and others only when a role session for that domain is explicitly
spawned. The operator's 2026-08-12 statement (quoted in issue #960) is
that domain expertise "must not be invocation-only" — QA/security/process
already have standing coverage; other domains (design, accessibility,
architecture, performance, and the rest of the 43-role taxonomy) do not.

## Problem, stated without a solution attached (JTBD tuple)

- **Job performer**: the operator running on-the-record across many
  concurrent role sessions, who cannot review every session's output.
- **Job**: get assurance that domain-specific invariants (a UX change has
  a rationale, a hot-path change has a measurement, an architecture
  change doesn't duplicate an existing mechanism) hold on every relevant
  change, not only on the sessions where that domain happened to be
  spawned.
- **Circumstance**: 43 role domains exist as specs
  (`roles/specs/*.spec.json`), but hook enforcement
  (`on-the-record/hooks/hooks.json`) only fires for a subset — currently
  concentrated in security/credential handling, record-claim/citation
  shape, and process/merge gating.
- **Desired outcome**: for each of the 43 domains, either a standing
  check exists (or is proposed) that catches the invariant without a
  human/agent remembering to spawn that role, or there is a written,
  specific reason the invariant cannot be a mechanical check and must
  stay spawn-only judgment.

The issue text (`## Ask`, `## Acceptance`) already names the target
artifact and acceptance shape; the JTBD above restates the same need in
outcome terms before any solution (gate design) is proposed.

## Opportunity-solution tree placement

- **Outcome**: on-the-record's per-domain invariants hold on every
  applicable change, independent of which roles were spawned for a
  given session (operator trust in unattended pipeline runs).
- **Opportunity**: standing enforcement currently clusters in
  security/QA/process; design, accessibility, architecture-composition,
  and performance-measurement domains have zero standing hooks — this
  is the gap the coverage matrix documents and the gap the prioritized
  landing plan targets first.
- **Candidate solutions**: (a) a full coverage-matrix doc classifying
  all 43 roles gate-now / directive-only / spawn-only (this issue's
  acceptance item 1-2); (b) landing the first enforceable domain-cluster
  gate (acceptance item 3, phase-2, requires approval — out of scope for
  this phase-1 PR).
- **Discriminating assumption test**: whether a gate-now invariant, once
  written as a hook, produces few enough false positives to stay
  default-on without operator override — untestable until a candidate
  gate actually ships; the proposal registers this as the pre-committed
  hypothesis for whichever cluster lands first (phase 2, future PR).

## Read evidence: what standing enforcement exists today

derived: `find on-the-record/hooks -maxdepth 1 -name "*.sh" | wc -l`
```
$ find on-the-record/hooks -maxdepth 1 -name "*.sh" | wc -l
43
```
(43 shell files under `on-the-record/hooks/`, includes both hooks and
one `directive.sh`; not 1:1 with the 43 role specs — hook count and role
count are independent quantities that happen to match.)

derived: `ls roles/specs/*.spec.json | wc -l`
```
$ ls roles/specs/*.spec.json | wc -l
43
```

code_under_review:
- on-the-record/hooks/hooks.json
- roles/specs/*.spec.json (all 43)
- on-the-record/hooks/credential-network-guard.sh
- on-the-record/hooks/credential-record-guard.sh
- on-the-record/hooks/test-authoring-invariant-guard.sh
- on-the-record/hooks/role-test-claim-guard.sh
- on-the-record/hooks/deviation-log-guard.sh
- on-the-record/hooks/acceptance-command-real-run-guard.sh
- on-the-record/hooks/accumulation-claim-guard.sh
- on-the-record/hooks/requirement-digest-preflight.sh
- on-the-record/hooks/product-capture-stopgate.sh
- on-the-record/hooks/pr-preflight.sh
- on-the-record/hooks/merge-allow-gate.sh
- on-the-record/hooks/spawn-allow-gate.sh
- on-the-record/hooks/gh-write-allow-gate.sh
- on-the-record/hooks/spec-index-preflight.sh
- on-the-record/hooks/role-axis-completeness-guard.sh
- on-the-record/hooks/record-claim-guard.sh

Reading `on-the-record/hooks/hooks.json` (`PreToolUse`/`PostToolUse`/`Stop`
entries), every registered hook matches on tool shape (`Bash`,
`Write|Edit|MultiEdit`, etc.), never on role/domain content.

canonical: on-the-record/hooks/claim-scan-preflight.sh, on-the-record/hooks/product-capture-stopgate.sh, on-the-record/hooks/delegated-judgment-gate.sh, on-the-record/hooks/directive.sh, on-the-record/hooks/role-spec-reference-guard.sh (read in full this session)

derived: `grep -l "accessibility\|interaction-design\|performance-engineering\|architecture" on-the-record/hooks/*.sh`
```
$ grep -l "accessibility\|interaction-design\|performance-engineering\|architecture" on-the-record/hooks/*.sh
on-the-record/hooks/claim-scan-preflight.sh
on-the-record/hooks/product-capture-stopgate.sh
on-the-record/hooks/delegated-judgment-gate.sh
on-the-record/hooks/directive.sh
on-the-record/hooks/role-spec-reference-guard.sh
```
Those five hits are role-name lists used for generic role-binding/dispatch
logic (e.g. enumerating all role names to validate a `Subject:` trailer or
role directory) — none of them encode an accessibility, design, or
performance rule specifically. This is consistent with the issue's own
claim: standing invariants exist for credential/network
(`credential-network-guard.sh`, `credential-record-guard.sh`), test-claim
integrity (`test-authoring-invariant-guard.sh`,
`role-test-claim-guard.sh`), record/deviation logging
(`deviation-log-guard.sh`), acceptance-command realness
(`acceptance-command-real-run-guard.sh`, `accumulation-claim-guard.sh`),
requirement capture (`requirement-digest-preflight.sh`,
`product-capture-stopgate.sh`), and merge/spawn/PR process
(`pr-preflight.sh`, `merge-allow-gate.sh`, `spawn-allow-gate.sh`,
`gh-write-allow-gate.sh`) — but nothing for design/UX rationale,
accessibility, architecture-duplication, or performance-measurement
content.

## Gap this proposal targets

The full 43-role classification and the prioritized landing plan are the
proposal's content: docs/issue-960/proposals/role-invariant-coverage.md.
This survey establishes only the current-state facts above; it does not
itself classify roles or recommend gates.
