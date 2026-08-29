---
issue: 2334
role: independent-verification-2
author: independent-verification-2
verifies_subject: true
loop_state: landed
type: verification
breaking: false
verdict: pass
code_under_review: PR #2766 (issue-2334/observability-explorability+adversarial-review-83d1d3bc), commit 78ef46ef324b3ebefff3c88e9b9e9fe96b41f8c9
upstream:
  - path: watchdog.py
    sha: 78ef46ef324b3ebefff3c88e9b9e9fe96b41f8c9
  - path: spawn.py
    sha: 78ef46ef324b3ebefff3c88e9b9e9fe96b41f8c9
  - path: on-the-record/monitors/poll_heartbeat_delta.py
    sha: 78ef46ef324b3ebefff3c88e9b9e9fe96b41f8c9
---

# issue-2334 — independent-verification-2 record

## What was done

Independently audited PR #2766 (branch
`issue-2334/observability-explorability+adversarial-review-83d1d3bc`,
head `78ef46ef`), which claims to fix issue #2334 (watchdog per-tick
anomaly summary line named only a count, never which signal fired). Rather
than trusting the PR's own record, re-derived every load-bearing claim from
a separate git worktree checked out at the PR's head commit.

canonical: `gh pr view 2766 --repo tokenmaxxxer/on-the-record --json
headRefName,baseRefName,mergeable,commits,files,state,title` — state OPEN,
base `main`, head `issue-2334/observability-explorability+adversarial-review-83d1d3bc`,
2 commits, 5 files touched (`watchdog.py`, `docs/reports/product/quality-bar.md`,
plus the PR author's own record/hunt-record/deviation-log files, which are
untracked in this branch — they land only on PR #2766's branch, per the
same `gh pr view --json files` output).

**1. Code diff.** derived: `git show 78ef46ef:watchdog.py | sed -n
'1715,1735p'` in a worktree at the PR head — the `if anomalies:` branch
now reads `classes = dict.fromkeys(a.split(":", 1)[0] for a in
anomalies)` then `print(f"[watchdog] {key}: 이상 신호 {len(anomalies)}건
({', '.join(classes)})")`; the `else: print(f"[watchdog] {key}: 정상")`
branch (the zero-anomaly/common-case path) is byte-for-byte outside the
diff hunk — confirms the record's "empty state unchanged" claim
structurally, not just by reading the PR's own diff excerpt.

**2. Live-tick reproduction (executed-live).** derived: independently
crafted (not copied from the PR record) a JSONL transcript with 3 genuine
structural `tool_result`/`is_error` blocks whose text matches
`_HARNESS_REFUSAL_PATTERNS` (`"Permission to use Bash has been denied"`),
then called `spawn.watchdog_check_one()` directly against it and
formatted both the old and new f-strings from its actual return value:
```
RAW anomalies: ['denied-tool-calls: 이번 스캔 구간에 3건']
BEFORE: [watchdog] issue-2334/denied-burst-INDEPENDENT-CHECK: 이상 신호 1건
AFTER : [watchdog] issue-2334/denied-burst-INDEPENDENT-CHECK: 이상 신호 1건 (denied-tool-calls)
```
Matches the PR record's own before/after pair exactly (same anomaly
string, same rendered output), independently reproduced rather than
re-pasted.

**3. Byte-overhead numbers.** derived: independently re-ran the byte-count
comparison (`len(s.encode())` for the before/after f-strings) for a
1-class and a synthetic 3-class anomaly list:
```
1-class: BEFORE=54B AFTER=74B delta=+20B
3-class: BEFORE=54B AFTER=104B delta=+50B
```
Matches the PR record's claimed deltas exactly.

**4. Full test suite (no regression).** derived: `python3 -m pytest test/
-q` on the PR head worktree:
```
15 failed, 414 passed, 3 xfailed in 2.45s
```
Failing-test-name set matches the PR record's pasted set name-for-name —
all in `test_convention_equivalence.py`, `test_local_dependency_env.py`,
`test_spawn_cross_family_skill_selection.py`,
`test_spawn_artifact_skill_pairing.py`, and
`test_spawn_skill_judge_haiku_timeout_overlap.py`, none touching
`watchdog.py`/`spawn.py`'s `watchdog_check_one`/`roster.py`'s anomaly
path. derived: `python3 -m pytest test/test_watchdog_heartbeat_noise.py
-q` — `6 passed in 0.87s`, matching the PR record.

