---
issue: 3061
role: adversarial-review+test-depth-audit+silent-failure-audit-626070ae
author: adversarial-review+test-depth-audit+silent-failure-audit-626070ae
skills: adversarial-review (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true  # eighth independent verification of PR #3087's deliverable, this time of round 6's repair (PR #3209's record) closing PR #3207's two holes
code_under_review: 3312d19c4806b784a3c4df73f0c5a828a79e10e6
type: defect-verification-record
breaking: false
verdict: Round 6 does not close hole 2. `_check_no_surrogates()`'s
  recursive walk correctly reaches every position round 6's own record
  named (unlisted key value, dict key, nested-under-non-named-field,
  50/900-level-deep nesting) but `isinstance(value, list)` silently
  excludes Python tuples — a surrogate inside a tuple value skips the
  walk entirely and reproduces the identical, original uncaught
  `UnicodeEncodeError` that truncates the state file (303 bytes to 0),
  the exact data-destroying crash hole 2 exists to prevent. The walk is
  also not robust to its own inputs: a self-referential dict/list and
  nesting beyond Python's default recursion depth both crash with an
  uncaught `RecursionError`, and a `bytes`/`set` field value passes
  validation silently, then crashes `grant()` with an uncaught
  `TypeError` at the JSON-serialization step. Grade: Incorrect. Hole 3
  (per-episode completeness) grades Present — all four task-named log
  constructions, independently built, report exactly the right episodes
  indeterminate, and `format_audit()` names each one. Cost of both
  fixes is quantified and not slow enough to matter on realistic input
  sizes. The 22 pre-existing failures are byte-identical by name at
  round 6's tip, and the five previously-Present properties plus the
  full 87-test delegation suite are re-confirmed. See "What was done"
  below for the full per-item evidence.
loop_state: verified
upstream:
  - path: PR https://github.com/tokenmaxxxer/on-the-record/pull/3087 (code
      on its own branch through commit 3312d19c, round 6's repair)
    sha: 3312d19c4806b784a3c4df73f0c5a828a79e10e6
  - path: docs/issue-3061/reports/adversarial-review+test-depth-audit+silent-failure-audit-db36701b.md (PR #3207, seventh independent verification — the round this repair responds to)
    sha: same-commit
  - path: docs/issue-3061/reports/implementation-blueprint+silent-failure-audit+test-derivation-0c2cc205.md (PR #3209, round 6's own repair record)
    sha: same-commit
---

# issue-3061 — adversarial-review+test-depth-audit+silent-failure-audit-626070ae record

## What was done

canonical: `3312d19c:delegation_state.py` (round 6's tip, commits
`c7b2fc31` fix + `3312d19c` tests, on top of `6f600355`) and
`docs/issue-3061/reports/adversarial-review+test-depth-audit+silent-failure-audit-db36701b.md`
(PR #3207's seventh verification) and
`docs/issue-3061/reports/implementation-blueprint+silent-failure-audit+test-derivation-0c2cc205.md`
(PR #3209's round-6 repair record), both read in full before this
session's own reproductions.

Eighth independent, builder-blind verification against issue #3061 — of
round 6's repair (PR #3209's record; two commits pushed directly onto PR
#3087's own branch: `c7b2fc31` the fix, `3312d19c` the regression tests,
on top of `6f600355`), which claims to close the two holes PR #3207's
seventh verification found in round 5: UTF-8 validation covering only
the three named manifest fields (`tool`/`resource`/`repo`), and
`audit()`'s truncated-episode check being computed once per log file
instead of per episode.

Every finding below was reproduced independently in an isolated `git
worktree` checkout of PR #3087's branch at `3312d19c` (never edited,
never merged, removed at session end via `git worktree remove --force`)
via small, self-contained Python reproduction scripts run directly
against `3312d19c:delegation_state.py`'s public functions (`grant()`,
`audit()`, `format_audit()`, `_validate_manifest()`) — not by reading
round 6's diff and trusting its own test suite. Skills `adversarial-review`,
`silent-failure-audit`, and `test-depth-audit` were invoked (Skill tool,
this session, this turn) before any reproduction was written.

### Item 1 — recursive UTF-8 walk: reach — grade: Present (in isolation)

canonical: `3312d19c:delegation_state.py:256-288` (`_check_no_surrogates()`)
recurses into `dict` values/keys and `list` elements at every depth,
raising `MalformedManifestError` the moment any string anywhere fails
`_is_utf8_safe()`.

derived: python3 reproduction calling `grant()` in an isolated tmp dir,
isolated worktree at `3312d19c` (this session, this turn), planting a
lone surrogate in four positions round 6's own record does not name —
list nested in dict nested in list, a key several levels down, a value
whose sibling keys are all valid, and structures 50 and 900 levels
deep — result:
```
list-in-dict-in-list: MalformedManifestError raised OK
list-in-dict-in-list: disk unchanged = True
key-several-levels-down: MalformedManifestError raised OK
key-several-levels-down: disk unchanged = True
sibling-keys-valid: MalformedManifestError raised OK
sibling-keys-valid: disk unchanged = True
deep-50-levels: MalformedManifestError raised OK
deep-50-levels: disk unchanged = True
deep-900-levels: MalformedManifestError raised OK
deep-900-levels: disk unchanged = True
```
All five reach cases the task asked to plant are caught cleanly, with
zero disk mutation on rejection — no depth limit up to 900 levels
(Python's default recursion limit is 1000).

### Item 1 — recursive UTF-8 walk: robustness — grade: Incorrect

**Finding A (critical, data-destroying): tuples bypass the walk entirely.**
`3312d19c:delegation_state.py:280-284`'s `elif isinstance(value, list):`
branch is the only place `_check_no_surrogates()` descends into a
sequence. `isinstance(x, list)` is `False` for a Python `tuple` — a
manifest entry value that is a tuple is silently skipped by the walk
(it matches none of the `str`/`dict`/`list` branches, so nothing
happens), even though the module's own JSON serializer
(`json.dumps()`, called inside `grant()`) serializes a tuple exactly
like a list — the value still reaches the UTF-8-encoding write step.

derived: python3 reproduction — (1) `grant()` a genuinely valid,
in-force delegation; (2) `grant()` again with a surrogate inside a
tuple value (`manifest=[{"tool": "Bash", "resource": "git *", "meta":
("bad\ud800",)}]`); (3) inspect the state file after, isolated
worktree at `3312d19c` (this session, this turn) — result:
```
tuple-with-surrogate: before=303B after=0B unchanged=False ::
  UnicodeEncodeError (crash): 'utf-8' codec can't encode character
  '\ud800' in position 294: surrogates not allowed
```
This is the identical uncaught `UnicodeEncodeError` at the identical
`path.write_text(..., encoding="utf-8")` call site that hole 2 was
opened to close, reproduced through a Python type the recursive walk's
own `isinstance` checks do not cover — and it destroys the pre-existing
303-byte valid delegation exactly as PR #3207's hole-2 reproduction
against round 5 did. A tuple is not a contrived attack shape: it is the
ordinary Python idiom for an immutable sequence, plausible from any
caller building a manifest entry programmatically via `grant(...,
manifest=[...])` (the module's own documented hand-authoring surface,
`3312d19c:delegation_state.py:186-189`), not merely a malicious JSON
payload — JSON parsing itself never produces a tuple, so this gap is
reachable only through the direct Python API, but that API is the
one this module's own docs tell authors to use.

**Finding B: the walk crashes on its own malformed input.**

derived: python3 reproduction, isolated worktree at `3312d19c` (this
session, this turn) — result:
```
self-referential-dict: before=303B after=303B unchanged=True ::
  RecursionError (crash)
deep-2000-with-surrogate: before=303B after=303B unchanged=True ::
  RecursionError (crash)
```
A self-referential dict (`d["loop"] = d`) or a list containing itself,
and a manifest entry nested past Python's default recursion depth
(2000 levels tried, limit is 1000), both crash `_check_no_surrogates()`
itself with an uncaught `RecursionError` — before `path.write_text()`
is ever reached, so no disk mutation occurs in these two cases (`before
== after`, confirmed above), but `grant()` still raises an exception no
caller of this module catches specifically, the same "uncaught crash on
malformed input" shape the prior hole-2 repair work exists to close,
one level up: the fix for "a string that crashes the write path"
introduces "a structure that crashes the validator."

**Finding C: unanticipated value types silently pass validation, then
crash later for an unrelated reason.**

derived: python3 reproduction, isolated worktree at `3312d19c` (this
session, this turn) — result:
```
bytes-value: before=303B after=303B unchanged=True ::
  TypeError (crash): Object of type bytes is not JSON serializable
set-value: before=303B after=303B unchanged=True ::
  TypeError (crash): Object of type set is not JSON serializable
```
Neither `bytes` nor `set` matches `_check_no_surrogates()`'s `str`/
`dict`/`list` branches, so validation raises nothing — `grant()`
proceeds past `_validate_manifest()` believing the entry is clean, then
crashes with an uncaught `TypeError` inside `json.dumps()`, which is
evaluated as an argument to `path.write_text()` and therefore runs
before the file is opened for writing — no disk mutation in this
case (`before == after`, confirmed above) — but the caller sees a
confusing, unrelated `TypeError` from a completely different subsystem
(the JSON encoder) instead of the `MalformedManifestError` the
validation layer exists to produce, and the state file was never
actually touched only by accident of Python's argument-evaluation
order, not by any check that named these types unsupported.

canonical: `3312d19c:test/test_delegation_state.py:709-740`
(`MalformedManifestTest.MALFORMED_SHAPES`) — the shape table this
round's own test suite exercises contains no tuple value, no
self-referential structure, and no `bytes`/`set` field value; every
entry uses only `dict`/`list`/`str`/`int`/`None` shapes, per direct
inspection of the shape table's literal contents this session, this
turn. Per `test-depth-audit`, this is a Happy-Path-Only gap in the
shape table relative to Python's own type surface, not a coverage gap
the task manufactured — the round's own test-derivation section
(`docs/issue-3061/reports/implementation-blueprint+silent-failure-audit+test-derivation-0c2cc205.md`,
"Test derivation") partitions by *position within the entry structure*
but never by *value type*, so this class of gap was structurally
outside what that partitioning could have found.

**Grade rationale.** Incorrect: round 6's own commit-message and record
claim ("UTF-8 validation now walks the entire entry structure
recursively... every dict key, every dict value, every list element, at
every depth") is falsified by Finding A, which reproduces the identical
named defect (an uncaught `UnicodeEncodeError` that truncates the state
file) hole 2 was opened to close. Findings B and C are a second,
related defect — the recursive walk itself is not robust to malformed
or type-unanticipated input, which is "the same failure it was written
to prevent," per this round's own task framing, one level removed from
where the string-position walk succeeds.

### Item 2 — per-episode completeness — grade: Present

canonical: `3312d19c:delegation_state.py:822,847-849` —
`episode_reached_completion = any(event_index < ri < boundary for ri in
result_indices)` is computed independently for every episode
`audit()` reports on, where `result_indices` is every `result` event's
index in the whole log.

derived: python3 reproduction, four independently-constructed synthetic
session logs (different event text/timing than PR #3207's or round 6's
own fixtures, built directly against `audit()`/`format_audit()`),
isolated worktree at `3312d19c` (this session, this turn):

```
A: two complete + truncated third
  flagged=2 (episode-alpha, episode-beta), indeterminate=1 (episode-gamma)
B: truncated middle + complete last
  flagged=1 (episode-beta), indeterminate=1 (episode-alpha)
C: all episodes complete (three)
  flagged=3, indeterminate=0
D: no episodes at all (empty log)
  flagged=0, indeterminate=0, no crash
```
Case A (two genuine completions before a truncated third) and case B
(a truncated middle before a genuine completion) each report
indeterminate for exactly the truncated episode, never the complete
ones — the failure PR #3207 reproduced against round 5 (an earlier or
later completion incorrectly vouching for an unrelated episode) does
not reproduce here. Case C (every episode complete) flags all of them
cleanly, confirming the per-episode check has not made `audit()`
over-cautious. Case D (no episodes) returns a coherent empty result
with no crash, a construction neither PR #3207's nor round 6's own
test suite names.

derived: `format_audit()` output for case A, isolated worktree at
`3312d19c` (this session, this turn) — result:
```
2 turn(s) since 2026-09-01 asked for authority a recorded delegation already covered (scanned 1 session log(s)):
  - ...episode-alpha: proceed?... (next action Bash:'git status' already in the manifest)
  - ...episode-beta: proceed?... (next action Bash:'git diff' already in the manifest)
1 episode(s) could not be seen to their end (session log truncated or still running) — reported indeterminate, not a clean verdict:
  - ...episode-gamma: proceed?...
```
Confirms the output names which specific episode(s) could not be seen
to the end, by timestamp, log path, and text excerpt — not folded
silently into the flagged-or-not count, which was the point of hole 3.

**Grade rationale.** Present: all four task-named constructions behave
correctly on independently-built inputs, and the naming requirement is
met.

### Item 3 — cost of both fixes — grade: Present (quantified, not slow enough to matter)

derived: python3 `time.perf_counter()` benchmarks, isolated worktree at
`3312d19c` (this session, this turn) — manifest validation on a
realistic 50-entry manifest (each entry carrying `tool`/`resource`/
`repo` plus a few extra fields, matching the module's own
hand-authoring surface): `0.125 ms/call`. Scaled to unrealistic sizes
to find the ceiling: `500` entries `1.227 ms/call`, `5000` entries
`16.535 ms/call`. `grant()` end-to-end with a 20-entry, 3-level-nested
manifest: `0.403 ms/call`. Recursive validation is not slow enough to
matter at any manifest size a real delegation would plausibly carry
(realistic manifests in this repo's own fixtures run a handful to a
few dozen entries).

derived: python3 benchmark of `audit()` against synthetic session logs
of increasing episode count, isolated worktree at `3312d19c` (this
session, this turn):
```
n_episodes=50   (150 events)  -> 8.88 ms
n_episodes=500  (1500 events) -> 17.75 ms
n_episodes=2000 (6000 events) -> 164.78 ms
n_episodes=5000 (15000 events)-> 965.45 ms
```
derived: identical benchmark against round 5's tip (`6f600355`, before
this round's per-episode change), isolated worktree at
`/tmp/pr3087-round5` (this session, this turn):
```
n_episodes=2000 (6000 events) -> 121.30 ms
n_episodes=5000 (15000 events)-> 674.94 ms
```
derived: `(164.78 - 121.30) / 121.30 * 100` = `~36%` overhead at 2000
episodes; `(965.45 - 674.94) / 674.94 * 100` = `~43%` overhead at 5000
episodes — round 6 adds a real, measurable tax over round 5 at equal
episode counts, but a constant-factor one, not a change in asymptotic
complexity: `audit()`'s per-episode cost was already superlinear before
round 6 (round 5's own numbers roughly square when episode count
scales by 2.5x — 121.30ms to 674.94ms is a 5.6x increase for a 2.5x
input increase — consistent with the pre-existing `episode = [tu for
tu in tool_uses if event_index < tu["index"] < boundary]` list
comprehension re-scanning `tool_uses` per episode, unchanged by this
round). At realistic scale — an audit run covering a day or a handful
of sessions, tens to low hundreds of episodes, per this repo's own
fixture conventions — both round 5's and round 6's costs are
single-digit milliseconds and not slow enough to matter. The
quadratic-ish scaling only becomes visible in the thousands-of-episodes
range, which round 6 did not introduce and did not make asymptotically
worse.

**Grade rationale.** Present: both costs are answered with concrete
numbers rather than an unquantified "should be fine"; neither is slow
enough to matter at realistic input sizes, and the pre-existing
scaling behavior of `audit()` (not round 6's own defect) is disclosed
rather than silently absorbed into "fast enough."

### Item 4 — regression count — grade: Present

derived: `python3 -m pytest -q -m "not slow"` inside an isolated
worktree at `3312d19c` (round 6's tip), this session, this turn —
result: `22 failed, 1034 passed, 3 xfailed, 2 warnings`.

derived: `python3 -m pytest -q -m "not slow"` inside a separate isolated
worktree at `6f600355` (round 5's tip), this session, this turn —
result: `22 failed, 1032 passed, 3 xfailed, 2 warnings`.

derived: `diff` of the two independently captured, sorted `FAILED` line
sets, this session, this turn — result: no output (`IDENTICAL`), 22
lines in each file.

**Grade rationale.** Present: the 22 pre-existing failures are
byte-identical by name at round 6's tip; round 6 introduces zero new
failures and fixes none of the pre-existing ones, matching round 6's
own record.

### Item 5 — spot-check of five previously-Present properties, and the full delegation suite — grade: Present

derived: `grep -n "_is_redundant_ask\|_REDUNDANT_ASK" delegation_state.py`
inside the isolated worktree at `3312d19c`, this session, this turn —
result: no match. `is_covered()` (`3312d19c:delegation_state.py:558`)
remains the sole classifier — no lexical classifier re-introduced.

derived: `python3 -m pytest test/test_delegation_state.py::RegressionFailureCasesTest -q`
inside the isolated worktree at `3312d19c`, this session, this turn —
result: `4 passed` — the four real historical misclassifications remain
correctly un-flagged.

canonical: `3312d19c:delegation_state.py:621-641` (`_extract_action()`)
reads only `tool_use.get("input")`'s own fields (`command`/`file_path`/
`path`/`url`/`description`), never the ask's own text — unchanged from
round 5, confirmed by direct code inspection this session, this turn.

derived: `python3 -m pytest test/test_delegation_state.py -k "ControlCharacter or single_command" -q`
inside the isolated worktree at `3312d19c`, this session, this turn —
result: `11 passed` — the single-command control-character detection
(round 5's hole-1 fix, graded Surface not Present by PR #3207 for its
undisclosed over-refusal cost, untouched this round) still functions;
this session did not re-derive the over-refusal cost since round 6's
diff does not touch that code path.

derived: `python3 -m pytest test/test_delegation_state.py::TruncatedLogIndeterminateTest -q`
inside the isolated worktree at `3312d19c`, this session, this turn —
result: `5 passed` — round 5's single-episode truncation handling
still holds under round 6's per-episode rewrite.

derived: `python3 -m pytest test/test_delegation_state.py -q` inside the
isolated worktree at `3312d19c`, this session, this turn — result:
`87 passed` — the full delegation-state suite passes in full at round
6's tip, matching round 6's own record.

**Grade rationale.** Present: all five previously-Present properties
re-confirmed independently, and the full suite passes.

## Why

canonical: PR #3207's record
(`docs/issue-3061/reports/adversarial-review+test-depth-audit+silent-failure-audit-db36701b.md`)
and PR #3209's round 6 record
(`docs/issue-3061/reports/implementation-blueprint+silent-failure-audit+test-derivation-0c2cc205.md`),
both read in full before this session's own reproductions.

Builder-blind, structurally independent verification (`adversarial-review`
skill, invoked this session): read only round 6's diff and its own
claims, then constructed inputs round 6's test suite does not contain
— a Python type (`tuple`) its own `isinstance` checks exclude, and
structural shapes (self-reference, over-depth nesting, `bytes`/`set`
values) no equivalence partition in its own test-derivation section
covers — run directly against the delivered code in an isolated
checkout, rather than trusting the passing 87-test suite as proof of
the claimed "walks the entire manifest entry recursively" property.
`silent-failure-audit` (invoked this session) framed Findings B and C
(validation silently lets an unanticipated type through, then a
different subsystem crashes uncaught for an unrelated reason) as the
same silently-absorbed-then-crashes-elsewhere shape this issue has
repeatedly found. `test-depth-audit` (invoked this session) located
the root cause of why round 6's own 87-test suite did not catch
Finding A: `MALFORMED_SHAPES`'s equivalence partition is entirely over
string *position*, never over Python value *type*, so a defect
reachable only through an unpartitioned type was structurally invisible
to it. This is the same standard the prior seven verification rounds
in this issue's history have applied, since a builder session grading
its own diff has repeatedly (rounds 1-6) missed exactly this class of
gap.

## Upstream basis

- PR #3087 (`https://github.com/tokenmaxxxer/on-the-record/pull/3087`),
  code at `3312d19c4806b784a3c4df73f0c5a828a79e10e6` (round 6's tip:
  `c7b2fc31` the fix, `3312d19c` the regression tests, on top of
  `6f600355`).
- `docs/issue-3061/reports/adversarial-review+test-depth-audit+silent-failure-audit-db36701b.md`
  (PR #3207, seventh independent verification, the round this repair
  responds to) — `same-commit`.
- `docs/issue-3061/reports/implementation-blueprint+silent-failure-audit+test-derivation-0c2cc205.md`
  (PR #3209, round 6's own repair record) — `same-commit`.

## Open findings

canonical: reproductions above, this session, this turn —
`3312d19c:delegation_state.py:256-288` (`_check_no_surrogates()`,
Finding A's `isinstance(value, list)` gap and Findings B/C's crash
surface) is the one code location these resolution paths change.

- Finding A (Incorrect, critical — data-destroying). resolution path:
  add `tuple` (and any other sequence type this module chooses to
  support, e.g. by checking `isinstance(value, (list, tuple))`) to the
  sequence branch of `_check_no_surrogates()`; add a
  `surrogate_in_tuple_value` shape to `MALFORMED_SHAPES` so the
  regression is pinned. Not fixed by this session — verification-only
  scope, no edits to PR #3087.
- Finding B (crash, not data-destroying). resolution path: either wrap
  the recursive walk to catch `RecursionError` and re-raise as
  `MalformedManifestError` (turning an uncaught interpreter-level
  crash into the same loud, typed error the rest of this validation
  layer already produces), or convert `_check_no_surrogates()` to an
  explicit-stack iterative walk with a cycle-detection set (`id()` of
  visited containers) and a depth cap, which closes both the
  self-reference and the over-depth case at once. Not fixed by this
  session.
- Finding C (crash, not data-destroying, but a confusing error surface).
  resolution path: `_check_no_surrogates()` should raise
  `MalformedManifestError` for any value that is not one of
  `str`/`dict`/`list`/`int`/`float`/`bool`/`None` (an explicit
  allowlist of JSON-representable types), rather than silently passing
  it through to fail later, opaquely, inside `json.dumps()`. Not fixed
  by this session.
- None of the above were edited in PR #3087; this record is
  verification-only, per the task's explicit instruction not to edit
  the subject PR. resolution path for all three: a subsequent repair
  round on PR #3087, re-checked by a ninth independent verification
  against fresh, independently-constructed inputs rather than this
  round's own citations.

## Next steps

None from this session — verification-only, `loop_state` set to
`verified` as the terminal state for this record kind.

## What did not work

None — no approach was tried and discarded during this session; every
reproduction script was run once, its output recorded, and the next
item's script written directly from the task's own framing.

skill-verdict: adversarial-review — applied: invoked; structured this entire session as builder-blind, evidence-cited reproduction against round 6's delivered code rather than its own claims, per the "What was done" and "Why" sections above
skill-verdict: silent-failure-audit — applied: invoked; classified Findings B and C's crash sites (validation silently lets an unanticipated type/structure through, then a different subsystem crashes uncaught) using the audit's trace-forward method, in the "Item 1" and "Why" sections above
skill-verdict: test-depth-audit — applied: invoked; located `MALFORMED_SHAPES`'s equivalence partition (string position only, never value type) as the structural reason round 6's own 87-test suite could not have caught Finding A, cited in "Item 1" and "Why" above
other mounted skills: not triggered
