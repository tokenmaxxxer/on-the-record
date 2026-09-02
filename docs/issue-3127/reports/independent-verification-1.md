---
issue: 3127
role: independent-verification-1
author: independent-verification-1
verifies_subject: true  # independent, builder-blind verification of PR #3131's own deliverable against issue #3127
loop_state: landed
code_under_review: 7f2490823ebf7cc153250935798010bad3de73f4
type: defect-verification-record
breaking: false
verdict: 3 of 3 literal acceptance checks Present (re-run this session
  against a linked worktree at `7f249082`), 3 of 3 must-not clauses
  Present (re-derived from `consumer-path-results.json` and
  `pre-registration.md` directly, not cited), confound check (#3091/
  #2507) re-derived and holds. The harness's core one-variable
  manipulation is Incorrect -- independently reproduced twice this
  session against this environment's real skill sources: (a) a genuine
  empty-stub `MUSTER_SKILL_REPO` hits a hard fail-closed multi-source
  conflict against `~/.claude/skills` before dispatch; (b) the harness's
  own literal, never-replaced `--skill-repo-off` default
  (`"<empty-sibling-dir>"`, not a real path) silently resolves through
  `~/.claude/skills` to the full real corpus content
  (content_sha256-verified match), which the override never touches --
  the more damning of the two since it is what the shipped code actually
  does by default, not a hypothetical. `execute_arm()` is confirmed
  unreachable from `main()`'s `--execute` branch by direct read of
  `main()`'s body. H1 (directive-byte comparison) and H2 (blind scoring)
  have no wiring anywhere in the file. H3 (wall-clock-to-landed) measures
  time-to-`session-end`, which under the unmodified two-phase default is
  at most a phase-1 proposal-PR opening, not a merge. This is a third
  independent verification of PR #3131; agrees with both PR #3135 and PR
  #3145 on the 3+3 literal checks (derived: this session's own three
  acceptance-check commands and three must-not reads, quoted below), and
  independently re-derives every substantive finding PR #3145 first
  surfaced, corroborating it with fresh reproductions of my own plus one
  additional, more direct repro of the silent-corpus-leak failure mode
  using the harness's actual shipped default.
upstream:
  - path: 7f249082:scripts/issue-3127/run_consumer_pair.py
    sha: 7f2490823ebf7cc153250935798010bad3de73f4
  - path: 7f249082:scripts/issue-3127/verify_preregistration.py
    sha: 7f2490823ebf7cc153250935798010bad3de73f4
  - path: 7f249082:docs/issue-3127/decisions/pre-registration.md
    sha: 7f2490823ebf7cc153250935798010bad3de73f4
  - path: 7f249082:docs/issue-3127/_assets/consumer-path-results.json
    sha: 7f2490823ebf7cc153250935798010bad3de73f4
  - path: skills.py
    sha: same-commit  # read/executed at this session's own unmodified HEAD
  - path: pipeline.py
    sha: same-commit  # read at this session's own unmodified HEAD, PR #3131 does not touch it
  - path: events.py
    sha: same-commit  # read at this session's own unmodified HEAD, PR #3131 does not touch it
---

# issue-3127 — independent-verification-1 record

## What was done

