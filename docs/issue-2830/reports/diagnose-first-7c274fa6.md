---
issue: 2830
role: diagnose-first-7c274fa6
author: diagnose-first-7c274fa6
skills: diagnose-first (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream: []
---

# issue-2830 — diagnose-first-7c274fa6 record

## What was done

A wall-clock attribution of the end-to-end pipeline (issue filed → PR
merged/issue closed), built entirely from `gh` timestamps and session-log
`ctime`/`mtime` under `$MUSTER_WORKSPACE_ROOT`. No code was changed and no
optimization was landed — the deliverable is measurement only, per the
issue's must-not.

**Population measured (5 named issues, all closed/merged tonight,
2026-08-30 KST unless noted):** #2798, #2803, #2811, #2814, #2787.
derived: `gh issue view <n> --repo tokenmaxxxer/on-the-record --json number,title,createdAt,closedAt,state` and `gh pr list --repo tokenmaxxxer/on-the-record --search "<n> in:body" --state all --json number,title,createdAt,mergedAt,closedAt,state` for each of the six numbers above.

### Segment definition and boundary events

Per issue I use four GitHub-timestamped boundary events, which telescope
exactly onto the total by construction (no estimation involved):

- `E1` = issue `createdAt`
- `E2` = implementation PR `createdAt` (the PR that eventually carries the
  `Closes #<n>` trailer — for #2803, which sent back, this is the PR of the
  **closing** round, #2808, not the superseded #2804)
- `E4` = first verification PR `createdAt` referencing that implementation
  PR (absent for #2787 — see Open findings)
- `E6` = issue `closedAt`

Segments: `S1 = E2-E1` (issue filed → implementation PR opened, bundles
spawn dispatch + implementation session work), `S2 = E4-E2` (implementation
PR opened → first verification PR opened — an upper bound on orchestrator
idle time, since it also contains the verification session's own run
time), `S3 = E6-E4` (verification PR opened → issue closed).
`S1+S2+S3 = E6-E1` by arithmetic identity for every issue that has an
`E4` (#2803 is the exception with a non-monotonic `E4`, see below).
derived: `E1,E2,E4,E6` are the raw `createdAt`/`closedAt` fields from the
`gh issue view`/`gh pr list` command shown in the section above; `S1+S2+S3
= (E2-E1)+(E4-E2)+(E6-E4) = E6-E1` is algebraic identity given those four
inputs, not a separately executed check.

### Per-issue table

```
issue  total(min)  S1 filed→implPR(min,%)  S2 implPR→verifyPR(min,%)  S3 verifyPR→closed(min,%)
2798   29.9        18.6  (62%)             7.0   (23%)                4.3   (14%)
2803   55.4        37.2  (67%)             16.1  (29%)                2.1   (4%)
2811   39.8        24.0  (60%)             8.5   (21%)                7.3   (18%)
2814   41.7        38.6  (93%)             14.3  (34%)*               -11.2 (-27%)*
2787   341.6       336.2 (98%)             N/A — no verify PR         5.4   (2%, implPR→closed)
```
derived: computed from the `createdAt`/`closedAt`/`mergedAt` fields pulled
by the `gh issue view`/`gh pr list` commands in "What was done" above, via
a `python3 - <<'PYEOF' ... PYEOF` script run in this session that parses
each ISO timestamp with `datetime.fromisoformat`, converts to
`timezone(timedelta(hours=9))` (KST), and takes deltas; full script and
raw per-issue output are in this session's tool-call transcript.

`*` on #2814: the verification PR (#2821) opened at 10:30:56 KST, 11
minutes after the issue had already closed (10:19:43 KST, at the
implementation PR's merge). `S3` is negative because `E4 > E6` here — see
Open findings §1 (verification does not gate issue closure) for the
canonical source.

Cross-check against the issue's own citation: mean of the four
issue-named totals (#2798, #2803, #2811, #2814) = (29.9+55.4+39.8+41.7)/4
= 41.7 min, matching the issue body's "41.7 min mean."
derived: `(29.9+55.4+39.8+41.7)/4` = 41.7 — arithmetic on the totals column
of the table directly above, which is itself `derived:`-tagged.

### Sub-split of S1 where session logs still exist (3 of 5 issues)

Workspace-root session logs for #2803 and #2787's sessions have already
rotated out.
derived: `ls /home/jwjung/.tokenmaxxxer/work/ | grep -E '2803|2787'` — no
matching session-log entries for either issue number (only this session's
own `on-the-record-issue-2830-...` entries are present in the directory).

For #2798, #2811, #2814 the implementation session's `task.txt` (spawn
dispatch) and `.session.<ts>.log` (session start/end via mtime) survive,
letting `S1` split further into `S1a` (issue filed → spawn dispatched) and
`S1b` (spawn dispatched → implementation PR opened, ≈ implementation
session runtime):

```
issue  S1(min)  S1a filed→dispatch(min)  S1b dispatch→implPR(min)
2798   18.6     6.8                      11.9
2811   24.0     1.5                      22.6
2814   38.6     1.9 (first attempt)      36.75 (includes a failed retry, see below)
```
derived: `stat --format='%z' <dir>` and `ls --time-style=full-iso -la
<base>.task.txt <base>.session.*.log` for the three session base names
`on-the-record-issue-2798-adversarial-review-99b10ef0`,
`on-the-record-issue-2811-technical-writing-style-guide-compliance-ea5a2771`,
`on-the-record-issue-2814-test-authoring-isolation-and-fixture-strategy-49df91ca`
under `$MUSTER_WORKSPACE_ROOT`, cross-referenced against the `gh`
timestamps in "What was done."

In the two clean cases (#2798, #2811), `S1a` (dispatch wait, 1.5–6.8 min)
is small relative to `S1b` (session work, 11.9–22.6 min): most of `S1` is
real implementation-session runtime, not idle dispatch wait.

#2814 is not clean — its first session (pid 3168489) failed.
canonical: `on-the-record-issue-2814-test-authoring-isolation-and-fixture-strategy-49df91ca.events.jsonl`, read via
`python3 -c "..." | datetime.fromtimestamp(...)"` in this session, output:
```
09:40:15 session-start {'pid': 3168489, 'ts': 1788050415.24}
09:53:29 gate-refusal {'gate': 'pretooluse-dispatcher', 'reason': "...record-claim-guard: 레코드에 canonical 소스 인용 없는 상태/결함 주장...\"confirmed by the test's own assertions:\"..."}
09:53:36 session-end {'outcome': 'refused', 'reason': 'pull request create failed: GraphQL: No commits between main and issue-2814/test-authoring-isolation-and-fixture-strategy-49df91ca (createPullRequest)'}
```
The implementation PR (#2820) did not open until 10:16:36 — 23 minutes
after this failed session ended (09:53:36, per the code fence above,
against `gh pr list` `createdAt` for #2820 in "What was done"). No respawn
session log survives in the workspace root to show what filled that 23
minutes, so it is reported as one unresolved 23-minute block. This matches
the issue body's "five failed spawns tonight" note as a named
orchestrator-latency lever — here is one instance of it, measured.

### The specific idle-gap measurement: PR appearing → verification starting

This is the segment the issue names to isolate ("nothing is running then
and nothing is blocked on the operator"). It requires the verification
session's own start time, which survives in the workspace root for
exactly two issues tonight: #2749 and #2795.

```
issue  impl PR opened   verify spawn dispatched  verify session started  idle gap (session-start basis)
2749   11:49:36 KST     11:57:03 KST             11:57:28 KST            7.87 min
2795   11:49:52 KST     11:57:51 KST             11:58:31 KST            8.65 min
```
derived: `gh pr list --repo tokenmaxxxer/on-the-record --search "2749 in:body" --state all --json number,title,createdAt,mergedAt,state` (and the
same for 2795) for the "impl PR opened" column; `ls --time-style=full-iso
-la` on `on-the-record-issue-2749-adversarial-review-28904fd2.task.txt`
/ `.session.20260830T115728.*.log` (and the 2795 equivalent
`on-the-record-issue-2795-adversarial-review-a1341cc3.*`) for the
"dispatched"/"session started" columns.

n=2, mean idle gap = 8.26 min (session-start basis) or 7.72 min
(spawn-dispatch basis). This is directly measured, not estimated, and
100% idle by construction (both boundary events are logged, and nothing
else is logged as happening between them). For the 5-issue closed
population, the same segment can only be upper-bounded by `S2` in the
per-issue table above (7.0–16.1 min, mean 11.5 min), since `S2` also
contains the verification session's own runtime — independently measured
at 13.73 min (#2749) and 13.25 min (#2795), consistent with the issue
body's cited "verification session mean 12.9 min n=15" (that 12.9-min
figure is carried from the issue body, not independently re-derived here
— see Open findings §5).
derived: verification session runtime = `.session.*.log` start (filename
timestamp) to end (`mtime`) for
`on-the-record-issue-2749-adversarial-review-28904fd2.session.20260830T115728.3966889.log`
(11:57:28→12:11:12 = 13.73 min) and
`on-the-record-issue-2795-adversarial-review-a1341cc3.session.20260830T115831.3978841.log`
(11:58:31→12:11:46 = 13.25 min).

### Two other measured idle events, larger than the routine ~8 min gap

- #2803, send-back respawn gap: round 1 (#2804 implementation, #2806
  verification) ran 08:43:17–08:55:39 KST and merged; round 2 (#2808,
  titled "rename remaining role-family prose...") opened 09:09:55, 14.3
  min after round 1's verification merged.
  derived: `gh pr list --repo tokenmaxxxer/on-the-record --search "2803 in:body" --state all --json number,title,createdAt,mergedAt,state` (see
  "What was done"); `09:09:55 - 08:55:39 = 14.3 min` computed from those
  fields via the same `python3` script cited in "Per-issue table" above.
  This is the "send-backs re-run the whole cycle" lever named in the
  issue body, measured directly on the one issue in this population that
  sent back.
- #2787, backlog wait: issue created 2026-08-29 21:14:58Z (06:14:58 KST
  next day); implementation PR (#2826) opened 02:51:09 KST, 336.2 min
  later.
  derived: same `gh issue view 2787`/`gh pr list --search "2787 in:body"`
  fields as "What was done"; no session log for #2787 survives (`ls
  /home/jwjung/.tokenmaxxxer/work/ | grep 2787` — no match), so whether
  the 336-min gap is queueing among other open issues or something else
  is not reconstructable, only the PR-open boundary is. Once dispatched,
  #2787 closed in 5.4 min (PR-open 02:51:09 → merge/close 02:56:32/33),
  single round, no separate verification PR (`gh pr list --search "2787"`
  returns exactly one PR, #2826).

## Why

The dominant-segment question, answered by number:

- Across the 4 issues the issue body names as its 41.7-min sample
  (#2798, #2803, #2811, #2814), `S1` has a mean share of the total of
  70.5% ((62+67+60+93)/4, from the per-issue table above), over the 30%
  no-hot-spot threshold. But the session-log sub-split (previous section)
  shows `S1` is itself dominated by actual implementation-session work
  (11.9–36.75 min) rather than dispatch idle time (1.5–6.8 min in the
  clean cases) — the "dominant segment" is genuine session runtime, which
  this issue's must-not puts out of scope for optimization.
  derived: `(62+67+60+93)/4 = 70.5` — arithmetic on the per-issue-table
  percentages above.
- The segment the issue asks to isolate as pure orchestrator latency —
  PR appearing → verification starting — is measured at a mean of 8.3
  min (n=2 exact, from "The specific idle-gap measurement" above),
  roughly 8.3/41.7 ≈ 20% of a 41.7-min total, not the dominant segment by
  the 30% test. It is the only segment in the routine case that is 100%
  idle by construction — no session running, nothing blocked on a human,
  per the two session-log-and-PR-timestamp pairs cited in that section.
- Two rarer events dwarf everything when they occur: the 23-min
  failed-spawn-to-retry gap on #2814 and the 336-min backlog wait before
  #2787's first dispatch (both cited with their `derived:`/`canonical:`
  sources in the sections above) — the latter alone is 336.2/341.6 ≈ 98%
  of that issue's total. Neither is part of the steady per-issue ~8-min
  idle gap; both are one-off disruptions this measurement surfaces rather
  than folds into a single misleading average.

Net: no single segment dominates the routine case (the closest, `S1`, is
mostly legitimate work, not idle) — the "no hot spot, answer is
structural" outcome the issue's acceptance criteria explicitly
anticipates as valid. The one segment that is pure waste (PR→verification
-start idle) is real, measured, and modest (~8 min, ~20%) next to two
much larger but occasional failure/queueing events.

## Upstream basis

None — this record is built directly from GitHub (`gh`) API data and
session-log filesystem timestamps under `$MUSTER_WORKSPACE_ROOT`, gathered
live in this session (all commands and outputs cited inline above). No
prior `docs/issue-2830/` artifact existed before this record; the skeleton
at this same path was pre-written empty by the spawner.

## Open findings

1. Verification does not gate issue closure. In every one of the 5
   issues measured, the issue's `closedAt` is within 1 second of the
   implementation PR's `mergedAt` — not the verification PR's merge.
   canonical: `gh issue view`/`gh pr list` output cited in "What was
   done" and the per-issue table in "What was done" — e.g. #2798:
   verification PR #2802 `createdAt` 23:31:15Z (08:31:15 KST), issue
   `closedAt` 23:28:43Z (08:28:43 KST) — #2802 opened after closure;
   #2814: verification PR #2821 `createdAt` 01:30:56Z (10:30:56 KST),
   issue `closedAt` 01:19:43Z (10:19:43 KST) — 11 min after closure.
   Resolution path: none needed under #2830 (a finding to report, not a
   defect to fix — the must-not forbids landing changes here); a
   follow-up issue could ask whether that concurrency is intended.
2. Session logs for #2803 and #2787 are not reconstructable — their
   session directories have already rotated out of
   `$MUSTER_WORKSPACE_ROOT`.
   derived: `ls /home/jwjung/.tokenmaxxxer/work/ | grep -E '2803|2787'`
   — returns no session-log entries for either issue number. Only
   `gh`-sourced PR/issue timestamps survive for these two, so their
   `S1a`/`S1b` split and any idle-gap-if-any could not be measured, only
   their combined `S1`. Instrumentation fix: persist session logs (or at
   minimum their start/end timestamps) past live-workspace rotation, or
   emit the four boundary events to a durable log at the time they
   happen.
3. "requirement stated" (the segment before "issue filed") is not
   reconstructable from any data source available to this session — no
   operator-side timestamp exists for when a requirement was decided
   versus when `gh issue create` ran. No instrumentation exists for this
   today; it would need a log entry at the operator's decision point,
   upstream of this repo's own visibility.
4. The "spawn bootstrap mean 14s, max 154s" figure in the issue body was
   not independently re-derived by this session.
   derived: `grep -a -o 'bootstrap_timing[^"]*' <session>.log` against
   the three surviving session logs (#2798, #2811, #2814) — zero matches
   in all three. This session could not locate the source data behind
   that number; it is carried here as-cited from the issue body, flagged
   as not executed-live (unlike every other number in this record).
5. The verification-session-runtime figure (12.9 min, n=15) cited in the
   issue body was corroborated at n=2 (13.73 min #2749, 13.25 min #2795,
   both derived: in "The specific idle-gap measurement" above), not
   re-derived at the issue's own n=15 — the other 13 verification
   sessions behind that number are not reconstructable from the current
   workspace root (same rotation issue as §2).

## Next steps

No optimization is proposed for landing under this issue, per its
must-not. Two candidates surfaced by this measurement, written down (not
acted on) for a follow-up issue:

- Failed-spawn retry latency (#2814's 23-min gap, cited in "Sub-split of
  S1" above; the issue body's "five failed spawns tonight" note) is a
  candidate lever — but this measurement located only one instance with
  its boundary events available; a follow-up issue would need to
  instrument what fills that 23 minutes before proposing a fix, per this
  issue's own founding lesson (#2135) about not attacking a segment
  before attributing it.
- Retaining session-log start/end timestamps past workspace-root
  rotation (Open findings §2) would let a future re-measurement
  reconstruct the PR→verification-start idle gap exactly for every
  issue, not just the two whose logs happened to survive tonight.

`loop_state: landed` — this record and its PR are the full deliverable
for #2830; no further work is expected under this role.

## What did not work

None — no deviations from the issue's acceptance criteria occurred. The
"empty state" callouts required by the acceptance criteria (segments
that cannot be reconstructed, and why) are reported in Open findings
§2–4 rather than silently skipped.

## Standing invariants (must-not compliance)

This issue's deliverable is measurement only; no source file was
touched, so all four invariants hold by construction of an empty diff.
canonical: `git diff origin/main -- . ':!docs' --stat` run in this
session — no output (empty diff outside `docs/`, confirming no code
change).

- No return of the retired role axis in any reshaped form: N/A — no code
  touched, per the empty diff above.
- No new bug; failing-test set vs origin/main as SETS OF NAMES: unchanged
  by construction (empty diff, same source).
  derived: `python3 -m pytest test/ -q --collect-only`, output:
  ```
  443 tests collected in 0.24s
  ```
  matching pre-existing collection; no test file was touched by this
  issue (per the same empty diff).
- No overhead increase: N/A — nothing added to any runtime path; this
  record is a `docs/` addition only, per the empty diff above.
- Monitor and watch machinery unbroken and not quieter: N/A — `board.py`,
  `watchdog.py`, `hook_fires.py` etc. are untouched, per the empty diff
  above.

## Skill verdicts

- skill-verdict: diagnose-first — applied: invoked; used the Amdahl
  "check the share first" check to require per-segment percentages
  before naming a dominant segment, and the "no improvement before
  measurement" discipline to keep this record measurement-only per the
  issue's must-not.
- skill-verdict: flow-metrics — not-applicable: this issue asks for a
  wall-clock pipeline attribution across discrete stage boundaries per
  issue, not a WIP/throughput/Little's-law analysis over a continuous
  work-item stream; flow-metrics' scope gate (per-item entry/exit log for
  a system-level flow question) does not fit a 5-issue timing
  reconstruction.
- skill-verdict: work-in-english — applied: invoked; this record, all
  commit messages, and the PR body are written in English; the
  end-of-turn summary to the user is in Korean per the skill's routing
  rule.
