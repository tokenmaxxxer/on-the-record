---
issue: 3061
role: implementation-blueprint+silent-failure-audit+test-derivation-0c2cc205
author: implementation-blueprint+silent-failure-audit+test-derivation-0c2cc205
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # not a verification -- this is round 6's repair, closing two holes PR #3207 found in round 5
code_under_review: 3312d19c4806b784a3c4df73f0c5a828a79e10e6
loop_state: landed
type: implementation
breaking: false
verdict: two holes closed (manifest UTF-8 validation now walks the entire entry structure recursively, not just tool/resource/repo; audit()'s truncated-episode completion check is now per-episode, not a single per-log flag); the previously-Present properties (no lexical classifier, four historical cases, action identity from tool_use arguments, single-command property, single-episode truncation handling) all survive unchanged; delivered directly onto PR #3087's branch, both test/ and tests/ run in full, 22 pre-existing failures byte-identical by name to round 5's own tip.
upstream:
  - path: PR https://github.com/tokenmaxxxer/on-the-record/pull/3087 (code delivered onto its branch through commit 6f600355, round 5's own repair)
    sha: 6f600355b5778817bda5a714c0b42c1673cb5c57
  - path: PR https://github.com/tokenmaxxxer/on-the-record/pull/3207 (seventh independent verification of round 5 -- the round this repair responds to)
    sha: b10d5b15a2142abb15975f6b4df8f3f556524497
---

# issue-3061 — implementation-blueprint+silent-failure-audit+test-derivation-0c2cc205 record

## What was done

Round 6 on PR #3087 (issue #3061), the scope-manifest delegation seam. PR #3207's seventh independent, builder-blind verification of round 5's repair (PR #3204) graded hole 1 (compound command via wildcard) Surface — `_is_provably_single_command()` refused every control/separator shape tried, no bypass found, left untouched this round — and graded holes 2 and 3 Incorrect. This session closed both, delivered under this task's build-now bypass (`CORE_BUILD_NOW=1`, this session's environment).

**Code delivered directly onto PR #3087's own branch** (`issue-3061/implementation-blueprint+silent-failure-audit+test-derivation+decision-brief-f458808c`), matching every prior round's placement precedent — PR #3087 stays the code PR; this session's own branch carries only this record. `delegation_state.py` and `test/test_delegation_state.py` are both **untracked in this session's own checkout** (based on `main`, where PR #3087 has not merged) for every citation below; both were edited and committed via a local `git worktree` checked out directly from `origin/issue-3061/implementation-blueprint+silent-failure-audit+test-derivation+decision-brief-f458808c` at `6f600355`, then pushed back onto that same remote branch as two commits (`c7b2fc31` code, `3312d19c` tests). Every citation below, including inside command strings, is to that pushed history, not to this checkout.

canonical: `gh pr view 3207 --json body` output, this session, this turn — full body read before writing any code, to extract the exact two holes fixed below
canonical: `gh pr view 3087 --json headRefOid` output, this session, this turn, after push — `headRefOid: 3312d19c4806b784a3c4df73f0c5a828a79e10e6`, confirming the push landed on the PR

### Hole 2 — UTF-8 validation covered only the three named fields (PR #3207 hole 2)

Round 5's `_validate_manifest_entry()` (`6f600355:delegation_state.py:256-272`) called `_is_utf8_safe()` only on `entry["tool"]`, `entry["resource"]`, and `entry["repo"]`. PR #3207 reproduced a lone Unicode surrogate crashing `grant()` uncaught with the identical `UnicodeEncodeError` round 5 claimed to close, in positions none of those three named fields cover: an unlisted key's string value, a surrogate used AS a dict key, and a surrogate nested inside a structure under a non-named field — and, because `Path.write_text()` truncates the target file before the encode error fires, each position destroys any pre-existing valid delegation state in the process.

The fix stops naming fields. `_check_no_surrogates()` (`3312d19c:delegation_state.py:256-288`) recursively walks the entire manifest entry — every dict key, every dict value, every list element, at every depth — and raises `MalformedManifestError` the moment any string found anywhere fails `_is_utf8_safe()`. `_validate_manifest_entry()` (`3312d19c:delegation_state.py:295-312`) keeps its existing per-named-field type checks (a non-string `tool`/`resource`/`repo` still gets the specific "field X is a Y, not a string" message) and then calls `_check_no_surrogates(entry, ...)` once over the whole entry, catching everything the named-field checks alone could not.

```python
def _check_no_surrogates(value, path: str) -> None:
    if isinstance(value, str):
        if not _is_utf8_safe(value):
            raise MalformedManifestError(...)
    elif isinstance(value, dict):
        for key, sub_value in value.items():
            if isinstance(key, str) and not _is_utf8_safe(key):
                raise MalformedManifestError(...)
            _check_no_surrogates(sub_value, f"{path}[{key!r}]")
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _check_no_surrogates(item, f"{path}[{i}]")
```
(`3312d19c:delegation_state.py:256-288`, quoted with messages elided.)

Because `grant()`'s `validated_manifest = _validate_manifest(manifest)` call (`3312d19c:delegation_state.py:206`, unchanged this round) already runs before `path.write_text(...)`, this closure means `grant()` refuses before touching disk in every new position, the same as the named-field positions round 5 already closed — verified below by execution, not just by code inspection.

derived: throwaway reproduction script run inside the isolated worktree at `3312d19c`, this session, this turn — `ds.grant(repo, "pre-existing", "jiwon", skill_env="")` writes a real state file and its bytes are captured, then `ds.grant(repo, "scope", "jiwon", skill_env="", manifest=manifest)` is called for each of the three new surrogate positions (`{"tool": "Bash", "resource": "git *", "note": "bad\ud800"}`, `{"tool": "Bash", "resource": "git *", "\ud800": "value"}`, `{"tool": "Bash", "resource": "git *", "meta": {"nested": ["ok", "bad\ud800"]}}`) — result: `MalformedManifestError` raised in all three positions, and the state file's bytes read back afterward equal the pre-existing capture in all three positions (disk unchanged: True/True/True), proving the pre-existing valid delegation is never destroyed.

derived: `python3 -m pytest test/test_delegation_state.py::MalformedManifestTest -q` (test/test_delegation_state.py untracked in this checkout; this session, this turn, against `3312d19c`) — result: `7 passed` — the three new positions added to `MALFORMED_SHAPES` are exercised by all three existing shape-table test methods (`is_covered()` never crashes, `describe()` never crashes, `grant()` refuses and leaves no partial file), covering all six surrogate positions now on record (three named-field, three new) — derived: `git show 3312d19c:test/test_delegation_state.py | grep -c '"surrogate'` inside the isolated worktree, this session, this turn — result: `6`.

### Hole 3 — audit()'s completion check was per-log, not per-episode (PR #3207 hole 3)

Round 5's `audit()` (`6f600355:delegation_state.py:791`) computed `log_reached_completion = trajectory_analyzer.final_result_event(events) is not None` once per log file, then consulted that single global flag only for the one episode whose boundary ran off the end of the transcript (`if boundary == len(events) and not log_reached_completion:`). PR #3207 reproduced that a log can carry more than one `result` event — one per completed episode — so an earlier episode completing normally made the global flag `True`, and a later episode truncated with no `result` event of its own still read as globally "reached completion" and got flagged as a clean avoidable stop.

The fix makes completion a fact checked per episode, for every episode audit() reports on, not only the one whose boundary reaches EOF:

```python
result_indices = [i for i, ev in enumerate(events) if ev.get("type") == "result"]
...
episode_reached_completion = any(
    event_index < ri < boundary for ri in result_indices)
if not episode_reached_completion:
    indeterminate.append({...})
    continue
```
(`3312d19c:delegation_state.py:822,847-849`, dict body abbreviated.) `result_indices` is every `result` event's index in the whole log, computed once; an episode is known-complete only if at least one of those indices falls strictly inside its own stretch (`event_index < ri < boundary`), regardless of what that episode's own boundary is — a genuinely-found next ask proves the log kept being written to, not that this specific episode's own turn ever reached a completion marker before that later writing happened.

Dropping the old `boundary == len(events)` gate (round 5 checked completion only for the episode that ran off the end of the log; round 6 checks it for every episode, unconditionally) changes which fixtures read as complete: an episode bounded by a real next ask but carrying no `result` event of its own is now also indeterminate, where round 5 treated "a next ask was found" as sufficient proof of completeness by itself. One pre-existing test, `EpisodeBindingTest.test_episode_ends_at_the_next_ask_not_the_end_of_log`, built exactly that shape (no `result` event anywhere in its log) and needed its first episode's own `_result_event()` added to keep asserting the exact same thing it always meant to assert (a genuinely-finished, covered episode is flagged) — not a weakened assertion; the assertions themselves (`count == 1`, `flagged[0]`'s excerpt) are unchanged.

