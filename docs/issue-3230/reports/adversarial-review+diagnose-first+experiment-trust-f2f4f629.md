---
issue: 3230
role: adversarial-review+diagnose-first+experiment-trust-f2f4f629
author: adversarial-review+diagnose-first+experiment-trust-f2f4f629
skills: adversarial-review (skill-repository(c05de12)), diagnose-first (skill-repository(c05de12)), experiment-trust (skill-repository(c05de12))
verifies_subject: true  # independent adversarial re-derivation of PR #3234's own three diagnostic findings
loop_state: done
type: verification
breaking: false
verdict: 2 of 3 named findings hold up under independent re-derivation (BM25, cache), 1 is Incorrect (async — a wired PostToolUse delivery mechanism this repo already ships was not checked), a fifth option the issue implies (scope the judge to the issue, not the dispatch) is never considered though the record's own cache evidence already argues against it, and the record draws no conclusion from its own 36-43% self-disagreement number about whether the judge's output is worth 16.7s at all. Shipped tooling (measure_skill_judge.py, 13 tests, truncation fix) is Present and independently reproduced correct.
upstream:
  - path: PR #3234 (branch issue-3230/diagnose-first+implementation-blueprint+experiment-trust-a01a3586)
    sha: c2151465252020fc4f18d150339469f77af93fb9
  - path: PR #3234's own diagnosis record (docs/issue-3230/reports/, untracked path in this session's working tree — belongs to that PR's branch, not this record's write-set)
    sha: c2151465252020fc4f18d150339469f77af93fb9
---

# issue-3230 — adversarial-review+diagnose-first+experiment-trust-f2f4f629 record

## What was done

Independently re-derived, in this session (structurally separate from PR
#3234's own authoring session, per adversarial-review — no shared
context, no access to that session's intent beyond what the PR and its
own record state), the three diagnostic findings PR #3234 uses to
justify shipping no dispatch-path change for issue #3230: the cache
repeat/disagreement numbers, the judge-vs-BM25 live comparison, and the
`spawn.py` async-delivery claim. Also independently ran the PR's
acceptance checks and full test suite from a fresh git worktree of the
PR branch, and read the two shipped production files
(`scripts/issue-3230/measure_skill_judge.py`,
`tests/test_issue_3230_skill_judge_cost.py`, materialized untracked into
this session's own working tree from
`origin/issue-3230/diagnose-first+implementation-blueprint+experiment-trust-a01a3586`
for citation — not committed here, they are PR #3234's own deliverable)
and the `consult.py` diff in full.

acceptance: `git worktree add /tmp/pr3234-verify c2151465252020fc4f18d150339469f77af93fb9`
then, inside that worktree, `python3 -m pytest tests/test_issue_3230_skill_judge_cost.py -q`
— result:
```
13 passed in 0.87s
```
acceptance: `python3 scripts/issue-3230/measure_skill_judge.py --report`
(same worktree) — result:
```
issue-3230 skill_judge dispatch-wait -- measured report
ledger files scanned: 41
raw skill_judge_perf events found: 1209
real (plausible) events after filter (duration_ms present AND wall_s >= 1.0s): 31
  filtered out as test-fixture noise (monkeypatched subprocess.run in this repo's own unit tests): 1178

-- skill_judge subprocess wall-clock time, per real dispatch --
  n=31 min=8.295s max=56.653s mean=21.796s median=20.700s p90=31.131s
  outcome_ok=True: 31/31
```
exit code 0. n grew from the PR's own n=21 to this session's n=31 (more
real spawns happened between the PR session and this one on the same
shared, live ledger corpus — expected drift, not a defect); median moved
from 16.343s to 20.700s but stays the same order of magnitude as both
the PR's own number and issue-3186/PR #3200's historical 16.663s
baseline.

acceptance (must-not, verbatim from the issue): `python3 scripts/issue-3186/measure_cross_family.py --report`
(same worktree) — result:
```
issue-3186 cross_family diagnosis -- measured report
log files scanned: 152
bootstrap_timing lines found: 18
```
exit code 0 — still runs, still finds data. derived: this session ran
`git status --short` inside the same worktree immediately before this
command — clean except for the untracked test-scratch dirs this session
created — confirming this session never touched `pipeline.py`,
`directive_assembly.py`, or `scripts/issue-3186/`.

acceptance: `python3 -m pytest -q` (same worktree, full suite) — result:
```
4 failed, 1433 passed, 3 xfailed, 2 warnings in 46.18s
```
matches the PR's own claimed counts exactly (4 failed / 1433 passed / 3
xfailed).

