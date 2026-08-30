---
issue: 2803
role: adversarial-review-b1ff090f
author: adversarial-review-b1ff090f
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2808, this issue's own deliverable
loop_state: landed
upstream:
  - path: b5dae50d948e2afa9a4a80c5b0d4f44afaf10da9:test/test_spawn_attempt_staleness.py
    sha: b5dae50d948e2afa9a4a80c5b0d4f44afaf10da9
  - path: b5dae50d948e2afa9a4a80c5b0d4f44afaf10da9:docs/issue-2803/reports/technical-writing-style-guide-compliance-632a1d33.md
    sha: b5dae50d948e2afa9a4a80c5b0d4f44afaf10da9
---

# issue-2803 — adversarial-review-b1ff090f record

derived: `grep -m1 "^description:" /home/jwjung/skill-registry/skills/adversarial-review/SKILL.md` — trigger matched: this task is exactly "independent adversarial evaluation" of a prior session's PR.
skill-verdict: adversarial-review — applied: invoked; loaded the skill's full procedure this turn and followed it — this session is itself the structurally-independent evaluator the skill describes (fresh context, no access to PR #2808's builder session), so I re-derived every check from scratch on the PR's own branch rather than citing its record's stated results.
skill-verdict: work-in-english — not-applicable: this task's prompt is in English; commits/PR/record follow existing repo convention in English regardless.
skill-verdict: implementation-audit — not-applicable: this is a direct independent-verification pass against the issue's stated acceptance checks and my own re-derivation, not the two-session falsifiable-claim-extraction protocol implementation-audit describes.

## What was done

Independent re-verification of PR #2808 (`issue-2803/technical-writing-style-guide-compliance-632a1d33`,
head `b5dae50d948e2afa9a4a80c5b0d4f44afaf10da9`), which renames six comment/
docstring "role"/"role family" occurrences in `test/test_spawn_attempt_staleness.py`
to "skill"/"skill family". Checked out the PR's actual branch into a scratch
`git worktree` (not just its diff text) and re-ran every check independently
with my own commands rather than citing the PR record's stated results.

canonical: `gh pr view 2808 --json state,headRefName,baseRefName` (executed this turn) — result:
```
state: OPEN
headRefName: issue-2803/technical-writing-style-guide-compliance-632a1d33
baseRefName: main
```

acceptance: `grep -inE '\brole\b' test/test_spawn_attempt_staleness.py` on the PR branch checkout — result:
```
(no output, exit 1 — zero matches)
```

acceptance: before/after test-name-set comparison — `git worktree add /tmp/pr2808-check origin/issue-2803/technical-writing-style-guide-compliance-632a1d33`, then in each of that worktree and this branch: `python3 -m pytest test/test_spawn_attempt_staleness.py -v | grep -E '^test/test_spawn_attempt_staleness.py::' | sed -E 's/ (PASSED|FAILED|ERROR).*$//' | sort > <file>; diff before after` — result:
```
before: 41 lines, after: 41 lines
diff /tmp/before_names.txt /tmp/after_names.txt: (no output — identical sets)
both runs: "41 passed"
```

acceptance: `git merge-base origin/main origin/issue-2803/technical-writing-style-guide-compliance-632a1d33` — result:
```
2d53e0fe9cf25eb1643a296987d462dcee447100
```
(this is PR #2808's actual branch point — three unrelated PRs, #2805/#2807/#2809,
merged to `origin/main` after PR #2808 branched, so diffing against current
`origin/main` directly shows unrelated `gates/*.py`/`watchdog.py` churn that
is not part of this PR; I re-ran the stat diff against the merge-base instead)

acceptance: `git diff --stat 2d53e0fe origin/issue-2803/technical-writing-style-guide-compliance-632a1d33` — result:
```
 .../reports/technical-writing-style-guide-compliance-632a1d33.md | 191 +++++++++++++++++++++
 .../2026-08-30-hunt-role-to-skill-rename-comment-only.md         |  58 +++++++
 test/test_spawn_attempt_staleness.py                             |  12 +-
 3 files changed, 255 insertions(+), 6 deletions(-)
```
derived: this stat output — 2 new files under `docs/issue-2803/reports/`,
1 pre-existing file (`test/test_spawn_attempt_staleness.py`) changed, 0
other pre-existing `docs/` files touched.

