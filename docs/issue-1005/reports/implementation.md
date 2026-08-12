---
code_under_review:
  - roles/specs/secure-coding.spec.json
  - gates/test_secure_coding_routing.py
type: fix
breaking: false
# canonical: python3 gates/test_secure_coding_routing.py && python3 gates/test_roles_due.py — result: both PASS, run live this session (full output pasted below under "Test output")
verdict: pass
loop_state: landed
---

# Implementation record — issue #1005, secure-coding routing-gap fix

## What was done

Added `use_when.trigger` to `roles/specs/secure-coding.spec.json`, mirroring
`roles/specs/security-threat-model.spec.json`'s already-working shape:
`path_patterns` covering auth/credential/permission/secret/password/login
and input/sanitize/validate surfaces, `content_patterns` for
`authenticate`/`password`/`credential`/`sanitize`/`validate input`, and
`record_absent_for: "secure-coding"`. `gates/roles_due.py`'s
`load_triggered_specs` reads this key with no gate code change required.

Added `gates/test_secure_coding_routing.py`: builds a scratch git repo the
same way `gates/test_roles_due.py` does, installs the *real*
`roles/specs/secure-coding.spec.json` from this working tree (read from
disk, not a synthetic fixture) into the scratch repo's base commit, then
runs `roles_due.roles_due()` against two seeded diffs — a security-relevant
one (`auth/login.py` containing `authenticate(password)`) and an unrelated
one (`widget.py`).

## Why
canonical: docs/issue-1005/reports/implementation/survey.md, section
"What causes the gap" (file read this session).
Basis: #993 phase-1 audit (docs/issue-993/proposals/product-discovery.md,
merged #1004) found secure-coding's `board_condition` never fires under
real orchestration because `roles_due.py`'s evaluator only reads
`use_when.trigger`, which secure-coding's spec lacked — the prose was
accurate but mechanically unreachable. Approved per phase-1 proposal PR
#1079 (docs/issue-1005/proposals/secure-coding-routing-fix.md).

## Upstream
canonical: `gh pr view 1079` run this session — output showed
`state: MERGED`, body "Part of #1005."
Based on: docs/issue-1005/proposals/secure-coding-routing-fix.md (merged
PR #1079), docs/issue-1005/reports/implementation/survey.md.

## What did not work

None.

## Test output

derived: `python3 gates/test_secure_coding_routing.py`
```
PASS: seeded security-relevant diff -> secure-coding is due
PASS: seeded unrelated diff -> secure-coding is not due
```

derived: `python3 gates/test_roles_due.py`
```
PASS: no trigger fires -> empty due list
PASS: matching path with no record -> due
PASS: matching path but record already exists -> not due
PASS: content pattern match fires
PASS: format_report renders one line per due role, empty list -> no lines
```

Both commands run live this session, output pasted verbatim above.

## Open findings
canonical: docs/issue-1005/reports/implementation/2026-08-12-hunt-secure-coding-routing-fix.md
(file read this session) — after-proposal hunt found nothing blocking.
Before-landing hunt dispatched separately this session (see reply); its
outcome is reported there, not restated here.
