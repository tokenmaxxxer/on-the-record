Subject: issue-576

# Current-state survey

Skip condition: pure bugfix. `_pr_for_branch`'s query already exists and
is queried at exactly one watch-pipeline call site; the fix is narrowing
its `gh pr list` filter, not a new design. Scout is skipped per that
condition (contract v3 scout-directive skip rule).

## Root cause

`spawn.py:1074` `_pr_for_branch(root, branch)`:

```python
r = subprocess.run(["gh", "pr", "list", "--head", branch, "--state", "all",
                    "--json", "number", "-q", ".[0].number"], ...)
```

`--state all` with `.[0].number` returns whichever PR `gh pr list` orders
first for that head branch. Observed ordering across the four
reproductions in the issue put the OLDER (already-merged) PR first, not
the round's newly-opened one — so when a head branch is reused
(`issue-476/product-discovery` round 2 after round 1's PR #479 merged,
etc.), the watch pipeline reports the stale merged PR's number/URL.

Call site (`spawn.py:4372-4381`, inside `_watch`'s per-line loop): a
candidate PR URL `m` is extracted from the session's stdout via
`_PR_URL_RE`, then confirmed against `_pr_for_branch(Path(cwd), br)` —
if `int(m.rsplit("/", 1)[-1]) == pr_number`, a `pr-opened` event fires
with that URL. Because `pr_number` here is memoized per-session
(comment at 4355-4361 explains why: avoid re-invoking `gh` per candidate
URL), a stale merged-PR number, once resolved, silently rejects the
correct new-PR URL for the rest of that session's stream — the new PR's
candidate URL never matches `pr_number` and `pr-opened` never fires for
it (this matches the issue's fourth reproduction: "watch reported #571
... actual new PR was #575" — the wrong number wins the memo and the
right one is simply dropped).

## Existing correct pattern in the same file

`ensure_pushed` (`spawn.py:3991-3997`) already solves this exact class of
bug for its own PR-exists check, with an explicit comment recording the
same past incident (issue #60, phase-2 PR silently skipped because
`gh pr view <branch>` matched phase-1's merged PR):

```python
pr = subprocess.run(["gh", "pr", "list", "--head", br, "--state", "open",
                     "--json", "number", "--jq", "length"], ...)
```

`_merged_pr_for_branch` (`spawn.py:1103`) and
`_pr_open_or_merged_for_branch` (`spawn.py:1082`) are two more
deliberately-scoped variants already living next to `_pr_for_branch`,
each narrowing `--state` for a specific caller's semantics. The
established convention in this file is: one function per needed state
filter, not one function whose callers hope they don't get the wrong
state.

## Call sites of `_pr_for_branch`

- `spawn.py:1225`, inside `approve_scope` — resolves the PR (open OR
  merged) hosting the `scope-approved` comment/approval, so it must keep
  matching `--state all`; approvals can legitimately live on an already-
  merged phase-1 PR. This site must NOT change.
- `spawn.py:4378`, inside `_watch`'s `pr-opened` detection — this is the
  one the issue's acceptance targets. It only ever wants the OPEN PR the
  armed session itself just created; a merged PR of the same branch is
  never the right answer here.

## Test harness

`test_spawn.py`'s `_run` helper (class around line 2203) monkeypatches
`spawn._pr_for_branch` directly via `mock.patch.object(spawn,
"_pr_for_branch", pr_for_branch)` for the whole `_watch` pipeline test
suite (tests at lines 2722-2800 already cover memoization, retry, and
non-PR-URL edge cases against this same seam). Renaming or adding a
function used only at the 4378 call site keeps that harness's patch
point intact only if the new function is what gets patched instead — the
proposal accounts for this in its write set.

## Separate findings requested by the task (stall report / DEAD watcher)

The task also asked to report — not silently fix — any separate findings
on "a stall report while the session had actually completed" and "a DEAD
watcher" observed during the operator's session. Neither of these two
symptoms is described with enough operational detail in issue #576 itself
(no timestamps, no roster/log excerpts, no reproduction steps) to locate
a root cause without speculation. Filing a fix for an unreproduced
symptom under this issue's scope would conflate two different defects
under one PR. This survey records the gap; the proposal below scopes to
the four reproduced pr-opened cases only, and flags the stall/DEAD-
watcher observations back to the user as needing their own issue with
concrete repro evidence (roster entries, watch log excerpts, or
`events.jsonl` lines from the session where it happened) before a fix
can be attempted.
