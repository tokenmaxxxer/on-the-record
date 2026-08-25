---
issue: 2285
role: implementation
loop_state: landed
upstream:
  - path: docs/issue-2241/proposals/2026-08-25-stage-2-consult-skill-source-confirmation.md
    sha: ccee895997e7629495aee4ff7c0588e3082c75bc
  - path: docs/issue-2285/reports/conformance-review.md
    sha: 9bbd1d5525c9d9ae36ac5b40dd24ab78e94b26cd
  - path: docs/issue-2285/reports/execution-observation.md
    sha: 8fefe7ffd678d9b0e15010ee27b014d51bec77ae
code_under_review:
  - consult.py
  - docs/specs/consult-guidance-source.md
  - test/test_consult_no_rulebook_identity_regression.py
type: docs
breaking: none
verdict: pass
---

# issue-2285 — implementation record

## What was done

canonical: `docs/issue-2241/proposals/2026-08-25-stage-2-consult-skill-source-confirmation.md`
(sha `ccee895997e7629495aee4ff7c0588e3082c75bc`) — the frozen write set,
Constraints, Rationale, "What will be done", "Out of scope", and "How
you'll know it worked" this delivery targets verbatim, unchanged from
the prior attempt.

Re-delivers issue #2241 stage 2 (role retirement program) on this
issue's own commit `c8c2c0bf226c8d81cfa28f4b84ba75d18c067319`. The
prior delivery (PR #2344) reached conformance review and was found
`Present` on ten of eleven extracted requirement clauses, `Incorrect`
on one — see "Why" below; that PR was later closed unmerged when the
repo's 2026-08-25 history rewrite invalidated its branch. This session
redelivers the same three files from scratch against the new `main`
(`46da1c8a`), computing every citation only after every edit —
including the `consult.py` comment that shifts line numbers — was
final.

Per contract v3 s19a build-now bypass (`CORE_BUILD_NOW=1`, set by the
spawner), the phase-1 proposal round was skipped — this is a direct
delivery.

- `docs/specs/consult-guidance-source.md` (new): documents that all
  three `consult.py` call sites that resolve guidance *content*
  (`consult.py:690`, `consult.py:964`, `consult.py:1357`) go
  unconditionally through `skills.resolve_role_source()`
  (`skills.py:354-376`), that `_ROLE_SKILLS` (`skills.py:286-337`) and
  the five `roles/<role>.json` existence-check call sites
  (`consult.py:403,738,864,1203,1352`) are untouched by this stage, and
  that `role` staying exposed as a lookup key is deferred to the
  proposal's own named later stages — not this stage's defect to fix.
  derived: `wc -l docs/specs/consult-guidance-source.md` — result: 95.
- `test/test_consult_no_rulebook_identity_regression.py` (new): a
  regression guard — a static source scan of `consult.py` for seven
  identifiers the #1955 commit (`5494b62b`) deleted from `spawn.py`
  (`rulebook_checkout`, `checkout_version`, `ensure_rulebook`,
  `rulebook_source`, `rulebook_dir`, `_role_source_allowlist`,
  `rulebook_version`), plus a behavioral check that
  `_readonly_plugin_dirs()` reaches `spawn.resolve_role_source()`
  identically whether `role` is present in `_ROLE_SKILLS` or not.
  derived: `grep -c 'def test_' test/test_consult_no_rulebook_identity_regression.py`
  — result: 3 (one static-scan test, two behavioral tests).
- `consult.py`: one Korean code comment only (no logic change), at the
  first `roles/<role>.json` existence-check call site (now
  `consult.py:397-402`), pointing at this proposal and naming the
  proposal's own later-stage sections as where that call site and
  `_ROLE_SKILLS` actually change.
  derived: `git diff --stat c8c2c0bf~1 c8c2c0bf -- consult.py` — result:
  `consult.py | 6 ++++++`, 6 insertions, 0 deletions — the comment is
  the only change to that file.

## Why

canonical: `docs/issue-2285/reports/conformance-review.md` R5 (this
issue's own prior review) — the concrete defect this redelivery exists
to fix, quoted in full below.

The prior PR #2344 delivery's own citations in
`docs/specs/consult-guidance-source.md` were computed *before* the same
commit's Korean comment insertion at the first existence-check call
site, then never recomputed — R5's `spec_vs_built`: "every `consult.py`
citation in the spec doc points six lines above its actual target
statement in the same commit's `consult.py`". `skills.py` citations
were unaffected since that commit touched no lines in `skills.py`.

This redelivery avoids the same failure mode by sequencing differently:
the `consult.py` comment (the one edit that shifts line numbers) was
written first, then every citation in both
`docs/specs/consult-guidance-source.md` and this record was derived
from `grep -n`/`sed -n ... | cat -n` against the actually-edited
working tree, after the shift had already happened — not against the
pre-edit file, and not against the original proposal's own now-stale
line numbers (`consult.py:470-471,484`, `skills.py:333-355`, both
written against an earlier commit than either delivery).

The proposal's own Constraints (frozen decision `single-skill-axis`; do
not touch `_ROLE_SKILLS` or the existence-check call sites; do not jump
later-stage key-migration work into this stage) are followed
verbatim — the only `consult.py` edit this session makes is the one
comment the proposal's own "What will be done" names.

## What did not work

None.

## Upstream basis

- `docs/issue-2241/proposals/2026-08-25-stage-2-consult-skill-source-confirmation.md`
  (sha `ccee895997e7629495aee4ff7c0588e3082c75bc`) — the frozen scope
  this delivery targets, cited throughout "What was done"/"Why" above.
- `docs/issue-2285/reports/conformance-review.md` (sha
  `9bbd1d5525c9d9ae36ac5b40dd24ab78e94b26cd`) — canonical: this
  session read this record directly (see quoted `spec_vs_built` in
  "Why"). R5's finding (citations stale by exactly the comment's own
  line count) is the concrete defect this redelivery fixes; the record's
  other ten `Present` verdicts (Constraints, Out-of-scope boundaries,
  the regression test's mechanism, the existing-test gate, rollback/
  empty-state, the operator-frozen constraint) are this session's basis
  for keeping the rest of the prior delivery's shape unchanged.
