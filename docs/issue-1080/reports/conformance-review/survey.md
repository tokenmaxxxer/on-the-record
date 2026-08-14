Subject: issue-1080

canonical: git log --oneline origin/issue-1080/implementation, read direct
## Current state (as of this survey)

`derived: git log --oneline origin/issue-1080/implementation -3`
```
bd407dfb issue-1080 phase-2: requirement_drift infra-tag exception
666f61f8 issue-1080 phase-1: after-proposal warrant hunt record
d5a46d6c issue-1080 phase-1: proposal for requirement_drift infra-tag exception
```

Target commit for this review: `bd407dfb` on `origin/issue-1080/implementation`.
canonical: find docs/issue-1080 -type f, read direct on this working tree (branch issue-1080/conformance-review, clean checkout)
No conformance-review record file exists yet for this subject on this branch
or on `origin/main` — board condition (issue-521) is met.

`derived: git diff $(git merge-base origin/main origin/issue-1080/implementation) origin/issue-1080/implementation -- spawn.py gates/requirement_linkage.py gates/test_requirement_drift.py --stat`
```
 gates/test_requirement_drift.py | 84 ++++++++++++++++++++++++++++++++++++++++
 spawn.py                        | 15 +++++++
 2 files changed, 99 insertions(+)
```

## Requirement extraction (from issue #1080 body)

Issue #1080 states a Problem, a Fix, and three Acceptance lines. These
decompose into four discrete, checkable requirements:

- R1 (Fix): `spawn.py::requirement_drift`'s `unreferenced_open` loop must
  skip items whose title/body contain the literal `_INFRA_TAG` value used
  by `gates/requirement_linkage.py` (`"infrastructure/no-direct-requirement"`)
  — same literal, not a re-declared copy, so the two checks cannot drift
  apart again.
- R2 (Acceptance: check): a unit test in `gates/` (or the module's chosen
  test home) demonstrates that an open item carrying
  `infrastructure/no-direct-requirement` is excluded from
  `unreferenced_open`.
- R3 (Acceptance: empty state): when no open item carries the infra tag,
  drift output is unchanged from prior (untagged) behavior — i.e. normal
  flagging of unreferenced items still fires.
- R4 (Acceptance: provenance): the fix is based on reading
  `spawn.py::requirement_drift` against `gates/requirement_linkage.py`,
  not invented independently.

No sampling derivation is needed — the issue names a single fix in a
single function with three enumerated acceptance lines; all four
requirements are reviewable directly against the diff.

canonical: git show origin/issue-1080/implementation:spawn.py, read direct
## What was found (read-only, informational — not a verdict)

`derived: git show origin/issue-1080/implementation:spawn.py | sed -n '2517,2540p'`
```
    sys.path.insert(0, str((root / "gates").resolve()))
    try:
        import requirement_linkage as _requirement_linkage
        infra_tag = _requirement_linkage._INFRA_TAG
    except ImportError:
        infra_tag = None
    ...
        if infra_tag is not None and infra_tag in text:
            continue
```
`spawn.py` imports `_INFRA_TAG` directly from `gates/requirement_linkage.py`
rather than restating the literal — this satisfies R1's "same literal"
clause structurally (import, not duplication).

canonical: pytest run in a worktree checked out at bd407dfb, this turn
`derived: (cd /tmp/impl-check && python3 -m pytest gates/test_requirement_drift.py -q)`
```
...                                                                      [100%]
3 passed in 0.05s
```
Three tests exist: `test_infra_tagged_item_excluded_from_unreferenced_open`,
`test_untagged_item_still_flagged`, `test_empty_tagged_items_leaves_drift_output_unchanged`
— naming maps directly to R2/R3.

This is a straight bugfix with no open design decision (single function,
single literal reused via import, three enumerated acceptance lines) —
scout-directive skip applies: "spec literally leaves no design decision
open." No scout sweep was run for this reason.
