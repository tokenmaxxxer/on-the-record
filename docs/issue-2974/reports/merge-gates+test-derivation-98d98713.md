---
issue: 2974
role: merge-gates+test-derivation-98d98713
author: merge-gates+test-derivation-98d98713
skills: merge-gates (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: gates/check_runner.py, gates/merge_gate.py, gates/risk_report.py, on-the-record/hooks/impact-guard.sh
    sha: 167cc19a9cf9dd31ac90250d0f9a069f6d70bf68
---

# issue-2974 — merge-gates+test-derivation-98d98713 record

## What was done

Three gate defects fixed, per the issue's three lettered findings (build-now
bypass, `CORE_BUILD_NOW=1`; delivered directly, no phase-1 proposal round).

**C — record-only PR mis-scoring (`gates/check_runner.py`).** Added
`pr_diff_paths()` (a `gh pr diff <pr> --name-only` call, same shape as
`ci.py`'s `_shadow_diff_paths`), `touches_implementation_paths()` (primary
signal: any diff path outside `docs/` counts as implementation; `None`/empty
diff fails closed to `True` so an unreadable diff is still scored, never
silently skipped), and `frontmatter_record_only_signal()` (corroborating
signal: reads `kind:` frontmatter — via `gates.record_frontmatter()` — off
the diff's own `docs/issue-<n>/reports/*.md` files, matched against the
closed `_RECORD_ONLY_KINDS`/`_IMPLEMENTATION_KINDS` sets — never a filename,
branch name, or skill name). canonical: `docs/specs/record-kind-vocabulary.md`
(read in full this session) — the two sets' entries are that spec's own
"Verification/observation records"+"Research/discovery records"+"Proposal/
decision records"+"Generic/legacy" category members (record-only) versus its
"Delivery/coding records" category members (implementation), copied as
string literals, not derived from any role/skill name. `main()` now computes
both signals before running mechanical checks: when the diff signal says
record-only, a new `RECORD_ONLY_MARKER` comment is posted and `run_checks()`
is never called (exit 0, non-blocking); when the two signals disagree, a
disagreement line is appended to whichever comment posts (record-only or
normal-scoring) rather than resolving it silently — the diff signal always
wins the record-only/scored decision itself. `gates/merge_gate.py`'s
`_RESULT_HEADER`/`parse_check_runner_result()` recognize the new marker
(`{"record_only": True}`) and `evaluate()` treats it as satisfied, distinct
from the pre-existing `no_checks` fail-closed case.

**B — batch merge inheriting unrelated risk (`gates/risk_report.py`,
`on-the-record/hooks/impact-guard.sh`).** `batch_blocked()` gained an
optional `batch_files: list[list[str]] | None` parameter: when given, an
individually-required proposal is only included if its own `files:`
overlap (`_paths_overlap`, already-existing glob-aware comparison) with at
least one PR's write-set in `batch_files`; `None` (default) preserves
today's behavior unchanged for every existing caller. `impact-guard.sh`
gained `_merge_pr_numbers()` (resolves the plain `gh pr merge <n>` shape
only; any other shape returns `None` for the whole command) and now calls
`gh pr diff <n> --name-only` per resolved PR to build `batch_files` before
calling `batch_blocked()` — any resolution failure leaves `batch_files`
as `None`, falling back to the pre-#2974 behavior rather than guessing.

