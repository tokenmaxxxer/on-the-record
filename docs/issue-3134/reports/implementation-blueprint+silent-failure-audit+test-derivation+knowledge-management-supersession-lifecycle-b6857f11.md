---
issue: 3134
role: implementation-blueprint+silent-failure-audit+test-derivation+knowledge-management-supersession-lifecycle-b6857f11
author: implementation-blueprint+silent-failure-audit+test-derivation+knowledge-management-supersession-lifecycle-b6857f11
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12)), knowledge-management-supersession-lifecycle (skill-repository(c05de12))
verifies_subject: false
code_under_review: 43b689f32fbc623281b6e803e18a5ad46544a39e (main tip at session start; PR #3143/#3156's amends: primitive already merged)
type: repair-round-delivery
breaking: false
verdict: All four reopen findings fixed and independently re-verified live. Finding 1 (commit-time gate denies the correcting session's own commit) and finding 2 (one unresolved edge anywhere blocks every unrelated commit) fixed together by splitting check() into check_staged() (commit-time, diff-scoped, structural-only) and check_landing() (merge-time, post-apply). Finding 3 (nothing calls write_backlinks() automatically) fixed by gates/amends_landing.py::land() plus a new PostToolUse hook, amends-landing-apply.sh, that calls it on a successful gh pr merge. Finding 4 (check() reports the index missing right after --update wrote it) fixed by anchoring the CLI's repo default to the checkout root instead of the invoking process's cwd. All 4 literal acceptance checks pass; a new end-to-end test drives the real preflight hook and the real land() function against a local bare-repo remote and confirms the backlink lands with no human step.
loop_state: done
upstream:
  - path: issue #3134 reopen comment (2026-09-02, "Reopened — the wiring blocks correcting sessions and the remedy cannot satisfy its own check"), read via `gh issue view 3134 --comments`
    sha: 43b689f32fbc623281b6e803e18a5ad46544a39e
  - path: docs/issue-3134/reports/adversarial-review+knowledge-management-supersession-lifecycle+silent-failure-audit-48484397.md (PR #3160), the independent verification whose live reproduction (findings 1-3) the reopen comment cites
    sha: 43b689f32fbc623281b6e803e18a5ad46544a39e
---

# issue-3134 — implementation-blueprint+silent-failure-audit+test-derivation+knowledge-management-supersession-lifecycle-b6857f11 record

## What was done

canonical: `gh issue view 3134 --comments` (read this session, full reopen
comment text) and `gh pr diff 3160` (read this session, PR #3160's full
record, 505 lines). Repair round 3 on the `amends:` primitive (issue
#3134). PR #3143/#3156 landed the primitive and its round-2 repair on
`main` (merge commit `92b6ec9b`), then PR #3160's independent
verification reproduced three defects live against that merged tree and
the issue reopener found a fourth while attempting to mitigate. This
round fixes all four together, on a fresh branch from `main` (no open PR
existed for this round).

**Finding 4 (fixed first, per the spawning task's own instruction, since
it could block this session's own record commit).** derived: `python3
gates/amends_index.py --update && python3 gates/amends_index.py`, run
from `gates/` rather than the checkout root -- result: `gate blocked:
docs/specs/amends-index.md missing`, reproducing the reopener's exact
complaint (the CLI's no-arg `repo` default was `Path(".").resolve()`,
the invoking process's cwd, not this checkout's own root -- `--update`
and `check` silently agreed only when run from the exact same
directory). `gates/amends_index.py`'s `main()` now defaults to
`_REPO_ROOT` (`Path(__file__).resolve().parent.parent`, already computed
for the `amends`/`amends_backlink` sys.path insert) instead of cwd; an
explicit positional arg still overrides it. Also fixed the stale
docstring at `render_index()` -- it said the index path without its
`specs/` segment (never a real path in this tree; `INDEX_PATH` at line 36
already had the correct one). New test class,
`tests/test_amends_index_wiring.py`'s `CliRepoRootResolutionTest`: runs
`--update` then a bare `check` via subprocess, both from a scratch repo's
root and from one level down (`gates/`), asserting both agree. derived:
`python3 -m pytest tests/test_amends_index_wiring.py -q` -- result: 10
passed (was 3 before this round).

**Findings 1+2 (fixed together -- they share one cause: `check()` blocked
a commit on a landing-step-only property, over the whole tree).** derived:
built a scratch git repo with a fresh target+corrector pair (`amends:`
field, target untouched, no backlink possible yet -- exactly the shape a
correcting session's own first commit produces) and ran the REAL
`amends-index-preflight.sh` with a simulated realistic `PreToolUse`
payload -- result before the fix: `HOOK EXIT CODE: 2` (deny), reproducing
PR #3160's finding 1 live. Root cause: the hook called
`amends_index.check()` -- full, unscoped, blocking on `missing_backlinks`
(a property that can never be true pre-landing) and on index staleness
anywhere in the tree (finding 2: one unrelated session's already-landed,
still-unresolved edge would deny every future report-touching commit,
repo-wide). Fix: `gates/amends_index.py` gained `check_staged(repo,
staged)` -- scoped to the commit's own staged paths, blocking ONLY on a
genuinely malformed edge (dangling target, missing section, conflict,
cycle) those paths participate in, never on a missing backlink or a stale
index -- and `check_landing(repo, staged)`, the merge-time counterpart
(see finding 3). `amends-index-preflight.sh` now calls `check_staged()`.
Re-ran the same live reproduction after the fix: derived: `bash
amends-index-preflight.sh` with the same payload -- result: exit 0
(allowed). Separately reproduced finding 2 live: a pre-existing broken
edge committed first, then an unrelated report file staged and run
through the real hook -- result: exit 0 (never blocked).

New unit tests, both in `tests/test_amends_index_wiring.py`: derived:
`python3 -m pytest tests/test_amends_index_wiring.py -q` -- result: 10
passed, full list below (`CheckStagedScopingTest` covers a correcting
session's own unlinked commit being allowed, an unrelated commit never
blocked by a foreign broken edge, and a commit that itself introduces a
broken edge still being denied; `CheckLandingTest` covers a still-missing
backlink denying at landing and passing once the apply step has run):
```
tests/test_amends_index_wiring.py::RealTreeSelfConsistencyTest::test_check_passes_against_the_actual_committed_tree PASSED
tests/test_amends_index_wiring.py::RealTreeUnlinkedAmendmentTest::test_check_fails_closed_on_an_unlinked_amendment_in_a_real_copy PASSED
tests/test_amends_index_wiring.py::RealTreeUnlinkedAmendmentTest::test_check_passes_once_both_the_index_and_the_backlink_are_landed PASSED
tests/test_amends_index_wiring.py::CheckStagedScopingTest::test_correcting_sessions_own_unlinked_commit_is_not_denied PASSED
tests/test_amends_index_wiring.py::CheckStagedScopingTest::test_unrelated_session_commit_never_blocked_by_a_foreign_unresolved_edge PASSED
tests/test_amends_index_wiring.py::CheckStagedScopingTest::test_a_commit_introducing_a_dangling_target_is_still_denied PASSED
tests/test_amends_index_wiring.py::CheckLandingTest::test_still_missing_backlink_denies_at_landing PASSED
tests/test_amends_index_wiring.py::CheckLandingTest::test_passes_once_the_apply_step_has_run PASSED
tests/test_amends_index_wiring.py::CliRepoRootResolutionTest::test_update_then_check_agree_from_the_scratch_repo_root PASSED
tests/test_amends_index_wiring.py::CliRepoRootResolutionTest::test_check_still_agrees_when_invoked_from_a_subdirectory PASSED
```

**Finding 3 (nothing calls `write_backlinks()`/`--apply-backlinks`
automatically).** derived: `grep -rln "apply-backlinks\|amends_index"
--include="*.yml" .` and `grep -n "amends" on-the-record/hooks/
merge-allow-gate.sh` -- result: no `.github/workflows` directory, no
caller anywhere, confirming PR #3160's own finding. Built
`gates/amends_landing.py::land(remote, branch, workdir=None)`: clones
`remote`@`branch` into a disposable directory (never the orchestrator's
own live checkout -- a concurrently-running session or human may be using
it), runs `write_backlinks()`+`update()` there, and pushes the result
back if anything changed. New `on-the-record/hooks/amends-landing-apply.sh`
(`PostToolUse`+`Bash`) calls it automatically on a successful
`gh pr merge` -- command-shape validation, `tool_response`
success-detection heuristic, and orchestrator-only identity check all
ported from `post-landing-obligation-gate.sh`'s own established
precedent rather than reimplemented. Registered in `hooks.json`'s `Bash`
matcher group (derived: `python3 -c "import json; json.load(open('on-the-record/hooks/hooks.json'))"`
-- result: valid JSON, no exception) and in both
`docs/specs/enforcement-boundary.md` and `docs/specs/generated-paths.md`
(classification `n/a` -- the hook shells out to `gates/amends_landing.py`
for the actual write, same shape as `post-landing-obligation-gate.sh`'s
own row; derived: ran `gate-registration-guard.sh`'s own
`_WRITE_CALL_RE`/hooks.json-cross-check logic by hand against the staged
files before committing -- result: both new rows resolve correctly, an
`out-of-tree` classification would have mismatched since the hook script
itself contains no literal write-call text).

New end-to-end test, `tests/test_amends_landing_e2e.py`, the scenario the
reopen comment named as "the test that matters": through the REAL
`amends-index-preflight.sh` (simulated `PreToolUse` payload, same
technique PR #3160 used) and the REAL `land()`, against a local bare-repo
remote (no GitHub credentials needed) --
1. an unrelated session's report commit (no `amends:` field) is never
   blocked;
2. a correcting session commits its own target+corrector pair through the
   real preflight hook -- succeeds;
3. `land()` is called directly (representing exactly what
   `amends-landing-apply.sh` does automatically -- no human runs the CLI
   by hand) and pushes the applied backlink back to the bare remote;
4. fetching the landed tree and opening the target directly shows the
   backlink marker under the amended heading, with the Summary section
   byte-identical (section grain preserved).

derived: `python3 -m pytest tests/test_amends_landing_e2e.py -q` --
result: 1 passed.

**silent-failure-audit pass (skill applied) on the new code.** derived:
invoked the `silent-failure-audit` skill against
`gates/amends_landing.py` and `on-the-record/hooks/amends-landing-apply.sh`
this session; found and fixed three real sites, committed at `3c6b59e1`:
(a) `land()` discarded `git commit`'s own returncode -- a silent commit
failure would fall through to `git push` and report `pushed: True` with
nothing actually landed (fixed: checked explicitly, returns `error`
instead); (b) `write_backlinks()`/`update()` were called unguarded
inside `land()`, contradicting its own "never raises" docstring claim
(fixed: wrapped in `try/except (OSError, ValueError)`); (c)
`amends-landing-apply.sh`'s final `subprocess.run` (the call to
`amends_landing.py` itself, `timeout=180`) had no
`OSError`/`SubprocessError` guard, so a hang would surface as a raw
traceback instead of this file's own fail-open-and-report posture used
everywhere else in it (fixed: wrapped, consistent stderr message).
derived: `python3 -m pytest tests/test_amends_landing_e2e.py
tests/test_amends_index_wiring.py -q` (re-run after the fix) -- result:
11 passed.

Final verification, this session, in order -- derived:
```
python3 -m pytest tests/test_amends_resolution.py -q      # 19 passed
python3 gates/probe_amends_is_discoverable.py; echo $?     # ok, exit 0
python3 gates/probe_amends_fails_closed.py; echo $?         # ok, exit 0
python3 -m pytest tests/ -q                                # 331 passed, 2 warnings
python3 -m pytest test/ -q                                  # 563 passed, 3 xfailed, 0 failed
```
331 is up from 323 pre-existing (8 new in `test_amends_index_wiring.py`
plus 1 new e2e test). `test/ -q`'s 0-failed state matches PR #3160's own
record's explanation (this branch forks from current `main`, after issue
#3091's fix already landed there), reproduced independently rather than
assumed.

## Why

The reopen comment named one root cause behind all four findings: the
enforcement built in round 2 was wired at the wrong time (commit, not
merge), against the wrong scope (whole tree, not the diff), with no
writer for the thing it demands (nothing calls the landing step). The
task offered two honest resolution shapes for finding 1: move enforcement
to merge time on `merge-allow-gate.sh`'s fastpath, or keep a scoped
commit-time check and refuse to LAND unlinked. This round took a hybrid
that keeps both properties without redundant enforcement: `check_staged()`
guarantees, at commit time, that only a structurally-sound edge (real
target, real section, no conflict, no cycle) can ever land -- and a
structurally-sound edge is, by construction, always resolvable by
`write_backlinks()`. Given that guarantee, the automatic apply step
(finding 3's `land()`) deterministically resolves every edge that reaches
it; there is no remaining class of "landed but still unlinked" for a
merge-time DENY gate to catch in the normal case. `check_landing()` was
still built and tested (not merely designed) for the residual race case
(two PRs independently landing correctors for the same target#anchor)
but is honestly documented as tested-not-wired rather than claimed live,
since `amends-landing-apply.sh` is `PostToolUse` and cannot deny --
wiring an actual `PreToolUse`/`gh pr merge` deny gate for that race is
named as a real, scoped follow-up rather than silently left unaddressed.

`land()` clones into a disposable directory rather than mutating the
orchestrator's own live checkout, mirroring PR #3160's own worktree
pattern and `merge-allow-gate.sh`/`impact-guard.sh`'s established
shared-checkout-clone precedent -- a concurrent session or human using
that checkout must never have their working tree rewritten out from
under them by a background side effect.

Rejected: fixing finding 4 by having `--update` and `check` both require
an explicit repo argument (removing the no-arg default entirely). This
would just move the same cwd-dependence bug to every caller instead of
fixing it once; anchoring the default to `_REPO_ROOT` (already computed
for the sys.path insert two lines above) fixes it centrally with no
behavior change for the common case (running from the checkout root, as
every existing caller already does) and no removed capability (an
explicit arg for a scratch/test repo still works exactly as before).

The knowledge-management-supersession-lifecycle skill was checked
against this task and judged not applicable: this session neither marks
a knowledge-library entry superseded/deprecated nor edits one -- it
repairs the enforcement wiring around the `amends:` mechanism itself, a
one-level-down primitive `supersedes:`'s own resolver does not touch. The
implementation-blueprint and test-derivation skills were checked and
judged not applicable in the strict sense their trigger describes: the
new module/hook shapes here closely mirror tightly-established existing
precedent in this repo (`post-landing-obligation-gate.sh`'s exact
command-shape/identity/success-detection pattern, `merge-allow-gate.sh`'s
disposable-checkout-clone pattern) rather than requiring an open
archetype selection from a blank slate, and the four things needing tests
were already concrete, literal reproduction scenarios named in the reopen
comment rather than abstract requirements needing black-box technique
routing (equivalence partitioning, decision tables, etc.) to derive test
cases from.

## What did not work

None.

## Upstream basis

See frontmatter `upstream:`. Also read in full this session, for context
(not upstream inputs this record builds on): `amends.py`,
`amends_backlink.py`, `gates/amends_index.py`,
`on-the-record/hooks/amends-index-preflight.sh`,
`on-the-record/hooks/merge-allow-gate.sh`,
`on-the-record/hooks/post-landing-obligation-gate.sh`,
`on-the-record/hooks/gate-registration-guard.sh`,
`on-the-record/hooks/pretooluse_dispatcher.py`,
`on-the-record/hooks/hooks.json`, `docs/specs/enforcement-boundary.md`,
`docs/specs/generated-paths.md` -- all read this session on this
session's own branch (main tip `43b689f32fbc623281b6e803e18a5ad46544a39e`
at session start).

## Open findings

None from this round -- all four reopen findings fixed and re-verified
live (see "What was done" above for each finding's own before/after
reproduction). One follow-up named honestly rather than silently left:
canonical: this session's own design reasoning above ("Why" section) --
a merge-time `PreToolUse`/`gh pr merge` DENY gate calling
`check_landing()` for the residual two-PRs-race case is designed and
tested (see the `CheckLandingTest` rows in the pass list above) but not
wired into a live hook, since the automatic apply step already resolves
every structurally-sound edge deterministically and `check_staged()`
already refuses a structurally-unsound one at commit time -- the race
window is genuinely narrow (two correctors for the same target#anchor
landing in truly concurrent PRs) and out of this round's frozen scope,
which derived: `gh issue view 3134 --comments` (cited in frontmatter
upstream) fixes as exactly the reopen comment's four named findings, not
a new one this session found on its own.

## Next steps

None -- `loop_state: done`. derived: the final verification block in
"What was done" above (`python3 -m pytest tests/ -q` -- result: 331
passed; `test/ -q` -- result: 563 passed, 0 failed) is the execution-live
basis for `done`, run in this same session. canonical: this session's own
tool-call history this turn contains no `gh pr merge`, `gh pr edit`, or
similar closing/merging action against any PR -- the PR this delivery
opens carries an `Advances #3134` trailer (not `Closes`), since this
delivery repairs a reopened issue's own thread rather than asserting a
fresh closure this session did not itself adjudicate as final, consistent
with `pr-preflight.sh`'s own escape hatch for a PR that references but
does not itself close an issue.

skill-verdict: silent-failure-audit — applied: invoked; audited
`gates/amends_landing.py`'s `land()` and
`on-the-record/hooks/amends-landing-apply.sh`'s new subprocess/error
paths, found and fixed three real silent-failure sites (see "What was
done" above, commit `3c6b59e1`)
skill-verdict: implementation-blueprint — not-applicable: the new
module/hook shapes closely mirror this repo's own tightly-established
precedent (`post-landing-obligation-gate.sh`, `merge-allow-gate.sh`)
rather than requiring an open architecture/archetype selection
skill-verdict: test-derivation — not-applicable: the four things needing
tests were already concrete, literal reproduction scenarios the reopen
comment itself named, not abstract requirements needing black-box
technique routing to derive test cases from
skill-verdict: knowledge-management-supersession-lifecycle —
not-applicable: this session repairs `amends:`'s own enforcement wiring;
it neither marks nor edits any knowledge-library entry's
superseded/deprecated status
other mounted skills: not triggered
