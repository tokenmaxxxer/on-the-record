---
status: proposed
files:
  - spawn.py
  - harness/driver.py
  - on-the-record/hooks/git-fetch-allow-gate.sh
  - on-the-record/hooks/test_git_fetch_allow_gate.py
  - on-the-record/hooks/hooks.json
  - tests/test_spawn.py
  - harness/test_driver.py
  - docs/issue-894/reports/implementation.md
  - docs/issue-894/reports/implementation/survey.md
---

# issue-894 implementation — drop bypassPermissions on resume, cover the gap with an allow-hook

Proposal: docs/issue-894/proposals/implementation.md

## Request

Implement finding #1 (Critical, CVSS 9.1, EoP) from the approved security-threat-model review
(docs/issue-894/reports/security-threat-model.md, PR #900): the resumed orchestrator turn runs
under `--permission-mode bypassPermissions`, which removes the host's own default-deny fallback
for any Bash shape the existing allow-hooks (merge/spawn/gh-write) do not recognize. The review's
disposition is "mitigate": drop bypassPermissions from both resume call sites and cover the one
genuinely-needed uncovered shape (`git fetch`) with a new narrow allow-hook, so the resumed
orchestrator still runs Bash under the host's ordinary default-deny plus the specific allow-hooks
— same posture a non-resumed orchestrator turn already has.

## Constraints

- Both resume call sites (`spawn.py::_resume_orchestrator_session`,
  `harness/driver.py::resume_orchestrator_session`) must drop bypassPermissions; leaving either
  one would leave that path with the same removed-fallback gap.
- Any new allow-hook must follow the existing three hooks' invariants exactly: orchestrator-only
  (CLAUDE_ROLE resolves empty via the session-role-bind.sh snapshot), shape-only validation
  (shlex tokenize, no argument-text inspection, no chaining/substitution operator surviving), and
  never emit `"deny"` — only ever `"allow"` or fall through.
- This is step 3 of issue #894's execution plan; step 2 (structural enforcement gate) is a
  separate work unit per the security-threat-model record's own scoping, not built here.
- The fix must be stated as requiring #776 harness re-measurement, not claimed as already
  verified — this implementation session runs unit tests, not a live #776 harness pass.

## Rationale

Two shapes were considered for closing the gap:

**A (chosen): drop bypassPermissions, extend the allow-hook set for the one missing shape
(`git fetch`).** This is the security-threat-model record's own concrete recommendation for
finding #1, and the survey traced that `git fetch` is the only Bash shape a resumed turn needs
beyond what merge-allow-gate.sh/spawn-allow-gate.sh already cover (docs/issue-894/reports/
implementation/survey.md, "What a resumed orchestrator turn needs"). It restores the same
fail-closed default-deny boundary a non-resumed orchestrator turn already has, with no broader
attack surface than that turn.

**B (rejected as primary, recorded as fallback): keep bypassPermissions, add a default-deny
fallback deny-gate.** Rejected as the primary fix because it does not match the security-threat-
model record's own disposition text, and because option A is achievable without any new
argument-text-inspection logic (the survey found no shape requiring it). Recorded per the task's
explicit ask as the fallback if a future #776 re-measure shows some Bash shape genuinely needed
by a resume cannot be safely covered by a narrow, shape-only allow-hook — in that case B trades
back some of A's tightened boundary for guaranteed completion, and that trade should be made
deliberately by a later session with that concrete evidence in hand, not assumed here.

## What will be done

1. Remove `"--permission-mode", "bypassPermissions"` from the `Popen` argv in
   `spawn.py::_resume_orchestrator_session` and the `subprocess.run` argv in
   `harness/driver.py::resume_orchestrator_session`; update both functions' docstrings to reflect
   the new posture and cite this issue.
2. Add `on-the-record/hooks/git-fetch-allow-gate.sh`, mirroring `merge-allow-gate.sh`'s
   structure: `ORCHESTRATE_OFF` kill switch, orchestrator-identity check via the
   session-role-bind.sh snapshot, strict shlex-tokenized shape match for `git fetch
   [<remote>] [<refspec>...]` (optionally `cd DIR &&`-prefixed) with no operator token in the
   tail, no backtick/`$(`/newline anywhere, emits `allow` JSON on match, bare `exit 0` otherwise.
3. Register the new hook in `on-the-record/hooks/hooks.json`'s `PreToolUse`/`Bash` matcher group.
4. Add `on-the-record/hooks/test_git_fetch_allow_gate.py`, mirroring
   `test_spawn_allow_gate.py`'s subprocess-driven test structure: orchestrator-identity allow,
   role-session no-allow, chained-command no-allow, `cd DIR &&`-prefixed allow.
5. Rewrite the existing bypassPermissions-asserting tests
   (`tests/test_spawn.py::ResumeOrchestratorSessionPermissionMode`,
   `harness/test_driver.py::test_resume_orchestrator_session_ok`) to assert bypassPermissions is
   ABSENT from the resume argv, keeping the rest of each test's round-trip assertions.
6. Write `docs/issue-894/reports/implementation.md` stating what was done, citing this survey and
   proposal, and stating plainly that the fix must be RE-MEASURED by the #776 harness to confirm
   the resumed orchestrator still completes the merge (#1/#4 PASS) under the narrower permission
   set — this session does not claim that PASS itself.
7. Run the affected unit test files and the security-relevant hook tests once, and report their
   actual output.

## Accumulation

This adds a fourth sibling hook file (`git-fetch-allow-gate.sh`) to the same
merge/spawn/gh-write-allow-gate.sh pattern, each a near-duplicate shlex-shape-check script
registered by hand in `hooks.json`. If a fifth, sixth, ... resume-needed Bash shape shows up
later (a future #776 re-measurement could surface one), repeating this by hand N more times means
N more near-identical files and N more `hooks.json` lines, each independently readable but
collectively a hand-maintained list with no single place enumerating "every shape a resumed
orchestrator turn may run." This proposal does not extract a shared shape-matching helper now —
the security-threat-model record traced exactly one missing shape, and the existing three hooks
already accepted this same per-hook duplication as their own design (docs/issue-810,
docs/issue-824). If a future re-measurement in fact surfaces a second or third missing shape,
that is the point to reconsider a shared `allow-gate-lib.sh`/shape-table helper rather than a
fifth hand-copied file — flagged here, not built here, since only one new hook is in scope.

## Out of scope

- Step 2 of issue #894 (structural enforcement of security-threat-model review for future
  trust-boundary changes) — a separate work unit per the security-threat-model record's scoping.
- Findings #3 ($TMPDIR session-bind race) and #4 (credential-flow scope) from the same
  security-threat-model record — separate mitigate dispositions, not this fix's scope.
- Actually executing a live #776 harness re-run — flagged as a required next step, not performed
  in this implementation session (no live orchestrator PR-merge cycle was run here).
- `gh pr view` / `gh pr list` / `git rebase` allow-hook coverage — the survey traced no call site
  where the resumed orchestrator's own Bash tool call needs these directly (see survey item 4);
  not added speculatively.

## How you'll know it worked

- `git grep -n "bypassPermissions" spawn.py harness/driver.py` shows no match inside
  `_resume_orchestrator_session` / `resume_orchestrator_session`.
- The new hook's test file and the rewritten resume-permission-mode tests pass when run directly.
- `docs/issue-894/reports/implementation.md` states the #776 re-measurement requirement in its
  own text (per the task's explicit instruction), not left implicit.
