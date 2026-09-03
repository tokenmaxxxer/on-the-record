<!-- on-the-record orchestrate directive, on-demand section file (issue #2102). Loaded via the always-on index injected by hooks/directive.sh. -->

What a wake is for (issue #3275).

The poll-heartbeat fires on a 120s cadence
(`on-the-record/monitors/poll-heartbeat.sh`, `POLL_HEARTBEAT_SLEEP_SECONDS`,
default 120). Before this file existed the cadence was armed and nothing said
what to do when it fired, so orchestrators read each tick as routine noise and
answered it with a line of acknowledgement. The mechanism ran; the behavior it
exists to drive did not.

A tick is not a report to be acknowledged. It is your turn to look.

## On every wake, inspect before you conclude

Do these yourself. Do not substitute the tick's own summary for them — the
summary is what one instrument saw, and the point of waking is to see what it
did not.

1. **Did the workspaces change?** For each RUNNING session, list files written
   under its workspace since the last wake. A session with no new artifact in
   several minutes is a question to answer, not a line to skip.
2. **What did it actually run?** Read the last handful of tool calls from the
   session log. Commands that only observe (`ps`, `ls`, `tail`, `git status`,
   repeated status polls) mean the session is waiting, not working.
3. **Is it still pointed at the goal?** Compare what it is doing against the
   issue it was spawned for. Drift is easiest to catch early and cheapest to
   correct mid-round, by issue comment, rather than at PR time.
4. **Is the observation layer itself alive?** If notifications have gone quiet
   while you are polling by hand to fill the gap, that is the signal — a
   silent channel and a quiet system look identical (issue #3275).

## Waiting is a third state, not a healthy one

`RUNNING` plus a growing log is *alive*, not *advancing*. A session that polls
in a loop grows its log forever and never moves. Three states, and they must
not collapse into two:

- **advancing** — new artifacts, commits, or PR state since the last wake;
- **waiting** — alive, log growing, but the growth is observation calls only;
- **stalled** — no growth at all.

`gates/session_progress.py` computes this distinction; `waiting` is reported,
never counted as healthy progress.

## What reaches the user

Not every wake is worth a message. Report a tick when it changed what you
know: a session waiting long enough to be worth intervening in, drift from
the issue, a returning PR, an observation channel that went silent. Absorb
the rest. A wake that found nothing is still a wake that did its job.

## Stopping and re-arming your own monitor (issue #3293)

The monitor is yours to end, and only yours. When the work is genuinely
finished -- no session running, nothing outstanding on the board, nothing
the user is waiting on -- stop it:

```
python3 CHECKOUT/spawn.py monitor-list        # tokens owned in this cwd
python3 CHECKOUT/spawn.py monitor-stop --owner <token>
```

The token is printed by your own heartbeat into
`~/.claude/tokenmaxxxer/poll-watchdog.log` as an `owner=` line. Take it
from there or from `monitor-list`. Never stop a heartbeat by pattern
(`pkill -f poll-heartbeat`): several sessions run on one machine, often
against other repositories entirely, and a pattern kill takes all of
them. That is the defect this issue removed, and reintroducing it by hand
is the same defect.

`monitor-stop` refuses rather than guesses. A refusal names its reason --
stale marker, reused pid, malformed token. Read the reason; do not retry
with a wider match.

Re-arm when work returns. The moment you spawn a session, or accept a new
ask from the user, arm poll-heartbeat again via the Monitor tool with
`persistent: true`. An un-armed monitor makes spawned sessions
unobservable, and unobserved is the worst state this system can be in --
worse than noisy.

The tick never tells you the work is done. It cannot: checking the board
and open issues on every 120s wake is too costly, so an idle tick says
only that no session is running and lists what the cheap local sources
knew -- a PR that returned this very tick, above all. It marks the
sources it did not consult, because outstanding work there is unknown,
not absent.

So the stop decision is yours and it takes one look, not an inference
from silence: when a tick reports no sessions running, check the board
and the open issues yourself, and stop the monitor only if that check
comes back empty. Two states look identical from silence alone and are
not -- the work is done, and nobody started the next thing.
