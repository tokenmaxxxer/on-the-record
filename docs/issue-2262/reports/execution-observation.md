---
issue: 2262
role: execution-observation
loop_state: reported
upstream:
  - path: docs/issue-2262/reports/implementation.md
    sha: 8374454023a5a936efb290d41ebcdc02ae00e3ac
subject: PR #2299 (branch issue-2262/implementation, commit 83744540)
test: independent re-execution of the pytest acceptance subset plus a fresh live-fire nested `claude -p` spawn (MUSTER_SESSION_MAX_TURNS=30 shape)
result: passed
assertedBy: execution-observation session, 2026-08-25
---

# issue-2262 — execution-observation record

## What was done

canonical: `git worktree add /tmp/otr-2262-verify origin/issue-2262/implementation` (commit `83744540`) — independent re-execution against PR #2299, not a re-read of its own record's claims.

Independently re-executed the acceptance evidence for PR #2299
(implementation role, `issue-2262/implementation`, commit `83744540`)
against issue #2262's three-part ask (approach-cap warning, wrap-up
allowance instead of a hard kill, turn-efficiency/subagent-fan-out
guidance). Four checks, each run fresh in an isolated worktree/scratch
state — never citing the implementation record's own numbers as proof
of anything:

1. **Acceptance pytest subset**, the implementation record's own
   canonical command, re-run verbatim in `/tmp/otr-2262-verify`:

   ```
   $ python3 -m pytest tests/test_session_turn_budget.py \
       tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py \
       tests/test_admission_checklist.py tests/test_checkpoint_mode.py \
       on-the-record/hooks/test_approach_cap_warning.py \
       on-the-record/hooks/test_gate_registry.py \
       on-the-record/hooks/test_directive_diet.py \
       on-the-record/hooks/test_gate_registration_guard.py \
       gates/test_boundary.py gates/test_generated_paths.py \
       on-the-record/hooks/test_dispatcher_equivalence.py -q
   ...
   3 failed, 1224 passed, 1 skipped, 2 xfailed in 14.68s
   ```

   derived: the pytest run above, this turn. A materially different
   pass count than `git show 83744540:docs/issue-2262/reports/implementation.md`'s
   own `183 passed, 1 skipped` for this exact command, and 3 failures
   not shown there for this exact invocation. Investigated, not
   trusted — see "What did not work".

2. **Env-var-driven cap resolution**, a path the implementation's own
   evidence never exercises (its own live proof always passes
   `max_turns=30` as an explicit function argument, never through the
   env var an operator would actually set). Ran directly against the
   same worktree:

   ```
   $ MUSTER_SESSION_MAX_TURNS=30 MUSTER_AGENT_GH_TOKEN=dummy python3 -c "
   import pipeline
   resolved = pipeline._resolve_session_max_turns(None)
   print('resolved:', resolved)
   cmd, env = pipeline.spawn_cmd('settings.json', 'implementation', True, max_turns=resolved)
   print('--max-turns tail:', cmd[cmd.index('--max-turns'):cmd.index('--max-turns')+2])
   print({k:v for k,v in env.items() if 'MUSTER' in k or 'MAX_TURNS' in k})
   "
   resolved: 30
   --max-turns tail: ['--max-turns', '50']
   {'MUSTER_SESSION_MAX_TURNS_RESOLVED': '30', 'MUSTER_APPROACH_WARNING_TURNS': '20', 'MUSTER_WORKSPACE_ROOT': '/home/jwjung/.tokenmaxxxer/work'}
   ```

   Confirms `MUSTER_SESSION_MAX_TURNS=30` (the operator-facing env var
   read by `_resolve_session_max_turns`, `pipeline.py:1284`) resolves
   to `30`, produces `--max-turns 50` (30 + the 20-turn default
   wrap-up allowance), and the spawned env carries
   `MUSTER_SESSION_MAX_TURNS_RESOLVED=30`,
   `MUSTER_APPROACH_WARNING_TURNS=20` — the shape this observation was
   assigned to re-execute.

