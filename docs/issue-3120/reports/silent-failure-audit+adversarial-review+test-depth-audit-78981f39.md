---
issue: 3120
role: silent-failure-audit+adversarial-review+test-depth-audit-78981f39
author: silent-failure-audit+adversarial-review+test-depth-audit-78981f39
skills: silent-failure-audit (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3132's own deliverable, author differs -- see docs/handbooks/observer-verification.md
loop_state: complete
upstream:
  - path: PR #3132, branch issue-3120/silent-failure-audit+test-derivation-7f269a06
    sha: f2b8572e6de4c4bc1863a673d11dd8578c379087
---

# issue-3120 — silent-failure-audit+adversarial-review+test-depth-audit-78981f39 record

## What was done

Independent, builder-blind verification of PR #3132 against issue
#3120's wake-notice defect only (the PR's own declared scope). Reviewed
from a separate git worktree so PR #3132's branch was never checked out
onto or edited from this session's own branch:

```
$ git worktree add /tmp/pr3132-review pr-3132-review
Preparing worktree (checking out 'pr-3132-review')
HEAD is now at f2b8572e issue-3120: invoke test-derivation skill, correct invoked-mismatch
```

canonical: this session's own `git worktree add` transcript above, this turn — the review environment for every check below.

## Why

Graded each acceptance/must-not item by direct reproduction against the
real `on-the-record/hooks/directive.sh` subprocess, not by reading PR
#3132's own claims first, per `defect-verification-independence-from-upstream-verdicts`.
Where the spawning prompt named a specific adversarial construction
(negative case, boundary conditions, injected removal failure, real
`origin/main` re-derivation, cross-platform mechanism), that
construction was executed, not simulated in the abstract — full
transcripts are inline in each section below.

## What did not work

None.

## Upstream basis

- PR #3132, branch `issue-3120/silent-failure-audit+test-derivation-7f269a06`, commit `f2b8572e6de4c4bc1863a673d11dd8578c379087` (frontmatter `upstream:` above).
- `f2b8572e6de4c4bc1863a673d11dd8578c379087:docs/issue-3120/reports/silent-failure-audit+test-derivation-7f269a06.md` — the builder's own record on PR #3132's branch (untracked on this branch). This session read it only as a cross-check against verdicts already reached independently below, never as their source.
- `f2b8572e6de4c4bc1863a673d11dd8578c379087:gates/probe_wake_notice_clears.py` — the new probe, on PR #3132's branch (untracked on this branch).
- Issue #3120 (`gh issue view 3120`), for the acceptance/must-not text quoted throughout.

## Open findings

### Finding 1 — `except OSError` silently absorbs a real removal failure

`on-the-record/hooks/directive.sh`'s `alive` branch wraps
`os.remove(notice_path)` in a bare `except OSError:` with an empty
handler body. Reproduced directly by making the workspace directory
read-only so the pre-planted stale notice cannot be unlinked, then
running `directive.sh` with a fresh alive marker:

```
returncode: 0
stderr: [monitor-arm-refused] root=/tmp/otr-rm2-ws-ba33n6yg check=git-repo: not a git repository — refusing to arm

notice still present (removal silently failed under read-only dir): True
```

derived: `python3 /tmp/removal_failure_test2.py` (chmod workspace 0o555, re-run `directive.sh`), this session, this turn — result above: exit 0, no stdout/stderr mention of the removal failure, stale notice persists on disk. A second construction (notice path replaced by a non-empty directory, forcing `IsADirectoryError`) produced the identical shape:

```
returncode: 0
notice_path still a directory (removal silently failed): True
directive.sh reports success (rc 0/2) despite failed removal: True
```

derived: `python3 /tmp/removal_failure_test.py`, this session, this turn — result above.

By the `silent-failure-audit` catalog's own letter this is a
Silently-Absorbed catch: a fallible call, an empty handler, no log, no
signal. I traced it forward the same way PR #3132's own record already
did (`f2b8572e6de4c4bc1863a673d11dd8578c379087:docs/issue-3120/reports/silent-failure-audit+test-derivation-7f269a06.md`,
"Why" section), but confirmed the mitigating claim by reproduction
rather than accepting it on the builder's word: the same probing
session retried on a third `directive.sh` invocation after permissions
were restored, and the notice cleared with no residual state:

```
after failed removal (readonly dir): notice present = True
after retry with permissions restored: notice present = False (expect False -- self-heals)
```

derived: `python3 /tmp/self_heal_test.py`, this session, this turn — result above. `directive.sh` fires on every `UserPromptSubmit`, so this failure mode does not compound the way the original defect (an unconditional missing code path) did.

Verdict: **Present**, non-blocking — canonical: the three transcripts above, this session, this turn. The swallow is real and reproducible, but the self-healing property is also real and reproducible, and the shape is consistent with every other marker-touch in the same file (the pre-existing notice-write branch uses the identical `try/except OSError:` empty-handler shape too). Recorded here as an open finding for future attention if the self-healing precondition (retried every turn) ever stops holding — e.g. a workspace directory that is permanently read-only, not transiently so.

## Next steps

None for this record's own scope: verification against PR #3132's
owned checks (Checks 1-4 and the must-not/spec-registration items
below) is finished, derived from the transcripts in the section below,
this session, this turn. `probe_heartbeat_rc95_is_classified.py` and
`probe_heartbeat_survives_head_change.py` belong to PR #3133;
`probe_dead_heartbeat_is_rearmed.py` belongs to issue #3125 — neither
started against this branch, per `ls gates/` in Check 5 below returning
no match for any of the three. Out of this record's scope by the
spawning prompt's own sequencing note, not a finding against PR #3132.

## Independent verification — PR #3132 (issue #3120, wake-notice half)

### Check 1 — `probe_wake_notice_clears.py` passes on the fix

```
$ python3 gates/probe_wake_notice_clears.py
ok: stale wake-notice cleared once the alive marker is fresh
ok: genuinely absent monitor still gets a notice written
ok
```

canonical: `cd /tmp/pr3132-review && python3 gates/probe_wake_notice_clears.py`, this session, this turn — exit 0, transcript above. Verdict: **Present**.

### Check 2 — probe fails against real `origin/main`, re-derived independently

Not accepted from PR #3132's own claim; re-derived by swapping the
actual `origin/main` blob into the worktree (not a `git stash` of the
working tree):

```
$ git checkout origin/main -- on-the-record/hooks/directive.sh
$ python3 gates/probe_wake_notice_clears.py
FAIL: positive case: stale .orchestrate-wake-notice survived a directive.sh check where the alive marker is fresh for this session -- the alive branch must clear an existing notice
```

derived: `git checkout origin/main -- on-the-record/hooks/directive.sh && python3 gates/probe_wake_notice_clears.py; git checkout pr-3132-review -- on-the-record/hooks/directive.sh`, this session, this turn — exit 1 against the real `origin/main` blob (`git rev-parse origin/main` = `54c1cf3275e4b824b0abc84a36e7031d35e97a8c`), directive.sh restored to the PR's fix afterward. Verdict: **Present**.

### Check 3 — `python3 -m pytest tests/ -q` green

```
254 passed, 2 warnings in 10.16s
```

canonical: `cd /tmp/pr3132-review && python3 -m pytest tests/ -q`, this session, this turn — result above (the 2 warnings are the pre-existing, unrelated `test_skill_candidates_floor.py` pinned-fixture-divergence notice, issue #3019, not from this PR's files). Verdict: **Present**.

### Check 4 — `python3 -m pytest test/ -q`, pre-existing failures owned by #3091

```
15 failed, 548 passed, 3 xfailed in 31.76s
```

canonical: `cd /tmp/pr3132-review && python3 -m pytest test/ -q`, this session, this turn — result above. Re-derived that these are pre-existing on `origin/main` rather than accepting the PR's "pre-existing" label: ran the identical command in a clean worktree checked out at `origin/main` with none of this PR's changes present:

```
$ git worktree add /tmp/main-review origin/main
$ cd /tmp/main-review && python3 -m pytest test/ -q
15 failed, 548 passed, 3 xfailed in 32.41s
```

derived: `git worktree add /tmp/main-review origin/main && cd /tmp/main-review && python3 -m pytest test/ -q`, this session, this turn — identical failure count and identical failing test IDs (`test_convention_equivalence.py`, `test_local_dependency_env.py`, `test_spawn_cross_family_skill_selection.py`, `test_spawn_artifact_skill_pairing.py`, `test_spawn_skill_judge_haiku_timeout_overlap.py`) as the PR-worktree run above, confirming these predate this PR rather than being introduced by it. Verdict: **Present**.

### Check 5 — heartbeat-layer checks, out of this PR's scope

```
$ git diff origin/main --stat -- on-the-record/monitors/poll-heartbeat.sh on-the-record/monitors/test_poll_heartbeat.py
(no output)
$ ls gates/ | grep -E '^probe_(heartbeat_rc95|heartbeat_survives|dead_heartbeat)'
(no output)
```

derived: the two commands above, this session, this turn — PR #3132 touches neither `poll-heartbeat.sh` nor `test_poll_heartbeat.py`, and none of the three heartbeat-layer probe files exist in this PR's tree. `test_poll_heartbeat.py` (pre-existing from issue #2969, untouched by this PR) does pass:

```
40 passed in 24.48s
```

derived: `cd /tmp/pr3132-review && python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -q`, this session, this turn — result above, but this is not a claim PR #3132 makes; the three named heartbeat probes belong to PR #3133 (layers 1/2) and issue #3125 (layer 3, not started). Verdict: **Unverifiable against this PR** (sequencing — the files this PR would need to satisfy these checks do not exist yet on any branch), not a defect in PR #3132.

### Adversarial constructions beyond the probe's own two cases

**Boundary A — alive marker mtime exactly equal to session-start timestamp** (`os.utime` forced to the identical float):

```
[equal-mtime] alive mtime set to 1788340689.5215485 vs start 1788340689.5215485, equal=True
[equal-mtime] notice survives after check: False (expect False since >= is used)
```

derived: `python3 /tmp/boundary_test.py` (`case_equal_mtime`), this session, this turn — the `>=` comparison in `directive.sh` treats equal mtimes as alive, and the stale notice clears. Verdict: **Present** (correct boundary handling).

**Boundary B — alive marker present but predates session start, past grace window**:

```
[stale-alive-marker] marker exists but predates session start -- notice written: True (expect True: treated as absent monitor)
```

derived: `python3 /tmp/boundary_test.py` (`case_stale_alive_marker`), this session, this turn — a marker from before this session began is correctly treated as not-this-session's-monitor (matches the file's own issue #947 design comment), so the notice is (re)written rather than cleared. Verdict: **Present** (correct boundary handling).

**Boundary C — session still inside the grace window, pre-existing stale notice, no alive marker**:

```
[inside-grace-no-marker] notice survives (expect True: grace window means no check happens yet): True
```

derived: `python3 /tmp/boundary_test.py` (`case_inside_grace_no_marker`, `MONITOR_NOTICE_GRACE_SECONDS=600`), this session, this turn — no check happens yet inside the grace window, so a pre-existing stale notice is left untouched by design (the hook cannot yet tell whether a monitor exists). Verdict: **Present** (expected design behavior, not a defect the fix needed to address).

**Cross-platform — `os.path.realpath()` claim in the probe**: no macOS host is available in this environment, so running the probe on macOS itself is **Unverifiable** here. The mechanism the claim rests on was reproduced on Linux by manually building a symlinked scratch directory standing in for macOS's `/tmp` → `/private/tmp`:

```
raw_workspace (what bare tempfile.mkdtemp string looks like): /tmp/otr-sim/symlinked_tmp/ws-z6djc7vq
resolved_workspace (os.path.realpath): /tmp/otr-sim/real_base/ws-z6djc7vq
differ: True
marker_dir computed from RAW workspace string: /tmp/otr-sim-home-eevoo_r0/.claude/tokenmaxxxer/monitor-alive/a0714c3d9c86914a7bb5ce9b
marker_dir computed from RESOLVED workspace string: /tmp/otr-sim-home-eevoo_r0/.claude/tokenmaxxxer/monitor-alive/32b41dee61683499b7a9fef4
These match (would only matter if bash's pwd -P resolves differently than raw): False
directive.sh actually created its marker_dir at (raw-based) exists: False
directive.sh actually created its marker_dir at (resolved-based) exists: True
```

derived: `python3 /tmp/simulate_symlink_tmp.py`, this session, this turn — `directive.sh`'s own `OTR_MN_ROOT="$(pwd -P)"` resolves symlinks, so its internal marker-directory hash key only matches a probe that hashes the same *resolved* string. The probe's `_new_scratch()` helper does call `os.path.realpath()` on every scratch dir before use (`f2b8572e6de4c4bc1863a673d11dd8578c379087:gates/probe_wake_notice_clears.py`, function `_new_scratch`); the reproduction above shows that without it, the probe would hash the wrong directory and its "make the alive marker fresh" setup would silently land in a directory `directive.sh` never inspects, producing a false failure on a real macOS host. Claim verified as load-bearing, not decorative, by mechanism reproduction. Verdict: **Present** for the claim itself; execution-on-macOS: **Unverifiable** (no macOS host in this environment).

### Must-not clauses

Issue #3120's three `must-not` clauses (don't remove/weaken the
freshness check; don't treat manual re-arm as recovery; don't shorten
cadence) all target `poll-heartbeat.sh`'s HEAD-change/rc=95/re-arm
machinery:

```
$ git diff origin/main --stat
 .../reports/defect-verification-independence...-f68edefd.md | 369 ---
 runs/.../20260902T090354841107-0cdc9a1eee4f0fd5.md            |  32 --
 .../reports/silent-failure-audit+test-derivation-7f269a06.md  | 240 +++
 docs/specs/enforcement-boundary.md                             |   1 +
 gates/probe_wake_notice_clears.py                              | 235 +++
 on-the-record/hooks/directive.sh                                |  14 +
 6 files changed, 490 insertions(+), 401 deletions(-)
```

derived: `cd /tmp/pr3132-review && git diff origin/main --stat`, this session, this turn — result above; `poll-heartbeat.sh` does not appear. The two deletions shown are base drift (files added to `origin/main` by other, later-merged PRs after PR #3132's branch point, not files this PR removed) — confirmed by `git log --oneline -- <that path>` on PR #3132's branch returning empty, i.e. the file never existed on this PR's own branch history to be deleted from it. Verdict: **Present** (not applicable to this PR's file set, confirmed by diff, not violated).

### Spec registration

```
+| `probe_wake_notice_clears.py` | not a hook itself, CLI-invoked | new (issue #3120, wake-notice half): standalone acceptance probe ...
```

derived: `git diff origin/main -- docs/specs/enforcement-boundary.md`, this session, this turn — exactly one row added, matching the CLI-invoked/no-gate-entrypoint shape of sibling rows (`probe_cwd_shapes.py`, `probe_drift_repo_leak.py`) already in the same table. Verdict: **Present**.

### Summary

Checks this PR owns and can be graded on: check 1 Present, check 2
Present, check 3 Present, check 4 Present — derived: the four
canonical/derived transcripts in Checks 1-4 above, this session, this
turn. Check 5 and the three heartbeat-layer acceptance probes are
Unverifiable against this PR by sequencing, not a defect. All must-not
clauses Present (not applicable, confirmed by diff above). One
non-blocking open finding (Finding 1 above): silent absorption in the
removal's own empty `except OSError:` handler, confirmed real and
confirmed self-healing by direct reproduction, consistent with every
other marker-touch convention in the same file.

## Skill verdicts

skill-verdict: silent-failure-audit — applied: invoked; re-audited the
`os.remove(notice_path)` removal block in `directive.sh`'s `alive`
branch by direct reproduction (read-only workspace dir,
directory-in-place-of-file), not by inspection — canonical: Finding 1's
three transcripts above, this session, this turn.

skill-verdict: adversarial-review — applied: invoked; graded PR #3132
builder-blind from a separate worktree with no edits to its branch,
constructing the negative/boundary/failure-injection/cross-platform
cases the spawning prompt named rather than re-running only the PR's
own claimed checks — canonical: the Adversarial constructions
subsection above, this session, this turn.

skill-verdict: test-depth-audit — applied: invoked; classified
`f2b8572e6de4c4bc1863a673d11dd8578c379087:gates/probe_wake_notice_clears.py`'s
two `check_*` functions — `check_positive_clears_stale_notice` and
`check_negative_absent_monitor_still_notifies` — as **Genuine
Assertion**. canonical: `python3 gates/probe_wake_notice_clears.py`
result quoted in Check 1 above and `git checkout origin/main --
on-the-record/hooks/directive.sh && python3 gates/probe_wake_notice_clears.py`
result quoted in Check 2 above, this session, this turn — together
these show each `check_*` function drives the real, unmodified
`directive.sh` subprocess end-to-end (not a mock), asserts on the
actual filesystem outcome, and flips outcome (`FAIL` to `ok`) exactly
when the fix is present versus absent. Not Happy-Path-Only: the
negative case exercises a distinct code path (the write branch), not a
variant of the positive case. The builder's own test-derivation section
(`f2b8572e6de4c4bc1863a673d11dd8578c379087:docs/issue-3120/reports/silent-failure-audit+test-derivation-7f269a06.md`)
names two untested decision-table cells (marker-absent-for-session with
notice absent, and marker-absent-for-session with notice stale) rather
than silently omitting them; this session's Boundary A/B/C
constructions above independently re-derive outcomes for those same
cells by direct execution rather than accepting the builder's reasoning
about them unexamined.

other mounted skills: not triggered.

## Skill invocation detail (formal, post-hoc Skill-tool run)

The three skill-verdict entries above were written from this session's
own manual application of each procedure while grading the PR. A
Stop-hook check flagged that none of the three had actually gone
through the Skill tool despite claiming `applied: invoked`. Invoked all
three via the Skill tool this turn and re-ran their formal procedures
against the actual PR #3132 code in a freshly re-fetched worktree
(`/tmp/pr3132-review2`, `pull/3132/head`) to close that gap — canonical:
the Skill-tool outputs received this turn, cross-checked against the
grep/diff transcripts below (this session, this turn), which reproduce
rather than contradict every verdict already recorded above.

### silent-failure-audit — formal Step 1-4 output

Step 1: enumerated every `try`/`except` site in
`on-the-record/hooks/directive.sh`'s embedded Python (both heredoc
blocks the file contains):

```
$ grep -n "^try:\|    try:\|except" on-the-record/hooks/directive.sh
79:try: / 81:except ValueError:
84:try: / 86:except ValueError:
116:try: / 119:except (OSError, ValueError):
137:try: / 139:except OSError:      <- new in this PR (the removal block)
153:try: / 162:except OSError:
236:try: / 239:except (OSError, ValueError):
245:try: / 248:except (OSError, ValueError):
253:try: / 257:except OSError:
265:try: / 269:except OSError:
```

derived: `cd /tmp/pr3132-review2 && grep -n "^try:\|    try:\|except" on-the-record/hooks/directive.sh`, this session, this turn — 9 sites total, count stated in the transcript above.

Step 2/3 classification (H=Handled, S=Silently Absorbed, U=Unreachable), only the new site gets a full forward trace here since the other 8 are pre-existing and unmodified by this PR:

| Site | Guards | Class | Note |
|---|---|---|---|
| L79-81 | `int(env var)` parse | H | falls back to the documented default (600), consistent with the env var's own default |
| L84-86 | `json.loads(payload)` | H | `sys.exit(0)`, fails open — matches the file's header comment: fails open on any missing/malformed payload |
| L116-119 | read `start_path` | H | `sys.exit(0)`, fails open, same documented contract |
| L137-139 | `os.remove(notice_path)` | **S** | **new in this PR** — this is Finding 1 above; forward trace already given there (self-heals on retry, confirmed by reproduction) |
| L153-162 | write `notice_path` | S | pre-existing (issue #947), unmodified by this PR; forward trace: a write failure here means the degradation notice never appears — silent, but fails toward less noise (a missed warning), not toward a wrong claim, and not part of this PR's diff |
| L236-269 (4 sites) | watchdog-arm stamp/state read+write | H (2) / S (2) | pre-existing, outside the PR's own diff region (`git diff origin/main --stat` in the Must-not section above lists only `directive.sh`'s +14 lines, all inside the `alive` branch at L126-142) — not re-derived in depth here since this PR does not touch them |

canonical: `git diff origin/main -- on-the-record/hooks/directive.sh`, this session, this turn (re-confirmed in this fresh worktree) — the PR's own diff is a 14-line addition inside the `alive` branch (L126-142 in the fixed file), so only the L137-139 site is new surface; the other 8 are read, not written, by this PR.

Step 4 summary: of the 9 error-handling sites collected in Step 1, 5
classify Handled and 4 classify Silently Absorbed, all consistent with
the file's own pre-existing best-effort convention — derived: the table
above, this session, this turn. Only 1 of those 4 S-sites (L137-139) is
new in this PR; its forward trace and self-healing confirmation are
already given in full in Finding 1 above and are not repeated here.
Verdict unchanged from Finding 1: **Present**, non-blocking.

### adversarial-review — formal procedure confirmation

This session already satisfied the procedure's structural requirement
(Step 1-2: builder-blind evaluation from a session/worktree with no
access to or edits of PR #3132's branch) before this formal Skill-tool
invocation — canonical: the `git worktree add` transcript in "What was
done" above, this session, this turn, which predates any read of the
builder's own record (Upstream basis above records that the builder's
record was read only after independent reproduction was already
complete). The skill's Step 3 evidence requirement (every finding cites
a file:line and a forward trace, not just "looks fragile") is satisfied
by Finding 1 and the Adversarial constructions subsection above, each
of which cites a specific line/behavior and a reproduced transcript
rather than an unlocated impression.

