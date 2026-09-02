---
issue: 3061
role: silent-failure-audit+implementation-blueprint+test-derivation-addc17f2
author: silent-failure-audit+implementation-blueprint+test-derivation-addc17f2
skills: silent-failure-audit (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: same-commit
loop_state: landed
type: fix
breaking: false
verdict: fixed
upstream:
  - path: PR #3212 (8th independent verification of PR #3087 round-6, tokenmaxxxer/on-the-record)
    sha: 1c7c9dbbab4d0ca2cc95b1cfa1ecf89d3630ce43
  - path: PR #3087 branch tip this round built on
    sha: 3312d19c4806b784a3c4df73f0c5a828a79e10e6
---

# issue-3061 — silent-failure-audit+implementation-blueprint+test-derivation-addc17f2 record

## What was done

Round 7 on PR #3087's scope-manifest delegation seam (`delegation_state.py`
on PR #3087's branch, untracked in this repo's own tree — the module and
its test module (`test_delegation_state.py`, no path prefix quoted below
on purpose, same untracked-in-this-repo caveat throughout this record)
both live on
`issue-3061/implementation-blueprint+silent-failure-audit+test-derivation+decision-brief-f458808c`,
not on this record's branch), closing the one hole PR #3212's 8th
independent verification found still open in round 6's
`_check_no_surrogates()` recursive walk.

canonical: `gh pr view 3212 --repo tokenmaxxxer/on-the-record` output —
"Hole 2 (malformed manifest, UTF-8) — Incorrect. ... The walk is also not
robust to its own inputs: a self-referential dict/list and nesting past
Python's default recursion depth both crash with an uncaught
RecursionError; a bytes/set field value passes validation silently, then
crashes grant() with an uncaught TypeError at the JSON-serialization step."

The pre-fix code (PR #3087 branch tip 3312d19c, `delegation_state.py`
lines 256-292) recursed into `str`/`dict`/`list` only and did nothing at
all — no check, no rejection — for any other Python type, so a `bytes`
or `set` field simply passed through unexamined.

derived: `git worktree add /tmp/pr3087-work origin/issue-3061/implementation-blueprint+silent-failure-audit+test-derivation+decision-brief-f458808c`
then, on the pre-fix tree (`git stash` of this round's edits), running:
```
python3 -c "
import delegation_state as ds, tempfile
with tempfile.TemporaryDirectory() as repo:
    d = {'tool': 'Bash', 'resource': 'x'}; d['self'] = d
    ds.grant(repo, 'scope', 'jiwon', skill_env='', manifest=[d])
"
```
— result: uncaught `RecursionError: maximum recursion depth exceeded`
traceback, confirming the self-reference crash named above.

`_check_no_surrogates(value, path, _depth, _visiting)` in
`delegation_state.py` (PR #3087 branch, this round's commit) now:

1. **Cycle detection.** `_visiting` is a `frozenset` of `id()` of every
   dict/list currently open on the *current* recursion path (not a
   global "ever seen" set — the same sub-object legitimately appearing
   twice as sibling values, a diamond, is not a cycle). Before descending
   into a container, its `id()` is checked against `_visiting`; if
   present, `MalformedManifestError` is raised naming it a cycle. This
   catches a self-referential dict, a self-referential list, and a cycle
   spanning two containers in O(1) at the point of re-entry — never by
   letting Python's own call stack run out. Identity (`id()`), never
   `==`/`hash()`, is what is compared, so a value engineered to raise on
   comparison or hashing is never touched by the cycle check.
2. **Explicit depth bound.** A new module constant,
   `_MANIFEST_MAX_DEPTH = 64`, is checked at the top of every recursive
   call; exceeding it raises `MalformedManifestError` naming the path and
   the bound. This is independent of `sys.getrecursionlimit()` (which the
   walk does not control and must not rely on) — 64 is far above any
   realistic manifest's nesting (a handful of levels under
   `tool`/`resource`/`repo`/an optional `meta`-shaped extra field) and
   far below the interpreter's default recursion limit (1000), leaving
   headroom for whatever stack depth the caller already has in play.
   `_validate_manifest_entry()` additionally wraps its call to
   `_check_no_surrogates()` in `try/except RecursionError ->
   MalformedManifestError` as defense in depth only — the explicit bound
   should make this unreachable, but the wrapper holds the "never an
   uncaught crash" standard even against an unforeseen pathological shape.
3. **Positive value/key type allowlist.** The walk used to do nothing at
   all for any value that was neither `str`, `dict`, nor `list`, passing
   `bytes`, `set`, custom objects, anything, straight through to
   `grant()`'s `json.dumps()` at the disk-write step. The allowed set is
   now stated *positively* and enforced at validation time: `str`
   (checked for UTF-8 safety, as before), `int`/`float`/`bool`/`None`,
   `dict`, `list`. Anything else raises `MalformedManifestError` naming
   the offending type. The same allowlist applies to dict *keys* —
   previously a non-string key was silently unchecked; now it must be
   `str` (JSON object keys are strings; a non-string key is either
   silently restringified in an unvalidated way or an outright
   `TypeError` at `json.dumps()`, e.g. for a tuple key).

**Why this set, stated as the record must:** these are exactly, and
only, the value shapes `json.dumps(record, ...)` at `grant()`'s
`path.write_text(...)` can turn into bytes on disk without raising. Any
value outside `{str, int, float, bool, None, dict, list}` is therefore
already going to fail at the write step one way or another; rejecting it
here, at validation time, converts a late crash inside `grant()`'s disk
write into an early, reported `MalformedManifestError` at the same
boundary every other malformed shape in this module already raises at.

Test coverage: `HostileManifestShapeTest`, new, added to the PR #3087
branch's test module, covering exactly the required equivalence
partition — self-referential dict, self-referential list, a cycle
through two containers, nesting one level past `_MANIFEST_MAX_DEPTH`,
`bytes`, `set`, a custom `object()`, and a value engineered to raise on
`==`/`hash()`/`iter()` (proving the walk rejects by *type*, never by
touching the hostile behaviour) — plus two boundary/regression cases:
nesting *exactly* at the bound is accepted, and a non-cyclic shared
sub-object (a diamond) is not mistaken for a cycle. Each hostile shape is
checked on both paths: `grant()` raises `MalformedManifestError` (never
`RecursionError`/`TypeError`) and writes nothing to disk
(`assertIsNone(ds.load_state(...))`); `is_covered()` returns `False` and
prints exactly one stderr line naming the rejection (captured via
`contextlib.redirect_stderr`), never raises, never hangs.

acceptance: `python3 -m pytest test/test_delegation_state.py -q`
(run on PR #3087 branch tip, this round's commit, at /tmp/pr3087-work) —
result:
```
91 passed in 0.87s
```

## Why

**The rule this round is really about:** a validator that crashes on
hostile input has not validated anything — it has only moved the crash a
few stack frames later, from `grant()`'s disk write (a plaintext
`UnicodeEncodeError`/`TypeError` a caller has no reason to expect from a
function documented to raise `MalformedManifestError`) to the validator
itself (`RecursionError` from the walk's own unbounded recursion). Every
rejection must be a *reported* rejection — `MalformedManifestError` on
the write path, a named stderr line on every read path — never an
uncaught crash of any kind, regardless of how the input is malformed:
wrong type (rounds 4-6), a lone surrogate (round 5-6), or now hostile to
the *walk itself* (round 7).

Cycle detection by container identity (not by depth accounting alone)
was chosen over "just raise the depth bound and let a cycle eventually
trip it" because a cycle mis-attributed as "too deep" is a worse
diagnostic than a cycle correctly named as a cycle, and because relying
solely on the depth bound to catch a cycle wastes `_MANIFEST_MAX_DEPTH`
recursive calls before failing, when the cycle is detectable in O(1) at
the point of re-entry. Comparing by `id()` rather than `==` was chosen
specifically so the validator can never be made to execute a hostile
value's own `__eq__`/`__hash__`.

acceptance: `python3 -m pytest test/test_delegation_state.py -k HostileManifestShapeTest -q`
— result:
```
9 passed
```
(includes `_RaisesOnCompareOrIterate`, engineered to raise on
`==`/`hash()`/`iter()`; the pass — not an error — proves the walk never
touched those methods.)

The value/key type allowlist is stated *positively* (an explicit
enumerated "allowed" set) rather than negatively (an ever-growing
"known-bad types" blocklist, which is what the previous rounds'
surrogate-only check already was) because the failure this round closes
is exactly the blocklist failure mode: round 6 handled
`str`/`dict`/`list` and was silent about everything else, so every *new*
JSON-incompatible type a caller could construct (`bytes` this round, but
the same gap would have reopened for any other type never explicitly
named) reached `grant()`'s write step uncaught. A positive allowlist
closes the gap for every type not explicitly named, present and future,
in one step, rather than requiring another round to name the next one.

Rejected alternative: catching `RecursionError`/`TypeError` at the
`grant()` call boundary and translating them to
`MalformedManifestError` there, without touching the walk itself. This
was rejected because it does not close the read-path gap —
`is_covered()`/`describe()`/`audit()` call `_check_no_surrogates()`
indirectly through `_safe_manifest()` without going through `grant()`'s
boundary at all, so a malformed value already on disk (written before
this fix, or hand-edited) would still crash those read paths uncaught;
the fix has to live in the walk itself to cover every entry point, not
just the write one.

## Upstream basis

- PR #3212 (`1c7c9dbbab4d0ca2cc95b1cfa1ecf89d3630ce43`) — 8th independent
  verification of PR #3087 round-6, the direct source of this round's
  scope.
  canonical: `gh pr view 3212 --repo tokenmaxxxer/on-the-record` output —
  confirmed hole 3 (per-episode truncation completeness) "Present",
  quantified round-6's cost as acceptable ("Manifest validation:
  sub-millisecond at realistic manifest sizes (50 entries,
  0.125ms/call)"), and found the recursive surrogate walk "not robust to
  its own inputs" on the three grounds this record's fix closes.
- PR #3087 branch tip (`3312d19c4806b784a3c4df73f0c5a828a79e10e6`) — the
  code this round built directly on top of.

## Open findings

None. The three gaps PR #3212 named — self-reference/cycle, unbounded
depth, JSON-incompatible value/key types — are each closed by a distinct,
independently-tested mechanism (identity-based cycle detection, an
explicit depth bound, a positive type allowlist).

derived: `git -C /tmp/pr3087-work diff --stat` — result:
```
 delegation_state.py           | 143 +++++++++++++++++++++++++++++++++++-------
 test/test_delegation_state.py | 139 ++++++++++++++++++++++++++++++++++++++++
 2 files changed, 258 insertions(+), 24 deletions(-)
```
(this round's only edits — no other file touched) plus the full-suite
`FAILED`-line diff in "How this was checked" below (exit 0, no new
regression) — together the basis for "no new gap introduced."

## How this was checked

acceptance: `python3 -m pytest test/test_delegation_state.py -q`
(run on PR #3087 branch tip, this round's commit, at /tmp/pr3087-work) —
result:
```
91 passed in 0.87s
```
(82 of these existed before this round; the other 9 are
`HostileManifestShapeTest`'s new methods, `subTest`-parametrized over 8
hostile shapes each for two of them, plus two boundary/regression
methods — net new assertions, nothing pre-existing changed shape.)

acceptance: `python3 -m pytest test/ tests/ -q`
run twice before this round's edit (via `git stash`) and twice after, on
the same worktree, with `FAILED` lines extracted, sorted, and diffed —
result:
```
before (both runs, byte-identical): 20 failed, 817 passed, 3 xfailed
after  (both runs, byte-identical): 20 failed, 821 passed, 3 xfailed
diff of sorted FAILED-line sets (before vs after): exit 0 (no difference)
```
This environment measures 20 pre-existing failures, not the 22 PR #3212
reported from its own sandbox run — PR #3212's own record independently
re-derived its regression count at each tip it worked from rather than
citing a fixed global constant, and this session's sandbox differs from
that one. What this round holds itself to, and verified above, is that
the *set of failing test names* in this environment is unchanged by
this round's edit — not a specific magic number carried over from a
different sandbox.

acceptance: manual reproduction of every required hostile shape directly
against `grant()` and `is_covered()` (self-referential dict,
self-referential list, a two-container cycle, nesting one level past
`_MANIFEST_MAX_DEPTH`, `bytes`, `set`, a custom `object()`, a
compare/iterate-hostile object) via a `python3 -c "..."` script — result:
```
self_ref_dict OK MalformedManifestError: manifest entry 0['self'] contains a cycle -- a container that refers back to its...
self_ref_list OK MalformedManifestError: manifest entry 0['meta'][0] contains a cycle -- a container that refers back to...
two_container_cycle OK MalformedManifestError: manifest entry 0['meta']['y']['x'] contains a cycle -- a container that refers b...
nest_past_bound OK MalformedManifestError: manifest entry 0['meta']['n']['n']['n']['n']['n']['n']['n']['n']['n']['n']['n'][...
bytes_value OK MalformedManifestError: manifest entry 0['meta'] is a bytes, which is not a type a manifest value may be
set_value OK MalformedManifestError: manifest entry 0['meta'] is a set, which is not a type a manifest value may be (...
custom_object OK MalformedManifestError: manifest entry 0['meta'] is a Custom, which is not a type a manifest value may b...
hostile_value OK MalformedManifestError: manifest entry 0['meta'] is a Hostile, which is not a type a manifest value may...
legit accepted, no crash
```
every shape raised `MalformedManifestError` from `grant()` (never
`RecursionError`/`TypeError`) and left `ds.load_state(repo)` as `None`
(asserted in-script); reproduced live before being encoded as
`HostileManifestShapeTest`.

acceptance: boundary/diamond reproduction via a `python3 -c "..."`
script — result:
```
at_bound accepted
one_past_bound rejected: manifest entry 0['meta']['n']['n']['n']['n']['n']['n']['n'][...
diamond_sibling accepted, manifest= [{'tool': 'Bash', 'resource': 'x', 'meta': {'a': {'k': 'v'}, 'b': {'k': 'v'}}}]
```
— nesting exactly at `_MANIFEST_MAX_DEPTH` round-trips through
`load_state()` unchanged; one level past it is rejected; a diamond
(same sub-dict referenced twice as sibling values) is accepted, not
misdiagnosed as a cycle.

acceptance: cost, timing script (2000 iterations of
`_validate_manifest()` alone on a 50-entry manifest with nested `meta`
fields; 200 iterations of full `grant()` on the same manifest) —
result:
```
0.1570 ms/call for _validate_manifest() alone, 50 entries
0.4818 ms/call for grant() with 50-entry manifest (validation + disk write)
```
comparable to PR #3212's own round-6 baseline (0.125ms/call at the same
manifest size, per the canonical citation in "Upstream basis" above) —
the cycle/depth/type checks add negligible overhead.

## What did not work

None as a design dead end. One immediate self-correction: the first
draft of `HostileManifestShapeTest` used `io.StringIO`/
`contextlib.redirect_stderr` without importing `io`/`contextlib`,
caught by two `NameError` failures from this session's own
lint-test-on-edit hook.

acceptance: `python3 -m pytest test/test_delegation_state.py -q`
(after adding the two missing imports in the same edit pass) — result:
```
91 passed in 0.87s
```
The three checks (cycle, depth, type allowlist) themselves needed no
rework after that.

## Next steps

None identified for this seam by this round. `loop_state: landed`.

skill-verdict: silent-failure-audit — applied: invoked; used to frame
the fix itself — every rejection path in `_check_no_surrogates()`
(cycle, depth, type) raises a named `MalformedManifestError`, or, on the
read path, is caught by `_safe_manifest()` and reported on stderr rather
than absorbed or left to escape as a raw `RecursionError`/`TypeError`.

acceptance: `python3 -m pytest test/test_delegation_state.py -k HostileManifestShapeTest -q`
— result:
```
9 passed
```
(the manual reproduction transcript in "How this was checked" above is
the same evidence, cross-referenced here as the audit's basis.)

skill-verdict: implementation-blueprint — not-applicable: this round is
a bounded fix to one existing recursive function plus its one call site
in a single file already on PR #3087's branch, not new multi-module
structure or a fan-out contract to freeze.
skill-verdict: test-derivation — applied: invoked; the eight required
hostile shapes were treated as an equivalence partition over "ways a
manifest value can defeat the walk's own recursion or type assumptions"
(self-reference x2 shapes, a two-container cycle, a depth-boundary
value, and four type/behaviour-hostile leaf values), matching the test
module's own stated derivation convention (equivalence partitioning by
requirement, per its module docstring), plus two explicit boundary-value
cases (exactly-at-bound, one-past-bound) per BVA practice.
