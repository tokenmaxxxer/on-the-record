---
issue: 2679
role: adversarial-review+silent-failure-audit-9c5cc15d
author: adversarial-review+silent-failure-audit-9c5cc15d
skills: adversarial-review (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
verifies_subject: true  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: e84fb1580abb45c2bd7ee38d00a5f2125759f8ec
loop_state: landed
type: review
breaking: false
verdict: approved
upstream:
  - path: PR #2688 (tokenmaxxxer/on-the-record, branch issue-2679/silent-failure-audit+api-design-error-design-b496a493)
    sha: e84fb1580abb45c2bd7ee38d00a5f2125759f8ec
---

# issue-2679 — adversarial-review+silent-failure-audit-9c5cc15d record

canonical: this session's own independent, from-scratch derivation of the
terminal-state list for `_cross_family_skill_matches_with_consult()` and its
callers, built by reading `consult.py`/`spawn.py`/`skills.py` on PR #2688's
head `e84fb1580abb45c2bd7ee38d00a5f2125759f8ec` before comparing to the PR's
own claimed count, plus two live, self-constructed reproductions run against
a local worktree checkout of that head (not the PR's own test fixtures), is
the live-invocation evidence for the skill-verdict lines below.

skill-verdict: adversarial-review — applied: invoked; treated PR #2688's "7
terminal states, 1 disclosed-uncovered" claim as a claim to independently
re-derive rather than a checklist to confirm, per Step 1-3 of the skill (own
enumeration built first from `consult.py`/`spawn.py` reads, compared to the
PR's count only afterward; two of the PR's confirmatory reproductions
re-built from scratch instead of reusing its test file)
skill-verdict: silent-failure-audit — applied: invoked; classified every
return path of `_cross_family_skill_matches_with_consult()` and its two
callers (Handled=prints before returning, Silently Absorbed=returns/skips
with no print, Unreachable=dead code) per Step 1-2 of the skill, then traced
the one S-classified site (the "8th state" below) forward to confirm it
cannot be reached from any real spawn (Step 3)

## What was done

Narrow, single-claim verification of PR #2688 (branch
`issue-2679/silent-failure-audit+api-design-error-design-b496a493`, head
`e84fb1580abb45c2bd7ee38d00a5f2125759f8ec`): is the PR's "full code
enumeration finds 7 terminal states (not 4)... an 8th, synthetic-fixture-only
state is disclosed as deliberately uncovered" claim actually exhaustive?
Scope per the orchestrator's instructions was this one claim only — the
byte-identical pre-existing-failure-set claim and the candidate-list fix were
already checked upstream and were not re-verified here.

derived: `git fetch origin pull/2688/head:pr-2688 && git worktree add
/tmp/pr2688-check pr-2688 && cd /tmp/pr2688-check && git rev-parse HEAD` —
result:
```
e84fb1580abb45c2bd7ee38d00a5f2125759f8ec
```

Read `_cross_family_skill_matches_with_consult()` (consult.py:607-746) plus
its two call sites — `spawn.py`'s `_spawn_one` (the per-spawn
`skill_judge_outcome` ledger path, spawn.py:3281-3737) and `consult.py`'s
`_composed_consult_skill_source()` (consult.py:749-778) — end to end,
building an independent list of every path that returns without calling
`_skill_judge_consult()` before comparing it to the PR's claimed count.

### Independent enumeration (built before reading the PR's own list)

canonical: own read of consult.py:607-746 and spawn.py:3281-3737 on the
checked-out head above — the eight branches below are quoted verbatim from
that read, not from the PR's description of them.

**Within `_cross_family_skill_matches_with_consult()` itself — 4 return
paths that end without invoking the judge:**

1. **BM25 has zero candidates.** `scored` empty → returns immediately.
```python
    if not scored:
        print(f"[{role}] skill_judge 자문 안 함 — BM25 후보 0개 (no-candidates)",
              file=sys.stderr)
        return [], "no-candidates"
```
(consult.py:635-642) — has its own print, outcome `"no-candidates"`.

