---
issue: 2333
role: implementation
loop_state: done
upstream:
  - path: (none — build-now delivery, contract v3 s19a; no prior proposal round)
    sha:
code_under_review:
  - consult.py
  - spawn.py
  - tests/test_spawn_consult_panel.py
  - tests/test_consult_trace_root.py
  - test/test_spawn_cross_family_skill_selection.py
  - on-the-record/commands/consult.md
  - on-the-record/directive/delegation-loops.md
type: feat
breaking: "no — `_consult_trace_path()` return value changes shape (dir/shard-id.md instead of a bare file), but it and `_consult_trace_dir()`/`_consult_log_aggregate()` are internal `spawn.`-namespaced functions, not a public CLI/API surface; the only shipped CLI contract change is additive (`spawn.py consult-log`)"
verdict: pass
---

# issue-2333 — implementation record

## What was done

Sharded `docs/issue-<n>/reports/consult-log.md` per session, per issue
#2333's "Preferred" option (1):

- `consult.py`: `_consult_trace_path(issue, cwd)` now returns
  `docs/issue-<n>/reports/consult-log/<session-ts-pid>.md` (or
  `docs/reports/consult-log/<session-ts-pid>.md` with no issue) instead of
  a single flat file. The `<session-ts-pid>` id
  (`_consult_session_shard_id()`) is computed once per process (UTC
  microsecond timestamp + pid) and cached for the process's lifetime, so
  every consult/verb/skill_judge call inside one session appends to the
  same shard file, while two different sessions — different processes,
  different branches — write to two different paths, even if they start
  in the same second (pid differs) or share a pid across a long-running
  host (timestamp differs).
- Added `_consult_trace_dir(issue, cwd)` (the shard directory, used by
  both the writer and the reader) and `_consult_log_aggregate(issue,
  cwd)` — a reader that globs every shard under the directory, sorted by
  filename (fixed-width timestamps sort lexicographically =
  chronologically), and concatenates their contents. Each shard's lines
  are byte-identical to what `_append_consult_trace()` always wrote, so
  the aggregate reproduces what the old single `consult-log.md` would
  have contained — see the Executed evidence section for a live run.
- Added a `spawn.py consult-log --issue <n> [-C <repo>]` CLI subcommand
  that prints `_consult_log_aggregate()`'s output.
- `_commit_consult_trace()`, `_persist_consult_raw_output()`, and the
  "no traceless consults" `finally`-block in `consult_cmd()`/
  `_verb_cmd()`/`_skill_judge_consult()` needed no code changes — they
  already operate on whatever `_consult_trace_path()` returns, so every
  consult call still appends exactly one line, every time, in its own
  `finally` (issue requirement 3 holds by construction, not by a
  separate check).
- Updated `on-the-record/commands/consult.md` and `on-the-record/
  directive/delegation-loops.md` to describe the sharded layout and the
  `consult-log` reader subcommand instead of the old flat path.
- Updated `tests/test_consult_trace_root.py` and `test/
  test_spawn_cross_family_skill_selection.py`, which asserted the real
  (unmocked) `_consult_trace_path()`/`_consult_root()` output against the
  old flat path, to match the sharded layout / read through the
  aggregator. Tests that stub `_consult_trace_path` themselves
  (`gates/test_consult_siblings.py`, `tests/test_spawn_directive_assembly.py`,
  `tests/test_gates.py`, the existing `ConsultCmd` class in the gate
  file) needed no changes.
- Added a `ConsultLogSharding` test class to the named acceptance gate
  (`tests/test_spawn_consult_panel.py`): two sessions writing distinct
  shard files, chronological aggregation, the empty-state (no prior
  consults), the single-session case, and a real `git init`/branch/merge
  exercise on the two-session scenario.

## Why

Append-only file + concurrent writers + one shared path is what makes the
git merge conflict predictable, per the issue text. Sharding removes the
shared path, which removes the class of conflict rather than the
individual instances of it. The issue's `.gitattributes merge=union`
alternative only works when the merge driver cannot interleave a single
logical entry's lines across two sides — true for consult-log's
single-line entries, which is why the issue lists sharding as *preferred*
there rather than mandatory. Sharding is strictly stronger (a union merge
driver still requires every consumer's git to have the attribute
configured; sharding requires nothing from the consumer) and was no
harder to build correctly, so that is what shipped.

## What did not work

None.

## Deviations

