---
issue: 3083
role: adversarial-review+test-depth-audit+defect-verification-independence-from-upstream-verdicts-928476fd
author: adversarial-review+test-depth-audit+defect-verification-independence-from-upstream-verdicts-928476fd
skills: adversarial-review (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12))
verifies_subject: true  # independent, builder-blind verification of PR #3089's own deliverable against issue #3083
code_under_review: e5978d52615388389d984b7bccece82b65eb82a6
type: defect-verification-record
breaking: false
verdict: All 4 acceptance criteria Present, both must-not clauses held.
  See "Verdict summary" table below for the per-criterion evidence.
loop_state: landed
upstream:
  - path: PR #3089 (github.com/tokenmaxxxxer/on-the-record/pull/3089),
      fetched as local ref pr-3089-verify, head commit d89b74dc -- not
      merged to main, untracked in this repo's own tree
    sha: d89b74dc2ef58bf9196cfd1e6cabbdc757f424b9
  - path: lifecycle.py (unmodified by PR #3089) at the shared base commit
    sha: 573e7382282be24439c223c1603be648dd0e158f
---

# issue-3083 — adversarial-review+test-depth-audit+defect-verification-independence-from-upstream-verdicts-928476fd record

## What was done

Independent, builder-blind verification of PR #3089 against issue #3083's
Acceptance and must-not sections. Did not edit, merge, or comment on PR
#3089.

canonical: `gh pr view 3089 --json headRefName,baseRefName,mergeable,commits`
output, read this session — result: `headRefName:
issue-3083/diagnose-first+silent-failure-audit+test-derivation-3d40ffc9`,
`baseRefName: main`, `mergeable: MERGEABLE`, 2 commits (`e5978d52`,
`d89b74dc`).

**Setup**: `git fetch origin pull/3089/head:pr-3089-verify` (resolves to
`d89b74dc`), `git worktree add /tmp/pr3089-verify pr-3089-verify` (PR's
own state) and `git worktree add /tmp/base-573e --detach 573e7382`
(pre-fix base), both removed with `git worktree remove` at the end of
this session; no push, no edit, no merge to either ref.

Note on paths cited below: `gates/probe_hooks_additive_survives_merge.py`
(this issue's new probe file) is untracked in this repo's own working
tree throughout this record — it exists only on PR #3089's branch,
added at commit e5978d52, and every command below that names it ran
inside the separate `/tmp/pr3089-verify` or `/tmp/probe_prefix_check`
worktrees/copies, never in this repo's own checkout.

### 1. The four acceptance checks, run directly against the PR's own worktree

canonical: `python3 -m pytest tests/test_spawn_gate_wiring.py -q` run at
`/tmp/pr3089-verify` (commit `d89b74dc`), this session
Acceptance requirement met — checked: `python3 -m pytest tests/test_spawn_gate_wiring.py -q` — result:
```
27 passed in 9.14s
```

canonical: `python3 -m pytest tests/test_respawn_deliverable_gate.py -q`
run at `/tmp/pr3089-verify` (commit `d89b74dc`), this session
Acceptance requirement met — checked: `python3 -m pytest tests/test_respawn_deliverable_gate.py -q` — result:
```
13 passed in 0.94s
```

canonical: `python3 -m pytest tests/ -q` run at `/tmp/pr3089-verify`
(commit `d89b74dc`), this session
Acceptance requirement met — checked: `python3 -m pytest tests/ -q` — result:
```
187 passed, 2 warnings in 9.36s
```

canonical: `python3 gates/probe_hooks_additive_survives_merge.py`
(untracked here, see note above) run at `/tmp/pr3089-verify` (commit
`d89b74dc`), this session
Acceptance requirement met — checked: `python3 gates/probe_hooks_additive_survives_merge.py` (untracked here) — result:
```
ok
exit=0
```

derived: comparing the 4 figures above against PR #3089's own reported
Test plan (27/13/187 passed, probe `ok`) — result: exact match, but
independently re-run rather than cited from the PR body.

**All 4 acceptance criteria: Present.**

### 2. Cluster A must-not, checked by experiment (removal case)

The issue's must-not requires the additive guard to still fail if a
future edit removes a PostToolUse registration. Removed a real entry
from the actual `on-the-record/hooks/hooks.json` in the PR worktree
(`/tmp/pr3089-verify`) and reran the real test, then restored the file.

canonical: this session's own script and its output, run at
`/tmp/pr3089-verify`
```
$ python3 -c "
import json
p = 'on-the-record/hooks/hooks.json'
d = json.load(open(p))
for b in d['hooks']['PostToolUse']:
    if b.get('hooks'):
        removed = b['hooks'].pop(0)
        print('removed:', removed)
        break
json.dump(d, open(p, 'w'), indent=2)
"
removed: {'type': 'command', 'command': '${CLAUDE_PLUGIN_ROOT}/hooks/fail-open-wrapper.sh ${CLAUDE_PLUGIN_ROOT}/hooks/retry-loop-bound.sh post'}
```

derived: `python3 -m pytest tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present -q`
against that mutated `hooks.json` — result:
```
FAILED ... AssertionError: PostToolUse commands removed by this change: {...}
1 failed in 0.99s
```

derived: the same command against the restored (`cp` from backup)
`hooks.json` — result: `1 passed in 0.83s`

**Cluster A must-not: Present.** The extracted guard function still
fails on a real removal, not just the probe's synthetic sets.

canonical: `tests/test_spawn_gate_wiring.py:391-403` at commit `d89b74dc`
(the extracted function, quoted verbatim from the PR diff this session
already fetched):
```
def _assert_post_tool_use_additive(before_commands: set, after_commands: set) -> None:
    missing = before_commands - after_commands
    assert missing == set(), (
        "PostToolUse commands removed by this change: %s" % missing)
```
This is the same `missing = before - after; assertEqual(missing, set())`
logic the pre-fix file already had (per the issue body's own quote of
it) — only the separate `assertGreater(len(after), len(before))` line
was removed, not this one, satisfying the must-not's "not by loosening"
condition.

### 3. The new probe against the pre-fix and post-fix test file

canonical: this session's own commands and output
```
$ git show 573e7382:tests/test_spawn_gate_wiring.py > /tmp/test_spawn_gate_wiring_prefix.py
$ grep -c "_assert_post_tool_use_additive" /tmp/test_spawn_gate_wiring_prefix.py
0
```

derived: copied the probe file (`gates/probe_hooks_additive_survives_merge.py`,
untracked here, see note in "What was done") and the pre-fix test file
into a standalone `/tmp/probe_prefix_check/` tree (`gates/` and `tests/`
subdirs) and ran it from there — result:
```
Traceback (most recent call last):
  ...
    wiring._assert_post_tool_use_additive(identical, identical)
AttributeError: module 'test_spawn_gate_wiring' has no attribute '_assert_post_tool_use_additive'
exit=1
```

This confirms the probe genuinely fails (non-zero exit) against the
pre-fix file, not vacuously. Section 1 above already confirmed (`ok`,
exit 0) that the same probe passes against the post-fix file, and that
one run exercises both of the issue's specified scenarios internally —
confirmed by reading the probe's own `main()` body (quoted next).

canonical: `gates/probe_hooks_additive_survives_merge.py:264-291`
(untracked here) at commit `d89b74dc` (quoted verbatim from the PR diff
this session already fetched):
```
    try:
        wiring._assert_post_tool_use_additive(identical, identical)
    except AssertionError as exc:
        _fail("guard rejected the post-merge state (before == after, "
              f"nothing removed or added): {exc}")
    ...
    try:
        wiring._assert_post_tool_use_additive(before, after_with_removal)
    except AssertionError:
        pass
    else:
        _fail("guard failed to detect a removed PostToolUse command "
              "(the regression that motivated this file, PR #2872)")
```

**Minor quality note (not an acceptance failure)**: the probe's pre-fix
failure mode is an unhandled `AttributeError` traceback, not the
probe's own designed `FAIL: ...` message. It still satisfies "must fail
against the current test file" (issue's exact wording, non-zero exit
either way), but a reader running it pre-fix sees a raw traceback rather
than the probe's intended diagnostic.

### 4. Cluster B — re-derived independently, not accepted from PR #3089's own diagnosis (load-bearing)

Per defect-verification-independence-from-upstream-verdicts, treated PR
#3089's "respawn path intact, no live defect" claim as a claim to
re-test, not a settled fact.

canonical: `lifecycle.py:173` at commit `573e7382` (unmodified by PR
#3089):
```
RESPAWN_CONSECUTIVE_CONFIRMATIONS = 2
```

canonical: `lifecycle.py:537-550` at commit `573e7382` (unmodified by PR
#3089), the debounce block:
```
    confirm_prior = state.get(key, {})
    if verdict != "crashed":
        if confirm_prior.get("crash_confirms"):
            state[key] = {**confirm_prior, "crash_confirms": 0}
            _sp._respawn_state_save(state)
        return
    crash_confirms = confirm_prior.get("crash_confirms", 0) + 1
    if crash_confirms < _sp.RESPAWN_CONSECUTIVE_CONFIRMATIONS:
        state[key] = {**confirm_prior, "crash_confirms": crash_confirms}
        _sp._respawn_state_save(state)
        print(f"[watchdog] {key}: crashed 판정 {crash_confirms}/"
              f"{_sp.RESPAWN_CONSECUTIVE_CONFIRMATIONS}회 연속 확인 대기 중 — "
              "아직 재스폰하지 않음", file=sys.stderr)
        return
```
This matches PR #3089's own citation of the same lines.

derived: `git diff --name-only 573e7382 d89b74dc` — result:
```
docs/issue-3083/reports/diagnose-first+silent-failure-audit+test-derivation-3d40ffc9.md
gates/probe_hooks_additive_survives_merge.py
tests/test_respawn_deliverable_gate.py
tests/test_spawn_gate_wiring.py
```
(the `gates/` and `docs/` entries above are untracked here, see note in
"What was done" — quoted because they are the PR's own diff output).
`lifecycle.py` is not in this list — PR #3089 does not touch production
respawn code, only two test files and a new gate script.

Constructed a genuinely crashed session **from scratch**, independent of
PR #3089's own test fixtures and independent of the pre-existing sibling
test it cites — a standalone script that builds its own throwaway
bare-remote + clone, a real dead pid, and a real `session-start` event,
then calls `spawn.session_end_verdict()` directly (not mocked) before
ever calling `_auto_respawn_check`:

canonical: `/tmp/verify_cluster_b.py`, written and run by this session,
core of `build_crashed_session()`:
```python
def build_crashed_session(tmp: Path):
    remote = tmp / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    work = tmp / "work"
    subprocess.run(["git", "clone", "-q", str(remote), str(work)], check=True)
    (work / "a.txt").write_text("1")
    _git(work, "add", "a.txt")
    _git(work, "commit", "-q", "-m", "c1")
    events_path = spawn._events_path(str(work))
    events_path.write_text(
        '{"ts": 1, "type": "session-start", "detail": {"pid": %d}}\n' % DEAD_PID)
```

derived: `python3 /tmp/verify_cluster_b.py` run at `/tmp/pr3089-verify`,
this session — result:
```
PASS: not called before threshold, called exactly once at threshold
PASS: skip reported in stderr and ledger, never silent
```
The script asserts, and this run confirmed: `session_end_verdict()`
genuinely returns `"crashed"` for this fixture; `_respawn_or_cap.call_count == 0`
after 1 crashed verdict; `_respawn_or_cap.call_count == 1` after the 2nd
consecutive crashed verdict on the same `state` dict; and, in a second
fixture with an existing deliverable PR, the skip is reported (`"4242"`
present in captured stderr) and `ledger_write` is called exactly once.

**Mutation check** (test-depth-audit skill, Step 4): patched
`lifecycle.py`'s debounce condition to always-false (debounce
permanently disabled) and reran both PR #3089's own test file and the
independent script above, then reverted.

derived: `python3 -m pytest tests/test_respawn_deliverable_gate.py -q`
with the mutation applied, run at `/tmp/pr3089-verify` — result:
```
3 failed, 10 passed in 0.92s
FAILED ...test_respawn_proceeds_without_deliverable_still_respawns_genuine_crash
FAILED ...test_respawn_skip_is_reported_names_the_pr_in_stderr_and_ledger
FAILED ...test_respawn_proceeds_without_deliverable_when_gate_finds_none
```

derived: `python3 /tmp/verify_cluster_b.py` with the same mutation
applied — result:
```
AssertionError: BUG: _respawn_or_cap called after only 1 crashed verdict (threshold is 2) -- debounce not enforced
```

derived: `cp /tmp/lifecycle.py.bak lifecycle.py` (revert) then
`python3 -m pytest tests/test_respawn_deliverable_gate.py -q` — result:
`13 passed in 0.98s` (back to the pre-mutation state).

**Test-depth-audit finding (Surface, not a defect)**: the mutation run
directly above shows `3 failed, 10 passed` (3+10=13, matching the file's
full passing count from §1). The one that kept passing under the
mutation is
`test_respawn_skip_is_reported_never_silent_even_without_pr_number` in
`tests/test_respawn_deliverable_gate.py`.

canonical: `tests/test_respawn_deliverable_gate.py:266-282` at commit
`d89b74dc` (quoted verbatim from the PR diff this session already
fetched):
```
    def test_respawn_skip_is_reported_never_silent_even_without_pr_number(self):
        found = {"number": None, "branch": "issue-9002/implementation", "state": "MERGED"}
        entry = self._entry()
        state = {}
        stderr = io.StringIO()
        with mock.patch.object(spawn, "_subject_has_deliverable", return_value=found), \
             mock.patch.object(spawn, "_respawn_or_cap") as respawn_or_cap, \
             contextlib.redirect_stderr(stderr):
            self._confirm_crash(state, entry)
            respawn_or_cap.assert_not_called()
            spawn._auto_respawn_check("issue-9002/demo", entry, state)
        respawn_or_cap.assert_not_called()
        self.assertIn("issue-9002/implementation", stderr.getvalue())
```
`_subject_has_deliverable` is mocked to return `found` for every call in
this block, including the warm-up call inside `_confirm_crash`. Because
a found deliverable suppresses `_respawn_or_cap` regardless of which
call crossed the debounce threshold, this test's two assertions
(`assert_not_called()`, `"issue-9002/implementation" in stderr`) hold
identically whether the debounce fired on the warm-up call or the final
call — the mutation above proved this by leaving it passing. It still
correctly verifies "a skip is reported, never silent"; it does not, by
itself, prove the debounce specifically gates this skip, the way its
three siblings do. Not introduced by this PR: the assertions' shape is
unchanged from the pre-fix version quoted in PR #3089's own record; the
PR only added the `_confirm_crash` warm-up call needed to reach this
code path at all.

**Cluster B verdict, independently confirmed: the respawn path is
intact.** A genuinely crashed session (constructed from scratch, not
imported from any test fixture) is not respawned after one crashed
verdict and is respawned after two, matching
`RESPAWN_CONSECUTIVE_CONFIRMATIONS = 2`.

**Cluster B must-not: Present.** `lifecycle.py` is untouched by the PR
(confirmed by the `git diff --name-only` above), so no assertion was
loosened to match a broken respawn path.

### 5. `tests/` vs `test/` — counted separately

derived: `python3 -m pytest test/ -q` run at `/tmp/pr3089-verify`
(commit `d89b74dc`) — result:
```
15 failed, 548 passed, 3 xfailed in 32.21s
```

derived: `python3 -m pytest test/ -q` run at `/tmp/base-573e` (commit
`573e7382`, pre-fix) — result:
```
15 failed, 548 passed, 3 xfailed in 32.04s
```

derived: `diff` of the two runs' sorted `FAILED` line lists (`grep ^FAILED | sort`
on each, then `diff`) — result: empty (byte-identical failing-test set,
same test names on both). PR #3089 neither causes nor fixes any `test/`
(singular) failure.

derived: `python3 -m pytest tests/ -q` run at `/tmp/base-573e` (commit
`573e7382`, pre-fix) — result:
```
5 failed, 182 passed, 2 warnings in 6.31s
```
Same 5 named failures as PR #3089's own reported "before" state and as
this session's independent re-run above; the issue body's own quoted
figure ("5 failed, 105 passed") undercounts the passed total relative to
both this session's and PR #3089's run of the identical commit — not a
PR #3089 defect, since PR #3089's own "before" figure and this session's
independent one agree with each other and disagree with the issue text
in the same direction.

**Counts, reported separately:**

| suite | pre-fix (573e7382) | PR #3089 head (d89b74dc) |
|---|---|---|
| `tests/` | 5 failed, 182 passed | 0 failed, 187 passed |
| `test/`  | 15 failed, 548 passed, 3 xfailed | 15 failed, 548 passed, 3 xfailed (identical set) |

## Why

Followed defect-verification-independence-from-upstream-verdicts
throughout: every acceptance check was re-run directly rather than cited
from PR #3089's Test plan checklist. Cluster B — flagged as load-bearing
in the assigning prompt — was re-derived from a session constructed
independently of both PR #3089's test file and the sibling test it
cites, then stress-tested by mutation (test-depth-audit Step 4) rather
than accepted on the strength of the citation alone. The Surface finding
in §4 came directly from that mutation step, not from reading the test's
assertions alone.

## What did not work

None.

## Upstream basis

canonical: `gh issue view 3083` output, read this session — full body
(Acceptance section's 4 `check:` lines, both must-not clauses) already
quoted and addressed individually, section by section, in "What was
done" above.

- Issue #3083.
- PR #3089 (github.com/tokenmaxxxxer/on-the-record/pull/3089), local ref
  `pr-3089-verify`, head `d89b74dc2ef58bf9196cfd1e6cabbdc757f424b9` — not
  merged, untracked in this repo's own tree, not edited or merged by
  this session (all PR-branch commands ran in a separate `/tmp/pr3089-verify`
  worktree, never this repo's own working tree).
- `lifecycle.py` at the shared base commit
  `573e7382282be24439c223c1603be648dd0e158f`, read directly (lines
  173, 506-606) to independently confirm the debounce mechanism.

## Open findings

1. **Surface** (not a defect, not a regression):
   `tests/test_respawn_deliverable_gate.py`'s
   `test_respawn_skip_is_reported_never_silent_even_without_pr_number`
   does not, by itself, prove the debounce gates this particular skip
   path. Resolution path: mock `_subject_has_deliverable` to return
   `None` during the warm-up call and only `found` on the final call, so
   a debounce break would show up here too. Not blocking — the property
   it currently verifies ("skip is reported, never silent") still holds.
2. `test/` (singular) has pre-existing failures — out of this issue's
   and this PR's scope per issue #3091 (per the assigning prompt). No
   action needed from this PR.

derived: `python3 -m pytest tests/test_respawn_deliverable_gate.py -q`
with `lifecycle.py`'s debounce mutated to always-false (already run and
quoted in full in §4 above) — result: this one test still passes while
its siblings fail; that divergence is finding 1's basis.

derived: `diff` of the sorted `test/` `FAILED` line lists between commit
`573e7382` and `d89b74dc` (already run and quoted in full in §5 above)
— result: empty; that identical set is finding 2's basis.

## Next steps

None further — see "Verdict summary" table below for the per-criterion
evidence.

## Verdict summary

canonical: all six rows below cite the exact command output already
quoted in §1-§4 above (independently re-run this session, not cited from
PR #3089's own Test plan or record). The probe path in row 4 is
untracked here, see note in "What was done".

| Criterion | Verdict | Basis |
|---|---|---|
| check: `pytest tests/test_spawn_gate_wiring.py -q` | Present | §1 |
| check: `pytest tests/test_respawn_deliverable_gate.py -q` | Present | §1 |
| check: `pytest tests/ -q` | Present | §1 |
| check: `python3 gates/probe_hooks_additive_survives_merge.py` | Present | §1 (post-fix pass) + §3 (pre-fix fail, both internal scenarios) |
| must-not: Cluster A guard must still catch a removal | Present | §2, real `hooks.json` removal experiment |
| must-not: Cluster B fix must not paper over a live defect | Present | §4, independently constructed crashed session + mutation testing |

derived: §4's mutation run (`python3 -m pytest tests/test_respawn_deliverable_gate.py -q`
with the debounce mutated) — result already quoted in full in §4 above:
```
3 failed, 10 passed in 0.92s
```
3/4 = 75% of the fixed tests are Genuine Assertion (fail under the
mutation); the remaining one is Mock-Dominated on the debounce axis
specifically (passes under the same mutation) — this is the basis for
both skill-verdict lines below.

skill-verdict: adversarial-review — applied: invoked; treated PR #3089's
own record and Test plan as a claim to independently re-test rather than
a settled fact throughout §1-§5 above, per its blind-evaluation stance.
skill-verdict: test-depth-audit — applied: invoked; the mutation-testing
result immediately above classified the 4 fixed respawn tests as 3
Genuine-Assertion plus 1 Surface/Mock-Dominated-on-the-debounce-axis,
cited by file:line in §4 with a concrete mutation reproduction.
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; Cluster B (§4), the load-bearing claim, was re-derived
from a from-scratch independent script rather than cited from PR #3089's
own diagnosis or its cited sibling test, and the Surface finding above
is documented with the same evidentiary weight as the Present verdicts
rather than as a footnote, per the skill's equal-rigor requirement.
