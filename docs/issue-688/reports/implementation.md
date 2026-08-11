---
code_under_review:
  - on-the-record/hooks/delegated-judgment-gate.sh
  - on-the-record/hooks/test_delegated_judgment_gate.py
  - on-the-record/hooks/test_delegated_judgment_gate_triage.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Implemented the approved proposal
(docs/issue-688/proposals/2026-08-11-delegated-judgment-corpus-path.md):

- `on-the-record/hooks/delegated-judgment-gate.sh`: `depth_match` now
  takes the branch-derived `issue` int as an argument and reads the
  issue-scoped product-doc corpus instead of the retired flat one. No
  second issue-number derivation was added — the call site passes the
  same `issue` variable already produced by the branch match (line 343)
  and already reused for `decisions_dir` (line 660). Empty/absent
  corpus at the new location still returns `False` unchanged (no new
  branch). Updated the docstring header (two spots) and the
  `derivation_source` audit-trail string to describe the issue-scoped
  corpus.
- `on-the-record/hooks/test_delegated_judgment_gate.py`: moved
  `_product_corpus`'s write target to the issue-scoped corpus directory
  matching the fixture's fixed `issue-42` branch, and added
  `t_no_retired_flat_product_path_in_the_hook_source`, asserting the
  script source no longer contains the retired flat corpus path string.
- `on-the-record/hooks/test_delegated_judgment_gate_triage.py` (added to
  the frozen write set by the after-proposal warrant hunt): moved its
  three retired-flat-corpus references to the issue-scoped corpus path,
  keyed by the module's `ISSUE` constant.

## Why

`delegated-judgment-gate.sh`'s depth axis read the retired flat
product-doc path; issue #684 moved the writer
(`product-capture-stopgate.sh`) to an issue-scoped location, so the
reader and writer disagreed and the depth axis silently evaluated
against nothing.

## Upstream

docs/issue-688/proposals/2026-08-11-delegated-judgment-corpus-path.md

## What did not work

None.

## Doctrine placement

No env var, config key, new dependency, migration, or public
signature/wire-format change — nothing to place on the doctrine ladder
beyond this record and the existing spec table
(docs/specs/generated-paths.md, unchanged per the proposal's Out of
scope).

## Open findings

None.

## Verification run

```
$ python3 on-the-record/hooks/test_delegated_judgment_gate.py
24 passed
$ python3 on-the-record/hooks/test_delegated_judgment_gate_triage.py
3 passed
$ python3 -m pytest on-the-record/hooks/ -q -k delegated_judgment
27 passed, 112 deselected in 3.05s
```
