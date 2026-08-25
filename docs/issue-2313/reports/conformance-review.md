---
issue: 2313
role: conformance-review
loop_state: reported
upstream:
  - path: PR #2336 (branch issue-2313/implementation)
    sha: 18cd271919f0960134b656a166f55953448b21fd
subject: PR #2336 (tokenmaxxxer/on-the-record) — compound `cd X && CMD`/`;` check_runner classification fix + `--repo` semantics clarification for issue #2313
test: issue-2313#Acceptance (gate / empty state / provenance) + issue-2313 body items 1-2
result: passed
assertedBy: issue-2313/conformance-review session (builder-blind), 2026-08-25
---

# issue-2313 — conformance-review record

## What was done

canonical: `git fetch origin pull/2336/head:pr-2336` + `git worktree add
/tmp/pr2336-wt pr-2336` (PR #2336 head `18cd271919f0960134b656a166f55953448b21fd`,
base commit `907428d9ab189c36053813fe59ff403467f2a2ba`), plus `gh issue view
2313` and `gh pr view 2336` / `gh pr diff 2336` — every citation, test run,
and live probe below was read/executed this session, independent of the
builder's own account in
`18cd271919f0960134b656a166f55953448b21fd:docs/issue-2313/reports/implementation.md`
(read only to locate what to independently re-check, never taken on faith).

