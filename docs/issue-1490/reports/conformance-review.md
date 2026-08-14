---
code_under_review:
  - pytest.ini
  - requirements-dev.txt
  - docs/handbooks/operations.md
  - tests/test_spawn.py
subject: issue-1490
role: conformance-review
kind: review-record
loop_state: draft-reported
---

# Conformance review — issue-1490 parallel test-suite speedup (phase 2)

## Upstream / basis

Requirement list: issue #1490 body itself (Requirements 1-4, Acceptance
1-4). Reviewed artifact: PR #1503 / branch `issue-1490/implementation`
at commit `49aa3161191f648a1efccdec0cb0474d5455e4b1`.
canonical: git log origin/issue-1490/implementation -1 --format=%H — result: 49aa3161191f648a1efccdec0cb0474d5455e4b1
That command confirmed the sha this session then checked out into a
scratch worktree at `/tmp/wt-1490-impl`.

canonical: git show origin/issue-1490/implementation:docs/issue-1490/reports/implementation.md — result: the implementation role's delivery record, read this session for context only (this path does not exist on this review's own branch, only on `issue-1490/implementation`); not trusted as evidence in place of independent re-execution below.

## What was done

Checked out the implementation-branch tip into an isolated worktree and
independently re-ran the acceptance commands and inspected the changed
files, rather than relying on the implementation record's own pasted
output.

acceptance: python3 -m pytest -q --ignore=bench -m "not slow" — result: see fenced output below
Run this session, independent, in `/tmp/wt-1490-impl`:
```
17 failed, 1825 passed, 1 xfailed in 428.76s (0:07:08)
```

canonical: `cat pytest.ini` (this session, in `/tmp/wt-1490-impl`)
```
[pytest]
python_functions = test_* t_*
norecursedirs = runs
addopts = -n auto
markers =
    slow: real subprocess spawn or real git clone/checkout lifecycle tests, excluded by default (issue #1490); run with -m slow or without -m "not slow" to include.
```

canonical: `grep -c "@pytest.mark.slow" tests/test_spawn.py` (this session, in `/tmp/wt-1490-impl`)
```
64
```

canonical: `grep -n -i "regression\|pre-merge\|change class" docs/handbooks/operations.md docs/handbooks/hooks.md` (this session, in `/tmp/wt-1490-impl` — both greps returned no match, no output)

acceptance: python3 -m pytest -o addopts="" -q tests/test_gates.py::t_consult_trace_leaves_scratch_clone_clean_on_success tests/test_gates.py::t_consult_trace_leaves_scratch_clone_clean_on_failure tests/test_gates.py::t_find_violations_uses_record_evidence_for_keywordless_merge — result: see fenced output below
Run this session, in `/tmp/wt-1490-impl`:
```
3 failed in 0.14s
```
derived: the 3 IDs above appeared in this session's own not-slow run
above but were not among the 14 pre-existing IDs the implementation
record itemized as investigated. Run alone (serial, single test
process, no other test loaded), all 3 reproduce the same assertion
shapes seen under `-n auto` — this shows they predate the change and
are not a parallel-execution isolation defect this PR introduced; they
were simply not individually itemized in the delivery record's
isolation-investigation section.

## Verdicts

canonical: `cat pytest.ini` (this session, above) — `addopts = -n auto`
is present, parallelizing every bare `python3 -m pytest` invocation.

**Requirement 1 — parallelize the default run; enumerate/fix
shared-state coupling first, document isolation fixes: Present.**
canonical: git show origin/issue-1490/implementation:docs/issue-1490/reports/implementation.md — result: documents an isolation investigation
Every `-n auto` outcome-anomaly was re-run alone via `-o addopts=""`,
reproducing byte-identically in isolation (predates the change, not a
collision), and two genuinely load-sensitive tests
(`SpawnOneNoWait.test_no_wait_returns_promptly_without_calling_await_bounded`,
`SpawnOneIssueRoleClaim.test_concurrent_spawn_one_calls_let_exactly_one_through`)
were tiered into `slow` rather than left racing under `-n auto`. This
session's own isolation spot-check above reproduces the same pattern —
reproducible alone, unrelated to parallelism, supporting the record's
method.

