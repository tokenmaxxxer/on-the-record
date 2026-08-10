---
status: proposed
files:
  - docs/issue-573/reports/implementation/survey.md
  - docs/issue-573/proposals/implementation.md
  - roles/architecture.json
  - roles/security-threat-model.json
  - roles/specs/architecture.spec.json
  - roles/specs/security-threat-model.spec.json
  - gates/role_spec_shape.py
  - gates/test_role_spec_shape_batch9.py
  - on-the-record/hooks/delegated-judgment-gate.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/test_delegated_judgment_gate.py
  - docs/product/.gitkeep
  - gates/gates.py
---

# Proposal — issue #573: delegated-judgment gate (implementation, phase 1)

Phase 1 only: this session's write set is the two files above under
docs/issue-573/reports/implementation/ and docs/issue-573/proposals/;
everything else in `files:` is frozen for phase 2, opened only on
approval. Grounded in docs/issue-573/proposals/architecture.md (PR #581,
merged, all 12 sections) and docs/issue-573/reports/implementation/survey.md;
does not re-derive architecture's own component-boundary or methodology
work.

## Request

Build the merged architecture design end to end: the axis-role schema
extension on roles and role specs; the delegated-judgment-gate hook
implementing the two-axis AND rule, full-panel quorum, and the
panel-unanimous-support-v1 synthesis rule; contradiction-only auto-reject
carrying a routable finding object; the auto-*.md / remediation-*.md
audit-record writers; write-scope-based remediation routing with a
bounded (3-round) loop; in-place gh pr/issue comment posting generated
from the audit record at synthesis time, covering all five issue-timeline
firing events; and the degradation rule (empty product corpus escalates
everything, via the AND composition, no special-case branch). Zero-install
consumer surface: no `gates/` package import from a deployed hook — port
whatever logic is needed inline, matching every other hook in
on-the-record/hooks/. Tests per firing event and per synthesis branch.

## Constraints

- No import of `gates/` from the deployed hook (`on-the-record/hooks/delegated-judgment-gate.sh`)
  — it is a zero-install consumer surface, same rule every existing hook
  in that directory already follows (they inline what they need or shell
  out to `python3` with a self-contained heredoc, never `import gates`).
- Same structural mirror as impact-guard.sh: `_checkout_resolve()`,
  `TARGET_REPO="$(pwd -P)"`, `ORCHESTRATE_OFF` kill switch, Python
  heredoc — no deviation from that shape without a stated reason.
- `gates/role_spec_shape.py` gets additive-only checks (new field/shape
  acceptance); its existing top-level-required-keys and field-type
  constants are not restructured.
- Which of the 30 roles ultimately owns which axis is out of scope
  (architecture.md says so explicitly); this phase seeds `judgment_axes`
  only on the two roles the gate's own tests need to exercise a
  multi-role panel (architecture, security-threat-model), not all 30.
- The audit-record and remediation-record files themselves
  (docs/issue-<n>/decisions/auto-*.md, remediation-*.md) are written by
  the gate at runtime; this phase does not hand-author example records
  into the write set — only the writer code and its tests.
- `docs/product/.gitkeep` is added only if docs/product/ does not
  already exist in this repo (degradation-rule test needs an
  empty-corpus fixture state to assert against; verified empty vs.
  absent during phase 2, not assumed here).
