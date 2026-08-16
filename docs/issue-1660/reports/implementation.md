---
code_under_review:
  - gates/requirement_met.py
  - gates/test_requirement_met.py
  - on-the-record/hooks/directive.sh
  - on-the-record/hooks/test_directive_content.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Wired the requirement-fidelity program into the co-injected orchestrate
directive (`on-the-record/hooks/directive.sh`), mirroring the existing
#1024/#310 blocks, with three new obligations each naming its gate
module:

1. DESIGN-RESEARCH INTAKE (#1653): requires a `design-research: <ref>`
   trace or `design-research-skip: mechanical` before drafting a
   design-bearing issue. Checked by `gates/design_research_consult.py`
   (already landed, module-only before this change).
2. LANDING REQUIREMENT-MET GRADE (#1651): before `gh pr merge`, spawn a
   builder-blind grader session running `gates/requirement_met.py`.
   Deterministic artifact-presence sub-check blocks the merge; semantic
   verdict is advisory only.
3. SCOPE ADHERENCE AT LANDING (#1658): runs `gates/scope_adherence.py`
   against the PR's touched files vs the issue's `scope:` field before
   `gh pr merge`. Declared-scope violation blocks; undeclared scope is
   advisory only.

Added `on-the-record/hooks/test_directive_content.py` asserting all
three obligations' presence in `directive.sh` alongside the existing
#1024/#310 blocks (same test shape as the pre-existing directive-content
guard).

Folded the two #1651 review fixes into `gates/requirement_met.py`:
- `_artifact_in_diff_hunk()` tightens `artifact_in_diff` so a path only
  named in a diff header line (`diff --git`/`---`/`+++`) — i.e. only
  named in prose — no longer counts; the artifact string must appear in
  an actual added (`+`, non-`+++`) hunk line.
- `check()` now returns `{"blocked", "blocking_reasons", "advisory"}`
  instead of a bare list — `advisory` surfaces each criterion's raw
  text, semantic verdict, cited artifact, and `artifact_in_diff` flag,
  so the calling orchestrator can record/display the semantic verdicts
  without them blocking landing by themselves. `main()` prints each
  advisory line before the blocking-reasons summary.

## Why

northpole req#6 (issue #1660): the requirement-fidelity modules
(#1006/#1024/#1017/#310 already enforced; #1651/#1652/#1653/#1658
landed but module-only/inert) are only load-bearing once wired into the
co-injected orchestrate directive — that is how this class of discipline
is applied today in this repo. Builder-blind grading is mandated because
a builder attesting its own PR meets the requirement is the exact
failure mode `requirement_met.py` exists to catch; keeping the semantic
verdict advisory-only (never blocking by itself) avoids approval-fatigue
from over-gating on a probabilistic judgment, per the issue's stated
mitigation.

## Upstream basis

Issue #1660 acceptance criteria (verbatim in the issue body) and the
issue's own `design-research:` trace (2026-08-16 research briefs on
goal-drift prevention / requirement-met verification / HITL steering),
which chose directive-layer wiring over hard PreToolUse hooks — the
latter is an explicitly out-of-scope follow-up per the issue
("Hard-hook hardening ... is a sequenced follow-up").

Also: commit 003e7b3f on this branch (issue-1660/implementation).

## Acceptance verification

checked: directive.sh contains the three new obligations, each naming
its gate module; the new directive-content test asserts their presence.
canonical: `python3 -m pytest -q gates/test_requirement_met.py on-the-record/hooks/test_directive_content.py`
```
18 passed in 0.79s
```

checked: requirement_met artifact-presence tighten has a red test and a
green test, both in gates/test_requirement_met.py
(`t_red_artifact_named_only_in_diff_header_prose_fails` and
`t_green_artifact_in_added_hunk_line_passes`).
canonical: `python3 -m pytest -q gates/test_requirement_met.py`
```
18 passed in 0.79s
```

checked: live acceptance criterion (real design-bearing issue blocked
without a design-research trace; real landing PR spawns a builder-blind
grader gating on deterministic artifact-presence; a PR touching
out-of-scope files is flagged).
unverifiable: this is directive text consumed by a future orchestrator
session acting on a live issue/PR — it cannot be executed within this
single implementation turn, which has no live issue/PR to orchestrate
against. The directive text and its supporting gates
(`gates/design_research_consult.py`, `gates/requirement_met.py`,
`gates/scope_adherence.py`) are landed and unit-tested; the live
behavior activates the next time an orchestrator session follows this
directive.

Full-suite run, fast tier.
canonical: `python3 -m pytest -q -m "not slow"`
```
2103 passed, 19 xfailed, 2 xpassed in 20.27s
```

Test-tier note (issue #1518 directive): `.on-the-record/test-tiers.json`
declares a `fast`/`slow` split; this change touches
`on-the-record/hooks/*.sh` and `on-the-record/hooks/test_*.py`, both in
`slow`'s `trigger_change_classes`, so the slow tier was also run (`gh`-
and spawn-dependent tests, unrelated to this change's own diff, ~5min
wall-clock).

## What did not work

None.

## Open findings

None.
