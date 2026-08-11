---
code_under_review:
  - spawn.py
  - test_spawn.py
type: fix
breaking: false
verdict: pass
loop_state: committing
---

## What was done

Per the approved proposal
(docs/issue-732/proposals/absorbed-branch-untracked-recut.md): in
`checkout_issue_branch`'s `local_zero` branch (spawn.py), untracked
files are now carried across the fresh re-cut via `git stash push -u`
/ `git stash pop` instead of being left stuck on the absorbed branch.
A leftover stash from an interrupted prior run (recognizable by a
fixed marker message) is recovered first, before the re-cut, closing
the window where `clean`'s preservation guard could see a clean tree
while work was hidden in a stash (the after-proposal hunt finding
folded into the proposal). Added four regression tests to
test_spawn.py: absorbed+untracked-only (incl. a path colliding with
base's tree) re-cuts with files preserved; leftover-stash recovery;
committable-commits-ahead workspace stays byte-identical (no stash
used).

derived: `python3 -m pytest test_spawn.py -q`
```
397 passed in 32.29s
```

## Why

Fixes #732 — absorbed branch holding only untracked work deadlocks
respawn forever because `local_zero` re-cut collides with those
untracked paths and falls back to a no-op.

## Upstream / basis

docs/issue-732/proposals/absorbed-branch-untracked-recut.md

## What did not work

None.

## Rationale for deviations

None.

## Open findings

None.

## Resolution path

Not applicable — no open findings.

## Next steps

None — record will move to `landed` once committed and pushed.