2. **Fast-path (exact quoted trigger phrase) picks fill all k slots.**
`remaining <= 0` → returns before building `candidates` at all.
```python
    if remaining <= 0:
        print(f"[{role}] skill_judge 자문 안 함 — fast-path 로 슬롯이 다 참: "
              f"{outcome_prefix}", file=sys.stderr)
        return fast_dirs, outcome_prefix
```
(consult.py:708-714) — has its own print, outcome `"fast-path:<names>"`.

3. **Fast-path fills some but not all slots, and zero BM25 candidates
remain after excluding the fast-path names** (`outcome_prefix` truthy,
`candidates` empty) — this is the PR's fix:
```python
        if outcome_prefix:
            print(f"[{role}] skill_judge 자문 안 함 — fast-path 이후 남은 BM25 "
                  f"후보 0개, fast-path 픽만 반영: {outcome_prefix}", file=sys.stderr)
```
(consult.py:726-728) — before this PR this branch returned silently (see
"Check 2" below for a live before/after-style comparison against its sibling
branch).

4. **No fast-path picks at all, and `candidates` is still empty**
(`outcome_prefix` falsy branch of the same `if not candidates:`):
```python
        else:
            print(f"[{role}] skill_judge 자문 안 함 — fast-path 이후 남은 후보 0개 "
                  f"(no-candidates)", file=sys.stderr)
        return fast_dirs, (outcome_prefix or "no-candidates")
```
(consult.py:729-732).

derived: with no fast-path names, `candidates = scored[:_CROSS_FAMILY_CONSULT_TOPN]`
unfiltered; state 1 above already returns before this point whenever `scored`
is empty; `grep -n '_CROSS_FAMILY_CONSULT_TOPN\s*=' directive_assembly.py` —
result:
```
699:_CROSS_FAMILY_CONSULT_TOPN = 8  # 이슈 본문: consult 에 넘기는 BM25 상위 후보 수
```
a fixed literal, not configurable — so `scored[:8]` can only be empty if
`scored` itself is empty, which state 1 already excludes. Branch 4 is
structurally dead code today; it prints defensively but has no live path.

**Two paths where the judge *is* invoked** (bundled into the PR's count
because the acceptance criteria also asks whether the log distinguishes
success from failure, not because these are "not-invoked" states):

5. Success — consult.py:736-738, prints `"skill_judge 자문 완료"`.
6. Judge call raises (timeout/parse failure/nonzero exit) — consult.py:739-743,
prints `"skill_judge 자문 실패 ... fail-open"`.

**Caller-level — the function is never called at all:**

7. **Adhoc spawn (`--issue` not given).** `_cross_family_future` is never
submitted (`spawn.py:3316-3322` gates the `executor.submit(...)` on
`issue is not None`), so at the join site:
```python
                else:
                    cross_family_dirs, skill_judge_outcome = [], "not-run"
                    print(f"[{role}] skill_judge 자문 안 함 — --issue 없는 스폰이라 "
                          f"자문 자체를 안 던졌다 (not-run)", file=sys.stderr)
```
(spawn.py:3672-3679) — has its own print, ledger outcome `"not-run"`.

8. **`role_source["source"] != "skill-repo"`.** The future *is* submitted
unconditionally whenever `issue is not None` (spawn.py:3318-3322, before the
`role_source["source"] == "skill-repo"` gate at spawn.py:3655), but if that
gate is false the code never reaches the join at spawn.py:3670-3671 — the
future's result is discarded, `skill_judge_outcome` stays at its
spawn.py:3281 initializer `"not-run"`, and no print fires for this branch
specifically.

### Comparing to the PR's claim

My independent count is also 8 branches across the same two files, matching
the PR body's "7 terminal states... plus an 8th disclosed" (my numbering
groups them as 4 not-invoked + 2 invoked + 2 caller-level = 8; the PR's "7 +
1" appears to count the same set with the 8th singled out as the disclosed
exception rather than folded into the base 7 — the underlying branches are
the same set either way).

