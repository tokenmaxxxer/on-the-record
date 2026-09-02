#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3120, layer 2.

Exists so the survival requirement can be stated as a plain `check:` line
(`python3 gates/probe_heartbeat_survives_head_change.py`) instead of a
shell one-liner, mirroring gates/probe_drift_repo_leak.py's convention.

This is the CONSUMER condition, not "this session survives": a session
doing no plugin development at all -- an ordinary `arm_root` with no git
repo of its own, no on-the-record work in flight -- must see its Monitor
heartbeat keep ticking across a HEAD change in the on-the-record checkout
it is armed against. That checkout moving is entirely outside the
consumer's control (a `git pull`, a `claude plugin marketplace update`,
or any merge), so the survival requirement cannot depend on the consumer
doing anything.

`on-the-record/monitors/poll-heartbeat.sh` runs `spawn.py watchdog
--auto-respawn` on every due tick, in the FOREGROUND, as a brand-new
subprocess. `watchdog_freshness_check` (watchdog.py:1867) returns
`WATCHDOG_STALE_CODE_SENTINEL = 95` (spawn.py:677) when it finds the
checkout HEAD moved during that invocation. Before issue #3120's fix,
poll-heartbeat.sh's tick loop has no restart mechanism at all for that
sentinel -- the process keeps running unmodified, the "재기동 필요"
(restart required) instruction is delivered and then nothing acts on it.
The fix (layer 2) makes the tick `exec` itself back into the SAME pid the
moment it classifies rc=95, so the loop keeps ticking with freshly
re-captured code and a freshly re-captured startup_head, self-healing
with no external re-arm.

