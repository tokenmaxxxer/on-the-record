---
issue: 2637
role: execution-observation
author: execution-observation
skills: work-in-english (skill-repository), observability-phase-trace (skill-repository(297e350))
verifies_subject: true  # independent re-verification of PR #2643's deliverable, different author
loop_state: landed
code_under_review:
  - path: priorities.py
    sha: 58ff8a6110059ed20fbdcfc6d8ecb263d6adc4ad
  - path: spawn.py
    sha: 58ff8a6110059ed20fbdcfc6d8ecb263d6adc4ad
  - path: on-the-record/hooks/deliverable-guard.sh
    sha: 58ff8a6110059ed20fbdcfc6d8ecb263d6adc4ad
  - path: on-the-record/hooks/product-capture-stopgate.sh
    sha: 58ff8a6110059ed20fbdcfc6d8ecb263d6adc4ad
  - path: on-the-record/hooks/skill-verdict-guard.sh
    sha: 58ff8a6110059ed20fbdcfc6d8ecb263d6adc4ad
type: verification
breaking: none
verdict: pass
upstream:
  - path: docs/issue-2637/reports/architecture-interface-contract-shape+silent-failure-audit-a86b8985.md
    sha: aa152c797e60e6620e8162dec586b97fc8f171e1
  - path: priorities.py
    sha: 58ff8a6110059ed20fbdcfc6d8ecb263d6adc4ad
---
skill-verdict: work-in-english — applied: invoked; this record, commit messages and PR body written in English, final chat summary in Korean
skill-verdict: observability-phase-trace — not-applicable: issue #2637 is a write-path/conflict-elimination change to a docs artifact, not a RED/USE/Golden-Signals observability surface with a phase-1-named methodology to trace against

# issue-2637 — execution-observation record

## What was done

canonical: `gh pr view 2643` output (this session) — result: `{"mergeStateStatus":"CLEAN","mergedAt":null,"state":"OPEN"}`. PR #2643 (`issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985`, tip commit `aa152c797e60e6620e8162dec586b97fc8f171e1`) carries the fix and its own implementation record but had not merged to `main` as of this session.

Independently re-executed all three of issue #2637's acceptance checks against that branch's real code, plus one extra functional check on the before-landing warrant-hunter's anchor-bypass fix.

derived: `git merge --no-ff origin/issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985` (this session, this branch) — result: `Merge made by the 'ort' strategy.` bringing the branch's commits into this `issue-2637/execution-observation` branch so the reviewed files exist in this branch's own working tree; confirmed by `git log --oneline -3 -- priorities.py` (this session) — result: `58ff8a61 issue-2637: shard priorities.md into one-file-per-entry directory` is now an ancestor of this branch.

### Check 1 — two branches from the same base merge without conflict

acceptance: fresh two-branch-merge demo, independent of the implementation record's own demo (different entries and worktree paths), run this session — result:

```
$ git worktree add /tmp/obs2637-a -b obs2637-throwaway-a aa152c79   # entry X, 03:00 timestamp
$ git worktree add /tmp/obs2637-b -b obs2637-throwaway-b aa152c79   # entry Y, 15:00 timestamp
$ git worktree add /tmp/obs2637-int -b obs2637-throwaway-int aa152c79
$ cd /tmp/obs2637-int
$ git merge --no-ff obs2637-throwaway-a -m "obs-demo: merge X"
Merge made by the 'ort' strategy.
 docs/reports/product/priorities/20260827T030000000000-30001.md | 1 +
exit=0
$ git merge --no-ff obs2637-throwaway-b -m "obs-demo: merge Y"
Merge made by the 'ort' strategy.
 docs/reports/product/priorities/20260827T150000000000-30002.md | 1 +
exit=0
$ git status --porcelain
(no output — clean, no unmerged paths)
```

canonical: the transcript above, this session — zero `CONFLICT` lines, exit 0 on both merges, satisfying the acceptance criterion. Cleanup re-verified with fresh output this session:

```
$ git worktree remove /tmp/obs2637-a --force
$ git worktree remove /tmp/obs2637-b --force
$ git worktree remove /tmp/obs2637-int --force
$ git branch -D obs2637-throwaway-a obs2637-throwaway-b obs2637-throwaway-int
obs2637-throwaway-a 브랜치 삭제 (과거 d160872b).
obs2637-throwaway-b 브랜치 삭제 (과거 aa461d45).
obs2637-throwaway-int 브랜치 삭제 (과거 9df70548).
$ git worktree list
/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2637-execution-observation  5f23f894 [issue-2637/execution-observation]
$ git branch --list "obs2637-*"
(no output)
```

