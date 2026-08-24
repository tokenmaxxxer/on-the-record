---
issue: 2166
role: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2166/reports/conformance-review/survey.md
    sha: 7b159893ad271bacb15e055f53850545eb219a81
  - path: docs/issue-2166/proposals/2026-08-24-conformance-review-issue-2166.md
    sha: 7b159893ad271bacb15e055f53850545eb219a81
subject: commit b9cd89af0e6626fa98db53d580c95936d6710f6e (consult.py,
  tests/test_retrieval_eval.py; PR #2171, merged to main — original
  authoring commits cd4c59a31efd96eecd70f6b422de539502eda2d4,
  64c5c5714ad2ccbb01c8da22e518f9c4f49d3809, still open at phase-1 survey
  time)
test: issue #2166 body ("Investigate"/"Fix"/"Acceptance" text),
  decomposed into REQ-1..REQ-8
  (docs/issue-2166/reports/conformance-review/survey.md §2, §6)
result: failed
assertedBy: issue-2166/conformance-review session (role-handoff contract
  v3)
---

# issue-2166 — conformance-review record

## What was done

Audited `issue-2166/implementation`'s delivery against the requirement
line items the phase-1 survey extracted
(docs/issue-2166/reports/conformance-review/survey.md §2, §6).

canonical: gh pr view 2171 --json state,mergedAt,mergeCommit,headRefName,url — pasted live run below (executed-unit), this session:
```
$ gh pr view 2171 --json state,mergedAt,mergeCommit,headRefName,url
{"headRefName":"issue-2166/implementation","mergeCommit":{"oid":"b9cd89af0e6626fa98db53d580c95936d6710f6e"},"mergedAt":"2026-08-24T08:00:03Z","state":"MERGED", ...}
```
canonical: gh pr view 2171 fence directly above (executed-unit, this session) — open at phase-1 survey time, merged since. This phase-2 session audits the same two commits (`cd4c59a3`, `64c5c571`) as landed on `main` via `b9cd89af`.

The per-requirement verdicts are in the Findings section below. REQ-8's
`Incorrect` verdict carries the phase-1 proposal's own already-approved
verdict forward unchanged. REQ-7's verdict is revised in this phase-2
session from the approved proposal's `Surface` to `Incorrect` — the
Deviations section below states why.

## Why

The verdicts below instantiate the approved proposal
(docs/issue-2166/proposals/2026-08-24-conformance-review-issue-2166.md)
without re-deriving method or evidence already fixed during phase 1,
except for REQ-7, where this session's own independent re-execution
turned up evidence the proposal did not have (Deviations).
`conformance-review-verdict-assignment` rule 2 (Incorrect for an active,
reproducible contradiction) and rule 6 (re-check before finalizing) were
applied to that revision — both shown in REQ-7's finding block below.

## Findings

---
requirement: investigate `market-analysis-mece-proposal`'s mount for
  issue #525 (implementation role) — pull real BM25/judge scores,
  establish genuine mismatch vs legitimate cross-domain applicability
  (REQ-1)
spec_ref: issue #2166 body, "Investigate" bullet 1, first clause
verdict: Present
evidence: `b9cd89af:docs/issue-2166/reports/implementation.md` (derived
  block); this session's own replay fence below
rationale: canonical: python3 -c spawn._bm25_cross_family_scores replay, issue #525's real body, against origin/main — pasted live run below (executed-unit), this session:
```
$ cd /tmp/wt-2166-main && gh issue view 525 --json body -q .body > /tmp/issue525.txt
$ python3 -c "..."
market-analysis-mece-proposal rank 10 of 269 score 21.507
work-in-english rank 13 of 269 score 20.477
TOPN 8
```
canonical: fence directly above (executed-unit, this session) — matches the implementation record's own pasted numbers and the phase-1 survey's own replay exactly. `market-analysis-mece-proposal` sits outside `_CROSS_FAMILY_CONSULT_TOPN=8` — the judge candidate slate never receives it for this input. Minor open finding, canonical: survey §6 finding 4 — the implementation record's determination rests on this rank measurement alone, not a discussion of the skill's own description wording; not scored as its own requirement failure.

---
requirement: investigate the same, for issue #527 (interaction-design
  role) (REQ-2)
spec_ref: issue #2166 body, "Investigate" bullet 1, second clause
verdict: Unverifiable
evidence: missing evidence location — issue #527 in
  `tokenmaxxxer/on-the-record` or `tokenmaxxxer/tm-dicequest`
