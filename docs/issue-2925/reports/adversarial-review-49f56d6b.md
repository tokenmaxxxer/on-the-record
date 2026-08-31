---
issue: 2925
role: adversarial-review-49f56d6b
author: adversarial-review-49f56d6b
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: PR #2932 (issue-2925/refactoring-legacy-seam-selection+silent-failure-audit-63ccc91e, commit 53a4f5f10580543354c8b446621da1cd5ca09930)
loop_state: landed
type: verification
breaking: false
verdict: deletion-justified-two-informational-gaps
upstream:
  - path: gates/patrol_board.py (present on origin/main at 46779718d2435a8749d7c736e86d3f54a5dc30d5; deleted on PR head)
    sha: 46779718d2435a8749d7c736e86d3f54a5dc30d5
  - path: gates/patrol_promote.py (present on origin/main at 46779718d2435a8749d7c736e86d3f54a5dc30d5; deleted on PR head)
    sha: 46779718d2435a8749d7c736e86d3f54a5dc30d5
  - path: gates/patrol_queue.py (present on origin/main at 46779718d2435a8749d7c736e86d3f54a5dc30d5; deleted on PR head)
    sha: 46779718d2435a8749d7c736e86d3f54a5dc30d5
  - path: gates/patrol_trigger.py (present on origin/main at 46779718d2435a8749d7c736e86d3f54a5dc30d5; deleted on PR head)
    sha: 46779718d2435a8749d7c736e86d3f54a5dc30d5
  - path: gates/patrol_wiring.py (present on origin/main at 46779718d2435a8749d7c736e86d3f54a5dc30d5; deleted on PR head)
    sha: 46779718d2435a8749d7c736e86d3f54a5dc30d5
  - path: gates/precision_measure.py (present on origin/main at 46779718d2435a8749d7c736e86d3f54a5dc30d5; deleted on PR head)
    sha: 46779718d2435a8749d7c736e86d3f54a5dc30d5
  - path: consult.py
    sha: 53a4f5f10580543354c8b446621da1cd5ca09930
  - path: gates/gh_rest.py
    sha: 53a4f5f10580543354c8b446621da1cd5ca09930
  - path: gates/record_lint.py
    sha: 53a4f5f10580543354c8b446621da1cd5ca09930
  - path: on-the-record/gates/record_lint.py
    sha: 53a4f5f10580543354c8b446621da1cd5ca09930
  - path: on-the-record/hooks/gh-write-allow-gate.sh
    sha: 53a4f5f10580543354c8b446621da1cd5ca09930
  - path: on-the-record/commands/run.md
    sha: 53a4f5f10580543354c8b446621da1cd5ca09930
  - path: on-the-record/monitors/poll-heartbeat.sh
    sha: 53a4f5f10580543354c8b446621da1cd5ca09930
  - path: on-the-record/monitors/test_poll_heartbeat.py
    sha: 53a4f5f10580543354c8b446621da1cd5ca09930
---

# issue-2925 — adversarial-review-49f56d6b record

## What was done

Independent verification of PR #2932, which deletes the patrol program
(five modules issue #2925 named — `gates/patrol_board.py`,
`gates/patrol_promote.py`, `gates/patrol_queue.py`,
`gates/patrol_trigger.py`, `gates/patrol_wiring.py` — plus a sixth,
`gates/precision_measure.py`, the issue did not name), trims
`on-the-record/monitors/poll-heartbeat.sh`'s patrol tick machinery and its
test, and edits six survivor files the PR claims resolved their patrol
references rather than amputating them.

canonical: `gh pr view 2932 --json title,body,headRefName,baseRefName,additions,deletions,files,url` (this session) — 163 additions / 2004 deletions across 17 files, base `origin/main`, head `issue-2925/refactoring-legacy-seam-selection+silent-failure-audit-63ccc91e` at `53a4f5f1`; the PR body's own claims were read here only as a list of assertions to test, not as ground truth — every claim below is re-derived independently from the two worktrees and live command execution described in each section, not from this body text or from the PR's own delivery record. A prior review attempt on this PR died mid-run with no record produced; this is a fresh pass. Two other independent verification sessions are running on PR #2932 in parallel with a general mandate; this record was scoped adversarially per the spawning brief, on five specific attack points rather than general correctness.

