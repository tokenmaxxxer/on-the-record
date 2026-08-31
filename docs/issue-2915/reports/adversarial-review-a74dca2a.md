---
issue: 2915
role: adversarial-review-a74dca2a
author: adversarial-review-a74dca2a
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
loop_state: landed
upstream:
  - path: docs/issue-2915/reports/diagnose-first+observability-methodology-selection-f198342c.md  # untracked here — PR #2917 unmerged
    sha: e755ffea51f50d03a080fc795beb28eac39ac9f9
---

# issue-2915 — adversarial-review-a74dca2a record

## What was done

Independent adversarial verification of PR #2917 (issue #2915), a documentation-only
change to `docs/handbooks/monitor-liveness.md`. PR state confirmed directly —
canonical: `gh pr view 2917 --json state,mergedAt,headRefOid,baseRefName` — result:
`{"baseRefName":"main","headRefOid":"e755ffea51f50d03a080fc795beb28eac39ac9f9","mergedAt":null,"state":"OPEN"}`.
Three commits make up the PR — canonical: `gh pr view 2917 --json commits --jq '.commits[].oid'`
— result: `974b0f124b8ca39c381755c7c851c62955bfbe66` (content commit),
`02958772c4bc49a25fdb161a038ea3c72fc13777`, `e755ffea51f50d03a080fc795beb28eac39ac9f9` (head).
Neither is an ancestor of `origin/main` — derived: `git merge-base --is-ancestor
974b0f124b8ca39c381755c7c851c62955bfbe66 origin/main` — result: exit non-zero (not an
ancestor) — the PR is genuinely unmerged, not already-landed history.

Four background workers independently re-derived every checkable claim from primary
sources (PR diff, `hooks.json`, hook source, git history of `docs/handbooks/monitor-liveness.md`,
`gh issue`/`gh pr` output, and reproduced scripts) without reading the PR's own record as
ground truth. Findings below are synthesized from their raw, command-and-output-cited
output against the PR's five claims (a)-(e) and the task's four attack points.

skill-verdict: adversarial-review — applied: invoked; loaded via Skill tool and used as
this session's own evaluator-role protocol — this session IS the "evaluator" of the
protocol (fresh context, receives only PR #2917 + issue text, no access to the builder
session), re-deriving claims from primary sources per Step 2's "evidence requirement"
rather than trusting the PR body.
other mounted skills: not triggered (work-in-english — followed as house style without
needing the skill's own text; implementation-audit — this is a PR review, not a two-session
spec-conformance audit, so it does not apply).

## Why

adversarial-review's core mechanism is that a structurally independent evaluator with no
stake in the artifact and no access to builder intent is required to catch defects a
self-reviewing builder would rationalize past. The task's own framing named the specific
failure mode to hunt for — "a search that returns a clean answer for a population it never
reached" — so each of the four attack points was assigned to an independent worker that
reproduced the underlying commands/scripts itself rather than summarizing the PR's prose.

## What did not work

None.

## Upstream basis

