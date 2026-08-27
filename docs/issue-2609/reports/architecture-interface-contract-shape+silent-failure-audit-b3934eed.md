---
issue: 2609
role: architecture-interface-contract-shape+silent-failure-audit-b3934eed
author: architecture-interface-contract-shape+silent-failure-audit-b3934eed
skills: architecture-interface-contract-shape (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
loop_state: landed
upstream:
  - path: docs/issue-2593/reports/architecture-module-boundary-definition+architecture-decomposition-strategy-386ff408.md
    sha: 483d106dba5d77dac0273b9c24be314de265474d
  - path: gates/merge_gate.py
    sha: 7236e3158f1570458301f5ef681642546899cdda
  - path: gates/spawn_on_pr.py
    sha: 7236e3158f1570458301f5ef681642546899cdda
  - path: docs/issue-2609/reports/architecture-interface-contract-shape+silent-failure-audit-ded46e17.md
    sha: 7236e3158f1570458301f5ef681642546899cdda
  - path: directive_assembly.py
    sha: ddde5afce98fa537a10970888bf1da85c6f2354c
  - path: docs/handbooks/observer-verification.md
    sha: ddde5afce98fa537a10970888bf1da85c6f2354c
  - path: test/test_verifies_subject_scaffold.py
    sha: ddde5afce98fa537a10970888bf1da85c6f2354c
---

# issue-2609 — architecture-interface-contract-shape+silent-failure-audit-b3934eed record

## What was done

Wires `verifies_subject` so it arrives by construction, closing the gap
named in the landing comment posted after PR #2615 merged: the
merge-gating mechanism (`gates/merge_gate.py:173`,
`gates/spawn_on_pr.py:76`) already read the field, but nothing wrote it —
a session authoring a verifying record had to know from
`docs/handbooks/observer-verification.md` that the key existed at all.

canonical: `gh issue view 2609 --comments` output, read this session —
the landing comment states "nothing emits the field... So the remaining
work on this issue: make the field arrive by construction, not by a
session remembering the handbook."

`directive_assembly.py::_stamp_additive_record_fields()` — the single
call site every additive record-field stamp already goes through for
`author:` — now also stamps `verifies_subject: false` into every
session's record skeleton at bootstrap, regardless of role/skill name.
This is the same call site `write_record_skeleton()` uses for every real
role/skill record. A session no longer has to consult the handbook to
discover the field exists; it is already sitting in the frontmatter of
the file being edited. The *value* stays 100% self-declared — a session
whose own work is an independent verification of its subject flips
`false` to `true` itself before committing; nothing in the scaffold
inspects role name, skill name, or task text to decide that for it.

`docs/handbooks/observer-verification.md` documents the new scaffolding
section, the `spawn_roles.json`/#2610 non-dependency, and the
historical-records non-migration explicitly (see "Why" below for both).

derived: `git show ddde5afc --stat` this session ->
```
directive_assembly.py                             |  25 +++++++++++++++++++++++++-
docs/handbooks/observer-verification.md            |  27 +++++++++++++++++++++++++++
test/test_verifies_subject_scaffold.py             | 134 ++++++++++++++++++++++++++++++
3 files changed, 185 insertions(+), 1 deletion(-)
```

## Why

### Decision 1 — what determines a record should carry the field: presence is universal, the value stays self-declared

canonical: this session's own spawn task text (unchanged since session
start, no re-fetch needed), which states verbatim: "verifies_subject is
a self-declaration by design (#2605's Option 2) — so scaffolding it
must not turn into a new closed set of names deciding who declares it.
If your approach reintroduces an enumeration of which sessions verify,
it has failed the same test #2615 just passed."

Two shapes were available:

- **Rejected: key the stamp off `role`/skill name** (e.g. only stamp
  `true` for roles literally named `execution-observation` or
  `conformance-review`, or only stamp the *key* for those two). This
  reintroduces, one layer up in the scaffold, exactly the closed
  two-name set `PR_TRIGGERED_RECORD_KINDS` used to be — the merge gate
  itself would stay kind-free, but "which sessions even get offered the
  field" would not. It also cannot generalize: role is a free-form slug
  under slug identity, not validated against any closed role set — this
  very session's own role
  (`architecture-interface-contract-shape+silent-failure-audit-b3934eed`)
  matches no legacy role name. derived: `grep -n "free-form slug" -A3
  directive_assembly.py` this session ->
  ```
  # issue #2575: `role` is a free-form slug under slug identity (#2555)
  # and is never validated against a closed role set any more (#2555/
  # #2560/#2561) — a literal name match against a fixed tuple can no
  # longer answer "is this a code-producing session" (it never matches
  ```
  A name-keyed stamp would silently never fire for slug-axis sessions —
  the same failure mode this pre-existing comment (in
  `write_record_skeleton()`, unchanged by this session) already
  documents ruling out a role-name check for "is this a code-producing
  session."
- **Adopted: stamp the key into every skeleton, universally, default
  `false`.** `write_record_skeleton()` is called at bootstrap for
  every role/skill session regardless of what it will produce — most
  records are not independent verifications of their subject, so
  `false` is the safe default (identical to a record that never got the
  field at all, from `merge_gate.py`'s point of view: `!= "true"` does
  not count either way — verified by
  `EndToEndMergeGateTest.test_zero_qualifying_records_refuses_naming_the_count`
  below). What changes is that the *key's presence* is now
  unconditional, not gated by any name/content signal. The session
  decides the *value* — self-declaration stays entirely about content.

Per architecture-interface-contract-shape rule 8 (Open Host Service +
Published Language), `verifies_subject: true` is already the boundary
contract between arbitrary producers and the one consumer
(`merge_gate.py`) — this session extends that same contract's producer
side (the scaffold that offers the field) without adding any
per-producer negotiation (no role list decides who gets it). Rule 12
(hide likely-to-change decisions, expose the minimal contract) is why
the scaffold's default is a bare `false`, not a heuristic guess at
`true`/`false` based on task text or spawn context — computing that
guess would require exposing (and getting wrong) a classification this
skill's own catalog of context-mapping patterns treats as inherently
unstable, whereas "every record gets the key, default false" is the
minimal, stable surface.

### Decision 2 — historical records: not touched, not backfilled

canonical: `gh issue view 2609` body, read this session — the
`## Acceptance` section's "must not" bullet: "do not rename, migrate or
rewrite any record under `docs/issue-*/reports/` — standing operator
decision." canonical: `docs/issue-2609/reports/architecture-interface-
contract-shape+silent-failure-audit-ded46e17.md`, read this session ->
```
1. **34 closed subjects would show 0 qualifying records under the new
   mechanism despite having satisfied the old kind-matching one, with no
   currently-open subject affected.** derived: a script (this session)
   comparing, per subject in `spawn.board(root)`, the old kind-matching
```

Per the standing operator decision and per the prior session's own
finding quoted above, this session makes no change to any existing
record under `docs/issue-*/reports/`. `verifies_subject` did not exist
as a concept before PR #2615 landed, so no record written before that PR
can carry it regardless of this session's scaffolding — the scaffold
only changes what *new* skeletons default to. A subject whose only
candidate verifying records predate the field (either predate #2609
entirely, or landed between #2615 and this session, before the scaffold
existed) still shows 0 qualifying records from those records; closing
that subject now requires a newly-written record (through the
now-scaffolded path) to supply a qualifying `verifies_subject: true`.
This is stated plainly in `docs/handbooks/observer-verification.md`'s
new "What #2609 did NOT change" bullet — derived: `grep -n "not
amended" docs/handbooks/observer-verification.md` this session -> 1 hit.

### Sequencing: does not read spawn_roles.json, unaffected by #2610

The task flagged that the record scaffold "currently reads
`record_fields`/`record_spec` from `spawn_roles.json`, which issue
#2610 will retire" and asked to say whether this delivery is invalidated
by that. It is not: `write_record_skeleton()`'s `spawn_roles.json` read
(the `spec_lines` block, `_sp.role_data().get(role, {}).get(
"record_spec")`) is a separate call site from
`_stamp_additive_record_fields()`, which this change extends. The new
`verifies_subject: false` stamp is keyed on nothing but "a record
skeleton is being written" — no `spawn_roles.json` lookup participates.
#2610 retiring `spawn_roles.json` does not touch this stamp; no
reordering is needed. derived: `git show ddde5afc -- directive_assembly.py`
this session — the only changed lines are inside
`_stamp_additive_record_fields()` and its docstring;
`write_record_skeleton()`'s `spec_lines` block (the actual
`spawn_roles.json` consumer) is untouched, confirmed by the diff hunk
boundaries (single hunk, `_stamp_additive_record_fields` only).