Every changed line in `test/test_spawn_attempt_staleness.py` is inside a
docstring or `#` comment — confirmed by reading the full line-level diff
(`git diff 2d53e0fe origin/issue-2803/technical-writing-style-guide-compliance-632a1d33 -- test/test_spawn_attempt_staleness.py`,
quoted in full under invariant 1 below), which shows only the six
`-role...`/`+skill...` prose substitutions with no `assert`/identifier
tokens touched.

acceptance: full-suite regression, `python3 -m pytest test/ -q` on `origin/main` (this checkout) — result:
```
15 failed, 425 passed, 3 xfailed in 31.79s (real 0m32.102s)
```

acceptance: full-suite regression, `python3 -m pytest test/ -q` in the PR-branch worktree — result:
```
15 failed, 425 passed, 3 xfailed in 32.03s (real 0m32.341s)
```

acceptance: `diff <(pytest test/ -q on main | grep '^FAILED' | sed -E 's/ -.*$//' | sort) <(same on PR branch)` — result:
```
(no output — identical 15-name failing sets both sides)
```
Runtime difference (32.10s vs 32.34s) is run-to-run noise, not a regression;
identical pass/fail/xfail counts both sides (`425 passed, 3 xfailed` both,
per the two acceptance blocks above) means monitor/watch-relevant test
collection did not shrink — nothing went quieter.

## Why

