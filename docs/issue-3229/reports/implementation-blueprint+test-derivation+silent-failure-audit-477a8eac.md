---
issue: 3229
role: implementation-blueprint+test-derivation+silent-failure-audit-477a8eac
author: implementation-blueprint+test-derivation+silent-failure-audit-477a8eac
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: same-commit
loop_state: landed
type: feature
breaking: false
verdict: enforcement-established
upstream:
  - path: delegation_state.py
    sha: same-commit
  - path: on-the-record/hooks/delegation-live-check.sh
    sha: same-commit
---

# issue-3229 — implementation-blueprint+test-derivation+silent-failure-audit-477a8eac record

## What was done

Wired issue #3061's `delegation_state.py` scope-manifest lookup into a
live turn via a new `Stop` hook, `on-the-record/hooks/delegation-live-check.sh`,
registered in `on-the-record/hooks/hooks.json` immediately after
`skill-verdict-guard.sh` and classified in `hook_classification.json` as
`invariant-injecting`, wrapped by `fail-open-wrapper.sh`.

This branch was cut fresh from `origin/main` at `a4ea9418`. Four prior
rounds of this same issue already ran to completion on a separate,
now-stale, never-merged implementation branch
(`issue-3229/implementation-blueprint+silent-failure-audit+test-derivation-b3718614`,
PR #3232 and its round PRs #3236/#3241/#3248/#3252/#3255) — canonical:
`git log --oneline --all | grep 3229` output, cross-checked against
`gh pr list --repo tokenmaxxxer/on-the-record --search 3229 --state all`:
round 1 shipped the hook, round 2 (PR #3236's adversarial review) found
and fixed a crash-trap direction bug and retired an unsound
adjacency-suppression path, round 3 (PR #3248's verification, PR #3241's
repair) restored a narrow, structurally-bound suppression case, and
round 4 (PR #3255's verification, its own repair commit `893e2b64`)
closed a scope-widening boundary probe. That branch was based on an old
`main` (predates issue #3228's silent-failure-lint work among others)
and was never merged, so it could not simply be fast-forwarded —
canonical: `git diff main origin/issue-3229/implementation-blueprint+silent-failure-audit+test-derivation-b3718614 --stat`
output, showing a large majority of the changed files unrelated to this
issue's own code. That diff named a foreign report file,
`docs/issue-3229/reports/implementation-blueprint+silent-failure-audit+test-derivation-b3718614.md`
— untracked on `main` and on this branch; it lived only on that stale,
unmerged branch and was never committed here.

Rather than re-deriving four already-verified rounds of reasoning from
scratch, this session extracted the cumulative code diff of the five
delegation-specific commits on that stale branch
(`3bd1f3fb`, `44facda0`, `2a2fea06`, `f059a1b3`, `893e2b64`) restricted to
the actual code paths (`delegation_state.py`,
`on-the-record/hooks/delegation-live-check.sh`, `hooks.json`,
`hook_classification.json`, `fail-open-wrapper.sh`,
`tests/test_issue_3229_delegation_live_wiring.py`,
`docs/specs/enforcement-boundary.md`, `docs/specs/generated-paths.md`) via
`git diff 3bd1f3fb^ 893e2b64 -- <paths>`, and applied that diff onto the
current branch with `git apply` — derived: `git apply --check`, clean,
no conflict. Two divergences from current `main` needed manual repair
after applying (see `## Rationale for deviations`).

The delivered hook (canonical: `on-the-record/hooks/delegation-live-check.sh`,
this commit):
- reads `transcript_path`/`cwd`/`stop_hook_active`/`last_assistant_message`
  off the raw `Stop` event JSON;
- loads `.on-the-record/delegation-state.json` via
  `delegation_state.load_state()`/`in_force()`; a session with no grant
  recorded at all produces no output and no stderr (silent, cheap no-op);
- derives the intended action from the `tool_use` events of the episode
  immediately preceding the ask (`_previous_episode_boundary()`, the
  backward mirror of `audit()`'s own forward `_episode_boundary()`) using
  the SAME `_extract_action()`/`is_covered()` #3061's `audit()` already
  uses — never from the question's prose;
- emits `{"decision": "block", "reason": ...}` on stdout only when the
  manifest is present and well-formed, the episode can be established
  complete (transcript's last assistant event matches the payload's own
  `last_assistant_message`), and one of the narrow, disclosed positive
  shapes holds (a fully-covered clean episode, or a single covered action
  whose own `tool_result.is_error` is true AND the ask does not name a
  wider scope than what was attempted, per `_ask_names_wider_scope()`'s
  closed marker set: force flags near push/publish, `main`/`master`/
  `production`/`prod`);
- leaves every other shape untouched (empty stdout) and writes a stderr
  reason for every decline except "no grant at all" (per the issue's
  "must not silently do nothing" clause);
- short-circuits before any of the above on `stop_hook_active` (issue
  #1725 retry-loop contract) and on a spawned session
  (`TOKENMAXXXER_SPAWNED`);
- fails toward NOT suppressing on any crash: `live_stop_decision()`
  catches every exception internally and returns `suppress=False`, and
  the shell trap remaps any nonzero exit to 0 (not 2) — the opposite
  direction from `stop-gate.sh`'s own house style, because for this hook
  the enforced action (`block`) is the dangerous one.

## Why

The seam question the issue asks to settle first (what can a `Stop` hook
actually do) was answered experimentally, not assumed, in the ported
work — canonical: `on-the-record/hooks/delegation-live-check.sh`'s own
module comment (this commit), which states plainly that the seam was
"established experimentally before this hook was written, not assumed
from documentation" and that a `Stop` hook can genuinely refuse the stop
via `{"decision": "block", "reason": ...}` on stdout, the same mechanism
`skill-verdict-guard.sh`'s own hard-violation path already uses. This is
real enforcement, not `additionalContext` (a same-turn correction the
orchestrator merely sees) and not an audit record (an after-the-fact
log) — the two weaker alternatives the issue names and asks to be ruled
out or delivered honestly if that is all the seam supports.

Deriving the intended action from `tool_use` events rather than the
ask's own prose was inherited directly from `audit()`'s existing
approach (issue #3061) precisely because the issue asks for the "same
way," and because the ask's prose is exactly the surface an earlier
review round's defect (PR #3236, canonical: `delegation_state.py`'s own
module comment above `_ask_names_wider_scope`, this commit) exploited:
an episode of innocuous, individually covered actions immediately before
a text-only ask about something completely different, dangerous, and
never attempted was wrongly suppressed under a first-draft "adjacency
implies correlation" rule. That defect, and its fix (retiring the
adjacency path down to `suppress: False` everywhere, then rebuilding a
narrower, structurally-bound suppression case keyed only on
harness-reported facts — episode length, manifest coverage,
`tool_result.is_error` — never on the ask's wording), is carried forward
unmodified from that prior, independently-verified work rather than
re-derived, since re-deriving it from scratch risked reintroducing the
exact bug those verification rounds already caught and fixed.

Porting the commits' code via `git diff`/`git apply` rather than
`git cherry-pick` was chosen after cherry-pick hit a conflict on the
foreign-authored report file named above — a conflict `board-gate.sh`
would then refuse this session from resolving at all (a session may
append to, but never alter or remove, another author's existing report
lines, per contract v3 s11) — and that same conflict would have recurred
on every subsequent commit in the pick sequence. Restricting the diff to
the actual code paths sidesteps it entirely while still carrying forward
the exact, already-verified code changes byte-for-byte.

## What did not work

None.

## Rationale for deviations

Two divergences from current `main` surfaced only after applying the
ported diff, both resolved in favor of `main`'s own already-landed state
rather than the stale branch's:

- `on-the-record/hooks/test_hook_classification.py`'s registration-count
  assertion conflicted during the initial cherry-pick attempt: `main`
  had already moved the expected count upward via issue #3231, while the
  stale branch's commit still assumed the pre-#3231 count. Resolved by
  computing the new literal as `main`'s own current count plus this
  delivery's own one added registration, rather than reapplying the
  stale branch's older, now-superseded literal — canonical:
  `on-the-record/hooks/test_hook_classification.py`,
  `test_registration_count_matches_the_issues_own_count`, this commit;
  acceptance: `python3 -m pytest on-the-record/hooks/test_hook_classification.py -q` — result: PASS.
- The ported diff's `hook_classification.json`/`fail-open-wrapper.sh`
  hunks carried a second, duplicate `amends-landing-apply.sh` entry
  classified `invariant-injecting` — stale from before issue #3231
  reclassified that same registration as `observability` on `main`.
  Applying the raw diff produced two conflicting entries for the same
  registration and a case-list mismatch in
  `test_wrapper_notice_case_list_matches_wrapped_invariant_injecting_entries`,
  reproduced live before the fix — derived:
  `python3 -m pytest on-the-record/hooks/test_hook_classification.py -q`
  (1 failed before this fix, 0 failed after — acceptance:
  `python3 -m pytest on-the-record/hooks/test_hook_classification.py -q` — result: PASS,
  see the same command cited above). Removed the duplicate entry and the
  duplicate case arm, keeping only this delivery's own
  `delegation-live-check.sh` addition — canonical:
  `on-the-record/hooks/hook_classification.json` and
  `on-the-record/hooks/fail-open-wrapper.sh`, this commit.

## Upstream basis

- `delegation_state.py` (this commit) — issue #3061's `load_state()`,
  `in_force()`, `is_covered()`, `_extract_action()`, `audit()`,
  `_episode_boundary()` are the functions `live_stop_decision()` reuses
  or mirrors; unchanged by this delivery.
- `on-the-record/hooks/skill-verdict-guard.sh` (pre-existing, unchanged)
  — the prior art this delivery's `Stop`-hook registration position and
  `decision:"block"` precedent are drawn from.
- Ported code diff: `git diff 3bd1f3fb^ 893e2b64` on
  `origin/issue-3229/implementation-blueprint+silent-failure-audit+test-derivation-b3718614`
  (commits `3bd1f3fb`, `44facda0`, `2a2fea06`, `f059a1b3`, `893e2b64`),
  restricted at port time to the code paths listed under "What was done."

## Open findings

None open. `SingleFailedUnrelatedActionResidualRiskTest` in
`tests/test_issue_3229_delegation_live_wiring.py` documents one disclosed,
narrow residual (a single covered action that fails for a reason
unrelated to a differently-shaped ask that immediately follows it, and
whose ask names no closed-set scope-escalation marker) — this is a named
and tested limit of the round-3/round-4 narrowing, not an unresolved
defect; further narrowing it was explicitly out of scope for the round-4
work this session ported — canonical: commit `893e2b64`'s own message.

## Acceptance

- acceptance: `python3 -m pytest tests/test_issue_3229_delegation_live_wiring.py -q` — result: PASS
  ```
  28 passed in 0.98s
  ```
- acceptance: `python3 -m pytest test/test_delegation_state.py -q` — result: PASS
  ```
  92 passed in 0.87s
  ```
- must-not demonstration (real hook binary, constructed `Stop` payloads):
  `MustNotSuppressTest` in `tests/test_issue_3229_delegation_live_wiring.py`
  drives `bash on-the-record/hooks/delegation-live-check.sh` as a real
  subprocess (never imports `live_stop_decision()` directly, per that
  file's own module docstring) for each of: no manifest recorded
  (`test_no_manifest_recorded_leaves_stop_untouched`), a malformed one
  (`test_malformed_manifest_leaves_stop_untouched`), and an action outside
  the manifest (`test_action_outside_manifest_leaves_stop_untouched`) —
  plus two more must-not partitions the issue also names: no derivable
  action (`test_no_derivable_action_leaves_stop_untouched`) and an
  incomplete episode (`test_incomplete_episode_leaves_stop_untouched`).
  All five assert empty stdout (stop left standing) — included in the
  28-passed run cited above.
- Regression check — derived: `python3 -m pytest -q -m "not slow"`:
  ```
  2 failed, 1494 passed, 3 xfailed
  ```
  Both failures (`harness/fixture-operator-experience/test_flow.py` ::
  `test_first_contact_fires_once_per_workspace`, and
  `on-the-record/checks/test_macos_bash32_compat.py` ::
  `MacosBash32CompatTest::test_current_head_is_clean`) reproduce
  identically on pristine `origin/main` before this delivery's changes —
  derived: `git stash && python3 -m pytest harness/fixture-operator-experience/test_flow.py on-the-record/checks/test_macos_bash32_compat.py -q; git stash pop`,
  same 2 failures — pre-existing, not introduced by this delivery.

## Next steps

None. `loop_state: landed`.

## Skill verdicts

skill-verdict: work-in-english — applied: invoked; all commit messages,
code comments, and this record are written in English per the skill's
routing rule; only the final chat-facing summary is in Korean.
skill-verdict: diagnose-first — not-applicable: the diagnostic question
this issue poses (what a `Stop` hook can observe/do) was already settled
experimentally across four prior, independently-verified rounds on the
stale branch this session ported from; this session's own work was a
mechanical port plus conflict repair, not a fresh cost/cause diagnosis.
skill-verdict: technical-feasibility-spike-report — not-applicable: no
new timeboxed spike was run this session; the feasibility question was
already answered and recorded by the prior rounds' own experiments
(canonical: `on-the-record/hooks/delegation-live-check.sh`'s module
comment, this commit).
other mounted skills: not triggered.