Two git worktrees were built for direct comparison: `origin/main` at
`46779718d2435a8749d7c736e86d3f54a5dc30d5` (pre-deletion state, all six
patrol modules present) and PR head at
`53a4f5f10580543354c8b446621da1cd5ca09930` (post-deletion state). Five
background workers (`freelunch:freelunch-worker`, run foreground per
contract v3 s22's headless-consume-same-turn override) each dug one attack
angle against these worktrees with live command execution — grep bounds
stated per-angle, diffing, and actually running the changed code, not
reasoning from the diff text alone. Findings below are synthesized from
their raw, evidence-backed reports; the worktrees were removed
(`git worktree remove --force` on both paths) after use as scratch
cleanup, not part of the deliverable.

### PRIMARY attack: is deleting `gates/precision_measure.py` a scope expansion?

Issue #2925 named five patrol modules; the PR deletes a sixth,
`gates/precision_measure.py` (287 lines), justified as: "its only
functional half depended entirely on `patrol_queue`, with zero other
callers repo-wide."

canonical: `gates/precision_measure.py` on `origin/main` (46779718) — read
in full. `import patrol_queue` sits at **module scope** (top of file, not
inside a function), so the entire module — including the ostensibly
patrol-independent statistics functions (`stratified_sample`,
`wilson_lower_bound`, `_z_one_sided`, `build_report`, `format_report`,
`cmd_report`) — fails to import at all once `patrol_queue.py` is gone.
Only `_population()` (feeding `cmd_sample`) calls patrol_queue functions
directly, but the import-time coupling means the "non-patrol half" claim
undersells the coupling: nothing in the file was independently invocable
regardless of that half's own logic.

derived: `grep -rn "precision_measure" --exclude-dir=.git .` (origin/main
worktree, whole repo including docs/) — every hit outside the file itself
and its own git history is a `docs/issue-*/reports/*.md` narrative mention
of a manual, one-off CLI run. Zero hits in `on-the-record/hooks/`,
`on-the-record/commands/`, `on-the-record/monitors/`, or any gate-registry
file (`gates/gates.py`, `hooks.json`, `monitors.json`).

canonical: `docs/specs/enforcement-boundary.md:51` (origin/main) — the
repo's own pre-existing, first-party module-classification table
(written for issue #1614, unrelated to this PR) labels
`precision_measure` **"not a hook itself, CLI-invoked"** — in contrast to
`closure_sweep.py` in the same table, which is documented as wired into
`roster_watchdog()` on every tick. This is independent evidence, not
PR-authored, that the module was never automatically triggered.

derived: `git log --follow -- gates/precision_measure.py` (origin/main) —
exactly one commit since introduction (issue #1614); never touched again,
never subsequently wired into anything. No file exists at
`gates/test_precision_measure.py` — untracked, never committed to this
repo despite being described as created in
`docs/issue-1614/reports/implementation.md:8`; zero test coverage
currently exercises `precision_measure.py`.

**Verdict** (derived: the three checks immediately above, this section):
the sixth-module deletion is justified, not unauthorized scope creep.
`precision_measure.py` has zero callers outside the already-deleted
`patrol_queue`, is import-time coupled to it so no "independent half" was
ever reachable in practice, was never registered in any
hook/command/monitor/gate path, and carries zero test coverage. Removing
dead code whose only real dependency is being deleted in the same PR is
standard practice, not empire-building — the issue naming five modules by
example does not obligate leaving a sixth, provably-dead dependent module
in place.

### SECOND attack: were the six survivor-file patrol references resolved or amputated?

Each of the six files was diffed against `origin/main`, read in the
PR-head worktree for context, and actually executed against real inputs
(not inferred from the diff alone).

canonical: `consult.py`, PR-head worktree — `judge_cmd()` previously
enqueued findings into `patrol_queue` (`"enqueued"` return key); post-PR
it inline-reverifies the judge's cited excerpt against the real file and
returns a plain `"findings"` list. derived: live invocation
`spawn.judge_cmd('security-review', HEAD_sha, cwd='.')` (worker's session,
PR-head worktree) returned a well-formed skip result, and the judge log
write path (`runs/judge-log.md`, renamed from `runs/patrol-judge-log.md`)
worked. The only prior consumer of the `"enqueued"` key,
`gates/patrol_wiring.py`, is deleted in the same PR. RESOLVED CLEANLY.

canonical: `gates/gh_rest.py`, diffed against `origin/main` — comment/docstring-only change (dropped a cross-reference to `patrol_board.find_board_issue`'s caching pattern). derived: `python3 -c "import gates.gh_rest"` (PR-head worktree) succeeds; `grep -rn "patrol_board\|find_board_issue"` (PR-head, whole repo) returns zero hits. RESOLVED CLEANLY.

canonical: `gates/record_lint.py` and `on-the-record/gates/record_lint.py`, diffed against `origin/main` — docstring accuracy fix only (dropped a claim that `patrol_queue`'s sweep-lane scanner calls `find_records()`). derived: `diff gates/record_lint.py on-the-record/gates/record_lint.py` (PR-head) is empty — both copies stayed byte-identical. Both were run live against `docs/issue-2925/reports/adversarial-review-49f56d6b.md` itself as a real record-file input, each producing correct exit-1/exit-0 lint output. RESOLVED CLEANLY.

canonical: `on-the-record/hooks/gh-write-allow-gate.sh`, diffed against `origin/main` — `bash -n` (PR-head) is clean; the changed lines are comments only (a reference to deleted issue-#1586 patrol-board edit-in-place logic replaced with a pointer to `on-the-record/commands/run.md`'s 합의 절차/최소·감사 가능한 편집 sections). derived: read `on-the-record/commands/run.md` (PR-head) directly and confirmed both referenced section headers exist there; executed the hook with a synthetic `PreToolUse` payload for `gh issue edit`, producing `permissionDecision: allow`, exit 0 — the verb-shape logic this comment documents is untouched. RESOLVED CLEANLY.

canonical: `on-the-record/commands/run.md`, diffed against `origin/main` — the deleted paragraph instructed running `gates/patrol_wiring.py run <repo-root> <merge-sha>` post-merge and described a `.on-the-record/patrol-disabled` kill-switch. derived: read the PR-head file directly — the merge-step section ends cleanly with no orphaned step and no dangling reference; `grep -n patrol` (PR-head, this file) returns zero hits. RESOLVED CLEANLY.

**Verdict** (derived: the five per-file diff-plus-execution checks
immediately above, this section): no amputations found. All six files'
patrol references were genuinely rewired or excised together with their
now-deleted dependents; no broken callers, no silently-degraded behavior,
no dangling doc references.

### THIRD attack: is the `judge_cmd()` return-key fix complete?

The PR claims it caught and fixed, mid-edit, its own introduced
inconsistency between `"enqueued"` and `"findings"` as `judge_cmd()`'s
return key.

derived: `diff -u <origin/main copy> <PR-head copy> consult.py` — all
three success/near-success `return {...}` statements in `judge_cmd()`
were changed in lockstep from `"enqueued": [...]` to `"findings": [...]`,
alongside removing the `patrol_queue.enqueue()`/`save_queue()` side
effect entirely (the function no longer writes to a queue; it re-verifies
excerpts against the live file and returns them).

canonical: PR-head `consult.py` — return contract confirmed as:

```
L1492/L1511  {"skipped": True, "reason": ..., "skill": skill, "merge": merge_sha}
L1537        {"skipped": False, "skill": skill, "merge": merge_sha, "findings": []}
L1542        {"skipped": False, "skill": skill, "merge": merge_sha, "findings": []}
L1567        {"skipped": False, "skill": skill, "merge": merge_sha, "findings": findings}
```

derived: `grep -rn "judge_cmd" <PR-head repo> --include="*.py"` — the only
real caller is `spawn.py:2651`, which passes the whole result dict
straight to `json.dumps(result, ...)` and never indexes `result["enqueued"]`
or `result["findings"]` by name — it is key-agnostic. `grep -rn
'"enqueued"\|\.get("enqueued"'` across the whole PR-head repo returns zero
hits: no caller anywhere still expects the old key.

**Verdict** (derived: the two checks immediately above, this section):
the fix is complete, not half-done. Definition and the sole real caller
agree; no remaining reader of the old key exists anywhere in the repo.
Gap (informational, not a defect): no unit test pins `judge_cmd()`'s
return shape directly, so this contract isn't regression-guarded by CI —
a coverage gap, not evidence the claimed fix is wrong.

### FOURTH attack: leftover patrol vocabulary beyond the literal string, and the docs/ claim

derived: `git grep -rni "patrol" -- . ':!docs' ':!.git'` (PR-head) —
confirms the PR's own claim: exactly one hit,
`test/test_retirement_count.py:44: self.assertFalse(retirement_count.line_hits("patrol the controller"))`,
an unrelated English test string (substring match, not a feature
reference).

derived: broader vocabulary sweep on PR-head for
`PATROL|patrol_board|patrol_promote|patrol_queue|patrol_trigger|patrol_wiring|precision_measure|board_line|boardline|promote_to_issue|rate_cap|ratecap|checkbox.approval|queue_entry` and `find . -iname "*patrol*"` (excluding `.git`, `docs/`) — zero hits in live code; the only filesystem matches are 11 pre-existing files under `docs/` (proposals/specs/reports), none newly created or touched by this PR's diff.

derived: `git diff origin/main...pr-2932-head --name-status -- docs/` (this
worktree) — the literal "docs/ untouched" claim does **not** hold. Three
paths are touched:

```
A  docs/issue-2925/reports/refactoring-legacy-seam-selection+silent-failure-audit-63ccc91e.md
A  docs/issue-2925/reports/refactoring-legacy-seam-selection+silent-failure-audit-63ccc91e/deviation-log/20260831T051900361562-b1a39e12d408dd07.md
M  docs/specs/reconciled-index.md
```

(both `A` paths are untracked on this branch — they exist only on PR
branch `issue-2925/refactoring-legacy-seam-selection+silent-failure-audit-63ccc91e`
at commit `53a4f5f1`, read via the `pr-2932-head` worktree used
throughout this record.)

canonical: inspected each — the two `A` files are this PR's own delivery
record and deviation log, the standard per-role artifact every phase-2 PR
in this repo adds, not a leftover patrol reference (their content
documents the removal; that's expected subject matter for an audit
record, not scope creep). `docs/specs/reconciled-index.md`'s one-line
diff is a mechanical checksum update reflecting
`on-the-record/commands/run.md`'s changed hash — `grep -ni patrol` on
both versions of `reconciled-index.md` returns nothing. derived:
`git diff origin/main...pr-2932-head` for each of the 11 pre-existing
`docs/` files whose *filename* carries patrol vocabulary (e.g.
`docs/specs/patrol-channel-contract.md`) — all 11 produced empty diffs:
byte-identical, no rename, no migration, no content edit.

**Verdict** (derived: the four checks in this section): the substantive
concern is satisfied, the literal phrasing is not. No historical
patrol-named document was renamed, migrated, or modified — that specific
worry is clean. But "the diff touches no docs/ file at all" is
technically false: it touches 3 docs/ files, both process-standard (own
delivery record + generated index checksum). Stated plainly since asked
to: if "zero docs/ diff, full stop" was meant literally, this PR does not
meet it; if the intent was "don't touch *existing* patrol documentation,"
it does.

### FIFTH attack: silent absorption and the four standing invariants

canonical: full tick, host bash — `TOKENMAXXXER_CHECKOUT=<PR-head>
POLL_HEARTBEAT_MAX_TICKS=1 POLL_HEARTBEAT_SLEEP_SECONDS=0 bash
on-the-record/monitors/poll-heartbeat.sh` under GNU bash 5.1.16: produced
a normal `roster_watchdog` report, `EXIT_CODE=0`.

canonical: full tick, bash 3.2 — `docker run --rm ... bash:3.2 sh -c "...
bash on-the-record/monitors/poll-heartbeat.sh"`: produced normal output
(with expected `gh`-auth-related content differences from the sandboxed
container), `EXIT_CODE=0`; `bash -n` also clean under 3.2.

canonical: diff of `on-the-record/monitors/poll-heartbeat.sh` and
`on-the-record/monitors/test_poll_heartbeat.py` between the two worktrees
— every removed `printf` (`[patrol-poll] ...`) and every removed test
(`t_patrol_wiring_does_not_alter_...`, `t_patrol_quiet_tick_...`,
`t_patrol_promotion_tick_...`, `t_patrol_crashed_skill_tick_...`,
`t_patrol_kill_switch_...`, `t_patrol_tick_skips_when_checkout_vanishes_...`)
belongs exclusively to the deleted patrol block; no non-patrol log line or
test was dropped alongside it. derived: `grep -rl
"patrol-poll\|poll-watchdog.log\|poll_heartbeat_last_state"` (PR-head)
hits only the script/test themselves and `on-the-record/hooks/poll-rearm.sh`,
which does not parse the patrol-specific lines. This is corroborated by
the PR's own delivery record
(`docs/issue-2925/reports/refactoring-legacy-seam-selection+silent-failure-audit-63ccc91e.md`
— untracked on this branch, lives only on the PR branch at commit
`53a4f5f1`, read via the `pr-2932-head` worktree), which shows the roster
call (`spawn.role_data()`) has thrown `AttributeError`, swallowed by
`2>/dev/null`, since the feature's introduction — patrol never actually
ran in production, so there was no previously-firing signal for any
downstream consumer to have depended on. Not a silent regression: nothing
that used to fire now silently doesn't.

canonical: grepped `consult.py`, `gates/*.py`, and this PR's touched files
for anything resembling patrol's promotion responsibility redistributed
elsewhere under a new name — nothing found; the `consult.py` key rename
and judge-log path rename are cosmetic, not a reintroduced promotion
mechanism. derived: `python3 -m pytest
on-the-record/monitors/test_poll_heartbeat.py test/test_retirement_count.py
-q` — `origin/main` 33 passed vs. PR-head 27 passed (exactly the 6 removed
patrol tests, no unrelated coverage loss, no new failures). No overhead
increase or monitor/watch breakage observed — both bash-version ticks
above completed normally.

**Open finding surfaced here (informational, not a PR-#2932 defect):**
canonical: `git grep -rn "role_data" -- . ':!docs'` on PR-head returns 4
hits, including a live call site
`bench/run.py:37: spec = spawn_mod.role_data()[skill]` — but no
`role_data` definition exists anywhere in `spawn.py`. derived: the same
grep against `origin/main` returns the identical 4 hits, confirming this
is **pre-existing**, not introduced by PR #2932, and unrelated to
patrol's own removal. It does, however, directly contradict the PR's
cited verification evidence (the PR's delivery record states this exact
grep returns nothing) and is a genuine dangling reference to the retired
`role_data()` roster query the patrol program depended on. Not a blocker
for PR #2932 (it doesn't touch `bench/run.py`), but the PR's own
evidentiary claim is factually wrong and should be corrected or
acknowledged.

canonical: `docs/specs/acceptance-commands.md:34` (both refs, unchanged by
this PR) — still lists a pytest command for a path named
`gates/test_patrol_board.py`; no file exists there (untracked / never
present at that path in this repo's tracked history). `docs/specs/enforcement-boundary.md`
(both refs, unchanged) still documents all five deleted patrol modules as
live. Both are living-spec docs, not historical audit records, so the
"docs/ never touched" discipline this PR followed leaves them stale
rather than corrected. Informational, out of scope for this PR under the
discipline it was operating on.

## Why

The spawning brief asked for adversarial coverage on five specific attack
points rather than general correctness (two parallel sessions cover the
general angle). Each attack point required sustained, independent digging
against live worktrees rather than trusting the PR's own description, so
the work was fanned out to five background workers per the freelunch
directive's research-task width rule (5 independent search angles,
comparable-to-100+-lines effort each → fan-out threshold met), each given
both worktrees and told to execute real commands rather than reason from
the diff. Findings were synthesized here without re-running the workers'
work (per the directive's no-verification-pass-on-return rule), but two
of their citations (the `precision_measure` import-scope claim and the
`role_data` grep discrepancy) were cross-checked against each other's raw
output and are reported with their exact commands so a reader can re-run
them.

## What did not work

None.

## Upstream basis

See the `upstream:` frontmatter list above for the exact paths and shas
read. In addition: `docs/specs/enforcement-boundary.md` and
`docs/specs/acceptance-commands.md` at `origin/main`
(`46779718d2435a8749d7c736e86d3f54a5dc30d5`, unchanged on PR head) were
read as corroborating, PR-independent evidence for the precision_measure
and stale-docs findings; `gh pr view 2932 --json ...` (this session) was
read for PR metadata (title, body, file list, addition/deletion counts).

## Open findings

1. The PR's delivery record claims `git grep -rn "role_data" -- . ':!docs'`
   returns zero hits; independently re-run (this session), it returns 4,
   including a live dangling call site at `bench/run.py:37`. Pre-existing
   on `origin/main`, not caused by this PR, and not a blocker to PR
   #2932's own scope — but the PR's cited verification evidence is
   factually incorrect and should be corrected in a follow-up, or at
   minimum acknowledged. Routed to the human/orchestrator for
   disposition; not fixed here per the adversarial-review skill's
   evaluate-don't-fix contract.
2. The literal "diff touches no docs/ file at all" check does not hold —
   3 docs/ files are touched (this PR's own delivery record + deviation
   log, and a mechanical `reconciled-index.md` checksum line). No
   historical patrol-named document was renamed, migrated, or modified,
   which is the substantive concern the check appears aimed at, and this
   part is clean. If the literal zero-touch reading was intended, this PR
   does not satisfy it; flagged for the human to judge which reading
   governs acceptance.
3. `docs/specs/acceptance-commands.md` and `docs/specs/enforcement-boundary.md`
   (living specs, not historical records) are now stale — they still
   describe the five deleted patrol modules as live and list a pytest
   command for a `test_patrol_board.py` path that does not exist. Left
   untouched under this PR's docs/-never-touched discipline; informational,
   routed to whoever owns those specs' upkeep.

## Next steps

None — `loop_state: landed`. derived: the acceptance-check evidence in
each of the five attack sections above (this record) is the basis for
this terminal state. This is a terminal, review-only record; no code was
changed by this session. The three open findings above are
informational/routed, not blockers to PR #2932's own claims: the
precision_measure deletion is justified, the six survivor-file edits are
resolved (not amputated) and independently executed against real inputs,
the judge_cmd() return-key fix is complete and consistent across every
caller, the deeper patrol-vocabulary sweep found nothing orphaned beyond
the docs/ literal-phrasing gap noted above, both bash-version ticks exit 0
with normal output, and no silent absorption or retired-role-axis revival
was found.

skill-verdict: adversarial-review — applied: invoked; loaded the skill
before evaluating PR #2932, followed its evaluator posture (find problems,
cite locations, evaluate-don't-fix) for every attack point above.
skill-verdict: work-in-english — applied: invoked; this record, all
commit/PR text, and worker prompts were written in English; only the
final chat summary to the user is in Korean.
