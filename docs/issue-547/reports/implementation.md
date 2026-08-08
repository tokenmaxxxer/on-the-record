---
code_under_review:
  - gates/accumulation.py
  - gates/test_accumulation.py
  - on-the-record/hooks/accumulation-claim-guard.sh
  - on-the-record/hooks/test_accumulation_claim_guard.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Applied the approved phase-1 proposal
(`docs/issue-547/proposals/2026-08-09-accumulation-claim-authoring-time.md`)
end to end, matching its "What will be done" section:

- `gates/accumulation.py`: added `check_accumulation_claim_for_files(work,
  files, body)` — a static-list entry point that reuses the existing
  `_touches_shape_1`/`_touches_shape_5` detectors against a plain path
  list instead of a `git diff`, so it can be called from proposal
  authoring time (no committed diff exists yet at that point).
- `gates/test_accumulation.py`: new unit tests for the new function —
  shape-5 path with/without the section, shape-1 existing-over-threshold
  path with/without the section, and a files list touching neither
  shape.
- `on-the-record/hooks/accumulation-claim-guard.sh`: added a branch that
  fires on `Write|Edit|MultiEdit` writes to
  `docs/issue-<n>/proposals/*.md`. For `Write` it reads `tool_input.content`
  directly; for `Edit`/`MultiEdit` it reconstructs the full resulting
  file by reading on-disk content and applying `old_string`/`new_string`
  (or each `edits[]` entry in order), per the proposal's design note —
  a fragment-only scan would miss a `files:` list edited incrementally.
  It parses `files:` and checks each listed path against the shape
  detectors, and requires a filled `## Accumulation` heading in the
  reconstructed body when either shape is touched. The pre-existing
  `.py`-write branch (phase-2 safety net) is unchanged in behavior; a
  shared `_touches_shape_1_py_write()` was factored out only to preserve
  its original "current write + whole tracked `.py` tree" scan after the
  new branch was inserted above it.
- `on-the-record/hooks/test_accumulation_claim_guard.py`: new tests —
  proposal `Write` naming `roles/x.json` with no `## Accumulation` denied,
  same write with the section filled allowed, a proposal naming only
  unrelated files never blocked, a non-proposal `.md` write (e.g. a
  report) ignored, and an incremental `Edit` appending a path to an
  already-open `files:` list still caught (regression test for the
  earlier warrant-hunt finding the proposal cites).

## Why

Issue #547: the accumulation-claim-guard only checked the field the
first time phase 2 edited an accumulation-shaped `.py` file, after the
proposal's write set was already frozen — the cost of a missing
`## Accumulation` section landed at the expensive point (mid-build,
per #533's two failed-no-commit attempts) instead of the cheap one
(proposal authoring). This delivery moves the check to proposal
authoring time per the approved proposal, without changing the
`.py`-write safety net that still covers cases the authoring-time check
can't see (a brand-new file, or a `files:` list that changes mid-build).

## Upstream / basis

`docs/issue-547/proposals/2026-08-09-accumulation-claim-authoring-time.md`
(approved via `APPROVE issue-547/implementation` issue comment,
single-account mode, from listed approver JiwonJung94).

## What did not work

None.

## Doc-placement ladder

- No new env var, config key, dependency, or migration introduced — no
  handbook update required.
- No changed public signature or wire format beyond the new
  `check_accumulation_claim_for_files` entry point, which is additive
  and already fully specified in the approved proposal's own "What will
  be done" — no separate decision record needed for it.
- No benchmark/investigation numbers produced.

## How it was confirmed

```
$ python3 gates/test_accumulation.py
ok - t_shape1_seventh_gh_call_without_accumulation_line_flags
ok - t_shape5_roles_json_touch_without_accumulation_line_flags
[... other ok lines ...]
12/12 passed
```

```
$ python3 -m pytest on-the-record/hooks/test_accumulation_claim_guard.py -q
...........                                                              [100%]
11 passed in 0.54s
```

derived: `python3 -m pytest -q` run twice — once on the clean pre-edit
worktree (836 passed, 1 pre-existing unrelated failure,
`test_gates.py::t_rulebook_version_is_recorded`, which asserts the
rulebook version string never contains "커밋안됨" and fails on any dirty
working tree, reproduced before this session's first edit) and once
after this change (846 passed, same single pre-existing failure, no new
failures).

## Open findings

None raised against this delivery.

## closed_checks

- check: unit test — proposal `.md` write missing `## Accumulation` for
  an accumulation-shaped `files:` scope is refused at write time
  (`t_proposal_write_naming_roles_json_without_accumulation_is_denied`,
  `on-the-record/hooks/test_accumulation_claim_guard.py`)
  code_sha: 3a5924f
- check: `python3 -m pytest` green in clean worktree (pre-existing
  failure only, confirmed present before this session's first edit)
  code_sha: 3a5924f
