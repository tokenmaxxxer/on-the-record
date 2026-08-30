---
issue: 2893
role: independent-verification-2
author: independent-verification-2
verifies_subject: true  # this record is an independent verification of PR #2898 (issue-2893/diagnose-first-6a58e6a9)
code_under_review: on-the-record/hooks/skill-verdict-guard.sh, gates/record_lint.py, on-the-record/gates/record_lint.py, directive_assembly.py, docs/handbooks/skill-verdict-obligation.md, test/test_skill_verdict_guard_zero_invocation_signal.py
type: verification-record
breaking: false
verdict: PASS-with-one-unaddressed-acceptance-criterion — the root-cause derivation, the zero-invocation record check, and the before/after hook behavior all independently reproduced; the issue's own explicit "must not grow injected directive bytes without stating the delta" line is violated in substance (the injected `_SKILL_VERDICT_PROSE` grew 907→1460 bytes, +60%) and the delta is never stated anywhere in the record
loop_state: landed
upstream:
  - path: docs/issue-2893/reports/diagnose-first-6a58e6a9.md
    sha: cf7ee7d749b3eb3ef89bb358ab0d65d3dc1d7ec5
---

# issue-2893 — independent-verification-2 record

## What was done

canonical: `gh issue view 2893 --comments` (read this session, before starting).

Independent verification of PR #2898 (`issue-2893/diagnose-first-6a58e6a9` → `main`, `Closes #2893`). The upstream record, `docs/issue-2893/reports/diagnose-first-6a58e6a9.md` (untracked on this verification branch — exists on `issue-2893/diagnose-first-6a58e6a9` / inside PR #2898, not on `main`), is the record under verification. Checked out the PR head into a scratch worktree (`git worktree add /tmp/pr2898-check pr-2898 -f`, removed at the end of this session) and `origin/main` into a second worktree (`/tmp/main-check`), and re-ran the PR's own claims from scratch rather than trusting its record.

Reproduced independently, this session:

- **Unit test count.** `python3 -m pytest test/test_skill_verdict_guard_zero_invocation_signal.py -q -o addopts=""` on the PR worktree → `7 passed`, matching the record exactly.
- **Full-suite count and failing-set identity, re-run on both trees, not diffed against the PR's own pasted output.** PR worktree: `python3 -m pytest . -q -o addopts=""` → `17 failed, 654 passed, 3 xfailed`. `origin/main` worktree: `17 failed, 651 passed, 3 xfailed` (the 3-test gap is exactly the 3 new cases the PR says it added). Extracted both `FAILED ...` line sets, sorted, diffed with plain `diff` → empty (`IDENTICAL FAILURE SETS`, confirmed by my own script run, not the PR's). This independently confirms the "no new failures" acceptance line.
- **`retirement_count.py`, re-run on both trees.** PR worktree: `python3 gates/retirement_count.py` → `1135 occurrence(s)`. `origin/main` worktree: same command → `1135 occurrence(s)`. Exact match, confirming "unchanged from origin/main."
- **The two packaged copies of the new check stay identical.** `diff gates/record_lint.py on-the-record/gates/record_lint.py` on the PR worktree → empty. `zero_invocation_summary_check` reads correctly in both.
- **`decision: "block"` audit.** `grep -n 'decision' on-the-record/hooks/skill-verdict-guard.sh` on the PR worktree: every hit is either a comment disclaiming block behavior or absent from the actual `finish()`/JSON-emission code path — `finish()` only ever emits `hookSpecificOutput.additionalContext`, confirmed by direct read of `finish()`'s body (`on-the-record/hooks/skill-verdict-guard.sh:209-218`). No blocking behavior was introduced.
- **Before/after behavior change, reproduced by directly running the real shipped hook script (not a mock), on a synthetic transcript matching the issue's own consumer-session shape (one mounted skill, zero Skill-tool invocations, on an `issue-2893/implementation` branch with a pre-existing record missing the summary line) — this is the acceptance's "count Skill tool calls... before and after" check, executed against the actual production code path rather than re-typing the PR's own claimed numbers:**
  - Copied `test/test_skill_verdict_guard_zero_invocation_signal.py` (PR version) into the `origin/main` worktree and ran it there: `1 failed, 6 passed` — the one failure is exactly `ZeroInvocationRecordSummaryTest::test_missing_summary_line_is_named_in_the_notice`, asserting `"issue #2893" in ctx`, which pre-fix code cannot produce (pre-fix `skill-verdict-guard.sh` never reads the record file on the zero-invocation branch at all).
  - Same test file, same hook, on the PR worktree (post-fix): `7 passed`.
  - This is a directly-executed, deterministic before/after reproduction of the fix's actual effect: 0 Skill-tool calls in the transcript in both cases (matching the record's own live-`claude -p` finding that invocation logic is untouched by design), but the Stop hook's `additionalContext` differs — pre-fix, silent about the record; post-fix, names the missing `other mounted skills: not triggered` line and cites issue #2893.
