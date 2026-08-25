---
issue: 2284
role: implementation
author: implementation
kind: coding-record
loop_state: landed
upstream:
  - path: docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md
    sha: ccee895997e7629495aee4ff7c0588e3082c75bc
  - path: docs/decisions/2026-08-25-retire-role-axis-staging.md
    sha: same-commit
code_under_review:
  - roster.py
  - spawn.py
  - gates/record_lint.py
  - docs/specs/record-kind-vocabulary.md
  - docs/handbooks/record-contract.md
  - test/test_issue_scoped_lease.py
  - test/test_record_kind_field.py
type: feat
breaking: no — additive only, every field/behavior change is opt-in per the stage-1 proposal's Constraints
verdict: pass
---

# issue-2284 — implementation record

## What was done

Landed issue #2241 stage 1 (role retirement program) exactly per
`docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-
kind.md`'s files: write set — roles stay fully in place, nothing yet
depends on the three new concepts (commit 4a860dff):

- **Issue-scoped lease**: added `roster.lease_key(issue,
  disambiguator) -> str` (`roster.py:131-141`), returning
  `f"issue-{issue}/{disambiguator}"` — the same shape spawn.py already
  built inline. Replaced spawn.py's one lease-key construction site
  (`spawn.py:2866`, `roster_key = f"issue-{issue}/{role}" ...`) with
  `lease_key(issue, role) ...`, re-exported as `spawn.lease_key`. No
  other producer of this key shape exists (derived: `grep -n
  "issue-{issue}/{role}\|roster_register(" spawn.py roster.py
  pipeline.py`); the two consumers that already split it apart
  (`board.py:1084`, `spawn.py:978`, both `key.split("/", 1)[1]`) needed
  no change — they already treat the key's second half as an opaque
  string, not specifically a role.