derived: branch 4's derivation above (candidates = scored[:_CROSS_FAMILY_CONSULT_TOPN]
when fast_names is empty, unreachable given the fixed TOPN=8 and state 1's
guarantee) means branch 4, though real code with its own print, contributes
no live discrepancy against the PR's claim; I did not find a 9th branch it
missed within this function or its two direct callers.

### Check 1 — is the 8th state ("synthetic-fixture-only") actually
unreachable from a real spawn?

canonical: `role_source` is assigned exactly twice in `spawn.py`, both from
functions that hardcode the literal `"skill-repo"` with no conditional
branch producing anything else.

derived: `grep -n 'role_source\s*=' spawn.py` — result:
```
3304:        role_source = resolve_static_policy_source(skill_registry_root)
3685:            role_source = merge_composed_skill_source(role_source, cross_family_dirs)
```

canonical: both producer functions read at skills.py:458 and skills.py:515
return the literal unconditionally:
```python
# skills.py:458 (resolve_static_policy_source)
    return {"source": "skill-repo", "skill_dirs": skill_dirs,
            "skills": [d.name for d in skill_dirs],
            "skill_sha": _sp.skill_repo_sha(skill_dirs[0].parent) if skill_dirs else None}
```
```python
# skills.py:515 (merge_composed_skill_source)
    return {"source": "skill-repo", "skill_dirs": merged_dirs,
```
There is no third producer and no code path that mutates `role_source["source"]`
after assignment.

canonical: the PR's own test at
`test/test_spawn_skill_judge_haiku_timeout_overlap.py:385`
(`test_ledger_entry_records_not_run_when_role_source_is_not_skill_repo`)
confirms this by construction — it can only reach the branch by
monkey-patching `spawn.resolve_static_policy_source` to return a synthetic
`{"source": "flat", ...}` dict that no real code path produces:
```python
    def test_ledger_entry_records_not_run_when_role_source_is_not_skill_repo(self):
        role_source = {"source": "flat", "skill_dirs": [], "skills": [], "skill_sha": None}
        ...
            with mock.patch.object(spawn, "resolve_static_policy_source",
                                   lambda repo_root: role_source), \
```
I found no way to reach this state from an unmodified `_spawn_one()` call —
**Present**: the "deliberately left uncovered because synthetic-fixture-only"
disclosure is accurate, not a hidden production gap.

derived: since `skill_judge_outcome` stays at its `"not-run"` initializer in
this branch, it is byte-identical to state 7's `"not-run"` (adhoc spawn) even
though the underlying situation differs — state 7 never submits the future
at all, state 8 submits it and then abandons the result (and never calls
`_cross_family_executor.shutdown(wait=False)` either, spawn.py:3680-3681 is
also skipped in this branch). This only matters if `role_source["source"]`
ever stops being a hard-coded constant; today the derivation above shows it
provably is, so this is noted under "Open findings" rather than raised as a
blocking finding.

### Check 2 — does the newly-ungated print actually fire on the branch-3b
repro (k=5, 3 fast-path picks, no BM25 candidates remain), and is it
distinguishable from the neighbouring "fills all slots" line?

derived: self-built Python repro (own skill-repo fixture, not the PR's
`test_spawn_cross_family_skill_selection.py` fixture) — a temp skill-repo
with 3 skills, each description carrying a distinct quoted trigger phrase,
all three phrases present in the task text — calling
`spawn._cross_family_skill_matches_with_consult(task_text, "implementation",
repo, 9999, tmp, k=5)` — result:
```
OUTCOME: fast-path:aaa-skill,bbb-skill,ccc-skill
STDERR: [implementation] skill_judge 자문 안 함 — fast-path 이후 남은 BM25 후보 0개, fast-path 픽만 반영: fast-path:aaa-skill,bbb-skill,ccc-skill
```

derived: same fixture, same task text, `k=3` instead (all 3 fast-path picks
exactly fill the slots, the neighbouring "fills all slots" branch) — result:
```
OUTCOME: fast-path:aaa-skill,bbb-skill,ccc-skill
STDERR: [implementation] skill_judge 자문 안 함 — fast-path 로 슬롯이 다 참: fast-path:aaa-skill,bbb-skill,ccc-skill
```

