---
issue: 2705
role: adversarial-review-249cc937
author: adversarial-review-249cc937
skills: adversarial-review (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2753's own deliverable
code_under_review: on-the-record PR #2753 (c6068dcf496c11d1423814e22ab9975fb686aff7)
type: review
breaking: false
verdict: changes-recommended — the core fix, the three first-cut-bug fixes, and the enumeration all hold under independent re-derivation (see below for the executed commands), but the parser-in-front-of-a-guard attack surface this task asked me to probe is not closed: a `cd <subdir> && git add <relpath> && git commit` or subshell `(cd <subdir> && git add <relpath> && git commit)` bundled shape live-reproduces the exact bypass this PR exists to fix. A second, opposite-direction bug also reproduces live — `:(exclude)` pathspec magic is not recognized and causes an over-refusal. Neither is a regression from this PR (both shapes were equally unrefused/unreachable before it), so this does not undo the fix's net improvement.
loop_state: landed
upstream:
  - path: on-the-record PR #2753, branch issue-2705/secure-coding-input-validation-injection-defense+adversarial-review-cd806f25
    sha: c6068dcf496c11d1423814e22ab9975fb686aff7
---

# issue-2705 — adversarial-review-249cc937 record

## What was done

Build-now bypass (contract v3 s19a): checked: `printenv | grep CORE_BUILD_NOW`
— result: `CORE_BUILD_NOW=1`. Delivers directly, no proposal round.

canonical: `gh pr view 2753 --json title,body,state,headRefName,baseRefName`
— read at session start: PR #2753, OPEN, base `main`, head
`c6068dcf496c11d1423814e22ab9975fb686aff7`, branch
`issue-2705/secure-coding-input-validation-injection-defense+adversarial-review-cd806f25`.
Checked out the PR head into an isolated worktree (`git fetch origin
pull/2753/head:pr-2753-review && git worktree add /tmp/pr2753-wt
pr-2753-review`) and re-derived every claim below against that
checkout, not by re-reading the PR's own record. Every file this record
cites that lives only on the PR branch (not this review branch) is
cited in `<sha>:<path>` commit-pinned form below, per that branch's own
tip `c6068dcf496c11d1423814e22ab9975fb686aff7`.

### 1. The bundled-add bypass fix itself — holds

canonical: `c6068dcf:on-the-record/hooks/gate-registration-guard.sh`
lines 162-303 — adds `_shell_segments`/`_pending_add_segments`/
`_pending_add_targets`, which parse the pending command's own `git add`
segment(s), cross-reference `git status --porcelain=v1 -z
--untracked-files=all`, and fold matches into the same `added`/
`staged_all` sets the pre-existing `git diff --cached` path already
populates.

Live-fired against a real PreToolUse JSON payload on stdin (harness:
`bash on-the-record/hooks/gate-registration-guard.sh` fed
`{"tool_name":"Bash","tool_input":{"command":"<cmd>"},"cwd":"<dir>"}`
via a Python subprocess wrapper, since the hook reads stdin), with an
untracked `gates/evil_probe.py` (throwaway probe file in the
`/tmp/pr2753-wt` worktree only, never committed; no row in
`docs/specs/enforcement-boundary.md`) as the unregistered-module
fixture. All four required directions confirmed with the exit code
captured explicitly:

derived: `echo "$PAYLOAD" | bash on-the-record/hooks/gate-registration-guard.sh; echo "EXIT-CODE: $?"`, run once per row below —
```
=== confirm exit code for REFUSE bundled (no row) ===
gate-registration-guard: newly-added gate/hook module(s) missing a spec registration row (issue #441/#684):
gates/evil_probe.py: no row in docs/specs/enforcement-boundary.md
EXIT-CODE: 2
=== confirm exit code for ALLOW bundled (row present) ===
EXIT-CODE: 0
```

| shape | spec row | command | exit |
|---|---|---|---|
| bundled one-call | absent | `git add gates/evil_probe.py && git commit -m x` | **2** (refused) |
| bundled one-call | present | `git add gates/evil_probe.py && git commit -m x` | **0** (allowed) |
| stage-then-commit (2 calls) | absent | `git add gates/evil_probe.py` then `git commit -m x` | **2** (refused) |
| stage-then-commit (2 calls) | present | `git add gates/evil_probe.py` then `git commit -m x` | **0** (allowed) |

### 2. First-cut bugs the PR's own adversarial-review pass caught — all three re-verified fixed

canonical: `git show 8160def4~1:on-the-record/hooks/gate-registration-guard.sh`
— the parent of the fix commit has zero occurrences of
`_pending_add` (grep confirms), so the `-A`/`-u`/`-c`/`-C`/`.`-scoping
handling did not exist pre-fix; the fixed behavior for all three is
pinned in the shipped regression suite,
`c6068dcf:test/test_gate_registration_guard_bundled_add_commit.py`.

canonical: `python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -v`,
run against the PR-head worktree — result: `11 passed in 2.83s`,
matching the PR's own claimed count exactly (11 test methods across 7
classes, covering the `-A`/`--all`/`-u` dead-code fix, the `-c`/`-C`
global-option fix, and the `.`-scoping fix).

