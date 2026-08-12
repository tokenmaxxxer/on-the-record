---
kind: current-state-survey
subject: issue-1037
code_under_review:
- docs/specs/northpole.md
- docs/issue-973/reports/product-discovery/current-state.md
- docs/issue-1024/reports/implementation.md
- docs/issue-1006/reports/implementation.md
- docs/issue-776/reports/execution-observation.md
- docs/issue-896/reports/product-discovery/survey.md
- docs/issue-927/reports/implementation/survey.md
---

# Gap register — adversarial northpole audit (issue #1037)

## Background / context

canonical: docs/specs/northpole.md, read this session — claims every one of the 7 north-pole requirements is served by at least one named mechanism, none marked bare `GAP`.

This audit tries to refute that "served" claim per requirement against repo actuals, per issue #1037's 6 named suspects plus a search for further gaps.

## Method

For each named suspect, located the most recent repo record addressing it and read what it actually verified, then checked one additional angle per requirement beyond the named suspects.

## Gap register

### Requirement #1 — Orchestration to completion: holds once, single-run

canonical: docs/issue-776/reports/execution-observation.md's own step-10 evaluate_all transcript, that verdict record's live run, read this session — reads `orchestration_to_completion: PASS`.

canonical: same file's "What was done" steps 1-8 transcript, read this session — a fresh `claude -p` session (run #7, commit `2a8b878`) filed an issue, spawned `implementation`, and merged PR #8 in a real separate GitHub repo (`JiwonJung94/northpole-harness-fixture`).

canonical: same file's step-9 independent-rebuild transcript, that record's own fresh `git clone` + build/test run, read this session:
```
3 passed in 0.02s
0.1.0
cli_exit=0
```

Runs #1-#6 needed 6 prior iterations before this result first appeared — canonical: same file's "Trajectory verdict" section transcript, read this session, contrasting run #6's full permission-denial list against run #7's empty one.

derived: `ls docs/issue-776/reports/execution-observation/` — highest file is `run7`-prefixed, no `run8` exists yet.

**Severity:** Medium — one successful run so far, no repeat-run transcript exists yet.
**Proposed closing issue:** re-run `harness/driver.py`'s steady-state path at least twice more against fresh fixture-target copies.

### Requirement #2 — Full record-ability: not independently refuted here

This survey itself was written under `record-claim-guard.sh`'s citation enforcement (the tool-error rejections this session received while drafting earlier versions are the live evidence). No refuting evidence located beyond requirement #5's finding below.

### Requirement #3 — Real-wired verification (intake gate): refuted

canonical: docs/issue-1024/reports/implementation.md's own "Verification performed" transcript, read this session:
```
$ python3 gates/test_requirement_intake_consult.py
4/4 passed
$ python3 -m pytest tests/test_spawn.py -k intake -v
3 passed, 465 deselected
```

Both are unit tests exercising the gate module directly, not a real requirement intake in a live session — matches the issue's named suspect verbatim.

derived: `grep -rl requirement_intake_consult docs --include=*.md`, run this session — matches confined to `docs/issue-1024/**` and `docs/specs/enforcement-boundary.md`; none shows the gate firing against an actual operator-stated requirement in a live session.

