---
issue: 3059
role: independent-verification-1
author: independent-verification-1
verifies_subject: true  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-3059/reports/silent-failure-audit+technical-writing-structure-comprehension+test-derivation+adversarial-review-95e5c316.md
    sha: f77f02f7c442b8f02790d25b60bae15adbe6c0a9
---

# issue-3059 — independent-verification-1 record

## What was done

Independently audited PR #3069 (`tokenmaxxxer/on-the-record`, branch
`issue-3059/silent-failure-audit+technical-writing-structure-comprehension+test-derivation+adversarial-review-95e5c316`,
"distinguish unmapped-interpreter checks from genuine judgment
criteria") — the only open PR against issue #3059, tip commit
`f77f02f7`. Re-derived every claim in the subject's own record by
re-executing the same commands myself against a `git worktree` checkout
of the PR's tip commit, rather than trusting the record's transcript.

canonical: `gh pr view 3069` — the subject record lives at
`f77f02f7:docs/issue-3059/reports/silent-failure-audit+technical-writing-structure-comprehension+test-derivation+adversarial-review-95e5c316.md`
(untracked in this branch's own working tree — this branch
`issue-3059/independent-verification-1` was cut from `8d4a819e`, before
`f77f02f7` landed on `issue-3059/implementation` — read via
`git show f77f02f7:<path>`) — derived:
`git show f77f02f7:docs/issue-3059/reports/silent-failure-audit+technical-writing-structure-comprehension+test-derivation+adversarial-review-95e5c316.md | head -1`
```
---
```

**Re-run against a `git worktree` of PR tip `f77f02f7`:**

Acceptance criterion 1 (unmapped-token check reports a distinct reason;
genuine prose unchanged) —
derived: `cd /tmp/verify-3059 && python3 -c "import sys; sys.path.insert(0,'gates'); import check_runner as cr; print(cr.parse_checks(open('/dev/stdin').read()))" <<< '## Acceptance\n- x\n  - check: \`grep -n foo bar.md\`'`
```
[{'type': 'judgment', 'raw': '`grep -n foo bar.md`', 'reason': 'unmapped-interpreter', 'command': 'grep -n foo bar.md', 'tool': 'grep'}]
```
matches the record's claimed result byte-for-byte. Empty-state re-check
— derived: `python3 -c "import sys; sys.path.insert(0,'gates'); import check_runner as cr; print(cr.parse_checks('## Acceptance\n- check: document \`grep -n foo bar.md\`\n'))"`
```
[{'type': 'judgment', 'raw': 'document `grep -n foo bar.md`'}]
```
— a stating-verb-prefixed bullet (issue #2509's shape) still carries no
`reason`, confirming the new branch does not swallow the pre-existing
judgment path.

Acceptance criterion 2 (message names the sanctioned `bash -c` form) —
the issue's own check names an external `study-companion` repo not
present in this session; the subject record discloses this
(`unverifiable:` tag, substituting the equivalent in-repo mechanism). I
independently confirm the substitution is equivalent by tracing the same
code path directly: `gates/check_runner.py`'s `_judgment_line()` (at the
worktree tip) emits `bash -c {shlex.quote(item['command'])}` plus a
sentence naming the missing token — the same string shape the issue's
`grep -i -e 'bash -c' -e interpreter` check would match against
`check_runner.py`'s own PR-comment output — derived:
`cd /tmp/verify-3059 && python3 -c "
import sys; sys.path.insert(0,'gates')
import check_runner as cr
print(cr.format_no_checks_comment([{'type':'judgment','raw':'\`grep -n foo bar.md\`','reason':'unmapped-interpreter','command':'grep -n foo bar.md','tool':'grep'}]))"`
```
no checks declared

이 이슈의 `## Acceptance` 절에 있는 1개 `check:`/`gate:` 항목이 실행되지 않았다 — 판단이 필요한(judgment) 기준이라서가 아니라, 첫 토큰이 인터프리터 허용목록에 없어서다. 이것은 통과가 아니라 별개의 결과다 — 머지 게이트는 이걸 만족으로 취급하면 안 된다:
- `grep -n foo bar.md` — 첫 토큰 `grep`이 인터프리터 허용목록(python3, python, bash, sh, pytest, node, npx, deno, bun)에 없어 명령으로 실행되지 않았다(판단이 필요한 기준이라서가 아니다). 허용된 형태로 감싸 실행하라: `bash -c 'grep -n foo bar.md'`
```
— the rendered comment contains both `bash -c` and `interpreter`-adjacent
text (허용목록/인터프리터), satisfying the issue's grep-based check in
substance.

Acceptance criterion 3 (allowlist + convention documented) —
derived: `cd /tmp/verify-3059 && grep -rn 'INTERPRETERS\|bash -c' on-the-record/directive/acceptance-format.md`
```
on-the-record/directive/acceptance-format.md:119:  `INTERPRETERS` list — `bash`, `bun`, `deno`, `node`, `npx`, `pytest`,
on-the-record/directive/acceptance-format.md:125:  `check: \`bash -c "grep -n foo bar.md"\`` runs; `check: \`grep -n foo
```
2 matches, matching the record's claim.

Must-not 1 (do not widen `INTERPRETERS`) — canonical: `gh pr diff 3069`
shows `INTERPRETERS = ("python3", "python", "bash", "sh", "pytest",
"node", "npx", "deno", "bun")` with no hunk touching that assignment;
the only new module-level name is `_COMMON_NON_INTERPRETER_TOOLS`, a
disjoint `frozenset`, consulted only inside the already-`judgment`
branch of `parse_checks()` — derived:
`cd /tmp/verify-3059 && python3 -m pytest gates/test_check_runner.py -k test_interpreters_allowlist_is_not_widened -q`
```
1 passed
```