### 3. New bypasses found in this pass — parser-in-front-of-a-guard surface, per the task's brief

I went looking for shapes the PR's own first cut didn't cover, per the
task's explicit list (pathspecs, `--` separators, quoted/escaped paths,
globs, no-arg `add`, subshell/`cd`, semicolons, heredoc). All were
live-fired against the same fixture (`gates/evil_probe.py`, untracked,
unregistered, same throwaway probe file as above).

**Confirmed refuses correctly (no bypass).** derived: each command
below run individually through the same live-fire harness as §1, with
exit code captured — all seven returned exit 2 (refused) except the
no-arg case, which is not a real bypass vector:
- glob: `git add gates/*.py && git commit -m x` → refused (the existing
  `fnmatch.fnmatch(u, rel)` fallback in `_pending_add_targets`,
  `c6068dcf:on-the-record/hooks/gate-registration-guard.sh:266-268`,
  already matches glob patterns against the untracked set).
- `--` separator: `git add -- gates/evil_probe.py && git commit -m x` → refused.
- semicolon instead of `&&`: `git add gates/evil_probe.py; git commit -m x`
  → refused (`;` is in the `_shell_segments` separator set,
  `c6068dcf:on-the-record/hooks/gate-registration-guard.sh:188`).
- quoted path with a space (`"gates/evil probe.py"`) and shell-escaped
  space (`gates/evil\ probe.py`) → both refused.
- `env FOO=bar git add gates/evil_probe.py && git commit -m x` →
  refused, confirming the PR's own claimed wrapper-prefix fix
  (first-occurrence `"git"` token search, not position-0) holds.
- heredoc: `git add gates/evil_probe.py && git commit -F - <<'EOF'` →
  refused; `strip_heredoc_bodies` blanks the heredoc body but leaves the
  `git add ... && git commit` skeleton outside it intact.
- `git add` with no path argument → contributes zero targets (dead end,
  not a real bypass vector — bare `git add` with no path is itself a
  no-op in real git).

