# Current-state survey — issue #476 round 2 (wiring gap)

## Background

Per the operator's registered iterative decision rule (round one's own
`docs/issue-476/proposals/discovery.md`, H1 decision rule): H1's primary
metric `fabrication_survival_rate` was measured post-rollout on
2026-08-10 (`docs/issue-476/reports/execution-observation.md`, dated
section) against qualifying records — measured value 100% (undefined by
the strict zero-denominator reading) — derived: that record's own corpus
table and "Metric measurement vs registered threshold" section, read this
session — against the registered threshold ≤10%. Root cause found that
session, read again this session, unchanged: `claim_scan.py` and
`reexecution_gate.py` are present and correct (fix commit `49a6154`,
`Closes #490`), but wired into zero triggers — no hook, no CI workflow
file, no `.reexecution/` history entry ever created. This is the decision
rule's "check exists but the trigger condition is a self-reported field a
session can omit" branch, "realized in a stronger form than anticipated"
per that record's own words: not omission, absence of a trigger at all.

## Opportunity-solution-tree placement (OST four-layer vocabulary)

- **Outcome** (unchanged from round one, `docs/issue-476/proposals/
  discovery.md`): reduce the rate at which fabricated verification/claim
  language survives into merged records undetected — i.e. make
  `fabrication_survival_rate` fall and stay at or under the registered
  threshold with the registered guardrail (`false_reject_rate`) also
  holding, same pair as round one.
- **Opportunity** (narrowed this round, was broader in round one): the
  mechanized check that would catch fabrication exists and is correct,
  but nothing on the deployed, zero-install hook surface ever invokes
  it — a distinct, narrower opportunity than round one's original "no
  mechanism exists" framing. Round one's opportunity is resolved (H1's
  checks were built, `docs/issue-476/reports/implementation.md`); this
  round's opportunity is one level down the tree: build exists, wiring
  does not.
- **Candidate solutions** (this round's scope, scored in the sibling
  proposal): (a) a PreToolUse `Bash` chokepoint on `gh pr create`/`gh pr
  edit`, mirroring `pr-preflight.sh`'s existing shape, calling
  `claim_scan.scan_text()` inline; (b) the same chokepoint additionally
  invoking `reexecution_gate.run_reexecution()` synchronously; (c) a
  separate async/deferred trigger — a `PostToolUse` hook on the `gh pr
  create` call that starts re-execution without blocking the triggering
  turn; (d) a Stop-event hook mirroring `role-test-claim-guard.sh`'s
  shape instead of a `Bash`-matcher PreToolUse hook.
- **Discriminating assumption test**: whichever candidate is chosen, the
  test that discriminates it from "another gate that can be satisfied by
  performance" is the same one round one already registered and this
  session's re-read execution-observation record already used —
  independent re-execution against a constructed fabricated-positive case
  that reaches the actual deployed hook (not a sandboxed direct function
  call) after the wiring ships. Round one's sandbox pilot called
  `claim_scan.scan_text()`/`run_reexecution()` directly, never through a
  hook — derived: that record's own "Script" line naming a scratch Python
  file, not a hook invocation, read this session; round two's
  discriminating test must go through `on-the-record/hooks/hooks.json`'s
  actual dispatch path, or it re-proves round one's already-settled "the
  logic is correct" finding instead of this round's actual open question
  (does anything call it).

## JTBD tuple (problem stated before any solution)

- **Job performer**: the plugin's own hook-and-gate layer (not a human,
  not the role session under audit) — the actor whose job is to produce a
  verdict on a claim before that claim reaches `main`.
- **Job**: when a role session is about to make an irreversible,
  operator-visible act that carries a fabrication-prone claim (opening or
  editing a PR whose body says "reproduced"/"verified"/"passed"), decide
  whether that claim has traceable, currently-correct evidence — without
  waiting for a human or a separate CI system to notice.
- **Circumstance**: the deployed consumer surface has no GitHub Actions
  and no server-side CI a plugin can assume exists (`docs/specs/
  enforcement-boundary.md`'s zero-install baseline, restated in
  `UNENFORCED-CLAUSES.md`'s own framing: "zero installation" reaches a
  session's own `gh pr merge`/`git push`/hook layer and nothing beyond
  it) — so the only reachable trigger surface is this plugin's own
  `PreToolUse`/`PostToolUse`/`Stop` hooks, firing inside the same session
  that produced the claim.
- **Desired outcome**: a fabricated claim never reaches a merged state
  without at least one independent, non-self-reported verdict having been
  attempted against it — not "the check would have caught it had it run,"
  which is exactly what round one's checks already are today.

If the issue text were read as naming a solution ("wire an automatic
trigger"), that is restated above as the JTBD's job clause, not adopted
as the chosen mechanism — which chokepoint and which fail posture remain
open, scored in the sibling proposal.

## What exists now (read this session, current commit)

- `gates/claim_scan.py` (commit `49a6154` fix): `scan_text()`,
  `_repo_targets(base=...)`, `_dotted_to_file()`. Correct per round one's
  post-fix sandbox re-run — derived: `docs/issue-476/reports/
  execution-observation.md`, "Findings 1-2 status: closed" section, read
  this session.
- `gates/reexecution_gate.py`: `run_reexecution()`, SHA-pinned worktree
  re-run. Correct per that same record's earlier fabricated-positive
  cases (all caught by re-execution, per its own raw-results table) —
  derived: same file, "Raw per-case results" section, read this session.
- `on-the-record/hooks/hooks.json`: full hook table read this session —
  no entry anywhere in `PreToolUse`, `PostToolUse`, or `Stop` names
  `claim_scan` or `reexecution_gate`.
- `UNENFORCED-CLAUSES.md`'s own gates table (read this session, unchanged
  since round one) still lists both as `contract, CI-supplement ... not
  yet a PreToolUse hook, CI-only where installed` — the deployed surface's
  own documentation already states the gap; this round's job is closing
  it, not discovering that it is stated.

## Initial-friction constraint carried into the sibling proposal

Per this round's assignment: most of the qualifying records in the
2026-08-10 measurement window would currently hard-fail `claim_scan`'s
evidence-marker check outright (no adjacent code fence or `Repro:`/
`Verify:` line) — derived: `docs/issue-476/reports/
execution-observation.md`'s corpus table, `evidence_marker_present`
column, read this session (thirty-four qualifying records scanned, only
two show the marker present). Wiring the check to actually fire, with no
transition period, would flip today's pass-through into a near-total
block rate on the existing record style. This is a discriminating-
assumption-test input, not a reason to soften the check: the sibling
proposal must register a rollout-friction hypothesis (warn-then-enforce
vs. immediate-enforce) alongside H1's re-registered wiring hypothesis,
rather than silently picking one.