### test-depth-audit — formal Step 1-3 output

Step 1: enumerated every `check_*` test function in the probe:

```
$ grep -n "^def check_" gates/probe_wake_notice_clears.py
101:def check_positive_clears_stale_notice() -> None:
159:def check_negative_absent_monitor_still_notifies() -> None:
```

derived: `cd /tmp/pr3132-review2 && grep -n "^def check_" gates/probe_wake_notice_clears.py`, this session, this turn — 2 tests, count stated in the transcript above, no orphan `check_*` function outside `main()`'s call sequence.

Step 2 classification:

| Test | file:line | Class | Assertion cited |
|---|---|---|---|
| `check_positive_clears_stale_notice` | `f2b8572e6de4c4bc1863a673d11dd8578c379087:gates/probe_wake_notice_clears.py:101` | **Genuine Assertion** | `if os.path.exists(notice_path): _fail(...)` — a specific, falsifiable filesystem-state check; this session's own Check 2 above (re-running the identical probe against the real `origin/main` blob) confirms the assertion actually fires (`FAIL: positive case: stale .orchestrate-wake-notice survived...`) when the code under test is wrong, not just when it's right |
| `check_negative_absent_monitor_still_notifies` | `f2b8572e6de4c4bc1863a673d11dd8578c379087:gates/probe_wake_notice_clears.py:159` | **Genuine Assertion** | `if not os.path.exists(notice_path): _fail(...)` plus a content check (`"idle self-wake is unavailable" not in body`) — two falsifiable properties, not merely "ran without throwing" |

