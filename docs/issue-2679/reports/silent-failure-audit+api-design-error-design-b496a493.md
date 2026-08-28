---
issue: 2679
role: silent-failure-audit+api-design-error-design-b496a493
author: silent-failure-audit+api-design-error-design-b496a493
skills: silent-failure-audit (skill-repository(297e350)), api-design-error-design (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review:
  - path: skills.py
    sha: same-commit
  - path: consult.py
    sha: same-commit
  - path: spawn.py
    sha: same-commit
  - path: test/test_spawn_skills_mount.py
    sha: same-commit
  - path: test/test_spawn_cross_family_skill_selection.py
    sha: same-commit
type: fix
breaking: false
verdict: fixes the candidate-list divergence and the incomplete not-invoked enumeration in code with regression tests; corrects the 95%-population claim and discloses the fail-open delay nuance in an appended section on PR #2682's own record (contract v3 s11 forbids editing another author's existing lines). The two items not disputed by the verification (the byte-identical pre-existing failure set, and fail-open never blocking a spawn) and the log-only fix itself are untouched.
loop_state: landed
upstream:
  - path: docs/issue-2679/reports/silent-failure-audit+api-design-error-design-3353dd59.md
    sha: 7e7165e7223a1a25de9b0ead5b8b780780c29ef5
  - path: docs/issue-2679/reports/adversarial-review+conformance-review-sampling-derivation-0d692f76.md
    sha: 24e9ea68c0a476c3e42c7aca6caa54de1602b0d7
---

# issue-2679 — silent-failure-audit+api-design-error-design-b496a493 record

## What was done

Send-back fix for PR #2682 (`issue-2679/silent-failure-audit+api-design-error-design-3353dd59`,
head `7e7165e7223a1a25de9b0ead5b8b780780c29ef5`). Built directly on that
branch tip — the log-only `skill_judge` outcome-logging fix and the
unknown-`--skills` candidate-naming fix from PR #2682 are both kept
as-is; this record fixes exactly the three items an independent
verification landed on main at `24e9ea68c0a476c3e42c7aca6caa54de1602b0d7:docs/issue-2679/reports/adversarial-review+conformance-review-sampling-derivation-0d692f76.md:1`
sent back. Nothing outside those three items was changed.

Build-now bypass (contract v3 s19a): this session's environment carries
`CORE_BUILD_NOW=1`, set by the spawner.
acceptance: `printenv CORE_BUILD_NOW` — result:
```
1
```
Delivers directly, no phase-1 proposal round.

**Item 2 — candidate list can diverge from what is mountable (fixed in
code).** The verification reproduced a divergence: a hook-carrying skill
directory (a `hooks/` subdirectory — mount always refused by
`skills.py`'s `resolve_skill_source()`/`resolve_static_policy_source()`/
`resolve_role_family_source()`/`resolved_skill_sources()`) was still
listed as a candidate in the unknown-name error, so the error could name
a skill that then dead-ends one step later — the failure mode issue
#2679's `must not` was written to prevent.

