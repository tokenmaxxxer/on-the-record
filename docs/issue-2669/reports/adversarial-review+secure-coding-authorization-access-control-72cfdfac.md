---
issue: 2669
role: adversarial-review+secure-coding-authorization-access-control-72cfdfac
author: adversarial-review+secure-coding-authorization-access-control-72cfdfac
skills: adversarial-review (skill-repository(297e350)), secure-coding-authorization-access-control (skill-repository(297e350))
verifies_subject: true  # independent verification of PR #2706's deliverable
loop_state: terminal
upstream:
  - path: PR #2706 (tokenmaxxxer/on-the-record), branch issue-2669/secure-coding-authorization-access-control+adversarial-review-7696a512
    sha: 50aea93e3499cf70edf7612584700ba7525362dc
---

# issue-2669 — adversarial-review+secure-coding-authorization-access-control-72cfdfac record

## What was done

Independent, hostile re-verification of PR #2706 (the send-back fix for PR
#2700's critical fail-open bypass, itself already independently verified by
PR #2703, merged). Two fresh clones were made from scratch — one checked out
to `50aea93e` (`pr-2706`), one to `6166815e` (clean `origin/main`) — and
every claim was re-derived from raw command execution against the actual
shipped `on-the-record/hooks/upstream-defect-scope-guard.sh` and its new
test file, never inherited from the PR's own description or record.

canonical: `gh pr view 2706 -R tokenmaxxxer/on-the-record --json headRefOid,headRefName,url,title` — result: headRefOid `50aea93e3499cf70edf7612584700ba7525362dc`, headRefName `issue-2669/secure-coding-authorization-access-control+adversarial-review-7696a512`

### 1. Collapse-the-distinction attack matrix

All 7 constructed cases were run against the real hook via a crafted stdin
JSON payload (`{"tool_name":"Bash","tool_input":{"command":...},"cwd":...}`,
exit 0=allow / exit 2=deny), against `pr-2706` (`50aea93e`):

| Case | rc | Verdict |
|---|---|---|
| a. leading `cd` to the harness's own payload cwd | 2 | DENY |
| b. `cd .` no-op | 2 | DENY |
| c. `cd` to an existing non-repo dir | 2 | DENY |
| d. `cd` to a symlink → non-repo dir | 2 | DENY |
| e. `cd` to a nonexistent path | 2 | DENY |
| f. `cd` to a dir whose `.git` exists but is unreadable (chmod 000) | 2 | DENY |
| g. PR #2703 bypass verbatim: `cd /tmp && gh pr create --repo <unrelated>` | 2 | DENY |

derived: fresh clone `git clone https://github.com/tokenmaxxxer/on-the-record.git && git fetch origin pull/2706/head:pr-2706 && git checkout pr-2706`, then for each row a Python driver piping the stdin JSON payload into `bash on-the-record/hooks/upstream-defect-scope-guard.sh` and reading its exit code — result: rc=2 (deny) on all 7 rows, reproducible by re-running the same driver against the same commit.