### Demonstrated end-to-end through the real construction path, not asserted

`test/test_verifies_subject_scaffold.py` (new, committed `ddde5afc`)
exercises `spawn.write_record_skeleton()` directly — the real path every
actual session's record goes through — rather than hand-built dicts:

- `ScaffoldStampsTheFieldUniversallyTest`: an arbitrary, never-enumerated
  role slug (`totally-unenumerated-slug-9f3a`) gets `verifies_subject:
  false` in its skeleton; the two legacy names
  (`execution-observation`/some other slug) get byte-identical
  treatment (no special-casing); `spawn.frontmatter()` reads the default
  as `"false"`; a respawn into an existing workspace never overwrites a
  session's own flip to `true` (`write_record_skeleton()`'s existing
  "never touch an existing record" guarantee, unchanged).
- `EndToEndMergeGateTest`: builds a real subject board on disk (real
  `git init`, real `write_record_skeleton()` calls, real
  `spawn.board()` read) and drives `gates/spawn_on_pr.py`'s
  `verifying_record_count()`/`REQUIRED_INDEPENDENT_VERIFICATIONS`
  exactly as `gates/merge_gate.py::required_verification_missing()`
  does:
  - `test_zero_qualifying_records_refuses_naming_the_count`: 0 records
    -> count is `2` (the refusal, reproducing acceptance bullet 2).
  - `test_one_scaffolded_record_flipped_true_still_refuses`: one
    scaffolded-then-flipped record from an arbitrary author
    (`reviewer-alpha-7c1d`, never `execution-observation`/
    `conformance-review`) -> `1` still missing.
  - `test_two_scaffolded_records_from_other_authors_satisfy_the_
    requirement`: two scaffolded-then-flipped records from two
    arbitrary, distinct, non-enumerated authors -> `0` missing, i.e. the
    merge is allowed on the strength of two such records — the
    load-bearing demonstration the task asked for.
  - `test_two_self_authored_scaffolded_records_still_refuse`: two
    scaffolded-then-flipped records both re-authored to match the
    subject's own deliverable author (`implementation`) -> still `2`
    missing (acceptance bullet 3, self-verification guard reused
    unchanged).

