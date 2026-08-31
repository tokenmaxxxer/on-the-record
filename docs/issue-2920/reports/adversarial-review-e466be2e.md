---
issue: 2920
role: adversarial-review-e466be2e
author: adversarial-review-e466be2e
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
loop_state: landed
upstream:
  - path: PR #2927 (github.com/tokenmaxxxer/on-the-record/pull/2927)
    sha: 6199011258ef78b062457fcc3363e655a845f549
  - path: 6199011258ef78b062457fcc3363e655a845f549:docs/issue-2920/reports/refactoring-legacy-seam-selection+silent-failure-audit-b9f1e0f4.md
    sha: 6199011258ef78b062457fcc3363e655a845f549
---

# issue-2920 — adversarial-review-e466be2e record

skill-verdict: adversarial-review — applied: invoked; loaded via Skill tool before verifying (Skill tool call, this session). canonical: this session's own tool-call transcript (Skill invocation of `adversarial-review`). Used the skill's blind/independent-evaluator posture — every claim below was re-derived from primary sources (diff, two real worktrees, live execution against the actual skill-repository) before the PR's own record was read, per the task's explicit instruction.
skill-verdict: work-in-english — applied: invoked; loaded via Skill tool this session, followed for the language split (this record in English, final chat summary in Korean).
skill-verdict: silent-failure-audit — applied: invoked; loaded via Skill tool this session. Claim (b) is exactly a silent-failure-to-visible-failure change, so its H/S/U framing and "trace forward from catch to consequence" method were applied directly to that claim (see attack point THIRD below) and also surfaced Finding 2 (a legitimate case wrongly landing in the new "unresolved" signal instead of "handled").

## What was done

Independently verified PR #2927 (`resolve_skill_family_source()` →
`resolve_consult_skill_source()`, issue #2920) against primary sources
only: the diff, two real worktrees, and live Python execution against
the real, on-disk skill-repository checkout at `$MUSTER_SKILL_REPO`
(`/home/jwjung/skill-registry/skills`, `MUSTER_SKILL_REPO_SHA=c05de12`)
— not synthetic tmpdir fixtures, and not the PR's own record, which was
read only after every number below was independently reproduced.

canonical: this session's own shell transcript —
`git merge-base origin/main HEAD` (run inside a worktree at PR head
`6199011258ef78b062457fcc3363e655a845f549`) returned `85d9f61d2acd5fe0e795593caa676f0bf306f420`,
i.e. the PR's true merge-base, one commit behind `origin/main` tip
(`6db165ce...`, which added an unrelated test file after this PR
branched — see Test evidence).

Worktrees used this session (removed at the end of the session,
`git worktree remove --force` on all three):
- PR head — `git fetch origin pull/2927/head:pr-2927-head && git worktree add /tmp/pr2927-head pr-2927-head`, sha `6199011258ef78b062457fcc3363e655a845f549`
- `origin/main` tip — `git worktree add /tmp/main-base origin/main`, sha `6db165ce`
- PR's true merge-base — `git worktree add /tmp/pr2927-base 85d9f61d`, sha `85d9f61d2acd5fe0e795593caa676f0bf306f420`

## Why

The task named five attack points plus four standing invariants. Each
was checked by construction (running the actual resolution function, the
actual gate, and the actual test suite) rather than by reading the PR's
narrative, per adversarial-review's blind-evaluator method: an evaluator
that trusts the builder's own derivations is not independent.

### FIRST — central behaviour, live, real skill names

