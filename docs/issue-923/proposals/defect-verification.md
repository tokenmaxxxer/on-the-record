---
status: proposed
files:
  - docs/issue-923/reports/defect-verification.md
---

# Proposal — issue #923 defect-verification, step 1

## Intent

Reproduce the block on an observation-role scoreboard record whose
evidence is its own executed-live measurement citation, per PR #895
(fixture PR #15 merged, requirement met, scoreboard record never
committed). Pin which gate refuses, why the observation's own citations
don't satisfy it, and whether the refusal is silent. No fix — that is
#923 step 2 (implementation), gated on this record.

## Constraints

- Cite `gh issue view 923` as canonical evidence for the #895 account; do
  not re-litigate #895's own measurement.
- Pin the exact gate/regex/check path in `gates/record_lint.py` and its
  wiring in `on-the-record/hooks/hooks.json`, not just restate the
  issue's already-known symptom.
- No fix, no test additions — those belong to step 2.

## What will be done

Write docs/issue-923/reports/defect-verification/current-state.md
(already committed alongside this proposal, phase-1 survey home)
pinning:

1. The gate that fires on a `docs/issue-*/reports/**` `Write` is
   `outcome_claim_citation_check` (issue #870,
   gates/record_lint.py:96-146), wired through
   on-the-record/hooks/record-claim-guard.sh into
   on-the-record/hooks/hooks.json:63-65 — not #919/#920, which gate the
   `Bash`/`git commit` surface.
2. Reproduced live: an observation record's natural prose `canonical:
   <transcript description>` citation on an OUTCOME-marked line (e.g.
   "requirement met: PASS") is refused with exit 2; a stand-alone
   backtick-quoted `derived: <path>` tag in the same 4-line window is
   accepted.
3. The gate's own refusal is not silent — `record-claim-guard.sh` prints
   the violated rule to stderr and blocks with exit 2, surfaced to the
   calling model the same turn; the "silent" half of #923's account
   (no PR, nothing said to the user) sits one layer above, in
   session/role-protocol behavior this survey cannot re-reproduce
   without the original #895 session's transcript.

Recommend, without implementing, the seam for step 2: extend
`_EXECUTED_LIVE_CANONICAL`/`has_derived`
(gates/record_lint.py:88-136) to accept a plain-prose `canonical:`
citation naming a transcript/measurement the current turn's role itself
produced (not only a shell-command-prefixed string or a stand-alone
backtick-quoted `derived:` line) as a third executed-live shape, while
keeping the existing two shapes for implementation done-claims — closing
the gap this survey's Finding 3 reproduces, without weakening #892/#918/
#919/#920's catch of a fabricated done-claim.

On phase-2 approval, docs/issue-923/reports/defect-verification.md (the
role's own contract-mandated record — findings, severity, `loop_state`)
is written per `verify:finding-record` / `verify:severity-classification`,
restating this survey's confirmed mechanism as a formal finding addressed
to `implementation`, with severity assigned by the deterministic band
lookup.

## Out of scope

- Any change to `gates/record_lint.py`, `record-claim-guard.sh`, or
  `hooks.json` (step 2, implementation role).
- Re-running the #895 execution-observation session or recovering its
  transcript.
- Designing the exact regex/shape extension for step 2's fix — this
  proposal names the seam, not its implementation.

## How you'll know it worked

docs/issue-923/reports/defect-verification/current-state.md pins the
exact gate (`outcome_claim_citation_check`, gates/record_lint.py:96-146,
wired at on-the-record/hooks/hooks.json:63-65), a live reproduction of
the refusal and of the one citation shape that already passes, and a
concrete finding on whether the refusal is silent — with file:line
citations and code-fenced command output for every claim — and names an
extension seam for step 2 without implementing it.

## Scout

Skip: investigative reproduction/pinning task with no product-facing
design decision open — the issue asks for the refusing gate to be pinned
and its refusal mechanism reproduced, not for a design direction to be
chosen among external products; there is no external field to scout.

## What did not work

Two intermediate drafts of the current-state survey itself tripped the
very gates under investigation (`canonical_source_claim_check` matching
"closed" inside "fail-closed" in the survey's own title;
`outcome_claim_citation_check` matching "PASS" inside a prose sentence
quoting the check's own regex; `bare_count_claim_check` matching "2
work" inside "step-2 work"; `orphaned_path_reference_check` matching a
backtick-quoted illustrative path that does not exist in this tree).
Each was rephrased to avoid the trigger token or given the required
citation/fence; no gate behavior was bypassed to land the survey.
