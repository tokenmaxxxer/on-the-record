---
issue: 2705
role: adversarial-review-a243c784
author: adversarial-review-a243c784
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2864's own deliverable
code_under_review: on-the-record PR #2864 (de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0)
loop_state: landed
type: review
breaking: false
verdict: changes-recommended — checked: reproduced all four task-brief items against a `git worktree add` checkout of PR #2864's head (`de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0`) — result: the strong/weak split is real (guard byte-unchanged, nudge legible, both control cases pass), but "no overhead increase" fails in the realistic case: derived: 500-call `subprocess.run` timing loop against the PR head's actual script, before vs. after a single `{"violations": []}` file exists in `$STATE_DIR` — result: `1.525 ms/call` -> `33.925 ms/call`, ~22x, permanent, on the broadest-matcher hook path in the system.
upstream:
  - path: de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0:on-the-record/hooks/gate-registration-post-guard.sh
    sha: de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0
  - path: de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0:docs/issue-2705/reports/architecture-interface-contract-shape-3f3d4ef5.md
    sha: de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0
---

# issue-2705 — adversarial-review-a243c784 record

## What was done

Independent, round-4 re-derivation of PR #2864's `gate-registration-post-guard.sh`, a weaker-
promise `PreToolUse`+`PostToolUse` companion to `gate-registration-guard.sh` for the bundled
`git add && git commit` shape. All four task-brief items were re-derived from scratch against a
`git worktree add /tmp/pr2864-wt pr-2864` checkout of the PR head
(`de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0`) plus a fresh `git worktree add /tmp/main-wt-fresh
origin/main` for comparison — canonical: `git worktree list` after cleanup shows only this
session's own worktree, both temp worktrees removed via `git worktree remove --force`.

### 1. Pre-mode overhead — re-measured; the fast path is a one-way door

canonical: read `de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0:on-the-record/hooks/gate-registration-post-guard.sh`
lines 97–103 (bash-only `pre`-mode short-circuit: `for _f in "$STATE_DIR"/*.json; do [ -e "$_f" ]
&& { _has_state=1; break; }; done`) and line 355 (`_save(data)` called unconditionally after the
sha loop in `post` mode, not gated on any violation having been appended) — the short-circuit
checks file *existence* only, never content, and no code path in the file ever calls
`os.remove`/`os.unlink` on a state-dir JSON file (derived: `grep -n "os.remove\|os.unlink"
on-the-record/hooks/gate-registration-post-guard.sh` on the PR head — no match).

derived: 500-call `subprocess.run` timing loop against the PR head's actual script, `TMPDIR`
pointed at a fresh empty dir — result:
```
no-state (n=500):      1.525 ms/call
```
— in the same order of magnitude as the PR's own 0.96ms claim (different machine).

Then dropped one `{"violations": []}` file into `$STATE_DIR` (simulating a resolved, or a never-
violated-but-`post`-touched, session) and re-ran the identical loop — derived: same script,
same harness, only `$STATE_DIR` contents changed — result:
```
empty-violations-state-file-present (n=500):  33.925 ms/call
```
(an earlier, cruder 200-call run gave `0.963s` total vs. `6.926s` total for the same before/after
— same order of magnitude, independent confirmation.)

canonical: reproduced live that a **clean** bundled commit also creates this file, not only a
violating one — in a scratch fixture repo (`/tmp/otr-fixture-*`, not a path in this repository)
shaped like this one's `docs/specs/`/`gates/` layout, staged a new gate file together with its
`docs/specs/enforcement-boundary.md` row in one `git add ... && git commit ...` call, fed the
real commit output through `post` mode, then read the state dir — result: `ls -la $STATE_DIR`
showed a new `.json` file, `cat` on it returned `{"violations": []}` — the file exists despite
nothing being wrong with the commit.

canonical: `de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0:on-the-record/hooks/test_gate_registration_post_guard.py`
lines 109–141 (`test_pre_mode_warns_then_clears_once_row_lands`) already asserts
`json.loads(state_file.read_text())["violations"] == []` *after* resolution — the test suite's
own fixture already proves the file persists post-resolution — but derived: `grep -n "def test_"
on-the-record/hooks/test_gate_registration_post_guard.py` on the PR head — result: 7 tests, none
named around timing, short-circuit, or fast-path behavior. No test in the shipped suite checks
what that persistence does to the `pre`-mode fast path on a later call.

