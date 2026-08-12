# Deviation loop (issue #803)

Nests inside the #699 R3 goal loop (`directive.sh`'s "YOUR DEVIATION LOOP"
paragraph carries the injected steering text verbatim; this handbook is the
reference doc for the entry format the guard checks). Design source:
`docs/issue-803/proposals/2026-08-11-self-driven-deviation-loop.md`.

## RECOGNIZE

A deviation is mid-task work that is NOT normal task friction: it counts
only if resolving it needs something the current task's own scope did not
already call for (an edit outside the frozen write set, a role-shaped
judgment, a risk that would recur beyond this one task). A test failure
the task exists to fix, a routine lint/type error in a file already being
edited, or an expected retry is not a deviation.

## CLASSIFY

**INLINE-FIX** iff all hold:
1. stays inside the current task's frozen write set,
2. mechanical — no design/architecture/security/product judgment a
   reviewer would need to weigh alternatives on,
3. does not change what the deliverable claims to do,
4. a one-off, not a recognizable systemic pattern.

**FILE-AS-ISSUE** otherwise. When (1)-(4) do not obviously resolve the
call, render it via one `spawn.py consult <role> "<question>"` call before
acting.

## RESOLVE AND CONTINUE

Both cases append to a deviation log — `docs/issue-<n>/reports/deviation-log.md`
when an issue is in scope, else `docs/reports/deviation-log.md` (same
issue-keyed-vs-not split `consult-log.md` already uses).

- **Inline**: apply the fix, append one line — timestamp, `inline`,
  one-line description, the diff's location. Resume the original task
  same turn.
- **Filed**: draft the issue, `spawn.py spawn <role> "<task>" --issue <n>
  --background`, append one line — timestamp, `filed`, issue number,
  role, one-line description. Wait via `spawn.py watch --issue <n>` if
  the deviation blocks the original task, otherwise continue other work
  in parallel. When the PR merges, append a `resolved` line — timestamp,
  `resolved`, issue number, PR, one line on what changed — and resume the
  original task referencing the resolution.

Every deviation, inline or filed, leaves exactly one traceable log entry;
RECOGNIZE keeps this from becoming noise (no entry for non-deviations).

## Enforcement

`on-the-record/hooks/deviation-log-guard.sh` (Stop hook) reads
`transcript_path` off the raw Stop event, scans it for a recognized-
deviation marker, and cross-checks via `git diff`/`git log -p` against the
deviation-log path(s) whether a matching append landed this turn. It
refuses session-end via `hookSpecificOutput.additionalContext` (not a hard
block) when a marker exists with no matching append.

## Dependencies

- Depends on #787 (a plain session entering orchestration) for this loop
  to have anywhere to run.
- Depends on #801 (quiet-gap self-wake) for full autonomy on filed
  deviations that outlive the current turn.
- Neither dependency is resolved by this document; both are carried
  forward from the design proposal unchanged.