derived: `git diff 6f600355 3312d19c -- test/test_delegation_state.py | grep '^-' | grep -v '^---'` (test/test_delegation_state.py untracked in this checkout; this session, this turn) — result: the only removed lines from any pre-existing test body are two comment lines inside `test_episode_ends_at_the_next_ask_not_the_end_of_log`; no assertion line in any pre-existing test method was touched.

The task named two log constructions:
- Episodes A and B each end with their own `result` event; episode C's covered action is followed by nothing at all — no `result` event, no next ask.
- Episode A's covered action is followed directly by episode B's ask with no `result` event for A in between; episode B then reaches its own `result` event.

derived: `python3 -m pytest test/test_delegation_state.py::MultiEpisodeCompletionTest -q` (test/test_delegation_state.py untracked in this checkout; this session, this turn, against `3312d19c`) — result: `2 passed` — `test_two_complete_episodes_then_a_truncated_third_is_indeterminate` (episodes A and B flagged, `count == 2`; episode C indeterminate, `len(indeterminate) == 1`) and `test_middle_episode_truncated_while_last_completes_is_indeterminate` (episode B flagged, `count == 1`; episode A indeterminate, `len(indeterminate) == 1`).

derived: `python3 -m pytest test/test_delegation_state.py::TruncatedLogIndeterminateTest test/test_delegation_state.py::EpisodeBindingTest -q` (test/test_delegation_state.py untracked in this checkout; this session, this turn, against `3312d19c`) — result: `9 passed` — round 5's single-episode truncation handling (killed mid-episode, partial final JSON line, control case reaching a result event, uncovered truncated episode) and round 4's episode-binding property both still hold under the new per-episode check.