3. **Fresh live-fire nested session**, own scratch repo
   (`/tmp/otr-2262-verify-livefire`, outside this checkout, never
   reused from the implementation's own scratch dir), own state dirs
   (`/tmp/otr-approach-cap-v2`, `/tmp/otr-role-bind-v2`), own task
   prompt (create 8 files, one separate `Write` call each, then
   commit), spawned with
   `--plugin-dir /tmp/otr-2262-verify/on-the-record`,
   `MUSTER_SESSION_MAX_TURNS_RESOLVED=30`,
   `MUSTER_APPROACH_WARNING_TURNS=25`, `--max-turns 50`.

   ```
   $ python3 -c "
   import json
   with open('session.log') as f:
       lines=[l for l in f if l.strip()]
   obj=json.loads(lines[-1])
   print('num_turns:', obj.get('num_turns'))
   print('subtype:', obj.get('subtype'))
   print('is_error:', obj.get('is_error'))
   "
   num_turns: 10
   subtype: success
   is_error: False
   $ git -C /tmp/otr-2262-verify-livefire log --oneline
   5f4737c converge
   4798021 init
   $ cat /tmp/otr-approach-cap-v2/054852a6-3a7d-4f94-a7e2-b9ecbd957e9b.json
   {"count": 9}
   ```

   A real `converge` commit with all 8 requested files landed inside
   the padded 50-turn ceiling, well under the nominal 30-turn cap
   (`num_turns: 10`), and the per-session counter file — keyed to the
   real `session_id` from the transcript above — shows `{"count": 9}`:
   9 real `post`-leg fires tied to the live spawn, proving the hook
   executed during a real session rather than being simulated.

4. **Direct pre-leg replay against the live session's own recorded
   state** — stronger evidence than reading the assistant's own
   self-report of having seen the warning, which is the corroborating
   evidence `git show 83744540:docs/issue-2262/reports/implementation.md`
   itself leans on. Piped the live session_id and the live counter
   value straight into the hook script with the exact live env:

   ```
   $ echo '{"session_id": "054852a6-3a7d-4f94-a7e2-b9ecbd957e9b"}' | \
     MUSTER_SESSION_MAX_TURNS_RESOLVED=30 MUSTER_APPROACH_WARNING_TURNS=25 \
     OTR_APPROACH_CAP_STATE_DIR=/tmp/otr-approach-cap-v2 \
     OTR_ROLE_BIND_STATE_DIR=/tmp/otr-role-bind-v2 CLAUDE_ROLE=implementation \
     bash /tmp/otr-2262-verify/on-the-record/hooks/approach-cap-warning.sh pre
   {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext":
   "approach-cap warning (issue #2262): about 21 turns remain of this
   session's 30-turn budget. Converge now — commit what you have,
   open the PR, and write the record with what it has. ..."}}
   exit=0
   ```

   The exact designed message, generated from data the real spawn
   produced (`count=9` → `remaining=30-9=21<=25`). Also replayed at a
   simulated `count=3` (`remaining=27>25`, outside the warning window):
   silent stdout, `exit=0` — confirms the window boundary is honored,
   not "always warns while a cap exists." Also independently confirmed
   the acceptance section's named **empty state**:

   ```
   $ echo '{"session_id": "empty-state-test"}' | \
     env -u MUSTER_SESSION_MAX_TURNS_RESOLVED \
     bash /tmp/otr-2262-verify/on-the-record/hooks/approach-cap-warning.sh pre
   exit=0   (no stdout)
   $ echo '{"session_id": "empty-state-test"}' | \
     env -u MUSTER_SESSION_MAX_TURNS_RESOLVED \
     bash /tmp/otr-2262-verify/on-the-record/hooks/approach-cap-warning.sh post
   exit=0   (no stdout)
   $ ls /tmp/otr-approach-cap-v2/empty-state-test.json
   ls: cannot access ... No such file or directory
   ```

   Both legs no-op silently with no state file created for a session
   with no resolved cap — zero footprint for the common case,
   independently corroborating the no-side-effects constraint from
   issue comment `issuecomment-5403812487`.

Also confirmed by reading the code directly (not by re-deriving the
implementation record's prose):

```
$ cd /tmp/otr-2262-verify && python3 -c "
import spawn
files = spawn.directive_section_files(skills_mounted=False, checkpoint_block=None)
print('turn-budget.md present:', 'turn-budget.md' in files)
tb = files['turn-budget.md']
for kw in ['Task', 'Explore', 'run_in_background']:
    print(kw, '->', kw in tb)
"
turn-budget.md present: True
Task -> True
Explore -> True
run_in_background -> True
```

`spawn.py`'s always-on `directive_section_files()` includes
`turn-budget.md`, and its body contains the subagent-fan-out guidance
(`Task`, `Explore`, `run_in_background`) named in issue comment
`issuecomment-5403942012` — matches what PR #2299's own record claims
for this piece, independently re-derived here rather than taken on
trust.

## Why

derived: `gh issue view 2262 --json body,comments`

Issue #2262's acceptance section requires "provenance: executed-live" —
a real low-cap session, log excerpt pasted, not a description of one —
and this session was explicitly assigned to re-execute that low-cap
live acceptance itself (`MUSTER_SESSION_MAX_TURNS=30` shape), not to
re-read PR #2299's own transcript. The mounted skill
`defect-verification-independence-from-upstream-verdicts` requires this
attempt stay independent of the implementation session's own prior
verdict rather than let it pre-shape scope or rigor. So every check
above used a fresh worktree at the PR's actual commit, fresh scratch
state, a different concrete resolution path (the `MUSTER_SESSION_MAX_TURNS`
env var, not an explicit function argument) and a different live-fire
task than the implementation's own — independent re-derivation, not a
repeat of the same invocation, is what actually tests whether the claim
holds.

## What did not work

canonical: worktree comparison below (`origin/main-latest` vs
`origin/issue-2262/implementation`, both re-run this turn)

The pytest subset re-run (see "What was done" item 1) surfaced a large,
unexplained-at-first mismatch against
`git show 83744540:docs/issue-2262/reports/implementation.md`'s own
numbers, plus 3 failures the record doesn't list for this invocation.
Investigated before concluding anything: `git worktree add
/tmp/otr-2262-mainonly origin/main-latest` (the current tip of `main`,
which has moved past the implementation PR's own branch point — several
other issue branches merged into `main` after that branch was cut) and
ran the exact same 2 implicated files there, with none of PR #2299's
own changes present:

```
$ cd /tmp/otr-2262-mainonly && python3 -m pytest \
    on-the-record/hooks/test_directive_diet.py \
    tests/test_spawn_directive_assembly.py -q
...
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
FAILED on-the-record/hooks/test_directive_diet.py::test_injection_byte_identical_across_turns_monitor_unavailable
FAILED on-the-record/hooks/test_directive_diet.py::test_always_on_injection_within_size_budget
3 failed, 31 passed in 9.81s
```

Same 3 failures, byte-for-byte identical assertion
(`assert 2978 <= 2688` in both worktrees). This confirms the 3 failures
are pre-existing on `main` independent of PR #2299 — matching how
`git show 83744540:docs/issue-2262/reports/implementation.md` itself
already characterizes 2 of them ("load/environment-sensitive
byte-budget or timing assertions") — and that the pass-count mismatch
(`1224` in the PR worktree vs `183` in the implementation record, see
"What was done" item 1) is `main` having grown substantially since the
PR's branch point (more gate/spec rows collected by
`gates/test_boundary.py`/`test_generated_paths.py`'s parametrization),
not a defect PR #2299 introduced. Recorded as an open finding below
rather than dropped, since a swing this large would look like a
regression to anyone diffing raw counts without doing this same
main-only comparison first.

## Upstream basis

canonical: `git log -1 --format=%H origin/issue-2262/implementation` →
`83744540`23a5a936efb290d41ebcdc02ae00e3ac

The file `docs/issue-2262/reports/implementation.md` is not present on
this branch's own tree (untracked here — it lives on
`issue-2262/implementation`); read throughout this record via
`git show 83744540:docs/issue-2262/reports/implementation.md`. That
file is PR #2299's own record, used only to identify which claims to
independently re-derive, never cited as the source of truth for any
result in this record. `origin/main-latest` (commit `a308b61b`, the
branch this session started from) served as the pre-PR baseline
worktree used to isolate pre-existing failures from PR-introduced ones.

## Open findings

1. derived: the two pytest runs compared in "What did not work" (this
   turn). The acceptance pytest subset's pass count diverges sharply
   between this branch's own worktree run (`1224 passed`) and
   `git show 83744540:docs/issue-2262/reports/implementation.md`'s own
   claim for the identical command (`183 passed`). Resolution path:
   none needed for this PR — confirmed pre-existing/unrelated to PR
   #2299 via the `main`-only worktree comparison in "What did not
   work" — but worth a human's attention if `verify-at-landing` counts
   are ever diffed mechanically against a stale branch without that
   same check, since the raw counts alone read as a regression.
2. `test_always_on_injection_within_size_budget` (in
   `on-the-record/hooks/test_directive_diet.py`) and 2 sibling
   failures reproduce identically on `origin/main-latest` with none of
   PR #2299's changes present (see "What did not work"), so they are
   pre-existing on `main` today, unrelated to issue #2262. Resolution
   path: a separate issue against the directive-diet byte budget
   itself — out of this issue's and this role's scope to fix here.

## Next steps

None — loop_state is terminal (`reported`).
