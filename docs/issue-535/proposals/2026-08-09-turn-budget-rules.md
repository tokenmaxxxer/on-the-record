---
status: proposed
files:
  - on-the-record/commands/run.md
  - on-the-record/hooks/directive.sh
---

## Request

The orchestrator's long foreground tool-call chains (multi-step merge and
verification sequences run inside one turn) block the harness's queued
user input until the turn ends — observed repeatedly on 2026-08-09. The
harness's queueing behavior is outside this repo, but the orchestration
contract currently *encourages* this shape (multi-step verify+merge
sequences done in one turn) — this is the part that's ours to fix. Add
explicit turn-budget rules to `/orchestrate:run` and the UserPromptSubmit
hook text: (1) operations expected to exceed ~30s go to background and
the turn closes right after arming observation; (2) multi-item mechanical
sequences (batch merges) get scripted into one background command
instead of an interactive foreground chain; (3) every reply ends at the
earliest point where remaining work is armed in background — close the
turn, let notifications drive the next one.

## Constraints

- Only `on-the-record/commands/run.md` and `on-the-record/hooks/directive.sh`
  may change — the two surfaces the issue names.
- Must not contradict or duplicate the existing bounded-wait pattern
  already established for role-session watching (`spawn.py watch
  --stall-timeout`, directive.sh 74-90) — the new rule generalizes it,
  it does not replace it.
- Must not weaken the existing "no auto-progression without user consent"
  gates (run.md step 6, "실행 계획" section) — backgrounding an operation
  is about *where* it runs, not about skipping a human decision point.
- Docs-only change: no dependency, schema, or env-var surface is touched.

## Rationale

**Alternative considered: a mechanical PreToolUse hook that measures
elapsed foreground Bash time and blocks/warns past a threshold** (the
same enforcement style already used elsewhere in this plugin — e.g.
`retry-loop-bound.sh`, `contract-guard.sh`). Rejected for this pass: a
hook can only see *past* elapsed time after the fact (a single Bash call
already ran long, or N calls already happened in the current turn) — it
cannot know in advance that an *upcoming* operation (a `gates/*.py` run,
a batch of merges) is expected to exceed ~30s, which is exactly the
judgment the issue's fix direction asks for ("any operation *expected*
to exceed ~30s"). The issue's own acceptance criteria also scope this
phase to contract text (`grep` for rule anchors in the changed docs), not
a new gate script. A mechanical enforcement hook remains a plausible
phase-2/follow-up if the contract-text rule proves insufficient in
practice — the "empty state" acceptance criterion below names this
explicitly.

**Alternative considered: rewrite the existing role-session background
mandate (run.md step 4) to also cover the orchestrator's own operations,
instead of adding a new section.** Rejected: step 4 is specifically about
spawning role sessions (a different mechanism — `spawn.py <role>` — with
its own background/foreground semantics already correctly stated). The
gap this issue targets is the orchestrator's *own* foreground chains
(merges, verification runs, watchdog polling), which is a distinct
concern from role-session spawning. Folding the new rule into step 4
would conflate "background the thing you spawn" with "background the
thing you yourself run," which are different operations with different
existing patterns to reference (spawn's `run_in_background: true` vs. a
bare Bash call that should itself be backgrounded or deferred).

## What will be done

1. In `on-the-record/commands/run.md`, add a new top-level section (near
   the existing "체크아웃/검증 상태 관련 주의" and watchdog material) titled
   turn-budget rules, stating the three rules from the issue's fix
   direction, each cross-referencing the concrete existing surface it
   applies to:
   - Rule 1 (~30s threshold → background): applies to `gates/*.py`
     verification runs (lines 416-423), `gates/landing_readiness.py`
     (line 281), and the watchdog poll (lines 513-522) — rewrite the
     watchdog instruction to explicitly say the poll itself must not
     occupy a blocking foreground turn.
   - Rule 2 (batch mechanical sequences → one background script):
     applies to the decision queue's merge acceptance step (step 6,
     lines 266-277) when 2+ queued items are mechanical merges — state
     that N `gh pr merge` calls become one background script, not N
     foreground calls.
   - Rule 3 (close the turn once armed): state as a general default,
     explicitly generalizing the watch/re-arm shape already used for
     role sessions (directive.sh 74-90) to all foreground work covered
     by rules 1-2.
2. In `on-the-record/hooks/directive.sh`, add one short paragraph to the
   injected `cat <<EOF` block restating the three rules in compressed
   form (consistent with the hook's existing style of condensing run.md
   into a per-prompt reminder), pointing to `/orchestrate:run` for detail
   the same way the existing bullets do (line 114).
3. Run the existing hook test suite
   (`on-the-record/hooks/test_*.py` via `python3 -m pytest`) to confirm
   no existing hook test regresses from the directive.sh text change.

## Out of scope

- Any new `gates/*.py` mechanical enforcement of the turn-budget rule
  (see Rationale — a plausible follow-up, not this pass).
- Changes to `spawn.py`, `watch`, or `watchdog` *behavior* — only the
  contract text describing when/how the orchestrator invokes them.
- Any other plugin hook (`stop-gate.sh`, `deliverable-guard.sh`, etc.) —
  only the two files the issue names.

## How you'll know it worked

- `grep` for the new rule-anchor text in `on-the-record/commands/run.md`
  and `on-the-record/hooks/directive.sh` finds all three rules present in
  both files (documented in the delivery PR, per the issue's first
  acceptance check).
- A `grep` sweep of both changed files for any remaining instruction that
  mandates foreground blocking beyond one bounded watch call, documented
  in the PR body, per the issue's second acceptance check.
- `python3 -m pytest on-the-record/hooks/` passes (docs-only change — no
  new test file is added in this phase; existing hook tests must not
  regress from the directive.sh text edit).
- provenance: read (phase-1 proposal; no code executed yet).
- empty state: not applicable — no corpus/data surface is touched; if a
  turn-budget rule cannot be enforced by contract text alone (e.g. the
  batch-merge scripting rule), the phase-2 record will name
  `gates/*.py` as the enforcement hook that would carry it, per the
  issue's own empty-state acceptance criterion.

## Hunt record

after-proposal: docs-only, no before-landing dispatch — all touched paths (`docs/issue-535/proposals/`, `docs/issue-535/reports/`) are under `docs/`, per the warrant directive's docs-only fast path.
