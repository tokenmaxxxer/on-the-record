---
kind: current-state-survey
subject: issue-1098
code_under_review:
- gates/landing_obligation.py
- gates/landing_readiness.py
- on-the-record/hooks/post-landing-obligation-gate.sh
- on-the-record/hooks/hooks.json
- roles/specs/defect-verification.spec.json
- gates/roles_due.py
- spawn.py
---

# Current-state survey — conformance review of issue #1098's landed commit

## Background

canonical: `gh issue view 1098`, read this session — cites northpole
req#3 (real-wired verification) and req#5 (problems not pushed back to
the human, solved by spawning role agents) as the requirements this
issue answers.

canonical: docs/issue-1098/reports/implementation.md, read this session
— that record claims commit 7df3f55 (squash-merged as 1ce4a7ff) delivers
the post-landing obligation-tracking half of the loop, and defers the
actual refiling/spawn wiring to `roles_due.py`'s existing trigger
mechanism, naming that composition (not a new filer) out of this
proposal's own scope.

canonical: `git merge-base --is-ancestor 1ce4a7ff1649646ea0266bb0e325e32f2717e666 HEAD && echo on-main`, run this session — result:
```
on-main
```

## Requirement list extracted

1. **northpole req#3** — real-wired verification: a landing's
   correctness must be established by actually running the changed
   behavior, not by narration or code-reading alone.
   canonical: docs/specs/northpole.md, section "3. Real-wired
   verification", read this session.
2. **northpole req#5** — a discovered problem is not surfaced to the
   human for manual handling; it is resolved by autonomously spawning
   the role-appropriate agent(s), with the process transparently
   recorded.
   canonical: docs/specs/northpole.md, section "5. Problems are not
   pushed back to the human", read this session.

## Findings

### Req #3 — obligation resolution composes with real reexecution verdicts

canonical: gates/landing_obligation.py, function
`resolve_with_reexecution_verdict` (lines 84-104), read this session —
reads `.reexecution/<issue>-<role>.json`, a verdict file
`reexecution_gate.py` itself writes by re-running a claimed command in a
SHA-pinned worktree (not narration), and only resolves an obligation
when that verdict's `timestamp` post-dates the obligation's own
`opened_at`.

canonical: python3 -m pytest gates/test_landing_obligation.py gates/test_landing_readiness.py on-the-record/hooks/test_post_landing_obligation_gate.py -q — result: pass, 37 passed, executed live this session against current HEAD (includes commit 1ce4a7ff), matching the implementation record's own cited count:
```
37 passed in 0.46s
```

### Req #5 — obligation state exists; the autonomous-spawn half is split across two issues, and the spawn step itself stays advisory-only

canonical: docs/issue-1098/proposals/2026-08-12-post-landing-verify-refile-loop.md,
work item 4 (the refiling-composition item), read this session — that
item's own text scopes the `roles/specs/*.spec.json` trigger wiring for
loop step 2 as a separate follow-up, not this proposal's own write set.

canonical: `git log --oneline --all -- roles/specs/defect-verification.spec.json`, run this session — result:
```
a961deae issue-1102 phase-2: wire roles/specs obligation trigger (#1109)
fc47efe5 issue-1102 phase-2: wire roles/specs obligation trigger for defect-verification
869aada6 issue-807 step3: apply role-methodology strengthening plan to 6 specs (#935)
```
canonical: roles/specs/defect-verification.spec.json, `use_when.trigger`
block, read this session — the follow-up trigger wiring landed under
issue #1102 (PR #1109), a separate subject/branch/PR from issue-1098's
own commit:
```
"trigger": {
  "obligation_status": ["failing"],
  "record_absent_for": "defect-verification"
}
```

canonical: `git merge-base --is-ancestor a961deae HEAD && echo on-main`, run this session — result:
```
on-main
```
That trigger wiring is present in the current working tree via issue
#1102, not via issue-1098's own commit.

canonical: `grep -n 'roles.due 와 마찬가지로 advisory-only' spawn.py`, run this session — result, `spawn.py`'s own comment stating the `roles-due`-family evaluator never auto-spawns and instead produces advisory output a human or orchestrator must read and act on:
```
5565:        # roles-due 와 마찬가지로 advisory-only: 절대 자동 스폰하지 않는다.
```

canonical: `grep -rln "roles-due\|roles_due" on-the-record/hooks/*.sh`, run this session — result, no hook under `on-the-record/hooks/` invokes `roles-due`/`roles_due` automatically:
```
(no output)
```

Net for req#5, stated as fact rather than restated claim: an
obligation's `"failing"` status is now a board condition a role-spec
trigger can match (per the trigger block above), but the evaluator that
reads that condition (`gates/roles_due.py`, invoked via `spawn.py
roles-due`) is advisory-only by its own author's comment above, and no
hook calls it automatically. The chain from "obligation goes failing" to
"a role agent is actually spawned with no operator prompting" has an
open link at the spawn step itself — neither issue-1098's commit nor
issue #1102's follow-up wires that last call.

## What did not work

None.
