---
code_under_review:
  - on-the-record/hooks/record-claim-shape-directive.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/test_record_claim_guard.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Added `on-the-record/hooks/record-claim-shape-directive.sh`, a new
UserPromptSubmit hook that states record-claim-guard.sh's citation
shape proactively, before the PreToolUse gate ever fires (issue #730,
per the approved proposal at
docs/issue-730/proposals/2026-08-11-proactive-claim-citation-shape-directive.md).

The hook fires only when `CLAUDE_ROLE` is set (a spawned role session —
the same audience `record-claim-guard.sh` gates) and
`gates/record_lint.py` is importable from the resolved gates directory
(same resolution `record-claim-guard.sh` already uses); it silently
no-ops otherwise, and honors the `ORCHESTRATE_OFF` kill switch.

The printed `<record-claim-citation-directive>` block names, in
`record_lint.py`'s own check order, the four rules
`record-claim-guard.sh` enforces: bare count/ratio claim (issue #333),
`unverifiable:` line (issue #310), `checked: ... — result: unverifiable`
line (issue #331), backtick-quoted path reference (issue #330). Each
rule's stated text is the check function's own docstring
(`bare_count_claim_check.__doc__`, etc.), pulled at hook-run time via
`import record_lint` — not a hand-typed second copy — so a future
docstring change on the check function changes what this directive
states too.

Registered in `on-the-record/hooks/hooks.json` under `UserPromptSubmit`,
alongside the existing `directive.sh` entry.

Added four tests to `on-the-record/hooks/test_record_claim_guard.py`:
`t_directive_names_all_four_record_lint_rules` (asserts the rendered
text names all four rule shapes and their issue numbers — the issue's
own Acceptance wording), `t_directive_is_silent_without_claude_role`,
`t_directive_fails_open_without_orchestrate_off_flag_set_wrong`, and
`t_directive_shows_visible_notice_on_renamed_check_function` (added
after the before-landing hunt below).

## Why

record-claim-guard.sh's citation shape was stated in no proactive
directive text, so every role learned it only from refusal — per the
#726 audit catalog row 9, the single most frequent gate-refusal on
2026-08-11. This closes that gap the way the approved proposal
specified: generated from `record_lint.py`'s own check functions, not
a second drifting prose copy.

## Upstream

Based on: docs/issue-730/proposals/2026-08-11-proactive-claim-citation-shape-directive.md

## What did not work

- Wrote the `derived:`-tagged test-name path
  on-the-record/hooks/test_record_claim_guard.py::t_directive_names_all_four_record_lint_rules
  as a backtick-quoted reference in this record's first draft; the
  `::function_name` suffix made record-claim-guard.sh's own
  orphaned-path check (issue #330 mirror) treat it as an unresolved
  path and deny the write. Fixed by dropping backticks off any
  `::function`-suffixed reference below.
- First attempt to write this record ran with the Bash tool's cwd left
  inside `on-the-record/hooks` from prior test runs; `approval-gate.sh`
  resolves `docs/specs/approvers.md` relative to the tool call's `cwd`,
  so the write was refused there even though the file exists at the
  outer repo root. Re-ran the write from the outer repo root cwd and it
  passed.
- Also backtick-quoted the hunt record's own path (a
  docs/issue-730/reports/... reference), and that path did not yet
  exist at write time — `record-claim-guard.sh` denied it as an
  orphaned reference. Fixed by writing that path without backticks.

## Hunt (before-landing, issue #730 warrant directive)

Dispatched a `warrant-hunter` on stance 0 ("assume the gate/directive
just touched is bypassable — find the bypass"), cap 120s. Its record
landed at
docs/issue-730/reports/implementation/hunt-2026-08-11-proactive-claim-citation-shape-directive.md
(a repo-level board-gate refused the hunter's originally-specified
docs/issue-730/reports/hunt-2026-08-11-proactive-claim-citation-shape-directive.md
path as belonging to another role's record area — filed at the nearest
permitted path instead).

closed_checks:
- check: before-landing hunt stance 0 (bypass-of-the-gate-just-touched)
  code_sha: same as code_under_review above (working-tree files, no
  commit sha assigned to this uncommitted transition)
  finding: renaming any of the four hard-coded
  `record_lint.<check_fn>` attribute references silently produced the
  same empty, exit-0 output as every legitimate fail-open path (no
  CLAUDE_ROLE, missing gates dir, ORCHESTRATE_OFF) — indistinguishable
  from a healthy no-op, contradicting the header comment's drift-safety
  claim.
  resolution: wrapped the rule-table build and print loop in a
  try/except AttributeError that now prints a visible
  `<record-claim-citation-directive>` fallback notice naming the
  broken attribute instead of vanishing silently. Reproduced fixed
  behavior directly (see command below) and added regression test
  `t_directive_shows_visible_notice_on_renamed_check_function`.

```
$ cd on-the-record && cp gates/record_lint.py /tmp/record_lint.py.bak && \
  python3 -c "s=open('gates/record_lint.py').read(); open('gates/record_lint.py','w').write(s.replace('def bare_count_claim_check','def bare_count_claim_check_renamed',1))" && \
  cd hooks && echo '{}' | CLAUDE_ROLE=worker bash record-claim-shape-directive.sh; echo "EXIT=$?"; \
  cp /tmp/record_lint.py.bak ../gates/record_lint.py
<record-claim-citation-directive>
record-claim-shape-directive.sh could not generate the citation
shape text from gates/record_lint.py (module 'record_lint' has no attribute 'bare_count_claim_check') — record_lint.py's
check functions likely changed name/shape. record-claim-guard.sh
still enforces the shape even though this directive can't state it.
</record-claim-citation-directive>
EXIT=0
```

## Acceptance verification

- The shared role directive states the claim-citation shape — checked:
  test_record_claim_guard.py::t_directive_names_all_four_record_lint_rules
  — result: pass, derived: `cd on-the-record/hooks && python3 -m pytest . -q`

```
$ python3 -m pytest . -q
........................................................................ [ 40%]
........................................................................ [ 81%]
................................                                         [100%]
176 passed in 13.70s
```

## Open findings

None outstanding — the single before-landing hunt finding above is
resolved in this same commit and closed above.