Nothing stray left in this checkout.

### Check 2 — chronological order recoverable without a shared file

acceptance: `priorities.read_priorities(None, '.')` run this session inside the merged-together `/tmp/obs2637-int` worktree, immediately after the two merges above — result:

```
num entries: 3
0 '# Priorities\n\nAppend-only, newest entry last.\n\n- 2026-08-12: ...'
1 '- 2026-08-27T03:00:00Z: [OBS entry X, earlier timestamp, merged FIRST]\n'
2 '- 2026-08-27T15:00:00Z: [OBS entry Y, later timestamp, merged SECOND]\n'
```

derived: the transcript above, this session — entry X (filename `20260827T030000000000-30001.md`, earlier timestamp) was merged FIRST into git but sorts as `entries[1]`; entry Y (filename `20260827T150000000000-30002.md`, later timestamp) was merged SECOND but sorts as `entries[2]`. Filename-timestamp order, not git-merge order, drives the output, matching `priorities.py`'s `sorted(d.glob("*.md"))` reader (`priorities.py:117-118`, quoted in full below):

```python
    d = _priorities_dir(issue, cwd)
    if d.is_dir():
        entries.extend(p.read_text(encoding="utf-8") for p in sorted(d.glob("*.md")))
    return entries
```

The legacy `docs/reports/product/priorities.md` block always appears first (`entries[0]` in the transcript above), matching `read_priorities()`'s own module docstring.

### Check 3 — every consumer of `priorities.md` still works

canonical: `git grep -l "priorities.md" HEAD` (this session, this branch, post-merge) — result: 29 files, four more than the implementation record's own 25-file count. derived: diffing this session's 29-file list against the implementation record's own 25-entry table (this session) — the four new hits are `docs/issue-2637/reports/architecture-interface-contract-shape+silent-failure-audit-a86b8985.md`, `priorities.py`, `spawn.py`, and `on-the-record/hooks/product-capture-stopgate.sh` — this PR's own new/changed files, which now themselves contain the literal string `"priorities.md"` in prose or comments. No missed external consumer.

Re-ran the code-consumer functional checks directly against `on-the-record/hooks/*.sh` in isolated throwaway repos, independently of the implementation record's own transcripts:

acceptance: `deliverable-guard.sh` invoked with synthetic PreToolUse payloads, `TOKENMAXXXER_SPAWNED` unset to reach the orchestrator code path — result:

```
$ env -u TOKENMAXXXER_SPAWNED bash -c '... file_path=src/docs/reports/product/priorities/hack.md ... | bash on-the-record/hooks/deliverable-guard.sh; echo "bypass exit: $?"'
orchestrate: this is an orchestrator session and src/docs/reports/product/priorities/hack.md is a deliverable path in a board repo. ...
bypass exit: 2
$ env -u TOKENMAXXXER_SPAWNED bash -c '... file_path=src/foo.py ... | bash on-the-record/hooks/deliverable-guard.sh; echo "src exit: $?"'
orchestrate: this is an orchestrator session and src/foo.py is a deliverable path in a board repo. ...
src exit: 2
$ env -u TOKENMAXXXER_SPAWNED bash -c '... file_path=docs/reports/product/priorities/20990101T000000000000-1.md ... | bash on-the-record/hooks/deliverable-guard.sh; echo "shard exit: $?"'
shard exit: 0
```