Verdict: no case found where a session-chosen/unresolvable cwd collapses back to allow, across the 7 shapes attempted. This does not prove no such case exists — only that these 7 attempts (including the exact PR #2703 bypass string) did not find one.

### 2. Legitimate harness fail-open still functions

With no leading `cd` and the payload `cwd` itself pointing at a directory
that is not a git checkout (simulating the harness's own workspace failing
to resolve, independent of anything the session did), the hook returns
rc=0 (ALLOW).

derived: same driver as item 1, payload `{"cwd": "<empty non-repo dir>", "tool_input": {"command": "gh pr create --repo some-unrelated-org/upstream-repo --title x --body y"}}`, no leading `cd` in the command string — result: rc=0 (allow), against `pr-2706` (`50aea93e`).
canonical: `50aea93e:on-the-record/hooks/upstream-defect-scope-guard.sh:209-210` — the `in_scope()` fallback that fires when `operative_cwd()` returns `session_chosen=False`, allowing when only the harness's own cwd was unresolvable.

### 3. Self-found docstring gap vs its test's actual assertion

canonical: `50aea93e:test/test_upstream_defect_scope_guard_cross_repo_cwd.py:223-233` —
```python
@unittest.expectedFailure
def test_harness_cwd_origin_removed_bypass_should_be_denied(self):
    mutated = Path(self._tmp.name) / "harness-mutated"
    _init_repo_with_origin(mutated, "git@github.com:tokenmaxxxer/on-the-record.git")
    subprocess.run(["git", "remote", "remove", "origin"], cwd=mutated, check=True, timeout=30)
    cmd = ("gh pr create --repo some-unrelated-org/upstream-repo --title x --body y")
    r = _run_guard(cmd, cwd=str(mutated))
    self.assertEqual(r.returncode, 2, r.stderr)
```
This pins exactly the corrected claim: the session removes its own harness
workspace's `origin` remote (no `cd` involved — `cwd=mutated` is the
payload/harness cwd itself), and the resulting harness-cwd resolution
failure is (per `expectedFailure`) wrongly allowed. It is not narrower than
the corrected docstring prose describes.

