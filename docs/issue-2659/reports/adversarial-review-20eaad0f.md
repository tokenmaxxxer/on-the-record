---
issue: 2659
role: adversarial-review-20eaad0f
author: adversarial-review-20eaad0f
skills: adversarial-review (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: true
loop_state: landed
upstream:
  - path: on-the-record/hooks/deliverable-guard.sh
    sha: 490dc6197d97d3184c2a1ea376a70c9e5ce07ec4
  - path: test/test_deliverable_guard_priorities_shard.py
    sha: 490dc6197d97d3184c2a1ea376a70c9e5ce07ec4
---

# issue-2659 — adversarial-review-20eaad0f record

## What was done

Independent adversarial verification of PR #2752 against issue #2659's three acceptance checks.

canonical: `gh pr view 2752 --repo tokenmaxxxer/on-the-record` — result:
```
state:	OPEN
number:	2752
url:	https://github.com/tokenmaxxxer/on-the-record/pull/2752
```

Reproduction ran in throwaway clones/worktrees/submodules under `/tmp`, executed by four parallel background workers, never touching this session's own working tree. Every claim below is re-derived from a worker's own command+output transcript, not restated from the PR's description or its own record file.

### Acceptance 1 — clone / linked worktree / submodule reach the same verdict

acceptance: 12-run matrix — 2 states (merge-base, PR head) x 3 layouts (ordinary clone, linked worktree, submodule) x 2 payload shapes (deny-shaped write to a fixture path, allow-shaped write to `docs/specs/approvers.md`) — `bash on-the-record/hooks/deliverable-guard.sh < payload.json`, exit 2 = deny, exit 0 = allow (convention confirmed by reading the hook's own `trap` wrapper: any non-{0,2} exit is also forced to 2) — result:

```
payload deny fixture: {"tool_input":{"file_path":"<repo>/src/x.py"}}   (not a repo path -- a
  throwaway file inside each worker's own /tmp clone, never committed anywhere)
payload allow fixture: {"tool_input":{"file_path":"<repo>/docs/specs/approvers.md"}}

RUN ordinary-BASE / deny    -> EXIT CODE: 2
RUN ordinary-BASE / allow   -> EXIT CODE: 0
RUN worktree-BASE / deny    -> EXIT CODE: 0   <-- BUG: fail-open
RUN worktree-BASE / allow   -> EXIT CODE: 0
RUN submodule-BASE / deny   -> EXIT CODE: 2
RUN submodule-BASE / allow  -> EXIT CODE: 2   <-- BUG: false-positive over-deny
RUN ordinary-PR2752 / deny  -> EXIT CODE: 2
RUN ordinary-PR2752 / allow -> EXIT CODE: 0
RUN worktree-PR2752 / deny  -> EXIT CODE: 2   <-- fixed
RUN worktree-PR2752 / allow -> EXIT CODE: 0
RUN submodule-PR2752 / deny -> EXIT CODE: 2
RUN submodule-PR2752 / allow-> EXIT CODE: 0   <-- fixed
```

derived: full 12-run transcript (command, stdin, cwd, stdout, stderr, exit code) reproduced under `/tmp/ordinary-{BASE,PR2752}`, `/tmp/worktree-{BASE,PR2752}`, `/tmp/submodule-super-{BASE,PR2752}/sub` by the matrix-reproduction background worker (task id a6d55edecd9df124f) via `git clone https://github.com/tokenmaxxxer/on-the-record.git /tmp/matrix-base && git fetch origin pull/2752/head:pr-2752`.

Precondition confirmed with `file .git` in all 6 checkout dirs:
```
/tmp/ordinary-BASE/.git: directory
/tmp/ordinary-PR2752/.git: directory
/tmp/worktree-BASE/.git: ASCII text
/tmp/worktree-PR2752/.git: ASCII text
/tmp/submodule-super-BASE/sub/.git: ASCII text
/tmp/submodule-super-PR2752/sub/.git: ASCII text
```
— ordinary clones show a `.git` directory; worktree/submodule show a `.git` file (gitdir pointer), the exact shape a bare `os.path.isdir` walk cannot resolve.

At BASE the two non-ordinary layouts fail in *opposite* directions from the same root defect: worktree has no directory-shaped `.git` anywhere above it, so the old walk finds nothing and falls through to the old `sys.exit(0)` fallback (fail-open); submodule's walk instead climbs past the submodule's file-shaped `.git` and locks onto the *superproject's* real `.git` directory, misidentifying the superproject as the repo root and wrongly denying even an exempt write. At the PR head all 6 rows match the ordinary-clone row exactly. **Acceptance 1 holds** (derived: table above).

### Acceptance 2 — root genuinely undeterminable -> refusal, not allow

Two independent angles, both against the PR head.

**(a) No repository anywhere in the ancestry** (matrix worker): a directory whose own `.git` is an empty regular file (invalid gitdir pointer), no valid `.git` up to `/`.

acceptance: `bash deliverable-guard.sh < payload.json` for a deny-shaped and an allow-shaped payload (absolute `file_path`), BASE script vs PR-head script — result:

```
BASE script,   deny-shaped payload  -> EXIT CODE: 0, stdout/stderr empty
BASE script,   allow-shaped payload -> EXIT CODE: 0, stdout/stderr empty
PR-head script, deny-shaped payload -> EXIT CODE: 2
  stderr: orchestrate: could not determine whether /tmp/no-repo-dir/src/x.py is
  inside a git repository (git rev-parse --is-inside-work-tree exited 128: fatal:
  invalid gitfile format: /tmp/no-repo-dir/.git) -- cannot verify this write is
  outside a board repo, denying rather than silently allowing it through.
PR-head script, allow-shaped payload -> EXIT CODE: 2 (same stderr shape, path substituted)
```

**(b) git subprocess itself cannot answer** (failure-mode worker, task id a69fd96515c9e855c), against a deny-shaped (non-exempt) payload inside a real repo, five conditions:

acceptance: `env PATH=<broken-or-fake-git> bash deliverable-guard.sh < payload-deny-boardrepo.json` for (i) git missing from PATH, (ii) a fake `git` exiting 128 with stderr, (iii) a fake `git` exiting 0 with garbage stdout, (iv) a fake `git` exiting 0 with empty stdout, (v) a fake `git` sleeping 15s against the code's own `subprocess.run(..., timeout=10)` — result:

```
(a) git missing:         EXIT=2  "could not determine ... (git rev-parse did not run) ... denying"
(b) git errors (128):    EXIT=2  "could not determine ... exited 128: fatal: fake error ... denying"
(c1) git garbage stdout: EXIT=2  "could not determine ... exited 0:  ... denying"
(c2) git empty stdout:   EXIT=2  "could not determine ... exited 0:  ... denying"
(d) git hangs 15s:       EXIT=2  "could not determine ... (git rev-parse did not run) ... denying"
                          real 0m20.058s  user 0m0.024s  sys 0m0.016s
```
derived: the ~20s wall-clock for (d), against a 10s `timeout=10` declared in the source, is consistent with two independent `_run_git` calls (exemption-resolution, then activation) each being killed at the timeout rather than a full 2x15s=30s hang, confirming the timeout is enforced in the actual subprocess call, not merely present as a dead literal in the source.

Both angles (a) and (b) confirm the fail-closed behavior for the activation-check code path.

Acceptance 2 holds for both angles tested. It does **not** hold universally — see Open finding 1 below.

### Acceptance 3 — ordinary checkouts unchanged

acceptance: `python3 -m pytest test/ -q`, fresh clones of `origin/main` vs the PR head (test-suite worker, task id abf70375f3d21f85e), stable across 3 reruns each — result:

```
origin/main:  15 failed, 403 passed, 6 xfailed
pr-2752:      16 failed, 410 passed, 3 xfailed
```

derived: `diff` of the two runs' failing-name lists (not counts, per this task's explicit requirement) shows the PR head's failing set equals origin/main's 15 names plus exactly one more — a test named `test_approval_gate_sh_is_byte_identical` in `test/test_auto_approval_shadow_wiring.py` — investigated rather than accepted at face value, see Invariant 2 below. The ordinary-clone rows of the Acceptance-1 matrix (deny=2/allow=0, both BASE and PR head, table above) additionally satisfy this acceptance's literal "pass/refuse pair before and after" wording.

## Standing invariants

**1. No return of the retired role axis, in any reshaped form.**

derived: `git diff origin/main pr-2752 | grep -n -w -i 'role' | wc -l` (invariants worker, task id abab3a6c68b6a7fcb) — result:
```
260
```
Isolating PR #2752's own commits against its merge-base instead of the moved-forward `origin/main`:
derived: `git diff 00aeaae4 pr-2752 | grep -n -w -i 'role' | wc -l` — result:
```
5
```
all inert — a `role:` docs-frontmatter key (explicitly out of scope for the role-to-skill rename per the prior #2741 verification), plus 4 lines of English prose in the new report describing the absence of role-axis changes.
derived: `git diff 00aeaae4 pr-2752 -- on-the-record/hooks/deliverable-guard.sh test/test_deliverable_guard_priorities_shard.py test/test_deliverable_guard_worktree_submodule.py | grep -n -w -i role` — result:
```
(no output)
```
**Verdict: clean.** The 260-hit naive count is a stale-branch artifact (see invariant 2), not evidence against this PR.

**2. No new bug — failing-test SET vs origin/main, as sets of names.**

Not identical as raw sets against the naive `origin/main..pr-2752` diff — one extra name (Acceptance 3). Investigated independently by two workers from two separate clones:
```
git merge-base origin/main pr-2752 -> 00aeaae457e82b5504421615eca04587b45de577
git diff 00aeaae4 pr-2752 -- on-the-record/hooks/approval-gate.sh -> (empty, both clones)
git diff 00aeaae4 origin/main -- on-the-record/hooks/approval-gate.sh -> shows the role-to-skill
  rename (PR #2746, merged as e1b35a53, after pr-2752's branch point)
```
derived: the two commands above, run independently by the test-suite worker and the invariants worker from separate clones, agree — **the failing test diffs the checkout against whatever `origin/main` currently resolves to, not against the PR's merge-base — a stale-branch/merge-base test-harness artifact, not a bug PR #2752's own diff introduced.** Matches this task's stated framing.

derived: `git diff 00aeaae4 pr-2752 --stat` — result:
```
docs/issue-2659/reports/...adversarial-review-f42ec06a.md (new) | 256 ++++++++
docs/issue-2659/... ledger entry (new)                          |   1 +
on-the-record/hooks/deliverable-guard.sh                        | 131 +++++----
test/test_deliverable_guard_priorities_shard.py                 |  89 +++----
test/test_deliverable_guard_worktree_submodule.py (new)          | 163 ++++
5 files changed, 546 insertions(+), 94 deletions(-)
```
confirms PR #2752's own diff touches exactly 5 files; `approval-gate.sh` is not among them.

**3. No overhead increase.**

derived: `du -sb on-the-record/directive` on isolated worktrees of both branches (invariants worker) — result:
```
53162  origin/main worktree
53162  pr-2752 worktree
```
byte-identical.

derived: hook runtime, `time -p bash deliverable-guard.sh < payload` x 5 runs x 2 scenarios (plain-repo cwd, worktree cwd) x 2 branches = 20 timed runs — result:
```
plain-repo, origin/main: real 0.03 0.03 0.02 0.03 0.03
plain-repo, pr-2752:     real 0.03 0.03 0.03 0.03 0.03
worktree,   origin/main: real 0.02 0.03 0.03 0.03 0.03
worktree,   pr-2752:     real 0.03 0.04 0.03 0.04 0.03
```
all 20 samples in the 0.02-0.04s band; no systematic separation (plain-repo scenario shows none; worktree scenario shows +0.01s on 2/5 pr-2752 samples, within `time -p`'s 10ms resolution noise floor). **Verdict: unchanged.**

**4. Monitor/watch machinery unbroken and not quieter.**

derived: `python3 -m pytest test/test_watchdog_heartbeat_noise.py on-the-record/monitors/test_poll_heartbeat.py -q` on isolated worktrees of both branches — result:
```
origin/main: 36 passed in 2.40s   (10 workers, 36 items, 36 dots, 0 s/x/F)
pr-2752:     36 passed in 2.37s   (10 workers, 36 items, 36 dots, 0 s/x/F)
```
identical collection count, 0 skipped/xfailed/failed on both. **Verdict: green-unchanged, not quieter.**

## Test-suite claims (four xfail->pass tests, one new xfail)

acceptance: `python3 -m pytest test/test_deliverable_guard_priorities_shard.py -v` on the PR head (test-suite worker) — result:
```
PASSED test_bypass_via_planted_git_directory_should_be_denied
PASSED test_bypass_via_planted_git_symlink_should_be_denied
PASSED test_bypass_inside_linked_worktree_should_be_denied
PASSED test_bypass_via_planted_git_directory_reaches_exempt_suffixes
XFAIL  test_bypass_via_nested_git_init_reaches_exempt_priorities_dir
20 passed, 1 xfailed in 1.04s
```

All 4 flipped tests keep the byte-identical assertion `self.assertEqual(r.returncode, 2, r.stderr)` before and after — no weakened assertion.
derived: `git diff origin/main pr-2752 -- test/test_deliverable_guard_priorities_shard.py` (test-suite worker) confirms the assertion lines are unchanged; only the code under test changed:
```python
def _git_root_from(path_hint):
    probe = _nearest_existing_dir(posixpath.dirname(path_hint))
    r = _run_git(["rev-parse", "--show-toplevel"], probe)
    if r is not None and r.returncode == 0:
        top = r.stdout.strip()
        if top:
            return top
    return None
```
replacing a bare `os.path.isdir(posixpath.join(probe, ".git"))` walk. A planted fake `.git` (bare `mkdir`/`ln -s`, no real git content) satisfied the old `isdir` check trivially; `git rev-parse --show-toplevel` does not treat a content-less `.git` name as a repo boundary and keeps walking to the real root, so the priorities-shard exemption regex correctly fails to match and the write is denied — a genuine mechanism fix, not a relaxed test.

The new xfail plants a *real* `git init`-created subdirectory. The test-suite worker directly reproduced this against both hook versions, not just read the diff:
```
old (origin/main) deliverable-guard.sh against this payload -> rc=0 (exempt/bypass)
new (pr-2752) deliverable-guard.sh against this payload      -> rc=0 (exempt/bypass)
```
Both sides return 0 — unchanged by PR #2752 (a genuinely `git init`'d subdirectory is indistinguishable from a real nested repo using only git-boundary signals — issue #2637's still-open class). derived: the two-sided reproduction above. **Verdict: the new xfail documents a pre-existing gap, not a regression introduced by this PR.**

## Why

Delegated fixture-building and hook reproduction to four parallel background workers (freelunch fan-out: 4 independent angles, ~100+ lines of raw command/output each) rather than running the matrix inline, so this record's citations come from raw, independently-executed transcripts rather than this session's own narration. Each acceptance check and PR claim was re-derived from primary evidence (fresh clones/worktrees/submodules, actual hook invocations) instead of cited from the PR's own record, per defect-verification-independence-from-upstream-verdicts — including negative/edge paths (git missing/erroring/timing-out/malformed-output, rootless directories) the PR's own summary does not walk through case-by-case (canonical: Acceptance 2(b) and Open finding 1 above, this same record). Where two workers' results appeared to conflict (the exemption-path allow-shaped payload denied in one edge case but allowed in another), the conflict was traced to a real variable (absolute vs. relative `file_path`) rather than discarded or averaged away — see Open finding 1.

## What did not work

None.

## Upstream basis

- `on-the-record/hooks/deliverable-guard.sh` @ `490dc6197d97d3184c2a1ea376a70c9e5ce07ec4` (PR #2752 head)
- `test/test_deliverable_guard_priorities_shard.py` @ `490dc6197d97d3184c2a1ea376a70c9e5ce07ec4`
- the PR's new test file covering worktree/submodule shapes (added in this PR, untracked on this session's own branch; verified with `git log --oneline pr-2752 -- test/test_deliverable_guard_worktree_submodule.py` -> `9bcb7581 issue-2659: fix deliverable-guard root-walk fail-open in worktree/submodule`) @ `490dc6197d97d3184c2a1ea376a70c9e5ce07ec4`
- merge-base: `00aeaae457e82b5504421615eca04587b45de577`
- `origin/main` tip at review time: `e1b35a53` (per this session's gitStatus)

## Open findings

1. **Exemption-resolution does not inherit the activation check's fail-closed guarantee, for a specific payload shape.**

   failure_scenario: from inside a real board repo, with `git` fully broken (missing from PATH, or a fake `git` that errors/hangs/returns garbage), a Write whose `tool_input.file_path` is passed as the exact relative string equal to an `EXEMPT_SUFFIXES` entry (e.g. `docs/specs/approvers.md`) is silently **allowed** on all 5 broken-git conditions tested.

   derived: failure-mode worker ran conditions a'-e' (git missing, erroring, garbage stdout, empty stdout, 15s-hang) against `{"tool_input":{"file_path":"docs/specs/approvers.md"},"cwd":"<real board repo>"}` on the PR head — result:
   ```
   a' git missing:  EXIT=0
   b' git errors:   EXIT=0
   c1' garbage:     EXIT=0
   c2' empty:       EXIT=0
   d' hangs 15s:    EXIT=0   (real 0m10.054s -- one failed _run_git call, not two)
   e' no repo:      EXIT=0
   ```
   all 6 -> exit 0 (allow), including the hang case, which returned after only ~10s / one failed `_run_git` call, vs ~20s / two calls for the deny-shaped payload in Acceptance 2(b) — confirming the exemption path makes only one, earlier `_run_git` attempt and never reaches the hardened activation check.

   Root cause, from the exemption-resolution branch of `on-the-record/hooks/deliverable-guard.sh` (matrix worker's diff dump, corroborated by the failure-mode worker's independent read of the same file): when `_git_root_from` returns `None` for any reason (including a git-subprocess failure), the exemption-matching code does not deny — it falls back to matching the raw, unresolved `file_path` string against `EXEMPT_SUFFIXES` and `sys.exit(0)`s before the hardened `--is-inside-work-tree` activation check the PR added is ever reached.

   Scoped, not universal: the matrix worker's Acceptance-2(a) "no repository anywhere" edge case used an absolute `file_path` for the same allow-shaped content and got exit 2 (deny) — the raw absolute string does not exact-match the relative `EXEMPT_SUFFIXES` entries, so it falls through to the fail-closed activation check. The gap is specific to a relative `file_path` that textually equals an exempt suffix; not exercised when the tool call supplies an absolute path. Whether this repo's actual hook invocation typically supplies absolute or relative `file_path` values was not checked in this pass.

   unverifiable: whether this exemption-path behavior is new to PR #2752 or pre-existed identically on `origin/main` — the failure-mode worker checked out only the PR head and did not re-run conditions a'-e' against the BASE script. The old exemption-resolution code (per the same diff region) also had a "root not found -> match raw path" fallback, which suggests it likely pre-existed, but that is inference from a diff read, not an executed reproduction, and is reported as an open question rather than asserted as fact.

   resolution path: outside the acceptance checks' literal wording once "the root cannot be determined" is read as "the activation check's own root-membership decision" — which is what all three acceptance checks and the PR's description specifically test, and which this PR does fix correctly (Acceptance 1-2 above). But it matches this task's explicit framing ("a guard that fails closed in one failure mode and open in another is still fail-open") for the exemption-resolution code path. Recommend a follow-up issue scoped to hardening the exemption-resolution fallback, rather than blocking this PR: issue #2659's own scope is the board-repo activation walk (fixed, verified above), and `EXEMPT_SUFFIXES` is a small, fixed, human-curated allowlist rather than attacker-controlled input, so practical exposure is narrow.

2. **BASE's submodule case had an undocumented opposite-direction bug** (false-positive over-deny of an allow-shaped write) not described in issue #2659's own framing (fail-open only).

   derived: matrix worker, submodule-BASE/allow row in Acceptance 1's table above -> exit 2 (denied `docs/specs/approvers.md`). Traced to the same root defect as the worktree fail-open: walking up from the submodule's working directory, the old `os.path.isdir` walk skips the submodule's file-shaped `.git` and locks onto the superproject's real `.git` directory one level up, misidentifying the superproject as the repo root.

   resolution path: none needed — the PR's `git rev-parse`-based walk fixes this as a side effect of the same change (submodule-PR2752/allow row -> exit 0, correct). Reported for completeness: the PR fixed a materially wider bug than its own bug report named.

## Next steps

None — review-only deliverable, no code changes proposed by this record.

skill-verdict: adversarial-review — applied: invoked; structured this record's blind, evidence-first verification of PR #2752's own claims via independently-executed reproduction (four parallel workers reproducing rather than restating the PR's transcript), per the skill's Step 1-3.
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; re-derived every acceptance check and PR claim from primary evidence rather than citing the PR's own record, included negative/edge-case paths (git missing/erroring/timeout/malformed output, rootless directories) beyond the happy-path matrix, and reported the BASE-vs-PR-head comparison gap for Open finding 1 as an explicit `unverifiable:` item with the same rigor as the confirmed findings rather than omitting it. canonical: Acceptance 2(b) and Open finding 1 sections above, this same record.
skill-verdict: work-in-english — applied: invoked; this record, all worker prompts, and repo-bound text are in English; the final user-facing summary is in Korean per policy.
other mounted skills: test-depth-audit — not triggered; this task was hook-behavior/root-cause verification, not a test-suite quality-classification audit.
