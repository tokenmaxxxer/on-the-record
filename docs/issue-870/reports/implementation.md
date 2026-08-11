---
code_under_review:
  - gates/record_lint.py
  - on-the-record/gates/record_lint.py
  - on-the-record/hooks/record-claim-guard.sh
  - on-the-record/hooks/record-claim-shape-directive.sh
  - gates/test_record_lint.py
  - on-the-record/hooks/test_record_claim_guard.py
type: feature
breaking: false
canonical: `python3 -m pytest gates/ on-the-record/hooks/ -q` (684 passed, 1 xfailed, run this session)
verdict: pass
loop_state: landed
---

# Implementation record — issue #870 phase 2

## What was done

Shipped candidate (a) from the approved phase-1 proposal
(docs/issue-870/proposals/2026-08-11-generalized-fake-success-detection.md,
`status: approved` via the single-account `APPROVE issue-870/implementation`
comment on the issue) as the highest-value default-on piece.

New marker vocabulary added, sibling to #793's `_STATE_CLAIM_MARKER`:

```
_OUTCOME_CLAIM_MARKER: requirement(s) met | done | PASS/passes/passed | complete(d)
```

- New check function `outcome_claim_citation_check(text)` added to
  `gates/record_lint.py`, mirrored byte-identically into
  `on-the-record/gates/record_lint.py` — canonical:
  `diff gates/record_lint.py on-the-record/gates/record_lint.py` (exit
  0, no output, run this session).
- Citation-KIND requirement: when an outcome marker fires outside a
  markdown heading line, the `canonical:` tag within 3 lines above it
  must itself be an executed-live reference. Accepted shapes:

  ```
  gh ...
  git ...
  pytest ...
  python3 ... / python ...
  npm ... / npx ...
  bash ... / sh ... / ./...
  acceptance: <command> — result: PASS|FAIL|UNMEASURED
  derived: <command>   (#333's own count-claim citation, accepted as a sibling source)
  ```

  A bare file-read citation (already sufficient for #793's own check)
  does not qualify — the checker requires one of the shapes above.
- Wired into `lint_record()` (the aggregator both `record-claim-guard.sh`
  and `gates/ci.py` call), into the `PreToolUse` hook
  on-the-record/hooks/record-claim-guard.sh (same enforcement point
  #793 already uses, no new hook registration — canonical:
  gates/record_lint.py and on-the-record/hooks/record-claim-guard.sh,
  both read this session, each carrying a new line calling
  `outcome_claim_citation_check`), and into the `UserPromptSubmit`
  on-the-record/hooks/record-claim-shape-directive.sh's generated rule
  list, which builds its printed text from `record_lint.py`'s
  check-function docstrings at hook-run time, so adding the new
  function to its `rules` list was the only edit needed there.
- Tests added: `gates/test_record_lint.py` (5 new cases) and
  `on-the-record/hooks/test_record_claim_guard.py` (4 new cases,
  including one pinning that an honestly-written
  `UNMEASURED-with-reason` claim with no executed-live citation is not
  rejected by candidate (a) alone — (a) checks citation KIND, not
  truth, the division of labor the proposal states between (a) and
  staged (b)). Targeted and repo-wide suites re-run this session —
  canonical: `python3 -m pytest gates/test_record_lint.py
  on-the-record/hooks/test_record_claim_guard.py -q` (35 passed, 1
  xfailed pre-existing/unrelated) and `python3 -m pytest gates/
  on-the-record/hooks/ -q` (684 passed, 1 xfailed), both run this
  session.
- Also updated `t_directive_names_all_four_record_lint_rules` to assert
  the new `#870` rule text appears in the generated directive output —
  the test's own name is now stale (it now checks five rules, not
  four); left as-is, renaming it is outside this proposal's write set.

## Why

