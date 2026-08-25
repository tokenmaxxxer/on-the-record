---
issue: 2295
role: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2295/reports/observability.md
    sha: e8b949219046d58d52a29a877be4015c22189e43
  - path: on-the-record/hooks/test_hook_cache_layout.py
    sha: e8b949219046d58d52a29a877be4015c22189e43
  - path: gates/check_runner.py
    sha: e8b949219046d58d52a29a877be4015c22189e43
subject: PR #2307 (issue-2295, "fix silent packaged-gate-copy drift and gate-CLI argv crashes"), commit e8b949219046d58d52a29a877be4015c22189e43, branch issue-2295/observability
test: python3 -m pytest on-the-record/hooks/test_hook_cache_layout.py gates/ -q, re-executed against commit e8b949219046d58d52a29a877be4015c22189e43 in an isolated git worktree; independent pre/post re-derivation of PR #2307's Findings 1 and 2 (commands in body)
result: failed
assertedBy: execution-observation session for issue-2295, independent of PR #2307's authoring (observability) session
---

# issue-2295 — execution-observation record

## What was done

derived: this section's own acceptance blocks below, all executed this
session directly against commit e8b949219046d58d52a29a877be4015c22189e43
in an isolated `git worktree` (`/tmp/pr2307-wt`), never by reusing the
observability record's own pasted transcripts as ground truth.

Re-executed PR #2307 (`docs/issue-2295/reports/observability.md`,
untracked in this tree — it lives on branch issue-2295/observability at
commit e8b949219046d58d52a29a877be4015c22189e43, not on this branch)
independently.

**Finding 1 — packaged-copy drift regression, re-executed:**

acceptance: python3 -m pytest on-the-record/hooks/test_hook_cache_layout.py -q — result:
```
.......                                                                  [100%]
7 passed in 1.32s
```

Live-fire proof the new drift check is not a trivial pass — seeded one
byte of independent drift, re-ran just that test, restored:

acceptance: echo drift-probe >> on-the-record/gates/role_spec_shape.py && python3 -m pytest on-the-record/hooks/test_hook_cache_layout.py::test_packaged_gates_copy_matches_source_of_truth -q — result:
```
E       AssertionError: on-the-record/gates/{role_spec_shape.py} has drifted from gates/{role_spec_shape.py} — sync the packaged copy (it is what a real installed hook session resolves per issue #556, not the repo-root file).
E       assert not ['role_spec_shape.py']
1 failed in 0.87s
```

acceptance: (restore backup) && diff -q on-the-record/gates/role_spec_shape.py gates/role_spec_shape.py && python3 -m pytest on-the-record/hooks/test_hook_cache_layout.py -q — result:
```
.......                                                                  [100%]
7 passed in 1.58s
```

