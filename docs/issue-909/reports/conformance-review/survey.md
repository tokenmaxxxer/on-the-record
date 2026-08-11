Subject: issue-909

# Capability inventory — survey (phase 1, step 1)

Scope: every hook/gate script under on-the-record/hooks/ and
on-the-record/gates/, every skill/command under on-the-record/commands/
and on-the-record/monitors/, cross-checked against
on-the-record/hooks/hooks.json, on-the-record/monitors/monitors.json,
and docs/handbooks/, docs/specs/.

Scout skip: no design decision open — this is a pure enumerate-and-diff
sweep against an existing spec (contract v3 s19 rigor floor + skip
condition 2), so scout-directive did not run. Skip reason recorded per
directive.

## Method

canonical: derived: `find on-the-record/hooks on-the-record/gates -type f | sort` (executed this session)
canonical: derived: `grep -oP '\$\{CLAUDE_PLUGIN_ROOT\}/hooks/\K[a-z0-9_-]+\.sh' on-the-record/hooks/hooks.json | sort -u` (executed this session)
canonical: derived: `grep -oP '`[a-z][a-z0-9_-]*\.(sh|py)`' docs/specs/enforcement-boundary.md | sort -u` (executed this session)

registered set (34 entries) diffed against the on-disk .sh set and
against the doc-claimed set; every name present in one set but not
another was grepped across the full tree for any other invocation site
(source, CLI call, monitors.json row).

## Inventory table

| capability | implemented | registered/wired | documented | doc-accurate | reachable |
|---|---|---|---|---|---|
| 34 hooks.json rows (self-update, session-role-bind, directive, record-claim-shape-directive, record-tiering-directive, retry-loop-bound, deliverable-guard, contract-guard, pr-preflight, test-authoring-invariant-guard, delegation-post-gate, claim-scan-preflight, spec-index-preflight, role-axis-completeness-guard, gate-registration-guard, impact-guard, plan-order-guard, delegated-judgment-gate, merge-allow-gate, spawn-allow-gate, gh-write-allow-gate, credential-network-guard, record-claim-guard, credential-record-guard, record-tiering-guard, role-spec-reference-guard, call-shape-guard, accumulation-claim-guard, approval-gate, stop-poll-rearm, stop-gate, role-test-claim-guard, decision-queue-stopgate, report-framing-check, product-capture-stopgate) | Y | Y | Y (enforcement-boundary.md rows) | Y, spot-checked | Y |
| on-the-record/hooks/poll-rearm.sh | Y | not a hooks.json row — shared library, sourced by stop-poll-rearm.sh and directive.sh | Y (own header) | Y | Y, via its two registered callers |
| on-the-record/hooks/record-scaffold.sh | Y | not a hooks.json row by explicit design (CLI-invoked, no lifecycle event to hang off) | Y, docs/handbooks/record-authoring.md gives the CLI invocation | Y | Y — CLI-invoked, `record-scaffold.sh <role> <issue-n>` |
| on-the-record/gates/gates.py | Y | imported by accumulation-claim-guard.sh, call-shape-guard.sh, record-claim-guard.sh, pr-preflight.sh (all registered) | Y | Y | Y |
| on-the-record/gates/record_lint.py | Y | imported by record-claim-guard.sh and spec-index-preflight.sh (both registered) | Y | Y | Y |
| on-the-record/gates/role_spec_shape.py | Y | imported by role-spec-reference-guard.sh and role-axis-completeness-guard.sh (both registered) | Y | Y | Y |
| on-the-record/monitors/poll-heartbeat.sh | Y | monitors.json row, "when": "always" | Y | Y | Y |
| on-the-record/commands/consult.md (/consult) | Y | directory-convention discovery | Y, referenced from spawn-allow-gate.sh/directive.sh and multiple issue records | Y | Y |
| on-the-record/commands/run.md (/run) | Y | directory-convention discovery | Y, docs/handbooks/operations.md cites its acceptance procedure | Y | Y |
| on-the-record/hooks/absorbed-branch-recut-guard.sh | Y (103 lines) | N | Y, and the doc text asserts it IS wired (see finding below) | N | N |

## Finding: absorbed-branch-recut-guard.sh is an orphan (implemented-but-unwired + stale-doc)

