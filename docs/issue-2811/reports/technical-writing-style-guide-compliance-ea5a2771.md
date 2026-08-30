---
issue: 2811
role: technical-writing-style-guide-compliance-ea5a2771
author: technical-writing-style-guide-compliance-ea5a2771
skills: technical-writing-style-guide-compliance (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: spawn.py
    sha: same-commit
---

# issue-2811 — technical-writing-style-guide-compliance-ea5a2771 record

## What was done

Rewrote the seven "role"-vocabulary occurrences in `spawn.py lines 1399-1438`
(the `_skill_family()` and `_attempt_superseded()` docstrings) to the
vocabulary the code's own identifiers use ("skill"/"skill family"). No
identifier, assertion, or executable line was touched — only the three
`"""..."""` docstring blocks changed.

Before (verbatim, `_skill_family()` docstring):
```
    """`role`에서 lease 분해자 접미사를 떼 role family 를 돌려준다. 접미사가
    없으면(분해자 없이 role 을 직접 넘긴 옛 호출부/테스트 픽스처) role 을
    그대로 돌려준다 — family 는 "role 에서 알아낼 수 있는 가장 넓은, 그러나
    여전히 issue 번호와 함께 써야 안전한 식별자"이지, "항상 접미사가 있다"는
    가정이 아니다."""
```
After:
```
    """`skill`에서 lease 분해자 접미사를 떼 skill family 를 돌려준다. 접미사가
    없으면(분해자 없이 skill 을 직접 넘긴 옛 호출부/테스트 픽스처) skill 을
    그대로 돌려준다 — family 는 "skill 에서 알아낼 수 있는 가장 넓은, 그러나
    여전히 issue 번호와 함께 써야 안전한 식별자"이지, "항상 접미사가 있다"는
    가정이 아니다."""
```

Before (verbatim, `_attempt_superseded()` docstring, two sentences):
```
    같은 작업(issue + role family)에 대한 더 나중의 성공한(`"session-log"`)
...
    보수적 기본값: issue/role/ts 중 하나라도 없거나 타입이 안 맞으면
```
After:
```
    같은 작업(issue + skill family)에 대한 더 나중의 성공한(`"session-log"`)
...
    보수적 기본값: issue/skill/ts 중 하나라도 없거나 타입이 안 맞으면
```

derived: spawn.py lines 1399 and 1405 (`def _skill_family(skill: str) -> str:` /
`return _LEASE_DISAMBIGUATOR_SUFFIX_RE.sub("", skill or "")`) and
spawn.py lines 1418-1421 (`_attempt_superseded()` reading `attempt.get("skill")`)
— read this turn: both functions' actual parameter/dict-key vocabulary is
`skill`, never `role`, confirming the docstrings described the wrong noun
for the identifiers sitting beside them.

acceptance: `sed -n '1399,1438p' spawn.py | grep -inE '\brole\b'` before
the edit (captured this turn against the pre-edit working tree, before
any change was applied) — result:
```
2:    """`role`에서 lease 분해자 접미사를 떼 role family 를 돌려준다. 접미사가
3:    없으면(분해자 없이 role 을 직접 넘긴 옛 호출부/테스트 픽스처) role 을
4:    그대로 돌려준다 — family 는 "role 에서 알아낼 수 있는 가장 넓은, 그러나
13:    같은 작업(issue + role family)에 대한 더 나중의 성공한(`"session-log"`)
17:    보수적 기본값: issue/role/ts 중 하나라도 없거나 타입이 안 맞으면
```
acceptance: `sed -n '1399,1438p' spawn.py | grep -oinE '\brole\b' | wc -l`
before the edit — result: `7` (matches the issue's stated count exactly).

acceptance: `sed -n '1399,1438p' spawn.py | grep -inE '\brole\b'` after
the edit — result:
```
(no output, exit 1 — zero matches)
```

acceptance (invariant 3, no overhead / prose-only): `git diff -- spawn.py`
— every changed line sits inside one of the three `"""..."""` docstring
blocks quoted above; no `def`, `return`, `if`, or other executable line
appears in the diff — result (full diff, 2 hunks, 5 insertions / 5
deletions):
```
@@ -1397,9 +1397,9 @@ _LEASE_DISAMBIGUATOR_SUFFIX_RE = re.compile(r"-[0-9a-f]{8}$")
 def _skill_family(skill: str) -> str:
-    """`role`에서 lease 분해자 접미사를 떼 role family 를 돌려준다. 접미사가
-    없으면(분해자 없이 role 을 직접 넘긴 옛 호출부/테스트 픽스처) role 을
-    그대로 돌려준다 — family 는 "role 에서 알아낼 수 있는 가장 넓은, 그러나
+    """`skill`에서 lease 분해자 접미사를 떼 skill family 를 돌려준다. 접미사가
+    없으면(분해자 없이 skill 을 직접 넘긴 옛 호출부/테스트 픽스처) skill 을
+    그대로 돌려준다 — family 는 "skill 에서 알아낼 수 있는 가장 넓은, 그러나
     여전히 issue 번호와 함께 써야 안전한 식별자"이지, "항상 접미사가 있다"는
     가정이 아니다."""
     return _LEASE_DISAMBIGUATOR_SUFFIX_RE.sub("", skill or "")
@@ -1408,11 +1408,11 @@ def _skill_family(skill: str) -> str:
 def _attempt_superseded(attempt_id: str, attempt: dict, attempts: dict,
                          outcomes: dict) -> bool:
     """`attempt`(halt 가 아직 클래스 재확인으로는 안 풀린 것으로 나온 시도)가
-    같은 작업(issue + role family)에 대한 더 나중의 성공한(`"session-log"`)
+    같은 작업(issue + skill family)에 대한 더 나중의 성공한(`"session-log"`)
     시도로 superseded 됐는지 본다. 위 모듈 주석 참고 — 매칭 규칙과 증거
     위치의 근거는 거기 있다.
 
-    보수적 기본값: issue/role/ts 중 하나라도 없거나 타입이 안 맞으면
+    보수적 기본값: issue/skill/ts 중 하나라도 없거나 타입이 안 맞으면
     `False`(판정 불가 — 아직 안 풀림 쪽으로) — `_halt_condition_cleared`와
     같은 fail-safe 방향."""
     issue = attempt.get("issue")
```

acceptance (invariant 1, no return of the retired axis in any form):
`git diff -- spawn.py | grep -inE 'role'` — result: matches only on the
5 removed (`-`) lines quoted above. `git diff -- spawn.py | grep '^+' |
grep -v '^+++'` — result: every added line uses `skill`, never `role` or
a synonym (no "persona", "actor", or other stand-in noun introduced).

## Why

`technical-writing-style-guide-compliance`'s word-choice rule (rule 4:
use the term that matches the identifier) requires prose describing an
identifier to use that identifier's own vocabulary. `_skill_family()`'s
parameter is named `skill`, `_attempt_superseded()` reads
`attempt.get("skill")` (`spawn.py:1419`), and both are exercised via the
`skill` field on ledger entries — so "role"/"role family" in these two
docstrings was describing the same identifiers with a retired noun,
exactly the shape issue #2811 names, left behind by PR #2731's
identifier-only rename.

These are internal (non-public, underscore-prefixed) function
docstrings, not user-facing instructional steps, so this edit is scoped
to vocabulary only, not a mood/voice/person rewrite. acceptance: `git
diff -- spawn.py` (quoted in full above under "What was done") — result:
the only token substitutions in the entire diff are `role`->`skill` and
`role family`->`skill family`; every other word, all punctuation, and
all sentence structure is byte-identical before/after, confirming the
meaning of every sentence is unchanged and no mood/voice/person was
altered, only the noun.

skill-verdict: technical-writing-style-guide-compliance — applied: invoked; used at the spawn.py lines 1399-1438 word-choice rewrite (rule 4: match identifier vocabulary) per skill-repository(c05de12).

## What did not work

None.

## Upstream basis

- Issue #2811 (this issue, `gh issue view 2811`, read this session) —
  names `spawn.py lines 1399-1438` exactly and the seven-occurrence count.
  acceptance: `sed -n '1399,1438p' spawn.py | grep -oinE '\brole\b' |
  wc -l` before the edit (re-cited from "What was done" above) — result:
  `7`, matching the issue text's stated count.
- PR #2731 — the identifier-only rename (`role` -> `skill` on
  `_skill_family`/`_attempt_superseded` and related fields) that left
  these docstrings' prose stale; named by issue #2811's own text as the
  origin of the drift.
