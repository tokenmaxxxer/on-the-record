# Issue #587 — architecture phase-1 current-state survey

## What already exists (verified by reading, not assumed)

- `on-the-record/hooks/delegated-judgment-gate.sh` (around lines 330-399) already writes
  `docs/issue-<n>/decisions/remediation-<seq>.md` on a `reject` verdict with a routable `finding`
  (#573 §6/§7). Fields: `finding_source`, `routed_to`, `target_path`, `required_fix`,
  `contradicting_role`, `round`, `status` (`open`|`resolved`|`escalated`), `timestamp`.
- Round counting and escalation are **already machine-managed from existing records**, not a gap:
  `round_n = len(chain) + 1` where `chain` is every prior `remediation-*.md` still routing the same
  `target_path`; escalation (`status: escalated`) fires on `round_n > 3` OR `routed_to is None` OR
  `repeat_contradiction` (same contradicting role + target_path + required_fix as a prior round).
  No new state store is needed for this half of #587 — it is already read/written against
  `docs/issue-<n>/decisions/remediation-*.md` alone.
- The gate posts a PR comment and an issue comment on routing — two of the five #573 §12 timeline
  events (`Verdict synthesized`, `Remediation routed`) are already firing from the gate. `PR opened
  under judgment` and `Escalation to operator` are specified in #573 §12 but not confirmed wired in
  this pass; `Remediation PR merged` is documented (§12) as reusing `spawn.py watch`'s existing
  session-end detection, not a new channel.
- `spawn.py`'s CLI already accepts `<role> <task> --issue <n> -C <repo> [--unattended]` and creates
  an `issue-<n>/<role>` branch with the task text embedded in the session prompt (per
  `on-the-record/commands/run.md`). This is the only spawn primitive that exists; there is no
  `remediation`-specific subcommand today.
- `roles/*.json`'s `write_scope` is the sole routing lookup, already reused three times (§1 axis
  ownership, §7 remediation routing, §9 panel eligibility) — `role_scope()` in
  `on-the-record/hooks/delegated-judgment-gate.sh` is the canonical resolver.

## The actual gap (what #587 is asking for)

1. Nothing reads `status: open` `remediation-*.md` records and turns them into a spawn
   invocation. Today a human (the orchestrator, per `on-the-record/commands/run.md`) reads the
   routing PR/issue comment and manually decides to run `spawn.py <role> "<task I write>"`. The
   task text is orchestrator-authored prose, not derived from `required_fix`/`finding_source`
   verbatim — this is the "manual judgment" the issue names.
2. `on-the-record/commands/run.md` has no step instructing the orchestrator loop to launch a
   remediation spawn task mechanically rather than re-deriving routing from the PR/issue comments
   it reads.
3. No e2e test exercises a full judged-PR → rejection → remediation-routed → remediation PR →
   re-judgment → closure cycle against a disposable fixture target repo. `test_spawn.py` and
   `on-the-record/hooks/test_delegated_judgment_gate.py` test components in isolation.
4. No idempotency check prevents re-spawning the same remediation round twice if the orchestrator
   loop runs `spawn.py` again before the first remediation session reports.

## Skip record — external scouting

This is an internal orchestration mechanism extending this repo's own established conventions
(write-by-hook audit records, zero-install CLI, `write_scope`-as-router) with no external product
category to compare against — the "field" to scout is this repo's own prior art, which the survey
above already reads directly (#573's implementation and its own architecture proposal, which this
step composes with rather than duplicates). Per scout-directive, skipping the external sweep;
reason: no comparable external product exists for a first-party judgment-loop orchestrator.
