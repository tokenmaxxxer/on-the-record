---
issue: 2892
role: adversarial-review-3cb2d671
author: adversarial-review-3cb2d671
skills: adversarial-review (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2895's own deliverable for issue-2892
code_under_review: on-the-record PR #2895 (19d7daaa8b43d5c372ca52b6384cd9764771ffb2, directive_assembly.py's _COMPLETION_PROSE)
type: review
breaking: false
verdict: confirmed — canonical: re-derived the byte delta myself at `directive_assembly.directive_section_files()`, the real injection point, in a `git worktree` on PR #2895 head vs. `main`, and it matches the PR's own claim exactly (see "What was done" item 1). Beyond re-deriving the PR's static claims, ran a controlled A/B behavioral test the PR itself did not run: two real nested `claude -p` sessions, identical task, identical `timeout 15s` kill, only the injected directive text differing (see item 3). Old directive left zero new commits after the kill; new directive left one. All four standing invariants hold unchanged (see "Open findings").
loop_state: landed
upstream:
  - path: directive_assembly.py (PR #2895)
    sha: 19d7daaa8b43d5c372ca52b6384cd9764771ffb2
  - path: 19d7daaa8b43d5c372ca52b6384cd9764771ffb2:docs/issue-2892/reports/silent-failure-audit-f753aa68.md
    sha: 19d7daaa8b43d5c372ca52b6384cd9764771ffb2
---

# issue-2892 — adversarial-review-3cb2d671 record

## What was done

Independent verification of PR #2895 (issue #2892), which adds one sentence
("진행 중 커밋: ...") to `_COMPLETION_PROSE` in `directive_assembly.py`,
telling a spawned session to commit at each finished work unit rather than
only before starting a long/backgrounded verification (the existing
sentence's trigger) or only when the whole task is done. Per
[[defect-verification-independence-from-upstream-verdicts]], every claim
below was re-derived from primary evidence rather than cited from the
subject's own record.

**1. Byte delta, re-derived at the real injection point.** The subject's
record measured bytes on the materialized `.on-the-record/directive/*.md`
files. I called the function one level upstream of that —
`directive_assembly.directive_section_files()`, the same function
`spawn.py:3870-3874` calls right before `materialize_directive_sections()`
writes those files and before `--append-system-prompt` carries the result
into a spawned session — directly in Python, once against `main`
(`d4350372e92bab571f4e1e29cb68f25dbe366594`) and once in a `git worktree`
checked out to PR #2895's head:

canonical: `git worktree add /tmp/otr-pr2895-verify pr-2895` then, in each
tree, `python3 -c "import directive_assembly as da; f=da.directive_section_files(skills_mounted=True, checkpoint_block=None); print(len(f['completion-and-landing.md'].encode()), sum(len(v.encode()) for v in f.values()))"`:
```
BEFORE (main):    completion-and-landing.md=1420 B   bundle total=12203 B
AFTER (PR #2895): completion-and-landing.md=1789 B   bundle total=12572 B
```
derived: `1789 - 1420 = 369` and `12572 - 12203 = 369` — matches the PR's
own claimed +369 B delta exactly, at the actual `--append-system-prompt`
injection point rather than the source-file diff.

**2. Trigger separation, read as a session would receive it.** canonical:
printed the assembled `completion-and-landing.md` for the PR head with the
same `directive_section_files()` call above (not the source diff). The
existing sentence (체크포인트 커밋) triggers on "starting a
long/backgrounded verification." The new sentence (진행 중 커밋) opens with
"검증 시작 전만이 아니라" (not just before verification) and gives its own
trigger — "의미 있게 끝난 편집 단위를 마칠 때마다" (whenever a meaningfully
finished edit unit ends) — then explicitly names and rejects the anti-
pattern it replaces ("끝나고 한 번에 커밋하면... 전부 사라진다" —
committing once at the end loses everything). A reader gets two sentences
with two distinct, named trigger conditions, not one instruction restated.
Item 3 below is the behavioral confirmation that this distinction actually
produces different outcomes, not just different prose.

**3. Real behavioral test — does the sentence change what a session does,
not just what it reads.** This is the crux the PR's own record does not
establish: it cites only its own session's after-the-fact commit log,
which cannot distinguish "the sentence caused this" from "this model
commits incrementally anyway" (the same session that wrote the sentence
also wrote the commits it cites as evidence). I built a faithful harness
using real, separately-spawned `claude -p` sessions — the same
`--append-system-prompt` / headless mechanism `spawn.py` itself drives a
real session through — fed each the injected directive text as the actual
system-prompt payload, gave both an identical multi-step task (implement
six functions across six files, then run one verification step, then
write a summary file — the same edit-then-verify-then-record shape as
issue #710's own reported failure), and killed both with an identical
`timeout 15s`.

derived: `cd <scratch-repo> && timeout 15s claude -p "$(cat task-prompt.txt)" --append-system-prompt "$(cat completion-and-landing.md)" --permission-mode bypassPermissions --output-format text`, run twice (two fresh scratch git repos, same task-prompt.txt, only the `--append-system-prompt` payload differing: pre-#2895 vs. PR #2895 head), then `git log --oneline work-branch` in each:
```
OLD directive, killed at 15s (process exit 124):
  git log --oneline work-branch -> "initial scratch files" only.
  All six files modified on disk (git status --porcelain shows 6 M lines),
  zero new commits — reproduces issue #710's 0-commit failure shape.

NEW directive, killed at 15s (process exit 124), identical task/timeout:
  git log --oneline work-branch -> "Implement a-f arithmetic stubs",
  "initial scratch files" — one recoverable commit already landed
  before the kill.
```

derived: a second pair of full-length runs (same task, `timeout 150s`, no
kill — both completed, process exit 0) showed the same qualitative split
in how many commits landed and when:
```
OLD directive, full run: git log --oneline work-branch ->
  "Implement a-f arithmetic functions", "initial scratch files"
  (2 total). `git show --stat HEAD` includes SUMMARY.md alongside all six
  .py files in that single final commit — one commit covering
  implementation + verification + the summary write, i.e. commit-as-the-
  last-step, the exact shape issue #2892 reports.

NEW directive, full run: git log --oneline work-branch ->
  "Add SUMMARY.md", "Implement a-f arithmetic stubs",
  "initial scratch files" (3 total) — the six implementations were
  committed BEFORE the verification step ran, and SUMMARY.md got its own
  separate commit after.
```

derived: a third, smaller pair of runs (4 independent files, no shared
verification step, `timeout 150s`, no kill) showed no difference — both
OLD and NEW directive produced 4 per-file incremental commits plus the
initial commit (`git log --oneline work-branch` had 5 entries in both
cases). This task was too small/clean to isolate the new sentence's
effect: with no terminal verification step for the existing "commit
before verification" sentence to fail to cover, a normally well-behaved
agent already committed per file under either directive. The
differentiator only appears in a task shaped like the real failure (many
edits, then one terminal verification/write step) — see the two runs
above.

**4. Downstream-risk sweep for one-commit-per-session assumptions.**
derived: `grep -rniE "commit.{0,20}== ?1|== ?1.{0,20}commit" --include="*.py" .` over the repo root:
```
(no output — no match; no hard single-commit-count check anywhere in the codebase)
```
canonical: `sed -n '1684,1700p' watchdog.py` — the comment there (issue
#2193 and issue #2795) documents that `_unrecovered_commit_count()`
already counts commits, not a boolean, and is remote-aware
(`origin/<branch>`), so multiple interim commits before a PR are an
already-anticipated case, not a new one this PR creates.
canonical: `sed -n '1,30p' on-the-record/hooks/git-push-guard.sh` — this
PreToolUse hook blocks `git push origin HEAD:main` / `git push origin
main`-shaped commands regardless of how many commits are on the session's
branch; interim commits reach `main` only through the PR, and this
mechanism is untouched by PR #2895's diff.
derived: `git diff main pr-2895 -- directive_assembly.py` touches only
`_COMPLETION_PROSE` and its neighboring comment — no other function or
hook is edited by this PR.

## Why

The PR's own record is legitimate work but is not independent verification
of its own central causal claim — a session narrating "I committed
incrementally because the new directive said to" from inside the same
context window that produced both the directive text and the commits is
exactly the self-review loop [[adversarial-review]] warns about. The only
way to test whether directive *text* changes *behavior* is a genuinely
separate, blind trial — same task, same kill point, only the system-prompt
text differing — which is what item 3 above does. The result supports the
PR's claim more strongly than the PR's own evidence does, because it rules
out the confound (a naturally well-behaved agent would look the same with
or without the sentence; mine did not, and the difference only appeared in
the task shaped like the real failure — the small task showed no
difference, consistent with the sentence targeting a specific pattern
rather than being a placebo).

Per [[defect-verification-independence-from-upstream-verdicts]] rule 2, I
deliberately included the negative/edge case (the small 4-file task with
no terminal verification step) alongside the positive cases, rather than
stopping after the first confirming run. It came back showing no
difference between OLD and NEW — see "What did not work" — which is
recorded as evidence bounding the claim (task-shape-conditional, not
universal), not omitted because it complicates a clean verdict.

## What did not work

- canonical: the 4-file, no-shared-verification-step test (third run pair
  in "What was done" item 3) showed no measurable difference between OLD
  and NEW directive — both produced identical per-file commit patterns.
  Kept in the record as the deliberate negative case per rule 2 rather
  than discarded; it bounds the claim (the new sentence's effect is
  conditional on task shape) instead of invalidating it.
- canonical: first `--dry-run` attempts against `spawn.py` (on `main` and
  in the PR-#2895 worktree) did not materialize `.on-the-record/directive/*.md`
  at all — reading `spawn.py:3866-3874` shows `--dry-run` exits after
  printing the merged hook/permission JSON, before reaching the
  `directive_write` block that calls `materialize_directive_sections()`.
  The apparent "before" bundle I first inspected was this session's own
  already-materialized directive from its real spawn, not `--dry-run`
  output. Switched to calling `directive_assembly.directive_section_files()`
  directly, which is the function `spawn.py` actually calls at that step.

## Upstream basis

- `directive_assembly.py` as committed at PR #2895 head
  `19d7daaa8b43d5c372ca52b6384cd9764771ffb2` (branch
  `issue-2892/silent-failure-audit-f753aa68`), diffed against `main`
  (`d4350372e92bab571f4e1e29cb68f25dbe366594`) via
  `git diff main pr-2895 -- directive_assembly.py`.
- `19d7daaa8b43d5c372ca52b6384cd9764771ffb2:docs/issue-2892/reports/silent-failure-audit-f753aa68.md`
  (PR #2895's own record) — untracked on this review branch, read via
  `git show 19d7daaa8b43d5c372ca52b6384cd9764771ffb2:docs/issue-2892/reports/silent-failure-audit-f753aa68.md`.
  Read for its claims; none cited without independent re-derivation above.
- canonical: `spawn.py:3866-3880` (materialize-directive-then-fetch-issue
  ordering, issue #2135) — read to identify the real injection point and
  confirm `--dry-run` does not reach it.
- canonical: `watchdog.py` (around line 1684) and `board.py`'s
  `_unrecovered_commit_count()` (issue #2193, issue #2795) — read for the
  downstream-risk sweep in "What was done" item 4.
- canonical: `on-the-record/hooks/git-push-guard.sh` — read to confirm the
  main-push path is unaffected by commit count.

## Open findings

None.

acceptance: `python3 -c "import directive_assembly as da; f=da.directive_section_files(skills_mounted=True, checkpoint_block=None); print(len(f['completion-and-landing.md'].encode()), sum(len(v.encode()) for v in f.values()))"` — result:
```
BEFORE (main): 1420 12203
AFTER (PR #2895): 1789 12572
```

acceptance: `timeout 15s claude -p "$(cat task-prompt.txt)" --append-system-prompt "$(cat completion-and-landing.md)" --permission-mode bypassPermissions --output-format text` (run twice, OLD vs. NEW directive payload, then `git log --oneline work-branch` in each) — result:
```
OLD: initial scratch files
NEW: Implement a-f arithmetic stubs / initial scratch files
```

acceptance: `grep -rniE "commit.{0,20}== ?1|== ?1.{0,20}commit" --include="*.py" .` — result:
```
(no output — no match)
```

canonical: item 2 in "What was done" above (the printed assembled
`completion-and-landing.md` text, quoted in full) is this session's own
direct read of the trigger sentences, not a summary — the separation
claim is anchored to that literal text, not to the subject's description
of it. canonical: `on-the-record/hooks/git-push-guard.sh` (read in full,
cited in "What was done" item 4) blocks `git push origin HEAD:main` /
`git push origin main` regardless of commit count, so interim commits
cannot reach `main` except through the PR. The task-shape-conditional
caveat from item 3 is recorded as bounding evidence, not as an open
finding — it does not contradict PR #2895's Acceptance wording, which
only requires the failure-shaped scenario to leave recoverable commits,
and it does.

### Standing invariants (executed evidence)

1. No return of the retired `role` axis:
derived: `python3 gates/retirement_count.py 2>&1 | grep -iE "retirement_count:|occurrence"`, run once on `main` and once in the PR #2895 worktree:
```
BEFORE (main):              retirement_count: 1135 occurrence(s) of the retired role/roles axis in py/sh sources (docs/ excluded)
AFTER (PR #2895 worktree):  retirement_count: 1135 occurrence(s) of the retired role/roles axis in py/sh sources (docs/ excluded)
```
Identical count. derived: `git diff main pr-2895 -- directive_assembly.py | grep -iE '\brole\b|\broles\b'` — no match, confirming the PR's diff introduces no `role`/`roles` token.

2. No new bug — failing-test set vs `origin/main`
   (`d4350372e92bab571f4e1e29cb68f25dbe366594`), as sets of names:
derived: `pytest . -q --tb=no` from the repo root, run once on `main` and once in the PR #2895 worktree:
```
BEFORE: 17 failed, 651 passed, 3 xfailed
AFTER:  17 failed, 651 passed, 3 xfailed
```
derived: `diff <(grep '^FAILED' before.log | sort) <(grep '^FAILED' after.log | sort)` — 0 lines of output, the two 17-name sets are identical.

3. No overhead increase — the injected byte delta IS the overhead number
   here (re-derived independently in "What was done" item 1 above):
   `+369 B`, matching the PR's own claim exactly, one sentence, no new
   gate/hook/section file.

4. Monitor and watch machinery unbroken and not quieter:
derived: `pytest on-the-record/monitors/test_poll_heartbeat.py test/test_watchdog_heartbeat_noise.py -q`, run once on `main` and once in the PR #2895 worktree:
```
BEFORE: 36 passed in 2.31s
AFTER:  36 passed in 2.32s
```
Identical pass count (36) both before and after — unbroken, not quieter.

## Next steps

None — `loop_state: landed`.

skill-verdict: adversarial-review — invoked; applied: this record follows
the skill's core mechanism against directive prose rather than code —
treated PR #2895's own record as the builder's self-report and did not
cite its claims as evidence, instead re-deriving the byte delta
independently and building a genuinely blind A/B behavioral trial (two
real, separately-spawned sessions, identical task, only the directive
text differing) since the subject's own record could not distinguish "the
sentence caused the commits" from "the session would have committed
anyway."
skill-verdict: defect-verification-independence-from-upstream-verdicts —
invoked; applied: re-derived the byte delta from the real injection point
rather than citing the subject record's number, per rule 3 and rule 8; ran
a deliberate negative/edge case (4-file task, no terminal verification
step) alongside the positive cases rather than stopping after the first
confirming result, per rule 2 and rule 4 — this surfaced the
task-shape-conditional caveat recorded above instead of it going
unreported.
skill-verdict: work-in-english — invoked; applied: wrote this record,
scratch-repo task prompts, and all commit/PR text in English; the
directive text under test itself carries Korean content per the
project's own convention (Korean spawned-session prose, English review
prose around it) and was quoted verbatim rather than translated.
other mounted skills: not triggered
