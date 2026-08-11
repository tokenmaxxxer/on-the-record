---
code_under_review:
  - spawn.py
type: docs
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Implemented the approved phase-1 proposal
(docs/issue-742/proposals/confirm-bypasspermissions-baseline.md) for
issue #742: corrected the comments in `spawn.py`'s `role_settings()`
around the `permissions.allow` construction block (spawn.py:492-533) so
they state the current, measured permission-judging layer instead of
the pre-#700 one. No allowlist expansion — the proposal's Acceptance-1
empty state ("no expansion target found → record the reasoning and a
0-denial baseline, then stop") is what this issue exercises, per the
issue's own APPROVE comment. No logic, test, or behavior change.

- `spawn.py`: inserted a new comment block, right before the
  `WebSearch`/`WebFetch`/`Read`/`Grep`/`Glob` paragraph (originally at
  line 492), stating that issue #700 (commit `b762681`, 2026-08-11
  10:38) moved the real role-spawn paths (`spawn_cmd()`/`consult_cmd()`)
  to `--permission-mode bypassPermissions`, that Anthropic's own docs
  ("Allow rules have no effect in bypassPermissions because everything
  else is already approved.") make this repo's `permissions.allow` list
  inert for those paths, and that `PreToolUse`/`PermissionRequest` hooks
  are now the layer that actually judges a tool call. The new block also
  states the two reasons the list is kept rather than deleted: (1)
  `role_settings()` is also called from the `--dry-run` path
  (`main()`'s `a.dry_run` branch, spawn.py:3883) which never spawns a
  `claude` process at all, so no permission-mode applies there and the
  printed `permissions.allow` is exactly what this function still
  builds; (2) if a role spawn is ever moved off `bypassPermissions`
  again, this list becomes the operative boundary again immediately.
  - Two adjoining sentences that stated the old mechanism in the present
    tense were corrected to past tense with an "(당시)" ("at the time")
    qualifier so they read as history, not current fact: the
    `WebSearch`/`WebFetch` paragraph's "`headless 세션은 --permission-mode
    acceptEdits 로 뜨고 답할 사람이 없어서 ... 그냥 거부된다`" (spawn.py,
    originally line 494-495), and the issue-#558 workspace-bash
    paragraph's matching sentence (spawn.py, originally line 509-510) —
    both were written when `permissions.allow` genuinely was the
    operative Bash gate (pre-#700) and both continued to assert that in
    the present tense.
  - `git diff spawn.py` touches only `#`-comment lines — confirmed below.

## Why

Issue #742's structural hypothesis (`permissions.allow` lacks a `Bash`
entry post-#695, causing the measured denial-retry loop) was falsified
by phase-1's live measurement: #700 already moved every real role-work
spawn to `bypassPermissions`, under which `permissions.allow` "has no
effect" per Anthropic's docs, and a four-pattern live probe in a real
role session reproduced zero denials. The remaining gap the survey
found is a documentation-accuracy one, not a functional one: the
comments explaining why `permissions.allow` entries exist still cited
the pre-#700 threat model (`acceptEdits` + no answering human) in the
present tense, which would mislead a future reader into treating
`permissions.allow` as the operative Bash boundary when it is not
(`PreToolUse`/`PermissionRequest` hooks are). This change fixes that
mismatch without touching behavior.

## Upstream

Based on: docs/issue-742/proposals/confirm-bypasspermissions-baseline.md,
docs/issue-742/reports/implementation/survey.md

## What did not work

None.

## Rationale for deviations

None — the change matched the approved proposal's "What will be done"
exactly (comment-only correction in `role_settings()`, no allowlist
expansion, no test changes). No scope-exceeded stop occurred and no
proposal-stated alternative was swapped mid-build.

## Doc placement

- No new env var, config key, dependency, or migration introduced — no
  handbook update required.
- No public signature, wire format, or behavior changed — this is a
  comment-only diff inside one existing function; no
  docs/issue-742/decisions/ entry applies.
- No new benchmark or investigation numbers produced by this change —
  the denial-count baseline (0 denials, 4 patterns) and the #700 commit
  citation were already recorded in
  docs/issue-742/reports/implementation/survey.md at phase-1; this
  record cites them, it does not re-derive them.

## How it was verified

```
derived: git diff --stat spawn.py
```
```
 spawn.py | 35 +++++++++++++++++++++++++++++------
 1 file changed, 29 insertions(+), 6 deletions(-)
```
`git diff spawn.py` (full, not just `--stat`) was read directly and
every changed line begins with `#` inside `role_settings()` — no
non-comment line differs from `main`.

```
derived: python3 -m pytest tests/test_spawn.py -k "allow or permission or bash_entry or workspace_bash" -q
```
```
17 passed, 384 deselected in 6.91s
```
The same set of tests the proposal named as already covering this
untouched logic — shown passing above — continues to pass against the
comment-only diff.

Full suite, run at phase-2 completion:
```
derived: python3 -m pytest -q
```
```
FAILED gates/test_boundary.py::t_all_gates_modules_recorded
FAILED gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint
FAILED tests/test_gates.py::t_rulebook_version_is_recorded
FAILED tests/test_gates.py::t_find_violations_uses_record_evidence_for_keywordless_merge
4 failed, 1098 passed, 2 skipped in 173.47s (0:02:53)
```
The first, second, and fourth failures above are the pre-declared
already-red set on `main` (owned by issue-759, unrelated to this
change). The third, `t_rulebook_version_is_recorded`, is not a new
failure caused by this change: it reads the git-dirty status of this
same on-the-record checkout (the `execution-observation` rulebook's
`installLocation` resolves back to this repo in this dev environment)
and fails whenever the working tree has uncommitted changes — which it
did while this suite ran (this session's own not-yet-committed diff).
Confirmed by stashing the diff and re-running the full three-file gate
suite in isolation:
```
derived: git stash && python3 -m pytest gates/test_boundary.py gates/test_generated_paths.py tests/test_gates.py -q; git stash pop
```
```
FAILED gates/test_boundary.py::t_all_gates_modules_recorded
FAILED gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint
FAILED tests/test_gates.py::t_find_violations_uses_record_evidence_for_keywordless_merge
3 failed, 121 passed in 25.58s
```
Exactly the pre-declared 3-failure red set on a clean tree —
`t_rulebook_version_is_recorded` passes clean and will pass again once
this session's change is committed. Not counted as a new failure
introduced by this change; not added to the pre-declared red set since
it is a working-tree artifact, not a code defect (same pattern
independently observed and recorded in
docs/issue-743/reports/implementation.md's "How it was verified").

## Hunt

- after-proposal (phase 1, stance 0 — assume the gate just touched is
  bypassable): NO FINDING, recorded in
  docs/issue-742/reports/implementation/2026-08-11-hunt-confirm-bypasspermissions-baseline.md.
- before-landing (phase 2, stance 1 — assume this change and another
  plugin's rule cancels it out): NO FINDING, appended to the same
  hunt-record file. Checked `on-the-record/hooks/*.sh`/`*.py` for any
  hook that reads `permissions.allow` (none), cross-checked
  `spawn_cmd()`'s own `bypassPermissions` comment for consistency
  (consistent), and checked source-text-scanning tests/gates for
  dependence on the edited comment block's wording (none). Surfaced
  (but did not raise as a finding, since no gate parses it and the
  suite still passes) a stale mirror of the same retired claim in
  `tests/test_spawn.py`'s `WebToolPermissionAccess` docstring — noted
  below under Open findings since `tests/test_spawn.py` is outside this
  issue's frozen write set.

closed_checks:
- check: no-allowlist-expansion-comment-only-diff
  code_under_review: spawn.py
- check: no-new-test-failures-beyond-known-red-set
  code_under_review: spawn.py

## Open findings

None blocking against this issue's write set. The before-landing hunt
noticed that `tests/test_spawn.py`'s `WebToolPermissionAccess` class
docstring (around line 584) still repeats the same pre-#700
`acceptEdits`/`permissions.allow` claim this record's `spawn.py` change
retires — stale prose, not a functional defect (no gate parses it,
`pytest tests/test_spawn.py -k WebToolPermissionAccess -q` passes: `3
passed`). `tests/test_spawn.py` is outside this issue's frozen write
set (`spawn.py`, `docs/issue-742/**` only per the approved proposal), so
it was not touched here. Resolution path: a future doc-accuracy pass
(or the next issue that touches that test file) can reword that
docstring the same way; no issue is required to track it since it is
cosmetic and non-blocking.
