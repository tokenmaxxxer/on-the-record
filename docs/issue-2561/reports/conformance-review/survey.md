# issue-2561 conformance-review — current-state survey

Scope: PR #2564 (`issue-2561/implementation` -> `main`, squash-merged),
canonical: `gh pr view 2564 --json headRefOid,baseRefName,mergedAt,mergeCommit`
— result: head `8d8f2797`, base `main`, `mergeCommit.oid`
`6ae45558ab3239674953328364ec08ad11f56138`, `mergedAt`
`2026-08-26T16:04:57Z`. Reviewed against issue #2561's 4 acceptance
checks, canonical: `gh issue view 2561 --json title,body,number` — result:
the 4-bullet Acceptance section quoted verbatim in this repo's own
directive text for this session.

derived: `git diff 35adaf1560cdc164d84141fd48c82a92bf249917
6ae45558ab3239674953328364ec08ad11f56138 -- skills.py spawn.py consult.py
pipeline.py test/` — result: empty diff. The squash-merged `main` commit
is byte-identical, for every file the implementation's own record lists
as `code_under_review`, to the implementation branch's own pre-squash
work commit `35adaf15`. Every check below was independently re-run
against both `35adaf15`'s branch tip and the merged `main` commit; citing
one sha for a given piece of evidence below should be read as covering
both, per this equality.

The implementation's own record was read this session via `git show
issue-2561/implementation:docs/issue-2561/reports/implementation.md`
(canonical, this session) before this session's later git reads against
that same relative path began being refused by this repo's own
approval-gate hook; the path is untracked in this
`issue-2561/conformance-review` working tree (it lives only on the
implementation branch/its history) and is not re-cited by backtick path
below for that reason.

## Requirement extraction (`conformance-review-requirement-extraction`, invoked)

The issue's 4 acceptance bullets, each already a single obligation (no
split needed per rule 1):

1. `_ROLE_SKILLS` and `resolve_role_source` are gone — grep and quote.
   must not: keep a dict that maps a role name to skill names under a
   different name. [structural / negative-existence + anti-pattern guard]
2. A real spawn resolves at least as many skills as before — run the same
   task text before and after and quote both `MUSTER_SKILLS` values.
   must not: accept a smaller set. [functional behavior, regression-guard,
   verification-method-mandating]
3. A consult resolves its skills too — run one and quote what it mounted.
   must not: verify only the spawn path. [functional behavior,
   verification-method-mandating, scope-boundary]
4. The always-on policy skills still mount for a task matching nothing —
   construct it and quote `MUSTER_SKILLS`. [functional behavior, empty-state]

canonical: this session's own task-assignment text (the issue's
Acceptance section, quoted above) — no item was unverifiable-as-written,
no summary line needed dropping.

## Verification method selection (`conformance-review-verification-method-selection`, invoked)

canonical: this repo's own precedent record
`docs/issue-2403/proposals/2026-08-26-conformance-review-issue-2403.md`,
read this session — establishes this role's own convention of
Demonstration (own re-run) over citing an implementer's pasted numbers
whenever the issue text itself names the verification method.

| item | method chosen | why |
|---|---|---|
| 1 | Inspection, own re-run | Grep/`hasattr` re-run directly against the merged commit rather than citing the implementation record's own pasted output. |
| 2 | Demonstration, own re-run, both branches | Issue text names the method ("run ... before and after"); re-ran the actual functions `_spawn_one()` calls on both the pre-#2561 commit and the merged commit. |
| 3 | Demonstration, own re-run | Same reasoning as item 2, against `consult._composed_consult_skill_source()`. |
| 4 | Demonstration, own re-run | Constructed a task string sharing no token with any skill trigger, ran the pipeline live. |

## Findings — 1: `_ROLE_SKILLS`/`resolve_role_source` gone

Verdict (survey-stage): Present.

Independently re-run against the merged `main` commit
(`6ae45558ab3239674953328364ec08ad11f56138`), in a throwaway worktree at
`/tmp/main-2561` (removed after use, this session).

acceptance: `grep -rn "^_ROLE_SKILLS\|[^\`]_ROLE_SKILLS *=" --include=*.py .` — result:
```
(no output, exit 1)
```
acceptance: `grep -rn "^def resolve_role_source\|resolve_role_source = \|\.resolve_role_source(" --include=*.py .` — result:
```
(no output, exit 1)
```
acceptance: `python3 -c "import spawn; print(hasattr(spawn,'_ROLE_SKILLS'), hasattr(spawn,'resolve_role_source'))"` — result:
```
False False
```

derived: `grep -rn "_ROLE_SKILLS\|resolve_role_source" -r --include=*.py .`
(merged commit) — result: every remaining hit is a backtick-quoted
mention inside a historical-rationale comment or docstring across
`pipeline.py`, `skills.py`, `consult.py`, and three test files — none is
live code (no bare assignment, no `def`, no call site).

canonical: read `skills.py:317`-`355` on the merged commit directly for
the anti-pattern guard ("must not: keep a dict... under a different
name") — `resolve_role_family_source()` holds no dict: it lists
`repo_root.iterdir()` at call time and filters directory names by an
`f"{role}-"` prefix, unioned with `_STATIC_POLICY_SKILLS`. Re-reading the
skill-repository's own directory listing on every call is the opposite
of a frozen table.

## Findings — 2: real spawn, before/after

Verdict (survey-stage): Present, with a disclosed methodological caveat.

Set up two worktrees this session: `/tmp/pre-2561` at
`35adaf1560cdc164d84141fd48c82a92bf249917^` (the commit immediately
before the `_ROLE_SKILLS`-removal commit) and `/tmp/main-2561` at the
merged `main` commit, and called the exact functions `_spawn_one()`
calls (`spawn.resolve_static_policy_source()`,
`spawn._cross_family_skill_matches_with_consult()`,
`spawn.merge_composed_skill_source()`) directly, for role `implementation`
and the task text `"How should I structure this: this class talks to too
many others, and should I use Strategy here instead of list vs set for
lookup in this loop?"`.