Third independent, builder-blind verification of PR #3131 (branch
`issue-3127/experiment-trust+product-discovery-hypothesis-preregistration+implementation-blueprint+silent-failure-audit-4eda8e00`,
head `7f249082`) against issue #3127. Two prior independent verifications
already exist and are landed on `main` (PR #3135, PR #3145); this
session's task explicitly assigned it slot `independent-verification-1`
for the same subject, so it was carried out as a genuinely independent
attempt (own checkout, own commands, own reads of primary sources)
rather than a citation of the prior two, per
`defect-verification-independence-from-upstream-verdicts` rule 3 (re-derive
rather than cite) and rule 9 (a clean-looking upstream record does not
lower how many self-devised checks this pass runs).

canonical: `gh issue view 3127` output, read this session -- three
acceptance checks and three must-not clauses, quoted in the issue body.

canonical: `gh pr view 3131` output, read this session -- delivers the
pre-registered design and harness; `run_status: "not_executed"` by the
PR's own description.

Setup: `git fetch origin pull/3131/head:pr-3131-review`, then
`git worktree add /tmp/pr3131-review pr-3131-review` (head `7f249082`).
All command output below ran from that worktree unless stated otherwise;
the worktree was removed after this session's checks completed
(`git worktree remove /tmp/pr3131-review --force`), without adding any
commit to PR #3131's own branch.

### The three literal acceptance checks

canonical: this session's own terminal output, run against
`/tmp/pr3131-review`:

```
$ python3 scripts/issue-3127/run_consumer_pair.py --dry-run; echo exit=$?
=== issue-3127 consumer-path pair plan (dry run; nothing executed) ===
...
exit=0
$ test -f docs/issue-3127/_assets/consumer-path-results.json && echo PRESENT
PRESENT
$ python3 scripts/issue-3127/verify_preregistration.py; echo exit=$?
OK: pre-registration commit 84226988e930981b02d00abd30e22c83100e875f is an
ancestor of results commit 9c9801cd470129580de54b78a32abc30875de90e
exit=0
```
All three: Present.

### The three must-not clauses

canonical: `7f249082:docs/issue-3127/_assets/consumer-path-results.json`,
read directly in the worktree this session -- `decision` field reads
`"unmeasured -- explicitly not reported as a null/no-effect result"`,
and a `power_statement` field states concretely what the registered n=2
can and cannot resolve (an effect smaller than the registered 3-point
combined margin, "roughly one grade-band shift per pair," is
unresolvable at this n; this is a directional-threshold decision rule,
never a significance claim). `arms` shows `run_status: "not_executed"`
applied uniformly to both arms of both registered pairs, not narrowed to
drop a bad outcome (there is no outcome yet, so nothing was dropped).
Present.

canonical: `7f249082:docs/issue-3127/decisions/pre-registration.md`'s
"Power statement" section, read directly -- carries the identical
disclosure, committed before any result existed per the commit-order
check above (acceptance check 3). Present.

canonical: `7f249082:scripts/issue-3127/run_consumer_pair.py`'s
`build_plan()`, read directly -- `held_constant.skill_name_argument`
holds only the `--skills <name>` argument text constant across arms, not
`spawn.py`'s own BM25/mounting behavior; the pre-registration lists BM25
selection position as a reported diagnostic, not something engineered
away. Present.

All three must-nots: Present.

### Confound check (issue #3091/#2507) -- independently re-derived, holds

derived: `python3 -m pytest test/test_spawn_cross_family_skill_selection.py -k test_family_skill_never_returned_as_cross_family_candidate -q`,
run this session against `/tmp/pr3131-review`:

```
FAILED ...Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate
AssertionError: Lists differ:
  [PosixPath('/tmp/tmpe89af735/implementation-blueprint')] != []
1 failed in 0.84s
```

canonical: `7f249082:pipeline.py`'s `_cross_family_candidate_corpus()`,
read directly (this file is untouched by PR #3131, read at this
session's own unmodified HEAD) -- body opens with `del skill`, then
`family_names = set(_sp._STATIC_POLICY_SKILLS)`; no role/family
exclusion set exists anywhere in the function. The docstring's own claim
about #2507 removing the role-family exclusion is confirmed against the
running code, not just against its own prose. Present -- the current
candidate pool is not narrowed by the stale pin, so #3053's selection
numbers do not need re-deriving on this account.

derived: `git ls-files | grep -i issue-3126`, run against
`/tmp/pr3131-review` -- zero hits (exit 1); confirms the PR's stated
path correction (everything under `issue-3127`, not the issue body's
literal `issue-3126` typo) was actually applied throughout. Present.

### Full test suite (baseline check)

derived: `python3 -m pytest tests/ -q`, run against `/tmp/pr3131-review`:
```
254 passed, 2 warnings in 10.50s
```
(the 2 warnings are a pre-existing pinned-fixture divergence, issue
#3019, unrelated to PR #3131's four files.)

derived: `python3 -m pytest test/ -q`, run against `/tmp/pr3131-review`:
```
15 failed, 548 passed, 3 xfailed in 31.79s
```
Same 15 failing node IDs both prior verifications reported as the
pre-existing baseline owned by #3091 (including the
`Bm25CrossFamilySkillMatchesTest` failure re-derived above); none of PR
#3131's own four delivered files appear as a cause.

## The deeper question: does the harness's one-variable manipulation actually work?

derived: this session's own three acceptance-check runs and three
must-not reads in the sections above (quoted there) establish only that
the literal issue-text checks pass; they do not by themselves establish
that the harness would produce a valid measurement if run for real. Per
`defect-verification-independence-from-upstream-verdicts` rule 2
(include at least one edge case / negative path, not only happy-path
checks), this session went further and independently reproduced the
harness's core manipulation mechanism itself, before reading either
prior verification's own write-up of it (rule 3: re-derive, don't cite).

### Reproduction 1: a genuine empty-stub directory still fail-closes

canonical: `7f249082:scripts/issue-3127/run_consumer_pair.py` module
docstring, read directly -- claims the skills-off arm's `MUSTER_SKILL_REPO`
points at "an empty sibling directory containing nothing but a
placeholder for the named skill," so the corpus is "present but empty"
and the `--skills` resolver's fail-closed unknown-skill rejection never
fires.

derived: built the described stub and pointed `MUSTER_SKILL_REPO` at it,
in this session's own real environment (`$MUSTER_SKILL_REGISTRY_ROOT`
populated, `~/.claude/skills` a real symlink to it):
```
$ mkdir -p /tmp/my-stub-skill-repo/product-discovery-hypothesis-preregistration
$ head -3 $MUSTER_SKILL_REGISTRY_ROOT/product-discovery-hypothesis-preregistration/SKILL.md \
    > /tmp/my-stub-skill-repo/product-discovery-hypothesis-preregistration/SKILL.md
$ MUSTER_SKILL_REPO=/tmp/my-stub-skill-repo python3 -c "
import spawn, skills
from pathlib import Path
try:
    r = skills.resolved_skill_sources('product-discovery-hypothesis-preregistration', Path('/tmp/my-stub-skill-repo'))
    print('RESOLVED (no conflict):', r)
except SystemExit as e:
    print('SYSTEM EXIT (fail-closed):', e)
"
SYSTEM EXIT (fail-closed): --skills: product-discovery-hypothesis-preregistration
가 둘 이상의 소스에서 겹친다 -- skill-repository(?), ~/.claude/skills
(/home/jwjung/.claude/skills/product-discovery-hypothesis-preregistration)
```
A genuine empty-frontmatter-only stub does not produce "corpus present
but empty" in this environment -- it hits a hard fail-closed exit before
dispatch, because `resolved_skill_sources()` (`skills.py:302-417`) also
reads `~/.claude/skills` (`local-user` tier) and the target repo's own
`.claude/skills` (`local-repo` tier) unconditionally; `MUSTER_SKILL_REPO`
only ever controls the `skill-repo` tier.

