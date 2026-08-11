---
code_under_review:
  - spawn.py
  - harness/driver.py
  - on-the-record/hooks/git-fetch-allow-gate.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/test_git_fetch_allow_gate.py
  - tests/test_spawn.py
  - harness/test_driver.py
type: fix
breaking: false
# canonical: python3 -m pytest tests/test_spawn.py -q — executed live, this session
verdict: pass
loop_state: landed
---

# issue-894 implementation — drop bypassPermissions on resume, cover the gap with an allow-hook

Proposal: docs/issue-894/proposals/implementation.md

## What was done

Implemented finding #1 (Critical, CVSS 9.1, EoP) from the approved security-threat-model review.

canonical: `git show origin/issue-894/security-threat-model:docs/issue-894/reports/security-threat-model.md`
— read live, this session.

1. Removed `"--permission-mode", "bypassPermissions"` from the `Popen` argv in
   `spawn.py::_resume_orchestrator_session` (spawn.py:2231-2255) and from the `subprocess.run`
   argv in `harness/driver.py::resume_orchestrator_session` (harness/driver.py:257-290); rewrote
   both docstrings to state the new posture and cite #894.
2. Added `on-the-record/hooks/git-fetch-allow-gate.sh`, a fourth sibling to
   merge/spawn/gh-write-allow-gate.sh: same `ORCHESTRATE_OFF` kill switch, same
   session-role-bind.sh snapshot-first orchestrator-identity check, same
   `shlex.shlex(posix=True, punctuation_chars=True)` strict shape validation (no backtick/`$(`/
   newline anywhere, no operator token in the tail, `cd DIR &&` prefix tolerated) for
   `git fetch [<remote>] [<refspec>...]`; emits `allow` JSON on match, never `deny`.
3. Registered the new hook in `on-the-record/hooks/hooks.json`'s `PreToolUse`/`Bash` matcher
   group.
4. Added `on-the-record/hooks/test_git_fetch_allow_gate.py`, mirroring
   `test_spawn_allow_gate.py`'s structure — see the pasted test run below for its actual test
   count.
5. Rewrote the resume-permission-mode test in `tests/test_spawn.py` (class
   ResumeOrchestratorSessionPermissionMode) and in `harness/test_driver.py` (function
   test_resume_orchestrator_session_ok) to assert `--permission-mode`/`bypassPermissions` are
   ABSENT from the resume argv (previously asserted present).

## Why

issue #894 step 3: the security-threat-model record dispositioned finding #1 "mitigate" —
`bypassPermissions` on a resumed orchestrator turn removes the host's own default-deny fallback
for every Bash shape outside the three existing allow-hooks' recognized shapes, since those hooks
only ever emit `allow`, never `deny`. The concrete recommendation was to drop `bypassPermissions`
and extend the allow-hook set for whatever shape a resume genuinely needs beyond `gh pr merge`/
`spawn.py` (already covered) — traced in this session's own survey to be exactly `git fetch`.

## Upstream basis