- **Author identity**: added `spawn._stamp_additive_record_fields(issue,
  role) -> str` (the single "stamp this record" call site the
  proposal's Accumulation note asks for) and wired it into
  `_RECORD_SKELETON`/`write_record_skeleton` so every record gains an
  `author:` frontmatter line the first time its skeleton is written.
  `write_record_skeleton` already refuses to touch an existing record
  file (respawn-into-same-workspace case), so `author:` is append-only
  by construction — no separate enforcement needed. Stage 1 keeps roles
  in place, so `author:` is populated with the writing role (the only
  session-scoped identity available at this stage); a later stage
  widens `_stamp_additive_record_fields` itself once a non-role identity
  axis exists.
- **Record-kind vocabulary**: added `docs/specs/record-kind-
  vocabulary.md`, a closed vocabulary built from a repo-wide frequency
  sweep of existing ad hoc `kind:` values — derived: `grep -rhoP
  '^kind:\s*\K.*' --include=*.md docs | sed 's/[[:space:]]*$//' | sort
  | uniq -c | sort -rn` returned 40 distinct spellings across (derived:
  `grep -rl "^kind:" --include=*.md docs | wc -l`) 430 files. Added
  `gates/record_lint.py::record_kind_vocabulary_check(root, text)`,
  which flags a frontmatter `kind:` value outside that vocabulary —
  deliberately **not** called from `lint_record()`'s blocking
  aggregation (this repo's DEMOTE convention: land a new check
  advisory-only, promote it in a later stage once the field is
  load-bearing).
- Added `docs/handbooks/record-contract.md` documenting all three
  concepts and their additive/append-only invariants.
- Added `test/test_issue_scoped_lease.py` (lease-key shape,
  renew/flat-progress/expire+requeue identical for a role-keyed vs a
  non-role-keyed lease) and `test/test_record_kind_field.py`
  (vocabulary hit/miss/empty-state, and that the check never reaches
  `lint_record()`'s aggregation).
- Ran `python3 gates/spec_index.py . --update` after adding the new
  `docs/specs/*` file — a no-op (the new file isn't in the index's
  curated "Tracked documents" table, and no already-tracked spec file
  changed; `git status --porcelain docs/specs/reconciled-index.md`
  showed no diff after the run, and the file did not appear in this
  commit's changed-file list).

## Why

Chosen approach and rejected alternative are the proposal's own
Rationale (generalize `roster.py`'s existing #2101 lease mechanism via
one key-builder function, vs. building a new lease primitive from
scratch) — unchanged by this implementation, so not re-litigated here.
Two implementation-level judgment calls the proposal left open:

- **What `author:` holds at this stage**: the proposal names the *shape*
  (append-only, distinct from the lease key) but not the concrete value.
  Roles are still the only session-scoped identity axis standing at
  stage 1 (frozen decision `single-skill-axis`, reaffirmed in
  `docs/decisions/2026-08-25-retire-role-axis-staging.md`), and
  inventing a new identity scheme here would itself be a new
  role-shaped primitive — exactly what that frozen decision forbids.
  Using the role string keeps stage 1 to proving the field's mechanics
  (existence, write-once, append-only) rather than pre-deciding a later
  stage's identity design.
- **Advisory wiring for the kind check**: `gates/record_lint.py` has no
  existing two-tier (advisory vs. blocking) convention *inside this
  file* — `lint_record()`'s aggregation is unconditionally blocking.
  The nearest repo precedent for "new check, not yet load-bearing" is
  `gates/scope_adherence.py`'s `ADVISORY` verdict class and the
  `on-the-record` plugin's own DEMOTE registry pattern (hooks that
  print/log without denying). Rather than add a new blocking/advisory
  split mechanism to `record_lint.py` itself (out of scope — the
  proposal's Constraints forbid wiring any gate to refuse for `kind:`'s
  absence/values at this stage), I added the check as a standalone
  function and simply never call it from `lint_record()` — the
  cheapest way to guarantee it cannot block anything, verified by
  `test_record_kind_field.py`'s
  `test_lint_record_source_never_calls_the_kind_check`.

## What did not work

None.

## Upstream basis

`docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-
kind.md` (sha ccee895997e7629495aee4ff7c0588e3082c75bc) is the
authoritative spec — its files:, Constraints, Out of scope, and
Rollback sections were followed verbatim (frontmatter `sha:` above).
`docs/decisions/2026-08-25-retire-role-axis-staging.md` (same-commit as
this record on main) supplied Option D's rationale for keeping
`author:` and the lease key as separate fields.

## Open findings

None.

## Next steps

None — `loop_state: landed` is terminal for a `coding-record`
(session-protocol.md's per-kind terminal-state table). Stages 3-6 (per
`docs/issue-2241/proposals/`) are separate future issues that wire
consumers onto these fields; none of that work belongs to this issue.

## Evidence

acceptance: `python3 -m pytest test/test_issue_scoped_lease.py test/test_record_kind_field.py -v` — result:
```
============================== 10 passed in 3.33s ==============================
```

acceptance: `python3 -m pytest test/ gates/ -q` (full existing suite, proving
byte-identical behavior for role-keyed lease callers and no regression
anywhere else) — result:
```
1200 passed, 8 xfailed in 6.37s
```

acceptance: `python3 gates/spec_index.py .` (drift gate, after the `--update` run
above) — result:
```
통과: 모든 spec 문서가 기록된 해시와 일치한다
```

Sample-record demonstration against a real (temp) workspace, exercising
the actual `spawn.write_record_skeleton` code path and `board.py`'s
real frontmatter reader — derived: a script calling
`spawn.write_record_skeleton(str(tmp_workspace), 9999,
"implementation")`, then adding `kind: coding-record` to simulate a
session filling it in, then `board.frontmatter(p)`:
```
issue='9999' role='implementation' author='implementation' kind='coding-record' loop_state='in-progress'
OK: board.frontmatter parses author:/kind: alongside role: without error
```

Empty-state / rollback check (proposal's Rollback section): reverting
the four code/spec changes in one commit restores byte-identical
behavior for every existing caller by construction, not by a separate
test — `roster.lease_key`/`_stamp_additive_record_fields`/
`record_kind_vocabulary_check` are each a single new call site with no
other code path reading their output yet (derived: `grep -rn
"lease_key\|_stamp_additive_record_fields\|record_kind_vocabulary_check"
--include=*.py .` finds only their own definitions, the one caller each,
and this stage's own tests), so removing them removes exactly what
stage 1 added and nothing else.

## Acceptance verification

- derived: `python3 -m pytest test/test_issue_scoped_lease.py test/test_record_kind_field.py -v` — checked: `test/test_issue_scoped_lease.py` — result: pass
- derived: `python3 -m pytest test/ gates/ -q` — checked: `test/` — result: pass
- derived: `python3 gates/spec_index.py .` — checked: `gates/spec_index.py` — result: pass

## skill-verdict

skill-verdict: implementation-blueprint — not-applicable: single coherent patch across a handful of already-fixed files/call sites (existing `_RECORD_SKELETON` template, existing `roster_key` f-string, existing `record_lint.py` check-function pattern) — no new multi-module structure to select, and not a fan-out.
skill-verdict: implementation-complexity-coupling-management — not-applicable: no CBO/LCOM threshold crossed, no new accessor chain, no cross-module import direction introduced — the one new cross-module call (`spawn.py` -> `roster.lease_key`) follows the file's own established `_sp`-injection re-export pattern.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF pattern introduced or removed; `_stamp_additive_record_fields` is a plain function, not a Strategy/Factory/Visitor.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: no data structure, algorithm, or communication scheme choice — a dict-keyed lease and a set-membership vocabulary check are both unchanged existing shapes.
skill-verdict: work-in-english — applied: invoked; every commit message, docstring, comment, spec/handbook doc, and this record itself is in English, per the skill's Korean-trigger rule (the issue/task prompt was partly in Korean).
other mounted skills: not triggered