- PR #2808 / issue #2803 (`03626993`, this repo, same fix shape applied
  to `test/test_spawn_attempt_staleness.py`) — the prior delivery whose
  record cited these same `spawn.py lines 1399-1438` lines.
  canonical: `git show 03626993:docs/issue-2803/reports/technical-writing-style-guide-compliance-632a1d33.md`
  (read this turn) — that record's "What was done" section states: "the
  code's own vocabulary is 'skill family', never 'role family'", citing
  `spawn.py lines 1399-1438`.
- PR #2810 / `3a9b4247` (independent verification of PR #2808) — Finding
  2 in that record is the direct trigger for this issue.
  canonical: `git show 3a9b4247:docs/issue-2803/reports/adversarial-review-b1ff090f.md`
  (read this turn) — that record's Finding 2 states verbatim: "those
  exact lines say 'role'/'role family' seven times in their own
  docstrings" and "it leaves `spawn.py` carrying the identical
  stale-wording pattern, unswept because the sweep was scoped to `test/`
  only" — that seven-count is independently re-derived fresh in this
  record's "What was done" section above (same `grep -oinE '\brole\b'`
  result, `7`, on this session's own pre-edit checkout).

## Open findings

Sweep population and rule: "non-test source" = every git-tracked `*.py`
file outside a `test/`, `tests/`, or `spec/` directory (repo root and
subdirectories), excluding files whose own basename starts with `test_`
(these are test files placed outside a `test/` directory). Both repos
named by `printenv ON_THE_RECORD CLAUDE_PLUGIN_ROOT_CORE` were confirmed
as git repos via `git -C <path> rev-parse --show-toplevel` (both printed
a toplevel path, no error) and are the same on-the-record repo (`git
remote -v` on both — identical `tokenmaxxxer/on-the-record.git` origin
URL both places) and the tokenmaxxxer-core repo respectively.