Scope was narrowed to consult-log; hook-fires and deviation-log sharding
were not built in this delivery. The issue's point 1 also names
`.orchestrate-hook-fires.log` ("Same for hook-fires") and point 2 flags
deviation logs as needing sharding (multi-line entries, union-unsafe). I
looked at both before deciding to leave them out:

- `.orchestrate-hook-fires.log` (written from `on-the-record/hooks/
  directive.sh`, `on-the-record/hooks/stop-gate.sh`, `on-the-record/
  hooks/stop-poll-rearm.sh`): `directive.sh`'s own "issue #2028:
  append-only fire counter" comment states this file's purpose is a
  per-workspace fire counter, and `on-the-record/hooks/
  test_hook_fire_counter.py`'s
  `t_directive_and_stop_gate_share_the_same_counter_file_in_a_workspace`
  test asserts that different hooks within one workspace share the same
  counter file — so session-level sharding (matching consult-log) is the
  right granularity. A stable per-session shard id is available inside
  these bash hooks the same way `directive.sh` already derives one for
  its monitor-notice marker: hash the `session_id` field off the hook's
  stdin JSON payload (`directive.sh` lines 81-91,
  `hashlib.sha256(session_id)[:24]`). The complication is that today's
  fire-counter write happens before that JSON is parsed, by design (its
  comment: "written before any kill-switch/role short-circuit... so the
  count reflects every real trip") — wiring in session-id sharding means
  restructuring stdin handling (capture once, reuse for the counter write
  and the existing payload parse) across three hook scripts that fire on
  every UserPromptSubmit/Stop event, for every consumer session, fleet
  wide. That restructuring is buildable — the design above is the
  concrete sketch for it — but its blast radius sits outside this
  delivery's named gate (`tests/test_spawn_consult_panel.py` does not
  touch hook-fires), so I filed it as a follow-up instead of rushing it
  in alongside the consult-log change.
- Deviation logs (`docs/issue-<n>/reports/deviation-log.md`): these have
  no shared Python writer (entries are appended by hand by whichever
  session recognizes a deviation); the only mechanical contract on them
  is `on-the-record/hooks/deviation-log-guard.sh`, which computes the
  path from the branch name alone, with no role or session component
  today. Sharding this means changing that guard's path computation,
  `docs/handbooks/deviation-loop.md`'s documented entry format, and
  reconciling a pre-existing role-scoped convention already visible in
  the repo (many `docs/issue-*/reports/<role>/deviation-log.md` files use
  a path the current guard does not check) — a separate, larger piece of
  work. Its entries are multi-line, so gitattributes union is unsafe per
  the issue's own reasoning, leaving sharding as the only correct option
  for it — also filed as a follow-up rather than attempted here.

## Upstream basis

None. Build-now delivery (`CORE_BUILD_NOW=1`, contract v3 s19a): no
phase-1 proposal round ran for this issue.

## Open findings