rationale: canonical: gh issue view 527 against both repositories — pasted live run below (executed-unit), this session:
```
$ gh issue view 527 --json title,body -R tokenmaxxxer/on-the-record
{"title":"docs(issue-523): phase-1 proposal — technical-writing/devrel write_scope split", ...}
$ gh issue view 527 -R tokenmaxxxer/tm-dicequest
GraphQL: Could not resolve to an issue or pull request with the number of 527. (repository.issue)
```
canonical: fence directly above (executed-unit, this session) — matches survey §4. Neither result names the interaction-design-role session issue #2166's own live-finding paragraph describes.

---
requirement: investigate `work-in-english`'s mount for issue #525 — pull
  real BM25/judge scores, establish mismatch given its own description's
  stated firing condition (REQ-3)
spec_ref: issue #2166 body, live-finding paragraph, second skill
verdict: Present
evidence: `b9cd89af:consult.py:352-363`; `b9cd89af:tests/test_retrieval_eval.py:224-257`
rationale: canonical: git show cd4c59a3 -- consult.py — pasted live run below (executed-unit), this session:
```
$ git show cd4c59a3 -- consult.py | grep -A2 "task_lower = task_text.lower"
    task_lower = task_text.lower()
    fast: list[tuple[int, str, Path]] = []
-    for _score, name, d, _source in scored:
+    for _score, name, d, _source in scored[:_sp._CROSS_FAMILY_CONSULT_TOPN]:
```
canonical: fence directly above (executed-unit, this session) — `work-in-english` measures outside the top-8 BM25 slate structurally (REQ-1's replay fence above), but pre-fix still auto-picked via the fast-path phrase scan because that scan iterated the entire `scored` list rather than the top-N slice shown above.

canonical: python3 -m pytest tests/test_retrieval_eval.py -q, origin/main worktree — pasted live run below (executed-unit), this session:
```
$ cd /tmp/wt-2166-main && python3 -m pytest tests/test_retrieval_eval.py -q
9 passed in 1.31s
```
canonical: fence directly above (executed-unit, this session) — the mechanism-level finding and fix are established and independently reproducible; REQ-8 below covers a distinct evidence-citation defect in the same commit's shipped comment/docstring that does not change this verdict on the mechanism itself.

---
requirement: classify whether this is the same class as #2128 (already
  addressed) or a case #2128's tuning missed (REQ-4)
