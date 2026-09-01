---
issue: 2962
role: independent-verification-1
author: independent-verification-1
verifies_subject: true
kind: verify-record
loop_state: cleared
upstream:
  - path: 57fab5bd6fd4164b6ae943a9a6ef2d5000035150:docs/issue-2962/reports/silent-failure-audit+test-derivation-167b9a63.md
    sha: 57fab5bd6fd4164b6ae943a9a6ef2d5000035150
  - path: 57fab5bd6fd4164b6ae943a9a6ef2d5000035150:on-the-record/hooks/hook_classification.json
    sha: 57fab5bd6fd4164b6ae943a9a6ef2d5000035150
---

# issue-2962 — independent-verification-1 record

## What was done

Independently audited PR #2966 (branch `issue-2962/silent-failure-audit+test-derivation-167b9a63`, head `57fab5bd6fd4164b6ae943a9a6ef2d5000035150`) — the deliverable for this subject — against the issue's 5 acceptance checks and its `must not` list, rather than trusting the PR's own claimed results.

canonical: `gh pr view 2966` output (state: OPEN, mergeable: MERGEABLE, files: 12 changed)

Checked out the PR head in an isolated `git worktree` at `/tmp/pr2966-review` (removed after the audit) and re-ran every check the issue names myself:

acceptance: `python3 -m pytest on-the-record/hooks/ -k hook_classification -q` — result:
```
6 passed in 0.82s
```
acceptance: `python3 -m pytest on-the-record/hooks/ -k visible_fail_open -q` — result:
```
6 passed in 0.98s
```
acceptance: `python3 -m pytest on-the-record/hooks/ -k notice_no_external_dependency -q` — result:
```
3 passed in 0.81s
```
acceptance: `python3 -m pytest on-the-record/hooks/ -k heredoc_failure_bails -q` — result:
```
5 passed in 0.81s
```
acceptance: `python3 -m pytest on-the-record/hooks/ -k fail_open_ledger_fields -q` — result:
```
5 passed in 0.87s
```
acceptance: `python3 -m pytest on-the-record/checks/ on-the-record/hooks/ -q` — result:
```
29 passed in 1.01s
```

All 6 runs match the PR body's claimed counts exactly (25 across the 5 acceptance `-k` filters, 29 for the combined regression run) — reproduced independently, not taken on the PR author's word.

Beyond re-running tests, read the actual diff for each changed file (`git diff origin/main HEAD` inside the worktree) and cross-checked it against the issue's acceptance criteria and `must not` list, one item at a time:

canonical: `git diff origin/main HEAD -- on-the-record/hooks/hook_classification.json` and `on-the-record/hooks/hooks.json`, read directly in the worktree this session