### Reproduction 2: the harness's own literal shipped default silently leaks the full corpus

canonical: `7f249082:scripts/issue-3127/run_consumer_pair.py` lines
360-366, read directly -- the `--skill-repo-off` argparse default is the
literal string `"<empty-sibling-dir>"`, not a real path.

derived: `grep -n "mkdir\|empty-sibling-dir" scripts/issue-3127/run_consumer_pair.py`,
run against `/tmp/pr3131-review` -- only that one argparse default line
and its help text match; no function anywhere in the file creates such a
directory. This means an unconfigured `--execute` run (i.e. what the
harness actually ships) never runs reproduction 1's scenario at all; it
runs this one instead.

derived: reproduced the harness's actual default this session, without
creating any stub directory:
```
$ MUSTER_SKILL_REPO="<empty-sibling-dir>" python3 -c "
import spawn, skills
from pathlib import Path
r = skills.resolved_skill_sources('product-discovery-hypothesis-preregistration', Path('<empty-sibling-dir>'))
print('RESOLVED:', r)
"
RESOLVED: [{'source': 'local-user', 'dir': PosixPath('/home/jwjung/.claude/skills/product-discovery-hypothesis-preregistration'), ...,
  'content_sha256': 'a917a97f528c2f63ec18413d85f9f33602ec1e4c081ab805219a51894e635109', ...}]
```
canonical: `skills.py:102-105`'s `_skill_repo_root()`, read directly --
an env value that fails `Path(...).is_dir()` (true for the literal
string `"<empty-sibling-dir>"`) is treated as absent, falling through to
the sibling/managed-clone fallback. In this reproduction
`resolved_skill_sources()` found only the `local-user` tier match (no
`skill-repo` tier match at all, since the literal string resolves to
nothing), so it silently returns the full real corpus content with
`returncode == 0`, genuine success, indistinguishable in the harness's
own code from a real skills-off run. This is the failure mode PR #3145
described as "silently resolves through `~/.claude/skills` to the full
real corpus" -- independently confirmed here, and additionally confirmed
to be what the *shipped, unconfigured* harness actually does, not only
what a hand-built stub scenario produces.

