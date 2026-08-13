---
code_under_review:
  - gates/finding_shape.py
  - gates/findings_due.py
  - gates/test_finding_shape.py
  - gates/test_findings_due.py
  - gates/test_consult_siblings.py
  - spawn.py
  - on-the-record/commands/consult.md
  - docs/specs/enforcement-boundary.md
  - docs/specs/reconciled-index.md
type: feature
breaking: false
# canonical: python3 gates/test_finding_shape.py && python3 gates/test_findings_due.py && python3 gates/test_consult_siblings.py — result: all cases passed (executed live this session, fenced output below)
verdict: pass
loop_state: landed
---

Subject: issue-1202

## What was done

canonical: docs/issue-1202/proposals/domain-findings-and-consult-siblings.md (read this session) — approved via the issue-level comments `APPROVE issue-1202/requirements-engineering` and `APPROVE issue-1202/implementation` (gh issue view 1202, read this session)

Built the approved phase-1 proposal's write set, committed at `0200bbc`:

- `gates/finding_shape.py` (new): `check_finding(path) -> list[str]`,
  hand-rolled frontmatter/section parser same family as
  `role_spec_shape.py`. Rejects a finding missing/empty `domain_rule`
  (the playbook citation), `## Evidence`, `## Impact`, or
  `## Proposed direction` — the shape gate requirement 2 asks for. Also
  adds `check_rate_bound(findings_root, role, session_id, bound=3)`:
  counts finding files under `<root>/<role>/` whose optional `session:`
  frontmatter field matches `session_id`, returns `None` under bound
  or a reject reason naming `session_summary_path()`'s summary-line
  file once the bound is reached (requirement 3, per-session not
  cumulative, matching the proposal's §4 resolution).
- `gates/findings_due.py` (new): `findings_due(target_root) -> list[dict]`
  / `format_report(due) -> list[str]`, mirroring
  `gates/need_detector.py`'s two-function shape exactly. Scans
  `docs/reports/findings/<role>/*.md` and every
  `docs/issue-*/reports/findings/<role>/*.md`, skips
  `*-session-summary.md`, skips any finding already carrying
  `relayed_to_issue:`. Pure classifier, no spawn, no `gh issue` write.
- `spawn.py`: added `spawn.py findings-due` CLI subcommand (prints
  `findings_due.format_report()` lines only — same
  `roles-due`/`needs-due` print-only shape at spawn.py:5254-5276 the
  survey cited). Added the three consult-sibling verbs (requirement 5):
  `_verb_cmd(verb, role, prompt_text, issue, cwd)` is the shared
  session-assembly/trace runner (reuses `_consult_cmd_and_env()`,
  `_consult_trace_path()`, `_persist_consult_raw_output()`,
  `_commit_consult_trace()` unchanged), with `_parse_verb_json()`
  generalizing `_parse_consult_verdict()` to a per-verb required key.
  `ideate_cmd`/`draft_cmd`/`review_cmd` are thin wrappers naming their
  verb, required return key (`options`/`draft`/`findings`), and prompt
  template. `_append_consult_trace()` gained an optional `verb: str =
  "consult"` parameter (default preserves `consult_cmd()`'s existing
  call site and trace-line format byte-for-byte); the four verbs now
  share one trace file family with a `verb=` field distinguishing
  lines, per proposal §6. CLI dispatch: `spawn.py ideate|draft|review
  <role> "<prompt>" [--issue <n>]`, same three-flat-subcommand shape
  proposal §6 chose over a nested `consult <verb>` form. `consult_cmd()`
  itself is untouched — the sibling verbs are new functions beside it,
  not a rewrite of it.
- `on-the-record/commands/consult.md`: documented the three sibling
  verbs (usage, return shape, shared no-branch/no-commit/no-PR
  contract), and added a `design-rationale:` frontmatter field this
  file had never carried (see `## What did not work`).
- `docs/specs/enforcement-boundary.md` + `docs/specs/reconciled-index.md`:
  registration rows for the two new gate modules
  (`gate-registration-guard.sh` requirement) and the regenerated index
  (`python3 gates/spec_index.py --update`, required alongside any
  `docs/specs/*` edit).
- Tests, case counts each backed by this session's own run below:
  `gates/test_finding_shape.py`, `gates/test_findings_due.py`,
  `gates/test_consult_siblings.py`.

## Acceptance check run this session

canonical: derived command output directly below (executed live this session)

derived: python3 gates/test_finding_shape.py && python3 gates/test_findings_due.py && python3 gates/test_consult_siblings.py

```
ok - test_finding_shape_accepts_complete_finding
ok - test_finding_shape_rejects_empty_evidence_section
ok - test_finding_shape_rejects_missing_domain_rule
ok - test_finding_shape_rejects_missing_evidence_section
ok - test_finding_shape_rejects_missing_file
ok - test_rate_bound_allows_under_bound
ok - test_rate_bound_ignores_session_summary_files
ok - test_rate_bound_is_per_session_not_cumulative
ok - test_rate_bound_rejects_fourth_finding_with_summary_path
9/9 passed
ok - test_findings_due_empty_when_no_findings_dir
ok - test_findings_due_lists_un_relayed_finding
ok - test_findings_due_reads_per_issue_variant
ok - test_findings_due_skips_relayed_finding
ok - test_findings_due_skips_session_summary_files
5/5 passed
ok - test_draft_cmd_returns_traced_draft_no_repo_writes
ok - test_ideate_cmd_returns_traced_options_no_repo_writes
ok - test_review_cmd_returns_traced_findings_no_repo_writes
ok - test_verb_cmd_wrong_key_triggers_retry_then_raises
4/4 passed
```

Covers acceptance checks 1-3: the shape gate + rate bound
(`test_finding_shape.py`), the board-reading integration
(`test_findings_due.py`), and the consult-sibling verbs returning traced
JSON with no repo side effect (`test_consult_siblings.py`). Acceptance
check 4 (live: one real role session records a genuine finding on a
fixture repo and the orchestrator relays it) needs a live `claude -p`
role session plus a separate orchestrator turn — MOCK: not run this
session (single headless turn, no second turn to relay from); the
machinery it would exercise is unit-tested above against the same
finding-file shape a live session would produce.

derived: python3 -c "import ast; ast.parse(open('spawn.py').read())"

```
(exits 0, no output — spawn.py parses clean after the edits)
```

## What did not work

`on-the-record/commands/consult.md`'s edit was first attempted without a
`design-rationale:` frontmatter field — `design-rationale-guard.sh`
refused it, since this pre-existing file (predates that guard) had never
carried the field. Expected: the doc edit lands with the file's existing
frontmatter shape; actual: the guard required a field the file had never
had. Fixed inline in the same edit before retrying — stays inside the
frozen write set (this file is explicitly listed), mechanical, one-off;
logged per the deviation-loop directive as inline, not filed.

An earlier draft of `gates/test_consult_siblings.py`'s retry-then-raise
case asserted `len(calls) == 2`, mirroring
`gates/test_consult_json_parse.py`'s own assertion for the analogous
`consult_cmd()` case. Expected: only the two session attempts get
counted by the patched `subprocess.run` fake; actual: run failed —

derived: python3 gates/test_consult_siblings.py (pre-fix)

```
AssertionError: expected exactly one retry, got 4
```

canonical: the fenced output directly above (executed live this session) — `_commit_consult_trace()`'s two `git add`/`git commit` calls go through the same globally-patched `spawn.subprocess.run` (module attribute patch, not an instance patch), so the count is 4, not 2.

Confirmed this is pre-existing behavior of the untouched `consult_cmd()`
path, not something this change broke —

derived: git stash && python3 gates/test_consult_json_parse.py; git stash pop

```
AssertionError: expected exactly one retry, got 4 attempts
```

canonical: the fenced output directly above (executed live this session, stashed this session's own diff and re-ran the pre-existing test against `476875e`) — the same pre-existing off-by-count already exists in `test_consult_json_parse.py` independent of this issue's changes.

Fixed this session's own new test's assertion to `== 4` rather than
touching the pre-existing file — `_commit_consult_trace`/`consult_cmd`
are outside this issue's frozen write set, and the pre-existing test's
own failure is a separate, already-latent defect this session did not
introduce and is not scoped to fix.

While iterating on that same fixture (before `_persist_consult_raw_output`
was correctly patched in the test), a stray run wrote real files under
this repo's own `docs/reports/consult-raw-failures/`, and a subsequent
`rm -rf` on that directory during cleanup deleted files that turned out
to be pre-existing, git-tracked evidence from a prior commit rather than
scratch this session had created. Expected: the directory held only
this session's stray test output; actual —

derived: git log --oneline -3 -- docs/reports/consult-raw-failures

```
3f63975 consult-trace: land pre-#1134 raw-failure evidence files (2026-08-13 02:22, cited in #1123/#1141)
```

canonical: the fenced output directly above (executed live this session) — those files were pre-existing committed evidence, not this session's scratch.

Restored via `git checkout -- docs/reports/consult-raw-failures` before
any commit in this session, and `git status` was re-checked clean on
that path before proceeding — no committed work was lost.

## Rationale for deviations

None — no divergence from the approved proposal's stated plan. The
`design-rationale:` frontmatter addition and the two `docs/specs/`
registration edits are mechanical gate-compliance fixes to files already
inside (or required alongside) the frozen write set, not a scope or
approach change.

## Open findings

None — no blocking finding from verify/qa/review is outstanding on this
branch as of this session.

## Doc-placement ladder

- No env var / config key / new dependency / migration / setup step was
  introduced — nothing to place in a handbook.
- No library-or-format choice over a named alternative and no changed
  public signature/wire format beyond what the proposal's own phase-1
  Ambiguities-resolved section already recorded — no new decisions
  section needed this phase.
- No benchmark or investigation numbers were produced — nothing beyond
  this record itself.
- `docs/specs/enforcement-boundary.md` gained the two new gate-module
  registration rows this delivery required, and
  `docs/specs/reconciled-index.md` was regenerated in the same commit —
  both landed at `0200bbc` already, listed in `code_under_review:` above.

## Hunt

warrant-hunter dispatched this session against this issue's diff before
phase-2 completion, per the hunt-cadence directive (stance rotates, not
chosen — this session's stance: state-mutation/race-condition).

closed_checks:
- check: rate-bound counting reads finding files' `session:` frontmatter
  field rather than mtime/ctime, so concurrent role sessions writing
  findings for the same role in the same wall-clock window cannot
  undercount or overcount each other's bound
  canonical: gates/test_finding_shape.py `test_rate_bound_is_per_session_not_cumulative` + `test_rate_bound_allows_under_bound` (executed live this session, fenced output above)
  code_sha: (see `code_under_review:` above, this record's own list)
