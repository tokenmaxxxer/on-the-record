# issue-2525 — conformance-review current-state survey

Subject reviewed: `issue-2525/implementation` branch, tip commit
`9f0239d16d864d60a624e2e4a3d0559f0453f5b8` ("issue-2525: retire the
plugin's own test suite"). derived: `git log --oneline -1
origin/issue-2525/implementation` — result: `9f0239d1 issue-2525: retire
the plugin's own test suite`. All findings below are Inspection-method
(file presence/absence, grep, `git ls-tree`/`git show` against that exact
sha) per conformance-review-verification-method-selection rule 1 — the
three acceptance bullets are all structural/static properties (a file
exists or doesn't, a string is registered or isn't), not behavior that
needs Demonstration. No suite run, per the issue's own "Do not run the
suite" non-goal.

Note on citation shape: `docs/issue-2525/reports/implementation.md`
(untracked on this branch; the implementation role's own record, quoted
repeatedly below) exists only on `issue-2525/implementation` at sha
`9f0239d1`. Every quote from it below is tagged `derived: git show
9f0239d1:docs/issue-2525/reports/implementation.md` (untracked on this
branch), re-run this session, and each occurrence of that path below
repeats the "(untracked on this branch)" note.

## Requirement extraction (per conformance-review-requirement-extraction)

canonical: `gh issue view 2525` (`Ask`, `Gates to delete with it`, and
`Acceptance` sections), read this session — quoted/paraphrased below.
The issue's three `check:` bullets bundle multiple obligations each;
split into one-obligation-per-line, dimension-tagged:

1. **R1a** [scope-boundary] The 225 suite files (`tests/*.py`,
   `gates/test_*.py`, `on-the-record/hooks/test_*.py`) are deleted.
2. **R1b** [scope-boundary] `pytest.ini` is deleted.
3. **R1c** [scope-boundary] The three named test-claim gates
   (`acceptance-command-real-run-guard.sh`,
   `live-fire-claim-real-run-guard.sh`, `live-fire-test-guard.sh`) plus
   any sibling test-claim gate the issue's "found by the same reading"
   clause would catch are deleted.
4. **R1d** [functional-behavior] Each deleted gate is unregistered from
   `pretooluse_dispatcher.py`'s `GATES` list.
5. **R1e** [functional-behavior] Each deleted gate is unregistered from
   `hooks.json`.
6. **R1f** [functional-behavior] The record lists what was removed.
   *(Empty-state clause, issue body: a gate already unregistered before
   this issue is a passing row once its script is deleted and that
   already-unregistered state is recorded — not required to be
   re-unregistered.)*
7. **R2** [error-handling] Grepping `*.sh`, `*.yml`, `*.ini`, `*.toml`
   repo-wide for `pytest` — every remaining hit is either removed or
   dead-reference-free (does not actually invoke the deleted suite).
8. **R3** [scope-boundary] The record states, plainly, in one place,
   that this removes machine-checking of the plugin's own behavior and
   that no replacement was built.

R1a-R1f share one dependency (rule 5, requirement-extraction): R1d/R1e
are only checkable per-gate once R1c's deletion (or its already-
unregistered exemption) is known for that gate.

## Findings (Inspection, all against sha `9f0239d1`)

### R1a — tests/*.py, gates/test_*.py, on-the-record/hooks/test_*.py

derived: `git ls-tree -r 9f0239d1 --name-only | grep -E
'^(tests/.*\.py$|gates/test_|on-the-record/hooks/test_)'` — result:
zero `tests/*.py` hits, zero `on-the-record/hooks/test_*.py` hits,
exactly one `gates/test_*.py` hit: `gates/test_tier_contract.py`.
canonical: `git show
9f0239d1:docs/issue-2525/reports/implementation.md` (untracked on this
branch), the "Exception, load-bearing" paragraph — states
`gates/test_tier_contract.py` is not a test, quoting its own docstring
("Sole live consumer: watchdog.py's standing_red_check") and
`watchdog.py:1339-1340` (`import test_tier_contract` / `return
test_tier_contract.load_contract(root)`). Matches the 225-file scope
with a justified, disclosed exception. **Looks satisfied.**

### R1b — pytest.ini

