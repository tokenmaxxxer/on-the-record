---
issue: 3129
role: adversarial-review+silent-failure-audit+test-depth-audit-e93e7a3b
author: adversarial-review+silent-failure-audit+test-depth-audit-e93e7a3b
skills: adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3137's repair round 3 (commits f20da852, d582459c)
code_under_review: d582459c2c7109fd3c5e0058e781e425f0bba224
type: defect-verification-record
breaking: false
loop_state: landed
verdict: Round-3-enumerated shapes (heredoc, semicolon, subshell-wrapping-the-whole-`cd`-chain,
  `-R`-before-subcommand) Present — acceptance: `python3 /tmp/verify5_test/harness.py
  /tmp/pr3137-verify5/on-the-record/hooks` (against `d582459c`) — result: all four correctly keyed to
  the `cd`/`-R` target, zero session-cwd leakage. Un-enumerated shapes — acceptance: same harness —
  derived: `printf '%s\n' subshell-gh-cd-outside pushd-not-cd repo-equals-before-number
  gh-repo-env-prefixed quoted-path-with-space | wc -l` — result: 5 (of 9) Incorrect (`cd /a && (gh issue
  edit 42 --body x)` total silent miss; `pushd /a && gh issue edit 42 --body x` silently keyed to
  session cwd; `gh issue edit --repo=o/r 42 --body x` total silent miss; `GH_REPO=o/r gh issue edit 42
  --body x` total silent miss; `cd "/path with space" && gh issue edit 42 ...` silently keyed to session
  cwd). derived: `printf '%s\n' two-cds-must-key-to-second gh-looking-text-inside-heredoc
  gh-api-not-issue-edit gh-issue-comment-not-edit | wc -l` — result: 4 (of 9) Present: correctly-keyed
  `cd /a; cd /b && gh issue edit 42 --body x` (keys to `/b`), correctly-keyed heredoc body containing a
  gh-issue-edit-looking line, and two non-edit `gh` commands correctly writing no marker. Round-3's own
  `ShapesFailAgainstPreRepairCommit` regression class Present, confirmed non-tautological — acceptance:
  `diff <(git show bf28bf93:on-the-record/hooks/amendment_channel.py)
  on-the-record/hooks/amendment_channel.py` (from `/tmp/pr3137-verify5`) — derived: `diff ... | wc -l` —
  result: 77, the pre-repair fetch is genuinely different code; acceptance: `python3 -m pytest
  tests/test_amendment_channel.py::ShapesFailAgainstPreRepairCommit -v` — result: 4 passed. Cross-repo
  isolation, unresolvable-slug isolation, fire-once/absorption — all Present, re-confirmed — acceptance:
  `python3 -m pytest tests/test_amendment_channel.py -q -k "cross_repo or unresolvable_slugs or
  FiresOncePerAmendment or AbsorbedAmendmentStopsAnnouncing"` — result: 11 passed; acceptance: `python3
  gates/probe_running_session_sees_amendment.py` — result: ok, exit 0; acceptance: `python3
  gates/probe_amendment_notice_fires_once.py` — result: ok, exit 0. Full suite Present, count unchanged —
  acceptance: `python3 -m pytest tests/test_amendment_channel.py -q` — result: 66 passed; acceptance:
  `python3 -m pytest tests/ -q` — result: 320 passed, 0 failed, matching PR #3167's own record;
  acceptance: `python3 -m pytest test/ -q` — result: 15 failed, 548 passed, 3 xfailed, same 5 files
  PR #3091 already owns, count did not move.