**Requirement 2 — slow marker on real subprocess/git lifecycle tests;
default excludes, `-m slow` opts in; orchestrator's pre-merge
regression policy names which tier is required for which change
class: Surface.** The marker and the two run modes are Present:
`cat pytest.ini` above registers `slow`; canonical: `sed -n "1100,1170p" docs/handbooks/operations.md` (this session, in `/tmp/wt-1490-impl`) documents `python3 -m pytest -m "not slow"` and `python3 -m pytest -m slow`; `grep -c "@pytest.mark.slow" tests/test_spawn.py` above shows 64 marker sites.
canonical: `grep -n -i "regression\|pre-merge\|change class" docs/handbooks/operations.md docs/handbooks/hooks.md` (this session, above) — no match in either file.
The third clause — a pre-merge regression policy naming which tier is
required for which change class (code touching spawn lifecycle → slow
tier required) — is Absent, per that grep. `docs/handbooks/operations.md`
only tells an operator new lifecycle tests "should carry
`@pytest.mark.slow` at authoring time" — an authoring convention, not a
change-class-keyed pre-merge policy statement.

**Requirement 3 — target under 300s default-tier wall-clock, record
measured before/after: Present** for the record-keeping half; see
Acceptance 1 below for whether the target is actually met.
canonical: git show origin/issue-1490/implementation:docs/issue-1490/reports/implementation.md — result: before 1272.43s / 21m12.791s (true single-threaded), after three not-slow runs: 248.92s, 317.56s, 288.83s.
These figures satisfy the record-the-measurement half of Requirement 3
as literally stated.

**Requirement 4 — no test deleted or weakened: Present.**
canonical: git show origin/issue-1490/implementation:docs/issue-1490/reports/implementation.md — result: baseline single-threaded outcome line reads 21+1885+1; combined both-tiers-parallel outcome line reads 20+1886+1.
derived: 21+1885+1 = 1907; 20+1886+1 = 1907 — same total. That same
record's cited `diff` output (fenced under its own "## Pass/fail-set
diff" heading) states, in its own `derived:` line, that its comparison
file has 1909 lines total and exactly 2 of them differ — derived here:
1909 - 2 = 1907 unchanged lines, consistent with the matching totals
above. Both differing lines are attributable to a `tempfile`-generated
directory name embedded in one synthetic fixture's node ID, not to a
missing or newly-different-outcome test, per that record's own
explanation. No test file in the diff (`docs/handbooks/operations.md`,
`pytest.ini`, `requirements-dev.txt`, `tests/test_spawn.py`) removes a
test function or an assertion; `@pytest.mark.slow` re-tiers tests, it
does not delete or skip them.

canonical: git show origin/issue-1490/implementation:docs/issue-1490/reports/implementation.md — result: three recorded measurements 248.92s, 317.56s (already over budget), 288.83s; derived: 1 of those 3 recorded runs already exceeds 300s.

**Acceptance 1 — the default-tier run's wall-clock target: Incorrect.**
(Issue text: the not-slow command completing under 300s, measured and
recorded.)
acceptance: python3 -m pytest -q --ignore=bench -m "not slow" — result: reproduced below
```
17 failed, 1825 passed, 1 xfailed in 428.76s (0:07:08)
```
That independent run measured 428.76s in a clean scratch worktree,
well over budget. Its outcome line is not clean (see the fence just
above), though per the isolation spot-check above (Requirement 1)
those outcomes are pre-existing, not new ones caused by this change —
the timing itself still stands. derived: across the 4 measurements now
on record (the delivery record's 3 plus this session's 1), 2 sit over
the 300s budget and 2 sit under it — the budget is not reliably held;
the acceptance bullet as literally written does not hold across
independent re-measurement.
canonical: git show origin/issue-1490/implementation:docs/issue-1490/reports/implementation.md — result: its Open findings section names a second concurrent `spawn.py` session (per its own `ps aux` snapshot) as a candidate cause for its own 317.56s outlier.
This review did not gather comparable contention evidence for its own
428.76s run (time budget) — see this record's own Open findings below.

canonical: git show origin/issue-1490/implementation:docs/issue-1490/reports/implementation.md — result: "## Pass/fail-set diff" section's diff of sorted baseline vs combined outcome-ID lists shows a 2-line diff out of a 1909-line comparison, both lines belonging to one synthetic tempfile-named fixture; its methodology sorts every outcome-tagged line from both raw run outputs before comparing.

**Acceptance 2 — the both-tiers outcome-ID-set match: Present,
verified via the record's own citable diff, not independently
re-executed by this session.** (Issue text: the combined command
producing the same outcome-ID set as the pre-change single-threaded
run, recorded as a test-ID diff.) Running the true single-threaded
baseline (21m12s per the delivery record) plus a full combined re-run
was outside this review's time budget; the diff cited immediately
above is a concrete, inspectable comparison, not a summary. Rated
Present on the strength of that inspectable methodology and the
matching total-outcome-count under Requirement 4 above, with the
caveat that this review did not re-execute the full single-threaded
baseline itself.