Requirement extraction (conformance-review-requirement-extraction): issue
#2313's body has two independently-numbered obligations (compound-command
classification, item 1; `--repo` semantics clarification, item 2 — rule
1, already split by the issue author). The `## Acceptance` block's
`provenance` line bundles two obligations with `;` ("the consumer's exact
compound check re-run post-fix showing test-classification and PASS" and
"the misleading `--repo` case demonstrated pre-fix and the clarified
message post-fix") — split into R4 and R5 per rule 1, each stated as
dependent on its corresponding fix (R1 and R2 respectively) per rule 5.
The `gate: gates/test_check_runner.py` line and the trailing
`infrastructure/no-direct-requirement` tag are not themselves checkable
obligations (no observable success condition beyond naming the governing
test file — rules 2 and 3): treated as the verification-method pointer
for R1 and R3, not a separate R-item.

acceptance: `cd /tmp/pr2336-wt && git diff --stat 907428d9ab1~1...18cd2719`
— result:
```
.orchestrate-hook-fires.log                                              |   2 +
docs/issue-2313/reports/implementation.md                                | 244 ++++++++++++++++++
docs/issue-2313/reports/implementation/2026-08-25-hunt-compound-check-classification.md | 44 +++++
docs/issue-2313/reports/implementation/deviation-log.md                  |   5 +
gates/check_runner.py                                                    |  54 ++++--
gates/test_check_runner.py                                               |  75 +++++++
on-the-record/directive/merge-gates.md                                   |  10 +-
7 files changed, 421 insertions(+), 13 deletions(-)
```
small enough (2 code files plus 1 directive file with requirement-bearing
hunks) that every requirement-bearing hunk was read in full — every
citation below was independently opened and, where executable, rerun in
the worktree — so conformance-review-sampling-derivation is not
applicable (see skill-verdict below).

### R1 — Body item 1: compound `cd X && CMD`/`cd X; CMD` classifies by the final real command

- requirement: "Compound `cd X && CMD` shapes should classify by the
  final real command (split on `&&`/`;`)."
- spec_ref: issue #2313 body, item 1
- verdict: **Present**
- canonical: `18cd2719:gates/check_runner.py:121-125` (read this session):
```
_COMPOUND_SEP = re.compile(r"&&|;")


def _final_segment(cmd: str) -> str:
    parts = _COMPOUND_SEP.split(cmd)
    return parts[-1].strip() if len(parts) > 1 else cmd
```
- canonical: `18cd2719:gates/check_runner.py:167,173` — `classify_cmd =
  _final_segment(cmd)` feeds every classification branch (`test`,
  bare-`.py`-through-pytest wrap around line 189, `file-existence`
  fallback around line 202, and `_artifact_touched(classify_cmd,
  declared)` at line 173) instead of the raw compound string.
- canonical: `18cd2719:gates/check_runner.py:248-256` — `run_checks()`
  routes any command matching `_COMPOUND_SEP` through
  `subprocess.run(chk["command"], shell=True, ...)` instead of
  `shlex.split` + argv-exec, since `cd` is a shell builtin and cannot be
  exec'd directly — required for the compound command to actually run,
  not just classify correctly.
- canonical: independently reran, this session, in `/tmp/pr2336-wt`
  against a stand-in `/tmp/repro2/frontend/scripts/check-hex-tokens.mjs`
  (`process.exit(0);`):
```
$ python3 -c "
import sys; sys.path.insert(0, 'gates')
import check_runner as cr
from pathlib import Path
section = '\n- check: \`cd frontend && node scripts/check-hex-tokens.mjs\`\n'
checks = cr.parse_checks(section)
print('classified:', checks)
print('results:', cr.run_checks(Path('/tmp/repro2'), checks))
"
classified: [{'type': 'test', 'raw': '`cd frontend && node scripts/check-hex-tokens.mjs`', 'command': 'cd frontend && node scripts/check-hex-tokens.mjs'}]
results: [{'check': '`cd frontend && node scripts/check-hex-tokens.mjs`', 'type': 'test', 'command': 'cd frontend && node scripts/check-hex-tokens.mjs', 'status': 'pass', 'output': ''}]
```
  `type: 'test'`, not `file-existence` — matches the issue's own worked
  example exactly.
- canonical: independently reran, this session, `18cd2719:gates/test_check_runner.py`
  (derived: `python3 gates/test_check_runner.py`, full transcript fenced
  under R3 below) — `t_compound_cd_command_classifies_as_test_not_file_existence`
  (line 334) and `t_compound_semicolon_command_classifies_as_test_not_file_existence`
  (line 346) both `ok`.
- rationale: Test (verification-method-selection rule 4 — existing
  coverage reused and rerun rather than re-derived) plus an independent
  live Demonstration against a fresh stand-in script this session (fence
  above), since the issue's own worked example names a specific script
  path this checkout does not carry.

### R2 — Body item 2: `--repo` semantics clarified for target-repo (consumer) use

- requirement: "Clarify the directive and/or the usage string" that
  `--repo` means the repo whose issue/PR is being checked, not always
  the plugin's own `${CHECKOUT}`.
- spec_ref: issue #2313 body, item 2
- verdict: **Present**
- canonical: `main:gates/check_runner.py:382` (pre-fix, read this
  session) — `body = gh_rest.fetch_issue_body(repo, issue)`, confirming
  the issue's own `check_runner.py:381` citation: `--repo`'s `repo` is
  the `cwd` used for every `gh` call, i.e. the repo whose issue is
  fetched.
- canonical: `18cd2719:gates/check_runner.py:21-29` (module docstring)
  and `:418-419` (usage string) vs. `main:gates/check_runner.py:16` and
  `:375` (pre-fix) — pre-fix carried no target-repo warning at all
  (`[--repo <경로>]` with no disambiguation); post-fix adds the explicit
  "on-the-record 자신의 PR을 orchestrate 할 땐 ... target-repo(소비
  저장소) 작업을 orchestrate 할 땐 절대 `${CHECKOUT}`이 아니라" clause to
  both the docstring and the usage string, independently confirmed via
  `git show main:gates/check_runner.py` vs. the worktree copy, this
  session.
- canonical: `18cd2719:on-the-record/directive/merge-gates.md:41-50` vs.
  `main:on-the-record/directive/merge-gates.md:38-44` (pre-fix) — the
  `ACCEPTANCE CHECK-RUNNER AT LANDING` bullet's worked example changes
  from `--repo ${CHECKOUT}` (no warning) to `--repo <repo>` plus the same
  target-repo clause, independently diffed this session.
- rationale: Inspection (verification-method-selection rule 1 — a
  static, textual presence-and-accuracy property) for the clarified text
  itself; Analysis, not a live Demonstration (rule 2), for why the
  clarification is correct — reproducing the actual "target-repo work
  misled into reading the plugin's own issue" failure live would require
  a second consumer-repo checkout not available in this review session,
  so the code path (`repo` param flows straight into every `gh` call's
  `cwd`, confirmed above) was traced instead of re-triggered.