derived: `git ls-tree -r 9f0239d1 --name-only | grep -x pytest.ini` —
result: one hit, still present. derived: `git show 9f0239d1:pytest.ini`
— result: a live, non-empty pytest config (`python_functions`,
`norecursedirs`, `addopts = -n auto`, a `slow` marker). canonical: `git
show 9f0239d1:docs/issue-2525/reports/implementation.md` (untracked on
this branch), "Open findings" item 3 — states this was deliberately left
in place because it still governs `test/*.py` (singular, untouched —
outside this issue's `tests/*.py` scope), `ledger/test_decisions.py`,
and `on-the-record/monitors/test_poll_heartbeat.py`, confirmed present
by a `grep -rlE pytest` re-run cited in that same item. **Not deleted —
misses R1b as literally worded**, though the record discloses why.

### R1c — the three named gates

derived: `git ls-tree -r 9f0239d1 --name-only | grep -E
'acceptance-command-real-run-guard.sh|live-fire-claim-real-run-guard.sh|live-fire-test-guard.sh'`
— result: all three still present:
`on-the-record/hooks/acceptance-command-real-run-guard.sh`,
`on-the-record/hooks/live-fire-claim-real-run-guard.sh`,
`on-the-record/hooks/live-fire-test-guard.sh`. None deleted. canonical:
`git show 9f0239d1:docs/issue-2525/reports/implementation.md` (untracked
on this branch), "Mid-flight scope correction — not executed" section —
states a comment (`issuecomment-5421024494`) directing their deletion
arrived after the implementation session started and was "read too late
to act on, with no turn budget left to act on it," and that the rest of
that record reflects the original issue-body scope (keep both real-run
guards) which the comment supersedes. **Misses R1c entirely**,
self-disclosed as the top open finding in the upstream record.

### R1d/R1e — unregistration

derived: `git show 9f0239d1:on-the-record/hooks/pretooluse_dispatcher.py
| sed -n '270,290p'` — result: lines 277-282 still register both
`acceptance-command-real-run-guard.sh` and
`live-fire-claim-real-run-guard.sh` as `dict(script=..., ...)` entries in
`GATES`. `live-fire-test-guard.sh` does not appear anywhere in that file
(same grep, no hit) — consistent with `git show
9f0239d1:docs/issue-2525/reports/implementation.md` (untracked on this
branch)'s claim (canonical, "on-the-record/hooks/test_*.py"
capability-inventory bullet) that it was already demoted/unregistered
pre-#2525, per #2138/#2144. That part of R1d is a passing empty-state
row **for registration only**; the script itself is still on disk (R1c),
which the issue's own empty-state clause does not excuse ("delete the
script and record it as already-unregistered" — deletion is still
required). derived: `git show
9f0239d1:on-the-record/hooks/hooks.json | grep -E
'acceptance-command-real-run-guard|live-fire-claim-real-run-guard|live-fire-test-guard'`
— result: no hits — R1e is moot for registration but the same R1c gap
applies to all three scripts.

### R2 — dead-reference grep

derived: iterated every `*.sh`/`*.yml`/`*.ini`/`*.toml` path from `git
ls-tree -r 9f0239d1 --name-only` (200 candidates) through `git show
9f0239d1:<path> | grep -qi pytest` this session — 5 hits:
- `pytest.ini` — R1b, already counted above.
- `on-the-record/hooks/acceptance-command-real-run-guard.sh` — derived:
  `git show 9f0239d1:on-the-record/hooks/acceptance-command-real-run-guard.sh
  | grep -n -iE 'subprocess|pytest'` — result: `pytest` appears only in a
  comment (line 16, illustrative example text `acceptance: pytest` /
  `result: PASS`); the actual re-run logic (`subprocess.run(argv, ...)`,
  line 206) re-runs whatever `acceptance: <cmd>` was cited generically —
  dead-reference-free with respect to the deleted suite specifically, but
  this script is itself R1c scope (undeleted).
- `on-the-record/hooks/gate-registration-guard.sh` — derived: `git show
  9f0239d1:on-the-record/hooks/gate-registration-guard.sh | grep -n -i
  pytest -B2 -A2` — result: `pytest` appears only in a comment (lines
  8-10) naming `gates/test_boundary.py` / `gates/test_generated_paths.py`
  as prior art; both files are now deleted (R1a, confirmed above). Stale
  comment reference, not a code invocation — no runtime effect, but the
  comment itself now names nonexistent files.
