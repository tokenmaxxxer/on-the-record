---
issue: 2978
role: observability-signal-golden+test-derivation-5c7f5864
author: observability-signal-golden+test-derivation-5c7f5864
skills: observability-signal-golden (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: gates/spawn_on_pr.py, gates/closure_sweep.py, test/test_watchdog_heartbeat_noise.py, tests/test_watchdog_normal_state_not_violation_2978.py
    sha: f0d8c2eb8fdf2b685203ab39b9921708ae86bab7
---

# issue-2978 — observability-signal-golden+test-derivation-5c7f5864 record

## What was done

Fixed two watchdog checks that reported a correct, expected state as a
violation (build-now bypass, `CORE_BUILD_NOW=1`; delivered directly, no
phase-1 proposal round).

**1 — spawn-on-pr's "no PR yet" false positive
(`gates/spawn_on_pr.py::missing_verification()`).**

canonical: `gates/spawn_on_pr.py` at commit `f0d8c2eb`, lines 465-478:
```
        branch = subject_deliverable_branch(subject, pr_index)
        if branch is None:
            # issue #2978: `_slug` (from `subject_deliverable_record()`
            # above) is `None` when this subject's OWN deliverable record
            # has never landed to main -- meaning its deliverable PR has
            # never existed in the first place (this subject only reached
            # this loop because a *verification* record already landed
            # for it, e.g. reviewing a not-yet-opened deliverable). That
            # is the ordinary state of a freshly filed issue, not a
            # mapping failure -- nothing was ever lost from `pr_index`,
            # so there is nothing to report or one-shot-mark. Once a
            # deliverable record HAS landed (`_slug` is not `None`), its
            # PR necessarily existed and merged at some point -- an
            # unmappable branch past that point is a genuine anomaly
            if _slug is None:
                continue
```
`_slug` was already computed a few lines above (`_slug, subject_fm =
subject_deliverable_record(subject_board)`) for `subject_author`/
`verification_deficit`, but previously went unused past that assignment.
`_slug is None` means no unique non-verifying record exists in
`subject_board` — i.e. this subject's own deliverable has never landed.
When `_slug` is not `None`, the deliverable record HAS landed (its PR
necessarily existed and merged at some point), so the pre-existing
"찾지 못했다" print/one-shot-mark path (e.g. #2379's corrupted
merge-base case) still runs unchanged.

**2 — closure-sweep's "record after merge" false positive
(`gates/closure_sweep.py::find_violations()`).**

canonical: `gates/closure_sweep.py` at commit `f0d8c2eb`, lines 86-101
(`_pr_is_record_only`) and 460-484 (`find_violations`, call site):
```
def _pr_is_record_only(root: Path, pr: int) -> bool:
    ...
    paths = check_runner.pr_diff_paths(root, pr)
    return not check_runner.touches_implementation_paths(paths)
```
```
            kind = classify(issue_state, pr_state, pr_body, issue, False)
            if kind is None and pr_state == "MERGED" and issue_state == "OPEN":
                if ci._phase2_record_evidence(root, pr, branch, issue):
                    kind = classify(issue_state, pr_state, pr_body, issue, True)
            ...
            if kind and _pr_is_record_only(root, pr):
                kind = None
            if kind:
                violations.append(...)
```
Once `classify()` names a violation candidate — either
`OPEN_PR_ON_CLOSED_ISSUE` (a still-open PR referencing an issue GitHub
already auto-closed via an earlier delivery merge) or
`MERGED_DELIVERY_ISSUE_OPEN` (a merged PR whose issue is still open) —
the candidate is discarded if `_pr_is_record_only()` says the PR's diff
never leaves `docs/`. `_pr_is_record_only()` reuses issue #2974's own
structural signal verbatim
(`check_runner.touches_implementation_paths()` on
`check_runner.pr_diff_paths()`'s output) rather than a branch name or
issue age. The diff-fetch only runs once `kind` is already truthy —
same lazy-gh-call placement as the pre-existing
`ci._phase2_record_evidence()` call a few lines above it — so a healthy
tick with nothing to report costs zero extra `gh` calls.

Two pre-existing tests in `test/test_watchdog_heartbeat_noise.py`
(`TestSpawnOnPrUnmappableSubjectBranchSuppression`) used a bare `{}`
subject-board fixture to exercise the one-shot noise-suppression
marker. Under fix 1 an empty subject board is now exactly the suppressed
"no PR yet" case, so those fixtures were changed to a landed
(non-verifying) `_landed_deliverable_board()` fixture, which still
exercises the same suppression marker on the "genuinely missing branch"
path fix 1 leaves untouched.

acceptance: `python3 -m pytest test/test_watchdog_heartbeat_noise.py gates/test_spawn_on_pr.py -q` — result:
```
33 passed in 0.86s
```

Four new tests in `tests/test_watchdog_normal_state_not_violation_2978.py`
exercise `missing_verification()`/`find_violations()` directly against
the issue's four named acceptance checks.

acceptance: `python3 -m pytest tests/test_watchdog_normal_state_not_violation_2978.py -q` — result:
```
4 passed in 0.82s
```

acceptance: `python3 -m pytest tests/ -k spawn_on_pr_no_pr_yet -q` — result:
```
1 passed in 0.91s
```
acceptance: `python3 -m pytest tests/ -k spawn_on_pr_genuinely_missing_branch -q` — result:
```
1 passed in 0.86s
```
acceptance: `python3 -m pytest tests/ -k closure_sweep_record_after_merge -q` — result:
```
1 passed in 0.90s
```
acceptance: `python3 -m pytest tests/ -k closure_sweep_genuine_violation -q` — result:
```
1 passed in 0.89s
```

## Why

The issue's own must-not is explicit: neither check may be silenced
wholesale (a branch genuinely lost from `pr_index` and an issue
genuinely left open both still need reporting), and the distinction must
be structural — never issue age, a time window, or a hardcoded issue
number. Both fixes reuse a signal the codebase had already computed for
an unrelated reason, rather than adding a new age/window/cutoff check:

- Fix 1 reuses `subject_deliverable_record()`'s existing landed/not-landed
  distinction (already computed for `subject_author`/`verification_deficit`
  a few lines above — canonical: `gates/spawn_on_pr.py` line 428,
  `_slug, subject_fm = subject_deliverable_record(subject_board)`)
  instead of adding a new `gh` call or an issue-age check.
- Fix 2 reuses issue #2974's `touches_implementation_paths()` /
  `pr_diff_paths()` verbatim (canonical:
  `docs/issue-2974/reports/merge-gates+test-derivation-98d98713.md`,
  "C — record-only PR mis-scoring" section) — the same reusable
  principle #2974 already proved for `check_runner`/`merge_gate`'s
  record-only scoring: record-only status is decided by whether the diff
  touches implementation paths, not by a branch name. Applying the same
  primary signal here means closure-sweep and check-runner now agree on
  what "record-only" means, instead of each inventing its own heuristic.

`_pr_is_record_only()` deliberately does not consult
`frontmatter_record_only_signal()`'s `kind:` corroboration — canonical:
`gates/check_runner.py` lines 693-701 (`main()`) show
`record_only = not touches_impl` decided from the diff alone, with
`fm_signal`/`disagreement` used only for the posted comment's visibility,
never to override the diff verdict — mirroring that exactly avoids
inventing a second, divergent record-only definition inside the same
repo.

## Upstream basis

- `docs/issue-2974/reports/merge-gates+test-derivation-98d98713.md` —
  origin of the reused `touches_implementation_paths()`/`pr_diff_paths()`
  structural signal (`gates/check_runner.py`).
- `gates/spawn_on_pr.py::subject_deliverable_record()`,
  `subject_deliverable_branch()`, `missing_verification()` — existing
  code the fix reuses/extends, unchanged in signature.
- `gates/closure_sweep.py::classify()`, `find_violations()`,
  `gates/ci.py::_phase2_record_evidence()` — existing code the fix
  extends without changing `classify()`'s own signature/contract.

## Open findings

None.

## Next steps

None — loop_state: landed.

skill-verdict: observability-signal-golden — not-applicable: this issue
is about watchdog signal *correctness* (spawn-on-pr/closure-sweep false
positives), not about placing latency/traffic/errors/saturation panels on
a service-rollup dashboard aggregating multiple children — the skill's
actual trigger.
skill-verdict: test-derivation — applied: invoked; the four acceptance
checks are two 2-condition decision tables (subject's-own-deliverable-
landed x branch-found-in-pr_index for spawn-on-pr; PR-touches-
implementation x issue-already-closed/still-open for closure-sweep) — the
new tests in `tests/test_watchdog_normal_state_not_violation_2978.py`
cover the feasible cell each acceptance check names (the "no PR
yet"/"record after merge" empty-state cells and the "genuinely
missing"/"genuine violation" real-violation cells), plus the two
pre-existing-fixture updates in `test/test_watchdog_heartbeat_noise.py`
that keep the previously-tested "genuinely missing branch" cell covered
under the new discriminator. Medium-depth per this issue's own risk
profile (functional watchdog noise, not safety/regulatory/revenue-
impacting) — GWT-shaped test cases with named routing, no full
boundary-value/pairwise apparatus (neither axis is an ordered/numeric
range or a 3+-parameter combinatorial space).