### R3 — Acceptance empty state: a simple non-compound command classifies unchanged

- requirement: "empty state: a simple non-compound command —
  classification unchanged."
- spec_ref: issue #2313 Acceptance, line `empty state`
- verdict: **Present**
- canonical: `18cd2719:gates/check_runner.py:124-125` —
  `_final_segment()` returns `cmd` unchanged whenever `_COMPOUND_SEP`
  finds no separator (`len(parts) > 1` guards the split), so a
  non-compound command's `classify_cmd` is byte-identical to the pre-fix
  `cmd`.
- canonical: `18cd2719:gates/test_check_runner.py:395-402`,
  `t_simple_noncompound_command_classification_is_unchanged` — asserts
  both the classified type and the `command` field are unchanged for
  `` `node --check dist/bundle.js` ``.
- canonical: independently reran this session in `/tmp/pr2336-wt`,
  derived: `python3 gates/test_check_runner.py`:
```
$ python3 gates/test_check_runner.py
ok - t_all_judgment_checks_do_not_abort_run_checks_when_pre_filtered
ok - t_artifact_smoke_check_actually_runs_and_fails_on_a_broken_artifact
ok - t_artifact_smoke_check_passes_when_the_artifact_parses
ok - t_bare_artifact_path_without_measurement_language_stays_file_existence
ok - t_bare_conventional_filename_and_dotfile_still_classify_as_file_existence_and_fail
ok - t_bare_path_still_classifies_as_file_existence
ok - t_bare_py_gate_path_is_wrapped_to_run_through_pytest
ok - t_classification_is_byte_identical_without_a_declaration
ok - t_compound_cd_command_actually_runs_through_a_shell_and_passes
ok - t_compound_cd_command_classifies_as_test_not_file_existence
ok - t_compound_cd_command_with_declared_artifact_still_classifies_as_artifact_smoke
ok - t_compound_command_final_bare_py_segment_is_wrapped_through_pytest
ok - t_compound_semicolon_command_classifies_as_test_not_file_existence
ok - t_cross_family_bare_identifier_classifies_as_judgment_not_file_existence
ok - t_declared_artifact_command_classifies_as_artifact_smoke
ok - t_format_comment_lists_skipped_judgment_items_outside_the_pass_total
ok - t_format_comment_names_the_artifact_smoke_type
ok - t_format_no_checks_comment_reports_judgment_items_distinctly
ok - t_genuinely_missing_path_shaped_artifact_still_classifies_as_file_existence_and_fails
ok - t_measurement_language_prose_bullet_classifies_as_judgment_not_file_existence
ok - t_node_command_without_declaration_classifies_as_test_not_file_existence
ok - t_npx_deno_bun_are_on_the_interpreter_allowlist
ok - t_py_gate_path_with_explicit_interpreter_is_left_alone
ok - t_run_checks_records_a_failure_instead_of_crashing_on_unexecutable_command
ok - t_simple_noncompound_command_classification_is_unchanged
ok - t_source_level_command_stays_test_even_with_a_declaration
ok - t_unclassifiable_check_is_still_judgment_and_refused_by_the_runner
ok - t_work_in_english_skill_name_classifies_as_judgment_not_file_existence
28/28 passed
```
- canonical: independently reran this session in `/tmp/pr2336-wt`, full
  `gates/` suite regression check, derived: `python3 -m pytest gates/ -q`:
```
$ python3 -m pytest gates/ -q
970 passed, 8 xfailed in 65.75s (0:01:05)
```
  no regression versus the builder's own claimed count in
  `18cd2719:docs/issue-2313/reports/implementation.md:189-194`,
  independently reproduced rather than copied.
- rationale: Test (rule 4 — existing gate `gates/test_check_runner.py`
  named directly by the Acceptance block's `gate:` line, reused and
  rerun rather than re-derived).

### R4 — Acceptance provenance, obligation 1: consumer's exact compound check re-run post-fix, executed-live, test-classification + PASS

- requirement: "the consumer's exact compound check re-run post-fix
  showing test-classification and PASS" (Acceptance `provenance`,
  obligation 1; depends on R1's fix existing).