**A — empty R-ID canon (`docs/specs/requirements.md`,
`docs/specs/requirement-digest.md`).** Added two new entries, R005 and
R006, each sourced from a genuine, still-open, non-infra-tagged issue with
a verbatim operator-authored ask and an already-enforced check (chosen
specifically to avoid the fabrication risk of inventing an operator quote):
R005 (source #1664, the `classify()` function in `gates/stale_revert_guard.py`)
and R006 (source #511, the `classify_axes()` function in `gates/risk_report.py`
— the very module this same issue edits for finding B). Digest regenerated
via `python3 gates/requirement_digest.py --update`; canon grew from 4 to 6
live R-IDs, derived: `git show 167cc19a:docs/specs/requirement-digest.md | grep -c "R[0-9]"` (before) vs `grep -c "R[0-9]" docs/specs/requirement-digest.md` (after) — see Verification section for both outputs.

New test files, both passing standalone (derived: `python3 -m pytest gates/test_check_runner.py gates/test_risk_report.py -q` — result below in Verification): `gates/test_check_runner.py` (pure
`touches_implementation_paths()`/`frontmatter_record_only_signal()` cases
plus `main()` integration tests covering record-only-not-scored,
implementation-still-scored, and both disagreement directions) and
`gates/test_risk_report.py` (implicated-still-blocks,
unrelated-does-not-block, empty state, and `batch_files=None`
backward-compatibility cases).

## Why

**C:** the issue's consult explicitly rejected deciding record-only status
from frontmatter alone or from filename/branch/skill name. The diff itself
is the only signal that can't be spoofed by what a record chooses to call
itself, so it is primary; `kind:` is real but was observed absent on a live
record in this same session's own sweep — canonical: `gh pr diff 2965` output,
whose added report file (on PR #2965's own unmerged branch, issue-2960/
test-derivation-8718eaa7 — not present in this branch's working tree) carries
`role:`/`author:`/`skills:`/`verifies_subject:`/`code_under_review:`/
`loop_state:` frontmatter lines but no `kind:` line at all — so it can only
corroborate, never decide alone, and when it contradicts the diff, silently
overriding either signal would hide exactly the kind of drift issue #2974
exists to surface.

**B:** `batch_blocked()` already computed axes per-proposal; the missing
piece was scoping *which* proposals apply to *this* batch, not changing how
individual-approval is decided for a proposal a batch actually touches — so
the fix is additive (an optional filter), never a weakening of the
dominant-axis rule itself.

**A:** the issue's consult was explicit that loosening the gate is
rejected — the fix has to grow the canon. R001-R004 are keyed to
`docs/specs/requirements.md`'s own "operator's own words, unedited"
constraint; I did not attempt to mint R-IDs for the six watchdog-flagged
issues listed in the issue's `population:` note (#2774/#2864/#2872/#2883/
#2890/#2956) because all three of their common parent issues I read in full
(#2705, #2139, #2941 — canonical: `gh issue view <n> --json body` output for
each, read in full this session) carry `infrastructure/no-direct-requirement`
legitimately (self-referential gate-machinery work with no product
requirement to cite) — minting a requirement quote for them would have
been exactly the fabrication the registry's format is built to prevent.
Instead I mined two *different*, already-substantive, non-infra-tagged
issues (#1664, #511 — same canonical source: `gh issue view <n> --json body`)
that this session had independent reason to trust (both already had a live
enforced check I could name precisely, and #511 is the design doc for the
very `risk_report.py` axes this same session edits for finding B).

## Upstream basis

Base commit `167cc19a9cf9dd31ac90250d0f9a069f6d70bf68` (branch tip at
session start) for `gates/check_runner.py`, `gates/merge_gate.py`,
`gates/risk_report.py`, `on-the-record/hooks/impact-guard.sh`,
`docs/specs/requirements.md`. GitHub issues read in full as sourcing/
context: #2974 (subject), #2965/#2967/#2968 (live record-only-PR
mis-scoring cases, via `gh pr diff --name-only`), #2705/#2139/#2941/#2609
(candidate R-ID sources, rejected — infra-tagged), #1664 and #511 (R005/
R006 sources, accepted).

## Open findings

None.

## Next steps

None — loop_state: landed.

skill-verdict: merge-gates — applied: invoked; used Step 4's fail-direction
audit framing (every gate's failure direction named) to characterize the
three defects. canonical: `gh issue view 2974 --json body` output (read in
full this session) plus the live artifact of finding C's diff (`gh pr diff
2965` — that PR's own comment history/check-runner scoring 2/4 against
predicate-code checks its branch never carried) — from those: finding C is
a wrong-target scoring bug (it scores the wrong branch, not classically
fail-open/closed), finding B is an over-broad fail-closed inheriting from
an unimplicated proposal, and finding A is a fail-open-via-escape-tag-ritual
when the citation gate's own canon is empty. Step 1's branch inventory and
Step 3's combined-state mechanism did not apply — this issue is about
existing per-PR gate logic, not queue/inventory design.
skill-verdict: test-derivation — applied: invoked; used Step 3's
problem-shape routing informally (2 discrete signals x discrete outcomes =
decision-table shape) when deriving `gates/test_check_runner.py`'s
`main()`-level cases (record-only/not-scored, implementation/scored, and
both disagreement directions) and `gates/test_risk_report.py`'s cases
(implicated/blocks, unrelated/does-not-block, empty-state,
`batch_files=None`/back-compat) so each combination of {diff signal} x
{frontmatter signal or batch-implication} that the issue's acceptance
distinguishes has its own named test — see Verification section for the
passing run of both files. Skipped the skill's full formal apparatus (Step
3a classification table, itemized EP/BVA partition lists, a written
traceability matrix) as disproportionate to a 3-item structural gate bugfix
with acceptance criteria that already name the exact pytest `-k`
identifiers to hit.

other mounted skills: not triggered — `work-in-english` guidance followed
throughout (English commit messages, code comments, and this record) but
never invoked via the Skill tool.

## Verification

- derived: `python3 -m pytest gates/ -k record_only_pr_not_scored -q`
  ```
  2 passed in 0.86s
  ```
- derived: `python3 -m pytest gates/ -k record_signal_disagreement -q`
  ```
  2 passed in 0.83s
  ```
- derived: `python3 -m pytest gates/ -k batch_merge_unrelated_proposal -q`
  ```
  4 passed in 0.90s
  ```
- derived: `python3 -m pytest gates/ -q` (full suite, no regressions)
  ```
  42 passed in 1.32s
  ```
- derived: `python3 -m pytest test/test_auto_approval_shadow_wiring.py test/test_merge_gate_record_kind.py test/test_verifies_subject_scaffold.py test/test_watchdog_heartbeat_noise.py test/test_checkout_staleness.py -q` (nearby consumers of `requirement-digest.md`/`risk_report`/`check_runner`/`merge_gate`, no regressions)
  ```
  41 passed in 1.18s
  ```
- derived: `python3 gates/requirement_digest.py .`
  ```
  통과: docs/specs/requirement-digest.md 이 docs/specs/requirements.md 과 일치한다
  ```
- unverifiable: the acceptance item's literal `grep -c "^R[0-9]" docs/specs/requirement-digest.md` returns `0` (checked live, exit 1) because every digest entry is rendered with a `"- "` bullet prefix (`- R001: ...`), a format `watchdog.py`'s `_DIGEST_LIVE_ENTRY_RE` (`^- (R\d+): ...`) depends on for its own real advisory parsing — changing the render format to satisfy the bare `^R[0-9]` anchor would break that load-bearing consumer for a cosmetic match, and nothing in the issue's must-not list asks for a render-format change.
  derived: `grep -c "R[0-9]" docs/specs/requirement-digest.md` (no anchor, counts the same entries the literal check means to)
  ```
  6
  ```
  derived: `git show 167cc19a:docs/specs/requirement-digest.md | grep -c "R[0-9]"` (same count, base commit, before this session's R005/R006)
  ```
  4
  ```
- derived: `bash -n on-the-record/hooks/impact-guard.sh`
  ```
  (exit 0, no output)
  ```
- derived: `python3 -c "import ast; ast.parse(open('/tmp/impact_guard_embedded.py').read())"` (the hook's embedded python heredoc, extracted and parsed standalone)
  ```
  (no error)
  ```
