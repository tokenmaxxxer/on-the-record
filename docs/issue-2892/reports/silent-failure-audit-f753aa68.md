---
issue: 2892
role: silent-failure-audit-f753aa68
author: silent-failure-audit-f753aa68
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: directive_assembly.py
type: implementation-record
breaking: false
verdict: incremental-commit-sentence-added-to-completion-and-landing-md
loop_state: landed
upstream:
  - path: directive_assembly.py
    sha: same-commit
---

# issue-2892 — silent-failure-audit-f753aa68 record

## What was done

Added one instruction to `_COMPLETION_PROSE` in `directive_assembly.py`
(lines 139-143 as committed) — the source of the `completion-and-landing.md`
section that on-the-record materializes into every spawned session's
`.on-the-record/directive/` and injects via `--append-system-prompt`. The
existing checkpoint-commit sentence in that constant only fires "before
starting a long/backgrounded verification"; it does not cover a session
that edits many files, passes its build (verification already done), and
is killed while writing its record next — the exact failure this issue
reports (21 edited files, 3 new files, build green, 0 commits, killed at
the 220-turn limit).

The new sentence ("진행 중 커밋: ...") generalizes the trigger from "about
to verify" to "finished a work unit," instructs committing right there
rather than once at the end, and states explicitly that these interim
commits land only on the session's own branch — `main` is still reached
only through the PR.

canonical: `git diff HEAD~1 HEAD -- directive_assembly.py` (this session's
own commit `ecbe839c8a32fa2b5d74bb4dc9dea80136224ada`):
```diff
+# Issue #2892: the checkpoint-commit sentence below only fires "before
+# starting a long/backgrounded verification" -- a session that edits many
+# files, passes its build, and is killed while writing the record next
+# (verification already done, commit still pending) falls outside that
+# trigger. The added sentence generalizes the trigger to "finish a work
+# unit," not "about to verify," and is worded to fire mid-task rather than
+# reduce to "commit when done."
 _COMPLETION_PROSE = (
@@ (existing lines unchanged) @@
+    "진행 중 커밋: 검증 시작 전만이 아니라, 의미 있게 끝난 편집 단위를\n"
+    "마칠 때마다 그 자리에서 커밋하라 — 끝나고 한 번에 커밋하면 턴\n"
+    "한도가 그 사이 어디서 끊기든 이전 작업이 전부 사라진다. 이 중간\n"
+    "커밋은 이 세션 자신의 브랜치에만 쌓인다, main 은 여전히 PR 로만\n"
+    "받는다.\n"
```

