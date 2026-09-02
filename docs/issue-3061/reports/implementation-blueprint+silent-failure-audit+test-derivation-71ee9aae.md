---
issue: 3061
role: implementation-blueprint+silent-failure-audit+test-derivation-71ee9aae
author: implementation-blueprint+silent-failure-audit+test-derivation-71ee9aae
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: 39c3240f6c1eeb8b0a5cbcaf7c02f6c25b8e29b6
loop_state: landed
type: fix
breaking: false
verdict: fixed — tuple stays rejected, but the allowlist's stated rule now
  names the reason (round-trip type stability through save+load), not a
  claim ("everything json.dumps() can write") the code never actually
  enforced. Independently re-derived the 22-vs-20 pre-existing-failure
  discrepancy PR #3216 raised: both numbers are correct, for different
  pytest scopes, at the same commit — not a shrinking baseline.
upstream:
  - path: docs/issue-3061/reports/adversarial-review+test-depth-audit+silent-failure-audit-10935689.md
    sha: 081e7971d0020f343c43b206255decc51a022cd9
  - path: PR #3087 branch tip this round built on — delegation_state.py
      and test_delegation_state.py, both untracked in this repo's own
      tree (they live only on
      issue-3061/implementation-blueprint+silent-failure-audit+test-derivation+decision-brief-f458808c)
    sha: fdb57899a3a93d11e586900b70d7aaa8431b9b86
---

# issue-3061 — implementation-blueprint+silent-failure-audit+test-derivation-71ee9aae record

## What was done

Round 8 on PR #3087's scope-manifest delegation seam, closing the one edge
PR #3216's ninth independent verification found Incorrect in round 7's
type allowlist, and independently re-deriving a pre-existing-failure-count
discrepancy the spawning prompt flagged (22 vs 20) rather than letting it
stand unexplained.

canonical: `gh pr view 3216` body (state: MERGED) — "Type allowlist —
Incorrect on one edge. ... a `tuple` is hard-rejected even though
`json.dumps` serializes it as a JSON array without error, the exact
standard round 7's own record states the allowlist enforces."

**The tuple edge.** A `tuple` manifest value is hard-rejected by
`_check_no_surrogates()`'s `isinstance(value, (dict, list))` container
check (it falls to the generic `else` branch), even though `json.dumps()`
serializes a tuple as a JSON array without raising — the exact standard
the module's own comment claimed to enforce ("the only value shapes that
can ever survive that write are JSON's own"). Code and stated
justification disagreed.

derived: `python3 -c "import json; print(json.dumps({'a': (1,2,3)}))"` —
result: `{"a": [1, 2, 3]}` (no error) — confirms the premise: `json.dumps()`
does accept a tuple value.

Two defensible resolutions existed: admit tuple (matching the stated
rule), or keep rejecting it and correct the stated rule to name the real
reason. Tested the round-trip consequence before choosing:

derived: `python3 -c "import json; print(json.loads(json.dumps((1,2,3))) == (1,2,3))"`
— result: `False` — a tuple value, round-tripped through `grant()`'s write
(`json.dumps`) and a later `load_state()`'s read (`json.loads`), comes
back as a `list`, not a `tuple`. The in-memory record `grant()` returns
(which still holds the original tuple) would then compare unequal to the
same entry read back off disk — a value silently changing Python type
across a save and load. `fdb57899:test_delegation_state.py:149-153`
(`test_grant_with_explicit_manifest_round_trips_through_load_state`)
already asserts exactly this kind of equality
(`ds.load_state(self.repo)["manifest"] == manifest`), so admitting tuple
would have made that class of assertion fail the moment a tuple value was
in the manifest.

**Decision: keep rejecting tuple.** The round-trip instability is itself
the argument for exclusion, per the round's framing. Changed instead:

1. Rewrote the module-level comment above `_MANIFEST_MAX_DEPTH` and the
   `_check_no_surrogates()` docstring to state the narrower, accurate
   rule: the allowlist is the set of types a `json.dumps()`/`json.loads()`
   round trip hands back as the SAME Python type it started as
   (`str`/`int`/`float`/`bool`/`None`/`dict`/`list`), not "everything
   `json.dumps()` can write without raising." The new comment names
   `tuple` explicitly as the case the distinction exists for and explains
   the equality-across-reload hazard.
   derived: `git show 39c3240f -- delegation_state.py | head -60` (this
   session, this turn) — shows the rewritten comment block landed as
   `39c3240f:delegation_state.py:297-329`.
