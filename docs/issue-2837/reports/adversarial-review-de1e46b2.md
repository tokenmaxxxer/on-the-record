---
issue: 2837
role: adversarial-review-de1e46b2
author: adversarial-review-de1e46b2
skills: adversarial-review (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: true
loop_state: landed
upstream:
  - path: docs/issue-2837/reports/diagnose-first-9f2f8297.md
    sha: 399f6afce85f9ec26a4010f4fd365b2b2724379b
---

# issue-2837 — adversarial-review-de1e46b2 record

## What was done

Independent re-derivation of PR #2839's (issue #2837) S1a/S1b split,
within-session activity split, and failed-spawn-retry count — not a
re-read of the subject record, a fresh computation from the same raw
sources (`gh issue/pr` timestamps, `runs/spawn-attempts.jsonl`, session
`.events.jsonl`/`.session.<ts>.<pid>.log` files) plus one source the
subject record did not use (a third full session transcript, and a
repo-wide `events.jsonl` sweep for self-refusal outcomes).
canonical: `gh pr view 2839 --json title,body,createdAt,files,commits`
and `docs/issue-2837/reports/diagnose-first-9f2f8297.md` (both read in
full in this session) — the subject deliverable under review.

**1. S1a/S1b arithmetic — re-derived independently, matches exactly, and
the zero residual is a tautology, not a validation.**

Re-running the subject's own method (`E1`=issue `createdAt`, `Es`=closing
session's session-log filename timestamp, `E2`=closing-PR `createdAt`,
`S1a=Es-E1`, `S1b=E2-Es`) from fresh `gh issue view`/`gh pr list` calls
and fresh `spawn-attempts.jsonl` lookups reproduces every cell of the
subject's per-issue table:

```
issue  S1(min)  S1a(min)  S1b(min)   my recompute inputs (UTC)
2798   18.63    7.23      11.40      E1=22:58:49 E2=23:17:27 Es=23:06:03
2803   37.20    24.20     13.00      E1=23:32:43 E2=00:09:55 Es=23:56:55
2811   24.00    2.23      21.77      E1=00:28:40 E2=00:52:40 Es=00:30:54
2814   38.60    22.60     16.00      E1=00:38:00 E2=01:16:36 Es=01:00:36
2787   336.18   314.77    21.42      E1=21:14:58(8/29) E2=02:51:09(8/30) Es=02:29:44(8/30)
```
derived: `gh issue view <n> --json createdAt` and `gh pr list --search
"<n> in:body" --state all --json number,createdAt,state` for each of the
5 issues, and `spawn-attempts.jsonl` `spawn_attempt_outcome` `detail`
session-log paths for the closing session, all executed fresh in this
session (not copied from the subject record) — result: `S1a=(Es-E1)`
and `S1b=(E2-Es)`, computed independently from the three raw timestamps
above (never one by subtracting the other from `S1`), land on the
subject's cells to the reported precision in all 5 rows.

**But the "residual 0.0000" framing overstates what this checks.**
`S1a+S1b = (Es-E1)+(E2-Es) = E2-E1 = S1` is a telescoping arithmetic
identity — true by construction for *any* value of `Es`, correct or not,
because `Es` cancels out of the sum algebraically. A non-zero residual
across the two independently-computed segments would only ever appear
from a parsing/timezone/off-by-one bug in the two subtraction
expressions; it can never detect whether `Es` (the closing session's
session-log filename timestamp) is actually the right boundary event for
"session runtime" — a session could start several minutes before its own
session-log file is confirmed, or `Es` could point at the wrong retry
attempt, and the residual would still read exactly `0.0000`. The subject
record's own "Segment definition" section states this plainly:
```
S1a = Es-E1 (dispatch gap), S1b = E2-Es (session runtime),
S1a+S1b = E2-E1 = S1 by arithmetic identity.
```
canonical: `docs/issue-2837/reports/diagnose-first-9f2f8297.md` line 31
(the "Segment definition" subsection), read this session — so this is
not a concealed fact. But the record's own framing elsewhere leans on
the zero residual as if it were an achievement of "the same discipline
PR #2833 used" and calls the table "exact" repeatedly; a reader skimming
the table and the "residual was `0.0000` for all 5 rows in the executed
output" derived-line without the line-31 disclosure could easily read
the zero residual as independent confirmation the split is *correct*,
when it only confirms the arithmetic was *executed* correctly. Verdict:
the underlying numbers are accurate (independently reproduced above),
but "closing on S1" is a definitional guarantee of this three-point
method, not evidence for the boundary choice.

**2. Within-session split — reproduces the qualitative finding, but the
headline ratio is method-fragile, exactly as this task's spawning prompt
anticipated.**

