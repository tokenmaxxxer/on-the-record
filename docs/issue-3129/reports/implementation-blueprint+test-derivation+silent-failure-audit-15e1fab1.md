---
issue: 3129
role: implementation-blueprint+test-derivation+silent-failure-audit-15e1fab1
author: implementation-blueprint+test-derivation+silent-failure-audit-15e1fab1
skills: implementation-blueprint (skill-repository(c05de12)), test-derivation (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: on-the-record/hooks/hooks.json
loop_state: landed
type: fix
breaking: false
verdict: pass — acceptance: `python3 -m pytest tests/test_amendment_channel.py -q` — result: 79 passed; acceptance: `python3 gates/probe_running_session_sees_amendment.py` — result: ok; acceptance: `python3 gates/probe_amendment_notice_fires_once.py` — result: ok; acceptance: `python3 -m pytest tests/ -q` — result: 333 passed, 0 failed
upstream:
  - path: on-the-record/hooks/hooks.json
    sha: 7fa8906bd6d0f42d9994c0dda99bf7c26aa0b7d0
---

# issue-3129 — implementation-blueprint+test-derivation+silent-failure-audit-15e1fab1 record

## What was done

Round 6 on PR #3137 (branch `issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`, this session's local branch head reset onto that history to build here per this round's spawn instructions). Build-now delivery (`CORE_BUILD_NOW=1`, spawner-set).

derived: `python3 -m pytest tests/ -q` at branch tip `9e42e12e` (before this round's fix)
```
bringing up nodes...
........................................................................ [ 21%]
........................................................................ [ 43%]
.............................................................F.......... [ 64%]
........................................................................ [ 86%]
.............................................                            [100%]
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
1 failed, 332 passed, 2 warnings in 10.35s
```
This is 1 failed, not the 23 the task described against `7fa8906b` (round 5's first commit) — `9e42e12e` ("repair round 5 -- test coverage for the trust-root swap") had already landed on top of it before this round started.

derived: `python3 -m pytest tests/test_amendment_channel.py -q` at the same branch tip, run before any change of this round
```
bringing up nodes...
........................................................................ [ 91%]
.......                                                                  [100%]
79 passed in 1.02s
```
This confirms the task's three named amendment-channel fixture/ordering failures (`test_matching_repo_writes_marker_keyed_to_url_issue_number`, and the two `MarkerWriteFailed`/`NoIssueUrlInResponse`-vs-`NoRegisteredRepo` tests) were already resolved by `9e42e12e` — none needed further work this round.

The one real remaining failure was `HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present`. Diagnosed with:

derived: `git diff origin/main..HEAD -- on-the-record/hooks/hooks.json` at branch tip `9e42e12e`
```
-          {
-            "type": "command",
-            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/fail-open-wrapper.sh ${CLAUDE_PLUGIN_ROOT}/hooks/amends-landing-apply.sh"
-          }
         ]
       },
@@ -84,6 +80,10 @@
           {
             "type": "command",
             "command": "${CLAUDE_PLUGIN_ROOT}/hooks/fail-open-wrapper.sh ${CLAUDE_PLUGIN_ROOT}/hooks/lint-test-on-edit.sh post"
+          },
+          {
+            "type": "command",
+            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/fail-open-wrapper.sh ${CLAUDE_PLUGIN_ROOT}/hooks/amendment-channel.sh"
           }
```
Round 5's first commit (`7fa8906b`) deleted the pre-existing `PostToolUse` entry for `amends-landing-apply.sh` from the `Bash`-matcher block while adding the new `amendment-channel.sh` hook to the catch-all (`matcher: None`) block — an accidental deletion during that edit, not an intentional replacement (`amends-landing-apply.sh` and `amendment-channel.sh` are unrelated hooks with unrelated purposes; nothing in the round-5 commit messages or diff claims retiring `amends-landing-apply.sh`).

Fix applied: restored `amends-landing-apply.sh`'s `PostToolUse` entry to its original position in the `Bash`-matcher block, alongside `gate-registration-post-guard.sh`, where it lived before round 5 (`git show origin/main:on-the-record/hooks/hooks.json`, read directly, confirms that original placement). `amendment-channel.sh`'s new wiring in the catch-all block is untouched.

derived: `python3 -m pytest tests/ -q` after the `hooks.json` fix
```
bringing up nodes...
........................................................................ [ 21%]
........................................................................ [ 43%]
........................................................................ [ 64%]
........................................................................ [ 86%]
.............................................                            [100%]
333 passed, 2 warnings in 10.35s
```

acceptance: `python3 -m pytest tests/test_amendment_channel.py -q` — result:
```
79 passed in 1.02s
```
acceptance: `python3 gates/probe_running_session_sees_amendment.py` — result:
```
ok
```
acceptance: `python3 gates/probe_amendment_notice_fires_once.py` — result:
```
ok
```
acceptance: `python3 -m pytest tests/ -q` — result:
```
333 passed, 2 warnings in 10.35s
```

## Why

`test_pre_existing_post_tool_use_commands_are_all_still_present` was right and the code was wrong: it is the additive-only guard for `PostToolUse` (shared with `gates/probe_hooks_additive_survives_merge.py`, issue #3083), and its job is exactly to catch a hook silently dropped by an unrelated edit — which is what happened. Restoring the deleted entry, not weakening the assertion, is the only correct fix; the test's contract (nothing pre-existing may be removed) is unchanged and still holds for every other `PostToolUse` command (derived: the same test passing after the fix, shown above).

The three fixture/ordering failures the task listed needed no further code or fixture change this round: they were already fixed on the branch by `9e42e12e` (derived: `tests/test_amendment_channel.py -q` green before this round touched anything, shown above).

derived: reading `test_cd_does_not_move_the_registered_repo`, `test_no_registered_repo_is_fail_closed_not_skip_silently`, and `test_issue_number_comes_from_the_url_never_the_command_text` in `tests/test_amendment_channel.py` (lines ~415-521), plus their passing status in the 79-passed run above, confirms round 5's design properties hold: registration is the trust root, cd-steering fails closed (`test_cd_does_not_move_the_registered_repo`), a session with no registration fails closed (`test_no_registered_repo_is_fail_closed_not_skip_silently`), and command text is never read for attribution (`test_issue_number_comes_from_the_url_never_the_command_text` — a command naming issue 42 textually, keyed instead by the URL's issue 999). None of these assertions were touched or weakened this round.

## What did not work

None.

## Upstream basis

Builds on PR #3137's branch tip at commit `9e42e12e700d486ff53381ed108c3c73d31c2dca` ("issue-3129: repair round 5 -- test coverage for the trust-root swap"), itself built on `7fa8906bd6d0f42d9994c0dda99bf7c26aa0b7d0` ("issue-3129: repair round 5 -- launcher-owned trust root, positive success check") — the round-5 commit that introduced the `hooks.json` regression this round fixes.

## Open findings

None. canonical: the four acceptance-check outputs and the full-suite run recorded above under `## What was done`, all captured this turn.

## Next steps

None — loop_state is `landed`. canonical: this round's own commit(s), pushed to PR #3137's remote branch `issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`, PR left open and not merged (per this round's task instructions).

## Skill verdicts

other mounted skills: not triggered — this round's fix was a single-entry restoration in `hooks.json` plus one metadata correction, none of which involved deciding multi-module structure (implementation-blueprint), deriving new tests from requirements (test-derivation, since existing coverage already satisfied the acceptance criteria), or auditing newly written error-handling code (silent-failure-audit, since no error-handling code was written this round).