**5. Downstream consumer check.** derived: `sed -n '38,52p'
on-the-record/monitors/poll_heartbeat_delta.py` — confirmed `TAG_RE =
re.compile(r"^\[(poll-report|watchdog|health|reconcile|orphaned|resume|watchdog-crash|returned-pr)\]\s*([^:]+):")`
stops its `([^:]+)` capture at the first colon after `{key}`, i.e. before
the new parenthetical is ever reached — the tag/key extraction this
consumer relies on is unaffected. Also independently confirmed the PR's
own hunt record's finding that `ALWAYS_RE` contains the bare substring
`watcher-dead` (`r"^\[(resume|orphaned|watchdog-crash|awaiting-approval)\]|STALLED|CRASHED|COMPLETED|watcher-dead"`),
so a `watcher-dead` class name appearing in the new parenthetical can
trigger an extra always-emit of the summary line — but the corresponding
per-signal bullet line (`  - watcher-dead: ...`, unchanged by the diff)
already always-emitted independently before this change under its own
dedup key, so this is at most redundant emission, never a suppression.

**6. Acceptance-gate claim.** The issue names
`tests/test_watchdog_local_signals.py` (untracked — never created in this
repo) as its gate. derived: `find . -iname "*watchdog_local_signals*"` in
the PR head worktree — zero matches; `grep -rln "import watchdog"
--include="*.py" .` — only `spawn.py` imports `watchdog.py`, no test file
does. Confirms the PR record's claim that this named path is untracked —
verification instead rests on the executed-live reproduction above, which
this record independently reproduces.

**7. Per-class-count structural claim (adversarial-review finding).**
derived: read `spawn.py:1688-1753` directly in the PR head worktree — each
of the anomaly classes (`log-silence`, `background-delegation-phrasing`,
`denied-tool-calls`, `heartbeat-only-growth`, `no-commits-late`,
`watcher-missing`, `watcher-dead`, `watcher-silent`, plus `roster.py`'s
`flat-progress`) is guarded by its own independent `if` block containing
exactly one `anomalies.append(...)` call — no loop or branch can append
the same class twice within one `watchdog_check_one()` call, so a
per-class occurrence count could structurally never exceed 1 given the
current call graph. Independently confirms the PR record's adversarial-
review finding that motivated dropping the count field for a plain
deduped class-name list.

No discrepancy found between the PR's claims and independently
reproduced evidence in the checks above (derived: tags 1 through 7). No
new bug, no regression, no overhead on the common (zero-anomaly) case.

## Why

Verify-at-landing convention requires an independent verification record,
not a re-read of the PR's own record, before this subject's deliverable
counts as landed. Independent worktree re-derivation (rather than trusting
pasted numbers) is the only way to catch a plausible-but-wrong claim —
e.g. a byte-count or test-name set that was hand-typed rather than
actually re-run. All numeric/behavioral claims in the PR record were
re-executed from scratch here and matched exactly; nothing was accepted
on the PR author's word alone.

## What did not work

None — every independently re-run check matched the PR record's claims on
the first attempt; no dead end, no discarded approach.

## Upstream basis

PR #2766 (issue #2334), branch
`issue-2334/observability-explorability+adversarial-review-83d1d3bc`, head
commit `78ef46ef324b3ebefff3c88e9b9e9fe96b41f8c9` — canonical: `gh pr view
2766 --repo tokenmaxxxer/on-the-record` output (state OPEN). Code paths
audited: `watchdog.py`, `spawn.py`,
`on-the-record/monitors/poll_heartbeat_delta.py` — all at the same head
commit (`sha: 78ef46ef324b3ebefff3c88e9b9e9fe96b41f8c9` per contract §1,
not `same-commit`, since these paths land on the PR's branch, not this
record's own commit). The PR author's own record
(`docs/issue-2334/reports/observability-explorability+adversarial-review-83d1d3bc.md`,
untracked in this branch — lives only on PR #2766's branch) was read via
`gh pr diff 2766` rather than a local path.

## Open findings

None new. The PR's own open finding (unguarded "class: detail" colon
convention in `classes = dict.fromkeys(a.split(":", 1)[0] for a in
anomalies)`) was independently checked against the current anomaly-append
call sites (see check 7 above) — all follow the convention today,
consistent with this repo's stated preference for trusting internal
call-graph invariants over defensive parsing for inputs that cannot
currently occur. No new open finding raised by this verification.

## Next steps

None — `loop_state: landed`. `verifies_subject: true`; this record is an
independent verification of issue #2334's deliverable (PR #2766).

other mounted skills: not triggered — this record was written directly in
English per the work-in-english guidance without invoking the Skill tool.
