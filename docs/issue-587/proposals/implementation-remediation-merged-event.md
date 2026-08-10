# Issue #587 — implementation proposal (phase 1, remediation round: timeline event 4)

status: proposed
files:
  - on-the-record/hooks/delegated-judgment-gate.sh
  - spawn.py
  - test_spawn.py

## Request

Remediation round (operator-relayed 2026-08-10, e2e verdict FAILED on PR #599's record): wire
issue-timeline event 4 ("Remediation PR merged"). The step-3 execution-observation record
(`docs/issue-587/reports/execution-observation/e2e-fixture-target-repo.md`, per-event table row 4)
confirmed — by source grep and by an empirical fixture-repo merge — that no shipped code posts the
`#573 §12` event-4 comment when a routed-to role's remediation PR merges. The architecture proposal
already named the merge-detection channel to reuse (`spawn.py`'s existing session-end/watch
surface); this round posts the comment per §12's format and proves it fires with a test.

## Constraints

- Format is fixed by `#573` §12, verbatim, not re-derived: `Remediation merged: PR #<m> resolves
  round <r> of PR #<n>` + link to PR #<m>, one line plus links, posted as an issue comment.
- Writer is the existing gate-adjacent surface, never a role self-reporting (§12: "the gate, same
  as section 11 — never a role, never the operator").
- No new state store: round/candidate-PR/status all come from records the gate already writes or
  fields this round adds to that same record family — never a separate marker file (architecture
  doc's binding "no new state" requirement, restated in survey.md's round-2 addendum).
- Idempotent: a merge event posts its comment exactly once, same read-then-check-marker discipline
  every other `spawn.py` comment poster already uses (`_post_session_end_comment`,
  `_post_stall_comment`).

## Rationale

Considered wiring event-4 detection directly into `on-the-record/hooks/delegated-judgment-gate.sh`
itself — i.e., have the gate notice a merge the next time it runs and post the comment then.
Rejected: the gate only runs on `gh pr create`/comment PreToolUse events against a *candidate* PR
under judgment; it has no trigger tied to a *remediation* PR's merge, which can happen with no gate
invocation at all (a plain `git merge`, as the execution-observation record's own drive
demonstrated — "No gh call was made by this plain git merge"). Detecting a merge needs an
after-the-fact sweep or a watch-loop hook, not a PreToolUse-triggered script — which is exactly the
surface the architecture doc's §12 hand-off already pointed at (`spawn.py`'s existing
session-end/watch surface), not the gate. The gate's only role in this round is adding the
candidate-PR field to `remediation-<seq>.md` so the sweep has something to link back to — the
detection and posting logic stays in `spawn.py`, alongside its other idempotent comment posters.

Considered inventing a new lightweight merge-watcher script under `on-the-record/hooks/` instead of
extending `spawn.py`. Rejected: the architecture doc's §12 text is explicit that "this phase does
not invent a new merge-detection channel" — `spawn.py` already has `_pr_open_or_merged_for_branch`
(MERGED-aware PR lookup) and the `_post_session_end_comment`/`_roster_reconcile_unreported` pair
(idempotent marker-based comment posting plus a periodic sweep pattern) — adding a second surface
would duplicate both the PR-state lookup and the idempotency discipline this repo already has in
one place.

## Accumulation

`_merged_pr_for_branch`/`_remediation_merge_sweep` add one more inline `gh`/`subprocess.run` call
site to `spawn.py`, in the same family as `_pr_open_or_merged_for_branch`,
`_post_session_end_comment`, `_post_stall_comment`, `_pr_list_call_ok` (all already inline,
un-abstracted `subprocess.run(["gh", ...])` calls). If this pattern keeps recurring — a fifth,
sixth, Nth idempotent-comment-off-a-marker poster — the accumulation this repo already tolerates is
one call site per event type, each a few lines, not a shared helper; that stays fine up to roughly
the count already in `spawn.py` today (four). Past that, the fix is a small
`_post_marked_comment(root, issue, marker, body_fn)` shared wrapper factoring out the
read-`_issue_comments`-then-check-marker-then-`gh api ... comments`-post skeleton every one of these
functions currently repeats by hand — not a new transport, just deduplicating the five-line
idempotency check itself. Not built now because four near-identical bodies is still cheaper to read
than one indirection layer, per this round's own scope (posting mechanism + test only).

## What will be done

1. `on-the-record/hooks/delegated-judgment-gate.sh`: add a `candidate_pr: <pr_ref>` field to the
   `remediation-<seq>.md` record the reject-path already writes (alongside `finding_source`,
   `routed_to`, `target_path`, `required_fix`, `contradicting_role`, `round`, `status`,
   `timestamp`) — the candidate PR number is already a local variable (`pr_ref`) in scope at that
   write site; this is field addition only, no new write path.
2. `spawn.py`: add a `_merged_pr_for_branch(root, branch) -> int | None` helper (MERGED-state-only,
   sibling to `_pr_open_or_merged_for_branch`) and a `_remediation_merge_sweep(root, issue) -> int`
   function, same shape as `_roster_reconcile_unreported`: for each
   `docs/issue-<n>/decisions/remediation-*.md` with `status: open`, resolve its `routed_to` role's
   branch (`issue-<n>/<role>`, the same convention `remediation_spawn.py`'s idempotency check
   already assumes), check `_merged_pr_for_branch` for that branch, and if merged, post the §12
   event-4 comment (`round`, `candidate_pr`, the merged PR number) via `gh issue comment` guarded by
   a fixed marker read back through `_issue_comments` before posting (idempotent, matching
   `_post_session_end_comment`'s read-then-check pattern) — never posting twice for the same
   remediation record.
3. `test_spawn.py`: a new test class (sibling to `PostSessionEndComment`/
   `RosterReconcileUnreported`) asserting: a fixture `remediation-1.md` with `status: open` and a
   merged branch produces exactly one `gh issue comment` call whose body matches §12's format
   verbatim; a second sweep with the marker already present posts nothing; a record whose branch is
   not (yet) merged posts nothing; `status: escalated`/`resolved` records are skipped without a PR
   lookup at all.
4. Run the full `spawn.py`/`gates/` test suites and this repo's other existing suites, fenced output
   captured in the phase-2 implementation record once approved.

## Out of scope

- Wiring `_remediation_merge_sweep` into a specific caller (a cron-like periodic invocation, the
  `watch`/`reconcile` CLI subcommands, or the orchestrator's `run.md` loop) beyond exposing the
  function and a thin CLI entry point equivalent to how `reconcile --unreported` already exposes
  `_roster_reconcile_unreported` — the call-site wiring choice is a `run.md`-contract decision, and
  this round's job (per the operator's remediation-round scope) is the posting mechanism and its
  test, not a new orchestration step.
- Re-verifying the other four already-confirmed-firing timeline events (1, 2, 3, 5) — this round is
  scoped to event 4 only, per the operator's remediation-round text.
- Any change to `gates/remediation_spawn.py` itself (the finding→spawn-task generator from the
  earlier step-2 round) — unaffected by this round's write set.

## How you'll know it worked

`python3 -m pytest test_spawn.py -q` (new class) and the existing `gates/test_remediation_spawn.py`
both pass; a fenced confirmation run reproducing the new test class's pass, plus a manual
fixture-repo check (same disposable-temp-dir pattern the step-3 execution-observation record already
used) showing the event-4 comment posts on a real fixture merge and does not re-post on a second
sweep, both go into the phase-2 implementation record.
