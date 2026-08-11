---
status: proposed
files:
  - spawn.py
  - docs/issue-742/reports/implementation/survey.md
  - docs/issue-742/proposals/confirm-bypasspermissions-baseline.md
  - docs/issue-742/reports/implementation/2026-08-11-hunt-confirm-bypasspermissions-baseline.md
  - docs/issue-742/reports/implementation.md
---

## Request

#742 asks for a fix to the permission-denial retry loop it measured
(1,226 denials across 219 sessions, four command-shape patterns:
compound-command partial approval, unapproved simple commands, `/tmp`
writes, BOM/unicode-whitespace) and names a specific structural
hypothesis: `role_settings()`'s `permissions.allow` never got a `Bash`
entry when #695 removed the role-session sandbox. It asks (a) which
permission layer actually judges Bash post-#695, measured live rather
than assumed, and (b) what, if anything, should be added to the
allowlist, weighing wall-clock recovery against how much the role
session's reach outside its workspace grows.

## Constraints

- No sandbox reintroduction (#695 is an operator decision, out of
  scope per the issue).
- No changes to the harness's own approval classifier — only to command
  shapes this repo produces.
- The allowlist judgment call must be justified and recorded, not
  assumed.
- Acceptance-1 (denial-count before/after) has a stated empty state:
  "if no expansion target is found, record the reasoning with a
  0-denial baseline and stop" — this proposal exercises that clause.
  Acceptance-2 (allowlist unit tests) has a correspondingly stated
  "N/A" empty state when no expansion happens.

## Rationale

**Chosen: no `permissions.allow` expansion; comment-only correction in
`role_settings()`.** The survey (`docs/issue-742/reports/implementation/survey.md`)
found that #700 (commit `b762681`, landed 2026-08-11 10:38, before this
session's branch point) already changed every real role-work spawn
(`spawn_cmd()`, `consult_cmd()` — the only two `["claude", ...]`
invocations in `spawn.py` that do role work) to
`--permission-mode bypassPermissions`. Per Anthropic's own docs
(`https://code.claude.com/docs/en/permission-modes`, quoted in the
survey): "`bypassPermissions` mode disables permission prompts and
safety checks" and "Allow rules have no effect in `bypassPermissions`
because everything else is already approved." A live four-pattern probe
in this exact session (a spawned `implementation`-role process,
confirmed via `ps -ef` to be running with `--permission-mode
bypassPermissions`) reproduced zero denials for all four patterns #742
names, including the BOM-shaped `python3` heredoc.

**Rejected alternative: add a `Bash` (or scoped Bash sub-pattern) entry
to `permissions.allow` anyway, as defense-in-depth against a future
mode revert.** Rejected because it would be speculative
future-proofing against a revert nobody has proposed: `permissions.allow`
entries are inert for every current spawn path (the docs excerpt above
is unconditional, not "inert unless X"), so adding them today changes
no runtime behavior and cannot be exercised by any test that reflects
real spawn behavior — a unit test asserting "pattern P is present in
the allow list" would pass while `bypassPermissions` makes P
irrelevant, which is worse than no test: it certifies a boundary that
is not the operative one. If `bypassPermissions` is ever reverted, that
revert is itself a decision that should re-derive the allowlist against
whatever mode is active then, not inherit assumptions frozen today
against an unknown future classifier/mode combination. Leaving
`permissions.allow` as-is, with the comment correction below, keeps the
one artifact that actually needs to be accurate (the comments
explaining *why* the list exists) honest without adding dead
configuration.

**Rejected alternative: no code change at all, survey-only.** Considered,
since the functional finding is "nothing to change." Rejected because
the existing comments at `spawn.py:492-501` and `spawn.py:507-518`
state a threat model (`headless` + `acceptEdits` + `permissions.allow`
gates Bash) that #700 has since made false for the spawn paths that use
`role_settings()`'s output — leaving them as-is actively misleads a
future reader into treating `permissions.allow` as the operative Bash
boundary. A comment-only annotation is the minimum change that keeps
the code's stated rationale truthful, directly serves #742's own
"which layer judges Bash, measured, not assumed" question by recording
the answer at the point future readers will look, and carries no
behavioral or test-surface risk (no logic, no new dependency, no
schema change).