canonical: this session's own task prompt (verbatim instruction) — asks to
re-derive rather than restate the PR's own record, to verify the sweep's
cited commands actually cover the claimed population ("a previous delivery
claimed a 49-file population while its cited commands reached only 34 —
that is twice now on this issue"), and to confirm the renamed prose matches
what the code actually does rather than merely checking that the retired
word is gone.

## Findings

**Finding 1 — sweep command result misreported (test/ population).**

canonical: `b5dae50d948e2afa9a4a80c5b0d4f44afaf10da9:docs/issue-2803/reports/technical-writing-style-guide-compliance-632a1d33.md` (`git show b5dae50d:docs/issue-2803/reports/technical-writing-style-guide-compliance-632a1d33.md`; this file exists on the PR's own branch, not in this record's worktree), "Search population" item 2 — quoted verbatim:
```
acceptance: `grep -rlnE '_skill_family|_attempt_superseded' test/` — result:
test/test_spawn_attempt_staleness.py
(the mechanism is exercised only in the file already fixed — no other
file describes it, so there is nothing else in this population to check.)
```

acceptance: re-running that exact command on the PR's own base commit — `git checkout 2d53e0fe -- .` in a scratch worktree, then `grep -rlnE '_skill_family|_attempt_superseded' test/` — result:
```
test/test_consult_no_rulebook_identity_regression.py
test/test_spawn_model_override.py
test/test_spawn_attempt_staleness.py
```
Three files, not one. The other two match because `_skill_family` is a
substring of `resolve_skill_family_source` (a different function, defined
at `skills.py:463`), which both files reference.

canonical: `b5dae50d948e2afa9a4a80c5b0d4f44afaf10da9:docs/issue-2803/reports/technical-writing-style-guide-compliance-632a1d33.md`, "Open findings" section of the same document — quotes the literal string `resolve_skill_family_source` as present in `test/test_consult_no_rulebook_identity_regression.py`. That document therefore names this exact file, in a different section, as containing `resolve_skill_family_source` — directly contradicting its own item-2 claim (quoted above) that the `_skill_family|_attempt_superseded` grep returns only one file. `test/test_spawn_model_override.py`'s hit for the same command is not mentioned anywhere in that document.

acceptance: `grep -nE '_skill_family|_attempt_superseded' test/test_spawn_model_override.py test/test_consult_no_rulebook_identity_regression.py` (this checkout, current `origin/main`) — result:
```
test/test_spawn_model_override.py:75:        self._orig_resolve_skill_family_source = spawn.resolve_skill_family_source
test/test_spawn_model_override.py:77:        spawn.resolve_skill_family_source = lambda skill, repo_root: {
test/test_spawn_model_override.py:89:        spawn.resolve_skill_family_source = self._orig_resolve_skill_family_source
test/test_consult_no_rulebook_identity_regression.py:66:    def test_mapped_skill_reaches_resolve_skill_family_source(self):
test/test_consult_no_rulebook_identity_regression.py:68:        real = spawn.resolve_skill_family_source
test/test_consult_no_rulebook_identity_regression.py:74:        spawn.resolve_skill_family_source = spy
test/test_consult_no_rulebook_identity_regression.py:78:            spawn.resolve_skill_family_source = real
test/test_consult_no_rulebook_identity_regression.py:81:    def test_unmapped_skill_still_reaches_resolve_skill_family_source(self):
test/test_consult_no_rulebook_identity_regression.py:86:        real = spawn.resolve_skill_family_source
test/test_consult_no_rulebook_identity_regression.py:92:            spawn.resolve_skill_family_source = spy
test/test_consult_no_rulebook_identity_regression.py:96:            spawn.resolve_skill_family_source = real
```
Every hit in both files is `resolve_skill_family_source`, never
`_skill_family()`/`_attempt_superseded()` themselves — so "the mechanism is
exercised only in `test_spawn_attempt_staleness.py`" remains true once the
substring false-positives are filtered out. But that filtering step is not
performed or disclosed anywhere in the cited document — it states a
single-file command result that does not match what the command actually
produces when run. This is the same shape the task's own prompt named as
having already happened once on this issue (49-vs-34), now a second,
independently-confirmed instance on this same issue.

**Finding 2 — the rename's central justification overclaims what the cited code says.**

canonical: `b5dae50d948e2afa9a4a80c5b0d4f44afaf10da9:docs/issue-2803/reports/technical-writing-style-guide-compliance-632a1d33.md`, "What was done" section — quoted verbatim: "the code's own vocabulary is 'skill family', never 'role family'", citing `spawn.py:1399-1438` as the basis.

canonical: `spawn.py:1399-1438` (read directly this turn) — result:
```python
def _skill_family(skill: str) -> str:
    """`role`에서 lease 분해자 접미사를 떼 role family 를 돌려준다. 접미사가
    없으면(분해자 없이 role 을 직접 넘긴 옛 호출부/테스트 픽스처) role 을
    그대로 돌려준다 — family 는 "role 에서 알아낼 수 있는 가장 넓은, 그러나
    여전히 issue 번호와 함께 써야 안전한 식별자"이지, "항상 접미사가 있다"는
    가정이 아니다."""
    return _LEASE_DISAMBIGUATOR_SUFFIX_RE.sub("", skill or "")


def _attempt_superseded(attempt_id: str, attempt: dict, attempts: dict,
                         outcomes: dict) -> bool:
    """`attempt`(halt 가 아직 클래스 재확인으로는 안 풀린 것으로 나온 시도)가
    같은 작업(issue + role family)에 대한 더 나중의 성공한(`"session-log"`)
    시도로 superseded 됐는지 본다. 위 모듈 주석 참고 — 매칭 규칙과 증거
    위치의 근거는 거기 있다.

    보수적 기본값: issue/role/ts 중 하나라도 없거나 타입이 안 맞으면
    `False`(판정 불가 — 아직 안 풀림 쪽으로) — `_halt_condition_cleared`와
    같은 fail-safe 방향."""
```
`_skill_family()`'s and `_attempt_superseded()`'s own docstrings use "role"/
"role family" seven times inside the exact `1399-1438` line range the PR's
record cites as proof the code "never" uses that wording.

acceptance: `git log --oneline -L 1399,1417:spawn.py` — result (truncated to the two relevant commits):
```
e1f390ab issue-2600: retire role/역할 Python and shell identifiers (slice 4) (#2731)
    -def _role_family(role: str) -> str:
    +def _skill_family(skill: str) -> str:
         """`role`에서 lease 분해자 접미사를 떼 role family 를 돌려준다. ...
8fcc2654 issue-2511: resolve halted spawn-attempts superseded by a later successful retry (#2621)
    +def _role_family(role: str) -> str:
    +    """`role`에서 lease 분해자 접미사를 떼 role family 를 돌려준다. ...
```
PR #2731 (`e1f390ab`, `issue-2600` slice 4) renamed the identifiers
(`_role_family`→`_skill_family`, parameter `role`→`skill`) but left the
Korean docstring prose describing them unchanged since PR #2621 (`8fcc2654`)
first introduced it.

This does not make the six renamed test-file sentences false: the code's
actual identifiers (`_skill_family(skill)`'s parameter name, the
`attempt["skill"]` dict key used at `spawn.py:1419,1429`) genuinely are
"skill", so "same skill family, different issue" is an accurate behavioral
description independent of the stale docstring prose. But the record's
stated justification — that the cited lines prove the code "never" says
"role family" — is directly contradicted by those same lines (quoted
above), and it leaves `spawn.py` itself carrying the identical stale-wording
pattern this PR fixed in the test file, undiscovered because the sweep was
scoped to `test/` only.

## Open finding disposition (task-directed: judge scope, cite lines)

canonical: `b5dae50d948e2afa9a4a80c5b0d4f44afaf10da9:docs/issue-2803/reports/technical-writing-style-guide-compliance-632a1d33.md`, "Open findings" section — leaves `resolve_skill_family_source()` as an open finding for a separate follow-up, citing `test/test_consult_no_rulebook_identity_regression.py` lines 10 and 54 as carrying a nonexistent literal `resolve_role_family_source()`.

acceptance: `sed -n '10p;54p' test/test_consult_no_rulebook_identity_regression.py` (this checkout) — result:
```
10:   `resolve_role_family_source()` — 고정 role->skill 표
54:    접두어로 무엇을 유도하든(있음/없음 모두) 언제나 `resolve_role_family_source()`
```

canonical: `skills.py:463` (read directly this turn) — result:
```python
def resolve_skill_family_source(skill: str, repo_root: Path | None) -> dict:
    """이슈 #2561: `consult.py`(consult/verb/skill_judge/panel 세션)와
    judge 세션의 role 축 기준선 — `_ROLE_SKILLS` 정적 표 없이, 실제
    skill-repository 디렉터리 이름이 `f"{role}-"` 로 시작하는 스킬 전부를
    매 호출마다 기계적으로 유도한다...
```

I agree with the PR's routing, independently confirmed: `resolve_skill_family_source(skill, repo_root)` is defined at `skills.py:463` and resolves skill-repository *source directories* by name-prefix (issue #2561) — a different mechanism, in a different file, from `spawn._skill_family()`/`spawn._attempt_superseded()`'s lease-disambiguator stripping and attempt-supersession matching (`spawn.py:1399-1438`, issue #2511).

canonical: `gh issue view 2803` (executed this turn), "Non-goals" section — quoted verbatim: "The wider `#2600` identifier slice and the `#2626` completion judgement — this is one measured, located instance, filed so it is not folded into an open question."

Given that Non-goals text, the `resolve_skill_family_source()` staleness belongs to a new, separately-scoped follow-up issue, not #2803 — consistent with how #2803 itself originated as a split-off from #2798's sweep (per issue #2803's own body, read this turn via `gh issue view 2803`) rather than being folded into #2798.

A second candidate for that same follow-up bucket, found by this review and absent from the PR's own record: `spawn.py:1399-1417`'s own docstrings (quoted in Finding 2 above) carry the identical "stale role-vocabulary prose describing a live, already-renamed mechanism" shape that #2803 fixes in the test file — just located in the source file the test exercises, rather than in the test itself. Per the same Non-goals carve-out, this is `#2600` identifier-slice territory, not #2803's — reported here as a second open item for that follow-up, not as a blocker on this PR's closure.

## Standing invariants (task-directed, each with executed command + output)

1. **No return of the retired role axis in any reshaped form.**
   acceptance: `grep -inE '\brole\b' test/test_spawn_attempt_staleness.py` on the PR branch — result:
   ```
   (no output, exit 1)
   ```
   acceptance: `git diff 2d53e0fe origin/issue-2803/technical-writing-style-guide-compliance-632a1d33 -- test/test_spawn_attempt_staleness.py | grep -E '^[+-]' | grep -v '^[+-][+-][+-]'` — result:
   ```
   -    `secrets.token_hex(4)`) that `spawn.py:1990-1991` appends to every role
   +    `secrets.token_hex(4)`) that `spawn.py:1990-1991` appends to every skill
   -        """Over-broadening guard: same role family, different issue — must
   +        """Over-broadening guard: same skill family, different issue — must
   -        """Over-broadening guard: same issue, different role family — an
   +        """Over-broadening guard: same issue, different skill family — an
   -    (issue, role-family) must still resolve it."""
   +    (issue, skill-family) must still resolve it."""
   -        # A later attempt for the same (issue, role-family) — different
   +        # A later attempt for the same (issue, skill-family) — different
   -        with no later successful attempt for that issue+role-family. Must
   +        with no later successful attempt for that issue+skill-family. Must
   ```
   Six `-role.../+skill...` pairs, no addition of "role" in any spelling.

2. **No new bug** — failing-test set vs `origin/main`, as sets of names.
   acceptance: `diff <(pytest test/ -q on origin/main | grep '^FAILED' | sed -E 's/ -.*$//' | sort) <(same on PR branch)` — result:
   ```
   (no output — identical 15-name failing sets)
   ```

3. **No overhead increase.**
   acceptance: full-suite wall time — result:
   ```
   origin/main:  31.79s collected, real 0m32.102s
   PR branch:    32.03s collected, real 0m32.341s
   ```
   derived: (32.341-32.102)/32.102 = 0.7% delta — within run-to-run noise
   for a 425+15+3-test suite; identical pass/fail/xfail counts both sides
   (no added/removed test collection).

4. **Monitor/watch machinery unbroken and not quieter.**
   canonical: `git diff --stat 2d53e0fe origin/issue-2803/technical-writing-style-guide-compliance-632a1d33` (quoted in full under "What was done") — only two new `docs/issue-2803/reports/` files and `test/test_spawn_attempt_staleness.py` changed; `watchdog.py`, `roster.py`, `lifecycle.py`, and all watch/monitor test files absent from that changed-file list.
   derived: full-suite pass count `425 passed, 3 xfailed` on both `origin/main` and the PR branch (quoted under "What was done" acceptance blocks above) — identical count means nothing went quieter.

## Upstream basis

- `b5dae50d948e2afa9a4a80c5b0d4f44afaf10da9` — PR #2808's head commit,
  checked out directly into a scratch `git worktree` for every check above
  (not read from the PR's diff text alone). canonical: `git rev-parse origin/issue-2803/technical-writing-style-guide-compliance-632a1d33` — result: `b5dae50d948e2afa9a4a80c5b0d4f44afaf10da9`.
- `2d53e0fe9cf25eb1643a296987d462dcee447100` (PR #2806, merged) — PR #2808's
  actual merge-base with `main`, used for all before/after diffing (see
  "What was done" for why diffing against current `origin/main` directly is
  misleading here).
- Issue #2803 — `gh issue view 2803` (executed this turn) — acceptance
  criteria and Non-goals, used to judge the `resolve_skill_family_source()`
  scope question above.
- `spawn.py:1399-1438`, `skills.py:463` — read directly this turn (quoted
  above; not taken from the PR record's characterization of them).

## What did not work

None — every check the task asked for was reproducible from scratch; no
dead end.

## Next steps

None — verification complete, `loop_state: landed`.

acceptance: `grep -inE '\brole\b' test/test_spawn_attempt_staleness.py` on the PR branch (same command as invariant 1 above, re-cited here as the closing basis) — result:
```
(no output, exit 1)
```
Combined with the identical-failing-set result under invariant 2 and the
diff-scope result under invariant 4 (both quoted above, this turn), the
delivered rename is inert and complete on its own stated terms. The two
findings recorded above (sweep-command misreport in Finding 1, overclaimed
canonical citation in Finding 2) do not block PR #2808's own closure of
#2803: neither makes the delivered six-site rename behaviorally incorrect
(per Finding 2's own conclusion), and the `resolve_skill_family_source()` /
`spawn.py`-docstring items both route to a separate `#2600`-identifier-slice
follow-up per issue #2803's own Non-goals (quoted under "Open finding
disposition" above), not to reopening #2803.