Neither reproduction (1: hard crash; 2: silent full-corpus leak) is the
one-variable "present but empty" manipulation the harness's own
docstring claims. Incorrect.

### H1 (directive-composition byte comparison) has no enforcement code

derived: `grep -n "^def " scripts/issue-3127/run_consumer_pair.py`, run
against `/tmp/pr3131-review` -- 11 functions: `build_plan`,
`spawn_command`, `render_dry_run`, `scrub_skill_slugs`,
`collect_directive_bytes`, `collect_ledger_tokens`, `collect_metrics`,
`execute_arm`, `_os_environ`, `emit_not_executed_results`, `main`. None
compares two arms' directive-byte counts, applies a threshold, or
refuses to count a pair if a manipulation check fails.
`collect_directive_bytes()` (lines 217-221) reads one workspace's own
directive-directory size; nothing calls it against a pair and compares
the two arms. Absent as enforcement.

### The blind quality scorer does not exist in code

derived: `grep -n "scrub_skill_slugs\|evaluate_pair\|quality_blind_score" scripts/issue-3127/run_consumer_pair.py`,
run against `/tmp/pr3131-review` -- `scrub_skill_slugs()` is defined
(lines 196-214, a real redaction function against a known-slug list) but
called nowhere else in the file; `evaluate_pair` appears only inside the
dry-run's own printed comment text (line 187-188), never imported or
invoked. `quality_blind_score` appears only as a hardcoded `None` (line
333). No scoring function exists anywhere in this PR's four delivered
files. Absent.

### `execute_arm()` is unreachable from `main()`'s `--execute` branch

canonical: `7f249082:scripts/issue-3127/run_consumer_pair.py`'s `main()`
(lines 346-408), read directly -- the `--execute` branch (after the
`--i-understand-this-spawns-real-sessions` confirmation check) calls only
`emit_not_executed_results(plan)`, relabels the result's `run_status`,
and prints a per-arm "would execute ... see execute_arm()" message to
stderr. `execute_arm()` itself is never called. Confirmed independently
by direct read of `main()`'s full body, not by citation of either prior
verification's claim of the same. Incorrect (as coded, `--execute` does
not execute).

### Wall-clock-to-landed measures time-to-session-end, not time-to-merge

canonical: `7f249082:scripts/issue-3127/run_consumer_pair.py`'s
`execute_arm()` (lines 257-318), read directly -- `t0 = time.monotonic()`
set immediately before the dispatch subprocess call, `wall_clock_s`
computed immediately after the `spawn.py watch --follow` subprocess
returns.

canonical: `events.py`'s `_watch(..., follow=True)`, read directly (this
file is untouched by PR #3131, read at this session's own unmodified
HEAD) -- the follow loop's stop condition returns only when a
`session-end` event is consumed (lines 774-776); per the same file's own
comment, "session-end 만이 종료를 뜻한다" (only session-end counts as
termination).