spec_ref: issue #2166 body, "Investigate" bullet 2
verdict: Present
evidence: `f7d431c253b581adbb44725c81d4a0f74816eae7` (#2128, `issue-2124:
  skill recommender tuning`)
rationale: canonical: git log --all -- pipeline.py spawn.py consult.py, grep 2124 — pasted live run below (executed-unit), this session:
```
$ git log --format='%ad %H %s' --all -- pipeline.py spawn.py consult.py | grep -i 2124
2026-08-24 f7d431c253b581adbb44725c81d4a0f74816eae7 issue-2124: skill recommender tuning ... (#2128)
```
canonical: fence directly above (executed-unit, this session) — matches the implementation record's own citation. REQ-3's pre-fix hunk above independently verifies the root-cause narrative: the fast-path scan was unconditional over the full `scored` list, #2128's own addition, and #2166's fix bounds it — a case #2128's own tuning missed.

---
requirement: if a genuine mismatch is established, narrow
  `market-analysis-mece-proposal`'s description or strengthen the
  skill-judge second-pass filter; if a naming/description problem,
  reword the description (REQ-5)
spec_ref: issue #2166 body, "Fix" section, both bullets
verdict: Present
evidence: `b9cd89af:consult.py:366` (`scored[:_sp._CROSS_FAMILY_CONSULT_TOPN]`,
  quoted in REQ-3's evidence above)
rationale: canonical: b9cd89af:docs/issue-2166/reports/implementation.md Rationale section — read this session. It documents two alternatives considered and rejected (a corpus-wide IDF/rarity filter, and rewording `work-in-english`'s declared phrases, out of this repo's write scope). The shipped fix satisfies the acceptance's remedy generically — it narrows the fast-path mechanism itself rather than either skill's own description — and both rejections read as reasoned, not guessed ahead of the evidence.

---
requirement: acceptance — a regression using issue #525's actual task
  text through the retrieval pipeline shows
  `market-analysis-mece-proposal` no longer mounts, or the investigation
  concludes it's correct and closes with reasoning (REQ-6a)
spec_ref: issue #2166 body, "Acceptance", first bullet (named skill only)
verdict: Present
evidence: REQ-1's replay fence above (`market-analysis-mece-proposal`
  rank 10, outside `TOPN=8`)
rationale: canonical: REQ-1's replay fence above (this session, executed-unit) — `market-analysis-mece-proposal` does not mount for issue #525's real text under current code; the acceptance's own no-forced-fix branch applies, and it is reasoned, not asserted.

---
requirement: same acceptance regression, for issue #527's actual task
  text (REQ-6b)
spec_ref: issue #2166 body, "Acceptance", first bullet, read against the
  live-finding paragraph's second named session (issue #527); split from
  REQ-6a per `conformance-review-finding-record`'s one-verdict-per-
  requirement rule (survey §2 note)
verdict: Unverifiable
evidence: same missing evidence location as REQ-2 — issue #527 in either
  repository checked
rationale: canonical: REQ-2's gh issue view 527 fence above (this session, executed-unit) — no resolvable issue #527 exists to pull real task text from, so no regression against it can be run either way.

---
requirement: executed acceptance evidence in the record (REQ-7)
spec_ref: issue #2166 body, "Acceptance", second bullet, referencing
  #2137
verdict: Incorrect
spec_vs_built: canonical: python3 -m pytest test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_spawn_artifact_skill_pairing.py tests/test_retrieval_eval.py -q — the implementation record's own citation (b9cd89af:docs/issue-2166/reports/implementation.md, read this session), quoted below:
```
$ python3 -m pytest test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_spawn_artifact_skill_pairing.py tests/test_retrieval_eval.py -q
40 passed in 36.17s
```
The phase-1 survey session could only reach part of these 4 files, blocked by an environment hook (survey §5, Deviations below); this session's environment did not block it.

canonical: python3 -m pytest test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_spawn_artifact_skill_pairing.py tests/test_retrieval_eval.py -q — this session's own first-pass rerun against origin/main, pasted live below (executed-unit):
```
$ python3 -m pytest test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_spawn_artifact_skill_pairing.py tests/test_retrieval_eval.py -q
39 passed in 1.51s
```
canonical: python3 -m pytest, fence directly above (executed-unit, this session) — 39 passed, not the record's cited 40.

canonical: python3 -m pytest test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_spawn_artifact_skill_pairing.py tests/test_retrieval_eval.py -q and --collect-only, second pass — pasted live below (executed-unit), this session:
```
$ python3 -m pytest test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_spawn_artifact_skill_pairing.py tests/test_retrieval_eval.py -q
39 passed in 1.51s
$ python3 -m pytest test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_spawn_artifact_skill_pairing.py tests/test_retrieval_eval.py --collect-only -q
39 tests collected in 0.02s
```
canonical: python3 -m pytest --collect-only, fence directly above (executed-unit, this session) — 39 passed again, 39 collected total; the record's cited 40 cannot be this exact file set at this commit.
evidence: `b9cd89af:docs/issue-2166/reports/implementation.md`
  acceptance-evidence section; this session's three live reruns above
rationale: same pattern as REQ-8 below — an active, reproducible
  contradiction of a specific cited count, not a mere gap — so
  `Incorrect` rather than `Surface`. `py_compile` and the
  `tests/test_retrieval_eval.py` subset (REQ-3's own fence above) both
  reproduce cleanly; this verdict concerns only the combined-count
  citation's own accuracy, not the underlying suite's health.

---
requirement: evidence-citation accuracy of the shipped fix's own inline
  comment and test docstring (REQ-8, reviewer-surfaced, not one of the
  issue's own line items)
spec_ref: issue #2166 body — the fix's own motivating claim (implicit in
  the "Fix"/"Acceptance" sections' expectation that the shipped artifact
  correctly documents the defect it closes)
verdict: Incorrect
spec_vs_built: canonical: git show cd4c59a3 -- consult.py, grep of tests/test_retrieval_eval.py on origin/main — pasted live run below (executed-unit), this session:
```
$ git show cd4c59a3 -- consult.py | grep -n 47위
+47위여도(재현: 이슈-525 과제
$ grep -n 47 tests/test_retrieval_eval.py
231:        is low/irrelevant (measured rank 47 of 269 for a real on-the-record
```
canonical: fence directly above (executed-unit, this session) — `consult.py:359`'s own inline comment and `tests/test_retrieval_eval.py:231`'s docstring both attribute rank 47 to issue-525's task text as the reproduction source. Neither shipped site carries its own `derived:`-style citation for "47".
evidence: `b9cd89af:consult.py:359`,
  `b9cd89af:tests/test_retrieval_eval.py:231`; REQ-3's replay fence above
rationale: canonical: REQ-1's python3 -c spawn._bm25_cross_family_scores replay fence above (this session, executed-unit) — rank 13 of 269 `derived: python3 -c spawn._bm25_cross_family_scores replay, REQ-1's fence above`, not the shipped comment/docstring's rank 47, for that same named input, matching the implementation record's own `derived:` block exactly. The record's own citation is internally consistent and reproducible; the shipped comment/docstring's figure is not — an active contradiction, not a mere omission, so `Incorrect` rather than `Absent` (`conformance-review-verdict-assignment` rule 2). Does not change REQ-3's `Present` verdict on the fix mechanism itself.

## Upstream basis

- `docs/issue-2166/reports/conformance-review/survey.md`, sha
  `7b159893ad271bacb15e055f53850545eb219a81` — requirement extraction
  (§2), independent re-derivation (§3), REQ-2/REQ-6b unresolvability
  (§4), REQ-7's partial reproduction (§5), and the four open findings
  (§6) this record's Findings and Open findings sections build on.
- `docs/issue-2166/proposals/2026-08-24-conformance-review-issue-2166.md`,
  sha `7b159893ad271bacb15e055f53850545eb219a81` — the approved phase-1
  proposal this record instantiates. canonical: gh issue view 2166 --json comments — pasted live run below (executed-unit), this session:
  ```
  $ gh issue view 2166 --json comments -q '.comments[] | .author.login+": "+.body'
  JiwonJung94: APPROVE issue-2166/conformance-review
  ```
  canonical: fence directly above (executed-unit, this session) — `JiwonJung94` is listed in `docs/specs/approvers.md` (read this session) — the same account as this PR's author (single-account mode).
- commit `b9cd89af0e6626fa98db53d580c95936d6710f6e`, merged to `main`
  via PR #2171 (original commits `cd4c59a3`, `64c5c571`). canonical: gh pr view 2171 --json state,mergedAt,mergeCommit,headRefName,url, pasted live near the top of this record (executed-unit, this session).

## Open findings

1. **REQ-7's acceptance-evidence citation does not reproduce** — this
   session's own finding, revising the approved proposal's `Surface` to
   `Incorrect`. canonical: REQ-7's finding block above, this session's own reruns. Resolution path: a follow-up commit re-running the exact combined 4-file command in the implementation session's own environment (or a clean CI run) and re-pasting the actual result, or stating why a different result was originally collected if that turns out to be the explanation rather than a plain miscount.
2. **REQ-8's evidence-citation mismatch.** canonical: REQ-8's finding block above, this session's own replay. Resolution path: a follow-up commit correcting `consult.py:359`'s comment and `tests/test_retrieval_eval.py:231`'s docstring to cite the REQ-3/REQ-8-measured figure, or citing a distinct derivation explicitly if one exists.
3. **The live `approval-gate.sh`/`gh state_reason` defect itself**
   (survey §5-6) — out of this role's write scope
   (`on-the-record/hooks/` is not under `docs/issue-2166/`); reported,
   not patched. canonical: gh issue view 2166 --json state,comments,state_reason — pasted live run below (executed-unit), this session:
   ```
   $ gh issue view 2166 --json state,comments,state_reason
   Unknown JSON field: "state_reason"
   ```
   canonical: fence directly above (executed-unit, this session) — confirms the underlying `gh` CLI incompatibility still exists. The specific test/*.py-command-blocking symptom did not reproduce this phase-2 session — the Deviations section below cites the bypass this session hit instead. The underlying `gh` incompatibility above is unfixed and would still block a session without that bypass. A third independent hit of the same defect class issue-2164's conformance-review session first recorded.
4. **REQ-1's "read the skill's own description field" clause** — minor,
   carried from survey §6 finding 4; not scored as its own requirement
   failure (REQ-1's Findings block above).

## Deviations

The approved proposal's step 2 set REQ-7's verdict to `Surface`, on the
survey's own rationale that this review session's environment could
only reach part of the 4 files in the implementation record's combined
acceptance-evidence command (survey §5). canonical: sed -n '178,191p' on-the-record/hooks/approval-gate.sh — pasted live run below (executed-unit), this session:
```
$ sed -n '178,191p' on-the-record/hooks/approval-gate.sh
if os.environ.get("CORE_BUILD_NOW") == "1":
    sys.stderr.write(
        "approval-gate: CORE_BUILD_NOW=1 — bypassing phase-2 approval check "
        "for issue-%d/%s write (%s).\n" % (issue, role, n)
    )
    sys.exit(0)
```
canonical: fence directly above (executed-unit, this session) — this session's own environment carries `CORE_BUILD_NOW=1` (set by the spawner per contract v3 s19a); the phase-1 survey session did not, so it reached the failing `gh --json state_reason` call instead. Full reproduction here turned up a more specific defect than the proposal anticipated — REQ-7's finding block above shows the record's own cited combined-run result does not match this session's own reruns. This record therefore renders REQ-7 as `Incorrect` rather than the proposal's `Surface` — a revision made solely on new evidence this session gathered inside its own frozen write set (the record file itself), following the same independent-replay method the proposal's own Rationale already commits to for REQ-8, not a re-litigation of any other requirement's verdict. canonical: the approved proposal's step 4 — read this session — maps both `Surface` and `Incorrect` to the same `failed` value, so this revision leaves `result: failed` unchanged.

## Next steps

None needed from this role or branch — `loop_state` above is already
this record kind's terminal value, `reported`. canonical: roles/specs/conformance-review.spec.json loop_state.terminal — read this session. The four open findings above name their own resolution paths for whoever picks them up next.

## What did not work

The phase-1 survey session's combined 4-file `pytest` acceptance-
evidence reproduction (REQ-7) could not reach all four files, blocked
by the `approval-gate.sh`/`gh state_reason` environment defect (open
finding 3). canonical: survey §5-6 — read this session. This phase-2 session was not blocked the same way (Deviations above). canonical: python3 -m pytest test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_spawn_artifact_skill_pairing.py tests/test_retrieval_eval.py -q — REQ-7's finding block above (executed-unit, this session) — all 4 files ran, which is what surfaced REQ-7's revised verdict. Nothing else in this phase-2 write diverged from the approved proposal's plan.

## Skill verdicts

skill-verdict: conformance-review-finding-record — applied: invoked;
loaded this session before writing the Findings section above; its
field list (`requirement`/`spec_ref`/`verdict`/`evidence`/`rationale`,
plus `spec_vs_built` for REQ-7 and REQ-8's `Incorrect` verdicts) shaped
every block, one per REQ-1..REQ-6b, REQ-7, REQ-8.

skill-verdict: conformance-review-traceability-and-evidence — applied: invoked;
loaded this session; every evidence citation above pins a
`sha:path:line` pointer against `b9cd89af` — canonical: gh pr view 2171 --json state,mergedAt,mergeCommit,headRefName,url, pasted live near the top of this record (executed-unit, this session) — rather than a bare path, and `consult.py` and `tests/test_retrieval_eval.py` are cited as separate contributing files for REQ-3/REQ-8 rather than bundled.

skill-verdict: conformance-review-verdict-assignment — applied: invoked;
loaded this session to re-derive REQ-7's verdict against the new
evidence gathered this session (rule 2's Incorrect-not-Absent choice,
and rule 6's re-check — the combined command rerun a second time before
finalizing, both shown in REQ-7's finding block above). REQ-1..REQ-6b
and REQ-8's verdicts are carried forward from the phase-1 proposal's own
invocation of this skill (proposal skill-verdicts section) without
re-derivation, since their evidence is unchanged.

skill-verdict: conformance-review-requirement-extraction — applied:
invoked (phase-1 session, per the approved proposal's own
skill-verdicts section, carried forward verbatim): produced the
REQ-1..REQ-7 split (REQ-6 further split into REQ-6a/REQ-6b) in survey
§2 that this record's Findings section instantiates one-for-one.

skill-verdict: conformance-review-verification-method-selection —
applied: invoked (phase-1 session, carried forward verbatim): set the
Test method (reusing/replaying the implementation record's own
reproduction) for REQ-1/REQ-3/REQ-7 and Inspection for REQ-4, methods
this phase-2 session's own reruns above continue to use unchanged.

other mounted skills: not triggered — conformance-review-sampling-derivation
(full enumeration was feasible at this size, survey §7) and
conformance-review-severity-classification (no severity-weighting was
requested) stay `not-applicable`, unchanged from the phase-1 proposal's
own verdict lines for them.