- spec_ref: issue #2313 Acceptance, line `provenance`, clause 1
- verdict: **Present**
- canonical: this session's own independent rerun (fenced under R1
  above) against a freshly-created stand-in script at
  `/tmp/repro2/frontend/scripts/check-hex-tokens.mjs` (the consumer's
  real script is not in this checkout) — `classified: [{'type': 'test',
  ...}]`, `results: [{..., 'status': 'pass', ...}]` — executed-live this
  session, not copied from the builder's own record.
- rationale: Demonstration (verification-method-selection rule 3 — a
  qualitative functional claim: the exact reported shape now classifies
  and executes correctly), performed independently rather than trusting
  the builder's pasted transcript in
  `18cd2719:docs/issue-2313/reports/implementation.md:196-214`, which
  this evidence corroborates but does not substitute for.

### R5 — Acceptance provenance, obligation 2: misleading `--repo` case demonstrated pre-fix, clarified message demonstrated post-fix

- requirement: "the misleading `--repo` case demonstrated pre-fix and
  the clarified message post-fix" (Acceptance `provenance`, obligation
  2; depends on R2's fix existing).
- spec_ref: issue #2313 Acceptance, line `provenance`, clause 2
- verdict: **Present**
- canonical: independently reproduced this session —
  `git show main:gates/check_runner.py` (pre-fix: `[--repo <경로>]`, no
  target-repo warning, matches the issue's reported confusion) vs.
  `18cd2719:gates/check_runner.py` (post-fix: explicit target-repo
  clause) — both citations pinned under R2 above; same comparison
  independently rerun against `on-the-record/directive/merge-gates.md`
  (`main` vs. `18cd2719`), also pinned under R2.
- rationale: Analysis (verification-method-selection rule 2) — this
  obligation is a documentation fix for a misleading example, not a
  runtime behavior change (`--repo`'s actual semantics were already
  "the checked issue/PR's own repo," confirmed under R2); "demonstrated
  pre-fix"/"post-fix" is satisfied by the textual before/after
  comparison re-derived independently above, since live-reproducing a
  second consumer session being misled by the old text is not a
  condition this review session can realistically stage (rule 2's
  "conditions the review session cannot realistically reproduce").

## Why

Builder-blind means every claim above was re-derived or re-executed this
session in an isolated worktree
(`git worktree add /tmp/pr2336-wt pr-2336`), rather than taken from the
builder's own account in
`18cd271919f0960134b656a166f55953448b21fd:docs/issue-2313/reports/implementation.md`.
conformance-review-verification-method-selection routed R1 and R3 to
Test (existing `gates/test_check_runner.py` coverage, reused per rule 4
and rerun independently this session — fenced in full under R3 above,
derived: `python3 gates/test_check_runner.py` and
`python3 -m pytest gates/ -q`), R1 and R4 additionally to Demonstration
against a fresh stand-in script this session, R2 to Inspection for the
textual clarification itself, and R2's-correctness/R5 to Analysis (rule
2 — the misleading-use condition isn't realistically stageable inside
this review session). conformance-review-sampling-derivation was judged
not-applicable and skipped: the diff's requirement-bearing surface is 2
code files plus 1 directive file, small enough that every hunk was read
in full (see "What was done" for the `git diff --stat`, fenced above).

The PR also carries a self-caught fix outside issue #2313's frozen
Acceptance: a pre-landing warrant-hunter pass in the builder session
found `_artifact_touched()` still receiving the un-split compound
command (same first-token blind spot as R1, in the declared-
`runtime-artifacts` touch-check branch specifically), fixed and pinned
with `t_compound_cd_command_with_declared_artifact_still_classifies_as_artifact_smoke`
(`18cd2719:gates/test_check_runner.py:382-393`) before this PR opened —
independently confirmed present and passing in this session's rerun,
fenced under R3 above. This is not a frozen-Acceptance requirement
(issue #2313 never names `_artifact_touched` or `runtime-artifacts`
checks), so it is noted here rather than scored as its own R-item, per
rule 3 (do not invent a checkable item the spec never named) — but it
directly strengthens R1's "classify by final command, consistently"
claim, so it is recorded as context, not silently dropped.