canonical: `7f249082:scripts/issue-3127/run_consumer_pair.py`'s
`spawn_command()` (lines 130-140), read directly -- passes only
`--skills`, the task text, `--issue`, `--model`, `-C`; no
single-phase/checkpoint/build-now flag, so the spawned session runs
under the unmodified two-phase default (role-handoff contract v3 s19):
a `session-end` there is at most a phase-1 proposal-PR opening, not a
merge.

derived: `grep -n "gh pr\|merged\|mergedAt\|pr view" scripts/issue-3127/run_consumer_pair.py`,
run against `/tmp/pr3131-review` -- zero matches; no PR/board-state poll
exists anywhere in the file. Incorrect against the harness's own printed
claim (`render_dry_run()` text states "wall-clock to landed: time from
spawn dispatch to the arm's PR reaching a merged/landed state, not first
output"), though currently unreachable in practice since `execute_arm()`
itself is dead code (prior finding above).

## Why

Ran every acceptance check and must-not clause myself from a fresh
worktree rather than trusting either prior verification's report of the
same result, per `defect-verification-independence-from-upstream-verdicts`
rules 1 and 3 -- a Present verdict from two prior sessions is a claim to
re-test, not a settled fact, and re-deriving from primary evidence
(`consumer-path-results.json`, `pre-registration.md`, the harness source
itself) rather than citing the prior records' summaries is what makes
this a third *independent* verification rather than a restatement.

canonical: this session's own commands and code reads quoted throughout
the sections above (all `derived:`/`canonical:`-tagged in place) --
where this session's checks overlap with PR #3145's (the resolver
conflict, H1/H2 absence, `execute_arm()` unreachability, the wall-clock
stop condition), the prior records' own write-ups were read only after
this session's own reproductions had already run, per rule 10 (keep the
outcome slot open until the attempt runs, not pre-shaped by a prior
framing). Reproduction 2 above goes further than a re-run of PR #3145's
own command -- it uses the harness's actual literal, unconfigured
`--skill-repo-off` default rather than a hand-built empty-stub
directory -- satisfying rule 2's edge-case requirement with a genuinely
new attempt rather than a repeated one.

## What did not work

None -- every check above ran to completion; no approach was attempted
and abandoned this session.

## Rationale for deviations

None. `git worktree add`/`git worktree remove` and the two live Python
reproductions were run against a detached worktree of PR #3131's own
branch and against this session's own live environment; no commit was
added to PR #3131's branch, no repository write occurred outside this
record file and the worktree cleanup. No scope was exceeded and no
approach here was swapped mid-session.

## Upstream basis