Net: the fast path's 0.96ms cost holds only on a machine/`$TMPDIR` that has never had a single
bundled commit touch a `gates/*.py`/`on-the-record/hooks/*.sh`/`.github/workflows/*.yml` file —
clean or violating. That condition is unlikely to survive this PR's own landing in this specific
repository, where such files are touched routinely (this PR is itself an example). After the
first such commit, every tool call in every session sharing that `$TMPDIR` pays the measured
~22x-34ms/call cost, with no self-healing mechanism, on the broadest-matcher `pre`-mode hook in
the system.

### 2. Weaker-promise legibility — confirmed legible

canonical: reproduced the bundled shape for real against a scratch fixture repo shaped like this
one (`docs/specs/enforcement-boundary.md`, `docs/specs/generated-paths.md`,
`on-the-record/hooks/hooks.json`, `gates/`) — ran a real `git add <new-gate-file> && git commit -m
"bundled: add new gate" -m "no registration row on purpose"`, fed that real commit's stdout
through `post` mode (exit 0, no stdout — correct, `post` never blocks), then fed a `Read`-tool
payload for the same session through `pre` mode. The literal `additionalContext` a session
receives:
```
gate-registration-guard (post-commit report, issue #2705): the following commit(s) already exist
in git history and cannot be blocked or reverted by this hook -- gate-registration-guard.sh only
sees a `git commit`'s staged set BEFORE the command runs, so a bundled `git add ... && git commit
...` call left nothing to refuse at the time it fired:
  - ff26c95: gates/new_gate.py: no row in docs/specs/enforcement-boundary.md
Add the missing row(s) above in a follow-up commit now. This report is the weaker half of a
deliberate two-guard split (issue #2705): gate-registration-guard.sh's own PreToolUse/`--cached`
check is unchanged and still REFUSES the commit outright when the file was staged in an earlier,
separate Bash call -- only the single-call bundled shape lands first and is reported after the
fact.
```
(The `gates/new_gate.py`/`ff26c95` names in the transcript above are the scratch fixture repo's
own untracked path and commit, not this repository's.) This names the commit that already
exists, states this hook did not and cannot prevent it, and names the sibling guard's stronger
promise by filename. acceptance: live `post`-then-`pre` reproduction above — result: all three
elements present in the actual text a session reads.

### 3. False-positive / control-case check

acceptance: clean bundled commit (row staged in the same `git add`), reproduced in item 1 above —
result: `post` mode wrote `{"violations": []}` and the next `pre`-mode call for that session
produced empty stdout — matches
`de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0:on-the-record/hooks/test_gate_registration_post_guard.py`
line 143 `test_bundled_add_and_commit_with_row_already_staged_is_clean`, independently reproduced
rather than restated.

acceptance: unbundled shape against the untouched `gate-registration-guard.sh` — derived: `git
diff origin/main...HEAD -- on-the-record/hooks/gate-registration-guard.sh` on the PR branch —
result: empty (byte-unchanged, confirmed independently, not restated from the PR body). Then, in
the same scratch fixture repo, staged a new unregistered gate file (fixture-only untracked path,
not in this repository) in one Bash call and fed a synthetic `PreToolUse`/`Bash`/`git commit`
payload to the unmodified script in a second call — result:
```
gate-registration-guard: newly-added gate/hook module(s) missing a spec registration row (issue #441/#684):
<fixture-path>: no row in docs/specs/enforcement-boundary.md
Fix the row in the same commit (docs/specs/enforcement-boundary.md, and for a hook script also docs/specs/generated-paths.md), then retry the commit.
exit: 2
```
Confirmed: the unbundled shape is still refused at exit 2, unchanged.

### 4. Enumeration re-derivation — the 6/1 split holds, but is incomplete

derived: `grep -lE '"?--cached"?|git show :|git diff --cached' on-the-record/hooks/*.sh` and the
equivalent over `$CLAUDE_PLUGIN_ROOT_CORE/hooks/*.sh` (17 files total in that directory) on the PR
head — result: the same 6 same-blind-spot hooks the PR's own table names
(`acceptance-command-real-run-guard.sh`, `live-fire-claim-real-run-guard.sh`,
`spec-index-preflight.sh`, `requirement-digest-preflight.sh`, `handbook-trigger-gate.sh`,
`trailer-gate.sh`) and the same 1 never-wired hook (`live-fire-test-guard.sh`) — derived:
`grep -rn "live-fire-test-guard" on-the-record/hooks/hooks.json on-the-record/hooks/pretooluse_dispatcher.py
on-the-record/hooks/pretooluse-dispatcher.sh` — result: no match in any of the three, exit 1 on
each, independently reproduced.

But re-checking the wiring status of the PR's own "2 Stop-event, not applicable" rows — which the
PR's record established only via `head -3`/`head -6` (confirming the event-type comment, never
checking `hooks.json`) — found both are **also never wired**, the same class of defect as
`live-fire-test-guard.sh`:

canonical: `de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0:docs/specs/enforcement-boundary.md` line 170
claims `deviation-log-guard.sh` is a live `Stop` hook, "appended to the `Stop` array immediately
after `stop-gate.sh`"; line 159 claims `product-capture-stopgate.sh` is likewise a live `Stop`
hook. canonical: read the `Stop` array out of `on-the-record/hooks/hooks.json` (`json.load(...)
['hooks']['Stop']`) on both the PR-head checkout and the live plugin's own copy
(`/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/on-the-record/hooks/hooks.json`, which
`diff` against the repo checkout shows differs only by this PR's own new
`gate-registration-post-guard.sh` lines, nothing else) — result: exactly 3 entries in the `Stop`
array, `stop-poll-rearm.sh`, `stop-gate.sh`, `skill-verdict-guard.sh`. Neither
`deviation-log-guard.sh` nor `product-capture-stopgate.sh` appears in either copy. derived:
`grep -rl "deviation-log-guard\.sh\|product-capture-stopgate\.sh" --include="*.py" --include="*.json"
--include="*.yaml" --include="*.yml" .` over the whole repo — result: only comment mentions in
sibling scripts and doc rows, no wiring entry anywhere.

This is the same #909-class defect the PR already flags for `live-fire-test-guard.sh` — the
enumeration's own methodology checked wiring only where the blind-spot hunt made it directly
relevant (`live-fire-test-guard.sh`, which is `PreToolUse`-typed), not uniformly across the "not
applicable" rows too — so the PR's "1 orphan hook" count understates what its own sweep already
touched.

