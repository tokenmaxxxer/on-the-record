---
issue: 2609
role: architecture-interface-contract-shape+silent-failure-audit-ded46e17
author: architecture-interface-contract-shape+silent-failure-audit-ded46e17
skills: architecture-interface-contract-shape (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
loop_state: landed
upstream:
  - path: docs/issue-2593/reports/architecture-module-boundary-definition+architecture-decomposition-strategy-386ff408.md
    sha: 483d106dba5d77dac0273b9c24be314de265474d
---

# issue-2609 — architecture-interface-contract-shape+silent-failure-audit-ded46e17 record

## What was done

canonical: this record's factual claims are grounded in direct `Read` of
`gates/spawn_on_pr.py`, `gates/merge_gate.py`, `gates/skip_eligibility.py`,
`gates/trivial_lane_gate.py`, `docs/handbooks/observer-verification.md`,
`docs/specs/enforcement-boundary.md`, `spawn.py` (LEGACY dict area), and
`test/test_merge_gate_record_kind.py`/`gates/test_spawn_on_pr.py`, plus `gh
issue view 2609 --json title,body,comments`, all read/executed directly
this session (build-now delivery, `CORE_BUILD_NOW=1`, single phase — no
proposal round per contract v3 s19a).

Implemented Issue A of the design in
`docs/issue-2593/reports/architecture-module-boundary-definition+
architecture-decomposition-strategy-386ff408.md` (Option 2, sha
483d106dba5d77dac0273b9c24be314de265474d) and the operator ruling on that
design's Open finding 1 (issue #2609 body, 2026-08-27: the
`skip_eligibility.py`-driven kind-specific exemption goes entirely).

**Merge-gating mechanism (`gates/merge_gate.py`, the load-bearing piece):**

- `_exempt_own_record_kind()` deleted. Replaced by
  `_own_pr_supplies_verification(repo, subject, own_branch, subject_author)`
  — reads the evaluated PR's own branch content directly via `git show
  origin/<branch>:docs/issue-<n>/reports/<slug>.md` (the branch isn't
  landed yet, so `spawn.board()` has nothing to join against) and, if that
  record self-declares `verifies_subject: true` with an `author:`
  different from the subject's deliverable author, exempts this PR from
  the check outright — same sibling-cycle-break purpose as the deleted
  function (issue #2233/#2380), no kind-name matching.
- `required_verification_missing()` rewritten: no longer calls
  `spawn_on_pr.applicable_record_kinds()`. Now computes
  `max(0, spawn_on_pr.REQUIRED_INDEPENDENT_VERIFICATIONS -
  spawn_on_pr.verifying_record_count(subject_board, subject_author))` and
  returns that integer deficit (`0` = satisfied).
- `evaluate()`'s refusal message rewritten to name the mechanism and the
  count it saw, not a list of kind names (acceptance bullet 2's own
  wording) — `f"required_verification_missing(): 독립 검증 기록이
  부족하다 -- {seen}/{required}개 확인됨 ({missing}개 더 필요)"`.
- `import gates` added (sibling import, same flat-import pattern the file
  already uses for `spawn_on_pr`/`check_run_artifact`/`check_runner`/
  `stale_revert_guard`) to reuse `gates.record_frontmatter()` for parsing
  the branch content read above — no new frontmatter parser written.

**Self-declared count (`gates/spawn_on_pr.py`):**

- `PR_TRIGGERED_RECORD_KINDS` deleted.
- `REQUIRED_INDEPENDENT_VERIFICATIONS = 2` added — a count, not a
  vocabulary.
- `verifying_record_count(subject_board, subject_author=None)` added —
  counts board entries with `verifies_subject: true` (frontmatter) and
  `author:` different from `subject_author`. No `kind:` value, filename,
  or skill name participates. Reuses the existing self-verification guard
  unchanged in spirit (acceptance bullet 3).
- `_filter_execution_observation()` deleted entirely, and its call site in
  `missing_verification()` removed (operator ruling: the skip-eligibility
  exemption goes, not re-expressed under another name or as a reduced
  threshold).
