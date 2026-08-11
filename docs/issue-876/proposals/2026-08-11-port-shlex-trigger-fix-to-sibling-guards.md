---
status: approved
files:
  - on-the-record/hooks/gate-registration-guard.sh
  - on-the-record/hooks/role-axis-completeness-guard.sh
  - on-the-record/hooks/test_gate_registration_guard.py
  - on-the-record/hooks/test_role_axis_completeness_guard.py
  - docs/issue-876/reports/implementation/survey.md
  - docs/issue-876/reports/implementation/resolution.md
  - docs/issue-876/proposals/2026-08-11-port-shlex-trigger-fix-to-sibling-guards.md
---

Note (this session): `docs/issue-876/reports/implementation.md` — the
phase-2 record path — is mechanically blocked by
`on-the-record/hooks/approval-gate.sh` (`CLAUDE_ROLE=implementation`,
branch `issue-876/implementation`, no `APPROVE issue-876/implementation`
comment on the issue yet). `approval-gate.sh`'s own scope is exactly the
role's record file plus `src/`/`test(s)/` paths — it does not gate
`on-the-record/hooks/*.sh` or its tests — so this session's actual fix is
committed in the same PR; the write-up that would otherwise live in
`implementation.md` lives at
`docs/issue-876/reports/implementation/resolution.md` instead, a
phase-1-legal path, matching the precedent issue #866's own PR (`7d97bd6`)
set for this exact situation. This PR's body carries a plain `#876`
reference, no `Closes`.

# Proposal — issue #876, implementation

## Request

