---
code_under_review:
  - on-the-record/hooks/contract-guard.sh
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/test_contract_guard.py
  - on-the-record/hooks/test_pr_preflight.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Round 2 (2026-08-11) — execution provenance + phase-1 closes refusal

## What was done

Implemented the approved re-investigation proposal
(`docs/issue-741/proposals/2026-08-11-execution-provenance-and-phase1-closes-refusal.md`),
which addresses two roots identified by this issue's re-investigation
(survey.md's "Round 2" section) behind two real-world falsifications of
the Round 1 fix below.

canonical: docs/issue-741/reports/implementation/survey.md "Round 2" section
Real-world recurrences addressed: PR #768 (issue-759 phase-1, a docs-only
diff) and PR #763 (issue-743 phase-1, an author-written `Closes #743`).

**(a) `contract-guard.sh` — execution provenance log.** Added an
unconditional JSON-line append to `$CONTRACT_GUARD_PROVENANCE_LOG`
(default `~/.claude/on-the-record/hook-provenance.log`), recording this
exact running script's own absolute path (`CG_SELF_PATH`, computed by the
bash wrapper via the same `cd "$(dirname ...)" && pwd -P` idiom
`self-update.sh` already uses) and sha256, plus the `pr`/`repo`/`issue`/
`phase2`/`is_src_test`/`is_record`/`closes_present_before` verdict it
computed for this merge. The `files`/`is_src_test`/`role`/`is_record`
computation (previously positioned after the `phase2` round-scoping gate)
moved to immediately after `issue` is determined and validated — the
earliest point its own data dependency (`issue`) allows — so it, and
`phase2` right after it, are both always available before the log write,
regardless of which way either of the two existing gates (`if not
phase2`, `if not (is_src_test or is_record)`) will go. Both gates keep
their original positions and exact conditions; only the computation
order changed. The log write itself is wrapped in `try/except Exception:
pass`, including directory creation — a log failure can never become a
new deny path or change what merges.

**(b) `pr-preflight.sh` — phase-1 author-written `Closes` refusal.**
Added one more check, right after the existing `check_body()` call, that
fires only when `phase == "phase1"` and `check_body` returns no
violation: scans the body via `_CLOSES_REF.finditer()` (iterating every
match, not `.search()`'s first-match-only) for a closing-keyword
reference to the PR's own issue, and denies when a match exists.
`check_body`/`_plan_from_body`/`_CLOSES_REF` themselves are byte-for-byte
unchanged. `.finditer()` mirrors `gates/ci.py`'s `_closes_ref_for_issue`
semantics without importing it (zero-install) — the after-proposal
warrant hunt (stance 0, below) identified that the proposal's own draft
wording pointed at this file's pre-existing `.search()` idiom, which
stops at the first closing-keyword match even when it names a different
issue; the shipped check does not reproduce that bypass.

**`test_contract_guard.py`:** `_run_guard()` gained an `extra_env`
parameter. Two new cases: `test_provenance_log_records_self_path_hash_and_verdict`
(PR #747/#739-shaped fixture — docs-only, same-round approval — asserts
the log line's `script_path`/`script_sha256` match the actually-running
`contract-guard.sh`, and `phase2=true`/`is_src_test=false`/
`is_record=false` are recorded even though the two content gates below
the log write both end up denying the attach) and
`test_provenance_log_write_failure_does_not_change_verdict` (log path
under a regular file standing in for a directory — asserts identical
`returncode` and identical recorded `gh pr edit` calls against the same
fixture with a working log path).

**`test_pr_preflight.py`:** Added `_phase1_closes_ref()`, a pure-Python
duplicate of the new inline check (same convention this file already
used for `check_body`/`_plan_from_body`), plus five new cases in the
existing `run()` matrix: the `check_body(126, "Closes #126", "phase1")
== []` regression pin (proposal-mandated, demonstrates the gate lives
outside `check_body`), the PR #763-shaped case (plain `#743` + `Closes
#743` both present), the decoy-reference case pinning the after-proposal
hunt finding (`"Fixes #999, ... Closes #743"` — a naive `.search()` would
land on `#999` and miss the real `#743`; `_phase1_closes_ref` must not),
and the existing "phase1 plain #459 reference only" case extended to
also assert the new check finds nothing to deny. Also added two
`test_hook_*` functions that drive the real `pr-preflight.sh` end-to-end
via subprocess against a stub `gh` — this delivery's own acceptance bar
specifically asked for a stub-driven hook-level test, not just the
duplicated-logic assertions above (see Acceptance verification).

```
$ python3 -m pytest on-the-record/hooks/test_pr_preflight.py -v
collecting ... collected 0 items
```
That first run against the file as it stood before this round's `test_hook_*`
additions (see "What did not work") led to converting them into
pytest-collectible `test_*` functions:
```
$ python3 -m pytest on-the-record/hooks/test_pr_preflight.py -v
collecting ... collected 2 items
on-the-record/hooks/test_pr_preflight.py::test_hook_denies_phase1_docs_only_pr_with_author_written_closes PASSED
on-the-record/hooks/test_pr_preflight.py::test_hook_allows_legitimate_phase2_pr PASSED
```
so `python3 -m pytest on-the-record/hooks/test_pr_preflight.py` now
reports real PASS/FAIL output as the proposal's own "How you'll know it
worked" section assumed it already did.

`docs/issue-741/decisions/execution-provenance-and-phase1-closes-refusal.md`
(new) records both chosen designs, their rejected alternatives, and a
known-and-accepted residual risk the before-landing hunt surfaced
(below).

## Why

canonical: docs/issue-741/reports/implementation/survey.md "Round 2" section (re-investigation) and docs/issue-741/proposals/2026-08-11-execution-provenance-and-phase1-closes-refusal.md
PR #819 (`f2b9097`) landed the re-investigation proposal this round
implements. Round 1's fix (`is_src_test`/`is_record` content gate in
`contract-guard.sh`) was logically correct and covered by the test
matrix from Round 1 (see below), but still failed twice in production
for two independent reasons the proposal's Rationale traces in full.