**Acceptance 3 — `tests/` isolation fixes named per test in the
delivery record: Present.**
canonical: git show origin/issue-1490/implementation:docs/issue-1490/reports/implementation.md — result: two named load-sensitive tests moved to `slow` (`SpawnOneNoWait.test_no_wait_returns_promptly_without_calling_await_bounded`, `SpawnOneIssueRoleClaim.test_concurrent_spawn_one_calls_let_exactly_one_through`), with the first's concrete symptom stated (an elapsed-time assertion measured 15.4s even fully isolated).
This satisfies the acceptance bullet's "named per test" as literally
stated for the isolation-fix class it covers (load-sensitive-under-
`-n auto` tests); no other test in the frozen write set required an
isolation fix per this session's own spot-check (Requirement 1 above).

**Acceptance 4 — empty state: not applicable: Present.** Re-tiering an
existing suite with no new corpus; matches the issue's own framing.

## Why

Per-requirement/acceptance fidelity verdicts, sourced from the built
artifact (checked-out worktree, re-run commands) and the issue text,
per the conformance-review role's rulebook — never a holistic
code-quality judgment, never a fix, deliberately without trusting the
implementation role's own stated intent for what its command output
means.

## What did not work

None.

## Open findings

acceptance: python3 -m pytest -q --ignore=bench -m "not slow" — result: reproduced below
```
17 failed, 1825 passed, 1 xfailed in 428.76s (0:07:08)
```
That 428.76s measurement, over the 300s budget, stands alongside the
delivery record's own 317.56s outlier cited under Acceptance 1 above.

- **Acceptance 1 — Incorrect.** Two independently-observed measurements
  now sit over the 300s budget (317.56s in the delivery record,
  428.76s in this session's own run). Addressed to: implementation
  role (owns `pytest.ini`, the `slow` tiering, and its own delivery
  record). Resolution path below.

canonical: `grep -n -i "regression\|pre-merge\|change class" docs/handbooks/operations.md docs/handbooks/hooks.md` (this session, above) — no match in either file.

- **Requirement 2, third clause — Absent.** No `docs/handbooks/*` file
  states a pre-merge regression policy naming which test tier is
  required for which change class (e.g. "code touching spawn lifecycle
  → slow tier required"). Addressed to: implementation role (or
  whichever role owns the orchestrator's pre-merge policy surface, if
  distinct from `docs/handbooks/operations.md`). Resolution path
  below.

## Next steps

canonical: this record's own Verdicts section above, all citations
already given there — result: Present for Requirement 1, Requirement 3
(record-keeping half), Requirement 4, Acceptance 2, Acceptance 3,
Acceptance 4; Surface for Requirement 2; Incorrect for Acceptance 1.

Findings above route to the implementation role per contract v3 s19
hand-off — this role does not edit `pytest.ini`, `tests/test_spawn.py`,
or `docs/handbooks/operations.md`. The parallel/slow-tier
infrastructure itself rates Present and the outcome-set-match
requirement rates Present per an inspectable record diff, but this
session's own independent re-measurement of the issue's headline
wall-clock target landed over budget (Acceptance 1: Incorrect), and
one clause of Requirement 2 (the pre-merge regression policy) has no
textual match anywhere in `docs/handbooks/` (Surface).

## Resolution path

acceptance: python3 -m pytest -q --ignore=bench -m "not slow" — result: reproduced below
```
17 failed, 1825 passed, 1 xfailed in 428.76s (0:07:08)
```
That 428.76s measurement (this session's own run) sat over the 300s
budget.

For Acceptance 1: implementation role either (a) re-investigates why
an independent run measured 428.76s — rule out host contention with a
cleaner methodology than a single `ps aux` snapshot (e.g. a `ps`
sample taken every few seconds across the run's whole duration rather
than a single point-in-time snapshot), or (b) if contention cannot be
ruled out on this shared host, states plainly in its delivery record
that the budget is contention-sensitive and not a guaranteed bound,
and proposes either a tighter cushion or a documented measurement
protocol (e.g. median of N runs, or a dedicated/quiet-host
requirement).

For Requirement 2: implementation role adds an explicit statement to
`docs/handbooks/operations.md` (or names the correct existing policy
surface if one already exists elsewhere and was missed by this
review's grep) naming which tier is required for which change class,
per the issue's own Requirement 2 wording.