2. Added `"tuple_value": (1, 2, 3)` to `HostileManifestShapeTest`'s
   `_hostile_shapes()` fixture, at `39c3240f:test_delegation_state.py:910`
   — PR #3216 named this fixture's omission of tuple in either direction
   as exactly why the mismatch was structurally invisible to the existing
   suite. No code-path change was needed for this addition to pass: the
   existing `else` branch (`39c3240f:delegation_state.py:395-399`)
   already rejected tuple correctly; only the fixture and the comment
   were wrong/incomplete.
3. Added a dedicated regression test at
   `39c3240f:test_delegation_state.py:943-966`
   (`test_tuple_is_rejected_even_though_json_dumps_accepts_it`) that
   proves the premise (`json.dumps()` accepts a tuple) and the rejection
   (`ds.grant()` still raises `MalformedManifestError`, no state file
   written) in one place, so a future attempt to admit tuple without
   addressing the round-trip hazard fails loudly rather than silently
   regressing.

derived: `python3 -m pytest test_delegation_state.py -q` (isolated
worktree `/tmp/pr3087-work` at this round's commit, this session, this
turn) — result: `92 passed in 0.85s` (round 7's own record reported 91;
+1 for the new dedicated test).

**The 20-vs-22 pre-existing-failure discrepancy.** The spawning prompt
noted PR #3216 reports 20 pre-existing failures where earlier rounds
(round 4 through round 6) reported 22, and asked which is right at round
7's tip and what happened to the other two.

derived: `python3 -m pytest test/ tests/ -q` at commit `fdb57899` (round
7's tip, isolated worktree `/tmp/pr3087-tip`) and independently at its
parent `3312d19c` (isolated worktree `/tmp/pr3087-parent`) — result: `20
failed, 821 passed, 3 xfailed` at both, sorted `FAILED`-line sets
byte-identical between the two (`diff` exits 0) — matching PR #3216's own
claim exactly. Re-ran twice more at each tip for stability — same counts
both times, no flakiness observed.

derived: `python3 -m pytest -q -m "not slow"` (no path arguments — full
default collection) at commit `3312d19c` (round 6's actual tip, isolated
worktree `/tmp/pr3087-round6-full`) — result: `22 failed, 1034 passed, 3
xfailed`, matching PR #3212's (round-6 verification) claimed count
exactly.

derived: sorted-`FAILED`-line `diff` of that full-default-collection run
(the 22-failed set derived immediately above) against a `python3 -m
pytest test/ tests/ -q` run at the same commit `3312d19c` (the 20-failed
set derived two paragraphs above) — the difference (22 minus 20 = 2) is
exactly two test IDs that live outside the `test/`/`tests/` directories:
one in `on-the-record/checks/test_macos_bash32_compat.py` (test
`MacosBash32CompatTest::test_current_head_is_clean`) and one in
`harness/fixture-operator-experience/test_flow.py` (test
`test_first_contact_fires_once_per_workspace`).

**Both numbers are correct — 22 = 20 + 2, for different pytest scopes, at
the same commit** (derived counts above: 22 full-default-collection, 20
`test/ tests/`-scoped, 2-item difference named and located outside
`test/`/`tests/`). 22 is the full-repo default-collection count (round 4
through round 6's verifications ran bare `pytest -q -m "not slow"`, no
path args). 20 is the `test/ tests/`-scoped count (PR #3216, round 7's
own record, and this round all ran `pytest test/ tests/ -q`). The
underlying repo state did not change between rounds 6 and 7 in a way that
fixed two failures — the count changed because the invocation's scope
narrowed, undocumented as a scope change, and the two counts were
compared as if they measured the same thing. The two tests that
"disappeared" simply live in directories (`harness/`,
`on-the-record/checks/`) neither the `test/ tests/` command nor the
spawning prompt's instruction to run `test/` and `tests/` in full covers.

The baseline this round used, per the spawning prompt's explicit
instruction (`test/` and `tests/` in full): **20 pre-existing failures**,
byte-identical by name at round 7's tip and its parent (derived counts
above).

