---
status: approved
files:
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/test_pr_preflight.py
  - docs/issue-1177/reports/implementation/survey.md
  - docs/issue-1177/proposals/amendments-reconciled-preflight.md
  - docs/issue-1177/reports/implementation.md
---

## Request

Role sessions currently never re-read the issue thread before opening
their PR, so an operator comment posted mid-run (an amendment) is missed
and the orchestrator has to request a revision and respawn — this
happened 4 times on one day (PRs #1167/#1168/#1170/#1176). Add a
mechanical pre-PR check that refuses `gh pr create`/`gh pr edit` when the
newest issue comment postdates the session's spawn time, until the
role's own record cites that comment's id.

## Constraints

- Enforcement-hooks-only: the check has to be a hook, not a norm the role
  is asked to follow.
- Existence check only — whether the record *cites* the newest comment
  id, not whether it correctly *addressed* the amendment's content (that
  judgment stays with review, per the issue's Requirement 2).
- False-positive bound: an issue with no comments after spawn time must
  pass untouched (Requirement 3 / Acceptance empty state).
- Zero-install: this hook ships inline (no `gates/` import), same
  constraint `pr-preflight.sh` already operates under.

## Rationale

Considered a new sibling hook (`amendments-preflight.sh`) instead of
extending `pr-preflight.sh`. Rejected: the phase-determination block in
`pr-preflight.sh` already fetches `gh issue view <n> --json comments` and
already parses the branch into `issue`/`role` — a sibling hook would
either re-run that same `gh` call (double the network round-trip on
every `gh pr create`/`edit`) or need to import internals from a script
that is deliberately not import-safe (it embeds its logic in a bash
heredoc specifically so it needs no `gates/` checkout — see
`pr-preflight.sh`'s own header comment). Extending the existing hook
keeps the "block `gh pr create`" responsibility in one file and reuses
work already done for a different check.

Considered keying "directive-load time" off the record file's own mtime
or the branch's first commit time. Rejected: neither reflects when the
session actually loaded its directives — a record file can be created
minutes into a session, and the branch's first commit can predate spawn
by an arbitrary amount if the branch was created earlier and resumed.
spawn.py already timestamps the actual moment (`session-start` event, ts
= `time.time()` at the point the session process starts) into a file
that survives the session and needs no new instrumentation.

## What will be done

Extend `pr-preflight.sh`'s existing GUARD script, right after phase
determination:

1. Read the session's directive-load time as the last `session-start`
   event's `ts` from `<cwd>.events.jsonl` (spawn.py's existing sibling
   events file — `EVENTS_SUFFIX = ".events.jsonl"`, `_events_path(work)`
   = `Path(str(work) + EVENTS_SUFFIX)`). Missing file, missing event, or
   unparseable timestamp → fail-open (no block; matches the file's
   existing fail-open convention for every other unknown).
2. From the `comments` list already fetched for phase determination,
   find the newest by `createdAt`. No comments, or none newer than the
   directive-load time → pass untouched (Requirement 3's empty state).
3. If the newest comment postdates spawn: parse its numeric id from
   `url` (`#issuecomment-<digits>`), then check
   `docs/issue-<n>/reports/<role>.md` for a line containing both
   `amendments-reconciled` and that numeric id. Missing file or missing
   line → `deny()` (exit 2) with a hint naming the record path and the
   comment id to cite. Present → pass.

Add hermetic `test_hook_*` cases to `test_pr_preflight.py`, following the
file's existing subprocess-driven pattern (stub `gh`, real script,
`tmp_path` repo): denies on an unreconciled post-spawn comment, allows
once reconciled, allows with no post-spawn comments, allows with no
comments at all, and allows (fail-open) with no events file.

## Accumulation

This adds no new inline `gh`/subprocess call — it reuses the `comments`
list `pr-preflight.sh` already fetches once per invocation for phase
determination (see Rationale). If N more pre-PR checks needed their own
comment/timestamp read in the future, each would cost one more pass over
the same already-fetched `comments` list (cheap, in-process), not one
more `gh` round-trip — so this does not create a per-check network-call
accumulation. The one place this *does* accumulate is `pr-preflight.sh`
itself growing one more `deny()`-guarded block per new pre-PR rule; that
growth is the same shape the file already has (phase check, plan check,
closing-keyword check) and stays within one file rather than spreading
across sibling hooks, which is the choice this proposal's Rationale makes
explicitly.

## Out of scope

- Verifying that the record's reconciliation actually addresses the
  amendment's content — the issue explicitly assigns that to review.
- Any change to how `spawn.py` writes `session-start` events — read-only
  dependency.
- A sibling hook file — folded into the existing one per Rationale.

## How you'll know it worked

`python3 -m pytest on-the-record/hooks/test_pr_preflight.py -v` — all
cases pass, including the new `test_hook_*_post_spawn_comment*` and
`test_hook_allows_pr_when_no_events_file` cases pinning the Acceptance
bar (fixture issue with a post-spawn comment blocks until reconciled;
without one, no block).