This probe drives the real, unmodified `on-the-record/monitors/
poll-heartbeat.sh` for a BOUNDED, multi-tick run (`POLL_HEARTBEAT_MAX_TICKS`)
against a fake `spawn.py` whose `watchdog` role deterministically returns
95 on exactly its first invocation (simulating "HEAD moved during the
watchdog's first run") and 0 on every invocation after. The exec target
(`${CHECKOUT}/on-the-record/monitors/poll-heartbeat.sh`) is a real copy of
the ACTUAL script under test, so a genuine `exec` -- not a simulated one
-- either succeeds or does not.

Why this distinguishes fixed-from-broken mechanically, not by timing: an
`exec` restart resets the tick loop's own `tick` counter to 0 in the new
process image (a brand-new invocation of the script), because the whole
point of `exec` is that nothing about the running program's state
survives except the pid and open file descriptors. So with
`POLL_HEARTBEAT_MAX_TICKS=N`:
  - unfixed: the SAME process counts every tick itself, top to bottom,
    and stops after exactly N due ticks (N watchdog invocations total).
  - fixed: tick 1 (the stale one) triggers a restart before the tick
    counter ever increments for that iteration; the new process image
    then runs its OWN bounded N ticks from a fresh tick=0 -- so the
    process makes 1 (stale, pre-restart) + N (post-restart) = N+1
    watchdog invocations in total, and the run still terminates cleanly
    (bounded by the post-restart image's own counter), proving the loop
    kept ticking on the far side of the restart rather than merely not
    crashing.

The probe checks the watchdog-invocation marker count is N+1 (proves the
restart actually happened AND the process kept ticking afterward, not
just N, which is what an unpatched loop that never restarts also
produces), that the stale-code classification line reached stdout on the
first tick, and that the whole bounded run still exits 0 (no hang, no
crash) -- the "still ticking" bar the issue's acceptance text sets.

Run as `python3 gates/probe_heartbeat_survives_head_change.py` from the
repo root, no arguments, no real git HEAD movement needed (the sentinel is
driven directly, mirroring the existing FAKE_SPAWN_PY test-double
convention on-the-record/monitors/test_poll_heartbeat.py already uses for
this exact script), no network. Prints `ok` and exits 0 on success; prints
a message to stderr and exits non-zero otherwise.
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLL_HEARTBEAT = ROOT / "on-the-record" / "monitors" / "poll-heartbeat.sh"

N_POST_RESTART_TICKS = 2

FAKE_SPAWN_PY = """#!/usr/bin/env python3
import os, sys

if sys.argv[1:2] == ["poll-due"]:
    sys.exit(0)

if sys.argv[1:2] == ["watchdog"]:
    marker = os.environ["FAKE_SPAWN_MARKER"]
    with open(marker, "a", encoding="utf-8") as f:
        f.write("watchdog-ran\\n")
    n_prior = 0
    if os.path.exists(marker):
        with open(marker, encoding="utf-8") as f:
            n_prior = sum(1 for _ in f)
    if n_prior == 1:
        # first-ever invocation of this process's on-disk checkout:
        # simulate "HEAD moved while this watchdog run was in flight".
        print("[watchdog] \\ucf54\\ub4dc-\\uc2e0\\uc120\\ub3c4: \\uccb4\\ud06c\\uc544\\uc6c3 HEAD \\uac00 \\ubc14\\ub018\\ub2e4 "
              "(\\uc2dc\\uc791=aaaaaaaaaaaa \\ud604\\uc7ac=bbbbbbbbbbbb) \\u2014 \\uc7ac\\uae30\\ub3d9 \\ud544\\uc694")
        sys.exit(95)
    sys.exit(0)

sys.exit(0)
"""


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = tmp / "checkout"
        checkout.mkdir()
        (checkout / "spawn.py").write_text(FAKE_SPAWN_PY, encoding="utf-8")

        # Real copy of the actual script under test at the real
        # CHECKOUT-relative path poll-heartbeat.sh execs into on rc=95 --
        # so a genuine `exec` either succeeds or does not; nothing here
        # simulates the restart itself.
        exec_target = checkout / "on-the-record" / "monitors" / "poll-heartbeat.sh"
        exec_target.parent.mkdir(parents=True)
        shutil.copyfile(POLL_HEARTBEAT, exec_target)
        exec_target.chmod(exec_target.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        # poll_heartbeat_delta.py is loaded by relative path from the
        # running script's own SCRIPT_DIR, which after the exec is the
        # copy's directory, not the real repo's -- copy its sibling too.
        shutil.copyfile(
            ROOT / "on-the-record" / "monitors" / "poll_heartbeat_delta.py",
            exec_target.parent / "poll_heartbeat_delta.py",
        )
        # poll-heartbeat.sh sources ../hooks/poll-rearm.sh relative to its
        # own SCRIPT_DIR -- needed post-restart too.
        hooks_dir = checkout / "on-the-record" / "hooks"
        hooks_dir.mkdir(parents=True)
        shutil.copyfile(
            ROOT / "on-the-record" / "hooks" / "poll-rearm.sh",
            hooks_dir / "poll-rearm.sh",
        )

        marker = tmp / "marker.log"
        home = tmp / "home"
        home.mkdir()
        # arm_root: an ordinary, non-git, non-board directory -- the
        # "session doing no plugin development" the acceptance text names,
        # not this checkout and not a board repo.
        arm_root = tmp / "consumer_project"
        arm_root.mkdir()

        env = dict(os.environ)
        env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
        env["FAKE_SPAWN_MARKER"] = str(marker)
        env["POLL_HEARTBEAT_MAX_TICKS"] = str(N_POST_RESTART_TICKS)
        env["POLL_HEARTBEAT_SLEEP_SECONDS"] = "0"
        env["FAKE_POLL_DUE"] = "1"
        env["HOME"] = str(home)
        env["ORCHESTRATE_OFF"] = ""
        env["OTR_MONITOR_OFF"] = ""
        env.pop("CLAUDE_SKILL", None)

        r = subprocess.run(
            ["bash", str(POLL_HEARTBEAT)], input="", capture_output=True,
            text=True, env=env, timeout=20, cwd=str(arm_root),
        )

        if r.returncode != 0:
            _fail(
                f"poll-heartbeat.sh did not terminate cleanly after a "
                f"HEAD-change tick -- the consumer's Monitor loop must "
                f"still exit 0 on its own bound, not hang or crash. "
                f"rc={r.returncode} stdout={r.stdout!r} stderr={r.stderr!r}"
            )

        if "재기동 필요" not in r.stdout:
            _fail(f"the stale-code tick's own message never reached "
                  f"stdout: {r.stdout!r}")

        if "[watchdog-stale-code]" not in r.stdout:
            _fail(f"rc=95 was not classified on the tick that hit it: "
                  f"{r.stdout!r}")

        n_watchdog_runs = 0
        if marker.exists():
            n_watchdog_runs = sum(
                1 for line in marker.read_text(encoding="utf-8").splitlines()
                if line.strip() == "watchdog-ran"
            )

        expected = 1 + N_POST_RESTART_TICKS
        if n_watchdog_runs < expected:
            _fail(
                f"watchdog ran only {n_watchdog_runs} time(s); expected "
                f"{expected} (1 stale tick + {N_POST_RESTART_TICKS} "
                f"post-restart ticks from a FRESH tick counter). A count "
                f"of exactly {N_POST_RESTART_TICKS} (not {expected}) means "
                f"the loop's own tick counter never reset -- no restart "
                f"happened, and the consumer's Monitor is still running "
                f"the same stale-code-detecting process forever with "
                f"nothing having self-healed (issue #3120's defect)."
            )

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