## What did not work

None — every requirement's evidence reproduced on the first
independent attempt this session; no retry was needed.

## Upstream basis

- PR #2336, `tokenmaxxxer/on-the-record`, head commit
  `18cd271919f0960134b656a166f55953448b21fd` (branch
  `issue-2313/implementation`, base `907428d9ab189c36053813fe59ff403467f2a2ba`)
  — sha for every `gates/check_runner.py`, `gates/test_check_runner.py`,
  and `on-the-record/directive/merge-gates.md` citation above; fetched
  this session via `git fetch origin pull/2336/head:pr-2336` and
  `git worktree add /tmp/pr2336-wt pr-2336`.
- `18cd2719:docs/issue-2313/reports/implementation.md` — the builder's
  own record, read only to locate what to independently re-check; not
  present on this `conformance-review` branch (PR-only, unmerged),
  hence the sha-pinned citations throughout this record.
- issue #2313 itself (body items 1-2, Acceptance block) — `gh issue view
  2313`, this session.
- `main:gates/check_runner.py` and
  `main:on-the-record/directive/merge-gates.md` (this branch's own base,
  pre-fix) — read this session, used as the pre-fix baseline for R2 and
  R5's comparison.

## Open findings

None — all five body/Acceptance-derived requirements (R1 through R5)
independently re-verified as Present against PR #2336's head commit; no
gap surfaced beyond the frozen scope. resolution path: none (no open
findings to resolve).

## Next steps

`loop_state` is `reported` (terminal for a review-record per the session
protocol's kind table) — nothing pending from this record itself.

skill-verdict: conformance-review-requirement-extraction — applied: invoked;
split issue #2313's Acceptance `provenance` line (bundled with `;`) into
R4 and R5, kept the issue body's already-split items 1 and 2 as R1 and
R2, and excluded the `gate:`/`infrastructure/no-direct-requirement`
lines from the checkable list as pointers/tags with no observable
success condition of their own (rules 2 and 3).
skill-verdict: conformance-review-verification-method-selection — applied: invoked;
routed R1 and R3 to Test (existing coverage reused per rule 4, rerun
independently — derived: `python3 gates/test_check_runner.py`), R1 and
R4 additionally to Demonstration against a fresh stand-in script, R2 to
Inspection (rule 1 — textual property), and R2's-correctness/R5 to
Analysis (rule 2 — the misleading-use condition isn't realistically
stageable inside this review session).
skill-verdict: conformance-review-verdict-assignment — applied: invoked;
all five requirements independently re-verified and assigned Present; no
Incorrect/Absent/Unverifiable verdict was needed, so no `spec_vs_built`
field or missing-evidence naming was required.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked;
every evidence citation above is pinned to file:line plus PR #2336's
head sha `18cd271919f0960134b656a166f55953448b21fd` (or `main`'s for the
pre-fix baseline), re-executed this session rather than paraphrased from
the builder's record.
skill-verdict: conformance-review-finding-record — applied: invoked; this
file, one block per requirement with requirement/spec_ref/verdict/
evidence/rationale; no `spec_vs_built` field needed since no requirement
verdicted `Incorrect`.
other mounted skills: conformance-review-sampling-derivation (full
enumeration was feasible — 2 code files plus 1 directive file with
requirement-bearing hunks — not-applicable), conformance-review-severity-classification
(scope was not extended into risk-weighting a recorded finding — there
are no findings to weight — not-applicable), implementation-audit
(cross-family keyword match only — this role's own conformance-review
skill family already governs this exact task more specifically —
not-applicable) — not triggered.

warrant-hunter before-landing dispatch: skipped. This session's diff is
a single new file under `docs/issue-2313/reports/` — the warrant-protocol
directive's DOCS-ONLY FAST PATH explicitly skips the before-landing
dispatch when every touched path is under `docs/`; separately,
`CORE_BUILD_NOW=1` bypassed the proposal round entirely (contract v3
s19a), so there is no proposal file/slug and no after-proposal
transition to dispatch against either. Reason recorded here per the
directive's own "a skip is never silent" requirement.