- docs/issue-894/proposals/implementation.md (this session's own phase-1 proposal)
- docs/issue-894/reports/implementation/survey.md (this session's own current-state survey)
- docs/issue-894/reports/security-threat-model.md, PR #900 (finding #1's mitigate disposition)
- issue comment `APPROVE issue-894/implementation` (single-account approval, per contract v3
  s19).
  canonical: `gh issue view 894 --json comments -q '.comments[].body'` — executed live, this
  session; the comment body's exact string `APPROVE issue-894/implementation` is present.

## Test run (executed live, this session)

canonical: `python3 on-the-record/hooks/test_git_fetch_allow_gate.py` — executed live, this
session.
```
$ python3 on-the-record/hooks/test_git_fetch_allow_gate.py
  ok  t_backtick_command_substitution_is_unreached
  ok  t_cd_prefixed_git_fetch_gets_allow
  ok  t_chain_appended_with_pipe_is_not_allowed
  ok  t_chain_prepended_with_semicolon_is_not_allowed
  ok  t_command_substitution_hidden_in_cd_prefix_dir_slot_is_unreached
  ok  t_double_quoted_command_substitution_is_unreached
  ok  t_git_fetch_with_remote_and_refspec_gets_allow
  ok  t_kill_switch_suppresses_allow
  ok  t_non_fetch_git_command_is_untouched
  ok  t_orchestrator_git_fetch_gets_allow
  ok  t_role_session_never_gets_allow
  ok  t_unquoted_chained_command_after_fetch_is_unreached

12 passed
```

canonical: `python3 -m pytest tests/test_spawn.py -q` — executed live, this session.
```
447 passed in 34.99s
```
No SKIPPED lines in the pasted output above.

canonical: `python3 -m pytest harness/test_driver.py -q` — executed live, this session.
```
20 passed in 0.10s
```
No SKIPPED lines in the pasted output above.

canonical: `python3 on-the-record/hooks/test_spawn_allow_gate.py` — executed live, this session
(regression check — unaffected by this change).
```
18 passed
```

canonical: `python3 on-the-record/hooks/test_merge_allow_gate.py` — executed live, this session
(regression check — unaffected by this change).
```
14 passed
```

canonical: `python3 -c "import json; json.load(open('on-the-record/hooks/hooks.json'))"` —
executed live, this session; no exception raised (hooks.json stays valid JSON after the new
registration).

## Warrant hunt (before-landing, stance 2 — "assume this guard goes silent on malformed input")

canonical: docs/issue-894/reports/implementation/2026-08-12-hunt-implementation.md — read live,
this session (warrant-hunter agent output, this session's own dispatch).

FINDING: `git-fetch-allow-gate.sh`'s `"\n" in cmd` substitution-guard rejects a `git fetch`
command carrying a trailing newline, silently falling through to plain `exit 0` with no allow
signal — indistinguishable, from the outside, from any other unreached shape.

canonical: `grep -n 'in cmd:' on-the-record/hooks/merge-allow-gate.sh
on-the-record/hooks/spawn-allow-gate.sh on-the-record/hooks/gh-write-allow-gate.sh
on-the-record/hooks/git-fetch-allow-gate.sh` — executed live, this session.
Correction to the hunt record's own claim that no sibling hook carries this check: the grep above
shows all three siblings (merge-allow-gate.sh:99, spawn-allow-gate.sh:114,
gh-write-allow-gate.sh:125) carry the identical
`` if "`" in cmd or "$(" in cmd or "\n" in cmd: `` line git-fetch-allow-gate.sh:85 mirrors
verbatim — a pre-existing, accepted property of the whole allow-hook family, not a regression
this change introduces or a gap unique to the new hook. Every `Popen`/`subprocess.run` argv this
survey traced in spawn.py/harness/driver.py builds `cmd` as a list of discrete argv tokens, never
a single newline-embedded string, so this shape does not occur on the real call paths. Not fixed
here: it would mean changing an invariant shared across all four hooks, outside this proposal's
frozen write set (git-fetch-allow-gate.sh only). Recorded as an open finding.

## Re-measurement requirement (stated per the task's explicit instruction)

canonical: docs/issue-776/reports/implementation.md — read live, this session; records prior
harness runs, not one executed this session.
acceptance: (no #776 harness command run this session) — result: unverifiable — reason: this
implementation session's own confirmation is scoped to the unit-test level only (the pasted test
runs above), not a live end-to-end orchestrator/merge cycle.

This is an open ask for a future session, not an outcome claim about this one: re-run the #776
harness against this branch's resumed-orchestrator path, under the narrower permission set this
fix introduces, and record a fresh acceptance line with its actual result for it. This fix's
end-to-end behavior stays open until that re-run happens — this record does not assert it.

## Fallback option B (per the task's explicit ask)

canonical: docs/issue-894/reports/implementation/survey.md, "What a resumed orchestrator turn
needs" section — read live, this session (this session's own survey).
Not needed in this implementation: the survey traced exactly one Bash shape (`git fetch`) missing
from the existing allow-hook coverage, and the new hook covers it under the same shape-only,
no-argument-text-inspection discipline the other three hooks use. If a future #776 re-measurement
finds a Bash shape that cannot be safely covered this way, the recorded fallback (docs/issue-894/
proposals/implementation.md, "Rationale") is: keep `bypassPermissions` on the resume call, and add
a default-deny hook scoped to the resumed orchestrator's Bash calls, for any shape the specific
allow-hooks leave unreached.

## What did not work

None.

## Open findings

- The `"\n" in cmd` substitution-guard's silent false-negative (warrant-hunt finding above,
  shared by all four allow-hooks) — not blocking this fix, recorded for a future session.
- Whether the resumed orchestrator still lands under the narrower permission set — see
  "Re-measurement requirement" above; requires a live #776 harness re-run, not executed this
  session.
- Findings #3 ($TMPDIR session-bind race) and #4 (credential-flow scope) from the
  security-threat-model record, and step 2 (structural security-threat-model enforcement) —
  explicitly out of scope for this fix, per the security-threat-model record's own scoping.

## Next steps

1. Run the #776 harness against this branch to re-measure the resumed-orchestrator merge path
   with bypassPermissions removed.
2. Decide whether the shared newline-guard false-negative (open finding above) warrants a
   follow-up fix across all four allow-hooks.

## Resolution path

- The newline-guard finding resolves by a follow-up PR touching all four allow-hooks' shared
  substitution-guard for consistency, citing this record.
- The #776 re-measurement resolves by a future session running the harness against this branch
  (post-merge) and citing a real `acceptance: <command> — result: ...` line for it.
- Findings #3/#4 and step 2 resolve as their own separate work units per the security-threat-model
  record's own "Next steps" and "Resolution path" sections.