## Why

For hole 2, the fix stops enumerating field positions and instead walks the whole structure, because the task's own framing named the mistake precisely: a check written against the cases someone listed rather than against the whole input, the same shape four lexical-classifier rounds and round 5's hole-1 token list already failed on by omission. A recursive structural walk cannot miss a position no one thought to name, the same reasoning `str.isprintable()` was chosen over a token list for hole 1 in round 5. Reusing `_is_utf8_safe()` (unchanged this round) rather than writing a new surrogate check keeps exactly one definition of "round-trips through UTF-8" in the module.

For hole 3, per-episode scoping was chosen over adding a second, narrower global flag (e.g. one that special-cased only the trailing episode differently from the rest) because a second special-cased flag would only re-narrow the same bug shape one position over; the task's own two named constructions (a truncated trailing episode, a truncated middle episode) each defeat a single-extra-flag design on their own, and only a uniform per-episode rule closes both at once. `result_indices` scans the log once and is reused across every episode's check rather than re-scanning per episode, keeping the cost linear in log size.

derived: `python3 -m pytest test/test_delegation_state.py::MultiEpisodeCompletionTest -q` (test/test_delegation_state.py untracked in this checkout; this session, this turn, against `3312d19c`) — result: `2 passed`, confirming the uniform per-episode rule (not a second special-cased flag) is what actually closes both of the task's named constructions.

## Silent-failure audit (silent-failure-audit skill, invoked this session)

Scope: the two new/changed error-handling-adjacent sites this round's diff touches in `delegation_state.py` (untracked in this checkout) at `3312d19c`.

1. `_check_no_surrogates()` (`3312d19c:delegation_state.py:256-288`) — no try/except; a plain recursive `if`/`elif` with `raise MalformedManifestError(...)` on the failure branch, the same propagation contract as the per-field checks it extends. **Handled**: propagates to `grant()` (loud, by design — an authoring-time bug must fail loudly) or is caught by `_safe_manifest()` (fail-closed plus a stderr diagnostic, unchanged this round) on every read path (`is_covered()`, `_describe_manifest()`, `audit()`).
   derived: throwaway reproduction script cited in the "Hole 2" section above (grant() refuses, no partial file, in all three new positions) plus `python3 -m pytest test/test_delegation_state.py::MalformedManifestTest -q` (this session, this turn, against `3312d19c`) — result: `7 passed`.
