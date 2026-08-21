---
code_under_review:
  - docs/reports/keep-role-precision-sample.md
type: report
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #1750

## What was done

Delivered the approved phase-1 proposal
(`docs/issue-1750/proposals/keep-role-precision-sample.md`, approved via
`APPROVE issue-1750/implementation` on the issue). Produced and committed
`docs/reports/keep-role-precision-sample.md` (commit 1d37f638):

1. Recomputed the 20 sampled indices via the proposal's deterministic
   rule (every 15th row, 1-indexed, among the 307 `keep-role` rows in
   `docs/reports/rulebook-hook-audit.md`, in report order):
   `1, 16, 31, 46, 61, 76, 91, 106, 121, 136, 151, 166, 181, 196, 211,
   226, 241, 256, 271, 286`.
2. For each of the 20, resolved its repo + hook file path (via
   `gh api repos/tokenmaxxxer/<repo>-rulebook/git/trees/main?recursive=true`)
   and fetched the FULL script body live (`gh api .../contents/<path> -q
   '.content' | base64 -d`), then re-judged promote/keep-role/retire
   against the audit's own stated classification rule (Methodology
   section: directive.sh mechanism-is-core/content-is-role-unique ->
   keep-role; `*-gate.sh` mechanism-is-core/check-content-is-role-specific
   -> keep-role, UNLESS the check content restates a role-handoff-contract
   -wide, not domain-wide, requirement -> promote).
3. Wrote the report with the 20-row table (original class, re-judged
   class, one-line reason grounded in the fetched script), the precision
   figure, the re-judged class distribution, and a conclusion section
   naming the triggered threshold branch.

canonical: `docs/reports/keep-role-precision-sample.md` "Sample table" and
"Precision and re-judged class distribution" sections (this session's own
commit 1d37f638, containing the 20 fetched-script re-judgments and the
computed figure).

derived: count of rows re-judged `keep-role` in the sample table
```
$ grep -cE '^\| [0-9]+ \|.*\| keep-role \| keep-role \|' docs/reports/keep-role-precision-sample.md
18
```
The remaining 2 rows (#9 `interaction-design/id-stage-order`, #10
`issue-retrospective/proposal-order-gate`) are the disagreements, each
re-judged `keep-role` -> `promote` for the reason stated in that row: the
fetched full script enforces only the role-handoff-contract-wide
survey/scout/phase-ordering norm with zero domain-specific content, the
same pattern the original #1746 audit itself classified `promote` for
`implementation-rulebook`'s `survey-order-gate.sh`.

derived: total keep-role rows sampled from
```
$ awk -F'|' '$0 ~ /\| keep-role \|/ && $6 !~ /^[[:space:]]*$/ {print NR}' docs/reports/rulebook-hook-audit.md | wc -l
307
```

## Why

Program phases 3-5 hinge on whether the #1746 audit's 307 keep-role
count, derived from header-comment reading only, is reliable. This issue
exists to measure that reliability on a sample before any further phase
commits resources to it (per the issue text and its
`validity-consult: docs/reports/consult-log.md` trailer).

## Upstream basis

- Issue #1750 (this issue's own Acceptance 1-2, frozen).
- `docs/issue-1750/proposals/keep-role-precision-sample.md` (approved
  phase-1 proposal this delivery implements).
- `docs/reports/rulebook-hook-audit.md` (issue #1746's audit, the subject
  being sample-verified).

## Acceptance verification

1. checked: 20 samples selected by the stated deterministic rule, each
   with a full-script re-judgment and reason.
   canonical: `docs/reports/keep-role-precision-sample.md` "Sample table"
   section (commit 1d37f638), 20 rows each carrying original class,
   re-judged class, and a reason grounded in the fetched script content.
   acceptance: `grep -c '^| [0-9]' docs/reports/keep-role-precision-sample.md` — result:
   ```
   $ grep -c '^| [0-9]' docs/reports/keep-role-precision-sample.md
   20
   ```
2. checked: precision figure computed and the threshold conclusion
   stated explicitly.
   canonical: `docs/reports/keep-role-precision-sample.md` "Conclusion"
   section (commit 1d37f638).
   acceptance: `grep -n "Computed precision\|branch is triggered" docs/reports/keep-role-precision-sample.md` — result:
   ```
   $ grep -n "Computed precision\|branch is triggered" docs/reports/keep-role-precision-sample.md
   **Computed precision: 18/20 = 90%.**
   90% >= the 80% threshold stated in the issue's Acceptance criterion 2, so
   the **>=80% branch is triggered: the keep-role figure (307) stands**, and
   ```

## What did not work

None.

## Doc-placement ladder

- Benchmark/investigation numbers -> `docs/reports/`:
  `docs/reports/keep-role-precision-sample.md` (this delivery's sole
  write-set file, per the frozen proposal, committed as 1d37f638).

## Hunt

Dispatch skipped this cycle: the write set is a single measurement report
with no executable code path and no runtime component, so there is
nothing beyond the script-content judgments already made and cited above
for a hunter to independently probe. Recorded per the hunt-cadence
requirement.

## Open findings

None.

## Rationale for deviations

Not applicable — the delivery followed the approved proposal's build
section verbatim (one file, `docs/reports/keep-role-precision-sample.md`,
20-row table + precision + threshold conclusion), with no scope-exceeded
stop and no alternative swap.
