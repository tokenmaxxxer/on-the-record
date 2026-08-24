# issue-2166 conformance-review — current-state survey

Phase-1 survey (survey-order-directive) for the conformance audit of
branch `issue-2166/implementation`'s delivery, still open as PR #2171
against `main` at survey time.

```
$ gh pr view 2171 --json state,title,mergedAt,url
{"mergedAt":null,"state":"OPEN","title":"issue-2166: narrow skill-recommender fast path to BM25 top-N candidates","url":"https://github.com/tokenmaxxxer/on-the-record/pull/2171"}
```
canonical: gh pr view 2171 --json state,title,mergedAt,url — pasted live run above (executed-unit)

## 1. What landed

```
$ git log --oneline origin/main..origin/issue-2166/implementation
64c5c571 issue-2166: log the issue-527 reproduction-substitution deviation
cd4c59a3 issue-2166: narrow skill-recommender fast path to BM25 top-N candidates
```
canonical: git log --oneline origin/main..origin/issue-2166/implementation — pasted live run above (executed-unit)

```
$ git show cd4c59a3 --stat
 consult.py                                |  15 +-
 docs/issue-2166/reports/implementation.md | 306 ++++++++++++++++++++++++++++++
 tests/test_retrieval_eval.py              |  35 ++++
 3 files changed, 355 insertions(+), 1 deletion(-)
$ git show 64c5c571 --stat
 .../reports/implementation/deviation-log.md           | 19 +++++++++++++++++++
 1 file changed, 19 insertions(+)
```
canonical: git show cd4c59a3 --stat; git show 64c5c571 --stat — pasted live
run above (executed-unit). Two commits, `Subject: issue-2166` on both,
`Closes #2166` on `cd4c59a3` only (the deviation-log follow-up carries no
closing trailer, matching contract's phase-2-delivery-PR convention).

A wider two-way diff (`git diff origin/main..origin/issue-2166/implementation
-- consult.py pipeline.py`) shows far more churn than the two commits above —
a `룰북`→skill-repo-guidance terminology reversion in unrelated docstrings and
LLM prompt text. That reversion is not part of either commit above
(`git show cd4c59a3 -- consult.py` touches only one hunk, lines 348-370); it
is branch staleness — this branch's merge-base with `main` is `d9a1e826`,
before issue-2164's rename (`3ea0ec88`) landed on `main`. A real three-way
merge resolves this cleanly:

```
$ git merge-tree $(git merge-base origin/main origin/issue-2166/implementation) origin/main origin/issue-2166/implementation | grep -c "<<<<<<<"
0
```
canonical: git merge-tree (merge-base) origin/main origin/issue-2166/implementation
— pasted live run above (executed-unit). Zero conflict markers — GitHub's
own merge button keeps issue-2164's rename AND issue-2166's fix. Not a
defect; recorded so a later reader doesn't mistake the raw two-way diff for
what actually lands.

## 2. Requirement extraction (conformance-review-requirement-extraction applied)

Issue #2166's body (`gh issue view 2166`, read at session start), split one
obligation per line (rule 1), dimension-tagged (rule 6), the issue-527
referent flagged unverifiable-as-written (rule 2 — no session/issue exists
under that number, see §4):

1. **REQ-1** (functional) — investigate `market-analysis-mece-proposal`'s
   mount for issue #525 (implementation role): pull real BM25/judge scores,
   establish whether it is a genuine mismatch or legitimate cross-domain
   applicability, by reading the skill's own description field. Source:
   issue body, "Investigate" bullet 1, first clause.
2. **REQ-2** (functional, unverifiable-as-written) — same, for issue #527
   (interaction-design role). Source: same bullet, second clause.
3. **REQ-3** (functional) — investigate `work-in-english`'s mount: pull real
   BM25/judge scores, establish mismatch given its own description's stated
   firing condition (Korean + English-internals-target-policy). Source:
   issue body, live-finding paragraph, second skill.
4. **REQ-4** (scope-boundary) — classify whether this is the same class as
   #2128 (already addressed) or a case #2128's tuning missed. Source:
   "Investigate" bullet 2.
5. **REQ-5** (functional, conditional on REQ-1/REQ-3's outcome per rule 5) —
   if a genuine mismatch is established: narrow
   `market-analysis-mece-proposal`'s description, OR strengthen the
   skill-judge second-pass filter; if a naming/description problem: reword
   the description. Source: "Fix" section, both bullets.
6. **REQ-6a/REQ-6b** (functional/scope-boundary) — acceptance: a
   regression using issue #525's (6a) and issue #527's (6b) actual task
   text through the retrieval pipeline shows `market-analysis-mece-proposal`
   no longer mounts (or the investigation concludes it's correct and
   closes with reasoning — no forced fix if unwarranted). Source:
   "Acceptance", first bullet. Split in two — one verdict per finding,
   matching `conformance-review-finding-record`'s own "exactly one of
   five verdicts per requirement" rule — rather than kept as the single
   item this survey originally extracted it as; the issue's own
   acceptance text names only `market-analysis-mece-proposal` by string,
   even though the live-finding paragraph raises `work-in-english` too
   (see §5's REQ-5 note on this asymmetry).
7. **REQ-7** (error-handling/traceability) — executed acceptance evidence
   in the record. Source: "Acceptance", second bullet, referencing #2137.

No summary line restates 3+ sub-points (rule 3 n/a); the issue states no
sampling derivation (rule 4 n/a — full enumeration is feasible at this size,
see §7).

## 3. Independent re-derivation (REQ-1, REQ-3, REQ-4) — not taken on trust

conformance-review-verification-method-selection applied: Test method for
REQ-1/REQ-3 (an executable reproduction already exists in the implementation
record — reuse it per rule 4, replay it rather than trust the pasted numbers
per rule 5); Inspection for REQ-4 (a structural git-log fact).

```
$ gh issue view 525 --json body -q .body > /tmp/issue525.txt
$ python3 -c "
from unittest import mock
import spawn
body = open('/tmp/issue525.txt').read()
with mock.patch.object(spawn, '_installed_plugin_skill_dirs', lambda: {}):
    scored = spawn._bm25_cross_family_scores(body, 'implementation', spawn._skill_repo_root())
for i, (score, name, d, source) in enumerate(scored):
    if name in ('market-analysis-mece-proposal', 'work-in-english'):
        print(f'{name} rank {i+1} of {len(scored)} score {score:.3f}')
print('TOPN', spawn._CROSS_FAMILY_CONSULT_TOPN)
"
market-analysis-mece-proposal rank 10 of 269 score 21.507
work-in-english rank 13 of 269 score 20.477
TOPN 8
```
canonical: python3 reproduction of spawn._bm25_cross_family_scores against
issue #525's real body, run against the issue-2166/implementation worktree
checkout — pasted live run above (executed-unit).

This matches the implementation record's own pasted `derived:` block
exactly (same ranks, same scores to 3 decimals). `market-analysis-mece-proposal`
sits outside `_CROSS_FAMILY_CONSULT_TOPN=8` — the judge candidate slate
(`consult.py:367`, `scored[:_sp._CROSS_FAMILY_CONSULT_TOPN]`, unchanged by
this fix) never receives it for this input. **REQ-1: Present.**

`work-in-english` also measures outside the top-8 slate structurally, but
(pre-fix) still auto-picked via the fast-path phrase scan because that scan
iterated the entire `scored` list, not the top-N slice:

```
$ git show cd4c59a3 -- consult.py | grep -A2 "task_lower = task_text.lower"
    task_lower = task_text.lower()
    fast: list[tuple[int, str, Path]] = []
-    for _score, name, d, _source in scored:
+    for _score, name, d, _source in scored[:_sp._CROSS_FAMILY_CONSULT_TOPN]:
```
canonical: git show cd4c59a3 -- consult.py — pasted live run above
(executed-unit).

```
$ cd <issue-2166/implementation worktree> && python3 -m pytest tests/test_retrieval_eval.py -q
.........
9 passed in 1.31s
```
canonical: python3 -m pytest tests/test_retrieval_eval.py -q, run against
the issue-2166/implementation worktree checkout — pasted live run above
(executed-unit), including the new
`test_fast_path_ignores_declared_phrase_outside_bm25_topn`. **REQ-3:
Present** — the mechanism-level finding for `work-in-english` is
established and reproducible, and the fix is correct. §6 finding 1 below
surfaces a distinct evidence-citation defect in the same commit's shipped
comment/docstring, which does not change this verdict on the mechanism
itself.

```
$ git log --format='%ad %H %s' --date=short --all -- pipeline.py spawn.py consult.py | grep -i 2124
2026-08-24 f7d431c253b581adbb44725c81d4a0f74816eae7 issue-2124: skill recommender tuning — enriched BM25 documents, exact-phrase fast path, judge prompt diet, offline retrieval eval (#2128)
```
canonical: git log --all -- pipeline.py spawn.py consult.py, grep 2124 —
pasted live run above (executed-unit). Matches the implementation record's
own citation; the record's root-cause narrative (the fast-path scan was
unconditional over the full `scored` list, #2128's own addition) is
independently verified by the pre-fix hunk quoted above. **REQ-4:
Present.**

## 4. REQ-2 / REQ-6 — issue-527 unresolvable (independently re-checked)

```
$ gh issue view 527 --json title,body -R tokenmaxxxer/on-the-record
{"title":"docs(issue-523): phase-1 proposal — technical-writing/devrel write_scope split", ...}
$ gh issue view 527 -R tokenmaxxxer/tm-dicequest
GraphQL: Could not resolve to an issue or pull request with the number of 527. (repository.issue)
```
canonical: gh issue view 527 against both repositories — pasted live run
above (executed-unit), matching the implementation record's own citations
exactly.

Issue #527, as named in issue #2166's own live-finding paragraph, is not a
resolvable GitHub issue in either repository checked. **REQ-2: Unverifiable**
— missing evidence location: issue #527 in `tokenmaxxxer/on-the-record` or
`tokenmaxxxer/tm-dicequest`; neither names the interaction-design-role
session the issue describes. **REQ-6b: Unverifiable** for the same reason.
**REQ-6a: Present** (§3's replay already establishes
`market-analysis-mece-proposal` does not mount for issue #525's text, so
the acceptance's own no-forced-fix branch applies).

**REQ-5: Present**, with a scope-interpretation note. The shipped fix
(`consult.py:361`, the topN slice) satisfies the acceptance's second remedy
branch generically — it narrows the fast-path mechanism itself, not either
skill's own description. The implementation record's own rationale section
documents two alternatives considered and rejected: a corpus-wide
IDF/rarity filter on declared-phrase tokens, and rewording
`work-in-english`'s declared phrases (out of this repo's write scope — that
file lives in the separate `skill-repository` repo). Both rejections read
as reasoned, not guessed ahead of the evidence.

## 5. REQ-7 — executed acceptance evidence, partially reproducible

The implementation record's acceptance-evidence section pastes three runs:
`py_compile` (OK), a combined 4-file pytest invocation, and an isolated
pre-fix-fails/post-fix-passes replay of the new regression test.

```
$ cd <issue-2166/implementation worktree> && python3 -m py_compile consult.py tests/test_retrieval_eval.py && echo "SYNTAX OK"
SYNTAX OK
```
canonical: python3 -m py_compile, run against the issue-2166/implementation
worktree checkout — pasted live run above (executed-unit); this session
independently reproduced this result and the tests/test_retrieval_eval.py
suite already replayed in §3.

This session could not reproduce the implementation record's combined
4-file pytest run:

```
$ python3 -m pytest test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_spawn_artifact_skill_pairing.py tests/test_retrieval_eval.py -q
PreToolUse:Bash hook error: approval-gate: cannot read issue #2166 (or gh failed: Unknown JSON field: "state_reason" ...). The issue is the canonical approval anchor; its own unavailability cannot be waved through. (contract v3 s19)
```
canonical: pasted live hook-denial transcript above (executed-unit) — this
session's own `on-the-record/hooks/pretooluse-dispatcher.sh` /
`approval-gate.sh` chain, whose `gh issue view <n> --json
state,comments,state_reason` call the installed `gh` CLI rejects with
`Unknown JSON field: "state_reason"`, denies any Bash command naming a
`test/*.py` path (the singular directory only — `tests/*.py`, plural, is
unaffected) regardless of actual approval state. This is the same defect
issue-2164's conformance-review session already recorded in its own survey
and proposal Constraints for the same repository, one branch over — a
second independent hit, raising its priority beyond a one-off.

**REQ-7: Surface** — the evidence has the right shape and the checkable
subset (py_compile, and the tests/test_retrieval_eval.py suite already
replayed in §3) reproduces exactly; the remaining three `test/*.py` files
this session cannot independently execute contribute the rest of the
record's cited combined count.

## 6. Open findings surfaced during survey

1. **Evidence-citation mismatch in the shipped fix (new finding, not one of
   the issue's own REQ items — REQ-8).** `consult.py`'s own inline comment
   (added by `cd4c59a3`) reads, in full:

   ```
   그 스킬의 BM25 순위가 무관한 과제에서 47위여도(재현: 이슈-525 과제
   텍스트) 판단 없이 자동 픽된다.
   ```
   canonical: git show cd4c59a3 -- consult.py — pasted live run above
   (executed-unit; the fuller hunk is quoted in §3).

   This attributes rank 47 to issue-525's task text as the reproduction
   source. The new regression test's docstring repeats the same number:

   ```
   $ grep -n "47\|rank" tests/test_retrieval_eval.py
   231:        is low/irrelevant (measured rank 47 of 269 for a real on-the-record
   ```
   canonical: grep against tests/test_retrieval_eval.py, on the
   issue-2166/implementation worktree checkout — pasted live run above
   (executed-unit).

   canonical: §3's replay above, same function call and same issue-525
   body — pasted live run there. That replay measures `work-in-english`
   at a different, lower rank and score, matching the implementation
   record's own pasted evidence exactly. The record's own citation is
   internally consistent and reproducible; the shipped code comment and
   test docstring's "47" figure is not, for the same named input, and
   neither location carries its own `derived:`-style citation.
   **Verdict: Incorrect** — spec_vs_built: the record's own rationale
   requires the §3-measured rank as the reproducible basis for the fix's
   motivation; what shipped in `consult.py`'s inline comment and
   `tests/test_retrieval_eval.py:231` is a different, non-reproducing
   number attributed to the same input. This does not change REQ-3's
   Present verdict on the fix mechanism itself — the topN slice is
   correct and independently tested (§3) regardless of which number a
   comment cites — but it is a real defect in the delivered artifact's
   own internal evidence trail. Resolution path: a follow-up commit
   correcting the comment/docstring to cite the §3-measured figure, or —
   if 47 is a distinct, undocumented measurement against different
   conditions — citing that derivation explicitly instead of attributing
   it to issue-525's text.
2. **REQ-7's partial-verification gap (§5)** — resolution path: re-run the
   three `test/*.py` files this session could not reach, from a session
   with no `CLAUDE_ROLE` set, or once the `approval-gate.sh`/`gh`
   `state_reason` defect is fixed.
3. **The live `approval-gate.sh`/`gh state_reason` defect itself (§5)** —
   out of this role's write scope (`on-the-record/hooks/` is not under
   `docs/issue-2166/`); reported, not patched. A second independent hit of
   the same defect issue-2164's conformance-review session already
   surfaced.
4. **REQ-1's "read the skill's own description field" clause** — the
   implementation record's Upstream-basis section lists
   `market-analysis-mece-proposal/SKILL.md` among files read, but its
   determination rests solely on the BM25-rank measurement, not on any
   discussion of the description's own wording (contrast:
   `work-in-english`'s declared phrases are quoted and discussed). Minor
   — the rank measurement is dispositive of the acceptance criterion on
   its own — noted, not scored as its own REQ failure.

## 7. Sampling scope

Full enumeration, not sampling: two commits, three touched files
(`consult.py`, `tests/test_retrieval_eval.py`, plus the record/deviation-log
doc pair), issue-named requirement line items REQ-1 through REQ-7 (REQ-6
split into REQ-6a/REQ-6b, §2) plus one reviewer-surfaced finding (REQ-8,
§6). conformance-review-sampling-derivation does not apply at this size —
see its own skill-verdict line in the phase-1 proposal.
