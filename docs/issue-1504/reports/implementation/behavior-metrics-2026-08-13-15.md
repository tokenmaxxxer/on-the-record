# Agent-behavior efficiency metrics — 2026-08-13..15 drives

derived: `python3 scripts/behavior_metrics.py --since 2026-08-13 --until 2026-08-16 --json`

```
(a) re-check keys with count>1: 1
(b) zero-commit implementation sessions: 1
(c) issues with round-trip artifacts: 97
(d) wait/poll seconds: None (not derivable: no runs/ or roster heartbeat history is git-tracked in this checkout)
```

## (a) re-check count per (role, issue, unchanged-subject-hash)

canonical: `docs/issue-1163/reports/conformance-review/deviation-log.md`,
read this turn — git-tracked, no history walk needed (current file
content already carries every turn's entry as an append-only log).

canonical: `python3 scripts/behavior_metrics.py --since 2026-08-13 --until 2026-08-16 --json`, this turn —
25 re-check entries extracted repo-wide; 24 belong to
`docs/issue-1163/reports/conformance-review/deviation-log.md` (role
conformance-review, issue 1163), matching the PR #1489 re-check loop the
issue names. 1 entry has no resolvable role directory (`unknown`).

derived: `python3 -c "import sys; sys.path.insert(0,'scripts'); import behavior_metrics as bm; e=bm.extract_recheck_entries(bm.REPO); print(len(e))"`
```
25
```

Limitation: the subject-hash is computed by stripping timestamps, hex
shas, and digits from each entry's line and hashing what remains.

canonical: `docs/issue-1163/reports/conformance-review/deviation-log.md` (read
this turn) — the 24 entries there hash to mostly-distinct values (max
repeat count 2, per the `derived:` command above) even though a human
reading them can see they are all the same blocker (missing `APPROVE
issue-1163/conformance-review` comment) re-stated with different
supporting evidence each turn (different PR numbers cited, different
`gh` output quoted). Natural-language re-check narration varies enough
turn to turn that a text-hash dedup under-merges.

The entry count per (role, issue) — 24 for (conformance-review, 1163) —
matches the issue's own "re-checked the same unresolved blocker 35
times" framing better than the hash-bucketed count. scripts/
behavior_metrics.py exposes both (`recheck_counts()` for the hash-keyed
view, `extract_recheck_entries()`'s raw list for the per-(role,issue)
count).

## (b) sessions ending with 0 commits vs. role's expected deliverable

canonical: `git log --since=2026-08-13 --until=2026-08-16 --name-only`,
this turn, filtered to commits carrying a `Subject: issue-<n>` trailer,
grouped by issue for the `implementation` role.

canonical: `git show --stat 01660bf9a9a9c9a920326ffc187a2fc71c749dfa`, this turn —
issue #1468's implementation-record-carrying commit
("record six unrecorded gates/*.py modules in enforcement-boundary.md")
changed only `docs/issue-1468/reports/implementation.md` and
`docs/specs/enforcement-boundary.md` — zero non-doc (code) files.

derived: `python3 scripts/behavior_metrics.py --since 2026-08-13 --until 2026-08-16 --json` (`b_zero_commit_sessions` field)
```
1 flagged session: issue 1468, role implementation, commits 0
```
out of 97 implementation-role landings the same run identified
(`c_round_trips_per_landed_issue` key count from the same output).

This is a narrower signal than the issue's "0 commits" framing — that
issue names a session that produced literally zero commits and was
recovered only by watchdog respawn. A session that never commits leaves
no git trace by definition, so this checkout cannot contain that exact
artifact.

canonical: `find docs/issue-1490 -type f` (read this turn) — issue
#1490's tree has only a proposal and a survey, no implementation.md and
no deviation-log entry describing a terminated attempt, consistent with
that gap. What IS derivable and reported here is the adjacent pattern:
an implementation session whose landed commit changed only
documentation, not the code the role's issue asked for — named as its
own waste-pattern row below, distinct from true zero-commit
termination.

## (c) round-trip count per landed change

canonical: `gh pr list --state merged --search "merged:2026-08-13..2026-08-15" --limit 200 --json number,title,body`, this turn —
200 merged PRs returned (page-capped; true count may be higher).

Source: count of files under `docs/issue-<n>/{proposals,reports}/**/*.md`
(one round-trip unit per proposal/report/deviation-log artifact),
restricted to the issue numbers that same `gh pr list` output names in a
PR title or body.

derived: `python3 -c "import sys; sys.path.insert(0,'scripts'); import behavior_metrics as bm; l=bm.extract_landed_issues('2026-08-13','2026-08-16'); print(len(l), sorted(l)[:5])"`
```
97 ['0', '1', '1097', '1109', '1110']
```

Limitation: the issue-number extraction (`#(\d+)` / `issue-(\d+)` regex
over PR title+body) over-matches on bare `#<digit>` occurrences inside PR
bodies that are not issue references (list markers, code excerpts) — `0`
and `1` in the derived output above are visibly spurious. The remaining
entries are consistent with known high-round-trip subjects:

derived: `python3 -c "import json; d=json.load(open('/tmp/bm.json')); print(sorted(d['c_round_trips_per_landed_issue'].items(), key=lambda x:-x[1])[:5])"`
```
[('1199', 96), ('1174', 66), ('1160', 14), ('1163', 10), ('1165', 10)]
```

This gap is named again under the follow-up recommendations below and
left uncorrected in this delivery: correcting it needs either a
stricter PR-body convention (e.g. requiring `Closes #<n>` specifically,
already a repo convention per contract v3 s19 phase-2 PRs) or
cross-referencing against `docs/issue-<n>/` existing on disk, which the
script does not yet do.

## (d) wait/poll time attributable to sessions blocking on external state

canonical: `find . -maxdepth 1 -type d` (read this turn, also recorded in
`docs/issue-1504/reports/implementation/survey.md`) — no `runs/`
directory or roster heartbeat/wait-state log is git-tracked, so this
metric is not derivable from this checkout.

canonical: `find docs/issue-1490 -type f`, this turn — returns only a
proposal and a survey for issue #1490, the issue's own cited example
("Issue #1490 phase-2 (first attempt): the implementation session
entered a background-wait pattern and terminated with 0 commits") is not
present as a committed artifact, consistent with the same gap: a session
that waits or terminates without committing leaves no git trace to
recover after the fact.

Missing record needed to make (d) live-derivable: a per-session
wait/poll event log (start/stop timestamps of each blocking wait, keyed
by session id) written to a git-tracked or otherwise durable location —
no such record exists, live or historical, per the two canonical checks
above.

## Ranked waste patterns (by measured/estimated cost)

1. **Re-check loop on an unresolved approval blocker** (metric a) —
   24 re-check turns on issue 1163/conformance-review
   (canonical: `docs/issue-1163/reports/conformance-review/deviation-log.md`,
   read this turn), each a full role session spawn producing an
   identical verdict ("blocker still holds", per the entries quoted in
   the (a) section above). Cost estimate: 24 session spawns, each
   citing at least 2-3 `gh`/`git` round-trips in its own `canonical:`
   line, for zero net progress across all 24. Highest-confidence,
   highest-volume pattern in this window.
2. **Round-trip artifact volume concentrated on a few issues** (metric c)
   — issues 1199 and 1174 each carry 60-96 proposal/report artifacts
   (derived counts above), an order of magnitude above the median landed
   issue. Whether this reflects genuine iteration complexity or the same
   re-check/respawn waste as pattern 1 is not distinguishable from
   artifact count alone; flagged as data-insufficient for a rules issue
   without a manual read of those two issues' logs.
3. **Doc-only "implementation" landing** (metric b) — issue 1468's
   landed commit touched no code, only two doc files
   (canonical: `git show --stat 01660bf9a9a9c9a920326ffc187a2fc71c749dfa`,
   this turn), for a role whose deliverable was a code-test fix. Single
   occurrence in this window; too low-volume on its own to justify a
   policy change, but worth watching if it recurs.
4. **Wait/poll time (metric d) and true zero-commit terminations** —
   entirely unmeasured; the issue's own headline anecdote (#1490's
   background-wait termination) is itself invisible to this repo's git
   history (canonical: `find docs/issue-1490 -type f`, this turn). This
   is a data gap, not a measured-zero result.

## What record would detect each pattern LIVE (design only, no enforcement)

- Pattern 1 (re-check loop): a watchdog-side counter keyed by
  (role, issue, blocker-identity) that increments on each respawn whose
  deviation-log entry matches the prior entry's `filed`+"still holds"
  shape; observe-only signal, no cap. Needs deviation-log entries to
  carry a stable `blocker-id:` field instead of free narration, so the
  signal does not depend on this script's fragile text-hash dedup
  (see (a)'s limitation above).
- Pattern 2 (artifact volume): a per-issue artifact-count gauge, alerting
  (observe-only) when an issue's `docs/issue-<n>/{proposals,reports}/`
  file count crosses a percentile threshold relative to the issue's own
  historical median — requires no new record, just a periodic re-run of
  this script's `round_trip_counts()`.
- Pattern 3 (doc-only landing): a merge-gate-adjacent check comparing an
  implementation-role commit's changed-file set against the issue's
  declared write set (already tracked in the phase-1 proposal's `files:`
  frontmatter) — flags when zero write-set-declared code paths changed;
  observe-only.
- Pattern 4 (wait/poll, zero-commit): needs a new record — a
  session-lifecycle log (session start, each wait/poll event with
  duration, session end with commit count) written to a durable,
  git-tracked-or-equivalent location. This does not exist today per the
  two `find` canonical checks in the (d) section above; it is the
  largest gap named in this report.

## Follow-up-issue recommendations

- **Data-sufficient now**: pattern 1 (re-check loop) has 24 concrete,
  citable instances in this window alone plus the issue's own 35-count
  anecdote from a different window — enough volume to justify a
  rules/caps follow-up issue (e.g. "cap consecutive identical-verdict
  re-checks, escalate to park after N" per the precedent already landed
  in `docs/issue-1476/proposals/park-approval-blocked-respawn.md` for a
  related respawn class).
- **Data-insufficient, needs instrumentation first**: patterns 2, 3, and
  4. Pattern 2 needs the artifact count corrected for spurious issue-ref
  matches (tighten `extract_landed_issues()`'s regex, or cross-reference
  `docs/issue-<n>/` existence) before it is trustworthy enough to size a
  rule against. Pattern 3 has one instance — not enough volume yet.
  Pattern 4 has zero instances because the record it needs does not
  exist; the recommended follow-up there is instrumentation-only (add
  the session-lifecycle log named above), with any caps/rules deferred
  to a second follow-up once that log has accumulated real data.