- **Classification data matches wiring.** `57fab5bd6fd4164b6ae943a9a6ef2d5000035150:on-the-record/hooks/hook_classification.json` lists 12 registrations. Counted `on-the-record/hooks/hooks.json` directly: `SessionStart`×2, `UserPromptSubmit`×1, `PreToolUse`×2, `PostToolUse`×4, `Stop`×3 = 12, and the two lists match name-for-name — derived: manual JSON read of both files, worktree session — result: 12/12 matched, including `pretooluse-dispatcher.sh` marked `wrapped: false`.
- **`fail-open-wrapper.sh` notice mechanism** — canonical: `git diff origin/main HEAD -- on-the-record/hooks/fail-open-wrapper.sh` (+28/-1). A `case "$_hook_name" in session-role-bind.sh|directive.sh|post-landing-obligation-gate.sh|stop-gate.sh|skill-verdict-guard.sh)` block prints a `[fail-open][DEGRADED] ...` `printf` line before the pre-existing python3/disk-dependent ledger call, using only shell builtins (`case`, `printf`). `pretooluse-dispatcher.sh` is correctly absent from this `case` list — it is classified invariant-injecting but `wrapped: false`, so it never reaches this wrapper, matching its deliberate fail-closed posture. Hooks not in the list fall through the `case` default (`*) ;;`) with no notice, unchanged from before.
- **Heredoc-cascade fix** — canonical: `git diff origin/main HEAD -- on-the-record/hooks/stop-gate.sh on-the-record/hooks/skill-verdict-guard.sh on-the-record/hooks/post-landing-obligation-gate.sh`. In each of the 3 registered hooks using the `IFS='' read -r -d '' VAR <<'PY' || true` shape, the variable is now pre-initialized (`CHECK=""` / `GUARD=""`) immediately before the heredoc and the hook bails with `exit 1` immediately after if the variable came back empty — before ever reaching `python3 -c "$VAR"`. `exit 1` is the same code the old `set -u` cascade already produced — derived: `bash -c 'set -u; unset VAR; printf "%s" "$VAR"; echo $?'` on this session's own shell — result: exits `1`, `unbound variable`. So this is a "fail cleanly instead of noisily" fix, not a new fail-closed posture: no hook that was fail-open before is fail-closed now, and all 3 stay wrapped by `fail-open-wrapper.sh`.
- **Ledger fields** — canonical: `git diff origin/main HEAD -- on-the-record/hooks/hook_ledger.py`. `record_fail_open()` gained `fallback_fired: bool` as its own JSON field, alongside the pre-existing `exit_code`, never merged into a string; `fail-open-wrapper.sh` passes `"$_fallback_fired"` as a new positional CLI arg, and `hook_ledger.py`'s `sys.argv` parsing was reindexed to match (`_fallback = sys.argv[4]`, `_argv = sys.argv[5:]`).
- **`must not` list** — canonical: `git diff origin/main HEAD -- on-the-record/hooks/pretooluse-dispatcher.sh` — result: empty diff (file untouched by this PR). No hook's fail-open default was tightened to fail-closed (verified above). The notice path is `printf`+`case` only, positioned before any python3/subprocess call. The notice text is a distinct literal (`[fail-open][DEGRADED] ...`), not the raw traceback — canonical: `on-the-record/hooks/fail-open-wrapper.sh` diff, same read.
- Spot-read `57fab5bd6fd4164b6ae943a9a6ef2d5000035150:on-the-record/hooks/test_visible_fail_open.py` (worktree, this session) to check the new tests exercise real behavior rather than tautologies: `_run_wrapper()` shells out via `subprocess.run([WRAPPER, hook_path], ...)` against a fixture hook script written to a tempdir, and assertions check the subprocess's captured stdout for the `NOTICE_MARKER` string — a behavioral assertion against the real wrapper script, not a mock.

`57fab5bd6fd4164b6ae943a9a6ef2d5000035150:docs/issue-2962/reports/silent-failure-audit+test-derivation-167b9a63.md` cites the same commands and counts reproduced above; this session's own independent runs corroborate those claims rather than merely repeating them — canonical: pytest output blocks above, executed this session in the isolated worktree.

## Why

Independent verification per `docs/handbooks/observer-verification.md` means re-executing the acceptance evidence rather than trusting the subject's own record, and reading the diff against the issue's stated constraints rather than trusting the PR description's summary of itself.

acceptance: `python3 -m pytest on-the-record/hooks/ -k hook_classification -q && python3 -m pytest on-the-record/hooks/ -k visible_fail_open -q && python3 -m pytest on-the-record/hooks/ -k notice_no_external_dependency -q && python3 -m pytest on-the-record/hooks/ -k heredoc_failure_bails -q && python3 -m pytest on-the-record/hooks/ -k fail_open_ledger_fields -q` — result:
```
6 passed in 0.82s
6 passed in 0.98s
3 passed in 0.81s
5 passed in 0.81s
5 passed in 0.87s
```
All 5 issue-named acceptance checks pass on independent re-run, and the diff audit in "What was done" found no violation of the `must not` list — `verifies_subject: true` set on that basis.

## What did not work

None.

## Upstream basis

- `57fab5bd6fd4164b6ae943a9a6ef2d5000035150:docs/issue-2962/reports/silent-failure-audit+test-derivation-167b9a63.md` (PR #2966's own deliverable record) — sha `57fab5bd6fd4164b6ae943a9a6ef2d5000035150` (PR head; not present on this branch's own worktree, cited commit-fixed).
- `57fab5bd6fd4164b6ae943a9a6ef2d5000035150:on-the-record/hooks/hook_classification.json`, `fail-open-wrapper.sh`, `hook_ledger.py`, `stop-gate.sh`, `skill-verdict-guard.sh`, `post-landing-obligation-gate.sh` — same sha, all read directly this session via `git diff origin/main HEAD -- <path>` in an isolated worktree at `/tmp/pr2966-review` (removed after the audit; not present in this branch's own worktree).

## Open findings

None.

## Next steps

None — loop_state is terminal (`cleared`).

skill-verdict: work-in-english — applied: invoked; wrote this record, the commit message, and the PR body in English per the skill, reserving Korean for the end-of-turn summary to the user.
other mounted skills: not triggered