- `applicable_record_kinds()` kept, but re-scoped: it no longer backs the
  merge-gating check (nothing in `merge_gate.py` calls it anymore) — its
  sole remaining caller is `missing_verification()`/
  `spawn_missing_for_pr()`'s auto-spawn tick, which still needs concrete
  role identity to invite a session. Its `kinds` default changed from the
  deleted constant to `AUTO_SPAWN_ROLES` (see "Why" for why this survives
  as a live-code exception to acceptance bullet 4).
- `subject_deliverable_branch()`/`_implementation_session_active()`:
  their `PR_TRIGGERED_RECORD_KINDS` exclusion-set reference swapped to
  `AUTO_SPAWN_ROLES` (same values, same purpose — excluding the two
  auto-spawned observer branches/roster entries to isolate the
  deliverable).

**`gates/skip_eligibility.py`:**

- `classify_for_subject()`, and its now-orphaned private helpers
  (`_numstat`, `_deleted_paths`, `read_record_text`, `_ref_resolvable`),
  deleted entirely — not just the two dead `"implementation"` fallback
  strings the design doc flagged (its sole production caller,
  `_filter_execution_observation()`, is deleted above). derived: `grep -rn
  classify_for_subject --include=*.py .` this session → only the
  definition line in `gates/skip_eligibility.py` remains, zero other
  callers. The `gates.py` sibling-import machinery (the
  `_GATES_IMPL_KEY`/`importlib` block) and the now-unused `subprocess`
  import removed with it.
- `classify_rows`/`non_docs_lines_changed`/`hard_to_revert_hit`/
  `claim_vocabulary_hit` untouched — `gates/trivial_lane_gate.py` imports
  these directly, unrelated to the deleted per-subject wrapper. derived:
  `python3 -c "import sys; sys.path.insert(0,'gates'); import
  trivial_lane_gate"` this session → succeeds, no import error.

**Tests:**

- `test/test_merge_gate_record_kind.py` fully rewritten:
  `VerifyingRecordCountTest` (counting, self-verification guard, no
  kind/filename participation), `OwnPrSuppliesVerificationTest`
  (qualifying/non-qualifying/self-authored/no-context cases, plus a
  regression-lock assertion that the `git show` ref is `origin/<branch>`,
  never the bare name), `RequiredVerificationMissingIntegrationTest`
  (the load-bearing refusal, the two-qualifying-records satisfied case,
  and the two-self-authored-records-still-refuses case — acceptance
  bullets 2 and 3 directly). derived: `python3 -m pytest
  test/test_merge_gate_record_kind.py -q` this session → `13 passed in
  0.83s`.
- `gates/test_spawn_on_pr.py`: its `ROLE` test fixture constant renamed
  from the arbitrary `"execution-observation"` to `"generic-role"` —
  purely a mocked/opaque value in that file (monkeypatches
  `missing_verification` wholesale), no behavior change, removes an
  incidental bullet-4 grep hit. derived: `python3 -m pytest
  gates/test_spawn_on_pr.py -q` this session → `10 passed in 0.92s`.

**Docs (not under `docs/issue-*/reports/`, so in scope — the standing
operator decision only excludes issue-record content):**

