# Observer verification: self-declared, counted (issue #2609)

## Scaffolding: the field arrives by construction

`gates/directive_assembly.py`'s `_stamp_additive_record_fields()` -- the
single call site every additive record-field stamp goes through, already
used for `author:` -- stamps a `verifies_subject: false` line into
*every* session's record skeleton at bootstrap (`write_record_skeleton()`),
regardless of role/skill/kind. A session no longer has to know from this
handbook that the field exists at all; it is already sitting in the
frontmatter of the file it is editing. What stays 100% self-declared is
the *value*: a session whose own work is an independent verification of
its subject flips `false` to `true` itself before committing, per the
guidance below. Nothing branches on a role/skill name to decide the
default -- keying the stamp off `role` would reintroduce, one layer up,
exactly the closed set #2609 deleted from the merge-gating check itself.

`gates/merge_gate.py`'s `required_verification_missing()` — the check a
PR cannot merge without passing — gates on a self-declared, counted
field. It used to key off a closed set of `kind:` values (stage 5 of
issue #2241's role-axis retirement, see "History" below); issue #2609
removed that closed set entirely, per the design in
`docs/issue-2593/reports/architecture-module-boundary-definition+
architecture-decomposition-strategy-386ff408.md` (Option 2).

## Current mechanism

`gates/spawn_on_pr.py`:

- `REQUIRED_INDEPENDENT_VERIFICATIONS = 2` — a count, not a vocabulary.
  It says how many independent checks a subject needs, never which ones.
- `verifying_record_count(subject_board, subject_author)` counts board
  entries whose frontmatter carries `verifies_subject: true` and whose
  `author:` differs from `subject_author`. No `kind:` value, filename,
  or skill name participates — any record may self-declare
  `verifies_subject: true`, the same self-declaration pattern already
  used for `author:`.

`gates/merge_gate.py`:

- `required_verification_missing()` computes
  `max(0, REQUIRED_INDEPENDENT_VERIFICATIONS - verifying_record_count(...))`
  and returns that deficit (`0` when satisfied). The refusal reason
  printed by `evaluate()`/`main()` names the mechanism
  (`required_verification_missing()`) and the count it saw, e.g. `"1/2개
  확인됨 (1개 더 필요)"`.
- `_own_pr_supplies_verification()` replaces the old
  `_exempt_own_record_kind()`'s branch-suffix exemption (see "History").
  It reads the PR-under-evaluation's own branch content directly (`git
  show origin/<branch>:docs/issue-<n>/reports/<slug>.md`, since the
  branch is not yet landed and `spawn.board()` has nothing to join
  against) and, if that record itself qualifies
  (`verifies_subject: true`, author differs from the subject's
  deliverable author), exempts this PR from the check outright: landing
  a verification-supplying PR can only help the subject meet the
  requirement, never hurt it, so blocking it on the very count it is
  about to increase serves no purpose.

## Self-verification guard (unchanged in spirit)

Presence of `verifies_subject: true` is not sufficient — the record
also has to have been produced by someone other than the subject's own
deliverable author. This is the same guard stage 5 built for `kind:`
matching, carried over unchanged: a qualifying record whose `author:`
equals the subject's own `author:` does not count toward the
requirement. `subject_author` is looked up once from the subject's own
deliverable record (`spawn_on_pr.subject_deliverable_record()`,
unchanged by #2609); if that record or its `author:` field is absent,
the guard is skipped rather than treating every match as suspect.

## What #2609 did NOT change

- `spawn_on_pr.py`'s own auto-spawn tick (`missing_verification`/
  `spawn_missing_for_pr`) still invites two fixed named roles
  (`AUTO_SPAWN_ROLES`, same two values `PR_TRIGGERED_RECORD_KINDS` used
  to hold) when a subject hasn't landed a qualifying record yet — a
  role-selection decision (which skill to invite), structurally
  distinct from the merge-gating obligation check above, which no
  longer reads this list or any kind/name at all. Generalizing or
  removing named role selection here is issue #2610's separate surface
  (`spawn_roles.json` / the role catalog's retirement).
- `subject_deliverable_record()`'s single-kind `implementation` match
  (identifying the subject's own deliverable record, as opposed to an
  observer's) — unrelated to the two-kind observer axis this issue
  removed, reused unchanged.
- The `skip_eligibility.py::classify_rows`/`hard_to_revert_hit`/etc.
  three-axis classifiers `trivial_lane_gate.py` still uses directly —
  only the per-subject wrapper (`classify_for_subject()`, whose sole
  caller was the now-deleted execution-observation skip-eligibility
  exemption) is gone.
- The scaffolding stamp above (`_stamp_additive_record_fields()`) does
  not read `spawn_roles.json`'s `record_fields`/`record_spec` — that is
  a separate call site in `write_record_skeleton()` (the `spec_lines`
  block) which issue #2610 is scheduled to retire. The stamp is keyed
  on nothing but "a record skeleton is being written," so #2610's
  retirement of `spawn_roles.json` does not invalidate it.
- Records that landed before this scaffolding existed, or before #2609
  at all, are not amended — `docs/issue-*/reports/` is never migrated
  (standing operator decision). A subject whose only candidate
  verifying records predate the field still shows 0 qualifying records
  until a newly-written record supplies one; this scaffold changes what
  new records default to, not what old ones say.

## History: stage 5's kind-matching (superseded)

Issue #2241 stage 5 (`docs/issue-2241/proposals/2026-08-25-stage-5-
observer-record-kind.md`) replaced a hardcoded two-role-name match
(`PR_TRIGGERED_ROLES`) with a two-`kind:`-value match
(`PR_TRIGGERED_RECORD_KINDS`), matching an entry's `kind:` frontmatter
OR (as a legacy fallback) its filename stem against
`("execution-observation", "conformance-review")`. Stage 5's own
proposal explicitly deferred the question of *whether* two named kinds
should decide the obligation at all — issue #2609 is that deferred
question, decided by closing it: no `kind:` value, filename, or skill
name decides the obligation anymore, replaced by the self-declared
counted mechanism above. `_exempt_own_record_kind()` (stage 5's
circularity-breaker, itself a stage-2 rename of `_exempt_own_role`) is
deleted; `_own_pr_supplies_verification()` above replaces it.

An execution-observation-specific skip-eligibility carve-out
(`gates/skip_eligibility.py`'s three-axis size/reversibility/claim-
vocabulary classification, wired in via `spawn_on_pr.py`'s
`_filter_execution_observation()`) also existed alongside stage 5's
kind-matching, exempting some low-risk subjects from needing an
execution-observation record specifically. Issue #2609's operator
ruling on its own Open finding 1 removed this exemption entirely rather
than converting it to a kind-free equivalent ("every subject takes the
same count requirement") — `_filter_execution_observation()` and
`classify_for_subject()` (its sole caller) are both deleted.

Reverting to the stage-5 kind-matching version is **not** safe without
also reverting the record contract: `verifies_subject: true` is a new
field, so records written only under the current mechanism would not
satisfy a reverted kind-matching check (they may lack a recognized
`kind:` value or filename). Records written before #2609 that already
carry a required `kind:` value do satisfy the current mechanism only if
they are also amended to carry `verifies_subject: true` going forward —
existing landed records are not retroactively rewritten (`docs/issue-*/
reports/` is never migrated), so a subject whose two observer records
landed before #2609 needs newly-written qualifying records to satisfy
the count-based check.
