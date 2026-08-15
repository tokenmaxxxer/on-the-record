---
status: proposed
files:
  - docs/issue-745/proposals/item3-execution-observation-conditioning.md
---

# Proposal — issue #745, Item 3: diff/risk-conditioned `execution-observation` spawning

Phase 1 only, per operator direction (2026-08-15, in-conversation, per the issue's own "결정 유보" section): Item 3 proceeds first as a pre-registered experiment, replacing the docs-only-only candidate 1 in `docs/issue-745/proposals/product-discovery.md`'s Item 3 with a multi-factor design (change size, reversibility, claim type), while preserving `#476`'s no-self-report line unconditionally. **Proposal only — the conditioning itself is not implemented in this PR.**

## Why the original Item 3 candidate is insufficient on its own

`docs/issue-745/proposals/product-discovery.md` Item 3 candidate 1 conditions spawning on one axis only — whether the diff carries an executable artifact (`roles/execution-observation.json`'s own stated `board_condition`). canonical: `docs/issue-745/reports/product-discovery/current-state.md` §3 — of 158 issue directories carrying an `implementation.md` report, only 25 also carry any `execution-observation*` record (133, 84%, already skip it in practice, unconditioned). A single docs-only/not-docs-only axis does not distinguish a one-line additive config tweak from a hard-to-revert change to `gates/*.py` or `on-the-record/hooks/*.sh` — both currently land in the same "not docs-only" bucket and would both require the role under candidate 1 alone, or both skip it under any looser single-axis rule. The operator's charge for this session names three axes explicitly: change size, reversibility, claim type.

## The conditioning rule (proposal, not yet implemented)

`execution-observation` is **required** when the landed diff trips ANY of:

1. **Change size** — non-docs (code/config/hook/gate) lines changed (added + removed, `git diff --stat` numstat sum) at or above 50 lines.
2. **Reversibility** — the diff touches any path in a fixed hard-to-revert allowlist: `gates/*.py`, `on-the-record/hooks/*.sh` (and `hooks.json` registering them), `roles/*.json`, migration-shaped paths, or any path deletion (not pure addition).
3. **Claim type** — the landing record/PR body trips `gates/claim_scan.py`'s existing claim-vocabulary regex (`reproduced|verified|confirmed|passed|tests? pass(es|ed)?|repro(duces|duced)?`) — i.e., the author is making an execution claim at all, regardless of diff shape.

`execution-observation` is **skip-eligible** only when ALL three axes read low-risk: non-docs lines changed under 50, no hard-to-revert path touched, and no claim-vocabulary match in the record. This strictly subsumes the original candidate 1's docs-only rule (a docs-only diff trivially has zero non-docs lines changed and, in practice, carries no execution claim) while adding coverage for small-but-risky and code-but-safe cases the single-axis rule could not separate. `#476`'s mechanism itself is untouched by this proposal — when `execution-observation` *does* run, or when `gates/claim_scan.py`/`gates/reexecution_gate.py` fire independently of role spawning, mechanized re-execution still applies exactly as today; this proposal only conditions *whether a session is spawned*, never whether a claim, once made, gets independently re-executed.

## Candidates scored (RICE)

Reach/impact scored against the same "sessions this repo runs per week across active issue×role branches" basis `docs/issue-745/proposals/product-discovery.md` already used and flagged as lacking a direct cadence log.

| # | Candidate | Reach | Impact | Confidence | Effort | RICE | Note |
|---|---|---|---|---|---|---|---|
| 1 | Multi-factor conditioning (size + reversibility + claim type, above) | 4 | 4 | 0.6 | 3 | 3.2 | Subsumes candidate 2; the axes are independently checkable against data already in the diff and the record, no new instrumentation needed |
| 2 | Original Item 3 candidate 1 — docs-only `board_condition` enforcement only | 3 | 4 | 0.8 | 2 | 4.8 | Higher raw RICE (simpler, higher confidence) but leaves the 133/158-issue skip population's small-but-risky and code-but-safe cases undifferentiated — the exact gap the operator's charge names axes to close |
| 3 | No change (status quo — unconditioned orchestrator judgment) | 5 | 1 | 0.9 | 0 | — | Baseline candidate |

Candidate 1 is preferred over the higher-raw-RICE candidate 2 for the same reason `docs/issue-745/proposals/product-discovery.md` Item 1 preferred its own candidate 1 over a higher-RICE alternative: candidate 2 screens on one axis only and was already in scope before this session; the operator's charge this turn is specifically to add the size/reversibility/claim-type axes, so candidate 1 is the one carried into pre-registration below.

## Pre-registered hypothesis package — candidate 1 (multi-factor conditioning)

Guardrail metric: `fabrication_survival_rate` — the same named metric from `docs/issue-476/reports/execution-observation.md`, already the guardrail for the original Item 3 candidate in `docs/issue-745/proposals/product-discovery.md` — named and non-empty at this same registration moment, distinct from the primary metric below. This preserves `#476`'s no-self-report line exactly: no nonzero rate is acceptable regardless of the primary metric's outcome, mirroring the zero-tolerance framing `docs/issue-707/proposals/product-discovery.md` and the original Item 3 package both already established for this same metric.

- **Metric**: `execution_observation_sessions_per_landed_pr`, computed separately for two populations over the measurement window — (R) PRs the multi-factor rule classifies as *required* (any axis trips), and (S) PRs it classifies as *skip-eligible* (all three axes low-risk).
- **Measurement window**: the next 20 landed PRs after the conditioning rule ships, classified retroactively by the same three axes (diff numstat, hard-to-revert path list, `claim_scan.py`'s regex against the landing record) so population membership is reproducible from the ledger and diff history alone, not from what actually got spawned.
- **Threshold**: population (S)'s `execution_observation_sessions_per_landed_pr` falls to at most 10% of its own pre-change baseline (the same 20-PR-equivalent population, reclassified retroactively over the most recent 20 landed PRs before the rule ships, using the identical three-axis test). Population (R) stays within measurement noise of its own pre-change baseline (no more than a 10% relative change either direction — a rise in (R) would mean the rule is over-triggering on already-required PRs, a defect worth catching, not a cost regression; a fall would mean required PRs are silently skipping the role).
- **Guardrail status at measurement**: `fabrication_survival_rate` over the same 20-PR window must be exactly zero across **both** populations (R) and (S) combined — not a percentage tolerance — stated explicitly next to the primary metric's value, never implied. A single fabricated, unverified execution claim shipping because it fell into population (S) is the exact harm `#476` exists to prevent; the rule's entire size/reversibility/claim-type design exists to keep such a PR out of (S) in the first place (axis 3 alone should already route any claim-bearing PR to (R)), so a guardrail breach here is also evidence the claim-type axis itself is under-specified, not just that the experiment failed.
- **Decision rule**: population (S) at or below its 10% threshold AND population (R) within its noise band AND the guardrail at zero across both populations → **persist**, and consider whether the 50-line size threshold or the hard-to-revert path list can be widened further. If population (S) does not reach the 10% threshold → **pivot**: the three axes are not classifying enough of the currently-unconditioned-skip population as low-risk; re-examine which axis is over-triggering before loosening any threshold. If population (R) falls outside its noise band → **pivot**: the rule is either over- or under-triggering on already-required PRs; tighten or loosen the specific axis responsible before retrying. If the guardrail is ever nonzero, in either population, regardless of the cost metrics → **kill immediately**: the conditioning rule is refused and every PR reverts to the unconditioned always-eligible path until redesigned, mirroring `#476`'s own decision-record precedent for invariant violations and the original Item 3 package's identical zero-tolerance clause. No pivot is acceptable on the guardrail.
- **Revert condition**: any nonzero guardrail reading in either population, or population (S) failing to reach its 10% threshold across two consecutive 20-PR measurement windows after one axis-threshold adjustment.

## ITWWS (if this works we should ...)

If candidate 1 persists at threshold: fold the original Item 3 candidate 1 (docs-only `board_condition` enforcement) into this rule as axis coverage it already subsumes, rather than pre-registering it separately, and re-examine whether the same three-axis shape generalizes to other verification-shaped roles carrying an unenforced `use_when`/`board_condition` clause — the same generalization question the original Item 3 package's own ITWWS named, now carried forward under the refined rule. Deferred to whichever role and issue the operator assigns this to next; not actioned in this proposal.

## 결정 유보 (decision deferred)

This proposal stops here. The multi-factor conditioning rule is scored against the docs-only-only alternative, and the chosen candidate carries a named metric, numeric threshold (per population), a zero-tolerance guardrail preserving `#476`'s line, a fixed 20-PR measurement window, a mechanical decision rule, and a revert condition — none of it implemented. Whichever role the operator assigns next builds the classification check and ships it; this PR carries no code changes.
