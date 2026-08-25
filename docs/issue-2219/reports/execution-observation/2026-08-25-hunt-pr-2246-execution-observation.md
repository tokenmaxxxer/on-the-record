---
proposal: docs/issue-2219/reports/execution-observation.md
---

# Hunt record — pr-2246-execution-observation

## after-proposal — stance 1: harness-fidelity of the session's AFTER re-run against PR #2246's actual behavior

Verdict: FINDING — the record's step-3 "residual denial" claims (an orphaned-path #330 line surviving in both AFTER runs) do not reproduce against the real deployed hook run on PR #2246's actual worktree; one of the two fragments the record says still returns `rc=2` with a `#330` line actually returns a clean `rc=0` pass, and the other's AFTER output never contains a `#330` line at all.
Kind: silent-failure
Seed: docs/issue-2219/reports/execution-observation.md, step 3 ("Live-fire AFTER, using the hook's own embedded Python guard logic")
cap_seconds: not specified by dispatcher
tier: default
diff_stat_lines: not applicable (independent re-run, not a diff review)
started_at: 2026-08-25T09:10:00+09:00
ended_at: 2026-08-25T09:35:00+09:00

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2219-execution-observation
git worktree add /tmp/pr2246-wt origin/issue-2219/implementation

# Reconstruct the two verbatim Write payloads straight from the raw session
# log named in issue #2219's own Acceptance section (lines 622 and 683),
# same content the execution-observation record itself used (saved earlier
# by that session at /tmp/write_622_full.md and /tmp/write_683_full.md,
# still present on disk), with cwd set to the log's own recorded cwd
# (/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2208-implementation,
# still present on disk, still a real git repo).

python3 -c "
import json
content = open('/tmp/write_683_full.md').read()
payload = {'session_id': 's1',
  'cwd': '/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2208-implementation',
  'tool_name': 'Write',
  'tool_input': {'file_path': '/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2208-implementation/docs/issue-2208/reports/implementation.md',
                 'content': content}}
open('/tmp/payload_683.json','w').write(json.dumps(payload))
"

# Run the REAL deployed hook script (not a hand-extracted Python fragment)
# against PR #2246's actual worktree, on the #870 fragment:
cat /tmp/payload_683.json | bash /tmp/pr2246-wt/on-the-record/hooks/record-claim-guard.sh
echo "RC=$?"
```

### Observed
```
RC=0
```
No output at all, and `rc=0` — the #870 fragment passes cleanly through the real hook against PR #2246's real code.

The #333 fragment (write_622, same reproduction method with `/tmp/write_622_full.md`) does return `rc=2` through the real hook, but with exactly one line naming the `"Fixed" section` #870 residual the record itself also names — and never an orphaned-path `#330` line, confirmed on repeated re-runs.

### Expected
The record's step 3 states: "#870 fragment AFTER: rc=2; the quoted #870 claim itself no longer appears; one unrelated orphaned-path (#330) line remains" and "#333 fragment AFTER: ... plus the same orphaned-path (#330) lines". Both of those `#330`-line claims should be reproducible through the real deployed hook against the actual PR #2246 worktree, the way the #870-"Fixed section" residual is. They are not: one fragment's AFTER run in the record is stricter (rc=2) than what the real hook actually returns (rc=0, clean pass), and neither fragment's real AFTER run ever emits a `#330` line. This means the record's own harness — hand-extracting the guard's embedded Python and manually pointing `RCG_GATES_DIR` at scratch-copied module files, rather than running `record-claim-guard.sh` itself against a real worktree — silently diverged from the code path the real deployed hook exercises (most likely by resolving the orphaned-path check's git-root differently than the real script's `script_dir`-relative resolution does), producing residuals in the record that the actual shipped hook does not produce. The record's "replay-environment artifact" explanation for the #330 residual is explaining a defect in its own harness, not a fact about the real hook's post-fix behavior — and undersells the fix, which for the #870 fragment is actually a full clean pass, not a partial one.