## What will be done

- `spawn.py`: add a comment near the `permissions.allow` construction
  block (`role_settings()`, around lines 492-539) noting that
  `--permission-mode bypassPermissions` (issue #700, `spawn_cmd()` /
  `consult_cmd()`) has made this list's Bash-relevant entries inert for
  real role spawns since 2026-08-11, that `PreToolUse`/`PermissionRequest`
  hooks are the layer that now actually judges a tool call, and that the
  list is retained because `role_settings()` is also called by
  non-`bypassPermissions` paths that don't do role work (the marketplace
  warm-up/install/doctor-probe spawns) and as the artifact the CLI would
  fall back to were `bypassPermissions` ever disabled for a role. No
  logic changes — the `permissions.allow` construction itself is
  untouched.
- `docs/issue-742/reports/implementation.md`: the phase-2 record,
  written after approval, documenting the comment-only diff, the
  post-change test run, and closing the loop_state.
- No changes to `role_settings()`'s allow-list contents, no new
  environment variable, no new dependency, no test file changes (the
  17 existing `permissions.allow`-construction tests in
  `tests/test_spawn.py` already cover the untouched logic and continue
  to pass against a comment-only diff).

## Accumulation

Not accumulation-cost-shaped. The proposed change is one comment block
in one function (`role_settings()`) in one file (`spawn.py`), touched
once, not a repeated per-instance edit across `roles/*.json` or similar
N-file lists. The survey's observation that `spawn.py` has five inline
`subprocess.run(["claude", ...])` call sites with no shared helper
(lines 326, 715, 3465, 3588, and the doctor probe at 3406) is pre-existing
structure this proposal describes but does not add to or repeat — no new
call site is introduced, and consolidating those five into a shared
helper is not part of this change (would be a separate, larger refactor
with its own risk/benefit tradeoff, out of scope here). If a future
issue did add a sixth inline spawn site, that repetition would be that
issue's accumulation question to answer, not retroactively this one's.

## Out of scope

- Reverting or altering `--permission-mode bypassPermissions` itself
  (issue #700's decision; revisiting it is a separate issue with its
  own risk analysis, per that commit's own rationale).
- Fixing the harness's own approval-classifier behavior (explicitly out
  of scope per #742's own text).
- Re-deriving or auditing the historical 219-session/1,540-denial log
  corpus (not present in this repo; accepted as given context).
- Any sandbox reintroduction.

## How you'll know it worked

- Acceptance-1's empty state is satisfied: the survey's four-probe
  table, executed live in this session (a real `implementation`-role
  spawn), shows a 0-denial baseline across all four patterns #742
  names, with the reasoning (permission-mode change, not allowlist
  content, already closed the gap) recorded in the survey.
- Acceptance-2 is N/A per its own empty-state clause, since no
  `permissions.allow` expansion is proposed.
- Phase-2 diff review: `git diff spawn.py` shows only comment lines
  changed inside `role_settings()`, no functional lines touched.
- `python3 -m pytest tests/test_spawn.py -k "allow or permission or
  bash_entry or workspace_bash"` continues to show all pre-existing
  tests passing after the comment edit (17 passed at survey time).
- `python3 -m pytest gates/test_boundary.py gates/test_generated_paths.py
  tests/test_gates.py` continues to show exactly the same three
  pre-existing failures owned by issue-759 (`t_all_gates_modules_recorded`,
  `t_all_generators_recorded_and_disjoint`,
  `t_find_violations_uses_record_evidence_for_keywordless_merge`) and no
  new ones.
