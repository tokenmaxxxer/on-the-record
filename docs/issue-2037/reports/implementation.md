---
Subject: issue-2037
code_under_review:
  - on-the-record/hooks/pr-preflight.sh
  - gates/design_artifacts_gate.py
loop_state: landed
type: implementation
breaking: false
verdict: pass
---

# Refuse a malformed one-line design-artifacts declaration loudly

## What was done

canonical: gh issue view 2037, run live this session.

Per the frozen Acceptance in #2037: a `design-artifacts:` tag line that
carries trailing content on the same line (e.g. `design-artifacts: a.md,
b.md, c.md`) previously fell through `_parse_artifacts_declaration`'s
tag regex (`^\s*[-*]?\s*design-artifacts\s*:\s*$`, requires nothing
after the colon) into `None` — byte-identical to an issue with no
declaration at all, so the existence gate silently no-op'd on an issue
that clearly intended a declaration (per the issue body: observed live,
tm-webfolio #5).

1. `on-the-record/hooks/pr-preflight.sh`: after the existing
   `_parse_artifacts_declaration(...)` call returns `None`, added an
   `else` branch. It scans the issue body for any line matching
   `design-artifacts\s*:\s*\S+` (tag with trailing content). On a
   match, it calls `deny(...)`, quoting the required tag+bullet/fence
   shape. Well-formed declarations (parsed non-`None`) and bodies with
   no `design-artifacts` token at all reach the new branch's loop with
   no match, so both fall through unchanged.
2. `gates/design_artifacts_gate.py`: mirrored the same detection as a
   standalone `malformed_declaration_line(body)` function (the issue
   names this file "if shared" — the hook's inline port and this module
   parse the same contract shape) and wired it into `check()`'s
   existing `declared is None` branch.
3. Tests: `test/test_design_artifacts_gate.py` gained a
   `MalformedDeclarationLineTest` class, a `check()`-level test
   (`test_declared_one_line_comma_form_refuses_loudly`), and a
   `parse_declaration` regression test pinning the one-line form's
   `None` result. `on-the-record/hooks/test_pr_preflight.py` gained
   three end-to-end `test_hook_*` cases driving the real
   `pr-preflight.sh` subprocess, one per Acceptance path named in the
   issue: malformed one-line, well-formed declaration, token-absent
   body.

canonical: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q, run live this session — result: 24 passed (full pasted output under "Test evidence" below).

## Why

The issue's Acceptance names exactly one shape to catch
(`design-artifacts:\s*\S+`, tag with trailing content) and requires the
other two paths stay byte-identical — a minimal `else` branch keyed off
the existing `None` return, rather than restructuring
`parse_declaration`/`_parse_artifacts_declaration` itself, is the
smallest change that satisfies both: it never touches the accepted-shape
parsing path at all, so well-formed and undeclared bodies provably
cannot regress (they were already reaching that `None`-vs-not-`None`
branch point unchanged; only the new `else` arm is new code). This is a
mechanical, single-shape parse-contract fix with no design decision
open (issue tags: `validity-consult-skip: trivial`,
`design-research-skip: mechanical`) — scouting was skipped per the
scout-directive's mechanical-issue skip condition, and no phase-1
survey/proposal round applies because the task that spawned this
session carries `CORE_BUILD_NOW=1` (build-now bypass, contract v3
s19a).

## Upstream / basis

- Issue #2037 body (Acceptance, empty state, provenance lines) —
  canonical: gh issue view 2037, run live this session.
- `gates/design_artifacts_gate.py` and its inline port in
  `on-the-record/hooks/pr-preflight.sh`, both from issue #2013 (phase
  2, artifact-gate existence check) — the contract shape and the
  `None`-on-no-tag byte-inert behavior this fix builds on.

## What did not work

Nothing else did not work.

## Acceptance verification

- malformed one-line design-artifacts refuses quoting the required shape — checked: on-the-record/hooks/test_pr_preflight.py::test_hook_denies_pr_when_design_artifacts_is_one_line_comma_form — result: pass: canonical: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q -k design_artifact, run live this session, 6 passed
- well-formed declaration behaves byte-identically — checked: on-the-record/hooks/test_pr_preflight.py::test_hook_allows_pr_when_design_artifacts_well_formed_2037 — result: pass: canonical: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q -k design_artifact, run live this session, 6 passed
- design-artifacts token absent behaves byte-identically — checked: on-the-record/hooks/test_pr_preflight.py::test_hook_allows_pr_when_design_artifacts_token_absent_2037 — result: pass: canonical: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q -k design_artifact, run live this session, 6 passed

## Open findings

None.

## Test evidence

canonical: python3 -m pytest -q -m "not slow", run live this session in the repo root — result: 2543 passed, 19 xfailed, 2 xpassed.

```
$ python3 -m pytest -q -m "not slow"
2543 passed, 19 xfailed, 2 xpassed in 42.54s
```

canonical: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q, run live this session in the repo root (slow tier, triggered by this diff touching `on-the-record/hooks/*.sh` and `on-the-record/hooks/test_*.py` per `.on-the-record/test-tiers.json`'s `trigger_change_classes`) — result: 24 passed.

```
$ python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q
24 passed in 1.12s
```

canonical: python3 test/test_design_artifacts_gate.py, run live this session in the repo root — result: 15 tests, all passing.

```
$ python3 test/test_design_artifacts_gate.py
...............
----------------------------------------------------------------------
Ran 15 tests in 0.002s

OK
```

canonical: python3 -m pytest -q -m slow, run live this session in the repo root — result: 1 failed, 105 passed, 2 xfailed.

```
$ python3 -m pytest -q -m slow
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
1 failed, 105 passed, 2 xfailed in 286.98s (0:04:46)
```

The one failure above is pre-existing and unrelated to this diff.

canonical: git stash && python3 -m pytest -q tests/test_spawn_directive_assembly.py -k test_without_flag_is_byte_identical_to_today && git stash pop, run live this session (this issue's write set reverted) — result: 1 failed, same failure reproduces.

```
$ python3 -m pytest -q tests/test_spawn_directive_assembly.py -k test_without_flag_is_byte_identical_to_today
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
1 failed in 1.15s
```

Root cause: this session's own shell environment carries
`CORE_BUILD_NOW=1` (the build-now bypass this record's own delivery
used), and that test asserts `CORE_BUILD_NOW` is absent from a copy of
`os.environ` it forwards to a subprocess — an ambient-environment
sensitivity in that test, not a regression from this issue's write set
(`on-the-record/hooks/pr-preflight.sh`,
`gates/design_artifacts_gate.py`, and their two test files). Fixing
that test is out of scope per the issue's frozen write set ("Touch
only hooks/pr-preflight.sh (+ its tests) and
gates/design_artifacts_gate.py if shared").