- Commit carries the `Subject: issue-573` trailer per contract v3 s13;
  phase-1 PR body references `#573` as plain text, never `Closes #573`
  (contract v3's phase-1/phase-2 split, reinforced by the known
  contract-guard defect #577).

## Rationale

Considered building the gate as a thin wrapper that imports
`gates/risk_report.classify_axes()` directly from the deployed hook,
mirroring `impact-guard.sh` literally (that hook does import
`gates.risk_report` via a checkout-relative `sys.path` add, not a true
zero-install port). Rejected: architecture.md's own "Deployment target"
framing and this issue's stated requirement both call out zero-install
explicitly for the delegated-judgment surface, and unlike
`impact-guard.sh` (an existing, already-shipped hook whose import style
predates this issue and is out of this phase's scope to refactor), the
new hook has no existing consumers depending on the checkout-import
shape — so this phase can port the specific classifier logic the gate
actually needs (the four-axis grade function and its fail-closed
defaults) inline into the new hook's own heredoc, rather than importing
the package. This keeps the new hook installable in a target repo that
never clones the on-the-record checkout at all, which the checkout-import
style does not guarantee (`_checkout_resolve()` falls back to `git
clone`, a network dependency the zero-install framing is meant to avoid
for this specific new surface).

Also considered: growing `gates/role_spec_shape.py`'s existing large
batch test files (e.g. `test_role_spec_shape_batch8b.py`) in place
instead of adding a new batch file. Rejected in favor of a new
`test_role_spec_shape_batch9.py`, matching the repo's own established
convention of one batch file per feature addition round (batches 2
through 8b already follow this shape) rather than growing any single
file past what that convention already treats as "done."

## Warrant hunt (after-proposal)

The after-proposal hunt (docs/reports/2026-08-10-hunt-implementation.md,
stance 4 — write set cannot carry this work) found a real gap:
`gates/gates.py`'s `_always_writable()` allowlist does not include
`docs/issue-<n>/decisions/**`, so the gate's own audit/remediation record
writes (architecture.md sections 4/7) would fail the repo's existing
write-scope CI check the moment they land on a PR branch. `gates/gates.py`
is added to this proposal's frozen write set above (one line, extending
`_always_writable()`'s path list) to close this gap; no other change to
that file is in scope.

## Accumulation

`judgment_axes` on `roles/*.json` is the same repeated same-line-edit
shape as `write_scope`: at 28 more roles it does not change form, it is
still one array field per file, checked by the same
`gates/role_spec_shape.py` pass — no per-role special casing accrues.
The inline `gh pr comment` / `gh issue comment` calls inside the new hook
are bounded at exactly the five section-12 events plus the two
section-11 comment kinds; more issues using this same gate does not add
more call sites inside this hook, it runs the same fixed set of calls
once per decision — the accumulation axis here is decisions-per-issue,
not call-sites-per-hook, and decision volume is already bounded by the
section-8 loop cap (3 rounds) per finding chain.

## What will be done

1. Add `judgment_axes` to `roles/architecture.json` and
   `roles/security-threat-model.json` (architecture owns
   `maintenance_complexity`, security-threat-model owns
   `attack_potential` — the two axes architecture.md's own worked
   example and section-11 sample table already use).
2. Add `axis_evaluation` (ref[], optional) to both roles'
   `roles/specs/*.spec.json` `required_fields`, with the section-1
   `reference_resolution` clause and the section-6 conditional `finding`
   presence rule (finding required iff `verdict: contradicts`).
3. Extend `gates/role_spec_shape.py`: accept `judgment_axes` on
   `roles/*.json`; accept `axis_evaluation`'s shape including the
   conditional-finding check; reuse the existing reference-resolution
   walker, add no new checker file.
4. Write `on-the-record/hooks/delegated-judgment-gate.sh`:
   - Matches the same `gh pr review --approve` / single-account `APPROVE
     issue-<n>/<role>` comment acts `pr-preflight.sh` already matches.
   - Computes the impact axis via an inlined port of the four-axis
     fail-closed grade logic (dominant-axis rule, no averaging).
   - Computes the depth axis via a small inline matcher against the
     target repo's `docs/product/*.md` corpus; empty/absent corpus ->
     no match (this is the whole degradation rule — no separate branch).
   - Resolves `eligible_roles` from `write_scope` intersection +
     `judgment_axes` union (section 9), requires full-panel quorum,
     applies `panel-unanimous-support-v1` (section 9's three clauses)
     to decide approve / reject / escalate.
   - Writes `docs/issue-<n>/decisions/auto-<sequence>.md` (four-field
     format, section 4) on every resolved decision, fail-closed on any
     unresolvable field.
   - On reject, resolves `finding.target_path` against `write_scope`
     (section 7), writes `docs/issue-<n>/decisions/remediation-<sequence>.md`,
     increments `round`, escalates at `round > 3` or a repeat
     contradiction from the same role on the same path (section 8).
   - Posts the section-11 synthesis comment (`gh pr comment --body-file -`)
     at every synthesis resolution, the section-11 remediation comment at
     every routing, and the section-12 issue-timeline comment (`gh issue
     comment --body-file -`) at all five firing events — every posted
     comment generated verbatim from the audit-record fields it just
     wrote, never composed independently.
5. Register the new hook in `on-the-record/hooks/hooks.json` under the
   existing `PreToolUse`/`Bash` matcher block.
6. Write `on-the-record/hooks/test_delegated_judgment_gate.py`: one test
   per firing event (auto-approve, auto-reject with finding, escalate on
   no-quorum, escalate on empty/absent corpus, remediation routed, loop
   bound exhausted, repeat-contradiction escalation, all five section-12
   issue comments) and one per section-9 synthesis branch (approve /
   reject / escalate), run against a temp target-repo fixture the same
   way the existing impact-guard test file already sets one up.
7. Add `gates/test_role_spec_shape_batch9.py` covering the new
   `judgment_axes`/`axis_evaluation` shape acceptance and rejection
   cases (including the section-6 conditional-finding and section-1
   "axis owned by zero/multiple roles" schema-error cases).
8. Extend `gates/gates.py`'s `_always_writable()` to include
   `docs/issue-*/decisions/**`, so the gate's own audit/remediation
   record writes pass the existing write-scope CI check (warrant-hunt
   finding, see below).
9. Run the new tests once and fix what breaks before opening the phase-2
   PR for review, per the no-mock directive's single confirmation run.

## Out of scope

- Assigning `judgment_axes` to the remaining 28 roles — per
  architecture.md, a follow-up per-role content decision.
- Widening the depth-axis matcher's vocabulary beyond an initial small
  match rule — architecture.md names this as the explicit post-launch
  tuning lever (H1's pivot rule), not something this phase freezes.
- The "remediation PR merged" issue-timeline event's underlying
  merge-detection channel (section 12) — architecture.md states this
  reuses an existing session-end watch mechanism already observed
  elsewhere; this phase wires the comment-posting call for that event
  but does not build a new merge-watcher.
- Any change to `impact-guard.sh` or `gates/risk_report.py` themselves —
  both are read-only dependencies per the component boundary.

## How you'll know it worked

- `gates/role_spec_shape.py roles/specs/architecture.spec.json` and the
  security-threat-model equivalent both pass with the new
  `axis_evaluation` field present, and fail with a clear reason when
  `finding` is missing on a `contradicts` verdict.
- The new hook's test suite exercises and passes all five section-12
  events, all three section-9 synthesis branches, the section-3
  contradiction-only bar, the section-5 degradation rule (no special-case
  branch present in the merged code — verifiable by reading the diff),
  and the section-8 loop bound (round 4 escalates; a second contradiction
  on the same path from the same role escalates before round 3).
- `hooks.json` lists the new hook once, in the existing
  `PreToolUse`/`Bash` block; a manual approval-act invocation against a
  fixture target repo with a matching product-corpus entry produces
  exactly one auto-decision record and one PR comment, never two.
- No `import gates` (or `sys.path` addition targeting the checkout) exists
  anywhere in `on-the-record/hooks/delegated-judgment-gate.sh`.
