---
proposal: docs/issue-2156/proposals/conformance-review.md
---

# Hunt record — conformance-review

## after-proposal — stance 0: assume the gate/rule just touched is bypassable — find the bypass.

Verdict: FINDING — the proposal's own stated success criterion for the
frontmatter `result` field (worst-case agreement with the 8 cited
verdicts) is unenforced anywhere: `result` is not a declared enum field
for this role, so a future phase-2 session can write any `result` value
regardless of the actual R1-R8 verdicts and no existing gate objects.
Kind: silent-failure
Seed: docs/issue-2156/proposals/conformance-review.md, docs/issue-2156/reports/conformance-review/survey.md
cap_seconds: 60
tier: default (size:docs-only <=20-line-equivalent)
diff_stat_lines: 2 new files under docs/ (proposal + survey)
started_at: 2026-08-24T15:05:00+09:00
ended_at: 2026-08-24T15:35:00+09:00

The proposal's "What will be" section for phase 2 states:

> ... `result` recomputed as the worst-case across the 8 cited verdicts.

and its closing section states:

> ... the frontmatter `result` field matches the worst-case of those 8
> verdicts.

canonical: `grep -n '"recomputation"' -A9 roles/specs/conformance-review.spec.json`
(executed this session) — the spec's own `recomputation.checked_by`
field reads `"TBD (follow-up — issue-521 out-of-scope note: per-role
recomputation enforcement is a follow-up once evidence from real usage
shows which roles need it)"` — i.e. this exact cross-check is admitted,
in the spec phase 2 will fill the record against, to not exist yet.

canonical: `python3 -c "import json; cfg=json.load(open('roles/conformance-review.json')); print(list(cfg.get('record_fields', {}).keys()))"`
(executed this session) — output: `['loop_state']`. `result` is absent
from this role's `record_fields` declaration.

canonical: `grep -n "선언되지 않은 필드는 검사하지 않는다" -A1 on-the-record/gates/gates.py`
(executed this session, `record_enums()` docstring) — "undeclared
fields are not checked (they remain free text)".

canonical: `grep -rln "recomputation\|worst-case\|worst_case" on-the-record/gates/ on-the-record/hooks/`
(executed this session) — the only hit is `on-the-record/gates/role_spec_shape.py`,
which only checks that `roles/specs/*.spec.json` has a `recomputation`
*key* present (a shape check on the spec file itself), never that a
filled review record's `result` value agrees with the worst case of its
own cited per-requirement verdicts.

### Reproduce

```
$ grep -n '"recomputation"' -A9 roles/specs/conformance-review.spec.json
  "recomputation": {
    "rule": "overall verdict = the worst-case result across all cited
    test entries (failed > cantTell > inapplicable > untested >
    passed), never a standalone summary field asserted independently
    of the cited results (issue-515 invariant 4).",
    "checked_by": "TBD (follow-up — issue-521 out-of-scope note:
    per-role recomputation enforcement is a follow-up once evidence
    from real usage shows which roles need it)"
  },

$ python3 -c "import json; cfg=json.load(open('roles/conformance-review.json')); print(list(cfg.get('record_fields', {}).keys()))"
['loop_state']

$ grep -rln "recomputation\|worst-case\|worst_case" on-the-record/gates/ on-the-record/hooks/
on-the-record/gates/role_spec_shape.py
```

### Observed

`record_enums()` (`on-the-record/gates/gates.py`), the write-time enum
enforcer for role records, reads its allow-list from `roles/<role>.json`'s
`record_fields`, not from `roles/specs/<role>.spec.json`.
`roles/conformance-review.json` declares only `loop_state` there, so per
the gate's own stated behavior `result` is free text at write time: no
membership check against the EARL 5-value enum, and — since a
static-list membership check is the only kind of thing this gate
performs — no cross-field check that `result` agrees with the worst
case of the 8 `verdict:` entries in the requirement blocks below it,
either. Nothing else under `gates/` or `hooks/` names
`recomputation`/`worst-case` against an already-filled record.

### Expected

Either `result` should be a declared, enum-checked field for this role
with an actual recomputation check against its own cited verdicts
(closing the `checked_by: TBD` gap the spec names), or the proposal's
closing section should not present worst-case `result` agreement as a
verifiable outcome, since as things stand a phase-2 session satisfies it
by construction — nothing in this repository can currently contradict
it.