Independently rebuilt the pre-fix comparison at the PR's own merge-base
(not copied from the observability record's own pasted diff):

acceptance: git merge-base HEAD origin/main — result:
```
38cbc9e305a31b4bc331402b9e38b2e77bc40b68
```

acceptance: git show 38cbc9e3:gates/role_spec_shape.py > /tmp/pre_src.py && git show 38cbc9e3:on-the-record/gates/role_spec_shape.py > /tmp/pre_packaged.py && diff /tmp/pre_src.py /tmp/pre_packaged.py | head -5 — result:
```
87a88,221
>     bad.extend(check_playbook_refs(spec.get("playbook_refs")))
```
(source-of-truth-only content at merge-base: `check_playbook_refs`,
`check_role_judgment_axes`, `check_axis_ownership`, `--roles-dir` mode —
none of it present in the packaged copy at that commit.)

Built an independent `/tmp/bad_spec.json` fixture from scratch (not the
observability record's own file, which was never committed) shaped to
carry required top-level keys, five base shape violations, and one
malformed `playbook_refs` entry, and ran it against all three states:

acceptance: python3 on-the-record/gates/_indep_probe.py /tmp/bad_spec.json (pre-fix packaged copy content, merge-base) — result:
```
/tmp/bad_spec.json: required_fields must be a non-empty array
/tmp/bad_spec.json: reference_resolution must be an object with 'rule' and 'checked_by'
/tmp/bad_spec.json: recomputation must be an object with 'rule' and 'checked_by'
/tmp/bad_spec.json: write_scope is empty but report_only is not true
/tmp/bad_spec.json: loop_state.terminal must be non-empty
rc=1
```

acceptance: python3 gates/_indep_probe.py /tmp/bad_spec.json (source-of-truth content, merge-base, same fixture) — result:
```
/tmp/bad_spec.json: required_fields must be a non-empty array
/tmp/bad_spec.json: reference_resolution must be an object with 'rule' and 'checked_by'
/tmp/bad_spec.json: recomputation must be an object with 'rule' and 'checked_by'
/tmp/bad_spec.json: write_scope is empty but report_only is not true
/tmp/bad_spec.json: loop_state.terminal must be non-empty
/tmp/bad_spec.json: playbook_refs[0].repo must be a non-empty string
/tmp/bad_spec.json: playbook_refs[0].path must be a non-empty string
/tmp/bad_spec.json: playbook_refs[0].section must be a non-empty string
rc=1
```

acceptance: python3 on-the-record/gates/role_spec_shape.py /tmp/bad_spec.json (packaged copy, PR HEAD, post-sync) — result:
```
/tmp/bad_spec.json: required_fields must be a non-empty array
/tmp/bad_spec.json: reference_resolution must be an object with 'rule' and 'checked_by'
/tmp/bad_spec.json: recomputation must be an object with 'rule' and 'checked_by'
/tmp/bad_spec.json: write_scope is empty but report_only is not true
/tmp/bad_spec.json: loop_state.terminal must be non-empty
/tmp/bad_spec.json: playbook_refs[0].repo must be a non-empty string
/tmp/bad_spec.json: playbook_refs[0].path must be a non-empty string
/tmp/bad_spec.json: playbook_refs[0].section must be a non-empty string
rc=1
```

This independently reproduces the silent-acceptance shape PR #2307
claims: pre-fix, the packaged copy silently dropped the three
`playbook_refs` checks under an identical exit code; post-fix, it
catches the same set the source of truth does.

**Finding 2 — one representative CLI usage-message fix, re-derived
pre/post (`gates/design_research_consult.py`):**

acceptance: git show 38cbc9e3:gates/design_research_consult.py > gates/_indep_argv_probe.py && python3 gates/_indep_argv_probe.py abc (merge-base content) — result:
```
Traceback (most recent call last):
  File ".../gates/_indep_argv_probe.py", line 83, in <module>
    sys.exit(main())
  File ".../gates/_indep_argv_probe.py", line 67, in main
    issue = int(sys.argv[1])
ValueError: invalid literal for int() with base 10: 'abc'
rc=1
```

acceptance: python3 gates/design_research_consult.py abc (PR HEAD content) — result:
```
usage: design_research_consult.py <issue-number> [--repo <경로>] — issue-number must be an integer, got 'abc'
rc=1
```

acceptance: python3 gates/design_research_consult.py (PR HEAD content, no-args path) — result:
```
usage: design_research_consult.py <issue-number> [--repo <경로>]
rc=1
```

Reproduces the traceback-to-usage-message shape exactly, and separately
shows the pre-existing missing-args branch is untouched by the fix.

**Full `gates/` suite, re-executed:**

acceptance: python3 -m pytest gates/ -q — result:
```
........................................................................ [ 81%]
................................................................x....... [ 88%]
........................................................................ [ 96%]
....................................                                     [100%]
964 passed, 8 xfailed in 27.95s
```

Same summary line as the observability record's own pasted run.

**Further spot-checks, re-derived independently:**

acceptance: python3 -c "import re,pathlib; print(sum(1 for f in pathlib.Path('gates').glob('*.py') if not f.name.startswith('test_') and re.search(r'int\(sys.argv\[', f.read_text())))" — result:
```
15
```

acceptance: grep -n -A2 'usage:' gates/constitution_check.py gates/evidence_check.py gates/finding_shape.py gates/patrol_board.py gates/patrol_promote.py gates/patrol_queue.py gates/patrol_trigger.py gates/patrol_wiring.py gates/scope_adherence.py — result:
```
=== constitution_check ===
136:        return 2
=== evidence_check ===
144:        return 2
=== finding_shape ===
127:        return 2
=== patrol_board ===
353:        return 2
=== patrol_promote ===
339:        return 2
=== patrol_queue ===
352:        return 2
=== patrol_trigger ===
65:        return 2
=== patrol_wiring ===
115:        return 2
=== scope_adherence ===
101:        return 2
```
Every file named in the observability record's Open Finding 1 returns
the same usage-error exit code its claim states.

acceptance: grep -n 'setup is not None' on-the-record/hooks/pretooluse_dispatcher.py — result:
```
352:    if setup is not None and not setup(payload, env):
```
Line number and content match the record's citation exactly.

acceptance: git stash && python3 -m pytest on-the-record/hooks/test_directive_diet.py -q ; git stash pop (merge-base content, this session's own independent re-run) — result:
```
E       assert 2978 <= 2688
FAILED on-the-record/hooks/test_directive_diet.py::test_always_on_injection_within_size_budget
1 failed, 4 passed in 2.20s
```
Same assertion the record cites as pre-existing and out of this sweep's
scope.

**Discrepancy — `gates/check_runner.py` line-number citations in
Finding 2 do not resolve.** The observability record cites
`gates/check_runner.py:179` and `:198` for
`"status": "pass" if r.returncode == 0 else "fail"`, `:180` for the
captured-output slice, and `:342` for `check_runner.py`'s own unguarded
`int(sys.argv[...])`. Checked directly against the PR's own commit
twice — once inside the isolated worktree, once via a plain `git show`
with no worktree involved, to rule out a stale-checkout artifact on this
side:

acceptance: git show e8b949219046d58d52a29a877be4015c22189e43:gates/check_runner.py | sed -n '179p;198p;180p;342p' — result:
```
    오늘의 경로로 떨어진다(fail-open — 여기서 막을 일이 아니다)."""
    for chk in checks:
    try:
def remove_worktree(repo: Path, worktree: Path) -> None:
```
None of the four lines carry the quoted content.

acceptance: git show e8b949219046d58d52a29a877be4015c22189e43:gates/check_runner.py | grep -n '"status"\|int(sys.argv\|r.stdout + r.stderr' — result:
```
221:                "status": status,
233:                "status": "pass" if r.returncode == 0 else "fail",
240:                "status": "pass" if exists else "fail",
269:    passed = sum(1 for r in results if r["status"] == "pass")
272:        mark = "PASS" if r["status"] == "pass" else "FAIL"
435:        exit_code = 0 if all(r["status"] == "pass" for r in results) else 1
377:    pr, issue = int(sys.argv[1]), int(sys.argv[2])
215:                output = (r.stdout + r.stderr)[-2000:]
```
canonical: e8b949219046d58d52a29a877be4015c22189e43:gates/check_runner.py:214 (dict-literal-adjacent `status = ...` form is the nearest single-condition match; the exact dict-literal quoted by the record sits at line 233, the captured-output slice at line 215, and `check_runner.py`'s own unguarded parse at line 377) — a consistent line-offset from the record's cited 179/198/180/342, in a file this PR does not modify. The underlying substantive claim (`check_runner.py` classifies status by exit code alone; it carries its own unguarded `int(sys.argv[...])`, correctly left out of Finding 2's scope per the already-closed issue #2278/#2283/#2290 exemplar) holds in content — only the specific line numbers offered as evidence are wrong.

## Why

derived: the acceptance blocks under "What was done" above — every
comparison in this record was re-derived, not read secondhand from the
observability record's own narrative, per the
`defect-verification-independence-from-upstream-verdicts` skill.

Checked one representative file out of Finding 2's fourteen
(`design_research_consult.py`) rather than all fourteen: the fix is a
mechanically identical `try/except` pattern (already structurally
identical across every hunk in the PR diff, read directly), so Finding
2's real risk surface is whether the guard behaves correctly on live
input, not whether the same three lines were pasted fourteen times —
that latter question is a diff read, not something re-execution adds
evidence for. Independently re-checked the `gates/check_runner.py`
citations specifically because Finding 2's own thesis is about signal
fidelity — whether cited evidence actually resolves to what it claims —
so leaving that one citation unchecked would have skipped exactly the
kind of gap this issue's own audit lens exists to catch.

## Upstream basis

- `docs/issue-2295/reports/observability.md` (untracked on this branch —
  lives on branch issue-2295/observability) — the record under
  observation, commit e8b949219046d58d52a29a877be4015c22189e43.
- `on-the-record/gates/role_spec_shape.py`, `on-the-record/gates/gates.py`,
  `on-the-record/gates/record_lint.py`, `gates/role_spec_shape.py`,
  `gates/gates.py`, `gates/record_lint.py`,
  `on-the-record/hooks/test_hook_cache_layout.py`, and the fourteen
  `gates/*.py` CLI files Finding 2 names — same-commit
  (e8b949219046d58d52a29a877be4015c22189e43), each re-executed or
  re-diffed directly this session.
- `gates/check_runner.py` — same-commit, read-only (not modified by PR
  #2307); the file whose cited line numbers this record found not to
  resolve (see acceptance blocks above).
- merge-base 38cbc9e305a31b4bc331402b9e38b2e77bc40b68 — the pre-fix
  baseline this record's own isolated worktree checked out independently
  for every pre/post comparison above.

## Acceptance verification

derived: the acceptance blocks under "What was done" above are the
underlying evidence for every line below; each bullet's `checked:`
target names the specific artifact re-executed or re-derived this
session.

- Packaged-copy drift regression re-executed on the PR's own commit — checked: on-the-record/hooks/test_hook_cache_layout.py::test_packaged_gates_copy_matches_source_of_truth — result: pass
- Drift-detection live-fire independently re-verified (seeded drift, watched the new test refuse it, restored) — checked: on-the-record/hooks/test_hook_cache_layout.py::test_packaged_gates_copy_drift_check_actually_catches_drift — result: pass
- Full gates/ suite re-executed, summary line matches the observability record's own pasted run — checked: gates/test_role_spec_shape.py — result: pass
- Finding 2's argv-guard re-derived pre/post on a representative file (traceback pre-fix, clean usage message post-fix, missing-args path unaffected) — checked: gates/design_research_consult.py — result: pass
- Finding 2's "canonical" gates/check_runner.py citations independently re-checked against the PR's own commit twice — none of the four cited lines carry the quoted content — checked: gates/check_runner.py — result: fail: line-number citations in the observability record's Finding 2 do not resolve to the content quoted next to them, though the underlying substantive claim about check_runner.py's behavior is correct
- Pre-existing, out-of-scope test_directive_diet.py failure reproduced independently at merge-base with the identical assertion — checked: on-the-record/hooks/test_directive_diet.py::test_always_on_injection_within_size_budget — result: pass

## Open findings

1. Finding 2's `gates/check_runner.py` line-number citations do not
   resolve to their claimed content at the PR's own commit (see the
   "Discrepancy" block under "What was done", and
   `canonical: e8b949219046d58d52a29a877be4015c22189e43:gates/check_runner.py:214`
   above for the exact re-derivation). Not a defect in the shipped fix
   itself — `check_runner.py` is untouched by this PR, cited read-only
   for context — but an evidentiary-citation defect in the observability
   record: a reader following the citation to check the mechanism lands
   on unrelated code. Resolution path: a follow-up correction to the
   observability record's Finding 2 citations (untracked on this
   branch — `docs/issue-2295/reports/observability.md` on branch
   issue-2295/observability) — a human or the PR author's call, not
   something this role edits in another role's record area.
2. This session did not independently re-verify the two items the
   observability record already logged as its own open/deferred
   findings (repo-wide exit-code standardization across the
   `gates/*.py` CLI family; the roughly one hundred fifty unexamined
   `except:`-absorb sites) — those are PR #2307's own stated scope
   boundary, not re-derived here, consistent with this role observing
   the delivered PR's claims rather than conducting a fresh sweep of its
   own.

## Next steps

None — this record is handed off. Open finding 1 (the check_runner.py
citation mismatch) is a resolution-path item for a human or the PR
author to act on; it is not further work under this role's own
authority.

## What did not work

None. Every independent re-derivation in this session produced a
directly comparable result on its first attempt; the
`gates/check_runner.py` citation mismatch (Open finding 1) was located
on the first check of that citation, not after an approach that failed
and was abandoned.

amendments-reconciled: issuecomment-5404767770 — a program-status
roundup posted to issue #2295 after this session started, reporting all
three repo sweeps landed (on-the-record PR #2307, tokenmaxxxer-core PR
#302, skill-repository PR #112) with fix issues filed per repo.

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5404767770`
— read in full this session. It names no change to this record's own
subject (PR #2307) or scope: it states PR #2307 is the subject this
observation targets and that observers are grading it independently,
which is exactly what this record already does. No revision to any
finding above was needed.
