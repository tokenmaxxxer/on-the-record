---
issue: 2219
role: implementation
loop_state: landed
upstream:
  - path: gates/record_lint.py
    sha: same-commit
code_under_review:
  - gates/record_lint.py
  - on-the-record/gates/record_lint.py
  - gates/test_record_lint.py
  - on-the-record/hooks/test_record_claim_guard.py
type: fix
breaking: none
verdict: pass
---

# issue-2219 — implementation record

## What was done

canonical: `on-the-record-issue-2208-implementation.session.20260824T231045.1590418.log` (recovered per this issue's own Acceptance instruction, read this session) plus `gates/record_lint.py`/`on-the-record/gates/record_lint.py` (diffed this session).

Root-caused both verbatim rejections quoted in issue #2219 to two distinct defects, then fixed both:

1. **Stale packaged mirror.** `record-claim-guard.sh` resolves its gate module from `on-the-record/gates/` first (issue #556's cache-layout order), not from `gates/`. That packaged copy of `record_lint.py` had not been synced since issue #791/#968 — every precision fix from #1599/#1614/#1620/#1628 landed only in `gates/record_lint.py`. This alone produced the issue's `#333` verbatim rejection (`` `fail-open`, with the full suite still passing 9/9. ``): the *current* `gates/record_lint.py` already had the PR #1622 fence-proximity exemption; the deployed, stale copy did not.
2. **Evidence-adjacency window too narrow, even in the current module.** `canonical_source_claim_check` (#793) and `outcome_claim_citation_check` (#870) only searched a fixed 3-4 physical-line window around a claim. Two real shapes fall outside that window: (a) the record's own `` `acceptance: ... — result:` `` + fence evidence sits several lines earlier under the *same* `### N. <item>` subsection, and (b) a `derived:`/`acceptance:` label and the sentence it introduces get split across physical lines by markdown's own soft-wrap, so a same-line-anchored regex never connects them. This produced the issue's `#870` verbatim rejection (`acceptance: diff of the two fenced runs above — result: both negative cases read` `` `completed` ``).

Fix, in `gates/record_lint.py`:
- `_section_bounds()`: widened the evidence search from a fixed line count to the claim's enclosing markdown section (nearest heading before/after) for `canonical_source_claim_check` and `outcome_claim_citation_check` — deliberately narrower than "the whole record": PR #1622 already found a whole-document fence exemption too permissive (one early fence silently vouching for every later bare count), so this stays scoped to one section.
- `_dewrap()`: collapse soft-wrapped line breaks inside an evidence window before running any label regex against it, so a wrapped sentence reads as one line for matching purposes.
- `_CLAIM_DERIVED_TAG` widened to accept a bare (non-backtick) `derived:` label — the same leniency `canonical:` already had — and generalized as a sibling evidence tag for any claim type, not just count claims.
- New `_acceptance_evidence_lines()` / `_ACCEPTANCE_RESULT_LEADIN`: recognizes this project's own documented executed-live convention (`on-the-record/directive/acceptance-format.md`: `` `acceptance: <command> — result:` ``) immediately followed by a fenced block as grounding in its own right, independent of any `canonical:` wrapper.
- Every check function's rejection message now ends with a "통과하려면 ..." sentence naming the concrete evidence shape that satisfies it, for #310/#331/#333/#330/#793/#870/#791.
- `_prose_window()`: the section-scoped evidence window excludes fenced-block lines (delimiters and content) before matching — see "What did not work" below for why.
- Synced the fixed module to `on-the-record/gates/record_lint.py` so the deployed hook actually runs it.

acceptance: `python3 -m pytest gates/test_record_lint.py -q -o addopts=` — result:
```
75 passed in 2.48s
```
acceptance: `python3 -m pytest on-the-record/hooks/test_record_claim_guard.py on-the-record/hooks/test_hook_cache_layout.py -q -o addopts=` — result:
```
32 passed in 1.08s
```
derived: per the two fenced runs directly above, both suites pass in full — seven new cases in `gates/test_record_lint.py` and five new cases in `on-the-record/hooks/test_record_claim_guard.py`, on top of the 68/22 that already existed.

**Live-fire before/after, through the actual deployed hook** (`on-the-record/hooks/record-claim-guard.sh`), against the exact two record fragments recovered from the session log:

acceptance: before/after script (`/tmp/run_guard_before_after.py`, replays both verbatim record fragments through the pre-fix and post-fix `on-the-record/gates/record_lint.py`) — result:
```
##### BEFORE (stale packaged record_lint.py) #####
[repro1 / #870 quote] rc= 2
quoted-claim present: True
[repro2 / #333 quote] rc= 2
quoted-claim present: True

##### AFTER (synced record_lint.py, issue #2219 fix) #####
[repro1 / #870 quote] rc= 2
quoted-claim present: False
[repro2 / #333 quote] rc= 2
quoted-claim present: False
```
canonical: the AFTER run's `rc= 2` on both lines is a *different*, unrelated denial (an orphaned-path #330 hit on the session log's own file path, an artifact of replaying the fixture from this repo instead of the original session's working tree) — `quoted-claim present: False` on both is the actual before/after proof: the exact two verbatim claims quoted in this issue no longer appear in the guard's stderr after the fix, in either repro.

acceptance: genuinely-unevidenced control, same before/after script, against a record with an outcome claim and a bare count claim and nothing else in its section — result:
```
rc= 2
record-claim-guard: issue #333 (bare count), issue #793 (canonical source), and issue #870 (outcome claim) all still fire, each ending in a 통과하려면 (would-pass) sentence.
```
Confirms the fix does not weaken enforcement: a claim with no fence, no `canonical:`/`derived:` tag, and no `acceptance: ... — result:` pairing anywhere in its section is still refused by all three rules, and each denial now names the passing shape.

skill-verdict: other mounted skills — not triggered (implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint: this is a within-module regex/evidence-scope fix to one existing file plus its packaged mirror and tests — no coupling/cohesion threshold, GoF-pattern decision, performance-critical data-structure choice, or new cross-module architecture was in play, so none of the four applied).

## Why

`_section_bounds` scopes to the claim's own subsection rather than the whole record because PR #1622 already discovered that a whole-document evidence exemption is too permissive — a single fence or tag early in a long record would silently vouch for every later claim, which is exactly the failure mode #2219 asks NOT to reintroduce ("Do not weaken what the guards enforce"). Scoping to the nearest enclosing markdown section is the narrowest boundary that still resolves both verbatim repros, since this project's own record convention already organizes one `### N. <item>` subsection per claim+evidence pair.

Recognizing `` `acceptance: ... — result:` `` + an immediately-following fence as grounding in its own right (not just as *content* nested inside a `canonical:` tag) was necessary because the #870 repro's actual evidence uses exactly that shape with no `canonical:` wrapper at all — this is the project's own documented, dominant citation convention (`on-the-record/directive/acceptance-format.md`, `gates/requirement_met.py`'s COMMAND-IDENTITY check), so teaching the guard to recognize it is closing a gap against the project's own stated convention, not inventing a new one.

Rejected alternative: reconstructing the full file for `Edit`/`MultiEdit` fragments in `record-claim-guard.sh` (today it only sees the changed fragment, per that script's own comment) would close a related but separate gap — evidence living in an *untouched* part of the file, invisible to an `Edit` call entirely. Not implemented here: neither verbatim repro in this issue was an `Edit`-fragment case (both were full-content `Write` calls), so it is out of this issue's concrete, evidenced scope, and the existing code comment already documents it as a known write-time approximation.

## What did not work

canonical: before-landing warrant-hunt dispatched against commit `ff1de0b7` (this issue's first landed commit), finding text read this session.

The first cut of the section-scoped widening joined every line in `[lo, hi)` — including fenced code-block content — before matching `canonical:`/`derived:` labels. A `canonical:`/`derived:` string appearing only as illustrative example text inside a fence (e.g. documentation showing the tag format itself) then satisfied #793/#870 for an unrelated claim elsewhere in the same section — a real false-negative the warrant-hunt reproduced directly against `canonical_source_claim_check`/`outcome_claim_citation_check`. Fixed by adding `_prose_window()`, which excludes fenced lines from the window before matching; only the author's own live prose counts as evidence, never quoted/pasted fence content. Regression-pinned as `t_2219_canonical_tag_inside_fence_is_not_real_evidence` in `gates/test_record_lint.py`, and re-verified live through the deployed hook.

acceptance: `python3 -m pytest gates/test_record_lint.py -q -o addopts=` (re-run after the fence-exclusion fix) — result:
```
76 passed in 4.04s
```
derived: per the fenced re-run above, the suite count rose from 75 to 76 (the one new regression-pin test), still all green — the fence-exclusion fix did not disturb either verbatim repro (re-checked directly against `/tmp/repro1.md`/`/tmp/repro2.md`, both still resolve clean) or any pre-existing case.

## Upstream basis

- Issue #2219 body (denial counts, both verbatim rejection quotes, Acceptance section).
- `on-the-record-issue-2208-implementation.session.20260824T231045.1590418.log` — the live session recoverable per the issue's own Acceptance instruction; both verbatim rejections were located and replayed from it verbatim (extracted from this log's `Write` tool-call payloads at message indices 683 and 621 respectively — scratch files under `/tmp`, not committed).
- `on-the-record/directive/acceptance-format.md` (the `acceptance: ... — result:` convention this fix now recognizes as grounding).
- PR #1622 / issue #1620 (the fence-proximity precedent this fix deliberately stays narrower than).

## Open findings

None blocking this issue. One unrelated, out-of-scope sighting stays untouched by design: replaying the full `repro2` fixture still trips a *separate* `#870` line elsewhere in that same fixture file, on a different sentence than either claim this issue's Acceptance section quotes verbatim — left alone rather than expanding this fix's scope past what was evidenced.

## Next steps

None — loop_state is terminal (landed).
