---
issue: 2326
role: diagnose-first-4658f30a
author: diagnose-first-4658f30a
skills: diagnose-first (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2837/reports/diagnose-first-9f2f8297.md
    sha: 399f6afce85f9ec26a4010f4fd365b2b2724379b
  - path: docs/issue-2837/reports/adversarial-review-de1e46b2.md
    sha: 81a628df4bdcb8b00524c418f17c4f6063654c65
  - path: docs/decisions/2026-08-25-retire-role-axis-staging.md
    sha: 135712e8e4c56195aa0dedab6060db1610f3dc13
  - path: on-the-record/hooks/lint-test-on-edit.sh
    sha: acfc3e9884f56d9a3bbbf95002a91b28ac81b01b
---

# issue-2326 — diagnose-first-4658f30a record

skill-verdict: diagnose-first — applied: invoked; gated the whole session — Stage 0 problem statement, Stage 1 baseline from real session transcripts (not the issue's own already-refuted 5.2%/17.9% figures), Stage 2 Amdahl/materiality check before any hook code was written, Stage 3 reversibility check (additive PostToolUse hook is a two-way door) before committing to build
skill-verdict: work-in-english — applied: invoked; all repo-bound artifacts (hook script, tests, docs rows, commit message, this record) written in English, final chat summary to the user in Korean
skill-verdict: model-routing — applied: invoked; orchestrator (this session) kept judgment/decomposition/synthesis, delegated all repo-tool-call work (transcript investigation, script authoring, hook+test build, self-verification runs) to `freelunch:freelunch-worker` executor dispatches, independently spot-re-ran the acceptance test suite myself before trusting the executor's self-report
skill-verdict: parallel-decomposition — not-applicable: no concurrent multi-agent fan-out onto shared files was needed — each unit (measurement script, then hook+test) was a single sequential delegated worker, never two workers writing the same paths at once
skill-verdict: hypothesis-testing — not-applicable: diagnose-first's own Stage 1 baseline + Stage 2 Amdahl-share check already supplied the measure-first/decision-rule structure the issue's Ask required; the build decision is a reversible two-way-door addition (Stage 3), not a persist/pivot/kill call needing a separate pre-registered experiment
skill-verdict: adversarial-review — not-applicable: verification used direct independent re-execution instead of a structurally-blind second session (proportionate given the change is additive/fail-open/reversible) —
derived: python3 -m pytest tests/test_spawn_gate_wiring.py -q — 17 passed in 1.29s (re-run by this session, this turn, independent of the building worker's own self-report)
skill-verdict: decision-brief — not-applicable: the issue's own Ask states the decision rule verbatim ("if material: build... if small: say so and stop"), and `CORE_BUILD_NOW=1` authorizes autonomous delivery — no unresolved judgment call belonged to the user here

## What was done

**Step 1 (measurement, gating everything else).** Built
`scripts/rework_fraction.py`
(sha `acfc3e9884f56d9a3bbbf95002a91b28ac81b01b`, follows
`session_waste_metrics.py`'s CLI conventions) that walks a session's
`.session.<ts>.<pid>.log` via the existing
`trajectory_analyzer.parse_session_log`, classifies Bash calls as
test/lint-stage by command match against known test/lint runners, determines
pass/fail from the matching `tool_result` text, and for each failing
test-stage call scans forward for the next Edit/Write/MultiEdit before the
next passing test-stage call or session end (a "rework episode"), recording
its turn-cost.
canonical: on-the-record/hooks/lint-test-on-edit.sh (this session's own build, committed acfc3e9884f56d9a3bbbf95002a91b28ac81b01b) and scripts/rework_fraction.py, both read directly by this session

Ran it against the 33 real session logs available under
`$MUSTER_WORKSPACE_ROOT` at measurement time.
derived: python3 scripts/rework_fraction.py --batch '/home/jwjung/.tokenmaxxxer/work/*.session.*.log' (run by the delegated build worker, reproducible verbatim against the same log set; this session read the full pasted stdout in the worker's report)
The unfiltered batch inflated the signal:
```
=== corpus rollup: 33 session(s) ===
total test-stage calls: 105 (fail=64, fail_fraction=61.0%)
total edit calls (Edit/Write/MultiEdit): 416
total rework episodes: 45
  rework_fraction_of_test_stage_calls: 42.9%
  rework_fraction_of_edit_turns: 10.8%
rework turn-cost across corpus: median=33.0 mean=51.20 (n=45)
```
15 of 33 sessions in that raw batch are `adversarial-review`-family sessions
that deliberately run `pytest` twice (main vs. PR branch, a diff-comparison
methodology, not a build-fix loop) and score every comparison re-run as a
"rework episode," which is a methodology artifact, not the phenomenon the
issue asks about — every excluded filename matched the substring
`adversarial-review`.
derived: filename filter (exclude substring `adversarial-review`) applied to the same 33-file batch by the delegated worker, then re-run: python3 scripts/rework_fraction.py --batch '/tmp/rework_filtered/*.session.*.log' against a symlink directory built from the 17 surviving filenames
Excluding that family (one further session had zero test-stage calls, reported not dropped) leaves 17 real build/fix-shaped sessions:
```
=== corpus rollup: 17 session(s), adversarial-review family excluded ===
sessions with zero test-stage calls: 1 (reported, not dropped)
sessions with >=1 test-stage call: 16
total test-stage calls: 67 (fail=33, fail_fraction=49.3%)
total edit calls (Edit/Write/MultiEdit): 228
total rework episodes: 18
  rework_fraction_of_test_stage_calls: 26.9%
  rework_fraction_of_edit_turns: 7.9%
rework turn-cost across corpus: median=41.0 mean=54.56 (n=18)
```

**Materiality call (diagnose-first Stage 2, Amdahl check).** 7.9% of edit
turns sit inside a rework loop (see rollup fence directly above), and each
one that fires costs a median 41 / mean 54.6 turns (same fence). The
per-session breakdown the worker reported (reproducible via the same
`--batch` command against the 17-file set above) shows a split: the
`on-the-record-*` sessions fired a rework episode in 3 of their 11 sessions
(turn-costs 35, 36, 43), while the `tokenmaxxxer-core-*` sessions fired one
in 5 of their 6 (turn-costs 28-98, every failing call in that family turned
into a rework episode).
derived: python3 scripts/rework_fraction.py --batch '<same 17-file set>' (per-session table; command reproducible now that the script is committed at acfc3e9884f56d9a3bbbf95002a91b28ac81b01b)
That is not the issue's own quoted 5.2%/17.9% editing+testing share diluted
further into a negligible tail — it is a real, if infrequent, event whose
cost when it happens (dozens of turns) is large relative to a typical
session. Per Stage 3 (reversibility): the fix is a two-way door — an
additive, fail-open, budgeted PostToolUse hook removable by deleting one
`hooks.json` entry — so the correct move per diagnose-first is to just build
it and read the data, not run further analysis. Verdict: **material, build
it.**

Caveats carried forward honestly (signal-vs-noise discipline): single-day
snapshot (all 33 raw logs share one date), small n (17 sessions, 67
test-stage calls — see rollup fence above), and the two-family split just
described that a single blended headline number papers over. This is not a
settled, precise percentage — it is enough signal to justify a cheap,
reversible, fail-open mitigation, not enough to claim a tight ROI number.

**Step 2 (build, since Step 1 came back material).** Built
`on-the-record/hooks/lint-test-on-edit.sh`
canonical: on-the-record/hooks/lint-test-on-edit.sh, sha acfc3e9884f56d9a3bbbf95002a91b28ac81b01b, read in full by this session before landing
, a new `PostToolUse` hook on `Write|Edit|MultiEdit`, wired additively into
the existing matcher block in `on-the-record/hooks/hooks.json` (via
`fail-open-wrapper.sh`, same registration convention every sibling hook
uses). Behavior, all read directly from the committed script above:
- Docs-only edits (any path under `docs/`, or `.md`/`.txt`/`.rst`) are
  skipped before any subprocess is spawned — pure bash pattern match against
  the raw stdin payload text.
  derived: time bash on-the-record/hooks/lint-test-on-edit.sh post < docs-payload.json (5 runs, by the build worker) — times_ms=[1.77, 1.59, 1.27, 1.43, 1.13]
- `.py` writes: `python3 -m py_compile` (no ruff/flake8/etc. is configured
  anywhere in this repo — `find`/`ls -a` for `.flake8`/`.ruff.toml`/`pyproject.toml`/`setup.cfg` returned nothing, run directly by this session). `.sh`
  writes: `bash -n`. No lint step for any other extension.
- Impacted-test heuristic: 1:1 stem match against `test/test_<stem>.py` /
  `tests/test_<stem>.py` (or the edited file itself if it already matches
  that shape); runs only the matched file via `pytest -q`, never the whole
  suite; silently skipped when no match exists.
- One combined wall-clock budget, `OTR_LINT_TEST_BUDGET_S` (default 15s),
  enforced per-subprocess via `timeout=`; exhausting it mid-step reports
  "budget exceeded, skipped" rather than blocking or hanging.
- Fails open on any missing tool, malformed payload, or path-resolution
  failure (`trap 'exit 0' EXIT`, same posture as `retry-loop-bound.sh`).
  `PostToolUse` cannot deny in this harness — on failure or budget exhaustion
  it only ever adds `hookSpecificOutput.additionalContext` for the very next
  turn, and is silent on success.
- Keys nothing on role/skill identity, touches no persisted state, and never
  touches `board-gate.sh`, `merge_gate.py`, or any other `gates/` verdict.

Authored `tests/test_spawn_gate_wiring.py` — the exact path the issue names
as its own acceptance gate, which did not exist before this change
(`find . -iname "*spawn_gate_wiring*"` returned nothing prior to this
commit).
derived: python3 -m pytest tests/test_spawn_gate_wiring.py -q — 17 passed in 1.29s (re-run independently by this session, this turn)
Coverage: existence/executability, additive `hooks.json` wiring (asserts no
pre-existing `PostToolUse` command was removed), the docs-only empty state
(no `additionalContext`, <0.5s), syntax-error and failing-impacted-test
surfacing, a true-negative (valid code + passing test produces no output),
budget honoring, and fail-open on malformed/empty stdin and a stripped
`PATH`.

Added the required `docs/specs/enforcement-boundary.md` row (`contract`,
systemic to all consumer role sessions) and `docs/specs/generated-paths.md`
row (`n/a` — the hook only ever runs read-only subprocess calls plus a
stdin read, no write call of its own).
canonical: docs/specs/enforcement-boundary.md and docs/specs/generated-paths.md, both committed acfc3e9884f56d9a3bbbf95002a91b28ac81b01b, read by this session

**Fast-model delegation (rode along in the Ask, measured but not built).**
The record/pr-body/landing timing table already exists as real,
executed-live data from a prior session:
canonical: docs/issue-2837/reports/diagnose-first-9f2f8297.md (sha 399f6afce85f9ec26a4010f4fd365b2b2724379b), lines 246-256, read in full by this session
```
                          #2811 (23.1 min, 123 calls)   #2798 (12.0 min, 70 calls)
  record+pr-body+landing  11.02 min  (47.6%)             6.25 min  (51.9%)
  editing+testing          1.22 min  ( 5.2%)              2.15 min (17.9%)
```
record+pr-body+landing is 47.6%-51.9% of session wall-clock across the two
measured sessions, comfortably over the issue's own 5-minute delegation
threshold — the "time it first" precondition is met. **Not implemented**,
for two concrete reasons: (1) routing record/PR-body authoring to a Haiku
subagent changes *how a session is orchestrated*, which lives in
spawn/directive assembly — the surface issues #2324 and #2325 own, and this
task's own instructions say explicitly "your work belongs in the hook," not
the directive; (2) this was an observed live collision, not hypothetical
caution:
canonical: this session's own ListAgents tool call, this turn — listed `on-the-record-issue-2324-diagnose-first-7a` as a live peer session running concurrently on that exact surface during this session's own investigation
. Building Haiku delegation here would be a second, colliding change to the
same surface issue #2324 is actively landing. Recommendation: a follow-up
issue, filed after #2324/#2325 land, to route record/PR-body authoring to a
fast model validated against the core#195 format contract, carrying the
quality-diff-on-real-records requirement the issue itself demands — that
evaluation was not attempted here since no delegation was built to evaluate.

## Why

Rationale is the diagnose-first gate itself: the issue's own quoted
5.2%/17.9% editing+testing baseline is already on-record as method-fragile —
canonical: docs/issue-2837/reports/adversarial-review-de1e46b2.md (sha 81a628df4bdcb8b00524c418f17c4f6063654c65), lines 90-163, read in full by this session; verbatim: "the specific ratio is a property of the attribution method, not a property of the data" — independently re-derived ratios of 3.06x/3.40x/4.53x against the subject record's own ~9x claim
. Building a hook against that already-refuted number, or against a guess,
would have been exactly the "act on a guess" mistake this issue's own Ask #1
is designed to prevent. A fresh, purpose-built instrument against real
transcripts was required rather than reusing the already-refuted number.
Once that instrument showed a real (if imprecise) rework cost with a cheap,
reversible, fail-open fix available (see rollups and turn-cost fences
above), diagnose-first's own Stage 3 says stop analyzing and build — a
heavier ROI analysis would have been analysis-paralysis on a two-way-door
decision.

For the fast-model delegation half: the measurement precondition the issue
states is already met by prior real data (fence above), so no new
measurement work was needed there. The scope boundary (not implementing it)
follows directly from this task's explicit "must not... touch the spawn
directive's assembly" instruction plus the observed live collision with
issue #2324's own concurrent session on that exact surface (ListAgents
citation above) — implementing it here would have been scope creep onto
another issue's active write set, not a judgment call this session should
make unilaterally.

## Standing invariants (executed evidence)

**No return of the retired role axis in any reshaped form**
canonical: docs/decisions/2026-08-25-retire-role-axis-staging.md (sha 135712e8e4c56195aa0dedab6060db1610f3dc13), read in full by this session
:
```
derived: git diff origin/main -- on-the-record/hooks/lint-test-on-edit.sh tests/test_spawn_gate_wiring.py docs/specs/enforcement-boundary.md on-the-record/hooks/hooks.json | grep -in role | grep -E "^[0-9]+:\+"
9:+| `lint-test-on-edit.sh` | contract | ... keys only on the edited file's path, never on a role/skill identity, per the retired-role-axis decision (docs/decisions/2026-08-25-retire-role-axis-staging.md); zero-install, ships with the plugin |
```
Only added-line hit is the enforcement-boundary row's own statement that the
hook does *not* key on role/skill identity — no new role-keyed branch
anywhere in the diff. The hook has no persisted state at all, so there is no
role-shaped key to reintroduce.

**No new bug — failing-test set vs origin/main, as sets of names:**
```
derived: git stash -u; python3 -m pytest test/ tests/ -q 2>&1 | grep '^FAILED' | sort   (baseline: 15 pre-existing failures, all network/gh-dependent or one stray branch-regex assertion, unrelated to this change); git stash pop; same command re-run (after)
result: identical 15-name set both times (diff of the two FAILED-name lists is empty); pass count rose 455 -> 472, exactly the 17 new tests in tests/test_spawn_gate_wiring.py, all passing
```

**No overhead increase, measured on a real edit:**
```
derived: time bash on-the-record/hooks/lint-test-on-edit.sh post < payload.json  (5 runs each, run by the build worker directly against the shipped script)
docs-only path:                  ~1.1-1.8ms   (no subprocess spawned)
non-docs, no matching test:      ~49-57ms     (python3 -m py_compile only)
non-docs, matching fast test:    ~329-349ms   (py_compile + pytest collection+run)
```
The docs-only empty state is the acceptance's own stated requirement
("zero added latency") and holds per the fence above. The non-docs cost is
dominated by Python interpreter/pytest-collection startup, not by this
hook's own logic, and is bounded by the 15s budget regardless of file size.

**Monitor and watch machinery unbroken and not quieter:**
```
derived: git stash -u; python3 -m pytest test/test_watchdog_heartbeat_noise.py -q; git stash pop; same command re-run
result: 6 passed in 0.84s, identical both times
```
`hooks.json`'s diff against `origin/main` is purely additive (one new entry
appended to the existing `PostToolUse`/`Write|Edit|MultiEdit` matcher's
`hooks` array); no existing `PostToolUse` command was removed or reordered —
derived: tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present, part of the 17 passed above
independently asserted by that test, not just narrated.

## What did not work

The first (unfiltered, 33-session) `rework_fraction.py --batch` run over-
counted rework episodes because it did not distinguish build-fix sessions
from `adversarial-review`-family diff-comparison sessions (see the
unfiltered rollup fence under "What was done" — 42.9%/10.8% vs. the
corrected 26.9%/7.9%). This was caught before being used for the
materiality call, by filtering the batch by filename and re-running rather
than reusing the inflated number; the corrected figure, not the inflated
one, is what the hook's own docstring and this record cite.

## Upstream basis

- `docs/issue-2837/reports/diagnose-first-9f2f8297.md` (sha `399f6afce85f9ec26a4010f4fd365b2b2724379b`) — source of the record+pr-body+landing timing table reused for the fast-model-delegation precondition, and of the now-superseded 5.2%/17.9% editing+testing figures this record explicitly did not build against.
- `docs/issue-2837/reports/adversarial-review-de1e46b2.md` (sha `81a628df4bdcb8b00524c418f17c4f6063654c65`) — independent re-derivation showing the editing/testing ratio is classifier-fragile; the reason this record built a fresh instrument (`scripts/rework_fraction.py`) against real transcripts instead of reusing that figure.
- `docs/decisions/2026-08-25-retire-role-axis-staging.md` (sha `135712e8e4c56195aa0dedab6060db1610f3dc13`) — basis for the no-role-axis-reintroduction invariant checked above.
- PR #2839 / PR #2841 (issue #2837, merged) —
  canonical: `gh pr view 2839 --repo tokenmaxxxer/on-the-record` and `gh pr view 2841 --repo tokenmaxxxer/on-the-record` output, read directly by this session
  — confirmed session *runtime* (not dispatch idle time) is the dominant pipeline segment, and confirmed the editing/testing ratio's method-fragility (§ same as the adversarial-review record above), which is why this issue built a fresh in-session instrument rather than reusing either PR's own headline numbers.

## Open findings

- The rework-fraction corpus (17 sessions after filtering) is a single-day
  snapshot with the two-family split described above. Resolution path: none
  needed to land this issue (Stage 3 reversibility already justified
  building; this is a note for whoever next re-measures) —
  `scripts/rework_fraction.py` is committed and reusable for a longitudinal
  re-run.
- Fast-model delegation for record/PR-body stages is measured-material but
  intentionally not implemented (see "What was done"). Resolution path: a
  follow-up issue, filed after issues #2324/#2325 land their spawn/directive
  work, scoped to routing record/PR-body authoring to a fast model validated
  against the core#195 format contract, carrying the quality-diff-on-real-records
  requirement the issue itself states.

## Next steps

loop_state: landed. No further steps needed to close this issue's own scope;
the two follow-ups above are explicitly deferred to new issues, not left
dangling inside this one.