**Severity:** Medium — gate logic unit-tested; live trigger path unverified.
**Proposed closing issue:** capture one real intake transcript (same harness/driver.py pattern as issue #776) where an operator states a requirement and the gate visibly fires.

### Requirement #4 — Autonomous completion + human-legible reporting: holds once, same caveat as #1

canonical: docs/issue-776/reports/execution-observation.md's own step-10 evaluate_all transcript, that same run's live result, read this session — reads `autonomous_completion_reporting: PASS`, on the same single-run basis as req#1 above; no run #8 transcript exists yet to confirm a repeat.

**Severity:** Medium — see req#1's proposed closing issue (same fix covers both).

### Requirement #5 — Problems are not pushed back to the human: refuted

canonical: docs/issue-973/reports/product-discovery/current-state.md's own grep transcript, read this session — `grep -rln "SendMessage\|ListAgents" spawn.py gates/ roles/ docs/specs/` returns zero hits.

Same survey cites `spawn.py:4095-4162` (`consult_cmd`): exactly one bounded `subprocess.run` per call, one caller, one headless session, no second session, no exchange, no rebuttal. `docs/specs/northpole.md`'s req#5 traceability cites this same `consult_cmd()` as serving req#5 — matches the issue's named suspect verbatim ("panel 2-session SendMessage round-trip never measured live"): the primitive is not merely unmeasured, it is unadopted anywhere in this repo's own machinery.

**Severity:** High — the requirement's literal text names live multi-agent discussion; the cited mechanism is structurally sequential/single-session.
**Proposed closing issue:** issue #973 already exists and targets this exact gap; this audit corroborates it independently.

### Requirement #6 — Condensed requirement management: not independently refuted here

derived: `ls docs/specs/requirements.md docs/specs/northpole.md`, run this session — both exist; no counter-evidence located.

### Requirement #7 — Inviolable constraint (default-on, plugin-only): refuted

canonical: docs/issue-1006/reports/implementation.md's own frontmatter, read this session, states `verdict: pending`, `loop_state: coding` — the operator-experience layer (issue #1006, matching the issue's named suspect "operator-experience blocks never observed in a pristine session") is still mid-build.

canonical: docs/issue-896/reports/product-discovery/survey.md's own "Verified facts" transcript, read this session:
```
$ grep -l board_condition roles/specs/*.spec.json | wc -l
43
$ grep -rln board_condition gates/ hooks/
gates/role_spec_shape.py (shape check only, and its test file)
```

All 43 roles carry a machine-readable `board_condition`, but no gate or hook evaluates it against live diff/branch state — matches the issue's named suspect verbatim ("43-role utilization mostly unproven"): a role whose trigger condition holds can silently not run, with no mechanical signal that it should have.

canonical: docs/issue-927/reports/implementation/survey.md's own "Finding 6" transcript, read this session — `grep -n "stall_limit\|last_progress" tests/test_spawn.py` returns no match; every existing stall test mocks the stall rather than driving a real detached subprocess past the boundary — adjacent to but not the same as the issue's named "watcher-dead stale-pid false warnings every tick" suspect.

unverifiable: watcher-dead stale-pid false-warning rate — no record located in this audit's time budget measuring a live false-positive rate in either direction; nearest evidence is the absence, above, of any live-fire stall-survival test, leaving both true- and false-warning behavior unmeasured live.

**Severity:** High for the role-utilization signal (a requirement claiming "everything works by default" has no live enforcement of one of its own named mechanisms). Medium for the operator-experience layer, still mid-build with no proven default either way.
**Proposed closing issue:** issue #896 and issue #1006 already exist and target these two gaps directly; this audit corroborates both independently. A new issue is warranted only for the watcher-dead false-warning rate, since no existing issue measures it live.

## Summary table

| Req | Claim | Status | Severity | Evidence |
|---|---|---|---|---|
| 1 | Orchestration to completion | holds once, single-run | Medium | issue-776 execution-observation.md |
| 2 | Full record-ability | not independently refuted | n/a | this report itself |
| 3 | Real-wired verification (intake gate) | refuted | Medium | issue-1024 implementation.md |
| 4 | Autonomous completion + reporting | holds once, single-run | Medium | issue-776 execution-observation.md |
| 5 | Problems not pushed to human (panel judgment) | refuted | High | issue-973 current-state.md |
| 6 | Condensed requirement management | not independently refuted | n/a | docs/specs/*.md existence |
| 7 | Inviolable default-on constraint | refuted | High | issue-896 survey.md, issue-1006 implementation.md |

## Beyond the named suspects

The single-run durability gap on req#1/#4, and the role-coverage enforcement gap under req#7 traced to `gates/role_spec_shape.py`'s shape-only check, are findings this session derived independently rather than restating a named suspect, though both overlap thematically with the issue's "no end-to-end run" and "43-role utilization" suspects.

## What did not work

None.
