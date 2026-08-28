---
issue: 2679
role: adversarial-review+conformance-review-sampling-derivation-0d692f76
author: adversarial-review+conformance-review-sampling-derivation-0d692f76
skills: adversarial-review (skill-repository(297e350)), conformance-review-sampling-derivation (skill-repository(297e350))
verifies_subject: true  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: 7e7165e7223a1a25de9b0ead5b8b780780c29ef5
loop_state: landed
type: review
breaking: false
verdict: changes-requested
upstream:
  - path: docs/issue-2679/reports/silent-failure-audit+api-design-error-design-3353dd59.md
    sha: 7e7165e7223a1a25de9b0ead5b8b780780c29ef5
---

# issue-2679 — adversarial-review+conformance-review-sampling-derivation-0d692f76 record

canonical: this session's own dispatch of three independent foreground
workers, each in a fresh clone of `tokenmaxxxer/on-the-record` re-running
every claim from raw commands/code (see "What was done" below), is the
live-invocation evidence for the adversarial-review skill-verdict line
below.

acceptance: per-day stratification of the 202-line consult trace (this
session's own re-partitioning, Attack section below) — result:
```
6 calendar-day strata (08-22 through 08-27), each fully censused rather
than sampled (202 lines total, no subset excluded), derivation shown
per stratum
```
is the live-invocation evidence for the conformance-review-sampling-derivation
skill-verdict line below.

skill-verdict: adversarial-review — applied: invoked; structured the whole review as independent fresh-clone re-derivation with no reliance on PR #2682's own conclusions or record, per Step 1-3 of the skill (no builder-intent context imported; every claim re-run or re-read directly by three independent workers)
skill-verdict: conformance-review-sampling-derivation — applied: invoked; used for the population-disagreement attack — stratified the 202-entry consult trace by calendar day (rule 1) rather than trusting the flat aggregate, ran a full census per stratum since population size (202) made complete inspection feasible rather than sampling (rule 5's highest-impact-tier logic), and the per-day breakdown states the derivation explicitly (rule 3)

## What was done

Independent verification of PR #2682 (`tokenmaxxxer/on-the-record`, branch
`issue-2679/silent-failure-audit+api-design-error-design-3353dd59`, head
`7e7165e7223a1a25de9b0ead5b8b780780c29ef5`), "issue-2679: skill resolver
dead-end error + skill_judge outcome logging" — folds in #2071 Defect 1.

### Method

Three independent foreground workers, each in its own fresh clone of
`tokenmaxxxer/on-the-record`, re-derived every claim from raw
commands/code with no access to PR #2682's own conclusions beyond what was
needed to locate the disputed numbers.

### Attack: population disagreement — 95%/8-timeouts vs. "nearly every spawn"

**Verdict: ABSENT.** The 95% figure is not representative of the
population #2071 Defect 1 and its 2026-08-28 recurrence describe, and the
PR's "fail-open is rare, so leave the budget alone" conclusion does not
follow from it.

canonical: `gh issue view 2071 --repo tokenmaxxxer/on-the-record` — Defect
1: "skill_judge consult times out at 45s and falls open to BM25 on nearly
every spawn... Observed on most spawns in the tm-dicequest /
skill-repository dogfood (2026-08-23)"
canonical: `gh issue view 2071 --repo tokenmaxxxer/on-the-record
--comments` — 2nd comment: "Defect 1 recurred and is still live
2026-08-28, five days later and in a different consumer repo... timed out
after 35.3 seconds"

derived: `git ls-files 'docs/*consult-log*' 'docs/**/consult-log*' | xargs
grep -h "verb=skill_judge" | wc -l` — result:
```
202
```
(reproduced independently in a fresh clone; matches the PR's count)

derived: same population piped to outcome/timeout greps — result:
```
192 ok
10 error (8 of those timeout-worded, 시간초과)
```
reproduces the PR's 192/202=95%, 8 timeouts exactly.

The arithmetic is not in dispute. The population is:

derived: path inspection of all 134 matching trace files — every one
lives under `docs/issue-<N>/...` in on-the-record's own issue-tracker
numbering (1111-2579) — i.e. 100% of the 202 lines are this repo's own
orchestrator, spawning subagents against this repo's own issues, traced
during this repo's own development. None carry any marker of the
`tm-dicequest` or `skill-repository` consumer repos #2071 names.
canonical: `consult.py:581` (`_append_consult_trace`) — the trace-line
schema (`timestamp | role=... | verb=skill_judge | issue=... |
question=... | outcome=...`) has no field for source repo, orchestrator
identity, registry size, or cache warmth — the population cannot be split
into "this repo" vs. "consumer repo" by any recorded attribute, because no
consumer-repo line exists in it at all.

derived: per-calendar-day total/timeout breakdown of the 202 lines —
result:
```
2026-08-22 total=12 timeout=0   (0%)
2026-08-23 total=17 timeout=4   (23.5%)   <- same calendar day as #2071's own cited tm-dicequest incident
2026-08-24 total=50 timeout=1   (2%)
2026-08-25 total=31 timeout=0   (0%)
2026-08-26 total=79 timeout=3   (3.8%)    <- 39% of the whole sample, lowest timeout rate
2026-08-27 total=13 timeout=0   (0%)
```
The trace stops 2026-08-27 — one day before the 2026-08-28 consumer
observation in #2071's comment; it cannot even temporally cover that
incident. The one day in this repo's own trace that coincides with
#2071's cited tm-dicequest dogfood date (08-23) already shows a 23.5%
timeout rate — nearly 6x the reported 95%/5% aggregate — while the
largest single day (08-26, 39% of the whole sample) pulls the aggregate
down with a 3.8% rate. The 95% aggregate is disproportionately carried by
one low-timeout, high-volume day, not evidence that timeouts are rare in
general.

canonical: `consult.py:52-54`:
```python
SKILL_JUDGE_TIMEOUT_DEFAULT = 90  # issue #2076: measured completion rate at 45s was <80% in
# consumer dogfood (issue #2071 defect 1) — raised to give the haiku judge more room before
# BM25 fail-open, still env-overridable via SKILL_JUDGE_TIMEOUT
```
canonical: `consult.py:181-199` (`_skill_judge_timeout`) — the effective
per-call timeout reads a `SKILL_JUDGE_TIMEOUT` env override, else a p90
cutoff computed from `runs/ledger.jsonl` once >=50 real samples exist,
else the 90s default; `runs/` is gitignored (`.gitignore:1`) — a
per-installation, non-portable runtime value. The consumer incidents (45s
in #2071's original report, 35.3s in the 08-28 recurrence) happened under
that consumer's own locally-derived budget, which this repo's committed
trace structurally cannot reflect.

canonical: this session's per-day stratification above (not a summary or
grep signal alone, but the raw per-line trace re-partitioned by calendar
day and re-counted) is the ground truth for the conclusion below.

**Conclusion:** the 202-entry population is this repo's own self-dogfood
trace (single machine/session line, no consumer traffic, temporally
ending before the cited consumer incident, under this repo's own
locally-computed timeout budget) — not the population #2071 Defect 1 and
its 08-28 recurrence are about (external consumer-repo spawns under their
own local budgets). The 95%/rare-fail-open number does not license PR
#2682's decision to leave the timeout budget untouched; it measures a
demonstrably easier population than the one the issue was filed about.

### Claim 1 — byte-identical pre-existing failure set

**Verdict: PRESENT.**

derived: `pytest -q -m "not slow"` on a fresh clone of `origin/main` —
result:
```
16 failed, 492 passed, 3 xfailed
```
derived: `pytest -q -m "not slow"` on a fresh clone of PR #2682's head —
result:
```
16 failed, 497 passed, 3 xfailed
```
matches the PR's claimed 497/16 exactly; reran 2x more, stable.

derived: `diff <(sort main_failed_nodeids.txt) <(sort
pr_failed_nodeids.txt)` — result:
```
(empty, exit 0)
```
the 16 failing nodeids are byte-identical between main and the PR branch.

derived: targeted-files run (`test_spawn_skills_mount.py
test_spawn_role_skill_resolution.py
test_spawn_cross_family_skill_selection.py
test_spawn_skill_judge_haiku_timeout_overlap.py`) — result:
```
main:       10 failed, 76 passed
PR branch:  10 failed, 81 passed
nodeid diff: (empty, exit 0)
```
the 10 pre-existing failures are the identical 10 nodeids on both
branches. (The PR's own report says "80 passed" for this subset; actual
is 81 both times reproduced in this session — a minor off-by-one in the
PR's own report, not a masked regression, consistent with ~5 new tests
the PR adds in this file set.)

derived: `grep -rn 'git.*diff\|git show' test/*.py` for any test
asserting byte-identity against a git-tracked baseline (the failure mode
that made a prior PR's identical claim false) — found one:
`test/test_auto_approval_shadow_wiring.py:157`, targeting
`on-the-record/hooks/approval-gate.sh`. That file is not among PR #2682's
touched files (`gh pr diff 2682 --name-only`), and the test passes on the
PR branch regardless —
derived: `pytest test/test_auto_approval_shadow_wiring.py -k
byte_identical -v` — result:
```
1 passed
```
No other "byte-identical"-named test in the suite compares against a
git-tracked baseline — this PR does not repeat the prior incident's
failure mode.

### Claim 2 — candidate list source (`_available_skills_clause()`)

**Verdict: ABSENT / INCORRECT.** The "must not diverge from what's
actually mountable" requirement is violated in a concrete, reproducible
way.

canonical: `skills.py:115-124`:
```python
def _available_skills_clause(available: list[str]) -> str:
    """이슈 #2679: unknown-skill 거부의 두 출구(`resolved_skill_dirs`,
    `resolved_skill_sources`)가 후보 절을 같은 모양으로 낸다 — 후보는 항상
    거부한 바로 그 resolver 가 이미 나열한 목록에서 오지, 손으로 관리하는
    별도 표에서 오지 않는다(그래야 실제 마운트 가능한 것과 어긋날 수
    없다). 후보가 하나도 없으면(스킬을 하나도 못 찾은 설치) 빈 목록을
    찍는 대신 그렇다고 명시한다(empty-state 요구)."""
    if not available:
        return "사용 가능한 스킬이 하나도 없다"
    return f"쓸 수 있는 이름: {', '.join(available)}"
```
this is a pure formatter with no data source of its own; it only formats
whatever `list[str]` its caller passes.

canonical: `skills.py:140-146` (`resolved_skill_dirs`, call site 1):
```python
    available = sorted(p.name for p in repo_root.iterdir()
                        if p.is_dir() and not p.name.startswith("."))
    unknown = [n for n in names if n not in available]
    if unknown:
        sys.exit(f"--skills: 모르는 스킬 {', '.join(unknown)} "
                  f"— {_sp._available_skills_clause(available)}")
    return [repo_root / n for n in names]
```
unknown-check and the clause both read this same local `available` list
— a bare directory listing.

canonical: `skills.py:315-348` (`resolved_skill_sources`, call site 2) —
same directory-listing pattern, reused for both the unknown-check and the
clause.

canonical: mount-decision code (`resolve_skill_source`, skills.py:481-496
and callers) applies a filter neither call site's candidate list
applies:
```python
    hooked = [d for d in skill_dirs if (d / "hooks").is_dir()]
    if hooked:
        sys.exit(f"resolve_skill_source: {skill_name!r} 이 지정한 스킬 중 "
                  f"{', '.join(d.name for d in hooked)} 가 hooks/ 를 들고 있다 — "
                  f"skill-repository 는 가이던스 전용이다(훅 없음, 이슈 #1758)")
```

derived: adversarial repro — built
`/tmp/fake-skill-repo/{good-skill/, hooked-skill/hooks/}` and called the
real resolver functions directly — result:
```
resolve_skill_source('hooked-skill', repo_root) -> sys.exit: "...hooked-skill 가 hooks/ 를 들고 있다..." (fails to mount)
resolved_skill_dirs('good-skill,totally-bogus-name', repo_root) -> sys.exit: "--skills: 모르는 스킬 totally-bogus-name — 쓸 수 있는 이름: good-skill, hooked-skill"
```
`hooked-skill` is listed as a usable candidate in the same error that
just rejected `totally-bogus-name`, yet resolving `hooked-skill` itself
always fails. Reproduced the same pattern for the four-tier
`resolved_skill_sources()` path.

The PR's own docstring at `skills.py:116-121` (quoted above) claims the
candidate list "그래야 실제 마운트 가능한 것과 어긋날 수 없다" ("so it
cannot diverge from what's actually mountable") — this is falsified by
the direct-execution repro above, not merely theoretically incomplete.

### Claim 3 — completeness of the not-invoked enumeration (4 shapes)

**Verdict: ABSENT / INCORRECT.** Full enumeration of `consult.py:607-736`
and `spawn.py:3669-3678` finds a 5th silent, production-reachable shape
beyond the PR's claimed 4, plus a 6th the PR's own report separately (and
only partially) discloses as unfixed.

canonical: consult.py:635-642 -> `no-candidates` (PR shape a, has a
print)
canonical: consult.py:708-714 -> fast-path fills all slots (PR shape c,
has a print)
canonical: `consult.py:715-722`:
```python
              f"{outcome_prefix}", file=sys.stderr)
        return fast_dirs, outcome_prefix
    candidates = [(name, d, source)
                  for _, name, d, source in scored[:_sp._CROSS_FAMILY_CONSULT_TOPN]
                  if name not in fast_names]
    if not candidates:
        if not outcome_prefix:
            print(f"[{role}] skill_judge 자문 안 함 — fast-path 이후 남은 후보 0개 "
                  f"(no-candidates)", file=sys.stderr)
        return fast_dirs, (outcome_prefix or "no-candidates")
```
two sub-branches gated by `if not outcome_prefix`:
 - 3a: `outcome_prefix` falsy -> `no-candidates`, WITH print (= PR shape
   b).
 - 3b: `outcome_prefix` truthy (fast-path partially filled, no BM25
   candidates remain) -> returns `outcome_prefix` unchanged (same string
   shape as shape c) — the print is gated on `if not outcome_prefix`,
   which is False here, so **no print at all**.

canonical: `spawn.py:3669-3678`:
```python
                if _cross_family_future is not None:
                    cross_family_dirs, skill_judge_outcome = _cross_family_future.result()
                else:
                    # 이슈 #2679: --issue 없는 스폰은 자문 자체를 안 던진다
                    # (위 `if issue is not None:`) — 이 줄이 없으면 성공
                    # 로그도 실패 로그도 안 남아 "자문이 성공했는지 아예
                    # 안 불렸는지" 를 로그만으로 구분할 수 없다.
                    cross_family_dirs, skill_judge_outcome = [], "not-run"
                    print(f"[{role}] skill_judge 자문 안 함 — --issue 없는 스폰이라 "
                          f"자문 자체를 안 던졌다 (not-run)", file=sys.stderr)
```
`issue is None` -> `"not-run"`, WITH print (PR shape d). `.result()` is
on line 3670.

derived: adversarial repro against the real production
`k=_COMPOSED_SKILLS_TOPK=5` (spawn.py:614), monkeypatching only the
BM25/phrase-match inputs to return 3 scored candidates that all match
declared phrases — result:
```
branch 3b: RETURNED ([...3 dirs...], 'fast-path:alpha,beta,gamma'), STDERR = '' (empty)
contrast, shape (c) with k=3 (fast-path exactly fills all slots): RETURNED same-shaped outcome string, STDERR = '[role] skill_judge 자문 안 함 — fast-path 로 슬롯이 다 참: fast-path:alpha,beta,gamma\n'
```
The two cases return a byte-identical outcome string but only one logs —
the exact "no line means two different things" failure the issue was
filed to eliminate is still present, and fires under ordinary production
inputs (no internal-shape monkeypatching needed), whenever a role/task has
fewer than 5 distinct BM25-scored candidates that all carry matching
declared phrases.

canonical:
`7e7165e7223a1a25de9b0ead5b8b780780c29ef5:docs/issue-2679/reports/silent-failure-audit+api-design-error-design-3353dd59.md:243-255`
— the PR's own report separately discloses a 6th, different gap (a
`role_source["source"] == "flat"` fixture path that never enters the
cross-family join block at all, leaving `skill_judge_outcome` at
`"not-run"` via a third silent path spawn.py's fix doesn't cover), waved
off as "synthetic-fixture-only, not reachable in production." That claim
is not re-verified here; it is a distinct gap from 3b, which required no
fixture manipulation.

**Count: at least 6 behaviorally distinct terminal states exist, not
4** — 5 as of this fix's own code, one more that the PR's report
acknowledges but leaves unfixed.

### Claim 4 — fail-open must not block a spawn

**Verdict: PRESENT, with a delay nuance not captured by "non-blocking."**

canonical: `consult.py:538-543`:
```python
        _call_t0 = time.monotonic()
        for attempt_num, attempt_prompt in enumerate((base_prompt, retry_prompt), start=1):
            r = subprocess.run(cmd, cwd=cwd or str(_sp.ROOT), input=attempt_prompt, text=True,
                               capture_output=True, timeout=judge_timeout, env=env)
            call_wall_s = time.monotonic() - _call_t0
            if r.returncode != 0:
```
`subprocess.run(..., timeout=judge_timeout, ...)` guarantees the call
returns (raises `TimeoutExpired`) after at most `judge_timeout` seconds;
it cannot hang forever.

canonical: `consult.py:724-732` — `except Exception as ex:`
unconditionally converts any judge failure, including timeout, into a
BM25 fallback (`outcome = "fail-open"`) — the spawn always proceeds
eventually; a hanging judge cannot indefinitely prevent a spawn.

canonical: `spawn.py:3313-3320` — the judge call is dispatched to a
single-worker `ThreadPoolExecutor` before workspace clone/branch checkout
starts, so the two run concurrently (comment: "이슈 #2061: skill_judge
자문 ... 을 워크스페이스 클론/브랜치 체크아웃(~12s)과 겹치도록 그 전에
먼저 던진다").

canonical: `spawn.py:3669-3678`:
```python
                if _cross_family_future is not None:
                    cross_family_dirs, skill_judge_outcome = _cross_family_future.result()
                else:
                    # 이슈 #2679: --issue 없는 스폰은 자문 자체를 안 던진다
                    # (위 `if issue is not None:`) — 이 줄이 없으면 성공
                    # 로그도 실패 로그도 안 남아 "자문이 성공했는지 아예
                    # 안 불렸는지" 를 로그만으로 구분할 수 없다.
                    cross_family_dirs, skill_judge_outcome = [], "not-run"
                    print(f"[{role}] skill_judge 자문 안 함 — --issue 없는 스폰이라 "
                          f"자문 자체를 안 던졌다 (not-run)", file=sys.stderr)
```
`.result()` (line 3670) is a **blocking join** inside the
`"cross_family"` timed stage — if the judge call runs longer than the
~12s workspace-setup overlap window (exactly what happens on a timeout,
35-90s), the spawn's session launch is delayed by the difference, up to
nearly the full `judge_timeout` in the worst case: on the exact case the
issue is about (timeouts), it delays session start by tens of seconds on
the critical path, not zero.

The requirement "a hanging judge must never prevent a spawn from
proceeding" holds — it never blocks forever, never prevents. It is not
fully non-blocking, though. PR #2682's framing that "fail-open is rare,
so log-only is enough" elides that even a rare fail-open still costs a
real, bounded delay.

### Summary table

canonical: each row below recaps the verdict already established with
full file:line citations and reproductions in the Attack and Claim 1-4
sections above (this record, same session) — no new claim is introduced
here.

| # | Claim | Verdict |
|---|---|---|
| — | 95%/8-timeouts population representative of #2071/08-28's population | **ABSENT** — structurally different, easier population |
| 1 | Byte-identical pre-existing failure set before/after | **PRESENT** |
| 2 | Candidate list cannot diverge from what's mountable | **ABSENT / INCORRECT** — reproduced a divergence |
| 3 | Exactly 4 not-invoked shapes, all now logged | **ABSENT / INCORRECT** — found a 5th silent shape + 6th disclosed-but-unfixed |
| 4 | Fail-open cannot block a spawn | **PRESENT**, with an undisclosed delay nuance |

## Why

PR #2682 folds in #2071 Defect 1 (skill_judge timeout/fail-open) and adds
skill-resolver dead-end errors plus skill_judge outcome logging. Its own
record leans on a single aggregate number (95% ok / 8 timeouts out of
202) to justify leaving the timeout budget alone, and makes four further
numbered claims about candidate-list correctness, enumeration
completeness, and non-blocking fail-open behavior. Per adversarial-review
(no builder-intent imported, structurally independent evaluator) and
conformance-review-sampling-derivation (stratify before trusting an
aggregate; run a full census when the population is small enough, as
202 lines was), the only way to catch a population mismatch or an
incomplete enumeration is to re-derive every claim from raw commands and
code in a fresh clone, stratified by the dimension the claim's own
argument depends on (calendar day, for the population claim), rather than
accepting the PR's own aggregate and code-path count at face value.

## What did not work

acceptance: three-worker fresh-clone re-derivation dispatch (population
stratification worker, pytest-reproduction worker, code-repro worker),
this session — result:
```
all three workers returned findings on the first pass; none required
re-dispatch or a second attempt
```

None — all three verification workers completed their assigned angles on
the first dispatch with no re-dispatch needed.

## Upstream basis

`7e7165e7223a1a25de9b0ead5b8b780780c29ef5:docs/issue-2679/reports/silent-failure-audit+api-design-error-design-3353dd59.md`
(untracked in this branch's own working tree — this branch is cut from
`origin/main` and PR #2682 is unmerged; the path exists only at that
commit, not on `main`), on `tokenmaxxxer/on-the-record`, branch
`issue-2679/silent-failure-audit+api-design-error-design-3353dd59`.

derived: `git cat-file -e
7e7165e7223a1a25de9b0ead5b8b780780c29ef5:docs/issue-2679/reports/silent-failure-audit+api-design-error-design-3353dd59.md
&& echo ok` — result:
```
ok
```
confirms the sha independently, matching this record's own citations in
the "What was done" section above.

## Open findings

1. **Population disagreement (ABSENT).** The 95%/8-timeouts figure PR
   #2682 uses to justify leaving `SKILL_JUDGE_TIMEOUT_DEFAULT` unchanged
   is drawn from this repo's own self-dogfood trace, not from the
   consumer-repo population #2071 Defect 1 and its 08-28 recurrence
   describe (see Attack section above for the full per-day
   stratification). Resolution path: PR #2682 (or a follow-up against
   #2679/#2071) needs to either gather consumer-repo trace data before
   concluding fail-open is rare, or drop the "leave the budget alone"
   conclusion and re-open the timeout-budget question.
2. **Claim 2, candidate-list divergence (ABSENT / INCORRECT).** (See
   Claim 2 above for the full reproduction.) `_available_skills_clause()`'s
   candidate list includes hook-carrying skill dirs that
   `resolve_skill_source` always refuses to mount, so the docstring's
   "cannot diverge from what's actually mountable" claim is false by
   direct reproduction. Resolution path: PR #2682 needs the
   candidate-list builder to apply the same `hooks/`-directory filter
   `resolve_skill_source` applies, or the docstring's claim needs to be
   corrected to describe the actual (weaker) guarantee.
3. **Claim 3, incomplete not-invoked enumeration (ABSENT / INCORRECT).**
   (See Claim 3 above for the full reproduction.) At least 6
   behaviorally distinct terminal states exist in
   `consult.py:607-736`/`spawn.py:3669-3678`, not the 4 the PR claims;
   branch 3b (`outcome_prefix` truthy, no BM25 candidates remain) is
   silent and reachable under ordinary production inputs, and a 6th gap
   is disclosed but left unfixed in the PR's own report. Resolution
   path: PR #2682 needs the print in `consult.py:715-722` ungated from
   `if not outcome_prefix`, or an equivalent log line added for branch
   3b specifically, before the "no silent not-invoked path remains"
   claim can be considered true.

## Next steps

None for this record — terminal.