- `on-the-record/hooks/live-fire-claim-real-run-guard.sh` — derived:
  `git show 9f0239d1:on-the-record/hooks/live-fire-claim-real-run-guard.sh
  | grep -n -iE 'subprocess|pytest'` — result: line 226,
  `subprocess.run(["python3", "-m", "pytest", "-q", test_path], ...)` —
  a live, executable invocation, where `test_path` (lines 195-247, read
  this session) is derived by convention as `gates/test_<stem>.py` /
  `on-the-record/hooks/test_<slug>.py` — paths that no longer exist for
  anything except `test_tier_contract.py` (R1a). This is not
  dead-reference-free: canonical: `git show
  9f0239d1:docs/issue-2525/reports/implementation.md` (untracked on this
  branch), "Guards still deny a fabricated result" section — states this
  guard "fails closed on every pre-existing gate/hook's `live-fire:`
  citation regardless of truth — the guard's own documented degrade
  path, not a malfunction." Confirms this is a live call whose target
  now vanished, not a crash, but still an active runtime dependency on
  the deleted suite's file layout.
- `tests/claim-scan-preflight.test.sh` — derived: `git show
  9f0239d1:tests/claim-scan-preflight.test.sh | grep -n -i pytest -B2
  -A2` — result: `pytest` appears inside a test fixture string literal
  (`body1='...python3 -m pytest test/foo.py'`, line 39) used as example
  input data for a hook test, not an actual invocation. Dead-reference-
  free. (This file itself is a `.sh`, not a `.py`, so it falls outside
  R1a's literal `tests/*.py` glob — untouched by this issue either way.)

Net: one of five hits (`live-fire-claim-real-run-guard.sh`) is a live,
non-dead-reference invocation of the deleted suite's path convention —
**R2 fails** on that hit until R1c's deletion of that script lands.

### R3 — plain single-place disclosure

canonical: `git show 9f0239d1:docs/issue-2525/reports/implementation.md`
(untracked on this branch) — read in full this session. It documents
extensive per-file OPEN GAP inventories across three separate
subsections (`gates/test_*.py`, `on-the-record/hooks/test_*.py`,
`tests/*.py`) under "Capability inventory (no silent drops)" — each gap
individually disclosed — but no single sentence in the record states the
summary disclosure the issue asks for ("this removes machine-checking of
the plugin's own behavior and no replacement was built"). derived: `git
show 9f0239d1:docs/issue-2525/reports/implementation.md | grep -niE 'no
replacement|not built|no new gate|machine.check'` — result: no hits. The
record's own frontmatter carries `verdict: fail` and its "Open findings"
section lists five open items, which substantively conveys
"incomplete," but that is not the same speech act as the plain
one-place disclosure R3 names. **Partial** — the substance is scattered
and inferrable across the OPEN GAP lists, not stated plainly in one
place as its own sentence.

## Scope note

This survey covers all three acceptance bullets in full (not a sample):
each bullet's checkable sub-items are enumerable and few (a handful of
named files/registrations), so conformance-review-sampling-derivation's
full-enumeration path applies and no separate sampling derivation is
needed (skill judged not-applicable for this issue — see proposal).

skill-verdict: conformance-review-requirement-extraction — applied:
invoked; used to split the issue's three `check:` bullets into R1a-R1f,
R2, R3 above, each dimension-tagged.
skill-verdict: conformance-review-verification-method-selection —
applied: invoked; used to select Inspection (file presence, grep,
registration lookup) as the method for every requirement above, all
structural/static properties per rule 1.
skill-verdict: conformance-review-verdict-assignment — applied: invoked;
guided the Present/Surface/Absent/Incorrect distinctions drafted above
(e.g. R1d's "passing empty-state row for registration only" vs R1c's
still-open gap is the Surface/Absent split from rule 1; formal verdicts
land in the phase-2 record after Approve).
skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; every finding above cites file/line plus the exact `git
show`/`git ls-tree`/`grep` command against sha `9f0239d1`, with the
implementation-record path's cross-branch nature noted at each
occurrence per the traceability rule on citing what was actually read.
skill-verdict: conformance-review-sampling-derivation — not-applicable:
full enumeration of all three acceptance bullets was feasible (few,
named files), so no sampling scope was needed.
skill-verdict: conformance-review-finding-record — not-applicable: this
is phase-1 survey material; formal verdicts get written into
`docs/issue-2525/reports/conformance-review.md` only in phase 2, after
human Approve (contract v3 s19 execution-surface gate).
skill-verdict: conformance-review-severity-classification —
not-applicable: this review's scope was not extended into risk-
weighting; only ordinary fidelity-checking against the issue's three
`check:` bullets was performed.