- `docs/issue-2285/reports/execution-observation.md` (sha
  `8fefe7ffd678d9b0e15010ee27b014d51bec77ae`) — canonical: this session
  read this record directly. It independently re-executed and
  mutation-tested the prior delivery's regression test from a fresh
  worktree, against two deliberately reintroduced regressions (a
  forbidden identifier, and a branch skipping `resolve_role_source()`
  for unmapped roles); this redelivery repeats both mutations directly
  against the redelivered file (see Acceptance below for the live
  re-run and its own result).
- Issue #2285 (`gh issue view 2285`, read this session) — the frozen
  Acceptance text and the operator-frozen constraint comment
  (2026-08-25).

## Open findings

None.

## Next steps

None — `loop_state` is terminal (`landed`).

## Acceptance

gate: `tests/test_spawn_consult_panel.py`

acceptance: `python3 -m pytest tests/test_spawn_consult_panel.py -q` — result:
```
bringing up nodes...

...........................................................x....         [100%]
63 passed, 1 xfailed in 14.85s
```

acceptance: `python3 -m pytest test/test_consult_no_rulebook_identity_regression.py -v` — result:
```
test/test_consult_no_rulebook_identity_regression.py::ReadonlyPluginDirsAlwaysSkillRepoTest::test_mapped_role_reaches_resolve_role_source PASSED
test/test_consult_no_rulebook_identity_regression.py::ReadonlyPluginDirsAlwaysSkillRepoTest::test_unmapped_role_still_reaches_resolve_role_source PASSED
test/test_consult_no_rulebook_identity_regression.py::NoRulebookIdentitySourceStaticScanTest::test_consult_py_never_names_a_retired_rulebook_identifier PASSED

3 passed in 10.24s
```

acceptance: `python3 -m pytest test/test_spawn_role_skill_resolution.py -q` — result:
```
bringing up nodes...

.........                                                                [100%]
9 passed in 11.89s
```
(unmodified, still green — no behavior change to `resolve_role_source()`
itself.)

acceptance: `python3 gates/spec_index.py --update` — result:
`docs/specs/reconciled-index.md 갱신됨`; `git diff docs/specs/reconciled-index.md`
run immediately after — result: empty (no tracked row's hash changed;
the new spec file is not one of the curated `docs/specs/*.md` entries
this index tracks — `docs/specs/approvers.md` and
`docs/specs/flows-schema.md` are the only two, `grep -c '^| \`docs/specs/'
docs/specs/reconciled-index.md` — result: 2).

acceptance: `python3 gates/spec_index.py` (check mode) — result: `통과:
모든 spec 문서가 기록된 해시와 일치한다`.

**Mutation tests on the new regression guard, confirming it is a real
detector (repeats execution-observation's confirmation method, cited in
"Upstream basis" above, against the redelivered file):**

acceptance: reintroduced `rulebook_checkout = None` before
`consult_cmd`'s definition, then `python3 -m pytest test/test_consult_no_rulebook_identity_regression.py -v`
— result:
```
FAILED test/test_consult_no_rulebook_identity_regression.py::NoRulebookIdentitySourceStaticScanTest::test_consult_py_never_names_a_retired_rulebook_identifier
AssertionError: <re.Match object; span=(32887, 32904), match='rulebook_checkout'> is not None
1 failed, 2 passed in 0.80s
```

