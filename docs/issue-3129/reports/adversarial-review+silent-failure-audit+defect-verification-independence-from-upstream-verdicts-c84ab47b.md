---
issue: 3129
role: adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-c84ab47b
author: adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-c84ab47b
skills: adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3137's own deliverable, author differs -- see docs/handbooks/observer-verification.md
loop_state: complete
upstream:
  - path: PR #3137, branch issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019
    sha: a0abb72dc132d723bae499503a396d8e79af81cd
---

# issue-3129 — adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-c84ab47b record

## What was done

amendments-reconciled: `issuecomment-5508124905` landed on issue #3129
partway through this session, reporting a competing verification (PR
#3147):

```
$ gh api repos/tokenmaxxxer/on-the-record/issues/comments/5508124905 -q '.body'
## PR #3137 held — marker has no repo dimension
...
One Incorrect: the amendment marker is keyed by issue number alone.
```

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5508124905 -q '.body'`, this session, this turn — full text above (truncated for the fence; complete body reports PR #3147 finding the marker has no repo dimension). Re-derived this claim myself against the real code rather than citing it — see Finding 5 below.

Independent, builder-blind verification of PR #3137 against issue
#3129's 4 named acceptance checks and 3 must-not clauses, run by direct
reproduction from a separate git worktree (PR #3137 never checked out
onto or edited from this session's own branch, and never merged):

```
$ git fetch origin pull/3137/head:pr-3137-review
$ git worktree add /tmp/pr-3137-review pr-3137-review
HEAD is now at a0abb72d issue-3129: deviation log entry for the dropped-staging incident
```

canonical: this session's own `git worktree add` transcript above, this turn — the review environment for every check below. PR #3137 HEAD = `a0abb72dc132d723bae499503a396d8e79af81cd`.

Per `defect-verification-independence-from-upstream-verdicts`, every
check below was re-derived rather than accepted from PR #3137's own
"Test plan" claims, and the two failure modes the issue calls "the
substance of the work" (drowning, re-announcement) were each given a
second, independently-constructed probe beyond the PR's own two named
gate probes, plus the negative/edge-case paths the spawning prompt
named that neither of the two named acceptance probes cover (a
concurrent-write race, a pre-spawn amendment, cross-issue isolation).

## Why

Graded each acceptance/must-not item by running the real shipped
`a0abb72d:on-the-record/hooks/amendment_channel.py` /
`a0abb72d:on-the-record/hooks/amendment-channel.sh` directly (subprocess
and in-process calls alike), not by reading PR #3137's description
first. Where the spawning prompt named a specific adversarial
construction not covered by the issue's two named probes — drowning at
higher tick counts, cross-issue isolation, a real multi-process
concurrent-write race, a pre-spawn amendment, the must-not clauses —
that construction was executed against the actual module, with full
transcripts inline below, not simulated in the abstract or inferred
from reading the code alone.

## What did not work

One Bash invocation in this session combined a `git commit` setup step
with a heredoc'd Python snippet in the same call and was refused by
`heredoc-command-refusal-gate.sh` (the classifier flagged the whole
multi-command block, not just the commit line). Re-ran the two steps
as separate Bash calls with no heredoc:

```
$ git init -q && git config user.email a@b.c && git config user.name probe \
    && git commit -q --allow-empty -m init && git checkout -q -b issue-9999/some-role
$ git rev-parse --abbrev-ref HEAD
issue-9999/some-role
```

derived: the two re-run commands above, this session, this turn — both exit 0, `/tmp/probe-worker-repo` created with the expected branch, used directly in Must-not 2's reproduction below. Tooling friction only, not a finding against PR #3137.

## Upstream basis

- PR #3137, branch `issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`, commit `a0abb72dc132d723bae499503a396d8e79af81cd` (frontmatter `upstream:` above).
- `a0abb72d:on-the-record/hooks/amendment_channel.py`, `a0abb72d:on-the-record/hooks/amendment-channel.sh`, `a0abb72d:tests/test_amendment_channel.py`, `a0abb72d:gates/probe_running_session_sees_amendment.py`, `a0abb72d:gates/probe_amendment_notice_fires_once.py` — the delivered artifact, read and executed directly, on PR #3137's own branch (all five untracked on this branch).
- Issue #3129 (`gh issue view 3129`), for the acceptance/must-not text quoted throughout.
- `origin/main` at `02c3c8cb58444ed0deb53f65fcd831f1eb71b28b`, and the merge-base `820e9dc5ecbcbadf00ad3f03406e1e375837e3a2`, both checked out into separate worktrees to re-derive claims about pre-existing state rather than accept them.

## Open findings

### Finding 1 — PR #3137 is not rebased onto current `origin/main`; its own "15 pre-existing `test/` failures" claim is now stale

PR #3137's merge-base with `origin/main` is `820e9dc5`, not `origin/main`'s tip `02c3c8cb` — the branch is 8 commits behind, including `73b614fd` (issue #3091's own delivery landing on main after this PR branched).

```
$ git merge-base --is-ancestor origin/main HEAD   # inside the PR worktree
main-is-ancestor-of-PR=NO
$ git log --oneline HEAD..origin/main | wc -l
8
```

derived: `cd /tmp/pr-3137-review && git merge-base --is-ancestor origin/main HEAD; git log --oneline HEAD..origin/main`, this session, this turn — 8 commits, including `73b614fd` (issue-3091 implementation-blueprint+test-derivation+silent-failure-audit).

Re-derived the "15 failed, pre-existing, owned by #3091" claim at three points instead of accepting it:

```
# PR #3137 branch (a0abb72d)
15 failed, 548 passed, 3 xfailed in 32.28s
# PR #3137's own merge-base (820e9dc5, before any of this PR's commits)
15 failed, 548 passed, 3 xfailed in 32.40s
# origin/main tip (02c3c8cb, includes #3091's later fix)
563 passed, 3 xfailed in 32.39s   -- 0 failed
```

derived: `python3 -m pytest test/ -q` run in three separate worktrees this session, this turn — `/tmp/pr-3137-review` (PR HEAD), `/tmp/mergebase-review` (merge-base `820e9dc5`), `/tmp/main-review` (`origin/main` tip `02c3c8cb`). Same 15 failing test IDs at both the PR HEAD and the merge-base (`test_convention_equivalence.py`, `test_local_dependency_env.py`, `test_spawn_cross_family_skill_selection.py`, `test_spawn_artifact_skill_pairing.py`, `test_spawn_skill_judge_haiku_timeout_overlap.py`), confirming the 15 failures genuinely predate this PR's own commits rather than being introduced by them — the PR's characterization was accurate when written. But `origin/main`'s current tip is fully green: issue #3091's own delivery (`73b614fd`, landed on main after this PR branched) already fixed all 15. `test/` is not one of the 4 named acceptance checks (only `tests/` — plural — is), so this does not change any acceptance/must-not verdict below. It is a landing-readiness fact: merging PR #3137 as-is would reintroduce 15 now-fixed `test/` failures onto `main` until it is rebased. Non-blocking for this record's own scope; flagged for whoever lands the PR.

### Finding 2 — two amendments landing before any tool call coalesce into one notice carrying only the later note; independently reproduced, and confirmed as a deliberate, already-tested design choice rather than an unaddressed gap

The spawning prompt named this case explicitly ("the orchestrator amends the issue ... two amendments land between two tool calls") as outside what either named acceptance probe checks (both probes space amendments apart with worker ticks in between). Reproduced directly against the shipped module, in-process:

```
>>> v1 = ac.write_amendment(state_dir, issue, note="FIRST-AMEND")
>>> v2 = ac.write_amendment(state_dir, issue, note="SECOND-AMEND")
versions written: 1 2
>>> ac.check_notice(state_dir, "worker-session-A", issue)
'[amendment] issue #9999 was amended ... Note: SECOND-AMEND'
>>> ac.check_notice(state_dir, "worker-session-A", issue)   # immediate next tick
None
```

derived: `python3 -c "..."` against `a0abb72d:on-the-record/hooks/amendment_channel.py` imported directly, this session, this turn — one notice fires, carrying only `SECOND-AMEND`; `FIRST-AMEND`'s text is not recoverable through this channel (the marker stores only current state, not a queue). This is not an unaddressed gap: PR #3137 ships a unit test asserting the identical shape, `a0abb72d:tests/test_amendment_channel.py:146-148`:

```
    def test_two_amendments_before_absorption_coalesce_into_one_notice(self):
        """State-transition gap (test-derivation): S1 (unabsorbed) --write_amendment--> S1
        is a real transition -- the orchestrator can amend twice before the
```

canonical: `git show a0abb72d:tests/test_amendment_channel.py | sed -n '146,148p'`, this session, this turn. The same test's docstring (lines 149-152, not re-quoted here) states the design rationale directly: "an older, superseded correction does not need its own separate notice." My reproduction above matches this test's own assertion (single notice, latest note only). Verdict: **Present** (deliberate, tested behavior) — recorded here because the spawning prompt asked the question explicitly, not because it is a defect.

### Finding 3 — a session spawned after a pre-existing amendment gets that amendment announced as new on its first tool call, not as already-absorbed

The spawning prompt's other named untested case: "the very first tool call of a session that was spawned AFTER an amendment was written." Reproduced directly:

```
>>> ac.write_amendment(state_dir, "9999", note="pre-spawn correction, already in the body the worker read at spawn")
>>> ac.check_notice(state_dir, "brand-new-worker-session", "9999")   # this session_id's FIRST ever check
'[amendment] issue #9999 was amended ... Note: pre-spawn correction, already in the body the worker read at spawn'
```

derived: `python3 -c "..."` against `a0abb72d:on-the-record/hooks/amendment_channel.py`, this session, this turn — the marker/seen state machine has no notion of "this session's spawn-time issue read already reflects the current marker version"; every session's first `check_notice` call for an issue compares against an implicit `seen == 0`, so any marker version > 0 fires once on first contact, whether or not that content was already current when the session's own worktree/branch was created. This is a real, confirmed behavior, not a hypothesis from reading the code. Severity is low: the notice is advisory-only and non-blocking (Must-not 2 below), so the cost is one redundant "re-read the issue" line the session can freely disregard, not a wrong or blocking action.

The same underlying code path (a session's first-ever `check_notice` call) is exercised, without the pre-spawn framing, `a0abb72d:tests/test_amendment_channel.py:111-113`:

```
    def test_first_check_after_amendment_fires(self):
        ac.write_amendment(self.state_dir, "1", note="fix the brief")
        notice = ac.check_notice(self.state_dir, "sess-1", "1")
```

canonical: `git show a0abb72d:tests/test_amendment_channel.py | sed -n '111,113p'`, this session, this turn. Verdict: **Present** (confirmed, low-severity, not covered by either named acceptance probe).

### Finding 4 — concurrent orchestrator writes degrade as documented (lost increments, never corruption or a crash), verified under real multi-process concurrency

`write_amendment`'s own docstring claims "read-increment-write is not atomic across processes ... the failure mode of a lost increment here is a missed notice tick, not a wrong one." Verified this under actual concurrent subprocesses (matching real deployment: each `gh issue edit` is a distinct `python3 amendment_channel.py` invocation with a distinct PID, unlike a naive same-process thread race which shares `_atomic_write_json`'s PID-keyed temp filename and is not representative):

```
20 concurrent `python3 on-the-record/hooks/amendment_channel.py` subprocess invocations, each one `gh issue edit 9999 --body "race-N"`:
final version: 16   note: race-14
(0 nonzero exit codes, 0 stderr output across all 20)
```

derived: `python3 -c "..."` spawning 20 `subprocess.run(["python3", "amendment_channel.py"], ...)` calls via a `ThreadPoolExecutor`, this session, this turn — 4 of 20 increments lost (16 of 20 landed), zero crashes, zero corrupted marker reads, final marker always valid JSON with the content of one of the writes that did land. Matches the documented tradeoff exactly. Verdict: **Present**, consistent with design.

### Finding 5 — the amendment marker has no repo dimension; cross-repo collision reproduced independently

`issuecomment-5508124905` (quoted in "What was done" above) reports a
competing verification (PR #3147) grading this **Incorrect**: the
marker is keyed by issue number alone, with no repo/org component, so
two unrelated repos sharing the same `issue-<n>/<role>` branch name
collide. Re-derived directly against the code rather than accepting
the comment's verdict, per `defect-verification-independence-from-upstream-verdicts`:

```
$ grep -n "def marker_path" -A2 amendment_channel.py
def marker_path(state_dir: str, issue: str) -> str:
    return os.path.join(state_dir, "issue-%s.marker.json" % _safe(str(issue)))
```

canonical: `cd /tmp/pr-3137-review2/on-the-record/hooks && grep -n "def marker_path" -A2 amendment_channel.py`, this session, this turn — `marker_path` builds its filename from `issue` alone; `default_state_dir()` (read directly, same file) has no repo/org input either. Reproduced the collision end-to-end through the real `write_amendment`/`check_notice` pair with two independent scratch git repos, both on branch `issue-42/some-role`, distinct `origin` remotes:

```
>>> ac.write_amendment(state_dir, '42', note='repo-a specific correction')   # orchestrator in repo-a
1
>>> ac.check_notice(state_dir, 'worker-session-in-repo-b', '42')             # unrelated worker in repo-b
'[amendment] issue #42 was amended ... Note: repo-a specific correction'
```

derived: `python3 -c "..."` against `a0abb72d:on-the-record/hooks/amendment_channel.py` imported directly, two separate scratch repos under `/tmp/cross-repo-test/{repo-a,repo-b}` each with its own `git remote add origin <distinct-url>`, this session, this turn — repo-b's worker receives repo-a's correction verbatim, confirming the collision independently rather than citing the comment's own claim. This is the same orchestrator-shared-state-keyed-without-repo shape as issues #3081 and #3095, per the comment. Verdict: **Incorrect** — this is a real defect in PR #3137, not covered by any of the issue's 4 named acceptance checks or 3 must-nots (none of them name repo scoping), so it does not change any of the Present verdicts above, but it is a genuine finding against the delivered code. Per the comment, a repair round is already spawned against PR #3137's own branch; this session does not edit PR #3137 or duplicate that repair, per the spawning prompt's explicit instruction.

## Independent verification — PR #3137 (issue #3129)

### Check 1 — `python3 -m pytest tests/test_amendment_channel.py -q`

```
35 passed in 0.87s
```

canonical: `cd /tmp/pr-3137-review && python3 -m pytest tests/test_amendment_channel.py -q`, this session, this turn — result above. Verdict: **Present**.

### Check 2 — `python3 gates/probe_running_session_sees_amendment.py`

```
ok
EXIT=0
```

canonical: `cd /tmp/pr-3137-review && python3 gates/probe_running_session_sees_amendment.py; echo EXIT=$?`, this session, this turn — result above. Confirmed the probe's own "must fail against current main" claim by checking file existence directly rather than re-running it there (the module does not exist to import): `ls on-the-record/hooks/amendment_channel.py gates/probe_running_session_sees_amendment.py` inside `/tmp/main-review` (origin/main tip) returned "no such file or directory" for all four PR-introduced paths, this session, this turn. Verdict: **Present**.

### Check 3 — `python3 gates/probe_amendment_notice_fires_once.py`

```
ok
EXIT=0
```

canonical: `cd /tmp/pr-3137-review && python3 gates/probe_amendment_notice_fires_once.py; echo EXIT=$?`, this session, this turn — result above. Beyond accepting this probe's own pass, ran an independent second construction against the module directly (50 ticks per phase instead of 12, plus a cross-issue isolation check the shipped probe does not attempt):

```
ALL INDEPENDENT PROBE ASSERTIONS PASSED
```

derived: `python3 -c "..."` — a standalone script asserting, in-process against `amendment_channel.check_notice`/`write_amendment`: 0 fires across 50 ticks with no amendment; exactly 1 fire across 50 ticks after one amendment; 0 fires across 20 ticks for issue A after an unrelated amendment on issue B (no cross-issue bleed); exactly 1 fire for issue B's own amendment; exactly 1 fire for issue A's second amendment after a 30-tick quiet gap. This session, this turn — full transcript above (ALL INDEPENDENT PROBE ASSERTIONS PASSED, no assertion failures). Verdict: **Present**.

### Check 4 — `python3 -m pytest tests/ -q`

```
289 passed, 2 warnings in 10.49s
```

canonical: `cd /tmp/pr-3137-review && python3 -m pytest tests/ -q`, this session, this turn — result above (0 failed; the 2 warnings are the pre-existing, unrelated `test_skill_candidates_floor.py` pinned-fixture-divergence notice, issue #3019, not from this PR's files). Verdict: **Present**.

### Must-not 1 — no `gh` call, no network call of any kind, from the `PostToolUse` hot path

Read `a0abb72d:on-the-record/hooks/amendment_channel.py` end to end and grepped for every subprocess/network primitive:

```
$ grep -n "subprocess\|urllib\|requests\|curl\|socket\|http" amendment_channel.py
54:import subprocess
236:    costs one fast subprocess call per tool use, not a `gh` round trip.
241:        r = subprocess.run(
245:    except (OSError, subprocess.SubprocessError):
$ grep -n '"gh"\|gh issue' amendment_channel.py amendment-channel.sh
(matches only inside docstrings/comments referring to the ORCHESTRATOR's own gh command it detects by regex, never a gh invocation of its own)
```

canonical: `cd /tmp/pr-3137-review/on-the-record/hooks && grep -n ...`, this session, this turn — the sole `subprocess.run` call in the entire module is `issue_for_cwd`'s `git -C <cwd> rev-parse --abbrev-ref HEAD` (local git plumbing, no network). `maybe_write_from_command` detects `gh issue edit ... --body` purely by regex over the Bash tool's own command *text* it is handed — it never executes `gh` itself. Verdict: **Present**.

### Must-not 2 — not a blocking gate; advisory only

Read `main()`/the `.sh` wrapper for a `permissionDecision`/`decision` field or a nonzero/blocking exit path — none exists (`main()` always `return 0`; the `.sh` wrapper's trailing line is an unconditional `exit 0` independent of the python process's own exit code). Then constructed an amendment and drove the real shipped hook end to end as the next tool call, per the spawning prompt's explicit instruction to check the session's next tool call proceeds:

```
$ printf '%s' '{"session_id":"worker-1","tool_name":"Read","tool_input":{},"cwd":"/tmp/probe-worker-repo"}' \
    | OTR_AMENDMENT_STATE_DIR=/tmp/my-probe-state bash on-the-record/hooks/amendment-channel.sh
{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "[amendment] issue #9999 was amended ... Note: a mid-flight correction"}}
EXIT_CODE=0
```

derived: the command above, run against the real, unmodified `a0abb72d:on-the-record/hooks/amendment-channel.sh` with a freshly-planted amendment marker and a real `issue-9999/some-role` git branch as the worker's `cwd`, this session, this turn — exit 0, output shape is exactly `hookSpecificOutput.additionalContext` with no `decision`/`permissionDecision` field of any kind, confirming a session's next tool call is never denied by this hook.

`a0abb72d:on-the-record/hooks/hook_classification.json`'s new row for `amendment-channel.sh`, read directly rather than cited from the PR description:

```
"class": "observability", rationale: "surfaces an orchestrator's issue-body amendment into a running worker session's context via additionalContext (issue #3129); absence loses the mid-flight correction signal but enforces no rule and blocks nothing"
```

canonical: `git show a0abb72d:on-the-record/hooks/hook_classification.json | python3 -c "..."`, this session, this turn. `a0abb72d:on-the-record/hooks/hooks.json`'s `PostToolUse` registration for it carries no `matcher` key at all (same shape as the pre-existing always-fire `approach-cap-warning.sh` post entry), confirmed by parsing the JSON directly this session, this turn — it fires on every tool call as the issue requires, not a filtered subset. Verdict: **Present**.

### Must-not 3 — does not treat killing and re-spawning as the answer

```
$ grep -n "kill\|respawn\|re-spawn\|os\.kill\|SIGKILL\|SIGTERM\|exit(1)\|sys.exit(1)" amendment_channel.py amendment-channel.sh
(no output)
```

canonical: `cd /tmp/pr-3137-review/on-the-record/hooks && grep -n ...`, this session, this turn — no match. The module's only effect is a local marker write (orchestrator side) and a local advisory read (worker side); nothing in this PR's diff touches process lifecycle. Verdict: **Present**.

### Cross-platform (mtime granularity, temp paths)

The issue requires both probes to "run on Linux and macOS" and warns that mtime granularity differs (HFS+ 1-second) and temp paths differ. No macOS host is available in this environment, so live macOS execution of the two named gate probes is **Unverifiable** here — stated plainly rather than assumed clean. The mechanism itself was confirmed platform-portable by direct grep, not by reading the code and inferring:

```
$ grep -n "mtime\|st_mtime\|getmtime" amendment_channel.py
28:*content*, not read off the filesystem's mtime -- mtime granularity differs
30:so two writes in the same tick could be indistinguishable by mtime alone.
$ grep -rn "st_mtime\|getmtime\|os.stat" ../../gates/probe_running_session_sees_amendment.py ../../gates/probe_amendment_notice_fires_once.py
(no output)
```

canonical: `cd /tmp/pr-3137-review/on-the-record/hooks && grep -n ...` (two greps above), this session, this turn — zero uses of `os.stat`/`st_mtime`/`getmtime` in `amendment_channel.py` or either probe (the two docstring lines matched are prose explaining why mtime is avoided, not a mtime read); both probes use `tempfile.mkdtemp()` for every scratch path (confirmed by reading their source this session). Temp paths route through `default_state_dir()` → `OTR_AMENDMENT_STATE_DIR` env override, else `$TMPDIR` (falls back to `/tmp`), the same `$TMPDIR`-first convention this PR's own new row in `docs/specs/generated-paths.md` documents (that file is tracked on this branch already, pre-existing on `main`). The mechanism is platform-portable by construction; live macOS execution remains Unverifiable in this environment.

## Verdict summary

| Item | Verdict |
|---|---|
| Check 1 — `tests/test_amendment_channel.py -q` | Present |
| Check 2 — `probe_running_session_sees_amendment.py` | Present |
| Check 3 — `probe_amendment_notice_fires_once.py` | Present |
| Check 4 — `tests/ -q` | Present |
| Must-not 1 — no `gh`/network in `PostToolUse` | Present |
| Must-not 2 — advisory only, never blocking | Present |
| Must-not 3 — no kill-and-respawn | Present |
| Cross-platform mechanism (design) | Present |
| Cross-platform (live macOS execution) | Unverifiable — no macOS host in this environment |

canonical: the 9 check/must-not sections above (Check 1-4, Must-not 1-3, Cross-platform mechanism and its macOS sub-item), each with its own `canonical:`/`derived:` transcript, this session, this turn. 4/4 acceptance checks Present, 3/3 must-nots Present, by direct reproduction — no defect found against any named check or must-not. Finding 1 (stale rebase) is a landing-readiness note outside the named checks' scope. Findings 2-4 answer the spawning prompt's named untested cases (amendment race, pre-spawn timing, concurrent writes) and are confirmed-benign/deliberate, not defects. Finding 5 is a real, independently-reproduced **Incorrect** (marker has no repo dimension) reported via `issuecomment-5508124905` and re-derived directly against the code this session, this turn — it does not touch any of the 9 named items above but is a genuine defect in PR #3137's delivered code, already the subject of a separately-spawned repair round per that comment.

## Next steps

None for this record's own scope: verification against PR #3137's 4
acceptance checks and 3 must-nots is finished, derived from the
transcripts above, this session, this turn. Whoever lands PR #3137
should rebase onto current `origin/main` first (Finding 1) so `test/`
does not regress by 15 failures that are already fixed there, and
should wait for the Finding 5 repair round (marker repo dimension)
before merging. This session does not merge or edit PR #3137, per the
spawning prompt.

skill-verdict: adversarial-review — applied: invoked; used its blind-evaluator framing to grade PR #3137 from the artifact and issue text alone, without reading the builder's own implementation-blueprint record before forming verdicts
skill-verdict: silent-failure-audit — applied: invoked; traced every `try`/`except` in `amendment_channel.py` (read_marker, write_amendment, _read_seen, _write_seen, check_notice, issue_for_cwd, main) forward to its downstream effect — all fail open by documented, low-blast-radius design, the one write-failure path the PR's own commit message claims to have fixed (stderr trace on `write_amendment` OSError) verified present in the delivered code
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; every check re-derived by direct execution (fresh worktrees, in-process reproductions, a real 20-subprocess concurrency race) rather than accepted from PR #3137's "Test plan" checklist, including re-deriving the "pre-existing test/ failures" claim against three separate commits instead of citing it
skill-verdict: conformance-review-finding-record — applied: invoked; used its requirement/evidence/rationale/verdict field shape for each Check/Must-not block above, folded into this record's own pre-existing skeleton sections per this task's explicit instruction not to create a separate docs/issue-3129/reports/conformance-review.md
skill-verdict: verify-finding-record — applied: invoked; used its attempt/outcome/evidence/steps shape for Findings 2-4's reproduction attempts above, folded into this record rather than a separate docs/issue-3129/reports/defect-verification.md for the same reason
skill-verdict: work-in-english — applied: invoked; this record, all commit messages, and all scratch scripts written in English; the final chat summary to the user is in Korean per the policy
other mounted skills: not triggered
