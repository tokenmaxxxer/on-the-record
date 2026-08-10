# Scout brief — issue-597

Non-product infra role; no external market sweep applies. Scouting here means
surveying this plugin's own best comparable prior art for the same shape of
problem (gate-written, record-cited GitHub comment), per the current-state
survey's gaps.

## Must-bes (from the closest comparable: the sections 11 and 12 writer pattern)
- Writer is a gate/hook, never the orchestrating role's free prose (section 11: "the
  gate ... never a role, never the operator").
- Comment content is generated from record fields verbatim, not re-composed
  at write time.
- Same `gh ... --body-file -` transport as everything else — no new channel.
- Detection reuses an existing observation surface where one exists (section 12
  reused `spawn.py`'s watch mechanism instead of inventing PR-merge
  detection); only invent new detection where no surface yet exists (issue
  reopened/closed — confirmed by the survey to have no existing detector).

## Performance axes this design competes on
- **Anti-theater strength** — can it be gamed by a role writing plausible
  but uncited prose? issue-476's answer (mechanized re-execution) doesn't
  transfer directly (no command to re-run for a narrative); the adapted
  floor is *citation resolvability*, checked the same way `record-claim-guard.sh`
  already checks backtick-quoted paths against the working tree.
- **Non-duplication of section 12** — coarser cadence (per transition, not
  per event) must be structurally enforced (trigger taxonomy), not left to
  the writer's judgment.
- **Empty-state honesty** — first-transition-on-a-new-issue case must be a
  named branch in the writer logic, not an omission that silently produces
  a fabricated "prior cost" claim.

## Adopt / skip
- **Adopt**: the writer-is-a-gate pattern wholesale, as sections 11 and 12
  establish it — same hook family, same transport, same "generated from
  record fields, not re-composed" rule.
- **Skip**: inventing a wholly new detection channel for PR-merge — section 12
  already solved that; #597 only needs to add reopened/closed detection on
  the `PreToolUse`/`Bash` vantage point `delegated-judgment-gate.sh` already
  occupies.

## Gap line
The field (this plugin's own prior art) already meets: writer-is-a-gate,
`gh --body-file -` transport, repo-native citation convention, PR-merge
detection reuse. It is missing: (a) any structured four-element comment
schema (issue-320's hook is a free-text regex checker, not a schema-and-writer
pair), (b) any issue-reopened/closed detection, (c) any mechanism enforcing
that a cited path actually exists (the closest analog, `record-claim-guard.sh`'s
backtick-path check, exists but is scoped to role Write/Edit content, not to
gate-generated comment bodies).

## Process note
Single sweep pass against internal prior art only — no external web search
angle applies to an internal gate-design decision. Saturation reached: the
survey plus this pass already surface every reusable pattern and every gap;
a further round would not change the proposal's build decisions.

Sources: docs/issue-573/proposals/architecture.md, docs/issue-320/proposals/2026-08-07-semantic-effect-reporting.md, docs/issue-476 (via docs/issue-573/reports/product-discovery/current-state.md), on-the-record/hooks/hooks.json, on-the-record/hooks/delegated-judgment-gate.sh, on-the-record/hooks/report-framing-check.sh, on-the-record/hooks/record-claim-guard.sh
