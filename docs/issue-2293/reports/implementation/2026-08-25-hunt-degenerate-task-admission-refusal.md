---
proposal: docs/issue-2293/proposals/ (build-now, no phase-1 proposal file — CORE_BUILD_NOW=1, contract v3 s19a)
---

# Hunt record — degenerate-task-admission-refusal

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `_admission_check_degenerate_task`'s regex `^#?\d+$` does not match a leading-minus numeric task (e.g. `-538`), so a bare issue-number-shaped task with no `--issue` still reaches a live spawn when the number is preceded by `-`, because argparse's negative-number heuristic accepts it as the ordinary `task` positional (not as an unrecognized option).
Kind: silent-failure
Seed: pipeline.py `_admission_check_degenerate_task` / `_DEGENERATE_TASK_RE = re.compile(r"^#?\d+$")`; spawn.py ADMISSION_CHECKS row "degenerate-task"; the incident being closed is `spawn.py implementation 538` (typo for `--issue 538`).
cap_seconds: 180
tier: size:>200-lines
diff_stat_lines: 341 insertions across 6 files (pipeline.py, spawn.py, watchdog.py, tests/test_admission_checklist.py, tests/test_spawn_gate_wiring.py, docs/issue-2293/reports/implementation.md)
started_at: 2026-08-25T00:00:00Z
ended_at: 2026-08-25T00:20:00Z

### Reproduce
```
$ python3 -c "
import sys; sys.path.insert(0, '.')
import pipeline
ctx = {'issue': None, 'task': '-538', 'force_adhoc_task': False, 'role': 'implementation'}
print(pipeline._admission_check_degenerate_task(ctx))
"
```
And confirmed end-to-end through the real CLI (this actually spawned a live nested agent session in this working tree — bootstrap/session log/board-gate checks all ran, cost $0.06 per the printed summary):
```
$ python3 spawn.py implementation -538
```

### Observed
The direct predicate call prints nothing (no did-you-mean refusal) and returns `True` (admitted) for `task='-538', issue=None`, versus `False` (refused, with the did-you-mean message) for `task='538', issue=None` — same digits, same "meant `--issue` but typed a bare number" shape, different admission outcome. The live CLI run produced:
```
[implementation] directive composition: total=4B (base-task=4B)
[implementation] 플러그인 0개, 룰북 skill-repo(...), core 플러그인 core, terse, freelunch, scout, warrant, ...
[implementation] bootstrap_timing admission=1.241 ...
[implementation] 라이브 로그: .../runs/last-session.log
...
[implementation] progressed, 보드 변화 1건, 비용 $0.06
```
i.e. a real live agent was spawned with `task="-538"` and `issue=None`, no admission refusal at all — argparse accepts `-538` as the ordinary `task` positional (its "looks like a negative number and no option strings look like negative numbers" special case), so it never even reaches the flag-parsing ambiguity the CLI author might assume forces `--issue` typos into a form the regex catches.

### Expected
A task that is exactly a (possibly-signed) issue-number-shaped token with no `--issue` given should be refused the same way `538` and `#538` are — the whole point of item 6 is that a numeral standing alone as the task is almost certainly a missing/mistyped `--issue`, and a minus sign in front of the number does not make that any less true (nor does it make the task any more likely to be genuine "adhoc" free text). As written, `^#?\d+$` only catches the unsigned/hash-prefixed forms, leaving the negative-number form of the exact same mistake to reach a live spawn silently, which is the same silent-failure class the incident (`spawn.py implementation 538`) was written to close.
