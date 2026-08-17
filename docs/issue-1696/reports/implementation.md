---
code_under_review:
  - gates/requirement_met.py
  - gates/test_requirement_met.py
  - on-the-record/hooks/directive.sh
  - gates/acceptance_gate.py
loop_state: landed
type: feature
breaking: false
verdict: implemented
---

## What was done

Implemented the command-identity rule for executed-live provenance
(issue #1696): documented it in both the orchestrate/role directive text
(`on-the-record/hooks/directive.sh`, new COMMAND-IDENTITY paragraph in
the ACCEPTANCE FORMAT block) and the acceptance-format documentation
(`gates/acceptance_gate.py` module docstring), and added a deterministic
sub-check to `gates/requirement_met.py`'s grader: `_provenance_map()`
pairs each `check:`/`gate:` bullet with its `provenance:` continuation
line; `_recorded_commands_in_diff()` extracts `acceptance: <command> —
result: ...` citations from the PR diff's added lines (same shape
`gates/record_lint.py`'s `_EXECUTED_LIVE_CANONICAL` already
canonicalizes); `_command_identity_mismatch()` compares an
`executed-live` check's named command surface against the diff's
recorded command, normalized for environment-variable prefixes, and
flags a mismatch when a same-first-token candidate exists but none
matches exactly. `grade()` now blocks on this independent of the
semantic verdict, and `check()` surfaces `provenance`/
`command_identity_mismatch` in its advisory output.

## Why

Resolved problem from the issue: a builder proved `python3 -m
devdigest.cli` (PYTHONPATH-dependent) while the check named the
installed `python3 -m devdigest` line, which had no `__main__.py` and
could not run — an honest-looking record hid a command that would fail
every scheduled run. The fix makes command-identity a mechanical,
deterministic check rather than relying on a builder-blind reviewer to
catch it by chance.

## Upstream

basis: docs/issue-1696/proposals/2026-08-17-command-identity.md

## Rationale for deviations

None applicable — this implementation follows the proposal's own build
plan without divergence.

## What did not work

canonical: docs/reports/2026-08-17-hunt-command-identity-rule.md
warrant-hunt (dispatched end of phase 2) found: `_command_identity_mismatch`'s
same-first-token candidate filter silently missed a mismatch when the
artifact named `python devdigest.py` but the one recorded citation ran
`python3 devdigest.py` — no candidate shared the artifact's first token,
so the function returned no-mismatch instead of flagging the interpreter
difference. Fixed: when the diff carries exactly one recorded
`acceptance:` citation, compare it to the artifact directly instead of
first filtering by leading token; the first-token heuristic now only
applies when more than one citation exists to disambiguate among.
Regression test added: `t_command_identity_flags_leading_token_mismatch_with_single_citation`.

canonical: https://github.com/tokenmaxxxer/on-the-record/pull/1699#issuecomment-5311562204
Independent builder-blind review of PR #1699 found two further defects
in `_command_identity_mismatch` where the grader contradicted its own
documented rule: (1) `_strip_env_prefix` normalized an env-prefix-only
difference (`PYTHONPATH=src python3 -m devdigest` vs `python3 -m
devdigest`) into a match, even though env-prefix is the exact crutch
the rule forbids — probed `mismatch=False` when it should be `True`.
(2) with >=2 recorded citations, a `cd src && ...`/`bash -c '...'`
wrapped command's literal first token (`cd`/`bash`) never matched the
artifact's first token, so it silently fell through the "no candidate"
escape hatch regardless of whether the wrapped command actually
matched — probed `(False, False)` for both a would-match and a
would-mismatch wrapped command. Fixed: added `_strip_wrapper_head()`
(strips a leading `cd <path> && `/`bash -c`/`sh -c` head, quote-stripped)
used only for candidate-token matching and for the final identity
comparison (cd/shell wrapping is not part of a command's identity);
`_strip_env_prefix()` is now used only to find first-token candidates,
never for the final equality check, so an env-prefix-only difference
still flags. Regression tests added:
`t_command_identity_flags_env_prefix_only_difference`,
`t_command_identity_strips_cd_wrapper_head_for_candidate_matching`,
`t_command_identity_flags_mismatch_inside_cd_wrapper_head`.

## Confirmation run

canonical: python3 -m pytest gates/test_requirement_met.py -q
acceptance: python3 -m pytest gates/test_requirement_met.py -q — result: PASS
```
22 passed in 0.80s
```

canonical: python3 -m pytest gates/test_acceptance_gate.py -q
acceptance: python3 -m pytest gates/test_acceptance_gate.py -q — result: PASS
```
13 passed in 0.83s
```

Test-tier directive (issue #1518): this repo carries
`.on-the-record/test-tiers.json`. Fast tier ran per that config:

canonical: python3 -m pytest -q -m "not slow"
acceptance: python3 -m pytest -q -m "not slow" — result: FAIL
```
2198 passed, 19 xfailed, 2 xpassed, 1 failed in 23.47s
```

The one failure (test_sweep_call_budget, a gh-call-count assertion in
tests/test_gh_quota_guard.py, unrelated to this issue's files) pre-dates
this change:

canonical: git stash && python3 -m pytest -q tests/test_gh_quota_guard.py -k test_sweep_call_budget && git stash pop
```
same assertion failure reproduced against unmodified main before this
change's files were touched
```

This change touches `on-the-record/hooks/directive.sh`, matching
`on-the-record/hooks/*.sh` in `trigger_change_classes`, so the slow tier
also ran:

canonical: python3 -m pytest -q -m slow
acceptance: python3 -m pytest -q -m slow — result: PASS
```
100 passed, 2 xfailed in 477.65s (0:07:57)
```

derived: git grep -n "COMMAND-IDENTITY" on-the-record/hooks/directive.sh gates/acceptance_gate.py
```
gates/acceptance_gate.py:8:COMMAND-IDENTITY (issue #1696): `provenance: executed-live`로 표시한
on-the-record/hooks/directive.sh:301:- COMMAND-IDENTITY (issue #1696): a \`check:\` bullet with
```

## Doc placement

No env var, config key, new dependency, migration, or setup step was
introduced. No public signature or wire format changed beyond what the
proposal's Rationale already records. No benchmark/investigation
numbers beyond the confirmation run above. No additional doc-placement
entries needed for this change.

## Open findings

None.

## Hunt

warrant-hunter dispatched at end of phase 2 (background, result
consumed before commit per contract v3 s22 — no delegated work left
unconsumed across the turn boundary).

closed_checks:
- command-identity mismatch fixture (mismatched vs matching vs
  no-citation vs executed-unit provenance), covered in
  gates/test_requirement_met.py — code_sha: see code_under_review above;
  graded via the confirmation run.
- leading-token mismatch with a single recorded citation, covered in
  gates/test_requirement_met.py — code_sha: see code_under_review above;
  graded via the confirmation run.

resolved_findings:
- docs/reports/2026-08-17-hunt-command-identity-rule.md — same-first-token
  filter silently missed a leading-interpreter-token mismatch
  (`python` vs `python3`) when only one citation existed to compare
  against; fixed in gates/requirement_met.py's
  `_command_identity_mismatch` (single-citation case now compares
  directly) and covered by a new regression test — see "What did not
  work" above.
- canonical: https://github.com/tokenmaxxxer/on-the-record/pull/1699#issuecomment-5311562204
  independent builder-blind review found (1) env-prefix-only
  differences normalized into a false match, (2) cd/wrapper-headed
  recorded commands silently escaping the candidate filter with
  >=2 citations; both fixed in gates/requirement_met.py and covered by
  three new regression tests — see "What did not work" above.
