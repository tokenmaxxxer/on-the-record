---
issue: 2893
role: silent-failure-audit-1745a079
author: silent-failure-audit-1745a079
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2893/reports/diagnose-first-6a58e6a9.md
    sha: cf7ee7d749b3eb3ef89bb358ab0d65d3dc1d7ec5
  - path: directive_assembly.py
    sha: same-commit
  - path: gates/record_lint.py
    sha: 4d1dde6c0a87f20248bae35d8193e562c0fc70f1
  - path: on-the-record/gates/record_lint.py
    sha: 4d1dde6c0a87f20248bae35d8193e562c0fc70f1
  - path: on-the-record/hooks/skill-verdict-guard.sh
    sha: 4d1dde6c0a87f20248bae35d8193e562c0fc70f1
  - path: docs/handbooks/skill-verdict-obligation.md
    sha: 4d1dde6c0a87f20248bae35d8193e562c0fc70f1
---

# issue-2893 — silent-failure-audit-1745a079 record

## What was done

Round 2 on PR #2898 (issue #2893). Merged PR #2898's branch
(`issue-2893/diagnose-first-6a58e6a9`, head `cf7ee7d749b3eb3ef89bb358ab0d65d3dc1d7ec5`)
into this branch and made one further change on top: reworded
`directive_assembly.py`'s `_SKILL_VERDICT_PROSE` to deliver the same
all-uninvoked durable-trace requirement (issue #2893's fix) at a smaller
byte cost, and disclosed that acceptance criterion 1 was not fully
satisfiable as written.

Both independent verifications of PR #2898 (#2900, #2901, both merged)
confirmed the diagnosis and the fix's substance and separately found the
same gap: `_SKILL_VERDICT_PROSE` grew from 907 to 1460 bytes (+553,
+61%), a per-spawn `--append-system-prompt` cost that is itself larger
than the 439 bytes issue #2893 cites as the overhead problem it is
answering, and PR #2898 never stated that delta.

canonical: `git diff --stat` (this session's own commit, over the merge
of PR #2898) — result:
```
directive_assembly.py | 16 +++++-----------
1 file changed, 5 insertions(+), 11 deletions(-)
```

Old wording repeated the summary line's rationale in a full new
paragraph ("적용될 스킬이 없었다"는 그 판단 자체를..., plus the
"검토했지만 안 맞았다" vs "검토 자체를 안 했다" contrast) alongside the
already-existing optional-summary-line sentence, duplicating content the
directive already carried. Rewrite: keep the existing
optional-summary-line sentence exactly as core-team-written pre-#2893
(`... 선택적으로 요약 한 줄만 남겨도 된다: \`other mounted skills: not
triggered\`.`), then add one short sentence converting "optional" to
"required" specifically for the all-uninvoked case (`단,
전부-미호출(마운트된 스킬을 하나도 호출하지 않음)이면 이 요약 줄은
필수다(이슈 #2893).`) instead of restating the mechanism from scratch.
Same requirement, no new paragraph.

Measured at the real injection point — the full `--append-system-prompt`
block a `skills_mounted=True` spawn actually sends
(`directive_section_files(skills_mounted=True)` →
`_directive_system_prompt_block()`), comparing `origin/main` to this
branch in two separate Python processes (one per worktree, so no stale
import state):

```
derived:
  git worktree add /tmp/main-worktree origin/main
  python3 -c "... load both directive_assembly.py copies, call
  directive_section_files(skills_mounted=True) then
  _directive_system_prompt_block() on each, len(.encode('utf-8')) ..."
result:
  origin/main:    12753 bytes
  this branch:    12945 bytes
  delta:          +192 bytes
```

+192 bytes, not +553 — under half of PR #2898's growth, and under the
439 bytes issue #2893 itself names as the overhead this issue is meant
to reduce, not add to. The durable-trace guarantee (a session that
invokes zero of its mounted skills must state that judgment in its own
record, checked once at Stop via the unchanged `gates/record_lint.py`
regex and `on-the-record/hooks/skill-verdict-guard.sh` wiring from PR
#2898 — neither touched this round) is unchanged; only the prose stating
it shrank.

## Why

### The gap this round closes

Both #2900 and #2901 independently re-derived the same finding: the
issue's own "must not" line — "must not grow injected directive bytes
without stating the delta" — was violated on the "stating the delta"
half (PR #2898's PR body and record never computed or reported the
907→1460 change), and the delta itself, once computed, is larger than
the 439-byte number the issue names as the problem this fix answers.

canonical: `git diff main pr2898 -- directive_assembly.py` (this
session, re-read) — the +553 bytes are not new guarantees: the old
sentence already said "마운트만 되고 호출하지 않은 스킬은 이 줄이 필요
없다 — 선택적으로 요약 한 줄만 남겨도 된다: `other mounted skills: not
triggered`."; PR #2898's version keeps that sentence nearly verbatim and
then adds a full second paragraph restating the same summary-line
concept with its own worked rationale, rather than editing the existing
sentence from "optional" to "required" in place.

The leaner rewrite in "What was done" above keeps every requirement PR
#2898 added (all-uninvoked case now mandatory, not optional; same
`other mounted skills: not triggered` line; same "no skill is now
mandatory to invoke" guarantee) and drops only the restated mechanism,
not any requirement.

### Why not zero-growth

A zero-byte fix was considered and rejected: the pre-#2893 sentence
never stated that the all-uninvoked case is mandatory rather than
optional (it said "선택적으로" uniformly, for every not-invoked skill)
— some new text is required to carry that state change, or the
directive would keep telling sessions the summary line is optional in
exactly the case `gates/record_lint.py`'s `zero_invocation_summary_check`
(from PR #2898, unchanged this round) now enforces it. +192 bytes is
reported as this round's answer, not claimed as a proven floor — a
future session finding a smaller phrasing should still state its own
delta per this same "must not."

### Criterion 1 — not satisfiable as written, said plainly

Issue #2893's first acceptance line asks for "root cause named from the
two sessions' logs, not inferred" (issue #710, and issue #711's
2026-08-28 session). PR #2898's own record already checked for both and
reported them unreachable:

canonical: `docs/issue-2893/reports/diagnose-first-6a58e6a9.md`, "Root
cause, from the two sessions' own evidence" section (this session,
re-read in full) — `gh issue view 710`/`gh issue view 711` against this
repo resolve to unrelated issues (neither is this repo's #2893
incident), and no local `~/.tokenmaxxxer/work/` workspace for either
survived retention. That section's diagnosis is built from the issue's
own quoted evidence plus this repo's current code and prior art, not
from reading the incident transcripts directly, and says so.

#2901's independent verification credited that disclosure as the right
behavior but flagged that the record never said, in one direct sentence,
that criterion 1 could not be met as written. Saying it here plainly:
**criterion 1 is not satisfiable from this repo as written** — the two
incident sessions' transcripts do not exist in any location this session
(or PR #2898's) can reach, so "named from the logs" was replaced with a
diagnosis built from direct code reading (the nudge mechanism's own
gating condition) and a live `claude -p` reproduction (PR #2898's "Live
reproduction" section) — a different, weaker evidentiary standard than
the criterion asked for, disclosed rather than presented as equivalent.
If a future session gains access to the downstream target repo's session
logs for issues #710/#711, re-deriving the root cause from the actual
transcripts would let criterion 1 be met as originally written; nothing
in this repo makes that possible today.

### Standing invariants (all 4 re-run on this branch, post-merge)

1. **No return of the retired role axis**:
   `derived: python3 gates/retirement_count.py` — this branch 1135,
   `origin/main` 1135 (unchanged).
2. **No new bug**: `derived: python3 -m pytest . -q -o addopts=""` from
   the repo root — this branch 17 failed / 654 passed / 3 xfailed,
   `origin/main` 17 failed / 651 passed / 3 xfailed (the 3-test gap is
   PR #2898's own new `ZeroInvocationRecordSummaryTest` cases).
   `derived: diff <(sorted FAILED lines, this branch) <(sorted FAILED
   lines, origin/main)` — result: exit 0, empty diff — the two 17-line
   sorted `FAILED` name lists are byte-identical.
3. **No overhead increase — this round's deliverable**: +192 bytes at
   the real injection point (see "What was done" above), stated in full
   this time.
4. **Monitor/watch machinery unbroken, not quieter**:
   `derived: python3 -m pytest test/test_watchdog_heartbeat_noise.py test/test_ps_live_reliability.py -q -o addopts=""`
   — 10 passed, both this branch and `origin/main`.

### Live-spawn acceptance criterion — not re-run this round

Issue #2893's second acceptance line ("spawn one real session with a
mounted skill and count `Skill` tool calls, before and after") was
already executed live in PR #2898 (its "Live reproduction" section: 0
Skill calls in all 4 sessions, before and after, because that fix — and
this round's follow-on — touch record verification, not invocation
logic). This round's change is a same-requirement reword of already-
inert-to-invocation prose; re-running the same live spawn would measure
the same unaffected-by-design result PR #2898 already recorded, so it is
not repeated here (record-order guidance: assemble from executed
results, not re-derive what a prior commit already established and this
round did not touch).

This session's own mounted-skill list (`--skills silent-failure-audit`)
went uninvoked, which the fix delivered this round (and originally, in
PR #2898) requires this record to disclose — see the `skill-verdict`
line at the end of this record. It is, incidentally, a live first-party
instance of exactly the all-uninvoked case the fix covers.

## What did not work

None.

## Upstream basis

- `docs/issue-2893/reports/diagnose-first-6a58e6a9.md` (sha in
  frontmatter) — PR #2898's own record: root-cause derivation, live
  reproduction, and the pre-existing "optional" summary-line wording
  this round narrows further.
- `directive_assembly.py` (same-commit) — `_SKILL_VERDICT_PROSE`
  reworded this commit.
- `gates/record_lint.py` / `on-the-record/gates/record_lint.py` (sha in
  frontmatter, unchanged this round) — `zero_invocation_summary_check`,
  the mechanical enforcement the reworded prose describes.
- `on-the-record/hooks/skill-verdict-guard.sh` (sha in frontmatter,
  unchanged this round) — the Stop-hook wiring that calls the above.
- `docs/handbooks/skill-verdict-obligation.md` (sha in frontmatter,
  unchanged this round) — handbook description of the same mechanism.

## Open findings

Carried forward from PR #2898's record, neither touched this round:

- The two incident sessions' (#710, #711) own transcripts remain
  unread — see "Criterion 1" above; no resolution path exists from
  inside this repo today.
- `scripts/measure_skill_invocation.py`'s `inj_re` regex still matches
  retired cross-family phrasing that no longer appears in the live
  template (`spawn.py:4007-4010`), making its
  `injected_cross_family`/`orphaned_cross_family`/orphan-injection-rate
  fields dead for any session spawned since that wording changed. Out of
  this issue's scope; a measurement-script staleness bug, not the
  invocation gap itself.

## Next steps

None — `loop_state: landed`.

skill-verdict: work-in-english — applied: invoked; the SKILL.md content
was loaded via the Skill tool this session. Its policy was followed in
substance: this record, all code, commit and PR text are in English;
only the final user-facing chat summary (outside this record) is in
Korean, per the skill's policy for a Korean-communicating session.
other mounted skills: not triggered — `silent-failure-audit` (mounted
via `--skills`) was not invoked. This round's only code change is a
prose-constant reword in `directive_assembly.py` (no new error-handling
path, no API/file/DB/input-validation code touched); the merged-in code
from PR #2898 (the actual try/except and regex-check additions) was
authored and audited in that PR's own session, not this one. Opening the
skill here would have been invocation to satisfy the obligation rather
than because a genuine error-handling-review moment existed — exactly
what issue #2893's own "must not" (and this fix) treats as worse than a
correctly-skipped skill.
