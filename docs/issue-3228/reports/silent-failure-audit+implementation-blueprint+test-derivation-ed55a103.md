---
issue: 3228
role: silent-failure-audit+implementation-blueprint+test-derivation-ed55a103
author: silent-failure-audit+implementation-blueprint+test-derivation-ed55a103
skills: silent-failure-audit (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: scripts/lint/silent_failure.py, tests/test_issue_3228_silent_failure_lint.py, scripts/lint/fixtures/silent_failure/**
loop_state: complete
type: implementation
breaking: false
verdict: complete
upstream:
  - path: scripts/issue-3127/verify_preregistration.py
    sha: f722841fcf28c0e299713af2a8e69015a6eaf673
  - path: scripts/preflight/consumer_preconditions.py
    sha: f722841fcf28c0e299713af2a8e69015a6eaf673
  - path: delegation_state.py
    sha: f722841fcf28c0e299713af2a8e69015a6eaf673
  - path: scripts/consumer-path/verify_manipulation.py
    sha: f722841fcf28c0e299713af2a8e69015a6eaf673
  - path: on-the-record/hooks/amendment_channel.py
    sha: f722841fcf28c0e299713af2a8e69015a6eaf673
---

# issue-3228 — silent-failure-audit+implementation-blueprint+test-derivation record

## What was done

Delivered `scripts/lint/silent_failure.py` (a static AST lint), fixtures
under `scripts/lint/fixtures/silent_failure/`, and
`tests/test_issue_3228_silent_failure_lint.py`.

derived: `ls scripts/lint/fixtures/silent_failure/history_before/ | wc -l`
and the same command against `history_after/` — result: both
directories hold one file per site (site1_2, site3, site4, site5,
site6, site7).

**The seven defects, characterised.** Read all seven repairs in git
history. canonical: `git log --oneline -- scripts/issue-3127/verify_preregistration.py
scripts/preflight/consumer_preconditions.py delegation_state.py
scripts/consumer-path/ on-the-record/hooks/amendment_channel.py` output,
cross-referenced with `git show fb0bb0d3:scripts/issue-3127/verify_preregistration.py`.
Commits: fb0bb0d3 (original, pre-repair verify_preregistration.py),
1245c649/125cef42/8205c160 (its repairs, sites 3 and 4);
`da899f2a`'s own committed comments narrate sites 1 and 2 (canonical:
`scripts/preflight/consumer_preconditions.py:216-219` at sha
f722841fcf28c0e299713af2a8e69015a6eaf673, "an earlier version did" /
"Rule: absence and zero are different" — no separate pre-fix commit
exists, checked: `git log --oneline -- scripts/preflight/consumer_preconditions.py`
— result: only `da899f2a`/`0f6cb358`, both post-fix); `b6f5eb05`'s
comments narrate site 5 (canonical: `delegation_state.py:584-620` at
the same sha — checked: `git log --oneline -- delegation_state.py` —
result: only `b6f5eb05`, post-fix); `scripts/consumer-path/verify_manipulation.py`'s
module docstring narrates site 6 (canonical:
`scripts/consumer-path/verify_manipulation.py:17-26` at the same sha);
`638620e4`'s comments narrate site 7 (canonical:
`on-the-record/hooks/amendment_channel.py:213-259` at the same sha).
All seven share: an operation that can fail to observe something (a
syscall raises, a subprocess exits non-zero or hangs, a glob can't
prove non-chained, evidence could be self-written) has a code path
where "could not observe" and "observed, and it's fine" produce the
same reported value.

**Mechanism chosen and why**, weighed against the issue's four named
candidates (canonical: the issue body's own "Candidates worth
weighing" paragraph, read via `gh issue view 3228`):

| Candidate | Cost to author | Catches of the 7 | Rejected because |
|---|---|---|---|
| (a) subprocess timeout + returncode branch lint | Add `timeout=`, branch on `.returncode`, or `check=True` | sites 3, 4 | *(chosen)* |
| (b) boolean-coercion-of-numeric lint | Don't truth-test a value also used in a numeric comparison | site 2 | High false-positive risk repo-wide: `if x and x > 0:` on a dynamically-typed value is a common, often-correct idiom without static typing to confirm the value can legitimately be zero |
| (c) tri-state observed-true/false/not-observed convention | Every check function adopts a new sentinel type | all seven, in principle | Requires introducing a new type and migrating existing functions -- fixing sites, not making the shape unwritable |
| (d) fixture-derives-from-captured-payload check | Author captures a real payload once, tests load from it | site 7 | Narrow, and only checkable by convention (file exists, test loads it), not by verifying the fixture stays representative |

Chose (a), generalised into three AST rules in
`scripts/lint/silent_failure.py` — canonical:
`scripts/lint/silent_failure.py:15-30`'s own docstring names SF001
(missing timeout), SF002 (unchecked returncode), SF003 (a
returncode-guarded branch returning the same sentinel a
genuinely-different branch returns unconditionally). Rationale: purely
syntactic (no type inference, no dataflow across functions); the
domain generalises past the seven historical sites. derived: `git
ls-files '*.py' | xargs grep -l "subprocess\.\(run\|Popen\|check_output\|check_call\|getoutput\)"
2>/dev/null | wc -l` — result: 138. derived: `git ls-files '*.py' |
xargs grep -n "subprocess\.\(run\|Popen\|check_output\|check_call\|getoutput\)"
2>/dev/null | wc -l` — result: 617 (both commands run live this
session; that many existing subprocess call sites is why the mechanism
still has ongoing value beyond the two historical sites it was
motivated by). It also gives the cheapest, least ambiguous remedy an
author can act on. SF003 most directly operationalises the issue's own
diagnostic sentence — canonical: `git show fb0bb0d3:scripts/issue-3127/verify_preregistration.py`
lines 30-37, `_first_commit_for_path`'s real pre-repair code, shows the
git-failure branch (`if r.returncode != 0: return None`) and the
genuinely-empty branch (`return lines[0] if lines else None`)
returning the identical `None` literal one function apart.

**Proof against history.** `scripts/lint/fixtures/silent_failure/history_before/`
and `history_after/` hold matched pairs per site — the site-3/site-4
pair is the real fb0bb0d3/current code trimmed to the relevant
functions; the other four pairs are reconstructions built from the
comments each repair commit itself left (the same commits cited in
"The seven defects, characterised" above), since none of those four
fixes has a separate pre-fix commit to `git show`.

checked: `python3 scripts/lint/silent_failure.py --self-check` —
result (captured live this session, exit code 0):
```
PASS: history_before/site3_git_failure_conflation.py: pre-repair shape is flagged
PASS: history_before/site4_missing_timeout.py: pre-repair shape is flagged
PASS: history_before/site1_2_consumer_preconditions.py: outside this mechanism's documented scope (not a subprocess-observation defect)
PASS: history_before/site5_delegation_state_wildcard.py: outside this mechanism's documented scope (not a subprocess-observation defect)
PASS: history_before/site6_forgeable_evidence.py: outside this mechanism's documented scope (not a subprocess-observation defect)
PASS: history_before/site7_amendment_channel_fixture.py: outside this mechanism's documented scope (not a subprocess-observation defect)
PASS: history_after/site3_git_failure_conflation.py: repaired shape stays quiet
PASS: history_after/site4_missing_timeout.py: repaired shape stays quiet
PASS: history_after/site1_2_consumer_preconditions.py: repaired shape stays quiet
PASS: history_after/site5_delegation_state_wildcard.py: repaired shape stays quiet
PASS: history_after/site6_forgeable_evidence.py: repaired shape stays quiet
PASS: history_after/site7_amendment_channel_fixture.py: repaired shape stays quiet
PASS: a nonexistent/unreadable file reports an error, not a silent skip
PASS: a permission-denied file reports an error, not a silent skip
PASS: a file with a syntax error reports an error, not a silent skip
PASS: a target with zero subprocess call sites is distinguished from a clean pass
PASS: scanning that same zero-call-site target end-to-end exits nonzero
```
Every line above reads PASS; no FAIL line appears in that transcript.

**Verdict on catch rate**, derived directly from the transcript above:
only the site-3 and site-4 `history_before/` lines assert a finding
was raised ("pre-repair shape is flagged"); the other four
`history_before/` lines assert the opposite ("outside this mechanism's
documented scope"). So the mechanism catches the git-failure/empty
conflation and the missing-timeout defect, and does not catch the
statvfs-except-true defect, the zero-inode-falsy defect, the
fnmatch-wildcard defect, the forgeable-evidence defect, or the
fixture-realism defect — none of those five touch a subprocess call
site, which is this mechanism's entire domain. A single mechanism
covering every one of the seven would have to be candidate (c) (the
tri-state convention), at the price of a repo-wide migration this
issue explicitly says not to do.

**A precision gap found by actually running it, and how it was
resolved.** Running the lint over the real, current
`scripts/issue-3127/verify_preregistration.py` in full (not only the
two functions where sites 3 and 4 lived) surfaced SF003 candidates in
`_repo_owner_repo`/`_pr_merge_commit`/`_pr_commit_order`/
`_first_pr_commit_touching` (canonical:
`scripts/issue-3127/verify_preregistration.py:199-264` at sha
f722841fcf28c0e299713af2a8e69015a6eaf673). checked: `python3 -m pytest
tests/test_issue_3228_silent_failure_lint.py -q` before the fix below
— result (captured live this session):
```
FAILED tests/test_issue_3228_silent_failure_lint.py::test_real_repaired_files_stay_quiet
AssertionError: scripts/issue-3127/verify_preregistration.py should be quiet, got:
[...:217: [SF003] the returncode-failure branch at line 218 returns Constant(value=None),
 the same value line 222 returns for a genuinely different, non-failure reason...,
 ...:235: [SF003] ... line 236 ... line 240 ...]
```
Those four helpers' own docstrings state every failure mode (a `gh`
command failing, malformed JSON, an absent field) deliberately
collapses to the same `None`-means-"fail closed, exclude" signal,
always read identically by their one caller — a different, correct
pattern from the site-3 bug (a command failure conflated with a
genuinely-valid empty result that fed two different downstream
branches), but a per-function AST lint with no dataflow across
functions cannot see the caller and tell the two apart. Resolved by
adding the same `# silent-failure: allow <reason>` escape hatch
SF001/SF002 already had to SF003 too (canonical:
`scripts/lint/silent_failure.py:325-328`), and by scoping the
regression-guard test
(`tests/test_issue_3228_silent_failure_lint.py:145-168`,
`test_real_repaired_functions_stay_quiet`) to the two named functions
rather than annotating or rewriting the others, matching "do not fix
more sites." checked: `python3 -m pytest
tests/test_issue_3228_silent_failure_lint.py -q` after the fix —
result (captured live this session):
```
11 passed in 0.84s
```

**Must-not demonstrations**
(`scripts/lint/fixtures/silent_failure/{unreadable,syntax_error,no_subprocess}/`,
exercised by both the self-check transcript above and
`tests/test_issue_3228_silent_failure_lint.py:99-128`):
- A nonexistent path, and (when not running as root) a real
  permission-denied (`chmod 000`) file, both produce a reported
  `FileResult.error`, never a silent 0-findings pass — see the
  self-check transcript's "a nonexistent/unreadable file reports an
  error..." and "a permission-denied file reports an error..." lines
  above.
- A file with a real syntax error (an unclosed paren) produces a
  reported parse error, never a silent skip — see the transcript's "a
  file with a syntax error reports an error..." line above. canonical:
  this session's own `lint-test-on-edit.sh` hook independently
  confirmed the fixture is invalid Python at write time, reporting
  `SyntaxError: '(' was never closed` via its own `python3 -m
  py_compile` check.
- A target with zero subprocess call sites makes the CLI refuse to
  report a clean pass — see the transcript's final two lines above.
  checked: `python3 scripts/lint/silent_failure.py
  scripts/lint/fixtures/silent_failure/no_subprocess` — result
  (captured live this session):
```
no subprocess call sites found across the scanned target(s) -- refusing to report a clean pass (a scan that examined nothing is not distinguishable from a broken scan)
```
  exit code 1.

**Wiring** — repo already runs checks automatically in three places:
1. `pytest.ini` auto-discovers every `test_*.py` file repo-wide with no
   per-file registration step. checked: `python3
   gates/probe_full_suite_is_one_command.py` — result (captured live
   this session, exit code 0):
```
ok: every test file in the repo is accounted for by a known command. Running all of them still takes 5 commands, not one: `python3 -m pytest -q`; `bash tests/check-write-set-conflicts.test.sh`; `bash tests/claim-scan-preflight.test.sh`; `bash tests/run-orchestrate-tests.sh`; `bash tests/test_stop_gate.sh`
```
   `tests/test_issue_3228_silent_failure_lint.py` runs automatically
   inside that `python3 -m pytest -q` command, including a
   subprocess-level invocation of `--self-check`
   (`test_self_check_passes`), which is what wires the self-check into
   the automatically-run suite.
2. `gates/check_runner.py` re-executes this issue's own `## Acceptance`
   `check:` lines verbatim against the PR's head commit and scores/
   posts the result — canonical: `gates/check_runner.py:102-103`'s
   `INTERPRETERS` tuple contains `python3`, and both this issue's
   acceptance lines start with `python3`, so both classify `test` (not
   `judgment`) and actually run.
3. `on-the-record/hooks/lint-test-on-edit.sh` (a registered
   `PostToolUse` hook) ran `python3 -m py_compile` plus impacted tests
   on every `.py` file this session edited or wrote — canonical: this
   session's own transcript shows it fired after every Write/Edit to
   `scripts/lint/silent_failure.py` and
   `tests/test_issue_3228_silent_failure_lint.py`, at one point
   surfacing the `test_real_repaired_files_stay_quiet` failure quoted
   above before it was fixed. Authoring-time feedback, not a merge
   gate, but a fourth "runs automatically" surface worth naming since
   the issue's whole ask is authoring-time enforcement.

Deliberately not turned on: a full-repo scan gate. The precision-gap
paragraph above is the demonstration of why: scanning
`scripts/issue-3127/verify_preregistration.py` alone already surfaced
two additional SF003 candidates (lines 217 and 235, quoted above)
outside this issue's named sites; extending that scan to the 138 files
with a subprocess call (derived count above) would multiply that. The
issue's own framing is authoring-time, forward enforcement for new
sites, not a retroactive audit of pre-existing call sites, so the
regression guard is scoped to the two functions the seven defects
actually named.

**Portability.** Pure `ast`/`os`/`sys`/`dataclasses`/`pathlib` — no
`/proc`, no GNU-only flags, no shell scripts added. derived: `grep -rn
"/proc" scripts/lint/ tests/test_issue_3228_silent_failure_lint.py` —
result: no matches (empty output, run live this session).
`os.geteuid` (used only to skip the real-chmod self-check assertion
when running as root) is POSIX and present on both target platforms.

## Why

See "Mechanism chosen and why" above; folded into "What was done"
because the issue asked for the choice and its justification as one
deliverable.

**Test derivation note** (test-derivation skill). The two acceptance
`check:` lines and the must-not clause (canonical: the issue's own
`## Acceptance` section, read via `gh issue view 3228`) are the written
acceptance criteria. Given-When-Then per criterion:
- *pytest check*: Given the bundled fixtures, When `pytest
  tests/test_issue_3228_silent_failure_lint.py -q` runs, Then all
  cases pass. checked: `python3 -m pytest
  tests/test_issue_3228_silent_failure_lint.py -q` — result: the `11
  passed in 0.84s` block quoted above under "A precision gap found by
  actually running it".
- *self-check*: Given the same fixtures, When
  `scripts/lint/silent_failure.py --self-check` runs standalone, Then
  it exits 0 and every internal assertion reads PASS — the full
  transcript is quoted above under "Proof against history".
- *must-not*: Given an unreadable path and a syntax-error file, When
  scanned, Then each reports a distinct error, never a clean pass —
  the same self-check transcript quoted under "Proof against history"
  covers this.

Classified as Medium risk per the skill's own Step 3a (functional, not
safety/regulatory, but the lint's own correctness is the thing under
test) — routed to Given-When-Then scenarios per criterion plus a
decision-table-shaped fixture matrix (site by before/after by
caught/missed, the table under "Mechanism chosen and why" above), not
EP/BVA or state-transition testing (no ordered numeric input domain, no
lifecycle/mode to model). derived: `grep -c "^def test_"
tests/test_issue_3228_silent_failure_lint.py` — result: 11. Those
eleven test functions cover all three written criteria above
(self-check invocation, history before/after proof, must-not/
empty-state) plus the regression guard and allow-marker demonstration.
Residual: these tests do not establish that the mechanism will keep
catching future subprocess-shaped defects with call signatures other
than `subprocess.run`/`Popen`/`check_output`/`check_call` (e.g.
`os.system`, `asyncio.create_subprocess_exec`) — out of scope by
construction, named in `scripts/lint/silent_failure.py:70`'s
`_SUBPROCESS_ATTRS` set.

## What did not work

No approach was tried and discarded in this build. checked: `python3
-m pytest tests/test_issue_3228_silent_failure_lint.py -q` — result
(captured live this session):
```
11 passed in 0.84s
```
canonical: "A precision gap found by actually running it" above
narrates the one course-correction this build needed (SF003's false
positive on `_repo_owner_repo`-shaped helpers) together with the
before/after pytest output bracketing it.

## Upstream basis

- `scripts/issue-3127/verify_preregistration.py` (sha
  f722841fcf28c0e299713af2a8e69015a6eaf673) — sites 3 and 4, real
  before-code recovered from commit fb0bb0d3 (canonical: `git show
  fb0bb0d3:scripts/issue-3127/verify_preregistration.py`), real
  after-code is its current content at the sha above.
- `scripts/preflight/consumer_preconditions.py` (sha
  f722841fcf28c0e299713af2a8e69015a6eaf673) — sites 1 and 2, current
  content is real; pre-repair content reconstructed from
  `scripts/preflight/consumer_preconditions.py:210-227` at the sha
  above (comments `da899f2a` committed alongside the fix).
- `delegation_state.py` (sha f722841fcf28c0e299713af2a8e69015a6eaf673)
  — site 5, current content is real; pre-repair content reconstructed
  from `delegation_state.py:584-650` at the sha above (`b6f5eb05`'s
  comments).
- `scripts/consumer-path/verify_manipulation.py` (sha
  f722841fcf28c0e299713af2a8e69015a6eaf673) — site 6, current content
  is real; pre-repair content reconstructed from
  `scripts/consumer-path/verify_manipulation.py:1-34` at the sha above
  (its own module docstring).
- `on-the-record/hooks/amendment_channel.py` (sha
  f722841fcf28c0e299713af2a8e69015a6eaf673) — site 7, current content
  is real; pre-repair content reconstructed from
  `on-the-record/hooks/amendment_channel.py:727-807` at the sha above
  (`638620e4`'s comments).

## Open findings

None outstanding. checked: `python3 -m pytest
tests/test_issue_3228_silent_failure_lint.py -q` — result (captured
live this session):
```
11 passed in 0.84s
```
canonical: "A precision gap found by actually running it" above is the
only gap this build's own testing surfaced, and its resolution is
part of that same passing run.

## Next steps

checked: `python3 scripts/lint/silent_failure.py --self-check` —
result (captured live this session, exit code 0): transcript quoted in
full above under "Proof against history".

Optional future work, not undertaken here to avoid scope creep beyond
what issue #3228 asks: a full-repo audit reconciling the pre-existing
subprocess call sites (derived count under "Mechanism chosen and why"
above) against SF001-3; and/or a second mechanism (candidate (b) or
(d) from the table above) for the sites this one does not cover
(statvfs/zero-inode, fnmatch wildcard, forgeable evidence, fixture
realism), each as its own issue.

skill-verdict: silent-failure-audit — applied: invoked; used to
characterise all seven defects as catch/absorb/unreachable-shaped
(Step 1-2 of the skill's procedure) and to structure the "documented
miss" reasoning for the five uncaught sites in the fixtures and this
record's mechanism table.
skill-verdict: implementation-blueprint — applied: invoked; checked:
`python3 <skill-dir>/scripts/prep.py classify --single-file` — result
(run live this session):
```
VETO: single file, single concern, no callers -> no-structure
Reason: ceremony where it doesn't earn its keep — just write it correctly and note 'this is a script; flat is fine'.
```
confirming the flat single-file design already chosen for
`scripts/lint/silent_failure.py` rather than splitting it into a
package.
skill-verdict: test-derivation — applied: invoked; used to derive
Given-When-Then scenarios per acceptance criterion and the site by
before/after traceability matrix documented in the "Why" section
above, at Medium depth per the skill's own risk/complexity
classification.