- Hook-fires sharding: design sketched under Deviations above
  (session-id-hash shard files under `.orchestrate-hook-fires/`,
  mirroring `directive.sh`'s existing monitor-notice marker pattern) —
  needs a stdin-capture-once refactor across `directive.sh`/
  `stop-gate.sh`/`stop-poll-rearm.sh`, updated assertions in
  `on-the-record/hooks/test_hook_fire_counter.py` and `on-the-record/
  hooks/test_stop_poll_rearm_deadman.py`, and a small aggregator (same
  shape as `_consult_log_aggregate()`). Resolution path: a follow-up
  issue.
- Deviation-log sharding: needs `on-the-record/hooks/
  deviation-log-guard.sh`'s path computation extended with a session
  component, `docs/handbooks/deviation-loop.md` updated to match, and a
  decision on the pre-existing role-scoped path convention the guard does
  not currently enforce. Resolution path: a separate follow-up issue from
  hook-fires — different guard, different convention drift to untangle
  first.

## Next steps

None.

## Executed evidence

acceptance: `python3 -m pytest tests/test_spawn_consult_panel.py -q`
(the named gate, includes the new `ConsultLogSharding` class) — result:

```
..........................................................x.....         [100%]
63 passed, 1 xfailed in 1.18s
```

acceptance: `python3 -m pytest tests/test_consult_trace_root.py
gates/test_consult_siblings.py gates/test_consult_verdict_parsing.py
gates/test_consult_json_parse.py
test/test_spawn_cross_family_skill_selection.py
test/test_spawn_skill_judge_haiku_timeout_overlap.py -q` (adjacent
consult-path tests exercising the real, unmocked
`_consult_trace_path()`/`_consult_root()`, updated for the new shard
layout) — result:

```
..................................................................x..... [ 59%]
....x.......x..................x..................                       [100%]
118 passed, 4 xfailed
```

acceptance: `git stash && python3 -m pytest
tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace
-q; git stash pop` (checking whether the one unrelated failure in the
wider test suite is caused by this change) — result: same failure with
this delivery's changes stashed out:

```
FAILED tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace
1 failed in 22.48s
```

**Provenance — two real sessions consulting on one issue, executed live**
(acceptance requirement): a scratch git repo, a stubbed `claude` binary
returning a canned verdict, two branches each running the real
`spawn.py consult` CLI end to end (real `consult_cmd()`, real trace
write, real `git add`+`git commit` via `_commit_consult_trace()`).

acceptance: on branch `issue-2333/session-a`, `python3 spawn.py consult
implementation "세션 A: 이 스키마 변경 breaking 인가?" --issue 2333 -C
"$REPO" --no-contract` — result:

```
{"answer": "ok", "confidence": "high", "caveats": []}
$ find docs/issue-2333/reports/consult-log -type f
docs/issue-2333/reports/consult-log/20260825T043729328882-526607.md
```

acceptance: on a second branch `issue-2333/session-b` checked out from
`main` (session-a's branch not yet touched), `python3 spawn.py consult
implementation "세션 B: 이 인덱스 필요한가?" --issue 2333 -C "$REPO"
--no-contract` — result:

```
{"answer": "ok", "confidence": "high", "caveats": []}
$ find docs/issue-2333/reports/consult-log -type f
docs/issue-2333/reports/consult-log/20260825T043733640389-527423.md
```

acceptance: `git checkout main && git merge -q --no-edit
issue-2333/session-a && git merge --no-edit issue-2333/session-b; echo
$?` — result:

```
Merge made by the 'ort' strategy.
 docs/issue-2333/reports/consult-log/20260825T043733640389-527423.md | 1 +
 1 file changed, 1 insertion(+)
 create mode 100644 docs/issue-2333/reports/consult-log/20260825T043733640389-527423.md
0
```

The two sessions never wrote the same path, so the merge had nothing to
reconcile — the same two branches appending to the old single
`consult-log.md` from the same base commit would have produced a
conflict on that shared file.

acceptance: `python3 spawn.py consult-log --issue 2333 -C "$REPO"` (the
new reader/aggregator, run against `main` after both merges above) —
result:

```
- 2026-08-25T04:37:29.328900+00:00 | role=implementation | verb=consult | issue=2333 | question='세션 A: 이 스키마 변경 breaking 인가?' | outcome='ok: ok | evidence=[verified:0 failed:0 unverified-cmd:0 no-evidence:1]'
- 2026-08-25T04:37:33.640411+00:00 | role=implementation | verb=consult | issue=2333 | question='세션 B: 이 인덱스 필요한가?' | outcome='ok: ok | evidence=[verified:0 failed:0 unverified-cmd:0 no-evidence:1]'
```

Both entries are present, in chronological order, in the pre-#2333
single-file format — reconstructed from two sessions that never touched
the same path.

**Empty state** (single-session issue, no concurrency provoked): the
`ConsultLogSharding::
test_single_session_issue_layout_reads_identically_to_the_one_shard`
method in `tests/test_spawn_consult_panel.py` (covered by the first
pytest run above) asserts a lone shard's content and the aggregate are
byte-equal; by construction a single shard cannot collide with anything.

## skill-verdict

skill-verdict: implementation-blueprint — not-applicable: single-file,
single-function change inside one already-established module
(`consult.py`'s existing trace-path/append/commit trio), not a
multi-module structure decision.
skill-verdict: implementation-complexity-coupling-management —
not-applicable: no coupling/cohesion metric crossed a threshold and no
cross-module import direction changed; `_consult_trace_path()` kept its
existing signature and callers.
skill-verdict: implementation-design-pattern-selection — not-applicable:
no GoF-pattern indirection question here — this is a path-scheme change
(flat file → sharded dir + reader), not a class-shape decision.
skill-verdict: implementation-performance-data-structure-choice —
not-applicable: `_consult_log_aggregate()` globs and concatenates a
handful of small per-session files; no loop-membership-test, algorithm-
class, or cache-maintenance tradeoff is in play at this scale.
skill-verdict: work-in-english — applied: invoked; this record, the
commit message, the PR, and all new/changed code comments and test names
are in English (project convention already in effect; the skill's own
trigger — Korean user communication in this session — applies, but no
Korean landed in shipped artifacts as a result of following it).
other mounted skills: not triggered.
