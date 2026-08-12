# Warrant hunt — issue-1017 requirement-linkage-anchor proposal

proposal: docs/issue-1017/proposals/2026-08-12-requirement-linkage-anchor.md

## after-proposal, stance 4 (write set cannot carry the work)

FINDING: `gates/pr_reference.py` is a second real call site of
`acceptance_gate.check_issue_body` (PR-close time, reached from
`gates/ci.py`'s `--closes-only` path), not just `spawn.py`'s
`require_acceptance_gate`. The proposal's write set only wires the new
`requirement_linkage` check into the `spawn.py` draft-time path.

derived: `grep -n "acceptance_gate" gates/pr_reference.py`
```
20:import acceptance_gate
106:    bad = acceptance_gate.check_issue_body(issue, issue_body)
```

Disposition: not a scope gap for this proposal as written. Issue #1017's
ask is a draft-time backstop ("checked by acceptance_gate-style
backstop" for NEW issues at drafting) plus spawn-task passthrough and a
digest next-action line — it does not ask for a PR-close-time CI gate
the way `acceptance_gate` itself carries. The proposal's `## Out of
scope` already excludes changing `acceptance_gate.py`; a CI-close-time
enforcement point for `requirement_linkage` was not part of the request
and is left for a future issue if wanted, rather than silently folded
into this write set. Noted here so the omission is a stated choice, not
an unexamined gap.

## before-landing — stance 1: assume this change and another plugin's/gate's rule cancel each other — find the pair

Verdict: FINDING — `require_requirement_linkage` hard-blocks spawning any phase-1 (pre-approval) session on a freshly-opened issue whose body doesn't yet cite a requirement ID, with no CLI override — including the very phase-1 discovery/proposal-authoring session whose job is to determine and write that citation, creating a chicken-and-egg refusal that other gates (`require_board`, `require_no_repo_config`) avoid by exposing an `override` bool wired to a flag (`--no-contract`, `--trust-repo-config`).
Kind: composition
Seed: gates/requirement_linkage.py (new), spawn.py::require_requirement_linkage (line ~1020), spawn.py::main (line 4825)
cap_seconds: 120
tier: default
diff_stat_lines: 113
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:02:00Z

### Reproduce
```
python3 -c "
import sys
sys.path.insert(0,'gates')
import requirement_linkage as rl
body = 'We should add a new gate for X because it seems useful.'
print(rl.check_issue_body(1099, body))
"
```
Then, on any board repo, `python3 spawn.py --issue 1099 ... ` for a freshly-opened,
not-yet-approved issue (`_ci._approved_roles_on_issue` returns empty) whose body has
no `R\d+`/`northpole req#n` citation and no `infrastructure/no-direct-requirement`
tag hits `require_requirement_linkage` (spawn.py:1020, called unconditionally at
spawn.py:4825, no override parameter/flag unlike `require_board`'s `override` or
`require_no_repo_config`'s `override`) and `sys.exit`s before any session — including
a phase-1 proposal-authoring session — is spawned.

### Observed
`check_issue_body` returns a non-empty violation list for the ordinary case of a
newly-opened issue with a plain-English description and no requirement citation yet;
`require_requirement_linkage` turns that into `sys.exit(...)`, refusing to spawn.

### Expected
The phase-1 proposal-authoring flow (which itself is what determines and records the
requirement linkage, per the warrant-directive's own two-phase design: propose first,
then implement) must be able to run before a citation exists in the issue body. As
written, no code path can ever add the citation via `spawn.py`, because the gate that
demands the citation fires on every pre-approval spawn with no override, including the
first one.