- **The one open finding: the "must not grow injected directive bytes without stating the delta" acceptance line.** The fix's `directive_assembly.py` change rewords `_SKILL_VERDICT_PROSE` (materialized into `skill-obligations.md`, which rides `--append-system-prompt` at turn 1 whenever any skill is mounted — the same mechanism visible at the top of this very session's own system prompt). Measured directly by importing the module in both worktrees:
  ```
  derived: python3 -c "import directive_assembly as da; print(len(da._SKILL_VERDICT_PROSE.encode('utf-8')))"
  origin/main worktree: 907
  PR worktree:          1460
  delta: +553 bytes, +61%
  ```
  Grepped the PR's own record for any mention of this delta — `grep -n "byte\|delta" docs/issue-2893/reports/diagnose-first-6a58e6a9.md` on the PR worktree (untracked on this verification branch, same file as above) — the only "byte-identical" mentions found are about the two packaged `record_lint.py` copies and about the zero-mounted-vs-mounted-but-unused test comparison, not about `_SKILL_VERDICT_PROSE`'s growth. No number, no acknowledgment, anywhere in the record. This is a concrete, executed-live miss against one of the issue's three explicit acceptance "must not" clauses.

## Why

Chose to re-derive the two headline counts and the before/after behavior rather than re-read the PR's own pasted output, per the standing independent-verification convention: a record dense with `derived:`/`canonical:` tags is easy to cite without checking. The PR's record itself is unusually thorough (it even self-discloses a mid-session invoke-before-apply mistake caught by its own Stop hook, corrected in place rather than quietly amended — a good signal for its overall care), so the highest-value use of this session was hunting for a claim the record's own thoroughness might have let slip past, rather than re-confirming things already well-evidenced.

That is what the byte-delta check was for. The issue's acceptance list has exactly three "must not" sub-clauses (no per-turn reminder, no mandatory invocation, no unstated byte growth); the record's "Why this shape, not a stronger nudge" section explicitly addresses the first two by name but never mentions the third, even though the very prose it is rewording (`_SKILL_VERDICT_PROSE`) is injected-directive content by the record's own admission ("the full `_SKILL_CHECK_PROSE`/`_SKILL_VERDICT_PROSE` text riding `--append-system-prompt` at turn 1"). Measuring the actual before/after byte counts (rather than assuming "just a reword" is small) confirmed this is not a rounding-error omission: +553 bytes is a 61% growth of that one constant, on every session with any mounted skill.

## What did not work

None — every independently re-run command reproduced its claimed output on the first attempt; no approach was tried and abandoned this session.

## Upstream basis

- `docs/issue-2893/reports/diagnose-first-6a58e6a9.md` (sha in frontmatter; untracked on this verification branch — exists on `issue-2893/diagnose-first-6a58e6a9` / inside PR #2898) — the record under verification.
- PR #2898 (`gh pr view 2898`, `git diff origin/main...pr-2898`), read in full this session.
- `origin/main` (fetched this session) — the pre-fix baseline used for every independent re-derivation above.

## Open findings

1. **The record never states the injected-directive byte delta the issue's own acceptance explicitly requires when the fix grows it.** `_SKILL_VERDICT_PROSE` grew 907→1460 bytes (+553, +61%, derived above in "What was done") and this number appears nowhere in `docs/issue-2893/reports/diagnose-first-6a58e6a9.md` (untracked on this verification branch — same file cited in "Upstream basis" above). This does not break any test and the growth itself (clarifying that the "all-uninvoked" case now owes a summary line) is plausibly a reasonable size for the content added — but the issue's acceptance criterion was "must not grow ... without stating the delta," not "must not grow only if the growth is small," and the record simply doesn't address it. Resolution path: a follow-up amendment to the record (or a PR comment) stating this delta would close the gap; it does not require reverting or re-doing the code change itself.

## Next steps

None required from this role — `loop_state: landed`.
acceptance: `python3 -m pytest test/test_skill_verdict_guard_zero_invocation_signal.py -q -o addopts=""` (this session, PR worktree) — result:
```
.......
7 passed in 0.36s
```
This verification session's own checks (full-suite identical-failure-set diff, `retirement_count.py` match, before/after hook run, byte-delta measurement, all in "What was done" above) are complete; the one open finding above needs a follow-up amendment to the PR's own record, not further work from this role.

skill-verdict: work-in-english — applied: invoked; this record and the session's Korean-facing summary follow that skill's routing (repo-bound artifacts in English, user-facing summary in Korean) — invoked via the Skill tool this session before writing this record.
other mounted skills: not triggered.