Two further narrative-only inaccuracies, neither changing the table's correct "6" total: the
PR's recap sentence ("2 in on-the-record at the general level plus
`requirement-digest-preflight.sh`'s narrower variant, 2 in tokenmaxxxer-core") names only 3
on-the-record hooks by implication, omitting `spec-index-preflight.sh`. And the "all other core
hooks" grouped row cites `ordering-norm-gate.sh` — derived: `ls
$CLAUDE_PLUGIN_ROOT_CORE/hooks/ordering*` — result: only `ordering-gate.sh` exists on disk; the
`ordering-norm-gate.sh` name is stale (a repo doc title referencing an issue #257 fold of that
name into `ordering-gate.sh` was found by filename search, not independently re-verified beyond
confirming `ordering-norm-gate.sh` itself is absent from disk).

## Why

The task brief asked me to re-derive, hardest first, not restate. The overhead claim is where a
plausible, benchmarked-against-a-baseline number (0.96ms) hides a structural one-way-door problem
that only surfaces when the fast path is exercised *after* realistic use, not on a pristine
machine — exactly the failure mode the brief named. I verified it by reproducing the actual state
transition (bundled commit -> state file written, resolved or not -> next `pre` call) against the
real shipped script, not by reasoning about the code in the abstract.

## What did not work

None — every reproduction in this record used the PR head's actual scripts via `git worktree`,
and every control case (clean bundled commit, unbundled shape, unchanged guard) was reproduced
live rather than assumed from the PR's own claims.

## Upstream basis

- `de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0:on-the-record/hooks/gate-registration-post-guard.sh`,
  `de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0:on-the-record/hooks/hooks.json`,
  `de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0:on-the-record/hooks/test_gate_registration_post_guard.py`.
  sha: `de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0`
- `de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0:docs/issue-2705/reports/architecture-interface-contract-shape-3f3d4ef5.md`
  — the PR's own enumeration table and overhead claim, re-derived rather than restated in this
  record. sha: `de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0`

## Open findings

1. **[blocking-for-the-claim] Pre-mode fast path is a one-way door, not a steady-state 0.96ms
   cost.** canonical: item 1 above — `_save(data)` in `post` mode writes the state file
   unconditionally, nothing ever deletes a state file, and the `pre`-mode short-circuit checks
   file existence only. Resolution path: either (a) delete the state file (not just empty its
   `violations` list) once `still_open` is empty in `pre` mode, and skip writing a state file in
   `post` mode when no violation was found, or (b) have the bash fast path check a cheap
   non-empty sentinel (e.g. file size) rather than bare existence, so a `{"violations": []}` file
   doesn't defeat it. Either fix keeps the claim true in the case that actually matters — steady
   state after the first commit — not only before it.
2. **[undercounted, not blocking] Enumeration's "1 orphan hook" should be "at least 3."**
   canonical: item 4 above — `deviation-log-guard.sh` and `product-capture-stopgate.sh` are
   claimed live in `docs/specs/enforcement-boundary.md` but absent from `hooks.json`'s `Stop`
   array. Not a regression from this PR and out of its fix scope (it touches neither file), but
   the "enumeration plus the command that established its verdict" acceptance criterion is not
   fully met while these two rows cite only an event-type check, not a wiring check.
3. **[cosmetic] Two narrative-only inaccuracies in the PR's own record** — canonical: item 4
   above — the "6" recap sentence omits `spec-index-preflight.sh` by name, and the "all other
   core hooks" row cites a filename (`ordering-norm-gate.sh`) that does not exist on disk. The
   table itself is correct in both cases; only the prose restating it is off.

## Next steps

`loop_state: landed`. Per the task brief ("Open a PR with your record even if you find nothing"),
delivery is this record plus its PR — findings are reported, not fixed, in this round. Finding #1
is real enough that the PR should not land carrying "no overhead increase" without either a fix
or an explicit caveat narrowing that claim to the pristine-state case. Findings #2 and #3 are
informational for whoever next touches this issue's enumeration or the
`deviation-log-guard.sh`/`product-capture-stopgate.sh` wiring gap.

## Standing invariants (re-derived independently)

- **No return of the retired role axis**: derived: `git diff origin/main...pr-2864 | grep -inE
  "role.?axis|CLAUDE_ROLE.*axis|role_axis"` — result: only self-referential hits inside the PR's
  own record file (describing this same check), no hit in any code/spec file.
- **Failing-test set vs. `origin/main`, as sets of names**: derived: `python3 -m pytest test/
  gates/ on-the-record/ -q` run separately on the PR head worktree and a fresh `origin/main`
  worktree, `^FAILED` lines captured from each, sorted, and diffed as plain text — result:
  `diff /tmp/pr_failed.txt /tmp/main_failed.txt` exited 0 (identical 15-line sets). Counts:
  acceptance: `python3 -m pytest test/ gates/ on-the-record/ -q` (PR head) — result: `15 failed,
  505 passed, 3 xfailed`; acceptance: same command (`origin/main` worktree) — result: `15 failed,
  498 passed, 3 xfailed`. `505 - 498 = 7`, matching this PR's own new test file — acceptance:
  `python3 -m pytest on-the-record/hooks/test_gate_registration_post_guard.py -q` (PR head) —
  result: `7 passed`.
- **No overhead increase**: false in the realistic case, true only in the pristine one — see
  finding #1 and item 1 above for the executed measurement.
- **Monitor/watch machinery unbroken and not quieter**: acceptance: `python3 -m pytest test/ -k
  "fleet_scan or monitor or watch" -q` (PR head) — result: `15 passed`; acceptance: same command
  (`origin/main` worktree) — result: `15 passed` — identical pass count on both. "Not quieter":
  derived: `grep -n "hook_fires\|hook-fires"
  on-the-record/hooks/gate-registration-post-guard.sh on-the-record/hooks/gate-registration-guard.sh`
  — result: no match in either file — the new hook is exactly as silent to the fires-log as its
  unmodified sibling already was, not a newly introduced gap.

skill-verdict: adversarial-review — applied: invoked; this session is the structurally-independent
evaluator for PR #2864's own deliverable (round 4 of this issue), so every claim above was
re-derived by running the PR head's actual shipped scripts rather than restating or trusting the
PR's own record — per the skill's guidance to produce located, reproduced findings over a
"looks good" pass.
