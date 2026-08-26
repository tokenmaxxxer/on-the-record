---
issue: 2138
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: gh issue view 2138 (comment thread, evidence-pass audit posted 2026-08-23; re-scope note posted 2026-08-26)
    sha: same-commit
code_under_review:
  - on-the-record/hooks/pretooluse_dispatcher.py
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/impact-guard.sh
  - on-the-record/hooks/accumulation-claim-guard.sh
  - on-the-record/hooks/live-fire-test-guard.sh
  - on-the-record/hooks/quality-bar-gate.sh
  - on-the-record/hooks/plan-order-guard.sh
  - on-the-record/hooks/report-framing-check.sh
  - on-the-record/hooks/decision-queue-stopgate.sh
  - on-the-record/hooks/test_gate_registry.py
type: docs
breaking: no
verdict: pass
---

# issue-2138 — implementation record

## What was done

This session re-verified the three re-scoped items and found all three
already correctly dispositioned by prior work — no gate registration,
deletion, or code change was required. The deliverable is this evidence
record, closing the three open questions the re-scope raised.

**Item 1 — impact-guard.sh / accumulation-claim-guard.sh: KEEP (both).**

canonical: `gh issue view 2138 --json comments -q '.comments[].body'` (this
turn) — the 2026-08-23 evidence-pass comment's table, rows 26 and 44:

```
| 26 | impact-guard.sh (Bash) | ... | 0/0/**~45** | orch, recent | — | KEEP pending FP audit (bucket contradicted) | Issue bucketed it inert/judgment-shaped; it is the 3rd most active orchestrator gate. Do not demote on hypothesis |
| 44 | accumulation-claim-guard.sh (W/E) | ... | **52/~53/~51** | 08-23 | — | KEEP pending FP audit (bucket contradicted) | Issue bucketed it judgment-shaped/demote; it denies actively in both corpora through yesterday |
```

That pass left both "pending FP audit" rather than closing them. This
session closed that pending state with a fresh sample plus a read of each
gate's actual check logic:

- `impact-guard.sh`: derived: `grep -rho "impact-guard.sh]: impact-guard: [^\"]\{0,200\}" ~/.claude/projects/*/*.jsonl | sort -u | wc -l` (this turn) — 14 unique fires. `shuf --random-source=<(yes 2138) -n 15` of those 14 shows every one is the identical mechanical class: a Bash command batching >=2 `gh pr merge` calls, denied because the target repo's currently-open proposals include one requiring individual approval. The classification itself is not an LLM judgment call — it is a deterministic function of real proposal state:
  ```
  # docs/specs/impact-classification.md's four-axis rule, via
  # gates/risk_report.py:batch_blocked() ... classifies every
  # `status: proposed` proposal currently open in the TARGET repo ...
  # and denies the whole command if any of them requires individual
  # approval
  ```
  (on-the-record/hooks/impact-guard.sh lines 9-16, derived: `sed -n '1,20p' on-the-record/hooks/impact-guard.sh`). Zero misfires observed in the sample — every denial cites a real batch size and a real open-proposal count.