None of the three `file_path` values above (untracked, synthetic — they exist only as a field inside a `PreToolUse` JSON payload string, never written to disk in this or any repo) are real files. Confirms the anchored `PRODUCT_CAPTURE_PRIORITIES_DIR_RE` regex fix — the `src/`-rooted bypass path is denied (exit 2), a genuine shard path is exempt (exit 0). derived: a first attempt at this same check with `TOKENMAXXXER_SPAWNED=1` still set (this observer session's own ambient env, not unset) returned exit 0 for every payload including the plain `src/foo.py` write — a false "everything passes" read caused by testing the wrong code path (a spawned-role session, not an orchestrator session), not a defect in the guard; corrected by unsetting the variable as shown above.

acceptance: `product-capture-stopgate.sh` run in a fresh isolated `mktemp -d` git repo with a real JSONL transcript containing a Korean priorities-anchor sentence (`우선순위가 더 중요합니다`) — result:

```
=== before entry exists ===
{"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": "product-capture-stopgate: statements matching these categories were not reflected in docs/reports/product/: priorities/ (spawn.py priorities-path; e.g. \"우선순위가 더 중요합니다\"). Record them as structured entries before ending the turn."}}
=== after untracked shard exists ===
(no output, rc=0)
```

Nudges before a shard exists, goes silent once one does, matching the implementation record's claim about the new `git status --porcelain` untracked-file fallback.

derived: a first attempt at this check used a single-line JSON array (`[{"type":"user",...}]`) as the transcript file instead of JSONL (one JSON object per line), and produced no nudge at all in either state — a false negative, not a hook defect. Root cause reproduced directly:

```
$ python3 -c "import json; print(isinstance(json.loads('[{\"type\":\"user\"}]'), dict))"
False
```

The hook's transcript reader calls `json.loads(line)` once per line and only processes `dict` results (tool-result entries are also `type:"user"` but carry structured, non-authored content and must be skippable the same way) — a whole-array transcript line parses to a `list`, so every line was silently skipped. Fixed by writing one JSON object per line; reproduced correctly above.

`skill-verdict-guard.sh`'s diff is wording-only (adds a `priorities is sharded per entry since issue #2637` clause to the obligations-reminder string) — canonical: `git show 58ff8a61 -- on-the-record/hooks/skill-verdict-guard.sh` (this session), 3-line diff, no logic path changed — so no functional re-test was needed beyond the diff read.

derived: `python3 -m py_compile priorities.py spawn.py` (this session) — result: exit 0, both compile clean.

## Why

Execution-observation's job is independent re-verification of a landed/landing deliverable, not re-summarizing the implementer's own transcript. All three checks above were re-run against the real branch code with fresh, independently chosen inputs (different demo timestamps, a fresh isolated git repo for the Stop-hook test) so a mistake in the implementation record's own transcript would not simply be echoed back here.

## What did not work

Two dead ends in this session's own testing, both self-corrected before being reported in Check 3 above:

- First `deliverable-guard.sh` run left `TOKENMAXXXER_SPAWNED=1` set, which no-ops the guard entirely (it only gates orchestrator sessions) — misread as "guard does nothing" until re-run with `env -u TOKENMAXXXER_SPAWNED` (see Check 3's `deliverable-guard.sh` block above).
- First `product-capture-stopgate.sh` run wrote the synthetic transcript as a JSON array instead of JSONL, so every line silently failed the reader's `isinstance(entry, dict)` check. derived: reproduced this session —

```
$ python3 -c "import json; print(isinstance(json.loads('[{\"type\":\"user\"}]'), dict))"
False
```

  (see Check 3's `product-capture-stopgate.sh` block above for the full root-cause writeup) — misread as "the hook is broken" until the transcript format was fixed.

## Upstream basis

- `docs/issue-2637/reports/architecture-interface-contract-shape+silent-failure-audit-a86b8985.md` (sha `aa152c797e60e6620e8162dec586b97fc8f171e1`) — the implementation record this session cross-checked against, read in full.
- `priorities.py` (sha `58ff8a6110059ed20fbdcfc6d8ecb263d6adc4ad`) — the reader/writer module whose ordering and no-loss behavior this session re-verified directly.
- PR #2643 (`gh pr view 2643`, canonical, this session) — the delivery vehicle for issue #2637; still open (`state: OPEN`, `mergedAt: null`) as of this record.

## Open findings

None. All three acceptance checks reproduced independently this session with results matching the implementation record's claims; the one prior finding (anchor-bypass in `deliverable-guard.sh`) was independently re-confirmed fixed, not just read as claimed.

## Next steps

derived: `python3 -m py_compile priorities.py spawn.py && git log --oneline -1 -- priorities.py` (this session, re-run at close of this record) — result:

```
58ff8a61 issue-2637: shard priorities.md into one-file-per-entry directory
```

(compile succeeded silently, exit 0; the `git log` line above confirms the file this record reviewed is still the same commit cited throughout.) This record's own verification work is complete — every acceptance check in Check 1/2/3 above ran live this session with output matching the implementation record's claims. PR #2643 is the code delivery vehicle and remains the responsibility of its own review/merge path; nothing further is queued behind this observation.
