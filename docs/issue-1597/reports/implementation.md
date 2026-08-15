---
code_under_review:
  - gates/patrol_wiring.py
  - gates/test_patrol_wiring.py
  - on-the-record/commands/run.md
type: feature
breaking: false
# canonical: python3 -m pytest gates/test_patrol_wiring.py gates/test_patrol_trigger.py gates/test_patrol_board.py -q (this session's own run, fenced below)
verdict: pass
loop_state: landed
---

derived: `python3 -m pytest gates/test_patrol_wiring.py gates/test_patrol_trigger.py gates/test_patrol_board.py -q 2>&1 | tail -3`
canonical: pasted pytest output below, this session's own run, after code commit 60ac6b0c.
```
...........................                                              [100%]
27 passed in 1.05s
```

# Implementation record: issue #1597 E1 (post-merge patrol wiring)

## What was done

canonical: docs/issue-1597/proposals/patrol-wiring-e1.md, read this
session — its plan section is what this record implements.

Built `gates/patrol_wiring.py`:

- Kill-switch check (`.on-the-record/patrol-disabled`) as the first
  statement of the entry function `run()`, via a shared
  `kill_switch_active` helper for a future E2 entry point to import.
- `patrol_trigger.should_fire(event)` gates the rest of the call chain.
- Up to 3 roles' worth of real judge hits: roles walked from
  `roles/*.json`, `judge_cmd` called per candidate (reusing the
  prefilter already inside `judge_cmd`, no second selector);
  `patrol_board.run_patrol_board` called only for roles whose
  `judge_cmd` call returned a non-empty `enqueued` list.
- `judge_cmd` is injectable (`run(repo_root, merge_sha, judge_cmd=None)`)
  so tests never spawn a real judge subprocess; production callers get
  `spawn.judge_cmd` via a lazy import.

Built `gates/test_patrol_wiring.py`, covering: kill-switch short-circuit
(entry point and shared helper); should_fire honored on a
patrol-artifact-only event; the 3-role cap stopping the loop when every
candidate is a hit; the required regression test that prefilter misses
do not exhaust the cap (function name
test_three_prefilter_misses_do_not_exhaust_cap in
gates/test_patrol_wiring.py); board-run gating on non-empty `enqueued`;
and a respawn regression test (proposal item 5) — two separate
`python3 -c` subprocess invocations sharing on-disk state via a shared
calls-log file, checking a respawned run does not redo a role the
killed first run already recorded, and that a patrol-artifact-only
event still refuses to fire across the respawn boundary.

derived: `python3 -m pytest gates/test_patrol_wiring.py -q 2>&1 | tail -2`
```
.......                                                                  [100%]
7 passed in 1.02s
```

Edited `on-the-record/commands/run.md`'s merge step: one new
instruction immediately after the existing
`gh pr merge <n> --merge --delete-branch` line, running
`python3 gates/patrol_wiring.py run <repo-root> <merge-sha>` and
checking its trace output; the same edit documents the kill-switch file
inline.

canonical: on-the-record/commands/run.md, the edited merge step, read
directly this session.

That edit also required adding a `design-rationale:` frontmatter field
to run.md (pre-existing gap, unrelated to this issue) to satisfy
`design-rationale-guard.sh`, which fires on any edit to
`on-the-record/commands/*.md` — an inline, mechanical, in-write-set fix.

`docs/specs/enforcement-boundary.md` got a new row for
`patrol_wiring.py`, and `docs/specs/reconciled-index.md` was
regenerated via `python3 gates/spec_index.py --update` — required by
`gate-registration-guard.sh` before the commit would go through, not in
the frozen write set but a mechanically-forced same-commit plumbing
addition rather than a scope expansion.

## Why

Issue #1597 asks for the five already-landed patrol pieces to be
chained together at the merge-command seam so patrol runs automatically
after a PR lands, with a kill-switch checked first (#1360 lesson) and a
regression test that the anti-loop guard survives a watchdog respawn
mid-flow (flagged unverified by a prior validity consult).

## Upstream / basis

docs/issue-1597/proposals/patrol-wiring-e1.md — approved phase-1
proposal for this delivery.

canonical: `gh pr view 1601 --json state,mergedAt` — this session's own
run, before starting this delivery's implementation.
```
{"mergedAt":"2026-08-15T13:41:22Z","state":"MERGED"}
```

## Rationale for deviations

The approved proposal's plan section described E1's role loop as
stopping once the existing per-merge trace-line count reaches
`JUDGE_MAX_ROLES_PER_MERGE`. The task brief opening this session carried
a binding review correction overriding that design: a raw trace-line
count also counts `judge_cmd`'s prefilter-miss outcomes.

canonical: spawn.py lines 5560-5568 (`_append_judge_trace`), read this
session:
```
def _append_judge_trace(path: Path, ts: str, role: str, merge_sha: str, outcome: str) -> None:
    """judge 실행 한 건당 한 줄 — 성공/실패/캡-초과 가리지 않는다. `merge=`
    필드는 `_judge_roles_run_today()`가 3-역할 캡을 세는 데 쓰는 grep
    앵커다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = (f"- {ts} | role={role} | verb=judge | merge={merge_sha} "
            f"| outcome={outcome[:300]!r}\n")
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
```
One trace line is written per call regardless of outcome (hit,
prefilter-miss, or cap-exceeded), so a raw line count conflates misses
with hits.

Phase-2 implements the corrected design instead: `run()` maintains its
own `hits` counter, incremented only when a `judge_cmd` call returns
`skipped=False`, and stops the loop at 3 hits — never touching
`judge_cmd`'s own internal per-merge cap or trace format. The regression
test named above exercises this directly (part of the fenced run
earlier in this record).

## What did not work

None — no approach was written then discarded this session.

## Open findings

None known at time of writing.

## Doc-placement ladder

- [x] `on-the-record/commands/run.md` (command/procedure doc):
  merge-step instruction + kill-switch documentation added in the same
  commit as the code it documents.
- [x] `docs/specs/enforcement-boundary.md` + `docs/specs/reconciled-index.md`:
  new gate-registration row, same commit (mechanically required, see
  above).
- Not applicable this delivery: no new env var/config key/dependency/
  migration (proposal's Out of scope section names none); the one
  substantive design choice (hit-counted cap) is recorded above as the
  deviation section rather than a separate decisions/ doc; no
  benchmark/investigation numbers to place under reports/.

## Live demo status

canonical: `git log -1 --format=%H` on this branch, this session's own
run — 60ac6b0c, no PR opened against main yet at that point.

The proposal's acceptance section specifies two live demos — a real
merge triggering the chain, and a second real merge short-circuited by
the kill-switch — exercised through this repo's own orchestrator merge
step. This delivery's own PR is not yet open against main, so the seam
being exercised (`gh pr merge` followed by the new
`python3 gates/patrol_wiring.py run` line) has no merge to run against
until this PR itself lands.

MOCK: no live demo transcript is included in this record. What would
make it real: merging this PR through the normal orchestrator flow,
then running the two demos on this repo's next two merges (one plain,
one with `.on-the-record/patrol-disabled` present) and appending the
resulting `[patrol-wiring]` trace lines to this record.

## Next steps

Push this branch and open the phase-2 PR carrying `Closes #1597`; after
merge, run the two live demos above on this repo's own subsequent
merges and append their trace output to this record.

## Resolution path

Any open finding raised on this delivery is resolved by a follow-up
commit on this same branch/PR before merge, or, if raised after merge, a
new issue scoped to the specific finding.
