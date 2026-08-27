---
issue: 2629
role: technical-writing-structure-comprehension+silent-failure-audit-c1414f3e
author: technical-writing-structure-comprehension+silent-failure-audit-c1414f3e
skills: technical-writing-structure-comprehension (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: gh issue view 2629 (body + correcting comment)
    sha: same-commit
---

# issue-2629 — technical-writing-structure-comprehension+silent-failure-audit-c1414f3e record

## What was done

Removed the two remaining dead `write_scope` references the issue's
correcting comment named (the 43 data keys in `spawn_roles.json` were
already gone — PR #2630/#2610 deleted that file first):

1. `protocol.md:134-157` — the section heading dropped its "and it is a
   gate — not just prose" clause, and the paragraph asserting
   structural enforcement was rewritten. It now states, present tense,
   that write-scope enforcement was removed by operator decision, lists
   the three now-gone artifacts it depended on (`roles/<name>.json`,
   the `gates/ci.py` diff check, `issue-<n>/<role>` branch naming), and
   says the boundary above holds by convention, not a gate.
2. `docs/specs/role-spec-template.schema.json` — removed `"write_scope"`
   from the `required` array (line 13 in the pre-change file). The
   `write_scope` property definition and the `report_only` field
   (which references it conditionally) were left in place as optional
   schema vocabulary — nothing schema-invalid about a role spec
   declining to set an optional field.

canonical: `sed -n '130,157p' protocol.md` (post-change) and
`python3 -c "import json; print(json.load(open('docs/specs/role-spec-template.schema.json'))['required'])"` —
result: `['role', 'source_standard', 'required_fields',
'reference_resolution', 'recomputation', 'loop_state', 'use_when']`
(no `write_scope`).

## Why

Judgment call the issue asked me to make explicitly: delete the section
or rewrite it to record that scope limitation was removed by operator
decision. I rewrote rather than deleted, because the surrounding
prose (`### The boundary is bidirectional`) still makes a true claim —
a judgment role doesn't ship code and coding doesn't ship a verdict —
and that claim needed *some* answer to "is this enforced or just
prose," since the section originally existed to answer exactly that
question. Deleting the paragraph outright would have left the question
unanswered, which reads worse than either "yes, by a gate" or "no, by
convention" — a reader hits the boundary claim and has no way to know
whether it's checked. The replacement says plainly that it is not
checked anymore, that this was a decision (not a gap), and does not
gesture at reinstating it. The schema fix is not a judgment call: an
optional field's presence in `required` for a mechanism with zero
implementing code left is dead weight and was removed outright, not
softened into a comment.

Followed `technical-writing-structure-comprehension` while drafting the
replacement paragraph: split the enforcement claim into short sentences
plus a 3-item list instead of one run-on sentence carrying three
technical facts, and dropped the now-nonsensical "regardless of any
override" clause (nothing overrides a mechanism that no longer exists).

skill-verdict: technical-writing-structure-comprehension — applied: invoked; loaded skill-registry/skills/technical-writing-structure-comprehension/SKILL.md and applied its chunk-break and filler-deletion rules to the protocol.md write-scope paragraph
skill-verdict: silent-failure-audit — not-applicable: this change edits doc prose and a JSON schema's `required` array, no error-handling code path was written or touched

canonical: `git diff protocol.md` (this session, this turn) — the
rewritten paragraph is split into short sentences plus a 3-item list,
replacing the original single long sentence, and the "regardless of any
override" clause is gone.

## What did not work

None.

## Upstream basis

- Issue #2629 body (original filing: 43 `write_scope` keys in
  `spawn_roles.json` + the `protocol.md`/schema references) — superseded
  in part.
- Issue #2629 correcting comment (posted after PR #2630/#2610 landed) —
  scope for this record: `spawn_roles.json` is gone, `protocol.md:
  147-156` and the schema's `required` array are what's left. sha:
  same-commit.

canonical: `gh issue view 2629 --comments` output — body confirms the
original 43-key/`spawn_roles.json` framing, the comment confirms it is
superseded and re-scopes to `protocol.md:147-156` + the schema.

## Open findings

Two adjacent defects noticed while reading `protocol.md`, both out of
this issue's stated scope (the correcting comment names only
`protocol.md:147-156` and the schema; everything else it explicitly
marks "verified clean, leave alone" or doesn't mention) — recorded here
so they aren't lost, not fixed here:

1. `protocol.md:107` ("One role is one `roles/<name>.json`.") still
   describes `roles/<name>.json` as a live, present-tense concept,
   unrelated to write_scope. This predates this change (PR #2630/#2610
   removed the directory but did not sweep `protocol.md`'s other
   mentions of it) and is a bigger surface than this issue's two named
   spots.
2. `gates/spec_index.py --update` (the regenerator `protocol.md`'s own
   spec-change convention calls for) throws on this branch, and
   identically on `main` pre-change — pre-existing breakage from the
   same `roles/` removal, not introduced by this change; left unfixed
   as out of scope. `docs/specs/reconciled-index.md` was therefore not
   regenerated, and shows no diff either way.

derived: `ls roles/` — result: `ls: cannot access 'roles/': No such
file or directory` (finding 1, artifact absence).
derived: `python3 gates/spec_index.py --update` run on this branch,
then via `git stash && python3 gates/spec_index.py --update; git stash
pop` on pre-change HEAD — result: identical `FileNotFoundError:
.../roles/specs/brand-design.spec.json` traceback both times (finding
2, pre-existing, not introduced here).

## Next steps

None — issue scope delivered.

canonical: `python3 -m pytest -q` output (this session, this turn), run
on this branch and again on pre-change HEAD via `git stash`.
Acceptance requirement met — checked: `python3 -m pytest -q` — result:
477 passed, 16 failed, identical pass/fail counts and identical failing
test IDs on both this branch and pre-change HEAD (the 16 failures are
pre-existing sandboxed-network/git-remote errors, e.g. `fetch 실패 —
fatal: 'origin' does not appear to be a git repository`, unrelated to
this diff).
