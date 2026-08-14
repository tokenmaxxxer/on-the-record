---
subject: issue-246
role: execution-observation
observed_role: implementation
observed_pr: 253
code_under_review: bc53410e
loop_state: handed-off
---

# Execution-observation record — issue #246, PR #253 (`implementation` role)

Auto-spawned by `spawn_on_pr.py` on PR creation for `issue-246/implementation`.
Phase-2 approval posted this session as the issue-level comment whose
entire body is `APPROVE issue-246/execution-observation`, author
`jjongkwann` (listed in `docs/specs/approvers.md`), single-account mode
per role-handoff contract v3 s19 — same pattern as PR #253's own
`APPROVE issue-246/implementation` comment, also `jjongkwann`.

## Independence

This role did not author, edit, or execute the observed artifact. PR
#253's three commits are the `implementation` role's; nothing under
`spawn.py`, the classifier's test file, or the observed role's own
proposal/report files was written or edited by this session. This
session ran the shipped, already-landed test suite as-is and read diffs
directly; no part of the observed role's implementation task was redone.

## What this session did

Checked outcome, trajectory, and step against the PR #253 diff, the code
at the current default-branch tip, and an independent re-run of the
regression fixtures the observed role's own record names.

## Why

canonical: gh issue view 246
Issue #246 asked for three fixes to the `permission_denials` refusal
classifier in `spawn.py` — report-loss inputs, per-layer dedup masking,
and a non-pinning regression fixture — plus an issue-level comment
requiring the dedup masking's session-wide suppression to be fixed rather
than documented as an accepted limit. This record checks that against
the code itself, not against the observed role's own narration of it.

## What was read this session

- canonical: gh issue view 246 — body and both comments (the original
  three defects, the scope-expansion requirements, and
  `APPROVE issue-246/implementation`).
- canonical: gh pr view 253 --json commits,mergedAt,mergeCommit,files,reviews
  — three commits, empty `reviews`, six changed files (two proposal/report
  docs plus the classifier source and its test file).
- canonical: git show ce059e46 -- spawn.py — the delivery diff to the
  classifier, in full.
- canonical: git show ce059e46 -- test_spawn.py — the delivery diff to
  the classifier's test file, in full (via a `def test_` name diff).
- canonical: git show 71c9a49c --stat / git show 74849e56 --stat — the
  two earlier, docs-only commits' write sets.
- canonical: docs/issue-246/proposals/refusal-classifier-residual-fixes.md
  — `## Constraints`, `## Out of scope`, `## How you'll know it worked`
  sections, read in full.
- canonical: docs/issue-246/reports/implementation.md — read in full.
- canonical: spawn.py:3110-3229, spawn.py:6581-6721 (current default-branch
  tip) — `_classify_refusal_text`, `_flush_correlated_refusals`,
  `_flush_unverified`, and the `_spawn_one` stream loop, to check the fix
  against later, unrelated issues that touched the same region.
- canonical: tests/test_spawn.py (current default-branch tip, via
  `grep -n 'def test_'`) — located every fixture name the observed role's
  record cites, checking that each one still exists after the test
  file's later, unrelated move from the repo root into `tests/`.

## Evidence — classifier fix, current default-branch tip

canonical: git show ce059e46 -- spawn.py (hunk `@@ -2845,24 +2917,29 @@`)
The `type=="result"` branch reads `raw_denials =
result.get("permission_denials")` and branches on `isinstance(raw_denials,
list)`: a real list (any shape) routes to `_flush_correlated_refusals`;
anything else (absent, `None`, or a truthy non-list) routes to
`_flush_unverified`. A post-loop check (`spawn.py:6716-6721`) calls
`_flush_unverified` when the stream loop exits with `result_seen` still
`False` and `pending_refusals` non-empty — the terminal-`result`-line-
never-arrived path.

canonical: git show ce059e46 -- spawn.py
The dedup key for the gate layer widened from a stem-only pair to
`("gate", hook_path, reason)`; the harness/sandbox layers widened from a
layer-wide single-element key to `("harness", detail)` /
`("sandbox", detail)`, where `detail` is
`" ".join(text.strip().split())[:300]` — whitespace-collapsed and
truncated before being used as the key.

canonical: git show ce059e46 -- spawn.py, cross-checked against
spawn.py:3189-3218 at the current default-branch tip
The old session-wide `refusals_seen` boolean gate was replaced with
per-candidate correlation: a `Counter` built from the confirmed
`permission_denials`' `tool_name` fields, consumed one unit per buffered
candidate whose own resolved `tool_name` (traced through a new
`tool_use_names` id-to-name map built from `tool_use` blocks) still has a
remaining count in that counter. A candidate whose `tool_name` no longer
has a remaining count is dropped rather than emitted under its classified
layer label.