Byte delta (Acceptance bullet 1), derived — measured against the pre-change
constant (`git show HEAD~1:directive_assembly.py`, loaded and evaluated
before/after this session's own edit):
```
completion-and-landing.md bytes: before=1420 after=1789 delta=+369
total directive bundle bytes (skills_mounted=True, code_scoped=True): before=12203 after=12572 delta=+369
```
The delta is +369 B (369/4 ≈ 92 tok by this repo's byte/4 convention) on a
~12.2 KB bundle — one sentence, no new section, no new trigger line, no
gate, no hook.

## Why

The issue's own evidence — a session for #710 hit the 220-turn limit with
0 commits after 21 edited files and a passing build — shows committing is
the last step in current practice, so a hard turn-limit ceiling can land
anywhere and lose everything before it. The issue's own grep
(`commit (early|often|incrementally)|중간.*커밋|commit as you go` over
`*.md`/`*.sh`/`*.py`, docs/ excluded) missed the nearest existing text
(`체크포인트 커밋`, this same `_COMPLETION_PROSE` constant, unchanged
lines 128-131) because that sentence's own trigger — "before starting a
long/backgrounded verification" — does not cover the reported failure
mode: the session's build (its verification) had already passed, and it
died on the step after, writing the record. Rather than add a new
section (issue #2135 governs directive bytes as overhead), this session
extended the existing sentence's neighbor with a second, distinctly
triggered sentence in the same constant, keeping the "why" (turn limit can
land mid-work) and the "where" (own branch only, PR still gates main)
inside the same paragraph a session already reads.

Considered and rejected: patching `tokenmaxxxer-core`'s
`core/directive/session-protocol.md` (the file carrying the analogous
`git add` warning this issue's acceptance explicitly must not touch)
instead of, or in addition to, `directive_assembly.py`. Rejected because
this session is spawned against `on-the-record#2892` only — the
role-handoff contract's own scoping rule (verified in
`docs/issue-2827/_assets/tokenmaxxxer-core-patch/README.md`, the prior
session that had to make the same call for issue #2827) restricts this
session's write authority to the on-the-record repo, branch, and PR; it
has no issue, branch, or review path in `tokenmaxxxer-core`. The issue's
own acceptance wording — "`bash core/hooks/directive.sh` (or the
on-the-record equivalent that emits the session directive)" — accepts
either mechanism, and `directive_assembly.py` is that on-the-record
equivalent: it is the file this repo's own spawned sessions (including
this one, which received this exact prose at session start) actually run
through.

## What did not work

None.

## Upstream basis

`directive_assembly.py` lines 120-152 (as committed at
`ecbe839c8a32fa2b5d74bb4dc9dea80136224ada`), `sha: same-commit`.

## Standing invariants (executed evidence)

1. No return of the retired `role` axis, derived:
```
git diff --unified=0 -- directive_assembly.py | grep -iE '\brole\b|\broles\b'
```
result: no match (`no role/roles token in diff`). Baseline count unaffected:
```
python3 gates/retirement_count.py 2>&1 1>/dev/null | tail -1
```
result: `retirement_count: 1135 occurrence(s) of the retired role/roles axis in py/sh sources (docs/ excluded)` — identical before and after this session's commit (this session's diff touches no `role`/`roles` token).

2. No new bug — failing-test set vs `origin/main` (`d4350372e92bab571f4e1e29cb68f25dbe366594`), as sets of names via `pytest . -q --tb=no` from the repo root, run twice from the same working tree (once with this commit applied via `git stash`, once with it stashed out): both runs report `17 failed, 651 passed, 3 xfailed`, and the 17 failed test IDs are the identical set in both runs (`test_first_contact_fires_once_per_workspace`, `test_origin_captured_before_workspace_reassignment`, the `test_spawn_cross_family_skill_selection.py`/`test_spawn_artifact_skill_pairing.py`/`test_spawn_skill_judge_haiku_timeout_overlap.py` clusters, `test_convention_equivalence.py`'s two, and `test_pre_existing_post_tool_use_commands_are_all_still_present`) — none of these touch `directive_assembly.py` or `_COMPLETION_PROSE`; this commit adds zero new failures and fixes none of the pre-existing 17.

3. No overhead increase — the directive byte delta IS the overhead number here: +369 B (see byte-delta block above), a single sentence extending an existing constant, no new gate/hook/section file.

4. Monitor and watch machinery unbroken and not quieter: `on-the-record/monitors/test_poll_heartbeat.py` and `test/test_watchdog_heartbeat_noise.py` are both inside the `pytest .` run above and both pass in both the with-commit and without-commit runs (part of the identical 651-pass set) — this commit does not touch `on-the-record/hooks/directive.sh`, `on-the-record/monitors/`, or any poll/watchdog path.

## Open findings

None.

## Next steps

None — `loop_state: landed`.

skill-verdict: silent-failure-audit — not-applicable: this task's deliverable is a one-sentence prose addition to a directive string constant (`directive_assembly.py`'s `_COMPLETION_PROSE`); it adds no try/catch, Promise rejection, error callback, or result-type path for the audit to enumerate.
skill-verdict: work-in-english — invoked; applied: wrote the code comment, commit message, and this record in English (matching the surrounding prose's own Korean-content/English-comment convention for the added Korean sentence itself, per that skill's project-convention-conflict guard), Korean reserved for the final user-facing reply.
other mounted skills: not triggered