derived: to check the PR's own "pre-existing, unrelated" claim
independently rather than by re-running the PR's own stash-and-restore
trick on the PR's own branch, this session ran the same 3 failing test
files against a **separate, clean checkout** — this session's own branch
tip (`origin/main`, no PR #3234 changes present at all):
`python3 -m pytest -q on-the-record/hooks/test_hook_classification.py harness/fixture-operator-experience/test_flow.py on-the-record/checks/test_macos_bash32_compat.py`
— result:
```
FAILED on-the-record/hooks/test_hook_classification.py::HookClassificationTest::test_registration_count_matches_the_issues_own_count
FAILED on-the-record/hooks/test_hook_classification.py::HookClassificationTest::test_every_hooks_json_registration_has_a_classification_entry
FAILED harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace
FAILED on-the-record/checks/test_macos_bash32_compat.py::MacosBash32CompatTest::test_current_head_is_clean
4 failed, 10 passed in 0.88s
```
Same 4 test IDs, same assertion messages (including the
`on-the-record/hooks/amendment_channel.py` `/proc`-dependency line
quoted verbatim in both runs). This independently confirms the PR's
"pre-existing, unrelated" claim via a structurally different check than
the PR's own.

## Why

R007/issue-3230 explicitly asked for the "skill selection didn't get
worse" half of any change to be demonstrated, and said a well-argued
refusal to change is an acceptable outcome — but a refusal is exactly the
outcome that leaves the 16.7s wait in place, so the issue's own framing
(and this task) calls for harder scrutiny of a refusal than of a change.
adversarial-review supplies the structural independence (this session
has no stake in PR #3234's conclusions); diagnose-first's G2 "verify"
axis (evidence over opinion, check the causal claim against the four
causal axes) is what the re-derivation below applies to each of the
record's three sub-questions; experiment-trust's Step 1 scope gate was
checked against the judge-vs-BM25 comparison specifically (see "Skill
verdicts" below) since that comparison is the one thing in the PR that
looks like a variant contrast.

### Item 1 — the cache finding (25% repeat, 43% disagree)

Grade: **Present, with an unremarked methodology gap in how the PR
derived it.**

Re-ran the PR's own methodology (glob over
`~/.tokenmaxxxer/work/*/docs/issue-*/reports/consult-log{,/*.md}`,
regex `skill=(\S+) \| verb=skill_judge \| issue=(\S+) \| question='(.*?)' \| outcome=`)
verbatim in this session:
```
$ python3 /tmp/verify_repeats.py
total trace lines: 180 | fixture-filtered out: 126 | real remaining: 54
repeat share of REAL dispatches: 0.222 (12/54)
```
derived: `python3 /tmp/verify_repeats.py`, executed live this session,
same glob/regex/fixture-filter the PR's own evidence appendix documents
— close to, not identical to, the PR's own 56/25% (expected drift on a
live, growing corpus; the PR's own record already flags its numbers as
session-to-session-variable).

But the PR's regex requires the literal field name `skill=` immediately
before `verb=skill_judge`. Checking that requirement against the actual
corpus:
```
$ grep -rh "skill=.* | verb=skill_judge" ~/.tokenmaxxxer/work/*/docs/issue-*/reports/consult-log/ 2>/dev/null | wc -l
114
$ grep -rh "role=.* | verb=skill_judge" ~/.tokenmaxxxer/work/*/docs/issue-*/reports/consult-log/ 2>/dev/null | wc -l
9400
```
derived: both `grep` commands executed live this session against the
same directory the PR's own script scans (114 vs 9400 = the `role=`
field name accounts for 98.8% of matching lines in this one glob
component alone). canonical: `git log --all --oneline -S'line = (f"- {ts} | skill={skill} | verb={verb} "' -- consult.py`
(this session) shows the field rename `role=` → `skill=` landed at
commit `190321de059bf8b12de9cb2f943e8f8233f51ad2` ("issue-2139: relic
sweep batch — retired role-axis wording fixes..."). The PR's scan
silently excludes essentially all pre-rename trace lines — not flagged
anywhere in the PR's own record or evidence appendix.

Separately, the same glob also massively over-counts: consult-log files
are git-committed (not gitignored), so any workspace whose checkout
includes a commit that touched one of them gets an identical byte-for-
byte copy, and a naive glob counts every copy as a separate observation.
```
$ python3 /tmp/verify_repeats3.py
total glob-matched paths: 10893
unique-by-content files: 205 | duplicate files skipped: 10688
```
derived: `python3 /tmp/verify_repeats3.py`, executed live this session,
sha256-deduplicating file contents before scanning — 98.1% of the
glob-matched paths (10688/10893 = 0.981) are exact-duplicate copies of
one of only 205 distinct files. canonical: `git ls-files -- docs/issue-305/reports/consult-log/`
run in an arbitrary workspace checkout this session, lists a consult-log
file as git-tracked, confirming the duplication mechanism (shared
commits across workspace clones, not gitignored runtime-only state).

Re-deriving the PR's numbers correctly — content-hash-deduplicated, both
field-name eras included, using an `ast.literal_eval`-based parser (the
PR's own quote-matching regex silently returns no match on any outcome
field containing an internal apostrophe, e.g. "isn't" inside a
`rejected=[...]` reason — verified directly this session: the naive
regex parsed 0/8 = 0% of sampled multi-occurrence keys' `outcome=`
fields, `derived: python3 /tmp/debug_pick.py`, executed live this
session):
```
$ python3 /tmp/robust_parse.py
total skill_judge lines: 315 | parsed ok: 315 | fixture-filtered: 24 | real remaining: 291
real keys repeated >1x: 36 | repeat events: 93
repeat share of real dispatches: 0.3196 (93/291)
repeat-pair comparisons (both ok:): agree=52 disagree=29
disagree share: 0.358 (29/81)
repeated keys with at least one non-ok(parse-error) outcome among the repeats: 7
```
derived: `python3 /tmp/robust_parse.py`, executed live this session —
full script content in "Evidence appendix".

**The qualitative finding replicates on a corrected, ~5x-larger real
sample** (n=291 vs. the PR's n=56, derived above): repeat share 32% (vs.
the PR's 25%), disagreement-among-repeats 36% (vs. the PR's 43%), plus 7
repeated keys where at least one repeat came back as a parse error
(matching the PR's own claim of "sometimes a parse failure"). The core
substantive conclusion — a large-enough share of dispatches repeat, and
a large-enough share of *those* repeats disagree on byte-identical
input, that a naive cache is unsafe — holds up independently, derived
above. The gap is in the PR's own methodology write-up: canonical: the
PR's own record's Question 1 section and evidence appendix (read in full
this session, quoted in the task context provided to this session)
contain no mention of either the corpus-duplication issue or the
field-name-rename undercount, despite both being discoverable with tools
the PR's own script already demonstrates using (`git log -S`, a content
hash would have been a one-line addition to its own dedup-free glob).
This does not overturn the finding; it means the specific 56/25%/43%
numbers reported as *the* measurement were a narrower, unexamined slice
of a real signal that turns out to point the same direction.

**The inference the record does not draw.** The issue asked for the
16.7s wait to be cut without making selection worse; canonical: the PR's
own record (read in full this session) treats "the judge disagrees with
itself 36-43% of the time on identical input" as a fact about caching
safety only — its "Putting the three answers together" section and its
"Open findings" section contain no framing of the disagreement rate as a
question about the judge's own reliability, only as a caching-safety
constraint (searched directly in this session's copy of the PR's record
text for "worth", "reliab", "trust", "value" near the disagreement
numbers — none found). It is also a fact about the judge's own value: a
decision procedure that flips a genuine share of the time on the exact
same question is, by that same measurement, not a stable oracle — every
dispatch pays the full 16.7s median for an answer that a nontrivial
fraction of the time would have come out differently had it been asked
again seconds later. The record never asks whether paying 16.7s per
dispatch for an answer with that much self-variance is defensible at
all, independent of whether it's cached. Grade for this specific
inferential step: **Surface** — the underlying data is present and
correctly reported, but the record stops one question short of where
its own numbers point.

### Item 2 — the BM25 finding (0/5 agreement)

Grade: **Present, confirmed — holds up on a larger, independently-run
live sample, not a small-sample artifact.**

Re-ran the PR's own live comparison methodology (same functions,
`consult._sp._bm25_cross_family_scores()` and
`consult._cross_family_skill_matches_with_consult()`, real subprocess
calls, an isolated scratch cwd) against 10 fresh, real issue titles this
session selected independently — none overlapping the PR's own 5
(#3231/#3228/#3128/#3103/#3047) or the self-referential #3230/#3186:
```
$ python3 /tmp/live_agreement_verify.py
{"issue": 3229, "bm25_top2": ["refactoring-legacy-seam-selection", "secure-coding-dependency-supply-chain-security"], "judge_picked": ["refactoring-legacy-seam-selection"]}
{"issue": 3183, "bm25_top2": ["legal-compliance-license-compatibility", "refactoring-legacy-strangler-fig-migration"], "judge_picked": []}
{"issue": 3134, "bm25_top2": ["defect-verification-reproduction-evidence-quality", "technical-feasibility-verdict-and-timebox-selection"], "judge_picked": []}
{"issue": 3125, "bm25_top2": ["data-engineering-failure-handling", "conformance-review-traceability-and-evidence"], "judge_picked": []}
{"issue": 3120, "bm25_top2": ["incident-response-tool-landscape", "silent-failure-audit"], "judge_picked": []}
{"issue": 3118, "bm25_top2": ["adversarial-review", "game-growth-system-design"], "judge_picked": []}
{"issue": 3095, "bm25_top2": ["parallel-decomposition", "ml-engineering-ml-test-score-scoring"], "judge_picked": []}
{"issue": 3091, "bm25_top2": ["technical-feasibility-license-scan", "conformance-review-finding-record"], "judge_picked": []}
{"issue": 3083, "bm25_top2": ["merge-gates", "test-depth-audit"], "judge_picked": ["merge-gates"]}
{"issue": 3182, "bm25_top2": ["observability-signal-red", "capacity-planning-headroom-band-and-degradation-risk"], "judge_picked": []}
n= 10
agree (non-trivial, both non-empty and equal): 0
agree (incl. both-empty as agreement): 0 / 10
```
derived: `python3 /tmp/live_agreement_verify.py`, executed live this
session, 10 real subprocess `skill_judge` calls plus 10 real BM25
scoring calls (full driver script in "Evidence appendix"), wall-clock
17.6s-57.8s per call — same order of magnitude as the PR's own and
issue-3186's numbers.

0/10 = 0% exact-set agreement (derived: same command output quoted
immediately above, `/tmp/live_agreement_verify.py`), same strict
definition the PR used (a judge pick that is a strict subset of BM25's
top-2, as in issues 3229 and 3083 above, does not count as agreement,
matching the PR's own treatment of issue #3228's single-element pick).
The judge picked nothing in 8/10 = 80% of cases (derived from the
10-row table above), matching the PR's own 4/5 = 80% almost exactly.
Combined across both independently-run samples: 0/5 + 0/10 = 0/15 = 0%
exact agreement, summing the two counts derived above. This is not a
small-sample artifact — a second, independently-selected, 2x-larger live
sample reproduces both the headline number and the underlying "judge
correctly recognizes when nothing fits, BM25 fail-open cannot" pattern.
The refusal to replace the judge with BM25 is sound.

### Item 3 — the async finding ("this codebase has none today")

Grade: **Incorrect.** This is the one finding that does not survive
independent re-derivation.

Confirmed the record's `spawn.py` citations are accurate — canonical:
`spawn.py:4002-4010, 4387-4388, 4402-4418`, read directly in this
session:
```python
# spawn.py:4002-4010
_cross_family_executor: concurrent.futures.ThreadPoolExecutor | None = None
_cross_family_future = None
    if issue is not None:
        _cross_family_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        _cross_family_future = _cross_family_executor.submit(
            _cross_family_skill_matches_with_consult,
```
```python
# spawn.py:4387-4388
if _cross_family_future is not None:
    cross_family_dirs, skill_judge_outcome = _cross_family_future.result()
```
The join-before-Popen ordering claim is accurate.

But the record's conclusion — "this codebase has none today (the
closest analogue, `--append-system-prompt`, is assembled at the same
Popen-time join)... a structural addition, not a fast-path fix" — is
falsified by this repo's own `on-the-record/hooks/amendment_channel.py`,
which the record never mentions, cites, or greps for. canonical:
`on-the-record/hooks/amendment_channel.py:10-19`, read directly in this
session:
```python
"""Amendment channel (issue #3129): the local-file bridge that lets an
orchestrator's mid-flight issue-body edit reach a spawned worker session
that already read the issue once at spawn and never re-reads it.
...
The seam this uses instead: `PostToolUse` fires on every tool call in a
worker session and its output lands in that session's context
(`hookSpecificOutput.additionalContext`).
```

