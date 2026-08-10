# Conformance review — issue-597 sixth firing condition (phase 2)

## Upstream / basis

Requirement list: `docs/issue-597/proposals/conformance-review.md` (phase 1,
PR #612, approved via `APPROVE issue-597/conformance-review`). Reviewed
artifact: PR #607, `on-the-record/hooks/delegated-judgment-gate.sh`
(commit `edf45943f9b6d0f63e909758276fbeeea666d3f1`),
`on-the-record/hooks/test_delegated_judgment_gate.py`. Spec:
`docs/issue-597/proposals/architecture.md`, issue #597 body.

## What was done

Artifact-only re-read of `delegated-judgment-gate.sh` and its test file
against `architecture.md` sections 1-5 and the issue's acceptance bullets;
ran the test suite as evidence for R9/R10:

```
$ python3 on-the-record/hooks/test_delegated_judgment_gate.py
  ok  t_all_five_issue_timeline_events_fire_across_reject_flow
  ok  t_auto_approve_single_role
  ok  t_auto_reject_with_finding_and_remediation
  ok  t_escalate_on_empty_corpus
  ok  t_escalate_on_no_quorum
  ok  t_framing_snapshot_baseline_on_delivery_merged_no_prior_records
  ok  t_framing_snapshot_fails_closed_on_unresolvable_citation
  ok  t_framing_snapshot_on_issue_closed_cites_decision_record
  ok  t_framing_snapshot_on_issue_reopened_cites_role_record
  ok  t_kill_switch_disables_the_gate
  ok  t_loop_bound_exhausted_escalates_at_round_4
  ok  t_multi_role_panel_quorum_and_unanimous_support_approves
  ok  t_no_import_gates_and_no_checkout_resolve_in_the_hook_source
  ok  t_no_trigger_no_side_effects
  ok  t_partial_support_with_no_opinion_escalates_not_approves
  ok  t_repeat_contradiction_from_same_role_escalates_before_round_3

16 passed
```

Checked `on-the-record/hooks/hooks.json` directly to verify no new
`PreToolUse` matcher was registered for R2. One verdict rendered per
requirement below.

## Verdicts

**R1 — Writer is the deployed gate, not orchestrator free prose: Present.**
`build_framing_snapshot` assembles the comment body and the same
function's caller posts it via `_gh(["issue", "comment", ...])`, inside
`delegated-judgment-gate.sh` itself — no role-authored text passes through
unmodified.

**R2 — Three transitions, single detection mechanism, no new hook:
Present, with one spec/table divergence noted.** `FRAMING_TRANSITIONS`
lists all three patterns (`gh pr merge`, `gh issue reopen <n>`, `gh issue
close <n>`) matched by one shared loop against the same `cmd` string
already extracted from the `Bash` PreToolUse payload; `hooks.json`'s
`PreToolUse`/`Bash` matcher entry is unchanged — `delegated-judgment-gate.sh`
is still the only line there, no new matcher block. This satisfies the
requirement as extracted. Divergence: architecture §2's table states
delivery-merged is detected via "spawn.py's watch/session-end signal that
section 12 already reuses" ("no new detection"), but the code detects it
the same way as the other two — a `gh pr merge` command-pattern match on
the existing hook, not a session-end signal. The delivered mechanism is
still singular and free of any new hook registration (satisfying the
requirement's literal check), but it does not match the specific "Detected
by" cell architecture.md names for that row. Flagged per contract §5 as a
spec/implementation contradiction on that one table cell, not a fidelity
failure of R2 as extracted.

**R3 — Four labeled elements per comment: Present.** Both branches of
`build_framing_snapshot` (the `if not records:` baseline branch and the
populated branch) produce an `elements` dict with exactly the four keys
`Resolved problem`, `Prior cost`, `Newly possible`, `Still broken`, and the
output loop always emits all four `**Label:**` lines in that fixed order.

**R4 — Mechanically-resolvable citation check before posting, fail-closed:
Present.** `build_framing_snapshot` iterates every element's citation
through `resolve_citation` before any `_gh` call; on any failure it
returns `None` and the caller skips posting entirely. Confirmed also by
test `t_framing_snapshot_fails_closed_on_unresolvable_citation` (no
log/no post on an unresolvable citation, in the run above).

**R5 — Citation-per-element vs. citation-per-comment: Present, per-element
confirmed.** Every element in both branches carries its own
`(sentence, citation)` pair, and the output loop emits one `Citation:`
line immediately under each `**Label:**` line — four citations per
comment, one per element, not one citation for the whole comment. Matches
both source wordings; no divergence found.

**R6 — Content assembled from cited record text, never freely composed:
Incorrect.** The populated branch's per-element fallback sentences (e.g.
"No resolved-problem field found in this issue's audit records yet.") are
hardcoded strings authored by the gate itself, not extracted from any
record's text, yet on the fallback path they are paired with
`fallback_cite` (`records[0]`'s own path) as if that file were their
source — that file need not contain any such sentence. Architecture §5's
baseline exception covers only the case where no records exist at all
(the `if not records:` branch); it does not cover the case reached here —
records exist, but a specific field/heading was not found within them.
This second, uncovered case invents a sentence with no antecedent text in
the cited record, contradicting architecture §3's explicit rule ("never
invents a sentence with no antecedent text in a record") and the
acceptance line it maps to.

**R7 — Baseline behavior when no prior records exist: Present.** The
`if not records:` branch posts an explicit baseline statement per element
plus a baseline-form citation
(`"{issue} (no prior record; issue body is the baseline)"`), matching
architecture §5's example verbatim in form. Confirmed by test
`t_framing_snapshot_baseline_on_delivery_merged_no_prior_records` in the
run above.

**R8 — No duplication of section-12 one-line events: Present.** Read the
section-12 event-posting arms directly (the `gh pr create` handling):
those fire on a different trigger command and post single-line strings
("Judgment opened...", "Verdict: ...", "Remediation routed...",
"Escalated..."). The framing-snapshot arms fire on three distinct trigger
commands (`gh pr merge`, `gh issue reopen`, `gh issue close`) that
section 12 never matches, and the framing-snapshot loop's `sys.exit(0)`
returns before section-12's logic runs in the same invocation — the two
code paths are mutually exclusive per script run, not a restatement of one
by the other. Matches architecture §3's non-duplication paragraph (coarser
cadence, distinct header, no restated content).

**R9 — Test-fixture check: four labeled sections + citations asserted:
Present.** `t_framing_snapshot_baseline_on_delivery_merged_no_prior_records`,
`t_framing_snapshot_on_issue_reopened_cites_role_record`,
`t_framing_snapshot_on_issue_closed_cites_decision_record`, and
`t_framing_snapshot_fails_closed_on_unresolvable_citation` assert on the
`## Framing snapshot` header, all four `**Label:**` strings, and specific
citation path/baseline text (not merely "a comment was posted") — see
their source in `test_delegated_judgment_gate.py`, and the passing run
reproduced above.

**R10 — Writer-path test exists, same pattern as the pre-existing
writer-path tests: Present.** The four framing-snapshot tests use
`_stub_gh_with_stdin` and `_run_cmd` to invoke the real script the same
way the pre-existing writer-path tests invoke it via `_run` — a stubbed
`gh` logging every call plus stdin body, asserted against the captured
log — the same integration-test convention, extended to also capture
stdin for the framing-snapshot body.

## Why

Per-requirement fidelity verdicts, artifact-only, per the conformance-review
role's rulebook (never a holistic quality read, never a fix).

## What did not work

(none — phase 2 rendered verdicts directly from the already-scoped
requirement list; no method changes needed.)

## loop_state

kind: review-record
loop_state: draft-reported

## Open findings

- **R6 — Incorrect.** Fallback sentences for "field not found within an
  existing record" are gate-authored prose cited to a record that need not
  contain them, uncovered by architecture §5's no-records-at-all baseline
  exception. Addressed to: implementation role (owns
  `delegated-judgment-gate.sh`, `docs/issue-597/reports/implementation.md`
  write scope). Resolution path below.
- **R2 — spec/table divergence (not itself a fidelity failure).**
  Architecture §2's table names "spawn.py's watch/session-end signal" as
  delivery-merged's detection surface; the delivered code detects it via
  `gh pr merge` command-pattern match instead, on the same hook as the
  other two transitions. Addressed to: architecture role (owns
  `docs/issue-597/proposals/architecture.md`), for the table cell to be
  corrected or reconciled — the code's actual mechanism otherwise satisfies
  R2 as extracted.

## Next steps

Findings above route to the implementation role (R6) and architecture role
(R2 table note) per contract v3 s19 hand-off — this role does not edit
`delegated-judgment-gate.sh` or `architecture.md`. Verdict tally: Present
for R1, R2, R3, R4, R5, R7, R8, R9, R10; Incorrect for R6. Overall: the
sixth firing condition substantially conforms, with one Incorrect finding
(R6) that should block treating #597 as fully conformant until addressed,
since it targets the same acceptance-mapping line ("never invents a
sentence... antecedent text in a record") architecture §3 and the issue's
acceptance bullet 1 both state directly.

## Resolution path

R6: implementation role either (a) extends architecture §5's baseline
exception explicitly to the per-field-not-found case (a proposal-level
change, then re-implements the fallback citation to point at a genuine
issue-level baseline citation, not a specific record's path), or (b)
changes the fallback citation to the same baseline-citation form R7 already
uses (`"{issue} (no prior record; issue body is the baseline)"`) when a
field is absent from an otherwise-present record, so the citation's claim
matches what it actually points to. R2: architecture role corrects
section 2's table cell to state the actual mechanism (command-pattern match
on the existing `PreToolUse`/`Bash` hook), or explains why the table's
original design was superseded during implementation.
