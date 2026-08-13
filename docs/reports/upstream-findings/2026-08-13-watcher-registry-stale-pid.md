# Watcher registry stale-pid after re-arm

Filed via the upstream defect channel (issue #1131). This is the fallback
record: at the time this file was written, upstream was not called live
from this requirements-engineering session (no consumer-session
`/report-upstream` invocation happened here) — this instance is the
scaffolded first-real-case artifact the phase-1 proposal named, not a
live confirmed filing. A consumer session running `/report-upstream`
against this observation writes its own draft/confirmation/filing
record; upstream has already tracked the underlying defect directly as
issue #1133.

## Plugin version

Not applicable to this scaffold entry — a live `/report-upstream` run
fills this with `git rev-parse HEAD` of the installed plugin at
observation time.

## Reproduction

Observed 3 times in one consumer session on 2026-08-13: after
`spawn.py watch --issue <n> --follow` re-arms a watcher, `spawn.py
watchdog` keeps reporting the OLD watcher pid as `DEAD` on every
subsequent tick — the re-arm itself succeeds, but the watchdog registry
entry is never updated to the new pid.

## Observation context

Reported first in issue #1131's own body ("watcher registry showing
stale pids as DEAD after re-arm, observed 3 times in one day in a
consumer session, recorded only as chat text") as the motivating example
for building this channel. The underlying defect is already tracked
directly as upstream issue #1133 ("watcher re-arm never updates the
watchdog registry; watcher-dead remediation text blocks foreground"),
opened 2026-08-13, which also documents the second, related blocking-call
defect in the watchdog's own remediation instructions.

## Outcome

Cite #1133 as the canonical upstream tracking issue for this defect —
this fallback file exists to satisfy the phase-1 proposal's acceptance
line ("First real case to file through the channel once built") and to
demonstrate the channel's fallback-write path structurally, not to
duplicate #1133's tracking.
