# Ordering-Norm Gate Sweep

Skill-axis phase 2d (issue #1753): sweep all 307 `keep-role` rows in
`docs/reports/rulebook-hook-audit.md` for the pattern #1750's precision
sample surfaced — `*-gate.sh` hooks that enforce only the contract-wide
write-order/phase-order/survey-first norm with zero domain content,
misclassified `keep-role` because the original audit read header
comments only.

## Screen

derived: `grep '| keep-role |' docs/reports/rulebook-hook-audit.md | grep -v '| 307 |'` (excludes the Summary table's own `keep-role | 307` count row) — 307 rows.

Deterministic filter applied to the `hook file` column of every keep-role
row: filename matches the regex

```
(order|phase|sequence)[a-zA-Z0-9_./-]*-gate\.sh
```

case-insensitive. This targets the same filename shape as the six
already-promoted implementation-rulebook hooks (`proposal-shape-gate.sh`,
`record-shape-gate.sh`, `survey-order-gate.sh`) and the two disagreements
#1750's precision sample found — a hook file named for ordering/phase/
sequence, not for a domain deliverable.

```
python3 /tmp/extract_rows.py   # matched rows printed, count on last line
```
14 rows matched. 307 − 14 = 293 screened out (filename carries no order/
phase/sequence token — e.g. `wcag-em-gate.sh`, `record-fields-gate.sh`,
`evidence-metric-gate.sh` — left `keep-role` unexamined by this sweep,
consistent with the audit's own domain-parameterized-content
classification rule for those).

Screen shape check: 14 matched + 293 screened-out = 307 (equal to the
full keep-role row count). No non-matching row was treated as a
candidate; no matching row was left without a verdict (see per-candidate
table below).

## Per-candidate verdicts

Each row's full script was fetched live via `gh api
repos/tokenmaxxxer/<rulebook>/contents/<path>` (not the audit's
header-comment excerpt) and read in full.

| rulebook | hook file | verdict | evidence |
|---|---|---|---|
| architecture-rulebook | `arch-sequence-gate/hooks/sequence-gate.sh` | **promote** | Header states it "owns exactly one methodology: phase ORDERING" (survey→scout-brief-or-skip→proposal→record); body is pure sibling-file-existence checks via `gate-lib.py`, no domain keyword/section requirement anywhere in the script. |
| content-design-rulebook | `content-design-phase1-basis/hooks/phase1-basis-gate.sh` | **promote** | Header: "phase-1 proposal must state a survey+scout basis (or documented skip)"; body is a single regex check for a survey/scout basis statement, no content-design-domain vocabulary (copy, tone, channel, etc.) anywhere. |
| customer-support-rulebook | `customer-support-phase1-order/hooks/phase1-order-gate.sh` | keep-role (confirmed) | Header + body require every structural claim to cite one of **`sla`/`escalation`/`playbook`/`evidence-metric`/`five-whys`** adjacent to the claim (`check_facet(...)` calls) — domain-parameterized content, not pure ordering. |
| devrel-rulebook | `phase-order/hooks/phase-order-gate.sh` | **promote** | Header: proposal "may not be written before" survey.md exists (phase-1 order only); body checks sibling-file existence only, no devrel-domain content (no docs/API/SDK-specific requirement in the script). |
| incident-response-rulebook | `incident-response-proposal-order-gate/hooks/order-gate.sh` | **promote** | Header: "enforces the phase-1 survey→scout→propose ORDER constraint"; body checks for a `scout` heading's presence and sibling-file existence — no incident-response-domain content (no severity/blast-radius/postmortem-field requirement). |
| interaction-design-rulebook | `interaction-design/plugins/id-stage-order/hooks/stage-order-gate.sh` | **promote** | Header: "owns exactly one cross-cutting constraint: ... stage ordering (survey → scout → proposal → [approval, core's job] → phase-2 record)"; body is explicitly "both checks purely file-EXISTENCE based (never content)" — no interaction-design-domain content. |
| issue-retrospective-rulebook | `proposal-order-gate/hooks/proposal-order-gate.sh` | **promote** | Header: "Owns: phase ordering (phase-1-before-phase-2, contract v3 s19)"; body reads the sibling proposal for a survey path + scout-brief-or-skip statement only — no retrospective-domain content. |
| issue-retrospective-rulebook | `timeline-order-gate/hooks/timeline-order-gate.sh` | keep-role (confirmed) | Header: "Timeline-first ordering (issue #12 record norm) — a record's Timeline section must be present, and no causal-claim language ('contributing factor(s)'/'root cause') may appear before it." This is an in-document blameless-postmortem norm specific to issue-retrospective, not the contract's phase-1→phase-2 write-order norm — domain content. |
| observability-rulebook | `observability-phase-trace/hooks/phase-trace-gate.sh` | keep-role (confirmed) | Enforces that a phase-2 record's **deviation markers** ("이탈"/"deviat"/"switch"/"변경") each carry a nearby **reason marker**, traced against a `methodology_named` state file the role's own methodology-selector plugin writes — role-specific semantic content, not generic ordering. |
| pr-communications-rulebook | `race-sequence/hooks/race-sequence-gate.sh` | keep-role (confirmed) | Enforces the domain-specific **RACE** framework order (Research → Action → Communication → Evaluation) on `loop_state: landed` records — a named methodology, not the contract's generic phase ordering. |
| risk-management-rulebook | `erm-verdict-methodology/hooks/erm-order-gate.sh` | keep-role (confirmed) | Enforces **ISO 31000:2018 process-clause ordering (6.3/6.4/6.5/6.6)** on erm-verdict documents — domain-specific standard citation, not generic ordering. |
| security-threat-model-rulebook | `security-threat-model/hooks/sequence-gate.sh` | **promote** | Header: "sequence-precondition gate: a phase-1 proposal write must not happen before this issue's phase-1 survey exists"; body is a single survey-existence precondition, no threat-model-domain content (no STRIDE/asset/mitigation requirement). |
| user-discovery-rulebook | `user-discovery-hypothesis-order/hooks/hypothesis-order-gate.sh` | keep-role (confirmed) | Enforces **Customer Development** ordering discipline specific to user-discovery: falsifiable hypotheses stated before interviews, evidence before verdict, tracked via `hypotheses_stated`/`evidence_logged`/`verdict_written` — domain methodology, not generic contract ordering. |
| ux-engineering-rulebook | `ux-phase1-structure-gate/hooks/phase1-structure-gate.sh` | keep-role (confirmed) | Enforces the **Double Diamond** (Discover → Define) seven-section phase-1 proposal structure adopted in issue-1/issue-7 §4.4 — a named UX-domain framework's document shape, not the contract's generic ordering norm. |

Verdict shape check: 14 candidates, 14 verdicts (7 `promote`, 7 confirmed
`keep-role`) — every candidate row above carries a verdict.

```
grep -c '^\| ' docs/reports/ordering-norm-sweep.md | true   # sanity only; see explicit count below
```
derived: manual count of the per-candidate table's data rows above — 14 rows, 14 verdicts, 0 unverdicted.

## Reclassified promote list

Mirrors the audit's promote-row format (`core target — note`).

| rulebook | hook file | core target / note |
|---|---|---|
| architecture-rulebook | `arch-sequence-gate/hooks/sequence-gate.sh` | `core/hooks/ordering-norm-gate.sh` (new, or fold into an existing core phase-order gate if one is created by the promotion follow-up) — Enforces the contract v3 s19 survey→scout-brief-or-skip→proposal→record file-existence ordering role-agnostically; no per-role parameterization needed. |
| content-design-rulebook | `content-design-phase1-basis/hooks/phase1-basis-gate.sh` | `core/hooks/ordering-norm-gate.sh` (new, or fold into same) — Enforces the same contract v3 s19 survey+scout-basis-before-proposal ordering; no content-design-specific parameterization needed. |
| devrel-rulebook | `phase-order/hooks/phase-order-gate.sh` | `core/hooks/ordering-norm-gate.sh` (new, or fold into same) — Enforces the same contract v3 s19 survey-before-proposal ordering; no devrel-specific parameterization needed. |
| incident-response-rulebook | `incident-response-proposal-order-gate/hooks/order-gate.sh` | `core/hooks/ordering-norm-gate.sh` (new, or fold into same) — Enforces the same contract v3 s19 survey→scout→propose ordering; no incident-response-specific parameterization needed. |
| interaction-design-rulebook | `interaction-design/plugins/id-stage-order/hooks/stage-order-gate.sh` | `core/hooks/ordering-norm-gate.sh` (new, or fold into same) — Enforces the same contract v3 s19 survey→scout→proposal→record stage ordering (approval step already deferred to core's own `approval-gate.sh`); no interaction-design-specific parameterization needed. |
| issue-retrospective-rulebook | `proposal-order-gate/hooks/proposal-order-gate.sh` | `core/hooks/ordering-norm-gate.sh` (new, or fold into same) — Enforces the same contract v3 s19 phase-1-before-phase-2 ordering; no issue-retrospective-specific parameterization needed. |
| security-threat-model-rulebook | `security-threat-model/hooks/sequence-gate.sh` | `core/hooks/ordering-norm-gate.sh` (new, or fold into same) — Enforces the same contract v3 s19 survey-before-proposal ordering; no threat-model-specific parameterization needed. |

7 rows reclassified to `promote`, each naming a core target. No hook was
moved or edited by this sweep; promotion execution (creating/wiring the
shared `core/hooks/ordering-norm-gate.sh` and retiring the 7 per-rulebook
copies) is a follow-up core issue fed by this list, per the issue's
requirement 3.

## Updated class counts (informational, not a rewrite of the audit)

derived: 307 (original keep-role) − 7 (reclassified) = 300 keep-role,
7 + 7 (already-promoted) = 14 promote, 0 retire, 314 total — unchanged
total, per the audit's own Summary table shape.
