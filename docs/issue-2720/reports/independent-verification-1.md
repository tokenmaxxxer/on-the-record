---
issue: 2720
role: independent-verification-1
author: independent-verification-1
verifies_subject: true  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: consult.py (PR #2722 branch issue-2720/technical-writing-style-guide-compliance+conformance-review-requirement-extraction+adversarial-review-8361dea3)
    sha: c3e1afc77b4709942a87cf1281effb73fae82b3c
  - path: directive_assembly.py (same branch/commit)
    sha: c3e1afc77b4709942a87cf1281effb73fae82b3c
  - path: spawn.py (same branch/commit)
    sha: c3e1afc77b4709942a87cf1281effb73fae82b3c
  - path: gates/record_lint.py (same branch/commit)
    sha: c3e1afc77b4709942a87cf1281effb73fae82b3c
  - path: on-the-record/gates/record_lint.py (same branch/commit)
    sha: c3e1afc77b4709942a87cf1281effb73fae82b3c
---

# issue-2720 — independent-verification-1 record

## What was done

Build-now bypass (contract v3 s19a): `CORE_BUILD_NOW=1` was set in this
session's environment by the spawner — checked: `printenv | grep
CORE_BUILD_NOW` — result: `CORE_BUILD_NOW=1`. So this record delivers
directly, no phase-1 proposal round.

Independent verification of PR #2722
(`issue-2720/technical-writing-style-guide-compliance+conformance-review-requirement-extraction+adversarial-review-8361dea3`,
head `c3e1afc77b4709942a87cf1281effb73fae82b3c`, still OPEN — canonical:
`gh pr view 2722 --json headRefOid,state`), which claims to close issue
#2720 by finding and fixing runtime prompt strings in `.py` files that
`#2600`'s slice 3 (PR #2714, `.md`-glob only) missed. All checks below
were re-derived independently from a fresh git worktree at the PR's own
head commit, not taken from the subject's own record.

**Population derivation, re-run independently.** Copied the subject's
own AST+`tokenize` scanner script out of its record body into a
worktree cut from `origin/main` (`39890acf`, the PR's actual merge
base — canonical: `git merge-base origin/main pr-2722-check` ==
`39890acf`) and ran it there:
```
$ grep -vc docstring /tmp/iv2720/base_out2.txt   # pre-fix, base commit
300
$ grep -c docstring /tmp/iv2720/base_out2.txt
186
```
Then ran the identical scanner on the PR head worktree:
```
$ grep -vc docstring /tmp/iv2720/pr_out2.txt     # post-fix, PR head
285
$ grep -c docstring /tmp/iv2720/pr_out2.txt
186
```
derived: `300 - 285 = 15` (shell arithmetic), matching the PR's claimed
"15 lines fixed" exactly, and the unchanged `186 == 186` confirms no
docstring was touched (must-not 4c). The record's own reported "471
hits / 285 string-literal" is exactly reproduced this way (285+186=471).
(First attempt at this reproduction gave 301/286 pre/post because I had
copied the scanner script itself into the walked worktree, and the
scanner's own source contains the literal string `"역할"` inside its
`contains_vocab()` function — removing the copied script before
scanning reconciled to the subject's numbers exactly; noted so a future
auditor doesn't repeat the same off-by-one.)

derived: `diff <(grep -v docstring base_out2.txt|sort) <(grep -v
docstring pr_out2.txt|sort)` — the 15 removed lines are exactly
`consult.py:1032,1414,1449,1515,1677,1678,1682,1686`,
`directive_assembly.py:210,265,303,321`, `gates/record_lint.py:941`,
`on-the-record/gates/record_lint.py:941`, `spawn.py:3737` — matching the
PR diff's touched lines one-for-one (checked against `gh pr diff 2722`).

**Coupled-line disposition table spot-checked.** canonical: `git show
pr-2722-check:directive_assembly.py` read directly at lines 176 and 509
— confirms the record-path pattern `docs/issue-<n>/reports/<role>.md`
(:176) and the `role:` frontmatter-key template in `_RECORD_SKELETON`
(:509) are the literal placeholder tokens the record says they are;
deferring both to slice 4 (identifiers) and slice 5 (persisted keys)
rather than editing here is correct per the issue's own stated
must-not — editing the prose token alone here would describe a
naming/key pattern that does not exist yet. `gates/record_lint.py:1457`
(+ its `on-the-record/` twin) has the same path-pattern shape, same
correct deferral. `consult.py:1414`'s fix (`역할 '{role}' 의
관할(role jurisdiction)` → `스킬 '{role}' 의 관할(skill jurisdiction)`)
leaves the `{role}` interpolation itself untouched everywhere in the
diff — derived: `gh pr diff 2722 | grep -E '^\+.*\{role\}|^\+.*\{peer_role\}'`
shows every added line keeps the identical `{role}`/`{peer_role}`
interpolation token from the removed line, satisfying must-not 4b (no
identifier renamed).

**Kind-boundary claim (automatic model-prompt injection vs.
CLI/log/GitHub-comment text) spot-checked against files the record did
NOT edit**, to check for a genuine miss rather than trust the record's
own boundary: canonical: direct reads of `watchdog.py`, `events.py`,
`board.py`, `pipeline.py`, `relay.py`, `roster.py`,
`gates/spawn_on_pr.py`, `gates/acceptance_authoring_rule.py`, and
`gates/findings_due.py` at every one of the 270 remaining string-literal
hits' line numbers (`285 total − 15 fixed = 270` derived: `wc -l
pr_sl.txt` minus the 15-line diff above) — every sink found is
`print(...)`, `sys.exit(...)`, a `gh api issues/comments`/`gh pr create
--body` call, or a dict/frontmatter key literal (e.g. `roster.py`'s bare
`"role"` hits are dict keys, persisted-key kind, out of scope per the
issue's own Non-goals). None is `subprocess.run(cmd, input=<prompt>)` to
a model. canonical: `spawn.py:2416-2420` — `gates/findings_due.py`'s one
call site is explicitly commented `# print-only 모양` there, confirming
operator-facing, not model-facing. canonical: `grep -rln "import
acceptance_authoring_rule" --include=*.py --include=*.sh .` returned
empty — `gates/acceptance_authoring_rule.py` is not imported by any file
in the repo, is a standalone CLI tool invoked manually (output
`게이트 통과`/`게이트 차단`), also correctly out of scope.

`gates/record_lint.py`'s wiring claim (the record's justification for
including it despite the issue not naming it) checked directly:
canonical: `grep -n "import record_lint" on-the-record/hooks/record-claim-guard.sh`
→ line 90, inside one of the 21 `dict(script=...)` entries in
`on-the-record/hooks/pretooluse_dispatcher.py`'s `GATES` list — derived:
`grep -c 'dict(script=' on-the-record/hooks/pretooluse_dispatcher.py` =
21. The two other files the record's "not wired" claim covers
(`acceptance_authoring_rule.py`, `findings_due.py`) are named only in a
comment inside `contract-guard.sh` (canonical: `grep -n
"acceptance_authoring_rule\|findings_due\|closure_sweep"
on-the-record/hooks/contract-guard.sh` → line 7/14, both `#`-prefixed
comment lines, not an `import` statement), so the record's claim that
neither is reachable through a wired gate holds.

**Acceptance checks re-run independently, not re-pasted from the
record:**
```
$ python3 -m py_compile consult.py directive_assembly.py spawn.py \
    gates/record_lint.py on-the-record/gates/record_lint.py
(exit 0, no output)

$ python3 -m pytest -q test/
15 failed, 389 passed, 6 xfailed in 2.57s
```
acceptance: `python3 -m pytest -q test/` — result: failing-test names
and the failure reason (`fatal: 'origin' does not appear to be a git
repository` — sandboxed worktree with no real git remote) matched the
record's claim exactly, character for character on the summary line.
```
$ python3 spawn.py consult general-purpose "2+2는 얼마인가? 숫자만 답하라."
[consult] 배경에서 돈다 ... (backgrounded; result via consult-log)
$ tail runs/consult-logs/<...>.log
{
  "answer": "4",
  "confidence": "high",
  "caveats": []
}
```
acceptance: `python3 spawn.py consult general-purpose "..."` — result:
above JSON. This independently exercises the edited `base_prompt` in
`consult_cmd` (`consult.py:1032`) end to end and returns a well-formed
judgment — req 3's "consult call still returns a usable judgment"
reproduced live.
```
$ python3 -c "
import sys; sys.path.insert(0, 'gates')
import record_lint
bad = record_lint.canonical_source_claim_check('## Section\nThe session is running and the PR is merged, found here.\n')
print(bad[0] if bad else 'NO FINDING')
"
레코드에 canonical 소스 인용 없는 상태/결함 주장 (issue #793): '...' — skill output / ...
```
acceptance: above `python3 -c ...` command — result: confirms the edited
gate message still fires and now reads "skill output", not "role
output".

## Why

canonical: `gh issue view 2720` output (Acceptance section) — independent
verification exists to catch a plausible-but-wrong delivery before it
counts toward `#2600`'s slice-3 closure; canonical: `gh issue view 2626`
comments / `docs/issue-2626/reports/adversarial-review+silent-failure-audit-9ea418cf.md`
(cited in this issue's own body) record that slice 3 was already
declared complete once before (PR #2714) while missing an entire kind of
hit. So this session re-derived the population from the base commit
itself (not trusted the subject's pasted numbers), re-ran every
acceptance check from a clean worktree, and specifically hunted for
files the subject's record did NOT touch to check whether the kind
boundary it drew (automatic model injection vs. CLI-facing text)
actually holds, rather than only re-checking the lines it did touch.

## What did not work

None — the reproduction converged on the subject's exact numbers and
exact test-suite output on the first correctly-scoped attempt (after
excluding this session's own copied scanner script from the walked
tree, noted above as a self-caught methodology artifact, not a defect
in the subject's work).

## Upstream basis

See frontmatter `upstream:` — all five touched files cited at PR #2722's
head commit. canonical: `gh pr view 2722 --json headRefOid,state` (state
OPEN at verification time) and `gh pr view 2722 --json files` (five
code files: `consult.py`, `directive_assembly.py`, `spawn.py`,
`gates/record_lint.py`, `on-the-record/gates/record_lint.py`, plus the
subject's own record and deviation-log file).

## Open findings

- Acceptance req 3's second half ("a session spawned after the change
  reaches a PR") is not literally demonstrated by the subject — canonical:
  the subject's own record's "Demonstration (req 3)" section marks this
  `unverifiable:` with a stated reason (spawning a real session opens a
  branch/workspace/PR under the operator's GitHub account, an
  external-system side effect this single-issue vocabulary fix does not
  warrant triggering). This is a disclosed gap, not a false claim of
  completion, and matches the hook contract's `unverifiable: ... —
  reason` shape. Resolution path: none needed from this verification —
  PR #2722 itself (a session reaching a PR, carrying this exact edit) is
  a version of the demonstration, and a stronger literal
  re-demonstration would require the same external side effect this
  verification also declines to trigger, for the same reason.
- The subject's record leaves slice 4 (identifiers: `role`/`peer_role`
  Python variables, plus `directive_assembly.py:176,509` and
  `gates/record_lint.py:1457` + its `on-the-record/` twin) and slice 5
  (persisted keys — this session also observed many `"role"` dict-key
  literals in `roster.py`/`pipeline.py`/`board.py`/`events.py` during
  the kind-boundary spot-check above) explicitly open under `#2600`'s
  own Non-goals — not a defect in this PR, just noted so a future
  auditor does not re-raise it as new.

## Next steps

None for this verification. derived: this record's own "Population
derivation"/"Coupled-line disposition"/"Kind-boundary" sections above
(each carrying its own `canonical:`/`derived:` tags) show PR #2722
reproduces exactly: the population derivation matches the subject's
counts (`300 → 285`, 15 lines), the 15 fixed lines match the PR diff
one-for-one, docstrings are untouched (`186 == 186`), no `role`/
`peer_role` identifier is renamed, and the kind boundary the subject
drew holds against every file this session spot-checked that the
subject did not touch. All four executable acceptance checks
(`py_compile`, `pytest`, `spawn.py consult`, the `record_lint` gate
message) reproduce independently with output identical to the subject's
claims.

## Skill verdicts

skill-verdict: work-in-english — not-applicable: not invoked via the
Skill tool this session (guidance-only per the spawn prompt; this
record and all repository-bound work were already written in English by
default).