Issue #876: `gate-registration-guard.sh` and `role-axis-completeness-guard.sh`
still carry the pre-#866 `\bgit\s+commit\b` substring trigger regex that
`spec-index-preflight.sh` moved away from in PR #875. A `git -c
<key>=<val> commit ...` (or any other global option between `git` and
`commit`) silently defeats the trigger on both, letting the commit land
with neither guard's actual check (spec-registration presence /
axis-completeness) ever running. Port the same `shlex.split`-based token
check PR #875 landed, unchanged in shape, to both sibling hooks. Also
judge, with evidence, whether the resulting triplication should become a
shared helper.

## Constraints

- `on-the-record/hooks/spec-index-preflight.sh` is frozen (issue's own
  scope line) — read-only reference, never edited.
- Port the existing shape; no new design for the trigger check itself.
- Each hook's own regression test file is the only place new test cases
  land — no new shared test module.
- `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` must show no
  new failures versus `origin/main`, compared via isolated worktrees
  (this repo's own `t_rulebook_version_is_recorded` fails against a dirty
  working tree, so a direct in-place run is not a valid comparison
  method — same constraint issue #866's proposal recorded).

## Rationale

Considered extracting the token-check into a shared Python helper module
(e.g. `gates/hook_trigger.py`) imported by all three hooks, since the
same nine-line check is now duplicated a third time. Rejected: the
survey found this repo's "no guaranteed checkout, inline-port instead of
import" constraint still live and current, not stale precedent —
`hooks.json` invokes every hook via `${CLAUDE_PLUGIN_ROOT}/hooks/<script>.sh`,
outside any guarantee that a consumer-repo `gates/` checkout exists at
invocation time. The one hook in this family that already imports a
module instead of duplicating (`role-axis-completeness-guard.sh` →
`gates/role_spec_shape.py`) exists only because that module's two
functions are too large (112 lines) to reasonably re-port, and even then
it needs a two-candidate fallback probe plus fail-open handling for a
missing/stale module — verified this session that the packaged
`on-the-record/gates/` copy is in fact currently missing both functions
the hook needs, so that fallback is load-bearing today, not defensive
boilerplate. A shared helper for this much smaller check would inherit
the identical staleness risk while saving far less code, and — because
this hook family's own documented policy is fail-open on any
missing/stale dependency — a missing shared helper would silently skip
the trigger check entirely, reproducing the exact silent-bypass failure
mode this issue exists to close. Duplication guarantees the check is
always present, because it is each hook's own source text; every other
hook in the directory that needs Python logic already follows this same
inline-port convention (full evidence: `docs/issue-876/reports/implementation/survey.md`,
"The shared-helper question").

Considered leaving the two `import re` / regex-only trigger lines
otherwise untouched and only widening the regex pattern (e.g.
`\bgit\b.*\bcommit\b`) instead of switching to `shlex.split` tokenizing.
Rejected: that was exactly the failure mode PR #875's own fix reasoning
rejected for `spec-index-preflight.sh` (a looser substring match starts
firing on `commit` inside an unrelated token, e.g. `--grep=commit`,
`commit-tree`, or inside a quoted string) — porting the same shape as
already landed and tested is what the issue asks for, and reproducing a
known-worse alternative would contradict the issue's explicit "새로
설계하지 말고 그 모양을 그대로 옮겨라" instruction.

## Accumulation

This change grows the `shlex.split`-based `git commit` trigger-check
snippet from one occurrence (`spec-index-preflight.sh`, landed in PR
#875) to three (adding `gate-registration-guard.sh` and
`role-axis-completeness-guard.sh`), each a byte-for-byte inline port, not
a call to a shared function — the exact shape this guard checks for.
Judged deliberately, not defaulted into: see `## Rationale` above and
`docs/issue-876/reports/implementation/survey.md` ("The shared-helper
question") for the full evidence trail.

If a fourth `PreToolUse`/`Bash` hook is ever added that also needs to
gate on `git commit`, it inherits the same duplication rather than a
shared import, for the same reason — `hooks.json` invokes every hook via
`${CLAUDE_PLUGIN_ROOT}/hooks/<script>.sh` with no guaranteed consumer-repo
checkout, and this hook family's own fail-open policy means a missing
shared dependency degrades to silently skipping the check, not to a
loud failure. This snippet stays small (9 lines) and self-contained by
design; it is not expected to grow in complexity the way
`role_spec_shape.py`'s two functions did before that pair earned an
import-with-fallback treatment. If a future change to the trigger
check's own logic (not just its call sites) is needed, that edit still
has to land in three places by hand — an explicit, accepted cost of the
fail-open-safety trade this proposal makes, not an unnoticed one. A
fifth or sixth occurrence, or any growth in the snippet's own size or
complexity past what one hook-header comment can explain, is the signal
to revisit this decision (e.g. a generated/templated hook body checked in
per-hook, rather than a runtime import) — not a reason to default to
sharing now.

## What will be done

1. In `gate-registration-guard.sh`: add `shlex` to the GUARD body's
   import line, replace the `re.search(r"\bgit\s+commit\b", cmd)` trigger
   check with the same `shlex.split(cmd)` + `"git" in tokens and "commit"
   in tokens` check `spec-index-preflight.sh` uses (fail-open on
   `ValueError` from an unparseable command), and note the port in the
   file's header comment.
2. In `role-axis-completeness-guard.sh`: same port. `re` stays imported
   (used later in the file for `roles/*.json` path matching); `shlex` is
   added to the GUARD body's top import line.
3. Add one regression case to each hook's own test file — a real staged
   violation (unregistered gate module / zero-owner axis) committed via
   `git -c user.name=Bot -c user.email=bot@example.com commit -m msg`,
   asserting `returncode == 2` and the expected stderr — plus one
   `git commit-tree ...` true-negative case, matching each file's
   existing end-to-end (real hook process, real `git init` fixture)
   convention rather than importing a pure-python mirror.
4. Run each hook's own test file, then `on-the-record/hooks/` as a whole,
   then `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` in two
   isolated `git worktree` checkouts (this branch's tip, `origin/main`)
   and diff the failure sets.
5. Dispatch one before-landing `warrant:warrant-hunter` (stance rotation
   per `.warrant-hunt.count`), wait for and consume its result in this
   same turn (contract v3 s22 — headless single-shot).
6. Write `docs/issue-876/reports/implementation/resolution.md` recording
   the fix, the shared-helper judgment call, the hunt, and the
   verification transcripts.

## Out of scope

- `spec-index-preflight.sh` itself and its test — frozen per the issue.
- Redesigning the trigger-detection approach (e.g. a different
  tokenizer, a stricter/looser match) — port the landed shape only.
- The commit-time-only design limitation (a GitHub server-side
  squash-merge commit is structurally invisible to a `PreToolUse` hook)
  — already recorded by #866, explicitly not reopened by this issue.
- A shared helper module — judged and rejected, see Rationale.

## How you'll know it worked

- Both hooks deny a `git -c <k>=<v> commit ...` invocation carrying a
  staged violation their existing plain-`git commit` case already
  denies, with matching stderr content.
- `python3 -m pytest on-the-record/hooks/ -q` passes in full, including
  the new cases.
- The branch-vs-`origin/main` worktree comparison of
  `gates/ tests/ on-the-record/hooks/` shows the branch's failure set is
  empty (or strictly smaller, and never a superset of) `origin/main`'s
  failure set, with no failure introduced by this change.