- `docs/specs/enforcement-boundary.md`: the `merge_gate.py`,
  `spawn_on_pr.py`, and `skip_eligibility.py` rows updated to describe the
  current (post-#2609) mechanism instead of the superseded kind-matching
  one.
- `docs/handbooks/observer-verification.md`: substantially rewritten —
  "Current mechanism"/"Self-verification guard"/"What #2609 did NOT
  change" sections describe today's behavior; the old content is kept
  under a new "History: stage 5's kind-matching (superseded)" section
  rather than deleted, since it's the accurate historical record of what
  #2233/#2380/stage-5 built and why. Added a rollback-safety caveat this
  handbook didn't need before: reverting the code without also accounting
  for the record contract change (`verifies_subject:` is new; existing
  landed kind-matched records don't carry it) is not safe by itself.
- `python3 gates/spec_index.py --update` attempted per contract v3's
  docs/specs/* regeneration rule. derived: executed this session → fails
  with `FileNotFoundError: .../roles/specs/brand-design.spec.json`.
  derived: `git log --oneline -3 -- roles/` this session → top entry
  `480d1a78 issue-2539: Stage 6C -- consolidate roles/ into
  spawn_roles.json, delete roles/ + roles/specs/` — `roles/` was already
  deleted repo-wide before this session started, so
  `docs/specs/reconciled-index.md` was already stale against that
  deletion, a pre-existing condition not caused by this session. Not
  fixed here — `docs/specs/reconciled-index.md` left unchanged.

## Why

canonical: `docs/issue-2593/reports/architecture-module-boundary-definition+
architecture-decomposition-strategy-386ff408.md` (Option 2, the rejected
kind-presence-alone alternative, and the Open finding 1 fork), plus the
issue #2609 body's operator ruling — both read this session; skill-tool
output for both mounted skills, invoked directly this session.

### Reused the upstream design, did not re-derive it

Per the issue's own instruction, Option 2 (self-declared boolean +
count threshold) was not revisited. `verifying_record_count()`/
`REQUIRED_INDEPENDENT_VERIFICATIONS` implement it as specified: a count,
not a vocabulary, reusing the existing self-verification guard rather
than writing a second one (acceptance bullet 3's own instruction).

### The operator ruling changed the scope of "Issue A" from what the design assumed

canonical: `gh issue view 2609` body, read this session — the "Operator
decision on the design's Open finding 1" section, quoted in "What was
done" above ("every subject is subject to the same count requirement...
the exemption goes").

The design's own Stage A description assumed Open finding 1 (the
skip-eligibility fork) would be resolved by *converting* the exemption's
effect ("excuse this named kind" → "need one fewer independent check, any
kind" — see the design's "behavior-change cost" paragraph, sha
483d106dba5d77dac0273b9c24be314de265474d). The operator ruling instead
closed it the other way: the exemption goes, full stop, "every subject
takes the same count requirement." This is why
`_filter_execution_observation()` is deleted outright rather than
rewritten to shrink `REQUIRED_INDEPENDENT_VERIFICATIONS` for
skip-eligible subjects — a threshold-reduction carve-out would have been
exactly the "kind-specific exemption under another name" the ruling
forbids, since `classify_for_subject()`'s three axes are inherently about
whether a change needs an execution-observation-*flavored* check
specifically.

### The sibling-cycle break had to be redesigned, not just renamed

canonical: `gates/merge_gate.py`'s pre-session `_exempt_own_record_kind()`
(deleted this session; the version read and analyzed is the one this
session's own `git diff` shows as removed) and its test coverage in
`test/test_merge_gate_record_kind.py`'s prior
`ExemptOwnRecordKindTest.test_sibling_observer_pair_both_exempt`, both
read directly this session before rewriting.

The old `_exempt_own_record_kind()` dropped the *entire* two-kind set from
`missing` whenever the evaluated PR's own branch suffix was one of the
two named kinds — a hack that only works because there are exactly two
required names and each one's presence implies "the other one is my
sibling, don't wait on it." Under a kind-free count, there's no "the
other one" to infer; there's just a number. A naive translation (own PR
supplies 1 → count += 1) reproduces the exact deadlock it used to break:
two sibling PRs, each seeing `board count (0, nothing landed) + own
bonus (1) = 1 < 2 required`, neither able to merge first. Read directly
via `git show` and applying architecture-interface-contract-shape rule 12
("hide design decisions that are likely to change, expose only the
minimal contract needed"), `_own_pr_supplies_verification()` instead
exempts the evaluated PR outright when it itself qualifies: landing a
verification-supplying PR can only help the count, never hurt it, so
blocking it on the very number it's about to increase serves no purpose
— true for any threshold, not just two.

### `verifies_subject: true` as a Published Language (skill-verdict basis)

canonical: Skill-tool output for `architecture-interface-contract-shape`,
loaded directly this session (rules 8/11b/12 cited below).

Per architecture-interface-contract-shape rule 8, the closed two-name
match is replaced by an Open Host Service-shaped contract: any producer,
regardless of skill or `kind:`, emits the same self-declared boolean
field, and the one consumer (`merge_gate.py`) reads only that field plus
`author:` — no bespoke per-producer negotiation. Rule 11b (delete
interface surface with zero live callers) is why `classify_for_subject()`
and its four private helpers are deleted rather than left "just in case"
once their sole caller was removed. derived: `grep -rn
classify_for_subject --include=*.py .` this session, run before deleting
— confirmed zero callers outside `gates/skip_eligibility.py` itself
before the deletion was made, not assumed.

### `AUTO_SPAWN_ROLES` — a deliberate, named, live-code exception to acceptance bullet 4

canonical: `gates/spawn_on_pr.py`'s own module docstring ("10개
board_condition 역할 중... 2개만 대상이다"), read this session, and the
issue #2609 body's `## Non-goals` section ("The `역할:` catalog and
`spawn_roles.json`... filed separately"), read via `gh issue view 2609`
this session.

Acceptance bullet 4's empty state ("remaining hits are comments or
documentation citations only, each named in the record") is not fully met
by this delivery. derived: `grep -rnE
'"(implementation|coding|execution-observation|conformance-review)"'
--include=*.py gates/ *.py` this session, after all other changes in this
record landed → 5 hits: `gates/skip_eligibility.py:85` (comment citing
the deleted fallback strings by name, a documentation citation),
`gates/spawn_on_pr.py:50`, `gates/spawn_on_pr.py:188` (docstring citation
of a historical dead lookup, a documentation citation),
`gates/spawn_on_pr.py:203`, and `spawn.py:748`. Three of the five are live
code, not comments/docs:

1. `gates/spawn_on_pr.py:50` — `AUTO_SPAWN_ROLES = ("execution-observation",
   "conformance-review")`.
2. `gates/spawn_on_pr.py:203` — `subject_deliverable_record()`'s
   `kind_field == "implementation"` single-kind match.
3. `spawn.py:748` — the `LEGACY` filename dict (`"conformance-review":
   "review-record.md"`, etc.).

(2) and (3) are outside this issue's mechanism entirely: (2) identifies
*the* deliverable record (there is exactly one kind by definition, not a
vocabulary of interchangeable names), explicitly called out in the design
(sha 483d106dba5d77dac0273b9c24be314de265474d) as machinery "reused
unchanged"; (3) is contract-v1-to-v2 legacy filename detection, predating
and unrelated to the observer-pair axis.

(1) is the one that needed a real decision. `spawn_on_pr.py`'s auto-spawn
tick (`missing_verification`/`spawn_missing_for_pr`) must invite a
*concrete* role/skill by name — `spawn._spawn_one(cwd, role, task, ...)`
has no way to spawn "any qualifying producer," only a named one. This
file's own docstring states its scope is narrowly the 2-of-10
`board_condition` roles that are mechanically presence-checkable by
commit-landed-and-record-absent alone; the other 8 are handled by
different, content-classifying machinery elsewhere. Sourcing the two
names from `spawn_roles.json`'s existing `record_absent_for` metadata
instead of a local tuple was considered and rejected. derived: `grep -n
'"record_absent_for"' spawn_roles.json` this session → 10 hits (10 roles
carry that field, not 2), so reproducing "which of these 10 are the 2
mechanically presence-checkable ones" from generic JSON fields would
re-derive undocumented judgment already baked into this file's narrow
scope, touching `spawn_roles.json` consumption — issue #2610's stated
separate surface ("retiring spawn_roles.json and the 44-entry catalog"),
not absorbed here per this issue's own coordination instruction.

The decision made: keep `AUTO_SPAWN_ROLES` as a small, explicitly-scoped,
clearly-documented constant used *only* for spawn-target selection —
structurally and functionally decoupled from the merge-gating obligation.
derived: `grep -nE
'"(implementation|coding|execution-observation|conformance-review)"'
gates/merge_gate.py` this session → 0 hits — `merge_gate.py` reads zero
role names, zero kind values, anywhere, after this change. This is not
the "kind-specific exemption under another name" the operator ruling
forbids — that prohibition is about the skip-eligibility *exemption*
(deleted, not renamed); a role-invitation list is a different kind of
decision (who gets asked to produce something) from an obligation check
(who counts once produced). But it is honestly a "closed set of names
decid[ing] which session is spawned next" in bullet 1's own descriptive
framing, so this record states it plainly rather than let the grep
numbers imply full closure. Full removal of named role selection here is
coordinated with, not duplicated into, issue #2610.

### silent-failure-audit: caught and fixed a real defect in this session's own new code

canonical: this session's own diff to `gates/merge_gate.py`
(`_own_pr_supplies_verification()`, written and then corrected within
this same session, before any commit) and
`gates/check_runner.py::checkout_pr_worktree()`/
`fetch_all_role_branches()`, read directly this session to establish the
`origin/<branch>` convention.

Invoked after writing `_own_pr_supplies_verification()`. Trace: the
function's `git show` call originally read `f"{own_branch}:docs/issue-
{issue_num}/reports/{slug}.md"` — the bare branch name. `repo` here is
the orchestrator checkout `evaluate()`/`main()` operate against
(confirmed via `check_runner.checkout_pr_worktree()`'s own docstring: "PR
#`pr`의 head 커밋을 `repo`(오케스트레이터 체크아웃, `origin` 리모트를
가짐)에서 fetch"), which has no local branch of that exact name — only
`origin/<branch>`, mirrored by `check_runner.fetch_all_role_branches()`
(already called once at the top of `evaluate()`). `checkout_pr_worktree()`
itself reads `origin/{head_ref}`, never bare `head_ref`, for the
identical resolution problem. The bare-name version would have made
`_own_pr_supplies_verification()` return `False` on every call in
production (git show failing to resolve the ref), silently and
permanently defeating the cycle-break it exists for — never wrong in the
sense of approving a bad merge, but the sibling-deadlock regression
described above would have shipped live, undetected, because the
function's own fail-closed default (`False` = "no exemption, fall
through to the normal count") looks identical whether the branch
genuinely doesn't qualify or the ref just never resolved. Classification:
would have been Silently Absorbed (default-value substitution — `False`
— without recording that resolution failed, silent-failure-catalog
pattern) had it shipped; fixed before commit to `origin/{own_branch}`,
matching `checkout_pr_worktree()`'s established convention, with a
regression-lock assertion in the test. derived: `python3 -m pytest
test/test_merge_gate_record_kind.py::OwnPrSuppliesVerificationTest -q`
this session, after the fix → `3 passed`, including the assertion that
the `git show` argument contains `origin/<branch>:`.

No other new/changed error-handling site in this diff was found Silently
Absorbed. canonical: `gates/merge_gate.py`'s `pr_refs()`/
`latest_check_runner_comment()`/`staleness()`, read directly this session
to compare conventions. `_own_pr_supplies_verification()`'s remaining
`returncode != 0 -> return False` and `verifies_subject != "true" ->
return False` paths are the same fail-closed no-op shape the deleted
`_exempt_own_record_kind()` used for its `own_branch=None`/other-subject
cases (a real absence, not a masked one, now that the ref resolves
correctly); no try/except was added around the `subprocess.run` call
itself (a `git`-binary-missing `FileNotFoundError` would propagate
uncaught) — checked against sibling functions in the same file and found
consistent with this codebase's existing convention of treating
git/gh-binary presence as an environment precondition, not a fallible
operation to guard, not a new gap this diff introduces.

### Skill verdicts

skill-verdict: architecture-interface-contract-shape — applied: invoked; used rule 8 (Open Host Service/Published Language) to justify `verifies_subject: true` as the boundary contract shape (any producer, one consumer, no per-producer negotiation), rule 11b (delete interface surface with zero live callers) to justify deleting `classify_for_subject()`/its helpers outright rather than leaving them after their sole caller was removed, and rule 12 (hide likely-to-change decisions, expose the minimal contract) to justify `_own_pr_supplies_verification()`'s outright-exemption shape over a naive +1-credit translation of the old mechanism.
skill-verdict: silent-failure-audit — applied: invoked; audited this session's own new error-handling site (`_own_pr_supplies_verification()`'s `git show` call) and found a real Silently-Absorbed-shaped defect (bare branch name never resolves against the orchestrator checkout, silently and permanently defeating the cycle-break) — fixed to `origin/{own_branch}` before commit, with a regression-lock test assertion; the function's remaining fail-closed paths and the unguarded `subprocess.run` call were checked against this file's sibling functions and found consistent with existing convention, not new gaps.

## What did not work

canonical: this session's own working diff to `gates/merge_gate.py`,
edited and corrected within this same turn before any commit. derived:
`python3 -m pytest test/test_merge_gate_record_kind.py::OwnPrSuppliesVerificationTest
-q` this session, after the fix → `3 passed` (same command/result cited
under "Why" → silent-failure-audit above).

None in the sense of a written-then-reverted change surviving to commit.
One in-session self-correction: `_own_pr_supplies_verification()`'s first
draft read the bare branch name from `git show` (see "Why" →
silent-failure-audit above, same citations apply). The silent-failure-audit
pass found this before this record was written or any commit made; fixed
in place, not left as a deviation from a prior approved shape (this is a
build-now, single-phase delivery with no separate phase-1 proposal to
diverge from).

## Upstream basis

canonical: `docs/issue-2593/reports/architecture-module-boundary-definition+
architecture-decomposition-strategy-386ff408.md`, opened directly via
`Read` this session. derived: `git log --format=%H -1 -- <that path>`
this session → `483d106dba5d77dac0273b9c24be314de265474d` (landed in a
prior commit, not this one).

- `docs/issue-2593/reports/architecture-module-boundary-definition+
  architecture-decomposition-strategy-386ff408.md` (sha
  483d106dba5d77dac0273b9c24be314de265474d) — the design this issue
  implements Option 2 of; not re-derived, per the issue's own
  instruction.
- `gh issue view 2609` body — the operator ruling on the design's Open
  finding 1 (skip-eligibility exemption removal), and the acceptance
  checks this record's live demonstrations answer directly.

## Open findings

canonical: this session's own script output comparing old vs. new
verification counts across `spawn.board(root)`, and `gh issue view <n>
--json state -q .state` for each affected subject, both executed this
session (full command text and counts in the finding below).

1. **34 closed subjects would show 0 qualifying records under the new
   mechanism despite having satisfied the old kind-matching one, with no
   currently-open subject affected.** derived: a script (this session)
   comparing, per subject in `spawn.board(root)`, the old kind-matching
   count (`kind:`/filename in `AUTO_SPAWN_ROLES`, author differs) against
   the new `verifying_record_count()` → 34 subjects had old_count>=2,
   new_count<2 (none carry `verifies_subject:`, a field that didn't exist
   before this session). derived: `gh issue view <n> --json state -q
   .state` for all 34 (issue-2138, -2227, -2285, -2286, -2288, -2291,
   -2293, -2333, -2348, -2379 through -2383, -2393, -2395, -2402, -2403,
   -2409, -2412 through -2414, -2417, -2431, -2432, -2443, -2447, -2451,
   -2463, -2467, -2479, -2488, -2509, -2516) — all 34 return `CLOSED`,
   this session. Since a closed subject's PRs have already all merged,
   `required_verification_missing()` has nothing left to re-evaluate for
   it, so this is not a live blocker today. It is a real, structural
   transition cost of the mechanism (landed pre-#2609 records don't carry
   the new field, and `docs/issue-*/reports/` is never migrated to add
   it): a subject that happens to reopen, or any future subject whose
   deliverable PR is still open at the exact moment this change lands
   while its observer PRs already landed under the old kind-matching
   rules, would see its already-satisfied verification reset to 0 and
   need newly-written qualifying records. Not resolved here — resolving
   it would mean either migrating old records (forbidden by this issue's
   own `must not:`) or adding a legacy-compatibility read path (risks
   re-introducing exactly the kind-matching this issue removes). Flagged
   for the operator to decide whether this residual risk needs a
   time-boxed follow-up or is accepted as part of the stated cost.
2. **`AUTO_SPAWN_ROLES`'s full removal (making `spawn_on_pr.py`'s
   auto-spawn tick genuinely kind-free) is coordinated with, not resolved
   by, this issue** — see "Why" above (the `AUTO_SPAWN_ROLES` subsection,
   same citations apply). Needs issue #2610's `spawn_roles.json`/
   role-catalog surface, or a follow-up that generalizes role-selection
   independently of that catalog; this record does not propose which.

## Next steps

`loop_state: landed` — this record is terminal for this session. Two
follow-up candidates are not undertaken in this session, left for
whoever picks up the two items under "Open findings" above: a decision on
whether the closed-subject transition gap needs active mitigation, and
`spawn_on_pr.py`'s auto-spawn role-selection generalization coordinated
with issue #2610.
