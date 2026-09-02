---
issue: 3120
role: silent-failure-audit+experiment-trust+adversarial-review-bd34ba25
author: silent-failure-audit+experiment-trust+adversarial-review-bd34ba25
skills: silent-failure-audit (skill-repository(c05de12)), experiment-trust (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3132's own deliverable, author differs -- see docs/handbooks/observer-verification.md
loop_state: complete
upstream:
  - path: PR #3132, branch issue-3120/silent-failure-audit+test-derivation-7f269a06
    sha: f2b8572e6de4c4bc1863a673d11dd8578c379087
---

# issue-3120 — silent-failure-audit+experiment-trust+adversarial-review-bd34ba25 record

## What was done

Second, independent, builder-blind verification of PR #3132 (issue
#3120's wake-notice half) from a fresh worktree, never editing or
checking out the PR onto this session's own branch.

```
$ git worktree add /tmp/verify-pr3132 pr-3132
Preparing worktree (checking out 'pr-3132')
HEAD is now at f2b8572e issue-3120: invoke test-derivation skill, correct invoked-mismatch
```

canonical: this session's own `git worktree add` transcript above, this turn.

The first verification (PR #3138) already ran the negative case, three
boundary conditions, and one removal-failure injection, and graded 4/4
Present. Per `defect-verification-independence-from-upstream-verdicts`,
I did not read its transcripts before forming my own conclusions on the
questions the spawning prompt asked me to emphasize; I only used its
summary (visible in the PR list) to know which ground was already
covered, then went further rather than re-deriving the same four items.

**1. Re-derived the acceptance probe directly.** The probe file
(`gates/probe_wake_notice_clears.py`) is untracked on this branch —
it lives only on PR #3132's branch until it merges, so every run below
was executed inside the separate `/tmp/verify-pr3132` worktree, never
this branch's own working tree.

```
$ cd /tmp/verify-pr3132 && python3 gates/probe_wake_notice_clears.py
ok: stale wake-notice cleared once the alive marker is fresh
ok: genuinely absent monitor still gets a notice written
ok
$ echo $?
0
```

```
$ cd /tmp/verify-pr3132 && git checkout origin/main -- on-the-record/hooks/directive.sh && python3 gates/probe_wake_notice_clears.py
FAIL: positive case: stale .orchestrate-wake-notice survived a directive.sh check where the alive marker is fresh for this session -- the alive branch must clear an existing notice
$ echo $?
1
```
(reverted with `git checkout HEAD -- on-the-record/hooks/directive.sh` afterward, inside `/tmp/verify-pr3132`)

canonical: both transcripts above, run this turn against PR #3132's
own worktree and against the real `origin/main` blob of
`directive.sh` (not a claim taken from the PR body).

**2. PR #3133 exec-restart interaction (the spawning prompt's first named emphasis).**

Read `on-the-record/monitors/poll-heartbeat.sh` in PR #3133's branch
(`pr-3133`, fetched via `git fetch origin pull/3133/head:pr-3133`).
The alive-marker touch is one-shot, before the tick loop:

```
# poll-heartbeat.sh:110-118 (comment on the touch itself, PR #3133 branch):
# Written before the sleep loop so it reflects "the monitor process
# launched", not "a tick completed".
_alive_dir="$(PWD_P="$(pwd -P)" python3 -c '...')"
if [ -n "${_alive_dir}" ]; then
  mkdir -p "${_alive_dir}" 2>/dev/null && \
    touch "${_alive_dir}/alive" 2>/dev/null || true
fi
```

canonical: `git show pr-3133:on-the-record/monitors/poll-heartbeat.sh` output, read this turn, lines 95-118.

PR #3133's `exec bash "${_exec_target}"` (poll-heartbeat.sh:597, on
`watchdog_rc == 95`) replaces the process image and re-runs the entire
script from the top, so this touch fires again on every exec-restart,
not just first launch — confirmed by reading the diff:

```
$ git diff origin/main pr-3133 -- on-the-record/monitors/poll-heartbeat.sh
+      _exec_target="${CHECKOUT}/on-the-record/monitors/poll-heartbeat.sh"
+      if [ -f "${_exec_target}" ]; then
+        printf '[poll-heartbeat] stale code (rc=95) -- restarting via exec %s\n' "${_exec_target}"
+        exec bash "${_exec_target}"
```

canonical: transcript above, this turn (`git diff origin/main pr-3133 -- on-the-record/monitors/poll-heartbeat.sh`).

`directive.sh`'s alive check is `os.path.getmtime(alive_path) >= start`
where `start` is this session's OWN first-observed timestamp
(`git show pr-3132:on-the-record/hooks/directive.sh`, lines 103-125).
Since `touch` only ever sets mtime to *now*, and an exec-restart
happens strictly after the session that owns that monitor already
started, the re-touch can only move `alive` False→True or leave it
True — it cannot introduce staleness for the monitor's own session.
Confirmed by simulation (constructed this session, throwaway, not
shipped in the PR):

```
$ python3 /tmp/verify_scenarios.py   # scenario_exec_interaction()
monitor started, alive mtime=1788343809.5698178
session start recorded, start mtime=1788343809.6948202
monitor alive mtime < session start (pre-exec alive=False)
monitor exec-restarts, alive mtime re-touched to 1788343809.7708213
post-exec directive.sh turn: notice exists = False
```

derived: `python3 /tmp/verify_scenarios.py` (scenario 1), this turn.

Verdict: the spawning prompt's hypothesis (exec makes the monitor
"look freshly started and therefore stale-until-first-stamp") does
**not** hold. The freshness comparison directive.sh makes is monotone
in the re-touch's favor, not against it — opposite of a flapping
regression, for the monitor's own session.

