---
proposal: (build-now bypass, no phase-1 proposal file — issue #2592 spawn.py --role -> --session retirement)
---

# Hunt record — spawn-role-to-session-flag-retirement

## before-landing — stance 2: assume this guard goes silent when its own input is malformed — make it go silent

Verdict: NO FINDING
Seed: spawn.py's pre-parse `--role` retirement guard added right before `a = ap.parse_args()`
  (`if any(tok == "--role" or tok.startswith("--role=") for tok in sys.argv[1:]): sys.exit(...)`,
  spawn.py:1771-1772); diff at /tmp/otr-2592-diff.txt (spawn.py, events.py, directive_assembly.py,
  pipeline.py, watchdog.py, on-the-record/directive/{merge-gates,spawn-and-board}.md)
canonical: spawn.py:1771-1772 (guard source, read directly); local `python3 spawn.py ...` runs
  quoted below; `grep -n add_argument spawn.py` and `grep -rn "spawn.py" --include=*.py
  --include=*.sh . | grep -- "--role"` run against this checkout
cap_seconds: 120
tier: size:21-200-lines
diff_stat_lines: 239
started_at: 2026-08-27T00:00:00Z
ended_at: 2026-08-27T00:20:00Z

Tried and ruled out (each still exits non-zero, none is silent):
- `--role` after a `--` separator: guard still fires (it scans raw tokens, ignoring `--`, so it is
  over-eager here, not silent — the opposite of the stance).
  acceptance: `python3 spawn.py -C . watch --issue 5 -- --role foo` — result:
  ```
  spawn.py: --role 는 은퇴했다(이슈 #2592) — 세션을 고르는 건 역할이 아니라 슬러그다. 대신 --session <slug> 를 써라
  exit=1
  ```
- `--role=` / `--role=foo` (with `=`): caught by `tok.startswith("--role=")`.
  acceptance: `python3 spawn.py -C . watch --issue 5 --role=` — result: same guard message, exit=1.
- `--rol` (argparse abbreviation/prefix): guard's exact-match misses it, but since no remaining
  flag starts with `--rol` (`grep -n add_argument spawn.py` shows only `--rearm` and
  `--remediation-merged` among `--r*` flags), argparse itself rejects it with
  `error: unrecognized arguments: --rol foo`, exit 2.
  acceptance: `python3 spawn.py -C . watch --issue 5 --rol foo` — result:
  ```
  usage: spawn.py [-h] [-C CWD] ... [role] [task] [consult_question] [panel_question]
  spawn.py: error: unrecognized arguments: --rol foo
  exit=2
  ```
- `--ROLE` (case variant): same as above — guard misses it, argparse still rejects it.
  acceptance: `python3 spawn.py -C . watch --issue 5 --ROLE foo` — result:
  ```
  spawn.py: error: unrecognized arguments: --ROLE foo
  exit=2
  ```
- grepped the whole repo for any remaining caller that still builds a spawn.py
  watch/await-approval/recut-corrupted invocation with literal `--role` — none found outside the
  guard's own message string in spawn.py:1772; all Popen argv lists in spawn.py/events.py were
  updated to `--session` in this diff (verified against /tmp/otr-2592-diff.txt).
  acceptance: `grep -rn "spawn.py" --include=*.py --include=*.sh . 2>/dev/null | grep -- "--role"`
  — result: only `spawn.py:1772:        sys.exit("spawn.py: --role 는 은퇴했다...`.
- checked for a second `main(argv)`-style entry point or a leftover `watch_role`/`a.watch_role`
  reference that might read parsed args via a path the guard doesn't cover — `main()` (spawn.py:1590)
  takes no argv parameter and both the guard and `ap.parse_args()` read `sys.argv[1:]` consistently.
  acceptance: `grep -rn watch_role --include=*.py .` — result: no output (no match).

In every bypass case argparse's own unrecognized-arguments handling still produces a loud,
non-zero-exit failure (just without the issue #2592 redirect message) — never a silent
success-shaped acceptance of `--role`. Could not produce a reproduction where malformed input
makes the guard's absence look like success, so per the stance's own rule (no repro = no
finding) this is a miss.
