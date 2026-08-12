code_under_review:
- on-the-record/hooks/hooks.json
- on-the-record/hooks/merge-allow-gate.sh
- on-the-record/hooks/live-fire-claim-real-run-guard.sh
- on-the-record/hooks/acceptance-command-real-run-guard.sh
- gates/reexecution_gate.py
- gates/landing_readiness.py
- gates/closure_sweep.py
- gates/roles_due.py
- gates/accumulation.py
- on-the-record/monitors/monitors.json

## What each named substrate piece actually is

**#892 executed-live gate** is two hooks, not one file.
canonical: `grep -rl "#892" on-the-record/hooks/*.sh` output (read
directly this turn) — matched `live-fire-claim-real-run-guard.sh` and
`acceptance-command-real-run-guard.sh`, both under `PreToolUse`. They
fire at commit time on the committing session's own claim language,
blocking a false execution assertion. Neither has any post-landing
branch — canonical: on-the-record/hooks/live-fire-claim-real-run-guard.sh
and on-the-record/hooks/acceptance-command-real-run-guard.sh (both read
directly this turn), neither file references `gh pr merge`.

**`gates/reexecution_gate.py`** is a *pull* mechanism: some caller must
choose to invoke `reexecution_gate.py --issue --role --sha --command`,
which writes a verdict to `.reexecution/<issue>-<role>.json`.
canonical: gates/landing_readiness.py:56-70 (`reexecution_blocking_cause`,
read directly this turn) — that function only *reads* the verdict file
and turns a failing verdict into a `BLOCKED_ON_SCOPE` cause; nothing in
it or its visible callers writes the verdict automatically off a
landing event.

**`gates/landing_readiness.py`**'s `classify` is a pure function with
no side effects. canonical: gates/landing_readiness.py:29-52 (read
directly this turn). `blocking_causes` is already a list of
`{reason, scope}` entries — a shape a new obligation cause could join
without changing `classify`'s signature.

**`gates/closure_sweep.py`**'s `classify` is board-wide and read-only.
canonical: gates/closure_sweep.py:41-55 (read directly this turn) — it
reports `OPEN_PR_ON_CLOSED_ISSUE` / `MERGED_DELIVERY_ISSUE_OPEN`, never
writes anything, and runs on demand (`--post`), not off a landing
event.

**`gates/roles_due.py`** reads `roles/specs/*.spec.json`'s
`use_when.trigger` against the diff'd files of the current branch.
canonical: gates/roles_due.py:1-24 (module docstring + imports, read
directly this turn) — diff-shaped, not landing-event-shaped: it answers
which role's board record is missing given changed files, never what a
just-landed PR still owes.

**Monitor/watchdog** (`on-the-record/monitors/monitors.json`) tracks
session liveness/idleness; it carries no verification-obligation logic.
canonical: on-the-record/monitors/monitors.json (read directly this
turn) — its keys are session-tracking fields, none reference PRs,
issues, or verdicts.

**`hooks.json`'s `PostToolUse`** array has one entry today.
canonical: on-the-record/hooks/hooks.json, key `hooks.PostToolUse`
(read directly this turn via `python3 -c "json.load(...)"`) — matcher
`Write|Edit|MultiEdit|Bash` running `retry-loop-bound.sh post`. Because
the matcher already covers `Bash`, this hook point already fires after
every `gh pr merge` call; no listener is registered there today.

**`gates/accumulation.py`** is precedent for a "presence-only" gate
(checks a field exists, never grades its content).
canonical: gates/accumulation.py:1-24 (module docstring, read directly
this turn).

**Warrant-hunter** is a subagent dispatch (the `Agent` tool, per the
warrant directive), not a repo-committed `gates/*.py` module.
canonical: `find . -iname "warrant-hunter*" -not -path
"*/node_modules/*"` output (read directly this turn) — every hit
resolves under `docs/issue-170/_assets/rulebook-skeleton/**` or
`docs/issue-167/_assets/rulebook-skeleton/**` fixture-asset trees, not
a live agent-definition path in this checkout; the actual subagent
type resolves through the harness's agent registry outside this repo's
files. Per the warrant directive text itself, it dispatches at
proposal-write and before-landing transitions of the *dispatching*
session — a prompt-driven, optional step, not a mechanical gate a
session cannot skip past, and it is not scoped to a landed PR's later
runtime/test behavior.

## The actual gap

canonical: `grep -rl "gh pr merge" on-the-record/hooks/*.sh` output
(read directly this turn) — the only match is
`on-the-record/hooks/merge-allow-gate.sh`, a `PreToolUse` allow-gate
that decides whether a merge may proceed; it has no post-landing
branch. Combined with the reads above, no hook or gate anywhere in
this tree runs automatically after a `gh pr merge` call returns
success — every piece that could compose into a land→verify→refile→
continue loop (`reexecution_gate.py`, `landing_readiness.py`,
`closure_sweep.py`, `roles_due.py`) is invoked on demand by some other
session's choice, never by the landing event itself.

## Constraint from the ask (req#7: hooks/directive text/gates only)

The issue body rules out CI and explicit skill invocation. That leaves
the `PostToolUse` hook point (matching `gh pr merge` success the way
`merge-allow-gate.sh` matches it for `PreToolUse`), an obligation
artifact in the shape `reexecution_gate.py` already established, and a
`landing_readiness.py`/`closure_sweep.py`-style pure classifier so the
obligation is visible to any later gate or orchestrator turn without
re-deriving it.
