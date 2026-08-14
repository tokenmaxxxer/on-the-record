---
kind: survey
loop_state: drafted
---

## What was done

Current-state survey ahead of conformance review for issue #1112
("consult pipeline regression: '판단 JSON 을 못 찾음' recurring after
#1097 fix").

canonical: gh issue view 1112 (this turn) — issue is CLOSED; body cites
northpole req#3 (real-wired verification): "consult is the
validity-check wiring for issue drafting; when it silently degrades,
issues get drafted without the #1024 validity consult."

canonical: git log --all --oneline | grep 1112 (this turn) — the
implementation branch merged twice: PR #1116 (bff77c18, phase-1
proposal) and PR #1119 (be8cf825 fix commit, 9d72954a phase-2 record),
merge commit 1efcee83.

canonical: git branch --contains 1efcee83 (this turn) — result includes
`remotes/origin/HEAD -> origin/main`, confirming be8cf825 is on main.

code_under_review:
- spawn.py
- gates/test_consult_json_parse.py

canonical: docs/issue-1112/reports/implementation.md (read this turn) —
the phase-2 implementation record states: `role_settings()` gains
`inject_self_hosted_hooks: bool = True`; `consult_cmd()` (spawn.py:4378)
and `_run_panel_session()` (spawn.py:4514) supply
`inject_self_hosted_hooks=False`; `spawn_cmd()` call sites (spawn.py:4987,
spawn.py:5631) keep the default `True`. A new regression test file
`gates/test_consult_json_parse.py` is added. A live smoke was recorded
appended to `docs/reports/consult-log.md`, committed in the same commit
be8cf825.

canonical: git show be8cf825 -- spawn.py (this turn) — verbatim diff
confirms the described `role_settings()` signature change and the two
opt-out call sites; `spawn_cmd()`'s calls are untouched by the diff.

canonical: git show be8cf825 -- gates/test_consult_json_parse.py (this
turn) — verbatim file content confirms three tests:
`t_both_attempts_exhausted_raises_with_reported_symptom` (reproduces the
exact reported failure symptom string and asserts exactly 2 attempts
including the retry), `t_consult_cmd_settings_never_carry_self_hosted_hooks`,
`t_run_panel_session_settings_never_carry_self_hosted_hooks`.

canonical: find docs/issue-1112 -iname '*conformance*' (this turn) —
empty result before this session's writes: this session is the first
one that has written any conformance-review material for this subject.

## Scout skip record

Skipped. Reason: requirement extraction here is a mechanical
enumeration of the issue's own stated Problem/Acceptance text (which
this role never authors), per the issue text itself (canonical: gh
issue view 1112, this turn) — no product-shaped or comparable-system
design question needs research to enumerate that text.

## Why

Board condition (issue-521 conformance-review spec): an implementation
commit landed on the branch, and prior to this session no
conformance-review record existed for that commit sha (see canonical
citations above) — this session exists to close that gap.

## Upstream

Based on: #1112 (issue text), docs/issue-1112/reports/implementation.md,
commit be8cf825cc3b3cd2a5beee9e26d0eea51cc66b61.

## Open findings

None.
