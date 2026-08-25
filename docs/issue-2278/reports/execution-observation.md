---
issue: 2278
role: execution-observation
kind: verify-record
loop_state: cleared
upstream:
  - path: gates/check_runner.py
    sha: 41be748d4d6a7dd2cd0a10039b004a0cb84f06b8
subject: gates/check_runner.py at commit 41be748d4d6a7dd2cd0a10039b004a0cb84f06b8 (PR #2283, open, targets issue #2278)
test: >
  python3 gates/test_check_runner.py;
  python3 -m pytest gates/test_check_runner.py -q;
  python3 -m pytest gates/test_merge_gate.py gates/test_requirement_met.py -q;
  independent re-derivation of both live counterexamples (issue #2213/PR
  #2255's cross_family, issue #2208/PR #2218's work-in-english) against
  their real, live gh issue bodies, old-module-vs-new-module diff;
  independently constructed genuinely-missing path-shaped FAIL case
result: passed
assertedBy: independent re-execution, issue-2278/execution-observation session, 2026-08-25
---

# issue-2278 — execution-observation record

## What was done

Independent execution-observation of PR #2283 (`issue-2278: invert
check_runner classifier default to judgment for non-path backticks`,
open, head commit `41be748d`, targets issue #2278). This session wrote
no code change to `gates/check_runner.py` or its test suite — it checked
out PR #2283's head into an isolated `git worktree` at
`/tmp/pr2283-worktree` (`git worktree add /tmp/pr2283-worktree
origin/issue-2278/implementation`) and re-ran, from there, the exact
suites PR #2283's own record claims, plus the two named counterexamples
and the genuinely-missing-path FAIL case from issue #2278's own
Acceptance section, independently re-derived rather than re-pasted. PR
#2283's own record, `docs/issue-2278/reports/implementation.md` —
untracked on this branch (PR #2283 is still open, not merged; that path
exists only on `origin/issue-2278/implementation`, read via the worktree
checkout above) — lands at the same head commit, `41be748d`.

Check 1 — the gate's own runner:

```
$ python3 gates/test_check_runner.py
[... 21 ok lines ...]
ok - t_cross_family_bare_identifier_classifies_as_judgment_not_file_existence
ok - t_genuinely_missing_path_shaped_artifact_still_classifies_as_file_existence_and_fails
ok - t_work_in_english_skill_name_classifies_as_judgment_not_file_existence
21/21 passed
```
canonical: python3 gates/test_check_runner.py — result: PASS, 21/21, 0 SKIPPED.

Check 2 — full pytest suite for the same file:

```
$ python3 -m pytest gates/test_check_runner.py -q
............................                                             [100%]
28 passed in 30.17s
```
canonical: python3 -m pytest gates/test_check_runner.py -q — result: PASS, 28/28, 0 SKIPPED.

Check 3 — downstream consumers (`requirement_met.py` reuses
`parse_checks`; `merge_gate.py` reuses `run_checks`/`format_comment`):

```
$ python3 -m pytest gates/test_merge_gate.py gates/test_requirement_met.py -q
......................................................                   [100%]
54 passed in 44.50s
```
canonical: python3 -m pytest gates/test_merge_gate.py gates/test_requirement_met.py -q — result: PASS, 54/54, 0 SKIPPED.

Check 4 — independent re-derivation of both live counterexamples, from
scratch, against the issues' current real bodies (not PR #2283's own
record transcript). This session fetched both bodies live (`gh issue
view 2213 --json body -q .body`, `gh issue view 2208 --json body -q
.body`) and wrote its own comparison script, loading the pre-#2278
module via `git show HEAD^:gates/check_runner.py` into a throwaway
module (not PR #2283's own script, not committed) alongside the
worktree's post-change `check_runner`:

```
=== issue #2213 ===
  OLD=[file-existence] NEW=[judgment      ] per-spawn `cross_family` timing plus `cache_read_input_tokens` and con
=== issue #2208 ===
  OLD=[judgment      ] NEW=[judgment      ] the judge's historical abstention rate is reported as a number with th
  OLD=[test          ] NEW=[test          ] `tests/test_retrieval_eval.py` passes with negative clauses stripped f
  OLD=[file-existence] NEW=[judgment      ] `work-in-english` is bound statically for the roles that need it and n
```
canonical: throwaway comparison script, this session, against `gh issue
view 2213/2208 --json body -q .body` fetched live — result: PASS. Both
named counterexamples flip `file-existence` -> `judgment` under the new
classifier against the issues' real, current bodies; the two unrelated
lines in issue #2208's section (`judgment`, `test`) are unchanged by the
inversion, as expected since neither one is an unmatched backtick.

Check 5 — genuinely-missing path-shaped FAIL case, constructed
independently (own filename, not PR #2283's `missing_report.json`):

```
classification: [('file-existence', 'eo_2278_scratch_result.cfg')]
run result: fail
```
canonical: `check_runner.parse_checks("- check: results land in
\`eo_2278_scratch_result.cfg\`\n")` then `run_checks` against an empty
tempdir, this session — result: PASS. A bare (no `/`) backtick ending in
a known extension (`.cfg`) still classifies `file-existence` and still
genuinely FAILs when absent.

Observation (not a defect in this PR): while constructing check 5, a
first attempt used a slash-bearing filename
(`fixtures/eo_2278_check.yaml`) and got classified `test`, not
`file-existence` — traced to `parse_checks`'s pre-existing
`looks_like_command` branch (`"/" in tokens[0] and
tokens[0].count(".") >= 1`), which fires *before* the new
`_looks_like_path` branch is ever reached and is unmodified by this PR
(`gh pr diff 2283` shows no hunk touching that condition). In practice
`_looks_like_path`'s `"/" in token` arm mainly governs slash-bearing
tokens with no dot (e.g. a bare directory-shaped token); most real
slash+extension paths already route through the older command branch.
This does not affect PR #2283's correctness — the issue's genuine-FAIL
requirement is about a backtick that isn't a path being wrongly demoted,
and PR #2283's own regression test correctly used a bare (no `/`)
filename that does exercise the branch it actually changed.

## Why

Per this role's governing skill
(`defect-verification-independence-from-upstream-verdicts`), a review
requirement marked satisfied and a coding record's own pasted evidence
are claims pending independent re-derivation, not evidence in their own
right. Issue #2278 explicitly asked for two live counterexamples and one
genuinely-missing-path FAIL case to be re-verified after the change; the
invoking task named all three as required independent re-executions, not
re-reads of PR #2283's implementation record. Each is reproduced above
with its own freshly-written script and freshly-fetched issue bodies,
not the implementation record's transcript.

## Upstream basis

- `docs/issue-2278/reports/implementation.md` at sha `41be748d` (PR
  #2283, `origin/issue-2278/implementation` — untracked on this branch,
  see "What was done" above) — the acceptance-evidence claims this
  record's five checks were independently re-derived from and re-run
  against, not re-pasted from.
- `gates/check_runner.py`, `gates/test_check_runner.py` at the same
  commit — the actual artifacts re-verified by checks 1-3 above.
- Issue #2278's own body and Acceptance section (`gate:`, `provenance:`
  lines) — canonical: `gh issue view 2278`.
- Issue #2213 and issue #2208's own, live `## Acceptance` sections —
  canonical: `gh issue view 2213 --json body -q .body`, `gh issue view
  2208 --json body -q .body`, both fetched this session.

## Open findings

none — the observation under Check 5 above is a pre-existing,
unmodified control-flow fact about `parse_checks`'s branch ordering, not
a defect this PR introduced or a gap in its regression coverage of the
branch it actually changed.

## Next steps

None — loop_state is terminal (`cleared`, kind `verify-record`). PR
#2283 is still open (not yet merged); this record's five independent
re-executions match its implementation record's claims exactly, with no
divergence to hand back.
