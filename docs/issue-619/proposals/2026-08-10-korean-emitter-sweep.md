---
status: proposed
files:
  - spawn.py
  - test_spawn.py
  - docs/issue-619/reports/implementation.md
---

## Request

#619: repo-bound output from the deployed surface (issue/PR comments,
committed records, parser-matched refusal texts) must be English, using
stable machine-matchable tokens. Console-only Korean UX may stay Korean,
but each emitter string must be classified explicitly. Do not rewrite
merged history — only change emitters, and update any parser matching
Korean in the same unit.

## Constraints

- No rewriting of already-merged issue comments or committed records —
  only the emitter code changes going forward.
- Every changed/kept string gets classified repo-bound vs console-only in
  this record.
- Any parser matching Korean in the changed strings updates in the same
  commit as the emitter (survey found none exists for the field labels;
  the marker constant is both defined and matched inside `spawn.py`
  itself).
- Phase 1 (this PR) proposes only; delivery happens in a phase-2 PR that
  carries `Closes #619`.

## Rationale

Considered leaving the Korean field labels (워크스페이스/로그/트리거/브랜치/
사유/상세) as-is and only translating the marker's Korean substring
(재스폰 상한... 도달), on the theory that the labels are self-evident from
position and translating only the machine-matched part would satisfy the
letter of "stable machine-matchable tokens." Rejected: the issue's stated
motivation is explicitly locale-fragile *downstream parsing* (remediation
spawn templates, #597's framing writer) — a comment body that mixes
English structural tokens with Korean field labels is still not
machine-matchable by a parser written against English conventions, and
it leaves the four templates internally inconsistent (three already-
English markers next to Korean bodies). Converting the full four-function
set to one consistent English vocabulary is the option that actually
resolves the stated parsing friction, not just the marker string.

## Accumulation

This touches the four inline `subprocess.run(["gh", "api", ...])`
issue-comment call sites in `spawn.py`, an already-existing repeated
shape (not introduced by this change). The change only edits each call's
body f-string content (Korean → English field labels/sentences) in
place — it adds no new call site and no new shared helper, so it does not
grow the accumulation count. If more such issue-comment emitters appear
later, the accumulation question is the same one the existing shape
already carries (whether to factor the four `_post_*_comment` functions
into one templated helper); that dedup question is unaffected by this
text-only translation and is out of #619's scope.

## What will be done

- In `spawn.py`, translate the Korean body text of the four issue-comment
  emitters (`_post_crash_comment`, `_post_stall_comment`,
  `_post_session_end_comment`, `_post_stranded_push_comment`) to English,
  replacing the field labels 워크스페이스/로그/트리거/브랜치/사유/상세 with
  stable English tokens (`workspace:`, `log:`, `trigger:`, `branch:`,
  `reason:`, `detail:`) and translating the explanatory sentences.
- Translate `_CRASH_COMMENT_MARKER`'s embedded Korean substring
  (재스폰 상한({cap}) 도달 → English equivalent, e.g. "respawn cap
  ({cap}) reached") so all four marker constants are consistently
  English; the other three markers already are.
- Verify (survey already did this, re-confirm in phase 2) that no code in
  `spawn.py` or `test_spawn.py` matches on the Korean substrings being
  removed — tests reference markers via the constants, not retyped
  literals, so no test-literal edits are expected, only a green run.
- Classify every console-only Korean site found in the survey
  (spawn.py's `clean` subcommand output, kill-signal/warning/hint prints,
  `--help` text) as out-of-scope-by-design, and list them explicitly in
  the phase-2 record per #619's acceptance "empty state" clause.
- Run the full test suite (pytest) after the change and paste fenced
  output in the phase-2 record.

## Out of scope

- Gate/hook refusal strings in `gates/*.py` and
  `on-the-record/hooks/*.sh` — survey traced these to local stdout/CI-log
  output or assistant-prose-matching regexes, never a `gh api ...
  comments` call or a committed-record write; they are not repo-bound
  emitters under this issue's definition and are not touched.
- Console-only Korean prints (`clean` subcommand summary, kill/warning
  hints, `--help` text) — left as Korean, listed in the phase-2 record.
- Rewriting any already-merged issue comment or committed record.
- Any translation work outside `spawn.py`'s four comment emitters — the
  survey found no other repo-bound Korean emitter.
- Factoring the four emitters into a shared templated helper — a
  dedup/accumulation question, not a translation, deferred per the
  Accumulation section above.

## How you'll know it worked

- `grep -P '[\x{AC00}-\x{D7A3}]'` over the bodies built by the four
  `_post_*_comment` functions (and `_CRASH_COMMENT_MARKER`) in `spawn.py`
  returns nothing.
- `pytest test_spawn.py` (and the full suite) passes, fenced output in
  the phase-2 record.
- The phase-2 record lists every console-only Korean site left unchanged,
  matching the survey's inventory.