derived: `python3 -m pytest test/ tests/ -q` at this round's commit
(`39c3240f`, isolated worktree `/tmp/pr3087-work`, this session, this
turn) — result: `20 failed, 822 passed, 3 xfailed` (822 = 821 + 1 new
test from this round); sorted `FAILED`-line set diffed against the
pre-edit `fdb57899` set — identical (`diff` exits 0). This round's edit
fixed zero pre-existing failures and introduced zero new ones.

No merge, no edits outside `delegation_state.py` and
`test_delegation_state.py` on PR #3087's branch. Nothing else on the seam
was touched — cycle detection, the depth bound, the reporting paths, the
single-command property, and the per-episode completeness logic are all
outside this round's scope; the full-suite run above re-confirms their
byte-identical pass/fail status but they were not otherwise re-examined.

## Why

**Reject tuple, don't admit it.** The task framed two defensible answers
and asked which, with a reason. Admitting tuple would have resolved the
comment/code disagreement in the *other* direction (making the code match
its stated "anything json.dumps can write" rule), but the empirical check
above (`json.loads(json.dumps((1,2,3))) == (1,2,3)` → `False`) shows that
rule was never actually safe to enforce as written: a tuple is exactly
the case where "serializes fine" and "round-trips stably" come apart, and
`fdb57899:test_delegation_state.py:149-153` already depends on round-trip
stability holding for every accepted type. Keeping the rejection and
fixing the comment instead means the code's actual behavior (already
correct on this point across all nine prior verifications) does not have
to change at all — only the sentence that mis-described why.

Rejected alternative: admit tuple and normalize it to a list at
validation time (so `grant()` would store `list(value)` instead of the
tuple, sidestepping the round-trip mismatch by making the in-memory and
on-disk representations agree from the start). Not taken because it
widens the validator's job beyond rejection/acceptance into silent
value-coercion — every other accepted type is stored as authored, and a
manifest author who wrote a tuple would get back something they didn't
write with no rejection to notice it. The task's own framing ("either
accept tuple... or keep rejecting it") did not offer this third option,
and it trades one silent surprise (unconditional rejection with a clear
error) for a quieter one (silent type substitution) — a worse direction
for a validator whose entire round-6/round-7 history (per
docs/issue-3061/reports/adversarial-review+test-depth-audit+silent-failure-audit-10935689.md,
canonical: `gh pr view 3216` body, "Reporting — Present" section) has
been about making every hostile shape a *reported* rejection rather than
a surprise somewhere else.

**Comment/docstring correction over new runtime behavior.** The
`_check_no_surrogates()` runtime logic was already correct before this
round — `tuple` already lands in the final `else`
(`39c3240f:delegation_state.py:395-399`) and raises
`MalformedManifestError` naming the type and the allowed set. Applying
the silent-failure-audit lens to this specific path:

canonical: `39c3240f:delegation_state.py:395-399`
(`_check_no_surrogates()`'s final `else` branch) and
`39c3240f:delegation_state.py:453-464` (`_safe_manifest()`) — both read
directly this session, this turn.

- Write path: `grant()` calls `_validate_manifest()` →
  `_check_no_surrogates()`; the `else` branch's `raise
  MalformedManifestError(...)` is not caught anywhere inside `grant()`,
  so it propagates to the caller uncaught — classified **Handled**
  (propagated upward), not Silently Absorbed.
  derived: `python3 -m pytest test_delegation_state.py -k HostileManifestShapeTest -q`
  (isolated worktree `/tmp/pr3087-work`, this session, this turn) —
  result: `2 passed` — `test_grant_refuses_every_hostile_shape_without_crashing_or_writing`
  (`39c3240f:test_delegation_state.py:915-931`) passes for the
  `tuple_value` shape too, asserting `MalformedManifestError` is raised
  and `ds.load_state()` returns `None` afterward (no partial write).
- Read path: `is_covered()` calls `_safe_manifest()`, which catches
  `MalformedManifestError` at line 460, prints a named stderr line at
  lines 461-463, and returns `[]` (fails closed to zero covered actions)
  — classified **Handled** (logged with context + observable fail-closed
  state change), not Silently Absorbed.
  derived: same test run above —
  `test_is_covered_rejects_every_hostile_shape_with_a_reported_stderr_line`
  (`39c3240f:test_delegation_state.py:933-941`) passes for the
  `tuple_value` shape too, asserting `is_covered()` returns `False` and
  stderr contains `"malformed manifest"`.

So the only actual defect was the stated rule disagreeing with the code —
a documentation/comment fix, not a behavior fix, is what closes it.

**Establishing 20 vs 22 rather than picking one.** The spawning prompt
treated the discrepancy as a possible sign of "silently shrinking
baseline" drift — exactly the failure mode issue #3061's own acceptance
criteria exist to catch (a wake/round that reports progress without
re-deriving it). Re-running both scopes at the same commit (`3312d19c`),
rather than trusting either round's stated count, is what showed the
discrepancy is explained by an undocumented scope change (bare `pytest -q`
vs `pytest test/ tests/ -q`) and not by any actual fix or regression —
see the derived counts and the located 2-item diff in "What was done"
above.

## Upstream basis

- docs/issue-3061/reports/adversarial-review+test-depth-audit+silent-failure-audit-10935689.md
  (PR #3216, ninth independent verification, sha
  081e7971d0020f343c43b206255decc51a022cd9) — source of the tuple finding
  and the 20-failure count this round re-derived and confirmed
  (canonical: `gh pr view 3216` body, quoted above in "What was done").
- PR #3087 branch tip `fdb57899a3a93d11e586900b70d7aaa8431b9b86` (round
  7's fix) — the commit this round's fix (`39c3240f`) was built on top
  of, on `issue-3061/implementation-blueprint+silent-failure-audit+test-derivation+decision-brief-f458808c`.

## Open findings

None found in this round's own scope (the tuple edge and the
20-vs-22 count). Both are resolved above with executed evidence:
`39c3240f:delegation_state.py:395-399`/`453-464` plus the
`HostileManifestShapeTest` run confirm the tuple edge is Handled, and the
sorted-`FAILED`-line diffs in "What was done" confirm 22 = 20 + 2 is a
scope difference, not drift.

## What did not work

Nothing attempted in this round was abandoned or reverted. The
"normalize tuple to a list at validation time" alternative (see Why,
Rejected alternative) was considered and rejected before any code was
written for it — no implementation was attempted and discarded.

## Next steps

`loop_state` is `landed`: this round's fix, its regression test, and the
independently re-derived 20-failure baseline are pushed to PR #3087's
branch at commit `39c3240f`.

derived: `git log --oneline -1 origin/issue-3061/implementation-blueprint+silent-failure-audit+test-derivation+decision-brief-f458808c`
(this session, this turn) — result: `39c3240f issue-3061: round-8 fix —
reconcile tuple rejection with its stated rule`, confirming the push
landed on PR #3087's branch tip.

Per the project's round-based independent-verification loop, a further
pass may still run the same way rounds 4 through 9 did before it; this
round's own audit (cited above) did not surface any further hole for
that pass to find, but a tenth independent pass, not this record, is
what would confirm that.

skill-verdict: silent-failure-audit — applied: invoked; traced the tuple
rejection's error-handling chain on both the write path (`grant()` →
`_validate_manifest()` → `_check_no_surrogates()`'s `else` branch →
uncaught `MalformedManifestError`, `39c3240f:delegation_state.py:395-399`)
and the read path (`is_covered()` → `_safe_manifest()`,
`39c3240f:delegation_state.py:453-464`) — both classified Handled, not
Silently Absorbed; confirmed via the `HostileManifestShapeTest` suite run
this session (see Why section).
skill-verdict: test-derivation — applied: invoked; routed the round's
acceptance criterion (tuple round-trip trap) to equivalence partitioning
— tuple is an invalid-type partition for manifest values, distinguished
from bytes/set by clearing `json.dumps()` while still being round-trip-
unstable — classified Medium depth (functional correctness, not
safety-critical); derived the `tuple_value` fixture entry
(`39c3240f:test_delegation_state.py:910`) and the dedicated round-trip-
premise regression test (`39c3240f:test_delegation_state.py:943-966`)
from that partition.
skill-verdict: implementation-blueprint — not-applicable: this round is a
single-function comment/docstring correction plus one test addition to
an existing validator, not new code spanning multiple modules or a
structural decision.
