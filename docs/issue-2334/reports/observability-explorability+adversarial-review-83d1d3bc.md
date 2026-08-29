---
issue: 2334
role: observability-explorability+adversarial-review-83d1d3bc
author: observability-explorability+adversarial-review-83d1d3bc
skills: observability-explorability (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: watchdog.py
    sha: same-commit
---

# issue-2334 — observability-explorability+adversarial-review-83d1d3bc record

## What was done

Fixed the alarm-without-content defect (#2334): the watchdog per-tick anomaly
summary line named only a count, never the signal, forcing a log dig every
time. `watchdog.py:1723-1731` (`roster_watchdog`), when `anomalies` is
non-empty:

```diff
-            print(f"[watchdog] {key}: 이상 신호 {len(anomalies)}건")
+            # name the signal class(es) inline, reusing each anomaly's existing "class: detail" label
+            classes = dict.fromkeys(a.split(":", 1)[0] for a in anomalies)
+            print(f"[watchdog] {key}: 이상 신호 {len(anomalies)}건 ({', '.join(classes)})")
```
derived: `git diff --stat -- watchdog.py` — result: `1 file changed, 3 insertions(+), 1 deletion(-)`

`classes` is built from the substring before the first `:` of each string
already in `anomalies` — the same "class: detail" convention already used
by every anomaly-producing site in `spawn.py`'s `watchdog_check_one()`
(e.g. `denied-tool-calls: 이번 스캔 구간에 3건`), so this is zero new
queries and zero new data source, deduped in first-appearance order.
Empty-anomaly-list path (`else: print(f"[watchdog] {key}: 정상")`,
`watchdog.py:1735`) is untouched — canonical: the diff above touches only
the `if anomalies:` branch, the `else:` line is outside the hunk.

Real single-anomaly tick, executed live against `spawn.watchdog_check_one()`
with a crafted JSONL log containing 3 genuine structural denial
(`is_error`+refusal-pattern) `tool_result` blocks — canonical: executed by
me directly, `python3` one-off script calling `spawn.watchdog_check_one()`
with a real crafted JSONL, then formatting both the old and new f-strings
against its actual return value (not hand-typed):
```
RAW anomalies: ['denied-tool-calls: 이번 스캔 구간에 3건']
BEFORE: [watchdog] issue-2334/denied-burst: 이상 신호 1건
AFTER : [watchdog] issue-2334/denied-burst: 이상 신호 1건 (denied-tool-calls)
```

Byte-overhead per tick (UTF-8), old vs. new, for the executed 1-class case
above and a synthetic 3-class case — derived: `python3` one-off script
constructing both format strings from the same `key`/`anomalies` inputs
and comparing `len(s.encode())`:
```
1-class: BEFORE=54B  AFTER=74B  delta=+20B
3-class: BEFORE=54B  AFTER=104B delta=+50B
0-class (healthy tick, by far the common case): delta=0B — line untouched
```

## Why

**Inline-vs-pointer split.** canonical: observability-explorability skill,
loaded this turn via the Skill tool — its rules state: retain the raw
high-dimensionality data behind any new aggregate (rule 1), and let ad-hoc
questions be answered by querying that raw data rather than by shipping
more code for a new fixed view (rule 2). This watchdog tick already had
that shape once I looked at it: the summary line is the aggregate
("panel"), and the very next lines (`for a in anomalies: print(f"  - {a}")`,
unchanged) are the full raw per-signal detail — already retained, already
printed, one line away. So the fix inlines only the minimum identifying
dimension (the class label — `denied-tool-calls`, not the full "이번 스캔
구간에 3건" detail text) into the summary line, and leaves the full raw
detail exactly where it already was. Cramming detail text into the summary
line itself would instead be the failure mode the skill's rule 3 warns
against (proliferating pre-aggregated panel text) rather than pointing at
raw data that is already one line below. The issue's own example
(`이상 신호 1건 (denied-tool-calls: 3)`) matches this split.

**Adversarial review.** Spawned a blind evaluator (fresh `general-purpose`
subagent, given only the raw diff and the observed `anomalies` string
shape — no issue text, no rationale, no builder framing) against my first
version of this fix, which tracked a per-class *count*
(`class_counts[cls] = class_counts.get(cls, 0) + 1`, rendered as
`"class: n"`). canonical: evaluator's returned critique text — it traced
every `anomalies.append(...)` call site in `spawn.py`'s
`watchdog_check_one()` and `roster.py`'s `lease_renew()` and reported each
anomaly class is appended at most once per tick via mutually-exclusive
`if`/`elif` branches, so the count could never be anything but one,
making the count field misleading dead weight ("presents itself as real
frequency aggregation but is inert" — evaluator's words). canonical:
`spawn.py:1688-1753`, read directly by me to confirm the branches are in
fact mutually exclusive (one `if`/`elif` chain, each `anomalies.append`
reachable at most once per call). Simplified the fix to a plain deduped
class-name list (`dict.fromkeys(...)`) — see "What did not work" below.
The evaluator's other two findings were assessed and not acted on: the
"redundant with the next lines" finding is the point of the fix (the
issue is specifically that the operator was skimming past those next
lines and asking for the class inline so a round-trip to them isn't
needed); the "no defensive handling of a colon-less anomaly string"
finding is a real edge case against an implicit convention already shared
by all current anomaly producers, and this repo's own convention is to
trust internal call-graph invariants rather than add validation for
inputs that cannot occur given the current code — recorded as an open
finding below rather than defended against.

skill-verdict: observability-explorability — applied: invoked; used to
decide the inline-vs-pointer split (class label inline, full per-signal
detail already retained one line below) for the watchdog summary line,
see the "Inline-vs-pointer split" paragraph above.
skill-verdict: adversarial-review — applied: invoked; spawned a blind
`general-purpose` evaluator subagent (Agent tool, foreground, given only
the raw diff, no issue/spec context — canonical: the agent dispatch
prompt and its returned critique text this turn); the evaluator's finding
that the per-class count was structurally always one was independently
verified by me against `spawn.py:1688-1753` and the fix was simplified
accordingly, see the "Adversarial review" paragraph above and "What did
not work" below.

## Upstream basis

Issue #2334 — canonical: `gh issue view 2334` output (state: OPEN). Code
path: `watchdog.py`, same commit as this record (`sha: same-commit`).

## What did not work

- Wrote a per-class occurrence-counting version first
  (`class_counts: dict[str, int]` accumulator, rendered `"class: n, class2:
  m"`), matching the issue's own example text `(denied-tool-calls: 3)`
  literally (count-shaped). The blind adversarial-review pass (see "Why")
  showed the count could never be anything but one given the current call
  graph, which I confirmed by reading `spawn.py:1688-1753` myself (see
  canonical tag above) — every anomaly class is appended at most once per
  tick through mutually-exclusive branches. Replaced it with a plain
  deduped class-name list (`dict.fromkeys(...)`), which conveys the same
  information (which classes fired) without a misleading always-one count
  and with fewer bytes per tick. derived: same byte-measurement script as
  above, rerun against the earlier per-count version before replacing it:
  ```
  earlier (with counts): 1-class=77B, 3-class=113B
  final (no counts):     1-class=74B, 3-class=104B
  ```

## Open findings

- `classes = dict.fromkeys(a.split(":", 1)[0] for a in anomalies)` relies
  on the implicit "class: detail" string convention already shared by
  every current anomaly-append call site in `spawn.py`'s
  `watchdog_check_one()`. canonical: `spawn.py:1688-1753`, read directly —
  `log-silence`, `background-delegation-phrasing`, `denied-tool-calls`,
  `heartbeat-only-growth`, and the watcher-state signals all follow the
  "class: detail" shape. No new validation was added for a future anomaly
  string that omits the colon (it would fold entirely into the summary
  parenthetical instead of failing loudly) — left unguarded, consistent
  with this codebase's convention of trusting internal call-graph
  invariants rather than defending against inputs that cannot occur
  today. Resolution path: none needed unless a future anomaly producer
  breaks the convention; if it does, fix the producer to add the colon
  rather than add defensive parsing at the consumer.

## Downstream consumer check (monitor/watch machinery not broken)

`on-the-record/monitors/poll_heartbeat_delta.py:29` —
```
TAG_RE = re.compile(r"^\[(poll-report|watchdog|health|reconcile|orphaned|resume|watchdog-crash|returned-pr)\]\s*([^:]+):")
```
canonical: `grep -n "TAG_RE\|이상 신호" ./on-the-record/monitors/poll_heartbeat_delta.py`,
read directly by me — match group 2 (`[^:]+`) stops at the first colon
after `<key>`, i.e. at `{key}:`, before the new parenthetical is ever
reached, so this consumer's tag/key extraction is unaffected by the new
trailing text.

## Test/regression evidence (no new bug)

Ran the full suite on my changed tree, after the final simplified edit —
derived: `python3 -m pytest test/ -q`:
```
15 failed, 414 passed, 3 xfailed in 1.90s
```

Failing-test-name set (not just the count) below. The delegated build
worker compared this set against a `git stash`-reverted (pre-fix,
origin/main-based) tree and reported the identical set and totals; I
independently re-ran `python3 -m pytest test/ -q` myself on the
post-fix, post-simplification tree (the run pasted immediately above)
and confirmed the same names and the same totals reappear — derived: the
two `python3 -m pytest test/ -q` runs (worker's pre-fix run and my own
post-fix run) match name-for-name:
```
test/test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape
test/test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim
test/test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment
test/test_spawn_cross_family_skill_selection.py::Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate
test/test_spawn_cross_family_skill_selection.py::FourSurfaceCandidateCorpusTest::test_score_reaches_judge_question_labeled
test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_success_logs_picked_rejected_reasons_and_returns_picked_paths
test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_no_declaration_line_byte_identical_to_baseline
test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive
test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeOverlapOrderingTest::test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows
test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_declared_artifact_matching_skill_gets_pairing_line
test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo
test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline
test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_completed_outcome
test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_consult_error_raises_and_still_traces
test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_fail_open_outcome
```
None of these touch `watchdog.py`, `spawn.py`'s `watchdog_check_one`, or
`roster.py`'s anomaly path — the set is identical with and without this
change, so no new bug.

The issue names `tests/test_watchdog_local_signals.py` as its acceptance
gate; that path is untracked in this repo — it was never created here,
and it is not a renamed/moved form of any existing file. derived: `find .
-iname "*watchdog_local_signals*"` — result: no output (zero matches).
Also `grep -rln "import watchdog" --include="*.py" .` — result: only
`spawn.py` imports `watchdog.py`; no test file does. Per this repo's
verify-at-landing convention ("do not author new persistent test files by
default"), verification was via the executed-live run in "What was done"
above, not a new test file. The one existing watchdog-adjacent persistent
test — derived: `python3 -m pytest test/test_watchdog_heartbeat_noise.py -q`,
run by me directly after the final edit:
```
6 passed in 0.83s
```

## Standing invariants (checked)

- **No return of the retired role axis, in any reshaped form.** The
  grouping key here is each anomaly's existing signal-class label
  (`denied-tool-calls`, `log-silence`, `watcher-missing`, ...), not any
  role concept. canonical: `git log --all --oneline --grep="role axis" -i`
  output, read directly — the real "role axis" retirement (issue #2241
  staging proposal, issue #2626 reshape-survival audit,
  `docs/decisions/2026-08-25-retire-role-axis-staging.md`) is an
  unrelated session/worktree naming-scheme axis (role-based branch
  naming, retired for skill-axis naming), not anomaly-signal grouping.
  Nothing in this diff references role, branch naming, or that axis.
- **No new bug.** See "Test/regression evidence" above — identical
  failing-test-name set, same pass/xfail totals, with and without this
  change.
- **No overhead increase (binds hardest).** See byte-overhead
  measurements in "What was done": the common case (a healthy tick with
  zero anomalies) is byte-for-byte unchanged; only anomaly ticks (already
  the rare, worth-the-cost case) grow, by a small measured amount per
  case — not a wall of text, one parenthetical of class labels.
- **Monitor/watch machinery not broken, exercised via a real heartbeat.**
  See "Downstream consumer check" (regex still matches) and "What was
  done" (real `spawn.watchdog_check_one()` execution, before/after lines
  pasted, both before and after the change).

## Next steps

None — `loop_state: landed`. This delivers the full fix; the one open
finding above (unguarded colon convention) is accepted as consistent with
existing codebase convention, not a blocker.