derived: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v` on `pr-2706` (`50aea93e`) — result: `7 passed, 2 xfailed`, with `test_harness_cwd_origin_removed_bypass_should_be_denied` reported XFAIL (its `assertEqual(rc, 2)` genuinely fails at runtime — the bypass is real, not a stale marker on an already-closed case).
derived: manual reproduction outside the test harness — `git init`, `git remote add origin ...`, `git remote remove origin`, then the same driver as item 1 with `cwd` set to that mutated dir and no leading `cd` in the command — result: rc=0 (allow), matching the test's expected failure.

Verdict: disclosure breadth matches assertion narrowness for this gap — no over-broad-disclosure defect found here.

### 4. Two carried-forward gaps

**(i) Spoofed/fake origin remote.**
derived: `diff <(git show pr-2700-orig:test/test_upstream_defect_scope_guard_cross_repo_cwd.py | sed -n '/test_spoofed_origin_remote_bypass_should_be_denied/,/^$/p') <(git show pr-2706:test/test_upstream_defect_scope_guard_cross_repo_cwd.py | sed -n '/test_spoofed_origin_remote_bypass_should_be_denied/,/^$/p')` — result: empty diff, byte-identical between PR #2700's original version and `50aea93e`.
derived: same `pytest -v` run as item 3 — result: `test_spoofed_origin_remote_bypass_should_be_denied` reported XFAIL (still present, still runs).

**(ii) `pushd`/subshell/chained-`cd`.**
derived: `grep -rn "pushd" test/` on `pr-2706` (`50aea93e`) — result: no matches; this gap is not pinned by any test in this PR or in PR #2700's original version (`git show pr-2700-orig:test/ | grep pushd` also empty).
derived: same driver as item 1, three payloads (`pushd /tmp && gh ...`, `(cd /tmp && gh ...)`, `cd /tmp && cd /tmp && gh ...`) against `pr-2706` — result: rc=2 (deny) on all three, since the single-leading-`cd` regex doesn't match these forms and resolution falls back to the payload cwd (a valid checkout), so target≠origin → deny.

Verdict: gap (i) is test-pinned and unchanged. Gap (ii) was never actually
encoded as a runnable regression test in either PR — it exists only as
prose in prior review reports and in PR #2706's own record. It is
currently harmless (fails closed, confirmed live above), but PR #2706
neither closes it nor claims it as test-covered; a future change to the
`cd`-parsing regex that also recognizes `pushd` would have no regression
test catching a reintroduced bypass in that direction.

### 5. `timeout=` on subprocess call sites

| Site | `timeout=`? |
|---|---|
| hook's own `git -C <cwd> remote get-url origin` | `timeout=10`, pre-existing |
| test `_init_repo_with_origin`: `git init -q` | `timeout=30`, added by #2706 |
| test `_init_repo_with_origin`: `git remote add origin` | `timeout=30`, added by #2706 |
| test `_run_guard`: `subprocess.run(["bash", HOOK_PATH], ...)` | `timeout=30`, pre-existing |

canonical: `50aea93e:on-the-record/hooks/upstream-defect-scope-guard.sh:170-173` — the hook's own `git -C <cwd> remote get-url origin` call, `timeout=10`.
canonical: `50aea93e:test/test_upstream_defect_scope_guard_cross_repo_cwd.py:70-72,88-91` — the two `_init_repo_with_origin` subprocess calls (now `timeout=30`) and the `_run_guard` bash-hook invocation (`timeout=30`, pre-existing).
derived: `git show pr-2700-orig:test/test_upstream_defect_scope_guard_cross_repo_cwd.py` around the same helper — result: the two `_init_repo_with_origin` calls had no `timeout=` kwarg in PR #2700's version (`check=True)` only).

Verdict: exactly "two sites added timeout, one pre-existing, all three now present" as claimed.

### 6. Test-suite delta

`pytest.ini` on `origin/main` (`6166815e`) defines a `slow` marker
(subprocess/git-clone lifecycle tests, issue #1490), so `-m "not slow"` is a
real, documented subset rather than an arbitrary narrowing. Both runs
completed in under 3 seconds each, well inside the 2-minute timeout risk
window, so no further narrowing was needed.

derived: `git clone https://github.com/tokenmaxxxer/on-the-record.git` at `6166815e` (clean main), `python3 -m pytest test/ -m "not slow" -q --tb=no -rA` — result: `15 failed, 380 passed, 4 xfailed in 2.83s`.
derived: `git clone https://github.com/tokenmaxxxer/on-the-record.git`, `git fetch origin pull/2706/head:pr-2706 && git checkout pr-2706` (`50aea93e`), same pytest command — result: `15 failed, 387 passed, 6 xfailed in 2.92s`.
derived: nodeid-set diff (`diff`/`comm` over extracted nodeid lists from both `-rA` outputs) — result: the 15 failing nodeids are byte-identical between the two runs (pre-existing failures in `test_convention_equivalence.py`, `test_local_dependency_env.py`, `test_spawn_cross_family_skill_selection.py`, `test_spawn_artifact_skill_pairing.py`, `test_spawn_skill_judge_haiku_timeout_overlap.py`, none touched by this PR); exactly 7 new passing nodeids and 2 new xfailed nodeids, all 9 inside the single new file `test_upstream_defect_scope_guard_cross_repo_cwd.py`; `comm -23` on the sorted passed-nodeid lists (A minus B) returned empty, i.e. zero regressions; total collected-node count A=399, B=408, delta=+9=7+2 exactly.

Caveat: this covers the `-m "not slow"` subset only; the `slow`-marked
subset was not run (per the stated timeout risk) and its state relative to
the PR's claim was not checked either way — narrower than "the full suite"
but the narrowing and its scope are stated here, not silently assumed.

Verdict: the claimed delta (identical 15 pre-existing failures, +7 passed,
+2 xfailed, no other change) matches the independently observed delta
exactly, within the stated `-m "not slow"` subset.

## Why

The fix's entire value is a single distinction (session-chosen vs
harness-native unresolvable cwd) that is easy to accidentally collapse
under an unconsidered edge case, so the attack order went from
highest-consequence (a live re-opened bypass, items 1-2) to the specific
failure mode this repo has been burned by before (an over-broad disclosure
whose test asserts less than its prose claims, item 3), to confirming
nothing already-settled quietly regressed (item 4), to mechanical
bookkeeping claims (items 5-6) — matching the order given in the task
brief. Both investigative units (items 1-5 against live clones of the
hook; item 6 as a separate long-pole pytest-diff unit needing its own
clone) were run as background `freelunch:freelunch-worker` agents per this
session's freelunch-directive width/threshold tally (width=2, both units
exceeding the ~100-line/sustained-digging bar, no shared mutable state
since each used its own clone); their raw findings are what this record's
`derived:`/`canonical:` tags cite, re-expressed here rather than pasted as
an unverified third-party transcript.

