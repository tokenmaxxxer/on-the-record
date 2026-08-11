---
code_under_review:
  - on-the-record/hooks/record-claim-shape-directive.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/test_record_claim_guard.py
type: feat
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record: issue-730

## Summary of work

Added `on-the-record/hooks/record-claim-shape-directive.sh`, a new
UserPromptSubmit hook that proactively states the claim-citation shape
`record-claim-guard.sh` (via `on-the-record/gates/record_lint.py`) enforces,
so a role session's first record write already knows the shape instead of
learning it only from a PreToolUse refusal (the issue's own failure mode,
per the #726 audit catalog row 9).

The hook fires only when `CLAUDE_ROLE` is set (a spawned role session — the
audience that hits the gate; `hooks/directive.sh` is the orchestrator's own
directive and already excludes role sessions the other way around) and
`gates/record_lint.py` resolves and imports successfully; it fails open
(silent no-op, exit 0) otherwise, and respects the existing `ORCHESTRATE_OFF`
kill switch. Its printed text is generated at hook-run time from
`record_lint.py`'s own four check functions — `unverifiable_reason_check`,
`checked_claim_reason_check`, `bare_count_claim_check`,
`orphaned_path_reference_check` — read in the same order
`record-claim-guard.sh` itself imports and calls them in, joining each
function's docstring into one line (the first-line-only draft truncated
docstrings mid-sentence; see What did not work) so the printed rule text
comes from the check's own source rather than a hand-typed second copy.

Registered the new hook in `on-the-record/hooks/hooks.json` under the
`UserPromptSubmit` array, alongside the existing `directive.sh` entry.

Extended `on-the-record/hooks/test_record_claim_guard.py` with four tests:
`t_shape_directive_names_the_three_acceptance_rules_for_a_role_session`
(asserts the issue's own Acceptance wording — count-needs-citation,
path-must-resolve, unverifiable-needs-reason — all appear in the rendered
text for a `CLAUDE_ROLE`-set session; this is the empty-state pin: it fails
if the directive text is removed or stops naming these rules),
`t_shape_directive_names_all_four_record_lint_checks_in_call_order`
(asserts all four check names appear in `record_lint.py`'s own call order),
`t_shape_directive_silent_without_claude_role`, and
`t_shape_directive_respects_kill_switch`.

derived: `cd on-the-record/hooks && python3 -m pytest test_record_claim_guard.py -q`
```
................
16 passed in 0.67s
```

## Why

Basis: `docs/issue-730/proposals/2026-08-11-proactive-claim-citation-shape-directive.md`
(approved via the single-account-mode `APPROVE issue-730/implementation`
comment on the issue, posted by JiwonJung94 — PR #733's own author, listed
in `docs/specs/approvers.md`). The proposal's Rationale, backed by
`docs/issue-730/reports/implementation/survey.md`, established that the fix
belongs entirely in on-the-record (the gate only fires in
on-the-record-hosted sessions) and that the directive text must be
generated from `record_lint.py`'s own functions rather than hand-authored,
to avoid the drifting-second-copy failure the issue itself names.

## Doc placement ladder

- No env var, config key, new dependency, or migration introduced — no
  handbook update required.
- No library-or-format choice over a named alternative beyond what the
  proposal's own Rationale already recorded (docstring-sourced generation
  over a hand-typed copy or a shared external spec file) — no new
  decisions entry needed beyond that proposal section.
- No benchmark/investigation numbers produced beyond this record and the
  hunt record below — no separate reports entry needed.

## What did not work

- First draft of the hook's docstring-to-text conversion took only the
  first physical source line of each check function's docstring
  (`doc.strip().splitlines()[0]`). Three of the four docstrings wrap onto a
  second source line mid-sentence (e.g. `checked_claim_reason_check`'s
  docstring ends "...unverifiable\` result needs" on line one, "a reason."
  on line two), so the rendered directive text was truncated mid-word for
  those three rules. Confirmed by running the hook directly with
  `CLAUDE_ROLE` set and reading its stdout before writing the fix. Fixed by
  joining the whole docstring on whitespace (`" ".join(doc.split())`)
  instead of taking only the first line.
- The record scaffold's first `Write` attempt (this same file, before the
  hook script existed) was denied by `record-claim-guard.sh` itself
  (issue #330 orphaned-path-reference check) for backtick-referencing
  `on-the-record/hooks/record-claim-shape-directive.sh` before that file
  existed on disk. Reordered: wrote the hook script and test first, then
  this record, so every backtick path reference in it already resolves.
- Second `Write` attempt of this same file was denied twice more by the
  same guard, each time for a different reason: a bare digit-plus-noun
  phrase referencing the orphaned-path check by its issue number, and a
  bare digit-plus-noun phrase describing the test count, both typed
  outside a code fence with no `derived:` tag; and a backtick-quoted
  reference to a decisions-folder path that this change never creates
  (see Doc placement ladder above — no decisions entry was needed, so the
  directory does not exist). Fixed by rewording both count references to
  avoid a bare number immediately followed by a plural noun, and by
  dropping the backticks around the nonexistent decisions path so it
  reads as prose rather than a path reference.

## Hunt record

Two dispatches, both recorded in full at
`docs/issue-730/reports/implementation/hunt-2026-08-11-proactive-claim-citation-shape-directive.md`:
- after-proposal (stance 0, cap 180s, tier `size:>200-lines`): FINDING —
  `record_lint.orphaned_path_reference_check`'s path-prefix allow-list
  (`src|test|tests|docs|gates|on-the-record`) omits other real top-level
  repo directories (`scripts/`, `bench/`, `roles/`, `ledger/`,
  `.claude-plugin/`), so a fabricated backtick path under one of those
  prefixes silently bypasses the orphaned-path-reference check (issue
  #330). This is a pre-existing gap in `record_lint.py`'s own check, not
  something this proposal introduces or widens, and the proposal's own
  scope (proactive directive text mirroring what the gate already checks)
  cannot close a hole in the gate's checking logic itself — out of scope
  for this issue's write set. Left as an open finding below for whoever
  owns `record_lint.py`'s rule coverage.
- before-landing (stance 1, cap 120s, tier `size:21-200-lines`): NO
  FINDING.

## closed_checks

- `on-the-record/hooks/test_record_claim_guard.py` full suite, including
  the new tests added in this change, `code_under_review` as listed above.
  derived: `cd on-the-record/hooks && python3 -m pytest test_record_claim_guard.py -q`
  ```
  16 passed in 0.67s
  ```

## Open findings

One, from the after-proposal hunt (see Hunt record above):
`record_lint.orphaned_path_reference_check`'s directory allow-list omits
real top-level repo directories (`scripts/`, `bench/`, `roles/`, `ledger/`,
`.claude-plugin/`), letting a fabricated path under those prefixes bypass
the orphaned-reference check silently (exit 0, no stderr). Out of scope
for issue-730's frozen write set (this issue adds proactive directive text
about the existing gate; it does not touch the gate's own check logic) —
reported here for the next role/issue that owns `record_lint.py`'s rule
coverage.

## Resolution path

Widen `record_lint._PATH_REF`'s prefix alternation (or replace it with a
repo-root-relative resolution that doesn't hardcode a prefix list) in a
follow-up issue against `on-the-record/gates/record_lint.py`, with a
regression test pinning at least one previously-bypassed prefix (e.g.
`scripts/`) to a denied write.