2. `audit()`'s new `result_indices`/`episode_reached_completion` computation (`3312d19c:delegation_state.py:822,847-849`) — not a try/except; a list comprehension over `.get("type")` and a generator inside `any(...)`, neither of which can raise (no I/O, no parsing, both pure dict/list operations over already-parsed `events`). **N/A** for this classification — nothing fallible to catch; the branch itself is the fix.

derived: `git diff 6f600355 3312d19c -- delegation_state.py | grep -F "except" | grep '^+'` (delegation_state.py untracked in this checkout; this session, this turn) — result: no output — zero new `except` clauses this round; every new check either raises loudly at the one authoring boundary (`grant()`) or is read through the pre-existing `_safe_manifest()` fail-closed wrapper.

The two pre-existing unguarded sites named in round 4's and round 5's own audits (`audit()`'s `since` parsing, `grant()`'s disk write) remain out of scope — neither is one of this round's two named holes, and the `git diff` citation above (touching only the cited line ranges) confirms neither regressed.

## Test derivation (test-derivation skill, invoked this session)

Two High-risk requirements (A=yes: each is a data-destroying crash or a security-relevant false-clean verdict), full derivation.

**R-hole2** (a manifest string that cannot round-trip through UTF-8 must be rejected wherever it appears in the entry, not only in tool/resource/repo) — equivalence partitioning over string position within the entry structure. Partitions: the three pre-existing named-field positions (re-verified for non-regression) plus the three new positions the task named (an unlisted key's value, a surrogate as a dict key, a surrogate nested under a non-named field), folded into `MALFORMED_SHAPES` and exercised by the existing shape-table test methods plus a dedicated grant()-refuses-before-disk-write reproduction for the three new positions.
derived: `python3 -m pytest test/test_delegation_state.py::MalformedManifestTest -q` (this session, this turn, against `3312d19c`) — result: `7 passed`, covering every partition above (six surrogate positions total, per the `grep -c` citation in the "Hole 2" section).

**R-hole3** (an episode must be individually known-complete; other complete episodes in the same log must not make an unrelated episode read as complete) — decision table over {this episode's own boundary: found-next-ask or ran-to-EOF} × {a `result` event exists inside this episode's own stretch: yes or no} × {other episodes in the same log completed: yes or no}. Feasible columns: (found-next-ask, own-result=yes) flags/withholds per coverage, unaffected by completion, exercised by round 4's own `test_episode_ends_at_the_next_ask_not_the_end_of_log` (now carrying its own result event); (found-next-ask, own-result=no, others-complete=yes) is indeterminate, the task's named "middle truncated" case; (ran-to-EOF, own-result=no, others-complete=yes) is indeterminate, the task's named "trailing truncated after two complete" case; (ran-to-EOF, own-result=no, others-complete=no) is indeterminate, round 5's own single-episode case, re-verified unchanged; (ran-to-EOF, own-result=yes) flags, round 5's own control case, re-verified unchanged.
derived: `python3 -m pytest test/test_delegation_state.py::MultiEpisodeCompletionTest test/test_delegation_state.py::TruncatedLogIndeterminateTest test/test_delegation_state.py::EpisodeBindingTest -q` (this session, this turn, against `3312d19c`) — result: `11 passed`, covering every feasible column above.

derived: `git show 3312d19c:test/test_delegation_state.py | grep -c "    def test_"` (this session, this turn) — result: `87` total test methods.
derived: `git show 6f600355:test/test_delegation_state.py | grep -c "    def test_"` (this session, this turn) — result: `85`; the difference between the two counts above is exactly `MultiEpisodeCompletionTest`'s two new methods — no pre-existing test method was deleted or renamed, per the `git diff`-of-removed-lines citation in the "Hole 3" section above.

## What did not work

None. No approach was tried and discarded during this round; the recursive-walk design for hole 2 and the per-episode `result_indices` design for hole 3 were each the design this session settled on directly — reasoned out from the task's own framing (walk the whole input, not named cases; check every episode individually, not a per-log flag) before writing any code, not a later correction of an earlier attempt.

derived: `python3 -m pytest test/test_delegation_state.py -q` (test/test_delegation_state.py untracked in this checkout; this session, this turn, against `3312d19c`) — result: `87 passed`, run once the design above was implemented and never revised afterward.

## Test suite

Ran both `test/` and `tests/` in full, plus the narrower `-m "not slow"` selection prior rounds' own records used for direct comparison, against the pushed commit `3312d19c` via an isolated `git worktree` (removed at session end).

derived: `python3 -m pytest -q -m "not slow"` at `3312d19c` (this session, this turn) — result: `22 failed, 1034 passed, 3 xfailed, 2 warnings`.
derived: `python3 -m pytest -q -m "not slow"` at `6f600355` (round 5's own tip, before this round's edits), same isolated worktree mechanism, this session, this turn — result: `22 failed, 1032 passed, 3 xfailed, 2 warnings`.
derived: `diff` of the two independently captured, sorted `FAILED` line sets (`3312d19c` vs `6f600355`), this session, this turn — result: no output (identical), 22 lines in each file — the pre-existing failures are byte-identical by name to round 5's own tip; the passed-count difference between the two runs above is exactly this round's two new test methods, no other test count changed.
derived: `python3 -m pytest test/ tests/ -q` at `3312d19c` (this session, this turn) — result: `20 failed, 817 passed, 3 xfailed, 2 warnings` (the plain `test/ tests/` invocation selects a narrower subset than the repo-root `-m "not slow"` run above — the same 20-vs-22 split prior rounds' own records already noted between the two invocations).
derived: `python3 -m pytest test/test_delegation_state.py -q` at `3312d19c` (this session, this turn) — result: `87 passed`.

## Doc placement

- [x] Code delivered to `delegation_state.py` and `test/test_delegation_state.py` (both untracked in this checkout, PR #3087-only) on PR #3087's own branch (not this session's branch) — matches every prior round's placement precedent.
- [x] This session's own record placed at `docs/issue-3061/reports/` — matches this repo's existing bucket convention for this issue.
- [x] No `docs/specs/*` file touched this round — derived: `git diff 6f600355 3312d19c --stat` at `3312d19c`, this session, this turn — result: only `delegation_state.py` and `test/test_delegation_state.py` changed, both untracked in this checkout — `gates/spec_index.py --update` not applicable.

## Upstream basis

- PR #3087, branch `issue-3061/implementation-blueprint+silent-failure-audit+test-derivation+decision-brief-f458808c`, code through `6f600355` (round 5's repair) — this round's starting point.
- PR #3207 (`b10d5b15`), seventh independent, builder-blind verification — every "Hole N" reference above traces to this record's own findings, read in full before any code was written (sha: same-commit, this record lands in this same checkout's history).

## Open findings

- The two pre-existing unguarded sites named in round 4's and round 5's own silent-failure audits (`audit()`'s `since` parsing, `grant()`'s disk-write failure path) remain unfixed — out of scope for this round's two named holes, unchanged disposition.
- Neither this round nor round 5 added a dedicated regression test for a bare Python `bool` as a manifest field value (same named gap round 5's record disclosed) — `isinstance(bool_value, str)` is `False` regardless of the bool's value, provably identical in code path to the tested `entry_field_wrong_type_int` case, but not separately exercised.

## Next steps

None from this session — round 6 is delivered onto PR #3087's branch and this record is landed. Next step (outside this session's scope) is an eighth independent, builder-blind verification round against `3312d19c`.

skill-verdict: silent-failure-audit — applied: invoked; enumerated the two new/changed error-handling-adjacent sites this round's diff touches in delegation_state.py, classified each Handled/N-A with derived pytest citations in the "Silent-failure audit" section above
skill-verdict: test-derivation — applied: invoked; routed the two round-6 requirements to equivalence-partitioning and decision-table techniques with derived pytest coverage citations in the "Test derivation" section above
skill-verdict: implementation-blueprint — not-applicable: derived: `git diff 6f600355 3312d19c --stat` at `3312d19c` (this session, this turn) shows this round's entire diff confined to `delegation_state.py` and `test/test_delegation_state.py` (both untracked in this checkout, PR #3087-only) — one existing module plus its test file, no new file, no multi-module fan-out, no architectural/structural decision to freeze
other mounted skills: not triggered