This is not dead or proposed code — it is registered and wired in
production. canonical: `on-the-record/hooks/amendment-channel.sh:1-6`
and `on-the-record/hooks/hooks.json` (registers this hook), both read
directly in this session:
```bash
#!/usr/bin/env bash
# PostToolUse: amendment channel (issue #3129). Registered unmatched (all
# tools) so it fires on every tool call -- the only high-frequency
# in-session channel a headless spawned worker has, since UserPromptSubmit
# (directive.sh) is a one-shot for it.
```

The write side (`write_amendment(state_dir, repo, issue, note)`,
`on-the-record/hooks/amendment_channel.py:593-616`, read directly in
this session) is a plain function taking an arbitrary `note` string (up
to `_NOTE_MAX = 2000` chars, `amendment_channel.py:362`, read directly
this session) and bumping a version marker; the read side
(`check_notice()`/`_run_hook_full()`, same file, lines 651-679 and
975-1023, read directly in this session) fires unconditionally on every
`PostToolUse` call in every session that has an issue-scoped `cwd`, and
delivers the note into that session's own context exactly once, on its
next tool call — precisely the "delivery mechanism to reach an
already-started session" the record says does not exist. Today
`write_amendment()` is triggered only from `record_amendment_from_response()`,
which fires specifically on a `gh issue edit --body` tool call
(`amendment_channel.py:874-915`, read this session) — so wiring the
`_cross_family_future`'s completion callback to call `write_amendment()`
directly is unbuilt integration work, not something that ships today.
But "unbuilt integration onto an existing, wired delivery primitive" is
a materially different, and much smaller, claim than "this codebase has
none today... a structural addition" — derived: this is a direct
contradiction between the record's stated claim (quoted above,
canonical) and the code cited in this same paragraph (canonical,
`amendment_channel.py:10-19` and `:593-616`) — the record overstates the
gap by conflating "no wiring for this specific use" with "no mechanism
at all."

