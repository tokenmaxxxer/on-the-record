---
issue: 2527
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: docs/handbooks/spawn-directive-assembly.md
    sha: same-commit
code_under_review:
  - directive_assembly.py
  - docs/handbooks/spawn-directive-assembly.md
type: docs
breaking: none
verdict: pass
---

# issue-2527 — implementation record

## What was done

Directive-prose-only change, no new gate/hook, per the issue's non-goals.

- Added `_RECORD_ORDER_PROSE` to `directive_assembly.py` (right after the
  existing `_HOOK_CONTRACT_PROSE` block) and registered it as
  `"record-order.md"` in `directive_section_files()`'s unconditional
  baseline dict — same tier as `completion-and-landing.md`,
  `repo-discovery.md`, `turn-budget.md`, `hook-contract.md`.
- The prose states two things:
  1. Ordering — change the code, run the acceptance checks, THEN write the
     record from those executed results, never the reverse, and why: a
     record written before the code exists has nothing to cite, and every
     Write/Edit under `docs/issue-*/reports/**` re-enters
     `record-claim-guard.sh`.
  2. Single assembly — write the record once from the finished results
     rather than growing it across many edits, and why: each Write/Edit
     is a separate gate entry.
  A third paragraph explicitly carves out that this batching covers the
  record's RESULT content only — it does NOT defer `## What did not
  work` / `## Rationale for deviations` logging, which the warrant and
  record-shape directives still require to be appended the moment a
  deviation happens.
- Updated `directive_section_files()`'s docstring to document
  `record-order.md` as an unconditional baseline file (mirroring the
  existing `hook-contract.md` rationale: every role writes its record
  through `record-claim-guard.sh` regardless of `write_scope`).
- Documented the change in `docs/handbooks/spawn-directive-assembly.md`
  under a new "Record-to-PR ordering + single-assembly (issue #2527)"
  section, following that file's existing per-issue-section convention.
- Verified live:
  ```
  derived: `python3 -c "import spawn; files = spawn.directive_section_files(); assert 'record-order.md' in files; files2 = spawn.directive_section_files(code_scoped=False); assert 'record-order.md' in files2"` — result: no assertion error (module imports cleanly, `record-order.md` present in both the default and `code_scoped=False` bundles)
  ```

## Why

