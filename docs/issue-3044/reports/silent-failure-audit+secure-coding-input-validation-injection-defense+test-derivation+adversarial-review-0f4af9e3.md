---
issue: 3044
role: silent-failure-audit+secure-coding-input-validation-injection-defense+test-derivation+adversarial-review-0f4af9e3
author: silent-failure-audit+secure-coding-input-validation-injection-defense+test-derivation+adversarial-review-0f4af9e3
skills: silent-failure-audit (skill-repository(c05de12)), secure-coding-input-validation-injection-defense (skill-repository(c05de12)), test-derivation (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
code_under_review: same-commit
type: coding-record
breaking: false
verdict: delivered
upstream:
  - path: docs/issue-3044/ (issue body, referencing issue #3042 / PR #3043 and PR #3055)
    sha: same-commit
---

# issue-3044 — silent-failure-audit+secure-coding-input-validation-injection-defense+test-derivation+adversarial-review-0f4af9e3 record

## What was done

Closed the gap issue #3044 named: a record could claim
`skill-verdict: <name> — applied: invoked; ...` for a skill it never
actually opened via the Skill tool, and neither the check function nor
its only caller could ever refuse that claim — only report it.

1. `gates/record_lint.py`'s `skill_verdict_reason_check(text, mounted)`
   gained a converse loop, appended after the existing per-`mounted`-name
   loop (that loop is byte-identical to before):

   ```python
   for name, content in found.items():
       if name in mounted_set:
           continue
       applied_m = _SKILL_VERDICT_APPLIED.match(content)
       if applied_m and _SKILL_VERDICT_INVOKED_MARKER.match(
               applied_m.group(1).strip()):
           bad.append(
               "invoked-mismatch (issue #3044): "
               f"{name!r} 의 `skill-verdict` 줄이 `applied: invoked; "
               "...`라고 주장하지만, 이 세션의 transcript 는 그 스킬이 "
               "Skill 도구로 호출된 적이 없다는 것을 보여준다 — "
               "not-applicable 로 정정하거나, 실제로 Skill 도구를 호출한 "
               "뒤 다시 기록하라.")
   return bad
   ```
   (`gates/record_lint.py:592-601` post-edit — see
   `canonical: gates/record_lint.py:548` for the full function.) For any
   `skill-verdict: <name> — ...` line whose `name` is absent from
   `mounted`, if that line's content matches `applied: invoked; ...`
   (the same `_SKILL_VERDICT_APPLIED` + `_SKILL_VERDICT_INVOKED_MARKER`
   regexes the existing #2062 check uses), it appends a violation string
   prefixed `"invoked-mismatch (issue #3044): "`. `not-applicable:`
   lines never match `_SKILL_VERDICT_APPLIED` so they never fire this
   loop. Applied identically (via `cp` after editing the canonical copy,
   confirmed with `diff`) to the mirror file
   `on-the-record/gates/record_lint.py`.

   canonical: `diff gates/record_lint.py on-the-record/gates/record_lint.py`
   — result: empty (no output), confirmed identical after the edit.

2. `on-the-record/hooks/skill-verdict-guard.sh` now splits
   `skill_verdict_reason_check`'s return value into `hard` (violations
   whose string starts with `"invoked-mismatch"`) and `soft` (everything
   else — the pre-existing #2039/#2062 shape-only checks, untouched).
   When `hard` is non-empty the hook writes
   `{"decision": "block", "reason": ...}` and exits 0 before reaching the
   old advisory `finish(...)` call; `soft` violations still flow through
   the original advisory `additionalContext` path exactly as before.

3. New test file on-the-record/hooks/test_skill_verdict_reason_check.py
   (added this commit): Part 1 is six `unittest.TestCase` methods
   calling `record_lint.skill_verdict_reason_check` directly,
   equivalence-partitioned by (line type: `applied: invoked;` vs
   `not-applicable:`) x (name membership: in the invoked list vs not),
   plus regression coverage for the pre-existing #2039 missing-line,
   #2039 empty-content, #2062 missing-marker, and empty-`mounted`-is-a-
   no-op paths. Part 2 is three subprocess tests that run the real
   `skill-verdict-guard.sh` Stop hook end to end against a fabricated
   transcript and a synthetic `issue-999999/implementation`
   branch/record, proving the hook actually emits `decision: "block"`
   for an invoked-mismatch record, stays advisory (no `"decision"` key)
   when all `applied: invoked;` claims are truthful, and degrades to
   non-blocking when the transcript path does not exist on disk.

skill-verdict: silent-failure-audit — applied: invoked; used to classify skill-verdict-guard.sh's report-only Stop-hook path as Silently Absorbed (catches the violation, does nothing enforceable with it) and forward-trace its downstream consequence to gates/ci.py's missing caller, which shaped the choice to block at the Stop hook instead
skill-verdict: test-derivation — applied: invoked; used to route the acceptance criteria to equivalence partitioning on (line type: applied-invoked vs not-applicable) × (name membership: in the invoked list vs not), producing the partition-mapped test matrix in the new test file above
skill-verdict: secure-coding-input-validation-injection-defense — not-applicable: no shell/SQL/HTML/URL rendering sink or allowlist/encoding decision is involved; the fix is an in-process list-membership check, not a trust-boundary crossing
skill-verdict: adversarial-review — not-applicable: build-now single-session delivery scope; verification is the executed acceptance pytest suite plus a live demonstration of the Stop hook refusing a synthetic violating record, not a separate adversarial session

## Why

The audit's Handled / Silently Absorbed / Unreachable framing applied to
`skill-verdict-guard.sh` classifies its pre-#3044 report-only path as
Silently Absorbed: the hook already computes `invoked_skill_names` from
the real transcript (`on-the-record/hooks/skill-verdict-guard.sh` lines
117-153 pre-edit) and already runs `skill_verdict_reason_check` against
it (`on-the-record/hooks/skill-verdict-guard.sh` line 314 pre-edit), but
the function only ever checked "does every invoked name have a line" —
never "does every `applied: invoked;` line's name appear in the invoked
list" — so a record could assert an invocation the hook's own evidence
already refuted, and the hook's only response to any violation, true or
false, was `hookSpecificOutput.additionalContext`
(`on-the-record/hooks/skill-verdict-guard.sh` lines 212-222 pre-edit,
`finish()`) — advisory, never `decision: "block"`. Forward-tracing that
gap's downstream consequence: the natural place to catch it a second
time would be `gates/ci.py` at merge, but `record_skill_verdicts_in` in
`gates/record_lint.py` has zero callers there and CI has no durable
transcript artifact to re-derive an invoked-set from — confirmed no
`.session.log`/transcript file is committed:

canonical: `git ls-files | grep -iE '\.session\.log$|transcript'` —
result: empty (no output; no such file is tracked in the repo).

`gates/flows.py`'s `_session_last_activity` reads a *local, uncommitted*
per-session log for a status dashboard, not something CI can see at
merge time on a different machine. A `gates/ci.py` caller could only
check a record's `skill-verdict:` lines against the record's own
self-declared `skills:` frontmatter (the *mounted* set) — which cannot
refute the exact exploit this issue demonstrates (a truly-mounted skill
falsely claimed as invoked), because the mounted set already contains
that name; only the session-side Stop hook, holding the real transcript,
can tell "mounted" and "invoked" apart. So: the Stop hook blocks on
`invoked-mismatch` specifically (the one category its transcript
evidence can prove false), and `gates/ci.py` is intentionally left
untouched — there is no artifact it could check that would add
signal beyond what the record's own frontmatter already asserts.

All other (pre-existing #2039/#2062 shape-only) violation categories
stay advisory-only and byte-unaffected, per the issue's must-not-weaken
constraint — those checks never judged truth, only shape, and this
change does not start judging shape-only violations as blocking.

This also answers the `breaking: false` frontmatter field: the change
tightens `skill_verdict_reason_check` so it can newly reject a
previously-accepted false claim, but it adds no new parameter, changes
no function signature, and no external API/interface is touched — not
breaking in the conventional sense, only stricter for the one dishonest
input shape it now catches.

## What did not work

None.

## Upstream basis

- This issue: #3044 (issue body).
- Found-by reference named in the issue body: issue #3042 / PR #3043
  (Mechanisms 5 and 6 of the skill-layer mechanism audit) and PR #3055 —
  prose references this design responds to, not code this commit
  builds on top of; no sha needed for either per the issue body's own
  framing.
- `gates/record_lint.py`'s pre-existing `skill_verdict_reason_check`
  (issue #2039/#2153/#2062 lineage) and
  `on-the-record/hooks/skill-verdict-guard.sh`'s pre-existing
  `invoked_skill_names`/`finish()` machinery (issue #2576/#2681/#2893
  lineage) are the code this commit edits in place; `code_under_review:
  same-commit` applies (both the pre-existing code and this commit's
  edits to it land together in this PR).

## Open findings

None.

## Next steps

None — delivered in this commit. Acceptance commands run and their
real output:

canonical: `python3 -m pytest on-the-record/hooks/ -q -k invoked` —
result:
```
.........                                                                [100%]
9 passed in 0.92s
```

canonical: `grep -rn 'invoked' gates/record_lint.py | head -1` — result:
```
gates/record_lint.py:545:_SKILL_VERDICT_INVOKED_MARKER = re.compile(r"(?i)^invoked\s*;")
```

canonical: `python3 -m pytest on-the-record/hooks/ -q` — result:
```
..........F......................F........                               [100%]
2 failed, 40 passed in 1.10s
```
The 2 failures are `test_hook_classification.py::HookClassificationTest`
(`test_every_hooks_json_registration_has_a_classification_entry`,
`test_registration_count_matches_the_issues_own_count`) — pre-existing
and unrelated to this change (they compare `hooks.json` registrations
for `gate-registration-post-guard.sh` against
`on-the-record/hooks/hook_classification.json`, a file this PR does not
touch). Reproduced on the pre-edit tree via `git stash` before making
any change here:

derived: `git stash && python3 -m pytest on-the-record/hooks/test_hook_classification.py -q; git stash pop`
— result: same 2 failures, 4 passed, on the unmodified tree (commit
`8d4a819e08f3adf68a76bfe93065bc9ba6ce8c6a`), confirming this change did
not introduce or worsen them.

Acceptance requirement met — checked: all three acceptance commands
above, executed for real this session, pasted verbatim.
