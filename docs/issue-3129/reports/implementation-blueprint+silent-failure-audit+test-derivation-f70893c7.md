---
issue: 3129
role: implementation-blueprint+silent-failure-audit+test-derivation-f70893c7
author: implementation-blueprint+silent-failure-audit+test-derivation-f70893c7
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: on-the-record/hooks/amendment_channel.py, on-the-record/hooks/hook_input.py, tests/test_amendment_channel.py, gates/probe_running_session_sees_amendment.py, gates/probe_amendment_notice_fires_once.py
type: implementation-record
breaking: true
verdict: seam-redesigned-command-text-no-longer-parsed-for-repo, cross-repo-edit-fails-closed-as-policy-violation, no-registration-fails-closed-not-silent, multi-repo-session-support-does-not-exist-today-therefore-broken-by-design, exit-code-masked-by-preexisting-shell-wrapper-stderr-still-forwarded
loop_state: landed
upstream:
  - path: docs/issue-3129/reports/adversarial-review+silent-failure-audit+test-depth-audit-e93e7a3b.md
    sha: ca58cd7f0bb8b81bdb83dbe1fbac85762843cf5a
  - path: on-the-record/hooks/amendment_channel.py
    sha: 28e8e63fdee55b8c2b81ed49110e6ad9303f1cc8
  - path: on-the-record/hooks/hook_input.py
    sha: 10f70859049c759b7dc53634459871be6914d7a6
  - path: tests/test_amendment_channel.py
    sha: 09b768e431288df2f5e1a0c46b118d1e65b04db2
  - path: gates/probe_running_session_sees_amendment.py
    sha: 9fb4a4769f39944c859ab7cc3e5b0a8f57dee3f1
  - path: gates/probe_amendment_notice_fires_once.py
    sha: 9fb4a4769f39944c859ab7cc3e5b0a8f57dee3f1
---

# issue-3129 — implementation-blueprint+silent-failure-audit+test-derivation-f70893c7 record

