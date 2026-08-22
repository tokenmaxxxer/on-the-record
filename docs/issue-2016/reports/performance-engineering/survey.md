---
subject: issue-2016
---

# Survey: single-session wall-clock attribution (phase 1, measurement only)

Scope: profile one representative single-phase role session end-to-end —
boot, directive assembly, per-tool-call gate/hook overhead, test tail,
record/PR ceremony — and attribute real wall-clock to each named bucket.
canonical: `gh issue view 2016` (Acceptance text: "Phase 1 is
measurement ... Only buckets that measurably dominate get a fix
proposal"). This survey pass makes no optimization edits, per that
scope.

skip note: scouting (scout-directive) skipped — this is pure internal
measurement of this repository's own hook/test machinery, not a
product-shaped deliverable with external exemplars to compare against;
the spec (Acceptance) fully determines the deliverable shape (named
buckets + top-2 + numbers), leaving no open design decision scouting
would inform.

## Method

Every number below is either read from an already-instrumented source
(spawn.py's own `_BOOTSTRAP_TIMING`, real session transcript logs) or
measured live in this session by invoking the actual hook script with a
representative stdin payload and timing it with `date +%s.%N`. Hook
scripts were run standalone (not through the Claude Code harness), so
these numbers exclude harness-side IPC/process-spawn overhead on top of
the script's own wall-clock — they are a floor for hook cost, not a
ceiling.

Two hook layers exist and both fire on every Bash tool call in a real
session: the `core` plugin's hooks (`CLAUDE_PLUGIN_ROOT=/home/jwjung/tokenmaxxxer-core/core`)
and this repo's own `on-the-record/hooks/*.sh`, wired separately in each
plugin's `hooks.json`.

## Bucket 1 — boot (spawn.py's own instrumented phases)

spawn.py has carried per-phase bootstrap timing since issue #711
(`_BOOTSTRAP_TIMING`, `_timed()`, `spawn.py:102-121`), printed as
`bootstrap_timing` on every spawn (`spawn.py:8197`).

derived: `grep bootstrap_timing` over real implementation-session log files, different subjects, different days

Measured value: `workspace=0.000 branch=0.000 rulebook=0.000 core=0.000
gh_token=0.000 settings=0.001 total=0.001` seconds, identical across
those independent respawns.

spawn.py's own accounted bootstrap phases are effectively free once the
issue workspace/branch already exist (the common case for a role
respawn). This does not cover the Claude Code harness's own
process-start cost (loading hooks.json, spawning the model process),
which is outside spawn.py and outside what `_BOOTSTRAP_TIMING`
instruments — the "boot 2s" figure in the issue's consult caveat likely
refers to that harness-level cost, not spawn.py's bootstrap phases,
which this measurement shows are near-zero.

## Bucket 2 — directive assembly (UserPromptSubmit, once per user turn)

`core`'s `hooks.json` wires several scripts to `UserPromptSubmit`.

derived: `time bash core/hooks/directive.sh` against a representative UserPromptSubmit payload

Measured: 3.999s wall. The other UserPromptSubmit scripts
(record-claim-shape-directive.sh, record-tiering-directive.sh,
test-tier-directive.sh, role-deviation-directive.sh) each measured
0.002s — directive.sh alone dwarfs that combined.

Root cause, `directive.sh:41`, a `gh auth status` precondition probe run
unconditionally on every prompt submit:

canonical: `grep -n "gh auth status" /home/jwjung/tokenmaxxxer-core/core/hooks/directive.sh`
```
41:  gh auth status >/dev/null 2>&1 || missing="${missing}
```

derived: `time gh auth status`

Measured: real 0m3.896s. The isolated timing of that one call matches
directive.sh's own measured total closely enough to attribute the
bucket's cost to this line.

This fires once per user prompt submission (not per tool call), so its
total session cost scales with turn count, not tool-call count.

## Bucket 3 — per-tool-call gate/hook overhead (PreToolUse, every Bash call)

`core`'s `hooks.json` wires a set of scripts to the catch-all `.*`
matcher; this repo's `on-the-record/hooks/hooks.json` wires a larger set
to the `Bash`-inclusive matchers. Both layers fire on every single Bash
tool call.

derived: timed each of the `core` `.*`-matched scripts against a representative Bash tool_input payload

Measured, sum 0.56s: board-gate 0.006, approval-gate 0.048, gh-guard
0.007, trailer-gate 0.049, record-fields-gate 0.067,
handbook-trigger-gate 0.033, proposal-shape-gate 0.050,
record-shape-gate 0.084, survey-order-gate 0.056, ordering-gate 0.042,
facet-keyword-gate 0.032, citation-gate 0.043, ordering-norm-gate 0.043.

derived: timed each of the repo-local `on-the-record/hooks/*.sh` Bash-matched scripts against the same payload

Measured: summed 1.598s.

Combined: ~2.15s of pure gate/hook wall-clock per Bash tool call,
dominated not by any single expensive script but by many separate
`bash`-subprocess spawns (each 25-85ms, consistent with shell/python
process-start cost rather than heavy logic — none of these scripts made
a network call in this trace). This is the bucket that scales worst:
unlike boot or directive assembly (paid once), this pays out on every
Bash invocation in the session. A single-phase session in this repo
commonly issues dozens of Bash calls, so the aggregate is plausibly the
largest or second-largest bucket in total session wall-clock, even
though no individual measurement here exceeds the test tail.

## Bucket 4 — test tail

derived: `python3 -m pytest -q -m "not slow"`

Measured: 2481 succeeded, 18 xfailed, 3 xsucceeded, wall 39.75s
pytest-reported / 40.35s real.

This measurement (39.75s) sits close to the issue's own consult caveat
figure ("fast tests 46s"), canonical: `gh issue view 2016` (Acceptance
provenance line) — under it, not over it, so this survey finds no
evidence of regression or of large remaining headroom in this bucket.

## Bucket 5 — Stop / record-PR ceremony (once per turn-end)

`core`'s `hooks.json` wires scripts to `Stop`; this repo wires more.

derived: timed all Stop-wired scripts against a representative Stop payload

Measured: stop-poll-rearm.sh 0.003s, stop-gate.sh 0.003s,
deviation-log-guard.sh 0.027s, role-test-claim-guard.sh 0.024s,
decision-queue-stopgate.sh 4.638s, report-framing-check.sh 0.004s,
product-capture-stopgate.sh 0.003s.

`decision-queue-stopgate.sh` dominates at 4.6s. Root cause,
`on-the-record/hooks/decision-queue-stopgate.sh:56`:

canonical: `grep -n "spawn.py flows --json" on-the-record/hooks/decision-queue-stopgate.sh`
```
56:FLOWS_JSON="$(python3 "$CHECKOUT/spawn.py" flows --json -C "$REPO" 2>/dev/null || true)"
```

`spawn.py flows --json` walks board/PR state via `gh`, a network round
trip — the same shape of cost as bucket 2's `gh auth status`, paid again
here. Whether Stop fires once per session or once per assistant turn is
flagged below under Open findings as not directly established by this
survey.

## Attribution summary (single representative session, ordered by total measured contribution)

| bucket | per-occurrence cost | frequency in a session | dominant driver |
|---|---|---|---|
| per-tool-call gate/hook overhead | ~2.15s | once per Bash call (commonly dozens) | many hook-script process spawns, none individually expensive |
| test tail | ~40s | once | pytest fast-suite collection+run, near floor per issue's own caveat |
| Stop/record-PR ceremony | ~4.6s | once per turn-end | `gh`-backed `spawn.py flows --json` inside decision-queue-stopgate.sh |
| directive assembly | ~4.0s | once per user prompt | `gh auth status` network probe inside directive.sh |
| boot (spawn.py bootstrap) | ~0.001s | once | negligible on a warm workspace |

## Top-2 buckets

1. **Test tail** (~40s/session, single occurrence) — the single largest
   per-occurrence number measured here (bucket 4 above). Per the
   issue's own consult caveat this bucket is already treated as
   near-floor; this measurement (39.75s vs the caveat's cited 46s) is
   consistent with that, not evidence of regression or of large
   remaining headroom.
2. **Per-tool-call gate/hook overhead** (~2.15s x N Bash calls) — not a
   fixed cost like the other buckets; it recurs on every single Bash
   tool call, so its session total is a multiple of a per-call figure
   that individually looks small next to the test tail but, summed
   across a typical session's dozens of Bash calls, is plausibly
   comparable to or larger than the test tail (see bucket 3 above for
   the per-call measurement). This bucket had no prior per-session
   wall-clock attribution — issue #2016's own stated empty state ("no
   per-bucket wall-clock attribution exists for a single session") —
   canonical: `gh issue view 2016` (empty state line).

Both secondary buckets (directive assembly ~4.0s, Stop ceremony ~4.6s)
are individually smaller than either top-2 bucket but share a distinct
root-cause pattern: each is a single, unconditional `gh` network round
trip (`gh auth status`, `spawn.py flows --json`) rather than many small
process spawns. That distinction matters for what a phase-2 fix would
look like for each — noted, not acted on, per phase-1 scope.

## Open findings

- Whether Stop fires once per session or once per assistant turn is not
  established by this survey (would require instrumenting a live
  multi-turn session with a Stop-event counter) — this changes the true
  session-total weight of bucket 5 (and, if turns exceed 1, of bucket 2
  as well) but not the per-occurrence cost measured in buckets 2 and 5
  above.
- The per-Bash-call hook-script spawns were timed standalone, outside
  the Claude Code harness's own IPC/spawn machinery for invoking each
  hook — real per-call cost inside a live harness session may differ
  from this floor measurement.

resolution path: a phase-2 session (after approval) would instrument a
live multi-turn session's Stop/UserPromptSubmit event counts directly
(e.g. by grepping a full session transcript for hook-invocation markers)
to convert these per-occurrence numbers into a true session total.