Fix: added `_carries_hooks(skill_dir) -> bool` (`skills.py`, one
definition, `(skill_dir / "hooks").is_dir()`) and replaced every
duplicate `(d / "hooks").is_dir()` inline check (4 call sites: the three
`resolve_*_source()` mount-refusal checks, plus
`resolved_skill_sources()`'s per-match hooks check) with calls to it —
reuse, not a second copy. Both candidate-list builders now filter
through the same predicate before building the error clause:
- `resolved_skill_dirs()`: the name-existence check (`available`, used
  for the unknown/known decision) stays as-is — filtering that would
  make a hooks-carrying name requested by its exact name report
  "unknown" instead of reaching the hooks-specific refusal message
  downstream, which is outside this item's scope. Only the copy of
  `available` given to `_available_skills_clause()` for the error text
  is filtered.
- `resolved_skill_sources()`: `all_available` (used only in the
  fully-unknown-name `sys.exit`, not in the per-name match logic) is now
  built from `_carries_hooks()`-filtered repo/plugin/tier3/tier4 name
  sets.

`_carries_hooks` was added to `spawn.py`'s explicit skills.py re-export
block (`spawn.py`, next to `_available_skills_clause`) in the same edit
that introduced the new cross-module name — the missing-re-export
`AttributeError` class of mistake PR #2682's own record documented
hitting once already, in its "What did not work" section.

acceptance: `python3 -c` invoking `resolve_skill_source('hooked-skill', repo_root)` and `resolved_skill_dirs('good-skill,totally-bogus-name', repo_root)` against a temp dir with `good-skill/` and `hooked-skill/hooks/` (real filesystem, no mocks) — result:
```
resolve_skill_source('hooked-skill') -> resolve_skill_source: 'hooked-skill' 이 지정한 스킬 중 hooked-skill 가 hooks/ 를 들고 있다 — skill-repository 는 가이던스 전용이다(훅 없음, 이슈 #1758)
resolved_skill_dirs(...) -> --skills: 모르는 스킬 totally-bogus-name — 쓸 수 있는 이름: good-skill
```
`hooked-skill` is still refused when requested by its own name (unchanged
behavior), and no longer appears as a candidate for an unrelated unknown
name (the fix — `good-skill` is the only candidate now).

Regression tests added in `test_spawn_skills_mount.py`, class
`ResolvedSkillDirsTest`: methods
`test_unknown_name_candidates_exclude_hooked_dirs` and
`test_exact_name_request_for_hooked_dir_still_gets_hooks_error` (the
second guards against over-filtering — the name-known/unknown decision
itself must stay unchanged); class `ResolvedSkillSourcesFourTierTest`:
method `test_nowhere_found_candidates_exclude_hooked_dirs`.
acceptance: `python3 -m pytest -q test/test_spawn_skills_mount.py -k hooked` — result:
```
3 passed
```

**Item 3 — not-invoked enumeration incomplete (fixed in code, one path
disclosed as deliberately uncovered).** The verification's code-level
enumeration of `consult.py`'s `_cross_family_skill_matches_with_consult()`
and `spawn.py`'s cross-family join lists 7 terminal states total, not the
4 PR #2682 claimed, 2 of them silent before this fix:

1. no BM25 candidates at all -> `no-candidates`, printed (pre-existing)
2. fast-path fills all remaining slots -> `fast-path:<names>`, printed
   (PR #2682's before-landing-hunt fix)
3. fast-path partial fill, no BM25 candidates left, `outcome_prefix`
   empty -> `no-candidates`, printed (PR #2682's fix)
4. fast-path partial fill, no BM25 candidates left, `outcome_prefix`
   truthy -> returned `outcome_prefix` unchanged, was not printed — same
   outcome-string shape as state 2, reachable under ordinary production
   inputs (any task with fewer than 5 distinct BM25-scored candidates all
   carrying a matching declared phrase, no monkeypatching needed) — the
   gap this item fixes
5. judge succeeds -> `completed`, printed (PR #2682's fix)
6. judge errors or times out -> `fail-open`, printed (pre-existing)
7. `issue is None` -> `not-run`, printed (PR #2682's fix)

Fix (`consult.py`, the `if not candidates:` branch): ungated the print
from `if not outcome_prefix:` — state 3 and state 4 now each print a
distinguishable line (`"...남은 후보 0개 (no-candidates)"` vs `"...남은
BM25 후보 0개, fast-path 픽만 반영: {outcome_prefix}"`).

acceptance: `python3 -c` calling `_cross_family_skill_matches_with_consult()` with `k=5`, three skills each with a distinct declared phrase in the task text, monkeypatching only `_skill_judge_consult` (real BM25/phrase-match code path, no internal-shape patching) — result:
```
OUTCOME: fast-path:alpha,beta,gamma
STDERR: [implementation] skill_judge 자문 안 함 — fast-path 이후 남은 BM25 후보 0개, fast-path 픽만 반영: fast-path:alpha,beta,gamma
```
Before this fix, stderr was empty for this exact scenario.

Regression test added: `test_spawn_cross_family_skill_selection.py`,
class `ConsultJudgeStageTest`, method
`test_fast_path_partial_fill_with_no_remaining_candidates_prints` —
asserts the new line appears and explicitly asserts state 2's "슬롯이 다
참" text does not appear in it, so the two states cannot silently
collapse back into sharing one message.
acceptance: `python3 -m pytest -q test/test_spawn_cross_family_skill_selection.py -k fast_path` — result:
```
2 passed
```

**8th state, left uncovered by design (same disclosure PR #2682's own
record already made, carried forward here rather than silently dropped):**
`role_source["source"] != "skill-repo"` (the `"flat"` fixture shape
exercised by `SkillJudgeLedgerFieldTest.test_ledger_entry_records_not_run_when_role_source_is_not_skill_repo`
in `test_spawn_skill_judge_haiku_timeout_overlap.py`) never enters the
`if role_source["source"] == "skill-repo":` block in `spawn.py`, so
`skill_judge_outcome` stays at its `"not-run"` initial value with no
print — a third silent path the `issue is None` print (scoped inside
that same `if` block) does not cover. Left uncovered because
`resolve_static_policy_source()` always returns `source: "skill-repo"`
in production, per its own return statement in `skills.py` — re-read
this session rather than re-asserted without checking — making this a
synthetic-fixture-only path with no reachable production trigger.

## Why

Item 3's state 4 is the same pattern the original PR fixed for states 1,
2, and 3: a fallback path that returns successfully with nothing
distinguishing it from a healthy run. Per silent-failure-audit's
classification this is "default-value substitution without recording";
fixing state 4 the same way (record which state fired, do not touch the
fallback) keeps the whole enumeration internally consistent instead of
leaving one silent branch using the same reasoning that justified fixing
the other three.

Item 2 applies the same skill's remediation principle to the error
message itself: an error that lists a candidate which will itself fail
one step later is a second, disguised silent failure — the caller is
told "try this" with no signal that "this" was never going to work.
Reusing the resolver's own refusal predicate (`_carries_hooks`) rather
than writing a second definition of "mountable" is what keeps the
candidate list unable to drift from the mount decision again.

Item 1 is a record-accuracy question, not a code question — the fix
(log-only) does not change here. PR #2682's record used a 95%-completion
measurement to justify leaving the timeout budget alone without checking
whether the measured population matched the population the decision was
about. Per api-design-error-design's error-message discipline applied to
the record's own claims, the correction states the population gap
plainly instead of restating the number as settled. Gathering real
consumer-repo trace data is out of scope for this send-back, so the
correction defers rather than fabricates a number.

skill-verdict: silent-failure-audit — applied: invoked; used to classify
item 3's newly-found state 4 as the same "default-value substitution
without recording" pattern PR #2682 used for the other three, and item
2's candidate-list divergence as a second-order silent failure; both
fixes follow the skill's Step 5 remediation (add the missing
record/filter, leave the underlying fallback/refusal behavior alone).
skill-verdict: api-design-error-design — not-applicable: this issue's
surfaces are CLI `sys.exit` messages, stderr log lines, and a markdown
record's own prose — no HTTP problem+json/RFC 9457 envelope or endpoint
is involved.

## What did not work

None — both live reproductions above matched the verification's exact
scenario on the first attempt; no re-dispatch was needed for either.

## Deviations

None. Both code items were fixed inside the scope the send-back named;
the two items the verification did not dispute (item 1's byte-identical
failure set, item 4's non-blocking fail-open) and the log-only fix
itself were left untouched, as instructed.

## Acceptance

acceptance: `python3 -m pytest -q test/test_spawn_skills_mount.py test/test_spawn_role_skill_resolution.py test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py` — result:
```
10 failed, 85 passed
```
derived: `git stash -u && python3 -m pytest -q test/test_spawn_skills_mount.py test/test_spawn_role_skill_resolution.py test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py 2>&1 | grep '^FAILED' | sort > /tmp/before_failed.txt && git stash pop && python3 -m pytest -q test/test_spawn_skills_mount.py test/test_spawn_role_skill_resolution.py test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py 2>&1 | grep '^FAILED' | sort > /tmp/after_failed.txt && diff /tmp/before_failed.txt /tmp/after_failed.txt` — result:
```
(empty diff)
```
the pre-existing network-sandbox failures are the same nodeids before and
after this fix; the passed count of 85 is PR #2682's own 81 plus the 4
new regression tests this fix adds.

acceptance: `python3 -m pytest -q -m "not slow"` — result:
```
16 failed, 501 passed, 3 xfailed
```
derived: same before/after `git stash -u` comparison at full-suite scope — result:
```
(empty diff)
```
the 16 pre-existing failures match the ones the verification's own
from-scratch reproduction already established; 501 passed is the
verification's own 497 plus the 4 new tests.

acceptance: re-derived the per-day population stratification cited in
the appended correction on PR #2682's own record, independently in this
session — `git ls-files 'docs/*consult-log*' 'docs/**/consult-log*' | xargs grep -h "verb=skill_judge"`
piped per day through `grep -c` for the day prefix and for `시간초과` —
result:
```
2026-08-22 total=12 timeout=0
2026-08-23 total=17 timeout=4
2026-08-24 total=50 timeout=1
2026-08-25 total=31 timeout=0
2026-08-26 total=79 timeout=3
2026-08-27 total=13 timeout=0
```
matches, byte for byte, both the verification's own table and the copy
appended into PR #2682's record in this session.

## Upstream basis

`docs/issue-2679/reports/silent-failure-audit+api-design-error-design-3353dd59.md`
at `7e7165e7223a1a25de9b0ead5b8b780780c29ef5` (PR #2682, the deliverable
this send-back fixes) — read in full before starting, code and record
prose alike.
`24e9ea68c0a476c3e42c7aca6caa54de1602b0d7:docs/issue-2679/reports/adversarial-review+conformance-review-sampling-derivation-0d692f76.md:1`
(the independent verification landed on main via PR #2687) — the three
items this record's scope is defined by, plus the two items that
verification left standing; read in full, not excerpted, before deciding
what to fix.

## Open findings

Carried forward from the appended correction on PR #2682's own record
(not duplicated here in full — see that record's "Open findings
(appended)" section):

1. **Population disagreement, still open.** The 95%/8-timeouts figure is
   drawn from this repo's own self-dogfood trace, not the consumer-repo
   population #2071 Defect 1 and its 2026-08-28 recurrence describe.
   Resolution path unchanged from the correction: a follow-up needs real
   consumer-repo trace data before "fail-open is rare" can be asserted
   for that population.
2. **8th not-invoked state, deliberately uncovered.**
   `role_source["source"] != "skill-repo"` has no reachable production
   trigger (`resolve_static_policy_source()` always returns
   `source: "skill-repo"`) — not filed separately, same reasoning PR
   #2682 gave, re-checked rather than re-asserted in this session.

## Next steps

None — `loop_state: landed`.

## Skill verdicts

skill-verdict: silent-failure-audit — applied: invoked; see "Why" above.
skill-verdict: api-design-error-design — not-applicable: see "Why" above.
other mounted skills: not triggered (work-in-english, research-evidence-discipline — guidance-only per their own configuration note, this record's own English-only text already follows work-in-english's intent).