Note on paths below: `on-the-record/hooks/amendment_channel.py`, `on-the-record/hooks/hook_input.py`, `on-the-record/hooks/amendment-channel.sh`, `tests/test_amendment_channel.py`, and both `gates/probe_*.py` files are untracked in THIS checkout (this session's own branch carries only this record) -- all code changes described below were made and committed on PR #3137's branch (`issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`) in a separate worktree, per the "Branch topology" section. Every commit sha cited is real and resolves on that branch.

## What was done

Repair round 4 on the amendment channel's WRITE side: deleted the command-text repo-attribution parser entirely (`target_repo_for_command()`, `_explicit_repo_flag()`, and their regexes) and replaced it with a seam that never reads the `gh issue edit` command text for a repo at all.

New design, implemented in `record_amendment_from_response()` (commit `28e8e63fdee55b8c2b81ed49110e6ad9303f1cc8`):

1. This session's own REGISTERED repo comes from `repo_slug_for_cwd()` applied to the `PostToolUse` payload's own top-level `cwd` field -- the directory `spawn.py` launched this process into. `spawn.py`'s own registration call is:
   ```python
           roster_register(roster_key, {
               "pid": proc.pid, "skill": skill,
               "issue": issue, "ts": int(time.time()),
               "work": str(cwd), "log": str(log_path),
   ```
   derived: `grep -n 'roster_register(roster_key' spawn.py` on PR #3137's branch checkout at `/tmp/pr3137-work` -- 2 call sites (the fork-child early stub and this post-`Popen` registration), both writing a single `"work": str(cwd)` key.
2. The actual edited issue's repo+number comes from `gh issue edit`'s own success output (`https://github.com/<owner>/<repo>/issues/<n>`), read from the `PostToolUse` payload's `tool_response` field via a new shared helper, `hook_input.tool_response_text()` (commit `10f70859049c759b7dc53634459871be6914d7a6`), and a new regex, `_issue_url_from_response()`.
3. Command text is consulted for exactly one thing now: `_gh_issue_edit_body_call()` decides whether a Bash call is a `gh issue edit ... --body...` invocation at all (a shape gate, never an attribution parse).

Logic: registered repo == URL repo -> write the marker keyed to the URL's own issue number (never a number lifted from the command text). Registered repo != URL repo -> `RepoMismatch`: no marker, one stderr line naming both repos, `main()` returns nonzero. No URL in `tool_response` -> `NoIssueUrlInResponse`: same fail-closed shape. No resolvable registered repo at all (`repo_slug_for_cwd(cwd)` is `None`) -> `NoRegisteredRepo`: same fail-closed shape -- this is also the path a session started outside `spawn.py` takes, since there is no separate "was this registered" bit to check apart from whether `cwd`'s own git origin resolves.

Test suite (commit `09b768e431288df2f5e1a0c46b118d1e65b04db2`): deleted the three shape-enumeration test classes and added three replacements.
```
$ git show d582459c:tests/test_amendment_channel.py | grep -c '    def test_'
66
$ git show 9fb4a476:tests/test_amendment_channel.py | grep -c '    def test_'
65
```
derived: both commands above, run this session in `/tmp/pr3137-work` (both commits reachable in this same repo's object database via the worktree) -- net -1 (19 test methods deleted across `WriterSideTargetsCommandNotSessionCwd`=3, `WriterSideParserHandlesRealCommandShapes`=12, `ShapesFailAgainstPreRepairCommit`=4; 18 added across `RecordAmendmentFromResponse`=7, `PreviouslyBrokenShapesAreNowIrrelevant`=6, `MainExitCodeReflectsWriteOutcome`=5 -- per-class counts via a `python3` regex scan of both blobs, run this session).

The three deleted classes asserted specific `cd`/`--repo`/heredoc/subshell command shapes parsed correctly. The three added classes: `RecordAmendmentFromResponse` (repo-match / repo-mismatch / no-url / empty-response / None-response / no-registered-repo, all driven by `tool_response` fixtures), `PreviouslyBrokenShapesAreNowIrrelevant` (PR #3170's own 5 un-enumerated shapes -- `pushd`, a quoted `cd` path with a space, a subshell wrapping only `gh`, `--repo=` before the issue number, `GH_REPO=` env prefix -- reproduced as command-text fixtures wrapped with a normal `tool_response`, each now trivially `AmendmentWritten`), and `MainExitCodeReflectsWriteOutcome` (invokes `amendment_channel.py` as a real subprocess and asserts its own exit code and stderr for each fail-closed outcome).

## Why

canonical: `docs/issue-3129/reports/adversarial-review+silent-failure-audit+test-depth-audit-e93e7a3b.md` (untracked in this checkout; merged to main as PR #3170, sha `ca58cd7f0bb8b81bdb83dbe1fbac85762843cf5a`) own summary line, quoted verbatim: "5 of 9 [un-enumerated command shapes] Incorrect -- two silent cwd-fallbacks ... and three total silent misses with zero stderr". Three rounds each closed the shapes that round's own verification found and left the next round's finder something new.
derived: `git log --oneline --all -- on-the-record/hooks/amendment_channel.py` in `/tmp/pr3137-work`, showing `28e8e63f` (this round), `d582459c`, `f20da852`, `7957bda7`, `bedd1c72`, `0eb2daf8`, `57987dd6`, `b0fddeaf`, `7d951975`, `a0abb72d` as the full repair chain on that branch.

The implementation-blueprint consult for this round (`/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/consult-logs/20260902T125114834311-932182.log`) recommended changing the seam instead of adding shapes: trust what `spawn.py` registered for the session, treat an edit outside that repo as a policy violation rather than something to parse around, and fail closed (not skip) when the repo cannot be determined.
canonical: consult log's own `"answer"` field, quoted verbatim: "(c) spawn.py가 세션에 등록한 target repo(들)를 신뢰 소스로 삼고, gh 명령 텍스트 파싱은 완전히 폐기한다... repo를 결정할 수 없으면 skip이 아니라 fail-closed marker(unresolved 상태로 기록)를 남긴다." -- and its `"caveats"` field, which names both caveats investigated below.

`gh issue edit`'s own success output already reports exactly which issue it edited -- parsing that structured, tool-authored fact is a bounded problem (one URL shape), unlike parsing arbitrary shell text for user intent (open-ended shell grammar).

## What did not work

None.

## Branch topology

Investigated before touching anything, per this round's instruction.

```
$ gh pr view 3137 --json headRefName,state,url
{"headRefName":"issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019","state":"OPEN","url":"https://github.com/tokenmaxxxer/on-the-record/pull/3137"}
```
canonical: the `gh pr view 3137` output above, run this session -- a DIFFERENT branch than this session's own `issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-f70893c7`.

```
$ git ls-tree -r origin/issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019 --name-only | grep -iE 'amendment|hook_input'
gates/probe_amendment_notice_fires_once.py
gates/probe_running_session_sees_amendment.py
on-the-record/hooks/amendment-channel.sh
on-the-record/hooks/amendment_channel.py
on-the-record/hooks/hook_input.py
tests/test_amendment_channel.py
```
canonical: the `git ls-tree` output above, run this session against the fetched branch -- confirming all the amendment-channel files live on PR #3137's branch, not on this session's own branch.

This is the two-branch case: code changes were made in a separate worktree (`git worktree add /tmp/pr3137-work issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`), committed there in 4 incremental commits, and pushed to that same branch.

```
$ git push origin issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019
   d582459c..9fb4a476  issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019 -> issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019
```
canonical: the `git push` output above, run this session -- fast-forwarded `d582459c..9fb4a476`, not merged, `main` untouched. This record itself lands as a commit on this session's own branch, not on PR #3137's branch.

## Caveat 1 — sessions with more than one legitimate target repo

Investigated `roster_register()`'s call sites in `spawn.py` (untracked in this checkout; read on PR #3137's branch worktree, unmodified this round). Both the fork-child early-registration stub and the main post-`Popen` registration write exactly one `work` field per roster entry, never a list:

```python
        roster_register(roster_key, {
            "pid": proc.pid, "skill": skill,
            "issue": issue, "ts": int(time.time()),
            "work": str(cwd), "log": str(log_path),
```
derived: `grep -n 'roster_register(roster_key' spawn.py` in `/tmp/pr3137-work` -> 2 matches, both entry literals containing a singular `"work": str(cwd)` key and no list/set field anywhere in either literal.

`spawn.py` today registers exactly ONE workspace/repo per session -- not a hypothetical, this is what the actual `roster_register()` call sites write. This redesign's "same repo as registered, else policy violation" rule therefore cannot distinguish "an edit landed in the wrong repo by mistake" from "this orchestrator legitimately edits a second repo's issues from one session" -- both look identical (`RepoMismatch`) from inside `amendment_channel.py`. This IS a real regression relative to repair rounds 2/3's cd-based targeting, which explicitly supported and tried to correctly attribute exactly this pattern (round 2's own worked example: an `on-the-record` session `cd`-ing into a `study-companion` checkout to edit that repo's issues). This round's own mandate explicitly requires this tradeoff ("An edit that lands outside the registered repo is a POLICY VIOLATION... fail closed"), so it is not an accidental regression, but it is a real, currently-live capability the new design cannot serve until `spawn.py`'s registration schema is extended from one repo to a set.

## Caveat 2 — sessions not started through spawn.py (no registration)

There is no separate "was this session registered" bit anywhere in this design -- a session's registered repo IS `repo_slug_for_cwd(cwd)`, so "never registered" and "registered to an unresolvable repo" are the same code path (`NoRegisteredRepo`), and both fail closed: no marker, one stderr line, `main()` returns nonzero. Verified with a real test, not asserted in prose only:

```python
    def test_no_registered_repo_is_fail_closed_not_skip_silently(self):
        """issue #3129 round-4 caveat 2: a session with no resolvable
        registered repo (not started through spawn.py, or `cwd` is not a
        git checkout at all) must fail CLOSED -- no marker, loud stderr --
        never skip silently as if amendments simply don't apply here."""
```
canonical: `tests/test_amendment_channel.py` (untracked in this checkout; commit `09b768e431288df2f5e1a0c46b118d1e65b04db2` on PR #3137's branch), class `RecordAmendmentFromResponse`, method `test_no_registered_repo_is_fail_closed_not_skip_silently` -- asserts `isinstance(result, ac.NoRegisteredRepo)`, that no marker file exists, and that `_report_write_result()` writes a stderr line containing "registered repo". A companion method in `MainExitCodeReflectsWriteOutcome`, `test_no_registered_repo_exits_nonzero_with_stderr`, drives the same case through the real `amendment_channel.py` subprocess entrypoint and checks the actual process exit code. Both are part of `tests/test_amendment_channel.py`'s suite; see the "Acceptance checks" section below for the full-suite run rather than a narrow, cherry-pickable single-test citation here.

### Is this path silent in a real running session? (investigated, not asserted)

Traced the real shipped hook chain rather than guessing.
```
$ grep -n amendment-channel on-the-record/hooks/hooks.json
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/fail-open-wrapper.sh ${CLAUDE_PLUGIN_ROOT}/hooks/amendment-channel.sh"
```
canonical: `on-the-record/hooks/hooks.json` (untracked in this checkout; read on PR #3137's branch worktree, unmodified this round) -- every live invocation goes through `fail-open-wrapper.sh` first, not `amendment-channel.sh` directly.

Ran the real chain end to end with a manufactured `RepoMismatch` payload:
```
$ echo "$PAYLOAD" | on-the-record/hooks/fail-open-wrapper.sh on-the-record/hooks/amendment-channel.sh
amendment-channel: POLICY VIOLATION -- gh issue edit #42 landed in acme/OTHERREPO but this session is registered to acme/widgets -- no marker written (an edit outside a session's own registered repo is refused, never silently attributed)
wrapper's own exit code observed by caller: 0
```
canonical: manual `fail-open-wrapper.sh`/`amendment-channel.sh` invocation this session, `PAYLOAD` built with `tool_response` naming a different repo (`acme/OTHERREPO`) than the fixture checkout's own `origin` (`acme/widgets`) -- reproducible with any `RepoMismatch`-shaped payload.

Two things are both true, and point opposite directions:
- The stderr line IS forwarded, not lost.
  ```
  $ sed -n '44,46p' on-the-record/hooks/fail-open-wrapper.sh
      "$@" <"$_in_file" 2>"$_err_file"
      rc=$?
      cat "$_err_file" >&2 2>/dev/null || true
  ```
  derived: the fence above, run this session in `/tmp/pr3137-work` -- `cat "$_err_file" >&2` runs unconditionally after the child process exits, regardless of `rc`.
- `amendment_channel.py`'s new nonzero exit code from `main()` NEVER reaches this repo's automated fail-open ledger, because `amendment-channel.sh` itself (unmodified this round, out of this round's file scope) ends unconditionally with:
  ```
  $ tail -5 on-the-record/hooks/amendment-channel.sh
  DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
  command -v python3 >/dev/null 2>&1 || exit 0

  python3 "$DIR/amendment_channel.py"
  exit 0
  ```
  derived: the fence above, run this session in `/tmp/pr3137-work` -- so `fail-open-wrapper.sh`'s own `rc=$?` (captured immediately after `"$@" <"$_in_file" 2>"$_err_file"`) is always `0` for this hook regardless of what `amendment_channel.py` returned. The ledger's other trigger -- `grep -q 'Traceback (most recent call last)' "$_err_file"` -- also does not fire, since the diagnostic lines are not a Python traceback.
  ```
  $ grep -n '_fallback_fired' on-the-record/hooks/fail-open-wrapper.sh
  ```
  derived: the command above, run this session in `/tmp/pr3137-work` -- shows the allowlist `session-role-bind.sh|directive.sh|post-landing-obligation-gate.sh|stop-gate.sh|skill-verdict-guard.sh`, which does not include `amendment-channel.sh`, so even a genuine crash of this hook produces no in-band `[fail-open][DEGRADED]` notice today.

Verdict: NOT silent in the sense of "the text is discarded" (it is not, confirmed above); but effectively silent in the sense of "nothing in this repo's own automated failure-surfacing machinery (the fail-open ledger, the DEGRADED in-band notice) reacts to it" -- a human or tool would have to be separately grepping raw hook stderr for this module's own text. This is a pre-existing property of `amendment-channel.sh`'s own unconditional `exit 0`.
```
$ git show f20da852:on-the-record/hooks/amendment-channel.sh | tail -3
python3 "$DIR/amendment_channel.py"
exit 0
```
derived: the fence above, run this session in `/tmp/pr3137-work` -- the identical unconditional `exit 0` predates this round's commits (present at round-3 tip `f20da852`, for the unresolvable-repo/unwritable-state-dir stderr lines that already existed there), so this is not a new regression this round introduces. Changing `amendment-channel.sh`'s own exit-code contract or `fail-open-wrapper.sh`'s allowlist was out of this round's file scope (`amendment_channel.py`/`hook_input.py` only).

## Upstream basis

- `docs/issue-3129/reports/adversarial-review+silent-failure-audit+test-depth-audit-e93e7a3b.md` (sha `ca58cd7f0bb8b81bdb83dbe1fbac85762843cf5a`, merged as PR #3170, untracked in this checkout). canonical: this file's own body, quoted verbatim in the "Why" section above -- the 5 un-enumerated command shapes this round's redesign makes irrelevant.
- `/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/consult-logs/20260902T125114834311-932182.log`. canonical: this file's own `"answer"`/`"caveats"` JSON fields, quoted verbatim in the "Why" section above -- the implementation-blueprint consult that recommended the registered-repo/policy-violation/fail-closed design.
- `spawn.py`, `roster.py` (read-only this round, not modified; untracked in this checkout, read on PR #3137's branch worktree). canonical: `grep -n 'roster_register(roster_key' spawn.py` output, quoted in "Caveat 1" above -- the `roster_register()` call sites cited there.
- `on-the-record/hooks/fail-open-wrapper.sh`, `on-the-record/hooks/amendment-channel.sh` (read-only this round, not modified; untracked in this checkout). canonical: the fenced `sed`/`tail`/`grep` output quoted in "Caveat 2" above -- the ledger-masking mechanics cited in that investigation.

## Skill verdicts

- skill-verdict: silent-failure-audit — applied: invoked via the Skill tool against the new/changed error-handling paths in `record_amendment_from_response`, `_report_write_result`, `_issue_url_from_response`, `run_hook`/`_run_hook_full`, `main`, and `hook_input.tool_response_text`; the fail-open-wrapper.sh/amendment-channel.sh masking finding in Caveat 2's investigation above was traced by hand afterward (real commands, real output, quoted there), not left as the sub-agent's own unverified summary.
- skill-verdict: test-derivation — applied: used to decide the equivalence-partition shape for `RecordAmendmentFromResponse` (match / mismatch / no-URL / empty-response / None-response / no-registered-repo) over `WriteResult`'s own variants rather than an ad hoc list of cases.
- skill-verdict: implementation-blueprint — applied: invoked for this round's own consult, cited above (`.../consult-logs/20260902T125114834311-932182.log`), which shaped the registered-repo/tool_response/fail-closed seam before any code was written.
- skill-verdict: test-authoring-isolation-and-fixture-strategy — not-applicable: fixtures here are the same per-test `tempfile.TemporaryDirectory()`-scoped real git checkouts the existing suite already used before this round -- no shared state, no new isolation question raised by moving from command-text to tool_response fixtures.
- skill-verdict: work-in-english — applied: this task's dispatch arrived with Korean framing (the implementation-blueprint consult log's own `answer`/`caveats` fields are in Korean); all code, tests, commit messages, and this record are written in English.

## Open findings

- Caveat 1 (multi-repo sessions) — open, not resolved this round: `spawn.py`'s roster schema needs a set-of-repos field before a session can legitimately target more than one repo under this design. No code change proposed here; documented as a known gap.
- Caveat 2's ledger-visibility gap — open, not resolved this round: `amendment-channel.sh`'s own unconditional `exit 0` and its absence from `fail-open-wrapper.sh`'s `_fallback_fired` allowlist both predate this round and are out of this round's file scope. A future round could either propagate `amendment_channel.py`'s real exit code through `amendment-channel.sh` (weighed against every other hook's shared "PostToolUse must never block" contract) or add `amendment-channel.sh` to the allowlist for an in-band DEGRADED notice.

## Acceptance checks (all run for real, this session, in /tmp/pr3137-work at commit 9fb4a4769f39944c859ab7cc3e5b0a8f57dee3f1)

```
$ python3 -m pytest tests/test_amendment_channel.py -q
65 passed in 0.96s
```
canonical: `python3 -m pytest tests/test_amendment_channel.py -q` output (65 passed in 0.96s)
Acceptance requirement met — checked: `python3 -m pytest tests/test_amendment_channel.py -q` — result: 65 passed

```
$ python3 gates/probe_running_session_sees_amendment.py; echo $?
ok
0
```
canonical: `python3 gates/probe_running_session_sees_amendment.py` output (ok, exit 0)
Acceptance requirement met — checked: `python3 gates/probe_running_session_sees_amendment.py` — result: ok, exit 0

```
$ python3 gates/probe_amendment_notice_fires_once.py; echo $?
ok
0
```
canonical: `python3 gates/probe_amendment_notice_fires_once.py` output (ok, exit 0)
Acceptance requirement met — checked: `python3 gates/probe_amendment_notice_fires_once.py` — result: ok, exit 0

```
$ python3 -m pytest tests/ -q
319 passed, 2 warnings in 13.58s
```
canonical: `python3 -m pytest tests/ -q` output (319 passed, 2 warnings in 13.58s -- both warnings from `test_skill_candidates_floor.py`'s pre-existing `SkillCandidatesPinnedFixtureDivergenceTest`, issue #3019, a file untouched by this round's commits, not failures)
Acceptance requirement met — checked: `python3 -m pytest tests/ -q` — result: 319 passed, 2 warnings (pre-existing, unrelated)

All four acceptance requirements above are met — Closes #3129 (the write-side seam this round targeted is fully redesigned and tested; both caveats above are documented, investigated design limitations the round's own mandate anticipated, not failing acceptance criteria).

## Next steps

None — `loop_state: landed`. Both open findings above are candidates for a future round, not blockers for this one.
