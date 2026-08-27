---
proposal: none (build-now bypass, CORE_BUILD_NOW=1)
---

# Hunt record — spawn-attempt-supersession

## before-landing — stance 1: assume the gate/check just touched is bypassable — find the bypass

Verdict: FINDING — `spawn._attempt_superseded()` trusts the untrusted, attacker/bug-appendable `spawn-attempts.jsonl` ledger's own `outcome: "session-log"` claim with zero re-verification, letting a forged (or optimistically-mis-recorded) later "success" entry for the same (issue, role) permanently silence a halt whose blocking condition is independently, verifiably still true.
Kind: composition
Seed: uncommitted working-tree diff at /tmp/otr_2511_diff.txt (roster.py, spawn.py, test/test_spawn_attempt_staleness.py — adds `spawn._attempt_superseded()` and wires it into `roster.spawn_attempt_sweep()` via `condition_cleared or superseded`)
cap_seconds: 180
tier: size:diff>200 lines (240 across 3 files)
diff_stat_lines: 240
started_at: 2026-08-27T04:40:00Z
ended_at: 2026-08-27T04:50:00Z

### Reproduce
```python
import json, tempfile, sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, ".")
import spawn, roster

td = tempfile.TemporaryDirectory()
attempts_path = Path(td.name) / "spawn-attempts.jsonl"

def append(ev):
    with attempts_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(ev, ensure_ascii=False) + "\n")

patches = [
    mock.patch.object(spawn, "SPAWN_ATTEMPTS_PATH", attempts_path),
    mock.patch.object(spawn, "ledger_write", lambda ev: None),
    mock.patch.object(spawn, "ledger_check_and_stamp", lambda *a, **k: True),
]
for p in patches:
    p.start()

# Real halted attempt: cwd points at a directory that genuinely, right
# now, is not a git repo (a real, still-unfixed cwd-invalid bug).
real_bad_cwd = "/definitely/not/a/real/checkout/anywhere"
assert not Path(real_bad_cwd).is_dir()

halted_ts = 1000.0
append({"event": "spawn_attempt",
        "attempt_id": "9001:victim-role-aaaa1111:111:1000",
        "issue": 9001, "role": "victim-role-aaaa1111",
        "pid": 111, "cwd": real_bad_cwd, "ts": halted_ts})
append({"event": "spawn_attempt_outcome",
        "attempt_id": "9001:victim-role-aaaa1111:111:1000",
        "outcome": "halted",
        "detail": f"-C 가 존재하지 않는 디렉터리다: {real_bad_cwd}\n  cwd 는 레포 루트를 가리켜야 한다.",
        "ts": halted_ts})

# Confirm the class re-check genuinely says "still broken" right now.
print("class-recheck says condition cleared:",
      spawn._halt_condition_cleared("cwd-invalid", {"cwd": real_bad_cwd}, ""))

# A forged (or optimistically mis-recorded) later "success" for the
# identical (issue, role) subject -- appended by anyone/anything with
# plain filesystem write access to the jsonl ledger (the same access
# already required to write the real spawn_attempt/outcome lines this
# feature reads). No real spawn ran, no workspace was ever created; the
# "session log" path below does not exist on disk and is never checked.
fake_session_log = "/tmp/this-session-log-does-not-exist-xyz.log"
assert not Path(fake_session_log).exists()
append({"event": "spawn_attempt",
        "attempt_id": "9001:victim-role-aaaa1111:999:2000",
        "issue": 9001, "role": "victim-role-aaaa1111",
        "pid": 999, "cwd": "/irrelevant", "ts": halted_ts + 1000})
append({"event": "spawn_attempt_outcome",
        "attempt_id": "9001:victim-role-aaaa1111:999:2000",
        "outcome": "session-log",
        "detail": fake_session_log,
        "ts": halted_ts + 1000})

with mock.patch("builtins.print") as mocked_print:
    count = roster.spawn_attempt_sweep(d_all={})

printed = "\n".join(str(c.args[0]) for c in mocked_print.call_args_list)
print("---- sweep output ----")
print(printed)
print("live halts reported this tick:", count)

for p in patches:
    p.stop()
td.cleanup()
```

Run against the working tree:
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2511-silent-failure-audit+observability-explorability-fac0f402
python3 /tmp/repro_supersession.py   # the script above
```

### Observed
```
class-recheck says condition cleared: False
---- sweep output ----
[spawn-attempt] issue-9001/victim-role-aaaa1111: halt RESOLVED at 2026-08-27T04:46:30Z (class=cwd-invalid, resolved_via=superseded, originally attempted at 1970-01-01T00:16:40Z) — no longer a live halt: -C 가 존재하지 않는 디렉터리다: /definitely/not/a/real/checkout/anywhere
live halts reported this tick: 0
```
The halt is marked `spawn_attempt_resolved` (`resolved_via=superseded`), the attempt_id is added to the durable `resolved` set (per the existing #2511/#2594 dedup contract — "already surfaced as resolved once — never replayed again"), and `spawn_attempt_sweep()` reports zero live halts, even though `_halt_condition_cleared("cwd-invalid", ...)` independently, correctly says the condition is still true (the directory still doesn't exist) and the claimed session-log path was never created.

### Expected
`_attempt_superseded()` should not treat `outcome == "session-log"` as sufficient on its own — the same file that records the halt (`reason`, `cwd`, etc., already untrusted enough that `_halt_condition_cleared()` deliberately re-derives every class from live filesystem/git state rather than trusting recorded fields) also records the "later success," yet the new function is the one path in this whole mechanism that takes a recorded claim at face value instead of re-deriving it (e.g. checking that the recorded session-log `detail` path actually exists, or that a roster/workspace entry for that (issue, role) was actually created). This contradicts the design invariant `_halt_condition_cleared()`'s own docstring states as the reason #2511 exists at all ("모든 클래스가 그 조건을 다시 확인한다... 시간이 지난다고 저절로 참이 되는 술어가 아니다" — no class is allowed to resolve on the strength of a recorded claim rather than a live re-check), and lets the OR-composition of `condition_cleared or superseded` silently override a verified-still-broken class-recheck with an unverified ledger entry.