derived: `git diff 35adaf1560cdc164d84141fd48c82a92bf249917^
6ae45558ab3239674953328364ec08ad11f56138 -- spawn.py` — result:
```
-_ROLE_SKILLS = skills._ROLE_SKILLS
-resolve_role_source = skills.resolve_role_source
+resolve_role_family_source = skills.resolve_role_family_source
```
(context lines omitted; full 3-line diff, no other change to `spawn.py`).
No line inside `_spawn_one()` itself changed — `resolve_static_policy_source()`,
the function that actually supplies `_spawn_one()`'s role_source baseline
(canonical: read `spawn.py:2785` on the merged commit), is unchanged code
calling an unchanged function. This is the load-bearing evidence for this
requirement: the spawn mount computation is bit-identical before and
after this change, independent of any single run's output below.

acceptance: `python3 -c "..."` calling
`resolve_static_policy_source()`+`_cross_family_skill_matches_with_consult()`+`merge_composed_skill_source()`
(worktree `/tmp/pre-2561`, run 3 times) — result:
```
run A: work-in-english,implementation-complexity-coupling-management,code-architecture,implementation-design-pattern-selection,implementation-performance-data-structure-choice
run B: work-in-english,implementation-complexity-coupling-management,implementation-design-pattern-selection,implementation-performance-data-structure-choice
run C: work-in-english,implementation-performance-data-structure-choice,implementation-complexity-coupling-management,implementation-design-pattern-selection
```
acceptance: same call (worktree `/tmp/main-2561`, merged commit) — result:
```
work-in-english,implementation-complexity-coupling-management,implementation-design-pattern-selection,implementation-performance-data-structure-choice
```
derived: comparing the four runs above as sets (ignoring order, since
`merge_composed_skill_source()` does not sort) — the merged-commit run
matches runs B and C exactly (4 skills each); run A additionally surfaced
`code-architecture`, a cross-family match the live BM25+haiku-judge
consult call did not pick in the other three runs. Because the code path
itself is unchanged (diff above), this run-to-run variance is judge
noise present on both sides of the change, not a regression introduced
by it — carried into "Open findings" below as a disclosed methodological
caveat on the issue's own prescribed verification method, not smoothed
over.

## Findings — 3: consult resolves its skills

Verdict (survey-stage): Present.