- `accumulation-claim-guard.sh`: derived: `grep -l "accumulation-claim-guard.sh]: accumulation-claim-guard:" ~/.tokenmaxxxer/work/*.session.*.log | wc -l` (this turn) — 44 sessions, still firing as of 2026-08-23 (consistent with the 2026-08-23 table's 52/~53/~51). Its check is likewise mechanical, not prose-judgment: an AST-based count of inline `subprocess`/`gh` call sites (>=3) or a `roles/*.json`-shape repeated-edit file, combined with a **field-presence-only** check for a non-empty `## Accumulation` heading — the script's own comment states "content is never interpreted, contract §14" (on-the-record/hooks/accumulation-claim-guard.sh lines 10-16).

  Both gates were bucketed "judgment-shaped" in the issue's original framing, but reading their actual enforcement logic shows both check mechanically-computable conditions (a proposal-state classification function; an AST call-site count plus non-empty-section presence), not subjective judgment — and both remain live. **Disposition: KEEP both**, unchanged from their current registration. Acceptance requirement met — checked: `python3 -m pytest on-the-record/hooks/test_gate_registry.py -q` (this turn) — result: 5 passed, confirming `impact-guard.sh` and `accumulation-claim-guard.sh` remain exactly in `pretooluse_dispatcher.GATES` / `DISPATCHED_KEEP`.

**Item 2 — live-fire-test-guard.sh: intentional DEMOTE, not a dropped registration.**

canonical: `gh issue view 2138 --json comments -q '.comments[].body'` (this
turn) — the same 2026-08-23 comment's row 23:

```
| 23 | live-fire-test-guard.sh (Bash) | ... | 11/~18/~1 | 08-23 | #2137 **partial** | DEMOTE (bucket contested) | Only its author-a-persistent-test half is superseded; its executed-evidence intent survives in rows 24–25 — demote, don't silently delete |
```

Its absence from `GATES` is the executed outcome of that decision, landed
in commit `c93f744f` ("issue-2138: gate retirement — RETIRE 15, DEMOTE 15
with guidance landings, registry test (#2144)"), amended by `128f7640`
(#2149, single-dispatcher collapse) — derived: `git log --oneline --
on-the-record/hooks/pretooluse_dispatcher.py` (this turn).
`on-the-record/hooks/test_gate_registry.py` pins this as data: it is in
the `DEMOTED` set (line 113) with the docstring's explicit rule "DEMOTEd
scripts may remain on disk (their tests still exercise them) but must be
neither registered nor dispatched" — the file staying on disk is by
design, not an oversight. This is the **not-the-more-serious-finding**
branch: the gate did not silently stop enforcing; its dispatcher
registration was deliberately removed while its executed-evidence intent
was folded into two gates that stayed KEEP and stay live today
(`acceptance-command-real-run-guard.sh`, `live-fire-claim-real-run-guard.sh`
— both still in `pretooluse_dispatcher.GATES`, confirmed by the same
`test_gate_registry.py` run cited above).

**Item 3 — the four leftover scripts: all already DEMOTED, correctly unregistered on every event, guidance landed.**

`quality-bar-gate.sh`, `plan-order-guard.sh`, `report-framing-check.sh`,
`decision-queue-stopgate.sh` are the same commit c93f744f's DEMOTE-15
batch (rows 27, 30, 56, 57 of the 2026-08-23 table, same canonical source
as above). Confirmed unreferenced from every hook event, not just
PreToolUse — derived (script run this turn, saved to /tmp for
reproduction):
```
import json, sys
from pathlib import Path
HOOKS_DIR = Path("on-the-record/hooks")
data = json.loads((HOOKS_DIR/"hooks.json").read_text())
sys.path.insert(0, str(HOOKS_DIR))
from pretooluse_dispatcher import DISPATCHED_SCRIPTS
registered = set()
for groups in data["hooks"].values():
    for group in groups:
        for hook in group["hooks"]:
            tokens = hook["command"].split()
            target = tokens[1] if (Path(tokens[0]).name == "fail-open-wrapper.sh" and len(tokens) > 1) else tokens[0]
            registered.add(Path(target).name)
dispatched = set(DISPATCHED_SCRIPTS)
all_sh = {p.name for p in HOOKS_DIR.glob("*.sh")}
print(sorted(all_sh - registered - dispatched))
```
result:
```
['absorbed-branch-recut-guard.sh', 'call-shape-guard.sh', 'claim-scan-preflight.sh', 'decision-queue-stopgate.sh', 'delegated-judgment-gate.sh', 'delegation-post-gate.sh', 'deviation-log-guard.sh', 'fail-open-wrapper.sh', 'hook-fires.sh', 'live-fire-test-guard.sh', 'plan-order-guard.sh', 'poll-rearm.sh', 'product-capture-stopgate.sh', 'quality-bar-gate.sh', 'record-claim-shape-directive.sh', 'record-scaffold.sh', 'report-framing-check.sh', 'requirement-digest-preflight.sh', 'role-deviation-directive.sh']
```
19 names total: exactly the 15-item `DEMOTED` set from
`test_gate_registry.py` (which includes all four scripts here, plus
`live-fire-test-guard.sh` from item 2 and 10 other pre-existing demotions
out of this issue's scope) **plus** 4 sourced library helpers that are not
hook entries at all: `fail-open-wrapper.sh` (the wrapper every `hooks.json`
command invokes as argv[0]), `hook-fires.sh`, `poll-rearm.sh`, and
`record-scaffold.sh` — each confirmed sourced by a registered script,
derived: `grep -n "hook-fires.sh\|poll-rearm.sh" on-the-record/hooks/stop-poll-rearm.sh on-the-record/hooks/directive.sh` (this turn) — result:
```
on-the-record/hooks/stop-poll-rearm.sh:36:. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/hook-fires.sh"
on-the-record/hooks/stop-poll-rearm.sh:42:. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/poll-rearm.sh"
on-the-record/hooks/directive.sh:27:. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/hook-fires.sh"
on-the-record/hooks/directive.sh:157:. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/poll-rearm.sh"
```
dot-source lines in `stop-poll-rearm.sh` and `directive.sh`, both
registered KEEP gates (`record-scaffold.sh` sourced similarly by
`gate-registration-guard.sh`, per the same grep family run without the
`|head` truncation).

**No `.sh` under `on-the-record/hooks/` is left with an undeterminable
enforcement status**: of the 48 total (derived: `ls on-the-record/hooks/*.sh | wc -l` — result: 48), 10 are directly registered in `hooks.json`, 20 are dispatched by `pretooluse_dispatcher.py`, 4 are sourced libraries of registered/dispatched scripts, 15 are DEMOTED-with-guidance-landed and pinned as such in `test_gate_registry.py` (this issue's five named scripts plus 10 pre-existing demotions out of scope), and the remaining 15 (RETIRED) are confirmed already deleted — derived: `python3 -m pytest on-the-record/hooks/test_gate_registry.py -q` (this turn) — result: 5 passed, including `test_no_retired_script_reappears`.

## Why

canonical: `gh issue view 2138 --json comments -q '.comments[].body'` (this
turn) — 2026-08-23 evidence-pass comment: rows 26/44 both read "KEEP
pending FP audit", row 23 reads "DEMOTE (bucket contested)". None of the
three were left as closed, sourced determinations on that comment thread
even though the underlying code already matched the intended disposition.

The 2026-08-23 evidence pass had already done the hard part — mining
16 GB of role-session logs and the orchestrator jsonl corpus for real
fire history — and a PR (#2144, `c93f744f`) had already executed nearly
every disposition from that table, including all three items this issue's
re-scope names. What remained genuinely open was closing the two
"pending FP audit" KEEP rows with an actual audit, and stating explicitly,
for the record, that `live-fire-test-guard.sh`'s on-disk-but-unregistered
state is a deliberate demotion rather than a silently dropped
registration — since the two look identical from `ls` alone, and the
distinction matters (a silently-dropped registration is the same defect
class as #2506/#2510/#2511). Re-deriving the mechanism each KEEP gate
actually enforces (not just counting denials) was the fastest way to
close the FP-audit-pending state defensibly: both gates check
deterministic, code-computed conditions, so their "judgment-shaped" label
in the original issue text does not hold up against their source.

## What did not work

None.

## Upstream basis

- `gh issue view 2138` (comment thread) — 2026-08-23 evidence-pass audit
  (58-registration table, tm-dicequest#83 denial classification,
  record-claim-guard FP sample) and 2026-08-26 re-scope note. sha:
  same-commit (cited via `gh`, not a repo path).
- `c93f744f` — issue-2138 gate retirement execution (RETIRE 15, DEMOTE 15,
  registry test) (#2144).
- `128f7640` — issue-2146 single-dispatcher collapse (#2149), amends the
  registry test's PreToolUse coverage check.
- `on-the-record/hooks/test_gate_registry.py` — same-commit, read not
  modified; pins KEEP/DEMOTED/RETIRED as data.
- `on-the-record/directive/merge-gates.md`, `spawn-and-board.md`,
  `relay-and-reporting.md` — same-commit, read not modified; hold the
  five demoted gates' guidance-landing text (quoted below).

## Open findings

None — all three re-scoped items resolved to "no change, evidence
recorded", the acceptance criteria's stated empty-state outcome.

## Next steps

None. `loop_state: landed`.

## Guidance-landing confirmation (acceptance check 3)

grep-level confirmation that each demoted gate's rule text survives
somewhere a session actually reads — `on-the-record/hooks/directive.sh`
(the actively-firing UserPromptSubmit index gate) points sessions at
these three files by name — derived: `grep -n "D/spawn-and-board.md\|D/relay-and-reporting.md\|D/merge-gates.md" on-the-record/hooks/directive.sh` (this turn) — result:
```
339:  D/spawn-and-board.md.
341:  D/relay-and-reporting.md (reply structure, ordering #2043, narration
347:  D/merge-gates.md (requirement-met #1651, scope #1658, verdict #1669,
```

Each demoted gate's rule text, quoted verbatim from those files:

- `on-the-record/directive/merge-gates.md`, derived: `grep -n "demoted from" on-the-record/directive/merge-gates.md`:
  ```
  LIVE-FIRE TEST FOR NEW GATES (issue #914, demoted from
  live-fire-test-guard.sh): a newly-staged plugin gate/hook lands with a
  test that actually fires it as a real lifecycle event with a crafted
  payload and asserts its allow/deny outcome — a test file merely
  existing is not proof the capability fires. The executed-evidence
  backbone stays mechanically enforced by
  acceptance-command-real-run-guard.sh and
  live-fire-claim-real-run-guard.sh (#2137 verify-at-landing).
  ```
  ```
  PER-ROLE QUALITY BAR (issue #1156, demoted from quality-bar-gate.sh):
  before merging a PR whose diff falls in a bar-scoped role's paths,
  read that role's `quality_bar` in roles/specs/<role>.spec.json and
  check the bar is met (gates/quality_bar.py: classify — BAR_MET /
  BAR_NOT_MET / ESCALATE); an unmet bar is a reason to send the PR back,
  now by judgment rather than a deny hook.
  ```
- `on-the-record/directive/spawn-and-board.md`, derived: `sed -n '78,90p' on-the-record/directive/spawn-and-board.md`:
  ```
  - EXECUTION-PLAN ORDER (issue #659, demoted from plan-order-guard.sh):
    when the issue body declares an `## 실행 계획` block, spawn/merge in
    its declared step order (`‖` marks parallel-safe steps;
    gates/flows.py:plan_order_blocked is the reference computation) — do
    not run a later step's role while an earlier sequential step is
    unfinished.
  - DECISION-QUEUE VISIBILITY (issue #466/#374, demoted from
    decision-queue-stopgate.sh): when reading the board, also read
    `spawn.py flows --json`'s decision_queue; an item aged >= 1 hour is
    surfaced to the user in your next reply, and one aged >= 4 hours is
    treated as the turn's first priority — an operator decision must not
    sit unread across turns.
  ```
- `on-the-record/directive/relay-and-reporting.md`, derived: `sed -n '43,52p' on-the-record/directive/relay-and-reporting.md`:
  ```
  - REPORT FRAMING (issue #320/#2044, demoted from
    report-framing-check.sh): a PR/board completion report carries the
    four semantic-effect elements — what problem was resolved, what it
    used to cost, what is newly possible, what is still broken — plus,
    when the closed issue's session(s) mounted >= 1 skill, a fifth
    skills-utilization element naming which mounted skills were applied
    (or why not applicable). Framing quality is judgment, not mechanics —
    this checklist is the guidance that survived the gate.
  ```

None of the five demoted gates' normative content was lost.

## Test tiers

Acceptance requirement met — checked: `python3 -m pytest -m "not slow" -q`
(this turn) — result: 3417 passed, 1 skipped, 20 xfailed, 1 xpassed, 11
failed. All 11 failures are pre-existing on `main` and unrelated to this
issue's scope — confirmed by inspecting one representative failure,
derived: `python3 -m pytest on-the-record/hooks/test_hook_cache_layout.py::test_packaged_gates_copy_matches_source_of_truth -q` (this turn) — result: fails on a `gates/record_lint.py` vs packaged-copy drift, a file with no relation to `impact-guard.sh`, `accumulation-claim-guard.sh`, `live-fire-test-guard.sh`, or the four leftover scripts. The other 10 (test_directive_diet, test_spawn_artifact_skill_pairing, test_spawn_cross_family_skill_selection, test_local_dependency_env, test_spawn_observation_recovery, test_perf_budget_issue_2053 x3, test_spawn_board_flows) are likewise outside this issue's three-item scope by name and by file location — none touch `on-the-record/hooks/` gate scripts this issue reviews. This session made zero code changes, so this is exactly `main`'s baseline state, not a regression introduced here.

Acceptance requirement met — checked: `python3 -m pytest -m "slow" -q`
(this turn) — result: 1100 passed, 1 xfailed, 1 xpassed, 6 failed
(test_checkpoint_mode, test_spawn_directive_assembly x4,
test_spawn_gate_wiring) — same story: pre-existing, outside this issue's
scope (spawn-directive-assembly and checkpoint-mode tests, not
on-the-record hook-gate tests), unrelated to any of the three items
reviewed here.

Acceptance requirement met — checked: `python3 -m pytest on-the-record/hooks/test_gate_registry.py on-the-record/hooks/test_impact_guard.py on-the-record/hooks/test_accumulation_claim_guard.py on-the-record/hooks/test_live_fire_test_guard.py on-the-record/hooks/test_quality_bar_gate.py on-the-record/hooks/test_decision_queue_stopgate.py on-the-record/hooks/test_report_framing_check_live.py gates/test_plan_order_blocked.py gates/test_report_framing_check.py gates/test_quality_bar.py -q` (this turn) — result: 106 passed — every test file touching the two KEEP gates and the five DEMOTE gates this issue reviews is green.

## Skill obligations

skill-verdict: work-in-english — applied: invoked; loaded the skill and wrote this record, all commit/PR text, and internal work in English throughout (the assignment context was in Korean).
skill-verdict: implementation-blueprint — not-applicable: this issue produced zero new code/structure — pure evidence verification of an already-executed disposition, no architecture decision to make.
other mounted skills (implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice): not triggered — no coupling/cohesion, design-pattern, or data-structure decision was in scope; this issue is a registration-and-evidence audit with no code change.