Must-not 2 (do not auto-wrap in `bash -c`) — canonical:
`gates/check_runner.py`'s `run_checks()` (read at the worktree tip)
dispatches only on `kind in ("test", "grep", "file-existence",
"artifact-smoke")`; every other `kind`, including `judgment` with a
`reason`, falls to `else: raise JudgmentCheckError(...)` — the new
`reason`/`command`/`tool` fields are read only by the comment-rendering
functions, never by `run_checks()` — derived:
`cd /tmp/verify-3059 && python3 -m pytest gates/test_check_runner.py -k test_unmapped_interpreter_never_executes_even_if_fed_to_run_checks -q`
```
1 passed
```

Full test suite — derived: `cd /tmp/verify-3059 && python3 -m pytest gates/ -q`
```
57 passed in 0.87s
```
matches the record's claim of "57 passed, 0 failed". Narrower run —
derived: `cd /tmp/verify-3059 && python3 -m pytest gates/test_check_runner.py -q`
```
22 passed in 0.82s
```
matches the record's claim of "22 passed (11 pre-existing, 11 new)".

`shlex.quote` fix (the adversarial-review finding the subject record
says it fixed) — derived: `bash -c 'grep -n "foo bar" /etc/hostname'; echo $?` vs. `grep -n "foo bar" /etc/hostname; echo $?`
```
1
1
```
both forms exit identically (no match, same reason) on a
quote-containing pattern — the `shlex.quote`-wrapped form does not
corrupt the quoting, which is what the record's fix claims.

`code_under_review` sha citation — derived: `git rev-parse da8b3b0e`
```
da8b3b0e53cc1f3287e131edc32e1a2112df0cc1
```
matches the subject record's `code_under_review:` frontmatter exactly.

Citation accuracy in the subject record's Open findings (misattribution
fix, #2073 vs #2509) — derived: `git show 80c2dfe9 -- gates/check_runner.py | grep -n INTERPRETERS`
```
+INTERPRETERS = ("python3", "python", "bash", "sh", "pytest",
+                or tokens[0] in INTERPRETERS
```
confirms issue #2073 (PR #2091, commit `80c2dfe9`) introduced
`INTERPRETERS` — derived: `git log --oneline --all -- gates/check_runner.py | grep -i 2509`
```
dfd87617 issue-2509: fix check_runner false FAIL on foreign-owned paths and stating-verb bullets (#2513)
```
confirms #2509/PR #2513 hardened the same classifier (foreign-owned
paths, stating-verb prose) without touching `INTERPRETERS` — the
record's corrected citation (crediting #2073 for the allowlist, #2509
for a separate hardening) is accurate.

other mounted skills: not triggered.

## Why

Verify-at-landing (contract §1): a deliverable is work plus executed
acceptance evidence, and an independent verification exists to catch a
gap between what a record *claims* it ran and what actually happens
when the same commands are re-run by someone else, against the actual
committed code rather than the record's transcript. I re-executed every
numbered acceptance criterion and both must-nots against a fresh
`git worktree` of the PR's tip commit rather than reading the record's
prose as sufficient, and separately traced the two citation claims
(the shlex-quote fix's correctness, the #2073/#2509 attribution) back
to the actual git history rather than trusting the record's own
Open-findings disposition.

## What did not work

None.

## Upstream basis

- canonical: `gh pr view 3069` and `gh pr diff 3069` (PR #3069, tip
  `f77f02f7`) — supplies the change under review.
- upstream record: `docs/issue-3059/reports/silent-failure-audit+technical-writing-structure-comprehension+test-derivation+adversarial-review-95e5c316.md`
  at sha `f77f02f7c442b8f02790d25b60bae15adbe6c0a9` (untracked in this
  branch's own working tree, cut from `8d4a819e` before `f77f02f7`
  landed — read via `git show f77f02f7:<path>`, confirmed present per
  the derived check under "What was done" above).
- All re-derivations above ran against `git worktree add /tmp/verify-3059 f77f02f7`, removed after verification — derived: `git worktree remove /tmp/verify-3059 --force && git worktree list`
```
/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-3059-independent-verification-1  f77f02f7 [issue-3059/independent-verification-1]
```
(worktree entry for `/tmp/verify-3059` no longer listed).

## Open findings

None — all 3 Acceptance criteria and both must-nots hold under
independent re-execution above; the subject record's own Open findings
(quote-escaping bug, doc wording, misattribution, weak initial test
coverage) were each disclosed and each independently re-confirmed as
fixed in the tip commit (see the `shlex.quote` and #2073/#2509 citation
checks above). The two items the subject record left out-of-scope
(tools outside the curated 6; `main()`'s empty-state-before-record-only
ordering) match the issue's own must-not (no general command allowlist)
and its 3 Acceptance criteria (documentation of the consequence, not a
reordering) respectively — correctly scoped out, not silently dropped
requirements.

## Next steps

None — verification complete, `loop_state: landed`. Final re-check
(fresh worktree, run immediately before writing this record) — derived:
`git worktree add /tmp/verify-3059-final f77f02f7 && cd /tmp/verify-3059-final && python3 -m pytest gates/ -q`
```
57 passed in 0.93s
```