Before (merge-base `85d9f61d`, old `resolve_skill_family_source`):
derived: `python3 -c "import spawn; r=spawn._skill_repo_root(); [print(n, spawn.resolve_skill_family_source(n, r)['skills']) for n in ['adversarial-review','code-architecture','conformance-review','implementation','totally-bogus-xyz-123']]"`, executed in `/tmp/pr2927-base` with `MUSTER_SKILL_REPO=/home/jwjung/skill-registry/skills` — result:
```
adversarial-review    -> ['work-in-english']
code-architecture     -> ['work-in-english']
conformance-review    -> ['conformance-review-finding-record', 'conformance-review-requirement-extraction', 'conformance-review-sampling-derivation', 'conformance-review-severity-classification', 'conformance-review-traceability-and-evidence', 'conformance-review-verdict-assignment', 'conformance-review-verification-method-selection', 'work-in-english']
implementation        -> ['implementation-audit', 'implementation-blueprint', 'implementation-complexity-coupling-management', 'implementation-design-pattern-selection', 'implementation-performance-data-structure-choice', 'work-in-english']
totally-bogus-xyz-123 -> ['work-in-english']
```
(conformance-review = 8 entries counted directly in this pasted list;
implementation = 6 entries counted directly in this pasted list —
matching the task prompt's "mounted 8 and 6 skills before".)

After (PR head `6199011258ef78b062457fcc3363e655a845f549`, `resolve_consult_skill_source`):
derived: the same command against the same real skill-repository, executed in `/tmp/pr2927-head` — result:
```
adversarial-review    -> ['adversarial-review', 'work-in-english']       unresolved: []
code-architecture     -> ['code-architecture', 'work-in-english']        unresolved: []
conformance-review    -> ['work-in-english']                             unresolved: ['conformance-review']
implementation        -> ['work-in-english']                             unresolved: ['implementation']
totally-bogus-xyz-123 -> ['work-in-english']                             unresolved: ['totally-bogus-xyz-123']
```

This confirms, by direct execution against the real skill-repository:
(i) a real leaf name now mounts itself + POLICY where it mounted only
`work-in-english` before; (ii) a retired role name mounts only POLICY
and is surfaced in `unresolved`, where it used to silently absorb an
entire family; (iii) a nonexistent selector behaves identically to a
retired role name (POLICY-only + `unresolved`) in the pasted output
above — all three distinguishable by the `unresolved` key.

`--skills` parity, derived, executed in `/tmp/pr2927-head`:
```
>>> skills_r = spawn.resolve_skill_source("adversarial-review", repo_root)
>>> consult_r = spawn.resolve_consult_skill_source("adversarial-review", repo_root)
>>> set(skills_r["skill_dirs"]) == set(consult_r["skill_dirs"]) - {repo_root/"work-in-english"}
True
```

Multi-skill CSV, derived, executed in `/tmp/pr2927-head`:
```
>>> spawn.resolve_consult_skill_source("adversarial-review,code-architecture", repo_root)["skills"]
['adversarial-review', 'code-architecture', 'work-in-english']
>>> spawn.resolve_consult_skill_source("adversarial-review,conformance-review", repo_root)["unresolved"]
['conformance-review']
```

`panel_cmd()` is the PR's cited second multi-skill form: canonical,
`6199011258ef78b062457fcc3363e655a845f549:consult.py:1673-1699` —
`_run_panel_session()` calls `_composed_consult_skill_source()`, the
same function `consult_cmd()`/`_verb_cmd()` use; no separate code path
(confirmed by reading that file range in the PR-head worktree).

### SECOND — claim (d)'s docstring-citation defence: NOT CONFIRMED

canonical: `python3 gates/retirement_count.py` — the same script
byte-identical between the two trees, confirmed via
`git diff origin/main...HEAD -- gates/retirement_count.py` (empty
output) — executed live in three worktrees:
```
/tmp/main-base   (origin/main tip, 6db165ce):                  1135 occurrence(s)
/tmp/pr2927-base (true merge-base, 85d9f61d2acd5fe...):         1135 occurrence(s)
/tmp/pr2927-head (PR head, 6199011258ef78b0...):                1101 occurrence(s)
```
derived: `python3 gates/retirement_count.py 2>&1 | grep "occurrence(s)"`,
run three times in `/tmp/pr2927-head` for stability — identical (1101)
every time. PR #2927 (and its own record) claims 1135 → **1098**; live
re-execution of the gate against the PR's own head gives **1101** — a
mismatch of 3.

Added-line role-token count, reproduced with the gate's own
`rc.line_hits()` function (imported directly from
`gates/retirement_count.py`, not reimplemented), applied to every `+`
line of `git diff origin/main...HEAD -- consult.py skills.py spawn.py
'test/*.py'`:
```
derived: [l for l in added_lines if rc.line_hits(l)] — result: 17 lines match, not 14.
```
16 of the 17 are docstring/comment prose. The 17th is not — it is a
Python function definition added by this PR:
```python
+    def test_retired_role_name_no_longer_pulls_in_family_members(self):
```
canonical: `6199011258ef78b062457fcc3363e655a845f549:test/test_consult_skill_resolution_2920.py:129`
— a live code identifier (function name) containing "role", not a
citation in prose or a comment. Claim (d) states "all docstring
citations, zero code identifiers"; this line is neither a docstring nor
a comment. The 3-occurrence gap (1098 claimed vs 1101 measured) and the
3-line gap (14 claimed vs 17 measured) point at the same undercount.

**Verdict on claim (d): the count is wrong (measured, reproduced three
times), and the "zero code identifiers" sub-claim is false (one
function-name identifier found).** This does not mean the retired role
*axis* (a name→skill-cluster table) survives — the standing-invariant
check below confirms no reshaped table exists in the resolution path —
but the PR's own acceptance-criterion-#2 arithmetic does not reproduce
under direct re-execution of its own cited gate and should not be taken
at face value without re-running it.

### THIRD — claim (b): silent → visible, three channels, fail-open not fail-closed

Applying silent-failure-audit's classification: this site used to be
Silently Absorbed (unmatched selector → POLICY-only mount, no signal)
and the claim is that it is now Handled (surfaced, and the operation
still completes rather than failing closed). Traced forward on all
three channels, live, against the real skill-repository, executed in
`/tmp/pr2927-head`:

1. Env var — derived:
```
>>> cmd, env, sp = spawn._consult_cmd_and_env("conformance-review", None, None, task_text="", issue=None)
>>> env["MUSTER_SKILLS"], env["MUSTER_SKILLS_UNRESOLVED"]
('work-in-english', 'conformance-review')
```
2. Verdict fields — derived: ran `consult.consult_cmd("conformance-review",
   "a question", cwd=tmpdir)` end-to-end with `subprocess.run` mocked to
   return a valid session JSON and `_cross_family_skill_matches_with_consult`
   stubbed to isolate the resolution path — result:
```
verdict["skills_mounted"]    == ['work-in-english']
verdict["skills_unresolved"] == ['conformance-review']
verdict["answer"]            == 'some answer'
```
   The call returns a usable answer; it does not raise or `sys.exit`.
   This is the live behavior that satisfies #2569's settled decision
   (free-form consult argument, must not reject an unmatched selector).
3. Durable trace — derived: the same run wrote, to the trace file read
   back after the call:
```
- 2026-08-31T04:51:40.093872+00:00 | skill=conformance-review | verb=consult | issue=none | question='a question' | outcome='ok: some answer | evidence=[verified:0 failed:0 unverified-cmd:0 no-evidence:1]' | mounted='work-in-english' | unresolved='conformance-review'
```
   Byte-identical no-op, derived: `consult._append_consult_trace(p, ts,
   "some-skill", None, "q", "ok: a")` (no `mounted=`/`unresolved=`
   kwargs) produces the exact same `repr()` of the written line on both
   the PR-head tree and the merge-base tree:
```
"- 2026-01-01T00:00:00+00:00 | skill=some-skill | verb=consult | issue=none | question='q' | outcome='ok: a'\n"
```
   (identical string, both trees — no regression for callers that don't
   pass the new kwargs).

canonical: the three code blocks immediately above are this session's
own executed output (Python REPL-style transcripts run against the PR
head worktree). All three channels reproduce; claim (b) holds.

### FOURTH — retirement did not overreach... except one case: FINDING

POLICY baseline / `work-in-english` mounting was checked broadly: every
resolution call in FIRST above always carries `work-in-english` in
`skills`, confirmed by direct inspection of the pasted output there
(canonical: same transcripts). That part holds. But the specific
sub-requirement — "a consult that legitimately needs only
`work-in-english` must still work without being treated as an error" —
does not fully hold:

derived: `spawn.resolve_consult_skill_source("work-in-english", repo_root)`,
executed in `/tmp/pr2927-head` against the real skill-repository —
result:
```
{'skills': ['work-in-english'], 'unresolved': ['work-in-english'], ...}
```
The mount is correct (`work-in-english` is present in `skills`), but the
selector is also reported in `unresolved` — the exact false-positive
shape this PR's own visibility mechanism is meant to avoid.

Root cause, canonical:
`6199011258ef78b062457fcc3363e655a845f549:skills.py:504-512`:
```python
names = [n.strip() for n in skill.split(",") if n.strip()]
if repo_root is not None and repo_root.is_dir():
    matched = [n for n in names
               if n not in _STATIC_POLICY_SKILLS
               and not n.startswith(".")
               and (repo_root / n).is_dir()]
else:
    matched = []
unresolved = [n for n in names if n not in matched]
```
`_STATIC_POLICY_SKILLS` is excluded from `matched` (reasonable on its
own — it is added unconditionally via `baseline`, so counting it in
`matched` too would double it inside `merge_composed_skill_source()`),
but nothing then excludes a POLICY-named token from `unresolved` when it
was explicitly requested and did resolve via the baseline.

Reproduced identically at the env-var layer, derived, executed in
`/tmp/pr2927-head`:
```
>>> cmd, env, sp = spawn._consult_cmd_and_env("work-in-english", None, None, task_text="", issue=None)
>>> env["MUSTER_SKILLS"], env["MUSTER_SKILLS_UNRESOLVED"]
('work-in-english', 'work-in-english')
```
and with a multi-name selector in both orders, derived, executed in
`/tmp/pr2927-head`:
```
>>> spawn.resolve_consult_skill_source("work-in-english,adversarial-review", repo_root)["unresolved"]
['work-in-english']
>>> spawn.resolve_consult_skill_source("adversarial-review,work-in-english", repo_root)["unresolved"]
['work-in-english']
```
`_STATIC_POLICY_SKILLS` is exactly `{'work-in-english'}` today
(canonical: `6199011258ef78b062457fcc3363e655a845f549:skills.py:440`),
so this is not hypothetical: it fires for the literal, current POLICY
skill name whenever a caller names it explicitly as (part of) the
consult selector. It would also corrupt the corpus measurement issue
#2920's own acceptance check #3 asks for going forward ("how many
consults mounted only `work-in-english`"), by making a legitimate,
fully-successful `work-in-english`-only consult indistinguishable — in
the new `unresolved` channel — from a genuinely failed/typo'd one. This
is a reproducible defect, not a framing disagreement: the mount works,
but the visibility signal this PR adds misclassifies this one input
shape as a failure.

### FIFTH — claim (c): cross-family match untouched — CONFIRMED

`_readonly_plugin_dirs()` rewire, derived, executed in `/tmp/pr2927-head`
against the real skill-repository:
```
>>> [d.name for d in consult._readonly_plugin_dirs("conformance-review") if d.name == "work-in-english" or "conformance" in d.name]
['work-in-english']
>>> [d.name for d in consult._readonly_plugin_dirs("conformance-review-verdict-assignment") if d.name == "work-in-english" or "conformance" in d.name]
['work-in-english', 'conformance-review-verdict-assignment']
```
canonical: `merge_composed_skill_source()` (skills.py) and
`_cross_family_skill_matches_with_consult()` (consult.py, BM25+
skill_judge, #2507/#2561) show zero `+`/`-` lines inside either function
body in `git diff origin/main...HEAD` — only surrounding docstring/
call-site text was touched; verified by reading both functions'
definitions end-to-end in the PR-head worktree
(`6199011258ef78b062457fcc3363e655a845f549:skills.py:528-540`,
`6199011258ef78b062457fcc3363e655a845f549:consult.py:618-`, unchanged
bodies against `origin/main`'s copies at the same names).

### Standing invariants

1. No reshaped role axis survives, checked by construction:
   derived: `grep -nE "def [a-zA-Z_]+\(.*\brole\b" consult.py skills.py
   spawn.py` — empty; `grep -nE "^\s*\"role\"|\['role'\]"
   consult.py skills.py` — empty (both run in `/tmp/pr2927-head`). The
   only remaining `role`-named live identifier near this path is
   `a.role` — canonical: spawn.py's CLI-dispatch attribute
   (`a.role == "consult"`/`"judge"`/…, selecting which spawn.py
   subcommand runs), not a selector→skill-cluster table, untouched by
   this PR, out of this issue's scope. No dict, naming convention, or
   parameter carrying a role→skill-family mapping was found in
   `resolve_consult_skill_source()`, `_composed_consult_skill_source()`,
   `_consult_cmd_and_env()`, or `_readonly_plugin_dirs()` (all four read
   top-to-bottom, live, this session).
2. No new functional bugs found beyond Finding 2 below — derived:
   `python3 -m pytest test/test_consult_skill_resolution_2920.py -q`,
   executed in `/tmp/pr2927-head` — result: `13 passed in 0.84s`.
3. No behavior regression for byte-identical callers: confirmed above
   (THIRD, byte-identical no-op trace line); `resolved_skill_dirs()` /
   `resolve_skill_source()` (the `--skills` path) show zero `+`/`-`
   lines in `git diff origin/main...HEAD -- skills.py` inside either
   function body.
4. Historical docs untouched: derived: `git diff origin/main...HEAD
   --name-status -- docs/`, executed in `/tmp/pr2927-head` — result:
```
A	docs/issue-2920/reports/refactoring-legacy-seam-selection+silent-failure-audit-b9f1e0f4.md
A	docs/issue-2920/reports/refactoring-legacy-seam-selection+silent-failure-audit-b9f1e0f4/2026-08-31-hunt-resolve-consult-skill-source.md
```
   both `A` (added), no `M`/`D`/`R` against any existing `docs/issue-*`
   path.

### Test evidence

derived: `python3 -m pytest test/test_consult_skill_resolution_2920.py -q`, executed in `/tmp/pr2927-head` — result:
```
13 passed in 0.84s
```
derived: `python3 -m pytest test/ -q`, executed in `/tmp/pr2927-head` (PR head) — result:
```
15 failed, 521 passed, 3 xfailed in 31.65s
```
derived: `python3 -m pytest test/ -q`, executed in `/tmp/pr2927-base` (true merge-base `85d9f61d2acd5fe...`) — result:
```
15 failed, 508 passed, 3 xfailed in 31.64s
```
derived: `diff <(...--collect-only on merge-base...) <(...--collect-only on PR head...)` — the 15 failing test names in both `FAILED` summaries above are the identical set (compared line-by-line, not just counted). The pass-count delta of `521 - 508` equals `13`, exactly the new file's test count from the block above — confirmed via `pytest --collect-only -q` set-diff (`comm -13`/`comm -23`) between `origin/main` tip and the PR head: the only other collection differences are two tests renamed 1:1 in
`6199011258ef78b062457fcc3363e655a845f549:test/test_consult_no_rulebook_identity_regression.py`
(`test_mapped_skill_reaches_resolve_skill_family_source` →
`test_mapped_skill_reaches_resolve_consult_skill_source` and its
`unmapped_skill` sibling) and this exact set of five tests present on
`origin/main`'s tip but absent from *both* the PR head and the true
merge-base:
```
test/test_spawn_attempt_halt_report_cadence.py::EmptyStateTest::test_absent_file_emits_nothing_and_is_not_created
test/test_spawn_attempt_halt_report_cadence.py::EmptyStateTest::test_empty_file_emits_nothing_and_stays_untouched
test/test_spawn_attempt_halt_report_cadence.py::FirstReportUnchangedTest::test_single_tick_line_is_byte_identical_to_pre_change_format
test/test_spawn_attempt_halt_report_cadence.py::UnresolvedHaltReportCadenceTest::test_before_vs_after_derivation_no_longer_shows_the_9673_distribution
test/test_spawn_attempt_halt_report_cadence.py::UnresolvedHaltReportCadenceTest::test_bounded_across_full_retention_window
```
canonical: this file was added by `6db165ce` (`git log --oneline
--follow -- test/test_spawn_attempt_halt_report_cadence.py`), a commit
one ahead of this PR's merge-base — not a PR-caused deletion.

## What did not work

None.

## Open findings

1. **[CONFIRMED, moderate-major] `gates/retirement_count.py` numbers in
   PR #2927 / its record do not reproduce.** SECOND above: live
   execution of the PR's own cited gate on the PR's own head gives
   1135 → 1101, not the claimed 1135 → 1098; the gate's own
   `line_hits()` applied to this commit's added lines finds 17 matches,
   not the claimed 14, one of which
   (`6199011258ef78b062457fcc3363e655a845f549:test/test_consult_skill_resolution_2920.py:129`,
   `test_retired_role_name_no_longer_pulls_in_family_members`) is a
   genuine Python function-name identifier, contradicting the "zero code
   identifiers" sub-claim. Resolution path: re-run
   `gates/retirement_count.py` and the added-line `line_hits()` scan and
   correct the acceptance-#2 numbers in the PR body/record, and either
   justify the one function-name identifier explicitly (arguably a
   citation-by-test-name, parallel to the gate's own self-exemption
   reasoning — but that argument was not made) or rename it.
2. **[CONFIRMED, defect] `resolve_consult_skill_source()` reports a
   POLICY skill name as `unresolved` even when explicitly requested and
   successfully mounted.** FOURTH above: reproduced for
   `"work-in-english"` alone and combined with a real leaf name, at the
   function-return-value layer and the env-var layer
   (`MUSTER_SKILLS_UNRESOLVED`). Contradicts this review's fourth attack
   point ("a consult that legitimately needs only `work-in-english`
   must still work without being treated as an error") and would
   corrupt future corpus counts of "mounted only `work-in-english`"
   (issue #2920 acceptance check #3). Resolution path:
   `6199011258ef78b062457fcc3363e655a845f549:skills.py:512` —
   `unresolved = [n for n in names if n not in matched]` should also
   exclude `_STATIC_POLICY_SKILLS` members
   (`unresolved = [n for n in names if n not in matched and n not in _STATIC_POLICY_SKILLS]`).

## Next steps

None from this session — this record evaluates PR #2927; it does not
fix it. Findings 1-2 above should be routed back to the PR (or a
follow-up issue) for correction before the retirement-count and
visibility claims are relied on elsewhere.