- PR #3131, branch
  `issue-3127/experiment-trust+product-discovery-hypothesis-preregistration+implementation-blueprint+silent-failure-audit-4eda8e00`,
  head `7f249082` -- verified in a linked worktree at
  `/tmp/pr3131-review` (removed after this session's checks; all
  `7f249082:`-prefixed paths above refer to that worktree, not to a path
  present in this session's own working tree).
- `skills.py` (this session's own unmodified HEAD) --
  `resolved_skill_sources()`/`_skill_repo_root()`, read and executed
  directly for both reproductions above.
- `pipeline.py` (this session's own unmodified HEAD, untouched by PR
  #3131) -- `_cross_family_candidate_corpus()`, read directly for the
  confound-check re-derivation.
- `events.py` (this session's own unmodified HEAD, untouched by PR
  #3131) -- `_watch()`'s `session-end` stop condition, read directly.
- PR #3135
  (`docs/issue-3127/reports/experiment-trust+adversarial-review+defect-verification-independence-from-upstream-verdicts-51782ba3.md`,
  read via `git show origin/main:...`, first independent verification)
  -- read for cross-reference after this session's own checks had
  already run; agrees on the 3+3 literal checks.
- PR #3145
  (`docs/issue-3127/reports/experiment-trust+test-depth-audit+silent-failure-audit-f8660411.md`,
  read via `git show origin/main:...`, second independent verification)
  -- read for cross-reference after this session's own checks had
  already run; this session's reproductions 1 and 2, and the H1/blind-scorer/
  `execute_arm()`/wall-clock findings, independently corroborate its
  findings rather than cite them, with reproduction 2 going further
  (harness's actual shipped default, not a constructed stub).

## Open findings

canonical: this session's own reproductions 1 and 2 and the four
deeper-question findings in "The deeper question" section above (each
independently derived this session, `derived:`/`canonical:`-tagged in
place) -- all open against PR #3131 / issue #3127, not against this
verification record. Each was already listed as open by PR #3145 and is
independently re-confirmed here, so no new resolution paths are added
beyond what is already on record there:

- Skills-off corpus-emptying manipulation does not work as documented in
  this real environment -- reproduced twice this session (reproductions
  1 and 2 above).
- H1 (directive-byte comparison) is not enforced anywhere in code.
- The blind quality scorer (`scrub_skill_slugs()` + an evaluator) is not
  wired into anything -- defined but never called.
- `execute_arm()` is unreachable from `main()`'s `--execute` branch.
- Wall-clock-to-landed measures time-to-session-end, not time-to-merge,
  under the current unmodified two-phase spawn default.
- `test_family_skill_never_returned_as_cross_family_candidate` is a
  live, currently-failing stale test (issue #3091's scope, not #3127's).

amendments-reconciled: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5508098646`
(issue #3127 comment, posted 2026-09-02T10:24:26Z, after this session's own
checks above had already run) -- the operator holds PR #3131 and spawns a
repair round scoped to four defects: skills-off manipulation not achieving
"present but empty," H1 prose-only, blind scorer unimplemented, and
wall-clock-to-landed measuring time-to-session-end not time-to-merge, citing
both PR #3135 and PR #3145.

canonical: "Reproduction 1"/"Reproduction 2" and the "H1", "blind quality
scorer", and "Wall-clock-to-landed" subsections under "The deeper question"
heading above (this session's own `derived:`/`canonical:`-tagged reads and
live reproductions) match all four defects the operator's comment names. No
amendment to this record's own verdict is needed: the comment does not
change any of this session's own primary-source reads or live
reproductions, and this session's findings already match the scope the
operator now spawns a repair round against.

## Next steps

derived: this session's own checks -- `python3 scripts/issue-3127/run_consumer_pair.py --dry-run`
(exit 0), `test -f docs/issue-3127/_assets/consumer-path-results.json`
(present), `python3 scripts/issue-3127/verify_preregistration.py` (exit
0), `python3 -m pytest tests/ -q` (254 passed), `python3 -m pytest test/
-q` (15 pre-existing failures, 548 passed), plus the two live resolver
reproductions and the four deeper-question code reads -- all quoted in
full above. `loop_state: landed` -- this record commits them to this
session's own branch and this session opens a PR carrying it, per the
spawning instructions (does not merge, edit, or add commits to PR
#3131). The open findings above remain open against PR #3131 / issue
#3127, not against this verification record.

skill-verdict: defect-verification-independence-from-upstream-verdicts —
applied: invoked; loaded via the Skill tool this session and applied
derived: this session's own worktree commands and live Python
reproductions, quoted throughout the sections above -- rules 1 and 3
(ran the acceptance checks and must-nots from primary sources myself,
in a fresh worktree, before reading either prior verification's
write-up), rule 2 (reproduction 2 above is a genuinely new edge-case
attempt -- the harness's actual unconfigured default -- not a repeat of
reproduction 1 or of PR #3145's own command), and rule 9 (did not let
the existence of two prior landed verifications shrink how many checks
this pass ran; ran the acceptance checks, must-nots, confound check, and
all four deeper-question reproductions regardless).
skill-verdict: work-in-english — applied: invoked; loaded via the Skill
tool this session; this record, all commands, and all commit/PR text are
written in English per the skill (the spawning task and surrounding
directives are in Korean, but engineering exhaust stays English); the
final chat summary to the user is in Korean.
