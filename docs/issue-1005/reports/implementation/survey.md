# Current-state survey — issue #1005 (secure-coding routing gap)

## Skip condition (scout-directive)

Pure bugfix: the fix is filling in a missing structured `trigger` block
using a pattern already established and machine-checked for 4 other
roles in this same file family — no new design decision, no new
predicate shape, no product/UX surface. Scouting an external field is
not applicable; the "field" here is this repo's own `roles/specs/*`
convention, surveyed below.

## What causes the gap

canonical: roles/specs/secure-coding.spec.json (read directly)
```json
{
  "role": "secure-coding",
  ...
  "use_when": {
    "board_condition": "authentication or input-handling code landed on the branch AND no secure-coding record exists yet for that commit sha"
  }
}
```
secure-coding's spec carries `use_when.board_condition` as prose only —
no `use_when.trigger` key.

canonical: gates/roles_due.py lines 40-53 (read directly)
```python
trigger = (spec.get("use_when") or {}).get("trigger")
if isinstance(trigger, dict) and trigger:
    out[spec.get("role") or p.stem] = spec
```
`load_triggered_specs` only picks up specs whose `use_when.trigger` is a
non-empty dict. Since secure-coding has no `trigger`, it is never
included in this function's output, so `roles_due()` can never surface
it — structurally unreachable regardless of what lands on any branch.

canonical: docs/issue-993/proposals/product-discovery.md, "Utilization table" row for secure-coding (merged #1004, read directly)
This phase-1 proposal's own audit reached the same diagnosis: "board_condition text exists, matching commits exist, 0 records exist."

## The established pattern (what already works)

derived:
```
$ grep -l '"trigger"' roles/specs/*.spec.json
roles/specs/accessibility.spec.json
roles/specs/conformance-review.spec.json
roles/specs/execution-observation.spec.json
roles/specs/interaction-design.spec.json
roles/specs/security-threat-model.spec.json
```
canonical: roles/specs/security-threat-model.spec.json (read directly)
security-threat-model is the closest sibling — also security-adjacent,
also has prose board_condition text about authentication/trust-boundary
surfaces, and already carries a working `trigger`:
```json
"trigger": {
  "path_patterns": ["**/auth/**", "**/*permission*", "**/*credential*", "**/*secret*"],
  "content_patterns": ["trust boundary", "authentication", "bypassPermissions", "sudo"],
  "record_absent_for": "security-threat-model"
}
```
canonical: gates/test_roles_due.py (read directly)
`test_roles_due.py` unit-tests the generic mechanism (path match,
content match, record-already-exists suppression, no-match empty case)
against scratch git repos — the mechanism itself is already covered;
what is missing is only secure-coding's own spec entry.

## Write set (frozen)

- roles/specs/secure-coding.spec.json — add `use_when.trigger`
  (path_patterns + content_patterns + `record_absent_for:
  "secure-coding"`), mirroring `board_condition`'s stated scope
  (authentication AND input-handling — wider than
  security-threat-model's auth/trust-boundary-only scope).
- gates/test_secure_coding_routing.py — new live-fire test proving the
  real spec fires on a seeded security-relevant diff and not on a
  seeded unrelated diff (issue's own acceptance requirement).
- docs/issue-1005/reports/implementation.md — phase-2 record (written
  once phase-2 opens).
- docs/issue-1005/proposals/secure-coding-routing-fix.md — this
  proposal, to be written next in this same turn.
- (this file) docs/issue-1005/reports/implementation/survey.md.

No gate/hook code changes needed: canonical: gates/roles_due.py (read
directly) `roles_due()` already generalizes over any spec carrying a
`trigger` — adding the key is the entire spec-side fix.

## Live-fire test plan

canonical: gates/test_roles_due.py (read directly) — the existing suite
already proves the generic mechanism holds for an arbitrary role+trigger
pair using scratch repos (case 2: matching path + no record -> due;
case 1: no match -> empty). The acceptance requirement in issue #1005
asks for proof against secure-coding's own real spec, not the generic
mechanism, so phase 2 adds a new small test
(gates/test_secure_coding_routing.py) that builds a scratch repo, loads
the real `roles/specs/secure-coding.spec.json` from this repo (not a
synthetic spec), seeds one branch with a security-relevant diff and
another with an unrelated diff, and asserts `roles_due()` surfaces
secure-coding for the former only.

## Alternative considered

Rewrite `board_condition` prose itself instead of adding a `trigger`.
Rejected: canonical: docs/issue-993/proposals/product-discovery.md (read
directly) already confirms the prose text is fine ("condition text
exists, matching commits exist") — the gap is purely mechanical (missing
structured predicate), not a wrong condition, so rewriting the prose
would not fix reachability.