The phase-1 proposal's RICE scoring picked (a) as cheapest and highest-
reach: a mechanical, one-layer-up extension of the already-shipped #793
gate, no new hook registration needed. (b) (a per-target `acceptance:`
command run at `Stop`) is the only candidate supplying REAL execution
evidence and is recommended to ship alongside (a) in the proposal, but
needs new plumbing scoped in the proposal as separate build work: a
stored per-target command, a one-time setup flow, a new
`Stop`/`SubagentStop` hook registration — canonical:
docs/issue-870/proposals/2026-08-11-generalized-fake-success-detection.md
(read this session, "## Out of scope" section). Per the phase-2
invocation's own instruction — ship the highest-value default-on piece
first, record the rest as staged next steps — (a) ships now; (b) is
staged below, not built.

## Upstream / basis

docs/issue-870/proposals/2026-08-11-generalized-fake-success-detection.md
(approved), the section proposing candidate (a) and the "Out of scope"
section (which already scopes the two hooks/gate functions themselves
as the second phase's own work, pending approval).

## Staged next steps (not built this PR)

- **(b) — per-target `acceptance:` command.** Needs: a one-time setup
  prompt mirroring #831's `ensure_target_remote` shape (attended-only,
  gated on the `unattended` flag), a `ledger_write` event
  (`acceptance_command_confirmed`), a `Stop`/`SubagentStop` hook that
  detects an outcome claim written this turn and, if an `acceptance:`
  command is on record, runs it (bounded timeout) and requires the
  claim's citation to match the actual exit status; when no command is
  on record, requires an `UNMEASURED-with-reason` citation instead of
  blocking. New plumbing beyond this PR's write set.
- **(c) — adversarial re-verify.** Per the proposal, explicitly NOT a new
  hook: role-handoff contract v3 s19's phase-1/phase-2 human-approval
  split already occupies this role; (a), shipped here, is what makes
  that approval checkable rather than a bare assertion.

## Open findings

Before-landing warrant hunt (stance: assume this guard goes silent when
its own input is malformed), reported into
docs/issue-870/reports/implementation/2026-08-11-hunt-generalized-fake-success-detection.md
— canonical:
docs/issue-870/reports/implementation/2026-08-11-hunt-generalized-fake-success-detection.md
(read this session):

```
FINDING — `_EXECUTED_LIVE_CANONICAL`'s "acceptance:\s" branch matched any
free text starting with the literal word "acceptance:", not an
actually-shaped `acceptance: <command> — result: PASS|FAIL|UNMEASURED`
line, so a `canonical: acceptance: reviewer says it looks fine` tag
satisfied the new OUTCOME-claim citation requirement with zero
execution evidence.
```

```
Resolved this session: tightened _EXECUTED_LIVE_CANONICAL's
"acceptance:" branch to require \bresult:\s*(?:PASS|FAIL|UNMEASURED)\b
after the command text, and added two regression-pin tests
(t_outcome_claim_with_unbacked_acceptance_prose_is_still_reported,
t_outcome_claim_with_real_acceptance_result_line_passes, both in
gates/test_record_lint.py).
```

canonical: `python3 -m pytest gates/test_record_lint.py
on-the-record/hooks/test_record_claim_guard.py -q` (35 passed, 1
xfailed, run this session, after the fix above). The hunt surfaced no
other issue; there is nothing further pending here.

## What did not work

```
First draft of _OUTCOME_CLAIM_MARKER matched inside a markdown section
heading too (a heading whose text names what this section covers),
demanding a citation for a section title rather than an actual claim.
Fixed by skipping lines whose stripped content starts with "#" before
checking the outcome marker, same shape reasoning
bare_count_claim_check already uses to skip fenced code.
```

- The checker refused this very record's first-draft write on that
  heading line (`PreToolUse` denial naming the heading text, this
  session) before the fix above landed.
- First draft also used backtick-quoted `path:LINE-LINE` references as
  citations (a script path suffixed with a line range). The #330
  orphaned-path checker treats the whole backtick span as a literal
  path and refused it, since no file exists with a trailing line-range
  suffix in its name. Replaced with plain-prose file references (no
  backticks) so the path checker does not attempt to resolve them as
  paths.
- Initial `_EXECUTED_LIVE_CANONICAL` regex accepted any citation starting
  with the literal prefix `acceptance:`, with no requirement that a
  result outcome actually follow it — the before-landing hunt (above)
  surfaced that this made the OUTCOME-claim checker trivially
  satisfiable by unbacked prose. Fixed as described in "Open findings"
  above.