canonical: docs/issue-741/reports/implementation/survey.md, "사례 2 근본 원인 (PR #768, issue-759 phase-1)" section
(a) The process that executed `gh pr merge` for PR #768 ran a stale
Claude Code plugin-cache copy of `contract-guard.sh` (`installedAt`/
`lastUpdated` timestamped well before the content-gate commit),
undetectable from `git log` on the checkout alone — only surfaced by
hand-diffing every cache directory against `installed_plugins.json`.

canonical: docs/issue-741/reports/implementation/survey.md, "사례 1 근본 원인 (PR #763, issue-743 phase-1)" section
(b) Nothing in the live execution path ever refused an author writing
`Closes #<issue>` directly into a phase-1 PR body themselves (PR #763) —
`check_body`'s phase1 branch deliberately doesn't check for it (own
test: `tests/test_gates.py`'s `t_pr_reference_phase1_does_not_gate_closing_keywords_itself`),
and `gates/ci.py`'s `_phase1_mismatch`, which does, lost its only caller
when GitHub Actions retired (issue #460).

## Acceptance verification

- PR #747/#739-shaped docs-only PR + same-round approval records `phase2=true` but `is_src_test=false`/`is_record=false`, and the log line's `script_path`/`script_sha256` match the real running script — checked: on-the-record/hooks/test_contract_guard.py::test_provenance_log_records_self_path_hash_and_verdict — result: pass
- log directory unwritable (regular file occupying a path segment) leaves the merge verdict and `gh pr edit` calls byte-identical to a working log path — checked: on-the-record/hooks/test_contract_guard.py::test_provenance_log_write_failure_does_not_change_verdict — result: pass
- docs-only phase-1 PR body carrying an author-written `Closes #<issue>` (PR #763 shape) is refused by the real, unmodified `pr-preflight.sh` (subprocess, stub `gh`), `returncode == 2` — checked: on-the-record/hooks/test_pr_preflight.py::test_hook_denies_phase1_docs_only_pr_with_author_written_closes — result: pass
- a legitimate phase-2 delivery PR passes through the real, unmodified `pr-preflight.sh` untouched by the new phase-1-only check, `returncode == 0` — checked: on-the-record/hooks/test_pr_preflight.py::test_hook_allows_legitimate_phase2_pr — result: pass
- decoy-reference bypass named by the after-proposal hunt (a closing keyword for a different issue appears before the real one) — the new check still locates the real match via `.finditer()` — checked: on-the-record/hooks/test_pr_preflight.py::run — result: pass
- `check_body(126, "Closes #126", "phase1") == []` stays unaffected, `check_body` itself byte-for-byte unchanged — checked: on-the-record/hooks/test_pr_preflight.py::run — result: pass
- the proposal's own "How you'll know it worked" third bullet (a real `gh pr merge` after this PR lands appends a new provenance-log line, `sha256sum` against that moment's `contract-guard.sh` matches) — checked: docs/issue-741/proposals/2026-08-11-execution-provenance-and-phase1-closes-refusal.md — result: unverifiable: that event is a future production merge this session cannot execute; test_provenance_log_records_self_path_hash_and_verdict exercises the identical code path (real script, subprocess, its own path/hash) as a stand-in

## Verification run

```
$ python3 -m pytest on-the-record/hooks/test_contract_guard.py on-the-record/hooks/test_pr_preflight.py -v
============================= test session starts ==============================
collected 21 items

on-the-record/hooks/test_contract_guard.py::test_cross_repo_same_number_judges_target_not_cwd PASSED [  4%]
on-the-record/hooks/test_contract_guard.py::test_repo_flag_targets_repo_but_no_local_approvers_is_unreached PASSED [  9%]
on-the-record/hooks/test_contract_guard.py::test_full_pr_url_targets_repo_but_no_local_approvers_is_unreached PASSED [ 14%]
on-the-record/hooks/test_contract_guard.py::test_cd_prefix_reads_target_approvers_and_attaches PASSED [ 19%]
on-the-record/hooks/test_contract_guard.py::test_cd_prefix_allows_when_target_pr_closes_issue PASSED [ 23%]
on-the-record/hooks/test_contract_guard.py::test_repo_flag_overrides_cd_prefix_when_they_disagree PASSED [ 28%]
on-the-record/hooks/test_contract_guard.py::test_no_repo_indicator_unchanged_cwd_behavior PASSED [ 33%]
on-the-record/hooks/test_contract_guard.py::test_write_failure_still_denies_merge PASSED [ 38%]
on-the-record/hooks/test_contract_guard.py::test_prior_round_approval_allows_new_phase1_pr PASSED [ 42%]
on-the-record/hooks/test_contract_guard.py::test_same_round_approval_attaches_closes_when_missing PASSED [ 47%]
on-the-record/hooks/test_contract_guard.py::test_same_round_approval_with_closes_allows PASSED [ 52%]
on-the-record/hooks/test_contract_guard.py::test_cross_role_approval_still_gates_phase2 PASSED [ 57%]
on-the-record/hooks/test_contract_guard.py::test_docsonly_pr_with_same_round_approval_gets_no_closes PASSED [ 61%]
on-the-record/hooks/test_contract_guard.py::test_docsonly_pr_with_no_approval_gets_no_closes PASSED [ 66%]
on-the-record/hooks/test_contract_guard.py::test_code_bearing_pr_with_same_round_approval_gets_closes PASSED [ 71%]
on-the-record/hooks/test_contract_guard.py::test_unrelated_file_under_reports_dir_gets_no_closes PASSED [ 76%]
on-the-record/hooks/test_contract_guard.py::test_own_record_file_alone_gets_closes PASSED [ 80%]
on-the-record/hooks/test_contract_guard.py::test_provenance_log_records_self_path_hash_and_verdict PASSED [ 85%]
on-the-record/hooks/test_contract_guard.py::test_provenance_log_write_failure_does_not_change_verdict PASSED [ 90%]
on-the-record/hooks/test_pr_preflight.py::test_hook_denies_phase1_docs_only_pr_with_author_written_closes PASSED [ 95%]
on-the-record/hooks/test_pr_preflight.py::test_hook_allows_legitimate_phase2_pr PASSED [100%]

============================== 21 passed in 3.65s ==============================
```

derived: `grep -c "^def test_" on-the-record/hooks/test_contract_guard.py`
```
19
```
This total is the pre-existing Round 1 matrix plus this round's two new
provenance-log cases.

```
$ python3 on-the-record/hooks/test_pr_preflight.py
PASS: phase2 Closes with incomplete non-final step -> denied
PASS: phase2 no closing keyword, plan None -> denied
PASS: phase1 plain #459 reference -> allowed
PASS: phase2 Closes #459, plan None -> allowed
PASS: phase2 Closes #459, plan all done -> allowed
PASS: phase2 Closes #459, only final step incomplete -> allowed
PASS: _plan_from_body parses steps
PASS: _plan_from_body returns None with no header
PASS: check_body(126, 'Closes #126', 'phase1') == [] (unchanged, gate lives outside check_body)
PASS: _phase1_closes_ref(126, 'Closes #126') finds it -> would deny
PASS: PR #763 shape: check_body('phase1') allows (plain ref present)
PASS: PR #763 shape: _phase1_closes_ref finds 'Closes #743' -> would deny
PASS: decoy shape: a naive .search() call would find the wrong issue (#999)
PASS: decoy shape: _phase1_closes_ref still finds the real 'Closes #743' via finditer
PASS: phase1 plain #459 reference only: check_body allows (existing case)
PASS: phase1 plain #459 reference only: _phase1_closes_ref finds nothing -> allowed

All checks passed
```

canonical: `python3 -m pytest tests/test_gates.py -k phase1_does_not_gate_closing_keywords_itself -v`
```
tests/test_gates.py::t_pr_reference_phase1_does_not_gate_closing_keywords_itself PASSED
1 passed, 109 deselected
```
`check_body` itself is unmodified this round.

canonical: `python3 -m pytest -q` run against the working tree with this
round's uncommitted changes applied
```
1189 passed, 2 skipped, 1 xfailed, 5 failed in 193.18s
FAILED gates/test_boundary.py's t_all_gates_modules_recorded
FAILED gates/test_capability_gates.py's t_actual_tree_schema_field_orphans_catches_alive
FAILED gates/test_generated_paths.py's t_all_generators_recorded_and_disjoint
FAILED harness/fixture-target/test_fixture_target.py's test_resolve_version_returns_version_string_when_flag_set
FAILED tests/test_gates.py's t_rulebook_version_is_recorded
```
canonical: `git stash` (returns the tree to the clean `c58e23f` state) followed by re-running the same three node IDs
```
3 failed in 0.06s
FAILED gates/test_boundary.py's t_all_gates_modules_recorded
FAILED gates/test_generated_paths.py's t_all_generators_recorded_and_disjoint
FAILED harness/fixture-target/test_fixture_target.py's test_resolve_version_returns_version_string_when_flag_set
```
The same three reproduce identically on the clean tree (`git stash pop`
restored this round's changes afterward) — pre-existing, not introduced
by this round's diff. `gates/test_capability_gates.py`'s
`t_actual_tree_schema_field_orphans_catches_alive` is the known-red
fixture issue-811 is currently working on (per this turn's own
instructions, left untouched). `tests/test_gates.py`'s
`t_rulebook_version_is_recorded` asserts the working tree carries no
uncommitted-changes marker in `spawn.rulebook_version`'s output — it
fails only while this round's changes sit uncommitted and clears once
they land in a commit. None of the five are new regressions from this
round's diff.

## What did not work

- Expected `python3 -m pytest on-the-record/hooks/test_contract_guard.py
  on-the-record/hooks/test_pr_preflight.py -v` (the proposal's own "How
  you'll know it worked" command) to report new PASS results from
  `test_pr_preflight.py` once the new cases were added there. Running it
  reported zero collected items from that file (see the fenced
  transcript in "What was done" above) — it had no pytest-collectible
  `test_*` functions, only a `run()` invoked via `if __name__ ==
  "__main__"`, a property of the file predating this round. Fixed by
  adding two subprocess-driven `test_hook_*` functions (also needed
  anyway for this delivery's own acceptance bar: a stub-driven
  hook-level test asserting both the phase-1 refusal and the phase-2
  pass-through) — `python3 -m pytest` on this file now collects those
  two, both passing.

## Hunt

After-proposal (stance 0, phase 1, already in
`docs/issue-741/reports/implementation/hunt-2026-08-11-execution-provenance-and-phase1-closes-refusal.md`,
"after-proposal — stance 0"): FINDING — the proposal's own draft wording
for the `pr-preflight.sh` check pointed at this file's pre-existing
`.search()` idiom, which would reproduce a decoy-reference bypass
`gates/ci.py`'s own `_closes_ref_for_issue` docstring documents having
hunted once already. Resolved in the shipped implementation via
`.finditer()` (see "What was done" (b) above) and pinned by the "decoy
shape" test cases in both `test_pr_preflight.py`'s standalone runner and
this record's Acceptance verification.

Before-landing (stance 1, this session, same hunt-record file
"before-landing — stance 1"): FINDING — `contract-guard.sh`'s any-role
phase2 signal and `pr-preflight.sh`'s exact-role phase2 signal can
disagree on the same issue's approval comments (a pre-existing
divergence, documented in `docs/issue-741/decisions/phase2-signal-choice.md`'s
"Scope boundary" section and `docs/issue-653/reports/architecture/survey.md`
gap #1), and this delivery's new `pr-preflight.sh` check gives that
divergence a new, live consequence: it can refuse the exact
closing-trailer edit `contract-guard.sh`'s own broker-attach exists to
require. Not fixed here — see
`docs/issue-741/decisions/execution-provenance-and-phase1-closes-refusal.md`'s
"Known, accepted residual risk" section for the full reproduction and the
reason it stays deferred: fixing it means unifying the two hooks' phase
signals, which issue #653's ADR and this issue's own Round 1 decision
doc already scoped out on separate investigations, and this round's own
re-investigation (the proposal's Constraints and Rationale sections)
turned up no new grounds to reopen that boundary. The scenario needs
three preconditions together (a different role's approval comment on the
same issue, a prior `contract-guard.sh` broker-attach failure, and a
manual retry of the identical edit) and does not affect either of this
delivery's two Acceptance rows for (b) above — neither uses a cross-role
approval comment.

## Open findings

The residual risk under "Hunt" above (before-landing stance 1) remains
open, by design — see that section and the linked decision doc for the
resolution path (phase-signal unification across `contract-guard.sh` and
`pr-preflight.sh`, a future issue's scope, not this one's).

---

# Round 1 (2026-08-11) — content-based phase-2 gate

Verbatim, unchanged from the previously-landed record (PR #819,
`f2b9097`) — preserved here as historical context for Round 2 above.

```
Implemented the approved phase-1 proposal
(docs/issue-741/proposals/2026-08-11-phase2-content-gate.md) in
contract-guard.sh:

- Widened the existing gh_json("pr", "view", pr, "--json",
  "body,number,commits") call to also request `files` — one more field
  on a call already made, no new round trip.
- After the existing round-scoped `phase2` boolean, added a second,
  independent content-based condition: any path in the PR's own diff
  matches (^|/)(src|tests?)/, OR matches the acting role's own exact
  record file docs/issue-<n>/reports/<role>.md — the same two patterns
  approval-gate.sh:116-119 already gates writes on.
- The acting role is derived from `git rev-parse --abbrev-ref HEAD` (run
  with cwd=target_cwd or os.getcwd()) parsed against
  ^issue-(\d+)/([\w-]+)$, the same lookup pr-preflight.sh/
  approval-gate.sh already perform. If the branch doesn't parse, or its
  issue number doesn't match the PR's own issue, the record-file half of
  the check is skipped (narrows the match, never widens it) — the
  (^|/)(src|tests?)/ half still applies unconditionally.
- The existing attach-or-deny block now runs only when `phase2 AND` the
  new content boolean both hold; when `phase2` is true but the PR carries
  no phase-2-shaped path, the script exits 0 without touching the body —
  same as an ordinary phase-1 merge.

In test_contract_guard.py:

- FAKE_GH's `pr view` branch now also emits `files` from the fixture
  (data.get("files", [])).
- Added _repo_dir_on_branch(): a real git init + checkout -b + one empty
  commit, needed for the record-file half of the check, which requires
  `git rev-parse --abbrev-ref HEAD` to resolve (an unborn branch with
  zero commits does not resolve — see What did not work).
- Updated the pre-existing fixtures whose scenario expects Closes
  attached (test_cross_repo_same_number_judges_target_not_cwd,
  test_cd_prefix_reads_target_approvers_and_attaches,
  test_no_repo_indicator_unchanged_cwd_behavior,
  test_write_failure_still_denies_merge,
  test_same_round_approval_attaches_closes_when_missing,
  test_cross_role_approval_still_gates_phase2) with a "files": [{"path":
  "src/example.py"}] entry, so they keep exercising the same "PR is
  actually phase-2-shaped" scenario they always represented, now under
  the widened --json call.
- Added the regression/empty-state/content-positive matrix from the
  proposal's "What will be done": test_docsonly_pr_with_
  same_round_approval_gets_no_closes (the #741/PR-#747/#739 regression
  itself — Acceptance item 1), test_docsonly_pr_with_no_approval_gets_
  no_closes (empty-state pairing), test_code_bearing_pr_with_same_
  round_approval_gets_closes (Acceptance item 2 — regression guard,
  generalized to the new content-gated path), test_unrelated_file_
  under_reports_dir_gets_no_closes (the after-proposal hunt's exact
  scenario, pinned as a permanent regression), and test_own_record_
  file_alone_gets_closes (a genuine docs-only phase-2 delivery is still
  recognized).

New: docs/issue-741/decisions/phase2-signal-choice.md records the
chosen signal, the two rejected alternatives, and the forgeability
judgment in permanent form.

Why: contract-guard.sh's round-scoping condition (issue #577) is
trivially true for any same-round approval, including a docs-only
phase-1 proposal PR — approval by definition postdates phase-1's first
commit on a shared branch. This produced two premature issue closures:
issue-729/PR #739, then this issue's own phase-1 PR #747 (a 4-doc-file
PR whose body said "Refs #741", closed anyway once the broker attached
Closes #741 on same-round approval). Basis:
docs/issue-741/proposals/2026-08-11-phase2-content-gate.md.

Acceptance verification: docs-only phase-1 PR + same-round approval —
Closes not attached, PR merges without closing the issue —
test_docsonly_pr_with_same_round_approval_gets_no_closes passes,
asserting returncode == 0 and no gh pr edit call recorded, on a
pr_body/files fixture shaped exactly like PR #747/#739 (docs-only diff,
Refs #<n> body, same-round approval comment). Code-bearing phase-2 PR +
approval — Closes attached and merge proceeds, as today —
test_code_bearing_pr_with_same_round_approval_gets_closes passes,
asserting the trailer is attached via the recorded gh pr edit call, on a
fixture whose diff includes a src/ path.

What did not work: first _repo_dir_on_branch() attempt did a bare git
init + checkout -b <branch> with no commit — `git rev-parse
--abbrev-ref HEAD` failed with exit 128 ("ambiguous argument 'HEAD':
unknown revision") because an unborn branch (zero commits) doesn't
resolve as a revision for rev-parse, even though HEAD is a valid symbolic
ref. Fixed by committing once (--allow-empty, pinned local
user.name/user.email) right after the checkout. First
test_code_bearing_pr_with_same_round_approval_gets_closes fixture used
"path": "on-the-record/hooks/contract-guard.sh" as the "this PR touches
real code" file — it does not match (^|/)(src|tests?)/ (no src/test(s)/
path segment), so the test failed by not getting an attach. Replaced with
"src/contract_guard.py", which matches the pattern the code actually
checks.

Open findings: the before-landing warrant hunt (stance 1,
docs/issue-741/reports/implementation/2026-08-11-hunt-phase2-content-gate.md,
section "before-landing — stance 1") returned a FINDING, reproduced with
runnable commands in that file: pr-preflight.sh's own phase-2 signal
(unscoped by time, exact "APPROVE issue-<n>/<role>" match only) can force
a Closes #<issue> trailer into a docs-only PR's body at gh pr
create/edit time, in the case where the approval comment already exists
before the PR is opened/edited (a different ordering than either real
recurrence: PR #739 and PR #747 both had approval land after PR
creation, so pr-preflight.sh saw no approval yet and did not force the
trailer). contract-guard.sh's new content gate only refuses to ADD
Closes on a non-phase-2-shaped diff — it does not strip one already
present — so in that ordering the issue could still auto-close on a
docs-only merge via GitHub's native keyword-closing.

pr-preflight.sh is not part of this proposal's write set, and unifying
its comment-matching logic with contract-guard.sh's was already
explicitly deferred by this proposal's own Rationale ("Scope boundary —
pr-preflight.sh unification, explicitly out") and, before that, by issue
#653's ADR
(docs/issue-653/proposals/2026-08-10-closes-trailer-preflight-hardening.md
lines 60-70, 88-91), which named it as its own gap
(docs/issue-653/reports/architecture/survey.md gap #1). This finding
does not revise that boundary; it adds one more concrete reason a future
issue may want to reopen it — either round/content-scoping
pr-preflight.sh's signal, or having contract-guard.sh actively strip a
disagreeing Closes trailer.

This does not affect the two Acceptance rows this delivery targets — both
reproduced real-world orderings (#739, #747: approval lands after PR
creation) are covered by the passing test matrix above; the finding
describes a third, not-yet-observed ordering.
```
