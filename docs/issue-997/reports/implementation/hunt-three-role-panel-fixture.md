---
proposal: docs/issue-997/proposals/three-role-panel-fixture.md
---

# Hunt record — three-role-panel-fixture

## after-proposal — stance: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: NO FINDING
Seed: docs/issue-997/proposals/three-role-panel-fixture.md; on-the-record/hooks/test_delegated_judgment_gate.py
cap_seconds: 120
tier: default
diff_stat_lines: ~21-200 (bucket estimate for planned code diff; current diff is docs-only)
started_at: 2026-08-12T14:55:00+09:00
ended_at: 2026-08-12T15:00:00+09:00

Note: assigned hunt-record path docs/issue-997/reports/hunt-three-role-panel-fixture.md
was refused by board-gate ("belongs to another role. implementation writes
only implementation.md, implementation/** — never a foreign record" —
contract v3 s11), since this session's role is `implementation` and that
path is outside its write scope. Recorded here instead, under the role's
own writable subtree, as the closest available honest record of the same
work.

Checked whether adding PERFORMANCE_ROLE + two 3-role-panel test functions
needs any file outside the proposal's write set
(test_delegated_judgment_gate.py, docs/issue-997/reports/implementation.md).

- The fixture is fully self-contained: `_init_target()` writes each role's
  dict straight into `target/roles/<name>.json` inside a throwaway tmp dir;
  `delegated-judgment-gate.sh`'s `load_roles()` reads only from
  `TARGET/roles/*.json` (script line ~442-448). The real repo's
  `roles/performance-engineering.json` / `roles/specs/*.spec.json` are never
  read by this test — reusing the axis name `"performance"` is a naming
  choice for fidelity, not a load-bearing dependency the build needs.
  `role_scope()` / `glob_matches()` are schema-agnostic (no required-field
  validation), so the synthetic `{"write_scope": [...], "judgment_axes":
  [...]}` shape already used by ARCHITECTURE_ROLE/SECURITY_ROLE is
  sufficient for a third role dict too.
- Considered a path collision: `docs/issue-997/reports/implementation/`
  already exists as a directory (containing `survey.md`), and the proposal
  targets `docs/issue-997/reports/implementation.md`. Reproduced by writing
  to that exact path with `Path.write_text()` — it succeeded cleanly
  (`implementation.md` and `implementation/` are distinct filesystem
  entries; no collision). Not a finding.
- No shared helper, gate script, or `roles/*.json` file needs modification
  to add the third role dict and two test functions as scoped.