upstream:
  - path: docs/issue-3129/reports/adversarial-review+silent-failure-audit+test-depth-audit-0be2218f.md
    sha: c045d4a4f069a2967a82a64a08807849f50c9c0f
  - path: docs/issue-3129/reports/implementation-blueprint+silent-failure-audit+test-derivation-18d0fea5.md
    sha: b0bc14ac4e32033624ff3042e1587d2a0ced8fb8
  - path: on-the-record/hooks/amendment_channel.py (PR #3137, branch -a641f019)
    sha: d582459c2c7109fd3c5e0058e781e425f0bba224
---

# issue-3129 — adversarial-review+silent-failure-audit+test-depth-audit-e93e7a3b record

## What was done

canonical: `gh pr view 3137` output (head `d582459c2c7109fd3c5e0058e781e425f0bba224`, unchanged since
PR #3167's round-3 record) — derived: `git log -1 pr-3137-verify5 --format='%H %s'` after `git fetch
origin pull/3137/head:pr-3137-verify5` — result: `d582459c... issue-3129: close test-derivation gaps
found by post-fix silent-failure-audit/test-derivation pass`, matching the sha PR #3167's record cites.
PR #3163's record (round 2's findings) and PR #3167's record (round 3's fix — Design A shell-aware
parsing with heredoc-body stripping, `;`/`||`/subshell/`{ }`-brace support, chained-`cd` walking, flags-
before-subcommand detection, `target_repo_for_command()` calling the tri-state `cd_target()` resolver
directly instead of the permissive `resolved_cwd()` wrapper), both read first per the spawning prompt.
This session's assignment: round 3 closed exactly the 8 shapes PR #3163 enumerated (plus 4 bonus
coverage gaps its own post-fix audit found) — a fix that targets an enumerated list closes those and
nothing else, so this session drove the real `run_hook` entrypoint (via the real `amendment-channel.sh`
wrapper, matching production cwd/env handling) against nine shapes NOT on that list.

derived: `git worktree add /tmp/pr3137-verify5 pr-3137-verify5` (head `d582459c`) and `git worktree add
/tmp/pr3137-prefix5 bf28bf93` (round 2's tip, the commit round 3's fix landed on top of) — neither
worktree was merged into or edited, per the spawning prompt's explicit instruction not to edit or merge
PR #3137.

### 1. Nine un-enumerated command shapes, both worktrees

canonical: `d582459c:tests/test_amendment_channel.py:601-627` (`WriterSideParserHandlesRealCommandShapes.
_payload`/`_assert_keys_to_study_not_session`), read first, gave the payload/assertion shape this
session's own harness reuses. derived: harness at `/tmp/verify5_test/harness.py` — three git checkouts
per run (`session-checkout` origin `tokenmaxxxer/on-the-record`, `a-checkout` origin
`tokenmaxxxer/repo-a`, `b-checkout` origin `tokenmaxxxer/repo-b`, plus a `path with space` checkout
origin `tokenmaxxxer/repo-space`), each command run through `bash on-the-record/hooks/amendment-
channel.sh` via `subprocess.run(cwd=session_cwd, input=payload)` — the accurate production invocation
shape.

acceptance: `python3 /tmp/verify5_test/harness.py /tmp/pr3137-verify5/on-the-record/hooks` (tip
`d582459c`) — result:

```
subshell-gh-cd-outside            cd /a && (gh issue edit 42 --body x)
  -> markers: []  stdout: ''  stderr: ''
two-cds-must-key-to-second        cd /a; cd /b && gh issue edit 42 --body x
  -> markers: ['issue-42__tokenmaxxxer_repo-b.marker.json']
pushd-not-cd                      pushd /a && gh issue edit 42 --body x
  -> markers: ['issue-42__tokenmaxxxer_on-the-record.marker.json']  stderr: ''
repo-equals-before-number         gh issue edit --repo=tokenmaxxxer/repo-a 42 --body x
  -> markers: []  stdout: ''  stderr: ''
gh-repo-env-prefixed              GH_REPO=tokenmaxxxer/repo-a gh issue edit 42 --body x
  -> markers: []  stdout: ''  stderr: ''
quoted-path-with-space            cd "/path with space" && gh issue edit 42 --body x
  -> markers: ['issue-42__tokenmaxxxer_on-the-record.marker.json']  stderr: ''
gh-looking-text-inside-heredoc    cd /a && gh issue edit 42 --body-file - <<'EOF'
                                   this line contains && gh issue edit 99 --body evil
                                   EOF
  -> markers: ['issue-42__tokenmaxxxer_repo-a.marker.json']
gh-api-not-issue-edit             gh api -X PATCH repos/tokenmaxxxer/repo-a/issues/42 -f body=x
  -> markers: []
gh-issue-comment-not-edit         cd /a && gh issue comment 42 --body x
  -> markers: []
```

acceptance: same harness re-run against `/tmp/pr3137-prefix5/on-the-record/hooks` (`bf28bf93`, round
2's tip, one commit before round 3's fix) — result:

```
subshell-gh-cd-outside            markers: []  (identical to tip)
pushd-not-cd                      markers: ['issue-42__tokenmaxxxer_on-the-record.marker.json']  (identical)
repo-equals-before-number         markers: []  (identical)
gh-repo-env-prefixed              markers: []  (identical)
quoted-path-with-space            markers: ['issue-42__tokenmaxxxer_on-the-record.marker.json']  (identical)
two-cds-must-key-to-second        markers: ['issue-42__tokenmaxxxer_on-the-record.marker.json']  (WRONG pre-repair; tip is right)
gh-looking-text-inside-heredoc    markers: ['issue-42__tokenmaxxxer_on-the-record.marker.json']  (WRONG pre-repair; tip is right)
```

Five shapes are byte-identical between the two worktrees (not a round-3 regression, but never closed by
round 3 either); two (`two-cds-must-key-to-second`, `gh-looking-text-inside-heredoc`) differ, confirming
round 3 genuinely fixed those two.

canonical: `d582459c:on-the-record/hooks/amendment_channel.py:147-149`:

```python
_GH_ISSUE_EDIT_RE = re.compile(
    r"(?:^|[;&|]\s*)gh\s+(?:(?!issue\s+edit\b)\S+\s+)*issue\s+edit\s+(\d+)\b"
)
```

derived: standalone regex check at `/tmp/verify5_test/check_regex.py`, importing this exact module —
result:

```
subshell-wrap-gh match: None
repo-eq-before-number match: None
env-prefixed match: None
```

`.search()` returns `None` for `"cd /a && (gh issue edit 42 --body x)"` (the anchor `(?:^|[;&|]\s*)`
never matches immediately before `gh` when a bare `(` precedes it — subshells are not in the anchor's
character class), `None` for `"gh issue edit --repo=tokenmaxxxer/repo-a 42 --body x"` (the mandatory
`issue\s+edit\s+(\d+)` suffix requires digits immediately after `edit`, and `--repo=...` sits between
`edit` and `42`), and `None` for `"GH_REPO=tokenmaxxxer/repo-a gh issue edit 42 --body x"` (the anchor
requires `gh` at start-of-string or right after `;`/`&`/`|`; an env-var-assignment prefix satisfies
neither).

canonical: `d582459c:on-the-record/hooks/amendment_channel.py:454-456`:

```python
    m = _GH_ISSUE_EDIT_RE.search(command)
    if not m or not _BODY_FLAG_RE.search(command):
        return
```

All three commands above hit this early `return` — no marker, no stderr, no observable trace at all,
matching the harness's empty-`stdout`/empty-`stderr`/empty-`markers` result for those three cases.

canonical: `d582459c:on-the-record/hooks/hook_input.py:100-103`:

```python

_CD_STEP_RE = re.compile(r"^\s*cd\s+(\S+)\s*(?:&&|\|\||;|\n)")
_HEREDOC_OPEN_RE = re.compile(r"<<(-)?\s*(['\"]?)(\w+)\2")

```

derived: standalone check at `/tmp/verify5_test/check_cd.py`, importing this exact module — result:

```
quoted-space cd_target: NoCdTarget(reason='no-cd-prefix')
pushd cd_target: NoCdTarget(reason='no-cd-prefix')
subshell-only-gh cd_target (cd is outside): CdTarget(path='/a')
```

`hook_input.cd_target('cd "/path with space" && do-thing')` returns `NoCdTarget` (`\S+` cannot cross the
embedded space inside the quoted path, so the regex never matches the `&&` terminator at all) and
`hook_input.cd_target("pushd /a && do-thing")` also returns `NoCdTarget` (the literal `cd` token is
required; `pushd` is not recognized as a directory change at all even though it functionally is one).
Both then reach:

canonical: `d582459c:on-the-record/hooks/amendment_channel.py:434-442`:

```python
    explicit = _explicit_repo_flag(command, segment_start)
    if explicit:
        return explicit
    cd_result = hook_input.cd_target(command)
    if isinstance(cd_result, hook_input.CdTarget):
        return repo_slug_for_cwd(cd_result.path)
    if isinstance(cd_result, hook_input.OpaqueCommand):
        return None
    return repo_slug_for_cwd(cwd)
```

`NoCdTarget` falls to the final `return repo_slug_for_cwd(cwd)` line — the session cwd — the exact
"legitimate, no cd at all" fallback reserved for commands that structurally never `cd` anywhere. Both
`pushd /a` and `cd "/path with space"` DO change the effective directory in a real shell; the parser
cannot tell the difference between "genuinely no cd" and "a cd shape I don't recognize," so it silently
substitutes the wrong, resolvable repo instead of reporting unknown — contradicting:

canonical: `d582459c:on-the-record/hooks/amendment_channel.py:63-64`:

```python
Neither source resolving falls through to the same unresolvable-repo
handling below -- never a fallback to the session cwd.
```

derived: same `/tmp/verify5_test/check_cd.py` result above — `hook_input.cd_target("cd /a &&
(do-thing)")` returns `CdTarget(path='/a')` by contrast — the cd-resolution layer itself has no defect
for `subshell-gh-cd-outside`; the sole cause there is `_GH_ISSUE_EDIT_RE` never recognizing `(gh` as a
valid command start (the same fenced anchor `(?:^|[;&|]\s*)` above excludes `(`), a detection-layer gap,
not a resolution-layer one.

**Verdict for this section**: derived: `printf '%s\n' subshell-gh-cd-outside pushd-not-cd repo-equals-
before-number gh-repo-env-prefixed quoted-path-with-space | wc -l` — result: 5 (=5/9 Incorrect, listed
in the harness result table above). Two of those five (`pushd`, quoted-path-with-embedded-space) are
silent cwd-fallbacks — the exact must-not category the task called out and round 3's own docstring
(`amendment_channel.py:63-64` fenced above) claims eliminated. Three of those five (`(gh` subshell,
`--repo=` before the number, `GH_REPO=` prefix) are total silent misses — the command is never even
recognized as `gh issue edit`, so no marker, no notice, and no stderr trace distinguishes it from
nothing having happened. derived: `printf '%s\n' two-cds-must-key-to-second gh-looking-text-inside-
heredoc gh-api-not-issue-edit gh-issue-comment-not-edit | wc -l` — result: 4 (=4/9 Present, listed in
the same table): the two chained-`cd` and heredoc-with-injected-fake-command cases correctly key to the
real target and ignore the injected fake, and the two non-edit `gh` commands correctly write no marker
at all (`_GH_ISSUE_EDIT_RE` requires the literal substring `issue\s+edit`, which `gh api ...` never
contains and `gh issue comment ...` does not satisfy).

### 2. Round-3's own regression class against `bf28bf93` — confirmed non-tautological

canonical: `d582459c:tests/test_amendment_channel.py:730-737` (`ShapesFailAgainstPreRepairCommit` class
docstring) and `:774-779`:

```python
    def test_heredoc_mis_keys_to_session_cwd_pre_repair(self):
        cmd = ("cd %s && gh issue edit 42 --body-file - <<'EOF'\n"
               "fixed brief\nEOF" % self.study_repo)
        self._run_pre_repair(cmd)
        self.assertIsNotNone(ac.read_marker(self.state_dir, "tokenmaxxxer/on-the-record", "42"))
        self.assertIsNone(ac.read_marker(self.state_dir, "tokenmaxxxer/study-companion", "42"))
```

This class (`:738-797`) covers exactly 4 of PR #3163's 4 originally-enumerated mis-keying/miss shapes
(heredoc, semicolon, subshell-wrapping-the-whole-`cd`-chain, `-R`-before-subcommand), each run through
the real, unmodified `amendment-channel.sh` fetched via `git show bf28bf93:on-the-record/hooks/<file>`
into a scratch dir (`setUp`, `:738-756`), not the fixed module imported in-process.

acceptance: `diff <(git show bf28bf93:on-the-record/hooks/amendment_channel.py)
on-the-record/hooks/amendment_channel.py` (from `/tmp/pr3137-verify5`) — derived: `diff <(git show
bf28bf93:on-the-record/hooks/amendment_channel.py) on-the-record/hooks/amendment_channel.py | wc -l` —
result: 77 — the fetched pre-repair content is genuinely different from the tip, so this class exercises
different code, not a same-content no-op that would pass regardless of whether the fix exists.

acceptance: `python3 -m pytest tests/test_amendment_channel.py::ShapesFailAgainstPreRepairCommit -v`
(from `/tmp/pr3137-verify5`) — result:

```
4 passed in 0.88s
```

Each test asserts the pre-repair wrong-repo/no-repo outcome (e.g. the fenced
`test_heredoc_mis_keys_to_session_cwd_pre_repair` above asserts the `on-the-record` marker EXISTS and the
`study-companion` marker does NOT) against the real historical script, not the fixed one —
`test-depth-audit`: Genuine Assertion, confirmed by construction (a positive assertion on the OLD
script's wrong output, using content independently confirmed different from the new script by the 77-
line diff above), not Execution-Only and not tautological.

Gap, canonical: same `d582459c:tests/test_amendment_channel.py:730-797` file range read above — this
class does not cover the two-cds, quoted-space, pushd, `--repo=`-before-number, `GH_REPO=`-prefixed, or
`(gh`-subshell shapes from §1 — it only re-confirms PR #3163's own original 4, not this session's newly
found 5 Incorrect cases (three of which, per §1's cross-worktree comparison above, also fail identically
pre- and post-repair, i.e. are not regressions round 3 introduced, but were never closed by it either).

### 3. Cross-repo isolation, unresolvable-slug isolation, fire-once/absorption

acceptance: `python3 -m pytest tests/test_amendment_channel.py -q -k "cross_repo or
unresolvable_slugs or FiresOncePerAmendment or AbsorbedAmendmentStopsAnnouncing"` (from
`/tmp/pr3137-verify5`) — result:

```
11 passed in 0.86s
```

acceptance: `python3 gates/probe_running_session_sees_amendment.py` — result: `ok`, exit 0. acceptance:
`python3 gates/probe_amendment_notice_fires_once.py` — result: `ok`, exit 0. All three re-confirmed
against the current tip in this session's own worktree, not cited from PR #3167's own record. Present.

### 4. Full suite

acceptance: `python3 -m pytest tests/test_amendment_channel.py -q` (from `/tmp/pr3137-verify5`) —
result:

```
66 passed in 1.36s
```

matching PR #3167's own record exactly. acceptance: `python3 -m pytest tests/ -q` — result:

```
320 passed, 2 warnings in 10.55s
```

(the 2 warnings are the pre-existing pinned-fixture-divergence notices from
`test_skill_candidates_floor.py`, unrelated to this module, same as PR #3163's record noted). acceptance:
`python3 -m pytest test/ -q` — result:

```
15 failed, 548 passed, 3 xfailed in 32.08s
```

derived: `python3 -m pytest test/ -q 2>&1 | grep -c FAILED` — result: 15 — the FAILED lines name the same
5 files (`test_convention_equivalence.py`, `test_local_dependency_env.py`,
`test_spawn_artifact_skill_pairing.py`, `test_spawn_cross_family_skill_selection.py`,
`test_spawn_skill_judge_haiku_timeout_overlap.py`) PR #3091 already owns; none touch the writer module,
the shared input-parsing module, or the shipped hook wrapper. Count did not move from PR #3167's own `15
failed, 548 passed, 3 xfailed`. Present.

## Why

canonical: this session's own §1-§4 acceptance/derived citations above (the `66 passed`/`320 passed`
suite runs, the nine-shape harness, and the `ShapesFailAgainstPreRepairCommit` pre-repair diff/test-run)
are the evidentiary basis for the three skill applications below; nothing in this section restates a
number without one of those citations already established above.

Per `adversarial-review`'s blind-evaluator stance, this session did not stop at PR #3163's enumerated
list or at round 3's own green suite (§4 above, `66 passed`) — it built five additional command shapes
plausible for a real orchestrator (`pushd` as a `cd` alternative, a quoted path containing a space, an
env-var-prefixed target, a flag positioned before rather than after the issue number, and a subshell
wrapping only the `gh` invocation rather than the whole `cd && gh` chain) and found the fix (§1 above)
closes exactly its enumerated list and nothing structurally adjacent to it — a parser that handles eight
named shapes and nothing else has narrowed the collision, not closed the family, the same framing PR
#3163's own record (`docs/issue-3129/reports/adversarial-review+silent-failure-audit+test-depth-audit-
0be2218f.md`, read first this session) used against round 2.

Per `silent-failure-audit`, the central question was not whether these five cases crash (nothing here
raises — `run_hook` is a documented total function, canonical:
`d582459c:on-the-record/hooks/amendment_channel.py:493-510`, read first this session, its own docstring)
but whether the wrong outcome is observable. It is not, in either sub-class, per §1's own fenced
citations above: the two silent-cwd-fallback cases (`pushd`, quoted-path-with-space) produce a
plausible, successfully-written marker to the WRONG repo, classified `NoCdTarget` (the "genuinely no cd"
case) rather than `OpaqueCommand` (the "cd present but unparseable" case that already routes to the
no-marker-plus-stderr branch, per the `amendment_channel.py:434-442` fence in §1) — the parser doesn't
know it doesn't know. This is a "default-value substitution without recording that a fallback occurred"
pattern (silent-failure catalog), one level upstream of the `OpaqueCommand`-vs-`NoCdTarget` distinction
the fix's own design correctly drew for the shapes it does recognize. The three total-miss cases (`(gh`
subshell, `--repo=` before the number, `GH_REPO=` prefix) are a plain "unguarded operation" pattern, per
the `_GH_ISSUE_EDIT_RE`/`maybe_write_from_command` fences in §1: the command never reaches ANY of the
module's error-observability machinery (neither the no-marker-plus-stderr branch nor the marker write) —
the mid-flight correction the whole channel exists to deliver silently never happens, with literally zero
trace in stdout, stderr, or the marker directory, per the harness JSON result in §1.

Per `test-depth-audit`, `ShapesFailAgainstPreRepairCommit` (§2 above) was confirmed Genuine Assertion by
construction — its `setUp` fetches the real historical file content via `git show`, independently
confirmed different from the tip by the 77-line diff in §2 — and its four assertions (§2's fenced
example) are positive claims about the OLD script's wrong output, not a tautology that would also pass
against the fixed script. Its narrower scope (4 of PR #3163's original 4 shapes, none of this session's
newly found 5, per §2's "Gap" paragraph) is a coverage gap, not a depth defect in the tests that exist.

## What did not work

canonical: this session's own worktree/harness history (no other record to cite; this is a first-person
account of this turn's own execution). derived: `git worktree list` (run from
`/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-3129-adversarial-review+silent-failure-audit+test-
depth-audit-e93e7a3b`) — result: `/tmp/pr3137-verify5` and `/tmp/pr3137-prefix5` both listed, neither
merged into this branch. None of this session's own reproductions in §1-§4 above failed to run on the
first attempt; no worktree was merged or edited, per the spawning prompt's instruction. One thing worth
flagging as a near-miss, not a failure: PR #3163's own record noted a relative-cd process-cwd-vs-
declared-cwd distinction (canonical: `docs/issue-3129/reports/adversarial-review+silent-failure-audit
+test-depth-audit-0be2218f.md`, "What did not work" section, read first this session) — that concern
does not apply to this session's own 9 shapes since none of them use a relative `cd` target (all use
absolute paths, per the harness command strings quoted verbatim in §1's result block above), so it was
not re-triggered.

## Skill verdicts

skill-verdict: adversarial-review — applied: invoked; used the blind-evaluator stance to build five
command shapes plausible for a real orchestrator beyond PR #3163's own enumerated list (`pushd`, a
quoted path with an embedded space, `GH_REPO=` env-var prefix, `--repo=` before the issue number, and a
subshell wrapping only `gh`) rather than stopping at round 3's own suite — canonical: §4 above's
`acceptance: python3 -m pytest tests/test_amendment_channel.py -q` — result: `66 passed` fence, cited
alongside the independent reproductions in §1 that still break two of the three categories the fix's own
docstring (`amendment_channel.py:63-64` fence, §1 above) claims to have closed.

skill-verdict: silent-failure-audit — applied: invoked; classified the two silent-cwd-fallback shapes
(`pushd`, quoted-path-with-space) as a default-value-substitution-without-recording pattern one layer
upstream of the `OpaqueCommand`/`NoCdTarget` distinction the round-3 fix correctly drew for the shapes it
does recognize, and the three total-miss shapes (`(gh` subshell, `--repo=` before the number, `GH_REPO=`
prefix) as an unguarded-operation pattern — canonical: §1's `_GH_ISSUE_EDIT_RE`/`maybe_write_from_command`
/`cd_target` fences and their `check_regex.py`/`check_cd.py` derived results, full trace-forward given
there.

skill-verdict: test-depth-audit — applied: invoked; confirmed `ShapesFailAgainstPreRepairCommit`
(`d582459c:tests/test_amendment_channel.py:730-798`) is Genuine Assertion by construction — canonical:
§2's 77-line-diff fence and the `4 passed` fence — its `setUp`'s `git show bf28bf93:...` fetch was
independently confirmed to differ from the tip, and its 4 assertions are positive claims about the
historical script's wrong output — the closest analog available to mutation testing without hand-editing
the module, sufficient to rule out tautology. Flagged its scope gap (§2's "Gap" paragraph: 4 of PR
#3163's original 4, none of this session's newly found 5) as a coverage gap for whoever picks this
finding up next, not a defect in the tests that exist.

skill-verdict: work-in-english — applied: invoked; this record, every scratch script under
`/tmp/verify5_test/`, and this session's commit messages are in English; the end-of-turn summary to the
user follows in Korean per policy.

other mounted skills: not triggered — `implementation-audit`, `verify-finding-record` (configured by
task-text match, not this role's own mounted set) did not apply — derived: `git ls-files
'**/defect-verification*'` — result: no matches under this issue's own reports tree for this role, so
`verify-finding-record`'s target path convention is not in play; this record already follows
`implementation-audit`'s Present/Surface/Absent/Incorrect/Unverifiable taxonomy directly per the
spawning prompt's own instruction without a separate invocation.

## Upstream basis

canonical: `gh pr view 3137` output and the fetched worktree at head `d582459c2c7109fd3c5e0058e781e425f0bba224`
(same head cited throughout §1-§4 above; not same-commit with this record; this session did not edit or
merge this PR, per the spawning prompt's explicit instruction). Repair round 3 is commits `f20da852` and
`d582459c`, applied on top of round 2's tip `bf28bf93` (PR #3163 already verified Incorrect on 3 of 3
attacked shapes there, per that record read first this session).

- PR #3163's record
  (`docs/issue-3129/reports/adversarial-review+silent-failure-audit+test-depth-audit-0be2218f.md`, merged
  via `c045d4a4`) — read first per this session's spawning instructions; its own "Open findings" §1-§2
  are the two defect classes round 3 was built to close, and this session confirmed both ARE closed for
  the exact shapes PR #3163 named (§1-§2 above), but not for the broader family this session constructed.
- PR #3167's record
  (`docs/issue-3129/reports/implementation-blueprint+silent-failure-audit+test-derivation-18d0fea5.md`,
  merged via `b0bc14ac`) — read first per this session's spawning instructions; every acceptance number
  it cites was independently re-derived against the same tip in §4 above, not cited from that record, and
  matched exactly (`66 passed`, `320 passed, 0 failed`, `15 failed, 548 passed, 3 xfailed`).

## Open findings

1. `cd "/path with space" && gh issue edit 42 --body x` — a quoted `cd` target containing a space
   silently keys the marker to the orchestrator's own session cwd, not the quoted target. derived:
   `/tmp/verify5_test/check_cd.py` result (fenced in §1): `NoCdTarget(reason='no-cd-prefix')` for exactly
   this string, against both `d582459c` and `bf28bf93` (not a regression this round introduced, but
   squarely the "never a fallback to the session cwd" must-not this repair round's own docstring claims
   to guarantee):

   ```python
   Neither source resolving falls through to the same unresolvable-repo
   handling below -- never a fallback to the session cwd.
   ```

   (`d582459c:on-the-record/hooks/amendment_channel.py:63-64`, fenced in full in §1). This is the single
   most common real-world shape of the five found here, since paths containing spaces are routine.
   derived: `/tmp/verify5_test/check_cd.py`, result fenced immediately below — root cause, canonical:
   `d582459c:on-the-record/hooks/hook_input.py:100-103`:

   ```python

   _CD_STEP_RE = re.compile(r"^\s*cd\s+(\S+)\s*(?:&&|\|\||;|\n)")
   _HEREDOC_OPEN_RE = re.compile(r"<<(-)?\s*(['\"]?)(\w+)\2")

   ```

   `_CD_STEP_RE`'s `(\S+)` capture group cannot cross the whitespace inside a quoted path, so the regex
   never matches at all and `cd_target()` returns `NoCdTarget` (the "genuinely no cd" case) instead of
   either correctly resolving the quoted path or returning `OpaqueCommand` (the "cd present but not
   parseable with confidence" case that already routes to the no-marker-plus-stderr branch, per
   `amendment_channel.py:434-442` fenced in §1). Resolution path: extend `_CD_STEP_RE` (or a pre-pass) to
   consume a `'...'`/`"..."` quoted path as a single token before falling through to `\S+`, mirroring the
   quote-stripping already done post-match at `hook_input.py:313-320` (fenced in §1) but applied before
   the terminator match, not after.
2. `pushd /a && gh issue edit 42 --body x` — same silent-cwd-fallback shape as finding 1, for a
   different unrecognized directory-change verb. derived: `/tmp/verify5_test/check_cd.py` result (fenced
   in §1): `NoCdTarget(reason='no-cd-prefix')` for `"pushd /a && do-thing"`, identical against both
   `d582459c` and `bf28bf93` per the harness JSON result in §1. derived: same `check_cd.py` run — root
   cause and resolution path are structurally the same as finding 1, canonical:
   `d582459c:on-the-record/hooks/hook_input.py:100-103` (fenced in finding 1 above) — `_CD_STEP_RE` only
   recognizes the literal token `cd`; `pushd` is not currently in scope at all. Lower priority than
   finding 1 since `pushd` is a less common orchestrator idiom than a quoted path, but the same category
   of defect.
3. `gh issue edit --repo=o/r 42 --body x` (`--repo=` positioned before the issue number, not after) and
   `GH_REPO=o/r gh issue edit 42 --body x` (env-var-prefixed target) are both total silent misses — no
   marker, no stderr. derived: `/tmp/verify5_test/check_regex.py` result (fenced in §1): both `.search()`
   calls return `None` against:

   ```python
   _GH_ISSUE_EDIT_RE = re.compile(
       r"(?:^|[;&|]\s*)gh\s+(?:(?!issue\s+edit\b)\S+\s+)*issue\s+edit\s+(\d+)\b"
   )
   ```

   (`d582459c:on-the-record/hooks/amendment_channel.py:147-149`), identical against both `d582459c` and
   `bf28bf93` per §1's harness comparison. derived: same `check_regex.py` run — neither is a regression
   this round introduced — round 3's own fix widened this regex to tolerate flags BETWEEN `gh` and `issue
   edit`, and separately covered `--repo=` AFTER the issue number, canonical:
   `d582459c:tests/test_amendment_channel.py:650-652`:

   ```python
       def test_repo_flag_equals_form_before_body(self):
           cmd = "gh issue edit 42 --repo=tokenmaxxxer/study-companion --body 'fixed brief'"
           self._assert_keys_to_study_not_session(cmd)
   ```

   but not a flag between `edit` and the number, nor an env-var prefix before `gh` itself. Resolution
   path: for the `--repo=`-before-the-number case, loosen the mandatory `issue\s+edit\s+(\d+)\b` suffix to
   tolerate flags between `edit` and the digits, symmetric to the existing flags-between-`gh`-and-`issue`-
   edit tolerance; for `GH_REPO=`, either widen the anchor to permit a leading `\w+=\S+\s+` prefix, or
   explicitly scope this module to "does not support env-var-prefixed invocations" and route it through
   the observable no-marker-plus-stderr path instead of a bare silent non-match — the module's own
   docstring (`amendment_channel.py:55-64`, quoted in "What was done") already commits to "two sources are
   authoritative," and `GH_REPO` is a third source real `gh` respects that isn't mentioned as
   out-of-scope anywhere in the current docstring.
4. `cd /a && (gh issue edit 42 --body x)` — a subshell wrapping only the `gh` invocation (not the whole
   `cd && gh` chain, which round 3's own test suite already covers) is also a total silent miss, derived:
   `/tmp/verify5_test/check_regex.py` result (fenced in §1): `.search()` returns `None` for this exact
   string against:

   ```python
   _GH_ISSUE_EDIT_RE = re.compile(
       r"(?:^|[;&|]\s*)gh\s+(?:(?!issue\s+edit\b)\S+\s+)*issue\s+edit\s+(\d+)\b"
   )
   ```

   (`d582459c:on-the-record/hooks/amendment_channel.py:147-149`), identical against both `d582459c` and
   `bf28bf93` per §1's harness comparison. derived: `/tmp/verify5_test/check_regex.py` result fenced
   immediately above (`None`) — root cause is at the detection layer, not the resolution layer: the
   anchor `(?:^|[;&|]\s*)` above simply does not include `(` as a valid character immediately preceding
   `gh`. `cd_target()` itself already resolves this shape correctly on its own, derived: the same
   `/tmp/verify5_test/check_cd.py` run fenced below:

   ```
   quoted-space cd_target: NoCdTarget(reason='no-cd-prefix')
   pushd cd_target: NoCdTarget(reason='no-cd-prefix')
   subshell-only-gh cd_target (cd is outside): CdTarget(path='/a')
   ```

   the third line, `CdTarget(path='/a')`, confirms the resolution layer is not at fault here. Resolution
   path: add `(` (and `{`) to the anchor's character class, symmetric to how `_unwrap_enclosing_group()`
   already treats those brackets as transparent wrappers on the `cd`-resolution side.
5. Carried forward, unchanged by this repair round (PR #3147's/#3159's/PR #3163's minor findings, out
   of this round's stated scope, canonical: PR #3163's own record's "Open findings" §3-4, read first this
   session): silent truncation at `_NOTE_MAX` with no truncation marker; `main()`'s stdin/stdout `OSError`
   paths still silently drop; the subshell trailing-`)`-leaking-into-note cosmetic PR #3163 noted (not
   independently re-checked this round, out of this session's assigned shape list). Not re-litigated
   further here.

## Next steps

canonical: findings 1-5 above, each with its own root-cause fence and resolution path already stated in
"Open findings" — this section only orders them, it does not restate unfenced claims. Findings 1-2 are
the highest-priority carry-forward: both are silent-cwd-fallback writes, the exact must-not category this
whole repair round's own docstring (`amendment_channel.py:63-64`, fenced in §1) claims eliminated, and
finding 1 in particular (a quoted path containing a space) is a far more common real-world shape than any
of PR #3163's original four. Findings 3-4 are total silent misses — less dangerous (no wrong data reaches
a worker) but still a complete, untraceable loss of the mid-flight correction the channel exists to
deliver. Finding 5 is carried forward, unchanged, out of scope. This session does not edit or merge PR
#3137, per the spawning prompt's explicit instruction; these findings are handed to whoever picks the PR
up next.

`loop_state: landed` — derived: this record's §1-§4 above, each with its own `acceptance:`/`derived:`
command and result, cover every check the spawning prompt assigned (the nine named shapes, the
pre-repair regression-class validity check, cross-repo/unresolvable-slug/fire-once re-confirmation, and
the full suite); no further action is planned from this session itself.