The outcome string returned to the ledger is identical between k=3 and k=5
(`"fast-path:aaa-skill,bbb-skill,ccc-skill"` both times) — confirming the
PR body's claim that this state has "the same outcome-string shape as the
already-fixed 'fast-path fills all slots' case." The stderr message text
differs between the two runs above: "fast-path 로 슬롯이 다 참" (slots fully
filled) vs. "fast-path 이후 남은 BM25 후보 0개, fast-path 픽만 반영" (0 BM25
candidates remain after fast-path) — two different message bodies with
different information content, not the same string with cosmetic rewording.
A reader diffing the two stderr lines above can tell the two states apart
without also inspecting the ledger `skill_judge_outcome` field.

derived: `python3 -m pytest -q test/test_spawn_cross_family_skill_selection.py -k "fast_path or no_bm25 or completed_outcome"` — result:
```
4 passed
```
(the PR's own regression tests, run live rather than only read, to
corroborate the self-built repro above.)

## Why

canonical: this session's own spawning prompt (quoted at the top of this
conversation) states the count history in the sentence below directly.

The task explicitly warned that three prior sessions each raised this same
count (PR #2682 said 4 terminal states, PR #2687's verification found a 5th,
PR #2688 now says 7+1) and asked me not to start from the PR's number and
check it off, since that is exactly the failure mode that let the count
creep three times in a row. Building the list from the code first, then
diffing against the PR's claim, is the only way to catch either an
over-claim or an under-claim without inheriting the PR's own framing.

## What did not work

None — no dead end, no discarded approach, no re-scoping.

## Upstream basis

PR #2688 (`tokenmaxxxer/on-the-record`, branch
`issue-2679/silent-failure-audit+api-design-error-design-b496a493`, head
`e84fb1580abb45c2bd7ee38d00a5f2125759f8ec`), verified via a local worktree
checkout of `refs/pull/2688/head` at `/tmp/pr2688-check`. This record does
not cite the PR's own two report files by path since they live only on the
PR's branch, not in this session's working tree — their claims were read
via `gh pr view 2688` (PR body) rather than filesystem paths from this repo.

## Open findings

One non-blocking observation (not routed as a fix-required finding, since
the branch it concerns is provably unreachable today, per Check 1 above): if
`role_source["source"]` ever stops being an unconditional literal — a fourth
producer function is added to `skills.py` that returns something other than
`"skill-repo"` — the join-skip branch at `spawn.py:3670-3681` would silently
collide with the adhoc-spawn `"not-run"` outcome (same ledger string, no
print) and reopen exactly the "no line, can't tell which state" ambiguity
this PR fixed elsewhere. No action needed now; flagging so a future change
to `resolve_static_policy_source`/`resolve_role_family_source`/
`merge_composed_skill_source` doesn't reintroduce this by surprise.

## Answer to the acceptance question

canonical: Check 1 and Check 2 above (this session's own derivations, not a
summary of them) are the basis for the verdict in this section.

Can a reader of stderr still encounter "no line" and be unable to tell which
of two or more states produced it, for a real spawn? Per the derivations in
Check 1 and Check 2 above: no, for every state reachable from an unmodified
`_spawn_one()` call today — all 4 of the not-invoked return paths inside
`_cross_family_skill_matches_with_consult()` print before returning (branch
4 is dead/unreachable but still prints defensively), both invoked outcomes
(success/fail-open) print, and the caller-level not-invoked adhoc-spawn
state (branch 7) prints. The one remaining silent branch (branch 8,
`role_source["source"] != "skill-repo"`) is real code but was confirmed
unreachable in Check 1's derivation — the PR's "deliberately left
uncovered, synthetic-fixture-only" disclosure is accurate, not a euphemism
for a production gap.

**Present**: the not-invoked enumeration is exhaustive for production
reachability, and the newly-ungated print (branch 3) is both live and
distinguishable from its neighbour (branch 2), per Check 2's derivation.

## Next steps

None — this record closes the one narrow claim assigned to this session.