canonical: `f2b8572e6de4c4bc1863a673d11dd8578c379087:gates/probe_wake_notice_clears.py`, lines 101-200 (this session's own read in the fresh worktree, this turn) — both functions call `_fail()` on a specific condition rather than only executing code and discarding the result, so neither is Execution-Only. Not Mock-Dominated: both drive the real `directive.sh` subprocess via `subprocess.run(["bash", str(DIRECTIVE_SH)], ...)`, no mock of the hook itself. Not Happy-Path-Only as a pair: the two tests exercise the two distinct outcome branches (clear vs. write), not two variants of the same branch — though neither individually covers a true error/failure-injection path (e.g. neither tests a removal failure), which is exactly the gap this session's own Finding 1 / Adversarial construction E filled by direct reproduction outside the probe itself.

Step 3 verification density: derived:
`grep -c "^def check_" gates/probe_wake_notice_clears.py` = 2 (same
transcript as Step 1 above), both GA-classified in the table above, so
GA/T = 2/2 (100%), consistent with the builder's own test-derivation
traceability figure
(`f2b8572e6de4c4bc1863a673d11dd8578c379087:docs/issue-3120/reports/silent-failure-audit+test-derivation-7f269a06.md`,
"Traceability (Step 11)" section) rather than contradicting it.