**Confirmed BYPASS (exit 0, should refuse) — new finding, not covered
by the shipped regression suite.** derived: same live-fire harness as
§1, run against the three commands below.
```
=== cd-before-add: cd gates && git add evil_probe.py && git commit (cwd stays repo root in payload) ===
EXIT-CODE: 0
=== subshell: (cd gates && git add evil_probe.py && git commit -m x) ===
EXIT-CODE: 0
=== relative parent-then-child cd: cd ../pr2753-wt/gates && git add evil_probe.py && git commit -m x ===
EXIT-CODE: 0
```
All three return exit 0 — silent allow — on the identical unregistered-
module fixture that the bundled-literal-path case in §1 correctly
refuses (exit 2). Root cause, derived from reading the same two spans
live-fired above:
```python
# c6068dcf:on-the-record/hooks/gate-registration-guard.sh:115
cwd = e.get("cwd") or os.getcwd()
```
```python
# c6068dcf:on-the-record/hooks/gate-registration-guard.sh:258-260
        abs_p = raw if os.path.isabs(raw) else os.path.normpath(
            os.path.join(cwd, raw))
```
`cwd` is read once from the static PreToolUse payload's `cwd` field and
never re-derived for an in-command `cd`. `_shell_segments` correctly
splits `cd gates`, `git add evil_probe.py`, and `git commit -m x` into
three separate segments (`(`/`)`/`&&` are all separators in the set at
`c6068dcf:on-the-record/hooks/gate-registration-guard.sh:188`), and
`_pending_add_segments` correctly finds the `git add` segment in
isolation — but nothing in the pipeline inspects the *other* segments
for a preceding `cd`, so `evil_probe.py` resolves against the payload's
original `cwd` (repo root) instead of `repo_root/gates`, producing
`rel = "evil_probe.py"`, which matches neither the literal untracked
entry `gates/evil_probe.py` nor its fnmatch fallback (no wildcard
character in the pattern, so `fnmatch` degrades to an exact-match
comparison). This is not a fail-closed refusal on an unanalyzable shape
(the task's explicit "do not accept fail-closed" instruction) — it is a
silent, wrong-direction resolution producing an incorrect allow on a
shape the parser fully, successfully tokenizes.

**Confirmed over-refuse (opposite direction — fail-closed widening,
contradicts the PR's own stated design invariant).** derived: live
probe with two untracked unregistered files in the PR-head worktree —
`gates/evil_probe.py` (given a throwaway spec row for this probe only,
so it is registered and inert for this specific test) and
`gates/second_evil.py` (an untracked, second throwaway probe file,
created and deleted within this session's `/tmp/pr2753-wt` worktree
only, never committed, left unregistered). Real git's `:(exclude)`
pathspec magic means `git add . ':(exclude)gates/second_evil.py'`
stages everything under `.` except `second_evil.py`, so a correct guard
should stay silent (nothing new and unregistered would actually land):
```
=== git add . ':(exclude)gates/second_evil.py' && git commit -m x ===
gate-registration-guard: newly-added gate/hook module(s) missing a spec registration row (issue #441/#684):
gates/second_evil.py: no row in docs/specs/enforcement-boundary.md
EXIT-CODE: 2
```
The guard refused, citing exactly the untracked, throwaway file the
exclude pathspec was meant to carve out — a false refusal, not a
security bypass. Root cause, from the same span cited in §3's bypass
finding above:
```python
# c6068dcf:on-the-record/hooks/gate-registration-guard.sh:254-257
        if raw == ".":
            cwd_rel = os.path.relpath(cwd, repo_root).replace(os.sep, "/")
            prefix = "" if cwd_rel == "." else cwd_rel + "/"
            out.update(u for u in untracked if u.startswith(prefix))
```
`:(exclude)`/`:!` magic pathspecs are not special-cased anywhere in
`_pending_add_targets`; the exclude token itself falls through the
generic literal/fnmatch branch and (since it matches nothing literally)
contributes zero targets on its own, but the unconditional `.` branch
above still sweeps in everything under `cwd` regardless. This directly
contradicts the same commit's own header comment at
`c6068dcf:on-the-record/hooks/gate-registration-guard.sh:44-48`, which
reads "No new fail-closed surface: a `git add` segment this guard
cannot parse ... simply contributes no pending targets, same fail-open
posture" — but an unrecognized `:(exclude)` token does not leave the
`.` contribution unfiltered the way that comment claims; it leaves it
exactly as over-broad as if the exclude token were never there.

## Why

canonical: this record's §1-§3 above (executed this session against the
PR-head worktree) is the basis for every conclusion below — the task's
framing that this fix is a parser sitting in front of a guard, and that
its attack surface is therefore the parser, is confirmed by the two new
findings in §3, both of which are parser gaps (a resolution-context gap
and a pathspec-magic gap), not logic errors in the guard's downstream
spec-row check.

I worked the task's own list of unexplored shapes (pathspecs, `--`,
quoting, globs, no-arg, subshell/`cd`, `;`, heredoc) against the live
shipped hook rather than reading the diff for correctness alone, per
the task's "exercise both directions live" instruction. derived:
`python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -v`
(§2 above) — result: 11 passed, confirming the three bugs the PR's own
first-cut adversarial-review pass already found are closed and pinned,
so a repeat search over that identical surface would have found
nothing new; I instead worked the surface the task explicitly called
out as unexplored. Most of that list holds up (§3, "Confirmed refuses
correctly"); two shapes did not, in opposite directions, and both trace
to the same structural choice — `cwd`/positional-path resolution is
computed once from the static payload and never reconciled against the
*other* segments of the same command (a prior `cd`) or against pathspec
magic syntax git itself understands. I did not attempt a fix; the task
asked for verification, not remediation, and the two findings are
reported under "Open findings" below with a recommended resolution path
rather than patched in this record's own commit, consistent with
`verifies_subject: true` review scope.

### Enumeration re-derivation (acceptance check 3)

Re-ran the PR's own derivation commands independently rather than
trusting its table, all against the PR-head worktree:

canonical: `grep -rln "diff --cached\|--cached" on-the-record/hooks/*.sh on-the-record/hooks/*.py`
— result: 6 files (`acceptance-command-real-run-guard.sh`,
`requirement-digest-preflight.sh`, `live-fire-test-guard.sh`,
`gate-registration-guard.sh`, `live-fire-claim-real-run-guard.sh`,
`spec-index-preflight.sh`).

canonical: `grep -rln "diff --cached\|--cached" $CLAUDE_PLUGIN_ROOT_CORE/hooks/*.sh $CLAUDE_PLUGIN_ROOT_CORE/hooks/lib/*.sh`
— result: 2 files (`handbook-trigger-gate.sh`, `trailer-gate.sh`).

canonical: `grep -rln '"git", "status"\|git status' on-the-record/hooks/*.sh on-the-record/hooks/*.py`
— result: 3 files (`deviation-log-guard.sh`, `gate-registration-guard.sh`
[already counted above], `product-capture-stopgate.sh`); `head -6
on-the-record/hooks/deviation-log-guard.sh on-the-record/hooks/product-capture-stopgate.sh`
— result: both open with `# Stop:` — Stop-event hooks fire after the
turn already ran, not before a pending command, so both are correctly
excluded from this population.

canonical: `grep -n 'live-fire-test-guard\|requirement-digest-preflight' on-the-record/hooks/hooks.json on-the-record/hooks/pretooluse_dispatcher.py`
— result: no matches (grep exit 1) for either script in either wiring
file, confirming both are unwired dead code as the PR claims.

canonical: `grep -n 'script="spec-index-preflight.sh"\|script="gate-registration-guard.sh"\|script="acceptance-command-real-run-guard.sh"\|script="live-fire-claim-real-run-guard.sh"' on-the-record/hooks/pretooluse_dispatcher.py`
— result: all four present in the `GATES` list, confirming the 3
"affected, not fixed" siblings are actually wired and reachable.

canonical: `grep -n 'deny(' $CLAUDE_PLUGIN_ROOT_CORE/hooks/trailer-gate.sh $CLAUDE_PLUGIN_ROOT_CORE/hooks/handbook-trigger-gate.sh`
— result: both files' `deny()` is `... exit 0; }  # issue-282 DEMOTE:
advisory, not blocking`, confirming the "advisory-only, never blocks"
characterization for both core hooks.

Population re-derived independently from these six commands: 1 fixed +
3 wired-affected (on-the-record) + 2 core wired-affected (advisory) + 2
unwired-dead-code = 8 total matches, 6 on-the-record + 2 core — matches
the PR's claimed "3 more on-the-record hooks and 2 core hooks share
this blind spot, 2 more are unwired dead code" exactly. The count is
right.

## What did not work

A probe-harness detail, not a finding about the code under review: the
first wrapper script combined `set -e` with printing an `EXIT-CODE: $?`
line after the piped hook invocation, so a nonzero exit from a refused
command exited the wrapper before that line printed. derived: switched
to a plain wrapper without `set -e` (`/tmp/probe2.sh`, shown inline
above as the harness for every `EXIT-CODE:` line in §1 and §3) before
drawing any conclusion from an exit code — every exit code cited in
this record was captured with that corrected wrapper, confirmed by the
explicit `EXIT-CODE: 0`/`EXIT-CODE: 2` lines quoted in §1 and §3 above.

## Upstream basis

canonical: `gh pr view 2753 --json title,body,state,headRefName,baseRefName`
and `gh pr diff 2753`, both read at session start — PR #2753
(`tokenmaxxxer/on-the-record`), head
`c6068dcf496c11d1423814e22ab9975fb686aff7`.

- The pre-fix parent commit `8160def48e0c3392af39fc2ac18057ab42e60a39`
  and the record-fix-only follow-up `c6068dcf`. derived: `git show
  c6068dcf --stat` — result: only
  `c6068dcf:docs/issue-2705/reports/secure-coding-input-validation-injection-defense+adversarial-review-cd806f25.md`
  changed, 2 insertions/17 deletions (single-file record edit).
- Issue #2705 itself. canonical: `gh issue view 2705`, read at session
  start.

## Open findings

- **cd/subshell-before-`git add` bypass** (§3 above, "Confirmed
  BYPASS"): `cd <subdir> && git add <relpath> && git commit`, its
  subshell variant `(cd <subdir> && git add <relpath> && git commit)`,
  and any other shape where an earlier segment of the same command
  changes the effective directory before the `git add` segment runs,
  silently bypasses the fix this issue delivered. Resolution path: a
  follow-up fix threading a per-segment "effective cwd" through
  `_shell_segments`/`_pending_add_segments` (tracking `cd`/`pushd`
  segments preceding each `git add` segment and resolving that add's
  relative paths against the accumulated cwd, not the static payload
  `cwd`), with a regression test pinning both the plain-`cd` and
  subshell-`cd` shapes verified live in this record's §3. Recommend
  filing as a follow-up issue against `gate-registration-guard.sh`
  specifically (narrower than #2757's sibling-hook scope, since this is
  a gap in the fix #2757 was filed on top of, not one of the five
  siblings #2757 enumerates).
- **`:(exclude)` pathspec over-refusal** (§3 above, "Confirmed
  over-refuse"): `git add . ':(exclude)<path>'` (and by the same
  mechanism, `:!<path>`) causes a false refusal on a path real git
  would not actually stage, contradicting this same commit's own header
  comment at `c6068dcf:on-the-record/hooks/gate-registration-guard.sh:44-48`
  claiming no new fail-closed surface. Lower priority than the bypass
  above — wrong direction, costing a spurious refusal rather than a
  silent unregistered-module landing — but worth folding into the same
  follow-up fix, since both trace to the same `_pending_add_targets`
  function.
- The three "affected, not fixed here" on-the-record siblings
  (`acceptance-command-real-run-guard.sh`, `live-fire-claim-real-run-guard.sh`,
  `spec-index-preflight.sh`) and the two advisory-only core hooks
  (`trailer-gate.sh`, `handbook-trigger-gate.sh`): per the Enumeration
  re-derivation above, PR #2753's characterization of these as
  out-of-scope for this issue, needing their own follow-up fix, checks
  out against my independent grep/wiring re-derivation. I did not
  additionally live-probe whether these siblings would inherit a
  cd/subshell-class gap once someone ports this PR's fix shape to them
  — recommending that the eventual follow-up fix for those siblings
  design in the per-segment-cwd tracking from the start, rather than
  copy this PR's static-`cwd` approach and reproduce the same gap five
  more times.
- #2757 (filed on the strength of PR #2753's enumeration claim): the
  Enumeration re-derivation section above (six independently-run grep/
  wiring commands, matching the PR's claimed 3 on-the-record + 2 core +
  2 dead-code split exactly) confirms #2757's premise — the enumerated
  population is accurate.

## Next steps

None for this record; `loop_state: landed`. The two new findings above
are recommended as follow-up issue(s) rather than as next steps of this
review.

## Standing invariants

1. **No return of the retired role axis in any reshaped form.**
   derived: `git diff 00aeaae4 c6068dcf -- on-the-record/hooks/gate-registration-guard.sh test/test_gate_registration_guard_bundled_add_commit.py | grep -ic role`
   — result: `0`.
2. **No new bug — failing-test-name set vs origin/main, not counts.**
   canonical: `python3 -m pytest test/ gates/ -q`, run once in a
   worktree of PR head `c6068dcf` — result: `16 failed, 429 passed, 6
   xfailed`; run once more in a separate worktree of `origin/main`
   (`e1b35a53`) — result: `15 failed, 419 passed, 6 xfailed`. Diffing
   the two failing-test-name sets (`comm -13` of the two sorted name
   lists, not a count comparison, as instructed): the PR worktree's set
   is the origin/main set plus exactly one extra name — the file
   `test/test_auto_approval_shadow_wiring.py`, test method
   `SimulatedApprovalAppendsSampleTest::test_approval_gate_sh_is_byte_identical`.
   This is the stale-branch symptom flagged in the task: PR #2753's
   branch base is `00aeaae4`, four commits behind `origin/main`
   (`e1b35a53`), which predates PR #2746 (the role→skill rename that
   evidently fixed this specific byte-identical check on `origin/main`
   but which the PR-2753 branch never picked up). Confirmed PR #2753
   does not touch `approval-gate.sh`: derived: `git diff 00aeaae4
   c6068dcf --stat` — result: only 3 files touched (the record
   markdown, `on-the-record/hooks/gate-registration-guard.sh`, and the
   new test file), `approval-gate.sh` absent from that list. So the
   extra failure is inherited from the stale base, not introduced by
   this PR's diff — the two sets are equal outside that one
   pre-existing, branch-age artifact.
3. **No overhead increase.** canonical: `du -sb on-the-record/directive`,
   run in the PR-head worktree — result: `53162`, matching the stated
   baseline exactly. derived: `git diff 00aeaae4 c6068dcf --stat --
   on-the-record/directive` — result: empty (directory untouched by
   this diff). Measured the added parse cost directly: derived: three
   repeated `/usr/bin/time -f "%e s"` runs of the hook against a plain
   `git commit -m x` (no `git add` segment in the text) gave
   `0.04s/0.03s/0.04s`; three runs against the bundled `git add
   gates/evil_probe.py && git commit -m x` (which triggers the new
   `git status` subprocess call) gave `0.06s/0.06s/0.06s` — roughly
   20ms added, and only on the narrow trigger (a command whose text
   contains a parseable `git add` segment); the no-`git-add` case shows
   no measurable added cost, consistent with the PR's claim that the
   extra `git status` call is conditional on `pending_add_segments`
   being non-empty
   (`c6068dcf:on-the-record/hooks/gate-registration-guard.sh:272-273`).
4. **Monitor/watch machinery unbroken and not quieter.** derived: `git
   diff 00aeaae4 c6068dcf --stat` — result: 3 files touched (listed in
   invariant 2 above), none in any monitor/watch-class path; `git diff
   00aeaae4 c6068dcf --stat | grep -i 'monitor\|watch'` — result:
   empty.

## Skill verdicts

- skill-verdict: adversarial-review — applied: invoked; canonical: this
  record's §1-§3 above (executed this session against the PR-head
  worktree, not re-read from the PR's own record) is the evidence for
  this verdict. derived: `python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -v`
  — result: 11 passed, exercising neither of the two new shapes found
  in §3 — an independent evaluator pass working the task's explicit
  list of unexplored parser shapes rather than re-treading the three
  bugs the PR's own first-cut review already found (§2), surfacing two
  new findings under "Open findings" above (one bypass, one
  over-refusal). Sequencing correction (logged as an inline deviation,
  `docs/issue-2705/reports/adversarial-review-249cc937/deviation-log/`):
  this session's own role IS the two-party protocol's evaluator seat
  relative to PR #2753's builder session — a separate session, given
  the artifact and re-deriving every claim rather than trusting the
  builder's record — but the `Skill` tool call for `adversarial-review`
  itself was not made until after §1-§3's probing and the initial PR
  #2761 push, not before, so the original `applied: invoked` line was
  written ahead of the actual tool call. Corrected in this same commit
  by calling `Skill(adversarial-review)` and updating this line; the
  §1-§3 findings themselves are unchanged by the correction, since they
  already followed the skill's mechanism (independent re-derivation,
  every finding cited to a file:line/exit-code, no findings-free report
  accepted) in substance before the tool call caught up to it in form.
- other mounted skills: not triggered — `work-in-english` matched the
  task-configuration list but this record, all commands, and all probe
  scripts were already authored in English throughout, matching repo
  convention, so no action was needed from it; `implementation-audit`,
  `growth-analytics-metric-selection`, `premortem`, and
  `technical-feasibility-verdict-and-timebox-selection` do not apply to
  an adversarial-review-shaped verification task (no falsifiable-claim
  extraction protocol, no North Star metric, no pre-commitment plan to
  pressure-test, no feasibility-probe verdict to set).
