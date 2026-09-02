---
issue: 3120
role: implementation-blueprint+silent-failure-audit-91ef1225
author: implementation-blueprint+silent-failure-audit-91ef1225
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
type: chore
breaking: false
verdict: delivered
upstream:
  - path: docs/issue-3120/reports/silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0.md
    sha: eec9a051c8d9d4dc4c68ebcfa4a3bcc0f9a6fe41
  - path: docs/issue-3120/reports/silent-failure-audit+test-derivation-7f269a06.md
    sha: f2b8572e6de4c4bc1863a673d11dd8578c379087
---

# issue-3120 — implementation-blueprint+silent-failure-audit-91ef1225 record

## What was done

Combined PR #3132 (branch `issue-3120/silent-failure-audit+test-derivation-7f269a06`,
tip `f2b8572e6de4c4bc1863a673d11dd8578c379087` — untracked in this record's
own branch working tree, present on that PR's branch: `probe_wake_notice_clears.py`
+ `on-the-record/hooks/directive.sh`) and PR #3133 (branch
`issue-3120/silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0`,
pre-merge tip `eec9a051c8d9d4dc4c68ebcfa4a3bcc0f9a6fe41` — also untracked here,
present on that PR's branch: `probe_heartbeat_rc95_is_classified.py`,
`probe_heartbeat_survives_head_change.py` (untracked in this record's own
branch working tree, present on PR #3133's branch),
`on-the-record/monitors/poll-heartbeat.sh`) into one landable delivery, per
issue #3120's five-check Acceptance section being split across the two
disjoint-file PRs.

skill-verdict: silent-failure-audit — applied: invoked; used the trace-forward
method narrowly on the one interaction the spawning task named (does PR
#3133's `exec` self-heal leave PR #3132's staleness/notice checks reading a
"stale-until-first-stamp" window) rather than a full site-enumeration audit
of the merged tree. canonical: this session's own trace of
`on-the-record/monitors/poll-heartbeat.sh` and `on-the-record/hooks/directive.sh`
plus a scratch empirical harness run this turn — see "Open findings" #2.
skill-verdict: implementation-blueprint — not-applicable: this task combines
two already-complete PR branches (a git merge + verification), it does not
write new code spanning modules or fan out parallel workers needing a frozen
contract.

Steps taken, in order:

1. `git checkout -B issue-3120/silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0 origin/issue-3120/silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0` (PR #3133's own branch, checked out under its own name so the eventual push lands on that branch directly, not a throwaway).
2. `git merge --no-ff origin/issue-3120/silent-failure-audit+test-derivation-7f269a06` (PR #3132's branch) into it.
3. Ran the five acceptance checks plus `tests/` on the resulting merge commit.
4. Investigated the named exec/notice interaction (see "Open findings" #2).
5. Pushed the merge commit directly to `issue-3120/silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0` (PR #3133's branch on origin), making PR #3133 the combined deliverable. PR #3132 left open and untouched — the orchestrator closes it separately with a note pointing at #3133.

Merge commit: `606279df354616719a5965e4f0b48449048eefcf` on
`issue-3120/silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0`.
canonical: `git push origin issue-3120/silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0` output this turn — `eec9a051..606279df issue-3120/silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0 -> issue-3120/silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0`, confirming PR #3133 (that branch) now carries both PRs' commits.

## Why

`git merge --no-ff` of PR #3132's branch into PR #3133's branch produced
zero conflicts.
canonical: `git merge --no-ff origin/issue-3120/silent-failure-audit+test-derivation-7f269a06 -m "..."` output this turn — `Merge made by the 'ort' strategy.` followed by an 8-file diffstat, no `CONFLICT` line.
The task's anticipated conflict site, `docs/specs/enforcement-boundary.md`,
merged cleanly between the two PRs: PR #3133 never touched that file at all —
derived: `git log origin/main..origin/issue-3120/silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0 --oneline -- docs/specs/enforcement-boundary.md` — result: empty output (no commits) — so PR #3132's one-line addition (the `probe_wake_notice_clears.py` registration row) applied on top of PR #3133's untouched copy with no overlap. The `docs/issue-3120/` record trees are disjoint filenames
(`silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0.md`
vs `silent-failure-audit+test-derivation-7f269a06.md`), so those merged with
no conflict either — "take both sides" required no actual git-level
intervention here, both sides just landed side by side.

Acceptance checks, run on the merge commit
(`606279df354616719a5965e4f0b48449048eefcf`), this turn:

```
acceptance: python3 gates/probe_heartbeat_rc95_is_classified.py — result:
ok
exit:0

acceptance: python3 gates/probe_heartbeat_survives_head_change.py — result:
ok
exit:0

acceptance: python3 gates/probe_wake_notice_clears.py — result:
ok: stale wake-notice cleared once the alive marker is fresh
ok: genuinely absent monitor still gets a notice written
ok
exit:0

acceptance: python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -q — result:
46 passed in 26.66s

acceptance: python3 -m pytest tests/ -q — result:
254 passed, 2 warnings in 10.16s
```

Acceptance requirement met — 5 of 5 checks pass on the combined branch
(all five commands above exited 0 / reported all-pass, this turn, no
skipped or xfailed items in the pytest summaries).

`tests/` reported separately per instruction using the same
`acceptance: python3 -m pytest tests/ -q` run quoted directly above —
result: 254 passed, 0 failed on this run — no pre-existing failures
surfaced within `tests/` itself. The 15 pre-existing failures the
spawning task named as owned by #3091 live under `test/` (singular), a
different top-level directory from the `tests/` (plural) acceptance-check
target named in the issue's Acceptance section, and were not exercised by
this check.

## What did not work

None — the merge itself required no conflict resolution (see "Why",
canonical: the `git merge --no-ff` output cited there, no `CONFLICT` line).
One deviation from the spawning task's assumption: it anticipated a real
conflict in `docs/specs/enforcement-boundary.md` between the two PRs; none
existed. A different, pre-existing conflict was found there instead —
canonical: `git merge-tree` output quoted in "Open findings" #1 below — between
the combined branch and current `origin/main`, present identically on each
original PR's branch alone (checked independently before combining anything,
same "Open findings" #1 citation), which is outside this task's scope: the
spawning prompt's instructions named only checkout-3133 / merge-3132 /
run-checks / push-to-3133 as the authorized steps, with no rebase-onto-main
step, and this repository's own recent commit history (`git log --oneline -5`
on this branch, this session's start-of-conversation git status) shows
rebase-onto-main handled as its own separate session type for other PRs
(e.g. "issue-3120: rebase PR #3140 onto origin/main" `82156c31`, "issue-3118:
rebase PR #3126 onto origin/main" `02c3c8cb`).

## Upstream basis

- `docs/issue-3120/reports/silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0.md` — sha `eec9a051c8d9d4dc4c68ebcfa4a3bcc0f9a6fe41` (PR #3133's branch tip before this merge; untracked in this record's own branch working tree, present on that commit — `derived: git show eec9a051c8d9d4dc4c68ebcfa4a3bcc0f9a6fe41 --stat | head -5`).
- `docs/issue-3120/reports/silent-failure-audit+test-derivation-7f269a06.md` — sha `f2b8572e6de4c4bc1863a673d11dd8578c379087` (PR #3132's branch tip; same untracked-here/present-on-that-commit status).
- Both PRs' own upstream claims (layer 1/2 rc=95 classification + exec self-heal for #3133; wake-notice clear for #3132) are unmodified by this session. canonical: `git diff eec9a051..606279df -- on-the-record/monitors/poll-heartbeat.sh gates/probe_heartbeat_rc95_is_classified.py gates/probe_heartbeat_survives_head_change.py` and `git diff f2b8572e..606279df -- on-the-record/hooks/directive.sh gates/probe_wake_notice_clears.py` (both run this turn during the merge/verify sequence) show only the merge's own file-union, no content edits to either side's code/probes — this session moved no line of either PR's code or probes, only merged the two commit histories and pushed.

## Open findings

1. Pre-existing `origin/main` conflict on `docs/specs/enforcement-boundary.md`,
   present on each original PR independently, not introduced by this merge.
   derived: `git merge-tree $(git merge-base origin/main origin/issue-3120/silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0) origin/main origin/issue-3120/silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0 | grep -c "changed in both"` — result: `1`; the identical check against PR #3132's branch alone (`origin/issue-3120/silent-failure-audit+test-derivation-7f269a06`) — result: `1`. `origin/main` has since removed the `probe_orphan_sweep_spares_live.py` row that both PRs' shared base commit (`820e9dc5`) still carried; each PR's branch still has that row untouched, adjacent to each PR's own new-row addition, producing an add/near-delete conflict against current `main` (base hash `64bf3a19`, main's current hash `ab19523d`, combined-branch hash `4ecd6738` — `derived: git diff origin/main origin/issue-3120/silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0 -- docs/specs/enforcement-boundary.md` shown this turn). Mechanical to resolve (drop the stale row `main` already dropped, keep each PR's own addition), not a semantic choice between #3132 and #3133's own content — but resolving it means rebasing onto `main`, which this task's brief did not authorize. `derived: gh pr view 3133 --json mergeable -q .mergeable` — result: `CONFLICTING`, for this reason. Flagged for the orchestrator; not fixed here.

2. The named exec-restart / wake-notice interaction: traced and empirically
   probed this turn, no flapping found. Question asked: after PR #3133's
   `exec` self-heal on `rc=95`, is the freshly-exec'd monitor read as
   "stale-until-first-stamp" by PR #3132's notice logic, producing a notice
   a later turn then clears?
   - canonical: `on-the-record/monitors/poll-heartbeat.sh` lines 110-119 (the
     workspace-scoped `alive` marker touch that `.orchestrate-wake-notice`'s
     clear logic in `directive.sh` checks, `probe_wake_notice_clears.py`'s
     target — both untracked in this record's own branch working tree,
     present on PR #3133's / #3132's branches respectively) sit in the
     script's top-level startup code, before the tick loop — `exec bash
     "${_exec_target}"` at line 598 restarts execution from line 1 of the
     target script, so that startup touch re-runs on every exec restart, not
     just the original launch.
   - canonical: `on-the-record/hooks/directive.sh`'s second, separate
     staleness mechanism, `_monitor_liveness_check_and_notify` (the
     `[orchestrate][MONITOR-DEAD]` per-turn line, de-duped by a `last_tick`
     episode key — the mechanism that actually matches "a notice a later
     turn clears", since its episode state silently clears once a fresh
     stamp arrives, `directive.sh` lines ~251-259) reads
     `runs/poll_heartbeat_alive.json`'s `last_tick`, written by
     `_alive_stamp_write` unconditionally on every loop iteration
     (`poll-heartbeat.sh` line 484), including the iteration that goes on to
     hit `rc=95` and `exec` — so a fresh stamp already exists moments before
     every restart, and the default 360s staleness threshold
     (`MONITOR_LIVENESS_STALE_SECONDS:-360`) has ample margin over the
     default 120s tick cadence (`POLL_HEARTBEAT_SLEEP_SECONDS:-120`).
   - derived: a scratch harness run this turn (not committed, deleted after
     use — reused `gates/probe_heartbeat_survives_head_change.py` (untracked
     in this record's own branch working tree, present on PR #3133's
     branch)'s real-`poll-heartbeat.sh`-plus-fake-`spawn.py` scaffold;
     `POLL_HEARTBEAT_SLEEP_SECONDS=5`, sampling the actual
     `runs/poll_heartbeat_alive.json` stamp and the `alive` marker's mtime
     through the `rc=95` → `exec` boundary) — result: `MAX observed gap:
     5.46s (threshold 360s)` / `ANY sample perceived as stale: True` (only
     before the very first tick ever wrote a stamp, i.e. `last_tick is
     None`, which is correct/expected — not the exec-restart window); the
     `alive` marker's final mtime landed ~5.1s after launch (at the
     exec-restart moment), not at the original t=0 launch, confirming it
     gets re-touched at restart rather than left stale until the next full
     tick.
   - Conclusion: no flapping observed or expected from this interaction —
     both mechanisms already have a fresh timestamp at or immediately after
     the exec boundary, by construction (the stamp write precedes the
     due-check/exec decision within the same loop iteration; the
     alive-marker touch is part of the script's re-executed startup code).
     Recorded per instruction; not fixed because nothing needs fixing.

## Next steps

None from this session for the combine-and-verify task itself — PR #3133 is
the combined deliverable per the acceptance run quoted in full in the "Why"
section above (`acceptance: python3 -m pytest tests/ -q` and the four probe
`acceptance:` entries there, all this turn). Follow-ups belong to the
orchestrator: (a) close PR #3132 with a note pointing at #3133 once this
lands, (b) a separate "rebase PR #3133 onto origin/main" session for Open
finding #1 above (pre-existing on both original PRs, not new).
