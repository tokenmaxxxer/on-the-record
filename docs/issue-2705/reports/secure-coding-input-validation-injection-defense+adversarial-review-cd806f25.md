---
issue: 2705
role: secure-coding-input-validation-injection-defense+adversarial-review-cd806f25
author: secure-coding-input-validation-injection-defense+adversarial-review-cd806f25
skills: secure-coding-input-validation-injection-defense (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: 8160def48e0c3392af39fc2ac18057ab42e60a39
loop_state: landed
type: implementation
breaking: false
verdict: fixed -- `gate-registration-guard.sh` now catches a newly-added, unregistered `gates/*.py`/`on-the-record/hooks/*.sh`/`.github/workflows/*.yml` module in the bundled `git add X && git commit` shape, matching the pre-existing stage-then-commit behavior; enumerated all other PreToolUse hooks reading staged/working-tree state and confirmed the identical blind spot in 5 siblings (3 on-the-record, 2 core, all left unfixed here -- out of this issue's scope, follow-up recommended) and non-reachability in 2 more (dead code, unwired); an independent blind adversarial-review evaluator caught 3 real bugs in the first cut (git add -A/-u/--all dead-code branch, git -c/-C global-option bypass, git add . repo-wide-vs-cwd-scoping bug), all fixed and pinned with regression tests before landing
upstream:
  - path: on-the-record/hooks/gate-registration-guard.sh
    sha: 8160def48e0c3392af39fc2ac18057ab42e60a39
---

# issue-2705 — secure-coding-input-validation-injection-defense+adversarial-review-cd806f25 record

## What was done

**The fix.** `on-the-record/hooks/gate-registration-guard.sh` is a PreToolUse
hook, which the harness fires BEFORE the guarded Bash command's text runs.
The guard's target list was built solely from `git diff --cached
--name-status`, so a bundled `git add <new gate> && git commit` -- this
repo's own recommended landing shape (#2135) -- had nothing staged yet at
hook time, and the guard passed silently on an unregistered gate/hook
module.

Added `_shell_segments`/`_pending_add_segments`/`_pending_add_targets`
(on-the-record/hooks/gate-registration-guard.sh:168-266) that parse the
pending command's own `git add` segment(s) for the paths this exact
command is ABOUT to stage, cross-reference them against `git status
--porcelain=v1 -z --untracked-files=all` (untracked-only, matching the
guard's existing "newly-added" scope), and fold any match into the same
`added`/`staged_all` sets the pre-existing `git diff --cached` path
already populates -- so every downstream check (spec-row presence,
hooks.json wiring, generated-paths classification) runs unchanged on the
combined set. No fail-closed widening: a `git add` shape the parser
cannot resolve contributes zero pending targets and the guard stays
fail-open on that gap, same posture as every other environment gap this
file already documents.

**First-cut bugs an independent adversarial review caught and I then
fixed** (see "Why" below for how this was run):
- `git add -A`/`--all`/`-u`/`--update` were dead code -- the generic
  `-`-prefix filter stripped the flag token before the special case that
  was supposed to handle it ever ran, so `git add -A && git commit` (the
  single most idiomatic "stage everything" bundled form) stayed
  completely undetected. Fixed by classifying flags before filtering
  positional args (`_pending_add_targets`, lines 220-235); `-u`/`--update`
  correctly contributes nothing (it only ever stages already-tracked
  files, never a new untracked one).
- `git -c <key>=<val> add ...` / `git -C <dir> add ...` (a two-token
  global option between `git` and `add`) broke the flag-skip loop and
  silently dropped the whole segment -- the exact bypass class this
  file's own lines 74-91 already document as fixed once for the sibling
  `commit`-detection check (issue #866/#876), never hardened for the new
  `add`-detection logic. Fixed in `_pending_add_segments` (lines
  196-217).
- `git add .` was treated as staging every untracked file in the whole
  repo, not just the acting directory's subtree -- a docs-only `cd docs
  && git add . && git commit` could have false-closed on an unrelated
  stray untracked gate file sitting anywhere else in the tree. Fixed by
  scoping `.` to `cwd`-relative prefix matching (lines 237-240).
- (Lower severity, fixed alongside the above): `git status --porcelain`'s
  default quoting for filenames with spaces/non-ASCII bytes could not be
  undone by a fixed-offset slice; switched to `--porcelain=v1 -z` (NUL-
  separated, unquoted) parsing (lines 245-266). Shell redirection tokens
  (`<`, `>`, `&`) are now segment separators too, so a redirect target no
  longer pollutes the candidate-path list (line 179).

**Regression tests**: canonical: `python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -v` output -- result: 11 passed. `test/test_gate_registration_guard_bundled_add_commit.py` holds 11 test methods across 7 classes, running the real shipped hook via a real PreToolUse JSON payload on stdin against a real local git checkout, matching `test/test_upstream_defect_scope_guard_cross_repo_cwd.py`'s harness shape. Covers: bundled literal-path add+commit (deny/allow), stage-then-commit unchanged (deny/allow), `-A`/`--all`, `-u` (must NOT flag), `-c`/`-C` global options, and `.` scoping (deny at root, no false-deny from an unrelated subdirectory).

**Enumeration** (acceptance check 3 -- population: all PreToolUse hooks
in `on-the-record/hooks/` and core's `hooks/`):

derived: `grep -rn "diff --cached\|--cached" on-the-record/hooks/*.sh on-the-record/hooks/*.py` plus `grep -rn "diff --cached\|--cached" <core>/hooks/*.sh <core>/hooks/lib/*.sh` (core root resolved via `$CLAUDE_PLUGIN_ROOT_CORE`) -- 8 hook files matched across both directories; `grep -rln '"git", "status"\|git status' on-the-record/hooks/*.sh on-the-record/hooks/*.py` found 2 more (`deviation-log-guard.sh`, `product-capture-stopgate.sh`) but both are `Stop`-event hooks (checked: `head -6` of each file's own header comment — result: both say `# Stop:`), which fire after the whole turn already ran, not before a pending command, so they are out of this population.

| hook | event wiring | reads | verdict | command establishing verdict |
|---|---|---|---|---|
| `on-the-record/hooks/gate-registration-guard.sh` | PreToolUse/Bash, wired in `pretooluse_dispatcher.py`'s `GATES` list (checked: `grep -n 'script="gate-registration-guard.sh"' on-the-record/hooks/pretooluse_dispatcher.py` — result: present) | `git diff --cached --name-status` | **was affected — fixed in this commit** | live probe: temp probe script cloning this repo, feeding a real PreToolUse JSON payload on stdin to `bash gate-registration-guard.sh` -- against the pre-fix file content (checked out via `git show HEAD~1:on-the-record/hooks/gate-registration-guard.sh`, i.e. this commit's parent) the bundled shape returned exit 0 (silent allow) on an unregistered gate; against the post-fix file it returns exit 2 (refused), matching the pre-existing separate-commands shape |
| `on-the-record/hooks/acceptance-command-real-run-guard.sh` | PreToolUse/Bash, wired (`fastpath=_grep_git_commit` in the same `GATES` list) | `git diff --cached --name-status` (on-the-record/hooks/acceptance-command-real-run-guard.sh:121) | **affected, not fixed here** | derived: `grep -n 'diff.*--cached' on-the-record/hooks/acceptance-command-real-run-guard.sh` -- result: line 121, same `git diff --cached --name-status` call as the fixed guard, gating whether a staged `acceptance: <cmd> — result: PASS|FAIL` citation gets re-run; a bundled `git add <file-with-citation> && git commit` sees an empty staged diff and skips the re-run silently, same root cause |
| `on-the-record/hooks/live-fire-claim-real-run-guard.sh` | PreToolUse/Bash, wired (same list) | `git diff --cached --name-status` (line 135) | **affected, not fixed here** | derived: `grep -n 'diff.*--cached' on-the-record/hooks/live-fire-claim-real-run-guard.sh` -- result: line 135, identical shape gating a `live-fire: <path> — result: ...` citation re-check |
| `on-the-record/hooks/spec-index-preflight.sh` | PreToolUse/Bash, wired (`fastpath=_grep_git_commit`) | `git diff --cached --name-only` (line 116) | **affected, not fixed here** | live probe: same harness shape -- staged a spec-file content change that no longer matches `docs/specs/reconciled-index.md`'s recorded hash; bundled `git add <spec> && git commit` returned exit 0 (should refuse — stale index went undetected), separate stage-then-commit correctly returned exit 2 with the stale-index message |
| `on-the-record/hooks/live-fire-test-guard.sh` | **not wired** | `git diff --cached --name-status` (line 157) | not reachable at all today, independent of this bug (separate #909-shaped orphan-hook gap) | derived: `grep -n 'live-fire-test-guard' on-the-record/hooks/hooks.json` and `grep -n 'script="live-fire-test-guard' on-the-record/hooks/pretooluse_dispatcher.py` -- both empty; the script is on disk but nothing in `hooks.json`/`pretooluse_dispatcher.py`'s `GATES` list invokes it |
| `on-the-record/hooks/requirement-digest-preflight.sh` | **not wired** | `git diff --cached --name-only` (line 142) | not reachable at all today, same as above | derived: `grep -n 'requirement-digest-preflight' on-the-record/hooks/hooks.json` and `grep -n 'script="requirement-digest-preflight' on-the-record/hooks/pretooluse_dispatcher.py` -- both empty |
| `<core>/hooks/trailer-gate.sh` | PreToolUse/Bash, wired (`pretooluse_dispatcher.py`'s `GATES`, status `"demote"` — advisory only, `deny()` always `exit 0`) | `git diff --cached --name-only` (line 151) | **affected**, but advisory-only so no block was ever at stake — the bundled shape silently suppresses the advisory trailer-missing notice instead of printing it | live probe: same harness shape -- staged a synthetic `docs/issue-<n>/reports/` fixture file (untracked, throwaway probe path, not a real repo path) with a commit message lacking a `Subject:` trailer; bundled shape returned empty stderr (advisory suppressed), separate stage-then-commit shape printed the advisory trailer-missing text; both exit 0 (demoted, never blocking) |
| `<core>/hooks/handbook-trigger-gate.sh` | PreToolUse/Bash, wired (same list, also `"demote"`) | `git diff --cached --name-only` (line 151 of that file) | **affected** (same code shape as `trailer-gate.sh`: `deny()` at line 30 also `exit 0`), not separately live-probed here — code-read verdict only | derived: `grep -n 'cached\|deny(' <core>/hooks/handbook-trigger-gate.sh` -- result: line 151 `git diff --cached --name-only`, line 30 `deny() { ... exit 0; }  # issue-282 DEMOTE: advisory, not blocking` |

Every other core hook (`board-gate.sh`, `ordering-gate.sh`, `record-shape-gate.sh`,
`citation-gate.sh`, `facet-keyword-gate.sh`, `proposal-shape-gate.sh`,
`record-fields-gate.sh`, `survey-order-gate.sh`, `gh-guard.sh`,
`approval-gate.sh`) reads no staged/working-tree state at all — checked:
`grep -rn '"git", "status"\|"git","status"\|git status\|"git", "diff"'
<core>/hooks/*.sh` — result: zero matches outside `trailer-gate.sh` /
`handbook-trigger-gate.sh`, so no other core hook is in this population.

## Why

The root cause (PreToolUse fires before the guarded command's text runs)
is structural to the harness, not a bug in any one hook's logic — every
hook that derives "what changed" from `git diff --cached` inherits it.
The issue's own "must not" list rules out the two cheap fixes (move to
PostToolUse changes the guarantee silently; fail-closed on anything
unanalyzable blocks ordinary work), so the only fix that keeps the same
guarantee is making the guard aware of what the pending command ITSELF
is about to do — parsing the `git add` segment(s) already present in the
same Bash call's text and treating their (currently-untracked) targets
identically to an already-staged "A". This mirrors the precedent the
guard's own header comments cite (spec-index-preflight.sh /
role-axis-completeness-guard.sh's narrow-trigger convention, and the
`shlex.shlex(..., punctuation_chars=True)` tokenization issue
#824/#834/#882 already established for the sibling `commit`-detection
logic) rather than inventing a new parsing approach.

Scope: this issue's acceptance asks for the enumeration ("the
enumeration plus, for each, the command that established its verdict"),
not a fix to every sibling. Fixing all 5 affected siblings in the same
commit would multiply the review surface and risk for a bundled PR far
beyond what one gate's registration bug warrants, and 3 of the 5
(`acceptance-command-real-run-guard.sh`, `live-fire-claim-real-run-guard.sh`,
`spec-index-preflight.sh`) are independent fail-closed contract gates
with their own edge cases, deserving their own dedicated fix + review
cycle rather than a rushed copy-paste of this file's parsing helpers.
The 2 advisory-only core hooks (`trailer-gate.sh`,
`handbook-trigger-gate.sh`) never blocked anything even before this
fix, so the operational cost of leaving them as-is is lower. Follow-up
issues are recommended for the 3 fail-closed siblings.

`secure-coding-input-validation-injection-defense` skill applied: the
new parsing code's only trust-boundary-adjacent behavior is reading
session-supplied Bash command text and resolving it into filesystem
paths, then feeding those into `subprocess.run` calls. Reviewed against
rule 5 (parameterized OS calls) and rule 10 (scope a review pass to the
changed lines and trust boundaries they cross) -- scoped to the new
`_shell_segments`/`_pending_add_segments`/`_pending_add_targets`
functions and the `git status`/`fnmatch` calls they feed; no
allowlist/denylist/encoding change was needed since nothing in this
diff reaches a shell, SQL, or HTML sink with unparameterized input.
See the "Skill verdicts" section below for the citation backing this.

`adversarial-review` skill applied: spawned a structurally independent
evaluator subagent (Agent tool, fresh context, `general-purpose` type,
agentId `a0a7e291e23edc073`) and gave it only the diff, the full
post-diff file, and the new test file -- no issue text, no explanation
of intent, no claim about what the fix was supposed to do. Its critique
surfaced 3 real bugs in the first cut (the `-A`/`-u`/`--all` dead-code
branch, the `-c`/`-C` global-option bypass, and the `git add .`
repo-wide-vs-cwd-scoping error), all fixed in this same commit (see
"What was done" above) and pinned with new regression tests so a future
refactor cannot silently reintroduce them. The wrapper-prefix finding
(`env FOO=bar git add ...`, `if ...; then git add ...; fi`) was
addressed by relaxing the segment's `git`-token search from
position-0-only to first-occurrence -- derived: live probe of `env
FOO=bar git add <new gate> && git commit` against the post-fix file,
result: exit 2 (refused). See the "Skill verdicts" section below for
the full citation backing both skill applications.

## Upstream basis

No upstream `docs/issue-2705/` input existed before this record — this
is the first delivery for the issue (build-now bypass, contract v3
s19a: `CORE_BUILD_NOW=1` was present in this session's environment at
spawn time, authorizing direct delivery without a separate phase-1
proposal round). The only upstream basis is the issue text itself and
the live repository state at the commit this fix landed on top of --
canonical: `gh issue view 2705` output, read directly at the start of
this session.

## Open findings

canonical: the enumeration table in this record's own "What was
delivered" section above (commit `8160def4`) is the source for the
three items below; no separate read is needed to restate their
verdicts here.

- The 3 fail-closed sibling hooks confirmed affected above
  (`acceptance-command-real-run-guard.sh`, `live-fire-claim-real-run-guard.sh`,
  `spec-index-preflight.sh`) still silently skip their staged-content
  check in the bundled shape. Resolution path: a follow-up issue per
  hook (or one issue covering all three, since they likely share a very
  similar fix shape to this one), porting the same
  pending-add-detection approach. Not fixed here — out of this issue's
  stated acceptance scope (enumeration + this one gate's fix only).
- `live-fire-test-guard.sh` / `requirement-digest-preflight.sh` are
  unwired dead code, unrelated to this issue's bug (they are unreachable
  in EVERY shape, not just the bundled one). Resolution path: a separate
  issue in the #909 orphan-hook-registration family, not this one.
- The 2 advisory-only core hooks (`trailer-gate.sh`,
  `handbook-trigger-gate.sh`) have the same blind spot but it only
  suppresses an advisory notice, never a block. Resolution path: low
  priority, candidate for the same follow-up fix as the 3 fail-closed
  siblings if that work happens.

## What did not work

None — the fix converged after one adversarial-review round; no
approach was tried and abandoned.

## Next steps

None for this record; `loop_state: landed`. Follow-up work (sibling
hook fixes, orphan-hook wiring) is tracked as "Open findings" above,
recommended as separate issues rather than next steps of this one.

## Standing invariants

1. **Role axis retirement**: zero role-axis references touched.
   derived: `git diff HEAD~1 HEAD -- on-the-record/hooks/gate-registration-guard.sh
   test/test_gate_registration_guard_bundled_add_commit.py | grep -ic
   role` — result: `0`. (Re-deriving the exact stated origin/main
   baseline count is out of scope here since this invariant is about
   non-regression from this session's own diff, which introduces zero
   role-axis lines either way; a scoped re-derivation via `git ls-tree
   -r --name-only origin/main | grep -v '^docs/'` piped through
   `git show origin/main:<f> | grep -owc role` per file gave 1179 on
   this pass, same order of magnitude as the stated 1390 but not an
   exact match — likely a methodology difference in how the original
   count was taken, not evidence of regression, since it was computed
   against unmodified origin/main content this session never touched.)
2. **No new bug**: failing-test-name sets compared before/after, not
   counts. derived: `python3 -m pytest test/ gates/ -q` run three times
   — pre-fix (`git stash` applied, 15 failed/419 passed), post-fix
   before adding the new regression test file (15 failed/419 passed),
   and post-fix with the new test file (15 failed/430 passed). The 15
   failing test names are byte-identical across all three runs
   (`test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape`
   and 14 others, all pre-existing network/environment-dependent
   failures in `test_spawn_*`/`test_local_dependency_env.py` unrelated
   to this diff — none of those files reference
   `gate-registration-guard.sh`, checked: `grep -l
   "gate-registration-guard" test/test_convention_equivalence.py
   test/test_local_dependency_env.py
   test/test_spawn_cross_family_skill_selection.py
   test/test_spawn_artifact_skill_pairing.py
   test/test_spawn_skill_judge_haiku_timeout_overlap.py` — result: no
   matches). 11 new tests added, all pass.
3. **No overhead increase**: `on-the-record/directive` untouched.
   derived: `du -sb on-the-record/directive` — result: `53162`, matching
   the stated baseline exactly (the directory was never in this diff's
   file set, checked: `git show 8160def4 --stat` — result: only
   `on-the-record/hooks/gate-registration-guard.sh` and
   `test/test_gate_registration_guard_bundled_add_commit.py`). No new
   hook registration, no new dispatcher entry — the fix is entirely
   inside the already-wired `gate-registration-guard.sh` gate's own
   Python body, one extra `git status` subprocess call only on the
   already-narrow fast-pathed trigger (a Bash command whose text
   contains both `git` and `commit`, and additionally now only spends
   the extra `git status` call when a `git add` segment was found in
   that same text) — no additional runtime cost on any commit that
   doesn't match the pre-existing narrow trigger.
4. **Monitor/watch machinery**: untouched and not applicable. derived:
   `git show 8160def4 --stat` — result: only
   `on-the-record/hooks/gate-registration-guard.sh` (modified) and
   `test/test_gate_registration_guard_bundled_add_commit.py` (new) are
   touched by the code commit; no watch/monitor-class file is in that
   set.

## Skill verdicts

canonical: this session's own tool-call transcript (the two `Skill`
tool invocations earlier in this record's authoring turn, and the
`Agent` tool invocation with agentId `a0a7e291e23edc073`) is the source
for both verdicts below; the fixes each verdict references are pinned
at commit `8160def48e0c3392af39fc2ac18057ab42e60a39`.

- skill-verdict: secure-coding-input-validation-injection-defense —
  applied: invoked; reviewed the new parsing/subprocess code against
  rules 5 (parameterized OS calls — verified via `grep -n "shell=True"
  on-the-record/hooks/gate-registration-guard.sh`, no matches, so no
  string-built shell commands anywhere in the diff) and 10 (scope a
  review to the changed trust-boundary-adjacent lines — scoped to the
  three new parsing functions and their `subprocess.run`/`fnmatch`
  calls); no denylist-as-sole-defense or unparameterized-shell finding
  to act on.
- skill-verdict: adversarial-review — applied: invoked; spawned an
  independent blind evaluator subagent (Agent tool, fresh context, no
  issue text or intent given) against the first-cut diff; it surfaced 3
  real bugs (`git add -A`/`-u`/`--all` dead code, `git -c`/`-C`
  global-option bypass, `git add .` repo-wide-vs-cwd-scoping), each of
  which I independently reproduced via a live probe against the
  then-current file before fixing and pinning with a new regression
  test.
</content>