canonical: spawn.py:3110-3125 (current default-branch tip, docstring of
`_classify_refusal_text`)
The dedup-key normalization rule — whitespace-collapse, 300-char
truncation, case preserved, layer-1 keyed on the hook's full path rather
than its filename stem — is stated inline in the function's own
docstring.

canonical: git show ce059e46 --stat / git show 71c9a49c --stat / git show
74849e56 --stat
Across all three commits the only files touched are the classifier
source, its test file, and the issue's own `docs/issue-246/*` records —
no `_await_bounded` or watch-cycle code appears in any diff, and no new
CLI flag, log line, or hook file is added; the fix reads fields
(`permission_denials`, `tool_use_id`, `tool_use` blocks) the stream loop
was already parsing.

canonical: spawn.py:3189-3218 (current default-branch tip)
The `unattributable` counter inside `_flush_correlated_refusals` — the
observed role's own record describes an earlier cut that dropped
`tool_name`-less `permission_denials` entries from the leftover count
entirely — is present at the current tip, not only at the commit PR #253
landed.

No defect surfaced in this region during this observation beyond what the
observed role's own record already names and bounds under its own
open-findings section (N-candidates-vs-M-same-`tool_name`-denials, and
the 300-char truncation-collision trade-off) — both are explicitly
accepted residuals in the proposal's own "Out of scope" section, not
gaps this PR introduced.

## Acceptance verification

canonical: python3 -m pytest tests/test_spawn.py -k "eof_with_pending or untrustworthy_permission_denials or two_distinct_same_layer or two_identical_same_layer or two_hook_paths_sharing or whitespace_variant_same_layer or denial_entry_missing_tool_name or unresolved_tool_use_id_with_well_shaped or repeated_result_line or spurious_candidate_tool_name" -q
— result:
```
...........                                                              [100%]
11 passed, 492 deselected in 279.60s (0:04:39)
```
This selection matches, by name, the regression fixtures the observed
role's record lists for the three defects: the EOF/crash flush, the
malformed-`permission_denials`-shape flush, the two same-layer-dedup
pairs, the hook-stem-collision case, the whitespace-normalization-
collision case, the `tool_name`-missing case, the unresolved-
`tool_use_id` case, the repeated-`result`-line case, and both halves of
the replaced case-(iii) fixture (the mismatch case and its
match-correlates companion, both caught by the same `-k` substring). All
selected cases are green in the run above.

unverifiable: a full, unfiltered `python3 -m pytest tests/test_spawn.py -q`
run was attempted twice in this session (foreground, then backgrounded)
and neither finished within this session's available wall time before
being stopped — the suite has grown substantially since PR #253's own
merge-time run (later, unrelated issues added fixtures across the whole
file), and this environment's per-test cost pushed a full run past
several minutes without finishing. The filtered run above is the
load-bearing evidence for the verdicts below; it directly exercises every
fixture those verdicts cite.

## Verdict 1 — outcome

canonical: python3 -m pytest tests/test_spawn.py -k "eof_with_pending or untrustworthy_permission_denials or two_distinct_same_layer or two_identical_same_layer or two_hook_paths_sharing or whitespace_variant_same_layer or denial_entry_missing_tool_name or unresolved_tool_use_id_with_well_shaped or repeated_result_line or spurious_candidate_tool_name" -q
— result: green, per the Acceptance verification section above.

The classifier fix addresses issue #246's three defects and its
scope-expansion's requirement to fix, rather than pin, the session-wide
suppression — see "Evidence" above for the code-level grounding of each,
and "Acceptance verification" above for the fixture-level grounding. The
two open items the observed role's record carries forward are
pre-existing, explicitly accepted trade-offs from the proposal's own
scope, not gaps this observation adds.

## Verdict 2 — trajectory

canonical: git show 71c9a49c --stat / git show 74849e56 --stat / git show
ce059e46 --stat
The commit ordering is docs-only, then docs-only (the scope-expansion
rework, still pre-code), then code-plus-docs — the survey and proposal
preceded any code, and the scope-expansion comment was folded into the
proposal before implementation began, not after.

## Verdict 3 — step

canonical: git show ce059e46 -- spawn.py / tests/test_spawn.py (current
default-branch tip) — see "Evidence" and "Acceptance verification" above
No single deficient artifact was located. Every item this session could
check against the diff, and every fixture this session could
independently re-run, lined up with the code at both the merge commit and
the current default-branch tip. This observation recommends no
remediation round.

## Rationale for deviations

canonical: gh issue view 246 (this role's write scope is a single record
under `docs/issue-246/reports/`, per `roles/execution-observation.json`)
None — this role performed no code authoring or fixing; it observed and
recorded verdicts against already-landed code, within that write scope.

## What did not work

None.
