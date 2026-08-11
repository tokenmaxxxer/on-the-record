---
code_under_review:
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/gate-registration-guard.sh
  - on-the-record/hooks/test_gate_registration_guard.py
  - docs/specs/enforcement-boundary.md
type: feature
breaking: false
canonical: python3 -m pytest gates/ on-the-record/hooks/ -q
verdict: pass
loop_state: landed
---

Subject: issue-909

# issue-909 implementation record (step 2 + step 3)

## Why

A capability that exists in the tree but can never fire is the same as
one that does not exist (issue #909's own framing).
canonical: docs/issue-909/reports/conformance-review/survey.md lines
42-59, read this session.
This step wires the one orphan the phase-1 survey found and generalizes
the standing check so the same doc-row-without-wiring gap cannot land
again unnoticed.

## What was done

canonical: docs/issue-909/reports/conformance-review/survey.md lines
42-59, read this session (phase-1 inventory, merged as #911).
The survey found exactly one orphan —
`on-the-record/hooks/absorbed-branch-recut-guard.sh`: implemented (103
lines), documented at docs/specs/enforcement-boundary.md:76 and
docs/issue-784/reports/implementation.md:39 as a live `PreToolUse`+`Bash`
hook shipped with the plugin, but absent from
`on-the-record/hooks/hooks.json` — never fires in an installed session.
The survey's root-cause note (same file, lines 56-59): the existing
`gate-registration-guard.sh` checks a newly-staged hook script against
`docs/specs/enforcement-boundary.md` row presence only, never against
`hooks.json` itself, so a doc row that falsely claims wiring currently
satisfies the guard.

1. **Wire vs. retire decision: WIRE.**
   `absorbed-branch-recut-guard.sh` is a safety-relevant guard (closes a
   gap #732's spawn-time-only recut leaves: a mid-run session's branch
   absorbed by a concurrent orchestrator merge, surfacing today as a
   silent "No commits between main and issue-<n>/<role>" at PR-create
   time — per the script's own header comment, on-the-record/hooks/absorbed-branch-recut-guard.sh
   lines 1-32, read this session). It is well-formed — fail-open on
   missing `spawn.py`/recut failure, never denies — and its doc row
   already describes exactly the wiring it needs. Retiring a working
   safety guard because it was never plugged in would re-open the #784
   gap it was built to close; wiring it makes the existing doc claims
   true instead of stale. Added to `on-the-record/hooks/hooks.json`'s
   `PreToolUse`/`Bash` matcher group, ahead of `contract-guard.sh` (same
   interposition-point convention its own header comment already
   documents — before the matched `git commit`/`gh pr create` runs). No
   other doc edits were needed: docs/specs/enforcement-boundary.md:76 and
   docs/issue-784/reports/implementation.md:39 become accurate once the
   hooks.json row exists.

2. **Standing check (step 3).** Extended `gate-registration-guard.sh`
   (issue #759) rather than writing a new gate — same
   deny-before-effect/`PreToolUse`+`Bash` shape, same file it already
   inspects. For a newly-staged `on-the-record/hooks/*.sh` file, the
   guard now also reads `on-the-record/hooks/hooks.json` (staged-aware,
   via the existing `read_spec()` helper) and denies the commit when the
   script's `docs/specs/enforcement-boundary.md` row does not explicitly
   say it is not a live hook (`"not a hook itself"`, `` "not wired into
   `hooks.json`" ``, `"CLI-invoked"` — the exact phrasing
   `poll-rearm.sh`/`record-scaffold.sh` already use for their by-design
   exemption, docs/specs/enforcement-boundary.md lines 82-84 and 104,
   read this session) and the script's basename has no matching
   `hooks.json` command entry. Fails open when no `hooks.json` exists in
   the tree at all. `docs/specs/enforcement-boundary.md`'s own row for
   `gate-registration-guard.sh` was updated to describe the extension.

3. **Tests.** Added three cases to
   `on-the-record/hooks/test_gate_registration_guard.py`, covering: a new
   hook script with a "live hook" doc row and no `hooks.json` entry
   (reproduces the exact `absorbed-branch-recut-guard.sh` shape); the
   same script with a `hooks.json` entry in the same staged commit; a
   script whose doc row explicitly says it is not a hook. Outcomes for
   all three are in the acceptance run below.

## Acceptance check

canonical: python3 -m pytest on-the-record/hooks/test_gate_registration_guard.py gates/test_boundary.py gates/test_generated_paths.py gates/test_hooks_parity.py on-the-record/hooks/test_absorbed_branch_recut_guard.py -q (executed this session, pasted output below)
acceptance: `python3 -m pytest on-the-record/hooks/test_gate_registration_guard.py gates/test_boundary.py gates/test_generated_paths.py gates/test_hooks_parity.py on-the-record/hooks/test_absorbed_branch_recut_guard.py -q` — result: PASS (42 passed, 0 failed, 0 skipped).
```
$ python3 -m pytest on-the-record/hooks/test_gate_registration_guard.py gates/test_boundary.py gates/test_generated_paths.py gates/test_hooks_parity.py on-the-record/hooks/test_absorbed_branch_recut_guard.py -q
..........................................                               [100%]
42 passed in 2.05s
```
This targeted run covers the module changed (`gate-registration-guard.sh`
+ its own test file), the two modules its check ports logic from
(`test_boundary.py`, `test_generated_paths.py`), the hooks.json/spawn.py
registration-parity test (`test_hooks_parity.py`), and the wired hook's
own suite (`test_absorbed_branch_recut_guard.py`, unmodified by this
change).

canonical: docs/issue-909/reports/conformance-review/survey.md lines
61-63, read this session ("Broken-reference scan ... zero broken
references found").
The merged survey's broken-reference scan already found zero broken
docs/handbooks + docs/specs cross-references, so no doc-reference fixes
were needed beyond the one stale claim resolved by wiring the hook.

## What did not work

None.

## Open findings

canonical: docs/issue-909/reports/conformance-review/survey.md lines
79-81, read this session (the survey's one open finding).
None — resolved by wiring `absorbed-branch-recut-guard.sh` into
`hooks.json`, which also makes the two previously-stale doc claims
(docs/specs/enforcement-boundary.md:76,
docs/issue-784/reports/implementation.md:39) accurate again without
further edit.

loop_state: landed
