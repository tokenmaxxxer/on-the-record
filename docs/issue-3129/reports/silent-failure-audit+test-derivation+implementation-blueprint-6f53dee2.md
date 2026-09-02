---
issue: 3129
role: silent-failure-audit+test-derivation+implementation-blueprint-6f53dee2
author: silent-failure-audit+test-derivation+implementation-blueprint-6f53dee2
skills: silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: on-the-record/hooks/amendment_channel.py, tests/test_amendment_channel.py, gates/probe_running_session_sees_amendment.py, gates/probe_amendment_notice_fires_once.py, docs/specs/generated-paths.md
loop_state: landed
type: fix
breaking: false
verdict: pass — acceptance: `python3 -m pytest tests/test_amendment_channel.py -q` — result: 47 passed; acceptance: `python3 gates/probe_running_session_sees_amendment.py` — result: ok; acceptance: `python3 gates/probe_amendment_notice_fires_once.py` — result: ok; acceptance: `python3 -m pytest tests/ -q` — result: 301 passed, 0 failed
upstream:
  - path: docs/issue-3129/reports/implementation-blueprint+silent-failure-audit+test-derivation-a641f019.md
    sha: 587dfa893b0f40ac7cfdcf570529187b39efd0aa
---

# issue-3129 — silent-failure-audit+test-derivation+implementation-blueprint-6f53dee2 record

## What was done

Repair round on PR #3137, delivered as commits on branch issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019 (checked out and pushed to directly, per this session's spawn instructions — no new branch/PR opened for the code). None of that branch's own new/edited files (amendment_channel.py, its test file, the two probes) exist on this record's own branch's tree, since PR #3137 has not merged to main — checked: `git ls-files | grep -c amendment_channel` on this branch → 0. This record is written from this session's own assigned branch, per this repo's board-gate contract (writes under docs/issue-3129/ require the session's own branch unless the issue declares a `maintenance-targets:` entry — checked: `gh issue view 3129 --json body -q .body | grep -i maintenance-targets` — no match). Every code citation below is therefore commit-sha-qualified (`git show <sha>:<path>`), reproducible from any branch regardless of which files exist on this record's own branch.

Scope: the single Incorrect finding both landed independent verifications converged on — the amendment marker state machine keyed the marker by issue number alone, no repo dimension, so two repos sharing branch shape issue-42/some-role collided on the same marker file.

canonical: second independent verification of PR #3137, commit c76d066260b5c98e8a3c3b26d36ddd6c642ac4b4 — read via `git show c76d0662`. Its body names "the marker is keyed by issue number alone... no repo or org dimension" as the one Incorrect finding among otherwise-Present criteria.

Reproduced through the real `run_hook` entrypoint before making any change (run live during this session on branch a641f019): two git checkouts on branch issue-42/some-role, two different `origin` remotes, amended issue #42 from the first repo's cwd, then fed a worker payload from the second repo's cwd through `run_hook` — it returned the first repo's notice text verbatim.

derived: swapped the pre-fix module content at commit 61065ede in for the working copy (`git show 61065ede:on-the-record/hooks/amendment_channel.py > on-the-record/hooks/amendment_channel.py`, on branch a641f019), ran `python3 -m pytest tests/test_amendment_channel.py -k "cross_repo or unresolvable or different_repos" -q`, restored the fixed file immediately after (captured live during this session, before commit 7d951975 landed):
```
FAILED tests/test_amendment_channel.py::MarkerReadWrite::test_different_repos_get_independent_markers
FAILED tests/test_amendment_channel.py::RunHookEndToEnd::test_two_repos_with_unresolvable_slugs_do_not_collide
FAILED tests/test_amendment_channel.py::GhCommandDetection::test_unresolvable_repo_does_not_write_a_marker_and_logs_to_stderr
FAILED tests/test_amendment_channel.py::RunHookEndToEnd::test_cross_repo_amendment_does_not_leak_to_an_unrelated_repo
4 failed in 0.94s
```

Fix, in commit order on branch a641f019:

