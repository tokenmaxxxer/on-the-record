---
proposal: docs/issue-1005/proposals/secure-coding-routing-fix.md
---

# Hunt record — secure-coding-routing-fix

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: NO FINDING
Seed: docs/issue-1005/proposals/secure-coding-routing-fix.md, docs/issue-1005/reports/implementation/survey.md (commit 65d8b4b)
cap_seconds: 120
tier: default
diff_stat_lines: 202
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:05:00Z

Checked whether adding `use_when.trigger` to roles/specs/secure-coding.spec.json
requires touching gates/role_spec_shape.py or docs/specs/role-spec-template.schema.json
(neither is in the frozen write set), and whether anything else reads
secure-coding.spec.json in a way an extra key would break.

- docs/specs/role-spec-template.schema.json's `use_when` sub-schema has no
  `additionalProperties: false`, and the schema is never loaded/validated
  by any Python gate anyway (grep for the filename only turns up docstring
  references in gates/test_role_spec_shape_batch*.py comments, not a
  jsonschema.validate() call).
- gates/role_spec_shape.py's `check()` (the actual enforcement, hand-rolled,
  confirmed by its own docstring: "no jsonschema dependency") only requires
  `use_when.board_condition` to be a non-empty string; it never inspects
  `use_when.trigger` or rejects extra keys. security-threat-model.spec.json
  already carries `use_when.trigger` and passes this same checker today,
  confirming the checker is silent on the trigger key both ways.
- gates/roles_due.py's `load_triggered_specs()` explicitly documents that a
  spec without `trigger` is simply skipped and one with `trigger` is picked
  up — this is exactly the mechanism the proposal's phase-2 plan depends on,
  and it needs no schema/shape-gate changes to work.
- grep for "secure-coding" across gates/*.py found no other consumer of the
  spec file's shape (gates/role_spec_shape.py's `_VERIFICATION_FAMILY_ROLES`
  tuple and spawn.py's role roster both reference the role name, not
  `use_when`, and are unaffected by adding `trigger`).

The frozen 3-file write set (roles/specs/secure-coding.spec.json,
gates/test_secure_coding_routing.py, docs/issue-1005/reports/implementation.md)
is sufficient for the described phase-2 change; no additional file needs
touching to keep existing gates passing.

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass.

Verdict: FINDING — roles_due()'s `record_absent_for` check treats presence of ANY existing `docs/issue-<n>/reports/secure-coding.md` as "not due," so a stale/unrelated secure-coding record (e.g. from an earlier, already-closed review) permanently suppresses re-surfacing for genuinely new, later security-relevant diffs on the same issue branch — the trigger never fires again for that issue regardless of what new auth/credential code lands.
Kind: design-error
Seed: roles/specs/secure-coding.spec.json (use_when.trigger addition), gates/roles_due.py, gates/test_secure_coding_routing.py (uncommitted working-tree diff)
cap_seconds: 120
tier: default
diff_stat_lines: ~50 (spec: +19, new test file: +99)
started_at: 2026-08-12T16:14:16+09:00
ended_at: 2026-08-12T16:14:40+09:00

### Reproduce
```python
# /tmp/bypass_test.py — build scratch repo (as gates/test_secure_coding_routing.py does),
# but seed docs/issue-1/reports/secure-coding.md BEFORE committing the new auth change:
rd = repo / "docs" / "issue-1" / "reports"
rd.mkdir(parents=True)
(rd / "secure-coding.md").write_text("# secure-coding record\nverdict: pass (old, unrelated review)\n")
# ... commit init, checkout issue-1/implementation ...
(repo / "auth" / "login.py").write_text("def authenticate(password):\n    pass\n")
# commit "add new auth login logic"
due = roles_due.roles_due(repo, base="origin/main")
```
Run: `python3 /tmp/bypass_test.py`

### Observed
`due: []` — secure-coding is reported as not due, even though a brand-new `auth/login.py` with `authenticate(password)` just landed on the branch, because an old unrelated `secure-coding.md` record already exists for issue-1.

### Expected
A genuinely new security-relevant diff landing after a prior secure-coding record was written should re-surface the role as due (e.g. gated on record recency/commit-sha, per the spec's own `board_condition` text: "no secure-coding record exists yet for that commit sha" — but `record_absent_for` only checks file existence, never commit sha, so it can never match this condition as documented).