canonical: derived: full-file read of on-the-record/hooks/hooks.json (93 lines) this session — no `absorbed-branch-recut-guard` line anywhere in the PreToolUse/Bash matcher block or any other block.
The script exists at on-the-record/hooks/absorbed-branch-recut-guard.sh (103 lines) but has no entry in hooks.json, so it never fires in an installed session.

canonical: docs/specs/enforcement-boundary.md line 76, read this session: "`absorbed-branch-recut-guard.sh` | contract | new (#784): `PreToolUse`+`Bash`, intercepts `git commit`/`gh pr create` and ... Ships with the plugin".
This line asserts the hook is a live PreToolUse/Bash trigger shipped with the plugin. That assertion is false against the current hooks.json content read above — the doc is stale.

canonical: docs/issue-784/reports/implementation.md line 39, read this session: "Added `on-the-record/hooks/absorbed-branch-recut-guard.sh`, a" [PreToolUse hook implementing the recut].
Same stale claim repeated in the implementation record for issue #784.

canonical: derived: `grep -rn "absorbed-branch-recut-guard" --include='*.sh' --include='*.json' --include='*.py' .` (executed this session) — the only hits outside the script's own file, its own test file, and prose docs are a Korean-language comment in spawn.py and the doc lines cited above; no script or hook anywhere calls or sources it.
No invocation site exists anywhere in the tree. The capability is genuinely unreachable, not just undocumented in one place.

## Root-cause note (feeds step 3, not acted on here)

canonical: on-the-record/hooks/gate-registration-guard.sh lines 1-4, read this session: "PreToolUse (Bash): deny-before-effect gate on a newly-staged gate/hook module with no matching row in docs/specs/enforcement-boundary.md ... — issue #759."
The standing check that should have caught this orphan (gate-registration-guard.sh) verifies a new gate/hook module has a matching row in docs/specs/enforcement-boundary.md — it does not verify a matching row in hooks.json itself. absorbed-branch-recut-guard.sh has the enforcement-boundary.md row (cited above), which is exactly why it satisfied gate-registration-guard.sh while never being registered in hooks.json. The doc-registration check and the actual-wiring check are two different surfaces, and only the first is currently enforced — this is the mechanism gap step 3's standing check needs to close.

## Broken-reference scan (docs/handbooks + docs/specs cross-references into on-the-record/)

canonical: derived: for every file under docs/handbooks/ and docs/specs/ that references an on-the-record/(hooks|gates|commands|monitors)/*.{sh,py,md} path, resolved the referenced path against the working tree this session — zero broken references found.

## Orphans ranked by impact

canonical: see the canonical citations under "Finding: absorbed-branch-recut-guard.sh is an orphan" above (hooks.json full-file read, enforcement-boundary.md:76, implementation.md:39, grep with zero invocation sites).

1. on-the-record/hooks/absorbed-branch-recut-guard.sh — HIGH. A safety-relevant guard that recuts a mid-run session's branch when a concurrent orchestrator merge absorbs it out from under the session. Both the spec and the issue #784 implementation record assert it is live and shipped, but hooks.json has no entry for it, so it has never fired in any installed session. The gap it was built to close (docs/issue-784/proposals/absorbed-branch-mid-run-recut.md) is still open in practice while every downstream record believes it is closed.

canonical: derived: this session's full sweep results above (inventory table + method section) — every other on-disk hook/gate/monitor/command name traced to either a hooks.json/monitors.json row, an import/source call site, or an explicit documented CLI-only design.

No other orphan was found in this sweep. poll-rearm.sh and record-scaffold.sh are unregistered by explicit, documented design, not by accident, and every gate/monitor/command module traced to a live call site.

## What did not work

None.

## Open findings

- absorbed-branch-recut-guard.sh: implemented-but-unwired + stale-doc, HIGH impact — addressed_to: implementation (step 2 of issue #909), resolution path: add the missing hooks.json PreToolUse/Bash row (or explicitly retire the script and correct the two stale doc claims), tracked at docs/issue-909/reports/conformance-review/survey.md.

kind: survey
loop_state: report-open
next steps: implementation (step 2) wires or retires absorbed-branch-recut-guard.sh per this finding; then step 3 adds a standing check that diffs hooks.json registration against enforcement-boundary.md rows so this orphan class cannot re-accumulate silently.