## Upstream basis

- PR #2706, tokenmaxxxer/on-the-record, branch
  `issue-2669/secure-coding-authorization-access-control+adversarial-review-7696a512`,
  head `50aea93e3499cf70edf7612584700ba7525362dc` — canonical: `gh pr view 2706 -R tokenmaxxxer/on-the-record --json headRefOid,headRefName,url,title`.
- `50aea93e:on-the-record/hooks/upstream-defect-scope-guard.sh` and
  `50aea93e:test/test_upstream_defect_scope_guard_cross_repo_cwd.py` — read
  and executed directly from a fresh clone at that commit, not inherited
  from the PR's description or its own record.
- PR #2703 (merged, `6166815e`) — settled prior verification of PR #2700's
  disclosed claims (legitimate cross-repo allow, written-for-deny case, no
  other guard branch moved); not re-litigated here. Item 1 (rows a and g)
  and item 4 (sub-point i) confirm PR #2706 did not disturb what #2703
  already settled.

## Open findings

derived: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v` executed against `pr-2706` (`50aea93e`) — result: `7 passed, 2 xfailed`, consistent with the per-item verdicts in "What was done" above (items 1 through 6, each carrying its own `derived:`/`canonical:` citation to the exact command or file:line read).

- None blocking. Items 1 through 6 above each found the claimed behavior
  present and reproducible from a fresh clone: no fail-open bypass
  survived the attack matrix (item 1), the legitimate harness fail-open
  still works (item 2), the self-disclosed docstring correction is
  honestly scoped to what its test pins (item 3), both carried-forward
  gaps are unchanged (item 4), all three subprocess sites carry
  `timeout=` (item 5), and the test-suite delta matches the claim exactly
  within the stated subset (item 6).
- Non-blocking observation (item 4, sub-point ii): the
  `pushd`/subshell/chained-`cd` gap has never been encoded as a runnable
  test in this PR chain (#2700 or #2706) — only described in prose. It is
  currently harmless (denies, confirmed live in item 4 above), but a
  future fix to the `cd`-parsing regex in the `pushd` direction would have
  no regression test guarding it. Resolution path: a future PR touching
  this hook's cd-parsing should add an `expectedFailure` (or, once fixed,
  a passing) test for this case, mirroring the shape already used for the
  spoofed-origin and origin-removed cases (item 3 and item 4 sub-point i
  above). Not raised as a new issue here since it does not block PR #2706,
  which neither introduced it nor misrepresented it as test-covered.

## What did not work

None.

## Next steps

acceptance: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v` (executed against `pr-2706`, `50aea93e`) — result:
```
7 passed, 2 xfailed
```
This matches every per-item verdict recorded in "What was done" (items
1-6). No further verification round is warranted; nothing here is
deferred; this record's `loop_state` is `terminal`.

skill-verdict: adversarial-review — applied: invoked; used as the operating frame for the entire verification (structurally independent re-derivation from raw commands in fresh clones, blind to PR #2706's own claims/record, actively attempting to collapse the fix's core distinction across 7 shapes before accepting any claim as true)
skill-verdict: secure-coding-authorization-access-control — applied: invoked; used to structure the authorization-boundary analysis in items 1-2 (fail-open vs fail-closed branch selection in `in_scope()`, treating "does an unhandled input shape collapse to allow-by-default" as the primary attack surface for a scope-decision guard)
other mounted skills: work-in-english and test-depth-audit — not triggered as separate Skill-tool invocations; test-depth-audit's genuine-assertion-vs-execution-only lens was applied inline while reading the xfail tests in items 3-4, but the skill itself was not loaded via the Skill tool, so no applied: line is claimed for it.