This does not automatically mean async dispatch *was* safe to ship this
round — the 2000-char note cap, the "advisory, decide whether the
correction is right, do not halt" semantics `format_notice()` attaches,
and how many tool calls elapse before a session's first natural
`PostToolUse` fire are all open questions the record never gets to ask
because it stopped at "no mechanism exists." What it does mean is that
Question 3's stated reason for ruling out async is factually wrong on
its central claim (derived above, from the direct comparison between the
record's claim and the cited code), independent of whether the ultimate
no-ship-this-round outcome would survive a corrected version of that
diagnosis.

### The unnamed fifth option — scope the judge to the issue, not the dispatch

Grade: **Absent** — never raised anywhere in the record — but the
record's own Item-1 evidence already argues against it, so this omission
does not make the refusal premature.

canonical: `spawn.py:3950`, read directly in this session —
`_cross_family_task_text = task`, where `task` is the full per-dispatch
prompt text (phase framing, repair-round specifics, approval-comment
text — see the same-file `_dp("role-skill-triggers", ...)` block quoted
under Item 3 above for the shape of what gets appended per dispatch).
Task text genuinely differs dispatch-to-dispatch on the same issue
number — a phase-1 proposal spawn and a phase-2 continuation spawn for
the same issue carry different `task` strings.

An issue-scoped cache would use a *looser* key than the PR's own Item-1
cache proposal (task-text + corpus-state), collapsing exactly the
dispatch-to-dispatch differences just cited into a single served answer.
Item-1's own finding — that the *tighter* key (byte-identical task text)
already disagrees with itself 32-36% of the time (this session's
re-derivation, Item 1 above) — is evidence against the looser key too:
an issue-scoped cache would combine that same judge-internal noise with
real, legitimate task-text variation the judge is supposed to be
sensitive to, which can only make the instability worse, not better.
Nothing in this session's re-derivation of Item 1 or Item 2 suggests an
issue-scoped judge would be safer than the task-text-scoped cache the
record already rejected. The record should still have named and
dismissed this option explicitly — an issue asking "does the judge need
to run on every dispatch at all" deserves an answer to that literal
question — but a corrected record would very likely reject it too, on
evidence the PR already gathered.

### What the PR ships: tooling, tests, truncation fix

Grade: **Present**, correct, independently reproduced.

acceptance: `python3 -m pytest tests/test_issue_3230_skill_judge_cost.py -q`
(this session, `/tmp/pr3234-verify` worktree, same run cited in "What
was done" above) — result:
```
13 passed in 0.87s
```
13/13 = 100% pass, derived immediately above. canonical:
`scripts/issue-3230/measure_skill_judge.py` (materialized untracked into
this session's working tree from the PR branch, read in full this
session) — `main()` returns 1 and prints to stderr distinguishing "no
`skill_judge_perf` event at all" from "events found but all filtered as
noise," with the literal string "not a 0s median" in the error message,
matching the issue's acceptance criterion verbatim. `TestEmptyState`
(the class name exercising exactly this contract, counted directly in
this session's copy of `tests/test_issue_3230_skill_judge_cost.py`) has
5/13 = 38% of the file's passing tests, all included in the 13/13
passing result quoted above.

One undisclosed scope note: canonical: `git diff main origin/issue-3230/diagnose-first+implementation-blueprint+experiment-trust-a01a3586 -- consult.py`,
run this session — the diff widens **two** truncation limits, not one —
```python
-            f"| question={question[:200]!r} | outcome={outcome[:300]!r}")
+            f"| question={question[:4000]!r} | outcome={outcome[:2000]!r}")
```
The PR body and the PR's own record's "What was done" section both
describe only the question-field widen ("widened
`_append_consult_trace()`'s question-field truncation... from 200 to
4000 characters"); canonical: PR #3234's body and its own record, read
in full this session — neither mentions the outcome-field change (300→2000)
at all. It is the same class of fix (observability-only, matches the
comment already present at `consult.py:437-449`) and does not touch
selection or timing logic, so this is not a correctness defect — but it
is a real, silent scope expansion beyond what the PR's own description
says it did.

## What did not work

None. canonical: this session's own commands and their printed output,
quoted throughout "What was done" and "Why" above (worktree pytest runs,
the `/tmp/verify_repeats.py` / `/tmp/verify_repeats3.py` /
`/tmp/robust_parse.py` / `/tmp/live_agreement_verify.py` re-derivations)
— every planned re-derivation in this session ran to completion and
produced output; none was abandoned mid-session. The naive quote-
matching regex parser used in an early pass of Item 1 was superseded by
the `ast.literal_eval`-based parser once its no-match failure mode was
found — derived: `python3 /tmp/debug_pick.py`, this session, ran the
naive parser against 8 sampled multi-occurrence keys and got 0/8 = 0%
successful `picked=` extractions, shown in Item 1 above — this is a
correction made within this session's own diagnostic work, not a
deviation from an approved plan; this session runs single-phase under
the build-now bypass with no phase-1 proposal to diverge from.

## Upstream basis

- PR #3234 / branch `issue-3230/diagnose-first+implementation-blueprint+experiment-trust-a01a3586`,
  sha `c2151465252020fc4f18d150339469f77af93fb9` — the deliverable this
  record verifies (`verifies_subject: true`).
- PR #3234's own diagnosis record, same sha (path is on that PR's own
  branch, not materialized in this session's working tree per this
  session's own write-set restriction — read via `git show
  origin/issue-3230/diagnose-first+implementation-blueprint+experiment-trust-a01a3586:docs/issue-3230/reports/diagnose-first+implementation-blueprint+experiment-trust-a01a3586.md`
  this session) — every claim graded above is drawn from and cited
  against this record's own text.
- `spawn.py`, `consult.py`, `on-the-record/hooks/amendment_channel.py`,
  `on-the-record/hooks/amendment-channel.sh`,
  `on-the-record/hooks/hooks.json` — this session's own repository
  checkout (branch `issue-3230/adversarial-review+diagnose-first+experiment-trust-f2f4f629`),
  read directly, pre-existing files unmodified by this session.

## Open findings

- **Item 3 (async) should be re-diagnosed with the amendment channel in
  scope**: whether wiring `write_amendment()` to the `_cross_family_future`
  completion callback (instead of, or alongside, the current `gh issue
  edit` trigger) is actually safe — note-size limits, advisory-vs-binding
  semantics, how many tool calls elapse before first delivery — is a real
  open question this session did not resolve, only showed was wrongly
  foreclosed. Resolution path: a follow-up diagnosis session scoped to
  "can the amendment channel carry a skill-judge correction," reusing
  this record's Item 3 citations as its starting point.
- **The fifth option (issue-scoped judge) was reasoned about but not
  empirically tested**: this session argued from the record's own
  Item-1 numbers that it would likely be rejected, but did not run a
  live comparison the way Item 2 did. Resolution path: if a future
  session wants to close this gap fully, re-run Item 1's methodology
  grouped by `issue` alone (dropping the `question` half of the key) and
  report the resulting disagreement rate directly.
- **This session's own corpus-scan numbers (n=291, 32%, 36%, all derived
  in Item 1 above) are themselves a live, growing-corpus measurement**,
  not a frozen ground truth — a future re-run will not reproduce them
  exactly, same caveat the PR's own record already carried for its n=56
  numbers.

## Next steps

canonical: `python3 -m pytest tests/test_issue_3230_skill_judge_cost.py -q`
— result: 13 passed (this session, quoted in full under "What was
done"); acceptance: `python3 scripts/issue-3230/measure_skill_judge.py --report`
— result: exit code 0 (this session, quoted in full under "What was
done") — all re-derivations this session planned to run (cache scan,
BM25 live comparison, `spawn.py`/`amendment_channel.py` code reading,
full test suite) completed and produced output; no outstanding execution
remains for this session. loop_state: done.

## Skill verdicts

skill-verdict: adversarial-review — applied: invoked; this session is
structurally independent from PR #3234's authoring session (no shared
context), received the PR's deliverable (record + diff + shipped files)
and evaluated it for real, located defects per the skill's procedure —
the Item 3 finding (async claim Incorrect) and the Item 1 methodology
gap (corpus duplication + field-name undercount, unremarked in the PR)
are exactly the kind of self-review-blind-spot this skill exists to
surface.
skill-verdict: diagnose-first — applied: invoked; used G2's "verify
against evidence, not opinion" axis to re-derive each of the record's
three Stage-2 causal claims independently rather than taking the
record's own numbers on trust, and the Amdahl-style share reasoning to
argue why an issue-scoped cache (a looser version of an already-rejected
tighter key) is unlikely to be safer without a fresh test.
skill-verdict: experiment-trust — not-applicable: invoked; checked the
Step 1 scope gate against the judge-vs-BM25 comparison (the one thing in
PR #3234 that resembles a variant contrast) — it is a paired diagnostic
comparison run against fixed, non-randomly-assigned inputs, not an
online controlled experiment with random assignment to variants, so per
the skill's own scope gate this routes away from SRM/A/A validation
rather than through it. This matches the PR record's own skill-verdict
for `experiment-trust`, independently re-checked here rather than
accepted on the PR's say-so.

## Evidence appendix

`/tmp/verify_repeats3.py` (content-hash dedup + PR's own regex, Item 1
first-pass re-derivation):
```python
import glob, re, collections, hashlib

paths = glob.glob('/home/jwjung/.tokenmaxxxer/work/*/docs/issue-*/reports/consult-log/*.md') + \
        glob.glob('/home/jwjung/.tokenmaxxxer/work/*/docs/issue-*/reports/consult-log.md') + \
        glob.glob('/home/jwjung/.tokenmaxxxer/work/*/docs/reports/consult-log/*.md')

seen_hashes = {}
dup_files = 0
unique_paths = []
for p in paths:
    try:
        content = open(p, 'rb').read()
    except Exception:
        continue
    h = hashlib.sha256(content).hexdigest()
    if h in seen_hashes:
        dup_files += 1
        continue
    seen_hashes[h] = p
    unique_paths.append(p)

print("unique-by-content files:", len(unique_paths), "| duplicate files skipped:", dup_files)
```

`/tmp/robust_parse.py` (ast.literal_eval-based trace-line parser, Item 1
final re-derivation — full body):
```python
import glob, re, collections, hashlib, ast

paths = glob.glob('/home/jwjung/.tokenmaxxxer/work/*/docs/issue-*/reports/consult-log/*.md') + \
        glob.glob('/home/jwjung/.tokenmaxxxer/work/*/docs/issue-*/reports/consult-log.md') + \
        glob.glob('/home/jwjung/.tokenmaxxxer/work/*/docs/reports/consult-log/*.md')

seen_hashes = {}
unique_paths = []
for p in paths:
    try:
        content = open(p, 'rb').read()
    except Exception:
        continue
    h = hashlib.sha256(content).hexdigest()
    if h in seen_hashes:
        continue
    seen_hashes[h] = p
    unique_paths.append(p)

FIXTURE_ISSUES = {"2040", "2055", "2061", "2274", "1", "none"}
FIXTURE_TASK_PREFIXES = ("Task:\ntask\n", "Task:\nplease write a haiku")

def literal_prefix(s, start):
    quote = s[start]
    i = start + 1
    n = len(s)
    while i < n:
        c = s[i]
        if c == '\\':
            i += 2
            continue
        if c == quote:
            return s[start:i+1], i + 1
        i += 1
    return None, None

def parse_trace_line(line):
    m = re.match(r"^- (\S+) \| (?:skill|role)=(\S+) \| verb=(\S+) \| issue=(\S+) \| question=", line)
    if not m:
        return None
    ts, skill, verb, issue = m.groups()
    qstart = m.end()
    if qstart >= len(line) or line[qstart] not in "'\"":
        return None
    qlit, after_q = literal_prefix(line, qstart)
    if qlit is None:
        return None
    rest = line[after_q:]
    m2 = re.match(r"^ \| outcome=", rest)
    if not m2:
        return None
    ostart = m2.end()
    if ostart >= len(rest) or rest[ostart] not in "'\"":
        return None
    olit, after_o = literal_prefix(rest, ostart)
    if olit is None:
        return None
    try:
        question = ast.literal_eval(qlit)
        outcome = ast.literal_eval(olit)
    except Exception:
        return None
    return {"ts": ts, "skill": skill, "verb": verb, "issue": issue,
            "question": question, "outcome": outcome}

def picked_names(outcome):
    if not outcome.startswith("ok:"):
        return None
    m = re.search(r"picked=\[([^\]]*)\]", outcome)
    if not m:
        return None
    return tuple(sorted(re.findall(r"([a-zA-Z0-9_-]+)=", m.group(1))))

total = 0
parsed = 0
fixture = 0
real_counter = collections.Counter()
real_entries = collections.defaultdict(list)
for p in unique_paths:
    text = open(p, errors='replace').read()
    for line in text.splitlines():
        if '| verb=skill_judge |' not in line:
            continue
        total += 1
        rec = parse_trace_line(line)
        if rec is None:
            continue
        parsed += 1
        issue, question, outcome = rec["issue"], rec["question"], rec["outcome"]
        if issue in FIXTURE_ISSUES or question.startswith(FIXTURE_TASK_PREFIXES):
            fixture += 1
            continue
        key = (issue, question)
        real_counter[key] += 1
        real_entries[key].append(rec)

real_total = sum(real_counter.values())
repeats = {k: c for k, c in real_counter.items() if c > 1}
repeat_events = sum(c - 1 for c in repeats.values())

agree = 0
disagree = 0
error_pairs = 0
for k, entries in real_entries.items():
    if len(entries) < 2:
        continue
    picks = [picked_names(e["outcome"]) for e in entries]
    ok_picks = [pk for pk in picks if pk is not None]
    if sum(1 for pk in picks if pk is None):
        error_pairs += 1
    if len(ok_picks) < 2:
        continue
    first = ok_picks[0]
    for pk in ok_picks[1:]:
        if pk == first:
            agree += 1
        else:
            disagree += 1
```

`/tmp/live_agreement_verify.py` (Item 2 independent live driver — issue
list and driver body):
```python
import sys, time, json
from pathlib import Path
import consult
import spawn as _sp

SCRATCH = Path("/tmp/otr-issue3230-verify-judge-sample")
SCRATCH.mkdir(parents=True, exist_ok=True)
TASKS = [
    (3229, "Wire the delegation checker into the live turn, or say honestly that the seam cannot enforce"),
    (3183, "R007: launcher-owned trust root for the consumer-path comparison, replacing the in-session skills toggle"),
    (3134, "supersedes: cannot correct one section of a foreign record -- add amends:, with discoverability as the actual requirement"),
    (3125, "The dead-monitor recovery path is an instruction to the orchestrator, so recovery depends on a model noticing a line"),
    (3120, "The heartbeat dies whenever the checkout HEAD moves: rc=95 (stale code) is unclassified and nothing restarts it"),
    (3118, "Verification sessions leave /tmp worktrees no cleanup mechanism can see, and session logs are never swept"),
    (3095, "spawn-on-pr's parked-subject list leaks across repos the same way requirement-drift did"),
    (3091, "A second test directory has been red all along, and 12 of its 15 failures are in the skill layer"),
    (3083, "main is red: a wiring test that only passes before its own change lands, plus four respawn-gate failures"),
    (3182, "consumer loop: enumerate and shrink the preconditions a plugin-only install does not satisfy"),
]
repo_root = _sp._skill_repo_root()
for issue, task_text in TASKS:
    t0 = time.monotonic()
    scored = consult._sp._bm25_cross_family_scores(
        task_text, "diagnose-first", repo_root, Path.home(), Path.cwd())
    bm25_top = [name for _s, name, _d, _src in scored[:8]]
    picked_dirs, outcome = consult._cross_family_skill_matches_with_consult(
        task_text, "diagnose-first", repo_root, None, str(SCRATCH),
        k=2, home=Path.home(), target_repo_root=Path.cwd())
    dt = time.monotonic() - t0
    print(json.dumps({
        "issue": issue, "wall_s": round(dt, 3), "outcome": outcome,
        "bm25_top2": bm25_top[:2],
        "judge_picked": [d.name for d in picked_dirs],
    }))
```