acceptance: `python3 -m pytest test/test_verifies_subject_scaffold.py -q`
— result:
```
........                                                                 [100%]
8 passed in 0.86s
```

Acceptance checks from the issue body, re-run against this session's own
tree (not assumed carried over from PR #2615):

acceptance: `grep -rn 'PR_TRIGGERED_RECORD_KINDS' --include=*.py .` —
result:
```
(0 hits)
```

acceptance: `grep -rnE '"(implementation|coding|execution-observation|conformance-review)"' --include=*.py gates/ *.py`
— result:
```
gates/skip_eligibility.py:85   (comment, pre-existing)
gates/spawn_on_pr.py:50        (AUTO_SPAWN_ROLES, pre-existing, documented non-goal)
gates/spawn_on_pr.py:188       (docstring, pre-existing)
gates/spawn_on_pr.py:203       (subject_deliverable_record, pre-existing, unrelated axis)
directive_assembly.py:582      (new: this session's own docstring, explaining why the
                                 stamp does NOT key on these two names -- a documentation
                                 citation, not a branch)
spawn.py:749                   (LEGACY filename dict, pre-existing, contract-v1-to-v2)
```
6 hits, all comments/docstrings, none a live branch in the merge-gating
path — one more than the ded46e17 record's 5, from this session's own
new comment naming the rejected alternative.

acceptance: `grep -rln 'verifies_subject' . | grep -vE 'gates/|issue-2609|test'`
— result:
```
directive_assembly.py
docs/handbooks/observer-verification.md
docs/specs/enforcement-boundary.md
docs/issue-2593/reports/architecture-module-boundary-definition+architecture-decomposition-strategy-386ff408.md
```
`directive_assembly.py` is new in this list — it now emits the field,
not just documents it.

acceptance: `python3 -m pytest test/ -q` — result:
```
342 passed, 15 failed
```
The same 15 fail identically on the pre-change tree. derived: `git
stash -u && python3 -m pytest test/ -q && git stash pop` this session ->
`15 failed, 334 passed` on the unmodified tree, same 15 test IDs
(`gh`/remote-fetch failures in a sandboxed checkout — `fatal: 리모트
저장소에서 읽을 수 없습니다`) — environment/network-dependent, not caused
by this diff.

### Skill verdicts

skill-verdict: architecture-interface-contract-shape — applied: invoked; used rule 8 (Open Host Service/Published Language) to justify extending the existing self-declared-field contract's producer side (universal scaffolding) rather than adding per-producer negotiation, and rule 12 (hide likely-to-change decisions, expose the minimal contract) to justify a bare `false` default over a heuristic guess at the value.
skill-verdict: silent-failure-audit — applied: invoked; audited this session's own diff to `directive_assembly.py`. derived: `git show ddde5afc -- directive_assembly.py | grep -E 'try:|except|catch'` this session -> 0 hits — the change is pure string construction with no new fallible operation and no new error-handling site, so there is nothing to classify; zero findings, not a skipped audit.

## What did not work

None.

## Upstream basis

See frontmatter `upstream:`. `docs/issue-2593/reports/architecture-
module-boundary-definition+architecture-decomposition-strategy-
386ff408.md` supplies Option 2 (not re-derived, per the issue's own
instruction, same as the prior session). `gates/merge_gate.py`/
`gates/spawn_on_pr.py` (PR #2615) supply the read side this session does
not reshape. `docs/issue-2609/reports/architecture-interface-contract-
shape+silent-failure-audit-ded46e17.md` supplies the prior session's own
record and its landing comment naming this session's exact scope.

## Open findings

None. acceptance: `python3 -m pytest test/test_verifies_subject_scaffold.py -q`
— result:
```
8 passed in 0.86s
```
The specific gap named in the landing comment ("nothing emits the
field") is closed by this session's scaffolding change: the same
command above demonstrates the field being produced through the real
`write_record_skeleton()` path and a merge passing on two such records
from non-deliverable authors (`EndToEndMergeGateTest.
test_two_scaffolded_records_from_other_authors_satisfy_the_requirement`).

## Next steps

None for this issue. Follow-on, out of this issue's scope per its own
`## Non-goals` and this record's sequencing note: issue #2610's
retirement of `spawn_roles.json` (unaffected by this change, see "Why"
above); the board's bracket rendering (Issue B of the design); the
consumer-visible vocabulary purge (#2600/#2601/#2139).
