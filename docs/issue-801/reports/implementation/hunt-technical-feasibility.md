---
proposal: docs/issue-801/proposals/technical-feasibility.md
---

# Hunt record — technical-feasibility

## before-landing — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: NO FINDING
Seed: on-the-record/hooks/poll-rearm.sh, directive.sh, stop-poll-rearm.sh, hooks.json, spawn.py poll_due()
cap_seconds: 60
tier: default
diff_stat_lines: ~90
started_at: 2026-08-11T19:20:00+09:00
ended_at: 2026-08-11T19:30:00+09:00
note: dispatcher-given path docs/issue-801/reports/hunt-technical-feasibility.md
  is rejected by board-gate for role 'implementation' (foreign record); wrote
  to docs/issue-801/reports/implementation/hunt-technical-feasibility.md instead.

Checked whether two near-simultaneous callers (UserPromptSubmit + Stop) of
poll_rearm_arm_if_due -> `spawn.py poll-due` -> `spawn.py:poll_due()` can both
observe "due" and double-spawn the watchdog. Ran poll_due() from 20 forked
processes concurrently against a shared poll_state.json:

```
python3 - <<'PY'
import spawn, tempfile, pathlib, multiprocessing as mp
d = pathlib.Path(tempfile.mkdtemp()); ps = d / "poll_state.json"
def worker(q): q.put(spawn.poll_due(poll_state=ps))
ctx = mp.get_context("fork"); q = ctx.Queue()
procs = [ctx.Process(target=worker, args=(q,)) for _ in range(20)]
[p.start() for p in procs]; [p.join() for p in procs]
print("True count:", sum(q.get() for _ in procs), "of", len(procs))
PY
```
Observed: `True count: 1 of 20` — the fcntl.flock-guarded read-check-stamp is
correctly atomic; only one caller ever gets "due" per 60s window regardless
of how many hook events fire close together. No double-spawn race here.

Also checked poll_rearm_resolve_checkout's unlocked self-clone fallback
(`git clone` into `$HOME/.claude/tokenmaxxxer/on-the-record` with no lock,
unlike poll_due's lock file). Reproduced two concurrent `git clone` calls
targeting the same not-yet-existing directory: the loser fails (`fatal:
could not create work tree dir 'own': File exists`, rc=128) but the script
only gates on `[ -f "$own/spawn.py" ]` after the clone attempt, not on the
clone's exit code, so the loser's post-check still finds spawn.py written
by the winner and returns success too. In the one case checked, both
callers ended up returning the same valid checkout path with no corruption
observed; a stricter race window (loser checks before winner's clone
finishes writing objects) would just make that hook invocation return 1
(skip arming that turn) which self-heals on the next turn per the file's
own documented "best-effort" framing — could not produce an invisible,
non-self-healing wrong state within the cap.