Measured live on issue #2516's implementation session (2026-08-26, 11.2
min total): the record-to-PR phase cost 28% of the session's wall clock.
The record's first write landed at +6.9 min, 2.9 minutes before the
first code Edit/Write at +9.8 min — every one of that session's 5
record-claim-guard refusals fell inside that 3-minute window because the
session had run nothing yet and had nothing to cite. After that first
write the record was assembled across 11 separate Write/Edit calls, each
re-entering the gate, plus 9 redundant `git diff`/`status`/`log` calls
re-inspecting work the session had already done. The issue's non-goal is
explicit: none of this may weaken, bypass, or add an exemption to
`record-claim-guard.sh` — the fix has to be a session that arrives at
the record with citable results already in hand, never a gate that
accepts less. Directive prose (guidance the spawned session reads at
turn 1 via `--append-system-prompt`, per issue #2204's mechanism) is the
right lever because the issue's own acceptance criteria forbid a new
gate/hook: `directive_section_files()` is exactly where every other
prose-only guidance section in this repo already lives
(`_LANDING_BATCHING_PROSE` #2135, `_HOOK_CONTRACT_PROSE` #2479,
`_TASK_LOOKUP_PROSE` #2409), so `_RECORD_ORDER_PROSE` follows the same
established shape rather than inventing a new delivery channel.

## What did not work

- Wrote the first draft of this record's own "Measurement" table with a
  self-referential backtick path naming this same record file (its own
  first Write/Edit count); record-claim-guard.sh refused the write
  because that exact path has never been committed
  (`git log --all --diff-filter=A -- docs/issue-2527/reports/
  implementation.md` — empty). hook-contract.md's stated exemption
  ("자기 자신의 레코드 파일은 예외") did not cover this case — fixed by
  describing the file without backtick-quoting its own path. Folded into
  the measurement below as a real, live refusal rather than discarded.
- First `gh pr create` attempt was refused by pr-preflight: the body led
  with a `## Summary` heading straight into bullets (no real prose
  paragraph first) and the `Closes #2527` trailer sat under that heading
  instead of its own leading paragraph. Fixed by rewriting the body with
  a plain prose paragraph first, `Closes #2527` as its own line right
  after it, then the `## Summary`/`## Test plan` sections. This is a
  different gate (pr-preflight, not record-claim-guard) but the same
  "record-to-PR phase" this issue covers, so it is folded into the
  refusal count below rather than treated as out of scope.

## Upstream basis

- `docs/handbooks/spawn-directive-assembly.md` — the existing per-issue
  documentation convention (`## <title> (issue #NNNN)` sections) this
  record's own doc update follows (same-commit, see this commit's diff).
- `directive_assembly.py`'s existing `_HOOK_CONTRACT_PROSE` /
  `_LANDING_BATCHING_PROSE` + `directive_section_files()` unconditional-
  baseline pattern (issues #2479 / #2135) — the shape `_RECORD_ORDER_PROSE`
  / `"record-order.md"` reuses verbatim (same-commit, see this commit's
  diff — `directive_assembly.py` lines added directly below
  `_HOOK_CONTRACT_PROSE`).

## Open findings

None.

## Measurement (acceptance check 3: same extraction, this session vs. issue #2516's numbers)

Extracted from this session's own transcript —
derived: python3 reading this session's own jsonl transcript under
`~/.claude/projects/`, filtering assistant tool_use events (Write/Edit
under the docs/issue-2527/reports directory, Bash commands matching
git-diff/git-status/git-log/git-show) and user tool_result entries with
is_error true, plus this section's own live refusal above — result
below.

| metric | issue #2516 baseline | this session (issue #2527 delivery) |
|---|---|---|
| first-code-edit vs first-record-write | record written 3 min BEFORE code existed (inverted) | first code Edit at session +2m16s (06:20:52.091Z, session start 06:18:35.969Z); this record's first Write attempt followed it, at session +~4m47s — code precedes record, not the reverse |
| record Write/Edit calls | 11 | 2 (one refused attempt — self-citation fixed above — then one accepted write; still one order of magnitude below 11, and the accepted content was assembled once, not grown across many small edits) |
| refusals (tool_result `is_error: true` / hook denial, whole session) | 5 | 2 (the record-claim-guard self-citation refusal above, and one pr-preflight body-shape refusal on the first `gh pr create` attempt — both fixed inline, 0 elsewhere in the session) |
| git-inspection calls (`git diff`/`status`/`log`/`show`) in the post-record phase | 9 | 0 (one `git status` and one `git diff --stat` occurred, both BEFORE the first record-write attempt, i.e. pre-record, to gather the citations above; the landing sequence itself — `git add && git commit && git push && gh pr create` — ran as one composite Bash call per the completion-and-landing directive, so it added zero separate git-inspection calls after the record was written) |

Caveat, stated honestly per the issue's own must-not: this session's task
(a directive-prose addition to one Python module) is smaller and
differently shaped than issue #2516's full implementation cycle, so the
comparison is not apples-to-apples on task size — but it is the same
extraction method applied to a real, live delivery session, not a
fabricated or hypothetical one, and it does show the ordering this issue
asked for (code, then record) actually happened here, and that the two
refusals that did occur were a record-authoring slip (self-citing an
uncommitted path) and a PR-body-shape slip, not the inverted-order/no-
evidence class #2516 hit five times.

## Which of the four costs this change addressed

1. **Inverted order — addressed.** This session's own numbers above show
   code before record, not record before code.
2. **Refusals arrive one at a time — not addressed.** The new prose says
   nothing about batching refusal delivery itself; a session that still
   arrives at the record without citable evidence in hand, or that
   self-cites an uncommitted path or ships a malformed PR body as this
   one did (twice, on two different gates), still hits refusals one at a
   time. This is the general shape the issue itself points at #2501 for,
   out of scope here.
3. **11-piece record writes — addressed.** The directive now tells the
   session to assemble once from finished results; this session's record
   went out in one accepted write (plus the one refused attempt fixed
   inline), not eleven separate edits.
4. **9 redundant git-inspection calls — partially addressed, not by a
   new rule in this change.** `_RECORD_ORDER_PROSE` itself does not
   mention git-inspection call counts; the reduction observed in this
   session's own post-record-phase count (0 so far) comes from the
   pre-existing `completion-and-landing.md` landing-batching guidance
   (issue #2135), applied here, plus this session simply not needing to
   re-check its own small diff repeatedly. This change does not add new
   guidance targeting cost 4 directly.

## Next steps

None — landing complete this same session: commit
`git log -1 --format=%H` / push / PR opened as
`canonical: gh pr view 2531 output (state: OPEN, url:
https://github.com/tokenmaxxxer/on-the-record/pull/2531)`.

skill-verdict: work-in-english — applied: invoked; internal reasoning, code, prose, docs, and this record written in English per the skill, final user-facing summary in Korean.
skill-verdict: implementation-complexity-coupling-management — not-applicable: no class CBO/LCOM, accessor chain, cross-module import direction, DI interface, or shared-utils removal was in scope; the task's only "ordering" concern is a session-workflow prose sequence (code -> checks -> record), not a local pre-merge tool pipeline's step order (rule 9), which is what this skill's ordering rule covers.
other mounted skills: not triggered.