1. `7d951975:on-the-record/hooks/amendment_channel.py` — added `repo_slug_for_cwd(cwd)`, which resolves owner/repo from `git remote get-url origin` (local git-config plumbing, no network) plus a regex over https/`git@host:`/`ssh://` URL shapes. `marker_path`, `seen_path`, `read_marker`, `write_amendment`, `_read_seen`, `_write_seen`, `check_notice` all gained a required `repo` parameter; on-disk filenames now carry it (`issue-<n>__<repo>.marker.json`, `seen/<session>__<repo>__issue-<n>.json`). `maybe_write_from_command` and `run_hook` resolve `repo` from the payload's `cwd` and skip the write/read entirely when it is `None`, with one stderr diagnostic on the write side.
2. `0eb2daf8:tests/test_amendment_channel.py` (built up across commits b0fddeaf then 0eb2daf8) — every existing call site updated for the new `repo` parameter; test fixtures gained a real `origin` remote (previously plain `git init` with none, which would have made every existing test's repo unresolvable under the new design). New cases — see "Test derivation" below.
3. `57987dd6:gates/probe_running_session_sees_amendment.py` and `57987dd6:gates/probe_amendment_notice_fires_once.py` — both probes previously ran the orchestrator's `gh issue edit` from either a bare non-git `orchestrator_cwd` or a plain `git init` worker repo with no `origin`; both fixtures now share one `origin` URL across the worker checkout and the orchestrator's own cwd. Probe 1's marker-existence check now computes the expected path via the module's own `marker_path()` (imported for path computation only; the hook script itself still runs unmodified as a subprocess).
4. `docs/specs/generated-paths.md` (commit bedd1c72): updated the amendment-channel.sh row's filename description from the stale issue-only-keyed shape to the repo-and-issue-keyed one.

## Why

**Why local `git remote get-url origin` instead of reusing `plumbing._repo_slug()`** (what PR #3084 and #3106 both reuse for `requirement_drift`/`spawn_on_pr`, per this session's spawn instructions — canonical: read via `git show e5172b24` and `git show b9457ad1`): `plumbing._repo_slug()` shells out to `gh repo view --json nameWithOwner`, a network round trip, cached only for the lifetime of one process. The amendment-channel module runs as a brand-new `python3` subprocess on every single `PostToolUse` call (its `.sh` wrapper execs it fresh each time — no persistent process, no cross-call cache), so calling `_repo_slug()` from the read path (which runs on every worker tool call) would reintroduce, on the repo-resolution step, the exact `gh`-polling-from-`PostToolUse` cost issue #3129's own acceptance criteria forbid on the amendment-check step itself. `git remote get-url origin` is local git-config plumbing — the same no-network technique already used elsewhere in this repo (canonical: `git show 61065ede:spawn.py | sed -n '3160,3172p'` — `_workspace_target_path()`, which builds the origin URL locally before any clone/fetch).

This is a deliberate departure from "reuse their slug resolution" read as "call the same function": read instead as "reuse the owner/repo identity scheme," not the specific network-based resolver, since reusing the resolver verbatim would reopen the must-not issue #3129 itself names. Recorded here per this session's own spawn instruction to record an ambiguous reading rather than wait mid-flight for approval that cannot reach a running session — the exact problem issue #3129 is about.

**Why an unresolvable repo skips the write/read entirely, with no fallback identifier** (issue #3128's requirement, applied here pre-emptively): issue #3128 was still open at the time of this session — canonical: `gh issue view 3128` → `state: OPEN`; derived: `git ls-files | grep -c "test_repo_slug_unresolvable\|probe_unresolvable_slug_does_not_merge_repos"` → 0 in this tree, so there was no landed reference implementation to copy from (those two names are issue #3128's own named, not-yet-built acceptance files — cited here as absent by design, not as existing paths, so left unbacktick'd). Any shared fallback key — a literal string, a path hash, a cwd basename — is itself a bucket two different unresolvable repos would collide into, the identical leak this repair fixes for the resolvable case. Skipping the write/read means no bucket is ever created for an unresolvable repo. The write side logs one stderr line per occurrence since it corresponds to a single, rare orchestrator action; the read side stays silently quiet, matching the module's three pre-existing silent-quiet conditions on its own read path (missing cwd/session_id/issue), for the same reason.

**Why the test/probe fixtures needed real `origin` remotes added, not just call-site signature updates**: the pre-existing fixtures were plain `git init` repos or bare directories with no `origin` configured. Under the new required-repo design those resolve to `None`, so leaving them unchanged would silently degrade nearly the whole existing suite to skipped writes / `None` reads rather than failing loudly on a signature mismatch — the same silent-regression shape this repair fixes, just relocated into the tests.

## Test derivation

derived: `python3 -m pytest tests/test_amendment_channel.py -q` — run live during this session on branch a641f019 at commit bedd1c72:
```
...............................................                          [100%]
47 passed in 0.96s
```
derived: `python3 -m pytest tests/test_amendment_channel.py -q --collect-only 2>&1 | grep -c "::"` → 47 (35 pre-existing before this session + 12 added by this session).

New cases added by this session, by class:
- `MarkerReadWrite.test_different_repos_get_independent_markers` — unit-level: two repos, same issue number, independent marker read-back.
- `RunHookEndToEnd.test_cross_repo_amendment_does_not_leak_to_an_unrelated_repo` — end-to-end via `run_hook`, the pre-fix reproduction above turned into a permanent regression test.
- `RunHookEndToEnd.test_two_repos_with_unresolvable_slugs_do_not_collide` — issue #3128's shape applied here.
- `GhCommandDetection.test_unresolvable_repo_does_not_write_a_marker_and_logs_to_stderr` — write-side unresolvable case.
- `RepoSlugForCwd` — a new class covering the https origin, `git@host:owner/repo.git` SSH, `ssh://host/owner/repo`, no origin remote, unparseable origin, non-git directory, missing directory, and empty cwd partitions.

derived: `git show bedd1c72:tests/test_amendment_channel.py | sed -n '/^class RepoSlugForCwd/,/^class IssueForCwd/p' | grep -c "    def test_"`
```
8
```

Skill-tool test-derivation run, second invocation (run against the already-landed first round of cases above), is what surfaced the `RepoSlugForCwd` gap: the first round only exercised `repo_slug_for_cwd` indirectly through the https form. `spawn.py`'s own `_workspace_target_path()` explicitly handles the `git@host:` SSH form elsewhere in this repo (canonical: `git show 61065ede:spawn.py | sed -n '3169,3172p'`), so that partition was a real, not hypothetical, gap.

## Silent-failure audit

Skill-tool run against this diff's new error-handling sites.

derived: `git show bedd1c72:on-the-record/hooks/amendment_channel.py | sed -n '124,154p'` (repo_slug_for_cwd, the new function) plus the two call sites:
```
136:    if not cwd or not isinstance(cwd, str) or not os.path.isdir(cwd):
137:        return None
140:    except (OSError, subprocess.SubprocessError):
141:        return None
142:    if r.returncode != 0:
143:        return None
145:    if not origin:
146:        return None
148:    return m.group("slug") if m else None
344:    if repo is None:   # maybe_write_from_command
410:    if not repo:       # run_hook
```
All sites classify Handled: each returns/consumes an explicit `None` a caller checks — the write side (line 344) additionally logs a stderr diagnostic; the read side's silent `None` (line 410) was checked against the module's three pre-existing sibling silent-quiet conditions (missing cwd/session_id/issue, same function, immediately above line 410) and found consistent with that established design, not a new gap this diff introduces. No empty catch block, no bare `except: raise-swallowed`, no default-value substitution left untraced.

## Upstream basis

- PR #3137's own implementation record, commit 587dfa893b0f40ac7cfdcf570529187b39efd0aa — the deliverable this repair round patches. canonical: read in full via the Read tool before making any change.
- Second independent verification of PR #3137, commit c76d066260b5c98e8a3c3b26d36ddd6c642ac4b4 (PR #3147) — canonical: read via `git show c76d0662`.
- Issue #3129, canonical: `gh issue view 3129` (full body read in this session).
- Issue #3128, canonical: `gh issue view 3128` → `state: OPEN`.
- PR #3084 (commit e5172b24565e990f974292614df951410d729ce, issue #3081) and PR #3106 (commit b9457ad1f1cdd330da384ffd3d3c702d33ada193, issue #3095) — canonical: read via `git show e5172b24` / `git show b9457ad1`, to confirm the repo-keying shape this repair's marker/seen filenames follow before departing from their specific network-based resolver (see "Why" above).

## skill-verdict

- skill-verdict: silent-failure-audit — applied: invoked; see "Silent-failure audit" section above (derived: the `git show`/`sed` line-cite block there) for the sites and classification.
- skill-verdict: test-derivation — applied: invoked; invoked twice, see "Test derivation" section above (derived: the `pytest --collect-only` count and the `RepoSlugForCwd` method-count block there) for the derived cases and the coverage gap the second invocation found.
- skill-verdict: implementation-blueprint — not-applicable: targeted repair inside one already-existing single-file module (a parameter addition plus one new helper function), not new multi-module architecture or a parallel-worker fan-out decision — the skill's own stated exclusion ("do NOT use for... a one-line fix... purely algorithmic work") covers this shape.
- other mounted skills: not triggered.

## Open findings

None open from this repair round's own scope.

acceptance: `python3 -m pytest tests/test_amendment_channel.py -q` — run live this session on branch a641f019 at commit bedd1c72 — result:
```
...............................................                          [100%]
47 passed in 0.96s
```
acceptance: `python3 gates/probe_running_session_sees_amendment.py` — result: `ok`
acceptance: `python3 gates/probe_amendment_notice_fires_once.py` — result: `ok`
acceptance: `python3 -m pytest tests/ -q` — result:
```
301 passed, 2 warnings in 10.20s
```

Informational, not part of issue #3129's acceptance (per this session's spawn instructions, reported separately, pre-existing and owned by issue #3091):
acceptance: `python3 -m pytest test/ -q` — result: `15 failed, 548 passed, 3 xfailed`. derived: `git stash && python3 -m pytest test/ -q; git stash pop` run once before the fix and once after, on branch a641f019 — the same 15 test names failed both times, none amendment-channel-related.

Issue #3128 itself remains open on `main` as a separate, broader-scoped issue (also covers `watchdog.requirement_drift` and `spawn_on_pr.parked_report`, neither touched by this session) — this repair applies its stated requirement to the amendment-channel module specifically, pre-emptively.

## What did not work

Nothing attempted in the repair itself was abandoned or reverted. The one deviation from a literal reading of the spawn instructions — using `repo_slug_for_cwd()`'s local-only resolution instead of literally calling `plumbing._repo_slug()` — is a deliberate reading of an ambiguous instruction, made once and kept, documented in the "Why" section above rather than a false start.

Landing this record hit a board-gate: writing under docs/issue-3129/ from branch a641f019 (where all the code commits above landed) was refused — the contract requires this session's own assigned branch (issue-3129/silent-failure-audit+test-derivation+implementation-blueprint-6f53dee2) for that path unless the issue declares a `maintenance-targets:` entry, which issue #3129 does not. Resolved by switching to this session's own branch to write this record, keeping all code commits on a641f019 where the spawn instructions explicitly directed them, and citing every code fact above by commit sha rather than the current branch's own working tree, so the citations stay reproducible regardless of which branch this record itself lives on.

## Next steps

None from this repair round.

acceptance: `git log --oneline -1 issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019` — result:
```
bedd1c72 issue-3129: update generated-paths.md for the repo-keyed marker filename
```
That branch's commits are pushed to origin; PR #3137 stays open, not merged by this session, per spawn instructions. This record's own branch is pushed separately, per the board-gate resolution above.