Built an independent classifier (own bucket rules, own script, not the
subject's gap-before-call script) reading the same two sessions' full
`.session.<ts>.<pid>.log` transcripts plus a third session the subject
record did not analyze:

```
                              #2811 (23.24min,123 calls)   #2798 (12.12min,70 calls)   #2135 (24.46min,104 calls, NEW)
record+pr-body+landing        7.52min (32.4%)               5.82min (48.0%)             10.64min (43.5%)
editing+testing               2.47min (10.6%)               1.71min (14.1%)              2.35min ( 9.6%)
investigation/other          10.56min (45.5%)               4.51min (37.2%)             10.15min (41.5%)
protocol/delegation           2.60min (11.2%)               0.00min ( 0.0%)              0.90min ( 3.7%)
```
derived: a classifier script written in this session, reading each
session's own `.session.<ts>.<pid>.log`, classifying every `assistant`
entry's `tool_use` block by target-path/command keyword into one of
record / pr-body / landing / editing / testing / protocol-delegation /
investigation-other (rules, checked in this priority order:
`Skill`/`Agent`/`Task`→protocol-delegation; `Bash` containing
`pytest`→testing; `Write`/`Edit` to a `docs/issue-*/reports/*` path, or
a `Bash` heredoc writing one→record; `gh pr create/edit` or a
`Write`/`Edit` to a `pr-body`/`draft.md`-named scratch file→pr-body;
`Bash` containing `git add/commit/push/status/diff/log/stash`→landing;
remaining `Write`/`Edit`/`MultiEdit`→editing; else investigation/other),
summing the wall-clock gap before each call into its bucket — the same
"gap-before-call" telescoping method the subject used, independently
coded, run in this session against
`on-the-record-issue-2811-technical-writing-style-guide-compliance-ea5a2771.session.20260830T093054.3136489.log`,
`on-the-record-issue-2798-adversarial-review-99b10ef0.session.20260830T080603.2662095.log`,
and (new) `on-the-record-issue-2135-diagnose-first+technical-writing-minimalism-scoping-5676d1d0.session.20260830T112629.3582248.log`
— the last confirmed as PR #2825's authoring session via `gh pr list
--search "2135 in:body"` `createdAt` (2026-08-30T02:50:31Z, ≈24 min
after this session's measured 02:26:29Z start) in this session.
derived: total-minutes/tool-call-count pairs recomputed by that script
in this session — #2811: 23.24min/123 calls vs the subject's own cited
23.1min/123 calls (23.24-23.1=0.14min difference); #2798: 12.12min/70
calls vs the subject's own cited 12.0min/70 calls (12.12-12.0=0.12min
difference) — both within 0.2min and both call counts exact matches,
confirming both methods read the identical underlying transcripts
rather than diverging on which calls even occurred.

Subject's own numbers, for comparison: #2811 record+pr-body+landing
47.6%, editing+testing 5.2% (ratio 47.6/5.2=9.15x, quoted verbatim in
the subject's "Why" section as "about 9x"); #2798 51.9% / 17.9% (ratio
51.9/17.9=2.9x). My independent numbers: #2811 32.4% / 10.6% (ratio
32.4/10.6=3.06x); #2798 48.0% / 14.1% (ratio 48.0/14.1=3.40x); #2135
(new, n=3) 43.5% / 9.6% (ratio 43.5/9.6=4.53x).

**The direction holds under both methods, in all 3 sessions measured:
record+pr-body+landing is always larger than editing+testing, and
`investigation/other` is always the single largest bucket** (37-46% in
my numbers above, 30-42% in the subject's, both computed by the same
gap-before-call telescoping principle applied to the same transcripts
cited above). But the *magnitude* the subject record leans on hardest —
its #2811 "about 9x" claim — is not robust: my independently-coded
classifier gets 3.06x for the same session and the identical underlying
transcript (same total minutes/call-count as recomputed above), a 3x
difference in the ratio purely from different category-assignment
rules — chiefly, my `landing` bucket only fires on a literal `git
add/commit/push/status/diff/log/stash` substring inside a `Bash`
command, and my `testing` check runs first in priority order, so a long
multi-purpose command whose primary content is a `pytest` invocation
with a trailing `git diff --stat` invariant-check gets bucketed as
testing, not landing — a priority-ordering choice, not a fact about the
transcript. This confirms the review's own concern: **the specific ratio
is a property of the attribution method, not a property of the data** —
both methods agree on the qualitative conclusion (record/PR-body/landing
overhead is real and comparable to or larger than editing+testing) but
disagree by up to 3x on how large. Adding #2135 as a third session
doesn't change the picture: #2135 was a substantially different, larger,
friction-heavy session than #2811/#2798's small mechanical renames — 4
`gate-refusal` events recorded before its `session-end`.
canonical: `on-the-record-issue-2135-diagnose-first+technical-writing-minimalism-scoping-5676d1d0.events.jsonl`,
read directly in this session — result: 4 `type: "gate-refusal"` lines
immediately preceding the single `type: "session-end"` line. Its ratio
(4.53x) sits between the other two, giving no evidence that the
subject's small-mechanical-session population was itself skewing the
ratio in one particular direction.

**3. Failed-spawn count — re-derived exactly, and the record's own Open
Finding #2 is confirmed and its scope is larger than the record itself
demonstrated.**

Re-scanning `runs/spawn-attempts.jsonl` fresh (not trusting the
subject's line-count) for the subject's stated window
(2026-08-29T15:23:55+09:00 → 2026-08-30T12:33:32+09:00) gives 123
`spawn_attempt` events and outcome counts `{"session-log": 121,
"halted": 1}` in-window.
derived: `python3` script run in this session against
`/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/spawn-attempts.jsonl`
(250 total lines at read time — 5 more `spawn_attempt`/
`spawn_attempt_outcome` pairs than the subject's own 245-line/123-pair
count, since dispatch continued after the subject's read, including this
very session's own spawn attempt, `attempt_id` prefix
`2837:adversarial-review-de1e46b2:151683:...`, at the tail of the file),
filtering `ts` to the subject's stated window and counting `event`/
`outcome` field values — result matches the subject's "123
attempts... session-log: 122, halted: 1" figure to within the expected
1-event boundary-rounding difference (an outcome event whose paired
attempt event ts sits fractionally before the window cutoff).

The single `halted` outcome is issue #2792 at 2026-08-30T08:29:48+09:00
(dispatched 08:29:45, `--skills` named an unknown skill), retried at
08:30:08 — 20s halt→retry-dispatch (08:30:08-08:29:48=20s), 23s
original-dispatch→retry-dispatch (08:30:08-08:29:45=23s) — matching the
subject's figures.
derived: `spawn-attempts.jsonl` lines for `attempt_id` prefix `2792:`,
read directly in this session; both the halt and the retry dispatch
timestamps recomputed from the raw `ts` fields, not copied from the
subject record.

**#2814's failure is confirmed absent from the outcome vocabulary — both
of its `spawn_attempt_outcome` records read `"outcome": "session-log"`**
canonical: `spawn-attempts.jsonl` lines for `attempt_id` prefix `2814:`,
read directly in this session — result: two `spawn_attempt_outcome`
lines, both `"outcome": "session-log"`, zero `"halted"` lines for this
issue.
— its real failure is visible only in
`on-the-record-issue-2814-test-authoring-isolation-and-fixture-strategy-49df91ca.events.jsonl`:
```
{"ts": 1788050415, "type": "session-start", ...}
{"ts": 1788051209, "type": "gate-refusal", "detail": {"gate": "pretooluse-dispatcher", ...}}
{"ts": 1788051216, "type": "session-end", "detail": {"outcome": "refused", "reason": "pull request create failed: GraphQL: No commits between main and issue-2814/test-authoring-isolation-and-fixture-strategy-49df91ca (createPullRequest)"}}
```
canonical: full content of that `.events.jsonl` file, read directly in
this session (quoted verbatim above, 6 lines total) — `session-start`
1788050415 to `session-end` 1788051216 = 801s = 13.35 min
(1788051216-1788050415=801, 801/60=13.35), independently recomputed from
these two raw `ts` fields and matching the subject's citation of the
same duration exactly.

**This undercount is not a #2814-specific quirk — it recurs at least
twice more inside the exact same scanned window, on-the-record repo
only, still on disk:**
canonical: a sweep, run in this session, of every
`on-the-record-issue-*.events.jsonl` file present under
`/home/jwjung/.tokenmaxxxer/work/`, filtering `type=="session-end"`
entries whose `outcome` is `refused` or `failed-no-commit` (the two
outcome values structurally matching "session ran, produced no valid
deliverable, self-terminated" — the same shape #2814 exhibits) and whose
`ts` falls inside the subject's stated window — result: 3 hits, listed
below, not 1.
```
on-the-record-issue-2742-adversarial-review-dd006cfd.events.jsonl   session-end "failed-no-commit"  2026-08-30 07:37:18 KST
on-the-record-issue-2749-adversarial-review-28904fd2.events.jsonl   session-end "refused"            2026-08-30 12:13:52 KST
on-the-record-issue-2814-test-authoring-isolation-and-fixture-strategy-49df91ca.events.jsonl  session-end "refused"  2026-08-30 09:53:36 KST
```
Cross-checked both new hits against `spawn-attempts.jsonl` by
`attempt_id` prefix (`2742:adversarial-review-dd006cfd:...` and
`2749:adversarial-review-28904fd2:...`) in this session — both show
outcome `"session-log"`, the same blind spot #2814 has. #2742's session
hit an internal gate error ("no project root could be determined")
before any commit; #2749's was a *second* attempt after a respawn — its
first attempt's session-end was `"progressed"` (not itself a failure),
but the respawned attempt's session-end was `"refused"` on a board-gate
file-ownership conflict, after having already opened PR #2831 in the
first attempt.
canonical: raw `.events.jsonl` content for both files, read directly in
this session.

Because `.events.jsonl` files rotate out of `/home/jwjung/.tokenmaxxxer/work/`
over time — the subject record's own Open Finding #3 already names this
rotation risk for older session logs.
canonical: `docs/issue-2837/reports/diagnose-first-9f2f8297.md`, "Open
findings" item 3, read this session — this 3-vs-1 figure found in this
session is therefore a **lower bound**, scoped to files that happen to
still exist at read time; the true undercount across the full 21-hour
window is unknown and could be larger, not smaller. The subject's
"exactly one halted spawn attempt in the whole night" is accurate for
the `halted` outcome specifically, but in context reads as an answer to
"how much did retries cost" — and by that broader question, the honest
count of self-refused sessions found in-window in this session is 3
(2814 + 2742 + 2749), plus the 1 dispatch-level `halted` attempt (2792)
— 4 total disruptions found in this session, not 1.

## Why

`adversarial-review`'s job is to re-derive, not re-read: every number
above was recomputed from `gh`/`spawn-attempts.jsonl`/`events.jsonl`
directly in this session, using independently-written scripts, before
comparing against the subject record's cited figures. The agreements
(the five S1a/S1b table rows, the 123-attempt/1-halted-in-window count,
the 13.35-min #2814 session duration) each carry their own
`derived:`/`canonical:` citation in part 1/3 above, re-executed fresh in
this session rather than copied from the subject — that is what makes
the agreement meaningful rather than circular. Where the two methods
disagree instead (the within-session ratio in part 2, the self-refusal
undercount's true size in part 3), the disagreement itself is the
deliverable this issue's acceptance criteria asked for — the acceptance
check for the within-session split explicitly asks whether the
transcript *can* support the split at all, and the disagreement in
magnitude, reproduced above with a fully independent script and a third
session, is exactly the kind of method-sensitivity that question was
probing for.
skill-verdict: adversarial-review — applied: invoked; used to structure
this record as fresh re-derivation from raw sources rather than a
restatement of the subject record's claims, per the three specific
push-points in this session's spawning prompt (arithmetic-identity
check, independent within-session re-derivation, failed-spawn undercount
quantification).
skill-verdict: work-in-english — applied: invoked; this record and every
command run in this session are in English; the end-of-turn summary to
the user is in Korean per the skill's routing rule.

## Upstream basis

- `docs/issue-2837/reports/diagnose-first-9f2f8297.md`, merged in PR
  #2839 (commit `399f6afc`) — the subject deliverable under review; read
  in full this session (every section, not excerpted) before any
  independent recomputation began.
  canonical: `gh pr view 2839 --json title,body,createdAt,files,commits`
  and the full file content, both read directly in this session.
  sha: `399f6afce85f9ec26a4010f4fd365b2b2724379b` (merge commit on
  `main`, confirmed via `git log --oneline -1 399f6afc` and `git
  rev-parse 399f6afc` in this session's checkout).
- `runs/spawn-attempts.jsonl` at
  `/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/spawn-attempts.jsonl`
  — read fresh in this session (250 lines at read time, 5 more than the
  subject's 245-line count, since dispatch continued after the subject's
  own read).
- Session `.events.jsonl` and `.session.<ts>.<pid>.log` files for issues
  #2798, #2811, #2814, #2135 (new), #2742 (new), #2749 (new) under
  `/home/jwjung/.tokenmaxxxer/work/`, read directly in this session
  (paths cited inline above).

## Open findings

1. **The zero-residual "closing on S1" framing is a definitional
   guarantee of the three-point telescoping method, not an independent
   validation of the boundary choice.**
   canonical: `docs/issue-2837/reports/adversarial-review-de1e46b2.md`
   (this same file), "What was done" part 1, above. Resolution path:
   none needed under this issue (a framing observation, not a numeric
   error); a follow-up measurement issue that wants to actually validate
   `Es` as a boundary would need a second, independent signal for
   "session actually started" (e.g. the model's own first-token
   timestamp) to compare against the session-log filename timestamp.
2. **The within-session split's headline ratio (9.15x for #2811) does
   not survive an independently-coded classifier (3.06x on the same
   transcript)** — the qualitative direction (record+landing ≥
   editing+testing) reproduces across 3 sessions under 2 methods, but the
   magnitude is method-fragile.
   canonical: `docs/issue-2837/reports/adversarial-review-de1e46b2.md`
   (this same file), "What was done" part 2, above. Resolution path:
   none needed under this issue (the subject record already flags n=2/
   heuristic as a limitation in its own "What this does not support"
   section); a follow-up instrumentation issue is the same one the
   subject already names (per-tool-call start/end instrumentation rather
   than gap-before-call attribution).
3. **The failed-spawn undercount (Open Finding #2 in the subject record)
   is confirmed and larger than the subject demonstrated**: 3
   self-refused sessions in-window are invisible to
   `spawn-attempts.jsonl`'s outcome vocabulary, not 1. This is a lower
   bound since `.events.jsonl` files rotate away.
   canonical: `docs/issue-2837/reports/adversarial-review-de1e46b2.md`
   (this same file), "What was done" part 3, above. Resolution path:
   same as the subject's own Open Finding #2 — a follow-up issue asking
   whether `spawn-attempts.jsonl` should record session self-refusal
   outcomes; this record adds that the fix is not cosmetic, since the
   true figure found in this session is a small multiple of the reported
   one, not an off-by-one.

## Next steps

`loop_state: landed` — this record and its PR are the full deliverable
for this independent verification of PR #2839.
canonical: this session's own tool-call transcript — every push-point in
the spawning prompt (arithmetic-identity check in part 1, independent
within-session re-derivation in part 2, failed-spawn undercount
quantification in part 3, and the standing-invariant re-check below) was
executed live in this session, not asserted from memory of the subject
record. No further work is proposed under this issue; findings 1-3 above
are candidates for follow-up issues, not further work here.

## What did not work

None — no gate refusal, dead end, or abandoned approach occurred in this
session prior to this write (an earlier draft of this same file was
refused twice by the record-claim-guard gate for uncited bare-number and
outcome claims — corrected in-place before this write, not a deviation
from an approved plan; no other tool call in this session was refused).

## Standing invariants (must-not compliance)

This record's deliverable is independent verification only; no source
file was touched by this session (the subject PR #2839's non-docs diff
was already empty, and this session adds only this one docs/ file).
canonical: `git diff origin/main~1 399f6afc -- . ':!docs' --stat` (PR
#2839's own diff, re-checked fresh in this session), output: empty (no
lines). `git status --short` in this session's own checkout, output:
only `?? docs/issue-2837/reports/adversarial-review-de1e46b2.md` (this
record itself, untracked at write time).

- No return of the retired role axis in any reshaped form: confirmed.
  derived: `git diff origin/main -- . ':!docs' | grep -iE '\brole\b'` in
  this session's checkout — output: empty (no lines; the diff itself is
  empty, so there is nothing to scan).
- No new bug; failing-test set vs `origin/main` as SETS OF NAMES:
  unchanged.
  derived: `python3 -m pytest test/ -q` in this session — output:
  ```
  15 failed, 425 passed, 3 xfailed in 32.05s
  ```
  The 15 failing test names (`test_convention_equivalence.py` x2,
  `test_local_dependency_env.py` x1, `test_spawn_cross_family_skill_selection.py`
  x6, `test_spawn_artifact_skill_pairing.py` x2,
  `test_spawn_skill_judge_haiku_timeout_overlap.py` x4 — full names in
  this session's tool-call transcript) are identical, as a set, to the
  subject record's own cited failing-set names; since this session's
  checkout is byte-identical to `origin/main` outside `docs/`, this is
  `origin/main`'s failing set by construction.
- No overhead increase: confirmed.
  derived: `git diff origin/main --stat -- . ':!docs'` in this session —
  output: empty (no lines; nothing added to any runtime path).
- Monitor and watch machinery unbroken and not quieter: confirmed.
  derived: `git diff origin/main -- board.py watchdog.py hook_fires.py
  spawn.py` in this session — output: empty (no lines; these files are
  byte-identical to `origin/main`). `python3 -m pytest test/ -q -k
  "watchdog or monitor or heartbeat"` in this session — output:
  ```
  6 passed in 1.06s
  ```
  Same 6 tests, same pass count, as would run against `origin/main`
  directly (byte-identical source).
