# Survey — issue #1043 execution-observation

## Scope

Observed: role `implementation`, issue #1043, subject `issue-1043`.
Named this session, not "recent work" — resolved by reading the issue
and its PRs first, before any of the observed role's own record.

## What was read this session, in order

1. canonical: `gh issue view 1043` (this session).
   Issue body (watcher-dead false-positive report, requirement linkage
   R001) plus full 9-comment thread.

2. canonical: `gh pr view 1050` / `gh pr diff 1050` (this session).
   `issue-1043/implementation`'s first PR, state CLOSED, 3 docs-only
   files. canonical: `gh pr view 1050 --json comments` (this session):
   its own comment reads "Duplicate of merged PR #1049."

3. canonical: `gh pr list --search 1043 --state all --json
   number,title,state,headRefName,mergedAt` (this session).
   Full PR set for `issue-1043/implementation`: #1049 merged (phase-1),
   #1050 closed (duplicate), #1059 closed, #1061 merged (phase-2
   re-delivery).

4. canonical: `gh pr view 1049 --json state,mergedAt,body,files,commits`
   (this session).
   Merged phase-1 proposal PR, squash commit
   `002878c0251f4ac9cb22470815ae72a00cad948c`.

5. canonical: `gh pr diff 1061` (this session, full diff, read before
   its own record narrative).
   Landed code change: `spawn.py` (`_watch()` read-before-write
   watcher-claim guard) and `tests/test_spawn.py` (two new `WatchFollow`
   cases), plus proposal/hunt/`reports/implementation.md`. Squash commit
   `5f5e5ff060f7e2f25fd1e8aa62b3f844f332021d`.

6. canonical: `docs/issue-1043/reports/implementation.md` (read via
   `gh pr diff 1061`, this session, after the diff per fresh-eyes
   ordering) — the observed role's own phase-2 record.

7. canonical: `Read spawn.py:3903-3966` (this session, current working
   tree).
   Confirmed the merged hunk is coherent with `_watch()`'s existing
   `key`/`entry` locals (`_lookup_roster_entry`), not dangling.

8. canonical: `python3 -m pytest tests/test_spawn.py -k watcher_dead`
   (executed live this session against the current working tree).
   result: `2 passed, 501 deselected`.

## What is being judged

Three verdict levels, against the evidence named above:
- **outcome** — whether PR #1061 (the code that actually landed)
  satisfies issue #1043's stated acceptance ("stale auto-armed pid +
  live follow watcher → no watcher-dead flag; no watcher at all → flag
  fires"), recomputed as the worst case among the record's own cited
  step-level results, not restated as a summary.
- **trajectory** — three named checks: scouted-when-required (survey.md
  records a scout skip under the pure-bugfix ground), surveyed-before-
  proposing (survey.md predates and is cited by the proposal),
  approved-by-human (a real `APPROVE issue-1043/implementation` string
  match from an approvers.md account, single-account mode since
  `JiwonJung94` authored and approved).
- **step** — whether `spawn.py:3903-3966` and its regression tests are
  each sound, including the observed role's own before-landing hunt
  finding (a TOCTOU race in the read-before-write guard, judged
  non-blocking by the observed role itself).

## Scout skip record

Skipped. This is an audit/observation task against a fully-specified
verdict methodology (`roles/specs/execution-observation.spec.json` in
`tokenmaxxxer/on-the-record`, plus this session's own role directive) —
there is no product-facing or exemplar-comparable design decision open;
the methodology itself is fixed by the spec and the role directive, not
by this session's judgment. Matches the scout-directive's own skip
condition for work the spec already leaves no design decision open on.
