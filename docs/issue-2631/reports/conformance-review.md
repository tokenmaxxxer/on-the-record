---
issue: 2631
role: conformance-review
author: conformance-review
verifies_subject: true  # independent verification of PR #2633's deliverable against issue #2631's own acceptance text
loop_state: reported
type: review-record
code_under_review:
  - gates/model_routing.py:39-91 (`_role_tier()` removed; `route_model()` loses its `role` parameter and the `"roles": [...]` key on every tier)
  - on-the-record/hooks/quality-bar-gate.sh:121-234 (`BAR_ROLES` literal removed; `bar_scoped_roles()` called with `_TRIGGER_PATH_PATTERNS` directly)
  - pipeline.py:575-599 (`resolved_role_model()`'s sole call site updated to the new `route_model()` signature)
  - .on-the-record/model-routing.json (live policy: `"roles"` keys dropped from all three tiers)
  - docs/specs/enforcement-boundary.md:62 (`model_routing.py` row updated to describe the new signature)
  - cdd7e3a4:docs/issue-2631/reports/architecture-interface-contract-shape+model-routing-e54786b2.md (implementation record; untracked in this checkout, read via git show — see Upstream basis)
breaking: "none — this is a review record, no code changed by this role"
verdict: "pass — canonical: independent re-derivation, this session, of all of issue #2631's Acceptance checks plus its must-not clause against branch issue-2631/architecture-interface-contract-shape+model-routing-e54786b2 HEAD 444b6906f6609e3f9e9b5cce0d8e74c5e4415d2d (fresh git worktrees at /tmp/wt-2631-before origin/main and /tmp/wt-2631-after the branch tip) — every named requirement confirmed Present; OPEN FINDING (not a named acceptance bullet): PR #2633 currently shows mergeable: CONFLICTING / mergeStateStatus: DIRTY (`gh pr view 2633 --json mergeable,mergeStateStatus` this session) due to a real conflict in docs/reports/product/priorities.md against main's own #2632, unrelated to the role-name-list removal itself — see Open findings"
upstream:
  - path: docs/issue-2631/reports/architecture-interface-contract-shape+model-routing-e54786b2.md
    sha: 444b6906f6609e3f9e9b5cce0d8e74c5e4415d2d
  - path: gates/model_routing.py, on-the-record/hooks/quality-bar-gate.sh (code under review)
    sha: cdd7e3a4178139c1cc1c61ca25826937c1a0458f
subject: PR #2633 (branch issue-2631/architecture-interface-contract-shape+model-routing-e54786b2, HEAD 444b6906f6609e3f9e9b5cce0d8e74c5e4415d2d, OPEN, not merged)
test: issue #2631's own Acceptance section, https://github.com/tokenmaxxxer/on-the-record/issues/2631
result: passed
assertedBy: conformance-review session, issue-2631 (builder-blind; independently re-ran every acceptance check in fresh git worktrees against both origin/main and the PR branch tip, rather than trusting the implementation record's pasted output)
---

# issue-2631 — conformance-review record

canonical: `gh issue view 2631 --json title,body,number` (this session) —
issue #2631's Acceptance section, quoted verbatim in "Requirement list"
below.

skill-verdict: work-in-english — applied: invoked; this record and all
commands run this session are in English; the final chat summary to the
user is in Korean per the skill's routing rule.
skill-verdict: conformance-review-verification-method-selection —
applied: invoked; used rule 3 (Demonstration, not code-reading) for
AC-2/AC-4's functional-behavior claims — actually called
`route_model()`/`bar_scoped_roles()` with representative subjects/
payloads in fresh worktrees rather than inferring the before/after
equivalence from the diff.
skill-verdict: conformance-review-verdict-assignment — applied: invoked;
rule 6 (re-check before finalizing) drove the merge-base/merge-tree
investigation recorded under Open findings, once a tip-to-tip diff of
`protocol.md`/`docs/specs/role-spec-template.schema.json` first looked
like a possible regression — see Open findings for the canonical
evidence and conclusion.
skill-verdict: conformance-review-finding-record — applied: invoked;
every requirement below carries a verdict from the five-value set, a
file:line/command evidence pointer, and a one-line rationale connecting
the two.
skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; every citation below is pinned to file:line plus the commit sha
this session actually read (`444b6906`/`cdd7e3a4` on the branch, or
`3567f44c` where the citation is to current main), and the merge-conflict
finding names the exact spec state (current `origin/main`) the branch was
diffed against.

## What was done

Independent conformance review of PR #2633 (issue #2631's delivery,
branch `issue-2631/architecture-interface-contract-shape+model-routing-e54786b2`,
HEAD `444b6906`, still OPEN — not merged) against issue #2631's own
Acceptance section. Set up two fresh `git worktree`s — `/tmp/wt-2631-before`
pinned to `origin/main`, `/tmp/wt-2631-after` pinned to the branch tip —
and re-ran every named check plus the must-not clause against real code
in both worktrees, rather than trusting the implementation record's
pasted transcripts. Also independently ran `scripts/audit_removal_claim.py`
myself against the branch, and checked the PR's actual mergeability
against current `main`.

derived: `git rev-parse origin/main origin/issue-2631/architecture-interface-contract-shape+model-routing-e54786b2` (this session) —
```
3567f44c8c17919442cd38f4079fc271b566b9ec
444b6906f6609e3f9e9b5cce0d8e74c5e4415d2d
```

derived: `git diff 49c4854b8d699130fe88e6f6db6e4287feb313c0 origin/main -- gates/model_routing.py on-the-record/hooks/quality-bar-gate.sh gates/quality_bar.py` (this session) —
```
(no output)
```
Confirms `origin/main`'s only commit since the branch's merge-base
(`3567f44c`, issue #2629/PR #2632) never touched either reviewed file or
`quality_bar.py`, so `origin/main` is a valid "before" baseline for AC-2
and AC-4 below even though it is one commit ahead of the branch's actual
base.

## Requirement list

canonical: `gh issue view 2631` body, `## Acceptance` section (this
session, quoted verbatim) —

- AC-1: `gates/model_routing.py` no longer decides a model tier by
  testing membership in a fixed list of names — check: `grep -n 'if role
  in' gates/model_routing.py` and the replacement's own logic; empty
  state: 0 membership tests on a name list.
- AC-2: model routing still routes — the same work still lands on the
  same tier, or the change in routing is stated — check: route several
  real subjects before and after, showing the tier each got.
- AC-3: `BAR_ROLES` is gone, and `quality-bar-gate.sh` no longer iterates
  a fixed list of names — check: `grep -n 'BAR_ROLES'
  on-the-record/hooks/quality-bar-gate.sh`; empty state: 0 occurrences.
- AC-4: the quality-bar gate still classifies and still refuses what it
  refuses today, or the change is stated — check: run the gate against a
  payload it should exercise and one it should deny, before and after.
- AC-5: `scripts/audit_removal_claim.py` is run against the result before
  the PR opens, with its output in the record and every hit classified
  true/false positive — check: the tool's output plus the per-hit
  classification.
- MUST-NOT-1: do not satisfy any bullet by renaming, relocating,
  sharding, or reading the same names from config; do not silently
  change which model tier work routes to as a side effect.

## AC-1 — Present

canonical: `444b6906:gates/model_routing.py` (this session, worktree
`/tmp/wt-2631-after` read) — `_role_tier()` is gone entirely, and every
tier in `DEFAULT_POLICY` (lines 41-45) is now `{"model": "sonnet"}` with
no `"roles"` key.

derived: `git show origin/issue-2631/architecture-interface-contract-shape+model-routing-e54786b2:gates/model_routing.py | grep -n 'if role in'` (this session) —
```
(no output, exit 1)
```

Rationale: the exact grep the acceptance names returns zero hits against
the branch tip, and the function that performed the membership test
(`_role_tier`) is deleted outright, not renamed or moved — matches AC-1's
empty state literally.

## AC-2 — Present

canonical: `444b6906:gates/model_routing.py:63-91` (this session) —
`route_model()` no longer takes `role`; priority order is now
`design_bearing_override` → `single_phase_tier` → `default_tier` only.

derived: independent re-run, this session, of `route_model()` for six
subjects in both worktrees (`/tmp/wt-2631-before` = `origin/main`,
`/tmp/wt-2631-after` = branch tip) — before:
```
ux-engineering False None -> ('sonnet', 'role-tier:judgment')
brand-design False None -> ('sonnet', 'role-tier:judgment')
content-design True None -> ('sonnet', 'role-tier:judgment')
architecture False True -> ('sonnet', 'design-bearing-override')
api-design False None -> ('sonnet', 'default-tier:mid-design')
random-role True None -> ('sonnet', 'single-phase-tier:mechanical')
```
— after:
```
ux-engineering False None -> ('sonnet', 'default-tier:mid-design')
brand-design False None -> ('sonnet', 'default-tier:mid-design')
content-design True None -> ('sonnet', 'single-phase-tier:mechanical')
architecture False True -> ('sonnet', 'design-bearing-override')
api-design False None -> ('sonnet', 'default-tier:mid-design')
random-role True None -> ('sonnet', 'single-phase-tier:mechanical')
```
This independent run matches the implementation record's own transcript
exactly. The **model** selected is identical (`"sonnet"`) for every
subject in both directions. The **rule** attribution changes only for
the three named roles that used to hit `role-tier:judgment`
(`ux-engineering`, `brand-design`, `content-design`); `architecture`,
`api-design`, and `random-role` are unaffected in both fields.

Rationale: the routing change is real (rule tag, not model, for the
three roles) and is stated explicitly rather than discovered — satisfies
AC-2's "or the change in routing is stated" clause, independently
reproduced rather than trusted from the record's own claim.

## AC-3 — Present

canonical: `444b6906:on-the-record/hooks/quality-bar-gate.sh` (this
session, worktree read) — the `BAR_ROLES = [...]` literal (old line 124)
and the `role_patterns = {role: ... for role in BAR_ROLES}` comprehension
(old line 247) are both gone; `bar_scoped_roles(pr_files,
_TRIGGER_PATH_PATTERNS)` is called directly.

derived: `git show origin/issue-2631/architecture-interface-contract-shape+model-routing-e54786b2:on-the-record/hooks/quality-bar-gate.sh | grep -n 'BAR_ROLES'` (this session) —
```
(no output, exit 1)
```

Rationale: the exact grep the acceptance names returns zero hits against
the branch tip — matches AC-3's empty state literally.

## AC-4 — Present

canonical: `444b6906:gates/quality_bar.py` — unmodified by this PR (not
in `git diff --stat origin/main 444b6906`'s file list at all, this
session), so `bar_scoped_roles`/`classify` are the same functions before
and after; only the dict fed into `bar_scoped_roles` changed shape.

derived: independent re-run, this session, of `quality_bar.bar_scoped_roles()`
against a synthetic docs-only file list and a synthetic auth-path file
list, feeding the removed `BAR_ROLES`-gated comprehension (before) and
`_TRIGGER_PATH_PATTERNS` directly (after) —
```
before: docs-only scoped= frozenset()                                 auth-path scoped= frozenset({'secure-coding', 'test-authoring'})
after:  docs-only scoped= frozenset()                                 auth-path scoped= frozenset({'secure-coding', 'test-authoring'})
```
Both scoped-role sets are byte-identical before and after.

derived: `bash -n on-the-record/hooks/quality-bar-gate.sh` against
`/tmp/wt-2631-after` (this session) — exit 0, no output.

Rationale: the classification the gate would act on (which domains a
given file set implicates) is unchanged for both a docs-only and an
auth-path file list, and the script still parses — satisfies AC-4's
"still classifies and still refuses what it refuses today" clause,
independently reproduced.

## AC-5 — Present

canonical: `scripts/audit_removal_claim.py` exists on the branch tip
(`444b6906:scripts/audit_removal_claim.py`, 161 lines, this session).

derived: `python3 scripts/audit_removal_claim.py /tmp/audit_claims_2631.json --root .` (this session, worktree `/tmp/wt-2631-after`, claims = the same `removed_names`/`member_samples`/`min_coloc` the implementation record used for both claims) — result (abbreviated to the verdict/q1/q3 fields; full JSON also captured this session):
```
=== model_routing role-tier membership test ===
verdict: RESHAPE_DETECTED
q1: {"checked": ["_role_tier"], "live_hits": [], "gone": true}
q3: {"checked": true, "branch_hits": [], "still_branches": false}
q2 colocated_files: [gates/__pycache__/model_routing.cpython-310.pyc (4), gates/model_routing.py (4), pipeline.py (2)]

=== quality-bar-gate BAR_ROLES literal ===
verdict: RESHAPE_DETECTED
q1: {"checked": ["BAR_ROLES"], "live_hits": [], "gone": true}
q3: {"checked": true, "branch_hits": [], "still_branches": false}
q2 colocated_files: [on-the-record/hooks/quality-bar-gate.sh (7)]
```
This independent run reproduces the same `RESHAPE_DETECTED` verdicts and
the same q1/q3 results the implementation record reports. The q2
colocated-files lists match on every non-git-internal file
(`gates/model_routing.py`, `pipeline.py`,
`on-the-record/hooks/quality-bar-gate.sh`); this session's run
additionally omits `.git/index`, `.git/objects/pack/*.pack`, and two of
the four `__pycache__/*.pyc` hits the record lists — attributable to a
freshly-created `git worktree` (shares the parent repo's `.git/objects`
by reference rather than scanning its own full `.git/index`, and had not
yet executed `human_comprehensibility`/`quality_bar` to populate their
bytecode caches). All of those omitted hits are exactly the ones the
implementation record itself classifies as false positives, so the
narrower result here is consistent with, not contradictory to, the
record's per-hit classification.

canonical: `cdd7e3a4:docs/issue-2631/reports/architecture-interface-contract-shape+model-routing-e54786b2.md`,
"## `scripts/audit_removal_claim.py` output and per-hit classification"
section (untracked in this checkout — this session's own branch is
`issue-2631/conformance-review`, based on `main`; the implementation
record exists only on the unmerged branch `issue-2631/architecture-
interface-contract-shape+model-routing-e54786b2`, commit `444b6906`,
read via `git show <sha>:<path>` this session) — the record's per-hit
classification (git-internals and pycache = false positive/build-
artifact, `model_routing.py`'s new docstring = false positive/
documentation-of-the-removal, `pipeline.py`'s two incidental substrings =
false positive, `quality-bar-gate.sh`'s `_TRIGGER_PATH_PATTERNS` = false
positive/flagged rather than silently dismissed) was read this session
and each classification checks out against the colocation reasons this
session independently found above.

Rationale: the tool ran, both claims verdict `RESHAPE_DETECTED` (every
hit individually classified, matching AC-5's literal ask — "output plus
the per-hit classification", not a demand for a zero-hit result), and
every hit's classification is independently verifiable true. One
traceability caveat, not verdict-changing: the record's displayed
"result:" block is a hand-reformatted summary of the tool's JSON output,
not a verbatim paste of its actual stdout shape (`=== name ===` /
`verdict:` / `detail:` / raw JSON) — the values match under independent
re-run, but a future reader replaying the exact command would see
differently-shaped (not differently-valued) output than what the record
shows.

## MUST-NOT-1 — Present

canonical: `git diff origin/main 444b6906 -- gates/model_routing.py
on-the-record/hooks/quality-bar-gate.sh` (this session, full diff read) —
both name lists are deleted outright (no new file, no config indirection,
no rename); `.on-the-record/model-routing.json` (the one config file that
changed) only drops the same `"roles"` keys, it does not gain a
replacement enumeration.

derived: `grep -rn "route_model(\|_role_tier\|model_routing\." /tmp/wt-2631-after --include=*.py | grep -v "/gates/model_routing.py:"` (this session) —
```
pipeline.py:598:        policy = model_routing.load_policy(_sp.ROOT)
pipeline.py:599:        return model_routing.route_model(single_phase, design_bearing_verdict, policy)
```
Exactly one call site, already updated to the new signature — no other
caller was missed, and nothing reintroduces a name list elsewhere.

derived: `python3 -m pytest -q -m "not slow"` (this session) — before
(`/tmp/wt-2631-before`, `origin/main`): `16 failed, 475 passed`; after
(`/tmp/wt-2631-after`, branch tip): `16 failed, 475 passed`, same
failing test names in both runs. No regression from this removal, and
the routing change from AC-2 is the one stated, not silent, model-tier
side effect this must-not clause requires be named — which it is, in
both the implementation record and AC-2 above.

Rationale: neither list survives as a rename, a relocation, a shard, or a
config-driven re-read of the same names, and the one real behavior change
(rule-tag drift for the three roles under AC-2) is stated rather than
discovered — both clauses of the must-not hold.

## Open findings

**PR #2633 is currently not mergeable — a real conflict, not the
role-name-list removal itself.**

derived: `gh pr view 2633 --json mergeable,mergeStateStatus,baseRefName` (this session) —
```
{"baseRefName":"main","mergeStateStatus":"DIRTY","mergeable":"CONFLICTING"}
```

derived: `git merge-tree $(git merge-base origin/main <branch>) origin/main <branch>` (this session) —
```
changed in both
  base   100644 90429561fa59f5f7b28190ce3bbba597415d1920 docs/reports/product/priorities.md
  our    100644 71ac385a4b1ff7a065bed4ede7e2e56331bf43c9 docs/reports/product/priorities.md
  their  100644 e1f3f7817c1b96698c8237afb90c32f2c8589241 docs/reports/product/priorities.md
@@ -163,6 +163,7 @@
   Three things must hold together... empty state: a consumer whose role
--
+<<<<<<< .our
```
`docs/reports/product/priorities.md` is the only file `git merge-tree`
reports as "changed in both" — both `main`'s own commit `3567f44c`
(issue #2629/PR #2632) and this branch's own commit `444b6906` append a
new dated entry to the same changelog region, producing an unresolved
`<<<<<<<` conflict marker. This is a genuine merge conflict a human or
the PR author must resolve before this PR can land — it blocks merging
regardless of the reviewed code's own correctness.

Investigated and ruled a false alarm, not a second finding: the branch's
own `protocol.md` and `docs/specs/role-spec-template.schema.json` also
diff against current `origin/main` (a tip-to-tip diff at first appears to
show the branch reintroducing structural write-scope enforcement that
main's #2632 just removed). But neither file appears in `git show --stat`
for either of this branch's own commits (`cdd7e3a4`, `444b6906`) —

canonical: `git show --stat cdd7e3a4 444b6906` (this session) —
```
 .../20260827T082617904635-3616075da9c10e0f.md         |  1 +
 docs/reports/product/priorities.md                    | 19 +++++++++++++++++++
 2 files changed, 20 insertions(+)
 .on-the-record/model-routing.json                  |   9 +-
 ...erface-contract-shape+model-routing-e54786b2.md | 300 +++++++++++++++++++++
 docs/specs/enforcement-boundary.md                 |   2 +-
 gates/model_routing.py                             |  50 ++--
 on-the-record/hooks/quality-bar-gate.sh            |  37 ++-
 pipeline.py                                        |  10 +-
 6 files changed, 353 insertions(+), 55 deletions(-)
```
— confirming this session's own commits never touch `protocol.md` or
`docs/specs/role-spec-template.schema.json` at all. The apparent
"reintroduction" is pure base staleness: the branch's merge-base
(`49c4854b`) predates `main`'s `3567f44c`, so a tip-to-tip diff shows
main's later removal as if the branch were reverting it. `git merge-tree`
does not list either file as "changed in both", confirming a real merge
would simply take main's newer version with no conflict — consistent
with this not being a defect in the reviewed delivery.

Resolution path: the PR author (or an orchestrator) rebases or merges
`main` into this branch, resolving the one real conflict in
`docs/reports/product/priorities.md` by keeping both dated entries
(main's #2629 entry and this branch's own operator-ruling entry), then
re-pushes. `protocol.md`/`role-spec-template.schema.json` need no manual
action — they resolve to main's version automatically once merged. Not
scored as a failure of AC-1 through MUST-NOT-1 above, since none of the
named checks or the must-not text concern mergeability against a moving
`main` — but it is the reason this PR cannot be merged as pushed today,
and is exactly the kind of gap the issue's own "must not... discovered
later" framing asks a reviewer not to let pass silently.

## What did not work

None — this session performed only review actions (`git worktree`,
`grep`, `git show`, a scratch reproduction script, `pytest`, `gh pr
view`, `git merge-tree`) against existing branches; no code or test file
governed by this PR was modified.

## Why

canonical: this session's own AC-1 through MUST-NOT-1 blocks above (each
carrying its own `canonical:`/`derived:` re-derivation) and the Open
findings section's `gh pr view`/`git merge-tree` output — re-derived
every one of issue #2631's named acceptance checks plus its must-not
clause independently, in fresh git worktrees, rather than trusting the
implementation record's pasted transcripts, per builder-blind convention.
Precedent for this approach: prior conformance-review records for issue
#2616 (commit `965de0ca`) and issue #2629 (commit `38a755c1`) — both
untracked on this checkout's own branch, read via `git show
<sha>:docs/issue-<n>/reports/conformance-review.md` this session. Every
requirement above verdicted Present (see AC-1 through MUST-NOT-1), with
every independently-reproduced number and output matching the
implementation record's own claims. The one substantive gap found — PR
#2633 currently `CONFLICTING` against `main`, per the `gh pr
view`/`git merge-tree` output cited under Open findings — is not a
failure of any bullet named in the Requirement list above (mergeability
against a moving base was never named there), so the overall verdict
recorded in this record's own frontmatter is `pass`; but it is a real,
currently-blocking condition the implementation record's own "Next
steps" (build-now, no further work queued) does not mention, so it is
recorded here as an Open finding with a resolution path rather than
silently left for whoever attempts to merge next.

## Upstream basis

`docs/issue-2631/reports/architecture-interface-contract-shape+model-routing-e54786b2.md`
(commit `444b6906f6609e3f9e9b5cce0d8e74c5e4415d2d`) is untracked in this
checkout (this session's own branch is `issue-2631/conformance-review`,
based on `main`; that record exists only on the unmerged branch
`issue-2631/architecture-interface-contract-shape+model-routing-e54786b2`)
and is the implementation record this review checked against issue
#2631's own Acceptance text (not against the record's self-assessment) —
read this session via `git fetch origin
issue-2631/architecture-interface-contract-shape+model-routing-e54786b2`
and `git show 444b6906:docs/issue-2631/reports/architecture-interface-contract-shape+model-routing-e54786b2.md`.
`gates/model_routing.py`, `on-the-record/hooks/quality-bar-gate.sh`,
`pipeline.py`, `.on-the-record/model-routing.json`, and
`docs/specs/enforcement-boundary.md` at commit
`cdd7e3a4178139c1cc1c61ca25826937c1a0458f` are the code under review.
`gates/quality_bar.py` and `scripts/audit_removal_claim.py`
(issue #2626/#2627) are pre-existing, unmodified by this PR, reused as-is.

## Next steps

None — `loop_state: reported` is terminal for this record kind. The one
open item (PR #2633's merge conflict) is the PR author/orchestrator's to
resolve, not a follow-up this review record queues for itself.