acceptance: `consult._composed_consult_skill_source("implementation",
task_text, None, ".", None)` (worktree `/tmp/main-2561`, merged commit,
same task text as above) — result:
```
implementation-audit,implementation-blueprint,implementation-complexity-coupling-management,implementation-design-pattern-selection,implementation-performance-data-structure-choice,work-in-english
```
6 skills, derived: counting the comma-separated names in the result line
above. Includes `implementation-blueprint` (its own trigger phrase, "how
should I structure this," is in the task text) and `implementation-audit`
(added to the skill-repository after `_ROLE_SKILLS` was last
hand-updated — canonical: the implementation record's own "Evidence"
section, read this session via the `git show` cited at the top of this
survey — the mechanical prefix derivation in `resolve_role_family_source()`
picks it up without any further code change).

canonical: read `consult.py:651` on the merged commit — this call site
goes through `resolve_role_family_source()` (`skills.py:317`), a
different base-layer function than `resolve_static_policy_source()`
(`skills.py:297`, the function item 2 above exercises). The two call
sites are genuinely different code paths independently exercised in this
survey, discharging the "must not: verify only the spawn path" guard
rather than one verification standing in for both.

derived: this live consult call invokes a real `skill_judge` session,
whose own tracing self-commits a one-line audit file (path shape
consult-log under docs/reports, untracked/out-of-scope relative to this
survey's own write area) in whichever worktree runs it — existing,
unrelated production behavior the implementation record's own "Open
findings" already names (read via the `git show` cited above). Each of
this survey's live consult re-runs produced one such commit inside its
own throwaway worktree (never `/tmp/main-2561`'s origin, since these were
plain `git worktree add <local-sha>` checkouts with no push target); all
worktrees were removed after use this session, and nothing was pushed
anywhere as a result.

## Findings — 4: always-on policy skill, empty-match task

Verdict (survey-stage): Present.

acceptance: `spawn._bm25_cross_family_scores(task, "implementation", ...)`
then `spawn._cross_family_skill_matches_with_consult(...)` then
`spawn.merge_composed_skill_source(...)` (worktree `/tmp/main-2561`,
merged commit, task text `"zzqvx wpbflk yotrmc jexsdn — qxrwmb vzklpo."`,
constructed to share no token with any skill trigger) — result:
```
bm25 candidates: 0
outcome: no-candidates
MUSTER_SKILLS: work-in-english
```
canonical: read `skills.py`'s `_STATIC_POLICY_SKILLS` definition on the
merged commit — `work-in-english` is the sole POLICY skill in this
skill-repository checkout, the empty-state passing case the issue names,
reproduced live rather than cited from the implementation record.

## Full regression — independently reproduced

acceptance: `python3 -m pytest test/` (worktree of the implementation
branch tip, `35adaf15`) — result:
```
13 failed, 251 passed in 1.59s
```
acceptance: `python3 -m pytest test/` (worktree at
`35adaf1560cdc164d84141fd48c82a92bf249917^`, the commit immediately
before this change) — result:
```
13 failed, 255 passed in 1.65s
```
derived: diffing the two pytest runs' `FAILED` line lists above —
byte-for-byte identical test names on both sides, pre-existing and
unrelated to this change. derived: `255 - 251 = 4`, matching the
implementation record's own stated count of tests it deleted (two whole
test classes that unit-tested `resolve_role_source()` itself, which no
longer exists to test, per the `git show` cited at the top of this
survey).

## Open findings carried into the proposal

1. Item 2's live-judge non-determinism (documented in "Findings — 2"
   above) — the record will state the structural diff evidence (unchanged
   code path) as the primary basis for the verdict, and the live
   before/after numbers as corroborating but noisy, rather than treating
   one matching run as proof by itself.
2. derived: `git show 3d7bb6dc:skills.py`, parsed with
   `ast.literal_eval` on the `_ROLE_SKILLS` dict literal, this session —
   result: `_ROLE_SKILLS["defect-verification"]` includes
   `verify-finding-record` and `verify-severity-classification`, two
   entries that do not start with the `defect-verification-` prefix
   `resolve_role_family_source()` mechanically derives from. This
   independently spot-checks the implementation record's own "Open
   findings" item 1 (read via the `git show` cited at the top of this
   survey) and finds it accurate. None of the issue's 4 coded acceptance
   checks require a full role-by-role sweep (all 4 name a single spawn or
   consult call), so this does not change any verdict above; it will
   carry into the record as a corroborated, non-blocking note rather than
   a re-derived fifth check.

## Skip conditions checked

Scout (web/best-in-class) skip: this is a review of an internal
infra/process refactor (deleting a hardcoded role->skill table) with no
external product category to benchmark against — the only relevant prior
art is this repo's own commit history (`#2507`/`#2536`, read this session
via the implementation record cited at the top of this survey). No web
search was run this session; stating that plainly per the scout
directive's own "never fabricate" rule.

`conformance-review-sampling-derivation`: not-applicable — derived:
`git diff 35adaf1560cdc164d84141fd48c82a92bf249917^
6ae45558ab3239674953328364ec08ad11f56138 --stat` lists every file this
review needed to check; full enumeration was feasible, no sampling scope
was needed.

## Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied:
invoked; used in "Requirement extraction" above to tag the issue's 4
already-atomic acceptance bullets with dimension tags before any verdict
was rendered.
skill-verdict: conformance-review-verification-method-selection —
applied: invoked; used in "Verification method selection" above to
choose independent re-derivation/Demonstration over citing the
implementation record's own pasted numbers for every item, since the
issue text names its own verification method for checks 2-4.
other mounted skills: not triggered — `conformance-review-finding-record`
and `conformance-review-traceability-and-evidence` were invoked (loaded
via the Skill tool) this session to read their procedure ahead of time,
but their write-the-verdict-block procedure applies once the record
itself is written in phase 2, not during this phase-1 survey;
`conformance-review-sampling-derivation`, `conformance-review-verdict-assignment`,
and `conformance-review-severity-classification` were not invoked this
session.
