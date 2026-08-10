---
status: proposed
files:
  - docs/issue-628/reports/execution-observation.md
---

## Request

Independently drive, on fixture repos built outside this repository's
tree, the shipped entrypoints named in issue #628 across today's merged
PRs — prioritizing the surfaces the issue flags as never exercised
outside their own tests (#573 delegated-judgment-gate, core#189
rejection lifecycle, #566 product-capture, #586 `--roles-dir` wiring) —
then render, per surface, the three-level verdict (outcome / trajectory
/ step) against that fixture evidence in
`docs/issue-628/reports/execution-observation.md`.

## Constraints

- Verdict claims require citation adjacent to the claim (commit SHA,
  file:line, PR URL, or this session's own fenced fixture-drive output)
  — no bare assertion.
- Independence: never edit any observed surface's `src/`, `test/`, or
  another issue's `docs/issue-<n>/` path outside this role's own report
  and proposal paths.
- Per the survey's tension note: invoking an already-shipped hook/CLI
  entrypoint against a fixture built this session, to observe present
  runtime behavior, is the acceptance criterion issue #628 itself names
  (`provenance: executed-live`) and is distinct from re-executing the
  implementation work — no hook/gate/CLI source file gets rewritten or
  redesigned by this observation.
- Absence of a finding must be evidenced (fixture built, entrypoint
  invoked, what fired) — never asserted as "looks fine."
- No fixes: findings are recorded with file:line, repro, signature
  class (a)-(h), and severity; they route to remediation, not to an
  edit in this branch.

## What will be done

1. Build one scratch fixture repo per surface family under `$TMPDIR`
   (outside this repo), matching each entrypoint's documented payload
   contract.
2. Drive each prioritized surface first: `delegated-judgment-gate.sh`
   (#573, PRs #583/#585) with a constructed two-axis payload; core#189's
   REJECT-token path (PRs #191/#194) through whatever consumer-repo call
   site the diff shows; `product-capture-stopgate.sh` (#566, PR #575)
   via a constructed Stop-hook transcript payload; the `--roles-dir`
   entrypoint (#586, PR #594) via its CLI invocation.
3. Then drive the remaining named surfaces: `claim-scan-preflight.sh`
   (#476, PR #580); the `#587` remediation-spawn/reconcile chain (PRs
   #595/#603/#606/#621), specifically re-checking the ROOT-vs-target
   fix in #621 and whether the sibling-sweep audit exists; the #577
   contract-guard time-scoping fix (PR #591) against a freshly evaluated
   (non-cached) predicate; the #597 framing sixth condition (PR #607)
   for the fabricated-citation defect class; the #600 decision-wait stop
   rule (PR #622) for pattern-match brittleness.
4. For any surface legitimately unreachable in a fixture (no consumer
   repo available, no reachable trigger path), record the concrete
   blocker in the hunt table rather than skipping the row.
5. Write `docs/issue-628/reports/execution-observation.md`: a per-surface
   hunt table (surface, exercised-how, finding-or-evidence-of-absence,
   signature class) with fenced drive output per surface, followed by
   the outcome/trajectory/step verdict section, independence statement
   preceding all verdict language.

## Out of scope

Fixing anything found; filing issues; editing any observed surface's
source, tests, or another issue's docs tree; re-litigating #587's
already-recorded three prior silent failures beyond citing them as
established; hunting #576/#619 (marked "phase 2 in flight" — not yet
merged, nothing to drive).

## What did not work

- After-proposal warrant hunt (stance 0, `docs/reports/2026-08-10-hunt-execution-observation-silent-failure-hunt.md`)
  found the "evidenced absence" / "fenced fixture-drive output"
  requirement below has no mechanical enforcement — an executor could
  hand-type a plausible fenced block or invoke the "legitimately
  unreachable" escape hatch without a real fixture drive, and every
  "how you'll know it worked" item would still read as satisfied.
  Mitigation folded into phase 2 (not a proposal-text fix, since no
  automated checker exists for this claim class, unlike
  `role-test-claim-guard.sh`'s test-run cross-check): each fenced drive
  block in the hunt record must include the fixture's `$TMPDIR` path
  and the literal command invoked, so a reader can independently confirm
  the block is not hand-typed; any "legitimately unreachable" row must
  name the concrete blocker (missing consumer repo, no reachable
  trigger) rather than a bare "not reachable."

## How you'll know it worked

`docs/issue-628/reports/execution-observation.md` exists, committed,
with every named surface in the issue body appearing as a table row
(finding or evidenced absence), every verdict-bearing sentence carrying
an adjacent citation, the independence statement preceding all verdict
language, and `loop_state` at a terminal value for this record kind.