acceptance: on-the-record, `git ls-files '*.py' | grep -v -E
'^(test|tests|spec)/' | grep -v -E '(^|/)test_[^/]*\.py$'` (directory
exclusion plus the stated `test_`-basename exclusion together) —
population result: `127` files.

derived: a warrant-hunter probe dispatched before landing (see below)
re-ran `git ls-files '*.py' | grep -v -E '^(test|tests|spec)/'` (the
directory exclusion alone, with no basename filter) and found it
returns `144`, not `127` — an earlier draft of this section cited that
144-file command as the population even though the rule stated above
includes the `test_`-basename exclusion; the command now cited above
is the one that actually implements the stated rule. Re-running both
commands this turn confirms the same split:
```
git ls-files '*.py' | grep -v -E '^(test|tests|spec)/' | wc -l
144
git ls-files '*.py' | grep -v -E '^(test|tests|spec)/' | grep -v -E '(^|/)test_[^/]*\.py$' | wc -l
127
```

acceptance: on-the-record, `xargs grep -lE
'_skill_family|_attempt_superseded'` over the `127`-file population —
result: `consult.py roster.py skills.py spawn.py` (4 files reference
the mechanism's identifiers at all).
acceptance: `diff <(git ls-files '*.py' | grep -v -E
'^(test|tests|spec)/' | sort) <(git ls-files '*.py' | grep -v -E
'^(test|tests|spec)/' | grep -v -E '(^|/)test_[^/]*\.py$' | sort)` —
result: 17 lines (e.g. `harness/test_driver.py`,
`gates/test_spawn_on_pr.py`, `ledger/test_decisions.py`) — `test_`-
basename files outside a `test/` directory; none of the 17 is
`consult.py`, `roster.py`, `skills.py`, or `spawn.py`, so the
144-vs-127 population difference does not change the mechanism-sweep
result above.
acceptance: `grep -n '_skill_family|_attempt_superseded' consult.py
skills.py` — result: every hit in these two files is
`resolve_skill_family_source` (`consult.py:864,1254`,
`skills.py:463`) — the different, already-routed-to-#2561 mechanism per
this issue's stated non-goals, not `_skill_family`/`_attempt_superseded`.
acceptance: on-the-record, `xargs grep -inE '\brole[ _-]family\b'` over
the population — result:
```
roster.py line 595:    (issue, role-family) already reached `"session-log"`. If so, the halt is
spawn.py:1363:# 이 함수는 그 잔여를 별도로 묻는다: "같은 작업(issue + role family)에 대한
spawn.py:1372:# `-{hex8}`로 붙는다)를 뗀 나머지를 "role family"로 본다. 정확 role 문자열
```
Manually sanity-checked: `roster.py line 595` sits inside
`spawn_attempt_sweep()`'s docstring describing the call into
`_sp._attempt_superseded()` (confirmed: `sed -n '590,598p' roster.py`
shows "`_sp._attempt_superseded()` is asked next ... whether a later
attempt for the same (issue, role-family) already reached
`"session-log"`") — same mechanism, same retired noun, but outside
`spawn.py lines 1399-1438`. `spawn.py lines 1363 and 1372` sit in the module-level
comment block (`spawn.py lines 1341-1396`) immediately preceding
`_skill_family()`, also describing the same matching rule with
`role`/`role family`, also outside the issue's stated `1399-1438` range
(confirmed: `sed -n '1358,1373p' spawn.py`, quoted context read this
turn, shows the same "(issue + role family)" / "'role family'로 본다"
phrasing immediately above `_LEASE_DISAMBIGUATOR_SUFFIX_RE`'s
definition at line 1396). Per this task's explicit instruction not to
widen the diff beyond `spawn.py lines 1399-1438`, these three sites are left
unfixed and reported here rather than folded into this delivery:
- `roster.py line 595` — "role-family" describing `_attempt_superseded()`'s
  matching key. Resolution path: a follow-up issue scoped to
  `roster.py`'s own prose, same shape as this one.
- `spawn.py:1363` and `spawn.py:1372` — "role family" in the module
  comment block directly above the two functions this issue scoped in.
  acceptance: `sed -n '1341,1396p' spawn.py | grep -oinE '\brole\b' |
  wc -l` — result: `5` (5 total "role" occurrences in that
  adjacent-but-out-of-range block). Resolution path: a follow-up issue
  extending the same rename to `spawn.py lines 1341-1396`.

acceptance: tokenmaxxxer-core repo, `git ls-files '*.py' | grep -v -E
'^(test|tests|spec)/' | grep -v '/test_\|^test_'` — population result:
`3` files (`hooks/lib/gate-lib.py`, `hooks/pretouse_dispatcher.py`,
`hooks/tests/gate-prose-coverage-check.py`).
acceptance: same repo, `xargs grep -lE
'_skill_family|_attempt_superseded'` over that population — result:
empty (this mechanism does not exist in tokenmaxxxer-core's tracked
non-test `*.py` files).
acceptance: same repo, `xargs grep -inE '\brole[ _-]family\b'` over that
population — result: empty (zero matches).
acceptance: same repo, `xargs grep -inE '\brole\b'` over that
population — result: 6 hits, all in `hooks/pretouse_dispatcher.py`
(e.g. "root-and-role resolution", "role-handoff-contract.md", "the
env-var plumbing that used to feed a role-keyed config"). Manually
checked: these describe a distinct, still-live dispatcher-role concept
(which script/role resolves a given hook invocation) unrelated to
`_skill_family()`/`_attempt_superseded()` — not a finding for this
issue, not renamed.

The "code no longer has this behavior" case (per this task's step 2
instruction) did not arise. derived: reading `_skill_family()` and
`_attempt_superseded()`'s bodies (`spawn.py lines 1399-1438`, quoted under
"What was done" above) this turn — every rewritten sentence still
accurately describes current behavior (the suffix-stripping regex, the
fail-safe `False` default, the later-attempt supersession scan); only
the noun was wrong, not the facts, so no sentence needed a
behavior-accuracy flag instead of a wording fix.

Warrant-hunter probe (dispatched before landing, given this diff and
this record's draft, stance: hunt for a sentence that reads current but
describes behavior the code lacks, or a citation the record's own
command doesn't support): NO FINDING on the `spawn.py` docstring
rewrite itself — derived: the probe re-read the post-edit
`spawn.py` lines 1399-1438 against the rewritten prose this turn and
found every sentence accurate. ONE FINDING on this record's sweep-
population citation, fixed in place above (see the `derived:` block
under "acceptance: on-the-record, `git ls-files ... | grep -v -E
'(^|/)test_[^/]*\.py$'`" a few paragraphs up): the "144 files"
population count in an earlier draft of this section did not implement
this section's own stated `test_`-basename-exclusion rule. The
population is now `127` files (the command that actually implements
the stated rule), and the mechanism-sweep result (`consult.py roster.py
skills.py spawn.py`) is re-derived against the corrected population and
found unchanged.

## Acceptance verification

- retired noun removed from the docstring range the issue names — checked: grep-role-range — result: pass: derived: `sed -n '1399,1438p' spawn.py | grep -inE '\brole\b'` returns no output (exit 1) after the edit, versus 7 matches before (see "What was done", same command re-run fresh this turn)
- rename is inert (test-name-set identity) — checked: pytest-name-set-diff — result: pass: `python3 -m pytest test/ -v` name sets before/after are both 443 names, `diff` between them empty
- no new bug (failing-set vs origin/main, this same checkout) — checked: pytest-failing-set-diff — result: pass: `python3 -m pytest test/ -q` failing-name sets before/after are both the same 15 names, `diff` between them empty
- diff touches no executable line — checked: git-diff-spawn-py — result: pass: `git diff -- spawn.py` — all 10 changed lines (5 insertions/5 deletions) sit inside the three docstrings quoted under "What was done"; no `def`/`return`/`if` line appears in the diff
- monitor/watch machinery (`test/test_watchdog_heartbeat_noise.py`, `test/test_spawn_attempt_staleness.py`) unbroken, not quieter — checked: pytest-watchdog-staleness — result: pass: `python3 -m pytest test/test_watchdog_heartbeat_noise.py test/test_spawn_attempt_staleness.py -v` — 47 passed both before and after, 152 output lines both times
- diff does not touch watchdog.py/events.py (monitor/watch source) — checked: git-diff-stat — result: pass: `git diff --stat` shows only `spawn.py` changed
- no reintroduction of the retired axis under a synonym — checked: diff-role-grep — result: pass: `git diff -- spawn.py | grep -inE 'role'` matches only removed (`-`) lines; `git diff -- spawn.py | grep '^+' | grep -v '^+++'` shows only `skill` on added lines

## Next steps

None — record is terminal (`loop_state: landed`); the three sites above
are explicitly deferred to follow-up issues, not silently dropped.