**3. Shared-workspace clearing/flapping (the spawning prompt's second named emphasis).**

Simulated two sessions in one workspace — one whose monitor is alive,
one whose monitor is absent — across 7 directive.sh turns:

```
$ python3 /tmp/verify_scenarios.py   # scenario_shared_workspace_flap()
turn2 (alive session, post-grace): notice exists = False
turn4 (absent session, post-grace, first check): notice exists = True
turn5 (absent session, already notified): notice mtime unchanged = True
turn6 (alive session, subsequent turn): notice exists = False
turn7 (alive session, again): notice exists = False
```

derived: `python3 /tmp/verify_scenarios.py` (scenario 2), this turn.

Mechanism read from `git show pr-3132:on-the-record/hooks/directive.sh`
lines 103-145: `notified_path` is per-session and gates BOTH branches
— once a session has written the notice once, every later turn of
that SAME session short-circuits before the alive check, so it can
never rewrite (no repeated flap from one session). The alive branch
carries no such latch, so an alive session clears on every post-grace
turn, forever. Net effect measured above: not a sustained flap — it
settles to "notice absent" as long as some alive session keeps taking
turns after the absent session's one-time write.

**4. Symlink injection — removal branch destructiveness and failure signaling.**

The first verification injected read-only and directory-in-place-of-file.
Added a symlink pointing outside the workspace, both succeeding and
failing:

```
$ python3 /tmp/verify_scenarios.py   # scenario_symlink_outside_workspace()
outside target survives = True, content unchanged = True
symlink entry itself removed from workspace = True
directive.sh reported success (rc in (0,2)) = True
```

```
$ python3 /tmp/verify_scenarios.py   # scenario_symlink_removal_fails(), chmod 555 on workspace dir
directive.sh rc=0 (0/2 both mean 'ran to completion, no directive failure')
symlink dirent survives removal failure = True
outside target untouched = True
```

derived: `python3 /tmp/verify_scenarios.py` (scenarios 3-4), this turn.

`os.remove()` follows POSIX `unlink()` semantics — it removes the
symlink dirent itself, never the target it points to, regardless of
whether the target is inside or outside the workspace; this is a
guarantee of `os.remove()` itself, not something the fix's code has to
special-case. On a removal failure (`PermissionError`, an `OSError`
subclass, from a read-only parent dir), the bare
`except OSError: pass` (`git show pr-3132:on-the-record/hooks/directive.sh`
lines 135-138) swallows it — consistent with every other best-effort
marker touch already in that file (`hook_fires_record`, the GC call,
the notice write itself all use the identical
`except OSError: pass` / `|| true` shape, confirmed by reading the
full file this turn). It does not report false success in any
observable sense: this branch's `sys.exit(0)` already meant "the
directive ran" on every other `directive.sh` path — there is no
separate "notice removed: true/false" signal anywhere in this hook for
a removal failure to falsify.

**5. Full test suite, run against PR #3132's own worktree.**

```
$ cd /tmp/verify-pr3132 && python3 -m pytest tests/ -q
254 passed, 2 warnings in 10.27s
```

```
$ cd /tmp/verify-pr3132 && python3 -m pytest test/ -q
15 failed, 548 passed, 3 xfailed in 32.06s
```

canonical: both transcripts, this turn, against PR #3132's real
worktree (not accepted from the PR body's claim). `tests/` (the suite
this issue's own acceptance line names) matches exactly: 254 passed.

`test/` (not named in this issue's acceptance line, but claimed in the
PR body as "15 failed, pre-existing, owned by #3091, unrelated to this
change") needed independent bisection, since a bare `origin/main`
worktree checked out fresh came back fully green:

```
$ cd /tmp/verify-main && python3 -m pytest test/ -q     # origin/main, tip 02c3c8cb
563 passed, 3 xfailed in 32.02s
```

Bisected by isolating PR #3132's own 3 changed files from everything
else:

```
$ git merge-base pr-3132 origin/main
820e9dc5ecbcbadf00ad3f03406e1e375837e3a2
$ git diff --stat 820e9dc5 origin/main -- spawn.py test/test_local_dependency_env.py \
    test/test_spawn_cross_family_skill_selection.py test/test_spawn_artifact_skill_pairing.py \
    test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_convention_equivalence.py
 spawn.py                                        | 12 ++++++++
 test/test_convention_equivalence.py             | 19 ++++++++----
 test/test_local_dependency_env.py               |  9 +++++-
 ... (6 files changed, 85 insertions(+), 31 deletions(-))
$ git log --oneline 820e9dc5..origin/main -- spawn.py test/test_local_dependency_env.py \
    test/test_spawn_cross_family_skill_selection.py
73b614fd [issue-3091/implementation-blueprint+test-derivation+silent-failure-audit-a7dcf475] (#3139)
b35391ea issue-3118: sweep-orphans for /tmp worktrees, stale workspaces, and session logs (#3126)
$ git checkout -b test-pr3132-content pr-3132 && python3 -m pytest test/ -q
15 failed, 548 passed, 3 xfailed in 31.98s   # same 15 test names, byte-identical set
$ git diff --stat 820e9dc5 pr-3132 -- spawn.py test/test_local_dependency_env.py \
    test/test_spawn_cross_family_skill_selection.py test/test_spawn_artifact_skill_pairing.py \
    test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_convention_equivalence.py
   # (no output -- byte-identical to the merge-base for all 6 files)
```

canonical: all four transcripts above, this turn, run from a scratch
`/tmp/verify-main` worktree of `origin/main`.

`spawn.py` and the 5 affected test files on PR #3132's branch are
byte-identical to the merge-base — PR #3132's own commit never touched
them. Commit `73b614fd`, tagged `[issue-3091/...]`, is the fix that
made `test/` green on current `origin/main`; it landed AFTER PR #3132's
branch point, and (per the recent-commits list visible at session
start) also after the first verification (`a80cd550`, PR #3138) ran —
which is why that verification's "confirmed identical against a clean
origin/main worktree" was accurate *at the time it ran* but does not
reproduce against `origin/main` today. The `#3091` attribution is
independently confirmed correct by this bisection; the "pre-existing"
framing needs a rebase-currency caveat, not a correctness correction.

**6. Registration collision (found, not asked for).**

```
$ git diff origin/main pr-3132 -- docs/specs/enforcement-boundary.md
-| `probe_orphan_sweep_spares_live.py` | ... (issue #3118) ...
+| `probe_wake_notice_clears.py` | ... (issue #3120, wake-notice half) ...
$ git diff --stat 820e9dc5 pr-3132 -- docs/specs/enforcement-boundary.md
 docs/specs/enforcement-boundary.md | 1 +
 1 file changed, 1 insertion(+)
```

canonical: both transcripts above, this turn. The second command shows
PR #3132's own commit is a pure insertion against its own base — it
never had the probe's registration row to delete; that row was added
to `origin/main` by issue #3118, also after PR #3132's branch point.
The `git diff origin/main pr-3132` rendering as a replacement is a
stale-branch diff artifact, not a deletion in PR #3132's own commit.
It is, however, a real insertion-adjacent-to-insertion merge conflict
that will surface (visibly, via ordinary `git merge`/rebase conflict
markers, not silently) whenever this PR is actually landed.

**7. Per-criterion verdict table**, each classification following
`implementation-audit`'s taxonomy against items 1-6 above (a Present
claim only stands if it also survives the edge/error-path depth check
that skill requires):

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| a | Positive case: stale notice clears once alive marker is fresh | Present | item 1, first transcript |
| b | Negative case: genuinely absent monitor still gets a notice | Present | item 1, first transcript |
| c | Probe fails against real unmodified `origin/main` | Present | item 1, second transcript |
| d | PR #3133 exec-restart does not make the monitor's own session see a spurious/flapping notice | Present | item 2, all transcripts |
| e | Shared-workspace notice clearing does not sustain a flap across sessions | Present | item 3, transcript |
| f | Removal branch does not destructively follow a symlink pointing outside the workspace | Present | item 4, first transcript |
| g | Removal failure is swallowed without propagating a directive.sh failure or false success signal | Present | item 4, second transcript |
| h | `tests/ -q`, this issue's own acceptance-named suite | Present | item 5, first transcript |
| i | `on-the-record/monitors/test_poll_heartbeat.py -q` and the two heartbeat probes | Unverifiable (sequencing, owned by PR #3133/#3125 per the spawning prompt's own scoping) | out of PR #3132's file set |
| j | `docs/specs/enforcement-boundary.md` registration | Present, with a residual rebase-conflict caveat | item 6, both transcripts |

canonical: `git show pr-3132:on-the-record/hooks/directive.sh`, lines
103-145 (the full alive/notice block, already quoted piecemeal in
items 1-4 above), re-read in full this turn for the trace below.

Per `silent-failure-audit`'s own taxonomy, the removal branch's bare
`except OSError: pass` mechanically classifies as **Silently
Absorbed** (an empty-equivalent catch), not Handled — named here
rather than glossed over. Forward-traced per that skill's Step 3:
catch site (lines 135-138) → no return value consulted by any caller
(this is a top-level script exit, not a function with a caller) → no
downstream code in the file reads a "notice removed" flag →
`sys.exit(0)` fires unconditionally on this branch whether or not the
removal succeeded (confirmed by the symlink-removal-fails transcript
in item 4). The trace ends at "the program continues with no
indication either way" — benign here specifically because item g
above already confirmed nothing downstream depends on it, and because
every other marker touch in this same file (`hook_fires_record`'s
write, the GC subprocess call, the notice write itself, all read this
turn) already uses the identical best-effort/no-consumer shape — this
is the file's established convention, not a one-off introduced by this
fix.

## Why

`adversarial-review` + `defect-verification-independence-from-upstream-verdicts`:
graded every criterion by direct reproduction in a worktree the PR
author never touched, re-deriving the acceptance probe's pass/fail
delta against the real `origin/main` blob rather than accepting either
PR's or the first verification's claims. Where the spawning prompt
named a specific new construction (the PR #3133 exec interaction, the
shared-workspace flap, the outside-workspace symlink), I built and ran
a runnable scratch reproduction for each rather than reasoning about
mechanism only from reading the code.

## What did not work

Initially copied the wake-notice probe script to `/tmp` to run it
against a plain `origin/main` checkout without disturbing the
worktree; the probe computes its own repo root from `__file__`, so the
copy resolved a wrong `directive.sh` path and failed on an unrelated
setup error rather than testing anything:

```
$ cp gates/probe_wake_notice_clears.py /tmp/probe_wake_notice_clears_copy.py   # run inside /tmp/verify-pr3132
$ python3 /tmp/probe_wake_notice_clears_copy.py
FAIL: directive.sh not found at /on-the-record/hooks/directive.sh
```

derived: transcript above, this turn. Fixed by running the probe in
place inside the `/tmp/verify-pr3132` worktree and swapping
`directive.sh`'s content in and out with
`git checkout <ref> -- on-the-record/hooks/directive.sh` instead (used
throughout item 1 above).

## Upstream basis

- PR #3132, branch `issue-3120/silent-failure-audit+test-derivation-7f269a06`, sha `f2b8572e6de4c4bc1863a673d11dd8578c379087` (real, fetched via `git fetch origin pull/3132/head:pr-3132`)
- PR #3133, branch `issue-3120/silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0` (read-only, for the exec-interaction question only; not graded, not edited)
- `origin/main`, tip `02c3c8cb` at review time (real, fetched)

## Open findings

1. **PR #3132 is stale relative to current `origin/main`; rebase before landing.** Its branch predates commit `73b614fd` (#3139), so its own `test/ -q` run still shows the 15 failures #3091 already resolved on `origin/main`.
   derived: `cd /tmp/verify-main && git checkout -b test-pr3132-content pr-3132 && python3 -m pytest test/ -q` — result: `15 failed, 548 passed, 3 xfailed`, versus `git checkout origin/main && python3 -m pytest test/ -q` — result: `563 passed, 3 xfailed`, both run this turn (full transcripts in item 5 above). Not a defect in PR #3132's delivered code — a landing-readiness note. Resolution path: rebase onto current `origin/main` before merge (same pattern already used for PR #3126: commit `02c3c8cb`, "issue-3118: rebase PR #3126 onto origin/main").
2. **`docs/specs/enforcement-boundary.md` will merge-conflict, not silently drop a row.** PR #3132's insertion and issue #3118's registration-row insertion land at the same location relative to their common ancestor.
   derived: `git diff --stat 820e9dc5 pr-3132 -- docs/specs/enforcement-boundary.md` — result: pure `1 insertion(+)`, confirming PR #3132's own commit deletes nothing (full transcript in item 6 above). Resolution path: same rebase as finding 1 will surface this as an ordinary conflict to resolve by hand, not a silent loss.
3. **Notice-clearing is turn-driven, not swept.** If the last alive-session turn in a shared workspace happens to precede a later absent-monitor session's one-time notice write, the notice persists until some future alive session's turn.
   derived: `python3 /tmp/verify_scenarios.py` (scenario 2, `scenario_shared_workspace_flap`), this turn — transcript in item 3 above shows the write/clear pattern this conclusion is drawn from. Bounded and self-healing (no sustained flap observed across the 7 simulated turns), matches the fix's stated scope in issue #3120 (no sweep was ever asked for) — named here as a known limit, not a defect to fix in this PR.

None of the three findings above block PR #3132's own owned acceptance
item: the wake-notice probe passes on the fix and fails on the real
`origin/main` blob (item 1 transcripts), and `tests/ -q` — the suite
this issue's acceptance line actually names — passed clean
(`254 passed, 2 warnings in 10.27s`, item 5 transcript).

## Next steps

derived: `python3 /tmp/verify_scenarios.py` and
`python3 -m pytest tests/ -q` / `python3 -m pytest test/ -q`, all run
this turn, transcribed in items 1-5 above.

No further action from this session — both spawner-named constructions
(item 2, item 3) and the routine checks (items 1, 4, 5) were run this
turn against real subprocesses with no check left unexecuted, so this
record's own frontmatter loop-state field is set to its terminal value
for this record kind. Findings 1-2 are actionable by whoever lands PR
#3132 (rebase before merge); finding 3 is informational only.

## Skill verdicts

derived: items 1-7 of `## What was done` above (all transcripts
already cited there) are the basis for every `applied:` line below —
no new command runs are needed to support this section.

skill-verdict: adversarial-review — applied: invoked; this whole
record is Session B of the two-party protocol against PR #3132's
deliverable (Session A), reproduced from a fresh worktree with no
shared context with the PR's own authoring session, per items 1-6 in
What was done.

skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; re-derived the acceptance probe's pass/fail delta against the real `origin/main` blob (item 1) rather than citing the first verification's (PR #3138) already-Present grade, and devised negative/edge constructions (item 4's symlink injections) rather than only happy-path checks.

skill-verdict: silent-failure-audit — applied: invoked; classified the removal branch's `except OSError: pass` as Silently Absorbed (not Handled) per the catalog and forward-traced it to its endpoint in item 7 of What was done, rather than accepting "best-effort" as self-evidently safe.

skill-verdict: implementation-audit — applied: invoked; item 7's per-criterion verdict table applies the Present/Surface/Absent/Incorrect/Unverifiable taxonomy with the required edge/error-path depth check on each Present claim.

skill-verdict: work-in-english — applied: invoked; this entire record (commit messages, this document) is written in English per the policy; the end-of-turn summary to the user is in Korean.

skill-verdict: experiment-trust — not-applicable: no A/B or variant-comparison experiment is involved in verifying a hook fix.