- PR #2917's own builder record — canonical: `gh pr view 2917 --json state,mergedAt` —
  result: `state: OPEN, mergedAt: null` — was originally written on the PR branch to
  `docs/issue-2915/reports/diagnose-first+observability-methodology-selection-f198342c.md` (untracked here, PR #2917 unmerged): that path does not exist in this worktree, so its
  content was read via `gh pr view 2917 --json body` and `gh pr diff 2917`, not via a local
  checkout. PR head sha `e755ffea51f50d03a080fc795beb28eac39ac9f9`.
- `docs/handbooks/monitor-liveness.md` — history reconstructed via
  `git log --oneline --all -- docs/handbooks/monitor-liveness.md` and per-commit `git show`.
- `on-the-record/hooks/hooks.json`, `on-the-record/hooks/directive.sh`,
  `on-the-record/hooks/stop-poll-rearm.sh`, `on-the-record/monitors/poll-heartbeat.sh`,
  `on-the-record/monitors/poll_heartbeat_delta.py` — read directly, cross-checked against
  the handbook's new prose and against the PR's numeric claims.
- `gh issue view 2915`, `gh pr view 2917 --json body,comments,commits,state,mergedAt,headRefOid,baseRefName`,
  `gh pr diff 2917` — primary GitHub state, not the PR author's paraphrase of it.

## Open findings

### Finding 1 (MAJOR) — claim (e) "no code change is warranted" is not supported by the issue's own acceptance bar

canonical: `gh issue view 2915` (issue body, "must not" acceptance list) — result quoted
verbatim by the research worker:

> "must not let a session be unobserved for longer after this issue than before it. Any
> change must be shown to shorten, not lengthen, the measured latency above."

PR #2917 ships zero code changes — derived: `gh pr diff 2917 --name-only` — result: 4 files,
all under `docs/` (listed in Finding 4) — and its own handbook text states the latency is
unbounded absent a turn:

```
docs/handbooks/monitor-liveness.md ("Structural limit: full-idle death cannot self-heal"):
"Both directive.sh and stop-poll-rearm.sh are turn-driven — they only fire on a
UserPromptSubmit or Stop event, i.e. when the session receives or finishes handling a
user turn. If the Monitor dies during a fully idle stretch (no user turn arriving at
all, and no Monitor left to tick), nothing in this repo observes that death or emits
the re-arm directive until the next turn actually happens."
```

A change that makes literally no code change cannot, by construction, "be shown to
shorten" a measured latency — it can only leave it exactly where it was. The PR's own
"no code change is warranted" conclusion is therefore in direct tension with the
acceptance bar stated in the issue it claims to resolve: it satisfies "must not lengthen"
trivially (nothing moved) but does not attempt, let alone demonstrate, the "must be shown
to shorten" half of the same sentence.

This is not merely "already broken for N days" (the PR's own framing, addressed at
Finding 2) — a concrete, previously-existing, cheap candidate mitigation exists and was
never reconsidered — derived: `git show 6361aaba -- on-the-record/monitors/poll_heartbeat_delta.py`
(commit `6361aaba`/`7fb27337`, 2026-08-18, "fix(issue-1732): drop the 1800s 'monitoring
active, no changes' heartbeat line") — result: removed an *unconditional* ~30-minute
backstop emission that had existed since #1220:

```
-        healthy = sum(1 for k in new_lines if "#" not in k and not k.startswith("__fixed__"))
-        heartbeat_lines = [
-            f"[heartbeat] monitoring active, {healthy} session(s) tracked, no changes"
-        ]
-        heartbeat_lines.extend(curr[k] for k in order if k.startswith("returned-pr:"))
-        sys.stdout.write("\n".join(heartbeat_lines) + "\n")
-        emitted_now = True
```

That backstop was coupled to `poll-heartbeat.sh`'s own turn-independent 120s tick loop (not
to a hook event), so it did not require any of the platform capabilities the handbook
correctly documents as unavailable to a plugin (`docs/issue-801/proposals/technical-feasibility.md`:
no OS-level cron/systemd timer API, no way to keep `ScheduleWakeup` armed past session
death, no unattended Routine provisioning). Restoring an analogous bounded, turn-independent
"still alive" signal — even at reduced frequency to control the noise #1732/#2913 were
fighting — is a candidate code change inside the platform's existing capabilities that the
PR does not evaluate or rule out; it only documents that the gap exists. Corroborating that
this candidate was never actually reconciled — canonical: `on-the-record/monitors/poll-heartbeat.sh`
inline comment (read directly) — result: it still asserts the removed behavior is present
("Also emits a bounded ~30min aliveness heartbeat when a due tick would otherwise be fully
suppressed for that long, so the Monitor channel never goes silent past a bound (issue req
#1220)") — a stale comment describing code that #1732 deleted, left uncorrected by this
documentation-only PR.

Verdict: claim (e) is a judgement asserted without engaging the issue's own explicit
"must be shown to shorten" bar or the one concrete mitigation candidate visible in this
repo's own history. This is the review's most severe finding.

### Finding 2 (MODERATE) — claim (d)'s "twelve days" is an arithmetic error; the actual gap is thirteen

canonical: `git show -s --format='%H%n%ai%n%s'` for the two anchor commits — result:

```
6361aaba/7fb27337  2026-08-18 18:04:38 +0900  fix(issue-1732): drop the 1800s heartbeat line
85d9f61d           2026-08-31 12:04:52 +0900  issue-2906: quiet HEALTHY heartbeat re-notification (#2913)
```

derived: `date -d "2026-08-31" +%s` minus `date -d "2026-08-18" +%s` = 1123200 seconds /
86400 = 13 days, not twelve. Both the PR body and the landed handbook text repeat "12
days" — an off-by-one in a document whose stated purpose is precision-correction of an
earlier imprecise bound.

### Finding 3 (MODERATE) — claim (d)'s framing exculpates #2913 more than the history supports

The PR's claim (d) frames #2913 as merely "revert[ing] an accidental one-day forcing
cadence rather than causing a new regression." That is defensible only in the narrow sense
that #2913 did not *create* the underlying turn-gated-only detection gap (that dates to
#1732, 13 days earlier per Finding 2). It elides the more consequential reading: the #2905
bug that #2913 fixed had been accidentally producing near-continuous notifications for
about a day — canonical: `85d9f61d` commit message (read via `git show -s`) — result:
"[poll-report] HEALTHY line always includes the entry's last-tool-activity timestamp,
which changes on nearly every due tick ... defeating poll_heartbeat_delta.py's ... delta
suppression ... measured at 87.8% of 2493 Monitor-relayed task-notifications carrying no
actionable content" — which functioned as an unintentional liveness signal masking the
#1732 gap. #2913 removed that accidental signal along with the noise, which is the change
that made the pre-existing, latent #1732 gap operationally live again for the first time
since 2026-08-18 — not a neutral fact the PR's "reverted an accident, not a new
regression" framing conveys.

### Finding 4 (MINOR) — claim (a)'s call-site count is narrowly true but omits a third, undisclosed source-level call site

canonical: `gh pr diff 2917 --stat` — result:
```
docs/handbooks/monitor-liveness.md                                                    | 78 +++++-  (modified)
docs/issue-2915/reports/diagnose-first+observability-methodology-selection-f198342c.md | 270 ++++ (new)
.../diagnose-first+observability-methodology-selection-f198342c/2026-08-31-hunt-build-now-docs-only.md | 19 ++ (new)
.../deviation-log/20260831T035256899558-d9183944b5e44541.md                           | 14 ++ (new)
4 files changed, 376 insertions(+), 5 deletions(-)
```
Confirms the PR is genuinely doc-only (satisfies the "no new bugs" / "no monitor-watch
breakage" invariants trivially, since no `.sh`/`.py`/`.json` is touched).

Within `hooks.json`'s wiring, claim (a) is verified: exactly two call sites —
`on-the-record/hooks/directive.sh:272` (wired to `UserPromptSubmit`) and
`on-the-record/hooks/stop-poll-rearm.sh:133` (wired to `Stop`) — confirmed by reading all
5 registered event types in `on-the-record/hooks/hooks.json` and grepping every other
wired script for the staleness-check symbols, with zero hits. The search was bounded as:
whole-repo grep for the literal function name `_monitor_liveness_check_and_notify` and the
artifact names `poll_heartbeat_alive.json`/`MONITOR-DEAD` (not scoped to `on-the-record/`
alone); confirmation that only one `hooks.json` outside `docs/` exists — derived: `find .
-name hooks.json -not -path './docs/*'` — result: 1 hit; the other 34 are unrelated decoy
skeleton templates under `docs/issue-170`/`docs/issue-167`, individually checked and
confirmed to contain neither `staleness` nor `MONITOR-DEAD` nor `poll_heartbeat`; a
repo-wide check for cron/systemd/timer files and symlinks — derived: `find . -iname
'*cron*' -o -iname '*.timer' -o -iname '*.service'` and `find . -type l` — result: zero of
either; and tracing `poll-rearm.sh` (sourced by both hook scripts) to confirm it does not
itself define the staleness-check function.

However: `tests/run-orchestrate-tests.sh:18-20` execs `bash "$H/directive.sh"` directly,
outside any `hooks.json` trigger, purely to test stdout-injection behavior — since
`_monitor_liveness_check_and_notify` is called unconditionally near the bottom of
`directive.sh` (line 272), this test harness invocation also executes the staleness-check
function. It is test-only and not reachable from a live session, so it does not change the
production-path conclusion, but the PR's claim ("exactly two call sites... cross-checked
against hooks.json's full event wiring") is accurate only for the hooks.json-wired scope
and does not disclose that a third, source-level invocation point exists. Materiality: low
(no production behavior implication), but it is exactly the kind of "clean answer for a
population the search never fully reached" pattern the task flagged as this repo's
recurring defect class — the PR's search was scoped to hooks.json wiring, not to "every
call site" as claim (a)'s own wording states.

### Finding 5 (MINOR) — claim (b)'s Summary line ("0 of 29") is a technically-consistent but incomplete compression of the Test Plan's own "1/30"

canonical: `gh pr view 2917 --json body` — result, PR body Summary: "0 of 29 simulated
ticks emitted any notification across a 60-minute healthy, unchanging-roster stretch." PR
body Test plan: "1/30 ticks emit over simulated 60 min."

derived: reproducing the PR's own simulation script (`python3 /tmp/issue2915/sim_healthy_ticks.py`,
30 ticks × 120s = 3600s = 60 minutes exactly, no boundary bug) — result: tick 0 always
emits unconditionally (a pre-existing, #1220-era baseline-snapshot behavior —
`poll_heartbeat_delta.py`: `first_tick = not os.path.exists(state_path)` ... `if
first_tick or changed or ALWAYS_RE.search(line):`), and ticks 1-29 (the 29 *remaining*
ticks) correctly stay silent under #2913's delta-suppression — derived: 1 (tick 0, emits) +
29 (ticks 1-29, silent) = 30 total ticks. "0 of 29" and "1 of 30" are therefore the same
run described two ways, not conflicting measurements. But the Summary's phrasing, read in
isolation, drops the "of the remaining" qualifier and could be read as "zero notifications
fired in the entire hour," which is not what happened (one did, at tick 0, by design). This
is the same pattern as Findings 2-3: technically-narrow truths worded to read more
favorably than the full picture supports.

Separately, claim (c)'s ~29ms staleness-check latency was independently reproduced — derived:
timing the extracted staleness-check body directly, 10 trials — result: mean 21.79ms
(range 17.4-26.5ms), and via the bash-wrapped path — result: mean 24.67ms (range
19.7-32.1ms) — same order of magnitude as the claimed 28.8ms. Substantiated by a real,
reproducible measurement, not asserted without evidence. No finding here beyond noting the
PR states a single-shot value rather than a mean/variance.

### Finding 6 (confirms PR is accurate) — the handbook edit is mechanism-accurate, not a gap-relabel

Both threshold values and their file/default attribution were independently verified
against source — canonical: `on-the-record/hooks/directive.sh:211`,
`on-the-record/hooks/stop-poll-rearm.sh:56`, `watchdog.py:67`,
`on-the-record/monitors/poll-heartbeat.sh:184` (all read directly) — and match exactly:

```
on-the-record/hooks/directive.sh:211        local threshold="${MONITOR_LIVENESS_STALE_SECONDS:-360}"
on-the-record/hooks/stop-poll-rearm.sh:56   local threshold="${MONITOR_LIVENESS_STALE_SECONDS:-180}"
watchdog.py:67                              POLL_INTERVAL_SEC = 60
on-the-record/monitors/poll-heartbeat.sh:184 sleep_seconds="${POLL_HEARTBEAT_SLEEP_SECONDS:-120}"
```

The handbook's "unbounded absent a turn" conclusion is a correct description of the actual
current mechanism — canonical: `on-the-record/hooks/hooks.json` (all 5 registered event
types read in full) and `on-the-record/hooks/directive.sh:207-272` /
`on-the-record/hooks/stop-poll-rearm.sh:52-133` (both staleness-check bodies read in full)
— result: both are wired exclusively to turn-triggered events (`UserPromptSubmit`,
`Stop`), no periodic/timer-driven event registers either function — including the
zero-turn edge case. This is not a documented-limitation relabel of an unexamined gap; the
gap was genuinely traced to its root cause (turn-gated invocation, no coupling to the
Monitor's own turn-independent tick). The defect is entirely in the conclusion drawn from
that accurate mechanism description (Finding 1), not in the mechanism description itself.

### Standing invariants (re: PR #2917's own diff, not this record's)

- No revival of the retired role axis: clean — canonical: `gh pr diff 2917` full text
  (read directly) — result: the only "role axis" hit in the diff is the PR's own prose
  quoting this review's four invariants back at itself (self-referential, not
  config/vocabulary reappearing).
- No new bugs: not applicable / clean — canonical: `gh pr diff 2917 --name-only` — result:
  zero `.sh`/`.py`/`.json` files touched (see Finding 4's diffstat).
- No overhead increase: clean — canonical: `gh pr diff 2917` full text (read directly) —
  result: no new timer, cron, or process; the diff only narrates pre-existing intervals.
- No monitor/watch breakage: clean — canonical: `gh pr diff 2917 --name-only` — result: no
  monitor or hook script modified; the doc's quantitative claims match source (Finding 6),
  so it does not plant a wrong-threshold landmine for a future code change. Caveat:
  Finding 4's undisclosed third call site is a precision gap in the doc's own accuracy
  claim, not a functional break.
- Historical records under `docs/` are unchanged/unrenamed: clean — canonical: `gh pr diff
  2917 --name-only` (see Finding 4's diffstat) — result: the diff modifies only the living
  handbook `docs/handbooks/monitor-liveness.md` and adds new files under
  `docs/issue-2915/`; no `docs/issue-*/reports/` historical record is renamed, migrated, or
  modified by this PR.

## Next steps

Per adversarial-review's protocol, this session evaluates and does not fix. Routing:
Finding 1 (claim (e) unsupported against the issue's own acceptance bar, with an
unreconciled candidate mitigation) is the one that should block accepting PR #2917 as a
final resolution to issue #2915 as-is — either the PR needs to evaluate/rule out the
`poll-heartbeat.sh`-coupled bounded-backstop mitigation and get explicit sign-off that
unbounded worst-case latency is an accepted tradeoff for reduced noise, or a follow-up
issue needs to carry that decision explicitly rather than leaving it implicit in a
"no code change is warranted" conclusion. Findings 2-3 (13-day arithmetic, exculpatory
framing) and 5 (Summary phrasing) are correctness/precision fixes to the same PR before
merge. Finding 4 (undisclosed third call site) is optional-disclosure, low materiality.
`loop_state: landed` reflects this record's own completion — the decision on PR #2917
itself is the maintainer's, not this session's.