acceptance: reintroduced a conditional branch in
`_readonly_plugin_dirs()` skipping `resolve_role_source()` for a role
absent from `_ROLE_SKILLS`, then re-ran the same test — result:
```
FAILED test/test_consult_no_rulebook_identity_regression.py::ReadonlyPluginDirsAlwaysSkillRepoTest::test_unmapped_role_still_reaches_resolve_role_source
AssertionError: Lists differ: ['no-such-role'] != []
1 failed, 2 passed in 0.83s
```
The mapped-role sibling test was unaffected in both mutations. Both
mutations were reverted before commit; `git diff --stat c8c2c0bf~1
c8c2c0bf -- consult.py` in "What was done" above confirms only the
6-line comment survives in the committed diff.

**Citation self-check, re-deriving every citation in
`docs/specs/consult-guidance-source.md` against the final working tree
(the exact check R5 found this delivery's predecessor failed):**

acceptance: `grep -n 'resolve_role_source(role' consult.py` — result:
```
690:    plugins = _sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"]
964:    out = list(_sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"])
1357:    plugins = _sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"]
```

acceptance: `grep -n '^def resolve_role_source\|^def resolve_skill_source' skills.py`
— result:
```
354:def resolve_role_source(role: str, repo_root: Path | None) -> dict:
379:def resolve_skill_source(skill_name: str, repo_root: Path | None) -> dict:
```

acceptance: `grep -n 'f = _sp.ROOT / "roles"' consult.py` — result:
```
403:        f = _sp.ROOT / "roles" / f"{role}.json"
738:        f = _sp.ROOT / "roles" / f"{role}.json"
864:        f = _sp.ROOT / "roles" / f"{role}.json"
1203:        f = _sp.ROOT / "roles" / f"{role}.json"
1352:    f = _sp.ROOT / "roles" / f"{role}.json"
```

Every number cited in `docs/specs/consult-guidance-source.md` matches
this output exactly — the function definition spans lines 354 through
376 (the line before the next `def` at line 379), the three call sites
are at lines 690, 964, and 1357, and the five existence-check sites are
at lines 403, 738, 864, 1203, and 1352.

acceptance: `python3 -m pytest test/test_consult_no_rulebook_identity_regression.py tests/test_spawn_consult_panel.py test/test_spawn_role_skill_resolution.py -q && python3 gates/spec_index.py`
(this session, one combined run grounding every claim in the "Acceptance
verification" section below) — result:
```
bringing up nodes...

....................................................................x... [ 94%]
....                                                                     [100%]
75 passed, 1 xfailed in 27.78s
통과: 모든 spec 문서가 기록된 해시와 일치한다
```

skill-verdict: work-in-english — applied: invoked; loaded before authoring any commit message, code comment, docstring, or this record — all repository-bound text in this delivery is English; this final summary to the user is the one Korean-facing exception the skill itself carves out.

skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every citation in "What was done" and this Acceptance section is pinned to file:line and re-derived against the working tree in the "Citation self-check" block above, and R5's finding is linked backward via `docs/issue-2285/reports/conformance-review.md`'s sha in "Upstream basis" rather than only described in prose.

skill-verdict: conformance-review-finding-record — not-applicable: this is an implementation record, not a conformance-review record — there is no requirement/verdict block to write here; R5's own finding block already lives in the upstream `docs/issue-2285/reports/conformance-review.md`.

other mounted skills: not triggered — implementation-blueprint (three small, already-conventionalized artifacts — a spec doc, one test file following an established sibling test's pattern, one code comment — with no open structural decision to classify against), implementation-design-pattern-selection (no GoF-pattern indirection introduced or reconsidered), implementation-complexity-coupling-management (no coupling/cohesion metric crossed a threshold; no cross-module import direction changed), implementation-performance-data-structure-choice (no data-structure/algorithm/communication-scheme choice was in scope).

## Acceptance verification

- claim — checked: c8c2c0bf226c8d81cfa28f4b84ba75d18c067319:test/test_consult_no_rulebook_identity_regression.py:38 — result: pass
- claim — checked: c8c2c0bf226c8d81cfa28f4b84ba75d18c067319:tests/test_spawn_consult_panel.py:4 — result: pass
- claim — checked: c8c2c0bf226c8d81cfa28f4b84ba75d18c067319:test/test_spawn_role_skill_resolution.py:23 — result: pass
- claim — checked: c8c2c0bf226c8d81cfa28f4b84ba75d18c067319:gates/spec_index.py:78 — result: pass
