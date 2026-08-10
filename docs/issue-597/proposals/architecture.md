# Architecture proposal — issue-597: framing-snapshot comments at flow transitions

## Upstream / basis
Issue #597. Survey: `docs/issue-597/reports/architecture/survey.md`. Scout brief:
`docs/issue-597/reports/architecture/scout-brief.md`. Prior art extended:
`docs/issue-573/proposals/architecture.md` (sections 11-12),
`docs/issue-320/proposals/2026-08-07-semantic-effect-reporting.md`.

## 1. Writer: a gate, extending the section-12 writer, not a new surface

`delegated-judgment-gate.sh` already runs as a `PreToolUse` hook on the
`Bash` matcher (registered in `on-the-record/hooks/hooks.json`) and already
writes to issues via `gh issue comment <n> --body-file -` for section-12's
five events. This proposal adds a **sixth firing condition** to the same
script rather than introducing a new hook or a new transport: fewer moving
parts, one writer to audit, and it reuses the vantage point (every outgoing
`gh` command is visible to it before it runs) that the new transitions need
anyway.

Rejected alternative: a `run.md` contract step (role narrates the framing,
contract step posts it). Rejected because the content would then originate
from the role's free text — exactly the failure mode issue-320's
`report-framing-check.sh` already tried and failed to gate (it can only
check keyword presence, not citation validity, and it checks the
orchestrator's own prose rather than writing anything itself). The gate
must *synthesize* the four elements from records itself, not check a role's
synthesis after the fact.

## 2. Trigger taxonomy: three transitions, one detection mechanism

All three transitions are detected the same way — by pattern-matching the
`gh` command about to run, at the same `PreToolUse` point section 12 already
observes:

| Transition | Detected by | Existing surface reused? |
|---|---|---|
| Delivery PR merged | `spawn.py`'s watch/session-end signal that section 12 already reuses for its "remediation PR merged" event | Yes — no new detection |
| Issue reopened | `gh issue reopen <n>` command pattern seen by the same `PreToolUse`/`Bash` hook | No — new match added to the existing hook |
| Issue closed | `gh issue close <n>` command pattern seen by the same `PreToolUse`/`Bash` hook | No — new match added to the existing hook |

Reopened/closed are new match arms in `delegated-judgment-gate.sh`'s
existing command-pattern dispatch, not a new hook registration — the hook
already fires on every `Bash` call, so adding two more command patterns to
its existing case logic is the minimal change.

## 3. Comment format: four labeled sections, each with a mandatory citation

```
## Framing snapshot — <transition label> (<issue-#> / <PR-# if applicable>)

**Resolved problem:** <synthesized sentence>
Citation: <record path or commit sha>

**Prior cost:** <synthesized sentence>
Citation: <record path or commit sha>

**Newly possible:** <synthesized sentence>
Citation: <record path or commit sha>

**Still broken:** <synthesized sentence>
Citation: <record path or commit sha>
```

Content generation rule: each element's sentence is assembled from fields
already present in cited records (role record sections, audit records,
PR/issue bodies) — never freely composed by the gate. This mirrors section
11's rule that comment bodies are "generated verbatim from the audit
record, never re-composed." Concretely, the gate reads: the merging PR's
linked role records (`docs/issue-<n>/reports/<role>.md`), the audit record
section 11 already writes, and (for reopened/closed) the issue body's
acceptance criteria — and quotes/paraphrases directly from those, attaching
the source path as the citation. It never invents a sentence with no
antecedent text in a record.

Non-duplication of section 12: this comment fires once per transition
(three transitions, not five events), at a coarser cadence than section
12's per-event lines. It is visually distinguished by the `## Framing
snapshot` header so the two comment kinds are never confused when scanning
the issue timeline, and it links back to the section-12 events it
summarizes rather than restating their content.

## 4. Citation rule: mechanized resolvability check, not free trust

Every `Citation:` line must resolve — checked mechanically before the
comment posts, the same way `record-claim-guard.sh`'s `orphaned_path_reference_check`
already verifies backtick-quoted paths exist in the working tree for
role-authored records. The gate applies the identical check to its own
generated comment body before posting: if a citation path does not exist
(or is not a valid commit sha), the gate fails closed and does not post —
it does not post a citation-free comment. This is the anti-theater floor
adapted from issue-476's "field presence is gameable" line: since there is
no command to re-execute for a narrative claim, the enforceable substitute
is that every claim's *source* must be a real, checkable artifact, not that
the claim's *content* is independently re-derived.

## 5. Baseline behavior: no prior records

When a transition fires on an issue with no prior role records or audit
records to cite (first proposal of a new issue reaching its first
transition), the gate does not fabricate "prior cost" or "resolved problem"
content. It posts the same four-section format with an explicit baseline
statement per empty element, e.g.:

```
**Prior cost:** No prior records exist for this issue — this is the
first tracked transition. Baseline: no established cost to compare
against yet.
Citation: <issue-#> (no prior record; issue body is the baseline)
```

The citation for a baseline element points to the issue itself (its number
or body), stating explicitly that it is a baseline citation, not a record
citation — so the mechanized resolvability check in section 4 still has
something real to verify, and "empty" is a stated fact rather than a
silently skipped section.

## Out of scope (implementation-role territory)

- The exact regex/parse for matching `gh issue reopen`/`gh issue close`
  command lines.
- The exact field-extraction logic that pulls sentences from role records
  into the four elements (this proposal fixes the *rule* — assembled from
  cited record text, never freely composed — not the extraction code).
- Test fixtures driving a simulated transition (acceptance criteria names
  this; it is phase-2/implementation work).

## Acceptance mapping

- "Framing comment lands at each covered transition, four labeled
  elements, each citing at least one record path" → sections 2, 3.
- "Empty state states baseline explicitly" → section 5.
- "Written by the deployed surface, not orchestrator free prose" →
  section 1 (extends the existing gate, same writer-path test pattern as
  section 11-12).

## What did not work
(none yet — phase 1, no build attempted)

## loop_state
kind: proposal
loop_state: scope-proposed

## Open findings
None at phase 1. Detection-pattern edge cases (e.g. `gh issue close` via a
different subcommand alias, or PR auto-merge not going through a `gh`
command the hook observes) are flagged for implementation-phase scouting,
not resolved here.

## Next steps
Await approval (`APPROVE issue-597/architecture` per contract v3 s19,
single-account mode, since this session both authors and would approve).
On approval: implement the sixth firing condition and citation-check
extension in `delegated-judgment-gate.sh`, write
`docs/issue-597/reports/architecture.md`.

## Resolution path
Implementation-phase work resolves the detection-pattern edge cases named
above via the same scout-then-build discipline, scoped to
`on-the-record/hooks/delegated-judgment-gate.sh` and its tests.
